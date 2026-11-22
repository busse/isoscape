"""Fit the scan to the ground from street-corner control points, and report the error.

    python3 georef.py <cps.json> <georef.json>

cps.json: {"points": [[u, v, lon, lat, "label"], ...]} with u, v in scan pixels (read off the
scan) and lon, lat from OpenStreetMap intersections (corners.py). The ground is a local plane
in meters (equirectangular about 37.55 N, as in the redlining story's measure.py).

Fits a similarity (scale, rotation, shift), an affine, and a second-order polynomial, each by
least squares, and reports for each the RMS and largest residual in meters, both on the fitting
points and leave-one-out (each point predicted by a fit without it). The affine is written as
the transform used, unless the polynomial's leave-one-out RMS is lower by more than a meter.
"""
import json
import math
import sys

import numpy as np

LAT0 = 37.55
KX = 111320 * math.cos(math.radians(LAT0))
KY = 111132


def to_m(lon, lat):
    return (np.asarray(lon) + 77.46) * KX, (np.asarray(lat) - LAT0) * KY


def to_ll(x, y):
    return np.asarray(x) / KX - 77.46, np.asarray(y) / KY + LAT0


def design(uv, kind):
    u, v = uv[:, 0] / 1000.0, uv[:, 1] / 1000.0
    one = np.ones_like(u)
    if kind == 'affine':
        return np.stack([one, u, v], 1)
    if kind == 'poly2':
        return np.stack([one, u, v, u * u, u * v, v * v], 1)
    raise ValueError(kind)


def fit(uv, xy, kind):
    if kind == 'similarity':
        # x = a u - b v + c ; y = b u + a v + d  (v grows down, so flip it first)
        u, v = uv[:, 0] / 1000.0, -uv[:, 1] / 1000.0
        A = np.zeros((2 * len(u), 4))
        A[0::2] = np.stack([u, -v, np.ones_like(u), np.zeros_like(u)], 1)
        A[1::2] = np.stack([v, u, np.zeros_like(u), np.ones_like(u)], 1)
        b = xy.reshape(-1)
        p = np.linalg.lstsq(A, b, rcond=None)[0]
        return {'kind': kind, 'p': p.tolist()}
    D = design(uv, kind)
    cx = np.linalg.lstsq(D, xy[:, 0], rcond=None)[0]
    cy = np.linalg.lstsq(D, xy[:, 1], rcond=None)[0]
    return {'kind': kind, 'cx': cx.tolist(), 'cy': cy.tolist()}


def apply(t, uv):
    uv = np.asarray(uv, float).reshape(-1, 2)
    if t['kind'] == 'similarity':
        a, b, c, d = t['p']
        u, v = uv[:, 0] / 1000.0, -uv[:, 1] / 1000.0
        return np.stack([a * u - b * v + c, b * u + a * v + d], 1)
    D = design(uv, t['kind'])
    return np.stack([D @ np.array(t['cx']), D @ np.array(t['cy'])], 1)


def inverse(t, xy, guess=(5000, 4000)):
    """Ground meters to scan pixels, by Newton steps on the forward transform."""
    xy = np.asarray(xy, float).reshape(-1, 2)
    uv = np.tile(np.array(guess, float), (len(xy), 1))
    for _ in range(30):
        f = apply(t, uv)
        e = 0.5
        J = np.stack([(apply(t, uv + [e, 0]) - f) / e, (apply(t, uv + [0, e]) - f) / e], 2)
        uv = uv - np.linalg.solve(J, (f - xy)[..., None])[..., 0]
    return uv


def report(pts):
    uv = np.array([p[:2] for p in pts], float)
    x, y = to_m([p[2] for p in pts], [p[3] for p in pts])
    xy = np.stack([x, y], 1)
    out = {}
    for kind in ('similarity', 'affine', 'poly2'):
        t = fit(uv, xy, kind)
        r = np.hypot(*(apply(t, uv) - xy).T)
        loo = []
        for i in range(len(pts)):
            m = np.arange(len(pts)) != i
            ti = fit(uv[m], xy[m], kind)
            loo.append(float(np.hypot(*(apply(ti, uv[i:i + 1]) - xy[i:i + 1]).T)[0]))
        out[kind] = {'t': t, 'res': r.tolist(), 'loo': loo,
                     'rms': float(np.sqrt((r ** 2).mean())), 'max': float(r.max()),
                     'loo_rms': float(np.sqrt((np.array(loo) ** 2).mean())), 'loo_max': float(max(loo))}
    return out


if __name__ == '__main__':
    cps = json.load(open(sys.argv[1]))
    pts = cps['points']
    out = report(pts)
    for k, o in out.items():
        print(f"{k:10s} n={len(pts)} rms {o['rms']:.1f} m  max {o['max']:.1f} m   leave-one-out rms {o['loo_rms']:.1f} m  max {o['loo_max']:.1f} m")
    use = 'affine'
    if out['poly2']['loo_rms'] < out['affine']['loo_rms'] - 1.0 and len(pts) >= 10:
        use = 'poly2'
    t = out[use]['t']
    if out['similarity']['t']:
        a, b = out['similarity']['t']['p'][:2]
        print(f"similarity: {math.hypot(a, b) / 1000:.4f} m per px, rotation {math.degrees(math.atan2(b, a)):.2f} deg")
    print('using', use)
    print(f"{'point':40s} {'res m':>7s} {'loo m':>7s}")
    for p, r, l in zip(pts, out[use]['res'], out[use]['loo']):
        print(f"{p[4]:40s} {r:7.1f} {l:7.1f}")
    json.dump({'use': use, 'transform': t, 'fits': {k: {kk: vv for kk, vv in o.items() if kk != 't'} | {'t': o['t']} for k, o in out.items()},
               'points': pts, 'lat0': LAT0}, open(sys.argv[2], 'w'), indent=1)
