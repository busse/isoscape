# What the two Flood Insurance Studies say about the James at Richmond

Read November 23, 2026. Sources:

- **2025 FIS:** FEMA Flood Insurance Study 510129V000C, City of Richmond, effective July 8, 2025, 134 pages. It has a text layer. The profile panels are vector drawings with outlined text.
- **1998 FIS:** FEMA 510129V000, revised July 20, 1998, 48 pages. It is a scan. I read it with tesseract OCR and by rasterizing pages.

Page numbers are PDF pages, with the printed page in brackets where they differ. In the 2025 report the PDF page is the printed page plus 5. Machine-readable values are in `fis.json`, built by `scripts/build_fis_json.py`.

## Vertical datums

- **2025: NAVD88.** Section 6.1 says the flood elevations in the report and on the FIRMs are referenced to NAVD88 (PDF p. 49 [44]). The profiles are labeled "ELEVATION IN FEET (NAVD)".
  - Table 19 (same page) gives the NGVD29-to-NAVD88 conversion at nine quadrangle corners: Richmond NE -1.042, Drewrys Bluff NE -1.059, Chesterfield NE -1.025, Bon Air NE -0.980, Midlothian NE -0.969, Hallsboro NE -0.933, Beach NE -1.045, Chester NE -1.083 and Winterpock NE -0.981. The county average is -1.013 ft.
  - Interpolated by this check: -1.04 at the City Locks and -0.98 at the Westham gauge. NGS NCAT gives -1.03 at both.
- **1998: NGVD29.** Section 3.2 states that all elevations are referenced to NGVD (PDF p. 13 [9]). Profiles and Table 2 are labeled "FEET NGVD". The report gives no conversion factor.

## a. James River flood profiles

### 2025 profiles: how I read them

- **Panels:** 17P to 23P (PDF pp. 106 to 112).
- **Stationing:** feet above a point about 20,500 ft upstream of Roxbury Road.
- **Profiles shown:** 10, 4, 2, 1, "1%+" and 0.2 percent annual chance.
- **Method:** Because the panels are vector art, I took line positions from the PDF geometry (via pdftocairo SVG) and scaled them from the major grid, which is 20 ft and 1,000 ft per 72 pt. Lines were assigned by vertical order, top to bottom: 0.2%, 1%+, 1%, 2%, 4%, 10%, bed.
- **Precision:** about 0.05 ft on flat reaches and about 0.3 ft on the steepest ramps. Check: the 1% reading matches the 2025 Floodway Data at A through H and L through O within 0.05 ft. It matches at I within 0.3 ft and at J within 0.15 ft. At K, the reading was taken 140 ft upstream of the section to avoid the bridge step.
- **Stations of labels:** taken from the label leader lines in the geometry.
- **Gauges:** neither gauge is labeled on the profiles. I placed both on the stationing from OSM centerline chainage. Ten labeled bridges give a constant offset of 137,100 ft, within ±300 ft. That puts the City Locks at about 161,530 and Westham at about 203,720 (just above Huguenot, as USGS describes).
- **Not labeled anywhere:** the Great Shiplock, the city limits, the Hollywood/Belle Isle dam and Bosher's Dam. Three structures are labeled only "WEIR".
- **Evidence:** `evidence/fis2025_p108_panel19P_downtown-108.png`.

### 2025 water-surface elevations at landmarks

Feet NAVD88. "dn" and "up" are readings just downstream and just upstream of a bridge step.

| Landmark (station, panel) | 10% | 4% | 2% | 1% | 1%+ | 0.2% |
|---|---|---|---|---|---|---|
| Downstream end of profile (132,400; 17P) | 19.5 | 23.4 | 26.2 | 29.1 | 34.8 | 35.7 |
| Confluence of Broad Rock Creek (about 151,250; 18P) | 23.5 | 28.1 | 31.4 | 34.7 | 41.3 | 42.3 |
| Confluence of Gillies Creek (160,195; 19P) | 25.2 | 29.8 | 33.1 | 36.4 | 43.0 | 44.1 |
| **City Locks gauge** (about 161,530, derived) | 25.8 | 30.3 | 33.6 | **36.9** | 43.5 | 44.5 |
| I-95 bridge (164,010), dn / up | 26.2 / 26.2 | 30.7 / 30.8 | 34.0 / 34.1 | 37.3 / 37.3 | 43.8 / 43.9 | 45.0 / 45.0 |
| Railroad (CSX Bellwood Sub per OSM; 164,725), dn / up | 26.3 / 26.6 | 30.9 / 31.3 | 34.2 / 34.7 | 37.5 / 38.0 | 44.1 / 44.5 | 45.1 / 45.6 |
| **Mayo Bridge** (US 360 / S. 14th St; 165,592), dn / up | 26.6 / 27.2 | 31.4 / 32.5 | 34.8 / 35.9 | **38.0 / 39.0** | 44.6 / 45.2 | 45.7 / 46.3 |
| Railroad (CSX Richmond District per OSM; 166,551), dn / up | 27.3 / 27.5 | 32.6 / 33.3 | 36.1 / 36.8 | 39.1 / 39.7 | 45.3 / 45.8 | 46.4 / 46.9 |
| 9th St / Manchester Bridge (US 60; 168,431), dn / up | 28.4 / 32.4 | 33.4 / 35.1 | 36.8 / 38.0 | 39.8 / 40.7 | 45.9 / 46.5 | 47.0 / 47.6 |
| T. Tyler Potterfield Bridge (169,153), dn / up | 33.5 / 35.2 | 36.0 / 37.2 | 38.6 / 39.4 | 41.1 / 41.8 | 46.8 / 47.4 | 47.8 / 48.4 |
| Channel opposite the Tredegar/Brown's Island Way sign (169,640) | 38.4 | 40.4 | 42.0 | 44.0 | 49.2 | 50.1 |
| Lee Bridge (US 1/301; 170,522), dn / up | 39.6 / 39.9 | 41.7 / 41.9 | 43.3 / 43.4 | 45.1 / 45.3 | 50.0 / 50.1 | 50.9 / 50.9 |
| Hollywood dam reach (about 173,450; not labeled) | 49.5 | 51.4 | 52.8 | 54.0 | 56.8 | 57.3 |
| Confluence of Reedy Creek (176,113) | 63.9 | 65.6 | 67.0 | 68.2 | 70.6 | 71.0 |
| Boulevard Bridge (SR 161; 181,453), dn / up | 77.8 / 80.7 | 79.8 / 82.9 | 81.4 / 84.7 | 82.9 / 86.4 | 86.1 / 89.9 | 86.6 / 90.5 |
| Railroad (CSX North End Sub per OSM; 184,816), dn / up | 86.3 / 89.2 | 88.6 / 91.7 | 90.4 / 93.6 | 92.2 / 95.6 | 96.0 / 99.8 | 96.7 / 100.4 |
| Powhite Parkway (SR 76; 186,073), dn / up | 90.8 / 91.4 | 93.3 / 93.8 | 95.2 / 95.7 | 97.1 / 97.6 | 101.3 / 101.7 | 102.0 / 102.4 |
| Lower WEIR (196,110), dn / up | 107.2 / 107.3 | 109.2 / 109.3 | 110.9 / 110.9 | 112.6 / 112.7 | 116.6 / 116.7 | 117.3 / 117.4 |
| Upper WEIR (197,855), dn / up | 113.2 / 113.4 | 115.1 / 115.3 | 116.5 / 116.8 | 118.0 / 118.2 | 121.1 / 121.3 | 121.6 / 121.8 |
| Huguenot Bridge (SR 147; 203,291), dn / up | 117.5 / 117.8 | 119.9 / 120.2 | 121.6 / 121.9 | 123.4 / 123.7 | 127.2 / 127.4 | 127.8 / 128.0 |
| **Westham gauge** (about 203,720, derived) | 118.0 | 120.4 | 122.2 | **124.0** | 127.7 | 128.3 |
| Chippenham (US 150; 211,895), dn / up | 124.2 / 124.5 | 126.7 / 127.0 | 128.6 / 128.9 | 130.5 / 130.8 | 134.3 / 134.6 | 134.9 / 135.2 |
| WEIR at 213,211 (no step) | 124.6 | 127.1 | 129.0 | 130.9 | 134.8 | 135.4 |
| Upstream end of profile (219,150) | 128.9 | 131.6 | 133.5 | 135.5 | 139.4 | 140.1 |

The full set of readings, including Stony Point, Rattlesnake, Powhite, Cherokee and Pittaway creek confluences and the stream bed, is in `fis.json`.

How to read the table:

- **The two lower weirs** (196,110 and 197,855) are probably the Williams Island dams. WDR 1986 names those dams as the Westham gauge's control, and the 1998 profile puts the Williams Island Dam about 1.1 mi below Huguenot.
- **The weir at 213,211** is probably Bosher's Dam. It sits about 1.8 mi above the gauge, and OFR 70-51 gives 1.7 mi. The 1998 profile labels Boshers Dam at its section W.
- **None of these name matches is printed in the 2025 report.** They are UNCONFIRMED.
- **Below the Mayo Bridge the surface is nearly flat.** The 1% rises only 1.1 ft from the Locks (36.9) to the Mayo Bridge's downstream face (38.0).
- **Most of the 1% climb through the falls happens at steps:**
  - Mayo Bridge: +1.0 ft.
  - The 9th Street rapids and the Potterfield/Brown's Island dam line: 39.8 to 44.0 between 168,150 and 169,640.
  - The long ramp from Lee to Boulevard: 45 to 83 ft.

### 2025 Floodway Data, James River

Table 23, PDF p. 62 [57]. Distances in feet; elevations in feet NAVD88. The "without" and "with" columns are the 1% elevation without and with the floodway.

| XS | Distance | Width (total/in city) | Velocity (ft/s) | Regulatory | Without | With | Increase |
|---|---|---|---|---|---|---|---|
| A | 135,943 | 1,012/549 | 6.9 | 30.6 | 30.6 | 31.1 | 0.5 |
| B | 140,508 | 1,055/418 | 7.2 | 32.2 | 32.2 | 32.4 | 0.2 |
| C | 145,016 | 1,481/1,291 | 5.8 | 33.2 | 33.2 | 33.8 | 0.6 |
| D | 152,727 | 2,195/1,707 | 4.4 | 34.9 | 34.9 | 35.5 | 0.6 |
| E | 158,169 | 2,624/2,478 | 3.9 | 36.0 | 36.0 | 36.8 | 0.8 |
| F | 161,592 | 2,620 | 4.1 | 36.9 | 36.9 | 37.6 | 0.7 |
| G | 168,223 | 1,592 | 10.0 | 39.8 | 39.8 | 40.3 | 0.5 |
| H | 170,220 | 2,662 | 7.6 | 44.8 | 44.8 | 45.4 | 0.6 |
| I | 175,499 | 2,003 | 11.6 | 66.0 | 66.0 | 66.2 | 0.2 |
| J | 181,150 | 1,414 | 13.1 | 82.0 | 82.0 | 82.5 | 0.5 |
| K | 181,608 | 1,448 | 11.7 | 85.9 | 85.9 | 86.2 | 0.3 |
| L | 198,423 | 2,088 | 9.2 | 118.2 | 118.2 | 118.2 | 0.0 |
| M | 205,600 | 2,157/15 | 7.1 | 125.5 | 125.5 | 125.9 | 0.4 |
| N | 209,736 | 2,265/247 | 6.9 | 128.8 | 128.8 | 129.4 | 0.6 |
| O | 216,099 | 2,110/32 | 6.6 | 132.9 | 132.9 | 133.8 | 0.9 |

Section areas are in `fis.json`. Section F, at 161,592, is about 60 ft from my derived City Locks station.

### 2025 discharges and gauge use

Table 9 (PDF p. 32 [27]), in cfs:

| Location | 10% | 4% | 2% | 1% | 0.2% |
|---|---|---|---|---|---|
| USGS gage 02037500 | 147,500 | 195,900 | 236,600 | 281,400 | 404,400 |
| Upstream of Gillies Creek | 148,511 | 197,243 | 238,222 | 283,329 | 407,172 |
| About 2,000 ft upstream of Chippenham Parkway (downstream end) | 149,248 | 198,222 | 239,404 | 284,735 | 409,193 |

Gauge record and method:

- Table 11 (PDF p. 35 [30]) uses the Westham record from 09/07/1935 to 02/25/2016.
- Table 12 (PDF p. 39 [34]) lists gage analysis plus regression equations, HEC-RAS 5.0.5, a model calibrated to the gage rating curve, and "natural valley analyses" for the City's levee systems. The analysis date is March 25, 2020.
- The City Locks gauge is not used or mentioned anywhere in the report.

Stillwater and tidal elevations:

- 2025: Table 10 (non-coastal stillwater) and every coastal section are marked not applicable (PDF pp. 35, 47 to 48).
- 1998: none given.

### 1998 profiles and Floodway Data (NGVD29)

The 1998 report shows 10, 50, 100 and 500-year profiles; there is no 4% profile. The James panels are 01P, 02P, 03P, 03P(a), 03P(b) and 03P(c) (PDF pp. 27 to 32). It uses two stationing systems:

- feet above the mouth, from 519,700 to 559,000 ft;
- historical miles above the mouth, from 105.5 to 114.5 mi.

**1998 Floodway Data** (Table 2, PDF p. 16 [12]; evidence `evidence/fis1998_p16_floodway_james.png`). Regulatory 1% values in feet NGVD29:

| Section | Location | 1% (ft NGVD29) |
|---|---|---|
| A to M3 | 519,700 to 544,710 ft | 26.8, 27.6, 27.7, 27.7, 27.9, 29.0, 30.0, 31.0, 31.1, 31.6, 31.8, 32.0, 32.0, 32.6, 32.8, 33.3 |
| M4 | 546,355 ft | 33.5 |
| M5 | 548,155 ft | 34.7 |
| M6 | 549,135 ft (the City Locks) | 34.8 |
| M7 | 553,920 ft | 38.1 |
| M8 | 554,480 ft | 38.5 |
| M9 | 554,610 ft | 38.5 |
| M10 | 556,105 ft | 46.6 |
| M11 | 558,930 ft | 57.6 |
| N, O | 106.39, 106.83 mi | 66.9, 79.8 |
| P, Q, R | 108.58, 108.76, 109.40 mi | 102.8, 105.9, 109.5 |
| S, T, U | 110.33, 110.59, 110.99 mi | 114.7, 119.6, 121.4 |
| V | 111.73 mi (the Westham gauge, mile 111.7) | 126.4 |
| W | 113.35 mi (Bosher's Dam) | 135.0 |

Floodway widths at M3 to M9 run to the landside toe of the levee/floodwall (footnote 4).

**1998 labels on panel 03P** (feet above mouth, read from the leader lines; the 1998 stationing equals the 2025 stationing plus about 387,700 ft):

| Label | Station (ft above mouth) |
|---|---|
| Confluence of Gillies Creek | 547,889 |
| I-95 | 551,723 |
| Seaboard Coastline Railroad | 552,444 |
| Mayo's Bridge | 553,247 |
| Southern Railway | 553,953 |
| 9th Street / Manchester Street | 555,945 |
| Brown's Island Dam | 556,667 |

**1998 profile readings** (panel 03P, read from the 200 dpi scan, about ±0.3 ft, feet NGVD29; evidence `evidence/fis1998_p29_panel03P-29.png`):

| Place | 10-yr | 50-yr | 100-yr | 500-yr |
|---|---|---|---|---|
| City Locks | 21.8 | 30.1 | 34.2 | 46.6 |
| I-95 | 22.0 | 30.6 to 30.7 | 35.0 to 35.2 | 46.8 to 47.0 |
| Mayo's Bridge, downstream / upstream | 22.6 / 22.7 | 31.3 / 32.1 | 36.0 / 37.0 | 47.8 / 48.3 |

**The 1998 report disagrees with itself.** Its plotted 100-year line sits 0.6 to 0.9 ft below its own Floodway Data at M5 to M8. For example, M5 is plotted at 33.8 against 34.7 in the table, and M7 at 37.2 against 38.1. The two agree at M4 (33.5). The table is the regulatory value.

**1998 upper-reach labels** (panels 03P(b) and 03P(c), historical miles, ±0.05 mi):

| Label | Mile |
|---|---|
| Hollywood Dam | 106.0 |
| Reedy Creek | 106.7 |
| Boulevard Bridge | 107.5 |
| Seaboard Coastline RR | 108.2 |
| Powhite Freeway | 108.35 |
| Williams Island Dam | 110.6 |
| Corporate limits | 110.8 |
| Huguenot Bridge | 111.65 |
| Bosher's Dam (section W) | 113.35 |
| Upper corporate limits | 114.5 |

At the Boulevard Bridge, read by eye to ±1 ft (feet NGVD29): 10-yr 81.8, 50-yr 86.1, 100-yr 88.0, 500-yr 93.7.

**1998 discharges** (Table 1, PDF p. 11 [7]), James at the downstream corporate limits: 10-yr 131,000 cfs; 50-yr 232,000; 100-yr 290,000; 500-yr 475,000. These come from a log-Pearson Type III fit of the Westham peaks, supplied by the Virginia State Water Control Board (PDF p. 10 [6]).

## b. The floodwall (Richmond Local Flood Protection Project) and the tributaries

### 2025 levee treatment

- **Table 8, Levee Systems** (PDF p. 29 [24]): three systems, all **Accredited** and all owned by the City of Richmond.
  - NLD 4605000002, Richmond, Virginia (North): FIRM panels 5101290041F and 0043F.
  - NLD 4605000007, Richmond, Virginia (South): panels 0039F and 0043F.
  - NLD 4605000003, Richmond Filtration Plant: panels 0017E and 0036E.
- **Section 4.4** (PDF p. 28 [23]) explains accreditation under 44 CFR 65.10 and provisional accreditation.
- **Notes to Users:**
  - PDF p. 8 says FEMA has identified levee systems and that accreditation needs 44 CFR 65.10.
  - PDF p. 13 has the special notes for accredited and provisionally accredited levee systems. It says owner data for continued accreditation was due by September 28, 2022.
- **Map legend** (PDF p. 15): the protected areas are shown as having reduced flood hazard from the 1% or greater flood by an accredited or provisionally accredited levee, and overtopping or failure is possible. That is the shaded Zone X "area with reduced flood risk due to levee."
- **Table 12** (PDF p. 39 [34]) says natural valley analyses were done for the levee systems. No natural-valley or without-levee profile is printed.
- **What the 2025 report does not give:**
  - a design flood;
  - top-of-wall elevations;
  - the positions, sills or tops of the closures and gates;
  - pump-station data for the river wall;
  - ponding-area elevations.

  The word "closure" does not appear in either report.

### 1998 levee treatment

From PDF p. 9 [5]:

- The USACE built a levee/floodwall to protect the Shockoe Creek area on the north side and low southside Richmond from the James.
- FEMA required 3 ft of freeboard over the 100-year flood.
- The Richmond system met that test for the 100-year flood but does not protect against the 500-year flood.

The same page carries the older history, repeated in the 2025 Table 5 (PDF p. 27 [22]): the earlier Shockoe Creek levee at the creek mouth gave only limited protection. It was overtopped in 1972, and its pumping had to stop for structural reasons during Camille in 1969.

### What the FIS implies for the top of the wall

This is inference, not a printed value:

- **The 1998 freeboard test** puts the wall top at no less than the 1998 1% plus 3 ft. That is about 37.8 ft NGVD29 (36.8 NAVD88) at the Locks and about 41 ft NGVD29 (40 NAVD88) at the Mayo Bridge.
- **The NWS overtopping stage** at the City Locks is 41 ft NAVD88. On the 2025 profiles, 41 ft falls between the 1% (36.9) and the 0.2% (44.5). Interpolating log-linearly in annual chance gives about a 0.4% flood, a 240-year return period. That is close to the City's 280-year design statement for the northern wall (FloodKit, PDF p. 5).

### Interior drainage and Shockoe Bottom ponding

- **Model:** the 2025 Shockoe Creek study is a SWMM 5.1.012 model of storm drains, combined sewers, underground storage, pumping stations and overland flow (Table 12, PDF p. 43 [38]). It starts at the confluence with the Kanawha Canal, inside the wall.
- **Floodway Data** (PDF p. 70 [65]), 1% in feet NAVD88:

  | Section | Distance above the Kanawha Canal | 1% |
  |---|---|---|
  | A | 262 ft | 19.4 |
  | B | 394 ft | 20.5 |
  | C | 619 ft | 21.2 |
  | D, E | 924 ft, 1,354 ft | 25.3 |
  | F | 1,936 ft | 32.2 |
  | H | 2,665 ft | 35.2 |
  | J | 3,225 ft | 39.3 |
  | L | 4,232 ft | 46.1 |

- **At the downstream end of panel 37P** (PDF p. 126; Dock Street at about 60 ft, the I-95 overhead at about 200 ft), the vector reading gives 10% about 17.7, 2% about 18.7, 1% 19.4 and 0.2% about 21.2 ft NAVD88. This is ±0.2 ft, and line identity is less certain here.
- **These are interior rain-flood levels.** They are about 17 ft below the James 1% at the Locks (36.9), so the model assumes the wall holds the river out.
- **No ponding-area outline or elevation is given.**

### Tributaries

| Stream | 2025 FIS | 1998 FIS |
|---|---|---|
| Gillies Creek | Detailed (Table 2: from the James to 580 ft above East Richmond Road). Floodway Data PDF p. 59: sections A to D (1,337 to 5,558 ft above the James) regulatory 1% = 36.3 NAVD88, which is James backwater. Without backwater: 23.5, 28.0, 29.2, 33.9. E 37.6, F 42.6, G 44.7, H 54.8. The James 1% at the Gillies confluence reads 36.4. Profile 13P. Mouth discharges 3,366 / 4,876 / 6,045 / 7,813 / 18,619 cfs (Table 9). | Profile 19P; partly approximate (PDF p. 6). 100-yr 7,100 cfs at Jennie Scher Road (PDF p. 12). No floodway table. |
| Shockoe Creek | SWMM, interior (above). Profiles 37P to 39P, split flow 40P. | Not studied in detail. |
| Reedy Creek | Floodway PDF p. 65: A (1,871 ft above the James) 71.4 regulatory (James backwater), 66.3 without. Profiles 33P to 36P. | Approximate only. |
| Goodes Creek | Joins Broad Rock Creek, not the James. A 45.2 (Broad Rock backwater), PDF p. 60. | A 42.2 NGVD29 (PDF p. 20). |
| Cannon Creek Branch | Part of the Shockoe system (Bacons Quarter), SWMM, A 75.5 (PDF p. 56). | Not studied. |
| Almond Creek | Not named in either report. UNCONFIRMED how it is mapped. | Not named. |

## c. Historical floods and principal flood problems

**2025 Table 6** (PDF p. 27 [22]) lists one event: James River near Richmond (USGS 02037500), June 23, 1972, 126.4 ft NAVD88, a 100 to 200-year recurrence.

126.4 equals the 28.62 ft stage plus the old 98.82 NGVD29 zero, converted (126.41). It does not use the current USGS NAVD88 zero, which would give 126.66.

**2025 Table 5** (PDF p. 27 [22]) says:

- Floods of 20-year size or larger reach much of the industrial and commercial district.
- Agnes was among the largest floods, and tropical storms from May to November cause the biggest ones.
- Navigation to the City Locks stops at a 14 ft flood stage.
- The Shockoe levee history (above).
- Gaston, August 30, 2004, dropped up to 14 in of rain on the Shockoe basin.
- The text is cited to the 2009 FIS.

**1998 Section 2.3** (PDF p. 8 [4]) lists these large floods. 1936 and 1985 are absent.

| Flood | Peak flow (cfs) | Recurrence interval |
|---|---|---|
| May 1771 | none given | 50 to 100 years |
| October 1870 | none given | 20 to 50 years |
| November 1877 | none given | 20 to 50 years |
| April 1937 | 148,000 | 10 to 20 years |
| August 1940 | 151,000 | 10 to 20 years |
| September 1944 | 150,000 | 10 to 20 years |
| December 1948 | 136,000 | 10 to 20 years |
| August 1969 | 222,000 | 20 to 50 years |
| June 1972 | 313,000 | 100 to 200 years |

The 1998 report also says (PDF p. 9 [5]):

- Gathright Dam cuts peak discharges at Richmond by about 1.5 percent.
- A channel improvement downstream lowers major-flood elevations in Richmond. The scan literally says it "shortened the channel by approximately 2 feet in the city," which probably means flood levels.

## d. Floodway Data

Given in full above for the 2025 James (Table 23) and the 1998 James (Table 2). The 2025 table holds every lettered section A to O in `fis.json`, with section areas and velocities. The 1998 table holds A to M11 and N to W.

## e. Differences between 1998 and 2025 that matter

1. **Datum.** NGVD29 in 1998, NAVD88 in 2025. The shift at Richmond is -1.03 to -1.04 ft.
2. **Discharges.**
   - The 1% fell from 290,000 to 284,735 cfs.
   - The 0.2% fell from 475,000 to 409,193 cfs.
   - The 10% rose from 131,000 to 149,248 cfs.
   - A 4% flood was added.
3. **The tidal reach is higher in 2025 by about 3 ft, from the downstream boundary up to the Mayo Bridge.** Everything below is in NAVD88, with the 1998 values converted.

   | Place | 1998 1% | 2025 1% |
   |---|---|---|
   | Downstream limit | 25.8 | 29.1 |
   | City Locks | 33.8 (table M6) | 36.9 |
   | Mayo Bridge, upstream face | about 37.1 (M7) | 39.0 |

   The 10% at the Locks rose from about 20.8 to 25.8. The 0.2% at the Locks barely moved (45.4 to 44.5).
4. **The falls and above are lower in 2025.**

   | Place | 1998 1% (NAVD88) | 2025 1% (NAVD88) |
   |---|---|---|
   | Boulevard Bridge | about 87 (±1) | 82.9 to 86.4 |
   | Westham, section V | 125.4 | 124.0 |
   | Bosher's Dam, section W | 134.0 | 130.9 |

5. **Model and stationing.** The 1998 analysis used HEC-2 (USACE Norfolk, James restudied only below Hollywood Dam). The 2025 analysis used HEC-RAS 5.0.5 calibrated to the gauge rating. The stationing changed too; in the downtown reach, 1998 = 2025 + 387,700 ft.
6. **Levees.**
   - **1998:** the wall passes the 3 ft freeboard test, and the floodway stops at the levee toe.
   - **2025:** three accredited systems under 44 CFR 65.10, shown as reduced-hazard Zone X, with natural-valley analyses mentioned but not printed. The water filtration plant levee appears for the first time.
7. **Tributaries.** Shockoe Creek and the Bacons Quarter and Cannon Creek branches are new in 2025 (SWMM, 2021). Gillies and Reedy creeks are now detailed, with James backwater set as the regulatory level near their mouths.

## The FIS beside the real floods

At the City Locks (NAVD88), compared with the 2025 FIS:

| Flood | Level | Where it falls on the 2025 profiles |
|---|---|---|
| Agnes, 313,000 cfs | 35.5 | 1.4 ft below the 1% (36.9), though its flow is about 10% larger than the FIS 1% |
| 1985, 218,000 cfs | 29.7 | between the 10% and 4% |
| Camille, 222,000 cfs | 27.6 | between the 10% and 4%, though its flow lies between the 4% and 2% |
| March 1936 | 26.5 | just above the 10% |
| Fran | 22.7 | below the 10% |
| November 2020 | 17.0 | below the 10% |

At the downstream face of the Mayo Bridge, the 1% is 38.0. Camille reached 28.9 there (HA-410 Table 1). Agnes is estimated at about 36.8.

For a given flow, the 2025 profiles at the Locks run 2 to 5 ft above the measured historic crests. At Westham they agree with the gauge record within about 1 ft: Agnes 126.7 falls between the 1% (124.0) and 0.2% (128.3), as its flow does.

Possible causes, all UNCONFIRMED:

- the floodwall now confines the floodplain;
- the model's downstream starting water surface;
- a conservative regulatory model.

**Do not use FIS profiles as stand-ins for historic floods on the tidal reach.**
