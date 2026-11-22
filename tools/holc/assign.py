"""Give each graded piece its area label, and draw each area's outline (in scan pixels).

    python3 -I assign.py <seg.npz> <labels.json> <areas_px.json> [<scan.jpg> <preview.png>]

A piece takes the label of a seed point (labels.json) that falls inside it, if the seed's
grade matches the piece's tint. A piece holding two labels' seeds is split
between them by a watershed on the scan's darkness. A piece holding no seed is named, in
order: by an assignment in labels.json that states its evidence; by contact (the labeled piece
of its grade it shares the most printed line with); else by the nearest seed of its grade
(distance from the seed point to the piece's nearest pixel), unless that is over MAX_NEAR px,
when it is left out. Every piece not named by its own seed is listed in the notes for review. Each area's pieces are then joined: closed with an ellipse JOIN px
across (bridging the heavy line between two pieces of one area), holes holding a label circle
or smaller than HOLE px or not mostly bare paper filled, and grown together by HALF px, each pixel going to the nearest area, so
the outline runs down the middle of the printed boundary line and neighbors share an edge. Outlines are simplified to SIMPLIFY px.
"""
import json
import sys

import cv2
import numpy as np

JOIN = 31
HOLE = 6000
HALF = 14          # px: measured half-gap between the tints of two areas across a printed line (median 14.3)
CONTACT = 30
SNAP = 60
MAX_NEAR = 1200   # px (about 1.9 km): a tinted piece farther than this from any label of its grade is left out
SIMPLIFY = 2.0
G = 'ABCD'


def split_shared(lbl, grade, seeds, scan):
    """A piece holding seeds of two labels (a printed boundary with a gap in it) is split by a
    watershed on the scan's blurred darkness, started from the seeds, so the cut follows the
    heaviest line between them."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    by = {}
    for s in seeds:
        if s.get('leader_only'):
            continue
        p = int(lbl[s['at'][1], s['at'][0]])
        if p:
            by.setdefault(p, {}).setdefault(s['label'], []).append(s['at'])
    gray = None
    grade = list(grade)
    log = []
    for p, labs in by.items():
        if len(labs) < 2:
            continue
        if gray is None:
            gray = np.asarray(Image.open(scan).convert('L'))
        yy, xx = np.nonzero(lbl == p)
        x0, y0, x1, y1 = xx.min() - 30, yy.min() - 30, xx.max() + 30, yy.max() + 30
        m = lbl[y0:y1, x0:x1] == p
        dark = cv2.GaussianBlur(255 - gray[y0:y1, x0:x1], (0, 0), 6)
        img = cv2.cvtColor(dark, cv2.COLOR_GRAY2BGR)
        mk = np.zeros(m.shape, np.int32)
        mk[~cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)] = 1
        names = sorted(labs)
        for k, lab in enumerate(names):
            for (x, y) in labs[lab]:
                # a disc wider than the label circle, so the marker reaches past the circle's ring
                disc = np.zeros(m.shape, np.uint8)
                cv2.circle(disc, (x - x0, y - y0), 140, 1, -1)
                mk[(disc > 0) & m] = k + 2
        seedmask = mk.copy()
        cv2.watershed(img, mk)
        # pixels of the piece the background flooded, and the watershed's own line, go to the
        # nearest seed's basin
        from scipy import ndimage
        named = mk >= 2
        _, (iy, ix) = ndimage.distance_transform_edt(~named, return_indices=True)
        fix = m & ~named
        mk[fix] = mk[iy[fix], ix[fix]]
        # basins cut off from their own seed go to the label around them
        for k in range(2, len(names) + 2):
            nc, cc = cv2.connectedComponents((mk == k).astype(np.uint8), connectivity=8)
            for j in range(1, nc):
                part = cc == j
                if (seedmask[part] == k).any():
                    continue
                ring = cv2.dilate(part.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~part
                vals = mk[ring]
                vals = vals[(vals >= 2) & (vals != k)]
                if len(vals):
                    mk[part] = np.bincount(vals).argmax()
        sub = lbl[y0:y1, x0:x1]
        for k, lab in enumerate(names[1:], start=1):
            q = len(grade)
            grade.append(grade[p])
            sub[m & (mk == k + 2)] = q
            log.append(f"piece {p} held {', '.join(names)}: split by watershed; {lab} -> piece {q}")
    return lbl, np.array(grade, np.int8), log


def main(seg, labels, out, scan=None, preview=None):
    d = np.load(seg)
    lbl, grade = d['lbl'], d['grade']
    paper = d['paper'] if 'paper' in d.files else None
    heavy = d['heavy']
    lbl, grade, splitlog = split_shared(lbl, grade, json.load(open(labels))['seeds'], scan)
    L = json.load(open(labels))
    seeds = L['seeds']
    x0, y0, x1, y1 = L['frame']
    n = len(grade)
    keep = np.zeros(n, bool)
    ys, xs = np.nonzero(lbl)
    ids = lbl[ys, xs]
    cnt = np.bincount(ids, minlength=n)
    sx = np.bincount(ids, xs, minlength=n) / np.maximum(cnt, 1)
    sy = np.bincount(ids, ys, minlength=n) / np.maximum(cnt, 1)
    for i in range(1, n):
        inside = x0 < sx[i] < x1 and y0 < sy[i] < y1
        for ex in L['exclude']:
            if ex[0] < sx[i] < ex[2] and ex[1] < sy[i] < ex[3]:
                inside = False
        keep[i] = inside
    label_of = {}
    how = {}
    notes = list(splitlog)
    for s in seeds:
        if s.get('leader_only'):
            continue
        x, y = s['at']
        p = int(lbl[y, x])
        if p == 0:
            # a seed read at an arrow tip can sit on the arrow's own ink: take the nearest piece
            # of the seed's grade within SNAP px
            win = lbl[y - SNAP:y + SNAP + 1, x - SNAP:x + SNAP + 1]
            yy, xx = np.nonzero((win > 0) & (np.take(grade, win) == G.index(s['label'][0]) + 1))
            if len(yy):
                k = np.argmin((yy - SNAP) ** 2 + (xx - SNAP) ** 2)
                p = int(win[yy[k], xx[k]])
                notes.append(f"seed {s['label']} at {s['at']} snapped to piece {p}")
        if p == 0:
            notes.append(f"seed {s['label']} at {s['at']} is not inside a piece")
            continue
        if G[grade[p] - 1] != s['label'][0]:
            notes.append(f"seed {s['label']} at {s['at']} falls in a {G[grade[p]-1]} piece")
            continue
        if p in label_of and label_of[p] != s['label']:
            notes.append(f"piece {p} holds seeds {label_of[p]} and {s['label']}")
        label_of[p] = s['label']
        how[p] = 'seed'
    # pieces named by evidence outside the map's own labels (labels.json "assign"), each with its reason
    for o in L.get('assign', []):
        x, y = o['at']
        p = int(lbl[y, x])
        if p and G[grade[p] - 1] == o['label'][0]:
            label_of[p] = o['label']
            how[p] = 'assigned: ' + o['why']
            notes.append(f"piece {p} at {o['at']} -> {o['label']} by assignment: {o['why']}")
        else:
            notes.append(f"assignment {o} matched no piece of its grade")
    # pieces with no seed: first by contact (the labeled piece of the same grade sharing the
    # longest stretch of printed line, within CONTACT px), repeated until nothing changes;
    # then the nearest seed of the same grade
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * CONTACT + 1, 2 * CONTACT + 1))
    todo = [p for p in range(1, n) if keep[p] and p not in label_of]
    ring = {}
    for p in todo:
        yy, xx = np.nonzero(lbl == p)
        bx0, by0 = max(xx.min() - CONTACT - 2, 0), max(yy.min() - CONTACT - 2, 0)
        sub = lbl[by0:yy.max() + CONTACT + 2, bx0:xx.max() + CONTACT + 2]
        grown = cv2.dilate((sub == p).astype(np.uint8), kc).astype(bool)
        nb = sub[grown & (sub != p) & (sub != 0)]
        ring[p] = {int(q): int(c) for q, c in zip(*np.unique(nb, return_counts=True)) if grade[q] == grade[p]}
    changed = True
    while changed:
        changed = False
        for p in todo:
            if p in label_of:
                continue
            votes = {}
            for q, c in ring[p].items():
                if q in label_of:
                    votes[label_of[q]] = votes.get(label_of[q], 0) + c
            if votes:
                lab = max(votes, key=votes.get)
                label_of[p] = lab
                how[p] = 'contact ' + ', '.join(f'{k}:{v}' for k, v in votes.items())
                notes.append(f"piece {p} ({G[grade[p]-1]}, {cnt[p]} px, at {sx[p]:.0f},{sy[p]:.0f}) -> {lab} by contact ({how[p][8:]})")
                changed = True
    for p in todo:
        if p in label_of:
            continue
        m = (lbl == p)
        yy, xx = np.nonzero(m)
        best = None
        for s in seeds:
            if s['label'][0] != G[grade[p] - 1]:
                continue
            dd = np.min((xx - s['at'][0]) ** 2 + (yy - s['at'][1]) ** 2) ** 0.5
            if best is None or dd < best[0]:
                best = (dd, s['label'])
        if best and best[0] > MAX_NEAR:
            notes.append(f"piece {p} ({G[grade[p]-1]}, {cnt[p]} px, at {sx[p]:.0f},{sy[p]:.0f}) left out: nearest {G[grade[p]-1]} label {best[1]} is {best[0]:.0f} px away")
            continue
        if best:
            label_of[p] = best[1]
            how[p] = f'nearness {best[0]:.0f} px'
            notes.append(f"piece {p} ({G[grade[p]-1]}, {cnt[p]} px, at {sx[p]:.0f},{sy[p]:.0f}) -> {best[1]} by nearness, {best[0]:.0f} px")
    areas = {}
    for p, lab in label_of.items():
        areas.setdefault(lab, []).append(p)
    kj = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (JOIN, JOIN))
    from scipy import ndimage
    order = sorted(areas, key=lambda s: (s[0], float(s[1:])))
    # 1. each area's pieces joined and its holes filled, into one map of areas (0 = none)
    amap = np.zeros(lbl.shape, np.int16)
    boxes = {}
    for ai, lab in enumerate(order, start=1):
        ps = areas[lab]
        yy, xx = np.nonzero(np.isin(lbl, ps))
        bx0, by0 = max(xx.min() - 60, 0), max(yy.min() - 60, 0)
        bx1, by1 = xx.max() + 60, yy.max() + 60
        sub = np.isin(lbl[by0:by1, bx0:bx1], ps).astype(np.uint8)
        sub = cv2.morphologyEx(sub, cv2.MORPH_CLOSE, kj)
        # fill holes: small ones, ones that hold a label of this area, ones not mostly bare paper
        inv = (1 - sub).astype(np.uint8)
        nh, hl, st, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
        circ = [s['at'] for s in seeds if s['label'] == lab]
        for h in range(1, nh):
            hx, hy, hw, hh, ha = st[h]
            if hx == 0 or hy == 0 or hx + hw >= sub.shape[1] or hy + hh >= sub.shape[0]:
                continue  # touches the box edge: outside
            hold = any(0 <= c[1] - by0 < sub.shape[0] and 0 <= c[0] - bx0 < sub.shape[1] and hl[c[1] - by0, c[0] - bx0] == h for c in circ)
            if paper is not None:
                hm = (hl == h) & ~heavy[by0:by1, bx0:bx1]  # the hole's own ground, not its border line
                paperish = paper[by0:by1, bx0:bx1][hm].mean() if hm.any() else 0.0
            else:
                paperish = 1.0
            if ha < HOLE or hold or paperish < 0.5:
                sub[hl == h] = 1
        win = amap[by0:by1, bx0:bx1]
        win[(sub > 0) & (win == 0)] = ai
        boxes[ai] = (bx0, by0, bx1, by1)
    # 2. every area grown by HALF px, each pixel to the nearest area, so two areas sharing a
    #    printed line meet on its middle and an outer edge lies on the middle of its line
    feats = []
    for ai, lab in enumerate(order, start=1):
        bx0, by0, bx1, by1 = boxes[ai]
        bx0, by0 = max(bx0 - HALF - 4, 0), max(by0 - HALF - 4, 0)
        bx1, by1 = bx1 + HALF + 4, by1 + HALF + 4
        win = amap[by0:by1, bx0:bx1]
        dist, (iy, ix) = ndimage.distance_transform_edt(win == 0, return_indices=True)
        sub = ((win[iy, ix] == ai) & (dist <= HALF)).astype(np.uint8)
        ps = areas[lab]
        cs, hier = cv2.findContours(sub, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        polys = []
        for i, c in enumerate(cs):
            if hier[0][i][3] != -1:
                continue
            ring = cv2.approxPolyDP(c, SIMPLIFY, True)[:, 0, :] + [bx0, by0]
            holes = []
            j = hier[0][i][2]
            while j != -1:
                h = cv2.approxPolyDP(cs[j], SIMPLIFY, True)[:, 0, :] + [bx0, by0]
                if cv2.contourArea(cs[j]) >= HOLE:
                    holes.append(h.tolist())
                j = hier[0][j][0]
            if cv2.contourArea(c) < 2000:
                continue
            polys.append([ring.tolist()] + holes)
        feats.append({'label': lab, 'grade': lab[0], 'area_number': lab[1:], 'pieces': [int(p) for p in ps],
                      'how': {int(p): how[p] for p in ps}, 'polygons_px': polys})
    json.dump({'areas': feats, 'notes': notes}, open(out, 'w'))
    want = sorted({x['label'] for x in seeds})
    print('missing:', [w for w in want if w not in areas])
    print(len(feats), 'areas;', sum(len(f['polygons_px']) for f in feats), 'polygons')
    for t in notes:
        print(' ', t)
    if scan and preview:
        from PIL import Image, ImageDraw
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(scan).convert('RGB')
        im = im.resize((im.width // 4, im.height // 4))
        dr = ImageDraw.Draw(im)
        for f in feats:
            for poly in f['polygons_px']:
                for r in poly:
                    dr.line([tuple(v) for v in (np.array(r + [r[0]]) / 4)], fill=(255, 0, 255), width=2)
            big = max((pl[0] for pl in f['polygons_px']), key=lambda r: cv2.contourArea(np.array(r, np.int32)))
            cx, cy = np.mean(big, 0) / 4
            dr.text((cx - 10, cy), f['label'], fill=(0, 0, 0), stroke_width=3, stroke_fill=(255, 255, 255))
        im.save(preview)


if __name__ == '__main__':
    main(*sys.argv[1:])
