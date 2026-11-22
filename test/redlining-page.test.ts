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
