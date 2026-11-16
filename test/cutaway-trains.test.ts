import assert from 'node:assert/strict'
import { test } from 'node:test'
import { cutPlane } from '../src/cutaway.ts'
import { distanceToRing, flatElevations, isCoupled } from '../src/cutaway-scene.ts'
import { PALETTES } from '../src/palette.ts'
import { trainBoxes } from '../src/parts.ts'
import type { Vec2 } from '../src/geom.ts'
import type { View } from '../src/view.ts'

const view = { squash: 0, toScreen: ([e]: Vec2, z = 0) => [e * 10, -z * 10] } as unknown as View
// A track running north from the origin; a train of an engine, its tender and three coaches.
const line: Vec2[] = [[0, 0], [0, 200]]
const boxes = trainBoxes('history:t', line, { cars: 3, at: 10 }, () => 0)

test('a train faces the start of its line, and each car knows whether one stands ahead of it', () => {
  const cars = boxes.filter((b) => !b.id.endsWith(':cab'))
  for (const b of cars) assert.deepEqual(b.front?.map((v) => Math.round(v)), [-0, -1])
  // The engine leads; the tender and every coach have something just ahead.
  assert.deepEqual(cars.map((b) => isCoupled(b, boxes)), [false, true, true, true, true])
})

test('the flat section draws one car end per track, square on and true size, where the track meets the plane', () => {
  // A plane running east across the track at N′ = 60, the near side lifted away.
  const plane = cutPlane([0, 60], 90, 0, 'right')
  const items = flatElevations(view, PALETTES.paper, plane, boxes, 16)
  const ends = items.filter((it) => it.id.startsWith('history:t:'))
  assert.equal(ends.length, 1)
  const xs = ends[0].shapes.flatMap((s) => s.pts.map((p) => p[0] / 10))
  // A coach 3.1 m wide, centered on the track.
  assert.ok(Math.abs(Math.min(...xs) + 1.55) < 0.01 && Math.abs(Math.max(...xs) - 1.55) < 0.01)
})

test('distance to a convex ring is zero inside and the gap outside', () => {
  const sq: Vec2[] = [[0, 0], [2, 0], [2, 2], [0, 2]]
  assert.equal(distanceToRing([1, 1], sq), 0)
  assert.ok(Math.abs(distanceToRing([3, 1], sq) - 1) < 1e-9)
})
