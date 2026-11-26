#!/usr/bin/env python3
"""The surface watershed draining to the low ground of Shockoe Bottom, from a 3DEP DEM.

    python3 tools/floods/rain/watershed.py DEM.npy OUT.geojson [--box WEST,SOUTH,EAST,NORTH]

Dev tool (numpy, scipy, shapely). The DEM is the 3DEP exportImage of the box
-77.52..-77.37 E, 37.515..37.66 N at 0.0001 degree pixels (about 9 by 11 m), asked for with
pixels square in degrees so the image covers exactly the box (see `servedBox` in
src/dem-sources.ts). The URL is in rain.json.

Method:
  1. Priority-flood from the grid's edge (Barnes et al. 2014): every cell is reached from its
     lowest neighbor already reached, so pits and flats are filled and every cell gets one
     downhill (or level) receiver. Eight neighbors.
  2. The target is the low ground of the Bottom: cells under 8 m (26 ft) NAVD88 within 400 m of
     17th and Main (37.5339 N, 77.4304 W) and north of the floodwall line (37.5310 N).
  3. The watershed is every cell whose chain of receivers enters the target.
This is the land surface only. Shockoe Creek runs in a pipe, and the combined sewers cross
ridges, so the city's sewershed (about 8,000 acres) is not the same shape.
"""
import heapq
import json
import sys

import numpy as np


def main():
    dem_path, out = sys.argv[1], sys.argv[2]
    box_ = [-77.52, 37.515, -77.37, 37.66]
    if "--box" in sys.argv:
        box_ = [float(v) for v in sys.argv[sys.argv.index("--box") + 1].split(",")]
    west, south, east, north = box_
    z = np.load(dem_path).astype(np.float64)
    h, w = z.shape
    dlat, dlon = (north - south) / h, (east - west) / w
    z = np.where(np.isfinite(z), z, np.nanmax(z))
    lat = north - (np.arange(h) + 0.5) * dlat
    lon = west + (np.arange(w) + 0.5) * dlon

    # priority-flood
    filled = z.copy()
    rec = np.full(h * w, -1, dtype=np.int64)
    seen = np.zeros(h * w, dtype=bool)
    pq = []
    for y in range(h):
        for x in (0, w - 1):
            i = y * w + x
            heapq.heappush(pq, (z[y, x], i))
            seen[i] = True
    for x in range(1, w - 1):
        for y in (0, h - 1):
            i = y * w + x
            heapq.heappush(pq, (z[y, x], i))
            seen[i] = True
    flat = filled.ravel()
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    order = []
    while pq:
        e, i = heapq.heappop(pq)
        order.append(i)
        y, x = divmod(i, w)
        for dy, dx in nb:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                j = yy * w + xx
                if not seen[j]:
                    seen[j] = True
                    if flat[j] < e:
                        flat[j] = e
                    rec[j] = i
                    heapq.heappush(pq, (flat[j], j))
    filled = flat.reshape(h, w)

    # target: the Bottom's low ground
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    dy_m = (LA - 37.5339) * 110574
    dx_m = (LO + 77.4304) * 111320 * np.cos(np.radians(37.53))
    target = (z < 8.0) & (np.hypot(dx_m, dy_m) < 400) & (LA > 37.5310)
    inside = target.ravel().copy()
    # process in flood order: a cell is inside if its receiver is inside (receivers come first)
    for i in order:
        r = rec[i]
        if r >= 0 and inside[r]:
            inside[i] = True
    ws = inside.reshape(h, w)

    cell_area = (dlat * 110574) * (dlon * 111320 * np.cos(np.radians(lat)))[:, None]
    area_m2 = float((ws * cell_area).sum())
    edge_touch = bool(ws[0, :].any() or ws[-1, :].any() or ws[:, 0].any() or ws[:, -1].any())

    # polygon: union of cells, simplified
    from shapely.geometry import box, mapping
    from shapely.ops import unary_union
    from scipy import ndimage
    lab, n = ndimage.label(ws)
    sizes = ndimage.sum(ws, lab, range(1, n + 1))
    keep = lab == (1 + int(np.argmax(sizes)))
    rows = []
    for y in range(h):
        xs = np.where(keep[y])[0]
        if len(xs) == 0:
            continue
        # runs
        br = np.where(np.diff(xs) > 1)[0]
        starts = np.r_[xs[0], xs[br + 1]]
        ends = np.r_[xs[br], xs[-1]]
        for a, b in zip(starts, ends):
            rows.append(box(west + a * dlon, north - (y + 1) * dlat, west + (b + 1) * dlon, north - y * dlat))
    poly = unary_union(rows).buffer(0)
    poly = poly.simplify(0.00008, preserve_topology=True)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda p: p.area)
    poly = type(poly)(poly.exterior)  # drop pinholes
    np.save(out.replace(".geojson", "-mask.npy"), keep)
    feat = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": mapping(poly), "properties": {
        "name": "Shockoe Bottom surface watershed (land surface, from 3DEP; not the sewershed)",
        "area_km2": round(area_m2 / 1e6, 2), "area_acres": round(area_m2 / 4046.856), "touches_dem_edge": edge_touch,
        "target_cells": int(target.sum()), "dem": f"3DEP, box {box_}, {w} x {h} cells",
        "method": "priority-flood receivers, eight neighbors, upstream of the Bottom's ground under 8 m within 400 m of 17th and Main"}}]}
    json.dump(feat, open(out, "w"))
    ys, xs = np.where(keep)
    print(json.dumps({"area_km2": area_m2 / 1e6, "acres": area_m2 / 4046.856, "touches_edge": edge_touch,
                      "lat_range": [float(lat[ys.max()]), float(lat[ys.min()])],
                      "lon_range": [float(lon[xs.min()]), float(lon[xs.max()])],
                      "max_elev_m": float(z[keep].max()), "min_elev_m": float(z[keep].min())}))


if __name__ == "__main__":
    main()
