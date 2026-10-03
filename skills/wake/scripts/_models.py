#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///
"""Shared helpers for the local models: where they live, one-time download consent, download with
sha256 check, onnxruntime sessions. Imported by depth.py / segment.py / inpaint.py; the CLI is models.py.

Where models are stored (first match wins):
  1. $LEMO_WAKE_MODELS                         explicit override (ignored if it looks like an unexpanded
                                               variable, e.g. "/models" or "${CLAUDE_PLUGIN_DATA}/models")
  2. the Claude Code plugin data dir           ~/.claude/plugins/data/<plugin>-<marketplace>/models
                                               (inferred when this skill runs from the plugin cache;
                                               survives plugin updates, removed on uninstall)
  3. <skill folder>/models/                    skill installed by copying the folder (git-ignored)
Files already present in the old default ~/.cache/lemo-wake/models are reused, never downloaded again.
$CLAUDE_PLUGIN_DATA / $CLAUDE_SKILL_DIR are deliberately NOT read: a shell can carry another plugin's values.
Keep it that way - LEMO_WAKE_MODELS is the only path override.

Consent: before the FIRST download, scripts stop with exit code 10 and a message for the agent, which asks
the user once and records the answer (models.py consent yes|no) in <models dir>/consent.json.
If the user declined, scripts stop with exit code 11 ("declined - work around it").
A failed download exits with code 12 and prints mirror / manual-download hints.

Downloads honour HF_ENDPOINT (e.g. https://hf-mirror.com for mainland China); sha256 is always verified.
Inference uses onnxruntime on CPU. LEMO_WAKE_EP=coreml / cuda tries hardware acceleration and falls back
to CPU if the session cannot be built (on Apple Silicon CPU is usually faster - leave it off).
Only the standard library is used here; onnxruntime / numpy are declared by the calling scripts.
"""
import hashlib, json, os, re, sys, time, urllib.request
from pathlib import Path

EXIT_NEED_CONSENT, EXIT_DECLINED, EXIT_DOWNLOAD_FAILED = 10, 11, 12
HF = "https://huggingface.co"

# name -> url, local file, bytes, sha256 (= Hugging Face LFS hash), what it does, licence, cost of not having it
REGISTRY = {
    "depth-anything-v2-small": dict(
        url=f"{HF}/onnx-community/depth-anything-v2-small/resolve/main/onnx/model.onnx",
        file="depth_anything_v2_small.onnx", bytes=99060839,
        sha256="afb6a5c28f3b6bf1618c6e43f02073ef9dfdc70e937502d51603e57b0a1df10c",
        model="Depth Anything V2 Small", license="Apache-2.0", used_by="depth.py",
        does="depth map (near/far) for 3D parallax and layer-by-layer reveals",
        without="depth parallax and depth-ordered layers have to be faked by hand-drawn masks or simple 2D layering"),
    "birefnet-lite": dict(
        url=f"{HF}/onnx-community/BiRefNet_lite-ONNX/resolve/main/onnx/model.onnx",
        file="birefnet_lite.onnx", bytes=224005088,
        sha256="5600024376f572a557870a5eb0afb1e5961636bef4e1e22132025467d0f03333",
        model="BiRefNet-lite", license="MIT", used_by="segment.py --model general",
        does="cuts out the main subject (products, objects, people) with soft edges",
        without="clean cut-outs of photo subjects are harder; colour keys, boxes and code-drawn shapes replace them"),
    "modnet": dict(
        url=f"{HF}/Xenova/modnet/resolve/main/onnx/model.onnx",
        file="modnet.onnx", bytes=25888640,
        sha256="07c308cf0fc7e6e8b2065a12ed7fc07e1de8febb7dc7839d7b7f15dd66584df9",
        model="MODNet", license="Apache-2.0", used_by="segment.py --model portrait",
        does="portrait matting (keeps fine hair)",
        without="people cannot be lifted out cleanly with their hair; motion stays on the background, light or camera"),
    "mobilesam-encoder": dict(
        url=f"{HF}/Acly/MobileSAM/resolve/main/mobile_sam_image_encoder.onnx",
        file="mobile_sam_image_encoder.onnx", bytes=28157093,
        sha256="580f5fb648ea1062c0aabc26217aed56921985f03f0cbbd852bba81d760cc749",
        model="MobileSAM (image encoder)", license="MIT", used_by="segment.py --model sam",
        does="picks one specific element by clicking a point or drawing a box",
        without="individual elements (each pastry, each balloon) cannot be picked out of a photo, so fewer things can jump or fly on their own"),
    "mobilesam-decoder": dict(
        url=f"{HF}/Acly/MobileSAM/resolve/main/sam_mask_decoder_multi.onnx",
        file="sam_mask_decoder_multi.onnx", bytes=16496559,
        sha256="8976b90a87ba50a6a72217a5ff994f7d25ce16f2229fcc1ed259e1294c622ffe",
        model="MobileSAM (mask decoder)", license="MIT", used_by="segment.py --model sam",
        does="second half of MobileSAM", without="(same as the encoder)"),
    "lama": dict(
        url=f"{HF}/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx",
        file="lama_fp32.onnx", bytes=208044816,
        sha256="1faef5301d78db7dda502fe59966957ec4b79dd64e16f03ed96913c7a4eb68d6",
        model="LaMa", license="Apache-2.0", used_by="inpaint.py --engine lama",
        does="fills the hole left behind when an object is moved (clean background plate)",
        without="holes behind moved objects get the simple OpenCV fill (fine for small spots) or must be covered by staging"),
}

LEGACY_DIR = Path.home() / ".cache" / "lemo-wake" / "models"
SKILL_DIR = Path(__file__).resolve().parent.parent


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _mb(n):
    return f"{n / 1e6:.0f}MB"


def _foreign_plugin_dir(v):
    """True if v lies in another plugin's data folder (.../plugins/data/<name>/... without 'lemo-wake' in <name>),
    e.g. LEMO_WAKE_MODELS="$CLAUDE_PLUGIN_DATA/models" expanded by a shell that carries another plugin's value."""
    parts = Path(v).expanduser().parts
    for i in range(len(parts) - 2):
        if parts[i] == "plugins" and parts[i + 1] == "data":
            return "lemo-wake" not in parts[i + 2].lower()
    return False


def _bad_env(v):
    """An env value that is really an unexpanded / empty-expanded placeholder, or another plugin's folder."""
    return ("${" in v or "CLAUDE_PLUGIN_DATA" in v or v.rstrip("/\\") in ("/models", "\\models", "models", "")
            or _foreign_plugin_dir(v))


def plugin_data_dir():
    """If this skill runs from Claude Code's plugin cache (.../plugins/cache/<marketplace>/<plugin>/<version>/...),
    return the matching persistent data dir (.../plugins/data/<plugin>-<marketplace>), else None."""
    parts = SKILL_DIR.parts
    for i in range(len(parts) - 3):
        if parts[i] == "plugins" and parts[i + 1] == "cache":
            mkt, plugin = parts[i + 2], parts[i + 3]
            clean = lambda s: re.sub(r"[^A-Za-z0-9_-]", "-", s)
            return Path(*parts[:i + 1]) / "data" / f"{clean(plugin)}-{clean(mkt)}"
    return None


_warned = []


def models_dir(create=True):
    env = os.environ.get("LEMO_WAKE_MODELS", "").strip()
    if env and _bad_env(env):
        if not _warned:
            print(f"! ignoring LEMO_WAKE_MODELS={env!r} (an unexpanded placeholder, or another plugin's data folder)", file=sys.stderr)
            _warned.append(1)
        env = ""
    if env:
        d = Path(env).expanduser()
    elif plugin_data_dir():
        d = plugin_data_dir() / "models"
    else:
        d = SKILL_DIR / "models"
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def _ok(p, m):
    return p.is_file() and (not m.get("bytes") or p.stat().st_size == m["bytes"])


def local_path(name):
    """Existing, complete copy of a model (models dir first, then the old default cache), or None."""
    m = REGISTRY[name]
    for d in (models_dir(create=False), LEGACY_DIR):
        if _ok(d / m["file"], m):
            return d / m["file"]
    return None


# ---------------- consent ----------------
def consent_file():
    return models_dir(create=False) / "consent.json"


def consent():
    """True / False if the user answered, None if never asked."""
    try:
        return bool(json.loads(consent_file().read_text())["download"])
    except Exception:
        return None


def set_consent(yes):
    f = models_dir() / "consent.json"
    f.write_text(json.dumps({"download": bool(yes), "date": time.strftime("%Y-%m-%d")}, indent=1) + "\n")
    return f


def model_table(highlight=()):
    rows = []
    for n, m in REGISTRY.items():
        if n == "mobilesam-decoder":
            continue
        size = m["bytes"] + (REGISTRY["mobilesam-decoder"]["bytes"] if n == "mobilesam-encoder" else 0)
        mark = "*" if n in highlight or (n == "mobilesam-encoder" and "mobilesam-decoder" in highlight) else " "
        have = "installed" if local_path(n) else "not downloaded"
        rows.append(f" {mark} {m['model'].replace(' (image encoder)', ''):<24} {_mb(size):>6}  {m['license']:<10} {have:<15} {m['does']}")
    return "\n".join(rows)


def _need_consent_msg(name):
    m = REGISTRY[name]
    total = sum(x["bytes"] for x in REGISTRY.values())
    return f"""MODEL DOWNLOAD NEEDS THE USER'S OK (asked only once, ever).
{m['used_by']} needs {m['model']} ({m['does']}), which is not on this machine yet.

Tell the user once, in their language, and ask whether local models may be downloaded when needed:
  - what: the models below (* = needed right now); each is downloaded only when first needed, all together ~{_mb(total)}
  - source: Hugging Face (huggingface.co, or the mirror in $HF_ENDPOINT), sha256-verified, no account or key
  - stored in: {models_dir(create=False)}
  - if they decline: you will still finish the film with code-only approaches; concretely
      depth  -> {REGISTRY['depth-anything-v2-small']['without']}
      cutout -> {REGISTRY['birefnet-lite']['without']}
      pick   -> {REGISTRY['mobilesam-encoder']['without']}
      fill   -> {REGISTRY['lama']['without']}
{model_table(highlight=[name])}

Then record the answer (never ask again) and re-run this command:
  {SKILL_DIR / 'scripts' / 'models.py'} consent yes      # or: consent no"""


def _declined_msg(name):
    m = REGISTRY[name]
    return (f"DECLINED - the user chose not to download local models, so {m['model']} is unavailable.\n"
            f"Work around it and still finish the film: {m['without']}.\n"
            f"(If the user later changes their mind: {SKILL_DIR / 'scripts' / 'models.py'} consent yes)")


# ---------------- download ----------------
def _url(m):
    ep = os.environ.get("HF_ENDPOINT", "").strip().rstrip("/")
    return m["url"].replace(HF, ep, 1) if ep else m["url"]


def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def download(name):
    m = REGISTRY[name]
    dst = models_dir() / m["file"]
    url = _url(m)
    tmp = dst.with_name(f"{dst.name}.part{os.getpid()}")
    print(f"downloading {m['model']} (~{_mb(m['bytes'])}, once) from {url.split('/')[2]} -> {dst}", file=sys.stderr)
    t0, last = time.time(), 0.0
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "lemo-wake"})
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or m["bytes"])
            got = 0
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b); got += len(b)
                now = time.time()
                if now - last > 0.5 or got == total:
                    last = now
                    print(f"\r  {got / total * 100:5.1f}% {_mb(got)}/{_mb(total)}  {got / max(now - t0, 1e-6) / 1e6:.1f}MB/s ",
                          end="", file=sys.stderr, flush=True)
        print(file=sys.stderr)
        if tmp.stat().st_size != m["bytes"]:
            raise IOError(f"wrong size {tmp.stat().st_size} != {m['bytes']} (truncated download?)")
        if _sha256(tmp) != m["sha256"]:
            raise IOError("sha256 mismatch (corrupted file, or the mirror serves a different file)")
        os.replace(tmp, dst)
    except KeyboardInterrupt:
        tmp.unlink(missing_ok=True); die("download interrupted", 130)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        mirror = "" if os.environ.get("HF_ENDPOINT") else \
            "  - mainland China / blocked network: retry with HF_ENDPOINT=https://hf-mirror.com <same command>\n"
        die(f"downloading {m['model']} failed: {e}\n  url: {url}\nWhat to try:\n{mirror}"
            f"  - another mirror or a proxy (HF_ENDPOINT=<mirror root>), then re-run\n"
            f"  - download manually from {m['url']}\n    and save it as exactly: {dst}\n"
            f"  - or point LEMO_WAKE_MODELS at a folder that already has {m['file']}\n"
            f"If nothing works, finish the film without it: {m['without']}.", EXIT_DOWNLOAD_FAILED)
    print(f"{m['model']} ready ({time.time() - t0:.0f}s)", file=sys.stderr)
    return dst


def fetch(name):
    """Local path of a model; downloads it if missing - but only after the user's one-time consent."""
    if name not in REGISTRY:
        die(f"unknown model {name} (known: {', '.join(REGISTRY)})")
    p = local_path(name)
    if p:
        return str(p)
    c = consent()
    if c is None:
        print(_need_consent_msg(name), file=sys.stderr); sys.exit(EXIT_NEED_CONSENT)
    if c is False:
        print(_declined_msg(name), file=sys.stderr); sys.exit(EXIT_DECLINED)
    return str(download(name))


# ---------------- inference helpers ----------------
def providers():
    import onnxruntime as ort
    avail = ort.get_available_providers()
    want = os.environ.get("LEMO_WAKE_EP", "cpu").lower()
    if want == "coreml" and "CoreMLExecutionProvider" in avail:
        return ["CoreMLExecutionProvider", "CPUExecutionProvider"]
    if want == "cuda" and "CUDAExecutionProvider" in avail:
        return ["CUDAExecutionProvider", "CPUExecutionProvider"]
    return ["CPUExecutionProvider"]


def session(name):
    """Fetch (if needed, with consent) and build an InferenceSession; falls back to CPU if CoreML/CUDA fails."""
    import onnxruntime as ort
    path = fetch(name)
    so = ort.SessionOptions()
    so.log_severity_level = 3
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    prov = providers()
    try:
        return ort.InferenceSession(path, so, providers=prov)
    except Exception as e:
        if prov == ["CPUExecutionProvider"]:
            die(f"loading model {name} failed: {e}\n  the file may be corrupted: delete {path} and re-run to download it again")
        print(f"! {prov[0]} unavailable ({str(e).splitlines()[0][:120]}), falling back to CPU", file=sys.stderr)
        try:
            return ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
        except Exception as e2:
            die(f"loading model {name} failed: {e2}\n  the file may be corrupted: delete {path} and re-run to download it again")


def imread(path, flags=None):
    """Read an image via imdecode (works with non-ASCII paths on Windows). BGR uint8 by default."""
    import cv2, numpy as np
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        die(f"cannot read image: {path}")
    im = cv2.imdecode(data, cv2.IMREAD_COLOR if flags is None else flags)
    if im is None:
        die(f"cannot decode image (unsupported format?): {path}")
    return im


def imwrite(path, im, params=()):
    import cv2
    ext = os.path.splitext(path)[1].lower() or ".png"
    ok, buf = cv2.imencode(ext, im, list(params))
    if not ok:
        die(f"cannot write image: {path} (unsupported extension {ext}?)")
    Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    buf.tofile(str(Path(path).expanduser()))


if __name__ == "__main__":
    import runpy
    runpy.run_path(str(Path(__file__).with_name("models.py")), run_name="__main__")
