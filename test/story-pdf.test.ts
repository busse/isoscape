import { test } from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { compilePage, PAGES_DIR } from '../src/pages.ts'
import { imageSize } from '../src/social.ts'
import { compileForPrint, piecesFor, printCss, printDoc, printRoute, shortTitle, stackTables, type Asset } from '../tools/pdf/print.ts'
import { deadInstructions, SHARED, substitute, type Change } from '../tools/pdf/wording.ts'

const STORIES = ['jackson-ward', 'redlining']

/** Every picture a page names, as story_pdf.py would prepare it (same names, the files' own sizes). */
const assetsFor = (slug: string): Record<string, Asset> => {
  const src = readFileSync(join(PAGES_DIR, `${slug}.md`), 'utf8')
  const names = new Set([...src.matchAll(/!\[[^\]]*\]\(([^)\s]+)\)/g)].map((m) => m[1]))
  const social = src.match(/^social:\s*(\S+)/m)?.[1]
  if (social) names.add(social)
  const out: Record<string, Asset> = {}
  for (const n of names) {
    const bytes = readFileSync(join(PAGES_DIR, n))
    if (n.endsWith('.svg')) {
      const vb = bytes.toString('utf8').match(/viewBox="[\d.]+ [\d.]+ ([\d.]+) ([\d.]+)"/)
      out[n] = { file: n, w: Number(vb?.[1] ?? 400), h: Number(vb?.[2] ?? 300), gaps: [0.3, 0.6, 0.9] }
    } else {
      const s = imageSize(bytes) ?? { width: 1200, height: 630 }
      out[n] = { file: n.replace(/\.\w+$/, '.jpg'), w: s.width, h: s.height }
    }
  }
  return out
}

test('the print build holds every section, figure and picture of each story', () => {
  for (const slug of STORIES) {
    const { page } = compileForPrint(slug)
    for (const ed of ['phone', 'large'] as const) {
      const doc = printDoc(slug, { edition: ed, assets: assetsFor(slug), date: 'November 22, 2026' })
      for (const h of page.headings) assert.ok(doc.html.includes(`id="${h.id}"`), `${slug} ${ed}: section ${h.id}`)
      for (const f of page.figures) assert.ok(doc.html.includes(`id="${f.id}"`), `${slug} ${ed}: ${f.id}`)
      // every picture's alt text, as written or with its slider wording for the PDF (wording.ts)
      for (const m of page.html.matchAll(/<img\b[^>]*?\balt="([^"]*)"/g)) {
        const reworded = substitute(m[1], SHARED, 'compare', 'alt', [], { a: '', b: '' })
        assert.ok(doc.html.includes(`alt="${m[1]}"`) || doc.html.includes(`alt="${reworded}"`), `${slug} ${ed}: picture "${m[1].slice(0, 40)}…"`)
      }
      assert.equal(doc.figures, page.figures.length)
      // every caption, the About note, the sources
      const plain = (h: string) => h.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ')
      const text = plain(doc.html)
      const reword = (h: string) => doc.substitutions.reduce((t, c) => t.split(c.from).join(c.to), h.replace(/\s+/g, ' '))
      for (const m of page.html.matchAll(/<figcaption>([\s\S]*?)<\/figcaption>/g)) assert.ok(text.includes(plain(reword(m[1])).slice(0, 200)), `${slug} ${ed}: a caption`)
      assert.match(doc.html, /About this page\./)
      assert.match(doc.html, /<h2 id="sources">Sources<\/h2>/)
      // the title page and the colophon
      assert.match(doc.html, /<p class="byline">Chris Busse<\/p>/)
      assert.ok(doc.html.includes(`https://isoscape.chrisbusse.com/p/${slug}.html`))
      assert.match(doc.html, /Made from the web page with isoscape's PDF tool, drafted with Claude\./)
      assert.doesNotMatch(doc.html, /pdf-links|hand-drawn|by hand|chrisbusse\.com|Buy a print|Shop prints/i)
      assert.doesNotMatch(doc.html, /—/, 'no em dashes')
      // no lightbox links, no explorer routes left
      assert.doesNotMatch(doc.html, /class="fig-open"|href="#\//)
    }
  }
})

test('a compare slider prints as its two pictures, each under its own label', () => {
  for (const slug of STORIES) {
    const { page } = compileForPrint(slug)
    const compares = page.figures.filter((f) => f.compare).length
    assert.ok(compares > 0)
    for (const ed of ['phone', 'large'] as const) {
      const doc = printDoc(slug, { edition: ed, assets: assetsFor(slug), date: 'x' })
      assert.doesNotMatch(doc.html, /class="cmp|role="slider"/)
      assert.equal((doc.html.match(/<div class="side">/g) ?? []).length, 2 * compares, `${slug} ${ed}`)
      for (const m of page.html.matchAll(/<div class="cmp" data-a="([^"]*)" data-b="([^"]*)"/g)) {
        for (const label of [m[1], m[2]]) assert.ok(doc.html.includes(`<p class="side-label">${label.charAt(0).toUpperCase() + label.slice(1)}</p>`), `${slug}: label ${label}`)
      }
    }
  }
})

test('links in a PDF stay inside for this page and go to the live site for the rest', () => {
  assert.equal(printRoute('#/redlining/sources', 'redlining'), '#sources')
  assert.equal(printRoute('#/about/contact', 'redlining'), 'https://isoscape.chrisbusse.com/p/about.html#contact')
  assert.equal(printRoute('#richmond-downtown-time:1925', 'redlining'), 'https://isoscape.chrisbusse.com/#richmond-downtown-time:1925')
  assert.equal(printRoute('https://example.org/', 'redlining'), 'https://example.org/')
  assert.equal(shortTitle('Redlining in Richmond, VA: the 1937 map'), 'Redlining in Richmond, VA')
  assert.equal(shortTitle('Jackson Ward, Richmond, VA, before I-95'), 'Jackson Ward')
})

test('tall pictures are cut at blank rows, and wide tables stack on the phone', () => {
  assert.deepEqual(piecesFor(1000, 2000), [[0, 1000]])
  const cut = piecesFor(1800, 700, [0.2, 0.35, 0.6, 0.9])
  assert.deepEqual(cut.map(([a, b]) => [Math.round(a), Math.round(b)]), [[0, 630], [630, 1080], [1080, 1620], [1620, 1800]])
  for (const [a, b] of cut) assert.ok(b - a <= 700)
  const t = '<div class="table"><table><thead><tr><th>#</th><th>Name</th><th>Sheet</th></tr></thead><tbody><tr><td>1</td><td>Bank</td><td>308</td></tr></tbody></table></div>'
  const s = stackTables(t)
  assert.match(s, /<li><p class="t">1 Bank<\/p><p class="v"><span class="k">Sheet:<\/span> 308<\/p><\/li>/)
  const two = '<div class="table"><table><thead><tr><th>A</th><th>B</th></tr></thead><tbody><tr><td>1</td><td>2</td></tr></tbody></table></div>'
  assert.equal(stackTables(two), two)
})

test('the pdf: setting shows the PDF line only when set', () => {
  const read = () => null
  const off = compilePage('---\ndeck: A deck.\n---\n# T\n\nBody.', 'story.md', read)
  assert.doesNotMatch(off.html, /pdf-links|\.pdf/)
  assert.equal(off.pdf, undefined)
  const on = compilePage('---\ndeck: A deck.\npdf: true\n---\n# T\n\nBody.', 'story.md', read)
  assert.equal(on.pdf, true)
  assert.equal((on.html.match(/<p class="pdf-links"/g) ?? []).length, 2, 'near the top and at the end')
  assert.match(on.html, /<p class="deck">A deck\.<\/p>\n<p class="pdf-links"/, 'under the deck')
  assert.match(on.html, /href="p\/story-phone\.pdf"[^>]*>phone edition<\/a>, <a href="p\/story-large\.pdf"[^>]*>large-screen edition<\/a>/)
  assert.match(on.html, /Read this as a PDF: /)
  const stat = compilePage('---\npdf: true\n---\n# T\n\nBody.', 'story.md', read, undefined, { idPrefix: '', imageHref: (n) => n, pdfHref: (n) => n })
  assert.match(stat.html, /<\/h1>\n<p class="pdf-links"[^>]*>Read this as a PDF: <a href="story-phone\.pdf"/)
  const print = compilePage('---\npdf: true\n---\n# T\n\nBody.', 'story.md', read, undefined, { pdfHref: null })
  assert.doesNotMatch(print.html, /pdf-links/)
  const no = compilePage('---\npdf: false\n---\n# T', 'story.md', read)
  assert.doesNotMatch(no.html, /pdf-links/)
})

test('the PDF says what a reader can do with paper, and the web page keeps its own words', () => {
  for (const slug of STORIES) {
    const { page } = compileForPrint(slug)
    for (const ed of ['phone', 'large'] as const) {
      const doc = printDoc(slug, { edition: ed, assets: assetsFor(slug), date: 'x' })
      assert.deepEqual(doc.dead, [], `${slug} ${ed}: instructions to a screen left in the PDF`)
      assert.ok(doc.substitutions.length > 0)
      assert.doesNotMatch(doc.html, /divider|arrow keys|Click any picture|All figures/i)
    }
    // the page itself is untouched
    assert.match(page.html, /left of the divider/)
  }
  const rl = printDoc('redlining', { edition: 'phone', assets: assetsFor('redlining'), date: 'x' })
  assert.ok(rl.html.includes('then (first picture) and today (second picture); the two pictures follow, 1937 first, then today.'))
  assert.ok(rl.html.includes('Content note: the next paragraph quotes a racial slur from the 1937 form.'))
  const jw = printDoc('jackson-ward', { edition: 'large', assets: assetsFor('jackson-ward'), date: 'x' })
  assert.ok(jw.html.includes('The same frame about 1925 (first picture) and in 1952 (second picture). The two pictures follow, about 1925 first, then 1952.'))
  // a rule's labels come from the slider; a sentence about the lightbox goes whole
  const changes: Change[] = []
  assert.equal(substitute('A (left of the divider), B (right). Drag the divider, or move it with the arrow keys.', SHARED, 'compare', 'cap', changes, { a: 'then', b: 'now' }),
    'A (first picture), B (second picture). The two pictures follow, then first, then now.')
  assert.equal(changes.length, 3)
  assert.equal(substitute('Maps. Click any picture to open it large; the arrow keys step. Next.', SHARED, 'all', 'text', []), 'Maps. Next.')
  // the check finds what no rule covers, and lets names and addresses pass
  assert.equal(deadInstructions('<p>Drag the map to pan. Tap a dot.</p>').length, 2)
  assert.deepEqual(deadInstructions('<p>The Richmond Free Press reported it (<a href="https://x.org/press-release">x.org/press-release</a>).</p>'), [])
  assert.deepEqual(deadInstructions('<p>We slide it here.</p>', ['slide']), [])
})

test('the print layout never cuts a picture or runs past the page', () => {
  for (const ed of ['phone', 'large'] as const) {
    const css = printCss(ed, 'Short', 'https://example.org/p/x.html')
    assert.doesNotMatch(css, /object-fit:\s*cover/, 'pictures are fitted whole')
    assert.doesNotMatch(css, /margin[^;{}]*:\s*[^;{}]*-\d/, 'no negative margins: Chrome clips at the page edge, or shrinks the document')
  }
})

// ---- the PDF itself (needs Chrome, poppler-utils and Python with pikepdf; skipped without them) --

const has = (cmd: string, args: string[]) => spawnSync(cmd, args, { encoding: 'utf8' }).status === 0
const chrome = ['google-chrome', 'chromium', 'chromium-browser'].find((c) => has(c, ['--version'])) ?? (process.env.CHROME && has(process.env.CHROME, ['--version']) ? process.env.CHROME : undefined)
const tools = chrome !== undefined && has('pdftotext', ['-v']) && has('pdfinfo', ['-v']) && has('python3', ['-c', 'import pikepdf, PIL, pdfplumber'])

test('the redlining PDF quotes the slur once, after its content note, and nowhere else', { skip: tools ? false : 'needs Chrome, poppler-utils, pikepdf and pdfplumber' }, () => {
  const word = ['dar', 'kies'].join('')
  const out = mkdtempSync(join(tmpdir(), 'story-pdf-test-'))
  try {
    const run = spawnSync('python3', ['tools/pdf/story_pdf.py', 'redlining', '--edition', 'phone', '--out', out, '--date', '2026-11-22'], { encoding: 'utf8', timeout: 300_000 })
    assert.equal(run.status, 0, run.stdout + run.stderr)
    const pdf = join(out, 'redlining-phone.pdf')
    assert.ok(!pdf.includes(word))
    // the text layer, page by page
    const text = spawnSync('pdftotext', ['-layout', pdf, '-'], { encoding: 'utf8', maxBuffer: 64 << 20 }).stdout
    const pages = text.split('\f')
    const flat = (s: string) => s.replace(/\s+/g, ' ')
    assert.equal(flat(text).split(word).length - 1, 1, 'quoted exactly once')
    const at = pages.findIndex((p) => p.includes(word))
    const note = pages.findIndex((p) => flat(p).includes('Content note: the next paragraph quotes a racial slur'))
    assert.ok(note >= 0 && (note === at || note === at - 1), `note on page ${note + 1}, quotation on ${at + 1}`)
    const between = flat(pages.slice(note, at + 1).join(' '))
    const span = between.slice(between.indexOf('Content note'), between.indexOf(word))
    assert.doesNotMatch(span, /Fig\. \d+\./, 'no figure between the note and the quotation')
    assert.ok(span.length < 1200, 'the note leads straight into the paragraph')
    // metadata, outline, contents list and alternate text
    const info = spawnSync('pdfinfo', [pdf], { encoding: 'utf8' }).stdout + spawnSync('pdfinfo', ['-meta', pdf], { encoding: 'utf8' }).stdout
    assert.ok(!info.includes(word), 'not in the metadata')
    assert.match(info, /Author:\s+Chris Busse/)
    assert.match(info, /Tagged:\s+yes/)
    const inside = spawnSync('python3', ['-c', `
import pikepdf, sys
p = pikepdf.open(sys.argv[1])
out = []
with p.open_outline() as o:
    def walk(items):
        for i in items:
            out.append(str(i.title)); walk(i.children)
    walk(o.root)
def tags(e):
    if isinstance(e, pikepdf.Array):
        for x in e: tags(x)
    elif isinstance(e, pikepdf.Dictionary) and '/S' in e:
        for k in ('/Alt', '/ActualText', '/T'):
            if k in e: out.append(str(e[k]))
        if '/K' in e: tags(e.K)
tags(p.Root.StructTreeRoot.get('/K'))
for k, v in p.docinfo.items(): out.append(str(v))
print('\\n'.join(out))
`, pdf], { encoding: 'utf8', maxBuffer: 64 << 20 })
    assert.equal(inside.status, 0, inside.stderr)
    assert.ok(!inside.stdout.includes(word), 'not in the outline, alternate text or document info')
    assert.match(inside.stdout, /Sources/)
    const contents = flat(pages.slice(1, 4).join(' '))
    assert.match(contents, /Contents/)
    assert.ok(!contents.includes(word), 'not in the contents list')
  } finally {
    rmSync(out, { recursive: true, force: true })
  }
})
