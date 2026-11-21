"""Test maps and the score chart for the edge-of-town measures (research stage).

Usage: python3 test_maps.py <work-dir> <out-dir> <town-slug> [...]

Every map is the same 16 km square around the town's population-weighted center, north up.
Colors: neutral grays for context, blue for the built-up area, yellow with a black ring for
the three chains (shape tells them apart), black outline marks for comparison stores.
"""
import json
import os
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HALF = 8000
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8984"
GRAYS = ["#f1f0ec", "#e2e1dc", "#cfcec8"]  # housing density classes, light to dark
ROAD = "#b9b8b2"
ROAD_MAIN = "#8a8984"
BLUE = "#2a78d6"
BLUE_FILL = "#cde2fb"
YELLOW = "#eda100"
CHAIN_MARK = {"Dollar General": "s", "Family Dollar": "o", "Dollar Tree": "^"}
OTHER_MARK = {"grocery": ("D", "none", INK, 7), "pharmacy": ("P", INK2, INK2, 8),
              "convenience": ("o", MUTED, MUTED, 4)}
MAIN = {"motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                     "axes.edgecolor": INK2, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2})


def town_map(d, slug, out):
    meta = json.load(open(f"{d}/meta.json"))
    cx, cy = meta["center"]
    place = gpd.read_file(f"{d}/place.gpkg")
    blocks = gpd.read_file(f"{d}/blocks.gpkg")
    built = gpd.read_file(f"{d}/builtup.gpkg")
    ua = gpd.read_file(f"{d}/ua.gpkg")
    roads = gpd.read_file(f"{d}/roads.gpkg")
    s = pd.read_csv(f"{d}/scores.csv")

    fig, ax = plt.subplots(figsize=(8, 8.9), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    b = blocks[blocks["ALAND20"] > 0].copy()
    b["hu"] = b["HOUSING20"] / (b["ALAND20"] / 1e6)
    for (lo, hi), c in zip([(77.2, 164.1), (164.1, 1e9)], GRAYS[1:]):
        sel = b[(b["hu"] >= lo) & (b["hu"] < hi)]
        if len(sel):
            sel.plot(ax=ax, color=c, linewidth=0)
    built[built["setting"] == "lead"].plot(ax=ax, color=BLUE_FILL, alpha=0.75, linewidth=0)
    built[built["setting"] == "loose"].boundary.plot(ax=ax, color=BLUE, linewidth=1.6)
    minor = roads[~roads["highway"].isin(MAIN)]
    major = roads[roads["highway"].isin(MAIN)]
    minor.plot(ax=ax, color=ROAD, linewidth=0.5)
    major.plot(ax=ax, color=ROAD_MAIN, linewidth=1.6)
    if len(ua):
        ua.boundary.plot(ax=ax, color=INK2, linewidth=1.0, linestyle=(0, (5, 3)))
    place.boundary.plot(ax=ax, color=INK, linewidth=1.4)
    ax.plot([cx], [cy], marker="+", color=INK, markersize=14, mew=2)

    for k, (m, fc, ec, sz) in OTHER_MARK.items():
        o = s[s["kind"] == k]
        ax.scatter(o["x"], o["y"], marker=m, s=sz ** 2, facecolors=fc, edgecolors=ec,
                   linewidths=1.2, zorder=5)
    for k, m in CHAIN_MARK.items():
        o = s[s["kind"] == k]
        ax.scatter(o["x"], o["y"], marker=m, s=13 ** 2, facecolors=YELLOW, edgecolors=INK,
                   linewidths=1.8, zorder=6)
        for _, r in o.iterrows():
            if abs(r.x - cx) < HALF - 600 and abs(r.y - cy) < HALF - 400:
                ax.annotate(f'A {r.A_lead:.1f} · {r.A_loose:.1f}', (r.x, r.y), xytext=(9, -3),
                            textcoords="offset points", fontsize=7.5, color=INK, zorder=7,
                            bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.85))
    ax.set_xlim(cx - HALF, cx + HALF)
    ax.set_ylim(cy - HALF, cy + HALF)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    for sp in ax.spines.values():
        sp.set_color(MUTED)
    # scale bar, 2 km
    x0, y0 = cx - HALF + 600, cy - HALF + 600
    ax.plot([x0, x0 + 2000], [y0, y0], color=INK, linewidth=2.5)
    ax.text(x0 + 1000, y0 + 180, "2 km", ha="center", fontsize=8)
    name = place["NAMELSAD"].iloc[0]
    ax.set_title(f"{name.replace(' town', '')}, Virginia", loc="left", fontsize=14,
                 fontweight="bold", pad=22)
    ax.text(0, 1.012, f'{meta["pop_in_limits"]:,} people in the town limits (2020). '
            f'Built-up area: homes + paved {meta["builtup_km2"]["lead"]} km², homes only {meta["builtup_km2"]["loose"]} km². '
            f'Urban area: {", ".join(meta["ua"]) if meta["ua"] else "none"}.',
            transform=ax.transAxes, fontsize=7.5, color=INK2)
    handles = [
        Line2D([], [], marker="s", ls="", mfc=YELLOW, mec=INK, mew=1.5, ms=9, label="Dollar General"),
        Line2D([], [], marker="o", ls="", mfc=YELLOW, mec=INK, mew=1.5, ms=9, label="Family Dollar"),
        Line2D([], [], marker="^", ls="", mfc=YELLOW, mec=INK, mew=1.5, ms=9, label="Dollar Tree"),
        Line2D([], [], marker="D", ls="", mfc="none", mec=INK, mew=1.2, ms=6, label="Supermarket or grocery"),
        Line2D([], [], marker="P", ls="", mfc=INK2, mec=INK2, ms=7, label="Pharmacy chain"),
        Line2D([], [], marker="o", ls="", mfc=MUTED, mec=MUTED, ms=4, label="Convenience store"),
        Line2D([], [], marker="+", ls="", color=INK, ms=10, mew=2, label="Population-weighted center"),
        Line2D([], [], color=INK, lw=1.4, label="Town limits (2024)"),
        Line2D([], [], color=INK2, lw=1.0, ls=(0, (5, 3)), label="Census urban area (2020)"),
        Line2D([], [], color=BLUE, lw=1.6, label="Built-up edge, homes only"),
        Patch(fc=BLUE_FILL, ec="none", label="Built-up area, homes + paved"),
        Patch(fc=GRAYS[2], ec="none", label="425+ homes per sq mi"),
        Patch(fc=GRAYS[1], ec="none", label="200-425 homes per sq mi"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=7.2, frameon=False,
               bbox_to_anchor=(0.5, 0.045))
    fig.text(0.02, 0.012, "Labels: score A homes + paved · homes only (0 center, 1 built-up edge, above 1 beyond it). "
             "Stores: USDA SNAP retailers authorized as of 2025. Blocks: Census 2020. Non-road impervious: NLCD 2021. Roads: © OpenStreetMap contributors (ODbL). "
             "Research draft made with Claude, not affiliated with any company named.",
             fontsize=6.3, color=INK2, wrap=True)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.17)
    fig.savefig(f"{out}/map-{slug}.png", facecolor=SURFACE)
    plt.close(fig)


ROWS = ["Dollar General", "Family Dollar", "Dollar Tree", "grocery", "pharmacy", "convenience"]
LABEL = {"grocery": "Supermarket or grocery", "pharmacy": "Pharmacy chain",
         "convenience": "Convenience store"}


def score_chart(work, slugs, out):
    s = pd.concat([pd.read_csv(f"{work}/{t}/scores.csv").assign(town=t) for t in slugs])
    null = pd.concat([pd.read_csv(f"{work}/{t}/null.csv").assign(town=t) for t in slugs])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=200, sharey=True)
    fig.patch.set_facecolor(SURFACE)
    cap = 8
    rng = np.random.default_rng(1)
    for ax, col, title in [(axes[0], "A_lead", "Homes + paved (200 homes per sq mi or 20% impervious)"),
                           (axes[1], "A_loose", "Homes only (200 homes per sq mi)")]:
        ax.set_facecolor(SURFACE)
        ylab = ["Random main-road points"] + [LABEL.get(r, r) for r in ROWS][::-1]
        q = np.clip(null[col].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).values, 0, cap)
        ax.plot([q[0], q[4]], [0, 0], color=MUTED, lw=1.5)
        ax.add_patch(plt.Rectangle((q[1], -0.18), q[3] - q[1], 0.36, fc=GRAYS[2], ec=MUTED))
        ax.plot([q[2]], [0], marker="|", color=INK, ms=12, mew=2)
        for i, k in enumerate(ROWS[::-1], start=1):
            v = np.clip(s.loc[s["kind"] == k, col].values, 0, cap)
            y = i + rng.uniform(-0.15, 0.15, len(v))
            if k in CHAIN_MARK:
                ax.scatter(v, y, marker=CHAIN_MARK[k], s=70, fc=YELLOW, ec=INK, lw=1.4, zorder=3)
            else:
                m, fc, ec, sz = OTHER_MARK[k]
                ax.scatter(v, y, marker=m, s=max(sz, 6) ** 2, fc=fc, ec=ec, lw=1.2, zorder=3)
        ax.axvline(1, color=BLUE, lw=1.2)
        ax.text(1.05, len(ROWS) + 0.55, "built-up edge", color=BLUE, fontsize=8)
        ax.set_yticks(range(len(ylab)))
        ax.set_yticklabels(ylab)
        ax.set_xlim(0, cap + 0.3)
        ax.set_ylim(-0.6, len(ROWS) + 0.9)
        ax.set_xticks([0, 1, 2, 4, 6, 8])
        ax.set_xticklabels(["0", "1", "2", "4", "6", "8+"])
        ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.grid(axis="x", color="#e2e1dc", lw=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.suptitle("Where stores sit in Marion, South Hill and Chase City, by score A (test of the measure, 3 towns)",
                 x=0.01, ha="left", fontsize=11.5, fontweight="bold")
    fig.supxlabel("Score A: distance from center ÷ distance to the built-up edge on that bearing (0 center, 1 edge)",
                  x=0.58, y=0.085, fontsize=9.5, color=INK2)
    fig.text(0.01, 0.005, "Every SNAP-authorized store of these kinds within 8 km of the town limits (USDA FNS, 2025).\n"
             "Gray box: middle half of 4,000 random points on trunk, primary, secondary and tertiary roads "
             "(© OpenStreetMap contributors); whiskers 10th-90th percentile. Scores above 8 drawn at 8.",
             fontsize=6.8, color=INK2)
    fig.subplots_adjust(left=0.19, right=0.99, top=0.86, bottom=0.2, wspace=0.08)
    fig.savefig(f"{out}/scores.png", facecolor=SURFACE)
    plt.close(fig)


def main():
    work, out, slugs = sys.argv[1], sys.argv[2], sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    for t in slugs:
        town_map(f"{work}/{t}", t, out)
    score_chart(work, slugs, out)


if __name__ == "__main__":
    main()
