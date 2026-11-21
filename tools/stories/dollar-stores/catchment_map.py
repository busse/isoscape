"""Map of Dollar General catchments by road in named counties (research stage).

Usage: python3 catchment_map.py <catchment-out-dir> <raw-dir> <out.png> <COUNTYFP> [...]
"""
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
GRAYS = ["#e2e1dc", "#cfcec8"]
YELLOW, BLUE = "#eda100", "#2a78d6"
MAIN = {"trunk", "primary", "secondary"}
OFFSET = {"Hartfield": (-125, -32), "Deltaville": (12, 8), "Topping": (10, 10)}  # label placement, points


def main():
    d, raw, out, fips = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    blocks = gpd.read_file(f"{d}/blocks.gpkg")
    c = pd.read_csv(f"{d}/catchments.csv")
    roads = gpd.read_file(f"{d}/roads.gpkg")
    gro = gpd.read_file(f"{d}/grocery.gpkg")
    dg = gpd.read_file(f"{d}/dg.gpkg")
    focus = blocks[blocks["COUNTYFP20"].isin(fips)]
    x0, y0, x1, y1 = focus.total_bounds
    pad = 2500
    fig, ax = plt.subplots(figsize=(9, 9.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor("#eef3f8")  # water and everything without a land block
    land = blocks.dissolve()
    land.plot(ax=ax, color=SURFACE, linewidth=0)
    b = blocks.copy()
    b["hu"] = b["HOUSING20"] / (b["ALAND20"] / 1e6)
    b[(b["hu"] >= 77.2) & (b["hu"] < 164.1)].plot(ax=ax, color=GRAYS[0], linewidth=0)
    b[b["hu"] >= 164.1].plot(ax=ax, color=GRAYS[1], linewidth=0)
    # only the edges two stores' areas share; the shoreline is not an edge between stores
    areas = blocks[blocks["store"] >= 0].dissolve("store").geometry
    edges = []
    keys = list(areas.index)
    for i, a in enumerate(keys):
        for b_ in keys[i + 1:]:
            if areas[a].distance(areas[b_]) < 1:
                edges.append(areas[a].boundary.intersection(areas[b_].buffer(2)))
    gpd.GeoSeries(edges, crs=blocks.crs).plot(ax=ax, color=BLUE, linewidth=1.3)
    roads[~roads["highway"].isin(MAIN)].plot(ax=ax, color="#c9c8c2", linewidth=0.35)
    roads[roads["highway"].isin(MAIN)].plot(ax=ax, color=MUTED, linewidth=1.4)
    cty = blocks.dissolve("COUNTYFP20").geometry
    cedges = [cty[a].boundary.intersection(cty[b_].buffer(2)) for i, a in enumerate(cty.index)
              for b_ in list(cty.index)[i + 1:] if cty[a].distance(cty[b_]) < 1]
    gpd.GeoSeries(cedges, crs=blocks.crs).plot(ax=ax, color=INK, linewidth=0.9, linestyle=(0, (6, 3)))
    ax.scatter(gro.geometry.x, gro.geometry.y, marker="D", s=34, facecolors=SURFACE, edgecolors=INK, lw=1.2, zorder=9)
    other = dg[~dg["County"].isin(c["county"].unique())]
    ax.scatter(other.geometry.x, other.geometry.y, marker="s", s=70, fc=YELLOW, ec=INK, lw=1.0, alpha=0.55, zorder=5)
    for _, r in c.iterrows():
        ax.plot([r.x, r.center_x], [r.y, r.center_y], color=INK, lw=0.8, ls=(0, (2, 2)), zorder=6)
        ax.scatter([r.center_x], [r.center_y], marker="o", s=55, fc=SURFACE, ec=BLUE, lw=1.8, zorder=7)
        ax.scatter([r.x], [r.y], marker="s", s=150, fc=YELLOW, ec=INK, lw=1.8, zorder=8)
        yr = r.authorized.split("/")[-1]
        ax.annotate(f"{r.place} {yr}\n{r.catch_people:,} people · grocery {r.nearest_grocery_road_m / 1000:.1f} km",
                    (r.x, r.y), xytext=OFFSET.get(r.place, (10, 6)), textcoords="offset points", fontsize=7.2, zorder=9,
                    bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none", alpha=0.9))
    ax.set_xlim(x0 - pad, x1 + pad)
    ax.set_ylim(y0 - pad, y1 + pad)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    sx, sy = x0 - pad + 1500, y0 - pad + 1500
    ax.plot([sx, sx + 5000], [sy, sy], color=INK, lw=2.5)
    ax.text(sx + 2500, sy + 500, "5 km", ha="center", fontsize=8)
    ax.set_title("Mathews and Middlesex: who lives nearest each Dollar General, by road", loc="left",
                 fontsize=13, fontweight="bold", pad=20)
    ax.text(0, 1.012, "Each blue outline holds the 2020 Census blocks whose nearest Dollar General by road is the store "
            "inside it. Open circle: that area's population center.", transform=ax.transAxes, fontsize=7.4, color=INK2)
    handles = [
        Line2D([], [], marker="s", ls="", mfc=YELLOW, mec=INK, mew=1.5, ms=9, label="Dollar General (label: year authorized for SNAP)"),
        Line2D([], [], marker="s", ls="", mfc=YELLOW, mec=INK, mew=1, ms=8, alpha=0.55, label="Dollar General in a neighboring county"),
        Line2D([], [], marker="o", ls="", mfc=SURFACE, mec=BLUE, mew=1.8, ms=7, label="Population center of the store's area"),
        Line2D([], [], marker="D", ls="", mfc="none", mec=INK, mew=1.2, ms=6, label="Supermarket or grocery"),
        Line2D([], [], color=BLUE, lw=1.3, label="Edge between stores' areas, by road"),
        Line2D([], [], color=MUTED, lw=1.4, label="Primary and secondary roads"),
        Line2D([], [], color=INK, lw=0.9, ls=(0, (6, 3)), label="County line"),
        Patch(fc=GRAYS[1], label="425+ homes per sq mi"), Patch(fc=GRAYS[0], label="200-425 homes per sq mi"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=7, frameon=False, bbox_to_anchor=(0.5, 0.04))
    fig.text(0.02, 0.012, "Stores: USDA SNAP retailers authorized as of 2025; the year is SNAP authorization, not opening "
             "(2004-05 dates mean 'by then'). Blocks: Census 2020. Roads: © OpenStreetMap contributors (ODbL). "
             "Grocery distance by road. Research draft made with Claude, not affiliated with any company named.",
             fontsize=6.2, color=INK2, wrap=True)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.15)
    fig.savefig(out, facecolor=SURFACE)


if __name__ == "__main__":
    main()
