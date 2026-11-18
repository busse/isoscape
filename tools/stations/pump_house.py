#!/usr/bin/env python3
"""Model the Byrd Park Pump House (the "New Pump-House", Richmond) as it worked in about 1885,
for a cutaway: ROUGH DRAFT. Written with Claude for Chris Busse.

Everything is placed in one local frame, in meters, fitted to OpenStreetMap's outline of the
building (way 236152567):

  a  along the building's long axis toward the east-southeast (bearing 119.7 deg), from its
     west face (OSM node 2442157628, the southwest corner of the 1883 block);
  b  across it toward the north-northeast (bearing 29.7 deg), from its south face.

The 1883 block is about 39.4 m by 16.4 m (OSM). The 1905 annex, west of a = 0, is not drawn:
this is the building of 1885. Levels are the 2019 schematic design study's (Timmons Group with
3north, from a laser scan), read as feet above NAVD88 (an assumption): the machine room floor
("Level 1 upper") 92.06 ft = 28.06 m, the pits ("Level 1 lower") 86.31 ft = 26.31 m, the
pavilion floor ("Level 2") 114.23 ft = 34.77 m, the building 46 ft high.

The machinery is The American Engineer's of December 26, 1884 (p. 260): nine single-acting
plunger pumps in three gangs, each gang on one partial vertical turbine of the outward-flow
(Fourneyron) type, 21 ft inside and 28 ft outside, under a 20-ft fall; a 12-in shaft per wheel
with three 36-in cranks at 120 deg; 16-ft connecting rods up to crossheads in guides on lattice
girders overhead, two rods down from each to a 14-in plunger in a 36-in chamber; one 36-in
suction, one 30-in discharge main, 3,600 ft to the reservoir. Where in the room each gang
stood is not known from any source reached: the gangs are spaced evenly along the central
block (approximate). The water levels are inferred: the forebay "level with a walkway that
wraps around the north facade" (NRHP 2002), the walkway's height from the lidar; the tail 20 ft
lower (The American Engineer). The canals' beds and banks are today's lidar (3DEP, in the
I-195 to Rocketts cache).

    python3 tools/stations/pump_house.py   # writes history/pump-house.json
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'history' / 'pump-house.json'

LON0, LAT0 = -77.4861874, 37.5365919          # OSM node 2442157628: a = 0, b = 0
KX = 111_320 * math.cos(math.radians(LAT0))
KY = 110_574


def unit(bearing):
    r = math.radians(bearing)
    return (math.sin(r), math.cos(r))


UA, UB = unit(119.7), unit(29.7)


def lonlat(a, b):
    x, y = a * UA[0] + b * UB[0], a * UA[1] + b * UB[1]
    return [round(LON0 + x / KX, 8), round(LAT0 + y / KY, 8)]


def rect(a0, a1, b0, b1):
    return [lonlat(a0, b0), lonlat(a1, b0), lonlat(a1, b1), lonlat(a0, b1)]


def quad(pts):
    return [lonlat(a, b) for a, b in pts]


def octagon(a, b, r, n=10):
    return [lonlat(a + r * math.cos(2 * math.pi * k / n), b + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


# ---- sources -------------------------------------------------------------------------------

SRC = {
    'ae-1884': 'https://www.friendsofpumphouse.org/uploads/1/1/5/3/115357711/the-american-engineer_orig.jpg',
    'nrhp': 'https://www.dhr.virginia.gov/VLR_to_transfer/PDFNoms/127-0193_New_Pump_House_2002_Final_Nomination.pdf',
    'haer': 'https://www.loc.gov/item/va1319/',
    'haer-5': 'https://tile.loc.gov/storage-services/service/pnp/habshaer/va/va1300/va1319/photos/162148pv.jpg',
    'study-2019': 'https://issuu.com/3north/docs/php_pump_house_park_schematic_desig',
    'bolling-1900': 'http://www.waterworkshistory.us/VA/Richmond/RichmondWaterWorks1900.pdf',
    'friends-tour': 'https://www.friendsofpumphouse.org/pump-house-tour.html',
    'quinn-evans': 'https://www.friendsofpumphouse.org/uploads/1/1/5/3/115357711/pump_house_vision_plan.pdf',
    'artwork-1897': 'https://rvanews.com/news/pumphouse-circa-1897/124415',
    'osm': 'https://www.openstreetmap.org/way/236152567',
    'lidar': 'https://www.usgs.gov/3d-elevation-program',
}
AE, NRHP, HAER, STUDY, OSM = SRC['ae-1884'], SRC['nrhp'], SRC['haer'], SRC['study-2019'], SRC['osm']

# ---- levels (m above sea level) ------------------------------------------------------------
FOOT = 23.6          # foundations (approximate)
PIT = 26.31          # "Level 1 lower" (2019 study)
FLOOR = 28.06        # machine room floor, "Level 1 upper" (2019 study)
PAV = 34.77          # pavilion floor, "Level 2" (2019 study)
EAVE = 38.4          # pavilion eaves (approximate: scaled from HAER VA-34-1)
RIDGE = FLOOR + 46 * 0.3048   # 46 ft (2019 study), read from the machine room floor
WING_RIDGE = 43.9    # the wings' cross-gables (approximate: HAER VA-34-1)
FOREBAY = 30.7       # forebay water (inferred: about 0.8 m under the north walkway, lidar 31.5)
TAIL = FOREBAY - 20 * 0.3048  # 20-ft fall (The American Engineer)
BED = 21.4           # canal beds: today's lidar water surface

# ---- plan (m) ------------------------------------------------------------------------------
L, D = 39.4, 16.4            # the 1883 block (OSM)
WING = 7.5                   # wing width along a (approximate, from HAER VA-34-1 and the Quinn Evans plan)
CB = (WING, L - WING, 1.2, 15.9)   # the central block: wings stand 1.2 m proud on the south, 0.5 m on the north (NRHP: more on the south)
T = 0.9                      # wall thickness (approximate)
HUB_B = 8.5                  # the shafts' line across the room (approximate)
R_OUT = 28 * 0.3048 / 2      # wheel radius, 28 ft outside (The American Engineer)
HUB_Z = 29.0                 # shaft height (approximate: a 16-ft rod must reach crossheads under the pavilion floor)
CUT_B = 5.0                  # the cut plane (regions/pump-house-cutaway.json)
GANGS = [CB[0] + 0.3 + k * 8.1 for k in range(3)]   # each gang's west end (approximate)

features = []


def part(id_, name, ring, z0, z1, tone, conf, note, sources, **more):
    f = {'id': id_, 'name': name, 'kind': 'landmark', 'from': 1883, 'to': 1899, 'ring': ring,
         'elevation': round(z0, 3), 'upTo': round(z1, 3), 'tone': tone, 'confidence': conf, 'note': note, 'sources': sources}
    f.update({k: v for k, v in more.items() if v is not None})
    features.append(f)


PH = 'The New Pump-House'
SHELL = ('Random-ashlar granite from the site and James Netherwood\'s quarries, built 1881-83 by Col. Wilfred Emory Cutshaw, city engineer '
         '(NRHP 2002). Outline from OpenStreetMap; wall thickness approximate.')

# ---- the wings (kept whole: the cut does not touch them) ------------------------------------
for side, (a0, a1) in (('w', (0.0, WING)), ('e', (L - WING, L))):
    name = f'{PH}: {"west" if side == "w" else "east"} wing'
    note = (SHELL + ' Each end is a cross-gabled wing with lancet windows, a steep slate roof and pinnacled gables; the upper floor held the '
            f'{"gentlemen" if side == "w" else "ladies"}\'s powder room and offices, and a stair at the south corner (NRHP 2002). '
            'The wing roof\'s height is scaled from HAER VA-34-1 (approximate).')
    # Walls (hollow, so a cut through a wing reads as a plan), the machine room floor and the upper floor.
    for wid, rg in (('s', rect(a0, a1, 0, T)), ('n', rect(a0, a1, D - T, D)), ('end', rect(a0, a0 + T, T, D - T) if side == 'w' else rect(a1 - T, a1, T, D - T))):
        part(f'ph-w-{side}-wall-{wid}', name, rg, FOOT, EAVE, 'stone', 'written', note, [NRHP, HAER, OSM])
    inner = (a0 + T, a1) if side == 'w' else (a0, a1 - T)
    part(f'ph-w-{side}-floor1', name, rect(inner[0], inner[1], T, D - T), FLOOR - 0.25, FLOOR, 'floor', 'approximate', note, [NRHP, STUDY])
    part(f'ph-w-{side}-floor2', name, rect(inner[0], inner[1], T, D - T), PAV - 0.3, PAV, 'floor', 'approximate',
         'The wing\'s upper floor, level with the pavilion: powder room and offices, with lancet windows opening onto the pavilion (NRHP 2002).', [NRHP, STUDY])
    part(f'ph-w-{side}-stair', name, rect(inner[0] + 0.3, inner[0] + 1.5, T + 0.2, T + 6.0) if side == 'w' else rect(inner[1] - 1.5, inner[1] - 0.3, T + 0.2, T + 6.0),
         FLOOR, PAV, 'wood', 'written', 'Stairs at the southern corners of the machine room, with a landing halfway up to the viewing catwalk, then on to the pavilion (NRHP 2002). Form approximate.',
         [NRHP], shape='stair', steps=20)
    # Its inner wall toward the central block, above the pavilion floor (lancet windows onto the pavilion: NRHP 2002).
    part(f'ph-w-{side}-wall-in', name, rect(a1 - T, a1, T, D - T) if side == 'w' else rect(a0, a0 + T, T, D - T), PAV, EAVE, 'plaster', 'written', note, [NRHP])
    # The cross-gable: its eaves on the wing's east and west walls (the ring's first and third edges).
    part(f'ph-w-{side}-roof', name, [lonlat(a1 + 0.3, -0.3), lonlat(a1 + 0.3, D + 0.3), lonlat(a0 - 0.3, D + 0.3), lonlat(a0 - 0.3, -0.3)],
         EAVE, WING_RIDGE, 'roof', 'approximate', note, [NRHP, HAER], shape='gable')
    for bb in (-0.3, D + 0.3):
        part(f'ph-w-{side}-pinnacle-{0 if bb < 0 else 1}', name, rect((a0 + a1) / 2 - 0.3, (a0 + a1) / 2 + 0.3, bb - 0.3, bb + 0.3),
             WING_RIDGE - 0.6, WING_RIDGE + 0.9, 'stone', 'approximate', 'A flat-topped pinnacle crowning the gable (NRHP 2002). Size approximate.', [NRHP, HAER])

# ---- the central block: machine room below, pavilion above ----------------------------------
A0, A1, B0, B1 = CB
WALL_NOTE = SHELL + ' The north wall stands in the forebay\'s water to the walkway, so the machine room is below water on that side (NRHP 2002).'
part('ph-c-wall-south', f'{PH}: south wall', rect(A0, A1, B0, B0 + T), FOOT, PAV - 0.3, 'stone', 'written',
     WALL_NOTE + ' Five bays of double lancet windows lit the machine room from the south (NRHP 2002); not drawn in the rough draft.', [NRHP, HAER, OSM])
part('ph-c-wall-north', f'{PH}: north wall', rect(A0, A1, B1 - T, B1), FOOT, PAV - 0.3, 'stone', 'written', WALL_NOTE, [NRHP, HAER, OSM])

# The machine room floor, with pits for the wheels and pumps (sizes approximate; the pits survive, full of water: NRHP 2002).
FLOOR_NOTE = ('The machine room floor: wood in its day, "long removed"; granite and earth today (NRHP 2002). Level from the 2019 study. '
              'The pits\' outlines here are approximate.')
PIT_B = (4.0, 13.0)
xs = [A0 + T * 0.0]
for g in GANGS:
    xs += [g, g + 7.6]
xs.append(A1)
for k in range(0, len(xs), 2):
    if xs[k + 1] - xs[k] > 0.2:
        part(f'ph-c-floor-{k // 2}', f'{PH}: machine room floor', rect(xs[k], xs[k + 1], B0 + T, B1 - T), FLOOR - 0.25, FLOOR, 'floor', 'written', FLOOR_NOTE, [NRHP, STUDY])
for k, g in enumerate(GANGS):
    part(f'ph-c-floor-s{k}', f'{PH}: machine room floor', rect(g, g + 7.6, B0 + T, PIT_B[0]), FLOOR - 0.25, FLOOR, 'floor', 'written', FLOOR_NOTE, [NRHP, STUDY])
    part(f'ph-c-floor-n{k}', f'{PH}: machine room floor', rect(g, g + 7.6, PIT_B[1], B1 - T), FLOOR - 0.25, FLOOR, 'floor', 'written', FLOOR_NOTE, [NRHP, STUDY])
    part(f'ph-c-pit-{k}', f'{PH}: pump pit', rect(g + 1.7, g + 7.6, PIT_B[0], PIT_B[1]), PIT - 0.4, PIT, 'stone', 'written',
         'A pump pit, its floor at "Level 1 lower" (2019 study); the pits hold water today (NRHP 2002). Outline approximate.', [NRHP, STUDY, SRC['haer-5']])

# ---- the three gangs ---------------------------------------------------------------------------
AE_NOTE = (' The American Engineer, December 26, 1884: designed by the late Prof. Charles A. Smith, built and erected by H. A. Ramsay '
           '(Ramsay Engineering Works, Baltimore) under contract with Col. W. E. Cutshaw.')
PLACE = ' Its place in the room is approximate: no plan of the room with the machines was found that can be scaled.'
for k, g in enumerate(GANGS):
    wa = g + 0.8                                 # the wheel's plane
    pumps = [g + 3.2, g + 4.9, g + 6.6]          # the three cranks
    # Wheel pit and tail water.
    part(f'ph-c-wheelpit-{k}', f'{PH}: wheel pit', rect(wa - 0.8, wa + 0.8, HUB_B - R_OUT - 0.3, HUB_B + R_OUT + 0.3), TAIL - 1.2, TAIL - 0.9, 'stone', 'approximate',
         'The wheel\'s pit, down to the tail water, where the cast-iron diffuser under the wheel let the spent water go to the tailrace (The American Engineer, 1884). Depth and size approximate.' + PLACE, [AE])
    part(f'ph-c-tailpit-{k}', f'{PH}: tail water', rect(wa - 0.8, wa + 0.8, HUB_B - R_OUT - 0.3, HUB_B + R_OUT + 0.3), TAIL - 0.9, TAIL, 'water', 'approximate',
         'Tail water in the wheel pit, 20 ft below the forebay (The American Engineer, 1884).' + PLACE, [AE])
    part(f'ph-c-diffuser-{k}', f'{PH}: diffuser', rect(wa - 0.7, wa + 0.7, HUB_B - 2.2, HUB_B + 2.2), TAIL - 0.2, HUB_Z - R_OUT + 0.15, 'iron', 'written',
         'A large cast-iron diffuser below the wheel "delivers the water into the tail-race with the least possible loss" (The American Engineer, 1884). Shape approximate.', [AE])
    # The wheel: a disc standing on its diameter across the room (its plane runs north-south, its shaft east-west).
    part(f'ph-c-wheel-{k}', f'{PH}: turbine wheel {k + 1}', quad([(wa - 0.45, HUB_B - R_OUT), (wa - 0.45, HUB_B + R_OUT), (wa + 0.45, HUB_B + R_OUT), (wa + 0.45, HUB_B - R_OUT)]),
         HUB_Z - R_OUT, HUB_Z + R_OUT, 'iron', 'written',
         'A partial vertical turbine of the outward-flow (Fourneyron) type, all iron, 21 ft inside and 28 ft outside; water under a 20-ft head entered through its center into a guide chamber '
         'that turned it onto about a quarter of the buckets.' + AE_NOTE + ' Bolling (1900) gives 23 1/2 ft. Replaced in 1891 by geared Leffel wheels (NRHP 2002).' + PLACE,
         [AE, SRC['bolling-1900'], NRHP], shape='disc')
    # The penstock: from the head gate at the forebay, through the north wall, into the wheel's center.
    pa = wa - 1.5
    part(f'ph-c-penstock-{k}', f'{PH}: penstock {k + 1}', rect(pa - 0.76, pa + 0.76, HUB_B, 22.5), HUB_Z - 0.76, HUB_Z + 0.76, 'iron', 'written',
         'An iron penstock 5 ft in diameter, from the forebay through the north wall into the wheel\'s center (The American Engineer, 1884); three openings in the north wall (NRHP 2002; '
         'HAER VA-34-5). Drawn level and square; in the engraving it drops to the wheel on a slant.' + PLACE, [AE, NRHP, SRC['haer-5']])
    part(f'ph-c-penstock-elbow-{k}', f'{PH}: penstock {k + 1}', rect(pa - 0.76, wa - 0.45, HUB_B - 0.76, HUB_B + 0.76), HUB_Z - 0.76, HUB_Z + 0.76, 'iron', 'written',
         'The penstock\'s elbow into the wheel\'s center (The American Engineer, 1884).' + PLACE, [AE])
    part(f'ph-x-gate-{k}', f'{PH}: head gate {k + 1}', rect(pa - 1.1, pa + 1.1, 21.6, 22.6), TAIL, FOREBAY + 1.6, 'wood', 'written',
         'A sluice gate 6 ft by 6 ft at the penstock\'s head, worked by a hydraulic cylinder 10 in in diameter (The American Engineer, 1884). Frame drawn as a block; place approximate.', [AE])
    part(f'ph-x-gate-cyl-{k}', f'{PH}: head gate {k + 1}', octagon(pa, 22.1, 0.25), FOREBAY + 1.6, FOREBAY + 3.0, 'iron', 'written',
         'The gate\'s hydraulic cylinder, 10 in (The American Engineer, 1884).', [AE])
    # The tailrace tunnel, under the south walkway to the canal's lower level.
    part(f'ph-x-tailrace-{k}', f'{PH}: tailrace {k + 1}', rect(wa - 0.9, wa + 0.9, -9.0, HUB_B - R_OUT - 0.3), TAIL - 0.9, TAIL, 'water', 'approximate',
         'A tunnel under the stone walkway carried the spent water out to the canal on the south side (NRHP 2002; Friends of Pump House tour). Number, size and line approximate: one per wheel is assumed.',
         [NRHP, SRC['friends-tour']])
    # Shaft, cranks, rods, crossheads, pumps.
    part(f'ph-c-shaft-{k}', f'{PH}: shaft {k + 1}', rect(wa - 0.6, pumps[-1] + 0.6, HUB_B - 0.17, HUB_B + 0.17), HUB_Z - 0.17, HUB_Z + 0.17, 'iron', 'written',
         'A wrought-iron shaft 12 in in diameter, keyed to the wheel, with three cranks of 36-in throw set 120 deg apart (The American Engineer, 1884).' + PLACE, [AE])
    for j, pa_ in enumerate(pumps):
        tag = f'{k}-{j}'
        part(f'ph-c-crank-{tag}', f'{PH}: crank', rect(pa_ - 0.12, pa_ + 0.12, HUB_B - 0.3, HUB_B + 0.3), HUB_Z - 0.5, HUB_Z + 0.95, 'iron', 'written',
             'A crank of 36-in throw (The American Engineer, 1884).', [AE])
        ch = PAV - 0.75   # the crosshead, under the floor (a 16-ft rod would put it a little higher: approximate)
        part(f'ph-c-rod-{tag}', f'{PH}: connecting rod', rect(pa_ - 0.09, pa_ + 0.09, HUB_B - 0.09, HUB_B + 0.09), HUB_Z + 0.9, ch - 0.15, 'iron', 'written',
             'A connecting rod 16 ft long, 4 by 9 in, up to the crosshead overhead (The American Engineer, 1884).', [AE])
        part(f'ph-c-crosshead-{tag}', f'{PH}: crosshead', rect(pa_ - 0.25, pa_ + 0.25, HUB_B - 0.75, HUB_B + 0.75), ch - 0.15, ch + 0.2, 'iron', 'written',
             'A crosshead working in fixed guides held by lattice girders overhead (The American Engineer, 1884).', [AE])
        for s, db in (('s', -0.6), ('n', 0.6)):
            part(f'ph-c-pumprod-{tag}-{s}', f'{PH}: pump rod', rect(pa_ - 0.05, pa_ + 0.05, HUB_B + db - 0.05, HUB_B + db + 0.05), FLOOR + 0.3, ch, 'iron', 'written',
                 'Two pump rods to each pump, from the crosshead down to the plunger (The American Engineer, 1884).', [AE])
        part(f'ph-c-plunger-{tag}', f'{PH}: plunger', rect(pa_ - 0.7, pa_ + 0.7, HUB_B - 0.7, HUB_B + 0.7), FLOOR + 0.2, FLOOR + 0.4, 'iron', 'written',
             'The yoke where the two pump rods take the plunger (approximate).', [AE])
        part(f'ph-c-pump-{tag}', f'{PH}: pump {3 * k + j + 1}', octagon(pa_, HUB_B, 0.46), PIT - 0.4, FLOOR + 0.2, 'iron', 'written',
             'One of nine vertical single-acting plunger pumps: a plunger 14 in in diameter in a chamber 36 in across, with double-beat Cornish valves of 20 in '
             '(The American Engineer, 1884); stroke 6 ft (NRHP 2002). Twelve million gallons a day for the nine against a head of 175 ft (The American Engineer).' + PLACE, [AE, NRHP])
        part(f'ph-c-airvessel-{tag}', f'{PH}: air vessel', octagon(pa_, HUB_B + 2.0, 0.33), PIT - 0.4, FLOOR + 2.0, 'iron', 'written',
             'An air vessel over each pump\'s discharge (The American Engineer, 1884). Size approximate.', [AE])
        part(f'ph-c-branch-{tag}', f'{PH}: discharge branch', rect(pa_ - 0.2, pa_ + 0.2, HUB_B + 0.4, 13.6), PIT, PIT + 0.4, 'iron', 'approximate',
             'From the pump to the main (approximate).', [AE])
    # Lattice girders over the gang, carrying the guides.
    for s, db in (('s', -1.0), ('n', 1.0)):
        part(f'ph-c-girder-{k}-{s}', f'{PH}: lattice girder', rect(g + 2.4, g + 7.4, HUB_B + db - 0.12, HUB_B + db + 0.12), PAV - 1.3, PAV - 0.32, 'iron', 'written',
             'Lattice girders over the pumps, holding the crosshead guides (The American Engineer, 1884); metal trusses under the pavilion floor are seen in HAER VA-34-5.', [AE, SRC['haer-5']])

# The common suction and discharge main, along the north side of the room.
part('ph-c-main', f'{PH}: discharge main', rect(GANGS[0] + 2.0, GANGS[-1] + 7.4, 13.3, 14.06), PIT, PIT + 0.76, 'iron', 'written',
     'The nine pumps discharge "through a common discharge pipe 30 in in diameter" (The American Engineer, 1884). Its line in the room is approximate.', [AE])
part('ph-c-suction', f'{PH}: suction', rect(A0 + 0.4, GANGS[-1] + 7.4, 14.1, 15.0), PIT, PIT + 0.91, 'iron', 'written',
     'The nine pumps drew "from one common suction pipe 36 in in diameter" (The American Engineer, 1884), from the forebay (1909 annual report: about 16 ft of head on it). '
     'A rising-stem valve in the northwest corner survives (NRHP 2002). Line approximate.', [AE, NRHP])
MID = (A0 + A1) / 2
part('ph-x-main-out', f'{PH}: main to the reservoir', rect(MID - 0.38, MID + 0.38, B1 - T, 22.0), PIT, PIT + 0.76, 'iron', 'written',
     'The 30-in main leaves the house northward, under the forebay, for the Byrd Park reservoir 3,600 ft away and 175 ft up (The American Engineer, 1884; NRHP 2002 sketch map, "pipe to Byrd Park reservoir"). '
     'Bolling (1900) gives a lift of 165 ft.', [AE, NRHP, SRC['bolling-1900']])
for k, b0 in enumerate(range(36, 90, 6)):
    f = {'id': f'ph-x-main-hill-{k}', 'name': f'{PH}: main to the reservoir', 'kind': 'landmark', 'from': 1883, 'to': 1899,
         'ring': rect(MID - 0.38, MID + 0.38, b0, b0 + 6), 'height': 0.76, 'tone': 'iron', 'confidence': 'approximate',
         'note': 'The 30-in main up the hill toward the reservoir, drawn on the ground; it ran buried (NRHP 2002 sketch map: a dashed pipe). Line approximate.',
         'sources': [AE, NRHP]}
    features.append(f)

# Catwalks and stair.
for k, g in enumerate(GANGS):
  part(f'ph-c-catwalk-grease-{k}', f'{PH}: greasing catwalk', rect(g + 2.4, g + 7.4, HUB_B + 1.3, HUB_B + 2.1), PAV - 2.2, PAV - 2.05, 'iron', 'written',
     'A catwalk "originally used to service and grease the joints", reached by a cast-iron spiral stair at the east end (NRHP 2002; HAER VA-34-6). Height and line approximate.', [NRHP, HAER])
part('ph-c-spiral', f'{PH}: spiral stair', octagon(A1 - 1.2, HUB_B + 1.7, 0.8), FLOOR, PAV - 2.05, 'iron', 'written',
     'An "ornate cast-iron spiral staircase at the east end" up to the greasing catwalk (NRHP 2002; HAER VA-34-6). The Friends\' tour puts it in the northwest corner.', [NRHP, HAER, SRC['friends-tour']])
part('ph-c-catwalk-view', f'{PH}: viewing catwalk', rect(A0, A1, B0 + T, B0 + T + 1.1), 29.33 + 1.2, 29.33 + 1.35, 'wood', 'written',
     'A catwalk hung on the south wall, reached from landings on the stairs at the south corners, where workers and pavilion visitors watched the machinery (NRHP 2002; Friends of Pump House). '
     'Height approximate (the 2019 study\'s mezzanine landing is 4 ft 2 in over the floor).', [NRHP, SRC['friends-tour'], STUDY])

# The pavilion: floor, arcades, ceiling, roof.
PAV_NOTE = ('The open-air pavilion over the machine room, 3,392 sq ft (Quinn Evans plan): a painted pine floor, a Gothic arcade of six Tudor arches each side on seven cast-iron columns, '
            'the two end arches narrower, with railings of zinc-coated tin; a flat ceiling on wooden trusses. Enclosed with glass in 1899 because rain came through the floor onto the machinery (NRHP 2002).')
for k in range(8):   # in pieces, so each sorts among the machines under it
    for j, (b0, b1) in enumerate(((B0, HUB_B - 1.2), (HUB_B - 1.2, HUB_B + 1.2), (HUB_B + 1.2, B1))):
        part(f'ph-c-pav-floor-{k}-{j}', f'{PH}: pavilion floor', rect(A0 + (A1 - A0) * k / 8, A0 + (A1 - A0) * (k + 1) / 8, b0, b1), PAV - 0.3, PAV, 'floor', 'written',
             PAV_NOTE + ' Level from the 2019 study.', [NRHP, STUDY, SRC['quinn-evans']])
COLS = [0.0, 3.2, 7.7, 12.2, 16.7, 21.2, 24.4]   # terminal arches 3.2 m, central ones 4.5 m (approximate)
for side, bb in (('s', B0 + 0.2), ('n', B1 - 0.2)):
    for j, c in enumerate(COLS):
        aa = A0 + c + (0.2 if j == 0 else -0.2 if j == 6 else 0)
        part(f'ph-c-col-{side}{j}', f'{PH}: pavilion arcade', rect(aa - 0.15, aa + 0.15, bb - 0.15, bb + 0.15), PAV, EAVE - 0.9, 'iron', 'written', PAV_NOTE, [NRHP, HAER, SRC['artwork-1897']])
    part(f'ph-c-arcade-head-{side}', f'{PH}: pavilion arcade', rect(A0, A1, bb - 0.2, bb + 0.2), EAVE - 0.9, EAVE, 'stone', 'written',
         PAV_NOTE + ' The arches and tin spandrels are drawn as a plain band (rough draft).', [NRHP, HAER])
    part(f'ph-c-rail-{side}', f'{PH}: pavilion railing', rect(A0, A1, bb - 0.04, bb + 0.04), PAV, PAV + 1.0, 'iron', 'written', PAV_NOTE, [NRHP, HAER])
part('ph-c-roof', f'{PH}: roof', [lonlat(A0, B0 - 0.4), lonlat(A1, B0 - 0.4), lonlat(A1, B1 + 0.4), lonlat(A0, B1 + 0.4)], EAVE, RIDGE, 'roof', 'approximate',
     'A steep slate roof with rows of imbrication and iron cresting on the ridge, on large wooden trusses (NRHP 2002). Ridge at the 2019 study\'s 46 ft; pitch approximate. '
     'Lifted off in the cutaway, so the dance floor shows.', [NRHP, STUDY], shape='gable', only='whole')

# ---- water and walks (not cut) ---------------------------------------------------------------
# Water is clipped to the cutaway's frame (regions/pump-house-cutaway.json), since modeled parts
# are not cut at the plate's edges.
REGIONS = [json.loads((ROOT / 'regions' / n).read_text()) for n in ('pump-house-cutaway.json', 'pump-house-cutaway-b55.json', 'pump-house-cutaway-across.json')]


def frame_ab(REGION):
    clon, clat = REGION['center']
    cx, cy = (clon - LON0) * KX, (clat - LAT0) * KY
    n, e = unit(REGION['bearing']), unit(REGION['bearing'] + 90)
    hw, hd = REGION['width'] / 2 - 0.5, REGION['depth'] / 2 - 0.5
    pts = [(cx + sx * hw * e[0] + sy * hd * n[0], cy + sx * hw * e[1] + sy * hd * n[1]) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return [(x * UA[0] + y * UA[1], x * UB[0] + y * UB[1]) for x, y in pts]


def clip(poly, window):
    def side(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    sgn = 1 if sum((window[i][0] * window[(i + 1) % 4][1] - window[(i + 1) % 4][0] * window[i][1]) for i in range(4)) > 0 else -1
    out = list(poly)
    for i in range(len(window)):
        a, b = window[i], window[(i + 1) % len(window)]
        inp, out = out, []
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            sp, sq = sgn * side(p, a, b), sgn * side(q, a, b)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
        if not out:
            return []
    return out


FRAMES = [frame_ab(r) for r in REGIONS]

WATER_NOTE = (' The channel\'s banks are today\'s lidar (3DEP); its 1885 level is inferred, not measured.')
FOREBAY_Q = [[(-90, 8.0), (-20, 17.5), (-20, 33.0), (-90, 22.0)], [(-20, 17.5), (0, 22.0), (0, 37.0), (-20, 33.0)],
             [(0, 22.0), (42, 22.5), (42, 34.5), (30, 36.5), (0, 37.0)]]
for k, q in enumerate(FOREBAY_Q):
    for fr in FRAMES:
        q = clip(q, fr) if len(q) >= 3 else q
    if len(q) < 3:
        continue
    part(f'site-forebay-{k}', 'Pump House Canal (the forebay)', quad(q), FOREBAY - 0.1, FOREBAY, 'water', 'written',
         'Drawn as its surface only. The forebay: the Pump House Canal, turned off above the Three Mile Locks and dammed at the east end of the house; its waterline level with the walkway round the north front (NRHP 2002).'
         + WATER_NOTE, [NRHP, SRC['lidar']])
part('site-forebay-dam', 'Pump House Canal: the dam', rect(42.0, 44.0, 20.5, 35.0), FOREBAY - 1.5, FOREBAY + 0.6, 'stone', 'approximate',
     'The forebay was dammed off at the far east side of the building (NRHP 2002). Its line and form are approximate; the 1924 hydroelectric station stands on it today.', [NRHP])
LOWER_Q = [[(-90, -13.5), (-20, -12.5), (-20, -9.5), (-90, -10.0)], [(-20, -12.5), (0, -16.0), (0, -7.5), (-20, -9.5)],
           [(0, -16.0), (20, -24.0), (20, -13.0), (0, -7.5)], [(20, -24.0), (44, -28.5), (44, -13.5), (20, -13.0)],
           [(44, -28.5), (62, -31.0), (62, -13.0), (44, -13.5)]]
for k, q in enumerate(LOWER_Q):
    for fr in FRAMES:
        q = clip(q, fr) if len(q) >= 3 else q
    if len(q) < 3:
        continue
    part(f'site-lower-{k}', 'James River and Kanawha Canal, below the locks', quad(q), TAIL - 0.1, TAIL, 'water', 'written',
         'The canal\'s lower ("Richmond") level, below the Three Mile Locks, where the tailraces ran out and the water went on to the mills downtown (NRHP 2002; Bolling 1900).'
         ' Its 1885 level here is the forebay\'s less the 20-ft fall (approximate).' + WATER_NOTE, [NRHP, SRC['bolling-1900'], SRC['lidar']])
part('site-walk-north', f'{PH}: north walkway', rect(-2.0, L + 2.0, D, 21.6), FOREBAY + 0.5, FOREBAY + 0.8, 'stone', 'written',
     'The stone walkway round the north front, at the forebay\'s waterline (NRHP 2002; HAER VA-34-1). Width approximate.', [NRHP, HAER])

history = {
    'title': 'The New Pump-House, about 1885 (rough draft)',
    'method': 'Rough draft, modeled with Claude for Chris Busse from curated parts in tools/stations/pump_house.py: outline from OpenStreetMap; levels from the 2019 schematic design study; '
              'machinery from The American Engineer (1884); rooms from the 2002 National Register nomination and HAER VA-34. Every part names its sources and how it is known.',
    'present': 2026,
    'about': 'Richmond\'s New Pump-House, 1881-83, by Col. Wilfred Emory Cutshaw: canal water turned three turbines that drove nine pumps, lifting drinking water to the Byrd Park reservoir; an open-air pavilion over the machines held dances and pleasure parties.',
    'epochs': [{'year': 1885, 'title': 'The New Pump-House at work', 'note': 'The original Ramsay machinery, two years in service; the pavilion still open.'}],
    'features': features,
    # Today's paths, roads and canal lines are not drawn in 1885: the water is modeled above.
    'rules': [
        {'where': {'tag': 'highway'}, 'eras': [], 'note': 'Today\'s paths and drives, not drawn in this rough draft.'},
        {'where': {'tag': 'waterway'}, 'eras': [], 'note': 'The canals are modeled as parts (forebay, lower level).'},
    ],
    'dates': [],
}
# Figures for scale (cutaway travelers): a few people on the dance floor, an engineer below.
print('wheel 2 plane', lonlat(GANGS[1] + 0.8, 0), lonlat(GANGS[1] + 0.8, 8));print('travelers', [lonlat(a, b) for a, b in ((13.0, 11.0), (18.5, 12.5), (21.0, 10.0), (26.5, 12.0), (19.0, 6.2))])
OUT.write_text(json.dumps(history, indent=1, ensure_ascii=False) + '\n')
print(f'{OUT.relative_to(ROOT)}: {len(features)} parts; through {lonlat(L / 2, CUT_B)}; center {lonlat(L / 2, D / 2)}')
