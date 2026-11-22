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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def pct(x):
    return str(round(x * 100))


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
        'hD1': f"{n['motorway_in_d_by_area_km']['D1']:.1f}", 'hD5': f"{n['motorway_in_d_by_area_km']['D5']:.1f}", 'hD8': f"{n['motorway_in_d_by_area_km']['D8']:.1f}",
        'hlD': pct(n['motorway_and_links']['by_grade_share']['D']),
        'n2000D': pct(y['D']['share_2000_on']), 'n2000A': pct(y['A']['share_2000_on']),
        'jw_pct': pct(n['jackson_ward_1952_survival']['share_standing']), 'jw_n': f"{n['jackson_ward_1952_survival']['outlines_1952']:,}",
        'fD': pct(n['frame']['share_of_grade_inside']['D']), 'fC': pct(n['frame']['share_of_grade_inside']['C']),
    })
    t.update(boxes.tokens(n))
    t['yB'] = pct(y['B']['share_by1937'])
    t['BOXES'] = boxes.page_grid(t)
    # The framed menu sheet of the twelve D areas, when tools/sets/set.py has made it (see
    # sets/redlining-1937.json): an editorial proof, never a print for sale.
    menu = os.path.exists(os.path.join(ROOT, 'pages', 'redlining-menu.webp'))
    t['MENU'] = ('::: figure wide\n![The 1937 map framed by twelve numbered boxes, one for each D area, each a close view of it today with its number, its name and a short note on what the 1937 form recorded and what stands there now](redlining-menu.webp)\n\n'
                 "The twelve D areas as a set: the 1937 map in the middle, framed by a box for each area today. *How this was made:* composed by `tools/sets/set.py` from "
                 "`sets/redlining-1937.json` (written by `boxes.py`), from the same builds as the figures above; grades as Mapping Inequality digitized them (CC BY-NC 2.5). "
                 'An editorial sheet for this page only; it is not for sale. Working draft.\n:::') if menu else ''
    text = open(os.path.join(HERE, 'story.md')).read()
    # Notes to the drafters (<!-- … -->) stay in story.md only.
    text = re.sub(r'<!--.*?-->\n?', '', text, flags=re.S)
    for k, v in t.items():
        text = text.replace('{{' + k + '}}', str(v))
    assert '{{' not in text, 'an unfilled {{token}} is left in story.md'
    open(os.path.join(ROOT, 'pages/redlining.md'), 'w').write(text)
    print('wrote pages/redlining.md')


if __name__ == '__main__':
    main()
