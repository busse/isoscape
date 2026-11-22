"""Cut town windows out of a filtered Virginia OSM file into Overpass-style JSON.

Usage: python3 osm_extract.py <roads.osm.pbf>[,<neighbor.osm.pbf>...] <bboxes.txt> <out-dir> [batch]

Several files, comma-separated, are read in turn so a window at a state line gets the
neighboring state's roads too; an element in two files is kept once.

Windows are written in batches (default 60 per pass over the file): holding all of
Virginia's 461 CDP windows at once ran out of memory on the first try.

The input is Geofabrik's Virginia extract filtered on the Mac to drivable highways and the
three chains' brand:wikidata tags (filter recorded in sources.md). bboxes.txt lines are
"<slug> <south,west,north,east> ..." as written for the editorial towns. Output matches what
measure.py reads from Overpass ("out geom"): ways with nodes, geometry and tags.
"""
import json
import os
import sys

import osmium

CHAINS = ("Q145168", "Q5433101", "Q5289230")


def main():
    src, boxes, out = sys.argv[1:4]
    batch = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    os.makedirs(out, exist_ok=True)
    allw = []
    for line in open(boxes):
        slug, bb = line.split()[:2]
        if os.path.exists(f"{out}/{slug}.json"):
            continue
        s, w, n, e = map(float, bb.split(","))
        allw.append((slug, s, w, n, e))
    for i in range(0, len(allw), batch):
        run(src, [(*x, []) for x in allw[i:i + batch]], out)


def run(srcs, wins, out):
    seen = set()
    for src in srcs.split(","):
        run_one(src, wins, seen)
    for slug, *_, acc in wins:
        json.dump({"source": "Geofabrik extracts, filtered", "elements": acc}, open(f"{out}/{slug}.json", "w"))
        print(slug, len(acc))


def run_one(src, wins, seen):
    fp = osmium.FileProcessor(src).with_locations()
    for o in fp:
        key = (o.type_str(), o.id)
        if key in seen:
            continue
        if o.is_way():
            try:
                pts = [(nd.lon, nd.lat) for nd in o.nodes]
            except osmium.InvalidLocationError:
                continue
            ids = [nd.ref for nd in o.nodes]
        elif o.is_node():
            if o.tags.get("brand:wikidata") not in CHAINS:
                continue
            pts, ids = [(o.location.lon, o.location.lat)], None
        else:
            continue
        seen.add(key)
        lons = [p[0] for p in pts]
        lats = [p[1] for p in pts]
        tags = dict(o.tags)
        for slug, s, w, n, e, acc in wins:
            if max(lats) < s or min(lats) > n or max(lons) < w or min(lons) > e:
                continue
            if ids is None:
                acc.append({"type": "node", "id": o.id, "lat": pts[0][1], "lon": pts[0][0], "tags": tags})
            else:
                acc.append({"type": "way", "id": o.id, "nodes": ids, "tags": tags,
                            "geometry": [{"lat": la, "lon": lo} for lo, la in pts]})


if __name__ == "__main__":
    main()
