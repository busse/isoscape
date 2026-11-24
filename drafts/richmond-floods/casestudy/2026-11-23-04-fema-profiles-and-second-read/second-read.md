# Second reader's check of `river/` (floods.md, floods.json, datums.md, floodwall.md, before-the-wall.md)

Checked November 23, 2026 against the primary sources, using the copies in `river/raw/` first. My arithmetic is in `scripts/recompute.py` (output in `work/recompute.json`). It reproduces every conversion in `river/tools/build_floods_json.py` to 0.01 ft. Elevations are in feet. HA-410 readings are my own, from a 300 dpi render of Figure 1, with a grid overlay (`scripts/ha410_overlay.py`). Precision is about ±0.3 ft at plotted marks and about ±0.7 ft between marks.

## Claims table

### Crests and peaks

| Claim | Earlier value | My value | Source and page | Verdict |
|---|---|---|---|---|
| Agnes, Westham stage and flow | 28.62 ft, 313,000 cfs, June 23, 1972 | same; 0900 hours | USGS peak file (raw); PP 924 station 612 (PDF p. 267); WDR 1986 PDF p. 230 | CONFIRMED |
| Agnes, City Locks crest | 36.5 ft, 4 p.m. | 36.5 ft at 4 p.m. June 23; flood stage reached 3 a.m. June 22 | NOAA Agnes disaster survey report (govinfo); PP 924 Table A4, PDF p. 406 | CONFIRMED |
| Agnes, City Locks NAVD88 | 35.47 | 35.47 (NCAT -1.027); 35.46 (FIS Table 19 interpolated, -1.041) | recompute | CONFIRMED |
| Agnes sign, Dock and Pear streets | 17 ft above ground, 35.5 NAVD88 | same | hmdb 133685 | CONFIRMED |
| Agnes sign, Tredegar St at Browns Island Way | 3 ft, 40 NAVD88 | same; the sign is about 270 m north of the channel centerline | hmdb 124035; OSM projection | CONFIRMED (see disagreement 6) |
| Agnes, Westham NAVD88 | 126.66 (98.04 zero) or 126.41 | both arithmetic right. FEMA uses 126.4 (the converted old zero) | FIS 2025 Table 6, PDF p. 27 | CONFIRMED; FEMA's choice noted |
| Camille, Westham | 24.95 ft, 222,000 cfs, 2400 hours Aug. 21 | same | OFR 70-51 printed p. 118; peak file | CONFIRMED |
| Camille, City Locks | 28.64 ft at 6 a.m. Aug. 22 | 28.64 at 0600 and 0700 Aug. 22 (NWS list rounds to 28.6) | OFR 70-51 printed p. 119 (PDF p. 131) | CONFIRMED |
| Camille at mile 104.6 | 29.9 NGVD29 | 29.9 (HA-410 Table 1). OFR 70-51 Table 2 gives 27.6 on the old scale + 2.36 = 29.96 | HA-410; OFR printed p. 20 | CONFIRMED |
| 1985, Westham | 24.77 ft, 218,000 cfs, 0800 Nov. 7 | same | WDR 1986 PDF p. 230; MARFC 1985 | CONFIRMED |
| 1985, City Locks | 30.76 ft → 29.73 NAVD88 | same. The NGVD29 era is assumed, not stated | NWS crest list | CONFIRMED (datum era by inference) |
| March 1936, Westham | 23.42 ft, 175,000 cfs, Mar. 19 | same | peak file; OFR Table 2 | CONFIRMED |
| March 1936, Locks/Mayo | 26.5 on the old scale → 28.86 at Mayo; PP 924 27.5 at the Locks | same. HA-410 marks near the Locks read 27.2 to 27.5 NGVD29; mark at mile 104.59 reads 28.5; at 104.79, 28.8 | NWS; PP 924 Table A4; HA-410 | CONFIRMED |
| 1936 Locks crest date | NWS Mar. 30, HA-410 Mar. 20 | NWS list does say 1936-03-30 | raw/nwps_ricv2.json | CONFIRMED (the disagreement is real) |
| Fran, Westham | 21.23 ft, 152,000 cfs | same | peak file | CONFIRMED |
| Fran, City Locks | 23.75 → 22.72 | 23.75 confirmed. The NGVD29 era is UNCONFIRMED (no USGS series before Oct. 2007) | NWS | UNCONFIRMED (datum) |
| November 2020, Westham | 18.33 ft, 108,000 cfs | same | peak file | CONFIRMED |
| November 2020, City Locks | 16.96 NAVD88 | 16.96 at 04:48 to 04:54 EST Nov. 14, approved, parameter 62620 (NAVD88) | USGS instantaneous values, fetched today | CONFIRMED |
| January 2010, City Locks | 15.92, datum UNCONFIRMED | 15.92 NAVD88, approved, 18:30 to 18:42 EST Jan. 27 | USGS instantaneous values, parameter 62620 | CORRECTED (resolved: NAVD88) |
| 1771 | c38 on the old scale; about 39.3 NAVD88 at Mayo | c38 and datum 2.36 (Table 2); 38 ft May 27, 1771, from a Corps report (station page). Derived 39.33. The 1998 FIS calls it a 50 to 100-year flood (PDF p. 8) | OFR printed pp. 20, 119 | CONFIRMED as source; elevation UNCONFIRMED |
| 19th-century HA-410 values | 1870 27.5, 1877 29.0, 1886 25.6, 1889 26.6 | same | HA-410 Table 1 | CONFIRMED |

### Datums

| Claim | Earlier value | My value | Source and page | Verdict |
|---|---|---|---|---|
| NGVD29 to NAVD88 at Richmond | -1.03 ft | NCAT -0.313 m = -1.027 ft at Westham. FIS 2025 Table 19: -1.04 at the Locks, -0.98 at Westham (interpolated); county average -1.013 | raw/ncat.json; FIS 2025 PDF p. 49 | CONFIRMED (use -1.03 or -1.04 at the Locks; -0.98 to -1.03 at Westham) |
| Westham zero | 98.82 NGVD29; 98.04 NAVD88 | same. 98.82 - 1.03 = 97.79; with Table 19, 97.84. The gap is 0.20 to 0.25 ft | OFR p. 118; PP 924; WDR 1986; site file | CONFIRMED |
| Old Weather Bureau gauge | 2.36 ft higher, 0.9 mi upstream, before Sept. 1957 | same per OFR. WDR 1986 puts it at mile 109.5 and the Locks at 108.7, so 0.8 mi on the newer mileage | OFR p. 119; WDR p. 230 | CONFIRMED |
| City Locks gauge after 1957 | 0.0 NGVD29 | same | OFR p. 119 | CONFIRMED |
| USGS NAVD88 series at the Locks | from 2007-10-01 | 62620 series from 2007-10-01; site file zero 0.00 NAVD88 | USGS series catalog, fetched today | CONFIRMED |
| NOAA 8638495 vs NWS, Jan. 2010 | gap "runs the wrong way" for an NGVD29 reading | NOAA max 16.929 vs USGS NAVD88 15.92. NOAA is 1.01 ft higher, which is exactly what an NGVD29-referenced number looks like | raw/noaa_8638495_datums.json; USGS | WRONG reasoning (see disagreement 1) |

### HA-410 surface profile

My readings are NGVD29, river miles on HA-410's own mileage.

| Claim | Earlier value | My value | Source and page | Verdict |
|---|---|---|---|---|
| Locks to Mayo rise, 1969 | 1.3 ft | 28.64 → 29.9 to 30.0 = 1.3 ft | OFR; HA-410 | CONFIRMED |
| 1969 at the City Locks (103.7) | 28.6 | 28.5 | HA-410 Figure 1 | CONFIRMED |
| 1969 at I-95 (104.25) | 28.8 | 28.7 (leader at mile 104.20) | HA-410 | CONFIRMED |
| 1969 at Mayo's Bridge (104.6) | 30.2 | 30.0 (leader at 104.59) | HA-410 | CONFIRMED |
| 1969 at the 9th St bridge (105.1) | 38 to 34, dropping | two marks at mile 105.06: 38.1 and 34.4 | HA-410 | CONFIRMED |
| 1969 at Lee Bridge (105.5) | 43.5 | 43.9 ±0.7 | HA-410 | CONFIRMED within precision |
| 1969 at Boulevard Bridge (107.5) | 84.9 | 83.8 ±0.7. The nearest marks are 85.1 at mile 107.59 and 79.4 at 107.28 | HA-410 | CORRECTED |
| 1969 at miles 108.2, 107.0, 106.5, 106.1 | 94.3, 75, 71, 66 | 94.4, 74.7, 70.8, 66.0 | HA-410 | CONFIRMED |
| 1937 at Lee, Boulevard, 108.2 | 42.0, 82.3, 91.8 | 42.0, 82.5, 91.8 | HA-410 | CONFIRMED |
| 1937 at the Locks | 26.6 | 26.3 | HA-410 | CONFIRMED (±0.3) |
| 1936 at Boulevard, 105.6, 108.9 | 83.0, 44.5, 102.5 | 82.9, 44.6, 102.4 | HA-410 | CONFIRMED |
| HA-410 figure range | "Westham gauge (111.7)" row in the profile table | Figure 1 spans miles 109.0 to about 102.5 only. The Westham row is the gauge value, not a plotted point | HA-410 | CONFIRMED with note |

### FIS-related claims

| Claim | Earlier value | My value | Source and page | Verdict |
|---|---|---|---|---|
| FEMA discharges at Westham | 147,500; 195,900; 236,600; 281,400; 404,400 | identical in the Richmond 2025 FIS Table 9 | FIS 2025 PDF p. 32 | CONFIRMED |
| 1% flood at Westham | about 27.4 ft stage (125.4 NAVD88), the earlier agent's estimate | FIS 2025: 124.0 NAVD88 at the gauge station (stage 26.0 on the 98.04 zero) | FIS 2025 panel 22P, PDF p. 111 | CORRECTED |
| FEMA FIS unreachable; profiles UNCONFIRMED | none | now read; see `fis.md` | FIS 2025, 1998 | resolved |
| Gathright Dam effect | no published estimate found | about 1.5 percent of Richmond peak discharges | FIS 1998 PDF p. 9 | CORRECTED |
| Westham flow "includes water in the Kanawha Canal" | yes | Daily discharges exclude canal flow; the 313,000 maximum and the long-term average include it | WDR 1986 PDF p. 230 | CORRECTED (partly wrong) |

### Floodwall

| Claim | Earlier value | My value | Source and page | Verdict |
|---|---|---|---|---|
| Authorization | WRDA 1986 sec. 401(a): $91.8M total, $68.9M federal, $22.9M non-federal; includes the wastewater plant; Chief's report Nov. 16, 1981; District report Sept. 1980 | same | 100 Stat. 4126 (raw/wrda1986.txt) | CONFIRMED |
| Cost ceiling raised | $134M, $100.5M federal, $33.5M non-federal, Nov. 8, 1993 | same | PL 103-135, 107 Stat. 1375 | CONFIRMED |
| Dedication | Oct. 21, 1994 | same | hmdb 23953; DPU thread | CONFIRMED |
| Construction start | Nov. 5, 1988 | not re-read (Virginia HD 64, 1989) | none | UNCONFIRMED (not rechecked) |
| Final cost | $143M | $143M at dedication (DPU thread); the marker gives no cost | DPU thread | CONFIRMED (one source) |
| $153M | "the city now values it at about $153 million" | DPU thread calls it the current value. FloodKit (PDF p. 4) says the system protects about 750 acres valued at about $153 million, i.e. the value of the protected land | FloodKit 2026; DPU thread | UNCONFIRMED (meaning conflicts) |
| Acres | 750 = 150 + 600 | same | marker | CONFIRMED |
| North wall | 4,277 ft total; 3,947 concrete; 140 sandbag; closures 2 railroad, 5 road, 1 railroad/road, 4 pedestrian; 1 pump at 75,000 gpm | same | hmdb 23953 | CONFIRMED |
| South wall | 3,566 concrete; 1,887 bin wall/levee; 7,170 earthen levee; 175 sandbag; closures 4 railroad, 1 road, 1 railroad/road; pumps 4,400 and 28,000 gpm; walk 5,655 ft | same. FloodKit gives rounder and different numbers: earthen levee about 9,000 ft, bin wall about 2,000 ft, concrete about 2,000 ft | hmdb 23953; FloodKit PDF p. 5 | CONFIRMED (marker); FloodKit difference added |
| Closures | 19 = 6 road, 6 railway, 2 both, 1 canal, 4 pedestrian | same | DPU thread | CONFIRMED |
| Design | 32 ft / 280-year / "century" | "32 feet" in RVANews 2011, no gauge named. 280 years applies to the **northern** concrete wall in FloodKit (PDF p. 5). The 1998 FIS says the system met 3 ft freeboard over the 100-year but not the 500-year | RVANews; FloodKit; FIS 1998 PDF p. 9 | CONFIRMED as quoted; 32 ft UNCONFIRMED |
| Overtopping | 41 ft at the City Locks | 41 ft ("Flood wall is overtopped"). The same table lists 35 ft as the river-stage sensor's operating limit | raw/nwps_ricv2.json | CONFIRMED (sensor limit added) |
| Top-of-wall elevation | none found | none in either FIS | FIS 1998, 2025 | UNCONFIRMED |
| Closures in floods | Jan. 1996 and Sept. 1996 (some gates, Dock St); 1999 (Dock and Brander); Nov. 12, 2020 (Dock at noon, Brander in the evening, Low Line doors); Feb. 17, 2025 (Dock St, 17th to 21st) | 1996: two floods, gates including Dock St, months not stated. 1999: DPU thread and WTVR. 2020: WTVR (forecast 18.5). 2025: Richmonder, Feb. 17 | RVANews 2011; WTVR Nov. 12, 2020; Richmonder Feb. 17, 2025; DPU thread | CONFIRMED (1996 months UNCONFIRMED; Low Line doors not rechecked) |
| FEMA recertified 2010 | yes | the 2011 article says "last year" | RVANews | CONFIRMED (inferred year) |
| Accreditation now | none | three systems accredited (North, South, Filtration Plant) | FIS 2025 Table 8, PDF p. 29 | added |

## Disagreements, and what I believe is right

1. **City Locks datum, 2007 to 2010.**
   - The earlier research left the January 2010 crest's datum open, and said the 1.01 ft NOAA-NWS gap "runs the wrong way" for an NGVD29 reading. That reasoning is backward.
   - For a fixed water surface, the NGVD29 number is about 1.03 ft *larger* than the NAVD88 number. NOAA's 16.93 is 1.01 ft larger than USGS's 15.92.
   - USGS's approved series at 02037705 is explicitly "water surface elevation above NAVD 1988" (parameter 62620). It gives 15.92 for that flood, and it runs continuously from October 1, 2007.
   - So the NWS 2010 value is NAVD88. The NOAA station value is either NGVD29-referenced or on a station datum about 1 ft below NAVD88.
   - Use 15.92 NAVD88. The FIS does not help here: it never mentions the City Locks gauge.
2. **1969 at the Boulevard Bridge.** 83.8 ±0.7 ft NGVD29, not 84.9. The 84.9 is the mark at mile 107.59, not the line at the bridge.
3. **1% flood at Westham.** The FIS gives 124.0 NAVD88 at the gauge station (1998 FIS: 126.4 NGVD29 = 125.4 NAVD88). The earlier 125.4 estimate matches the 1998 value by coincidence, and it is 1.4 ft above the current one.
4. **$153 million.** The FloodKit attaches the figure to the 750 protected acres, while the DPU thread reads as the wall's value. Do not print "the wall is worth $153 million" without a clearer source.
5. **Canal flow.** WDR 1986 says daily Westham discharges exclude the Kanawha Canal, but the 313,000 cfs record peak includes it. The earlier sentence was too broad.
6. **The Agnes sign at Tredegar reads 40 ft NAVD88, below the 1969 profile there.** The FIS largely explains this.
   - The nearest channel point to the sign is station 169,640. That is above a 3 to 5 ft step in the FIS profiles across the Potterfield bridge and Brown's Island dam line (1% of 41.1 just below versus 44.0 at the sign's station).
   - The sign stands about 270 m off the channel, behind Brown's Island, in ground that drains to the river below that step.
   - The 1969 HA-410 profile at the sign's equivalent mile (about 105.33) is about 42.8 NGVD29 (41.8 NAVD88), in the channel above the step.
   - The 2025 FIS runs about 1.4 ft high at the Locks against Agnes. Shifted down by that much, the FIS 1% below the step is about 39.3 to 39.7. That agrees with the sign's 40.
   - So the sign is credible for the backwater pocket. It is not a channel point.
   - PARTLY RESOLVED; the drainage path is UNCONFIRMED in the field.
7. **The 0.25 ft Westham gauge-zero disagreement.**
   - The FIS shows that FEMA converts the old zero: Table 6 gives Agnes as 126.4, which is 28.62 + 98.82 - 1.03. FIS Table 19 puts the Westham conversion at about -0.98, so the converted zero is 97.84 and the gap to USGS's 98.04 is 0.20 ft.
   - The FIS does not settle which is physically right.
   - I keep 98.04 (a direct GNSS tie of the present zero, ±0.08 ft) for drawing, with 0.25 ft uncertainty, and note FEMA's convention. UNCONFIRMED.
8. **Top of the wall.**
   - Neither FIS gives a top elevation. The 1998 FIS implies a top at least 3 ft above its 1% (at least about 36.8 NAVD88 at the Locks).
   - The NWS 41 ft overtopping stage sits at about a 0.4% (240-year) flood on the 2025 profiles. That fits the City's 280-year design statement for the northern wall.
   - "32 feet" remains UNCONFIRMED and fits no stated gauge.
9. **The 1% flood beside real floods.**

   | Place | 2025 FIS 1% | Agnes | 1985 | Camille |
   |---|---|---|---|---|
   | City Locks | 36.9 | 35.5 (1.4 ft below) | 29.7 (7.2 ft below) | 27.6 (9.3 ft below) |
   | Mayo Bridge, downstream face | 38.0 | about 36.8, estimated (UNCONFIRMED) | about 31.0, estimated (UNCONFIRMED) | 28.9 |

   - On the tidal reach the FIS profiles stand 2 to 5 ft above what floods of the same flow actually did.
   - At Westham, by contrast, Agnes falls between the 1% and 0.2%, as its flow does.
   - The FIS 1% is not a stand-in for Agnes, even though Agnes's flow exceeds it.
10. **Fran 1996 and February 2003 datum era.**
    - Both are assumed NGVD29 because the USGS NAVD88 series starts in 2007.
    - One piece of evidence cuts the other way. February 2003 (113,000 cfs) at 17.76 as NAVD88 would fit the 2010 to 2020 crests (104,000 cfs → 15.92; 108,000 → 16.96) better than 16.73 does.
    - UNCONFIRMED. Fran's level carries a one-sided +1.0 ft uncertainty.
11. **Mileage.** OFR 70-51 puts the old gauge 0.9 mi above the Locks. WDR 1986 puts them 0.8 mi apart on its newer mileage (109.5 and 108.7). This is minor and does not change any level.
12. **The DPU thread puts Juan "in 1986."** The flood was November 1985. Theirs is the error.

## Not rechecked

- Virginia House Document 64 (construction start, the 1989 cost).
- The Low Line Green doors.
- The VCU slide collection.
- The water filtration plant levee's design flow (467,000 cfs, city grant application). The FIS confirms only that this levee exists and is accredited.
- Richmond Family Magazine street details. They remain secondary and UNCONFIRMED.
