"""After corridor_ends.py: put back the 1952 buildings that lifespans.py took to be standing today
(today's buildings cover half or more of the outline) but that the 1952 scene does not draw:
the buildings covering them are dated after 1952, or not dated at all (drawn today only). Left
as they were, they leave holes in the 1952 scene where the sheet shows a building (the
Hippodrome on Second Street, the Eggleston Hotel's block).

    python3 uncovered.py <edition file> <jackson-ward-lost.geojson> <today's buildings.json> <drawn ids> <history/sanborn/lost.geojson> [present]

<today's buildings.json> is `node tools/sanborn/dates.ts jackson-ward <out>` (each OSM building's year,
or null); <drawn ids> lists, one per line, the OSM ids the 1952 scene draws, read from its SVG
(`grep -o 'data-id="[wr][0-9]*'`), so "drawn in 1952" is what the renderer decided, not a guess.

Each is added to the lost file as the edition has it, ending (`to`) at the earliest year after 1952 of
the buildings now on its outline (end "rebuilt"), or at `present` (default 2026) where none is
dated: a building that stands today but has no year is then drawn traced until today's scene.
Names and stories come with it from the edition file. One that overlaps by 30% a building of the
earlier downtown tracing (history/sanborn/lost.geojson) standing in 1952 is left out, so the two
tracings do not draw one building twice (finish.py's rule, by area)."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from geo import to_m

EDITION = 1952


def pm(ring):
    r = np.asarray(ring); x, y = to_m(r[:, 0], r[:, 1]); return Polygon(np.stack([x, y], 1)).buffer(0)


def main(ed, lost, today, drawn, older, present='2026'):
    olds = [pm(f['geometry']['coordinates'][0]) for f in json.load(open(older))['features'] if f['properties']['from'] <= EDITION < f['properties']['to']]
    otree = STRtree(olds)
    twice = 0
    shown = {l.strip() for l in open(drawn) if l.strip()}
    lf = json.load(open(lost))
    have = {f['properties']['id'] for f in lf['features']}
    tb = [b for b in json.load(open(today)) if len(b['ring']) >= 3]
    tp = [pm(b['ring']) for b in tb]
    keep = [i for i, p in enumerate(tp) if not p.is_empty]
    tp = [tp[i] for i in keep]; tb = [tb[i] for i in keep]
    tree = STRtree(tp)
    added = []
    for f in json.load(open(ed))['features']:
        pr = f['properties']
        if pr.get('coverage') or pr['id'] in have:
            continue
        p = pm(f['geometry']['coordinates'][0])
        if p.is_empty or p.area == 0:
            continue
        on = [j for j in tree.query(p) if tp[j].intersection(p).area > 0.05 * p.area]
        cover = sum(tp[j].intersection(p).area for j in on) / p.area
        if cover < 0.5:
            continue  # lifespans.py left it out for another reason (dropped by the cleaning)
        years = [tb[j]['year'] for j in on]
        if any(tb[j]['id'] in shown for j in on):
            continue  # the 1952 scene draws a building of today on it
        if any(olds[i].intersection(p).area > 0.3 * p.area for i in otree.query(p)):
            twice += 1
            continue
        dated = [y for y in years if y is not None and y > EDITION]
        to = min(dated) if dated else int(present)
        props = {'id': pr['id'], 'from': EDITION, 'lastSeen': EDITION, 'to': to, 'end': 'rebuilt',
                 'material': pr['material'], 'storeys': pr['storeys'], 'sheet': pr['sheet'], 'edition': EDITION,
                 'color': pr['color'], 'storeysFrom': pr.get('storeysFrom', 'assumed')}
        for k in ('name', 'use', 'byEye'):
            if k in pr: props[k] = pr[k]
        lf['features'].append({'type': 'Feature', 'properties': props, 'geometry': f['geometry']})
        added.append((pr['id'], pr.get('name'), to))
    json.dump(lf, open(lost, 'w'))
    print(len(added), 'put back;', twice, 'left out as drawn by the downtown tracing;', sum(1 for a in added if a[1]), 'named:', [a[1] for a in added if a[1]])


if __name__ == '__main__':
    main(*sys.argv[1:])
