"""Shared loading for the floods spike's dev tools (not used by isoscape itself)."""
import json, math
import numpy as np

KX = 111320 * math.cos(math.radians(37.533))
KY = 110574

def load_dem(prefix):
    h = json.load(open(prefix + '.json'))
    z = np.fromfile(prefix + '.f32', dtype=np.float32).reshape(h['height'], h['width'])
    return h, z

class Grid:
    """Lon/lat <-> pixel for the exported window (row 0 north), and meters."""
    def __init__(self, h):
        self.h = h
        self.px = (h['east'] - h['west']) / h['width']
        self.py = (h['north'] - h['south']) / h['height']
        self.dx = self.px * KX
        self.dy = self.py * KY
    def rc(self, lon, lat):
        return (self.h['north'] - lat) / self.py - 0.5, (lon - self.h['west']) / self.px - 0.5
    def ll(self, r, c):
        return self.h['west'] + (c + 0.5) * self.px, self.h['north'] - (r + 0.5) * self.py

def osm_ways(path):
    d = json.load(open(path))
    for e in d['elements']:
        if e['type'] == 'way' and 'geometry' in e:
            yield e['id'], e.get('tags', {}), [(p['lon'], p['lat']) for p in e['geometry'] if p is not None]
        elif e['type'] == 'relation' and 'members' in e:
            t = e.get('tags', {})
            for m in e['members']:
                if m.get('type') == 'way' and m.get('geometry'):
                    yield ('r%s' % e['id']), dict(t, _role=m.get('role', '')), [(p['lon'], p['lat']) for p in m['geometry'] if p is not None]
