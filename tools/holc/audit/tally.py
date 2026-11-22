"""Tally an audit of HOLC area-description transcriptions against their scans.

    python3 -I tally.py <differences.csv> <ad_data.json> [--city Richmond --state VA]

differences.csv holds one row per field where the scan and the transcription differ (see
README.md for its columns and classes). The transcription file gives the denominators: every
record of the city, and every field of the 1937 form in `forms.FIELDS`. Prints Markdown tables:
differences by class, by field group, by field and by form.
"""

import argparse
import collections
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forms import FIELDS, NUMERIC, load  # noqa: E402

CLASSES = ["a", "b", "c", "d"]
NAMES = {"a": "substantive", "b": "formatting", "c": "ambiguous", "d": "blank vs text"}


def group(key):
    if key in ("security_grade", "area_number", "name_of_city"):
        return "1 heading (city, grade, area no.)"
    if key == "clarifying_remarks" or key in ("description_of_terrain", "favorable_influences",
                                              "detrimental_influences", "trend_of_desirability"):
        return "free text (2-4, 13, 14)"
    if key.startswith("information_obtained"):
        return "15 informant and date"
    if key in NUMERIC:
        return "numeric (5b, 5c-d %, 6c, 7, 8, 9b, 10b, 11b, 12)"
    return "other short text (5, 6, 9a/c, 10a/c, 11a)"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("diffs")
    ap.add_argument("data")
    ap.add_argument("--city", default="Richmond")
    ap.add_argument("--state", default="VA")
    a = ap.parse_args()
    recs = load(a.data, a.city, a.state)
    diffs = list(csv.DictReader(open(a.diffs)))
    keys = [k for _, k in FIELDS]
    nforms, nfields = len(recs), len(keys)
    total = nforms * nfields
    filled = sum(1 for r in recs.values() for k in keys if r.get(k, "").strip(" .-"))

    c = collections.Counter(d["class"] for d in diffs)
    print("Forms: %d. Fields per form: %d. Field slots: %d. Slots with text in the "
          "transcription: %d.\n" % (nforms, nfields, total, filled))
    print(table(["class", "differences", "per 100 slots", "per 100 filled"],
                [[x + " " + NAMES[x], c[x], "%.2f" % (100 * c[x] / total),
                  "%.2f" % (100 * c[x] / filled)] for x in CLASSES]
                + [["all", len(diffs), "%.2f" % (100 * len(diffs) / total),
                    "%.2f" % (100 * len(diffs) / filled)]]))

    sc = collections.Counter(d.get("subclass", "") for d in diffs if d["class"] == "a")
    if any(sc):
        print("\nSubstantive differences by kind\n")
        print(table(["kind", "differences"], sorted(sc.items())))

    print("\nBy grade (a1 = value or reference changed)\n")
    rows = []
    for g in "ABCD":
        labs = [l for l in recs if l[0] == g]
        a1 = [d for d in diffs if d["area"][0] == g and d.get("subclass", "").startswith("a1")]
        hit = {d["area"] for d in a1}
        aa = [d for d in diffs if d["area"][0] == g and d["class"] == "a"]
        rows.append([g, len(labs), len(labs) * nfields, len(aa), len(a1), "%d of %d" % (len(hit), len(labs))])
    print(table(["grade", "forms", "slots", "a (all)", "a1", "forms with an a1"], rows))

    print("\nBy field group (denominator: forms x fields in the group)\n")
    gsize = collections.Counter(group(k) for k in keys)
    gc = collections.defaultdict(collections.Counter)
    for d in diffs:
        gc[group(d["field"])][d["class"]] += 1
    rows = []
    for g in sorted(gsize):
        n = gsize[g] * nforms
        rows.append([g, n] + ["%d (%.1f%%)" % (gc[g][x], 100 * gc[g][x] / n) for x in CLASSES])
    print(table(["group", "slots"] + [x + " " + NAMES[x] for x in CLASSES], rows))

    print("\nBy field (only fields with a difference; denominator %d forms)\n" % nforms)
    fc = collections.defaultdict(collections.Counter)
    for d in diffs:
        fc[d["field"]][d["class"]] += 1
    names = dict((k, n) for n, k in FIELDS)
    rows = [[names[k], k] + [fc[k][x] for x in CLASSES] for k in keys if k in fc]
    print(table(["form field", "schema key"] + CLASSES, rows))

    print("\nBy form (denominator %d fields each)\n" % nfields)
    pc = collections.defaultdict(collections.Counter)
    page = {}
    for d in diffs:
        pc[d["area"]][d["class"]] += 1
        page[d["area"]] = d["page"]
    order = sorted(recs, key=lambda l: (l[0], float(l[1:])))
    rows = [[l, page.get(l, "")] + [pc[l][x] for x in CLASSES] for l in order]
    print(table(["area", "page"] + CLASSES, rows))
    sub = [l for l in order if pc[l]["a"]]
    print("\nForms with at least one substantive difference: %d of %d." % (len(sub), nforms))


if __name__ == "__main__":
    main()
