# Jackson Ward pocket guide: orientation data

From OpenStreetMap as cached November 16, 2026 (`data/richmond-streetcars/osm.json`) and the story's trace (`history/jackson-ward.json`), by `vantage.py`, `orient.py`, `map.py` and `labels.py`. A check against the map only: nobody has stood at these places for this record.

## The frame and the grid

North-up plan, x -800 to 700 m and y -780 to 480 m from 37.5505 N, 77.4375 W (about 1,500 m by 1,260 m: Belvidere Street to past 7th Street, Broad Street to the railroad). Columns A–F west to east, 250 m; rows 1–6 north to south, 210 m. Six phone tiles of two columns by three rows (500 by 630 m, 30 m overlap).

## Places to stand (kept)

| # | Square | Title | Lat, lon | Sidewalk (OSM) | Where to stand | Look (bearing) | Gilpin outline | Why kept |
|---|---|---|---|---|---|---|---|---|
| 1 | B2 | Chamberlayne Avenue's bridges from West Leigh Street | 37.551211, -77.443566 | w1121057677 | on the north sidewalk of West Leigh Street just west of Brook Road | north and northwest to the two curved bridges that carry Chamberlayne Avenue over Brook Road and the railroad (345°) | 256.1 m away | The Belvidere Street extension, dated 1958 by the story's correction; 1952 houses and a coal yard where it runs. Reachable sidewalk, no ramp crossing. |
| 2 | B2 | Gilpin Court from Chamberlayne Avenue | 37.55263, -77.441226 | w1215813972 | on the west sidewalk of Chamberlayne Avenue at West Charity Street | east across the avenue at Gilpin Court (70°) | 18.0 m away | Owner's standing decision: across Chamberlayne Avenue from Gilpin Court, on the far sidewalk. |
| 3 | C2 | Chamberlayne Parkway bridge | 37.55139, -77.440856 | w1122219208 | on the west sidewalk of the Chamberlayne Parkway bridge, about halfway across | east along the highway in its trench toward the North 1st Street bridge, then west toward Belvidere Street (110°, 290°) | 67.1 m away | A bridge over the trench: look along it both ways. West sidewalk, so no ramp is crossed to reach it. |
| 4 | C3 | Sixth Mount Zion, and where Saint James Street ends | 37.550238, -77.438362 | w1483868750 | on the south sidewalk of West Duval Street, across from the church | north at Sixth Mount Zion Baptist Church with the highway behind it, then northeast to the corner of West Duval and Saint James Streets, about 60 m east, where Saint James Street ends at the trench (0°, 60°) | 114.0 m away | The church the road swung around; Saint James Street ends 60 m east (merged with that point). |
| 5 | D4 | Second Street at Leigh Street | 37.5475, -77.437268 | w1205384874 | on the northeast corner of North 2nd and East Leigh Streets, across Leigh Street from Eggleston Plaza | south down 2nd Street toward Clay and Broad Streets, then north up 2nd Street toward the highway (215°, 35°) | 419.2 m away | The Deuce and the Hotel Eggleston corner; the plainest street-level orientation point. |
| 6 | D3 | North 1st Street bridge | 37.55022, -77.436077 | w1485475447 | on the east sidewalk of the North 1st Street bridge, about halfway across | east along the trench toward where 2nd Street ends on each side, then west toward the Chamberlayne Parkway bridge (115°, 295°) | 164.6 m away | A bridge over the trench: 2nd Street's ends on both sides are in view. |
| 7 | D3 | Where Second Street ends, south of the trench | 37.54943, -77.435684 | w1205384865 | on the west sidewalk of North 2nd Street at its north end, where it meets East Duval Street | north across the highway to where 2nd Street starts again (40°) | 256.0 m away | Where Second Street ends on the south side. |
| 8 | E5 | The Coliseum site | 37.545438, -77.433806 | w1125516638 | on the north sidewalk of East Leigh Street, across the street from the Coliseum | south across East Leigh Street at the Richmond Coliseum (200°) | 704.8 m away | Navy Hill and the Coliseum; no pair (reason in pairs.py NO_PAIR). |
| 9 | E2 | Bates Street, and where Second Street starts again | 37.55118, -77.433766 | w1306725612 | at the corner of North 2nd and East Bates Streets, on the east side of 2nd | southeast along Bates Street, then southwest down 2nd Street to where it ends at the trench (130°, 220°) | 74.7 m away | JXN Haus street; looks down 2nd Street to its north end at the trench. |
| 10 | E4 | North 5th Street bridge | 37.548644, -77.432886 | w1293548427 | on the west sidewalk of the North 5th Street bridge, about halfway across | east along the trench toward the North 7th Street bridge, then west toward the North 1st Street bridge (115°, 295°) | 353.0 m away | The 5th Street bridge, which the story's correction names; east end of the traced 1952 streets. |

Each point is on its OSM sidewalk (snapped within 10 m of its target), not within 2 m of the Gilpin Court outline, and in the largest connected part of the graph of OSM sidewalks, footways and crossings with every unsignalled crossing of a motorway, trunk, their ramps or a primary road left out (`vantage.py` asserts both).

## Considered and dropped

- **saint-james-north**: Where Saint James Street ends north of the trench: its only mapped sidewalk there is not joined to the streets around it by mapped sidewalks and crossings, and it is 59 m from the Gilpin Court outline.
- **saint-james-south**: Where Saint James Street ends south of the trench: 60 m from the Sixth Mount Zion point on the same street, so the two are one point, with both views.
- **second-north**: Where Second Street ends north of the trench: no mapped sidewalk within 40 m of its end; the Bates Street point, about 130 m north, looks down 2nd Street to it.
- **seventh-bridge**: The North 7th Street bridge: no mapped sidewalk where it crosses the trench is reachable by mapped sidewalks and crossings.

## The street index

84 names. Rows by kind (a name can have more than one):
- 1952, cut by the trench: 24
- 1952, the stretch under today's highway: 7
- today: 49
- today, also ends at the trench: 2
- today, crosses the trench on a bridge: 5
- today, ends at the trench: 21

Bridges over the trench (OSM bridge ways crossing the highway footprint): North 1st Street, North 7th Street, North 5th Street, Chamberlayne Parkway, Chamberlayne Avenue.
Exits (OSM `junction:ref`): Exit 190: 5th St., Exit 76A: Chamberlayne Ave., Exit 76B: Belvidere St..
Landmarks (labels only): Greater Richmond Convention Center, J. Sargeant Reynolds Community College, VCU (Cabaniss Hall), Abner Clay Park, Maggie L. Walker National Historic Site, Sharon Baptist Church, Richmond Coliseum, Baker Public School, Calhoun Community Center, Greater Mount Moriah Baptist Church, Sixth Mount Zion Baptist Church, Ebenezer Baptist Church.

## Label rules

**Plan maps** (`map.py`): today's streets upright in ink; the 1952 stretches the trench cut dashed in dark red, named in italic; the 7 stretches joined across the trench as the USGS map shows them are drawn dashed and carry today's name of their street. A rendering owes a name to every street with 30 m or more inside it (a tile: inside its own squares, not its overlap); a name goes along the street at full size, then smaller (not under 11.5 px on the phone, 8.5 pt on the sheet), then level beside the street with a leader no more than 70 px away (100 px on the sheet). A rendering that leaves off a name it owes fails the run. Final round: the six tiles and the sheet leave off none; together the tiles name all 84 names. The overview names only the main streets and says so.

**Drawings** (`labels.py`): positions from `isoscape locate` (the drawing tool's own projection, terrain included). Today's half: every named street. 1952 half: the sheet-read 1952 stretches in italic, dark red; a today's street only where it ran on the same line in 1952: no traced 1952 building on its center line (within 2 m), not in or within 30 m of a block the 1952 sheets were not traced for, not on today's bridges or in today's highway footprint. So in Navy Hill, where the 1952 streets were not read off the sheets, today's lines drawn through houses are not named in 1952 (the owner's rule (6): left unlabeled). A street named in both halves is named at the same ground place (within 6 m). Names only on ground at least 30 m inside the story's frame (its near edge is the drawing's slab). A name with no straight run long enough is set level beside its line with a leader; failing that it is left off that picture.

## What each drawing could not name

- **ward**: 1952: Brook Alley, Cameo St., (1952) St. Paul St.; today: Avenue D.
- **ward-sheet**: 1952: W. Jackson St., Brook Alley, W. Federal St., Maggie Lena Walker Memorial Plaza, Cameo St., Oak St., (1952) W. Duval St., (1952) Axtel St., (1952) Brook Rd., (1952) Brook Rd., (1952) Munford St., (1952) W. Baker St., (1952) Shooks St., (1952) W. Charity St., (1952) St. Paul St., (1952) St. John St., (1952) Cave Alley, (1952) Paradise Alley, (1952) Cottage Alley, (1952) N. 5th St.; today: E. Preston St., Avenue D, Price St., Richmond Henrico Turnpike, Hickory St., Maggie L Walker Pl., Maggie Lena Walker Memorial Plaza, Oak St..
- **1**: 1952: Chamberlayne Ave., Brook Alley, W. Clay St., (1952) W. Duval St., (1952) W. Charity St.; today: W. Clay St..
- **2**: 1952: none; today: none.
- **3**: 1952: Brook Rd., Brook Alley; today: Brook Rd., Hickory St..
- **4**: 1952: St. Paul St.; today: St. Paul St..
- **5**: 1952: none; today: none.
- **6**: 1952: W. Charity St., St. John St.; today: W. Charity St., St. John St..
- **7**: 1952: W. Charity St., E. Federal St.; today: W. Charity St., E. Federal St..
- **9**: 1952: none; today: none.
- **10**: 1952: E. Bates St., (1952) Cave Alley; today: none.
