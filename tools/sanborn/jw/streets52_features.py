"""Turn the 1952 street center lines read off the sheets (streets1952.json) into the history's
curated lost streets: the stretches inside the highway's corridor where no street runs today.

    python3 streets52_features.py streets1952.json geo1952.json highway-footprint.geojson \
        osm-jw.json history/jackson-ward.json out.json [--write]

Each read line is carried to the ground by its sheet's fit and cut into 2 m steps. A step is
taken to be a street that survives when it lies within 9 m of a street in today's OpenStreetMap
that the 1952 scene draws (any road but the motorway and its ramps), running within 30 degrees
of the same direction; or within 9 m of a lost street already in the history or of a line
already taken from an earlier sheet. The runs of steps left are the lost stretches. A run is
kept when, cut to the corridor grown by 20 m (to reach the corners just outside it), it is at
least 20 m long and at least 40% of it lies in the corridor itself. With --write the kept
stretches go into the history file as `street` features (ids starting "lost52-"), replacing
any written before; without it they are printed and written to out.json for looking at."""
import json, sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import LineString, Point, shape
from shapely.ops import unary_union
from shapely import transform as stransform, STRtree
from geo import w2i, i2w, to_m, to_ll

NEAR_M, ANGLE_DEG, GROW_M, MIN_M, MIN_INSIDE = 9, 30, 20, 20, 0.4
DRAWN = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'service',
         'living_street', 'primary_link', 'secondary_link', 'tertiary_link', 'pedestrian'}
ALLEY = ('alley', 'Alley')
SOURCE = 'https://www.loc.gov/item/sanborn09064_018/'


def m_of(ll):
    ll = np.asarray(ll, float)
    x, y = to_m(ll[:, 0], ll[:, 1])
    return np.stack([x, y], 1)


def segs(lines):
    out = []
    for L in lines:
        for a, b in zip(L[:-1], L[1:]):
            if np.hypot(*(b - a)) > 0.5:
                out.append((a, b))
    return out


def covered(p, d, tree, segl):
    for i in tree.query(Point(p).buffer(NEAR_M)):
        a, b = segl[i]
        ab = b - a
        t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
        if np.hypot(*(a + t * ab - p)) > NEAR_M:
            continue
        cos = abs(np.dot(ab, d)) / (np.hypot(*ab) * np.hypot(*d))
        if cos >= math.cos(math.radians(ANGLE_DEG)):
            return True
    return False


def runs(xy, tree, segl):
    L = LineString(xy)
    n = max(2, int(L.length / 2) + 1)
    pts = np.array([L.interpolate(t, normalized=True).coords[0] for t in np.linspace(0, 1, n)])
    d = np.gradient(pts, axis=0)
    free = np.array([not covered(p, v, tree, segl) for p, v in zip(pts, d)])
    out, cur = [], []
    for p, f in zip(pts, free):
        if f:
            cur.append(p)
        elif cur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return [np.array(r) for r in out if len(r) >= 2]


def main():
    reads, geo, fp, osm, hist, out = sys.argv[1:7]
    write = '--write' in sys.argv
    reads, geo = json.load(open(reads)), json.load(open(geo))
    polys = {f['properties']['name']: shape(f['geometry']) for f in json.load(open(fp))['features']}
    corr = stransform(polys['corridor'], lambda c: m_of(c))
    zone = corr.buffer(GROW_M)
    H = json.load(open(hist))
    today = [m_of(w['g']) for w in json.load(open(osm)) if w['tags'].get('highway') in DRAWN and len(w['g']) > 1]
    curated = [m_of(f['line']) for f in H['features'] if f.get('kind') == 'street' and not f['id'].startswith('lost52-')]
    segl = segs(today + curated)
    kept = []
    for sh, streets in reads.items():
        if sh.startswith('_'):
            continue
        p = geo[sh]['params']
        for name, uv in streets.items():
            tree = STRtree([LineString([a, b]) for a, b in segl])
            xy = i2w(p, np.asarray(uv, float))
            for r in runs(xy, tree, segl):
                piece = LineString(r).intersection(zone)
                parts = list(piece.geoms) if hasattr(piece, 'geoms') else [piece]
                for q in parts:
                    if q.is_empty or q.geom_type != 'LineString' or q.length < MIN_M:
                        continue
                    inside = q.intersection(corr).length / q.length
                    if inside < MIN_INSIDE:
                        continue
                    q = q.simplify(0.5)
                    kept.append(dict(sheet=sh, name=name, line=np.asarray(q.coords), inside=inside, length=q.length, uv_read=uv))
                    segl += segs([np.asarray(q.coords)])
    feats = []
    for k in kept:
        lon, lat = to_ll(k['line'][:, 0], k['line'][:, 1])
        slug = k['name'].lower().split(' (')[0].replace(' ', '-').replace('(', '').replace(')', '')
        fid = f"lost52-{k['sheet']}-{slug}"
        n = sum(1 for f in feats if f['id'].startswith(fid))
        fid = fid if n == 0 else f'{fid}-{n + 1}'
        alley = any(a in k['name'] for a in ALLEY)
        feats.append({
            'id': fid, 'name': k['name'].split(' (')[0] if 'alley (' not in k['name'] else 'Alley', 'kind': 'street',
            'highway': 'service' if alley else 'residential', 'from': 1952, 'to': 1956,
            'line': [[round(float(a), 7), round(float(b), 7)] for a, b in zip(lon, lat)],
            'note': (f"A stretch of {k['name']} inside the Turnpike's corridor, where no street runs today, "
                     f"as printed on the 1952 Sanborn sheet {k['sheet']} (volume 3): its center line read off the sheet "
                     f"(tools/sanborn/jw/streets1952.json) and carried to the ground by the sheet's fit "
                     f"(good to about 3-6 m). {round(k['length'])} m, {round(100 * k['inside'])}% of it in the corridor polygon. "
                     "Drawn from the 1952 survey (it is older; earlier sheets not checked for it) to 1956, "
                     "when the corridor was being cleared (approximate: 1955-58)."),
            'sources': [SOURCE, 'https://www.openstreetmap.org/'],
        })
    for f in feats:
        print(f"{f['id']:45s} {f['name']:32s} {f['note'].split('. ')[2] if False else ''}")
    json.dump({'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'id': f['id'], 'name': f['name']},
         'geometry': {'type': 'LineString', 'coordinates': f['line']}} for f in feats]}, open(out, 'w'))
    print(len(feats), 'stretches,', round(sum(k['length'] for k in kept)), 'm')
    if write:
        H['features'] = [f for f in H['features'] if not f['id'].startswith('lost52-')] + feats
        json.dump(H, open(hist, 'w'), indent=1, ensure_ascii=False)
        open(hist, 'a').write('\n')


if __name__ == '__main__':
    main()
