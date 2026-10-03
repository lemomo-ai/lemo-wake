---
description: "Turn one image into a ~5 s looping animation. 把一张图做成约 5 秒的循环动图。"
when_to_use: "Turn any single picture the user gives (their own photo, portrait, poster, illustration, product shot, logo, chart, sticker, Xiaohongshu cover, chat or app screenshot...) into a ~5 second seamlessly looping animation, by reading the image, taking it apart, rebuilding and re-choreographing its elements in code. Delivers MP4 (posts), GIF (chats), WebP (web) and a WeChat sticker GIF, all from the same film at the source's own size. You decide how; the docs are references. No image generation, no API keys. Use whenever the user gives an image and says \"make it move\", \"animate this\", \"turn it into a GIF / WebP / motion poster / cinemagraph\", \"lemo-wake\", or in Chinese \"让它动起来\", \"做成动图\", \"做成 GIF\", \"动态海报\", \"给这张图加动效\", \"叫醒这张图\", \"能不能变成动态的\", \"做个表情包动图\" - even if they don't mention a skill, a duration or a format. Not for: multi-shot narrative films written from scratch, plain filters or crops, generating new images from text."
argument-hint: <image path> [seconds] [idea]
license: MIT
metadata:
  version: "1.0.0"
  author: Lemomo
  homepage: https://github.com/lemomo-ai/lemo-wake
  gallery: https://lemomo-ai.github.io/lemo-wake/
---

# lemo-wake: wake up a still image

Input: one image. Output: one film made for that image (about 5 s, loops forever), delivered as four files.

**Everything in this skill is a reference, not a rule.** You are the director and the motion designer: you look at the image and decide what happens, how big, how it ends and when it is good enough. The references, types, effect blocks and scripts are tools and lessons from earlier films. If you have a better idea, do it; no need to explain why you departed from the docs.

Fixed boundaries: **no image generation, no services that need API keys, no calling other skills.** Material comes only from the image itself, from code, and from local models (depth, cut-out, hole filling).

**Talk to the user in their language.** Everything you say to the user - questions, progress updates, the final summary - is in the language the user writes in (Chinese or English; follow the user). These docs are in English only for you.

**Read `references/taste.md` before planning.** It is the most important reference: what viewers loved and rejected. In short: things in the picture must really move (light or colour alone is not motion); default to big actions that chain across the whole picture; the signature move grows from this image; the film keeps the source's exact size and aspect ratio.

## Paths

Only the text substituted into this file counts. **Never take the shell variables CLAUDE_SKILL_DIR or CLAUDE_PLUGIN_DATA** (`echo`, `env`) for these paths: the Bash environment can carry values that belong to another plugin (seen in practice: another plugin's data folder), and using them would put models and history in someone else's folder. The scripts never read those variables either; the only path override they honour is `LEMO_WAKE_MODELS` (ignored, with a warning, if it points into another plugin's data folder).

- `$S` = this skill's folder: `${CLAUDE_SKILL_DIR}`. If that still reads literally as a `${...}` placeholder, `$S` is the folder that contains this SKILL.md (the path you loaded it from, e.g. `~/.claude/skills/lemo-wake`). Scripts are in `$S/scripts/`.
- Persistent data folder: `${CLAUDE_PLUGIN_DATA}` - kept across plugin updates, never inside the plugin folder itself.
  - If the line above shows a real path (and it belongs to lemo-wake): put models there by prefixing every model command with `LEMO_WAKE_MODELS="<that path>/models"`, and keep the history at `<that path>/history.jsonl`. Shell variables do not survive between your commands, so write the prefix each time.
  - If it still starts with `${` (e.g. the skill was installed by copying or linking the folder): set nothing. The scripts find their models folder themselves (`$S/scripts/models.py where` prints it; usually `$S/models/`) and the history lives at `$S/history.jsonl`.
- Project output goes into the current working directory, never into the folder of the user's image.

## Workflow

Go at your own pace; skip or repeat steps.

**0. First run: check the environment**
```bash
node $S/scripts/doctor.mjs          # says what is missing; --fix installs npm deps + headless browser (~190 MB)
```
Needs Node >= 18, ffmpeg, uv. Tested on macOS; on Linux/Windows, if a step fails, work out what is missing and fix it (install a dependency, adjust a path, set `CHROME=<browser path>`).

**1. Create the project**
```bash
$S/scripts/new_project.py <image> <slug> --dur 4.5    # render length; total = this + any reset transition appended later
```
The canvas is the source's own pixel size (HEIC converted, EXIF rotated; only images with a long side over 2560 px are scaled down for speed, and it says so - `--max-long 0` keeps everything). All coordinates refer to `<src>/assets/source.*`.

The length can change any time: edit `dur` in `<src>/config.js` and re-render (`render.mjs` renders `fps x dur` frames, t = 0 .. dur - 1/fps). With an in-picture ending, `dur` is the whole film and `render(dur)` should look like `render(0)`; with a `reset.py` transition, the transition is added after `dur`.

**2. Read the image and plan** (write it into `<proj>/DIRECTOR.md`)

Decide: what kind of image this is, what its elements naturally do, which action belongs only to this image, what state the picture starts in, how the action travels across it, where the climax is, how it ends and loops. References:
- `$S/references/taste.md` - the quality bar (read first).
- `$S/types/<kind>.md` - what works for this kind of image, with case cards of approved films: `photo`, `portrait`, `multi` (several photos), `poster`, `illustration`, `clay` (clay / paper-cut / 3D), `ui` (screenshots), `chart`, `logo`, `sticker` (stickers / avatars), `xhs` (Xiaohongshu covers / text cards). Mixed images: read two.
- `$S/references/motion-grammar.md` - reading questions, structures, camera, motion principles, rhythm, self-check.
- `$S/references/recipes.md` - techniques that worked across types.
- `$S/references/effects.md` - the 49 effect blocks and 27 reset transitions.
- `$S/references/pitfalls.md` - technical traps.
- The history file (see Paths), if it exists: recent films, so this one isn't more of the same. Change `seed` values every film; `FX.pick(name, seed)` draws parameters from recommended ranges.

**3. Measure and prepare material**
```bash
$S/scripts/measure.py grid <src>/assets/source.jpg <proj>/grid.png   # coordinate grid (out optional: default <name>-grid.png next to the image)
$S/scripts/measure.py info|palette <img>                             # size / main colours
$S/scripts/measure.py bbox|runs|vruns <img> --color '#hex' ...       # element bounds (-h lists the options)
$S/scripts/depth.py   <src>/assets/source.jpg --out <src>/assets/depth.png      # depth (near = white)
$S/scripts/segment.py <src>/assets/source.jpg --out <src>/assets/mask.png [--cutout subj.png]
      # --model general (main subject) | portrait (people, hair) | sam (pick elements: --point x,y ... --neg x,y --box x0,y0,x1,y1 --each)
      # several objects in one mask: --box 20,30,300,360 --box 400,30,700,360 (write the numbers out; zsh won't split an unquoted $VAR)
$S/scripts/inpaint.py <src>/assets/source.jpg <mask.png> --out <src>/assets/plate.png [--engine lama|opencv] [--dilate N] [--split]
      # --split: the mask holds several neighbouring objects (a row of planets, products, icons + labels) - fill each one
      #          on its own at near-native resolution instead of one big downscaled blob (watch stderr for "downscale 3x")
node $S/scripts/fetch_fonts.mjs <src> "family=..."                # Google Fonts saved locally; CJK fonts: add &text= with the used characters
```
Text, flat shapes, geometry, lines, textures and light are best rebuilt in code; photos, real people and specific products come from the source. For SAM, a `--box` is often steadier than a single point. (Model commands: add the `LEMO_WAKE_MODELS=...` prefix from Paths; see "Local models" below.)

**4. Build `<src>/index.html`** from the template (layers `#view` frame / `#cam` camera / `#post` post-processing).
- `render.mjs` grabs frames with several headless browsers in parallel and out of order, so `window.render(t)` must draw the same frame for the same `t` every time (no state carried from the previous frame). Set `window.READY = true` only after all images and fonts are loaded.
- `lib.js`: easing, keyframes, springs, shake, seamless loops, noise, camera, parallax, glyphs, ink, ribbons, tiles, pixel particles, noise dissolve, text animation, number rolls, analytic particles (see the comments in the file). `L.Camera` never zooms below 1 and keeps the view inside the source; to look past the edge, paint that area and pass `extend` (recipes.md, "Extending the canvas beyond the source").
- The template's base colour follows the source's border and its paper grain is off (`GRAIN = null`); switch grain on for paper or print looks, not for dark images.
- `fx.js`: 49 ready-made effect blocks, `FX.make(name, params)` -> `draw(g, t)`. Good as supporting actors, atmosphere, loop transitions or raw material; the signature move is usually your own code.
- three.js may be downloaded locally if real 3D helps.

**5. Look at frames and iterate**
```bash
node $S/scripts/render.mjs <src> stills 0.2 1.0 2.0 3.0 4.4
$S/scripts/sheet.py <proj>/sheet.png --stills <src> 0.2 1.0 2.0 3.0 4.4
$S/scripts/sheet.py <proj>/vs.png --vs-source <src> 4.4           # compare with the source (render that still first)
$S/scripts/sheet.py <proj>/f.png --frames <src>/frames --idx 0 40 80 -1   # after a full render: by frame number (or --n 8)
```
Rendering is fast, so look often. A first version usually only "moves"; if it is not big or good enough, start over.

**6. Full render and the loop**
```bash
node $S/scripts/render.mjs <src> frames                           # -> <src>/frames; page errors go to render.log, exit code 2
$S/scripts/reset.py --list                                        # 27 frame-level transitions
$S/scripts/reset.py <src>/frames --kind <kind> [--seed N] [--origin x,y] [--pre-hold .3]   # -> <src>/frames_loop
```
The content does not need to return to its start: the end can be full and the beginning empty. Join last frame to first with a transition that fits the style - an in-picture ending you write (often the best), an fx.js in-picture transition (`backplay`, `passby`, `pushcut`, `lightcut`), or a `reset.py` kind. The first frame doubles as the still preview in many apps, so make it look good.

**7. Encode and QA**
```bash
$S/scripts/encode.py <frames dir> <proj>/<slug>                   # -> 4 files + <slug>.encode.json
$S/scripts/qa.py <frames dir> --src <src> --encode <proj>/<slug>.encode.json
```
The four files, all from the same frames:

| File | Size | For |
|---|---|---|
| `<slug>.mp4` | original pixels, H.264 (an odd width or height is rounded down to even: 941 -> 940) | posts: WeChat Moments, Xiaohongshu, Douyin, Instagram, X |
| `<slug>.gif` | scaled only as far as needed, <= 5 MB, width < 1080 (busy full-frame motion can end up ~300-450 px wide) | chats: WeChat, QQ, Weibo |
| `<slug>.webp` | original pixels; ~8 MB is a target (quality/fps drop a little first, never below 12 fps / q50) | web pages, GitHub, galleries |
| `<slug>-sticker.gif` | longest side 240, dropping to 200 when needed to stay <= 500 KB | WeChat custom sticker |

Use `--no-mp4 / --no-gif / --no-webp / --no-sticker` to skip one (a rerun merges into the existing `<slug>.encode.json`, so skipped formats keep their entries), and `--gif-max / --webp-max / --sticker-max` (MB) when the user names a platform limit. `--gif-width` is only a cap: the size limit decides the GIF's width, so for a wider chat GIF raise `--gif-max` as well. qa.py FAIL usually means a technical problem worth fixing; WARN is often intentional (an empty first frame by design). It also writes `qa_sheet.jpg` whose last tile is the first frame, to check the loop seam.

**8. Deliver**

Append one line to the history file (see Paths; create it if missing):
```json
{"date":"2026-01-31","slug":"cat","image_type":"photo","arc":"build","signature":"breakfast crouches, leaps out, bounces back onto the plates","main":"own code: SAM sprites + squash","fx":["steam seed=12"],"reset":"in-picture: true loop","dur":5,"verdict":"","why":""}
```
If the user later gives a verdict, fill in `verdict` and `why`.

Tell the user (in their language): the four file paths and sizes and what each is for, the signature move and structure, how it loops, anything notable from QA, and what can only be judged by watching it play. Invite changes. If the user likes the film, you may mention once that it can be shared to the community gallery with `/lemo-wake:upload` (plugin installs); never upload anything yourself.

## Local models

Five small ONNX models run on the CPU: Depth Anything V2 Small (depth, 99 MB), BiRefNet-lite (subject cut-out, 224 MB), MODNet (portrait matting, 26 MB), MobileSAM (pick elements, 44 MB in 2 files), LaMa (fill holes, 208 MB). Each is downloaded from Hugging Face only when first needed. Many films need none of them. `$S/scripts/models.py` shows status. **Consent is only about downloading:** a model already on disk just runs, with no question to the user (status then reads "not needed (models already installed)"). Ask only when a script actually stops with exit code 10.

- **Exit code 10 - ask once.** The first time a model would be downloaded, the script stops and prints what is needed. Tell the user once, in their language: which model(s), what they are for, size, source (Hugging Face), where they will be stored, and what declining costs (you will still finish the film with code-only approaches; say concretely what gets harder, e.g. depth parallax, clean cut-outs of photo subjects, filling the hole behind a moved object). Record the answer with `$S/scripts/models.py consent yes` or `consent no` and re-run. It is never asked again. If you already know in step 2 that you will want a model that is not installed and `models.py` says consent is "not asked yet", ask early so the user isn't interrupted mid-way.
- **Exit code 11 - declined.** Do not ask again; work around it.
- **Exit code 12 - download failed.** Find a way yourself: retry with a mirror (`HF_ENDPOINT=https://hf-mirror.com`, common for mainland China), a proxy, or a manual download to the exact path the script prints. Files are sha256-checked either way.
- `models.py fetch all` pre-downloads everything (only when the user wants that).

**When a model is unavailable - declined, or the download failed - never get stuck.** Find a reasonable compromise with your own methods and still complete the film: colour keys, `measure.py bbox`, hand-drawn polygons or masks, elements rebuilt in code, layered 2D parallax instead of depth, `inpaint.py --engine opencv` for small holes, code-painted backgrounds, or staging that keeps objects in place and hides holes behind motion, dust, fog or paint. Mention briefly in the final summary which compromise you chose.

## Adjustable (decide yourself if the user doesn't say)

- Duration: about 5 s including the loop transition. If the user wants N seconds, scale the beats but keep physical timings (impacts, drops) about the same; give the extra time to reveals and holds. Films that must feature many parts (several photos) may run longer.
- Size: always the source's own size; see taste.md. Size limits only change the chat GIF and the sticker; the WebP limit is a target.
- Frame rate: render at 30; the WebP drops to 12-15 fps as needed, the chat GIF and sticker lower.

---

lemo-wake 1.0.0 · official repository: https://github.com/lemomo-ai/lemo-wake · gallery: https://lemomo-ai.github.io/lemo-wake/
