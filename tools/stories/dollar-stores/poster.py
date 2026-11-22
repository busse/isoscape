"""Editorial poster (24 x 36 in): "Why does it always seem like there's a Dollar General on the edge
of town?" Working draft d2.

Usage: python3 poster.py <ds-dir> <tests.csv> <dg_classes.csv> <out-stem>

<ds-dir> is the working folder with stores_dedup.csv.gz, hpms/va2024.gpkg, counties/va_regions.gpkg
(Virginia counties and cities tagged with the five regions of regions.json), fonts/ (the print's
Libre Baskerville, converted from tools/print/fonts to TTF), and the Virginia place folders
(work_all/<slug>, work_cdp/<geoid>) holding place.gpkg, builtup.gpkg, roads.gpkg, meta.json.
Writes <out-stem>.png (preview, 100 dpi) and <out-stem>.pdf.

Every number printed comes from tests.csv / dg_classes.csv / stores_dedup; none is typed in.
The 234 and 2,078 and every chart are the six other states (set B), never Virginia; the grid is
Virginia. Made with Claude.
"""
import json
import math
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager, patheffects  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from PIL import ImageFont  # noqa: E402
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
# West to east. Short names are what the grid and the locator print.
REGIONS = [("Southwest", "Southwest"), ("Valley and Blue Ridge", "Valley and Blue Ridge"),
           ("Piedmont and Southside", "Piedmont and Southside"), ("Urban crescent", "Urban crescent"),
           ("Northern Neck, Middle Peninsula and Eastern Shore", "Northern Neck, Middle Peninsula and Eastern Shore")]
REGION_FILL = ["#e6e4de", "#d7d5ce", "#e6e4de", "#d7d5ce", "#e6e4de"]

FONTS = {}


def setup_fonts(ds):
    for k, v in {"regular": "400-normal", "bold": "700-normal", "italic": "400-italic"}.items():
        p = f"{ds}/fonts/libre-baskerville-latin-{v}.ttf"
        font_manager.fontManager.addfont(p)
        FONTS[k] = p
    plt.rcParams.update({"font.family": "Libre Baskerville", "text.color": INK, "axes.edgecolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2})


def wrap(s, width_in, size, kind="regular"):
    """Wrap s to width_in inches at size points, measured in the poster's own font."""
    f = ImageFont.truetype(FONTS[kind], 100)
    lines = []
    for para in s.split("\n"):
        line = ""
        for word in para.split():
            trial = f"{line} {word}".strip()
            if f.getlength(trial) * size / 100 / 72 > width_in and line:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return "\n".join(lines)


def text(fig, x, y, s, **kw):
    """Place text in inches from the top-left corner."""
    return fig.text(x / W, 1 - y / H, s, **kw)


def para(fig, x, y, s, width, size, **kw):
    kw.setdefault("color", INK2)
    kw.setdefault("linespacing", 1.5)
    return text(fig, x, y, wrap(s, width, size), fontsize=size, va="top", **kw)


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
    bits = [f"{int(r.aadt):,} vehicles a day" if pd.notna(r.aadt) else "no traffic count"]
    if pd.notna(r["rank"]) and r["rank"] <= 2:
        bits.append("busiest road in" if r["rank"] == 1 else "2nd-busiest road in")
    if r.junction_m <= 250:
        bits.append("at a junction")
    text(fig, x, y - 0.40, f"{r.label}", fontsize=12, fontweight="bold", va="bottom")
    text(fig, x, y - 0.07, f"{yr} · " + " · ".join(bits), fontsize=7.6, color=INK2, va="bottom")


def locator(fig, counties, va, x, y, w):
    """Virginia by region, with the grid's stores."""
    b = counties.total_bounds
    h = w * (b[3] - b[1]) / (b[2] - b[0])
    ax = axes(fig, x, y, w, h)
    for i, (key, short) in enumerate(REGIONS):
        part = counties[counties.region == key]
        part.plot(ax=ax, color=REGION_FILL[i], edgecolor=SURFACE, linewidth=0.4)
        part.dissolve().boundary.plot(ax=ax, color=INK2, linewidth=0.9)
    ax.scatter(va.x, va.y, s=46, marker="s", fc=YELLOW, ec=INK, lw=1.3, zorder=5)
    spots = {"Southwest": (0.13, 0.24), "Valley and Blue Ridge": (0.40, 0.72),
             "Piedmont and Southside": (0.52, 0.08), "Urban crescent": (0.88, 0.90),
             "Northern Neck, Middle Peninsula and Eastern Shore": (0.885, 0.56)}
    halo = [patheffects.withStroke(linewidth=4, foreground=SURFACE)]
    key = []
    for i, (k, short) in enumerate(REGIONS):
        sx, sy = spots[k]
        ax.text(sx, sy, str(i + 1), transform=ax.transAxes, fontsize=14, fontweight="bold", ha="center",
                va="center", color=INK, path_effects=halo, zorder=8)
        n = int((va.region == k).sum())
        key.append(f"{i + 1}  {short} ({n})")
    text(fig, x, y + h + 0.3, "\n".join(key), fontsize=10, color=INK2, va="top", linespacing=1.45)
    ax.set_xlim(b[0], b[2])
    ax.set_ylim(b[1], b[3])
    ax.set_aspect("equal")
    ax.axis("off")
    return h


def dot_rows(ax, rows, xmax=0.6):
    ys = list(range(len(rows)))[::-1]
    for y, (lab, dg, lo, hi, rnd, cv) in zip(ys, rows):
        ax.plot([lo, hi], [y, y], color=INK2, lw=2)
        ax.plot([rnd], [y], marker="|", color=INK, ms=26, mew=3.2, zorder=4)
        ax.scatter([cv], [y - 0.24], marker="o", s=70, fc=SURFACE, ec=INK2, lw=1.6, zorder=4)
        ax.scatter([dg], [y], marker="s", s=190, fc=YELLOW, ec=INK, lw=2, zorder=5)
        ax.text(0, y + 0.36, lab, fontsize=11.5, color=INK, va="bottom")
        ax.text(xmax, y - 0.05, f"{dg:.0%}", fontsize=13, fontweight="bold", ha="right", va="center")
    ax.set_xlim(-0.01, xmax)
    ax.set_ylim(-0.7, len(rows) - 0.1)
    ax.set_yticks([])
    ax.set_xticks(np.arange(0, xmax + 0.01, 0.1))
    ax.set_xticklabels([f"{int(v * 100)}%" for v in np.arange(0, xmax + 0.01, 0.1)], fontsize=10.5)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.set_facecolor(SURFACE)


def main():
    ds, tests_path, classes_path, out = sys.argv[1:5]
    setup_fonts(ds)
    t = pd.read_csv(tests_path)
    T = {(r.label, r.test): r for r in t.itertuples()}
    cls = pd.read_csv(classes_path)
    st = pd.read_csv(f"{ds}/stores_dedup.csv.gz", low_memory=False)
    hp = gpd.read_file(f"{ds}/hpms/va2024.gpkg")
    hp.sindex
    counties = gpd.read_file(f"{ds}/counties/va_regions.gpkg").to_crs(hp.crs)
    va = st[(st.state == "VA") & (st.unit.isin(["small", "CDP"])) & (st.kind == "Dollar General")
            & (st.A_lead > 1) & (st.A_lead <= 2) & (st.edge_dist > 30)].copy()
    pts = gpd.GeoDataFrame(va, geometry=gpd.points_from_xy(va.x, va.y), crs=hp.crs)
    va["region"] = gpd.sjoin(pts, counties[["region", "geometry"]], predicate="within", how="left")["region"].values
    assert va.region.notna().all(), "a grid store fell outside every region"
    order = {k: i for i, (k, _) in enumerate(REGIONS)}
    va = va.sort_values(["region", "x"], key=lambda c: c.map(order) if c.name == "region" else c).reset_index(drop=True)
    vstores = st[st.state == "VA"]
    # two stores at one town's edge: name the side of town each is on
    va["label"] = va["NAME"]
    for name, g in va.groupby("NAME"):
        if len(g) > 1:
            for i, r in g.iterrows():
                a = math.degrees(math.atan2(r.x - r.center_x, r.y - r.center_y)) % 360
                side = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"][int((a + 22.5) // 45) % 8]
                va.loc[i, "label"] = f"{name}, {side} side"

    six = cls[(cls.set == "B") & (cls.unit == "small")].groupby("class")["stores"].sum()
    total = int(six.sum())
    edge = int(six.get("edge band", 0))
    c1, c2, c3, c4, c5, c6 = (T[(PRIMARY, k)] for k in ("C1", "C2", "C3", "C4", "C5 (lead)", "C6"))
    k1, k2, k3 = T[(CONTRAST, "C1")], T[(CONTRAST, "C2")], T[(CONTRAST, "C3")]
    junction_x = c2.share / (c2.expected / c2.n_stores)
    small = st[(st.set == "B") & (st.unit == "small") & (st.kind == "Dollar General") & (st.edge_dist > 30)]
    town = small[small.A_lead <= 1]
    town_new = (town.auth_year > 2005).mean()

    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor(SURFACE)

    # header: the question, the answer, and where the grid's stores are
    text(fig, 1.0, 1.55, "Why does it always seem like there's a", fontsize=52, fontweight="bold", va="bottom")
    text(fig, 1.0, 2.55, "Dollar General on the edge of town?", fontsize=52, fontweight="bold", va="bottom")
    deck = (f"Most Dollar General stores near small towns are in town. We counted every Dollar General near a "
            f"small town in six states that border or sit close to Virginia. Of the {total:,} stores, {edge} stand "
            f"just outside the built-up part of town, about one in {round(total / edge)}. Those {edge} tend to be on "
            f"the busier roads coming in. About one in {round(1 / c2.share)} is within 800 feet of a spot where two "
            f"US or state highways cross. That is roughly {junction_x:.0f} times what we would expect if the stores "
            f"had been scattered at random along the same roads. Convenience stores do the same thing. "
            f"The edge stores are also newer. Of the {edge}, {c4.share:.0%} were first approved to take SNAP "
            f"benefits after 2005, compared with {town_new:.0%} of the stores in town. These are the roads people "
            f"use to get into town, which may be why the edge stores seem so common.")
    deck_lines = wrap(deck, 15.0, 15).count("\n") + 1
    para(fig, 1.0, 3.2, deck, 15.0, 15)
    counties_b = counties.total_bounds
    lx, lw = 16.9, 6.1
    text(fig, lx, 0.95, "The 30 Virginia stores on this poster", fontsize=12.5, fontweight="bold", va="bottom")
    lh = locator(fig, counties, va, lx, 1.15, lw)
    del counties_b

    # the grid: every Virginia edge store, by region, west to east
    gy = max(3.2 + deck_lines * 15 * 1.5 / 72 + 1.0, 1.15 + lh + 1.3)
    text(fig, 1.0, gy, f"Every Dollar General at the edge of a small Virginia town or community ({len(va)} stores)",
         fontsize=20, fontweight="bold", va="bottom")
    para(fig, 1.0, gy + 0.18, ("Each map is 3 km (1.9 miles) across, with north at the top. The yellow square is "
                               "the store, and the arrow points toward the middle of town. The maps are grouped "
                               "by region and run from west to east."), 22, 12)
    cols, size, gapy = 6, 2.55, 1.1
    gapx = (22.0 - cols * size) / (cols - 1)
    x0, y0 = 1.0, gy + 1.62
    for i, r in va.iterrows():
        cx_, cy_ = i % cols, i // cols
        tile(fig, ds, hp, vstores, r, x0 + cx_ * (size + gapx), y0 + cy_ * (size + gapy), size)
    # region bars: a rule over each run of tiles that share a row and a region, named once per run
    nrows = math.ceil(len(va) / cols)
    for row in range(nrows):
        idx = list(range(row * cols, min((row + 1) * cols, len(va))))
        runs, start = [], idx[0]
        for a_, b_ in zip(idx, idx[1:] + [None]):
            if b_ is None or va.region[b_] != va.region[a_]:
                runs.append((start, a_))
                start = b_
        for s_, e_ in runs:
            ry = y0 + row * (size + gapy) - 0.74
            xa = x0 + (s_ % cols) * (size + gapx)
            xb = x0 + (e_ % cols) * (size + gapx) + size
            fig.add_artist(Line2D([xa / W, xb / W], [1 - ry / H] * 2, color=INK2, lw=1.2))
            k = [i for i, (key, _) in enumerate(REGIONS) if key == va.region[s_]][0]
            cont = s_ % cols == 0 and s_ > 0 and va.region[s_ - 1] == va.region[s_]
            text(fig, xa, ry - 0.05, f"{k + 1}  {REGIONS[k][1].upper()}" + ("  (continued)" if cont else ""),
                 fontsize=9.5, color=INK2, va="bottom")
    grid_bottom = y0 + nrows * (size + gapy) - gapy

    # legend row
    ly = grid_bottom + 0.3
    handles = [Line2D([], [], color=c, lw=lw + 1, label=lab) for _, _, c, lw, lab in CLASSES]
    leg = fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.0 / W, 1 - ly / H), ncol=5, fontsize=11,
                     frameon=False, title="Vehicles on an average day, 2024", title_fontsize=11, alignment="left")
    marks = [Line2D([], [], marker="s", ls="", mfc=YELLOW, mec=INK, mew=2, ms=13, label="Dollar General at the edge"),
             Line2D([], [], marker="s", ls="", mfc=YELLOW, mec=INK, mew=1, ms=9, alpha=0.6,
                    label="Other Dollar General, Family Dollar, Dollar Tree"),
             Line2D([], [], marker="o", ls="", mfc=SURFACE, mec=INK2, mew=1.4, ms=8, label="Convenience store"),
             Line2D([], [], marker="D", ls="", mfc=SURFACE, mec=INK, mew=1.2, ms=7, label="Grocery"),
             Line2D([], [], color=INK, lw=1.0, ls=(0, (4, 2)), label="Town limits"),
             Line2D([], [], color=BUILT, lw=10, label="Built-up town")]
    fig.legend(handles=marks, loc="upper left", bbox_to_anchor=(12.6 / W, 1 - ly / H), ncol=3, fontsize=11,
               frameon=False, title="On the maps", title_fontsize=11, alignment="left")
    fig.add_artist(leg)

    # charts band: the six other states, where the tests were run
    cy0 = ly + 1.55
    para(fig, 1.0, cy0 - 0.55, ("We first saw this in Virginia. To check it wasn't a fluke, we wrote the tests down ahead "
                                 "of time and ran them on North Carolina, Tennessee, Kentucky, West Virginia, "
                                 "Maryland and South Carolina."),
         22, 12.5, color=INK)
    cy0 += 0.55
    text(fig, 1.0, cy0, "Where the stores are", fontsize=21, fontweight="bold", va="bottom")
    text(fig, 1.0, cy0 + 0.36, "Dollar Generals near small towns in the six states", fontsize=11.5,
         color=INK2, va="bottom")
    ax = axes(fig, 2.9, cy0 + 0.65, 4.5, 2.7)
    order_ = [("in town", "In town"), ("edge band", "At the edge"), ("on the edge line (margin)", "On the edge line"),
              ("beyond A 2", "Farther out")]
    vals = [int(six.get(k, 0)) for k, _ in order_]
    ys = list(range(len(order_)))[::-1]
    ax.barh(ys, vals, height=0.62, color=["#cfcec8", YELLOW, "#cfcec8", "#cfcec8"],
            edgecolor=[SURFACE, INK, SURFACE, SURFACE], linewidth=[0, 2, 0, 0])
    for y_, v, (_, lab) in zip(ys, vals, order_):
        ax.text(-30, y_, lab, ha="right", va="center", fontsize=11.5)
        ax.text(v + 25, y_, f"{v:,}", va="center", fontsize=12, fontweight="bold")
    ax.set_xlim(0, max(vals) * 1.22)
    ax.axis("off")
    para(fig, 1.0, cy0 + 3.6, (f"If the stores had been dropped at random spots along the same main roads, about "
                               f"{c5.expected / c5.n_stores:.0%} of those within twice the distance to the edge "
                               f"would have landed in the edge band. Only {c5.share:.0%} did. The edge actually has "
                               f"fewer Dollar Generals than chance would give it."),
         6.7, 11)

    text(fig, 8.6, cy0, "What the edge stores sit next to", fontsize=21, fontweight="bold", va="bottom")
    text(fig, 8.6, cy0 + 0.36, f"The {int(c2.n_stores)} Dollar Generals at the edge of a small town",
         fontsize=11.5, color=INK2, va="bottom")
    ax2 = axes(fig, 8.6, cy0 + 0.8, 7.0, 2.6)

    def ci(r):
        lo, hi = [float(v) for v in str(r.share_ci).split("-")]
        return lo, hi
    rows = [("Within 250 m (about 800 ft) of a crossing of two US or state highways", c2.share, *ci(c2),
             c2.expected / c2.n_stores, k2.share),
            ("On one of the two busiest roads into town", c1.share, *ci(c1), c1.expected / c1.n_stores, k1.share),
            ("Inside the town limits", c3.share, *ci(c3), c3.expected / c3.n_stores, k3.share)]
    dot_rows(ax2, rows)
    para(fig, 8.6, cy0 + 3.85, (f"Yellow squares show the edge Dollar Generals, with a gray line for the margin of "
                                f"error. Black ticks show what random spots on the same roads at the same edges "
                                f"would give. Open circles show convenience stores at the edge, which land in "
                                f"nearly the same places. On average, the road in front of an edge Dollar General "
                                f"also carries about {c6.share:.1f} times as much traffic as those random spots."), 7.4, 11)

    text(fig, 16.6, cy0, "How new the stores are", fontsize=21, fontweight="bold", va="bottom")
    text(fig, 16.6, cy0 + 0.36, "Share first approved to accept SNAP after 2005", fontsize=11.5, color=INK2,
         va="bottom")
    ax3 = axes(fig, 17.4, cy0 + 0.7, 4.8, 2.3)
    bars = [("In town", town_new, len(town)), ("At the edge", c4.share, int(c4.n_stores))]
    for i, (lab, v, n) in enumerate(bars):
        ax3.bar(i, v, width=0.6, color=YELLOW if i else "#cfcec8", edgecolor=INK if i else SURFACE,
                linewidth=2 if i else 0)
        ax3.text(i, v + 0.03, f"{v:.0%}", ha="center", fontsize=19, fontweight="bold")
        ax3.text(i, -0.08, f"{lab}\n{n:,} stores", ha="center", va="top", fontsize=11.5)
    ax3.set_ylim(0, 1.05)
    ax3.set_xlim(-0.6, 1.6)
    ax3.axis("off")
    para(fig, 16.6, cy0 + 3.85, ("SNAP is the federal food program that used to be called food stamps. A store can be "
                                 "approved later than the day it opened, and the records only go back to 2005, so "
                                 "the approval year is a rough stand-in for when a store arrived."),
         6.4, 11)

    # how we know
    hy = cy0 + 5.8
    fig.add_artist(Line2D([1.0 / W, 23.0 / W], [1 - (hy - 0.3) / H] * 2, color=GRID, lw=1.5))
    text(fig, 1.0, hy, "How the edge was measured", fontsize=17, fontweight="bold", va="top")
    text(fig, 12.4, hy, "What the data can't show", fontsize=17, fontweight="bold", va="top")
    left = ("We started at the spot where most of a town's people live, based on 2020 Census counts, and worked "
            "outward. The built-up part of town ends where there are fewer than 200 homes per square mile and "
            "less than a fifth of the land is built on or paved (not counting roads). A store counts as \"at the edge\" if it is past that line but less than twice as far from the "
            "center. \"Small town\" here means an incorporated place with fewer than 25,000 people. A separate "
            "review, also run with Claude, redid every calculation from scratch.")
    right = ("The maps show where the stores are. Why the company chose a particular site is not in the data. "
             "Things like zoning and water and sewer lines would matter, and neither is included. There are also "
             "exceptions. Most edge stores are outside the town limits, and in West Virginia none of the 19 edge "
             "stores is near a highway crossing. The Virginia maps include every edge store, including the ones "
             "that don't fit. A yellow square marks a location only. It is not a judgment of any store or town.")
    para(fig, 1.0, hy + 0.5, left, 10.6, 11)
    para(fig, 12.4, hy + 0.5, right, 10.6, 11)
    src = ("Stores: USDA Food and Nutrition Service, SNAP Retailer Locator historical data, stores authorized as of "
           "2025. Traffic: Federal Highway Administration, HPMS 2024. Homes and people: U.S. Census Bureau, 2020 "
           "blocks. Town limits, counties: Census TIGER/Line and cartographic boundaries, 2024. Paved land: USGS "
           "NLCD 2021. Roads: © OpenStreetMap contributors (ODbL). Regions: groups of Virginia's planning district "
           "commissions. Made with Claude. Independent, and not affiliated with any company named. Working draft "
           "d2, November 2026.")
    para(fig, 1.0, H - 1.05, src, 22, 9, color=MUTED, linespacing=1.4)
    fig.savefig(out + ".png", facecolor=SURFACE)
    fig.savefig(out + ".pdf", facecolor=SURFACE)
    print("bottom of how-we-know text (in):", hy + 0.5 + 5 * 11 * 1.5 / 72, "sources start", H - 1.05)


if __name__ == "__main__":
    main()
