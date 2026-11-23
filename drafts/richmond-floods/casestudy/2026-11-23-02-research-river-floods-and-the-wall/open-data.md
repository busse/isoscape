# Open data for drawing Richmond's floods

All links checked or read November 23, 2026. "Public domain" means a US federal work unless noted.
Nothing below was downloaded for the photo collections; they are listed only.

## Gauges

| Dataset | URL | Format | License | Notes |
|---|---|---|---|---|
| USGS 02037500 Westham, annual peaks 1935 to 2025 | https://nwis.waterdata.usgs.gov/nwis/peak?site_no=02037500&agency_cd=USGS&format=rdb | tab-delimited RDB | public domain | 91 peaks; codes 1, 5, 8 explained in file header. Copy in `raw/peak_02037500.rdb` |
| USGS 02037500 site description and datum | https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=02037500&siteOutput=expanded ; https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items/USGS-02037500?f=json | RDB, JSON | public domain | gauge zero 98.04 ft NAVD88 |
| USGS 02037500 daily discharge since Oct. 1934 | https://waterservices.usgs.gov/nwis/dv/?format=rdb&sites=02037500&parameterCd=00060&startDT=1934-10-01 | RDB | public domain | series 145310 |
| USGS 02037500 instantaneous stage and flow | https://waterservices.usgs.gov/nwis/iv/?format=rdb&sites=02037500&parameterCd=00065,00060 | RDB | public domain | historical IV did not return for 2010 to 2025 windows today; try https://waterdata.usgs.gov/monitoring-location/USGS-02037500/ |
| USGS 02037705 City Locks, elevation above NAVD88 since Oct. 2007 | https://waterservices.usgs.gov/nwis/iv/?format=rdb&sites=02037705&parameterCd=62620 | RDB | public domain | no peak file ("No sites/data found") |
| NWS RMDV2 (Westham): crests, flood categories, impact stages | https://api.water.noaa.gov/nwps/v1/gauges/rmdv2 ; page https://water.noaa.gov/gauges/RMDV2 | JSON | public domain | minor 12, moderate 15, major 22 ft. Copy in `raw/nwps_rmdv2.json` |
| NWS RICV2 (City Locks): crests from 1901, categories, impacts | https://api.water.noaa.gov/nwps/v1/gauges/ricv2 ; page https://water.noaa.gov/gauges/RICV2 | JSON | public domain | minor 8, moderate 19, major 28 ft; mixed datums, see `datums.md`. Copy in `raw/nwps_ricv2.json` |
| MARFC flood summaries for Richmond (top crests, tropical floods, by month, by year, by category, per-event sheets) | https://www.weather.gov/media/marfc/Top20/JMS/Richmond.pdf and siblings under /Tropcal_Floods/, /Month/, /Years/, /Category/ | PDF | public domain | Westham only |
| NOAA tide station 8638495 Richmond River Locks (2007 to 2010) | https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/8638495/datums.json ; https://tidesandcurrents.noaa.gov/benchmarks/8638495.html | JSON, HTML | public domain | tidal datums; nine benchmarks with NAVD88 elevations; station removed Sept. 14, 2010 |

## Flood extents and water surfaces

| Dataset | URL | Format | License | Notes |
|---|---|---|---|---|
| USACE/NWS "Richmond Partner FIM": inundation for every foot, City Locks 8 to 35 ft, Westham 11 to 28 ft | app https://experience.arcgis.com/experience/8d12656d99224ac4b599fb270f4d199f/page/Richmond-Locks ; item metadata https://www.arcgis.com/sharing/rest/content/items/8d12656d99224ac4b599fb270f4d199f?f=json ; web maps 7cdf21aecdf247c2acb918c7c01f600f (Locks) and d2fd3ce625614b508ca0aed38e6e6b21 (Westham) | cached map tiles (images) | US Government, no-warranty statement; no license named | HEC-RAS on a 5 ft DEM; depth rasters and boundaries exist but are not published as data; request from USACE Norfolk or NWS Wakefield |
| USGS HA-409, HA-410, HA-411: Flood of August 1969, Bon Air, Richmond and Drewrys Bluff quadrangles | https://pubs.usgs.gov/ha/410/plate-1.pdf (and /ha/409/, /ha/411/) | scanned PDF, 1:24,000 | public domain | mapped 1969 extent; HA-410 also has a crest table since 1870 and a profile through the falls |
| USGS OFR 70-51, Flood of August 1969 in Virginia | https://pubs.usgs.gov/of/1970/0051/report.pdf | PDF, 136 pp | public domain | Table 2 historic stages incl. 1771; gauge datums; hourly 1969 hydrographs |
| USGS Professional Paper 924, Agnes floods | https://pubs.usgs.gov/pp/0924/report.pdf | PDF, 414 pp, 65 MB | public domain | Table A4 crest elevations 1936, 1969, 1972 |
| USGS OFR 86-486, Flood of November 1985 | https://pubs.usgs.gov/publication/ofr86486 (42 plates; text PDF not found) | PDF plates | public domain | not read; may hold Richmond high-water marks |
| FEMA National Flood Hazard Layer | https://www.fema.gov/flood-maps/national-flood-hazard-layer ; service https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer | shapefile, file geodatabase, REST | public domain | refused connection from this environment; includes levee lines (S_Levee) and BFE lines |
| FEMA Flood Insurance Study, City of Richmond (510129), effective and 2022 preliminary | https://msc.fema.gov/portal (search Richmond, City of); preliminary FIRM panels under https://prd-floodmaps.msc.fema.gov/prelim/PrelimData/Virginia/Richmond%20City/prelim_issue_date-2022-02-02/ | PDF | public domain | refused connection from this environment; the flood profiles are what `datums.md` needs |
| Henrico County FIS (2021), discharges at the Westham gauge | https://henricolibrary.org/images/FEMA/51087CV001B.pdf (Vol. 1), 51087CV002B.pdf (Vol. 2) | PDF | public domain | Table 9, PDF p. 36 |

## Terrain

| Dataset | URL | Format | License | Notes |
|---|---|---|---|---|
| 2025 City of Richmond lidar DEM, 1 ft | https://www.fisheries.noaa.gov/inport/item/80311 ; bulk https://noaa-nos-coastal-lidar-pds.s3.amazonaws.com/dem/VA_Richmond_DEM_2025_14836/index.html ; viewer https://coast.noaa.gov/dataviewer/#/lidar/search/where:ID=14836/details/14836 | GeoTIFF, 2,083 tiles | CC0 1.0 | flown Feb. 14, Feb. 17 and Mar. 1, 2025, "normal river levels"; NAVD88 (GEOID18) US ft; Virginia South ftUS; about 117 sq mi. Note the February 18, 2025 flood fell between flights |
| USGS 3DEP lidar and 1 m DEMs (statewide Virginia projects) | https://apps.nationalmap.gov/downloader/ ; https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/ | LAZ, GeoTIFF | public domain | which project covers Richmond is UNCONFIRMED here; the city 2025 set is finer |

## Structures

| Dataset | URL | Format | License | Notes |
|---|---|---|---|---|
| USACE National Levee Database | https://levees.sec.usace.army.mil/ | web app, API | public | Richmond system ID not obtained: the feature service asked for a token and search endpoints returned "not found" |
| OpenStreetMap floodwall ways (`wall=flood_wall`) | https://www.openstreetmap.org/way/307148064 (and the ways listed in `floodwall.md`) | OSM | ODbL 1.0 | concrete parts mapped; earthen levee not found. Extract in `raw/osm_floodwall_from_cache.geojson` |
| City of Richmond open data | https://data.richmondgov.com/ (UNCONFIRMED that a floodwall layer exists) | various | varies | not checked in this pass |

## Photographs and video (list only; nothing downloaded)

| Collection | URL | Rights as stated | Content |
|---|---|---|---|
| VCU Libraries, Richmond Comprehensive Planning Slide Collection | https://scholarscompass.vcu.edu/rcp/index.100.html | "public domain in the United States," credit VCU Libraries requested | 1969 flood slides: Boulevard Bridge, Byrd St., East Main St., Riverside Dr., rail tracks |
| USGS OFR 70-51 and HA-410 figures | links above | the photos are credited to the Richmond Times-Dispatch and News-Leader, so they are NOT public domain despite appearing in a USGS report | 1969 Main Street, I-95 |
| USACE Norfolk District on DVIDS | https://www.dvidshub.net/video/404037/richmond-floodwall | public domain | 2015 floodwall B-roll |
| USACE Norfolk District, "Remembering Agnes" | https://www.dvidshub.net/video/844004/remembering-agnes | public domain is typical for DVIDS; rights not checked | 2022 video |
| Library of Virginia (Flickr and catalog), Agnes photographs | https://www.lva.virginia.gov/copyright.htm (policy) | not checked; LVA terms vary by item | "Richmond After the Flood," "14th Street Bridge Under Water" (titles cited by virginiaplaces.org) |
| NOAA Photo Library | https://photolib.noaa.gov/ | usually public domain; not checked for Richmond floods | UNCONFIRMED |

Avoid newspaper photographs (Times-Dispatch, News-Leader) unless licensed, and avoid any image
centered on an identifiable public figure.

## Sites that refused or failed today

- FEMA hosts (prd-floodmaps.msc.fema.gov, hazards.fema.gov): proxy refused (CONNECT 502).
- Overpass API (overpass-api.de, overpass.kumi.systems): connection closed.
- NLD feature service: "Token Required."
- wdr.water.usgs.gov annual report PDFs: 404.
- en.wikipedia.org, 1985 Election Day floods: permission request not answered; skipped.
- 6amcity floodwall history article: body not served.
