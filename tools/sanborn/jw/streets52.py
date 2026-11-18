"""Find the street center lines printed on the 1952 sheets, inside the highway's corridor, where
today's streets do not run: the streets the Turnpike took.

    python3 streets52.py "<50% scan path with {sh}>" geo1952.json highway-footprint.geojson \
        osm-jw.json history/jackson-ward.json out.geojson [sheet ...]

On a Sanborn sheet the blocks are closed outlines and the streets are the paper between them.
The printed lines are found as in trace52.py (a black-hat of 7 px on the 50% scan, plus anything
dark); every ink piece less than 60 px (9 m) across is dropped, which takes out the lettering,
house numbers, the dashes of pipe lines and the hydrant marks, and leaves the long lines of the
block outlines. The paper left is split into regions; the largest is the street space (it runs
out to the sheet's margins). Its center line is its skeleton, kept where the street is no more
than 2 x 13 m wide (the margins and open lots are wider). Each sheet's skeleton is carried to the
ground by the sheet's fit (geo1952.json).

The pieces kept: inside the corridor polygon grown by 25 m (to reach the corners just outside it),
more than 10 m from any street in today's OpenStreetMap that the 1952 scene draws (not the
motorway or its ramps) and from the lost streets already curated in the history, and longer
than 25 m. Where two sheets overlap, the first sheet listed wins. The pieces are simplified to
1.5 m. Out: GeoJSON lines with the sheet each came from, for looking at against the sheets and
for naming; history features are written from them by streets52_features.py."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np, cv2
from PIL import Image
from skimage.morphology import skeletonize
from shapely.geometry import LineString, MultiLineString, shape, mapping
from shapely.ops import unary_union, transform, linemerge
from geo import i2w, to_m, to_ll, px_per_m

MIN_LINE_PX = 60      # ink pieces smaller than this across are lettering and dashes
HALF_WIDTH_M = 13     # skeleton kept where the street is at most 26 m wide
NEAR_TODAY_M = 10     # a piece this close to a street drawn today is that street
CORRIDOR_GROW_M = 25
MIN_PIECE_M = 25
DRAWN = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'service',
         'living_street', 'primary_link', 'secondary_link', 'tertiary_link', 'pedestrian'}


def street_space(img):
    v = np.asarray(Image.open(img).convert('RGB')).max(2)
    bh = cv2.morphologyEx(v, cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8))
    ink = ((bh > 25) | (v < 150)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    keep = np.maximum(st[:, 2], st[:, 3]) >= MIN_LINE_PX
    keep[0] = False
    lines = cv2.dilate(keep[lab].astype(np.uint8), np.ones((3, 3), np.uint8))
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(1 - lines, connectivity=4)
    big = 1 + int(np.argmax(st2[1:, 4]))
    space = (lab2 == big).astype(np.uint8)
    # smooth the edges so lettering left in the street does not branch the skeleton
    space = cv2.morphologyEx(space, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    return space


def trace_paths(sk):
    """Skeleton pixels -> pixel paths between ends and junctions."""
    H, W = sk.shape
    pts = set(zip(*np.nonzero(sk)))
    nb = lambda p: [(p[0] + dy, p[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                    if (dy or dx) and (p[0] + dy, p[1] + dx) in pts]
    deg = {p: len(nb(p)) for p in pts}
    nodes = {p for p in pts if deg[p] != 2}
    seen, paths = set(), []
    for s in nodes:
        for q in nb(s):
            if (s, q) in seen:
                continue
            path, prev, cur = [s], s, q
            while True:
                path.append(cur)
                seen.add((prev, cur)); seen.add((cur, prev))
                if cur in nodes:
                    break
                nxt = [r for r in nb(cur) if r != prev and (cur, r) not in seen]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
            paths.append(path)
    return paths


def sheet_lines(img, params):
    space = street_space(img)
    dt = cv2.distanceTransform(space, cv2.DIST_L2, 5)
    m_px = 1 / px_per_m(params)
    sk = skeletonize(space > 0) & (dt * m_px <= HALF_WIDTH_M) & (dt * m_px >= 2.5)
    out = []
    for path in trace_paths(sk.astype(np.uint8)):
        if len(path) < 8:
            continue
        uv = np.array([(c, r) for r, c in path], float)
        xy = i2w(params, uv)
        out.append(LineString(xy).simplify(1.0))
    return out


if __name__ == '__main__':
    fmt, geo, fp, osm, hist, out = sys.argv[1:7]
    sheets = sys.argv[7:]
    geo = json.load(open(geo))
    tm = lambda x, y, z=None: to_m(x, y)
    corr = [transform(tm, shape(f['geometry'])) for f in json.load(open(fp))['features']
            if f['properties']['name'] == 'corridor'][0]
    zone = corr.buffer(CORRIDOR_GROW_M)
    today = [transform(tm, LineString(w['g'])) for w in json.load(open(osm))
             if w['tags'].get('highway') in DRAWN and len(w['g']) > 1]
    curated = [transform(tm, LineString(f['line'])) for f in json.load(open(hist))['features']
               if f.get('kind') == 'street']
    taken = unary_union([g.buffer(NEAR_TODAY_M) for g in today + curated])
    feats = []
    for sh in sheets:
        lines = [l.intersection(zone) for l in sheet_lines(fmt.format(sh=sh), geo[sh]['params'])]
        rest = unary_union([l for l in lines if not l.is_empty]).difference(taken)
        rest = linemerge(rest) if rest.geom_type == 'MultiLineString' else rest
        parts = list(rest.geoms) if hasattr(rest, 'geoms') else [rest]
        mine = []
        for p in parts:
            if p.geom_type != 'LineString' or p.length < MIN_PIECE_M:
                continue
            p = p.simplify(1.5)
            mine.append(p)
            x, y = np.asarray(p.coords).T
            lon, lat = to_ll(x, y)
            feats.append({'type': 'Feature', 'properties': {'sheet': sh, 'length_m': round(p.length, 1)},
                          'geometry': {'type': 'LineString', 'coordinates': [[round(a, 7), round(b, 7)] for a, b in zip(lon, lat)]}})
        if mine:
            taken = taken.union(unary_union([m.buffer(NEAR_TODAY_M) for m in mine]))
    for i, f in enumerate(feats):
        f['properties']['id'] = i
    json.dump({'type': 'FeatureCollection', 'features': feats}, open(out, 'w'))
    print(len(feats), 'pieces', round(sum(f['properties']['length_m'] for f in feats)), 'm')
