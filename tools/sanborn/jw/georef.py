"""Fit the Jackson Ward sheets (Sanborn 1925 vol. 3 as republished in 1952) to the ground.

    python3 georef.py cps1952.json "<50% scan path with {sh}>" geo1952.json [sheet ...]

Where the corners that survive today lie along one street, the scale is read off the sheet's
own scale bar instead ("_bar": {sheet: meters per full-resolution pixel}) and only rotation and
shift are fitted.

Control points in cps1952.json are street-corner centers read by eye off the full-resolution
scan ([u, v, lon, lat, label], u and v in full-resolution pixels), their ground positions the
crossing of today's OpenStreetMap center lines. Each sheet is fitted with a similarity (scale
free: the scans differ a little in size) to the corners, then refined against today's city
block outlines: each outline point is pulled toward the sheet's nearest ink, the pull capped at
3 px (0.5 m) so blocks rebuilt or cut since 1952 do not drag the fit. The refined fit is kept
only if it moves no corner more than 4 m from where it was read. The residuals reported are
each corner's distance, in meters, from where the kept fit puts it."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from geo import to_m, fit_sim, w2i, px_per_m
from register import refine, CAP
from PIL import Image
from scipy import ndimage
from ref import blocks

BLOCKS = os.path.join(os.path.dirname(__file__), '../../../data/sanborn/blocks-jw.json')

def ink_dt(img):
    """Distance to the nearest printed line; ink read relative to the paper (these scans print
    their lines in a brownish gray, lighter than the earlier editions')."""
    v = np.asarray(Image.open(img).convert('RGB')).max(2).astype(float)
    ink = v < 0.62 * np.percentile(v, 90)
    return np.minimum(ndimage.distance_transform_edt(~ink), CAP).astype(np.float32)

def fit_sheet(rows, img, bar=None):
    uv = np.array([r[:2] for r in rows], float) / 2  # full-resolution pixels -> 50% scan
    x, y = to_m([r[2] for r in rows], [r[3] for r in rows]); xy = np.stack([x, y], 1)
    if bar:
        # the scale read off the sheet's own scale bar (m per full-resolution px): corners that
        # survive today all lie along one street, so only rotation and shift are fitted
        from rigid import fit_rigid
        p0 = fit_rigid(xy, uv, 1 / (2 * bar))
    else:
        p0 = fit_sim(xy, uv)
    res0 = np.hypot(*(w2i(p0, xy) - uv).T) / px_per_m(p0)
    dt = ink_dt(img)
    pts = blocks(BLOCKS, 1.0)
    H, W = dt.shape
    q = w2i(p0, pts); k = (q[:, 0] > 0) & (q[:, 0] < W) & (q[:, 1] > 0) & (q[:, 1] < H)
    p1, cost, inl, n = refine(dt, pts[k], p0)
    res1 = np.hypot(*(w2i(p1, xy) - uv).T) / px_per_m(p1)
    keep = p1 if res1.max() <= 4.0 else p0
    res = res1 if keep is p1 else res0
    return dict(params=[float(v) for v in keep], refined=keep is p1, corners=[r[4] for r in rows],
                resid_m=[round(float(v), 1) for v in res], resid_corners_only=[round(float(v), 1) for v in res0],
                m_per_px=round(1 / px_per_m(keep), 4), block_inliers=round(inl, 2), block_points=n)

if __name__ == '__main__':
    cps, fmt, out = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3]
    bars = cps.pop('_bar', {})
    want = sys.argv[4:] or list(cps)
    geo = json.load(open(out)) if os.path.exists(out) else {}
    for sh in want:
        g = fit_sheet(cps[sh], fmt.format(sh=sh), bars.get(sh))
        if bars.get(sh): g['scale_bar_m_per_px_full'] = bars[sh]
        geo[sh] = g
        print(sh, 'refined' if g['refined'] else 'corners', 'm/px', g['m_per_px'], 'resid', g['resid_m'], 'corners-only', g['resid_corners_only'], 'block inliers', g['block_inliers'])
    json.dump(geo, open(out, 'w'), indent=1)
