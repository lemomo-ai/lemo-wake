#!/usr/bin/env python3
"""Open a pull request that adds one prepared film folder to the lemo-wake gallery.
Run it only after the user has seen the folder and said yes.

    submit.py <dir>/films/<id> [--dry-run]

Uses the GitHub CLI (gh) as the user's own account. If the user cannot push to the repository it forks it
first. Commits use the account's GitHub no-reply address, never the email in the user's git config.
--dry-run checks everything (login, id free, files) and prints the plan without forking, pushing or opening anything.

Always targets the official repository lemomo-ai/lemo-wake (branch gallery), never a fork - also when this plugin
was installed from a fork or a copy. It refuses a target that is a fork, and checks the opened PR's URL.

Exit codes: 20 gh missing / not logged in, 21 id already in the gallery, 22 a git or GitHub step failed.
"""
import argparse, json, shutil, subprocess, sys, tempfile, time
from pathlib import Path

OFFICIAL = "lemomo-ai/lemo-wake"   # the one real gallery; forks and copies of this plugin still submit here
ALLOWED = {"meta.json", "film.webp", "film.gif", "preview.webp", "source.jpg", "notes.md"}


def die(msg, code):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def run(cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        die(f"{' '.join(cmd[:3])} ... failed:\n{(p.stderr or p.stdout).strip()[-800:]}", 22)
    return p


def gh_json(*args):
    p = run(["gh", "api", *args], check=False)
    return json.loads(p.stdout) if p.returncode == 0 and p.stdout.strip() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--repo", default=OFFICIAL, help=argparse.SUPPRESS)
    ap.add_argument("--base", default="gallery")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    folder = Path(a.folder).expanduser().resolve()
    fid = folder.name
    names = {p.name for p in folder.iterdir()} if folder.is_dir() else set()
    if not {"meta.json", "preview.webp"} <= names or not names & {"film.webp", "film.gif"} or names - ALLOWED:
        die(f"{folder} is not a folder made by prepare.py (expected meta.json, film.webp|gif, preview.webp)", 22)
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    if meta.get("consent") is not True:
        die("meta.json has no consent - run prepare.py again with the user's agreement", 22)

    if not shutil.which("gh"):
        die("the GitHub CLI (gh) is not installed: https://cli.github.com", 20)
    if run(["gh", "auth", "status"], check=False).returncode != 0:
        die("gh is not logged in - ask the user to run: gh auth login", 20)
    user = gh_json("user")
    if not user:
        die("could not read the GitHub account (gh api user)", 20)
    login, uid = user["login"], user["id"]
    email = f"{uid}+{login}@users.noreply.github.com"

    repo = gh_json(f"repos/{a.repo}")
    if not repo:
        die(f"cannot see {a.repo} - is it public, or does this account have access?", 22)
    if repo.get("fork") or repo.get("full_name", "").lower() != a.repo.lower():
        die(f"{a.repo} is a fork or has moved (now {repo.get('full_name')}); films go to the official gallery {OFFICIAL}", 22)
    if a.repo.lower() != OFFICIAL.lower():
        print(f"! submitting to {a.repo}, not the official gallery {OFFICIAL}", file=sys.stderr)
    if gh_json(f"repos/{a.repo}/contents/films/{fid}?ref={a.base}") is not None:
        die(f"films/{fid} already exists in the gallery - choose another title/slug and prepare again", 21)
    can_push = bool(repo.get("permissions", {}).get("push"))
    target = a.repo if can_push else f"{login}/{a.repo.split('/')[1]}"
    branch = f"submit/{fid}"
    title = f"Film: {meta['title']}"
    files = {n: (folder / n).stat().st_size for n in sorted(names)}

    plan = {"account": login, "commit_email": email, "push_to": f"{target}:{branch}",
            "fork_first": not can_push, "pull_request": f"{a.repo} <- {branch} (base {a.base})",
            "title": title, "files": {f"films/{fid}/{n}": s for n, s in files.items()}}
    if a.dry_run:
        print(json.dumps({"dry_run": True, **plan}, ensure_ascii=False, indent=2))
        return

    if not can_push and not gh_json(f"repos/{target}"):
        run(["gh", "repo", "fork", a.repo, "--clone=false"])
        for _ in range(30):
            if gh_json(f"repos/{target}"):
                break
            time.sleep(2)
        else:
            die(f"the fork {target} did not appear in time - run again in a minute", 22)

    cred = ["-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]
    with tempfile.TemporaryDirectory(prefix="lemo-wake-upload-") as tmp:
        work = Path(tmp) / "repo"
        run(["git", *cred, "clone", "--quiet", "--depth", "1", "--branch", a.base, "--filter=blob:none",
             "--sparse", f"https://github.com/{a.repo}.git", str(work)])
        run(["git", "sparse-checkout", "set", f"films/{fid}"], cwd=work)
        run(["git", "checkout", "--quiet", "-b", branch], cwd=work)
        dest = work / "films" / fid
        dest.mkdir(parents=True, exist_ok=True)
        for n in names:
            shutil.copyfile(folder / n, dest / n)
        run(["git", "add", f"films/{fid}"], cwd=work)
        run(["git", "-c", f"user.name={login}", "-c", f"user.email={email}", "commit", "--quiet",
             "-m", f"Add film: {meta['title']} ({fid})"], cwd=work)
        run(["git", *cred, "push", "--quiet", "--force", f"https://github.com/{target}.git",
             f"HEAD:refs/heads/{branch}"], cwd=work)

    body = "\n".join([
        f"**{meta['title']}** · `{meta['category']}` · by {meta['author']}", "",
        "| file | size |", "|---|---|", *[f"| `{n}` | {s / 1e6:.2f} MB |" for n, s in files.items()], "",
        "- [x] I have the rights to this image and film (my own work, or I am allowed to share it; "
        "people shown in it agreed).",
        "- [x] I publish the film (and the original, if included) under CC BY-NC 4.0 and agree that the "
        "lemo-wake project may show it in its README, gallery and posts about the project.", "",
        f"Submitted with `/lemo-wake:upload` (lemo-wake {meta.get('lemo_wake', '?')}, https://github.com/{OFFICIAL}).",
    ])
    existing = run(["gh", "pr", "list", "--repo", a.repo, "--head", branch, "--state", "open",
                    "--json", "url", "--jq", ".[0].url"], check=False).stdout.strip()
    if existing:
        print(existing)
        return
    head = branch if can_push else f"{login}:{branch}"
    p = run(["gh", "pr", "create", "--repo", a.repo, "--base", a.base, "--head", head,
             "--title", title, "--body", body])
    url = p.stdout.strip().splitlines()[-1]
    if not url.lower().startswith(f"https://github.com/{a.repo.lower()}/pull/"):
        die(f"the pull request did not land in {a.repo}: {url}", 22)
    print(url)


if __name__ == "__main__":
    main()
