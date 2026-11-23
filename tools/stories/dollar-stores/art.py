"""Art poster (24 x 36 in): every Virginia town and city, drawn alike. Rough draft.

Usage: python3 art.py <ds-dir> <out-stem>

Chris's brief (November 21): a "simplified artistic" version, "denser and reduced element
resolution", every town and city (227). Each square is the same 5 km of ground around the
town's population-weighted center, north up. Only three things are drawn:
- the built-up town (the lead edge), as a flat gray shape;
- the counted roads (HPMS 2024), as dark lines, thicker for more traffic, simplified to 25 m;
- every Dollar General, as a yellow square with a black ring.
Squares are grouped by the five regions of regions.json and run west to east within each.
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
    P.text(fig, 0.9, 1.95, f"Every town and city in Virginia, {len(pl)} of them, each drawn as the same 5 km of "
           f"ground. Gray is the built-up town, dark lines are the counted roads (thicker for more traffic) and "
           f"yellow squares are Dollar General stores.", fontsize=13, color=P.INK2, va="bottom")
    x0, y0, pitch = 0.9, 2.55, 22.2 / COLS
    size = pitch * 0.84
    i = 0
    row = 0
    for rk, (key, short) in enumerate(P.REGIONS):
        grp = pl[pl.region == key]
        if not len(grp):
            continue
        ry = y0 + row * (pitch + 0.22)
        P.text(fig, x0, ry + 0.02, f"{rk + 1}  {short.upper()}  ({len(grp)})", fontsize=9, color=P.INK2,
               va="bottom")
        fig.add_artist(Line2D([x0 / W, (x0 + 22.2 - (pitch - size)) / W], [1 - (ry + 0.06) / H] * 2, color=P.INK2,
                              lw=0.6))
        for k, (_, r) in enumerate(grp.iterrows()):
            c, rr = k % COLS, row + k // COLS
            tx, ty = x0 + c * pitch, y0 + rr * (pitch + 0.22) + 0.16
            ax = P.axes(fig, tx, ty, size, size)
            frame = box(r.x - HALF, r.y - HALF, r.x + HALF, r.y + HALF)
            b = gpd.read_file(f"{ds}/work_all/{r.slug}/builtup.gpkg")
            b = b[b.setting == "lead"].clip(frame)
            if len(b):
                b.plot(ax=ax, color=GRAY, linewidth=0)
            h = hp.iloc[list(hp.sindex.query(frame, predicate="intersects"))]
            for lo, hi, lw in WIDTH:
                s = h[(h.aadt >= lo) & (h.aadt < hi)]
                if len(s):
                    s.clip(frame).plot(ax=ax, color=ROADINK, linewidth=lw, capstyle="round")
            d = dg[(abs(dg.x - r.x) < HALF) & (abs(dg.y - r.y) < HALF)]
            ax.scatter(d.x, d.y, s=34, marker="s", fc=P.YELLOW, ec=INK, lw=1.0, zorder=5)
            ax.set_xlim(r.x - HALF, r.x + HALF)
            ax.set_ylim(r.y - HALF, r.y + HALF)
            ax.set_aspect("equal")
            ax.axis("off")
            ax.set_facecolor(PAPER)
            P.text(fig, tx, ty + size + 0.02, r["name"], fontsize=6.5, color=P.INK2, va="top")
            i += 1
        row += math.ceil(len(grp) / COLS)
    P.text(fig, 0.9, H - 0.55, "Stores: USDA SNAP Retailer Locator, authorized as of 2025. Roads and traffic: FHWA "
           "HPMS 2024. Built-up town: 2020 Census blocks and USGS NLCD 2021. Made with Claude. Independent, and not "
           "affiliated with any company named. Chris Busse, rough draft, November 2026.", fontsize=8, color=P.MUTED,
           va="top")
    fig.savefig(out + ".png", facecolor=PAPER)
    fig.savefig(out + ".pdf", facecolor=PAPER)
    print("places", i, "rows", row, "bottom of grid (in):", round(y0 + row * (pitch + 0.22), 2))
    print(pl.groupby("region", sort=False).size().to_string())


if __name__ == "__main__":
    main()
