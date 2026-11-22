"""Contact sheet: every town of the editorial draw at one scale, for review (research stage).

Usage: python3 contact_sheet.py <work-dir> <pool-dir> <draw.csv> <out.png>

Rows are regions, columns size bands, as drawn. Each tile is the same 12 km square around the
town's population-weighted center, north up: roads, the built-up area (blue), the town limits
(black), and the stores (yellow with black ring; shape tells the chain). Comparison stores are
left off at this size.
"""
import json
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HALF = 6000
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
ROAD, BLUE_FILL, BLUE, YELLOW = "#c9c8c2", "#cde2fb", "#2a78d6", "#eda100"
MARK = {"Dollar General": "s", "Family Dollar": "o", "Dollar Tree": "^"}
MAIN = {"motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"}
BANDS = ["under 1,000", "1,000-2,499", "2,500-9,999", "10,000-49,999"]


def main():
    work, pool, draw_path, out = sys.argv[1:5]
    draw = pd.read_csv(draw_path)
    stores = pd.read_csv(f"{pool}/stores.csv")
    regions = list(dict.fromkeys(draw["region"]))
    fig, axes = plt.subplots(len(regions), 4, figsize=(16, 21.5), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    for _, r in draw.iterrows():
        ax = axes[regions.index(r.region), BANDS.index(r.band)]
        t = r.NAME.rsplit(" ", 1)[0].lower().replace(" ", "-")
        m = json.load(open(f"{work}/{t}/meta.json"))
        cx, cy = m["center"]
        built = gpd.read_file(f"{work}/{t}/builtup.gpkg")
        lead = built[built["setting"] == "lead"]
        place = gpd.read_file(f"{work}/{t}/place.gpkg")
        roads = gpd.read_file(f"{work}/{t}/roads.gpkg")
        ax.set_facecolor(SURFACE)
        lead.plot(ax=ax, color=BLUE_FILL, linewidth=0)
        roads[~roads.highway.isin(MAIN)].plot(ax=ax, color=ROAD, linewidth=0.35)
        roads[roads.highway.isin(MAIN)].plot(ax=ax, color=MUTED, linewidth=1.1)
        place.boundary.plot(ax=ax, color=INK, linewidth=1.0)
        st = stores[stores["town"] == t]
        for k, mk in MARK.items():
            o = st[st.kind == k]
            ax.scatter(o.x, o.y, marker=mk, s=60, fc=YELLOW, ec=INK, lw=1.3, zorder=5)
        ax.set_xlim(cx - HALF, cx + HALF)
        ax.set_ylim(cy - HALF, cy + HALF)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel("")
        ax.set_ylabel("")
        for sp in ax.spines.values():
            sp.set_color(MUTED)
        name = r.NAME.rsplit(" ", 1)[0]
        flag = " · joined to a larger urban area" if m["in_larger_urban_area"] else ""
        flag += " · drawn statewide (empty cell)" if isinstance(r.get("note"), str) else ""
        ax.set_title(f"{name}  {int(r['pop']):,}", loc="left", fontsize=10, fontweight="bold", pad=3)
        if flag:
            ax.text(0.01, 0.985, flag.strip(" ·"), transform=ax.transAxes, fontsize=6.5, color=INK2, va="top",
                    bbox=dict(fc=SURFACE, ec="none", alpha=0.85, pad=1))
    for i, reg in enumerate(regions):
        axes[i, 0].annotate(reg, (-0.06, 0.5), xycoords="axes fraction", rotation=90, ha="center", va="center",
                            fontsize=10, color=INK2)
    for j, b in enumerate(BANDS):
        axes[0, j].annotate(f"{b} people", (0.5, 1.09), xycoords="axes fraction", ha="center", fontsize=10.5, color=INK2)
    fig.suptitle("The editorial draw: 20 Virginia towns and cities, each a 12 km square at one scale",
                 x=0.02, y=0.992, ha="left", fontsize=15, fontweight="bold")
    handles = [Line2D([], [], marker=mk, ls="", mfc=YELLOW, mec=INK, mew=1.3, ms=8, label=k) for k, mk in MARK.items()]
    handles += [Patch(fc=BLUE_FILL, label="Built-up: 200+ homes per sq mi or 20% non-road paved"),
                Line2D([], [], color=INK, lw=1.0, label="Town or city limits (2024)"),
                Line2D([], [], color=MUTED, lw=1.1, label="Interstate, US and primary roads")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 0.018))
    fig.text(0.02, 0.006, "Draw: one town per region and size band, seed 20261121, from towns and cities under 50,000 "
             "(Census Vintage 2024). Stores: USDA SNAP, authorized as of 2025. Built-up: Census 2020 blocks, NLCD 2021. "
             "Roads: © OpenStreetMap contributors (ODbL). Research draft made with Claude, not affiliated with any "
             "company named.", fontsize=7, color=INK2)
    fig.subplots_adjust(left=0.04, right=0.99, top=0.94, bottom=0.05, hspace=0.12, wspace=0.04)
    fig.savefig(out, facecolor=SURFACE)


if __name__ == "__main__":
    main()
