"""
Dev tool (floods spike, step 15): a rough check of how much water could leave Shockoe
Bottom over the riverfront line at a given pool level, with the floodwall's line open
(the wall removed, case c) and with only the wall's openings open (case b). Broad-crested
weir, Q = 1.7 * b * H^1.5 (SI), summed in 2 m pieces along OSM's north wall line, the crest
being the highest ground within 4 m of the line (case c) or the ground in the openings
(case b). An order-of-magnitude look, not hydraulics: it ignores the water's approach,
submergence by the Dock beyond, the sewers, and every opening's real width and sill.

  python3 tools/floods/outlet.py <dem-prefix> <osm.json> <spill-out-dir>
"""
import json, math, os, sys
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(__file__))
from common import Grid, KX, KY, load_dem, osm_ways

FT = 3.28084

def main():
    prefix, osm_path, out = sys.argv[1:4]
    h, _ = load_dem(prefix); g = Grid(h)
    zc = np.load(os.path.join(out, 'z-c_wall_removed.npy')).astype(float)
    crest_c = ndimage.maximum_filter(zc, size=5)
    north = [pts for wid, t, pts in osm_ways(osm_path) if t.get('wall') == 'flood_wall' and wid in (307149343, 307149341, 307149340, 307149344, 1303402964)]
    rep = json.load(open(os.path.join(out, 'spill.json')))
    gaps = [(p, q, d) for (p, q), d in zip(rep['osm_wall_gaps_lonlat'], rep['osm_wall_gaps_m']) if p[1] > 37.53]
    pieces_c = []
    for pts in north:
        for a, b in zip(pts, pts[1:]):
            L = math.hypot((b[0] - a[0]) * KX, (b[1] - a[1]) * KY); n = max(1, int(L / 2))
            for k in range(n):
                t = (k + 0.5) / n; lon = a[0] + (b[0] - a[0]) * t; lat = a[1] + (b[1] - a[1]) * t
                r, c = g.rc(lon, lat)
                pieces_c.append((L / n, float(ndimage.map_coordinates(crest_c, [[r], [c]], order=1)[0])))
    # The gaps themselves count too in case c (the line runs on across them).
    pieces_b = []
    for p, q, d in gaps:
        r, c = g.rc((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        sill = float(ndimage.map_coordinates(zc, [[r], [c]], order=1)[0])
        pieces_c.append((d, sill)); pieces_b.append((d, sill))
    def Q(pieces, L): return sum(1.7 * w * max(0.0, L - z) ** 1.5 for w, z in pieces)
    levels = np.arange(5.5, 11.01, 0.25)
    rows = [{'level_m': round(float(L), 2), 'level_ft': round(float(L) * FT, 1), 'Q_wall_removed_m3s': round(Q(pieces_c, L), 1), 'Q_openings_only_m3s': round(Q(pieces_b, L), 1)} for L in levels]
    def needed(pieces, q):
        lo, hi = 0.0, 15.0
        for _ in range(60):
            m = (lo + hi) / 2
            if Q(pieces, m) < q: lo = m
            else: hi = m
        return round(hi, 2)
    res = {'line_length_m': round(sum(w for w, _ in pieces_c), 1), 'openings': [{'mid_lonlat': [round((p[0] + q[0]) / 2, 5), round((p[1] + q[1]) / 2, 5)], 'width_m': d, 'sill_m': round(z, 2)} for (p, q, d), (_, z) in zip(gaps, pieces_b)],
           'rows': rows, 'level_to_pass': {}}
    for q in (170, 310):
        res['level_to_pass'][f'{q}_m3s'] = {'wall_removed_m': needed(pieces_c, q), 'openings_only_m': needed(pieces_b, q)}
    json.dump(res, open(os.path.join(out, 'outlet.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'rows'}, indent=1))

if __name__ == '__main__':
    main()
