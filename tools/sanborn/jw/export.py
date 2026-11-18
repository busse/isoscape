"""Gather the traced Jackson Ward sheets into one edition file in the format of
../extract.py (history/sanborn/<edition>.geojson), plus what this edition adds:

  color    'colored' or 'uncolored' (printed as a plain outline; the 1925 printing colors the same
           buildings yellow, so these are taken for frame: an inference, not printed)
  storeys  2, assumed (the sheets print each building's stories; they were not read, except for
           the named buildings in named.csv)
  storeysFrom 'assumed' or 'sheet'
  name, use where read by eye (named.csv: edition, sheet, a point inside the building (lon, lat;
           u50, v50 on the 50% scan), name, use, stories, note)
  id       jw<edition>-<sheet>-<n>; n is the number printed on that sheet's overlay
  byEye    true for outlines placed by eye (fixes.json addpoly)

Buildings whose center falls in one already taken from an earlier sheet are skipped (sheets lap
at their edges). Coverage: per sheet, the hull of its buildings' centers grown by 25 m, as in
extract.py.

    python3 export.py <edition> <out.geojson> <named.csv> <trace.json>..."""
import json, sys, csv, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon, MultiPoint
from shapely.ops import unary_union
from geo import to_m, to_ll

def main(edition, out, named, *traces):
    edition = int(edition)
    names = []
    if os.path.exists(named):
        from shapely.geometry import Point
        for r in csv.DictReader(open(named)):
            if r.get('edition') and int(r['edition']) != edition: continue
            x, y = to_m(float(r['lon']), float(r['lat'])); r['_pt'] = Point(float(x), float(y)); names.append(r)
    feats, taken, cover = [], [], []
    for path in traces:
        t = json.load(open(path)); sh = t['sheet']; cs = []
        for n, b in enumerate(t['buildings']):
            r = np.array(b['ring']); x, y = to_m(r[:, 0], r[:, 1]); poly = Polygon(np.stack([x, y], 1)).buffer(0)
            if poly.is_empty or poly.area < 4: continue
            c = poly.representative_point(); cs.append(poly.centroid)
            if any(q.contains(c) for q in taken): continue
            taken.append(poly)
            pr = {'edition': edition, 'sheet': sh, 'id': f'jw{edition}-{sh}-{n}', 'n': n, 'material': b['material'], 'color': b['color'],
                  'storeys': 2, 'storeysFrom': 'assumed', 'area': round(poly.area, 1)}
            if b.get('byEye'): pr['byEye'] = True
            for row in [r for r in names if r['sheet'] == sh and poly.buffer(0.5).contains(r['_pt'])]:
                if row.get('name'): pr['name'] = row['name']
                if row.get('use'): pr['use'] = row['use']
                if row.get('stories'):
                    try: pr['storeys'] = int(float(row['stories'])); pr['storeysFrom'] = 'sheet'
                    except ValueError: pass
            ring = b['ring'] + [b['ring'][0]]
            feats.append({'type': 'Feature', 'properties': pr, 'geometry': {'type': 'Polygon', 'coordinates': [ring]}})
        if cs:
            cover.append(MultiPoint(cs).convex_hull.buffer(25))
    cov = unary_union(cover)
    for p in ([cov] if cov.geom_type == 'Polygon' else list(cov.geoms)):
        x, y = p.exterior.xy; lon, lat = to_ll(np.array(x), np.array(y))
        feats.append({'type': 'Feature', 'properties': {'edition': edition, 'coverage': True},
                      'geometry': {'type': 'Polygon', 'coordinates': [list(zip(lon.round(7).tolist(), lat.round(7).tolist()))]}})
    json.dump({'type': 'FeatureCollection', 'edition': edition, 'features': feats}, open(out, 'w'))
    print(out, sum(1 for f in feats if not f['properties'].get('coverage')), 'buildings')

if __name__ == '__main__':
    main(*sys.argv[1:])
