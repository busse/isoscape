#!/usr/bin/env python3
"""The guide's stops and walking route, from OpenStreetMap (the region's cache), written to
route.json for the map, the pairs and the page.

    python3 tools/stories/jackson-ward-guide/route.py

Each stop is given as a target near where a walker should stand; the target is moved to the
nearest point of a mapped sidewalk (OSM footway=sidewalk) within 25 m, or else onto the nearest
street, so every standing point is on a public way. The route between stops is the shortest
walk over OSM's streets, sidewalks and crossings (never the motorway or its ramps), with any
step inside the approximate Gilpin Court outline (gilpin.py) counted five times its length, so
the route keeps to the streets around it. Distances are along that walk.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, load, osm, to_ll, to_m  # noqa: E402

import networkx as nx  # noqa: E402
from shapely.geometry import LineString, Point, Polygon  # noqa: E402

WALK = {'footway', 'path', 'pedestrian', 'steps', 'residential', 'tertiary', 'secondary', 'primary',
        'unclassified', 'service', 'living_street', 'primary_link', 'secondary_link', 'tertiary_link', 'crossing', 'cycleway'}
SNAP_M = 25
GILPIN_WEIGHT = 5
WALK_M_PER_MIN = 80   # about 3 mph, for the time hint (an assumption, said so on the map)

# id, short title, target (lon, lat), what to face (bearing in degrees, 0 = north), and how the
# target was chosen. Bearings are the direction the walker looks.
STOPS = [
    dict(n=1, key='second-leigh', title='Second Street at Leigh Street',
         target=(-77.43730, 37.54752), face=225,
         where='at the corner of North 2nd and East Leigh Streets, on the east side of 2nd, by Eggleston Plaza',
         sees='south down 2nd Street toward Clay and Broad Streets'),
    dict(n=2, key='second-trench', title='Where Second Street stops',
         target=(-77.43545, 37.54952), face=45,
         where='at the north end of North 2nd Street, where it meets East Duval Street by the highway',
         sees='north across I-95 to where 2nd Street starts again'),
    dict(n=3, key='sixth-mount-zion', title='Sixth Mount Zion Baptist Church',
         target=None, face=0,
         where='on the south sidewalk of West Duval Street, across from the church',
         sees='north at Sixth Mount Zion Baptist Church, with the highway behind it'),
    dict(n=4, key='chamberlayne-bridge', title='Chamberlayne Parkway bridge',
         target=(-77.44072, 37.55138), face=110,
         where='on the east sidewalk of the Chamberlayne Parkway bridge, halfway across',
         sees='east along the trench toward the North 1st Street bridge'),
    dict(n=5, key='gilpin-edge', title='Gilpin Court, where Apostle Town stood',
         target=(-77.44128, 37.55262), face=70,
         where='on the west sidewalk of Chamberlayne Avenue at West Charity Street',
         sees='east across the avenue at Gilpin Court'),
    dict(n=6, key='bates-street', title='Bates Street and the JXN Haus',
         target=(-77.43378, 37.55115), face=120,
         where='at the corner of North 2nd and East Bates Streets',
         sees='east along Bates Street'),
    dict(n=7, key='first-bridge', title='North 1st Street bridge',
         target=(-77.43601, 37.55018), face=115,
         where='on the east sidewalk of the North 1st Street bridge, halfway across',
         sees='east along the trench, toward the cut ends of 2nd Street and Navy Hill beyond'),
    dict(n=8, key='coliseum', title='The Coliseum site',
         target=(-77.43365, 37.54560), face=200,
         where='on the sidewalk of East Leigh Street beside the Coliseum',
         sees='south at the Richmond Coliseum'),
]

CHURCH_WAY = 297832917   # Sixth Mt Zion Baptist Church, 14 West Duval Street (OSM)


def graph():
    G = nx.Graph()
    ways = []
    for e in osm():
        t = e.get('tags', {})
        if e['type'] != 'way' or t.get('highway') not in WALK or t.get('foot') == 'no' or t.get('access') == 'private':
            continue
        g = e.get('geometry') or []
        if not g:
            continue
        lon0 = sum(q['lon'] for q in g) / len(g)
        lat0 = sum(q['lat'] for q in g) / len(g)
        if not (-77.452 < lon0 < -77.424 and 37.540 < lat0 < 37.560):
            continue
        pts = [to_m(q['lon'], q['lat']) for q in g]
        ways.append((e, pts))
        for a, b, p, q in zip(e['nodes'][:-1], e['nodes'][1:], pts[:-1], pts[1:]):
            G.add_node(a, xy=p)
            G.add_node(b, xy=q)
            G.add_edge(a, b, d=math.dist(p, q), way=e['id'])
    return G, ways


def snap(target_xy, ways):
    p = Point(target_xy)
    best = None
    for e, pts in ways:
        if e['tags'].get('footway') != 'sidewalk' or len(pts) < 2:
            continue
        L = LineString(pts)
        d = L.distance(p)
        if d <= SNAP_M and (best is None or d < best[0]):
            best = (d, L.interpolate(L.project(p)), e['id'])
    if best is None:
        for e, pts in ways:
            if e['tags'].get('highway') == 'footway' or len(pts) < 2:
                continue
            L = LineString(pts)
            d = L.distance(p)
            if best is None or d < best[0]:
                best = (d, L.interpolate(L.project(p)), e['id'])
    return (best[1].x, best[1].y), best[2], best[0]


def main():
    G, ways = graph()
    gil = Polygon([to_m(*q) for q in load('gilpin-outline.json')['outline_lonlat']])
    for a, b, k in G.edges(data=True):
        m = Point((G.nodes[a]['xy'][0] + G.nodes[b]['xy'][0]) / 2, (G.nodes[a]['xy'][1] + G.nodes[b]['xy'][1]) / 2)
        k['w'] = k['d'] * (GILPIN_WEIGHT if gil.contains(m) else 1)
    # the church: the point of West Duval Street nearest it, then 9 m on past the street's middle
    ch = next(e for e in osm() if e['type'] == 'way' and e['id'] == CHURCH_WAY)
    cxy = Polygon([to_m(q['lon'], q['lat']) for q in ch['geometry']]).centroid
    duval = [pts for e, pts in ways if e['tags'].get('name') == 'West Duval Street' and e['tags'].get('highway') != 'footway']
    best = min((LineString(p) for p in duval), key=lambda L: L.distance(cxy))
    on = best.interpolate(best.project(cxy))
    dx, dy = on.x - cxy.x, on.y - cxy.y
    k = math.hypot(dx, dy)
    STOPS[2]['target'] = to_ll(on.x + dx / k * 9, on.y + dy / k * 9)
    nodes = list(G.nodes)
    out = []
    for s in STOPS:
        xy, wid, dist = snap(to_m(*s['target']), ways)
        if s['key'] == 'sixth-mount-zion':
            assert not Polygon([to_m(q['lon'], q['lat']) for q in ch['geometry']]).buffer(3).contains(Point(xy))
        assert not gil.buffer(2).contains(Point(xy)), s['key'] + ' falls inside the Gilpin Court outline'
        node = min(nodes, key=lambda n: math.dist(G.nodes[n]['xy'], xy))
        lon, lat = to_ll(*xy)
        out.append(dict(s, target=None, lon=round(lon, 6), lat=round(lat, 6), xy=[round(xy[0], 1), round(xy[1], 1)],
                        on_way=f'w{wid}', snapped_m=round(dist, 1), node=node))
    legs, path = [], []
    for a, b in zip(out[:-1], out[1:]):
        p = nx.shortest_path(G, a['node'], b['node'], weight='w')
        d = sum(G.edges[u, v]['d'] for u, v in zip(p[:-1], p[1:]))
        d += math.dist(a['xy'], G.nodes[a['node']]['xy']) + math.dist(b['xy'], G.nodes[b['node']]['xy'])
        coords = [a['xy']] + [list(G.nodes[n]['xy']) for n in p] + [b['xy']]
        inside = sum(G.edges[u, v]['d'] for u, v in zip(p[:-1], p[1:]) if G.edges[u, v]['w'] > G.edges[u, v]['d'])
        legs.append(dict(frm=a['n'], to=b['n'], m=round(d), minutes=round(d / WALK_M_PER_MIN), inside_gilpin_m=round(inside)))
        path.append([[round(x, 1), round(y, 1)] for x, y in coords])
    total = sum(l['m'] for l in legs)
    back = nx.shortest_path_length(G, out[-1]['node'], out[0]['node'], weight='d')
    res = dict(about=__doc__.strip(), walk_m_per_min=WALK_M_PER_MIN, stops=out, legs=legs, path=path, total_m=total,
               total_minutes=round(total / WALK_M_PER_MIN), last_to_first_m=round(back))
    json.dump(res, open(os.path.join(HERE, 'route.json'), 'w'), indent=1)
    for s in out:
        print(s['n'], s['title'], s['lat'], s['lon'], s['on_way'], s['snapped_m'])
    for l in legs:
        print(l)
    print('total', total, 'm; back to start', round(back), 'm')


if __name__ == '__main__':
    main()
