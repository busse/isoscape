#!/usr/bin/env python3
"""A cutaway sheet's context inset: a small flat map, north up, of where the cut building
stands and what its work joined (a canal, a river, a reservoir), drawn from today's OpenStreetMap
lines and a few curated marks. Written with Claude for Chris Busse.

    python3 tools/cutaway/context.py fetch cutaways/pump-house-context.json    # network: OSM API
    python3 tools/cutaway/context.py preview cutaways/pump-house-1885.json      # out/cutaways/<name>-inset.svg

The context file holds the extract's bounding box, what to keep from it (`keep`: ways and
relations by id, with a role), and after `fetch` the kept geometry (`features`), so `sheet.py`
never touches the network. The sheet's `inset` (in the cutaway spec) says where the inset sits
and what it marks: labels, the lines of curated works (a main whose line is approximate is drawn
dashed), and flow arrows.

Colors are palette.ts's paper palette (land, water, waterLine, ink, route).
"""
import argparse, json, math, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))

LAND, WATER, WATER_LINE, INK, ROUTE, DIM = '#ebe5d6', '#a8cad8', '#7fa9bc', '#2c2b33', '#b5392f', '#6d6a72'   # palette.ts, paper
SERIF = "'Libre Baskerville', Baskerville, Georgia, serif"
API = 'https://api.openstreetmap.org/api/0.6/map.json?bbox={},{},{},{}'


def fetch(path):
    ctx = json.load(open(path))
    w, s, e, n = ctx['bbox']
    nodes, ways, rels = {}, {}, {}
    # The API serves at most 0.25 square degrees and 50,000 nodes: ask in tiles.
    step = 0.008
    lon = w
    while lon < e:
        lat = s
        while lat < n:
            url = API.format(round(lon, 5), round(lat, 5), round(min(e, lon + step), 5), round(min(n, lat + step), 5))
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'isoscape (cutaway context inset)'})
            data = json.load(urllib.request.urlopen(req, timeout=120))
            for el in data['elements']:
                {'node': nodes, 'way': ways, 'relation': rels}[el['type']][el['id']] = el
            lat += step
        lon += step
    feats = []
    for k in ctx['keep']:
        if k['type'] == 'way':
            wy = ways.get(k['id'])
            if wy is None:
                print(f'missing way {k["id"]}', file=sys.stderr)
                continue
            feats.append({**k, 'coords': [[nodes[i]['lon'], nodes[i]['lat']] for i in wy['nodes'] if i in nodes]})
        else:
            rl = rels.get(k['id'])
            if rl is None:
                print(f'missing relation {k["id"]}', file=sys.stderr)
                continue
            members = []
            for m in rl['members']:
                if m['type'] == 'way' and m['ref'] in ways:
                    members.append({'role': m['role'], 'coords': [[nodes[i]['lon'], nodes[i]['lat']] for i in ways[m['ref']]['nodes'] if i in nodes]})
            feats.append({**k, 'members': members})
    ctx['features'] = feats
    ctx['fetched'] = 'OpenStreetMap API 0.6, map call, tiles of 0.008 deg'
    json.dump(ctx, open(path, 'w'), indent=1)
    print(f'{path}: {len(feats)} features')


def render(inset, root=ROOT):
    """The inset as (width, height, svg body), in its own units (1 unit = 1 m on the ground)."""
    ctx = json.load(open(os.path.join(root, inset['context'])))
    w, s, e, n = inset.get('bbox', ctx['bbox'])
    lat0 = (s + n) / 2
    kx, ky = 111_320 * math.cos(math.radians(lat0)), 110_574
    W, H = (e - w) * kx, (n - s) * ky
    P = lambda lon, lat: ((lon - w) * kx, (n - lat) * ky)
    pts = lambda cs: ' '.join(f'{x:.1f},{y:.1f}' for x, y in (P(*c) for c in cs))
    u = W / 1000           # one unit of the inset's type and strokes: a thousandth of its width
    out = [f'<rect x="0" y="0" width="{W:.1f}" height="{H:.1f}" fill="{LAND}"/>']
    out.append(f'<clipPath id="ctx-clip"><rect x="0" y="0" width="{W:.1f}" height="{H:.1f}"/></clipPath><g clip-path="url(#ctx-clip)">')
    # Water areas: a relation's outer ways closed along the frame where it cuts them.
    for f in ctx['features']:
        if f.get('role') != 'river':
            continue
        out.append(water_area(f, P, W, H, u))
    for f in ctx['features']:
        if f.get('role') == 'canal':
            out.append(f'<polyline points="{pts(f["coords"])}" fill="none" stroke="{WATER}" stroke-width="{f.get("width", 16):.1f}" stroke-linejoin="round" stroke-linecap="butt"/>')
    for f in ctx['features']:
        if f.get('role') == 'reservoir':
            out.append(f'<polygon points="{pts(f["coords"])}" fill="{WATER}" stroke="{INK}" stroke-width="{1.2 * u:.1f}"/>')
        if f.get('role') == 'subject':
            out.append(f'<polygon points="{pts(f["coords"])}" fill="{INK}" stroke="{INK}" stroke-width="{2.5 * u:.1f}"/>')
            xs = [P(*c) for c in f['coords']]
            cx, cy = sum(x for x, _ in xs) / len(xs), sum(y for _, y in xs) / len(xs)
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{45 * u:.1f}" fill="none" stroke="{ROUTE}" stroke-width="{3 * u:.1f}"/>')
    # Curated lines: a main in the route's red, dashed where its line is approximate; a canal in water.
    for ln in inset.get('lines', []):
        if ln.get('kind') == 'canal':
            # A channel today's map leaves out (a dry bed): drawn as a canal, from curated points.
            out.append(f'<polyline points="{pts(ln["coords"])}" fill="none" stroke="{WATER}" stroke-width="{ln.get("width", 14):.1f}" stroke-linejoin="round"/>')
            continue
        dash = f' stroke-dasharray="{9 * u:.1f} {6 * u:.1f}"' if ln.get('approximate') else ''
        out.append(f'<polyline points="{pts(ln["coords"])}" fill="none" stroke="{ROUTE}" stroke-width="{3.2 * u:.1f}" stroke-linecap="round"{dash}/>')
    # Flow arrows: a short line with a head, in the water's or the main's color.
    for ar in inset.get('arrows', []):
        (x0, y0), (x1, y1) = P(*ar['from']), P(*ar['to'])
        col = ROUTE if ar.get('kind') == 'main' else INK
        l = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / l, (y1 - y0) / l
        hs = 12 * u
        out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1 - ux * hs * 0.8:.1f}" y2="{y1 - uy * hs * 0.8:.1f}" stroke="{col}" stroke-width="{2.4 * u:.1f}"/>')
        out.append(f'<polygon points="{x1:.1f},{y1:.1f} {x1 - ux * hs - uy * hs * 0.5:.1f},{y1 - uy * hs + ux * hs * 0.5:.1f} {x1 - ux * hs + uy * hs * 0.5:.1f},{y1 - uy * hs - ux * hs * 0.5:.1f}" fill="{col}"/>')
    out.append('</g>')
    # Labels: a name at a point, set from its start, middle or end, roman or italic.
    for lb in inset.get('labels', []):
        x, y = P(*lb['at'])
        size = lb.get('size', 1) * 26 * u
        anchor = {'start': 'start', 'middle': 'middle', 'end': 'end'}[lb.get('anchor', 'start')]
        style = ' font-style="italic"' if lb.get('italic') else ''
        weight = ' font-weight="bold"' if lb.get('bold') else ''
        col = WATER_LINE if lb.get('water') else INK
        for i, line in enumerate(lb['text'].split('\n')):
            out.append(f'<text x="{x:.1f}" y="{y + i * size * 1.25:.1f}" font-family="{esc(SERIF)}" font-size="{size:.1f}" text-anchor="{anchor}" fill="{col}"{style}{weight}>{esc(line)}</text>')
    # North arrow and scale bar, bottom left.
    bx, by = 30 * u, H - 30 * u
    feet = inset.get('scaleFeet', 1000)
    bar = feet * 0.3048
    out.append(f'<rect x="{bx:.1f}" y="{by - 6 * u:.1f}" width="{bar:.1f}" height="{6 * u:.1f}" fill="{INK}"/>')
    out.append(f'<rect x="{bx + bar / 2:.1f}" y="{by - 6 * u:.1f}" width="{bar / 2:.1f}" height="{6 * u:.1f}" fill="{LAND}" stroke="{INK}" stroke-width="{1.2 * u:.1f}"/>')
    out.append(f'<text x="{bx:.1f}" y="{by - 12 * u:.1f}" font-family="{esc(SERIF)}" font-size="{20 * u:.1f}" fill="{INK}">0</text>')
    out.append(f'<text x="{bx + bar:.1f}" y="{by - 12 * u:.1f}" font-family="{esc(SERIF)}" font-size="{20 * u:.1f}" fill="{INK}" text-anchor="middle">{feet:,} ft</text>')
    nx, ny = bx + bar + 70 * u, by
    out.append(f'<polygon points="{nx:.1f},{ny - 60 * u:.1f} {nx + 12 * u:.1f},{ny - 30 * u:.1f} {nx - 12 * u:.1f},{ny - 30 * u:.1f}" fill="{INK}"/>')
    out.append(f'<text x="{nx:.1f}" y="{ny - 6 * u:.1f}" font-family="{esc(SERIF)}" font-size="{22 * u:.1f}" fill="{INK}" text-anchor="middle" font-weight="bold">N</text>')
    out.append(f'<rect x="0" y="0" width="{W:.1f}" height="{H:.1f}" fill="none" stroke="{INK}" stroke-width="{2.4 * u:.1f}"/>')
    return W, H, '\n'.join(out)


def water_area(f, P, W, H, u):
    """A water relation as one SVG path: outer and inner rings closed with the frame where they
    leave it (even-odd fill), so a river cut by the inset's edge is still an area."""
    try:
        from shapely.geometry import LineString, box
        from shapely.ops import polygonize, unary_union
    except ImportError:
        sys.exit('context.py needs shapely to close water areas: pip install shapely')
    frame = box(0, 0, W, H)
    outers = [LineString([P(*c) for c in m['coords']]) for m in f['members'] if m['role'] == 'outer' and len(m['coords']) > 1]
    inners = [LineString([P(*c) for c in m['coords']]) for m in f['members'] if m['role'] == 'inner' and len(m['coords']) > 1]
    lines = unary_union([ln.intersection(frame) for ln in outers] + [frame.exterior])
    faces = list(polygonize(lines))
    seeds = [P(*c) for c in f.get('inside', [])]
    from shapely.geometry import Point, Polygon
    keep = [fc for fc in faces if any(fc.contains(Point(sx, sy)) for sx, sy in seeds)]
    holes = [Polygon(ln.coords) for ln in inners if ln.is_closed]
    area = unary_union(keep)
    for h in holes:
        area = area.difference(h)
    polys = [area] if area.geom_type == 'Polygon' else list(getattr(area, 'geoms', []))
    d = []
    for pg in polys:
        for ring in [pg.exterior, *pg.interiors]:
            cs = list(ring.coords)
            d.append('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in cs) + 'Z')
    return f'<path d="{" ".join(d)}" fill="{WATER}" fill-rule="evenodd" stroke="{WATER_LINE}" stroke-width="{1.0 * u:.1f}"/>'


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['fetch', 'preview'])
    ap.add_argument('path')
    a = ap.parse_args()
    if a.cmd == 'fetch':
        fetch(a.path)
        return
    spec = json.load(open(a.path))
    W, H, body = render(spec['inset'])
    os.makedirs(os.path.join(ROOT, 'out', 'cutaways'), exist_ok=True)
    name = os.path.splitext(os.path.basename(a.path))[0]
    dest = os.path.join(ROOT, 'out', 'cutaways', f'{name}-inset.svg')
    open(dest, 'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" width="{W:.0f}" height="{H:.0f}">{body}</svg>')
    print(dest)


if __name__ == '__main__':
    main()
