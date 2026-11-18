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
    for k, v in {'paved': c['paved']['buildings'], 'corridor': c['corridor']['buildings'], 'all': f"{c['all traced']['buildings']:,}", 'date': a.date}.items():
        text = text.replace('{{' + k + '}}', str(v))
    assert '{{' not in text, 'an unfilled {{token}} is left in story.md'
    open(os.path.join(ROOT, 'pages/jackson-ward.md'), 'w').write(text)
    print('wrote pages/jackson-ward.md')


if __name__ == '__main__':
    main()
