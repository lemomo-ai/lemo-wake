#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pillow", "pillow-heif"]
# ///
"""Create a new animation project: normalize the source image, copy the template, write config.js.

  new_project.py <image> <slug> [--dur 5] [--fps 30] [--parent .] [--max-long 2560] [--out 16:9 | 1920x1080]

Creates <parent>/<slug>-alive/src/{index.html, lib.js, fx.js, config.js, fonts.css, assets/source.(png|jpg), fonts/}

The output size is the user's choice (ask in step 1). By default the canvas (= design coordinates = output size of
every deliverable) is the source image's own pixel size and aspect ratio.
  --out W:H    another aspect ratio; the long side stays the source's long side (1086x1448 --out 16:9 -> 1448x814)
  --out WxH    an exact pixel size
  With --out the design coordinates are the OUTPUT pixels (CFG.srcW x CFG.srcH = outW x outH) and CFG.img holds the
  source size; the template places the source centred and fitted as a placeholder. How the picture uses the new
  frame is your design. Without --out, design coordinates = source pixels, as before.
Normalization done here once (all later coordinates refer to assets/source.*):
  - HEIC/HEIF (iPhone default) -> regular image
  - EXIF orientation -> pixels rotated upright
  - long side > --max-long (default 2560) -> scaled down proportionally. This is a performance guard for
    12-48 MP phone photos (render time, memory, file size). Use --max-long 0 to keep full resolution.
    The original size is recorded in config.js (CFG.orig) and reported.
  - alpha channel -> PNG, otherwise high-quality JPG
--dur is the render length. A frame-level reset transition (reset.py) is appended after it, so for a
~5 s film with a 0.5 s reset use --dur 4.5; with an in-picture ending --dur is the whole film.
To change the length later, edit `dur` in <src>/config.js and re-render.
"""
import argparse, os, re, shutil, sys
from PIL import Image, ImageOps

try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("img"); ap.add_argument("slug")
    ap.add_argument("--dur", type=float, default=5); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--parent", default=".")
    ap.add_argument("--max-long", type=int, default=2560, help="shrink only if the long side exceeds this (0 = never)")
    ap.add_argument("--out", help="output size the user picked: an aspect ratio W:H (16:9, 9:16, 1:1, 3:4) or exact WxH pixels")
    a = ap.parse_args()
    if not os.path.isfile(a.img): sys.exit(f"image not found: {a.img}")
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proj = os.path.join(os.path.abspath(a.parent), f"{a.slug}-alive"); src = os.path.join(proj, "src")
    if os.path.exists(os.path.join(src, "index.html")): sys.exit(f"already exists: {src} (pick another slug or delete it)")
    os.makedirs(os.path.join(src, "assets"), exist_ok=True); os.makedirs(os.path.join(src, "fonts"), exist_ok=True)

    im = Image.open(a.img); notes = []
    if (im.format or "").upper() in ("HEIF", "HEIC"): notes.append("HEIC converted")
    t = ImageOps.exif_transpose(im)
    if t.size != im.size or (im.getexif().get(0x0112, 1) not in (1, None)): notes.append("rotated upright from EXIF")
    im = t
    orig = im.size
    alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    im = im.convert("RGBA" if alpha else "RGB")
    if a.max_long and max(im.size) > a.max_long:
        s = a.max_long / max(im.size)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        notes.append(f"{orig[0]}x{orig[1]} scaled to {im.width}x{im.height} for speed (--max-long 0 keeps full size)")
    ext = "png" if alpha or a.img.lower().endswith(".png") else "jpg"
    dst = os.path.join(src, "assets", f"source.{ext}")
    im.save(dst, quality=95, subsampling=0) if ext == "jpg" else im.save(dst)

    for f in ("index.html", "lib.js", "fx.js"): shutil.copy(os.path.join(skill, "assets", "template", f), src)
    W, H = im.size
    OW, OH = W, H
    if a.out:
        m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([:x])\s*(\d+(?:\.\d+)?)\s*", a.out.lower())
        if not m: sys.exit(f"--out: use W:H (16:9) or WxH (1920x1080), got {a.out!r}")
        p, kind, q = float(m.group(1)), m.group(2), float(m.group(3))
        if kind == "x": OW, OH = int(p), int(q)
        else:
            L = max(W, H); r = p / q
            OW, OH = (L, round(L / r)) if r >= 1 else (round(L * r), L)
        OW, OH = OW // 2 * 2, OH // 2 * 2                      # H.264 wants even sides
    with open(os.path.join(src, "config.js"), "w") as fh:
        fh.write("// orig = the user's original pixel size before any --max-long shrink.\n")
        if (OW, OH) == (W, H):
            fh.write("// design coordinates = source pixels (srcW x srcH); output canvas outW x outH = the same size.\n")
            fh.write(f"window.CFG = {{ srcW: {W}, srcH: {H}, outW: {W}, outH: {H}, orig: [{orig[0]}, {orig[1]}], "
                     f"dur: {a.dur:g}, fps: {a.fps}, source: 'assets/source.{ext}' }};\n")
        else:
            fh.write("// output size picked by the user: design coordinates = output pixels (srcW x srcH = outW x outH);\n")
            fh.write("// img = the source image's pixel size (assets/source.*). The frame is yours to design.\n")
            fh.write(f"window.CFG = {{ srcW: {OW}, srcH: {OH}, outW: {OW}, outH: {OH}, img: [{W}, {H}], orig: [{orig[0]}, {orig[1]}], "
                     f"dur: {a.dur:g}, fps: {a.fps}, source: 'assets/source.{ext}' }};\n")
    open(os.path.join(src, "fonts.css"), "a").close()
    print(f"project: {proj}")
    size = f"canvas {W}x{H} (same as source)" if (OW, OH) == (W, H) else f"canvas {OW}x{OH} (output size picked; source {W}x{H} is CFG.img)"
    print(f"{size}, {a.dur:g}s @{a.fps}fps" + (f" ({'; '.join(notes)})" if notes else ""))


main()
