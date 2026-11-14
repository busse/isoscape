"""Register a scanned map sheet to the ground.

The sheet's ink (its printed lines) is turned into a distance field: how far each pixel is
from the nearest line. Reference lines from today's data (city block outlines, and old
buildings that still stand) are dropped onto the sheet under a trial similarity transform;
the transform is good when they land on ink. A search over rotation, scale and position
(by FFT correlation), then a local refinement, finds the best one. The share of reference
points that land within 2 px of ink is reported as the fit's score."""
import json, math, sys
import numpy as np
from PIL import Image
from scipy import ndimage, optimize, signal
from geo import w2i, i2w, sim

CAP = 3.0


def ink_field(path, dark=105):
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.int16)
    v = im.max(2)
    ink = v < dark
    dt = ndimage.distance_transform_edt(~ink)
    return np.minimum(dt, CAP).astype(np.float32), im


def cost_at(dt, uv):
    return ndimage.map_coordinates(dt, [uv[:, 1], uv[:, 0]], order=1, cval=CAP)


def search(dt, pts, guess, search_px, thetas, scales):
    H, W = dt.shape
    r = int(search_px)
    pad = np.pad(dt, r, constant_values=CAP)
    best = None
    for th in thetas:
        for s in scales:
            uv = w2i((guess[0], guess[1], th, s), pts)
            q = np.round(uv).astype(int)
            keep = (q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H)
            if keep.sum() < 200:
                continue
            q = q[keep]
            qmin, qmax = q.min(0), q.max(0)
            K = np.zeros((qmax[1] - qmin[1] + 1, qmax[0] - qmin[0] + 1), np.float32)
            np.add.at(K, (q[:, 1] - qmin[1], q[:, 0] - qmin[0]), 1)
            out = signal.correlate(pad, K, mode='valid', method='fft')
            win = out[qmin[1]:qmin[1] + 2 * r + 1, qmin[0]:qmin[0] + 2 * r + 1] / len(q)
            j, i = np.unravel_index(np.argmin(win), win.shape)
            c = win[j, i]
            if best is None or c < best[0]:
                best = (c, (guess[0] + i - r, guess[1] + j - r, th, s))
    return best


def refine(dt, pts, p0):
    H, W = dt.shape
    uv0 = w2i(p0, pts)
    keep = (uv0[:, 0] >= 0) & (uv0[:, 0] < W) & (uv0[:, 1] >= 0) & (uv0[:, 1] < H)
    sub = pts[keep]
    sc = np.array([1, 1, 0.002, p0[3] * 0.002])
    f = lambda z: cost_at(dt, w2i(tuple(np.asarray(p0) + z * sc), sub)).mean()
    r = optimize.minimize(f, np.zeros(4), method='Nelder-Mead', options=dict(xatol=0.05, fatol=1e-4, maxiter=600))
    p = tuple(float(v) for v in np.asarray(p0) + r.x * sc)
    d = cost_at(dt, w2i(p, sub))
    return p, float(d.mean()), float((d <= 2).mean()), int(len(sub))


def register(path, pts, guess, search_m=90, dth=4, dscale=0.08, steps=(9, 9), field=None):
    dt, im = field if field is not None else ink_field(path)
    th0, s0 = guess[2], guess[3]
    thetas = th0 + np.radians(np.linspace(-dth, dth, steps[0]))
    scales = s0 * np.linspace(1 - dscale, 1 + dscale, steps[1])
    # coarse pass at a third of the resolution
    k = 3
    small = np.minimum(ndimage.minimum_filter(dt, size=k)[::k, ::k], CAP)
    g = (guess[0] / k, guess[1] / k, th0, s0 / k)
    c, p = search(small, pts[::2], g, search_m * s0 / k, thetas, scales / k)
    p = (p[0] * k, p[1] * k, p[2], p[3] * k)
    # second, finer pass around the winner
    thetas = p[2] + np.radians(np.linspace(-dth / 4, dth / 4, 5))
    scales = p[3] * np.linspace(1 - dscale / 4, 1 + dscale / 4, 5)
    c, p = search(dt, pts, p, 8 * p[3], thetas, scales)
    p, mean, inl, n = refine(dt, pts, p)
    return dict(params=p, cost=mean, inliers=inl, points=n), dt, im


def overlay(im, pts, params, out, extra=None, width=1400, thick=0, grid=False):
    """The sheet with the reference lines drawn over it in red (and extra in blue)."""
    o = im.astype(np.uint8).copy()
    H, W = o.shape[:2]
    for P, col in ((pts, (230, 0, 0)), (extra, (0, 60, 230))):
        if P is None:
            continue
        uv = np.round(w2i(params, P)).astype(int)
        k = (uv[:, 0] >= 1) & (uv[:, 0] < W - 1) & (uv[:, 1] >= 1) & (uv[:, 1] < H - 1)
        for du in range(-thick, thick + 1):
            for dv in range(-thick, thick + 1):
                o[np.clip(uv[k, 1] + dv, 0, H - 1), np.clip(uv[k, 0] + du, 0, W - 1)] = col
    img = Image.fromarray(o)
    if grid:
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        for g in range(0, max(W, H), 200):
            d.line([(g, 0), (g, H)], fill=(0, 140, 255), width=2); d.line([(0, g), (W, g)], fill=(0, 140, 255), width=2)
            d.text((g + 4, 4), str(g), fill=(0, 60, 200)); d.text((4, g + 4), str(g), fill=(0, 60, 200))
    img.thumbnail((width, width * 2))
    img.save(out)
