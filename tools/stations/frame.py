"""A local frame for modeling one building into a history file, and the part record itself.

A building is easiest to model in meters along its own axes: `a` across its front (to the
right, facing it from the street), `b` back from the front into the lot. `Frame` turns those
into lon/lat about an origin; `Parts` collects parts (history.ts `HistoryFeature`, kind
`landmark`) in the form src/cutaway-scene.ts reads: a ring, a bottom and top elevation, a
tone, how the part is known, a note and its sources.

    from frame import Frame, Parts
    F = Frame(lon0, lat0, a_bearing=116.0)          # a runs along bearing 116°, b along 26°
    P = Parts(F, year_from=1928, year_to=None)
    P.box('x-wall', 'A wall', -12.8, -12.2, 0, 41, 0.0, 15.0, 'brick', 'written', 'note', [src])
"""

import math

KY = 110_574  # meters per degree of latitude, as region.ts uses


class Frame:
    def __init__(self, lon0, lat0, a_bearing):
        self.lon0, self.lat0 = lon0, lat0
        self.kx = 111_320 * math.cos(math.radians(lat0))
        r = math.radians(a_bearing)
        self.ua = (math.sin(r), math.cos(r))
        # b points back from the front into the lot: a's bearing turned 90° left, so that,
        # facing the building from the street, a runs to the right.
        self.b_bearing = (a_bearing - 90) % 360
        r = math.radians(self.b_bearing)
        self.ub = (math.sin(r), math.cos(r))
        self.a_bearing = a_bearing

    def en(self, a, b):
        """Meters east and north of the origin."""
        return (a * self.ua[0] + b * self.ub[0], a * self.ua[1] + b * self.ub[1])

    def lonlat(self, a, b):
        e, n = self.en(a, b)
        return [round(self.lon0 + e / self.kx, 8), round(self.lat0 + n / KY, 8)]

    def ring(self, pts):
        return [self.lonlat(a, b) for a, b in pts]

    def rect(self, a0, a1, b0, b1):
        return self.ring([(a0, b0), (a1, b0), (a1, b1), (a0, b1)])


class Parts:
    """Parts of one modeled building, each from `z0` to `z1` (elevations, meters)."""

    def __init__(self, frame, year_from, year_to=None):
        self.F = frame
        self.year_from, self.year_to = year_from, year_to
        self.features = []

    def add(self, id_, name, ring, z0, z1, tone, conf, note, sources, **more):
        f = {'id': id_, 'name': name, 'kind': 'landmark', 'from': self.year_from}
        if self.year_to is not None:
            f['to'] = self.year_to
        f.update({'ring': ring, 'height': round(z1 - z0, 3), 'tone': tone, 'elevation': round(z0, 3), 'upTo': round(z1, 3),
                  'confidence': conf, 'note': note, 'sources': list(sources)})
        f.update({k: v for k, v in more.items() if v is not None})
        self.features.append(f)
        return f

    def box(self, id_, name, a0, a1, b0, b1, z0, z1, tone, conf, note, sources, **more):
        return self.add(id_, name, self.F.rect(a0, a1, b0, b1), z0, z1, tone, conf, note, sources, **more)

    def poly(self, id_, name, pts, z0, z1, tone, conf, note, sources, **more):
        return self.add(id_, name, self.F.ring(pts), z0, z1, tone, conf, note, sources, **more)

    def line(self, id_, name, kind, pts, width, note, sources):
        f = {'id': id_, 'name': name, 'kind': kind, 'from': self.year_from}
        if self.year_to is not None:
            f['to'] = self.year_to
        f.update({'line': self.F.ring(pts), 'width': width, 'note': note, 'sources': list(sources)})
        self.features.append(f)
        return f
