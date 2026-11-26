#!/usr/bin/env python3
"""Write the floods story page, pages/richmond-floods.md, from its source here (story.md).

    python3 tools/stories/richmond-floods/figures.py   # the pictures (pages/richmond-floods-*.webp)
    python3 tools/stories/richmond-floods/page.py

Every computed number comes from drafts/richmond-floods/counts.json ("rc3": each drawing's counts
from its build) or tools/floods/rain/data/rain.json (the rain analysis), and is filled in where
story.md says {{name}}; nothing else in the text types them. Each citation written
[Key](#sources) lands on its entry under Sources (an H4, so GitHub's anchor rule names it).
Notes to the drafters (<!-- … -->) stay in story.md. Made with Claude.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PLATES = {
    '1771': 'shockoe-1788-flood-1771', '1936': 'shockoe-1936-flood-1936', '1969': 'shockoe-1969-flood-1969',
    '1972': 'shockoe-1972-flood-1972', '1985': 'shockoe-1985-flood-1985', '1996': 'shockoe-1996-flood-1996',
    '2020': 'shockoe-2020-flood-2020', 'gaston': 'shockoe-2004-flood-gaston-b', 'tw': 'shockoe-2026-flood-agnes-today',
    'mw': 'manchester-2026-flood-agnes-today', 'mnw': 'manchester-2026-flood-agnes-today-nowall',
}
OVERTOPPED_FT = 41.0   # NWS RICV2 impacts: "Flood wall is overtopped"
FRAN_FT = 22.7         # levels.json, 1996-09


def anchor(text):
    """GitHub's heading anchor (src/markdown.ts)."""
    return re.sub(r'\s', '-', re.sub(r'[^\w\s-]', '', text.lower()).strip())


def tokens():
    c = json.load(open(os.path.join(ROOT, 'drafts/richmond-floods/counts.json')))['rc3']
    t = {}
    for k, n in PLATES.items():
        p = c['plates'][n]
        t[f'a_{k}'] = f"{p['floodAcres']:,.1f}"
        t[f'n_{k}'] = f"{p['floodShownInWater']:,}"
        t[f's_{k}'] = f"{p['floodShown']:,}"
        if 'floodShownDepthMedianFt' in p:
            t[f'med_{k}'] = f"{p['floodShownDepthMedianFt']:g}"
            t[f'max_{k}'] = f"{p['floodShownDepthMaxFt']:g}"
        if 'floodUnknownAcres' in p:
            t[f'ua_{k}'] = f"{p['floodUnknownAcres']:,.1f}"
            t[f'ub_{k}'] = f"{p['floodUnknownBuildings']:,}"
    b = c['boxes']['shockoe']['1972:1972']
    t['dm_1972'] = round(b['market']['depthFt'])
    t['ds_1972'] = round(b['station']['depthFt'])
    t['dd_1972'] = round(b['dock']['depthFt'])
    t['dg_market'] = round(c['boxes']['shockoe']['gaston-b:2004']['g-market']['depthFt'])
    t['dm_hull'] = round(c['boxes']['manchester']['agnes-today-nowall:2026']['hull']['depthFt'])
    r = json.load(open(os.path.join(ROOT, 'tools/floods/rain/data/rain.json')))
    t['rain_total'] = f"{r['basin_total_in']['radar_corrected']:.0f}"
    t['rain_low'] = f"{r['basin_total_in']['low']:.1f}"
    t['rain_high'] = f"{r['basin_total_in']['high']:.1f}"
    t['peak_hour'] = f"{r['basin_peak_hour']['inches']:.1f}"
    t['six_hour'] = f"{r['basin_max_n_hour']['6']['inches']:.0f}"
    t['ws_sqmi'] = f"{r['watershed']['area_km2'] / 2.589988:.0f}"
    t['ws_acres'] = f"{round(r['watershed']['area_acres'], -1):,.0f}"
    t['gallons'] = f"{r['basin_volume']['million_gallons'] / 1000:.1f}"
    # Fran's level may be a foot higher (its datum is not recorded): the gap is given as a range.
    t['fran_gap'] = f"{OVERTOPPED_FT - FRAN_FT - 1:.0f} to {OVERTOPPED_FT - FRAN_FT:.0f}"
    # The lidar's ground (the spill test, steps 15 and 20 of the case study): the pit beside the
    # 17th Street Market, 4.07 m; 17th and Main, 6.58 m.
    t['low_pit'] = f"{4.07 / 0.3048:.1f}"
    t['ground_17main'] = f"{6.58 / 0.3048:.1f}"
    return t


def main():
    t = tokens()
    text = open(os.path.join(HERE, 'story.md')).read()
    text = re.sub(r'<!--.*?-->\n?', '', text, flags=re.S)
    for k, v in t.items():
        text = text.replace('{{' + k + '}}', str(v))
    left = re.findall(r'\{\{(\w+)\}\}', text)
    assert not left, f'unfilled tokens: {left}'
    keys = re.findall(r'^#### (.+)$', text[text.index('\n## Sources'):], flags=re.M)
    anchors = {k: anchor(k) for k in keys}

    def cite(m):
        k = re.sub(r'\s+', ' ', m.group(1))
        if k.lower() == 'sources':
            return m.group(0)
        assert k in anchors, f'cited source "{k}" has no entry in Sources'
        return f'[{k}](#{anchors[k]})'
    text = re.sub(r'\[([^\[\]]+)\]\(#sources\)', cite, text)
    used = set(re.findall(r'\]\(#([\w-]+)\)', text))
    unused = [k for k, a in anchors.items() if a not in used]
    assert not unused, f'sources never cited: {unused}'
    open(os.path.join(ROOT, 'pages/richmond-floods.md'), 'w').write(text)
    body = text[text.index('\n# '):text.index('\n## Sources')]
    words = len(re.findall(r"[A-Za-z0-9][\w'’.,-]*", re.sub(r'\]\([^)]*\)|!\[[^\]]*\]|[#*>|:_`\[\]]', ' ', body)))
    print(f'wrote pages/richmond-floods.md ({words:,} words before Sources)')


if __name__ == '__main__':
    main()
