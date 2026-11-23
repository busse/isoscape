#!/usr/bin/env python3
"""The guide's vantage points: numbered places to stand and look, in no required order, each on a
public sidewalk mapped in OpenStreetMap (the region's cache), written to vantage.json for the maps,
the pairs, the page and the folded sheet.

    python3 tools/stories/jackson-ward-guide/vantage.py

The numbers run west to east and are only for finding the places. There is no route: readers go
between them as they choose. Each point is placed on its named sidewalk (`way`) at the
projection of its target, and checked:

  - it is not inside, or within 2 m of, the approximate Gilpin Court outline (gilpin.py);
  - it can be reached from the ordinary streets around it without crossing a motorway, a trunk
    road or their ramps, or a primary road, except at a crossing OpenStreetMap tags
    crossing=traffic_signals: its sidewalk lies in the largest connected part of the graph of
    OSM's sidewalks, footways and crossings with every other such crossing left out (`graph`,
    the rules the guide's earlier walking route used). Crossings are judged against the road
    they cross on the same level, so a bridge's sidewalk is not taken for a crossing of the
    highway under it.

Each point says where to stand (the corner and the side of the street), which way to look
(`face`, degrees from north, drawn as a view cone on the maps), and what is in view today (plain
map facts). What the 1952 sheets show there, and the history, are in story.md with the story's
sources. Points considered and dropped are listed in DROPPED with the reason.
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

GILPIN_CLEAR_M = 0.5  # no step of the graph this close to the Gilpin Court outline
OSM_DATE = 'November 16, 2026'   # when the region's OSM cache was fetched (data/richmond-streetcars)
BBOX = (-77.452, -77.424, 37.540, 37.560)
ROADS = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary',
         'secondary_link', 'tertiary', 'tertiary_link', 'residential', 'unclassified', 'service', 'living_street'}
FAST = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link'}
FOOTWAY_KINDS = {'sidewalk', 'crossing', 'link', 'traffic_island', 'refuge_island', None, 'path'}

# Vantage points, by key: the sidewalk (OSM way), a target near the spot in plan meters, the way
# to look (degrees from north; a second bearing where the text says to look both ways), and the
# words: where to stand and what is in view today. Numbers are given west to east in main().
VANTAGE = [
    dict(key='belvidere-extension', title='Chamberlayne Avenue\'s bridges from West Leigh Street', way=1121057677, xy=(-530, 86), face=[345],
         where='on the north sidewalk of West Leigh Street just west of Brook Road',
         sees='north and northwest to the two curved bridges that carry Chamberlayne Avenue over Brook Road and the railroad'),
    dict(key='gilpin-edge', title='Gilpin Court from Chamberlayne Avenue', way=1215813972, xy=(-328.8, 235.5), face=[70],
         where='on the west sidewalk of Chamberlayne Avenue at West Charity Street',
         sees='east across the avenue at Gilpin Court'),
    dict(key='chamberlayne-bridge', title='Chamberlayne Parkway bridge', way=1122219208, xy=(-296.2, 98.4), face=[110, 290],
         where='on the west sidewalk of the Chamberlayne Parkway bridge, about halfway across',
         sees='east along the highway in its trench toward the North 1st Street bridge, then west toward Belvidere Street'),
    dict(key='sixth-mount-zion', title='Sixth Mount Zion, and where Saint James Street ends', way=1483868750, xy=(-76.0, -29.0), face=[0, 60],
         where='on the south sidewalk of West Duval Street, across from the church',
         sees='north at Sixth Mount Zion Baptist Church with the highway behind it, then northeast to the corner of West Duval and '
              'Saint James Streets, about 60 m east, where Saint James Street ends at the trench'),
    dict(key='second-leigh', title='Second Street at Leigh Street', way=1205384874, xy=(20.5, -331.7), face=[215, 35],
         where='on the northeast corner of North 2nd and East Leigh Streets, across Leigh Street from Eggleston Plaza',
         sees='south down 2nd Street toward Clay and Broad Streets, then north up 2nd Street toward the highway'),
    dict(key='first-bridge', title='North 1st Street bridge', way=1485475447, xy=(125.6, -31.0), face=[115, 295],
         where='on the east sidewalk of the North 1st Street bridge, about halfway across',
         sees='east along the trench toward where 2nd Street ends on each side, then west toward the Chamberlayne Parkway bridge'),
    dict(key='second-trench', title='Where Second Street ends, south of the trench', way=1205384865, xy=(160.3, -118.3), face=[40],
         where='on the west sidewalk of North 2nd Street at its north end, where it meets East Duval Street',
         sees='north across the highway to where 2nd Street starts again'),
    dict(key='coliseum', title='The Coliseum site', way=1125516638, xy=(326.0, -559.7), face=[200],
         where='on the north sidewalk of East Leigh Street, across the street from the Coliseum',
         sees='south across East Leigh Street at the Richmond Coliseum'),
    dict(key='bates-street', title='Bates Street, and where Second Street starts again', way=1306725612, xy=(329.6, 75.2), face=[130, 220],
         where='at the corner of North 2nd and East Bates Streets, on the east side of 2nd',
         sees='southeast along Bates Street, then southwest down 2nd Street to where it ends at the trench'),
    dict(key='fifth-bridge', title='North 5th Street bridge', way=1293548427, xy=(407, -205), face=[115, 295],
         where='on the west sidewalk of the North 5th Street bridge, about halfway across',
         sees='east along the trench toward the North 7th Street bridge, then west toward the North 1st Street bridge'),
]
# Considered and left out, with the reason (said in orientation.md).
DROPPED = {
    'saint-james-north': 'Where Saint James Street ends north of the trench: its only mapped sidewalk there is not joined to the '
                         'streets around it by mapped sidewalks and crossings, and it is 59 m from the Gilpin Court outline.',
    'saint-james-south': 'Where Saint James Street ends south of the trench: 60 m from the Sixth Mount Zion point on the same '
                         'street, so the two are one point, with both views.',
    'second-north': 'Where Second Street ends north of the trench: no mapped sidewalk within 40 m of its end; the Bates Street '
                    'point, about 130 m north, looks down 2nd Street to it.',
    'seventh-bridge': 'The North 7th Street bridge: no mapped sidewalk where it crosses the trench is reachable by mapped sidewalks '
                      'and crossings.',
}


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
            G.add_edge(a, b, d=d, w=d + extra / n, way=e['id'])
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




def main():
    import networkx as nx
    net = Net()
    G, info = graph(net)
    main_part = max(nx.connected_components(G), key=len)
    pts = []
    for v in VANTAGE:
        s = dict(v, target=to_ll(*v['xy']), n=0)
        node, xy, d = place_stop(G, s)
        assert not net.gilpin.buffer(2).contains(Point(xy)), v['key'] + ' is inside the Gilpin Court outline'
        reach = any(nb in main_part for nb in G.neighbors(node))
        assert reach, v['key'] + ' cannot be reached without an unsafe crossing'
        lon, lat = to_ll(*xy)
        pts.append(dict({k: x for k, x in v.items() if k not in ('xy', 'way')}, lon=round(lon, 6), lat=round(lat, 6),
                        xy=[round(xy[0], 1), round(xy[1], 1)], on_way=f"w{v['way']}", snapped_m=round(d, 1),
                        gilpin_m=round(net.gilpin.distance(Point(xy)), 1)))
    pts.sort(key=lambda p: p['xy'][0])
    sys.path.insert(0, HERE)
    from orient import grid_of
    for i, p in enumerate(pts):
        p['n'] = i + 1
        p['square'] = grid_of(*p['xy'])
    json.dump(dict(about=__doc__.strip(), osm_date=OSM_DATE, points=pts, dropped=DROPPED), open(os.path.join(HERE, 'vantage.json'), 'w'), indent=1)
    for p in pts:
        print(p['n'], p['square'], p['key'], p['xy'], p['on_way'], 'snapped', p['snapped_m'], 'gilpin', p['gilpin_m'])


if __name__ == '__main__':
    main()
