#!/usr/bin/env python3
"""The twelve D areas: what each 1937 form recorded, what stands on that ground now, and the
sources for both, for the page's figures (page.py). The owner chose (November 22, 2026) to keep
the set as the page's figures, with no framed sheet.

    python3 tools/stories/redlining/measure.py     # numbers.json
    python3 tools/stories/redlining/boxes.py       # prints the figures' Markdown

Numbers are written as {{tokens}} and filled from numbers.json (see `tokens`), never typed. The
forms are paraphrased; each box quotes its form at most once, attributed, checked on the scan.

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
from areas import title as area_title, slug  # noqa: E402
from outlines import CREDIT, HOW  # noqa: E402
from fmt import pct  # noqa: E402

URL = {
    'form': 'https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/ad_RichmondVA.pdf',
    'osm': 'https://www.openstreetmap.org/',
    'parcels': 'https://services1.arcgis.com/k3vhq11XkBNeeOfM/ArcGIS/rest/services/Year_of_Construction/FeatureServer/0',
    'ev': 'https://encyclopediavirginia.org/entries/urban-renewal-in-richmond/',
    'evb': 'https://encyclopediavirginia.org/entries/blackwell-james-h-ca-1864-1931/',
    'lva': 'https://www.lva.virginia.gov/events/exhibitions/online/oe/exhibits/show/mapping-inequality/mapping-inequality-timeline',
    'craig': 'https://uncommonwealth.lva.virginia.gov/blog/2025/11/17/a-brief-history-of-public-housing-in-the-city-of-richmond',
    'mosby': 'https://projects.propublica.org/hud/properties/VA007000008',
    'rmag': 'https://richmondmagazine.com/news/features/house-of-blackwell/',
    'dhr': 'https://www.dhr.virginia.gov/press-release-posts/washington-park-historic-african-american-community-richmond-highway-marker/',
    'civic': 'https://www.rva.gov/sites/default/files/Planning/PDFDocuments/UsefulLinks/CivicGroupMaps/',
    'valentine': 'https://thevalentine.org/wp-content/uploads/2024/12/Valentine-self-guided-tour-Oregon-Hill-WEB.pdf',
    'fulton': 'https://news.vcu.edu/article/via_online_oral_history_project_residents_of_demolished_africanamerican',
}
# Each key names an entry in the story's Sources section (story.md); page.py points the link at it.
LABEL = {'form': 'FRASER, Richmond area descriptions', 'osm': 'OpenStreetMap', 'parcels': 'City of Richmond parcels',
         'ev': 'Gray-Sparks', 'evb': 'Kneebone, Blackwell', 'lva': 'LVA timeline', 'craig': 'Craig 2025', 'mosby': 'HUD via ProPublica',
         'rmag': 'Eshleman 2018', 'dhr': 'DHR, Washington Park', 'civic': 'City of Richmond civic-group maps',
         'valentine': 'The Valentine, Oregon Hill', 'fulton': 'Historic Fulton Oral History Project', 'measure': 'measured here'}

# at: [lon, lat] the box is centered on (the area's middle); ground: meters across in the menu.
# `form` paraphrases the 1937 form (read on the scan; at most one short quotation each); `now`
# says what stands there, naming who built or cleared where the sources name them.
BOXES = [
    {'label': 'D1', 'at': [-77.4395, 37.5520], 'ground': 3000,
     'form': 'A population 95% Black, family incomes of $350 to $750 a year, one home in five lived in by its owner, and single houses forty years old and more in poor to very poor repair. It wrote that the population was falling "because of demolition to save taxes."',
     'now': 'I-95 and I-64 run {{D1_mkm}} km of carriageway through it. The Richmond Housing Authority opened Gilpin Court, public housing, on cleared Apostle Town land in 1943, and VCU\'s medical campus now covers most of Navy Hill. About {{carver_D1}}% of D1 lies west of Belvidere Street and north of Broad Street, in today\'s Carver.',
     'cite_form': ['form'], 'cite_now': ['measure', 'craig', 'ev', 'civic'],
     'note': 'In 1937: 95% Black, incomes of $350–750, one home in five owner-occupied, houses forty years old and more. Since: Gilpin Court (1943) on Apostle Town; the Turnpike, now I-95 and I-64; VCU\'s medical campus on most of Navy Hill.'},
    {'label': 'D2', 'at': [-77.4421, 37.5912], 'ground': 1500,
     'form': 'Flat ground, frame single houses, a population entirely Black, family incomes of $350 to $750, and half the homes lived in by their owners. The form for C7, which borders it, faults C7 for lying too near D2, and the form for D4 calls this area Oak Park.',
     'now': 'The state\'s historical marker for Washington Park says emancipated African Americans settled here after the Civil War, and that two planned developments, Oak Park and Washington Park, later drew many residents. Of the {{D2_parcels}} parcels the city dates here, {{D2_1938_77}}% were built between 1938 and 1977. First Baptist Church of Washington Park stands inside the outline.',
     'cite_form': ['form'], 'cite_now': ['dhr', 'parcels', 'osm'],
     'note': 'In 1937: flat ground, frame houses, a population the form recorded as entirely Black, half of homes owner-occupied. Its neighbor C7\'s form faults C7 for lying too near D2, and D4\'s form calls D2 Oak Park. Since: {{D2_1938_77}}% of the houses the city dates here were built 1938–1977.'},
    {'label': 'D3', 'at': [-77.4300, 37.5880], 'ground': 1800,
     'form': 'The form called the area "Mostly woods and bushes", with practically no homes, and recorded the few families there as Black.',
     'now': 'The woods are built over: OpenStreetMap maps {{D3_bldg}} buildings inside the outline, with shops along Laburnum Avenue. The city\'s year-built parcels cover only {{D3_parcels}} lots here, so when the buildings went up is not measured. The pale green field to the northwest is Forest Lawn Cemetery, in the drawing\'s color for parks and cemeteries; most of it lies outside the 1937 grades, and none of it is A.',
     'cite_form': ['form'], 'cite_now': ['osm', 'parcels'],
     'note': 'In 1937 the form found "Mostly woods and bushes" and practically no homes. Since: the woods are built over, {{D3_bldg}} buildings in today\'s OpenStreetMap, with shops along Laburnum Avenue.'},
    {'label': 'D4', 'at': [-77.4270, 37.5760], 'ground': 1600,
     'form': 'Its only remark reads "Same as Oak Park, D2." It repeats D2\'s figures for values, rents, owners and mortgage money, and recorded a population entirely Black, frame single houses, and half the homes lived in by their owners.',
     'now': 'Of the {{D4_parcels}} parcels the city dates here, {{D4_by1937}}% were built by 1937 and {{D4_1938_77}}% between 1938 and 1977. Hunt and Hazelhurst Avenues lie in the area the City of Richmond\'s civic-group map gives the Providence Park Civic Association.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'civic'],
     'note': 'In 1937: described as the same as Oak Park, D2: frame houses, a population it recorded as entirely Black, half owner-occupied. Since: about half the houses the city dates here are from before 1937, most of the rest from 1938–1977.'},
    {'label': 'D5', 'at': [-77.4100, 37.5520], 'ground': 3000,
     'form': 'A population 75% Black and growing, frame single houses about fifteen years old in fair repair, one home in three lived in by its owner, and mortgage money reported at 40% of appraisal.',
     'now': 'Interstate 64 runs {{D5_mkm}} km of carriageway through it. Mosby Court, public housing, stands inside it. It opened in 1962, and many of the 1,300 people the City\'s 17th Street Urban Renewal Project displaced moved there.',
     'cite_form': ['form'], 'cite_now': ['measure', 'ev', 'mosby'],
     'note': 'In 1937: frame houses about fifteen years old, a population the form recorded as 75% Black, one home in three owner-occupied. Since: Mosby Court (1962), where many families the 17th Street renewal displaced moved; I-64 runs {{D5_mkm}} km through it.'},
    {'label': 'D6', 'at': [-77.4070, 37.5320], 'ground': 2800,
     'form': 'The form is headed Church Hill and bounded by Venable Street, Nine Mile Road, Oakwood Cemetery, the Southern Railway, the river and 17th Street. It recorded a population 80% Black "and increasing", flats and single frame houses about forty years old in fair repair, one home in three lived in by its owner, and mortgage money reported at 50% of appraisal.',
     'now': 'More of 1937 stands here than in any other D area: {{D6_by1937}}% of the {{D6_parcels}} parcels the city dates here were built by 1937. OpenStreetMap marks {{D6_hist}} of the {{D6_osm}} building outlines in the area as historic or heritage. The area takes in parts of what the city\'s maps call Church Hill North and Union Hill.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm', 'civic'],
     'note': 'In 1937: flats and frame houses forty years old, a population the form recorded as 80% Black and increasing. Since: more of 1937 stands here than in any other D area; {{D6_by1937}}% of the houses the city dates were built by then.'},
    {'label': 'D7', 'at': [-77.4060, 37.5190], 'ground': 2000,
     'form': 'The form is headed Fulton and bounded by Nicholson Street, National Cemetery Road and Williamsburg Avenue. It recorded a population 80% Black, single frame houses about fifty years old in bad repair, and one home in four lived in by its owner, and its field for mortgage funds for home purchase reads "None".',
     'now': 'In 1967 a study sponsored by the Richmond Redevelopment and Housing Authority (RRHA) designated Fulton Bottom, a neighborhood of about 850 homes, churches, schools and stores, a "slum". The 1970 renewal plan would displace about 785 households. The RRHA began buying and razing Fulton properties in the early 1970s, and the last homes on Denny Street came down in the late 1980s. Only {{D7_by1937}}% of the parcels the city dates here were built by 1937. Historic Fulton Memorial Park stands on the ground, and former residents tell the neighborhood\'s story in the Historic Fulton Oral History Project.',
     'cite_form': ['form'], 'cite_now': ['ev', 'parcels', 'osm', 'fulton'],
     'note': 'In 1937: frame houses fifty years old, "bad" repair, a population the form recorded as 80% Black. Since: labeled a "slum" in an RRHA-sponsored study in 1967 and cleared by the late 1980s; Historic Fulton Memorial Park stands on the ground.'},
    {'label': 'D8', 'at': [-77.4560, 37.5420], 'ground': 2600,
     'form': 'A population 95% Black, brick flats and frame single and double houses about 25 years old in fair repair, one home in four lived in by its owner, and mortgage money reported at 50% of appraisal. The form described Black families leaving D1 as displacing white residents, and called D8\'s houses "aged and obsolete structures".',
     'now': 'HUD approved the 380-acre Randolph Urban Renewal Project in 1973; its planning study expected about 1,800 families and individuals to be displaced, and Encyclopedia Virginia gives its aims as "slum clearance" and the Downtown Expressway. The expressway runs {{D8_mkm}} km of carriageway through D8, and the Library of Virginia writes that it cut the Randolph and Oregon Hill neighborhoods in half. About a quarter of D8 ({{oh_lo}} to {{oh_hi}}%) lies in the Oregon Hill Historic District as the Valentine bounds it, a neighborhood the Valentine describes as white and blue-collar by the mid-1900s; the form\'s figures are for D8 as a whole.',
     'cite_form': ['form'], 'cite_now': ['ev', 'lva', 'measure', 'valentine'],
     'note': 'In 1937: brick flats and frame houses, a population the form recorded as 95% Black. Since: the Randolph renewal (1973) and the Downtown Expressway, {{D8_mkm}} km of it through D8.'},
    {'label': 'D9', 'at': [-77.4716, 37.5336], 'ground': 1500,
     'form': 'The form is headed Riverview. It recorded vacant land, "Practically undeveloped and inaccessible", and expected it to become a D area once built.',
     'now': 'It was built after the map: {{D9_1938_77}}% of the {{D9_parcels}} parcels the city dates here are from 1938 to 1977. Riverview Community Park lies inside the outline.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm'],
     'note': 'In 1937 the form found vacant land, "Practically undeveloped and inaccessible", and graded it D before anyone lived there. Since: {{D9_1938_77}}% of the houses the city dates here were built 1938–1977.'},
    {'label': 'D10', 'at': [-77.4570, 37.5190], 'ground': 1700,
     'form': 'A population 95% Black, family incomes of $500 to $750, frame single houses 25 years old and older in poor repair, two homes in five lived in by their owners, and mortgage money reported at 50% of appraisal.',
     'now': 'Of the {{D10_parcels}} parcels the city dates here, {{D10_by1937}}% were built by 1937. A Boys and Girls Club and the Fonticello Food Forest stand inside the outline, which lies in the area the city\'s civic-group map gives the Swansboro association.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm', 'civic'],
     'note': 'In 1937: frame houses 25 years old and older in poor repair, a population the form recorded as 95% Black, two homes in five owner-occupied. Since: about half the houses the city dates here were standing by 1937.'},
    {'label': 'D11', 'at': [-77.4470, 37.5215], 'ground': 1300,
     'form': 'The only D area recorded as white; the form is headed South Richmond. It gave its people as "Laboring Whites", with family incomes of $1,500 to $1,800, the highest recorded for any D area, frame and brick houses about twenty years old in fair repair, three homes in five lived in by their owners, and mortgage money reported at 60% of appraisal.',
     'now': 'Of the {{D11_parcels}} parcels the city dates here, {{D11_since2000}}% were built in 2000 or later, the largest share of any D area. Sacred Heart Catholic Church and the Hull Street post office stand inside the outline.',
     'cite_form': ['form'], 'cite_now': ['parcels', 'osm'],
     'note': 'In 1937: the one D area the form recorded as white, "Laboring Whites", with the highest incomes of any D area. Since: {{D11_since2000}}% of the buildings the city dates here are from 2000 or later, the most of any D area.'},
    {'label': 'D11.5', 'at': [-77.4430, 37.5125], 'ground': 2000,
     'form': 'A population 95% Black, family incomes of $500 to $750, frame single houses about 25 years old, about a third of the homes (35%) lived in by their owners, and mortgage money reported at 35 to 40% of appraisal.',
     'now': 'The neighborhood is named, through the school that bore his name from 1951, for James H. Blackwell, principal of Manchester\'s first school for Black students from 1888; when Richmond absorbed Manchester in 1910, the city allowed no Black principals, and he was made a teacher. In 1970, 464 scattered-site public housing units were built in the neighborhood. Of the {{D11_5_parcels}} parcels the city dates, {{D11_5_1938_77}}% were built between 1938 and 1977.',
     'cite_form': ['form'], 'cite_now': ['evb', 'rmag', 'parcels'],
     'note': 'In 1937: frame houses about 25 years old, a population the form recorded as 95% Black, 35% of homes owner-occupied, mortgage money at 35–40% of appraisal. Since: 464 scattered-site public housing units, built in 1970.'},
]


def tokens(n):
    """{{token}} values from numbers.json: for each area, e.g. D7_by1937 (percent), D7_parcels."""
    t = {}
    for label, a in n['areas'].items():
        k = label.replace('.', '_')
        t[f'{k}_by1937'] = pct(a['share_by1937']) if a['share_by1937'] is not None else 'n/a'
        t[f'{k}_1938_77'] = pct(a['share_y1938_1977']) if a['share_y1938_1977'] is not None else 'n/a'
        t[f'{k}_since2000'] = pct(a['share_since2000']) if a['share_since2000'] is not None else 'n/a'
        t[f'{k}_parcels'] = f"{a['parcels']:,}"
        t[f'{k}_bldg'] = f"{a['buildings_osm']:,}"
        t[f'{k}_km2'] = f"{a['km2']:.1f}"
        t[f'{k}_mkm'] = f"{a['motorway_km']:.1f}"
    t['D1_tp'] = f"{n['motorway_in_d1_km']['turnpike']:.1f}"
    t['pp_D4'] = pct(n['osm_checks']['providence_park_share_in_D4'])
    t['D6_hist'] = f"{n['osm_checks']['D6_buildings_historic_or_heritage']:,}"
    t['D6_osm'] = f"{n['osm_checks']['D6_buildings_osm']:,}"
    return t


def fill(text, t):
    out = re.sub(r'\{\{(\w+)\}\}', lambda m: t[m.group(1)], text)
    assert '{{' not in out
    return out


def cites(keys):
    return '; '.join(f'[{LABEL[k]}](#{"how-we-know-the-redrawn-map-the-buildings-and-the-measures" if k == "measure" else "sources"})' for k in keys)


def page_grid(t):
    """The page's section for the set: one figure per D area, each opening in the lightbox. Each
    caption says first what the picture shows, then what the form recorded and what stands now;
    how the pictures were made is said once, in the section's opening paragraph."""
    out = []
    for b in BOXES:
        lab = b['label']
        out += ['::: figure',
                f"![{area_title(lab)}, graded D in 1937, seen from the south today, with the 1937 grades tinted on the ground: the area itself in the red of grade D, its neighbors in the other grades' colors](redlining-d-{slug(lab)}.webp)",
                '',
                f"**{area_title(lab)}, today, over the 1937 grades.** *What the 1937 form recorded:* {fill(b['form'], t)} [{cites(b['cite_form'])}] "
                f"*What stands there now:* {fill(b['now'], t)} [{cites(b['cite_now'])}]",
                ':::', '']
    return '\n'.join(out)


if __name__ == '__main__':
    n = json.load(open(os.path.join(HERE, 'numbers.json')))
    print(page_grid(tokens(n)))
