# Jackson Ward pocket guide, working draft d1: independent check

Checked November 23, 2026, by Claude, an agent that did not draft the guide. Nothing in any repo
was changed. Every row is in `findings.csv` (163 rows: 128 claim-list rows `C001`-`C128`, then
route `R`, map `M`, pair `P`, Gilpin Court `G`, page `T` and About `A`).

## Verdict

**Ready for the owner's review after the listed fixes.** The story's facts are carried
faithfully: of the 52 story-fact sentences, none misquotes the story or adds a date, number,
actor or cause, and the sources and "Who keeps the ward's history" match the story word for
word. The problems are in what the guide adds on its own: one false statement about the
Coliseum, a route that crosses a highway exit ramp without saying so and clips the Gilpin Court
outline, and wayfinding that puts two stops on the wrong side of the street.

## Must fix

1. **Stop 8 says the 1952 sheets were not traced for the Coliseum's blocks. They were.**
   `history/sanborn/jackson-ward-1952.geojson` has 34 traced 1952 outlines, all from sheet 309
   (one of the story's 15 sheets), inside the Coliseum's OpenStreetMap footprint (way
   321367756), and 116 within 60 m of it. The story does not make this claim. The other half of
   the note is right: the footprint's center is about 609 m in front of the view's center, past
   the near edge at 600 m, so isoscape leaves the Coliseum out of the "today" view.
   *Fix:* delete ", and the 1952 sheets were not traced for its blocks" from the stop 8 note,
   from `NO_PAIR` in `pairs.py` and from `pairs.json`.

2. **Between stops 4 and 5 the walk crosses the Turnpike's exit ramp at grade, and the guide
   does not say so.** At the north end of the Chamberlayne Parkway bridge, the exit ramp OSM
   w601102858 (motorway_link, 3 lanes, one way) meets Chamberlayne Avenue at grade. From stop 4
   (east sidewalk, w1122219209), the mapped way on is crossing w1122219206, tagged
   `crossing=uncontrolled`, across the ramp and the start of West Baker Street. After that it
   takes the signalled crossing w1225580661 over the avenue. The drawn line runs on the
   carriageway through the junction.
   *Fix (the owner decides):* either say at stop 4 that the way to stop 5 crosses the highway
   exit ramp at the north end of the bridge, at a crossing with no signal, and then crosses
   Chamberlayne Avenue at the signal; or move stop 4 to the west sidewalk (w1122219208) and
   re-route 3→4. OSM gives a 589 m all-sidewalk approach by way of the signalled crossing
   w1122219166, but its other crossings are unmarked or uncontrolled and still need checking.

3. **The route enters the Gilpin Court outline.** Leg 5→6 as drawn runs 10.9 m inside the
   outline, at about 37.55155 N, 77.43921 W to 37.55148 N, 77.43892 W. That is the north
   sidewalk of West Baker Street, where the outline (parcels joined by a 14 m closing) overlaps
   the sidewalk. `route.json` reports 0 m because `route.py` tests only each edge's midpoint. No
   stop is inside the outline (the nearest is stop 5, 18 m away).
   *Fix:* keep that block to the south side of West Baker Street, or test the drawn line
   against the outline in `route.py` and re-route until it is 0 m.

## Should fix

- **Stop 1, "by Eggleston Plaza"** (C024). The stop is on the northeast corner, north of Leigh.
  OSM's Eggleston Plaza (way 495303214) is on the southeast corner, about 40 m away across East
  Leigh Street. *Fix:* "across Leigh Street from Eggleston Plaza", or move the stop.
- **Stop 8, "beside the Coliseum"** (C111, and C005 in "How to use"). The stop is on the
  **north** sidewalk of East Leigh Street (w1125516638). The Coliseum is across the street,
  50 m away, and East Leigh there has up to 5 lanes. *Fix:* "Stand on the north sidewalk of
  East Leigh Street, across the street from the Coliseum"; "ends across East Leigh Street from
  the Coliseum".
- **Stop 7's caption mentions hatched blocks, but the picture has none** (C101, P03). *Fix:*
  delete that sentence.
- **The 1952 half of stop 2 shows a later street** (P02). See "The pairs" below. *Fix:* crop the
  box north of the line, as d1.md offers.
- **The 1952 street lines are credited only to the Sanborn sheets** (C008, C015, C127, M09,
  A01). Seven of the 31 stretches are straight joins placed from the USGS map of 1933–34, as
  the story says. The overview's caption, the About note and the compact map credits omit USGS.
  The letter sheet's credit includes it. *Fix:* add the USGS clause to each.
- **"Every fact in it comes from the page"** (C014, A01). Directions and distances come from
  OpenStreetMap. *Fix:* "Every historical fact in it comes from the page ..., with that page's
  sources; directions and distances come from OpenStreetMap."
- **"2nd Street is one that ends"** (C038). This is true in OSM and visible from the stop, but
  the story's text does not say which streets end and which are bridged. *Fix:* "...; 2nd
  Street is one of them."
- **"The 1952 buildings are traced from the Sanborn sheets"** (C125). The 1952 halves also draw
  buildings standing today that the city dates to 1952 or earlier (the story says so). *Fix:*
  add "or, where they still stand, drawn from today's map".
- **The deck and summary say "each place in 1952 and today"** (T01). Stop 8 has no pair.
  *Fix:* "seven of them shown in 1952 and today".
- **The east map's JXN Haus label points to a spot on Bates Street** (M04). Its leader ends at
  the street's midpoint, but the story gives no location. *Fix:* drop the leader.
- **West map street names near stops 3 and 5** (M02, M03). "E. Duval St." sits right under
  stop 3, which is on West Duval. The only "Chamberlayne Ave." label is on the Belvidere
  extension across the highway; the avenue at stop 5 is not named. *Fix:* drop that East Duval
  label, name West Duval at stop 3, and name Chamberlayne Ave. beside stop 5.
- **Route quality, from the map** (R03–R05). The route follows an informal path (w1485475439,
  82 m). It uses streets with no mapped sidewalk (East Charity, North 2nd north of the trench,
  part of East Baker). About 1.95 km of the 3.13 km line runs on street center lines or the 1st
  Street Cycle Track. Kept to mapped sidewalks and crossings only, the walk is about 3.8 km
  (about 48 minutes). *Fix:* make `route.py` prefer footways and leave out `informal=yes`, then
  redraw and restate the distance.
- **No text directions between stops** (T02). A phone reader has to follow the line on a 390 px
  map. *Fix:* add one wayfinding line per leg.
- **RRHA is never spelled out** (G02). *Fix:* "(RRHA)" after the authority's full name at
  stop 5.

The notes (direction words such as "east" along Bates Street, which runs at 129°; split rows and
mislabeled rows in claims.csv; the east map also showing stop 3; the key lacking a landmark row;
crowded 1952 labels at 390 px; the letter sheet's 6.8 pt type and different title) are in
`findings.csv`.

## The claim list, row by row

- All 52 story-fact rows are faithful. Joined sentences keep their sources and hedges.
- Two rows say less than the story, and neither changes the meaning:
  - Row 81 leaves out the MOU's "at least ten years".
  - Row 104 leaves out the 12 m² rule, the untraced ramp loop and "a floor". It keeps
    "approximate".
- The rows that are wrong or say more are all guide-made: C008, C014, C015, C038, C101, C110,
  C125 and C127.
- **Errors in claims.csv itself:**
  - Row 2 (a heading) is labeled a story fact.
  - Rows 21 and 33 are matched to unrelated story sentences.
  - Row 68 gives the story sentence as "...on the plan"; for the cap the story says "...on the
    cap".
  - Rows 29/30, 41/42 and 54/55 are single sentences split at an abbreviation.
- **Missing from claims.csv:** the front matter, the ten alt texts, the text inside the images
  (keys, credits, pair labels) and the letter sheet's stop list. These were checked here
  instead.

## Route and map audit

**Stops** (OSM cache `data/richmond-streetcars/osm.json`, November 16, 2026). All eight stops
are on mapped sidewalks.

| Stop | Position | Bearing and distance to what it says you see | Line of sight in plan |
|---|---|---|---|
| 1 | NE corner of 2nd and Leigh | Down 2nd Street at 218° | Clear |
| 2 | 9 m from the 2nd/Duval node | North end of 2nd, 118 m at 34° | Clear |
| 3 | 10 m south of West Duval's center | Church 13 m away, 18° | Highway behind the church |
| 4 | East sidewalk, 52% across the bridge | 1st Street bridge, 415 m at 109° | 91% of the line inside the motorway footprint |
| 5 | 10 m west of the avenue | Outline 18 m at 78° | — |
| 6 | 8 m from the 2nd/Bates corner | Bates runs at 129° | — |
| 7 | East sidewalk, about 60% across | Cut ends of 2nd, 97 m and 117 m | — |
| 8 | North sidewalk of Leigh | Coliseum 105 m at 212° | — |

**Legs.**

| Leg | Length |
|---|---|
| 1→2 | 285 m |
| 2→3 | 430 m |
| 3→4 | 275 m |
| 4→5 | 191 m |
| 5→6 | 796 m |
| 6→7 | 287 m |
| 7→8 | 870 m |
| **Total** | **3,134 m** (3.1 km, 1.9 mi, 39 min at 80 m a minute) |

Stop 8 back to stop 1 is 390 m. These numbers reproduce `route.json` exactly.

**Safety, from the map only.** This is a check against OpenStreetMap. Nobody has walked the
route.

- One at-grade motorway ramp crossing, uncontrolled (must fix 2).
- One informal path.
- About 300 m of streets with no mapped sidewalk.
- Stretches where the line implies crossings that OSM's sidewalks do not join: Duval Street
  between 1st Street and the church, and leg 5→6.
- Mapped crossings that are unmarked: 1st Street and the cycle track at Duval, St. John, St.
  James, East Bates and service drives.

**Maps.**

- The discs are within 1.5 px of their coordinates.
- The scale bars measure 200 m to within the width of the end ticks.
- North is true north.
- The 24 names of 1952 streets match `streets1952.json`.
- Today's names follow OSM ways, apart from the label placements in M02 and M03.
- The letter sheet's stop list matches the page word for word and is 612 × 792 pt.

**Pairs.**

- Each pair is one box cut from both scenes, and every caption carries the ground estimate.
- At stop 2, the faint later line is **Maggie L. Walker Place** (OSM w6037438). fix.md lists it
  among today's streets that run through traced 1952 buildings. It is unlabeled and looks like
  any 1952 street, so a reader would take it for one.
- At stop 5, the curved band is Brook Road, which existed in 1952. No bridges or ramps appear.
- No later structure was seen in stops 1, 3, 4, 5 and 7.

## What could not be checked

- Whether sidewalks, crossings, signals or curb ramps exist on the ground where OSM does or does
  not map them; lighting; traffic.
- The real view from each stop: plan only, with no heights, trees, fences or walls on the
  bridges.
- Later streets in the 1952 half of stop 6 (Navy Hill north of the trench), because the 1952
  streets there were never read off the sheets.
- The exact place of each disc in the pairs beyond the story's fit (`views._fit`, good to a few
  meters).
- Any source outside the repo: no web source was opened this session. The guide's facts were
  checked against the story page only, as the brief asked.
- How the page looks on a real phone: only the drafting renders (`guide-390.png`) and the
  file:// preview's HTML were read.
