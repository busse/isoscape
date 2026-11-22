"""Read control points off the scan by machine: each named corner's two streets (OpenStreetMap,
today) are laid on the scan through the current fit and slid to where they best sit on the
printed lines; the corner's place on the scan is where they then cross.

    python3 -I snapcp.py <scan.jpg> <osm.json> <georef.json> <candidates.json> <cps out.json> [reach px=40]

candidates.json: [[lon, lat, label, "street A|alt", "street B|alt"], ...] (from corners.py).
For each corner, every street of today (residential and larger, as in globalfit.py) within
RADIUS m of it is sampled every 4 m and mapped to the scan by the current transform (start from
globalfit.py's fit, so the shift left to find is small). The neighborhood, not just the two
named streets, is used so the match is unique in a grid of like blocks. The shift within +-reach px that puts the samples nearest the
ink (gray < INK; mean distance to ink, capped at CAP px) is kept. A corner is accepted when, at
the best shift, at least MIN_ON of the samples lie within 2 px of ink and the best shift beats
every shift more than 12 px away from it by at least MARGIN (a clear, single answer); others
are reported and left out.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from shapely.geometry import Point

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corners  # noqa: E402
import georef  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
INK = 105
CAP = 6.0
RADIUS = 300.0
MIN_ON = 0.6
MARGIN = 0.4


def samples(g, c, step_m=2.0):
    """Points every step_m along geometry g (lon/lat) within RADIUS of corner c, in meters."""
    out = []
    for line in getattr(g, 'geoms', [g]):
        xs, ys = line.xy
        mx, my = georef.to_m(list(xs), list(ys))
        for i in range(len(mx) - 1):
            a, b = np.array([mx[i], my[i]]), np.array([mx[i + 1], my[i + 1]])
            n = max(int(np.hypot(*(b - a)) / step_m), 1)
            for t in np.linspace(0, 1, n, endpoint=False):
                p = a + (b - a) * t
                if np.hypot(*(p - c)) <= RADIUS:
                    out.append(p)
    return np.array(out)


def main(scan, osm, gj, cj, outp, reach=40):
    reach = int(reach)
    t = json.load(open(gj))['transform']
    gray = np.asarray(Image.open(scan).convert('L'))
    ways = corners.load(osm)
    cand = json.load(open(cj))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import globalfit
    hood = globalfit.street_samples(osm, None, step=4.0)
    pts, rejected = [], []
    for lon, lat, lab, A, B in cand:
        cx, cy = georef.to_m([lon], [lat])
        c = np.array([cx[0], cy[0]])
        if corners.named(ways, A).is_empty or corners.named(ways, B).is_empty:
            rejected.append((lab, 'street not found'))
            continue
        S = hood[np.hypot(*(hood - c).T) <= RADIUS]
        uv = georef.inverse(t, np.vstack([S, c[None]]), guess=tuple(georef.inverse(t, c[None])[0]))
        P, C = uv[:-1], uv[-1]
        x0, y0 = int(P[:, 0].min()) - reach - 10, int(P[:, 1].min()) - reach - 10
        x1, y1 = int(P[:, 0].max()) + reach + 10, int(P[:, 1].max()) + reach + 10
        win = gray[max(y0, 0):y1, max(x0, 0):x1]
        dt = np.minimum(ndimage.distance_transform_edt(win >= INK), CAP)
        Q = P - [max(x0, 0), max(y0, 0)]
        best = None
        costs = np.full((2 * reach + 1, 2 * reach + 1), np.inf)
        for dy in range(-reach, reach + 1):
            for dx in range(-reach, reach + 1):
                q = np.round(Q + [dx, dy]).astype(int)
                ok = (q[:, 0] >= 0) & (q[:, 1] >= 0) & (q[:, 0] < dt.shape[1]) & (q[:, 1] < dt.shape[0])
                if ok.mean() < 0.95:
                    continue
                v = dt[q[ok, 1], q[ok, 0]]
                costs[dy + reach, dx + reach] = v.mean()
        k = np.unravel_index(np.argmin(costs), costs.shape)
        dy, dx = k[0] - reach, k[1] - reach
        q = np.round(Q + [dx, dy]).astype(int)
        on = float((dt[q[:, 1], q[:, 0]] <= 2).mean())
        yy, xx = np.mgrid[-reach:reach + 1, -reach:reach + 1]
        far = np.hypot(yy - dy, xx - dx) > 12
        margin = float(costs[far].min() - costs[k]) if far.any() else 0.0
        u, v = C[0] + dx, C[1] + dy
        row = [round(float(u), 1), round(float(v), 1), lon, lat, lab]
        info = f"{lab:42s} shift ({dx:+d},{dy:+d}) px  on-ink {on:.2f}  margin {margin:.2f}"
        if on >= MIN_ON and margin >= MARGIN and abs(dx) < reach and abs(dy) < reach:
            pts.append(row)
            print('ok  ', info)
        else:
            rejected.append((lab, info))
            print('drop', info)
    json.dump({'points': pts, 'rejected': rejected,
               'method': 'snapcp.py: OSM streets slid onto printed lines, chamfer on ink'}, open(outp, 'w'), indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:])
