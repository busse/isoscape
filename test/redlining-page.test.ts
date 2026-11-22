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
