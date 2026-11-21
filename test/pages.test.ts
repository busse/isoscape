import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { compilePage, frontMatter, loadPages, pageLink } from '../src/pages.ts'
import { renderExplorer } from '../src/explorer.ts'

test('front matter is read and stripped', () => {
  const { data, body } = frontMatter('---\ntitle: "How it\'s made"\norder: 10\n---\n# Hi\n')
  assert.deepEqual(data, { title: "How it's made", order: '10' })
  assert.equal(body, '# Hi\n')
  assert.deepEqual(frontMatter('# No front matter').data, {})
})

test('links written for GitHub become explorer routes', () => {
  assert.equal(pageLink('how', '#rapids'), '#/how/rapids')
  assert.equal(pageLink('how', 'about.md'), '#/about')
  assert.equal(pageLink('how', './about.md#data'), '#/about/data')
  assert.equal(pageLink('how', '#/other/x'), '#/other/x')
  assert.equal(pageLink('how', 'https://example.org/a.md'), 'https://example.org/a.md')
})

test('a page compiles with defaults, prefixed ids and inlined images', () => {
  const p = compilePage('# Title here\n\n## Part one\n\nSee [two](#part-two).\n\n## Part two\n\n![d](d.svg) ![e](../secret.svg)', 'thing.md', (name) =>
    name === 'd.svg' ? Buffer.from('<svg/>') : null)
  assert.equal(p.slug, 'thing')
  assert.equal(p.title, 'Title here')
  assert.equal(p.order, 100)
  assert.equal(p.file, 'pages/thing.md')
  assert.match(p.html, /<h2 id="p-thing-part-one">/)
  assert.match(p.html, /href="#\/thing\/part-two"/)
  assert.match(p.html, /src="data:image\/svg\+xml;base64,PHN2Zy8\+"/)
  assert.doesNotMatch(p.html, /secret/)
})

test('a bad slug is refused', () => {
  assert.throws(() => compilePage('---\nslug: Bad Slug\n---\nx', 'x.md'), /slug/)
})

test('pages load from a folder in order, skipping drafts and READMEs', () => {
  const dir = mkdtempSync(join(tmpdir(), 'isoscape-pages-'))
  writeFileSync(join(dir, 'b.md'), '---\ntitle: B\norder: 20\n---\nb')
  writeFileSync(join(dir, 'a.md'), '---\ntitle: A\norder: 30\n---\na')
  writeFileSync(join(dir, 'c.md'), '---\ntitle: C\norder: 5\n---\nc')
  writeFileSync(join(dir, '_draft.md'), 'draft')
  writeFileSync(join(dir, 'README.md'), 'about this folder')
  assert.deepEqual(loadPages(dir).map((p) => p.slug), ['c', 'b', 'a'])
  assert.deepEqual(loadPages(join(dir, 'missing')), [])
})

test('the shipped pages load, and carry the sections the explorer links to', () => {
  const pages = loadPages()
  const how = pages.find((p) => p.slug === 'how-its-made')
  assert.ok(how, 'pages/how-its-made.md')
  assert.ok(pages.find((p) => p.slug === 'about'), 'pages/about.md')
  const ids = new Set(how.headings.map((h) => h.id))
  // Every "#/how-its-made/<id>" the per-build story links to must exist.
  for (const id of ['camera', 'inputs', 'ground', 'drawing', 'rapids', 'rivers', 'buildings', 'bridges', 'paint-order', 'archive-and-explorer']) {
    assert.ok(ids.has(id), `how-its-made has a "${id}" section`)
  }
  // And every in-page link on the shipped pages lands on a real section.
  const all = new Map(pages.map((p) => [p.slug, new Set([...p.headings.map((h) => h.id), ...p.figures.map((f) => f.id)])]))
  for (const p of pages) {
    for (const [, slug, section] of p.html.matchAll(/href="#\/([a-z0-9-]+)(?:\/([^"]+))?"/g)) {
      assert.ok(all.has(slug), `${p.file} links to a page "${slug}"`)
      if (section) assert.ok(all.get(slug)!.has(section), `${p.file} links to ${slug}#${section}`)
    }
  }
})

test('the explorer embeds the pages, safely', () => {
  const html = renderExplorer([], [compilePage('# T\n\n</script><b>x</b>', 't.md')])
  const embedded = html.match(/<script type="application\/json" id="pagesData">([\s\S]*?)<\/script>/)
  assert.ok(embedded)
  const pages = JSON.parse(embedded[1]) as { slug: string; html: string }[]
  assert.equal(pages[0].slug, 't')
  assert.match(pages[0].html, /&lt;\/script&gt;&lt;b&gt;x&lt;\/b&gt;/)
  // The explorer's own script must still parse.
  const script = html.match(/<script>\n([\s\S]*?)<\/script>/)
  assert.ok(script)
  assert.doesNotThrow(() => new Function(script[1]))
})

test('a link to a map on the public site stays inside the explorer', async () => {
  const { pageLink } = await import('../src/pages.ts')
  assert.equal(pageLink('world-landmarks', 'https://busse.github.io/isoscape/#lm-eiffel-tower', 'https://busse.github.io/isoscape/'), '#lm-eiffel-tower')
  assert.equal(pageLink('world-landmarks', 'https://example.com/#x', 'https://busse.github.io/isoscape/'), 'https://example.com/#x')
})

test('a page can name its own link-preview image, and the share page uses it', async () => {
  const { compilePage } = await import('../src/pages.ts')
  const { writeSocial, imageSize } = await import('../src/social.ts')
  const { readFileSync, mkdtempSync: mk } = await import('node:fs')
  // A 2×1 baseline JPEG header is enough for the size reader: SOI, then SOF0 with height 1, width 2.
  const jpeg = Buffer.from([0xff, 0xd8, 0xff, 0xc0, 0x00, 0x11, 0x08, 0x00, 0x01, 0x00, 0x02, 0x03, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xff, 0xd9])
  assert.deepEqual(imageSize(jpeg), { width: 2, height: 1 })
  const page = compilePage('---\ntitle: World\nsummary: Five places.\nsocial: card.jpg\n---\n\n# World\n', 'world.md', (n) => (n === 'card.jpg' ? jpeg : null))
  assert.equal(page.social?.name, 'card.jpg')
  assert.throws(() => compilePage('---\nsocial: nope.jpg\n---\n# X\n', 'x.md', () => null))
  const out = mk(join(tmpdir(), 'iso-social-'))
  await writeSocial(out, [], [page], { siteUrl: 'https://example.org/iso/' })
  const html = readFileSync(join(out, 's', 'page-world.html'), 'utf8')
  assert.match(html, /og:image" content="https:\/\/example.org\/iso\/s\/page-world.jpg"/)
  assert.match(html, /og:image:width" content="2"/)
  assert.deepEqual(readFileSync(join(out, 's', 'page-world.jpg')), jpeg)
})

test('a page\'s raster images carry their size, a figure links its larger copy, and a deck sits under the title', async () => {
  const { imageSize } = await import('../src/social.ts')
  // A minimal lossy WebP header (VP8): 320 × 136.
  const webp = Buffer.alloc(30)
  webp.write('RIFF', 0, 'ascii'); webp.write('WEBP', 8, 'ascii'); webp.write('VP8 ', 12, 'ascii')
  webp.writeUInt16LE(320, 26); webp.writeUInt16LE(136, 28)
  assert.deepEqual(imageSize(webp), { width: 320, height: 136 })
  const files: Record<string, Buffer> = { 'a.webp': webp, 'a-large.webp': webp, 'b.webp': webp }
  const src = '---\ndeck: What you will see, [and how](#how).\n---\n# T\n\n::: figure\n![A](a.webp)\n:::\n\n::: figure\n![B](b.webp)\n:::\n\n![C](b.webp)\n\n## How\n'
  const p = compilePage(src, 'f.md', (n) => files[n] ?? null)
  assert.equal(p.deck, 'What you will see, [and how](#how).')
  assert.match(p.html, /<h1 id="p-f-t">T<\/h1>\n<p class="deck">What you will see, <a href="#\/f\/how">and how<\/a>\.<\/p>/)
  assert.match(p.html, /<a class="fig-open" href="p\/a-large\.webp"[^>]*><img src="data:image\/webp;base64,[^"]+" alt="A" width="320" height="136"/)
  assert.match(p.html, /<a class="fig-open" href="p\/b\.webp"/)
  assert.match(p.html, /<p><img src="data:image\/webp;base64,[^"]+" alt="C" width="320" height="136" loading="lazy"><\/p>/)
  assert.deepEqual(p.figures.map((f) => f.id), ['fig-1', 'fig-2'])
})
