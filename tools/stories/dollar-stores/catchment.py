"""Store-first view: who lives closest, by road, to each Dollar General, and where is their center?

Usage: python3 catchment.py <raw-dir> <roads.json> <out-dir> <County> [<County> ...]

For every Dollar General in the window (USDA SNAP, still authorized), every 2020 Census block
is assigned to the Dollar General nearest to it along the road network (OpenStreetMap). That
set of blocks is the store's catchment. For the stores in the named counties it reports:

  catchment people and homes (2020), and their population-weighted center
  how far the store sits from that center, straight and by road
  the road the store is on, the nearest supermarket and the nearest other Dollar General by road
  people living within 5 km by road

Distances by road run along mapped roads from the road point nearest each block's centroid;
the snap from block to road is added. Rivers without a mapped bridge or ferry separate
catchments, as they do on the ground. Water blocks have no people.
"""
import json
import os
import sys
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point

CRS = 32618  # UTM 18N: the Middle Peninsula and Northern Neck
BBOX = (37.15, -77.05, 38.05, -76.15)  # south, west, north, east; matches the Overpass query
NEAR_M = 5000
GROCERY = {"Supermarket", "Super Store", "Large Grocery Store", "Medium Grocery Store"}


def stores(raw):
    with zipfile.ZipFile(os.path.join(raw, "snap.zip")) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), encoding="utf-8-sig", dtype=str)
    df = df[(df["State"].str.strip() == "VA") & (df["End Date"].fillna("").str.strip() == "")].copy()
    lat, lon = df["Latitude"].astype(float), df["Longitude"].astype(float)
    s, w, n, e = BBOX
    df = df[(lat > s) & (lat < n) & (lon > w) & (lon < e)]
    name = df["Store Name"].str.upper()
    df["kind"] = np.where(name.str.contains("DOLLAR GENERAL"), "Dollar General",
                          np.where(df["Store Type"].isin(GROCERY), "grocery", None))
    df = df[df["kind"].notna()]
    g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["Longitude"].astype(float), df["Latitude"].astype(float)),
                         crs=4326).to_crs(CRS)
    g["County"] = g["County"].str.strip().str.title()
    return g


def graph(path):
    d = json.load(open(path))
    xy, rows, cols, w, ways = {}, [], [], [], []
    from pyproj import Transformer
    tf = Transformer.from_crs(4326, CRS, always_xy=True)
    for e in d["elements"]:
        if e.get("type") != "way" or "geometry" not in e:
            continue
        pts = [tf.transform(q["lon"], q["lat"]) for q in e["geometry"]]
        for nid, p in zip(e["nodes"], pts):
            xy[nid] = p
        for a, b, pa, pb in zip(e["nodes"], e["nodes"][1:], pts, pts[1:]):
            rows.append(a)
            cols.append(b)
            w.append(float(np.hypot(pa[0] - pb[0], pa[1] - pb[1])))
        t = e.get("tags", {})
        ways.append({"highway": t.get("highway"), "ref": t.get("ref", ""), "name": t.get("name", ""),
                     "geometry": LineString(pts)})
    ids = np.array(list(xy))
    index = {n: i for i, n in enumerate(ids)}
    r = np.array([index[a] for a in rows])
    c = np.array([index[b] for b in cols])
    m = coo_matrix((np.r_[w, w], (np.r_[r, c], np.r_[c, r])), shape=(len(ids), len(ids))).tocsr()
    pts = np.array([xy[n] for n in ids])
    return m, pts, gpd.GeoDataFrame(ways, crs=CRS)


def main():
    raw, roads_path, out, counties = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    os.makedirs(out, exist_ok=True)
    m, nodes, ways = graph(roads_path)
    tree = cKDTree(nodes)
    st = stores(raw)
    dg = st[st["kind"] == "Dollar General"].reset_index(drop=True)
    gro = st[st["kind"] == "grocery"].reset_index(drop=True)
    s, w, n, e = BBOX
    blocks = gpd.read_file(f"zip://{raw}/tl_2020_51_tabblock20.zip",
                           columns=["GEOID20", "COUNTYFP20", "POP20", "HOUSING20", "ALAND20"],
                           bbox=(w, s, e, n)).to_crs(CRS)
    blocks = blocks[blocks["ALAND20"] > 0].reset_index(drop=True)
    c = blocks.geometry.representative_point()
    bsnap, bnode = tree.query(np.c_[c.x, c.y])
    dsnap, dnode = tree.query(np.c_[dg.geometry.x, dg.geometry.y])
    gsnap, gnode = tree.query(np.c_[gro.geometry.x, gro.geometry.y])

    dist, _, src = dijkstra(m, indices=dnode, min_only=True, return_predecessors=True)
    node_to_store = {nd: i for i, nd in enumerate(dnode)}  # a node shared by two stores keeps one
    blocks["store"] = [node_to_store.get(s_, -1) for s_ in src[bnode]]
    blocks["road_m"] = dist[bnode] + bsnap
    blocks.loc[~np.isfinite(blocks["road_m"]), "store"] = -1

    gdist = dijkstra(m, indices=gnode, min_only=True)
    from_store = dijkstra(m, indices=dnode)  # each store to every node
    rows = []
    for i, srow in dg.iterrows():
        if srow["County"] not in counties:
            continue
        cb = blocks[blocks["store"] == i]
        pop = cb["POP20"].astype(float)
        if pop.sum() == 0:
            continue
        cc = cb.geometry.representative_point()
        cx, cy = (cc.x * pop).sum() / pop.sum(), (cc.y * pop).sum() / pop.sum()
        _, cnode = tree.query([cx, cy])
        near = blocks[(from_store[i][bnode] + bsnap + dsnap[i]) <= NEAR_M]
        others = [from_store[i][dnode[j]] for j in range(len(dg)) if j != i and dnode[j] != dnode[i]]
        wd = ways.distance(srow.geometry)
        way = ways.loc[wd.idxmin()]
        rows.append({
            "store": srow["Store Name"].strip(), "address": f'{srow["Street Number"]} {srow["Street Name"]}',
            "place": srow["City"].strip().title(), "county": srow["County"],
            "authorized": srow["Authorization Date"],
            "on_road": f'{way["ref"] or ""} {way["name"] or ""}'.strip(), "road_class": way["highway"],
            "catch_people": int(pop.sum()), "catch_homes": int(cb["HOUSING20"].sum()),
            "catch_km2": round(cb["ALAND20"].sum() / 1e6, 1),
            "store_to_center_m": round(float(np.hypot(srow.geometry.x - cx, srow.geometry.y - cy))),
            "store_to_center_road_m": round(float(from_store[i][cnode] + dsnap[i])),
            "median_resident_road_m": round(float(np.median(np.repeat(cb["road_m"].values,
                                                                      cb["POP20"].astype(int).values)))),
            "people_within_5km_road": int(near["POP20"].sum()),
            "nearest_grocery_road_m": round(float(gdist[dnode[i]] + dsnap[i])),
            "nearest_other_dg_road_m": round(float(min(others))),
            "center_x": cx, "center_y": cy, "x": srow.geometry.x, "y": srow.geometry.y,
        })
    res = pd.DataFrame(rows)
    res.to_csv(f"{out}/catchments.csv", index=False)
    blocks[["GEOID20", "COUNTYFP20", "POP20", "HOUSING20", "ALAND20", "store", "road_m", "geometry"]].to_file(
        f"{out}/blocks.gpkg")
    dg.drop(columns=[c_ for c_ in dg.columns if c_ not in ("Store Name", "County", "Authorization Date", "geometry")]
            ).to_file(f"{out}/dg.gpkg")
    gro[["Store Name", "geometry"]].to_file(f"{out}/grocery.gpkg")
    ways.to_file(f"{out}/roads.gpkg")
    pd.set_option("display.width", 250)
    print(res.drop(columns=["center_x", "center_y", "x", "y"]).to_string())


if __name__ == "__main__":
    main()
