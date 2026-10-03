# Illustration and Painting

Painted or drawn images: oil and palette-knife paintings, Chinese ink and blue-green landscape painting, watercolour picture-book pages, children's crayon drawings, digital fantasy paintings, often with a title painted or lettered in.

## What these images usually contain
- A medium you can see: brush and knife marks, ink on paper, watercolour washes, crayon on paper texture, gold-leaf linework, sticker-like cut edges.
- A scene whose light and perspective were painted as one piece. Pulling it apart damages it, but a few things usually sit *on top* of smooth areas and lift out cleanly: a title, a path or bridge, a moon, characters, small props.
- Paper media (ink, crayon, watercolour) are multiplicative: image = paper × ink. Take the ink away and plain paper is underneath, so nothing needs inpainting.
- Visual rhymes and named motifs: a crescent on a book cover echoing the moon in the sky, a title that describes an action ("a line becomes a landscape"), beacon towers along a wall, a path leading to the sun.
- Rigid parts: faces and characters (move them whole, and keep faces undeformed), buildings, lettering.

## What tends to work
- **Repaint it in its own process.** Pencil underdrawing, then knife strokes laying in colour, then stickers slapping down. Or one ink stroke dragged across blank paper that heaves up into the mountain. Or crayon elements drawn in one scribble. The `draw`, `paint` and `inkbloom` blocks give quick versions; a signature move usually deserves custom code.
- **Find the rhyme or the title's verb and build the signature from it.** The book's moon flies off the cover and becomes the sky's moon. The line becomes the landscape. The stone path paves itself to the far cliff and the sun ignites. The arch's two halves close at the top.
- **Characters really move.** Children's drawings especially: the sun spins in, clouds slide in from the paper edge, the family and the cat jump out of the grass, the house hops and the chimney puffs. Light alone doesn't count; let the light hit things that react.
- **Relay and impact propagation.** Fire runs along a wall tower by tower. An impact whips along a stroke and the far mountains spring up in sequence. A closing arch sends cables dropping from the middle outward and sails rising like a wave. Give each element an arrival time and start its reaction from there.
- **Night-to-day or unlit-to-lit, carrying objects with it.** Make an unlit or night grade of the plate in the shader, then return to the original colours by per-pixel arrival time, triggered by a physical event (the last stone lands, the moon locks into place). Point lights (stars, windows, reflections) can ping on one by one.
- **Paper × ink decomposition.** Estimate the paper with a large-scale normalized blur, take ink = image / paper, split the ink into soft regions that sum to one, and move, stretch or reveal each region independently. At rest the product gives back the original exactly. For crayon, a blank-paper plate plus per-element ink layers multiplied back keeps every moved element "on the paper".
- **When a big background can't be inpainted:** leave the landmark spots as paper-coloured slots with a pencil sketch computed from the original, lay paint around them, and let the stickers land on top. Or cover gaps with the painting's own cloud or mist motifs.
- **Depth layers.** Split along least-visible seams (through mist and clouds) so mountains can rise from a cloud sea in order, far to near.
- **Labelled educational diagrams** (a row of planets with their names, the parts of a flower, a labelled map or cutaway, "the water cycle"). Mixed with `chart.md`: the labels are content, and the drawing has its own logic (order, size, orbit, sequence, flow). Let the elements perform that logic: enter in their real order, fall into line, the one being "called" answers with a hop or a flare, the cycle actually turns. Treat each element and its label as a pair: cut both, let the label arrive with its element (stamped as it lands, swinging on, trailing behind) and never cross another label in flight. At rest every label is exactly where the source has it, readable and held long enough to read. A label painted over a busy area (lettering across a flame) can simply stay in the plate. Neighbouring elements make one big merged hole: `inpaint.py --split` fills them one by one; on a dark painted background, a few code-drawn stars or specks over the filled areas hide the smudge (keep them out of other objects' glow). Motion that contradicts the subject (wrong order, wrong direction of orbit) reads as a mistake.
- **Loop options:** `mist` for landscapes, `ink` for ink painting, `brush` for knife or impasto painting, `erase` for pencil and crayon, `watercolor` when the framing at both ends matches. Often best: an in-picture reset that reverses the story (the moon flies back into the book while the night spreads like an indigo wash; the stones sink back into the clouds; the family ducks back into the grass; mist rolls in and the mountains sink into blank space).

## Pitfalls
- A page-curl reset was disliked even on a picture book: it's a generic overlay, and its mirrored back side looked cheap. Iris and ripple were disliked too.
- Frame-level resets (`crayon`, `watercolor`) over an ending at full frame and an opening close-up show two compositions at once. Either match the framing or reset inside the picture.
- Flat colour tints on lit objects look like yellow plastic. Multiply the object's own texture by a warm colour. Thin straight sun rays look like a cheap lens flare; use fewer, wider, softer wedges. Round radial glows look like glowing balls; flatten them and lower the opacity.
- A night front driven by a 1-D sweep looked like a hard eraser edge. Warp the arrival field with large-scale noise so the front spreads in irregular washes.
- An inpainted plate and the original differ slightly in base colour, and a mask that hugs the letters shows a glyph-shaped ghost. Use a broad, soft exclusion zone behind lifted layers.
- Paper estimated at small scale inside big ink areas comes out dirty and feeds back into the ink mask. Estimate at a large scale first. Guard `pow(0, 0)` in shaders; the NaNs look like stray ink dots.
- Multiplied ink can't occlude: dark on dark only gets darker. An element that must pass in front of foliage needs an opaque sprite.
- Anisotropic stroke noise on a round blob of wet ink gives comb-like streaks. Use isotropic noise there.
- Camera-zoom impact pulses can dip below z = 1 and show the image edge. `L.Camera` floors its own spline at 1; clamp again after every effect you add on top.
- Clean geometric displacement of painted parts reads like slideware. Prefer reveals and motion that match how the medium is made.

## Case cards

### Set Out for the Unknown: Paving the Way to Sunrise
- **Signature:** in blue pre-dawn, the traveller has no path. Nineteen stone slabs rise one by one from the cloud sea and lock into place, each catching warm light. The last one slams onto the far cliff, the sun ignites, morning floods the painting, gold runs back along the steps to the traveller's feet, and the title writes itself along an arc.
- **Structure:** night with flowing waterfalls, the paving (camera follows the path head), the slam, a held breath, the sun ignites, light spreads as the camera pulls to full frame, the title, a hold.
- **Technique:** SAM box-select on the floating steps, cut into slabs at the dark risers, and plates inpainted in two passes. A shader night grade returns to the original by arrival time from the sun. A "cloud surface" mask softly cuts each slab below its resting line so it surfaces top first.
- **Loop:** in-picture. The light retreats into the sun, the title fades, slabs sink back into the clouds far to near, and the camera returns to the opening.
- **Hard part:** the first lighting tinted the slabs like plastic, the rays looked like a lens flare, and the slam and the ignition blurred into one beat. Textured warm light, wider soft rays and a short pause before ignition fixed them.

### The Moon Doesn't Sleep: The Moon That Flew Out of the Book
- **Signature:** the gold crescent on the owl's book lifts off the cover, flips over, flies along the title line lighting each character, and grows until it crashes into the moon's place in the sky. A flash and a jolt, then moonlight spreads, and stars, village windows and reflections ping on until it reaches the small animals looking up.
- **Structure:** a moonless night lit only by the lantern, the crescent's flight, the merge (climax, pull to full frame), moonlight spreading, a hold, the moon returning to the book.
- **Technique:** one shader with a text-free plate, an unlit plate (stars filled, windows darkened rather than erased), title alpha from original minus plate, and an analytic moonlight arrival time shared by JS and GLSL so star glints sync.
- **Loop:** in-picture. The moon shrinks back to a crescent and arcs down onto the book cover while the night spreads from the moon like a noise-warped indigo wash, and the camera pushes back in.
- **Hard part:** the first ending was a page curl and was rejected; the in-picture return replaced it. Also: glyph ghosts from plate colour mismatch, and a camera bug that made the frame jump periodically.

### A Line Becomes a Landscape: One Stroke Raises a Mountain
- **Signature:** a heavy ink stroke is dragged right to left across white paper, pools at the left end, then the whole line heaves up like a wave into the main mountain, overshoots and slams back (ink bursts from the peak, the frame jolts). The shock whips back along the line, the far mountains spring up out of the clouds, the red sun rises, and the calligraphy title writes itself.
- **Structure:** blank paper, the stroke, the mountain surges (climax), the shock spreads, the title, a hold, mist rolls back in.
- **Technique:** a paper × ink decomposition, so no inpainting at all. Each region is `pow(M, weight)` with weights summing to one, so the rest state equals the original. The dry and wet ink of the stroke are separate factors, and flying ink drops land exactly on the painting's own ink dots.
- **Loop:** in-picture. Mist rolls from lower left to upper right, and the mountains and line sink into it as blank space. Output starts on the held painting.
- **Hard part:** a dirty paper estimate, NaN dots from `pow(0,0)`, a too-fast surge (lengthened so the climax can be read), a straight seam where the mountain met the far hills (split by ink density instead), and comb streaks in the wet blob.

### Child's Crayon Drawing: The Rainbow Lands
- **Signature:** one rainbow stroke sweeps from its left foot across the sky and smashes into the apple tree. The tree squashes and wobbles, apples pop onto the branches, the cat and the hand-holding family leap out of the grass, and the shock reaches the house, which hops while the chimney puffs smoke rings.
- **Structure:** empty sky, the sun spins in, clouds slide in, the rainbow, the impact, the chain reaction, a hold with happy hops. The camera starts close on the house, follows the rainbow and pulls to full frame.
- **Technique:** a blank-paper plate (mask-normalized convolution) with per-element ink = image / paper multiplied back. The rainbow reveals by arc angle plus band. Figures pop out through a jagged grass-tip clip line. Elements animate on twos with boil.
- **Loop:** in-picture. Apples drop into the grass, the family and cat crouch and duck back in, the rainbow retracts, the clouds slide out, the sun shrinks away, and the camera pushes back to the house.
- **Hard part:** the `crayon` reset doubled the house (close and full framings overlapping), so the reset moved inside the picture. Falling apples turned dark where they crossed the foliage, which needed an opaque crayon sprite.

### Sydney Harbour: Closing the Steel Arch
- **Signature:** two half-arches reach out tilted up from the pylons, rivet sparks flying, then lower and close at the crown. Flash, paint chips, a shock ring, a hard push-in. The shock travels down: hangers drop from the middle outward, and the Opera House sails rise right to left like a wave.
- **Structure:** pencil underdrawing, knife strokes lay in sky and water, the stickers (pylons, deck, arches) slap down with lifting shadows, the closure, the propagation, a sheen across the sails, a hold.
- **Technique:** landmarks cut from the original as polygon stickers. The arches rotate about the pylons. Sails scale column by column from their base line to stand up. The camera rolls slightly and follows the action.
- **Loop:** `brush`. Diagonal paper-coloured strokes scrape it back to blank paper, echoing the opening knife strokes.
- **Hard part:** local inpainting couldn't produce an empty harbour. The landmark areas instead start as paper-white slots holding a pencil sketch computed from the original; paint goes around them and the stickers land on top. The sail sketch fades just before the coloured sails rise so the rise stays readable.

### The Great Wall: Beacon Relay
- **Signature:** beacons light tower by tower along the Great Wall from far to near. Gold light runs along the wall and smoke curls in the painting's own cloud motif. At the foreground gatehouse a gold ring bursts, the gold-leaf lines flash in turn, and the gold sun answers.
- **Structure:** the mountains rise from a sea of clouds in three depth layers, the fire relays along the wall, the climax at the gatehouse, the pull back to full frame, then the crossfade to the exact original.
- **Technique:** depth layers split along least-cost seams through the mist, mist on the layer edges, a wall mask lit by arc length along the wall's path, and cloud sprites lifted from the painting to cover gaps.
- **Loop:** `mist`. Clouds roll in over the frame and part on the opening.
- **Hard part:** separating a painting that was made as one piece into layers that can move without visible cuts. The seams follow the mist, and cloud sprites hide what is exposed.
