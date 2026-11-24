# Fine sampling of the 2025 FIS James River profiles; keeps only clean stations
# (exactly 7 clusters: 0.2%, 1%+, 1%, 2%, 4%, 10%, stream bed, in descending order).
import sys, json
sys.path.insert(0, '/home/claude/floods-research/check/scripts')
import profiles as pr
from read_james import STATIONS, page_for
NAMES = ['p0_2', 'p1plus', 'p1', 'p2', 'p4', 'p10', 'bed']
clean = []
x = 132400
while x <= 219150:
    pg = page_for(x)
    v = pr.sample2(pg, x)
    if len(v) == 7 and all(v[i] >= v[i+1] for i in range(6)):
        clean.append(dict(station_ft=x, panel=pr.PANELS[pg][0], pdf_page=pg, **dict(zip(NAMES, v))))
    x += 50
json.dump(clean, open('/home/claude/floods-research/check/work/james_fine.json', 'w'))
print('clean stations', len(clean))
def near(x, side):
    c = [r for r in clean if (r['station_ft'] <= x if side < 0 else r['station_ft'] >= x)]
    c.sort(key=lambda r: abs(r['station_ft'] - x))
    return c[0] if c and abs(c[0]['station_ft'] - x) <= 400 else None
rows = []
for name, x in STATIONS:
    for side in (-1, 1):
        r = near(x, side)
        if r:
            print(f"{name[:58]:58s} {x:7d} {'dn' if side<0 else 'up'} {r['station_ft']:7d} " + ' '.join(f"{r[k]:7.2f}" for k in NAMES))
