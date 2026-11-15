"""Place streetcar routes on today's OpenStreetMap streets, and write them into a history file.

    python3 tools/streetcars/build.py <osm.json> <routes.json> <history.json>

A route in routes.json is a list of stops. Between two stops the car follows the street they
share, along OSM's own street geometry:

- ["Floyd Avenue", "Robinson Street"]: the corner of two streets (names match OSM names as
  case-insensitive substrings, so "Broad Street" finds both "West Broad Street" and "East
  Broad Street"). Where they meet more than once, the corner nearest the previous stop wins.
- {"at": [lon, lat], "on": "Grove Avenue"}: a point, snapped to the nearest corner on that street.
- {"direct": [lon, lat]}: a straight run from the previous stop, for a line on its own
  right-of-way where no street follows it today.
- {"straight": ["Marshall Street", "21st Street"]}: a straight run to a corner, over a gap no
  street fills today (a viaduct since torn down).

The path between stops is the shortest walk over OSM's street graph, where streets named in
both stops cost 1 per meter and every other street 6, so it keeps to the named street and
only leaves it to bridge a gap (a street renamed, a block since closed). Each placed route
replaces the history's `streetcar` feature of the same id; every other feature is kept.
"""
import heapq, json, math, sys

osm_path, routes_path, history_path = sys.argv[1:4]
els = json.load(open(osm_path))['elements']

# ---- the street graph -------------------------------------------------------------------------
coord = {}
adj = {}
names_at = {}          # node -> set of lower-case street names through it
LAT0 = 37.55
KX = 111_320 * math.cos(math.radians(LAT0)); KY = 110_574
def dist(a, b):
    return math.hypot((a[0] - b[0]) * KX, (a[1] - b[1]) * KY)
STREETS = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'service', 'living_street',
           'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link', 'pedestrian', 'track'}
for e in els:
    if e['type'] != 'way' or 'geometry' not in e: continue
    t = e.get('tags', {})
    if t.get('highway') not in STREETS: continue
    if t.get('highway', '').startswith('motorway'): continue   # no streetcar ran on an interstate
    name = (t.get('name') or '').lower()
    nodes = e['nodes']; geom = e['geometry']
    for nid, g in zip(nodes, geom):
        if g is None: continue
        coord[nid] = (g['lon'], g['lat'])
        names_at.setdefault(nid, set()).add(name)
    for a, b in zip(nodes, nodes[1:]):
        if a not in coord or b not in coord: continue
        d = dist(coord[a], coord[b])
        adj.setdefault(a, []).append((b, d, name))
        adj.setdefault(b, []).append((a, d, name))

def has(node, street):
    s = street.lower()
    return any(s in n for n in names_at.get(node, ()))

def corner(a, b, near=None):
    cands = [n for n in names_at if has(n, a) and has(n, b)]
    if not cands:
        # Streets that meet without sharing a node: the closest pair of their nodes, within 150 m
        # (noted when over 40 m).
        na = [n for n in names_at if has(n, a)]; nb = [n for n in names_at if has(n, b)]
        best = None
        for x in na:
            for y in nb:
                d = dist(coord[x], coord[y])
                if best is None or d < best[0]: best = (d, x)
        if best is None or best[0] > 150:
            far = f' (nearest {best[0]:.0f} m apart)' if best else ''
            raise SystemExit(f'no corner of {a!r} and {b!r} in the OSM data{far}')
        if best[0] > 40: print(f'  note: {a!r} and {b!r} come within {best[0]:.0f} m; using that as the corner')
        cands = [best[1]]
    if near is None: return cands[0]
    return min(cands, key=lambda n: dist(coord[n], coord[near]))

def snap(pt, street):
    cands = [n for n in names_at if has(n, street)] if street else list(coord)
    return min(cands, key=lambda n: dist(coord[n], pt))

def path(src, dst, prefer):
    pref = [p.lower() for p in prefer]
    best = {src: 0.0}; prev = {}
    q = [(0.0, src)]
    while q:
        d, u = heapq.heappop(q)
        if u == dst: break
        if d > best.get(u, 1e18): continue
        for v, w, name in adj.get(u, ()):
            cost = w * (1 if any(p in name for p in pref) else 6)
            nd = d + cost
            if nd < best.get(v, 1e18):
                best[v] = nd; prev[v] = u; heapq.heappush(q, (nd, v))
    if dst not in prev and dst != src: raise SystemExit(f'no path between stops ({prefer})')
    out = [dst]
    while out[-1] != src: out.append(prev[out[-1]])
    return [coord[n] for n in reversed(out)]

def place(route):
    pts = []; last = None; last_names = ()
    for stop in route['stops']:
        if isinstance(stop, dict) and 'direct' in stop:
            p = tuple(stop['direct']); pts.append(p); last = snap(p, None); last_names = (); continue
        if isinstance(stop, dict) and 'straight' in stop:
            # A straight run to a corner, over a gap no street fills today (a viaduct since torn down).
            node = corner(stop['straight'][0], stop['straight'][1], last)
            pts.append(coord[node]); last, last_names = node, tuple(stop['straight']); continue
        if isinstance(stop, list):
            node = corner(stop[0], stop[1], last); names = tuple(stop)
        else:
            node = snap(tuple(stop['at']), stop['on']); names = (stop['on'],)
        if last is None or not pts:
            pts.append(coord[node])
        else:
            shared = [n for n in names if n in last_names] or list(names) + list(last_names)
            if last_names == () :
                pts.append(coord[node])     # after a direct run: straight on to the street
            else:
                pts.extend(path(last, node, shared)[1:])
        last, last_names = node, names
    return [[round(x, 7), round(y, 7)] for x, y in pts]

routes = json.load(open(routes_path))
hist = json.load(open(history_path))
placed = {}
for r in routes['routes']:
    runs = [place({'stops': s}) for s in r['runs']]
    length = sum(dist(a, b) for run in runs for a, b in zip(run, run[1:]))
    print(f"{r['id']}: {len(runs)} run(s), {length / 1609.34:.1f} miles")
    placed[r['id']] = {'id': r['id'], 'name': r['name'], 'kind': 'streetcar', 'from': r.get('from', 1888), 'to': r.get('to', 1950),
                       'route': r.get('route', ''), 'lines': runs, 'note': r['note'], 'sources': r['sources']}
feats = [f for f in hist['features'] if not (f['kind'] == 'streetcar' and f['id'] in placed)]
hist['features'] = feats + list(placed.values())
json.dump(hist, open(history_path, 'w'), indent=1, ensure_ascii=False); open(history_path, 'a').write('\n')
total = sum(dist(a, b) for f in placed.values() for run in f['lines'] for a, b in zip(run, run[1:]))
print(f'{len(placed)} lines, {total / 1609.34:.1f} route-miles placed')
