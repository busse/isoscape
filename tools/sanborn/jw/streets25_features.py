"""Apostle Town's 1925 streets into the history: the lines read off the 1925 sheet 318
(streets1925.json) as curated `street` features, and today's ways laid out with Gilpin Court
dated from its clearance, so the 1925 view draws the streets the 1925 sheet prints.

    python3 streets25_features.py streets1925.json geo1952.json osm-ways.json \
        history/sanborn/jackson-ward-1925-lost.geojson history/jackson-ward.json [--write]

Each read line is carried to the ground by sheet 318's 1952 fit (the 1925 sheet is registered
onto the 1952 one, reg25.py). The streets end in 1941, when the city began clearing Apostle Town
for Gilpin Court; the 1952 sheet prints the project's own layout there. Today's ways that lie
at least 80% inside the hull of the 1925 buildings ended in 1941 (grown by 5 m), other than the
streets the 1925 sheet prints on the same line (Calhoun, Saint Peter, West Charity), get an
era rule from 1941: Hickory Street's present line and the project's paths."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import numpy as np
from shapely.geometry import LineString, MultiPoint
from geo import i2w, to_m, to_ll

S1925 = 'https://www.loc.gov/item/sanborn09064_008/'
S1952 = 'https://www.loc.gov/item/sanborn09064_018/'
LVA = 'https://uncommonwealth.lva.virginia.gov/blog/2025/11/17/a-brief-history-of-public-housing-in-the-city-of-richmond'
KEEP = ('Calhoun Street', 'Saint Peter Street', 'West Charity Street')


def main():
    reads, geo, osm, lost25, hist = sys.argv[1:6]
    reads, geo = json.load(open(reads)), json.load(open(geo))
    H = json.load(open(hist))
    feats = []
    for sh, streets in reads.items():
        if sh.startswith('_'):
            continue
        for name, uv in streets.items():
            xy = i2w(geo[sh]['params'], np.asarray(uv, float))
            lon, lat = to_ll(xy[:, 0], xy[:, 1])
            L = LineString(xy)
            slug = name.lower().replace(' ', '-')
            feats.append({
                'id': f'lost25-{sh}-{slug}', 'name': name, 'kind': 'street', 'highway': 'residential',
                'from': 1925, 'to': 1941,
                'line': [[round(float(a), 7), round(float(b), 7)] for a, b in zip(lon, lat)],
                'note': (f"{name} in Apostle Town as the 1925 Sanborn sheet {sh} (volume 3) prints it, where no street runs today "
                         f"or today's runs on another line: its center line read off the sheet (tools/sanborn/jw/streets1925.json) and "
                         f"placed by the sheet's fit, which rests on one corner (good to about 10 m). {round(L.length)} m. "
                         "Drawn from the 1925 survey (the street is older; earlier sheets not checked) to 1941, when the city began "
                         "clearing Apostle Town for Gilpin Court; the 1952 sheet prints the project's layout here instead."),
                'sources': [S1925, S1952, LVA],
            })
    pts = []
    for f in json.load(open(lost25))['features']:
        if f['properties'].get('to') == 1941:
            c = np.asarray(f['geometry']['coordinates'][0])
            x, y = to_m(c[:, 0], c[:, 1])
            pts += list(zip(x, y))
    hull = MultiPoint(pts).convex_hull.buffer(5)
    ids = []
    for w in json.load(open(osm)):
        if not w['tags'].get('highway') or len(w['g']) < 2 or w['tags'].get('name') in KEEP:
            continue
        c = np.asarray(w['g'])
        x, y = to_m(c[:, 0], c[:, 1])
        L = LineString(list(zip(x, y)))
        if L.length > 0 and L.intersection(hull).length / L.length >= 0.8:
            ids.append(f"w{w['id']}")
    rule = {'where': {'id': sorted(ids)}, 'eras': [[1941, None]],
            'note': ("Hickory Street's present line and the paths between Gilpin Court's buildings: the 1952 Sanborn sheet 318 prints "
                     "them, the 1925 sheet does not (it prints Hickory on another line, with Tyler and Cabell Streets; "
                     "tools/sanborn/jw/streets1925.json). Dated from 1941, when the clearance for Gilpin Court began (approximate: "
                     "the project was built 1941-43). Before then the 1925 streets are drawn."),
            'sources': [S1925, S1952, LVA]}
    for f in feats:
        print(f['id'], f['note'].split('. ')[2] if False else '', len(f['line']))
    print(len(ids), 'ways dated from 1941')
    if '--write' in sys.argv:
        H['features'] = [f for f in H['features'] if not f['id'].startswith('lost25-')] + feats
        H['rules'] = [r for r in H['rules'] if not r.get('note', '').startswith("Hickory Street's present line")] + [rule]
        json.dump(H, open(hist, 'w'), indent=1, ensure_ascii=False)
        open(hist, 'a').write('\n')


if __name__ == '__main__':
    main()
