# Portraits and Personal Photos

People's own pictures: selfies, friends, couples, wedding and graduation photos, family groups, old studio portraits.

## What these images usually contain
- One to a handful of people as the clear subject, often shot in portrait orientation, with a meaningful setting behind them (a café, cherry trees, a campus, a sea cliff, a skyline, a painted studio backdrop).
- Props that carry the story: a drink, a bouquet, a graduation cap, a veil, birthday candles, string lights.
- People cut out cleanly. `segment.py --model portrait` keeps flyaway hair, and merging it with `general` helps. `sam` with points or boxes picks out props and individual people. Faces and bodies are rigid: they can move whole (jump, lift, flip up, land) but should not be warped, and without image generation their limbs and expressions cannot change.
- Backgrounds behind a whole person are hard to inpaint well. A small group can be cleaned at crop level. Removing a whole family at once from a downscaled frame tends to smear.

## What tends to work
- Turn the person into the performer as a whole: cut them out as a white-bordered sticker that is lifted out of the photo and slapped back down, or that jumps out past the frame edge. A pop-up card layer can flip upright. Children can run and hop into place for a group shot. Rigid motion of the whole figure reads as playful when the picture openly treats the person as a cut-out: a sticker, a card layer, a collage piece, a print being placed. Inside an untouched realistic photo, the same rigid hop reads as a cardboard puppet: arms that never move and a frozen face make people look stuck in the photo. Warping a face does not work either.
- So the life in a people picture mostly comes from changing what the photo is and how the people relate to it: the photo becomes an object (a print, a Polaroid, a card, a page, a screen), and the people leave it, enter it, get placed into it, or are revealed by it, and things around them react. Moving people in place inside the untouched photo is the weakest option.
- Use the occasion as the signature move. A graduation photo throws the cap. A wedding photo gets a gust of wind and a flying veil. A studio photo gets the backdrop unrolled and a flash bulb. A selfie gets cut out and stuck into a journal. Ask what this particular moment is about.
- Candid photos often have no occasion (a picnic, a walk, friends at a table). Ask instead: why was this photo taken, and what would the person who keeps it want to relive? How did these people come to be in this frame, and could the film show them arriving? What is the one prop or gesture that carries the mood, and what could it set off? What would the photo be as an object: a print being developed or handed over, a page in an album, a card that opens? Pick one answer and build one causal line from it.
- Craft-paper or social-media journal treatments have worked well for personal photos: card stock, washi tape, die-cut stickers, handwriting, stamps, wax seals, a tri-fold or pop-up card. They are one option among many; build whatever you choose inside the output size the user picked.
- Let the hit spread outward from the person: ice cubes jump out of the drink, petals burst from the tree, sunflowers fly out of the bouquet, the city lights up building by building.
- Keep motion inside the photo believable. Hair can move through layered displacement, which composites the hair over its own inpainted plate and is exact at zero displacement, but keep it small (around 20 px). Lights can switch on bulb by bulb with real glow spilling onto nearby surfaces.
- Endings that grow from the picture: the sticker lifts and drops back into its hole, the cap flies at the lens and covers it, the veil blows over the camera, the city switches off in reverse. Among `reset.py` kinds, `develop` suits old photos, `paper` suits journal pages and `leak` suits warm snapshots.
- When the action ends on the finished page, consider starting the output from the hold so the first frame (the preview) is the complete picture.

## Pitfalls
- Never deform faces, eyes or mouths, because it becomes uncanny fast. Keep people rigid and move them whole. A sticker that flips should not pass through zero thickness. Keep a minimum width, or it disappears into a line.
- Removing everyone from a group leaves a smeared hole. One fix is to keep some people in place and only remove the ones who move. Take the staying people from the same partly-cleaned plate so their pixels line up exactly.
- Sprites that jump reveal their cut-off bottom edge. Extend the legs or body downward by copying pixels before animating.
- Masks leak. A hat mask can include hair, and a tassel inside the hat mask leaves a white ghost in the sticker border. Trim masks by hand where needed, and cut moving parts out of the parent sprite.
- White borders on masks that touch the image edge turn comb-shaped, and tiny stray islands each get their own border. Close and open the mask, and drop small fragments, before computing the border.
- Partly hidden props (fruit behind a basket, flowers buried in a bouquet) look broken as stickers. Use only complete ones, duplicate them with variation, or redraw them cleanly in code in the page's style.
- A lift that covers its own hole loses the "cut out" reading. Choose a lift direction that keeps the person-shaped hole visible.
- Flying objects passing in front of a face steal attention. Route them around the face.
- An opening the viewer cannot parse (flat layers seen from an odd angle) feels strange. Start with a readable object, such as a closed card, a folded card or an empty Polaroid.
- In CSS 3D, stickers inside the same 3D context can be clipped by a flap that is still bouncing. Render them as 2D sibling layers that follow the same transform.
- Scaling a bitmap prop 20x toward the lens blurs it. Swap to a vector drawing once it is large.
- Supporting people who are only lit up, with no action of their own, feel lifeless. Give them a small reaction if possible.

## Case cards

### Café Selfie: Cut Out and Stuck Down
- **Signature:** a glowing die-cut line traces her outline. She peels out of the photo with a white border, leaving a person-shaped hole. She swings in mid-air and slaps back down larger, her head breaking the frame. The shock pops ice cubes out of her latte, a sun out of the window and leaves off the plant, then handwriting and a postmark finish the page.
- **Structure:** selfie close-up, cut, lift, slap-down climax, sticker chain reaction, handwriting and stamp, hold, then reverse.
- **Technique:** a portrait matte closed and dilated into a smooth die-cut shape. The photo card swaps to a holed version only while the sticker fully covers it. Handwriting fonts were fetched locally, and the drawn stickers take their colours from the photo.
- **Loop:** the stickers pop away, the ice jumps back into the cup, and she lifts and settles back into her hole as the border fades and the camera returns to the selfie.
- **Hard part:** peeling upward hid the hole behind her. Peeling toward the lower left and toward the camera showed the hole clearly. Ice arcs first crossed her face and were flattened to fly outward.

### Cherry-Blossom Picnic: Open It and They Jump Out
- **Signature:** a tri-fold gingham card opens flap by flap, and each of the three friends becomes a sticker that hops out. The one in the middle jumps highest and lands with a hit. Petals explode across the page, strawberries bounce out of the basket and title blocks slap down.
- **Structure:** folded card, seal sticker flies off, flaps open, three stickers jump out, landing hit, petals, fruit and title, then tape, handwriting and stamp.
- **Technique:** SAM cut-outs per person and prop, a LaMa plate under the jumpers, and a CSS 3D tri-fold with all paper elements drawn in code.
- **Loop:** `paper`: the whole journal page is pulled away to reveal the next folded card. The output starts on the finished page.
- **Hard part:** a sticker inside the 3D context was clipped by a flap that was still bouncing, and moving it to a 2D sibling layer fixed it. Partial fruit cut-outs looked like debris and were replaced by duplicated complete strawberries. A title font loaded without its glyphs and fell back to a default face.

### Graduation: Cap Toss Out of the Frame
- **Signature:** an empty-campus Polaroid. She bounces into the photo and out past its frame as a sticker, then throws her cap. It somersaults along a hand-drawn dotted trail and lands back on her head with a hit, and paper sunflowers burst out of her bouquet and cover the page.
- **Structure:** empty Polaroid, she bounces in, crouch, toss with the camera tilting up to follow, cap lands (climax), sunflowers, title and numerals, hold.
- **Technique:** a merged portrait matte, a SAM cap, and the empty campus from one clean LaMa pass, used as the opening. The top of the head under the cap was repainted in code. The sunflowers are drawn in code because the real ones were too occluded.
- **Loop:** she throws again, the cap tumbles at the lens, its board fills the screen and slides away to reveal the empty Polaroid.
- **Hard part:** the repainted head first looked like a striped hat. The cap's flip passed through zero thickness, and the camera did not follow the toss at first. The cap needed a loop at its apex so its path did not look flat.

### Seaside Wedding: The Wind Stands It Up
- **Signature:** a closed arched pop-up invitation is blown open by sea wind. The cover rises into the sunset backdrop, the cliff layer flips up, the couple's layer snaps upright (the moment he lifts her) and the veil whips out past the card edge. Flower layers pop up from their feet outward, the script writes itself and a wax seal stamps down.
- **Structure:** closed card seen from above, cover opens, layers flip up from far to near, couple (climax), flowers, text, hold.
- **Technique:** true CSS 3D layers placed at depth and scaled by (P−z)/P so they recombine into the photo exactly at the front view. The veil is a spring-driven mesh, and its alpha came from depth and from the colour difference against the plate.
- **Loop:** the wind returns, the veil blows off and covers the lens, the card folds shut behind it, and it clears to the closed invitation.
- **Hard part:** a first opening of half-raised layers seen at an angle was rejected as confusing. Starting from a closed invitation made it readable. Layers near the camera plane dropped out in CSS 3D, so the veil switches to a 2D canvas for the final push.

### 1960s Family Portrait: Click
- **Signature:** under a spotlight only the parents sit on the bench. The painted lake backdrop unrolls behind them and sways, the brother runs in and the sister hops in, and the flash fires, turning the frame white. As the white fades, the scalloped vintage print is there.
- **Structure:** empty studio, backdrop, family assembles, "look here" push-in, flash (climax), pull back on the finished print.
- **Technique:** SAM cut-outs of each person. Only the children were inpainted, so the parents never move. The studio is neutral black and white, and the warm sepia of the print appears with the flash.
- **Loop:** `develop`: the print fades to blank paper and the next one develops from the shadows. Try several seeds and pick the most even one.
- **Hard part:** inpainting the whole family smeared, which is why the parents stay put. A grey smoke puff read as a stain on the print and was cut, because a clean main line matters more than extras.

### Rooftop Blue Hour: The City Lights Up for Her
- **Signature:** the string lights beside her switch on bulb by bulb. The light leaps into the city and windows light up from near to far, towers rise into place, and the tallest one shoots up last and flashes at its tip. Then an evening breeze lifts her hair and swings the bulbs.
- **Structure:** dark dusk, string lights, windows, skyline rises, tower peak (climax), wind back on her, hold.
- **Technique:** a single WebGL shader with an unlit plate, per-window arrival times and buildings matted by their difference from an inpainted sky. Hair moves by layered displacement.
- **Loop:** in-picture: the towers sink, the windows switch off from far to near, the string lights go out last and the camera returns to its opening position.
- **Hard part:** the clean sky behind the buildings needed LaMa for large areas and interpolated sky near the stumps, because LaMa alone grew the towers into smoke. The unlit windows needed different methods near and far. A tower that settled too early broke the climax, so it was retimed to accelerate into the hit.
