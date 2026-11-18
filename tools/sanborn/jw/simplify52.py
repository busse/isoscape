"""Simplify the busy outlines of the 1952 Jackson Ward drawn layer (history/sanborn/jackson-ward-lost.geojson)
with simplify25.py's pass (1 m Douglas-Peucker stepping down so no wall moves more than 1 m, squaring
near-rectangles within 1 m and 5% of area, collinear points dropped; nothing dropped or merged).

    python3 simplify52.py <jackson-ward-lost.geojson> [MAX_CORNERS=10]

Only this series' own outlines (ids starting "jw1952") with more than MAX_CORNERS corners are touched:
most are the 614 that uncovered.py put back after ../clean.py had simplified the rest, and the
re-traced volume 1 sheets and count_restore.py's outlines, which never went through the cleaning.
They drew as dark hatching (each corner is an edge and a dot). The edition file
(history/sanborn/jackson-ward-1952.geojson) keeps every outline as traced, so the count does not change."""
import json, sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simplify25


def main(path, most=10):
    most = int(most)
    g = json.load(open(path))
    busy = [i for i, f in enumerate(g['features']) if f['properties']['id'].startswith('jw1952')
            and f['geometry']['type'] == 'Polygon' and len(f['geometry']['coordinates']) == 1
            and len(f['geometry']['coordinates'][0]) - 1 > most]
    tmp = tempfile.NamedTemporaryFile('w', suffix='.geojson', delete=False)
    json.dump({'type': 'FeatureCollection', 'features': [g['features'][i] for i in busy]}, tmp); tmp.close()
    print(len(busy), 'busy outlines (more than', most, 'corners):', end=' ')
    simplify25.main(tmp.name)
    out = json.load(open(tmp.name))['features']
    for i, f in zip(busy, out):
        g['features'][i] = f
    json.dump(g, open(path, 'w'))
    os.unlink(tmp.name)


if __name__ == '__main__':
    main(*sys.argv[1:])
