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
