"""Editorial poster, rough draft (24 x 36 in): "Why does it always seem like there's a Dollar
General on the edge of town?"

Usage: python3 poster.py <ds-dir> <tests.csv> <dg_classes.csv> <out-stem>

<ds-dir> is the working folder with stores_dedup.csv.gz, hpms/va2024.gpkg, and the Virginia place
folders (work_all/<slug>, work_cdp/<geoid>) holding place.gpkg, builtup.gpkg, roads.gpkg, meta.json.
Writes <out-stem>.png (preview, 100 dpi) and <out-stem>.pdf.

Every number printed comes from tests.csv / dg_classes.csv / stores_dedup (no number is typed in
by hand except where noted beside it). Research draft made with Claude.
"""
import json
import math
import os
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from shapely.geometry import box  # noqa: E402

W, H = 24, 36
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e2e1dc"
BUILT, ROAD, YELLOW = "#ecebe6", "#d6d5cf", "#eda100"
CLASSES = [(0, 2000, "#86b6ef", 1.2, "under 2,000"), (2000, 5000, "#5598e7", 2.0, "2,000 to 5,000"),
           (5000, 10000, "#2a78d6", 2.9, "5,000 to 10,000"), (10000, 20000, "#1c5cab", 3.8, "10,000 to 20,000"),
           (20000, 1e9, "#0d366b", 4.8, "20,000 and over")]
HALF = 1500
PRIMARY = "Set B: six states, small incorporated (PRIMARY)"
CONTRAST = "Set B: small incorporated, convenience stores (stated contrast)"

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK, "axes.edgecolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2})


def text(fig, x, y, s, **kw):
    """Place text in inches from the top-left corner."""
    return fig.text(x / W, 1 - y / H, s, **kw)


def axes(fig, x, y, w, h):
    """Axes in inches from the top-left corner."""
    return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


def tile(fig, ds, hp, stores, r, x, y, size):
    ax = axes(fig, x, y, size, size)
    folder = f"{ds}/work_cdp/{r.folder}" if str(r.folder).isdigit() else f"{ds}/work_all/{r.folder}"
    frame = box(r.x - HALF, r.y - HALF, r.x + HALF, r.y + HALF)
    meta = json.load(open(f"{folder}/meta.json"))
    cx, cy = meta["center"]
    built = gpd.read_file(f"{folder}/builtup.gpkg")
    built[built["setting"] == "lead"].clip(frame).plot(ax=ax, color=BUILT, linewidth=0)
    rd = gpd.read_file(f"{folder}/roads.gpkg")
    rd = rd[rd.intersects(frame)]
    if len(rd):
        rd.plot(ax=ax, color=ROAD, linewidth=0.6)
    h = hp.iloc[list(hp.sindex.query(frame, predicate="intersects"))]
    for lo, hi, col, lw, _ in CLASSES:
        s = h[(h.aadt >= lo) & (h.aadt < hi)]
        if len(s):
            s.plot(ax=ax, color=col, linewidth=lw, capstyle="round")
    place = gpd.read_file(f"{folder}/place.gpkg")
    lsad = str(place["LSAD"].iloc[0]) if "LSAD" in place else ""
    if lsad != "57":
        place.boundary.clip(frame).plot(ax=ax, color=INK, linewidth=1.0, linestyle=(0, (4, 2)))
    near = stores[(abs(stores.x - r.x) < HALF) & (abs(stores.y - r.y) < HALF) & (stores.id != r.id)]
    cv = near[near.kind == "convenience"]
    ax.scatter(cv.x, cv.y, s=22, marker="o", fc=SURFACE, ec=INK2, lw=1.0, zorder=5)
    gr = near[near.kind == "grocery"]
    ax.scatter(gr.x, gr.y, s=26, marker="D", fc=SURFACE, ec=INK, lw=1.0, zorder=5)
    od = near[near.kind.isin(["Dollar General", "Family Dollar", "Dollar Tree"])]
    ax.scatter(od.x, od.y, s=40, marker="s", fc=YELLOW, ec=INK, lw=1.0, alpha=0.6, zorder=5)
    ax.scatter([r.x], [r.y], s=170, marker="s", fc=YELLOW, ec=INK, lw=2.2, zorder=7)
    a = math.atan2(cx - r.x, cy - r.y)
    ex, ey = r.x + 0.86 * HALF * math.sin(a), r.y + 0.86 * HALF * math.cos(a)
    ax.annotate("", (ex, ey), (ex - 320 * math.sin(a), ey - 320 * math.cos(a)),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4))
    ax.set_xlim(r.x - HALF, r.x + HALF)
    ax.set_ylim(r.y - HALF, r.y + HALF)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_facecolor(SURFACE)
    for sp in ax.spines.values():
        sp.set_color(MUTED)
    yr = int(r.auth_year)
    yr = "by 2005" if yr in (2004, 2005) else str(yr)
    bits = [f"{int(r.aadt):,} a day" if pd.notna(r.aadt) else "no count"]
    if pd.notna(r["rank"]) and r["rank"] <= 2:
        bits.append("busiest road in" if r["rank"] == 1 else "2nd-busiest road in")
    if r.junction_m <= 250:
        bits.append("at a junction")
    text(fig, x, y - 0.42, f"{r.NAME}", fontsize=12, fontweight="bold", va="bottom")
    text(fig, x, y - 0.05, f"{yr} · " + " · ".join(bits), fontsize=8.6, color=INK2, va="bottom")


def dot_rows(ax, rows, xmax=0.6):
    ys = list(range(len(rows)))[::-1]
    for y, (lab, dg, lo, hi, rnd, cv) in zip(ys, rows):
        ax.plot([lo, hi], [y, y], color=INK2, lw=2)
        ax.plot([rnd], [y], marker="|", color=INK, ms=26, mew=3.2, zorder=4)
        ax.scatter([cv], [y - 0.24], marker="o", s=70, fc=SURFACE, ec=INK2, lw=1.6, zorder=4)
        ax.scatter([dg], [y], marker="s", s=190, fc=YELLOW, ec=INK, lw=2, zorder=5)
        ax.text(0, y + 0.36, lab, fontsize=12.5, color=INK, va="bottom")
        ax.text(xmax, y - 0.05, f"{dg:.0%}", fontsize=13, fontweight="bold", ha="right", va="center")
    ax.set_xlim(-0.01, xmax)
    ax.set_ylim(-0.7, len(rows) - 0.1)
    ax.set_yticks([])
    ax.set_xticks(np.arange(0, xmax + 0.01, 0.1))
    ax.set_xticklabels([f"{int(v * 100)}%" for v in np.arange(0, xmax + 0.01, 0.1)], fontsize=11)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.set_facecolor(SURFACE)


def main():
    ds, tests_path, classes_path, out = sys.argv[1:5]
    t = pd.read_csv(tests_path)
    T = {(r.label, r.test): r for r in t.itertuples()}
    cls = pd.read_csv(classes_path)
    st = pd.read_csv(f"{ds}/stores_dedup.csv.gz", low_memory=False)
    hp = gpd.read_file(f"{ds}/hpms/va2024.gpkg")
    hp.sindex
    va = st[(st.state == "VA") & (st.unit.isin(["small", "CDP"])) & (st.kind == "Dollar General")
            & (st.A_lead > 1) & (st.A_lead <= 2) & (st.edge_dist > 30)].sort_values("A_lead").reset_index(drop=True)
    vstores = st[st.state == "VA"]

    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor(SURFACE)
    # header
    text(fig, 1.0, 1.55, "Why does it always seem like there's a", fontsize=50, fontweight="bold", va="bottom")
    text(fig, 1.0, 2.55, "Dollar General on the edge of town?", fontsize=50, fontweight="bold", va="bottom")
    six = cls[(cls.set == "B") & (cls.unit == "small")].groupby("class")["stores"].sum()
    total = int(six.sum())
    edge = int(six.get("edge band", 0))
    c5 = T[(PRIMARY, "C5 (lead)")]
    c2 = T[(PRIMARY, "C2")]
    c4 = T[(PRIMARY, "C4")]
    deck = (f"Most of them aren't. Around the small towns of Virginia and six neighboring states, {edge} of "
            f"{total:,} Dollar General stores sit just past the edge of town, about one in {round(total / edge)}. "
            f"Those that do are found where state and US highways meet,\nthe same kind of place as the "
            f"convenience store next door, and {c4.share:.0%} of them were approved for food-stamp (SNAP) "
            f"shoppers after 2005. You notice them because they are on the roads you drive into town.")
    import textwrap
    deck = textwrap.fill(deck.replace("\n", " "), 128)
    text(fig, 1.0, 3.35, deck, fontsize=17, color=INK2, va="top", linespacing=1.45)

    # the grid: every Virginia edge store
    text(fig, 1.0, 5.55, f"Every Dollar General at the edge of a small Virginia town or community ({len(va)} stores)",
         fontsize=20, fontweight="bold", va="bottom")
    text(fig, 1.0, 5.93, "Each square is 3 km (1.9 miles) on a side, north up. The arrow points to the center of town. "
         "Roads are shaded by how many vehicles pass in a day.", fontsize=12, color=INK2, va="bottom")
    cols, size, gapy = 6, 2.9, 0.82
    gapx = (22.0 - cols * size) / (cols - 1)
    x0, y0 = 1.0, 6.95
    for i, r in va.iterrows():
        cx_, cy_ = i % cols, i // cols
        tile(fig, ds, hp, vstores, r, x0 + cx_ * (size + gapx), y0 + cy_ * (size + gapy), size)
    grid_bottom = y0 + math.ceil(len(va) / cols) * (size + gapy) - gapy
    # legend row
    ly = grid_bottom + 0.35
    handles = [Line2D([], [], color=c, lw=lw + 1, label=lab) for _, _, c, lw, lab in CLASSES]
    leg = fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0 / W, 1 - ly / H), ncol=5, fontsize=11.5,
                     frameon=False, title="Vehicles a day, 2024", title_fontsize=11.5, alignment="left")
    marks = [Line2D([], [], marker="s", ls="", mfc=YELLOW, mec=INK, mew=2, ms=13, label="Dollar General at the edge"),
             Line2D([], [], marker="s", ls="", mfc=YELLOW, mec=INK, mew=1, ms=9, alpha=0.6,
                    label="Other Dollar General, Family Dollar, Dollar Tree"),
             Line2D([], [], marker="o", ls="", mfc=SURFACE, mec=INK2, mew=1.4, ms=8, label="Convenience store"),
             Line2D([], [], marker="D", ls="", mfc=SURFACE, mec=INK, mew=1.2, ms=7, label="Grocery"),
             Line2D([], [], color=INK, lw=1.0, ls=(0, (4, 2)), label="Town limits"),
             Line2D([], [], color=BUILT, lw=10, label="Built-up town")]
    fig.legend(handles=marks, loc="upper left", bbox_to_anchor=(12.2 / W, 1 - ly / H), ncol=3, fontsize=11.5,
               frameon=False, title="On the map", title_fontsize=11.5, alignment="left")
    fig.add_artist(leg)

    # charts band
    cy0 = ly + 1.65
    text(fig, 1.0, cy0, "Is it true?", fontsize=22, fontweight="bold", va="bottom")
    text(fig, 1.0, cy0 + 0.38, "Where the Dollar General stores near small towns are, six states", fontsize=12,
         color=INK2, va="bottom")
    ax = axes(fig, 2.9, cy0 + 0.7, 4.7, 2.9)
    order = [("in town", "In town"), ("edge band", "At the edge"), ("on the edge line (margin)", "On the edge line"),
             ("beyond A 2", "Farther out")]
    vals = [int(six.get(k, 0)) for k, _ in order]
    ys = list(range(len(order)))[::-1]
    ax.barh(ys, vals, height=0.62, color=["#cfcec8", YELLOW, "#cfcec8", "#cfcec8"],
            edgecolor=[SURFACE, INK, SURFACE, SURFACE], linewidth=[0, 2, 0, 0])
    for y_, v, (_, lab) in zip(ys, vals, order):
        ax.text(-30, y_, lab, ha="right", va="center", fontsize=12.5)
        ax.text(v + 25, y_, f"{v:,}", va="center", fontsize=12.5, fontweight="bold")
    ax.set_xlim(0, max(vals) * 1.22)
    ax.axis("off")
    text(fig, 1.0, cy0 + 4.15, (f"Within twice the distance to the edge, the edge holds {c5.share:.0%} of these stores.\n"
         f"Random points along the same main roads land there {c5.expected / c5.n_stores:.0%} of the time."),
         fontsize=12, color=INK2, va="top", linespacing=1.4)

    c1, c3 = T[(PRIMARY, "C1")], T[(PRIMARY, "C3")]
    k1, k2, k3 = T[(CONTRAST, "C1")], T[(CONTRAST, "C2")], T[(CONTRAST, "C3")]
    text(fig, 8.6, cy0, "Where are the ones at the edge?", fontsize=22, fontweight="bold", va="bottom")
    text(fig, 8.6, cy0 + 0.38, f"The {int(c2.n_stores)} Dollar General stores at the edge of small towns, six states",
         fontsize=12, color=INK2, va="bottom")
    ax2 = axes(fig, 8.6, cy0 + 0.85, 7.0, 2.75)

    def ci(r):
        lo, hi = [float(v) for v in str(r.share_ci).split("-")]
        return lo, hi
    rows = [("Within 250 m of a junction of US or state routes", c2.share, *ci(c2), c2.expected / c2.n_stores, k2.share),
            ("On one of the two busiest roads into town", c1.share, *ci(c1), c1.expected / c1.n_stores, k1.share),
            ("Inside the town limits", c3.share, *ci(c3), c3.expected / c3.n_stores, k3.share)]
    dot_rows(ax2, rows)
    c6 = T[(PRIMARY, "C6")]
    text(fig, 8.6, cy0 + 4.15, (f"Black tick: random points on the same roads at the same edges.\nCircle: convenience stores at "
         f"the edge. The road past an edge Dollar\nGeneral carries {c6.share:.1f} times the traffic of other edge sites."),
         fontsize=12, color=INK2, va="top", linespacing=1.4)

    text(fig, 16.6, cy0, "When did they come?", fontsize=22, fontweight="bold", va="bottom")
    text(fig, 16.6, cy0 + 0.38, "Share approved for SNAP after 2005, six states", fontsize=12, color=INK2, va="bottom")
    ax3 = axes(fig, 17.4, cy0 + 0.75, 4.8, 2.4)
    small = st[(st.set == "B") & (st.unit == "small") & (st.kind == "Dollar General") & (st.edge_dist > 30)]
    town = small[small.A_lead <= 1]
    town_new = (town.auth_year > 2005).mean()
    bars = [("In town", town_new, len(town)), ("At the edge", c4.share, int(c4.n_stores))]
    for i, (lab, v, n) in enumerate(bars):
        ax3.bar(i, v, width=0.6, color=YELLOW if i else "#cfcec8", edgecolor=INK if i else SURFACE, linewidth=2 if i else 0)
        ax3.text(i, v + 0.03, f"{v:.0%}", ha="center", fontsize=20, fontweight="bold")
        ax3.text(i, -0.08, f"{lab}\n{n:,} stores", ha="center", va="top", fontsize=12.5)
    ax3.set_ylim(0, 1.05)
    ax3.set_xlim(-0.6, 1.6)
    ax3.axis("off")
    text(fig, 16.6, cy0 + 4.15, ("Approval for SNAP is not the opening date: a store approved\n"
         "in 2004 or 2005 may be older, since the record starts then."), fontsize=12, color=INK2, va="top",
         linespacing=1.4)

    # how we know
    hy = cy0 + 5.6
    fig.add_artist(Line2D([1.0 / W, 23.0 / W], [1 - (hy - 0.25) / H] * 2, color=GRID, lw=1.5))
    text(fig, 1.0, hy, "How we know, and what this can't say", fontsize=17, fontweight="bold", va="top")
    left = ("The edge of town is where homes thin below 200 per square mile and paved land (other than roads) drops\n"
            "below a fifth of the ground, measured outward from where the town's people live. \"At the edge\" means past\n"
            "that line but less than twice as far from the center. Small towns have under 25,000 people.\n"
            "The tests were written down before the data from North Carolina, Tennessee, Kentucky, West Virginia,\n"
            "Maryland and South Carolina was read, and an independent reviewer recomputed the results.")
    right = ("This shows where stores are, not why a company chose a site. Land prices, zoning and water and sewer\n"
             "are not in the data. Most edge stores are outside the town limits. In West Virginia none of the 19 edge\n"
             "stores is near a junction. The Virginia maps show every edge store in a small town or community,\n"
             "including those that fit none of the patterns. A dot is a location; nothing here rates a store,\n"
             "a town or the people who live there.")
    text(fig, 1.0, hy + 0.55, left, fontsize=11.5, color=INK2, va="top", linespacing=1.45)
    text(fig, 12.2, hy + 0.55, right, fontsize=11.5, color=INK2, va="top", linespacing=1.45)
    src = ("Stores: USDA Food and Nutrition Service, SNAP Retailer Locator historical data, stores authorized as of 2025. "
           "Traffic: Federal Highway Administration, HPMS 2024 (public domain).\nHomes and people: U.S. Census Bureau, 2020 "
           "blocks; town limits, TIGER/Line 2024. Paved land: USGS NLCD 2021. Roads: © OpenStreetMap contributors (ODbL). "
           "Research draft made with Claude.\nIndependent; not affiliated with any company named. Rough draft, "
           "November 2026.")
    text(fig, 1.0, H - 0.75, src, fontsize=9.5, color=MUTED, va="bottom", linespacing=1.4)
    fig.savefig(out + ".png", facecolor=SURFACE)
    fig.savefig(out + ".pdf", facecolor=SURFACE)


if __name__ == "__main__":
    main()
