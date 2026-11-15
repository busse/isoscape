"""Snap eyeballed control points: around each corner, slide today's block outlines (a 120 m
patch) over the sheet's ink by up to `reach` meters, keep the best shift, and refit. A local
patch is small enough to carry the corner's own shape, so the grid's repetition cannot fool it."""
import json, sys
import numpy as np
from scipy import ndimage
from geo import to_m, fit_affine, fit_sim, w2i, px_per_m
from ref import blocks
from register import ink_field

def snap(img, rows, kind='affine', reach=14.0, patch=120.0, cap=6.0, rounds=2):
    dt, _ = ink_field(img)
    dt = np.minimum(dt, cap)
    pts = blocks('../../data/sanborn/blocks.json', 0.5)
    uv = np.array([r[:2] for r in rows], float)
    x, y = to_m([r[2] for r in rows], [r[3] for r in rows]); xy = np.stack([x, y], 1)
    fit = fit_affine if kind == 'affine' and len(rows) >= 4 else fit_sim
    p = fit(xy, uv)
    for _ in range(rounds):
        s = px_per_m(p)
        new = []
        for k in range(len(rows)):
            near = pts[np.hypot(*(pts - xy[k]).T) < patch]
            if len(near) < 50:
                new.append(uv[k]); continue
            base = w2i(p, near)
            best = None
            r = int(reach * s)
            for du in range(-r, r + 1, 2):
                for dv in range(-r, r + 1, 2):
                    c = ndimage.map_coordinates(dt, [base[:, 1] + dv, base[:, 0] + du], order=0, cval=cap).mean()
                    if best is None or c < best[0]:
                        best = (c, du, dv)
            pk = w2i(p, xy[k:k + 1])[0]
            new.append(pk + [best[1], best[2]])
        uv = np.array(new)
        p = fit(xy, uv)
    res = np.hypot(*(w2i(p, xy) - uv).T) / px_per_m(p)
    return p, res, xy, uv

if __name__ == '__main__':
    cps, img, out, key = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3], sys.argv[4]
    p, res, xy, uv = snap(img, cps[key])
    print('m/px', round(1 / px_per_m(p), 4), 'resid', res.round(1))
    g = {}
    try: g = json.load(open(out))
    except Exception: pass
    warp = len(xy) >= 6
    g[key] = {'params': {'affine': [float(v) for v in p], 'xy': xy.tolist(), 'uv': uv.tolist()} if warp else [float(v) for v in p],
              'resid_m': res.round(1).tolist()}
    json.dump(g, open(out, 'w'))
