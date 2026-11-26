# 32. The Shockoe Creek surface watershed (20:13 to 20:33)

- The isoscape caches: `richmond-i195-rocketts` (2 m) stops at 37.546 N, far short of the
  head; `richmond-streetcars` (3DEP, 5 m) reaches 37.617 N but its east edge (-77.3928) stops
  on the divide itself. So a fresh 3DEP grid was fetched at 0.0001 degrees (about 9 by 11 m)
  over -77.52 to -77.37, 37.515 to 37.66, asked for with pixels square in degrees so it covers
  exactly the box.
- `ws-01.png`: priority-flood watershed of the Bottom's low ground: 31.5 km2, 7,780 acres. The
  city's figure for its Shockoe watershed is about 8,000 acres (Shockoe Small Area Plan, 2023,
  p42). The head is near Brookland Park Boulevard, just south of Bryan Park, which drains the
  other way (Upham Brook). The west lobe takes in the Museum District and Scott's Addition.
- `ws-02-river-check.png`: the James (TIGER) against the outline and the DEM; they agree. (A
  worry from the small-multiple panels, that the river crossed the watershed, was only the
  thick line at small scale.)
- `ws-03-two-dems.png`: the same method on the 5 m cache gives 28.7 km2: it sends a downtown
  wedge along the Downtown Expressway trench to the river. In a city the surface answer turns
  on trenches and embankments; the sewershed differs again. Basin rain is the same either way
  (10.31 against 10.34 in).
