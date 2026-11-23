# Water-surface elevations for drawing floods on lidar

All sources read November 23, 2026. Lidar for Richmond is in NAVD88 (the 2025 City of Richmond
lidar is NAVD88, GEOID18, US feet). Every flood below is given in NAVD88 feet.

## Answer first

- **Conversion at Richmond:** NAVD88 = NGVD29 minus 1.03 ft. NGS's NCAT tool returns
  minus 0.313 m (sigma 0.004 to 0.005 m) at both gauge sites
  (https://geodesy.noaa.gov/api/ncat/llh with inVertDatum=NGVD29, outVertDatum=NAVD88).
  Everything printed before about 1990 that says "mean sea level" or "msl" at Richmond means
  NGVD29 (the Sea Level Datum of 1929).
- **Westham gauge zero:** 98.82 ft NGVD29 in every published source from 1969 to 2020;
  98.04 ft NAVD88 in the current USGS site record (GNSS survey, accuracy 0.08 ft). Converting
  98.82 gives 97.79 ft NAVD88, so the two disagree by 0.25 ft. Use 98.04 for drawing and carry
  0.25 ft of uncertainty.
- **City Locks gauge zero:** three eras. Before September 1957, a Weather Bureau gauge 0.9 mi
  upstream near Mayo's Bridge with zero at 2.36 ft NGVD29. From September 1957, at the City Locks
  with zero at 0.0 ft NGVD29. Now 0.0 ft NAVD88 (USGS 02037705 reports NAVD88 elevation; series
  begins October 1, 2007). The exact switch date is UNCONFIRMED, and one NWS crest (January 2010)
  sits 1 ft off a NOAA record of the same flood.
- **The surface is nearly flat below the Mayo Bridge and steep above it.** In 1969 the flood
  surface rose only 1.3 ft from the Locks to Mayo's Bridge (0.9 mi), then about 10 ft through the
  rapids at the 9th Street (Manchester) Bridge, about 14 ft more to the Lee Bridge, and about
  40 ft to the Boulevard Bridge (USGS HA-410 Figure 1). Shockoe Bottom, Manchester, Rocketts and
  Fulton all sit on the flat reach. For them, one level per flood is enough.
- **What can be supported per flood:** a sloped profile through the falls only for 1936 (marks),
  1937 (Corps marks) and 1969 (USGS, partly built from 1937). For Agnes: three to four points.
  For everything else: a level at one or both gauges.

## (a) Gauge datums

| Gauge | Period | Gauge zero | Source (read 2026-11-23) |
|---|---|---|---|
| Westham, USGS 02037500 | 1934 to present | 98.82 ft NGVD29 | OFR 70-51 station page, printed p. 118 (PDF p. 130), https://pubs.usgs.gov/of/1970/0051/report.pdf; PP 924 station 612, PDF p. 267, https://pubs.usgs.gov/pp/0924/report.pdf; WDR 1986, PDF p. 230, https://pubs.usgs.gov/wdr/1986/va-86-1/report.pdf; MARFC "Gage Datum: 98.82 ft MSL," https://www.weather.gov/media/marfc/Top20/JMS/Richmond.pdf |
| Westham | current | 98.04 ft NAVD88, GNSS level 2, accuracy 0.08 ft | https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=02037500&siteOutput=expanded (alt_va, alt_meth_cd X, alt_datum_cd NAVD88); same in https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations/items/USGS-02037500?f=json ; NWS NWPS datum value 98.04 NAVD88 |
| City Locks (Weather Bureau 02-0377.00) | 1876 to Aug. 1957 | 2.36 ft NGVD29, at a site 0.9 mi upstream near Mayo's Bridge (old river mile 104.6) | OFR 70-51 Table 2 (printed p. 20) and station page p. 119: "Prior to September 1957, at site 0.9 mile upstream at datum 2.36 ft higher"; WDR 1986 p. 230 gives 1876 to 1956 near Mayo's Bridge |
| City Locks (02-0377.00, then 02037705) | Sept. 1957 to about 2007 | 0.0 ft NGVD29, "at City Locks entrance to Kanawha Canal ... just south of Dock Street and foot of Pear Street" | OFR 70-51 p. 119 |
| City Locks, USGS 02037705 | Oct. 2007 to present | 0.0 ft NAVD88; elevation parameter 62620 | site file alt_va 0.00 NAVD88 (leveled, 0.01 ft); series catalog shows 62620 from 2007-10-01, https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=02037705&seriesCatalogOutput=true |
| NOAA tide station 8638495 "Richmond River Locks" | 2007 to Sept. 2010 | station datum labeled NAVD88; MHHW 2.87 ft, MSL 1.11 ft, MLLW minus 0.81 ft on it | https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/8638495/datums.json ; benchmark sheet https://tidesandcurrents.noaa.gov/benchmarks/8638495.html (published 01/14/2011) |

Evidence that the NWS City Locks crest list mixes zeros:

1. Each pre-1957 NWS crest plus 2.36 ft equals the HA-410 Table 1 elevation within 0.1 ft (eleven
   floods checked; see `floods.md`).
2. The NWS's own impact table at City Locks says "Record flooding begins" at 35.5 ft. Agnes was
   36.5 ft on the 1957 NGVD29 gauge, which is 35.47 ft NAVD88. So the impact table is in NAVD88
   and the Agnes crest in the same record is in NGVD29.
3. The Agnes High Water Mark sign at Dock and Pear streets, a few hundred feet from the gauge,
   gives 35.5 ft NAVD88 (https://www.hmdb.org/m.asp?m=133685).

The open problem is the 2007 to 2010 period. NOAA gives the highest water at 8638495 as
5.408 m above MLLW on January 27, 2010, which is 16.93 ft on the station datum the API labels
NAVD88. NWS gives 15.92 ft for the same crest. The gap (1.01 ft) is the datum shift, but it runs
the wrong way for an NGVD29 reading. Either NOAA's station datum is not NAVD88 or the NWS value
was converted twice. UNCONFIRMED. The 2020 and 2025 crests come from the USGS NAVD88 series and
are taken as NAVD88.

Note on river miles. Two mileage systems appear. The 1969 and HA-410 figures put Westham at
mile 111.7 and the City Locks at 103.7; the 1972 and 1986 reports put them at 116.6 and 108.7.
Use names and coordinates, not miles.

## (b) Crest elevations at the gauges, NAVD88

Westham NAVD88 = stage + 98.04 (or + 97.79 by converting the old NGVD29 zero; the lower figure
is in brackets). City Locks NAVD88 as explained above. All derived here except where noted.

| Flood | Westham stage | Westham NAVD88 | City Locks NAVD88 | Where the Locks value applies |
|---|---|---|---|---|
| 1771 | none | none | about 39.3 (UNCONFIRMED) | near Mayo's Bridge |
| 1936 March | 23.42 | 121.46 [121.21] | 27.83 at Mayo's; 26.47 at Locks (PP 924 gives 27.5 NGVD29 at the Locks) | both |
| 1937 April | 22.65 | 120.69 [120.44] | 26.53 | near Mayo's Bridge |
| 1969 Camille | 24.95 | 122.99 [122.74] | 27.61 at Locks; 28.87 at Mayo's (HA-410 29.9 NGVD29) | both |
| 1972 Agnes | 28.62 | 126.66 [126.41] | 35.47 (sign: 35.5) | Locks |
| 1985 | 24.77 | 122.81 [122.56] | 29.73 | Locks |
| 1996 January | 20.63 | 118.67 [118.42] | 21.02 | Locks |
| 1996 Fran | 21.23 | 119.27 [119.02] | 22.72 | Locks |
| 2003 February | 18.73 | 116.77 [116.52] | 16.73 | Locks |
| 2020 November | 18.33 | 116.37 [116.12] | 16.96 | Locks |
| 2025 February | 17.14 | 115.18 [114.93] | 14.62 | Locks |

PP 924 Table A4 (PDF p. 406, https://pubs.usgs.gov/pp/0924/report.pdf) prints Westham crests as
122.2 (1936), 123.8 (1969) and 127.4 (1972) ft NGVD29. They equal stage + 98.82, which confirms
the old zero.

## (c) Surveyed high-water marks

| Mark | Location | Flood | Value | Datum | Source |
|---|---|---|---|---|---|
| High Water Mark sign "17 Feet" | Great Shiplock Park, Dock and Pear streets; 37 deg 31.572 min N, 77 deg 25.228 min W | Agnes 1972 | 17 ft above ground, 35.5 ft | NAVD88 | https://www.hmdb.org/m.asp?m=133685 (sign by City DPU, FEMA, USACE Norfolk, NWS, USGS, VDEM, DCR) |
| High Water Mark sign "3 Feet" | Tredegar Street at Brown's Island Way; 37 deg 32.066 min N, 77 deg 26.744 min W | Agnes 1972 | 3 ft above ground, 40 ft | NAVD88 | https://www.hmdb.org/m.asp?m=124035 |
| High Water Mark sign | Pony Pasture Rapids Park | Agnes 1972 | value not found | none | dedicated June 23, 2016; https://www.rva.gov/public-utilities/news/high-water-mark-sign-unveiled-pony-pasture . The release said signs "will follow" at Brown's Island, Plant Zero and Great Shiplock Park; Plant Zero UNCONFIRMED |
| Floodmarks, March 1936 | about 12 points, mile 108.9 to 102.7 | 1936 | read from graph, see profile table | NGVD29 | HA-410 Figure 1 |
| Floodmarks, April 1937 (Corps) | about 25 points | 1937 | read from graph | NGVD29 | HA-410 Figure 1 |
| Floodmarks, August 1969 | about 20 points | 1969 | read from graph | NGVD29 | HA-410 Figure 1 |
| Main Street Station marks | train shed | Agnes and others | NOT FOUND in any source I could reach | none | UNCONFIRMED |
| Floodwall "high-water-mark column" (1771, Agnes, Juan, Camille) | floodwall | several | NOT FOUND in any source I could reach | none | UNCONFIRMED |
| 1771 stone marker | Curles Neck, Henrico, 12.3 mi below Richmond | 1771 | a monument, not a measured mark | none | https://henrico.gov/locations/flood/ |
| USGS OFR 86-486 plates (1985) | 42 plates | 1985 | not read; the plates may carry Richmond marks | unknown | https://pubs.usgs.gov/publication/ofr86486 |

The two Agnes signs do not agree with the 1969 profile. At Tredegar and Brown's Island Way the
sign gives 40 ft NAVD88 (41.0 NGVD29). The 1969 profile at the same reach (between the Lee Bridge
and the 9th Street Bridge) reads about 42 to 43.5 ft NGVD29, yet Agnes was 8 ft higher than
Camille at the Locks and 3.7 ft higher at Westham. Possible reasons: the sign is in slack water
behind Brown's Island and the Haxall Canal, not on the main channel; the 1969 profile in this reach
was "constructed largely on the basis of the profile for the 1937 flood between miles 105 and 107"
(HA-410 text) and may be too high; or the sign's elevation is wrong. Do not interpolate a surface
through the falls from these two numbers. UNCONFIRMED.

## (d) The profile through the city

### Real floods: HA-410 Figure 1

USGS HA-410 (E. M. Miller, 1969), Figure 1, "Flood profile, James River near Richmond," plots
1936 marks, the 1937 profile and the 1969 profile from river mile 109 to 102.7 (old miles; City
Locks 103.7). Values below are read from the plate by eye at about 0.5 ft precision; they are not
published as numbers. Elevations are NGVD29; subtract 1.03 for NAVD88.

| Place (old river mile) | 1936 marks | 1937 | 1969 |
|---|---|---|---|
| Westham gauge (111.7), from gauge | 122.2 | 121.5 | 123.8 |
| Mile 108.9 (near the top of the plot) | 102.5 | 101.8 | 101.2 |
| Mile 108.2 | none | 91.8 | 94.3 |
| Boulevard Bridge (107.5) | 83.0 | 82.3 | 84.9 |
| Mile 107.0 | none | 74.3 | 75 |
| Mile 106.5 | none | 69.5 | 71 |
| Mile 106.1 | none | 64.7 | 66 |
| Mile 105.6 | 44.5 | 44.3 | 44.5 |
| Robert E. Lee Bridge (105.5) | none | 42.0 | 43.5 |
| Mile 105.2 | none | 40.8 | 40.5 to 42 |
| 9th Street (Manchester) Bridge (105.1) | none | 32.0 just below | 38 to 34 dropping |
| Mile 105.0 | none | 30.3 | 32 |
| Mayo's Bridge (104.6) | 28.6 | 27.2 (at 104.5) | 30.2 |
| I-95 (104.25) | 28.0 | 27.0 | 28.8 |
| City Locks (103.7) | 27.4 | 26.6 | 28.6 |
| Mile 103.0 to 102.7 | 27.0 to 26.3 | 25.7 to 25.9 | 28.4 to 28.3 |

The steepest single drop is just below the 9th Street Bridge, where about 8 to 10 ft of fall
happens within a tenth of a mile. Below Mayo's Bridge the surface is close to level; below the
Locks it falls only a few tenths of a foot per mile to the edge of the plot.

### Design floods: FEMA

I could not reach FEMA's Flood Insurance Study for the City of Richmond (community 510129): the
FEMA map servers (prd-floodmaps.msc.fema.gov, hazards.fema.gov) refused connections from this
environment. The profile elevations at named cross sections for the 10, 2, 1 and 0.2 percent
floods are therefore UNCONFIRMED here and are the first thing to get. The FIS is free from
https://msc.fema.gov (search "Richmond, City of"). The 2022 preliminary maps exist under
prelim_issue_date 2022-02-02.

What I did find:

- Design discharges at the Westham gauge (Henrico County FIS, Volume 1, Table 9, printed p. 27,
  PDF p. 36, effective 2021, https://henricolibrary.org/images/FEMA/51087CV001B.pdf):
  10 percent 147,500 cfs; 4 percent 195,900; 2 percent 236,600; 1 percent 281,400;
  0.2 percent 404,400. An older Henrico FIS gives 131,000; 232,000; 290,000; 475,000 for the 10,
  2, 1 and 0.2 percent floods at the "USGS Gage at Westham Bridge"
  (https://www.henricolibrary.org/images/FEMA/2007%20FEMA%20FIS%20Henrico%20County.pdf).
  Agnes (313,000 cfs) falls between today's 1 and 0.2 percent floods.
- By straight-line interpolation between the 1969 and 1972 peaks, the 1 percent flood would
  stand near 27.4 ft at Westham (about 125.4 ft NAVD88). This is my estimate, not FEMA's.
  UNCONFIRMED.
- A 2008 FEMA notice lists the Shockoe Creek base flood elevation at East Franklin Street as
  21 ft, revised to 23 ft NAVD88 (https://regulations.justia.com/regulations/fedreg/2008/04/03/E8-6912.html).
  That is the creek, not the river.

### Modeled surfaces you can use now: USACE / NWS flood inundation maps

The NWS Wakefield office publishes "Richmond Partner FIM," flood inundation maps for both gauges
made by USACE Norfolk District with HEC-RAS on a 5 ft DEM (ArcGIS item
8d12656d99224ac4b599fb270f4d199f, owner NWS.AKQ_noaa, read via
https://www.arcgis.com/sharing/rest/content/items/8d12656d99224ac4b599fb270f4d199f?f=json).
Layers exist for every whole foot:

- City Locks: 8 to 35 ft. Layer names (elev_008 to elev_035) equal the stage, consistent with a
  NAVD88 zero.
- Westham: 11 to 28 ft. Layer names run elev_109_8 (11 ft) to elev_125_8 (27 ft), that is stage
  plus 98.8. The 28 ft layer is elev_126_4 and is labeled "Record Flood at 28.6 ft."

Two cautions. First, the Westham layers imply a gauge zero of 98.8 ft on a NAVD88 DEM, 0.76 ft
above USGS's 98.04; this looks like the old NGVD29 zero used without conversion. UNCONFIRMED until
the USACE technical summary report is read. Second, these are cached image tiles, not elevation
grids; the depth rasters and boundaries would have to be requested from USACE or NWS.

### What each chosen flood can support

| Flood | Below Mayo's Bridge (Shockoe, Manchester, Rocketts, Fulton) | Through the falls | Above the falls (Westham, Riverside Dr.) |
|---|---|---|---|
| 1771 | one estimated level, plus or minus several feet | nothing | nothing |
| 1936 | level from the Locks and Mayo marks (26.4 to 27.8 NAVD88), with a 1.4 ft rise to Mayo's | 1936 marks at a few points; borrow the 1937 shape | Westham 121.46 |
| 1969 | level 27.6 at the Locks rising to 28.9 at Mayo's | full USGS profile (partly built from 1937) and a mapped extent | Westham 122.99 |
| 1972 Agnes | level 35.5 (gauge and sign agree) | one sign point (40.0) that conflicts with the 1969 shape | Westham 126.66 |
| 1985 | level 29.7 | none; scale 1969 shape | Westham 122.81 |
| 1996 Fran | level 22.7 | none; FIM layer for 21 ft Westham / 23 ft Locks | Westham 119.27 |
| 2020 | level 17.0 | none; FIM layers for 18 ft Westham / 17 ft Locks | Westham 116.37 |

For the flat reach, the method is simple and defensible: fill every lidar cell below the flood
level that connects to the river, add up to 1.4 ft of rise between the Locks and the Mayo Bridge,
and treat the floodwall (after 1994) as a barrier. For the falls, either borrow the USACE modeled
surface for the nearest stage, or draw the 1937/1969 profile shape shifted to the flood's gauge
values, and say so in the plate notes.
