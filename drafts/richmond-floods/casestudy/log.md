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
