#!/usr/bin/env python3
"""Street names on the story's isometric views of 1952 and today, for the guide's pairs and its
large view of the whole ward. Labels are placed in the guide's own post-processing, on rasters of
the story's scenes; no drawing code is changed.

Where a street falls in a picture comes from the drawing tool itself: `isoscape locate
jackson-ward --year Y lon,lat ...` gives the point's place on the drawn ground, terrain included,
in the scene's SVG units (cached per year in the work folder). Streets are densified every 8 m.

Rules (said on the page and in orientation.md):

  Today's half: every named street (OSM, as orient.py takes them: streets, and named alleys and
    plazas) is named along its line, upright type, ink, with a paper halo.
  1952 half:
    - the stretches the trench cut, as the story's trace has them (`lost52-`), are named in italic,
      dark red, the plan maps' second style;
    - a street of today is named only along stretches that ran where it runs in 1952: no traced
      1952 building outline stands on its center line (within ON_LINE_M), the stretch is not in, or
      within GAP_CLEAR_M of, a block the 1952 sheets were not traced for (the story's hatch), and it is not on today's
      bridges or in today's highway footprint. So today's lines through Navy Hill that the 1952
      views draw through houses, where the 1952 streets were never read off the sheets, get no
      label in 1952. A street's stretch under today's highway, joined across as the USGS map of
      1933-34 shows it (`lost-`), is named in upright type, since the street kept its name.
  A street named in both halves is named at the same place in both: positions are chosen once,
  from the stretch eligible in 1952, and drawn in each half at that ground point.

Labels run along the street, centered on it, kept upright, never over another label, the stop's
disc, the half's title band, or the picture's edge, and only on ground at least INSET_M inside
the story's frame. A name with no straight enough run long enough is set level beside its line,
near the middle of what the picture shows of it, with a short leader to the line; failing that
it is left off that picture, and each run lists what it left off.
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'stories', 'jackson-ward'))
from common import osm, palette, to_ll, to_m  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from shapely.geometry import LineString, Point, Polygon, box, shape  # noqa: E402
from shapely.ops import transform, unary_union  # noqa: E402

P = palette()
INK, PAPER, LOST = P['ink'], P['sky'], P['mark']['line']
FONTS = os.path.join(ROOT, 'tools/pdf/fonts')
STEP_M = 8
ON_LINE_M = 2.0
GAP_CLEAR_M = 30     # and not within this of a block the 1952 sheets were not traced for
INSET_M = 30         # names only on ground at least this far inside the story's frame (its near edge is the slab)
STREET = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'living_street', 'trunk'}
MINOR = {'service', 'pedestrian'}


def font(px, italic=False, bold=False):
    name = 'Inter-' + ('SemiBold' if bold and not italic else 'SemiBoldItalic' if bold else 'Italic' if italic else 'Regular') + '.ttf'
    return ImageFont.truetype(os.path.join(FONTS, name), max(6, round(px)))


SHORT = [('Saint ', 'St. '), (' Street', ' St.'), (' Avenue', ' Ave.'), (' Parkway', ' Pkwy.'), (' Road', ' Rd.'),
         ('North ', 'N. '), ('South ', 'S. '), ('East ', 'E. '), ('West ', 'W. '), (' Place', ' Pl.'), (' Drive', ' Dr.')]


def short(name):
    for a, b in SHORT:
        name = name.replace(a, b)
    return name


# ---- the streets, on the ground -------------------------------------------------------------

def densify(L, step=STEP_M):
    n = max(1, int(L.length / step))
    return [L.interpolate(i / n, normalized=True).coords[0] for i in range(n + 1)]


def streets(frame_m):
    """{name: [LineString, ...]} of today's named streets inside the plan polygon frame_m, the
    1952 stretches, the joined stretches, and today's bridges and highway footprint."""
    import map as M
    today = {}
    bridges = []
    for e in osm():
        t = e.get('tags', {})
        if e['type'] != 'way' or not e.get('geometry') or not t.get('name'):
            continue
        if not (t.get('highway') in STREET or t.get('highway') in MINOR):
            continue
        L = LineString([to_m(q['lon'], q['lat']) for q in e['geometry']])
        if not L.intersects(frame_m):
            continue
        today.setdefault(t['name'], []).append(L)
        if t.get('bridge') in ('yes', 'viaduct'):
            bridges.append(L)
    h = json.load(open(os.path.join(ROOT, 'history/jackson-ward.json')))
    lost, joined = {}, {}
    for f in h['features']:
        if f.get('kind') != 'street':
            continue
        L = LineString([to_m(*p) for p in f['line']])
        if f['id'].startswith('lost52-'):
            lost.setdefault(f['name'], []).append(L)
        elif f['id'].startswith('lost-'):
            joined.setdefault(f['name'], []).append(L)
    b = frame_m.bounds
    foot = M.gather((b[0], b[2], b[1], b[3]))['foot']
    return today, lost, joined, unary_union(bridges) if bridges else None, foot


def traced_1952():
    tm = lambda x, y, z=None: to_m(x, y)  # noqa: E731
    out = []
    for ft in json.load(open(os.path.join(ROOT, 'history/sanborn/jackson-ward-1952.geojson')))['features']:
        if ft['properties'].get('coverage'):
            continue
        try:
            out.append(transform(tm, shape(ft['geometry'])).buffer(0))
        except Exception:
            continue
    return unary_union(out)


def untraced_gaps(frame_m):
    """The blocks the story's 1952 view hatches as untraced: as views.untraced computes them."""
    import views
    tm = lambda x, y, z_=None: to_m(x, y)  # noqa: E731
    near = []
    for f in views.COVER[1952]:
        for ft in json.load(open(os.path.join(ROOT, f'history/sanborn/{f}.geojson')))['features']:
            if ft['properties'].get('coverage'):
                continue
            try:
                near.append(transform(tm, shape(ft['geometry'])).buffer(0).buffer(40))
            except Exception:
                continue
    gaps = frame_m.difference(unary_union(near)).buffer(-20).buffer(20)
    return unary_union([g for g in getattr(gaps, 'geoms', [gaps]) if g.area >= views.MIN_UNTRACED and g.centroid.x > to_m(views.EAST_OF, 0)[0]])


def eligible_1952(L, traced, gaps, foot, bridges):
    """The parts of a today's street line that are named in a 1952 half (see the module's rules)."""
    bad = traced.intersection(L.buffer(ON_LINE_M)).buffer(ON_LINE_M + 6)
    bad = unary_union([bad, gaps.buffer(GAP_CLEAR_M), foot.buffer(2)] + ([bridges.buffer(4)] if bridges is not None else []))
    g = L.difference(bad)
    return [p for p in getattr(g, 'geoms', [g]) if p.geom_type == 'LineString' and p.length > 20]


# ---- projection ---------------------------------------------------------------------------

_MEM = {}


def locate(work, year, pts):
    """Ground points (plan meters) -> SVG units on the drawn ground of the year's scene, through
    `isoscape locate` (one call for every point not yet known; cached in memory and in the work
    folder). Points are keyed to 0.1 m."""
    cache = os.path.join(work, f'locate-{year}.json')
    if year not in _MEM:
        _MEM[year] = json.load(open(cache)) if os.path.exists(cache) else {}
    known = _MEM[year]
    keys = [f'{x:.1f},{y:.1f}' for x, y in pts]
    need = sorted({k for k in keys if k not in known})
    for i in range(0, len(need), 20000):
        part = need[i:i + 20000]
        args = []
        for k in part:
            x, y = map(float, k.split(','))
            lon, lat = to_ll(x, y)
            args.append(f'{lon:.7f},{lat:.7f}')
        out = subprocess.run(['node', 'bin/isoscape.js', 'locate', 'jackson-ward', '--year', str(year), '--'] + args, cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        res = json.loads(out[out.index('['):])
        for k, r in zip(part, res):
            known[k] = [r['x'], r['y']]
        json.dump(known, open(cache, 'w'))
    return [known[k] for k in keys]


def warm(work, data):
    """Look up every point the placing may ask for, in one call per year."""
    today, lost, joined, bridges, foot, traced, gaps = data
    pts = []
    for Ls in today.values():
        for L in Ls:
            pts += densify(L, 4)
            for g in eligible_1952(L, traced, gaps, foot, bridges):
                pts += densify(g, 4)
    for d in (lost, joined):
        for Ls in d.values():
            for L in Ls:
                pts += densify(L, 4)
    for yr in (1952, 2026):
        locate(work, yr, pts)


# ---- placing ------------------------------------------------------------------------------

class Placer:
    """Places labels on one picture: a crop given in SVG units (x, y, w, h) of the shared frame
    rasterized at zoom z (pixels = (svg - corner) * z)."""

    def __init__(self, work, crop_svg, z, px, keep_out=()):
        self.work, self.crop, self.z, self.px = work, crop_svg, z, px
        x, y, w, h = crop_svg
        self.size = (round(w * z), round(h * z))
        self.taken = [k for k in keep_out]
        self.placed = []      # (key, ground point, angle hint) for reuse in the other half
        self.left_off = []

    def to_px(self, svg_pts):
        x0, y0 = self.crop[0], self.crop[1]
        return [((sx - x0) * self.z, (sy - y0) * self.z) for sx, sy in svg_pts]

    def text_size(self, s, italic, px):
        f = font(px, italic=italic)
        b = f.getbbox(s)
        return b[2] - b[0], px * 1.05

    def try_line(self, ground, year, s, italic, px, near=None):
        """Find a straight enough run of a ground line (plan meters) for the label; return
        (cx, cy, angle_deg, ground_mid, rect) or None. With `near` (a ground point), only runs
        centered within 6 m of it: the same place as in the other half."""
        pts = densify(ground, 4)
        svg = locate(self.work, year, pts)
        pix = self.to_px(svg)
        w, h = self.text_size(s, italic, px)
        need = w + px * 0.6
        W, H = self.size
        cum = [0.0]
        for a, b in zip(pix[:-1], pix[1:]):
            cum.append(cum[-1] + math.dist(a, b))
        n = len(pix)
        order = sorted(range(n), key=lambda i: abs(cum[i] - cum[-1] / 2))
        for i in order:
            j = i
            while j < n - 1 and cum[j] - cum[i] < need:
                j += 1
            if cum[j] - cum[i] < need:
                continue
            seg = pix[i:j + 1]
            a, b = np.array(seg[0]), np.array(seg[-1])
            chord = b - a
            L = np.linalg.norm(chord)
            if L < 1:
                continue
            nrm = np.array([-chord[1], chord[0]]) / L
            dev = max(abs(float(np.dot(np.array(p) - a, nrm))) for p in seg)
            if dev > px * 0.35:
                continue
            if near is not None and math.dist(pts[(i + j) // 2], near) > 6:
                continue
            c = (a + b) / 2
            if not (w / 2 + 8 < c[0] < W - w / 2 - 8 and h + 4 < c[1] < H - h):
                continue
            ang = math.degrees(math.atan2(chord[1], chord[0]))
            if ang > 90:
                ang -= 180
            if ang < -90:
                ang += 180
            rect = self.rect(c, w + px * 0.3, h * 1.1, ang)
            if not box(0, 0, W, H).contains(rect) or any(rect.intersects(t) for t in self.taken):
                continue
            return float(c[0]), float(c[1]), ang, pts[(i + j) // 2], rect
        return None

    def try_beside(self, ground, year, s, italic, px):
        """A level label beside the line, near its middle in the picture, with a leader: for a
        stretch too short or bent for a name along it. Returns (cx, cy, 0, mid, rect, leader)."""
        pts = densify(ground, 4)
        pix = self.to_px(locate(self.work, year, pts))
        W, H = self.size
        inside = [p for p in pix if 0 <= p[0] <= W and 0 <= p[1] <= H]
        if not inside:
            return None
        m = inside[len(inside) // 2]
        w, h = self.text_size(s, italic, px)
        for r in (px * 1.1, px * 1.6, px * 2.2, px * 3.0):
            for k in range(16):
                a = math.radians(-90 + k * 22.5)
                c = (m[0] + r * math.cos(a) * 1.4, m[1] + r * math.sin(a))
                rect = self.rect(c, w + px * 0.3, h * 1.1, 0)
                if not box(0, 0, W, H).contains(rect) or any(rect.intersects(t) for t in self.taken):
                    continue
                edge = rect.exterior.interpolate(rect.exterior.project(Point(m)))
                return c[0], c[1], 0.0, None, rect, (m[0], m[1], edge.x, edge.y)
        return None

    @staticmethod
    def rect(c, w, h, ang):
        t = math.radians(ang)
        ca, sa = math.cos(t), math.sin(t)
        corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        return Polygon([(c[0] + x * ca - y * sa, c[1] + x * sa + y * ca) for x, y in corners])

    def draw(self, im, c, ang, s, italic, px, color, leader=None):
        if leader:
            d = ImageDraw.Draw(im)
            d.line(leader, fill=PAPER, width=max(3, round(px * 0.16)))
            d.line(leader, fill=color, width=max(1, round(px * 0.06)))
            r = max(2, round(px * 0.1))
            d.ellipse((leader[0] - r, leader[1] - r, leader[0] + r, leader[1] + r), fill=color)
        f = font(px, italic=italic)
        b = f.getbbox(s)
        w, h = b[2] - b[0] + 16, b[3] - b[1] + 16
        layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((8 - b[0], 8 - b[1]), s, font=f, fill=color, stroke_width=max(2, round(px * 0.14)), stroke_fill=PAPER)
        layer = layer.rotate(-ang, resample=Image.BICUBIC, expand=True)
        im.paste(layer, (round(c[0] - layer.width / 2), round(c[1] - layer.height / 2)), layer)


def label_pair(work, crop_svg, z, px, keep_out, frame_m, data=None, priority=None, scenes=(1952, 2026)):
    """Labels for the 1952 and today halves of one crop. Returns {year: [(c, ang, text, italic,
    color)]} and the names left off, per year."""
    today, lost, joined, bridges, foot, traced, gaps = data
    x, y, w, h = crop_svg
    out = {1952: [], 2026: []}
    left = {1952: [], 2026: []}
    pl = {yr: Placer(work, crop_svg, z, px, keep_out) for yr in scenes}

    def visible(L, yr):
        pts = densify(L, 4)
        pix = pl[yr].to_px(locate(work, yr, pts))
        W, H = pl[yr].size
        inside = [p for p in pix if 0 <= p[0] <= W and 0 <= p[1] <= H]
        return len(inside) * 4 * len(pts) and len(inside) * L.length / max(1, len(pts) - 1)

    names = sorted(today, key=lambda n: -sum(visible(L, 2026) for L in today[n]))
    if priority:
        names.sort(key=lambda n: (n not in priority, priority.index(n) if n in priority else 0))
    for name in names:
        s = short(name)
        if sum(visible(L, 2026) for L in today[name]) < 40:
            continue
        both = []
        for L in sorted(today[name], key=lambda L: -L.length):
            both += eligible_1952(L, traced, gaps, foot, bridges)
        done = False
        # in both halves, at the same ground place, where the street ran in 1952 too
        for g in sorted(both, key=lambda g: -g.length):
            r = pl[2026].try_line(g, 2026, s, False, px)
            if r is None:
                continue
            r52 = pl[1952].try_line(g, 1952, s, False, px, near=r[3])
            if r52 is None:
                continue
            pl[2026].taken.append(r[4])
            pl[1952].taken.append(r52[4])
            out[2026].append(((r[0], r[1]), r[2], s, False, INK))
            out[1952].append(((r52[0], r52[1]), r52[2], s, False, INK))
            done = True
            break
        if not done:
            for L in sorted(today[name], key=lambda L: -L.length):
                r = pl[2026].try_line(L, 2026, s, False, px)
                if r is not None:
                    pl[2026].taken.append(r[4])
                    out[2026].append(((r[0], r[1]), r[2], s, False, INK))
                    done = True
                    break
            if not done:
                L = max(today[name], key=lambda L: visible(L, 2026))
                r = pl[2026].try_beside(L, 2026, s, False, px)
                if r is not None:
                    pl[2026].taken.append(r[4])
                    out[2026].append(((r[0], r[1]), 0.0, s, False, INK, r[5]))
                else:
                    left[2026].append(s)
            if both and not any(t[2] == s for t in out[1952]):
                g = max(both, key=lambda L: visible(L, 1952))
                r = pl[1952].try_beside(g, 1952, s, False, px) if visible(g, 1952) >= 30 else None
                if r is not None:
                    pl[1952].taken.append(r[4])
                    out[1952].append(((r[0], r[1]), 0.0, s, False, INK, r[5]))
                else:
                    left[1952].append(s)
    # the stretches under today's highway, joined across: upright, 1952 only, where the street is
    # not already named in the 1952 half
    for name, Ls in joined.items():
        s = short(name)
        if any(t[2] == s for t in out[1952]):
            continue
        for L in Ls:
            if visible(L, 1952) < 40:
                continue
            r = pl[1952].try_line(L, 1952, s, False, px)
            if r:
                pl[1952].taken.append(r[4])
                out[1952].append(((r[0], r[1]), r[2], s, False, INK))
    # the 1952 stretches the trench cut: italic, dark red
    for name, Ls in lost.items():
        s = short(name)
        for L in Ls:
            if visible(L, 1952) < 30:
                continue
            r = pl[1952].try_line(L, 1952, s, True, px)
            if r:
                pl[1952].taken.append(r[4])
                out[1952].append(((r[0], r[1]), r[2], s, True, LOST))
                continue
            r = pl[1952].try_beside(L, 1952, s, True, px)
            if r:
                pl[1952].taken.append(r[4])
                out[1952].append(((r[0], r[1]), 0.0, s, True, LOST, r[5]))
            else:
                left[1952].append('(1952) ' + s)
    return out, left, pl


def load_data(frame_m):
    """The streets, each line cut to the ground at least INSET_M inside the frame."""
    today, lost, joined, bridges, foot = streets(frame_m)
    inner = frame_m.buffer(-INSET_M)

    def clip(Ls):
        out = []
        for L in Ls:
            g = L.intersection(inner)
            out += [LineString([(round(x, 1), round(y, 1)) for x, y in p.coords])
                    for p in getattr(g, 'geoms', [g]) if p.geom_type == 'LineString' and p.length > 10]
        return out
    today = {n: c for n, c in ((n, clip(Ls)) for n, Ls in today.items()) if c}
    lost = {n: c for n, c in ((n, clip(Ls)) for n, Ls in lost.items()) if c}
    joined = {n: c for n, c in ((n, clip(Ls)) for n, Ls in joined.items()) if c}
    return today, lost, joined, bridges, foot, traced_1952(), untraced_gaps(frame_m)
