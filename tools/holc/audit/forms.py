"""Lay out Mapping Inequality's transcription of HOLC area-description forms in the order the
1937 form (NS FORM-8) prints its fields, so each record can be read beside its scan.

    python3 -I forms.py <ad_data.json> [--city Richmond --state VA] [--label D4]
            [--ocr-dir DIR --pages pages.json]   # flag values the OCR text lacks

The transcription file is the lab's `ad_data.json` (or a city subset of it). It is not part of
this repo. With --ocr-dir, each value is looked for in the page's OCR text (tesseract output,
`p-NNN.txt`, page index from pages.json); values not found are printed with "?", as a first
pass only. Every numeric field must still be read on the image.
"""

import argparse
import json
import os
import re

# (form field number, schema key) in the form's printed order.
FIELDS = [
    ("1 city", "name_of_city"), ("1 grade", "security_grade"), ("1 area no.", "area_number"),
    ("2 terrain", "description_of_terrain"), ("3 favorable", "favorable_influences"),
    ("4 detrimental", "detrimental_influences"),
    ("5a type", "occupation_or_type"), ("5b income", "estimated_annual_family_income"),
    ("5c foreign-born nat.", "foreign_born_nationality"), ("5c foreign-born %", "foreign_born_percent"),
    ("5d negro yes/no", "negro_yes_or_no"), ("5d negro %", "negro_percent"),
    ("5e infiltration", "infiltration_of"), ("5f relief", "relief_families"),
    ("5g increasing", "population_increasing"), ("5g decreasing", "population_decreasing"),
    ("6a type", "buildings_type"), ("6b construction", "construction"),
    ("6c age", "average_age"), ("6d repair", "repair"),
    ("7 1929 sale range", "price_range_dollars_1929"), ("7 1929 sale predom", "price_predominating_1929"),
    ("7 1929 rent range", "rent_range_dollars_1929"), ("7 1929 rent predom", "rent_predominating_1929"),
    ("7 low year", "middle_year"),
    ("7 low sale range", "price_range_dollars_middle_year"),
    ("7 low sale predom", "price_predominating_dollars_middle_year"),
    ("7 low sale %", "price_range_percent_middle_year"),
    ("7 low rent range", "rent_range_middle_year"),
    ("7 low rent predom", "rent_predominating_middle_year"),
    ("7 low rent %", "rent_range_percent_middle_year"),
    ("7 current year", "last_year"),
    ("7 current sale range", "price_range_dollars_last_year"),
    ("7 current sale predom", "price_predominating_dollars_last_year"),
    ("7 current sale %", "price_range_percent_last_year"),
    ("7 current rent range", "rent_range_last_year"),
    ("7 current rent predom", "rent_predominating_last_year"),
    ("7 current rent %", "rent_range_percent_last_year"),
    ("7 peak sale year", "peak_sales_year"), ("7 peak sale %", "peak_sales_percent"),
    ("7 peak rent year", "peak_rental_year"), ("7 peak rent %", "peak_rental_percent"),
    ("8a land", "occupancy"), ("8b dwelling units", "dwelling_units"), ("8c home owners", "home_ownership"),
    ("9a sales demand", "sales_demand_characterization"), ("9b sales amount", "sales_demand_amount"),
    ("9c sales activity", "sales_demand_activity"),
    ("10a rental demand", "rental_demand_characterization"), ("10b rental amount", "rental_demand_amount"),
    ("10c rental activity", "rental_demand_activity"),
    ("11a new types", "new_construction_types"), ("11b new amount", "new_construction_amount_last_year"),
    ("12a mortgage purchase", "availability_of_mortgage_funds_home_purchase"),
    ("12b mortgage building", "availability_of_mortgage_funds_home_building"),
    ("13 trend", "trend_of_desirability"), ("14 remarks", "clarifying_remarks"),
    ("15 informant", "information_obtained_from"), ("15 date", "information_obtained_month_and_day"),
    ("15 year", "information_obtained_193x"),
]

# Fields that hold a number (or a number range); every one of these is read on the image.
NUMERIC = {k for _, k in FIELDS if any(s in k for s in (
    "income", "percent", "price", "rent_", "year", "occupancy", "dwelling", "ownership",
    "amount", "mortgage", "average_age"))} | {"area_number"}


def norm(s):
    return re.sub(r"[^0-9a-z]", "", s.lower())


def load(path, city, state):
    rows = json.load(open(path))
    return {r["label"]: r for r in rows if r.get("city") == city and r.get("state") == state}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--city", default="Richmond")
    ap.add_argument("--state", default="VA")
    ap.add_argument("--label", action="append")
    ap.add_argument("--ocr-dir")
    ap.add_argument("--pages", help="JSON: label -> 1-based page number in the PDF")
    ap.add_argument("--compact", action="store_true", help="one line per printed field number")
    a = ap.parse_args()
    recs = load(a.data, a.city, a.state)
    pages = json.load(open(a.pages)) if a.pages else {}
    for label in a.label or sorted(recs):
        r = recs[label]
        ocr = ""
        if a.ocr_dir and label in pages:
            p = os.path.join(a.ocr_dir, "p-%03d.txt" % (pages[label] - 1))
            ocr = norm(open(p, errors="replace").read())
        print("== %s (page %s)" % (label, pages.get(label, "?")))
        line, cur = [], None
        for name, key in FIELDS:
            v = r.get(key, "")
            flag = ""
            if ocr and norm(v) and norm(v) not in ocr:
                flag = "?"
            if not a.compact:
                print("  %-1s %-22s %s" % (flag, name, json.dumps(v)))
                continue
            num = name.split()[0] + (" " + name.split()[1] if name.startswith("7 ") else "")
            if num != cur and line:
                print("  " + cur + ": " + " | ".join(line))
                line = []
            cur = num
            short = name[len(num):].strip() or name
            line.append("%s%s=%s" % (flag, short, json.dumps(v)))
        if a.compact and line:
            print("  " + cur + ": " + " | ".join(line))


if __name__ == "__main__":
    main()
