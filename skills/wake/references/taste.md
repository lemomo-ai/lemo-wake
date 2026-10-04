# Taste: what makes a film good

These standards come from reviewing many films side by side: which ones people kept, which ones they rejected, and why. They are the most important reference in this skill. They describe what good looks like, not how to build it; you decide the plan.

## 1. Things in the picture really move

- The objects in the image must physically move: jump, fall, roll, fly, rise, inflate, close up, snap together, settle back. That is what "coming alive" means to viewers.
- Light, weather, colour grading and time of day can be a link in the chain, but on their own they do not count as motion. A sunrise that only warms the colours, fog that only burns away, sunlight that only sweeps across a table: all read as a filter, and all were rejected.
- If light spreads, whatever it reaches should react: balloons inflate and lift off, birds start up, the cat's ear twitches, candles ignite, string lights pop on bulb by bulb.
- People in a photo are actors too. They act on each other and on the things around them: a hand passes the cake, a friend ducks the confetti, a child reaches for the bubble and it pops. A camera that pushes in or follows while everyone stays frozen reads as a dead photo, and was rejected.
- Playful, characterful object motion is welcome. Breakfast that crouches, leaps out of frame and bounces back onto the plates is much better than sunlight passing over still breakfast.

## 2. Default to big

- The picture starts incomplete or gets taken apart: separations hang apart, a bridge is broken, beacons are dark, the plates are empty, only one lamp is visible.
- One action chains across the whole picture, with a hit in the middle (an impact, a snap into register, a slam, a burst).
- The complete picture arrives at the climax, not at frame one.
- The action covers most of the frame and most of the duration. Photos can be big too: objects and people cut out and set in motion, a chain reaction that travels through the scene, a camera journey that follows them.
- Rejected as too small: the untouched source image with a little local wobble and a few particles on top; a wave that tilts a few degrees; rain pausing mid-air. Calm and restraint are for when the user asks for them.

## 3. The signature move belongs to this image

- It grows out of what only this picture has: its printing method, its light source, its structure, its words, its objects' nature (paper is pulled, ink spreads, a stamp lands, a balloon fills, a record needle drops).
- You can say it in one sentence.
- Swap test: replace the image with another of the same kind. If the film still works unchanged, it is too generic.
- Effect blocks and reset transitions are supporting actors and raw material. The signature move is usually written for the image.

## 4. You decide

- Everything in this skill (types, recipes, blocks, transitions, numbers) is reference material from earlier films. Read the image, make your own plan, and overturn it when a first version is merely "moving". Better ideas than the docs are welcome; there is no need to justify departing from them.
- The only fixed boundaries: no image generation, no services that need API keys, no calling other skills.

## 5. One causal line, not a pile of effects

- A single event (wind, light, impact, scent, fire, water, a tap) travels through the picture, and each element reacts when it arrives. That reads as cause and effect.
- Many unrelated small effects each doing their own thing read as messy, even when each one is nice.
- Supporting effects stay lower in amplitude and opacity than the main line. Main line big, support calm.

## 6. Effects happen inside the picture

- In photos, light comes from where the photo's lights really are; reflections and the ambient light follow; brightness changes smoothly across real surfaces. A geometric ring or ellipse expanding over a photo looks like a pasted-on transition.
- Compute "before" states from the photo's own pixels (an unlit version of the lamps, a cooler and darker scene) rather than laying a coloured layer on top.
- In illustrations and prints, effects speak the medium's language: registration and halftone for print, washes and dry brush for ink and watercolour, squash and bounce for clay, crayon strokes for crayon.

## 7. Rigid things stay rigid; no fake motion

- People's faces, products, buildings, tents and letterforms look wrong when bent or warped. Move them whole (translate, rotate, rise, parallax) or cut them out.
- Panning, zooming or warping the whole untouched image is not animation. Decompose and rebuild.

## 8. Output size: the user picks the frame, you design inside it

- The output size and aspect ratio are the user's choice (SKILL.md step 1); the default is the source's own size. Do not change it on your own: a portrait A4 report silently reflowed into 16:9 was rejected because the user had not asked for another size.
- What happens inside the frame is yours. Fill it with the photo, turn the photo into a print, a card or a page with room around it, build a scene: whatever this image needs. Several of the most liked portrait films turned a portrait photo into a landscape journal page, because the user had asked for 16:9 output; the same ideas can be built in the source's own ratio.
- The main deliverables (MP4 and WebP) are never downscaled below the output size. Size limits are targets: lower quality or frame rate a little before touching pixels. Only the chat GIF and the sticker GIF are smaller versions, by design.
- The one exception is the performance guard for very large photos (long side above 2560 px), which new_project.py applies and reports; full resolution only when the user wants it.

## 9. Several photos in one image: each one gets its moment

- In a photo pile, a collage or a travel journal, every photo should be seen clearly once: fly to the centre, enlarge, hold, maybe let something inside it move, then settle back into place.
- Sweeping all photos past quickly, or blowing them away and back, leaves nothing in focus. Accept a longer film (around 8–10 s) if that is what it takes.

## 10. Screenshots in a device look like a current real device

- If you put a screenshot into a phone, draw a modern phone: full-screen display, Dynamic Island, thin bezels, metal frame, glass reflections, a believable shadow. Flat schematic phones and older models with thick bezels and a home button were rejected.
- Adapt the screenshot to the phone's screen (re-lay it out, extend backgrounds, keep content undistorted) rather than choosing an outdated phone that matches the screenshot's ratio.

## 11. The loop and the first frame

- The film loops forever, but the content does not have to return to its start: it can start empty and end full. Join the last frame back to the first with a transition that fits the style (an in-picture ending, or a frame-level reset from reset.py).
- In-picture endings that grow from the film itself are the most liked: the moon shrinks back into the book cover while night spreads like an indigo watercolour wash; the fire dies to embers; the candles are blown out.
- Page-curl, iris and ripple resets have tended to look cheap. Prefer others unless the image really calls for one.
- The first frame is often used as the still preview, so make it look good. It does not have to be the source image.

## 12. Readability and craft

- Every frame should be composed: pause anywhere and it should look like a deliberate image, including mid-transition.
- Once key information (a title, a number, a face, a photo) arrives, hold it long enough to read.
- Text enters in the medium's own manner: stamped or registered for print, written stroke by stroke for calligraphy, typed for tech or archives.
- Charts stay truthful: values land exactly on the numbers the chart prints, and proportions follow the data.
- Platform-native covers (for example Xiaohongshu) need the surprise people expect on that platform (a feed card that gets tapped open, a double-tap heart), not just pieces flying into place.
- Judge rhythm by watching the film play, not from stills.
- The bar is "looks like work from a good motion studio". If a version is fine but ordinary, rethink the idea instead of polishing it; if the same idea fails twice, change the idea.

## 13. Variety

- Check recent entries in the history file before starting. If the structure, signature move and main camera move match the last few films, ask whether the image really needs that or whether it is habit.
- Change `seed` values for blocks and resets on every film.
