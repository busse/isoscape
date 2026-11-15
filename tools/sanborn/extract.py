"""Trace the buildings on georeferenced sheets: colored fills split by the printed party walls,
traced as polygons, carried to lon/lat, one GeoJSON per edition. Material from the color."""
import json, sys
import numpy as np
import cv2
from PIL import Image
from shapely.geometry import Polygon, MultiPoint, mapping
from shapely.ops import unary_union
from geo import i2w, to_ll
from material import classify, CLASSES

STOREYS = {'brick': 3, 'frame': 2, 'stone': 3, 'iron': 4, 'special': 3, 'fireproof': 6}


def trace(img, params, keep=None, min_m2=10, fireproof=False, tile=3000, overlap=400):
    """Big scans are read in overlapping tiles; a building is kept by the tile whose core holds
    its center, and only if it does not run off that tile."""
    Image.MAX_IMAGE_PIXELS = None
    src = Image.open(img).convert('RGB')
    W, H = src.size
    if W * H <= tile * tile * 1.5:
        return trace_window(np.asarray(src), params, (0, 0), (0, 0, W, H), keep, min_m2, fireproof)
    out = []
    for y0 in range(0, H, tile):
        for x0 in range(0, W, tile):
            box = (max(0, x0 - overlap), max(0, y0 - overlap), min(W, x0 + tile + overlap), min(H, y0 + tile + overlap))
            core = (x0, y0, min(W, x0 + tile), min(H, y0 + tile))
            out += trace_window(np.asarray(src.crop(box)), params, box[:2], core, keep, min_m2, fireproof, edges=(box, W, H))
    return out


def trace_window(im, params, off, core, keep, min_m2, fireproof, edges=None):
    cls, ink, _ = classify(im, fireproof)
    from geo import px_per_m
    s = px_per_m(params)
    mask = ((cls > 0) & (cls != 3)) | (cls == 3)
    mask = mask.astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    H, W = mask.shape
    if edges is None:
        b = int(0.02 * W)
        mask[:b] = 0; mask[-b:] = 0; mask[:, :b] = 0; mask[:, -b:] = 0
    if keep:
        k = np.zeros_like(mask)
        cv2.fillPoly(k, [np.array(keep, np.int32) - np.array(off, np.int32)], 1)
        mask &= k
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
    out = []
    px_m2 = 1 / (s * s)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] * px_m2 < min_m2:
            continue
        x, y, w, h = stats[i, :4]
        if edges is not None:
            (bx0, by0, bx1, by1), WW, HH = edges
            touches = (x == 0 and bx0 > 0) or (y == 0 and by0 > 0) or (x + w >= W and bx1 < WW) or (y + h >= H and by1 < HH)
            cx, cy = off[0] + x + w / 2, off[1] + y + h / 2
            if touches or not (core[0] <= cx < core[2] and core[1] <= cy < core[3]):
                continue
        comp = lab[y:y + h, x:x + w] == i
        votes = np.bincount(cls[y:y + h, x:x + w][comp], minlength=7)
        votes[0] = 0
        mat = CLASSES[int(votes.argmax())]
        if mat == 'stone' and stats[i, cv2.CC_STAT_AREA] * px_m2 > 1500:
            continue  # big blue: water, not a building
        sub = np.pad(comp.astype(np.uint8), 3)
        x, y = x - 3, y - 3
        # close over lettering and hatching inside the fill
        sub = cv2.morphologyEx(sub, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cs, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = max(cs, key=cv2.contourArea)
        filled = cv2.contourArea(c)
        if filled <= 0 or stats[i, cv2.CC_STAT_AREA] / filled < 0.55:
            continue  # an outline (a river bank, a canal wall), not a solid fill
        rect = cv2.minAreaRect(c)
        if filled >= 0.88 * rect[1][0] * rect[1][1]:
            c = cv2.boxPoints(rect).astype(float) + [x, y] + off  # near-rectangular: square it up
        else:
            c = cv2.approxPolyDP(c, 3.0, True)[:, 0, :].astype(float) + [x, y]
        c = c + off
        if len(c) < 3:
            continue
        xy = i2w(params, c)
        lon, lat = to_ll(xy[:, 0], xy[:, 1])
        poly = Polygon(np.stack([xy[:, 0], xy[:, 1]], 1)).buffer(0)
        if poly.is_empty or poly.area < min_m2:
            continue
        # thin strips (rails, fences drawn in color) are not buildings
        compact = poly.area / max(poly.length, 1e-6)
        if compact < 1.3 or (mat == 'stone' and compact < 2.5):
            continue
        out.append(dict(poly=poly, ll=list(zip(lon.round(7).tolist(), lat.round(7).tolist())), material=mat))
    return out


if __name__ == '__main__':
    edition, geofile, imgfmt, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    skip = set(sys.argv[5].split(',')) if len(sys.argv) > 5 else set()
    keeps = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else {}
    geo = json.load(open(geofile))
    feats, taken, cover = [], [], []
    for sh, g in sorted(geo.items(), key=lambda kv: (not kv[0].isdigit(), int(kv[0]) if kv[0].isdigit() else 0)):
        if sh in skip:
            continue
        bs = trace(imgfmt.format(sh=int(sh) if sh.isdigit() else sh), g['params'], keeps.get(sh), fireproof=int(edition) >= 1895)
        added = 0
        for bd in bs:
            c = bd['poly'].representative_point()
            if any(t.contains(c) for t in taken):
                continue
            taken.append(bd['poly']); added += 1
            feats.append({'type': 'Feature', 'properties': {'edition': int(edition), 'sheet': sh, 'material': bd['material'],
                          'storeys': STOREYS[bd['material']], 'area': round(bd['poly'].area, 1)},
                          'geometry': {'type': 'Polygon', 'coordinates': [bd['ll'] + [bd['ll'][0]]]}})
        if bs:
            hull = MultiPoint([b['poly'].centroid for b in bs]).convex_hull.buffer(25)
            cover.append(hull)
        print(sh, len(bs), 'added', added, flush=True)
    cov = unary_union(cover)
    polys = [cov] if cov.geom_type == 'Polygon' else list(cov.geoms)
    for p in polys:
        x, y = p.exterior.xy
        lon, lat = to_ll(np.array(x), np.array(y))
        feats.append({'type': 'Feature', 'properties': {'edition': int(edition), 'coverage': True},
                      'geometry': {'type': 'Polygon', 'coordinates': [list(zip(lon.round(7).tolist(), lat.round(7).tolist()))]}})
    json.dump({'type': 'FeatureCollection', 'edition': int(edition), 'features': feats}, open(out, 'w'))
    print('buildings', sum(1 for f in feats if not f['properties'].get('coverage')))
