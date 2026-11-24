# Period city, 1965 to 1975: public sources for building footprints

For the floods series' Camille (1969) and Agnes (1972) plates. Two areas: the north bank
(Shockoe Bottom, Shockoe Slip, Tobacco Row, Mayo Island) and the Manchester flats on the south
bank. Everything here was read on November 24, 2026. Samples are in `samples/`, each with a
caption file. Scripts are in `scripts/`. Nobody was contacted and no account was used.

## The short answer

- **Best public source, no login:** the USGS 1:24,000 **orthophoto map of the Richmond
  quadrangle, 1974 photography** (imprint 1977). It is a real vertical photograph, rectified,
  georeferenced and public domain, with a direct download. It covers both areas. At about 1 to
  2 m on the ground, block faces and freestanding buildings read; joined buildings with similar
  roofs do not split; heights cannot be read. With one shift (+2 m E, -14 m N) it sits on
  today's OSM streets in Shockoe.
- **Best source for Manchester's buildings:** the Sanborn **South Richmond volume, republished
  1952**, online at the Library of Congress, public domain. isoscape has traced none of it yet.
- **Nothing public and no-login was found between 1952 and 1974 that shows footprints** in the
  two areas. The USGS topographic quadrangles of 1964 (photorevised 1968 and 1974) show only an
  urban tint with landmark buildings.
- **Locked:** EarthExplorer single frames (login to download), ProQuest Digital Sanborn and
  FIMo (library card or subscription), USDA APFO film and NOAA NGS photos (orders), DHR's V-CRIS
  (account), historicaerials.com (purchase).

## The table

Verdicts: **use** (public, no login, useful now), **check** (public, useful as a check, not
for tracing), **lead** (may hold footprints, not found online), **locked** (needs a login,
library card, order or purchase; recorded, not used), **no** (looked at, not useful).

### 1. Aerial photography

| Source | Years | Ground resolution | Covers Shockoe / Manchester | License | Georeferenced | How a file is had | Verdict |
|---|---|---|---|---|---|---|---|
| USGS orthophoto map, Richmond quad, 1:24,000 (item 186506; metadata: Date on Map 1974, Aerial Photo Year 1974, Imprint 1977) | 1974 | GeoTIFF 2.03 m/px (300 dpi scan); GeoPDF 600 ppi, about 1.0 m/px; the printed halftone limits it to about 2 m in practice | both | USGS, public domain ("Acknowledgment of the U.S. Geological Survey is expected", metadata) | yes (NAD27, LCC); off by about 14 m in Shockoe until shifted | direct: https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/VA/VA_Richmond_186506_1974_24000_geo.tif (14.0 MB) and .../PDF/VA/24000/VA_Richmond_186506_1974_24000_geo.pdf (22.3 MB); found with the TNM API https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Historical%20Topographic%20Maps&bbox=-77.43,37.527,-77.425,37.532 ; metadata https://thor-f5.er.usgs.gov/ngtoc/metadata/waf/maps/historicaltopo/pdf/VA/24000/VA_Richmond_186506_1974_24000_geo.xml | **use** (samples: `shockoe-orthophoto-1974*.png`, `manchester-orthophoto-1974.png`, `testblock-*.png`) |
| USGS Aerial Photo Single Frames (EROS), incl. the photography behind the 1968 and 1974 photorevisions | 1937 to 2014 | full scans 400 dpi (medium, free) and 1,000 dpi (high, $30 a frame if not yet scanned), per the EROS FAQ | likely both (not verified: frame search needs EarthExplorer) | US Government | no (single frames) | EarthExplorer only, "Log in as a guest or as a registered user" (data.gov record https://catalog.data.gov/dataset/aerial-photo-single-frames ); downloads need a login. NASA CMR holds the collection record (C1220567654-USGS_LTA) but no frame records: a granule search over Shockoe for 1964 to 1976 returned 0. No public S3 or browse route was found. FAQ: https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-aerial-frequently-asked-questions-faqs | **locked** |
| NHAP / NAPP | 1980 to 1991 | | | | | too late for 1969 to 1972 | **no** |
| USDA APFO (ASCS/FSA) county film | film from 1955 | 12.5 micron scans, $13 a scan as of 2016 (FSA info sheet https://www.fsa.usda.gov/sites/default/files/documents/scans_infosheet_2017_Final.pdf ) | unknown: the city is urban and may lie at the edge of Henrico and Chesterfield flights | US Government | no | order only. The catalog PDF (https://www.fpacbc.usda.gov/sites/default/files/2025-04/catalog-2-040125.pdf , listed at https://www.fpacbc.usda.gov/geospatial-services/customer-services/imagery-catalogs ) and the older https://www.fsa.usda.gov/Internet/FSA_File/catalog.txt both failed to connect from here (not retried) | **locked** |
| NOAA NGS coastal aerial photography | from 1942 | 1:10,000 to 1:50,000 contact prints | the tidal James reaches Richmond; coverage not verified | "All photographs are available to the public for purchase" | no | order: https://www.fisheries.noaa.gov/inport/item/39951/printable-form ; NOAA Digital Coast's free historical sets cover only Pacific islands (https://coast.noaa.gov/digitalcoast/data/aerialphoto.html ) | **locked** |
| Virginia Department of Highways photography of Agnes | June 1972 | obliques | Figures 51 and 52 of USGS PP 924 credit it; Fig. 52 is "James River at Mayos Bridge at Richmond" | PP 924 itself public domain | no | PP 924, https://pubs.usgs.gov/pp/0924/report.pdf , page 71 (PDF page 81). No public VDOT archive of this photography was found | **check** (sample `agnes-1972-pp924-fig52-mayo-bridge.jpg`: massing and storeys in flood, not footprints) |
| VCU Libraries, MCV Aerial Exhibit | late 1950s to 1970 | obliques, about 1,700 px | upper Shockoe Valley only (north of the flood) | CC BY-NC-SA 4.0 | no | item https://gallery.library.vcu.edu/items/show/114805 ; original file linked on the page | **check** |
| VCU, Richmond Comprehensive Planning Slide Collection (City planning slides) | 1940s to 2000, mostly 1970s to 1990s | 35 mm slides | street views, some aerial views and floods (catalog says so) | "in the public domain in the United States" | no | https://scholarscompass.vcu.edu/rcp/index.110.html (169 index pages) | **check** (block-by-block ground truth) |
| HABS photographs (Main Street Station 1969 and 1971, Columbian Block 1969, Philip Morris leaf warehouse 1717-21 E Cary, canal locks 1971) | 1969 to 1971 | ground photos | Shockoe | "No known restrictions on images made by the U.S. Government" | no | e.g. https://www.loc.gov/pictures/collection/hh/item/va0562/ , .../va0573/ | **check** |
| The Valentine, Edith Shelton photographs (e.g. "17th and Dock Streets, Shockoe Bottom", October 1955) | 1950s | ground photos | Shockoe | no rights statement on the Google Arts and Culture page | no | https://artsandculture.google.com/asset/17th-and-dock-streets-shockoe-bottom-edith-shelton-photographer/lAH2wjAtIcWNAg (view only) | **check** |
| City of Richmond ArcGIS (org k3vhq11XkBNeeOfM) | 1999 on | Structures layer from 1999 6-inch orthos; aerials 2017 on | both | city disclaimer | yes | https://services1.arcgis.com/k3vhq11XkBNeeOfM/ArcGIS/rest/services (856 services listed); no historic aerial layer found by name or in an ArcGIS Online search of the org | **no** for 1965 to 1975 |
| Library of Virginia NHAP/NAPP set; Richmond-Petersburg Turnpike Authority records (work photos 1956 to 1958) | 1980s; 1956 to 1958 | | | | | reading room only (https://multipleexposure.virginiamemory.com/2013 , https://uncommonwealth.lva.virginia.gov/?p=42248 ) | **no** (wrong years) |
| historicaerials.com, aerialarchives.com | various | | | commercial | | view with watermark; download by purchase | **locked** |
| VGIN / VBMP statewide orthos | 2002 on | | | | | | **no** (wrong years) |

### 2. Maps

| Source | Years | Shows | Covers | License | Georeferenced | How a file is had | Verdict |
|---|---|---|---|---|---|---|---|
| Sanborn, Richmond, South Richmond volume, 1919 republished 1952 (LOC sanborn09064_021, 87 sheets; index "New Index, October, 1951") | 1951 to 1952 | every building, colored by material, storeys | **Manchester** (sheet 1: W 6th to E 3rd, Porter to Decatur; the index puts Hull Street 100 to 521 on sheets 1, 2 and 4) | "The content of the Library of Congress online Sanborn Maps Collection is in the public domain and is free to use and reuse." | no (fit with `rigid.py`) | https://www.loc.gov/item/sanborn09064_021/?fo=json gives IIIF URLs per sheet | **use** (sample `manchester-sanborn-1952-south-richmond-sheet1-25pct.jpg`) |
| Sanborn, South Richmond 1919 to Jul 1950 (sanborn09064_015, 85 sheets); South Richmond 1919 (in _005); Manchester 1910 (sanborn09042_003) | 1910 to 1950 | as above | Manchester | public domain | no | LOC item pages | **use** (earlier states) |
| Sanborn, Richmond vol. 2, 1925 republished 1952 (sanborn09064_017, 88 sheets) | 1952 | as above | east downtown, Shockoe | public domain | no | https://www.loc.gov/item/sanborn09064_017/ | **use**: isoscape traced vol. 2 from the 1950 issue (_011); the 1952 issue may carry two more years of corrections |
| Later Richmond Sanborn corrections (after 1952) | to about 1970 | | | | | none online at LOC: a LOC search for Richmond Sanborn items lists nothing after 1952 (https://www.loc.gov/maps/?q=sanborn+richmond+virginia&fo=json ). ProQuest Digital Sanborn Maps 1867 to 1970 and FIMo ("public domain 1865-1963") need a Library of Virginia card or account (https://lva-virginia.libguides.com/richmond-maps/sanborn ); whether either holds a post-1952 Richmond state was not checked | **locked** |
| USGS 7.5-minute Richmond quad: 1964 (imprint 1966), photorevised 1968 (imprint 1969, item 186504), photorevised 1974 (imprint 1976, item 186505); later 1981, 1987, 1994 | 1964 to 1974 | urban tint; only landmark and large isolated buildings | both | public domain | yes | e.g. https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/VA/VA_Richmond_186504_1964_24000_geo.tif (13.9 MB) | **no** for footprints (samples `shockoe-topo-*.png`) |
| USGS HA-410, Flood of August 1969, Richmond quadrangle | 1969 | flooded area on the 1:24,000 topo base | both | public domain | scanned PDF | https://pubs.usgs.gov/ha/410/plate-1.pdf (already used by the floods research) | **no** for footprints |
| City zoning maps, scanned, as tile services (HistoricZoning1923 to 1979Amended) | 1960, 1961, 1969, 1970, 1975, 1976, 1979 | zoning districts on a lot and street base | 1969 and 1970 cover the west side only; 1975 returned blank tiles over Shockoe at zoom 18 | no license stated; "Planning and Development Review" | yes (Web Mercator tiles) | e.g. https://tiles.arcgis.com/tiles/k3vhq11XkBNeeOfM/arcgis/rest/services/HistoricZoning1975/MapServer | **no** |
| Large-scale city topographic base with building outlines (copied as "Attachment One" in the Shockoe Valley NR file, 2015) | date not given | building outlines, contours in feet, benchmarks | 24th to 27th Streets (the copy) | | | not found online. The Library of Virginia lists "Topography area surrounding city of Richmond", R. H. Randall & Co., 1922, 1:2,400 (https://lva-virginia.libguides.com/richmond-maps/topographic-maps ), too early | **lead** (sample `shockoe-nr1983-attachment-one-basemap.png`) |
| Corps of Engineers: Flood Plain Information reports (Norfolk District, 1965 report cited in HA-410's crest table); James River Basin, Phase I General Design Memorandum, Richmond, 1984 | 1965; 1984 | unknown: GDMs often carry plates of the protected area | | GDM 1984 is in the Serial Set via ProQuest ("Reuse ... requires a license from ProQuest", https://libcat.library.tamu.edu/Record/in00002863950/Description ) | | not found as a free PDF (DTIC search hits were other projects) | **lead / locked** |
| Real-estate atlases (Beers 1876, Baist 1889) | 19th century | | | | | already assessed in `tools/sanborn/PROGRESS.md` | **no** (wrong years) |
| HABS/HAER site plans | 1969 to 1986 | single buildings (Virginia Fire and Marine 1970 site plan; Manchester Cotton and Woolen mill, 1986) | spots | public domain | no | LOC HABS | **no** for blocks |

### 3. Records

| Source | What it gives | How had | Verdict |
|---|---|---|---|
| City assessor year built (`Year_of_Construction`, already used) | year built of standing parcels only | ArcGIS REST, no login | in use; no demolition years |
| City `Structures` layer, field `FinalDemolitionPermitID` | maintained since the 1999 orthos | 3,566 structures in lon -77.437 to -77.415, lat 37.515 to 37.540; 0 with a demolition permit ID (query, today) | **no** |
| City open demolition-permit dataset | none found for Richmond | | **no** |
| National Register, Shockoe Valley and Tobacco Row Historic District (VLR 1981, NRHP 1983, NRIS 83003308), with the 2014-15 inventory update | the **1980 survey lists every street address, block face by block face**, including "vacant lot" and "parking lot", with dates of the buildings standing; text on Camille and Agnes (PDF page 13: "Flooding caused by hurricanes Camille (1969) and Agnes (1972) resulted in extensive damage ... many owners of water-damaged buildings chose not to repair them") | https://npgallery.nps.gov/GetAsset/2f9dd6b2-9d0e-4544-89d4-7071fc6d0063 (30.8 MB, 167 pages, has a text layer) | **use** as a 1980 check: a building standing in 1980 and dated before 1972 stood in 1972. A lot vacant in 1980 says nothing about 1972 |
| Shockoe Valley and Tobacco Row HD Boundary Increase (127-8182, NRHP Sept. 26, 2025) | East Broad Street, 4.7 acres | https://www.dhr.virginia.gov/wp-content/uploads/2023/03/127-8182_ShockoeValley_HD_Boundary_Increase_2025_NRHP_nomination_FINAL.pdf | outside the flood area |
| DHR page for 127-0344 | | the fetch of https://www.dhr.virginia.gov/historic-registers/127-0344/ was held for a permission prompt nobody answered; not retried. The NPGallery copy above was used instead | |
| Manchester Industrial HD (127-0457; 2000, 2004, 2011 increases) | inventories of buildings standing 2000 to 2011, between the river and Commerce Road, Semmes Avenue to Maury Street | https://www.dhr.virginia.gov/wp-content/uploads/2018/04/127-0457_Manchester_Industrial_HD_2000_Final_Nomination.pdf , ..._2004_BI_Final_Nomination-1.pdf , ..._2011_Update_Boundary_Increase_NR_Final.pdf (not downloaded) | **check** |
| Manchester Residential and Commercial HD (127-0859; 2002, 2006) | 251 buildings at listing | https://www.dhr.virginia.gov/wp-content/uploads/2018/04/127-0859_ManchesterResidentialCommercial_HD_2002_Final_NRHPamendments.pdf (not downloaded) | **check** (mostly off the flats) |
| DHR V-CRIS architectural survey | survey files, some with demolished resources | account required | **locked** |

## Notes on what was seen

- **The 1974 orthophoto, close up** (`shockoe-orthophoto-1974-geopdf600dpi.png`): streets,
  rail and the I-95 viaduct are sharp. A building alone on its lot, or one with a roof tone
  unlike its neighbors, can be outlined to about 3 to 5 m. A row of joined two- and three-story
  buildings under similar tar roofs reads as one dark mass: the party walls do not show.
  Shadows are too faint to measure heights. So it answers "is there a building here?" well,
  and "what is its outline?" only for big or freestanding buildings.
- **Registration**: with no shift the photo sits about 14 m south of today's streets in
  Shockoe; after the fitted shift the street lines sit on the pavement across a 900 m frame
  (`shockoe-ortho1974-osm-streets-fitted.png`). A fit for Manchester was unreliable (few
  streets, the best shift lay at the edge of the search); it needs corners read by eye, as the
  Sanborn sheets get.
- **The 1974 date cuts both ways**: a building on the 1974 photo stood in 1969 and 1972 (unless
  it was built on the spot after the flood). A building missing in 1974 may still have stood
  in 1972: the 1983 nomination says many flood-damaged buildings were not repaired. A pre-Agnes
  vertical (the 1968 photorevision photography in EarthExplorer) would settle those; it is
  behind the login.
- **Manchester**: isoscape has no Sanborn traces south of the river (every traced edition's
  footprints lie north of it), and the cached year-built parcels stop at about 37.5204 N, so
  325 of the 413 buildings the 2026 Manchester view shows are undated (floods log, step 35).
  The second gap is a fetch, not a research question.
