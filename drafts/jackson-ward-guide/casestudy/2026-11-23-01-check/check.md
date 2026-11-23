# Jackson Ward pocket guide: the brief checked against the published story

Checked November 23, 2026, against `pages/jackson-ward.md` (published November 22, 2026), its
data (`history/jackson-ward.json`, `tools/sanborn/jw/`) and the OpenStreetMap cache the story's
region uses (`data/richmond-streetcars/osm.json`, fetched November 16, 2026). Coordinates are
WGS 84. Distances are along the mapped sidewalks and streets (`tools/stories/jackson-ward-guide/route.py`).

**Answer first.** Most of the brief stands. Four things change: (1) only Chamberlayne Parkway and
1st Street of the brief's four "bridges" cross the trench on bridges; 2nd and St. James Streets end
at it; 5th and 7th Streets are the other bridges. (2) The Coliseum is a short walk (390 m from
Second and Leigh) but lies outside the story's drawn frame, so it can have no 1952-and-today pair.
(3) The story never gives Sixth Mount Zion's address; OSM has 14 West Duval Street. (4) The story
gives no place on Bates Street for the JXN Haus, and OSM does not map it, so the guide names the
street only. The proposed walk has 8 stops, 3.1 km (1.9 miles), about 40 minutes of walking.

## 1. The candidate stops and map elements, item by item

| Brief | Verdict | What the story says, with its source | Note |
|---|---|---|---|
| Bridges now carry 1st, 2nd, St. James and Chamberlayne Parkway over the trench | **Corrected** | "Seven streets that ran through at street level now end at the trench or cross it on a bridge: Chamberlayne Parkway, St. James, 1st, 2nd, Duval, 5th (now Maggie L. Walker Place) and 7th." The story's "today" streets picture marks the bridges, from the `streets` switch in `history/jackson-ward.json`: OSM ways of Chamberlayne Parkway, North 1st, North 5th and North 7th Streets (and Chamberlayne Avenue at the Belvidere junction). | In OSM, North 2nd Street ends at East Duval Street (south rim) and resumes at 37.55026, -77.43474 (north rim); St. James Street ends at Duval Street and resumes north of the trench; East Duval ends near 7th. So **bridged: Chamberlayne Parkway, 1st, 5th, 7th. Cut and ended: St. James, 2nd, Duval.** The story's text does not say which is which; its picture does. |
| "5th (now Maggie L. Walker Place)" (the story's wording, carried by the brief's list) | **Not clear in the story; question for Chris** | Same sentence. | The story's join for 5th (`lost-north-5th-street`) is a 25 m stretch on the south rim between OSM's Maggie L Walker Place (w6037438) and North 5th Street (w175298379). The bridge over the trench is named North 5th Street in OSM. The parenthetical reads as if 5th had been renamed. The guide leaves it out. |
| Second Street at Leigh: "Second Street, the ward's main street" | **Confirmed** | "Second Street, 'the Deuce,' was the ward's main commercial street" [Community Plan 2026]; "known as Black Wall Street by 1903" [NPS, Black Wall Street]; the Miller Hotel / Hotel Eggleston "at the corner of 2nd and Leigh," demolished 2009 [UVA, Green Book project]. | The Hippodrome is on sheet 308 "between Clay and Jackson Streets"; the story does not place it more closely, so the guide does not point to it. |
| Sixth Mount Zion Baptist Church, spared in 1956 and routed around | **Confirmed** | Spared in 1956; the register nomination says it was allowed to stand for its historical significance, credits Dr. Augustus Walter Brown Sr., and "notes that the interstate swings around it" [DHR 127-0472]; Wikipedia, citing Campbell, says the road was "rerouted slightly." Organized by John Jasper in 1867, in the ward from 1869. | **Address:** the story gives none. OSM: 14 West Duval Street (way 297832917). In OSM the motorway passes just north of the church. The guide gives no address. |
| The reconstructed Skipwith cottage at the JXN Haus, Bates Street | **Confirmed (street only)** | Taken by eminent domain in 1957, built 1793 by Abraham Peyton Skipwith, sold for about $25 and moved to Goochland County; rebuilt by the JXN Project, "opened on Bates Street in April 2026 with the JXN Haus" [LVA, House to Highway; Axios, April 2026; The Richmonder, April 2026; Richmond Magazine, May 2026]. | OSM has East Bates Street (way 6041104) north of the trench, running east from North 2nd Street; it does not map the JXN Haus. The guide stands the walker at 2nd and Bates and names the street only. |
| Gilpin Court boundary from a public street, where Apostle Town stood | **Confirmed** | Clearing of Apostle Town began with the ordinance of January 16, 1941 [LVA 2025]; dedicated April 28, 1943, 301 units [LVA 2025]; enlarged in 1957 to house families the Turnpike displaced [Encyclopedia Virginia]; homes; the page takes no position on the redevelopment plan. | Standing point is on the west sidewalk of Chamberlayne Avenue, across the avenue from the outline (checked in code: outside it). |
| The Coliseum site in Navy Hill | **Confirmed; within a sensible walk; no pair** | Built later on cleared blocks of Navy Hill [Kollatz 2019]; under construction December 30, 1968 [WVTF 2016]; on November 19, 2026, still standing, demolition aimed for the end of 2027 [WWBT, November 2026]. | 390 m from stop 1 along Leigh Street. It stands at the near (south) edge of the story's views, so isoscape leaves it out of their "today" (it draws only buildings wholly inside the frame), and the 1952 sheets were not traced for its blocks. No pair is possible from the story's scenes. |
| One plan map with today's streets named (OSM) | Done | | |
| The 1952 streets the trench removed, from the story's trace | **Confirmed, with three names the page does not list** | "Inside the corridor the 1952 sheets print 24 more stretches of 22 streets and alleys, 2,275 m in all ... Among them are: Moore, Gilmer, Munford, Shooks, Calhoun and West Baker Streets; St. Paul and St. John Streets; North 3rd, 4th, 5th and 6th Streets, and East and West Duval Streets; a stretch of Brook Road; Cave, Paradise, Cottage and Gilbert Alleys." [LoC, Sanborn 1952 vol. 3] | The trace also holds **Vance Street (printed "Vance Street (Walker)"), Axtel Street and West Charity Street (printed "(Tazewell)")**, and two stretches of Brook Road. The map draws and names them as the trace does. See section 2. |
| Today's I-95 footprint | Done | | Drawn from OSM motorway and ramp ways (lanes × 3.65 m plus shoulders), so it includes I-64 and its ramps, which the story's count polygon leaves out. Labeled "I-95 / I-64" (the story: "The road now carries I-95 and, through the ward, I-64 as well" [Feasibility Study 2022, §1.4.3]). |
| Gilpin Court as a bordered area, neutral label | Done | | Neither OSM nor the story has a boundary. The outline is the City of Richmond parcels owned by the Richmond Redevelopment and Housing Authority with land use "Multi-Family" (9 parcels, 46.7 acres; 49.3 acres with the streets between them), fetched once on November 23, 2026 and kept in `tools/stories/jackson-ward-guide/rrha-parcels.geojson`. The story gives about 38 acres. Marked approximate on the map. |
| Credits: OSM, Sanborn/LoC, USGS | Done | | USGS is credited for the seven street stretches joined across the trench (the 1933–34 map) and, on the page, for the lidar under the "today" views. The map itself uses no elevation. |
| "Who keeps the ward's history" | Carried over | | One sentence adapted: "This page does not draw on their collections" became "The story this guide is drawn from does not draw on their collections," since the guide draws only on the story. |

## 2. The 1952 streets the trench cut, from the story's trace

From `history/jackson-ward.json`: the 31 `street` features whose ids start `lost-` (7) or `lost52-` (24).

**Seven stretches joined straight across the trench** between a street's surviving ends, as the
USGS map of 1933–34 shows them running through: Chamberlayne Parkway, Saint James Street, North
1st Street, North 2nd Street, North 5th Street, East Duval Street, North 7th Street. On the map
these are drawn dashed under today's bridges where there is one, and named by today's street name.

**Twenty-four stretches read off the 1952 sheets** (sheet in brackets):

| Street (as the trace names it) | Sheet | Length in corridor test |
|---|---|---|
| Moore Street | 304 | 169 m, 83% in corridor |
| Gilmer Street | 304 | 112 m, 82% |
| Vance Street ("Vance Street (Walker)") | 304 | 98 m, 74% |
| West Duval Street | 304 | 126 m, 57% |
| Axtel Street | 304 | 33 m, 100% |
| Brook Road | 304 | 38 m, 100% |
| Munford Street | 304 | 129 m, 86% |
| Brook Road | 315 | 116 m, 79% |
| West Baker Street | 315 | 97 m, 63% |
| Shooks Street | 315 | 86 m, 97% |
| Calhoun Street | 317 | 99 m, 44% |
| West Charity Street ("(Tazewell)") | 317 | 98 m, 99% |
| West Baker Street | 326 | 104 m, 100% |
| Saint Paul Street | 326 | 87 m, 80% |
| Saint John Street | 326 | 45 m, 100% |
| North 3rd Street | 307 | 87 m, 71% |
| North 4th Street | 307 | 90 m, 68% |
| Cave Alley | 307 | 100 m, 76% |
| Paradise Alley | 307 | 95 m, 70% |
| Cottage Alley | 307 | 89 m, 68% |
| East Duval Street | 310 | 122 m, 98% |
| North 5th Street | 310 | 73 m, 100% |
| North 6th Street | 310 | 102 m, 93% |
| Gilbert Alley | 310 | 82 m, 96% |

22 distinct names, matching the page's "24 more stretches of 22 streets and alleys." Every one of
them is drawn and named on the letter map and on the two phone halves; the whole-walk phone map
leaves some names off at its size and says so.

## 3. The proposed stops

Every standing point is on an OSM sidewalk (footway=sidewalk), checked in code to lie outside the
Gilpin Court outline. "Look" is the direction the walker faces.

| # | Stop | Stand (lat, lon) | On (OSM way) | Where to stand | Look |
|---|---|---|---|---|---|
| 1 | Second Street at Leigh Street | 37.547500, -77.437268 | sidewalk w1205384874 | NE corner of North 2nd and East Leigh, east side of 2nd, by Eggleston Plaza (OSM name) | south down 2nd toward Clay and Broad |
| 2 | Where Second Street stops | 37.549375, -77.435499 | sidewalk w1210906690 | north end of North 2nd at East Duval, by the highway | north across I-95 to where 2nd resumes |
| 3 | Sixth Mount Zion Baptist Church | 37.550238, -77.438362 | sidewalk w1483868750 | south sidewalk of West Duval, across from the church | north at the church, the highway behind it |
| 4 | Chamberlayne Parkway bridge | 37.551388, -77.440672 | bridge sidewalk w1122219209 | east sidewalk, halfway across | east along the trench toward the 1st Street bridge |
| 5 | Gilpin Court, where Apostle Town stood | 37.552630, -77.441226 | sidewalk w1215813972 | west sidewalk of Chamberlayne Avenue at West Charity | east across the avenue at Gilpin Court |
| 6 | Bates Street and the JXN Haus | 37.551180, -77.433766 | sidewalk w1306725612 | corner of North 2nd and East Bates | east along Bates Street |
| 7 | North 1st Street bridge | 37.550220, -77.436077 | bridge sidewalk w1485475447 | east sidewalk, halfway across | east along the trench toward 2nd Street's cut ends and Navy Hill |
| 8 | The Coliseum site | 37.545438, -77.433807 | sidewalk w1125516638 | East Leigh Street beside the Coliseum | south at the Coliseum |

**Order and distances** (walking, along mapped sidewalks and streets):

| Leg | Distance | At 80 m a minute |
|---|---|---|
| 1 → 2 | 285 m | 4 min |
| 2 → 3 | 430 m | 5 min |
| 3 → 4 | 275 m | 3 min |
| 4 → 5 | 191 m | 2 min |
| 5 → 6 | 796 m (along West Baker Street, the edge of Gilpin Court, never through it) | 10 min |
| 6 → 7 | 287 m | 4 min |
| 7 → 8 | 870 m (down 1st Street, east on Leigh) | 11 min |
| **Total** | **3,134 m (1.9 miles)** | **about 40 min** |
| 8 → back to 1 | 390 m | 5 min |

**Why it starts and ends where it does.** It starts at Second and Leigh, the story's main street,
south of the trench and two blocks north of Broad Street, so a visitor coming from downtown begins
where the ward's old center was, before seeing the highway. It crosses the trench twice on bridges
(Chamberlayne Parkway, then 1st Street), so the walker sees it from both rims. It ends beside the
Coliseum, 390 m from the start along Leigh Street, so the walk closes as a loop.

**Dropped from the candidates:** a separate stop at the 5th Street bridge (tried in the first
route: from Bates Street it meant crossing back over the 1st Street bridge and walking east, 942 m;
the 1st Street bridge gives the same view of the cut ends).

## 4. Things noticed that are not the guide's to fix

- In the story's 1952 view, the crop at stop 5 shows the elevated Chamberlayne Avenue bridges and
  ramps at the I-64 junction, which look the same in 1952 and today. The story's scene draws them
  (its `atGrade` list sets only the Turnpike's bridges and two 1971 bridges at grade before their
  dates). If those structures postdate 1952, the story's 1952 view carries them too. Flagged for
  the main isoscape session; nothing changed.
- The story's views are not hatched in the raw scene; the guide's pairs use the story's own
  hatch (`views.untraced`) so the untraced Navy Hill blocks (stop 6, stop 7) read as untraced.
