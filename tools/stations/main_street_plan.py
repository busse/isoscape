"""Main Street Station's head house and concourse, for the cutaway: walls, floors, the stair from
Main Street, the waiting room's screen and ceiling, the offices, the roof and the clock tower.

Imported by main_street.py, which passes its `part` and frame helpers and its levels. No plan or
section of the head house is known (HABS VA-848 has photographs and data pages only), so:

  - its outline is OpenStreetMap's (way 366226941), which matches HABS's 102 ft 5 in by 63 ft;
  - what is where, floor by floor, follows HABS VA-848's written description (1969) and the 1970
    National Register nomination: a five-bay loggia on Main Street; behind it a public hall; the
    main stair in the loggia's first bay from the west, straight up to the first floor with a
    landing, between tiled walls; the waiting room filling most of the first floor, with a screen
    of columns and glazed arches on its west side, a coffered ceiling, and a five-bay arcade at
    its north end to the concourse; offices on the floors above, on a central east-west corridor;
    the mail room beneath the concourse; the clock tower at the southwest corner;
  - sizes and heights not given in those texts are approximate, scaled from photographs (HABS
    VA-848, Detroit Publishing): each part says so.

Bays along the front (a, meters east of the front's middle): the tower (6.15 m, OSM way
366226942), then six bays of 4.06 m, the middle five the loggia.
"""

import math

HH_W, HH_E, HH_N = -15.25, 15.25, 19.64      # the head house (OSM way 366226941)
T = 0.75                                     # outer wall thickness (approximate)
TOWER = (-15.25, -9.1, 0.0, 6.7)             # a0, a1, b0, b1 (OSM way 366226942)
BAYS = [-9.1 + 4.06 * k for k in range(7)]   # the loggia's bay lines, -9.1 to 15.26
ELL = (-12.6, 11.9, HH_N, 30.2)              # the concourse ell (OSM way 113030476; HAER VA-4, sheet 2: 35 ft deep)
B_GATE = ELL[3]


def build(part, rect, ring, plane, SRC, L):
    G, FF, L2, L3, L4 = L['G'], L['FF'], L['L2'], L['L3'], L['L4']
    CORNICE, BAL, RIDGE, FORE = L['CORNICE'], L['BALUSTRADE'], L['RIDGE'], L['FORECOURT']
    HABS = [SRC['habs-data'], SRC['nrhp']]
    PH = [SRC['habs-photo-side'], SRC['detroit-east'], SRC['habs-photo-front']]
    OSM = [SRC['osm-headhouse']]
    HH = 'Main Street Station: head house'

    def p(id_, name, rg, z0, z1, tone, conf, note, src, **kw):
        part(f'mss-h-{id_}', name, rg, z0, z1, tone, conf, note, src, **kw)

    HEIGHTS = ' Heights are scaled from photographs (approximate).'
    # ---- outer walls ------------------------------------------------------------------------
    WALL = 'An outer wall of the head house, of brick faced with a buff tile like Roman brick (HABS VA-848). Its line is OSM\'s; its thickness is approximate.' + HEIGHTS
    p('wall-west', HH, rect(HH_W, HH_W + T, TOWER[3], HH_N), G - 0.4, CORNICE - 0.5, 'brick', 'written', WALL, HABS + OSM + PH)
    p('wall-east', HH, rect(HH_E - T, HH_E, 0, HH_N), G - 0.4, CORNICE - 0.5, 'brick', 'written', WALL, HABS + OSM + PH)
    # The back wall: solid below the first floor; above it, the five-bay arcade to the concourse.
    p('wall-back-low', HH, rect(HH_W + T, HH_E - T, HH_N - T, HH_N), G - 0.4, FF, 'brick', 'written', WALL, HABS + OSM)
    ARC_TOP = FF + 5.4
    ARC = 'The five-bay arcade at the north end of the waiting room, its upper parts glazed, through which passengers went to the concourse (HABS VA-848). Its bays are taken to line up with the loggia\'s; sizes approximate.'
    for k, a in enumerate(BAYS[:6]):
        p(f'arcade-pier-{k}', 'Main Street Station: arcade to the concourse', rect(a - 0.4, a + 0.4, HH_N - T, HH_N), FF, ARC_TOP, 'plaster', 'written', ARC, HABS)
    for k in range(5):
        a0, a1 = BAYS[k] + 0.4, BAYS[k + 1] - 0.4
        p(f'arcade-glass-{k}', 'Main Street Station: arcade to the concourse', ring([(a0, HH_N - 0.4), (a1, HH_N - 0.4), (a1, HH_N - 0.35), (a0, HH_N - 0.35)]), FF + 2.9, ARC_TOP - 0.8, 'glass', 'written', ARC, HABS)
        p(f'arcade-arch-{k}', 'Main Street Station: arcade to the concourse', ring([(a0, HH_N - 0.4), (a1, HH_N - 0.4), (a1, HH_N - 0.35), (a0, HH_N - 0.35)]), ARC_TOP - 0.8, ARC_TOP, 'glass', 'written', ARC, HABS, shape='arch')
    for side, (a0, a1) in (('w', (HH_W + T, BAYS[0] - 0.4)), ('e', (BAYS[5] + 0.4, HH_E - T))):
        p(f'wall-back-{side}', HH, rect(a0, a1, HH_N - T, HH_N), FF, CORNICE - 0.5, 'brick', 'written', WALL, HABS + OSM)
    p('wall-back-high', HH, rect(BAYS[0] - 0.4, BAYS[5] + 0.4, HH_N - T, HH_N), ARC_TOP, CORNICE - 0.5, 'brick', 'written', WALL, HABS + OSM)

    # The front, on Main Street: the loggia's piers and the wall over its arches, the bay east of
    # it, and above, the first floor's arcade, its two French windows and the 13-bay gallery.
    FRONT = 'The Main Street front (HABS VA-848: seven bays; a five-bay loggia of rough-hewn stone with segmental arches; above it a five-bay arcade, and a 13-bay gallery under the cornice).' + ' Sizes and heights approximate, from photographs.'
    LOG_TOP = G + 4.4
    for k, a in enumerate(BAYS[:6]):
        a0, a1 = (a - 0.45, a + 0.45) if k > 0 else (a, a + 0.9)
        p(f'loggia-pier-{k}', 'Main Street Station: loggia', rect(a0, a1, 0, T), G, LOG_TOP, 'stone', 'written', FRONT, HABS + PH)
    p('loggia-head', 'Main Street Station: loggia', rect(BAYS[0], BAYS[5], 0, T), LOG_TOP, FF + 0.9, 'stone', 'written', FRONT, HABS + PH)
    p('front-east-low', HH, rect(BAYS[5] + 0.45, HH_E, 0, T), G, FF + 0.9, 'stone', 'written', FRONT, HABS + PH)
    # First floor and gallery: wall pieces between the openings, glass in them.
    p('front-high', HH, rect(BAYS[0], HH_E, 0, T), FF + 0.9, CORNICE - 0.5, 'brick', 'written', FRONT, HABS + PH)
    for k in range(5):
        a0, a1 = BAYS[k] + 0.45, BAYS[k + 1] - 0.45
        p(f'front-arcade-{k}', 'Main Street Station: first-floor arcade', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), FF + 1.2, FF + 4.4, 'glass', 'written', FRONT, HABS + PH)
        p(f'front-arcade-arch-{k}', 'Main Street Station: first-floor arcade', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), FF + 4.4, FF + 5.6, 'glass', 'written', FRONT, HABS + PH, shape='arch')
    a0, a1 = BAYS[6] - 2.75, BAYS[6] - 1.3
    p('front-french', 'Main Street Station: French window', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), FF + 0.6, FF + 4.6, 'glass', 'written',
      'One of the two French windows in the outer bays of the first floor, each opening on a small balcony (HABS VA-848). Size approximate.', HABS + PH)
    p('front-balcony', 'Main Street Station: balcony', rect(a0 - 0.5, a1 + 0.5, -0.8, 0), FF + 0.3, FF + 0.6, 'stone', 'written',
      'A small balustraded balcony on consoles under a French window (HABS VA-848). Size approximate.', HABS + PH)
    gal_w = (HH_E - HH_W) / 13
    for k in range(13):
        a0 = HH_W + k * gal_w + 0.55
        a1 = a0 + gal_w - 1.1
        if a1 <= TOWER[1] + 0.2:
            continue   # the tower's own windows stand there
        p(f'gallery-{k}', 'Main Street Station: gallery window', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), L2 + 0.7, L2 + 2.6, 'glass', 'written',
          'A window of the second floor\'s gallery, 13 bays across the front between engaged Corinthian columns (HABS VA-848). Sizes approximate.', HABS + PH)
    p('belt', 'Main Street Station: belt course', rect(BAYS[0], HH_E + 0.15, -0.15, 0), L2 - 0.15, L2 + 0.15, 'stone', 'approximate',
      'A stone band across the front at the second floor, as the photographs show it. Approximate.', PH)

    # The cornice and the balustrade above it, round all four sides.
    CORN = 'The relatively shallow entablature round the building, and the balustrade on it (HABS VA-848). Projection and heights approximate.'
    TA, TB = TOWER[1], TOWER[3]
    for side, rg in (('s', rect(TA, HH_E + 0.3, -0.3, 0.45)), ('n', rect(HH_W - 0.3, HH_E + 0.3, HH_N - 0.45, HH_N + 0.3)),
                     ('w', rect(HH_W - 0.3, HH_W + 0.45, TB, HH_N - 0.45)), ('e', rect(HH_E - 0.45, HH_E + 0.3, 0.45, HH_N - 0.45))):
        p(f'cornice-{side}', 'Main Street Station: cornice', rg, CORNICE - 0.5, CORNICE, 'stone', 'written', CORN, HABS + PH)
    for side, rg in (('s', rect(TA, HH_E, 0, 0.35)), ('n', rect(HH_W, HH_E, HH_N - 0.35, HH_N)),
                     ('w', rect(HH_W, HH_W + 0.35, TB, HH_N - 0.35)), ('e', rect(HH_E - 0.35, HH_E, 0.35, HH_N - 0.35))):
        p(f'balustrade-{side}', 'Main Street Station: balustrade', rg, CORNICE, BAL, 'stone', 'written', CORN, HABS + PH)

    # ---- floors -------------------------------------------------------------------------------
    FL = ' Its level is approximate (scaled from photographs).'
    for k, rg in enumerate((rect(TOWER[1], HH_E - T, 0, HH_N - T), rect(HH_W + T, TOWER[1], TOWER[3], HH_N - T))):
        p(f'floor-ground-{k}', 'Main Street Station: ground floor', rg, G - 0.4, G, 'floor', 'written',
          'The ground floor, at the level of the loggia: the public hall behind the loggia and the service rooms, baggage and mail (HABS VA-848).' + FL, HABS)
    STAIR = (BAYS[0], BAYS[1])               # the main stair's bay
    S0, S1, S2, S3 = 4.2, 10.2, 12.0, 18.0   # flight 1, landing, flight 2 (b)
    FIRST = 'The first floor, the level of the waiting room, the concourse and the platforms (HABS VA-848).' + FL
    for k, (a0, a1, b0, b1) in enumerate([(HH_W + T, STAIR[0], TOWER[3], HH_N - T), (STAIR[0], STAIR[1], T, S2 - 1.0), (STAIR[0], STAIR[1], S3, HH_N - T), (STAIR[1], HH_E - T, T, HH_N - T)]):
        p(f'floor-first-{k}', 'Main Street Station: first floor', rect(a0, a1, b0, b1), FF - 0.5, FF, 'floor', 'written', FIRST, HABS)
    p('floor-second', 'Main Street Station: second floor', rect(HH_W + T, HH_E - T, T, HH_N - T), L2 - 0.4, L2, 'floor', 'written',
      'The second floor, the low gallery story under the cornice: offices (HABS VA-848).' + FL, HABS)
    # The roof: a steep hip of red clay tile, springing behind the balustrade.
    R0 = (HH_W + 0.6, HH_E - 0.6, 0.6, HH_N - 0.6)
    run = (R0[3] - R0[2]) / 2
    rise = RIDGE - CORNICE
    k_in = run / rise

    def inset_at(z, extra):
        return R0[0] + (z - CORNICE) * k_in + extra, R0[1] - (z - CORNICE) * k_in - extra, R0[2] + (z - CORNICE) * k_in + extra, R0[3] - (z - CORNICE) * k_in - extra

    for nm, z, extra in (('third', L3, 0.9), ('fourth', L4, 0.9)):
        a0, a1, b0, b1 = inset_at(z, extra)
        p(f'floor-{nm}', f'Main Street Station: {nm} floor', rect(a0, a1, b0, b1), z - 0.35, z, 'floor', 'written',
          f'The {nm} floor, in the roof, lit by its dormers: offices (HABS VA-848: "three and two one-half stories"; the 1970 nomination: offices on the upper floors).' + FL, HABS)
    p('roof', 'Main Street Station: roof', rect(*R0), CORNICE, RIDGE, 'tile', 'written',
      'The very steep hipped roof of red clay tile (HABS VA-848). Its pitch and ridge height are scaled from photographs; its thickness is approximate.',
      HABS + PH, shape='inset', levels=[[0, 0, 0.55], [round(rise, 3), round(run, 3), round(run, 3)]])
    # Dormers on the front slope: a lower row of five, an upper row of three (HABS VA-848: two levels).
    DORM = 'A dormer on the roof\'s front: HABS VA-848 describes two levels of dormers, plain hipped ones alternating with pedimented ones. Places and sizes approximate, from photographs.'
    for row, (z0, z1, centers) in enumerate([(CORNICE + 0.5, CORNICE + 2.7, [(BAYS[k] + BAYS[k + 1]) / 2 for k in range(1, 5)]), (CORNICE + 4.4, CORNICE + 6.0, [(BAYS[k] + BAYS[k + 1]) / 2 for k in (1, 3)])]):
        for j, c in enumerate(centers):
            b_front = R0[2] + (z0 - CORNICE) * k_in - 0.4
            b_back = R0[2] + (z1 - CORNICE) * k_in + 0.6
            w = 0.95 if row == 0 else 0.75
            p(f'dormer-{row}-{j}', 'Main Street Station: dormer', rect(c - w, c + w, b_front, b_back), z0, z1, 'brick', 'approximate', DORM, HABS + PH)
            p(f'dormer-{row}-{j}-roof', 'Main Street Station: dormer', rect(c - w - 0.15, c + w + 0.15, b_front - 0.15, b_back), z1, z1 + 1.0, 'tile', 'approximate', DORM, HABS + PH,
              shape='inset', levels=[[0, 0, 0], [1.0, w, w]])
            p(f'dormer-{row}-{j}-glass', 'Main Street Station: dormer', ring([(c - w + 0.35, b_front - 0.04), (c + w - 0.35, b_front - 0.04), (c + w - 0.35, b_front), (c - w + 0.35, b_front)]), z0 + 0.4, z1 - 0.3, 'glass', 'approximate', DORM, HABS + PH)

    # ---- the clock tower ------------------------------------------------------------------------
    TW = 'The six-story clock tower at the southwest corner (HABS VA-848), its finial 110 ft above the ground (SAH Archipedia). Its outline is OSM\'s; its stages are scaled from photographs (approximate).'
    TSRC = HABS + [SRC['archipedia'], SRC['osm-tower']] + PH
    a0, a1, b0, b1 = TOWER
    SHAFT = FF + 17.5
    p('tower', 'Main Street Station: clock tower', rect(a0, a1, b0, b1), G - 0.4, SHAFT, 'brick', 'written', TW, TSRC)
    p('tower-cornice', 'Main Street Station: clock tower', rect(a0 - 0.3, a1 + 0.3, b0 - 0.3, b1 + 0.3), SHAFT - 0.2, SHAFT + 0.3, 'stone', 'written', TW, TSRC)
    p('tower-clock-stage', 'Main Street Station: clock tower', rect(a0 + 0.3, a1 - 0.3, b0 + 0.3, b1 - 0.3), SHAFT + 0.3, FF + 21.3, 'brick', 'written', TW, TSRC)
    p('tower-entablature', 'Main Street Station: clock tower', rect(a0, a1, b0, b1), FF + 21.3, FF + 21.8, 'stone', 'written',
      'The entablature on the clock stage\'s coupled columns (HABS VA-848). Size approximate.', TSRC)
    p('tower-dome', 'Main Street Station: clock tower', rect(a0 + 0.2, a1 - 0.2, b0 + 0.2, b1 - 0.2), FF + 21.8, FF + 25.4, 'tile', 'written',
      'The tower\'s square dome (HABS VA-848), scaled from photographs: approximate.', TSRC, shape='inset',
      levels=[[0, 0, 9], [0.5, 0.05, 9], [1.4, 0.45, 9], [2.3, 1.2, 9], [3.0, 2.0, 9], [3.6, 2.9, 9]])
    cx, cb = (a0 + a1) / 2, (b0 + b1) / 2
    p('tower-finial', 'Main Street Station: clock tower', rect(cx - 0.18, cx + 0.18, cb - 0.18, cb + 0.18), FF + 25.4, G + 33.5, 'stone', 'written',
      'The bronze finial, its top 110 ft above the ground (SAH Archipedia; HABS VA-848).', TSRC)
    # The clock faces, on the front and the east side: discs, as stacked strips.
    zc = FF + 19.4
    r = 1.15
    disc = []
    for i in range(20):
        t = 2 * math.pi * i / 20
        disc += [round(r + r * math.cos(t), 3), round(r + r * math.sin(t), 3)]
    strips = [disc]
    CLK = 'A clock face, one on each side of the tower (HABS VA-848). Size approximate.'
    p('tower-clock-s', 'Main Street Station: clock', plane(cx - r, b0 + 0.26, cx + r, b0 + 0.26, 0.04), zc - r, zc + r, 'plaster', 'written', CLK, TSRC, shape='frame', members=strips)
    p('tower-clock-e', 'Main Street Station: clock', plane(a1 - 0.26, cb - r, a1 - 0.26, cb + r, 0.04), zc - r, zc + r, 'plaster', 'written', CLK, TSRC, shape='frame', members=strips)
    # Its windows: on the front, and on the east side above the main roof's balustrade.
    TWIN = 'A window of the clock tower, as the photographs show them. Places and sizes approximate.'
    for k, (z0, z1, pair) in enumerate([(G + 1.2, G + 3.6, False), (FF + 1.0, FF + 4.0, False), (L2 + 0.6, L2 + 2.6, True), (FF + 12.9, FF + 14.5, True), (FF + 15.1, FF + 16.7, True)]):
        xs = [(cx - 1.25, cx - 0.2), (cx + 0.2, cx + 1.25)] if pair else [(cx - 0.75, cx + 0.75)]
        for j, (x0, x1) in enumerate(xs):
            p(f'tower-window-s-{k}-{j}', 'Main Street Station: clock tower', ring([(x0, b0 - 0.05), (x1, b0 - 0.05), (x1, b0), (x0, b0)]), z0, z1, 'glass', 'approximate', TWIN, PH)
            if z0 > BAL:
                y0, y1 = cb - (x1 - cx), cb - (x0 - cx)
                p(f'tower-window-e-{k}-{j}', 'Main Street Station: clock tower', ring([(a1, y0), (a1 + 0.05, y0), (a1 + 0.05, y1), (a1, y1)]), z0, z1, 'glass', 'approximate', TWIN, PH)

    # ---- the steps, the loggia and the stair to the first floor -----------------------------------
    p('front-steps', 'Main Street Station: steps from Main Street', ring([(BAYS[0], -4.0), (BAYS[5], -4.0), (BAYS[5], 0.0), (BAYS[0], 0.0)]), FORE, G, 'stone', 'approximate',
      'The steps up from the Main Street sidewalk to the loggia, as the Detroit Publishing photograph from the east (4a10737) shows them. Their number and depth are approximate.',
      [SRC['detroit-east'], SRC['loc-blog']], shape='stair', steps=8)
    LOG = 'The loggia\'s back wall, with the doors into the building: in its first bay from the west, to the main stair; in its third and fourth bays, into the public hall (HABS VA-848). The loggia\'s depth is approximate.'
    p('loggia-back', 'Main Street Station: loggia', rect(BAYS[0], BAYS[5], 3.5, 3.9), G, FF - 0.5, 'brick', 'written', LOG, HABS)
    for k in (0, 2, 3):
        a0, a1 = BAYS[k] + 1.0, BAYS[k + 1] - 1.0
        p(f'loggia-door-{k}', 'Main Street Station: loggia door', ring([(a0, 3.46), (a1, 3.46), (a1, 3.5), (a0, 3.5)]), G, G + 3.0, 'wood', 'written', LOG, HABS)
        p(f'loggia-transom-{k}', 'Main Street Station: loggia door', ring([(a0, 3.46), (a1, 3.46), (a1, 3.5), (a0, 3.5)]), G + 3.0, G + 4.0, 'glass', 'written', LOG, HABS, shape='arch')
    # The stair hall: the main stair between tiled walls, straight up with a landing.
    SH = 'The main stairway, from the Main Street entrance straight up to the first floor with a landing in the middle, between tiled walls; it comes up at the west end of the arcade to the concourse (HABS VA-848). Its width and run are approximate.'
    p('stair-wall-w', 'Main Street Station: main stairway', rect(STAIR[0] - 0.3, STAIR[0], TOWER[3], HH_N - T), G, FF - 0.5, 'plaster', 'written', SH, HABS)
    p('stair-wall-e', 'Main Street Station: main stairway', rect(STAIR[1], STAIR[1] + 0.3, 3.9, HH_N - T), G, FF - 0.5, 'plaster', 'written', SH, HABS)
    sa0, sa1 = STAIR[0] + 0.3, STAIR[1] - 0.3
    mid = G + (FF - G) / 2
    p('stair-1', 'Main Street Station: main stairway', ring([(sa0, S0), (sa1, S0), (sa1, S1), (sa0, S1)]), G, mid, 'stone', 'written', SH, HABS, shape='stair', steps=19)
    p('stair-landing', 'Main Street Station: main stairway', rect(sa0, sa1, S1, S2), mid - 0.3, mid, 'stone', 'written', SH, HABS)
    p('stair-2', 'Main Street Station: main stairway', ring([(sa0, S2), (sa1, S2), (sa1, S3), (sa0, S3)]), mid, FF, 'stone', 'written', SH, HABS, shape='stair', steps=19)
    p('hall-wall', 'Main Street Station: public hall', rect(STAIR[1] + 0.3, HH_E - T, 10.0, 10.3), G, FF - 0.5, 'plaster', 'approximate',
      'The wall between the public hall behind the loggia and the baggage rooms. HABS VA-848 says the front of the ground floor "apparently was a public hall" and that its plan had been altered; where it ended is not known.', HABS)

    # ---- the waiting room -----------------------------------------------------------------------------
    WR = 'Main Street Station: waiting room'
    SCR = 'The screen on the west side of the waiting room: columns, with glazing set in arches between them, between the waiting room and the stairway up from Main Street (HABS VA-848; the 1970 nomination calls it a large colonnaded glass screen). The columns\' number and spacing are approximate.'
    cols = [T + 0.9 + k * 2.75 for k in range(7)]
    sx = STAIR[1] + 0.15
    for k, b in enumerate(cols):
        p(f'screen-column-{k}', WR, rect(sx - 0.28, sx + 0.28, b - 0.28, b + 0.28), FF, FF + 5.0, 'plaster', 'written', SCR, HABS)
    for k in range(len(cols) - 1):
        b0, b1 = cols[k] + 0.3, cols[k + 1] - 0.3
        p(f'screen-glass-{k}', WR, ring([(sx, b0), (sx, b1), (sx - 0.05, b1), (sx - 0.05, b0)]), FF + 0.9, FF + 3.6, 'glass', 'written', SCR, HABS)
        p(f'screen-arch-{k}', WR, ring([(sx, b0), (sx, b1), (sx - 0.05, b1), (sx - 0.05, b0)]), FF + 3.6, FF + 5.0, 'glass', 'written', SCR, HABS, shape='arch')
    p('screen-head', WR, rect(sx - 0.3, sx + 0.3, T, HH_N - T - 0.1), FF + 5.0, L2 - 0.4, 'plaster', 'written', SCR, HABS)
    # The coffered ceiling: beams both ways under the second floor (HABS VA-848).
    CEIL = 'The waiting room\'s coffered ceiling (HABS VA-848). The coffers\' size is approximate.'
    for k, b in enumerate([T + 2.6 * i for i in range(1, 7)]):
        p(f'ceiling-beam-a-{k}', WR, rect(STAIR[1] + 0.3, HH_E - T, b - 0.15, b + 0.15), L2 - 0.95, L2 - 0.47, 'plaster', 'written', CEIL, HABS)
    for k, a in enumerate([STAIR[1] + 0.3 + 2.6 * i for i in range(1, 8)]):
        if a > HH_E - T - 0.5:
            continue
        p(f'ceiling-beam-b-{k}', WR, rect(a - 0.15, a + 0.15, T, HH_N - T), L2 - 0.95, L2 - 0.47, 'plaster', 'written', CEIL, HABS)

    # ---- offices above ---------------------------------------------------------------------------------
    OFF = 'Main Street Station: offices'
    CORR = 'A wall of the central corridor that runs east and west on each office floor, offices on either side (HABS VA-848). Its place is approximate.'
    for nm, z0, z1, extra in (('second', L2, CORNICE - 0.5, 0.0), ('third', L3, L4 - 0.35, 0.9), ('fourth', L4, L4 + 2.6, 0.9)):
        if nm == 'second':
            a0, a1 = HH_W + T, HH_E - T
        else:
            a0, a1, _, _ = inset_at(z1, extra)
        for side, b in (('s', 8.95), ('n', 10.7)):
            p(f'corridor-{nm}-{side}', OFF, rect(a0, a1, b - 0.12, b + 0.12), z0, z1, 'plaster', 'written', CORR, HABS)
    OFFW = 'A partition between offices (HABS VA-848: offices of merely functional design). Its place is approximate.'
    for k, a in enumerate((BAYS[1] + 0.15, BAYS[3])):
        for side, (b0, b1) in (('s', (T, 8.83)), ('n', (10.82, HH_N - T))):
            p(f'office-wall-{k}-{side}', OFF, rect(a - 0.1, a + 0.1, b0, b1), L2, CORNICE - 0.5, 'plaster', 'approximate', OFFW, HABS)

    # ---- the concourse ell, and the mail room under it ------------------------------------------------
    E0, E1, F0, F1 = ELL
    CC = 'Main Street Station: concourse'
    CON = 'The concourse, an ell from the back of the head house, enclosed on its sides but open to the shed on the north (HABS VA-848), 35 ft deep (HAER VA-4, sheet 2). Its height is approximate.'
    CTOP = FF + 6.8
    p('ell-wall-w', CC, rect(E0, E0 + 0.6, F0, F1), G - 0.4, CTOP, 'brick', 'written', CON, HABS + [SRC['haer-2'], SRC['osm-station']])
    p('ell-wall-e', CC, rect(E1 - 0.6, E1, F0, F1), G - 0.4, CTOP, 'brick', 'written', CON, HABS + [SRC['haer-2'], SRC['osm-station']])
    p('ell-floor', CC, rect(E0 + 0.6, E1 - 0.6, F0, F1), FF - 0.5, FF, 'floor', 'written', CON, HABS + [SRC['haer-2']])
    p('ell-roof', CC, rect(E0, E1, F0, F1), CTOP, CTOP + 0.5, 'roof', 'written', CON, HABS + [SRC['haer-2']])
    for k, b in enumerate([F0 + 2.6 * i for i in range(1, 4)]):
        p(f'ell-beam-{k}', CC, rect(E0 + 0.6, E1 - 0.6, b - 0.15, b + 0.15), CTOP - 0.55, CTOP - 0.07, 'plaster', 'written',
          'The concourse\'s coffered ceiling (HABS VA-848). Its coffers\' size is approximate.', HABS)
    MAIL = 'The mail room, beneath the concourse, with loading docks on the west side of the building (HABS VA-848; the 1970 nomination). Its walls\' places are approximate.'
    p('mail-floor', 'Main Street Station: mail room', rect(E0 + 0.6, E1 - 0.6, F0, F1 - 0.6), G - 0.4, G, 'floor', 'written', MAIL, HABS)
    p('mail-wall-n', 'Main Street Station: mail room', rect(E0 + 0.6, E1 - 0.6, F1 - 0.6, F1), G - 0.4, FF - 0.5, 'brick', 'written', MAIL, HABS)
    p('mail-dock', 'Main Street Station: mail room', rect(E0 - 3.0, E0, F0 + 1.5, F1 - 1.5), None, G, 'stone', 'written', MAIL, HABS)
    # The iron screen across the open north side, with its gates: posts, rails and bars.
    GATE = 'The wrought-iron screen between the concourse and the shed, with its numbered gates to the platforms (HABS VA-848; HAER photographs VA-4-9 to VA-4-11, "Gate 5"). Its pattern is drawn as plain bars; its height is approximate.'
    bars = []
    span = (E1 - 0.6) - (E0 + 0.6)
    x = 0.0
    while x <= span + 1e-6:
        bars.append([round(x, 3), 0.0, round(x, 3), 4.2, 0.05 if (round(x / 0.25) % 12) else 0.16])
        x += 0.25
    bars += [[0, 0.1, round(span, 3), 0.1, 0.12], [0, 2.4, round(span, 3), 2.4, 0.08], [0, 4.15, round(span, 3), 4.15, 0.12]]
    p('gates', 'Main Street Station: gates', plane(E0 + 0.6, F1 - 0.06, E1 - 0.6, F1 - 0.06, 0.08), FF, FF + 4.3, 'iron', 'written', GATE,
      HABS + [SRC['haer-photo-9']], shape='frame', members=bars)
