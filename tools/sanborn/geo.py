"""Shared geometry for the Sanborn tools: a local metric frame, the reference lines a sheet
is registered against, and similarity transforms between sheet pixels and the ground."""
import json, math
import numpy as np

LON0, LAT0 = -77.4268, 37.5340
KX = 111_320 * math.cos(math.radians(LAT0))
KY = 110_574


def to_m(lon, lat):
    return (np.asarray(lon) - LON0) * KX, (np.asarray(lat) - LAT0) * KY


def to_ll(x, y):
    return np.asarray(x) / KX + LON0, np.asarray(y) / KY + LAT0


def rings_of(geom):
    t, c = geom['type'], geom['coordinates']
    if t == 'Polygon':
        return c
    if t == 'MultiPolygon':
        return [r for p in c for r in p]
    if t == 'LineString':
        return [c]
    if t == 'MultiLineString':
        return c
    return []


def sample_lines(lines, step=1.0):
    """Points every `step` metres along polylines given in metres."""
    out = []
    for pts in lines:
        pts = np.asarray(pts, float)
        for a, b in zip(pts[:-1], pts[1:]):
            d = math.hypot(*(b - a))
            n = max(1, int(d / step))
            t = np.arange(n) / n
            out.append(a + (b - a) * t[:, None])
    return np.concatenate(out) if out else np.zeros((0, 2))


def load_lines(path):
    """Block outlines (or any polygons/lines) from GeoJSON, as metre polylines."""
    fc = json.load(open(path))
    lines = []
    for f in fc['features']:
        if not f.get('geometry'):
            continue
        for r in rings_of(f['geometry']):
            r = np.asarray(r)
            x, y = to_m(r[:, 0], r[:, 1])
            lines.append(np.stack([x, y], 1))
    return lines


def sim(params):
    """World metres -> image pixels: u,v = s*R(th)*(x,-y) + (tu,tv)."""
    tu, tv, th, s = params
    c, si = math.cos(th), math.sin(th)
    return np.array([[s * c, -s * si], [s * si, s * c]]), np.array([tu, tv])


def affine(params):
    """Six numbers (a, b, c, d, tu, tv): u = a*x' + b*y' + tu, v = c*x' + d*y' + tv, with y' = -y."""
    a, b, c, d, tu, tv = params
    return np.array([[a, b], [c, d]]), np.array([tu, tv])


def mat(params):
    return affine(params) if len(params) == 6 else sim(params)


def _warp(params):
    """A rubber sheet: an affine plus thin-plate corrections that make each control point exact."""
    from scipy.interpolate import RBFInterpolator
    key = id(params)
    if key not in _WARPS:
        A = params['affine']; xy = np.asarray(params['xy'], float); uv = np.asarray(params['uv'], float)
        du = uv - _w2i_lin(A, xy)
        dx = xy - _i2w_lin(A, uv)
        _WARPS[key] = (RBFInterpolator(xy, du, kernel='thin_plate_spline', smoothing=1.0),
                       RBFInterpolator(uv, dx, kernel='thin_plate_spline', smoothing=1.0))
    return _WARPS[key]


_WARPS = {}


def w2i(params, xy):
    if isinstance(params, dict):
        f, _ = _warp(params)
        return _w2i_lin(params['affine'], xy) + f(np.asarray(xy, float))
    return _w2i_lin(params, xy)


def i2w(params, uv):
    if isinstance(params, dict):
        _, g = _warp(params)
        uv = np.asarray(uv, float)
        return _i2w_lin(params['affine'], uv) + g(uv)
    return _i2w_lin(params, uv)


def _w2i_lin(params, xy):
    M, t = mat(params)
    q = np.stack([xy[:, 0], -xy[:, 1]], 1)
    return q @ M.T + t


def _i2w_lin(params, uv):
    M, t = mat(params)
    q = (np.asarray(uv, float) - t) @ np.linalg.inv(M).T
    return np.stack([q[:, 0], -q[:, 1]], 1)


def fit_sim(xy, uv):
    """Least-squares similarity from world points to image points (Umeyama, no reflection)."""
    xy = np.asarray(xy, float); uv = np.asarray(uv, float)
    a = np.stack([xy[:, 0], -xy[:, 1]], 1)
    ma, mb = a.mean(0), uv.mean(0)
    A, B = a - ma, uv - mb
    C = B.T @ A / len(a)
    U, S, Vt = np.linalg.svd(C)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1, d])
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / (A ** 2).sum(1).mean()
    th = math.atan2(R[1, 0], R[0, 0])
    t = mb - s * (R @ ma)
    return (t[0], t[1], th, s)


def fit_affine(xy, uv):
    """Least-squares affine from world points to image points: for small-scale key maps, whose
    drawing stretches a little differently along and across the grid."""
    a = np.stack([xy[:, 0], -xy[:, 1], np.ones(len(xy))], 1)
    cu, *_ = np.linalg.lstsq(a, uv[:, 0], rcond=None)
    cv, *_ = np.linalg.lstsq(a, uv[:, 1], rcond=None)
    return (cu[0], cu[1], cv[0], cv[1], cu[2], cv[2])


def px_per_m(params):
    if isinstance(params, dict):
        params = params['affine']
    M, _ = mat(params)
    return float(np.sqrt(abs(np.linalg.det(M))))
