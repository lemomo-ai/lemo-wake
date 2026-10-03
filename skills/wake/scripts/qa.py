#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["numpy", "opencv-python-headless"]
# ///
"""Pre-delivery QA: catches the most common failures and writes a contact sheet for a human (and you) to look at.

  qa.py <frames dir> --src <srcDir> [--fps 30] [--no-loop] [--encode <prefix>.encode.json] [--sheet out.png] [--json out.json]

  frames dir: the frames you deliver (frames_loop if a reset transition was added)
  --src:      the project's src dir (finds assets/source.* and render.log)
  --no-loop:  the film is explicitly not meant to loop. By default the loop seam is checked.

Checks (FAIL = usually a real technical problem; WARN = often intentional, keep it if you can say why):
  FAIL render errors   render.log has page errors / images or fonts that failed to load
  FAIL loop seam       last frame -> first frame jumps far more than normal frame-to-frame change
  FAIL size            chat GIF or sticker GIF still over its limit at the lowest tier
  WARN WebP size       WebP above its size target (pixel size is kept on purpose)
  WARN source unseen   no frame is close to the source image
  WARN source hold     frames close to the source last < 0.5 s
  WARN first frame     first frame nearly blank (many apps use it as the still preview)
  WARN dead zone / jump  long stretch with almost no motion; one frame changes far more than its neighbours
Exit code 1 if anything FAILs.
"""
import argparse, glob, json, os, sys
import cv2
import numpy as np


def gray(f, w=256):
    g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    if g is None: sys.exit(f"cannot read: {f}")
    return cv2.resize(g, (w, max(2, round(w * g.shape[0] / g.shape[1]))), interpolation=cv2.INTER_AREA).astype(np.float32)


def ssim(a, b):
    C1, C2 = 6.5025, 58.5225
    mu1, mu2 = cv2.GaussianBlur(a, (11, 11), 1.5), cv2.GaussianBlur(b, (11, 11), 1.5)
    s1 = cv2.GaussianBlur(a * a, (11, 11), 1.5) - mu1 ** 2; s2 = cv2.GaussianBlur(b * b, (11, 11), 1.5) - mu2 ** 2
    s12 = cv2.GaussianBlur(a * b, (11, 11), 1.5) - mu1 * mu2
    return float((((2 * mu1 * mu2 + C1) * (2 * s12 + C2)) / ((mu1 ** 2 + mu2 ** 2 + C1) * (s1 + s2 + C2))).mean())


def edges(g):
    return float((cv2.Canny(g.astype(np.uint8), 60, 160) > 0).mean())


def sheet(fs, out, n=8, h=200):
    ids = sorted(set([round(i * (len(fs) - 1) / (n - 1)) for i in range(n)]))
    tiles = []
    for i in ids + [0]:  # first frame appended at the end: shows the loop seam at a glance
        im = cv2.imread(fs[i]); im = cv2.resize(im, (round(im.shape[1] * h / im.shape[0]), h), interpolation=cv2.INTER_AREA)
        cv2.rectangle(im, (0, 0), (92, 18), (0, 0, 0), -1)
        cv2.putText(im, f"#{i}" + (" loop" if i == 0 and tiles else ""), (4, 13), 0, .42, (255, 255, 255), 1)
        tiles.append(im)
    cols = 5; rows = (len(tiles) + cols - 1) // cols; w = tiles[0].shape[1]
    S = np.full((rows * (h + 4), cols * (w + 4), 3), 24, np.uint8)
    for k, t in enumerate(tiles):
        y, x = (k // cols) * (h + 4), (k % cols) * (w + 4); S[y:y + h, x:x + t.shape[1]] = t[:, :w]
    cv2.imwrite(out, S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames"); ap.add_argument("--src"); ap.add_argument("--source")
    ap.add_argument("--fps", type=float, default=30); ap.add_argument("--no-loop", action="store_true")
    ap.add_argument("--encode"); ap.add_argument("--sheet"); ap.add_argument("--json")
    a = ap.parse_args()
    fs = sorted(glob.glob(os.path.join(a.frames, "f_*.*")))
    if len(fs) < 3: sys.exit(f"no frames: {a.frames}")
    cands = sorted(glob.glob(os.path.join(a.src, "assets", "source.*"))) if a.src else []
    src_img = a.source or (cands[0] if cands else None)
    res = []  # (level, item, message)
    add = lambda lv, k, msg: res.append((lv, k, msg))
    n, fps = len(fs), a.fps

    # render log
    log = os.path.join(a.src, "render.log") if a.src else None
    if log and os.path.isfile(log) and open(log, encoding="utf-8").read().strip():
        lines = [l for l in open(log, encoding="utf-8").read().splitlines() if l.strip()]
        add("FAIL", "render errors", f"{len(lines)}, e.g. {lines[0][:160]}")
    else:
        add("PASS", "render errors", "none" if log and os.path.isfile(log) else "no render.log (written by render.mjs)")

    G = [gray(f) for f in fs]
    d = np.array([0.0] + [float(np.abs(G[i] - G[i - 1]).mean()) for i in range(1, n)])
    typ = float(np.median(d[1:])) if n > 2 else 0

    # loop seam
    seam = float(np.abs(G[-1] - G[0]).mean())
    if not a.no_loop:
        thr = max(6.0, min(25.0, max(4 * typ, float(np.percentile(d[1:], 90)) * 1.2)))
        if seam > thr: add("FAIL", "loop seam", f"last->first difference {seam:.1f}, typical frame difference {typ:.1f}: every loop hard-cuts. Add a reset transition (reset.py) or an in-picture one")
        else: add("PASS", "loop seam", f"last->first difference {seam:.1f} (threshold {thr:.1f})")

    # source appearance and hold
    sim = None
    if src_img:
        S = gray(src_img); S = cv2.resize(S, (G[0].shape[1], G[0].shape[0]))
        sim = np.array([ssim(g, S) for g in G]); pk = float(sim.max()); at = int(sim.argmax())
        hold = int(((sim >= pk - .03) & (sim >= .75)).sum())
        if pk < .8: add("WARN", "source seen", f"closest frame to the source only reaches similarity {pk:.2f} (#{at}): viewers may never see the complete picture")
        else: add("PASS", "source seen", f"peak similarity {pk:.2f} (#{at}, {at / fps:.2f}s)")
        if pk >= .8:
            if hold / fps < .5: add("WARN", "source hold", f"frames close to the source last only {hold / fps:.2f}s (< 0.5s), too short to take in")
            else: add("PASS", "source hold", f"{hold / fps:.2f}s")
        e0, es = edges(G[0]), edges(S)
        if e0 < es * .25 and sim[0] < .6: add("WARN", "first frame", f"first frame has {e0 / max(es, 1e-6) * 100:.0f}% of the source detail, nearly blank (often used as the still preview)")
        else: add("PASS", "first frame", f"detail {e0 / max(es, 1e-6) * 100:.0f}% / similarity to source {sim[0]:.2f}")
    else:
        add("WARN", "source seen", "source image not found (no assets/source.* under --src): pass --source <path>; comparison skipped")

    # dead zones / jumps
    dead, run = [], 0
    for i, v in enumerate(list(d) + [99]):
        if 0 < i < n and v < .6: run += 1
        else:
            a0 = i - run
            # a hold on the source picture is a designed pause, not a dead zone
            is_hold = sim is not None and run > 0 and float(sim[a0:i].mean()) >= float(sim.max()) - .05
            if run / fps > .6 and a0 > 1 and not is_hold: dead.append(f"{a0 / fps:.2f}–{i / fps:.2f}s")
            run = 0
    jumps = []
    for i in range(2, n - 2):
        loc = float(np.median(np.r_[d[i - 2:i], d[i + 1:i + 3]]))
        if d[i] > 8 and d[i] > 3.5 * max(loc, 1): jumps.append(f"#{i}({i / fps:.2f}s) {d[i]:.0f}/{loc:.0f}")
    add("WARN" if dead else "PASS", "dead zone", ", ".join(dead) if dead else "none")
    add("WARN" if jumps else "PASS", "jump", "; ".join(jumps[:6]) + ("..." if len(jumps) > 6 else "") if jumps else "none")

    # deliverables
    if a.encode and os.path.isfile(a.encode):
        rep = json.load(open(a.encode))
        names = {"mp4": "MP4 (posts)", "gif": "GIF (chat)", "webp": "WebP (web)", "sticker": "sticker GIF"}
        for k, label in names.items():
            if k not in rep: continue
            r = rep[k]; sz = r.get("size") or ["?", "?"]
            msg = f"{r['bytes'] / 1e6:.2f}MB {sz[0]}x{sz[1]} {r.get('fps', '?')}fps"
            lv = "PASS" if r.get("ok", True) else ("WARN" if k == "webp" else "FAIL")
            if lv == "WARN": msg += f" - above the {r.get('target_bytes', 0) / 1e6:.0f}MB target (pixel size kept)"
            add(lv, label, msg)

    # output
    sh = a.sheet or os.path.join(os.path.dirname(os.path.abspath(a.frames)), "qa_sheet.jpg")
    sheet(fs, sh)
    icon = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}
    print(f"{n} frames {n / fps:.2f}s  frames dir {a.frames}")
    for lv, k, msg in res: print(f"{icon[lv]:<4} {k}: {msg}")
    print(f"contact sheet (last tile = first frame, to check the loop seam): {sh}")
    if a.json: json.dump([dict(level=lv, item=k, msg=m) for lv, k, m in res], open(a.json, "w"), ensure_ascii=False, indent=1)
    sys.exit(1 if any(lv == "FAIL" for lv, _, _ in res) else 0)


main()
