# Data Charts

Users bring keynote-style 3D or glow charts, flat infographics, dashboards and portrait A4 report pages (consulting-style one-pagers) and want the data itself to perform. Painted educational diagrams with name labels (planets in a row, parts of a plant) sit between this file and `illustration.md`; the latter has a note on them.

## What these images usually contain
- One chart form that already implies a motion: flows (Sankey), fills (donut, gauge), rotation (radial / calendar year), time (stacked area, line), rising and falling (bar series), a grid of days (heatmap).
- A headline KPI or conclusion number (62%, -18%, 4.4x) that is the real "hero" of the page.
- Labels, legends, axis text, small print, and on report pages a title block, subtitle and source line.
- Dark keynote backgrounds with additive glow, glass or reflective floors; or flat paper with very even colour, which makes clean plates easy.
- Often AI-generated: the data can be slightly inconsistent (a Sankey whose bands do not add up, a card date that does not match the bar it describes, grids that are not truly regular).

## What tends to work
- Find the verb the chart already contains and make it literal: energy flung along Sankey ribbons, coffee poured into a glass donut, a radial year dial that actually turns once, a time slider that pushes the whole stack forward, a sun hopping across monthly bars, a gust that blows a year of calendar cells away.
- Start incomplete. Take the chart apart in the opening (reverse-suck the flows, rewind the dial, drop the bands out of frame, blow the cells away) so the main body is the data rebuilding itself. This opening doubles as the loop transition.
- One causal chain across the whole page: source fills, pushes the next stage, the stage fills the next, the KPI lands last. Legends, cards and labels hang off the chain (a colour chip flies into the legend the first time that band appears, a snowflake flies into the coldest-day card).
- A climax that coincides with the data's conclusion: the KPI slams in when the counter reads its final value, the crossover is marked the instant the data actually crosses, the record bar punches out of the dial. Follow it with a shockwave that travels across the marks in arrival order (ribbons plucked like strings, bars bounced, cells flipped like a split-flap board).
- Truthful motion: bar heights, band thickness, pour time per segment and counters all derive from the real values (measured from the image, matched to its labels). Every intermediate frame should be a valid chart state; every counter stops exactly on the printed number.
- Keep the page. Portrait A4 stays portrait, at the source pixel size; header, title and source line can simply be the original pixels while the chart area performs.
- Rebuild vs. reuse: glowing additive marks on black are easy to redraw in code; flat bars, cells and text are best cut from the original as sprites (unmix alpha against the flat paper colour) so the settled frame is pixel-identical. A shader that samples the original by angle or column lets marks "grow" while keeping their exact texture.
- Camera: charts often need little. A tilted 3D stage that straightens as the data flows, a push into the first month that pulls back as the year fills, or a static frame with only a zoom punch and shake at the hit.
- Supporting blocks only where they serve the chain: `pulse` for light running along lines, `pop` for small items, `confetti` rarely. A plain `write` or `pop` sequence on its own is too small for this category.
- Loop: the in-picture take-apart is usually the best join. If it does not fit, `backplay`, `pushcut` into a flat paper area, or a frame-level `reset.py` kind such as `paper`, `flash`, `dissolve`, `mosaic` or `glitch` (for tech-styled dashboards) are options.

## Pitfalls
- Reflowing a portrait report into 16:9 when the user had not asked for another size. It was rejected ("the size is completely different from the original"); the output size is the user's choice, by default the source's own.
- Narrative out of order: the KPI arriving while its counter is only halfway, or the crossover marked at the end instead of when it happens.
- Rolling-digit odometers whose ones digit never stops: halves of two digits stacked, unreadable as stills and blurry in motion. Use integer counts, or roll only near a carry.
- Generic UI rings, ellipse halos and orange geometric bursts at the climax read as cheap overlays or a transition. Prefer shock lines that grow from the subject and reactions in the marks themselves.
- Ghosting on the fade back to the original: code-drawn geometry calibrated to the labels drifts a few pixels from the real pixels, font glyphs differ from the source. Draw shapes from measured pixels, keep calibrated values only for the readouts, switch to original-glyph sprites before settling, and let all aftershocks reach zero before crossfading.
- Additive compositing of crops: dark background pixels get added too and leave rectangles. Convert luminance to alpha first, or put the additive layer on its own canvas with CSS `plus-lighter`.
- Spline cameras overshooting below 1x during holds and exposing edges (`L.Camera` now floors z at 1 by default; a camera of your own needs the same floor), or drifting above 1x so the hold never matches the source; piecewise `L.kf` keyframes are safer. Big push-ins crop the title or labels on a dense page.
- Inpainting large smooth dark backgrounds can hallucinate glints and ghost numbers; a smooth fill (normalized convolution) may be cleaner. Segmentation struggles with glass segments sharing reflections; geometric sectors from measured dividers work.
- Mid-year passages where hundreds of items land per second read only as a wave; give the start, the end and a few data-driven beats (pollution days, the record month) real weight.
- Too many half-transparent items in the air at once turn to mush; make them opaque early.
- The film keeps its output size; `encode.py` never downscales the MP4 or WebP.

## Case cards

### City Energy Flow: Energy Flung Across the Chart
- **Signature:** four source bars charge up and fling glowing ribbons that swell like filling hoses, department bars grow and pass energy on to two tanks; when "useful" reads full, 62% slams into the corner and a shockwave plucks every ribbon.
- **Structure:** original, energy sucked back into the sources, charge, first fling, relay fling, 62% hit, settle into the original.
- **Technique:** ribbons, bars and readouts redrawn in canvas with a travelling wave on the free end that damps once pinned; title and 62% taken from the source with luminance-to-alpha; the whole stage tilted in CSS 3D and straightened by the hit.
- **Loop:** in-picture reverse suction at the start; first and last frames are the original.
- **Hard part:** a first reverse looked like a vertical wipe; it was rebuilt as ribbons actually retracting. The 62% first appeared while the counter was only partway; the hit was moved to land exactly when the value reaches its total. The source Sankey did not add up, so the bands were laid out from the labelled values.

### Annual Coffee Report: Pour It Full
- **Signature:** a stream of coffee falls from the spotlight and fills an empty glass donut segment by segment, percentages counting with the liquid level; the last drop flashes the ring and energy cascades into the KPIs and line chart.
- **Structure:** empty glass ring, four pours in order, splash climax, right-side cascade, hold on the full image, drain.
- **Technique:** the empty glass ring computed from the original (clean plate plus high-pass highlights and rim light); liquid level from a per-segment volume table so fill time is proportional to share; stream curves by fall time; floor reflection mirrors the liquid.
- **Loop:** the liquid drains under gravity and the camera returns, ending on the empty-ring first frame.
- **Hard part:** segmentation could not separate glass segments, so sectors were built from measured dividers. The stream stopped on the wrong segment's surface and crossed labels until fixed; a 3-frame drain was too abrupt and was lengthened.

### 365 Days of One City: A Year in One Turn
- **Signature:** the radial temperature dial turns one full revolution like a record and each day's bar pops out at twelve o'clock; the hottest red bar bursts out of the dial and a wave bounces the whole ring.
- **Structure:** original, whole dial rewinds a turn with bars sucked into the centre, the year refills in one turn, heat hit, inertial overshoot, settle.
- **Technique:** bars are not redrawn; a shader samples the original by angle with a spring growth mask per day, so the end state is pixel-identical; motion blur by sub-sampling the rotation; month labels follow the dial but stay upright.
- **Loop:** in-picture rewind at the start; first frame is the original.
- **Hard part:** labels rotating rigidly were upside-down at the key frame; ticks and labels had to be separated. The card's date did not match the data, so the hit was placed on the longest red bar under the matching month label.

### Wind and Solar Overtake Coal: The Time Slider
- **Signature:** a slider tagged with the year pushes from 2010 to 2030 while the whole stack ahead of it reshapes to that year's data; at the real crossover the headline word "overtake" gets a solar-yellow underline, and the slider hits 2030 with a wave rolling back along the band edges.
- **Structure:** original page, bands fall out of frame, coal rises from below and the other bands shoot in and stack into 2010, slow-fast sweep with a pause at the forecast line, crossover, impact, settle.
- **Technique:** band boundaries measured column by column from the image; readouts calibrated to the printed labels; header kept as original pixels; KPIs redrawn live in a matching thin weight.
- **Loop:** in-picture fall-out at the start; first frame is the original page.
- **Hard part:** the first version reflowed the portrait page into a landscape layout although the user had not asked for another size, and was rejected; the approved version keeps the original portrait canvas with the same action. The fade back then ghosted until geometry used measured pixels and settled text used original-glyph sprites.

### An Island's Four Seasons: The Sun Hops Through a Year
- **Signature:** a sun pops out of the decimal point in "4.4", hops month by month onto bars that rise to catch it, lands hardest on August's peak, then dives back between the two 4s and shrinks into the decimal point again.
- **Structure:** full page, bars sink back December to January, twelve hops with a heavy August hit, dive back into the KPI, hold.
- **Technique:** plate made by painting the flat paper colour over bars and numbers; bars are stretched crops of the original; hop arcs follow the data so summer hops are highest.
- **Loop:** the take-apart plays at the start and the sun returns to the same decimal point; first frame equals last.
- **Hard part:** an ellipse shock ring looked like cheap UI and was replaced with thin rays from the landing point; a spinning odometer for the running total became integer counts; the sun covered the 4s until they were made to squeeze apart.

### A Year of Clean Air: A Gust Blows the Year Away
- **Signature:** a gust peels all 365 day cells, the KPI and legend off the page; days fall back one by one in date order, heavy-pollution days fall harder and puff coloured smoke that shoves neighbours; then -18% slams down and a split-flap wave flips the year.
- **Structure:** full page, wind, blank calendar, days return (slow January, fast midyear, slow December), KPI hit, flip wave, hold.
- **Technique:** every day cell cut from the original by connected components and ordered by date (validated against weekdays); text unmixed from the white paper as transparent sprites.
- **Loop:** the gust plays at the start; first frame is the finished page.
- **Hard part:** rectangular crops carried white cards over the title; falling cells were translucent mush; flipping around the vertical axis showed blank backs, so the flip moved to the horizontal axis like a flap board.
