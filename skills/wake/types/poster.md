# Posters and Layout

Designed posters: typographic layouts, screen prints and vintage travel posters, movie posters built on a photo, collage posters, 3D-rendered exhibition posters.

## What these images usually contain
- A title layer (big display type, often bilingual) plus small print: subtitles, dates, rules, registration marks. Usually sits on a smooth area (sky, wall, paper) and can be lifted out cleanly.
- A picture layer that is one of: flat ink colours (print), a photograph (movie poster), cut paper pieces and a figure (collage), or rendered objects on a plain set (3D still life).
- Flat print and collage pull apart without damage; a photo or rendered scene can't, because its light and perspective are baked in. Those are semi-separable: lift the text and a few objects out, keep the rest as one plate.
- Rigid things: letterforms, products, faces, geometric objects. Move them whole (drop, roll, rotate, slide). Don't warp them.
- Many posters are portrait (A4, 2:3, 4:5). The output keeps that ratio unless the user picked another size; if they did, design for the new frame rather than stretching or cropping the layout.

## What tends to work
- **Read the title as a script.** Poster copy often names the action: "FORM & LIGHT" can play as two acts (objects land, then light sweeps). Before inventing a move, check whether the words already describe one.
- **Use the medium's own production process.** Print: colour separations, squeegee pulls, misregistration snapping into register, halftone. Collage: pieces slapped on from off-frame with lifting shadows. Rendered still life: objects that roll, fall, balance and topple under believable light. Photo poster: the scene's own light sources, weather and the title set into it.
- **Start incomplete, peak once.** Empty set, blank paper, dark city or exploded plates, then the build, then one hit (snap, click, slam, burst of light) where the complete poster arrives. Let the impact travel: shake, a flash, debris in the poster's own colours, a neighbouring object that trembles.
- **One causal chain.** A trigger releases a path, and things react as the path reaches them (cap lifts, a scent ribbon winds past the title and reaches the figure's ear, hair and clothes move). Give each element an arrival time and start its reaction there.
- **Lift text by back-solving alpha.** Inpaint a text-free plate (`inpaint.py`, in small separate passes), then solve each glyph's alpha from plate vs. original. That keeps the original letterforms and texture, and the layer composites back pixel-exact. Cut it into letters or words to animate.
- **Titles enter in the poster's dialect:** stamped, printed, letters slamming down in time with a rolling object, revealed by the light passing over them, condensed out of rain, ink-bleeding in. Once the title is complete, hold it long enough to read.
- **Rendered objects:** `segment.py --model sam` with point or box prompts gives clean masks. A rolling sphere can rotate its texture detail while the shading stays fixed to the screen. Cube faces can be cut apart and re-lit by face normal. A plate/original ratio map gives shadows that follow objects.
- **Light that belongs to the image.** To brighten an area, multiply (color-dodge or a gain on the source luminance). Don't screen a flat colour on top. To switch lights off, build an "unlit" plate first.
- **Loop options:** `paper` (the printed sheet is pulled away, a blank one slides in), `halftone`, `tear`, `brush` for collage, or an in-picture reset made from the film's own mechanism (a second strike that cuts the power again, daylight burning the frame to white, the separations flying apart again). `passby` and `lightcut` suit photo posters.

## Pitfalls
- Adding a little motion to the finished poster (rain pausing mid-air, a few particles) was rejected as too small. The picture has to go through a real change.
- An energy surge drawn as an expanding geometric ellipse read as a transition pasted over the photo and was rejected. The approved approach made the photo itself go dark and relight lamp by lamp.
- Flat colour tints (an orange layer for "lights on", a yellow wash on a lit object) look like a colour-adjustment layer or plastic. Scale the original pixels instead.
- Screen-blended light bands and white dust turn the scene grey and hazy. Multiplicative light and dust in the floor's own colour read as real.
- Dimming lamps by plain multiplication leaves black holes where the lamps were. Region masks inside an analytic light field show up as hard shapes in the sky. Separate ambient light (analytic) from lamp light (a per-pixel map), and blend them by how much of each pixel comes from the lamps.
- Canvas textures drawn with straight alpha turn a lightning glow into a solid coloured block. Premultiply.
- Mask dilation that's too generous erases contact shadows and leaves bright halos around objects. Shrink the exclusion instead.
- Camera splines with keyframes near a later push drift during the "still" hold. Pin the camera completely still for the hold.
- A dark opening frame works as suspense, but it makes a weak still preview. Consider starting the output from the held complete poster.

## Case cards

### Before the Rain Ends: Lightning Lights the Street
- **Signature:** in a blacked-out city on a rainy night, lightning hits a tower, and power runs back down the street. Streetlights click on from far to near, their reflections run down the wet road, the bus-shelter lightbox stutters and then blazes (the frame jolts), and the rain "rains in" the title.
- **Structure:** dark city, strike, lamp relay toward camera, shelter climax, title, hold, second strike, lights die near to far, back to dark. The camera pulls back from a close framing to full frame as the lights come toward it.
- **Technique:** one WebGL shader. An inpainted text-free plate, a title layer from back-solved alpha, an unlit plate (warm-light pixels replaced by a blur of their non-lamp surroundings), and a map of per-pixel switch-on times stretched vertically on the road so reflections light in columns. A depth map adds parallax. Lightning is a midpoint-displacement polyline. Rain is three procedural layers that complete whole cycles over the loop.
- **Loop:** in-picture. A second strike hits a tall lamp, the lights go out in sequence, rain washes the title off top to bottom, and the camera pushes back to the opening framing in the dark.
- **Hard part:** there's no ready answer for "what does a photo look like with the lights off". Early versions had black holes at the lamps and visible region edges in the sky. The unlit plate plus the ambient/lamp split fixed both.

### Paris: Plates Snap into Register
- **Signature:** four colour separations hang in mid-air, misregistered, then slam together into register. The frame jolts, flashes white, and ink spatters as the finished poster appears.
- **Structure:** blank paper and empty acetates, squeegee pulls ink onto each plate in turn while the sun rises, a slow orbit around the exploded view, the snap, then the Eiffel Tower flashes like an on-the-hour sparkle.
- **Technique:** k-means splits the print into its few inks plus the sun disc, keeping the original pixels, so the plates stack back almost exactly (mean error under 1/255). CSS 3D planes with a perspective camera give real parallax. Registration marks, colour bars and paper are drawn in code.
- **Loop:** `paper`. The printed sheet is pulled away and a fresh blank one is in place.
- **Hard part:** the snap only feels right if the reassembled stack is indistinguishable from the source. The plates must come from the original pixels, not re-drawn colours, and misregistration springs back to zero with damping.

### FORM & LIGHT: Click and Daylight
- **Signature:** a clay sphere rolls into an empty gallery with the letters of FORM slamming down behind it. A blue cube spins down, lands on one edge, teeters, and tips onto the sphere with a click (shake, flash, chips, the black arch hums). Then a band of window daylight sweeps across the frame and LIGHT develops in it.
- **Structure:** two acts taken straight from the title: FORM (objects land by their own physics), then LIGHT (the sweep). Then a hold.
- **Technique:** SAM masks for each object; LaMa plates with and without them (a second pass removes the arch for its tremble). The sphere rolls in a small shader that rotates its luminance detail while the shading stays fixed. The cube is cut into three faces and re-lit as it turns. Shadows come from a plate/original ratio map, and letters from back-solved alpha.
- **Loop:** in-picture. The daylight keeps strengthening and burns the frame to white via color-dodge (bright walls go first, the dark arch last), and the empty gallery comes back out of the white. Output starts on the held poster, so the first frame is the original.
- **Hard part:** the first light band (screen blend) made everything grey and the hold drifted. Switching to color-dodge with a narrow edge and pinning the camera fixed both. The rendered "cube" wasn't a true cube, so it rotates as a whole in the air and pivots on its ground edge rather than being rebuilt in 3D.

### Scent Trigger (a Japanese collage perfume poster)
- **Signature:** the bottle's cap lifts. A gold-leaf ribbon of scent winds past the title and the painted landscape to the woman's ear. Her earring glints, and her hair, sleeves, dried flowers and leaves stir in the breeze.
- **Structure:** paper pieces slap in from off-frame, a brush stroke is dragged across, the bottle drops and squashes on landing, the figure develops, the cap lifts, the scent travels. Close-up collage, then follow the bottle, push in on the figure, follow the scent, pull back to full frame.
- **Technique:** each collage piece and each glyph is its own layer. The figure is cut out with colour key plus GrabCut (hair included) and develops from bleached to normal, spreading outward from the face. Hair and clothing bend by row displacement with a weight map that keeps the face rigid. Leaves and flowers grow from their stems. The title ink-blooms in.
- **Loop:** `brush`. Broad brush strokes wipe the poster back to blank paper.
- **Hard part:** moving a cut-out person without uncanny warping. The face weight stays at zero and only the outer hair and the clothes below the shoulders bend.
