# Sources fetched (dollar stores, Virginia)

Raw downloads stay out of git. Each line: what, URL, date fetched, size, SHA-256, license.

| What | URL | Fetched | Size | SHA-256 | License |
|---|---|---|---|---|---|
| USDA FNS SNAP Retailer Locator, historical 2005-2025 (CSV in zip) | https://www.fns.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip | 2026-11-21 | 24,036,753 B | 872a6f814a63514a1f1b0c4517a90309a9fbb01d97d6e4dbb1e8b20421c08cce | US government work, public domain |
| Census Vintage 2024 place population estimates, Virginia | https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024_51.csv | 2026-11-21 | 60,567 B | 4ba55bcce6aeffba3963ac0da8030d39a3fb1340b87855f48dcbea8d1fe372f6 | Public domain |
| TIGER/Line 2024 places, Virginia | https://www2.census.gov/geo/tiger/TIGER2024/PLACE/tl_2024_51_place.zip | 2026-11-21 | 3,823,535 B | f530fd65c4d83cbf9a854cea6900fde5add4a7ca26bc8a11a59426c6ca07e16b | Public domain |
| TIGER/Line 2020 blocks, Virginia (POP20, HOUSING20) | https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_51_tabblock20.zip | 2026-11-21 | 311,011,970 B | 5722c3a80c66acb087429ea511a47d05a742a7b99712a63a711014fca5be9d61 | Public domain |
| TIGER/Line 2024 2020 urban areas, US | https://www2.census.gov/geo/tiger/TIGER2024/UAC20/tl_2024_us_uac20.zip | 2026-11-21 | 73,763,076 B | efa943399ad65d81421167502732a0ee3774be663da499681b25e0b412cd81f9 | Public domain |
| OSM via Overpass, Marion window (roads, buildings, chain and grocery points) | overpass-api.de, query in measure notes | 2026-11-21 | 6,052,321 B | 1e1947da3082000beb0c43ccbb5e6f4f866a9b2716615338064a764fc511800f | ODbL |
| OSM via Overpass, South Hill window | same | 2026-11-21 | 3,001,057 B | 8fd468bd73861b68e9a2d8b9937ed766d88a242f6fc0544362620dfb9a6e2419 | ODbL |
| OSM via Overpass, Chase City window | same | 2026-11-21 | 1,114,898 B | 1d0be0fbfd96a13d24529cdd7355940876fc9d0d670c1fc99ca99bf190845883 | ODbL |

| NLCD 2021 percent impervious, three test windows (WCS) | https://www.mrlc.gov/geoserver/ows, coverage mrlc_download__NLCD_2021_Impervious_L48 | 2026-11-21 | 1,050,540 B each | marion c6015d40..., south-hill 685443da..., chase-city eb4aa2ec... | Public domain (USGS/MRLC) |
| NLCD 2021 impervious descriptor, same windows | coverage mrlc_download__NLCD_2021_Impervious_descriptor_L48 | 2026-11-21 | 1,050,540 B each | marion 7a0d49c3..., south-hill c9292175..., chase-city ade60bbd... | Public domain |
| OSM via Overpass, Middle Peninsula and lower Northern Neck roads (bbox 37.15,-77.05,38.05,-76.15) | overpass-api.de | 2026-11-21 (OSM base 16:52 UTC) | 31,350,083 B | c7907e8ccebb170d413b43ce9f4b8aaed895aa233ad287a2a2cfe9fe37c8ce3b | ODbL |
| Geofabrik OpenStreetMap extract, Virginia | https://download.geofabrik.de/north-america/us/virginia/virginia-latest.osm.pbf | 2026-11-21 | 429,912,960 B | md5 fa4a5272b012447062f4c09ad078dc91 (matches Geofabrik's .md5) | ODbL |
| The same, filtered on the Mac to drivable highways and the three chains' brand:wikidata (pyosmium BackReferenceWriter) | virginia-roads.osm.pbf | 2026-11-21 | 67,219,024 B | 11ab9f74eb1941a23f4ad01aa3a233eab85e50acfb29b159aa8f4e27316812f7 | ODbL |
| NLCD 2021 impervious and descriptor, 20 editorial windows | MRLC WCS, as above | 2026-11-21 | 40 files | checksums in raw/nlcd-editorial20.sha256 on the Mac | Public domain |
| NLCD 2021 impervious and descriptor, all 227 places | MRLC WCS | 2026-11-21 | 454 files, archive 34,313,690 B | raw/nlcd-all-places.sha256 on the Mac | Public domain |
| NLCD 2001 impervious, all 227 places | MRLC WCS, coverage mrlc_download__NLCD_2001_Impervious_L48 | 2026-11-21 | 227 files, archive 21,596,149 B | raw/nlcd2001-all-places.sha256 on the Mac | Public domain |
| FHWA HPMS 2024 Spatial All Sections, Virginia, f_system 1-6 with AADT (262,439 sections, 6 GeoJSON pages) | https://data.transportation.gov/resource/42um-tgh5.geojson (where stateid=51) | 2026-11-21 | archive 28,078,095 B | raw/hpms/va2024.sha256 on the Mac | Public Domain U.S. Government (dataset metadata) |
| FHWA HPMS Virginia shapefiles 2012, 2014, 2015, 2016 | https://www.fhwa.dot.gov/policyinformation/hpms/shapefiles/virginia<year>.zip | 2026-11-21 | 39,058,420 / 185,087,392 / 287,747,546 / 266,399,970 B | raw/hpms/hist.sha256 on the Mac; the 2016 DBF is truncated at the source (declares 4,381,672,890 B, holds 2,147,485,719) | US government work |
| Planning district membership | https://www.vapdc.org/pdc-directory (opened, not downloaded) | 2026-11-21 | | | Facts, used in regions.json |
| Census 2024 cartographic boundary counties, US, 1:500k (Virginia used for the poster's regions and locator) | https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip | 2026-11-22 | 11,626,066 B | da4051717caec55c75e3748c3608c2a3dbde8d1ff401bbaf4f952e3c3fb63ef1 | Public domain |
| Libre Baskerville (the prints' typeface, already in the repo) | tools/print/fonts, converted woff to TTF for matplotlib | 2026-11-22 | | | SIL Open Font License (tools/print/fonts/OFL.txt) |

Raw files are kept on the Mac in `ISO-TEST/isoscape-work/dollar-stores/raw/`.

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
- Overpass API: 406 without a user agent; worked for small windows with one. OSM building
  coverage is thin in small towns (186 buildings in the Chase City window), so OSM buildings
  cannot draw an edge.
- VDOT Bidirectional Traffic Volume 2022 (ArcGIS item a8da35dd9ce54993b25f64487c3717ec):
  license text says VDOT's files are for the official business of the Commonwealth. Ask VDOT
  before using it on anything sold.
- VGIN statewide parcels: outlines and IDs. Values live in 133 local systems.
