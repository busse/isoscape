"""Cut the statewide inputs down to the test towns.

Usage: python3 prep.py <raw-dir> <work-dir> <town> [<town> ...]

Writes <work-dir>/<slug>/{place,blocks,ua,stores}.gpkg and bbox.json (WGS84, for Overpass).
All geometry is reprojected to UTM 17N (EPSG:32617), meters.
"""
import json
import os
import sys
import zipfile

import geopandas as gpd
import pandas as pd

CRS = 32617
REACH_M = 8000  # study window: 8 km around the town's limits

CHAINS = {
    "DOLLAR GENERAL": "Dollar General",
    "FAMILY DOLLAR": "Family Dollar",
    "DOLLAR TREE": "Dollar Tree",
}
GROCERY = {"Supermarket", "Super Store", "Large Grocery Store", "Medium Grocery Store"}
PHARMACY = ("CVS", "WALGREENS", "RITE AID")


def kind(row):
    name = row["Store Name"].upper()
    for k, v in CHAINS.items():
        if k in name:
            return v
    if any(name.startswith(p) for p in PHARMACY):
        return "pharmacy"
    if row["Store Type"] in GROCERY:
        return "grocery"
    if row["Store Type"] == "Convenience Store":
        return "convenience"
    return None


def load_snap(raw):
    with zipfile.ZipFile(os.path.join(raw, "snap.zip")) as z:
        name = z.namelist()[0]
        df = pd.read_csv(z.open(name), encoding="utf-8-sig", dtype=str)
    df = df[(df["State"].str.strip() == "VA") & (df["End Date"].fillna("").str.strip() == "")].copy()
    df["kind"] = df.apply(kind, axis=1)
    df = df[df["kind"].notna()]
    df["auth"] = pd.to_datetime(df["Authorization Date"], format="%m/%d/%Y")
    g = gpd.GeoDataFrame(
        df[["Record ID", "Store Name", "Store Type", "Street Number", "Street Name", "City", "kind", "auth"]],
        geometry=gpd.points_from_xy(df["Longitude"].astype(float), df["Latitude"].astype(float)),
        crs=4326,
    )
    return g.to_crs(CRS)


def main():
    raw, work, towns = sys.argv[1], sys.argv[2], sys.argv[3:]
    places = gpd.read_file(f"zip://{raw}/tl_2024_51_place.zip").to_crs(CRS)
    ua = gpd.read_file(f"zip://{raw}/tl_2024_us_uac20.zip")
    ua = ua[ua["NAME20"].str.contains(", VA")].to_crs(CRS)
    snap = load_snap(raw)
    blocks = None
    for town in towns:
        p = places[places["NAMELSAD"] == town]
        assert len(p) == 1, (town, len(p))
        slug = p["NAME"].iloc[0].lower().replace(" ", "-")
        d = os.path.join(work, slug)
        os.makedirs(d, exist_ok=True)
        window = p.geometry.iloc[0].buffer(REACH_M)
        win = gpd.GeoDataFrame(geometry=[window], crs=CRS)
        if blocks is None:
            blocks = gpd.read_file(f"zip://{raw}/tl_2020_51_tabblock20.zip",
                                   columns=["GEOID20", "POP20", "HOUSING20", "ALAND20"]).to_crs(CRS)
        b = gpd.sjoin(blocks, win, predicate="intersects").drop(columns="index_right")
        p.to_file(f"{d}/place.gpkg")
        b.to_file(f"{d}/blocks.gpkg")
        gpd.sjoin(ua, win, predicate="intersects").drop(columns="index_right").to_file(f"{d}/ua.gpkg")
        s = snap[snap.within(window)]
        s.to_file(f"{d}/stores.gpkg")
        w, s_, e, n = win.to_crs(4326).total_bounds
        a = win.to_crs(5070).buffer(500).total_bounds
        json.dump({"town": town, "bbox": [s_, w, n, e], "bbox5070": [round(v, -1) for v in a]},
                  open(f"{d}/bbox.json", "w"))
        print(town, "blocks", len(b), "stores", s["kind"].value_counts().to_dict())


if __name__ == "__main__":
    main()
