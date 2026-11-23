# Jackson Ward walking guide: the route, leg by leg

From OpenStreetMap as cached November 16, 2026 (`data/richmond-streetcars/osm.json`), by `route.py`. A check against the map only: nobody has walked it for this audit.

Total 4,190 m (2.6 mi), about 50 minutes at 80 m a minute. Stop 8 back to stop 1: 390 m. Length of the drawn line inside the Gilpin Court outline: 0.0 m.

## Stops

| Stop | Title | Stands on | Lat, lon |
|---|---|---|---|
| 1 | Second Street at Leigh Street | w1205384874 (on the northeast corner of North 2nd and East Leigh Streets, across Leigh Street from Eggleston Plaza) | 37.5475, -77.437268 |
| 2 | Where Second Street stops | w1205384865 (on the west sidewalk of North 2nd Street at its north end, where it meets East Duval Street by the highway) | 37.54943, -77.435684 |
| 3 | North 1st Street bridge | w1485475447 (on the east sidewalk of the North 1st Street bridge, about halfway across) | 37.55022, -77.436077 |
| 4 | Bates Street and the JXN Haus | w1306725612 (at the corner of North 2nd and East Bates Streets, on the east side of 2nd) | 37.55118, -77.433766 |
| 5 | Sixth Mount Zion Baptist Church | w1483868750 (on the south sidewalk of West Duval Street, across from the church) | 37.550238, -77.438362 |
| 6 | Chamberlayne Parkway bridge | w1122219208 (on the west sidewalk of the Chamberlayne Parkway bridge, about halfway across) | 37.55139, -77.440856 |
| 7 | Gilpin Court, where Apostle Town stood | w1215813972 (on the west sidewalk of Chamberlayne Avenue at West Charity Street) | 37.55263, -77.441226 |
| 8 | The Coliseum site | w1125516638 (on the north sidewalk of East Leigh Street, across the street from the Coliseum) | 37.545438, -77.433807 |

## What a walker should know, from the map

- **Both bridges have a sidewalk on each side** in OSM (Chamberlayne Parkway: w1122219208 west,
  w1122219209 east; North 1st Street: w1485475446 west, w1485475447 east). The walk uses the west
  sidewalk of Chamberlayne Parkway (stop 6) and the east sidewalk of North 1st Street (stop 3).
- **No motorway ramp is crossed.** The Turnpike exit ramp at the north end of the Chamberlayne
  Parkway bridge (w601102858) meets Chamberlayne Avenue at an uncontrolled crossing
  (w1122219206) on the bridge's east side; the walk stays on the west sidewalk and never reaches it.
- **Chamberlayne Parkway has no mapped crossing between Leigh Street and the bridge.** To reach its
  west side the walk goes round the Leigh Street / North Adams Street junction: the signal across
  West Leigh Street (w1122219166, zebra-marked) and a zebra-marked crosswalk across North Adams
  Street that OSM tags `uncontrolled` (w1122219201; 2 lanes, 25 mph). It does this on legs 5-6 and
  7-8. The junction's east leg across West Leigh (w1122219202; 4 lanes, uncontrolled) is not used;
  the walk crosses East Leigh at the signal at North 1st Street (w1022715851) instead, which
  is why leg 5-6 goes east along Leigh before it goes west.
- **Streets crossed with no marked crosswalk** (OSM `crossing=unmarked`): East Duval Street at
  North 1st Street (2 lanes, legs 2-3 and 4-5), East Federal and North 2nd Streets at their corner
  (legs 3-4 and 4-5), and residential streets (East and West Jackson, Saint James, Price, Saint
  Peter, West Duval). Marked, no signal: East Jackson at North 2nd, East Baker and East Charity at
  North 1st, North 1st at East Jackson.
- **The walk passes some stretches twice**: North 1st Street over the bridge (legs 3-4 and 4-5),
  and Chamberlayne Parkway's west sidewalk between Leigh Street and the bridge (legs 5-6 and 7-8).
  North of the trench the Gilpin Court outline covers West Baker Street's only sidewalk, so the
  east and west stops can only be joined south of the trench.
- **Gilpin Court:** the drawn line is 0.0 m inside the outline. It comes nearest at the corner of
  East Federal and North 2nd Streets, where it crosses both streets to reach Bates Street; it walks
  the south (far) sidewalk of East Federal. Stop 7 is on the west sidewalk of Chamberlayne Avenue,
  across the avenue from the outline.
- **Distances** are along the drawn line (the sidewalks' own geometry), rounded to 10 m in the
  directions; times at 80 m a minute.
- What the map cannot tell: whether the sidewalks, curb ramps and signals are there and working on
  the day, lighting, traffic, or construction. Nobody has walked the route for this audit.

## Stop 1 to stop 2: 283 m

**Directions as printed:** Cross North 2nd Street at the signal. Walk north on the west sidewalk of North 2nd Street for about 260 m, crossing East Jackson Street (marked crosswalk, no signal).

| Step | OSM way | Length | Notes |
|---|---|---|---|
| walk south, east sidewalk of North 2nd Street | w1205384874 | 6 m | |
| cross North 2nd Street (w374649613, highway=tertiary, lanes=2, maxspeed=25 mph) | w1205384858 | 16 m | crossing=traffic_signals |
| walk north, west sidewalk of North 2nd Street | w1205384878 | 43 m | |
| cross unnamed (w153958861, highway=service) | w1205384877 | 5 m | crossing=unmarked, crossing:markings=no |
| walk north, west sidewalk of North 2nd Street | w1210906701 | 55 m | |
| cross East Jackson Street (w6039534, highway=tertiary, lanes=2, maxspeed=25 mph) | w1210906698 | 10 m | crossing=marked, crossing:markings=yes |
| walk north, west sidewalk of North 2nd Street | w1205384865 | 147 m | |

## Stop 2 to stop 3: 147 m

**Directions as printed:** Walk west on the south sidewalk of East Duval Street for about 80 m. Cross East Duval Street (no marked crosswalk). Walk north on the east sidewalk of North 1st Street, onto the bridge over the highway, for about 50 m.

| Step | OSM way | Length | Notes |
|---|---|---|---|
| walk north, west sidewalk of North 2nd Street | w1205384865 | 2 m | |
| walk west, south sidewalk of East Duval Street | w1349721549 | 82 m | |
| cross East Duval Street (w54172720, highway=tertiary, lanes=2, maxspeed=25 mph) | w1485475443 | 10 m | crossing=unmarked, crossing:markings=no |
| walk north, south sidewalk of North 1st Street | w1485475442 | 2 m | |
| walk north, east sidewalk of North 1st Street | w1485475448 | 15 m | |
| walk north, east sidewalk of North 1st Street, on the bridge | w1485475447 | 35 m | |

## Stop 3 to stop 4: 426 m

**Directions as printed:** Walk north on the east sidewalk of North 1st Street, off the bridge, for about 240 m, crossing East Baker and East Charity Streets (marked crosswalks, no signals). Walk east on the south sidewalk of East Federal Street for about 90 m. Cross East Federal and North 2nd Streets (no marked crosswalks). Walk south on the east sidewalk of North 2nd Street for about 70 m.

| Step | OSM way | Length | Notes |
|---|---|---|---|
| walk north, east sidewalk of North 1st Street, on the bridge | w1485475447 | 33 m | |
| walk north, east sidewalk of North 1st Street | w1485475450 | 6 m | |
| cross East Baker Street (w6035888, highway=residential, maxspeed=25 mph) | w1485475440 | 11 m | crossing=uncontrolled, crossing:markings=lines, crossing:island=no |
| walk north, east sidewalk of North 1st Street | w1483868675, w1483868683, w1483868682 | 91 m | |
| walk north, footway (sidewalk) | w1483868682 | 1 m | |
| cross East Charity Street (w6041132, highway=residential, maxspeed=25 mph); North 1st Street (w38006095, highway=tertiary, maxspeed=25 mph) | w1483868674 | 12 m | crossing=uncontrolled, crossing:markings=yes |
| walk north, east sidewalk of North 1st Street | w1306725562, w1306725623 | 89 m | |
| walk east, south sidewalk of East Federal Street | w1306725623 | 87 m | |
| walk north, west sidewalk of North 2nd Street | w1306725623 | 1 m | |
| cross East Federal Street (w6039240, highway=residential, maxspeed=25 mph) | w1306725633 | 9 m | crossing=unmarked, crossing:markings=no |
| cross Avenue D (w174322625, highway=service); North 2nd Street (w6033312, highway=residential, maxspeed=25 mph) | w1306725636 | 18 m | crossing=unmarked, crossing:markings=no |
| walk south, east sidewalk of North 2nd Street | w1306725612 | 69 m | |

## Stop 4 to stop 5: 1058 m

**Directions as printed:** Walk north on the east sidewalk of North 2nd Street for about 70 m. Cross North 2nd and East Federal Streets (no marked crosswalks). Walk west on the south sidewalk of East Federal Street for about 90 m. Walk south on the east sidewalk of North 1st Street, across the bridge over the highway, for about 440 m, crossing East Charity Street (marked crosswalk, no signal), then East Baker Street (marked crosswalk, no signal), then East Duval Street (no marked crosswalk). Cross North 1st Street (marked crosswalk, no signal). Walk west on the north sidewalk of East Jackson Street for about 80 m. Cross East Jackson and Saint James Streets (no marked crosswalks). Walk west on the south sidewalk of West Jackson Street for about 140 m. Cross West Jackson Street (no marked crosswalk). Walk north on the east sidewalk of Price Street for about 50 m. Walk east on the south sidewalk of West Duval Street for about 100 m.

| Step | OSM way | Length | Notes |
|---|---|---|---|
| walk north, east sidewalk of North 2nd Street | w1306725612 | 69 m | |
| cross Avenue D (w174322625, highway=service); North 2nd Street (w6033312, highway=residential, maxspeed=25 mph) | w1306725636 | 18 m | crossing=unmarked, crossing:markings=no |
| cross East Federal Street (w6039240, highway=residential, maxspeed=25 mph) | w1306725633 | 9 m | crossing=unmarked, crossing:markings=no |
| walk south, west sidewalk of North 2nd Street | w1306725623 | 1 m | |
| walk west, south sidewalk of East Federal Street | w1306725623 | 87 m | |
| walk south, east sidewalk of North 1st Street | w1306725623, w1306725562 | 89 m | |
| cross East Charity Street (w6041132, highway=residential, maxspeed=25 mph); North 1st Street (w38006095, highway=tertiary, maxspeed=25 mph) | w1483868674 | 12 m | crossing=uncontrolled, crossing:markings=yes |
| walk south, footway (sidewalk) | w1483868682 | 1 m | |
| walk south, east sidewalk of North 1st Street | w1483868682, w1483868683, w1483868675 | 91 m | |
| cross East Baker Street (w6035888, highway=residential, maxspeed=25 mph) | w1485475440 | 11 m | crossing=uncontrolled, crossing:markings=lines, crossing:island=no |
| walk south, east sidewalk of North 1st Street | w1485475450 | 6 m | |
| walk south, east sidewalk of North 1st Street, on the bridge | w1485475447 | 69 m | |
| walk south, east sidewalk of North 1st Street | w1485475448 | 15 m | |
| walk south, south sidewalk of North 1st Street | w1485475442 | 2 m | |
| cross East Duval Street (w54172720, highway=tertiary, lanes=2, maxspeed=25 mph) | w1485475443 | 10 m | crossing=unmarked, crossing:markings=no |
| walk south, east sidewalk of North 1st Street | w1349721548 | 134 m | |
| cross North 1st Street (w6035187, highway=tertiary, lanes=1, maxspeed=25 mph) | w1205384863 | 17 m | crossing=marked, crossing:markings=yes |
| walk west, north sidewalk of East Jackson Street | w1205384872 | 45 m | |
| cross unnamed (w153958852, highway=service) | w1205384891 | 7 m | crossing=unmarked, crossing:markings=no |
| walk west, north sidewalk of East Jackson Street | w1213464538 | 38 m | |
| cross East Jackson Street (w692841331, highway=residential, maxspeed=25 mph) | w1213464537 | 10 m | crossing=unmarked, crossing:markings=no |
| cross Saint James Street (w6039065, highway=residential, maxspeed=25 mph) | w1213464536 | 11 m | crossing=unmarked, crossing:markings=no |
| walk west, south sidewalk of West Jackson Street | w1205384882 | 140 m | |
| cross West Jackson Street (w6035330, highway=residential, maxspeed=25 mph) | w1213464543 | 9 m | crossing=unmarked, crossing:markings=no |
| walk north, east sidewalk of Price Street | w1483868751 | 53 m | |
| walk east, south sidewalk of West Duval Street | w1483868747 | 23 m | |
| cross unnamed (w1220285854, highway=service) | w1483868748 | 8 m | crossing=unmarked, crossing:markings=no |
| walk east, south sidewalk of West Duval Street | w1483868749 | 69 m | |
| walk south, west sidewalk of Cameo Street | w1483868750 | 4 m | |

## Stop 5 to stop 6: 999 m

**Directions as printed:** Walk west on the south sidewalk of West Duval Street for about 100 m. Walk south on the east sidewalk of Price Street for about 50 m. Cross West Jackson Street (no marked crosswalk). Walk east on the south sidewalk of West Jackson Street for about 140 m. Walk south on the west sidewalk of Saint James Street for about 100 m. Cross Saint James Street (no marked crosswalk). Walk east on the north sidewalk of East Leigh Street for about 80 m. Cross East Leigh Street at the signal. Walk west on the south sidewalk of East Leigh Street for about 90 m. Cross Saint James Street (crosswalk, no signal). Walk west on the south sidewalk of West Leigh Street for about 120 m, crossing North Adams Street (marked crosswalk, no signal). Cross West Leigh Street at the signal. Walk north on the west sidewalk of Chamberlayne Parkway for about 180 m, crossing Price and West Jackson Streets (no marked crosswalks). Cross Saint Peter and West Duval Streets (no marked crosswalks). Walk north on the west sidewalk of Chamberlayne Parkway, onto the bridge over the highway, for about 30 m.

| Step | OSM way | Length | Notes |
|---|---|---|---|
| walk north, west sidewalk of Cameo Street | w1483868750 | 4 m | |
| walk west, south sidewalk of West Duval Street | w1483868749 | 69 m | |
| cross unnamed (w1220285854, highway=service) | w1483868748 | 8 m | crossing=unmarked, crossing:markings=no |
| walk west, south sidewalk of West Duval Street | w1483868747 | 23 m | |
| walk south, east sidewalk of Price Street | w1483868751 | 53 m | |
| cross West Jackson Street (w6035330, highway=residential, maxspeed=25 mph) | w1213464543 | 9 m | crossing=unmarked, crossing:markings=no |
| walk east, south sidewalk of West Jackson Street | w1205384882 | 140 m | |
| walk south, west sidewalk of Saint James Street | w1205384882 | 47 m | |
| cross unnamed (w153958850, highway=service) | w1205384883 | 5 m | crossing=unmarked, crossing:markings=no |
| walk south, west sidewalk of Saint James Street | w1122219190 | 50 m | |
| cross Saint James Street (w6039065, highway=residential, maxspeed=25 mph) | w1122219191 | 11 m | crossing=unmarked, crossing:markings=no |
| walk east, north sidewalk of East Leigh Street | w1205384889 | 6 m | |
| cross unnamed (w297841777, highway=service) | w1205384890 | 6 m | crossing=unmarked, crossing:markings=no |
| walk east, north sidewalk of East Leigh Street | w1122219192 | 75 m | |
| cross East Leigh Street (w692841321, highway=primary, lanes=4, maxspeed=25 mph) | w1022715851 | 17 m | crossing=traffic_signals, crossing:markings=zebra |
| walk west, south sidewalk of East Leigh Street | w1022715849 | 88 m | |
| cross Saint James Street (w6039065, highway=residential, maxspeed=25 mph) | w1022715850 | 10 m | crossing=uncontrolled |
| walk west, south sidewalk of West Leigh Street | w1193236968 | 85 m | |
| walk west, footway (sidewalk) | w1193236968 | 2 m | |
| cross North Adams Street (w354923839, highway=secondary, lanes=2, maxspeed=25 mph) | w1122219201 | 17 m | crossing=uncontrolled, crossing:markings=zebra |
| walk west, south sidewalk of West Leigh Street | w1198193570 | 13 m | |
| cross West Leigh Street (w38256518, highway=primary, lanes=4, maxspeed=25 mph) | w1122219166 | 17 m | crossing=traffic_signals, crossing:markings=zebra |
| walk north, west sidewalk of Chamberlayne Parkway | w1193261617 | 4 m | |
| walk north, east sidewalk of Price Street | w1122219167 | 5 m | |
| walk north, west sidewalk of Chamberlayne Parkway | w1122219167 | 18 m | |
| walk north, footway (sidewalk) | w1122219167 | 3 m | |
| cross Price Street (w6038456, highway=residential, maxspeed=25 mph) | w1122219215 | 13 m | crossing=unmarked, crossing:markings=no |
| walk north, west sidewalk of Chamberlayne Parkway | w1122219169 | 114 m | |
| cross West Jackson Street (w6035330, highway=residential, maxspeed=25 mph) | w1122219205 | 13 m | crossing=unmarked, crossing:markings=no, crossing:island=no |
| walk north, west sidewalk of Chamberlayne Parkway | w1122219204 | 13 m | |
| cross Saint Peter Street (w6038266, highway=residential, maxspeed=25 mph) | w1122219223 | 11 m | crossing=unmarked, crossing:markings=no, crossing:island=no |
| cross West Duval Street (w54172719, highway=residential, maxspeed=25 mph) | w1122219222 | 12 m | crossing=unmarked, crossing:markings=no, crossing:island=no |
| walk north, west sidewalk of Chamberlayne Parkway | w1122219221 | 4 m | |
| walk north, west sidewalk of Chamberlayne Parkway, on the bridge | w1122219208 | 31 m | |

## Stop 6 to stop 7: 143 m

**Directions as printed:** Walk north on the west sidewalk of Chamberlayne Parkway, off the bridge, for about 50 m. Walk north on the west sidewalk of Chamberlayne Avenue for about 80 m.

| Step | OSM way | Length | Notes |
|---|---|---|---|
| walk north, west sidewalk of Chamberlayne Parkway, on the bridge | w1122219208 | 38 m | |
| walk north, west sidewalk of Chamberlayne Avenue | w1122219207 | 5 m | |
| walk west, south sidewalk of West Baker Street | w1122219207 | 5 m | |
| walk north, west sidewalk of Chamberlayne Avenue | w1122219207 | 24 m | |
| cross unnamed (w323636852, highway=service, maxspeed=25 mph) | w1122219225 | 13 m | crossing=uncontrolled |
| walk west, north sidewalk of West Baker Street | w1225827584 | 2 m | |
| walk north, footway (sidewalk) | w1215813972 | 2 m | |
| walk north, west sidewalk of Chamberlayne Avenue | w1215813972 | 55 m | |

## Stop 7 to stop 8: 1134 m

**Directions as printed:** Walk south on the west sidewalk of Chamberlayne Avenue for about 90 m. Walk south on the west sidewalk of Chamberlayne Parkway, across the bridge over the highway, for about 70 m. Cross West Duval and Saint Peter Streets (no marked crosswalks). Walk south on the west sidewalk of Chamberlayne Parkway for about 180 m, crossing West Jackson and Price Streets (no marked crosswalks). Cross West Leigh Street at the signal. Walk east on the south sidewalk of West Leigh Street for about 120 m, crossing North Adams Street (marked crosswalk, no signal). Cross Saint James Street (crosswalk, no signal). Walk east on the south sidewalk of East Leigh Street for about 290 m, crossing North 1st and North 2nd Streets (signals). Cross East Leigh and North 3rd Streets at the signals. Walk east on the north sidewalk of East Leigh Street for about 280 m, crossing North 4th Street (signal).

| Step | OSM way | Length | Notes |
|---|---|---|---|
| walk south, west sidewalk of Chamberlayne Avenue | w1215813972 | 55 m | |
| walk south, footway (sidewalk) | w1215813972 | 2 m | |
| walk east, north sidewalk of West Baker Street | w1225827584 | 2 m | |
| cross unnamed (w323636852, highway=service, maxspeed=25 mph) | w1122219225 | 13 m | crossing=uncontrolled |
| walk south, west sidewalk of Chamberlayne Avenue | w1122219207 | 24 m | |
| walk east, south sidewalk of West Baker Street | w1122219207 | 5 m | |
| walk south, west sidewalk of Chamberlayne Avenue | w1122219207 | 5 m | |
| walk south, west sidewalk of Chamberlayne Parkway, on the bridge | w1122219208 | 69 m | |
| walk south, west sidewalk of Chamberlayne Parkway | w1122219221 | 4 m | |
| cross West Duval Street (w54172719, highway=residential, maxspeed=25 mph) | w1122219222 | 12 m | crossing=unmarked, crossing:markings=no, crossing:island=no |
| cross Saint Peter Street (w6038266, highway=residential, maxspeed=25 mph) | w1122219223 | 11 m | crossing=unmarked, crossing:markings=no, crossing:island=no |
| walk south, west sidewalk of Chamberlayne Parkway | w1122219204 | 13 m | |
| cross West Jackson Street (w6035330, highway=residential, maxspeed=25 mph) | w1122219205 | 13 m | crossing=unmarked, crossing:markings=no, crossing:island=no |
| walk south, west sidewalk of Chamberlayne Parkway | w1122219169 | 114 m | |
| cross Price Street (w6038456, highway=residential, maxspeed=25 mph) | w1122219215 | 13 m | crossing=unmarked, crossing:markings=no |
| walk south, footway (sidewalk) | w1122219167 | 3 m | |
| walk south, west sidewalk of Chamberlayne Parkway | w1122219167 | 18 m | |
| walk south, east sidewalk of Price Street | w1122219167 | 5 m | |
| walk south, west sidewalk of Chamberlayne Parkway | w1193261617 | 4 m | |
| cross West Leigh Street (w38256518, highway=primary, lanes=4, maxspeed=25 mph) | w1122219166 | 17 m | crossing=traffic_signals, crossing:markings=zebra |
| walk east, south sidewalk of West Leigh Street | w1198193570 | 13 m | |
| cross North Adams Street (w354923839, highway=secondary, lanes=2, maxspeed=25 mph) | w1122219201 | 17 m | crossing=uncontrolled, crossing:markings=zebra |
| walk east, footway (sidewalk) | w1193236968 | 2 m | |
| walk east, south sidewalk of West Leigh Street | w1193236968 | 85 m | |
| cross Saint James Street (w6039065, highway=residential, maxspeed=25 mph) | w1022715850 | 10 m | crossing=uncontrolled |
| walk east, south sidewalk of East Leigh Street | w1022715849 | 88 m | |
| cross North 1st Street (w6035187, highway=tertiary, lanes=1, maxspeed=25 mph) | w1122219219 | 16 m | crossing=traffic_signals, crossing:markings=zebra |
| walk east, south sidewalk of East Leigh Street | w1125516611 | 83 m | |
| cross North 2nd Street (w692841319, highway=tertiary, lanes=2, maxspeed=25 mph) | w1205384860 | 16 m | crossing=traffic_signals |
| walk east, south sidewalk of East Leigh Street | w1125516616 | 83 m | |
| cross East Leigh Street (w692841320, highway=primary, maxspeed=25 mph) | w1125516617 | 17 m | crossing=traffic_signals, crossing:markings=zebra, crossing:island=no |
| cross North 3rd Street (w1468119904, highway=secondary, lanes=5, maxspeed=25 mph) | w1125516620 | 21 m | crossing=traffic_signals, crossing:markings=zebra, crossing:island=no |
| walk east, north sidewalk of East Leigh Street | w1125516622, w1125516621 | 75 m | |
| cross North 4th Street (w6033497, highway=tertiary) | w1210121460 | 20 m | crossing=traffic_signals |
| walk east, north sidewalk of East Leigh Street | w1125516638 | 103 m | |
| walk south, footway (sidewalk) | w1125516638 | 3 m | |
| walk east, north sidewalk of East Leigh Street | w1125516638 | 79 m | |

## Every street crossing on the walk

| Crossing (OSM way) | Street | Tags | Legs |
|---|---|---|---|
| w1205384858 | North 2nd Street (tertiary, 2 lanes) | crossing=traffic_signals | 1->2 |
| w1210906698 | East Jackson Street (tertiary, 2 lanes) | crossing=marked, crossing:markings=yes | 1->2 |
| w1485475443 | East Duval Street (tertiary, 2 lanes) | crossing=unmarked, crossing:markings=no | 2->3, 4->5 |
| w1485475440 | East Baker Street (residential) | crossing=uncontrolled, crossing:markings=lines, crossing:island=no | 3->4, 4->5 |
| w1483868674 | East Charity Street (residential); North 1st Street (tertiary) | crossing=uncontrolled, crossing:markings=yes | 3->4, 4->5 |
| w1306725633 | East Federal Street (residential) | crossing=unmarked, crossing:markings=no | 3->4, 4->5 |
| w1306725636 | Avenue D (service); North 2nd Street (residential) | crossing=unmarked, crossing:markings=no | 3->4, 4->5 |
| w1205384863 | North 1st Street (tertiary, 1 lanes) | crossing=marked, crossing:markings=yes | 4->5 |
| w1213464537 | East Jackson Street (residential) | crossing=unmarked, crossing:markings=no | 4->5 |
| w1213464536 | Saint James Street (residential) | crossing=unmarked, crossing:markings=no | 4->5 |
| w1213464543 | West Jackson Street (residential) | crossing=unmarked, crossing:markings=no | 4->5, 5->6 |
| w1122219191 | Saint James Street (residential) | crossing=unmarked, crossing:markings=no | 5->6 |
| w1022715851 | East Leigh Street (primary, 4 lanes) | crossing=traffic_signals, crossing:markings=zebra | 5->6 |
| w1022715850 | Saint James Street (residential) | crossing=uncontrolled | 5->6, 7->8 |
| w1122219201 | North Adams Street (secondary, 2 lanes) | crossing=uncontrolled, crossing:markings=zebra | 5->6, 7->8 |
| w1122219166 | West Leigh Street (primary, 4 lanes) | crossing=traffic_signals, crossing:markings=zebra | 5->6, 7->8 |
| w1122219215 | Price Street (residential) | crossing=unmarked, crossing:markings=no | 5->6, 7->8 |
| w1122219205 | West Jackson Street (residential) | crossing=unmarked, crossing:markings=no, crossing:island=no | 5->6, 7->8 |
| w1122219223 | Saint Peter Street (residential) | crossing=unmarked, crossing:markings=no, crossing:island=no | 5->6, 7->8 |
| w1122219222 | West Duval Street (residential) | crossing=unmarked, crossing:markings=no, crossing:island=no | 5->6, 7->8 |
| w1122219219 | North 1st Street (tertiary, 1 lanes) | crossing=traffic_signals, crossing:markings=zebra | 7->8 |
| w1205384860 | North 2nd Street (tertiary, 2 lanes) | crossing=traffic_signals | 7->8 |
| w1125516617 | East Leigh Street (primary) | crossing=traffic_signals, crossing:markings=zebra, crossing:island=no | 7->8 |
| w1125516620 | North 3rd Street (secondary, 5 lanes) | crossing=traffic_signals, crossing:markings=zebra, crossing:island=no | 7->8 |
| w1210121460 | North 4th Street (tertiary) | crossing=traffic_signals | 7->8 |

Distinct street crossings by OSM tag: marked 2, traffic_signals 8, uncontrolled 4, unmarked 11.
No crossing of a motorway, a motorway ramp or a primary road without crossing=traffic_signals (route.py leaves those out of the graph and asserts it).
