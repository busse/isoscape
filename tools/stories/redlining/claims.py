#!/usr/bin/env python3
"""Every sentence of the redlining page, with what it cites, for the fact check.

    python3 tools/stories/redlining/claims.py OUT.csv [--compare EARLIER.md] [--findings FINDINGS.csv]

With --findings (the independent check's findings.csv, keyed by the earlier draft's row
numbers), each finding is carried to the sentence of this page most like the one it was made on,
with the checker's verdict, severity and correction, and what was done about it
(factcheck_d4.json). A finding whose sentence was rewritten lands on the closest sentence and
says so; none is dropped.

Reads pages/redlining.md (written by page.py) and lists each sentence of its body, figure
captions, alt texts, tables and list items, in page order, with its section, the sources it
cites (resolved to their URLs and the date each was opened, from the page's Sources section),
and, for sentences drawn from the 1937 forms, the scan page of each area it names (FRASER
ad_RichmondVA.pdf, one page per area). Sentences with no citation are listed too, marked as such,
so a checker sees the whole page. The Sources section itself is not listed.
"""
import csv
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SCAN = 'https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/ad_RichmondVA.pdf'
# Scan pages of the area descriptions (read November 22, 2026), and of the forms' headings.
PAGE = {'A5': 5, 'C4': 26, 'C7': 29, 'D1': 37, 'D2': 38, 'D3': 39, 'D4': 40, 'D5': 41, 'D6': 42, 'D7': 43,
        'D8': 44, 'D9': 45, 'D10': 46, 'D11.5': 47, 'D11': 48}
FORM_KEYS = ('HOLC area description', 'FRASER, Richmond area descriptions')


def sources(text):
    """{key: (urls, opened)} from the Sources section: from d5 each entry is an H4 (`#### key`)
    followed by its text; earlier drafts used `- **key**: …` list items, still read."""
    sec = text[text.index('\n## Sources'):]
    sec = sec[:sec.index('\n## ', 5)] if '\n## ' in sec[5:] else sec
    out = {}
    pat = r'^#### (.+?)\n(.*?)(?=^#### |\Z)' if '\n#### ' in sec else r'^- \*\*([^*\n]+?)\*\*[^\n:]*:(.*?)(?=^- \*\*|\Z)'
    for m in re.finditer(pat, sec, flags=re.S | re.M):
        body = ' '.join(m.group(2).split())
        urls = re.findall(r'https?://[^\s),;>]+', body)
        op = re.findall(r'(?:opened|downloaded|fetched|read on the scan|read|cached)[^;.)]*\d{4}', body)
        out[m.group(1).strip()] = (' '.join(u.rstrip('.') for u in urls), '; '.join(op))
    return out


def sentences(block):
    block = ' '.join(block.split())
    # A sentence ends at . ! or ? (or one followed by a closing quote or bracket), before a
    # space and a capital, an emphasis mark or a bracket; not after "St." or "v." or an initial.
    parts, cur = [], ''
    for tok in re.split(r'(\s+)', block):
        cur += tok
        if re.search(r'[.!?]["”)\]]?$', tok) and not re.search(r'(\b(St|v|vol|ch|p|pp|No|Jr|Dr|Mr|etc|al)\.|\b[A-Z]\.)$', tok):
            parts.append(cur); cur = ''
    parts.append(cur)
    return [p.strip() for p in parts if re.search(r'[A-Za-z]{3}', p)]


def carry(rows, findings_path):
    """{new row index: [finding, ...]}: each finding placed on the most similar new sentence."""
    record = json.load(open(os.path.join(HERE, 'factcheck_d4.json')))
    acts, placed = record['actions'], record.get('placed', {})
    out = {}
    norm = lambda t: re.sub(r'\W+', ' ', t).lower()  # noqa: E731
    new = [norm(r[2]) for r in rows]
    for f in csv.DictReader(open(findings_path)):
        if not f['verdict']:
            continue
        old = norm(f['sentence'])
        pin = placed.get(f['row'])
        cand = [i for i, r in enumerate(rows) if pin in r[2]] if pin else []
        best = cand[0] if cand else max(range(len(new)), key=lambda i: difflib.SequenceMatcher(None, old, new[i], autojunk=False).ratio())
        ratio = difflib.SequenceMatcher(None, old, new[best], autojunk=False).ratio()
        f['match'] = 'rewritten; placed by a named phrase (factcheck_d4.json)' if cand else 'same sentence' if ratio > 0.97 else ('revised sentence' if ratio > 0.55 else f'rewritten; closest sentence ({ratio:.2f})')
        f['action'] = acts.get(f['row'], '' if not f['severity'] else 'MISSING')
        out.setdefault(best, []).append(f)
    return out


def main():
    out_path = sys.argv[1]
    findings = sys.argv[sys.argv.index('--findings') + 1] if '--findings' in sys.argv else None
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
        if st.startswith('> ') and kind == 'notice':
            buf.append(st[2:]); continue
        if st.startswith('- ') or st.startswith('> '):
            flush(); kind = 'list item' if st.startswith('- ') else 'notice'
            buf.append(st[2:]); continue
        if st == '':
            flush(); kind = 'caption' if infig else 'text'; continue
        buf.append(st)
    flush()

    placed = carry(rows, findings) if findings else {}
    # --compare OLD.md: how each sentence stands against an earlier draft's page.
    before = []
    if '--compare' in sys.argv:
        old_text = open(sys.argv[sys.argv.index('--compare') + 1]).read()
        old_text = old_text[:old_text.index('\n## Sources')]
        before = [re.sub(r'\W+', ' ', x).lower() for x in sentences(re.sub(r'\]\(#[a-z0-9-]+\)', '](#)', old_text))]

    def versus(sent):
        if not before:
            return ''
        nrm = re.sub(r'\W+', ' ', re.sub(r'\]\(#[a-z0-9-]+\)', '](#)', sent)).lower()
        if nrm in before:
            return 'same'
        r = max(difflib.SequenceMatcher(None, nrm, b, autojunk=False).ratio() for b in before)
        return 'revised' if r > 0.75 else 'new'
    with open(out_path, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['n', 'section', 'kind', 'sentence', 'cites', 'source_urls', 'opened', 'scan_pages', 'note', 'vs_d4'] +
                   (['d3_rows', 'check_verdict', 'check_severity', 'check_correction', 'match', 'd4_action'] if findings else []))
        for i, (sec, kind, s) in enumerate(rows, 1):
            keys = re.findall(r'\[([^\[\]]+)\]\(#[a-z0-9-]+\)', s)
            keys = [k for k in dict.fromkeys(keys) if k in src or k in ('numbers', 'measured here', 'counted on the map', 'How we know', 'how we know')]
            urls, opened, notes = [], [], []
            for k in keys:
                if k in ('numbers', 'measured here', 'counted on the map', 'How we know', 'how we know'):
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
            fs = placed.get(i - 1, [])
            j = lambda k: ' || '.join(f[k] for f in fs)  # noqa: E731
            w.writerow([i, sec, kind, s, '; '.join(keys), ' '.join(urls), ' | '.join(opened), pages, '; '.join(notes), versus(s)] +
                       (['; '.join(f['row'] for f in fs), j('verdict'), j('severity'), j('correction'), j('match'), j('action')] if findings else []))
    print(f'{len(rows)} sentences to {out_path}')


if __name__ == '__main__':
    main()
