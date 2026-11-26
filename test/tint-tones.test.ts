import { test } from 'node:test'
import assert from 'node:assert/strict'
import { palette } from '../src/palette.ts'
import { OUTLINE, rainTones, tintPalette } from '../src/tint-tones.ts'

const lum = (c: string): number => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16)).reduce((a, b) => a + b, 0)

test('a tint without tones gets the very palette it was given', () => {
  const p = palette('paper')
  assert.equal(tintPalette(p, undefined), p)
  assert.equal(tintPalette(p, { values: ['A', 'B'] }), p)
})

test('rain tones run light to deep, one per value, and an outline takes the mark line', () => {
  const p = palette('paper')
  const t = rainTones(p, 7)
  assert.equal(t.length, 7)
  for (let k = 1; k < t.length; k++) assert.ok(lum(t[k]) < lum(t[k - 1]), `tone ${k} is darker than tone ${k - 1}`)
  const q = tintPalette(p, { tones: 'rain', values: ['0-2 in', '2-4 in', '4+ in', OUTLINE] })
  assert.equal(q.tint.tones.length, 4)
  assert.equal(q.tint.tones[3], p.mark.line)
  assert.deepEqual(q.tint.tones.slice(0, 3), rainTones(p, 3))
  assert.equal(q.tint.road, p.tint.road)
  assert.equal(p.tint.tones.length, 4) // the palette itself is left alone
})
