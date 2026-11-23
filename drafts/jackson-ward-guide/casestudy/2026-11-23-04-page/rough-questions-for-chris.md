# Jackson Ward pocket guide ("Seeing the change"): rough draft

**Answer first.** A rough draft is ready to look at: a street-named plan map in four renderings, a
1952-and-today pair for seven of the eight stops, and an unlisted draft page that builds. Nothing
is published or merged; the branch `guide/jackson-ward` is pushed. Eight questions for Chris are
below, each with a recommendation. The brief needed four corrections against the story (see
`check.md`): of its four "bridges" only Chamberlayne Parkway and 1st Street are bridges (2nd and
St. James end at the trench); the Coliseum can have no 1952 picture; Sixth Mount Zion's address and
the JXN Haus's place on Bates Street are not in the story.

## What Chris can look at

All in `/mnt/user-data/outputs/guide/jackson-ward/`:

- `map-phone-390.png`: the whole walk as a phone shows it (390 px wide). Some names are left off at
  this size, and the map says so. `map-phone.png` is the same at 3×.
- `map-phone-west-390.png`, `map-phone-east-390.png`: the two halves, which name every street,
  1952 and today. (Split west and east, not north and south: the trench runs across the ward
  and the stops fall on both sides of it, so a west/east split keeps names largest.)
- `map-letter.png`, `map-letter.pdf`: the whole walk on a US Letter sheet, with the stops listed
  under the key.
- `pairs/stop-1.png` to `stop-7.png`: each stop in 1952 and today.
- `guide.md`: the page as drafted; `guide-390.png` and `guide-1440.png`: the built page in
  headless Chrome (sandbox on, file:// only).
- `check.md`: the brief against the story, item by item, the 31 cut street stretches, the stops
  with coordinates, the route and distances.

The walk: 8 stops, 3.1 km (1.9 miles), about 40 minutes of walking at 80 m a minute; it starts
at Second and Leigh and ends beside the Coliseum, 390 m from the start.

## Questions for Chris (recommendation first)

1. **The Coliseum stop has no 1952-and-today picture.** It stands at the edge of the story's
   views, so their "today" leaves it out and the 1952 sheets were not traced there.
   *Recommend:* keep it as the last stop, text only (as drafted). Otherwise, drop it and end the
   walk at the 1st Street bridge, 2.3 km in all.
2. **The JXN Haus's place on Bates Street.** The story says only "on Bates Street," and
   OpenStreetMap does not map it. *Recommend:* keep the stop at the corner of North 2nd and East
   Bates and name the street only (as drafted). If you want the house number or a pin, it needs a
   source the story cites, so it would be a correction to the story first.
3. **Gilpin Court's outline.** No boundary exists in OSM or the story. I drew it from the City of
   Richmond's parcel records: RRHA-owned "Multi-Family" parcels, 46.7 acres (49 with the streets
   between them; the story gives about 38). It is labeled approximate. *Recommend:* keep it, with
   the source line on the map. Two RRHA parcels west and north of Chamberlayne Avenue (an office,
   and a community center parcel) are left outside. Is "Gilpin Court (RRHA public housing)" the
   wording you want?
4. **Stop 5's standing point** is on the west sidewalk of Chamberlayne Avenue at West Charity
   Street, across the avenue from Gilpin Court, looking at homes. *Recommend:* keep it; the text
   says the place's history and takes no position on the plan. If you'd rather not have walkers
   look into a housing project at all, move the stop to the north end of the Chamberlayne Parkway
   bridge (stop 4) and combine the two.
5. **"5th (now Maggie L. Walker Place)."** The story's list says this, but in OSM the bridge over
   the trench is North 5th Street and Maggie L Walker Place is a short street on the south rim.
   *Recommend:* the guide leaves the parenthetical out (as drafted); worth checking on the
   story page.
6. **Three cut streets the story's text does not name**: Vance Street (printed "Vance Street
   (Walker)"), Axtel Street and West Charity Street (printed "(Tazewell)"). They are in the
   story's trace, among its 24 stretches. *Recommend:* name them on the map, as the trace does
   (as drafted).
7. **Wayfinding names from OSM that the story does not use**: "Eggleston Plaza" (stop 1) and
   "14 West Duval Street" (Sixth Mount Zion; not used on the page). *Recommend:* keep "by
   Eggleston Plaza" as a place to stand, since it is a sign on the street, not a fact about the
   past; give no addresses.
8. **Practical notes not in the story** (a transit stop near the start, restrooms, accessibility
   of the bridge sidewalks, the walk at night). *Recommend:* leave them out; the page says only
   the walk's length and that every stop is on a public sidewalk.

## What is not done

- The PDFs (the explorer session's; not built here, as asked).
- No link from the story page, no menu entry (the page is `unlisted: true`).
- Not fact-checked by a separate reader; every line is from the story, but a check against the
  story page, line by line, is the next step.
- The 1952 view near stop 5 shows the Chamberlayne Avenue bridges at the I-64 junction in 1952
  too; this is the story's scene, not the guide's, and is flagged in `check.md` for the main
  session.
- The whole-walk phone map leaves about half the minor names off; the halves carry them.
- No outside reader has seen it; the HJWA chair's read is Chris's call.

## What the explorer session needs to finish the page and the PDFs

- Branch `guide/jackson-ward` (worktree `/home/claude/wt-jw-guide`). Source:
  `tools/stories/jackson-ward-guide/story.md` → `python3 tools/stories/jackson-ward-guide/page.py`
  → `pages/jackson-ward-guide.md`. Never edit the page itself.
- Images in `pages/`: `jackson-ward-guide-map-{phone,west,east,letter}.webp` and
  `jackson-ward-guide-pair-1..7.webp`. `map-letter` is not on the page; it is there for the
  folded-sheet PDF (US Letter, 765 × 990 CSS px at 3×; the PDF in outputs is vector).
- Rebuilding: `route.py` (stops, walk; OSM cache) → `map.py` (all renderings; `--full DIR` for
  review PNGs and the letter PDF) and `pairs.py --work DIR` (builds the story's 1952 and 2026
  scenes with `views.py`, needs `out/stories/jackson-ward/data.json` from
  `node tools/stories/jackson-ward/data.ts`) → `page.py`. `gilpin.py` reads the kept parcel file;
  `--fetch` refreshes it from the city.
- To publish: delete `unlisted: true`, add `pdf: true` once the PDFs exist, link from the story
  page, move the board entry (`story-jackson-ward-guide`, now at research, waiting on the owner).
- Phone PDF note: the map figures carry their own key and credits inside the image, so the PDF
  needs no separate key. The pairs are 1200 px wide with labels sized for 350 px display.
