#!/usr/bin/env python3
"""Fetch the public files behind the Gaston rain map. Standard library only.

    python3 tools/floods/rain/fetch.py OUTDIR [--only radar|aorc|other|all] [--keep]

Every file comes from a public, anonymous HTTPS endpoint (no account, no key, no form).
Each manifest gives the URL, the expected size in bytes and, where the server gives one,
an MD5 (the S3 ETag of a single-part upload). Files already present with the right size
and checksum are skipped. Nothing secret is printed or sent.

  radar   manifest-radar.json: 268 NEXRAD Level II volumes from KAKQ (Wakefield, VA),
          2004-08-30 11:30 UTC to 2004-08-31 06:30 UTC, about 630 MB, from the Unidata
          NEXRAD bucket on AWS (the older noaa-nexrad-level2 bucket answered 403 here).
  aorc    manifest-aorc.json: the one AORC v1.1 1 km APCP_surface Zarr chunk of 2004 that
          holds metro Richmond on Aug. 30 to 31, with the Zarr metadata (about 0.4 MB).
  other   manifest-other.json: Stage IV hourly, 6-hourly and 24-hourly GRIB1 files from the
          Iowa Environmental Mesonet archive (about 27 MB), the RIC Global Hourly CSV (9 MB),
          GHCN-Daily, NOAA Atlas 14 point answers, HURDAT2, the 3DEP DEM for the watershed
          (9 MB) and Census TIGER boundaries and water (about 16 MB).

The output tree mirrors each URL's host and path under OUTDIR.
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFESTS = {"radar": "manifest-radar.json", "aorc": "manifest-aorc.json", "other": "manifest-other.json"}


def local_path(out, url):
    rest = url.split("://", 1)[1]
    rest = rest.replace("?", "_").replace("&", "_").replace("=", "-")
    return os.path.join(out, rest)


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ok(path, entry):
    if not os.path.exists(path):
        return False
    if entry.get("bytes") and os.path.getsize(path) != entry["bytes"]:
        return False
    if entry.get("md5") and md5(path) != entry["md5"]:
        return False
    return True


def get(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "isoscape-rain-fetch/1"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(path + ".part", "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            os.replace(path + ".part", path)
            return True
        except Exception as e:  # network errors: retry, then report
            err = e
            time.sleep(2 * (attempt + 1))
    print(f"  FAILED {url}: {err}")
    return False


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        sys.exit(2)
    out = args[0]
    only = "all"
    if "--only" in args:
        only = args[args.index("--only") + 1]
    kinds = list(MANIFESTS) if only == "all" else [only]
    bad = 0
    for kind in kinds:
        mpath = os.path.join(HERE, MANIFESTS[kind])
        if not os.path.exists(mpath):
            print(f"{kind}: no manifest at {mpath}, skipped")
            continue
        files = json.load(open(mpath))["files"]
        total = sum(e.get("bytes") or 0 for e in files)
        print(f"{kind}: {len(files)} files, about {total / 1e6:.0f} MB")
        for i, e in enumerate(files):
            p = local_path(out, e["url"])
            if ok(p, e):
                continue
            if not get(e["url"], p) or not ok(p, e):
                bad += 1
                print(f"  check failed: {e['url']}")
            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{len(files)}")
    print("done" if not bad else f"done with {bad} failures")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
