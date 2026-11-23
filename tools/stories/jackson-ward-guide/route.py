#!/usr/bin/env python3
"""The guide's stops and walking route, from OpenStreetMap (the region's cache), written to
route.json for the maps, the pairs, the page and the folded sheet.

    python3 tools/stories/jackson-ward-guide/route.py [--audit FILE.md]

The walk keeps to what OpenStreetMap maps for people on foot: sidewalks, footways, mapped
crossings and pedestrian ways (never a road's center line, never a path tagged informal, never
private or foot=no). Rules a careful person would keep for strangers:

  - a crossing of a motorway or trunk road or its ramps, or of a primary road, is used only
    where OSM tags it crossing=traffic_signals; any other is left out of the graph;
  - a footway that crosses a street without being mapped as a crossing counts as an unmarked
    crossing of that street, under the same rules;
  - no step of the walk touches the approximate Gilpin Court outline (gilpin.py; tested on
    every step of the drawn line, within GILPIN_CLEAR_M), and a step within GILPIN_NEAR_M of it
    counts ten times its length, so the walk keeps to the far sidewalk where the outline meets a
    street and comes near it only to cross;
  - among walks that keep these rules, the shortest, with a crossing counted longer than it is
    (CROSS_COST: a signal costs least, then a marked crosswalk, then an unmarked one; more for
    a bigger street), so the walk takes a signal where one is near.

Crossings are judged against the road they cross on the same level (bridges and tunnels apart).
Each stop is a point on a named sidewalk (`way`), placed at the projection of its target.
Distances are along the drawn line, which is the sidewalks' own geometry. The directions between
stops are written from the walk's steps (`describe`): each sidewalk is named by the street it runs
beside (the nearest named road within 25 m running the same way), its side by which way it lies
from that road, crossings by their tags. With --audit, writes the per-leg audit (sidewalk sides,
every crossing with its OSM tags) as Markdown.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, load, osm, to_ll, to_m  # noqa: E402

import networkx as nx  # noqa: E402
from shapely.geometry import LineString, Point, Polygon  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

WALK_M_PER_MIN = 80   # about 3 mph, for the time hint (an assumption, said so on the page)
GILPIN_CLEAR_M = 0.5  # no step of the walk this close to the Gilpin Court outline
GILPIN_NEAR_M = 8     # a step this close counts ten times its length, so the walk takes the far sidewalk
OSM_DATE = 'November 16, 2026'   # when the region's OSM cache was fetched (data/richmond-streetcars)
BBOX = (-77.452, -77.424, 37.540, 37.560)
ROADS = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary',
         'secondary_link', 'tertiary', 'tertiary_link', 'residential', 'unclassified', 'service', 'living_street'}
FAST = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link'}
BRIDGE_STOPS = {'first-bridge', 'chamberlayne-bridge'}
FOOTWAY_KINDS = {'sidewalk', 'crossing', 'link', 'traffic_island', 'refuge_island', None, 'path'}

# Stops in walking order. `way` is the OSM sidewalk the walker stands on; `target` is near the
# spot. Bearings (`face`) are the direction the walker looks, 0 = north.
STOPS = [
    dict(key='second-leigh', title='Second Street at Leigh Street', way=1205384874, target=(-77.437268, 37.547500), face=215,
         where='on the northeast corner of North 2nd and East Leigh Streets, across Leigh Street from Eggleston Plaza',
         sees='south down 2nd Street toward Clay and Broad Streets'),
    dict(key='second-trench', title='Where Second Street stops', way=1205384865, target=(-77.435700, 37.549440), face=40,
         where='on the west sidewalk of North 2nd Street at its north end, where it meets East Duval Street by the highway',
         sees='north across I-95 to where 2nd Street starts again'),
    dict(key='first-bridge', title='North 1st Street bridge', way=1485475447, target=(-77.436077, 37.550220), face=115,
         where='on the east sidewalk of the North 1st Street bridge, about halfway across',
         sees='east along the trench, toward the cut ends of 2nd Street and Navy Hill beyond'),
    dict(key='bates-street', title='Bates Street and the JXN Haus', way=1306725612, target=(-77.433766, 37.551180), face=130,
         where='at the corner of North 2nd and East Bates Streets, on the east side of 2nd',
         sees='southeast along Bates Street'),
    dict(key='sixth-mount-zion', title='Sixth Mount Zion Baptist Church', way=1483868750, target=(-77.438362, 37.550238), face=0,
         where='on the south sidewalk of West Duval Street, across from the church',
         sees='north at Sixth Mount Zion Baptist Church, with the highway behind it'),
    dict(key='chamberlayne-bridge', title='Chamberlayne Parkway bridge', way=1122219208, target=(-77.440855, 37.551390), face=110,
         where='on the west sidewalk of the Chamberlayne Parkway bridge, about halfway across',
         sees='east across the bridge and along the trench toward the North 1st Street bridge'),
    dict(key='gilpin-edge', title='Gilpin Court, where Apostle Town stood', way=1215813972, target=(-77.441226, 37.552630), face=70,
         where='on the west sidewalk of Chamberlayne Avenue at West Charity Street',
         sees='east across the avenue at Gilpin Court'),
    dict(key='coliseum', title='The Coliseum site', way=1125516638, target=(-77.433807, 37.545438), face=200,
         where='on the north sidewalk of East Leigh Street, across the street from the Coliseum',
         sees='south across East Leigh Street at the Richmond Coliseum'),
]
for i, s in enumerate(STOPS):
    s['n'] = i + 1


def lay(t):
    """A way's level: its layer tag, else 1 on a bridge, -1 in a tunnel, 0 on the ground."""
    try:
        return int(t.get('layer', 1 if t.get('bridge') not in (None, 'no') else (-1 if t.get('tunnel') not in (None, 'no') else 0)))
    except ValueError:
        return 0


def inbox(g):
    lon = sum(q['lon'] for q in g) / len(g)
    lat = sum(q['lat'] for q in g) / len(g)
    return BBOX[0] < lon < BBOX[1] and BBOX[2] < lat < BBOX[3]


class Net:
    def __init__(self):
        self.foot, self.roads = [], []
        for e in osm():
            t = e.get('tags', {})
            if e['type'] != 'way' or not e.get('geometry') or not inbox(e['geometry']):
                continue
            pts = [to_m(q['lon'], q['lat']) for q in e['geometry']]
            if t.get('highway') in ROADS:
                self.roads.append((e, pts))
            elif t.get('highway') in ('footway', 'pedestrian', 'steps', 'path'):
                self.foot.append((e, pts))
        self.rlines = [LineString(p) for _, p in self.roads]
        self.rtree = STRtree(self.rlines)
        self.gilpin = Polygon([to_m(*q) for q in load('gilpin-outline.json')['outline_lonlat']])

    def crossed(self, pts, tags):
        L, l0 = LineString(pts), lay(tags)
        return [self.roads[i][0] for i in self.rtree.query(L)
                if self.rlines[i].intersects(L) and lay(self.roads[i][0]['tags']) == l0]

    def beside(self, a, b):
        """The named road a sidewalk step runs beside: nearest within 25 m whose direction is
        within 30 degrees of the step's; returns (road element, side word) or (None, None)."""
        mid = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        hd = math.atan2(b[1] - a[1], b[0] - a[0])
        best = None
        for i in self.rtree.query(mid.buffer(25)):
            e = self.roads[i][0]
            if not e['tags'].get('name') or e['tags'].get('highway') in ('service', 'motorway', 'motorway_link'):
                continue
            L = self.rlines[i]
            d = L.distance(mid)
            if d > 25:
                continue
            s = L.project(mid)
            p, q = L.interpolate(max(0, s - 3)), L.interpolate(min(L.length, s + 3))
            rd = math.atan2(q.y - p.y, q.x - p.x)
            diff = abs((hd - rd + math.pi / 2) % math.pi - math.pi / 2)
            if diff > math.radians(30):
                continue
            if best is None or d < best[0]:
                on = L.interpolate(s)
                best = (d, e, (mid.x - on.x, mid.y - on.y), (q.x - p.x, q.y - p.y))
        if best is None:
            return None, None
        _, e, off, rdir = best
        return e, side_word(rdir, off)


def axis(dx, dy):
    """'ns' for a street running nearer north-south (its sides are east and west), else 'ew'."""
    b = math.degrees(math.atan2(dx, dy)) % 180
    return 'ns' if b < 45 or b >= 135 else 'ew'


def side_word(rdir, off):
    if axis(*rdir) == 'ns':
        return 'east' if off[0] > 0 else 'west'
    return 'north' if off[1] > 0 else 'south'


def heading(dx, dy, ax):
    if ax == 'ns':
        return 'north' if dy > 0 else 'south'
    return 'east' if dx > 0 else 'west'


def crossing_cost(tags, crossed):
    """Extra meters for a crossing, or None where the walk must not cross."""
    kinds = {r['tags'].get('highway') for r in crossed}
    c = tags.get('crossing')
    if c == 'traffic_signals':
        return 10
    if kinds & FAST:
        return None
    marked = c in ('marked', 'zebra') or tags.get('crossing:markings') not in (None, 'no')
    if kinds & {'secondary', 'secondary_link'}:
        return 150 if marked else 250
    if kinds & {'tertiary', 'tertiary_link'}:
        return 40 if marked else 80
    if kinds - {'service'}:
        return 15 if marked else 30
    return 5


def graph(net):
    G = nx.Graph()
    zone = net.gilpin.buffer(GILPIN_CLEAR_M)
    near = net.gilpin.buffer(GILPIN_NEAR_M)
    info = {}
    for e, pts in net.foot:
        t = e['tags']
        if t.get('informal') == 'yes' or t.get('access') in ('private', 'no') or t.get('foot') == 'no':
            continue
        if t.get('highway') == 'footway' and t.get('footway') not in FOOTWAY_KINDS:
            continue
        cr = net.crossed(pts, t)
        extra = 0
        if t.get('footway') == 'crossing' or t.get('crossing'):
            extra = crossing_cost(t, cr)
        elif cr and t.get('highway') != 'steps':
            extra = crossing_cost({'crossing': 'unmarked'}, cr)
        if extra is None:
            continue
        if t.get('highway') == 'steps':
            extra += 30
        info[e['id']] = (t, cr)
        n = len(pts) - 1
        for a, b, p, q in zip(e['nodes'][:-1], e['nodes'][1:], pts[:-1], pts[1:]):
            if LineString([p, q]).intersects(zone):
                continue
            d = math.dist(p, q)
            G.add_node(a, xy=p)
            G.add_node(b, xy=q)
            G.add_edge(a, b, d=d, w=d * (10 if LineString([p, q]).intersects(near) else 1) + extra / n, way=e['id'])
    return G, info


def place_stop(G, s):
    """Put the stop on its sidewalk, splitting the nearest step of that way at the target."""
    xy = Point(to_m(*s['target']))
    best = None
    for a, b, k in G.edges(data=True):
        if k['way'] != s['way']:
            continue
        L = LineString([G.nodes[a]['xy'], G.nodes[b]['xy']])
        d = L.distance(xy)
        if best is None or d < best[0]:
            best = (d, a, b, L)
    assert best, f"stop {s['n']}: way {s['way']} is not in the walking graph"
    d, a, b, L = best
    assert d < 25, f"stop {s['n']} is {d:.0f} m from its sidewalk"
    q = L.interpolate(L.project(xy))
    k = dict(G.edges[a, b])
    G.remove_edge(a, b)
    node = f"stop{s['n']}"
    G.add_node(node, xy=(q.x, q.y))
    for u in (a, b):
        dd = math.dist(G.nodes[u]['xy'], (q.x, q.y))
        G.add_edge(u, node, d=dd, w=dd * k['w'] / max(k['d'], 1e-9), way=k['way'])
    return node, (q.x, q.y), d


def describe(G, info, net, path):
    """The leg as steps: runs along a street's sidewalk, and crossings, with their OSM tags."""
    steps = []
    for u, v in zip(path[:-1], path[1:]):
        k = G.edges[u, v]
        t, cr = info[k['way']]
        a, b = G.nodes[u]['xy'], G.nodes[v]['xy']
        # a crossing: mapped as one, or a short footway (not a sidewalk) over a road; a sidewalk
        # that runs over a driveway or an alley stays a sidewalk
        is_cross = bool(cr) and (t.get('footway') == 'crossing' or bool(t.get('crossing'))
                                 or (t.get('footway') != 'sidewalk' and LineString([a, b]).length < 30))
        if is_cross:
            names = []
            for r in cr:
                nm = r['tags'].get('name') or ('a driveway' if r['tags'].get('highway') == 'service' else r['tags'].get('highway'))
                if nm not in names:
                    names.append(nm)
            key = ('cross', k['way'])
            if steps and steps[-1]['key'] == key:
                steps[-1]['m'] += k['d']
                continue
            steps.append(dict(key=key, kind='cross', way=k['way'], m=k['d'], streets=names,
                              road_ids=[r['id'] for r in cr],
                              roads=[dict(id=r['id'], name=r['tags'].get('name'), highway=r['tags'].get('highway'),
                                          lanes=r['tags'].get('lanes'), maxspeed=r['tags'].get('maxspeed')) for r in cr],
                              tags={x: t[x] for x in ('crossing', 'crossing:markings', 'crossing:signals', 'crossing:island',
                                                      'tactile_paving', 'kerb') if x in t},
                              driveway=all(r['tags'].get('highway') == 'service' for r in cr)))
            continue
        road, side = net.beside(a, b)
        street = road['tags']['name'] if road else None
        ax = axis(b[0] - a[0], b[1] - a[1]) if road is None else None
        key = ('walk', street, side, t.get('bridge') == 'yes')
        if steps and steps[-1]['key'] == key:
            s = steps[-1]
            s['m'] += k['d']
            s['to'] = b
            s['ways'].append(k['way']) if s['ways'][-1] != k['way'] else None
            continue
        steps.append(dict(key=key, kind='walk', street=street, side=side, bridge=t.get('bridge') == 'yes',
                          frm=a, to=b, m=k['d'], ways=[k['way']], footway=t.get('footway')))
    # fold very short unnamed links (curb ramps, corner joins) into their neighbours' count
    for s in steps:
        s.pop('key')
        if s['kind'] == 'walk':
            dx, dy = s['to'][0] - s['frm'][0], s['to'][1] - s['frm'][1]
            s['heading'] = heading(dx, dy, axis(dx, dy))
    return steps


def round_m(m):
    return int(round(m, -1)) if m >= 30 else None


def cond(s):
    """What OSM maps at a crossing, in a few words."""
    t = s['tags']
    if t.get('crossing') == 'traffic_signals':
        return 'signal'
    if t.get('crossing') in ('marked', 'zebra') or t.get('crossing:markings') not in (None, 'no'):
        return 'marked crosswalk, no signal'
    if t.get('crossing') == 'uncontrolled':
        return 'crosswalk, no signal'
    return 'no marked crosswalk'


PLURAL = {'signal': 'signals', 'marked crosswalk, no signal': 'marked crosswalks, no signals',
          'crosswalk, no signal': 'crosswalks, no signals', 'no marked crosswalk': 'no marked crosswalks'}


def streets(names):
    """'Price Street' and 'West Jackson Street' -> 'Price and West Jackson Streets'."""
    if len(names) > 1 and all(n.endswith(' Street') for n in names):
        bare = [n[:-len(' Street')] for n in names]
        return (', '.join(bare[:-1]) + ' and ' + bare[-1]) + ' Streets'
    return ', '.join(names[:-1]) + ' and ' + names[-1] if len(names) > 1 else names[0]


def crossings(group):
    """[(names, cond), ...] -> 'A and B (no marked crosswalks)' or 'A (signal), then B (...)'."""
    conds = {c for _, c in group}
    names = [n for ns, _ in group for n in ns]
    if len(conds) == 1:
        c = conds.pop()
        return f"{streets(names)} ({PLURAL[c] if len(names) > 1 else c})"
    return ', then '.join(f"{streets(ns)} ({c})" for ns, c in group)


def directions(steps, frm, to):
    """Plain wayfinding, written from the steps: runs along one side of one street become one
    sentence; a cross street passed on the way is named; crossings of the street walked along, or
    onto another, are said with what OSM maps there. Driveways are left out."""
    out = []
    items = [dict(s) for s in steps if not (s['kind'] == 'cross' and s['driveway'])]
    # a short run at a corner (under SHORT m) is part of the run before it, or after it
    SHORT = 20
    changed = True
    while changed:
        changed = False
        for i, it in enumerate(items):
            if it['kind'] != 'walk' or it['m'] >= SHORT:
                continue
            prev = items[i - 1] if i > 0 and items[i - 1]['kind'] == 'walk' else None
            nxt = items[i + 1] if i + 1 < len(items) and items[i + 1]['kind'] == 'walk' else None
            if prev or nxt or i == 0 or i == len(items) - 1:
                (prev or nxt or {}).__setitem__('m', (prev or nxt or {'m': 0})['m'] + it['m'])
                items.pop(i)
                changed = True
                break
    runs = []
    for s in items:
        if s['kind'] == 'cross':
            along = runs[-1].get('street') if runs and runs[-1]['kind'] == 'walk' else None
            minor = {'Avenue A', 'Avenue B', 'Avenue C', 'Avenue D'}
            names = [n for n in s['streets'] if n not in minor] or s['streets']
            names = [n for n in names if n != along] or names
            s = dict(s, streets=names)
        if s['kind'] == 'walk' and runs and runs[-1]['kind'] == 'walk' and runs[-1]['street'] == s['street'] and runs[-1]['side'] == s['side']:
            runs[-1]['m'] += s['m']
            runs[-1]['bridge'] = runs[-1]['bridge'] or s['bridge']
            continue
        if (s['kind'] == 'walk' and len(runs) >= 2 and runs[-1]['kind'] == 'cross' and runs[-2]['kind'] == 'walk'
                and runs[-2]['street'] == s['street'] and runs[-2]['side'] == s['side'] and s['street']
                and s['street'] not in runs[-1]['streets']):
            c = runs.pop()
            runs[-1]['m'] += c['m'] + s['m']
            runs[-1].setdefault('past', []).append((c['streets'], cond(c)))
            runs[-1]['bridge'] = runs[-1]['bridge'] or s['bridge']
            continue
        runs.append(dict(s))
    # consecutive crossings make one sentence
    merged = []
    for r in runs:
        if r['kind'] == 'cross' and merged and merged[-1]['kind'] == 'cross':
            merged[-1]['group'].append((r['streets'], cond(r)))
            continue
        if r['kind'] == 'cross':
            r = dict(r, group=[(r['streets'], cond(r))])
        merged.append(r)
    runs = merged
    for i, r in enumerate(runs):
        if r['kind'] == 'cross':
            g = r['group']
            if all(c == 'signal' for _, c in g):
                out.append(f"Cross {streets([n for ns, _ in g for n in ns])} at the {'signals' if len(g) > 1 else 'signal'}.")
            else:
                out.append(f"Cross {crossings(g)}.")
            continue
        m = round_m(r['m'])
        if r['street'] is None:
            if m:
                out.append(f"Follow the sidewalk {r['heading']} for about {m} m.")
            continue
        what = f"the {r['side']} sidewalk of {r['street']}"
        if r['bridge']:
            last = all(x['kind'] != 'walk' for x in runs[i + 1:])
            first = all(x['kind'] != 'walk' for x in runs[:i])
            if last and to['key'] in BRIDGE_STOPS:
                what += ', onto the bridge over the highway,'
            elif first and frm['key'] in BRIDGE_STOPS:
                what += ', off the bridge,'
            else:
                what += ', across the bridge over the highway,'
        line = (f"Walk {r['heading']} on {what}" + (f" for about {m} m" if m else '')).rstrip(',')
        if r.get('past'):
            line += ', crossing ' + crossings([(n, c) for n, c in r['past']])
        out.append(line + '.')
    return out


def gilpin_overlap(net, coords):
    return net.gilpin.intersection(LineString(coords)).length


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--audit', default=None)
    a = ap.parse_args()
    net = Net()
    G, info = graph(net)
    out, nodes = [], []
    for s in STOPS:
        node, xy, d = place_stop(G, s)
        assert not net.gilpin.buffer(2).contains(Point(xy)), s['key'] + ' falls inside the Gilpin Court outline'
        lon, lat = to_ll(*xy)
        nodes.append(node)
        out.append(dict({k: v for k, v in s.items() if k not in ('target', 'way')}, lon=round(lon, 6), lat=round(lat, 6),
                        xy=[round(xy[0], 1), round(xy[1], 1)], on_way=f"w{s['way']}", snapped_m=round(d, 1)))
    legs, path = [], []
    for (a_, na), (b_, nb) in zip(zip(out, nodes), list(zip(out, nodes))[1:]):
        p = nx.shortest_path(G, na, nb, weight='w')
        d = sum(G.edges[u, v]['d'] for u, v in zip(p[:-1], p[1:]))
        coords = [list(G.nodes[n]['xy']) for n in p]
        inside = gilpin_overlap(net, coords)
        assert inside == 0, f"leg {a_['n']}->{b_['n']} runs {inside:.1f} m inside the Gilpin Court outline"
        steps = describe(G, info, net, p)
        for s in steps:
            if s['kind'] == 'cross':
                assert s['tags'].get('crossing') == 'traffic_signals' or not any(r['highway'] in FAST for r in s['roads']), s
        legs.append(dict(frm=a_['n'], to=b_['n'], m=round(d), minutes=max(1, round(d / WALK_M_PER_MIN)), inside_gilpin_m=0,
                         directions=directions(steps, a_, b_),
                         steps=[{k: (([round(v[0], 1), round(v[1], 1)]) if k in ('frm', 'to') else (round(v) if k == 'm' else v))
                                 for k, v in s.items()} for s in steps]))
        path.append([[round(x, 1), round(y, 1)] for x, y in coords])
    total = sum(l['m'] for l in legs)
    back = nx.shortest_path_length(G, nodes[-1], nodes[0], weight='d')
    res = dict(about=__doc__.strip(), osm_date=OSM_DATE, walk_m_per_min=WALK_M_PER_MIN, stops=out, legs=legs, path=path,
               total_m=total, total_minutes=round(total / WALK_M_PER_MIN), last_to_first_m=round(back),
               all_gilpin_overlap_m=round(gilpin_overlap(net, [q for leg in path for q in leg]), 2))
    json.dump(res, open(os.path.join(HERE, 'route.json'), 'w'), indent=1)
    for s in out:
        print(s['n'], s['title'], s['lat'], s['lon'], s['on_way'], s['snapped_m'])
    for l in legs:
        print(f"{l['frm']}->{l['to']}: {l['m']} m")
        for line in l['directions']:
            print('   ', line)
    print('total', total, 'm; back to start', round(back), 'm; inside Gilpin', res['all_gilpin_overlap_m'], 'm')
    if a.audit:
        write_audit(a.audit, res)


def write_audit(fn, res):
    L = ['# Jackson Ward walking guide: the route, leg by leg', '',
         f"From OpenStreetMap as cached {res['osm_date']} (`data/richmond-streetcars/osm.json`), by `route.py`. "
         'A check against the map only: nobody has walked it for this audit.', '',
         f"Total {res['total_m']:,} m ({res['total_m'] / 1609.344:.1f} mi), about {round(res['total_m'] / res['walk_m_per_min'] / 5) * 5} "
         f"minutes at {res['walk_m_per_min']} m a minute. Stop 8 back to stop 1: {res['last_to_first_m']} m. "
         f"Length of the drawn line inside the Gilpin Court outline: {res['all_gilpin_overlap_m']} m.", '',
         '## Stops', '', '| Stop | Title | Stands on | Lat, lon |', '|---|---|---|---|']
    for s in res['stops']:
        L.append(f"| {s['n']} | {s['title']} | {s['on_way']} ({s['where']}) | {s['lat']}, {s['lon']} |")
    for l in res['legs']:
        L += ['', f"## Stop {l['frm']} to stop {l['to']}: {l['m']} m", '', '**Directions as printed:** ' + ' '.join(l['directions']), '',
              '| Step | OSM way | Length | Notes |', '|---|---|---|---|']
        for s in l['steps']:
            if s['kind'] == 'walk':
                where = f"{s['side']} sidewalk of {s['street']}" if s['street'] else f"footway ({s.get('footway') or 'unnamed'})"
                L.append(f"| walk {s['heading']}, {where}{', on the bridge' if s['bridge'] else ''} | "
                         f"{', '.join('w' + str(w) for w in s['ways'])} | {s['m']} m | |")
            else:
                roads = '; '.join(f"{r['name'] or 'unnamed'} (w{r['id']}, highway={r['highway']}"
                                  + (f", lanes={r['lanes']}" if r['lanes'] else '') + (f", maxspeed={r['maxspeed']}" if r['maxspeed'] else '') + ')'
                                  for r in s['roads'])
                tags = ', '.join(f'{k}={v}' for k, v in s['tags'].items()) or 'no crossing tags (a footway across the road)'
                L.append(f"| cross {roads} | w{s['way']} | {s['m']} m | {tags} |")
    # every crossing used, by what OSM maps there (driveways and alleys apart)
    seen = {}
    for l in res['legs']:
        for s in l['steps']:
            if s['kind'] == 'cross' and not s['driveway']:
                seen.setdefault(s['way'], (s, []))[1].append(f"{l['frm']}->{l['to']}")
    L += ['', '## Every street crossing on the walk', '',
          '| Crossing (OSM way) | Street | Tags | Legs |', '|---|---|---|---|']
    for w, (s, legs) in sorted(seen.items(), key=lambda kv: kv[1][1][0]):
        roads = '; '.join(f"{r['name'] or r['highway']} ({r['highway']}" + (f", {r['lanes']} lanes" if r['lanes'] else '') + ')' for r in s['roads'])
        L.append(f"| w{w} | {roads} | {', '.join(f'{k}={v}' for k, v in s['tags'].items()) or 'none'} | {', '.join(legs)} |")
    kinds = {}
    for s, _ in seen.values():
        kinds[s['tags'].get('crossing', 'untagged')] = kinds.get(s['tags'].get('crossing', 'untagged'), 0) + 1
    L += ['', 'Distinct street crossings by OSM tag: ' + ', '.join(f'{k} {v}' for k, v in sorted(kinds.items())) + '.',
          'No crossing of a motorway, a motorway ramp or a primary road without crossing=traffic_signals '
          '(route.py leaves those out of the graph and asserts it).']
    open(fn, 'w').write('\n'.join(L) + '\n')
    print('wrote', fn)


if __name__ == '__main__':
    main()
