"""Which set of 1937 grade outlines the redlining story is built from. This is the one switch.

    USE = 'mapping-inequality'   # or 'nara-redraw'

Every script here (history.py, measure.py, charts.py, views.py, page.py) reads the outlines'
path and credit from this file, and history.py writes the path into the series, so after
changing USE, run history.py, measure.py, charts.py, views.py and page.py again to rebuild the
whole story from the other set. Both files live in data/holc/, outside git.

- `mapping-inequality`: the University of Richmond Digital Scholarship Lab's digitization
  (CC BY-NC 2.5). Free, noncommercial use only, with credit.
- `nara-redraw`: outlines redrawn from the National Archives' public-domain scan of the 1937
  map (being made separately for comparison). Must carry the same properties: `label` (A1 …
  D11.5), `grade` (A–D) and `label_coords` ([lat, lon]).
"""
USE = 'mapping-inequality'

SETS = {
    'mapping-inequality': {
        'path': 'data/holc/richmond-1937.geojson',
        'short': 'Mapping Inequality',
        'credit': "Grades: Home Owners' Loan Corporation, 1937 (National Archives, RG 195), as digitized by "
                  'Mapping Inequality, University of Richmond Digital Scholarship Lab (CC BY-NC 2.5)',
        'license': 'CC BY-NC 2.5',
    },
    'nara-redraw': {
        'path': 'data/holc/richmond-1937-redrawn.geojson',
        'short': 'the National Archives scan',
        'credit': "Grades: Home Owners' Loan Corporation, 1937 (National Archives, RG 195), outlines redrawn from "
                  'the public-domain scan; method after Mapping Inequality, University of Richmond Digital Scholarship Lab',
        'license': 'public domain (scan); redrawn outlines',
    },
}

OUTLINES = SETS[USE]
PATH = OUTLINES['path']
CREDIT = OUTLINES['credit']
