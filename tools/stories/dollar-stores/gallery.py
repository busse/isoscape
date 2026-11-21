"""Gallery of every edge-of-town chain store: one 3 km square per store, north up (research stage).

Usage: python3 gallery.py <work-dir> <osm-dir> <edge_points.csv> <out.png> [chain]

Each tile: the town's built-up area (blue), its limits (black), main roads (dark gray), other
roads (light), the store (yellow, black ring; shape by chain) and the town's center direction
(a small arrow at the tile edge). Caption: town, SNAP year, score A, limits in or out.
"""
import json
import math
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.geometry import LineString, box  # noqa: E402

HALF = 1500
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
ROAD, BLUE_FILL, YELLOW = "#c9c8c2", "#cde2fb", "#eda100"
MARK = {"Dollar General": "s", "Family Dollar": "o", "Dollar Tree": "^"}
MAIN = {"motorway", "trunk", "primary", "secondary", "motorway_link", "trunk_link", "primary_link"}


def roads(path, frame):
    d = json.load(open(path))
    tf = Transformer.from_crs(4326, 32617, always_xy=True)
    out = []
    for e in d["elements"]:
        if e.get("type") != "way" or len(e["geometry"]) < 2:
            continue
        g = LineString([tf.transform(q["lon"], q["lat"]) for q in e["geometry"]])
        if g.intersects(frame):
            out.append({"highway": e["tags"].get("highway"), "geometry": g})
    return gpd.GeoDataFrame(out, crs=32617)


def main():
    work, osm, pts_path, out = sys.argv[1:5]
    chains = sys.argv[5:] or list(MARK)
    p = pd.read_csv(pts_path)
    p = p[p["kind"].isin(chains)].sort_values(["kind", "A_lead"]).reset_index(drop=True)
    n = len(p)
    cols = 6
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.7, rows * 3.0 + 1.2), dpi=150)
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
        built[built["setting"] == "lead"].clip(frame).plot(ax=ax, color=BLUE_FILL, linewidth=0)
        rd = roads(f"{osm}/{r.town}.json", frame)
        if len(rd):
            rd[~rd.highway.isin(MAIN)].plot(ax=ax, color=ROAD, linewidth=0.4)
            rd[rd.highway.isin(MAIN)].plot(ax=ax, color=MUTED, linewidth=1.3)
        gpd.read_file(f"{d}/place.gpkg").boundary.clip(frame).plot(ax=ax, color=INK, linewidth=0.9)
        ax.scatter([r.x], [r.y], marker=MARK[r.kind], s=90, fc=YELLOW, ec=INK, lw=1.6, zorder=5)
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
        name = gpd.read_file(f"{d}/place.gpkg")["NAME"].iloc[0]
        yr = int(r.auth_year) if pd.notna(r.auth_year) else ""
        yr = "by 2005" if yr in (2004, 2005) else yr
        lim = "outside limits" if r.outside_limits else "inside limits"
        ax.set_title(f"{name}\n{yr} · A {r.A_lead:.2f} · {lim}", fontsize=7.2, loc="left", pad=2)
    fig.suptitle(f"Every {' / '.join(chains)} at the edge of a Virginia town or city ({n} stores, score A 1 to 2)",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.text(0.01, 0.004, "Each square is 3 km, north up; the arrow points to the town's population-weighted center. "
             "Blue: built-up (200+ homes per sq mi or 20% non-road paved). Black: town limits (2024). Stores: USDA SNAP; "
             "'by 2005' means already authorized when the file begins. Roads: © OpenStreetMap contributors (ODbL). "
             "Research draft made with Claude.", fontsize=6.5, color=INK2)
    fig.subplots_adjust(left=0.01, right=0.99, top=1 - 0.9 / (rows * 3.0 + 1.2), bottom=0.35 / (rows * 3.0 + 1.2),
                        hspace=0.32, wspace=0.05)
    fig.savefig(out, facecolor=SURFACE)


if __name__ == "__main__":
    main()
