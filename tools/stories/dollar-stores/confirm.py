"""The replication tests of plan v2 (casestudy/2026-11-21-09-replication/plan.md).

  python3 confirm.py features <out-dir> <hpms.gpkg> <places.gpkg> <work>:<osm>:<set> [...]
  python3 confirm.py tests <out-dir> <discovery_stores.csv>

features: for every place folder in each <work> dir, reads measure.py's outputs and writes one
row per store and per in-band random point with the features the tests need. <set> is
"discovery", "A" (Virginia CDPs) or "B" (six states). places.gpkg holds every TIGER 2024 place of
all seven states (EPSG:32617). For tests, discovery_stores.csv is pool.py's stores.csv for
Virginia's incorporated places: any store that entered a discovery test (A <= 3 there) is never
held out.

tests: pools everything, assigns each store once (lowest A), applies the units, and runs C1-C6
with the place-conditional statistic and a cluster bootstrap by place, then the sensitivities.
"""
import json
import math
import os
import re
import sys
from multiprocessing import Pool

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point

CRS = 32617
SEED = 20261121
MARGIN_M = 30
MATCH_M = 60
JUNCTION_M = 250
SMALL = 25000
CHAINS = ["Dollar General", "Family Dollar", "Dollar Tree"]
MAIN = {"trunk", "primary", "secondary", "tertiary", "trunk_link", "primary_link"}
POSTAL = {"51": "VA", "37": "NC", "47": "TN", "21": "KY", "54": "WV", "24": "MD", "45": "SC"}
STATE_PREFIX = {"VA", "NC", "TN", "KY", "WV", "MD", "SC", "GA", "AL", "MS", "OH", "IN", "IL", "MO", "AR", "PA", "DE", "DC", "NJ"}


def counts_as_route(token, state):
    """Plan v2, junction rule: I and US everywhere; the state's own primary numbers; Tennessee's
    "SR n" state routes; Kentucky numbers under 1000; never VA/NC "SR" secondaries, WV "CR" or SC "S-"."""
    m = re.match(r"^\s*([A-Za-z]+)[\s\-]*(\d+)", token)
    if not m:
        return False
    pre, num = m.group(1).upper(), int(m.group(2))
    if pre in ("I", "US"):
        return True
    if pre == "SR":
        return state == "TN"
    if pre == "KY":
        return num < 1000
    return pre in STATE_PREFIX and pre not in ("CR", "S")


def junction_tree(osm_path, state):
    d = json.load(open(osm_path))
    tf = Transformer.from_crs(4326, CRS, always_xy=True)
    refs, deg, xy = {}, {}, {}
    for e in d["elements"]:
        if e.get("type") != "way" or e.get("tags", {}).get("highway") not in MAIN | {"tertiary_link", "secondary_link", "motorway", "motorway_link"}:
            continue
        toks = frozenset(t.strip().upper() for t in str(e["tags"].get("ref", "")).split(";")
                         if t.strip() and counts_as_route(t, state))
        ns = e["nodes"]
        for k, (n, q) in enumerate(zip(ns, e["geometry"])):
            deg[n] = deg.get(n, 0) + (1 if k in (0, len(ns) - 1) else 2)
            xy[n] = (q["lon"], q["lat"])
            if toks:
                refs.setdefault(n, set()).add(toks)
    pts = [tf.transform(*xy[n]) for n, sets in refs.items()
           if len(sets) >= 2 and len(set().union(*sets)) >= 2 and deg.get(n, 0) >= 3]
    return cKDTree(np.array(pts)) if pts else None


def road_key(df):
    num = df["route_number"].fillna("").astype(str).str.strip()
    sig = df["route_signing"].fillna("").astype(str).str.strip()
    name = df["routename"].fillna("").astype(str).str.strip().str.upper()
    return pd.Series(np.where(num != "", "R" + sig + "-" + num, np.where(name != "", "N" + name, "S" + df.index.astype(str))),
                     index=df.index)


HP = None


def init(hp_path):
    global HP
    HP = gpd.read_file(hp_path)
    HP["road"] = road_key(HP)
    HP.sindex


def place_features(args):
    folder, osm_dir, set_name = args
    try:
        meta = json.load(open(f"{folder}/meta.json"))
        place = gpd.read_file(f"{folder}/place.gpkg")
        geoid, st = place["GEOID"].iloc[0], place["GEOID"].iloc[0][:2]
        state = POSTAL.get(st, "")
        pgeom = place.geometry.iloc[0]
        built = gpd.read_file(f"{folder}/builtup.gpkg").set_index("setting").geometry
        lead = built["lead"]
        edge_line = lead.boundary
        cx, cy = meta["center"]
        try:
            s = pd.read_csv(f"{folder}/scores.csv")
        except pd.errors.EmptyDataError:
            s = pd.DataFrame()
        nl = pd.read_csv(f"{folder}/null.csv")
        nl = nl[(nl["A_lead"] <= 3) | (nl["A_loose"] <= 3)].copy()
        nl["kind"], nl["id"], nl["auth_year"] = "random", None, np.nan
        pts = pd.concat([s.assign(is_store=True), nl.assign(is_store=False)], ignore_index=True)
        if pts.empty:
            return None
        P = gpd.GeoSeries(gpd.points_from_xy(pts.x, pts.y), crs=CRS)
        pts["edge_dist"] = P.distance(edge_line).values
        pts["inside_limits"] = P.within(pgeom).values
        jt = junction_tree(f"{osm_dir}/{os.path.basename(folder)}.json", state)
        pts["junction_m"] = jt.query(np.c_[pts.x, pts.y])[0] if jt is not None else np.inf
        # crossing roads (M5): length inside the built-up area shrunk by 30 m and outside it grown by 30 m
        inner, outer = lead.buffer(-MARGIN_M), lead.buffer(MARGIN_M)
        win = pgeom.buffer(8500)
        hp = HP.iloc[list(HP.sindex.query(win, predicate="intersects"))]
        # HPMS sections are short (cut wherever any attribute changes), so the test is made on
        # each whole road: the road's sections within the window, merged. A road crosses when it
        # reaches 30 m inside the built-up area and 30 m outside it, and touches the edge line.
        # Its AADT at the crossing is the highest among its sections within 30 m of the edge line.
        # (First version tested single sections; on the discovery data that missed most
        # crossings: fixed before any held-out place was read.)
        near_edge = hp[hp.intersects(lead.boundary.buffer(MARGIN_M))]
        ok = []
        for road in near_edge["road"].unique():
            geom = hp[hp["road"] == road].geometry.union_all()
            if geom.intersects(inner) and not geom.within(outer):
                ok.append(road)
        crosses = near_edge[near_edge["road"].isin(ok)]
        rank, rank_b = {}, None
        if len(crosses):
            r = crosses.groupby("road")["aadt"].max().sort_values(ascending=False)
            rank = {k: i + 1 for i, k in enumerate(r.index)}
            # S4: bearing of each crossing (from the center), to keep crossings on the store's side
            cp = crosses.geometry.intersection(lead.boundary).representative_point()
            crosses = crosses.assign(bear=np.arctan2(cp.x - cx, cp.y - cy))
        g = gpd.GeoDataFrame(pts[["x", "y"]], geometry=P, crs=CRS)
        for dist, tag in ((MATCH_M, ""), (100, "_100")):
            j = gpd.sjoin_nearest(g, hp[["aadt", "road", "geometry"]], how="left", max_distance=dist, distance_col="d")
            j = j[~j.index.duplicated()]
            pts["aadt" + tag] = j["aadt"].values
            pts["road" + tag] = j["road"].values
            pts["match_m" + tag] = j["d"].values
            pts["rank" + tag] = pts["road" + tag].map(rank)
        # S4 rank among crossings within 90 degrees of the point's bearing
        if len(crosses):
            pb = np.arctan2(pts.x.values - cx, pts.y.values - cy)
            rs = []
            for b, road in zip(pb, pts["road"]):
                dif = np.abs((crosses["bear"].values - b + np.pi) % (2 * np.pi) - np.pi)
                side = crosses[dif <= np.pi / 2]
                if road is None or (isinstance(road, float) and np.isnan(road)) or side.empty:
                    rs.append(np.nan)
                    continue
                r2 = side.groupby("road")["aadt"].max().sort_values(ascending=False)
                rs.append(list(r2.index).index(road) + 1 if road in r2.index else np.nan)
            pts["rank_side"] = rs
        else:
            pts["rank_side"] = np.nan
        pts["crossing_roads"] = len(rank)
        # S6: rays that leave and re-enter the built-up area on the way out
        def reentries(x, y):
            b = math.atan2(x - cx, y - cy)
            end = Point(cx + 20000 * math.sin(b), cy + 20000 * math.cos(b))
            h = lead.intersection(LineString([(cx, cy), end]))
            return len(getattr(h, "geoms", [h])) - 1 if not h.is_empty else 0
        pts["reentries"] = [reentries(x, y) for x, y in zip(pts.x, pts.y)]
        pts["geoid"], pts["state"], pts["set"] = geoid, state, set_name
        pts["folder"] = os.path.basename(folder)
        pts["pop"] = meta["pop_in_limits"]
        pts["joined"] = meta["in_larger_urban_area"]
        pts["gap_fallback"] = meta.get("center_gap_fallback", np.nan)
        pts["center_x"], pts["center_y"] = cx, cy
        keep = ["is_store", "id", "name", "kind", "auth_year", "x", "y", "A_lead", "A_loose", "edge_dist", "inside_limits",
                "junction_m", "aadt", "road", "match_m", "rank", "aadt_100", "rank_100", "match_m_100", "rank_side",
                "crossing_roads", "reentries", "geoid", "state", "set", "folder", "pop", "joined", "gap_fallback",
                "center_x", "center_y"]
        return pts[[c for c in keep if c in pts.columns]]
    except Exception as ex:  # one bad place must not stop the run; it is listed
        return pd.DataFrame([{"folder": os.path.basename(folder), "error": repr(ex)[:300]}])


def features(out, hp_path, places_path, specs):
    os.makedirs(out, exist_ok=True)
    jobs = []
    for spec in specs:
        work, osm, set_name = spec.split(":")
        for f in sorted(os.listdir(work)):
            if os.path.exists(f"{work}/{f}/null.csv"):
                jobs.append((f"{work}/{f}", osm, set_name))
    with Pool(2, initializer=init, initargs=(hp_path,)) as pool:
        parts = pool.map(place_features, jobs, chunksize=4)
    allp = pd.concat([p for p in parts if p is not None], ignore_index=True)
    errs = allp[allp.get("error").notna()] if "error" in allp else pd.DataFrame()
    allp = allp[allp["error"].isna()].drop(columns="error") if "error" in allp else allp
    places = gpd.read_file(places_path)[["GEOID", "LSAD", "FUNCSTAT", "NAME"]]
    allp = allp.merge(places.rename(columns={"GEOID": "geoid"}), on="geoid", how="left")
    allp.to_csv(f"{out}/points.csv.gz", index=False)
    errs.to_csv(f"{out}/errors.csv", index=False)
    print("points", len(allp), "places", allp["geoid"].nunique(), "errors", len(errs))


# ---------------------------------------------------------------- tests

def cluster_boot(df, stat, n=10000, seed=SEED):
    rng = np.random.default_rng(seed)
    groups = [g for _, g in df.groupby("geoid")]
    if len(groups) < 2:
        return np.nan, np.nan, np.nan
    est = stat(df)
    k = len(groups)
    vals = []
    for _ in range(n):
        pick = rng.integers(0, k, k)
        vals.append(stat(pd.concat([groups[i] for i in pick])))
    lo, hi = np.nanpercentile(vals, [2.5, 97.5])
    return est, lo, hi


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def verdict(lo, hi, sign):
    if np.isnan(lo):
        return "no data"
    if sign > 0:
        return "holds" if lo > 0 else "against" if hi < 0 else "cannot tell"
    return "holds" if hi < 0 else "against" if lo > 0 else "cannot tell"


CLAIMS = {
    "C1": lambda d: (d["rank"] <= 2).astype(float),
    "C2": lambda d: (d["junction_m"] <= JUNCTION_M).astype(float),
    "C3": lambda d: d["inside_limits"].astype(float),
}


def place_conditional(stores, null, claim, band_col="A_lead", lo=1.0, hi=2.0, abin=False, fn=None):
    fn = fn or CLAIMS[claim]
    nb = null[(null[band_col] > lo) & (null[band_col] <= hi)].copy()
    nb["y"] = fn(nb)
    s = stores.copy()
    s["x"] = fn(s)
    if abin:
        bins = [lo, 1.25, 1.5, hi]
        nb["bin"] = pd.cut(nb[band_col], bins)
        s["bin"] = pd.cut(s[band_col], bins)
        p = nb.groupby(["geoid", "bin"], observed=True)["y"].mean()
        s["p"] = [p.get((g, b), np.nan) for g, b in zip(s.geoid, s.bin)]
    else:
        s["p"] = s["geoid"].map(nb.groupby("geoid")["y"].mean())
    s = s.dropna(subset=["p"])
    est, l, h = cluster_boot(s, lambda d: (d["x"] - d["p"]).mean())
    k, n = int(s["x"].sum()), len(s)
    wl, wh = wilson(k, n)
    return {"n_stores": n, "n_places": s["geoid"].nunique(), "observed": k, "expected": round(s["p"].sum(), 1),
            "share": round(k / n, 3) if n else np.nan, "share_ci": f"{wl:.2f}-{wh:.2f}" if n else "",
            "D": round(est, 3), "D_low": round(l, 3), "D_high": round(h, 3)}


def tests(out):
    p = pd.read_csv(f"{out}/points.csv.gz", low_memory=False)
    p["incorporated"] = (p["LSAD"].astype(str) != "57") & (p["FUNCSTAT"] == "A")
    p["unit"] = np.where(p["joined"], "joined",
                         np.where(~p["incorporated"], "CDP", np.where(p["pop"] < SMALL, "small", "large")))
    st = p[p.is_store].copy()
    disc = pd.read_csv(sys.argv[3]) if len(sys.argv) > 3 else None
    st = st.sort_values("A_lead").drop_duplicates("id")  # each store once, at its lowest A
    used = set(disc.loc[disc["A_lead"] <= 3, "id"]) if disc is not None else set()
    st["held_out_ok"] = (st["set"] == "discovery") | ~st["id"].isin(used)
    st["usable"] = (st["edge_dist"] > MARGIN_M) & st["held_out_ok"]
    nl = p[~p.is_store & (p["edge_dist"] > MARGIN_M)]
    rows = []

    def run(label, sset, unit, kind="Dollar General", extra=None, null_extra=None, **kw):
        s = st[(st["set"].isin(sset)) & (st["unit"].isin(unit)) & (st["kind"] == kind) & st["usable"]]
        n = nl[(nl["set"].isin(sset)) & (nl["unit"].isin(unit))]
        if extra is not None:
            s = s[extra(s)]
        if null_extra is not None:
            n = n[null_extra(n)]
        band = kw.pop("band", (1.0, 2.0))
        e = s[(s["A_lead"] > band[0]) & (s["A_lead"] <= band[1])]
        for c, sign in (("C1", 1), ("C2", 1), ("C3", 1)):
            if c == "C3" and unit == ["CDP"]:
                continue
            r = place_conditional(e, n, c, lo=band[0], hi=band[1], **kw)
            r.update({"test": c, "label": label, "kind": kind, "verdict": verdict(r["D_low"], r["D_high"], sign)})
            rows.append(r)
        # C6: log AADT against the place's band mean
        nb = n[(n["A_lead"] > band[0]) & (n["A_lead"] <= band[1]) & (n["aadt"] > 0)]
        m = nb.groupby("geoid")["aadt"].apply(lambda v: np.log(v).mean())
        e6 = e[e["aadt"] > 0].copy()
        e6["p"] = e6["geoid"].map(m)
        e6 = e6.dropna(subset=["p"])
        est, l, h = cluster_boot(e6, lambda d: (np.log(d["aadt"]) - d["p"]).mean())
        rows.append({"test": "C6", "label": label, "kind": kind, "n_stores": len(e6), "n_places": e6["geoid"].nunique(),
                     "D": round(est, 3), "D_low": round(l, 3), "D_high": round(h, 3), "verdict": verdict(l, h, 1),
                     "share": round(math.exp(est), 2) if not np.isnan(est) else np.nan})
        if kind != "Dollar General":
            return
        # C4: newer than in-town stores, difference in shares, cluster bootstrap
        t = s[s["A_lead"] <= 1].assign(edge=0)
        both = pd.concat([e.assign(edge=1), t]).dropna(subset=["auth_year"])
        both["new"] = (both["auth_year"] > 2005).astype(float)

        def diff(d):
            a, b = d[d.edge == 1]["new"], d[d.edge == 0]["new"]
            return a.mean() - b.mean() if len(a) and len(b) else np.nan
        est, l, h = cluster_boot(both, diff)
        rows.append({"test": "C4", "label": label, "kind": kind, "n_stores": int((both.edge == 1).sum()),
                     "n_places": both["geoid"].nunique(), "D": round(est, 3), "D_low": round(l, 3),
                     "D_high": round(h, 3), "verdict": verdict(l, h, 1),
                     "share": round(both[both.edge == 1]["new"].mean(), 3)})
        # C5: among stores with A <= 3, in the band, against the place's random share; lead and loose
        for col in ("A_lead", "A_loose"):
            s3 = s[s[col] <= 3].copy()
            n3 = n[n[col] <= 3].copy()
            n3["y"] = ((n3[col] > 1) & (n3[col] <= 2)).astype(float)
            s3["x"] = ((s3[col] > 1) & (s3[col] <= 2)).astype(float)
            s3["p"] = s3["geoid"].map(n3.groupby("geoid")["y"].mean())
            s3 = s3.dropna(subset=["p"])
            est, l, h = cluster_boot(s3, lambda d: (d["x"] - d["p"]).mean())
            rows.append({"test": f"C5 ({'lead' if col == 'A_lead' else 'loose'})", "label": label, "kind": kind,
                         "n_stores": len(s3), "n_places": s3["geoid"].nunique(), "observed": int(s3["x"].sum()),
                         "expected": round(s3["p"].sum(), 1), "share": round(s3["x"].mean(), 3),
                         "D": round(est, 3), "D_low": round(l, 3), "D_high": round(h, 3), "verdict": verdict(l, h, -1)})

    run("Discovery recut: Virginia small incorporated", ["discovery"], ["small"])
    run("Discovery recut: Virginia small, under 10,000 (sensitivity)", ["discovery"], ["small"], extra=lambda d: d["pop"] < 10000,
        null_extra=lambda d: d["pop"] < 10000)
    run("Set B: six states, small incorporated (PRIMARY)", ["B"], ["small"])
    run("Set A: Virginia CDPs", ["A"], ["CDP"])
    run("Set B: six states, CDPs", ["B"], ["CDP"])
    run("Set B: six states, large incorporated (comparison)", ["B"], ["large"])
    run("Set B: small incorporated, convenience stores (stated contrast)", ["B"], ["small"], kind="convenience")
    # sensitivities on the primary
    run("S1: primary, stores 100 m+ from the edge", ["B"], ["small"], extra=lambda d: d["edge_dist"] > 100)
    run("S1: primary, band 0.75 to 2", ["B"], ["small"], band=(0.75, 2.0))
    run("S3: primary, random points matched by A bin", ["B"], ["small"], abin=True)
    run("S6: primary, without gap-fallback or re-entering places", ["B"], ["small"],
        extra=lambda d: (d["gap_fallback"] != True) & (d["reentries"] == 0),
        null_extra=lambda d: d["gap_fallback"] != True)
    run("Size sensitivity: six states, under 10,000", ["B"], ["small"], extra=lambda d: d["pop"] < 10000,
        null_extra=lambda d: d["pop"] < 10000)
    res = pd.DataFrame(rows)
    # S2 and S4 on the primary, C1 only
    prim_s = st[(st["set"] == "B") & (st["unit"] == "small") & (st["kind"] == "Dollar General") & st["usable"]]
    prim_s = prim_s[(prim_s["A_lead"] > 1) & (prim_s["A_lead"] <= 2)]
    prim_n = nl[(nl["set"] == "B") & (nl["unit"] == "small")]
    extra_rows = []
    for lab, fn in (("S2: C1 with a 100 m road match", lambda d: (d["rank_100"] <= 2).astype(float)),
                    ("S4: C1, crossings on the store's side only", lambda d: (d["rank_side"] <= 2).astype(float))):
        r = place_conditional(prim_s, prim_n, "C1", fn=fn)
        r.update({"test": "C1", "label": lab, "kind": "Dollar General", "verdict": verdict(r["D_low"], r["D_high"], 1)})
        extra_rows.append(r)
    res = pd.concat([res, pd.DataFrame(extra_rows)], ignore_index=True)
    res.to_csv(f"{out}/tests.csv", index=False)
    # classes of every Dollar General, by set and state
    dg = st[st["kind"] == "Dollar General"].copy()
    dg["class"] = np.select([dg["edge_dist"] <= MARGIN_M, dg["A_lead"] <= 1, dg["A_lead"] <= 2],
                            ["on the edge line (margin)", "in town", "edge band"], "beyond A 2")
    dg.groupby(["set", "state", "unit", "class"]).size().rename("stores").to_csv(f"{out}/dg_classes.csv")
    match = st.groupby(["set", "state", "kind"])["aadt"].apply(lambda v: round(v.notna().mean(), 3)).rename("match_rate")
    match.to_csv(f"{out}/match_rates.csv")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(res[["label", "test", "kind", "n_stores", "n_places", "observed", "expected", "share", "share_ci", "D", "D_low",
               "D_high", "verdict"]].to_string())


if __name__ == "__main__":
    if sys.argv[1] == "features":
        features(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    else:
        tests(sys.argv[2])
