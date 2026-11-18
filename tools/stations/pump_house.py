#!/usr/bin/env python3
"""Model the Byrd Park Pump House (the "New Pump-House", Richmond) as it worked in about 1885,
for a cutaway: WORKING DRAFT (d1). Written with Claude for Chris Busse.

Everything is placed in one local frame, in meters, fitted to OpenStreetMap's outline of the
building (way 236152567):

  a  along the building's long axis toward the east-southeast (bearing 119.7 deg), from its
     west face (OSM node 2442157628, the southwest corner of the 1883 block);
  b  across it toward the north-northeast (bearing 29.7 deg), from its south face.

The 1883 block is about 39.4 m by 16.4 m (OSM). The 1905 annex, west of a = 0, is not drawn:
this is the building of 1885.

The backbone is The American Engineer of December 26, 1884, pp. 260-261 (HathiTrust,
mdp.39015010782855, scans 270-271; public domain): the article's text, and four engravings
made from H. A. Ramsay's drawings: an elevation of one wheel with its penstock, diffuser and the
lattice girder over it; a plan of one gang; a section through one pump with the forebay wall,
the sluice gate and its cylinder, the two mains, the air vessel, the crank, rod and crosshead;
and an elevation of one gang along its shaft. The engravings carry no scale. They are scaled
here from the dimensions in the text (a 23-ft wheel, a 36-in pump chamber, a 16-ft rod, a 5-ft
penstock), so every machine is placed relative to its shaft, and the shaft is placed in the
room by the 2019 levels: the engravings put the shaft 7 1/2 ft over the floor the A-frames
stand on, which is taken to be the 2019 study's "Level 1 lower" (86.31 ft, 26.31 m, read as
NAVD88). Where each gang stood along the room is not shown in any drawing found: the three are
spaced evenly along the central block (approximate).

Other levels are the 2019 schematic design study's (Timmons Group with 3north, from a laser
scan; text read, drawings not seen): "Level 1 upper" 28.06 m, the pavilion floor 34.77 m, the
building 46 ft high. The north walkway's height is today's lidar (31.5 m). The canals' banks and
beds are today's lidar (3DEP, in the I-195 to Rocketts cache); their 1885 water levels are
modeled: the forebay as the engraving draws it against the shaft, the tail 20 ft lower.

    python3 tools/stations/pump_house.py   # writes history/pump-house.json and the regions' cutaway blocks
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'history' / 'pump-house.json'

LON0, LAT0 = -77.4861874, 37.5365919          # OSM node 2442157628: a = 0, b = 0
KX = 111_320 * math.cos(math.radians(LAT0))
KY = 110_574
FT = 0.3048


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


def ngon(a, b, r, n=10):
    return [lonlat(a + r * math.cos(2 * math.pi * k / n), b + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def plane(a0, b0, a1, b1, thick):
    """A frame part's ring: its first edge from (a0, b0) to (a1, b1) is the plane its members
    stand in; its second edge, `thick` long, is their thickness, to the left of that edge."""
    da, db = a1 - a0, b1 - b0
    l = math.hypot(da, db)
    na, nb = -db / l * thick, da / l * thick
    return quad([(a0, b0), (a1, b1), (a1 + na, b1 + nb), (a0 + na, b0 + nb)])


def r3(m):
    return [round(v, 3) for v in m]


# ---- sources -------------------------------------------------------------------------------

SRC = {
    'ae-1884': 'https://babel.hathitrust.org/cgi/pt?id=mdp.39015010782855&seq=270',
    'ae-1884-261': 'https://babel.hathitrust.org/cgi/pt?id=mdp.39015010782855&seq=271',
    'nrhp': 'https://www.dhr.virginia.gov/VLR_to_transfer/PDFNoms/127-0193_New_Pump_House_2002_Final_Nomination.pdf',
    'haer': 'https://www.loc.gov/item/va1319/',
    'haer-1': 'https://tile.loc.gov/storage-services/service/pnp/habshaer/va/va1300/va1319/photos/162144pv.jpg',
    'haer-5': 'https://tile.loc.gov/storage-services/service/pnp/habshaer/va/va1300/va1319/photos/162148pv.jpg',
    'haer-10': 'https://tile.loc.gov/storage-services/service/pnp/habshaer/va/va1300/va1319/photos/162153pv.jpg',
    'study-2019': 'https://issuu.com/3north/docs/php_pump_house_park_schematic_desig',
    'bolling-1900': 'http://www.waterworkshistory.us/VA/Richmond/RichmondWaterWorks1900.pdf',
    'report-1909': 'https://archive.org/details/annualreportofsu1909rich',
    'friends-tour': 'https://www.friendsofpumphouse.org/pump-house-tour.html',
    'quinn-evans': 'https://www.friendsofpumphouse.org/uploads/1/1/5/3/115357711/pump_house_vision_plan.pdf',
    'artwork-1897': 'https://rvanews.com/news/pumphouse-circa-1897/124415',
    'osm': 'https://www.openstreetmap.org/way/236152567',
    'lidar': 'https://www.usgs.gov/3d-elevation-program',
}
AE, AE2, NRHP, HAER, STUDY, OSM = SRC['ae-1884'], SRC['ae-1884-261'], SRC['nrhp'], SRC['haer'], SRC['study-2019'], SRC['osm']
AE_BOTH = [AE, AE2]

# ---- levels (m above sea level) ------------------------------------------------------------
FOOT = 23.0          # foundations (approximate)
LOW = 26.31          # the machine floor the A-frames stand on: "Level 1 lower" (2019 study)
UP = 28.06           # the raised floor along the south wall: "Level 1 upper" (2019 study)
PAV = 34.77          # pavilion floor, "Level 2" (2019 study)
EAVE = 38.4          # pavilion eaves (approximate: scaled from HAER VA-34-1)
RIDGE = UP + 46 * FT # 46 ft (2019 study), read from Level 1 upper
WING_RIDGE = 43.9    # the wings' cross-gables (approximate: HAER VA-34-1)
WALK_N = 31.5        # the north walkway (today's lidar)
BED = 21.4           # canal beds: today's lidar water surface
HUB_Z = LOW + 7.5 * FT               # the shafts: 7 1/2 ft over the A-frames' floor (AE engravings) = 28.60
FOREBAY = HUB_Z + 7.7 * FT           # forebay water as the section through a pump draws it = 30.95
TAIL = FOREBAY - 20 * FT             # the 20-ft fall (AE text) = 24.85

# ---- plan (m) ------------------------------------------------------------------------------
L, D = 39.4, 16.4            # the 1883 block (OSM)
WING = 7.5                   # wing width along a (approximate, from HAER VA-34-1 and the Quinn Evans plan)
CB = (WING, L - WING, 1.2, 15.9)   # the central block: wings stand 1.2 m proud on the south, 0.5 m on the north (NRHP: more on the south)
A0, A1, B0, B1 = CB
T = 0.9                      # wall thickness above the machine room (approximate)
B_IN_S = B0 + T              # inside face of the south wall
B_IN_N = B1 - 6.1 * FT       # inside face of the forebay wall: 6 ft thick at its top (AE p. 261) = 14.04
HUB_B = B_IN_N - 16 * FT     # the shafts' line: 16 ft in from that face (AE pp. 260-261) = 9.16
R_OUT, R_IN = 23 * FT / 2, 21 * FT / 2   # the wheel, 21 ft inside and 23 ft outside (AE text)
CUT_B = 4.6                  # the main cut plane (regions/pump-house-cutaway.json)
GANG = 8.0
GANGS = [A0 + 0.4 + k * GANG for k in range(3)]   # each gang's west end (approximate)
WHEEL_AT = 2.05              # each wheel's plane, east of its gang's west end; its penstock west of it (AE p. 261)
PUMPS_AT = [1.6, 3.45, 5.3]  # the three pumps east of the wheel (AE p. 261, scaled)
CRANK = 36 * 0.0254          # crank radius: "cranks of 36 inch throw" (AE), which gives the 6-ft stroke the NRHP states
ROD = 16 * FT                # connecting rod, 16 ft (AE text)
CH_B = HUB_B + 1.4 * FT      # the crosshead's line, a little north of the shaft (AE p. 261)
GIRDER_TOP = PAV - 0.35      # the lattice girders' tops, under the pavilion floor (AE: 19 ft over the shaft)
GIRDER_D = 1.9               # their depth, about 6 1/4 ft (AE p. 260)
FLOOR_B = 11.2               # the pavilion floor's near pieces, south of this, are lifted off over the four middle bays (regions/pump-house-cutaway.json)

features = []


def part(id_, name, ring, z0, z1, tone, conf, note, sources, **more):
    f = {'id': id_, 'name': name, 'kind': 'landmark', 'from': 1883, 'to': 1899, 'ring': ring,
         'elevation': round(z0, 3), 'upTo': round(z1, 3), 'tone': tone, 'confidence': conf, 'note': note, 'sources': sources}
    f.update({k: v for k, v in more.items() if v is not None})
    features.append(f)


PH = 'The New Pump-House'
SHELL = ('Random-ashlar granite from the site and James Netherwood\'s quarries, built 1881-83 by Col. Wilfred Emory Cutshaw, city engineer '
         '(NRHP 2002). Outline from OpenStreetMap; wall thickness approximate.')
AE_NOTE = (' The American Engineer, December 26, 1884, pp. 260-261: designed by the late Prof. Charles A. Smith, built and erected by H. A. Ramsay '
           '(Ramsay Engineering Works, Baltimore) under contract with Col. W. E. Cutshaw.')
SCALED = ' Form and size scaled from the engravings, which carry no scale, by the dimensions in the text.'
PLACE = ' Where each gang stood along the room is approximate: no drawing of the room with the machines in it was found.'

# ---- the wings (kept whole: the cut does not touch them) ------------------------------------
LANCET = ('A tall lancet window, as HAER VA-34-1 and -10 show them in the wings\' gables and end walls. '
          'Count and size approximate.')
for side, (a0, a1) in (('w', (0.0, WING)), ('e', (L - WING, L))):
    name = f'{PH}: {"west" if side == "w" else "east"} wing'
    note = (SHELL + ' Each end is a cross-gabled wing with lancet windows, a steep slate roof and pinnacled gables; the upper floor held the '
            f'{"gentlemen" if side == "w" else "ladies"}\'s powder room and offices, and a stair at the south corner (NRHP 2002). '
            'The wing roof\'s height is scaled from HAER VA-34-1 (approximate).')
    for wid, rg in (('s', rect(a0, a1, 0, T)), ('n', rect(a0, a1, D - T, D)), ('end', rect(a0, a0 + T, T, D - T) if side == 'w' else rect(a1 - T, a1, T, D - T))):
        part(f'ph-w-{side}-wall-{wid}', name, rg, FOOT, EAVE, 'stone', 'written', note, [NRHP, HAER, OSM])
    inner = (a0 + T, a1) if side == 'w' else (a0, a1 - T)
    part(f'ph-w-{side}-floor1', name, rect(inner[0], inner[1], T, D - T), UP - 0.25, UP, 'floor', 'approximate', note, [NRHP, STUDY])
    part(f'ph-w-{side}-floor2', name, rect(inner[0], inner[1], T, D - T), PAV - 0.3, PAV, 'floor', 'approximate',
         'The wing\'s upper floor, level with the pavilion: powder room and offices, with lancet windows opening onto the pavilion (NRHP 2002).', [NRHP, STUDY])
    part(f'ph-w-{side}-stair', name, rect(inner[0] + 0.3, inner[0] + 1.5, T + 0.2, T + 6.0) if side == 'w' else rect(inner[1] - 1.5, inner[1] - 0.3, T + 0.2, T + 6.0),
         UP, PAV, 'wood', 'written', 'Stairs at the southern corners of the machine room, with a landing halfway up to the viewing catwalk, then on to the pavilion (NRHP 2002). Form approximate.',
         [NRHP], shape='stair', steps=20)
    part(f'ph-w-{side}-wall-in', name, rect(a1 - T, a1, T, D - T) if side == 'w' else rect(a0, a0 + T, T, D - T), PAV, EAVE, 'plaster', 'written', note, [NRHP])
    part(f'ph-w-{side}-roof', name, [lonlat(a1 + 0.3, -0.3), lonlat(a1 + 0.3, D + 0.3), lonlat(a0 - 0.3, D + 0.3), lonlat(a0 - 0.3, -0.3)],
         EAVE, WING_RIDGE, 'roof', 'approximate', note, [NRHP, HAER], shape='gable')
    for bb in (-0.3, D + 0.3):
        part(f'ph-w-{side}-pinnacle-{0 if bb < 0 else 1}', name, rect((a0 + a1) / 2 - 0.3, (a0 + a1) / 2 + 0.3, bb - 0.3, bb + 0.3),
             WING_RIDGE - 0.6, WING_RIDGE + 0.9, 'stone', 'approximate', 'A flat-topped pinnacle crowning the gable (NRHP 2002). Size approximate.', [NRHP, HAER])
    # Lancet windows: two in each gable (south and north), five in the end wall (HAER VA-34-1).
    mid = (a0 + a1) / 2
    k = 0
    for c in (mid - 1.0, mid + 1.0):
        part(f'ph-w-{side}-lancet-{k}', name, plane(c + 0.38, -0.02, c - 0.38, -0.02, 0.06), 33.6, 37.7, 'glass', 'approximate', LANCET, [SRC['haer-1'], SRC['haer-10']], shape='arch')
        k += 1
        part(f'ph-w-{side}-lancet-{k}', name, plane(c - 0.38, D + 0.02, c + 0.38, D + 0.02, 0.06), 33.6, 37.7, 'glass', 'approximate', LANCET, [SRC['haer-1']], shape='arch')
        k += 1
    for c in (2.4, 5.2, 8.2, 11.2, 14.0):
        if side == 'w':
            rg = plane(-0.02, c - 0.38, -0.02, c + 0.38, 0.06)
        else:
            rg = plane(L + 0.02, c + 0.38, L + 0.02, c - 0.38, 0.06)
        part(f'ph-w-{side}-lancet-{k}', name, rg, 33.6, 37.7, 'glass', 'approximate', LANCET, [SRC['haer-1']], shape='arch')
        k += 1

# ---- the central block: walls -----------------------------------------------------------------
WALL_NOTE = SHELL + ' The north wall stands in the forebay\'s water to the walkway, so the machine room is below water on that side (NRHP 2002).'
TUN_HALF = 1.3     # half the tailrace tunnel's outside width (approximate)
WHEELS = [g + WHEEL_AT for g in GANGS]
# The south wall: below the tailraces' crowns in lengths between them, above in one.
xs = [A0] + [v for wa in WHEELS for v in (wa - TUN_HALF, wa + TUN_HALF)] + [A1]
for k in range(0, len(xs), 2):
    part(f'ph-c-wall-south-foot-{k // 2}', f'{PH}: south wall', rect(xs[k], xs[k + 1], B0, B_IN_S), FOOT, 26.27, 'stone', 'written', WALL_NOTE, [NRHP, HAER, OSM])
part('ph-c-wall-south', f'{PH}: south wall', rect(A0, A1, B0, B_IN_S), 26.27, PAV - 0.3, 'stone', 'written',
     WALL_NOTE + ' Five bays of double lancet windows lit the machine room from the south (NRHP 2002; HAER VA-34-10); in this cut only the wall\'s foot is left.', [NRHP, SRC['haer-10'], OSM])

# The forebay wall: battered on the water side, 6 ft thick at its top (AE p. 261), with an
# opening for each penstock and its gate. A frame across the wall, as long as each length.
FB_NOTE = ('The wall between the forebay and the machine room: battered on the water side and about 6 ft thick at its top, with an opening for each penstock '
           'closed by its sluice gate, as the section through a pump draws it (The American Engineer, 1884, p. 261). '
           'Thickness at its foot and the batter approximate.' + ' ' + WALL_NOTE)
BATTER = (17.0 - B1) / (WALK_N - FOOT)


def fb_profile(zlo, zhi):
    u = lambda z: (B1 - B_IN_N) + (WALK_N - z) * BATTER
    return r3([0, 0, u(zlo), 0, u(zhi), zhi - zlo, 0, zhi - zlo])


OPEN = (28.9, 31.0)  # the penstock opening's sill and head (AE p. 261, scaled)
edges = [A0]
for g in GANGS:
    edges += [g - 0.2, g + 1.7]
edges.append(A1)
for k in range(0, len(edges), 2):
    a0, a1 = edges[k], edges[k + 1]
    part(f'ph-c-wall-fore-{k // 2}', f'{PH}: forebay wall', plane(a1, B_IN_N, a1, 17.0, a1 - a0), FOOT, WALK_N, 'stone', 'drawn', FB_NOTE, [AE2, NRHP, HAER],
         shape='frame', members=[fb_profile(FOOT, WALK_N)])
for k, g in enumerate(GANGS):
    a0, a1 = g - 0.2, g + 1.7
    part(f'ph-c-wall-fore-sill-{k}', f'{PH}: forebay wall', plane(a1, B_IN_N, a1, 17.0, a1 - a0), FOOT, OPEN[0], 'stone', 'drawn', FB_NOTE, [AE2, NRHP],
         shape='frame', members=[fb_profile(FOOT, OPEN[0])])
    part(f'ph-c-wall-fore-head-{k}', f'{PH}: forebay wall', plane(a1, B_IN_N, a1, 17.0, a1 - a0), OPEN[1], WALK_N, 'stone', 'drawn', FB_NOTE, [AE2, NRHP],
         shape='frame', members=[[0, 0, fb_profile(OPEN[1], WALK_N)[2] - 0.0, 0, fb_profile(OPEN[1], WALK_N)[4], WALK_N - OPEN[1], 0, WALK_N - OPEN[1]]])
part('ph-c-wall-north', f'{PH}: north wall', rect(A0, A1, B1 - T, B1), WALK_N, PAV - 0.3, 'stone', 'written', WALL_NOTE, [NRHP, HAER, OSM])

# ---- floors and pits ------------------------------------------------------------------------
FLOOR_NOTE = ('The machine room floor: wood in its day, "long removed"; granite and earth today (NRHP 2002). Its two levels are the 2019 study\'s '
              '"Level 1 lower" and "Level 1 upper"; the A-frames stand on the lower, 7 1/2 ft under the shafts (The American Engineer, 1884). '
              'Where the one steps up to the other is approximate.')
STEP_B = HUB_B - R_OUT - 0.45   # the step up toward the south wall, just clear of the wheels (AE p. 260 puts it about 11 ft south of the shafts)
part('ph-c-floor-up', f'{PH}: machine room floor', rect(A0, A1, B_IN_S, STEP_B), UP - 0.25, UP, 'floor', 'written', FLOOR_NOTE, [NRHP, STUDY, AE])
PIT_NOTE = ('A pit for a pump, sunk about 15 ft under the shaft, as the section through a pump draws it (The American Engineer, 1884, p. 261); '
            'the pits survive and hold water today (NRHP 2002). Outline approximate.')
WPIT_NOTE = ('The wheel\'s pit, down past the tail water, where the cast-iron diffuser under the wheel let the spent water go to the tailrace '
             '(The American Engineer, 1884, pp. 260-261). Width and depth scaled from the engravings; outline approximate.')
PPIT = 24.0          # the pump pits' floor, 15 ft under the shaft (AE p. 261)
WPIT = 22.75         # the wheel pits' floor (approximate)
PP_B = (HUB_B - 0.55, HUB_B + 1.95)
WP_B = (STEP_B, HUB_B + R_OUT + 0.3)
# The lower floor, in lengths round the pits.
cuts = []
for wa in WHEELS:
    cuts.append((wa - 1.0, wa + 1.0, WP_B))
    for p in PUMPS_AT:
        cuts.append((wa + p - 0.7, wa + p + 0.7, PP_B))
cuts.sort()
k = 0
prev = A0
for (c0, c1, (pb0, pb1)) in cuts:
    if c0 > prev + 0.01:
        part(f'ph-c-floor-{k}', f'{PH}: machine room floor', rect(prev, c0, STEP_B, B_IN_N), LOW - 0.25, LOW, 'floor', 'written', FLOOR_NOTE, [NRHP, STUDY, AE]); k += 1
    if pb0 > STEP_B + 0.01:
        part(f'ph-c-floor-{k}', f'{PH}: machine room floor', rect(c0, c1, STEP_B, pb0), LOW - 0.25, LOW, 'floor', 'written', FLOOR_NOTE, [NRHP, STUDY, AE]); k += 1
    part(f'ph-c-floor-{k}', f'{PH}: machine room floor', rect(c0, c1, pb1, B_IN_N), LOW - 0.25, LOW, 'floor', 'written', FLOOR_NOTE, [NRHP, STUDY, AE]); k += 1
    prev = c1
if A1 > prev + 0.01:
    part(f'ph-c-floor-{k}', f'{PH}: machine room floor', rect(prev, A1, STEP_B, B_IN_N), LOW - 0.25, LOW, 'floor', 'written', FLOOR_NOTE, [NRHP, STUDY, AE])
part('ph-c-step', f'{PH}: machine room floor', rect(A0, A1, STEP_B - 0.25, STEP_B), LOW, UP, 'stone', 'approximate', FLOOR_NOTE, [STUDY, AE])

for k, (c0, c1, (pb0, pb1)) in enumerate(cuts):
    wheel = (pb0, pb1) == WP_B
    bot = WPIT if wheel else PPIT
    nm, nt = (f'{PH}: wheel pit', WPIT_NOTE) if wheel else (f'{PH}: pump pit', PIT_NOTE)
    part(f'ph-c-pit-{k}-floor', nm, rect(c0, c1, pb0, pb1), bot - 0.3, bot, 'stone', 'approximate', nt, [AE2, NRHP])
    walls = [('w', rect(c0 - 0.25, c0, pb0, pb1)), ('e', rect(c1, c1 + 0.25, pb0, pb1)), ('n', rect(c0, c1, pb1, pb1 + 0.25))]
    if not wheel:
        walls.append(('s', rect(c0, c1, pb0 - 0.25, pb0)))
    for s, rg in walls:
        part(f'ph-c-pit-{k}-{s}', nm, rg, bot - 0.3, LOW - 0.25, 'stone', 'approximate', nt, [AE2, NRHP])

# ---- the three gangs ---------------------------------------------------------------------------
WHEEL_NOTE = ('A partial vertical turbine of the outward-flow (Fourneyron) type, all iron, 21 ft inside and 23 ft outside; water under a 20-ft head came in '
              'through its center to a guide chamber that turned it onto about a quarter of the buckets.' + AE_NOTE +
              ' Bolling (1900) gives 23 1/2 ft. Replaced in 1891 by geared Leffel wheels (NRHP 2002; Bolling 1900).' + SCALED + PLACE)
for k, g in enumerate(GANGS):
    wa = g + WHEEL_AT
    pumps = [wa + p for p in PUMPS_AT]
    nm = f'{PH}: turbine wheel {k + 1}'
    # The wheel: its rim (the buckets) a ring of plates 3 1/2 ft wide; ten spokes; the guide chamber at its center.
    rim = []
    n = 28
    for i in range(n):
        t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        P = lambda r, t: (R_OUT + r * math.cos(t), R_OUT + r * math.sin(t))
        q = [P(R_OUT, t0), P(R_OUT, t1), P(R_IN, t1), P(R_IN, t0)]
        rim.append(r3([v for pt in q for v in pt]))
    part(f'ph-c-wheel-{k}-rim', nm, plane(wa + 0.53, HUB_B - R_OUT, wa + 0.53, HUB_B + R_OUT, 1.06), HUB_Z - R_OUT, HUB_Z + R_OUT, 'iron', 'drawn', WHEEL_NOTE,
         AE_BOTH + [SRC['bolling-1900'], NRHP], shape='frame', members=rim)
    spokes = []
    for i in range(10):
        t = 2 * math.pi * (i + 0.25) / 10
        spokes.append(r3([R_OUT + 0.55 * math.cos(t), R_OUT + 0.55 * math.sin(t), R_OUT + (R_IN + 0.05) * math.cos(t), R_OUT + (R_IN + 0.05) * math.sin(t), 0.2]))
    part(f'ph-c-wheel-{k}-spokes', nm, plane(wa + 0.12, HUB_B - R_OUT, wa + 0.12, HUB_B + R_OUT, 0.24), HUB_Z - R_OUT, HUB_Z + R_OUT, 'iron', 'drawn', WHEEL_NOTE,
         AE_BOTH, shape='frame', members=spokes)
    hub = []
    for i in range(12):
        t = 2 * math.pi * i / 12
        hub += [0.7 + 0.7 * math.cos(t), 0.7 + 0.7 * math.sin(t)]
    part(f'ph-c-wheel-{k}-guide', f'{PH}: guide chamber', plane(wa + 0.5, HUB_B - 0.7, wa + 0.5, HUB_B + 0.7, 1.0), HUB_Z - 0.7, HUB_Z + 0.7, 'iron', 'drawn',
         'The guide chamber at the wheel\'s center, which turned the water from the penstock onto the buckets nearly in line with their path (The American Engineer, 1884).' + SCALED,
         AE_BOTH, shape='frame', members=[r3(hub)])
    # The diffuser under the wheel, down into the tail water.
    part(f'ph-c-diffuser-{k}', f'{PH}: diffuser', rect(wa - 0.55, wa + 0.55, HUB_B - 1.85, HUB_B + 1.85), HUB_Z - 17.3 * FT, HUB_Z - R_OUT + 0.25, 'iron', 'drawn',
         'A large cast-iron diffuser below the wheel "delivers the water into the tail-race with the least possible loss" (The American Engineer, 1884). '
         '12 ft across and reaching 17 ft under the shaft in the engraving; its flare is drawn square.' + SCALED, AE_BOTH)
    part(f'ph-c-tailpit-{k}', f'{PH}: tail water', rect(wa - 0.98, wa + 0.98, WP_B[0], WP_B[1] - 0.02), WPIT, TAIL, 'water', 'approximate',
         'Tail water in the wheel pit, 20 ft below the forebay (The American Engineer, 1884). Level inferred.', [AE])
    # The penstock: from its opening in the forebay wall, falling at about 29 deg (AE p. 260), to an elbow that turns it into the wheel's center from the west (AE p. 261).
    pa0 = g
    PEN_NOTE = ('An iron penstock 5 ft in diameter, from its sluice gate in the forebay wall down at a slant to an elbow that turns it into the wheel\'s center '
                '(The American Engineer, 1884, pp. 260-261); three openings in the north wall (NRHP 2002; HAER VA-34-5). Drawn square in section.' + SCALED + PLACE)
    z0 = HUB_Z - 1.6
    u_in = B_IN_N - HUB_B
    part(f'ph-c-penstock-{k}', f'{PH}: penstock {k + 1}', plane(pa0 + 1.52, HUB_B, pa0 + 1.52, B1 + 0.2, 1.52), z0, HUB_Z + 2.4, 'iron', 'drawn', PEN_NOTE,
         AE_BOTH + [NRHP, SRC['haer-5']], shape='frame',
         members=[r3([0.3, 0.6, u_in, 3.1, 1.52]), r3([u_in - 0.2, 3.1, B1 + 0.2 - HUB_B, 3.1, 1.52])])
    elbow = []
    for i in range(12):
        t = 2 * math.pi * i / 12
        elbow += [0.76 + 0.76 * math.cos(t), 0.76 + 0.76 * math.sin(t)]
    part(f'ph-c-penstock-elbow-{k}', f'{PH}: penstock {k + 1}', plane(wa - 0.5, HUB_B - 0.6, wa - 0.5, HUB_B + 0.92, wa - 0.5 - pa0 - 0.4), HUB_Z - 1.3, HUB_Z + 0.22, 'iron', 'drawn',
         'The penstock\'s elbow, turning into the wheel\'s center from the side away from the pumps (The American Engineer, 1884, p. 261). Drawn as a short length of pipe.', AE_BOTH,
         shape='frame', members=[r3(elbow)])
    part(f'ph-x-gate-{k}', f'{PH}: sluice gate {k + 1}', rect(pa0 - 0.15, pa0 + 1.65, 15.35, 15.65), OPEN[0], OPEN[1] + 0.2, 'wood', 'drawn',
         'A sluice gate 6 ft by 6 ft at the penstock\'s head, in its opening in the forebay wall, worked by a hydraulic cylinder 10 in in diameter on the wall\'s top '
         '(The American Engineer, 1884, pp. 260-261).' + SCALED, AE_BOTH)
    part(f'ph-x-gate-cyl-{k}', f'{PH}: sluice gate {k + 1}', ngon(pa0 + 0.75, 15.5, 0.17), WALK_N, WALK_N + 2.1, 'iron', 'drawn',
         'The gate\'s hydraulic cylinder, 10 in (The American Engineer, 1884), standing about 7 ft over the wall\'s top in the engraving (p. 261).', AE_BOTH)
    # Shaft, A-frames, cranks, rods, crossheads, pumps.
    part(f'ph-c-shaft-{k}', f'{PH}: shaft {k + 1}', rect(wa - 0.6, pumps[-1] + 0.5, HUB_B - 0.155, HUB_B + 0.155), HUB_Z - 0.155, HUB_Z + 0.155, 'iron', 'drawn',
         'A wrought-iron shaft 12 in in diameter, keyed to the wheel, with three cranks of 36-in throw set 120 deg apart (The American Engineer, 1884).' + PLACE, AE_BOTH)
    hz = HUB_Z - LOW
    for j, fa in enumerate((wa + 0.82, (pumps[0] + pumps[1]) / 2, (pumps[1] + pumps[2]) / 2)):
        part(f'ph-c-aframe-{k}-{j}', f'{PH}: A-frame', plane(fa + 0.14, HUB_B - 1.6, fa + 0.14, HUB_B + 1.4, 0.28), LOW, HUB_Z + 0.4, 'iron', 'drawn',
             'An A-frame standard carrying the shaft\'s bearing between the pumps (The American Engineer, 1884, pp. 260-261).' + SCALED,
             AE_BOTH, shape='frame', members=[r3([0.1, 0, 1.6, hz, 0.28]), r3([2.9, 0, 1.6, hz, 0.28]), r3([0.65, 1.0, 2.4, 1.0, 0.16]),
                                              r3([1.25, hz - 0.3, 1.95, hz - 0.3, 1.95, hz + 0.4, 1.25, hz + 0.4])])
    for j, pa_ in enumerate(pumps):
        tag = f'{k}-{j}'
        ang = math.radians(90 + 120 * j)
        pin_b, pin_z = HUB_B + CRANK * math.cos(ang), HUB_Z + CRANK * math.sin(ang)
        part(f'ph-c-crank-{tag}', f'{PH}: crank', plane(pa_ + 0.1, HUB_B - 0.8, pa_ + 0.1, HUB_B + 0.8, 0.2), HUB_Z - 0.8, HUB_Z + 0.8, 'iron', 'drawn',
             'A crank of 36-in throw; the three on a shaft are set 120 deg apart (The American Engineer, 1884). Drawn at the angles of one moment.', AE_BOTH,
             shape='frame', members=[r3([0.8, 0.8, pin_b - HUB_B + 0.8, pin_z - HUB_Z + 0.8, 0.32])])
        ch = pin_z + math.sqrt(ROD ** 2 - (CH_B - pin_b) ** 2)
        ch = min(ch, GIRDER_TOP - 0.2)
        part(f'ph-c-rod-{tag}', f'{PH}: connecting rod', plane(pa_ + 0.05, HUB_B - 0.6, pa_ + 0.05, HUB_B + 0.8, 0.1), pin_z, ch, 'iron', 'drawn',
             'A connecting rod 16 ft long, 4 by 9 in, from the crank up to the crosshead overhead (The American Engineer, 1884).', AE_BOTH,
             shape='frame', members=[r3([pin_b - HUB_B + 0.6, 0, CH_B - HUB_B + 0.6, ch - pin_z, 0.23])])
        part(f'ph-c-crosshead-{tag}', f'{PH}: crosshead', rect(pa_ - 0.55, pa_ + 0.55, CH_B - 0.2, CH_B + 0.2), ch - 0.15, ch + 0.2, 'iron', 'drawn',
             'A crosshead working in fixed guides held by the lattice girders (The American Engineer, 1884).', AE_BOTH)
        for s, da in (('w', -0.45), ('e', 0.45)):
            part(f'ph-c-pumprod-{tag}-{s}', f'{PH}: pump rod', rect(pa_ + da - 0.05, pa_ + da + 0.05, CH_B - 0.05, CH_B + 0.05), 28.55, ch - 0.15, 'iron', 'drawn',
                 'Two pump rods to each pump, from the crosshead down past the shaft to the plunger (The American Engineer, 1884, p. 261).', AE_BOTH)
        part(f'ph-c-plunger-{tag}', f'{PH}: plunger', rect(pa_ - 0.55, pa_ + 0.55, CH_B - 0.15, CH_B + 0.15), 28.45, 28.6, 'iron', 'drawn',
             'The yoke where the two pump rods take the plunger (The American Engineer, 1884, p. 261).', AE_BOTH)
        part(f'ph-c-pump-{tag}', f'{PH}: pump {3 * k + j + 1}', ngon(pa_, HUB_B + 0.37, 0.46), PPIT, 28.45, 'iron', 'drawn',
             'One of nine vertical single-acting plunger pumps: a plunger 14 in in diameter in a chamber 36 in across, with double-beat Cornish valves of 20 in '
             '(The American Engineer, 1884); stroke 6 ft (NRHP 2002). Twelve million gallons a day for the nine against a head of 175 ft (The American Engineer).'
             + SCALED + PLACE, AE_BOTH + [NRHP])
        part(f'ph-c-airvessel-{tag}', f'{PH}: air vessel', ngon(pa_, HUB_B + 1.45, 0.3), 25.0, 29.55, 'iron', 'drawn',
             'An air vessel over each pump\'s discharge (The American Engineer, 1884).' + SCALED, AE_BOTH)
        part(f'ph-c-airvessel-top-{tag}', f'{PH}: air vessel', ngon(pa_, HUB_B + 1.45, 0.3), 29.55, 29.85, 'iron', 'drawn',
             'An air vessel over each pump\'s discharge (The American Engineer, 1884).', AE_BOTH, shape='dome')
        part(f'ph-c-branch-out-{tag}', f'{PH}: discharge branch', rect(pa_ - 0.25, pa_ + 0.25, HUB_B + 0.6, 12.4), 24.95, 25.45, 'iron', 'drawn',
             'From the pump\'s discharge valve to the common main (The American Engineer, 1884, p. 261).' + SCALED, AE_BOTH)
        part(f'ph-c-branch-in-{tag}', f'{PH}: suction branch', rect(pa_ - 0.22, pa_ + 0.22, HUB_B + 1.75, 13.2), 27.35, 27.8, 'iron', 'drawn',
             'From the common suction to the pump\'s suction valve (The American Engineer, 1884, p. 261).' + SCALED, AE_BOTH)
    # Lattice girders across the room over the gang, carrying the crosshead guides (AE pp. 260-261).
    # In short lengths, one lattice panel each, so each sorts with what stands near it.
    cutsb = [B_IN_S + i * (B_IN_N - B_IN_S) / 6 for i in range(7)]
    for j, ga in enumerate((wa + 0.8, (pumps[0] + pumps[1]) / 2, (pumps[1] + pumps[2]) / 2, pumps[2] + 0.62)):
        for h, (gb0, gb1) in enumerate(zip(cutsb, cutsb[1:])):
            span = gb1 - gb0
            mem = [r3([0, GIRDER_D - 0.12, span, GIRDER_D - 0.12, 0.24]), r3([0, 0.12, span, 0.12, 0.24])]
            step = 1.9
            u = -((gb0 - B_IN_S) % (step / 2))
            while u < span:
                for (x0, z0, x1, z1) in ((u, 0.12, u + step, GIRDER_D - 0.12), (u, GIRDER_D - 0.12, u + step, 0.12)):
                    # Clip the diagonal to this length.
                    t0, t1 = max(0.0, (0 - x0) / (x1 - x0)), min(1.0, (span - x0) / (x1 - x0))
                    if t1 > t0:
                        mem.append(r3([x0 + (x1 - x0) * t0, z0 + (z1 - z0) * t0, x0 + (x1 - x0) * t1, z0 + (z1 - z0) * t1, 0.07]))
                u += step / 2
            if h == 0:
                mem.append(r3([0.05, 0, 0.05, GIRDER_D, 0.12]))
            if h == len(cutsb) - 2:
                mem.append(r3([span - 0.05, 0, span - 0.05, GIRDER_D, 0.12]))
            part(f'ph-c-girder-{k}-{j}-{h}', f'{PH}: lattice girder', plane(ga + 0.13, gb0, ga + 0.13, gb1, 0.26), GIRDER_TOP - GIRDER_D, GIRDER_TOP, 'iron', 'drawn',
                 'Lattice girders across the room over the pumps, holding the crosshead guides (The American Engineer, 1884, pp. 260-261); about 6 ft deep in the engravings. '
                 'Metal trusses under the pavilion floor are seen in HAER VA-34-5.', AE_BOTH + [SRC['haer-5']], shape='frame', members=mem)

# The common suction and discharge mains, along the forebay wall (AE p. 261).
part('ph-c-main', f'{PH}: discharge main', rect(GANGS[0], A1 - 0.3, 12.02, 12.78), 24.82, 25.58, 'iron', 'drawn',
     'The nine pumps discharge "through a common discharge pipe, 30 inches in diameter" (The American Engineer, 1884), which runs along the room in a trench '
     'by the forebay wall (p. 261).' + SCALED, AE_BOTH)
part('ph-c-suction', f'{PH}: suction', rect(A0 + 0.3, A1 - 0.3, 12.74, 13.65), 27.15, 28.06, 'iron', 'drawn',
     'The nine pumps drew "from one common suction pipe, 36 inches in diameter" (The American Engineer, 1884), from the forebay (1909 annual report: about 16 ft '
     'of head on it). It runs along the forebay wall (p. 261). A rising-stem valve in the northwest corner survives (NRHP 2002).', AE_BOTH + [NRHP, SRC['report-1909']])
MID = (A0 + A1) / 2
part('ph-x-main-out', f'{PH}: main to the reservoir', rect(MID - 0.38, MID + 0.38, 12.4, 22.0), 24.82, 25.58, 'iron', 'written',
     'The 30-in main leaves the house northward, under the forebay, for the Byrd Park reservoir 3,600 ft away and 175 ft up (The American Engineer, 1884; NRHP 2002 sketch map, '
     '"pipe to Byrd Park reservoir"). Bolling (1900) gives a lift of 165 ft. Where it leaves the room is approximate.', [AE, NRHP, SRC['bolling-1900']])
for k, b0 in enumerate(range(36, 90, 6)):
    f = {'id': f'ph-x-main-hill-{k}', 'name': f'{PH}: main to the reservoir', 'kind': 'landmark', 'from': 1883, 'to': 1899,
         'ring': rect(MID - 0.38, MID + 0.38, b0, b0 + 6), 'height': 0.76, 'tone': 'iron', 'confidence': 'approximate',
         'note': 'The 30-in main up the hill toward the reservoir, drawn on the ground; it ran buried (NRHP 2002 sketch map: a dashed pipe). Line approximate.',
         'sources': [AE, NRHP]}
    features.append(f)

# Catwalks and stair.
for k, g in enumerate(GANGS):
    wa = g + WHEEL_AT
    part(f'ph-c-catwalk-grease-{k}', f'{PH}: greasing catwalk', rect(wa + 0.9, wa + PUMPS_AT[-1] + 0.6, CH_B + 0.9, CH_B + 1.6), GIRDER_TOP - GIRDER_D - 0.2, GIRDER_TOP - GIRDER_D - 0.05,
         'iron', 'written', 'A catwalk "originally used to service and grease the joints", reached by a cast-iron spiral stair at the east end (NRHP 2002; HAER VA-34-6). '
         'Height and line approximate.', [NRHP, HAER])
part('ph-c-spiral', f'{PH}: spiral stair', ngon(A1 - 0.7, B_IN_N - 1.0, 0.7), LOW, GIRDER_TOP - GIRDER_D - 0.05, 'iron', 'written',
     'An "ornate cast-iron spiral staircase at the east end" up to the greasing catwalk (NRHP 2002; HAER VA-34-6). The Friends\' tour puts it in the northwest corner.', [NRHP, HAER, SRC['friends-tour']])
part('ph-c-catwalk-view', f'{PH}: viewing catwalk', rect(A0, A1, B_IN_S, B_IN_S + 1.1), UP + 4 * FT + 1.2 - 0.15, UP + 4 * FT + 1.2, 'wood', 'written',
     'A catwalk hung on the south wall, reached from landings on the stairs at the south corners, where workers and pavilion visitors watched the machinery (NRHP 2002; Friends of Pump House). '
     'Height approximate (the 2019 study\'s mezzanine landing is 4 ft 2 in over Level 1 upper).', [NRHP, SRC['friends-tour'], STUDY])

# ---- the pavilion: floor, arcades ------------------------------------------------------------
PAV_NOTE = ('The open-air pavilion over the machine room, 3,392 sq ft (Quinn Evans plan): a painted pine floor, a Gothic arcade of six Tudor arches each side on seven cast-iron columns, '
            'the two end arches narrower, with railings of zinc-coated tin; a flat ceiling on wooden trusses. Enclosed with glass in 1899 because rain came through the floor onto the machinery (NRHP 2002).')
COLS = [0.0, 3.2, 7.7, 12.2, 16.7, 21.2, 24.4]   # terminal arches 3.2 m, central ones 4.5 m (approximate)
for k in range(len(COLS) - 1):   # the floor in bays between the columns, so each sorts among the machines under it
    # The far pieces reach a little under the lifted ones, so what stands below their edge sorts under them.
    for s, (b0, b1) in (('s', (B0, FLOOR_B)), ('n', (FLOOR_B - 0.3, B1))):
        part(f'ph-c-pav-floor-{s}-{k}', f'{PH}: pavilion floor', rect(A0 + COLS[k], A0 + COLS[k + 1], b0, b1), PAV - 0.3, PAV, 'floor', 'written',
             PAV_NOTE + ' Level from the 2019 study.', [NRHP, STUDY, SRC['quinn-evans']])
SPRING, APEX = 2.5, 3.05      # the arches' springing and point over the floor (approximate: HAER VA-34-1)
HEAD = EAVE - PAV


def tudor(span):
    """A four-centered arch over `span`: (u, z) from one springing to the point and down."""
    hs = span / 2
    rx, rz = 0.32 * hs, 0.62 * (APEX - SPRING)
    half = []
    for i in range(7):
        t = math.radians(80 * i / 6)
        half.append((rx * (1 - math.cos(t)), SPRING + rz * math.sin(t)))
    u1, z1 = half[-1]
    for i in range(1, 5):
        f = i / 4
        half.append((u1 + (hs - u1) * f, z1 + (APEX - z1) * f))
    return half + [(span - u, z) for u, z in reversed(half[:-1])]


for side, bb in (('s', B0 + 0.05), ('n', B1 - 0.35)):
    for j, c in enumerate(COLS):
        aa = A0 + c + (0.2 if j == 0 else -0.2 if j == 6 else 0)
        part(f'ph-c-col-{side}{j}', f'{PH}: pavilion arcade', ngon(aa, bb + 0.15, 0.13, 8), PAV, PAV + SPRING, 'iron', 'written', PAV_NOTE, [NRHP, HAER, SRC['artwork-1897']])
    for j in range(len(COLS) - 1):
        c0 = A0 + COLS[j] + (0.2 if j == 0 else 0)
        c1 = A0 + COLS[j + 1] - (0.2 if j + 1 == 6 else 0)
        arc = tudor(c1 - c0)
        mem = []
        for (u0, z0), (u1, z1) in zip(arc, arc[1:]):
            mem.append(r3([u0, z0, u1, z1, u1, HEAD, u0, HEAD]))
        part(f'ph-c-arch-{side}{j}', f'{PH}: pavilion arcade', plane(c0, bb, c1, bb, 0.3), PAV, EAVE, 'plaster', 'written',
             PAV_NOTE + ' The arches\' form is drawn from HAER VA-34-1 and -10; their height approximate.', [NRHP, SRC['haer-1'], SRC['haer-10']], shape='frame', members=mem)
        part(f'ph-c-rail-{side}{j}', f'{PH}: pavilion railing', plane(c0, bb + 0.1, c1, bb + 0.1, 0.08), PAV, PAV + 1.0, 'iron', 'written', PAV_NOTE, [NRHP, HAER],
             shape='frame', members=[r3([0, 0.95, c1 - c0, 0.95, 0.1]), r3([0, 0.1, c1 - c0, 0.1, 0.08])] +
             [r3([u, 0.1, u, 0.95, 0.04]) for u in [x * 0.3 for x in range(1, int((c1 - c0) / 0.3))]])
part('ph-c-roof', f'{PH}: roof', [lonlat(A0, B0 - 0.4), lonlat(A1, B0 - 0.4), lonlat(A1, B1 + 0.4), lonlat(A0, B1 + 0.4)], EAVE, RIDGE, 'roof', 'approximate',
     'A steep slate roof with rows of imbrication and iron cresting on the ridge, on large wooden trusses (NRHP 2002). Ridge at the 2019 study\'s 46 ft; pitch approximate. '
     'Lifted off in the cutaway, so the dance floor shows.', [NRHP, STUDY], shape='gable', only='whole')

# ---- water, walls and walks (not cut) ----------------------------------------------------------
REGIONS = [json.loads((ROOT / 'regions' / n).read_text()) for n in ('pump-house-cutaway.json', 'pump-house-cutaway-across.json')]


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


# Clipped to the main view's frame only: the cross cut is used for its flat section alone.
FRAMES = [frame_ab(REGIONS[0])]


def clipped(q):
    for fr in FRAMES:
        q = clip(q, fr) if len(q) >= 3 else q
    return q


WATER_NOTE = (' The channel\'s banks and bed are today\'s lidar (3DEP); its 1885 level is inferred, not measured.')
WALK_W = 17.4
FB_S = 17.0           # the forebay's water reaches under the walkway to the wall's foot
TERRACE = 26.45      # the south walkway, over the tailraces' crowns (approximate)
FOREBAY_Q = [[(-90, 8.0), (-20, 17.5), (-20, 33.0), (-90, 22.0)], [(-20, 17.5), (0, FB_S), (0, 38.5), (-20, 33.0)],
             [(0, FB_S), (42, FB_S), (42, 35.5), (30, 38.0), (0, 38.5)]]
for k, q in enumerate(x for x in (clipped(qq) for qq in FOREBAY_Q) if len(x) >= 3):
    part(f'ph-s-forebay-{k}', 'Pump House Canal (the forebay)', quad(q), BED, FOREBAY, 'water', 'written',
         'The forebay: the Pump House Canal, turned off above the Three Mile Locks and dammed at the east end of the house; its waterline level with the walkway round the north front (NRHP 2002). '
         'Its level here is where the section through a pump draws it against the shaft (The American Engineer, 1884, p. 261).' + WATER_NOTE, [NRHP, AE2, SRC['lidar']])
part('ph-s-forebay-dam', 'Pump House Canal: the dam', rect(42.0, 44.0, WALK_W, 35.0), BED, FOREBAY + 0.6, 'stone', 'approximate',
     'The forebay was dammed off at the far east side of the building (NRHP 2002). Its line and form are approximate; the 1924 hydroelectric station stands on it today.', [NRHP])
LOWER_EDGE = [(-90, -10.0), (-20, -9.5), (0, -7.5), (20, -13.0), (44, -13.5), (62, -13.0)]
LOWER_Q = [[(-90, -13.5), (-20, -12.5), (-20, -9.5), (-90, -10.0)], [(-20, -12.5), (0, -16.0), (0, -7.5), (-20, -9.5)],
           [(0, -16.0), (20, -24.0), (20, -13.0), (0, -7.5)], [(20, -24.0), (44, -28.5), (44, -13.5), (20, -13.0)],
           [(44, -28.5), (62, -31.0), (62, -13.0), (44, -13.5)]]
for k, q in enumerate(x for x in (clipped(qq) for qq in LOWER_Q) if len(x) >= 3):
    part(f'ph-s-lower-{k}', 'James River and Kanawha Canal, below the locks', quad(q), BED, TAIL, 'water', 'written',
         'The canal\'s lower ("Richmond") level, below the Three Mile Locks, where the tailraces ran out and the water went on to the mills downtown (NRHP 2002; Bolling 1900).'
         ' Its 1885 level here is the forebay\'s less the 20-ft fall (approximate).' + WATER_NOTE, [NRHP, SRC['bolling-1900'], SRC['lidar']])


def edge_b(a):
    for (a0, b0), (a1, b1) in zip(LOWER_EDGE, LOWER_EDGE[1:]):
        if a0 <= a <= a1:
            return b0 + (b1 - b0) * (a - a0) / (a1 - a0)
    return LOWER_EDGE[-1][1]


# The canal's north wall, in lengths along its edge, broken where each tailrace comes out.
CW_NOTE = ('The lower canal\'s retaining wall on the pump house side, with the tailraces\' mouths in it. Its line follows today\'s bank (lidar); its form and height are approximate.')
gaps = [(wa - TUN_HALF, wa + TUN_HALF) for wa in WHEELS]
k = 0
for (a0, b0), (a1, b1) in zip(LOWER_EDGE, LOWER_EDGE[1:]):
    pieces = [(a0, a1)]
    for g0, g1 in gaps:
        nxt = []
        for p0, p1 in pieces:
            if g1 <= p0 or g0 >= p1:
                nxt.append((p0, p1))
            else:
                if g0 > p0:
                    nxt.append((p0, g0))
                if g1 < p1:
                    nxt.append((g1, p1))
        pieces = nxt
    for p0, p1 in pieces:
        q = clipped([(p0, edge_b(p0)), (p1, edge_b(p1)), (p1, edge_b(p1) + 0.6), (p0, edge_b(p0) + 0.6)])
        if len(q) < 3:
            continue
        part(f'ph-s-canal-wall-{k}', 'James River and Kanawha Canal: wall', quad(q), BED, TERRACE, 'stone', 'approximate', CW_NOTE, [NRHP, SRC['lidar']])
        k += 1

# The stone walkway on the south side, over the tailraces, out to the canal wall.
for k, (a0, a1) in enumerate(((-1.0, 0.0), (0.0, 20.0), (20.0, L + 1.0))):
    for kk, q in enumerate(x for x in [clipped([(a0, edge_b(a0) + 0.6), (a1, edge_b(a1) + 0.6), (a1, B0), (a0, B0)])] if len(x) >= 3):
        part(f'ph-s-walk-south-{k}-{kk}', f'{PH}: south walkway', quad(q), TERRACE - 0.18, TERRACE, 'stone', 'approximate',
             'The tailraces ran in tunnels "underneath the stone walkway" on the south side (Friends of Pump House tour; NRHP 2002). '
             'The walkway\'s height and its reach to the canal are approximate.', [SRC['friends-tour'], NRHP])

# The tailrace tunnels: from each wheel pit south under the house and the ground to the lower canal.
TUN_NOTE = ('A vaulted tunnel carried the spent water from the wheel out under the stone walkway to the canal on the south side, below the locks '
            '(NRHP 2002; Friends of Pump House tour; Bolling 1900). One per wheel is assumed; its size, vault and line are approximate.')
SPR = TAIL + 0.1
for k, wa in enumerate(WHEELS):
    b_end = edge_b(wa) + 0.75
    b_start = WP_B[0]
    length = b_start - b_end
    nm = f'{PH}: tailrace {k + 1}'
    ri, ro = 0.9, TUN_HALF
    vault = []
    for i in range(8):
        t0, t1 = math.pi * i / 8, math.pi * (i + 1) / 8
        q = [(ro + ro * math.cos(t0), SPR - (WPIT - 0.3) + ro * math.sin(t0)), (ro + ri * math.cos(t0), SPR - (WPIT - 0.3) + ri * math.sin(t0)),
             (ro + ri * math.cos(t1), SPR - (WPIT - 0.3) + ri * math.sin(t1)), (ro + ro * math.cos(t1), SPR - (WPIT - 0.3) + ro * math.sin(t1))]
        vault.append(r3([v for pt in q for v in pt]))
    walls = [r3([0, 0, ro - ri, 0, ro - ri, SPR - (WPIT - 0.3), 0, SPR - (WPIT - 0.3)]),
             r3([ro + ri, 0, 2 * ro, 0, 2 * ro, SPR - (WPIT - 0.3), ro + ri, SPR - (WPIT - 0.3)]),
             r3([0, 0, 2 * ro, 0, 2 * ro, 0.3, 0, 0.3])]
    # Its first edge across the tunnel, from west to east at its mouth; it runs north from there. The
    # vault is a part of its own, springing over the water, so it always paints over it.
    part(f'ph-x-tailrace-{k}', nm, plane(wa - ro, b_end, wa + ro, b_end, length), WPIT - 0.3, SPR, 'stone', 'approximate', TUN_NOTE,
         [NRHP, SRC['friends-tour'], SRC['bolling-1900']], shape='frame', members=walls)
    off = SPR - (WPIT - 0.3)
    part(f'ph-x-tailrace-vault-{k}', nm, plane(wa - ro, b_end, wa + ro, b_end, length), SPR, SPR + ro, 'stone', 'approximate', TUN_NOTE,
         [NRHP, SRC['friends-tour'], SRC['bolling-1900']], shape='frame', members=[r3([v - (off if i % 2 else 0) for i, v in enumerate(m)]) for m in vault])
    part(f'ph-x-tailwater-{k}', nm, rect(wa - ri + 0.02, wa + ri - 0.02, b_end, b_start), WPIT, TAIL, 'water', 'approximate',
         'The spent water in the tailrace, at the lower canal\'s level (The American Engineer, 1884: a 20-ft fall).', [AE, NRHP])

for k, (a0, a1) in enumerate(((-2.0, 12.0), (12.0, 24.0), (24.0, L + 2.0))):
    part(f'ph-s-walk-north-{k}', f'{PH}: north walkway', rect(a0, a1, B1, WALK_W), WALK_N - 0.3, WALK_N, 'stone', 'written',
         'The stone walkway round the north front, on the forebay wall at the waterline (NRHP 2002; HAER VA-34-1). Width approximate.', [NRHP, HAER])

history = {
    'title': 'The New Pump-House, about 1885 (working draft)',
    'method': 'Working draft, modeled with Claude for Chris Busse from curated parts in tools/stations/pump_house.py: outline from OpenStreetMap; levels from the 2019 schematic design study; '
              'machinery from The American Engineer (1884), text and engravings; rooms from the 2002 National Register nomination and HAER VA-34. Every part names its sources and how it is known.',
    'present': 2026,
    'about': 'Richmond\'s New Pump-House, 1881-83, by Col. Wilfred Emory Cutshaw: canal water turned three turbines that drove nine pumps, lifting drinking water to the Byrd Park reservoir; an open-air pavilion over the machines held dances and pleasure parties.',
    'epochs': [{'year': 1885, 'title': 'The New Pump-House at work', 'note': 'The original Ramsay machinery, two years in service; the pavilion still open.'}],
    'features': features,
    'rules': [
        {'where': {'tag': 'highway'}, 'eras': [], 'note': 'Today\'s paths and drives, not drawn in 1885.'},
        {'where': {'tag': 'waterway'}, 'eras': [], 'note': 'The canals are modeled as parts (forebay, lower level).'},
    ],
    'dates': [],
}
OUT.write_text(json.dumps(history, indent=1, ensure_ascii=False) + '\n')

# ---- the regions' cut planes, figures and sections -----------------------------------------------
# Figures are visitors at a stated height (src/traveler.ts), for scale only: no source says who came.
VISITORS = [((A0 + 1.6, 7.5), 'visitor-skirt', 1), ((A0 + 6.0, 13.2), 'visitor', -1), ((A0 + 11.5, 13.6), 'visitor-skirt', 1),
            ((A0 + 12.6, 13.0), 'visitor', -1), ((A0 + 22.5, 6.0), 'visitor-skirt', -1)]
main = json.loads((ROOT / 'regions' / 'pump-house-cutaway.json').read_text())
main['title'] = 'The New Pump-House, about 1885: cut along the machine room (working draft)'
c = main['cutaway']
c['through'] = lonlat(L / 2, CUT_B)
c['floor'], c['keep'] = UP, 1.5
c['order'] = 'components'
c['lift'] = ['^history:ph-c-pav-floor-s-[1-4]$']
c['travelers'] = [{'at': lonlat(a, b), 'floor': PAV, 'facing': f, 'figure': fig} for (a, b), fig, f in VISITORS] + \
                 [{'at': lonlat(WHEELS[1] + 2.6, STEP_B - 1.2), 'floor': UP, 'facing': -1, 'figure': 'visitor'}]
c['section'] = {'from': -L / 2 - 4, 'to': L / 2 + 4, 'beyond': 13, 'other': 3, 'scale': 10, 'earth': 3,
                'travelers': [{'s': s, 'floor': PAV, 'facing': f, 'figure': fig} for s, fig, f in ((-9.0, 'visitor-skirt', 1), (-7.6, 'visitor', -1), (3.0, 'visitor-skirt', 1), (8.5, 'visitor', -1))]}
(ROOT / 'regions' / 'pump-house-cutaway.json').write_text(json.dumps(main, indent=2) + '\n')

across = json.loads((ROOT / 'regions' / 'pump-house-cutaway-across.json').read_text())
across['title'] = 'The New Pump-House, about 1885: cut across through the middle wheel (working draft)'
across['width'], across['depth'] = 150, 150   # wide enough to hold every part clipped to the main view's frame: this cut is used for its flat section alone
c = across['cutaway']
SEC_A = WHEELS[1] - 0.3          # just west of the middle wheel's center: its rim is cut, its penstock stands beyond
c['through'] = lonlat(SEC_A, 0)
c['floor'], c['keep'] = UP, 1.5
c['parts'] = 'ph-'
c['travelers'] = [{'at': lonlat(SEC_A - 2.5, 11.0), 'floor': PAV, 'facing': 1, 'figure': 'visitor-skirt'},
                  {'at': lonlat(SEC_A - 4.0, 7.0), 'floor': PAV, 'facing': -1, 'figure': 'visitor'}]
b_end = edge_b(WHEELS[1])
c['section'] = {'from': -27, 'to': 41, 'beyond': 25, 'slice': {'parts': ['^history:ph-w-'], 'depth': 0.1}, 'other': 3, 'scale': 10, 'earth': 3,
                'route': [[r3([b])[0], r3([z])[0]] for b, z in ((36, FOREBAY - 0.6), (B1 + 0.2, FOREBAY - 0.6), (B1 + 0.2, HUB_Z + 1.6), (B_IN_N, HUB_Z + 1.5),
                                                                (HUB_B + 0.3, HUB_Z - 1.0), (HUB_B, HUB_Z), (HUB_B, TAIL - 0.9), (b_end, TAIL - 0.9), (b_end - 5, TAIL - 0.6))],
                'travelers': [{'s': 4.5, 'floor': PAV, 'facing': 1, 'figure': 'visitor-skirt'}, {'s': 12.0, 'floor': PAV, 'facing': -1, 'figure': 'visitor'}]}
(ROOT / 'regions' / 'pump-house-cutaway-across.json').write_text(json.dumps(across, indent=2) + '\n')

print(f'{OUT.relative_to(ROOT)}: {len(features)} parts; shaft z {HUB_Z:.2f}, b {HUB_B:.2f}; forebay {FOREBAY:.2f}, tail {TAIL:.2f}; wheels at a {[round(w, 2) for w in WHEELS]}')
