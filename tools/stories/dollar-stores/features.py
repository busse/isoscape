"""Measure the stated reasons at each edge store and at random edge-band road points.

Usage: python3 features.py <raw-dir> <work-dir> <osm-dir> <nlcd-dir> <stores.csv> <out-dir>

Follows casestudy/2026-11-21-06-edge-stores/hypotheses.md, written before this ran. Edge band:
1 < A <= 2 on the lead edge. R: random main-road points in the same band of the same places,
40 per edge chain store in that place (drawn with SEED). G: edge-band supermarkets, groceries
and convenience stores.
"""
import json
import math
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

CRS = 32617
SEED = 20261121
PER_STORE = 40
CHAINS = ["Dollar General", "Family Dollar", "Dollar Tree"]
APPROACH = {"trunk", "primary", "secondary", "trunk_link", "primary_link"}
REACH_M = 5000
SUPERMARKET = {"Supermarket", "Super Store"}


def road_layers(path):
    d = json.load(open(path))
    tf = Transformer.from_crs(4326, CRS, always_xy=True)
    ways, xy, rows, cols, w = [], {}, [], [], []
    for e in d["elements"]:
        if e.get("type") != "way":
            continue
        pts = [tf.transform(q["lon"], q["lat"]) for q in e["geometry"]]
        t = e.get("tags", {})
        ways.append({"highway": t.get("highway"), "ref": t.get("ref", ""), "nodes": e["nodes"],
                     "geometry": LineString(pts) if len(pts) > 1 else None})
        for nid, p in zip(e["nodes"], pts):
            xy[nid] = p
        for a, b, pa, pb in zip(e["nodes"], e["nodes"][1:], pts, pts[1:]):
            rows.append(a)
            cols.append(b)
            w.append(math.hypot(pa[0] - pb[0], pa[1] - pb[1]))
    ways = gpd.GeoDataFrame([x for x in ways if x["geometry"] is not None], crs=CRS)
    ids = np.array(list(xy))
    ix = {n: i for i, n in enumerate(ids)}
    r = np.array([ix[a] for a in rows])
    c = np.array([ix[b] for b in cols])
    m = coo_matrix((np.r_[w, w], (np.r_[r, c], np.r_[c, r])), shape=(len(ids), len(ids))).tocsr()
    return ways, m, np.array([xy[n] for n in ids]), ix


def junctions(ways, ix, nodes_xy):
    """Nodes where ways carrying different US or state route numbers meet, and the road
    network branches there (degree 3 or more). A road carrying two numbers at once is one way
    and does not make a junction along its length."""
    refs, deg = {}, {}
    for _, wy in ways.iterrows():
        rs = frozenset(x.strip() for x in str(wy["ref"]).split(";") if x.strip() and not x.strip().startswith("SR"))
        ns = wy["nodes"]
        for k, n in enumerate(ns):
            deg[n] = deg.get(n, 0) + (1 if k in (0, len(ns) - 1) else 2)
            if rs:
                refs.setdefault(n, set()).add(rs)
    pts = [nodes_xy[ix[n]] for n, sets in refs.items()
           if len(sets) >= 2 and len(set().union(*sets)) >= 2 and deg.get(n, 0) >= 3]
    return cKDTree(np.array(pts)) if pts else None


def sample(path, xs, ys, size=1):
    with rasterio.open(path) as r:
        tf = Transformer.from_crs(CRS, r.crs, always_xy=True)
        a = r.read(1).astype(float)
        out = []
        for x, y in zip(xs, ys):
            X, Y = tf.transform(x, y)
            row, col = r.index(X, Y)
            win = a[max(row - size, 0):row + size + 1, max(col - size, 0):col + size + 1]
            win = win[win <= 100]
            out.append(float(win.mean()) if win.size else np.nan)
    return np.array(out)


def main():
    raw, work, osm_dir, nlcd, stores_path, out = sys.argv[1:7]
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(SEED)
    st = pd.read_csv(stores_path)
    st = st[~st["metro"]]
    low = float(os.environ.get("EDGE_LOW", "1"))  # 0.75 for the sensitivity check in hypotheses.md
    edge = st[(st["A_lead"] > low) & (st["A_lead"] <= 2)].copy()
    edge["group"] = np.where(edge["kind"].isin(CHAINS), edge["kind"],
                             np.where(edge["kind"] == "convenience", "convenience", "grocery"))
    edge = edge[edge["kind"].isin(CHAINS + ["grocery", "convenience"])]
    snap_types = None
    res = []
    for town, ge in edge.groupby("town"):
        d = f"{work}/{town}"
        m = json.load(open(f"{d}/meta.json"))
        cx, cy = m["center"]
        place = gpd.read_file(f"{d}/place.gpkg").geometry.iloc[0]
        built = gpd.read_file(f"{d}/builtup.gpkg")
        lead = built[built["setting"] == "lead"].geometry.iloc[0]
        nchain = int(ge["kind"].isin(CHAINS).sum())
        nl = pd.read_csv(f"{d}/null.csv")
        nl = nl[(nl["A_lead"] > low) & (nl["A_lead"] <= 2)]
        pts = ge[["x", "y", "kind", "group", "id", "auth_year", "A_lead"]].copy()
        if nchain and len(nl):
            r = nl.sample(PER_STORE * nchain, replace=len(nl) < PER_STORE * nchain, random_state=int(rng.integers(1e9)))
            pts = pd.concat([pts, pd.DataFrame({"x": r.x, "y": r.y, "kind": "random", "group": "random",
                                                "id": None, "auth_year": None, "A_lead": r.A_lead})])
        pts["town"] = town
        ways, mat, nxy, ix = road_layers(f"{osm_dir}/{town}.json")
        appr = ways[ways["highway"].isin(APPROACH)]
        crossing = appr[appr.intersects(lead.boundary)]
        appr_zone = unary_union(crossing.buffer(60)) if len(crossing) else None
        jt = junctions(ways[ways["highway"].isin(APPROACH | {"tertiary"})], ix, nxy)
        P = gpd.GeoSeries(gpd.points_from_xy(pts.x, pts.y), crs=CRS)
        pts["on_approach_road"] = P.within(appr_zone).values if appr_zone is not None else False
        pts["near_junction"] = (jt.query(np.c_[pts.x, pts.y])[0] <= 250) if jt is not None else False
        pts["outside_limits"] = ~P.within(place).values
        i01 = sample(f"{nlcd}/imperv2001-{town}.tif", pts.x, pts.y)
        i21 = sample(f"{nlcd}/imperv2021-{town}.tif", pts.x, pts.y)
        pts["imperv2001"], pts["imperv2021"] = i01, i21
        pts["greenfield"] = (i01 < 10) & (i21 >= 20)
        # people within 5 km by road, and the share of them outside the built-up area
        blocks = gpd.read_file(f"{d}/blocks.gpkg")
        blocks = blocks[blocks["POP20"] > 0]
        bc = blocks.geometry.representative_point()
        # snap only to the main connected road network, so a store beside a stray fragment of
        # road (a driveway mapped on its own) is not cut off from everyone (fixed after the
        # first run left 10 of 48 chain stores with no one within reach)
        from scipy.sparse.csgraph import connected_components
        _, lab = connected_components(mat, directed=False)
        keep = np.flatnonzero(lab == np.bincount(lab).argmax())
        tree = cKDTree(nxy[keep])
        bs, bn = tree.query(np.c_[bc.x, bc.y])
        ps, pn = tree.query(np.c_[pts.x, pts.y])
        bn, pn = keep[bn], keep[pn]
        dist = dijkstra(mat, indices=pn, limit=REACH_M)
        inside = bc.within(lead).values
        popv = blocks["POP20"].values.astype(float)
        reach, rural = [], []
        for k in range(len(pts)):
            dd = dist[k][bn] + bs + ps[k]
            near = dd <= REACH_M
            tot = popv[near].sum()
            reach.append(tot)
            rural.append(popv[near & ~inside].sum() / tot if tot else np.nan)
        pts["people_5km_road"], pts["share_outside_builtup"] = reach, rural
        # angle at the center between the point and the nearest supermarket
        if snap_types is None:
            import zipfile
            with zipfile.ZipFile(f"{raw}/snap.zip") as z:
                sn = pd.read_csv(z.open(z.namelist()[0]), encoding="utf-8-sig", dtype=str)
            sn = sn[(sn["State"].str.strip() == "VA") & (sn["End Date"].fillna("").str.strip() == "")
                    & sn["Store Type"].isin(SUPERMARKET)]
            g = gpd.GeoSeries(gpd.points_from_xy(sn["Longitude"].astype(float), sn["Latitude"].astype(float)),
                              crs=4326).to_crs(CRS)
            snap_types = pd.DataFrame({"x": g.x.values, "y": g.y.values})
        sm = snap_types[(abs(snap_types.x - cx) < 15000) & (abs(snap_types.y - cy) < 15000)]
        if len(sm):
            t2 = cKDTree(np.c_[sm.x, sm.y])
            _, k2 = t2.query(np.c_[pts.x, pts.y])
            a1 = np.arctan2(pts.x.values - cx, pts.y.values - cy)
            a2 = np.arctan2(sm.x.values[k2] - cx, sm.y.values[k2] - cy)
            diff = np.degrees(np.abs((a1 - a2 + np.pi) % (2 * np.pi) - np.pi))
            pts["angle_to_supermarket"] = diff
            # exploratory, added after the first run (not in hypotheses.md)
            pts["supermarket_m"] = t2.query(np.c_[pts.x, pts.y])[0]
        else:
            pts["angle_to_supermarket"] = np.nan
            pts["supermarket_m"] = np.nan
        res.append(pts)
        print(town, nchain, len(pts), file=sys.stderr)
    allp = pd.concat(res, ignore_index=True)
    allp.to_csv(f"{out}/edge_points.csv", index=False)


if __name__ == "__main__":
    main()
