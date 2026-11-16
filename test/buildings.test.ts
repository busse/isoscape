import { test } from 'node:test'
import assert from 'node:assert/strict'
import { groundCover, settlePrisms, type Prism } from '../src/scene.ts'
import type { Vec2 } from '../src/geom.ts'

const square = (x: number, y: number, s = 10): Vec2[] => [[x, y], [x + s, y], [x + s, y + s], [x, y + s]]
const prism = (outer: Vec2[], base: number, top: number, extra: Partial<Prism> = {}): Prism =>
  ({ outer, base, top, foot: 0, raised: base > 0, span: false, ...extra })

test('parts that reach the ground replace an outline only when they cover it', () => {
  assert.equal(groundCover(square(0, 0, 20), [], [square(0, 0, 20)]), 1)
  assert.ok(Math.abs(groundCover(square(0, 0, 20), [], [square(0, 0, 10)]) - 0.25) < 0.05)
  assert.equal(groundCover(square(0, 0, 20), [], []), 0)
})

test('a crown with nothing under it reaches down to what is there', () => {
  const shaft = prism(square(0, 0), 0, 100)
  const crown = prism(square(0, 0), 120, 130)
  assert.equal(settlePrisms([shaft, crown]), 1)
  assert.equal(crown.base, 100)
  const alone = prism(square(50, 50), 88, 94, { foot: 3 })
  settlePrisms([alone])
  assert.equal(alone.base, 3)
})

test('a cantilever held by a taller neighbor, and a mapped bridge, keep their bases', () => {
  const tower = prism(square(0, 0), 0, 188)
  const pod = prism(square(10, 0, 5), 46, 67)
  const span = prism(square(40, 0), 10, 14, { span: true })
  assert.equal(settlePrisms([tower, pod, span]), 0)
  assert.equal(pod.base, 46)
  assert.equal(span.base, 10)
})
