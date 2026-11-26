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
  // A compare figure holds two pictures, one figure.
  const imgs = [...page.html.matchAll(/<img (?!class="cmp-b")/g)].length
  assert.equal(page.figures.length, imgs, 'no picture outside a figure')
  const sliders = page.figures.filter((f) => f.compare)
  assert.ok(sliders.length >= 1 && sliders.length <= 4, 'one to four compare sliders')
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

test('each compare slider lays two pictures of one size over each other, and only the pages that ask for one have one', () => {
  const withCompare = ['jackson-ward', 'explore-with-chat', 'redlining', 'history-from-old-maps', 'richmond-floods']
  for (const slug of withCompare) {
    const page = loadPages().find((p) => p.slug === slug)
    assert.ok(page, slug)
    const cmps = [...page.html.matchAll(/<div class="cmp" [\s\S]*?<\/div>\n<div class="cmp-div"/g)].map((m) => m[0])
    assert.ok(cmps.length > 0, slug)
    assert.equal(cmps.length, page.figures.filter((f) => f.compare).length)
    for (const c of cmps) {
      const sizes = [...c.matchAll(/<img class="cmp-[ab]" [^>]*width="(\d+)" height="(\d+)"/g)].map((m) => m[1] + 'x' + m[2])
      assert.equal(sizes.length, 2, 'two pictures with their sizes')
      assert.equal(sizes[0], sizes[1], 'the same size, so they line up')
    }
  }
  // Every other page keeps plain figures (or none).
  for (const p of loadPages()) if (!withCompare.includes(p.slug)) assert.ok(!p.figures.some((f) => f.compare), p.slug)
})
