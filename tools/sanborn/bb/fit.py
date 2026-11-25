"""Fit each sheet to today's street corners (similarity: shift, turn, one scale) and report how
far each corner misses. Control points: [u, v, label] read off the 50% scans; ground from OSM."""
import json, sys, math
import numpy as np
sys.path.insert(0, '..')
from geo import to_m, fit_sim, w2i
osm = json.load(open('osm_corners.json')); cps = json.load(open(sys.argv[1])); out = {}
for sheet, rows in cps.items():
    uv = np.array([r[:2] for r in rows], float)
    x, y = to_m([osm[r[2]][0] for r in rows], [osm[r[2]][1] for r in rows]); xy = np.stack([x, y], 1)
    p = fit_sim(xy, uv); res = np.hypot(*(w2i(p, xy) - uv).T) / p[3]
    out[sheet] = dict(params=[float(v) for v in p], m_per_px=round(1 / p[3], 4),
                      corners=[dict(label=r[2], u=r[0], v=r[1], miss_m=round(float(m), 2)) for r, m in zip(rows, res)],
                      mean_m=round(float(res.mean()), 2), worst_m=round(float(res.max()), 2))
    print(sheet, 'm/px', out[sheet]['m_per_px'], 'mean', out[sheet]['mean_m'], 'worst', out[sheet]['worst_m'], [(r[2], round(float(m), 1)) for r, m in zip(rows, res)])
json.dump(out, open(sys.argv[2], 'w'), indent=1)
