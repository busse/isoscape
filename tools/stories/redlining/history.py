#!/usr/bin/env python3
"""Write history/richmond-1937.json, the redlining story's dated series, from the streetcar
series it extends and the 1937 grades.

    python3 tools/stories/redlining/history.py

The series is the streetcar city's (history/richmond-streetcars.json: its era rules, curated
features and dates), seen in 1937 and today. Its streetcar lines are put behind a switch
(`streetcars`): their routes are the 1925 ones, and over the 1937 grades their red reads as a
grade. Switches:

- `grades`: the 1937 grades as tinted ground, with a key (`Tint` in src/history.ts), and a label
  on each D area at the point Mapping Inequality labels it.
- `built`: the grades, and the limited-access highways built since drawn over them.

The grades come from Mapping Inequality's Richmond GeoJSON, cached in data/holc/ (CC BY-NC:
never for anything sold; see tools/stories/redlining/sources.md). The labels are read from it
here, so the file is written again whenever the cache changes.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
GRADES = 'data/holc/richmond-1937.geojson'
SOURCE_MI = 'https://dsl.richmond.edu/panorama/redlining/static/citiesData/VARichmond1937/geojson.json'
SOURCE_NARA = 'https://catalog.archives.gov/id/720357'

LEGEND = {
    'title': "The Home Owners' Loan Corporation's grades, 1937, in its own words",
    'labels': ['A "Best"', 'B "Still Desirable"', 'C "Definitely Declining"', 'D "Hazardous"'],
    'source': 'Grades: HOLC, 1937 (National Archives, RG 195), as digitized by Mapping Inequality, University of Richmond Digital Scholarship Lab (CC BY-NC)',
}


def main():
    base = json.load(open(os.path.join(ROOT, 'history/richmond-streetcars.json')))
    grades = json.load(open(os.path.join(ROOT, GRADES)))
    cars = []
    for f in base['features']:
        if f['kind'] == 'streetcar':
            cars.append({**f, 'switch': 'streetcars'})
    labels = []
    for g in grades['features']:
        p = g['properties']
        if (p.get('grade') or '') != 'D':
            continue
        lat, lon = p['label_coords']
        for sw in ('grades', 'built'):
            labels.append({
                'id': f"holc-{p['label'].lower().replace('.', '-')}-{sw}",
                'name': p['label'], 'kind': 'label', 'at': [lon, lat], 'switch': sw,
                'note': "The area's label, at the point Mapping Inequality places it.",
                'sources': [SOURCE_MI],
            })
    tint = {'file': GRADES, 'property': 'grade', 'values': ['A', 'B', 'C', 'D'], 'legend': LEGEND}
    out = {
        'extends': 'history/richmond-streetcars.json',
        'title': "Richmond in 1937, as the Home Owners' Loan Corporation graded it",
        'about': "In 1937 the federal Home Owners' Loan Corporation graded Richmond's residential areas from A to D. "
                 'The redlining story draws its grades on the ground, with the buildings standing then.',
        'epochs': [{'year': 1937, 'title': "The HOLC's grades",
                    'note': "Buildings standing today that the city dates to 1937 or before, and the series' curated features; the grades from Mapping Inequality's digitization of the 1937 map."},
                   {'year': 2026, 'title': 'Today, over the 1937 grades',
                    'note': "Today's buildings and streets, with the 1937 grades under them."}],
        'features': cars + labels,
        'switches': {
            'grades': {'tint': tint, 'note': 'The 1937 grades as tinted ground, with a key.'},
            'built': {'tint': {**tint, 'roads': ['motorway', 'motorway_link']},
                      'note': 'The grades, and the limited-access highways (OSM motorway and motorway_link) drawn over them.'},
        },
        'sources': [SOURCE_MI, SOURCE_NARA],
    }
    path = os.path.join(ROOT, 'history/richmond-1937.json')
    with open(path, 'w') as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write('\n')
    print(f'wrote history/richmond-1937.json: {len(cars)} car lines switched, {len(labels)} labels')


if __name__ == '__main__':
    main()
