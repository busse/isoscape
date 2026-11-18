"""Trace the buildings on the Jackson Ward sheets of Sanborn's Richmond volume 3 as printed in 1925,
after reg25.py has warped each sheet into the frame of the same sheet's 1952 half-size scan (so
geo1952.json places it).

The 1925 printing colors every building (pink brick, yellow frame, blue stone or concrete, gray
iron, olive fireproof), so only trace52.py's first pass is used: colored regions between the
printed lines, material by vote. Uncolored regions on these sheets are yards and lots, and are not
taken. Two more rules for this printing:
  - a colored region more than 8 times longer than wide and under 2.5 m across is a porch strip or a
    frame front run along a row, or the book's edge at the scan's border: left out;
  - regions within 25 px (about 4 m) of the warped image's edge are left out (the binding and the
    page edge, which print dark and colored).
Parts are joined as trace52.py joins them (a part under 40% of its neighbor's area and under 45 m2
joins it: a porch, a rear wing).

    python3 trace25.py <sheet> <warped 1925 scan> geo1952.json <out.json> [fixes1925.json]

fixes1925.json takes trace52.py's "drop", "droppt", "split", "addpoly" and "exclude"."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np, cv2
from PIL import Image
from trace52 import classify52, regions, finish
from geo import px_per_m
from material import CLASSES


def main(sheet, img, geofile, out, fixfile=None):
    p = json.load(open(geofile))[sheet]['params']
    fixes = (json.load(open(fixfile)).get(sheet, {}) if fixfile and os.path.exists(fixfile) else {})
    drop, nosplit = set(fixes.get('drop', [])), set(fixes.get('split', []))
    im = np.asarray(Image.open(img).convert('RGB')).copy()
    H, W = im.shape[:2]
    # the warp leaves pure white outside the 1925 page; the page edge itself is kept out by margin
    outside = (im.min(2) >= 254).astype(np.uint8)
    edge = cv2.dilate(outside, np.ones((51, 51), np.uint8)) > 0
    for q in fixes.get('exclude', []):
        cv2.fillPoly(im, [np.array(q['uv'], np.int32)], (255, 255, 255))
    cls = classify52(im)
    s = px_per_m(p); m2 = 1 / (s * s)
    n, lab, st, ink = regions(im)
    parts = {}
    for i in range(1, n):
        x, y, w, h, a = st[i]
        am = a * m2
        if am < 4 or am > 4000 or x <= 25 or y <= 25 or x + w >= W - 25 or y + h >= H - 25:
            continue
        if f'c{i}' in drop:
            continue
        sub = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        if edge[y:y + h, x:x + w][sub > 0].mean() > 0.2:
            continue
        c = cls[y:y + h, x:x + w][sub > 0]
        if (c > 0).mean() < 0.5:
            continue
        cs, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = max(cs, key=cv2.contourArea)
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(cnt)
        short = min(rw, rh) * np.sqrt(m2)
        if max(rw, rh) / max(min(rw, rh), 1) > 8 and short < 2.5:
            continue
        votes = np.bincount(c, minlength=7); votes[0] = 0
        mat = CLASSES[int(votes.argmax())]
        if mat == 'stone' and am > 1500:
            continue  # water
        parts[('c', i)] = dict(mat=mat, kind='colored', area=am, marks=[], box=(x, y, w, h), glyphs=0)
    return finish(sheet, p, parts, lab, lab, W, H, out, nosplit, fixes.get('addpoly', []), m2, fixes.get('droppt', []))


if __name__ == '__main__':
    main(*sys.argv[1:])
