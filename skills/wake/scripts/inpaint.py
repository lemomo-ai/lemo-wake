#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["numpy", "opencv-python-headless", "onnxruntime"]
# ///
"""Erase what the mask covers and fill in the background -> clean plate, same size as the image. Local CPU.

  inpaint.py <img> <mask.png> --out plate.png [--engine lama|opencv] [--dilate N] [--split]

  mask      white = erase. segment.py output works directly (soft edges >= 2% count as erase); an RGBA cut-out works too.
  --engine  lama (default): LaMa, ~208 MB downloaded once after the user's one-time consent (see models.py);
            continues structure and texture, ~2-4 s incl. loading.
            opencv: cv2.inpaint TELEA, no download; only for thin lines / small spots, large areas smear radially.
            If LaMa is unavailable (declined / download failed), opencv plus careful staging is the fallback.
  --dilate  grow the mask by N px. Default = 1% of the image diagonal (>= 8; 1672x941 -> 19). Too little and the
            subject's shadow/outline stays at the hole edge and LaMa "continues" it into dirty blotches (3D poster
            lettering especially); raise it if residue remains, lower to 6-8 for small objects in plain photos.
  --split   (lama) fill each separate object of the mask on its own crop, one after another (earlier fills become
            context for later ones). Use it when the mask is a row or cluster of neighbouring objects (planets in a
            line, products on a shelf, icons with their labels): by default the grown mask merges them into one big
            blob - or more than 6 blobs fall back to one pass - and the whole area is squeezed through LaMa's 512 input
            (stderr shows "downscale 3.75x"). With --split each object fills near native resolution. Letters of one
            word stay one object. Slower: one LaMa pass per object.
Only pixels inside the grown mask change (with a soft ramp in the grown band); everything else is pixel-identical.

LaMa takes a fixed 512 input, so:
- mask bbox up to ~400 px: filled near native resolution, hard to notice. Distant mask blobs are cropped and filled
  separately; neighbouring ones merge into one bigger fill unless you pass --split.
- the bigger the subject, the more it is downscaled (half-body portrait ~2x; > 40% of the frame -> whole image at 512):
  the filled area gets soft and smeary. Such a plate works as "background hidden behind the foreground" (subject
  moves a little, only edges show), not as a picture on its own.
- whatever the segmentation missed (single flyaway hairs, shadows, thin strings) stays on the plate.
Exit codes 10/11/12: model consent needed / declined / download failed (see models.py).
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2, numpy as np
from _models import session, imread, imwrite, die

N = 512          # LaMa fixed input size


def load_mask(path, H, W):
    m = imread(path, cv2.IMREAD_UNCHANGED)
    if m.ndim == 3:
        m = m[..., 3] if m.shape[2] == 4 else cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    if m.dtype != np.uint8:
        m = (m.astype(np.float32) / np.iinfo(m.dtype).max * 255).astype(np.uint8)
    h, w = m.shape
    if (h, w) != (H, W):
        if abs(w / h - W / H) > 0.01:
            die(f"mask size {w}x{h} does not match the image aspect {W}x{H}")
        print(f"! mask {w}x{h} resized to the image size {W}x{H}", file=sys.stderr)
        m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    return m


def lama_square(sess, img, hole):
    """img: HxWx3 BGR uint8 (any size), hole: HxW bool -> pad to square, run LaMa at 512, return same-size BGR uint8."""
    h, w = hole.shape
    side = max(h, w)
    py, px = side - h, side - w
    t, l = py // 2, px // 2
    if py or px:      # pad to square by mirroring image AND hole (otherwise LaMa paints the mirrored subject back in)
        img = cv2.copyMakeBorder(img, t, py - t, l, px - l, cv2.BORDER_REFLECT_101)
        hole = cv2.copyMakeBorder(hole.astype(np.uint8), t, py - t, l, px - l, cv2.BORDER_REFLECT_101).astype(bool)
    x = cv2.resize(img, (N, N), interpolation=cv2.INTER_AREA if side > N else cv2.INTER_CUBIC)
    m = cv2.resize(hole.astype(np.float32), (N, N), interpolation=cv2.INTER_AREA) > 0.01   # err on the large side
    x = np.ascontiguousarray(x[..., ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255
    y = sess.run(None, {"image": x, "mask": m[None, None].astype(np.float32)})[0][0]
    if y.max() <= 2:
        y = y * 255
    y = np.clip(y.transpose(1, 2, 0)[..., ::-1], 0, 255).astype(np.float32)
    y = cv2.resize(y, (side, side), interpolation=cv2.INTER_CUBIC if side > N else cv2.INTER_AREA)
    return np.clip(y[t:t + h, l:l + w], 0, 255).astype(np.uint8)


def plan_crop(region, W, H):
    """mask bbox -> crop with >= 15% context, close to square, at least 512 (small masks fill at native resolution)."""
    ys, xs = np.nonzero(region)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    bw, bh = x1 - x0, y1 - y0
    m = max(48, int(0.15 * max(bw, bh)))
    nw, nh = bw + 2 * m, bh + 2 * m
    S = max(N, nw, nh)
    cw, ch = min(W, S), min(H, S)
    cw = min(cw, max(ch, nw)); ch = min(ch, max(cw, nh))     # when one side hits the image edge, do not widen the other (less padding = more resolution)
    cx0 = int(np.clip((x0 + x1) // 2 - cw // 2, 0, W - cw)); cy0 = int(np.clip((y0 + y1) // 2 - ch // 2, 0, H - ch))
    return cx0, cy0, cx0 + cw, cy0 + ch


def split_groups(hole, D, d):
    """--split: one group per object. Objects = connected components of the ORIGINAL mask after closing small gaps
    (letters of one word stay together); each group's fill area is its own pixels grown by d, so a row of
    neighbours whose grown masks touch is still filled one object at a time, near native resolution."""
    k = max(2, min(d, 6))
    n, lab = cv2.connectedComponents(cv2.dilate(hole.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1))))
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * d + 1, 2 * d + 1)) if d else None
    groups = []
    for i in range(1, n):
        g = (lab == i) & hole
        if g.any():
            groups.append((cv2.dilate(g.astype(np.uint8), ker).astype(bool) & D) if d else g)
    return groups


def fill_lama(img, D, hole=None, d=0, split=False):
    H, W = D.shape
    sess = session("lama")
    if split:
        groups, whole = split_groups(hole, D, d), False
        if len(groups) > 40:
            print(f"! --split: {len(groups)} separate objects, one LaMa pass each - this may take a while", file=sys.stderr)
    else:
        # distant mask blobs are filled separately at higher resolution; earlier fills become context for later ones
        n, lab = cv2.connectedComponents(cv2.dilate(D.astype(np.uint8), np.ones((97, 97), np.uint8)))
        groups = [D & (lab == i) for i in range(1, n)]
        groups = [g for g in groups if g.any()]
        whole = D.mean() > 0.4 or len(groups) > 6
        if whole:
            groups = [D]
    groups.sort(key=lambda g: -g.sum())
    out, remaining, info = img.copy(), D.copy(), []
    for g in groups:
        x0, y0, x1, y1 = (0, 0, W, H) if whole and D.mean() > 0.4 else plan_crop(g, W, H)
        y = lama_square(sess, out[y0:y1, x0:x1], remaining[y0:y1, x0:x1])
        sel = g[y0:y1, x0:x1]
        out[y0:y1, x0:x1][sel] = y[sel]
        remaining &= ~g
        info.append(f"{'whole' if (x1 - x0, y1 - y0) == (W, H) else 'crop'} {x1 - x0}x{y1 - y0} (downscale {max(x1 - x0, y1 - y0) / N:.2f}x)")
    sc = [float(t.split("downscale ")[1].rstrip("x)")) for t in info]
    if len(info) > 4:
        info = [f"{len(info)} separate fills, downscale {min(sc):.2f}x-{max(sc):.2f}x"]
    if not split and max(sc) > 1.5 and cv2.connectedComponents(hole.astype(np.uint8))[0] > 2:
        info.append("tip: the mask holds several objects - --split fills them one by one at higher resolution")
    return out, "; ".join(info)


def fill_opencv(img, D, r):
    return cv2.inpaint(img, D.astype(np.uint8) * 255, max(3, r), cv2.INPAINT_TELEA), "TELEA"


def main():
    ap = argparse.ArgumentParser(description="erase by mask and fill the background -> same-size plate")
    ap.add_argument("img"); ap.add_argument("mask"); ap.add_argument("--out", required=True)
    ap.add_argument("--engine", choices=["lama", "opencv"], default="lama")
    ap.add_argument("--dilate", type=int, help="grow the mask by N px (default: 1%% of the diagonal, at least 8)")
    ap.add_argument("--split", action="store_true", help="lama: fill each separate object of the mask on its own, near native "
                    "resolution (a row of neighbouring objects that the grown mask would merge into one big blob)")
    a = ap.parse_args()

    img = imread(a.img); H, W = img.shape[:2]
    m = load_mask(a.mask, H, W)
    hole = m >= 4          # soft masks: faint semi-transparent hair counts too, or "ghost hair" remains
    if not hole.any():
        die("mask is empty (all black), nothing to erase")
    d = max(0, a.dilate) if a.dilate is not None else max(8, int(round(0.01 * np.hypot(H, W))))
    D = cv2.dilate(hole.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * d + 1, 2 * d + 1))) if d else hole.astype(np.uint8)
    D = D.astype(bool)
    if D.mean() > 0.95:
        die("mask covers almost the whole image, no background to reference")

    t0 = time.time()
    fill, info = fill_lama(img, D, hole, d, a.split) if a.engine == "lama" else fill_opencv(img, D, d)
    t1 = time.time()

    # composite: 100% fill inside the mask, ramp 1->0 in the grown band, untouched outside
    if d:
        dist = cv2.distanceTransform(D.astype(np.uint8), cv2.DIST_L2, 5)
        alpha = np.clip(dist / d, 0, 1)
        alpha[hole] = 1
    else:
        alpha = D.astype(np.float32)
    alpha = alpha[..., None]
    plate = np.where(D[..., None], np.round(fill * alpha + img * (1 - alpha)), img).astype(np.uint8)
    imwrite(a.out, plate)
    print(f"{a.engine}  {W}x{H}  grow {d}px  erased {D.mean() * 100:.1f}%  {info}  ({t1 - t0:.2f}s)", file=sys.stderr)
    print(a.out)


main()
