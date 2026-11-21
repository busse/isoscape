"""Make the count picture draw every building the count counts.

    python3 count_restore.py <edition file> <jackson-ward-lost.geojson> <highway-footprint.geojson>

The repository's cleaning (../clean.py) dropped small or spiky outlines from the drawn layer; in
the corridor that left 82 counted buildings undrawn, so the count picture and the count
disagreed (406 drawn against 489 counted). This puts back, as traced, every outline from the
edition file whose center falls in the corridor polygon, that is at least MIN_AREA m² (the
region's minBuildingArea: the renderer draws nothing smaller), and that the lost layer does not
hold, ending it in 1956 (end "highway") as corridor_ends.py does. count.py counts by the same
12 m² floor, so the picture and the numbers agree."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon, shape
from shapely import transform as stransform
from geo import to_m

MIN_AREA = 12
CLEARED = 1956


def m_of(c):
    return np.stack(to_m(c[:, 0], c[:, 1]), 1)


def main(ed, lost, fp):
    corr = [stransform(shape(f['geometry']), m_of) for f in json.load(open(fp))['features']
            if f['properties']['name'] == 'corridor'][0]
    lf = json.load(open(lost))
    have = {f['properties']['id'] for f in lf['features']}
    back = 0
    for f in json.load(open(ed))['features']:
        p = f['properties']
        if p.get('coverage') or p.get('notBuilding') or p['id'] in have:
            continue
        g = stransform(shape(f['geometry']), m_of).buffer(0)
        if g.area < MIN_AREA or not corr.contains(g.representative_point()):
            continue
        props = {'id': p['id'], 'from': 1952, 'lastSeen': 1952, 'to': CLEARED, 'end': 'highway',
                 'material': p['material'], 'storeys': p['storeys'], 'sheet': p['sheet'], 'edition': 1952,
                 'color': p['color'], 'storeysFrom': p.get('storeysFrom', 'assumed'), 'restoredForCount': True}
        for k in ('name', 'use', 'printed', 'byEye'):
            if k in p:
                props[k] = p[k]
        lf['features'].append({'type': 'Feature', 'properties': props, 'geometry': f['geometry']})
        back += 1
    json.dump(lf, open(lost, 'w'))
    print(back, 'put back')


if __name__ == '__main__':
    main(*sys.argv[1:])
