# James River floods at Richmond, 1771 to 2025

All sources were read on November 23, 2026. Machine-readable version: `floods.json` (built by
`tools/build_floods_json.py`, which holds every conversion). Rainfall and Tropical Storm Gaston
(2004) are covered by the other agent; Gaston was a creek and sewer flood, not a river flood, and
is left out here.

## How to read the numbers

Richmond has two river gauges, and they measure different things.

- **Westham** (USGS 02037500, NWS RMDV2, "James River near Richmond") sits on the left bank just
  upstream of the Huguenot Bridge, above the falls. It has measured stage and flow since
  October 1934. Its stage is feet above a gauge zero of 98.82 ft NGVD29 (98.04 ft NAVD88 by the
  current USGS survey). Its flow figures include water in the Kanawha Canal, and above 18.2 ft the
  river and canal exchange water (WDR 1986, PDF p. 230).
- **City Locks** (USGS 02037705, NWS RICV2) sits at the canal's tidewater entrance at the foot of
  Pear Street, below the falls, in the tidal reach. It gives no flow. Its record mixes three
  gauge zeros: a Weather Bureau gauge near Mayo's Bridge read 2.36 ft above NGVD29 until 1956; the
  gauge at the Locks read from 0.0 NGVD29 from September 1957; and today it reports elevation in
  NAVD88 directly (USGS elevation series from October 1, 2007). See `datums.md`.

A Locks crest and a Westham crest are not comparable numbers. The surface falls about 90 ft
between them in a big flood.

"Elev" columns below are feet above NAVD88. Values marked *derived* are computed here from a
published stage and a published gauge datum; they are not printed in any source.

## The table

Rank is by water level at City Locks (NGVD29). For floods measured before 1957 at the old gauge
near Mayo's Bridge, 1.3 ft is taken off to estimate the Locks level: the 1936 and 1969 floods both
show a 1.3 to 1.4 ft drop over that 0.9 mi (HA-410 Table 1 and Figure 1; PP 924 Table A4).

| Rank | Flood | Date of crest | Cause | Westham stage / flow | Westham elev NAVD88 (derived) | City Locks crest as published | City Locks elev NAVD88 (derived) |
|---|---|---|---|---|---|---|---|
| 1 | Great Fresh | May 27, 1771 | 10 to 12 days of rain in the Blue Ridge | none | none | "c38" ft on old WB scale (Corps, from diaries) | about 39.3 at Mayo's Bridge; UNCONFIRMED |
| 2 | Agnes | June 23, 1972 | Tropical Storm Agnes | 28.62 ft / 313,000 cfs (record) | 126.66 | 36.5 ft (record of the gauge era), 4 p.m. | 35.47; sign says 35.5 |
| 3 | Election Day flood (Juan) | Nov. 7, 1985 | Juan moisture then a stalled coastal low | 24.77 ft / 218,000 cfs | 122.81 | 30.76 ft | 29.73 |
| 4 | Camille | Aug. 22, 1969 (Locks 6 a.m.) | remnants of Hurricane Camille | 24.95 ft / 222,000 cfs | 122.99 | 28.64 ft | 27.61 |
| 5 | November 1877 | Nov. 26, 1877 | UNCONFIRMED | none | none | 29.0 ft msl at mile 104.6 | 27.97 at Mayo's Bridge |
| 6 | March 1936 | Mar. 19-20, 1936 | two rains on snowmelt | 23.42 ft / 175,000 cfs | 121.46 | 26.5 ft (old WB scale) | 27.83 at Mayo's; 26.47 at Locks (PP 924 gives 27.5 NGVD29) |
| 7 | April 1937 | Apr. 27, 1937 | statewide heavy rain | 22.65 ft / 152,000 cfs (daily mean; true peak higher) | 120.69 | 25.2 ft (old WB scale) | 26.53 at Mayo's |
| 8 | October 1870 | Oct. 1, 1870 | UNCONFIRMED | none | none | 27.5 ft msl at mile 104.6 | 26.47 at Mayo's |
| 9 | June 1889 | June 2, 1889 | UNCONFIRMED | none | none | 26.6 ft msl at mile 104.6 | 25.57 at Mayo's |
| 10 | Labor Day storm | Sept. 7, 1935 | 1935 Labor Day hurricane remnants | 21.01 ft / 127,000 cfs | 119.05 | 23.65 ft (old WB scale) | 24.98 at Mayo's |
| 11 | August 1940 | Aug. 18, 1940 | 1940 Southeast hurricane | 21.80 ft / 151,000 cfs | 119.84 | 23.3 ft (old WB scale) | 24.63 at Mayo's |
| 12 | April 1886 | Apr. 2, 1886 | UNCONFIRMED | none | none | 25.6 ft msl at mile 104.6 | 24.57 at Mayo's |
| 13 | December 1901 | Dec. 31, 1901 | UNCONFIRMED | none | none | 23.2 ft (old WB scale) | 24.53 at Mayo's |
| 14 | October 1972 | Oct. 7, 1972 | low and cold front, 6 to 8 in upstream | 21.76 ft / 162,000 cfs | 119.80 | 24.2 ft | 23.17 |
| 15 | Fran | Sept. 8, 1996 | remnants of Hurricane Fran | 21.23 ft / 152,000 cfs | 119.27 | 23.75 ft (city: 23.8) | 22.72 |
| 16 | September 1944 | Sept. 20-21, 1944 | UNCONFIRMED (no NWS summary) | 21.80 ft / 150,000 cfs | 119.84 | 22.4 ft (old WB scale) | 23.73 at Mayo's |
| 17 | February 1979 | Feb. 27, 1979 | UNCONFIRMED | 20.38 ft / 138,000 cfs | 118.42 | 22.5 ft | 21.47 |
| 18 | Blizzard melt | Jan. 21-22, 1996 | 2 to 4 ft of snow melted by rain | 20.63 ft / 141,000 cfs | 118.67 | 22.05 ft (city: 22) | 21.02 |
| 19 | November 2020 | Nov. 14, 2020 | heavy rain in the western basin | 18.33 ft / 108,000 cfs | 116.37 | 16.96 ft | 16.96 (already NAVD88) |
| 20 | February 2003 | Feb. 25, 2003 | UNCONFIRMED | 18.73 ft / 113,000 cfs | 116.77 | 17.76 ft | 16.73 |
| 21 | January 2010 | Jan. 27, 2010 | UNCONFIRMED | 18.10 ft / 104,000 cfs | 116.14 | 15.92 ft | datum UNCONFIRMED (15.92 or 16.93) |
| 22 | February 2025 | Feb. 18, 2025 | winter storms | 17.14 ft / 91,600 cfs (NWS provisional 17.23 / 92,822) | 115.18 | 14.62 ft | 14.62 |
| none | April 1987 | Apr. 18, 1987 | strong cyclone | 21.91 ft / 163,000 cfs | 119.95 | not in NWS list | none |
| none | September 1816 | Sept. 18, 1816 | tropical storm | none | none | none ("slightly lower" than the 1814 fresh) | none |

Sources for the table:

- Westham stage, flow and time: USGS annual peak file,
  https://nwis.waterdata.usgs.gov/nwis/peak?site_no=02037500&agency_cd=USGS&format=rdb. The
  January 1996 peak is not the 1996 water-year peak, so it comes from the NWS crest list,
  https://api.water.noaa.gov/nwps/v1/gauges/rmdv2 (flood.crests.historic).
- City Locks crests: NWS crest list, https://api.water.noaa.gov/nwps/v1/gauges/ricv2
  (flood.crests.historic). Camille's 28.64 ft and 6 a.m. time: USGS OFR 70-51, station
  02-0377.00, printed p. 119 (PDF p. 131), https://pubs.usgs.gov/of/1970/0051/report.pdf.
  Agnes's time: NOAA disaster survey report (below).
- 1870, 1877, 1886, 1889 and the cross-check of every pre-1957 crest: USGS Hydrologic Atlas
  HA-410, Table 1 "Peak stages, James River at Richmond," elevations above mean sea level at river
  mile 104.6, https://pubs.usgs.gov/ha/410/plate-1.pdf. The four 19th-century values carry the
  footnote "U.S. Army Corps of Engineers flood plain report, Norfolk district, September 1965."
- 1771: OFR 70-51 Table 2, printed p. 20 (PDF p. 32), "Richmond (at) c38" with datum 2.36, "c"
  meaning from Corps reports; and station page p. 119: "Stage, 38 ft May 27, 1771 (from report by
  Corps of Engineers)." The text calls the 1771 and 1795 values "determined from authenticated
  diary accounts."
- 1936 at the Locks: USGS Professional Paper 924, Table A4, PDF p. 406,
  https://pubs.usgs.gov/pp/0924/report.pdf.

Every pre-1957 NWS Locks crest that HA-410 also lists matches it once 2.36 ft is added (1901,
1906, 1919, 1924, 1935, 1936, 1937, 1940, 1942, 1944, 1948 all agree within 0.1 ft). That is the
strongest evidence that the NWS list mixes gauge zeros. The NWS "olddatum" flags do not follow
this rule (1936 and 1937 are flagged, 1935 and 1940 are not; October 1972 is flagged, Fran is
not), so the flags should be ignored.

## Disagreements recorded

- **1771 height.** Corps/USGS: 38 ft on the old Weather Bureau scale, about 40.4 ft NGVD29 at
  Mayo's Bridge (derived). Henrico County: "a flood stage of 45 feet above normal"
  (https://henrico.gov/locations/flood/). Richmond Family Magazine: a "record of 30 feet"
  (https://richmondfamilymagazine.com/community/history/water-water-everywhere/, July 30, 2019).
  Watson says a 40 ft figure in 1771 accounts was a ship's sounding near Warwick, not a Richmond
  stage (https://corpora.tika.apache.org/base/docs/govdocs1/204/204582.html). I trust the
  Corps/USGS figure as the only one tied to a gauge scale, but it rests on diaries and is
  UNCONFIRMED as an elevation. Taken at face value, 1771 was about 2 to 3 ft above Agnes at
  Mayo's Bridge.
- **Agnes in 1971 or 1972.** The City Locks River Gauge marker (Friends of James River Park,
  https://www.hmdb.org/m.asp?m=61821) says 1971. Every agency source says June 23, 1972.
- **Agnes at Westham "26 ft."** 12 On Your Side (Sept. 4, 2024) gives 26 ft; USGS gives 28.62.
  The TV figure is wrong.
- **Juan at the Locks.** 30.76 ft (NWS), 30.8 (Watson; RVANews), 30.7 (Friends marker), "31 feet"
  (city DPU, Holmberg). Same event, rounded differently.
- **1936 at the Locks.** NWS stage 26.5 on the old scale (28.86 NGVD29 at Mayo's Bridge, matches
  HA-410's 28.8) versus PP 924's 27.5 NGVD29 "at city locks." Both can be right: the second is at
  the newer site 0.9 mi downstream. NWS dates the 1936 Locks crest March 30; HA-410 says March 20
  and the Westham peak was March 19. I trust March 20.
- **May 1901.** HA-410 lists May 24, 1901 at 21.6 ft msl; NWS lists March 24, 1901 at 19.3 ft
  (= 21.66 msl). Same stage, different month. UNCONFIRMED which.
- **Agnes bridges.** NOAA's 1972 disaster report says 4 of 5 bridges were closed; the NWS Virginia
  flood page says 4 of 5 were destroyed (https://www.weather.gov/safety/flood-states-va). I trust
  the 1972 report: "closed."
- **Gauge record start.** The Friends marker says Locks monitoring began in 1882; the USGS 1986
  report says the Weather Bureau gauge near Mayo's Bridge ran from 1876 to 1956
  (https://pubs.usgs.gov/wdr/1986/va-86-1/report.pdf, PDF p. 230). I trust USGS.

## What flooded, by event

Street-level detail is thin in the sources I could reach. What is supported:

- **1771.** Buildings, boats and animals in Richmond destroyed; about 150 deaths along the river
  (Henrico County page). Upstream, tobacco warehouses and a public store were lost at a Cumberland
  County port (Library of Virginia, https://uncommonwealth.lva.virginia.gov/blog/2011/06/09/a-river-runs-through-it/).
  The 1771 stone marker stands on a hill at Curles Neck, Henrico, 12.3 mi below Richmond; it is not
  a Richmond high-water mark.
- **1936.** "Serious flooding of industrial and business sections" (Watson). Surveyed high-water
  marks exist along the river (HA-410 Figure 1).
- **1969 Camille.** Advance warning limited losses, but "serious flooding occurred in the lower
  elevations of the city," with photos of Main Street and I-95 (OFR 70-51, printed p. 22). The
  flooded area is mapped on USGS HA-409 (Bon Air), HA-410 (Richmond) and HA-411 (Drewrys Bluff).
  On HA-410 (my reading of the plate) the flooded area covers the Shockoe Valley floor up to about
  Main Street Station, all of Mayo Island, the Manchester flats between the river and roughly
  Commerce Road including the sewage treatment plant, the Gillies Creek valley through Fulton
  east toward Government Road, a strip at Rocketts, and the canal and Tredegar ground along the
  north bank above the Mayo Bridge. The VCU planning slide collection has 1969 photos of the
  Boulevard Bridge, Byrd Street, East Main Street, Riverside Drive and the rail tracks.
- **1972 Agnes.** Evacuation of low-lying areas from the morning of June 22; downtown lost power,
  drinking water and communications by June 23; the water purification plant was inundated; VEPCO
  lost a generating station and its dispatch center; 4 of 5 James bridges closed; the National
  Guard cordoned parts of the city (NOAA, Final Report of the Disaster Survey Team on the Events of
  Agnes, October 1972,
  https://www.govinfo.gov/content/pkg/CZIC-gb70-9-u55-1972/html/CZIC-gb70-9-u55-1972.htm). Water,
  sewage, electric and gas plants flooded; only one of five bridges usable; downtown closed for
  several days (USGS PP 924, PDF p. 95). At Dock and Pear streets the water stood 17 ft above
  ground; at Tredegar Street and Brown's Island Way, 3 ft (city/FEMA/USACE/NWS/USGS signs). Water
  reached 7th Street on the Southside and passed Marshall Street downtown; the 14th Street
  (Mayo) Bridge went under; Gillies Creek backed up into Fulton (Richmond Family Magazine, 2019;
  secondary, UNCONFIRMED by an agency source). Deaths and damage for Richmond alone: the signs say
  13 local deaths and over $140 million local damage; NOAA reports 5 deaths along the James.
- **1985.** "Several blocks of commercial and industrial buildings" flooded (Watson); "flooded
  several blocks of Downtown Richmond" (James River Association,
  https://thejamesriver.org/historic-james-river-crests/). UNCONFIRMED which blocks.
- **1996 January and September.** First floods after the wall. Some gates closed, including Dock
  Street (RVANews, May 12, 2011, https://rvanews.com/?p=41409).
- **2020 and 2025.** Floodwall closures; see `floodwall.md`.

## NWS impact stages (what floods at what level, today)

These are the NWS's current impact statements and are the best key from a crest to named places.
Read November 23, 2026 from the two NWPS records above.

City Locks (feet NAVD88): 8 minor flooding; 9 Ancarrow's boat landing closed; 11 Rocketts
Landing park and the Capital Trail begin to flood; 12.5 water covers Wharf Street and enters the
Tunnel Building; 18.5 treatment plant access from Maury into Brander Street flooded; 19 moderate,
Brander Street closed; 23 Tredegar Street closed; 24 Mayo Bridge closed; 27 21st and Cary
closed; 28 major; 29 Goodes Street closed; 33.5 near record; 35.5 record flooding begins;
41 "Flood wall is overtopped."

Westham (feet above gauge zero): 12 flood stage; 13.5 Huguenot Flatwater park; 14 Riverside Drive
begins to flood; 16 Pony Pasture parking; 17 homes near the gauge; 18.2 CSX tracks flooded;
22 major, riverfront industries and streets flooded; 23 city water filtration plant endangered;
27 near record; 28.62 record.

## Recommendation: which floods to draw

Draw seven, in this order of priority:

1. **Agnes, 1972.** The record of the gauge era and the reason the wall exists. Three agency
   elevations (both gauges plus two signs) and a mapped extent are possible.
2. **Camille, 1969.** The best documented: USGS mapped the flooded area on three quadrangles and
   drew a water-surface profile through the falls (HA-410). It is the calibration flood for the
   whole series.
3. **Election Day, 1985.** Third highest at the Locks and the flood that got the wall authorized
   the next year.
4. **March 1936.** The largest before Camille, with surveyed high-water marks on the HA-410
   profile; shows the industrial riverfront at its peak.
5. **Fran, 1996.** The highest water since the wall; the wall's first real use. The natural
   "after" picture.
6. **November 2020.** A modern flood measured in NAVD88 at both gauges, with gate closures on
   record, drawn on current lidar with no datum guesswork.
7. **1771 (optional).** The legend. Draw it only as an explicitly uncertain surface (about
   39 ft NAVD88 near Mayo's Bridge, plus or minus several feet), on modern terrain, labeled as an
   estimate.

A strong companion plate: **Agnes with the wall.** Agnes's 35.5 ft NAVD88 at the Locks is below
the NWS's 41 ft overtopping stage, so the same water today would be held out of Shockoe Bottom
and the Manchester flats (interior drainage aside).

Skip 1870, 1877, 1886 and 1889 as standalone plates: one elevation each, no extent, no cause on
record here. Skip 1987 and October 1972: no Locks crest (1987) or nothing to add.
