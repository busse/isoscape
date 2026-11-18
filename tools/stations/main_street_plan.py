"""Main Street Station's head house and concourse, for the cutaway: walls, floors and rooms, the
stair from Main Street, the waiting rooms, the restaurant, the offices, the roof and the tower.

Imported by main_street.py, which passes its `part` and frame helpers and its levels.

The two public floors are traced from the architects' plans printed in The Railroad Gazette of
July 13, 1900 (vol. 32, p. 478: "Entrance Floor" and "Main Floor", Wilson Bros. & Co.), with
their dimensions: the head house 102 ft by 62 ft 4 in, the concourse ("lobby") behind it 82 ft
wide and 34 ft 2 1/2 in deep, the front in a tower bay, five 12-ft bays and an east bay. The
Times (Richmond) of November 24, 1901 describes the finished building room by room in the same
arrangement, so the plans are taken as built. The floors' levels follow the same article's
longitudinal section (p. 479: ground, track, third and fourth floors, attic). Plan feet map onto
OpenStreetMap's outline (way 366226941, 30.5 by 19.64 m), x from the west face, y from the front:

  a = -15.25 + x * 30.5 / 102        b = y * 19.64 / 62.33

The concourse keeps HAER VA-4's depth (sheet 2), to the first truss. What is known only from
HABS VA-848 (1969) and photographs (finishes, the upper floors' partitions, the roof's dormers,
the tower's stages) says so in its note.

How the rooms were used in 1952 is not all recorded: each note says what the 1900 plan and the
1901 description name, and what HABS (1969) found.
"""

import math

S_X, S_Y = 30.5 / 102, 19.64 / 62.33


def X(x):
    """Meters east of the front's middle, for x ft from the west face on the 1900 plans."""
    return -15.25 + x * S_X


def Y(y):
    """Meters back from the front, for y ft from the front on the 1900 plans."""
    return y * S_Y


HH_W, HH_E, HH_N = -15.25, 15.25, 19.64      # the head house (OSM way 366226941)
T = 0.6                                      # outer wall thickness (22 in on the plans)
TOWER = (-15.25, -9.1, 0.0, 6.7)             # a0, a1, b0, b1 (OSM way 366226942)
BAYS = [X(21 + 12 * k) for k in range(6)]    # the front's five 12-ft bays: 21 to 81 ft
ELL = (-12.6, 11.9, HH_N, 30.2)              # the concourse (OSM way 113030476; HAER VA-4, sheet 2: 35 ft deep)
B_GATE = ELL[3]
CUT_A = X(66.7)                                # the cut plane (regions/main-street-station-cutaway.json)


def build(part, rect, ring, plane, SRC, L):
    G, FF, L2, L3, L4 = L['G'], L['FF'], L['L2'], L['L3'], L['L4']
    CORNICE, BAL, RIDGE, FORE = L['CORNICE'], L['BALUSTRADE'], L['RIDGE'], L['FORECOURT']
    HABS = [SRC['habs-data'], SRC['nrhp']]
    PLAN = [SRC['rg-1900'], SRC['times-1901']]
    PH = [SRC['habs-photo-side'], SRC['detroit-east'], SRC['habs-photo-front'], SRC['habs-photo-11']]
    OSM = [SRC['osm-headhouse']]
    HH = 'Main Street Station: head house'
    PLAN_NOTE = ' Traced from the plans in The Railroad Gazette, July 13, 1900 (Wilson Bros. & Co.), which The Times of November 24, 1901 describes as built.'

    def p(id_, name, rg, z0, z1, tone, conf, note, src, **kw):
        part(f'mss-h-{id_}', name, rg, z0, z1, tone, conf, note, src, **kw)

    def box(id_, name, x0, x1, y0, y1, z0, z1, tone, conf, note, src, **kw):
        """A part by plan feet: x from the west face, y from the front."""
        p(id_, name, rect(X(x0), X(x1), Y(y0), Y(y1)), z0, z1, tone, conf, note, src, **kw)

    def pane(id_, name, a0, b0, a1, b1, z0, z1, tone, conf, note, src, d=0.05, **kw):
        """A thin upright pane from (a0, b0) to (a1, b1), d thick."""
        dx, dy = a1 - a0, b1 - b0
        ln = math.hypot(dx, dy)
        na, nb = -dy / ln * d, dx / ln * d
        p(id_, name, ring([(a0, b0), (a1, b1), (a1 + na, b1 + nb), (a0 + na, b0 + nb)]), z0, z1, tone, conf, note, src, **kw)

    HEIGHTS = ' Heights are scaled from photographs (approximate).'
    # ---- outer walls ------------------------------------------------------------------------
    WALL = ('An outer wall of the head house: Kentucky stone to the track floor, Pompeian brick above (The Railroad Gazette, 1900; '
            'HABS VA-848). Its line is OSM\'s, which matches the plan\'s 102 ft by 62 ft 4 in.' + HEIGHTS)
    p('wall-west', HH, rect(HH_W, HH_W + T, TOWER[3], HH_N), G - 0.4, CORNICE - 0.5, 'brick', 'drawn', WALL, PLAN + HABS + OSM + PH)
    p('wall-east', HH, rect(HH_E - T, HH_E, 0, HH_N), G - 0.4, CORNICE - 0.5, 'brick', 'drawn', WALL, PLAN + HABS + OSM + PH)
    # The back wall: solid below the track floor except for the doors to the baggage rooms;
    # above it, the arcade to the concourse.
    p('wall-back-low', HH, rect(HH_W + T, HH_E - T, HH_N - T, HH_N), G - 0.4, FF - 0.5, 'brick', 'drawn', WALL, PLAN + HABS + OSM)
    ARC_TOP = FF + 5.4
    ARC = ('The arcade at the north end of the waiting room, its bays on the front\'s 12-ft lines, its arches glazed with round tracery '
           '(HABS VA-848; HAER photograph VA-4-10): the main stair comes up in its west bay, doors in the next, the news stand in the middle.' + PLAN_NOTE)
    for k, a in enumerate(BAYS):
        p(f'arcade-pier-{k}', 'Main Street Station: arcade to the concourse', rect(a - 0.4, a + 0.4, HH_N - T, HH_N), FF, ARC_TOP, 'stone', 'drawn', ARC, PLAN + HABS)
    for k in range(5):
        a0, a1 = BAYS[k] + 0.4, BAYS[k + 1] - 0.4
        p(f'arcade-arch-{k}', 'Main Street Station: arcade to the concourse', ring([(a0, HH_N - 0.32), (a1, HH_N - 0.32), (a1, HH_N - 0.27), (a0, HH_N - 0.27)]), ARC_TOP - 1.6, ARC_TOP, 'glass', 'drawn', ARC, PLAN + HABS + [SRC['haer-photo-10']], shape='arch')
        if k in (1, 3):
            # Double doors, glazed, in the bays either side of the news stand.
            for j, (u0, u1) in enumerate(((a0 + 0.3, (a0 + a1) / 2 - 0.02), ((a0 + a1) / 2 + 0.02, a1 - 0.3))):
                p(f'arcade-door-{k}-{j}', 'Main Street Station: arcade to the concourse', ring([(u0, HH_N - 0.32), (u1, HH_N - 0.32), (u1, HH_N - 0.27), (u0, HH_N - 0.27)]), FF, FF + 2.9, 'wood', 'drawn', ARC, PLAN)
                p(f'arcade-door-{k}-{j}-glass', 'Main Street Station: arcade to the concourse', ring([(u0 + 0.15, HH_N - 0.33), (u1 - 0.15, HH_N - 0.33), (u1 - 0.15, HH_N - 0.32), (u0 + 0.15, HH_N - 0.32)]), FF + 1.0, FF + 2.6, 'glass', 'drawn', ARC, PLAN)
            p(f'arcade-transom-{k}', 'Main Street Station: arcade to the concourse', ring([(a0, HH_N - 0.32), (a1, HH_N - 0.32), (a1, HH_N - 0.27), (a0, HH_N - 0.27)]), FF + 2.9, ARC_TOP - 1.6, 'glass', 'drawn', ARC, PLAN)
    for side, (a0, a1) in (('w', (HH_W + T, BAYS[0] - 0.4)), ('e', (BAYS[5] + 0.4, HH_E - T))):
        p(f'wall-back-{side}', HH, rect(a0, a1, HH_N - T, HH_N), FF - 0.5, CORNICE - 0.5, 'brick', 'drawn', WALL, PLAN + HABS + OSM)
    p('wall-back-high', HH, rect(BAYS[0] - 0.4, BAYS[5] + 0.4, HH_N - T, HH_N), ARC_TOP, CORNICE - 0.5, 'brick', 'drawn', WALL, PLAN + HABS + OSM)

    # ---- the front, on Main Street ------------------------------------------------------------
    FRONT = ('The Main Street front: the tower\'s bay, five 12-ft bays and an east bay as wide as the tower\'s (the 1900 plans); a five-arch '
             'loggia of rough-hewn stone, five arched openings over it, a 13-bay gallery under the cornice (HABS VA-848).' + HEIGHTS)
    LOG_TOP = G + 4.4
    RUST = ' Its courses are drawn about 0.55 m high, as the photograph shows them roughly (approximate).'
    COURSE = 0.55
    n_c = max(1, round((LOG_TOP - G) / COURSE))
    # The loggia's piers: 3 ft 6 in between 8 ft 6 in arches, on the 12-ft lines (the plan).
    PIER = 3.5 * S_X / 2
    for k, a in enumerate(BAYS):
        a0, a1 = (a - PIER, a + PIER)
        for c in range(n_c):
            z0, z1 = G + (LOG_TOP - G) * c / n_c, G + (LOG_TOP - G) * (c + 1) / n_c
            d = 0.03 if c % 2 == 0 else 0.0
            p(f'loggia-pier-{k}' + ('' if c == 0 else f'-c{c}'), 'Main Street Station: loggia', rect(a0 - d, a1 + d, -d, T), z0, z1, 'stone', 'drawn', FRONT + RUST, PLAN + HABS + PH)
    SPRING, CROWN = G + 3.2, G + 4.0
    ARCH = ('A segmental arch of the loggia, 8 ft 6 in wide (the 1900 plan), in rough-hewn stone (HABS VA-848). Its springing and rise are '
            'scaled from the Detroit Publishing photograph from the east (4a10737): approximate.')
    for k in range(5):
        a0, a1 = BAYS[k] + PIER, BAYS[k + 1] - PIER
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
        p(f'loggia-arch-{k}', 'Main Street Station: loggia', plane(a0, 0, a1, 0, T), G, LOG_TOP, 'stone', 'drawn', ARCH, PLAN + HABS + PH,
          shape='frame', members=plates)
    p('loggia-head', 'Main Street Station: loggia', rect(BAYS[0] - PIER, BAYS[5] + PIER, 0, T), LOG_TOP, FF + 0.9, 'stone', 'drawn', FRONT, PLAN + HABS + PH)
    BALU = ('The balustrade at the foot of the five arched openings over the loggia: columns on pedestals with balusters between (HABS VA-848; '
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
    p('sill-course', 'Main Street Station: string course', rect(BAYS[0] - PIER, HH_E + 0.15, -0.38, 0), FF - 0.25, FF, 'stone', 'written',
      'The stone course that tops the Kentucky stone base along the front, where the brick begins (The Railroad Gazette, 1900: stone "up to the track floor"; the photographs). Its size is approximate.', PLAN + PH)
    p('front-west-low', HH, rect(TOWER[1], BAYS[0] - PIER, 0, T), G, FF + 0.9, 'stone', 'drawn', FRONT, PLAN + HABS + PH)
    p('front-east-low', HH, rect(BAYS[5] + PIER, HH_E, 0, T), G, FF + 0.9, 'stone', 'drawn', FRONT, PLAN + HABS + PH)
    # Over the loggia: wall between five arched openings, glass in them (enclosed by 1952: the
    # upper loggia behind them was open in 1905, Sanborn; enclosed about 1920, BD+C).
    p('front-high', HH, rect(TOWER[1], HH_E, 0, T), FF + 0.9, CORNICE - 0.5, 'brick', 'drawn', FRONT, PLAN + HABS + PH)
    for k in range(5):
        a0, a1 = BAYS[k] + 0.45, BAYS[k + 1] - 0.45
        p(f'front-arcade-{k}', 'Main Street Station: arcade over the loggia', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), FF + 1.2, FF + 4.4, 'glass', 'drawn', FRONT, PLAN + HABS + PH)
        p(f'front-arcade-arch-{k}', 'Main Street Station: arcade over the loggia', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), FF + 4.4, FF + 5.6, 'glass', 'drawn', FRONT, PLAN + HABS + PH, shape='arch')
    # The east bay: one French window on a balcony, a cartouche over it (HABS photograph 12).
    ec = (BAYS[5] + HH_E) / 2
    a0, a1 = ec - 0.75, ec + 0.75
    p('front-french', 'Main Street Station: French window', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), FF + 0.6, FF + 4.6, 'glass', 'written',
      'The French window of the east bay over a small balcony, a cartouche above it (HABS VA-848; HABS photograph VA-848-12). Size approximate.', HABS + PH)
    p('front-balcony', 'Main Street Station: balcony', rect(a0 - 0.5, a1 + 0.5, -0.8, 0), FF + 0.3, FF + 0.6, 'stone', 'written',
      'A small balustraded balcony on consoles under the French window (HABS VA-848). Size approximate.', HABS + PH)
    p('front-cartouche', 'Main Street Station: cartouche', rect(ec - 0.6, ec + 0.6, -0.12, 0), FF + 5.0, FF + 6.2, 'stone', 'written',
      'The carved cartouche over the east bay\'s window (HABS photograph VA-848-12), drawn as a plain panel. Size approximate.', PH, shape='arch')
    for k, (a0, a1) in enumerate(((BAYS[5] + 0.5, BAYS[5] + 1.6), (HH_E - 1.6, HH_E - 0.5))):
        p(f'front-east-window-{k}', 'Main Street Station: window', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), G + 1.0, G + 3.4, 'glass', 'written',
          'A window of the barber shop in the east bay\'s stone base (the 1900 plan puts the barber shop here; HABS photograph VA-848-12 shows the windows). Size approximate.', PLAN + PH)
    gal_w = (HH_E - HH_W) / 13
    for k in range(13):
        a0 = HH_W + k * gal_w + 0.55
        a1 = a0 + gal_w - 1.1
        if a1 <= TOWER[1] + 0.2:
            continue   # the tower's own windows stand there
        p(f'gallery-{k}', 'Main Street Station: gallery window', ring([(a0, -0.06), (a1, -0.06), (a1, -0.02), (a0, -0.02)]), L2 + 0.7, L2 + 2.6, 'glass', 'written',
          'A window of the third floor\'s gallery, 13 bays across the front between engaged Corinthian columns (HABS VA-848). Sizes approximate.', HABS + PH)
        if k < 12:
            ar = HH_W + (k + 1) * gal_w
            if ar > TOWER[1] + 0.2:
                p(f'gallery-pilaster-{k}', 'Main Street Station: gallery', rect(ar - 0.22, ar + 0.22, -0.18, 0), L2 + 0.2, L2 + 3.2, 'stone', 'written',
                  'An engaged column between two gallery windows (HABS VA-848; HABS photograph VA-848-12). Drawn as a plain pilaster; size approximate.', HABS + PH)
    p('belt', 'Main Street Station: belt course', rect(TOWER[1], HH_E + 0.15, -0.15, 0), L2 - 0.15, L2 + 0.15, 'stone', 'written',
      'A stone band across the front at the third floor, as the photographs show it. Its size is approximate.', PH)

    # The cornice and the cresting of terra-cotta roundels over it, round all four sides.
    CORN = ('The shallow entablature round the building (HABS VA-848) and the terra-cotta cresting over it, a row of roundels between '
            'small piers (HABS photographs VA-848-12 and -14), drawn as a pierced band. Projection and heights approximate.')
    TA, TB = TOWER[1], TOWER[3]
    # The back's cornice and cresting in lengths of about 6 m, so each sorts against what stands near it.
    NBK = 5
    backs = [(HH_W - 0.3 + (HH_E - HH_W + 0.6) * i / NBK, HH_W - 0.3 + (HH_E - HH_W + 0.6) * (i + 1) / NBK) for i in range(NBK)]
    for side, rg in ([('s', rect(TA, HH_E + 0.3, -0.3, 0.45))] + [('n' + ('' if i == 0 else f'-p{i}'), rect(u0, u1, HH_N - 0.45, HH_N + 0.3)) for i, (u0, u1) in enumerate(backs)] +
                     [('w', rect(HH_W - 0.3, HH_W + 0.45, TB, HH_N - 0.45)), ('e', rect(HH_E - 0.45, HH_E + 0.3, 0.45, HH_N - 0.45))]):
        p(f'cornice-{side}', 'Main Street Station: cornice', rg, CORNICE - 0.5, CORNICE, 'stone', 'written', CORN, HABS + PH)
    # The cresting on the front: roundels (as rings of short members) between piers.
    span = HH_E - TA
    crest = [[0, 0.04, round(span, 3), 0.04, 0.08], [0, 0.76, round(span, 3), 0.76, 0.08]]
    u = 0.0
    while u <= span + 1e-6:
        crest.append([round(u, 3), 0, round(u, 3), 0.8, 0.14])
        cu = u + 0.5
        if cu < span - 0.2:
            for i in range(8):
                t0, t1 = 2 * math.pi * i / 8, 2 * math.pi * (i + 1) / 8
                crest.append([round(cu + 0.26 * math.cos(t0), 3), round(0.4 + 0.26 * math.sin(t0), 3), round(cu + 0.26 * math.cos(t1), 3), round(0.4 + 0.26 * math.sin(t1), 3), 0.05])
        u += 1.0
    p('balustrade-s', 'Main Street Station: cresting', plane(TA, 0.12, HH_E, 0.12, 0.2), CORNICE, BAL, 'stone', 'written', CORN, HABS + PH, shape='frame', members=crest)
    for side, rg in ([('n' + ('' if i == 0 else f'-p{i}'), rect(max(u0, HH_W), min(u1, HH_E), HH_N - 0.35, HH_N)) for i, (u0, u1) in enumerate(backs)] +
                     [('w', rect(HH_W, HH_W + 0.35, TB, HH_N - 0.35)), ('e', rect(HH_E - 0.35, HH_E, 0.35, HH_N - 0.35))]):
        p(f'balustrade-{side}', 'Main Street Station: cresting', rg, CORNICE, BAL, 'stone', 'written', CORN, HABS + PH)

    # ---- floors ---------------------------------------------------------------------------------
    FL = (' Its level follows the longitudinal section in The Railroad Gazette, July 13, 1900 (ground, track, third and fourth floors, attic), '
          'checked against photographs; to within about half a meter.')
    STAIR = (X(22), X(33.4))                 # the main stair, 12 ft wide between its walls
    S0, S1, S2, S3 = Y(19), Y(36), Y(41.1), HH_N - T   # flight 1, landing, flight 2 (b)
    for k, rg in enumerate((rect(TOWER[1], HH_E - T, T, HH_N - T), rect(HH_W + T, TOWER[1], TOWER[3], HH_N - T))):
        p(f'floor-ground-{k}', 'Main Street Station: ground floor', rg, G - 0.4, G, 'floor', 'drawn',
          'The ground floor ("entrance floor"), raised about 8 ft above the street against floods (The Railroad Gazette, 1900).' + FL, PLAN)
    FIRST = 'The track floor ("main floor"), level with the platforms: the waiting room, the restaurant, the ladies\' retiring room (The Railroad Gazette, 1900).' + FL
    for k, (a0, a1, b0, b1) in enumerate([(HH_W + T, STAIR[0], TOWER[3], HH_N - T), (STAIR[0], STAIR[1], T, S2 - 0.3), (STAIR[1], HH_E - T, T, HH_N - T)]):
        p(f'floor-first-{k}', 'Main Street Station: track floor', rect(a0, a1, b0, b1), FF - 0.5, FF, 'floor', 'drawn', FIRST, PLAN)
    # The floor lights in the upper loggia's floor, over the lower loggia (the plan: "Floor Lights").
    p('floor-lights', 'Main Street Station: floor lights', rect(BAYS[0] + 0.5, BAYS[5] - 0.5, T + 0.3, Y(11.3) - 0.3), FF - 0.02, FF + 0.01, 'glass', 'drawn',
      'Glass floor lights in the floor of the upper loggia, lighting the lower loggia beneath (the 1900 plan).' + PLAN_NOTE, PLAN)
    # The floor stops at the tower's walls, as the ground floor's does.
    for k, rg in enumerate((rect(TOWER[1], HH_E - T, T, HH_N - T), rect(HH_W + T, TOWER[1], TOWER[3], HH_N - T))):
        p('floor-second' + ('' if k == 0 else '-w'), 'Main Street Station: third floor', rg, L2 - 0.4, L2, 'floor', 'drawn',
          'The third floor, the gallery story under the cornice: the two railroads\' offices in 1901 (The Times) and in 1969 (HABS VA-848).' + FL, PLAN + HABS)
    # The roof: a steep hip of red clay tile, springing behind the cresting.
    R0 = (HH_W + 0.6, HH_E - 0.6, 0.6, HH_N - 0.6)
    run = (R0[3] - R0[2]) / 2
    rise = RIDGE - CORNICE
    k_in = run / rise

    def inset_at(z, extra):
        return R0[0] + (z - CORNICE) * k_in + extra, R0[1] - (z - CORNICE) * k_in - extra, R0[2] + (z - CORNICE) * k_in + extra, R0[3] - (z - CORNICE) * k_in - extra

    nc = max(1, round(rise / 1.4))
    roof_levels = [[round(rise * i / nc, 3), round(run * i / nc, 3), round(min(run, run * i / nc + 0.55), 3)] for i in range(nc)]
    roof_levels.append([round(rise, 3), round(run, 3), round(run, 3)])
    for nm, label, z, extra, use in (('third', 'fourth floor', L3, 0.9, 'the Railroad YMCA\'s rooms and the restaurant\'s kitchen in 1901 (The Times); offices by 1969 (HABS VA-848)'),
                                     ('fourth', 'attic', L4, 0.9, 'lit by the upper row of dormers')):
        a0, a1, b0, b1 = inset_at(z, extra)
        # In lengths of about 3 m along the roof, so each sorts against the length of roof over it.
        n_p = max(1, round((a1 - a0) / 3.0))
        for i in range(n_p):
            u0, u1 = a0 + (a1 - a0) * i / n_p, a0 + (a1 - a0) * (i + 1) / n_p
            # The tower stands in the roof's southwest corner: the floor stops at its walls.
            pieces = [(u0, u1, b0)] if u0 >= TOWER[1] else [(u0, min(u1, TOWER[1]), max(b0, TOWER[3]))] + ([(TOWER[1], u1, b0)] if u1 > TOWER[1] else [])
            for q, (v0, v1, c0) in enumerate(pieces):
                p(f'floor-{nm}' + ('' if i == 0 else f'-p{i}') + ('' if q == 0 else '-e'), f'Main Street Station: {label}', rect(v0, v1, c0, b1), z - 0.35, z, 'floor', 'drawn',
                  f'The {label}, in the roof: {use}.' + FL, PLAN + HABS, within='mss-h-roof')
    RIDGE_NOTE = (' Its ridge, about 41.4 m above sea level (some 115 ft over Main Street), runs parallel to the street about 11 m long between '
                  'its finials, as HABS photograph VA-848-10 (1971) shows it; measured on that photograph against the 102-ft front, with '
                  'VA-848-11 and -12 (approximate, to within about 1.5 m). The 1900 section draws the ridge about a meter lower.')
    p('roof', 'Main Street Station: roof', rect(*R0), CORNICE, RIDGE, 'tile', 'written',
      'The very steep hipped roof of dark red tile (The Railroad Gazette, 1900; HABS VA-848), drawn in courses about 1.4 m apart.' + RIDGE_NOTE,
      PLAN + HABS + PH + [SRC['habs-photo-12']], shape='inset', levels=roof_levels)
    for end, ra in (('w', R0[0] + run), ('e', R0[1] - run)):
        p(f'ridge-finial-{end}', 'Main Street Station: roof', rect(ra - 0.14, ra + 0.14, HH_N / 2 - 0.14, HH_N / 2 + 0.14), RIDGE, RIDGE + 3.6, 'iron', 'written',
          'A bronze finial at an end of the ridge (HABS VA-848: "decorative bronze finials appear at each end of the ridge"), drawn as a plain spire. About 3.6 m tall on HABS photograph VA-848-10; its form is approximate.', HABS + PH,
          shape='inset', levels=[[0, 0, 9], [0.6, 0.06, 9], [3.6, 0.139, 9]])
    # The chimney near the east end (HABS photograph VA-848-14: a tall paneled stack).
    ca, cb = HH_E - 3.2, HH_N - 5.0
    CH = L['CHIMNEY_TOP']
    p('chimney', 'Main Street Station: chimney', rect(ca - 0.6, ca + 0.6, cb - 0.6, cb + 0.6), CORNICE, CH, 'brick', 'written',
      'The tall paneled chimney near the east end of the roof (HABS VA-848, photograph 14). Its place along the roof is approximate; its top, about 35.3 m above sea level, is measured on HABS photograph VA-848-10 (approximate).', HABS + PH, over='mss-h-roof')
    p('chimney-cap', 'Main Street Station: chimney', rect(ca - 0.75, ca + 0.75, cb - 0.75, cb + 0.75), CH, CH + 0.4, 'stone', 'written',
      'The chimney\'s cap (HABS photograph VA-848-14). Size approximate.', HABS + PH, over='mss-h-roof')
    # Dormers on the front slope (HABS photographs VA-848-10, -11, -12 and -14), two kinds, each
    # identical wherever it stands:
    # - wall dormers, pedimented, of brick with a stone pediment (as the walls), standing on the cornice over the first, third and
    #   fifth bays, their fronts in the wall's plane;
    # - small hipped dormers of tile set into the slope: one over the second and fourth bays and
    #   one beyond the fifth, a little above the cornice, and an upper row of five on the bay lines.
    # Each is a closed solid that sits on the slope: its cheeks are cut by the roof's plane (a
    # wedge for a dormer in the slope), so nothing sinks below the tiles or floats above them, and
    # they stand over the roof's shell in the paint order. None straddles the cut plane.
    DORM = ('A dormer on the roof\'s front, of two kinds: pedimented wall dormers of brick and stone on the cornice over the first, third and fifth bays, '
            'and small hipped tile dormers set into the slope between them and in an upper row of five (HABS VA-848; HABS photographs VA-848-10, '
            '-11, -12 and -14). Their places and heights are measured on VA-848-10 against the 102-ft front (approximate); drawn plain, '
            'without the consoles and spires.')
    DS = HABS + PH + [SRC['habs-photo-12']]

    def on_roof(z):
        """How far back from the front the front slope stands at height z."""
        return R0[2] + (z - CORNICE) * k_in

    mids = [(BAYS[k] + BAYS[k + 1]) / 2 for k in range(5)]
    # Wall dormers: the body on the cornice, its cheeks running back to the slope.
    WP, WH, CAP = 0.85, 2.9, 1.3
    for j, c in enumerate(mids[0::2]):
        z0, z1 = CORNICE, CORNICE + WH
        b0 = 0.02
        ub, ur = on_roof(z1) - b0, on_roof(z0) - b0
        p(f'dormer-0-{j}', 'Main Street Station: dormer', plane(c + WP, b0, c + WP, b0 + ub, 2 * WP), z0, z1, 'brick', 'written', DORM, DS,
          shape='frame', members=[[0, 0, 0, round(WH, 3), round(ub, 3), round(WH, 3), round(ur, 3), 0]], over='mss-h-roof')
        p(f'dormer-0-{j}-pediment', 'Main Street Station: dormer', plane(c - WP - 0.1, b0 - 0.12, c + WP + 0.1, b0 - 0.12, 0.3), z1, z1 + CAP, 'stone', 'written', DORM, DS,
          shape='frame', members=[[0, 0, round(2 * WP + 0.2, 3), 0, round(WP + 0.1, 3), CAP]], over='mss-h-roof')
        # Its roof, hipped back from the pediment to the slope.
        p(f'dormer-0-{j}-roof', 'Main Street Station: dormer', rect(c - WP - 0.05, c + WP + 0.05, b0 + 0.18, b0 + ub), z1, z1 + CAP, 'tile', 'written', DORM, DS,
          shape='inset', levels=[[0, 0, 9], [CAP, WP + 0.05, 9]], over='mss-h-roof')
        p(f'dormer-0-{j}-glass', 'Main Street Station: dormer', ring([(c - 0.45, b0 - 0.04), (c + 0.45, b0 - 0.04), (c + 0.45, b0), (c - 0.45, b0)]), z0 + 0.9, z1 - 0.4, 'glass', 'written', DORM, DS, over='mss-h-roof')
    # Hipped dormers in the slope: a wedge whose cheeks are triangles on the tiles, a pyramid cap.
    HW, HH, HC = 0.5, 1.6, 1.4
    slope = [(c, CORNICE + 1.0) for c in (mids[1], mids[3], mids[4] + (mids[4] - mids[3]))] + [(BAYS[k], CORNICE + 4.5) for k in (1, 2, 3, 4, 5)]
    for j, (c, z0) in enumerate(slope):
        row = 1 if j < 3 else 2
        z1 = z0 + HH
        bf = on_roof(z0) - 0.05
        ub = on_roof(z1) - bf
        k = j if row == 1 else j - 3
        p(f'dormer-{row}-{k}', 'Main Street Station: dormer', plane(c + HW, bf, c + HW, bf + ub, 2 * HW), z0, z1, 'tile', 'written', DORM, DS,
          shape='frame', members=[[0, 0, 0, HH, round(ub, 3), HH]], over='mss-h-roof')
        p(f'dormer-{row}-{k}-roof', 'Main Street Station: dormer', rect(c - HW - 0.08, c + HW + 0.08, bf - 0.08, bf + ub), z1, z1 + HC, 'tile', 'written', DORM, DS,
          shape='inset', levels=[[0, 0, 9], [HC, HW + 0.08, 9]], over='mss-h-roof')
        p(f'dormer-{row}-{k}-glass', 'Main Street Station: dormer', ring([(c - 0.25, bf - 0.04), (c + 0.25, bf - 0.04), (c + 0.25, bf), (c - 0.25, bf)]), z0 + 0.3, z1 - 0.25, 'coal', 'written', DORM, DS, over='mss-h-roof')

    # ---- the clock tower ------------------------------------------------------------------------
    # Its stages are measured in round 4 on HABS photographs VA-848-10, -11 and -12 (1971) against
    # the 102-ft front (main_street.py, levels): a plain shaft to a corbelled balcony, a clock stage
    # with coupled columns at its corners, an entablature, a low drum and a ribbed dome about half
    # the clock stage's height, and the finial. The Railroad Gazette (1900), before construction,
    # gave the tower as 110 ft high, beside a perspective whose tower differs from the one built;
    # as photographed its finial is about 148 ft over Main Street, and Sanborn's "Clock Tower 90'"
    # (1905, 1952) fits its shaft, about 90 ft over the ground floor.
    TW = ('The clock tower at the southwest corner, with a clock face on each side (The Railroad Gazette, 1900; HABS VA-848). Its outline is '
          'OSM\'s. Its stages are measured on HABS photographs VA-848-10, -11 and -12 (1971) against the 102-ft front, approximate to within '
          'about 1.5 m: the shaft to about 90 ft over the ground floor, as the Sanborn atlases (1905, 1952) mark it ("Clock Tower 90\'"), '
          'the finial about 148 ft over Main Street. The 110 ft in The Railroad Gazette (1900) was written before the station was built, '
          'beside a perspective whose tower differs from the one built; it does not fit the photographs.')
    TSRC = PLAN + HABS + [SRC['archipedia'], SRC['osm-tower'], SRC['habs-photo-12'], SRC['habs-photo-1971'], SRC['sanborn-1905'], SRC['sanborn-1952']] + PH
    a0, a1, b0, b1 = TOWER
    SHAFT, ZC, R = L['TOWER_SHAFT'], L['CLOCK_Z'], L['CLOCK_R']
    STAGE, DRUM, DOME, FINIAL = L['STAGE_TOP'], L['DRUM_TOP'], L['DOME_TOP'], L['FINIAL_TOP']
    cx, cb = (a0 + a1) / 2, (b0 + b1) / 2
    p('tower', 'Main Street Station: clock tower', rect(a0, a1, b0, b1), G - 0.4, SHAFT - 1.4, 'brick', 'written', TW, TSRC)
    TB_ = 'The rusticated stone base of the tower, as the front\'s base continues round it (HABS VA-848; Detroit Publishing 4a10737). Courses about 0.55 m, approximate.'
    nb = round((FF - G + 0.4) / 0.55)
    for c in range(nb):
        z0, z1 = G - 0.4 + (FF - G + 0.4) * c / nb, G - 0.4 + (FF - G + 0.4) * (c + 1) / nb
        d = 0.1 if c % 2 == 0 else 0.07
        sides = [rect(a0 - d, a1 + d, b0 - d, b0 + 0.3), rect(a1 - 0.3, a1 + d, b0 + 0.3, 3.5)]
        for j, rg in enumerate(sides):
            p(f'tower-base-{c}-{j}', 'Main Street Station: clock tower', rg, z0, z1, 'stone', 'written', TB_, TSRC)
    BAND = 'A stone band round the tower between its stages, as the photographs show them. Places approximate.'
    # The bands stop at the tower's back, where the head house's floors meet it.
    for k, zb in enumerate((L2 + 0.1, FF + 11.6)):
        p(f'tower-band-{k}', 'Main Street Station: clock tower', rect(a0 - 0.15, a1 + 0.15, b0 - 0.15, b1), zb, zb + 0.3, 'stone', 'approximate', BAND, PH)
    # From the balcony up, the tower's parts stand over the roof's shell: the roof's footprint takes in
    # the tower's, so without it they would sort by depth against the roof, inside the tower.
    BALC = ('The balcony at the shaft\'s top, on a corbel table, with a balustrade round the clock stage (HABS photographs VA-848-10 to -12; '
            'Detroit Publishing 4a10737). Its height is measured on VA-848-10 (approximate); its corbels and balustrade are drawn plain.')
    p('tower-corbels', 'Main Street Station: clock tower', rect(a0 - 0.2, a1 + 0.2, b0 - 0.2, b1 + 0.2), SHAFT - 1.4, SHAFT - 0.2, 'stone', 'written', BALC, TSRC, over='mss-h-roof')
    # The balcony's floor and its balustrade, drawn as one solid band: four thin rails, each with a
    # footprint of its own, would sort against the roof's shell one by one.
    p('tower-cornice', 'Main Street Station: clock tower', rect(a0 - 0.4, a1 + 0.4, b0 - 0.4, b1 + 0.4), SHAFT - 0.2, SHAFT + 0.75, 'stone', 'written', BALC, TSRC, over='mss-h-roof')
    PIN = 'A pinnacle at a corner of the balcony under the clock stage, as the Detroit Publishing photographs show them. Size approximate.'
    for k, (x, y) in enumerate([(a0 - 0.2, b0 - 0.2), (a1 + 0.2, b0 - 0.2), (a1 + 0.2, b1 + 0.2), (a0 - 0.2, b1 + 0.2)]):
        p(f'tower-pinnacle-{k}', 'Main Street Station: clock tower', rect(x - 0.15, x + 0.15, y - 0.15, y + 0.15), SHAFT + 0.75, SHAFT + 2.15, 'stone', 'approximate', PIN, PH,
          shape='inset', levels=[[0, 0, 9], [0.7, 0, 9], [1.4, 0.14, 9]], over='mss-h-roof')
    p('tower-clock-stage', 'Main Street Station: clock tower', rect(a0 + 0.3, a1 - 0.3, b0 + 0.3, b1 - 0.3), SHAFT + 0.75, STAGE, 'brick', 'written', TW, TSRC, over='mss-h-roof')
    p('tower-entablature', 'Main Street Station: clock tower', rect(a0 - 0.1, a1 + 0.1, b0 - 0.1, b1 + 0.1), STAGE, STAGE + 0.5, 'stone', 'written',
      'The entablature on the clock stage\'s coupled columns (HABS VA-848), its top measured on HABS photograph VA-848-10. Size approximate.', TSRC, over='mss-h-roof')
    # The drum and the dome are round, sixteen-sided: HABS VA-848 calls the dome square, but the
    # photographs (VA-848-10, -11, -13) show a full, ribbed bell, rounder than a square cap; its
    # sixteen gores stand for the ribs. The dome's crown is about half the clock stage's height
    # above its foot (VA-848-10: dome and drum 51 px over a 91-px clock stage).
    def gon(rad, n=16):
        return ring([(cx + rad * math.cos(2 * math.pi * (i + 0.5) / n), cb + rad * math.sin(2 * math.pi * (i + 0.5) / n)) for i in range(n)])
    R_DOME = (a1 - a0) / 2 - 0.45
    p('tower-drum', 'Main Street Station: clock tower', gon(R_DOME + 0.1), STAGE + 0.5, DRUM, 'stone', 'written',
      'The low round base of the dome over the entablature (HABS photographs VA-848-10 and -13). Height measured on VA-848-10 (approximate).', TSRC,
      shape='revolve', levels=[[0, 1, 0], [round(DRUM - STAGE - 0.5, 3), 1, 0]], over='mss-h-roof')
    H = DOME - DRUM
    dome = [[round(H * k / 8, 3), round(max(0.1, math.sqrt(max(0.0, 1 - (k / 8) ** 2))), 3), 0] for k in range(9)]
    p('tower-dome', 'Main Street Station: clock tower', gon(R_DOME), DRUM, DOME, 'tile', 'written',
      'The tower\'s ribbed dome of tile (HABS VA-848, "square dome"; HABS photographs VA-848-10, -11 and -13 show it full and rounded), drawn '
      'round in sixteen gores; its crown about 48.7 m above sea level, measured on VA-848-10 against the 102-ft front: approximate.', TSRC,
      shape='revolve', levels=dome, over='mss-h-roof')
    p('tower-lantern', 'Main Street Station: clock tower', rect(cx - 0.35, cx + 0.35, cb - 0.35, cb + 0.35), DOME, DOME + 0.6, 'stone', 'written',
      'The base of the bronze finial on the dome (HABS VA-848). Size approximate.', TSRC, over='mss-h-roof')
    p('tower-finial', 'Main Street Station: clock tower', rect(cx - 0.22, cx + 0.22, cb - 0.22, cb + 0.22), DOME + 0.6, FINIAL, 'iron', 'written',
      'The bronze finial (HABS VA-848), drawn as a plain spire; its tip about 148 ft over Main Street, measured on HABS photographs VA-848-10 '
      'and -12 against the 102-ft front (approximate, to within about 8 ft). The Railroad Gazette (1900, before the station was built) and SAH Archipedia give '
      '110 ft, which does not fit the photographs. Its form is approximate.', TSRC,
      shape='inset', levels=[[0, 0, 9], [0.8, 0.05, 9], [round(FINIAL - DOME - 0.6, 3), 0.219, 9]], over='mss-h-roof')
    r = R
    disc = []
    for i in range(20):
        t = 2 * math.pi * i / 20
        disc += [round(r + r * math.cos(t), 3), round(r + r * math.sin(t), 3)]
    CLK = ('A clock face, one on each of the tower\'s four sides (The Railroad Gazette, 1900; HABS VA-848). About 9 ft across with its bezel and '
           'its center about 40.3 m above sea level, measured on HABS photographs VA-848-10 and -12 (approximate).')
    p('tower-clock-s', 'Main Street Station: clock', plane(cx - r, b0 + 0.26, cx + r, b0 + 0.26, 0.04), ZC - r, ZC + r, 'plaster', 'written', CLK, TSRC, shape='frame', members=[disc], over='mss-h-roof')
    p('tower-clock-e', 'Main Street Station: clock', plane(a1 - 0.26, cb - r, a1 - 0.26, cb + r, 0.04), ZC - r, ZC + r, 'plaster', 'written', CLK, TSRC, shape='frame', members=[disc], over='mss-h-roof')
    HANDS = 'The clock\'s hands; the time they show is arbitrary (approximate).'
    hands = [[r, r, r, round(r + 0.74 * r, 3), 0.1], [r, r, round(r + 0.48 * r, 3), round(r - 0.22 * r, 3), 0.13]]
    p('tower-hands-s', 'Main Street Station: clock', plane(cx - r, b0 + 0.19, cx + r, b0 + 0.19, 0.04), ZC - r, ZC + r, 'coal', 'approximate', HANDS, TSRC, shape='frame', members=hands, over='mss-h-roof')
    p('tower-hands-e', 'Main Street Station: clock', plane(a1 - 0.19, cb - r, a1 - 0.19, cb + r, 0.04), ZC - r, ZC + r, 'coal', 'approximate', HANDS, TSRC, shape='frame', members=hands, over='mss-h-roof')
    for k, (x, y) in enumerate([(a0 + 0.42, b0 + 0.42), (a1 - 0.42, b0 + 0.42), (a1 - 0.42, b1 - 0.42), (a0 + 0.42, b1 - 0.42)]):
        p(f'tower-column-{k}', 'Main Street Station: clock tower', rect(x - 0.42, x + 0.42, y - 0.42, y + 0.42), SHAFT + 0.75, STAGE, 'stone', 'written',
          'Coupled engaged Corinthian columns frame each face of the clock (HABS VA-848); drawn as a plain pier at each corner. Size approximate.', TSRC, over='mss-h-roof')
    TWIN = ('A window of the clock tower, as the photographs show them: single at the ground and first floors, paired above. Heights '
            'measured on HABS photograph VA-848-10 (approximate).')
    for k, (z0, z1, pair) in enumerate([(G + 1.2, G + 3.6, False), (FF + 1.0, FF + 4.0, False), (L2 + 0.6, L2 + 2.6, True), (FF + 12.6, FF + 15.0, True), (FF + 16.8, FF + 19.2, True)]):
        xs = [(cx - 1.25, cx - 0.2), (cx + 0.2, cx + 1.25)] if pair else [(cx - 0.75, cx + 0.75)]
        for j, (x0, x1) in enumerate(xs):
            fb = b0 - (0.17 if z1 <= FF else 0.0)
            p(f'tower-window-s-{k}-{j}', 'Main Street Station: clock tower', ring([(x0, fb - 0.05), (x1, fb - 0.05), (x1, fb), (x0, fb)]), z0, z1, 'glass', 'approximate', TWIN, PH)

    # ---- the steps and the lower loggia ---------------------------------------------------------------
    p('front-steps', 'Main Street Station: steps from Main Street', ring([(BAYS[0], -4.0), (BAYS[5], -4.0), (BAYS[5], 0.0), (BAYS[0], 0.0)]), FORE, G, 'stone', 'written',
      'The wide stairway up from the Main Street sidewalk to the loggia (The Times, 1901; the 1905 Sanborn map draws it across the middle bays; Detroit Publishing 4a10737). The number of steps is approximate.',
      [SRC['times-1901'], SRC['sanborn-1905'], SRC['detroit-east']], shape='stair', steps=8)
    LOG = ('The lower loggia\'s back wall, 10 ft behind the arches, with doors in its 12-ft bays: in the west bay to the main stair, in the '
           'third and fourth to the lower waiting room; the second bay is the ticket office\'s end.' + PLAN_NOTE)
    LB = Y(12.6)
    p('loggia-back', 'Main Street Station: loggia', rect(BAYS[0], BAYS[5], LB, LB + 0.35), G, FF - 0.5, 'brick', 'drawn', LOG, PLAN)
    for k in (0, 2, 3):
        a0, a1 = BAYS[k] + 0.7, BAYS[k + 1] - 0.7
        p(f'loggia-door-{k}', 'Main Street Station: loggia door', ring([(a0, LB - 0.04), (a1, LB - 0.04), (a1, LB), (a0, LB)]), G, G + 3.0, 'wood', 'drawn', LOG, PLAN)
        p(f'loggia-transom-{k}', 'Main Street Station: loggia door', ring([(a0, LB - 0.04), (a1, LB - 0.04), (a1, LB), (a0, LB)]), G + 3.0, G + 4.0, 'glass', 'drawn', LOG, PLAN, shape='arch')

    # ---- the entrance floor: drug store, main stair, ticket office, lower waiting room ---------------
    EF = 'Main Street Station: entrance floor'
    DRUG = ('The drug store, the west room of the entrance floor, with its prescription department behind; in 1901 it opened on the loggia and Main Street.'
            ' Its use in 1952 is not recorded.' + PLAN_NOTE)
    box('drug-wall-e', 'Main Street Station: drug store', 20.1, 22, 2, 62, G, FF - 0.5, 'plaster', 'drawn', DRUG, PLAN)
    box('drug-partition', 'Main Street Station: drug store', 2, 20.1, 36.4, 36.8, G, G + 2.6, 'wood', 'drawn', DRUG, PLAN)
    box('drug-wall-n', 'Main Street Station: drug store', 2, 20.1, 39.5, 40.2, G, FF - 0.5, 'plaster', 'drawn',
        'The wall between the drug store and the general service stair and elevator, which served the upper floors and the carriage concourse.' + PLAN_NOTE, PLAN)
    for k, (y0, y1) in enumerate(((4, 33),)):
        box(f'drug-counter-{k}', 'Main Street Station: drug store', 14.5, 16.5, y0, y1, G, G + 1.0, 'wood', 'approximate',
            'A counter in the drug store. The plan names the room but draws no fittings; this counter is approximate.', PLAN)
    SH = ('The main stair, 12 ft wide, straight up from the lower loggia to the track floor with a landing halfway, between walls '
          '(The Railroad Gazette, 1900: "entrance stairs"; The Times, 1901: a handsome landing "entirely finished in marble"; HABS VA-848: tiled walls).'
          ' The number of treads is approximate.')
    TILE = SH + ' Its wall tile is drawn in courses about 0.45 m high; their size and color are approximate.'
    nt = round((FF - 0.5 - G) / 0.45)
    for c in range(nt):
        z0, z1 = G + (FF - 0.5 - G) * c / nt, G + (FF - 0.5 - G) * (c + 1) / nt
        p('stair-wall-w' + ('' if c == 0 else f'-c{c}'), 'Main Street Station: main stair', rect(STAIR[0] - 0.12, STAIR[0], LB + 0.35, HH_N - T), z0, z1, 'plaster', 'drawn', TILE, PLAN + HABS)
    p('stair-wall-e', 'Main Street Station: main stair', rect(STAIR[1], STAIR[1] + 0.33, LB + 0.35, Y(53.3)), G, FF - 0.5, 'plaster', 'drawn', SH, PLAN + HABS)
    sa0, sa1 = STAIR[0], STAIR[1]
    mid = G + (FF - G) / 2
    p('stair-1', 'Main Street Station: main stair', ring([(sa0, S0), (sa1, S0), (sa1, S1), (sa0, S1)]), G, mid, 'stone', 'drawn', SH, PLAN + HABS, shape='stair', steps=19)
    p('stair-landing', 'Main Street Station: main stair', rect(sa0, sa1, S1, S2), mid - 0.3, mid, 'stone', 'drawn', SH, PLAN + HABS)
    p('stair-2', 'Main Street Station: main stair', ring([(sa0, S2), (sa1, S2), (sa1, S3), (sa0, S3)]), mid, FF, 'stone', 'drawn', SH, PLAN + HABS, shape='stair', steps=19)
    # The ticket office: a counter with three 10-ft windows facing the lower waiting room.
    TK = ('The ticket office, on the west side of the lower waiting room: a counter with three 10-ft windows, its ends canted, a ticket '
          'storage vault behind (The Railroad Gazette, 1900; The Times, 1901: the lower waiting room "flanked on one side by the ticket office"). '
          'HABS (1969) found the tickets sold in the concourse by then; where they were sold in 1952 is not recorded.')
    TKS = 'Main Street Station: ticket office'
    TX0, TX1 = 34.5, 43.6
    box('ticket-vault', TKS, 33.4, TX1, 53.3, 56.6, G, G + 3.2, 'plaster', 'drawn', TK, PLAN)
    box('ticket-ceiling', TKS, TX0, TX1, 20.3, 53.3, G + 3.2, G + 3.4, 'plaster', 'drawn', TK, PLAN)
    # Its front: the canted ends and the counter between them, a grille over the counter.
    a_f = X(TX1)
    for k, (y0, y1, x0) in enumerate(((20.3, 23.8, TX0), (49.8, 53.3, TX0))):
        pane(f'ticket-end-{k}', TKS, X(TX1 - 1.4), Y(y1 if k == 0 else y0), a_f, Y(y0 + 1.6 if k == 0 else y1 - 1.6), G, G + 3.2, 'wood', 'drawn', TK, PLAN, d=0.12)
        box(f'ticket-side-{k}', TKS, TX0, TX1 - 1.4, (y0 if k == 0 else y1 - 0.4), (y0 + 0.4 if k == 0 else y1), G, G + 3.2, 'wood', 'drawn', TK, PLAN)
    yw = [23.8 + (49.8 - 23.8) * i / 3 for i in range(4)]
    box('ticket-counter', TKS, TX1 - 0.9, TX1, 23.8, 49.8, G, G + 1.1, 'stone', 'drawn', TK + ' The counter\'s marble is from the 1900 text (marble wainscot); its height is approximate.', PLAN)
    box('ticket-head', TKS, TX1 - 0.4, TX1, 23.8, 49.8, G + 2.6, G + 3.2, 'wood', 'drawn', TK, PLAN)
    for k in range(3):
        y0, y1 = yw[k], yw[k + 1]
        box(f'ticket-mullion-{k}', TKS, TX1 - 0.4, TX1, y0 - 0.2, y0 + 0.2, G + 1.1, G + 2.6, 'wood', 'drawn', TK, PLAN)
        grille = []
        n_b = 14
        for i in range(n_b + 1):
            u = (Y(y1) - Y(y0) - 0.3) * i / n_b
            grille.append([round(u, 3), 0, round(u, 3), 1.5, 0.025])
        p(f'ticket-grille-{k}', TKS, plane(a_f - 0.05, Y(y0) + 0.15, a_f - 0.05, Y(y1) - 0.15, 0.03), G + 1.1, G + 2.6, 'iron', 'drawn',
          TK + ' Each window is drawn with a grille of plain bars; its pattern is approximate.', PLAN, shape='frame', members=grille)
        # A ticket case behind each window (approximate fittings).
        box(f'ticket-case-{k}', TKS, TX0 + 0.3, TX0 + 2.0, y0 + 1.0, y1 - 1.0, G, G + 2.2, 'wood', 'approximate',
            'A case for tickets against the office\'s back wall. The plan draws no fittings: approximate.', PLAN)
    box('ticket-mullion-3', TKS, TX1 - 0.4, TX1, 49.6, 50.0, G + 1.1, G + 2.6, 'wood', 'drawn', TK, PLAN)
    LW = ('The lower waiting room, 1,900 sq ft, between the ticket office and the elevator and Pullman ticket office, the baggage and express '
          'rooms behind it (The Railroad Gazette, 1900; The Times, 1901). Its benches are not drawn on the plan.')
    # Its north wall, with doors to the baggage room and to the wagon passage.
    for k, (x0, x1) in enumerate(((33.4, 35.5), (43.5, 47.5), (55.5, 58.5), (66.5, 70))):
        box(f'lower-wall-n-{k}', 'Main Street Station: lower waiting room', x0, x1, 61.6, 62.33, G, FF - 0.5, 'brick', 'drawn', LW, PLAN)
    for k, (x0, x1) in enumerate(((35.5, 43.5), (47.5, 55.5), (58.5, 66.5))):
        box(f'lower-door-{k}', 'Main Street Station: lower waiting room', x0, x1, 61.7, 61.8, G, G + 2.9, 'wood', 'drawn', LW, PLAN)
        box(f'lower-door-head-{k}', 'Main Street Station: lower waiting room', x0, x1, 61.6, 62.33, G + 2.9, FF - 0.5, 'brick', 'drawn', LW, PLAN)

    # ---- the track floor: waiting room, restaurant ------------------------------------------------------
    WR = 'Main Street Station: waiting room'
    WRN = ('The general waiting room, about 2,200 sq ft: five 12-ft bays across, two rows of free-standing columns 12 ft in from each side, '
           'three long double benches across its middle, a coffered ceiling (HABS VA-848), marble columns, wainscot and floor (The Railroad Gazette, 1900).')
    for k, y in enumerate((21.2, 31.6)):
        box(f'column-w-{k}', WR, 32.4 - 1.0, 32.4 + 1.0, y - 1.0, y + 1.0, FF, L2 - 1.3, 'stone', 'drawn', WRN + PLAN_NOTE, PLAN + HABS)
        box(f'column-w-{k}-cap', WR, 32.4 - 1.4, 32.4 + 1.4, y - 1.4, y + 1.4, L2 - 1.9, L2 - 1.3, 'stone', 'drawn', WRN, PLAN + HABS)
        box(f'column-w-{k}-base', WR, 32.4 - 1.3, 32.4 + 1.3, y - 1.3, y + 1.3, FF, FF + 0.5, 'stone', 'drawn', WRN, PLAN + HABS)
    BENCH = ('A long double bench, back to back, one of three across the general waiting room (the 1900 plan). Seat and back heights are approximate.' + PLAN_NOTE)
    for k, y in enumerate((21.2, 31.6, 41.1)):
        box(f'bench-{k}', WR, 40.5, 62.4, y - 1.5, y + 1.5, FF, FF + 0.45, 'wood', 'drawn', BENCH, PLAN)
        box(f'bench-{k}-back', WR, 40.5, 62.4, y - 0.15, y + 0.15, FF + 0.45, FF + 1.05, 'wood', 'drawn', BENCH, PLAN)
        for e, x in enumerate((40.5, 62.4)):
            box(f'bench-{k}-arm-{e}', WR, x - 0.3 if e else x, x if e else x + 0.3, y - 1.5, y + 1.5, FF + 0.45, FF + 0.75, 'wood', 'drawn', BENCH, PLAN)
    NEWS = ('The news stand and parcel delivery, set in the middle bay of the arcade between the waiting room and the concourse, opening on both '
            '(the 1900 plan). Its height is approximate.')
    box('news-stand', WR, 46.5, 56.6, 59.3, 65.6, FF, FF + 1.1, 'wood', 'drawn', NEWS, PLAN)
    box('news-stand-glass', WR, 46.8, 56.3, 59.6, 65.3, FF + 1.1, FF + 2.2, 'glass', 'drawn', NEWS, PLAN)
    box('news-stand-top', WR, 46.3, 56.8, 59.1, 65.8, FF + 2.2, FF + 2.5, 'wood', 'drawn', NEWS, PLAN)
    # The screen on the waiting room's west side: columns with glazed arches, toward the restaurant.
    SCR = ('The screen on the waiting room\'s west side, toward the restaurant and dining room: columns, with glazing set in arches between them '
           '(HABS VA-848; the 1970 nomination calls it a large colonnaded glass screen). The 1900 plan puts its columns on the 12-ft grid.')
    sx = X(21)
    cols = [Y(11.3), Y(21.2), Y(31.6), Y(41.5)]
    for k, b in enumerate(cols):
        p(f'screen-column-{k}', WR, rect(sx - 0.3, sx + 0.3, b - 0.3, b + 0.3), FF, FF + 5.0, 'stone', 'drawn', SCR, PLAN + HABS)
    for k in range(len(cols) - 1):
        b0, b1 = cols[k] + 0.32, cols[k + 1] - 0.32
        p(f'screen-glass-{k}', WR, ring([(sx, b0), (sx, b1), (sx - 0.05, b1), (sx - 0.05, b0)]), FF + 0.9, FF + 3.6, 'glass', 'written', SCR, PLAN + HABS)
        p(f'screen-arch-{k}', WR, ring([(sx, b0), (sx, b1), (sx - 0.05, b1), (sx - 0.05, b0)]), FF + 3.6, FF + 5.0, 'glass', 'written', SCR, PLAN + HABS, shape='arch')
        p(f'screen-dado-{k}', WR, ring([(sx + 0.05, b0), (sx + 0.05, b1), (sx - 0.1, b1), (sx - 0.1, b0)]), FF, FF + 0.9, 'stone', 'written', SCR, PLAN + HABS)
    p('screen-head', WR, rect(sx - 0.3, sx + 0.3, cols[0], cols[-1]), FF + 5.0, L2 - 0.4, 'plaster', 'drawn', SCR, PLAN + HABS)
    # The waiting room's front: an inner arcade 10 ft behind the front, the upper loggia between.
    FL2 = ('The waiting room\'s front wall, an arcade on the 12-ft lines 10 ft behind the front; between them the upper loggia, with floor lights '
           '(the 1900 plan; the 1905 Sanborn map marks the front open on both floors; enclosed by the 1920s, BD+C). Glazing approximate.')
    yb = Y(11.3)
    for k, a in enumerate(BAYS):
        p(f'inner-pier-{k}', WR, rect(a - 0.35, a + 0.35, yb - 0.3, yb + 0.3), FF, L2 - 0.4, 'stone', 'drawn', FL2, PLAN + [SRC['sanborn-1905'], SRC['bdc']])
    for k in range(5):
        a0, a1 = BAYS[k] + 0.35, BAYS[k + 1] - 0.35
        p(f'inner-glass-{k}', WR, ring([(a0, yb), (a1, yb), (a1, yb + 0.04), (a0, yb + 0.04)]), FF, FF + 4.0, 'glass', 'approximate', FL2, PLAN)
        p(f'inner-arch-{k}', WR, ring([(a0, yb), (a1, yb), (a1, yb + 0.04), (a0, yb + 0.04)]), FF + 4.0, FF + 5.4, 'glass', 'approximate', FL2, PLAN, shape='arch')
    p('inner-head', WR, rect(BAYS[0], BAYS[5], yb - 0.3, yb + 0.3), FF + 5.4, L2 - 0.4, 'plaster', 'drawn', FL2, PLAN)
    # The main stair's well: a balustrade round it on the track floor.
    WELL = 'The balustrade round the main stair\'s well on the track floor, where the stair comes up beside the concourse (the 1900 plan). Its pattern is approximate.'
    for k, (a0, b0, a1, b1) in enumerate(((STAIR[0], S2 - 0.3, STAIR[1] + 0.3, S2 - 0.3), (STAIR[1] + 0.3, S2 - 0.3, STAIR[1] + 0.3, HH_N - T))):
        ln = math.hypot(a1 - a0, b1 - b0)
        bal = [[0, 0.05, round(ln, 3), 0.05, 0.1], [0, 0.95, round(ln, 3), 0.95, 0.12]]
        u = 0.15
        while u < ln - 0.1:
            bal.append([round(u, 3), 0.1, round(u, 3), 0.9, 0.06])
            u += 0.25
        p(f'well-rail-{k}', 'Main Street Station: main stair', plane(a0, b0, a1, b1, 0.12), FF, FF + 1.0, 'stone', 'drawn', WELL, PLAN, shape='frame', members=bal)
    p('well-column', 'Main Street Station: main stair', rect(STAIR[1] - 0.05, STAIR[1] + 0.65, S2 - 0.65, S2 + 0.05), FF, L2 - 1.3, 'stone', 'drawn', WRN, PLAN)
    # The coffered ceiling: beams both ways under the third floor.
    CEIL = 'A beam of the waiting room\'s coffered ceiling (HABS VA-848: "the coffered ceiling in both the waiting room and on the concourse"). Laid on the 12-ft grid of the 1900 plan; depth approximate.'
    for k, y in enumerate((11.3, 21.2, 31.6, 41.1, 51.5)):
        p(f'ceiling-beam-a-{k}', WR, rect(X(21), HH_E - T, Y(y) - 0.2, Y(y) + 0.2), L2 - 1.3, L2 - 0.4, 'plaster', 'written', CEIL, PLAN + HABS)
    for k, x in enumerate((27, 33, 39, 45, 51, 57, 63, 69, 75)):
        p(f'ceiling-beam-b-{k}', WR, rect(X(x) - 0.12, X(x) + 0.12, Y(11.3), HH_N - T), L2 - 1.3 + (0 if x % 12 == 9 else 0.25), L2 - 0.4, 'plaster', 'written', CEIL, PLAN + HABS)
    # The restaurant and dining room, west of the screen.
    RS = 'Main Street Station: restaurant'
    REST = ('The restaurant and dining room, 19 ft 2 in wide, west of the waiting room behind its screen, with a curved lunch counter and stools, '
            'round tables, and the servery behind (The Railroad Gazette, 1900; The Times, 1901: kept "in first-class style" by the railroads, '
            'its kitchen on the fourth floor). Whether it still served in 1952 is not recorded.')
    box('lunch-counter', RS, 5.0, 18.4, 34.0, 35.6, FF, FF + 1.05, 'wood', 'drawn', REST, PLAN)
    box('lunch-counter-2', RS, 16.8, 18.4, 35.6, 41.0, FF, FF + 1.05, 'wood', 'drawn', REST, PLAN)
    box('lunch-counter-top', RS, 4.8, 18.6, 33.7, 35.8, FF + 1.05, FF + 1.12, 'stone', 'drawn', REST, PLAN)
    for k, x in enumerate((5.5, 7.9, 10.3, 12.7, 15.1)):
        box(f'stool-{k}', RS, x - 0.5, x + 0.5, 32.0, 33.0, FF, FF + 0.75, 'iron', 'drawn', REST, PLAN)
    for k, y in enumerate((37.0, 39.5)):
        box(f'stool-s-{k}', RS, 19.0, 20.0, y - 0.5, y + 0.5, FF, FF + 0.75, 'iron', 'drawn', REST, PLAN)
    for k, (x, y) in enumerate(((5.5, 21.2), (16.5, 21.2), (11.0, 13.2), (5.5, 5.9), (16.5, 5.9))):
        cx_, cy_ = X(x), Y(y)
        rr = 0.55
        top = ring([(cx_ + rr * math.cos(2 * math.pi * i / 10), cy_ + rr * math.sin(2 * math.pi * i / 10)) for i in range(10)])
        p(f'table-{k}', RS, top, FF + 0.7, FF + 0.76, 'wood', 'drawn', REST, PLAN)
        p(f'table-{k}-foot', RS, rect(cx_ - 0.08, cx_ + 0.08, cy_ - 0.08, cy_ + 0.08), FF, FF + 0.7, 'iron', 'drawn', REST, PLAN)
        for j in range(4):
            t = math.pi / 4 + j * math.pi / 2
            ch_a, ch_b = cx_ + 0.85 * math.cos(t), cy_ + 0.85 * math.sin(t)
            p(f'table-{k}-chair-{j}', RS, rect(ch_a - 0.2, ch_a + 0.2, ch_b - 0.2, ch_b + 0.2), FF, FF + 0.45, 'wood', 'approximate',
              'A chair at a table in the restaurant. The plan draws the tables, not chairs: approximate.', PLAN)
    box('servery-wall', RS, 2, 21, 41.3, 41.7, FF, L2 - 0.4, 'plaster', 'drawn', REST, PLAN)
    box('servery-door', RS, 13, 16, 41.2, 41.25, FF, FF + 2.4, 'wood', 'drawn', REST, PLAN)
    box('service-wall', 'Main Street Station: service stair', 2, 21, 46.8, 47.2, FF, L2 - 0.4, 'plaster', 'drawn',
        'The wall between the servery and the general service stair and elevator, which ran from the ground floor to the fourth floor (The Railroad Gazette, 1900).' + PLAN_NOTE, PLAN)

    # ---- offices above ---------------------------------------------------------------------------------
    OFF = 'Main Street Station: offices'
    CORR = ('A wall of the central corridor that runs east and west on each floor above the waiting room, rooms on either side (HABS VA-848). '
            'No plan of these floors was found: its place is approximate.')
    for nm, z0, z1, extra in (('second', L2, CORNICE - 0.5, 0.0), ('third', L3, L4 - 0.35, 0.9), ('fourth', L4, L4 + 2.6, 0.9)):
        if nm == 'second':
            a0, a1 = HH_W + T, HH_E - T
        else:
            a0, a1, _, _ = inset_at(z1, extra)
        # In lengths of about 3 m, so each sorts against what stands near it (the tower, the stair).
        n_p = max(1, round((a1 - a0) / 3.0))
        for side, b in (('s', 8.95), ('n', 10.7)):
            for i in range(n_p):
                u0, u1 = a0 + (a1 - a0) * i / n_p, a0 + (a1 - a0) * (i + 1) / n_p
                p(f'corridor-{nm}-{side}' + ('' if i == 0 else f'-p{i}'), OFF, rect(u0, u1, b - 0.12, b + 0.12), z0, z1, 'plaster', 'approximate', CORR, HABS,
                  within=None if nm == 'second' else 'mss-h-roof')
    DOOR = ('An office door on the corridor: HABS VA-848 says the doors throughout are generally wood with glazed panels. '
            'Their places are approximate.')
    for nm, z0, a_list in (('second', L2, (-13.0, -7.6, -2.2, 2.2)), ('third', L3, (-10.6, -7.6, -2.2)), ('fourth', L4, (-7.6, -2.2))):
        for j, a in enumerate(a_list):
            for side, b in (('n', 10.58), ('s', 9.07)):
                fb = (b - 0.04, b) if side == 'n' else (b, b + 0.04)
                p(f'door-{nm}-{side}-{j}', OFF, ring([(a, fb[0]), (a + 0.95, fb[0]), (a + 0.95, fb[1]), (a, fb[1])]), z0, z0 + 2.2, 'wood', 'written', DOOR, HABS,
                  within=None if nm == 'second' else 'mss-h-roof')
                p(f'door-{nm}-{side}-{j}-glass', OFF, ring([(a + 0.15, fb[0] - 0.01), (a + 0.8, fb[0] - 0.01), (a + 0.8, fb[1] + 0.01), (a + 0.15, fb[1] + 0.01)]), z0 + 1.2, z0 + 2.0, 'glass', 'written', DOOR, HABS,
                  within=None if nm == 'second' else 'mss-h-roof')
    OFFW = 'A partition between offices (HABS VA-848: offices of merely functional design). No plan of this floor was found: its place is approximate.'
    for k, a in enumerate((BAYS[1], BAYS[3])):
        for side, (b0, b1) in (('s', (T, 8.83)), ('n', (10.82, HH_N - T))):
            p(f'office-wall-{k}-{side}', OFF, rect(a - 0.1, a + 0.1, b0, b1), L2, CORNICE - 0.5, 'plaster', 'approximate', OFFW, HABS)

    # ---- the concourse, and the baggage and express rooms under it -------------------------------------
    E0, E1, F0, F1 = ELL

    def YL(y):
        """Meters back from the front, for y ft on the plans in the concourse (its depth is HAER's)."""
        return HH_N + (y - 62.33) * (F1 - HH_N) / (97.67 - 62.33)
    CC = 'Main Street Station: concourse'
    CON = ('The concourse (the "lobby" of the 1900 plan), 82 ft wide behind the head house, open to the shed through an iron fence and gates, '
           'under a flat trussed roof (The Railroad Gazette, 1900; HABS VA-848), 35 ft deep (HAER VA-4, sheet 2). Its height is approximate.')
    CTOP = FF + 6.8
    p('ell-wall-w', CC, rect(E0, E0 + 0.6, F0, F1), G - 0.4, CTOP, 'brick', 'drawn', CON, PLAN + HABS + [SRC['haer-2'], SRC['osm-station']])
    p('ell-wall-e', CC, rect(E1 - 0.6, E1, F0, F1), G - 0.4, CTOP, 'brick', 'drawn', CON, PLAN + HABS + [SRC['haer-2'], SRC['osm-station']])
    p('ell-floor', CC, rect(E0 + 0.6, E1 - 0.6, F0, F1), FF - 0.5, FF, 'floor', 'drawn', CON, PLAN + HABS + [SRC['haer-2']])
    p('ell-roof', CC, rect(E0, E1, F0, F1), CTOP, CTOP + 0.5, 'roof', 'drawn', CON, PLAN + HABS + [SRC['haer-2']])
    for k, b in enumerate([F0 + 2.6 * i for i in range(1, 4)]):
        p(f'ell-beam-{k}', CC, rect(E0 + 0.6, E1 - 0.6, b - 0.15, b + 0.15), CTOP - 0.55, CTOP - 0.07, 'plaster', 'written',
          'The concourse\'s coffered ceiling (HABS VA-848; HAER photograph VA-4-10). Its coffers\' size is approximate.', HABS + [SRC['haer-photo-10']])
    BG = 'Main Street Station: baggage room'
    BAG = ('The baggage room (45 ft 7 in by 35 ft 2 in) under the concourse, with an oak counter, a 12-ft passage to the express room with doors '
           'to slide up, a baggage lift in each back corner, and the wagon drive behind (The Railroad Gazette, 1900; The Times, 1901). '
           'By 1969 the mail room (HABS VA-848); its use in 1952 is not recorded.')
    p('mail-floor', BG, rect(E0 + 0.6, E1 - 0.6, F0, F1 - 0.6), G - 0.4, G, 'floor', 'drawn', BAG, PLAN + HABS)
    p('mail-wall-n', BG, rect(E0 + 0.6, E1 - 0.6, F1 - 0.6, F1), G - 0.4, FF - 0.5, 'brick', 'drawn', BAG, PLAN + HABS)
    for k, a in enumerate((X(22), X(34), X(46))):
        p(f'bag-door-n-{k}', BG, rect(a + 0.4, a + 3.0, F1 - 0.66, F1 - 0.6), G, G + 3.0, 'wood', 'drawn', BAG + ' The doors on the north side slid up; their number is approximate.', PLAN)
    p('bag-counter', BG, rect(X(33) - 0.3, X(33) + 0.3, F0 + 0.1, YL(72.8)), G, G + 1.0, 'wood', 'drawn', BAG, PLAN)
    p('bag-counter-2', BG, rect(X(33) - 0.3, X(57), YL(72.8) - 0.3, YL(72.8) + 0.3), G, G + 1.0, 'wood', 'drawn', BAG, PLAN)
    p('bag-partition', BG, rect(X(56.8), X(57.6), YL(62.33), F1 - 0.6), G, FF - 0.5, 'brick', 'drawn', BAG, PLAN)
    p('bag-partition-door', BG, rect(X(56.6), X(56.8), YL(66), YL(78)), G, G + 3.0, 'wood', 'drawn', BAG, PLAN)
    # The baggage lift in the northwest corner: its pit, its platform at the track floor, the
    # glazed screen round it on the concourse, the door to lift up toward the shed.
    LIFT = ('The baggage lift in the concourse\'s northwest corner, a hydraulic lift about 8 by 12 ft between the baggage room and the track floor, '
            'behind a glazed screen in the concourse, its door to the platforms lifting up (The Railroad Gazette, 1900; The Times, 1901). Its frame is approximate.')
    LX0, LX1, LY0 = X(11.5), X(21.4), YL(83.5)
    p('lift-platform', BG, rect(LX0 + 0.3, LX1 - 0.3, LY0 + 0.3, F1 - 0.3), FF - 0.3, FF, 'wood', 'drawn', LIFT, PLAN)
    p('lift-shaft-s', BG, rect(LX0, LX1, LY0, LY0 + 0.15), G, FF - 0.5, 'brick', 'drawn', LIFT, PLAN)
    p('lift-shaft-e', BG, rect(LX1 - 0.15, LX1, LY0, F1 - 0.6), G, FF - 0.5, 'brick', 'drawn', LIFT, PLAN)
    for k, (a0, b0, a1, b1) in enumerate(((LX0, LY0, LX1, LY0), (LX1, LY0, LX1, F1 - 0.1))):
        pane(f'lift-screen-{k}', CC, a0, b0, a1, b1, FF + 1.0, FF + 3.4, 'glass', 'drawn', LIFT, PLAN)
        pane(f'lift-screen-{k}-dado', CC, a0, b0, a1, b1, FF, FF + 1.0, 'wood', 'drawn', LIFT, PLAN, d=0.08)
    p('lift-head', CC, rect(LX0, LX1, LY0, F1 - 0.1), FF + 3.4, FF + 3.6, 'wood', 'drawn', LIFT, PLAN)
    p('lift-door', CC, rect(LX0 + 0.4, LX1 - 0.4, F1 - 0.12, F1 - 0.06), FF, FF + 3.0, 'wood', 'drawn', LIFT, PLAN)
    MAIL = 'A loading door on the west side under the concourse, to the wagon drive (The Times, 1901; HABS VA-848: "loading docks for the mail room beneath the concourse"). Number, places and sizes approximate.'
    for k, b in enumerate((F0 + 1.8, F0 + 5.6)):
        p(f'mail-dock-door-{k}', BG, rect(E0 + 0.6, E0 + 0.64, b, b + 2.6), G, G + 3.0, 'wood', 'written', MAIL, PLAN + HABS)
    p('mail-dock', BG, rect(E0 - 3.0, E0, F0 + 1.5, F1 - 1.5), None, G, 'stone', 'written', MAIL, PLAN + HABS)
    # The iron screen across the open north side: panels of interlocking rings between posts,
    # fleur-de-lis on top, a gate in each bay under a number board (HAER VA-4-9 to -11).
    GATE = ('The wrought-iron fence between the concourse and the shed, with gates to the platforms (the 1900 plan); panels of interlocking '
            'rings with fleur-de-lis along the top, a number board over each gate (HAER photographs VA-4-9 to VA-4-11, 1971: "Gate 5"). '
            'The rings are drawn as plain bars, which read better at this angle.')
    g0, g1 = LX1 + 0.1, E1 - 0.6
    span = g1 - g0
    # Seen nearly edge on from the camera, the rings cannot read: the panels are drawn as close
    # bars between heavier posts, with the rails and the fleur-de-lis cresting.
    bars = [[0, 0.06, round(span, 3), 0.06, 0.1], [0, 3.6, round(span, 3), 3.6, 0.1], [0, 1.2, round(span, 3), 1.2, 0.06]]
    x = 0.0
    k = 0
    while x <= span + 1e-6:
        bars.append([round(x, 3), 0.0, round(x, 3), 3.95 if k % 6 == 0 else 3.6, 0.14 if k % 6 == 0 else 0.035])
        x += 0.3
        k += 1
    x = 0.15
    while x < span:
        bars += [[round(x, 3), 3.6, round(x, 3), 3.9, 0.035]]
        x += 0.6
    p('gates', 'Main Street Station: gates', plane(g0, F1 - 0.06, g1, F1 - 0.06, 0.08), FF, FF + 4.1, 'iron', 'written', GATE,
      PLAN + HABS + [SRC['haer-photo-9'], SRC['haer-photo-10']], shape='frame', members=bars)
    # Number boards over the gates, one at the middle of each stub track's platform pair.
    gb = 0
    for k, a in enumerate((X(30), X(45), X(60), X(75))):
        if not (g0 < a < g1):
            continue
        p(f'gate-board-{gb}', 'Main Street Station: gates', rect(a - 0.35, a + 0.35, F1 - 0.12, F1 - 0.06), FF + 4.1, FF + 4.8, 'plaster', 'written',
          'A number board over a gate (HAER photograph VA-4-9 shows "5"). The gates\' places along the fence are approximate.', [SRC['haer-photo-9']])
        gb += 1
