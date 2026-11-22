#!/usr/bin/env python3
"""Write the redlining story page, pages/redlining.md, from its source here (story.md).

    python3 tools/stories/redlining/measure.py   # numbers.json
    python3 tools/stories/redlining/page.py

Every computed number comes from numbers.json and is filled in where story.md says {{name}};
nothing else in the text types them. The views are made by views.py, the charts by charts.py.
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxes  # noqa: E402
from fmt import pct  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def anchor(text):
    """GitHub's heading anchor (src/markdown.ts): lower case; letters, digits, spaces, hyphens and
    underscores kept; spaces to hyphens."""
    return re.sub(r'\s', '-', re.sub(r'[^\w\s-]', '', text.lower()).strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.date.today().strftime('%B %-d, %Y'))
    a = ap.parse_args()
    n = json.load(open(os.path.join(HERE, 'numbers.json')))
    g, m, y = n['graded_land'], n['motorway'], n['yearbuilt_by_grade']
    t = {'date': a.date}
    for k in 'ABCD':
        t[f'{k}_n'] = g[k]['areas']
        t[f'{k}_km2'] = f"{g[k]['km2']:.1f}"
        t[f'{k}_pct'] = pct(g[k]['share'])
        t[f'h{k}'] = pct(m['by_grade_share'][k])
        t[f'y{k}'] = pct(y[k]['share_by1937'])
    t.update({
        'hkm': f"{m['km_in_graded']:.1f}", 'hkm_all': f"{m['km_total_in_cache']:.0f}",
        'hkm_frame': f"{m['km_in_frame']:.0f}",
        'hD1': f"{n['motorway_in_d_by_area_km']['D1']:.1f}", 'hD5': f"{n['motorway_in_d_by_area_km']['D5']:.1f}", 'hD8': f"{n['motorway_in_d_by_area_km']['D8']:.1f}",
        'hlD': pct(n['motorway_and_links']['by_grade_share']['D']),
        'n2000D': pct(y['D']['share_2000_on']), 'n2000A': pct(y['A']['share_2000_on']),
        'jw_pct': pct(n['jackson_ward_1952_survival']['share_standing']), 'jw_n': f"{n['jackson_ward_1952_survival']['outlines_1952']:,}",
        'fD': pct(n['frame']['share_of_grade_inside']['D']), 'fC': pct(n['frame']['share_of_grade_inside']['C']),
    })
    t.update(boxes.tokens(n))
    t['HOW'] = boxes.HOW
    for k, v in n['terrain_by_grade'].items():
        t[f't{k}_med'] = f"{v['elev_median_m']:.0f}"
        t[f't{k}_p10'] = f"{v['elev_p10_m']:.0f}"
        t[f't{k}_steep'] = pct(v['share_steeper_10deg'])
    for k, v in n['frame']['share_of_area_outside'].items():
        t['cut_' + k.replace('.', '_')] = pct(v)
    t['hUn'] = f"{m['by_grade_km']['D'] - sum(n['motorway_in_d_by_area_km'].values()):.1f}"
    t['yB'] = pct(y['B']['share_by1937'])
    # The highway's base rates (measure.py `base_rate`): densities to two places, distances to
    # one, shares rounded once through pct.
    br = n['motorway_base_rate']
    for k, v in br['density'].items():
        t[f'dens_{k}'] = f"{v['km_per_km2']:.2f}"
    for k, v in br['density_near'].items():
        t[f'near_{k}'] = f"{v['km_per_km2']:.2f}"
    for k, v in br['median_distance_km'].items():
        t[f'med_{k}'] = f"{v:.1f}"
    loc = br['location_alone']
    t['exp_D'] = pct(loc['expected_share']['D'])
    t['exp_C'] = pct(loc['expected_share']['C'])
    t['exp_D_km'] = f"{loc['expected_km']['D']:.1f}"
    t['obs_D_km'] = f"{loc['observed_km']['D']:.1f}"
    t['ring_km'] = f"{br['ring_m'] / 1000:g}"
    t['near_km'] = f"{br['near_m'] / 1000:g}"
    t['near_D_km2'] = f"{br['density_near']['D']['km2']:.1f}"
    for s_, v in br['shift_D_share'].items():
        t[f'shift{s_}_lo'], t[f'shift{s_}_hi'] = pct(v['min']), pct(v['max'])
    t['edge_D_km'] = f"{br['D_km_within_25m_of_D_edge']:.1f}"
    t['A5_mkm'] = f"{n['areas']['A5']['motorway_km']:.1f}"
    oh = n['osm_checks']['D8_share_in_oregon_hill_district']
    t['oh_lo'], t['oh_hi'] = sorted([pct(v) for v in oh.values()], key=int)
    t['carver_D1'] = pct(n['osm_checks']['D1_share_west_of_belvidere_north_of_broad'])
    t['BOXES'] = boxes.page_grid(t)
    text = open(os.path.join(HERE, 'story.md')).read()
    # Notes to the drafters (<!-- … -->) stay in story.md only.
    text = re.sub(r'<!--.*?-->\n?', '', text, flags=re.S)
    for k, v in t.items():
        text = text.replace('{{' + k + '}}', str(v))
    assert '{{' not in text, 'an unfilled {{token}} is left in story.md'
    # Each citation lands on its entry in Sources (an H4 there, so GitHub's anchor rule names it).
    keys = re.findall(r'^#### (.+)$', text[text.index('\n## Sources'):], flags=re.M)
    anchors = {k: anchor(k) for k in keys}

    def cite(m):
        k = m.group(1)
        if k == 'sources':  # a link to the section itself
            return m.group(0)
        assert k in anchors, f'cited source "{k}" has no entry in Sources'
        return f'[{k}](#{anchors[k]})'
    text = re.sub(r'\[([^\[\]]+)\]\(#sources\)', cite, text)
    open(os.path.join(ROOT, 'pages/redlining.md'), 'w').write(text)
    print('wrote pages/redlining.md')


if __name__ == '__main__':
    main()
