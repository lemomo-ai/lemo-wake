# Xiaohongshu (RED) Covers and Text Cards

Portrait note covers (usually 3:4) built around a big title: a photo with headline, highlighter blocks and stickers on top, or a pure typographic card on paper with hand-drawn bits.

## What these images usually contain
- A large bold title, often in two or three lines, with one key number or phrase (days of a trip, books per year, minutes to cook).
- Platform decoration: yellow highlighter blocks, round or pill stickers ("super detailed", "solo meal"), speech bubbles, stars, short accent strokes, hand-drawn arrows, sticky notes, handwriting.
- Either a photo layer (travel, food, people) under the design layer, or a flat paper background (grid paper, solid mint, cream) that is easy to rebuild.
- Often one small object that is the only "thing" in a typographic card (a stack of books, a bowl, a cup).

## What tends to work
- Ask what makes this a note on that platform and not just any poster. Viewers expect a little surprise. One direction that worked: act out the platform moment itself — scroll a two-column feed, tap the card, the cover opens full screen and wakes up, a double-tap bursts a big red heart, likes roll up, the favourite star turns yellow, then the note shrinks back into the feed. Draw only generic feed UI; no brand logos.
- Another direction: let the title's own content drive the action. A number can be counted up by objects flying in (books shooting out of the book stack and landing in "52"); a list of ingredients can be the order in which food falls back into the bowl, each word of the title stamping down as its ingredient lands; a "10" can become a kitchen timer that completes one turn.
- Use the highlighter as a progress bar, the arrow as a fuse that carries the shock to a sticky note, the sticker as the final slap. Decoration becomes part of one causal chain.
- Make the photo layer react, not just the text: flower curtains spring per row, a skirt and hair ripple, petals are knocked into the air (and can turn into small hearts), the lake glints where the shock arrives.
- Typographic cards decompose cleanly: rebuild the grid paper procedurally (paper colour field times per-column and per-row line factors), back-solve alpha for each glyph against the plate, keep the original ink colour. Split sticker-style text into a white-outline layer and an ink layer so neighbours do not clip each other.
- Photo covers: `inpaint.py` to remove the title, `segment.py --model sam` for people, bowls, chopsticks, stickers; colour clustering for small ingredient pieces.
- A good opening is the complete cover (it doubles as the preview), then something shakes or tosses it apart in under a second; the complete cover returns at or after the climax and holds long enough to be read.
- Keep the exact source size (commonly 1086×1448). When the file gets heavy, trade frame rate and quality for size (for example 15 fps at a lower WebP quality), never pixels.
- Loop options: in-picture endings usually fit best (the note shrinking back into the feed; the opening shake that empties the page; a true loop where the closing hold is the original pixels). `paper` or `brush` from `reset.py` are alternatives for plain card styles.

## Pitfalls
- Assembling the cover piece by piece (words drop, highlighter wipes, sticker slaps) is big motion but generic; it was rejected for lacking the surprise expected on this platform.
- Geometric shock rings expanding from the impact read as a transition overlay; use flashes, shakes and reactions that arrive in order of distance.
- Code-drawn petals or props look like flat stickers next to photo pixels; cut real pieces from the image instead.
- Hearts or particles drawn over the title hide it; draw them behind the design layer.
- Closed flying books read as chalk sticks; open, flapping pages read as books. Check that small flying objects are recognisable at playback size.
- Font subsets: preload digits explicitly or some parallel render workers fall back to a serif for counters.
- Old and new text sets overlapping when the scatter is too slow; clear the page before the rebuild starts.
- Inpainted areas under a removed object look smeared once revealed; paint procedural detail over them (noodle strands, soup sheen) or keep them covered.
- Over-designed extras (a liquid column that looks like a sausage slice, a swirl highlight that looks like a HUD ring, drop shadows that look like dirt) — remove them.

## Case cards

### Dali, 5 days 4 nights: tap and double-tap
- **Signature:** found in a two-column feed, tapped open, the cover wakes up; a double-tap bursts a big red heart, bougainvillea petals fly up and turn into small hearts, the lake glints, her skirt lifts, likes roll from 8,848 to 12k and the favourite star turns yellow.
- **Structure:** feed scrolls and stops, shared-element zoom to full screen, title letters jelly-jump, sticker spins and slaps down, handwritten "photo spot!" with an arrow to her; double-tap climax with distance-ordered reactions; hold; overlays fade and the note shrinks back.
- **Technique:** the whole cover is drawn into an offscreen canvas, then interpolated between card rect and full screen; other feed cards are crops of the de-titled photo with different grades and related titles.
- **Loop:** doodles and UI fade, the note returns to its card and the feed slides back to its starting offset.
- **Hard part:** a first version built the cover element by element with a wind of petals as the ending; it was rejected as having no platform surprise and was rebuilt around the feed and double-tap.

### Read 52 books in a year: books fly into the number
- **Signature:** the book stack in the corner erupts like a fountain of flapping books that arc into "52" while the counter runs 1 to 51 and the highlighter fills like a year-long progress bar; "3" slams down from in front of the lens as the climax.
- **Structure:** full cover, book stack hops and shakes everything off the page, "Read in a year" drops letter by letter, book fountain and count, big 52nd book lands, "I only did" springs up, "3" slams, shock travels along the arrow, sticky note slaps on, "tested and works" is handwritten, dissolve to the original.
- **Technique:** grid paper rebuilt from line factors; per-glyph alpha back-solved; arrival times accelerate so reading gets faster; counter value drives the highlighter reveal; arrow drawn by geodesic distance along its stroke.
- **Loop:** the page-emptying hop is both opening and ending, so first and last frames are the full cover.
- **Hard part:** flying books first looked like chalk; opened flapping pages fixed it. Digits fell back to a serif in some workers until digits were preloaded.

### 10-minute tomato and egg noodles: everything lands back in the bowl
- **Signature:** the bowl's contents are tossed out and the timer resets; soup swirls in, noodles curl in, tomato, egg and scallion fall back one by one and each stamps its own word of the title; the "0" in "10" fills like a kitchen timer; chopsticks slam the rim for the climax.
- **Structure:** original, wind-up and toss toward the lens, empty bowl, soup spiral, noodles, ingredients with title stamps, chopstick hit with flash and distance-ordered hops, bubble, stars and sticker pop, steam, settle on the original.
- **Technique:** 2.5D top-down fall (scale 1 + height, drift toward centre, shadow sharpens on landing); dozens of ingredient sprites from SAM plus colour clustering; empty bowl wall rebuilt in code; rim repaired by polar interpolation; procedural noodles over the inpainted patch.
- **Loop:** the opening toss is the bridge from the final hold, which fades to original pixels.
- **Hard part:** colour-keyed noodles came out as crumbs and the inpainted soup was smeared; both were replaced by procedural layers. Title glyphs lost their outline to neighbours until split into outline and ink layers.
