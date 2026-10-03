# Clay, Papercraft and 3D

Images with volume and material: plasticine or stop-motion-style scenes, layered paper-cut art, 3D renders, toy-like stylized product shots.

## What these images usually contain
- A small stage (pedestal, beach, tunnel, shelf) with a few chunky hero objects, props scattered around them, and often a title made of the same material (clay letters, folded paper type).
- Pieces with clear edges and their own shadows. They segment well and can be pulled apart without damaging the picture. One image can give dozens of sprites.
- A soft, blurry background (sky, sea, distant islands) or a depth structure built from stacked layers (paper tunnels, terraces). A depth map from `depth.py` usually comes out clean here, and the layer structure and the depth structure are often the same thing.
- What's hard to recover: whatever is behind the big objects (the ground under a pedestal, the sea behind a popsicle). Local inpainting turns large holes into smears.

## What tends to work
- **Speak the material.** Clay suggests stop-motion: objects animated on twos (15 fps steps while the camera stays smooth), a slight per-frame "boil" on edges, exaggerated squash and stretch, things placed by hand, landing with a thud. Paper suggests folding, pop-up-book hinges, layers lifting toward the camera, dye soaking into white paper. Rendered solids suggest rolling, balancing, toppling and clicking together.
- **Build the set, in staggered acts.** Stage, then hero object, then the matching title piece, then props falling in. Overlap the acts so the next one starts while the last props are still landing. End on one larger hit (the last letter slams down, the whole frame jolts and flashes) with the complete picture arriving there.
- **Let each object enter in a way that fits what it is.** A popsicle can freeze into existence from the stick up (a noise dissolve with an icy rim) rather than fly in. Fruit drops and bounces. Ice gives a star glint. Letters "boing" up in the same frame as their matching object.
- **Turn the image's colour or material into the event.** Start from a white, undyed paper version of the scene (high-passed luminance times depth-based occlusion times a paper colour), then let one drop of colour spread through the tunnel by arrival time. Cut paper regions arrive as whole pieces (felzenszwalb segmentation), and each piece pops forward when the colour reaches it.
- **Take the title literally.** A title that names an action ("give the ocean some blue") can become the whole film's event. Letters made of the scene's material can enter the same way the material moves: clay letters boing, paper letters fold up on their bottom edge like a pop-up book.
- **3D renders and rendered still lifes:** a sphere can roll convincingly if its fine luminance detail rotates while the broad shading stays fixed to the screen. A box can be cut into its visible faces and re-lit by face orientation as it turns. A plate/original ratio map gives shadows that travel with the objects. Pivot falling blocks on the edge they land on.
- **Use depth for a real camera move.** In a layered image, pushing deep into the centre and pulling back with stronger magnification on near layers reads as backing out of a tunnel. A pulse on that magnification makes the whole structure lunge.
- **Hide what can't be inpainted.** Keep the hard-to-fill parts (pedestals, ground) in the plate and animate everything else. Cover soft inpainted areas with something the scene would plausibly have: cold mist, clay cloud puffs, dust. Strips of sea and sand behind objects can be redrawn in code from the image's own colour bands and tiled texture patches.
- **Loop options:** `squash` (the whole picture flattens to the floor and the empty set pops back) fits clay well. `zoom` and `shatter` fit punchy 3D. Reversing the film's own mechanism also works: titles fold back down, the camera dives back into the tunnel, colour retreats to the drop.

## Pitfalls
- An impact drawn as an expanding ring looked like a gun sight. Short radial impact lines read better on clay.
- Pieces that were partly hidden in the source have estimated, made-up pixels on their hidden side. Bring those pieces in last, from behind the objects that cover them, so the guessed parts are barely seen.
- Inpainting several large regions in one pass shrinks the crop and comes back blurry. Inpaint in separate smaller passes. Re-inpainting tile by tile on top of a blurry first pass made it worse (the model continued the blur and produced checkerboard texture).
- Depth and segmentation computed on the image *with* the title and hero still in it carry their shapes into every derived map, and ghosts show up during the reveal. Compute derived maps on the clean plate.
- Decorative transitions drawn in code (a sweep of stylized paper waves) looked geometric and cheap next to real papercraft. Build the reset from mechanisms already in the film.
- Colour arriving with a white flash looked washed out and purple. Scale the existing colour up instead. Square debris read as party confetti; droplet shapes read as water.
- Losing the impact beat when replacing an element's entrance (for example, a pedestal that no longer slams down) costs energy. Make sure some other hit still lands in that slot.
- Keep a real hold on the complete picture near the end (roughly a second, with only small ambient motion such as seaweed sway or frost glints). Slow pushes during the hold make it feel unfinished.
- Layer offsets used for "lifting" must be undone by the end of the loop, or the outer ring visibly jumps at the seam.

## Case cards

### A Little Sweet Summer: Frozen Out
- **Signature:** three popsicles freeze into existence one at a time from the stick up, each colour's clay title character boings up in the same frame, and the last character slams down to shake the whole frame.
- **Structure:** three staggered acts (strawberry, orange, kiwi), each with pedestal, popsicle, matching title character and falling fruit. Then the final character lands as the hammer blow, a capsule label squeezes out like clay, the English letters pop like popcorn, and the scene settles with frost glints and cold mist.
- **Technique:** SAM point prompts cut dozens of sprites (letters, sticks, fruit, leaves, ice). Occluded parts are estimated from convex hulls and filled with normalized convolution plus grain. Objects animate on twos with edge boil, and the camera barely moves, like a tripod.
- **Loop:** `squash`. The finished poster flattens to the floor and reveals the misty opening set.
- **Hard part:** there was no clean empty beach to use as a backdrop. The approved approach keeps the pedestals in the plate, inpaints the rest coarsely, redraws the sea-and-sand strip in code, and opens with low cold mist and clay cloud puffs that get sucked into each popsicle as it freezes. The opening background is softer than the rest of the film, but the action hides it.

### Give the Ocean Some Blue: One Drop of Blue
- **Signature:** one drop of blue falls into a still-white paper ocean. The blue spreads through the paper tunnel layer by layer, each piece glowing and lifting as it's dyed, while the camera backs out of the tunnel. The turtle takes colour and swims in, the outer wave frame is reached and the tunnel lunges, then the title folds up letter by letter like a pop-up book.
- **Structure:** white sea, the drop lands, the dye spreads and the camera pulls back (climax when the outermost ring is dyed), the title folds up, a hold where seaweed sways and fish swim, then the reverse.
- **Technique:** one WebGL shader. Dye arrival time is the larger of distance-from-drop and depth (open water spreads continuously; outer layers arrive as whole paper pieces). Pull-back perspective inverts `p = c + v / (z·(1 + K·d))` by fixed-point iteration, and K is pulsed at the climax. Title letters are minimal-alpha patches over the plate.
- **Loop:** in-picture. The title folds back down, the camera dives back into the tunnel, and the colour retreats from the outside in to the landing point. The last frame equals the first.
- **Hard part:** a white opening that showed ghost silhouettes of the turtle and the title (fixed by recomputing depth and segmentation on the plate). Patchy islands of dye from summing distance and depth (taking the max fixed it). A code-drawn paper-wave reset was scrapped for the reverse of the film's own mechanism.
