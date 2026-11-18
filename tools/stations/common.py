"""Helpers shared by the station models (broad_street.py, main_street.py): local frames in
meters about a station's center, lon/lat conversion as region.ts does it, and line smoothing."""

import math

KY = 110_574  # meters per degree of latitude, as region.ts uses


def unit(bearing):
    """The unit vector (east, north) of a compass bearing in degrees."""
    r = math.radians(bearing)
    return (math.sin(r), math.cos(r))


def lonlat_of(lon0, lat0):
    """A function from meters (east, north) about (lon0, lat0) to [lon, lat], rounded to 1e-7."""
    kx = 111_320 * math.cos(math.radians(lat0))

    def lonlat(p):
        return [round(lon0 + p[0] / kx, 7), round(lat0 + p[1] / KY, 7)]
    return lonlat


def chaikin(pts, n=3):
    """Chaikin's corner cutting, n rounds, keeping the ends."""
    for _ in range(n):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            out += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]), (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        out.append(pts[-1])
        pts = out
    return pts


def densify(pts, step):
    """Points no more than `step` meters apart along a polyline."""
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        d = math.dist(p, q)
        k = max(1, int(d // step))
        out += [(p[0] + (q[0] - p[0]) * i / k, p[1] + (q[1] - p[1]) * i / k) for i in range(1, k + 1)]
    return out
