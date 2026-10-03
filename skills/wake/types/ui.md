# Screenshots and UI

Chat screenshots (messaging apps, group chats, red-packet and sticker exchanges) and app screens that people want to turn into a lively moment to share.

## What these images usually contain
- A flat, near-uniform app background (chat grey, white list) with self-contained components on top: bubbles, avatars, timestamps, image messages, voice notes, red packets, stickers, cards, counters.
- A built-in order of events: messages arrive one by one, buttons get tapped, numbers tick, images open full size.
- One line or object that carries the story: a keyword ("I'll bring watermelon"), a date or count ("1000 days"), a gift, a reaction sticker.
- Often a portrait screenshot from an older or a newer phone; status bar and input bar are part of the image.

## What tends to work
- Components separate cleanly: compute alpha from the colour difference to the flat background and fill the message area with that colour to get an empty-chat plate. No segmentation model is usually needed; keep sprite coordinates in a `.js` file (a `fetch` of local JSON can fail under `file://`).
- Treat "messages appear in the real order" as the baseline, not the signature. The signature should grow from what is unique in this chat: a keyword that triggers the app's own easter egg (emoji rain), a red packet that gets opened, a number that hearts or confetti spell out, a photo message that opens into the world outside the phone.
- Let something leave the phone. A bubble flips out of the screen and becomes the object it stands for; a photo message enlarges behind the phone and becomes the background; the rain spills past the bezel. This gives the empty space around the device a job and turns UI into real motion.
- Borrow the platform's real gestures and exaggerate them: tap ripple, red-packet coin spin then tear-open, double-tap heart, unread red dot, counters rolling.
- Give every effect a destination and a cause: the hearts that burst from a gift fly back to form the number in the chat; the partner's reply turns into small hearts that land in that number and send a heartbeat through it.
- Camera: start close enough that the screenshot reads at about 1:1, follow new messages like auto-scroll, then pull back hard at the climax. The speed contrast sells the moment.
- Keep the source's exact pixel size and aspect ratio. If the idea needs room beyond the phone, pull the camera back inside that same frame rather than changing the canvas shape.
- A device mock-up, when used, must look like a current real phone: full-screen display with rounded corners, Dynamic Island, thin even black border, metal frame with edge highlights, glass reflection, soft ambient plus contact shadow, real side buttons, no logos.
- Adapt the screenshot to the phone, never the phone to the screenshot: extend it to a 19.5:9 screen by moving or uniformly scaling content (status-bar clusters into the two "ears" beside the island, header and chat moved down, chat area lengthened, home indicator and safe area added). Never stretch.
- Fitting fx blocks: `pop`, `write`, `pulse`, `confetti`. Loop options: an in-picture ending built from the signature object (a giant heart or watermelon sweeping across the lens, then cut back to the empty chat), `pop(out)`, or `reset.py` kinds such as `glitch`, `mosaic`, `crt`, `dissolve`.

## Pitfalls
- A drawn phone that looks like a flat diagram (uniform black slab, island pasted on a mismatched screen ratio) reads as fake immediately.
- Matching the phone to the screenshot's old 16:9 ratio gives a dated phone with bezels and a home button; that was rejected as not modern.
- The first seconds of sequential message pop-in carry little energy; land something heavy early (a red packet dropping with a phone shake) or shorten that stretch.
- Invented text (adding a caption that is not in the screenshot) — only reuse words from the image.
- New effects drawn on top of message text and hiding it; send them along a path away from the bubbles instead.
- Effects that start off-screen and take too long to arrive weaken the hit; spawn the first wave near the frame edge and bunch it at the climax.
- A long hold after the climax with only one small thing moving becomes a dead zone; let the background keep drifting (slow push, parallax, soft bokeh glints).
- Sharp star glints on a blurred photo background look fake; use soft bokeh.
- A full-screen cover-up transition held too long reads as a flat flash of colour; keep it to a few frames and keep motion continuous into the first frame.

## Case cards

### 1000 days anniversary: opening the red packet
- **Signature:** the red-packet bubble flips out of the phone into an opening cover, the coin spins faster and faster, the packet tears in two, hundreds of hearts burst across the frame and fly back to spell a giant "1000".
- **Structure:** empty chat close-up, his two messages and the red packet drop in, tap, packet flies out and flips, coin wind-up with a camera push, tear-open climax with a pink world spreading from the packet, hearts assemble into "1000", her reply flies in as small hearts and sends a heartbeat through the number, hold.
- **Technique:** sprites cut by colour difference plus an empty-chat plate; flip around the vertical axis swaps bubble face for cover; split along the seal arc; hearts sampled onto the glyph shape of "1000" and queued left to right on Bezier paths. Modern iPhone drawn in code; screenshot rebuilt onto a 19.5:9 screen.
- **Loop:** the "1000" hearts drift away and one giant heart sweeps up past the lens; while it covers the frame the empty-chat opening appears behind it.
- **Hard part:** the phone. A first flat mock-up and then an older-model phone matched to the screenshot ratio were both rejected; the approved version uses a modern full-screen phone with metal frame, island, reflection and shadow, and re-lays out the screenshot without distortion.

### Weekend picnic chat: watermelon rain
- **Signature:** the moment "I'll bring watermelon" is sent, the camera yanks back and an emoji rain of watermelons bursts out of the phone and fills the frame in three depth layers.
- **Structure:** messages arrive in real order with the camera auto-scrolling; the photo message blurs in, sharpens, then grows behind the phone into a lakeside world; red packet glints; voice note shows an unread dot; send, flash, phone shake, pull-back, rain; the cat sticker reply pops and dances to a beat with floating notes.
- **Technique:** a phone with code-drawn thickness (stacked layers, slight turn); vector watermelon slices so they scale to any size; rain split into far, mid and near layers; background photo kept soft as depth of field because the source photo is small.
- **Loop:** a huge watermelon smashes past the lens; when its flesh covers the frame, cut to the empty-chat opening.
- **Hard part:** the first rain started too far off-screen and felt sparse, so the hit was weak; spawn points moved close to the edge, count raised and timed to the flash. A dead hold after the rain was fixed by ending earlier and adding slow background push, parallax and lake bokeh.
