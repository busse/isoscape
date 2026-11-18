#!/usr/bin/env python3
"""Model Main Street Station (Richmond, opened 1901) and its train shed as of about 1952, into a
history file for the cutaway (regions/main-street-station-cutaway.json).

The station is drawn from curated parts, in one local frame in meters about the middle of the
head house's Main Street front (1520 E. Main Street):

  a  along the front, toward the east-southeast (bearing 126.9°), the head house's long axis;
  b  back from Main Street toward the north-northeast (bearing 36.9°), the shed's axis.

The frame is fitted to OpenStreetMap: the head house (building part, way 366226941: 30.5 by
19.6 m, which matches the 102 ft 5 in by 63 ft of HABS VA-848), its clock tower (way 366226942)
and the station outline (way 113030476), whose shed begins 39.4 m back from the front, where
HAER VA-4's plan (sheet 2) puts the first truss: 63 ft of head house, a 35-ft concourse ell and
a 31-ft taper. The train shed is drawn from HAER VA-4's measured drawings (1970): its trusses,
columns, brackets and monitors traced from the cross section (sheet 3, at 1/8 in = 1 ft), its
tracks and platforms from the same section, its bays (18 ft) and longitudinal bracing from the
plan and side elevation (sheet 2). The head house's rooms on its two public floors are traced
from the architects' plans in The Railroad Gazette of July 13, 1900, which The Times of November
24, 1901 describes as built; its floors' levels follow that article's section; its upper floors,
of which no plan was found, follow HABS VA-848 (1969); its stonework, dormers, roof and tower are
scaled from photographs (HABS, Detroit Publishing) against the 102-ft front.

    python3 tools/stations/main_street.py   # writes history/main-street-station.json

The interior parts are in main_street_plan.py.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import lonlat_of, unit  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'history' / 'main-street-station.json'
DOWNTOWN = ROOT / 'history' / 'richmond-downtown.json'

# The front's middle, from OSM way 366226941's front corners (-77.4296233, 37.5343167 and
# -77.4293455, 37.5341532).
O_LON, O_LAT = -77.4294842, 37.5342350
lonlat = lonlat_of(O_LON, O_LAT)
UA, UB = unit(126.9), unit(36.9)
FT = 0.3048


def ab(a, b):
    return (a * UA[0] + b * UB[0], a * UA[1] + b * UB[1])


def ring(pts):
    return [lonlat(ab(*p)) for p in pts]


def rect(a0, a1, b0, b1):
    """A rectangle in the frame, counter-clockwise on the ground."""
    return ring([(a0, b0), (a1, b0), (a1, b1), (a0, b1)])


def plane(a0, b0, a1, b1, thick):
    """A frame part's ring: its first edge from (a0, b0) to (a1, b1) is the plane its members
    stand in; its second edge, `thick` long, is their thickness, to the left of that edge."""
    dx, dy = a1 - a0, b1 - b0
    l = math.hypot(dx, dy)
    na, nb = -dy / l * thick, dx / l * thick
    return ring([(a0, b0), (a1, b1), (a1 + na, b1 + nb), (a0 + na, b0 + nb)])


def strip(a0, a1, b0, b1):
    """A track's ring: its first edge across the track (along a), its second along it (b)."""
    return ring([(a0, b0), (a1, b0), (a1, b1), (a0, b1)])


# ---- sources -------------------------------------------------------------------------------
LOC = 'https://tile.loc.gov/storage-services'
SRC = {
    'haer-1': f'{LOC}/master/pnp/habshaer/va/va0800/va0897/sheet/00001a.tif',
    'haer-2': f'{LOC}/master/pnp/habshaer/va/va0800/va0897/sheet/00002a.tif',
    'haer-3': f'{LOC}/master/pnp/habshaer/va/va0800/va0897/sheet/00003a.tif',
    'haer-data': f'{LOC}/master/pnp/habshaer/va/va0800/va0897/data/va0897data.pdf',
    'haer-photo-1': f'{LOC}/service/pnp/habshaer/va/va0800/va0897/photos/215874pv.jpg',
    'haer-photo-5': f'{LOC}/service/pnp/habshaer/va/va0800/va0897/photos/215878pv.jpg',
    'haer-photo-9': f'{LOC}/service/pnp/habshaer/va/va0800/va0897/photos/215882pv.jpg',
    'habs-data': f'{LOC}/master/pnp/habshaer/va/va0500/va0562/data/va0562data.pdf',
    'habs-photo-side': f'{LOC}/service/pnp/habshaer/va/va0500/va0562/photos/162774pv.jpg',
    'habs-photo-front': 'http://hdl.loc.gov/loc.pnp/hhh.va0562/photos.305473p',
    'habs-photo-1971': 'http://hdl.loc.gov/loc.pnp/hhh.va0562/photos.305470p',
    'habs-photo-1969': 'http://hdl.loc.gov/loc.pnp/hhh.va0562/photos.162772p',
    'nrhp': 'https://www.dhr.virginia.gov/wp-content/uploads/2018/04/127-0172_MainSt_Station_1970_Final_Nomination_NRHP.pdf',
    'nhl': 'https://www.dhr.virginia.gov/wp-content/uploads/2018/04/127-0172_MainStreetStation_1976_Nomination_NHL.pdf',
    'detroit-west': 'http://hdl.loc.gov/loc.pnp/det.4a18653',
    'detroit-east': 'http://hdl.loc.gov/loc.pnp/det.4a10737',
    'loc-blog': 'https://blogs.loc.gov/picturethis/2026/03/on-track-with-main-street-station-in-richmond-virginia/',
    'archipedia': 'https://archipediavm.upress.virginia.edu/buildings/VA-01-RI38',
    'osm-headhouse': 'https://www.openstreetmap.org/way/366226941',
    'osm-tower': 'https://www.openstreetmap.org/way/366226942',
    'osm-station': 'https://www.openstreetmap.org/way/113030476',
    'osm-sal': 'https://www.openstreetmap.org/way/38232584',
    'osm-co': 'https://www.openstreetmap.org/way/169784634',
    'osm-main': 'https://www.openstreetmap.org/way/699605461',
    'bdc': 'https://www.bdcnetwork.com/home/article/55144138/back-on-track',
    'obs-1952': 'https://streamlinerschedules.com/concourse/track2/orangeblossom195212.html',
    'gw': 'https://en.wikipedia.org/wiki/George_Washington_(train)',
    'gw-diesel': 'https://trainweb.us/fredatsf/C&OGW50.htm',
    'rg-1900': 'https://archive.org/details/sim_railway-age_1900-07-13_32_28',
    'times-1901': 'https://www.loc.gov/resource/sn85034438/1901-11-24/ed-1/?sp=1&st=text',
    'sanborn-1905': 'https://www.loc.gov/item/sanborn09064_003/',
    'sanborn-1952': 'https://www.loc.gov/item/sanborn09064_016/',
    'haer-photo-10': f'{LOC}/service/pnp/habshaer/va/va0800/va0897/photos/215883pv.jpg',
    'habs-photo-11': f'{LOC}/service/pnp/habshaer/va/va0500/va0562/photos/305471pv.jpg',
    'habs-photo-12': f'{LOC}/service/pnp/habshaer/va/va0500/va0562/photos/305472pv.jpg',
    'habs-photo-a1': f'{LOC}/service/pnp/habshaer/va/va1800/va1805/photos/305475pv.jpg',
    'detroit-nw': 'https://www.loc.gov/item/2016818689/',
    'odc-1950': 'https://richmondrailroadmuseum.com/main-street-station',
    'co-306-1953': 'https://piedmontsub.com/Richmond.shtml',
    'sal-e8-1955': 'https://www.railpictures.net/photo/243833',
}

# ---- levels (meters above sea level) --------------------------------------------------------
# The ground under Main Street and the shed is the elevation model's (USGS 3DEP). The ground
# floor is set at the ground the model gives round the head house; the first floor, the level
# of the waiting room, the concourse and the platforms, was scaled in round 1 from photographs
# against the 110-ft tower, about 6.5 m higher. Round 4 measured the front square on (HABS
# VA-848-10, 1971) against its own width, 102 ft: the first floor is 5.8 m (19 ft) over the
# ground floor there, as the 1900 section draws it, and the 110-ft figure does not fit the
# tower as built (see the tower's levels below). The floors are left where they were (every
# room, platform and train hangs on them); the 0.7 m is a known difference.
MAIN_ST = 6.1          # Main Street in front of the station (3DEP)
FORECOURT = 7.0        # the sidewalk at the foot of the front steps (3DEP)
G = 8.4                # the ground floor and the loggia (approximate)
FF = 14.9              # the first floor and the platforms (approximate)
L2 = FF + 7.2          # the second floor, the low gallery under the cornice
CORNICE = FF + 11.8    # the main cornice, where the roof springs (checked in round 4: within 0.7 m)
BALUSTRADE = FF + 12.6
L3 = FF + 12.2         # the third and fourth floors, in the roof, lit by its two rows of dormers
L4 = FF + 15.6
# The roof's ridge and the tower's stages, measured in round 4 (approximate, to within about
# 1.5 m) on three photographs: HABS VA-848-10 (1971, the front square on from the I-95
# viaduct, scaled by the front's 102-ft width and checked by its 12-ft bays), VA-848-12 (1971,
# from Main Street) and VA-848-11 (1971, from the east platform), each read from the cresting
# over the cornice, which the model already set where these photographs put it. Points set back
# from the front (the ridge, 9.8 m; the dome, 3.4 m) are corrected for the camera's distance,
# about 40 m in VA-848-10 (estimated from a pedestrian on the sidewalk and the front steps). The 1900 section's ridge, about
# 104 ft over the ground floor, agrees to within a meter. Sanborn's "Clock Tower 90'" (1905 and
# 1952) matches the measured shaft, about 90 ft over the ground floor.
RIDGE = FF + 26.5      # 41.4: was FF + 23.0 (37.9), which stood above the clock stage
TOWER_SHAFT = 35.9     # the shaft's top, the balcony's floor under the clock stage (was 32.4)
CLOCK_Z = 40.3         # the clock faces' centers (was 34.3)
CLOCK_R = 1.35         # their radius: about 9 ft across with the bezel (was 1.15)
STAGE_TOP = 43.0       # the clock stage's top, under its entablature (was 36.2)
DRUM_TOP = 44.8        # the dome's foot, on a low drum over the entablature (was 36.7)
DOME_TOP = 48.7        # the dome's crown (was 40.3)
FINIAL_TOP = 51.6      # the finial's tip, about 148 ft over Main Street (was 41.9, "110 ft")
CHIMNEY_TOP = 35.3     # the east chimney's top (was 33.9)
DECK = FF - 0.75       # the tops of the deck's girders, under the ties
DECK_BOTTOM = FF - 1.4

# ---- the head house and concourse: main_street_plan.py --------------------------------------
features = []


def part(id_, name, ring_, z0, z1, tone, conf, note, sources, **more):
    """A part of the station from elevation z0 to z1 (meters above sea level)."""
    f = {'id': id_, 'name': name, 'kind': 'landmark', 'from': 1901, 'to': 1985, 'ring': ring_, 'height': round(z1 - (z0 if z0 is not None else 0), 3),
         'tone': tone, 'elevation': None if z0 is None else round(z0, 3), 'upTo': round(z1, 3), 'note': note, 'sources': sources, 'confidence': conf}
    if z0 is None:
        del f['elevation']   # seated on the lowest ground under it
    f.update({k: v for k, v in more.items() if v is not None})
    features.append(f)


import main_street_plan as MP  # noqa: E402

MP.build(part, rect, ring, plane, SRC, globals())

# ---- the train shed (HAER VA-4) -------------------------------------------------------------
# Across the shed, in feet from its middle line (west negative), as the cross section (sheet 3)
# draws it looking north: columns at 59 ft each side (118 ft apart, sheet 2), eaves 13 ft 6 in
# beyond. The shed's middle line runs 0.25 m west of the head house's.
SHED_C = -0.25
SHED_B0 = 39.7                     # the first truss (HAER sheet 2; OSM way 113030476)
BAY = 18 * FT
NB = 6                             # bays drawn: the frame ends in the seventh
COL = 59.0                         # ft
EAVE = 73.1


def xa(x_ft):
    """The frame's a for x feet across the shed (east positive)."""
    return SHED_C + x_ft * FT


def top(x):
    """The main truss's top chord, ft above the platform at x ft from the middle."""
    return 44.8 - (44.8 - 21.1) * abs(x) / EAVE


def mtop(x):
    """The monitor's roof, ft above the platform."""
    return 53.2 - (53.2 - 43.4) * abs(x) / 28.3


BOTTOM = [(-59.2, 14.9), (-52.2, 20.0), (-41.9, 24.8), (-32.4, 28.3), (-22.5, 30.2), (-11.7, 31.4), (0.0, 32.0)]
TOP_NODES = [-47.7, -36.1, -27.8, -19.0, -8.0]


def truss_members():
    """The main truss, its brackets, the monitor's truss and the vent over it, in feet."""
    m = []
    half = []
    # Top chord: eave to peak, in one piece each side.
    half.append((-EAVE, top(EAVE), 0.0, top(0), 1.2))
    # Bottom chord: column to middle, by its nodes.
    for p, q in zip(BOTTOM, BOTTOM[1:]):
        half.append((p[0], p[1], q[0], q[1], 1.0))
    # Web: a Warren pattern between bottom nodes and top nodes.
    web = [(-59.2, top(59.2))]
    for k, xt in enumerate(TOP_NODES):
        web += [BOTTOM[k + 1], (xt, top(xt))]
    web.append(BOTTOM[-1])
    for p, q in zip(web, web[1:]):
        half.append((p[0], p[1], q[0], q[1], 0.6))
    # The column's head and its brackets under the overhang.
    half += [(-59.2, 14.9, -59.2, top(59.2), 1.2), (-60.0, 14.9, -64.2, 20.9, 0.6), (-64.2, 20.9, -60.0, 24.4, 0.6), (-71.6, 20.7, -64.2, 20.9, 0.6)]
    # The monitor: its posts on the main truss, its own truss and roof chord, its sides.
    half += [(-18.7, top(18.7), -18.7, mtop(18.7), 0.8), (-18.7, 45.1, 0.0, 45.1, 0.7), (-28.3, mtop(28.3), 0.0, mtop(0), 0.9),
             (-18.7, 45.1, -8.0, mtop(8.0), 0.5), (-8.0, mtop(8.0), -8.0, 45.1, 0.5), (-8.0, 45.1, 0.0, mtop(0), 0.5)]
    # The vent on the monitor's ridge.
    half += [(-2.6, mtop(2.6), -2.6, 56.8, 0.4), (-5.0, 56.8, 0.0, 58.3, 0.5)]
    for (x0, z0, x1, z1, d) in half:
        m.append((x0, z0, x1, z1, d))
        if not (x0 == 0 and x1 == 0):
            m.append((-x0, z0, -x1, z1, d))
    m.append((0.0, 32.0, 0.0, 44.8, 0.8))
    m.append((0.0, 45.1, 0.0, mtop(0), 0.5))
    return m


HALF = 22.7   # m: a truss part's first edge reaches just past the eaves each side


def to_u(x_ft):
    """Meters along a truss part's first edge, which starts HALF m west of the shed's middle."""
    return HALF + x_ft * FT


TRUSS_NOTE = ('A riveted steel truss of the shed, a modified Warren truss of 123-ft span, with its knee brackets under the 13 ft 6 in '
              'overhangs, the monitor\'s smaller truss on top and the vent on the monitor\'s ridge: traced from the cross section on '
              'HAER VA-4, sheet 3 (1970, at 1/8 in = 1 ft), member by member at its nodes; members\' depths approximate.')
SHED_SRC = [SRC['haer-3'], SRC['haer-2'], SRC['haer-data'], SRC['nhl']]
members = truss_members()
TH = 0.25     # half a truss's (and a column's) thickness; what lies between two trusses stops this short of each
for k in range(NB + 1):
    b = SHED_B0 + k * BAY
    mm = [[round(to_u(x0), 3), round(z0 * FT, 3), round(to_u(x1), 3), round(z1 * FT, 3), round(d * FT * 0.5, 3)] for (x0, z0, x1, z1, d) in members]
    part(f'mss-s-truss-{k}', 'Main Street Station train shed: truss', plane(SHED_C - HALF, b - 0.17, SHED_C + HALF, b - 0.17, 0.34),
         FF, FF + 18.5, 'steel', 'drawn', TRUSS_NOTE, SHED_SRC, shape='frame', members=mm)
    for side in (-1, 1):
        a = xa(side * COL)
        part(f'mss-s-column-{k}-{"w" if side < 0 else "e"}', 'Main Street Station train shed: column', rect(a - 0.25, a + 0.25, b - 0.25, b + 0.25),
             FF, FF + 14.9 * FT - 0.25, 'steel', 'drawn',
             'A built-up box column, one of two rows 118 ft apart and 18 ft on centers (HAER VA-4, sheets 2 and 3; photographs VA-4-4 to VA-4-6). Its size is approximate.',
             SHED_SRC + [SRC['haer-photo-5']])

# Roofing over each bay: the main slopes, the monitor's sides and roof, the vent's roof. Each is
# a slab laid on the chords, a bay long. The east slopes of the first bays are lifted away in the
# cutaway (regions/main-street-station-cutaway.json) to show the trusses.
ROOF_NOTE = ('The shed\'s roofing over one 18-ft bay, laid on the top chords as the cross section (HAER VA-4, sheet 3) draws it. '
             'Its covering is not described; its thickness is approximate.')
for k in range(NB):
    b0 = SHED_B0 + k * BAY
    b1 = b0 + BAY
    for side, tag in ((-1, 'w'), (1, 'e')):
        mm = [
            [to_u(side * EAVE), top(EAVE) + 0.8, to_u(side * 59.6), top(59.6) + 0.8, 0.18 / FT],
            [to_u(side * 59.6), top(59.6) + 0.8, to_u(side * 18.7), top(18.7) + 0.8, 0.18 / FT],
            [to_u(side * 30.0), mtop(28.3) + 0.2, to_u(0.0), mtop(0) + 0.8, 0.18 / FT],
            [to_u(side * 5.0), 57.4, to_u(0.0), 58.9, 0.15 / FT],
        ]
        part(f'mss-s-roof-{tag}-{k}', 'Main Street Station train shed: roof', plane(SHED_C - HALF, b0 + TH, SHED_C + HALF, b0 + TH, BAY - 2 * TH),
             FF, FF + 18.5, 'roof', 'drawn',
             ROOF_NOTE,
             SHED_SRC + [SRC['haer-1']], shape='frame',
             members=[[round(m[0], 3), round(m[1] * FT, 3), round(m[2], 3), round(m[3] * FT, 3), round(m[4] * FT, 3)] for m in mm])
    # The monitor's sides, open for light and air between the main roof and the monitor's roof:
    # the side elevation (HAER VA-4, sheet 2) draws them as a band of close vertical slats.
    for side, tag in ((-1, 'w'), (1, 'e')):
        a = xa(side * 18.7)
        z0, z1 = (top(18.7) + 1.4) * FT, (mtop(18.7) - 0.3) * FT
        slats = []
        u = 0.15
        while u < BAY - 2 * TH - 0.1:
            slats.append([round(u, 3), 0, round(u, 3), round(z1 - z0, 3), 0.07])
            u += 0.35
        slats += [[0, 0.05, round(BAY - 2 * TH, 3), 0.05, 0.1], [0, round(z1 - z0 - 0.05, 3), round(BAY - 2 * TH, 3), round(z1 - z0 - 0.05, 3), 0.1]]
        part(f'mss-s-louver-{tag}-{k}', 'Main Street Station train shed: monitor side', plane(a + 0.04, b0 + TH, a + 0.04, b1 - TH, 0.08),
             FF + z0, FF + z1, 'steel', 'drawn',
             'The open side of the monitor along the ridge, between the main roof and the monitor\'s roof (HAER VA-4, sheets 1 and 3), drawn in slats as the side elevation (sheet 2) draws it. The slats\' spacing is approximate.',
             SHED_SRC + [SRC['haer-1']], shape='frame', members=slats)
    # Longitudinal X-bracing between the columns, from 11 ft to 23 ft 6 in above the platform
    # (the side elevation, sheet 2), and the eave strut along the column heads.
    for side, tag in ((-1, 'w'), (1, 'e')):
        a = xa(side * COL)
        part(f'mss-s-brace-{tag}-{k}', 'Main Street Station train shed: bracing', plane(a + 0.08, b0 + TH, a + 0.08, b1 - TH, 0.16),
             FF, FF + 9, 'steel', 'drawn',
             'Diagonal bracing between two columns, as the side elevation draws it in every bay (HAER VA-4, sheet 2): from 11 ft to 23 ft 6 in above the platform.',
             SHED_SRC, shape='frame', members=[[0, 11 * FT, BAY - 2 * TH, 23.5 * FT, 0.12], [0, 23.5 * FT, BAY - 2 * TH, 11 * FT, 0.12], [0, 23.5 * FT, BAY - 2 * TH, 23.5 * FT, 0.25]])

# The roof over the taper between the concourse and the shed's first truss: the longitudinal
# section (HAER VA-4, sheet 2) draws it falling from the shed, about 33 ft over the platform,
# to the concourse's roof. Its plan is a taper (sheet 2); it is drawn here as wide as the
# concourse (approximate). In the cutaway it is lifted away, to show the gates.
TAPER_Z0 = FF + 6.8 + 0.5   # the concourse's roof (main_street_plan.py: CTOP)
part('mss-s-taper-roof', 'Main Street Station: roof between the concourse and the shed', plane(MP.ELL[1], MP.B_GATE, MP.ELL[1], SHED_B0 - 0.2, MP.ELL[1] - MP.ELL[0]),
     FF, FF + 33 * FT, 'roof', 'drawn',
     'The roof over the 31-ft taper between the concourse and the train shed, falling from the shed to the concourse as the longitudinal section (HAER VA-4, sheet 2) draws it. Its width and thickness are approximate.',
     [SRC['haer-2']], shape='frame',
     members=[[0, round(TAPER_Z0 - FF, 3), round(SHED_B0 - 0.2 - MP.B_GATE, 3), round(33 * FT, 3), 0.25]])

# ---- the deck, platforms and tracks ---------------------------------------------------------
# From the cross section (sheet 3): six stub tracks under the shed, and a through track under
# each overhang; five platforms, two of them along the column rows. Feet from the middle.
TRACKS = {'w': -68.7, '1': -49.9, '2': -25.9, '3': -15.2, '4': 9.3, '5': 20.5, '6': 49.6, 'e': 68.4}
PLATFORMS = [(-63.9, -54.7), (-45.0, -31.0), (-10.2, 4.3), (25.3, 44.5), (54.5, 63.8)]
DECK_W, DECK_E = xa(-75.0), xa(75.0)
B_GATE = MP.B_GATE                  # the concourse's open north side, its iron screen
B_END = SHED_B0 + NB * BAY          # the frame's edge, in the seventh bay
B_STUB = B_GATE + 2.4               # where the stub tracks end, at their bumpers (approximate)
TRACK_SRC = [SRC['haer-3'], SRC['haer-2'], SRC['nhl']]
DECK_SRC = [SRC['haer-photo-1'], SRC['bdc'], SRC['haer-2']]


def pieces(b0, b1, step=6.0):
    """Lengths from b0 to b1, broken at every truss line between (so a piece lies under one bay)
    and then into pieces no longer than `step`."""
    cuts = [b0] + [SHED_B0 + k * BAY for k in range(NB + 1) if b0 + 0.5 < SHED_B0 + k * BAY < b1 - 0.5] + [b1]
    out = []
    for p, q in zip(cuts, cuts[1:]):
        n = max(1, math.ceil((q - p) / step - 1e-9))
        out += [(p + (q - p) * i / n, p + (q - p) * (i + 1) / n) for i in range(n)]
    return out


# The deck, from the concourse to the frame's edge: steel girders on bents (HAER VA-4-1, a
# photograph from the southeast, shows the elevated platform on steel bents braced crosswise).
for k, (b0, b1) in enumerate(pieces(B_GATE, B_END, BAY)):
    part(f'mss-d-deck-{k}', 'Main Street Station: deck', rect(DECK_W, DECK_E, b0, b1), DECK_BOTTOM, DECK, 'ballast', 'written',
         'The deck that carries the tracks and platforms at the level of the waiting room, over the ground below: the platforms sit on the original trestles (Building Design + Construction). Its girders\' depth is approximate.',
         DECK_SRC)
# The bents under it: posts at each truss line, a cap beam across, crosswise braces between the
# outer posts. Their number and size are approximate (the photograph, not a drawing).
POSTS = [-72.0, -54.0, -36.0, -18.0, 0.0, 18.0, 36.0, 54.0, 72.0]
# The ground under the deck's two sides, roughly (3DEP): the bracing stands on it.
GROUND_UNDER = {'w': 9.0, 'e': 8.4}
for k in range(NB + 1):
    b = SHED_B0 + k * BAY
    for j, x in enumerate(POSTS):
        a = xa(x)
        part(f'mss-d-post-{k}-{j}', 'Main Street Station: trestle post', rect(a - 0.2, a + 0.2, b - 0.2, b + 0.2), None, DECK_BOTTOM - 0.5, 'steel', 'approximate',
             'A post of the steel trestle under the deck. HAER photograph VA-4-1 shows the deck on steel bents; their spacing here is approximate.', DECK_SRC)
    part(f'mss-d-cap-{k}', 'Main Street Station: trestle bent', rect(DECK_W, DECK_E, b - 0.2, b + 0.2), DECK_BOTTOM - 0.5, DECK_BOTTOM, 'steel', 'approximate',
         'The cap beam of a trestle bent under the deck. Approximate.', DECK_SRC)
for k in range(NB):
    b0 = SHED_B0 + k * BAY
    for side, x in (('w', POSTS[0]), ('e', POSTS[-1])):
        a = xa(x)
        z0 = GROUND_UNDER[side]
        hgt = DECK_BOTTOM - 0.5 - z0
        part(f'mss-d-xbrace-{side}-{k}', 'Main Street Station: trestle bracing', plane(a + 0.06, b0 + 0.2, a + 0.06, b0 + BAY - 0.2, 0.12), z0, DECK_BOTTOM - 0.5, 'steel', 'approximate',
             'Bracing between two posts of the trestle, as HAER photograph VA-4-1 shows it along the deck\'s east side. Approximate.', DECK_SRC,
             shape='frame', members=[[0, 0.6, BAY - 0.4, hgt, 0.12], [0, hgt, BAY - 0.4, 0.6, 0.12]])

# Platforms, in pieces so each sorts among the trains beside it.
for j, (x0, x1) in enumerate(PLATFORMS):
    for k, (b0, b1) in enumerate(pieces(B_GATE if j in (0, 4) else B_STUB - 0.6, B_END)):
        part(f'mss-d-platform-{j}-{k}', 'Main Street Station: platform', rect(xa(x0), xa(x1), b0, b1), DECK, FF, 'ramp', 'drawn',
             'A platform, as the cross section (HAER VA-4, sheet 3) draws it: its width, and its top about 1 ft above the rails. Where it meets the concourse is approximate.',
             TRACK_SRC)
# The platform heads before the concourse: one walk across the stub tracks' ends (approximate).
part('mss-d-apron', 'Main Street Station: platform heads', rect(xa(-45.0), xa(44.5), B_GATE, B_STUB - 0.6), DECK, FF, 'ramp', 'approximate',
     'The walk along the ends of the stub tracks, between the concourse\'s gates and the platforms. HAER photographs VA-4-9 to VA-4-11 show the gates opening on to the platforms; this walk\'s width is approximate.',
     [SRC['haer-photo-9'], SRC['haer-2']])

for t, x in TRACKS.items():
    a = xa(x)
    through = t in ('w', 'e')
    for k, (b0, b1) in enumerate(pieces(B_STUB if not through else B_GATE, B_END)):
        part(f'mss-d-track-{t}-{k}', 'Main Street Station: track', strip(a - 1.3, a + 1.3, b0, b1), DECK, DECK + 0.34, 'steel', 'drawn',
             ('A through track under the shed\'s overhang' if through else 'One of the six stub tracks under the shed') +
             ', placed from the cross section (HAER VA-4, sheet 3). Ties and rails at true size.', TRACK_SRC, shape='track')
    if not through:
        part(f'mss-d-bumper-{t}', 'Main Street Station: bumping post', rect(a - 1.2, a + 1.2, B_STUB - 0.6, B_STUB), DECK, DECK + 1.3, 'steel', 'approximate',
             'The stop at the end of a stub track. Its place and form are approximate: the plan (HAER VA-4, sheet 2) ends the tracks at the station end of the shed.', TRACK_SRC)

# ---- the through tracks alongside the head house and over Main Street -------------------------
# Each railroad's through track passes the head house on its own side on a trestle, and crosses
# Main Street on a bridge (HABS VA-848: "railroad tracks extend on either side of the building
# across bridges over Main Street"). The Seaboard used the west side, the C&O the east (Library
# of Congress, 2026; SEABOARD lettered on the west trestle in Detroit Publishing 4a18653). They
# are drawn straight to the frame's edge; today's lines (OSM) curve away beyond it.
for side, t in (('w', 'w'), ('e', 'e')):
    a = xa(TRACKS[t])
    walk = (MP.HH_E + 0.4, a - 1.7) if side == 'e' else (a + 1.7, MP.HH_W - 0.4)
    outer = (a + 2.4) if side == 'e' else (a - 2.4)
    lo, hi = (min(walk[0], outer), max(walk[1], outer))
    for k, (b0, b1) in enumerate(pieces(-27.0, B_GATE, 7.0)):
        part(f'mss-d-side-deck-{side}-{k}', 'Main Street Station: trestle deck', rect(lo, hi, b0, b1), DECK_BOTTOM, DECK, 'ballast', 'written',
             'The deck of the elevated through track beside the head house, carried on a trestle and across Main Street on a bridge (HABS VA-848; Detroit Publishing photographs). Its width and girders are approximate.',
             [SRC['habs-data'], SRC['detroit-east'], SRC['detroit-west']])
        if b1 > 2.0:
            part(f'mss-d-side-walk-{side}-{k}', 'Main Street Station: platform beside the head house', rect(walk[0], walk[1], max(b0, 2.0), b1), DECK, FF, 'ramp', 'written',
                 'The plank platform alongside the head house at the level of the first floor, as the Detroit Publishing photograph from the east (4a10737) shows it, with its iron railing. Its width is approximate.',
                 [SRC['detroit-east']])
        part(f'mss-d-track-{t}-s{k}', 'Main Street Station: track', strip(a - 1.3, a + 1.3, b0, b1), DECK, DECK + 0.34, 'steel', 'written',
             'The through track beside the head house, on its trestle. Its line here is approximate.', [SRC['habs-data'], SRC['osm-sal' if side == 'w' else 'osm-co']], shape='track')
    for k, b in enumerate([-28.0, -12.0, 2.0, 16.0, 30.0]):
        for x in (lo + 0.4, hi - 0.4):
            if b < -27 or b > B_GATE:
                continue
            # No post stands in Main Street: the bridge spans it.
            if -16.0 < b < -4.0:
                continue
            part(f'mss-d-side-post-{side}-{k}-{"a" if x == lo + 0.4 else "b"}', 'Main Street Station: trestle post', rect(x - 0.25, x + 0.25, b - 0.25, b + 0.25), None, DECK_BOTTOM, 'steel', 'approximate',
                 'A post of the trestle beside the head house. The trestles are documented as structure (HABS VA-848, the Detroit Publishing photographs), not post by post; their places are approximate.',
                 [SRC['habs-data'], SRC['detroit-west']])
    # The bridge's girders over Main Street (approximate depth).
    for g, x in enumerate((lo + 0.3, hi - 0.3)):
        part(f'mss-d-bridge-{side}-{g}', 'Main Street Station: bridge over Main Street', rect(x - 0.3, x + 0.3, -27.0, -2.0), DECK_BOTTOM - 1.2, DECK_BOTTOM, 'steel', 'written',
             'A plate girder of the bridge that carries the track over Main Street (HABS VA-848). Its depth is approximate.', [SRC['habs-data'], SRC['habs-photo-1971']])

# ---- on the platforms: carts, lamps, railings -------------------------------------------------
CART = ('A four-wheel baggage cart on the platform, as photographs of about 1950 and 1969 show them here (Old Dominion Chapter NRHS, J. I. Kelly, '
        'about 1950; HABS VA-848-A-1). Size approximate.')
for k, (x0, b0) in enumerate(((56.0, SHED_B0 + 3.0), (56.0, SHED_B0 + 7.0), (27.0, SHED_B0 + 14.0))):
    a0 = xa(x0)
    part(f'mss-d-cart-{k}', 'Main Street Station: baggage cart', rect(a0, a0 + 1.1, b0, b0 + 3.0), FF + 0.45, FF + 0.75, 'wood', 'written', CART,
         [SRC['odc-1950'], SRC['habs-photo-a1']])
    for j, (u0, u1) in enumerate(((0.3, 0.6), (2.4, 2.7))):
        part(f'mss-d-cart-{k}-wheels-{j}', 'Main Street Station: baggage cart', rect(a0 + 0.05, a0 + 1.05, b0 + u0, b0 + u1), FF, FF + 0.45, 'coal', 'written', CART,
             [SRC['odc-1950'], SRC['habs-photo-a1']])
    part(f'mss-d-cart-{k}-rack', 'Main Street Station: baggage cart', rect(a0, a0 + 1.1, b0, b0 + 0.08), FF + 0.75, FF + 1.6, 'wood', 'written', CART,
         [SRC['odc-1950'], SRC['habs-photo-a1']])
# Along the east trestle beside the head house: its lattice railing and gooseneck lamps.
RAIL = ('The iron railing along the outer edge of the trestle\'s deck beside the head house, of crossed bars (HABS photographs VA-848-11 and '
        'VA-848-A-1; Detroit Publishing 4a10737). Its pattern\'s size is approximate.')
a_e = xa(TRACKS['e']) + 2.4
ln = B_GATE + 27.0
lat = [[0, 0.05, round(ln, 3), 0.05, 0.08], [0, 1.05, round(ln, 3), 1.05, 0.1]]
u = 0.0
while u < ln - 0.5:
    lat += [[round(u, 3), 0.1, round(u + 0.5, 3), 1.0, 0.035], [round(u, 3), 1.0, round(u + 0.5, 3), 0.1, 0.035]]
    if round(u / 0.5) % 6 == 0:
        lat.append([round(u, 3), 0, round(u, 3), 1.1, 0.08])
    u += 0.5
part('mss-d-rail-e', 'Main Street Station: railing', plane(a_e - 0.06, -27.0, a_e - 0.06, B_GATE, 0.06), FF, FF + 1.1, 'iron', 'written', RAIL,
     [SRC['habs-photo-11'], SRC['habs-photo-a1'], SRC['detroit-east']], shape='frame', members=lat)
LAMP = ('A gooseneck lamp on the platform beside the head house (HABS photograph VA-848-11, 1971; VA-848-A-1, 1969). Present in 1952 is likely, '
        'not recorded. Places approximate.')
for k, b in enumerate((-20.0, 4.0, 18.0)):
    a = a_e - 0.35
    part(f'mss-d-lamp-{k}', 'Main Street Station: lamp', plane(a, b, a, b + 1.0, 0.12), FF, FF + 4.4, 'iron', 'approximate', LAMP,
         [SRC['habs-photo-11'], SRC['habs-photo-a1']], shape='frame', members=[[0.06, 0, 0.06, 4.3, 0.12], [0.06, 4.3, 0.7, 4.3, 0.08], [0.55, 3.95, 0.9, 3.95, 0.3]])

# ---- trains, about 1952 -----------------------------------------------------------------------
# The train lines: kind 'rail' with an elevation, so the trains stand on the deck and no track
# is drawn on the ground. The Seaboard used the west side, the C&O the east (the site plan in The
# Railroad Gazette, 1900; Sanborn 1905 and 1952); which stub track each train used is not known.
def rail_line(t, b0, b1, train, note, sources):
    a = xa(TRACKS[t])
    line = [lonlat(ab(a, b)) for b in (b0, (b0 + b1) / 2, b1)]
    features.append({'id': f'mss-track-{t}', 'name': 'Main Street Station: train', 'kind': 'rail', 'from': 1901, 'to': 1985, 'line': line,
                     'elevation': DECK + 0.2, 'train': train, 'note': note, 'sources': sources})


SIDES = [SRC['rg-1900'], SRC['sanborn-1952'], SRC['haer-3']]
CO = ('A Chesapeake and Ohio passenger train: a 4-6-4 steam engine of the C&O\'s L-2 class and cars in the C&O\'s blue, with a yellow band '
      'along the top and gray below, as a dated color photograph shows one just north of the station on February 25, 1953 (piedmontsub.com, '
      'L. Z. Daily). The engine and cars are drawn plain; the number of cars is illustrative.')
rail_line('5', B_STUB + 1.0, B_END + 60, {'cars': 3, 'at': 0, 'livery': 'co'}, CO, [SRC['co-306-1953']] + SIDES)
rail_line('6', B_STUB + 1.0, B_END + 60, {'cars': 3, 'at': 0.5, 'engine': False, 'livery': 'co'},
          'C&O passenger cars at a platform, in the blue, yellow and gray of the 1953 photograph (piedmontsub.com). Illustrative.', [SRC['co-306-1953']] + SIDES)
SAL = ('A Seaboard Air Line passenger train: a streamlined diesel unit, drawn plain in gray, and heavyweight cars in Pullman green. A 1955 '
       'photograph records the Seaboard\'s E8 diesels at its Richmond station (RailPictures.net, N. Plagens); none opened shows the engine '
       'of a Seaboard train here in 1952, so engine and colors are approximate. The Orange Blossom Special called in December 1952 (Official Guide).')
rail_line('2', B_STUB + 1.0, B_END + 60, {'cars': 3, 'at': 0, 'power': 'diesel'}, SAL, [SRC['sal-e8-1955'], SRC['obs-1952']] + SIDES)

# ---- the city: era rules and dates from the downtown series ---------------------------------
dt = json.loads(DOWNTOWN.read_text())
rules = [
    {'where': {'id': ['w38232584', 'w169784634', 'w1093994778', 'w1031329271', 'w752081997', 'w6036180', 'w169671715', 'w1031329272']}, 'eras': [],
     'note': 'Today\'s tracks and platform at the station, as OSM maps them: the curated deck, tracks and trains stand in for them.'},
] + dt['rules']
dates = [
    {'id': 'w113030476', 'name': 'Main Street Station (today\'s outline)', 'year': 2026, 'source': SRC['osm-station'],
     'note': 'Today\'s outline, with the shed enclosed in glass in 2017, is drawn only in today\'s view; earlier views draw the station from its curated parts.'},
    {'id': 'w366226941', 'name': 'Main Street Station head house (today\'s outline)', 'year': 2026, 'source': SRC['osm-headhouse'],
     'note': 'Drawn from curated parts before today.'},
    {'id': 'w366226942', 'name': 'Main Street Station clock tower (today\'s outline)', 'year': 2026, 'source': SRC['osm-tower'],
     'note': 'Drawn from curated parts before today.'},
] + dt['dates']

history = {
    'title': 'Main Street Station, about 1952',
    'method': ('The station is modeled from curated parts: the train shed from HAER VA-4\'s measured drawings (1970), traced from '
               'the cross section and the plan; the head house\'s rooms on its two public floors traced from the plans in The Railroad '
               'Gazette (July 13, 1900), which The Times (November 24, 1901) describes as built, fitted to OpenStreetMap\'s outline; its '
               'upper floors from HABS VA-848 (1969); its heights and stonework scaled from photographs. Uses of the rooms in 1952 are '
               'not all recorded. No other building stands in the frame; the streets and today\'s OSM features follow the downtown '
               'series\' era rules (no I-95 before 1958). Trains follow dated photographs where one was found. Every part names its sources.'),
    'present': 2026,
    'about': ('Main Street Station, the Union Station of the Seaboard Air Line and the Chesapeake and Ohio, opened on 27 November 1901 '
              '(HABS VA-848). The Seaboard left for Broad Street Station in 1959.'),
    'epochs': [{'year': 1952, 'title': 'Main Street Station, about 1952',
                'note': 'Both railroads still used the station; I-95 was not yet built beside it (opened 1958).'}],
    'features': features,
    'rules': rules,
    'dates': dates,
    'sanborn': dt['sanborn'],
    'streetsNearBuildings': dt.get('streetsNearBuildings', 60),
}
OUT.write_text(json.dumps(history, indent=1, ensure_ascii=False) + '\n')
print(f'{OUT.relative_to(ROOT)}: {len(features)} features')
