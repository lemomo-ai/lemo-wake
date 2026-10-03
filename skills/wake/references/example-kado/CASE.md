# Example: a bookshop poster rebuilt as a 5 s build film

Purpose: show what a complete, working implementation looked like (code organisation, beats, camera, texture techniques).
**Do not copy its structure or camera.** It is a build arc with a "close-up to full frame" camera; the next image most likely wants something else.

Source: `index.html`. It predates `lib.js`, so its helpers are inline; new projects should start from the template plus `lib.js`. The rendered film and its assets are not shipped with the skill (5 s, portrait 1080 x 1920), so this `index.html` is for reading only and cannot be rendered as is.

## Reading the image
- Theme: an independent book fair, "a city can be read": paper, print, the city. Mood: literary, forceful, printed texture.
- Lead: a red stamped character plus a paper ribbon floating out of a book.
- Element nature: the big word PRINT = movable type being set; the book = it opens; the ribbon = pulled out, twists and floats; the red character = a stamp that comes down; small text = typed on a typewriter.
- Layers: paper ground, black display type, red character, book, ribbon, circular photo window, small text.
- Dialect: print (patchy ink, registration feel, a highlighted typewriter cursor, paper grain).

## Structure and beats (5 s / 30 fps, portrait 1080 x 1920)
| Time | Event | Camera | Energy |
|---|---|---|---|
| 0-0.45 | Blue layout guide lines draw on | z 2.05, close on the top left | 2 |
| 0.04-1.3 | P R I / N T rise one by one out of masks (`outExpo`) | slow pull to z 1.75 | 3 |
| 0.72-1.75 | The closed book (title and red character on the cover) flies in and lands, the cover opens, three pages turn, the last stops half lifted | follow to the book, z 1.55 | 4 |
| 1.32-2.55 | The ribbon pulls out of the book's gap and twists up to the top right (its texture travels with the paper) | pan up with the ribbon | 4 |
| 2.2-2.8 | **Signature move:** the red character falls from 2.7x scale, blurred, its shadow darkening; impact at 2.55 with scale overshoot, ink spatter and a whole-frame shake | z 1.42, shake | 5 |
| 2.6-4.0 | The vertical title drops in character by character; small text types on; the round window irises open; a blue block wipes in; the date rolls | pull to full frame, z 1.0 | 3 |
| 4.0-4.75 | A light sweep crosses the paper | very slow pull back to 0.985 | 1 |
| 4.75-5 | Hold | | 1 |

## Technical notes
- Display type: Anton glyphs fitted to measured bounding boxes on a 3x canvas with a light ink texture; each letter rises with `translateY` inside its own `overflow: hidden` box.
- Ribbon: a Catmull-Rom centre line, resampled at equal spacing, each segment mapped with two exact triangles. A twist angle `phi(s)` sets the width via its cosine, and the back side is drawn in the paper-back colour. Texture coordinate `u = len - s` makes the content feed out with the paper. The shadow is drawn on a separate canvas with a CSS blur.
- Book: CSS 3D (`rotateZ` / `rotateX` for pose; the right half opens with `rotateY` from -179 to 0 degrees; three leaves turn staggered). A 1 px marker on top of the spine is rendered once and its screen position read back to recover design coordinates, which become the ribbon's start point.
- Photo: the original film substituted a generated black-and-white street scene for the photo in the poster. This skill does not generate images: take such a photo from the source (`L.crop`, with desaturation or a halftone treatment) or draw it in code (a street silhouette, for example).

## Detours
- The first ribbon used parallelogram slices and showed comb-like stripes on curves; switched to triangle mapping.
- Too much twist made the ribbon look like a DNA helix; capped at 0.85 rad.
- Letters were placed by eye and drifted visibly from the source; re-set them from `measure.py` bounds.
- Small text landed on black display letters and vanished; moved letters and reduced the size.
- The first delivery was the source image with local warping on top. It was rejected in favour of taking the poster apart and rebuilding it as one designed piece.
