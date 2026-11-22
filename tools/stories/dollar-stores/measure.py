"""Edge-of-town measures A and B for each town prepared by prep.py.

Usage: python3 measure.py <work-dir> <osm-dir> <nlcd-dir> <town-slug> [...]

<nlcd-dir> holds imperv2021-<slug>.tif (NLCD 2021 percent impervious) and impdesc2021-<slug>.tif
(its descriptor), clipped to the town's window (EPSG:5070). Only non-road impervious counts
(descriptor class 24, "non-road non-energy"): with roads in, an interstate's own blocks chain
the built-up area for kilometers along the corridor (Marion, first try).

A, relative radius
  center   population-weighted mean of 2020 block centroids inside the town limits
  built-up 2020 blocks with at least DENSITY_HU_KM2 housing units per km2 of land, closed by
           CLOSE_M (grow then shrink) so streets and small gaps do not split it, keeping the
           piece that holds the center
  edge     along the bearing from the center to a point, the farthest distance at which the
           ray is still inside the built-up area
  score    distance to the point / edge distance on its bearing (0 center, 1 edge, >1 outside)

B, lines on the map
  inside the incorporated limits; else inside a 2020 Census urban area; else outside both.

Writes <work>/<slug>/{builtup.gpkg,scores.csv,null.csv,roads.gpkg,osm_check.csv,meta.json}.
"""
import json
import math
import os
import sys

import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

CRS = 32617
# Two settings of the built-up edge, to show how much the answer leans on the choice.
# strict: 425 housing units per square mile (164.1 per km2), the 2020 urban-area core threshold
# loose:  200 housing units per square mile (77.2 per km2), closed over wider gaps
# lead:   the loose edge plus any block whose mean impervious cover is 20 percent or more, the
#         Census's impervious test for urban cores
SETTINGS = {"strict": (164.1, 200, None), "loose": (77.2, 400, None), "lead": (77.2, 400, 20)}
# MEASURE_FAST=1 (replication states): the strict edge is not traced (it is a copy of the lead
# edge in the outputs); no replication test uses it. The loose edge is kept for test C5.
FAST = os.environ.get("MEASURE_FAST") == "1"
RAY_M = 20000
NULL_N = int(os.environ.get("NULL_N", "4000"))  # 1500 for the replication states after Maryland, to save time
SEED = 20261121
NULL_ROADS = {"trunk", "primary", "secondary", "tertiary", "trunk_link", "primary_link"}
GAP_FALLBACK = []  # set when the center falls in a gap of the built-up area
NONROAD = 24  # NLCD impervious descriptor: non-road non-energy impervious
CHAIN_IDS = {"Q145168": "Dollar General", "Q5433101": "Family Dollar", "Q5289230": "Dollar Tree"}


def builtup(blocks, center, density, close_m, imperv_min):
    b = blocks[blocks["ALAND20"] > 0].copy()
    b["hu_km2"] = b["HOUSING20"].astype(float) / (b["ALAND20"].astype(float) / 1e6)
    keep_b = b["hu_km2"] >= density
    if imperv_min is not None:
        keep_b |= b["imperv"].fillna(0) >= imperv_min
    dense = unary_union(b[keep_b].geometry.buffer(0))
    closed = dense.buffer(close_m).buffer(-close_m)
    parts = list(getattr(closed, "geoms", [closed]))
    keep = [g for g in parts if g.contains(center)]
    if not keep:  # center fell in a gap: take the nearest piece (logged in meta.json)
        keep = [min(parts, key=lambda g: g.distance(center))]
        GAP_FALLBACK.append(True)
    return keep[0]


def edge_distance(area, center, bearing):
    end = Point(center.x + RAY_M * math.sin(bearing), center.y + RAY_M * math.cos(bearing))
    ray = LineString([center, end])
    try:
        hit = area.intersection(ray)
    except Exception:  # a few CDP edges are degenerate for GEOS (equal endpoints); repair and retry
        from shapely import make_valid, set_precision
        try:
            hit = set_precision(make_valid(area), 0.01).intersection(ray)
        except Exception:
            return float("nan")
    if hit.is_empty:
        return 0.0
    pts = []
    for g in getattr(hit, "geoms", [hit]):
        pts += list(g.coords)
    return max(center.distance(Point(p)) for p in pts)


def score(area, center, p):
    d = center.distance(p)
    b = math.atan2(p.x - center.x, p.y - center.y)
    e = edge_distance(area, center, b)
    return d, e, (d / e if e > 0 else float("inf"))


def line_b(p, place, ua):
    if place.contains(p):
        return "inside limits"
    if ua is not None and ua.contains(p):
        return "urban area, outside limits"
    return "outside both"


def osm_layers(path):
    d = json.load(open(path))
    roads, pois = [], []
    for e in d["elements"]:
        t = e.get("tags", {})
        if "highway" in t and "geometry" in e:
            roads.append({"highway": t["highway"], "ref": t.get("ref", ""),
                          "geometry": LineString([(q["lon"], q["lat"]) for q in e["geometry"]])})
        elif t.get("brand:wikidata") in CHAIN_IDS:
            if e["type"] == "node":
                pt = Point(e["lon"], e["lat"])
            else:
                c = e.get("center") or e["geometry"][0]
                pt = Point(c["lon"], c["lat"])
            pois.append({"chain": CHAIN_IDS[t["brand:wikidata"]], "osm": f'{e["type"]}/{e["id"]}', "geometry": pt})
    r = gpd.GeoDataFrame(roads, crs=4326).to_crs(CRS)
    p = gpd.GeoDataFrame(pois, columns=["chain", "osm", "geometry"], geometry="geometry", crs=4326).to_crs(CRS)
    return r, p


def main():
    work, osm_dir, nlcd_dir, slugs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    rng = np.random.default_rng(SEED)
    for slug in slugs:
        d = os.path.join(work, slug)
        place = gpd.read_file(f"{d}/place.gpkg").geometry.iloc[0]
        blocks = gpd.read_file(f"{d}/blocks.gpkg")
        with rasterio.open(f"{nlcd_dir}/imperv2021-{slug}.tif") as r:
            imp, aff = r.read(1).astype("float32"), r.transform
        with rasterio.open(f"{nlcd_dir}/impdesc2021-{slug}.tif") as r:
            desc = r.read(1)
        imp[(imp > 100) | (desc != NONROAD)] = 0
        zs = zonal_stats(blocks.to_crs(5070), imp, affine=aff, stats=["mean"], nodata=-1)
        blocks["imperv"] = [z["mean"] for z in zs]
        uag = gpd.read_file(f"{d}/ua.gpkg")
        ua = unary_union(uag.geometry) if len(uag) else None
        stores = gpd.read_file(f"{d}/stores.gpkg")
        # a few national SNAP rows have a blank or zero coordinate; they cannot be placed
        stores = stores[np.isfinite(stores.geometry.x) & np.isfinite(stores.geometry.y)]

        inside = blocks[blocks.representative_point().within(place)]
        w = inside["POP20"].astype(float)
        c = inside.geometry.centroid
        if w.sum() > 0:
            center = Point((c.x * w).sum() / w.sum(), (c.y * w).sum() / w.sum())
        else:  # no one counted inside (a few CDPs): the place's own interior point
            center = place.representative_point()
        GAP_FALLBACK.clear()
        if FAST:  # lead and loose only (loose is needed for C5 on the homes-only edge)
            lead_area = builtup(blocks, center, *SETTINGS["lead"])
            areas = {"strict": lead_area, "loose": builtup(blocks, center, *SETTINGS["loose"]), "lead": lead_area}
        else:
            areas = {k: builtup(blocks, center, *v) for k, v in SETTINGS.items()}
        # Rule (set 2026-11-21, before store results were read): a town whose built-up area is
        # under 1 km2 (fewer than ~200 homes per sq mi anywhere) takes its legal limits as part
        # of its edge, so the edge is never smaller than the town.
        lead_rule = "built-up"
        if areas["lead"].area < 1e6:
            areas["lead"] = areas["lead"].union(place)
            lead_rule = "built-up joined with the town limits (built-up under 1 km2)"
        gpd.GeoDataFrame({"setting": list(areas)}, geometry=list(areas.values()), crs=CRS).to_file(f"{d}/builtup.gpkg")
        area = areas["strict"]

        rows = []
        for _, s in stores.iterrows():
            dist, edge3, sc3 = score(areas["lead"], center, s.geometry)
            if FAST:
                edge, sc = edge3, sc3
                _, edge2, sc2 = score(areas["loose"], center, s.geometry)
            else:
                _, edge, sc = score(area, center, s.geometry)
                _, edge2, sc2 = score(areas["loose"], center, s.geometry)
            rows.append({"id": s["Record ID"], "name": s["Store Name"].strip(), "kind": s["kind"],
                         "address": f'{s["Street Number"]} {s["Street Name"]}'.strip(),
                         "auth_year": pd.Timestamp(s["auth"]).year,
                         "x": s.geometry.x, "y": s.geometry.y, "dist_m": round(dist),
                         "edge_m": round(edge), "A": round(sc, 2),
                         "edge_loose_m": round(edge2), "A_loose": round(sc2, 2),
                         "edge_lead_m": round(edge3), "A_lead": round(sc3, 2),
                         "B": line_b(s.geometry, place, ua)})
        pd.DataFrame(rows).to_csv(f"{d}/scores.csv", index=False)

        roads, pois = osm_layers(os.path.join(osm_dir, f"{slug}.json"))
        roads.to_file(f"{d}/roads.gpkg")
        # null model: points spread evenly by length along main roads within the window
        window = place.buffer(8000)
        main_roads = roads[roads["highway"].isin(NULL_ROADS)].clip(window)
        lines = [g for geom in main_roads.geometry for g in getattr(geom, "geoms", [geom])]
        lens = np.array([g.length for g in lines])
        pick = rng.choice(len(lines), NULL_N, p=lens / lens.sum())
        null = []
        for i in pick:
            p = lines[i].interpolate(rng.uniform(0, lines[i].length))
            _, _, sc3 = score(areas["lead"], center, p)
            if FAST:
                sc = sc3
                _, _, sc2 = score(areas["loose"], center, p)
            else:
                _, _, sc = score(area, center, p)
                _, _, sc2 = score(areas["loose"], center, p)
            null.append({"x": p.x, "y": p.y,
                         "A": sc, "A_loose": sc2, "A_lead": sc3, "B": line_b(p, place, ua)})
        pd.DataFrame(null).to_csv(f"{d}/null.csv", index=False)

        # OSM points of the three chains against the nearest SNAP point of the same chain
        chk = []
        for _, o in pois.iterrows():
            same = stores[stores["kind"] == o["chain"]]
            dmin = same.distance(o.geometry).min() if len(same) else None
            chk.append({"chain": o["chain"], "osm": o["osm"], "nearest_snap_m": None if dmin is None else round(dmin)})
        pd.DataFrame(chk, columns=["chain", "osm", "nearest_snap_m"]).to_csv(f"{d}/osm_check.csv", index=False)

        meta = {"center": [center.x, center.y], "pop_in_limits": int(w.sum()),
                "builtup_km2": {k: round(a.area / 1e6, 2) for k, a in areas.items()}, "limits_km2": round(place.area / 1e6, 2), "lead_rule": lead_rule,
                "center_gap_fallback": bool(GAP_FALLBACK),
                # Rule (same date): a town whose built-up area is more than 5 times its limits and
                # over 30 km2 is joined to a larger urban area and has no edge of its own.
                "in_larger_urban_area": bool(areas["lead"].area > 5 * place.area and areas["lead"].area > 30e6),
                "ua": None if ua is None else list(uag["NAME20"]),
                "settings": SETTINGS, "null_n": NULL_N, "seed": SEED}
        json.dump(meta, open(f"{d}/meta.json", "w"), indent=1)
        print(slug, meta)


if __name__ == "__main__":
    main()
