#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pillow", "numpy"]
# ///
"""Frames -> the four deliverables of every film, plus <prefix>.encode.json.

  encode.py <frames dir> <prefix> [--fps 30] [--no-mp4] [--no-gif] [--no-webp] [--no-sticker]
            [--gif-max 5] [--gif-width 1080] [--webp-max 8] [--sticker-max 0.5] [--sticker-side 240]

  frames dir: <src>/frames from render.mjs, or <src>/frames_loop from reset.py
  outputs (what each one is for):
    <prefix>.mp4          H.264 / yuv420p / no audio / +faststart, ORIGINAL pixel size, except that H.264 needs even
                          dimensions: an odd width/height is rounded DOWN by 1 px (941x1672 -> 940x1672).
                          For posts: WeChat Moments, Xiaohongshu, Douyin, Instagram, X.
    <prefix>.gif          "chat" GIF: scaled down only as far as needed to fit <= --gif-max MB (default 5) with
                          width < --gif-width (default 1080). --gif-width is a CAP, not a target: the size limit
                          decides the actual width (largest tier: 960 px long side), so for a wider GIF raise --gif-max too. Busy full-frame motion
                          (night scenes, star fields, a moving camera) lands well below the cap (e.g. ~420 px wide).
                          For WeChat chats, QQ, Weibo.
    <prefix>.webp         animated WebP at the ORIGINAL pixel size. --webp-max (default 8 MB) is only a target:
                          quality and fps go down a little first, never below 12 fps / q50 (then the
                          file is simply allowed to be bigger); pixels are never reduced. For web pages,
                          GitHub READMEs, galleries.
    <prefix>-sticker.gif  sticker GIF: longest side 240 (--sticker-side), dropping to 200 px / 8 fps when needed to stay
                          <= 500 KB; bayer dither, diff palette. Drag it into WeChat as a custom sticker.
  <prefix>.encode.json is merged: a rerun with --no-xxx keeps the entries of the skipped formats from the earlier run.
  All sizes are decimal MB (1 MB = 1,000,000 bytes), the way platforms state their limits.
  Platform limit overrides: --gif-max / --webp-max / --sticker-max (MB), --gif-width (px, exclusive).
Exit code 3 when the chat GIF or sticker cannot reach its limit even at the lowest tier.
The WebP over its target is only a warning (exit 0).
"""
import argparse, glob, json, os, subprocess, sys
import numpy as np
from PIL import Image

# chat GIF tiers: (long-side cap, fps, colors)
GIF_TIERS = [(960, 15, 256), (840, 15, 256), (720, 15, 256), (640, 15, 224), (560, 12, 200), (480, 12, 176),
             (420, 12, 160), (360, 10, 128), (320, 10, 112), (280, 10, 96), (240, 8, 80)]
# WebP tiers: (fps, quality) - the pixel size is always the canvas size
WEBP_TIERS = [(15, 82), (15, 75), (15, 68), (12, 66), (12, 58), (12, 50)]
# Floor = 12 fps / q50: below that fine detail goes soft and fast hits get only 2-3 frames.
# If the lowest tier is still over the target, keep it and accept the bigger file.
# sticker GIF tiers: (longest side, fps, colors) - the approved sticker look
STICKER_TIERS = [(240, 12, 128), (240, 10, 96), (240, 10, 64), (200, 10, 64), (200, 8, 48)]


def frames_of(d):
    fs = sorted(glob.glob(os.path.join(d, "f_*.*")))
    if not fs: sys.exit(f"no frames in {d}")
    return fs


def pattern(d):
    return os.path.join(d, "f_%05d" + os.path.splitext(frames_of(d)[0])[1])


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def even(x):
    return max(2, int(x) // 2 * 2)


def is_photo(f):
    """Rough 'photo / lots of gradients' test: many 5-bit colours after downscaling -> dither against banding."""
    im = Image.open(f).convert("RGB"); im.thumbnail((256, 256))
    a = (np.asarray(im) >> 3).reshape(-1, 3).astype(np.int32)
    return len(np.unique(a[:, 0] * 1024 + a[:, 1] * 32 + a[:, 2])) > 3000


def pick_frames(fs, src_fps, fps):
    n = len(fs); m = max(2, round(n / src_fps * fps))
    return [fs[min(n - 1, int(i * src_fps / fps + 1e-6))] for i in range(m)]


def enc_mp4(d, src_fps, out, crf):
    ff("-framerate", str(src_fps), "-i", pattern(d), "-an", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
       "-vf", "crop=trunc(iw/2)*2:trunc(ih/2)*2,scale=out_range=tv:out_color_matrix=bt709,format=yuv420p",
       "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
       "-movflags", "+faststart", out)


def enc_gif(d, src_fps, out, W, H, fps, colors, dither):
    dith = {"none": "none", "bayer": "bayer:bayer_scale=4", "sierra": "sierra2_4a"}[dither]
    vf = (f"fps={fps},scale={W}:{H}:flags=lanczos,split[a][b];[a]palettegen=max_colors={colors}:stats_mode=full[p];"
          f"[b][p]paletteuse=dither={dith}")
    ff("-framerate", str(src_fps), "-i", pattern(d), "-filter_complex", vf, "-loop", "0", out)


def enc_sticker(d, src_fps, out, W, H, fps, colors):
    vf = (f"fps={fps},scale={W}:{H}:flags=lanczos,split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];"
          f"[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
    ff("-framerate", str(src_fps), "-i", pattern(d), "-filter_complex", vf, "-loop", "0", out)


def enc_webp(fs, src_fps, out, fps, q, cache):
    sel = pick_frames(fs, src_fps, fps)
    ims = [cache.setdefault(f, Image.open(f).convert("RGB")) for f in sel]
    ims[0].save(out, save_all=True, append_images=ims[1:], duration=round(1000 / fps), loop=0, quality=q, method=4)
    return len(ims)


def kb(b):
    return f"{b / 1000:.0f}KB" if b < 1e6 else f"{b / 1e6:.2f}MB"


def main():
    ap = argparse.ArgumentParser(description="frames -> MP4 + chat GIF + WebP + sticker GIF")
    ap.add_argument("frames"); ap.add_argument("prefix")
    ap.add_argument("--fps", type=float, default=30, help="frame rate of the frames dir (render fps)")
    for k in ("mp4", "gif", "webp", "sticker"):
        ap.add_argument(f"--no-{k}", action="store_true", help=f"skip the {k}")
    ap.add_argument("--mp4", action="store_true", help=argparse.SUPPRESS)          # old flag, MP4 is default now
    ap.add_argument("--gif-max", type=float, default=5, help="chat GIF limit, MB")
    ap.add_argument("--gif-width", type=int, default=1080, help="cap: chat GIF width stays below this (the --gif-max size limit decides the actual width)")
    ap.add_argument("--webp-max", type=float, default=8, help="WebP size target, MB (pixels are never reduced)")
    ap.add_argument("--sticker-max", type=float, default=0.5, help="sticker GIF limit, MB")
    ap.add_argument("--sticker-side", type=int, default=240, help="sticker GIF longest side, px")
    ap.add_argument("--crf", type=int, default=18, help="MP4 quality (lower = better, bigger)")
    ap.add_argument("--dither", default="auto", choices=["auto", "none", "bayer", "sierra"], help="chat GIF dither")
    a = ap.parse_args()

    fs = frames_of(a.frames)
    w, h = Image.open(fs[0]).size
    os.makedirs(os.path.dirname(os.path.abspath(a.prefix)) or ".", exist_ok=True)
    rep = {"frames": len(fs), "src_fps": a.fps, "dur": round(len(fs) / a.fps, 3), "canvas": [w, h]}
    hard_fail = False

    if not a.no_mp4:
        out = a.prefix + ".mp4"; enc_mp4(a.frames, a.fps, out, a.crf); b = os.path.getsize(out)
        rep["mp4"] = dict(path=os.path.basename(out), size=[even(w), even(h)], fps=a.fps, crf=a.crf, bytes=b, ok=True,
                          use="posts: WeChat Moments, Xiaohongshu, Douyin, Instagram, X")
        print(f"  {rep['mp4']['path']}: {even(w)}x{even(h)} {a.fps:g}fps H.264 -> {kb(b)}")

    if not a.no_gif:
        out = a.prefix + ".gif"; cap = a.gif_max * 1e6
        dither = a.dither if a.dither != "auto" else ("bayer" if is_photo(fs[len(fs) // 2]) else "none")
        def gif_tier(i):
            L, fps, colors = GIF_TIERS[i]
            s = min(1.0, L / max(w, h), (a.gif_width - 1) / w)
            return even(w * s), even(h * s), fps, colors

        tried = {}                                   # tier -> bytes
        def try_tier(i):
            enc_gif(a.frames, a.fps, out, *gif_tier(i), dither); tried[i] = os.path.getsize(out); return tried[i]
        i = 0
        while True:
            b = try_tier(i)
            if b <= cap or i == len(GIF_TIERS) - 1: break
            W, H, fps, _ = gif_tier(i); budget = W * H * fps * cap / b * 1.4   # rough: size ~ pixels x fps
            i += 1
            while i < len(GIF_TIERS) - 1 and gif_tier(i)[0] * gif_tier(i)[1] * gif_tier(i)[2] > budget: i += 1
        if b <= cap and i > 0 and (i - 1) not in tried:  # the estimate may have skipped a tier that fits
            if try_tier(i - 1) <= cap: i -= 1
            else: try_tier(i)
        W, H, fps, colors = gif_tier(i); b = tried[i]
        rep["gif"] = dict(path=os.path.basename(out), size=[W, H], fps=fps, colors=colors, dither=dither, bytes=b,
                          max_bytes=int(cap), ok=b <= cap, use="chat: WeChat, QQ, Weibo")
        hard_fail |= b > cap
        print(f"  {rep['gif']['path']}: {W}x{H} {fps}fps {colors} colours dither={dither} -> {kb(b)}"
              + ("" if b <= cap else f"  (over {kb(cap)} even at the lowest tier)"))

    if not a.no_webp:
        out = a.prefix + ".webp"; cap = a.webp_max * 1e6; cache = {}
        i = 0
        while i < len(WEBP_TIERS):
            fps, q = WEBP_TIERS[i]
            n = enc_webp(fs, a.fps, out, fps, q, cache); b = os.path.getsize(out)
            if b <= cap: break
            i += 2 if b > 1.8 * cap and i + 2 < len(WEBP_TIERS) else 1
        rep["webp"] = dict(path=os.path.basename(out), size=[w, h], fps=fps, quality=q, frames=n, bytes=b,
                           target_bytes=int(cap), ok=b <= cap, use="web, GitHub README, galleries")
        print(f"  {rep['webp']['path']}: {w}x{h} {fps}fps q{q} -> {kb(b)}"
              + ("" if b <= cap else f"  (above the {kb(cap)} target; pixel size kept - use the MP4/GIF where a hard limit applies)"))

    if not a.no_sticker:
        out = a.prefix + "-sticker.gif"; cap = a.sticker_max * 1e6
        for L, fps, colors in STICKER_TIERS:
            L = round(L * a.sticker_side / 240); s = L / max(w, h)
            W, H = even(round(w * s / 2) * 2), even(round(h * s / 2) * 2)
            enc_sticker(a.frames, a.fps, out, W, H, fps, colors); b = os.path.getsize(out)
            if b <= cap: break
        rep["sticker"] = dict(path=os.path.basename(out), size=[W, H], fps=fps, colors=colors, bytes=b,
                              max_bytes=int(cap), ok=b <= cap, use="WeChat custom sticker")
        hard_fail |= b > cap
        print(f"  {rep['sticker']['path']}: {W}x{H} {fps}fps {colors} colours -> {kb(b)}"
              + ("" if b <= cap else f"  (over {kb(cap)} even at the lowest tier)"))

    # merge with an earlier report: a rerun that skips some formats keeps their entries (if those files still exist)
    jpath = a.prefix + ".encode.json"
    try:
        old = json.load(open(jpath))
    except Exception:
        old = {}
    kept = []
    for k in ("mp4", "gif", "webp", "sticker"):
        if k not in rep and isinstance(old.get(k), dict) and os.path.isfile(os.path.join(os.path.dirname(jpath), old[k].get("path", ""))):
            rep[k] = old[k]; kept.append(k)
    if kept:
        same = old.get("frames") == rep["frames"] and old.get("canvas") == rep["canvas"]
        print(f"  kept from the earlier run: {', '.join(kept)}" + ("" if same else
              "  (! made from a different frame set - re-encode them too if the frames changed)"))
    order = ["frames", "src_fps", "dur", "canvas", "mp4", "gif", "webp", "sticker"]
    rep = {k: rep[k] for k in order + [k for k in rep if k not in order] if k in rep}
    with open(jpath, "w") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1)
    sys.exit(3 if hard_fail else 0)


main()
