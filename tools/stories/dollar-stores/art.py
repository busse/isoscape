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
    rowh = size + 0.2 + gap
    for k, (_, r) in enumerate(pl.iterrows()):
        tx, ty = x0 + (k % COLS) * (size + gap), y0 + (k // COLS) * rowh
        ax = P.axes(fig, tx, ty, size, size)
        frame = box(r.x - HALF, r.y - HALF, r.x + HALF, r.y + HALF)
        b = gpd.read_file(f"{ds}/work_all/{r.slug}/builtup.gpkg")
        b = b[b.setting == "lead"].clip(frame)
        if len(b):
            b.plot(ax=ax, color=GRAY, linewidth=0)
        h = hp.iloc[list(hp.sindex.query(frame, predicate="intersects"))]
        for lo, hi, lw in WIDTH:
            sg = h[(h.aadt >= lo) & (h.aadt < hi)]
            if len(sg):
                sg.clip(frame).plot(ax=ax, color=ROADINK, linewidth=lw, capstyle="round")
        d = dg[(abs(dg.x - r.x) < HALF) & (abs(dg.y - r.y) < HALF)]
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
    P.text(fig, 0.9, H - 0.55, "Stores: USDA SNAP Retailer Locator, authorized as of 2025. Roads and traffic: FHWA "
           "HPMS 2024. Built-up town: 2020 Census blocks and USGS NLCD 2021. Made with Claude. Independent, and not "
           "affiliated with any company named. Chris Busse, rough draft, November 2026.", fontsize=8, color=P.MUTED,
           va="top")
    fig.savefig(out + ".png", facecolor=PAPER)
    fig.savefig(out + ".pdf", facecolor=PAPER)
    print("places", i, "rows", row, "bottom of grid (in):", round(y0 + row * rowh, 2))
    print(pl.groupby("region", sort=False).size().to_string())


if __name__ == "__main__":
    main()
