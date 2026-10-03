# Stickers and Avatars

Chat stickers, reaction images, greeting cards for family groups, and pet or cartoon avatars — usually square, meant to be seen small and on repeat.

## What these images usually contain
- One character or creature with a clear action or pose (running, waving, holding a cup), often hand-drawn with thick outlines and flat colour.
- A shouted word or slogan that is part of the joke, or a set of big decorative characters (gold, red, glittering) in greeting-card styles ("good morning", "peace and joy").
- Props and symbols with obvious behaviour: flowers, bouquets, suns, cranes, clouds, ribbons, stars, sparkles, coffee steam, speed lines, dust puffs.
- Often a plain paper or solid-colour background that can be keyed exactly; greeting-card styles instead have dense, photo-like detail everywhere.

## What tends to work
- Find the verb already in the picture and make it literal. A running duck really sprints out of frame and back; pencils stuck in a bun really erase and redraw the girl; a morning card really has the sun rise and the bouquet handed up; cranes really fly in carrying the banner.
- The words must take part, not sit as background: blown away by the slipstream and flying back to slam down, falling from the sky one by one, flying out of the sun, with the last character held high, trembling, then slammed as the climax.
- Destroy-and-rebuild suits this category: clear the scene (characters leave, words fly off, sun sets, picture is erased), hold a beat on the empty frame, then rebuild with one escalating chain that ends in a single heavy hit — screen shake, a one-frame zoom punch, flash, burst lines, a shock that makes everything already landed hop in order of distance.
- Little after-beats add charm: a squint smile, a small heart rising from the cup, stars popping in from near to far, a gold sheen across the letters.
- Plain backgrounds: compute alpha from the difference to the paper colour and back-solve the foreground colour, so sprites composite back to the original exactly; connected components split the pieces. For line art, a three-colour model (ink, white fill, background) gives separate line and fill alpha.
- Limbs and wings without cutting: rotate legs rigidly around the hip and hide the joint with an outlined capsule; animate wings and ribbons by mesh-warping a region of the body sprite with weights that fall to zero at the edges, so no hole opens.
- Busy greeting cards: `segment.py --model sam` (or `general`) for each word, flower and bird; assign shared white outlines to the nearest glyph; `inpaint.py` for the sky plate; fill holes with stamps of nearby texture (baby's breath) instead of trusting a smeared inpaint.
- Draw tools and symbols in code when they must be bigger or cleaner than in the source (a pencil enlarged to become the hero, then shrunk back before it reinserts).
- True loops fit stickers well: make every periodic motion an integer fraction of the duration (stride, dust, speed lines, ribbon wave), or end on original pixels so the seam is near zero. Otherwise a short in-picture transition (clouds closing from both sides and parting) or `squash` from `reset.py`.
- Keep the main film at the source's exact size (square sources stay square, for example 1254×1254). Every film also ships an automatic small sticker GIF (longest side 240, at most 500KB) for chat use, so the main file does not need to be shrunk for that.
- Short durations (about 4–6.5 s) and low frame rates (10–12 fps) suit the genre; a run cycle of four frames per step at 12 fps reads like hand-drawn animation on twos.

## Pitfalls
- Words flying along paths that cross words already landed pile into a mess; give each a clear lane.
- Hairline seams at the edge of a warped region, or a white gap at a rotating leg joint; pad the cut and put an outlined capsule under the joint.
- Tools at their original tiny size are unreadable at avatar size; enlarge them while they act.
- Grey "ghost" residue where something was erased looks dirty; erase cleanly. Too many leftover crumbs or particles also cost file size.
- Big solid areas revealed by a distance flood fill come in as blocky slabs; draw the outline first, then fill inward.
- A sun or prop removed from the plate leaves a pale ghost disc unless its halo is cut and filled too; a rising sun must stay inside the sky window so it does not pass in front of mountains.
- Hard geometric light rays and grey fog bands look cheap; blur rays at half resolution and grade dawn in colour (blue, violet, pink) instead of grey.
- A bouquet or object rising with overshoot exposes the frame's bottom edge; ease out without overshoot and extend the stems downward.
- Soft sprite edges blending with the layer below give white halos; dilate the alpha slightly to include adjacent original pixels.
- File size on detailed greeting cards: every whole-frame change (global shake, full-screen transition, global grade) costs heavily. Keep full-frame changes to the climax and the opening transition; make small hits local.

## Case cards

### Charge, duck!: sprint out and sprint back
- **Signature:** the duck crouches and zooms out of the right edge; its slipstream sweeps the three characters and the red stroke away; it bursts back in from the left, skids to a stop, the words fly back and slam down, and the dot of the "!" lands as the climax.
- **Structure:** running in place, wind-up, exit with stretch and afterimage, empty frame with dust, return and skid, words slam one by one, red stroke swipes in, dot lands with shake and burst lines, running in place again.
- **Technique:** sprites from paper-colour difference; legs rotate at the hip, wings and fist-wings mesh-warped inside the body sprite, ribbon tails as a travelling wave.
- **Loop:** true loop; stride, dust, speed lines and ribbon all divide the duration evenly.
- **Hard part:** a word's flight path crossed one already landed; entry moved to the upper left with less spin. Seams at warped wing edges and a gap at the back leg were fixed with padded cuts and an outlined thigh capsule.

### Line-art girl: two pencils
- **Signature:** the eraser-end pencil pulls itself out of her bun and erases the whole drawing from the bottom up; the other pencil shakes, escapes at the last moment, then redraws her along the lines; both fly back into the bun with two clicks, she squints a smile and a small heart rises from her cup.
- **Structure:** original, pencil pulls out and grows, zigzag erase upward with crumbs, escape, blank page, redraw from the bun outward, double reinsertion climax with squash and burst lines, smile and heart, hold on the original.
- **Technique:** pencils inpainted out and redrawn in code; ink and fill alpha from a three-colour model; draw order from geodesic distance along the ink, erase order from stamped eraser paths; impact squash shared between shader and overlay.
- **Loop:** true loop; the pencils end in their original places and the frame returns to the source.
- **Hard part:** pencils were too thin to read, the erased area left dirty ghosts, solid hair filled as a block. Fixed by enlarging the pencils, erasing cleanly, outline-then-fill, and erasing bottom-up for suspense.

### Good morning: sunrise and a bouquet
- **Signature:** the words leap away, the bouquet sinks, the sun sets back to dawn; then the sun rises, the bouquet is handed up from below, six roses open one after another, the ribbon bow tightens, and the three big characters drop from the sky — the last one hits with a flash, gold confetti and a shock that bounces roses and words.
- **Structure:** original, pack-up to dawn, empty sea of clouds, sunrise, bouquet up and roses bloom, bow tightens, words slam, subtitle pops letter by letter, gold sheen, hold on original pixels.
- **Technique:** segmentation for words, roses and bow; inpainted sky plate; rose holes filled with baby's-breath stamps so buds sit in a spray of small flowers; roses open by releasing a radial mask with an unwinding spring.
- **Loop:** true loop; the closing hold uses the original pixels.
- **Hard part:** dawn too long and grey, hard-edged rays, the bouquet's overshoot exposing the frame edge, white halos on roses; all fixed by colour grading, blurred rays, no overshoot and dilated alpha. The detailed image stays several MB at full size; frame rate and quality were lowered, not pixels.

### Peace and joy: cranes deliver the blessing
- **Signature:** two cranes fly in carrying the banner on red cords, it swings like a swing and drops into place; the sun rises and three gold characters fly out of it one by one; the fourth is tossed high, hangs trembling, then slams down — flash, rays, gold dust, stars popping from near to far.
- **Structure:** original, clouds close from both sides and part onto dawn, cranes deliver the banner and fly back crossing each other, sunrise, characters out of the sun, heavy final hit, sheen, hold.
- **Technique:** cranes and banner by SAM; gold characters cut by filling their red outlines; two inpaint passes; the sun moves only inside the visible sky window; wings flap by vertical mesh compression above the shoulder line.
- **Loop:** the opening cloud transition covers only the upper two thirds; the ending hold equals the first frame.
- **Hard part:** a pale ghost disc and leaking light where the sun was cut; solved by removing its halo too and restricting the window. File size was cut by making small hits local and keeping the climax shake to one frame.
