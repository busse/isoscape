"""Traffic tests for the edge stores, as written in casestudy/2026-11-21-07-traffic/hypotheses.md.

Usage: python3 traffic.py <hpms.gpkg> <work-dir> <edge_points.csv> <raw-dir> <out-dir>

hpms.gpkg: FHWA HPMS 2024 Virginia sections (functional system 1-6, with AADT), in EPSG:32617.
"""
import json
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from reasons import wilson

SEED = 20261121
MATCH_M = 60
CHAINS = ["Dollar General", "Family Dollar", "Dollar Tree"]


def road_id(df):
    num = df["route_number"].fillna("").astype(str).str.strip()
    name = df["routename"].fillna("").astype(str).str.strip().str.upper()
    rid = np.where(num != "", "R" + num, np.where(name != "", "N" + name, "S" + df.index.astype(str)))
    return pd.Series(rid, index=df.index)


def boot_median(v, n=10000, seed=SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(v)
    meds = np.median(rng.choice(v, (n, len(v)), replace=True), axis=1)
    return np.percentile(meds, [2.5, 97.5])


def main():
    hp_path, work, pts_path, raw, out = sys.argv[1:6]
    os.makedirs(out, exist_ok=True)
    hp = gpd.read_file(hp_path)
    hp["road"] = road_id(hp)
    p = pd.read_csv(pts_path)
    g = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.x, p.y), crs=32617)
    j = gpd.sjoin_nearest(g, hp[["aadt", "year", "road", "f_system", "geometry"]], how="left",
                          max_distance=MATCH_M, distance_col="match_m")
    j = j[~j.index.duplicated()]
    p["aadt"], p["aadt_year"], p["road"], p["match_m"] = j["aadt"], j["year"], j["road"], j["match_m"]

    places = gpd.read_file(f"zip://{raw}/tl_2024_51_place.zip")
    lsad = dict(zip(places.NAME.str.lower().str.replace(" ", "-"), places.LSAD))
    p["is_town"] = p["town"].map(lsad) == "43"

    # test 2: rank the roads crossing each place's built-up edge by AADT at the crossing
    p["busiest_rank"] = np.nan
    for town in p["town"].unique():
        built = gpd.read_file(f"{work}/{town}/builtup.gpkg")
        edge = built[built["setting"] == "lead"].geometry.iloc[0].boundary
        cross = hp[hp.intersects(edge)]
        if cross.empty:
            continue
        rank = cross.groupby("road")["aadt"].max().sort_values(ascending=False)
        order = {r: i + 1 for i, r in enumerate(rank.index)}
        sel = p["town"] == town
        p.loc[sel, "busiest_rank"] = p.loc[sel, "road"].map(order)
        p.loc[sel, "crossing_roads"] = len(order)
    p.to_csv(f"{out}/traffic_points.csv", index=False)

    rows = []
    def add(label, df, ref):
        v = df["aadt"].dropna()
        lo, hi = boot_median(v) if len(v) > 2 else (np.nan, np.nan)
        rv = ref["aadt"].dropna()
        med_r = float(np.median(rv)) if len(rv) else np.nan
        verdict = "supported" if med_r < lo else "contradicted" if med_r > hi else "cannot tell"
        b1 = (df["busiest_rank"] == 1).mean()
        b2 = (df["busiest_rank"] <= 2).mean()
        k1, k2, nn = int((df["busiest_rank"] == 1).sum()), int((df["busiest_rank"] <= 2).sum()), len(df)
        r1, r2 = (ref["busiest_rank"] == 1).mean(), (ref["busiest_rank"] <= 2).mean()
        w1, w2 = wilson(k1, nn), wilson(k2, nn)
        v1 = "supported" if r1 < w1[0] else "contradicted" if r1 > w1[1] else "cannot tell"
        v2 = "supported" if r2 < w2[0] else "contradicted" if r2 > w2[1] else "cannot tell"
        rows.append({"group": label, "n": len(df), "with_count": len(v), "median_aadt": float(np.median(v)) if len(v) else None,
                     "ci_low": lo, "ci_high": hi, "random_median": med_r, "verdict": verdict,
                     "on_busiest_crossing": round(b1, 3), "on_top2_crossing": round(b2, 3),
                     "random_on_busiest": round((ref["busiest_rank"] == 1).mean(), 3),
                     "random_on_top2": round((ref["busiest_rank"] <= 2).mean(), 3),
                     "busiest_k": k1, "busiest_ci": f"{w1[0]:.2f}-{w1[1]:.2f}", "busiest_verdict": v1,
                     "top2_k": k2, "top2_ci": f"{w2[0]:.2f}-{w2[1]:.2f}", "top2_verdict": v2})
    dg = p[p.kind == "Dollar General"]
    rnd = p[p.kind == "random"]
    add("Dollar General, all edge", dg, rnd)
    add("Dollar General, towns (follow-up to an exploratory split)", dg[dg.is_town], rnd[rnd.is_town])
    add("Dollar General, cities (same)", dg[~dg.is_town], rnd[~rnd.is_town])
    add("Three chains, all edge", p[p.kind.isin(CHAINS)], rnd)
    add("Supermarkets and groceries, edge", p[p.group == "grocery"], rnd)
    add("Convenience stores, edge", p[p.group == "convenience"], rnd)
    res = pd.DataFrame(rows)
    res.to_csv(f"{out}/traffic_tests.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.to_string())
    print("count years at matched points:", p["aadt_year"].value_counts().to_dict())


if __name__ == "__main__":
    main()
