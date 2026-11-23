import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import type { BuildMeta } from '../src/archive.ts'
import { renderExplorer } from '../src/explorer.ts'
import { compilePage, loadPages } from '../src/pages.ts'
import { seriesShopLine } from '../src/social.ts'
import { planStatic, renderContentPage } from '../src/static-pages.ts'
import { seriesView, ttFrame, ttNearest, ttPair, ttParse, ttPick, ttPos, ttRoute, ttStep, ttTicks } from '../src/through-time.ts'

const YEARS = [1737, 1788, 1800, 1860, 1865, 1870, 1886, 2026]

test('a series page route names one year or two, earlier first; anything else is not a state', () => {
  assert.deepEqual(ttParse('1865', YEARS), { a: 1865, b: null })
  assert.deepEqual(ttParse('1865..1870', YEARS), { a: 1865, b: 1870 })
  // A pair written later first is put earlier first: the earlier year is always on the left.
  assert.deepEqual(ttParse('2026..1737', YEARS), { a: 1737, b: 2026 })
  assert.deepEqual(ttParse('1865..1865', YEARS), { a: 1865, b: null })
  // Years the series does not have, headings and junk are not states (a heading id still opens its section).
  assert.equal(ttParse('1866', YEARS), null)
  assert.equal(ttParse('1865..1999', YEARS), null)
  assert.equal(ttParse('how-it-was-made', YEARS), null)
  assert.equal(ttParse('', YEARS), null)
  assert.equal(ttParse(undefined, YEARS), null)
  assert.equal(ttRoute('downtown', { a: 1865, b: null }), '#/downtown/1865')
  assert.equal(ttRoute('downtown', { a: 1865, b: 1870 }), '#/downtown/1865..1870')
})

test('stepping, the default pair and the pickers keep the earlier year on the left', () => {
  assert.equal(ttStep(YEARS, 1865, -1), 1860)
  assert.equal(ttStep(YEARS, 1865, 1), 1870)
  assert.equal(ttStep(YEARS, 1737, -1), null)
  assert.equal(ttStep(YEARS, 2026, 1), null)
  // Turning comparing on: the year shown against today, or on today, the year before against it.
  assert.deepEqual(ttPair(YEARS, 1865), { a: 1865, b: 2026 })
  assert.deepEqual(ttPair(YEARS, 2026), { a: 1886, b: 2026 })
  assert.deepEqual(ttPair([1900], 1900), { a: 1900, b: null })
  const s = { a: 1865, b: 1870 }
  assert.deepEqual(ttPick(YEARS, s, 'a', 1800), { a: 1800, b: 1870 })
  assert.deepEqual(ttPick(YEARS, s, 'b', 2026), { a: 1865, b: 2026 })
  // A pick that would cross the other side moves the other side, never the order.
  assert.deepEqual(ttPick(YEARS, s, 'a', 1886), { a: 1886, b: 2026 })
  assert.deepEqual(ttPick(YEARS, s, 'a', 2026), { a: 1886, b: 2026 })
  assert.deepEqual(ttPick(YEARS, s, 'b', 1860), { a: 1800, b: 1860 })
  assert.deepEqual(ttPick(YEARS, s, 'b', 1737), { a: 1737, b: 1788 })
  assert.deepEqual(ttPick(YEARS, s, 'b', 1999), s)
})

test('the timeline spaces years by the time between them, and every picture is placed in one shared frame', () => {
  const pos = ttPos(YEARS)
  assert.equal(pos[0], 0.02)
  assert.equal(pos[pos.length - 1], 0.98)
  // 1737 to 1788 is a long stretch, 1860 to 1865 a short one.
  assert.ok(pos[1] - pos[0] > 5 * (pos[4] - pos[3]))
  assert.equal(ttNearest(YEARS, pos, 0), 1737)
  assert.equal(ttNearest(YEARS, pos, 1), 2026)
  assert.equal(ttNearest(YEARS, pos, pos[4] + 0.001), 1865)
  assert.deepEqual(ttTicks(YEARS, 30), [1737, 1800, 1850, 1900, 1950, 2026])
  assert.deepEqual(ttTicks([1990, 2026], 30), [1990, 2026])
  // Two years' drawings of one frame that differ a little in height (as builds of the Richmond series do).
  assert.deepEqual(ttFrame([[-3024, -1587, 6048, 2642], [-3024, -1675.5, 6048, 2730.5]]), [-3024, -1675.5, 6048, 2730.5])
})

test('the view\'s functions stand alone, as the explorer embeds their source', () => {
  // The explorer writes each function's source into its page (toString), so none may reach for
  // another in this module (ttPick once called ttStep and threw in the browser) or hold a
  // template literal, which would end the explorer's own.
  for (const fn of [ttParse, ttRoute, ttStep, ttPair, ttPick, ttFrame, ttPos, ttNearest, ttTicks, seriesView]) {
    const src = fn.toString()
    assert.doesNotMatch(src, /`/, fn.name)
    assert.doesNotMatch(src, /\btt[A-Z]\w*\(/, `${fn.name} calls another helper by name`)
  }
  const pick = new Function(`return (${ttPick.toString()})`)()
  assert.deepEqual(pick(YEARS, { a: 1865, b: 1870 }, 'b', 1860), { a: 1800, b: 1860 })
  const pair = new Function(`return (${ttPair.toString()})`)()
  assert.deepEqual(pair(YEARS, 2026), { a: 1886, b: 2026 })
})

const build = (id: string, year: number, createdAt = '2026-03-01T00:00:00Z'): BuildMeta => ({
  id, name: `town-time-${year}`, region: 'town-time', title: `Town, ${year}`, palette: 'paper', createdAt, viewBox: [0, 0, 2000, 1000], bearing: 0, ms: 1, bytes: 1,
  stats: {}, config: { name: 'town-time', title: 'Town', center: [0, 0], width: 1, depth: 1, bearing: 0, scale: 1 },
  files: { svg: `builds/${id}/image.svg`, preview: `builds/${id}/preview.jpg` }, sky: '#fff',
  time: { year, series: 'town-time', title: `Era ${year}`, note: `What ${year} was.`, curated: [] },
} as unknown as BuildMeta)

const PAGE = compilePage(`---
title: The town through time
series: town-time
---

# The town through time

Pick a year.

## What changes

- [1888 and 1925](#/town/1888..1925). A change.
- [Read more](#more)

## More

Text.
`, 'town.md')

test('a page with series: names its series, and only a region name', () => {
  assert.equal(PAGE.series, 'town-time')
  assert.throws(() => compilePage('---\nseries: Town Time!\n---\n# x\n', 'x.md'), /series "Town Time!" must be a region name/)
  assert.equal(compilePage('# x\n', 'x.md').series, undefined)
})

test('the explorer carries the series page and its view; its script parses', () => {
  const html = renderExplorer([build('a', 1888), build('b', 1925)], [PAGE], { shop: { label: 'The shop', url: 'https://shop.example/', onSale: { 'town-time:1925': 'https://shop.example/p/1925' } } })
  const script = html.match(/<script>\n([\s\S]*?)<\/script>/)
  assert.ok(script)
  assert.doesNotThrow(() => new Function(script[1]))
  const data = JSON.parse(html.match(/<script type="application\/json" id="pagesData">([\s\S]*?)<\/script>/)?.[1] ?? '[]')
  assert.equal(data[0].series, 'town-time')
  // The quiet shop line goes to the shop's own front page.
  assert.match(data[0].shopLine, /<p class="tt-shop">Some of these years are sold as prints: <a href="https:\/\/shop\.example\/"[^>]*>The shop ↗<\/a><\/p>/)
  assert.match(html, /#page\.tt-wide \.doc \{/)
  // A series build in the viewer links to its page.
  assert.match(script[1], /Compare years on the series page →/)
})

test('without script, the series page lists its years as links and its year links open the explorer', () => {
  const builds = [build('a', 1888), build('b', 1925)]
  const plan = planStatic(builds, [PAGE.slug])
  // As the static pages compile it: a link to a state of its own view is left as '#<state>'.
  const statics = compilePage(readFileSync(new URL('../pages/downtown-through-time.md', import.meta.url), 'utf8'), 'x.md')
  assert.ok(statics.series)
  const own = { ...PAGE, html: PAGE.html.replace('href="#/town/1888..1925"', 'href="#1888..1925"') }
  const html = renderContentPage(own, { config: { shop: { label: 'The shop', url: 'https://shop.example/', onSale: { 'town-time:1925': 'u' } } }, plan, pages: [own], depth: 1 })
  assert.match(html, /<h2 id="the-years">The 2 years<\/h2>/)
  assert.match(html, /<li><a href="\.\.\/m\/town-time-1888\.html">1888: Era 1888<\/a><\/li><li><a href="\.\.\/m\/town-time-1925\.html">1925: Era 1925<\/a><\/li>/)
  // The list stands before the first section, where the explorer puts the view.
  assert.ok(html.indexOf('id="the-years"') < html.indexOf('What changes'))
  assert.match(html, /href="\.\.\/index\.html#\/town\/1888\.\.1925"/)
  assert.match(html, /class="tt-shop"[^]*?href="https:\/\/shop\.example\/\?utm_source=isoscape-explorer&amp;utm_medium=referral&amp;utm_campaign=town"/)
})

test('the shop line shows only while a year of the series, or the series, is on sale', () => {
  assert.equal(seriesShopLine({}, 'town-time'), undefined)
  assert.equal(seriesShopLine({ shop: { label: 'S', url: 'https://s/', onSale: { 'lm-': 'x' } } }, 'town-time'), undefined)
  assert.ok(seriesShopLine({ shop: { label: 'S', url: 'https://s/', onSale: { 'town-time:1925': 'x' } } }, 'town-time'))
  assert.ok(seriesShopLine({ shop: { label: 'S', url: 'https://s/', onSale: { town: 'x' } } }, 'town-time'))
})

test('the Richmond page: a series page whose every jump names years of the series, each item citing a source', () => {
  const page = loadPages().find((p) => p.slug === 'downtown-through-time')
  assert.ok(page)
  assert.equal(page.series, 'richmond-downtown-time')
  const epochs = (JSON.parse(readFileSync(new URL('../history/richmond-downtown.json', import.meta.url), 'utf8')) as { epochs: { year: number }[] }).epochs.map((e) => e.year)
  const jumps = [...page.html.matchAll(/href="#\/downtown-through-time\/([0-9.]+)"/g)].map((m) => m[1])
  assert.ok(jumps.length >= 5)
  for (const j of jumps) assert.ok(ttParse(j, epochs), `${j} names years of the series`)
  // Every item but "then and now" cites at least one source.
  const items = page.html.split('<li>').slice(1).map((li) => li.split('</li>')[0])
  for (const li of items.filter((x) => x.includes('#/downtown-through-time/') && !x.includes('then and now'))) assert.match(li, /href="https:\/\//, li.slice(0, 80))
  // Drafted with Claude, said plainly; nothing done "by hand".
  assert.match(page.html, /drafted with Claude/)
  assert.doesNotMatch(page.html, /by hand|hand-drawn|—/)
})
