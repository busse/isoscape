"""
Dev tool (floods series, d1): the counts every caption and the story draw from, written to
drafts/richmond-floods/counts.json. Runs `isoscape info` for each plate (and, for a plate with
the wall, the same level without it).

  python3 tools/floods/counts.py <levels.json> <out counts.json>
"""
import json, subprocess, sys

PLATES = [('1771', 1788, '1771-05'), ('1936', 1936, '1936-03'), ('1969', 1969, '1969-08'), ('1972', 1972, '1972-06'),
          ('1985', 1985, '1985-11'), ('1996', 1996, '1996-09'), ('2020', 2020, '2020-11'), ('agnes-today', 2026, '1972-06'),
          ('gaston-a', 2004, None)]
KEEP = ['buildings', 'floodAcres', 'floodHectares', 'floodBuildingsInWater', 'floodBuildingsSubmerged', 'floodDepthAtBuildingsMax', 'floodDepthAtBuildingsMedian',
        'floodDepthAtBuildingsMaxFt', 'floodDepthAtBuildingsMedianFt', 'floodBandHectares', 'floodLevelLow', 'floodLevelHigh', 'floodLinksHeld', 'floodWallPieces',
        'floodWallOpenings', 'floodDeckSpansAwash', 'floodRiverHectares', 'floodPondHectares', 'datedFromParcels', 'tracedDrawn', 'footprintsDrawn']

def info(flood, year):
    out = subprocess.run(['node', 'bin/isoscape.js', 'info', 'richmond-floods-d1', '--year', str(year), '--flood', flood], capture_output=True, text=True, check=True).stdout
    s = json.loads(out)
    return {k: s[k] for k in KEEP if k in s}

def main():
    levels = {f['id']: f for f in json.load(open(sys.argv[1]))['floods']}
    region = json.load(open('regions/richmond-floods-d1.json'))
    out = {'about': 'Counts for the floods series, d1 (rough draft): from `isoscape info` on regions/richmond-floods-d1.json. Buildings are those the dated view shows '
                     '(standing today by year built, plus traced and curated), not every building of the year. Acres are off the river’s own channel, inside the frame. '
                     'Depths at buildings are the deepest point of each footprint, true feet. Levels are feet NAVD88 at the City Locks (levels.json).',
           'plates': []}
    for key, year, fid in PLATES:
        fl = levels.get(fid) if fid else None
        rec = {'plate': key, 'city_year': year,
               **({'level_ft_navd88_locks': fl['level_navd88_ft'], 'uncertainty_ft': fl.get('uncertainty_ft'), 'mayo_bridge_ft': fl.get('mayo_bridge_navd88_ft'), 'basis': fl['basis']} if fl else
                  {'level_ft_navd88': 28.0, 'uncertainty_ft': 3.0, 'basis': 'Gaston: a judgment from reported depths (gaston-water.md), not a surveyed level'}),
               'with_wall': region['floods'][key].get('walls') is True, 'counts': info(key, year)}
        if key + '-nowall' in region['floods']:
            rec['counts_without_wall'] = info(key + '-nowall', year)
        out['plates'].append(rec)
        print(key, rec['counts'].get('floodAcres'), rec['counts'].get('floodBuildingsInWater'), rec.get('counts_without_wall', {}).get('floodAcres'))
    json.dump(out, open(sys.argv[2], 'w'), indent=1)

if __name__ == '__main__':
    main()
