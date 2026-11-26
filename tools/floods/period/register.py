"""Register an evidence crop to today's streets, from many control windows.

    python3 tools/floods/period/register.py <area> <image> [overlay.png]

Each control window is a 360 m square on a 300 m grid with at least 400 m of today's street
center lines (OSM) in it. In each, the shift that best puts the lines on pavement is found by
search (-36 to +36 m, 1 m steps): pavement is told by its contrast with the ground 3 m beyond
the street's edge on both sides (1974: streets print light; later photos: asphalt reads dark).
A window counts as a control point when its best shift stands clear of the second-best
cluster. A shift growing linearly across the crop (six numbers: a translation and a stretch or
turn) is fitted to the control points by least squares (a translation only with fewer than 12 clear points), dropping points more than 3 MADs (and
4 m) off, and written into the crop's JSON with every point and its residual.
"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
from common import Crop, streets, WIDTH

# 1974: pavement prints lighter than its sides. Later photos: asphalt is dark, but so are the
# shadows along one curb, which pull a darkness fit off the street; there the line is put where
# the street's two sides look most alike (symmetry, 0).
SIGN = {'1974': 1.0}
STEP, HALF, SEARCH = 300.0, 180.0, 36
MIN_LINEAR = 12


def samples(crop, bbox):
    """Points every 2 m along today's streets, with the unit normal and the street's width, in crop pixels."""
    pts = []
    for kind, lo, la in streets(bbox):
        c, r = crop.pixel(lo, la, reg=(0,) * 6)
        for i in range(len(c) - 1):
            dx, dy = c[i + 1] - c[i], r[i + 1] - r[i]
            L = np.hypot(dx, dy)
            if L < 1e-6:
                continue
            n = max(2, int(L * crop.px * crop.ground / 2))
            f = np.linspace(0, 1, n, endpoint=False)
            for t in f:
                pts.append((c[i] + t * dx, r[i] + t * dy, -dy / L, dx / L, WIDTH[kind]))
    return np.array(pts)


def window_shift(crop, P, sign):
    """Best shift (ground meters, east and north) for the points P, and how clearly it wins."""
    g = crop.gray
    H, W = g.shape
    m = 1.0 / (crop.px * crop.ground)  # pixels per ground meter
    shifts = np.arange(-SEARCH, SEARCH + 1)
    best = np.full((len(shifts), len(shifts)), np.nan)
    side = (P[:, 4] / 2 + 3) * m
    for i, sx in enumerate(shifts):
        for j, sy in enumerate(shifts):
            cx, cy = P[:, 0] + sx * m, P[:, 1] - sy * m
            vals = []
            for off in (0.0, side, -side):
                xs = np.round(cx + P[:, 2] * off).astype(int)
                ys = np.round(cy + P[:, 3] * off).astype(int)
                ok = (xs >= 0) & (ys >= 0) & (xs < W) & (ys < H)
                v = np.full(len(P), np.nan)
                v[ok] = g[ys[ok], xs[ok]]
                vals.append(v)
            if sign != 0:
                d = vals[0] - (vals[1] + vals[2]) / 2
                best[j, i] = sign * np.nanmean(d)
            else:
                # Symmetry: the street's two sides, 2 and 4 m out from the line, alike.
                diffs = []
                for off in (2 * m, 4 * m):
                    a = []
                    for sgn in (1, -1):
                        xs = np.clip(np.round(cx + sgn * P[:, 2] * off).astype(int), 0, W - 1)
                        ys = np.clip(np.round(cy + sgn * P[:, 3] * off).astype(int), 0, H - 1)
                        a.append(g[ys, xs])
                    diffs.append(np.abs(a[0] - a[1]))
                best[j, i] = -np.nanmean(diffs)
    k = np.nanargmax(best)
    j, i = np.unravel_index(k, best.shape)
    top = best[j, i]
    # The best score at least 6 m away from the winner: a clear peak beats it well.
    far = best.copy()
    yy, xx = np.mgrid[0:len(shifts), 0:len(shifts)]
    far[np.hypot(yy - j, xx - i) < 6] = np.nan
    second = np.nanmax(far)
    return shifts[i], shifts[j], float(top), float(second)


def main(area, key, overlay=None):
    crop = Crop(area, key)
    sign = SIGN.get(key, 0.0)
    H, W = crop.gray.shape
    # The crop's box in lon/lat, from its corners.
    from pyproj import Transformer
    back = Transformer.from_crs(crop.meta['crs'], 'EPSG:4326', always_xy=True)
    t = crop.t
    lo, la = back.transform([t[0], t[0] + t[1] * W], [t[3] + t[5] * H, t[3]])
    bbox = (lo[0], la[0], lo[1], la[1])
    P = samples(crop, bbox)
    m = 1.0 / (crop.px * crop.ground)
    pts = []
    gx = np.arange(HALF * m, W - HALF * m + 1, STEP * m)
    gy = np.arange(HALF * m, H - HALF * m + 1, STEP * m)
    for cx in gx:
        for cy in gy:
            sel = (np.abs(P[:, 0] - cx) < HALF * m) & (np.abs(P[:, 1] - cy) < HALF * m)
            if sel.sum() < 200:  # 400 m of street
                continue
            sx, sy, top, second = window_shift(crop, P[sel], sign)
            clear = (top - second) / max(1e-6, abs(top))
            pts.append(dict(col=float(cx), row=float(cy), dx=float(sx), dy=float(sy), score=round(top, 2), clear=round(clear, 3), n=int(sel.sum())))
    use = [p for p in pts if p['clear'] >= 0.15 and abs(p['dx']) < SEARCH and abs(p['dy']) < SEARCH]
    # Fit in ground meters, u, v in km from the crop's center.
    # Fewer than MIN_LINEAR clear points: a translation only (the stretch would be guessed).
    linear = len(use) >= MIN_LINEAR
    def design(ps):
        u = np.array([(p['col'] - W / 2) / m / 1000 for p in ps]); v = np.array([-(p['row'] - H / 2) / m / 1000 for p in ps])
        return np.stack([np.ones_like(u), u, v], 1) if linear else np.stack([np.ones_like(u), 0 * u, 0 * v], 1)
    keep = list(use)
    for _ in range(5):
        A = design(keep)
        ex, *_ = np.linalg.lstsq(A, np.array([p['dx'] for p in keep]), rcond=None)
        ey, *_ = np.linalg.lstsq(A, np.array([p['dy'] for p in keep]), rcond=None)
        A = design(use)
        res = np.hypot(A @ ex - [p['dx'] for p in use], A @ ey - [p['dy'] for p in use])
        mad = np.median(np.abs(res - np.median(res))) + 1e-6
        nk = [p for p, r in zip(use, res) if r <= max(4.0, np.median(res) + 3 * mad)]
        if len(nk) == len(keep):
            break
        keep = nk
    A = design(pts)
    for p, rx, ry in zip(pts, A @ ex, A @ ey):
        p['residual'] = round(float(np.hypot(rx - p['dx'], ry - p['dy'])), 2)
        p['used'] = p in keep
    rk = [p['residual'] for p in pts if p['used']]
    # Stored in CRS meters (ground meters divided by the CRS's ground factor).
    g = crop.ground
    affine = [float(ex[0] / g), float(ex[1]), float(ex[2]), float(ey[0] / g), float(ey[1]), float(ey[2])]
    crop.meta['registration'] = dict(
        method='shift growing linearly across the crop, fitted by least squares to control windows on today\'s OSM street center lines (register.py)',
        affine=affine, ground_shift_at_center_m=[round(float(ex[0]), 2), round(float(ey[0]), 2)],
        control_points=len(pts), used=len(keep), rms_m=round(float(np.sqrt(np.mean(np.square(rk)))), 2), max_m=round(float(max(rk)), 2), points=pts)
    json.dump(crop.meta, open(crop.meta_path, 'w'), indent=1)
    print(area, key, 'windows', len(pts), 'clear', len(use), 'used', len(keep), 'shift at center (m E, N)', round(ex[0], 1), round(ey[0], 1),
          'gradient (m/km)', np.round(ex[1:], 2), np.round(ey[1:], 2), 'rms', crop.meta['registration']['rms_m'], 'max', crop.meta['registration']['max_m'])
    if overlay:
        crop = Crop(area, key)
        img = crop.img.convert('RGB')
        d = ImageDraw.Draw(img)
        for kind, lo, la in streets(bbox):
            c, r = crop.pixel(lo, la)
            d.line(list(zip(c, r)), fill=(255, 0, 200), width=2)
        for p in pts:
            col = (0, 220, 0) if p['used'] else (255, 160, 0)
            d.ellipse([p['col'] - 9, p['row'] - 9, p['col'] + 9, p['row'] + 9], outline=col, width=3)
            d.text((p['col'] + 11, p['row'] - 6), f"{p['dx']:+.0f},{p['dy']:+.0f} r{p['residual']:.1f}", fill=col)
        img.thumbnail((2400, 2400))
        img.save(overlay, quality=82)


if __name__ == '__main__':
    main(*sys.argv[1:])
