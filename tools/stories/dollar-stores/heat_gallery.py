"""Traffic heat map gallery: each edge store's 3 km square with roads shaded by daily traffic.

Usage: python3 heat_gallery.py <work-dir> <osm-dir> <hpms.gpkg> <traffic_points.csv> <out.png> [towns|all]

Roads with an HPMS 2024 count are drawn in a one-hue blue ramp and widen with traffic (classes
below); roads without a count are thin light gray from OpenStreetMap. The built-up area is a
light warm gray, the town limits black, the store yellow with a black ring.
Ramp validated with the dataviz skill's validator (--ordinal, light mode): pass.
"""
import json
import math
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.geometry import LineString, box  # noqa: E402

HALF = 1500
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
ROAD, BUILT, YELLOW = "#d6d5cf", "#ecebe6", "#eda100"
CLASSES = [(0, 2000, "#86b6ef", 1.0, "under 2,000"), (2000, 5000, "#5598e7", 1.6, "2,000-5,000"),
           (5000, 10000, "#2a78d6", 2.3, "5,000-10,000"), (10000, 20000, "#1c5cab", 3.1, "10,000-20,000"),
           (20000, 1e9, "#0d366b", 4.0, "20,000 and over")]


def osm_roads(path, frame):
    d = json.load(open(path))
    tf = Transformer.from_crs(4326, 32617, always_xy=True)
    out = []
    for e in d["elements"]:
        if e.get("type") != "way" or len(e["geometry"]) < 2:
            continue
        g = LineString([tf.transform(q["lon"], q["lat"]) for q in e["geometry"]])
        if g.intersects(frame):
            out.append(g)
    return gpd.GeoSeries(out, crs=32617)


def main():
    work, osm, hp_path, pts_path, out = sys.argv[1:6]
    scope = sys.argv[6] if len(sys.argv) > 6 else "towns"
    hp = gpd.read_file(hp_path)
    p = pd.read_csv(pts_path)
    p = p[p.kind == "Dollar General"]
    if scope == "towns":
        p = p[p.is_town]
    p = p.sort_values("A_lead").reset_index(drop=True)
    n = len(p)
    cols = 6 if n > 20 else 5 if n > 12 else 4
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.9, rows * 3.15 + 2.2), dpi=170)
    fig.patch.set_facecolor(SURFACE)
    axes = axes.ravel()
    for ax in axes[n:]:
        ax.axis("off")
    for i, r in p.iterrows():
        ax = axes[i]
        d = f"{work}/{r.town}"
        m = json.load(open(f"{d}/meta.json"))
        cx, cy = m["center"]
        frame = box(r.x - HALF, r.y - HALF, r.x + HALF, r.y + HALF)
        built = gpd.read_file(f"{d}/builtup.gpkg")
        built[built["setting"] == "lead"].clip(frame).plot(ax=ax, color=BUILT, linewidth=0)
        osm_roads(f"{osm}/{r.town}.json", frame).plot(ax=ax, color=ROAD, linewidth=0.5)
        h = hp[hp.intersects(frame)]
        for lo, hi, col, lw, _ in CLASSES:
            s = h[(h.aadt >= lo) & (h.aadt < hi)]
            if len(s):
                s.plot(ax=ax, color=col, linewidth=lw, capstyle="round")
        place = gpd.read_file(f"{d}/place.gpkg")
        place.boundary.clip(frame).plot(ax=ax, color=INK, linewidth=0.9, linestyle=(0, (4, 2)))
        ax.scatter([r.x], [r.y], marker="s", s=95, fc=YELLOW, ec=INK, lw=1.7, zorder=6)
        a = math.atan2(cx - r.x, cy - r.y)
        ex, ey = r.x + 0.86 * HALF * math.sin(a), r.y + 0.86 * HALF * math.cos(a)
        ax.annotate("", (ex, ey), (ex - 300 * math.sin(a), ey - 300 * math.cos(a)),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2))
        ax.set_xlim(r.x - HALF, r.x + HALF)
        ax.set_ylim(r.y - HALF, r.y + HALF)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel("")
        ax.set_ylabel("")
        for sp in ax.spines.values():
            sp.set_color(MUTED)
        yr = int(r.auth_year)
        yr = "by 2005" if yr in (2004, 2005) else str(yr)
        cnt = f"{int(r.aadt):,} a day" if pd.notna(r.aadt) else "no count"
        rank = ""
        if pd.notna(r.busiest_rank):
            rank = " · busiest road in" if r.busiest_rank == 1 else " · 2nd-busiest road in" if r.busiest_rank == 2 else ""
        ax.set_title(f"{place['NAME'].iloc[0]} · {yr}\n{cnt}{rank}", fontsize=7.6, loc="left", pad=2)
    what = "town" if scope == "towns" else "town or city"
    fig.suptitle(f"The road past every Dollar General at the edge of a Virginia {what} ({n} stores)",
                 x=0.01, ha="left", fontsize=12.5, fontweight="bold")
    handles = [Line2D([], [], color=c, lw=lw + 0.5, label=lab) for _, _, c, lw, lab in CLASSES]
    handles += [Line2D([], [], marker="s", ls="", mfc=YELLOW, mec=INK, mew=1.5, ms=8, label="Dollar General"),
                Line2D([], [], color=INK, lw=0.9, ls=(0, (4, 2)), label="Town limits (2024)")]
    fig.legend(handles=handles, loc="lower center", ncol=7, fontsize=7.5, frameon=False,
               title="Average vehicles a day, 2024", title_fontsize=7.5, bbox_to_anchor=(0.5, 0.035))
    fig.text(0.01, 0.004, "Each square is 3 km, north up; the arrow points to the town's population-weighted center. "
             "Traffic: FHWA HPMS 2024 (public domain), counts reported by VDOT. Gray fill: built-up area.\nStores: USDA SNAP; "
             "'by 2005' means already authorized when the file begins. Other roads © OpenStreetMap contributors (ODbL). "
             "Research draft made with Claude, not affiliated with any company named.", fontsize=6.3, color=INK2)
    fig.subplots_adjust(left=0.01, right=0.99, top=1 - 0.75 / (rows * 3.15 + 2.2), bottom=1.55 / (rows * 3.15 + 2.2),
                        hspace=0.3, wspace=0.05)
    fig.savefig(out, facecolor=SURFACE)


if __name__ == "__main__":
    main()
