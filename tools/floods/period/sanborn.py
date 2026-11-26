"""Sanborn evidence for today's undated buildings: was the spot built on, on the same
footprint, in a traced edition?

    python3 tools/floods/period/sanborn.py <inventory.json> <out.json>

A traced footprint of an edition matches an undated building of today when their overlap is at
least MATCH of the smaller and the larger is at most 3 times the smaller (so a shed inside a
lost warehouse does not take the warehouse's years). For each edition whose coverage contains
the building's center the result is `present` (a match) or `gone` (mapped, nothing there; for
a building of today that means not yet built). Editions are those in history/sanborn/
(1886, 1895, 1905, 1924, 1950); the 1950-52 sheets are the last.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'sanborn'))
import numpy as np
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from geo import to_m

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
EDITIONS = [1886, 1895, 1905, 1924, 1950]
MATCH = 0.5


def poly_m(ring):
    r = np.asarray(ring)
    x, y = to_m(r[:, 0], r[:, 1])
    return Polygon(np.stack([x, y], 1)).buffer(0)


def main(inv_path, out_path):
    inv = json.load(open(inv_path))
    eds = []
    for y in EDITIONS:
        fc = json.load(open(os.path.join(ROOT, 'history', 'sanborn', f'{y}.geojson')))
        fs = [poly_m(f['geometry']['coordinates'][0]) for f in fc['features'] if not f['properties'].get('coverage')]
        cov = [poly_m(f['geometry']['coordinates'][0]) for f in fc['features'] if f['properties'].get('coverage')]
        eds.append((fc['edition'], fs, STRtree(fs), cov))
    out = {}
    for b in inv['undated']:
        p = poly_m(b['ring'])
        if p.is_empty:
            continue
        seen = []
        for year, fs, tree, cov in eds:
            if not any(c.contains(p.centroid) for c in cov):
                continue
            hit = False
            for i in tree.query(p):
                q = fs[i]
                small, big = sorted([p.area, q.area])
                if p.intersection(q).area >= MATCH * small and big <= 3 * small:
                    hit = True
                    break
            seen.append({'date': year, 'call': 'present' if hit else 'gone'})
        if seen:
            out[b['id']] = seen
    json.dump(out, open(out_path, 'w'))
    from collections import Counter
    print(len(inv['undated']), 'undated;', len(out), 'on a traced sheet;', Counter(s[-1]['date'] for s in out.values()),
          'last edition present:', Counter(s[-1]['call'] for s in out.values()))


if __name__ == '__main__':
    main(*sys.argv[1:])
