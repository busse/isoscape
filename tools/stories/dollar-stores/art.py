"""Art poster (24 x 36 in): every Virginia town and city, drawn alike. Rough draft.

Usage: python3 art.py <ds-dir> <out-stem>

Chris's brief (November 21): a "simplified artistic" version, "denser and reduced element
resolution", every town and city (227). Each square is the same 5 km of ground around the
town's population-weighted center, north up. Only three things are drawn:
- the built-up town (the lead edge), as a flat gray shape;
- the counted roads (HPMS 2024), as dark lines, thicker for more traffic, simplified to 25 m;
- every Dollar General, as a yellow square with a black ring.
One full grid with no breaks, still in the order of the five regions of regions.json, west to
east within each.
No captions or charts; the town's name, small, under each square. Made with Claude.
"""
import json
import math
import os
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from shapely.geometry import Point, box  # noqa: E402

import poster as P  # noqa: E402

W, H = 24, 36
HALF = 2500
COLS = 14
INK, ROADINK, GRAY, PAPER = "#1a1a1a", "#2b2b33", "#dcdad3", "#fbfaf7"
WIDTH = [(0, 2000, 0.35), (2000, 5000, 0.6), (5000, 10000, 0.9), (10000, 20000, 1.3), (20000, 1e9, 1.8)]


def slot(k, x0, y0, size, gap, rowh):
    return x0 + (k % COLS) * (size + gap), y0 + (k // COLS) * rowh


def label(fig, x, y, size, s):
    P.text(fig, x, y + size + 0.02, s, fontsize=6.5, color=P.INK2, va="top")


def panels(fig, ds, hp, counties, pl, f, x0, y0, size, gap, rowh, k0):
    """Fill the empty end of the last row with squares the size of the maps: a key (3), a
    locator (3 wide), three counted facts and two of copy. Every number comes from f."""
    free = COLS - k0 % COLS
    assert free == 11, f"the panels are laid out for 11 open slots, not {free}"
    at = lambda n: slot(k0 + n, x0, y0, size, gap, rowh)  # noqa: E731

    # key 1: a town, drawn the way the squares draw it
    x, y = at(0)
    ax = P.axes(fig, x, y, size, size)
    m = json.load(open(f"{ds}/work_all/floyd/meta.json"))
    cx, cy = m["center"]
    fr = box(cx - HALF, cy - HALF, cx + HALF, cy + HALF)
    b = gpd.read_file(f"{ds}/work_all/floyd/builtup.gpkg")
    b[b.setting == "lead"].clip(fr).plot(ax=ax, color=GRAY, linewidth=0)
    ax.set_xlim(cx - HALF, cx + HALF); ax.set_ylim(cy - HALF, cy + HALF); ax.set_aspect("equal"); ax.axis("off")
    ax.text(0.5, 0.5, "built-up\ntown", transform=ax.transAxes, ha="center", va="center", fontsize=8, color=INK)
    label(fig, x, y, size, "Key: built-up town (Floyd)")

    # key 2: road weights
    x, y = at(1)
    ax = P.axes(fig, x, y, size, size)
    names = ["under 2,000", "2,000 to 5,000", "5,000 to 10,000", "10,000 to 20,000", "20,000 and over"]
    for n, ((lo, hi, lw), nm) in enumerate(zip(WIDTH, names)):
        yy = 0.86 - n * 0.18
        ax.plot([0.02, 0.36], [yy, yy], color=ROADINK, lw=lw, solid_capstyle="round")
        ax.text(0.42, yy, nm, fontsize=6.5, va="center", color=INK)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    label(fig, x, y, size, "Key: vehicles a day, 2024")

    # key 3: the store mark
    x, y = at(2)
    ax = P.axes(fig, x, y, size, size)
    ax.scatter([0.5], [0.62], s=34, marker="s", fc=P.YELLOW, ec=INK, lw=1.0)
    ax.text(0.5, 0.36, "one Dollar General\nthat takes SNAP", ha="center", va="center", fontsize=7, color=INK,
            linespacing=1.4)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    label(fig, x, y, size, "Key: Dollar General")

    # locator, three squares wide: every place in the grid's order
    x, y = at(3)
    w = 3 * size + 2 * gap
    ax = P.axes(fig, x, y, w, size)
    counties.dissolve().boundary.plot(ax=ax, color=P.INK2, linewidth=0.6)
    for key, _ in P.REGIONS:
        counties[counties.region == key].dissolve().boundary.plot(ax=ax, color=P.INK2, linewidth=0.3)
    ax.scatter(pl.x, pl.y, s=3, color=INK, zorder=3)
    ax.plot(pl.x, pl.y, color=P.INK2, lw=0.2, alpha=0.3, zorder=2)
    bb = counties.total_bounds
    ax.set_xlim(bb[0], bb[2]); ax.set_ylim(bb[1], bb[3]); ax.set_aspect("equal"); ax.axis("off")
    label(fig, x, y, size, f"The {f['places']} places; the faint line follows the order of the squares")

    # three facts
    facts = [(f"{f['dg']:,}", "Dollar General stores in Virginia take SNAP benefits (USDA, 2025)."),
             (f"{f['places_with']:,}", f"of the {f['places']} places have at least one inside their square."),
             (f"{f['outside']:,}", f"of the {f['insq']:,} stores in these squares stand outside the gray. "
                                   f"The rest are in the built-up town.")]
    for n, (big, small) in enumerate(facts):
        x, y = at(6 + n)
        P.text(fig, x, y + 0.08, big, fontsize=30, fontweight="bold", color=INK, va="top")
        P.para(fig, x, y + 0.72, small, size - 0.05, 7.2, color=P.INK2, linespacing=1.35)

    # copy, two squares
    x, y = at(9)
    w = 2 * size + gap
    P.para(fig, x, y + 0.04, "Each square is centered on the middle of where the town's people live. The squares "
           "run in the order of Virginia's five planning regions, southwest to coast, and west to east within each.",
           w, 7, color=INK, linespacing=1.4)
    P.para(fig, x, y + 0.72, "Stores: USDA SNAP Retailer Locator, authorized as of 2025; a store that doesn't take "
           "SNAP is missing. Roads and traffic: FHWA HPMS 2024. Built-up town: 2020 Census blocks and USGS NLCD 2021. "
           "Made with Claude. Independent, and not affiliated with any company named. Chris Busse, rough draft, "
           "November 2026.", w, 6.5, color=P.MUTED, linespacing=1.35)


def main():
    ds, out = sys.argv[1:3]
    P.setup_fonts(ds)
    hp = gpd.read_file(f"{ds}/hpms/va2024.gpkg")
    hp["geometry"] = hp.geometry.simplify(25)
    hp.sindex
    counties = gpd.read_file(f"{ds}/counties/va_regions.gpkg").to_crs(hp.crs)
    st = pd.read_csv(f"{ds}/stores_dedup.csv.gz", low_memory=False)
    dg = st[(st.state == "VA") & (st.kind == "Dollar General")].drop_duplicates("id")

    rows = []
    for slug in sorted(os.listdir(f"{ds}/work_all")):
        f = f"{ds}/work_all/{slug}"
        meta = json.load(open(f"{f}/meta.json"))
        name = gpd.read_file(f"{f}/place.gpkg")["NAME"].iloc[0]
        cx, cy = meta["center"]
        rows.append({"slug": slug, "name": name, "x": cx, "y": cy})
    pl = pd.DataFrame(rows)
    pts = gpd.GeoDataFrame(pl, geometry=[Point(x, y) for x, y in zip(pl.x, pl.y)], crs=hp.crs)
    j = gpd.sjoin_nearest(pts, counties[["region", "geometry"]], how="left").drop_duplicates("slug")
    pl["region"] = j["region"].values
    order = {k: i for i, (k, _) in enumerate(P.REGIONS)}
    pl["r"] = pl.region.map(order)
    pl = pl.sort_values(["r", "x"]).reset_index(drop=True)

    fig = plt.figure(figsize=(W, H), dpi=100)
    fig.patch.set_facecolor(PAPER)
    P.text(fig, 0.9, 1.45, "Dollar General on the edge of town", fontsize=40, fontweight="bold", va="bottom",
           color=INK)
    P.para(fig, 0.9, 1.75, f"Every town and city in Virginia, {len(pl)} of them, each drawn as the same 5 km of "
           f"ground, in order from the southwest to the coast. Gray is the built-up town, dark lines are the counted roads (thicker for more traffic) and "
           f"yellow squares are Dollar General stores.", 22.2, 13)
    # one full grid, no breaks: the order is still by region and west to east within each
    x0, y0, gap = 0.9, 2.85, 0.12
    size = (22.2 - (COLS - 1) * gap) / COLS
    rows = math.ceil((len(pl) + 11) / COLS)
    rowh = (H - 0.75 - y0 - size - 0.2) / (rows - 1)  # last row's names end 0.75 in above the foot
    insq, inside, places_with = set(), set(), 0
    for k, (_, r) in enumerate(pl.iterrows()):
        tx, ty = x0 + (k % COLS) * (size + gap), y0 + (k // COLS) * rowh
        ax = P.axes(fig, tx, ty, size, size)
        frame = box(r.x - HALF, r.y - HALF, r.x + HALF, r.y + HALF)
        b = gpd.read_file(f"{ds}/work_all/{r.slug}/builtup.gpkg")
        b = b[b.setting == "lead"].clip(frame)
        if len(b):
            b.plot(ax=ax, color=GRAY, linewidth=0)
        gray = b.geometry.union_all() if len(b) else None
        h = hp.iloc[list(hp.sindex.query(frame, predicate="intersects"))]
        for lo, hi, lw in WIDTH:
            sg = h[(h.aadt >= lo) & (h.aadt < hi)]
            if len(sg):
                sg.clip(frame).plot(ax=ax, color=ROADINK, linewidth=lw, capstyle="round")
        d = dg[(abs(dg.x - r.x) < HALF) & (abs(dg.y - r.y) < HALF)]
        insq.update(d.id)
        places_with += bool(len(d))
        if gray is not None:
            inside.update(d.id[[gray.contains(Point(a, c)) for a, c in zip(d.x, d.y)]])
        ax.scatter(d.x, d.y, s=34, marker="s", fc=P.YELLOW, ec=INK, lw=1.0, zorder=5)
        ax.set_xlim(r.x - HALF, r.x + HALF)
        ax.set_ylim(r.y - HALF, r.y + HALF)
        ax.set_aspect("equal")
        ax.axis("off")
        P.text(fig, tx, ty + size + 0.02, r["name"], fontsize=6.5, color=P.INK2, va="top")
    i = len(pl)
    row = math.ceil(i / COLS)
    last = i - (row - 1) * COLS
    print("tile", round(size, 3), "in; last row holds", last, "of", COLS, "; empty slots", COLS - last)
    facts = {"dg": len(dg), "insq": len(insq), "places_with": places_with, "outside": len(insq - inside),
             "places": len(pl)}
    panels(fig, ds, hp, counties, pl, facts, x0, y0, size, gap, rowh, i)
    fig.savefig(out + ".png", facecolor=PAPER)
    fig.savefig(out + ".pdf", facecolor=PAPER)
    print("places", i, "rows", row, "bottom of grid (in):", round(y0 + row * rowh, 2))
    print(pl.groupby("region", sort=False).size().to_string())


if __name__ == "__main__":
    main()
