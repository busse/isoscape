#!/usr/bin/env python3
"""The guide's plan map: north up, a true plan, with today's streets named, the 1952 streets the
I-95 trench cut drawn and named in a second color and style, today's I-95/I-64 footprint,
Gilpin Court as a bordered area, the stops, the walk, a north arrow, a scale bar and credits.

    python3 tools/stories/jackson-ward-guide/map.py [--only phone,west,east,letter] [--full DIR] [--round N]

Writes pages/jackson-ward-guide-map-<name>.webp for the page (and, with --full, PNGs and the
letter PDF for review). Renderings:

  phone   the whole walk, tall (about 9:16), for a phone held upright; names that do not fit
          at this size are left off, and the two halves carry them all
  west    the west half (stops 3-5, and the cut streets toward Belvidere Street), names in full
  east    the east half (stops 1, 2 and 6-8), names in full; the halves overlap by about 160 m
  letter  the whole walk on a US Letter sheet, names in full

Everything is drawn in CSS pixels of the reader's screen (the phone renderings at 390 px wide)
and saved at three times that, so type sizes here are the sizes a reader sees. Labels are
placed in order of importance, each where it overlaps nothing already placed; a label that
fits nowhere is left off and listed in the run's output, so a rendering can be checked for
what it lost.

Sources: today's streets, bridges, the highway and the landmarks from OpenStreetMap (the
region's cache); the 1952 streets from the story's trace (the `street` features of
history/jackson-ward.json whose ids start "lost-" or "lost52-": the 31 stretches the story
draws); Gilpin Court's outline from gilpin.py; the stops and walk from route.json. Colors and
line weights are read from src/palette.ts (paper), never typed here.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, KX, KY, LAT0, LON0, ROOT, load, osm, palette, to_m  # noqa: E402

import numpy as np  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.patches  # noqa: E402,F401
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from PIL import ImageFont  # noqa: E402
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box as sbox  # noqa: E402
from shapely.ops import linemerge, unary_union  # noqa: E402

P = palette()


def mix(a, b, t):
    ra, rb = np.array(to_rgb(a)), np.array(to_rgb(b))
    return tuple(ra * (1 - t) + rb * t)


# Roles, each a palette color or a named mix of two.
C = {
    'paper': P['sky'],
    'ink': P['ink'],
    'muted': mix(P['ink'], P['sky'], 0.45),
    'street': mix(P['ink'], P['sky'], 0.62),
    'street_major': mix(P['ink'], P['sky'], 0.45),
    'alley': mix(P['ink'], P['sky'], 0.8),
    'highway': mix(P['ink'], P['sky'], 0.66),
    'highway_edge': mix(P['ink'], P['sky'], 0.4),
    'lost': P['mark']['line'],          # the 1952 streets the trench cut
    'gilpin_fill': P['plan'],
    'route': P['drive'],                # the suggested walk
    'route_band': P['driveBand'],
    'rail': P['rail'],
    'landmark': P['fresh'],
}
LW = P['lineWidth']          # the maps' line (0.6 SVG units); weights below are multiples of it
DASH = P['routeDash']

FONT = 'Inter' if any('Inter' in f.name for f in font_manager.fontManager.ttflist) else 'DejaVu Sans'
plt.rcParams.update({'font.family': FONT, 'text.color': C['ink']})


def _font_file(italic=False, bold=False):
    want = 'Inter-' + ('SemiBold' if bold else 'Regular' if not italic else '') + ('Italic' if italic else '') + '.otf'
    want = want.replace('Inter-Italic', 'Inter-Italic')
    for f in font_manager.fontManager.ttflist:
        if os.path.basename(f.fname) == want:
            return f.fname
    return font_manager.findfont(FONT)


_PIL = {}


def text_w(s, px, italic=False, bold=False):
    """Width of a line of text, in CSS px, at a font size of px."""
    k = (italic, bold, round(px * 10))
    if k not in _PIL:
        _PIL[k] = ImageFont.truetype(_font_file(italic, bold), size=max(1, round(px * 10)))
    return _PIL[k].getlength(s) / 10


SHORT = [('Saint ', 'St. '), (' Street', ' St.'), (' Avenue', ' Ave.'), (' Parkway', ' Pkwy.'), (' Road', ' Rd.'),
         ('North ', 'N. '), ('South ', 'S. '), ('East ', 'E. '), ('West ', 'W. '), (' Place', ' Pl.'), (' Drive', ' Dr.')]


def short(name):
    s = name
    for a, b in SHORT:
        s = s.replace(a, b)
    return s


# ---- the data -------------------------------------------------------------------------------

STREET_KINDS = {'primary': 'major', 'secondary': 'major', 'trunk': 'major', 'tertiary': 'minor', 'residential': 'minor',
                'unclassified': 'minor', 'living_street': 'minor', 'primary_link': 'link', 'secondary_link': 'link',
                'tertiary_link': 'link', 'service': 'alley', 'pedestrian': 'alley'}


def xy_of(g):
    return [to_m(q['lon'], q['lat']) for q in g]


def gather(bounds):
    x0, x1, y0, y1 = bounds
    clip = sbox(x0 - 200, y0 - 200, x1 + 200, y1 + 200)
    streets, bridges, motor, rail, named = [], [], [], [], {}
    landmarks = {}
    for e in osm():
        if e['type'] != 'way' or not e.get('geometry'):
            continue
        t = e.get('tags', {})
        pts = xy_of(e['geometry'])
        if len(pts) < 2 or not LineString(pts).intersects(clip):
            continue
        h = t.get('highway')
        if h in ('motorway', 'motorway_link'):
            lanes = 2
            try:
                lanes = int(str(t.get('lanes', '2')).split(';')[0])
            except ValueError:
                pass
            motor.append((LineString(pts), lanes * 3.65 / 2 + (3 if h == 'motorway' else 1.5)))
        elif h in STREET_KINDS:
            if h == 'service' and t.get('service') in ('parking_aisle', 'driveway', 'drive-through'):
                continue
            kind = STREET_KINDS[h]
            streets.append((pts, kind))
            if t.get('bridge') in ('yes', 'viaduct'):
                bridges.append((pts, kind))
            if t.get('name') and kind != 'alley':
                named.setdefault(t['name'], []).append((LineString(pts), kind))
        elif t.get('railway') == 'rail' and t.get('service') not in ('yard', 'siding', 'spur'):
            rail.append(pts)
        if e['id'] in (297832917, 321367756):    # Sixth Mt Zion Baptist Church; The Richmond Coliseum (OSM)
            landmarks[e['id']] = Polygon(pts)
    foot = unary_union([L.buffer(w, cap_style=2) for L, w in motor]).buffer(6).buffer(-6)
    lost = []
    for f in json.load(open(os.path.join(ROOT, 'history/jackson-ward.json')))['features']:
        if f.get('kind') == 'street' and (f['id'].startswith('lost-') or f['id'].startswith('lost52-')):
            lost.append((f['name'], LineString([to_m(*p) for p in f['line']]), f['id'].startswith('lost-')))
    gil = Polygon([to_m(*q) for q in load('gilpin-outline.json')['outline_lonlat']])
    return dict(streets=streets, bridges=bridges, foot=foot, rail=rail, named=named, lost=lost, gilpin=gil, landmarks=landmarks)


# ---- labels ---------------------------------------------------------------------------------

class Labeler:
    """Places labels (as rotated boxes in map meters) so that none overlaps another or a
    reserved area, and records what could not be placed."""

    def __init__(self, ax, mpp, bounds, inset):
        self.ax, self.mpp = ax, mpp
        x0, x1, y0, y1 = bounds
        self.inside = sbox(x0 + inset * mpp, y0 + inset * mpp, x1 - inset * mpp, y1 - inset * mpp)
        self.taken = []
        self.dropped = []

    def free(self, poly):
        return self.inside.contains(poly) and not any(poly.intersects(t) for t in self.taken)

    def reserve(self, poly):
        self.taken.append(poly)

    def rect(self, cx, cy, w_px, h_px, ang):
        w, h = w_px * self.mpp / 2, h_px * self.mpp / 2
        c, s = math.cos(ang), math.sin(ang)
        pts = [(-w, -h), (w, -h), (w, h), (-w, h)]
        return Polygon([(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts])

    def draw(self, cx, cy, s, px, ang, color, italic=False, bold=False, halo=True, z=20, lines=1):
        deg = math.degrees(ang)
        self.ax.text(cx, cy, s, fontsize=px * 0.72, rotation=deg, rotation_mode='anchor', ha='center', va='center',
                     color=color, style='italic' if italic else 'normal', fontweight=600 if bold else 'normal', zorder=z,
                     linespacing=1.1,
                     path_effects=[pe.withStroke(linewidth=px * 0.72 * 0.28, foreground=C['paper'])] if halo else None)

    def along(self, line, s, px, color, italic=False, bold=False, every=None, z=20, step=None, bend=0.35):
        """Place s along a line at the first free spots, each run straight over the label's
        length; with `every` (meters) more than once. Returns how many were placed."""
        w = text_w(s, px, italic, bold) + 4
        L_m = w * self.mpp
        if line.length < L_m * 0.9:
            return 0
        step = step or max(8.0, L_m / 4)
        placed = []
        # start from the middle of the line and work outward
        n = int(line.length // step)
        order = sorted(range(n + 1), key=lambda i: abs(i * step - line.length / 2))
        for i in order:
            d = i * step
            if d - L_m / 2 < 0 or d + L_m / 2 > line.length:
                continue
            if every and any(abs(d - q) < every for q in placed):
                continue
            if not every and placed:
                break
            a, b = line.interpolate(d - L_m / 2), line.interpolate(d + L_m / 2)
            seg = LineString([a, b])
            part = _substring(line, d - L_m / 2, d + L_m / 2)
            if part.hausdorff_distance(seg) > px * bend * self.mpp:
                continue
            ang = math.atan2(b.y - a.y, b.x - a.x)
            if ang > math.pi / 2:
                ang -= math.pi
            if ang < -math.pi / 2:
                ang += math.pi
            c = line.interpolate(d)
            r = self.rect(c.x, c.y, w, px * 1.25, ang)
            if self.free(r):
                self.reserve(r)
                self.draw(c.x, c.y, s, px, ang, color, italic, bold, z=z)
                placed.append(d)
        return len(placed)

    def near(self, x, y, s, px, color, italic=False, bold=False, reach=(0, 60), leader=False, z=21, prefer=None):
        """Place s horizontally at or near (x, y), trying rings of offsets out to reach[1] px."""
        lines = s.split('\n')
        w = max(text_w(t, px, italic, bold) for t in lines) + 4
        h = px * 1.25 * len(lines)
        tries = []
        for r in range(reach[0], reach[1] + 1, 6):
            for k in range(16):
                a = (prefer or 0) + k * math.pi / 8
                tries.append((r * math.cos(a), r * math.sin(a)))
            if r == 0:
                tries = tries[:1]
        for dx, dy in tries:
            cx, cy = x + dx * self.mpp, y + dy * self.mpp
            rr = self.rect(cx, cy, w, h, 0)
            if self.free(rr):
                self.reserve(rr)
                self.draw(cx, cy, s, px, 0, color, italic, bold, z=z)
                if leader and math.hypot(dx, dy) > 14:
                    edge = rr.exterior.interpolate(rr.exterior.project(Point(x, y)))
                    self.ax.plot([x, edge.x], [y, edge.y], color=color, lw=0.5, zorder=z - 1)
                return True
        self.dropped.append(s.replace('\n', ' '))
        return False


# Streets the walk uses or that frame it, named first so they keep their labels when space is short.
ROUTE_STREETS = ['Chamberlayne Parkway', 'North 2nd Street', 'East Leigh Street', 'West Duval Street', 'North 1st Street',
                 'East Duval Street', 'Chamberlayne Avenue', 'West Baker Street', 'East Bates Street', 'West Charity Street',
                 'East Broad Street', 'West Broad Street', 'North Belvidere Street', 'North 5th Street', 'East Baker Street']


def _substring(line, a, b):
    from shapely.ops import substring
    return substring(line, max(0, a), min(line.length, b))


# ---- drawing --------------------------------------------------------------------------------

def plot_lines(ax, pts, color, lw, z, ls='-', cap='round'):
    p = np.array(pts)
    ax.plot(p[:, 0], p[:, 1], color=color, lw=lw, ls=ls, zorder=z, solid_capstyle=cap, dash_capstyle='butt', solid_joinstyle='round')


def draw_map(ax, D, bounds, mpp, route, stops_in, full_labels, px_base):
    """Everything inside the map frame. Line widths are in points at the figure's dpi of 100
    CSS px per inch, so 1 pt is 100/72 CSS px."""
    pt = 72 / 100   # CSS px -> points
    x0, x1, y0, y1 = bounds
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(C['ink'])
        s.set_linewidth(LW * 1.6 * pt)
    ax.set_facecolor(C['paper'])
    # scale the street widths with the map: a residential street about 10 m wide, never under 1.2 px
    # line widths in CSS px, growing a little with the zoom but never to the street's true width,
    # so the walk and the names stay on top
    zoom = min(1.6, max(1.0, 2.6 / mpp))
    m = lambda meters, least: least * zoom * pt  # noqa: E731
    # Gilpin Court
    g = np.array(D['gilpin'].exterior.coords)
    ax.fill(g[:, 0], g[:, 1], color=C['gilpin_fill'], zorder=1, lw=0)
    ax.plot(g[:, 0], g[:, 1], color=C['ink'], lw=LW * 2.2 * pt, zorder=6, solid_joinstyle='round')
    # the highway
    for poly in getattr(D['foot'], 'geoms', [D['foot']]):
        q = np.array(poly.exterior.coords)
        ax.fill(q[:, 0], q[:, 1], color=C['highway'], zorder=2, lw=0)
        ax.plot(q[:, 0], q[:, 1], color=C['highway_edge'], lw=LW * pt, zorder=2.1)
        for hole in poly.interiors:
            h = np.array(hole.coords)
            ax.fill(h[:, 0], h[:, 1], color=C['paper'], zorder=2.05, lw=0)
            ax.plot(h[:, 0], h[:, 1], color=C['highway_edge'], lw=LW * pt, zorder=2.1)
    for pts in D['rail']:
        plot_lines(ax, pts, C['rail'], m(2.5, 1.0), 3)
        plot_lines(ax, pts, C['paper'], m(1.0, 0.4), 3.01, ls=(0, (3, 3)))
    # today's streets
    for pts, kind in D['streets']:
        if kind == 'alley':
            plot_lines(ax, pts, C['alley'], m(3, 0.7), 3.5)
    for pts, kind in D['streets']:
        if kind != 'alley':
            plot_lines(ax, pts, C['street_major'] if kind == 'major' else C['street'], m(14 if kind == 'major' else 9, 2.6 if kind == 'major' else 1.6), 4)
    # bridges over the trench: today's street with an inked casing
    for pts, kind in D['bridges']:
        w = m(14 if kind == 'major' else 9, 2.6 if kind == 'major' else 1.6)
        if not LineString(pts).intersects(D['foot']):
            continue
        plot_lines(ax, pts, C['ink'], w + 2.4 * pt, 4.4, cap='butt')
        plot_lines(ax, pts, C['paper'], w + 0.6 * pt, 4.45, cap='butt')
        plot_lines(ax, pts, C['street_major'] if kind == 'major' else C['street'], w, 4.5, cap='butt')
    # the 1952 streets the trench cut: dashed, in the mark's dark red, under today's bridges
    for name, L, joined in D['lost']:
        plot_lines(ax, list(L.coords), C['lost'], m(5, 1.6), 4.3, ls=(0, (2.2, 1.2)), cap='butt')
    # landmarks
    for wid, poly in D['landmarks'].items():
        q = np.array(poly.exterior.coords)
        ax.fill(q[:, 0], q[:, 1], color=C['landmark'], zorder=5, lw=0, alpha=0.85)
        ax.plot(q[:, 0], q[:, 1], color=C['ink'], lw=LW * pt, zorder=5.1)
    # the walk
    for leg in route['path']:
        p = np.array(leg)
        ax.plot(p[:, 0], p[:, 1], color=C['route'], lw=3.4 * zoom * pt, zorder=7, alpha=0.9,
                solid_capstyle='round', solid_joinstyle='round')
    lab = Labeler(ax, mpp, bounds, inset=4)
    # keep labels off the scale bar and the north arrow (drawn after, at these places)
    sx, sy = x0 + 12 * mpp, y0 + 34 * mpp
    lab.reserve(sbox(sx - 8 * mpp, sy - 28 * mpp, sx + 200 + 64 * mpp, sy + 26 * mpp))
    lab.reserve(sbox(x1 - 40 * mpp, y1 - 44 * mpp, x1, y1))
    for poly in D['landmarks'].values():     # no street name across a landmark
        lab.reserve(poly)
    # stops (reserve their discs first)
    r_px = 9.5 if px_base < 11 else 11
    for s in route['stops']:
        x, y = s['xy']
        if not (x0 < x < x1 and y0 < y < y1):
            continue
        ax.add_patch(plt.Circle((x, y), r_px * mpp, color=C['ink'], zorder=30))
        ax.add_patch(plt.Circle((x, y), r_px * mpp, fill=False, ec=C['paper'], lw=1.4 * pt, zorder=30.1))
        ax.text(x, y - 0.4 * mpp, str(s['n']), ha='center', va='center', fontsize=r_px * 1.15 * pt, color=C['paper'], fontweight=700, zorder=31)
        lab.reserve(Point(x, y).buffer((r_px + 2) * mpp))
    # labels in order of importance: the streets the walk uses, then landmarks, then the rest
    view = sbox(x0, y0, x1, y1)
    names = []
    for name, parts in D['named'].items():
        geo = linemerge(MultiLineString([L for L, k in parts]))
        geo = geo.intersection(view)
        if geo.is_empty:
            continue
        major = any(k == 'major' for _, k in parts)
        segs = [g for g in getattr(geo, 'geoms', [geo]) if g.geom_type == 'LineString']
        names.append((not major, -sum(g.length for g in segs), name, segs))
    names.sort(key=lambda t: (t[2] not in ROUTE_STREETS, ROUTE_STREETS.index(t[2]) if t[2] in ROUTE_STREETS else 0, t[0], t[1]))

    def name_street(name, segs):
        ok = 0
        for size in ((px_base, px_base * 0.88) if name in ROUTE_STREETS else (px_base,)):
            for g in sorted(segs, key=lambda g: -g.length):
                ok += lab.along(g, short(name), size, C['ink'], every=520 if full_labels else 900)
                if ok and not full_labels:
                    break
            if ok:
                break
        if not ok and name in ROUTE_STREETS:
            g = max(segs, key=lambda g: g.length)
            c = g.interpolate(0.5, normalized=True)
            ok = lab.near(c.x, c.y, short(name), px_base * 0.92, C['ink'], reach=(10, 40))
            if ok:
                return
        if not ok:
            lab.dropped.append(short(name))
    lm = D['landmarks']
    if 297832917 in lm:
        c = lm[297832917].centroid
        lab.near(c.x, c.y, 'Sixth Mount Zion\nBaptist Church', px_base, C['ink'], bold=True, reach=(14, 130), leader=True, prefer=-math.pi / 2)
    if 321367756 in lm and lm[321367756].centroid.within(sbox(x0, y0, x1, y1)):
        c = lm[321367756].centroid
        lab.near(c.x, c.y, 'Richmond Coliseum', px_base, C['ink'], bold=True, reach=(10, 80), prefer=math.pi, leader=True)
    gc = D['gilpin'].representative_point()
    gb = D['gilpin'].intersection(sbox(x0, y0, x1, y1))
    if not gb.is_empty:
        p = gb.representative_point() if not gb.contains(gc) else gc
        # prefer the area's own middle, away from the stop at its west edge
        cx, cy = (gb.centroid.x, gb.centroid.y) if gb.contains(gb.centroid) else (p.x, p.y)
        lab.near(cx, cy, 'Gilpin Court\n(RRHA public housing)', px_base * 1.05, C['ink'], bold=True, reach=(0, 120))
    for _, _, name, segs in names:
        if name in ROUTE_STREETS:
            name_street(name, segs)
    # JXN Haus: on Bates Street (the story); OSM does not map it, so it is named along the street
    bates = [L for L, k in D['named'].get('East Bates Street', [])]
    # the highway's name, in the trench
    hw = D['foot'].intersection(sbox(x0, y0, x1, y1))
    if not hw.is_empty:
        big = max(getattr(hw, 'geoms', [hw]), key=lambda q: q.area)
        spine = _spine(big)
        if spine is not None:
            if not lab.along(spine, 'I-95 / I-64', px_base * 1.05, C['ink'], bold=True, every=650 if full_labels else None, bend=1.2):
                lab.dropped.append('I-95 / I-64')
    # the 1952 streets: their labels in italic dark red, along the stretch if it fits, or beside it
    for name, L, joined in sorted(D['lost'], key=lambda t: -t[1].length):
        if joined:      # the seven stretches joining a street that survives: today's name stands for them
            continue
        if not L.intersects(view):
            continue
        s = short(name)
        if lab.along(L, s, px_base * 0.95, C['lost'], italic=True, step=4):
            continue
        c = L.interpolate(0.5, normalized=True)
        if not lab.near(c.x, c.y, s, px_base * 0.95, C['lost'], italic=True, reach=(8, 110 if full_labels else 30), leader=True):
            lab.dropped[-1] = '(1952) ' + s
    for _, _, name, segs in names:
        if name not in ROUTE_STREETS:
            name_street(name, segs)
    if bates:
        geo = linemerge(MultiLineString(bates))
        geo = max(getattr(geo, 'geoms', [geo]), key=lambda g: g.length)
        mid = geo.interpolate(0.5, normalized=True)
        lab.near(mid.x, mid.y, 'JXN Haus\n(on Bates St.)', px_base, C['ink'], bold=True, reach=(16, 90), leader=True, prefer=-math.pi / 2)
    return lab


def _spine(poly):
    """A rough center line of the highway's footprint: its long axis, sampled."""
    q = np.array(poly.exterior.coords)
    c = q.mean(0)
    u, s_, vt = np.linalg.svd(q - c, full_matrices=False)
    d = vt[0]
    t = (q - c) @ d
    a, b = t.min(), t.max()
    pts = []
    for k in np.linspace(a, b, 60):
        p = c + d * k
        n = np.array([-d[1], d[0]])
        cut = LineString([p - n * 400, p + n * 400]).intersection(poly)
        if cut.is_empty:
            continue
        mid = cut.centroid
        pts.append((mid.x, mid.y))
    if len(pts) < 2:
        return None
    return LineString(pts).simplify(15)


# ---- furniture ------------------------------------------------------------------------------

def north_arrow(ax, x, y, size_px, mpp):
    s = size_px * mpp
    ax.add_patch(plt.Polygon([(x, y + s), (x - s * 0.32, y - s * 0.35), (x, y - s * 0.12), (x + s * 0.32, y - s * 0.35)],
                             closed=True, fc=C['ink'], ec=C['ink'], lw=0.5, zorder=40))
    ax.text(x, y + s * 1.05, 'N', ha='center', va='bottom', fontsize=size_px * 0.62 * 0.72, fontweight=700, zorder=40,
            path_effects=[pe.withStroke(linewidth=2, foreground=C['paper'])])


def scale_bar(ax, x, y, mpp, px_base, walk):
    """Meters above, feet below, and the walking time a 400 m stretch takes."""
    pt = 72 / 100
    m_len, ft_len = 200, 500
    ftm = ft_len * 0.3048
    tick = 4 * mpp
    ax.add_patch(plt.Rectangle((x - 6 * mpp, y - 26 * mpp), (m_len + 16 * mpp) if False else max(m_len, ftm) + 60 * mpp, 50 * mpp,
                               fc=C['paper'], ec='none', alpha=0.85, zorder=39))
    ax.plot([x, x + m_len], [y, y], color=C['ink'], lw=1.6 * pt * 1.4, zorder=40, solid_capstyle='butt')
    for t in (0, 100, 200):
        ax.plot([x + t, x + t], [y, y + tick], color=C['ink'], lw=1.0 * pt * 1.4, zorder=40)
    ax.text(x + m_len + 4 * mpp, y + 2 * mpp, '200 m', fontsize=px_base * 0.9 * pt, va='bottom', zorder=40)
    ax.plot([x, x + ftm], [y - 2 * mpp, y - 2 * mpp], color=C['ink'], lw=0.8 * pt * 1.4, zorder=40)
    for t in (0, 250, 500):
        ax.plot([x + t * 0.3048] * 2, [y - 2 * mpp, y - 2 * mpp - tick], color=C['ink'], lw=1.0 * pt * 1.4, zorder=40)
    ax.text(x + ftm + 4 * mpp, y - 3 * mpp, '500 ft', fontsize=px_base * 0.9 * pt, va='top', zorder=40)
    ax.text(x, y - 16 * mpp, f'200 m is about {200 / walk:.1f} minutes on foot', fontsize=px_base * 0.85 * pt, va='top', color=C['ink'], zorder=40)


def key_and_credits(fig, rect, px_base, route, which, dropped_note):
    """The key and credits, drawn into a band of the figure (rect in figure fractions)."""
    pt = 72 / 100
    ax = fig.add_axes(rect)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    W = fig.get_figwidth() * 100 * rect[2]     # band width in CSS px
    Hh = fig.get_figheight() * 100 * rect[3]
    fx = lambda px: px / W   # noqa: E731
    fy = lambda px: px / Hh  # noqa: E731
    y = 1 - fy(6)
    row = px_base * 1.7
    items = [
        ('street', 'Streets today, named upright (OpenStreetMap)'),
        ('bridge', 'A street on a bridge over the highway today'),
        ('lost', '1952 streets the trench cut: dashed, named in italic (Sanborn maps, 1952, as traced for the story)'),
        ('highway', 'I-95 / I-64 today, in its trench'),
        ('gilpin', 'Gilpin Court, RRHA public housing; outline approximate, from city parcel records'),
        ('route', f'The suggested walk: {route["total_m"] / 1000:.1f} km ({route["total_m"] / 1609.34:.1f} miles), about {round(route["total_m"] / route["walk_m_per_min"] / 5) * 5} minutes of walking'),
        ('stop', 'A stop: where to stand, on a public sidewalk'),
        ('landmark', 'A landmark named in the guide'),
    ]
    sw = fx(30)
    import textwrap
    cols = 2 if W > 600 else 1
    colw = W / cols
    tchars = int((colw - 46) / (px_base * 0.92 * 0.53))
    ytop, ys = y, []
    for i, (kind, text) in enumerate(items):
        col = i * cols // len(items)
        if cols > 1 and i == len(items) // 2:
            ys.append(y)
            y = ytop
        x0k = fx(col * colw)
        text = '\n'.join(textwrap.wrap(text, tchars))
        nl = text.count('\n') + 1
        yy = y - fy(px_base * 1.25 * nl + px_base * 0.45) / 2
        xs = [x0k + fx(4), x0k + fx(4) + sw]
        if kind == 'street':
            ax.plot(xs, [yy, yy], color=C['street'], lw=2.2 * pt * 1.4, solid_capstyle='butt')
        elif kind == 'bridge':
            ax.plot(xs, [yy, yy], color=C['ink'], lw=5.2 * pt, solid_capstyle='butt')
            ax.plot(xs, [yy, yy], color=C['paper'], lw=3.6 * pt, solid_capstyle='butt')
            ax.plot(xs, [yy, yy], color=C['street'], lw=2.8 * pt, solid_capstyle='butt')
        elif kind == 'lost':
            ax.plot(xs, [yy, yy], color=C['lost'], lw=2.2 * pt, ls=(0, (2.2, 1.2)), dash_capstyle='butt')
        elif kind in ('highway', 'gilpin', 'landmark'):
            fc = {'highway': C['highway'], 'gilpin': C['gilpin_fill'], 'landmark': C['landmark']}[kind]
            ec = {'highway': C['highway_edge'], 'gilpin': C['ink'], 'landmark': C['ink']}[kind]
            ax.add_patch(plt.Rectangle((xs[0], yy - fy(px_base * 0.45)), sw if kind != 'landmark' else fx(12), fy(px_base * 0.9), fc=fc, ec=ec,
                                       lw=(1.4 if kind == 'gilpin' else 0.6) * pt))
        elif kind == 'route':
            ax.plot(xs, [yy, yy], color=C['route'], lw=3.6 * pt, solid_capstyle='round')
        elif kind == 'stop':
            ax.add_patch(matplotlib.patches.Ellipse((xs[0] + fx(8), yy), fx(16), fy(16), color=C['ink']))
            ax.text(xs[0] + fx(8), yy, '1', ha='center', va='center', color=C['paper'], fontsize=px_base * 0.9 * pt, fontweight=700)
        style = 'italic' if kind == 'lost' else 'normal'
        ax.text(xs[1] + fx(8), yy, text, va='center', fontsize=px_base * 0.92 * pt, style=style,
                color=C['lost'] if kind == 'lost' else C['ink'], linespacing=1.15)
        y -= fy(px_base * 1.25 * nl + px_base * 0.45)
    y = min([y] + ys)
    credit = ('Streets, bridges, highway, landmarks: © OpenStreetMap contributors (ODbL). 1952 streets: Sanborn Fire Insurance Map, Richmond, 1952, '
              'vol. 3, Library of Congress (public domain), read off the sheets for the Jackson Ward story; seven stretches joined across the trench as '
              'the USGS Richmond map of 1933–34 shows them. Gilpin Court outline: City of Richmond parcel records (RRHA multi-family parcels), approximate. '
              f'Walking time at about {route["walk_m_per_min"]} m a minute. Drawn by Chris Busse with isoscape, built with Claude. Draft, November 2026.')
    if dropped_note:
        credit = dropped_note + ' ' + credit
    import textwrap
    chars = int(W / (px_base * 0.8 * 0.52))
    ax.text(fx(4), y - fy(4), '\n'.join(textwrap.wrap(credit, chars)), va='top', fontsize=px_base * 0.8 * pt, color=C['muted'], linespacing=1.3)
    if which == 'letter':
        # the stops, where to stand, for the printed sheet
        n_lines = len(textwrap.wrap(credit, chars))
        y -= fy(px_base * 0.8 * 1.3 * n_lines + 18)
        ax.text(fx(4), y, 'The stops', va='top', fontsize=px_base * 1.05 * pt, fontweight=700)
        y -= fy(px_base * 1.7)
        y0s, half = y, (len(route['stops']) + 1) // 2
        wchars = int((colw - 30) / (px_base * 0.9 * 0.52))
        for i, st in enumerate(route['stops']):
            if i == half:
                y = y0s
            x0k = fx(4 + (colw if i >= half else 0))
            body = textwrap.wrap(f"{st['title']}. Stand {st['where']}; look {st['sees']}.", wchars)
            ax.text(x0k, y, f"{st['n']}", va='top', fontsize=px_base * 0.9 * pt, fontweight=700)
            ax.text(x0k + fx(14), y, '\n'.join(body), va='top', fontsize=px_base * 0.9 * pt, linespacing=1.25)
            y -= fy(px_base * 0.9 * 1.25 * len(body) + 6)


RENDERS = {
    # name: (bounds x0, x1, y0, y1 in plan meters, width in CSS px, base type size px, full labels, title)
    'phone': ((-780, 680, -745, 520), 390, 10.5, False, 'Seeing the change: a walk in Jackson Ward'),
    'west': ((-780, 40, -150, 520), 390, 11, True, 'West half: stops 3 to 5, and the Belvidere end'),
    'east': ((-120, 680, -745, 250), 390, 11, True, 'East half: stops 1, 2 and 6 to 8'),
    'letter': ((-780, 680, -745, 520), 765, 8.6, True, 'Seeing the change: a walk in Jackson Ward, Richmond, Virginia'),
}


def render(name, out_full, rnd):
    bounds, W, px, full, title = RENDERS[name]
    x0, x1, y0, y1 = bounds
    mpp = (x1 - x0) / (W - 2)
    map_h = (y1 - y0) / mpp
    D = gather(bounds)
    route = load('route.json')
    head = px * 3.6
    keyh = px * 1.7 * 8 + px * 1.25 * (5 if W < 500 else 0) + px * 0.8 * 1.3 * (10 if W < 500 else 5) + 30
    if name == 'letter':
        H = W * 11 / 8.5
        margin = 36
        key_need = px * 1.25 * 2 * 4 + px * 0.45 * 4 + px * 0.8 * 1.3 * 5 + 24
        avail = H - 2 * margin - head - key_need
        mpp = max((x1 - x0) / (W - 2 * margin), (y1 - y0) / avail)
        Wm = (x1 - x0) / mpp
        map_h = (y1 - y0) / mpp
        fig = plt.figure(figsize=(W / 100, H / 100))
        top = (H - margin - head) / H
        ax = fig.add_axes([(W - Wm) / 2 / W, top - map_h / H, Wm / W, map_h / H])
        key_rect = [(W - Wm) / 2 / W, margin / H, Wm / W, (top - map_h / H) - margin / H - 8 / H]
        title_y = (H - margin - 4) / H
        title_x = (W - Wm) / 2 / W
    else:
        H = head + map_h + keyh
        fig = plt.figure(figsize=(W / 100, H / 100))
        ax = fig.add_axes([1 / W, (keyh) / H, (W - 2) / W, map_h / H])
        key_rect = [6 / W, 2 / H, (W - 12) / W, (keyh - 8) / H]
        title_y = (H - 6) / H
        title_x = 8 / W
    fig.patch.set_facecolor(C['paper'])
    lab = draw_map(ax, D, bounds, mpp, route, None, full, px)
    north_arrow(ax, x1 - 22 * mpp, y1 - 30 * mpp, 18, mpp)
    sx = x0 + 12 * mpp
    scale_bar(ax, sx, y0 + 34 * mpp, mpp, px, route['walk_m_per_min'])
    fig.text(title_x, title_y, title, fontsize=px * 1.35 * 0.72, fontweight=700, va='top', ha='left')
    sub = ('North is up. Numbers are the stops, in walking order.' if name in ('phone', 'letter') else
           'North is up. The two halves overlap; together they name every street.')
    fig.text(title_x, title_y - px * 1.75 / H, sub, fontsize=px * 0.92 * 0.72, va='top', ha='left', color=C['muted'])
    note = 'Some names are left off at this size; the west and east halves name every street.' if name == 'phone' else ''
    key_and_credits(fig, key_rect, px, route, name, note)
    base = f'jackson-ward-guide-map-{name}'
    os.makedirs(os.path.join(ROOT, 'out/stories/jackson-ward-guide'), exist_ok=True)
    png = os.path.join(ROOT, 'out/stories/jackson-ward-guide', base + '.png')
    fig.savefig(png, dpi=300)
    if name == 'letter' and out_full:
        fig.savefig(os.path.join(out_full, base + f'-r{rnd}.pdf'))
    plt.close(fig)
    from PIL import Image
    im = Image.open(png).convert('RGB')
    im.save(os.path.join(ROOT, 'pages', base + '.webp'), quality=88, method=6)
    if out_full:
        os.makedirs(out_full, exist_ok=True)
        im.save(os.path.join(out_full, base + f'-r{rnd}.png'), optimize=True)
        im.resize((W, round(im.height * W / im.width)), Image.LANCZOS).save(os.path.join(out_full, base + f'-r{rnd}-{W}.png'))
    print(name, im.size, 'left off:', sorted(set(lab.dropped)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None)
    ap.add_argument('--full', default=None)
    ap.add_argument('--round', default='1')
    a = ap.parse_args()
    for n in (a.only.split(',') if a.only else RENDERS):
        render(n, a.full, a.round)


if __name__ == '__main__':
    main()
