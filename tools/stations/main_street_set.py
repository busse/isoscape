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
    366226941, 30.5 by 19.6 m), to its cornice, under a steep hipped roof of red tile whose
    ridge, about 11 m long, is measured on HABS photographs (1971);
  - the clock tower at the southwest corner (OSM way 366226942), about 148 ft to the finial as
    measured on HABS photographs VA-848-10, -11 and -12 (1971): its shaft, balcony, clock stage,
    entablature, drum, dome and finial;
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
    'habs-10': f'{LOC}/master/pnp/habshaer/va/va0500/va0562/photos/305470p.jpg',
    'habs-11': f'{LOC}/service/pnp/habshaer/va/va0500/va0562/photos/305471pv.jpg',
}

# ---- levels, meters above sea level (main_street.py) ------------------------------------------
MAIN_ST = 6.1          # Main Street in front of the station (USGS 3DEP)
G = 8.4                # the ground floor, raised about 8 ft above the street (The Railroad Gazette)
FF = 14.9              # the track floor and the platforms (scaled from photographs: approximate)
# The roof's ridge and the tower's stages, as the Main Street Station cutaway measured them in its
# round 4 (branch cutaway-main-street: tools/stations/main_street.py, levels; its sources.md,
# Round 4), copied here as data. Measured on three HABS photographs of 1971 (J. E. Boucher):
# VA-848-10 (photograph 305470, the front square on from the I-95 viaduct), scaled by the
# front's own width, 102 ft, and checked by its 12-ft bays and the 1900 section's floors;
# VA-848-12 (305472, from Main Street) and VA-848-11 (305471, from the east platform), which agree
# to within about 1.5 m and 1 m. Read from the cresting over the cornice; points set back from the
# front corrected for the camera's distance (about 40 m). All approximate, to within about 1.5 m
# (the finial to within about 8 ft). Sanborn's "Clock Tower 90'" (1905, 1952) fits the measured
# shaft, about 90 ft over the ground floor. The Railroad Gazette's 110 ft (1900), written before
# the station was built beside a perspective of a different tower, does not fit the photographs.
CORNICE = FF + 11.8    # 26.7: the main cornice, where the roof springs (about 68 ft over Main Street)
RIDGE = 41.4           # the ridge, about 115 ft over Main Street, about 11 m long between its finials
SHAFT = 35.9           # the tower's shaft, to the balcony's floor under the clock stage
BALCONY = 36.65        # the top of the balcony's balustrade
CLOCK = 40.3           # the clock faces' centers
CLOCK_R = 1.35         # the faces' radius: about 9 ft across with the bezel
STAGE_TOP = 43.0       # the clock stage's top, under its entablature
ENTAB = 43.5           # the entablature's top, the drum's foot
DRUM_TOP = 44.8        # the dome's foot
DOME_TOP = 48.7        # the dome's crown
FINIAL = 51.6          # the finial's tip, about 148 ft over Main Street
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
MEASURED = (' Heights measured on HABS photographs VA-848-10, -11 and -12 (1971) against the front\'s own width, 102 ft: approximate, '
            'to within about 1.5 m (5 ft).')
APPROX = (' Its cornice, about 26.7 m above sea level (some 68 ft over Main Street), is as the 1900 section draws it and as HABS photographs '
          'VA-848-10 and -12 (1971) show it (approximate).')
H10 = [SRC['habs-10'], SRC['habs-11'], SRC['habs-12']]

HH_NOTE = ('The head house, 102 ft by 62 ft 4 in (The Railroad Gazette, July 13, 1900), of golden Roman brick over a base of rough stone '
           '(HABS VA-848), drawn as a plain block to its cornice; its outline is OpenStreetMap\'s, which matches the plan.' + APPROX)
T1 = TOWER[1]
# In two pieces round the tower, which stands in its southwest corner, so the tower is drawn whole.
part('mss-head-house', 'Main Street Station (head house)', rect(T1, HH_E, 0.0, HH_N), MAIN_ST, CORNICE, 'stone', 'drawn', HH_NOTE,
     PLAN + HABS + [SRC['osm-headhouse']] + PH + H10)
part('mss-head-house-west', 'Main Street Station (head house)', rect(HH_W, T1, TOWER[3], HH_N), MAIN_ST, CORNICE, 'stone', 'drawn', HH_NOTE,
     PLAN + HABS + [SRC['osm-headhouse']] + PH + H10)
# The roof: one equal-pitched hip over the whole head house, its ridge parallel to Main Street
# (29.3 m long, 18.4 m deep at the eaves: the ridge about 10.9 m), drawn in two pieces that stand
# clear of the tower, east of it and behind it; where the roof meets the tower it is inside it.
ROOF = rect(HH_W + 0.6, HH_E - 0.6, 0.6, HH_N - 0.6)
ROOF_NOTE = ('The steep hipped roof of red tile (The Railroad Gazette, 1900; HABS VA-848), from the cornice to its ridge about 41.4 m above sea '
             'level (some 115 ft over Main Street), the ridge parallel to the street and about 11 m long, as HABS photograph VA-848-10 shows it; '
             'drawn plain, without its two rows of dormers, its ridge finials and its chimney.' + MEASURED)
ROOF_SRC = PLAN + HABS + PH + H10
part('mss-head-house-roof', 'Main Street Station (roof)', rect(T1 + 0.3, HH_E - 0.6, 0.6, HH_N - 0.6), CORNICE, RIDGE, 'tile', 'written',
     ROOF_NOTE, ROOF_SRC, shape='hip', roofRing=ROOF)
part('mss-head-house-roof-west', 'Main Street Station (roof)', rect(HH_W + 0.6, T1 + 0.3, TOWER[3] + 0.3, HH_N - 0.6), CORNICE, RIDGE, 'tile', 'written',
     ROOF_NOTE, ROOF_SRC, shape='hip', roofRing=ROOF)

a0, a1, b0, b1 = TOWER
TW = ('The clock tower at the southwest corner, with a clock face on each side (The Railroad Gazette, 1900; HABS VA-848), drawn in plain '
      'stages: shaft, balcony, clock stage, entablature, drum, dome and finial. Its outline is OpenStreetMap\'s. Its stages are measured on '
      'HABS photographs VA-848-10, -11 and -12 (1971) against the 102-ft front, approximate to within about 1.5 m: the shaft to about 35.9 m '
      'above sea level, some 90 ft over the ground floor, as the Sanborn atlases (1905, 1952) mark it ("Clock Tower 90\'"); the finial about '
      '148 ft over Main Street. The 110 ft in The Railroad Gazette (1900), written before the station was built beside a perspective whose '
      'tower differs from the one built, does not fit the photographs.')
TSRC = PLAN + HABS + [SRC['archipedia'], SRC['osm-tower']] + H10 + [SRC['sanborn-1905'], SRC['sanborn-1952']] + PH
part('mss-clock-tower', 'Main Street Station (clock tower)', rect(a0, a1, b0, b1), MAIN_ST, SHAFT, 'stone', 'written', TW, TSRC)
part('mss-clock-balcony', 'Main Street Station (clock tower)', rect(a0 - 0.3, a1 + 0.3, b0 - 0.3, b1 + 0.3), SHAFT, BALCONY, 'stone', 'written',
     'The balcony at the top of the shaft, with its balustrade round the clock stage (HABS photographs VA-848-10 to -12), drawn as one plain '
     'band; its floor about 35.9 m and its balustrade\'s top about 36.65 m above sea level, measured on VA-848-10 (approximate).', TSRC)
part('mss-clock-stage', 'Main Street Station (clock tower)', rect(a0 + 0.3, a1 - 0.3, b0 + 0.3, b1 - 0.3), BALCONY, STAGE_TOP, 'stone', 'written', TW, TSRC)
part('mss-clock-entablature', 'Main Street Station (clock tower)', rect(a0 - 0.1, a1 + 0.1, b0 - 0.1, b1 + 0.1), STAGE_TOP, ENTAB, 'stone', 'written',
     'The entablature over the clock stage (HABS VA-848), its top about 43.5 m above sea level, measured on HABS photograph VA-848-10 '
     '(approximate).', TSRC)
part('mss-clock-drum', 'Main Street Station (clock tower)', rect(a0 + 0.45, a1 - 0.45, b0 + 0.45, b1 - 0.45), ENTAB, DRUM_TOP, 'stone', 'written',
     'The low drum the dome stands on (HABS VA-848), to about 44.8 m above sea level, measured on HABS photograph VA-848-10 '
     '(approximate).', TSRC)
# The square ribbed dome, as a revolve on the tower's square: a quarter-ellipse in profile, its
# crown about half the clock stage's height over its foot (HABS VA-848-10).
DH = DOME_TOP - DRUM_TOP
part('mss-clock-dome', 'Main Street Station (clock tower)', rect(a0 + 0.5, a1 - 0.5, b0 + 0.5, b1 - 0.5), DRUM_TOP, DOME_TOP, 'tile', 'written',
     'The tower\'s square ribbed dome of tile (HABS VA-848), from about 44.8 m to about 48.7 m above sea level, drawn plain.' + MEASURED, TSRC,
     shape='revolve', levels=[[round(DH * k / 10, 3), round(max(0.1, math.sqrt(1 - (k / 10) ** 2)), 3), 0] for k in range(11)])
cx, cb = (a0 + a1) / 2, (b0 + b1) / 2
part('mss-clock-finial', 'Main Street Station (clock tower)', rect(cx - 0.25, cx + 0.25, cb - 0.25, cb + 0.25), DOME_TOP, FINIAL, 'iron', 'written',
     'The bronze finial (HABS VA-848), drawn as a plain spire, its tip about 51.6 m above sea level, about 148 ft over Main Street, measured '
     'on HABS photographs VA-848-10 and -12 against the 102-ft front (approximate, to within about 8 ft). The Railroad Gazette (1900, '
     'before the station was built) and SAH Archipedia give 110 ft, which does not fit the photographs. Its form is approximate.',
     TSRC, shape='revolve', levels=[[0, 1, 0], [round(FINIAL - DOME_TOP, 3), 0.15, 0]])
CLK = ('A clock face, one on each of the tower\'s four sides (The Railroad Gazette, 1900; HABS VA-848), about 9 ft across with its bezel, its '
       'center about 40.3 m above sea level (some 112 ft over Main Street).' + MEASURED)
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
