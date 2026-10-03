#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["numpy", "opencv-python-headless", "onnxruntime"]
# ///
"""Cut out the subject / pick elements -> 8-bit soft-edged mask (white = selected), same size as the image.
Runs on the local CPU; models are downloaded once after the user's one-time consent (see models.py).

  segment.py <img> --out mask.png                          main subject (general)
  segment.py <img> --out mask.png --model portrait         person (keeps semi-transparent hair)
  segment.py <img> --out mask.png --point 960,400          pick one element (points/boxes switch to sam)
  segment.py <img> --out mask.png --point 960,400 925,690  several points = parts of the SAME thing (popsicle + stick)
  segment.py <img> --out mask.png --point 620,450 960,400 1360,450 --each   each point picks its own thing, merged
  segment.py <img> --out mask.png --point 960,400 --neg 925,690            negative point: exclude this part
  segment.py <img> --out mask.png --box 20,30,960,360                      box select (sam; good for titles/text blocks)
  segment.py <img> --out mask.png --box 20,30,300,360 --box 400,30,700,360  several boxes = several objects, merged
                                    (also fine: --box 20,30,300,360 400,30,700,360, or one quoted string with both;
                                     in zsh an unquoted $BOXES does not split - write the boxes out or quote one string)
  segment.py <img> --out mask.png --model general --box 1080,480,1660,820  run the matting model inside a box (softer edges)
  other: --cutout cut.png also saves an RGBA cut-out; --hard outputs a binary mask. stderr prints coverage and bbox.

Models (coordinates are source pixels, same as measure.py):
  general   BiRefNet-lite (224 MB). Takes "the most salient group": on a poster usually the whole product group
            (with stand and garnish); in a landscape maybe just one small person. Use sam or --box for a specific element. ~2-4 s.
  portrait  MODNet (26 MB). Portrait matting, keeps flyaway hair better than general; useless without a person. ~0.2 s.
  sam       MobileSAM (44 MB). Selects "this one thing" from points/boxes; edges a bit harder. One click often gets
            only part of an object (popsicle without stick) - add a point on the missing part. Encode ~0.3 s, each prompt < 0.05 s.
Exit code 2 = empty mask. 10/11/12 = model consent needed / declined / download failed (see models.py).
"""
import argparse, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2, numpy as np
from _models import session, imread, imwrite, die

IMNET_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
IMNET_STD = np.array([0.229, 0.224, 0.225], np.float32)


def run1(sess, x):
    return sess.run(None, {sess.get_inputs()[0].name: x})[0]


def to_chw(rgb01):
    return np.ascontiguousarray(rgb01.transpose(2, 0, 1)[None].astype(np.float32))


# ---------- whole-image models ----------
def seg_birefnet(rgb):
    H, W = rgb.shape[:2]
    x = cv2.resize(rgb, (1024, 1024), interpolation=cv2.INTER_AREA if max(H, W) > 1024 else cv2.INTER_CUBIC)
    x = (x.astype(np.float32) / 255 - IMNET_MEAN) / IMNET_STD
    y = run1(session("birefnet-lite"), to_chw(x)).squeeze()          # logits
    y = 1 / (1 + np.exp(-np.clip(y, -30, 30)))
    return cv2.resize(y.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)


def seg_modnet(rgb, ref=512):
    H, W = rgb.shape[:2]
    s = ref / min(H, W)
    if max(H, W) * s > ref * 3:
        s = ref * 3 / max(H, W)
    h, w = max(32, int(H * s) // 32 * 32), max(32, int(W * s) // 32 * 32)
    x = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA if h < H else cv2.INTER_CUBIC)
    x = x.astype(np.float32) / 127.5 - 1
    y = run1(session("modnet"), to_chw(x)).squeeze()
    return cv2.resize(y.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)


FULL = {"general": seg_birefnet, "portrait": seg_modnet}


def seg_in_box(fn, rgb, box):
    """Run a whole-image model inside a box: 15% margin as context, zero outside the box."""
    H, W = rgb.shape[:2]
    x0, y0, x1, y1 = box
    m = int(0.15 * max(x1 - x0, y1 - y0))
    cx0, cy0, cx1, cy1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
    out = np.zeros((H, W), np.float32)
    out[cy0:cy1, cx0:cx1] = fn(rgb[cy0:cy1, cx0:cx1])
    keep = np.zeros_like(out); keep[y0:y1, x0:x1] = 1
    return out * keep


# ---------- SAM ----------
class Sam:
    """MobileSAM: encode once, then every point/box prompt only runs the fast decoder."""
    def __init__(self, rgb):
        self.H, self.W = rgb.shape[:2]
        self.s = 1024 / max(self.H, self.W)            # long side to 1024; the encoder normalizes and pads internally
        h, w = int(round(self.H * self.s)), int(round(self.W * self.s))
        x = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA if self.s < 1 else cv2.INTER_LINEAR).astype(np.float32)
        enc, self.dec = session("mobilesam-encoder"), session("mobilesam-decoder")
        self.emb = run1(enc, x)

    def __call__(self, pos=(), neg=(), box=None):
        pts, lab = [], []
        for p in pos: pts.append(p); lab.append(1)
        for p in neg: pts.append(p); lab.append(0)
        if box is not None:
            pts += [box[:2], box[2:]]; lab += [2, 3]
        else:
            pts.append((0, 0)); lab.append(-1)
        coords = np.array(pts, np.float32)[None] * self.s
        out = self.dec.run(None, {
            "image_embeddings": self.emb, "point_coords": coords,
            "point_labels": np.array(lab, np.float32)[None],
            "mask_input": np.zeros((1, 1, 256, 256), np.float32), "has_mask_input": np.zeros(1, np.float32),
            "orig_im_size": np.array([self.H, self.W], np.float32)})
        masks, iou = out[0][0], out[1][0]          # (K,H,W) logits, (K,)
        if len(iou) > 1:
            # single point is ambiguous: take the best of 3 candidates; several points/box: use output 0
            k = 1 + int(np.argmax(iou[1:])) if (len(pos) + len(neg) == 1 and box is None) else 0
        else:
            k = 0
        return masks[k], float(iou[k])


NUM = re.compile(r"-?\d+(?:\.\d+)?")


def parse_groups(tokens, n, flag):
    """All values given to a repeatable flag -> list of n-tuples. Tolerant: commas, spaces, semicolons, brackets,
    full-width commas, one quoted string holding several boxes ("10,20,300,400 500,20,800,400") or one box per flag."""
    text = " ".join(tokens).replace("，", ",")
    if not text.strip():
        return []
    v = [float(x) for x in NUM.findall(text)]
    if not v or len(v) % n:
        die(f"bad {flag} values: {text!r} - expected groups of {n} numbers "
            f"({'x,y' if n == 2 else 'x0,y0,x1,y1'}), got {len(v)} number(s)")
    return [v[i:i + n] for i in range(0, len(v), n)]


def main():
    ap = argparse.ArgumentParser(description="cut out subject / pick elements -> 8-bit soft mask")
    ap.add_argument("img"); ap.add_argument("--out", required=True)
    ap.add_argument("--model", choices=["general", "portrait", "sam"])
    ap.add_argument("--point", nargs="+", action="extend", default=[], metavar="X,Y")
    ap.add_argument("--neg", nargs="+", action="extend", default=[], metavar="X,Y")
    ap.add_argument("--box", nargs="+", action="extend", default=[], metavar="X0,Y0,X1,Y1")
    ap.add_argument("--each", action="store_true", help="each positive point / box selects its own object, then merge")
    ap.add_argument("--cutout"); ap.add_argument("--hard", action="store_true")
    a = ap.parse_args()

    bgr = imread(a.img); H, W = bgr.shape[:2]; rgb = np.ascontiguousarray(bgr[..., ::-1])
    pos = parse_groups(a.point, 2, "--point"); neg = parse_groups(a.neg, 2, "--neg")
    boxes = []
    for b in parse_groups(a.box, 4, "--box"):
        x0, y0, x1, y1 = b
        x0, x1 = sorted((max(0, min(W, x0)), max(0, min(W, x1)))); y0, y1 = sorted((max(0, min(H, y0)), max(0, min(H, y1))))
        if x1 - x0 < 4 or y1 - y0 < 4:
            die(f"box too small or outside the image: {b}")
        boxes.append([x0, y0, x1, y1])
    for x, y in pos + neg:
        if not (0 <= x < W and 0 <= y < H):
            die(f"point {x:g},{y:g} is outside the image ({W}x{H})")
    model = a.model or ("sam" if (pos or boxes) else "general")
    t0 = time.time()

    if model == "sam":
        if not pos and not boxes:
            die("sam needs --point or --box")
        sam = Sam(rgb)
        jobs = []
        if a.each:
            jobs = [dict(pos=[p], neg=neg) for p in pos] + [dict(neg=neg, box=b) for b in boxes]
        elif len(boxes) > 1:
            jobs = [dict(pos=pos, neg=neg, box=boxes[0])] + [dict(neg=neg, box=b) for b in boxes[1:]]
        else:
            jobs = [dict(pos=pos, neg=neg, box=boxes[0] if boxes else None)]
        mask = np.zeros((H, W), np.float32)
        for j in jobs:
            logit, score = sam(**j)
            print(f"  sam candidate score {score:.2f}", file=sys.stderr)
            # SAM logits near 0 mean "unsure"; a plain sigmoid leaves ghosting, x4 keeps only a 1-2 px antialiased edge
            mask = np.maximum(mask, 1 / (1 + np.exp(-np.clip(logit * 4, -30, 30))))
    else:
        if pos or neg:
            die(f"the {model} model takes no point prompts; use --model sam for points")
        fn = FULL[model]
        if boxes:
            mask = np.zeros((H, W), np.float32)
            for b in boxes:
                mask = np.maximum(mask, seg_in_box(fn, rgb, [int(round(v)) for v in b]))
        else:
            mask = fn(rgb)
    t1 = time.time()

    mask = np.clip(mask, 0, 1)
    if a.hard:
        mask = (mask > 0.5).astype(np.float32)
    m8 = np.round(mask * 255).astype(np.uint8)
    imwrite(a.out, m8)
    if a.cutout:
        imwrite(a.cutout, np.dstack([bgr, m8]))
    on = m8 > 127
    if not on.any():
        die(f"mask is empty ({model} found nothing) - try another model, more points or a box. Wrote {a.out}", 2)
    ys, xs = np.nonzero(on)
    bb = f"bbox {xs.min()},{ys.min()},{xs.max() + 1},{ys.max() + 1}"
    print(f"{model}  {W}x{H}  coverage {on.mean() * 100:.1f}%  {bb}  ({t1 - t0:.2f}s incl. model loading)", file=sys.stderr)
    print(a.out)


main()
