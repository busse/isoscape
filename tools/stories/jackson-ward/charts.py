#!/usr/bin/env python3
"""The Jackson Ward story's method charts, drawn from the same data as the maps.

    node tools/stories/jackson-ward/data.ts --residuals tools/stories/jackson-ward/residuals.csv
    python3 tools/stories/jackson-ward/charts.py [--only name,name] [--out pages/]

Writes pages/jackson-ward-<name>.webp (embedded in the story page) and, with --full DIR, a
full-size PNG of each for review. Every color is read from src/palette.ts (the paper palette)
through node, never typed here; where a chart needs a tone the palette does not hold, it is mixed
from two palette colors and the mix is named in `roles`. Drawn in the explorer's flat diagram
style: flat fills, inked edges, a dot on every corner of a plan's outlines, text in ink, one
accent per chart, no gridlines heavier than the paper.

Inputs (all in the repo or its caches; see the story page's "How we know"):
  out/stories/jackson-ward/data.json   tools/stories/jackson-ward/data.ts: ground grids, outlines
  tools/sanborn/jw/counts.json         the count (the one place its numbers live)
  tools/stories/jackson-ward/residuals.csv   the 1952 sheets' fit residuals (from the trace)
  --topo  the USGS Richmond 1:24,000 sheet surveyed 1933-34 (GeoTIFF, public domain)
  --sheet the trace's overlay of one 1952 Sanborn sheet (overlays/sheet-326-1952.jpg)
  --renders a folder holding the three renders for the three-way view
"""

import argparse
import csv
import json
import math
import os
import subprocess
import sys

import numpy as np
import matplotlib
import matplotlib.ticker

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_rgb  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


# ---- palette ---------------------------------------------------------------------------------

def load_palette():
    js = "import('./src/palette.ts').then(m => console.log(JSON.stringify(m.PALETTES.paper)))"
    out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


P = load_palette()


def mix(a, b, t):
    """A tone between two palette colors: t = 0 is a, 1 is b."""
    ra, rb = np.array(to_rgb(a)), np.array(to_rgb(b))
    return tuple(ra * (1 - t) + rb * t)


# The roles every chart colors by. Each is a palette color, or a named mix of two.
R = {
    'paper': P['sky'],
    'land': P['land'],
    'ink': P['ink'],
    'muted': mix(P['ink'], P['sky'], 0.45),
    'faint': mix(P['ink'], P['sky'], 0.82),
    'today': P['ink'],                      # today's measured ground
    'rebuilt': P['mark']['pick'],           # the rebuilt pre-1955 ground (the estimate)
    'band': P['mark']['near'],              # its stated error
    'cut': P['mark']['pick'],               # ground taken away
    'fill': mix(P['waterLine'], P['ink'], 0.35),  # ground added (a bank), and the 1934 evidence
    'set_aside': P['parking'],              # where the lidar is set aside
    'street': mix(P['ink'], P['sky'], 0.7),
    'line': P['mark']['line'],              # the lost streets, held at grade
    'pick': P['mark']['pick'],
    'near': P['mark']['near'],
    'quiet': P['mark']['quiet'],
    'shade_dark': P['shadeDark'],
    'shade_light': P['shadeLight'],
}

FONT = 'Inter'
if not any('Inter' in f.name for f in font_manager.fontManager.ttflist):
    FONT = 'DejaVu Sans'
plt.rcParams.update({
    'font.family': FONT,
    'font.size': 10.5,
    'text.color': R['ink'],
    'axes.labelcolor': R['muted'],
    'axes.edgecolor': R['muted'],
    'axes.facecolor': R['paper'],
    'figure.facecolor': R['paper'],
    'savefig.facecolor': R['paper'],
    'xtick.color': R['muted'],
    'ytick.color': R['muted'],
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.8,
    'axes.titlesize': 11.5,
    'axes.titleweight': 600,
    'axes.titlelocation': 'left',
    'legend.frameon': False,
    'legend.fontsize': 9.5,
})
LW = P['lineWidth'] * 2 / 0.75 * 0.75 * 1.6   # the maps' line, as the FAQ's diagrams double it
DOT = P['dotRadius'] * 2

CREDIT = 'Drafted with Claude for Chris Busse; working draft, not for publication.'


# ---- data ------------------------------------------------------------------------------------

class Data:
    def __init__(self, path):
        d = json.load(open(path))
        self.d = d
        g = d['grid']
        self.nx, self.ny, self.x0, self.y0, self.cell = g['nx'], g['ny'], g['x0'], g['y0'], g['cell']
        shape = (self.ny, self.nx)
        self.today = np.array(d['today'], dtype=float).reshape(shape)
        self.rebuilt = np.array(d['rebuilt'], dtype=float).reshape(shape)
        self.membrane = np.array(d['membrane'], dtype=float).reshape(shape)
        self.xs = self.x0 + np.arange(self.nx) * self.cell
        self.ys = self.y0 + np.arange(self.ny) * self.cell
        self.extent = (self.x0 - self.cell / 2, self.xs[-1] + self.cell / 2, self.y0 - self.cell / 2, self.ys[-1] + self.cell / 2)
        self.bearing = d['bearing']
        self.trench = [g for g in d['ground'] if g['id'] == 'turnpike-trench'][0]
        self.junction = [g for g in d['ground'] if g['id'] == 'junction-ramps'][0]

    def mask(self, rings):
        """Grid nodes inside rings (even-odd)."""
        X, Y = np.meshgrid(self.xs, self.ys)
        pts = np.column_stack([X.ravel(), Y.ravel()])
        inside = np.zeros(len(pts), dtype=bool)
        for r in rings:
            inside ^= Path(np.array(r)).contains_points(pts)
        return inside.reshape(X.shape)

    def sample(self, grid, pts):
        """Bilinear sample of a grid at view-meter points."""
        pts = np.asarray(pts, dtype=float)
        fx = np.clip((pts[:, 0] - self.x0) / self.cell, 0, self.nx - 1.001)
        fy = np.clip((pts[:, 1] - self.y0) / self.cell, 0, self.ny - 1.001)
        i, j = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - i, fy - j
        return (grid[j, i] * (1 - tx) * (1 - ty) + grid[j, i + 1] * tx * (1 - ty)
                + grid[j + 1, i] * (1 - tx) * ty + grid[j + 1, i + 1] * tx * ty)

    def north(self):
        """The direction of true north in view meters (E', N')."""
        b = math.radians(self.bearing)
        return (-math.sin(b), math.cos(b))


def hillshade(z, cell, az=315.0, alt=35.0, exaggerate=4.0):
    """Lit from the northwest (in view terms), 0 dark to 1 lit; rows run south to north."""
    from matplotlib.colors import LightSource
    ls = LightSource(azdeg=az, altdeg=alt)
    return ls.hillshade(z[::-1], vert_exag=exaggerate, dx=cell, dy=cell)[::-1]


def shade_rgb(z, cell):
    """A hillshade in the maps' own wash: land, darkened toward shadeDark and lit toward shadeLight."""
    s = hillshade(z, cell)
    flat = float(np.median(s))
    land = np.array(to_rgb(R['land']))
    dark = np.array(to_rgb(R['shade_dark']))
    light = np.array(to_rgb(R['shade_light']))
    t = (s - flat)[..., None]
    out = np.where(t < 0, land + (dark - land) * np.clip(-t * 4.0, 0, 0.85), land + (light - land) * np.clip(t * 3.5, 0, 1))
    return np.clip(out, 0, 1)


# ---- drawing helpers -------------------------------------------------------------------------

def plan_axes(ax, data, bounds):
    ax.set_aspect('equal')
    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(bounds[2], bounds[3])
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(R['ink'])
        s.set_linewidth(0.9)


def draw_streets(ax, data, kinds=('residential', 'tertiary', 'primary', 'secondary', 'primary_link', 'unclassified', 'living_street'), lw=0.55, color=None):
    for s in data.d['streets']:
        if s['kind'] in kinds:
            p = np.array(s['pts'])
            ax.plot(p[:, 0], p[:, 1], color=color or R['street'], lw=lw, solid_capstyle='round', zorder=2)


def draw_highway(ax, data, color=None, lw=0.8):
    for s in data.d['streets']:
        if s['kind'] in ('motorway', 'motorway_link'):
            p = np.array(s['pts'])
            ax.plot(p[:, 0], p[:, 1], color=color or R['muted'], lw=lw, zorder=2)


def outline(ax, ring, color=None, lw=None, dots=True, ls='-', z=5, fill=None, alpha=1.0):
    r = np.array(ring + [ring[0]])
    if fill is not None:
        ax.fill(r[:, 0], r[:, 1], color=fill, alpha=alpha, lw=0, zorder=z - 1)
    ax.plot(r[:, 0], r[:, 1], color=color or R['ink'], lw=lw or LW, ls=ls, zorder=z, solid_joinstyle='round')
    if dots:
        ax.scatter(r[:-1, 0], r[:-1, 1], s=DOT ** 2 * 0.9, color=color or R['ink'], zorder=z + 0.1, lw=0)


def scale_bar(ax, x, y, length=200, label=None):
    ax.plot([x, x + length], [y, y], color=R['ink'], lw=1.6, solid_capstyle='butt', zorder=9)
    for t in (x, x + length):
        ax.plot([t, t], [y - 8, y + 8], color=R['ink'], lw=1.2, zorder=9)
    ax.text(x + length / 2, y + 14, label or f'{length} m', ha='center', va='bottom', fontsize=9, zorder=9)


def north_arrow(ax, data, x, y, size=60):
    nx_, ny_ = data.north()
    ax.annotate('', xy=(x + nx_ * size, y + ny_ * size), xytext=(x, y),
                arrowprops=dict(arrowstyle='-|>', color=R['ink'], lw=1.2, mutation_scale=12), zorder=9)
    ax.text(x + nx_ * (size + 14), y + ny_ * (size + 14), 'N', ha='center', va='bottom', fontsize=9.5, fontweight=600, zorder=9)


def label(ax, x, y, s, size=9, ha='center', color=None, weight=None, z=8):
    ax.text(x, y, s, ha=ha, va='center', fontsize=size, color=color or R['ink'], fontweight=weight, zorder=z,
            bbox=dict(boxstyle='round,pad=0.18', fc=R['paper'], ec='none', alpha=0.85))


def footer(fig, text):
    fig.text(0.012, 0.012, text + ' ' + CREDIT, fontsize=8, color=R['muted'], ha='left', va='bottom', wrap=True)


def street_point(data, name, near=None):
    """Points of a named street (OSM), optionally only those within 400 m of a point."""
    pts = []
    for s in data.d['streets']:
        if s['name'] == name and s['kind'] not in ('footway', 'cycleway', 'service', 'steps'):
            for p in s['pts']:
                if near is None or math.hypot(p[0] - near[0], p[1] - near[1]) < 400:
                    pts.append(p)
    return np.array(pts)


def centerline(data):
    return np.array([c['p'] for c in data.d['checks']])


def cross_section(data, name, half=250):
    """A straight section along a named street, centered where it crosses the trench's center line."""
    cl = centerline(data)
    pts = street_point(data, name, near=None)
    # keep the street's points near the trench
    d = np.array([np.min(np.hypot(cl[:, 0] - p[0], cl[:, 1] - p[1])) for p in pts])
    pts = pts[d < 350]
    c = pts.mean(axis=0)
    u, s_, vt = np.linalg.svd(pts - c)
    v = vt[0]
    if v[1] < 0:   # run from southwest (near, small N') to northeast
        v = -v
    # where the street's line meets the center line
    best = None
    for a, b in zip(cl[:-1], cl[1:]):
        m = np.array([[v[0], a[0] - b[0]], [v[1], a[1] - b[1]]])
        if abs(np.linalg.det(m)) < 1e-9:
            continue
        t, w = np.linalg.solve(m, a - c)
        if 0 <= w <= 1:
            best = c + t * v
    o = best if best is not None else c
    s = np.arange(-half, half + 0.1, 2.0)
    line = o[None, :] + s[:, None] * v[None, :]
    return s, line, o, v


# ---- 1. where the trench was filled, and how deep ------------------------------------------

def diverging():
    return LinearSegmentedColormap.from_list('cutfill', [R['fill'], mix(R['fill'], R['land'], 0.6), R['land'], mix(R['cut'], R['land'], 0.6), R['cut']])


def chart_cut_fill(data, out):
    diff = data.rebuilt - data.today          # positive: ground taken away (a cut), now put back
    trench = data.mask(data.trench['rings'])
    junction = data.mask(data.junction['rings'])
    inside = trench | junction
    fig = plt.figure(figsize=(11.2, 8.6))
    ax = fig.add_axes([0.03, 0.19, 0.94, 0.74])
    bounds = (-950, 950, -600, 600)
    plan_axes(ax, data, bounds)
    ax.imshow(shade_rgb(data.today, data.cell), origin='lower', extent=data.extent, zorder=0, interpolation='bilinear')
    vmax = 9
    shown = np.where(inside & (np.abs(diff) > 0.05), diff, np.nan)
    im = ax.imshow(shown, origin='lower', extent=data.extent, cmap=diverging(), vmin=-vmax, vmax=vmax, zorder=1, interpolation='bilinear')
    draw_streets(ax, data, lw=0.5)
    for r in data.trench['rings']:
        outline(ax, r, color=R['ink'], lw=1.1, dots=False, z=6)
    for r in data.junction['rings']:
        outline(ax, r, color=R['ink'], lw=1.0, dots=False, ls=(0, (4, 2.5)), z=6)
    for ln in data.trench['lines']:
        p = np.array(ln['pts'])
        ax.plot(p[:, 0], p[:, 1], color=R['line'], lw=3.0, solid_capstyle='round', zorder=7)
        ax.scatter(p[:, 0], p[:, 1], s=DOT ** 2 * 1.6, color=R['ink'], zorder=7.1, lw=0)
    # street names, at each held line's northern end
    names = {'Chamberlayne Parkway': 'Chamberlayne Pkwy', 'Saint James Street': 'St. James', 'North 1st Street': '1st',
             'North 2nd Street': '2nd', 'East Duval Street': 'Duval', 'North 5th Street': '5th', 'North 7th Street': '7th'}
    for ln in data.trench['lines']:
        p = np.array(ln['pts'])
        top = p[np.argmax(p[:, 1])]
        lo_ = p[np.argmin(p[:, 1])]
        at, dy = (top, 26) if ln['name'] in ('Saint James Street', 'North 1st Street', 'North 2nd Street', 'Chamberlayne Parkway') else (lo_, -26)
        label(ax, at[0], at[1] + dy, names.get(ln['name'], ln['name']), size=8.5, weight=600)
    k = np.nanargmax(np.where(trench, diff, np.nan))
    j, i = divmod(k, data.nx)
    ax.annotate(f'deepest cut: {diff[j, i]:.1f} m\nof ground put back', xy=(data.xs[i], data.ys[j]), xytext=(data.xs[i] - 260, data.ys[j] + 170),
                fontsize=9, ha='center', arrowprops=dict(arrowstyle='-', color=R['ink'], lw=0.8), zorder=9,
                bbox=dict(boxstyle='round,pad=0.25', fc=R['paper'], ec='none', alpha=0.9))
    kk = np.nanargmin(np.where(inside, diff, np.nan))
    j2, i2 = divmod(kk, data.nx)
    ax.annotate(f'highest bank\ntaken down: {-diff[j2, i2]:.1f} m', xy=(data.xs[i2], data.ys[j2]), xytext=(data.xs[i2] - 60, data.ys[j2] + 260),
                fontsize=9, ha='center', arrowprops=dict(arrowstyle='-', color=R['ink'], lw=0.8), zorder=9,
                bbox=dict(boxstyle='round,pad=0.25', fc=R['paper'], ec='none', alpha=0.9))
    label(ax, 860, -330, 'Shockoe\nValley', size=9, color=R['muted'])
    scale_bar(ax, -900, -560, 200)
    north_arrow(ax, data, -880, -470, 50)
    ax.set_title('Where the trench was filled, and by how much', pad=8, fontsize=13)
    # the key, in a strip below the plan
    cax = fig.add_axes([0.03, 0.115, 0.30, 0.022])
    cb = fig.colorbar(im, cax=cax, orientation='horizontal')
    cb.outline.set_visible(False)
    cb.set_ticks([-8, -4, 0, 4, 8])
    cb.set_ticklabels(['8 m', '4 m', '0', '4 m', '8 m'])
    cax.tick_params(labelsize=8.5, length=0)
    fig.text(0.03, 0.145, 'bank taken down', fontsize=8.8, ha='left')
    fig.text(0.33, 0.145, 'cut filled', fontsize=8.8, ha='right')
    keys = [('trench', 0.37, 'trench: rebuilt from its rim and the\nstreets that crossed (a membrane)'),
            ('junction', 0.60, 'junction: banks under 50 m wide\ntaken down, the rest as measured'),
            ('line', 0.825, 'street held at grade,\nstraight between its ends')]
    for kind, x, txt in keys:
        y = 0.128
        st = dict(color=R['ink'], lw=1.1) if kind == 'trench' else dict(color=R['ink'], lw=1.0, ls=(0, (4, 2.5))) if kind == 'junction' else dict(color=R['line'], lw=3)
        fig.lines.append(plt.Line2D([x, x + 0.03], [y, y], transform=fig.transFigure, **st))
        fig.text(x + 0.037, y, txt, fontsize=8.8, va='center')
    footer(fig, 'Plan of the ward, north about 10° right of up. Lidar: USGS 3DEP (public domain), 5 m grid. Streets: OpenStreetMap contributors (ODbL). '
                'The fill is an estimate: about ±1.5 m mid-trench, ±3 m at its ends.')
    save(fig, out, 'cut-fill')


# ---- 2. the street profiles ------------------------------------------------------------------

def ft_to_navd(ft):
    """A 1934 contour (feet above mean sea level, NGVD 29) in NAVD 88 meters (Henrico 2021: NAVD 88 = NGVD 29 − 1.04 ft)."""
    return (ft - 1.04) * 0.3048


CHECKS = {   # ground.md, check 2: what the 1934 sheet says within about 60 m of each point
    'P1': ('unread', None), 'P2': ('unread', None), 'P3': ('unread', None),
    'P4': ('agrees', 0.05), 'P5': ('agrees', 0.8), 'P6': ('agrees', 0), 'P7': ('agrees', 0),
    'P8': ('agrees', 0.8), 'P9': ('agrees', 0), 'P10': ('agrees', 0), 'P11': ('disagrees', 3.5), 'P12': ('unread', None),
}


def chart_profiles(data, out):
    streets = [('Saint Peter Street', 'St. Peter Street'), ('North 1st Street', 'North 1st Street'), ('North 5th Street', 'North 5th Street')]
    rings_all = data.trench['rings'] + data.junction['rings']
    fig = plt.figure(figsize=(10.5, 13.2))
    gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 1.25], hspace=0.45, left=0.08, right=0.95, top=0.915, bottom=0.115)
    fig.suptitle('The ground along the streets the trench cut: today, and rebuilt for 1952', x=0.08, ha='left', fontsize=13.5, fontweight=600)
    for k, (osm, title) in enumerate(streets):
        ax = fig.add_subplot(gs[k])
        s, line, o, v = cross_section(data, osm)
        today = data.sample(data.today, line)
        rebuilt = data.sample(data.rebuilt, line)
        memb = data.sample(data.membrane, line)
        inside = np.zeros(len(line), dtype=bool)
        for r in rings_all:
            inside ^= Path(np.array(r)).contains_points(line)
        lo, hi = s[inside].min(), s[inside].max()
        ax.axvspan(lo, hi, color=R['set_aside'], zorder=0, lw=0)
        ax.text((lo + hi) / 2, 0.97, 'lidar set aside', transform=ax.get_xaxis_transform(), ha='center', va='top', fontsize=8.5, color=R['muted'])
        sel = inside
        ax.fill_between(s, np.where(sel, rebuilt - 1.5, np.nan), np.where(sel, rebuilt + 1.5, np.nan), color=R['band'], alpha=0.45, lw=0, zorder=1)
        ax.fill_between(s, np.where(sel, today, np.nan), np.where(sel, rebuilt, np.nan), where=sel & (rebuilt > today), color=R['cut'], alpha=0.10, lw=0, zorder=1)
        ax.plot(s, today, color=R['today'], lw=2, zorder=3, solid_capstyle='round')
        if np.max(np.abs(memb - rebuilt)[sel]) > 0.15:
            ax.plot(s[sel], memb[sel], color=R['rebuilt'], lw=1.2, ls=(0, (3, 2)), zorder=3)
        ax.plot(s[sel], rebuilt[sel], color=R['rebuilt'], lw=2.4, zorder=4, solid_capstyle='round')
        depth = rebuilt - today
        m = np.argmax(np.where(sel, depth, -1))
        ax.annotate(f'cut {depth[m]:.1f} m', xy=(s[m], (today[m] + rebuilt[m]) / 2), xytext=(s[m] + 70, today[m] + 0.3), fontsize=9.5, color=R['ink'],
                    arrowprops=dict(arrowstyle='-', color=R['muted'], lw=0.7), zorder=6)
        ax.annotate('', xy=(s[m], today[m]), xytext=(s[m], rebuilt[m]), arrowprops=dict(arrowstyle='<->', color=R['ink'], lw=0.9, shrinkA=0, shrinkB=0), zorder=6)
        ax.set_title(title, fontsize=12)
        ax.set_xlim(-250, 250)
        ylo = math.floor(min(today.min(), (rebuilt - 1.5)[sel].min()) - 1)
        yhi = math.ceil(max(today.max(), (rebuilt + 1.5)[sel].max()) + 1.5)
        ax.set_ylim(ylo, yhi)
        ax.set_ylabel('meters above sea level')
        ax.grid(axis='y', color=R['faint'], lw=0.6)
        ax.set_axisbelow(True)
        if k == 0:
            ax.text(-245, today[0] + 0.6, 'today (lidar)', fontsize=9.5, color=R['today'], fontweight=600)
            i_r = np.where(sel)[0][len(np.where(sel)[0]) // 3]
            ax.text(s[i_r] - 6, rebuilt[i_r] + 1.9, 'rebuilt (estimate) ±1.5 m', fontsize=9.5, color=R['rebuilt'], fontweight=600, ha='right')
        ax.set_xlabel('meters along the street, southwest (−) to northeast (+); 0 at the highway\'s center line', fontsize=9)
    # the long profile, with the 1934 sheet's evidence
    ax = fig.add_subplot(gs[3])
    cl = centerline(data)
    cl = cl[1:]                 # P1 lies outside the drawn frame
    ids = [c['id'] for c in data.d['checks']][1:]
    seg = np.hypot(np.diff(cl[:, 0]), np.diff(cl[:, 1]))
    cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.arange(0, cum[-1] + 0.1, 3.0)
    pts = np.column_stack([np.interp(s, cum, cl[:, 0]), np.interp(s, cum, cl[:, 1])])
    today = data.sample(data.today, pts)
    rebuilt = data.sample(data.rebuilt, pts)
    ylo, yhi = math.floor(today.min() - 2), math.ceil(rebuilt.max() + 3)
    for ft in range(100, 200, 10):
        z = ft_to_navd(ft)
        if not ylo < z < yhi:
            continue
        ax.axhline(z, color=R['fill'], lw=0.6, alpha=0.55, zorder=0)
        ax.text(cum[-1] + 48, z + 0.25, f'{ft} ft', fontsize=8, color=R['fill'], va='center')
    ax.fill_between(s, rebuilt - 1.5, rebuilt + 1.5, color=R['band'], alpha=0.45, lw=0, zorder=1)
    ax.plot(s, today, color=R['today'], lw=2, zorder=3)
    ax.plot(s, rebuilt, color=R['rebuilt'], lw=2.4, zorder=4)
    for c, cid in zip(cum, ids):
        zr = float(data.sample(data.rebuilt, np.array([[np.interp(c, cum, cl[:, 0]), np.interp(c, cum, cl[:, 1])]]))[0])
        kind, move = CHECKS[cid]
        if kind == 'agrees':
            ax.scatter([c], [zr], s=70, facecolor=R['paper'], edgecolor=R['fill'], lw=2, zorder=6)
            if move and move >= 0.5:
                ax.text(c, zr + 1.0, f'{move:g} m', fontsize=8, ha='center', color=R['fill'])
        elif kind == 'disagrees':
            ax.scatter([c], [zr], s=70, color=R['fill'], zorder=6)
            ax.annotate('1934: a ravine head here,\nat least 3.5 m different', xy=(c, zr), xytext=(c - 260, zr - 6.5), fontsize=9,
                        arrowprops=dict(arrowstyle='-', color=R['ink'], lw=0.7), zorder=7)
        else:
            ax.scatter([c], [zr], s=70, facecolor=R['paper'], edgecolor=R['fill'], lw=1.5, linestyle=(0, (2, 1.5)), zorder=6)
    ax.set_ylim(ylo, yhi)
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2))
    for c, cid in zip(cum, ids):
        ax.text(c, ylo + 0.4, cid, fontsize=8.5, ha='center', va='bottom', color=R['muted'])
    ax.set_xlim(-30, cum[-1] + 110)
    ax.set_title('Along the trench\'s center line, northwest to southeast, with the 1934 survey\'s check points', fontsize=12)
    ax.set_ylabel('meters above sea level')
    ax.set_xlabel('meters along the center line from P2 (Brook Road) to P12 (the valley wall past 7th Street)', fontsize=9)
    ax.spines['bottom'].set_visible(True)
    # legend
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=R['today'], lw=2, label='today (USGS lidar)'),
         Line2D([], [], color=R['rebuilt'], lw=2.4, label='rebuilt for 1952 (estimate)'),
         plt.Rectangle((0, 0), 1, 1, color=R['band'], alpha=0.45, label='stated error, ±1.5 m'),
         Line2D([], [], color=R['rebuilt'], lw=1.2, ls=(0, (3, 2)), label='membrane alone, no streets held'),
         Line2D([], [], color=R['fill'], lw=0.6, label='10-ft levels of the 1934 survey'),
         Line2D([], [], marker='o', ls='', mfc=R['paper'], mec=R['fill'], mew=2, ms=8, label='1934 sheet agrees (number: least move to agree)'),
         Line2D([], [], marker='o', ls='', color=R['fill'], ms=8, label='1934 sheet disagrees'),
         Line2D([], [], marker='o', ls='', mfc=R['paper'], mec=R['fill'], mew=1.2, ms=8, label='level not readable on the sheet')]
    fig.legend(handles=h, loc='lower center', ncol=3, bbox_to_anchor=(0.52, 0.004), fontsize=9, handlelength=2.2, columnspacing=1.5)
    fig.text(0.08, 0.946, 'Elevations in meters above sea level (NAVD 88). Lidar: USGS 3DEP. 1934: USGS Richmond 1:24,000, surveyed 1933–34, contours every 10 ft\n(converted). No 1934 contour can be read where the three streets cross the trench; the check points are on the center line (bottom). ' + CREDIT,
             fontsize=8, color=R['muted'], ha='left')
    save(fig, out, 'profiles')


# ---- 4. the hillshade pair -------------------------------------------------------------------

def chart_hillshade(data, out):
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.4))
    bounds = (-760, 820, -560, 520)
    for ax, grid, t in [(axs[0], data.today, 'Today (lidar)'), (axs[1], data.rebuilt, 'Rebuilt for 1952 (estimate)')]:
        plan_axes(ax, data, bounds)
        ax.imshow(shade_rgb(grid, data.cell), origin='lower', extent=data.extent, zorder=0, interpolation='bilinear')
        for r in data.trench['rings']:
            outline(ax, r, color=R['ink'], lw=0.9, dots=False, z=6)
        for r in data.junction['rings']:
            outline(ax, r, color=R['ink'], lw=0.8, dots=False, ls=(0, (4, 2.5)), z=6)
        ax.set_title(t, fontsize=12)
    scale_bar(axs[0], -720, -520, 200)
    north_arrow(axs[0], data, -700, -440, 50)
    fig.suptitle('The ground alone, lit from the northwest, before and after the trench is filled', x=0.012, ha='left', fontsize=13, fontweight=600)
    fig.subplots_adjust(left=0.012, right=0.988, top=0.86, bottom=0.08, wspace=0.03)
    footer(fig, 'Relief exaggerated 4× in the shading. Solid outline: the trench, rebuilt; dashed: the junction, ramp banks taken down. Lidar: USGS 3DEP.')
    save(fig, out, 'hillshade')


def save(fig, out, name):
    os.makedirs(out['pages'], exist_ok=True)
    png = os.path.join(out['tmp'], f'jackson-ward-{name}.png')
    fig.savefig(png, dpi=out['dpi'])
    plt.close(fig)
    im = Image.open(png).convert('RGB')
    if out.get('full'):
        os.makedirs(out['full'], exist_ok=True)
        im.save(os.path.join(out['full'], f'jackson-ward-{name}.png'), optimize=True)
    w = 1600
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(os.path.join(out['pages'], f'jackson-ward-{name}.webp'), quality=86, method=6)
    print('wrote', name, im.size)


CHARTS = {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=os.path.join(ROOT, 'out/stories/jackson-ward/data.json'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'pages'))
    ap.add_argument('--full', default=None, help='also write full-size PNGs here')
    ap.add_argument('--only', default=None)
    ap.add_argument('--topo', default=None)
    ap.add_argument('--sheet', default=None)
    ap.add_argument('--renders', default=None)
    a = ap.parse_args()
    data = Data(a.data)
    tmp = os.path.join(ROOT, 'out/stories/jackson-ward/png')
    os.makedirs(tmp, exist_ok=True)
    out = {'pages': a.out, 'full': a.full, 'tmp': tmp, 'dpi': 160, 'args': a}
    names = a.only.split(',') if a.only else list(CHARTS)
    for n in names:
        CHARTS[n](data, out)


CHARTS.update({'cut-fill': chart_cut_fill, 'profiles': chart_profiles, 'hillshade': chart_hillshade})


if __name__ == '__main__':
    main()
