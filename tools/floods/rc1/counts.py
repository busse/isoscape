"""Floods series rc1, rc2: restate drafts/richmond-floods/counts.json under the stage's key ("rc2"): every plate's
caption counts (from its build's `info`), its box counts (tools/floods/d3/boxcounts.ts output),
and the change from d3 caused by the overlapping-footprint rule (`tracedCovered`) and by counting
traced buildings in the water.

    python3 tools/floods/rc1/counts.py <plates-dir> <boxcounts-shockoe.json> <boxcounts-manchester.json>
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
KEYS = ['floodAcres', 'floodUnknownAcres', 'floodUnknownBuildings', 'buildings', 'traced', 'floodShown', 'floodShownInWater', 'floodShownSubmerged', 'floodShownDepthMedianFt', 'floodShownDepthMaxFt',
        'floodBuildingsInWater', 'tracedCovered', 'outbuildingsHidden', 'periodShown', 'periodUnconfirmed', 'floodDeckSpansAwash', 'floodWallPieces']


def main(plates, cs, cm):
    p = os.path.join(ROOT, 'drafts/richmond-floods/counts.json')
    c = json.load(open(p))
    out = {'about': ('Final draft rc1 (1.0.0-rc1). `plates`: each plate\'s caption counts from its build (scene stats): `floodShown` is every building the '
                     'plate draws, traced ones included, and `floodShownInWater` those standing in the water (d3 captions counted today\'s buildings '
                     'only: `buildings`, `floodBuildingsInWater`); `tracedCovered` the traced footprints left out under a building of the year (rule: '
                     'half or more covered, regions\' `tracedCovered: 0.5`). `boxes`: tools/floods/d3/boxcounts.ts on each plate (whole plate and '
                     'each box of tools/floods/d3/boxes.json, rc1 boxes). `fromD3`: the whole-plate count of buildings shown and in water, d3 against rc1, '
                     'as boxcounts counts them (traced included in both).'),
           'plates': {}, 'boxes': {'shockoe': json.load(open(cs)), 'manchester': json.load(open(cm))}, 'fromD3': {}}
    for f in sorted(os.listdir(plates)):
        if f.endswith('.info.json'):
            i = json.load(open(os.path.join(plates, f)))
            out['plates'][f[len('richmond-floods-'):-len('.info.json')]] = {k: i[k] for k in KEYS if k in i}
    for area in ('shockoe', 'manchester'):
        for k, v in out['boxes'][area].items():
            old = c.get('rc2', {}).get('boxes', {}).get(area, {}).get(k, {}).get('plate')
            if old:
                out['fromD3'][f'{area} {k}'] = {'shown': [old['shown'], v['plate']['shown']], 'inWater': [old['inWater'], v['plate']['inWater']],
                                                'outbuildingsHidden': [old.get('outbuildingsHidden'), v['plate'].get('outbuildingsHidden')]}
    out['about'] = out['about'].replace('Final draft rc1 (1.0.0-rc1)', 'Final draft rc3 (1.0.0-rc3)').replace('d3 against rc1', 'rc2 against rc3').replace('d3 captions', 'd3 captions') + (' rc2: land whose protection is not known (`floodUnknownAcres`, `floodUnknownBuildings`) is left out of the with-wall plates\' acres and buildings in the water and counted apart; Gaston drawn at 28 ft solid to 35 ft hatched. rc3: Gaston\'s pool held on the city side of the wall (`citySide`).')
    out['fromRc2'] = out.pop('fromD3')
    c['rc3'] = out
    json.dump(c, open(p, 'w'), indent=1, ensure_ascii=False)
    open(p, 'a').write('\n')
    for k, v in out['fromRc2'].items():
        print(k, v)


if __name__ == '__main__':
    main(*sys.argv[1:])
