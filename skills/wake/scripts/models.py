#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///
"""Local models: status, one-time download consent, pre-download.

  models.py                    list the models, where they are stored, consent status
                               (consent only matters for a model that is not installed yet)
  models.py where              print the models folder
  models.py consent yes|no     record the user's answer (asked once; scripts never ask again)
  models.py fetch all|NAME...  pre-download (needs consent; --yes records consent at the same time)

Names: depth-anything-v2-small, birefnet-lite, modnet, mobilesam-encoder, mobilesam-decoder, lama
(`mobilesam` = both MobileSAM files). Downloads honour HF_ENDPOINT (e.g. https://hf-mirror.com).
Exit codes of the model scripts: 10 = consent not asked yet, 11 = user declined, 12 = download failed.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _models as M


def main(argv):
    if not argv:
        c = M.consent()
        print(f"models folder: {M.models_dir(create=False)}")
        if M.LEGACY_DIR.is_dir() and any(M.LEGACY_DIR.glob("*.onnx")):
            print(f"also reused:   {M.LEGACY_DIR}")
        if c is None:
            missing = [n for n in M.REGISTRY if not M.local_path(n)]
            c_txt = ("not needed (models already installed)" if not missing else
                     "not asked yet - asked only when a missing model must actually be downloaded")
        else:
            c_txt = "yes" if c else "no (declined)"
        print(f"download consent: {c_txt}")
        print(M.model_table())
        return 0
    cmd = argv[0]
    if cmd == "where":
        print(M.models_dir(create=False)); return 0
    if cmd == "consent":
        if len(argv) < 2 or argv[1].lower() not in ("yes", "no", "y", "n"):
            M.die("usage: models.py consent yes|no")
        yes = argv[1].lower().startswith("y")
        f = M.set_consent(yes)
        print(f"recorded consent={'yes' if yes else 'no'} in {f}"); return 0
    if cmd == "fetch":
        names = [a for a in argv[1:] if not a.startswith("-")]
        if "--yes" in argv:
            M.set_consent(True)
        if not names:
            M.die("usage: models.py fetch all|NAME... [--yes]")
        if names == ["all"]:
            names = list(M.REGISTRY)
        names = [x for n in names for x in (["mobilesam-encoder", "mobilesam-decoder"] if n == "mobilesam" else [n])]
        for n in names:
            print(M.fetch(n))
        return 0
    M.die(f"unknown command {cmd!r}\n{__doc__}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
