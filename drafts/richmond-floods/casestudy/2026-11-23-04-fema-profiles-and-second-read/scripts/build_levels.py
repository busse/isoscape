# Builds check/levels.json: drawing levels on the tidal reach and control points through the falls.
import json, math
pts = json.load(open('/home/claude/floods-research/check/work/jr_chain.json'))['pts']   # OSM James River centerline, cached Nov 14 2026
OFF = 137100  # FIS 2025 station minus OSM chainage from the chain's downstream end (ten bridges agree within about 300 ft)
lat0 = 37.53
xy = lambda p: ((p[1] + 77.45) * 111320 * math.cos(math.radians(lat0)), (p[0] - lat0) * 110540)
P = [xy(p) for p in pts]; cum = [0]
for a, b in zip(P, P[1:]): cum.append(cum[-1] + math.dist(a, b))
L = cum[-1]
def lonlat(station_ft):
    s = L - (station_ft - OFF) / 3.28084
    for i in range(len(P) - 1):
        if cum[i] <= s <= cum[i + 1]:
            t = (s - cum[i]) / (cum[i + 1] - cum[i]); a, b = pts[i], pts[i + 1]
            return [round(a[1] + t * (b[1] - a[1]), 5), round(a[0] + t * (b[0] - a[0]), 5)]
# HA-410 old river mile -> FIS 2025 station, anchored on bridges and the Locks
ANCH = [(103.7, 161530), (104.20, 164010), (104.59, 165592), (105.10, 168431), (105.50, 170522), (107.51, 181453), (111.7, 203720)]
def ha2st(m):
    for (m0, s0), (m1, s1) in zip(ANCH, ANCH[1:]):
        if m0 <= m <= m1: return round(s0 + (m - m0) / (m1 - m0) * (s1 - s0))
    (m0, s0), (m1, s1) = (ANCH[0], ANCH[1]) if m < ANCH[0][0] else (ANCH[-2], ANCH[-1])
    return round(s0 + (m - m0) / (m1 - m0) * (s1 - s0))
C = -1.03  # NGVD29 -> NAVD88 (NGS NCAT at both gauges; FIS 2025 Table 19 gives -1.04 at the Locks)
W = 98.04  # Westham gauge zero NAVD88, USGS site file (GNSS, +/-0.08 ft)
S = {'OFR': 'USGS OFR 70-51 (1970), station 02-0377.00, printed p.119 (PDF p.131); Table 2 printed p.20',
     'PP924': 'USGS PP 924 Table A4, PDF p.406', 'HA410': 'USGS HA-410 (1969) Figure 1, read for this check at 300 dpi, +/-0.3 ft at marks, +/-0.7 ft between marks',
     'HA410T1': 'USGS HA-410 Table 1 (mile 104.6)', 'NWS': 'NWS NWPS RICV2 crest list (raw/nwps_ricv2.json)',
     'USGSPK': 'USGS annual peak file 02037500 (raw/peak_02037500.rdb)', 'USGSIV': 'USGS 02037705 parameter 62620 (NAVD88), approved instantaneous values, fetched 2026-11-23',
     'SIGN1': 'Agnes high-water sign, Dock and Pear streets (hmdb 133685)', 'SIGN2': 'Agnes high-water sign, Tredegar St at Browns Island Way (hmdb 124035)',
     'NOAA72': 'NOAA Agnes disaster survey report, Oct 1972 (govinfo CZIC-gb70-9-u55-1972)', 'FIS25': 'FEMA FIS 510129V000C (2025) Table 6, PDF p.27'}
def cp(place, mile=None, station=None, elev=None, src='', note=''):
    st = station if station is not None else (ha2st(mile) if mile is not None else None)
    d = {'place': place}
    if mile is not None: d['ha410_river_mile'] = mile
    if st is not None: d['fis2025_station_ft'] = st; d['lonlat_on_centerline'] = lonlat(st)
    d['elev_navd88_ft'] = round(elev, 2); d['elev_navd88_m'] = round(elev * 0.3048006, 3); d['source'] = src
    if note: d['note'] = note
    return d
LOCKS, MAYO = 161530, 165500
floods = []
def F(**k):
    k['level_navd88_m'] = round(k['level_navd88_ft'] * 0.3048006, 3); floods.append(k)
F(id='1972-06', name='Agnes', level_navd88_ft=35.5, uncertainty_ft=0.3,
  basis='City Locks gauge 36.5 ft on its 1957 NGVD29 zero minus 1.03, and the Dock and Pear sign 35.5 NAVD88 agree; add about 1.3 ft by the Mayo Bridge',
  sources=[S['NOAA72'], S['PP924'], S['NWS'], S['SIGN1']],
  mayo_bridge_navd88_ft=36.8, mayo_note='Locks plus 1.3 ft, the 1969 Locks-to-Mayo rise; not measured in 1972. UNCONFIRMED, +/-1 ft',
  control_points=[cp('City Locks gauge', station=LOCKS, elev=35.47, src=S['NOAA72'] + '; ' + S['PP924']),
                  cp('Tredegar St at Browns Island Way (pocket behind Brown\'s Island, NOT the main channel)', station=169640, elev=40.0, src=S['SIGN2'],
                     note='below the FIS 1% channel level there (44.0) and below the 1969 channel profile; consistent with water ponded behind Brown\'s Island at the level of the river below the Brown\'s Island dam step (FIS 1% 41.1 just below Potterfield bridge). Do not use as a channel point.'),
                  cp('Westham gauge', station=203720, elev=28.62 + W, src=S['USGSPK'] + '; gauge zero 98.04 NAVD88', note='FEMA (FIS 2025 Table 6) uses 126.4, i.e. the old 98.82 NGVD29 zero converted; difference 0.25 ft')])
F(id='1969-08', name='Camille', level_navd88_ft=27.6, uncertainty_ft=0.2,
  basis='City Locks 28.64 ft NGVD29 at 6 a.m. Aug 22 (OFR 70-51) minus 1.03; HA-410 marks agree',
  sources=[S['OFR'], S['PP924'], S['HA410']], mayo_bridge_navd88_ft=28.9, mayo_note='HA-410 Table 1: 29.9 NGVD29 at mile 104.6; OFR 70-51 Table 2: 27.6 on the old scale +2.36 = 29.96',
  control_points=[cp('City Locks gauge', station=LOCKS, elev=27.61, src=S['OFR']),
                  cp('I-95 bridge', 104.20, elev=28.7 + C, src=S['HA410']),
                  cp("Mayo's Bridge (mile 104.6)", 104.59, elev=29.9 + C, src=S['HA410T1']),
                  cp('just below 9th St bridge, foot of the drop', 105.06, elev=34.4 + C, src=S['HA410']),
                  cp('just below 9th St bridge, head of the drop', 105.06, elev=38.1 + C, src=S['HA410'], note='the two marks bracket a vertical drop at the 9th St bridge'),
                  cp('mile 105.21', 105.21, elev=40.5 + C, src=S['HA410']),
                  cp('mile 105.27', 105.27, elev=42.4 + C, src=S['HA410']),
                  cp('Robert E. Lee Bridge', 105.50, elev=43.9 + C, src=S['HA410'], note='between marks, +/-0.7 ft'),
                  cp('mile 106.1', 106.1, elev=66.0 + C, src=S['HA410'], note='HA-410 says the 1969 profile between miles 105 and 107 was built largely from the 1937 profile'),
                  cp('mile 106.5', 106.5, elev=70.8 + C, src=S['HA410'], note='as above'),
                  cp('mile 107.0', 107.0, elev=74.7 + C, src=S['HA410'], note='as above'),
                  cp('mile 107.28 (mark)', 107.28, elev=79.4 + C, src=S['HA410']),
                  cp('Boulevard Bridge', 107.51, elev=83.8 + C, src=S['HA410'], note='between marks, +/-0.7 ft; the earlier research read 84.9'),
                  cp('mile 107.59 (mark)', 107.59, elev=85.1 + C, src=S['HA410']),
                  cp('mile 108.19 (mark)', 108.19, elev=94.4 + C, src=S['HA410']),
                  cp('mile 108.72 (mark)', 108.72, elev=101.6 + C, src=S['HA410']),
                  cp('Westham gauge', station=203720, elev=24.95 + W, src=S['USGSPK'])])
F(id='1985-11', name='Election Day flood (Juan)', level_navd88_ft=29.7, uncertainty_ft=0.4,
  basis='NWS City Locks crest 30.76 ft, gauge era 1957-2007 (NGVD29 zero) minus 1.03; other accounts round to 30.7-31',
  sources=[S['NWS'], 'Friends of James River Park gauge marker (hmdb 61821): 30.7'], mayo_bridge_navd88_ft=31.0,
  mayo_note='Locks plus 1.3 ft assumed. UNCONFIRMED, +/-1 ft',
  control_points=[cp('City Locks gauge', station=LOCKS, elev=29.73, src=S['NWS']),
                  cp('Westham gauge', station=203720, elev=24.77 + W, src=S['USGSPK'] + '; WDR 1986 PDF p.230')])
F(id='1936-03', name='March 1936', level_navd88_ft=26.5, uncertainty_ft=0.4,
  basis='PP 924 gives 27.5 ft msl at the City Locks; HA-410 marks near the Locks read 27.2 to 27.5 NGVD29; minus 1.03',
  sources=[S['PP924'], S['HA410'], S['HA410T1']], mayo_bridge_navd88_ft=27.8, mayo_note='HA-410 Table 1: 28.8 NGVD29 at mile 104.6; old Weather Bureau gauge 26.5 + 2.36 = 28.86',
  control_points=[cp('mile 102.87 (mark)', 102.87, elev=26.8 + C, src=S['HA410']),
                  cp('mile 103.10 (mark)', 103.10, elev=27.3 + C, src=S['HA410']),
                  cp('City Locks', station=LOCKS, elev=27.5 + C, src=S['PP924']),
                  cp('mile 103.99 (mark)', 103.99, elev=27.5 + C, src=S['HA410']),
                  cp('mile 104.40 (mark)', 104.40, elev=27.9 + C, src=S['HA410']),
                  cp("Mayo's Bridge (mile 104.6)", 104.6, elev=28.8 + C, src=S['HA410T1']),
                  cp('mile 104.79 (mark)', 104.79, elev=28.8 + C, src=S['HA410']),
                  cp('mile 105.59 (mark, just above Lee Bridge)', 105.59, elev=44.6 + C, src=S['HA410']),
                  cp('Boulevard Bridge (mark)', 107.48, elev=82.9 + C, src=S['HA410']),
                  cp('mile 108.93 (mark)', 108.93, elev=102.4 + C, src=S['HA410']),
                  cp('Westham gauge', station=203720, elev=23.42 + W, src=S['USGSPK'])])
F(id='1996-09', name='Fran', level_navd88_ft=22.7, uncertainty_ft=1.0,
  basis='NWS City Locks crest 23.75 ft; taken as the NGVD29-zero era (USGS NAVD88 series starts Oct 1 2007); if the 1996 value were already NAVD88 the level is 23.75, so the error is one-sided upward',
  sources=[S['NWS'], 'City floodwall FAQ (23.8, secondary)'], mayo_bridge_navd88_ft=24.0, mayo_note='Locks plus 1.3 ft assumed. UNCONFIRMED',
  control_points=[cp('City Locks gauge', station=LOCKS, elev=22.72, src=S['NWS'], note='datum era UNCONFIRMED'),
                  cp('Westham gauge', station=203720, elev=21.23 + W, src=S['USGSPK'])])
F(id='2020-11', name='November 2020', level_navd88_ft=17.0, uncertainty_ft=0.1,
  basis='USGS approved NAVD88 series at City Locks peaks at 16.96 ft at 04:48-04:54 EST Nov 14 2020',
  sources=[S['USGSIV'], S['NWS']], mayo_bridge_navd88_ft=None, mayo_note='no measurement; the 1969 rise of 1.3 ft does not scale to a flood this small (UNCONFIRMED); draw flat or use the NWS/USACE FIM layers',
  control_points=[cp('City Locks gauge', station=LOCKS, elev=16.96, src=S['USGSIV']),
                  cp('Westham gauge', station=203720, elev=18.33 + W, src=S['USGSPK'])])
F(id='1771-05', name='Great Fresh of 1771', level_navd88_ft=38.0, uncertainty_ft=3.0,
  basis='Corps figure 38 ft on the old Weather Bureau scale near Mayo\'s Bridge (from diaries) + 2.36 - 1.03 = 39.3 at Mayo; minus 1.3 to the Locks. Rests on diary accounts and on the 1876 gauge scale; UNCONFIRMED as an elevation',
  sources=[S['OFR'] + ' (Table 2: c38, datum 2.36; station page: 38 ft May 27, 1771, from a Corps report)'], mayo_bridge_navd88_ft=39.3,
  mayo_note='derived; 1998 FIS lists May 1771 as a 50 to 100 year flood (PDF p.8)',
  control_points=[cp("Mayo's Bridge (old gauge site)", 104.6, elev=38 + 2.36 + C, src=S['OFR'])])
out = {'generated': '2026-11-23', 'datum': 'NAVD88 (feet and meters; m = ft x 0.3048006)',
       'reach': 'Tidal reach below the Mayo Bridge: draw level_navd88_ft from the Locks downstream (Rocketts, Fulton/Gillies mouth, Manchester flats) and ramp linearly to mayo_bridge_navd88_ft at the bridge',
       'dem_note': 'USGS 3DEP 1/3 arc-second DEM is referenced to NAVD88, horizontal NAD83 (data.gov catalog record for the 3DEP 1/3 arc-second DEM collection, read 2026-11-23). FIS 2025 mapping used the 2014 USGS VA NRCS lidar (Table 22, PDF p.51).',
       'stations': 'fis2025_station_ft is the FIS 2025 James profile stationing; HA-410 miles mapped to it through bridges (Locks 103.7, I-95 104.20, Mayo 104.59, 9th St 105.10, Lee 105.50, Boulevard 107.51, Westham 111.7). lonlat_on_centerline is the point on the OSM James centerline at that station (OSM data, ODbL; station-to-OSM offset 137,100 ft, +/-300 ft).',
       'fis_context_at_city_locks_navd88_ft': {'2025 FIS (station ~161,530)': {'10%': 25.8, '4%': 30.3, '2%': 33.6, '1%': 36.9, '1%+': 43.5, '0.2%': 44.5},
                                                '1998 FIS (converted -1.03)': {'10%': 20.8, '2%': 29.1, '1% table M6': 33.8, '0.2%': 45.4}},
       'floods': floods}
json.dump(out, open('/home/claude/floods-research/check/levels.json', 'w'), indent=1)
for f in floods: print(f['name'], f['level_navd88_ft'], f['level_navd88_m'], f['mayo_bridge_navd88_ft'], len(f['control_points']), f['control_points'][0].get('lonlat_on_centerline'))
