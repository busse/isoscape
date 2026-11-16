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
    # Each pier in courses of rough-hewn stone, every other one set 3 cm proud, so the joints
    # show (HABS VA-848: "rough-hewn stone"; Detroit Publishing 4a10737). Course heights are approximate.
    RUST = ' Its courses are drawn about 0.55 m high, as the photograph shows them roughly (approximate).'
    COURSE = 0.55
    n_c = max(1, round((LOG_TOP - G) / COURSE))
    for k, a in enumerate(BAYS[:6]):
        a0, a1 = (a - 0.45, a + 0.45) if k > 0 else (a, a + 0.9)
        for c in range(n_c):
            z0, z1 = G + (LOG_TOP - G) * c / n_c, G + (LOG_TOP - G) * (c + 1) / n_c
            d = 0.03 if c % 2 == 0 else 0.0
            p(f'loggia-pier-{k}' + ('' if c == 0 else f'-c{c}'), 'Main Street Station: loggia', rect(a0 - d, a1 + d, -d, T), z0, z1, 'stone', 'written', FRONT + RUST, HABS + PH)
    # The segmental arches between the piers: the stone over each opening, from the springing
    # to the loggia's head, in slices along the arc (the arches' rise is approximate).
    SPRING, CROWN = G + 3.2, G + 4.0
    ARCH = 'A segmental arch of the loggia, in rough-hewn stone (HABS VA-848: "a five-bay rough-hewn stone loggia with segmental arches"). Its springing and rise are scaled from the Detroit Publishing photograph from the east (4a10737): approximate.'
    for k in range(5):
        a0, a1 = BAYS[k] + 0.45, BAYS[k + 1] - 0.45
        span = a1 - a0
        rise = CROWN - SPRING
        r = (span * span / 4 + rise * rise) / (2 * rise)
        def arc(u):
            x = u - span / 2
            return rise - (r - math.sqrt(max(0.0, r * r - x * x)))
        plates = []
        n = 8
        for i in range(n):
            u0, u1 = span * i / n, span * (i + 1) / n
            plates.append([round(u0, 3), round(SPRING - G + arc(u0), 3), round(u1, 3), round(SPRING - G + arc(u1), 3),
                           round(u1, 3), round(LOG_TOP - G, 3), round(u0, 3), round(LOG_TOP - G, 3)])
        p(f'loggia-arch-{k}', 'Main Street Station: loggia', plane(a0, 0, a1, 0, T), G, LOG_TOP, 'stone', 'written', ARCH, HABS + PH,
          shape='frame', members=plates)
    p('loggia-head', 'Main Street Station: loggia', rect(BAYS[0], BAYS[5], 0, T), LOG_TOP, FF + 0.9, 'stone', 'written', FRONT, HABS + PH)
    BALU = ('The balustrade at the foot of the first floor\'s arcade: its columns stand on pedestals with balusters between (HABS VA-848; '
            'Detroit Publishing 4a10737). Drawn as a rail on plain balusters; sizes approximate.')
    bars = []
    span = BAYS[5] - BAYS[0]
    x = 0.12
    while x < span - 0.1:
        bars.append([round(x, 3), 0.12, round(x, 3), 0.72, 0.07])
        x += 0.3
    bars += [[0, 0.06, round(span, 3), 0.06, 0.12], [0, 0.78, round(span, 3), 0.78, 0.12]]
    p('front-balustrade', 'Main Street Station: balustrade', plane(BAYS[0], -0.32, BAYS[5], -0.32, 0.25), FF, FF + 0.9, 'stone', 'written', BALU, HABS + PH,
      shape='frame', members=bars)
    p('sill-course', 'Main Street Station: string course', rect(BAYS[0], HH_E + 0.15, -0.38, 0), FF - 0.25, FF, 'stone', 'approximate',
      'The stone course that tops the rusticated base along the front, under the first floor\'s balustrade, as the photographs show it. Approximate.', PH)
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

    # The roof is drawn in courses about 1.4 m apart up the slope, so it reads as tiled (the
    # photographs show the tile in courses; the spacing is approximate).
    nc = max(1, round(rise / 1.4))
    roof_levels = [[round(rise * i / nc, 3), round(run * i / nc, 3), round(min(run, run * i / nc + 0.55), 3)] for i in range(nc)]
    roof_levels.append([round(rise, 3), round(run, 3), round(run, 3)])
    for nm, z, extra in (('third', L3, 0.9), ('fourth', L4, 0.9)):
        a0, a1, b0, b1 = inset_at(z, extra)
        p(f'floor-{nm}', f'Main Street Station: {nm} floor', rect(a0, a1, b0, b1), z - 0.35, z, 'floor', 'written',
          f'The {nm} floor, in the roof, lit by its dormers: offices (HABS VA-848: "three and two one-half stories"; the 1970 nomination: offices on the upper floors).' + FL, HABS,
          within='mss-h-roof')
    p('roof', 'Main Street Station: roof', rect(*R0), CORNICE, RIDGE, 'tile', 'written',
      'The very steep hipped roof of red clay tile (HABS VA-848). Its pitch and ridge height are scaled from photographs; its thickness is approximate.',
      HABS + PH, shape='inset', levels=roof_levels)
    # Bronze finials at each end of the ridge (HABS VA-848); the west one stands on the half kept.
    for end, ra in (('w', R0[0] + run), ('e', R0[1] - run)):
        p(f'ridge-finial-{end}', 'Main Street Station: roof', rect(ra - 0.14, ra + 0.14, HH_N / 2 - 0.14, HH_N / 2 + 0.14), RIDGE, RIDGE + 2.6, 'iron', 'written',
          'A bronze finial at an end of the ridge (HABS VA-848: "decorative bronze finials appear at each end of the ridge"). Its height is approximate, from the photographs.', HABS + PH)
    # Dormers on the front slope: a lower row of five, an upper row of three (HABS VA-848: two levels).
    DORM = 'A dormer on the roof\'s front: HABS VA-848 describes two levels of dormers, plain hipped ones alternating with pedimented ones; the photographs show five or more in the lower row across the front. Places and sizes approximate, from photographs (Detroit Publishing 4a10737).'
    for row, (z0, z1, centers) in enumerate([(CORNICE + 0.5, CORNICE + 2.7, [(BAYS[k] + BAYS[k + 1]) / 2 for k in range(0, 5)]), (CORNICE + 4.4, CORNICE + 6.0, [(BAYS[k] + BAYS[k + 1]) / 2 for k in (0, 2)])]):
        for j, c in enumerate(centers):
            b_front = R0[2] + (z0 - CORNICE) * k_in - 0.4
            b_back = R0[2] + (z1 - CORNICE) * k_in + 0.6
            w = 0.95 if row == 0 else 0.75
            p(f'dormer-{row}-{j}', 'Main Street Station: dormer', rect(c - w, c + w, b_front, b_back), z0, z1, 'brick', 'approximate', DORM, HABS + PH, over='mss-h-roof')
            p(f'dormer-{row}-{j}-roof', 'Main Street Station: dormer', rect(c - w - 0.15, c + w + 0.15, b_front - 0.15, b_back), z1, z1 + 1.0, 'tile', 'approximate', DORM, HABS + PH,
              shape='inset', levels=[[0, 0, 9], [1.0, w, 9]], over='mss-h-roof')
            p(f'dormer-{row}-{j}-glass', 'Main Street Station: dormer', ring([(c - w + 0.35, b_front - 0.04), (c + w - 0.35, b_front - 0.04), (c + w - 0.35, b_front), (c - w + 0.35, b_front)]), z0 + 0.4, z1 - 0.3, 'glass', 'approximate', DORM, HABS + PH, over='mss-h-roof')

    # ---- the clock tower ------------------------------------------------------------------------
    TW = 'The six-story clock tower at the southwest corner (HABS VA-848), its finial 110 ft above the ground (SAH Archipedia). Its outline is OSM\'s; its stages are scaled from photographs (approximate).'
    TSRC = HABS + [SRC['archipedia'], SRC['osm-tower']] + PH
    a0, a1, b0, b1 = TOWER
    SHAFT = FF + 17.5
    cx, cb = (a0 + a1) / 2, (b0 + b1) / 2
    p('tower', 'Main Street Station: clock tower', rect(a0, a1, b0, b1), G - 0.4, SHAFT, 'brick', 'written', TW, TSRC)
    # Its foot is the rusticated stone base that runs along the front (HABS VA-848: windows of
    # the ground floor "set in the rusticated base"), in courses; stone bands mark its stages.
    TB = 'The rusticated stone base of the tower, as the front\'s base continues round it (HABS VA-848; Detroit Publishing 4a10737). Courses about 0.55 m, approximate.'
    nb = round((FF - G + 0.4) / 0.55)
    for c in range(nb):
        z0, z1 = G - 0.4 + (FF - G + 0.4) * c / nb, G - 0.4 + (FF - G + 0.4) * (c + 1) / nb
        d = 0.1 if c % 2 == 0 else 0.07
        sides = [rect(a0 - d, a1 + d, b0 - d, b0 + 0.3), rect(a1 - 0.3, a1 + d, b0 + 0.3, 3.5)]
        for j, rg in enumerate(sides):
            p(f'tower-base-{c}-{j}', 'Main Street Station: clock tower', rg, z0, z1, 'stone', 'written', TB, TSRC)
    BAND = 'A stone band round the tower between its stages, as the photographs show them. Places approximate.'
    for k, zb in enumerate((L2 + 0.1, FF + 12.3)):
        p(f'tower-band-{k}', 'Main Street Station: clock tower', rect(a0 - 0.15, a1 + 0.15, b0 - 0.15, b1 + 0.15), zb, zb + 0.3, 'stone', 'approximate', BAND, PH)
    p('tower-cornice', 'Main Street Station: clock tower', rect(a0 - 0.3, a1 + 0.3, b0 - 0.3, b1 + 0.3), SHAFT - 0.2, SHAFT + 0.3, 'stone', 'written', TW, TSRC)
    PIN = 'A pinnacle at a corner of the balcony under the clock stage, as the Detroit Publishing photographs show them. Size approximate.'
    for k, (x, y) in enumerate([(a0 - 0.15, b0 - 0.15), (a1 + 0.15, b0 - 0.15), (a1 + 0.15, b1 + 0.15), (a0 - 0.15, b1 + 0.15)]):
        p(f'tower-pinnacle-{k}', 'Main Street Station: clock tower', rect(x - 0.2, x + 0.2, y - 0.2, y + 0.2), SHAFT + 0.3, SHAFT + 1.9, 'stone', 'approximate', PIN, PH,
          shape='inset', levels=[[0, 0, 9], [0.9, 0, 9], [1.6, 0.19, 9]])
    p('tower-clock-stage', 'Main Street Station: clock tower', rect(a0 + 0.3, a1 - 0.3, b0 + 0.3, b1 - 0.3), SHAFT + 0.3, FF + 21.3, 'brick', 'written', TW, TSRC)
    p('tower-entablature', 'Main Street Station: clock tower', rect(a0, a1, b0, b1), FF + 21.3, FF + 21.8, 'stone', 'written',
      'The entablature on the clock stage\'s coupled columns (HABS VA-848). Size approximate.', TSRC)
    p('tower-dome', 'Main Street Station: clock tower', rect(a0 + 0.2, a1 - 0.2, b0 + 0.2, b1 - 0.2), FF + 21.8, FF + 25.4, 'tile', 'written',
      'The tower\'s square dome (HABS VA-848), scaled from photographs: approximate.', TSRC, shape='inset',
      levels=[[0, 0, 9], [0.4, 0.03, 9], [0.8, 0.12, 9], [1.2, 0.27, 9], [1.6, 0.48, 9], [2.0, 0.75, 9], [2.4, 1.1, 9], [2.8, 1.55, 9], [3.2, 2.1, 9], [3.6, 2.9, 9]])
    p('tower-lantern', 'Main Street Station: clock tower', rect(cx - 0.3, cx + 0.3, cb - 0.3, cb + 0.3), FF + 25.3, FF + 25.9, 'stone', 'written',
      'The base of the bronze finial on the dome (HABS VA-848). Size approximate.', TSRC)
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
    HANDS = 'The clock\'s hands; the time they show is arbitrary (approximate).'
    hands = [[r, r, r, r + 0.85, 0.09], [r, r, r + 0.55, r - 0.25, 0.12]]
    p('tower-hands-s', 'Main Street Station: clock', plane(cx - r, b0 + 0.19, cx + r, b0 + 0.19, 0.04), zc - r, zc + r, 'coal', 'approximate', HANDS, TSRC, shape='frame', members=hands)
    p('tower-hands-e', 'Main Street Station: clock', plane(a1 - 0.19, cb - r, a1 - 0.19, cb + r, 0.04), zc - r, zc + r, 'coal', 'approximate', HANDS, TSRC, shape='frame', members=hands)
    # The coupled columns that frame each clock face, drawn as a pier at each corner of its stage.
    for k, (x, y) in enumerate([(a0 + 0.3, b0 + 0.3), (a1 - 0.3, b0 + 0.3), (a1 - 0.3, b1 - 0.3), (a0 + 0.3, b1 - 0.3)]):
        p(f'tower-column-{k}', 'Main Street Station: clock tower', rect(x - 0.42, x + 0.42, y - 0.42, y + 0.42), SHAFT + 0.3, FF + 21.3, 'stone', 'written',
          'Coupled engaged Corinthian columns frame each face of the clock (HABS VA-848); drawn as a plain pier at each corner. Size approximate.', TSRC)
    # Its windows, on the front (on the east side the roof rises past the shaft).
    TWIN = 'A window of the clock tower, as the photographs show them. Places and sizes approximate.'
    for k, (z0, z1, pair) in enumerate([(G + 1.2, G + 3.6, False), (FF + 1.0, FF + 4.0, False), (L2 + 0.6, L2 + 2.6, True), (FF + 12.9, FF + 14.5, True), (FF + 15.1, FF + 16.7, True)]):
        xs = [(cx - 1.25, cx - 0.2), (cx + 0.2, cx + 1.25)] if pair else [(cx - 0.75, cx + 0.75)]
        for j, (x0, x1) in enumerate(xs):
            fb = b0 - (0.17 if z1 <= FF else 0.0)   # in the base, the window stands in its stone
            p(f'tower-window-s-{k}-{j}', 'Main Street Station: clock tower', ring([(x0, fb - 0.05), (x1, fb - 0.05), (x1, fb), (x0, fb)]), z0, z1, 'glass', 'approximate', TWIN, PH)

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
    # The west wall, the one seen behind the stair, in courses of tile (HABS VA-848: "enclosed on
    # either side by tiled walls"); the tile's color is not recorded: drawn buff, like the outside's.
    TILE = SH + ' Its tile is drawn in courses about 0.45 m high; their size and color are approximate.'
    nt = round((FF - 0.5 - G) / 0.45)
    for c in range(nt):
        z0, z1 = G + (FF - 0.5 - G) * c / nt, G + (FF - 0.5 - G) * (c + 1) / nt
        p('stair-wall-w' + ('' if c == 0 else f'-c{c}'), 'Main Street Station: main stairway', rect(STAIR[0] - 0.3, STAIR[0], TOWER[3], HH_N - T), z0, z1, 'brick', 'written', TILE, HABS)
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
    CEIL = 'A beam of the waiting room\'s coffered ceiling (HABS VA-848: "the coffered ceiling in both the waiting room and on the concourse"). The coffers\' size and depth are approximate.'
    for k, b in enumerate([T + 2.6 * i for i in range(1, 7)]):
        p(f'ceiling-beam-a-{k}', WR, rect(STAIR[1] + 0.3, HH_E - T, b - 0.2, b + 0.2), L2 - 1.3, L2 - 0.4, 'plaster', 'written', CEIL, HABS)
    for k, a in enumerate([STAIR[1] + 0.3 + 2.6 * i for i in range(1, 8)]):
        if a > HH_E - T - 0.5:
            continue
        p(f'ceiling-beam-b-{k}', WR, rect(a - 0.15, a + 0.15, T, HH_N - T), L2 - 1.3, L2 - 0.4, 'plaster', 'written', CEIL, HABS)

    # ---- offices above ---------------------------------------------------------------------------------
    OFF = 'Main Street Station: offices'
    CORR = 'A wall of the central corridor that runs east and west on each office floor, offices on either side (HABS VA-848). Its place is approximate.'
    for nm, z0, z1, extra in (('second', L2, CORNICE - 0.5, 0.0), ('third', L3, L4 - 0.35, 0.9), ('fourth', L4, L4 + 2.6, 0.9)):
        if nm == 'second':
            a0, a1 = HH_W + T, HH_E - T
        else:
            a0, a1, _, _ = inset_at(z1, extra)
        for side, b in (('s', 8.95), ('n', 10.7)):
            p(f'corridor-{nm}-{side}', OFF, rect(a0, a1, b - 0.12, b + 0.12), z0, z1, 'plaster', 'written', CORR, HABS,
              within=None if nm == 'second' else 'mss-h-roof')
    DOOR = ('An office door on the corridor: HABS VA-848 says the doors throughout are generally wood with glazed panels. '
            'Their places are approximate.')
    for nm, z0, a_list in (('second', L2, (-13.0, -7.6)), ('third', L3, (-10.6, -7.6)), ('fourth', L4, (-7.6,))):
        for j, a in enumerate(a_list):
            for side, b in (('n', 10.58), ('s', 9.07)):
                fb = (b - 0.04, b) if side == 'n' else (b, b + 0.04)
                p(f'door-{nm}-{side}-{j}', OFF, ring([(a, fb[0]), (a + 0.95, fb[0]), (a + 0.95, fb[1]), (a, fb[1])]), z0, z0 + 2.2, 'wood', 'written', DOOR, HABS,
                  within=None if nm == 'second' else 'mss-h-roof')
                p(f'door-{nm}-{side}-{j}-glass', OFF, ring([(a + 0.15, fb[0] - 0.01), (a + 0.8, fb[0] - 0.01), (a + 0.8, fb[1] + 0.01), (a + 0.15, fb[1] + 0.01)]), z0 + 1.2, z0 + 2.0, 'glass', 'written', DOOR, HABS,
                  within=None if nm == 'second' else 'mss-h-roof')
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
    for k, b in enumerate((F0 + 1.8, F0 + 5.6)):
        p(f'mail-dock-door-{k}', 'Main Street Station: mail room', rect(E0 + 0.6, E0 + 0.64, b, b + 2.6), G, G + 3.0, 'wood', 'written',
          'A loading door from the mail room to its docks on the west side (HABS VA-848: "on the west front ground floor are loading docks for the mail room beneath the concourse"). Number, places and sizes approximate.', HABS)
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
