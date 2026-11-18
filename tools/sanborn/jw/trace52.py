"""Trace the buildings on the Jackson Ward sheets of Sanborn's 1925 volume 3 as republished in
1951-52, where most frame buildings are printed as plain outlines with no color (the 1925 printing
colors the same buildings yellow), so the color tracer in ../extract.py misses them.

The sheet's printed lines are found by local contrast (a black-hat of 7 px on the 50% scan, plus
anything dark), thickened by 1 px, and the paper between them split into closed regions. A region
is a building part when:
  - most of it is colored (pink brick, yellow frame, blue, gray, green, olive): material by vote; or
  - it is uncolored and holds a glyph-sized printed mark inside it (the story number, the use
    letter "D", the roof circle; under 120 m2 an open mark, the F of a flat or a story number, is
    enough), and is not a yard or a lot strip: area 6-350 m2 (a larger outline
    on these sheets is a yard; none of the plain outlines checked by eye was a building that big), it
    fills at least half its rotated bounding box, and it is not more than 5 times longer than
    wide. Yards that hold a printed dimension or a block number pass this test too: looking at
    every sheet's overlay finds them, and they are dropped by hand (fixes.json).
Dashed lines are bridged first (a closing along 7 px lines at every 15 degrees), so an open
porch or a wall drawn dashed still closes its building off from the yard.
An uncolored region of the first pass (lines as printed) that holds regions of the second
(dashes bridged) filling under 70% of it had leaked into its yard, and one that holds two or more
marked regions of the second is a row of houses split by dashed party walls: in both cases the
second-pass regions replace it.
Parts that share a printed line are joined into one building when the smaller is under 40% of the
larger's area and under 45 m2 (a porch, a rear wing or an addition); parts of like size (row houses, a block of
stores) stay separate buildings. An uncolored part whose edge is more than half shared with
colored parts (a label box or a light well inside a colored building) joins that building. Region outlines are grown by 1.5 px to the middle of their lines.

    python3 trace52.py <sheet> <50% scan> geo1952.json <out.json> [fixes.json]

fixes.json (per sheet) lists what looking at the overlay found: "drop": region ids that are not
buildings (a yard holding a dimension, a block number), "add": [u, v] points (50% px) inside
outlined buildings the rules missed, "droppt": [u, v] points (50% px): the building holding each
is dropped before parts are joined (a yard), "split": ids not to join to a neighbor, "addpoly": outlines read by
eye ({"uv": [[u, v], ...] in 50% px, "material", "color"}) where an outline leaks on both passes,
"exclude": areas left out ({"uv": ..., "why"}), such as an inset drawn at another orientation.
Out: one record per building: ring (lon/lat), material, color ('colored' or 'uncolored'),
area m2, parts, ids of its regions, and the points where its marks sit (for reading labels)."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np, cv2
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union
from geo import i2w, to_ll, px_per_m
from material import classify, CLASSES

def classify52(im):
    """../material.py's colors, plus the 1951-52 printing's salmon pink for brick (as red over
    green as the earlier pink, but no bluer than the paper), which the earlier rule misses."""
    cls, ink, P = classify(im, True)
    q = im.astype(np.int16)
    rg = (q[..., 0] - q[..., 1]) - (int(P[0]) - int(P[1]))
    bg = (q[..., 2] - q[..., 1]) - (int(P[2]) - int(P[1]))
    cls[(cls == 0) & (rg > 14) & (bg > -8) & ~ink] = 1
    return cls

def regions(im, close_angles=()):
    v = im.max(2)
    bh = cv2.morphologyEx(v, cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8))
    ink = ((bh > 25) | (v < 150)).astype(np.uint8)
    closed = ink.copy()
    for ang in close_angles:
        # bridge the gaps of dashed lines along the sheet's own grid directions
        k = np.zeros((9, 9), np.uint8)
        dx, dy = np.cos(np.radians(ang)) * 4, np.sin(np.radians(ang)) * 4
        cv2.line(k, (int(round(4 - dx)), int(round(4 - dy))), (int(round(4 + dx)), int(round(4 + dy))), 1, 1)
        closed |= cv2.morphologyEx(ink, cv2.MORPH_CLOSE, k)
    inkc = cv2.dilate(closed, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(1 - inkc, connectivity=4)
    return n, lab, st, ink

def glyph_boxes(ink):
    """Printed marks the size of a letter or the roof circle: ink
    pieces standing alone, 5-19 px across (the 50% scan), 25-300 px of ink; those closing around a
    counter (D, A, the roof circle) count 1, open ones at least 7 x 9 px (F, 2, S) count a half. Dashes are
    thinner than 5 px; block numbers ('65N') are taller than 19."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    k = (st[:, 4] >= 25) & (st[:, 4] <= 300) & (np.minimum(st[:, 2], st[:, 3]) >= 5) & (st[:, 2] <= 19) & (st[:, 3] <= 19)
    k[0] = False
    out = []
    for i in np.flatnonzero(k):
        x, y, w, h = st[i, :4]
        # only marks that close around a counter: the use letters D and A, the roof circle, a B
        # (a printed dimension, 15' or 25', mostly does not)
        sub = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        cs, hier = cv2.findContours(np.pad(sub, 1), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        closed = hier is not None and any(hh[3] >= 0 and cv2.contourArea(c) >= 2 for c, hh in zip(cs, hier[0]))
        if closed or (w >= 7 and h >= 9):
            out.append((x, y, w, h, int(closed)))
    return np.array(out).reshape(-1, 5)

def count_glyphs(lab, boxes):
    """Each mark is given to the region that holds three quarters of the paper around it."""
    out = {}
    H, W = lab.shape
    for x, y, w, h, closed in boxes:
        x0, y0, x1, y1 = max(0, x - 2), max(0, y - 2), min(W, x + w + 2), min(H, y + h + 2)
        v = lab[y0:y1, x0:x1].ravel(); v = v[v > 0]
        if v.size:
            bc = np.bincount(v); r = int(bc.argmax())
            if bc[r] >= 0.75 * v.size:  # a mark on a line between two regions (an address, a width) is no one's
                # a closed mark counts whole; an open one (the F of a flat, the story number 2) half
                out[r] = out.get(r, 0) + (1 if closed else 0.5)
    return out

def grid_angles(im):
    """The directions of the sheet's printed lines: 0 and 90 degrees, and the two commonest others."""
    v = im.max(2)
    ink = (cv2.morphologyEx(v, cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8)) > 25).astype(np.uint8) * 255
    ls = cv2.HoughLinesP(ink, 1, np.pi / 180, 80, minLineLength=80, maxLineGap=3)
    angs = [0, 90]
    if ls is not None:
        ls = ls.reshape(-1, 4).astype(float)
        a = np.degrees(np.arctan2(ls[:, 3] - ls[:, 1], ls[:, 2] - ls[:, 0])) % 180
        h = np.bincount(np.round(a).astype(int) % 180, minlength=180)
        for d in (0, 90, 1, 89, 179, 91): h[d] = 0
        for _ in range(2):
            d = int(h.argmax())
            if h[d] < 5: break
            angs.append(d); h[max(0, d - 4):d + 5] = 0
    return angs

def main(sheet, img, geofile, out, fixfile=None):
    geo = json.load(open(geofile))[sheet]; p = geo['params']
    fixes = (json.load(open(fixfile)).get(sheet, {}) if fixfile and os.path.exists(fixfile) else {})
    drop, adds, nosplit = set(fixes.get('drop', [])), fixes.get('add', []), set(fixes.get('split', []))
    im = np.asarray(Image.open(img).convert('RGB')).copy()
    H, W = im.shape[:2]
    for q in fixes.get('exclude', []):
        # an inset drawn at its own orientation (fitted separately, or left out): blanked
        cv2.fillPoly(im, [np.array(q['uv'], np.int32)], (255, 255, 255))
    cls = classify52(im)
    s = px_per_m(p); m2 = 1 / (s * s)
    angs = grid_angles(im)
    parts = {}
    # pass 1, colored parts, on the lines as printed; pass 2, uncolored, with dashes bridged
    for pass_ in (1, 2):
        n, lab, st, ink = regions(im, () if pass_ == 1 else angs)
        if pass_ == 1: boxes = glyph_boxes(ink)
        found = collect(pass_, n, lab, st, cls, m2, W, H, drop, adds if pass_ == 2 else [], count_glyphs(lab, boxes))
        # (pass 1 also takes the uncolored buildings whose outlines close as printed; pass 2 adds
        # those that close only once their dashes are bridged)
        if pass_ == 1:
            taken = np.zeros((H, W), np.uint8); labs1 = lab
            for i, q in found.items():
                parts[('c', i)] = q; x, y, w, h = q['box']; taken[y:y + h, x:x + w][lab[y:y + h, x:x + w] == i] = 1
        else:
            # an uncolored part of pass 1 that holds pass-2 parts filling under 70% of it leaked
            # into its yard through a dashed line: its pass-2 parts replace it
            inside = {}
            for i, q in found.items():
                x, y, w, h = q['box']; m = lab[y:y + h, x:x + w] == i
                hit = labs1[y:y + h, x:x + w][m]
                k = np.bincount(hit).argmax() if hit.size else 0
                if k and ('c', k) in parts and parts[('c', k)]['kind'] == 'uncolored' and (hit == k).mean() >= 0.8:
                    inside.setdefault(k, []).append(i)
            for k, qs in inside.items():
                marked = [i for i in qs if found[i].get('glyphs', 0) >= 1]
                if sum(found[i]['area'] for i in qs) < 0.7 * parts[('c', k)]['area'] or len(marked) >= 2:
                    x, y, w, h = parts[('c', k)]['box']; taken[y:y + h, x:x + w][labs1[y:y + h, x:x + w] == k] = 0
                    del parts[('c', k)]
                    for i in qs: parts[('u', i)] = found[i]
            for i, q in found.items():
                if ('u', i) in parts: continue
                x, y, w, h = q['box']
                if taken[y:y + h, x:x + w][lab[y:y + h, x:x + w] == i].mean() > 0.2: continue
                parts[('u', i)] = q
    return finish(sheet, p, parts, labs1, lab, W, H, out, nosplit, fixes.get('addpoly', []), m2, fixes.get('droppt', []))

def collect(pass_, n, lab, st, cls, m2, W, H, drop, adds, gcount):
    added = {int(lab[int(v), int(u)]) for u, v in adds}
    parts = {}
    for i in range(1, n):
        x, y, w, h, a = st[i]
        am = a * m2
        if am < 2.5 or am > 4000 or x <= 2 or y <= 2 or x + w >= W - 2 or y + h >= H - 2:
            continue
        sub = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        c = cls[y:y + h, x:x + w][sub > 0]
        colored = (c > 0).mean()
        cs, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = max(cs, key=cv2.contourArea)
        filled = np.zeros_like(sub); cv2.drawContours(filled, [cnt], -1, 1, -1)
        holes = filled & (1 - sub)
        nh, hl, hs, hc = cv2.connectedComponentsWithStats(holes, connectivity=8)
        marks = [(float(hc[j][0] + x), float(hc[j][1] + y)) for j in range(1, nh) if 4 <= hs[j, 4] <= 300]
        # glyph-sized marks (a letter, a digit, the roof circle), not dashes or specks
        glyphs = gcount.get(i, 0)
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(cnt)
        fill = a / max(rw * rh, 1)
        elong = max(rw, rh) / max(min(rw, rh), 1)
        if f'{"c" if pass_ == 1 else "u"}{i}' in drop:
            continue
        if pass_ == 1 and colored >= 0.5 and am >= 4:
            votes = np.bincount(c, minlength=7); votes[0] = 0
            mat = CLASSES[int(votes.argmax())]
            if mat == 'stone' and am > 1500:
                continue  # water
            kind = 'colored'
        elif (pass_ == 2 and i in added) or ( ((glyphs >= 1 or (glyphs >= 0.5 and am <= 120)) and 6 <= am <= 350 and fill >= 0.5 and elong <= 5 and colored < 0.2)):
            mat, kind = 'frame', 'uncolored'
        else:
            continue
        parts[i] = dict(mat=mat, kind=kind, area=am, marks=marks, box=(x, y, w, h), glyphs=glyphs)
    return parts

def finish(sheet, p, parts, lab1, lab2, W, H, out, nosplit, addpolys=(), m2_=1.0, droppts=()):
    # region ids: colored parts 'c<id>' (pass 1), uncolored 'u<id>' (pass 2)
    owner = np.zeros((H, W), np.int32); keys = sorted(parts, key=str); idx = {k: j + 1 for j, k in enumerate(keys)}
    for k in keys:
        x, y, w, h = parts[k]['box']; L = lab1 if k[0] == 'c' else lab2
        m = L[y:y + h, x:x + w] == k[1]
        owner[y:y + h, x:x + w][m] = idx[k]
    lab = owner
    parts = {idx[k]: dict(parts[k], name=f'{k[0]}{k[1]}') for k in keys}
    for u, v in droppts:
        # the part holding each point is dropped (a yard), before parts are joined
        j = int(lab[int(v), int(u)])
        if j in parts:
            del parts[j]; lab[lab == j] = 0
    # join parts that share a printed line
    ids = sorted(parts)
    grown = {}
    for i in ids:
        x, y, w, h = parts[i]['box']
        x0, y0 = max(0, x - 4), max(0, y - 4); x1, y1 = min(W, x + w + 4), min(H, y + h + 4)
        grown[i] = (x0, y0, cv2.dilate((lab[y0:y1, x0:x1] == i).astype(np.uint8), np.ones((7, 7), np.uint8)))
    parent = {i: i for i in ids}
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in ids:
        x0, y0, g = grown[i]
        nb = set(np.unique(lab[y0:y0 + g.shape[0], x0:x0 + g.shape[1]][g > 0])) & set(ids)
        for j in nb:
            if j <= i or parts[i]['name'] in nosplit or parts[j]['name'] in nosplit: continue
            small, big = sorted((parts[i]['area'], parts[j]['area']))
            if small < 0.4 * big and small < 45:
                parent[find(i)] = find(j)
    # an uncolored part most of whose edge is shared with colored parts is a label box or a light
    # well inside a colored building: it joins that building
    for i in ids:
        if parts[i]['kind'] != 'uncolored': continue
        x0, y0, g = grown[i]
        ring = g.astype(bool) & (lab[y0:y0 + g.shape[0], x0:x0 + g.shape[1]] != i)
        nbl = lab[y0:y0 + g.shape[0], x0:x0 + g.shape[1]][ring]
        col = [j for j in set(nbl.tolist()) if j in parts and parts[j]['kind'] == 'colored']
        if col and sum((nbl == j).sum() for j in col) > 0.5 * ring.sum():
            parent[find(i)] = find(max(col, key=lambda j: (nbl == j).sum()))
    groups = {}
    for i in ids: groups.setdefault(find(i), []).append(i)
    recs = []
    for g in groups.values():
        mask_polys = []
        for i in g:
            x, y, w, h = parts[i]['box']
            sub = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
            sub = cv2.dilate(np.pad(sub, 3), np.ones((4, 4), np.uint8))
            cs, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnt = max(cs, key=cv2.contourArea)
            cnt = cv2.approxPolyDP(cnt, 1.2, True)[:, 0, :].astype(float) + [x - 3, y - 3]
            if len(cnt) >= 3:
                mask_polys.append(Polygon(cnt).buffer(0.8, join_style=2))
        poly = unary_union(mask_polys).buffer(-0.8, join_style=2)
        if poly.geom_type != 'Polygon':
            poly = max(poly.geoms, key=lambda q: q.area) if hasattr(poly, 'geoms') and len(poly.geoms) else None
        if poly is None or poly.is_empty: continue
        uv = np.array(poly.exterior.coords)[:-1]
        xy = i2w(p, uv); lon, lat = to_ll(xy[:, 0], xy[:, 1])
        main_part = max(g, key=lambda i: parts[i]['area'])
        recs.append(dict(ids=sorted(parts[i]['name'] for i in g), ring=[[round(float(a), 7), round(float(b), 7)] for a, b in zip(lon, lat)],
                         uv=[[round(float(a), 1), round(float(b), 1)] for a, b in uv],
                         material=parts[main_part]['mat'], color=parts[main_part]['kind'],
                         area=round(sum(parts[i]['area'] for i in g), 1), parts=len(g),
                         marks=[m for i in g for m in parts[i]['marks']]))
    for k, a in enumerate(addpolys):
        # outlines placed by eye where the rules failed (a house whose dashed outline leaks on both passes)
        uv = np.array(a['uv'], float)
        xy = i2w(p, uv); lon, lat = to_ll(xy[:, 0], xy[:, 1])
        recs.append(dict(ids=[f'p{k}'], ring=[[round(float(a_), 7), round(float(b_), 7)] for a_, b_ in zip(lon, lat)],
                         uv=uv.round(1).tolist(), material=a.get('material', 'frame'), color=a.get('color', 'uncolored'),
                         area=round(Polygon(uv).area * m2_, 1), parts=1, marks=[], byEye=True))
    json.dump(dict(sheet=sheet, buildings=recs), open(out, 'w'))
    from collections import Counter
    print(sheet, len(recs), 'buildings', Counter((r['color'], r['material']) for r in recs).most_common())

if __name__ == '__main__':
    main(*sys.argv[1:])
