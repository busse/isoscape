# Sample the 2025 FIS James River profiles (panels 17P-23P) at named stations.
import sys, json
sys.path.insert(0, '/home/claude/floods-research/check/scripts')
import profiles as pr
NAMES = ['0.2%', '1%+', '1%', '2%', '4%', '10%']
def page_for(x):
    for pg, (pn, x0, yt) in pr.PANELS.items():
        if x0 <= x <= x0 + 13000: return pg
def read(x):
    pg = page_for(x)
    fx, fy, ix = pr.cal(pg)
    res = pr.sample(pg, x)
    # drop legend-box hits (legend occupies the panel's lower right corner)
    X = ix(x)
    vals = [r for r in res]
    return pg, vals
STATIONS = [
 ('Downstream end of plotted profile', 132400), ('XS A', 135943), ('XS B', 140508), ('XS C', 145016),
 ('Confluence of Broad Rock Creek (label read by eye, +/-100 ft)', 151250), ('XS D', 152727), ('XS E', 158169),
 ('Confluence of Gillies Creek', 160195), ('XS F', 161592),
 ('City Locks gauge 02037705 (station derived, +/-300 ft)', 161527),
 ('I-95 (Richmond-Petersburg Turnpike), downstream face', 163980), ('I-95, upstream face', 164040),
 ('Railroad bridge (CSX Bellwood Sub per OSM), downstream', 164700), ('Railroad bridge, upstream', 164750),
 ('US 360 / South 14th St (Mayo Bridge), downstream face', 165560), ('Mayo Bridge, upstream face', 165625),
 ('Railroad bridge (CSX Richmond District per OSM), downstream', 166530), ('Railroad bridge, upstream', 166575),
 ('XS G', 168223),
 ('US 60 / South 9th St (Manchester Bridge), downstream face', 168400), ('Manchester Bridge, upstream face', 168460),
 ('T. Tyler Potterfield Memorial Bridge, downstream', 169130), ('Potterfield Bridge, upstream', 169175),
 ('Station of Agnes sign at Tredegar St/Browns Island Way (derived, sign is 270 m off centerline)', 169640),
 ('XS H', 170220),
 ('US 1/301 Robert E. Lee Bridge, downstream face', 170500), ('Lee Bridge, upstream face', 170545),
 ('XS I', 175499), ('Confluence of Reedy Creek', 176113), ('XS J', 181150),
 ('SR 161 Westover Hills Blvd (Boulevard Bridge), downstream face', 181430), ('Boulevard Bridge, upstream face', 181475),
 ('XS K', 181608), ('Railroad bridge (CSX North End Sub per OSM), downstream', 184790), ('Railroad bridge, upstream', 184845),
 ('SR 76 Powhite Parkway, downstream face', 186050), ('Powhite Parkway, upstream face', 186100),
 ('Confluence of Powhite Creek', 186397),
 ('WEIR (lower), downstream', 196080), ('WEIR (lower), upstream', 196140),
 ('WEIR (upper), downstream', 197825), ('WEIR (upper), upstream', 197885),
 ('XS L', 198423), ('Confluence of Rattlesnake Creek', 201604),
 ('SR 147 Huguenot Road (Huguenot Bridge), downstream face', 203270), ('Huguenot Bridge, upstream face', 203315),
 ('Westham gauge 02037500 (station derived, +/-300 ft)', 203717), ('XS M', 205600),
 ('Confluence of Stony Point Creek', 208586), ('XS N', 209736),
 ('US 150 Chippenham Highway, downstream face', 211870), ('Chippenham, upstream face', 211920),
 ('WEIR (Cherokee reach), downstream', 213180), ('WEIR (Cherokee reach), upstream', 213240),
 ('Confluence of Cherokee Creek', 213710), ('XS O', 216099), ('Confluence of Pittaway Creek', 218417),
 ('Upstream end of plotted profile', 219150)]
if __name__ == '__main__':
    out = []
    for name, x in STATIONS:
        pg, vals = read(x)
        out.append({'name': name, 'station_ft': x, 'pdf_page': pg, 'panel': pr.PANELS[pg][0], 'raw': vals})
        print(f"{name[:60]:60s} {x:7d} {pr.PANELS[pg][0]} {[v[0] for v in vals]}")
    json.dump(out, open('/home/claude/floods-research/check/work/james_raw.json', 'w'), indent=1)
