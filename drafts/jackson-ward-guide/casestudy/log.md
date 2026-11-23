# Case-study log: the Jackson Ward pocket guide ("Seeing the change")

Kept with Claude under Chris's case-study rule (November 21, 2026), so the development of this
piece can be told later. Each step has a dated folder beside this log with what was looked at.
Times are Eastern. Estimates against actuals are in `../effort.md`.

## How the piece started

A reader of the Jackson Ward story (published November 22, 2026) who drives those roads daily
could not place herself, because the drawings carry no street names; Historic Jackson Ward's
Land Use and Infrastructure chair called the story "a useful visualization tool." The
ISOSCAPE-PROMO session wrote a brief for a pocket guide, which Chris approved on November 23. The
main isoscape session (Claude, Opus 5.5) was asked for the rough draft: the check of the brief, the
street-named plan map, the stop pairs, the words and a draft page. The explorer session will
finish the page and make the PDFs. The run was stopped once by a usage limit and resumed.

## Step 1: checking the brief (08:26-08:47)

Folder: `2026-11-23-01-check/`.

- Read the story page, its tooling and data. The 31 cut stretches are the `lost-` (7) and
  `lost52-` (24) street features of `history/jackson-ward.json`.
- Looked at the area in diagnostic plots (`01`-`05`): OSM streets with names, bridges, parcels.
- Found: only Chamberlayne Parkway, 1st, 5th and 7th cross the trench on bridges; 2nd and
  St. James end at it. Sixth Mount Zion is 14 West Duval Street in OSM; the story gives no
  address. The JXN Haus is not in OSM. The Coliseum is 390 m from Second and Leigh but outside the
  story's frame.
- Gilpin Court has no boundary in OSM. A first outline from the city's year-built layer (large
  parcels dated 1941-71) missed the project's south blocks (the layer lacks parcels without a
  date). Dead end. Second try: the city's parcel layer queried for RRHA-owned Multi-Family parcels
  (9 parcels, 46.7 acres), kept in `tools/stories/jackson-ward-guide/rrha-parcels.geojson`
  (`04-rrha-parcels.png`).
- Route, round 1, with a 5th Street bridge stop (`05-route-round1-fifth-bridge.png`): 3.6 km, and
  the 5th Street bridge is not reachable from Bates Street without crossing back. Changed to the
  1st Street bridge: 3.1 km.
- `check.md` here is the check as delivered.

## Step 2: the pairs (08:48-08:58, then 09:02)

Folder: `2026-11-23-02-pairs/`.

- Built the story's 1952 and 2026 scenes with its own `views.py` (13 s and 23 s).
- Round 1 (`r1-*`): crops by viewBox. Stop 8 (Coliseum) showed empty ground today, because the
  Coliseum crosses the frame's edge and is not drawn; stop 6's 1952 half showed Navy Hill blocks
  empty, because no sheet was traced there. Decision: no pair for the Coliseum, and use the
  story's own hatch (`views.untraced`) on the 1952 half.
- Round 2 (`r2-*`): hatched. Seen at phone width, the in-picture labels and stop markers were too
  small (about 7 px).
- Round 3 (`r3-*`): labels and markers doubled; `r3-pair-6-at-350.png` is how a phone shows one.

## Step 3: the plan map (08:59-09:04)

Folder: `2026-11-23-03-map/`. Each round's renderings at reading size (`*-390.jpg`, letter at
765 px), as looked at.

- Round 1: whole walk, phone. The highway too faint; its label and most route street names
  dropped; the key ran off the right edge.
- Rounds 2-4: darker highway; the walk's streets named first, with a horizontal fallback; the key
  wrapped.
- Round 5 (halves and letter first seen): streets drawn at true width hid the walk at the halves'
  zoom; changed to fixed widths. Letter's key ran off the page; two-column key.
- Round 7: the map widened west, because Moore, Gilmer, Munford and the other sheet-304 streets
  near Belvidere were outside it (the brief names them).
- Round 8: 1952 names placed before minor streets so none is lost in the halves or the letter.
- Rounds 9-13: a stop list on the letter sheet; labels kept off the scale bar, the north arrow
  and the landmarks; the Coliseum label given a leader. Final: phone r12, halves r12, letter r13.
- Split west/east, not north/south: the trench crosses the ward and the stops fall on both sides.

## Step 4: the words and the page (09:04-09:10)

Folder: `2026-11-23-04-page/`.

- `story.md` → `page.py` → `pages/jackson-ward-guide.md`. Every sentence taken from the story with
  its source; the page's sources section is the story's own entries, copied by `page.py`.
- Round 1 screenshots (`page-390`, `page-1440`): pair labels unreadable on a phone; "1300.0 feet".
  Round 2: fixed. Round 3: the whole-walk map moved into the text column on desktop.
- Questions for Chris: `rough-questions-for-chris.md` (his answers to be added here).

## Chris's answers to the rough draft (November 23, 2026)

All eight recommendations accepted: the Coliseum stays as the text-only last stop; stop 5 stays on
the west sidewalk of Chamberlayne Avenue at West Charity Street, its text about the place's
history and taking no position; Gilpin Court keeps the parcel outline, labeled approximate, as
"Gilpin Court (RRHA public housing)"; Vance, Axtel and West Charity Streets are named as the trace
has them; no practical notes the story does not support; "by Eggleston Plaza" stays as a place to
stand, with no addresses; the guide leaves out "5th (now Maggie L. Walker Place)".

## Step 5: working draft d1 (November 23, 2026, 10:10-10:30)

Folder: `2026-11-23-05-d1/`. Every rendering kept there is one that was looked at.

- First, the story's fault the rough draft found (today's Belvidere Street extension and its
  bridges drawn in 1925 and 1952) was fixed on its own branch, `fix/jackson-ward-1952-bridges`
  (see `drafts/jackson-ward/casestudy/`), and merged here, so the pairs are cut from the
  corrected scenes. Stop 5's 1952 half no longer shows the bridges (`pairs-r4-stop-5.jpg`).
- Pairs, round 4: each half labeled in a paper band with the stop's number, the year large and a
  short place name ("1952 · Chamberlayne Ave. at Charity St."), sized for 350 px on a phone and
  checked to fit; the full title and the ground-estimate note moved to the caption. Looked at
  stop 5 and 2 full size and all seven at 350 px. Stop 2's 1952 half still shows a later street
  line through houses (the Navy Hill realignments listed in the story fix); left for the
  planning session.
- Maps, rounds 14-24: the overview names only the walk's spine and frames the two working maps;
  the working maps were made taller (the west map's south edge moved 90 m, the east map's
  110 m, so the scale bar no longer covers Chamberlayne Parkway's name or the Coliseum) and their
  type raised to 14 px for a 350 px display; 1952 names are placed after the walk's own streets,
  with the walk's streets labeled near their stops so the Belvidere cluster keeps every 1952 name;
  the scale bar's box is now kept free of labels. The letter sheet is now a true US Letter page
  (8.5 x 11 in) with half-inch margins; before, the PDF was 7.65 x 9.9 in.
- Dead end: placing every 1952 name before the walk's streets (round 20) lost Chamberlayne
  Avenue at stop 5 and East and West Duval Streets; reverted to walk streets first, placed toward
  their stops (round 21).
- Page: overview and "How to use this guide" first; the east map before stop 1, the west map
  before stop 3; each stop gives its map, its pair, where to stand and what to look at, then the
  story's sentences. "Who keeps the ward's history" is quoted from the story as it stands. The
  draft line is gone. Screenshots at 390 and 1440 px (headless Chrome, sandbox on, file:// only,
  network names unresolvable).
- Claim list: `claims.csv` (128 sentences, each with the story sentence it comes from and its
  source, or marked as the guide's own wayfinding or picture notes) for the independent check.

## The independent check of d1, and the owner's decisions for the final round (November 23, 2026)

An agent that had not drafted the guide checked d1 (163 rows; `2026-11-23-06-route/independent-check.md`
and `independent-check-findings.csv`). Verdict: the story's facts are carried faithfully (52 of 52
story-fact sentences); the problems are what the guide added. Must fix: stop 8 said the 1952 sheets
were not traced for the Coliseum's blocks (34 traced outlines sit inside its footprint); the walk
crossed the Turnpike's exit ramp at the north end of the Chamberlayne Parkway bridge at an
uncontrolled crossing, unsaid; the drawn line ran 10.9 m inside the Gilpin Court outline (route.py
tested only edge midpoints). Should fix: wrong sides of the street at stops 1 and 8, a hatch note
with no hatch at the 1st Street bridge, a later street in stop 2's 1952 half, the USGS credit
missing, an informal path, streets with no mapped sidewalk, about 1.95 km of the line on street
center lines, no written directions, RRHA not spelled out, label placements on the west map, the
JXN Haus leader, and gaps in claims.csv.

The owner's decisions, from the planning session: the guide and the story correction ship as one
change set, the guide driving; the route must be one a careful person would lay out for strangers
(mapped sidewalks and crossings only; a motorway ramp only at a signal; never inside the Gilpin
outline); directions between stops in plain words; stop 8 corrected and given a real pair if one
can be made; "About this guide" as plain facts; the page, three PDFs (phone, large screen and a
folded sheet) and the link from the story page finished in this round; earlier decisions stand
(Coliseum last; stop at Chamberlayne Avenue across from Gilpin Court; the outline labeled
approximate; Vance, Axtel and West Charity named; no practical notes; no addresses).

## Step 6: the route, from the sidewalks (10:40-11:05)

Folder: `2026-11-23-06-route/`. Plots of OSM's pedestrian network (sidewalks black, crossings by
tag: green signals, blue marked, magenta uncontrolled, red unmarked; Gilpin outline pink; the d1
line in cyan) were looked at for each area: `01`-`06`.

- `route.py` rewritten: a graph of footways only (sidewalks, crossings, footways, pedestrian ways;
  no road center lines, no `informal=yes`, nothing private). Crossings are judged against roads on
  the same level, so a bridge sidewalk is not taken for a crossing of the highway under it (the
  first try dropped both bridges' sidewalks as "motorway crossings").
- Safety rules in the graph: a crossing of a motorway, a trunk road, their ramps or a primary road
  is used only where OSM tags it `crossing=traffic_signals`. The only ramp crossing near the walk
  (w1122219206, uncontrolled) is out. Chamberlayne Parkway has no mapped crossing between Leigh
  Street and the bridge, so the only way to its west side is the Leigh/Adams junction: a signal
  across West Leigh (w1122219166) and a zebra across North Adams that OSM tags uncontrolled
  (w1122219201). The east leg of that junction across West Leigh (4 lanes, uncontrolled) is out;
  the walk takes the signal across East Leigh at North 1st Street instead.
- Gilpin Court: no step may touch the outline; a step within 8 m counts ten times its length, so
  the walk takes the far sidewalk. First try with a 4 m exclusion cut Bates Street off entirely
  (the only way onto 2nd Street north of the trench is a corner the outline comes within 2-3 m
  of); the weighted rule takes the south sidewalk of East Federal and crosses at that corner.
  The whole drawn line is tested: 0.0 m inside.
- North of the trench the outline covers West Baker Street's only sidewalk, so the west stops
  (Chamberlayne bridge, Gilpin Court) and the east ones (1st Street bridge, Bates Street) can be
  joined only south of the trench. The order was chosen by trying every order with stop 1 first
  and the Coliseum last: 1 Second and Leigh, 2 Where Second Street stops, 3 North 1st Street bridge,
  4 Bates Street, 5 Sixth Mount Zion, 6 Chamberlayne Parkway bridge (now its west sidewalk),
  7 Gilpin Court, 8 the Coliseum. 4,190 m, about 50 minutes. Ending elsewhere would save 370 m;
  the Coliseum stays last, as decided.
- Stop 1 kept on the northeast corner, now "across Leigh Street from Eggleston Plaza"; stop 2 moved
  across 2nd Street to its west sidewalk, so leg 1-2 crosses 2nd at the Leigh Street signal and
  never at the unsignalled Duval corner; stop 8 "on the north sidewalk of East Leigh Street, across
  the street from the Coliseum".
- Directions are written by `route.py` from the steps (sidewalk side by the nearest parallel named
  road, crossings by their tags), smoothed over corner links under 20 m, consecutive crossings
  merged. Four rounds of wording, read in full each time; the last cut them from 758 to 638 words.
- `route.md` is the per-leg audit (every crossing with its OSM tags).

## Step 7: maps and pairs (10:58-11:20)

Folder: `2026-11-23-07-maps-pairs/`. Map rounds r2-r17 at reading size; pair rounds r4 (d1) and r5.

- Maps follow the new route and numbering. The walk's streets from the directions are named first;
  Chamberlayne Avenue, West Charity and Chamberlayne Parkway are pinned near stops 6 and 7, West
  Duval near stop 5 (the west map's other "Chamberlayne Avenue" is the Belvidere extension, now not
  named there); East Duval is left off the west map; the JXN Haus is named in Bates Street's own
  label, "E. Bates St. (JXN Haus)", with no leader. The compact credits name the USGS map; the key
  has the landmark row. The west map reaches the Leigh/Adams junction.
- Dead ends: 1952 labels placed before the walk's streets (r8) lost West Jackson and Saint James;
  reverted. The 1952 name of a 45 m stretch of St. John Street fits on the west map and the sheet
  but not the east map.
- The east map's scale bar first moved to the lower right (r5) and then collided with the Coliseum
  when the map was made shorter for the PDF (r12); fixed with a two-line note, lower left (r13).
- The walk's line now has a paper casing, so it reads in grayscale (seen on the sheet, step 9).
- Labels are drawn plainly over a separate halo, so map names stay text in the sheet's SVG and PDF.
- Pairs (r5) follow the new numbering. Stop 2 is reframed: the box is moved up the picture until
  no point of Maggie L. Walker Place (w6037438) is in it; the 1952 half no longer shows it
  (`pairs-r4-stop-2-before.jpg`, `pairs-r5-stop-2-reframed.jpg`).
- Stop 8: a guide-only frame centered on the Coliseum was built as a trial (`coliseum-trial/`,
  a temporary region file, not kept). Its 1952 half shows the tracing stopping partway across the
  Coliseum's site (no traced 1952 building more than about 100 m south of its center) and draws
  today's Navy Hill streets, some laid out later. Rejected; stop 8 stays text-only, with the reason
  said as it is.

## Step 8: the page and the PDFs (11:00-11:22)

Folder: `2026-11-23-08-pdfs/`.

- The page: directions before each stop, then where to stand, the pair and the story's sentences;
  "About this guide" as plain facts after "Who keeps the ward's history"; the flagged sentence on
  OpenStreetMap's date sits with the directions in "How to use this guide". `pdf: true` and a new
  shared front-matter key, `pdf-extra:`, list the folded sheet on the PDF line (tested; README).
  The story page links the guide under its introduction.
- Phone PDF, round 1: the tall maps were cut inside their key (the tool cuts at the lowest blank
  row). The tool now prefers a blank band three times as tall as the lowest and 3% of the picture
  (`WIDE_GAP`, tested), and the maps leave such a band above their key. A first version (twice as
  tall, no minimum) moved a cut in the published Jackson Ward timeline; caught by comparing the
  three stories' PDFs text and layout before and after, and tightened until all six were
  identical. Round 3: the east map's frame itself was taller than a phone page and was cut at its
  scale bar; made 950 m tall so the map is whole on one page with its key on the next.

## Step 9: the folded sheet (11:12-11:27)

Folder: `2026-11-23-09-folded-sheet/`.

- `fold.py`: US Letter, landscape, folded in thirds. Outside: the map over two panels (map.py's
  `sheet` rendering, 6.8 x 7.9 in, names at 8.5 pt as text), the cover on the third. Inside: the
  eight stops with directions, where to stand, and the pairs.
- Round 1: type sizes 7.4-8.1 pt in the map's 1952 names and key; the map's own credits ran off its
  box. Fixed: no map text under 8.5 pt on the sheet, the credits moved to the cover (7.3 pt).
- Round 2: the stops ran past the third panel (stop 8's directions cut). Fixed: line height 1.17,
  pairs 1.2 in wide, no caption under them (the year is in each picture).
- Round 3: stop 2's pair floated left of stop 1's; stop 4's pair went to the next column away from
  its title. Fixed: each pair set at the top of its stop and cleared to the right.
- Round 4 in grayscale: the walk read like a major street; the cased line fixed it.
- `fold-mockup.jpg` shows the panels as folded: cover in front, the map's middle on the back,
  stops 1-4 beside the flap when the cover opens.

## Step 10: the final preview (11:24-)

Folder: `2026-11-23-10-final/`: screenshots of the guide at 390 and 1440 px (static page and
explorer), the story's new link, the final claim list (331 rows) and the route audit.
