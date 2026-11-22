"""Street corners from the cached OpenStreetMap data, for control points.

    python3 corners.py <osm.json> "<street A>" "<street B>" [...more pairs]

Prints each place where a way named like A meets or crosses a way named like B (lon, lat),
matching whole names case-insensitively; give alternatives as "a|b". Only highway ways are read.
"""
import json
import sys
from functools import lru_cache

from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union

HW = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'trunk', 'living_street',
      'primary_link', 'secondary_link', 'tertiary_link', 'service', 'pedestrian', 'trunk_link'}


def load(path):
    d = json.load(open(path))
    ways = []
    for e in d['elements']:
        t = e.get('tags', {})
        if e['type'] != 'way' or t.get('highway') not in HW or 'name' not in t:
            continue
        g = [p for p in (e.get('geometry') or []) if p]
        if len(g) < 2:
            continue
        ways.append((t['name'].lower(), LineString([(p['lon'], p['lat']) for p in g])))
    return ways


def named(ways, q):
    """Ways whose name is exactly one of q's '|'-separated names (case ignored)."""
    qs = {x.strip().lower() for x in q.split('|')}
    return unary_union([g for n, g in ways if n in qs])


def corners(ways, a, b):
    ga, gb = named(ways, a), named(ways, b)
    x = ga.intersection(gb)
    pts = []
    for g in getattr(x, 'geoms', [x]):
        if g.is_empty:
            continue
        c = g.centroid if g.geom_type != 'Point' else g
        if not any(abs(c.x - p[0]) < 2e-4 and abs(c.y - p[1]) < 2e-4 for p in pts):
            pts.append((round(c.x, 7), round(c.y, 7)))
    return pts


if __name__ == '__main__':
    ways = load(sys.argv[1])
    args = sys.argv[2:]
    for i in range(0, len(args), 2):
        print(args[i], '&', args[i + 1], corners(ways, args[i], args[i + 1]))
