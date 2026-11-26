"""
Dev tool (floods series, d1): write the series' region file from the checked levels, so every
level, its range and its source in the pictures come from one file.

  python3 tools/floods/make_region.py <levels.json> <out region.json> [frame A|B|C] [name]

Levels are feet NAVD88 at the City Locks, held downstream and ramped to the Mayo Bridge value
(levels.json "reach"); west of the bridge they are held at the Mayo value, except where the
file has control points there (Camille, 1936). Captions use `{measure}` placeholders that the
build fills in.
"""
import json, sys

FT = 0.3048006
FRAMES = {
    # Looking north across the river from Manchester, the house bearing of the downtown views.
    'A': {'center': [-77.4265, 37.5295], 'width': 2700, 'depth': 1700, 'bearing': -8.7},
    # Looking north-north-east up the Shockoe valley.
    'B': {'center': [-77.4258, 37.5305], 'width': 2200, 'depth': 1700, 'bearing': 25},
    # d2: Shockoe on its own (north bank), and Manchester on its own (south bank).
    'S1': {'center': [-77.4290, 37.5322], 'width': 2000, 'depth': 1400, 'bearing': 25},
    'S2': {'center': [-77.4290, 37.5318], 'width': 2200, 'depth': 1300, 'bearing': 0},
    'S3': {'center': [-77.4285, 37.5320], 'width': 2000, 'depth': 1500, 'bearing': 45},
    # Manchester: looking from the river toward the south bank.
    'M1': {'center': [-77.4300, 37.5212], 'width': 2200, 'depth': 1400, 'bearing': 200},
    'M2': {'center': [-77.4295, 37.5215], 'width': 2200, 'depth': 1400, 'bearing': 225},
    # Looking west-north-west up the river from Rocketts.
    'C': {'center': [-77.4262, 37.5300], 'width': 2300, 'depth': 1700, 'bearing': -65},
}
LOCKS = [-77.42171, 37.52409]
MAYO = [-77.43458, 37.5277]
DOWN = [-77.4085, 37.5150]      # below the frame, downstream: held at the Locks level
NINTH = [-77.44255, 37.53018]   # the 9th Street bridge, the foot of the falls

WALL_SRC = ['https://www.hmdb.org/m.asp?m=23953']
WALL_TOP_NOTE = 'the stage at which the weather service says the wall is overtopped (41 ft at the City Locks), not the wall\'s surveyed top'

def m(ft): return round(ft * FT, 3)

def profile(fl):
    L = fl['level_navd88_ft']; M = fl.get('mayo_bridge_navd88_ft') or L
    pts = [[*DOWN, m(L)], [*LOCKS, m(L)], [*MAYO, m(M)]]
    extra = [c for c in fl.get('control_points', []) if c.get('lonlat_on_centerline') and c['lonlat_on_centerline'][0] < MAYO[0] - 0.0005 and c['lonlat_on_centerline'][0] > NINTH[0] - 0.0001 and 'head of the drop' not in c['place'] and 'Tredegar' not in c['place']]
    for c in sorted(extra, key=lambda c: -c['lonlat_on_centerline'][0]):
        pts.append([*c['lonlat_on_centerline'], m(c['elev_navd88_ft'])])
    if not extra: pts.append([*NINTH, m(M)])
    return pts

def counts_lines(year, wall):
    # Two short lines under the level line: the counts, then what the picture cannot claim.
    city = f'Buildings: those standing today by year built, plus traced ones; lost, untraced buildings are missing.' if year < 2026 else 'Today\'s city.'
    return [
        '{floodAcres} acres under water off the channel; {floodBuildingsInWater} of the {buildings} buildings shown stand in it ({floodDepthAtBuildingsMedianFt} ft median, {floodDepthAtBuildingsMaxFt} ft deepest).',
        'A bathtub fill on today\'s ground, not a flood model. ' + city + (' Wall top: the 41 ft overtopping stage, not surveyed.' if wall else '') + ' ROUGH DRAFT.',
    ]

def main():
    levels = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    frame = FRAMES[sys.argv[3] if len(sys.argv) > 3 else 'A']
    name = sys.argv[4] if len(sys.argv) > 4 else 'richmond-floods-d1'
    south = (sys.argv[3] if len(sys.argv) > 3 else 'A').startswith('M')
    by = {f['id']: f for f in levels['floods']}
    r = {
        'title': 'Richmond, VA: Manchester and the south floodwall, the James in flood' if south else 'Richmond, VA: the James in flood, Shockoe Bottom to Rocketts' if (sys.argv[3] if len(sys.argv) > 3 else 'A').startswith('S') else 'Richmond, VA: the James in flood, Shockoe Bottom to Rocketts and Manchester',
        **frame, 'snap': False, 'scale': 2.0, 'squash': 0.5, 'exaggeration': 1.0, 'slab': 18, 'palette': 'paper',
        'bridgeDeck': 7, 'bridges': [{'match': 'Manchester', 'deck': 24}, {'match': 'Mayo', 'deck': 6}, {'match': 'Potterfield', 'deck': 3}],
        'minBuildingArea': 12, 'seatOnBanks': True, 'dots': 'all', 'data': 'richmond-i195-rocketts',
        'floodStyles': ['blue-grey', 'wall-cased-red', 'xray-heavy'],
        'terrain': {'exaggeration': 1.0, 'cell': 5, 'contour': 2, 'majorEvery': 5, 'demResolution': 2},
        'time': {'history': 'history/richmond-downtown.json', 'yearBuiltFrom': 'richmond-downtown-time',
                 'yearBuilt': {'url': 'https://services1.arcgis.com/k3vhq11XkBNeeOfM/ArcGIS/rest/services/Year_of_Construction/FeatureServer/0', 'field': 'Year_Built'}},
        'floodwalls': [
            {'name': 'Richmond floodwall', 'osm': 'flood_wall', 'top': m(41.0), 'maxGap': 60, 'from': 1994, 'sources': WALL_SRC, 'label': 'Floodwall (1994)',
             'note': 'Line from OSM (wall=flood_wall, chained across gaps up to 60 m: the openings). Top: ' + WALL_TOP_NOTE + '. Dedicated 21 October 1994.'},
            *[{'name': n, 'line': l, 'top': m(41.0), 'from': 1994, 'note': 'APPROXIMATE: not from any source; a short line from the end of the mapped wall to higher ground, so the fill does not run round an end the map leaves open.'}
              for n, l in [('APPROXIMATE tie-in, north wall west end', [[-77.436079, 37.534206], [-77.436221, 37.534646], [-77.436392, 37.534946]]),
                           ('APPROXIMATE tie-in, north wall east end', [[-77.425782, 37.530409], [-77.425197, 37.530641], [-77.424531, 37.530905]]),
                           ('APPROXIMATE tie-in, south wall west end', [[-77.444308, 37.529907], [-77.445113, 37.529923]]),
                           ('APPROXIMATE tie-in, south wall east end', [[-77.428734, 37.524582], [-77.428377, 37.523619], [-77.427722, 37.520497]])]],
        ],
        'floods': {},
    }
    def river(key, fid, title, year, first, wall=False, **more):
        fl = by[fid]
        r['floods'][key] = {'title': title, 'caption': first, 'profile': profile(fl), 'walls': wall, 'gates': 'closed',
                            'notes': counts_lines(year, wall), **more}
        if wall:
            nw = counts_lines(year, False)
            r['floods'][key + '-nowall'] = {**r['floods'][key], 'walls': False, 'notes': nw,
                'caption': first.replace('against today\'s city and wall, gates shut', 'on today\'s city with no floodwall')}
    lv = lambda fid: by[fid]['level_navd88_ft']
    mayo = lambda fid: by[fid].get('mayo_bridge_navd88_ft')
    river('1771', '1771-05', 'The flood of 1771, an estimate, on the town of about 1788', 1788,
          f'Water at about {lv("1771-05")} ft above sea level (NAVD88), ±3 ft, the May 1771 "Great Fresh" (diaries, via the Army Corps). Hatched: the top of the range.', uncertainty=m(3.0), band='beyond')
    r['floods']['1771-range'] = {**r['floods']['1771'], 'band': 'range',
        'caption': r['floods']['1771']['caption'].replace('Hatched: the top of the range.', 'Water: the bottom of the range; hatched: the rest of it.')}
    river('1936', '1936-03', 'The flood of March 1936', 1936,
          f'Water at {lv("1936-03")} ft above sea level (NAVD88) at the City Locks (±0.4 ft), {mayo("1936-03")} ft at the Mayo Bridge. USGS high-water marks.')
    river('1969', '1969-08', 'Hurricane Camille, August 1969', 1969,
          f'Water at {lv("1969-08")} ft above sea level (NAVD88) at the City Locks (±0.2 ft), {mayo("1969-08")} ft at the Mayo Bridge. USGS records and marks.')
    river('1972', '1972-06', 'Hurricane Agnes, June 1972', 1972,
          f'Water at {lv("1972-06")} ft above sea level (NAVD88) at the City Locks (±0.3 ft), about {mayo("1972-06")} ft at the Mayo Bridge. NOAA, USGS, the Dock Street sign.')
    gauges = [{'at': [-77.428532, 37.533434], 'name': '17th and Main'}, {'at': [-77.42916, 37.53460], 'name': 'Main Street Station'},
              {'at': [-77.429647, 37.532275], 'name': '17th and Dock'}]
    r['floods']['1972']['gauges'] = gauges
    # The same plate dry, pixel for pixel, for a compare divider: the same captions, water far below the ground.
    r['floods']['1972-dry'] = {**r['floods']['1972'], 'profile': [[*p[:2], -20.0] for p in r['floods']['1972']['profile']], 'gauges': []}
    river('1985', '1985-11', 'The Election Day flood, November 1985', 1985,
          f'Water at {lv("1985-11")} ft above sea level (NAVD88) at the City Locks (±0.4 ft), about {mayo("1985-11")} ft at the Mayo Bridge. Weather service crest record.')
    river('1996', '1996-09', 'Hurricane Fran, September 1996, against the new floodwall', 1996,
          f'Water at {lv("1996-09")} ft above sea level (NAVD88) at the City Locks, perhaps 1 ft more (hatched), about {mayo("1996-09")} ft at the Mayo Bridge. Weather service crest record.', wall=True, uncertainty=m(1.0), band='beyond')
    river('2020', '2020-11', 'November 2020, against the floodwall', 2020,
          f'Water at {lv("2020-11")} ft above sea level (NAVD88) at the City Locks (±0.1 ft), held to the Mayo Bridge. USGS gauge record.', wall=True)
    river('agnes-today', '1972-06', 'What if: the 1972 flood\'s height against today\'s floodwall', 2026,
          f'Not a flood that happened: water at the height the 1972 flood reached, {lv("1972-06")} ft at the City Locks, against today\'s city and wall, gates shut.', wall=True)
    r['floods']['agnes-today']['gauges'] = [{'at': [-77.4326, 37.5292], 'name': 'Mayo Island'}, {'at': [-77.42161, 37.52586], 'name': 'Great Shiplock Park'}]
    # Gaston, August 30, 2004: rain, not the river. Depths are reports at places; the pool is drawn
    # soft, from the low ground near 17th Street, inside the blocks the reports name (14th to 21st,
    # Dock to Broad), to about 28 ft, the research's single best figure (plus or minus 3 ft), with
    # the floodwall's gates open. See gaston-water.md and gaston-mechanism.md.
    ring = [[-77.432744, 37.533343], [-77.431228, 37.536184], [-77.426033, 37.536055], [-77.422424, 37.533857], [-77.426074, 37.530051], [-77.432744, 37.533343]]
    low = [-77.42930, 37.53337]
    markers = [
        {'n': '1', 'anchor': 'start', 'at': [-77.42826, 37.53399], 'key': '1  17th Street Market: where most of the water came together (Washington Post).'},
        {'n': '2', 'anchor': 'end', 'at': [-77.42835, 37.53420], 'key': '2  Havana \'59, 16 N. 17th St.: water 13 ft up the dining-room wall, by the owner\'s account (Washington Post).'},
        {'n': '3', 'at': [-77.42934, 37.53230], 'key': '3  Bottoms Up Pizza, 1700 Dock St.: 6 ft 2 in inside, over a 3 ft step, about 9 ft above the street (owner, NBC12).'},
        {'n': '4', 'at': [-77.430374, 37.534548], 'key': '4  15th and Main: "rapids" in the street (a witness).'},
        {'n': '5', 'at': [-77.42916, 37.53460], 'key': '5  Main Street Station: escaped damage (Washington Post).'},
    ]
    gaston_notes = [
        'Rain, not the James: 6 to 12 in in eight hours; the river stayed low and the wall\'s gates stood open. Depths are reports, not surveys; the edge is an estimate.',
        '1 17th Street Market, where the water met · 2 Havana \'59, 13 ft up the wall · 3 Bottoms Up, about 9 ft · 4 15th and Main, "rapids" · 5 Main Street Station, dry.',
        'The ground lets still water out at 19 to 22 ft; it stood higher because it came faster than it could leave. City of 2004 as recorded. ROUGH DRAFT.',
    ]
    base = {'walls': True, 'gates': 'open', 'soft': True, 'markers': markers, 'notes': gaston_notes}
    r['floods']['gaston-a'] = {**base, 'title': 'Tropical Storm Gaston, August 30, 2004: rain in Shockoe Bottom',
        'caption': 'A: a soft pool to about 28 ft above sea level (NAVD88), ±3 ft, in the blocks the reports name (AP, Washington Post, NBC12).', 'ponds': [{'level': m(28.0), 'from': low, 'ring': ring}]}
    r['floods']['gaston-b'] = {**base, 'title': 'Tropical Storm Gaston, August 30, 2004: rain in Shockoe Bottom',
        'caption': 'B: the range, not a level: water to 25 ft above sea level (NAVD88), hatched to 31 ft, in the blocks the reports name (AP, Washington Post, NBC12).',
        'ponds': [{'level': m(28.0), 'from': low, 'ring': ring}], 'uncertainty': m(3.0), 'band': 'range'}
    if south:
        # Manchester's own gauges, on the flats the south wall and levee guard.
        g = [{'at': [-77.436818, 37.522792], 'name': '5th and Stockton'}, {'at': [-77.437703, 37.519511], 'name': 'Commerce and Maury'},
             {'at': [-77.4235, 37.5170], 'name': 'treatment plant grounds'}]
        for k in ('1972', 'agnes-today', '1972-dry'):
            if k in r['floods']: r['floods'][k]['gauges'] = [] if k == '1972-dry' else g
    json.dump(r, open(out, 'w'), indent=2)
    open(out, 'a').write('\n')

if __name__ == '__main__':
    main()
