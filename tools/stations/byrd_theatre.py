#!/usr/bin/env python3
"""Model the Byrd Theatre (2908 W. Cary Street, Richmond) as it opened, Christmas Eve 1928.

No plan, section or seating chart of the building was found (see ref/byrd/ and the sheet's
notes). The model is placed from written descriptions and photographs inside the city lot the
1979 National Register nomination gives (about 84 x 135 ft, the 84 ft side on West Cary
Street, on the street's northeast side), so nearly every part is approximate and says so.

The local frame (tools/stations/frame.py): `a` across the front, to the right facing it from
Cary Street, and `b` back into the lot. Both are set on the theatre's OpenStreetMap outline
(way 327377540): its front runs at bearing 113.95° (its back at the same, its sides at 24.2°, a
skew of 0.3° that is ignored), and it measures 25.76 x 41.18 m, the nomination's 84 x 135 ft
(25.6 x 41.15 m) within 0.2 m. The model keeps the nomination's lot, centered on that outline.
The origin is the middle of the outline's front. Heights are given in meters above the Cary
Street sidewalk in front of the theatre, 67.25 m above sea level on the USGS 3DEP lidar
(data/byrd-theatre/dem.bin.gz, 67.2–67.3 m along the front), and written as elevations.

What rests on what:
  lot, front on Cary, NE side                 nomination, item 10 (written)
  outer lobby between two sets of a dozen doors nomination (written); Rudisill 1986 says 28
  lobby ceiling 25 ft, mezzanine on three sides nomination (written); plan approximate
  pool and fountain 20 x 8 ft                 nomination (written size; place approximate)
  projection booth "at the rear of the lobby" nomination (written); place approximate
  chambers over the center of the stage       nomination; Rudisill 1986; foundation (written)
  console on its lift in the open pit         Rudisill 1986 and its 1928 photograph (written)
  boxes either side of the stage              nomination; Rudisill 1986 (written)
  three air tunnels under the floor           foundation, About (written); routes approximate
  facade, marquee, blade sign, neighbors      c. 1929 photograph (written form; sizes approximate)
  every height but the lobby's, every depth   approximate

    python3 tools/stations/byrd_theatre.py   # writes history/byrd-theatre.json
"""

import json
import math
from pathlib import Path

from frame import Frame, Parts

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'history' / 'byrd-theatre.json'

# The middle of the front of the theatre's OSM outline (way 327377540); the HMDB marker (152369,
# 37° 33.134′ N, 77° 28.671′ W) stands on the sidewalk about 9 m east of it.
LON0, LAT0 = -77.4779424, 37.55226939
DATUM = 67.25                        # the sidewalk in front, m above sea level (3DEP lidar)
F = Frame(LON0, LAT0, a_bearing=113.95)
P = Parts(F, 1928, datum=DATUM)

SRC = {
    'nom': 'https://www.dhr.virginia.gov/VLR_to_transfer/PDFNoms/127-0287_Byrd_Theater_1979_Final_Nomination.pdf',
    'nom-map': 'https://www.dhr.virginia.gov/VLR_to_transfer/PDFNoms/127-0287_Byrd_Theater_1979_Final_Nomination.pdf#page=6',
    'to1986': 'https://journals.shareok.org/theatreorgan/article/download/3999/3978/3932',
    'to1977': 'https://journals.shareok.org/theatreorgan/article/download/2935/2914/2910',
    'organ': 'https://byrdtheatre.org/the-mighty-wurlitzer-organ/',
    'about': 'https://byrdtheatre.org/about/',
    'history': 'https://byrdtheatre.org/theatre-history/',
    'seats2025': 'https://byrdtheatre.org/news/2025/01/historic-landmark-restoration-recommences-at-the-byrd-theatre',
    'wiki': 'https://en.wikipedia.org/wiki/Byrd_Theatre',
    'photo1929': 'https://rvarephotoproject3.blogspot.com/2017/03/byrd-theater-c.html',
    'hmdb': 'https://www.hmdb.org/m.asp?m=152369',
    'osm': 'https://www.openstreetmap.org/way/327377540',
    # Round 3 (opened Nov. 18, 2026; research-round3.md)
    'style2014': 'https://www.styleweekly.com/revising-the-script/',
    'rfp': 'https://byrdtheatre.org/rfp-for-general-contractor/',
    'cc-seats': 'https://byrdtheatre.org/curators-corner-balcony-seat-replacement/',
    'cc-side': 'https://byrdtheatre.org/curators-corner-side-sections-start/',
    'cc-electrical': 'https://byrdtheatre.org/curators-corner-electrical/',
    'cc-building': 'https://byrdtheatre.org/curators-corners-historic-building/',
    'tours': 'https://byrdtheatre.org/tours/',
    'rfm2015': 'https://richmondfamilymagazine.com/arts/richmonds-movie-palace/',
    'rm2021': 'https://richmondmagazine.com/news/sunday-story/a-wild-and-lovely-contraption/',
    'boomer2014': 'https://www.boomermagazine.com/byrd-man/',
    'rvamag2026': 'https://rvamag.com/community/the-byrd-theatre-is-still-richmonds-palace-of-dreams.html',
    'mat2019': 'https://midatlantictraveler.wordpress.com/2019/04/16/va-hidden-gem-the-byrd-theatre-in-richmond/',
    'match2024': 'https://www.matchcollegiate.org/2024/05/23/the-byrd-theatre-richmonds-historic-gem/',
    'ct': 'https://cinematreasures.org/theaters/334',
    'rm2006': 'https://richmondmagazine.com/best-of-richmond/225-secrets-of-the-city/',
}
STYLE, RFP = SRC['style2014'], SRC['rfp']
NOM, PHOTO, T86 = SRC['nom'], SRC['photo1929'], SRC['to1986']
APPROX = 'No plan or section of the theatre was found; '

# ---- the cut and the main dimensions (meters; elevations above the sidewalk) ---------------------
CUT_A = 1.6           # the cut runs 1.6 m east of the center line, so the chandelier and the
                      # console, both on the center line, stand whole behind it
LOT_W, LOT_D = 25.6, 41.13          # 84 x 135 ft (41.15 m), 2 cm short so the back wall lies inside
                                    # the flat section's frame, which ends at 41.15 m on its earth's grid
W2 = LOT_W / 2
T = 0.6                             # outer walls (approximate)
WI = W2 - T                         # inner face of the side walls
WL = WI - 0.05                      # face of the plaster lining on them
Z_LOBBY = 0.3                       # lobby floor, a step up from the sidewalk (approximate)
Z_LCEIL = Z_LOBBY + 7.62            # the lobby ceiling, 25 ft (nomination)
Z_MEZZ = 3.9                        # mezzanine lounge floor (approximate)
B_VEST = 3.6                        # inner doors: the outer lobby runs from the front to here
B_HOUSE = 13.0                      # the auditorium's rear wall, behind the lobby
ROW = 0.86                          # row spacing, 34 in (approximate)
ROWS = 21                           # orchestra rows (approximate)
B_ROW0 = B_HOUSE + 0.6
RAKE = 0.075                        # fall per row toward the stage (approximate)
B_PIT = B_ROW0 + ROWS * ROW         # front of the orchestra pit
Z_FRONT_ROW = Z_LOBBY - RAKE * (ROWS - 1)
Z_FILL = -1.55                      # the bottom of the raked floor's fill: the tunnels' roof
B_STAGE = 35.05                     # the stage's front edge
B_PROS = 35.45                      # the proscenium wall, 35.45–36.25: the stage behind it is
                                    # 14 ft deep to the back wall (13 to 14 ft: Style Weekly 2014;
                                    # The Match 2024)
Z_STAGE = -0.2
Z_BSMT = -3.6                       # basement under the stage and the pit
Z_PIT = -3.2
Z_CORNICE = 14.6                    # top of the auditorium's side walls (approximate)
Z_CEIL = 15.0                       # the flat ceiling around the dome (approximate)
DOME_B, DOME_R, DOME_RISE = 23.0, 6.5, 3.6
Z_ROOF = 19.6                       # auditorium roof (approximate)
Z_CHAMBER = 10.4                    # organ chambers' floor (approximate)
Z_STAGE_ROOF = 16.9                 # roof over the stage and chambers (approximate)
Z_FRONT = 20.4                      # top of the front's parapet (approximate)
BAL_FRONT, BAL_ROWS, BAL_RISE, BAL_Z0 = 21.0, 13, 0.45, 6.4
PW = 2.8                            # half the pit's width (approximate): the spring room lies east of it
# The basement behind and beside the pit (all approximate; no plan was found):
B_BACK = LOT_D - T                  # the back wall's inner face
B_BS = B_PROS + 1.1                 # the basement rooms under the stage start here (36.55)
POND_A0, POND_A1 = PW + 0.3, WI     # the spring room: about 30 x 30 ft (Style Weekly 2014), house right
POND_B0, POND_B1 = B_PIT, B_BACK
Z_POND_W, Z_POND0 = -4.2, -5.6      # the water's surface and the pond's floor (approximate)
BOIL_A0 = -5.0                      # the boiler room: a -5.0 to the spring room's wall
Z_SHAFT = -6.2                      # the bottom of the console lift's shaft (approximate)
B_BOOTH = BAL_FRONT - BAL_ROWS * 0.9    # the booth's front wall, behind the balcony's last row
Z_BOOTH = BAL_Z0 + BAL_ROWS * BAL_RISE

FACADE = 'Byrd Theatre: the Cary Street front'
LOBBY = 'Byrd Theatre: lobby'
HOUSE = 'Byrd Theatre: auditorium'
STAGE = 'Byrd Theatre: stage'
ORGAN = 'Byrd Theatre: Wurlitzer organ'


def C(id_):
    return f'byrd-c-{id_}'      # cut parts


def K(id_):
    return f'byrd-k-{id_}'      # kept whole: stand behind the cut, not cut


def box(id_, name, a0, a1, b0, b1, z0, z1, tone, conf, note, src, **kw):
    return P.box(id_, name, a0, a1, b0, b1, z0, z1, tone, conf, note, src, **kw)


def seats(id_, name, a0, a1, b0, b1, z0, z1, note, src):
    """A row of seats, never cut: split at the plane, its ends show in their own red on the
    cut (and in the flat section, as the rows' profiles), and the part on the side lifted away
    stays, below the plan's height."""
    pieces = [(a0, a1)] if a1 <= CUT_A or a0 >= CUT_A else [(a0, CUT_A), (CUT_A, a1)]
    for k, (p, q) in enumerate(pieces):
        box(K(f'{id_}' + ('' if len(pieces) == 1 else f'-{k + 1}')), name, p, q, b0, b1, z0, z1, 'seat', 'approximate', note, src)


# ---- the massing, for whole views, and the outline of what the cut lifts away -------------------
box('byrd-w-mass', 'Byrd Theatre', -W2, W2, 0, LOT_D, 0, Z_ROOF, 'redBrick', 'approximate',
    'The theatre as one block on its lot (about 84 x 135 ft, nomination item 10), drawn in views without a cutaway. Height approximate.',
    [NOM], only='whole')

# ---- the street, the sidewalks, the neighbors ------------------------------------------------------
# West Cary Street, its sidewalks and the buildings round the theatre are OpenStreetMap's
# (data/byrd-theatre/osm.json), with the ground from the USGS 3DEP lidar. A neighbor stands in
# 1928 only where the assessor's year built (or an OSM start date) puts it up by then: the
# dated-series rule, history.ts. Neighbors are not modeled here.

# ---- the front -----------------------------------------------------------------------------------
FRONT_NOTE = 'The front on Cary Street: red brick with white terra-cotta ornament (nomination), its arched windows, frieze and cornice as the c. 1929 photograph shows them; sizes and places approximate.'
for k, (a0, a1) in enumerate(((-W2, -6.0), (6.0, W2))):
    box(C(f'front-pier-{k + 1}'), FACADE, a0, a1, 0, T, 0, Z_FRONT, 'redBrick', 'written', FRONT_NOTE, [NOM, PHOTO])
box(C('front-over-doors'), FACADE, -6.0, 6.0, 0, T, 3.6, Z_FRONT, 'redBrick', 'written', FRONT_NOTE, [NOM, PHOTO])
# Black marble round the entrance and the box office between the doors (nomination).
MARBLE = 'Black Italian marble, framing the main entrance and making the box office (nomination); its extent is approximate.'
for k, (a0, a1) in enumerate(((-6.4, -6.0), (6.0, 6.4))):
    box(C(f'entrance-marble-{k + 1}'), FACADE, a0, a1, -0.1, 0.0, 0, 3.6, 'marble', 'written', MARBLE, [NOM])
box(C('entrance-marble-head'), FACADE, -6.4, 6.4, -0.1, 0.0, 3.3, 3.6, 'marble', 'written', MARBLE, [NOM])
box(C('box-office'), 'Byrd Theatre: box office', -1.0, 1.0, -0.9, 0.6, 0, 2.7, 'marble', 'written',
    'The box office, "plain but impressive", of black Italian marble (nomination). Placed between the doors and sized approximately.', [NOM])
box(C('box-office-window'), 'Byrd Theatre: box office', -0.6, 0.6, -0.94, -0.9, 1.1, 2.0, 'glass', 'approximate',
    'The box office window. Approximate.', [NOM])
DOORS = 'One of two sets of a dozen plate-glass doors framed in brass, with the outer lobby between them (nomination; Rudisill writes of 28 brass doors). Their width and height are approximate.'
for name, b0, b1, a_ranges in (('outer', 0.15, 0.35, ((-6.0, -1.0), (1.0, 6.0))), ('inner', B_VEST - 0.1, B_VEST + 0.1, ((-6.0, 6.0),))):
    for j, (a0, a1) in enumerate(a_ranges):
        box(C(f'doors-{name}-{j + 1}'), LOBBY, a0, a1, b0, b1, Z_LOBBY if name == 'inner' else 0, 3.1, 'glass', 'written', DOORS, [NOM, T86])
        n = round((a1 - a0) / (10.0 / 12 if name == 'outer' else 1.0))
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            box(C(f'doors-{name}-{j + 1}-frame-{i}'), LOBBY, a - 0.05, a + 0.05, b0 - 0.03, b1 + 0.03, Z_LOBBY if name == 'inner' else 0, 3.1, 'bronze', 'written', DOORS, [NOM, T86])
    box(C(f'doors-{name}-head'), LOBBY, -6.0, 6.0, b0 - 0.03, b1 + 0.03, 3.1, 3.6, 'bronze', 'written', DOORS, [NOM, T86])
# The windows and ornament of the front, on its face.
def window(id_, a0, a1, z0, zs, zt, frame=0.35):
    box(C(f'{id_}-surround'), FACADE, a0 - frame, a1 + frame, -0.10, 0.0, z0 - frame, zt + frame * 0.6, 'terracotta', 'written', FRONT_NOTE, [NOM, PHOTO])
    box(C(f'{id_}'), FACADE, a0, a1, -0.14, -0.10, z0, zs, 'glass', 'written', FRONT_NOTE, [PHOTO])
    P.poly(C(f'{id_}-arch'), FACADE, [(a0, -0.14), (a1, -0.14), (a1, -0.10), (a0, -0.10)], zs, zt, 'glass', 'written', FRONT_NOTE, [PHOTO], shape='arch')


window('front-arch-window', -2.0, 2.0, 7.4, 11.0, 13.0)
for k, a in enumerate((-10.6, -8.2, 8.2, 10.6)):
    window(f'front-window-{k + 1}', a - 0.65, a + 0.65, 6.2, 8.2, 8.9, 0.22)
box(C('front-frieze'), FACADE, -W2, W2, -0.16, 0.0, 17.2, 18.4, 'terracotta', 'written', FRONT_NOTE, [NOM, PHOTO])
box(C('front-cornice'), FACADE, -W2 - 0.2, W2 + 0.2, -0.6, 0.0, 18.4, 18.9, 'terracotta', 'written', FRONT_NOTE, [NOM, PHOTO])
box(C('front-coping'), FACADE, -W2, W2, -0.05, T, Z_FRONT - 0.25, Z_FRONT, 'terracotta', 'approximate', FRONT_NOTE, [PHOTO])
# The marquee: "a simple bronze structure with no lettering" (nomination), across the front.
box(K('marquee'), 'Byrd Theatre: marquee', -7.6, 7.6, -3.0, 0.0, 3.9, 4.5, 'bronze', 'written',
    'The original marquee, "a simple bronze structure with no lettering" (nomination); its band is blank in the c. 1929 photograph too. Its size is approximate.', [NOM, PHOTO])
box(K('marquee-soffit-lights'), 'Byrd Theatre: marquee', -7.3, 7.3, -2.8, -0.2, 3.85, 3.9, 'lamp', 'approximate',
    'The marquee\'s underside, lit (approximate).', [PHOTO])
box(K('blade-sign'), 'Byrd Theatre: vertical sign', -11.3, -10.8, -2.3, -0.2, 6.0, 16.6, 'bronze', 'written',
    'The tall vertical sign at the corner of the front, as the c. 1929 photograph shows it (it came down in 1971, foundation history). Its lettering is not drawn; its size is approximate.', [PHOTO, SRC['history']])

# ---- outer walls -------------------------------------------------------------------------------
SIDE = 'An outer side wall of plain brick. Its thickness and height are approximate.'
# The east wall stands on the side the cut lifts away, where only its plan is drawn: below the
# sidewalk it is hidden by the ground beside it (`ground-east`, below).
for side, a0, a1 in (('west', -W2, -WI), ('east', WI, W2)):
    west = side == 'west'
    box(C(f'wall-{side}'), 'Byrd Theatre: side wall', a0, a1, T, B_HOUSE, 0, Z_ROOF, 'redBrick', 'approximate', SIDE, [NOM])
    box(C(f'wall-{side}-house'), 'Byrd Theatre: side wall', a0, a1, B_HOUSE, B_PIT, Z_FILL, Z_ROOF, 'redBrick', 'approximate', SIDE, [NOM])
    box(C(f'wall-{side}-front'), 'Byrd Theatre: side wall', a0, a1, B_PIT, B_PROS, -1.6 if west else Z_POND0, Z_ROOF, 'redBrick', 'approximate', SIDE, [NOM])
    box(C(f'wall-{side}-stage'), 'Byrd Theatre: side wall', a0, a1, B_PROS, LOT_D, Z_BSMT if west else Z_POND0, Z_STAGE_ROOF, 'redBrick', 'approximate', SIDE, [NOM])
    if west:
        box(C(f'wall-{side}-pit'), 'Byrd Theatre: basement wall', a0, a1, B_PIT, B_PROS, Z_BSMT, -1.6, 'redBrick', 'approximate', SIDE, [NOM])
# ---- the basement: the spring room, the boiler, coal, the air handler -------------------------
# Under the stage and beside the pit. No plan was found: the rooms are placed from the general
# manager's 2014 walk-through (Style Weekly: from the orchestra aisle backstage right, past the
# boiler, to a concrete opening over the spring and its pond, about 30 by 30 ft) and the
# foundation's RFP (coal door and coal room at the rear, boiler and air handler in the basement,
# a brick chimney flue). "Backstage right" may mean stage right (house left) or the walker's right
# (house right): drawn house right, approximately.
SPRING = ('The spring room: an underground spring breached in the 1927 excavation feeds a retention pond of about 30 by 30 feet, '
          'seen from a concrete opening past the boiler (the general manager, Style Weekly, 2014; a 2019 travel piece gives 25 by 25 feet). '
          'He says the spring was never used for the air conditioning; Cinema Treasures says its water can be pumped for it, and '
          'Wikipedia that it used to be. Its side of the stage and its depth are approximate.')
SPRING_SRC = [STYLE, SRC['mat2019'], SRC['ct'], SRC['rm2006']]
# The pond fills its room. The water is never cut: split at nothing, it shows as water in both sections.
box(C('pond-floor'), 'Byrd Theatre: the spring room', POND_A0, POND_A1, POND_B0, POND_B1, Z_POND0 - 0.3, Z_POND0, 'stone', 'approximate', SPRING, SPRING_SRC)
box(K('pond-water'), 'Byrd Theatre: the spring room', POND_A0, POND_A1, POND_B0, POND_B1, Z_POND0, Z_POND_W, 'water', 'written', SPRING, SPRING_SRC)
OPEN_B0, OPEN_B1 = 37.6, 39.4           # the concrete opening onto the pond, from the boiler room
box(C('pond-wall-north'), 'Byrd Theatre: the spring room', PW, POND_A1, POND_B0 - 0.3, POND_B0, Z_POND0 - 0.3, Z_FRONT_ROW - 0.3, 'stone', 'approximate', SPRING, SPRING_SRC)
for k, (b0, b1, z0, z1) in enumerate(((B_PIT, OPEN_B0, Z_POND0 - 0.3, Z_STAGE - 0.3), (OPEN_B1, B_BACK, Z_POND0 - 0.3, Z_STAGE - 0.3),
                                      (OPEN_B0, OPEN_B1, Z_POND0 - 0.3, Z_BSMT + 1.0), (OPEN_B0, OPEN_B1, Z_BSMT + 2.4, Z_STAGE - 0.3))):
    box(C(f'pond-wall-west-{k + 1}'), 'Byrd Theatre: the spring room', PW, POND_A0, b0, b1, z0, z1, 'stone', 'approximate',
        SPRING + ' The opening in this wall is the "concrete opening" of the walk-through; its size is approximate.', SPRING_SRC)

BASE = 'The basement under the stage and beside the pit. The foundation\'s RFP lists a coal door and coal room at the rear, the boiler and the air handler in the basement, and a brick chimney flue; the general manager walks past the boiler to the spring (Style Weekly, 2014). Rooms, sizes and places are approximate.'
BASE_SRC = [RFP, STYLE]
box(C('basement-floor'), STAGE, -WI, PW, B_BS, B_BACK, Z_BSMT, Z_BSMT + 0.3, 'floor', 'approximate', BASE, BASE_SRC)
box(C('basement-floor-front'), STAGE, -WI, -PW - 0.25, B_PIT, B_BS, Z_BSMT, Z_BSMT + 0.3, 'floor', 'approximate', BASE, BASE_SRC)
# The wall under the proscenium, between the air handler's room and the rooms under the stage, with a door.
for k, (a0, a1, z1) in enumerate(((-WI, -9.0, Z_STAGE - 0.3), (-8.0, -PW - 0.25, Z_STAGE - 0.3), (-9.0, -8.0, Z_STAGE - 0.3))):
    box(C(f'basement-wall-{k + 1}'), STAGE, a0, a1, B_BS - 0.3, B_BS, Z_BSMT + 0.3 if k < 2 else Z_BSMT + 2.4, z1, 'stone', 'approximate', BASE, BASE_SRC)
box(C('basement-wall-pit'), STAGE, -PW - 0.25, PW, B_STAGE, B_BS, Z_BSMT, Z_STAGE - 0.3, 'stone', 'approximate', BASE, BASE_SRC)
# The coal room at the rear, behind a wall with a doorway, its door to the alley in the back wall.
COAL = 'The coal room at the rear of the building, with its coal door to the alley (foundation, RFP). The coal heaped here fed the boiler next door. Places and sizes approximate.'
for k, (b0, b1, z0) in enumerate(((B_BS, 37.4, Z_BSMT + 0.3), (38.6, B_BACK, Z_BSMT + 0.3), (37.4, 38.6, Z_BSMT + 2.4))):
    box(C(f'coal-wall-{k + 1}'), STAGE, BOIL_A0 - 0.3, BOIL_A0, b0, b1, z0, Z_STAGE - 0.3, 'stone', 'approximate', COAL, [RFP])
P.poly(K('coal-heap'), 'Byrd Theatre: coal', [(-11.9, 38.2), (-6.0, 38.6), (-5.6, 40.4), (-11.9, 40.4)], Z_BSMT + 0.3, Z_BSMT + 1.5, 'coal', 'approximate',
       COAL, [RFP], shape='inset', levels=[[0, 0, 0], [1.2, 1.6, 0]])
box(K('coal-chute'), 'Byrd Theatre: coal', -10.6, -9.6, 39.4, B_BACK, Z_BSMT + 1.5, -0.9, 'iron', 'approximate', COAL, [RFP])
box(C('coal-door'), 'Byrd Theatre: coal door', -10.7, -9.5, B_BACK - 0.02, LOT_D + 0.03, -0.9, 0.1, 'iron', 'written', COAL, [RFP])
BOILER = 'The boiler, in the basement (foundation, RFP), which the general manager passes on his way to the spring (Style Weekly, 2014). Its flue rises in a brick chimney (RFP). Size and place approximate; drawn as a coal-fired boiler of the time.'
box(K('boiler'), 'Byrd Theatre: boiler', -3.9, -0.9, 37.3, 39.7, Z_BSMT + 0.3, Z_BSMT + 2.3, 'iron', 'written', BOILER, [RFP, STYLE])
box(K('boiler-door'), 'Byrd Theatre: boiler', -3.4, -2.0, 37.1, 37.3, Z_BSMT + 0.7, Z_BSMT + 1.4, 'coal', 'approximate', BOILER, [RFP])
box(K('boiler-breeching'), 'Byrd Theatre: boiler', -3.0, -2.2, 39.7, 39.95, Z_BSMT + 1.7, Z_BSMT + 2.3, 'iron', 'approximate', BOILER, [RFP])
FLUE = 'The brick chimney flue (foundation, RFP), drawn rising from the boiler up the back wall and past the roof. Place and height approximate.'
box(C('flue'), 'Byrd Theatre: chimney flue', -3.4, -1.8, 39.95, B_BACK, Z_BSMT + 0.3, Z_STAGE_ROOF + 2.2, 'redBrick', 'written', FLUE, [RFP])
# The air handler, west of the pit, where the three tunnels under the floor begin.
AIR = 'The air handler (foundation, RFP), in the basement where the three concrete tunnels under the orchestra floor begin (foundation, About). Drawn as a fan and coil box; its size, place and the ducts to the tunnels are approximate.'
box(K('air-handler'), 'Byrd Theatre: air handler', -11.6, -6.2, 32.2, 35.4, Z_BSMT + 0.3, Z_BSMT + 1.9, 'iron', 'written', AIR, [RFP, SRC['about']])
P.add(K('air-handler-fan'), 'Byrd Theatre: air handler', F.ring([(-5.0 + 0.6 * math.cos(2 * math.pi * k / 12), 33.8 + 0.6 * math.sin(2 * math.pi * k / 12)) for k in range(12)]),
      Z_BSMT + 0.3, Z_BSMT + 1.5, 'iron', 'approximate', AIR, [RFP], shape='revolve', levels=[[0, 1, 0], [1.2, 1, 0]])

# Beyond the east wall, below the sidewalk: the ground, drawn in the ground's own color and
# uninked, so the plan on the side the cut lifts away shows nothing below the ground (the raked
# floor and its fill go down 1.55 m).
box(K('ground-east'), 'The ground east of the theatre', W2, W2 + 3.0, B_HOUSE - 0.5, LOT_D, Z_POND0 - 0.4, 0, 'land', 'approximate',
    'The ground beside the theatre, below the sidewalk\'s level: it hides the floor\'s fill on the side the cut lifts away.', [SRC['osm']], only='cutaway')
LINING = 'The plastered inside face of the outer wall. Approximate.'
# Over the lobby's ceiling nothing is known of the rooms: the wall is left bare.
box(C('lining-lobby'), LOBBY, -WI, -WI + 0.05, T, B_HOUSE - 0.6, Z_LOBBY, Z_LCEIL, 'plaster', 'approximate', LINING, [NOM])
box(C('lining-house'), HOUSE, -WI, -WI + 0.05, B_HOUSE, B_PROS, Z_FRONT_ROW - 0.3, Z_CEIL, 'plaster', 'approximate', LINING, [NOM])
box(C('wall-back'), 'Byrd Theatre: back wall', -WI, 8.0, LOT_D - T, LOT_D, Z_BSMT, Z_STAGE_ROOF, 'redBrick', 'approximate', SIDE, [NOM])
box(C('wall-back-east'), 'Byrd Theatre: back wall', 8.0, WI, LOT_D - T, LOT_D, -1.6, Z_STAGE_ROOF, 'redBrick', 'approximate', SIDE, [NOM])
# The roof over the auditorium, and the ceiling between the dome and the near side wall, are
# lifted away in the cutaway (the region's `lift`), so the side wall's niches show; the flat
# section draws them.
box(C('roof'), 'Byrd Theatre: roof', -W2, W2, T, B_BOOTH, Z_ROOF - 0.4, Z_ROOF, 'roof', 'approximate', 'The roof over the lobby, flat behind the front\'s parapet. Height approximate.', [PHOTO])
box(C('roof-house'), 'Byrd Theatre: roof', -W2, W2, B_BOOTH, B_PROS + 0.8, Z_ROOF - 0.4, Z_ROOF, 'roof', 'approximate', 'The roof over the auditorium, flat. Height approximate.', [PHOTO])
box(C('stage-roof'), 'Byrd Theatre: roof', -W2, W2, B_PROS + 0.8, LOT_D, Z_STAGE_ROOF - 0.4, Z_STAGE_ROOF, 'roof', 'approximate', 'The roof over the stage and the organ chambers. Height approximate.', [NOM])

# ---- the lobby ------------------------------------------------------------------------------------
LOBBY_NOTE = 'The main lobby: its ceiling twenty-five feet high, vaulted and heavy with gold-leaf plaster; heavily veined marble halfway up the walls; three murals on one wall; the other three sides open onto a mezzanine lounge (nomination). The plan is approximate.'
box(C('lobby-floor'), LOBBY, -WI, WI, T, B_HOUSE, 0, Z_LOBBY, 'floor', 'approximate', LOBBY_NOTE, [NOM])
box(C('lobby-ceiling'), LOBBY, -WI, WI, B_VEST, B_HOUSE - 0.6, Z_LCEIL, Z_LCEIL + 0.4, 'gold', 'written', LOBBY_NOTE + ' Its height is the nomination\'s; drawn flat.', [NOM])
for k, b0 in enumerate((B_VEST + 0.3, B_VEST + 3.2, B_VEST + 6.1)):
    box(C(f'lobby-ceiling-beam-{k + 1}'), LOBBY, -WI, WI, b0, b0 + 0.4, Z_LCEIL - 0.45, Z_LCEIL, 'gold', 'approximate', LOBBY_NOTE, [NOM])
box(C('vestibule-ceiling'), LOBBY, -WI, WI, T, B_VEST + 0.1, Z_MEZZ, Z_MEZZ + 0.3, 'floor', 'approximate', 'The mezzanine lounge over the outer lobby (nomination: the lounge on three sides). Approximate.', [NOM])
box(C('mezz-west'), LOBBY, -WI, -9.0, B_VEST + 0.1, B_HOUSE - 0.6, Z_MEZZ, Z_MEZZ + 0.3, 'floor', 'approximate', 'The mezzanine lounge along the lobby\'s side (nomination). Its depth is approximate.', [NOM])
box(C('mezz-east'), LOBBY, 9.0, WI, B_VEST + 0.1, B_HOUSE - 0.6, Z_MEZZ, Z_MEZZ + 0.3, 'floor', 'approximate', 'The mezzanine lounge along the lobby\'s side (nomination). Its depth is approximate.', [NOM])
RAIL = 'The mezzanine\'s solid bronze handrail (nomination), on a low balustrade; its height is approximate.'
box(C('mezz-rail-front'), LOBBY, -9.0, 9.0, B_VEST + 0.1, B_VEST + 0.3, Z_MEZZ + 0.3, Z_MEZZ + 1.3, 'bronze', 'written', RAIL, [NOM])
for side, a0, a1 in (('west', -9.2, -9.0), ('east', 9.0, 9.2)):
    box(C(f'mezz-rail-{side}'), LOBBY, a0, a1, B_VEST + 0.1, B_HOUSE - 0.6, Z_MEZZ + 0.3, Z_MEZZ + 1.3, 'bronze', 'written', RAIL, [NOM])
    for k, b in enumerate((B_VEST + 2.5, B_VEST + 6.0)):
        box(C(f'mezz-post-{side}-{k + 1}'), LOBBY, a0 - 0.1, a1 + 0.1, b - 0.2, b + 0.2, Z_LOBBY, Z_MEZZ, 'stone', 'approximate', 'A marble-cased post under the mezzanine. Approximate.', [NOM])
# The back wall of the lobby, the auditorium's rear wall: three murals on it, marble below, and a door on the cut.
for k, (a0, a1) in enumerate(((-WI, 1.3), (3.3, WI))):
    box(C(f'house-rear-wall-{k + 1}'), LOBBY, a0, a1, B_HOUSE - 0.6, B_HOUSE, 0, BAL_Z0 + 3.5, 'plaster', 'approximate', LOBBY_NOTE, [NOM])
box(C('house-rear-door-head'), LOBBY, 1.3, 3.3, B_HOUSE - 0.6, B_HOUSE, 2.7, BAL_Z0 + 3.5, 'plaster', 'approximate', 'Over a door from the lobby into the auditorium. Approximate.', [NOM])
box(C('lobby-marble'), LOBBY, -WI, WI, B_HOUSE - 0.66, B_HOUSE - 0.6, Z_LOBBY, Z_LOBBY + 3.8, 'stone', 'written', 'Heavily veined marble halfway up the lobby\'s walls (nomination); its height here is approximate.', [NOM])
MURAL = 'One of the three murals that line one wall of the lobby (nomination), painted by Arthur Brounet (foundation). Not depicted: the panel is left plain. Which wall and their size are approximate.'
for k, a in enumerate((-6.5, -0.3, 6.5)):
    box(C(f'lobby-mural-{k + 1}'), LOBBY, a - 1.1, a + 1.1, B_HOUSE - 0.7, B_HOUSE - 0.66, Z_LOBBY + 4.2, Z_LOBBY + 6.4, 'bronze', 'written', MURAL, [NOM, SRC['about']])
    P.poly(C(f'lobby-mural-{k + 1}-arch'), LOBBY, [(a - 1.1, B_HOUSE - 0.7), (a + 1.1, B_HOUSE - 0.7), (a + 1.1, B_HOUSE - 0.66), (a - 1.1, B_HOUSE - 0.66)],
           Z_LOBBY + 6.4, Z_LOBBY + 7.1, 'bronze', 'written', MURAL, [NOM], shape='arch')
# The pool and fountain, 20 x 8 ft, where the concession counter later stood (nomination).
POOL = 'The twenty-by-eight-foot pool and fountain of the 1928 lobby, with its marble fender and bronze rails (nomination); it held fish (Rudisill 1986) and gave way to a candy stand about 1940–41 (foundation). Its place in the lobby is approximate.'
PA, PB0, PB1 = 3.05, 9.3, 9.3 + 2.44
for k, (a0, a1, b0, b1) in enumerate(((-PA, PA, PB0, PB0 + 0.3), (-PA, PA, PB1 - 0.3, PB1), (-PA, -PA + 0.3, PB0 + 0.3, PB1 - 0.3), (PA - 0.3, PA, PB0 + 0.3, PB1 - 0.3))):
    box(C(f'pool-fender-{k + 1}'), LOBBY, a0, a1, b0, b1, Z_LOBBY, Z_LOBBY + 0.6, 'stone', 'written', POOL, [NOM, T86, SRC['history']])
box(C('pool-water'), LOBBY, -PA + 0.3, PA - 0.3, PB0 + 0.3, PB1 - 0.3, Z_LOBBY, Z_LOBBY + 0.45, 'water', 'written', POOL, [NOM, T86])
box(K('fountain'), LOBBY, -0.3, 0.3, (PB0 + PB1) / 2 - 0.3, (PB0 + PB1) / 2 + 0.3, Z_LOBBY + 0.45, Z_LOBBY + 1.6, 'stone', 'approximate', POOL, [NOM])
P.add(K('lobby-chandelier'), LOBBY, F.ring([(-4.5 + 0.9 * math.cos(2 * math.pi * k / 12), 7.2 + 0.9 * math.sin(2 * math.pi * k / 12)) for k in range(12)]),
      Z_LCEIL - 2.6, Z_LCEIL, 'lamp', 'written', 'The lobby\'s large crystal chandelier (nomination). Its place and size are approximate.', [NOM],
      shape='revolve', levels=[[0, 0.15, 0], [0.5, 0.75, 0], [1.2, 1.0, 0], [1.7, 0.6, 0], [1.75, 0.08, 0], [2.6, 0.08, 0]])

# ---- the auditorium: the orchestra floor and its seats ----------------------------------------------
ORCH = 'The orchestra floor, falling in rows toward the stage. The rows, their spacing and the rake are approximate; no seating chart was found.'
SEATS = 'A row of seats in crimson velvet (nomination: red velvet accents), 19 in wide (the original seats, foundation 2025), in a center section between two aisles and two side sections (the foundation speaks of the main auditorium\'s center section). Rows and aisles approximate.'
box(C('orch-cross-aisle'), HOUSE, -WI, WI, B_HOUSE, B_ROW0, Z_FILL, Z_LOBBY, 'floor', 'approximate', ORCH, [NOM])
SECTIONS = ((-11.2, -5.6), (-4.6, 4.6), (5.6, 11.2))
for k in range(ROWS):
    b0 = B_ROW0 + k * ROW
    z = Z_LOBBY - RAKE * k
    box(C(f'orch-floor-{k + 1}'), HOUSE, -WI, WI, b0, b0 + ROW, Z_FILL, z, 'floor', 'approximate', ORCH + ' Cut down to the air tunnels\' roof: the floor and the ground it is laid on.', [NOM])
    for j, (a0, a1) in enumerate(SECTIONS):
        seats(f'orch-seats-{k + 1}-{j + 1}', HOUSE, a0, a1, b0 + 0.1, b0 + 0.62, z, z + 0.85, SEATS, [NOM, SRC['seats2025']])
# The open orchestra pit and the console's lift (1928: the stage was later extended over it).
PIT = 'The orchestra pit, open in 1928 (the stage was later extended over it: nomination; Rudisill 1986), with the console\'s lift at its middle. Its width is approximate: drawn narrow, to leave room beside it for the spring room.'
# The pit floor, round the lift's shaft.
for k, (a0, a1, b0, b1) in enumerate(((-PW, PW, B_PIT, 32.5), (-PW, PW, 34.5, B_STAGE), (-PW, -1.65, 32.5, 34.5), (1.65, PW, 32.5, 34.5))):
    box(C(f'pit-floor-{k + 1}'), STAGE, a0, a1, b0, b1, Z_PIT - 0.3, Z_PIT, 'floor', 'approximate', PIT, [NOM, T86])
box(C('pit-rail'), STAGE, -PW, PW, B_PIT, B_PIT + 0.25, Z_PIT, Z_FRONT_ROW + 0.95, 'plaster', 'written', 'The rail round the orchestra pit, a balustrade as the 1928 photograph of the console shows; its height is approximate.', [T86])
for side, a0, a1 in (('west', -WI, -PW), ('east', PW, WI)):
    box(C(f'pit-side-floor-{side}'), STAGE, a0, a1, B_PIT, B_PROS, Z_FRONT_ROW - 0.3, Z_FRONT_ROW, 'floor', 'approximate', 'The floor beside the pit, at the front row\'s level. Approximate.', [NOM])
    box(C(f'pit-side-wall-{side}'), STAGE, (a1 - 0.25) if side == 'west' else a0, a1 if side == 'west' else a0 + 0.25, B_PIT, B_STAGE, Z_BSMT, Z_FRONT_ROW + 0.95, 'plaster', 'approximate', PIT, [NOM])
box(C('stage-apron-wall'), STAGE, -PW, PW, B_STAGE, B_PROS, Z_PIT, Z_STAGE, 'plaster', 'approximate', 'The stage\'s front, down to the pit floor. Approximate.', [NOM])
# The lift's shaft under the pit (foundation, RFP: a screw lift in a basement shaft).
LIFT = 'The console\'s screw lift, in its shaft under the pit (foundation, RFP), the original Peter Clark lift (Rudisill 1986). The house organist says the building shudders slightly as it starts (Richmond Family Magazine, 2015). The shaft\'s depth and the screw\'s size are approximate.'
for k, (a0, a1, b0, b1) in enumerate(((-1.9, -1.65, 32.5, 34.5), (1.65, 1.9, 32.5, 34.5), (-1.9, 1.9, 32.25, 32.5), (-1.9, 1.9, 34.5, 34.75))):
    box(C(f'lift-shaft-{k + 1}'), ORGAN, a0, a1, b0, b1, Z_SHAFT, Z_PIT - 0.3, 'stone', 'approximate', LIFT, [RFP, T86])
box(C('lift-shaft-floor'), ORGAN, -1.9, 1.9, 32.25, 34.75, Z_SHAFT - 0.3, Z_SHAFT, 'stone', 'approximate', LIFT, [RFP])

# ---- the stage, the proscenium, the screen -----------------------------------------------------
STAGEN = ('The stage, 13 to 14 feet deep, with no dressing rooms and the alley about 15 feet behind the screen (Style Weekly, 2014; The Match, 2024): '
          '"the limited backstage area would not support stage productions" (nomination). Drawn 14 feet deep from the proscenium.')
# In two pieces: the one on the side the cut lifts away is lifted whole (the region's `lift`), to
# show the spring room and the boiler room under it.
box(C('stage-floor'), STAGE, -WI, CUT_A + 0.3, B_PROS, B_BACK, Z_STAGE - 0.3, Z_STAGE, 'wood', 'written', STAGEN, [NOM, STYLE, SRC['match2024']])
box(C('stage-floor-east'), STAGE, CUT_A + 0.3, WI, B_PROS, B_BACK, Z_STAGE - 0.3, Z_STAGE, 'wood', 'written', STAGEN, [NOM, STYLE, SRC['match2024']])
PROS = 'The proscenium wall. The opening\'s size is approximate; the 1928 photograph shows a deep arch with the original inner proscenium, covered in the 1950s (Rudisill 1986).'
OP, Z_OP = 7.2, 9.4
for k, (a0, a1) in enumerate(((-WI, -OP), (OP, WI))):
    box(C(f'pros-pier-{k + 1}'), STAGE, a0, a1, B_PROS, B_PROS + 0.8, Z_FRONT_ROW - 0.3, Z_ROOF, 'plaster', 'approximate', PROS, [NOM, T86])
box(C('pros-header'), STAGE, -OP, OP, B_PROS, B_PROS + 0.8, Z_OP, Z_CHAMBER, 'plaster', 'approximate', PROS, [NOM, T86])
box(C('pros-over-grille'), STAGE, -OP, OP, B_PROS, B_PROS + 0.8, Z_CHAMBER + 3.3, Z_ROOF, 'plaster', 'approximate', PROS, [NOM, T86])
INNER = 'The gilded frame of the original inner proscenium, shown in the 1928 photograph and covered in the 1950s by a CinemaScope screen (Rudisill 1986). Its size is approximate.'
for k, (a0, a1) in enumerate(((-OP - 0.45, -OP), (OP, OP + 0.45))):
    box(C(f'pros-frame-{k + 1}'), STAGE, a0, a1, B_PROS - 0.25, B_PROS, Z_STAGE, Z_OP + 0.45, 'gold', 'written', INNER, [T86])
box(C('pros-frame-top'), STAGE, -OP - 0.45, OP + 0.45, B_PROS - 0.25, B_PROS, Z_OP, Z_OP + 0.45, 'gold', 'written', INNER, [T86])
# The arch over the opening: the 1928 photograph (Rudisill 1986) shows the proscenium as a deep
# arch round the inner proscenium. Drawn as a gilded arch on the wall's face over the opening,
# with the plaster inside it; its rise and width are approximate.
ARCH = 'The proscenium arch over the inner proscenium, as the 1928 photograph shows it (Rudisill 1986: "the original inner proscenium which was covered in the 1950s with a Cinemascope screen"). Its rise and width are approximate.'
P.poly(C('pros-arch'), STAGE, [(-OP - 0.45, B_PROS - 0.3), (OP + 0.45, B_PROS - 0.3), (OP + 0.45, B_PROS - 0.26), (-OP - 0.45, B_PROS - 0.26)],
       Z_OP + 0.45, Z_CHAMBER, 'gold', 'written', ARCH, [T86], shape='arch')
P.poly(C('pros-arch-inner'), STAGE, [(-OP + 0.15, B_PROS - 0.34), (OP - 0.15, B_PROS - 0.34), (OP - 0.15, B_PROS - 0.3), (-OP + 0.15, B_PROS - 0.3)],
       Z_OP + 0.45, Z_CHAMBER - 0.3, 'plaster', 'approximate', ARCH, [T86])
GRILLE = 'The gold grille that runs along the entire length of the proscenium, concealing the organ chambers\' openings (nomination); the pipes speak through it (foundation). Drawn as bars; its height is approximate.'
n = 16
for i in range(n):
    a = -OP + (2 * OP) * (i + 0.5) / n
    box(C(f'grille-{i + 1}'), STAGE, a - 0.22, a + 0.22, B_PROS - 0.2, B_PROS + 0.1, Z_CHAMBER, Z_CHAMBER + 3.3, 'gold', 'written', GRILLE, [NOM, SRC['organ'], T86])
for k, z in enumerate((Z_CHAMBER, Z_CHAMBER + 3.0)):
    box(C(f'grille-rail-{k + 1}'), STAGE, -OP, OP, B_PROS - 0.25, B_PROS + 0.1, z, z + 0.3, 'gold', 'written', GRILLE, [NOM])
CURTAIN = 'The stage curtain, drawn open. Its 1928 color is not recorded: it is drawn in the seats\' red, as in 1986, when the new carpet was chosen "to match the seats and stage curtains" (Rudisill 1986); the nomination\'s scheme is amber and gold with red velvet accents. Its size is approximate.'
# Gathered open in folds either side, under a valance; the folds and their sizes are approximate.
for k, (a0, a1) in enumerate(((-OP, -4.4), (4.4, OP))):
    for j in range(4):
        f0 = a0 + (a1 - a0) * j / 4
        box(C(f'curtain-{k + 1}-{j + 1}'), STAGE, f0, f0 + (a1 - a0) / 4, B_PROS + 0.85 + 0.12 * (j % 2), B_PROS + 1.15 + 0.12 * (j % 2), Z_STAGE, Z_OP, 'seat', 'approximate', CURTAIN, [NOM, T86])
box(C('curtain-valance'), STAGE, -OP, OP, B_PROS + 0.85, B_PROS + 1.15, Z_OP - 1.9, Z_OP, 'seat', 'approximate', CURTAIN, [NOM, T86])
SCREEN = 'The screen, left blank: the opening program was a feature film and the organ (nomination; foundation). Its size and place are approximate.'
box(C('screen'), STAGE, -5.4, 5.4, B_PROS + 1.8, B_PROS + 1.9, 1.0, 7.0, 'screen', 'approximate', SCREEN, [NOM, SRC['history']])
for k, (a0, a1, z0, z1) in enumerate(((-5.8, -5.4, 0.6, 7.4), (5.4, 5.8, 0.6, 7.4), (-5.8, 5.8, 0.6, 1.0), (-5.8, 5.8, 7.0, 7.4))):
    box(C(f'screen-masking-{k + 1}'), STAGE, a0, a1, B_PROS + 1.8, B_PROS + 1.92, z0, z1, 'coal', 'approximate', 'The screen\'s masking, worked from the booth\'s switchboard (nomination). Approximate.', [NOM])

# ---- the organ: chambers over the stage, the console on its lift --------------------------------
CH = ('The organ\'s rooms, on the fourth floor over the stage, forty-odd steps up (Boomer, 2014): the general manager lists four, the blower, '
      'Main, Solo and relay rooms (Style Weekly, 2014), the foundation two pipe rooms over the center of the screen with the relays in a room of '
      'their own, the nomination three chambers; in some tellings the blower is in the basement. Drawn as four rooms side by side; the layout is approximate.')
CH_SRC = [STYLE, SRC['boomer2014'], SRC['organ'], NOM]
box(C('chamber-floor'), ORGAN, -WI, WI, B_PROS + 0.8, B_BACK, Z_CHAMBER - 0.3, Z_CHAMBER, 'floor', 'approximate', CH, CH_SRC)
for k, (a0, a1) in enumerate(((-9.6, -9.3), (2.9, 3.2), (9.3, 9.6))):
    box(C(f'chamber-wall-{k + 1}'), ORGAN, a0, a1, B_PROS + 0.8, B_BACK, Z_CHAMBER, Z_STAGE_ROOF - 0.4, 'plaster', 'approximate', CH, CH_SRC)
SHADES = 'The swell shutters at the front of the Main and Solo chambers, opened and closed like blinds from the console to make the pipes louder or softer (foundation: the sound leaves through shutters and a tone chute to the grille). Approximate.'
for i, a in enumerate([-9.15 + 0.6 * j for j in range(20) if -9.15 + 0.6 * j < 2.75] + [3.35 + 0.6 * j for j in range(10) if 3.35 + 0.6 * j < 9.15]):
    box(C(f'shutter-{i + 1}'), ORGAN, a, a + 0.12, B_PROS + 0.9, B_PROS + 1.2, Z_CHAMBER + 0.3, Z_CHAMBER + 3.0, 'wood', 'approximate', SHADES, [SRC['organ'], SRC['rfm2015']])
# Pipes in the Main and Solo chambers: ranks on their chests, each a row of pipes falling in height.
PIPES = 'Pipes standing in ranks on their wind chests: the Main chamber (foundation: strings, Tuba, Vox Humana, Tibia Plena and Diaphones) and the Solo. Wurlitzer Opus 1948 has seventeen ranks in all (nomination; foundation). Ranks, pipes and their sizes are drawn approximately.'
chest_b0, chest_b1 = B_PROS + 1.6, B_BACK - 0.3
for r, a in enumerate((1.9, 1.05, 0.25, -0.6, -1.5, -2.5, -3.6, -4.8, -6.0, -7.3, -8.5) + (4.1, 5.0, 6.0, 7.1, 8.3)):
    box(K(f'chest-{r + 1}'), ORGAN, a - 0.32, a + 0.32, chest_b0, chest_b1, Z_CHAMBER, Z_CHAMBER + 0.8, 'wood', 'approximate', PIPES, [SRC['organ'], NOM])
    tall = 4.6 - 0.3 * (r % 11)
    npipe = 9
    for i in range(npipe):
        b = chest_b0 + 0.18 + i * (chest_b1 - chest_b0 - 0.36) / (npipe - 1)
        h = min(tall * (1 - 0.075 * i) if r % 2 == 0 else tall * (0.55 + 0.05 * i), Z_STAGE_ROOF - 0.6 - Z_CHAMBER - 0.8)
        w = 0.2 if r % 11 < 3 else 0.14
        box(K(f'pipe-{r + 1}-{i + 1}'), ORGAN, a - w / 2, a + w / 2, b - w / 2, b + w / 2, Z_CHAMBER + 0.8, Z_CHAMBER + 0.8 + h, 'pipe', 'approximate', PIPES, [SRC['organ']])
RELAY = 'The relay room, where the console\'s wires meet the valves of the pipes; the relays "occupy their own room above the stage" (foundation). An eight-inch cable of thousands of wires runs to it from the console (RVA Mag, 2026). Placed at the west end; approximate.'
for k, b in enumerate((37.0, 38.2, 39.4)):
    box(K(f'relay-{k + 1}'), ORGAN, -11.9, -10.1, b, b + 0.8, Z_CHAMBER, Z_CHAMBER + 2.2, 'wood', 'approximate', RELAY, [SRC['organ'], SRC['rvamag2026']])
BLOWER = 'The organ\'s blower, which fills the chests with wind: in its own room up here by the general manager\'s list (Style Weekly, 2014), in the basement in other tellings. Drawn at the east end; approximate.'
box(K('blower'), 'Byrd Theatre: organ blower', 10.0, 11.8, 37.2, 39.6, Z_CHAMBER, Z_CHAMBER + 1.4, 'iron', 'approximate', BLOWER, [STYLE])
P.add(K('blower-motor'), 'Byrd Theatre: organ blower', F.ring([(10.9 + 0.45 * math.cos(2 * math.pi * k / 12), 36.85 + 0.3 * math.sin(2 * math.pi * k / 12)) for k in range(12)]),
      Z_CHAMBER, Z_CHAMBER + 0.9, 'iron', 'approximate', BLOWER, [STYLE], shape='revolve', levels=[[0, 1, 0], [0.9, 1, 0]])
# The cable from the console to the relay room: along under the stage and up the back wall.
CABLE = 'The cable from the console to the chambers: eight inches thick, thousands of wires (RVA Mag, 2026). Its route is not known: drawn under the stage and up the back wall, approximately.'
box(K('cable-1'), ORGAN, 0.75, 0.95, 34.75, B_BACK - 0.25, Z_STAGE - 0.55, Z_STAGE - 0.35, 'coal', 'approximate', CABLE, [SRC['rvamag2026']])
box(K('cable-2'), ORGAN, 0.75, 0.95, B_BACK - 0.25, B_BACK - 0.05, Z_STAGE - 0.55, Z_CHAMBER - 0.3, 'coal', 'approximate', CABLE, [SRC['rvamag2026']])
box(K('cable-0'), ORGAN, 0.75, 0.95, 33.4, 34.75, Z_SHAFT + 0.4, Z_SHAFT + 0.6, 'coal', 'approximate', CABLE, [SRC['rvamag2026']])
box(K('cable-0-up'), ORGAN, 0.75, 0.95, 34.55, 34.75, Z_SHAFT + 0.4, Z_STAGE - 0.35, 'coal', 'approximate', CABLE, [SRC['rvamag2026']])
# Percussion and effects over the screen (Richmond Family Magazine, 2015; Richmond magazine, 2021).
PERC = 'Percussion and effects over the screen, played from the console: drums, bells, a car horn, a bird whistle and tuned sleigh bells (Richmond Family Magazine, 2015; Richmond magazine, 2021). Their places and sizes are approximate.'
PERC_SRC = [SRC['rfm2015'], SRC['rm2021']]
box(C('perc-shelf'), ORGAN, -5.2, 5.2, 37.6, 38.9, 7.9, 8.1, 'wood', 'approximate', PERC, PERC_SRC)
for k, (a, r, h) in enumerate(((-4.2, 0.45, 0.5), (-3.0, 0.3, 0.35), (-2.2, 0.3, 0.35))):
    P.add(K(f'perc-drum-{k + 1}'), ORGAN, F.ring([(a + r * math.cos(2 * math.pi * j / 12), 38.25 + r * math.sin(2 * math.pi * j / 12)) for j in range(12)]),
          8.1, 8.1 + h, 'seat', 'approximate', PERC, PERC_SRC, shape='revolve', levels=[[0, 1, 0], [h, 1, 0]])
for k in range(8):
    box(K(f'perc-chime-{k + 1}'), ORGAN, -1.3 + 0.16 * k, -1.22 + 0.16 * k, 38.2, 38.28, 8.1 + 0.05 * k, 9.3, 'gold', 'approximate', PERC, PERC_SRC)
box(K('perc-bells'), ORGAN, 0.4, 1.4, 37.9, 38.6, 8.1, 8.5, 'gold', 'approximate', PERC, PERC_SRC)
box(K('perc-horn'), ORGAN, -0.2, 0.2, 38.1, 38.6, 8.1, 8.4, 'bronze', 'approximate', PERC, PERC_SRC)
CONSOLE = 'The mahogany console of Wurlitzer Opus 1948 (four manuals), on its original Peter Clark lift, raised from the open orchestra pit (Rudisill 1986 and its 1928 photograph; nomination: it "can be raised from the basement to stage level"). Shapes and sizes approximate.'
CB0, CB1 = B_PIT + 0.7, B_STAGE - 0.5
box(K('lift-screw'), ORGAN, -0.22, 0.22, 33.23, 33.67, Z_SHAFT, Z_STAGE - 0.65, 'iron', 'written', LIFT, [RFP, T86])
for k in range(int((Z_STAGE - 0.65 - Z_SHAFT) / 0.35)):
    z = Z_SHAFT + 0.2 + 0.35 * k
    box(K(f'lift-thread-{k + 1}'), ORGAN, -0.34, 0.34, 33.11, 33.79, z, z + 0.1, 'iron', 'approximate', LIFT, [RFP])
box(K('lift-nut'), ORGAN, -0.7, 0.7, 32.75, 34.15, Z_SHAFT, Z_SHAFT + 0.5, 'iron', 'approximate', LIFT, [RFP])
box(K('lift-platform'), ORGAN, -1.5, 1.5, CB0 - 0.2, CB1 + 0.2, Z_STAGE - 0.65, Z_STAGE - 0.4, 'gold', 'written', 'The elaborate fender round the top of the lift (Rudisill 1986, 1928 photograph). Approximate.', [T86])
box(K('console'), ORGAN, -1.05, 1.05, CB0 + 0.2, CB1 - 0.2, Z_STAGE - 0.4, Z_STAGE + 0.75, 'wood', 'written', CONSOLE, [T86, NOM])
box(K('console-keydesk'), ORGAN, -1.05, 1.05, CB0 + 0.2, CB0 + 0.85, Z_STAGE + 0.75, Z_STAGE + 1.35, 'wood', 'written', CONSOLE, [T86])
box(K('console-bench'), ORGAN, -0.6, 0.6, CB0 - 0.15, CB0 + 0.15, Z_STAGE - 0.4, Z_STAGE + 0.15, 'wood', 'approximate', CONSOLE, [T86])

# ---- the side walls inside: murals, pilasters, the opera boxes ----------------------------------
NICHE = 'One of the six murals in niches along the top of the auditorium\'s side walls (nomination), by Arthur Brounet (foundation): three a side. Not depicted: the panel is left plain. Places and sizes approximate, after the 1928 photograph.'
for k, b in enumerate((17.0, 21.5, 26.0)):
    P.poly(C(f'niche-{k + 1}-frame'), HOUSE, [(-WL, b - 1.5), (-WL + 0.12, b - 1.5), (-WL + 0.12, b + 1.5), (-WL, b + 1.5)], 7.8, 11.6, 'gold', 'written', NICHE, [NOM, T86])
    P.poly(C(f'niche-{k + 1}'), HOUSE, [(-WL + 0.12, b - 1.2), (-WL + 0.16, b - 1.2), (-WL + 0.16, b + 1.2), (-WL + 0.12, b + 1.2)], 8.1, 10.4, 'bronze', 'written', NICHE, [NOM])
    P.poly(C(f'niche-{k + 1}-arch'), HOUSE, [(-WL + 0.12, b + 1.2), (-WL + 0.12, b - 1.2), (-WL + 0.16, b - 1.2), (-WL + 0.16, b + 1.2)], 10.4, 11.3, 'bronze', 'written', NICHE, [NOM], shape='arch')
for k, b in enumerate((14.6, 19.25, 23.75, 28.25, 32.9)):
    box(C(f'pilaster-{k + 1}'), HOUSE, -WL, -WL + 0.25, b - 0.3, b + 0.3, 1.0, Z_CORNICE, 'gold', 'approximate', 'A gilded pilaster on the side wall, as the 1928 photograph shows the wall divided. Approximate.', [T86])
box(C('house-cornice'), HOUSE, -WL, -WL + 0.45, B_HOUSE, B_PROS, Z_CORNICE - 0.6, Z_CORNICE, 'gold', 'approximate', 'The cornice along the top of the side wall, under the ceiling. Approximate.', [T86])
box(C('house-dado'), HOUSE, -WL, -WL + 0.06, B_HOUSE, B_PROS, Z_FRONT_ROW - 0.3, 1.0, 'seat', 'approximate', 'The lower wall, hung in red (the nomination\'s amber, gold and red velvet scheme). Approximate.', [NOM])
BOXN = 'An opera-style box beside the stage, with a large mural behind it (nomination): a grand piano in one and a harp in the other, played from the organ console (nomination; Rudisill 1986). The harp does not play: a marimba below it makes the harp\'s sound (Richmond magazine, 2021; Richmond Family Magazine, 2015). Which box held which is not known; drawn approximately, the harp on this side.'
BOX_SRC = [NOM, T86, SRC['rm2021'], SRC['rfm2015']]
BB0, BB1 = 30.2, 33.8
box(C('box-west-floor'), HOUSE, -WL, -10.2, BB0, BB1, 3.6, 3.9, 'floor', 'approximate', BOXN, [NOM, T86])
box(C('box-west-front'), HOUSE, -10.4, -10.2, BB0, BB1, 3.9, 5.0, 'gold', 'written', BOXN, [NOM, T86])
box(C('box-west-mural'), HOUSE, -WL, -WL + 0.06, BB0 + 0.2, BB1 - 0.2, 4.4, 8.0, 'bronze', 'written', BOXN, [NOM])
box(C('box-east-floor'), HOUSE, 10.2, WI, BB0, BB1, 3.6, 3.9, 'floor', 'approximate', BOXN, [NOM, T86])
box(C('box-east-front'), HOUSE, 10.2, 10.4, BB0, BB1, 3.9, 5.0, 'gold', 'written', BOXN, [NOM, T86])
box(K('piano'), 'Byrd Theatre: the grand piano', 10.6, 11.9, BB0 + 0.6, BB0 + 2.4, 3.9, 4.95, 'coal', 'written', BOXN, BOX_SRC)
box(K('piano-lid'), 'Byrd Theatre: the grand piano', 11.8, 11.9, BB0 + 0.6, BB0 + 2.1, 4.95, 5.9, 'coal', 'approximate', BOXN, BOX_SRC)
# The harp (a Browne & Buckwell, Richmond magazine 2021), in the west box: its column, base, neck
# and a soundbox slanting up from the base, drawn in steps.
HARP = BOXN + ' The harp is a Browne & Buckwell, delivered by the Corley Music Co. from Grace Street (Richmond magazine, 2021).'
HB = BB0 + 1.2
box(K('harp-base'), 'Byrd Theatre: the harp', -11.25, -10.8, HB - 0.1, HB + 1.0, 3.9, 4.05, 'gold', 'written', HARP, BOX_SRC)
box(K('harp-column'), 'Byrd Theatre: the harp', -11.1, -10.95, HB - 0.05, HB + 0.07, 4.05, 5.75, 'gold', 'written', HARP, BOX_SRC)
box(K('harp-neck'), 'Byrd Theatre: the harp', -11.08, -10.97, HB - 0.05, HB + 0.85, 5.6, 5.75, 'gold', 'written', HARP, BOX_SRC)
for i in range(6):
    b = HB + 0.82 - 0.13 * i
    box(K(f'harp-soundbox-{i + 1}'), 'Byrd Theatre: the harp', -11.12, -10.93, b - 0.09, b + 0.09, 4.05 + 0.26 * i, 4.05 + 0.26 * (i + 1), 'gold', 'written', HARP, BOX_SRC)
MARIMBA = BOXN + ' The marimba\'s place below the box is approximate.'
box(K('marimba-frame'), 'Byrd Theatre: marimba', -11.9, -10.6, BB0 + 0.4, BB1 - 0.4, 2.7, 2.85, 'wood', 'written', MARIMBA, BOX_SRC)
for i in range(12):
    b = BB0 + 0.5 + i * (BB1 - BB0 - 1.0) / 12
    box(K(f'marimba-bar-{i + 1}'), 'Byrd Theatre: marimba', -11.8 + 0.03 * i, -10.7, b, b + 0.17, 2.85, 2.92, 'wood', 'approximate', MARIMBA, BOX_SRC)
    box(K(f'marimba-tube-{i + 1}'), 'Byrd Theatre: marimba', -11.0, -10.9, b + 0.04, b + 0.13, 2.7 - 0.6 + 0.03 * i, 2.7, 'pipe', 'approximate', MARIMBA, BOX_SRC)

# ---- the balcony and the booth ---------------------------------------------------------------
BAL = 'The balcony, an integral part of the theatre\'s visual effect (nomination); today 476 seats (Wikipedia). Its depth, rake and rows are approximate; the 1928 photograph shows its curved front, drawn straight.'
for k in range(BAL_ROWS):
    b1 = BAL_FRONT - k * 0.9
    b0 = b1 - 0.9
    z = BAL_Z0 + k * BAL_RISE
    box(C(f'bal-tier-{k + 1}'), HOUSE, -WI, WI, b0, b1, z - BAL_RISE - 0.3, z, 'floor', 'approximate', BAL, [NOM, SRC['wiki']])
    for j, (a0, a1) in enumerate(SECTIONS):
        seats(f'bal-seats-{k + 1}-{j + 1}', HOUSE, a0, a1, b0 + 0.25, b0 + 0.77, z, z + 0.85, SEATS.replace('in a center section between two aisles and two side sections (the foundation speaks of the main auditorium\'s center section)', 'in three sections like the floor\'s'), [NOM, SRC['seats2025']])
box(C('bal-front'), HOUSE, -WI, WI, BAL_FRONT, BAL_FRONT + 0.3, BAL_Z0 - 0.9, BAL_Z0 + 1.0, 'gold', 'approximate', BAL, [NOM, T86])
BOOTH = 'The projection booth, "at the rear of the lobby" (nomination), here behind the balcony\'s last row: two 35 mm Simplex projectors and Vitaphone sound (foundation; nomination), and the main switchboard that ran all the lighting, the curtain and the screen masking (nomination). Its size is approximate.'
box(C('booth-floor'), 'Byrd Theatre: projection booth', -6.0, 6.0, B_VEST + 1.0, B_BOOTH, Z_BOOTH - 0.3, Z_BOOTH, 'floor', 'approximate', BOOTH, [NOM, SRC['about']])
box(C('booth-front-low'), 'Byrd Theatre: projection booth', -6.0, 6.0, B_BOOTH - 0.3, B_BOOTH, Z_BOOTH, Z_BOOTH + 1.1, 'plaster', 'approximate', BOOTH, [NOM])
for k, (a0, a1) in enumerate(((-6.0, -2.3), (-1.3, 0.6), (1.6, 6.0))):
    box(C(f'booth-front-{k + 1}'), 'Byrd Theatre: projection booth', a0, a1, B_BOOTH - 0.3, B_BOOTH, Z_BOOTH + 1.1, Z_CEIL, 'plaster', 'approximate', BOOTH, [NOM])
for k, (a0, a1) in enumerate(((-2.3, -1.3), (0.6, 1.6))):
    box(C(f'booth-port-{k + 1}'), 'Byrd Theatre: projection booth', a0, a1, B_BOOTH - 0.3, B_BOOTH, Z_BOOTH + 1.6, Z_CEIL, 'plaster', 'approximate', BOOTH, [NOM])
box(C('booth-ceiling'), 'Byrd Theatre: projection booth', -6.0, 6.0, B_VEST + 1.0, B_BOOTH, Z_CEIL, Z_CEIL + 0.3, 'plaster', 'approximate', BOOTH, [NOM])
box(C('booth-back'), 'Byrd Theatre: projection booth', -6.0, 6.0, B_VEST + 1.0, B_VEST + 1.3, Z_BOOTH, Z_CEIL, 'plaster', 'approximate', BOOTH, [NOM])
box(C('booth-side'), 'Byrd Theatre: projection booth', -6.3, -6.0, B_VEST + 1.0, B_BOOTH, Z_BOOTH - 0.3, Z_CEIL + 0.3, 'plaster', 'approximate', BOOTH, [NOM])
for k, a in enumerate((-1.8, 1.1)):
    box(K(f'projector-{k + 1}'), 'Byrd Theatre: Simplex projector', a - 0.35, a + 0.35, B_BOOTH - 1.6, B_BOOTH - 0.5, Z_BOOTH, Z_BOOTH + 1.75, 'iron', 'written', BOOTH, [SRC['about']])
box(K('switchboard'), 'Byrd Theatre: switchboard', -5.6, -3.4, B_VEST + 1.4, B_VEST + 1.9, Z_BOOTH, Z_BOOTH + 2.2, 'iron', 'written', BOOTH, [NOM])

# ---- the ceiling and the dome, the chandelier ------------------------------------------------
CEIL = 'The auditorium\'s ceiling round the dome. Its height is approximate; the 1928 photograph shows a coffered ceiling with the dome at its center.'
DB0, DB1 = DOME_B - DOME_R, DOME_B + DOME_R
for k, (a0, a1, b0, b1) in enumerate(((-WI, -DOME_R, B_BOOTH, B_PROS), (DOME_R, WI, B_BOOTH, B_PROS), (-DOME_R, DOME_R, B_BOOTH, DB0), (-DOME_R, DOME_R, DB1, B_PROS))):
    box(C(f'ceiling-{k + 1}'), HOUSE, a0, a1, b0, b1, Z_CEIL, Z_CEIL + 0.4, 'plaster', 'approximate', CEIL, [T86])
# The corners between the square well and the dome's round edge: one convex piece per edge.
NSEG = 24
circle = [(DOME_R * math.cos(2 * math.pi * (k + 0.5) / NSEG), DOME_B + DOME_R * math.sin(2 * math.pi * (k + 0.5) / NSEG)) for k in range(NSEG)]


def to_square(p):
    a, b = p[0], p[1] - DOME_B
    s = DOME_R / max(abs(a), abs(b))
    return (a * s, DOME_B + b * s)


for k in range(NSEG):
    p, q = circle[k], circle[(k + 1) % NSEG]
    pts = [p, q, to_square(q)]
    # The square's corner between the two rays, if one lies between them.
    for ca, cb in ((DOME_R, DOME_R), (-DOME_R, DOME_R), (-DOME_R, -DOME_R), (DOME_R, -DOME_R)):
        ang = math.atan2(cb, ca) % (2 * math.pi)
        a0 = math.atan2(p[1] - DOME_B, p[0]) % (2 * math.pi)
        a1 = math.atan2(q[1] - DOME_B, q[0]) % (2 * math.pi)
        if a0 < ang < a1 or (a1 < a0 and (ang > a0 or ang < a1)):
            pts.append((ca, DOME_B + cb))
    pts.append(to_square(p))
    P.poly(C(f'ceiling-corner-{k + 1}'), HOUSE, pts, Z_CEIL, Z_CEIL + 0.4, 'plaster', 'approximate', CEIL, [T86])
DOME = 'The dome over the auditorium, with the great chandelier at its crown (nomination); a shell drawn shallow, as the 1928 photograph shows it. Its size is approximate.'
levels = []
for i in range(9):
    t = i / 8
    o = math.sqrt(max(0.0, 1 - (t * 0.985) ** 2))
    levels.append([round(DOME_RISE * t, 3), round(max(o, 0.17), 4), round(max(o - 0.4 / DOME_R, 0.12), 4)])
levels.append([round(DOME_RISE + 0.35, 3), 0.17, 0.0])
P.add(C('dome'), HOUSE, F.ring([(DOME_R * math.cos(2 * math.pi * (k + 0.5) / NSEG), DOME_B + DOME_R * math.sin(2 * math.pi * (k + 0.5) / NSEG)) for k in range(NSEG)]),
      Z_CEIL, Z_CEIL + DOME_RISE + 0.35, 'roof', 'approximate', DOME, [NOM, T86], shape='revolve', levels=levels)
CHAND = 'The great chandelier in the dome: four thousand hand-cut crystals and three hundred bulbs in four colors, some two tons, lowered for cleaning and relamping (nomination). The foundation gives about 5,000 crystals, 500 bulbs, 2½ tons, 18 ft tall and 10 ft across; drawn 18 ft tall and 10 ft across.'
CH_R, CH_H = 1.52, 5.49
ch_top = Z_CEIL + DOME_RISE
P.add(K('chandelier'), 'Byrd Theatre: the great chandelier', F.ring([(CH_R * math.cos(2 * math.pi * (k + 0.5) / 12), DOME_B + CH_R * math.sin(2 * math.pi * (k + 0.5) / 12)) for k in range(12)]),
      ch_top - CH_H, ch_top, 'lamp', 'written', CHAND, [NOM, SRC['about']], shape='revolve',
      levels=[[0, 0.04, 0], [0.5, 0.42, 0], [1.3, 0.62, 0], [1.35, 0.95, 0], [1.9, 1.0, 0], [2.0, 0.7, 0], [2.6, 0.78, 0], [2.65, 0.5, 0], [3.2, 0.42, 0], [3.3, 0.05, 0], [CH_H, 0.05, 0]])

# ---- the air tunnels under the floor --------------------------------------------------------------
TUN = 'One of three concrete tunnels beneath the floor through which the Carrier air-conditioning drew its cooled air (foundation, About). Their routes and sizes are not known: drawn running under the orchestra floor, approximately.'
Z_T0, Z_T1 = -3.0, Z_FILL - 0.25        # the tunnels' floor and roof (approximate)
for k, (a0, a1) in enumerate(((-9.0, -7.4), (-4.6, -3.0), (-0.4, 1.2))):
    box(C(f'tunnel-{k + 1}-floor'), 'Byrd Theatre: air tunnel', a0 - 0.25, a1 + 0.25, B_ROW0, B_PIT, Z_T0 - 0.25, Z_T0, 'stone', 'approximate', TUN, [SRC['about']])
    box(C(f'tunnel-{k + 1}-roof'), 'Byrd Theatre: air tunnel', a0 - 0.25, a1 + 0.25, B_ROW0, B_PIT, Z_T1, Z_T1 + 0.25, 'stone', 'approximate', TUN, [SRC['about']])
    # The tunnel nearest the cut is drawn open on its side toward it, so it shows in the cut.
    for j, (w0, w1) in enumerate(((a0 - 0.25, a0),) + (((a1, a1 + 0.25),) if k < 2 else ())):
        box(C(f'tunnel-{k + 1}-wall-{j + 1}'), 'Byrd Theatre: air tunnel', w0, w1, B_ROW0, B_PIT, Z_T0, Z_T1, 'stone', 'approximate', TUN, [SRC['about']])

RULES = []
YEAR_BUILT = 'https://services1.arcgis.com/k3vhq11XkBNeeOfM/ArcGIS/rest/services/Year_of_Construction/FeatureServer/0'

# ---- the history file -----------------------------------------------------------------------
features = P.features
history = {
    'title': 'The Byrd Theatre on its opening night, Christmas Eve 1928',
    'method': 'The theatre is modeled from curated parts inside the city lot of the 1979 National Register nomination (about 84 x 135 ft). No plan, section or seating chart was found, so rooms are placed from written descriptions (the nomination; Theatre Organ, 1986; the Byrd Theatre Foundation) and photographs (the 1928 interior views in Theatre Organ; the front c. 1929). Every part names its sources and how it is known. West Cary Street, the neighbors and the ground are today\'s, from OpenStreetMap and the USGS 3DEP lidar; a neighbor stands in 1928 only where the assessor\'s year built puts it up by then.',
    'present': 2026,
    'about': 'The Byrd Theatre opened on Christmas Eve 1928, "a great civic event" (nomination), with a feature film and the Wurlitzer organ.',
    'epochs': [{'year': 1928, 'title': 'Opening night, Christmas Eve 1928', 'note': 'December 24, 1928: the theatre\'s grand opening.'}],
    'features': features,
    'rules': RULES,
    'dates': [{'id': 'w327377540', 'name': 'Byrd Theatre', 'year': 2026, 'source': SRC['osm'],
               'note': 'Today\'s outline of the theatre is drawn only in today\'s scene; in 1928 the theatre is drawn from its curated parts.'}]
             + [{'id': w, 'name': f'{n} West Cary Street', 'year': 1923, 'source': YEAR_BUILT,
                 'note': 'One of the one-storey shops west of the theatre: the assessor dates their parcel 1923, and the c. 1929 photograph of the front shows a one-storey row of shops on that side. The parcel holds too many buildings for the year to be given to each by the general rule, so it is given here.'}
                for w, n in (('w327377551', 2916), ('w327377552', 2920))],
}
OUT.write_text(json.dumps(history, indent=1, ensure_ascii=False) + '\n')

# The share of parts whose own confidence is approximate (each piece counted once).
conf = [f['confidence'] for f in features if f['kind'] == 'landmark' and f.get('only') != 'whole']
share = sum(c == 'approximate' for c in conf) / len(conf)
print(f'{OUT.relative_to(ROOT)}: {len(features)} features; {len(conf)} cutaway parts, {share:.0%} approximate')
# Where things are, for the region and the sheet.
print('origin', F.lonlat(0, 0), 'cut through', F.lonlat(CUT_A, 0), 'b bearing', F.b_bearing, 'datum', DATUM)
print('B_PIT', round(B_PIT, 2), 'Z_FRONT_ROW', round(Z_FRONT_ROW, 3), 'B_BOOTH', round(B_BOOTH, 2), 'Z_BOOTH', Z_BOOTH)
