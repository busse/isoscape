"""Step 13: SNAP households near the stores (hypotheses in casestudy/2026-11-22-13-snap/hypotheses.md).

Usage: python3 snap_test.py <conf_all-dir> <acs-dir> <out-dir>

<acs-dir> holds b22010-bg-7states.dat (ACS 2020-2024 5-year, table B22010, block groups) and
cb_2024_<fips>_bg_500k.zip. Writes snap_points.csv.gz (S at every point used), snap_tests.csv
and snap_by_period.csv. Made with Claude.
"""
import math
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from confirm import MARGIN_M, SEED, SMALL, cluster_boot, mean_stat, verdict  # noqa: E402

CRS = "EPSG:32617"
FIPS = ["21", "24", "37", "45", "47", "51", "54"]
CAP = 400


def load_bg(acs):
    t = pd.read_csv(f"{acs}/b22010-bg-7states.dat", sep="|", header=None, dtype=str).iloc[:, :5]
    t.columns = ["GEO_ID", "hh", "hh_m", "snap", "snap_m"]
    t["GEOID"] = t.GEO_ID.str[9:]
    t["hh"] = pd.to_numeric(t.hh, errors="coerce").fillna(0)
    t["snap"] = pd.to_numeric(t.snap, errors="coerce").fillna(0)
    g = pd.concat([gpd.read_file(f"zip://{acs}/cb_2024_{f}_bg_500k.zip") for f in FIPS]).to_crs(CRS)
    g = g.merge(t[["GEOID", "hh", "snap"]], on="GEOID", how="left").fillna({"hh": 0, "snap": 0})
    g["area"] = g.area
    return g[["GEOID", "hh", "snap", "area", "geometry"]].reset_index(drop=True)


def circle_share(pts, bg, r, chunk=10000):
    """Area-weighted SNAP share of households within r metres of each point (in chunks, for memory)."""
    parts = [_circle(pts.iloc[i:i + chunk], bg, r) for i in range(0, len(pts), chunk)]
    return np.concatenate([a for a, _ in parts]), np.concatenate([b for _, b in parts])


def _circle(pts, bg, r):
    circ = shapely.buffer(shapely.points(pts.x.values, pts.y.values), r, quad_segs=16)
    left, right = bg.sindex.query(circ, predicate="intersects")
    inter = shapely.area(shapely.intersection(circ[left], bg.geometry.values[right]))
    f = inter / bg["area"].values[right]
    hh = np.bincount(left, weights=f * bg.hh.values[right], minlength=len(pts))
    sn = np.bincount(left, weights=f * bg["snap"].values[right], minlength=len(pts))
    return np.where(hh > 0, sn / np.where(hh > 0, hh, 1), np.nan), hh


def own_bg(pts, bg):
    i, j = bg.sindex.query(shapely.points(pts.x.values, pts.y.values), predicate="within")
    s = np.full(len(pts), np.nan)
    v = np.where(bg.hh.values[j] > 0, bg["snap"].values[j] / np.where(bg.hh.values[j] > 0, bg.hh.values[j], 1), np.nan)
    s[i] = v
    return s


def main():
    conf, acs, out = sys.argv[1:4]
    cols = ["is_store", "id", "kind", "auth_year", "x", "y", "A_lead", "edge_dist", "geoid", "state", "set",
            "pop", "joined", "LSAD", "FUNCSTAT"]
    p = pd.read_csv(f"{conf}/points.csv.gz", usecols=cols, low_memory=False)
    p = p[p.set == "B"]
    inc = (p.LSAD.astype(str) != "57") & (p.FUNCSTAT == "A")
    p["small"] = inc & ~p.joined.astype(bool) & (p["pop"] < SMALL)
    p["cls"] = np.where(p.A_lead <= 1, "town", np.where(p.A_lead <= 2, "edge", "out"))
    # as confirm.py: each store once, at its lowest A over every place (any unit), then filter
    st = p[p.is_store].sort_values(["A_lead", "pop", "geoid"], ascending=[True, False, True],
                                   kind="mergesort").drop_duplicates("id")
    st = st[st.small & (st.edge_dist > MARGIN_M)]
    p = p[p.small & (p.edge_dist > MARGIN_M)]
    st = st[st.kind.isin(["Dollar General", "convenience"]) & st.cls.isin(["town", "edge"])]
    keep = set(st.geoid)
    nl = p[~p.is_store & p.cls.isin(["town", "edge"]) & p.geoid.isin(keep)]
    nl = (nl.sample(frac=1, random_state=SEED).groupby(["geoid", "cls"], group_keys=False).head(CAP))
    pts = pd.concat([st, nl]).reset_index(drop=True)
    print("stores", len(st), "edge DG", int(((st.kind == "Dollar General") & (st.cls == "edge")).sum()),
          "null points", len(nl))

    bg = load_bg(acs)
    print("block groups", len(bg), "households", int(bg.hh.sum()))
    pts["S3"], pts["hh3"] = circle_share(pts, bg, 3000)
    pts["S8"], _ = circle_share(pts, bg, 8000)
    pts["Sbg"] = own_bg(pts, bg)
    pts.to_csv(f"{out}/snap_points.csv.gz", index=False)

    rows = []
    for test, kind, cls in (("S1", "Dollar General", "edge"), ("S2", "Dollar General", "town"),
                            ("S3", "convenience", "edge")):
        for m in ("S3", "S8", "Sbg"):
            s = pts[pts.is_store & (pts.kind == kind) & (pts.cls == cls)].dropna(subset=[m]).copy()
            ref = pts[~pts.is_store & (pts.cls == cls)].dropna(subset=[m]).groupby("geoid")[m].mean()
            s["p"] = s.geoid.map(ref)
            s = s.dropna(subset=["p"])
            s["d"] = s[m] - s["p"]
            est, lo, hi = cluster_boot(s, mean_stat("d"))
            rows.append({"test": test, "measure": {"S3": "3 km", "S8": "8 km", "Sbg": "own block group"}[m],
                         "primary": test == "S1" and m == "S3", "kind": kind, "class": cls, "n_stores": len(s),
                         "n_places": s.geoid.nunique(), "stores_mean": round(s[m].mean(), 4),
                         "null_mean": round(s["p"].mean(), 4), "D": round(est, 4), "D_low": round(lo, 4),
                         "D_high": round(hi, 4), "verdict": verdict(lo, hi, 1)})
    t = pd.DataFrame(rows)
    t.to_csv(f"{out}/snap_tests.csv", index=False)
    print(t.to_string())

    dg = pts[pts.is_store & (pts.kind == "Dollar General")].copy()
    dg["period"] = pd.cut(dg.auth_year, [0, 2005, 2015, 2100], labels=["by 2005", "2006-2015", "2016 and later"])
    per = dg.groupby(["cls", "period"], observed=True).agg(stores=("S3", "size"), S3_mean=("S3", "mean"),
                                                            S3_median=("S3", "median")).round(4)
    per.to_csv(f"{out}/snap_by_period.csv")
    print(per.to_string())


if __name__ == "__main__":
    main()
