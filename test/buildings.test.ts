import { test } from 'node:test'
import assert from 'node:assert/strict'
import { groundCover, seatLevel, settlePrisms, type Prism } from '../src/scene.ts'
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

test('a building on exaggerated slopes counts its height from the true slope', () => {
  // Flat ground: the ground itself.
  assert.equal(seatLevel([4, 4, 4, 4], 2), 4)
  // 20 m of drawn fall at 2x is 10 m of true fall: half of it shows below the roof.
  assert.equal(seatLevel([0, 20, 20, 0], 2), 5)
  // Unexaggerated ground: the middle of the fall.
  assert.equal(seatLevel([0, 20], 1), 10)
  assert.equal(seatLevel([0, 20], 0.5), 10)
})

test('a building tagged implausibly low, zero or unreadable gets the usual guess', async () => {
  const { buildingHeights } = await import('../src/classify.ts')
  for (const height of ['0.4', '0', 'huge', '37;35']) {
    const h = buildingHeights({ building: 'house', height }, 120)
    assert.equal(h.source, 'guess')
    assert.equal(h.top, 8)
  }
  assert.equal(buildingHeights({ building: 'house', height: '6' }, 120).top, 6)
  // A part may be low: steps, a plinth.
  assert.equal(buildingHeights({ 'building:part': 'steps', height: '0.5' }, 120).source, 'height')
})
