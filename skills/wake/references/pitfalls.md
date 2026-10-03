# Technical pitfalls

Each of these has broken a real film. Skim before building; check against them during QA.

## Rendering and determinism
- **`render(t)` must be a pure function of t.** `render.mjs` renders with several headless browsers in parallel, each taking a slice of frames. Any `x += v*dt` or "state from the previous frame" makes slices jump at their seams. Use analytic physics (`L.spring`, `L.particles`) or recompute from 0 every frame.
- Use `L.rng(seed)` / `L.hash` for randomness, never `Math.random()`.
- Wait for fonts and images before the first frame: await every `L.loadFonts` and `L.loadImg`, then set `window.READY = true`. Otherwise the first frames show fallback fonts or blanks.
- Page errors (exceptions, images that failed to load, font load failures) are written to `src/render.log`; `render.mjs` exits with code 2 and `qa.py` flags it. Do not ignore it: font fallback is easy to miss in stills.
- Rendering is fast (150 frames in seconds), so extra iterations are cheap. Re-render freely.

## Picture
- **Dark text on a dark element disappears.** After re-setting big type and colour blocks, check every small line for landing on a same-coloured area (for example small caps sitting on the stem of a big letter). Measure source coordinates, do not eyeball them.
- **Measure, don't guess.** `measure.py runs / vruns / bbox` gives the true bounds of letters and colour blocks; `measure.py grid` gives coordinates. Eyeballed positions are typically 10-30 px off, which shows the moment the last frame is compared with the source.
- **Curved ribbon textures.** Parallelogram slices misalign on curves into comb-like stripes. Map each segment with two exact triangles (`L.drawTri`; `L.strip` does this already).
- **Don't overdo ink texture.** Too many specks look like a starfield; `inkify` amount 0.5-1 is enough.
- **SVG filters inside a scaled container get blurry and slow.** Pre-render textures to a 3x canvas (`L.glyph`, `L.canvas(w, h, 3)`) and transform that.
- Canvas resolution must cover the camera's deepest push: pixels per design unit >= output scale x maximum z.
- **Camera splines undershoot.** Between a z = 1 plateau and neighbouring keys above 1, the Catmull-Rom spline dips below 1 and a dark band of ~10 px shows at the frame edge. `L.Camera` now floors z at 1 by default when `clampEdges` is on (`minZ` < 1 only if you pass it). A camera of your own, or zoom pulses added on top of it, need the same floor: clamp after every effect.
- **`L.Camera` keeps the view inside the source.** To let the camera look past the edge (tilt up into sky above the picture), paint that area yourself and pass `extend`; see `recipes.md`, "Extending the canvas beyond the source".
- **Dark images and the template base.** The template sets the page background (`--bg`) from the source's border colour and leaves the paper grain off (`GRAIN = null`): a multiply grain darkens a night or space picture all over. Turn grain on only for paper, print and light flat images.
- Vertical CJK text: `writing-mode: vertical-rl`, and make sure the element is still `position: absolute` (losing it when swapping classes sends the column to the left edge).
- CSS 3D (books, page turns): children need `transform-style: preserve-3d`, back faces `backface-visibility: hidden`.
- Canvas layers composited onto others need premultiplied alpha; straight alpha turns soft glows into solid coloured blocks.
- **GIF size.** A moving camera changes every pixel every frame, and GIFs stop compressing. `encode.py` steps the chat GIF down as needed; for a smaller GIF, keep the camera truly still in holds and grain static.
- **The film loops forever.** If the first and last frames differ a lot, every loop hard-cuts. `qa.py` checks this; fix it with a structure that closes on itself, an in-picture transition (`backplay` / `passby` / `pushcut` / `lightcut` in `fx.js`), or a frame-level reset from `reset.py`.

## Output size and encoding
- `new_project.py` makes the canvas the source image's own pixel size and aspect ratio. After HEIC conversion and EXIF rotation it shrinks only when the long side exceeds 2560 px (a performance guard for 12-48 MP phone photos; `--max-long 0` disables it). `CFG.orig` records the original size. From then on all coordinates refer to `src/assets/source.*`; do not measure the user's original file.
- `encode.py` always writes four files plus `<prefix>.encode.json`:
  - `<prefix>.mp4`: H.264 at the original size, for social posts (H.264 needs even dimensions: an odd width or height loses 1 px).
  - `<prefix>.gif`: chat GIF, scaled down only as far as needed to fit 5 MB with width under 1080.
  - `<prefix>.webp`: original size; about 8 MB is a target, and quality and frame rate drop before pixels do.
  - `<prefix>-sticker.gif`: longest side 240 (200 when needed to stay at most 500 KB), for chat stickers.
- Skip outputs with `--no-mp4 / --no-gif / --no-webp / --no-sticker`; a rerun merges into the existing `<prefix>.encode.json`, so skipped formats keep their entries for `qa.py`. Override platform limits with `--gif-max`, `--gif-width`, `--webp-max`, `--sticker-max`, `--sticker-side`. `--gif-width` is a cap, not a target: busy full-frame motion (night scenes, star fields, a moving camera) is squeezed to ~300-450 px by the 5 MB limit, and only a larger `--gif-max` buys width. Exit code 3 means the chat GIF or sticker could not reach its limit even at the lowest tier.

## Environment
- First run: `node $S/scripts/doctor.mjs` (`--fix` installs the npm dependencies and the headless browser).
- Output goes into a project folder under the current working directory. If the user's image is in a protected folder (on macOS, `~/Downloads` or `~/Desktop` may not be writable from some terminals), only read from there.
- `getImageData` on local images needs file access; `render.mjs` already launches the browser with `--allow-file-access-from-files`. Previewing the page by hand needs the same.
- zsh: in `"$3:stats"` the `:s` is parsed as a modifier; write `${3}` when a colon follows a variable. `set -- $var` does not split on spaces in zsh.
- macOS has no `timeout` command.
- Python scripts run with `uv run --script` (dependencies declared in the script header); no venv needed. The system `python3` may have no numpy / OpenCV / Pillow: run your own helper scripts with `uv run --with numpy --with opencv-python-headless --with pillow python helper.py`, or give them the same `# /// script` header as the bundled scripts.

## Assets without image generation
- **This skill does not generate images, call services that need API keys, or depend on other skills.** Assets have three sources: the source image itself, code drawing, and local model processing (`depth.py`, `segment.py`, `inpaint.py`).
- **Holes left by lifted subjects.** Small areas: `inpaint.py --engine lama` (or `--engine opencv`, which needs no download). Large inpainted plates are limited in quality; prefer structures that need no big fill, or let the plate show only briefly, behind motion, occlusion or fog.
- Check inpainting results. LaMa is good on repeating texture (sea, grass, sky) and blurry on structure (text, building edges, faces).
- **Do not force big holes.** Inpainting a whole image at once gets downscaled to about 512 px and smears large areas; tiling at full resolution can leave a checkerboard. Work around it instead:
  - Keep what you can: leave an occluded object (a pedestal, say) in the plate and choreograph it as present from the start instead of dropping it in.
  - Paintings and illustrations: leave a paper-coloured gap where a landmark goes, draw a pencil sketch layer computed from source edges, lay paint around it, then drop the landmark in as a sticker. An underdrawing is a good opening on its own.
  - Background bands (sea, sand, sky): draw them in code from small exposed patches of the source's colours; cleaner than inpainting.
  - If an inpainted area must show, cover it with cold fog, dust, paint or motion, or show it only briefly.
  - Inpainting each region as a crop at close to native resolution and pasting it back works better than one full-frame pass.
  - **A row of neighbouring objects** (planets in a line, products on a shelf, icons with labels): the default grown mask merges them into one blob, and LaMa fills it badly downscaled (stderr: `downscale 3.75x`). `inpaint.py --split` fills each object on its own crop, near native resolution, one after another. If two objects still merge, lower `--dilate`.
- Low-resolution sources (a poster of about 675 x 1199, say): photos cropped from them go soft when pushed in. Do not push the camera onto them, or give them a halftone or grain treatment.

## Local models
- `depth.py`, `segment.py` (`general` / `portrait` / `sam`) and `inpaint.py --engine lama` use local ONNX models. They are downloaded only after a one-time user consent, then work offline. Storage: the plugin data folder, or `LEMO_WAKE_MODELS`, or `<skill>/models`; `$S/scripts/models.py where` prints the actual folder.
- `$S/scripts/models.py` lists models and consent status, records the answer (`consent yes|no`) and pre-downloads (`fetch all|NAME`). Downloads honour `HF_ENDPOINT` for a mirror.
- Exit codes of the model scripts: **10** consent not asked yet (ask the user once, record it with `models.py consent`), **11** the user declined, **12** download failed (the message has mirror and manual-download hints).
- When a model is unavailable, find a compromise with your own methods and still finish the film: `inpaint.py --engine opencv`, colour keys and GrabCut or hand-drawn polygon masks instead of SAM, code-drawn layers and manual depth bands instead of a depth map, or a structure that needs no cut-outs.
- Depth maps may be 16-bit; normalise before converting to 8-bit or they clip to white and parallax and arrival timing silently stop working.

## Effect blocks (fx.js)
- **Areas and points are 0..1 fractions**, not pixels; measure with `measure.py grid` first. Block sizes scale with the short side, so parameters survive a resolution change.
- **Screen / lighter effects vanish on bright backgrounds** (white smoke, white bubble rims, dust on the brightest areas). Smoke switches to grey automatically; for the rest, move them to midtones, change colour, or lower the base brightness a little.
- **Periodic parameters must be integers** (`speed`, `cycles`, `turns`, `pulse`) or the loop will not close. `FX.pick` handles this; watch it when editing by hand.
- **Mesh warps** (`sway`, `wave`, `breathe`) fall to zero displacement at the area edge: make the area a ring larger than what should move, or its edge gets pinned. Do not use them on rigid subjects (tents, products, faces).
- **Pop-in and write-on blocks** cover the source with the box-edge colour first: clean on uniform backgrounds (chat screenshots, paper, flat colour); on photos, pass a `plate`.
- **Rotation** of a whole circle also turns its background: on uniform backgrounds use `mask: 'auto'` (rotates only what differs from the background and fills with the background colour); otherwise pass `mask` plus `plate` (`segment.py` + `inpaint.py`).
- **Depth parallax** shows slight ghosting at layer edges, especially on text: keep the amplitude modest; text can be cut out and kept out of the parallax.
- **Camera blocks** set the transform on `#cam`. Use either them or your own `L.Camera`, or combine via `extra`; do not apply both directly.
