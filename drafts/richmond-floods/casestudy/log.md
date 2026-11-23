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
