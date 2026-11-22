import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { PALETTES } from '../src/palette.ts'
import { timeline, MOMENTS } from '../tools/stories/redlining/timeline.ts'

test('the redlining timeline in pages/ is what its script writes', () => {
  assert.equal(readFileSync(new URL('../pages/redlining-timeline.svg', import.meta.url), 'utf8'), timeline(), 'pages/redlining-timeline.svg is stale: run node tools/stories/redlining/timeline.ts')
})

test('the redlining timeline uses only palette colors and gives every date a source', () => {
  const allowed = new Set<string>()
  const walk = (v: unknown): void => {
    if (typeof v === 'string' && /^#[0-9a-f]{6}$/i.test(v)) allowed.add(v.toLowerCase())
    else if (v && typeof v === 'object') for (const x of Object.values(v)) walk(x)
  }
  walk(PALETTES)
  for (const [hex] of timeline().matchAll(/#[0-9a-f]{6}\b/gi)) assert.ok(allowed.has(hex.toLowerCase()), `${hex} is not a palette color`)
  for (const m of MOMENTS) assert.ok(m.source.length > 0, `${m.date} has no source`)
})

// The owner chose to quote the D11.5 form's slur once, attributed, in the text. It must appear
// nowhere else: not twice on the page, not in alt text, captions or file names.
test('the D11.5 form is quoted once on the redlining page and nowhere else', () => {
  const word = ['dar', 'kies'].join('')
  const page = readFileSync(new URL('../pages/redlining.md', import.meta.url), 'utf8')
  assert.equal(page.split(word).length - 1, 1, 'the quotation appears exactly once on the page')
  for (const line of page.split('\n')) if (line.includes(word)) assert.ok(!line.startsWith('!['), 'not in alt text')
  for (const f of readdirSync(new URL('../pages/', import.meta.url))) assert.ok(!f.includes(word), `not in a file name: ${f}`)
})

// Every percentage on the page is rounded once, half up, from the unrounded share in numbers.json
// (tools/stories/redlining/fmt.py). d3 rounded twice and printed 64% for 64.53%.
test('the redlining page rounds each percentage once from numbers.json', () => {
  const page = readFileSync(new URL('../pages/redlining.md', import.meta.url), 'utf8').replace(/\s+/g, ' ')
  const n = JSON.parse(readFileSync(new URL('../tools/stories/redlining/numbers.json', import.meta.url), 'utf8'))
  const pct = (x: number): number => Math.floor(x * 100 + 0.5)
  const m = n.motorway.by_grade_share
  assert.notEqual(Math.round(m.D * 1000) / 1000, m.D, 'numbers.json keeps shares unrounded')
  const t = n.terrain_by_grade
  const want = [
    `${pct(m.D)}% lies in D areas, which were ${pct(n.graded_land.D.share)}% of the graded land; ${pct(m.C)}% lies in C`,
    `the limited-access highway inside graded land is A ${pct(m.A)}%, B ${pct(m.B)}%, C ${pct(m.C)}%, D ${pct(m.D)}%`,
    `graded land is A ${pct(n.graded_land.A.share)}%, B ${pct(n.graded_land.B.share)}%, C ${pct(n.graded_land.C.share)}%, D ${pct(n.graded_land.D.share)}%`,
    `about ${pct(t.D.share_steeper_10deg)}% of D, ${pct(t.C.share_steeper_10deg)}% of C and ${pct(t.B.share_steeper_10deg)}% of B is steeper`,
    `${pct(n.areas.D4.share_by1937)}% were built by 1937 and ${pct(n.areas.D4.share_y1938_1977)}% between 1938 and 1977`,
    `with ramps, D holds ${pct(n.motorway_and_links.by_grade_share.D)}%`,
  ]
  for (const w of want) assert.ok(page.includes(w), `the page should read: ${w}`)
  for (const [k, a] of Object.entries(n.areas) as [string, { share_by1937: number | null }][]) {
    if (a.share_by1937 === null) continue
    const double = Math.round(Math.round(a.share_by1937 * 1000) / 10)
    if (double !== pct(a.share_by1937)) assert.ok(!page.includes(`${double}% were built by 1937`), `${k} rounded twice`)
  }
})

// d5: the highway's base rates (measure.py `base_rate`) are printed from numbers.json, densities
// to two places and shares rounded once, as the page and its charts say.
test('the redlining page prints the highway base rates from numbers.json', () => {
  const page = readFileSync(new URL('../pages/redlining.md', import.meta.url), 'utf8').replace(/\s+/g, ' ')
  const n = JSON.parse(readFileSync(new URL('../tools/stories/redlining/numbers.json', import.meta.url), 'utf8'))
  const pct = (x: number): number => Math.floor(x * 100 + 0.5)
  const b = n.motorway_base_rate
  const d = (k: string) => b.density[k].km_per_km2.toFixed(2)
  const near = (k: string) => b.density_near[k].km_per_km2.toFixed(2)
  assert.notEqual(Math.round(b.location_alone.expected_share.D * 1000) / 1000, b.location_alone.expected_share.D, 'numbers.json keeps shares unrounded')
  const want = [
    `location alone would give it about ${pct(b.location_alone.expected_share.D)}%`,
    `D land carries ${d('D')} km of this highway, against ${d('ungraded')} km on the ungraded land`,
    `and ${d('C')} km on C`,
    `D land carries ${near('D')} km per square kilometer, against ${near('ungraded')} km on the ungraded land and ${near('C')} km on C`,
    `Half of the D land lies within ${b.median_distance_km.D.toFixed(1)} km of the State Capitol`,
    `moves D's share of the highway between ${pct(b.shift_D_share['24'].min)}% and ${pct(b.shift_D_share['24'].max)}%`,
  ]
  for (const w of want) assert.ok(page.includes(w), `the page should read: ${w}`)
})

// d5: every in-page link names a heading on the page (citations land on their Sources entry).
test('every in-page link on the redlining page names a heading on it', async () => {
  const { compilePage } = await import('../src/pages.ts')
  const src = readFileSync(new URL('../pages/redlining.md', import.meta.url), 'utf8')
  const dir = new URL('../pages/', import.meta.url)
  const p = compilePage(src, 'redlining.md', (name) => { try { return readFileSync(new URL(name, dir)) } catch { return null } }, undefined, { idPrefix: '' })
  const ids = new Set([...p.html.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]))
  const links = [...src.matchAll(/\]\(#([a-z0-9-]+)\)/g)].map((m) => m[1])
  assert.ok(links.length > 100)
  for (const l of links) assert.ok(ids.has(l), `#${l} names no heading`)
})

// d5: a wrapped line that starts with a year and a period ("1937. The HOLC…") would become a
// numbered list item; the page has no numbered lists.
test('no line of the redlining page starts like a numbered list item', () => {
  const page = readFileSync(new URL('../pages/redlining.md', import.meta.url), 'utf8')
  for (const line of page.split('\n')) assert.doesNotMatch(line, /^\s*\d+\. /, line)
})
