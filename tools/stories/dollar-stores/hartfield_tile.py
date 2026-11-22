"""A trial tile for the Hartfield Dollar General (Middlesex County), drawn like the poster's grid tiles.

Hartfield has no Census place, so the poster's rule scores this store against Deltaville CDP, 7.8 km
away (A = 4.95, "farther out"). This tile is a look at whether it could still go on the poster. It
uses what the rule would use where it can:
- gray: 2020 blocks with at least 200 homes per square mile (the lead edge's density test; the
  impervious-cover test is not applied here, and no 400 m closing);
- traffic: HPMS 2024;
- minor roads: the Overpass extract from the Mathews/Middlesex catchment step.
There is no town-limits line and no arrow to a center, because Hartfield has neither.

Usage: python3 hartfield_tile.py <ds-dir> <overpass-roads.json> <tabblock20.zip> <out-stem>
Made with Claude.
"""
import json
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from shapely.geometry import LineString, box  # noqa: E402

import poster as P  # noqa: E402

STORE_ID = 1153672
DENSE = 77.2  # homes per km2, = 200 per square mile


def main():
    ds, roads_json, blocks_zip, out = sys.argv[1:5]
    P.setup_fonts(ds)
    st = pd.read_csv(f"{ds}/stores_dedup.csv.gz", low_memory=False)
    r = st[st.id == STORE_ID].iloc[0]
    crs = "EPSG:32617"
    frame = box(r.x - P.HALF, r.y - P.HALF, r.x + P.HALF, r.y + P.HALF)
    fr_ll = gpd.GeoSeries([frame], crs=crs).to_crs(4326).iloc[0]

    els = json.load(open(roads_json))["elements"]
    lines = [LineString([(p["lon"], p["lat"]) for p in e["geometry"]]) for e in els
             if e.get("type") == "way" and len(e.get("geometry", [])) > 1]
    rd = gpd.GeoDataFrame(geometry=lines, crs=4326)
    rd = rd[rd.intersects(fr_ll.buffer(0.01))].to_crs(crs)

    bl = gpd.read_file(f"zip://{blocks_zip}", bbox=tuple(fr_ll.buffer(0.01).bounds))
    bl = bl.to_crs(crs)
    bl["dens"] = bl["HOUSING20"] / (bl["ALAND20"] / 1e6).clip(lower=1e-6)
    dense = bl[(bl.dens >= DENSE) & (bl.HOUSING20 > 0)]
    homes = int(bl[bl.intersects(frame)].HOUSING20.sum())

    hp = gpd.read_file(f"{ds}/hpms/va2024.gpkg", bbox=frame.buffer(500))
    near = st[(abs(st.x - r.x) < P.HALF) & (abs(st.y - r.y) < P.HALF) & (st.id != r.id) & (st.state == "VA")]

    W_, H_ = 3.6, 4.05
    fig = plt.figure(figsize=(W_, H_), dpi=300)
    fig.patch.set_facecolor(P.SURFACE)
    size = 2.55
    x0, y0 = 0.5, 0.75
    ax = fig.add_axes([x0 / W_, 1 - (y0 + size) / H_, size / W_, size / H_])
    dense.clip(frame).plot(ax=ax, color=P.BUILT, linewidth=0)
    if len(rd):
        rd.clip(frame).plot(ax=ax, color=P.ROAD, linewidth=0.6)
    for lo, hi, col, lw, _ in P.CLASSES:
        s = hp[(hp.aadt >= lo) & (hp.aadt < hi)]
        if len(s):
            s.plot(ax=ax, color=col, linewidth=lw, capstyle="round")
    cv = near[near.kind == "convenience"]
    ax.scatter(cv.x, cv.y, s=22, marker="o", fc=P.SURFACE, ec=P.INK2, lw=1.0, zorder=5)
    gr = near[near.kind == "grocery"]
    ax.scatter(gr.x, gr.y, s=26, marker="D", fc=P.SURFACE, ec=P.INK, lw=1.0, zorder=5)
    od = near[near.kind.isin(["Dollar General", "Family Dollar", "Dollar Tree"])]
    ax.scatter(od.x, od.y, s=40, marker="s", fc=P.YELLOW, ec=P.INK, lw=1.0, alpha=0.6, zorder=5)
    ax.scatter([r.x], [r.y], s=170, marker="s", fc=P.YELLOW, ec=P.INK, lw=2.2, zorder=7)
    ax.set_xlim(frame.bounds[0], frame.bounds[2])
    ax.set_ylim(frame.bounds[1], frame.bounds[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    for sp in ax.spines.values():
        sp.set_color(P.MUTED)
    ax.set_facecolor(P.SURFACE)
    bits = [f"{int(r.aadt):,} vehicles a day"]
    if r.junction_m <= 250:
        bits.append("at a junction")
    fig.text(x0 / W_, 1 - (y0 - 0.40) / H_, "Hartfield", fontsize=12, fontweight="bold", va="bottom")
    fig.text(x0 / W_, 1 - (y0 - 0.07) / H_, f"{int(r.auth_year)} · " + " · ".join(bits), fontsize=7.6,
             color=P.INK2, va="bottom")
    fig.text(x0 / W_, 1 - (y0 + size + 0.12) / H_,
             P.wrap("Trial tile. Hartfield has no Census boundary, so the poster's rule counts this store as "
                    "between towns. Gray: blocks with 200 or more homes per square mile.", size, 7),
             fontsize=7, color=P.MUTED, va="top", linespacing=1.4)
    fig.savefig(out + ".png", facecolor=P.SURFACE)
    print("homes in frame:", homes, "dense blocks in frame:", int(dense.intersects(frame).sum()),
          "nearby:", near.kind.value_counts().to_dict(), "A:", r.A_lead, "place:", r.NAME,
          "junction m:", round(r.junction_m), "rank:", r["rank"], "inside limits:", r.inside_limits)


if __name__ == "__main__":
    main()
