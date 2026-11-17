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

routes.json may hold `placing`, how a placed path is drawn:
- "middle": meters. Where the path runs on one carriageway of a street mapped as two one-way
  ways (today's divided roads), each point is moved halfway to the other carriageway, if one of
  the same name runs the other way within this distance: the line runs down the middle of the
  street, as the tracks did, and does not jump from one carriageway to the other at a cross
  street.
- "smooth": meters. The path is then smoothed along its length (a Gaussian of this width, the
  ends held where they are), so a step from one way to the next, a little roundabout or a
  street's sideways jog is drawn as a gentle bend, and corners are rounded.

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
oneways = {}           # lower-case name -> [(a, b)] segments of one-way ways (lon, lat)
node_ways = {}         # node -> [(name, oneway, (a, b) of a segment through it)]
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
    ow = t.get('oneway') == 'yes'
    for a, b in zip(nodes, nodes[1:]):
        if a not in coord or b not in coord: continue
        if name:
            if ow: oneways.setdefault(name, []).append((a, b))
            node_ways.setdefault(a, []).append((name, ow, (a, b))); node_ways.setdefault(b, []).append((name, ow, (a, b)))
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
    return [node_pt(n) for n in reversed(out)]

PLACING = {}

class P(tuple):
    """A placed point that remembers the OSM node it came from (None off the street graph)."""
    node = None

def node_pt(n):
    p = P(coord[n]); p.node = n; return p

def to_m(p): return ((p[0] - LON0) * KX, (p[1] - LAT0) * KY)
def from_m(q): return (q[0] / KX + LON0, q[1] / KY + LAT0)
LON0 = -77.45

def middle(p, reach):
    """`p` moved halfway to the opposite carriageway of its street, if there is one within reach."""
    n = getattr(p, 'node', None)
    if n is None: return p
    mine = [w for w in node_ways.get(n, ()) if w[1]]
    if not mine: return p
    pm = to_m(coord[n])
    best = None
    for name, _, (a, b) in mine:
        ua, ub = to_m(coord[a]), to_m(coord[b])
        d = (ub[0] - ua[0], ub[1] - ua[1]); dl = math.hypot(*d) or 1e-9
        for (c, e) in oneways.get(name, ()):
            if n in (c, e): continue
            vc, ve = to_m(coord[c]), to_m(coord[e])
            f = (ve[0] - vc[0], ve[1] - vc[1]); fl = math.hypot(*f) or 1e-9
            if (d[0] * f[0] + d[1] * f[1]) / (dl * fl) > -0.85: continue   # not running the other way
            t = max(0.0, min(1.0, ((pm[0] - vc[0]) * f[0] + (pm[1] - vc[1]) * f[1]) / (fl * fl)))
            q = (vc[0] + f[0] * t, vc[1] + f[1] * t)
            dd = math.hypot(q[0] - pm[0], q[1] - pm[1])
            if dd <= reach and (best is None or dd < best[0]): best = (dd, q)
    if best is None: return p
    q = best[1]
    return from_m(((pm[0] + q[0]) / 2, (pm[1] + q[1]) / 2))

def smooth(pts, sigma, step=2.0):
    """Resampled every `step` m and smoothed with a Gaussian of `sigma` m, the window shrinking
    symmetrically toward each end so the ends stay put."""
    m = [to_m(p) for p in pts]
    out = [m[0]]
    for a, b in zip(m, m[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); k = max(1, math.ceil(L / step))
        out += [(a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k) for i in range(1, k + 1)]
    h = int(3 * sigma / step)
    wts = [math.exp(-0.5 * (i * step / sigma) ** 2) for i in range(h + 1)]
    res = []
    for i in range(len(out)):
        k = min(h, i, len(out) - 1 - i)
        sw = wts[0]; sx = out[i][0] * wts[0]; sy = out[i][1] * wts[0]
        for j in range(1, k + 1):
            w = wts[j]; sw += 2 * w
            sx += w * (out[i - j][0] + out[i + j][0]); sy += w * (out[i - j][1] + out[i + j][1])
        res.append((sx / sw, sy / sw))
    return [from_m(q) for q in rdp(res, 0.3)]

def rdp(p, eps):
    if len(p) < 3: return list(p)
    keep = [False] * len(p); keep[0] = keep[-1] = True
    stack = [(0, len(p) - 1)]
    while stack:
        i, j = stack.pop()
        a, b = p[i], p[j]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1e-9
        best, bk = -1, -1
        for k in range(i + 1, j):
            d = abs((p[k][0] - a[0]) * dy - (p[k][1] - a[1]) * dx) / L
            if d > best: best, bk = d, k
        if best > eps: keep[bk] = True; stack += [(i, bk), (bk, j)]
    return [q for q, k in zip(p, keep) if k]

def place(route):
    pts = []; last = None; last_names = ()
    for stop in route['stops']:
        if isinstance(stop, dict) and 'direct' in stop:
            p = tuple(stop['direct']); pts.append(p); last = snap(p, None); last_names = (); continue
        if isinstance(stop, dict) and 'straight' in stop:
            # A straight run to a corner, over a gap no street fills today (a viaduct since torn down).
            node = corner(stop['straight'][0], stop['straight'][1], last)
            pts.append(node_pt(node)); last, last_names = node, tuple(stop['straight']); continue
        if isinstance(stop, list):
            node = corner(stop[0], stop[1], last); names = tuple(stop)
        else:
            node = snap(tuple(stop['at']), stop['on']); names = (stop['on'],)
        if last is None or not pts:
            pts.append(node_pt(node))
        else:
            shared = [n for n in names if n in last_names] or list(names) + list(last_names)
            if last_names == () :
                pts.append(node_pt(node))   # after a direct run: straight on to the street
            else:
                pts.extend(path(last, node, shared)[1:])
        last, last_names = node, names
    if PLACING.get('middle'): pts = [middle(p, PLACING['middle']) for p in pts]
    if PLACING.get('smooth'):
        dd = []
        for p in pts:
            if not dd or dd[-1] != tuple(p): dd.append(tuple(p))
        pts = smooth(dd, PLACING['smooth'])
    out = []
    for x, y in pts:   # a stop that repeats the last point adds nothing
        q = [round(x, 7), round(y, 7)]
        if not out or out[-1] != q: out.append(q)
    return out

routes = json.load(open(routes_path))
PLACING.update(routes.get('placing', {}))
hist = json.load(open(history_path))
placed = {}
for r in routes['routes']:
    runs = [place({'stops': s}) for s in r['runs']]
    length = sum(dist(a, b) for run in runs for a, b in zip(run, run[1:]))
    print(f"{r['id']}: {len(runs)} run(s), {length / 1609.34:.1f} miles")
    placed[r['id']] = {'id': r['id'], 'name': r['name'], 'kind': 'streetcar', 'from': r.get('from', 1888), 'to': r.get('to', 1950),
                       'route': r.get('route', ''), 'lines': runs, 'note': r['note'], 'sources': r['sources']}
# A curated bridge drawn on a line's old placement (each of its points within 0.5 m of it) moves
# with the line: each point to the nearest point of the new placement.
def nearest(p, run):
    pm = to_m(p); best = None
    for a, b in zip(run, run[1:]):
        ua, ub = to_m(a), to_m(b); dx, dy = ub[0] - ua[0], ub[1] - ua[1]; l2 = dx * dx + dy * dy or 1e-12
        t = max(0.0, min(1.0, ((pm[0] - ua[0]) * dx + (pm[1] - ua[1]) * dy) / l2))
        q = (ua[0] + dx * t, ua[1] + dy * t); d = math.hypot(q[0] - pm[0], q[1] - pm[1])
        if best is None or d < best[0]: best = (d, q)
    return best
old_runs = {f['id']: f.get('lines', []) for f in hist['features'] if f['kind'] == 'streetcar'}
for f in hist['features']:
    if f['kind'] != 'bridge' or not f.get('line'): continue
    for lid, runs in old_runs.items():
        if lid not in placed: continue
        for k, run in enumerate(runs):
            if len(run) < 2 or k >= len(placed[lid]['lines']): continue
            if all(nearest(p, run)[0] <= 0.5 for p in f['line']):
                f['line'] = [[round(x, 7), round(y, 7)] for x, y in (from_m(nearest(p, placed[lid]['lines'][k])[1]) for p in f['line'])]
feats = [f for f in hist['features'] if not (f['kind'] == 'streetcar' and f['id'] in placed)]
hist['features'] = feats + list(placed.values())
json.dump(hist, open(history_path, 'w'), indent=1, ensure_ascii=False); open(history_path, 'a').write('\n')
total = sum(dist(a, b) for f in placed.values() for run in f['lines'] for a, b in zip(run, run[1:]))
print(f'{len(placed)} lines, {total / 1609.34:.1f} route-miles placed')
