#!/usr/bin/env python3
"""The redlining story's method charts, from numbers.json (written by measure.py).

    python3 tools/stories/redlining/measure.py
    python3 tools/stories/redlining/charts.py [--full DIR]

Writes pages/redlining-<name>.webp (1600 px wide) and, with --full, a PNG of each for review:

- `land`: graded land by grade, in square kilometers, with the number of areas.
- `highways`: two bars split by grade, the graded land and the limited-access highway
  (OSM motorway) inside it, so the reader sees the highway's share beside the land's.

Colors are the map's own grade tones and ink, read from src/palette.ts, never typed here. Each
chart states its source, year and method under it. Drawn flat: thin marks, text in ink, no
gridlines heavier than the paper.
"""
import argparse
import json
import os
import subprocess

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
GRADES = ['A', 'B', 'C', 'D']
NAMES = {'A': 'A "Best"', 'B': 'B "Still Desirable"', 'C': 'C "Definitely Declining"', 'D': 'D "Hazardous"'}


def palette():
    js = "import('./src/palette.ts').then(m => console.log(JSON.stringify(m.PALETTES.paper)))"
    out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


P = palette()
TONE = dict(zip(GRADES, P['tint']['tones']))
INK, PAPER = P['ink'], P['sky']
plt.rcParams.update({'font.family': 'DejaVu Serif', 'text.color': INK, 'axes.edgecolor': INK, 'xtick.color': INK, 'ytick.color': INK})


def finish(fig, name, note, full):
    fig.text(0.02, 0.02, note, fontsize=9.5, style='italic', va='bottom', wrap=True)
    png = os.path.join(full or '/tmp', f'redlining-{name}.png')
    fig.savefig(png, dpi=200, facecolor=PAPER)
    plt.close(fig)
    im = Image.open(png).convert('RGB')
    im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS).save(os.path.join(ROOT, 'pages', f'redlining-{name}.webp'), quality=88, method=6)
    if not full:
        os.remove(png)
    print(f'redlining-{name}: {im.width}×{im.height}')


def land(n, full):
    g = n['graded_land']
    fig, ax = plt.subplots(figsize=(8, 3.9), facecolor=PAPER)
    fig.subplots_adjust(left=0.27, right=0.95, top=0.82, bottom=0.3)
    ax.set_facecolor(PAPER)
    ys = list(range(len(GRADES)))[::-1]
    for y, k in zip(ys, GRADES):
        ax.barh(y, g[k]['km2'], height=0.62, color=TONE[k], edgecolor=INK, linewidth=0.8)
        ax.text(g[k]['km2'] + 0.25, y, f"{g[k]['km2']:.1f} km²  ({round(g[k]['share'] * 100)}%, {g[k]['areas']} areas)", va='center', fontsize=10.5)
    ax.set_yticks(ys, [NAMES[k] for k in GRADES], fontsize=10.5)
    ax.set_xlim(0, max(g[k]['km2'] for k in GRADES) * 1.55)
    ax.set_xlabel('square kilometers', fontsize=10)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    fig.suptitle('Richmond\'s graded land in 1937, by grade', x=0.02, ha='left', fontsize=13.5, fontweight='bold')
    finish(fig, 'land', f"Source: the HOLC's 1937 Richmond map as digitized by Mapping Inequality (CC BY-NC). Areas measured on a local plane by "
                         f"tools/stories/redlining/measure.py; each grade's polygons merged. {n['graded_km2_union']:.1f} km² graded in all. The grade names are the HOLC's own.", full)


def highways(n, full):
    m = n['motorway']
    land_share = {k: n['graded_land'][k]['share'] for k in GRADES}
    rows = [('Graded land, 1937', land_share, f"{n['graded_km2_union']:.1f} km²"),
            ('Limited-access highway\ninside graded land, today', m['by_grade_share'], f"{m['km_in_graded']:.1f} km of carriageway")]
    fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=PAPER)
    fig.subplots_adjust(left=0.27, right=0.97, top=0.74, bottom=0.3)
    ax.set_facecolor(PAPER)
    for y, (label, share, total) in zip([1, 0], rows):
        x = 0.0
        for k in GRADES:
            w = share[k]
            ax.barh(y, w, left=x, height=0.58, color=TONE[k], edgecolor=PAPER, linewidth=2)
            if w >= 0.06:
                ax.text(x + w / 2, y, f'{k}  {round(w * 100)}%', ha='center', va='center', fontsize=10.5, fontweight='bold' if k == 'D' else 'normal')
            else:
                ax.text(x + w / 2, y - 0.36, f'{k} {round(w * 100)}%', ha='center', va='top', fontsize=9.5)
            x += w
        ax.text(1.0, y + 0.42, total, ha='right', va='bottom', fontsize=9.5)
    ax.set_yticks([1, 0], [r[0] for r in rows], fontsize=10.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 1.6)
    ax.set_xticks([])
    for s in ('top', 'right', 'bottom', 'left'):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    d_land, d_road = round(land_share['D'] * 100), round(m['by_grade_share']['D'] * 100)
    fig.suptitle(f'Where the highways run: D was {d_land}% of the graded land and holds\n{d_road}% of the limited-access highway inside it', x=0.02, ha='left', fontsize=13, fontweight='bold')
    finish(fig, 'highways', f"Sources: grades, HOLC 1937 via Mapping Inequality (CC BY-NC); highways, OpenStreetMap ways tagged motorway, fetched Nov. 16, 2026 (ODbL).\n"
                            f"Each carriageway counted; ramps left out (with ramps, D holds {round(n['motorway_and_links']['by_grade_share']['D'] * 100)}%). It shows where the roads run; why they run there is in \"How we know\". measure.py.", full)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--full')
    a = ap.parse_args()
    n = json.load(open(os.path.join(HERE, 'numbers.json')))
    land(n, a.full)
    highways(n, a.full)


if __name__ == '__main__':
    main()
