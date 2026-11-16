#!/usr/bin/env python3
"""Model Broad Street Station (Richmond, 1919–1975) as of 1943, its peak year, into a history file.

The station is drawn from curated parts rather than from today's OpenStreetMap outline, which
holds the Science Museum's 1971 dome theater. Everything is placed in two local frames, in
meters about the station's center (37.5611 N, 77.4658 W):

  building frame (a, b): a along the Broad Street front toward the southeast (bearing 130.8°),
                         b toward the back of the station (bearing 40.8°);
  track frame (s, t):    s along the station tracks toward the north-northwest (bearing 332°),
                         t across them toward the east-northeast (bearing 62°).

Both are fitted to OpenStreetMap: the frame of the station building (way 252997396) and the
eight surviving platform outlines (ways 783038346, 1493273526–1493273532). The loop the
tracks run on comes from the USGS 1:24,000 Richmond quadrangles of 1934 and 1956, which show
the same layout. Heights are approximate, scaled from period postcards against the published
frontage (240 ft) and the 100-ft rotunda; every part says what it rests on.

    python3 tools/stations/broad_street.py   # writes history/broad-street-station.json
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'history' / 'broad-street-station.json'
STREETCARS = ROOT / 'history' / 'richmond-streetcars.json'

LON0, LAT0 = -77.4658, 37.5611
KX = 111_320 * math.cos(math.radians(LAT0))
KY = 110_574  # meters per degree of latitude, as region.ts uses


def unit(bearing):
    r = math.radians(bearing)
    return (math.sin(r), math.cos(r))


UA, UB = unit(130.8), unit(40.8)
US, UT = unit(332.0), unit(62.0)


def ab(a, b):
    return (a * UA[0] + b * UB[0], a * UA[1] + b * UB[1])


def st(s, t):
    return (s * US[0] + t * UT[0], s * US[1] + t * UT[1])


def lonlat(p):
    return [round(LON0 + p[0] / KX, 7), round(LAT0 + p[1] / KY, 7)]


def ring(pts):
    return [lonlat(p) for p in pts]


def rect_ab(a0, a1, b0, b1):
    return ring([ab(a0, b0), ab(a1, b0), ab(a1, b1), ab(a0, b1)])


def poly_ab(ca, cb, r, n, phase=0.0):
    return ring([ab(ca + r * math.cos(phase + 2 * math.pi * k / n), cb + r * math.sin(phase + 2 * math.pi * k / n)) for k in range(n)])


def to_ab(p):
    return (p[0] * UA[0] + p[1] * UA[1], p[0] * UB[0] + p[1] * UB[1])


# ---- sources ---------------------------------------------------------------------------------

SANBORN_475 = 'https://www.loc.gov/resource/g3884rm.g3884rm_g09064192504/?sp=93'

SRC = {
    'archipedia': 'https://sah-archipedia.org/node/20518',
    'dhr': 'https://www.dhr.virginia.gov/historic-registers/127-0226/',
    'plan': 'https://commons.wikimedia.org/wiki/File:Richmond_Broad_Street_Station_floor_plan.png',
    'postcard': 'https://scholarscompass.vcu.edu/postcard/190',
    'postcard-a': 'https://commons.wikimedia.org/wiki/File:New_Union_Station,_Richmond,_Va._(16649844960).jpg',
    'postcard-b': 'https://commons.wikimedia.org/wiki/File:New_Union_Station,_Richmond,_Va._(16836070322).jpg',
    'photo-1969': 'https://commons.wikimedia.org/wiki/File:RF%26P_1013_with_Trains_34,_The_Silver_Comet,_and_Train_22,_The_Silver_Star_at_left_at_Broad_Street_Station,_Richmond,_VA_on_March_9._1969_(25031006304).jpg',
    'platforms': 'https://commons.wikimedia.org/wiki/File:Platforms_of_the_former_Broad_Street_Station,_Richmond.jpg',
    'usgs-1934': 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/PDF/VA/24000/VA_Richmond_186500_1934_24000_geo.pdf',
    'usgs-1956': 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/PDF/VA/24000/VA_Richmond_186501_1956_24000_geo.pdf',
    'osm-station': 'https://www.openstreetmap.org/way/252997396',
    'osm-platform': 'https://www.openstreetmap.org/way/1493273526',
    'towers': 'https://www.chicagorailfan.com/stbcric.html',
    'smv': 'https://smv.org/about/history-of-the-museum/',
    'styleweekly': 'https://www.styleweekly.com/?p=14331',
}

features = []


def part(id_, name, ring_, height, tone, note, sources, base=0.0, seat='min', shape='prism', on=None, **more):
    f = {'id': id_, 'name': name, 'kind': 'landmark', 'from': 1919, 'to': 1976, 'ring': ring_, 'height': height,
         'tone': tone, 'note': note, 'sources': sources}
    if base:
        f['base'] = base
    if seat != 'min':
        f['seat'] = seat
    if shape != 'prism':
        f['shape'] = shape
    if on is not None:
        f['on'] = on
    # only ('whole' or 'cutaway'), elevation, upTo, levels, steps, confidence: see history.ts.
    f.update({k: v for k, v in more.items() if v is not None})
    features.append(f)


# ---- the head house ----------------------------------------------------------------------------
# Frontage a = −41…37 (78 m with the porch; the published frontage is 240 ft, 73 m), depth
# b = −20…21 to the back wall, then the enclosed concourse passages to b = 35, all from OSM.
# The center of the front is a = −2.
HEAD = 'Broad Street Station (head house)'
H_NOTE = 'Indiana limestone. Plan from the OpenStreetMap outline and the 1919 first-floor plan; heights scaled from period postcards (approximate).'
H_SRC = [SRC['dhr'], SRC['plan'], SRC['postcard-a'], SRC['postcard-b'], SRC['osm-station']]
# These massing parts draw the head house in whole views; a cutaway draws its walls, floors and
# rooms instead (broad_street_plan.py), traced from the 1919 plates.
W = 'whole'
part('bss-wing-w', HEAD, rect_ab(-41, -20.5, -20, 21), 14.5, 'stone', 'West wing: the lunch room and the white waiting rooms. ' + H_NOTE, H_SRC, only=W)
part('bss-wing-e', HEAD, rect_ab(16.5, 37, -20, 21), 14.5, 'stone', 'East wing: the "colored" waiting room of the segregated station, and stores. ' + H_NOTE, H_SRC + [SRC['archipedia']], only=W)
part('bss-center', HEAD, rect_ab(-20.5, 16.5, -20, 21), 19.5, 'stone', 'The central pavilion, up to the attic with its clock, flanked by the figures Progress and Industry. ' + H_NOTE, H_SRC + [SRC['archipedia']], only=W)
part('bss-passages', HEAD, rect_ab(-36, 24, 21, 35), 9, 'stone', 'The enclosed concourse passages across the back of the head house. ' + H_NOTE, H_SRC, only=W)
part('bss-steps', HEAD, rect_ab(-21, 17, -29, -20), 1.0, 'stone', 'The porch, raised above the forecourt. ' + H_NOTE, H_SRC, only=W)
# The colonnade: six Tuscan columns between square end piers, after the Doric of St. Peter's
# Square; the entablature runs across them at the wings' cornice. Columns and piers stand on
# the porch and the entablature on the columns (`on`), so on the sloping forecourt they share
# one base and one top, 12.5 m over the porch's lowest ground.
for k in range(6):
    a = -15.5 + k * 5.4  # centered on the front (a = −2), between the piers
    part(f'bss-column-{k + 1}', HEAD, poly_ab(a, -24.5, 0.9, 10), 11.5, 'stone', 'One of the colonnade\'s six columns, modeled on the Doric of St. Peter\'s Square. ' + H_NOTE, H_SRC + [SRC['archipedia']], on='bss-steps', only=W)
for k, a in enumerate((-19.2, 15.2)):
    part(f'bss-pier-{k + 1}', HEAD, rect_ab(a - 1.2, a + 1.2, -25.7, -23.3), 11.5, 'stone', 'A square end pier of the colonnade. ' + H_NOTE, H_SRC, on='bss-steps', only=W)
part('bss-entablature', HEAD, rect_ab(-20.5, 16.5, -26.5, -20), 2.5, 'stone', 'The entablature over the colonnade. ' + H_NOTE, H_SRC, on='bss-column-1', only=W)
for k, (a0, a1) in enumerate(((-41, -20.5), (16.5, 37))):
    part(f'bss-marquee-{k + 1}', HEAD, rect_ab(a0, a1, -23.5, -20), 0.5, 'iron', 'Cast-iron and glass marquee over the wing\'s doors (approximate).', [SRC['postcard-a'], SRC['postcard-b']], base=4.2, only=W)
# The dome: a polygonal drum pierced by lunettes, then the Roman dome, its top about 108 ft up.
part('bss-drum', HEAD, poly_ab(-2, 0.5, 14.5, 12, math.pi / 12), 5.5, 'stone', 'The polygonal drum, pierced by lunettes after those of Columbia\'s Low Library. Rotunda 100 ft high inside; heights approximate.', [SRC['archipedia'], SRC['dhr'], SRC['styleweekly']], base=19.5, only=W)
part('bss-dome', 'Broad Street Station dome', poly_ab(-2, 0.5, 13.5, 24), 8.0, 'dome',
     'The Roman dome, still in its original terra-cotta tile in 1943; it was recovered in copper in 1954–55 (the green of later photographs). The tile\'s gray-green is read from tinted postcards: approximate.',
     [SRC['archipedia'], SRC['postcard-a'], SRC['postcard-b']], base=25.0, shape='dome', only=W)

# ---- the concourse, bridged over the tracks ----------------------------------------------------
# On the station's axis, 54 ft wide, as the first-floor plan (Plate 15) and the 1919 article
# give it; its floor at the waiting room's, carried over the tracks on piers.
import broad_street_plan as BP  # noqa: E402

C_SRC = [SRC['osm-station'], SRC['photo-1969'], SRC['platforms']]
CA0, CA1 = -2 + (1440 - BP.XC) * BP.K, -2 + (1860 - BP.XC) * BP.K
part('bss-concourse', 'Broad Street Station concourse', rect_ab(CA0, CA1, 35, 98), 10.0, 'stone',
     'The long concourse, carried from the head house out over the station tracks at the level of the waiting room, on piers; stairs led down from it to each platform. On the station\'s axis and 54 ft wide, as the 1919 first-floor plan and article give it; it ends past the last platform on the 1925 Sanborn sheet. Floor at the waiting room\'s level (approximate); height approximate.',
     C_SRC + [SANBORN_475, BP.P15, BP.AMAR], only=W, elevation=BP.FF - 1.0, upTo=BP.FF + 9.0, confidence='drawn')

# ---- tracks, platforms, canopies ---------------------------------------------------------------
# Platforms (OSM): four, 13.8 m apart, centers at t = 29.5, 43.3, 57.1, 70.9, 6.6 m wide. Two
# tracks run in each gap; with one beyond the last platform that makes the seven passenger
# tracks of the 1919 postcard, and two express tracks beyond them.
PLATFORMS = [29.5, 43.3, 57.1, 70.9]
TRACKS = [34.25, 38.55, 48.05, 52.35, 61.85, 66.15, 75.65, 79.95, 84.25]
EXPRESS = {7, 8}
TC = (TRACKS[0] + TRACKS[-1]) / 2
S_NORTH, S_SOUTH = 230.0, -100.0  # the straight through the station

# The loop's center line, north junction to south junction, from the USGS quadrangles (1934,
# 1956). Meters east and north of the station's center.
NORTH = [(40, 780), (30, 700), (18, 620), (0, 555), (-25, 500), (-55, 440), (-72, 380), (-76, 300)]
SOUTH = [(130, -95), (170, -125), (210, -145), (250, -150), (300, -137), (345, -110), (380, -75), (402, -25), (412, 30), (420, 90), (430, 140)]


def chaikin(pts, n=3, keep=()):
    for _ in range(n):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            out += [(0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]), (0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1])]
        out.append(pts[-1])
        pts = out
    return pts


def densify(pts, step):
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        d = math.dist(p, q)
        k = max(1, int(d // step))
        out += [(p[0] + (q[0] - p[0]) * i / k, p[1] + (q[1] - p[1]) * i / k) for i in range(1, k + 1)]
    return out


straight = [st(s, TC) for s in range(int(S_NORTH), int(S_SOUTH) - 1, -10)]
north = chaikin(NORTH + [straight[0]], 3)
south = chaikin([straight[-1]] + SOUTH, 3)
center = densify(north[:-1] + straight + south[1:], 3.0)
# Arc length along the center line, and where the straight begins and ends.
acc = [0.0]
for p, q in zip(center, center[1:]):
    acc.append(acc[-1] + math.dist(p, q))
total = acc[-1]


def s_of(p):
    return p[0] * US[0] + p[1] * US[1]


in_straight = [S_SOUTH - 0.5 <= s_of(p) <= S_NORTH + 0.5 and abs((p[0] * UT[0] + p[1] * UT[1]) - TC) < 0.5 for p in center]
first = in_straight.index(True)
last = len(in_straight) - 1 - in_straight[::-1].index(True)
L_START, L_END = acc[first], acc[last]

# Off the straight the nine tracks gather into four around the loop, then into the two that
# join the main line.
LOOP4 = [-6.0, -2.0, 2.0, 6.0]
LOOP2 = [-2.0, 2.0]


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def offset(i, d):
    di = TRACKS[i] - TC
    l4 = LOOP4[min(3, i * 4 // len(TRACKS))]
    l2 = LOOP2[0 if l4 < 0 else 1]
    if L_START <= d <= L_END:
        return di
    out = L_START - d if d < L_START else d - L_END
    rem = d if d < L_START else total - d
    o = di + (l4 - di) * smooth(out / 110)
    return o + (l2 - o) * smooth(1 - rem / 110)


def normal(k):
    p = center[max(0, k - 1)]
    q = center[min(len(center) - 1, k + 1)]
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dx, dy) or 1
    return (dy / n, -dx / n)  # to the right of the direction of travel (north → south)


# The right of a line running south-southeast is west-southwest: t grows the other way.
track_lines = []
for i in range(len(TRACKS)):
    pts = []
    for k, (p, d) in enumerate(zip(center, acc)):
        nx, ny = normal(k)
        o = -offset(i, d)
        pts.append((p[0] + nx * o, p[1] + ny * o))
    track_lines.append(pts)

LOOP_SRC = [SRC['usgs-1934'], SRC['usgs-1956'], SRC['towers'], SRC['postcard']]
for i, pts in enumerate(track_lines):
    express = i in EXPRESS
    features.append({
        'id': f'bss-track-{i + 1}', 'name': f'Broad Street Station {"express" if express else "passenger"} track', 'kind': 'rail',
        'from': 1919, 'to': 1976, 'width': 4.4, 'line': [lonlat(p) for p in pts[::2]] + ([lonlat(pts[-1])] if len(pts) % 2 == 0 else []),
        'note': ('One of the two express tracks' if express else 'One of the seven passenger tracks') +
        ' of the station loop (7 passenger, 2 express, from the 1919 opening card). Trains ran in at one junction with the RF&P main and out at the other, so none had to back in. Placed from the OSM platforms at the station and the USGS quadrangles of 1934 and 1956 around the loop; the gathering of tracks onto the loop is drawn, not surveyed.',
        'sources': LOOP_SRC,
    })

# Distance along a track line to where the straight through the station begins (from the
# north end) or ends (from the south end): its points pair one to one with the center line's.
def at_straight(pts, from_end=False):
    k = first if not from_end else len(pts) - 1 - last
    seq = list(reversed(pts)) if from_end else pts
    return sum(math.dist(p, q) for p, q in zip(seq[:k], seq[1:k + 1]))


# Platforms and their canopies, cut where the concourse passes over them.
def crossing(t, a_edge):
    # s where the line at offset t meets the concourse side a = a_edge.
    lo, hi = -150.0, 300.0
    f = lambda s: to_ab(st(s, t))[0] - a_edge
    for _ in range(60):
        mid = (lo + hi) / 2
        if (f(lo) < 0) == (f(mid) < 0):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


P_SRC = [SRC['osm-platform'], SRC['dhr'], SRC['platforms'], SRC['photo-1969']]
for k, t in enumerate(PLATFORMS):
    features.append({
        'id': f'bss-platform-{k + 1}', 'name': 'Broad Street Station platform', 'kind': 'platform', 'from': 1919, 'to': 1976,
        'ring': ring([st(S_SOUTH, t - 3.3), st(S_SOUTH, t + 3.3), st(S_NORTH, t + 3.3), st(S_NORTH, t - 3.3)]),
        'note': 'One of the four platforms, from its surviving outline (OSM), extended to the 1,200-ft train shed of the opening card.',
        'sources': P_SRC + [SRC['postcard']],
    })
    s1, s2 = sorted((crossing(t, CA0), crossing(t, CA1)))
    # In a cutaway the south (east-side) sheds stop short of the departure stairs, which are
    # drawn open; in whole views they run to the concourse over the stair houses.
    # (and stop 4.5 m short of the head house's back, b = 20.8, which platform 1 runs past).
    s_back = s1 - 14
    while to_ab(st(s_back, t))[1] - 4.5 * abs(UT[0] * UB[0] + UT[1] * UB[1]) < 20.8 + 4.5 and s_back > S_SOUTH:
        s_back -= 1.0
    for side, (s0, s9), only in (('south', (S_SOUTH + 4, s1 - 1), 'whole'), ('north', (s2 + 1, S_NORTH - 4), None), ('south', (S_SOUTH + 4, s_back), 'cutaway')):
        features.append({
            'id': f'bss-canopy-{k + 1}-{side}' + ('-cut' if only == 'cutaway' else ''), 'name': 'Broad Street Station platform canopy', 'kind': 'canopy', 'from': 1919, 'to': 1976,
            'line': [lonlat(st(s0, t)), lonlat(st(s9, t))], 'width': 8.0, 'height': 5.4,
            'note': 'A cast-iron and steel butterfly canopy on a single row of cast-iron columns, roofed in red-brown; several survive at the Science Museum. Width and height approximate.',
            'sources': P_SRC, **({'only': only} if only else {}),
        })
    # The stair and ramp houses: departures went down enclosed stairways on the east (south)
    # side, arrivals came up ramps on the west (north) side (1919 article; SAH Archipedia). A
    # cutaway draws the east stairs open instead (broad_street_plan.py).
    for side, s_edge, sign in (('south', s1, -1), ('north', s2, 1)):
        a, b = s_edge, s_edge + sign * 14
        features.append({
            'id': f'bss-ramp-{k + 1}-{side}', 'name': 'Broad Street Station ' + ('stair house' if side == 'south' else 'ramp house'), 'kind': 'landmark', 'from': 1919, 'to': 1976,
            'ring': ring([st(min(a, b), t - 2), st(max(a, b), t - 2), st(max(a, b), t + 2), st(min(a, b), t + 2)]),
            'height': 4.5, 'tone': 'ramp',
            'note': ('The house over a departure stair down from the concourse to the platform.' if side == 'south' else 'The house over an arrival ramp up from the platform to the concourse.') + ' Sides from the 1919 article and SAH Archipedia; placed from the 1969 photograph; approximate.',
            'sources': [SRC['photo-1969'], BP.AMAR, SRC['archipedia']], **({'only': 'whole'} if side == 'south' else {}),
        })
    # Piers under the concourse, on the platform: one under each wall and one on the axis.
    for j, a_pier in enumerate((CA0 + 0.6, -2.0, CA1 - 0.6)):
        sp = crossing(t, a_pier)
        part(f'bss-concourse-pier-{k + 1}-{j + 1}', 'Broad Street Station concourse pier', ring([st(sp - 0.6, t - 0.6), st(sp + 0.6, t - 0.6), st(sp + 0.6, t + 0.6), st(sp - 0.6, t + 0.6)]), 5.0, 'stone',
             'A pier carrying the concourse over the tracks, on the platform. Piers stood where the platforms pass under (1969 photograph); their number, size and places are approximate.',
             [SRC['photo-1969']], upTo=BP.FF - 1.0, confidence='approximate')

BP.build(part, ab, st, to_ab, crossing, PLATFORMS, lonlat)

# The loop's grounds: the tracks and the hill they ran around, out to 12 m beyond the outermost
# track and closed along the main line. None of today's streets, paths or parking run here.
edge = []
for k, (p, d) in enumerate(zip(center, acc)):
    if k % 3:
        continue
    nx, ny = normal(k)
    reach = max(abs(offset(i, d)) for i in range(len(TRACKS))) + 12
    edge.append((p[0] + nx * reach, p[1] + ny * reach))
# Back north just inside the main line (OSM ways 880021818 and 880021819), so it is kept.
edge += [(425, 160), (366, 302), (276, 392), (196, 476), (146, 545), (30, 760)]
features.append({
    'id': 'bss-grounds', 'name': 'Broad Street Station loop', 'kind': 'site', 'from': 1919, 'to': 1976, 'ring': ring(edge),
    'note': 'The station loop and the hill inside it, closed along the RF&P main: railroad land, so today\'s streets and lots there are not drawn.',
    'sources': LOOP_SRC,
})

# Woods on the hill inside the loop and along the main, from the green tint of the 1956
# quadrangle (its woodland symbol); taken to stand in 1943 as well.
WOODS = [
    [(19, 488), (87, 494), (112, 462), (150, 425), (181, 300), (169, 275), (131, 275), (125, 212), (87, 181), (56, 237), (0, 237), (-25, 275), (6, 312), (6, 400)],
    [(250, 419), (300, 400), (387, 275), (375, 237), (337, 244), (275, 337)],
]
for k, w in enumerate(WOODS):
    features.append({
        'id': f'bss-woods-{k + 1}', 'name': 'Woods by the station loop', 'kind': 'wood', 'from': 1919, 'to': 1976, 'ring': ring(w),
        'note': 'Woodland as the 1956 USGS quadrangle tints it; outline traced from that sheet, approximate.', 'sources': [SRC['usgs-1956']],
    })

# The express building beside the express tracks, from the 1956 quadrangle.
features.append({
    'id': 'bss-express', 'name': 'Express building (Railway Express Agency)', 'kind': 'landmark', 'from': 1919, 'to': 1976,
    'ring': ring([(106, 28), (125, 31), (150, -16), (134, -25)]), 'height': 8,
    'note': 'A long building beside the express tracks on the 1956 USGS quadrangle, taken here to be the express house; use and height are assumptions.',
    'sources': [SRC['usgs-1956']],
})

# ---- trains, 1943 ----------------------------------------------------------------------------
# In 1943 the station averaged 57 trains a day, and on April 22 handled 33,324 passengers, its
# record. Six trains stand in the loop, the number and makeup chosen for the picture.
TRAINS = [
    # track index, cars, engine at the north end?
    (1, 11, True), (3, 12, False), (4, 9, True), (6, 10, False), (7, 6, True),
]
for idx, cars, north_end in TRAINS:
    pts = track_lines[idx]
    if north_end:
        at = at_straight(pts) + 6
        train = {'cars': cars, 'at': round(at, 1)}
    else:
        at = at_straight(pts, from_end=True) + 6
        train = {'cars': cars, 'at': round(at, 1), 'reverse': True}
    f = next(x for x in features if x['id'] == f'bss-track-{idx + 1}')
    f['train'] = train
    f['note'] += ' A train stands here: a steam engine and heavyweight cars in Pullman green (the consist is illustrative).'
    f['sources'] = f['sources'] + ['https://www.hmdb.org/m.asp?m=9209']

# ---- the lines beyond the loop ------------------------------------------------------------------
features.append({
    'id': 'bss-acl-connection', 'name': 'RF&P connection south (toward the Atlantic Coast Line)', 'kind': 'rail', 'from': 1919, 'to': 1976,
    'line': [lonlat(p) for p in densify(chaikin([(372, 322), (420, 160), (440, 60), (458, -40), (470, -200), (480, -420)], 3), 6)],
    'note': 'The line south from the loop\'s east junction, toward the Atlantic Coast Line, traced from the 1956 USGS quadrangle (approximate).',
    'sources': [SRC['usgs-1956']],
    'train': {'cars': 22, 'at': 40, 'kind': 'freight'},
})

# ---- the city around it: car lines and era rules from the streetcar history ------------------------
sc = json.loads(STREETCARS.read_text())
# At this scale a car line is drawn at the width of its double track, not the bold city-map ribbon.
features += [{**f, 'width': 4.0} for f in sc['features'] if f['kind'] == 'streetcar' and f.get('from', 0) <= 1943 < f.get('to', 9999)]
# The fair grounds north of the tracks (1906–1941), for views of the years before 1943.
features += [f for f in sc['features'] if f['kind'] in ('grounds', 'track') or f['id'] == 'fair-grounds-site']

rules = [
    {'where': {'id': ['w1485004507', 'w1485004508', 'w1089070999']}, 'eras': [],
     'note': 'Remnants of the station tracks still mapped in OSM: the curated loop stands in for them.'},
] + sc['rules']

history = {
    'title': 'Broad Street Station at its height, 1943',
    'method': 'The station is modeled from curated parts: plan from OpenStreetMap and the 1919 first-floor plan; heights scaled from period postcards against the 240-ft frontage and the 100-ft rotunda; tracks and platforms from the surviving platform outlines and the USGS Richmond quadrangles of 1934 and 1956. The city around it is today\'s buildings dated by the City of Richmond\'s recorded year built; the car lines and era rules are those of the streetcar map. Trains are illustrative. Every part names its sources.',
    'present': 2026,
    'about': 'John Russell Pope\'s Union Station, opened January 6, 1919, for the RF&P and the Atlantic Coast Line, was busiest in the Second World War: 57 trains a day on average, and a record 33,324 passengers on April 22, 1943.',
    'epochs': [{'year': 1943, 'title': 'Broad Street Station at its height', 'note': 'The wartime peak: 57 trains a day, a record 33,324 passengers on April 22, 1943.'}],
    'features': features,
    'rules': rules,
    'dates': [
        {'id': 'w252997396', 'name': 'Broad Street Station (Science Museum of Virginia)', 'year': 1976, 'source': SRC['smv'],
         'note': 'Today\'s outline, with the museum\'s 1971 dome theater, is drawn from 1976, when the Science Museum took the building; before that the station is drawn from its curated parts.'},
    ],
    # Buildings on the 1924–25 Sanborn sheets (vol. 4, sheets 405–407 and 460) that are gone
    # today, traced by tools/sanborn (corners in cps1925v4.json); taken to stand until the 1950s.
    'sanborn': {'lost': ['history/sanborn/broad-street-lost.geojson', 'history/sanborn/fair-grounds.geojson'], 'editions': [1925],
                'source': 'https://www.loc.gov/item/sanborn09064_009/'},
    'streetsNearBuildings': 60,
    'streetcarScale': 1,
}
OUT.write_text(json.dumps(history, indent=1, ensure_ascii=False) + '\n')

# ---- the wider view: where the lines go --------------------------------------------------------
# The same scene, with the railroads drawn four times their width and each line's way out of
# town labeled at the edge of the frame. Places in meters east and north of the station.
LINES_SRC = ['https://chicagorailfan.com/stbrric.html', 'https://www.richmondrailroadmuseum.com/railroad-history']
LABELS = [
    ((-1200, 1720), 'end', 'To Washington', 'RF&P main line: Fredericksburg, Washington, New York'),
    ((-480, 1930), 'start', 'AY Tower', "The RF&P main meets the Atlantic Coast Line's Belt Line"),
    ((390, 350), 'start', 'Seaboard Junction', 'The Seaboard Air Line leaves the RF&P for Main Street Station'),
    ((-120, -60), 'end', 'Broad Street Station', 'RF&P, Atlantic Coast Line and N&W trains'),
    ((-2650, -3300), 'start', 'To Petersburg and Florida', 'ACL Belt Line over the James; N&W trains by way of Petersburg'),
    ((2750, -3180), 'end', 'Main Street Station', 'Seaboard Air Line south to Raleigh and Florida; C&O'),
    ((-3050, -1600), 'start', 'C&O James River line', 'west to Lynchburg'),
    ((-3100, -2380), 'start', 'Southern Railway', 'from Hull Street station, southwest to Danville'),
]
labels = [{
    'id': f'lines-label-{k + 1}', 'name': name, 'kind': 'label', 'from': 1919, 'to': 1976, 'at': lonlat(at), 'anchor': anchor, 'caption': caption,
    'note': 'Where the line went in 1943. Main Street Station served the Seaboard Air Line and the C&O, Hull Street station the Southern; AY Tower, about a mile northwest of Broad Street, was the wye of the RF&P main and the ACL; Seaboard Junction, just north of the station, was where the SAL left the RF&P.',
    'sources': LINES_SRC,
} for k, (at, anchor, name, caption) in enumerate(LABELS)]
lines = {**history, 'title': 'The lines from Broad Street Station, 1943', 'features': features + labels, 'railScale': 4,
         'epochs': [{'year': 1943, 'title': 'The lines from Broad Street Station', 'note': history['epochs'][0]['note']}],
         'sanborn': {**history['sanborn'], 'lost': ['history/sanborn/lost.geojson', *history['sanborn']['lost']], 'editions': [1925]}}
(ROOT / 'history' / 'broad-street-lines.json').write_text(json.dumps(lines, indent=1, ensure_ascii=False) + '\n')
print(f'{OUT.relative_to(ROOT)}: {len(features)} features; loop {total:.0f} m, straight {L_END - L_START:.0f} m')
