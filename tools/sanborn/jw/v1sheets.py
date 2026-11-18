"""Add the buildings re-traced from the 1952 volume 1 sheets 2 and 3 (Adams Street to 4th
Street, Broad Street to Clay: Second Street's blocks) to the Jackson Ward lost layer, for the
Jackson Ward series only.

    python3 v1sheets.py <today's buildings.json> <drawn ids> <history/sanborn/lost.geojson> \
        <history/sanborn/jackson-ward-lost.geojson> traced/v1-0002.json traced/v1-0003.json

The downtown series traced these two sheets with the color tracer (tools/sanborn/extract.py),
which found few of their buildings standing in 1952; here trace52.py traced them again (fits in
geo1952v1.json from cps1952v1.json: street corners read off the 50% scans, residuals 0.5-2.9 m).
Only buildings whose center lies north of Broad Street's center line on the sheet are taken
(the Jackson Ward frame starts at Broad). Each one is, as in lifespans.py and uncovered.py:
  - left out if today's buildings cover half or more of it and the 1952 scene draws one of them
    (today's data already draws it);
  - left out if it overlaps by 30% a building of the earlier downtown tracing
    (history/sanborn/lost.geojson) standing in 1952, so one building is not drawn twice;
  - otherwise added, from 1952 (the sheet's date; it may be older) to the earliest year after 1952
    of today's buildings on its outline (end "rebuilt"), or, if none is dated, to 2026 where today's
    buildings cover half of it (it stands, undated) and to 1960 where they do not (end "assumed",
    the downtown series' rule).
Names, uses and stories read off the sheets come from named.csv (rows for sheets v1-0002 and
v1-0003) through finish-style matching: a row's point inside the outline. The file's own
ids start "jw1952v1-"; running again replaces them."""
import json, sys, os, csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.strtree import STRtree
from geo import to_m

EDITION, ASSUMED, PRESENT = 1952, 1960, 2026
BROAD_V = {'v1-0002': 1620, 'v1-0003': 1672}   # Broad Street's center on each 50% scan
CLAY_V = {'v1-0002': 113, 'v1-0003': 150}


def stories(s):
    """'3' -> 3; '1-2' (parts of 1 and 2 stories) -> 2, the main part; '' -> None."""
    nums = [int(x) for x in s.replace('-', ' ').replace(',', ' ').split() if x.isdigit()]
    return max(nums) if nums else None


def pm(ring):
    r = np.asarray(ring); x, y = to_m(r[:, 0], r[:, 1]); return Polygon(np.stack([x, y], 1)).buffer(0)


def main(today, drawn, older, lost, *traced):
    shown = {l.strip() for l in open(drawn) if l.strip()}
    olds = [pm(f['geometry']['coordinates'][0]) for f in json.load(open(older))['features']
            if f['properties']['from'] <= EDITION < f['properties']['to']]
    otree = STRtree(olds)
    tb = [b for b in json.load(open(today)) if len(b['ring']) >= 3]
    tp = [pm(b['ring']) for b in tb]
    k = [i for i, p in enumerate(tp) if not p.is_empty]
    tb, tp = [tb[i] for i in k], [tp[i] for i in k]
    tree = STRtree(tp)
    named = {}
    here = os.path.dirname(os.path.abspath(__file__))
    for r in csv.DictReader(open(os.path.join(here, 'named.csv'))):
        if r['sheet'].startswith('v1-'):
            named.setdefault(r['sheet'], []).append(r)
    lf = json.load(open(lost))
    lf['features'] = [f for f in lf['features'] if not f['properties']['id'].startswith('jw1952v1-')]
    stats = dict(added=0, today=0, twice=0, south=0)
    for path in traced:
        t = json.load(open(path)); sh = t['sheet']
        for i, b in enumerate(t['buildings']):
            uv = np.asarray(b['uv'])
            cv = Polygon(uv).representative_point().y
            if not (CLAY_V[sh] < cv < BROAD_V[sh]):
                stats['south'] += 1
                continue
            p = pm(b['ring'])
            if p.is_empty or p.area == 0:
                continue
            on = [j for j in tree.query(p) if tp[j].intersection(p).area > 0.05 * p.area]
            cover = sum(tp[j].intersection(p).area for j in on) / p.area
            if cover >= 0.5 and any(tb[j]['id'] in shown for j in on):
                stats['today'] += 1
                continue
            if any(olds[q].intersection(p).area > 0.3 * p.area for q in otree.query(p)):
                stats['twice'] += 1
                continue
            dated = [tb[j]['year'] for j in on if tb[j]['year'] is not None and tb[j]['year'] > EDITION]
            if dated:
                to, end = min(dated), 'rebuilt'
            elif cover >= 0.5:
                to, end = PRESENT, 'rebuilt'
            else:
                to, end = ASSUMED, 'assumed'
            props = {'id': f'jw1952{sh[:2]}-{int(sh[3:])}-{i + 1}', 'from': EDITION, 'lastSeen': EDITION, 'to': to, 'end': end,
                     'material': b['material'], 'storeys': 2, 'sheet': sh, 'edition': EDITION,
                     'color': b['color'], 'storeysFrom': 'assumed'}
            poly = Polygon(uv)
            for r in named.get(sh, []):
                if poly.contains(Point(float(r['u50']), float(r['v50']))):
                    props['name'] = r['name']; props['use'] = r['use']
                    st = stories(r.get('stories', ''))
                    if st:
                        props['storeys'] = st; props['storeysFrom'] = 'sheet'
            lf['features'].append({'type': 'Feature', 'properties': props,
                                   'geometry': {'type': 'Polygon', 'coordinates': [b['ring']]}})
            stats['added'] += 1
    json.dump(lf, open(lost, 'w'))
    print(stats)


if __name__ == '__main__':
    main(*sys.argv[1:])
