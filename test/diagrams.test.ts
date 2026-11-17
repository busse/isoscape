import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { PALETTES } from '../src/palette.ts'
import { DIAGRAMS, SIZE, social } from '../tools/diagrams/faq.ts'

const PAGES = new URL('../pages/', import.meta.url)

/** Every hex color anywhere in a palette. */
const paletteHex = (): Set<string> => {
  const out = new Set<string>()
  const walk = (v: unknown): void => {
    if (typeof v === 'string' && /^#[0-9a-f]{6}$/i.test(v)) out.add(v.toLowerCase())
    else if (v && typeof v === 'object') for (const x of Object.values(v)) walk(x)
  }
  walk(PALETTES)
  return out
}

test('the diagrams in pages/ are what tools/diagrams/faq.ts writes', () => {
  for (const [name, make] of Object.entries(DIAGRAMS)) {
    assert.equal(readFileSync(new URL(name, PAGES), 'utf8'), make(), `pages/${name} is stale: run node tools/diagrams/faq.ts`)
  }
})

test('the diagrams use only palette colors, keep text as text, and say what they show', () => {
  const allowed = paletteHex()
  for (const [name, make] of [...Object.entries(DIAGRAMS), ['social', social] as const]) {
    const svg = make()
    for (const [hex] of svg.matchAll(/#[0-9a-f]{6}\b/gi)) assert.ok(allowed.has(hex.toLowerCase()), `${name}: ${hex} is not a palette color`)
    assert.match(svg, /<title id="[^"]+">[^<]+<\/title>\n<desc id="[^"]+">[^<]{80,}<\/desc>/, `${name}: title and desc`)
    assert.match(svg, /role="img" aria-labelledby=/)
    assert.match(svg, /@media \(prefers-color-scheme: dark\)/, `${name}: a dark theme`)
    assert.ok((svg.match(/<text /g) ?? []).length > 5, `${name}: its words are text`)
    assert.doesNotMatch(svg, /by hand|hand-drawn/i)
  }
  // Big enough to read on a phone: no type under 12 units in a drawing 400 wide.
  for (const v of Object.values(SIZE)) assert.ok(v >= 12)
})
