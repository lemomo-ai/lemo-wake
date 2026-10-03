#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["numpy", "opencv-python-headless", "onnxruntime"]
# ///
"""Monocular depth map: Depth Anything V2 Small (ONNX on the local CPU; ~99 MB, downloaded once after the
user's one-time consent - see models.py).

  depth.py <img> --out depth.png [--size 518] [--preview depth_preview.jpg]

Output: 16-bit grey PNG, same size as the image, near = white, far = black, normalized to 0..65535
(relative depth, not metres).
  --size     inference short side (rounded to a multiple of 14). 518 = training size, most stable; 700-1000
             gives finer edges but is slower and large flat areas can become uneven.
  --preview  also save an 8-bit false-colour preview (for eyeballing only).
Reading it: only relative order matters. Sky / flat backgrounds go to the far end; flat graphic elements
(text, stickers) are not understood - their depth follows whatever is underneath.
Exit codes 10/11/12: model consent needed / declined / download failed (see models.py).
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2, numpy as np
from _models import session, imread, imwrite, die

MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def infer_size(H, W, short):
    s = short / min(H, W)
    if max(H, W) * s > short * 3:                     # very long strips: cap the long side to save memory
        s = short * 3 / max(H, W)
    return max(14, int(round(H * s / 14)) * 14), max(14, int(round(W * s / 14)) * 14)


def main():
    ap = argparse.ArgumentParser(description="Depth Anything V2 Small -> 16-bit depth PNG (near = white)")
    ap.add_argument("img"); ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=518); ap.add_argument("--preview")
    a = ap.parse_args()
    if a.size < 140:
        die("--size too small (>= 140)")

    im = imread(a.img); H, W = im.shape[:2]
    h, w = infer_size(H, W, a.size)
    t0 = time.time()
    sess = session("depth-anything-v2-small")
    x = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA if h < H else cv2.INTER_CUBIC)
    x = (x[..., ::-1].astype(np.float32) / 255 - MEAN) / STD
    x = np.ascontiguousarray(x.transpose(2, 0, 1)[None])
    t1 = time.time()
    d = sess.run(None, {sess.get_inputs()[0].name: x})[0].squeeze().astype(np.float32)   # disparity: larger = nearer
    t2 = time.time()

    d = cv2.resize(d, (W, H), interpolation=cv2.INTER_CUBIC)   # back to source resolution
    lo, hi = float(d.min()), float(d.max())
    if hi - lo < 1e-6:
        die("depth map is flat (solid-colour image?)")
    d = (d - lo) / (hi - lo)
    imwrite(a.out, np.round(np.clip(d, 0, 1) * 65535).astype(np.uint16))
    if a.preview:
        imwrite(a.preview, cv2.applyColorMap(np.round(d * 255).astype(np.uint8), cv2.COLORMAP_INFERNO),
                [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"depth {W}x{H} (inference {w}x{h}, {t2 - t1:.2f}s, {t2 - t0:.2f}s incl. loading)", file=sys.stderr)
    print(a.out)


main()
