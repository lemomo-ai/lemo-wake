---
description: "Split one image into editable layers (PSD + PNG). 把一张图拆成图层（PSD + PNG）。"
when_to_use: "Take one picture apart into separate layers for editing elsewhere: each person, object or text block cut out on its own transparent layer, the clean background behind them filled in, plus a depth map. Delivers a layered PSD (Photoshop, Photopea, Affinity, Procreate), PNG layers cropped to size and a layers.json with positions and stacking order (After Effects, Figma, game engines). Works on any image, or reuses the parts of a finished lemo-wake project. Use when the user says \"split this into layers\", \"give me a PSD\", \"separate the people / objects from the background\", \"export the layers\", or in Chinese \"拆成图层\", \"分层\", \"导出 PSD\", \"把人和背景分开\", \"抠出来分层\", \"给我图层\". Not for: animation (that is lemo-wake's wake), removing a background only (one cut-out is enough), editable text layers, generating new pixels for hidden areas."
argument-hint: <image or lemo-wake project folder> [what to separate]
license: CC-BY-NC-4.0
metadata:
  version: "1.1.0"
  author: Lemomo
  homepage: https://github.com/lemomo-ai/lemo-wake
---

# Split an image into layers

You take one picture apart the way a designer would want to receive it: every element that someone might move, recolour or animate on its own layer, the background behind them clean, everything aligned to the original pixel grid. Then you pack it as a PSD, PNG layers and a `layers.json`.

**Talk to the user in their language** (Chinese or English; follow the user). These docs are in English only for you.

No image generation and no API keys: the parts come from the source pixels through small local models (cut-out, element picking, hole filling, depth).

## Paths

Only the text substituted into this file counts. **Never take the shell variables CLAUDE_SKILL_DIR or CLAUDE_PLUGIN_DATA** (`echo`, `env`) for these paths: the Bash environment can carry values that belong to another plugin.

- `$L` = this skill's folder: `${CLAUDE_SKILL_DIR}`. If that still reads literally as a `${...}` placeholder, it is the folder that contains this SKILL.md.
- `$W` = the wake skill's scripts, next to this skill: `$L/../wake/scripts`. The model tools live there (`segment.py`, `inpaint.py`, `depth.py`, `models.py`, `measure.py`). If that folder is missing, this skill was installed on its own; tell the user to install the lemo-wake plugin (`claude plugin install lemo-wake@lemo-wake`).
- Models folder: `${CLAUDE_PLUGIN_DATA}`. If that shows a real path that belongs to lemo-wake, prefix every model command with `LEMO_WAKE_MODELS="<that path>/models"` (shell variables do not survive between your commands, so write the prefix each time). If it still starts with `${`, set nothing; the scripts find their folder themselves (`$W/models.py where`).
- Output goes into the current working directory, never into the folder of the user's image.

## Local models and consent

The tools use up to five small ONNX models on the CPU: BiRefNet-lite (subject, 224 MB), MODNet (people, 26 MB), MobileSAM (pick elements, 44 MB), LaMa (fill the background, 208 MB), Depth Anything V2 Small (depth, 99 MB). A model already on disk just runs. If `$W/models.py` (no arguments) shows some missing and consent "not asked yet", ask once before you start, in one short message: what they are for, about 600 MB in all from Hugging Face, where they are stored. Only a clear yes counts; record it with `$W/models.py consent yes|no`. A script that stops with exit code 10 means the same question. If the user declines, you can still pack layers from masks you draw yourself (`measure.py bbox`, colour keys, polygons) and fill small holes with `inpaint.py --engine opencv`; say what that costs.

## 1. Find the input

- **A lemo-wake project** (`<slug>-alive/`, or its `src/`): the parts are usually already there. List them:
  ```bash
  $L/scripts/layers.py scan <project>
  ```
  It shows every image in `src/assets/` and what it looks like: `source`, `cut-out` (RGBA at the source's size), `mask`, `depth`, `plate?`, or `other size` (an already cropped part; `build` finds its place in the source by itself). For plates it also says how much of the picture each one changed (`differs_from_source`: the one with the most lifted out is usually the cleanest full background). Parts made for an animation may have been trimmed or repainted (a missing edge, a redrawn top); `build` checks the stacked layers against the source and marks the mismatch in red, so recut what does not match. Lift whatever is missing as in step 2.
- **An image**: make a folder `<slug>-layers/` in the current working directory and normalise the image there (HEIC, EXIF rotation):
  ```bash
  $L/scripts/layers.py prep <image> <slug>-layers/work
  ```
  It writes `<slug>-layers/work/assets/source.png`; below, `<a>` stands for that `work/assets` folder. Keep every mask and cut-out in `<a>` too. All coordinates are pixels of `<a>/source.png`.

If the user said what to separate ("just the two people", "the product and the logo"), that is the brief. Otherwise decide yourself and do not ask.

## 2. Take the picture apart

Look at the image first: what is in it, what covers what, what a designer would want to move. Usually that means:
- **each person whole, one layer per person**. A person includes what they wear and hold, and their own hands even where they rest on someone else. **Never cut off a head, an arm or a leg as its own layer**: the cut and the hole at the joint look like a broken doll, and nobody can use a loose arm.
  - One person: `--model portrait` (keeps hair) merged with `--model general` run inside a box around that person (keeps the body and what they hold). General and portrait both grab nearby things (a picnic blanket, a basket), so subtract the masks of objects that will be their own layers.
  - People who touch or overlap: one SAM box each often comes out with missing pieces. More reliable: make one mask of all the people together (portrait + general as above, objects subtracted), put a SAM point or box on each person as a seed, and give every pixel of the joint mask to the person whose seed mask it belongs to or lies nearest. Loose fragments go to the person they touch.
- **each object that stands on its own**: SAM, one box each (a box is steadier than a point; add `--neg` points to drop a neighbour; one click often gets only part of a thing, so add a point on the missing part). A container keeps its contents (the basket with its fruit, the vase with its flowers; `general` tends to drop thin stems, so add SAM points on them) unless the user wants the contents separately (food lifted off its plate).
- **many small things of one kind** (scattered berries, confetti, stars): one layer for the group, unless the user asked for each piece or each one clearly matters on its own.
- **openwork shapes** (a lattice tower, a fence, branches, lace): the mask also fills the gaps. Clear the gaps where the pixels match the background around them (compare with the filled background or key out the background colour inside the shape's box); where the gaps cannot be told apart, say so.
- **text blocks and logos** on posters and cards, as pixel layers (box select); they stay pixels, not editable text.
- **the background behind all of them**, filled in, so every element can be moved off it.
- **a depth map**, for the pack and for the user's own parallax work.

Do not split what belongs together (a cup and its saucer, a bouquet and the hands holding it), and do not cut tiny details nobody would move.

```bash
LEMO_WAKE_MODELS=... $W/depth.py   <a>/source.png --out <a>/depth.png
LEMO_WAKE_MODELS=... $W/segment.py <a>/source.png --out <a>/person1.png --model portrait
LEMO_WAKE_MODELS=... $W/segment.py <a>/source.png --out <a>/person1_g.png --model general --box x0,y0,x1,y1
LEMO_WAKE_MODELS=... $W/segment.py <a>/source.png --out <a>/cup.png --box x0,y0,x1,y1          # sam
LEMO_WAKE_MODELS=... $W/inpaint.py <a>/source.png <a>/all.png --out <a>/plate.png --dilate 6    # all = union of every element mask
$W/measure.py grid <a>/source.png <a>/grid.png                                                  # coordinates, if you need them
$W/sheet.py <a>/../parts.png --parts <a>/..                                                     # every mask over the image, cut-outs on a checkerboard
```
Masks are 8-bit grey at the source's size (white = the element); `build` takes masks or RGBA cut-outs directly. Combine and clean masks with NumPy / OpenCV through `uv` (maximum of two masks, remove one from another, feather or shrink 1-2 px where a halo of the old background shows); do not fetch other models. Look at the parts sheet before packing.

The background: inpaint the union of all element masks.
- `inpaint.py` grows the mask by about 1% of the diagonal by default. For clean edges (posters, illustrations, cut-outs that already include their soft edge) pass a small `--dilate` (4-8); keep the default for photos with hair and motion blur.
- `--split` fills separate regions one by one at near-native resolution. When the elements join into one big region it cannot split them, and the fill is downscaled (stderr says "downscale"); a soft result is acceptable. Large calm areas (sky, a wall, paper, a flat colour) can be filled in code with their own colour or gradient instead.
- **Never fill part of a hole while the rest of the object is still in the picture**: LaMa copies what it sees and paints the object back. Every pass masks the whole object (all of it, also the parts you fill later); to work at higher resolution, crop around a region so the whole hole inside the crop is masked.
- Even when the elements cover most of the frame, still make the background, but tell the user plainly that it is soft there because those pixels never existed. That is the honest limit without image generation.

Where one element covers another (a cat in front of a sofa), the lower layer has a gap where the upper one was. Leave it, or fill small gaps with `inpaint.py` on that layer's own cut-out. A **simple flat shape** may be completed in code from what is visible (a sun disc, a colour band, a circle badge: fit the shape, fill it with its own colour or texture). Never invent complex hidden content (a face, a hand, a building's hidden side).

## 3. Pack the layers

```bash
$L/scripts/layers.py build <slug>-layers --source <a>/source.png --plate <a>/plate.png --depth <a>/depth.png \
    --names "背景,原图,景深" --layer "背景人物=<a>/crowd.png" --layer "女孩=<a>/girl.png" --layer "帽子=<project>/src/assets/cap.png"
```
- Name each layer in the user's language, plainly ("女孩", "左边的杯子", "标题"), and pass `--names` for the background, source and depth layers in that language too.
- Order: **list the layers from the bottom up** (first = lowest). Decide it by what covers what in the picture. `--order depth` sorts by mean depth instead, a quick guess for separate objects spread through a scene, wrong for things that sit on each other.
- A cropped part from a project is found in the source automatically; if it was repainted or scaled, the script says so, then give its place as `name=file@x,y`.

It writes `layers.psd` (background, then one layer per element, the source and the depth map as hidden layers on top), `png/` (the background at full size, each element cropped to its own box, `source.png`, `depth.png`), `layers.json` (canvas size; per layer: file, x, y, width, height, z with 0 = bottom, mean depth) and `preview.png`.

**Look at `preview.png`** before you hand it over. A red "≠ source" card (and a `check:` warning) means the stacked layers do not reproduce the source there: a part is incomplete, misplaced or was repainted. Also look for ragged edges, missing hair, a halo, a part that grabbed its neighbour, a layer that should be two or two that should be one, the stacking order. Fix and build again. Then delete `<slug>-layers/work/` unless the user wants the masks.

## 4. Hand it over

Tell the user briefly, in their language: where the folder is, which layers it has (names, in order), and how to use it:
- `layers.psd` opens in Photoshop, Affinity Photo, Procreate, GIMP, or free in the browser at Photopea. The source and depth layers are hidden; switch them on to compare.
- `png/` with `layers.json` for After Effects, Figma, Keynote or a game engine: place each PNG at its `x, y`, stack by `z`.
- What the limits were: soft fill where a big element left the background, gaps where layers covered each other, text kept as pixels.
- They can turn the same picture into a film with `/lemo-wake:wake`.
