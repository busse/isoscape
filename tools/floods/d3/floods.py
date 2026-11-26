"""Floods series (d3, then final draft rc1): the plates' caption lines and their dry twins,
written into the two area regions. Captions are three short lines (the flood's caption, a count
line, a method line); every plate gets a pixel-aligned dry twin `<name>-dry` (`twinOf` the
plate, the water lowered out of sight, gauges off) whose caption is the plate's own, so the two
align. The stage mark ends the method line.

    python3 tools/floods/d3/floods.py ["FINAL DRAFT rc2"]

rc1: counts are over the whole city of each year, traced buildings included (`floodShown…`,
scene.ts); the footprints left out under a building of the year (`tracedCovered`) are counted
in the method line; Gaston's fifth pin says what the source says (Main Street Station
"escaped damage", Washington Post, Nov. 30, 2004), not "dry".
"""
import copy, json, sys

# rc2: "buildings in the water: N of M shown" (no verb to agree with N); land whose protection is
# not known is counted apart where a flood has `unknown`.
COUNT = '{floodAcres} acres under water off the channel; buildings in the water: {floodShownInWater} of the {floodShown} shown ({floodShownDepthMedianFt} ft median, {floodShownDepthMaxFt} ft deepest).'
COUNT_UNKNOWN = '{floodAcres} acres under water off the channel, plus {floodUnknownAcres} acres not known ({floodUnknownBuildings} buildings on it); buildings in the water: {floodShownInWater} of the {floodShown} shown ({floodShownDepthMedianFt} ft median, {floodShownDepthMaxFt} ft deepest).'
COUNTS_OLD = ('{floodAcres} acres under water off the channel; {floodBuildingsInWater} of the {buildings} buildings shown stand in it ({floodDepthAtBuildingsMedianFt} ft median, {floodDepthAtBuildingsMaxFt} ft deepest).',
              '{floodAcres} acres under water off the channel; {floodShownInWater} of the {floodShown} buildings shown stand in it ({floodShownDepthMedianFt} ft median, {floodShownDepthMaxFt} ft deepest).')
PINS = "Lettered pins: places named in reports (the boxes below); B and C are placed at the businesses' usual addresses."
LETTERS = 'ABCDE'  # rc1: Gaston's pins are lettered, so they are not read as the sheet's numbered boxes
WALL = ' Wall top: the 41 ft stage at which the weather service says the wall is overtopped, not surveyed.'
D3 = ' ' + (sys.argv[1] if len(sys.argv) > 1 else 'FINAL DRAFT rc3') + '.'
MAYO = 'perhaps 1 ft higher at the Mayo Bridge (assumed from 1969)'
SHOCKOE = {  # flood: city year (None: no evidence line)
    '1771': None, '1936': 1936, '1969': 1969, '1972': 1972, '1985': 1985, '1996': 1996, 'gaston-b': 2004, '2020': 2020, 'agnes-today': 'today',
}
MANCHESTER = ['agnes-today', 'agnes-today-nowall', '1996', '2020']
# rc2: titles and first caption lines, each from the checked levels (levels.json) and notes.json's sources.
TEXT = {
    '1771': ("The flood of 1771, an estimate, on the town of about 1788",
             "Water at about 38 ft above sea level (NAVD88) at the City Locks, derived from a 1771 stage of 38 ft on the old gauge near Mayo's Bridge (the Corps, from diaries); "
             "other accounts give 30 ft and 45 ft on unstated bases; ±3 ft is our judgment. Hatched: up to 41 ft."),
    '1972': (None, f"Water at 35.5 ft above sea level (NAVD88) at the City Locks (±0.3 ft; NOAA, USGS, the Dock Street sign), {MAYO}."),
    '1985': (None, f"Water at 29.7 ft above sea level (NAVD88) at the City Locks (±0.4 ft; weather service crest record), {MAYO}."),
    '1996': (None, f"Water at 22.7 ft above sea level (NAVD88) at the City Locks (weather service crest record), perhaps 1 ft more (hatched); {MAYO}."),
    '2020': (None, "Water at 17.0 ft above sea level (NAVD88) at the City Locks (±0.1 ft; USGS gauge record), held level upstream; in the falls above the Mayo Bridge, where the river's own surface stands higher, the river is drawn at its own surface."),
    'gaston-b': ("Gaston's rain, August 30, 2004, in Shockoe Bottom",
                 "Solid: water to about 28 ft above sea level (NAVD88), a middle figure of the reports; hatched to 35 ft: they imply 24 to 35 ft (AP, Washington Post, NBC12, WTVR)."),
}
M2020 = ("Water at 17.0 ft above sea level (NAVD88) at the City Locks (±0.1 ft; USGS gauge record), held level, with no rise assumed toward the Mayo Bridge. "
         "The weather service puts the treatment plant's access road, Maury to Brander Street, under water at 18.5 ft.")
# Ground whose protection is not known (Chris, rc2): the two lines that close the unmapped
# levee's possible courses (see `unknown` in flood.ts and notes.json).
UNKNOWN = {"lines": [
    [[-77.427722, 37.520497], [-77.4269, 37.5165], [-77.4262, 37.5127], [-77.4255, 37.5050]],
    [[-77.428734, 37.524582], [-77.4284, 37.5258], [-77.4265, 37.5258], [-77.4250, 37.5250], [-77.4235, 37.5240], [-77.4220, 37.5235],
     [-77.4205, 37.5229], [-77.4190, 37.5220], [-77.4175, 37.5200], [-77.4160, 37.5170], [-77.4150, 37.5050]]],
    "note": "Not known: the earthen levee is not mapped",
    "about": ("rc2 (Chris, November 25, 2026, 12:27): land the with-wall fill reaches only because the levee is not in our data. The first line continues "
              "the south wall's east tie-in south along the lidar ridge by I-95 past the frame; the second runs from the wall's east end along the river's "
              "south edge, just off the shore, past the frame (the levee could stand anywhere between I-95 and the bank). Land flooded with the wall but dry "
              "with both lines as walls is drawn as not known. The levee's course is given as along the west side of I-95, then south and west to Goodes "
              "Street (City FloodKit; floodwall.md), and WRDA 1986 sec. 401 says the project shall include flood protection for the wastewater plant; "
              "neither puts it on our map, so both courses are closed.")}
WITH_WALL = ('1996', '2020', 'agnes-today')


def period(year, wall, left_out=True):
    lo = f"; left out: {{outbuildingsHidden}} far-off outbuildings, {{tracedCovered}} footprints under a {year} building" if left_out else ''
    if wall:  # shorter, so the wall's line still fits three lines
        return f"Bathtub fill, not a flood model. Grey, dashed: {{periodUnconfirmed}} not ascertained for {year}{lo}."
    return (f"Bathtub fill, not a flood model. The city of {year} from maps, records and air photos; grey, dashed roof edge: "
            f"{{periodUnconfirmed}} not ascertained{lo}.")


DRY = 'Its dry twin: the same city with no flood, the same ground, wall and buildings, to compare.'


def dry(f, name):
    t = copy.deepcopy(f)
    for k in ('level', 'ponds', 'soft', 'uncertainty', 'band', 'within', 'unknown'):
        t.pop(k, None)
    t['profile'] = [[-77.4085, 37.515, -20.0], [-77.44255, 37.53018, -20.0]]
    t['gauges'] = []
    t['twinOf'] = name
    if t['notes'] and (t['notes'][0] in (COUNT, COUNT_UNKNOWN) or t['notes'][0] in COUNTS_OLD):
        t['notes'] = [DRY] + t['notes'][1:]
    return t


def main():
    p = 'regions/richmond-floods-shockoe.json'
    r = json.load(open(p))
    F = r['floods']
    for name, year in SHOCKOE.items():
        f = F[name]
        title, cap = TEXT.get(name, (None, None))
        if title: f['title'] = title
        if cap: f['caption'] = cap
        wall = WALL if f.get('walls') and f.get('gates') != 'open' else ''
        if name in WITH_WALL:
            f['unknown'] = UNKNOWN
        count = COUNT_UNKNOWN if name in WITH_WALL else COUNT
        if name == '1771':
            f['notes'] = [count, "Bathtub fill, not a flood model, on today's ground; the town of 1788 as the downtown history draws it: few of its buildings are known." + D3]
        elif name == 'agnes-today':
            f['notes'] = [count, "Bathtub fill, not a flood model. Today's city." + wall + D3]
        elif name == 'gaston-b':
            f['ponds'][0]['level'] = 8.534  # 28.0 ft, gaston-water.md section 4
            f['uncertainty'] = 2.134        # to 35.0 ft
            f['band'] = 'beyond'
            # rc3 (N1): the pool stands on the city side of the wall and of its openings; with the
            # gates open beside a low river, water reaching them ran out (step 15's spill test).
            f['ponds'][0]['citySide'] = True
            for k, mk in enumerate(f.get('markers', [])):
                mk['n'] = LETTERS[k]
            f['notes'] = [PINS, "Rain, not the James: the river stayed low and the wall's gates stood open; depths are reports, not surveys. " + period(2004, True)[len('Bathtub fill, not a flood model. '):] + D3]
        else:
            f['notes'] = [count, period(year, bool(wall), left_out=name != '2020') + wall + D3]
        F[f'{name}-dry'] = dry(f, name)
    json.dump(r, open(p, 'w'), indent=2); open(p, 'a').write('\n')
    p = 'regions/richmond-floods-manchester.json'
    r = json.load(open(p))
    F = r['floods']
    TITLES = {'1996': "Hurricane Fran's height (September 1996) against today's wall", '2020': "The November 2020 height against today's wall"}
    for name in MANCHESTER:
        f = F[name]
        if name in TITLES:  # on today's city, so the title says it is the flood's height
            f['title'] = TITLES[name]
        if name == '1996': f['caption'] = TEXT['1996'][1]
        if name == '2020': f['caption'] = M2020
        wall = WALL if f.get('walls') else ''
        if name in WITH_WALL:
            f['unknown'] = UNKNOWN
            f['gauges'] = [g for g in f.get('gauges', []) if g.get('name') != 'treatment plant grounds']
        f['notes'] = [COUNT_UNKNOWN if name in WITH_WALL else COUNT, "Bathtub fill, not a flood model. Today's city; the flats' earthen levee is not mapped." + wall + D3]
        F[f'{name}-dry'] = dry(f, name)
    json.dump(r, open(p, 'w'), indent=2); open(p, 'a').write('\n')


if __name__ == '__main__':
    main()
