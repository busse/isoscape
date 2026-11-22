#!/usr/bin/env python3
"""The twelve D areas as a set: what each 1937 form recorded, what stands on that ground now,
and the sources for both. One source for the page's grid (page.py) and the framed menu sheet
(sets/redlining-1937.json, written here for tools/sets/set.py).

    python3 tools/stories/redlining/measure.py     # numbers.json
    python3 tools/stories/redlining/boxes.py       # sets/redlining-1937.json

Numbers are written as {{tokens}} and filled from numbers.json (see `tokens`), never typed. The
forms are paraphrased; each box quotes its form at most once, attributed. The set is editorial:
it has no store section, no print files are made for sale, and it has no plate.

Source keys name entries in the story's Sources section (story.md): `form` is the DSL's
transcription of the 1937 area descriptions, `osm` today's OpenStreetMap, `parcels` the city's
year-built parcels, `measure` numbers.json.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
from areas import NAMES, slug  # noqa: E402
from outlines import CREDIT  # noqa: E402

URL = {
    'form': 'https://github.com/americanpanorama/HOLC_Area_Description_Data',
    'osm': 'https://www.openstreetmap.org/',
    'parcels': 'https://services1.arcgis.com/k3vhq11XkBNeeOfM/ArcGIS/rest/services/Year_of_Construction/FeatureServer/0',
    'ev': 'https://encyclopediavirginia.org/entries/urban-renewal-in-richmond/',
    'lva': 'https://www.lva.virginia.gov/events/exhibitions/online/oe/exhibits/show/mapping-inequality/mapping-inequality-timeline',
    'craig': 'https://uncommonwealth.lva.virginia.gov/blog/2025/11/17/a-brief-history-of-public-housing-in-the-city-of-richmond',
    'mosby': 'https://en.wikipedia.org/wiki/Mosby_Court',
    'rmag': 'https://richmondmagazine.com/news/features/house-of-blackwell/',
}
LABEL = {'form': 'HOLC area descriptions', 'osm': 'OpenStreetMap', 'parcels': 'City of Richmond parcels',
         'ev': 'Gray-Sparks', 'lva': 'LVA timeline', 'craig': 'Craig 2025', 'mosby': 'Wikipedia, Mosby Court',
         'rmag': 'Eshleman 2018', 'measure': 'measured here'}

# at: [lon, lat] the box is centered on (the area's middle); ground: meters across in the menu.
BOXES = [
    {'label': 'D1', 'at': [-77.4395, 37.5520], 'ground': 3000,
     'form': 'The form recorded a population 95% Black, family incomes of $350 to $750 a year, one home in five lived in by its owner, and single houses forty years old or more in poor to very poor repair. It wrote that the population was falling "because of demolition to save taxes."',
     'now': 'The Richmond–Petersburg Turnpike, now I-95 and I-64, runs {{D1_mkm}} km of carriageway through it. Gilpin Court was dedicated on cleared Apostle Town land in 1943, and VCU\'s medical campus now covers most of Navy Hill. The Jackson Ward story follows the Turnpike block by block.',
     'cite_form': ['form'], 'cite_now': ['measure', 'craig', 'ev'],
     'note': 'In 1937: 95% Black, incomes of $350–750, one home in five owner-occupied, houses forty years old and more. Since: Gilpin Court (1943) on Apostle Town; the Turnpike, now I-95 and I-64; VCU\'s medical campus on most of Navy Hill.'},
    {'label': 'D2', 'at': [-77.4421, 37.5912], 'ground': 1500,
     'form': 'The form recorded a population entirely Black, flat ground, frame single houses, family incomes of $250 to $750, and half the homes lived in by their owners. The form for C7, which borders it, faults C7 for lying too near D2.',
     'now': 'Most of what stands is newer than the map: of the {{D2_parcels}} parcels the city dates here, {{D2_1938_77}}% were built between 1938 and 1977. First Baptist Church of Washington Park stands inside the outline.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm'],
     'note': 'In 1937: flat ground, frame houses, a population the form recorded as entirely Black, half of homes owner-occupied. Its neighbor C7\'s form faults C7 for lying too near D2. Since: {{D2_1938_77}}% of the houses the city dates here were built 1938–1977.'},
    {'label': 'D3', 'at': [-77.4300, 37.5880], 'ground': 1800,
     'form': 'The form called the area "mostly woods and bushes," with practically no homes, and recorded the few families there as Black.',
     'now': 'The woods are built over: OpenStreetMap maps {{D3_bldg}} buildings inside the outline, with shops along Laburnum Avenue. The city\'s year-built parcels date only {{D3_parcels}} of them, so when they were built is not measured here.',
     'cite_form': ['form'], 'cite_now': ['osm', 'parcels'],
     'note': 'In 1937 the form found "mostly woods and bushes" and practically no homes. Since: the woods are built over, {{D3_bldg}} buildings in today\'s OpenStreetMap, with shops along Laburnum Avenue.'},
    {'label': 'D4', 'at': [-77.4270, 37.5760], 'ground': 1600,
     'form': 'The form gave D4 the same description as Oak Park, D3, and recorded a population entirely Black, frame single houses, half the homes lived in by their owners, and mortgage money at 60% of appraisal.',
     'now': 'Of the {{D4_parcels}} parcels the city dates here, {{D4_by1937}}% were built by 1937 and {{D4_1938_77}}% between 1938 and 1977. Providence Park lies inside the outline.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm'],
     'note': 'In 1937: described as the same as Oak Park, D3: frame houses, a population it recorded as entirely Black, half owner-occupied. Since: about half the houses the city dates here are from before 1937, most of the rest from 1938–1977.'},
    {'label': 'D5', 'at': [-77.4100, 37.5520], 'ground': 3000,
     'form': 'The form recorded a population 75% Black and growing, frame single houses about fifteen years old in fair repair, one home in three lived in by its owner, and mortgage money at 40% of appraisal.',
     'now': 'Interstate 64 runs {{D5_mkm}} km of carriageway through it. Mosby Court, which opened in 1962 for many of the 1,300 people the 17th Street renewal displaced, stands inside it, with the city jail beside it.',
     'cite_form': ['form'], 'cite_now': ['measure', 'ev', 'mosby', 'osm'],
     'note': 'In 1937: frame houses about fifteen years old, a population the form recorded as 75% Black, one home in three owner-occupied. Since: Mosby Court (1962), for families the 17th Street renewal displaced; I-64 runs {{D5_mkm}} km through it.'},
    {'label': 'D6', 'at': [-77.4070, 37.5320], 'ground': 2800,
     'form': 'The form recorded a population 80% Black "and increasing," flats and single frame houses about forty years old in fair repair, one home in three lived in by its owner, and mortgage money at 50% of appraisal.',
     'now': 'More of 1937 stands here than in any other D area: {{D6_by1937}}% of the {{D6_parcels}} parcels the city dates here were built by 1937. Many of the houses are marked in OpenStreetMap as historic.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm'],
     'note': 'In 1937: flats and frame houses forty years old, a population the form recorded as 80% Black and increasing. Since: more of 1937 stands here than in any other D area; {{D6_by1937}}% of the houses the city dates were built by then.'},
    {'label': 'D7', 'at': [-77.4060, 37.5190], 'ground': 2000,
     'form': 'The form recorded a population 80% Black, single frame houses about fifty years old in bad repair, one home in four lived in by its owner, and no mortgage money at all.',
     'now': 'A 1967 study called Fulton Bottom, about 850 homes, a slum; the 1970 renewal plan would displace about 785 households, and the last homes on Denny Street came down in the late 1980s. Only {{D7_by1937}}% of the parcels the city dates here were built by 1937. Historic Fulton Memorial Park stands on the ground.',
     'cite_form': ['form'], 'cite_now': ['ev', 'parcels', 'osm'],
     'note': 'In 1937: frame houses fifty years old, "bad" repair, no mortgage money, a population the form recorded as 80% Black. Since: called a slum in 1967 and cleared by the late 1980s; Historic Fulton Memorial Park stands on the ground.'},
    {'label': 'D8', 'at': [-77.4560, 37.5420], 'ground': 2600,
     'form': 'The form recorded a population 95% Black, brick flats and frame single and double houses about 25 years old in fair repair, and one home in four lived in by its owner. It wrote that Black families pushed out of D1 were moving into D8\'s oldest houses, displacing white tenants.',
     'now': 'HUD approved the 380-acre Randolph project in 1973; its planning study expected about 1,800 families and individuals to be displaced, for the Downtown Expressway. The Library of Virginia writes that the expressway cut Randolph and Oregon Hill in half. It runs {{D8_mkm}} km of carriageway through D8.',
     'cite_form': ['form'], 'cite_now': ['ev', 'lva', 'measure'],
     'note': 'In 1937: brick flats and frame houses, a population the form recorded as 95% Black, families moving in from D1. Since: the Randolph renewal (1973) and the Downtown Expressway, {{D8_mkm}} km of it through D8, across Randolph and Oregon Hill.'},
    {'label': 'D9', 'at': [-77.4716, 37.5336], 'ground': 1500,
     'form': 'The form recorded vacant land, "practically undeveloped and inaccessible," and expected it to become a D area once built.',
     'now': 'It was built after the map: {{D9_1938_77}}% of the {{D9_parcels}} parcels the city dates here are from 1938 to 1977. Riverview Community Park lies inside the outline.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm'],
     'note': 'In 1937 the form found vacant land, "practically undeveloped and inaccessible," and graded it D before anyone lived there. Since: {{D9_1938_77}}% of the houses the city dates here were built 1938–1977.'},
    {'label': 'D10', 'at': [-77.4570, 37.5190], 'ground': 1700,
     'form': 'The form recorded a population 95% Black, family incomes of $500 to $750, frame single houses about 25 years old in poor repair, and two homes in five lived in by their owners.',
     'now': 'Of the {{D10_parcels}} parcels the city dates here, {{D10_by1937}}% were built by 1937. A Boys and Girls Club and the Fonticello Food Forest stand inside the outline.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm'],
     'note': 'In 1937: frame houses about 25 years old in poor repair, a population the form recorded as 95% Black, two homes in five owner-occupied. Since: about half the houses the city dates here were standing by 1937.'},
    {'label': 'D11', 'at': [-77.4470, 37.5215], 'ground': 1300,
     'form': 'The only D area recorded as white. The form gave its people as "Laboring Whites," with family incomes of $1,500 to $1,800, the highest recorded for any D area, frame and brick houses about twenty years old in fair repair, three homes in five lived in by their owners, and mortgage money at 60% of appraisal.',
     'now': 'Of the {{D11_parcels}} parcels the city dates here, {{D11_since2000}}% were built in 2000 or later, the largest share of any D area. Sacred Heart Catholic Church and the Hull Street post office stand inside the outline.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm'],
     'note': 'In 1937: the one D area the form recorded as white, "Laboring Whites," with the highest incomes of any D area. Since: {{D11_since2000}}% of the buildings the city dates here are from 2000 or later, the most of any D area.'},
    {'label': 'D11.5', 'at': [-77.4430, 37.5125], 'ground': 2000,
     'form': 'The form recorded a population 95% Black, family incomes of $500 to $750, frame single houses about 25 years old, three homes in ten lived in by their owners, and mortgage money at 35 to 40% of appraisal.',
     'now': 'In 1970 the housing authority built 464 scattered-site public housing units here; the neighborhood took its name from James Heyward Blackwell. Of the {{D11_5_parcels}} parcels the city dates, {{D11_5_1938_77}}% were built between 1938 and 1977.',
     'cite_form': ['form'], 'cite_now': ['rmag', 'parcels'],
     'note': 'In 1937: frame houses about 25 years old, a population the form recorded as 95% Black, three homes in ten owner-occupied, mortgage money at 35–40% of appraisal. Since: 464 scattered-site public housing units, built in 1970.'},
]


def tokens(n):
    """{{token}} values from numbers.json: for each area, e.g. D7_by1937 (percent), D7_parcels."""
    t = {}
    for label, a in n['areas'].items():
        k = label.replace('.', '_')
        t[f'{k}_by1937'] = str(round(a['share_by1937'] * 100)) if a['share_by1937'] is not None else 'n/a'
        t[f'{k}_1938_77'] = str(round(a['share_y1938_1977'] * 100)) if a['share_y1938_1977'] is not None else 'n/a'
        t[f'{k}_since2000'] = str(round(a['share_since2000'] * 100)) if a['share_since2000'] is not None else 'n/a'
        t[f'{k}_parcels'] = f"{a['parcels']:,}"
        t[f'{k}_bldg'] = f"{a['buildings_osm']:,}"
        t[f'{k}_km2'] = f"{a['km2']:.1f}"
        t[f'{k}_mkm'] = f"{a['motorway_km']:.1f}"
    return t


def fill(text, t):
    out = re.sub(r'\{\{(\w+)\}\}', lambda m: t[m.group(1)], text)
    assert '{{' not in out
    return out


def cites(keys):
    return '; '.join(f'[{LABEL[k]}](#{"how-we-know" if k == "measure" else "sources"})' for k in keys)


def page_grid(t):
    """The page's section for the set: one figure per D area, each opening in the lightbox."""
    out = []
    for b in BOXES:
        lab = b['label']
        out += ['::: figure',
                f"![{lab}, {NAMES[lab]}, seen from the south today, with the 1937 grades tinted on the ground: the area itself in the red of grade D, its neighbors in the other grades' colors](redlining-d-{slug(lab)}.webp)",
                '',
                f"**{lab}, {NAMES[lab]}.** *What the 1937 form recorded:* {fill(b['form'], t)} [{cites(b['cite_form'])}] "
                f"*What stands there now:* {fill(b['now'], t)} [{cites(b['cite_now'])}] "
                "*How this was made:* today's OpenStreetMap buildings and streets on 2010s lidar, with the 1937 grades as Mapping Inequality digitized them "
                "(CC BY-NC 2.5) tinted under them. Working draft.",
                ':::', '']
    return '\n'.join(out)


def write_set(t):
    boxes = []
    for i, b in enumerate(BOXES, 1):
        boxes.append({'n': i, 'id': slug(b['label']), 'title': f"{b['label']}, {NAMES[b['label']]}",
                      'subtitle': 'Graded D, "Hazardous," in 1937; seen today', 'at': b['at'], 'year': 2026, 'ground': b['ground'],
                      'note': fill(b['note'], t),
                      'sources': [URL[k] for k in dict.fromkeys(b['cite_form'] + b['cite_now']) if k in URL]})
    cfg = {
        'about': 'Editorial: the redlining story\'s twelve D areas as a set, for the story page and its menu sheet only. No store section, no print files for sale, no plate. Written by tools/stories/redlining/boxes.py; do not edit by hand.',
        'slug': 'redlining-1937',
        'title': "Richmond's twelve D areas, 1937 and today",
        'subtitle': "The Home Owners' Loan Corporation's 1937 map of Richmond on the ground, and each area it graded D, \"Hazardous,\" as it stands now",
        'note': "The 1937 map shows buildings standing today that the city dates to 1937 or before, and Jackson Ward's from the 1925 and 1952 Sanborn maps; most others standing then are gone and not drawn. Box notes paraphrase the 1937 area descriptions. Working draft, not for sale.",
        'credit': f"Drawn by Chris Busse with isoscape  ·  {CREDIT}  ·  Map data © OpenStreetMap contributors (ODbL)  ·  Elevation: USGS 3DEP  ·  Year built: City of Richmond",
        'ground_note': 'The ground is today\'s, from lidar, except in Jackson Ward, where the Turnpike\'s trench is filled for 1937.',
        'map': {'region': 'richmond-1937', 'year': 1937},
        'with': {'1937': 'grades', '2026': 'built'},
        'key_heading': "The HOLC's grades:",
        'key': {'items': ['A "Best": green', 'B "Still Desirable": blue', 'C "Definitely Declining": yellow', 'D "Hazardous": red']},
        'box_label': "Richmond's D areas, 1937",
        'boxes': boxes,
    }
    with open(os.path.join(ROOT, 'sets', 'redlining-1937.json'), 'w') as fh:
        json.dump(cfg, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    print('wrote sets/redlining-1937.json')


if __name__ == '__main__':
    n = json.load(open(os.path.join(HERE, 'numbers.json')))
    write_set(tokens(n))
