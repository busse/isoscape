#!/usr/bin/env python3
"""Main Street Station's outside, in massing, for the Broad Street set's map and its box 7:
written into history/broad-street-lines.json as the parts `mss-*` (every other feature is kept).

The measurements are the ones the Main Street Station cutaway is modeled from (branch
cutaway-main-street, tools/stations/main_street.py and main_street_plan.py), copied here as
data: the same local frame, fitted to OpenStreetMap, and the same levels and sources.

  a  along the front, toward the east-southeast (bearing 126.9°), the head house's long axis;
  b  back from Main Street toward the north-northeast (bearing 36.9°), the shed's axis;

in meters about the middle of the head house's Main Street front. Heights are meters above sea
level (`elevation`, `upTo`); every part belongs to the model `mss`, so its levels are taken from
the ground under the station alone.

  - the head house, 102 ft by 62 ft 4 in (The Railroad Gazette, July 13, 1900; OSM way
    366226941, 30.5 by 19.6 m), to its cornice, under a steep hipped roof of red tile;
  - the clock tower at the southwest corner (OSM way 366226942), 110 ft to the finial (The
    Railroad Gazette; SAH Archipedia), its shaft, clock stage, dome and finial;
  - the one-story concourse behind it, 82 ft wide (the 1900 plan), 35 ft deep (HAER VA-4);
  - the train shed, 123 ft between its columns and 517 ft long (HAER VA-4), its gable roof
    from the eaves 21 ft 1 in to the ridge 44 ft 9 in above the platforms (HAER VA-4, sheet 3),
    on columns 18 ft apart, over the deck the tracks ran on, on its trestle 25 ft over the
    ground (Sanborn, 1952).

    python3 tools/stations/main_street_set.py
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'history' / 'broad-street-lines.json'

O_LON, O_LAT = -77.4294842, 37.5342350      # the front's middle (OSM way 366226941)
KX, KY = 111_320 * math.cos(math.radians(O_LAT)), 110_574
FT = 0.3048


def unit(bearing):
    r = math.radians(bearing)
    return (math.sin(r), math.cos(r))


UA, UB = unit(126.9), unit(36.9)


def lonlat(a, b):
    e, n = a * UA[0] + b * UB[0], a * UA[1] + b * UB[1]
    return [round(O_LON + e / KX, 7), round(O_LAT + n / KY, 7)]


def rect(a0, a1, b0, b1):
    """Counter-clockwise on the ground; its first edge runs along a at b0."""
    return [lonlat(a0, b0), lonlat(a1, b0), lonlat(a1, b1), lonlat(a0, b1)]


def eaves_b(a0, a1, b0, b1):
    """A ring whose first and third edges run along b (a gable's eaves along the shed)."""
    return [lonlat(a0, b0), lonlat(a0, b1), lonlat(a1, b1), lonlat(a1, b0)][::-1]


LOC = 'https://tile.loc.gov/storage-services'
SRC = {
    'rg-1900': 'https://archive.org/details/sim_railway-age_1900-07-13_32_28',
    'habs-data': f'{LOC}/master/pnp/habshaer/va/va0500/va0562/data/va0562data.pdf',
    'haer-data': f'{LOC}/master/pnp/habshaer/va/va0800/va0897/data/va0897data.pdf',
    'haer-2': f'{LOC}/master/pnp/habshaer/va/va0800/va0897/sheet/00002a.tif',
    'haer-3': f'{LOC}/master/pnp/habshaer/va/va0800/va0897/sheet/00003a.tif',
    'haer-photo-1': f'{LOC}/service/pnp/habshaer/va/va0800/va0897/photos/215874pv.jpg',
    'habs-photo-side': f'{LOC}/service/pnp/habshaer/va/va0500/va0562/photos/162774pv.jpg',
    'detroit-east': 'http://hdl.loc.gov/loc.pnp/det.4a10737',
    'archipedia': 'https://archipediavm.upress.virginia.edu/buildings/VA-01-RI38',
    'osm-headhouse': 'https://www.openstreetmap.org/way/366226941',
    'osm-tower': 'https://www.openstreetmap.org/way/366226942',
    'osm-station': 'https://www.openstreetmap.org/way/113030476',
    'sanborn-1952': 'https://www.loc.gov/item/sanborn09064_016/',
    'dhr': 'https://www.dhr.virginia.gov/?p=15225',
    'habs-12': f'{LOC}/service/pnp/habshaer/va/va0500/va0562/photos/305472pv.jpg',
    'sanborn-1905': 'https://www.loc.gov/item/sanborn09064_003/',
}

# ---- levels, meters above sea level (main_street.py) ------------------------------------------
MAIN_ST = 6.1          # Main Street in front of the station (USGS 3DEP)
G = 8.4                # the ground floor, raised about 8 ft above the street (The Railroad Gazette)
FF = 14.9              # the track floor and the platforms (scaled from photographs: approximate)
# Heights measured on HABS VA-848-12 (Library of Congress, photograph 305472, J. E. Boucher, 1971), an
# oblique view of the front from Main Street, along the tower's corner against the finial's 110 ft
# above the street (The Railroad Gazette, 1900): the eaves about 56 ft, the ridge about 80 ft (set
# back 31 ft, so less sure), the clock stage from about 78.5 ft, the clock faces' centers about
# 85 ft and their diameter about 7.5 ft, the dome from about 93 ft (Sanborn, 1905 and 1952:
# "Clock Tower 90'") to about 102 ft. All approximate, to within about 5 ft.
FTM = 0.3048
CORNICE = MAIN_ST + 56 * FTM     # where the roof springs
RIDGE = MAIN_ST + 80 * FTM
SHAFT = MAIN_ST + 78.5 * FTM - 0.3   # the tower's shaft, to the balcony under the clock stage
STAGE_TOP = MAIN_ST + 93 * FTM
DOME_TOP = MAIN_ST + 102 * FTM
FINIAL = MAIN_ST + 110 * FTM
CLOCK = MAIN_ST + 85 * FTM
CLOCK_R = 7.5 * FTM / 2      # the tower's shaft, to the balcony under the clock stage
DECK_BOTTOM = FF - 1.4

# ---- plan (main_street_plan.py) ---------------------------------------------------------------
HH_W, HH_E, HH_N = -15.25, 15.25, 19.64     # the head house (OSM way 366226941)
TOWER = (-15.25, -9.1, 0.0, 6.7)            # OSM way 366226942
ELL = (-12.6, 11.9, HH_N, 30.2)             # the concourse
SHED_C = -0.25                              # the shed's middle line, from the head house's
SHED_B0 = 39.7                              # the first truss (HAER VA-4, sheet 2)
BAY = 18 * FT
SHED_L = 517 * FT                           # HAER VA-4
NBAYS = round(SHED_L / BAY)                 # 29 bays of 18 ft (522 ft): the last one's end is 517 ft
SHED_B1 = SHED_B0 + SHED_L
EAVE, COL = 73.1, 59.0                      # ft from the middle: the eaves, the columns


def xa(x_ft):
    return SHED_C + x_ft * FT


parts = []


def part(id_, name, ring, z0, z1, tone, conf, note, sources, **more):
    f = {'id': id_, 'name': name, 'kind': 'landmark', 'from': 1901, 'to': 2026, 'ring': ring,
         'tone': tone, 'only': 'whole', 'model': 'mss', 'confidence': conf}
    if z0 is not None:
        f['elevation'] = round(z0, 3)
    f['upTo'] = round(z1, 3)
    f.update(more)
    f['note'] = note
    f['sources'] = sources
    parts.append(f)


PLAN = [SRC['rg-1900']]
HABS = [SRC['habs-data']]
PH = [SRC['habs-photo-side'], SRC['detroit-east']]
SHED = [SRC['haer-data'], SRC['haer-3'], SRC['haer-2']]
MEASURED = (' Heights measured on HABS photograph VA-848-12 (1971), an oblique view of the front, against the finial\'s 110 ft above '
            'the street: approximate, to within about 5 ft.')
APPROX = ' Its cornice, about 56 ft above Main Street, is measured on HABS photograph VA-848-12 (1971) against the 110-ft tower (approximate).'

HH_NOTE = ('The head house, 102 ft by 62 ft 4 in (The Railroad Gazette, July 13, 1900), of golden Roman brick over a base of rough stone '
           '(HABS VA-848), drawn as a plain block to its cornice; its outline is OpenStreetMap\'s, which matches the plan.' + APPROX)
T1 = TOWER[1]
# In two pieces round the tower, which stands in its southwest corner, so the tower is drawn whole.
part('mss-head-house', 'Main Street Station (head house)', rect(T1, HH_E, 0.0, HH_N), MAIN_ST, CORNICE, 'stone', 'drawn', HH_NOTE,
     PLAN + HABS + [SRC['osm-headhouse']] + PH)
part('mss-head-house-west', 'Main Street Station (head house)', rect(HH_W, T1, TOWER[3], HH_N), MAIN_ST, CORNICE, 'stone', 'drawn', HH_NOTE,
     PLAN + HABS + [SRC['osm-headhouse']] + PH)
part('mss-head-house-roof', 'Main Street Station (roof)', rect(T1 + 0.3, HH_E - 0.6, 0.6, HH_N - 0.6), CORNICE, RIDGE, 'tile', 'written',
     'The steep hipped roof of red tile (The Railroad Gazette, 1900; HABS VA-848), from the cornice at about 56 ft to the ridge at about '
     '80 ft above Main Street, drawn plain, without its two rows of dormers and its chimney, and from the tower east (behind the tower it '
     'is left flat).' + MEASURED,
     PLAN + HABS + PH + [SRC['habs-12']], shape='hip')

a0, a1, b0, b1 = TOWER
TW = ('The clock tower at the southwest corner, 110 ft high to its finial with a clock face on each side (The Railroad Gazette, 1900; '
      'HABS VA-848; SAH Archipedia), drawn in plain stages: shaft, clock stage, dome and finial. Its outline is OpenStreetMap\'s; '
      'its stages are scaled from photographs (approximate).')
TSRC = PLAN + HABS + [SRC['archipedia'], SRC['osm-tower'], SRC['habs-12'], SRC['sanborn-1905'], SRC['sanborn-1952']] + PH
TW = TW + MEASURED + ' The Sanborn sheets of 1905 and 1952 mark it "Clock Tower 90\'", about the top of its masonry.'
part('mss-clock-tower', 'Main Street Station (clock tower)', rect(a0, a1, b0, b1), MAIN_ST, SHAFT + 0.3, 'stone', 'written', TW, TSRC)
part('mss-clock-stage', 'Main Street Station (clock tower)', rect(a0 + 0.3, a1 - 0.3, b0 + 0.3, b1 - 0.3), SHAFT + 0.3, STAGE_TOP, 'stone', 'written', TW, TSRC)
# The square ribbed dome, as a revolve on the tower's square (main_street_plan.py: its levels).
part('mss-clock-dome', 'Main Street Station (clock tower)', rect(a0 + 0.2, a1 - 0.2, b0 + 0.2, b1 - 0.2), STAGE_TOP, DOME_TOP, 'tile', 'written',
     'The tower\'s square ribbed dome of tile (HABS VA-848), from about 93 ft to about 102 ft above Main Street.' + MEASURED, TSRC, shape='revolve',
     levels=[[0, 1, 0], [0.2, 1.06, 0], [0.4, 1.0, 0], [1.2, 0.93, 0], [2.0, 0.78, 0], [2.6, 0.5, 0], [round(DOME_TOP - STAGE_TOP, 3), 0.12, 0]])
cx, cb = (a0 + a1) / 2, (b0 + b1) / 2
part('mss-clock-finial', 'Main Street Station (clock tower)', rect(cx - 0.25, cx + 0.25, cb - 0.25, cb + 0.25), DOME_TOP, FINIAL, 'iron', 'written',
     'The bronze finial, its top 110 ft above the street (The Railroad Gazette, 1900; SAH Archipedia), drawn as a plain spire; its form is approximate.',
     TSRC, shape='revolve', levels=[[0, 1, 0], [round(FINIAL - DOME_TOP, 3), 0.15, 0]])
CLK = ('A clock face, one on each of the tower\'s four sides (The Railroad Gazette, 1900), about 7.5 ft across, its center about 85 ft above '
       'Main Street.' + MEASURED)
for side, (p0, p1, q) in {'s': ((a0 + 0.3, b0 + 0.27), (a1 - 0.3, b0 + 0.27), (0, -0.06)),
                          'e': ((a1 - 0.27, b0 + 0.3), (a1 - 0.27, b1 - 0.3), (0.06, 0)),
                          'n': ((a1 - 0.3, b1 - 0.27), (a0 + 0.3, b1 - 0.27), (0, 0.06)),
                          'w': ((a0 + 0.27, b1 - 0.3), (a0 + 0.27, b0 + 0.3), (-0.06, 0))}.items():
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    ua = ((p1[0] - p0[0]), (p1[1] - p0[1]))
    ln = (ua[0] ** 2 + ua[1] ** 2) ** 0.5
    ua = (ua[0] / ln, ua[1] / ln)
    d0 = (mid[0] - ua[0] * CLOCK_R, mid[1] - ua[1] * CLOCK_R)
    d1 = (mid[0] + ua[0] * CLOCK_R, mid[1] + ua[1] * CLOCK_R)
    ring_ = [lonlat(*d0), lonlat(*d1), lonlat(d1[0] + q[0], d1[1] + q[1]), lonlat(d0[0] + q[0], d0[1] + q[1])]
    part(f'mss-clock-face-{side}', 'Main Street Station (clock)', ring_, CLOCK - CLOCK_R, CLOCK + CLOCK_R, 'plaster', 'written', CLK, TSRC, shape='disc')

part('mss-concourse', 'Main Street Station (concourse)', rect(ELL[0], ELL[1], ELL[2], ELL[3]), G - 0.4, FF + 7.3, 'stone', 'drawn',
     'The concourse (the "lobby" of the 1900 plan), 82 ft wide behind the head house, one story at the level of the platforms under a flat '
     'roof (The Railroad Gazette, 1900; HABS VA-848), 35 ft deep (HAER VA-4, sheet 2), over the baggage room. Its height is approximate.',
     PLAN + HABS + [SRC['haer-2'], SRC['osm-station']])

# ---- the train shed and its deck ---------------------------------------------------------------
SHED_NOTE = ('The train shed of 1901, 123 ft wide and 517 ft long (HAER VA-4), its gable roof from the eaves, 21 ft 1 in above the platforms, '
             'to the ridge of its trusses, 44 ft 9 in, as the cross section (HAER VA-4, sheet 3) draws it; drawn plain, without the monitor '
             'along its ridge, in lengths of about 70 ft. Its level, the track floor\'s, is approximate.')
pieces = 7
for k in range(pieces):
    p0 = SHED_B0 + SHED_L * k / pieces
    p1 = SHED_B0 + SHED_L * (k + 1) / pieces
    part(f'mss-shed-roof-{k}', 'Main Street Station train shed (roof)', eaves_b(xa(-EAVE), xa(EAVE), p0, p1), FF + 21.1 * FT, FF + 44.8 * FT,
         'roof', 'drawn', SHED_NOTE, SHED + [SRC['dhr']], shape='gable')
COL_NOTE = ('A column of the shed, one of two rows 118 ft apart and 18 ft on centers (HAER VA-4, sheets 2 and 3), drawn plain to the eaves. '
            'Its size is approximate.')
for k in range(NBAYS + 1):
    b = min(SHED_B0 + k * BAY, SHED_B1 - 0.3)
    for side in (-1, 1):
        a = xa(side * COL)
        part(f'mss-shed-column-{k}-{"w" if side < 0 else "e"}', 'Main Street Station train shed (column)', rect(a - 0.3, a + 0.3, b - 0.3, b + 0.3),
             FF, FF + 21.1 * FT, 'iron', 'drawn', COL_NOTE, SHED)
DECK_NOTE = ('The deck that carries the stub tracks and platforms at the level of the waiting room, between the two railroads\' through tracks '
             '(HAER VA-4; photograph VA-4-1 shows it on steel bents), on its trestle 25 ft over the ground (Sanborn, 1952). Its girders\' '
             'depth is approximate.')
for k in range(pieces):
    p0 = ELL[3] if k == 0 else SHED_B0 + SHED_L * k / pieces
    p1 = SHED_B0 + SHED_L * (k + 1) / pieces
    part(f'mss-deck-{k}', 'Main Street Station (deck)', rect(xa(-62.0), xa(62.0), p0, p1), DECK_BOTTOM, FF, 'iron', 'written', DECK_NOTE,
         [SRC['haer-photo-1'], SRC['haer-data'], SRC['sanborn-1952']])
POST_NOTE = ('A post of the steel trestle under the deck (HAER photograph VA-4-1 shows the deck on steel bents). Their number and spacing here '
             'are approximate.')
for k in range(0, NBAYS + 1, 2):
    b = min(SHED_B0 + k * BAY, SHED_B1 - 0.3)
    for j, x in enumerate((-54.0, -18.0, 18.0, 54.0)):
        a = xa(x)
        part(f'mss-trestle-post-{k}-{j}', 'Main Street Station (trestle)', rect(a - 0.25, a + 0.25, b - 0.25, b + 0.25), None, DECK_BOTTOM,
             'iron', 'approximate', POST_NOTE, [SRC['haer-photo-1'], SRC['sanborn-1952']])

h = json.loads(OUT.read_text())
kept = [f for f in h['features'] if not f['id'].startswith('mss-')]
# The station's parts go where the old ones were, so the file reads in the same order.
at = next((i for i, f in enumerate(h['features']) if f['id'].startswith('mss-')), len(kept))
h['features'] = kept[:at] + parts + kept[at:]
# OSM's head house and tower are drawn in today's scene only, as its station outline is: in the
# set's years the parts stand for them.
for wid, nm, src in (('w366226941', 'Main Street Station head house (today\'s outline)', SRC['osm-headhouse']),
                     ('w366226942', 'Main Street Station clock tower (today\'s outline)', SRC['osm-tower'])):
    if not any(d['id'] == wid for d in h['dates']):
        h['dates'].append({'id': wid, 'name': nm, 'year': None, 'source': src,
                           'note': 'Drawn in today\'s scene only: in the set\'s years the station is drawn as curated parts (mss-*).'})
OUT.write_text(json.dumps(h, indent=1, ensure_ascii=False) + '\n')
print(f'{OUT.relative_to(ROOT)}: {len(parts)} parts of Main Street Station')
