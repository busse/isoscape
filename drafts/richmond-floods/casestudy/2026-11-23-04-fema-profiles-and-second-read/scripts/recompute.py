# Independent re-derivation of the conversions in river/tools/build_floods_json.py.
# Every input is listed with its source; outputs go to check/work/recompute.json.
import json
FT_PER_M = 3.280833333  # US survey foot
ncat_m = 99.687 - 100.000                      # raw/ncat.json at Westham: NGVD29 100.000 m -> NAVD88 99.687 m
ncat_ft = ncat_m * FT_PER_M
# FIS 2025 Table 19 (PDF p.49): NGVD29->NAVD88 at quadrangle NE corners (ft)
T19 = {(37.625, -77.375): -1.042, (37.500, -77.375): -1.059, (37.625, -77.500): -0.980,
       (37.500, -77.500): -1.025, (37.625, -77.625): -0.969, (37.500, -77.625): -0.933}
def bilin(lat, lon):
    la0 = 37.5 if lat < 37.625 else 37.625; la1 = la0 + 0.125
    lo0 = -77.5 if lon > -77.5 else -77.625; lo1 = lo0 + 0.125
    v = lambda a, b: T19[(a, b)]
    tx = (lon - lo0) / 0.125; ty = (lat - la0) / 0.125
    return (v(la0, lo0) * (1 - tx) * (1 - ty) + v(la0, lo1) * tx * (1 - ty) +
            v(la1, lo0) * (1 - tx) * ty + v(la1, lo1) * tx * ty)
locks = (37.52514666, -77.4208158); westham = (37.5632022, -77.5469314)   # USGS site files
c_locks = bilin(*locks); c_west = bilin(*westham)
W_NGVD = 98.82; W_NAVD = 98.04; OLD_WB = 2.36; MAYO_TO_LOCKS = 1.3
out = {'ncat_ft': round(ncat_ft, 3), 'fis_t19_locks_ft': round(c_locks, 3), 'fis_t19_westham_ft': round(c_west, 3),
       'fis_t19_average_ft': -1.013,
       'westham_zero_navd_from_ngvd_ncat': round(W_NGVD + ncat_ft, 2),
       'westham_zero_navd_from_ngvd_t19': round(W_NGVD + c_west, 2),
       'westham_zero_navd_usgs': W_NAVD}
floods = {  # stage at Westham (USGS peak file), Locks stage and era
 'Agnes 1972':   (28.62, 36.5, 'ngvd'), 'Camille 1969': (24.95, 28.64, 'ngvd'), 'Nov 1985': (24.77, 30.76, 'ngvd'),
 'Mar 1936':     (23.42, 26.5, 'wb'),   'Apr 1937': (22.65, 25.2, 'wb'),        'Fran 1996': (21.23, 23.75, 'ngvd'),
 'Jan 1996':     (20.63, 22.05, 'ngvd'), 'Feb 2003': (18.73, 17.76, 'ngvd'),    'Jan 2010': (18.10, 15.92, 'navd'),
 'Nov 2020':     (18.33, 16.96, 'navd'), 'Feb 2025': (17.14, 14.62, 'navd')}
rows = {}
for k, (ws, ls, era) in floods.items():
    r = {'westham_navd_usgs_zero': round(ws + W_NAVD, 2), 'westham_navd_converted_ncat': round(ws + W_NGVD + ncat_ft, 2),
         'westham_navd_converted_t19': round(ws + W_NGVD + c_west, 2), 'westham_ngvd': round(ws + W_NGVD, 2)}
    if era == 'ngvd':
        r['locks_ngvd'] = ls; r['locks_navd_ncat'] = round(ls + ncat_ft, 2); r['locks_navd_t19'] = round(ls + c_locks, 2)
    elif era == 'wb':
        r['mayo_ngvd'] = round(ls + OLD_WB, 2); r['mayo_navd_ncat'] = round(ls + OLD_WB + ncat_ft, 2)
        r['locks_est_ngvd'] = round(ls + OLD_WB - MAYO_TO_LOCKS, 2); r['locks_est_navd'] = round(ls + OLD_WB - MAYO_TO_LOCKS + ncat_ft, 2)
    else:
        r['locks_navd'] = ls; r['locks_ngvd'] = round(ls - ncat_ft, 2)
    rows[k] = r
out['floods'] = rows
# 1771: c38 on the old Weather Bureau scale (OFR 70-51 Table 2, station page)
out['1771'] = {'mayo_ngvd': 38 + OLD_WB, 'mayo_navd_ncat': round(38 + OLD_WB + ncat_ft, 2),
               'locks_est_navd': round(38 + OLD_WB - MAYO_TO_LOCKS + ncat_ft, 2)}
# HA-410 Table 1 elevations at mile 104.6 (NGVD29) -> NAVD88
out['ha410_t1_navd'] = {y: round(e + ncat_ft, 2) for y, e in {'1870': 27.5, '1877': 29.0, '1886': 25.6, '1889': 26.6, '1936': 28.8, '1937': 27.5, '1969': 29.9}.items()}
# NOAA 8638495 max vs USGS 62620 for 2010-01-27
out['noaa_vs_usgs_2010'] = {'noaa_max_ft': 16.929, 'usgs_navd88_ft': 15.92, 'difference_ft': round(16.929 - 15.92, 3)}
json.dump(out, open('/home/claude/floods-research/check/work/recompute.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
