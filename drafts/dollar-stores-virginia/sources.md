# Sources fetched (dollar stores, Virginia)

Raw downloads stay out of git. Each line: what, URL, date fetched, size, SHA-256, license.

| What | URL | Fetched | Size | SHA-256 | License |
|---|---|---|---|---|---|
| USDA FNS SNAP Retailer Locator, historical 2005-2025 (CSV in zip) | https://www.fns.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip | 2026-11-21 | 24,036,753 B | 872a6f814a63514a1f1b0c4517a90309a9fbb01d97d6e4dbb1e8b20421c08cce | US government work, public domain |
| Census Vintage 2024 place population estimates, Virginia | https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024_51.csv | 2026-11-21 | | (record on next fetch) | US government work, public domain |

## First reads of the SNAP file (2026-11-21)

- Virginia rows, all years: 15,874.
- Name match "DOLLAR GENERAL", still authorized (no end date): 505. Ever authorized: 561.
  Family Dollar 208 (293 ever). Dollar Tree 200 (215 ever). Name match only; to be checked.
- The file starts in 2005. 188 of the 505 Dollar General rows carry a 2004 or 2005
  authorization date, which marks stores already authorized when the file begins. Opening
  year is usable only from 2006 on.
- All 505 have coordinates. Geocode quality not yet checked.

## Not reachable or restricted (2026-11-21)

- Census Data API now returns "Missing Key". Bulk files on www2.census.gov need no key.
- Overpass API: 406 without a user agent, then 502 "at capacity". Retry later or use a
  Geofabrik Virginia extract (ODbL).
- VDOT Bidirectional Traffic Volume 2022 (ArcGIS item a8da35dd9ce54993b25f64487c3717ec):
  license text says VDOT's files are for the official business of the Commonwealth. Ask VDOT
  before using it on anything sold.
- VGIN statewide parcels: outlines and IDs. Values live in 133 local systems.
