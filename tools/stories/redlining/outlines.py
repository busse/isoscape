"""Which set of 1937 grade outlines the redlining story is built from. This is the one switch.

    USE = 'nara-redraw'  # the owner's choice, November 22, 2026   # or 'nara-redraw'

Every script here (history.py, measure.py, charts.py, views.py, page.py) reads the outlines'
path and credit from this file, and history.py writes the path into the series, so after
changing USE, run history.py, measure.py, charts.py, views.py and page.py again to rebuild the
whole story from the other set. The lab's file stays in data/holc/, outside git.

- `mapping-inequality`: the University of Richmond Digital Scholarship Lab's digitization
  (CC BY-NC 2.5). Free, noncommercial use only, with credit.
- `nara-redraw` (in use): the 48 outlines redrawn in code from the National Archives'
  public-domain scan of the 1937 map (via FRASER), georeferenced to OpenStreetMap street
  corners; tools/holc/ makes them, history/holc/richmond-1937-redrawn.geojson holds them
  (committed). Same properties: `label` (A1 … D11.5), `grade` (A–D), `label_coords` ([lat, lon]).
"""
USE = 'nara-redraw'  # the owner's choice, November 22, 2026

SETS = {
    'mapping-inequality': {
        'path': 'data/holc/richmond-1937.geojson',
        'short': 'Mapping Inequality',
        'credit': "Grades: Home Owners' Loan Corporation, 1937 (National Archives, RG 195), as digitized by "
                  'Mapping Inequality, University of Richmond Digital Scholarship Lab (CC BY-NC 2.5)',
        'license': 'CC BY-NC 2.5',
        'url': 'https://dsl.richmond.edu/panorama/redlining/static/citiesData/VARichmond1937/geojson.json',
        'how': 'the grades as Mapping Inequality digitized them from the 1937 map (CC BY-NC 2.5)',
    },
    'nara-redraw': {
        'path': 'history/holc/richmond-1937-redrawn.geojson',
        'short': "outlines redrawn with Claude from the National Archives scan",
        'credit': "Grades: Home Owners' Loan Corporation, 1937 (National Archives, RG 195, via FRASER); outlines redrawn "
                  'with Claude from the public-domain scan, positioned with OpenStreetMap street corners (ODbL)',
        'license': 'scan public domain; corners © OpenStreetMap contributors, ODbL',
        'url': 'https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/rg195_holc_Richmond_VA.pdf',
        'how': 'the grade outlines redrawn with Claude from the National Archives scan of the 1937 map and positioned with OpenStreetMap street corners (see How we know)',
    },
}

OUTLINES = SETS[USE]
PATH = OUTLINES['path']
CREDIT = OUTLINES['credit']
HOW = OUTLINES['how']
URL = OUTLINES['url']


def load(root):
    """The outlines as GeoJSON features, with the unnumbered pieces (unnumbered.json) split off
    the numbered areas into features of their own: `label` None, `unnumbered` True, grade kept.
    Citywide totals by grade count them; per-area figures leave them out."""
    import json
    import os
    from shapely.geometry import shape, mapping, Point
    from shapely.ops import unary_union
    here = os.path.dirname(os.path.abspath(__file__))
    data = json.load(open(os.path.join(root, PATH)))
    spec = json.load(open(os.path.join(here, 'unnumbered.json')))['pieces'] if USE == 'nara-redraw' else []
    out = []
    for f in data['features']:
        lab = (f['properties'].get('label') or '').strip()
        mine = [p for p in spec if p['in'] == lab]
        if not mine:
            out.append(f)
            continue
        g = shape(f['geometry'])
        parts = list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]
        keep = []
        for part in parts:
            hit = [p for p in mine if part.contains(Point(*p['at']))]
            if hit:
                out.append({'type': 'Feature', 'geometry': mapping(part),
                            'properties': {'label': None, 'grade': f['properties']['grade'], 'unnumbered': True, 'what': hit[0]['what']}})
            else:
                keep.append(part)
        assert len(keep) < len(parts), f'no unnumbered piece found in {lab}'
        out.append({**f, 'geometry': mapping(unary_union(keep))})
    return {'type': 'FeatureCollection', 'features': out}
