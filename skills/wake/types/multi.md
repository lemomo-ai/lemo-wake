# Multiple Photos

One image holding several photos: a pile of prints on a table, a scrapbook or journal collage, a mood board.

## What these images usually contain
- Several photos with white borders, overlapping in a definite stacking order and tilted at different angles. Some edges are hidden under other photos, tape or objects.
- A surface: linen, a wooden table, cream card stock. Often there are props too (camera, passport, tickets, dried flowers) and doodles (dotted flight paths, hearts, suns, a handwritten title).
- Each photo is its own little scene with things that could move inside it: boats, trams, scooters, palms, hair, water, fog.
- The photos are naturally separable, which makes "take it apart and rebuild it" cheap. In generated images, though, the photos are often not exact rectangles.

## What tends to work
- Give every photo its own moment to be seen. One proven pattern: the photo flies to the centre, grows to around 60% of the frame width and holds for roughly half a second to a second while the background dims and a paper sheen crosses it. Then it shrinks, rotates back to its original angle and lands in its exact place. The next photo can launch while the previous one is landing so the rhythm never stalls.
- While a photo is featured, make something inside it move: a canoe paddles, a camel caravan walks, a train runs into a tunnel, a tram drives toward the lens with its lights on, palms bend in the wind, hair lifts, a lake ripples and the fog drifts. Movement is easier to read at this size than after the photo lands.
- Find a cause that delivers the photos and comes from this image. A camera on the table can shoot each print out of its lens. A summer wind can blow the page empty and bring the photos back. A doodled paper plane can fly its dotted route after the last hit.
- Use the real stacking order as the landing order, so the last photo down rebuilds the original exactly. Save the heaviest landing for the last or most striking photo: it holds longest, drops fastest and shakes the whole surface. The other photos and props hop in the order the shock reaches them.
- Hold the camera still at full frame during the features. The centre spot works like a main screen, and camera moves distract from it. Keep zoom punches and shakes for the hits.
- Endings: photos flying back into the camera in reverse stacking order, or a true loop where the opening gust strips the page. A collage reads well with `paper`, `tear` or `brush` when a transition is needed.
- Featuring each photo makes the film longer than the usual ~5 s (around 9 s is reasonable). The MP4 and WebP keep full resolution; a longer film mostly costs WebP size, which `encode.py` handles by lowering quality/fps, not pixels.

## Pitfalls
- All the photos sweeping past fast, tilted and mid-flight leaves no photo with any focus. This was the main reason first versions were rejected.
- Motion inside the photos that only happens after landing, when each photo is small, is effectively invisible.
- Hidden parts of a lower photo have to be inpainted, and the result shows once the photo is enlarged. Inpaint each photo only from its own content: mask everything outside its outline so neighbouring colours don't bleed in. Then redraw the white border at its measured width and colour, and remeasure corners where a featured photo exposes defects.
- Corner points measured by eye are off by a few pixels and leak a neighbour's border or sky into the sprite. Snapping to the white-border edges (fit lines to the border-to-surface brightness step and intersect them) is more reliable, with manual fixes where the step is unclear.
- Shadows between photos are baked into the lower photo. Inpaint a band of about 10 px along the edge of the photo above, and redraw each photo's own shadow as its own layer.
- An inpainted empty table looks like plaster. One fix is to use the blurred LaMa result as the lighting layer and multiply it by real fabric texture tiled from visible areas. Blend the tiles in a way that preserves variance, and don't flip them, or diamond patterns appear.
- Wind lines and impact lines drawn on the top layer cross the photos and look dirty. Draw them on the paper layer so the photos cover them.
- Dimming the background too much greys out the whole middle section. A light warm dim of about 20% is enough.
- Identical flight arcs for every photo feel mechanical. Vary them: skimming low, lobbed high, a full flip before the final hit.
- Photos sliding off the page should stay flat and slide under the ones above. Lifting them breaks the stacking order.

## Case cards

### Travel Photo Pile: Click, One by One
- **Signature:** each press of the shutter on a vintage camera shoots a travel print out of the lens. The print flies to centre stage, enlarges and holds while something in it moves (a canoe paddles, camels walk, a train enters a tunnel), then drops onto its own spot in the pile. The snowy-train photo holds longest and slams down, shaking the whole table.
- **Structure:** empty table and camera close-up, six shutter clicks each with fly to centre, feature and land, heavy final hit, hold on the complete pile.
- **Technique:** per-photo sprites with hidden areas inpainted from their own content and borders redrawn. The empty linen was rebuilt as LaMa lighting multiplied by tiled real texture. SAM cut-outs of the moving subjects inside the photos. The passport and camera stay on top, and the camera recoils.
- **Loop:** in-picture: prints lift off from top to bottom and fly back into the lens while the camera pushes back to its close-up. The output starts from the hold, so the first frame is the full pile.
- **Hard part:** the first version flew each print straight from the lens to the table, and none could be seen properly. Adding a centre feature fixed it. Enlarging the prints then exposed inpainting and border defects that had to be remeasured. The prints were not true rectangles.

### Summer Travel Journal: Every Photo Steps Forward
- **Signature:** a summer gust strips the page bare and then brings the five photos back one at a time. Each one stops at centre stage, enlarged, while its contents come alive: hair and bougainvillea blowing, palms bending, a tram driving closer with its lights on, a scooter hopping, a lake rippling as fog drifts. It then lands back in the collage with a slap. The lake photo lands last and shakes the page, and a paper plane slips out from under it, flies its dotted route around a heart, and the title writes itself.
- **Structure:** wind takes the page apart, five features, each landing back in place, heavy final hit, paper plane, handwritten title, hold.
- **Technique:** borders found by threshold and line fitting, then perspective-flattened photo textures with hidden parts inpainted. The doodles were extracted by dividing them by the paper colour, so they recombine exactly with the source. Mesh warps with weight maps animate the palms, hair, water and fog, and SAM cut-outs handle the tram and scooter.
- **Loop:** no transition. The opening gust is itself the "take apart", so the film starts and ends on the complete page.
- **Hard part:** the first version swept every photo in quickly and moved their contents only after landing. Giving each photo a centre feature with its contents moving during it fixed that. Wind lines drawn over the photos looked dirty and were moved under them. The paper plane drawn on top looked like an ink smear across the lake and was moved underneath it.
