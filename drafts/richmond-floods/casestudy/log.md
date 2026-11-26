# Richmond's floods over time: case-study log

The running record of how this series was made: what was asked, what was shown, what was
decided, dead ends, fixes and timings. One dated, numbered folder per step sits beside this
file. Board entry: `series-richmond-floods`. Times are Eastern.

## 2026-11-23

### 01. The brief and a first plan (18:13 to 18:24) · `2026-11-23-01-brief-and-first-plan/`

- **18:13, Chris:** "New series to plan: Richmond's Floods Over Time. Pre/post flood wall. Show
  how much was submerged. Wasn't there a flood that the flood wall trapped water on the wrong
  side? This should expand our core capabilities into the meteorological."
- **Planning session (Claude Fable 5.2):** three web searches, then a first plan in chat
  (`first-plan.md`, with the sources used). The flood Chris remembered is Tropical Storm
  Gaston, August 30, 2004. First caution recorded: news reports blame the drainage system;
  whether the wall itself held water in is not yet sourced.
- Two technical risks named at the start: the two gauges (Westham and City Locks) report
  different crest numbers for one flood, and a flood surface slopes through the falls.
- Three questions put to Chris: which floods, map set or story or both, start research now.
- **18:14, Chris:** "Go hard at this. I think this could be a real big one that resonates with
  a lot of people so let's invest time and effort here." **18:15:** "But yet, Op. 55 sub
  agents to be economical". Taken as yes to the three recommendations (about five floods to
  start, both a set and a story, research now); said so to Chris.
- **18:16:** three Opus 5.5 subagents started in parallel (briefs in `briefs.md`):
  river floods and the floodwall; Gaston and the weather data; a drawing spike on branch
  `feature/flood-surface`.
- **18:24, Chris:** "Be sure to track all this work for your future case study with images".
  This log and folder started; every later step saves its renders, charts and source
  pictures-of-record here, each round to a new file.
- No images yet at this step: nothing has been drawn.

### 02. Research: river floods and the floodwall (18:16 to 18:48) · `2026-11-23-02-research-river-floods-and-the-wall/`

- Opus 5.5 subagent, 32 minutes, 183 tool uses, about 350,000 tokens. Files: floods.md and
  floods.json (24 floods), datums.md, floodwall.md, before-the-wall.md, open-data.md, SUMMARY.md.
- **The finding that makes the series drawable:** below Mayo Bridge a flood is nearly level,
  so one surveyed elevation per flood serves Shockoe, Manchester, Rocketts and Fulton. Agnes
  is 35.5 ft NAVD88 by three independent routes.
- **The finding that limits it:** above the bridge the surface climbs about 40 ft through the
  falls and only three floods have surveyed profiles.
- **The trap found:** the City Locks gauge has had three different zeros; its published
  crests are not comparable without conversion.
- Best single source: USGS Hydrologic Atlas HA-410 (Camille's mapped extent and profiles).
- Dead ends: FEMA's servers, Overpass and the National Levee Database could not be reached.
- No images at this step. Raw source copies (303 MB) are outside git; see SUMMARY.md.
- Not yet done: a second reader checking the numbers against the sources.

- **18:50, Chris: "Yes 1-3"** to: (1) draw 1771 as a clearly labeled estimate; (2) make an
  "Agnes against today's wall" plate; (3) download the City's flood insurance study from FEMA
  on the Mac. Question 4 (asking the Corps for its depth grids and design record) not
  answered; no request sent.
- **18:54:** FEMA's Map Service Center reached from the Mac. Flood Insurance Study reports for
  the City of Richmond (community 510129) downloaded: 510129V000C (effective July 8, 2025,
  134 pages, 16 MB) and 510129V000 (July 20, 1998, 48 pages, 7 MB). Kept on the Mac in
  `ISO-TEST/isoscape-work/richmond-floods/sources/fema-fis/` (over 5 MB, outside git).
- **18:56:** a fourth Opus 5.5 subagent started: extract the flood profiles and the levee
  text from both reports, and act as second reader on every number in step 02.

### 03. Research: Gaston and the weather data (18:16 to about 19:10) · `2026-11-23-03-research-gaston-and-the-weather/`

- Opus 5.5 subagent. Files: gaston-timeline.md, gaston-mechanism.md, gaston-water.md,
  rainfall-data.md, other-pluvial.md, sources.md, SUMMARY.md.
- **The answer to Chris's question:** partly. The flood was rain, the James was low, and the
  floodwall's gates were open the whole time. The Bottom is a bowl whose river side (Dock
  Street, railroad embankments, the wall) is higher than its lowest streets, so water the
  sewers could not take had to pond. Nothing measures the wall's own share of that.
- **What this does to the drawing:** the spike's Gaston render (a crisp pool at one chosen
  level) is the very thing the research warns against. Gaston should be depths at named
  places and a soft pool, with the gates drawn open.
- **A test we can run ourselves:** the lowest overland spill route from 17th and Main to the
  river on the lidar, with and without the wall. Started as step 15.
- No images at this step.

### 04. The FEMA flood profiles and a second read of the river numbers (18:56 to about 20:05) · `2026-11-23-04-fema-profiles-and-second-read/`

- Opus 5.5 subagent; the cloud workspace restarted partway and it resumed from its files.
  Files: fis.md, fis.json, second-read.md, levels.json, the reading scripts, and `evidence/`
  (eight rasterized pages from the two FEMA reports and USGS HA-410: the first images of
  record for this series' sources).
- **The drawing levels are settled** (ft NAVD88 at the City Locks): Agnes 35.5 ±0.3; November
  1985 29.7 ±0.4; Camille 27.6 ±0.2; March 1936 26.5 ±0.4; Fran 1996 22.7 (+1.0, one-sided);
  November 2020 17.0 ±0.1; 1771 38.0 ±3. The spike's placeholders (10.8, 9.0, 8.4 m) were
  within 0.05 m of the checked values for Agnes, 1985 and Camille.
- **A dead end worth knowing:** FEMA's 1% flood at the Locks (36.9 ft) is 1.4 ft above Agnes
  although Agnes carried more water. The FEMA profiles cannot stand in for historic floods
  downtown; they run 2 to 5 ft above observed floods on the tidal reach.
- **Eight corrections to step 02**, the main ones: the City Locks datum for 2007 to 2010 is
  resolved (NAVD88 from October 1, 2007); 1969 at the Boulevard Bridge is 83.8 ft NGVD29, not
  84.9; the "$153 million" attaches to the protected property, not the wall, and its meaning
  is unconfirmed. Everything else checked was confirmed.
- **Still not found anywhere:** the wall's top elevation, its design flood with a datum, and
  the positions and sills of its closures. Neither FEMA report prints them.
- **A cross-check nobody planned:** FEMA's Shockoe Creek model puts the 1% level near Dock
  Street at 19.4 ft NAVD88. Our lidar spill test (step 15) put the bowl's natural spill level
  at 19.1 ft. Two unrelated methods, 0.3 ft apart.
- The 3DEP terrain's vertical datum is confirmed as NAVD88.

### The gate: worth pursuing (20:03)

- **Chris:** "Yes worth it and your reccs. I will not be engaging 3rd parties offline for this
  at this time". The series passes from rough draft to working draft.
- Decided, on the planning session's recommendations: each flood is drawn on the city of its
  own year; the flood series is drawn at 1x terrain; Gaston is drawn as depths at named
  places with a soft pool, gates open, with no single surveyed-looking level; one neutral
  sentence on the 2009 lawsuit; a radar-based rain map for the Shockoe valley.
- **No outside requests:** nothing goes to the Corps, the city or the court. The wall's top
  elevation, its openings' sills and the two city engineering studies stay unknown, and the
  series says so where it matters. Public sources only.
- **20:10:** two Opus 5.5 subagents started: working draft d1 of the drawing (real levels,
  the city of each year, color and wall round two) on `feature/flood-surface`; and the
  radar rain map (steps numbered from 30).

### Drawing spike (Opus 5.5 subagent)

Branch `feature/flood-surface`, worktree `wt-floods`. Every picture below was looked at; all
levels in them are placeholders from the brief, not researched values, and each render says
"ROUGH TEST, placeholder levels" in its caption. Times Eastern.

#### 10. First fill (18:17 to 18:27) · `2026-11-23-10-spike-first-fill/`

- Read CLAUDE.md, the README, `terrain.ts`, `paintStrip` in `render.ts` and the building and
  bridge code in `scene.ts`. The downtown terrain cache is here: `richmond-downtown-time` reads
  `data/richmond-i195-rocketts/dem.bin.gz` (3DEP at 2 m), which covers Shockoe Bottom, Mayo
  Island and Manchester. New test region `regions/richmond-floods.json`, the downtown-time frame
  moved to take in Rocketts, with no `time` section.
- Datum: the code does not record a vertical datum. The cached grid is 3DEP; USGS documents
  its seamless DEM as NAVD88 in the continental US (not checked in this spike). Sampled
  ground: 17th and Main 5.9 m, Dock and Pear 6.4 m, the river at Rocketts -0.1 m.
- OSM in the cache has the floodwall: 11 ways tagged `barrier=wall`, `wall=flood_wall`, on
  both banks. The 2 m lidar does not give its top reliably (crest readings 6.7 to 13.8 m).
- Built `src/flood.ts` (bathtub fill from the river on the 5 m grid, walls as blocked grid
  links, ponds, a sloped surface by distance along control points), the drawing in
  `paintStrip`, buildings that start at the water, counts in `info`. First build 17 s
  including the PNG.
- `agnes-10.8m-nowall-r1.png`: the flood reads apart from the river (muddy tones by depth,
  the river's channel kept blue) and buildings stand in it. But pale lines cross all the water
  every strip (`bug-pale-lines-every-strip-x3.png`, and at 20x in the SVG,
  `bug-pale-lines-svg-zoom-x20.png`).
- `agnes-10.8m-wall-r1.png`: with the wall the flooded area was the same (180 ha): the wall
  did not hold anywhere.

#### 11. Strip seams (18:27 to 18:30) · `2026-11-23-11-strip-seams/`

- Tried lapping the flood's top row 0.6 m away from the camera: the lines only moved
  (`try-lap-far-lines-move-x20.png`). Cause: the three depth bands and the channel were
  stacked, and each layer's antialiased far edge let the one under it through. Fix: the layers
  are cut so they never overlap (each band from its depth to the next band's, off the
  channel), one coverage per pixel per strip. `fixed-exclusive-layers-x3.png`, `-x20.png`:
  gone.

#### 12. Wall leaks (18:30 to 18:34) · `2026-11-23-12-wall-leaks/`

- Debug plots of the grid (flooded, river, wall lines; ends circled), `mask-wall*.png`, and
  of ground above the wall's top in yellow, `high.png`.
- Leak 1, `mask-wall.png`: the walls end in low ground and the water goes round. Added four
  short tie-in lines marked APPROXIMATE in the region file (from each mapped end to ground
  above the placeholder top, read off the grid, two run past the frame): `mask-wall2.png`,
  no change.
- Leak 2: every open water node was a source, including a pond behind the Manchester wall.
  Now only the largest body of water is: `mask-wall3.png`, Manchester holds.
- Leak 3: a canal behind the north wall is joined to the river round the wall's end, so it
  was still a source. The largest body is now found without crossing a wall:
  `mask-wall4.png`, no change yet.
- Leak 4: a path-tracing script found the water passing through a 1.4 m gap between the
  mapped wall's end and my tie-in (rounded coordinates). Wall ends within 5 m of another wall
  are now joined: `mask-wall5.png`, Shockoe and Manchester dry. 547 grid links held, flooded
  area 180 to 84 ha. `agnes-wall-r2-holds-bridges-hidden.png`.

#### 13. Exaggeration (18:34 to 18:40) · `2026-11-23-13-exaggeration/`

- With the house terrain exaggeration (2.5x), the water stands at its exaggerated elevation
  while buildings and bridge clearances are true: 5 m of water hid 12.5 m of wall. Agnes
  "submerged" 136 buildings and 189 deck spans (`agnes-x2.5-136-submerged-bridges-hidden.png`);
  the river's bridges vanished.
- Same frame with the terrain not exaggerated (`regions/richmond-floods-x1.json`):
  6 buildings topped, and the buildings read as standing in water
  (`agnes-x1.0-6-submerged.png`). Recommendation for the series: draw flood views at 1x.
- Decks are now always drawn, awash, and counted (most deck heights are rules, not measured).
- Also saved: Gaston pond, a sloped Agnes surface, Juan and Camille at 2.5x (first rounds).

#### 14. Final round (18:40 to 18:55) · `2026-11-23-14-final-round/`

- The wall was too pale to find (`crop-north-wall-pale-r1-x3.png`); darkened it
  (`crop-north-wall-darker-r2-x3.png`). At the full view it is still a hairline.
- Final set at 1x: no flood, Agnes with and without the wall, Gaston, sloped Agnes, Juan,
  Camille, plus Agnes at 2.5x for comparison, and crops (Manchester's buildings and tanks
  standing in water; the wall holding; Gaston in Shockoe; the strip outside the wall
  downstream, which floods).
- Checks: no-flood builds of `richmond-downtown-topo`, `richmond-downtown-time`,
  `richmond-i195-rocketts` and `richmond-floods` are byte for byte the same as main's.
  `npm test` 274 pass, typecheck clean, `npm run check:visual`: five views identical or
  within tolerance (0.000% changed), two skipped for missing cache, none failed.
- Builds: 5 to 7 s for the SVG, about 17 s with the 3400 px PNG.
- Counts (placeholder levels, 1x; area is off the river's own channel):

  | Test | Flooded | Buildings in water | Topped | Depth at buildings, max / median | Decks awash |
  |---|---|---|---|---|---|
  | Agnes 10.8 m, no wall | 180.2 ha (445 ac) | 319 | 6 | 9.76 / 3.50 m | 155 |
  | Agnes 10.8 m, wall (top 12.5 m) | 84.2 ha (208 ac) | 32 | 3 | 9.76 / 3.74 m | 106 |
  | Agnes sloped 11.6 to 10.6 m | 184.2 ha (455 ac) | 327 | 8 | 10.13 / 3.64 m | 159 |
  | Juan 9.0 m, no wall | 149.7 ha (370 ac) | 245 | 5 | 7.96 / 2.41 m | 97 |
  | Camille 8.4 m, no wall | 133.8 ha (331 ac) | 218 | 3 | 7.36 / 1.94 m | 36 |
  | Gaston, pond at 8.9 m | 15.0 ha (37 ac) | 116 | 2 | 4.37 / 1.90 m | 0 |

#### 15. The spill-path test (18:58 to 19:08) · `2026-11-23-15-spill-path/`

Asked by the coordinator after step 03: is Shockoe Bottom a bowl, at what water level does it
spill to the James, and does the floodwall raise that level? Gates open, as in 2004.

- **Data used:** the cached 3DEP grid itself (`data/richmond-i195-rocketts/dem.bin.gz`, 2 m
  cells, as isoscape reads it, not blurred), cut to a window by `tools/floods/export-dem.ts`.
  The analysis is `tools/floods/spill.py` (a rising pool: cells taken in order of the highest
  ground on the lowest path from the low point), `sections.py`, `outlet.py`, `charts.py`.
  Numbers in `spill.json` and `outlet.json`.
- **Exploring:** `explore-1-orientation-hillshade.png`, `explore-2-bowl-contours-1m.png`.
  A first run started in the canal's end basin (1.6 m) and was wrong; the low point is now
  searched only in the blocks north of Cary Street. The canal (lidar 5.3 m) and the Dock
  (4.6 m) are held water above the tide, so they are not "the James": the pool may fill them.
  The James is the largest body of ground the lidar puts below 1.2 m.
  `explore-3-first-route-and-profile.png` is the first route found.
- **Low point:** 4.07 m (13.4 ft) NAVD88 at 37.53337, -77.42930, a pit beside the 17th Street
  Market; the street lows around it are about 5.0 m (16.4 ft). 17th and Main reads 6.60 m
  (21.6 ft), matching the research's 21.7 ft.
- **Cross-sections** (`sections-all.png`, `section-A` to `-E`): the floodwall barely shows. At
  2 m the thin wall is smoothed to a bump of a few tenths of a meter or nothing, so the lidar
  as cached does not see it. The CSX viaduct and I-95 read as open ground beneath (bare earth
  drops the decks). The riverfront strip between the Bottom and the Dock is only about 5.8 to
  6.7 m from 17th to 20th Street; at 15th Street it rises to 8 to 9 m.
- **Spill levels** (pool rising from the low point until it first reaches the James):
  - (a) lidar as is: **5.81 m (19.1 ft)**. Saddle at 37.53152, -77.43050, at 17th and Dock,
    where the canal's end basin meets the wall's V; the route then reaches tidal water by the
    Dock's head (37.53093, -77.43094). Pool 2.15 ha, about 9,800 m³. 17th and Main dry.
  - (b) wall standing, its openings open at street grade: the OSM wall ways burned in at the
    placeholder top (12.5 m), the gaps between them left open (Dock Street with the
    Peninsula Subdivision rail bridge by 18th Street, 10.6 m; South 14th Street, 16.9 m; the
    Richmond District rail by 14th, 10.6 m; East Byrd Street, 9.3 m): **6.62 m (21.7 ft)**,
    through the Dock Street opening by 18th Street (saddle 37.53127, -77.42808). Pool 10.1 ha,
    about 77,500 m³. 17th and Main 0.02 m deep, the 17th Street Market point 0.63 m.
  - (c) wall removed (ground rebuilt across 4 m either side of its line): 5.82 m (19.1 ft),
    the same as (a), because the lidar does not see the wall.
  - (d) wall and the riverfront railroad embankments removed: 5.91 m (19.4 ft). Taking the
    rail fill away does not lower it (the rebuilt ground there came out a little higher).
  - (e) hypothetical, every gate shut (not 2004): the pool would rise to the wall's
    placeholder top, 12.5 m, and spill round the west end by East Byrd Street.
- **The answer:** with the gates open, the wall as mapped raises the spill level by about
  0.8 m (2.7 ft), from 5.8 to 6.6 m, and only if OSM's gaps are the openings and the lidar's
  ground in them is their sill. Both levels are far below every reported Gaston surface
  (24 to 35 ft, 7.3 to 10.7 m): "up to 10 ft" at the low point (27 to 28 ft) is 1.6 to 2.7 m
  above them, Bottoms Up (30 to 31 ft), Havana '59 (34 to 35 ft) and the law office (24 to
  29 ft) higher still. None is consistent with water standing still behind the terrain; every
  report needs water above the spill level, that is, water flowing out over the riverfront
  faster than any static pool, or barriers the lidar does not show.
- **An order-of-magnitude look** (`outlet-weir-order-of-magnitude.png`; broad-crested weir
  over the riverfront line): to pass the research's rough runoff estimate (170 to 310 m³/s,
  6,000 to 11,000 cfs), the pool would stand at 6.9 to 7.2 m (23 to 24 ft) with the line
  open along its 1.2 km, and at 9.9 to 10.8 m (32 to 35 ft) with only the wall's four
  openings open. The reported levels fall between. So if the wall mattered, it would be by
  narrowing the way out, not by raising the sill. This ignores the sewers, the Dock's level,
  the approach and every opening's real width and sill: a reason to model it, not a finding.
- **Pictures:** `plan-spill-routes.png`, `stage-area-volume.png`, the sections, and an
  isoscape render of the pool at the lidar's spill level (`render-pool-at-spill-level-x1.png`
  and its crop), captioned "ROUGH TEST: the pool at the terrain's spill level, not an
  observed flood", with the wall not drawn. The render fills on isoscape's blurred 5 m grid
  (2.1 ha against the 2 m analysis's 2.15 ha), using a new pond option, `from`: only the pool
  connected to a low point.
- **What would settle it:** the wall's surveyed top and its closures' locations, widths and
  sills (the Corps' as-builts or O&M manual); the 1 m lidar or point cloud, where the wall
  shows; what the canal's end at 17th and Dock is (open channel or closure); sewer outfall
  capacities; and a 2D hydraulic model of the storm (or the 2022 Greeley and Hansen study).

#### 16. The flood's color (19:08 to 19:10) · `2026-11-23-16-flood-color/`

- Same Agnes view at 1x, with `--flood-style` looks laid over the palette: now (three muddy
  bands), `silt` (five lighter bands), `ripple` (muddy with surface strokes, more where deep),
  `murk` (tinted blue-brown), and `silt` with `ripple`. `compare-full.png`,
  `compare-crop-shockoe.png`, `compare-crop-manchester.png`.
- What I saw: `silt` hardly changes the picture, because most of Agnes is over 3 m deep and
  so in the darkest band; the gradient shows only at the edges. `murk` reads as water but
  also as woods or marsh beside the parks' greens. `ripple` reads most as a water surface,
  and keeps the river's blue apart. My pick: `ripple`, maybe with `silt`'s lighter edges.

#### 17. The wall as a subject (19:10 to 19:13) · `2026-11-23-17-wall-as-subject/`

- Agnes with the wall at 1x: as drawn now, `wall-bold` (dark face, pale top, a 1.4-unit ink
  line, 2.5 m thick) and `wall-strong` (the same with a 4-unit brick-red line).
  `compare-full.png`, `compare-crop-north-bank.png`.
- What I saw: now, the wall is invisible at full view. `wall-bold` shows close up only.
  `wall-strong` traces both walls at full view. My pick: `wall-strong`. The red is a choice
  to check against the series' other marks.

### Working draft d1 (Opus 5.5 subagent, 20:05 to 20:50)

After the gate. The owner's decisions: each flood on the city of its own year, 1x terrain, Gaston
as depths at places and a soft pool with the gates open, 1771 as a labeled estimate, an "Agnes
against today's wall" plate, public sources only. Levels from the checked `levels.json` (step 04).

#### 20. A correction to step 15 · `2026-11-23-20-spill-probes-corrected/`

- The coordinates I used for "17th and Main" in step 15 came from the research's spot checks
  and are about 200 m off: they lie near 15th Street. Taken from OSM's street geometry, 17th
  and Main is 37.53343, -77.42853. Its ground reads 6.58 m (21.6 ft), nearly the same as before
  (6.60 m) by chance. The 17th Street Market, at the middle of OSM's outline, reads 5.84 m
  (19.2 ft), not 5.99 m.
- The spill levels, saddles and the answer do not change. In case (b), 17th and Main gets
  0.04 m (it was 0.02 m) and the market gets 0.78 m (it was 0.63 m). Redrawn as
  `plan-spill-routes-r2.png` and `stage-area-volume-r2.png`, with `spill.json` re-run.

#### 21. The frame · `2026-11-23-21-frames/`

- Three frames over the tidal reach, at 1x, with Agnes on the 1972 city: A, bearing −8.7
  (the house bearing, from Manchester); B, bearing 25 (up the Shockoe valley); C, bearing −65
  (upriver from Rocketts). `frames-A-B-C.png` and one picture per frame, with each frame's
  region file.
- **Pick: B.** The valley opens into the picture, the riverfront and the wall line run across
  its middle, and Mayo Island, the Dock and Rocketts are all in it. A shows more of Manchester,
  but Manchester is nearly empty in past years (below). C reads well but puts the Bottom at the
  side.
- Kept inside the year-built parcels (south to 37.5204) and the cached elevation. Fulton and
  Gillies Creek do not fit: the parcels stop at −77.4056.

#### 22. Color, round two · `2026-11-23-22-color-round-two/`

- Five new looks, against round one on the same 1972 Agnes: `pale-silt`, `silt-sheen`,
  `blue-silt`, `grey-tan` and `ochre-wash`. Each has nine fine bands (0, 0.3, 0.6, 1, 1.5, 2, 3,
  4 and 6 m) on an eased ramp, a pale waterline and the river's channel in its own blue.
  `compare-full.png`, `compare-crop-shockoe.png`.
- What I saw: every new look reads as water, not mud, and the fine bands read as a depth
  gradient with soft contours.
  - `blue-silt` reads most as water, but its deep water is darker than the river, so "where the
    river went" looks deeper than the river itself.
  - `grey-tan` reads as fog or concrete.
  - `ochre-wash` reads as mud again.
  - `silt-sheen`'s glints read as grass at full view.
- **Pick: `pale-silt`**: siltier and paler, its depth carried by a smooth gradient, with a
  clean pale edge, and the river still apart.

#### 23. The wall, round two · `2026-11-23-23-wall-round-two/`

- `wall-cased`: a pale casing under a dark line. Too quiet at full view.
- `wall-cased-red`, round 1: the brick-red line was too thin under its casing.
- `wall-cased-red`, round 2: each 8 m piece's round-capped casing covered its neighbor's line,
  so the line read as a red and white dashed edge (`wall-crop2.png`).
- `wall-cased-red`, round 3: square ends, so the line is continuous (`wall-crop3.png`). It
  reads at full view and close up, with a label, "Floodwall (1994)", set on each wall line
  that runs 300 m or more in the frame.
- **Pick: `wall-cased-red`** (casing plus a 3.6-unit brick-red line, 2 m thick, a darker face).
  Shut openings are drawn in ink; open ones as a dashed line across the gap.

#### 24. The plates, round one · `2026-11-23-24-plates-round-one/`

- `regions/richmond-floods-d1.json` is written by `tools/floods/make_region.py` from
  `levels.json`. Each level is held downstream of the Locks, ramps to its Mayo Bridge value,
  and is held at that value west of the bridge, except where the file has marks there (Camille,
  1936).
- New code:
  - walls dated by `from` (the floodwall, 1994);
  - gates open or shut;
  - an estimate's range drawn as a pale band (two tries for 1771: `beyond` and `range`);
  - soft pools;
  - numbered markers keyed in the caption;
  - caption lines that take the build's own counts;
  - `floodStyles` on the region.
- Round one's captions ran off the plate (`contact-r1-captions-overflow.png`); they are now
  wrapped to the plate's width. The 1771 band reads as a pale grey margin with a dashed edge;
  `range` widens it.
- Gaston A (a soft pool to about 28 ft) and Gaston B (water to 25 ft drawn soft, plus a pale
  band to 31 ft) both read. `coverage-by-area.json` says where each year's buildings come from
  (`tools/floods/coverage.ts`).

#### 25. The plates, round two · `2026-11-23-25-plates-round-two/`

- The captions wrap. Looked at close: Fran against the wall, Agnes against today's wall, 1936
  and 1972 in Shockoe.

#### 26. The plates, d1 · `2026-11-23-26-plates-d1/`

- **Plates:** 1771 (two tries), 1936, 1969, 1972, 1985, 1996 with the wall, 2020 with the
  wall, Agnes against today's wall, and Gaston A and B. Also the contact sheet and the crops.
- **Gaston fix:** the dashed marks across the open gates were drawn on the ground under the
  water and the pool covered them; now they lie on the water (`gaston-gate-*`).
- **Counts** (`drafts/richmond-floods/counts.json`; "of the buildings this view shows"):

  | Plate | City | Level, ft NAVD88 at the Locks | Acres off the channel | Buildings shown | In water | Depth at buildings, median / max ft | Without the wall |
  |---|---|---|---|---|---|---|---|
  | 1771 | 1788 | 38.0 ±3 | 346.9 | 7 | 1 | 3.7 / 3.7 | |
  | 1936 | 1936 | 26.5 ±0.4 | 258.0 | 1,051 | 49 | 5.5 / 24.2 | |
  | Camille | 1969 | 27.6 ±0.2 | 276.0 | 1,114 | 60 | 6.0 / 27.5 | |
  | Agnes | 1972 | 35.5 ±0.3 | 335.6 | 1,119 | 89 | 11.0 / 33.3 | |
  | 1985 | 1985 | 29.7 ±0.4 | 299.5 | 1,154 | 74 | 7.1 / 27.5 | |
  | Fran, wall | 1996 | 22.7 (+1.0) | 143.6 | 1,180 | 1 | 20.5 / 20.5 | 205.6 acres, 43 in water |
  | 2020, wall | 2020 | 17.0 ±0.1 | 72.9 | 1,289 | 1 | 13.5 / 13.5 | 73.9 acres, 1 |
  | Agnes vs today's wall | 2026 | 35.5 ±0.3 | 194.7 | 1,877 | 31 | 13.4 / 33.3 | 322.5 acres, 216 |
  | Gaston A | 2004 | about 28 ±3 (reports) | 34.8 | 1,197 | 62 | 6.1 / 13.1 | |

### d1, round two (Opus 5.5 subagent, 2026-11-24)

The owner's notes on d1. First, never say "the river" when the water level is meant. Second,
the brown and the grey lack contrast against the ground.

- **27:** decision sheet for the owner, period city vs today's city; r2 reworded after his note.
- **28. Contrast candidates** · `2026-11-24-28-contrast-candidates/`. Five looks plus d1's
  `pale-silt`, measured in L* (`lstar.json`), then compared at full view, in crops and at
  600 px:

  | Look | Water edge vs ground ΔL* | ΔE | Deepest vs river ΔL* | Hatch vs ground ΔL* |
  |---|---|---|---|---|
  | pale-silt (d1) | −0.7 | 0.8 | 17.5 | (flat grey) |
  | umber | 28.4 | 30.4 | 51.5 | 38.8 |
  | green-brown | 25.8 | 28.9 | 44.7 | 36.1 |
  | blue-grey | 24.5 | 31.0 | 44.8 | 36.1 |
  | ochre | 22.3 | 41.5 | 40.1 | 30.8 |
  | knockback (ground paler) | 24.8 | 30.2 | 40.0 | 35.9 |

  The measurement confirms the owner's note: d1's shallow water was the same lightness as the
  ground (ΔL* −0.7). The range band is now hatched in the flood's hue over a light tint, with a
  dashed edge, replacing the flat pale grey.
- **29. Pick: `blue-grey`** · `2026-11-24-29-pick-blue-grey-streets/`.
  - Why: it reads as water at thumbnail size, and its hue is apart from the tan ground. The
    river's own channel is a lighter, more saturated blue on the flood, so it stays apart.
  - `umber` and `green-brown` read heavy, `ochre` reads as mud, and `knockback` washes out the
    city.
  - Added: streets laid on the water at half strength, so the street grid reads under it.
- **30. Plates, d1r2** · `2026-11-24-30-plates-d1r2/`. All plates re-rendered with the pick.
  - Captions cut to three lines: level and source; counts; what the picture cannot claim.
  - "The river at X ft" became "Water at X ft"; the what-if plate is now "the 1972 flood's
    height against today's floodwall".
  - Gaston pins 1 and 2 set to either side; the wall label kept off water (river or flood).
  - Counts are unchanged (`counts.json` re-run).

### d1, round three: the water's height on the buildings (Opus 5.5 subagent, 2026-11-24)

The owner asked whether the water is shown rising up the buildings. Before this round, no: the
water plane stood at the flood's height and the walls started at it, so a building in 11 ft of
water looked only a little shorter. Test plate: Agnes 1972.

- **Heights:** the flooded buildings this view shows have a median height of 28 ft (true at
  1x), against an 11 ft median depth, so about two-fifths of a typical wall is under water.
  Only 2 of the 89 buildings in water are under 20 ft tall, and 1 is topped. Single-story
  buildings do not vanish.
- **31. Tries** · `2026-11-24-31-water-on-the-walls-tries/`
  - See-through water at 70% and 50%: walls reach the ground, tinted below the surface, with a
    waterline. Close up (`tries-close-x4.png`) it works: the tinted band on each wall is the
    depth. At plate view the water turns pale and grey, losing the dark blue the owner chose,
    and the strips meet edge to edge, so faint pale lines cross the water every 10 m. At 85% it
    keeps the blue, but the seams still show (`aquarium-85-mid-view-strip-seams.png`).
    Not kept. Removing the seams needs the water painted once rather than per strip, which is
    more than a quick round.
  - Tide mark: a band above the surface as tall as the depth. It reads, but it puts the mark
    above the water, where none was. It misleads, so it is not kept.
  - Staff gauges at 17th and Main, Main Street Station and 17th and Dock: a post at true
    height, ticked every 5 ft, with the depth figure above it. The post is about 6 px at plate
    view; the figure carries the meaning. The depths (15, 11 and 19 ft) come from the 5 m grid;
    the 2 m lidar gives 17th and Main about 14 ft.
  - A dry plate, pixel-aligned (`1972-dry`: the same captions, the water below all ground), for
    the compare divider.
  - Not tried: a section strip along one street, as `src/section.ts` draws for cutaways. It
    would be the truest picture of depth against building height.
- **32. Pick** · `2026-11-24-32-pick-gauges-and-dry-pair/`: the opaque dark blue-grey,
  staff gauges and the dry pair. Applied to Agnes 1972 and to the 1972 height against today's
  wall. That plate shows no gauges, because its gauge places are dry behind the wall.

### d1, round four: x-ray walls (Opus 5.5 subagent, 2026-11-24)

- **33. Tries** · `2026-11-24-33-xray-walls-tries/`. The water stays opaque in the owner's
  blue-grey. Each wall standing in water also gets its part under the surface drawn over the
  water: a band in the wall's tone taken toward the flood's mid tone, a dark waterline along its
  top and a light line at its foot. It is painted once the strips nearer than the building (by
  the depth times cos(tilt)/squash, plus 1 m) are done. Variants: band, fade (the lower half
  nearer the water) and band with a heavier waterline. Compared at x4 with d1r3's opaque and
  70% see-through crops (`compare-close.png`), at mid view (`compare-mid.png`) and at 600 px
  (`compare-thumb.png`).
  - **Close up** it reads as the wall going on under the water: no seams, and the blue stays.
  - **Mid view:** a pale skirt under each building; it reads at least as much as a reflection
    or a shadow as it does as a submerged wall. Fade looks more like a reflection; the heavy
    waterline helps it read as a line on the wall.
  - **600 px:** nothing shows. At plate scale, 11 ft is about 6 px.
  - Risk: a nearer building painted before the band is crossed by it. I saw none in the crops,
    but I did not check every one.
- **34. Applied** · `2026-11-24-34-xray-walls-applied/`: `xray-heavy` (band plus 2.4-unit
  waterline) on Agnes 1972, its dry pair and the 1972 height against today's wall.
  - Gauge figures are set smaller, beside their posts.
  - The today's-wall plate has two riverward gauges: Mayo Island, 9 ft, and Great Shiplock
    Park, 24 ft. The first try at Mayo Island landed in the channel and read 33 to 34 ft; it was
    moved onto the island.

## 2026-11-24

### Chris reviews d1 (08:39 to 10:04)

The renders for each round are in the spike branch's step folders 27 to 34.

- **08:39, Chris:** "show me what I need to make the d1 decision". A decision sheet made (step
  27): the 1972 flood on the 1972 city as recorded, on today's city, and 1936 as a traced year.
- **08:44, Chris, revision 1:** "Why does B say, 'The same river on today's city...' ...the
  James River has been there always?" The planning session's wording was wrong: it said
  "river" for "water level". Fixed on the sheet and in every plate title and caption.
- **08:45, Chris, revision 2:** "The brown isn't showing enough contrast, doubly so the grey".
  Measured: d1's shallow water was the same lightness as the ground (0.7 L* lighter). Six
  candidates tried; blue-grey picked (24.5 L* darker than land at the edge); the grey range
  band replaced by a hatch in the flood color.
- **09:11, Chris:** "I like the dark blue." Locked as the series color. Then: "are we also
  raising the level of the blue (water) 'up' the buildings to show the height of the water
  against the buildings?" Honest answer: geometrically yes, visibly no.
- Rounds three and four: see-through water (right close up, fails at plate view: greys the
  blue, shows the 10 m paint bands); a tide mark (misleads, dropped); depth gauges with
  figures at named places (kept); a pixel-aligned dry twin of the plate for a compare
  divider (kept); submerged walls drawn over opaque water (kept: reads close up, not at
  plate view, because 11 ft of water is about 6 px on a full plate).
- **The conclusion from scale:** depth against buildings can only be read in close views. So
  the series is planned as a set: a big map for how far the water went, with numbered
  close-up boxes where the water on the walls reads.
- **10:04, Chris:** "1. yes" (keep the submerged walls; plan the series as a set). "2. treat
  Manchester view as its own. they are two distinctly separate areas of the city, especially
  in this context". So: two areas, Shockoe (north wall) and Manchester (south wall), each
  with its own big view and boxes.
- Still open with Chris: the period city (trace the missing buildings for Agnes and Camille,
  draw on today's city, or mix) and Gaston treatment A or B.

### d2: two areas, their views and their boxes (Opus 5.5 subagent, 2026-11-24, 10:05 to 10:50)

The owner's decisions at 10:04: keep the submerged walls, and plan the series as a set. It has
two areas, Shockoe and Manchester. The working flood is Agnes 1972.

- **35. Frames** · `2026-11-24-35-two-views-frames/`
  - **Shockoe:** S1 (bearing 25), S2 (bearing 0) and S3 (bearing 45). Pick S1: the valley runs
    straight into the picture, and the riverfront from the Mayo Bridge to Rocketts, Mayo Island
    and the whole north wall run across it. Region file: `regions/richmond-floods-shockoe.json`.
  - **Manchester:** M1 (bearing 200, looking from the river) and M2 (bearing 225). Pick M1: the
    flats, the south wall and the bluff read, and the I-95 bridge does not stand in front.
    Region file: `regions/richmond-floods-manchester.json`.
  - **Manchester's data:**
    - The lidar and OSM cover the view. The cached lidar stops at 37.5127 N, short of Goodes
      Street, so the levee's south end and Goodes Street are outside it.
    - The treatment plant is not tagged in OSM; its tanks and basins show in the buildings and
      the lidar.
    - The year-built parcels stop at about 37.5204 N, so most of Manchester's buildings are
      undated: 325 of the 413 the 2026 view shows.
    - The 1972 view shows 56 buildings against 413 today. It is too thin to stand as a picture
      of 1972 Manchester.
  - **The levee:**
    - It is not in OSM. The lidar shows a continuous ridge, 13.0 to 13.7 m NAVD88 (above the
      41 ft overtopping stage), from the south wall's east end at about -77.4284, 37.5235 south
      along the I-95 corridor to about -77.4260, 37.513 (the edge of the cache)
      (`manchester-lidar-hillshade-ridge.png`).
    - Whether that ridge is the levee or the highway's fill, the lidar cannot say. It is in the
      ground, so the fill already respects it, and it is drawn as ground, not as a wall.
    - It is also in the 1972 scene, which has today's ground: if it is the 1994 levee, the 1972
      plate is wrong east of the flats.
    - The plant lies east of it, open to the river in this fill. Whether the real levee encloses
      the plant is not in the data here.
- **36. The big views** · `2026-11-24-36-big-views/`. Agnes 1972, its dry twin, the 1972
  height against today's wall, and the same with no wall, for each area:

  | Area | View | Acres off the channel | Buildings in water / shown |
  |---|---|---|---|
  | Shockoe | 1972 | 220.4 | 87 / 634 |
  | Shockoe | 1972 height, with the wall | 122.3 | 22 / 1,101 |
  | Shockoe | 1972 height, no wall | 208.8 | 193 / 1,097 |
  | Manchester | 1972 | 537.9 | 45 / 56 |
  | Manchester | 1972 height, with the wall | 253.8 | 56 / 413 |
  | Manchester | 1972 height, no wall | 527.1 | 246 / 412 |

  - In Manchester the wall keeps about 273 acres dry in this frame (the research says the south
    wall protects 600 of 750 acres; the frame does not hold all of it). This is the strongest
    picture of the series.
- **37. Boxes and sheets** · `2026-11-24-37-boxes-and-sheets/`, made by `tools/floods/boxes.py`.
  - Each box is cut from the big view's SVG (420 by 280 units, about 210 m across). Its pair is
    the flood beside its dry twin (Shockoe) or beside the no-wall version (Manchester). The depth
    at each box's center comes from the 2 m lidar.
  - Each area also has a map with numbered box frames and a rough 4:3 sheet mockup.
  - Notes per box are in the report; three boxes are weak: Shockoe 6 (Tobacco Row, dry at its
    center), Shockoe 7 (Great Shiplock, nearly all water) and Manchester 3 (Commerce and Maury,
    dry either way).
- **Fixes**
  - The x-ray band is now drawn on floodwall pieces standing in water. Bridge piers still lack
    it.
  - Gauge depths now come from the 2 m elevation model, not the 5 m grid.
  - An order check counts nearer buildings that may be crossed by a band: 0 on the Shockoe 1972
    view, 12 candidates on Manchester 2026 (not inspected one by one).

### 05. Sources for the city of 1969 and 1972 (10:06 to 10:31) · `2026-11-24-05-sources-for-the-1969-72-city/`

- Opus 5.5 subagent, 24 minutes. Files: sources.md, method.md, scripts, four of its twelve
  sample images (the rest, 16 MB in all, are in the cloud workspace at
  /home/claude/floods-research/period-city/samples/).
- **Best public source, no login:** the 1974 USGS orthophoto map of the Richmond quadrangle
  (public domain, about 1 m per pixel). Good enough to say whether a building stood; too
  coarse to trace joined rows of buildings.
- **Why the period plates look empty:** the lifespan rule ends any traced building last seen
  on the 1950-52 maps in 1960 when nothing else dates its loss. In Shockoe Bottom the traced
  buildings fall from 177 in 1936 to 16 in 1969 and 1972. 111 buildings that stood in 1952
  are hidden in 1969; 80 of them are on ground below the 1972 water.
- **Recommended method:** carry the 1950-52 traces forward and drop only those the 1974 photo
  shows gone: one present/gone call per building, about 70 to 100 in Shockoe's flood area.
  Caveat: the photo is two years after Agnes; a building missing from it may have stood in
  1972 and been cleared after the flood.
- **Manchester** has no traces at all; its public source is the 1952 South Richmond Sanborn
  volume (Library of Congress, 87 sheets, 8 to 12 cover the flats).
- Behind logins or orders, so not used: USGS EarthExplorer single frames (1968, 1974), the
  Library of Virginia's Sanborn databases, USDA and NOAA film, Virginia DHR's survey system.
- One web fetch (a Virginia DHR page) waited on a permission prompt that went unanswered;
  the agent moved on without it.

### Period city from evidence (Opus 5.5 subagent, 2026-11-24, 10:34 to about 12:00)

The owner's decision at 10:33: "we want as much coverage as we can ascertain". So every dated
plate shows every building whose presence public, login-free sources ascertain, and says on what.

- **40. Images and registration** · `2026-11-24-40-evidence-images-and-registration/`
  - Reached, no login: the 1974 USGS orthophoto map (GeoPDF at 600 dpi, about 1 m a pixel;
    checksums in `tools/floods/period/fetch.py`); the City of Richmond's 1999 orthophotos (tiles,
    credit DIT/VGIN); VGIN VBMP orthophotos 2002 (spring), 2017 and 2021 (spring). Also seen and
    not used: VBMP 2006, 2007, 2009, 2011, 2013, 2015 (map services answer here); NAIP 2006 and
    2019 to 2023 and NAPP 1996 to 2003 on the federal imagery service (the NAPP export came back
    blank over Richmond); Henrico County's 1998 to 2026 services (no image over the city).
    Nothing public and login-free found for 1975 to 1998: the 1985 plate falls between 1974 and
    1999 (NHAP/NAPP frames and DOQs are behind EarthExplorer's login).
  - Registration of 1974 to today's streets, from control windows: Shockoe 21 of 44 windows,
    shift at the center 2.9 m W, 12.2 m S, growing about 1.5 m/km and 3 m/km across the crop,
    RMS 3.75 m, worst 6.4 m. Manchester 7 clear windows: a translation, 1.9 m W, 15.6 m S, RMS
    3.35 m. The research's single shift (+2 E, -14 N) was close. A fit of the later photos to dark
    pavement was pulled 6 to 10 m north by curb shadows, so they are used as published (look
    checked at three places).
- **41. Contact sheets, every image** · `2026-11-24-41-contact-sheets-all-images/`: 733 Shockoe
  buildings (405 traced with an assumed end, 328 of today's undated) and 332 in Manchester (all
  of today's undated; no traces south of the river), footprint over each of five images.
- **42. Block panels, 1974** · `2026-11-24-42-block-panels-1974/` (35 Shockoe, 28 Manchester,
  look notes beside them). The halftone is read better by block than by tile. Of 1,065 1974
  calls the look changed 251 and confirmed 16 by a line; the rest stood as the machine made
  them (most in Church Hill and residential Manchester, where trees and light house roofs
  cannot be told from yards: there the machine's "gone" calls were mostly made unclear).
- **43. Contact sheets, later photos** · `2026-11-24-43-contact-sheets-later-photos/`: 636 and
  332 buildings, 1999 to 2021. The look changed 1,060 of 3,844 later calls (most the machine's
  "unclear" made present on a building plainly there).
- **44. The 1980 National Register survey** · `2026-11-24-44-national-register-1980-check/`:
  495 addressed entries; 77 of today's buildings matched by OSM address, 29 of them undated.
  It dates 27 before 1969, and it showed that a missing Sanborn match is not absence (most of
  those had none): so no match is now unclear. It overruled one photo call (1705 E Franklin,
  called gone in 1974, dated ca. 1930 and standing in 1980). The test block's Franklin Street
  face (1703 to 1721) is all in the survey, dated 1842 to 1913.
- **45. Plates, round one** · `2026-11-24-45-plates-round-one/` (pale look). The pale
  unconfirmed buildings did not part from the cream walls: not kept.
- **46. Unconfirmed look** · `2026-11-24-46-unconfirmed-style-tries/`: pale, ghost, grey and
  slate. Pick: slate (60% toward a slate grey, finer ink).
- **47. Plates, round two** · `2026-11-24-47-plates-round-two/`, each plate full, the Bottom
  (or the flats) and the test block, before and after:

  | Plate | Shown before | After | Confirmed | Unconfirmed | In water |
  |---|---|---|---|---|---|
  | manchester-1969 · 1969 | 56 | 158 | 56 | 102 | 39 → 86 |
  | manchester-1972 · 1972 | 56 | 158 | 56 | 102 | 45 → 106 |
  | manchester-1985 · 1985 | 66 | 168 | 168 | 0 | 46 → 100 |
  | manchester-1996 · 1996 | 67 | 308 | 169 | 139 | 1 → 15 |
  | manchester-2020 · 2020 | 85 | 418 | 411 | 7 | 1 → 17 |
  | shockoe-1969 · 1969 | 670 | 1239 | 919 | 320 | 58 → 97 |
  | shockoe-1972 · 1972 | 669 | 1237 | 918 | 319 | 87 → 144 |
  | shockoe-1985 · 1985 | 688 | 1177 | 933 | 244 | 72 → 116 |
  | shockoe-1996 · 1996 | 710 | 1250 | 955 | 295 | 1 → 5 |
  | shockoe-2004 · gaston-a | 725 | 1086 | 999 | 87 | 62 → 97 |
  | shockoe-2020 · 2020 | 774 | 1104 | 1093 | 11 | 2 → 3 |

  - What it looks like: Shockoe Bottom is a full district again in 1969 and 1972, the rows
    along Franklin, 17th and 18th standing in the water. The unconfirmed slate buildings sit
    mostly in two places: the traced buildings of the Bottom gone by 1974 (not ascertained for
    1972) and Church Hill's small traced outbuildings under trees. In 1985 and 1996 Church Hill
    carries about 240 slate traced buildings whose loss no image dates (unclear under trees in
    1974 and 1999): honest, but busy. Manchester gains its industrial flats and tank farm
    (2020: 85 to 418 buildings).
  - Looks wrong: a few undated towers seen first in 1999 stand in slate on the 1996 plate (right
    by the rule, odd to see); some riverfront traced buildings last mapped in 1924 now stand
    in slate in 1969 and 1972; the slate is close to the water's lightest tone at plate view.
- **Choices** (whole evidence file, before the scene's leave-outs): ending at the earlier bound
  instead of the later removes 293 unconfirmed buildings in 1969 and 1972 and 278 in 1985;
  starting at the earlier bound adds 28 in 1985, 4 in 1996 and 57 in 2004.
- **Published views unchanged:** `tools/floods/period/unchanged.sh` built each in the base commit
  (b54d29f) and here and compared the SVGs with `cmp`: richmond-downtown-time 1925, 1950, 1960,
  1970, 2026; jackson-ward 1925, 1952, 1959, 2026 and 1952 `--with count`; richmond-1937;
  richmond-streetcars 1925; richmond-floods-d1 1972. All byte for byte the same. The visual check
  passes.
- Note: the crops in `data/floods-period/` (outside git) were scored as fetched at JPEG quality
  74; the 1999 pair (5.3 MB) was then saved again at 66 to keep each crop under 5 MB, and
  `fetch.py` now writes 66. A rerun of `score.py` on them can differ in the last digit.

### Decisions, 10:33 to 10:48

- **10:33, Chris:** on the period city, "we want as much coverage as we can ascertain"; on
  Manchester, go with the recommendation (today's city for now; a traced period Manchester
  deferred); on Gaston A or B, "unsure of what is being asked". The question had been put
  without its picture; re-asked with the crop and a plain description of each.
- **10:36:** an Opus 5.5 subagent started on evidence-based lifespans for every dated flood
  plate (steps from 40): the 1950s traces carried forward and checked against the 1974
  orthophoto and later public aerials; today's undated buildings checked backward; unclear
  buildings drawn in an "unconfirmed" style; opt-in for the flood regions so published
  views stay unchanged.
- **10:48, Chris:** "Gaston, B": solid water where the reports agree, a hatched band for the
  range, pins at the five named places, the river low, the gates open.

### Coverage reviewed; d3 started (12:18)

- The evidence-based coverage came back (steps 40 to 47 on the branch): Shockoe 1972 goes
  from 669 buildings drawn to 918 confirmed and 319 unconfirmed; buildings standing in the
  1972 water from 87 to 144. Fourteen published views proved byte-identical.
- Put to Chris: is the slate "unconfirmed" style right and strong enough; hide the far-off
  Church Hill outbuildings; then assemble the clean working draft of both sets.
- **12:18, Chris:** "Yes, to all proceed". Read as: slate accepted, with one more cue so it
  holds at plate size; outbuildings away from the water hidden by a stated rule; working
  draft d3 of both sets started (steps from 50) on the same Opus 5.5 subagent.

## 2026-11-25

### Chris finds a draw-order error; the look is approved (08:56 to 10:22)

Renders for this are in the branch's steps 55 to 58.

- **08:56, Chris:** "Manchester, second (middle) row, fourth from the left (two L shaped
  buildings): visually inspect the overlap of buildings and walls. Find error. Fix and fix
  elsewhere if root cause is some level of endemic".
- The planning session's first reading at sheet size got one of the two faults (a farther
  wall's submerged band painted over a nearer roof) and missed the main one. At 8x the agent
  found it: the garage of South Falls I painted over the nearer arm of its tower. The wall
  crossing the garage's foot, which the planning session had suspected, was correct.
- **Root causes, all endemic:** whole buildings ordered by simplified outlines, which fails
  for interlocking concave footprints; submerged bands painted late, over nearer items;
  floodwall pieces overlapping at bends. The 12 overlaps accepted in d3 as harmless wall
  joins were real faults; accepting them unseen was a mistake by both agent and planner.
- A check for "painted over a nearer item" now runs on every plate: Manchester 7 to 22
  faults and 80 to 104 wall joints per plate before, none after; Shockoe 36 to 82 before,
  3 to 12 after, every remaining case shown.
- The fix is on for the flood regions only; fourteen published views proved byte-identical.
  So the published catalog still has the interlocking-building fault where it occurs.
- **10:22, Chris:** "1 yes" (hide a traced footprint that a same-year building covers by half
  or more, on the flood plates; counts restated); "2 yes" (backlog: stricter draw order for
  the whole catalog); "3 approved": **the look of d3 is approved.** The series moves to
  final draft.

### Working draft d3 (Opus 5.5 subagent, 2026-11-24, 12:20 to about 13:10)

Chris at 12:18, "Yes, to all proceed": keep the slate look and add one cue to it; leave out the
far-off outbuildings by a stated rule; put together working draft d3 of both sets.

- **50. The cue** · `2026-11-24-50-unconfirmed-cue/`: four versions of the 1972 plate side by
  side (a crop at plate size, a close-up, the whole plate at 600 px): slate alone, slate with a
  dashed ink roof edge, slate with a darker roof, and slate with both a darker roof and a pale
  dashed roof edge (`unconfirmed-slate-both`). **Pick: both.** The darker roof still shows at
  600 px, where no line can. The pale dashes read at plate size and close up, and they keep the
  grey apart from the water's lightest tone. Only `palette.ts` changed (the `UnconfirmedLook`
  type), plus `paleItem`, which adds the dashes.
- **51. Outbuildings** · `2026-11-24-51-outbuildings-far-from-water/`: the rule is an
  unconfirmed traced footprint under 60 m², no part within 12 m of a street's center line, and
  dry 60 m around (`isOutbuilding`). Hidden per plate: 1936 3, 1969 47, 1972 42, 1985 44,
  1996 55, 2004 25, 2020 0. Each caption counts them. The rule is weaker than hoped: most of
  Church Hill's grey buildings in 1985 and 1996 front a street (they are houses, not
  outbuildings), so they stay. A flood's dry twin names its flood with `twinOf` and tests that
  flood's reach, so both draw the same buildings.
- **52. The Manchester x-ray overlaps** · `2026-11-24-52-xray-overlaps-manchester/`: all 12
  pairs are neighboring pieces of the south wall (0.39, 0.45, 0.64 to 0.68). At the joins they
  leave small dark notches, which show only close up. Accepted, not fixed. To list such pairs,
  run with `ISOSCAPE_XRAY_DEBUG=1`.
- **Boxes**
  - Shockoe kept 17th Street Market (moved 40 m east, off Main Street Station), Main Street
    Station, 17th and Dock, Shockoe Slip and Mayo Island.
  - Tobacco Row became 18th and Cary (Tobacco Row's west end; 10 buildings in water in 1972,
    wet in every flood).
  - Great Shiplock Park became East Franklin and Grace, 17th to 19th (29 buildings in water in
    1972). I found these places by counting buildings in water in 100 m cells across five floods.
  - Shockoe boxes are 340 by 165 SVG units, with no overlap beyond 1%.
  - Manchester boxes are 320 by 320. The tank farm box moved onto the tanks, and "On the wall"
    moved to the wall west of the Mayo Bridge. Commerce Road and Maury was dropped.
- **53, 54. d3, two rounds** · `2026-11-24-53-d3-round-one/`, `2026-11-24-54-d3-round-two/`.
  - Every plate has its dry twin. Captions are three lines.
  - Box pairs; across-floods strips for the 17th Street Market and East Franklin.
  - The two 4:3 sheets, composed by `tools/floods/d3/sheet.py` from set.py's pieces, with the
    key, bearing, scale and credits; the contact sheets.
  - Fran 1996 at the wall: a crop of that plate beside the same level with no wall.
  - Round one's faults, fixed in round two:
    - The Manchester maps were cut at the sides and lost two boxes.
    - Dead space under the boxes.
    - The wall label in box crops was huge.
    - Dry twins printed "{floodDepth...}" unfilled; they now say "The same plate with the
      water taken away".
    - The wall plates' third caption line wrapped.
    - Manchester's 1996 and 2020 titles read as if the city were of that year.
  - James Monroe Building (built 1981, CTBUH): the assessor gives no year, and no public photo
    between 1975 and 1998 was found, so the evidence drew it only from 1994. It now has a dated
    entry in `history/richmond-floods.json`. The other 50 undated buildings first seen in 1999
    stay grey on the 1996 plate. Among them is one 35 m building part near Broad Street.
- **Published views unchanged:** `unchanged.sh` against b54d29f gave the same 14 views, byte for
  byte (`unchanged-proof.txt`). check:visual is within tolerance. 294 tests pass.

### d3 round two: things painted over nearer things (Opus 5.5 subagent, 2026-11-25)

Chris on d3, Manchester box 4 (the two L-shaped buildings): "visually inspect the overlap of
buildings and walls. Find error. Fix and fix elsewhere if root cause is some level of endemic".

- **55. The fault at 8x** · `2026-11-25-55-box4-fault-8x/`. The two Ls are South Falls I (12
  floors, OSM w943656806) and its 3-level garage (w943656807), each wrapping round the other.
  - **Error 1:** the garage was painted over the nearer west arm of the tower (a 5-unit sliver at
    the corner; the tower's front edge broken). The cause: `compare` orders whole buildings, by
    their convex hulls. The hulls of two interlocking Ls overlap, so the order fell to the depth
    of their centers, which is wrong at one end.
  - **Error 2 (the no-wall tile):** the tower's x-ray band, on the face of its north arm behind
    the garage, was painted over the garage roof. The cause: a band waits until the water in
    front of its building is painted, and the wait is measured from the building's nearest
    point (its west arm). Everything painted in between, the nearer garage included, was
    covered by it. The `xrayOverlaps` stat missed it because it compared the same building
    depths. The 12 overlaps accepted at d3 were wall joints; this was not one of them.
  - **Not an error:** the wall across the garage's foot. The wall stands 9.5 to 15 m in front of
    the garage and its top (the 41 ft stage, 12.5 m) is 6.6 m above the ground behind it, so it
    hides the garage's foot. Measured, not assumed.
- **56. A check for the whole plate** (`src/occlusion.ts`, `tools/floods/d3/occlusion.ts`).
  - Each pair painted one over the other is sampled every 0.5 SVG units, using the nearest
    surface of each on that line of sight. A pair is flagged where the earlier stands more than
    0.75 m nearer over at least 2 square units.
  - On d3 it found, per plate: Shockoe 36 to 82 such pairs, Manchester 7 to 22; wall joints 80
    to 157 (a piece's casing ends poking into the next piece); plus pairs whose footprints
    overlap on the ground, listed apart.
- **57. Strict occlusion** (`occlusion: "strict"` in both area regions only):
  - concave buildings drawn as convex pieces (`convexPieces`, no seam walls or ink);
  - x-ray bands masked against the nearer items painted before them;
  - outlines overlapping by less than 0.5 m ordered as apart;
  - heavier overlaps (a traced footprint on today's building) left unordered, so they cannot
    force cycles;
  - wall pieces stopped at building outlines (20 pieces on the 2020 Shockoe plate), mitred at
    bends, their casing and line cut square to the screen, and ordered with room for the casing.

  After: Manchester 0 painted-over pairs and 0 wall joints on every plate. Shockoe has 3 to 12
  per plate, 17 distinct pairs in all (`residual-cases-all-plates.jpg`), all small slivers:
    - traced buildings meeting today's at sub-meter overlaps;
    - courtyard buildings (relations with inner rings, not cut into pieces): The Edge at ATC,
      St Paul's Church, r20688391;
    - the rail viaduct against Main Street Station's train shed (a deck and a shed modeled as
      prisms that share space).

  Wall joints are down to 2 or 3 per Shockoe plate, at one sharp bend. Pairs whose footprints
  overlap on the ground rose, because pieces and unordered overlaps count more pairs. They are
  the data: traced footprints lying on today's buildings.
- **58. Rerendered** · `2026-11-25-58-d3-rerendered/`: every plate, twin, box pair, strip and both
  sheets. Box counts are unchanged, except the Shockoe Slip box: one traced building drawn in
  pieces now counts by its pieces' combined center, outside the box.
- **Proof:** `unchanged.sh` against b54d29f: the same 14 views byte for byte (`unchanged-proof.txt`
  in step 58). check:visual within tolerance; 300 tests pass. Still open, shown and not fixed:
  - pairs whose footprints overlap on the ground (`overlap-cases-shockoe-1972-sample.jpg`). Most
    are traced footprints lying on a building of the same year, which the 1950s-era match in
    `lifespans.py` did not catch, and OSM buildings mapped twice (a relation and a way). A rule
    to hide a traced footprint covered half or more by a building drawn that year is proposed,
    not done: it changes coverage counts;
  - courtyard buildings are not cut into pieces;
  - Shockoe's 2 or 3 wall joints at one sharp bend;
  - labels are set over everything by convention.

### Final draft rc1 (Opus 5.5 subagent, 2026-11-25, 10:24 to about 12:00)

The look of d3 was approved at 10:22, with "1 yes" (leave out a traced footprint that a
building of the same year covers by half or more, on the flood plates; restate the counts). The
series is at final draft, `1.0.0-rc1`. No plate numbers, store, Changes page or board edits.

- **60. The merge with the redesigned main** · `2026-11-25-60-merge-redesigned-main/`.
  `origin/main` (8ec1d63 to e7074e4: the explorer in the misfit design language, the site moved to
  isoscape.chrisbusse.com on Cloudflare Pages, and the 10:22 log entry) merged into the branch
  (f091691). One conflict, this log: main's 2026-11-25 entry placed first, then the branch's d3
  sections. README, CLAUDE.md, how-its-made and `src/` merged without conflict; the flood material
  is intact beside main's new text. 300 tests passed, typecheck clean.
  - `unchanged.sh` now takes `VIEWS=` and skips a region the base lacks
    (`richmond-floods-d1` is not on main). Its first run against main showed seven views "DIFF"
    with no SVG on either side: the worktree had no `data/richmond-streetcars`, so both sides
    failed. A link to the main checkout's cache (read only, not committed) fixed it; the proof was
    rerun after all rc1 code (step 65).
- **61. The overlapping-footprint rule** · `2026-11-25-61-footprint-rule/`.
  - `tracedCovered: 0.5` in both area regions: a traced footprint half or more under today's
    buildings drawn that year (sampled every 0.5 m, courtyards not counted) is left out whole and
    counted (`{tracedCovered}`). Agnes 1972: 23 left out; 1936: 30; 1969, 1985, 1996: 23; Gaston: 3;
    2020: 0. Manchester has no traces.
  - Found while looking at the first build (`market-1972-first-build-pink-slab-44pct.jpg`): traced
    buildings standing in a flood were drawn from the ground with no x-ray band and were not
    counted. They now stand in the water as today's do. The d3 captions counted today's buildings
    only ("144 of the 851 shown"); rc1 counts every building drawn: "226 of the 1,173".
  - Counts (whole plate, traced included, d3 → rc1): 1936 1,202 → 1,172 shown, 151 → 145 in
    water; 1969 1,192 → 1,171, 150 → 142; 1972 1,195 → 1,173, 234 → 224; 1985 1,133 → 1,111,
    158 → 149; 1996 1,196 → 1,174, 10 → 10; Gaston 1,062 → 1,059, 73 → 73; 2020 and today's
    wall unchanged; Manchester unchanged. `counts.json` "rc1".
  - The painted-over check on all 26 plates and twins: Manchester 0; Shockoe 12 distinct pairs
    (d3: 17), 2 to 4 a plate (7 on 1936), all slivers (`residual-cases-rc1.jpg`). Footprints still
    partly under today's buildings (under half): 70 of 322 on 1972, 39 of them a quarter or more
    (`covered-cases-rc1.jpg`). Wall joints: 3 on the 2020 plate (`wall-joints-rc1.jpg`).
  - Courtyard buildings are not cut into pieces: `convexPieces` takes an outer ring only, and a
    hole needs a cut from it to the outline; not a contained change. One courtyard pair remains in
    the residual list.
- **62. Boxes** · `2026-11-25-62-boxes/`. The station's box moved 68 m east and 40 m nearer, so the
  head of the shed, the label and the water at its foot read, with I-95 at the edge
  (`station-try-2-picked.jpg`). Mayo Island (two buildings) did not earn its place: centered on
  the Mayo Bridge it showed the deck dry over the channel and awash on the island, a modeling
  rule rather than a fact (`mayo-bridge-try-...`). Tobacco Row at 22nd and 23rd was tried: dry at
  its center in every flood but 1972. Picked: **the canal at Virginia and Byrd streets**, where
  the north wall begins: wet in 1936, 1969, 1972 and 1985, dry behind the wall since
  (`canal-box-1972-and-today-picked.jpg`). The across-floods strips now run through all seven
  Shockoe floods for the market, 18th and Cary, and East Franklin; Gaston's tile reads "rain;
  reported depths: solid where reports agree, hatched for the range", the wall plates' "behind the
  wall (its openings drawn shut)".
  - `drafts/richmond-floods/notes.json` (`tools/floods/rc1/notes.py`): every sheet title, caption
    line, box title and note, key label and credit, with its sources, and a list of what changed
    where the research did not support an earlier line: Gaston's pin "Main Street Station, dry"
    (the Post says it "escaped damage"); "where the water met" (the Post: most water converged on
    17th and Main); the station "of 1901" (no research file dates it); "the island under the river";
    "wet in every flood" for 18th and Cary (dry behind the wall); East Franklin's "most still
    standing" (not checked); the 1771 line "buildings as recorded and traced" (the 1788 scene is the
    1737 plan plus buildings dated before 1788: six in the frame).
- **63. Piers and traced buildings in the water** · `2026-11-25-63-piers-and-traced-in-water/`.
  Piers standing in a flood get the x-ray band in the pier's tone (`dock-1972-pier-bands.jpg`);
  their bands first showed over nearer piers (5 new cases), fixed by masking a pier's band
  against every nearer item painted before it. A dry twin's wall label now sits where its flood's
  does (all twins checked against their plates' SVGs: same coordinates).
- **64. Sheets, round one** · `2026-11-25-64-sheets-rc1-round-one/`. `tools/floods/rc1/sheet.py`, 32 by
  24 in at 300 dpi (9600 by 7200 px), least type 9.4 pt, map type at least 10.3 pt (Shockoe) and
  6.7 pt (a gauge's name on Manchester's half-width maps; raised to 7.5 pt in the fix round).
  One sheet per Shockoe flood (1936, 1969, 1972, 1985, Fran with the wall, Gaston B, 2020 with the
  wall), the Manchester headline, a 32 by 10 in panel of Manchester's Fran and 2020 heights (a
  boxed sheet tried first: its boxes are all dry, and their notes spoke of the 1972 height), and
  the 1771 estimate as a 24 by 10.5 in panel without boxes (six buildings and an estimate ±3 ft:
  boxes would show water and nothing to read). 100 dpi layout tries are kept; the first 300 dpi
  proofs were overwritten by the fix round's before they were copied here (a lapse; the 100 dpi
  `shockoe-2004` shows round one's numbered pins).
- **65. Pre-check and the fix round** · `2026-11-25-65-precheck-and-fix-round/`. Against the README's
  final-draft checklist, at arm's length and in 100% tiles:
  - Fixed: Gaston's numbered pins read as the boxes' numbers and pin 1 sat on box 1's frame (now
    lettered A to E; box 1 moved 20 m east, so A falls inside it); the wall's label under box 5's
    frame on the wall plates (box moved 30 m west); "1 buildings"; Manchester's gauge name at 6.7 pt
    and the frames crossing the wall's label and the gauge's name (map type under 7.5 pt is set up
    to it; labels are laid back over frames).
  - Accepted (up close only): `drafts/richmond-floods/accepted-faults.md`, five items with crops.
  - Final proofs, contact sheets, strips and box pairs are in step 65 (sheets at 2400 px; the 2 MB
    proofs and the 300 dpi files are in the cloud workspace at /mnt/user-data/outputs/floods/rc1/,
    the full-resolution files under `full/`, listed in `full-resolution-files.txt`; over 5 MB, so
    outside git, to go to the Mac's `ISO-TEST/isoscape-work/richmond-floods/casestudy/`).
  - **Proof:** `unchanged.sh` against the new main (e7074e4): 12 published views byte for byte the
    same (`unchanged-proof.txt`); check:visual within tolerance (0.000%); 303 tests pass.
  - **For Chris:** whether to lower the footprint rule's threshold (0.4 would leave out 20 more
    footprints on the 1972 plate, 0.25 would leave out 39); whether boxes 1 and 2 may overlap as
    they now do (about 15% of a frame); and release.

### rc1 built and inspected (10:25 to about 13:40) · `2026-11-25-06-independent-inspection-rc1/`

- A fresh Opus 5.5 subagent built rc1 (steps 60 to 65 on the branch): ten sheets at 300 dpi,
  a source for every printed line (13 lines corrected while writing it), the footprint rule,
  traced buildings now counted in the water (Agnes: 226 of 1,173, where d3 said 144 of 851),
  submerged bands on piers. The agent that did the coverage and draw-order work could not be
  resumed (transcript lost); nothing committed was lost.
- An independent inspector then ran the fixed checklist, a critical read, and a fact check.
  **Verdict: fix.** Thirteen wall-visible faults and ten fact findings. The three that need
  Chris: the Manchester treatment plant drawn 20 ft under water with the wall up, where the
  text says its protection is unknown; the Mayo Bridge deck drawn dry over a flood that is
  recorded as covering it; Gaston's pins ("13 ft up the wall") beside water drawn 2 to 4 ft
  deep. One fact was simply wrong (the dates of the Franklin Street row).
- The planning session had caught two of the thirteen on its own look (the leaked "B" and
  the dry boxes on the Gaston sheet) and missed the rest.

### The fix round starts (12:27)

- Four questions put to Chris with the inspector's crops: draw the Manchester plant's ground
  as "unknown" with no depth; draw bridge decks under the water where the flood is above
  them; redraw Gaston's water at about 28 ft with the hatch to 35 ft so the pins and the
  picture agree; untangle the boxes and give Gaston its own box list.
- **12:27, Chris:** "yes to all, with an eye toward great quality".
- The one fix round the process allows began on the Opus 5.5 subagent that built rc1: rc2
  (steps from 70), covering all thirteen wall-visible faults and ten fact findings. A
  targeted recheck by the independent inspector follows. Because Gaston's picture changes,
  its before and after go back to Chris.

### Final draft rc2 (about 12:30 to 15:00) · `2026-11-25-70-…` to `2026-11-25-76-…`

The one fix round, on the Opus 5.5 subagent that built rc1, working in code with Claude under
Chris's 12:27 rulings. Every sheet of rc2 was looked at tile by tile at half resolution, with
100% crops wherever something looked doubtful; each round went to new files.

- **70, merge.** origin/main (e70005f9, the redesigned pages) merged, both sides of this log and
  of effort.md kept; how-its-made keeps main's text plus the floods paragraph. Tests 304.
- **71, ground not known.** A flood may name `unknown` lines: the courses the unmapped earthen
  levee could take. Ground flooded with the walls alone but dry with the walls plus those lines
  (and not the river itself) is drawn cross-hatched, not as water, and counted apart. Tries:
  strip seams in the hatch (a pale base under a coarser hatch fixed it), stepped edges (two
  3x3 smoothings), basins inside it drawn raised at the flood level (now left at their own
  level), a waterline inside the river (the second line moved off the shore), the Fran range
  hatch over the unknown ground (filtered). Manchester at the 1972 height: 41.5 acres and 2
  buildings in water with the wall, plus 212.8 acres not known (rc1 drew 48 buildings in water).
- **72, decks.** A deck piece whose middle is below the flood is drawn under the water. Mayo
  pieces under, of 18: 1936 8, 1969 14, 1972 18, 1985 18 (report in the step folder). Checked
  against the record: closed at 24 ft (weather service); under in Agnes (secondary).
- **73, Gaston.** Solid to about 28 ft, hatch to 35; pins re-read on the 2 m lidar; WTVR
  credited; "the remnants of Gaston"; its own four boxes. Before and after for Chris.
- **74, boxes.** Frames moved until none crosses another or holds another's badge; the sheet
  tool checks both, and that no frame is cut by a panel. Two dead ends: drawing badges before
  the labels laid back (badge 1 hidden under "Main Street Station"), and laying labels back as
  rectangles (they cut pin E's frame); now badges come last and a label is laid back through an
  exact mask of its own halo. Gaston's frames were made taller (260 x 112 units) and drawn
  narrower than their cells rather than cropping the subject.
- **75, sheets.** Ten sheets at 300 dpi, rebuilt four times. Found on the tiles and fixed:
  "13.4 / ft" split across lines (figures now stay with their units when wrapped); on 2020,
  slivers of depth tone and hooks of waterline where the river climbs through the falls
  (no tone on the river's own water; no waterline in a cell where the river stands above the
  flood or the dry side is mapped water; a test); the 2020 caption now says what the picture
  claims. The 1771 buildings are solid. The Manchester notch is gone with the not-known ground.
- **76, hand-back.** Painted-over check re-run on the final plates: the same 12 Shockoe pairs,
  Manchester none. accepted-faults.md moved to rc2: Mayo deck withdrawn, slab and box notes
  removed, items 1 to 4 re-verified with new crops, one close-up item added (a creek-mouth hook
  on the Manchester 2020 panel). Board: 1.0.0-rc2, rounds 2, faults listed.

**What was done about each rc1 finding**

| # | Done |
|---|---|
| A1 | Plant ground drawn "not known" (cross-hatch, keyed), no gauge, out of the with-wall counts, "plus N acres not known"; box 5 cites WRDA 1986 sec. 401; 2020 notes the 18.5 ft access road. |
| A2 | Decks under the water by rule, keyed "(deck heights are estimates)"; Mayo 8, 14, 18, 18 of 18 pieces under in 1936, 1969, 1972, 1985. |
| A3 | "B:" removed. |
| A4 | Gaston solid to 28 ft, hatch to 35; pins agree (A 8.9 ft, C about 27 ft as drawn, B about 31 ft in the hatch, said so). |
| A5 | No frame crosses another; badges after labels; Gaston and the with-wall sheets have their own lists. |
| A6 | Slab band gone; same frame height and rows on every sheet. |
| A7 | All water on a flood plate in the key's blue. |
| A8 | No line across the river at the falls; caption says the river is drawn at its own surface there. |
| A9 | A box with a gauge gives the gauge's depth, named (15, 11, 19 ft on 1972). |
| A10 | 1996 and 2020 use notes true for those floods. |
| A11 | "buildings in the water: 1 of the 6 shown". |
| A12 | No frame cut by a panel edge (checked by the tool). |
| A13 | "The river, canal and basins at their own level"; keys list only what each sheet draws. |
| Close-up | 1771 buildings solid and keyed; the Manchester notch gone. |
| Facts 1 to 10 | All reworded as the inspector supported (notes.json `changed`, rc2 entries, each with its source). |
| Disputed faults | Mayo deck and slab note fixed and removed; box overlap fixed; the rest re-verified. |
### rc2 built and rechecked (12:30 to about 16:20) · `2026-11-25-07-recheck-rc2/`

- The fix round produced rc2 (steps 71 to 76 on the branch). The Manchester with-wall counts
  fell from 254 acres and 48 buildings to 41.5 acres and 2 buildings, plus 212.8 acres "not
  known". The Mayo Bridge is under the water in 1972 and 1985 and partly in 1936 and 1969.
  Gaston is drawn solid to about 28 ft and hatched to 35.
- The inspector's recheck: all thirteen rc1 faults fixed in substance; **not a clean pass.**
  Three statements still say more than their sources (which 1996 flood shut the Dock Street
  gate; the U-wall's place; the 1771 accounts), a figure split from its unit on four sheets,
  and one drawing fault that fixing the river's color exposed: Gaston's rain pool drawn on
  the river side of the wall.
- A third round at this stage needs Chris's say-so. Put to him.

- **15:00, Chris:** "Approved on both": a third, short fix round (rc3), and the redrawn
  Gaston sheet comes back to him for a look confirmation after it. The say-so a third round
  needs under the stage rules is recorded here and on the board.
- rc3 started on the same Opus 5.5 subagent (steps from 80): the three statements, the split
  figure, Gaston's pool clipped to the city side of the wall, the empty quarter of the
  Gaston sheet (first choice: the rain chart from the rain-map branch), the wall label.

### Final draft rc3 (15:00 to about 16:30) · `2026-11-25-80-…` to `2026-11-25-83-…`

The third fix round, approved by Chris at 15:00 ("Approved on both"), scoped to the recheck's
list (`2026-11-25-07-recheck-rc2/recheck.md`). Done in code with Claude (Opus 5.5 subagent); every
sheet looked at again tile by tile, each round to new files.

- **80, Gaston's pool on the city side (N1).** A pond may be `citySide`: it does not spread
  across a floodwall or the line of its openings. The rc2 pool ran through the open gates down
  to the bank along Dock Street; with the gates open beside a low river the water ran out (the
  spill test, step 15: the Bottom spills to the river at about 19 ft). 100% before and after at
  Dock Street, the canal and both ends of the wall. One leftover, accepted (item 8): the
  hatched band's dashed edge can fall up to a grid cell beyond the wall's foot.
- **81, text.** F1 (which 1996 flood shut the Dock Street gate), F2 ("Just west"), F3 (1771:
  "other accounts give 30 ft and 45 ft on unstated bases"; the hatch is drawn to 12.50 m, 41.0 ft,
  at the Locks), Gaston "then a tropical depression" (NHC TCR, Table 1), box 3 plain, the key on
  the not-known ground ("the edges assume where it runs") and its buildings in the captions (54,
  22, 15; recomputed: Fran is 22, not the 20 the recheck guessed), 18th and Cary's title, a 1936
  note for Shockoe Slip (first try said the water "stopped short"; its count has one building
  touching the water, so it now says "only touched the edge"), Chapel Island's notes say what
  the box shows. Shockoe's with-wall captions drop "(0 buildings on it)".
- **82, layout.** N2: figures held to their units in every wrapped line, and the sheet tool now
  refuses a split; every sheet's laid-out lines are recorded in its `.maps.json` and grepped: none.
  N3: the Gaston sheet's empty quarter takes a rain panel (the watershed's hourly rain from the
  rain branch, its range and the timed events) in the sheet's type and palette; first try drew
  the event lines over the bars, now behind them. N4: the lower wall label, first only lifted
  (it then sat on the bridge), is now moved up and left, clear of the frame line and the stub.
- **83, sheets.** Ten sheets at 300 dpi, built three times; painted-over check unchanged from
  rc2; accepted faults: item 6 regraded B (close-up), items 7 (falls hooks, close-up, not fixed)
  and 8 added. Board: 1.0.0-rc3, rounds 3, budget_note kept.
### rc3 built and rechecked (15:05 to about 17:15) · `2026-11-25-08-recheck-rc3/`

- rc3 (steps 80 to 83 on the branch): the three statements reworded; figures kept with their
  units and the sheet tool made to refuse a split; Gaston's pool held to the city side of
  the wall; a rain panel (inches per hour over the watershed, four timed events) in the
  Gaston sheet's empty quarter; the wall label moved.
- The inspector's verdict: **ready for the owner's release decision**, with one caveat: the
  rain panel's "4:30 flooding under way" is more exact than its source (the time may be
  5:30 p.m. EDT). To be reworded.
- Put to Chris: look confirmation on the Gaston sheet, and its title (exact but long, or
  plainer with the depression wording in the caption).

- **16:09, Chris:** "It looks good and use the shorter pragmatically descriptive title". The
  redrawn Gaston sheet's look is confirmed. Title becomes "Shockoe Bottom: Gaston's rain,
  August 30, 2004", with the storm's status in the caption. Two text-only edits started (the
  title; "about 4:30, flooding reported"), the same art re-stamped as rc3.
- Not yet answered: the release decision and what release means (explorer and story only,
  also sold, or hold).

- **16:12, Chris:** "Move the content work forward and let me defer the publication shape
  until I read the editorial. This one may be of interest artistically to those in the
  impacted areas". The release decision waits on the editorial. An Opus 5.5 subagent started
  on the outline and first full draft of the story (branch `story/richmond-floods`, steps
  from 90), written for a reader new to all of it and for people who lived through these
  floods: plain respect, neutral on blame, nothing beyond the sources, unlisted.

### Rain map (Opus 5.5 subagent)

Branch `feature/flood-rain`, 20:06 to about 21:00. Code and data in `tools/floods/rain/`
(its README has the method, the numbers with their limits and the plan for other floods).

- **30 · Data reach** (`2026-11-23-30-data-reach/`). KAKQ Level II came from the Unidata
  bucket (the `noaa-nexrad-level2` bucket answered 403); AORC by anonymous Zarr; Stage IV not
  from NCAR EOL (its order form says the dataset is unavailable) but from the Iowa Environmental
  Mesonet's public archive. Nothing is left to fetch on the Mac. Raw radar deleted after use;
  `fetch.py` and three manifests refetch everything with sizes and checksums.
- **31 · Radar first look.** 268 volumes, 0.5-degree tilt, both Z-R relations. Tropical puts
  11.3 in over the city at most, standard half that. No clutter in clear air.
- **32 · Watershed.** 31.5 km2 (7,780 acres) on a fresh 3DEP grid; the city says about 8,000
  acres. The 5 m isoscape cache stops at the divide and gives 28.7 km2. Surface, not sewershed.
- **33 · Radar against gauges.** Dead end: one map-wide factor (x1.43) put 13.1 in on the
  watershed and did worse than no correction in a leave-one-out test. A local correction is
  used. Watershed total 10.3 in (8.6 to 11.6), peak hour 5 to 6 p.m. (2.2 in), 8.3 million m3
  (about 2.2 billion gallons). Six-hour rain over the whole watershed 10.0 in (8.3 to 11.2): at
  or beyond NOAA Atlas 14's 1,000-year six-hour point amount (8.04 in) by every estimate but
  AORC's. The one report inside the watershed (Science Museum, 6.56 in, unofficial) is well
  under the radar's 9.8 in there; unresolved.
- **34 · Plan map**, rounds 1, 2, 3, 5. **35 · Hourly panels** (1, 3, 5) **and hyetograph**
  (1, 3, 4, 5).
- **36 · Isometric.** (i) the rain as isoscape graded ground (`Tint.tones: "rain"`, new
  `src/tint-tones.ts`, two lines in scene.ts and history.ts, render.ts untouched; no-tint and
  1937-grades builds byte-identical before and after); rounds 1 to 4. First round read as a
  flooded city and lost an island of rain (band-builder bug, fixed). (ii) a composite over
  isoscape's drawing, rounds 1 to 5, recommended. (e) the explainer, rounds 1 to 3.
- Not done: an areal-reduction factor for Atlas 14 (said in words only); a sewershed polygon
  (none public); the board was not changed.
### rc3 re-stamped: the Gaston title and one event (16:09 to about 16:40) · `2026-11-25-84-gaston-title-restamp/`

- **16:09, Chris:** the Gaston sheet "looks good"; he asked for "the shorter pragmatically
  descriptive title". The recheck of rc3 (`2026-11-25-08-recheck-rc3/`) passed it for the
  release decision with one wording fix (R1).
- Text only, the same art re-stamped, so the version stays 1.0.0-rc3. The title is now
  "Shockoe Bottom: Gaston's rain, August 30, 2004". The storm's status moves to the rain
  panel's caption: "Gaston was a tropical depression over Richmond while the rain fell
  (National Hurricane Center)." The strip label reads "Gaston's rain, 2004", as does the plate's
  own title. The rain panel's 4:30 event reads "about 4:30, flooding reported"; notes.json says
  that Storm Events times are labeled EST and may be an hour later, and credits the 3:58 warning
  to Style Weekly quoting the weather service.
- Only the Gaston sheet was rendered again. Compared with the previous rc3 file at a pixel
  threshold of 24, two regions changed: the title line (x 1400 to 6600, y 0 to 400) and the
  rain panel (x 6200 to 9400, y 5400 to 6600). The map's placement and every box frame are
  identical (`.maps.json`), and no figure is split from its unit. The previous proof is kept here
  as `before-…`. The previous full file (7.5 MB, over the record's 5 MB limit) is in the outputs
  folder `floods/rc3/before-restamp/`; it should go to `ISO-TEST/isoscape-work/richmond-floods/casestudy/` on the Mac.

### Editorial (Opus 5.5 subagent)

Branch `story/richmond-floods` (worktree `wt-floods-story`, from `feature/flood-surface` with
`feature/flood-rain` and `origin/main` merged, then the re-stamped `feature/flood-surface`), 16:12 to
about 16:47. The owner at 16:12: "Move the content work forward and let me defer the publication shape
until I read the editorial." Drafted with Claude; nothing published; the board not touched.

- **Merges.** flood-rain: conflicts in this log and `effort.md` (both kept) and one import line in
  `src/scene.ts` (both imports kept). main: `catalog/pipeline.json` (main's decision text, the
  branch's accepted-faults list; `board.py check` passes) and this log (both). The re-stamped
  flood-surface (f769b432): this log (both).
- **90 · Outline** (`2026-11-25-90-editorial-outline/`): sixteen sections, the argument of each, its
  pictures, the pictures that do not exist, five questions for the owner
  (`tools/stories/richmond-floods/outline.md`).
- **91 · Draft 1, round 1** (`2026-11-25-91-editorial-draft1/`). `story.md` → `page.py` →
  `pages/richmond-floods.md` (`unlisted: true`, `shop: false`, `images: link`, a social picture).
  Every number is a token from `counts.json` rc3 or `rain.json`; every citation lands on an H4 under
  Sources, and `page.py` refuses an uncited source or an unknown key. Pictures by `figures.py`: the rc3
  plate SVGs rendered with their captions taken out in one frame per area (so pairs align for the
  divider), box crops, the market box across eight plates, the rc3 Gaston sheet's rain panel, the rain
  branch's plan map (its working title, which named the storm by its peak strength, cut off) and
  explainer. Read at 1280 and 390 px: the opening pair was a thin strip on a phone, the levels table
  could not be read there, Fig. 7 had no caption, a sentence stood orphaned after Fig. 8, and the
  prose ran about 4,350 words.
- **Found while drafting:** FEMA's study says an older levee at Shockoe Creek's mouth gave limited
  protection, was overtopped in 1972 and stopped pumping in Camille. The plates do not draw it; the
  page says so under its limits, and it is put to the owner.
- **92 · Draft 1, round 2** (`2026-11-25-92-editorial-draft2/`): the opening pair cut to the valley
  (aspect 1.6), the table cut to four columns, the strip two across, the 17th and Dock caption, trims.
  `test/jackson-ward-page.test.ts` lists the pages allowed compare figures; `richmond-floods` added.
  311 tests pass; typecheck clean.
- **Coordinator, during round 2:** the Gaston sheet was re-stamped (title "Shockoe Bottom: Gaston's
  rain, August 30, 2004"; "about 4:30, flooding reported"). Merged; the page crops the re-stamped
  sheet's rain panel, names the day "Gaston's rain", and gives the Storm Events time as labeled EST,
  perhaps 5:30 daylight time.
- **93 · Round 3 and screenshots** (`2026-11-25-93-editorial-screenshots/`): a copy-rule pass (three-item
  lists, two colon punches, one "and not the same" contrast; the lede's "every great flood ... across
  the Manchester flats" narrowed to what the sources map), then contact sheets of the page at 1280 and
  390 px. Prose about 4,100 words, captions about 870. `claims.json`: 96 claims, each with its sources,
  where each is quoted in the research, and the date read; only Watson's "Virginia Floods" was opened
  again for this draft (to name it).
- **For the owner:** the reading copy, its pictures, screenshots and `three-titles.md` are in the
  cloud workspace at `/mnt/user-data/outputs/floods/editorial/` (9 MB). Pictures wished for (none
  made): a section along 17th Street; the Dock and Pear sign beside the 1972 water; HA-410's mapped
  1969 extent over the 1969 plate; a period Manchester.
### The editorial, draft 1 (16:15 to about 17:00)

- The two text edits landed on the Gaston sheet (step 84 on the flood branch): title
  "Shockoe Bottom: Gaston's rain, August 30, 2004"; "about 4:30, flooding reported". A pixel
  comparison shows only the title line and the rain panel changed.
- An Opus 5.5 subagent wrote the outline and first full draft of the story on branch
  `story/richmond-floods` (steps 90 to 93 there): about 4,100 words and 16 figures, 96 claims
  each tied to a source, unlisted. It found one thing the plates do not draw: an older levee
  at Shockoe Creek's mouth that FEMA's study says was overtopped in 1972; the page says so
  under its limits.
- The planning session read the opening and the phone screenshot, ran the copy-rule checks
  (no em dashes; the naming of Gaston), and put the page on the Mac for Chris to read:
  `ISO-TEST/_preview/richmond-floods-editorial/index.html#/richmond-floods`, with the plain
  reading copy and the three titles beside it. The story PDF tool refused the draft because
  three sentences tell the reader to drag a divider; a print wording for those is to be added.

### Editorial: fact check and publication prep (Opus 5.5 subagent, 2026-11-26)

The owner: "let's get this wrapped up with quality, but quickly". An independent fact check of draft
1 (a separate Claude agent) found nothing blocking and 14 fixes.

- **94 · Fixes** (`2026-11-26-94-fact-check-fixes/fact-check.md`): all 14 applied in `story.md` and
  `page.py`, with the three extra points (the 1989 report for the construction start, $143 million as
  the city's figure, the 1996 closures without a month for Dock Street). Sources now point at research
  files inside this folder's step 02 to 04 and 15 and 20 paths.
- **95 · Publication prep** (`2026-11-26-95-publication-prep/`):
  - Title "Richmond, VA, under water: the James River floods of 1771 to 2020 and Gaston's rain of
    2004"; `unlisted` removed, `pdf: true`, order 23. Four lines at 390 px on the static page, five in
    the explorer (its heading type is larger).
  - `tools/stories/richmond-floods/pdf.json` rewords the two divider sentences the shared rules do
    not cover; the opening pair's labels are now "the city dry" and "the Agnes flood" so the print
    sentence reads. PDFs: phone 99 pages, 4.5 MB; large 37 pages, 11.5 MB (cloud workspace
    `/mnt/user-data/outputs/floods/editorial/final/`, over 5 MB, for the Mac). First pages and middle
    pages looked at: no cropped picture, layout intact. The PDF tool prints the old site address
    (busse.github.io/isoscape) on the title page and in footers (`SITE_URL` in `tools/pdf/`), as it
    does for every story; not changed here.
  - `isoscape.config.json`: nav entry and first on the front page's stories.
  - `how-its-made.md` and the README: "Floods (experimental)" becomes "Floods", saying the series is
    published as this story.
  - Release record: `releases/editorial/story-richmond-floods.json` → `releases/story-richmond-floods/v1.json`;
    `check.py --editorial --rebuild` with the rc3 plates, sheets, rain figures and this checkout's
    cache reproduced both steps (the page, and 36 pictures byte for byte). `figures.py` gained
    `--isoscape` (where `locate` runs) for this.
  - Board: published_version 1, orders 0, branch; stage left at outline for the coordinator.
  - 311 tests, typecheck clean, check:visual within tolerance, `unchanged.sh` against main: 12 views
    the same, the d1 region skipped (not on main).

## 2026-11-26

### Published (09:59 to about 11:05)

- **09:59, Chris:** "Just ship it." **10:00:** "I mean let's get this wrapped up with quality,
  but quickly." So: an independent fact check of the editorial first (a separate Opus 5.5
  subagent, read only): nothing blocking, 14 wording and citation fixes, all applied
  (`2026-11-26-94-fact-check-fixes/`). Title shortened by the planning session to "Richmond,
  VA, under water: the James River floods of 1771 to 2020 and Gaston's rain of 2004".
- **10:08, Chris** asked to rethink large media now that the site is on Cloudflare, and to
  separate the open-source tool from his work made with it. **10:09:** yes to keeping this
  series' images out of git and to a planned split (board: `studio-tool-split`); whether the
  studio repository is private or public is deferred. The 760 images went to the Mac; see
  `IMAGES.md`.
- The floods work went to main as one squashed commit (d0e23a2e), so the images are not in
  the repository's history either. The story PDF tool printed the old site address; fixed
  for every story.
- Built into the `cloudflare` branch, pushed to the preview address, looked at on desktop
  and phone sizes from the cloud workspace (the owner's connection was unreliable in a
  storm), then pushed live. One catch on the way: the site tool rewrote the routes file for
  drawings over 25 MB as empty, because this checkout does not hold those files; the live
  routes file was kept.
- **Live:** https://isoscape.chrisbusse.com/#/richmond-floods with phone and large PDFs;
  first in the front page's Stories and in the left menu. The site check passes on the live
  address. Editorial release record: `releases/story-richmond-floods/v1.json`.
- Not done: the forwarding page for this story at the old github.io address; any decision
  about selling the sheets.
