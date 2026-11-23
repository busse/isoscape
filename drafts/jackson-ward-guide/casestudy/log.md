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
