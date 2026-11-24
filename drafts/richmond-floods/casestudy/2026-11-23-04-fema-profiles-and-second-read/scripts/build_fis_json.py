# Builds check/fis.json from the vector profile readings (2025), the scanned readings (1998)
# and values typed from the two FIS reports. Page numbers are PDF pages (printed page in brackets).
import sys, json, math
sys.path.insert(0, '/home/claude/floods-research/check/scripts')
import profiles as pr
from read_james import page_for
F25 = 'FEMA FIS 510129V000C, City of Richmond, effective July 8, 2025'
F98 = 'FEMA FIS 510129V000, City of Richmond, revised July 20, 1998'
NAMES = ['p0_2', 'p1plus', 'p1', 'p2', 'p4', 'p10', 'bed']
def at(x0):
    for dx in (0, 25, -25, 50, -50, 75, -75, 100, -100):
        x = x0 + dx; pg = page_for(x); v = pr.sample2(pg, x)
        while len(v) > 1 and v[0] - v[1] > 20: v = v[1:]   # bridge-symbol caps far above the water
        if len(v) >= 7 and all(v[i] >= v[i+1] for i in range(6)) and v[5] - v[6] >= 3.0 and all(v[i] - v[i+1] < 12 for i in range(5)):
            if dx: print('  note: read', x0, 'at', x)
            return dict(zip(NAMES, v[:7]), used_station_ft=x), pg
    raise SystemExit(f'no clean reading near {x0}')
def _old(x):
    pg = page_for(x); v = pr.sample2(pg, x)
    # first six clusters are the profiles; anything 3 ft or more below the sixth is bed or bed hatching
    assert len(v) >= 7 and all(v[i] >= v[i+1] for i in range(6)) and v[5] - v[6] >= 3.0, (x, v)
    assert all(v[i] - v[i+1] < 12 for i in range(5)), (x, v)
    return dict(zip(NAMES, v[:7])), pg
# Landmarks: (name, label station on the profile, [(reading station, side)], note)
L = [
 ('Downstream end of James profile (FIS downstream limit, about 2,100 ft upstream of Chippenham Parkway per Table 2)', 132400, [(132400, 'at')], ''),
 ('Confluence of Broad Rock Creek', 151250, [(151250, 'at')], 'label station read by eye, +/-100 ft'),
 ('Confluence of Gillies Creek', 160195, [(160200, 'at')], ''),
 ('City Locks gauge USGS 02037705 (not labeled; station derived from OSM chainage)', 161530, [(161550, 'at')], 'station +/-300 ft; surface slope here about 0.0002, so +/-0.1 ft'),
 ('I-95 (Richmond-Petersburg Turnpike) bridge', 164010, [(163900, 'downstream'), (164150, 'upstream')], ''),
 ('Railroad bridge (OSM: CSX Bellwood Subdivision)', 164725, [(164600, 'downstream'), (165200, 'upstream')], ''),
 ('US 360 / South 14th Street (Mayo Bridge)', 165592, [(165500, 'downstream'), (165750, 'upstream')], ''),
 ('Railroad bridge (OSM: CSX Richmond District)', 166551, [(166450, 'downstream'), (166650, 'upstream')], ''),
 ('US 60 / South 9th Street (Manchester Bridge)', 168431, [(168150, 'downstream'), (168550, 'upstream')], 'profile ramps up through the 9th Street rapids between about 168,300 and 168,650'),
 ('T. Tyler Potterfield Memorial Bridge (spelled TAYLER on the profile)', 169153, [(169050, 'downstream'), (169250, 'upstream')], 'sits on the old Brown\'s Island dam line; OSM VEPCO Flash Board Dam projects to about 169,200'),
 ('Agnes sign at Tredegar St and Browns Island Way (station of the nearest channel point, derived)', 169640, [(169600, 'at')], 'sign is about 270 m north of the river centerline, behind Brown\'s Island'),
 ('US 1/301 Robert E. Lee Bridge', 170522, [(170400, 'downstream'), (170650, 'upstream')], ''),
 ('Hollywood Power Plant dam (not labeled; OSM weir projects to about 172,900-174,100)', 173500, [(173450, "at")], 'no step in the FIS profile here; the dam is drowned at these flows'),
 ('Confluence of Reedy Creek', 176113, [(176100, 'at')], ''),
 ('SR 161 Westover Hills Blvd (Boulevard Bridge)', 181453, [(181350, 'downstream'), (181750, "upstream")], ''),
 ('Railroad bridge (OSM: CSX North End Subdivision)', 184816, [(184700, 'downstream'), (184950, 'upstream')], ''),
 ('SR 76 Powhite Parkway', 186073, [(185950, 'downstream'), (186200, 'upstream')], ''),
 ('Confluence of Powhite Creek', 186397, [(186400, 'at')], ''),
 ('WEIR, lower (likely a Williams Island dam; WDR 1986 names the Williams Island dams as the Westham gauge control)', 196110, [(196000, 'downstream'), (196150, 'upstream')], ''),
 ('WEIR, upper (likely the other Williams Island dam)', 197855, [(197800, 'downstream'), (197900, 'upstream')], ''),
 ('Confluence of Rattlesnake Creek', 201604, [(201600, 'at')], ''),
 ('SR 147 Huguenot Road (Huguenot Bridge)', 203291, [(203150, 'downstream'), (203400, 'upstream')], ''),
 ('Westham gauge USGS 02037500 (not labeled; station derived from OSM chainage)', 203720, [(203700, 'at')], 'station +/-300 ft; slope about 0.0009, so +/-0.3 ft'),
 ('Confluence of Stony Point Creek', 208586, [(208300, 'downstream')], ''),
 ('US 150 Chippenham Highway', 211895, [(211800, 'downstream'), (212000, 'upstream')], ''),
 ('WEIR at 213,211 (likely Bosher\'s Dam: 1.7 mi above the Westham gauge per OFR 70-51 and WDR 1986; the 1998 profile labels Boshers Dam)', 213211, [(213150, 'downstream'), (213250, 'upstream')], 'no step at these flows'),
 ('Confluence of Cherokee Creek', 213710, [(213700, 'at')], ''),
 ('Confluence of Pittaway Creek', 218417, [(218650, 'upstream')], ''),
 ('Upstream end of James profile', 219150, [(219150, 'at')], ''),
]
rows = []
for name, st, reads, note in L:
    rr = []
    for x, side in reads:
        v, pg = at(x)
        rr.append({'side': side, 'read_at_station_ft': x, 'panel': pr.PANELS[pg][0], 'pdf_page': pg,
                   'wse_navd88_ft': {k: v[k] for k in NAMES}})
    rows.append({'landmark': name, 'station_ft': st, 'readings': rr, 'note': note})
XS = {'A': (135943, 30.6), 'B': (140508, 32.2), 'C': (145016, 33.2), 'D': (152727, 34.9), 'E': (158169, 36.0),
      'F': (161592, 36.9), 'G': (168223, 39.8), 'H': (170220, 44.8), 'I': (175499, 66.0), 'J': (181150, 82.0),
      'K': (181608, 85.9), 'L': (198423, 118.2), 'M': (205600, 125.5), 'N': (209736, 128.8), 'O': (216099, 132.9)}
fw25 = [  # Table 23 James River, PDF p.62 (printed 57)
 ('A',135943,'1,012/549',41041,6.9,30.6,30.6,31.1,0.5),('B',140508,'1,055/418',39390,7.2,32.2,32.2,32.4,0.2),
 ('C',145016,'1,481/1,291',49404,5.8,33.2,33.2,33.8,0.6),('D',152727,'2,195/1,707',65313,4.4,34.9,34.9,35.5,0.6),
 ('E',158169,'2,624/2,478',72137,3.9,36.0,36.0,36.8,0.8),('F',161592,'2,620',68362,4.1,36.9,36.9,37.6,0.7),
 ('G',168223,'1,592',28358,10.0,39.8,39.8,40.3,0.5),('H',170220,'2,662',37032,7.6,44.8,44.8,45.4,0.6),
 ('I',175499,'2,003',24313,11.6,66.0,66.0,66.2,0.2),('J',181150,'1,414',21565,13.1,82.0,82.0,82.5,0.5),
 ('K',181608,'1,448',24079,11.7,85.9,85.9,86.2,0.3),('L',198423,'2,088',30769,9.2,118.2,118.2,118.2,0.0),
 ('M',205600,'2,157/15',39888,7.1,125.5,125.5,125.9,0.4),('N',209736,'2,265/247',40734,6.9,128.8,128.8,129.4,0.6),
 ('O',216099,'2,110/32',42334,6.6,132.9,132.9,133.8,0.9)]
xs_rows = []
for r in fw25:
    v, pg = at(r[1] if r[0] not in ('J', 'K') else {'J': 181100, 'K': 181750}[r[0]])
    xs_rows.append({'xs': r[0], 'distance_ft': r[1], 'width_ft': r[2], 'area_sqft': r[3], 'velocity_fps': r[4],
                    'regulatory': r[5], 'without_floodway': r[6], 'with_floodway': r[7], 'increase': r[8],
                    'profile_read_1pct': v['p1'], 'profile_read_all': v})
fw98 = [  # Table 2 James River, 1998, PDF p.16 (printed p.12), feet NGVD29; distances feet above mouth (1) or historical miles (2)
 ('A','519,700 ft','850/810',33330,8.7,26.8,26.8,27.5,0.7),('B','520,980 ft','1000/910',40730,7.1,27.6,27.6,28.3,0.7),
 ('C','522,420 ft','1000/785',38510,7.5,27.7,27.7,28.4,0.7),('D','523,880 ft','1000/645',34510,8.4,27.7,27.7,28.4,0.7),
 ('E','525,040 ft','950/545',33290,8.7,27.9,27.9,28.6,0.7),('F','527,840 ft','1000/605',35450,8.2,29.0,29.0,29.4,0.4),
 ('G','531,880 ft','1000/885',34620,8.4,30.0,30.0,30.4,0.4),('H','533,540 ft','1100/580',38870,7.5,31.0,31.0,31.1,0.1),
 ('I','534,660 ft','1250/550',40520,7.2,31.1,31.1,31.7,0.6),('J','535,880 ft','1450/595',46930,6.2,31.6,31.6,32.3,0.7),
 ('K','536,840 ft','1600/570',48400,6.0,31.8,31.8,32.4,0.6),('L','538,180 ft','1800/915',55435,5.2,32.0,32.0,32.7,0.7),
 ('M','539,450 ft','2000/1590',58295,5.0,32.0,32.0,32.7,0.7),('M1','541,570 ft','2250/2175',64895,4.5,32.6,32.6,33.3,0.7),
 ('M2','543,450 ft','2800/2730',68840,4.2,32.8,32.8,33.6,0.8),('M3','544,710 ft','3150/3100 (to levee toe)',67165,4.3,33.3,33.3,34.1,0.8),
 ('M4','546,355 ft','3,520 (to levee toe)',66345,4.4,33.5,33.5,34.2,0.7),('M5','548,155 ft','3,440 (to levee toe)',61865,4.7,34.7,34.7,35.4,0.7),
 ('M6','549,135 ft','2,785 (to levee toe)',57930,5.0,34.8,34.8,35.5,0.7),('M7','553,920 ft','2,235 (to levee toe)',54645,5.3,38.1,38.1,38.6,0.5),
 ('M8','554,480 ft','1,875 (to levee toe)',43640,6.6,38.5,38.5,39.0,0.5),('M9','554,610 ft','1,700 (to levee toe)',35450,8.2,38.5,38.5,39.0,0.5),
 ('M10','556,105 ft','1,800',36800,7.9,46.6,46.6,47.3,0.7),('M11','558,930 ft','1,840',31940,9.1,57.6,57.6,57.7,0.1),
 ('N','106.39 mi','2,110',20729,14.0,66.9,66.9,66.9,0.0),('O','106.83 mi','1,932',33700,8.6,79.8,79.8,79.8,0.0),
 ('P','108.58 mi','1,541',26501,10.9,102.8,102.8,103.0,0.2),('Q','108.76 mi','2,313',37678,7.7,105.9,105.9,106.0,0.1),
 ('R','109.40 mi','2,336',39447,7.4,109.5,109.5,109.6,0.1),('S','110.33 mi','2,566',32971,8.8,114.7,114.7,114.9,0.2),
 ('T','110.59 mi','2,049',31328,5.5,119.6,119.6,119.7,0.1),('U','110.99 mi','1,635',29792,9.7,121.4,121.4,121.6,0.2),
 ('V','111.73 mi','2,320',41877,6.9,126.4,126.4,127.4,1.0),('W','113.35 mi','2,200',48212,6.4,135.0,135.0,135.9,0.9)]
fw98_rows = [dict(zip(['xs','distance','width_ft','area_sqft','velocity_fps','regulatory','without_floodway','with_floodway','increase'], r)) for r in fw98]
# 1998 profile panel 03P, read from the 200 dpi scan (NGVD29); stations are feet above mouth
p98 = [
 ('M4 (table 33.5)', 546355, 20.8, 29.1, 33.5, 45.9), ('Confluence of Gillies Creek', 547889, 21.1, 29.4, 33.8, 46.0),
 ('M5 (table 34.7)', 548155, 21.2, 29.7, 33.8, 46.0), ('M6 (table 34.8)', 549135, 21.6, 30.1, 34.2, 46.4),
 ('City Locks (derived station 549,230 +/-300)', 549230, 21.8, 30.1, 34.2, 46.6),
 ('I-95, downstream', 551550, 22.0, 30.6, 35.0, 46.8), ('I-95, upstream', 551900, 21.9, 30.7, 35.2, 47.0),
 ('Seaboard Coastline RR, upstream', 552600, 22.3, 31.3, 36.0, 47.6), ("Mayo's Bridge, downstream", 553100, 22.6, 31.3, 36.0, 47.8),
 ("Mayo's Bridge, upstream", 553400, 22.7, 32.1, 37.0, 48.3), ('M7 (table 38.1)', 553920, 22.9, 32.1, 37.2, 48.3),
 ('Southern Railway, upstream', 554100, 23.0, 32.8, 37.8, 49.2), ('M8 (table 38.5)', 554480, 23.4, 33.1, 37.9, 49.3)]
p98_rows = [{'place': a, 'station_ft_above_mouth': b, 'p10_ngvd29': c, 'p2_ngvd29': d, 'p1_ngvd29': e, 'p0_2_ngvd29': f} for a, b, c, d, e, f in p98]
out = {
 'reports': {'2025': {'id': '510129V000C', 'effective': '2025-07-08', 'pages': 134, 'datum': 'NAVD88',
                      'datum_source': 'Section 6.1, PDF p.49 (printed 44): flood elevations in the report and on the FIRMs are referenced to NAVD88',
                      'conversion': {'table': 'Table 19 Countywide Vertical Datum Conversion, PDF p.49 (printed 44)',
                                     'quad_corners_ft': {'Richmond NE (37.625,-77.375)': -1.042, 'Drewrys Bluff NE (37.500,-77.375)': -1.059,
                                                         'Bon Air NE (37.625,-77.500)': -0.980, 'Chesterfield NE (37.500,-77.500)': -1.025,
                                                         'Midlothian NE (37.625,-77.625)': -0.969, 'Hallsboro NE (37.500,-77.625)': -0.933,
                                                         'Beach NE (37.375,-77.500)': -1.045, 'Chester NE (37.375,-77.375)': -1.083, 'Winterpock NE (37.375,-77.625)': -0.981},
                                     'average_ft': -1.013, 'interpolated_at_city_locks_ft': -1.041, 'interpolated_at_westham_ft': -0.983,
                                     'note': 'NAVD88 = NGVD29 + conversion; interpolation is bilinear between quad corners (this check)'}},
             '1998': {'id': '510129V000', 'revised': '1998-07-20', 'pages': 48, 'datum': 'NGVD29',
                      'datum_source': 'Section 3.2, PDF p.13 (printed 9): all elevations referenced to NGVD; profiles and Table 2 labeled FEET NGVD',
                      'conversion': 'none stated in the report'}},
 'james_profiles_2025': {
   'source': F25 + ', Exhibit 1 Flood Profiles, James River panels 17P-23P, PDF pp.106-112',
   'stationing': 'feet above a point about 20,500 ft upstream of Roxbury Road (profile axis label)',
   'method': 'Profiles are vector drawings. Line positions were taken from the PDF geometry (pdftocairo SVG) and scaled from the major grid (20 ft and 1,000 ft per 72 pt). Lines were identified by order: 0.2% > 1%+ > 1% > 2% > 4% > 10% > stream bed. Reading precision 0.05 ft: the 1% reading matches all 15 Floodway Data values within 0.05 ft (see floodway_2025).',
   'precision_ft': 0.05,
   'evidence': 'evidence/fis2025_p108_panel19P_downtown-108.png',
   'landmarks': rows},
 'floodway_2025': {'source': F25 + ', Table 23 Floodway Data, James River, PDF p.62 (printed 57); distance in feet above a point about 20,500 ft upstream of Roxbury Road; widths total/within jurisdiction',
                   'rows': xs_rows},
 'floodway_1998': {'source': F98 + ', Table 2 Floodway Data, James River, PDF p.16 (printed p.12), feet NGVD; footnotes: (1) feet above mouth, (2) miles above mouth on historical milepost stationing, (4) width extends to landside toe of levee/floodwall',
                   'evidence': 'evidence/fis1998_p16_floodway_james.png', 'rows': fw98_rows},
 'james_profiles_1998_downtown': {'source': F98 + ', Exhibit 1, James River panel 03P, PDF p.29, feet NGVD29',
   'method': 'read from a 200 dpi render of the scan; grid calibrated at 198.2 px per 1,000 ft and 10.12 px per ft; profile lines found as dark runs of 4 px or more; precision about 0.3 ft',
   'evidence': 'evidence/fis1998_p29_panel03P-29.png',
   'labels_ft_above_mouth': {'Confluence of Gillies Creek': 547889, 'I-95 (Richmond-Petersburg Turnpike)': 551723, 'Seaboard Coastline Railroad': 552444,
                             "Mayo's Bridge": 553247, 'Southern Railway': 553953, '9th Street / Manchester Street': 555945,
                             'second label read as 8th Street (UNCONFIRMED reading)': 556086, 'Browns Island Dam': 556667},
   'offset_note': '1998 station = 2025 station + about 387,700 ft in this reach (I-95, Gillies, Mayo agree within 60 ft)',
   'internal_inconsistency': 'The plotted 100-year line sits 0.6 to 0.9 ft below the 1998 Floodway Data values at M5 to M8 (e.g. M5 33.8 plotted vs 34.7 table); it matches at M4 (33.5). The table is the regulatory value.',
   'rows': p98_rows},
 'james_profiles_1998_upper_labels_miles': {'source': F98 + ', panels 03P(b) and 03P(c), PDF pp.31-32',
   'labels': {'Hollywood Dam': 106.0, 'Confluence of Reedy Creek': 106.7, 'Boulevard Bridge': 107.5, 'Seaboard Coastline Railroad': 108.2, 'Powhite Freeway': 108.35,
              'Confluence of Powhite Creek': 108.55, 'Williams Island Dam': 110.6, 'Corporate limits': 110.8, 'Confluence of Rattlesnake Creek': 111.2,
              'Huguenot Bridge': 111.65, 'Confluence of Stony Point Creek': 112.5, 'Boshers Dam (section W)': 113.35, 'Confluence of Cherokee Creek': 113.4,
              'Confluence of Pittaway Creek': 114.3, 'Corporate limits (upstream)': 114.5},
   'label_precision_mi': 0.05,
   'boulevard_bridge_read_ngvd29': {'p0_2': 93.7, 'p1': 88.0, 'p2': 86.1, 'p10': 81.8, 'precision_ft': 1.0, 'page': 'PDF p.31, panel 03P(b)'}},
 'discharges_2025': {'source': F25 + ', Table 9 Summary of Discharges, PDF p.32 (printed 27)', 'units': 'cfs', 'rows': [
   {'location': 'about 2,000 ft upstream of Chippenham Parkway', 'da_sqmi': 6833, 'p10': 149248, 'p4': 198222, 'p2': 239404, 'p1': 284735, 'p0_2': 409193},
   {'location': 'upstream of confluence with Broad Rock Creek', 'da_sqmi': 6822, 'p10': 149009, 'p4': 197905, 'p2': 239021, 'p1': 284279, 'p0_2': 408538},
   {'location': 'upstream of confluence with Gillies Creek', 'da_sqmi': 6799, 'p10': 148511, 'p4': 197243, 'p2': 238222, 'p1': 283329, 'p0_2': 407172},
   {'location': 'upstream of confluence with Reedy Creek', 'da_sqmi': 6770, 'p10': 147884, 'p4': 196409, 'p2': 237215, 'p1': 282132, 'p0_2': 405452},
   {'location': 'at Powhite Parkway', 'da_sqmi': 6757, 'p10': 147600, 'p4': 196033, 'p2': 236761, 'p1': 281591, 'p0_2': 404675},
   {'location': 'at USGS gage 02037500', 'da_sqmi': 6753, 'p10': 147500, 'p4': 195900, 'p2': 236600, 'p1': 281400, 'p0_2': 404400}],
   'gage_record_used': 'Table 11, PDF p.35 (printed 30): 02037500, 09/07/1935 to 02/25/2016',
   'method': 'Table 12, PDF p.39 (printed 34): gage analysis and regression; HEC-RAS 5.0.5; calibrated to gage rating; natural valley analyses conducted for the City of Richmond levee systems; analysis date 03/25/2020'},
 'discharges_1998': {'source': F98 + ', Table 1, PDF p.11 (printed 7)', 'rows': [
   {'location': 'James River at downstream corporate limits', 'da_sqmi': 6758.0, 'p10': 131000, 'p2': 232000, 'p1': 290000, 'p0_2': 475000}],
   'method': 'PDF p.10 (printed 6): log-Pearson Type III of Westham annual peaks, values supplied by the Virginia State Water Control Board; HEC-2 (PDF p.12, printed 8); James restudied by USACE Norfolk from the downstream corporate limits to the downstream side of Hollywood Dam (PDF p.6, printed 2; OCR reads "Hollywood Drain")'},
 'stillwater_tidal': {'2025': 'Table 10 (non-coastal stillwater) and all coastal sections: not applicable (PDF pp.35, 47-48)', '1998': 'none given'},
 'historic_floods': {
   '2025_table6': {'source': F25 + ', Table 6 Historic Flooding Elevations, PDF p.27 (printed 22)',
                   'rows': [{'location': 'James River near Richmond, VA (USGS 02037500)', 'peak_navd88_ft': 126.4, 'date': '1972-06-23', 'recurrence_yr': '100 to 200'}]},
   '2025_table5': 'PDF p.27 (printed 22): 20-year flood floods a substantial part of the industrial and commercial section; Agnes June 1972 among the largest; navigation to City Locks interrupted at a 14 ft flood stage; Shockoe Creek levee overtopped in 1972 and pumping stopped for structural reasons in Camille 1969; Gaston Aug 30, 2004, up to 14 in of rain in the Shockoe basin (text cited to FEMA 2009)',
   '1998_list': {'source': F98 + ', Section 2.3, PDF p.8 (printed 4)', 'rows': [
     {'date': 'May 1771', 'cfs': None, 'recurrence': '50 to 100 years'}, {'date': 'October 1870', 'cfs': None, 'recurrence': '20 to 50 years'},
     {'date': 'November 1877', 'cfs': None, 'recurrence': '20 to 50 years'}, {'date': 'April 1937', 'cfs': 148000, 'recurrence': '10 to 20 years'},
     {'date': 'August 1940', 'cfs': 151000, 'recurrence': '10 to 20 years'}, {'date': 'September 1944', 'cfs': 150000, 'recurrence': '10 to 20 years'},
     {'date': 'December 1948', 'cfs': 136000, 'recurrence': '10 to 20 years'}, {'date': 'August 1969', 'cfs': 222000, 'recurrence': '20 to 50 years'},
     {'date': 'June 1972', 'cfs': 313000, 'recurrence': '100 to 200 years'}],
     'note': 'no 1936 or 1985 entry; April 1937 flow given as 148,000 (USGS peak file: 152,000, a daily mean)'}},
 'levees': {
   '2025_table8': {'source': F25 + ', Table 8 Levee Systems, PDF p.29 (printed 24)', 'rows': [
     {'nld_id': '4605000002', 'name': 'Richmond, Virginia (North)', 'status': 'Accredited', 'panels': ['5101290041F', '5101290043F'], 'owner': 'City of Richmond'},
     {'nld_id': '4605000003', 'name': 'Richmond Filtration Plant', 'status': 'Accredited', 'panels': ['5101290017E', '5101290036E'], 'owner': 'City of Richmond'},
     {'nld_id': '4605000007', 'name': 'Richmond, Virginia (South)', 'status': 'Accredited', 'panels': ['5101290039F', '5101290043F'], 'owner': 'City of Richmond'}]},
   '2025_text': 'Section 4.4, PDF p.28 (printed 23): accreditation under 44 CFR 65.10; Notes to Users PDF p.8 and PDF p.13 (accredited and provisionally accredited notes; owner data due by Sept 28, 2022); legend PDF p.15: area shown as reduced flood hazard from the 1% or greater flood by an accredited or provisionally accredited levee, overtopping or failure possible. Table 12 (PDF p.39): natural valley analyses conducted for the City levee systems. No top-of-wall elevation, design flood, interior drainage analysis, or with/without-levee profile is printed.',
   '1998_text': 'PDF p.9 (printed 5): USACE levee/floodwall protects the Shockoe Creek area and low-lying southside Richmond; FEMA required 3 ft freeboard over the 100-year flood; the system meets that for the 100-year flood but does not protect against the 500-year flood. Floodway widths M3 to M9 extend to the landside toe of the levee/floodwall (Table 2 footnote 4).'},
 'tributaries': {
   'Gillies Creek': {'2025': 'Table 23 PDF p.59 (printed 54): sections A-D (1,337 to 5,558 ft above the James) regulatory 1% = 36.3 NAVD88, set by James backwater; without backwater 23.5, 28.0, 29.2, 33.9; E 37.6, F 42.6, G 44.7, H 54.8, I 62.7. Profile panel 13P (PDF p.102). Discharge at mouth: 3,366 / 4,876 / 6,045 / 7,813 / 18,619 cfs (Table 9 PDF p.31).',
                     '1998': 'detailed in 1978 FIS; profile panel 19P; parts approximate (PDF p.6); 100-year 7,100 cfs at Jennie Scher Road (Table 1 PDF p.12); no floodway table in 1998.'},
   'Shockoe Creek': {'2025': 'SWMM 5.1.012 model of storm drains, combined sewers, storage and pumping stations (Table 12 PDF p.43); study from confluence with the Kanawha Canal to the CSX railroad, 3.0 mi, analysis 06/16/2021 (Table 2 PDF p.21). Table 23 PDF p.70: section A (262 ft above the Kanawha Canal) 1% = 19.4 NAVD88, B 20.5, C 21.2, D 25.3, E 25.3, F 32.2, G 33.8, H 35.2, J 39.3, L 46.1; this is interior flooding behind the wall, not river backwater. Profiles 37P-39P, split flow 40P.',
                     '1998': 'not studied in detail; Shockoe Creek levee history only (PDF p.9).'},
   'Reedy Creek': {'2025': 'Table 23 PDF p.65: section A (1,871 ft above the James) regulatory 71.4 (James backwater), 66.3 without backwater; profiles 33P-36P.', '1998': 'approximate only (PDF p.6).'},
   'Goodes Creek': {'2025': 'joins Broad Rock Creek, not the James; Table 23 PDF p.60, A 45.2 regulatory (backwater from Broad Rock Creek).', '1998': 'Table 2 PDF p.20, A 42.2 NGVD.'},
   'Cannon Creek Branch': {'2025': 'joins Bacons Quarter Branch (Shockoe system), SWMM; Table 23 PDF p.56, A 75.5.'},
   'Almond Creek': 'not named in either report (UNCONFIRMED whether mapped as Zone A or X)',
   'Stony Run': {'2025': 'joins Gillies Creek', '1998': 'Table 2 PDF p.21, A 49.5 NGVD; Gillies backwater from the Henrico FIS (PDF p.13).'}},
 'other_1998': {'Gathright Dam': 'reduces peak discharges at Richmond by about 1.5 percent of the average (PDF p.9, printed 5)',
                'downstream channel improvement': 'reduces major flood elevations in Richmond; the report says it shortened the channel by about 2 feet in the city (literal wording, PDF p.9)',
                'navigation': 'interrupted at a 14 ft flood stage at Richmond (PDF p.8)',
                'map history': 'FIS Dec 1978, FIRM June 15, 1979; revised July 20, 1998 (PDF p.2)'},
 'map_history_2025': 'Table 27 PDF p.81 (printed 76): initial identification 12/06/1974; FHBM revised 09/19/1975; initial FIRM 06/15/1979; revisions 07/20/1998, 04/02/2009, 07/16/2014, 07/08/2025',
}
json.dump(out, open('/home/claude/floods-research/check/fis.json', 'w'), indent=1)
for r in rows:
    print(r['landmark'][:50], [(x['side'], x['wse_navd88_ft']['p10'], x['wse_navd88_ft']['p4'], x['wse_navd88_ft']['p2'], x['wse_navd88_ft']['p1'], x['wse_navd88_ft']['p1plus'], x['wse_navd88_ft']['p0_2']) for x in r['readings']])
print([(r['xs'], r['regulatory'], r['profile_read_1pct']) for r in xs_rows])
