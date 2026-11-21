"""After finish.py (and the cleaning): end every lost Jackson Ward building whose center falls in the
highway's corridor polygon (highway-footprint.geojson, "corridor": today's paved roadway and ramps
plus 15 m each side) at the Turnpike's clearances, 1955-58, drawn as gone from 1956.

    python3 corridor_ends.py <jackson-ward-lost.geojson> <highway-footprint.geojson> [polygon name]

The rule is the same one count.py counts by: a point inside the building's outline falls in the
polygon. It rewrites `to` (1956) and `end` ("highway") in place and leaves every other building
as lifespans.py dated it. The corridor is a stand-in for the 1958 right-of-way, which has not been
seen (Library of Virginia, Acc. 40941), so the line between taken and left is approximate."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon, shape
from geo import to_m

CLEARED = 1956


def pm(ring):
    r = np.asarray(ring); x, y = to_m(r[:, 0], r[:, 1]); return Polygon(np.stack([x, y], 1)).buffer(0)


def main(lost, fp, name='corridor'):
    feats = {f['properties']['name']: f for f in json.load(open(fp))['features']}
    g = shape(feats[name]['geometry'])
    polys = [pm(p.exterior.coords) for p in getattr(g, "geoms", [g])]
    holes = [pm(i.coords) for p in getattr(g, 'geoms', [g]) for i in p.interiors]
    inside = lambda pt: any(P.contains(pt) for P in polys) and not any(H.contains(pt) for H in holes)
    fc = json.load(open(lost))
    n = changed = 0
    for f in fc['features']:
        c = pm(f['geometry']['coordinates'][0]).representative_point()
        if not inside(c):
            continue
        n += 1
        pr = f['properties']
        if pr['to'] != CLEARED or pr['end'] != 'highway':
            changed += 1
        pr['to'], pr['end'] = CLEARED, 'highway'
    json.dump(fc, open(lost, 'w'))
    print(n, 'inside the', name, 'polygon, ended', CLEARED, f'({changed} changed)')


if __name__ == '__main__':
    main(*sys.argv[1:])
