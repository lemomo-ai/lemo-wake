# Motion grammar: growing a film out of one image

This is a toolbox and a body of experience, not a set of rules. The arcs, camera moves, effects and numbers below are starting points. Use better ideas when you have them, and invent structures, camera moves and effects that are not listed; a one-line reason in `DIRECTOR.md` is enough. The one direction worth keeping: every choice should answer "why this image?". Quality standards live in `taste.md`.

## Contents
1. Reading the image: six questions
2. Arc: decide this first
3. Signature move
4. Camera grammar
5. Motion principles
6. Effects toolbox (with implementation hints)
7. Rhythm and timing
8. By image type
9. Self-check questions
10. Avoiding repetition

---

## 1. Reading the image: six questions

Before building, write these six answers into `DIRECTOR.md`; later decisions follow from them.

1. **What is it about?** A one-line theme plus a mood (lively, solemn, playful, dangerous, tender, technical...). Mood sets the base speed: a solemn image should not bounce, a playful one should not crawl.
2. **Who is the visual lead?** Where the eye lands first. The climax usually belongs to it.
3. **What is each element's nature?** How it moves in the real world: paper floats, curls and gets pulled out; ink bleeds and splashes; a stamp comes down; water flows; smoke disperses; light sweeps; neon flickers; gears turn; people walk; flowers open; glass shatters; film advances; books turn pages; letters are printed, handwritten or lit like neon. **The best motion amplifies an element's nature** instead of applying a generic animation unrelated to it (everything fading up from below is the worst case).
4. **Where are the layers?** Foreground, midground, background; what can separate and what overlaps. Occlusion is where 2.5D depth comes from.
5. **What is the visual path?** Where the composition leads the eye (diagonal, S-curve, radial, Z). Camera and entrance order that follow it make the film feel smooth.
6. **What style or era is it?** Print, film, ink, cyber, flat, hand-drawn, 3D render, pixel art... Style sets the effect dialect: print uses misregistration, halftone and ink; cyber uses RGB split, scanlines and glitches; ink painting uses bleeding and dry brush; film uses light leaks, scratches and gate weave. The wrong dialect looks cheap.

## 2. Arc: decide this first

Not every film has to go from nothing to something. Choose for the image:

| Arc | Description | Suits | Timing reference (5 s) |
|---|---|---|---|
| **Build** | Starts empty; elements assemble by some logic and settle into the complete picture | Layout-heavy posters with many elements; "making of" themes | 0-3.6 build, 3.6-5 hold with subtle motion |
| **Dissolve** | Starts complete; gets taken apart, blown away, dissolved, burned or paged away, leaving one element or a blank | Themes of time, memory, loss; endings that leave a question | 0-1 complete (let viewers see it), 1-4.4 dissolve, then blank or one lingering element |
| **Living still** | The frame stays complete and only inner elements come alive, cinemagraph-style: water flows, smoke drifts, light sweeps | On its own the motion is usually too small (see `taste.md`); more often combined with build, tour or transform | whole duration |
| **Loop** | First and last frames identical; seamless forever | Icons, characters, products, ambience; GIFs used as stickers, avatars or banners | close it with `L.cyc` / `L.loopNoise`; usually no hold |
| **Bookend** | Build, hold, then exit a different way (or the reverse) | A fuller story; more comfortable at 6 s or more | build 40% / hold 30% / exit 30% |
| **Reveal tour** | The camera travels between details, each stop revealing one, then pulls out to the whole | Dense, detailed illustrations, infographics, big scenes | 0.6-1 s per detail, full view at least 1 s |
| **Transform** | The picture changes from one state to another (day to night, line art to colour, black-and-white to colour, flat to 3D, photo to poster) | Images with a natural "two states" | change in the middle, steady states either side |

The table is not complete; combine arcs or invent new ones. Films that landed were mostly builds, tours or a mix: the picture starts incomplete, one action chains through it, and the complete picture arrives at the climax. Photos can do this too, for example opening on a single lamp and pulling out while its light spreads across the whole scene and things react.

## 3. Signature move

A film needs one move that **belongs only to this image**: the moment viewers remember. It grows out of question 3 (the elements' nature).

Derivation: lead element x its nature x one notch of exaggeration.

- A poster with a paper ribbon: the ribbon is pulled out of a book and twists away off frame.
- A stamped character: it drops from above and lands with an impact, ink spatter and a jolt.
- A coffee product shot: the steam rises and writes the brand name in the air, then disperses.
- A neon street at night: the sign flickers twice on a bad contact, then snaps fully on, and the whole street's reflections light up after it.
- An ink landscape: a drop of ink falls and spreads; the edge of the bloom becomes the mountain's outline, and the painting grows out of the ink.
- A portrait: the photo is a print lying on a table; a gust lifts it, the person steps out of it as a cut-out, catches the flying hat and lands back in place as the print settles.
- An aerial city view: streets light up in sequence like a circuit carrying current.
- A sneaker: it reassembles from exploding fragments, and the last piece in is the logo.
- An infographic: numbers roll, lines draw themselves as if by hand, and the key figure rushes toward the camera.

These are examples, not options. Derive a new one for each image.

## 4. Camera grammar

The camera is `L.Camera` keyframes (z zoom, cx/cy target, rot) plus layer parallax plus shake. Available moves:

- **Push / pull.** Pushing in builds focus and tension; pulling out reveals and releases. Ending on a pull to full frame is common, not mandatory.
- **Pan / track / follow.** Follow a moving element (the tip of a ribbon, a passing bird, travelling light) so the viewer's eye is led.
- **Whip pan.** A very fast lateral move with motion blur (`filter: blur` only on the 3-5 whip frames), to cut between two details.
- **Roll.** A slight rotation (2-6 degrees) adds energy, more so with shake at an impact. Large rotations only when the style supports them.
- **Snap zoom.** z jumps 10-20% within 2-4 frames and springs back, on an impact.
- **Rack focus.** Alternate `blur()` between foreground and background layers to fake a shallow-focus pull.
- **2.5D parallax / orbit.** Layers move at speeds set by depth (`L.parallax`), or give the layer container `perspective` plus small `rotateY` / `rotateX` for a slight walk-around.
- **Wipe by occlusion / match cut.** Swap content while a foreground element crosses the lens, or bridge two similarly shaped elements.
- **Still.** A locked camera is a choice too: in a living-still arc it makes the inner motion stand out.

Keyframes are joined by smooth splines, so the camera does not stop at each one. For a pause, give two neighbouring keyframes the same values.

**Speed contrast** is where camera polish comes from: slow, slow, suddenly fast, stop. A constant-speed push throughout is mediocre.

## 5. Motion principles

- **Anticipation, action, impact, rebound, settle.** Important entrances go through all five. A stamp: lift first (anticipation, shadow shrinks), accelerate down (`inQuad`), impact (scale overshoot, shake, ink spatter), rebound (spring), settle.
- **Stagger.** Elements in a group enter one after another, 30-120 ms apart; perfectly simultaneous entrances look dead.
- **Overlapping action.** The next action starts before the last one ends (one element is still rebounding while the next is in flight). This is where flow comes from.
- **Easing** (rules of thumb). Entrances: `outExpo` / `outQuart` (fast in, slow stop). Falls: `inQuad` / `inCubic`. Looping sway: `sin`. Springy: `outBack` / spring. `linear` almost only for things scrolling at constant speed.
- **Smear and stretch.** Fast-moving things get motion blur or a slight stretch along the direction of travel (`scaleX` 1.05-1.15), released when they stop.
- **Secondary motion.** The main action moves its surroundings: small text trembles when the stamp lands, nearby elements stir in the wind of a passing ribbon, the shadow arrives before the falling object.
- **Breathing.** A hold should not go completely dead: a ribbon drifting, grain, a very slow push (3% or less), one light sweep.

## 6. Effects toolbox (with implementation hints)

> **Ready-made blocks:** many common effects already exist as `fx.js` blocks (rain, snow, dust motes, bokeh, steam, smoke, fog, water, caustics, god rays, sheen, foliage shadows, sway, wave, blink, spin, depth parallax, line drawing, film grain, chromatic aberration...). Parameters and usage: `effects.md`. Use them or not; the signature move is usually written for the image.

Everything is built in one HTML page with Canvas2D, CSS or SVG; for real 3D, download three.js into `src/` and reference it locally.

| Effect | Implementation hint | Dialect |
|---|---|---|
| Motion blur | `filter: blur(Npx)` on fast frames with N following speed, or 3-5 ghost copies at decreasing opacity | general |
| RGB split / chromatic aberration | Draw the layer three times, one per channel via multiply/screen, offset 2-6 px; only on impact frames | cyber, glitch, streetwear |
| Light sweep | A diagonal gradient band in `#post` with `mix-blend-mode: soft-light` or `screen`, crossing in 0.6-0.9 s | print, product, metal |
| Flash white / black | A full-frame block in `#post`, opacity 0.6 to 0 over 1-2 frames | impacts, cuts |
| Particles | `L.particles` (analytic): ink drops, paper bits, dust, sparks, rain, snow, fireflies, bubbles | per style |
| Bloom | Duplicate the bright layer, `blur(20px)`, add with `screen` | neon, night, lamps |
| Depth of field | `blur()` on far and near layers, the focus layer sharp; interpolate for a focus pull | photography |
| Halftone | Canvas dot grid sized by brightness; can drive a "develop from halftone" entrance | print, pop art |
| Misregistration | Two colour plates of the same element offset a few px, then aligned | print, riso |
| Ink bloom / dissolve | Noise threshold mask: `L.fbm` noise field, threshold over t, `destination-in` | ink, fading away |
| Image to particles | `L.pixelate` samples the image into coloured particles that remember their home; compute positions per frame: scatter, gather, blow away | dissolve, assembly, digital |
| Noise dissolve | `L.dissolve` eats or grows the image by a noise threshold, optionally with a bright rim (burning, ink bloom, developing) | fading, growing, ink |
| Shards / assembly | `L.tiles` cuts a grid, each tile with its own path and rotation; or Voronoi shards | explosions, assembly |
| Ribbons | `L.strip` (exact triangle mapping, twist, pull-out) | paper strips, film, ribbons, banners |
| Displacement / liquify | Cut the image into a mesh with `drawTri` and perturb vertices with noise | water, heat, wind |
| Scanlines / CRT | Repeating linear gradient in `#post` plus slight flicker | retro electronics |
| Light leaks / scratches | Orange-red radial gradient on `screen`, drifting slowly; thin vertical lines flashing at random | film |
| 3D flip | CSS `perspective` + `preserve-3d` + `backface-visibility` for page turns, card flips, opening books | paper, books, cards |
| Text animation | `L.textAnim`: type, rise, drop, blur, scramble; `L.rollPrep` / `L.rollAnim` for number rolls | per style |
| Mask wipe | Animate `clip-path: inset() / circle() / polygon()` | reveals, transitions |
| Stroke drawing | Animate SVG path `stroke-dasharray` / `stroke-dashoffset` | line art, maps, signatures |

**Restraint is a reference too.** Effects are usually seasoning, and too many fight each other; but if the image wants everything turned up (cyber, glitch, party), turn it up. What matters is that each effect has a reason to be there (impact, transition, atmosphere). Implement anything that is not in the table if it fits.

## 7. Rhythm and timing

Rules of thumb, not hard rules. Break them knowingly.

- **Hook early.** There is usually motion within the first 0.3 s, so the film does not open on dead air. (A deliberately still opening works if it builds suspense.)
- **Climax position.** The strongest beat often sits early-middle (about 40-65%), but an explosive ending or an opening blast can work too.
- **Varied speed curve.** Fast-slow-fast, or slow-burst-release. Mark each section's energy (1-5) in the beat sheet and check that the curve is not flat.
- **Ending.** Build, tour and transform arcs usually hold the complete picture for about 0.8-1.2 s so it can be read; loops have no ending and close on themselves; a dissolve ends on a blank or a meaningful leftover.
- **Changing the duration.** When the user changes the length, scale the beat sheet proportionally, but keep physical times (impacts, rebounds) roughly as they are (a stamp needs about 0.3 s of fall to have weight); give the extra time to reveals and holds.

## 8. By image type

Per-category guidance (what such images contain, what tends to work, pitfalls, case cards) is in `../types/<id>.md`: photo, portrait, multi, poster, illustration, clay, ui, chart, logo, sticker, xhs. Asset techniques that apply across categories are in `recipes.md`.

## 9. Self-check questions

Use these to look at the first rendered version. They are questions, not a scorecard: when one answers "no", decide whether it is a real problem; if it is deliberate, keep it. The standards behind them are in `taste.md`.

- Is the action big enough? Does the picture go through a complete change, or is it the source with a little motion on top?
- Do things in the picture really move, or is only light and colour changing?
- Does the first second grab attention (not a slow fade-in)?
- Is there a signature move that belongs only to this image, and can you say it in one sentence?
- Is there depth (several layers moving at different speeds, or real occlusion and shadow; a deliberately flat style excepted)?
- Is there speed contrast (the motion report's bar chart is not a flat line)?
- Is it more than collage (at least one key asset usually changes while it moves: particles, shatter and reassembly, dissolve, develop, displacement)?
- Is there detail (shadows, grain, light, secondary motion, impact feedback)?
- Would any paused frame look good, including mid-transition?
- Is the last frame a beautiful complete picture (or a seamless loop, or a meaningful blank)?
- Is the jump from last frame to first smooth? The content need not return to its start; the ending transition just has to suit the image.
- Is the first frame attractive? Many places use it as the still preview, and it need not be the source.
- Are there visible flaws (text on a same-coloured block, elements jumping, texture seams, font fallback, grey blocks from images that failed to load)?
- Is it clearly different from the last film in `history.jsonl`?

## 10. Avoiding repetition

- Before starting, glance at the last few entries in `history.jsonl`. If this film's **arc, signature move and main camera move** closely match recent ones, stop and ask whether the image really needs that or whether it is habit.
- Watch out for "open on a close-up, end on a pull to full frame". It works well, which is why it becomes a habit.
- Watch out for "every text types in letter by letter". Match text entrances to style: a newspaper can roll off a press, neon can light tube by tube, handwriting can be stroked in, tech can decode from noise.
- Change `seed` on blocks and resets for every film; `FX.pick(name, seed)` draws numeric parameters from the recommended ranges. If the main action and the ending match the last few films, ask whether that is habit.
- Swap test: replace the image with another of the same kind. If the film still works unchanged, it is too generic; let at least one action grow from something only this image has.
- When finished, append a line to `history.jsonl` (fields in `SKILL.md`, including `main` / `fx` / `reset`).
