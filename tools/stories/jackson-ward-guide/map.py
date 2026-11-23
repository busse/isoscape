#!/usr/bin/env python3
"""The guide's plan maps: north up, a true plan, every street named, today's and the 1952 streets
the I-95 trench cut, with a grid (A-F, 1-6) to find a place by, the bridges over the trench, the
streets that end at it, the highway's numbered exits, landmarks, Gilpin Court as a bordered area,
and the vantage points with which way to look. No route.

    python3 tools/stories/jackson-ward-guide/map.py [--only overview,tile-1,...,sheet] [--full DIR] [--round N]

Renderings (orient.py's PLAN is the frame and the grid of all of them):

  overview  the whole frame at 390 px: the grid, the main streets, the highway, the places to
            stand, landmarks, with the key; which tile covers which squares is said under it
  tile-1..6 the frame in six tiles of two columns by three rows (500 by 630 m, with 30 m of overlap),
            390 px wide, each with a locator; on each, every street with 30 m or more inside it is
            named, at 13 px where it fits, else smaller (not under 11.5 px) or beside the street
            with a leader
  sheet     the whole frame for the folded sheet (fold.py): 8.9 x 7.5 in, every street named at
            8.5 pt or more, saved also as an SVG with its text kept as text

Everything is drawn in CSS pixels of the reader's screen and saved at three times that, so type
sizes here are the sizes a reader sees. Labels are placed in order of importance, each where it
overlaps nothing placed before; each run lists any name it could not place (`dropped`), and a
rendering that drops a name fails the run.

Sources: today's streets, bridges, the highway, its exits and the landmarks from OpenStreetMap
(the region's cache, through orient.py); the 1952 streets from the story's trace (the `street`
features of history/jackson-ward.json whose ids start "lost-" or "lost52-"); Gilpin Court's
outline from gilpin.py; the vantage points from vantage.py. Colors and line weights are read from
src/palette.ts (paper), never typed here.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, KX, KY, LAT0, LON0, ROOT, load, osm, palette, to_m  # noqa: E402
from orient import COLS, LANDMARKS, PLAN, ROWS  # noqa: E402

LANDMARK_IDS = set(LANDMARKS)

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
    'cone': P['drive'],                 # the view cone at a place to stand
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
            if t.get('name'):
                named.setdefault(t['name'], []).append((LineString(pts), kind))
        elif t.get('railway') == 'rail' and t.get('service') not in ('yard', 'siding', 'spur'):
            rail.append(pts)
        if e['id'] in LANDMARK_IDS:
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
        kw = dict(fontsize=px * 0.72, rotation=deg, rotation_mode='anchor', ha='center', va='center',
                  style='italic' if italic else 'normal', fontweight=600 if bold else 'normal', linespacing=1.1)
        if halo:
            # the halo on its own, under the text: matplotlib draws text with path effects as
            # outlines, so the name itself is drawn plainly on top and stays text in an SVG or PDF
            self.ax.text(cx, cy, s, color=C['paper'], zorder=z - 0.01,
                         path_effects=[pe.withStroke(linewidth=px * 0.72 * 0.28, foreground=C['paper'])], **kw)
        self.ax.text(cx, cy, s, color=color, zorder=z, **kw)

    def along(self, line, s, px, color, italic=False, bold=False, every=None, z=20, step=None, bend=0.35, toward=None):
        """Place s along a line at the first free spots, each run straight over the label's
        length; with `every` (meters) more than once. Returns how many were placed."""
        px = max(px, CURRENT.get('min_px') or 0)
        w = text_w(s, px, italic, bold) + 4
        L_m = w * self.mpp
        if line.length < L_m * 0.9:
            return 0
        step = step or max(8.0, L_m / 4)
        placed = []
        # start from the middle of the line and work outward
        n = int(line.length // step)
        mid = line.project(toward) if toward is not None else line.length / 2
        order = sorted(range(n + 1), key=lambda i: abs(i * step - mid))
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
        px = max(px, CURRENT.get('min_px') or 0)
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




def _substring(line, a, b):
    from shapely.ops import substring
    return substring(line, max(0, a), min(line.length, b))


def plot_lines(ax, pts, color, lw, z, ls='-', cap='round'):
    p = np.array(pts)
    ax.plot(p[:, 0], p[:, 1], color=color, lw=lw, ls=ls, zorder=z, solid_capstyle=cap, dash_capstyle='butt', solid_joinstyle='round')


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


def north_arrow(ax, x, y, size_px, mpp):
    s = size_px * mpp
    ax.add_patch(plt.Polygon([(x, y + s), (x - s * 0.32, y - s * 0.35), (x, y - s * 0.12), (x + s * 0.32, y - s * 0.35)],
                             closed=True, fc=C['ink'], ec=C['ink'], lw=0.5, zorder=40))
    ax.text(x, y + s * 1.05, 'N', ha='center', va='bottom', fontsize=size_px * 0.62 * 0.72, fontweight=700, zorder=40,
            path_effects=[pe.withStroke(linewidth=2, foreground=C['paper'])])

# ---- what is named -------------------------------------------------------------------------

# The overview names only these, so it stays legible at 390 px; the tiles and the sheet name all.
OVERVIEW_STREETS = ['North 2nd Street', 'East Leigh Street', 'West Leigh Street', 'Chamberlayne Parkway', 'North 1st Street',
                    'North Belvidere Street', 'East Broad Street', 'West Broad Street', 'North 5th Street', 'North 7th Street']
MIN_IN_VIEW = 30          # m: a street with this much inside a rendering is named on it
REACH = 70                # px: the farthest a name set beside its street may sit, with a leader
TILE_W, TILE_H, OVERLAP = 500, 630, 30


def tile_bounds(i):
    """Tile i (0-5): columns A-B, C-D, E-F; rows 1-3, 4-6."""
    x0, x1, y0, y1 = PLAN
    c, r = i % 3, i // 3
    return (x0 + c * TILE_W - OVERLAP, x0 + (c + 1) * TILE_W + OVERLAP, y1 - (r + 1) * TILE_H - OVERLAP, y1 - r * TILE_H + OVERLAP)


def tile_squares(i):
    c, r = i % 3, i // 3
    return f'{COLS[2 * c]}{3 * r + 1}–{COLS[2 * c + 1]}{3 * r + 3}'


RENDERS = {'overview': dict(bounds=PLAN, W=390, px=11.5, mode='overview', title='Jackson Ward, north up')}
for _i in range(6):
    RENDERS[f'tile-{_i + 1}'] = dict(bounds=tile_bounds(_i), W=390, px=12.5, mode='full', title=f'Map {_i + 1}: squares {tile_squares(_i)}', tile=_i)
RENDERS['sheet'] = dict(bounds=PLAN, W=893, px=11.8, mode='full', title='', sheet=True)
CURRENT = {'name': None, 'min_px': None}
KEY_GAP = 22   # CSS px of clear paper between a map and its key


# ---- drawing --------------------------------------------------------------------------------

def draw_grid(ax, bounds, mpp, px, lab):
    """Thin lines at the grid's squares, their letters and numbers in tabs along the frame."""
    pt = 72 / 100
    x0, x1, y0, y1 = PLAN
    vx0, vx1, vy0, vy1 = bounds
    cw, rh = (x1 - x0) / len(COLS), (y1 - y0) / ROWS
    for k in range(len(COLS) + 1):
        x = x0 + k * cw
        if vx0 < x < vx1:
            ax.plot([x, x], [max(y0, vy0), min(y1, vy1)], color=C['ink'], lw=0.7 * pt, alpha=0.55, ls=(0, (6, 4)), zorder=8)
    for k in range(ROWS + 1):
        y = y1 - k * rh
        if vy0 < y < vy1:
            ax.plot([max(x0, vx0), min(x1, vx1)], [y, y], color=C['ink'], lw=0.7 * pt, alpha=0.55, ls=(0, (6, 4)), zorder=8)
    tab = px * 1.25 * mpp
    for k, c in enumerate(COLS):
        cx = x0 + (k + 0.5) * cw
        if vx0 + tab < cx < vx1 - tab:
            for cy, va in ((vy1 - 2 * mpp, 'top'), (vy0 + 2 * mpp, 'bottom')):
                ax.text(cx, cy, c, ha='center', va=va, fontsize=px * (1.0 if CURRENT.get('min_px') else 0.95) * pt, fontweight=700, zorder=42,
                        bbox=dict(boxstyle='square,pad=0.18', fc=C['paper'], ec=C['ink'], lw=0.5))
                yy = cy - tab if va == 'top' else cy
                lab.reserve(sbox(cx - tab * 0.7, yy, cx + tab * 0.7, yy + tab))
    for k in range(ROWS):
        cy = y1 - (k + 0.5) * rh
        if vy0 + tab < cy < vy1 - tab:
            for cx, ha in ((vx0 + 2 * mpp, 'left'), (vx1 - 2 * mpp, 'right')):
                ax.text(cx, cy, str(k + 1), ha=ha, va='center', fontsize=px * (1.0 if CURRENT.get('min_px') else 0.95) * pt, fontweight=700, zorder=42,
                        bbox=dict(boxstyle='square,pad=0.18', fc=C['paper'], ec=C['ink'], lw=0.5))
                xx = cx if ha == 'left' else cx - tab
                lab.reserve(sbox(xx, cy - tab * 0.6, xx + tab, cy + tab * 0.6))


def cone(ax, x, y, face, mpp, z=7.5, r_px=46):
    """A view cone: a wedge 50 degrees wide toward `face` (degrees from north)."""
    r = r_px * mpp
    pts = [(x, y)]
    for a in np.linspace(face - 25, face + 25, 12):
        t = math.radians(a)
        pts.append((x + r * math.sin(t), y + r * math.cos(t)))
    ax.add_patch(plt.Polygon(pts, closed=True, fc=C['cone'], ec=C['ink'], lw=0.6, alpha=0.45, zorder=z))
    return Polygon(pts)


def end_bar(ax, p, toward, mpp, z=6):
    """A short bar across a street where it ends at the trench."""
    dx, dy = toward[0] - p[0], toward[1] - p[1]
    k = math.hypot(dx, dy) or 1
    nx_, ny_ = -dy / k, dx / k
    h = 7 * mpp
    ax.plot([p[0] - nx_ * h, p[0] + nx_ * h], [p[1] - ny_ * h, p[1] + ny_ * h], color=C['ink'], lw=2.2 * 72 / 100, zorder=z,
            solid_capstyle='butt')


def draw_map(ax, D, O, V, bounds, mpp, mode, px_base):
    pt = 72 / 100
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
    zoom = min(1.6, max(1.0, 2.6 / mpp))
    m = lambda meters, least: least * zoom * pt  # noqa: E731
    view = sbox(x0, y0, x1, y1)
    full = mode == 'full'
    R = RENDERS[CURRENT['name']]
    # the part a name is owed on: a tile's own squares (its overlap is room to spare); the frame
    core = view.intersection(sbox(PLAN[0], PLAN[2], PLAN[1], PLAN[3]))
    if 'tile' in R:
        core = core.intersection(sbox(x0 + OVERLAP, y0 + OVERLAP, x1 - OVERLAP, y1 - OVERLAP))
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
    for pts, kind in D['streets']:
        if kind == 'alley':
            plot_lines(ax, pts, C['alley'], m(3, 0.7), 3.5)
    for pts, kind in D['streets']:
        if kind != 'alley':
            plot_lines(ax, pts, C['street_major'] if kind == 'major' else C['street'], m(14, 2.6) if kind == 'major' else m(9, 1.6), 4)
    for pts, kind in D['bridges']:
        w = m(14, 2.6) if kind == 'major' else m(9, 1.6)
        if not LineString(pts).intersects(D['foot']):
            continue
        plot_lines(ax, pts, C['ink'], w + 2.4 * pt, 4.4, cap='butt')
        plot_lines(ax, pts, C['paper'], w + 0.6 * pt, 4.45, cap='butt')
        plot_lines(ax, pts, C['street_major'] if kind == 'major' else C['street'], w, 4.5, cap='butt')
    for name, L, joined in D['lost']:
        plot_lines(ax, list(L.coords), C['lost'], m(5, 1.6), 4.3, ls=(0, (2.2, 1.2)), cap='butt')
    # where streets end at the trench: a bar across the street's end
    for r in O['index']:
        for e in r['ends']:
            p = e['xy']
            if x0 < p[0] < x1 and y0 < p[1] < y1:
                parts = [L for L, k in D['named'].get(r['name'], [])]
                near = min(parts, key=lambda L: L.distance(Point(p)), default=None)
                if near is not None:
                    q = near.interpolate(near.project(Point(p)) + (-8 if near.project(Point(p)) > near.length / 2 else 8))
                    end_bar(ax, p, (q.x, q.y), mpp)
    for wid, poly in D['landmarks'].items():
        q = np.array(poly.exterior.coords)
        ax.fill(q[:, 0], q[:, 1], color=C['landmark'], zorder=5, lw=0, alpha=0.85)
        ax.plot(q[:, 0], q[:, 1], color=C['ink'], lw=LW * pt, zorder=5.1)
    lab = Labeler(ax, mpp, bounds, inset=4)
    draw_grid(ax, bounds, mpp, px_base, lab)
    # places to stand: cones, then discs
    r_px = 14 if CURRENT.get('min_px') else (9.5 if px_base < 12 else 10.5)
    for v in V:
        x, y = v['xy']
        if not (x0 < x < x1 and y0 < y < y1):
            continue
        for f in (v['face'] if full else []):
            cone(ax, x, y, f, mpp)
        ax.add_patch(plt.Circle((x, y), r_px * mpp, color=C['ink'], zorder=30))
        ax.add_patch(plt.Circle((x, y), r_px * mpp, fill=False, ec=C['paper'], lw=1.4 * pt, zorder=30.1))
        ax.text(x, y - 0.4 * mpp, str(v['n']), ha='center', va='center', fontsize=r_px * (1.05 if v['n'] < 10 else 0.85) * pt,
                color=C['paper'], fontweight=700, zorder=31)
        lab.reserve(Point(x, y).buffer((r_px + 2) * mpp))
    # the highway's name, in the trench
    hw = D['foot'].intersection(view)
    if not hw.is_empty:
        big = max(getattr(hw, 'geoms', [hw]), key=lambda q: q.area)
        spine = _spine(big)
        if spine is not None and not lab.along(spine, 'I-95 / I-64', px_base * 1.05, C['ink'], bold=True, every=700 if full else None, bend=1.2):
            c = big.representative_point()
            lab.dropped.pop() if lab.dropped and lab.dropped[-1] == 'I-95 / I-64' else None
            lab.near(c.x, c.y, 'I-95 / I-64', px_base, C['ink'], bold=True, reach=(0, REACH), leader=True)
    must = []          # (kind, text) that must be on this rendering
    # bridges: each labeled with its street
    for b in (O['bridges'] if full else []):
        parts = [L for L, k in D['named'].get(b['name'], []) if L.intersects(D['foot'])]
        seg = [L.intersection(view) for L in parts if L.intersection(view).length > 15]
        if not seg:
            continue
        g = max(seg, key=lambda q: q.length)
        g = max(getattr(g, 'geoms', [g]), key=lambda q: q.length)
        c = g.interpolate(0.5, normalized=True)
        text = short(b['name']) + ' bridge'
        must.append(text)
        lab.near(c.x, c.y, text, px_base * 0.95, C['ink'], bold=True, reach=(14, REACH + 20), leader=True)
    # exits
    for e in O['exits']:
        p = e['start']
        if x0 < p[0] < x1 and y0 < p[1] < y1 and full:
            must.append(e['label'])
            lab.near(p[0], p[1], e['label'], px_base * 0.88, C['ink'], italic=False, reach=(10, REACH + 20), leader=True)
    # landmarks
    for mk in O['landmarks']:
        x, y = mk['xy']
        if x0 < x < x1 and y0 < y < y1 and (full or mk['label'] in OVERVIEW_MARKS):
            must.append(mk['label'])
            text = '\n'.join(_wrap2(mk['label']))
            lab.near(x, y, text, px_base * 0.9, C['ink'], bold=True, reach=(0, REACH + 20), leader=True)
    # Gilpin Court
    gb = D['gilpin'].intersection(view)
    if gb.area > 4000:
        c = gb.centroid if gb.contains(gb.centroid) else gb.representative_point()
        must.append('Gilpin Court (RRHA public housing)')
        lab.near(c.x, c.y, 'Gilpin Court\n(RRHA public housing)', px_base * (1.0 if full else 0.9), C['ink'], bold=True, reach=(0, 160), leader=True)
    # today's streets: every one with MIN_IN_VIEW m in view (overview: its list), longest first
    names = []
    for name, parts in D['named'].items():
        u = unary_union([L for L, k in parts])
        geo = u.intersection(view)
        if u.intersection(core).length < MIN_IN_VIEW:
            continue
        if not full and name not in OVERVIEW_STREETS:
            continue
        segs = [g for g in getattr(geo, 'geoms', [geo]) if g.geom_type == 'LineString']
        merged = linemerge(MultiLineString(segs)) if len(segs) > 1 else segs[0]
        segs = [g for g in getattr(merged, 'geoms', [merged]) if g.geom_type == 'LineString']
        names.append((-geo.length, name, segs))
    names.sort()
    for _, name, segs in names:
        must.append(short(name))
        name_street(lab, name, segs, px_base, full)
    # the 1952 stretches: italic, dark red, along them or beside them with a leader
    for name, L, joined in sorted(D['lost'], key=lambda t: -t[1].length):
        if joined or not full:
            continue
        if L.intersection(core).length < min(MIN_IN_VIEW, L.length * 0.6):
            continue
        s = short(name)
        must.append('(1952) ' + s)
        if lab.along(L.intersection(view) if L.intersection(view).geom_type == 'LineString' else L, s, px_base * 0.95, C['lost'], italic=True, step=4):
            continue
        lab.dropped.pop() if lab.dropped and lab.dropped[-1] == s else None
        placed = False
        for f in (0.5, 0.25, 0.75, 0.1, 0.9):
            q = L.interpolate(f, normalized=True)
            for size in (px_base * 0.95, px_base * 0.88):
                if lab.near(q.x, q.y, s, size, C['lost'], italic=True, reach=(8, REACH), leader=True):
                    placed = True
                    break
                lab.dropped.pop()
            if placed:
                break
        if not placed:
            lab.dropped.append('(1952) ' + s)
    lab.must = must
    return lab


OVERVIEW_MARKS = {'Richmond Coliseum'}


def _wrap2(s):
    """A long label on two lines, split near its middle."""
    if len(s) < 20:
        return [s]
    w = s.split()
    best = min(range(1, len(w)), key=lambda k: abs(len(' '.join(w[:k])) - len(' '.join(w[k:]))))
    return [' '.join(w[:best]), ' '.join(w[best:])]


def name_street(lab, name, segs, px_base, full):
    """Along the street at full size, then a little smaller, then beside it with a leader at any of
    several points along it; never under the floor size (CURRENT['min_px'] or 11.5 px)."""
    s = short(name)
    floor = CURRENT.get('min_px') or min(px_base, 11.5)
    sizes = [px_base, max(floor, px_base * 0.92), floor]
    for size in dict.fromkeys(sizes):
        for g in sorted(segs, key=lambda g: -g.length):
            if lab.along(g, s, size, C['ink'], every=600 if full else 900, bend=0.45):
                return True
    if not full:
        for g in sorted(segs, key=lambda g: -g.length):
            q = g.interpolate(0.5, normalized=True)
            if lab.near(q.x, q.y, s, px_base, C['ink'], reach=(6, 30), leader=True):
                return True
            lab.dropped.pop()
        lab.dropped.append(s)
        return False
    for g in sorted(segs, key=lambda g: -g.length):
        if lab.along(g, s, floor, C['ink'], bend=0.9, step=4):
            return True
    for g in sorted(segs, key=lambda g: -g.length):
        for f in (0.5, 0.3, 0.7, 0.15, 0.85, 0.4, 0.6, 0.22, 0.78, 0.08, 0.92, 0.02, 0.98):
            q = g.interpolate(f, normalized=True)
            for size in dict.fromkeys(sizes[1:]):
                if lab.near(q.x, q.y, s, size, C['ink'], reach=(8, REACH if not RENDERS[CURRENT['name']].get('sheet') else 100), leader=True):
                    return True
                lab.dropped.pop()
    lab.dropped.append(s)
    return False


# ---- furniture ------------------------------------------------------------------------------

def scale_strip(ax, x, y, mpp, px):
    """A scale bar drawn in CSS pixels (ax spans the figure in px): 200 m and 500 ft."""
    pt = 72 / 100
    m200, f500 = 200 / mpp, 500 * 0.3048 / mpp
    ax.plot([x, x + m200], [y, y], color=C['ink'], lw=1.6 * pt * 1.4, solid_capstyle='butt')
    for t in (0, 0.5, 1):
        ax.plot([x + m200 * t] * 2, [y, y + 4], color=C['ink'], lw=1.0 * pt * 1.4)
    ax.text(x + m200 + 4, y + 1, '200 m', fontsize=px * 0.85 * pt, va='bottom')
    ax.plot([x, x + f500], [y - 2, y - 2], color=C['ink'], lw=0.8 * pt * 1.4)
    for t in (0, 0.5, 1):
        ax.plot([x + f500 * t] * 2, [y - 2, y - 6], color=C['ink'], lw=1.0 * pt * 1.4)
    ax.text(x + f500 + 4, y - 3, '500 ft', fontsize=px * 0.85 * pt, va='top')


def arrow_strip(ax, x, y, px, left=None):
    """A north arrow, in CSS pixels, its tip at (x, y)."""
    if left:
        x = left
    s = 14
    ax.add_patch(plt.Polygon([(x, y), (x - s * 0.32, y - s * 1.35), (x, y - s * 1.1), (x + s * 0.32, y - s * 1.35)],
                             closed=True, fc=C['ink'], ec=C['ink'], lw=0.5))
    ax.text(x - 10, y - s * 0.7, 'N', ha='right', va='center', fontsize=px * 0.8 * 72 / 100, fontweight=700)


TILE_NOTE = ('Key: under the overview map. © OpenStreetMap contributors (ODbL). 1952 streets: Sanborn map, 1952, '
             'and USGS, 1933–34. Drawn by Chris Busse with isoscape, built with Claude.')
KEY = [
    ('street', 'Streets today, named upright'),
    ('bridge', 'A street on a bridge over the highway'),
    ('end', 'Where a street ends at the trench'),
    ('lost', '1952 streets the trench cut: dashed, named in italic'),
    ('highway', 'I-95 / I-64 today; exits by number'),
    ('gilpin', 'Gilpin Court (RRHA public housing), outline approximate'),
    ('stop', 'A place to stand; the wedge shows which way to look'),
    ('landmark', 'A building or park named on the map'),
    ('grid', 'Grid squares A–F and 1–6, for the street index'),
]
CREDIT = ('© OpenStreetMap contributors (ODbL), as of November 16, 2026. 1952 streets: Sanborn map, Richmond, 1952, vol. 3, '
          'Library of Congress, as traced for the Jackson Ward story; seven joined across the trench as the USGS map of 1933–34 '
          'shows them. Gilpin Court: City of Richmond parcel records, approximate. Drawn by Chris Busse with isoscape, built with Claude.')


def key_rows(ax, x, y, w, px, fx, fy, items=KEY):
    """Draw the key's rows from (x, y) down, in figure fractions; returns the y below them."""
    import textwrap
    pt = 72 / 100
    sw = fx(28)
    chars = int((w - 44) / (px * 0.92 * 0.53))
    for kind, text in items:
        text = '\n'.join(textwrap.wrap(text, chars))
        nl = text.count('\n') + 1
        yy = y - fy(px * 1.25 * nl + px * 0.4) / 2
        xs = [x + fx(2), x + fx(2) + sw]
        if kind == 'street':
            ax.plot(xs, [yy, yy], color=C['street'], lw=2.2 * pt * 1.4, solid_capstyle='butt')
        elif kind == 'bridge':
            ax.plot(xs, [yy, yy], color=C['ink'], lw=5.2 * pt, solid_capstyle='butt')
            ax.plot(xs, [yy, yy], color=C['paper'], lw=3.6 * pt, solid_capstyle='butt')
            ax.plot(xs, [yy, yy], color=C['street'], lw=2.8 * pt, solid_capstyle='butt')
        elif kind == 'end':
            ax.plot(xs, [yy, yy], color=C['street'], lw=2.2 * pt * 1.4, solid_capstyle='butt')
            ax.plot([xs[1], xs[1]], [yy - fy(6), yy + fy(6)], color=C['ink'], lw=2.2 * pt, solid_capstyle='butt')
        elif kind == 'lost':
            ax.plot(xs, [yy, yy], color=C['lost'], lw=2.2 * pt, ls=(0, (2.2, 1.2)), dash_capstyle='butt')
        elif kind in ('highway', 'gilpin', 'landmark'):
            fc = {'highway': C['highway'], 'gilpin': C['gilpin_fill'], 'landmark': C['landmark']}[kind]
            ec = {'highway': C['highway_edge'], 'gilpin': C['ink'], 'landmark': C['ink']}[kind]
            ax.add_patch(plt.Rectangle((xs[0], yy - fy(px * 0.45)), sw if kind != 'landmark' else fx(12), fy(px * 0.9), fc=fc, ec=ec,
                                       lw=(1.4 if kind == 'gilpin' else 0.6) * pt))
        elif kind == 'stop':
            ax.add_patch(matplotlib.patches.Wedge((xs[0] + fx(8), yy), fx(22), 15, 65, fc=C['cone'], ec=C['ink'], lw=0.6, alpha=0.45))
            ax.add_patch(matplotlib.patches.Ellipse((xs[0] + fx(8), yy), fx(15), fy(15), color=C['ink']))
            ax.text(xs[0] + fx(8), yy, '1', ha='center', va='center', color=C['paper'], fontsize=px * 0.85 * pt, fontweight=700)
        elif kind == 'grid':
            ax.text(xs[0] + fx(10), yy, 'C4', ha='center', va='center', fontsize=px * 0.9 * pt, fontweight=700,
                    bbox=dict(boxstyle='square,pad=0.18', fc=C['paper'], ec=C['ink'], lw=0.5))
        ax.text(xs[1] + fx(8), yy, text, va='center', fontsize=px * 0.92 * pt, style='italic' if kind == 'lost' else 'normal',
                color=C['lost'] if kind == 'lost' else C['ink'], linespacing=1.15)
        y -= fy(px * 1.25 * nl + px * 0.4)
    return y


def locator(fig, rect, which):
    """A small plan of the whole frame with the grid, this tile shaded."""
    ax = fig.add_axes(rect)
    x0, x1, y0, y1 = PLAN
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_linewidth(0.6)
    ax.set_facecolor(C['paper'])
    for i in range(6):
        b = tile_bounds(i)
        ax.add_patch(plt.Rectangle((max(b[0], x0), max(b[2], y0)), min(b[1], x1) - max(b[0], x0), min(b[3], y1) - max(b[2], y0),
                                   fc=C['highway'] if i == which else 'none', ec=C['ink'], lw=0.4))
        cx, cy = (max(b[0], x0) + min(b[1], x1)) / 2, (max(b[2], y0) + min(b[3], y1)) / 2
        ax.text(cx, cy, str(i + 1), ha='center', va='center', fontsize=7, fontweight=700 if i == which else 'normal')


def render(name, out_full, rnd):
    R = RENDERS[name]
    bounds, W, px, mode = R['bounds'], R['W'], R['px'], R['mode']
    CURRENT['name'] = name
    CURRENT['min_px'] = px if R.get('sheet') else None
    x0, x1, y0, y1 = bounds
    mpp = (x1 - x0) / (W - 2)
    map_h = (y1 - y0) / mpp
    D = gather(bounds)
    O = load('orient.json')
    V = load('vantage.json')['points']
    pt = 72 / 100
    import textwrap
    if R.get('sheet'):
        head, keyh = 0, 0
        H = map_h + 2
    elif mode == 'overview':
        head = px * 3.4
        nkey = sum(len(textwrap.wrap(t, int((W - 56) / (px * 0.92 * 0.53)))) for _, t in KEY)
        keyh = px * 1.25 * nkey + px * 0.4 * len(KEY) + px * 0.8 * 1.3 * 6 + 24 + KEY_GAP + 18
        H = head + map_h + keyh
    else:
        head = px * 3.4
        keyh = px * 0.8 * 1.3 * len(textwrap.wrap(TILE_NOTE, int((W - 16) / (px * 0.8 * 0.52)))) + 14 + KEY_GAP + 18
        H = head + map_h + keyh
    fig = plt.figure(figsize=(W / 100, H / 100))
    fig.patch.set_facecolor(C['paper'])
    ax = fig.add_axes([1 / W, keyh / H, (W - 2) / W, map_h / H])
    lab = draw_map(ax, D, O, V, bounds, mpp, mode, px)
    # the scale bar and the north arrow sit outside the map, in the bands above and below it
    sb = fig.add_axes([0, 0, 1, 1], facecolor='none')
    sb.set_xlim(0, W)
    sb.set_ylim(0, H)
    sb.axis('off')
    yb = keyh - 14 if not R.get('sheet') else None
    if yb is not None:
        scale_strip(sb, 8, yb, mpp, px)
        arrow_strip(sb, W - (88 if 'tile' in R else 16), H - 6, px)
    if not R.get('sheet'):
        fig.text(8 / W, (H - 6) / H, R['title'], fontsize=px * 1.3 * pt, fontweight=700, va='top', ha='left')
        sub = ('North is up. Main streets only: maps 1 to 6 name every street.' if mode == 'overview'
               else 'North is up. The grid squares match the street index.')
        fig.text(8 / W, (H - 6 - px * 1.7) / H, sub, fontsize=px * 0.88 * pt, va='top', ha='left', color=C['muted'])
        if 'tile' in R:
            lw_ = 64
            locator(fig, [(W - lw_ - 6) / W, (H - head + 4) / H, lw_ / W, (head - 8) / H], R['tile'])
    W_css = W
    fx = lambda v: v / W_css  # noqa: E731
    fy = lambda v: v / H  # noqa: E731
    kax = fig.add_axes([0, 0, 1, 1], facecolor='none')
    kax.set_xlim(0, 1)
    kax.set_ylim(0, 1)
    kax.axis('off')
    if mode == 'overview':
        y = key_rows(kax, fx(8), (keyh - KEY_GAP - 18) / H, W - 16, px, fx, fy)
        kax.text(fx(8), y - fy(6), '\n'.join(textwrap.wrap(CREDIT, int((W - 16) / (px * 0.8 * 0.52)))), va='top',
                 fontsize=px * 0.8 * pt, color=C['muted'], linespacing=1.3)
    elif not R.get('sheet'):
        kax.text(fx(8), (keyh - KEY_GAP - 18) / H, '\n'.join(textwrap.wrap(TILE_NOTE, int((W - 16) / (px * 0.8 * 0.52)))),
                 va='top', fontsize=px * 0.8 * pt, color=C['muted'], linespacing=1.3)
    base = f'jackson-ward-guide-map-{name}'
    od = os.path.join(ROOT, 'out/stories/jackson-ward-guide')
    os.makedirs(od, exist_ok=True)
    png = os.path.join(od, base + '.png')
    fig.savefig(png, dpi=300)
    if R.get('sheet'):
        with matplotlib.rc_context({'svg.fonttype': 'none'}):
            fig.savefig(os.path.join(od, base + '.svg'))
    plt.close(fig)
    from PIL import Image
    im = Image.open(png).convert('RGB')
    if not R.get('sheet'):
        im.save(os.path.join(ROOT, 'pages', base + '.webp'), quality=88, method=6)
    if out_full:
        os.makedirs(out_full, exist_ok=True)
        im.save(os.path.join(out_full, base + f'-r{rnd}.png'), optimize=True)
        im.resize((W, round(im.height * W / im.width)), Image.LANCZOS).save(os.path.join(out_full, base + f'-r{rnd}-{W}.png'))
    dropped = sorted(set(lab.dropped))
    print(name, im.size, f'{len(lab.must)} names asked,', 'left off:', dropped)
    return dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None, help='overview,tile-1,...,tile-6,sheet')
    ap.add_argument('--full', default=None)
    ap.add_argument('--round', default='1')
    ap.add_argument('--allow-drops', action='store_true')
    a = ap.parse_args()
    bad = {}
    for n in (a.only.split(',') if a.only else RENDERS):
        d = render(n, a.full, a.round)
        if d and RENDERS[n]['mode'] == 'full':
            bad[n] = d
    if bad and not a.allow_drops:
        sys.exit(f'map: names left off: {bad}')


if __name__ == '__main__':
    main()
