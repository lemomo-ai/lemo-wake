# Techniques that worked

A cross-category toolbox: ways of reading an image and techniques that made earlier films land. Everything here is reference material. Read it to know how others thought and where they stumbled, then decide for your own image; better ideas are welcome.

- Quality standards (what good looks like, what was rejected): `taste.md`.
- Category guides with case cards of the sample films: `../types/<id>.md` (photo, portrait, multi, poster, illustration, clay, ui, chart, logo, sticker, xhs).
- Ready-made effect blocks and reset kinds, with suggestions by what the image contains: `effects.md`.
- Technical traps: `pitfalls.md`.

## 1. Judge an image on two axes

### Axis A: native medium, which sets the motion dialect

| Medium | Traits | Dialect that has worked |
|---|---|---|
| Photography (real light) | real light, depth of field, grain | cut-out objects that perform (jump, fall, fly, settle back); light that travels and makes things react; camera journeys that follow such an action (never the action themselves); depth layers; whole-frame weather or time change carried by objects; natural motion. Bending rigid things looks wrong. |
| Print / layout | type, colour fields, grids | typesetting actions (stamping, registration, typing, guide lines); take apart and reassemble |
| Painting (impasto, ink, watercolour) | strokes, pigment, paper | the act of painting (underdrawing, laying colour, bleeding, outlining); clean geometric slides tend to look like a slideshow |
| Clay / 3D render / stylised generated art | volume, squash | squash and stretch, physical drops, bounce |
| UI / infographics | components, data | components appear by interaction logic; number rolls; charts grow |
| Logo / icon / character | geometry, simplicity | geometric break-apart and assembly, stroke drawing, true loops |
| Abstract / pattern | nothing figurative | flow, breathing, endless pan |

### Axis B: can it be taken apart, and how to still go big

- **Without harm** (collage posters, clay sets, flat layout posters): a build is the most direct route. Elements fly in, drop, assemble.
- **Only with harm** (photographs, painted landscapes, where light and perspective are one piece): still go big.
  - Cut things out with SAM (`segment.py --model sam`), put an inpainted plate behind them, and let them perform: jump up, drop, roll in, fly away and come back.
  - Camera journeys; light, fire, fog or weather that travels (and carries objects with it, since colour alone does not count, see `taste.md`); depth layers that appear one by one.
  - Leave a gap and draw into it: a landmark's place starts as bare paper plus a pencil sketch computed from the source edges, paint is laid around it, and the landmark lands as a sticker.
- **Half** (a photograph with a text layer: postcards, movie posters): lift the text out (colour key plus inpainting) and perform it separately; treat the photo layer as above. Let both layers share one light grade so the text is shaded with the scene instead of looking pasted on.

Three questions worth asking while judging:
1. What should stay rigid? (people, products, letterforms)
2. Which causal line can run through the whole film? (wind, light, impact, scent, fire, water)
3. What state does the picture start in, and what has it become at the climax?

## 2. Technique catalogue

Each entry: the effect, how it was built, where it fits.

### 2.1 Whole-frame state change, done inside the photo

- **Cloud shadow sweep, overcast to sun.** Grade the whole frame cold, grey and desaturated; sweep a noisy soft edge across it, restoring the original colour behind the edge with a warm band along it. Sea glints flare only where lit and only just after the edge passes. In a shader: `mix(shade, lit, smoothstep(edge))`, with the edge function written once analytically and shared by JS and GLSL.
- **Light-source reveal.** Start from the picture's own lamp, window or sun; light spreads outward and everything it reaches warms and brightens. Drive it with an arrival-time map (distance from the source plus depth plus noise) and a wide feather, so the front follows real surfaces instead of a geometric ring. Pair it with things that physically react.
- **Computed "before" states.** Derive the unlit, colder or darker version from the photo's own pixels (desaturate, darken, darken more near the light it comes from, replace glowing pixels with an estimate of their unlit surroundings) rather than laying a coloured layer on top.
- **Depth parallax.** Estimate depth with `depth.py` (on the text-free plate if there is text), then solve parallax by fixed-point iteration on the depth map. Large offsets tear at depth discontinuities; check the edges of people and objects. Let it settle to zero on the full frame so the hold matches the source.
- **Colour or time transforms** (day to night, black-and-white to colour, line art to colour): open territory. Give the change a carrier that moves.

### 2.2 Impact and propagation

The common skeleton: **one event plus reactions queued by arrival time.** Define `tx(x)` = the moment the event reaches element `x` (for example distance from the impact point divided by a speed, or arc length along a path), and start every reaction from its own `tx`. This is what makes motion read as cause and effect instead of everyone doing their own thing.

- **Stamp impact.** Anticipation (lift, shadow shrinks), accelerating drop (`inQuad`), impact (scale overshoot, ink spatter, whole-frame shake), rebound (spring), settle.
- **Impact that travels down a structure.** Two halves of an arch meet and spark; the shock runs down the structure, hangers drop one by one from the middle, shell roofs stand up in a wave.
- **Relay ignition.** Beacons light one after another along a wall, far to near; the light runs along the path's arc length and bursts at the foreground tower.

### 2.3 Trigger and path

One action releases a path, and the path touches elements in turn, each reacting on contact. Example: a bottle cap lifts, a ribbon of scent winds past the title and the landscape to a figure's ear, and the earring glints while hair, sleeves and flowers stir. The path is the visible causal line; the arrival-time skeleton above schedules the reactions.

### 2.4 Registration snap

Colour separations hang in the air out of register, then slam together. Flash, shock ring, ink spatter, and the finished print is there. Build the plates from the original pixels (k-means into the print's few inks) so the reassembled stack is indistinguishable from the source; let misregistration spring back to zero with damping. Fits screen prints, risograph and vintage print design layers.

### 2.5 Freeze / crystal reveal

Elements freeze into existence from their root: a noise dissolve with an icy rim travels up from the base. Group by colour so same-coloured letters pop in on the same frame, and finish on a single heavy hit.

### 2.6 Text entrances matched to the medium

- **Brush writing with dry-brush edges.** Precompute a reveal-time map per character (progress along the stroke direction plus noise stretched along the stroke), then threshold it each frame to get alpha.
- **Stamped.** See stamp impact above.
- **Typewriter, decode, number roll.** Already in `lib.js` (`L.textAnim`, `L.rollPrep` / `L.rollAnim`).
- **Small Latin text "printed on".** Shrink from about 1.16x to 1 while fading in, staggered per letter.
- **Avoid:** ink droplets that fly apart and regather into the title. It reads as a digital glitch, not as ink.

### 2.7 Asset preparation (what makes big moves possible)

- **Colour-key text with per-glyph alpha.** Inpaint a text-free plate, then back-solve each glyph's alpha from plate `s`, original `p` and ink colour: `alpha = ((p - s) . (ink - s)) / |ink - s|^2`. Keeps the original letterforms and ink texture, and composites back pixel-exact. Works best where text sits on a smooth gradient (sky, wall, paper).
- **SAM sprites plus inpainted plates.** `segment.py --model sam` with points or (more reliably) boxes, then `inpaint.py` for the plate behind them. Suits clay sets, collages, food, balloons, anything liftable. With many pieces, keep a naming and layer-order table.
- **Plates.** `inpaint.py` (LaMa or OpenCV) is clean on small areas and repeating texture, soft on large ones. Choreograph so a large inpainted area is rarely seen, or cover it with fog, dust, paint or a gap. See `pitfalls.md` for working around big holes.
- **Code-rebuilt shapes.** Type, colour blocks, geometry, sky gradients, bands of sea and sand: draw them in code in the source's colours. Often cleaner than inpainting.

### 2.8 Extending the canvas beyond the source

The film keeps the source's size, and its rest frames should match the source, but a camera move may still reveal what lies just outside the picture: tilting up from a street into the night sky above it, panning past the edge of a table. One way that worked:
- **Paint the extra area in code** as a layer inside `#cam` at negative design coordinates (e.g. a 520 px band at `top: -520px`). Start from the colours along the source's border row and continue them: a gradient for sky or wall, plus texture of the same character (stars, haze, noise, grain) so it doesn't read as a flat fill. Lines that run into the edge should carry on.
- **Hide the seam.** Lay a soft band (fog, glow, gradient) across the source edge, and tie its opacity to how far the view has moved past the edge, so it is gone whenever the camera is back inside: the rest frames stay pixel-identical to the source.
- **Let the camera go there:** `new L.Camera(keys, {extend: {top: 520}})` (also `right`, `bottom`, `left`) widens the edge clamp by that much; z stays >= 1.
- **Give the new area something to do.** Empty painted sky looks fake under scrutiny; let something rise into it (sparks, a lantern, a star that flares), keep the excursion short, then come home.
- Check stills at the moment of maximum extension, and the rest frame against the source with `sheet.py --vs-source`.

### 2.9 Supporting effects

Seagull silhouettes, sea glints, flickering lamps, foam brightening with the swell, grass pressed flat at its arrival time: most of these now exist as blocks (`effects.md`). Supporting effects add detail to the main line; a small main line with many supporting effects turns back into "the source image with a bit of motion on top".
