#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow>=10"]
# ///
"""Prepare one film for the lemo-wake community gallery. Nothing is uploaded here.

    prepare.py <film.webp|film.gif> --title T [--title-en T] --category C --author A --out DIR --agree
               [--author-url URL] [--source IMAGE] [--notes NOTES.md] [--slug S] [--version V]

Writes DIR/films/<id>/:
  film.webp|film.gif   the film, at most 8 MB (a bigger WebP is re-compressed, floor 12 fps / q50)
  preview.webp         gallery thumbnail, long side 360, at most 1 MB
  source.jpg           optional original, long side <= 1600, all metadata removed
  notes.md             optional, at most 20 KB
  meta.json
and prints a JSON summary (files, sizes, warnings) on stdout.
"""
import argparse, datetime, json, re, shutil, sys, unicodedata
from pathlib import Path
from PIL import Image, ImageOps, ImageSequence

CATEGORIES = ["life", "people", "poster", "brand", "data", "social", "sticker", "art"]
FILM_MAX, PREVIEW_MAX, SOURCE_MAX, NOTES_MAX = 8_000_000, 1_000_000, 2_000_000, 20_000
WEBP_TIERS = [(15, 80), (15, 72), (15, 64), (12, 60), (12, 55), (12, 50)]  # (fps cap, quality); floor 12 fps / q50
PRIVATE = [(r"[\w.+-]+@[\w-]+\.[\w.-]+", "an email address"),
           (r"(?<!\d)(?:\+?\d[\d -]{8,}\d)(?!\d)", "a phone-like number"),
           (r"(?:/Users/|/home/|[A-Za-z]:\\\\Users\\\\)\S+", "a local file path")]


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def frames_of(path):
    """All frames as RGBA with their durations (ms)."""
    im = Image.open(path)
    out = []
    for f in ImageSequence.Iterator(im):
        out.append((f.convert("RGBA"), f.info.get("duration", im.info.get("duration", 66)) or 66))
    return out


def resample(frames, fps_cap):
    """Drop frames so the film plays at <= fps_cap, keeping the total length."""
    total = sum(d for _, d in frames)
    native = len(frames) * 1000 / total if total else 15
    if native <= fps_cap + 0.5:
        return frames
    step = 1000 / fps_cap
    out, t, next_t = [], 0.0, 0.0
    for f, d in frames:
        if t >= next_t - 1e-6:
            out.append([f, 0])
            next_t += step
        out[-1][1] += d
        t += d
    return [(f, int(round(d))) for f, d in out]


def save_webp(frames, path, quality, size=None):
    fr = [(f if size is None else f.resize(size, Image.LANCZOS)) for f, _ in frames]
    fr[0].save(path, "WEBP", save_all=True, append_images=fr[1:], duration=[d for _, d in frames],
               loop=0, quality=quality, method=4)
    return path.stat().st_size


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:32]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("film")
    ap.add_argument("--title", required=True)
    ap.add_argument("--title-en", default="", help="optional English title (the gallery is bilingual)")
    ap.add_argument("--category", required=True, choices=CATEGORIES)
    ap.add_argument("--author", required=True)
    ap.add_argument("--author-url", default="")
    ap.add_argument("--source")
    ap.add_argument("--notes")
    ap.add_argument("--slug", help="short ascii name for the folder id (default: from the film file name)")
    ap.add_argument("--version", default="1.0.0", help="lemo-wake version that made the film")
    ap.add_argument("--out", required=True)
    ap.add_argument("--agree", action="store_true",
                    help="the user agreed to CC BY-NC 4.0 and to the project showing the film (required)")
    a = ap.parse_args()
    if not a.agree:
        die("pass --agree only after the user has agreed to CC BY-NC 4.0 and to the project showing the film")

    film = Path(a.film).expanduser()
    if not film.is_file():
        die(f"film not found: {film}")
    ext = film.suffix.lower()
    if ext not in (".webp", ".gif"):
        die("the gallery takes an animated .webp or .gif (use the WebP lemo-wake made)")
    title, author = a.title.strip(), a.author.strip()
    if not title or len(title) > 80:
        die("title must be 1-80 characters")
    title_en = a.title_en.strip()
    if len(title_en) > 80:
        die("--title-en must be at most 80 characters")
    if not author or len(author) > 60:
        die("author must be 1-60 characters")
    if a.author_url and not re.fullmatch(r"https://[^\s\"'<>]+", a.author_url):
        die("--author-url must be an https:// link")

    frames = frames_of(film)
    if len(frames) < 2:
        die("the film has a single frame - it is not animated")
    w, h = frames[0][0].size
    dur_ms = sum(d for _, d in frames)

    m = re.fullmatch(r"https://github\.com/([A-Za-z0-9-]+)/?", a.author_url or "")
    login = (m.group(1).lower() if m else slugify(author)) or "anon"
    slug = slugify(a.slug or re.sub(r"(-alive|-loop)$", "", film.stem)) or "film"
    fid = f"{datetime.date.today():%Y%m%d}-{login}-{slug}"[:64].strip("-")
    dest = Path(a.out).expanduser() / "films" / fid
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    warnings, notes_out = [], {}

    # film
    out_film = dest / f"film{ext}"
    if film.stat().st_size <= FILM_MAX:
        shutil.copyfile(film, out_film)
    elif ext == ".gif":
        die(f"the GIF is {film.stat().st_size / 1e6:.1f} MB (limit 8 MB) - submit the WebP instead")
    else:
        out_film = dest / "film.webp"
        for fps, q in WEBP_TIERS:
            size = save_webp(resample(frames, fps), out_film, q)
            if size <= FILM_MAX:
                warnings.append(f"film re-compressed to fit 8 MB ({fps} fps, quality {q})")
                break
        else:
            shutil.rmtree(dest)
            die(f"still {size / 1e6:.1f} MB at 12 fps / q50 - too big for the gallery. Re-encode a shorter or "
                "smaller film (encode.py --webp-max 8) and try again", 3)

    # preview: long side 360, <= 1 MB
    s = 360 / max(w, h)
    psize = (max(2, round(w * s)), max(2, round(h * s))) if s < 1 else (w, h)
    for fps, q in [(15, 70), (12, 62), (10, 55), (8, 50)]:
        if save_webp(resample(frames, fps), dest / "preview.webp", q, psize) <= PREVIEW_MAX:
            break
    else:
        die("could not make a preview under 1 MB")

    # original, without metadata
    if a.source:
        src = Path(a.source).expanduser()
        if not src.is_file():
            die(f"source not found: {src}")
        im = ImageOps.exif_transpose(Image.open(src))
        bg = Image.new("RGB", im.size, (255, 255, 255))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[3])
        bg.thumbnail((1600, 1600), Image.LANCZOS)
        for q in (88, 82, 75, 68):
            bg.save(dest / "source.jpg", "JPEG", quality=q, optimize=True)  # no exif= -> no metadata written
            if (dest / "source.jpg").stat().st_size <= SOURCE_MAX:
                break

    # notes
    if a.notes:
        text = Path(a.notes).expanduser().read_text(encoding="utf-8")
        if len(text.encode()) > NOTES_MAX:
            die("notes are over 20 KB - shorten them")
        for pat, what in PRIVATE:
            for m in re.finditer(pat, text):
                warnings.append(f"notes contain what looks like {what}: {m.group(0)[:40]!r} - remove it before submitting")
        (dest / "notes.md").write_text(text, encoding="utf-8")

    meta = {
        "title": title,
        **({"title_en": title_en} if title_en else {}),
        "category": a.category,
        "author": author,
        **({"author_url": a.author_url} if a.author_url else {}),
        "license": "CC-BY-NC-4.0",
        "consent": True,
        "created": f"{datetime.date.today():%Y-%m-%d}",
        "lemo_wake": a.version,
        "width": w, "height": h,
        "seconds": round(dur_ms / 1000, 2),
    }
    (dest / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    files = {p.name: p.stat().st_size for p in sorted(dest.iterdir())}
    print(json.dumps({"id": fid, "folder": str(dest), "files": files, "meta": meta, "warnings": warnings},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
