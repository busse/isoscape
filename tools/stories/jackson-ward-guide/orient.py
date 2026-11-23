#!/usr/bin/env python3
"""The guide's orientation data, from OpenStreetMap (the region's cache) and the story's trace:
the plan's frame and grid, every street named in it (today's, and the 1952 stretches the trench
cut), which streets cross the trench on a bridge and which end at it, the highway's numbered
exits, and the landmarks a driver knows. Written to orient.json for map.py, labels.py, page.py,
fold.py and claims.py.

    python3 tools/stories/jackson-ward-guide/orient.py

Plain map facts only; nothing about history.

- Frame (PLAN): north up, 1,500 m by 1,260 m, from Belvidere Street to past 7th Street and from
  Broad Street to the railroad. Grid: columns A-F west to east (250 m), rows 1-6 north to south
  (210 m), so a square is named like "C4".
- Today's streets: OSM ways with a name and a street's highway tag (residential to primary,
  unclassified, living street; and named service ways and pedestrian ways, which are the named
  alleys and plazas), clipped to the frame. The highway itself (motorway and ramps) is not a
  street here; it is named "I-95 / I-64".
- Bridges over the trench: ways tagged bridge that cross today's highway footprint (map.py's
  `gather`).
- Ends at the trench: an end of a street (its ways of one name merged) within ENDS_M of the
  highway footprint, outside it and not at a bridge, on a side of it (north or south).
- The 1952 streets: the story's trace (history/jackson-ward.json): the 24 stretches read off the
  1952 sheets (`lost52-`), and the 7 stretches of surviving streets joined straight across the
  trench as the USGS map of 1933-34 shows them (`lost-`). Where a 1952 stretch's line is followed
  today by a different named street (for at least FOLLOW_SHARE of its length within FOLLOW_M), the
  index says which.
- Exits: motorway ramps with an OSM `junction:ref`, named by their destination.
- Landmarks: OSM features by name and id, labels only.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, ROOT, osm, to_m  # noqa: E402

from shapely.geometry import LineString, Point, Polygon, box  # noqa: E402
from shapely.ops import linemerge, unary_union  # noqa: E402

PLAN = (-800, 700, -780, 480)          # x0, x1, y0, y1 in plan meters (common.to_m)
COLS, ROWS = 'ABCDEF', 6
ENDS_M = 45
FOLLOW_M, FOLLOW_SHARE = 10, 0.6
STREET = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'living_street', 'trunk'}
MINOR = {'service', 'pedestrian'}      # counted only when named
# Landmarks a driver knows that stand today, by OSM way id, with the label used on the maps.
LANDMARKS = {
    297832917: 'Sixth Mount Zion Baptist Church',
    1471758839: 'Ebenezer Baptist Church',
    297832946: 'Sharon Baptist Church',
    296796863: 'Greater Mount Moriah Baptist Church',
    297832945: 'Maggie L. Walker National Historic Site',
    182380774: 'Baker Public School',
    182382385: 'Calhoun Community Center',
    44888568: 'Greater Richmond Convention Center',
    321367756: 'Richmond Coliseum',
    266499307: 'Abner Clay Park',
    224757079: 'Blues Armory',
    45088999: 'J. Sargeant Reynolds Community College',
    224258003: 'VCU (Cabaniss Hall)',
}


def grid_of(x, y):
    """The grid square holding a point, or None outside the frame."""
    x0, x1, y0, y1 = PLAN
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return None
    c = min(COLS.__len__() - 1, int((x - x0) / ((x1 - x0) / len(COLS))))
    r = min(ROWS - 1, int((y1 - y) / ((y1 - y0) / ROWS)))
    return f'{COLS[c]}{r + 1}'


def squares(geom):
    out = set()
    for g in getattr(geom, 'geoms', [geom]):
        if g.is_empty:
            continue
        L = g if g.geom_type == 'LineString' else g.exterior
        n = max(2, int(L.length / 10))
        for i in range(n + 1):
            p = L.interpolate(i / n, normalized=True)
            s = grid_of(p.x, p.y)
            if s:
                out.add(s)
    return sorted(out, key=lambda s: (s[1], s[0]))


def span(sq):
    """['C5','C6','D3','D4','D5'] -> 'C5–C6, D3–D5': the squares, by column, runs joined."""
    if not sq:
        return ''
    out = []
    for c in COLS:
        rows = sorted(int(s[1:]) for s in sq if s[0] == c)
        i = 0
        while i < len(rows):
            j = i
            while j + 1 < len(rows) and rows[j + 1] == rows[j] + 1:
                j += 1
            out.append(f'{c}{rows[i]}' if i == j else f'{c}{rows[i]}–{c}{rows[j]}')
            i = j + 1
    return ', '.join(out)


def footprint():
    sys.path.insert(0, HERE)
    import map as M
    return M.gather(PLAN)['foot']


def main():
    frame = box(PLAN[0], PLAN[2], PLAN[1], PLAN[3])
    foot = footprint()
    ways, node_use = [], {}
    for e in osm():
        t = e.get('tags', {})
        if e['type'] != 'way' or not e.get('geometry'):
            continue
        h = t.get('highway')
        if h in STREET | MINOR | {'motorway', 'motorway_link', 'primary_link', 'secondary_link', 'tertiary_link'}:
            for n in e['nodes']:
                node_use[n] = node_use.get(n, 0) + 1
        if not t.get('name') or not (h in STREET or h in MINOR):
            continue
        pts = [to_m(q['lon'], q['lat']) for q in e['geometry']]
        if len(pts) < 2:
            continue
        L = LineString(pts)
        if not L.intersects(frame):
            continue
        ways.append((e, L))
    today = {}
    for e, L in ways:
        t = e['tags']
        d = today.setdefault(t['name'], dict(name=t['name'], parts=[], bridge=False, bridge_ways=[], ends=[], minor=True))
        d['parts'].append(L)
        d['minor'] = d['minor'] and t['highway'] in MINOR
        if t.get('bridge') in ('yes', 'viaduct') and L.intersects(foot):
            d['bridge'] = True
            d['bridge_ways'].append(e['id'])
    for name, d in today.items():
        u = unary_union(d['parts'])
        merged = linemerge(u) if u.geom_type == 'MultiLineString' else u
        for g in getattr(merged, 'geoms', [merged]):
            for p in (Point(g.coords[0]), Point(g.coords[-1])):
                if p.distance(foot) <= ENDS_M and frame.contains(p) and not foot.contains(p):
                    if any(L.distance(p) < 1 and L.intersects(foot) for L in d['parts']):
                        continue        # the end of a bridge's approach, not a dead end
                    from shapely.ops import nearest_points
                    q = nearest_points(foot, p)[0]
                    if any(math.dist(x['xy'], (p.x, p.y)) < 40 for x in d['ends']):
                        continue
                    d['ends'].append(dict(side='south' if q.y > p.y else 'north', xy=[round(p.x, 1), round(p.y, 1)],
                                          square=grid_of(p.x, p.y)))
    # the 1952 stretches
    h = json.load(open(os.path.join(ROOT, 'history/jackson-ward.json')))
    lost = []
    for f in h['features']:
        if f.get('kind') != 'street' or not (f['id'].startswith('lost-') or f['id'].startswith('lost52-')):
            continue
        L = LineString([to_m(*p) for p in f['line']])
        joined = f['id'].startswith('lost-')
        follow = None
        for name, d in today.items():
            if name == f['name']:
                continue
            near = unary_union(d['parts']).buffer(FOLLOW_M)
            share = L.intersection(near).length / L.length
            if share >= FOLLOW_SHARE and (follow is None or share > follow[1]):
                follow = (name, round(share, 2))
        sheet = None if joined else f['id'].split('-')[1]
        printed = f['name']
        note = f.get('note', '')
        if not joined and 'A stretch of ' in note and '(' in note.split(' inside')[0]:
            printed = note.split('A stretch of ')[1].split(' inside')[0]
        lost.append(dict(id=f['id'], name=f['name'], printed=printed, joined=joined, sheet=sheet, m=round(L.length),
                         line=[[round(x, 1), round(y, 1)] for x, y in L.coords], squares=squares(L),
                         followed_by=follow[0] if follow else None))
    # the index: one row per name
    index = {}
    for name, d in today.items():
        g = unary_union(d['parts']).intersection(frame)
        sq = squares(g)
        if not sq or g.length < 30:
            continue        # at least 30 m inside the frame, as map.py names them
        kinds = []
        if d['bridge']:
            kinds.append('today, crosses the trench on a bridge')
        sides = sorted({x['side'] for x in d['ends']})
        if sides and not d['bridge']:
            kinds.append('today, ends at the trench (' + ' and '.join(f'{s} side' for s in sides) + ')')
        elif sides:
            kinds.append('today, also ends at the trench (' + ' and '.join(f'{s} side' for s in sides) + ')')
        if not kinds:
            kinds.append('today')
        index[name] = dict(name=name, squares=sq, grid=span(sq), kinds=kinds, minor=d['minor'],
                           ends=d['ends'], bridge_ways=d['bridge_ways'])
    for s in lost:
        r = index.setdefault(s['name'], dict(name=s['name'], squares=[], grid='', kinds=[], minor=False, ends=[], bridge_ways=[]))
        if s['joined']:
            k = f"1952, the stretch under today's highway (about {s['m']} m), joined as the USGS map of 1933–34 shows it"
        else:
            k = (f"1952, cut by the trench: about {s['m']} m"
                 + (f" printed \"{s['printed']}\"" if s['printed'] != s['name'] else '') + f", Sanborn sheet {s['sheet']}")
        if s['followed_by']:
            k += f"; its line is followed today by {s['followed_by']}"
        r['kinds'].append(k)
        r['squares'] = sorted(set(r['squares']) | set(s['squares']), key=lambda q: (q[1], q[0]))
        r['grid'] = span(r['squares'])
    # bridges, exits, landmarks
    bridges = [dict(name=n, ways=d['bridge_ways'], squares=index[n]['squares']) for n, d in today.items() if d['bridge'] and n in index]
    exits = []
    for e in osm():
        t = e.get('tags', {})
        if e['type'] == 'way' and t.get('highway') == 'motorway_link' and t.get('junction:ref') and e.get('geometry'):
            L = LineString([to_m(q['lon'], q['lat']) for q in e['geometry']])
            if L.intersects(frame):
                dest = (t.get('destination') or '').split(';')
                to = next((x for x in dest if x.endswith((' Street', ' Avenue'))), dest[0])
                exits.append(dict(ref=t['junction:ref'], to=to, way=e['id'],
                                  label=f"Exit {t['junction:ref']}" + (f": {to.replace(' Street', ' St.').replace(' Avenue', ' Ave.')}" if to else ''),
                                  start=[round(v, 1) for v in L.coords[0]], line=[[round(x, 1), round(y, 1)] for x, y in L.coords]))
    marks = []
    for e in osm():
        if e['type'] == 'way' and e['id'] in LANDMARKS and e.get('geometry'):
            P = Polygon([to_m(q['lon'], q['lat']) for q in e['geometry']])
            c = P.representative_point()
            if frame.contains(c):
                marks.append(dict(id=e['id'], label=LANDMARKS[e['id']], osm_name=e['tags'].get('name'), xy=[round(c.x, 1), round(c.y, 1)],
                                  square=grid_of(c.x, c.y), outline=[[round(x, 1), round(y, 1)] for x, y in P.exterior.coords]))
    out = dict(about=__doc__.strip(), plan=PLAN, cols=COLS, rows=ROWS,
               index=[index[k] for k in sorted(index, key=sort_key)], lost=lost, bridges=bridges, exits=exits, landmarks=marks)
    json.dump(out, open(os.path.join(HERE, 'orient.json'), 'w'), indent=1)
    from collections import Counter
    c = Counter()
    for r in out['index']:
        for k in r['kinds']:
            c[k.split(':')[0].split(' (')[0].split(';')[0]] += 1
    print(len(out['index']), 'names;', dict(c))
    print('bridges:', [b['name'] for b in bridges])
    print('ends:', [(r['name'], [(x['side'], x['square']) for x in r['ends']]) for r in out['index'] if r['ends']])
    print('exits:', [x['label'] for x in exits])
    print('landmarks:', len(marks), [m['label'] for m in marks])


def sort_key(name):
    """Alphabetical by the street's own name: 'North 2nd Street' sorts under 2nd; 'East Leigh'
    under Leigh, with the direction after."""
    import re
    w = name.split()
    if w[0] in ('North', 'South', 'East', 'West') and len(w) > 1:
        base = ' '.join(w[1:])
    else:
        base = name
    base = base.replace('Saint ', 'St ')
    m = re.match(r'(\d+)', base)
    return (0, int(m.group(1)), name) if m else (1, base.lower(), name)


if __name__ == '__main__':
    main()
