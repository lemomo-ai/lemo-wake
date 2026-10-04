# Landscape and Lifestyle Photography

Real (or photo-real) pictures: landscapes, interiors, food on a table, scenes from daily life, sometimes with a printed title on top like a postcard.

## What these images usually contain
- One continuous photograph where light, perspective and depth are baked together. Pulling it apart leaves holes that have to be filled, so "taking it apart" costs more than with posters or collages.
- Discrete, liftable things sitting in the scene: food items, balloons, candles, a pet, a lamp, boats, birds. These are the actors. `segment.py --model sam` with points or boxes cuts them out one by one.
- A light source that explains the whole mood (a fire, a lamp, the sun, candles, a window). It is a good carrier for a chain reaction, but it is not the action by itself.
- Large rigid shapes (tents, buildings, furniture) that look wrong when bent. Move them whole: translate, rotate, rise, parallax.
- People. When they are the subject, read `portrait.md`: rigid cut-outs of real people moving inside an untouched photo look like puppets.
- Sometimes a text layer (a calligraphy title, a caption) that can be cut out and performed separately.

## What tends to work
- Let the things in the photo perform: food crouches, jumps out of frame and lands back on the plate; candles fall into the cake like meteors; deflated balloons fill, stand up and lift off; buildings rise out of the skyline. Ask what each object would naturally do (fill, ignite, fall, roll, take off) and build the signature move from that.
- Start from an incomplete picture: a dark room, an empty plate, an empty sky, a dawn before the sun. The complete source image arrives at the climax.
- Use light as the fuse, not as the show. One option: a WebGL pass that blends a computed "before" state with the original according to an arrival-time map (distance from the source + depth + noise), so light spreads along real surfaces, and every object reacts at the moment the light reaches it.
- Compute the "before" state from the photo's own pixels (desaturate, darken, cooler; darken harder near the light source because those pixels were lit by it; replace glowing pixels with an estimated unlit plate). Do not paste a filter on top.
- A camera journey can support the action: open close on one emotional detail, follow the chain, pull out to the full frame for the climax. It is a supporting move, not the action: a camera travelling over a photo where only small things stir reads as a slideshow, and was rejected. The approved coast film worked because the lamplight spread and the coast physically reacted while the camera pulled back. `depth.py` gives the depth map for light parallax during moves; let the parallax settle to zero on the full frame so it matches the source exactly.
- Supporting blocks that fit photos: `godrays`, `dust`, `steam`, `embers`, `snow`, `fog`, `water`, `ripples`, `twinkle`, `sparkle`, `confetti`. Keep them secondary.
- Endings: an in-picture ending is usually best (the fire dies back to embers, she blows out the candles, a near out-of-focus balloon rises past the lens and covers the frame). A true loop also works when the action starts and ends on the full photo. Among `reset.py` kinds, `sweep`, `mist`, `steam`, `leak` or `develop` suit photos; `passby` and `lightcut` are in-picture options.
- If the photo carries a title, cut it out and let it be written or stamped in the style of its own lettering once the full frame has arrived.

## Pitfalls
- Light or colour alone does not count as motion. A sunrise that burns off fog, or sunlight sweeping across a breakfast table, reads as colour grading. If light spreads, the things it reaches must jump, rise, sway or ignite.
- Light spreading as a geometric ring or ellipse looks like a transition stuck on top. Use a wide feather (hundreds of pixels), bend the front with depth and noise, and warm only lit surfaces.
- A very dark first frame makes a near-black thumbnail. Lift the "before" state until the scene is still readable.
- Full-frame inpainting gets downscaled and smears large holes into blobs. Crop each region and inpaint it at close to native resolution, then paste it back. For big, simple surfaces (an empty plate, a mug bottom) rebuilding them in code can beat LaMa: a smooth push-pull fill plus procedural grain and speckles. Avoid mirrored tiling, because it creates diamond-shaped repeats.
- Depth maps may be 16-bit. Normalise them before converting to 8-bit, or they clip to pure white and both parallax and arrival timing silently stop working.
- Sprites cut with a dilated mask carry a 1 px rim of the old background, which shows as a halo once they move. Shrink the sprite alpha slightly while keeping the erase mask dilated.
- Effects drawn on a screen-blend overlay ignore occlusion (sparks glowing through rocks in front). Draw them into the object's own layer so nearer terrain still covers them.
- Full-screen white flashes wash the frame out to grey. Keep flashes local and warm, with only a faint global lift.
- Objects that are partly hidden in the photo look broken when they fly. Move only the complete ones, and leave the others in place with a gentle sway.
- Smoke drawn as line segments looks like a comb. Use soft radial puffs laid out over time, with a faint core.
- Camera splines can overshoot during the hold, so the full frame never quite matches the source. Keep the hold still at scale 1.
- Close-ups are limited by the source resolution. Past about 1.7 to 2x the photo turns soft.

## Case cards

### Lamplight Reveal (coastal postcard with a tent and a calligraphy title)
- **Signature:** opens on just the tent and its lamp, the only warm thing on a grey coast. The camera pulls back while rings of lamplight spread, warming the coast, flashing glints on the sea and pressing the grass flat.
- **Structure:** reveal journey: lamp close-up, slow pull-out with radial parallax, light spreads to the full view, brush title writes itself, a seagull crosses.
- **Technique:** depth-based radial parallax, a light-arrival blend, a brush-stroke reveal for the title. The tent and person stay rigid.
- **Loop:** in-page ending. The camera pushes back to the tent, the rings shrink into the lamp and the brush strokes un-write.
- **Hard part:** a first attempt bent the tent, scattered unrelated particles and swung the camera until the title was cropped, and it was rejected. A cleaner cloud-shadow version came next. The approved version has one continuous action carried by the picture's own light source. It is the most light-driven sample, so pair this approach with things that physically react.

### Fireside Calico Cat
- **Signature:** in a cold blue cabin the hearth holds only embers. The fire roars up, sparks burst, the cat's ear twitches, and the firelight crawls across the stone and floor until it outlines the cat in gold. The cat lets out a long breath, a candle lights and a mug starts to steam.
- **Structure:** cold close-up on the cat, the camera pans to the hearth, the flare-up (climax), the light spreads, pull-out to the full room, hold, then the fire dies.
- **Technique:** one WebGL shader blends the computed cold version with the original by fire strength times light arrival. The flame is the photo's own flame layer, stretched upward from the top of the logs with rising turbulence. Breathing and the ear twitch come from local transforms on a SAM mask.
- **Loop:** a log collapses in a burst of sparks, the fire sinks to embers, the warmth retreats and the camera returns to the cat.
- **Hard part:** stretching the flame also stretched the holes left by the grate bars, and the cold version still showed a ghost of the flame. Both were fixed by filling the bars with flame colour and computing the cold version from an inpainted firebox. Sparks first looked like rain, and they became fading streaks with hot heads.

### Breakfast Bounce
- **Signature:** the whole breakfast crouches and leaps out of frame, leaving empty plates. The pieces then bounce back one by one: berries plink into the bowl, the croissant thuds down, toast and eggs somersault in, and the last egg lands with a splat that sends a shock wave of little hops across the table.
- **Structure:** true loop: anticipation, jump-out, empty plates, staggered landings, splat climax with a ripple of hops, then a small steam heart and the original photo.
- **Technique:** 14 SAM sprites with squash and stretch. The empty plates were rebuilt in code (push-pull base colour plus procedural speckle). The film cross-fades to the untouched photo while still, so the first and last frames match the source pixel for pixel.
- **Loop:** none needed. The film starts and ends on the original, and the crouch picks up straight from the hold.
- **Hard part:** a first version had sunlight sweeping the table and lighting each item. It was rejected as too static, which led to the rule that the objects themselves must perform. Inpainting the plates also took several tries. Eggs spinning flat like wheels looked odd, and flipping them end over end like pancakes fixed it.

### Sunrise Balloons
- **Signature:** at blue dawn a flat balloon lies on the ground. Three burner blasts light it like a lantern and lift it upright. Then the sun bursts over the ridge, and wherever its light reaches, balloons inflate, fire their burners and lift off until about thirty fill the sky.
- **Structure:** build and journey: dawn close-up, the balloon stands up, pull-out, sunrise, balloons launch in the order the light arrives, full sky.
- **Technique:** 31 SAM balloon sprites with per-sprite depth, occluded only by terrain that is nearer. The dawn version is computed in the shader. Plates were inpainted in crops at about 1 to 1.5x scale.
- **Loop:** an extreme close, out-of-focus balloon rises past the lens, fills the frame and reveals the dawn opening.
- **Hard part:** this sample followed a rejected sunrise-over-a-lake film in which only colour changed, so here light only triggers and the balloons are the action. Launch flames first glowed through foreground rocks and had to move into the occluded layer. The cover-the-lens pass was first slowed in the middle and showed half a second of blur, and running it at constant speed fixed that.

### Birthday Candles as Shooting Stars
- **Signature:** in a dark room six lit candles streak down into the cake one by one. The frosting dips, sprinkles jump and the glow grows on the girl's face. The last candle slams in, light bursts outward, string lights come on bulb by bulb, balloons drop from the ceiling and party poppers fire confetti.
- **Structure:** build (dark, candles land, candlelight, whole room lit), hold, then she blows the candles out.
- **Technique:** candle sprites extended below the frosting line and clipped by a per-column frosting mask, so they appear to sink into the cake. Bulbs were found by brightness and local contrast. The dark version is computed per pixel.
- **Loop:** she blows, and the flames tip over and go out from right to left, smoke rises, confetti blows away, the room darkens and the camera returns to the cake, ready for the next wish.
- **Hard part:** the clip mask was saved without alpha, so the candle extensions showed as white sticks. A full-screen flash greyed out the climax and was localised. The relatives only get lit and have no action of their own, which is the remaining weakness.
