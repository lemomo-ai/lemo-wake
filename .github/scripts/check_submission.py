#!/usr/bin/env python3
"""Check a gallery pull request. Usage: check_submission.py <base ref>   (run from the PR checkout root)

A submission only ADDS one or more folders films/<id>/ with:
  meta.json (required), film.webp or film.gif (required, animated, <= 8 MB),
  preview.webp (required, animated, long side <= 480, <= 1 MB),
  source.jpg (optional, <= 2 MB, no EXIF), notes.md (optional, <= 20 KB).
"""
import json, re, subprocess, sys
from pathlib import Path
from PIL import Image

CATS = {"life", "people", "poster", "brand", "data", "social", "sticker", "art"}
LIMITS = {"film.webp": 8_000_000, "film.gif": 8_000_000, "preview.webp": 1_000_000,
          "source.jpg": 2_000_000, "notes.md": 20_000, "meta.json": 10_000}
ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}")
errors = []


def err(msg):
    errors.append(msg)
    print(f"::error::{msg}")


def animated(path):
    with Image.open(path) as im:
        return getattr(im, "n_frames", 1) > 1, im.size


def main():
    base = sys.argv[1]
    diff = subprocess.run(["git", "diff", "--name-status", "--no-renames", f"{base}...HEAD"],
                          capture_output=True, text=True, check=True).stdout.splitlines()
    if not diff:
        err("the pull request changes nothing")
    ids = set()
    for line in diff:
        status, path = line.split("\t", 1)
        parts = path.split("/")
        if len(parts) != 3 or parts[0] != "films" or not ID.fullmatch(parts[1]) or parts[2] not in LIMITS:
            err(f"{path}: a submission may only add films/<id>/{{{','.join(sorted(LIMITS))}}} "
                "(changes to anything else need a maintainer)")
            continue
        if status != "A":
            err(f"{path}: existing gallery files cannot be changed or removed by a submission")
            continue
        ids.add(parts[1])

    for fid in sorted(ids):
        d = Path("films") / fid
        names = {p.name for p in d.iterdir()}
        for n in names:
            size = (d / n).stat().st_size
            if n in LIMITS and size > LIMITS[n]:
                err(f"{d}/{n}: {size / 1e6:.2f} MB is over the {LIMITS[n] / 1e6:g} MB limit")
        if "meta.json" not in names:
            err(f"{d}: meta.json is missing")
            continue
        films = names & {"film.webp", "film.gif"}
        if len(films) != 1:
            err(f"{d}: exactly one film.webp or film.gif is needed")
        if "preview.webp" not in names:
            err(f"{d}: preview.webp is missing")
        try:
            m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        except Exception as e:
            err(f"{d}/meta.json: not valid JSON ({e})")
            continue
        t = m.get("title")
        if not isinstance(t, str) or not 0 < len(t.strip()) <= 80:
            err(f"{d}/meta.json: title must be 1-80 characters")
        te = m.get("title_en", "")
        if not isinstance(te, str) or len(te) > 80:
            err(f"{d}/meta.json: title_en (optional) must be at most 80 characters")
        if m.get("category") not in CATS:
            err(f"{d}/meta.json: category must be one of {', '.join(sorted(CATS))}")
        a = m.get("author")
        if not isinstance(a, str) or not 0 < len(a.strip()) <= 60:
            err(f"{d}/meta.json: author must be 1-60 characters")
        if "author_url" in m and not re.fullmatch(r"https://[^\s\"'<>]+", str(m["author_url"])):
            err(f"{d}/meta.json: author_url must be an https:// link")
        if m.get("license") != "CC-BY-NC-4.0":
            err(f"{d}/meta.json: license must be CC-BY-NC-4.0")
        if m.get("consent") is not True:
            err(f"{d}/meta.json: consent must be true (agreement to CC BY-NC 4.0 and to being shown by the project)")
        for f in films:
            try:
                anim, _ = animated(d / f)
                if not anim:
                    err(f"{d}/{f}: not animated")
            except Exception as e:
                err(f"{d}/{f}: cannot be read as an image ({e})")
        if "preview.webp" in names:
            try:
                anim, (w, h) = animated(d / "preview.webp")
                if not anim or max(w, h) > 480:
                    err(f"{d}/preview.webp: must be animated with the long side <= 480 px")
            except Exception as e:
                err(f"{d}/preview.webp: cannot be read ({e})")
        if "source.jpg" in names:
            try:
                with Image.open(d / "source.jpg") as im:
                    if im.format != "JPEG":
                        err(f"{d}/source.jpg: must be a JPEG")
                    if len(im.getexif()) or "exif" in im.info or "xmp" in im.info:
                        err(f"{d}/source.jpg: contains metadata (EXIF/XMP) - remove it (location, camera, date)")
            except Exception as e:
                err(f"{d}/source.jpg: cannot be read ({e})")

    if errors:
        print(f"\n{len(errors)} problem(s) found.")
        sys.exit(1)
    print(f"OK: {len(ids)} film(s): {', '.join(sorted(ids))}")


if __name__ == "__main__":
    main()
