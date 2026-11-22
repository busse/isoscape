#!/usr/bin/env python3
"""Write tools/stories/dollar-stores/counts.json: every number the story page prints, in one file.

    python3 tools/stories/dollar-stores/counts.py <stores_dedup.csv.gz>

Reads the committed results in drafts/dollar-stores-virginia/casestudy/ (tests.csv and
dg_classes.csv from step 9, snap_tests.csv from step 13, towns_tests.csv and towns_thirds.csv
from step 14). Two numbers need the store table itself, which is too big for git: the in-town
share approved after 2005 and the West Virginia junction count. page.py fills story.md from the
JSON; nothing in the text types a number. Made with Claude.
"""
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CS = os.path.join(ROOT, 'drafts/dollar-stores-virginia/casestudy')
PRIMARY = 'Set B: six states, small incorporated (PRIMARY)'
CONTRAST = 'Set B: small incorporated, convenience stores (stated contrast)'


def pct(v):
    return f'{v:.0%}'


def main():
    st = pd.read_csv(sys.argv[1], low_memory=False)
    t = pd.read_csv(f'{CS}/2026-11-21-09-replication/data/tests.csv')
    T = {(r.label, r.test): r for r in t.itertuples()}
    cls = pd.read_csv(f'{CS}/2026-11-21-09-replication/data/dg_classes.csv')
    six = cls[(cls.set == 'B') & (cls.unit == 'small')].groupby('class')['stores'].sum()
    c = {k: T[(PRIMARY, k)] for k in ('C1', 'C2', 'C3', 'C4', 'C5 (lead)', 'C6')}
    k = {k: T[(CONTRAST, k)] for k in ('C1', 'C2', 'C3')}
    small = st[(st.set == 'B') & (st.unit == 'small') & (st.kind == 'Dollar General') & (st.edge_dist > 30)]
    town = small[small.A_lead <= 1]
    wv = small[(small.state == 'WV') & (small.A_lead > 1) & (small.A_lead <= 2)]
    va = st[(st.state == 'VA') & (st.unit.isin(['small', 'CDP'])) & (st.kind == 'Dollar General')
            & (st.A_lead > 1) & (st.A_lead <= 2) & (st.edge_dist > 30)]
    s = pd.read_csv(f'{CS}/2026-11-22-13-snap/snap_tests.csv')
    s1 = s[(s.test == 'S1') & s.primary].iloc[0]
    s2 = s[(s.test == 'S2') & (s.measure == '3 km')].iloc[0]
    tw = pd.read_csv(f'{CS}/2026-11-22-14-snap-towns/towns_tests.csv').set_index('test')
    th = pd.read_csv(f'{CS}/2026-11-22-14-snap-towns/towns_thirds.csv').set_index('third')
    total = int(six.sum())
    edge = int(six['edge band'])
    out = {
        'total': f'{total:,}', 'edge': edge, 'one_in': round(total / edge), 'town': f"{int(six['in town']):,}",
        'margin': int(six['on the edge line (margin)']), 'farther': int(six['beyond A 2']),
        'places': int(c['C2'].n_places),
        'band_expected': pct(c['C5 (lead)'].expected / c['C5 (lead)'].n_stores), 'band_share': pct(c['C5 (lead)'].share),
        'junction': pct(c['C2'].share), 'junction_exp': pct(c['C2'].expected / c['C2'].n_stores),
        'junction_x': f"{c['C2'].share / (c['C2'].expected / c['C2'].n_stores):.0f}",
        'junction_one_in': round(1 / c['C2'].share), 'junction_conv': pct(k['C2'].share),
        'busiest': pct(c['C1'].share), 'busiest_exp': pct(c['C1'].expected / c['C1'].n_stores),
        'busiest_conv': pct(k['C1'].share),
        'inside': pct(c['C3'].share), 'inside_exp': pct(c['C3'].expected / c['C3'].n_stores),
        'outside': pct(1 - c['C3'].share), 'inside_conv': pct(k['C3'].share),
        'traffic_x': f"{c['C6'].share:.1f}",
        'new_edge': pct(c['C4'].share), 'new_town': pct((town.auth_year > 2005).mean()),
        'wv_edge': len(wv), 'wv_junction': int((wv.junction_m <= 250).sum()),
        'va_grid': len(va),
        's1_store': f'{s1.stores_mean:.1%}', 's1_null': f'{s1.null_mean:.1%}',
        's1_gap': f'{max(abs(s1.D_low), abs(s1.D_high)) * 100:.1f}',
        's2_store': f'{s2.stores_mean:.1%}', 's2_null': f'{s2.null_mean:.1%}',
        't_places': f"{int(tw.loc['T1', 'places']):,}",
        't1': f"{tw.loc['T1', 'rate_ratio_per_10pts']:.2f}", 't1_lo': f"{tw.loc['T1', 'low']:.2f}",
        't1_hi': f"{tw.loc['T1', 'high']:.2f}", 't2': f"{tw.loc['T2', 'rate_ratio_per_10pts']:.2f}",
        't_grocery': f"{tw.loc['T3 grocery', 'rate_ratio_per_10pts']:.2f}",
        't_conv': f"{tw.loc['T3 convenience', 'rate_ratio_per_10pts']:.2f}",
        'third_lo_dg': f"{th.loc['lowest third', 'dg_per_1000_hh']:.2f}",
        'third_hi_dg': f"{th.loc['highest third', 'dg_per_1000_hh']:.2f}",
        'third_lo_gr': f"{th.loc['lowest third', 'grocery_per_1000_hh']:.2f}",
        'third_hi_gr': f"{th.loc['highest third', 'grocery_per_1000_hh']:.2f}",
    }
    json.dump(out, open(os.path.join(HERE, 'counts.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
