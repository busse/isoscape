# Sources for the Gaston files

Every source below was read on **November 23, 2026**. The other files cite these by key, with the
page, table, line or record inside the source given at each citation, for example [S1 p8, Table 3].
Where I did arithmetic or a data extraction myself, the file says so and names the script input.

Quotations: at most one per source, under 15 words. Everything else is paraphrase.

## Primary: federal agencies and data

| Key | Source | URL | Notes |
|---|---|---|---|
| S1 | NHC Tropical Cyclone Report, Hurricane Gaston, AL072004 (Avila, revised Feb. 16, 2005; 14 pp.) | https://www.nhc.noaa.gov/data/tcr/AL072004_Gaston.pdf | Page numbers are PDF pages. Table 1 best track p4-5; Table 3 rain p8; impacts p3. |
| S2 | NWS Wakefield, Gaston event page (preliminary rainfall statement, Aug. 31, 2004, 11:23 a.m. EDT; Richmond 24-hour records table) | https://www.weather.gov/akq/Gaston | HTML. Says certified data come only from NCDC. |
| S3 | Billet, J., and K. Lynch (NWS Wakefield), "A Look at Tropical Storm Gaston Flooding in Virginia" (6 pp., undated) | https://www.glenallenweather.com/historylinks/2004/GastonFlood31aug2004.pdf | Hosted on a private weather site, authored by NWS staff. |
| S4 | Brown, Z. G., Y.-L. Lin and M. L. Kaplan, "Factors that contributed to the Hurricane Gaston flooding event in Richmond, Virginia," AMS paper 12b.3 (undated) | https://ams.confex.com/ams/pdfpapers/108535.pdf (redirects to https://studio.m-anage.com/ams/pdfpapers/108535.pdf) | |
| S5 | NCEI Storm Events Database, bulk details file for 2004 (StormEvents_details-ftp_v1.0_d2004_c20260323.csv.gz) | https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/ | Event IDs cited. The per-event web page (ncdc.noaa.gov/stormevents/eventdetails.jsp) **refused the fetch (robots)**; I used NCEI's published bulk download instead. |
| S6 | NCEI Storm Events, bulk fatalities file for 2004 (StormEvents_fatalities-ftp_v1.0_d2004_c20260323.csv.gz) | same directory as S5 | Fatality IDs 20910-20917. |
| S7 | NHC HURDAT2 Atlantic best tracks, file hurdat2-1851-2025-092326.txt | https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-092326.txt | Gaston header at line 45475. |
| S8 | NCEI Integrated Surface Database (Global Hourly), Richmond Intl. Airport, station 72401013740, 2004 | https://noaa-global-hourly-pds.s3.amazonaws.com/2004/72401013740.csv | Field AA1 = precipitation, tenths of mm. Times UTC. |
| S9 | NCEI GHCN-Daily via Access Data Service, PRCP, Aug. 30 to Sep. 1, 2004, all non-CoCoRaHS stations in 37.25-37.95 N, 77.1-77.8 W | https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&dataTypes=PRCP&stations=USC00440327,USC00444101,USC00445833,USC00447541,USC00449213,USW00013740,USW00093775&startDate=2004-08-30&endDate=2004-09-01&units=standard&format=csv | Coop values are for the 24 hours ending at the morning observation. |
| S10 | USGS NWIS, James River near Richmond (Westham), 02037500: instantaneous and daily discharge, Aug. 27 to Sep. 5, 2004 | https://nwis.waterservices.usgs.gov/nwis/iv/?format=rdb&sites=02037500&startDT=2004-08-30&endDT=2004-08-31 and https://waterservices.usgs.gov/nwis/dv/?format=rdb&sites=02037500&startDT=2004-08-27&endDT=2004-09-05 | Discharge only; no stage record in 2004. |
| S11 | USGS NWIS series catalog for 02037500 and 02037705 (City Locks) | https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=02037500,02037705&seriesCatalogOutput=true&outputDataTypeCd=iv,dv | Stage at Westham and City Locks both begin Oct. 1, 2007. |
| S12 | NWS National Water Prediction Service, gauge RMDV2 (James River at Richmond-Westham) flood categories | https://api.water.noaa.gov/nwps/v1/gauges/RMDV2 | JSON. |
| S13 | NOAA Atlas 14, Volume 2, Version 3, PFDS, partial-duration depths, at downtown Richmond (37.5350, -77.4300) and at RIC (37.5115, -77.3234) | https://hdsc.nws.noaa.gov/cgi-bin/new/cgi_readH5.py?lat=37.5350&lon=-77.4300&type=pf&data=depth&units=english&series=pds | Rows 5 min to 24 h; columns 1, 2, 5, 10, 25, 50, 100, 200, 500, 1,000 years. |
| S14 | NOAA/NWS Analysis of Record for Calibration (AORC) v1.1, 1 km hourly precipitation, Zarr | s3://noaa-nws-aorc-v1-1-1km/2004.zarr (listing: https://noaa-nws-aorc-v1-1-1km.s3.amazonaws.com/) | My extraction; nearest grid cell to each point; time label is hour ending (checked against S8). |
| S15 | FEMA DR-1544-VA page, and OpenFEMA declarations API | https://www.fema.gov/disaster/1544 ; https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$filter=disasterNumber%20eq%201544 | |
| S41 | USGS 3DEP Elevation Point Query Service, spot elevations (feet, NAVD88) | https://epqs.nationalmap.gov/v1/json | My queries at approximate coordinates; see gaston-water.md. |
| S42 | USGS Watershed Boundary Dataset, HUC12 layer | https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/6 | |
| S46 | NCEP/EMC Stage IV, NSF NCAR EOL dataset 21.093 | https://data.ucar.edu/dataset/ncep-emc-4km-gridded-data-grib-stage-iv-data ; DOI https://doi.org/10.5065/D6PG1QDD | The EOL page itself needs JavaScript and returned nothing; the UCAR catalog page answered. |
| S47 | NEXRAD Level II, KAKQ, Aug. 30, 2004 (Unidata bucket on AWS) | https://unidata-nexrad-level2.s3.amazonaws.com/?list-type=2&prefix=2004/08/30/KAKQ/ | 339 volume files listed, 00:01 to 23:56 UTC. |
| S48 | Iowa Environmental Mesonet, ASOS one-minute archive, RIC | https://mesonet.agron.iastate.edu/cgi-bin/request/asos1min.py | Precipitation all missing 17-03 UTC that night. |
| S49 | WPC tropical cyclone rainfall pages (D. Roth) | https://www.wpc.ncep.noaa.gov/tropical/rain/gaston2004.html (also camille1969, agnes1972, juan1985, fran1996, isabel2003, floyd1999, connie1955) | GIF maps. |
| S50 | NWS Wakefield, July 15, 2025 flooding page | https://www.weather.gov/akq/Jul152025_Flooding | |
| S53 | NWS MARFC flood event sheet, Aug. 31, 2004 (Matoaca, Appomattox River) | https://www.weather.gov/media/marfc/Flood_Events_2016/2004/Aug31%2C2004.pdf | |
| S54 | NCEI Storm Events bulk details files, 1950-2026 (77 files) | https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/ | Filtered for Virginia, Richmond city, and "Shockoe" in narratives. Before 1996 the database holds only tornado, wind and hail. |
| S55 | GHCN-Daily, RIC (USW00013740), full daily record 1939-03-01 to 2026-11-20 | https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&dataTypes=PRCP&stations=USW00013740&startDate=1930-01-01&endDate=2026-11-20&units=standard&format=csv | Calendar days, local standard time. |
| S45 | CoCoRaHS data export, Virginia, report date Aug. 31, 2004 and June 3, 2008 | https://data.cocorahs.org/export/exportreports.aspx?ReportType=Daily&dtf=1&Format=CSV&State=VA&ReportDateType=reportdate&StartDate=8/31/2004&EndDate=8/31/2004 | 2004: header only, no reports. 2008: reports present. |

## Primary: City of Richmond and its engineers

| Key | Source | URL | Notes |
|---|---|---|---|
| S16 | Steidel, R. C., R. Stone, L. Liang, E. J. Cronin, F. E. Maisch, "Downtown Shall Not Flood Again," WEFTEC 2006, pp. 3769-3795 (abstract only; full text is paywalled) | https://www.accesswater.org/publications/proceedings/-293573/downtown-shall-not-flood-again | Steidel was a senior Richmond DPU official. I read the abstract only. |
| S39 | Richmond DPU, Combined Sewer System Final Plan Report (May 30, 2024; 86 pp.) | https://www.rva.gov/sites/default/files/2024-08/Final%20Plan%20Report%202024%200530.pdf | PDF p15 (history, Fig. 2-1), p20 (12,000-acre system), p21 (Table 3-1, outfall volumes), p36 (Shockoe Retention Basin 35 MG). |
| S40 | City of Richmond, Shockoe Small Area Plan (August 2023) | https://rva.gov/sites/default/files/2023-08/082023_ShockoePlanFinal_0.pdf | PDF p42, "Flood Hazard" (8,000-acre watershed; Greeley and Hansen H&H study, 2022); p44 (impervious surfaces); p46 (list of studies); p25 and p88 (Camille, Agnes and Gaston in the district timeline). |
| S38 | City of Richmond DPU, "Floodwall FAQs" | https://www.rva.gov/public-utilities/news/floodwall-faqs | Read in two parts (page is over 100,000 characters). |
| S37 | Historical Marker Database, "Richmond Local Flood Protection" marker, Dock & 17th streets | https://www.hmdb.org/m.asp?m=23953 | Transcribes the city/USACE marker. |

## News and secondary (eyewitness detail and reported statements)

| Key | Source | URL |
|---|---|---|
| S17 | Adam Stone, "Recovery: Area Struck by 2004 Hurricane Improves Drainage," Government Technology / Emergency Management, July 9, 2009 | https://www.govtech.com/em/disaster/recovery-area-struck-by.html |
| S18 | "Shockoe businesses sue city for $31 million," Richmond BizSense, Aug. 28, 2009 | https://richmondbizsense.com/2009/08/28/shockoe-businesses-sue-city-for-31-million/ |
| S19 | "Businesses Sue over Virginia Flooding in 2004," Claims Journal (AP), Aug. 31, 2009 | https://www.claimsjournal.com/news/east/2009/08/31/103384.htm |
| S20 | "Duping the Dopplers," Style Weekly (undated, no byline; context is September 2004) | https://m.styleweekly.com/richmond/duping-the-dopplers/Content?oid=1378080 |
| S21 | "Combined Sewer Overflow (CSO) in Richmond," Virginia Places (Charles Grymes), citing Steidel et al. 2006 and Times-Dispatch articles of Aug. 25 and 29, 2024 | https://www.virginiaplaces.org/waste/csorichmond.html |
| S22 | "Historic Richmond Facing Uncertain Future After Flooding," Insurance Journal (AP), Sept. 20, 2004 | https://www.insurancejournal.com/magazines/mag-features/2004/09/20/46665.htm |
| S23 | "Historic Richmond Hard Hit by Gaston Flooding," Insurance Journal (AP), Sept. 2, 2004 | https://www.insurancejournal.com/news/east/2004/09/02/45479.htm |
| S24 | "Gaston Flooding Devastates Richmond," Fox News (AP), Sept. 1, 2004 | https://www.foxnews.com/story/gaston-flooding-devastates-richmond |
| S25 | "Gaston Kills 5; Parts of Richmond Condemned," Fox News (AP), Aug. 31, 2004 | https://www.foxnews.com/story/gaston-kills-5-parts-of-richmond-condemned.amp |
| S26 | NBC News (AP), Richmond flooding, early September 2004 | https://www.nbcnews.com/id/wbna5851220 |
| S27 | "Virginia flooding kills five," Spokesman-Review (AP), Sept. 1, 2004 | https://www.spokesman.com/stories/2004/sep/01/virginia-flooding-kills-five/ |
| S28 | "Bottom's Up," Washington Post, Nov. 30, 2004 | https://www.washingtonpost.com/wp-dyn/articles/A23727-2004Nov30.html |
| S29 | Kelly Avellino, "Is Richmond's floodwall enough during a hurricane over the city?" NBC12, Sept. 1, 2017 | https://www.12onyourside.com/story/36268074/is-richmonds-floodwall-enough-during-a-hurricane-over-the-city/ |
| S30 | Kelly Avellino, "Richmond in best position since Gaston to withstand Florence," NBC12, Sept. 11, 2018 | https://www.12onyourside.com/2018/09/11/richmond-best-position-since-gaston-withstand-florence-floodwalls-likely-wont-close/ |
| S31 | "Remembering the destruction of Hurricane Gaston 18 years later," NBC12, Aug. 30, 2022 | https://www.12onyourside.com/2022/08/30/remembering-destruction-hurricane-gaston-18-years-later/ |
| S32 | "Remembering Gaston and how it changed Richmond," NBC12, Aug. 30, 2024 | https://www.12onyourside.com/2024/08/30/watch-live-remembering-gaston-how-it-changed-richmond/ |
| S33 | "Richmond Remembers: How Gaston flooded Shockoe Bottom," WTVR, Aug. 30, 2024 | https://wtvr.com/news/local-news/richmond-remembers-tropical-storm-gaston-aug-30-2024 |
| S34 | "Monster sinkhole from Gaston," WTVR, Aug. 22, 2014 | https://www.wtvr.com/2014/08/22/monster-sinkhole-from-gaston |
| S35 | Sean Sublette, "Helene's impact on Richmond, and remembering Gaston," The Richmonder, Sept. 24, 2024 | https://www.richmonder.org/helene-and-the-hidden-creek-2/ |
| S36 | "Otherwise Known As 'Chyinek'," Richmond magazine, Sept. 27, 2013 | https://richmondmagazine.com/news/shockoe-creek-history/ |
| S43 | Wikipedia, "Hurricane Gaston (2004)" (used only as a pointer to other sources; nothing rests on it alone) | https://en.wikipedia.org/wiki/Hurricane_Gaston_(2004) |
| S44 | "The history of Richmond's nearly 30-year-old Flood Wall," NBC12, Sept. 4, 2024 | https://www.12onyourside.com/2024/09/04/history-richmonds-nearly-30-year-old-flood-wall/ |
| S51 | "Flash flood warnings swamp Richmond in 2025," Axios Richmond, July 18, 2025 | https://www.axios.com/local/richmond/2025/07/18/richmond-weather-flash-flood-warnings-record |
| S52 | "Richmond & VA Floods" compilation (glenallenweather.com; no compiler named) | https://glenallenweather.com/upload/richmondclimate/Richmond%20&%20VA%20Floods.pdf |

## Fetches that were refused (not worked around)

- NCEI Storm Events per-event page, https://www.ncdc.noaa.gov/stormevents/eventdetails.jsp?id=5421493 : robots refused. (The same database's public bulk files were used instead, S5.)
- Richmond Free Press, Sept. 9, 2004, on Virginia Chronicle: https://www.virginiachronicle.com/?a=d&d=RFP20040909.1.7 : robots refused.
- Virginia DCR, Richmond-Crater hazard mitigation document cited by Wikipedia for the 2008-2010 sewer gates, inlets and buyouts: https://www.dcr.virginia.gov/dam-safety-and-floodplains/document/cfpf/510129-CityofRichmond-1942-CFPF.pdf : client error.
- Richmond DPU, CSO Interim Plan Report (2021): https://rvah2o.org/wp-content/uploads/2021/07/Interim-Plan-Report-2021-0617-1.pdf : HTTP 403.
- Style Weekly, "At First Flush" (2010, Shockoe Retention Basin sludge): https://styleweekly.com/richmond/at-first-flush/Content?oid=1369472 : client error.
- WRIC, "Flooding, water damage among major concerns for Shockoe Bottom residents": client error.
- Colorado State news release on CoCoRaHS expansion in 2008: redirect loop. (CoCoRaHS's own export, S45, answered the question.)
- City of Richmond press release on Dock Street floodwall activation (rva.gov): redirect loop.
- Times-Dispatch articles (Aug. 25 and 29, 2024) were not fetched directly; they are known here only through S21.
