#!/usr/bin/env python3
"""Make a story page's PDFs: a phone edition and a large-screen (US Letter) edition.

    python3 tools/pdf/story_pdf.py <slug> [--edition phone|large|both] [--out DIR] [--date "November 22, 2026"]

It reads pages/<slug>.md, so a rebuilt page gives a rebuilt PDF, and writes
<DIR>/<slug>-phone.pdf and <DIR>/<slug>-large.pdf (DIR defaults to out/pdf). To publish, point
--out at the site's p/ folder, beside p/<slug>.html; see "Story PDFs" in the README.

How:
  1. Every picture the page names (and its `social:` picture, for the title page) is prepared for
     the edition: the larger copy (`<name>-large.<ext>`) where there is one, scaled to at most
     1440 px wide for the phone and 3200 px for the large edition, saved as JPEG (4:4:4, quality
     78 and 82), since Chrome would otherwise store a WebP losslessly. SVGs are copied with their
     fonts set to the PDF's own (embedded in the copy), so they print as vector type. Tall pictures
     are scanned for blank rows, where tools/pdf/print.ts may cut them across pages.
  2. tools/pdf/print.ts writes the print document (layout, title page, contents, colophon).
  3. Headless Chrome prints it to PDF (`--print-to-pdf`, sandbox on, file:// only), with a tagged
     structure and an outline from the headings. The contents list's page numbers come from the
     first printing, and it is printed again until they hold.
  4. pikepdf writes the document facts (title, author, subject, keywords, language) and the
     viewer preferences, and the result is checked: fonts embedded and from the allowed list,
     tagged, every page the expected size, no picture squeezed or running off the text area
     unless cut on purpose, body type at the edition's size (a document Chrome shrank to fit
     something too wide would not be).
  5. The print build rewords the page's few instructions to a screen (tools/pdf/wording.ts and
     tools/stories/<story>/pdf.json), prints every change, and stops if any such instruction is
     left that no rule covers.

Needs: Node 22.18+, Google Chrome or Chromium ($CHROME), Python 3 with Pillow, pikepdf and pdfplumber, and
rsvg-convert (librsvg) to look for blank rows in a tall SVG. No network.
"""
import argparse
import base64
import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pikepdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PAGES = os.path.join(ROOT, 'pages')
AUTHOR = 'Chris Busse'
SITE_URL = 'https://isoscape.chrisbusse.com/'

# Per edition: the widest picture kept, JPEG quality, the page size in points.
EDITION = {
    'phone': {'max_w': 1440, 'quality': 78, 'pt': (270, 480), 'label': 'Phone edition'},
    'large': {'max_w': 3200, 'quality': 82, 'pt': (612, 792), 'label': 'Large-screen edition (US Letter)'},
}
# Fonts a PDF may embed: the vendored Inter (tools/pdf/fonts) and Libre Baskerville
# (tools/print/fonts), both under the SIL Open Font License.
ALLOWED_FONTS = re.compile(r'^([A-Z]{6}\+)?(Inter|LibreBaskerville)[-A-Za-z]*$')
FONTS = {
    'Inter PDF': [('Inter-Regular.ttf', 400, 'normal'), ('Inter-Italic.ttf', 400, 'italic'), ('Inter-SemiBold.ttf', 600, 'normal'), ('Inter-Bold.ttf', 700, 'normal')],
    'Libre Baskerville PDF': [('../../print/fonts/libre-baskerville-latin-400-normal.woff', 400, 'normal'), ('../../print/fonts/libre-baskerville-latin-400-italic.woff', 400, 'italic'), ('../../print/fonts/libre-baskerville-latin-700-normal.woff', 700, 'normal')],
}
IMAGE = re.compile(r'!\[[^\]]*\]\(([^)\s]+)\)')


def chrome() -> str:
    for c in [os.environ.get('CHROME'), 'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser',
              '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:
        if c and (shutil.which(c) or os.path.exists(c)):
            return shutil.which(c) or c
    sys.exit('story_pdf: no Chrome or Chromium found (set $CHROME)')


def front_matter(src: str) -> dict:
    m = re.match(r'^---\n([\s\S]*?)\n---', src)
    out = {}
    for line in (m.group(1).split('\n') if m else []):
        kv = re.match(r'^\s*([A-Za-z][\w-]*)\s*:\s*(.*?)\s*$', line)
        if kv:
            out[kv.group(1)] = kv.group(2).strip('"\'')
    return out


def pictures(src: str) -> list:
    names = []
    for n in IMAGE.findall(src) + ([front_matter(src)['social']] if 'social' in front_matter(src) else []):
        n = n.removeprefix('./')
        if re.fullmatch(r'[\w.-]+\.(svg|png|jpe?g|webp)', n, re.I) and n not in names:
            names.append(n)
    return names


# ---- pictures -----------------------------------------------------------------------------------

def blank_rows(img: Image.Image) -> list:
    """Rows (as fractions of the height) at the middle of each blank band at least 4 px high (at 400 px wide)."""
    g = img.convert('RGB').resize((400, max(1, round(img.height * 400 / img.width))))
    bg = g.getpixel((2, 2))
    w, h = g.size
    px = g.load()
    blank = []
    for y in range(h):
        blank.append(all(max(abs(px[x, y][k] - bg[k]) for k in range(3)) <= 8 for x in range(0, w, 2)))
    out, run = [], None
    for y, b in enumerate(blank + [False]):
        if b and run is None:
            run = y
        elif not b and run is not None:
            if y - run >= 4:
                out.append(round((run + y) / 2 / h, 5))
            run = None
    return out


def font_faces() -> str:
    css = []
    for family, files in FONTS.items():
        for f, weight, style in files:
            path = os.path.normpath(os.path.join(HERE, 'fonts', f))
            kind = 'woff' if path.endswith('.woff') else 'truetype'
            data = base64.b64encode(open(path, 'rb').read()).decode()
            css.append(f"@font-face{{font-family:'{family}';src:url(data:font/{'woff' if kind == 'woff' else 'ttf'};base64,{data}) format('{kind}');font-weight:{weight};font-style:{style}}}")
    return '\n'.join(css)


STACK = re.compile(r"(?<![\w'\"-])(?:(?:'[^']+'|\"[^\"]+\"|-?[A-Za-z][\w-]*)\s*,\s*)*(sans-serif|serif|monospace)(?![\w-])")


def print_svg(text: str) -> str:
    """An SVG for print: its font stacks set to the PDF's embedded fonts, and those fonts inside it."""
    text = STACK.sub(lambda m: "'Libre Baskerville PDF', serif" if m.group(1) == 'serif' else "'Inter PDF', sans-serif", text)
    i = text.find('<style>')
    faces = font_faces()
    if i >= 0:
        return text[:i + 7] + '\n' + faces + '\n' + text[i + 7:]
    j = text.find('>', text.find('<svg')) + 1
    return text[:j] + f'<style>{faces}</style>' + text[j:]


def prepare(name: str, edition: str, work: str) -> dict:
    spec = EDITION[edition]
    path = os.path.join(PAGES, name)
    stem, ext = os.path.splitext(name)
    if ext.lower() == '.svg':
        text = open(path, encoding='utf-8').read()
        out = os.path.join(work, name)
        open(out, 'w', encoding='utf-8').write(print_svg(text))
        m = re.search(r'<svg[^>]*viewBox="[\d.\s-]*?\s([\d.]+)\s+([\d.]+)"', text)
        w, h = float(m.group(1)), float(m.group(2))
        info = {'file': name, 'w': w, 'h': h}
        if h / w > 1.2:
            png = subprocess.run(['rsvg-convert', '-w', '400', path], capture_output=True, check=True).stdout
            info['gaps'] = blank_rows(Image.open(io.BytesIO(png)))
        return info
    large = os.path.join(PAGES, f'{stem}-large{ext}')
    img = Image.open(large if os.path.exists(large) else path)
    img.load()
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGBA')
        ground = Image.new('RGB', img.size, (255, 255, 255))
        ground.paste(img, mask=img.split()[3])
        img = ground
    img = img.convert('RGB')
    if img.width > spec['max_w']:
        img = img.resize((spec['max_w'], round(img.height * spec['max_w'] / img.width)), Image.LANCZOS)
    out = f'{stem}.jpg'
    img.save(os.path.join(work, out), 'JPEG', quality=spec['quality'], subsampling=0, optimize=True, progressive=False)
    info = {'file': out, 'w': img.width, 'h': img.height}
    if img.height / img.width > 1.2:
        info['gaps'] = blank_rows(img)
    return info


# ---- printing -----------------------------------------------------------------------------------

def run_print_ts(slug: str, edition: str, work: str, date: str, pages: dict | None) -> dict:
    args = ['node', os.path.join(HERE, 'print.ts'), slug, '--edition', edition, '--assets', os.path.join(work, 'assets.json'),
            '--date', date, '--pages-dir', PAGES, '--out', os.path.join(work, 'page.html')]
    if pages is not None:
        json.dump(pages, open(os.path.join(work, 'pages.json'), 'w'))
        args += ['--pages', os.path.join(work, 'pages.json')]
    res = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    if res.returncode != 0:
        sys.exit(f'story_pdf: print.ts failed\n{res.stderr}')
    return json.loads(res.stdout)


def run_chrome(work: str, out: str) -> None:
    if os.path.exists(out):
        os.remove(out)
    profile = os.path.join(work, 'profile')
    res = subprocess.run([chrome(), '--headless=new', f'--user-data-dir={profile}', '--no-first-run', '--disable-extensions',
                          '--no-pdf-header-footer', '--generate-pdf-document-outline', f'--print-to-pdf={out}',
                          'file://' + os.path.join(work, 'page.html')], capture_output=True, text=True, timeout=600)
    if not os.path.exists(out):
        sys.exit(f'story_pdf: Chrome wrote no PDF\n{res.stderr[-2000:]}')


def section_pages(pdf_path: str, ids: list) -> dict:
    """The page (from 1) each named destination lands on, for the given heading ids."""
    pdf = pikepdf.open(pdf_path)
    index = {p.objgen: i + 1 for i, p in enumerate(pdf.pages)}
    dests = pdf.Root.get('/Dests')
    out = {}
    if dests is not None:
        for k, v in dests.items():
            name = k.lstrip('/')
            arr = v.get('/D') if isinstance(v, pikepdf.Dictionary) else v
            if name in ids and arr is not None:
                out[name] = index.get(arr[0].objgen)
    return out


def finish(pdf_path: str, doc: dict, slug: str, edition: str, date_iso: str, summary: str) -> None:
    url = f'{SITE_URL}p/{slug}.html'
    pdf = pikepdf.open(pdf_path, allow_overwriting_input=True)
    subject = summary
    keywords = ['isoscape', 'Richmond, Virginia', 'maps', 'history', doc['short'], EDITION[edition]['label']]
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta['dc:title'] = doc['title']
        meta['dc:creator'] = [AUTHOR]
        meta['dc:description'] = subject
        meta['dc:language'] = ['en-US']
        meta['dc:subject'] = keywords
        meta['pdf:Keywords'] = ', '.join(keywords)
        meta['pdf:Producer'] = 'Skia/PDF (Chrome), pikepdf'
        meta['xmp:CreatorTool'] = "isoscape's story PDF tool (tools/pdf/story_pdf.py)"
        meta['xmp:CreateDate'] = date_iso
        meta['xmp:ModifyDate'] = date_iso
    # Chrome tags a <figure> (the picture with its caption) as a Figure with no alternate text;
    # the picture inside it carries the alt text. Such a group is a Div, so readers do not
    # announce an empty figure.
    def regroup(e) -> None:
        if isinstance(e, pikepdf.Array):
            for x in e:
                regroup(x)
            return
        if not isinstance(e, pikepdf.Dictionary) or '/S' not in e:
            return
        if e.S == '/Figure' and not str(e.get('/Alt', '')).strip():
            e.S = pikepdf.Name('/Div')
        if '/K' in e:
            regroup(e.K)
    regroup(pdf.Root.StructTreeRoot.get('/K'))
    # Chrome builds the outline from the headings' rendered lines and drops the space at each line
    # break; put back each heading's own text.
    texts = {re.sub(r'\s+', '', t): t for t in doc['headings']}
    with pdf.open_outline() as outline:
        def fix(items) -> None:
            for it in items:
                key = re.sub(r'\s+', '', str(it.title))
                if key in texts:
                    it.title = texts[key]
                fix(it.children)
        fix(outline.root)
    pdf.docinfo['/Title'] = doc['title']
    pdf.docinfo['/Author'] = AUTHOR
    pdf.docinfo['/Subject'] = subject
    pdf.docinfo['/Keywords'] = ', '.join(keywords)
    pdf.docinfo['/Creator'] = f"isoscape's story PDF tool, from {url}"
    pdf.Root.Lang = pikepdf.String('en-US')
    pdf.Root.ViewerPreferences = pikepdf.Dictionary(DisplayDocTitle=True)
    pdf.Root.PageMode = pikepdf.Name('/UseOutlines')
    pdf.save(pdf_path, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)


def check(pdf_path: str, edition: str) -> dict:
    info = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True).stdout
    fonts = subprocess.run(['pdffonts', pdf_path], capture_output=True, text=True).stdout.splitlines()[2:]
    problems = []
    names = sorted({f.split()[0] for f in fonts})
    for f in fonts:
        cols = f.split()
        if not ALLOWED_FONTS.match(cols[0]):
            problems.append(f'font not on the allowed list: {cols[0]}')
        if 'Type 3' in f:
            problems.append(f'Type 3 font: {cols[0]}')
        if cols[-5] != 'yes':
            problems.append(f'font not embedded: {cols[0]}')
        if cols[-3] != 'yes':
            problems.append(f'font without a Unicode map: {cols[0]}')
    if 'Tagged:          yes' not in info:
        problems.append('not tagged')
    w, h = EDITION[edition]['pt']
    sizes = subprocess.run(['pdfinfo', '-f', '1', '-l', '9999', pdf_path], capture_output=True, text=True).stdout
    for m in re.finditer(r'Page\s+(\d+) size:\s+([\d.]+) x ([\d.]+) pts', sizes):
        if abs(float(m.group(2)) - w) > 1 or abs(float(m.group(3)) - h) > 1:
            problems.append(f'page {m.group(1)} is {m.group(2)} x {m.group(3)} pt')
    pages = int(re.search(r'Pages:\s+(\d+)', info).group(1))
    return {'pages': pages, 'bytes': os.path.getsize(pdf_path), 'fonts': names, 'problems': problems}


def placement_problems(pdf_path: str, edition: str, html: str, assets: dict) -> list:
    """Pictures that are cut, squeezed or run off the page.

    Every raster picture placed in the PDF must keep its own proportions, and must sit inside the
    page's text area, except where the print build cuts it on purpose (the halves of a wide
    picture, the pieces of a tall one: a `<div class="crop">` in the print HTML). So for each
    picture, the placements that leave the text area may not outnumber its deliberate crops.
    """
    import pdfplumber
    margin = {'phone': (22, 18, 40, 18), 'large': (60, 72, 70, 72)}[edition]
    t, r, b, l = (m * 0.75 for m in margin)
    # Pictures are told apart by their pixel size (several share one: they are counted together).
    size_of = {a['file']: (a['w'], a['h']) for a in assets.values() if not a['file'].endswith('.svg')}
    names = {}
    for f, wh in size_of.items():
        names.setdefault(wh, []).append(f)
    crops = {}
    for m in re.finditer(r'<div class="crop"[^>]*><img src="([^"]*)"', html):
        if m.group(1) in size_of:
            crops[size_of[m.group(1)]] = crops.get(size_of[m.group(1)], 0) + 1
    outside, problems = {}, []
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            W, H = page.width, page.height
            for im in page.images:
                sw, sh = im['srcsize']
                bw, bh = im['x1'] - im['x0'], im['bottom'] - im['top']
                key = (sw, sh)
                f = ' or '.join(names.get(key, [f'{sw}x{sh}']))
                if bw <= 0 or bh <= 0 or abs((bw / bh) / (sw / sh) - 1) > 0.01:
                    problems.append(f'page {n}: {f} is squeezed ({bw:.0f} x {bh:.0f} pt for {sw} x {sh} px)')
                if im['x0'] < l - 1 or im['x1'] > W - r + 1 or im['top'] < t - 1 or im['bottom'] > H - b + 1:
                    outside[key] = outside.get(key, 0) + 1
                    if outside[key] > crops.get(key, 0):
                        problems.append(f'page {n}: {f} runs outside the text area and is not a deliberate crop (cut off)')
        # Chrome shrinks a whole document to fit anything wider than the page: then every size is
        # off. The commonest type size must be the edition's body size.
        sizes = {}
        for page in pdf.pages[2:]:
            for ch in page.chars:
                sizes[round(ch['size'], 1)] = sizes.get(round(ch['size'], 1), 0) + 1
        body = max(sizes, key=sizes.get) if sizes else 0
        want = {'phone': 17, 'large': 15.5}[edition] * 0.75
        if abs(body - want) > 0.15:
            problems.append(f'body type is {body} pt, not {want} pt: something on a page is wider than the page and Chrome shrank the document')
    return problems


def build(slug: str, edition: str, out_dir: str, date: datetime.date, keep: bool) -> dict:
    src = open(os.path.join(PAGES, f'{slug}.md'), encoding='utf-8').read()
    fm = front_matter(src)
    work = tempfile.mkdtemp(prefix=f'story-pdf-{slug}-{edition}-')
    try:
        assets = {n: prepare(n, edition, work) for n in pictures(src)}
        json.dump(assets, open(os.path.join(work, 'assets.json'), 'w'))
        words = f'{date:%B} {date.day}, {date.year}'
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, f'{slug}-{edition}.pdf')
        tmp = os.path.join(work, 'print.pdf')
        pages = None
        for _ in range(4):
            doc = run_print_ts(slug, edition, work, words, pages)
            run_chrome(work, tmp)
            ids = [s['id'] for s in doc['sections']]
            found = section_pages(tmp, ids)
            if found == pages:
                break
            pages = found
        if doc['dead']:
            sys.exit(f'story_pdf: pages/{slug}.md has wording that tells the reader to work a screen, with no PDF wording for it.\n'
                     'Add a rule to SHARED in tools/pdf/wording.ts or to tools/stories/<story>/pdf.json (or an allow entry if it is not an instruction):\n  '
                     + '\n  '.join(doc['dead']))
        missing = [i for i in ids if not (pages or {}).get(i)]
        if missing:
            print(f'story_pdf: no page found for {missing}', file=sys.stderr)
        finish(tmp, doc, slug, edition, date.isoformat() + 'T12:00:00', fm.get('summary') or fm.get('deck') or doc['title'])
        shutil.move(tmp, out)
        result = check(out, edition)
        result['problems'] += placement_problems(out, edition, open(os.path.join(work, 'page.html'), encoding='utf-8').read(), assets)
        result['substitutions'] = doc['substitutions']
        result['file'] = out
        result['figures'] = doc['figures']
        result['compares'] = doc['compares']
        if keep:
            print(f'story_pdf: work kept in {work}', file=sys.stderr)
        return result
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('slug')
    ap.add_argument('--edition', choices=['phone', 'large', 'both'], default='both')
    ap.add_argument('--out', default=os.path.join(ROOT, 'out', 'pdf'))
    ap.add_argument('--date', help='the edition date, YYYY-MM-DD (default today)')
    ap.add_argument('--keep', action='store_true', help='keep the work folder (print HTML, prepared pictures)')
    a = ap.parse_args()
    if not os.path.exists(os.path.join(PAGES, f'{a.slug}.md')):
        sys.exit(f'story_pdf: no pages/{a.slug}.md')
    date = datetime.date.fromisoformat(a.date) if a.date else datetime.date.today()
    failed = False
    for ed in (['phone', 'large'] if a.edition == 'both' else [a.edition]):
        r = build(a.slug, ed, os.path.abspath(a.out), date, a.keep)
        for c in r['substitutions']:
            print(f"  wording: pages/{a.slug}.md, {c['where']}: \"{c['from']}\" -> \"{c['to']}\"")
        print(f"{r['file']}: {r['pages']} pages, {r['bytes'] / 1e6:.1f} MB, {r['figures']} figures ({r['compares']} compare), fonts {', '.join(r['fonts'])}")
        for p in r['problems']:
            print(f'  problem: {p}')
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
