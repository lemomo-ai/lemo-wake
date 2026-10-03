#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["numpy", "opencv-python-headless"]
# ///
"""Measure the source: coordinate grid, colour-block bounds, palette. All coordinates are source pixels (= design coordinates).
Usage: measure.py <command> <img> [options]   (measure the project copy <src>/assets/source.*, not the user's original)

  measure.py info    <img>                              size + aspect (the film has the same size)
  measure.py grid    <img> [out.png] [--step 25]        overlay a coordinate grid (1.5x, easy to read); without out
                                                        (or --out) it is written next to the image as <name>-grid.png
  measure.py runs    <img> --rows y0:y1 [--dark 60 | --color #d8452a --tol 60]
                                                        runs of the matching colour in that horizontal band
                                                        -> left/right bounds of letters/blocks
  measure.py vruns   <img> --cols x0:x1 [same options]  same, vertical -> top/bottom bounds
  measure.py bbox    <img> --color #hex [--tol 60] [--region x0,y0,x1,y1]   bounding box of a colour region
                     (without --color: pixels darker than --dark)
  measure.py palette <img> [--k 8]                      main colours (hex + share)
"""
import argparse, os, sys
import cv2, numpy as np

CMDS = ("info", "grid", "runs", "vruns", "bbox", "palette")


def load(p):
    try:
        im = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)   # works with non-ASCII paths too
    except OSError:
        im = None
    if im is None:
        sys.exit(f"cannot read image: {p}")
    return im


def grid_out(a):
    out = a.out or a.out_opt
    if not out:
        base, _ = os.path.splitext(a.img)
        out = base + "-grid.png"         # not "source.*": other scripts glob assets/source.*
    if os.path.splitext(out)[1].lower() not in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        out += ".png"
    return out


def mask_of(im, a):
    if a.color:
        h = a.color.lstrip('#'); rgb = np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float)
        d = np.linalg.norm(im[..., ::-1].astype(float) - rgb, axis=2)
        return d < a.tol
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    return g < a.dark


def runs(prof, thr=0.5):
    out, on = [], False
    for i, v in enumerate(prof):
        if v > thr and not on: on, s = True, i
        if v <= thr and on: on = False; out.append((s, i))
    if on: out.append((s, len(prof)))
    return [r for r in out if r[1] - r[0] >= 2]


def main():
    ap = argparse.ArgumentParser(prog="measure.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 usage="measure.py {info,grid,runs,vruns,bbox,palette} <img> [out.png] [options]")
    ap.add_argument('cmd', choices=CMDS, metavar='command'); ap.add_argument('img'); ap.add_argument('out', nargs='?', help='grid only: output image')
    ap.add_argument('--out', dest='out_opt', help='grid only: output image (same as the positional out)')
    ap.add_argument('--step', type=int, default=25); ap.add_argument('--rows'); ap.add_argument('--cols')
    ap.add_argument('--dark', type=int, default=60); ap.add_argument('--color'); ap.add_argument('--tol', type=float, default=60)
    ap.add_argument('--region'); ap.add_argument('--k', type=int, default=8)
    a = ap.parse_args()
    if a.cmd == 'runs' and not a.rows: ap.error("runs needs --rows y0:y1")
    if a.cmd == 'vruns' and not a.cols: ap.error("vruns needs --cols x0:x1")
    if a.out and a.cmd != 'grid': ap.error(f"unexpected argument {a.out!r} ({a.cmd} takes no output file)")
    im = load(a.img); H, W = im.shape[:2]
    if a.cmd == 'info':
        print(f"src {W}x{H}  aspect {W/H:.4f}  (the film is rendered at this same size)")
    elif a.cmd == 'grid':
        f = 1.5; g = cv2.resize(im, None, fx=f, fy=f)
        for x in range(0, W, a.step):
            major = x % (a.step * 4) == 0
            cv2.line(g, (int(x*f), 0), (int(x*f), g.shape[0]), (0, 0, 255) if major else (200, 200, 0), 1)
            if major: cv2.putText(g, str(x), (int(x*f)+2, 14), 0, .45, (0, 0, 255), 1)
        for y in range(0, H, a.step):
            major = y % (a.step * 4) == 0
            cv2.line(g, (0, int(y*f)), (g.shape[1], int(y*f)), (0, 0, 255) if major else (200, 200, 0), 1)
            if major: cv2.putText(g, str(y), (2, int(y*f)-3), 0, .45, (0, 0, 255), 1)
        out = grid_out(a); ok, buf = cv2.imencode(os.path.splitext(out)[1], g)
        if not ok: sys.exit(f"cannot encode {out}")
        try: buf.tofile(out)
        except OSError as e: sys.exit(f"cannot write {out}: {e} (pass an output path you can write, e.g. <proj>/grid.png)")
        print(out)
    elif a.cmd in ('runs', 'vruns'):
        m = mask_of(im, a)
        if a.cmd == 'runs':
            y0, y1 = map(int, a.rows.split(':')); print(runs(m[y0:y1].mean(0)))
        else:
            x0, x1 = map(int, a.cols.split(':')); print(runs(m[:, x0:x1].mean(1)))
    elif a.cmd == 'bbox':
        m = mask_of(im, a)
        if a.region:
            x0, y0, x1, y1 = map(int, a.region.split(',')); r = np.zeros_like(m); r[y0:y1, x0:x1] = True; m &= r
        ys, xs = np.nonzero(m)
        print('no match' if not len(xs) else f"x {xs.min()}–{xs.max()}  y {ys.min()}–{ys.max()}  px={len(xs)}")
    elif a.cmd == 'palette':
        z = cv2.resize(im, (200, int(200*H/W))).reshape(-1, 3).astype(np.float32)
        _, lab, cen = cv2.kmeans(z, a.k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1), 3, cv2.KMEANS_PP_CENTERS)
        cnt = np.bincount(lab.ravel(), minlength=a.k)
        for i in np.argsort(-cnt):
            b, g, r = cen[i].astype(int); print(f"#{r:02x}{g:02x}{b:02x}  {cnt[i]/cnt.sum()*100:.1f}%")


main()
