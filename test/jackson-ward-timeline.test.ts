import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { PALETTES } from '../src/palette.ts'
import { timeline, MOMENTS } from '../tools/stories/jackson-ward/timeline.ts'

test('the Jackson Ward timeline in pages/ is what its script writes', () => {
  assert.equal(readFileSync(new URL('../pages/jackson-ward-timeline.svg', import.meta.url), 'utf8'), timeline(), 'pages/jackson-ward-timeline.svg is stale: run node tools/stories/jackson-ward/timeline.ts')
})

test('the Jackson Ward timeline uses only palette colors and gives every date a source', () => {
  const allowed = new Set<string>()
  const walk = (v: unknown): void => {
    if (typeof v === 'string' && /^#[0-9a-f]{6}$/i.test(v)) allowed.add(v.toLowerCase())
    else if (v && typeof v === 'object') for (const x of Object.values(v)) walk(x)
  }
  walk(PALETTES)
  for (const [hex] of timeline().matchAll(/#[0-9a-f]{6}\b/gi)) assert.ok(allowed.has(hex.toLowerCase()), `${hex} is not a palette color`)
  for (const m of MOMENTS) assert.ok(m.source.length > 0, `${m.date} has no source`)
})
