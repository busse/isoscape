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
    ax.annotate(f'highest bank taken down:\n{-diff[j2, i2]:.1f} m, a ramp at the junction', xy=(data.xs[i2], data.ys[j2]), xytext=(data.xs[i2] - 60, data.ys[j2] + 260),
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
    gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 1.25], hspace=0.45, left=0.08, right=0.95, top=0.895, bottom=0.115)
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
    fig.text(0.08, 0.94, 'Elevations in meters above sea level (NAVD 88). Lidar: USGS 3DEP. 1934: USGS Richmond 1:24,000, surveyed 1933–34,\n'
             'contours every 10 ft (converted). No 1934 contour can be read where the three streets cross the trench; the check points\n'
             'are on the center line (bottom). ' + CREDIT,
             fontsize=8, color=R['muted'], ha='left', va='center', linespacing=1.35)
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
    ap.add_argument('--streets-check', action='store_true', help='draw today\'s streets over the 1934 sheet, to check its placing')
    a = ap.parse_args()
    data = Data(a.data)
    tmp = os.path.join(ROOT, 'out/stories/jackson-ward/png')
    os.makedirs(tmp, exist_ok=True)
    out = {'pages': a.out, 'full': a.full, 'tmp': tmp, 'dpi': 160, 'args': a}
    names = a.only.split(',') if a.only else list(CHARTS)
    for n in names:
        CHARTS[n](data, out)


CHARTS.update({'cut-fill': chart_cut_fill, 'profiles': chart_profiles, 'hillshade': chart_hillshade})


# ---- view meters and lon/lat (src/region.ts localMetres, src/view.ts makeView) ---------------

M_PER_DEG_LAT = 110_574


def from_view(data, pts):
    lon0, lat0 = data.d['center']
    kx = 111_320 * math.cos(math.radians(lat0))
    b = math.radians(data.bearing)
    x, y = np.asarray(pts)[..., 0], np.asarray(pts)[..., 1]
    e = x * math.cos(b) + y * math.sin(b)
    n = -x * math.sin(b) + y * math.cos(b)
    return lon0 + e / kx, lat0 + n / M_PER_DEG_LAT


def to_view(data, lon, lat):
    lon0, lat0 = data.d['center']
    kx = 111_320 * math.cos(math.radians(lat0))
    b = math.radians(data.bearing)
    e, n = (np.asarray(lon) - lon0) * kx, (np.asarray(lat) - lat0) * M_PER_DEG_LAT
    return e * math.cos(b) - n * math.sin(b), e * math.sin(b) + n * math.cos(b)


# ---- 5. the 1934 sheet, with the outline and the twelve check points ---------------------------

# View meters (E', N') the sheet is moved after its own projection and datum, found by a search
# (2 m steps, 40 m reach) for the shift that best puts today's street center lines between the
# sheet's printed street edges, away from the trench. The ground report's own fit found a shift
# of similar size (about 15 m). What is left over is the sheet's own error: under the National
# Map Accuracy Standards, 90% of well-defined points within about 12 m at 1:24,000.
TOPO_SHIFT = (6.0, 14.0)


def topo_on_view(data, path, bounds, res=1.5, shift=TOPO_SHIFT):
    """The 1934 USGS sheet resampled onto view meters (nearest pixel)."""
    import pyproj
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(path)
    tie = im.tag_v2[33922]
    px = im.tag_v2[33550]
    arr = np.asarray(im.convert('RGB'))
    # The sheet's own projection, from its GeoTIFF keys: polyconic about 37.5 N, 77.4375 W, NAD27.
    crs = pyproj.CRS('+proj=poly +lat_0=37.5 +lon_0=-77.4375 +x_0=0 +y_0=0 +datum=NAD27 +units=m +no_defs')
    tr = pyproj.Transformer.from_crs('EPSG:4326', crs, always_xy=True)
    xs = np.arange(bounds[0], bounds[1], res)
    ys = np.arange(bounds[2], bounds[3], res)
    X, Y = np.meshgrid(xs, ys)
    lon, lat = from_view(data, np.stack([X - shift[0], Y - shift[1]], -1))
    gx, gy = tr.transform(lon, lat)
    col = np.round((gx - tie[3]) / px[0]).astype(int)
    row = np.round((tie[4] - gy) / px[1]).astype(int)
    ok = (col >= 0) & (row >= 0) & (col < arr.shape[1]) & (row < arr.shape[0])
    out = np.ones(X.shape + (3,), dtype=np.uint8) * 255
    out[ok] = arr[row[ok], col[ok]]
    return out, (xs[0], xs[-1] + res, ys[0], ys[-1] + res)


GROUND_CHECKS = {   # ground.md, check 2: today (lidar), rebuilt, and the sheet's reading
    'P1': 'contours curve; levels not read', 'P2': 'one line; level not read', 'P3': 'one line; level not read',
    'P4': 'no contour: agrees (0.05 m)', 'P5': 'no contour: agrees within 0.8 m', 'P6': 'no contour: agrees',
    'P7': 'no contour: agrees', 'P8': 'no contour: agrees within 0.8 m', 'P9': 'no contour: agrees',
    'P10': 'no contour: agrees', 'P11': 'five contours bunched: a ravine head; disagrees', 'P12': 'the valley wall; kept as measured',
}


def chart_topo(data, out):
    path = out['args'].topo
    if not path:
        print('topo: no --topo sheet given; skipped')
        return
    bounds = (-780, 860, -560, 600)
    img, ext = topo_on_view(data, path, bounds)
    fig = plt.figure(figsize=(11.2, 8.6))
    ax = fig.add_axes([0.03, 0.12, 0.94, 0.80])
    plan_axes(ax, data, bounds)
    ax.imshow(img, origin='lower', extent=ext, zorder=0, interpolation='bilinear')
    ax.imshow(np.ones(img.shape[:2] + (4,)) * np.array(list(to_rgb(R['paper'])) + [0.25]), origin='lower', extent=ext, zorder=0.5)
    for r in data.trench['rings']:
        outline(ax, r, color=R['pick'], lw=1.6, dots=False, z=6)
    for r in data.junction['rings']:
        outline(ax, r, color=R['pick'], lw=1.3, dots=False, ls=(0, (4, 2.5)), z=6)
    if out['args'].streets_check:
        draw_streets(ax, data, lw=0.8, color=R['fill'])
    for c in data.d['checks']:
        x, y = c['p']
        if not (bounds[0] < x < bounds[1] and bounds[2] < y < bounds[3]):
            continue
        kind = CHECKS[c['id']][0]
        if kind == 'agrees':
            ax.scatter([x], [y], s=110, facecolor=R['paper'], edgecolor=R['ink'], lw=2, zorder=8)
        elif kind == 'disagrees':
            ax.scatter([x], [y], s=110, color=R['ink'], zorder=8)
        else:
            ax.scatter([x], [y], s=110, facecolor=R['paper'], edgecolor=R['ink'], lw=1.5, linestyle=(0, (2, 1.5)), zorder=8)
        ax.add_patch(plt.Circle((x, y), 60, fill=False, ec=R['ink'], lw=0.6, ls=(0, (2, 2)), zorder=7))
        label(ax, x + 42, y + 42, c['id'], size=9, weight=600)
    scale_bar(ax, -740, -525, 200)
    north_arrow(ax, data, -720, -440, 50)
    ax.set_title('The 1934 survey under the trench\'s outline, and the twelve points checked against it', fontsize=13, pad=8)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=R['pick'], lw=1.6, label='the trench\'s outline (rebuilt inside)'),
         Line2D([], [], marker='o', ls='', mfc=R['paper'], mec=R['ink'], mew=2, ms=9, label='the sheet agrees with the rebuilt ground'),
         Line2D([], [], marker='o', ls='', color=R['ink'], ms=9, label='the sheet disagrees (P11)'),
         Line2D([], [], marker='o', ls='', mfc=R['paper'], mec=R['ink'], mew=1.2, ms=9, label='level could not be read'),
         Line2D([], [], color=R['ink'], lw=0.6, ls=(0, (2, 2)), label='60 m around each point, the reach read')]
    fig.legend(handles=h, loc='lower left', ncol=3, bbox_to_anchor=(0.03, 0.035), fontsize=9)
    footer(fig, 'USGS Richmond, Va., 1:24,000, surveyed 1933–34 (public domain), placed on today\'s view by its own projection (polyconic, NAD27). '
                'P1 lies past the top of this frame. Readings from the ground report, check 2.')
    save(fig, out, '1934-checks')


# ---- 6. the hold-out test ----------------------------------------------------------------------

HOLDOUT = [   # ground.md, check 1: the fence moved onto undisturbed ground (m east, m north), RMS, 95%, worst
    ((-250, -330), 0.69, 1.59, 4.6, ''),
    ((-150, -450), 0.83, 2.06, 4.5, ''),
    ((-350, -250), 0.47, 0.90, 3.6, ''),
    ((0, -500), 1.13, 2.85, 6.0, 'crosses the Leigh Street cut'),
    ((-450, -150), 0.64, 1.31, 4.7, ''),
    ((-200, -600), 0.31, 0.66, 1.9, ''),
    ((200, 250), 1.82, 4.17, 8.3, 'onto the valley edge'),
]


def chart_holdout(data, out):
    rows = sorted(HOLDOUT, key=lambda r: r[2])
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    fig.subplots_adjust(left=0.30, right=0.97, top=0.80, bottom=0.2)
    ax.axvspan(0, 1.5, color=R['band'], alpha=0.35, lw=0, zorder=0)
    ax.axvline(1.5, color=R['rebuilt'], lw=1.2, zorder=1)
    ax.text(1.55, -0.5, 'stated error mid-trench: 1.5 m', fontsize=9, color=R['rebuilt'], va='center')
    ax.axvline(3.0, color=R['rebuilt'], lw=1.0, ls=(0, (3, 2)), zorder=1)
    ax.text(3.05, len(rows) - 0.45, 'at the trench\'s ends: 3 m', fontsize=9, color=R['rebuilt'], va='center')
    for k, (sh, rms, p95, worst, note) in enumerate(rows):
        ax.plot([0, worst], [k, k], color=R['faint'], lw=1, zorder=1)
        ax.scatter([rms], [k], s=60, color=R['ink'], zorder=4)
        ax.scatter([p95], [k], s=80, color=R['rebuilt'], zorder=4, edgecolor=R['paper'], lw=1.5)
        ax.scatter([worst], [k], s=60, facecolor=R['paper'], edgecolor=R['ink'], lw=1.5, zorder=4)
        ax.text(p95, k + 0.28, f'{p95:.2f}', fontsize=8.5, ha='center', color=R['ink'])
        lab = f'moved {sh[0]:+d} m east, {sh[1]:+d} m north'
        ax.text(-0.15, k, lab + ('\n' + note if note else ''), ha='right', va='center', fontsize=9.5, transform=ax.get_yaxis_transform() if False else ax.transData)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.set_xlim(0, 9)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xlabel('error of the rebuilt ground against the measured ground it replaced, meters')
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker='o', ls='', color=R['ink'], ms=7, label='typical (RMS)'),
         Line2D([], [], marker='o', ls='', color=R['rebuilt'], ms=8, label='95% of points within'),
         Line2D([], [], marker='o', ls='', mfc=R['paper'], mec=R['ink'], mew=1.5, ms=7, label='worst point')]
    ax.legend(handles=h, loc='lower right', fontsize=9)
    fig.suptitle('The method tried where the answer is known', x=0.012, ha='left', fontsize=13, fontweight=600, y=0.97)
    fig.text(0.012, 0.87, 'The trench\'s outline was moved onto undisturbed ground nearby, seven times. Each time the ground inside was rebuilt the same way and\n'
                          'compared with the lidar it replaced. On level plateau like the trench\'s, 95% of points come within about 0.7–2 m.', fontsize=9.5, va='top', color=R['ink'])
    footer(fig, 'Lidar: USGS 3DEP, 5 m grid. Numbers from the ground report, check 1.')
    save(fig, out, 'holdout')


CHARTS.update({'1934-checks': chart_topo, 'holdout': chart_holdout})


# ---- 7 and 8. the 1952 sheets' fit residuals -------------------------------------------------

def residuals():
    rows = list(csv.DictReader(open(os.path.join(HERE, 'residuals.csv'))))
    for r in rows:
        r['residual'] = float(r['residual m'])
        r['u'], r['v'] = float(r['u (full-res px)']), float(r['v (full-res px)'])
        r['mpp'] = float(r['m per full-res px'])
    return rows


def chart_sheet(data, out):
    path = out['args'].sheet
    if not path:
        print('sheet: no --sheet overlay given; skipped')
        return
    sheet = os.path.basename(path).split('-')[1]
    rows = [r for r in residuals() if r['sheet'] == sheet]
    im = Image.open(path).convert('RGB')
    MAG = 5                                   # disks drawn five times the sheet's scale, to be seen
    k = im.width / 4350.0                     # the overlay is the full-size scan scaled down
    fig = plt.figure(figsize=(11.2, 10.6))
    ax = fig.add_axes([0.02, 0.06, 0.62, 0.86])
    ax.imshow(np.asarray(im), zorder=0)
    ax.imshow(np.ones((im.height, im.width, 4)) * np.array(list(to_rgb(R['paper'])) + [0.35]), zorder=0.5)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_color(R['ink'])
    for r in rows:
        x, y = r['u'] * k, r['v'] * k
        rad = r['residual'] / r['mpp'] * k * MAG
        ax.add_patch(plt.Circle((x, y), max(rad, 2.5), fill=True, fc=R['pick'], alpha=0.35, ec=R['pick'], lw=1.5, zorder=5))
        ax.scatter([x], [y], s=28, color=R['ink'], zorder=6, lw=0)
        ax.annotate(f"{r['control point']}\n{r['residual']:.1f} m", xy=(x, y), xytext=(x + (40 if x < im.width * 0.75 else -150), y - 56), fontsize=8.5, zorder=7,
                    arrowprops=dict(arrowstyle='-', color=R['ink'], lw=0.7),
                    bbox=dict(boxstyle='round,pad=0.2', fc=R['paper'], ec='none', alpha=0.9))
    mean = sum(r['residual'] for r in rows) / len(rows)
    worst = max(r['residual'] for r in rows)
    fig.suptitle(f'One sheet, fitted to today\'s street corners: sheet {sheet} of the 1952 volume', x=0.02, ha='left', fontsize=13, fontweight=600, y=0.975)
    tx = 0.67
    lines = [
        ('How the sheet is placed', 600),
        (f'{len(rows)} street corners were read on the sheet (black dots) and matched to where today\'s street center lines cross. '
         'One fit (a shift, a turn and a scale) carries the whole sheet onto the map.', None),
        ('What a red disk means', 600),
        ('After the fit, each corner lands a little off. The disk\'s radius is that miss, drawn five times larger than the sheet\'s scale so it can be seen. '
         f'On this sheet the misses average {mean:.1f} m; the largest is {worst:.1f} m.', None),
        ('What it means for a building', 600),
        ('A building on this sheet may sit a few meters from where it stood, less than a house\'s width. '
         'No block was seen pushed across a street. Part of each miss is today\'s streets, some moved since 1952.', None),
        ('Colors on the sheet', 600),
        ('Pink: brick; yellow: frame; blue: stone or concrete block, as the sheet prints them. Magenta outlines: the tracing. '
         'Blue lines: today\'s streets (OpenStreetMap).', None),
    ]
    y = 0.90
    import textwrap
    for t, w in lines:
        txt = t if w else '\n'.join(textwrap.wrap(t, 46))
        fig.text(tx, y, txt, fontsize=10 if w else 9.5, fontweight=w or 400, va='top', color=R['ink'])
        y -= 0.03 if w else 0.022 * (txt.count('\n') + 1) + 0.03
    footer(fig, 'Sanborn Fire Insurance Map, Richmond, 1952, vol. 3, sheet ' + sheet + ' (Library of Congress, Geography and Map Division, Sanborn Maps Collection; public domain), with the trace\'s overlay.')
    save(fig, out, 'sheet-residuals')


def chart_residuals(data, out):
    rows = residuals()
    sheets = sorted({r['sheet'] for r in rows}, key=int)
    pick = out['args'].sheet and os.path.basename(out['args'].sheet).split('-')[1]
    fig, ax = plt.subplots(figsize=(11, 7.4))
    fig.subplots_adjust(left=0.09, right=0.56, top=0.84, bottom=0.12)
    import textwrap
    for k, sh in enumerate(sheets):
        v = [r['residual'] for r in rows if r['sheet'] == sh]
        y = len(sheets) - 1 - k
        ax.plot([0, 9.5], [y, y], color=R['faint'], lw=0.6, zorder=0)
        col = R['pick'] if sh == pick else R['ink']
        ax.scatter(v, [y] * len(v), s=36, color=col, alpha=0.85, zorder=3, lw=0)
        m = sum(v) / len(v)
        ax.plot([m, m], [y - 0.32, y + 0.32], color=col, lw=2.2, zorder=4)
        note = {'318': 'one corner; turned and shifted to fit the Gilpin Court buildings standing today',
                '326': 'worst: St. James & Duval',
                '309': 'scale from the sheet\'s scale bar; 7th St. corners left out (9–12 m)',
                '310': 'scale from the scale bar; corners on one street',
                '311': 'two corners carried from sheet 310',
                '317': 'two corners carried from 315; Webster St. corner left out (10.6 m)',
                '304': 'corners by water-pipe crossings', '320': 'corners by water-pipe crossings'}.get(sh, '')
        head = f"{len(v)} point{'s' if len(v) > 1 else ''}, mean {m:.1f} m"
        ax.text(9.8, y, '\n'.join(textwrap.wrap(head + (f'; {note}' if note else ''), 58)), fontsize=8.3, linespacing=1.05, va='center', color=R['muted'] if sh != pick else R['pick'], clip_on=False)
    ax.set_yticks(range(len(sheets)))
    ax.set_yticklabels([f'sheet {s}' for s in reversed(sheets)], fontsize=9.5)
    ax.tick_params(axis='y', length=0)
    ax.spines['left'].set_visible(False)
    ax.set_xlim(0, 9.5)
    ax.set_ylim(-0.7, len(sheets) - 0.3)
    ax.set_xlabel('how far each street corner lands from where the fit puts it, meters')
    fig.suptitle('Every sheet\'s fit: how far each control point misses', x=0.012, ha='left', fontsize=13, fontweight=600, y=0.97)
    fig.text(0.012, 0.905, f'{len(rows)} control points on {len(sheets)} sheets of the 1952 volume 3. Dots: one point each. Bar: the sheet\'s mean.'
             + (f' Sheet {pick} is the one shown up close.' if pick else ''), fontsize=9.5)
    footer(fig, 'Residuals from the 1952 trace (residuals.csv).')
    save(fig, out, 'residuals')


# ---- 9. the count: its polygons, and the count by sheet ---------------------------------------

def counts():
    return json.load(open(os.path.join(ROOT, 'tools/sanborn/jw/counts.json')))


def chart_count(data, out):
    from shapely.geometry import Polygon as SPoly
    from matplotlib.collections import PolyCollection
    c = counts()
    paved = [SPoly(poly[0], poly[1:]) for poly in data.d['footprint']['paved']]
    corridor = [SPoly(poly[0], poly[1:]) for poly in data.d['footprint']['corridor']]
    # Turn the plan so the corridor runs across the page (its long axis), north marked.
    pts = np.concatenate([np.array(poly[0]) for poly in data.d['footprint']['corridor']])
    ctr = pts.mean(axis=0)
    u, sv, vt = np.linalg.svd(pts - ctr)
    ang = math.atan2(vt[0][1], vt[0][0])
    ca, sa = math.cos(-ang), math.sin(-ang)

    def T(q):
        q = np.asarray(q, dtype=float) - ctr
        return np.column_stack([q[..., 0] * ca - q[..., 1] * sa, q[..., 0] * sa + q[..., 1] * ca]) if q.ndim == 2 else np.array([q[0] * ca - q[1] * sa, q[0] * sa + q[1] * ca])

    # Which buildings count is read from count.py's own list (counted-ids.json), so the plan shows
    # exactly what the count counts, by the same rule: a point inside the outline in the polygon,
    # no outline under 12 m2 (the map draws nothing smaller), the correction-table box left out.
    ids = json.load(open(os.path.join(ROOT, 'tools/sanborn/jw/counted-ids.json')))
    in_paved, in_corr = set(ids['paved']), set(ids['corridor'])
    groups = {'quiet': [], 'near': [], 'pick': []}
    n_in = {'paved': 0, 'corridor': 0}
    for b_ in data.d['traced']:
        if b_['id'] not in in_paved and b_['id'] not in in_corr and b_['m2'] < 12:
            continue
        in_p = b_['id'] in in_paved
        in_c = in_p or b_['id'] in in_corr
        n_in['paved'] += in_p
        n_in['corridor'] += in_c
        groups['pick' if in_p else 'near' if in_c else 'quiet'].append(T(b_['ring']))
    assert (n_in['paved'], n_in['corridor']) == (c['paved']['buildings'], c['corridor']['buildings']), (n_in, 'counted-ids.json and counts.json disagree: re-run count.py')
    tp = T(pts)
    bounds = (tp[:, 0].min() - 40, tp[:, 0].max() + 40, tp[:, 1].min() - 150, tp[:, 1].max() + 150)
    fig = plt.figure(figsize=(13, 7.6))
    ax = fig.add_axes([0.015, 0.36, 0.97, 0.54])
    plan_axes(ax, data, bounds)
    for st in data.d['streets']:
        if st['kind'] in ('residential', 'tertiary', 'primary', 'secondary', 'unclassified'):
            q = T(st['pts'])
            ax.plot(q[:, 0], q[:, 1], color=R['street'], lw=0.45, zorder=2)
    for g, fc in (('quiet', R['quiet']), ('near', R['near']), ('pick', R['pick'])):
        ax.add_collection(PolyCollection(groups[g], facecolors=fc, edgecolors=R['ink'], linewidths=0.25 if g == 'quiet' else 0.45, zorder=3 if g == 'quiet' else 4))
    for poly in data.d['footprint']['corridor']:
        for r in poly:
            q = T(r)
            ax.plot(np.append(q[:, 0], q[0, 0]), np.append(q[:, 1], q[0, 1]), color=R['ink'], lw=1.0, ls=(0, (4, 2.5)), zorder=6)
    for poly in data.d['footprint']['paved']:
        for r in poly:
            q = T(r)
            ax.plot(np.append(q[:, 0], q[0, 0]), np.append(q[:, 1], q[0, 1]), color=R['line'], lw=1.3, zorder=6)
    scale_bar(ax, bounds[0] + 30, bounds[2] + 30, 200)
    nv = T(np.array(data.north()) + ctr)
    x0, y0 = bounds[0] + 330, bounds[2] + 40
    ax.annotate('', xy=(x0 + nv[0] * 60, y0 + nv[1] * 60), xytext=(x0, y0), arrowprops=dict(arrowstyle='-|>', color=R['ink'], lw=1.2, mutation_scale=12), zorder=9)
    ax.text(x0 + nv[0] * 76, y0 + nv[1] * 76, 'N', ha='center', va='center', fontsize=9.5, fontweight=600, zorder=9)
    label(ax, bounds[0] + 120, bounds[3] - 40, 'west: Brook Road and the Belvidere ramps', size=8.5, color=R['muted'], ha='left')
    label(ax, bounds[1] - 30, bounds[3] - 40, 'east: the I-64 junction, cut at the line of 8th Street', size=8.5, color=R['muted'], ha='right')
    fig.suptitle('What the count counts: outlines on the 1952 sheets whose center falls inside each polygon', x=0.015, ha='left', fontsize=13, fontweight=600, y=0.975)
    fig.text(0.015, 0.925, 'The plan is turned so the highway runs across the page.', fontsize=9.5, color=R['muted'])
    # the numbers, from counts.json, and the count by sheet
    fig.text(0.015, 0.31, 'Buildings on the 1952 Sanborn sheets within this polygon', fontsize=11.5, fontweight=600, va='top')
    fig.text(0.015, 0.265, f"Paved polygon (today's roadway and ramps): {c['paved']['buildings']}", fontsize=10.5, va='top')
    fig.text(0.015, 0.23, f"Corridor (the paved polygon plus 15 m each side): {c['corridor']['buildings']}", fontsize=10.5, va='top')
    fig.text(0.015, 0.18, 'A count of outlines on a map. Outlines under 12 m² (privies and small\nsheds, which the map does not draw) are not counted; an apartment\nhouse is one. Not homes, families or people. '
                          'The polygon is\ntoday\'s footprint, standing in for the 1958 right-of-way,\nwhich has not been seen.', fontsize=9.5, va='top')
    bx = fig.add_axes([0.55, 0.075, 0.40, 0.185])
    sheets = sorted(c['corridor']['sheets'], key=int)
    xs = np.arange(len(sheets))
    pv = [c['paved']['sheets'].get(s_, 0) for s_ in sheets]
    cv = [c['corridor']['sheets'][s_] for s_ in sheets]
    bx.bar(xs, cv, color=R['near'], width=0.6, zorder=2)
    bx.bar(xs, pv, color=R['pick'], width=0.6, zorder=3)
    for x, a_, b2 in zip(xs, pv, cv):
        bx.text(x, b2 + 3, f'{a_} · {b2}', ha='center', fontsize=9)
    bx.set_xticks(xs)
    bx.set_xticklabels([f'sheet {s_}' for s_ in sheets], fontsize=9)
    bx.tick_params(axis='x', length=0)
    bx.set_ylim(0, max(cv) * 1.25)
    bx.set_yticks([0, 50, 100])
    bx.set_title('By sheet: paved · corridor', fontsize=10.5)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    h = [Patch(color=R['pick'], label='center in the paved polygon'), Patch(color=R['near'], label='in the corridor only'),
         Patch(color=R['quiet'], label='every other 1952 outline'),
         Line2D([], [], color=R['line'], lw=1.3, label='paved polygon'), Line2D([], [], color=R['ink'], lw=1.0, ls=(0, (4, 2.5)), label='corridor polygon')]
    fig.legend(handles=h, loc='upper left', ncol=5, bbox_to_anchor=(0.015, 0.355), fontsize=9, handlelength=1.6, columnspacing=1.2)
    footer(fig, 'Counts: tools/sanborn/jw/counts.json and counted-ids.json (count.py); this plan draws the same ids. Sanborn, Richmond 1952 vol. 3 (Library of Congress, public domain); streets: OpenStreetMap (ODbL).')
    save(fig, out, 'count')


CHARTS.update({'sheet-residuals': chart_sheet, 'residuals': chart_residuals, 'count': chart_count})


# ---- 3. the three-way view -------------------------------------------------------------------

def chart_threeway(data, out):
    """Crops of three builds of the region, by the same scene coordinates:
       <renders>/today.png|svg          node bin/isoscape.js build jackson-ward --year 2026 --png 3400
       <renders>/today-ground.png|svg   the 1952 build with the history's `ground` removed (a scratch copy)
       <renders>/rebuilt.png|svg        node bin/isoscape.js build jackson-ward --year 1952 --png 3400"""
    import re
    d = out['args'].renders
    if not d:
        print('three-way: no --renders folder given; skipped')
        return
    panels = [('today', 'Today, 2026: the trench as the lidar measures it'),
              ('today-ground', '1952 drawn on today\'s ground: the trench runs through a year it did not exist'),
              ('rebuilt', '1952 on the rebuilt ground: the trench filled by estimate, the lost streets at grade')]
    crop = (-640, 520, -430, 70)             # scene units (the SVG's): the trench from St. Peter Street to 5th Street
    fig = plt.figure(figsize=(11, 15.2))
    for k, (name, title) in enumerate(panels):
        # Render the SVG cropped to the window by its viewBox, at twice the PNG's scale.
        svg = open(os.path.join(d, name + '.svg')).read()
        svg = re.sub(r'viewBox="[^"]+"', f'viewBox="{crop[0]} {crop[2]} {crop[1] - crop[0]} {crop[3] - crop[2]}"', svg, count=1)
        tmp_svg = os.path.join(out['tmp'], f'three-way-{name}.svg')
        tmp_png = os.path.join(out['tmp'], f'three-way-{name}.png')
        open(tmp_svg, 'w').write(svg)
        subprocess.run(['rsvg-convert', '-w', '2320', tmp_svg, '-o', tmp_png], check=True)
        im = Image.open(tmp_png).convert('RGB')
        bg = Image.new('RGB', im.size, tuple(int(v * 255) for v in to_rgb(R['paper'])))
        ax = fig.add_axes([0.02, 0.665 - k * 0.3, 0.96, 0.262])
        ax.imshow(np.asarray(Image.open(tmp_png).convert('RGBA')) if False else np.asarray(Image.alpha_composite(bg.convert('RGBA'), Image.open(tmp_png).convert('RGBA')).convert('RGB')))
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(True); sp.set_color(R['ink']); sp.set_linewidth(0.9)
        ax.set_title(title, fontsize=11.5, pad=6)
    fig.suptitle('The same blocks three ways', x=0.02, ha='left', fontsize=13.5, fontweight=600, y=0.975)
    footer(fig, 'Crops of three builds of the Jackson Ward view, drawn by Chris Busse with isoscape; the middle one is a check made for this chart only. '
                'The ground in the bottom view is an estimate, about ±1.5 m mid-trench. Lidar: USGS 3DEP; streets and today\'s buildings: OpenStreetMap; '
                '1952 buildings: Sanborn, Library of Congress.')
    save(fig, out, 'three-way')


CHARTS.update({'three-way': chart_threeway})


# ---- the study area of the cap, over today's ward ----------------------------------------------

# Reconnect Jackson Ward Feasibility Study (OIPI, VDOT, City of Richmond; September 2022),
# section 3.2.4 and Table 6: the structural assessment areas, each named by the cross streets
# that bound it, and section 3.3: Areas B, C, D and E "were considered to be technically feasible".
STUDY_AREAS = [
    ('A', 'North Belvidere Street', 'Chamberlayne Parkway', False, 'not feasible: no room for piers\nbeside the planned interchange'),
    ('B', 'Chamberlayne Parkway', 'Saint Paul Street', True, ''),
    ('C', 'Saint Paul Street', 'Saint John Street', True, ''),
    ('D', 'Saint John Street', 'Saint James Street', True, ''),
    ('E', 'Saint James Street', 'North 1st Street', True, ''),
    ('F', 'North 1st Street', 'North 2nd Street', False, 'not feasible: too little clearance\nover the I-64 ramp'),
]
LANDMARKS = [   # a point inside each building, from the 1952 trace's named buildings (named.csv)
    ('Sixth Mount Zion Baptist', -77.4382508, 37.550512),
    ('Ebenezer Baptist', -77.4420336, 37.5505201),
    ('Leigh Street Armory', -77.4413725, 37.5500545),
    ('Hippodrome', -77.438113, 37.5472903),
]


def chart_study(data, out):
    from shapely.geometry import LineString, Point, Polygon as SPoly
    from shapely.ops import substring
    from matplotlib.collections import PolyCollection
    pts = centerline(data)
    head = pts[0] + (pts[0] - pts[1]) / np.linalg.norm(pts[0] - pts[1]) * 900
    cl = LineString(np.vstack([head, pts]))

    def station(name):
        P = [p for s in data.d['streets'] if s['name'] == name and s['kind'] not in ('footway', 'service') for p in s['pts']]
        near = [cl.project(Point(p)) for p in P if cl.distance(Point(p)) < 120]
        return float(np.mean(near))
    bounds = (-1250, 520, -330, 1000)
    fig = plt.figure(figsize=(11.2, 9.6))
    ax = fig.add_axes([0.02, 0.17, 0.96, 0.75])
    plan_axes(ax, data, bounds)
    ax.add_collection(PolyCollection(data.d['buildings'], facecolors=R['quiet'], edgecolors=R['muted'], linewidths=0.25, zorder=2))
    draw_streets(ax, data, lw=0.5)
    draw_highway(ax, data, color=R['ink'], lw=0.9)
    for k, (letter, a, b, ok, why) in enumerate(STUDY_AREAS):
        s0, s1 = station(a), station(b)
        band = substring(cl, s0, s1).buffer(48, cap_style=2)
        ring = np.array(band.exterior.coords)
        ax.fill(ring[:, 0], ring[:, 1], color=R['pick'] if ok else R['paper'], alpha=0.55 if ok else 0.85, zorder=4, lw=0)
        ax.plot(ring[:, 0], ring[:, 1], color=R['line'] if ok else R['ink'], lw=1.3, ls='-' if ok else (0, (4, 2.5)), zorder=5)
        m = substring(cl, (s0 + s1) / 2, (s0 + s1) / 2 + 1).coords[0]
        ax.text(m[0], m[1], letter, ha='center', va='center', fontsize=13, fontweight=700, color=R['ink'], zorder=7)
        if why:
            off = (-330, -60) if letter == 'A' else (230, -150)
            ax.annotate(why, xy=m, xytext=(m[0] + off[0], m[1] + off[1]), fontsize=8.5, ha='center', zorder=8,
                        arrowprops=dict(arrowstyle='-', color=R['ink'], lw=0.7),
                        bbox=dict(boxstyle='round,pad=0.25', fc=R['paper'], ec='none', alpha=0.92))
    for name, short in [('North Belvidere Street', 'Belvidere'), ('Chamberlayne Parkway', 'Chamberlayne'), ('Saint Paul Street', 'St. Paul'),
                        ('Saint John Street', 'St. John'), ('Saint James Street', 'St. James'), ('North 1st Street', '1st'), ('North 2nd Street', '2nd')]:
        p = substring(cl, station(name), station(name) + 1).coords[0]
        label(ax, p[0] + 62, p[1] + 66, short, size=8.5, color=R['ink'], weight=600)
    for name, lon, lat in LANDMARKS:
        x, y = to_view(data, lon, lat)
        ax.scatter([x], [y], s=34, color=R['ink'], zorder=8)
        label(ax, x - 14, y - 28, name, size=8.5, ha='right')
    gx, gy = to_view(data, -77.4391444, 37.5531215)   # the mean of the Gilpin Court blocks the 1952 sheets name
    label(ax, gx, gy, 'Gilpin Court', size=10, color=R['ink'], weight=600)
    label(ax, 250, -250, 'toward Broad Street', size=8.5, color=R['muted'])
    scale_bar(ax, bounds[0] + 40, bounds[2] + 40, 200)
    north_arrow(ax, data, bounds[0] + 60, bounds[2] + 120, 50)
    fig.suptitle('Where a cap was studied: the 2022 feasibility study\'s six areas over the highway', x=0.02, ha='left', fontsize=13, fontweight=600, y=0.975)
    fig.text(0.02, 0.935, 'Each area is drawn between the two cross streets the study names for it; the band\'s width (about 100 m) is ours, not the study\'s. Approximate.',
             fontsize=9.5, color=R['ink'])
    from matplotlib.patches import Patch
    h = [Patch(fc=R['pick'], alpha=0.55, ec=R['line'], label='found technically feasible (Areas B–E)'),
         Patch(fc=R['paper'], ec=R['ink'], ls='--', label='found not feasible (A, F)')]
    fig.legend(handles=h, loc='lower left', ncol=2, bbox_to_anchor=(0.02, 0.095), fontsize=9.5)
    fig.text(0.02, 0.085, 'The study area for its data reached wider, to Lombardy Street, School Street and Valley Road, 7th Street and Broad Street. '
             'The study proposed no single design;\nit tested whether a bridge or lid could stand here. This chart takes no position on whether one should.',
             fontsize=9, va='top')
    footer(fig, 'Source: Reconnect Jackson Ward Feasibility Study, Sept. 2022 (sections 1.1, 3.2.4, 3.3). Today\'s streets and buildings: OpenStreetMap (ODbL). '
                'Landmarks placed from the 1952 Sanborn trace.')
    save(fig, out, 'study-area')


CHARTS.update({'study-area': chart_study})



# ---- 11. the overlay plan: the highway over the 1952 houses over today's ward ------------------

COLISEUM = (-77.43443, 37.54463)   # The Richmond Coliseum: the center of its OSM outline (way 321367756)


def chart_overlay(data, out):
    """Decision 11: the early plan view, redrawn flat. Today's buildings in gray under today's street
    plan, the 1952 traced outlines in their printed colors over them, and the highway's paved
    footprint and corridor over both."""
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    gray = mix(P['ink'], P['sky'], 0.80)
    fig = plt.figure(figsize=(13, 10.6))
    ax = fig.add_axes([0.012, 0.14, 0.976, 0.79])
    bounds = (-950, 950, -790, 600)     # the region's frame, run south to take in the Coliseum
    plan_axes(ax, data, bounds)
    # Today's buildings and streets from the region's OSM cache, which reaches past the frame.
    osm = json.load(open(os.path.join(ROOT, 'data/richmond-streetcars/osm.json')))['elements']
    kinds = ('residential', 'tertiary', 'primary', 'secondary', 'primary_link', 'secondary_link', 'tertiary_link', 'unclassified', 'living_street', 'motorway', 'motorway_link', 'trunk')
    blds = []
    for e in osm:
        if e['type'] != 'way' or len(e.get('geometry', [])) < 2:
            continue
        g = e['geometry']
        x, y = to_view(data, [q['lon'] for q in g], [q['lat'] for q in g])
        if x.max() < bounds[0] - 50 or x.min() > bounds[1] + 50 or y.max() < bounds[2] - 50 or y.min() > bounds[3] + 50:
            continue
        t = e.get('tags', {})
        if 'building' in t and len(g) > 3:
            blds.append(np.column_stack([x, y]))
        elif t.get('highway') in kinds:
            ax.plot(x, y, color=R['street'], lw=0.5, zorder=2)
    ax.add_collection(PolyCollection(blds, facecolors=gray, edgecolors=mix(P['ink'], P['sky'], 0.6), linewidths=0.2, zorder=1))
    by = {}
    for t in data.d['traced']:
        if t['m2'] >= 12:
            by.setdefault(t['material'], []).append(np.array(t['ring']))
    for mat, rings in by.items():
        ax.add_collection(PolyCollection(rings, facecolors=P['traced'][mat], edgecolors=R['ink'], linewidths=0.22, zorder=3))
    for name, fc, a, ls, lw in (('corridor', R['near'], 0.32, (0, (4, 2.5)), 1.0), ('paved', R['pick'], 0.42, '-', 1.2)):
        for poly in data.d['footprint'][name]:
            for k, r in enumerate(poly):
                q = np.array(r)
                if k == 0:
                    ax.fill(q[:, 0], q[:, 1], color=fc, alpha=a, lw=0, zorder=4)
                ax.plot(np.append(q[:, 0], q[0, 0]), np.append(q[:, 1], q[0, 1]), color=R['line'], lw=lw, ls=ls, zorder=5)
    cx, cy = to_view(data, *COLISEUM)
    label(ax, cx + 150, cy + 20, 'the Coliseum (today)', size=9)
    for nm, lon, lat in (('Gilpin Court', -77.4405, 37.5545), ('Second Street', -77.4382, 37.5468), ('Leigh Street', -77.4318, 37.5468), ('Broad Street', -77.4420, 37.5452)):
        x, y = to_view(data, lon, lat)
        label(ax, x, y, nm, size=8.5, color=R['muted'])
    scale_bar(ax, -920, -765, 200)
    north_arrow(ax, data, -880, -690, 50)
    ax.set_title('The highway laid over the 1952 sheets, over today\'s ward', pad=8, fontsize=13)
    h = [Patch(color=R['pick'], alpha=0.6, label='highway: today\'s paved roadway and ramps'),
         Patch(facecolor=R['near'], alpha=0.5, edgecolor=R['line'], ls='--', label='corridor: plus 15 m each side'),
         Patch(color=P['traced']['brick'], label='1952 outline, brick'), Patch(color=P['traced']['frame'], label='1952 outline, frame'),
         Patch(color=P['traced']['stone'], label='1952, stone or concrete'), Patch(color=P['traced']['special'], label='1952, other materials'),
         Patch(color=gray, label='buildings today (OSM)'), Line2D([], [], color=R['street'], lw=1, label='streets today (OSM)')]
    fig.legend(handles=h, loc='lower left', ncol=4, bbox_to_anchor=(0.012, 0.062), fontsize=9, handlelength=1.6, columnspacing=1.2, frameon=False)
    footer(fig, 'Plan of the ward, north about 10° right of up. 1952 outlines: Sanborn Map Co., Richmond, Va., 1952, vol. 3, sheets 304–312, 315, '
                '317–320 and 326 (Library of Congress, Geography and Map Division, Sanborn Maps Collection; public domain), traced in code and fitted to '
                'today\'s street corners (a few meters off). Uncolored 1952 outlines are drawn as frame. Today\'s buildings and streets: OpenStreetMap '
                'contributors (ODbL). The highway polygons are today\'s footprint, a stand-in for the 1958 right-of-way.')
    save(fig, out, 'overlay')


CHARTS.update({'overlay': chart_overlay})


if __name__ == '__main__':
    main()
