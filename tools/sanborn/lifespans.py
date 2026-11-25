"""From traced editions to lost buildings with lifespans.

A traced footprint that today's buildings cover by half or more is taken to be a building that
still stands, or one rebuilt on the same footprint: today's data already draws it. The rest are
lost buildings. Each is followed through later editions (a later footprint covering half of
it is the same building) and given:
  from: the first edition it appears in (it may be older; the map cannot say);
  to:   the first year it is known to be gone. In order of preference:
        a later edition that maps the spot without it (evidence: map);
        the year built of a building that stands on the spot today (evidence: rebuilt);
        the opening of an expressway through it (evidence: highway);
        otherwise 1960, the start of the era that cleared most of downtown for parking
        (evidence: assumed)."""
import json, sys
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.strtree import STRtree
from geo import to_m

ASSUMED_END = 1960


def poly_m(ring):
    r = np.asarray(ring)
    x, y = to_m(r[:, 0], r[:, 1])
    return Polygon(np.stack([x, y], 1)).buffer(0)


def main(out, buildings_path, motorways_path, *editions, respect_years=False, strict_link=False):
    today = json.load(open(buildings_path))
    tpolys, tyears = [], []
    for b in today:
        if len(b['ring']) >= 3:
            p = poly_m(b['ring'])
            if not p.is_empty:
                tpolys.append(p); tyears.append(b['year'])
    ttree = STRtree(tpolys)
    roads = []
    for m in json.load(open(motorways_path)):
        x, y = to_m(*np.asarray(m['line']).T)
        roads.append((LineString(np.stack([x, y], 1)).buffer(18), m['year']))
    eds = []
    for path in editions:
        fc = json.load(open(path))
        fs = [f for f in fc['features'] if not f['properties'].get('coverage')]
        cov = [poly_m(f['geometry']['coordinates'][0]) for f in fc['features'] if f['properties'].get('coverage')]
        polys = [poly_m(f['geometry']['coordinates'][0]) for f in fs]
        eds.append(dict(year=fc['edition'], feats=fs, polys=polys, tree=STRtree(polys), cover=cov))
    entities = []
    for ei, ed in enumerate(eds):
        for f, p in zip(ed['feats'], ed['polys']):
            if f.get('_linked'):
                continue
            # With --respect-years, a building of today counts as this one only if it was built by
            # this edition's year (or is undated): a 2016 museum on the lot is not the 1924 garage.
            near = [i for i in ttree.query(p) if not respect_years or tyears[i] is None or tyears[i] <= ed['year']]
            cover = sum(p.intersection(tpolys[i]).area for i in near) / p.area
            if cover >= 0.5:
                continue
            ent = dict(first=ed['year'], last=ed['year'], f=f, p=p, to=None, evidence=None)
            # follow it through later editions
            for later in eds[ei + 1:]:
                hit = None
                for j in later['tree'].query(p):
                    q = later['polys'][j]
                    # With --strict-link the two must overlap by half of the larger, so a big garage
                    # is not followed into a small shed that later stood inside its outline.
                    if q.intersection(p).area >= 0.5 * (max if strict_link else min)(p.area, q.area):
                        hit = j; break
                if hit is not None:
                    later['feats'][hit]['_linked'] = True
                    ent.update(last=later['year'], f=later['feats'][hit], p=later['polys'][hit])
                elif any(c.contains(p.centroid) for c in later['cover']):
                    ent.update(to=later['year'], evidence='map'); break
            if ent['to'] is None:
                ys = [tyears[i] for i in ttree.query(ent['p']) if tyears[i] is not None and tpolys[i].intersection(ent['p']).area > 0.2 * ent['p'].area and tyears[i] > ent['last']]
                if ys:
                    ent.update(to=min(ys), evidence='rebuilt')
            if ent['to'] is None:
                ys = [y for r, y in roads if r.intersects(ent['p']) and y > ent['last']]
                if ys:
                    ent.update(to=min(ys), evidence='highway')
            if ent['to'] is None:
                ent.update(to=max(ASSUMED_END, ent['last'] + 1), evidence='assumed')
            entities.append(ent)
    feats = []
    for k, e in enumerate(entities):
        pr = e['f']['properties']
        feats.append({'type': 'Feature', 'properties': {'id': f'sanborn-{e["first"]}-{k}', 'from': e['first'], 'lastSeen': e['last'], 'to': e['to'],
                      'end': e['evidence'], 'material': pr['material'], 'storeys': pr['storeys'], 'sheet': pr['sheet'], 'edition': pr['edition']},
                      'geometry': e['f']['geometry']})
    covers = []
    for ed in eds:
        for c in ed['cover']:
            covers.append(ed['year'])
    json.dump({'type': 'FeatureCollection', 'editions': [e['year'] for e in eds], 'features': feats}, open(out, 'w'))
    from collections import Counter
    print(len(feats), 'lost buildings;', Counter(f['properties']['end'] for f in feats))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(*args, respect_years='--respect-years' in sys.argv, strict_link='--strict-link' in sys.argv)
