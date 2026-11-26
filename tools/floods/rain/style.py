"""Shared look for the Gaston rain pictures: isoscape's paper palette, one blue family for rain.

Every color is read from src/palette.ts (the paper palette) or mixed from two of its colors,
as tools/stories/jackson-ward/charts.py does, so no new hex values are introduced here.
"""
import json
import os
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import ListedColormap, BoundaryNorm, to_rgb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def load_palette():
    js = "import('./src/palette.ts').then(m => console.log(JSON.stringify(m.PALETTES.paper)))"
    out = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


P = load_palette()


def mix(a, b, t):
    ra, rb = np.array(to_rgb(a)), np.array(to_rgb(b))
    return tuple(ra * (1 - t) + rb * t)


RAIN_DEEP = mix(P["tint"]["tones"][1], P["ink"], 0.36)
R = {
    "paper": P["sky"],
    "land": P["land"],
    "ink": P["ink"],
    "muted": mix(P["ink"], P["sky"], 0.45),
    "faint": mix(P["ink"], P["sky"], 0.78),
    "water": P["water"],
    "waterLine": P["waterLine"],
    "rain": RAIN_DEEP,
    "rain_mid": mix(P["sky"], RAIN_DEEP, 0.5),
    "range": mix(P["sky"], RAIN_DEEP, 0.25),
    "pick": P["mark"]["pick"],
    "line": P["mark"]["line"],
    "shed": P["mark"]["line"],
}

# storm-total bands, inches
TOTAL_LEVELS = [0, 2, 4, 6, 8, 10, 12, 99]
# hourly bands, inches per hour
HOURLY_LEVELS = [0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 99]


def ramp(n, lo=0.05, hi=1.0):
    return [mix(P["sky"], RAIN_DEEP, t) for t in np.linspace(lo, hi, n)]


def cmap_for(levels, lo=0.07):
    cols = ramp(len(levels) - 1, lo)
    return ListedColormap(cols), BoundaryNorm(levels, len(cols)), cols


FONT = "Inter" if any("Inter" in f.name for f in font_manager.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({
    "font.family": FONT,
    "font.size": 10.5,
    "text.color": R["ink"],
    "axes.labelcolor": R["muted"],
    "axes.edgecolor": R["muted"],
    "axes.facecolor": R["paper"],
    "figure.facecolor": R["paper"],
    "savefig.facecolor": R["paper"],
    "xtick.color": R["muted"],
    "ytick.color": R["muted"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.titlesize": 11.5,
    "axes.titleweight": 600,
    "axes.titlelocation": "left",
    "legend.frameon": False,
    "legend.fontsize": 9.5,
})

CREDIT = "Made in code with Claude for isoscape (Chris Busse); see the artist statement."


def footer(fig, text, y=0.008):
    fig.text(0.012, y, text + " " + CREDIT, fontsize=7.6, color=R["muted"], ha="left", va="bottom", wrap=True)
