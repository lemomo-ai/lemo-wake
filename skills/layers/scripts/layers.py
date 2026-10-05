#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["numpy", "pillow", "pillow-heif", "psd-tools", "opencv-python-headless"]
# ///
"""Layer pack: turn the parts lifted out of a picture into a PSD, PNG layers and layers.json.

  layers.py prep <image> <workdir>                normalise the image (HEIC, EXIF rotation) -> <workdir>/assets/source.png
                                                  (keep the masks in <workdir>/assets/ too: wake's sheet.py --parts <workdir> then shows them)
  layers.py scan <folder>                         list the images in a folder and its subfolders (or a lemo-wake project:
                                                  its src/assets/) and what each one looks like: cut-out, mask, plate, depth
  layers.py build <outdir> --source <img> [--plate <img>] [--depth <img>]
                  --layer "name=file" [--layer ...] [--order given|depth] [--names "背景,原图,景深"] [--no-psd]

build:
  --source  the picture the parts were taken from; every part must have its size (they are all source pixels).
  --plate   the clean background (everything lifted out and filled in); becomes the bottom layer.
            Without it the source itself is the bottom layer.
  --depth   depth map (near = white, 8 or 16 bit). Used to sort the layers (near on top) and stored in the pack.
  --layer   one element. The file is an RGBA cut-out or a grey mask (white = the element; the colours then
            come from the source). Repeat for each element. Names may use any language.
            At the source's size it is used as is. A smaller, already cropped cut-out needs its place:
            "name=file@x,y" (top-left in source pixels), or without @ it is looked up in the source
            (template match; fails with exit 2 if the part was repainted, scaled or rotated - then give @x,y).
  --order   given (default): the order of the --layer options, first = lowest. Decide it by looking at what
            covers what (a cap lies on the head, so it goes above the person).
            depth: sort by each element's mean depth, far below near. A quick guess for separate objects
            spread through a scene; wrong for things that sit on each other.
  --names   names of the background, source and depth layers, comma-separated, in the user's language
            (default "background,source,depth"). The source and depth layers are hidden in the PSD.
  --no-psd  skip layers.psd.

Writes into <outdir>:
  layers.psd    background, then each element as its own layer (named), plus the source and the depth map as
                hidden layers on top for comparison
  png/          00-background.png (full size), NN-<name>.png (each element cropped to its own box), source.png, depth.png
  layers.json   canvas size and, per layer: file, x, y, width, height, z (0 = bottom), mean depth (0 far .. 1 near)
  preview.png   the parts on a checkerboard, for checking by eye (plus a red "≠ source" card where the stacked
                layers do not match the source)
The JSON summary has "check": how far the stacked visible layers are from the source (pixels_off > 0.2% is
also printed as a warning: usually a reused part that was repainted or cropped for an animation).
Exit code 2 = bad input (message says which).
"""
import argparse, glob, json, os, re, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp")


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def load(path):
    if not os.path.isfile(path):
        die(f"not found: {path}")
    try:
        im = Image.open(path)
        im.load()
    except Exception as e:
        die(f"cannot read {path}: {e}")
    return im


def as_depth01(im):
    """Depth map -> float array 0..1 (near = 1)."""
    a = np.asarray(im)
    if a.ndim == 3:
        a = a[..., :3].mean(axis=2)
    a = a.astype(np.float32)
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / (hi - lo) if hi > lo else np.zeros_like(a)


def element_rgba(im, src):
    """RGBA cut-out or grey mask (source size) -> RGBA array."""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        return np.asarray(im.convert("RGBA")).copy()
    if im.mode in ("L", "I", "I;16", "I;16B", "F", "1"):
        m = np.asarray(im).astype(np.float32)
        if m.max() > 255:
            m = m / 65535.0 * 255.0
        rgba = np.asarray(src.convert("RGBA")).copy()
        rgba[..., 3] = np.clip(m, 0, 255).astype(np.uint8)
        return rgba
    die("a layer must be an RGBA cut-out or a grey mask (this one is a plain RGB image)")


def bbox(alpha, thr=3):
    ys, xs = np.nonzero(alpha >= thr)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def locate(part, src_rgb, min_score=0.9):
    """Find a cropped RGBA part in the source (masked normalised cross-correlation)."""
    import cv2
    ph, pw = part.shape[:2]
    if ph > src_rgb.shape[0] or pw > src_rgb.shape[1]:
        return None, 0.0
    mask = (part[..., 3] >= 128).astype(np.uint8)
    if mask.sum() < 16:
        return None, 0.0
    tpl = np.ascontiguousarray(part[..., :3]).astype(np.float32)
    img = np.ascontiguousarray(src_rgb).astype(np.float32)
    m3 = np.dstack([mask] * 3).astype(np.float32)
    r = cv2.matchTemplate(img, tpl, cv2.TM_CCORR_NORMED, mask=m3)
    r = np.nan_to_num(r, nan=0.0, posinf=0.0, neginf=0.0)
    _, best, _, loc = cv2.minMaxLoc(r)
    # confirm with the mean colour error under the mask (correlation alone is loose on flat colours)
    x, y = loc
    diff = np.abs(img[y:y + ph, x:x + pw] - tpl)[mask > 0].mean()
    score = float(best) * max(0.0, 1.0 - diff / 64.0)
    return ((int(x), int(y)) if score >= min_score else None), score


def place(part, at, W, H):
    """Put a cropped RGBA part onto a transparent canvas at (x, y); clipped to the canvas."""
    out = np.zeros((H, W, 4), np.uint8)
    x, y = at
    ph, pw = part.shape[:2]
    sx0, sy0 = max(0, -x), max(0, -y)
    dx0, dy0 = max(0, x), max(0, y)
    w, h = min(pw - sx0, W - dx0), min(ph - sy0, H - dy0)
    if w <= 0 or h <= 0:
        die(f"a part placed at {x},{y} lies outside the {W}x{H} canvas")
    out[dy0:dy0 + h, dx0:dx0 + w] = part[sy0:sy0 + h, sx0:sx0 + w]
    return out


def slug(name, i):
    s = re.sub(r"[\\/:*?\"<>|\s]+", "-", name.strip()).strip("-.")
    return f"{i:02d}-{s or 'layer'}"


def font(size):
    for f in ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
              "C:/Windows/Fonts/msyh.ttc", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.isfile(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()


def checker(w, h, s=12):
    y, x = np.mgrid[0:h, 0:w]
    a = np.where(((x // s) + (y // s)) % 2 == 0, 236, 204).astype(np.uint8)
    return Image.fromarray(np.dstack([a, a, a])).convert("RGBA")


# ---------------------------------------------------------------- prep

def cmd_prep(a):
    im = load(a.image)
    notes = []
    if (im.format or "").upper() in ("HEIF", "HEIC"):
        notes.append("HEIC converted")
    t = ImageOps.exif_transpose(im)
    if t.size != im.size or im.getexif().get(0x0112, 1) not in (1, None):
        notes.append("rotated upright from EXIF")
    rgba = t.convert("RGBA")
    im = rgba if np.asarray(rgba)[..., 3].min() < 255 else t.convert("RGB")
    os.makedirs(os.path.join(a.workdir, "assets"), exist_ok=True)
    out = os.path.join(a.workdir, "assets", "source.png")
    im.save(out)
    print(json.dumps({"source": out, "size": list(im.size), "mode": im.mode, "notes": notes}, ensure_ascii=False))


# ---------------------------------------------------------------- scan

def classify(path, im, src_size, src_rgb=None):
    name = os.path.basename(path).lower()
    a = np.asarray(im)
    info = {"file": path, "size": list(im.size), "mode": im.mode}
    if src_size and tuple(im.size) != tuple(src_size):
        info["kind"] = "other size"
        return info
    if name.startswith("source."):
        info["kind"] = "source"
    elif "depth" in name:
        info["kind"] = "depth"
    elif im.mode in ("RGBA", "LA"):
        al = np.asarray(im.convert("RGBA"))[..., 3]
        b = bbox(al)
        rgb = np.asarray(im.convert("RGB"))
        info["kind"] = "cut-out" if b and al.min() < 250 and rgb[al >= 128].max(initial=0) > 8 else "image"
        if b:
            info["bbox"] = list(b)
            info["coverage"] = round(float((al >= 128).mean()), 4)
    elif im.mode in ("L", "I", "I;16", "I;16B", "1"):
        m = a.astype(np.float32)
        m = m / (65535.0 if m.max() > 255 else 255.0)
        b = bbox((m * 255).astype(np.uint8))
        info["kind"] = "mask"
        if b:
            info["bbox"] = list(b)
            info["coverage"] = round(float((m >= .5).mean()), 4)
    else:
        info["kind"] = "plate?" if re.search(r"plate|clean|bg|background|empty", name) else "image"
        if src_rgb is not None:  # how much of the picture this image changed (a plate: what was lifted out)
            d = np.abs(np.asarray(im.convert("RGB")).astype(np.int16) - src_rgb).max(axis=2)
            info["differs_from_source"] = round(float((d > 24).mean()), 4)
    return info


def cmd_scan(a):
    folder = a.folder
    for sub in ("src/assets", "assets"):
        if os.path.isdir(os.path.join(folder, sub)):
            folder = os.path.join(folder, sub)
            break
    files = sorted(f for f in glob.glob(os.path.join(folder, "**", "*"), recursive=True) if f.lower().endswith(IMG_EXT))
    if not files:
        die(f"no images in {folder}")
    srcs = [f for f in files if os.path.basename(f).lower().startswith("source.")]
    src_img = load(srcs[0]) if srcs else None
    src_size = src_img.size if src_img else None
    src_rgb = np.asarray(src_img.convert("RGB")).astype(np.int16) if src_img else None
    rows = [classify(f, load(f), src_size, src_rgb) for f in files]
    print(json.dumps({"folder": folder, "source_size": list(src_size) if src_size else None, "files": rows},
                     ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- build

def cmd_build(a):
    src = load(a.source)
    W, H = src.size
    src_rgba = src.convert("RGBA")
    depth = None
    if a.depth:
        dim = load(a.depth)
        if dim.size != (W, H):
            dim = dim.resize((W, H), Image.BILINEAR)
        depth = as_depth01(dim)
    if a.plate:
        plate = load(a.plate)
        if plate.size != (W, H):
            die(f"plate is {plate.size[0]}x{plate.size[1]}, source is {W}x{H}")
        plate = plate.convert("RGBA")
    else:
        plate = src_rgba

    if not a.layer:
        die("give at least one --layer name=file")
    elems = []
    for i, spec in enumerate(a.layer):
        if "=" not in spec:
            die(f'--layer needs "name=file", got: {spec}')
        name, f = spec.split("=", 1)
        at = None
        m = re.match(r"^(.*)@(-?\d+),(-?\d+)$", f)
        if m and not os.path.isfile(f):
            f, at = m.group(1), (int(m.group(2)), int(m.group(3)))
        im = load(f)
        if im.size == (W, H) and at is None:
            rgba = element_rgba(im, src)
        else:
            if im.mode not in ("RGBA", "LA", "P"):
                die(f"layer {name!r}: a cropped part must be an RGBA cut-out")
            part = np.asarray(im.convert("RGBA"))
            if at is None:
                at, score = locate(part, np.asarray(src.convert("RGB")))
                if at is None:
                    die(f"layer {name!r}: could not find this {im.size[0]}x{im.size[1]} part in the source "
                        f"(best match {score:.2f}); give its place as {name}={f}@x,y")
                print(f"layer {name!r}: found at {at[0]},{at[1]} (match {score:.2f})", file=sys.stderr)
            rgba = place(part, at, W, H)
        b = bbox(rgba[..., 3])
        if b is None:
            die(f"layer {name!r} is empty")
        d = None
        if depth is not None:
            w = rgba[..., 3].astype(np.float32) / 255.0
            d = float((depth * w).sum() / max(w.sum(), 1e-6))
        elems.append({"name": name.strip(), "rgba": rgba, "box": b, "depth": d, "given": i})

    order = a.order or "given"
    names = [n.strip() for n in a.names.split(",")] + ["background", "source", "depth"][len(a.names.split(",")):]
    bg_name, src_name, depth_name = names[:3]
    if order == "depth":
        if depth is None:
            die("--order depth needs --depth")
        elems.sort(key=lambda e: (e["depth"], e["given"]))
    else:
        elems.sort(key=lambda e: e["given"])

    out = a.outdir
    pdir = os.path.join(out, "png")
    os.makedirs(pdir, exist_ok=True)
    for f in glob.glob(os.path.join(pdir, "*.png")):
        os.remove(f)

    layers = []
    plate.save(os.path.join(pdir, "00-background.png"))
    layers.append({"name": bg_name, "file": "png/00-background.png", "x": 0, "y": 0, "width": W, "height": H,
                   "z": 0, "kind": "background"})
    for z, e in enumerate(elems, 1):
        x0, y0, x1, y1 = e["box"]
        fn = slug(e["name"], z) + ".png"
        Image.fromarray(e["rgba"][y0:y1, x0:x1]).save(os.path.join(pdir, fn))
        row = {"name": e["name"], "file": f"png/{fn}", "x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0,
               "z": z, "kind": "element"}
        if e["depth"] is not None:
            row["depth"] = round(e["depth"], 3)
        layers.append(row)
    src.convert("RGB").save(os.path.join(pdir, "source.png"))
    meta = {"canvas": {"width": W, "height": H}, "source": "png/source.png", "layers": layers,
            "note": "x, y = top-left in canvas pixels; z = stacking order, 0 = bottom; depth = mean depth, 0 far .. 1 near",
            "generator": "lemo-wake layers"}
    if depth is not None:
        Image.fromarray((depth * 255).round().astype(np.uint8)).save(os.path.join(pdir, "depth.png"))
        meta["depth"] = "png/depth.png"
    with open(os.path.join(out, "layers.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)

    # composite (also the PSD's merged preview), checked against the source
    comp = plate.copy()
    for e in elems:
        comp.alpha_composite(Image.fromarray(e["rgba"]))
    diff = np.abs(np.asarray(comp.convert("RGB")).astype(np.int16) - np.asarray(src.convert("RGB")).astype(np.int16)).max(axis=2)
    off = diff > 24
    check = {"mean_diff": round(float(diff.mean()), 2), "pixels_off": round(float(off.mean()), 4)}
    if off.any():
        ys, xs = np.nonzero(off)
        check["off_box"] = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]

    psd_path = None
    if not a.no_psd:
        psd_path = os.path.join(out, "layers.psd")
        write_psd(psd_path, W, H, plate, elems, src, depth, comp, (bg_name, src_name, depth_name))

    preview(os.path.join(out, "preview.png"), comp, plate, elems, depth, (bg_name, src_name, depth_name), off)

    if check["pixels_off"] > 0.002:
        print(f"check: {check['pixels_off']:.1%} of the pixels differ from the source when the visible layers are stacked "
              f"(box {check.get('off_box')}): a part is incomplete or misplaced - see the red areas in preview.png", file=sys.stderr)
    print(json.dumps({"out": out, "psd": psd_path, "order": order, "check": check, "layers": [
        {k: v for k, v in r.items() if k in ("name", "file", "x", "y", "width", "height", "z", "depth")} for r in layers]},
        ensure_ascii=False, indent=1))


def write_psd(path, W, H, plate, elems, src, depth, comp, names):
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer
    psd = PSDImage.new("RGBA", (W, H))  # RGBA: cut-out alpha becomes layer transparency, not a mask

    def add(im, name, top=0, left=0, visible=True):
        lay = PixelLayer.frompil(im, psd, "layer", top, left)  # (image, psd, name, top, left); RLE by default
        lay.name = name  # the setter also stores the Unicode name (non-Latin names need it)
        lay.visible = visible
        psd.append(lay)

    add(plate.convert("RGB"), names[0])
    for e in elems:
        x0, y0, x1, y1 = e["box"]
        add(Image.fromarray(e["rgba"][y0:y1, x0:x1]), e["name"], y0, x0)
    add(src.convert("RGB"), names[1], visible=False)
    if depth is not None:
        add(Image.fromarray((depth * 255).round().astype(np.uint8)).convert("RGB"), names[2], visible=False)
    try:  # store the merged image so viewers that only read it (Quick Look, thumbnails) show the picture
        hdr = psd._record.header
        px = np.asarray(comp.convert("RGBA"))
        psd._record.image_data.set_data([px[..., c].tobytes() for c in range(min(hdr.channels, 4))], hdr)
    except Exception:
        pass
    psd.save(path)


def preview(path, comp, plate, elems, depth, names, off=None):
    W, H = comp.size
    tile = 360
    k = tile / max(W, H)
    tw, th = max(1, round(W * k)), max(1, round(H * k))
    cards = [("composite", comp)]
    if off is not None and off.mean() > 0.002:
        red = np.asarray(comp.convert("RGBA")).copy()
        red[..., :3] = (red[..., :3] * 0.35).astype(np.uint8)
        red[off] = (255, 40, 40, 255)
        cards.append(("≠ source", Image.fromarray(red)))
    cards.append((names[0], plate))
    for z, e in enumerate(elems, 1):
        cards.append((f"{z}. {e['name']}", Image.fromarray(e["rgba"])))
    if depth is not None:
        cards.append((names[2], Image.fromarray((depth * 255).round().astype(np.uint8)).convert("RGBA")))
    cols = min(4, len(cards))
    rows = (len(cards) + cols - 1) // cols
    pad, lab = 16, 30
    sheet = Image.new("RGBA", (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad), (250, 250, 248, 255))
    dr = ImageDraw.Draw(sheet)
    fnt = font(18)
    for i, (label, im) in enumerate(cards):
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + lab + pad)
        bg = checker(tw, th)
        bg.alpha_composite(im.resize((tw, th), Image.LANCZOS))
        sheet.paste(bg, (x, y + lab))
        dr.text((x, y + 4), label, fill=(40, 40, 40, 255), font=fnt)
    sheet.convert("RGB").save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("prep"); p.add_argument("image"); p.add_argument("workdir")
    p = sp.add_parser("scan"); p.add_argument("folder")
    p = sp.add_parser("build"); p.add_argument("outdir")
    p.add_argument("--source", required=True); p.add_argument("--plate"); p.add_argument("--depth")
    p.add_argument("--layer", action="append"); p.add_argument("--order", choices=["depth", "given"])
    p.add_argument("--names", default="background,source,depth"); p.add_argument("--no-psd", action="store_true")
    a = ap.parse_args()
    {"prep": cmd_prep, "scan": cmd_scan, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    main()
