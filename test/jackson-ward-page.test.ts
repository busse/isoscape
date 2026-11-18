import { test } from 'node:test'
import assert from 'node:assert/strict'
import { loadPages } from '../src/pages.ts'
import { loadStaticPages } from '../src/static-pages.ts'

// The Jackson Ward story page (pages/jackson-ward.md, written by tools/stories/jackson-ward/page.py).

test('every link within the Jackson Ward page lands on an id, in the explorer and on the static page', () => {
  const page = loadPages().find((p) => p.slug === 'jackson-ward')
  assert.ok(page, 'pages/jackson-ward.md')
  const ids = new Set([...page.html.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]))
  const own = [...page.html.matchAll(/href="#\/jackson-ward\/([^"]+)"/g)].map((m) => m[1])
  assert.ok(own.length > 50, 'the page links within itself (sections and sources)')
  const missing = own.filter((id) => !ids.has('p-jackson-ward-' + id))
  assert.deepEqual([...new Set(missing)], [], 'explorer: links with no target')
  const { pages } = loadStaticPages(loadPages().map((p) => p.slug))
  const st = pages.find((p) => p.slug === 'jackson-ward')
  assert.ok(st)
  const sids = new Set([...st.html.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]))
  const shash = [...st.html.matchAll(/href="#([^"/][^"]*)"/g)].map((m) => m[1])
  assert.equal(shash.length, own.length, 'the static page has the same in-page links')
  assert.deepEqual([...new Set(shash.filter((id) => !sids.has(id)))], [], 'static page: links with no target')
})

test('every picture on the Jackson Ward page is a numbered figure with a caption', () => {
  const page = loadPages().find((p) => p.slug === 'jackson-ward')
  assert.ok(page)
  const imgs = [...page.html.matchAll(/<img /g)].length
  assert.equal(page.figures.length, imgs, 'no picture outside a figure')
  assert.ok(page.figures.length >= 20)
  page.figures.forEach((f, i) => assert.equal(f.n, i + 1))
  for (const m of page.html.matchAll(/<figcaption><p><span class="fig-n">Fig\. (\d+)\.<\/span>([^<]*)/g)) assert.ok(m[2].trim().length > 10, `Fig. ${m[1]} has a caption`)
  // The two Second Street keys stay inside their figures.
  for (const n of ['Corby Baking Company', 'Furniture storage warehouse']) {
    const at = page.html.indexOf(n)
    assert.ok(at > 0 && page.html.lastIndexOf('<figure', at) > page.html.lastIndexOf('</figure>', at), `the key holding "${n}" is inside its figure`)
  }
  assert.ok(page.deck && page.deck.length > 40, 'the page has a deck')
})
