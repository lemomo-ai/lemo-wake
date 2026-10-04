# Logos and Brand Marks

Users bring a brand mark, an icon plus wordmark lockup, sometimes with a tagline or seal, and want it to come alive as a motion logo.

## What these images usually contain
- A symbol with an idea built in: a ring and a satellite, steam that turns into mountains, a half sun with rays over waves, a crescent moon cut into a vinyl record.
- A wordmark (often geometric sans or retro serif), a wide-tracked tagline, sometimes a divider, a seal or a stamp.
- Flat, very even backgrounds (dark navy, bottle green, cream paper) and one to three ink colours. Decomposition is usually clean; no inpainting needed.
- Simple geometry that can be measured exactly: circles, rings, discs, horizon lines, sine-like waves, strokes with a consistent width.
- Square or wide formats; keep the source pixel size.

## What tends to work
- Read the story the mark already tells and let one element act it out. The satellite draws its own orbit; the steam climbs and snaps into mountain ridges; the sun pushes up out of the sea and its rays open like a fan; the moon is the stylus that drops onto the record. The name, tagline or style period often gives the hint (an "orbit" tagline, "sol" in the name, Art Deco fans, a 70s record label).
- Take the mark apart first, then let a single causal chain rebuild it: the hero element moves, its impact passes to the next element, and the full lockup arrives at the climax. Wordmark and tagline should be pushed into place by that chain, not simply faded in.
- Two hits with a breath between them works well (break the horizon, then open the fan; drop the needle, then the record spins up).
- Vary the letter grammar to suit the mark: letters popped up from the baseline by a bouncing ball, rising in order of distance from the cup, flipping outward from the centre like the fan, bouncing up from below the frame to the beat. Avoid defaulting to a plain staggered rise.
- Decomposition options: unmix alpha by projecting each pixel from background colour to ink colour; split by connected components into per-letter and per-part sprites; make sprites at 2x with a smooth alpha edge so push-ins stay sharp. Rebuild geometry as vectors from measurements (fitted circle centre and radius, a least-squares pivot for rays, sine fits for waves, skeleton plus stroke width for brush lines) so it can bend, roll, dent and spring.
- Swap vectors back to original sprites once things settle (fade the sprite in under the vector, then fade the vector out) so held frames are the source pixels.
- 2.5D is cheap and effective: tilt an orbit into perspective with near-large/far-small, give a hovering element a cast shadow, push the camera toward the action and pull back for the full lockup.
- Supporting blocks can add accents (`spin` for discs and wheels, `sheen` on metallic marks, `sparkle`), but they cannot carry the film alone.
- Loop: an in-picture take-apart at the start (rewind, sunset, "tea gone cold", reverse-wound orbit) with the original on the first and last frames is the natural join. Alternatives: a true loop for circular marks, `backplay`, or frame-level kinds like `squash`, `flash` or `zoom` for bold marks.

## Pitfalls
- Shape grammar that does not match the mark: round radial-gradient clouds looked like stains on an ink-line logo; flattened horizontal mist bands fit. Ellipse rings and orange geometric halos look like generic UI.
- Trails made of discrete circles read as bubbles; tapered, fading segments read as a comet tail.
- Fading a solid shape with opacity leaves a translucent grey disc; clip it away (for example, a shrinking circular mask) or keep it opaque while it moves.
- Too much rotation packed into the start of a move makes letters clump; spread the turns across the flight.
- Starting motion while the opening crossfade is still running creates double images; finish the crossfade on a still frame, then move.
- Dead air after the take-apart (one small object drifting slowly from rest) feels empty; give it initial speed.
- Camera pulling out immediately after a hit steals the moment; hold briefly, then pull back. Text appearing off-frame during a push-in is wasted.
- Elements that are not in the logo (a tonearm, a pouring stream) are fine as brief props but should exit quickly; they can read as additions.
- Dark letters crossing a dark disc vanish for a few frames; route them or keep the overshoot small.
- The film keeps its output size (`encode.py` never downscales the MP4 or WebP; only the chat GIF and sticker are smaller).

## Case cards

### Halora Orbit Mark: The Ball Draws Its Own Orbit
- **Signature:** the coral ball races around a tilted 3D orbit, its trail cooling from orange to the purple ring; when the ring closes it is flung out, bounces across each letter of the wordmark (each letter pops up to catch it), gets kicked back and slams into its slot, denting the ring and sending halo waves that lift the tagline.
- **Structure:** original, ball winds the ring back onto itself and letters sink, draw the orbit, six bounces, high lob, impact, settle into the original.
- **Technique:** ring and ball redrawn from measured sizes with perspective line width; letters as luminance-alpha sprites; ring dent as a Gaussian bump travelling both ways plus a spring.
- **Loop:** the reverse-winding take-apart plays at the start; first and last frames are the original.
- **Hard part:** the ball started its orbit from rest and left a near-empty second; given initial speed. A bubble-like trail became a tapered comet tail; the camera was too wide during bounces and now follows the ball.

### Mountain-Nook Tea House: Steam Becomes Mountains
- **Signature:** tea pours into an empty line-drawn cup, two wisps of steam twist upward and snap into the two mountain ridges, peaks spring up and flick ink dots; the impact makes the cup jump, the name rises letter by letter and the red seal stamps down from in front of the camera.
- **Structure:** full logo, "tea gone cold" take-apart (seal lifted, text sinks, ridges collapse into the cup), pour, climb, snap into mountains, cup jump, text, seal, hold.
- **Technique:** the two strokes skeletonized into a centreline with stroke width and redrawn with travelling waves; all other parts are 2x sprites unmixed against the flat paper.
- **Loop:** take-apart at the start; first frame equals last.
- **Hard part:** climax mist drawn as round gradients looked dirty; flattened ink bands fit the style. Thin steam drawn segment by segment beaded at the joints until drawn opaque on its own layer and composited once. The pull-back right after the hit stole it; a short hold fixed that.

### Solenne Seaside Hotel: Sunrise Fan
- **Signature:** the horizon bulges, breaks and twangs like a plucked string as the sun bursts out with gold droplets; the rays, folded into one, slide out and snap open like an Art Deco fan; the letters flip outward from the centre and the divider and tagline spread.
- **Structure:** original, sunset take-apart, night with rolling waves, bulge and break (hit one), fan opens (climax), letters and tagline, crossfade to the original.
- **Technique:** rays rotate as original sprites around a least-squares pivot, so they land pixel-exact; horizon and waves rebuilt from measured centrelines and sine fits so they can roll and lift; sun pop is an analytic damped oscillator.
- **Loop:** sunset at the start; first frame equals last.
- **Hard part:** the string recoil dipped into the first wave; small gold specks read as dust and became fewer, larger droplets; letters spun too much early and clumped until the flip was reduced and spread over the flight.

### Moon Groove Records: The Moon Drops the Needle
- **Signature:** a tonearm swings the crescent moon in, it drops into the gap in the record like a stylus, light runs around the grooves and pops the two stars; the music starts, the record turns a full revolution and the letters bounce up from below to the beat.
- **Structure:** original, rewind (record spins backwards, grooves retract, moon flung off, letters drop out), arm swings in, needle-drop hit, light runs the grooves, second beat with spin and letters, group bounce, crossfade to the original.
- **Technique:** disc, label and hole as vectors from sub-pixel radius fits; grooves revealed by annular-sector clipping of the original sprite so they stop on the source pixels; fling speed from the derivative of the spin angle.
- **Loop:** rewind at the start; first frame equals last.
- **Hard part:** the moon's dark side faded to a translucent grey disc until it was clipped by a shrinking circle; the record started spinning during the opening crossfade and doubled; the second beat felt weak until the record made a full turn.
