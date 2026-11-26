#!/usr/bin/env python3
"""Gaston rain on isoscape's view of the city: the composite (treatment ii) and the explainer.

    python3 tools/floods/rain/iso.py BUILD_DIR OUTDIR [--explainer] [--round N]

BUILD_DIR holds an isoscape build of the region with no rain on it, made with
    node bin/isoscape.js build richmond-gaston-rain --year 2004 --png --width 3400
(or richmond-gaston-rain-x3 for the explainer, relief drawn three times its height).
Points are placed on the picture with isoscape's own `locate` command (lon,lat to the SVG's
ground coordinates), so the rain, the watershed and the labels sit where isoscape draws the
ground. The rain is the corrected storm total (data/radar-grids.npz), smoothed as in the plan
map, laid over the drawing as a see-through wash with labeled isohyets.
Dev tool: numpy, scipy, matplotlib, Pillow.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style import R, plt, footer, ramp, mix, P  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DATA = os.path.join(HERE, "data")
Image.MAX_IMAGE_PIXELS = None


def locate(region, pts, cache):
    if os.path.exists(cache):
        got = json.load(open(cache))
        if len(got) == len(pts):
            return np.array([[g["x"], g["y"]] for g in got])
    args = [f"{lo:.6f},{la:.6f}" for lo, la in pts]
    out = subprocess.run(["node", "bin/isoscape.js", "locate", region, "--year", "2004", "--", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    got = json.loads(out.stdout)
    json.dump(got, open(cache, "w"))
    return np.array([[g["x"], g["y"]] for g in got])


def main():
    bdir, out = sys.argv[1], sys.argv[2]
    explainer = "--explainer" in sys.argv
    rnd = sys.argv[sys.argv.index("--round") + 1] if "--round" in sys.argv else "1"
    region = "richmond-gaston-rain-x3" if explainer else "richmond-gaston-rain"
    svg = os.path.join(bdir, f"{region}-2004.svg")
    png = os.path.join(bdir, f"{region}-2004.png")
    head = open(svg).read(4000)
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', head).group(1).split()]
    img = Image.open(png).convert("RGB")
    k = img.width / vb[2]
    to_px = lambda xy: np.column_stack([(xy[:, 0] - vb[0]) * k, (xy[:, 1] - vb[1]) * k])  # noqa: E731

    # a lon/lat mesh over the view, the watershed outline and the places to label
    # the region's frame (center -77.444, 37.5555; 8,600 by 6,400 m; bearing 0), a little inside
    lons = np.linspace(-77.4925, -77.3955, 66)
    lats = np.linspace(37.5270, 37.5840, 48)
    LO, LA = np.meshgrid(lons, lats)
    shed = json.load(open(os.path.join(DATA, "watershed-display.geojson")))["features"][0]["geometry"]["coordinates"][0]
    places = {"low": (-77.4304, 37.5339), "james": (-77.457, 37.5305), "fan": (-77.475, 37.553), "north": (-77.452, 37.5805),
              "church": (-77.418, 37.533), "capitol": (-77.4335, 37.5385), "valley": (-77.427, 37.566), "fanstart": (-77.468, 37.5555)}
    pts = list(zip(LO.ravel(), LA.ravel())) + [tuple(p) for p in shed] + list(places.values())
    xy = to_px(locate(region, pts, os.path.join(bdir, "locate-v2.json")))
    n = LO.size
    GX, GY = xy[:n, 0].reshape(LO.shape), xy[:n, 1].reshape(LO.shape)
    SX, SY = xy[n:n + len(shed), 0], xy[n:n + len(shed), 1]
    PL = {name: xy[n + len(shed) + i] for i, name in enumerate(places)}

    g = np.load(os.path.join(DATA, "radar-grids.npz"))
    tot = ndimage.gaussian_filter(g["total_corrected"].astype(float), 1.1)
    f = RegularGridInterpolator((g["lats"], g["lons"]), tot)
    Z = f(np.column_stack([LA.ravel(), LO.ravel()])).reshape(LO.shape)
    rain = json.load(open(os.path.join(DATA, "rain.json")))
    bt = rain["basin_total_in"]

    # crop: below the build's own caption, round the drawing
    top = int(max(0, GY.min() - 4))
    bottom = int(min(img.height, GY.max() + 40))
    img = img.crop((0, top, img.width, bottom))
    W, H = img.size
    scale = 2000 / W
    img = img.resize((2000, int(H * scale)), Image.LANCZOS)
    GX, GY, SX, SY = GX * scale, (GY - top) * scale, SX * scale, (SY - top) * scale
    PL = {kk: np.array([v[0] * scale, (v[1] - top) * scale]) for kk, v in PL.items()}
    W, H = img.size

    fig_w = 11.0
    fig_h = fig_w * (H / W) + (1.4 if not explainer else 1.6)
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=W / fig_w * 0.98)
    axh = fig_w * (H / W) / fig_h
    ax = fig.add_axes([0.0, 0.5 / fig_h, 1.0, axh])
    ax.imshow(img, extent=[0, W, H, 0])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    import matplotlib.patheffects as pe
    halo = [pe.withStroke(linewidth=3, foreground=R["paper"])]

    if not explainer:
        levels = [7, 8, 9, 10, 11, 12, 13]
        cols = ramp(len(levels) - 1, 0.25)
        ax.contourf(GX, GY, Z, levels=levels, colors=cols, alpha=0.42, zorder=2, extend="max")
        cs = ax.contour(GX, GY, Z, levels=levels[1:-1], colors=[R["rain"]], linewidths=1.3, zorder=3)
        lab = ax.clabel(cs, fmt=lambda v: f"{v:g} in", fontsize=9.5, inline=True, inline_spacing=6)
        for t in lab:
            t.set_color(R["rain"])
            t.set_fontweight(600)
            t.set_path_effects(halo)
        ax.plot(SX, SY, color=R["paper"], lw=4.2, zorder=4)
        ax.plot(SX, SY, color=R["shed"], lw=2.2, zorder=5)
        lx, ly = PL["low"]
        ax.scatter([lx], [ly], s=60, facecolor=R["shed"], edgecolor=R["paper"], lw=1.5, zorder=6)
        t = ax.annotate("lowest ground of Shockoe Bottom,\nnear 17th and Main", xy=(lx, ly), xytext=(lx + 120, ly + 70), fontsize=9.5, fontweight=600,
                        color=R["ink"], zorder=7, arrowprops=dict(arrowstyle="-", color=R["ink"], lw=0.9))
        t.set_path_effects(halo)
        nx_, ny_ = PL["north"]
        t = ax.text(nx_, ny_, "Shockoe Creek watershed", fontsize=11, fontweight=600, color=R["shed"], ha="center", zorder=7)
        t.set_path_effects(halo)
        jx, jy = PL["james"]
        t = ax.text(jx, jy, "James River", fontsize=10, style="italic", color=R["waterLine"], ha="center", zorder=7)
        t.set_path_effects(halo)
        fig.text(0.015, 1 - 0.15 / fig_h, "Gaston's rain on the city: 8 to 11 inches on all of the Shockoe Creek watershed", fontsize=14, fontweight=600, va="top")
        fig.text(0.015, 1 - 0.47 / fig_h, f"Storm total, inches (wash; lines every inch), on isoscape's Richmond of 2004, looking north. "
                 f"Watershed average {bt['radar_corrected']:.1f} in (range {bt['low']:.1f} to {bt['high']:.1f}).", fontsize=9.4, va="top")
        footer(fig, "Rain: NEXRAD Level II, KAKQ (NOAA), tropical Z-R, corrected to gauges (NCEI, NWS, NHC); lines every inch, smoothed to the radar's "
               "detail of about 1.5 km. Watershed: computed from USGS 3DEP. Drawing: isoscape (OpenStreetMap, USGS 3DEP, City of Richmond year built).", y=0.006)
        name = f"iso-composite-r{rnd}.png"
    else:
        # the explainer: a light wash of the rain, the funnel, the low point, the river low
        levels = [7, 8, 9, 10, 11, 12, 13]
        cols = ramp(len(levels) - 1, 0.25)
        ax.plot(SX, SY, color=R["paper"], lw=4.6, zorder=4)
        ax.plot(SX, SY, color=R["shed"], lw=2.6, zorder=5)
        # arrows: from the rim down the valley to the low point
        lx, ly = PL["low"]
        for key, bend in (("fanstart", -0.12), ("valley", 0.08), ("church", 0.3)):
            sx, sy = PL[key]
            ax.annotate("", xy=(lx, ly), xytext=(sx, sy), zorder=6,
                        arrowprops=dict(arrowstyle="-|>,head_width=0.45,head_length=0.9", color=R["shed"], lw=2.4, shrinkA=4, shrinkB=10,
                                        connectionstyle=f"arc3,rad={bend}"))
        ax.scatter([lx], [ly], s=90, facecolor=R["shed"], edgecolor=R["paper"], lw=1.8, zorder=7)

        def note(num, x, y, text, ha="left", dx=0, dy=0):
            t = ax.text(x + dx, y + dy, f"{num}  {text}", fontsize=10.5, fontweight=600, color=R["ink"], ha=ha, va="center", zorder=8,
                        bbox=dict(boxstyle="round,pad=0.35", fc=R["paper"], ec=R["faint"], lw=0.8, alpha=0.93))
            return t

        nx_, ny_ = PL["north"]
        note(1, nx_, ny_ - 10, f"About {bt['radar_corrected']:.0f} inches of rain fell on all of it, most between 2 and 9 p.m.", ha="center")
        fx, fy = PL["fan"]
        note(2, fx - 40, fy - 120, "The red line: the land that drains to one place,\n31 square km (12 sq mi)", ha="center")
        note(3, (fx + lx) / 2 + 60, (fy + ly) / 2 + 70, "The old creek runs in a pipe;\nwater the pipes could not take\nran over the streets", ha="center")
        note(4, lx, ly, "The low point: Shockoe Bottom,\nnear 17th and Main", ha="left", dx=30, dy=50)
        jx, jy = PL["james"]
        note(5, jx, jy + 5, "The James stayed low, far below flood\n(14,800 cubic feet a second at 9:15 p.m.)", ha="center")
        cx, cy = PL["church"]
        note(6, cx + 140, cy - 95, "Water from Church Hill\nand the Capitol slope\nran down into the Bottom", ha="left")
        fig.text(0.015, 1 - 0.15 / fig_h, "Why Shockoe Bottom flooded in Gaston, Aug. 30, 2004", fontsize=15, fontweight=600, va="top")
        fig.text(0.015, 1 - 0.47 / fig_h, "Richmond as it stood in 2004, looking north from across the James. Hills drawn three times their height to show the bowl. "
                 "", fontsize=9.6, va="top")
        footer(fig, f"Rain: NEXRAD KAKQ (NOAA) corrected to gauges; watershed average {bt['radar_corrected']:.1f} in (range {bt['low']:.1f} to {bt['high']:.1f}). "
               "Watershed: computed from USGS 3DEP (the land surface; the city's sewershed differs). River: USGS 02037500. Pipe, slopes: news accounts "
               "(AP, 2004) in the research notes. Drawing: isoscape.", y=0.006)
        name = f"explainer-r{rnd}.png"
    p = os.path.join(out, name)
    fig.savefig(p, dpi=W / fig_w * 0.98)
    plt.close(fig)
    # keep it under 2 MB
    im = Image.open(p)
    if os.path.getsize(p) > 1.9e6:
        im.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(p, optimize=True)
    print(p, round(os.path.getsize(p) / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
