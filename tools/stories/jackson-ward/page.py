#!/usr/bin/env python3
"""Write the Jackson Ward story page, pages/jackson-ward.md, from its source here (story.md).

    python3 tools/stories/jackson-ward/page.py

The count's numbers come from one file, tools/sanborn/jw/counts.json, and are filled in where
story.md says {{paved}}, {{corridor}} and {{all}}; nothing else in the text types them. The
region views and the link preview are made by views.py, the charts by charts.py and timeline.ts.
"""
import argparse
import datetime
import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.date.today().strftime('%B %-d, %Y'))
    a = ap.parse_args()
    c = json.load(open(os.path.join(ROOT, 'tools/sanborn/jw/counts.json')))
    text = open(os.path.join(HERE, 'story.md')).read()
    sp, sc = c['sensitivity']['paved'], c['sensitivity']['corridor']
    u = c['corridor']['uses_read']
    tokens = {'paved': c['paved']['buildings'], 'corridor': c['corridor']['buildings'], 'all': f"{c['all traced']['buildings']:,}", 'date': a.date,
              # how the edge and the rule move the count (count.py's `sensitivity` block)
              'paved_in': sp['edge_in_5m'], 'paved_out': sp['edge_out_5m'], 'corridor_in': sc['edge_in_5m'], 'corridor_out': sc['edge_out_5m'],
              'paved_any': sp['any_overlap'], 'corridor_any': sc['any_overlap'], 'paved_centroid': sp['centroid'], 'corridor_centroid': sc['centroid'],
              'beyond_paved': f"{round(100 * sp['beyond_traced_share'])}%", 'beyond_corridor': f"{round(100 * sc['beyond_traced_share'])}%",
              # what the letters on the sheets say the counted outlines were
              'read': sum(u.values()), 'dwellings': u['dwelling'], 'flats': u['flat'], 'garages': u['garage'], 'stores': u['store'],
              'church_outlines': u['church'], 'small': c['corridor']['buildings'] - c['corridor']['at_least_30m2'],
              'homes': u['dwelling'] + u['flat']}
    # The island picture's caption (history/jackson-ward.json) types its count; it must be the count's.
    h = open(os.path.join(ROOT, 'history/jackson-ward.json')).read()
    assert f"the {c['corridor']['buildings']} buildings on the 1952 Sanborn sheets" in h, 'the island caption does not match counts.json'
    assert f"({c['paved']['buildings']} on the Sanborn sheets)" in h, 'the paved island caption does not match counts.json'
    for k, v in tokens.items():
        text = text.replace('{{' + k + '}}', str(v))
    assert '{{' not in text, 'an unfilled {{token}} is left in story.md'
    open(os.path.join(ROOT, 'pages/jackson-ward.md'), 'w').write(text)
    print('wrote pages/jackson-ward.md')


if __name__ == '__main__':
    main()
