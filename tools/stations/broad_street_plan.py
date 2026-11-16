"""Broad Street Station's interior, traced from the 1919 plates, for cutaways.

Imported by broad_street.py, which passes its frame and helpers. Every part here is drawn only
in cutaway views (`only: 'cutaway'`); whole views keep the station's massing. Each part names
its sources and says how it is known (`confidence`):

  drawn        traced from a plate (a plan or a section) or a survey map;
  written      placed from a written account;
  approximate  inferred: no drawing or account gives its place or size.

Plan positions come from Plate 15, the first-floor plan (The American Architect, July 9, 1919),
read in plate pixels at 300 dpi and fitted to the model's (a, b) frame: the plate's x runs with
a (its right-hand wing, holding the Colored Waiting Room, is +a, the bearing-130.8° side), its
y against b (the portico, at the bottom of the sheet, faces Broad Street). The scale is the
published frontage: 240 ft across the outer walls, 725 to 2572 px. The axis (section line C-C)
is at x = 1650, the model's a = -2; the front wall (y = 1600) is the model's b = -20. The
published depth, 118 ft, then falls on the wings' back walls (y = 712) within 3 ft.

Heights come from Plates 17 and 18 (sections A-A, B-B and C-C). Their figures are illegible, so
they are scaled from the drawings: section C-C's length is fitted to the plan's depth (0.0373 m
a plate pixel), which also puts the dome's crown 100 ft above the first floor, as published.
The first floor's elevation is approximate: no figure is legible. It is set 1.7 m over today's
ground at the portico, which gives the concourse deck, at the same level, room over a steam engine
on today's ground where the tracks lay (5.9 m under its deck).
"""

import math

K = 73.152 / (2572 - 725)       # meters per plate pixel (240 ft across the outer walls)
XC, YF = 1650, 1600             # the axis and the front wall, in plate pixels
FF = 67.4                       # first floor, meters above sea level (approximate; see below)
# Levels above the first floor, scaled from sections A-A, B-B and C-C (Plates 17, 18).
BSMT, L2, L3, L4 = -5.1, 4.1, 7.3, 10.4
WING_TOP = 13.6                 # wing roof 13.0 and its parapet
FRONT_TOP = 17.2                # the front block over the vestibule
CORNICE, LUNETTE, ATTIC = 12.9, 20.5, 21.3
DOME_BASE, DOME_STEP, DOME_TOP = 21.8, 24.4, 30.8
CEIL_TOP = 27.3                 # the hall's ceiling at its crown

PDF = 'https://www.usmodernist.org/AMAR/AMAR-1919-07-09.pdf'
P15, P16, P17, P18 = (f'{PDF}#page={p}' for p in (27, 29, 31, 33))
AMAR = f'{PDF}#page=5'
ARCHIPEDIA = 'https://sah-archipedia.org/node/20518'
POSTCARD = 'https://commons.wikimedia.org/wiki/File:New_Union_Station,_Richmond,_Va._(16649844960).jpg'
NR = 'https://www.dhr.virginia.gov/VLR_to_transfer/PDFNoms/127-0226_Broad_Street_Station_1972_Final_Nomination.pdf'

PLAN = 'Traced from the first-floor plan (Plate 15, The American Architect, July 9, 1919).'
SECT = 'Heights scaled from sections A-A, B-B and C-C (Plates 17 and 18); their figures are illegible.'


def build(part, ab, st, to_ab, crossing, platforms, lonlat):
    """Add the cutaway parts with `part` (broad_street.py's), in its frames `ab` and `st`; return the stairs."""

    def P(x, y):
        return ab(-2 + (x - XC) * K, -20 + (YF - y) * K)

    def LL(pts):
        return [lonlat(q) for q in pts]

    def rect(x0, y0, x1, y1):
        return LL([P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)])

    def wall(p, q, t):
        """A wall on the segment p–q (plate px), t px thick, centered on it."""
        dx, dy = q[0] - p[0], q[1] - p[1]
        l = math.hypot(dx, dy)
        nx, ny = -dy / l * t / 2, dx / l * t / 2
        return LL([P(p[0] + nx, p[1] + ny), P(q[0] + nx, q[1] + ny), P(q[0] - nx, q[1] - ny), P(p[0] - nx, p[1] - ny)])

    def disc(x, y, r, n=12):
        return LL([P(x + r * math.cos(2 * math.pi * k / n + math.pi / n), y + r * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)])

    def cp(id_, name, ring, z0, z1, tone, conf, note, sources, only='cutaway', **kw):
        """A part from z0 to z1 meters above the first floor: by default drawn in cutaways only
        (`bss-c-…`); with only=None, in every view (`bss-…`); with 'whole', in whole views."""
        pid = f'bss-c-{id_}' if only == 'cutaway' else f'bss-{id_}'
        part(pid, name, ring, round(z1 - z0, 3), tone, note, sources, only=only, elevation=round(FF + z0, 3), confidence=conf, **kw)

    HALL = 'Broad Street Station: White Waiting Room'
    WING = 'Broad Street Station: east wing'
    plan_src = [P15]
    sect_src = [P15, P17, P18]
    PLAN_HT = PLAN + ' Height approximate.'

    # ---- the portico ---------------------------------------------------------------------------
    POR = 'Broad Street Station portico'
    part('bss-porch', POR, rect(1100, 1600, 2190, 1880), 1.0, 'stone',
         'The portico\'s floor, raised over the forecourt to the first floor. Its extent is from the plan; its height is the first floor\'s (approximate).', plan_src,
         upTo=FF, confidence='drawn')
    for k, x in enumerate((1387, 1485, 1586, 1698, 1800, 1898)):
        cp(f'column-{k + 1}', POR, disc(x, 1748, 23), 0, 11.8, 'stone', 'drawn',
           'One of the portico\'s six columns. Its place and size are from the plan; its height is scaled from the earlier postcard model (approximate).', plan_src + [ARCHIPEDIA], only=None)
    for k, x in enumerate((1276, 2007)):
        cp(f'portico-pier-{k + 1}', POR, rect(x - 20, 1728, x + 20, 1768), 0, 11.8, 'stone', 'drawn',
           'A square end pier of the colonnade. Place from the plan; height approximate.', plan_src, only=None)
    for k, x in enumerate((1133, 2146)):
        cp(f'pedestal-{k + 1}', POR, rect(x - 25, 1723, x + 25, 1773), 0, 3.0, 'stone', 'drawn',
           'A pedestal at the corner of the portico terrace. Place from the plan; height approximate.', plan_src, only=None)
    cp('entablature', POR, rect(1256, 1600, 2027, 1775), 11.8, 14.4, 'stone', 'approximate',
       'The entablature over the colonnade, from pier to pier. Extent from the plan; height approximate.', plan_src, only=None)

    # ---- the massing, for whole views ---------------------------------------------------------
    MASS = 'Broad Street Station (head house)'
    mass_note = ' Drawn whole in views without a cutaway. ' + PLAN + ' ' + SECT
    for id_, name, ring, top, note in [
        ('wing-w', MASS, LL([P(725, 1600), P(1305, 1600), P(1305, 755), P(1000, 755), P(725, 880)]), WING_TOP, 'The west wing: the lunch room, dining room and kitchen, and the white men\'s rooms.'),
        ('wing-e', MASS, LL([P(1995, 1600), P(2572, 1600), P(2572, 838), P(2330, 712), P(1995, 712)]), WING_TOP, 'The east wing: the Colored Waiting Room and its rooms, baggage and parcel check, stores.'),
        ('center', MASS, rect(1305, 1471, 1995, 1600), FRONT_TOP, 'The front block over Vestibule No. 1 and the entrance halls, with offices above.'),
        ('attic', MASS, rect(1305, 846, 1995, 1471), ATTIC, 'The block of the White Waiting Room, up to the cornice the dome stands on.'),
        ('vestibule', MASS, rect(1440, 700, 1860, 846), WING_TOP, 'The vestibule to the concourse.'),
        ('vestibule-west', MASS, rect(1305, 755, 1440, 846), WING_TOP, 'The rooms beside the vestibule to the concourse.'),
        ('passage-1-mass', MASS, rect(1160, 575, 1440, 755), 6.5, 'Enclosed Concourse Passage No. 1.'),
        ('passage-2-mass', MASS, rect(1860, 575, 2330, 712), 6.5, 'Enclosed Concourse Passage No. 2.'),
    ]:
        part(f'bss-{id_}', name, ring, top, 'stone', note + mass_note, sect_src, only='whole', upTo=FF + top, confidence='drawn')
    for k, (x0, x1) in enumerate(((725, 1305), (1995, 2572))):
        cp(f'marquee-{k + 1}', MASS, rect(x0, 1600, x1, 1690), 4.2, 4.7, 'iron', 'approximate',
           'A cast-iron and glass marquee over the wing\'s doors, from period postcards; the plan\'s wings, its size approximate.', [P15, POSTCARD], only=None)

    # ---- floors ---------------------------------------------------------------------------
    for k, (ring, what) in enumerate([
        (rect(1305, 880, 2549, 1441), 'the hall and the east wing'),
        (rect(1494, 1441, 2549, 1577), 'the vestibule and the east wing\'s front'),
        (LL([P(1860, 880), P(2549, 880), P(2549, 848), P(2326, 735), P(1860, 735)]), 'the east wing\'s back, with its cut corner'),
        (rect(1305, 755, 1463, 880), 'the rooms beside the concourse vestibule'),
        (rect(1463, 700, 1837, 880), 'the concourse vestibule'),
        (rect(1837, 735, 1860, 880), 'the concourse vestibule\'s east side'),
        (rect(1860, 598, 2307, 712), 'Enclosed Concourse Passage No. 2'),
    ]):
        cp(f'floor-{k + 1}', 'Broad Street Station: first floor', ring, -0.5, 0, 'floor', 'drawn',
           f'The first floor of {what}. {PLAN} Thickness approximate.', plan_src)
    cp('basement-floor', 'Broad Street Station: basement', rect(725, 712, 2572, 1600), BSMT - 0.3, BSMT, 'floor', 'drawn',
       'The basement floor, under the whole building. Its depth is scaled from sections A-A and C-C; what the basement held (baggage, mail, the heating plant, the trainmen\'s rooms, per the 1919 article) is not drawn.', sect_src + [AMAR])
    # The basement on piers, as the sections draw it; the grid is approximate.
    n = 0
    for x in range(800, 2560, 140):
        for y in range(780, 1600, 140):
            if 1440 <= x <= 1860 and y < 880:
                continue
            n += 1
            cp(f'basement-pier-{n}', 'Broad Street Station: basement pier', rect(x - 9, y - 9, x + 9, y + 9), BSMT, -0.5, 'stone', 'approximate',
               'A pier of the basement. Sections A-A, B-B and C-C draw the basement on piers; their spacing here is approximate.', sect_src)

    # ---- outer walls ------------------------------------------------------------------------
    T = 23  # 0.9 m
    outer = [
        ('front-east', (1995, 1600 - T / 2), (2572, 1600 - T / 2), WING_TOP),
        ('east', (2572 - T / 2, 1600), (2572 - T / 2, 838), WING_TOP),
        ('east-corner', (2572 - T / 2, 838), (2330, 712 + T / 2), WING_TOP),
        ('east-back', (2330, 712 + T / 2), (1860, 712 + T / 2), WING_TOP),
        ('passage-2-back', (1860, 575 + T / 2), (2330, 575 + T / 2), 6.5),
        ('passage-2-end', (2330 - T / 2, 575), (2330 - T / 2, 712), 6.5),
    ]
    for id_, p, q, top in outer:
        cp(f'wall-{id_}', 'Broad Street Station: outer wall', wall(p, q, T), BSMT, top, 'stone', 'drawn',
           f'An outer wall. {PLAN} {SECT} Wall thickness approximate.', sect_src)
    # The west wing, its passage and the entrance hall beside the vestibule stand whole behind
    # the cut, as solid blocks: nothing of their insides shows.
    cp('west-wing', 'Broad Street Station: west wing', LL([P(725, 1600), P(1305, 1600), P(1305, 755), P(1000, 755), P(725, 880)]), BSMT, WING_TOP, 'stone', 'drawn',
       'The west wing (the lunch room, dining room and kitchen, and the white men\'s rooms), drawn as a solid block: the cut does not open it. ' + PLAN + ' ' + SECT, sect_src)
    cp('passage-1', 'Broad Street Station: Enclosed Concourse Passage No. 1', rect(1160, 575, 1440, 755), -0.5, 6.5, 'stone', 'drawn',
       'Enclosed Concourse Passage No. 1, as a solid block. ' + PLAN_HT, plan_src)
    cp('entrance-hall-1', 'Broad Street Station: Entrance Hall No. 1', rect(1305, 1471, 1494, 1577), BSMT, FRONT_TOP, 'stone', 'drawn',
       'Entrance Hall No. 1, with its stair and elevator to the offices, as a solid block. ' + PLAN + ' ' + SECT, sect_src)

    # ---- the front block over the vestibule ----------------------------------------------------
    for k, (x0, x1) in enumerate([(1305, 1535), (1585, 1625), (1675, 1715), (1765, 1995)]):
        cp(f'front-wall-{k + 1}', 'Broad Street Station: front wall', rect(x0, 1577, x1, 1600), BSMT, FRONT_TOP, 'stone', 'drawn',
           'The front wall behind the portico, between its doors. ' + PLAN + ' ' + SECT, sect_src)
    for k, (x0, x1) in enumerate([(1535, 1585), (1625, 1675), (1715, 1765)]):
        cp(f'front-door-{k + 1}', 'Broad Street Station: front doors', rect(x0, 1577, x1, 1600), 4.5, FRONT_TOP, 'stone', 'drawn',
           'The wall over one of the doors from the portico into Vestibule No. 1. Doors from the plan; their height is approximate.', sect_src)
    for x in (1500, 1800):
        cp(f'vestibule-1-wall-{x}', 'Broad Street Station: Vestibule No. 1', rect(x - 6, 1471, x + 6, 1577), 0, FRONT_TOP - 0.6, 'plaster', 'drawn',
           'A side wall of Vestibule No. 1, between it and an entrance hall. ' + PLAN + ' ' + SECT, sect_src)
    for k, x in enumerate((1600, 1700)):
        cp(f'vestibule-1-column-{k + 1}', 'Broad Street Station: Vestibule No. 1', disc(x, 1515, 22), 0, L2, 'stone', 'drawn',
           'One of the two columns of Vestibule No. 1. ' + PLAN_HT, plan_src)
    for k, z in enumerate((L2, L3, L4)):
        cp(f'front-floor-{k + 2}', 'Broad Street Station: offices over the vestibule', rect(1506, 1471, 1794, 1577), z - 0.4, z, 'floor', 'drawn',
           ('The bridge passage over the vestibule (second-floor plan, Plate 16).' if k == 0 else 'An office floor over the vestibule.') + ' ' + SECT, [P16, P17, P18])
    cp('front-roof', 'Broad Street Station: roof over the vestibule', rect(1494, 1471, 1806, 1577), FRONT_TOP - 0.6, FRONT_TOP, 'stone', 'approximate',
       'The roof over the front block. Height scaled from section C-C; its build-up is approximate.', sect_src)
    cp('entrance-hall-2-wall', 'Broad Street Station: Entrance Hall No. 2', wall((1960, 1441), (1960, 1577), 12), 0, L2, 'plaster', 'drawn',
       'The wall between Entrance Hall No. 2 and the White Women\'s room. ' + PLAN_HT, plan_src)
    cp('entrance-hall-2-stair', 'Broad Street Station: Staircase No. 2', LL([P(1835, 1580), P(1880, 1580), P(1880, 1470), P(1835, 1470)]), 0, L2, 'stone', 'drawn',
       'Staircase No. 2, up to the offices. Its place is from the plan; drawn as a straight flight (approximate).', plan_src, shape='stair', steps=14)
    cp('entrance-hall-2-elevator', 'Broad Street Station: elevator', rect(1895, 1495, 1945, 1550), 0, L2, 'plaster', 'drawn',
       'The elevator in Entrance Hall No. 2. ' + PLAN_HT, plan_src)

    # ---- the White Waiting Room ----------------------------------------------------------------
    # Inner faces x 1335–1955, y 876–1441, the corners cut 110 px; walls 30 px (1.2 m).
    X0, X1, Y0, Y1, C, W = 1335, 1955, 876, 1441, 110, 30
    hall_note = 'The White Waiting Room. ' + PLAN + ' ' + SECT
    for k, (p, q) in enumerate([((X0, Y0 + C), (X0 + C, Y0)), ((X1 - C, Y0), (X1, Y0 + C)), ((X1, Y1 - C), (X1 - C, Y1)), ((X0 + C, Y1), (X0, Y1 - C))]):
        # The corners: a diagonal pier, outside the inner face.
        cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
        dx, dy = q[0] - p[0], q[1] - p[1]
        l = math.hypot(dx, dy)
        nx, ny = dy / l, -dx / l
        if nx * ((p[0] + q[0]) / 2 - cx) + ny * ((p[1] + q[1]) / 2 - cy) < 0:
            nx, ny = -nx, -ny
        ring = LL([P(*p), P(*q), P(q[0] + nx * W, q[1] + ny * W), P(p[0] + nx * W, p[1] + ny * W)])
        cp(f'hall-corner-{k + 1}', HALL, ring, 0, ATTIC, 'plaster', 'drawn', 'A cut corner of the White Waiting Room: the octagon of the plan. ' + PLAN + ' ' + SECT, sect_src)
    # The two long sides open under their great arches to the vestibules and counters beside the
    # hall: their walls start at the cornice.
    for side, x0, x1 in (('west', X0 - W, X0), ('east', X1, X1 + W)):
        cp(f'hall-{side}-arch', HALL, rect(x0, Y0 + C, x1, Y1 - C), CORNICE, ATTIC, 'plaster', 'drawn',
           'The wall over the great arch on this side of the hall, with its lunette window; below it the hall opens to the vestibules and counters. ' + PLAN + ' ' + SECT, sect_src)
    # The two ends: a door on the axis into each vestibule, the lunette over it.
    for end, y0, y1 in (('back', Y0 - W, Y0), ('front', Y1, Y1 + W)):
        for k, (x0, x1) in enumerate([(X0 + C, 1590), (1710, X1 - C)]):
            cp(f'hall-{end}-wall-{k + 1}', HALL, rect(x0, y0, x1, y1), 0, ATTIC, 'plaster', 'drawn', hall_note + ' Doors approximate.', sect_src)
        cp(f'hall-{end}-door-head', HALL, rect(1590, y0, 1710, y1), 6.0, CORNICE, 'plaster', 'approximate',
           'The wall over the hall\'s door on the axis, up to the lunette. The door\'s width and height are approximate.', sect_src)
        cp(f'hall-{end}-lunette-head', HALL, rect(1590, y0, 1710, y1), LUNETTE, ATTIC, 'plaster', 'drawn',
           'The wall over the crown of the lunette. ' + SECT, sect_src)
        cp(f'hall-{end}-lunette', HALL, rect(1590, (y0 + y1) / 2 - 2, 1710, (y0 + y1) / 2 + 2), CORNICE, LUNETTE, 'glass', 'drawn',
           'A lunette window, one on each side of the hall ("Inscription on four sides" runs under them). ' + SECT, sect_src)
    # The lunette seen across the hall: the west window, an arch of glass 11.75 m across from the
    # cornice to its crown, with its mullions (section C-C draws it in elevation).
    yc, half = (Y0 + Y1) / 2, 148
    cp('hall-west-lunette', HALL, LL([P(X0 + 1, yc + half), P(X0 + 1, yc - half), P(X0 + 3, yc - half), P(X0 + 3, yc + half)]), CORNICE, LUNETTE, 'glass', 'drawn',
       'The west lunette window over the great arch, 11.75 m across, as section C-C draws it. ' + SECT, sect_src, shape='arch')
    for k in range(1, 6):
        u = -1 + k / 3
        if abs(u) >= 1:
            continue
        y = yc + u * half
        top = CORNICE + (LUNETTE - CORNICE) * math.sqrt(max(0.0, 1 - u * u))
        cp(f'hall-west-mullion-{k}', HALL, rect(X0 + 3, y - 4, X0 + 9, y + 4), CORNICE, top, 'plaster', 'drawn',
           'A mullion of the west lunette. ' + SECT, sect_src)
    cp('hall-west-sill', HALL, rect(X0 + 1, yc - half - 6, X0 + 12, yc + half + 6), CORNICE - 0.5, CORNICE, 'plaster', 'drawn',
       'The sill of the west lunette, on the cornice. ' + SECT, sect_src)

    # The ceiling and dome: a stepped low dome over the hall, its ceiling a shallower vault inside.
    R = 13.6
    ring = LL([P(1645 + R / K * math.cos(2 * math.pi * k / 24), 1158.5 + R / K * math.sin(2 * math.pi * k / 24)) for k in range(24)])
    zs = [ATTIC, DOME_BASE] + [DOME_BASE + (DOME_STEP - DOME_BASE) * t for t in (0.5, 1.0)] + [DOME_STEP + (DOME_TOP - DOME_STEP) * k / 8 for k in range(1, 9)]
    levels = []
    for z in zs:
        if z <= DOME_BASE:
            o = R
        elif z <= DOME_STEP:
            o = 12.6 + (11.5 - 12.6) * (z - DOME_BASE) / (DOME_STEP - DOME_BASE)
        else:
            t = (z - DOME_STEP) / (DOME_TOP - DOME_STEP)
            o = 11.5 * math.sqrt(max(0.0, 1 - (t * 0.995) ** 2))
        u = (z - ATTIC) / (CEIL_TOP - ATTIC)
        i = 11.2 * math.sqrt(max(0.0, 1 - u * u)) if u < 1 else 0.0
        levels.append([round(z - ATTIC, 3), round(o / R, 4), round(min(i, o - 0.6) / R if i > 0 else 0.0, 4)])
    cp('dome', 'Broad Street Station dome', ring, ATTIC, DOME_TOP, 'dome', 'drawn',
       'The dome: a cornice ring, the stepped haunches and the low outer dome, in its original tile in 1943; inside, the hall\'s ceiling, a shallower vault. Profiles from sections A-A, B-B and C-C; the crown is 100 ft above the floor, as published.',
       sect_src + [ARCHIPEDIA], shape='revolve', levels=levels, only=None)
    # Benches: four long benches down the hall.
    for k, x in enumerate((1493, 1593, 1696, 1805)):
        cp(f'hall-bench-{k + 1}', HALL, rect(x - 13, 992, x + 13, 1307), 0, 0.9, 'wood', 'drawn',
           'One of the four long benches of the White Waiting Room (mahogany, per the National Register nomination). Position from the plan; height approximate.', plan_src + [NR])
    cp('news-stand', 'Broad Street Station: news and cigar stand', rect(1305, 1110, 1325, 1210), 0, 1.1, 'wood', 'drawn',
       'The News & Cigar Stand in its niche off the hall. ' + PLAN_HT, plan_src)

    # ---- the tickets band and the east wing (lifted away above its floor) -----------------------
    band = 'Broad Street Station: tickets, Pullman and information'
    for k, (y0, y1) in enumerate([(986, 1000), (1095, 1105), (1205, 1215), (1300, 1331)]):
        cp(f'band-pier-{k + 1}', band, rect(X1, y0, X1 + 24, y1), 0, CORNICE, 'plaster', 'drawn', 'A pier between the hall and the counters. ' + PLAN_HT, plan_src)
    for k, (y0, y1) in enumerate([(1000, 1095), (1105, 1205), (1215, 1300)]):
        cp(f'band-counter-{k + 1}', band, rect(X1 + 2, y0 + 8, X1 + 20, y1 - 8), 0, 1.1, 'wood', 'drawn',
           ['The Pullman counter.', 'The ticket counter (two ticket booths on the plan).', 'The information counter.'][k] + ' ' + PLAN_HT, plan_src)
    # Partitions: center lines in plate px, 8 px (0.3 m) thick, up to the second floor.
    parts = [
        ('band-back', (2085, 955), (2085, 1345)), ('band-1', (1985, 1100), (2085, 1100)), ('band-2', (1985, 1210), (2085, 1210)),
        ('cwr-top-1', (2085, 955), (2190, 955)), ('cwr-top-2', (2250, 955), (2549, 955)), ('cwr-bottom', (1985, 1347), (2549, 1347)),
        ('cwr-east-1', (2435, 955), (2435, 1110)), ('cwr-east-2', (2435, 1180), (2435, 1347)),
        ('strip-1', (2435, 1090), (2549, 1090)), ('strip-2', (2435, 1190), (2549, 1190)),
        ('front-1', (2195, 1347), (2195, 1577)), ('front-2', (2295, 1347), (2295, 1577)), ('front-3', (2440, 1347), (2440, 1577)),
        ('front-4', (2440, 1500), (2549, 1500)), ('matron', (2195, 1420), (2295, 1420)),
        ('back-1', (1960, 735), (1960, 955)), ('back-2', (2060, 735), (2060, 955)), ('back-3', (2200, 735), (2200, 955)),
        ('back-4', (2320, 735), (2320, 955)), ('parcel', (2060, 900), (2200, 900)), ('dining', (2320, 820), (2440, 820)),
        ('pantry-1', (2440, 800), (2440, 955)), ('pantry-2', (2440, 870), (2549, 870)),
        ('vestibule-7', (1870, 870), (1960, 955)),
    ]
    for id_, p, q in parts:
        # Each stops half its thickness short at both ends, so it meets its neighbor's face.
        l = math.hypot(q[0] - p[0], q[1] - p[1])
        u = ((q[0] - p[0]) / l * 4, (q[1] - p[1]) / l * 4)
        p, q = (p[0] + u[0], p[1] + u[1]), (q[0] - u[0], q[1] - u[1])
        cp(f'partition-{id_}', WING, wall(p, q, 8), 0, L2, 'plaster', 'drawn',
           'A partition of the first floor: around the Colored Waiting Room, the counters and lobbies, baggage and parcel check, Lunch Room No. 2, toilets and stores. ' + PLAN_HT, plan_src)
    for k, y in enumerate((1060, 1205)):
        cp(f'cwr-bench-{k + 1}', 'Broad Street Station: Colored Waiting Room', rect(2170, y - 13, 2390, y + 13), 0.02, 0.9, 'wood', 'drawn',
           'A long bench of the Colored Waiting Room, as the plan draws it. Height approximate.', plan_src)
    cp('cwr-floor-mark', 'Broad Street Station: Colored Waiting Room', rect(2095, 965, 2425, 1337), 0, 0.02, 'floor', 'drawn',
       'The Colored Waiting Room, in the east wing, opposite the lunch room across the White Waiting Room: Virginia law kept Black and white passengers apart. ' + PLAN, plan_src + [ARCHIPEDIA])
    cp('women-bench', 'Broad Street Station: White Women\'s room', rect(2015, 1478, 2140, 1503), 0, 0.9, 'wood', 'drawn', 'The bench of the women\'s waiting room. ' + PLAN_HT, plan_src)
    cp('lunch-2-counter', 'Broad Street Station: Lunch Room No. 2', rect(2362, 835, 2380, 945), 0, 1.1, 'wood', 'drawn', 'The counter of Lunch Room No. 2. ' + PLAN_HT, plan_src)
    cp('baggage-counter', 'Broad Street Station: baggage check', rect(2108, 770, 2126, 870), 0, 1.1, 'wood', 'drawn', 'The baggage-check counter. ' + PLAN_HT, plan_src)
    cp('lobby-2-stair', 'Broad Street Station: Lobby No. 2', LL([P(1880, 860), P(1945, 860), P(1945, 740), P(1880, 740)]), 0, L2, 'stone', 'drawn',
       'The stair in Lobby No. 2, up to the offices. Its place is from the plan; drawn as a straight flight (approximate).', plan_src, shape='stair', steps=14)

    # ---- the concourse vestibule ---------------------------------------------------------------
    VEST = 'Broad Street Station: concourse vestibule'
    for x0, x1 in ((1440, 1463), (1837, 1860)):
        cp(f'vestibule-6-wall-{x0}', VEST, rect(x0, 700, x1, 870), 0, WING_TOP - 0.6, 'plaster', 'drawn', 'A side wall of the vestibule to the concourse (Vestibule No. 6). ' + PLAN + ' ' + SECT, sect_src)
    for k, x in enumerate((1600, 1700)):
        cp(f'vestibule-6-column-{k + 1}', VEST, disc(x, 785, 22), 0, 9.0, 'stone', 'drawn', 'One of the two columns of the vestibule to the concourse. ' + PLAN_HT, plan_src)
    cp('vestibule-6-roof', VEST, rect(1440, 700, 1860, 846), WING_TOP - 0.6, WING_TOP, 'stone', 'approximate',
       'The roof over the vestibule to the concourse, open two storeys inside ("upper part of vestibule to concourse", Plate 16). Height approximate.', [P16])

    # ---- the concourse, out over the tracks ----------------------------------------------------
    # 54 ft wide on the axis (the plate's stub, 1440–1860 px), from the vestibule (y = 700) to past
    # the last platform (b = 98, the 1925 Sanborn sheet); about 250 ft from the head house.
    CON = 'Broad Street Station concourse'
    a0, a1 = -2 + (1440 - XC) * K, -2 + (1860 - XC) * K
    b0, b1 = -20 + (YF - 700) * K, 98.0
    WT = 0.6
    con_src = [P15, AMAR, NR]
    part('bss-c-concourse-deck', CON, LL([ab(a0, b0), ab(a1, b0), ab(a1, b1), ab(a0, b1)]), 1.0, 'floor',
         'The concourse floor, at the level of the waiting room, carried over the tracks on piers. Width from the plan (54 ft, as published); length from the 1925 Sanborn sheet; deck depth approximate.',
         con_src, only='cutaway', elevation=FF - 1.0, confidence='drawn')
    bays = 11
    bay = (b1 - b0) / bays
    for k in range(bays):
        s0 = b0 + k * bay
        w0, w1 = s0 + bay / 2 - 1.6, s0 + bay / 2 + 1.6  # a tall window in each bay
        for nm, (q0, q1, z0, z1) in {
            'pier': (s0, w0, 0, 8.4), 'pier-b': (w1, s0 + bay, 0, 8.4), 'sill': (w0, w1, 0, 1.0), 'head': (w0, w1, 6.8, 8.4),
        }.items():
            part(f'bss-c-concourse-west-{k + 1}-{nm}', CON, LL([ab(a0, q0), ab(a0 + WT, q0), ab(a0 + WT, q1), ab(a0, q1)]), z1 - z0, 'plaster',
                 'The concourse\'s west wall, with one of its eleven tall windows (per the 1919 article and the National Register nomination); window sizes approximate.',
                 [AMAR, NR], only='cutaway', elevation=FF + z0, confidence='written')
    part('bss-c-concourse-end', CON, LL([ab(a0 + WT, b1 - WT), ab(a1 - WT, b1 - WT), ab(a1 - WT, b1), ab(a0 + WT, b1)]), 8.4, 'plaster', 'The far end wall of the concourse. Approximate.', [AMAR],
         only='cutaway', elevation=FF, confidence='approximate')
    part('bss-c-concourse-roof', CON, LL([ab(a0, b0), ab(a1, b0), ab(a1, b1), ab(a0, b1)]), 0.6, 'stone',
         'The concourse roof, over an elliptical barrel vault (1919 article; National Register nomination). Height approximate.',
         [AMAR, NR], only='cutaway', elevation=FF + 8.4, confidence='approximate')
    # East wall: doors to the departure stairs, one at each platform.
    # b of each door's center: where a platform's center line meets the east wall.
    edges = [b0]
    for bb in sorted(to_ab(st(crossing(t, a1 - WT / 2), t))[1] for t in platforms):
        edges += [bb - 1.6, bb + 1.6]
    edges.append(b1)
    for k in range(0, len(edges), 2):
        q0, q1 = edges[k], edges[k + 1]
        part(f'bss-c-concourse-east-{k // 2 + 1}', CON, LL([ab(a1 - WT, q0), ab(a1, q0), ab(a1, q1), ab(a1 - WT, q1)]), 8.4, 'plaster',
             'The concourse\'s east wall, with a door to each departure stair. Approximate.', [AMAR], only='cutaway', elevation=FF, confidence='approximate')

    # Departure stairs on the east side, arrival ramps on the west (1919 article; SAH Archipedia):
    # a flight from the concourse door down each platform. Their run and width are approximate.
    stairs = []
    for k, t in enumerate(platforms):
        s = crossing(t, a1)
        top, foot = s - 1.5, s - 13.0
        ring = LL([st(foot, t - 1.5), st(foot, t + 1.5), st(top, t + 1.5), st(top, t - 1.5)])
        part(f'bss-c-stair-{k + 1}', 'Broad Street Station: departure stair', ring, 0, 'stone',
             'A stair down from the concourse to the platform. The 1919 article and SAH Archipedia put departures down stairways on the east side; this flight\'s place, run and width are approximate.',
             [AMAR, ARCHIPEDIA], only='cutaway', confidence='approximate', shape='stair', steps=30, upTo=FF)
        land = LL([st(s - 1.5, t - 1.5), st(s - 1.5, t + 1.5), st(s + 0.3, t + 1.5), st(s + 0.3, t - 1.5)])
        part(f'bss-c-landing-{k + 1}', 'Broad Street Station: departure stair', land, 0.4, 'stone', 'The landing at the top of the stair, outside the concourse door. Approximate.',
             [AMAR], only='cutaway', confidence='approximate', elevation=FF - 0.4)
        stairs.append((s, top, foot))
    return stairs

