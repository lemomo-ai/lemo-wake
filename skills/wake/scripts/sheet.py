#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pillow"]
# ///
"""Contact sheet: put frames / stills side by side to judge rhythm, composition, and compare with the source.

  sheet.py <out.png> <img1> <img2> ...                     any images in a row (wraps)
  sheet.py <out.png> --stills <srcDir> 0.2 1.0 2.0 4.95    the time points rendered by render.mjs stills
  sheet.py <out.png> --frames <frames dir> --idx 0 40 80 149   by frame number (commas also work: 0,40,80,-1)
  sheet.py <out.png> --frames <frames dir> --n 8                n evenly spaced frames
  sheet.py <out.png> --vs-source <srcDir> 4.95 [--source img]   that time vs the source (fidelity check)
options: --h 360 (tile height)  --cols 6 (tiles per row)  --label (time/frame label top-left)
"""
import argparse, glob, os, sys
from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out"); ap.add_argument("items", nargs="*")
    ap.add_argument("--stills"); ap.add_argument("--frames"); ap.add_argument("--vs-source"); ap.add_argument("--source", help="with --vs-source: the source image if it is not assets/source.*")
    ap.add_argument("--idx", nargs="+", action="extend", metavar="N", help="frame numbers, space or comma separated; negative = from the end")
    ap.add_argument("--n", type=int, help="with --frames: n evenly spaced frames (default 6)"); ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--h", type=int, default=360); ap.add_argument("--cols", type=int, default=6); ap.add_argument("--label", action="store_true")
    a = ap.parse_args()
    files, labels = [], []
    if a.stills:
        for t in a.items: files.append(os.path.join(a.stills, "stills", f"t_{t}.png")); labels.append(f"{t}s")
    elif a.vs_source:
        t = a.items[0]; cands = [a.source] if a.source else sorted(glob.glob(os.path.join(a.vs_source, "assets", "source.*")))
        if not cands: sys.exit(f"source not found: {a.vs_source}/assets/source.* (pass --source <path>)")
        files = [os.path.join(a.vs_source, "stills", f"t_{t}.png"), cands[0]]
        labels = [f"{t}s", "source"]; a.cols = 2
    elif a.frames:
        fs = sorted(glob.glob(os.path.join(a.frames, "f_*.*")))
        if not fs: sys.exit(f"no frames: {a.frames}")
        toks = [v for t in (a.idx or []) + (a.items if a.idx else []) for v in t.replace("，", ",").replace(",", " ").split()]
        if a.items and not a.idx: sys.exit(f"unexpected {' '.join(a.items)} - did you mean --idx {' '.join(a.items)}?")
        if toks:
            try: ids = [int(v) if int(v) >= 0 else len(fs) + int(v) for v in toks]
            except ValueError: sys.exit(f"--idx takes frame numbers, got: {' '.join(toks)}")
            bad = [v for v in ids if not 0 <= v < len(fs)]
            if bad: sys.exit(f"frame number out of range (0..{len(fs) - 1}): {bad}")
        else: n = max(1, a.n or 6); ids = [round(i * (len(fs) - 1) / max(1, n - 1)) for i in range(n)]
        files = [fs[i] for i in ids]; labels = [f"#{i} {i / a.fps:.2f}s" for i in ids]
    else:
        files = a.items; labels = [os.path.basename(f) for f in files]
    if not files: sys.exit(__doc__)
    ims = []
    for f in files:
        if not os.path.isfile(f):
            hint = " (render that time first: node render.mjs <src> stills <t>)" if os.sep + "stills" + os.sep in f else ""
            sys.exit(f"not found: {f}{hint}")
        im = Image.open(f).convert("RGB"); ims.append(im.resize((round(im.width * a.h / im.height), a.h), Image.LANCZOS))
    cols = min(a.cols, len(ims)); rows = (len(ims) + cols - 1) // cols
    cw = max(i.width for i in ims); W, H = cols * cw + (cols - 1) * 4, rows * a.h + (rows - 1) * 4
    sheet = Image.new("RGB", (W, H), (24, 24, 24)); d = ImageDraw.Draw(sheet)
    for k, im in enumerate(ims):
        x, y = (k % cols) * (cw + 4), (k // cols) * (a.h + 4); sheet.paste(im, (x, y))
        if a.label: d.rectangle([x, y, x + 8 + 7 * len(labels[k]), y + 16], fill=(0, 0, 0)); d.text((x + 4, y + 2), labels[k], fill=(255, 255, 255))
    sheet.save(a.out); print(a.out)


main()
