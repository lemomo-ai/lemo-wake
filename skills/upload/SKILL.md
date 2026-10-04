---
description: "Share a film to the lemo-wake gallery. 把动图投稿到作品墙。"
when_to_use: "Share a finished lemo-wake film to the community gallery on GitHub (github.com/lemomo-ai/lemo-wake, gallery branch). Checks the film, makes a small preview, strips photo metadata, asks the user to confirm everything, then opens a pull request from the user's own GitHub account. Only when the user asks to upload / share / submit a film."
argument-hint: [film file or project folder]
disable-model-invocation: true
license: MIT
metadata:
  version: "1.0.0"
  author: Lemomo
  homepage: https://github.com/lemomo-ai/lemo-wake
  gallery: https://lemomo-ai.github.io/lemo-wake/
---

# Share a film to the lemo-wake gallery

The gallery is the `gallery` branch of https://github.com/lemomo-ai/lemo-wake. A submission is one folder, `films/<id>/`, added through a pull request from the user's own GitHub account. A maintainer reviews it; after the merge it appears on the gallery page automatically.

**Talk to the user in their language** (Chinese or English; follow the user). These docs are in English only for you.

**Nothing leaves the machine until the user has seen exactly what will be published and said yes.** Never upload on your own initiative, never upload someone else's film, never skip the confirmation.

`$U` = this skill's folder: `${CLAUDE_SKILL_DIR}` (if that still reads literally as `${...}`, it is the folder that contains this SKILL.md). Never take a path from the shell variables `CLAUDE_SKILL_DIR` / `CLAUDE_PLUGIN_DATA`.

## 1. Find the film

The argument, if any, is a film file or a lemo-wake project folder. Otherwise look in the current working directory for the most recent project (`<slug>-alive/`) and its `<slug>.webp`. The gallery takes an animated **WebP or GIF** (prefer the WebP: original size, best quality). If it is unclear which film is meant, ask.

## 2. Collect the details (one message, in the user's language)

Ask in a single message, with your suggestion filled in for each so the user can just say "OK":
- **Title** - short, up to 80 characters; suggest "<what the image is> · <the move>", e.g. "炉边三花猫 · 炉火醒来". The gallery is bilingual, so also suggest the other language's version (Chinese title -> English, English title -> Chinese), e.g. "Calico by the fire · The fire wakes up". Pass the Chinese one as `--title` and the English one as `--title-en`.
- **Category** - the scene the picture comes from (not its style): `life` (everyday photos: food, pets, places, travel), `people` (portraits, couples, family, milestones), `poster` (posters, ads, campaigns), `brand` (logos, brand marks), `data` (charts, reports), `social` (Xiaohongshu covers, chat screenshots, social posts), `sticker` (stickers, greeting images), `art` (paintings, drawings, picture books). Suggest one.
- **Credit** - the name shown under the film. Default: their GitHub username.
- **Original image** (optional) - show the source next to the film? It is saved as a JPEG with all metadata (location, camera, date) removed, long side at most 1600 px.
- **Notes** (optional) - a few lines about how it was made (the director notes can be a starting point). Published as written; no personal details.
- **License and consent** - the film (and the original, if included) is published under **CC BY-NC 4.0** (others may share and adapt it with credit, not for commercial use), and the lemo-wake project may show it in its README, gallery and posts about the project. They must have the rights to the image: their own photo or artwork, or one they are allowed to share. Photos of other people need those people's OK.

Point out anything that looks private: faces of people other than the user, children, names, phone numbers, addresses, chat contents, licence plates, documents. Suggest leaving such a film out rather than publishing it.

## 3. Prepare and show what will be published

```bash
uv run $U/scripts/prepare.py <film> --title "..." --title-en "..." --category <cat> --author "<credit>" \
    --author-url https://github.com/<login> [--source <original image>] [--notes <notes.md>] \
    --out <workdir>/lemo-wake-upload --agree
```
`--agree` records the user's yes to the license and consent from step 2 - pass it only if they said yes. `<login>` is their GitHub username (`gh api user --jq .login`; if `gh` is not logged in yet, see step 4). The folder id is `<date>-<login>-<slug>`.
It checks the film (animated WebP/GIF, at most 8 MB; a bigger WebP is re-compressed, never below 12 fps / q50 - if it still does not fit it stops and says so), makes `preview.webp` (long side 360, at most 1 MB) for the gallery grid, writes the original without metadata, writes `meta.json`, and prints a JSON summary. It warns about text in the notes that looks like an email, phone number or local file path - fix those before going on. Use a work folder under the current working directory (not the user's image folder).

Show the user the summary: the folder `films/<id>/` with every file and its size, the full `meta.json`, the notes text if any, and where it goes (a pull request to lemomo-ai/lemo-wake, branch `gallery`, from their GitHub account `<login>`; the pull request and files are public once the repository is public). Ask for a clear yes.

## 4. Submit (only after the yes)

Needs the GitHub CLI (`gh`) logged in. If `gh auth status` fails, ask the user to run `! gh auth login` themselves - never handle their password or token.

```bash
python3 $U/scripts/submit.py <workdir>/lemo-wake-upload/films/<id>
```
It always submits to the official repository lemomo-ai/lemo-wake - also if this plugin came from a fork or a copy; never point it elsewhere. It forks the repository if the user cannot push to it, puts the folder on a new branch `submit/<id>` based on the current gallery, commits under the user's GitHub no-reply address (their real email is never used), pushes, opens the pull request and prints its URL. Exit 20 = `gh` missing or not logged in; 21 = the id already exists in the gallery (choose another title or slug); 22 = a git or GitHub step failed (the message says which; fix it, then run again - it is safe to repeat).

Tell the user the pull request URL, that an automatic check runs first and a maintainer reviews it, and that it shows up on https://lemomo-ai.github.io/lemo-wake/ after the merge. Then delete the work folder.

---

lemo-wake 1.0.0 · official repository: https://github.com/lemomo-ai/lemo-wake
