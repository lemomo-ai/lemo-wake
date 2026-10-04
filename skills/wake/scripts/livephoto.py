#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pillow", "numpy"]
# ///
"""Frames -> an Apple Live Photo (macOS only): <prefix>.pvt, plus an entry in <prefix>.encode.json.

  livephoto.py <frames dir> <prefix> [--fps 30] [--src <src dir>] [--cover SEC] [--seconds 3] [--h264]

  The whole film is sped up (or kept) to --seconds (default 3, the length of a camera Live Photo) and paired with
  one still frame, the cover. The cover is what the photo shows before it is pressed, so it should be the most
  complete frame, NOT frame 0 by default (films often start empty):
    --cover SEC   the film time of the cover frame (your choice after looking at the frames)
    otherwise     the frame closest to the source image (needs --src, same aspect ratio), else the most detailed
                  frame among the calmest ones (the held, complete picture)
  <prefix>.pvt is a Live Photo bundle (the HEIC still + the MOV + metadata.plist). Finder shows it as one file.
  To get it onto an iPhone: right-click it in Finder > Share > AirDrop, and send only that one item. A loose
  HEIC + MOV pair is saved by the iPhone as a separate photo and video.
  Needs the Xcode Command Line Tools (swiftc): xcode-select --install. The two small Swift tools in
  scripts/livephoto/ are compiled once into ~/Library/Caches/lemo-wake/. The bundle is checked with the system's
  own Live Photo reader before it is reported (no access to the Photos library, no permission prompt).
Exit code 4 when not on macOS or swiftc is missing, 1 when the bundle fails the check.
"""
import argparse, glob, hashlib, json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "livephoto")


def die(msg, code=1):
    print(msg, file=sys.stderr); sys.exit(code)


def tool(name):
    """Compile scripts/livephoto/<name>.swift once (cached by content hash) and return the binary path."""
    src = os.path.join(TOOLS, name + ".swift")
    h = hashlib.sha256(open(src, "rb").read()).hexdigest()[:12]
    out = os.path.join(os.path.expanduser("~/Library/Caches/lemo-wake/bin"), f"{name}-{h}")
    if not os.path.isfile(out):
        swiftc = shutil.which("swiftc")
        if not swiftc:
            die("swiftc not found: install the Xcode Command Line Tools (xcode-select --install), then run this again", 4)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        r = subprocess.run([swiftc, "-O", src, "-o", out], capture_output=True, text=True)
        if r.returncode:
            die(f"compiling {name}.swift failed:\n{r.stderr[-1500:]}")
    return out


def small(f, w=96):
    im = Image.open(f).convert("L"); h = max(2, round(w * im.height / im.width))
    return np.asarray(im.resize((w, h), Image.BILINEAR), dtype=np.float32)


def main():
    ap = argparse.ArgumentParser(description="frames -> Apple Live Photo (.pvt), macOS only")
    ap.add_argument("frames"); ap.add_argument("prefix")
    ap.add_argument("--fps", type=float, default=30, help="frame rate of the frames dir (render fps)")
    ap.add_argument("--src", help="the project's src dir: the cover defaults to the frame closest to assets/source.*")
    ap.add_argument("--cover", type=float, help="film time (s) of the cover frame")
    ap.add_argument("--seconds", type=float, default=3, help="Live Photo length (the film is sped up to this)")
    ap.add_argument("--h264", action="store_true", help="H.264 instead of HEVC for the video")
    a = ap.parse_args()
    if sys.platform != "darwin":
        die("Live Photos can only be made on macOS (Apple's AVFoundation writes the pairing metadata)", 4)
    fs = sorted(glob.glob(os.path.join(a.frames, "f_*.*")))
    if not fs: die(f"no frames (f_00000.jpg ...) in {a.frames}")
    n = len(fs); film = n / a.fps

    # cover frame
    if a.cover is not None:
        ci, why = min(n - 1, max(0, round(a.cover * a.fps))), "chosen"
    else:
        S = None
        for c in sorted(glob.glob(os.path.join(a.src, "assets", "source.*"))) if a.src else []:
            S = small(c); break
        G = [small(f) for f in fs[:: max(1, n // 60)]]; step = max(1, n // 60)
        if S is not None and abs(S.shape[0] / S.shape[1] - G[0].shape[0] / G[0].shape[1]) < .02:
            S = np.asarray(Image.fromarray(S).resize((G[0].shape[1], G[0].shape[0])), dtype=np.float32)
            j = int(np.argmin([np.mean((g - S) ** 2) for g in G])); why = "closest to the source"
        else:   # the complete picture is usually held still: among the calmest frames, take the most detailed one
            det = np.array([np.abs(np.diff(g, axis=0)).mean() + np.abs(np.diff(g, axis=1)).mean() for g in G])
            d = np.array([np.mean(np.abs(G[i] - G[i - 1])) for i in range(1, len(G))])
            mot = np.r_[d[0], np.maximum(d[:-1], d[1:]), d[-1]] if len(d) > 1 else np.zeros(len(G))
            calm = mot <= np.percentile(mot, 30)
            j = int(np.argmax(np.where(calm, det, -1))); why = "most detailed still moment"
        ci = min(n - 1, j * step)
    speed = min(1.0, a.seconds / film)          # < 1 = sped up
    key = ci / a.fps * speed

    out_dir = os.path.dirname(os.path.abspath(a.prefix)) or "."
    name = os.path.basename(a.prefix)
    with tempfile.TemporaryDirectory() as tmp:
        clip = os.path.join(tmp, "clip.mp4")
        pat = os.path.join(a.frames, "f_%05d" + os.path.splitext(fs[0])[1])
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", f"{a.fps:g}", "-i", pat,
                            "-vf", f"setpts=PTS*{speed:.6f},fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "14", clip],
                           capture_output=True, text=True)
        if r.returncode: die(f"ffmpeg failed: {r.stderr[-800:]}")
        still = os.path.join(tmp, "still" + os.path.splitext(fs[ci])[1]); shutil.copy(fs[ci], still)
        args = [tool("livephoto"), still, clip, tmp, name, "--key", f"{key:.3f}", "--duration", f"{a.seconds:g}"]
        if a.h264: args.append("--h264")
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode: die(f"livephoto failed: {(r.stderr or r.stdout)[-800:]}")
        pvt = os.path.join(tmp, name + ".pvt")
        v = subprocess.run([tool("validate"), pvt], capture_output=True, text=True)
        valid = v.returncode == 0
        dst = os.path.abspath(a.prefix) + ".pvt"
        shutil.rmtree(dst, ignore_errors=True); shutil.copytree(pvt, dst)
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fl in os.walk(dst) for f in fl)
    W, H = Image.open(fs[ci]).size
    print(f"  {os.path.basename(dst)}: {W}x{H} still + {a.seconds:g}s video (film {film:.1f}s x{1 / speed:.2f} speed), "
          f"cover frame #{ci} ({ci / a.fps:.2f}s, {why}) -> {size / 1e6:.2f}MB, system check: {'valid' if valid else 'FAILED'}")
    if why != "chosen": print("  look at the cover frame; pass --cover SEC to pick another one")

    jpath = a.prefix + ".encode.json"
    try: rep = json.load(open(jpath))
    except Exception: rep = {}
    rep["livephoto"] = dict(path=os.path.basename(dst), size=[W, H], seconds=a.seconds, speed=round(1 / speed, 3),
                            cover_frame=ci, cover_time=round(ci / a.fps, 3), bytes=size, ok=valid,
                            use="iPhone Photos as a Live Photo (AirDrop the .pvt), then Xiaohongshu / Moments")
    with open(jpath, "w") as fh: json.dump(rep, fh, ensure_ascii=False, indent=1)
    if not valid: die("the system's Live Photo reader rejected the bundle:\n" + v.stdout[-800:])


main()
