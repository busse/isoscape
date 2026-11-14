"""Reference lines for registration, from cached data: OSM street centre lines, city blocks."""
import json, sys
import numpy as np
from geo import to_m, sample_lines, load_lines

def streets(osm_path, step=2.0):
    d = json.load(open(osm_path))
    keep = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'trunk', 'living_street'}
    lines = []
    for e in d['elements']:
        t = e.get('tags', {})
        if e['type'] != 'way' or t.get('highway') not in keep or t.get('bridge'):
            continue
        g = [p for p in (e.get('geometry') or []) if p]
        if len(g) < 2:
            continue
        x, y = to_m([p['lon'] for p in g], [p['lat'] for p in g])
        lines.append(np.stack([x, y], 1))
    return sample_lines(lines, step)

def blocks(path, step=1.0):
    return sample_lines(load_lines(path), step)
