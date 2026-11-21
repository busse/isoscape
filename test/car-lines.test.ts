import assert from 'node:assert/strict'
import { test } from 'node:test'
import { followRun, nearestOn, roundStretches, runCarrying } from '../src/scene.ts'
import { simplifyLine } from '../src/geom.ts'
import type { Vec2 } from '../src/geom.ts'

test('a deck laid on a car line follows its bends and keeps its own nodes', () => {
  const run: Vec2[] = [[0, 0], [50, 0], [100, 20], [150, 20]]
  const deck: Vec2[] = [[20, 3], [130, 23]]
  assert.notEqual(runCarrying([[20, 0], [45, 0]], [run], 13.5), null)
  const on = deck.map((p) => nearestOn(p, run))
  assert.deepEqual(on[0], [20, 0])
  const out = followRun(on, [run])
  assert.deepEqual(out, [[20, 0], [50, 0], [100, 20], [130, 20]])
})

test('a round stretch keeps its curve; the rest is straightened as before', () => {
  const raw: Vec2[] = Array.from({ length: 101 }, (_, i): Vec2 => [i * 4, i < 50 ? 0 : 30 * Math.sin(((i - 50) / 50) * Math.PI)])
  const simple = simplifyLine(raw, 7)
  assert.equal(roundStretches(raw, simple, []), simple)
  const round = roundStretches(raw, simple, [{ from: [220, 0], to: [380, 0], tolerance: 0.5 }])
  assert.ok(round.length > simple.length)
  // Before the stretch's first straightened vertex nothing changes.
  const first = simple.findIndex((p) => p[0] >= 200)
  assert.deepEqual(round.slice(0, first), simple.slice(0, first))
})
