# Rainfall and meteorological data for Gaston and the flood series

Source keys resolve in `sources.md`. All sources read November 23, 2026. "Public domain" below
means a US federal work with no stated restriction; check each provider's notice before printing.

**The short version.** For Gaston, the best point data are the airport's hourly record [S8], the
NHC and NWS gauge lists [S1], [S2] and GHCN-Daily [S9]. The best gridded data are Stage IV
(4 km, hourly, from 2002) [S46] and AORC (1 km, hourly, from 1979) [S14]; I extracted AORC, and it
runs low against gauges. Radar (KAKQ Level II) exists for every scan that day [S47] and could give a
finer storm total with work. No gauge stood in the Shockoe watershed. NOAA Atlas 14 [S13] puts the
watershed rain at roughly a 500- to 1,000-year six-hour amount.

## 1. Gauge totals around Richmond, Aug. 30, 2004

| Station | Inches | Period | Kind | Source |
|---|---|---|---|---|
| Richmond (West End) | 12.60 | storm | unofficial | [S1 p8, Table 3], [S2] |
| Richmond (Math & Science Center) | 12.30 | storm | unofficial | [S1 p8], [S2] |
| Mechanicsville | 10.70 | storm | unofficial | [S1 p8], [S2] |
| Ashland (Hanover Co. airport ASOS, USW00093775) | 10.61 | Aug. 30 | official ASOS | [S1 p8], [S9] |
| Sandston (coop USC00447541) | 8.10 | 24 h to morning of Aug. 31 | coop | [S1 p8], [S9] |
| Richmond Intl. Airport (USW00013740) | 6.68 | Aug. 30 | official | [S1 p8], [S8], [S9] |
| Richmond (Science Museum) | 6.56 | storm | unofficial | [S1 p8], [S2] |
| Richmond (St. Christopher's School) | 6.40 | storm | unofficial | [S1 p8], [S2] |
| Chester | 6.20 | storm | | [S2] |
| St. Mary's School | 5.80 | storm | | [S2] |
| Winterpock (coop USC00449213) | 5.69 (plus 0.24 the day before) | to morning Aug. 31 | coop | [S2], [S9] |
| Hopewell (coop USC00444101) | 2.32 + 4.63 | mornings Aug. 30 and 31 | coop | [S9] |
| Ashland (coop USC00440327) | 4.63, then missing | morning Aug. 30 | coop | [S9] |
| WWBT TV-12 | 4.80 | storm | | [S2] |
| Clover Hill H.S.; Midlothian | 4.30; 4.30 | storm | | [S2] |
| Wakefield (NWS office) | 2.51 | storm | | [S1 p8], [S2] |

- Radar: 10 to 12 in over the city and western Hanover [S2].
- King William: 6 to 14 in in the north of the county [S5 event 5421494].
- The 24-hour Richmond records table on the NWS page ranks Gaston's 6.68 in second, behind 8.79 in
  for Connie in August 1955 [S2]. The full GHCN record also has 7.61 in on June 22, 2018 [S55],
  which the 2004 page predates. By calendar day at the airport, Gaston now ranks third.
- Coop daily values close at the observer's morning reading, so Aug. 30 rain often appears on
  Aug. 31 [S9].
- Exact locations of the unofficial "West End" and "Math & Science Center" gauges: UNCONFIRMED.

## 2. Hourly and sub-hourly rates

| Data | What exists for Aug. 30, 2004 | URL | License | Format |
|---|---|---|---|---|
| ISD / Global Hourly, KRIC | hourly totals plus specials, 1.27 and 2.10 in in successive hours ending 2:54 and 3:54 p.m. EDT; 3-h 3.95 in; 6-h 5.51 in [S8] | https://noaa-global-hourly-pds.s3.amazonaws.com/2004/72401013740.csv | public domain (NOAA Open Data) | CSV; precipitation in field AA1, tenths of mm |
| ASOS 1-minute, RIC (IEM) | all missing from 1 p.m. to 11 p.m. that day [S48] | https://mesonet.agron.iastate.edu/cgi-bin/request/asos1min.py | IEM, free | CSV |
| NCEI Hourly Precipitation Data (HPD v2, coop recording gauges) | not checked; whether any Richmond-area HPD gauge reported that day is UNCONFIRMED | https://www.ncei.noaa.gov/products/land-based-station/hourly-precipitation-data | public domain | CSV |
| Radar FFMP | peaks of 2 to 3+ in/h over a Shockoe sub-basin near 6 p.m. [S3 p5, Fig. 18] | (figure only) | | |
| AORC v1.1 | hourly, 1 km; my extraction below [S14] | s3://noaa-nws-aorc-v1-1-1km/2004.zarr | NOAA Open Data (check notice) | Zarr |

AORC extraction (hour-ending EDT, nearest 1 km cell) [S14]:

| Point | Total | Max 1 h | Max 3 h | Max 6 h |
|---|---|---|---|---|
| Shockoe Bottom (37.5325, -77.430) | 8.55 | 1.57 | 4.10 | 7.75 |
| Mid-valley (37.555, -77.425) | 8.29 | 1.67 | 4.40 | 7.59 |
| Upper valley (37.585, -77.405) | 8.67 | 1.76 | 4.78 | 8.07 |
| RIC airport cell | 6.99 | 2.06 | | |
| Ashland airport cell | 4.57 | | | |
| Max in box 37.35-37.80 N, 77.20-77.70 W | 8.97 at 37.566, -77.444 | | | |

AORC agrees well at the airport (6.99 vs 6.68 in) but is far low at Ashland (4.57 vs 10.61 in),
so its smoothing misses the heaviest cores. Use it for timing and pattern, not for peak totals.
Watershed points and coordinates are my approximations.

## 3. Gridded multi-sensor precipitation

**NCEP Stage IV** [S46]
- URL: https://data.ucar.edu/dataset/ncep-emc-4km-gridded-data-grib-stage-iv-data ; DOI
  https://doi.org/10.5065/D6PG1QDD ; archive at NSF NCAR EOL dataset 21.093.
- Coverage: from 2001-12-31 to present; so Aug. 2004 is covered.
- Resolution: about 4 km polar-stereographic grid; hourly, 6-hourly and 24-hourly analyses.
- Format: GRIB1 for 2004 (GRIB2 for later years).
- License: legal and access constraints "none" in the catalog.
- Not extracted here. Values for Richmond on Aug. 30, 2004: UNCONFIRMED.

**AORC v1.1** [S14]: 1 km (30 arc-second), hourly, 1979 to 2025, Zarr on AWS. Built from Stage IV,
NLDAS and PRISM. Extracted above.

**MRMS**: not available for 2004. MRMS reanalysis coverage of 2004: UNCONFIRMED.

## 4. NEXRAD radar, KAKQ (Wakefield)

- **Level II**: 339 volume scans for Aug. 30, 2004, 00:01 to 23:56 UTC, on the Unidata bucket
  [S47]: https://unidata-nexrad-level2.s3.amazonaws.com/?list-type=2&prefix=2004/08/30/KAKQ/ .
  Free (NOAA Big Data / Unidata). Format: compressed Archive II.
- **Level III** (one-hour, three-hour and storm-total precipitation products): held by NCEI.
  Availability for KAKQ on this date: UNCONFIRMED. Order through NCEI's NEXRAD archive.
- **Geometry** (my calculation): KAKQ is about 72 km (45 miles) south-southeast of Shockoe Bottom.
  The 0.5-degree beam there is roughly 1 km above ground, below the melting level, so a tropical
  rain estimate is reasonable but bright band and evaporation errors are small concerns.
- **How to get a storm total from Level II**: read each volume with Py-ART or wradlib; take the
  lowest clean tilt; convert reflectivity to rain rate with the tropical relation Z = 250 R^1.2
  (the NWS used the tropical Z-R that day, and its one-hour estimates were "only slightly below"
  gauges [S3 p5]); cap hail contamination near 53 dBZ; integrate over time between scans; regrid to
  1 km or finer; then bias-correct with the gauges in section 1 (RIC hourly, Ashland, Sandston,
  Mechanicsville, the two 12-inch reports). A good result could map rain over the Shockoe valley at
  about 1 km, finer than Stage IV.
- WSR-88D one-hour estimate over Richmond at 5 p.m.: Fig. 17 in [S3 p4], image only.

## 5. How rare: NOAA Atlas 14 (Volume 2, Version 3, Ohio River Basin and surrounding states)

Partial-duration depths, inches, downtown Richmond (37.5350, -77.4300) [S13]:

| Duration | 10-yr | 25-yr | 50-yr | 100-yr | 200-yr | 500-yr | 1,000-yr |
|---|---|---|---|---|---|---|---|
| 1 hour | 2.22 | 2.60 | 2.91 | 3.21 | 3.51 | 3.90 | 4.21 |
| 2 hours | 2.70 | 3.22 | 3.65 | 4.09 | 4.54 | 5.15 | 5.65 |
| 3 hours | 2.92 | 3.49 | 3.96 | 4.45 | 4.94 | 5.63 | 6.19 |
| 6 hours | 3.54 | 4.26 | 4.88 | 5.54 | 6.23 | 7.22 | 8.04 |
| 12 hours | 4.29 | 5.24 | 6.06 | 6.96 | 7.92 | 9.33 | 10.6 |
| 24 hours | 5.08 | 6.26 | 7.28 | 8.41 | 9.65 | 11.5 | 13.1 |

Values at the airport differ by 1 percent or less [S13, RIC query].

Gaston against these (my comparisons):
- RIC airport: peak hour 2.10 in, under a 10-year hour; 3 h 3.95 in, about 50-year; 6 h 5.51 in,
  about 100-year; 24 h 6.68 in, between 25- and 50-year.
- Shockoe watershed by AORC (likely low): 3 h 4.1 to 4.8 in, about 50- to 200-year; 6 h 7.6 to
  8.1 in, about 500- to 1,000-year.
- West End 12.60 in in about 8 h (per [S1 p3]): beyond the 1,000-year 12-hour depth (10.6 in).
- Caveats: Atlas 14 Volume 2 rests on data that predate Gaston (my understanding is through about
  2000; UNCONFIRMED). Return periods describe rain at a point, not floods. NOAA Atlas 15 is in
  preparation and will change these numbers.

So the series can say: at the airport, about a 100-year six-hour rain; over the Shockoe valley,
probably far rarer, on the order of a several-hundred-year six-hour rain or more. It should not say
"a 1,000-year flood."

## 6. Rivers and the James's level that evening (only what Gaston needs)

| Data | Gaston relevance | URL | Period |
|---|---|---|---|
| USGS 02037500 James near Richmond (Westham), discharge IV | 1,890 cfs at 2:15 p.m.; peak 14,800 cfs at 9:15 p.m.; 6,480 cfs daily mean Aug. 31 [S10] | https://waterdata.usgs.gov/monitoring-location/USGS-02037500 | discharge IV from 1990; daily from 1934 [S11] |
| USGS 02037500 stage | none in 2004; stage IV from Oct. 1, 2007 [S11] | | |
| USGS 02037705 James at City Locks (tidal) | no 2004 record; stage from Oct. 1, 2007 [S11] | https://waterdata.usgs.gov/monitoring-location/USGS-02037705 | |
| NWS RMDV2 flood categories | action 9 ft / 22,600 cfs; minor 12 ft / 42,000; moderate 15 ft / 66,700; major 22 ft / 167,000 [S12] | https://water.noaa.gov/gauges/RMDV2 | |
| USGS gauges on Shockoe Creek | none; it is piped | | |
| City rain gauges | DPU flow and rain monitoring for the CSO model exists in later years (modeled 2005-2022 [S39 p21]); a 2004 city gauge record is UNCONFIRMED | | |

## 7. CoCoRaHS

Not in Virginia in 2004. CoCoRaHS's own export returns no Virginia reports for Aug. 31, 2004, and
does return Virginia reports by June 3, 2008 [S45]. Useful for the series from 2008 on. License:
CoCoRaHS data are free to use with credit (check current terms).

## 8. Best tracks (HURDAT2)

File: https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-092326.txt [S7]. Public domain; text,
6-hourly positions, winds, pressure, wind radii from 2004.

| Storm | HURDAT2 ID | Line in file |
|---|---|---|
| Camille 1969 | AL091969 | 30398 |
| Agnes 1972 | AL021972 | 32185 |
| Juan 1985 | AL121985 | 37483 |
| Fran 1996 | AL061996 | 41614 |
| Isabel 2003 | AL132003 | 44909 |
| Gaston 2004 | AL072004 | 45475 |

(Do not confuse with Juan 2003, AL152003, or Fran 1990, AL071990.)

## 9. Storm rainfall maps (WPC, David Roth)

All pages return HTTP 200 [S49]. Each offers a track GIF, a storm-total rain map in three GIF
styles, and daily 24-hour maps ending 12 UTC. No gridded data files are offered; the maps are
contoured from NCDC, RFC, USGS and other gauge data.

| Storm | URL | Notes |
|---|---|---|
| Camille 1969 | https://www.wpc.ncep.noaa.gov/tropical/rain/camille1969.html | adds Virginia maps zoomed on Nelson County |
| Agnes 1972 | https://www.wpc.ncep.noaa.gov/tropical/rain/agnes1972.html | daily maps June 18-23 |
| Juan 1985 | https://www.wpc.ncep.noaa.gov/tropical/rain/juan1985.html | the Virginia flood rain fell after Juan and is not in the storm total |
| Fran 1996 | https://www.wpc.ncep.noaa.gov/tropical/rain/fran1996.html | heavy streak from SE North Carolina through central Virginia |
| Isabel 2003 | https://www.wpc.ncep.noaa.gov/tropical/rain/isabel2003.html | |
| Gaston 2004 | https://www.wpc.ncep.noaa.gov/tropical/rain/gaston2004.html | 6 to 12 in in about 8 h in Virginia |
| Floyd 1999, Connie 1955 | .../floyd1999.html, .../connie1955.html | also exist |

License: WPC pages are NWS works (public domain); confirm image credit lines.

## 10. Watershed and sewershed boundaries

- **USGS WBD**: Shockoe Creek is not its own HUC12; it lies in 020802060101 "Almond Creek-James
  River," 126.25 km² [S42]. https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/6 .
  Public domain.
- **StreamStats** (https://streamstats.usgs.gov/ss/): delineates on the land surface. In a basin
  whose creek is piped and whose sewers cross ridges, its boundary will be wrong in places. Useful
  as a first look only.
- **City sewershed**: the DPU's Shockoe CSO sewershed boundary (about 8,000 acres [S16], [S40 p42])
  is the right polygon. I found no public GIS download of it. The DPU's "Watershed Characterization
  Report" and the RVAH2O "find your watershed" map are cited by [S35]. UNCONFIRMED whether a
  downloadable layer exists.
- **Imperviousness**: compute from the NLCD impervious-surface layer (2001 and 2006 bracket the
  storm; https://www.mrlc.gov/data , public domain, 30 m) inside the sewershed polygon.
- **Lidar**: the isoscape terrain already holds it; use it for the spill-path test in
  `gaston-mechanism.md`.

## 11. Event records for the series generally

- **NCEI Storm Events** bulk CSV: details, fatalities and locations by year, 1950 to present;
  flood events only from 1996 [S5], [S54]. https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
  Public domain.
- **GHCN-Daily** for RIC back to 1939 [S55], with older Richmond city records under other IDs
  (for example Richmond Chimborazo Park, USW00013780, and Richmond City Locks, USC00447196, both in
  the station list; no 2004 data). Public domain.
- **OpenFEMA** disaster declarations [S15]. Public domain.
