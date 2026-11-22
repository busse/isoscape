#!/usr/bin/env python3
"""Every sentence of the redlining page, with what it cites, for the fact check.

    python3 tools/stories/redlining/claims.py OUT.csv

Reads pages/redlining.md (written by page.py) and lists each sentence of its body, figure
captions, alt texts, tables and list items, in page order, with its section, the sources it
cites (resolved to their URLs and the date each was opened, from the page's Sources section),
and, for sentences drawn from the 1937 forms, the scan page of each area it names (FRASER
ad_RichmondVA.pdf, one page per area). Sentences with no citation are listed too, marked as such,
so a checker sees the whole page. The Sources section itself is not listed.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SCAN = 'https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/ad_RichmondVA.pdf'
# Scan pages of the area descriptions (read November 22, 2026), and of the forms' headings.
PAGE = {'A5': 5, 'C7': 29, 'D1': 37, 'D2': 38, 'D3': 39, 'D4': 40, 'D5': 41, 'D6': 42, 'D7': 43,
        'D8': 44, 'D9': 45, 'D10': 46, 'D11.5': 47, 'D11': 48}
FORM_KEYS = ('HOLC area description', 'FRASER, Richmond area descriptions')


def sources(text):
    """{key: (urls, opened)} from the Sources section's `- **key**: …` entries."""
    sec = text[text.index('\n## Sources'):]
    sec = sec[:sec.index('\n## ', 5)] if '\n## ' in sec[5:] else sec
    out = {}
    for m in re.finditer(r'^- \*\*([^*\n]+?)\*\*[^\n:]*:(.*?)(?=^- \*\*|\Z)', sec, flags=re.S | re.M):
        body = ' '.join(m.group(2).split())
        urls = re.findall(r'https?://[^\s),;]+', body)
        op = re.findall(r'(?:opened|downloaded|fetched|read on the scan|cached)[^;.)]*\d{4}', body)
        out[m.group(1)] = (' '.join(u.rstrip('.') for u in urls), '; '.join(op))
    return out


def sentences(block):
    block = ' '.join(block.split())
    # A sentence ends at . ! or ? (or one followed by a closing quote or bracket), before a
    # space and a capital, an emphasis mark or a bracket; not after "St." or "v." or an initial.
    parts, cur = [], ''
    for tok in re.split(r'(\s+)', block):
        cur += tok
        if re.search(r'[.!?]["”)\]]?$', tok) and not re.search(r'(\b(St|v|vol|ch|p|pp|No|Jr|Dr|Mr|etc)\.|\b[A-Z]\.)$', tok):
            parts.append(cur); cur = ''
    parts.append(cur)
    return [p.strip() for p in parts if re.search(r'[A-Za-z]{3}', p)]


def main():
    out_path = sys.argv[1]
    text = open(os.path.join(ROOT, 'pages', 'redlining.md')).read()
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    src = sources(text)
    body = text.split('\n---\n', 1)[1]
    body = body[:body.index('\n## Sources')]
    rows, section, buf, kind = [], '', [], 'text'

    def flush():
        nonlocal buf
        if buf:
            for s in sentences(' '.join(buf)):
                rows.append((section, kind, s))
        buf = []

    infig = False
    for line in body.split('\n'):
        st = line.strip()
        if st.startswith('#'):
            flush(); section = st.lstrip('#').strip(); continue
        if st.startswith(':::'):
            flush(); infig = st != ':::'; kind = 'caption' if infig else 'text'; continue
        if st.startswith('!['):
            flush()
            alt = re.match(r'!\[(.*?)\]', st)
            rows.append((section, 'alt text', alt.group(1)))
            continue
        if st.startswith('|'):
            flush()
            if not re.match(r'^\|[-| ]+\|$', st):
                rows.append((section, 'table row', ' | '.join(c.strip() for c in st.strip('|').split('|'))))
            continue
        if st.startswith('- ') or st.startswith('> '):
            flush(); kind = 'list item' if st.startswith('- ') else 'notice'
            buf.append(st[2:]); continue
        if st == '':
            flush(); kind = 'caption' if infig else 'text'; continue
        buf.append(st)
    flush()

    with open(out_path, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['n', 'section', 'kind', 'sentence', 'cites', 'source_urls', 'opened', 'scan_pages', 'note'])
        for i, (sec, kind, s) in enumerate(rows, 1):
            keys = re.findall(r'\[([^\[\]]+)\]\(#(?:sources|how-we-know)\)', s)
            keys = [k for k in dict.fromkeys(keys)]
            urls, opened, notes = [], [], []
            for k in keys:
                if k in ('numbers', 'measured here', 'How we know', 'how we know'):
                    urls.append('tools/stories/redlining/numbers.json'); opened.append('computed by measure.py')
                    continue
                base = re.sub(r' [A-D]\d+(\.\d)?$', '', k)
                hit = src.get(k) or src.get(base) or next((v for kk, v in src.items() if kk.startswith(base)), None)
                if hit:
                    urls.append(hit[0]); opened.append(hit[1] or 'see Sources')
                else:
                    notes.append(f'cite "{k}" not found in Sources')
            pages = ''
            if any(k.startswith(FORM_KEYS) for k in keys) or (kind == 'caption' and 'What the 1937 form recorded' in s):
                labs = re.findall(r'\b([ACD]\d+(?:\.5)?)\b', s)
                pages = '; '.join(f'{l} p. {PAGE[l]}' for l in dict.fromkeys(labs) if l in PAGE)
                if pages:
                    urls.append(SCAN)
            if not keys and kind not in ('alt text',):
                notes.append('no citation on the page (framing, method or description)')
            if kind == 'alt text':
                notes.append('describes the picture')
            w.writerow([i, sec, kind, s, '; '.join(keys), ' '.join(urls), ' | '.join(opened), pages, '; '.join(notes)])
    print(f'{len(rows)} sentences to {out_path}')


if __name__ == '__main__':
    main()
