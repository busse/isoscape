# Rain maps for the floods series: Tropical Storm Gaston, Aug. 30, 2004

isoscape's first meteorological product: where the rain fell over Richmond, hour by hour, and
how much fell on the land that drains to Shockoe Bottom. Built with Claude under Chris Busse's
direction (see `pages/artist-statement.md`). Every number below is in `data/rain.json` with its
source; "computed" means computed here, by the scripts named.

Working draft, November 23, 2026. Case-study record: `drafts/richmond-floods/casestudy/`,
steps 30 to 36.

## What was reachable (Nov. 23, 2026, from the cloud container)

| Source | Reached? | Used for |
|---|---|---|
| NEXRAD Level II, KAKQ, Unidata bucket on AWS (`unidata-nexrad-level2`) | yes, 268 volumes, 602 MB, MD5-checked | radar rain, 11:30 UTC Aug. 30 to 06:30 UTC Aug. 31 |
| NEXRAD Level II, `noaa-nexrad-level2` bucket | no: HTTP 403 | (the Unidata bucket holds the same files) |
| AORC v1.1, 1 km hourly, `noaa-nws-aorc-v1-1-1km` | yes, anonymous Zarr | a gauge-corrected reference |
| NCEP Stage IV at NSF NCAR EOL (dataset 21.093) | no: its order form answers "Dataset is not currently available"; an order form is out of bounds anyway | |
| NCEP Stage IV, Iowa Environmental Mesonet archive | yes, GRIB1 hourly, 6-hourly, 24-hourly | a second gauge-corrected reference |
| NCEI Global Hourly (RIC), GHCN-Daily, HOMR station list | yes | gauges, radar position |
| NOAA Atlas 14 PFDS point answers | yes | return periods |
| USGS 3DEP exportImage | yes | the watershed |
| US Census TIGER 2023 (counties, area water) | yes | map base |
| NHC HURDAT2 | yes | the track |

Nothing was refused that this work needed, so the planning session has nothing it must fetch on
the Mac. The raw radar volumes were deleted after processing (disk); `fetch.py` refetches them.

## Rerun

```sh
python3 tools/floods/rain/fetch.py WORK/raw --only radar     # or all; stdlib only
python3 tools/floods/rain/radar.py WORK/raw WORK/derived/radar   # Py-ART (pip install arm-pyart)
python3 tools/floods/rain/aorc.py WORK/derived/aorc_raw.npz      # zarr, s3fs
python3 tools/floods/rain/watershed.py WORK/dem/dem10.npy WORK/derived/watershed.geojson
python3 tools/floods/rain/analyze.py WORK tools/floods/rain/data # rain.json and grids
python3 tools/floods/rain/figures.py OUT                         # plan map, hourly, hyetograph, check, bands
python3 tools/floods/rain/drape.py                               # the GeoJSON isoscape drapes
node bin/isoscape.js build richmond-gaston-rain --with rain --year 2004 --png --width 3400   # treatment (i)
node bin/isoscape.js build richmond-gaston-rain --year 2004 --png --width 3400               # base for (ii)
node bin/isoscape.js build richmond-gaston-rain-x3 --year 2004 --png --width 3400            # base for the explainer
python3 tools/floods/rain/iso.py OUT/richmond-gaston-rain OUT [--explainer]
```

All of these are dev tools (numpy, scipy, matplotlib, shapely, Py-ART, pygrib, zarr).
isoscape's build gains no dependency. The two regions read the `richmond-streetcars` data
cache (`"data"` in the region file).

## Method, in short

- **Radar.** Lowest tilt (0.5 degrees) reflectivity from each 4.2-minute volume (the tilts and
  cycle point to VCP 12; the 2004 files carry no VCP number Py-ART can read), sampled at the
  centers of a 0.005 by 0.00625 degree grid (about 0.55 km) by nearest ray and gate. dBZ under
  10 is no rain; over 53 is capped. Rate from Z = 250 R^1.2 (tropical, used by the NWS that
  day) and, for comparison, Z = 300 R^1.4. Linear in time between scans, summed by minute.
  KAKQ is 72 km from 17th and Main (azimuth 329 degrees): the beam center there is about
  1,000 m above sea level and the beam about 1.2 km wide; at the watershed's north edge
  1,090 m; at Ashland, 89 km out, 1,310 m and 1.5 km wide. Rain that grows below the beam, which
  is common in tropical rain, is missed, more so farther out. No clutter showed in clear air
  before the storm (12 to 14 UTC). The 0.9-degree tilt gives 6 percent less over the watershed.
- **Correction to gauges.** Raw tropical radar was low at the official gauges (airport by a
  factor of 1.41, Ashland 2.49, Sandston 1.62) and high at some unofficial reports in the city
  (Science Museum 0.68). One factor for the whole map (1.43, from the official gauges) was
  tested and rejected: predicting each gauge without itself, it misses by a typical factor of
  1.53, worse than no correction (1.49). The correction used is local: the radar times
  exp(inverse-distance-weighted mean of log(gauge / radar)), weight 1 / (d^2 + L^2), L = 5 km,
  unofficial reports at half weight. Its typical miss is a factor of 1.44. At the watershed's
  center the local factor is 1.12 (1.05 to 1.27 for L from 3 to 20 km). Point values remain
  uncertain by about 40 percent either way; the watershed average, which averages many cells,
  less.
- **The range** for the watershed is every defensible estimate of its total: raw radar 9.15 in,
  local corrections 9.85 to 11.60 in, AORC 8.56 in, Stage IV hourly 9.07 in and its 24-hour
  analysis 10.79 in. The hourly range scales the best estimate by the low and high ends.
- **Watershed.** The land surface draining to the Bottom's low ground (under 8 m within 400 m
  of 17th and Main), by priority-flood on 3DEP at 0.0001 degrees (about 9 by 11 m): 31.5 km2,
  7,780 acres. The city gives about 8,000 acres for its Shockoe watershed (Shockoe Small Area
  Plan, 2023, p42). The isoscape `richmond-streetcars` cache (3DEP, 5 m) gives 28.7 km2: its
  east edge stops at the divide, and it sends a downtown wedge (along the Downtown Expressway
  trench) to the river instead. In a city whose creek is a pipe, the surface answer and the
  sewer answer differ; this is the surface answer.

## The numbers (best estimate, with range)

- Watershed average, storm total: **10.3 in** (8.6 to 11.6).
- Peak hour over the watershed: **5 to 6 p.m. EDT, 2.2 in** (1.8 to 2.5). Every hour from 2 to
  8 p.m. brought 1.3 to 2.2 in.
- Water that fell on the watershed: **8.3 million cubic meters, about 2.2 billion gallons**
  (1.8 to 2.5 billion), computed as average depth times area. For scale, the city's Shockoe Retention
  Basin holds 35 million gallons (DPU Combined Sewer System Final Plan Report, 2024, p36).
- Return periods (NOAA Atlas 14 Vol. 2 v3 at the watershed's center; point frequencies):

| Duration | Watershed average, in (range) | about | Worst radar cell in it, in | about |
|---|---|---|---|---|
| 1 h | 2.2 (1.8 to 2.5) | 10-year (4 to 20) | 3.7 | 300-year |
| 2 h | 3.8 (3.1 to 4.2) | 60-year (20 to 130) | 5.5 | 800-year |
| 3 h | 5.5 (4.6 to 6.2) | 400-year (120 to 1,000) | 7.0 | beyond 1,000 |
| 6 h | 10.0 (8.3 to 11.2) | beyond 1,000 (all but AORC) | 11.2 | beyond 1,000 |
| 12 h | 10.3 (8.6 to 11.6) | 900-year (300 to beyond 1,000) | 11.5 | beyond 1,000 |

What can be said: over six hours, the rain on the whole Shockoe watershed reached or passed
NOAA's 1-in-1,000-year six-hour amount for a single point (8.04 in), by every estimate but
AORC's (7.9 in, about 900-year). Because Atlas 14 is for points, a whole-watershed average
should be compared with smaller (areally reduced) depths, which would make it rarer still.
What cannot be said: a return period past 1,000 years (Atlas 14 stops there and its data end
before 2004), anything about the flood's own return period (a flood depends on pipes, ground
and the river, not rain alone), or a figure for one street (the radar sees about 1.5 km).
"A 1,000-year flood" is not supported; "rain at or beyond the 1,000-year six-hour amount over
the whole watershed" is, with the caveats above. The hour-by-hour peak was ordinary (about a
10-year hour): it was six hours of it, without a break, that was rare.

The only report inside the surface watershed, the Science Museum's 6.56 in (unofficial; place
approximate), is well under the radar's 9.8 in there. The radar may be high there, or the
report incomplete; neither can be checked now.

## Pictures

`figures.py`: `plan-map` (storm total, 2-inch bands, gauges, watershed, city line, track note),
`hourly` (2 p.m. to 10 p.m. EDT, one panel an hour), `hyetograph` (watershed inches per hour
with range, the airport gauge, five timed events), `radar-vs-gauges` (before and after).
`iso.py`: `iso-composite` (treatment ii) and `explainer`. Treatment (i) is isoscape's own build
with the switch `rain` (`history/gaston-2004.json`).

**Treatment (i), drawn by isoscape.** The bands are a `Tint` (the same graded ground the 1937
grades use) read from `data/iso-drape.geojson`, painted strip by strip and draped like any
ground cover. One new field, `Tint.tones: "rain"`, asks for one hue, light to deep, instead of
the four grade tones; a value named `outline` takes the mark line (the watershed's ring). The
code is `src/tint-tones.ts`; `scene.ts` hands the renderer `tintPalette(pal, tint)`, which is
the same palette object for every scene without it. `render.ts` is untouched. Proved byte for
byte on `richmond-downtown` and on `richmond-1937 --with grades` (a tinted build): SVG and
HTML identical before and after. Its weakness is the picture: the whole view lies in 8 to 12
inches, so the bands differ little, and any rain color on the ground risks reading as standing
water (the first blue round did; the violet-gray kept does not, but is faint).

**Treatment (ii), composite.** isoscape's drawing without rain, with the rain laid over it as a
see-through wash and labeled isohyets, the watershed line and the low point, placed with
isoscape's own `locate`. Clearer, and it keeps the city readable. Recommended for now; (i) is the
path if the series wants the rain inside the drawing itself (print, explorer).

## The same pipeline for other floods

The radar steps need NEXRAD (from about 1995 at KAKQ). Before that, the rain comes from gauges
and published analyses only. What each could honestly show:

- **Camille, Aug. 19 to 20, 1969.** The flood in Richmond was the James, from 25 to 27 in of
  rain in Nelson County 150 km upstream. A rain map would be the WPC/Roth storm-total analysis
  (a contoured GIF from gauges; no grid), georeferenced and traced into bands, plus the gauge
  table. Honest scale: the state, not the city. Atlas 14 return periods only at gauges.
- **Agnes, June 1972.** Also a river flood. The WPC daily maps (June 18 to 23) and gauges, at
  the scale of the James basin; a hyetograph from any hourly gauge in NCEI's HPD archive.
- **Juan, November 1985.** The flood rain fell after Juan, in a separate system (WPC notes it is
  not in Juan's total); the map should be of the Nov. 3 to 6 rain over the upper James, from
  gauges and the NWS's later analyses. No radar archive.
- **Fran, September 1996.** WSR-88D Level II from KAKQ may exist for 1996 (check the bucket's
  1996 listing); if so, the same pipeline runs, with gauges from GHCN-Daily and HPD. The James
  flood came from rain upstream, so the map is regional.
- **Isabel, September 2003.** Radar, Stage IV and AORC all exist; the same pipeline runs as is.
  Rain at Richmond was moderate (4.32 in at RIC); the story there is wind and surge downriver.

For the river floods, the honest rain picture is a basin-wide total from gauges, with a note
that Richmond's water came from far upstream. Only Gaston (and the pluvial floods since, such
as July 2025) is a rain-on-the-city story that a city-scale radar map can tell.
