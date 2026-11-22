"""Run measure.py over many places in one process, skipping places already done and logging a
place that fails instead of stopping (one Virginia CDP raised a GEOS error and ended its batch).

Usage: python3 run_measure.py <work-dir> <osm-dir> <nlcd-dir> <slugs.txt> <failures.txt>
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure  # noqa: E402


def main():
    work, osm, nlcd, slugs, fails = sys.argv[1:6]
    for slug in open(slugs).read().split():
        if os.path.exists(f"{work}/{slug}/null.csv"):
            continue
        sys.argv = ["measure.py", work, osm, nlcd, slug]
        try:
            measure.main()
        except Exception:
            with open(fails, "a") as f:
                f.write(f"{slug}\t{traceback.format_exc().splitlines()[-1]}\n")


if __name__ == "__main__":
    main()
