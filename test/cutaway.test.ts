import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  below, clipSolid, cutPlane, inFront, isConvex, newell, prism, revolve, sectionOf, solidItem, splitSolids, stair, unionOutline,
  type Solid,
} from '../src/cutaway.ts'
import { confidenceOf } from '../src/history.ts'
import type { View } from '../src/view.ts'
import type { Vec2 } from '../src/geom.ts'

const area = (pts: readonly (readonly [number, number, number])[]) => {
  const n = newell(pts)
  return Math.hypot(n[0], n[1], n[2]) / 2
}
const cuts = (s: Solid) => s.faces.filter((f) => f.role === 'cut')
const xs = (s: Solid) => s.faces.flatMap((f) => f.pts.map((p) => p[0]))
const box: Vec2[] = [[0, 0], [4, 0], [4, 2], [0, 2]]
// The plane x = 1, running along +N′ (a view looking north, a plane bearing north), its right
// side (+E′) lifted away.
const plane = cutPlane([1, 0], 0, 0, 'right')

test('the cut plane runs along its bearing and points to the removed side', () => {
  assert.deepEqual(plane.u.map((v) => Math.round(v * 1e9) / 1e9), [0, 1])
  assert.deepEqual(plane.n.map((v) => Math.round(v * 1e9) / 1e9), [1, -0])
  const left = cutPlane([0, 0], 90, 0, 'left')
  // A plane running east with its left (north) side removed.
  assert.ok(Math.abs(left.n[1] - 1) < 1e-9)
})

test('a prism split by the plane: the back keeps a section, the front a plan up to the kept height', () => {
  const { back, front } = splitSolids([prism(box, 0, 3)], plane, 1)
  assert.equal(back.length, 1)
  assert.equal(front.length, 1)
  assert.deepEqual([Math.min(...xs(back[0])), Math.max(...xs(back[0]))], [0, 1])
  const section = cuts(back[0])
  assert.equal(section.length, 1)
  assert.ok(Math.abs(area(section[0].pts) - 6) < 1e-9)
  // The front is 3 wide, 2 deep and 1 high, cut on top (and on the plane, facing away).
  const tops = cuts(front[0]).filter((f) => f.pts.every((p) => Math.abs(p[2] - 1) < 1e-9))
  assert.equal(tops.length, 1)
  assert.ok(Math.abs(area(tops[0].pts) - 6) < 1e-9)
  assert.ok(front[0].faces.every((f) => f.pts.every((p) => p[0] >= 1 - 1e-9 && p[2] <= 1 + 1e-9)))
})

test('with nothing kept in front, the front is empty; a solid wholly behind is returned as is', () => {
  const whole = prism([[-3, 0], [-1, 0], [-1, 1], [-3, 1]], 0, 2)
  const { back, front } = splitSolids([prism(box, 0, 3), whole], plane)
  assert.equal(front.length, 0)
  assert.equal(back[1], whole)
  assert.equal(clipSolid(whole, inFront(plane)), null)
  assert.equal(clipSolid(prism(box, 0, 3), below(-1)), null)
})

test('the section of a prism, in plane coordinates', () => {
  const sec = sectionOf(prism(box, 0, 3), plane)
  assert.ok(sec !== null)
  const s = sec.map((p) => p[0])
  const z = sec.map((p) => p[1])
  assert.deepEqual([Math.min(...s), Math.max(...s), Math.min(...z), Math.max(...z)], [0, 2, 0, 3])
  assert.equal(sectionOf(prism([[2, 0], [3, 0], [3, 1], [2, 1]], 0, 1), plane), null)
})

test('a hollow drum cut through its axis shows two wall sections, not one solid', () => {
  // A 24-sided ring of radius 10 about (1, 0), one corner on the plane's direction.
  const ring: Vec2[] = Array.from({ length: 24 }, (_, k) => [1 + 10 * Math.cos(Math.PI / 2 + (2 * Math.PI * k) / 24), 10 * Math.sin(Math.PI / 2 + (2 * Math.PI * k) / 24)])
  const pieces = revolve(ring, [{ z: 0, outer: 1, inner: 0.5 }, { z: 4, outer: 1, inner: 0.5 }])
  assert.equal(pieces.length, 24)
  let total = 0
  for (const p of pieces) {
    const sec = sectionOf(p, plane)
    if (sec === null) continue
    let a = 0
    for (let i = 0; i < sec.length; i++) a += sec[i][0] * sec[(i + 1) % sec.length][1] - sec[(i + 1) % sec.length][0] * sec[i][1]
    total += Math.abs(a) / 2
  }
  // Two walls 5 thick and 4 high.
  assert.ok(Math.abs(total - 40) < 1e-6, String(total))
})

test('a stair rises tread by tread from its first edge', () => {
  const steps = stair([[0, 0], [2, 0], [2, 6], [0, 6]], 0, 3, 6)
  assert.equal(steps.length, 6)
  const tops = steps.map((s) => Math.max(...s.faces.flatMap((f) => f.pts.map((p) => p[2]))))
  assert.deepEqual(tops, [0.5, 1, 1.5, 2, 2.5, 3])
})

test('drawing a box: only faces turned to the camera, sections last', () => {
  const view = { squash: 0.6, toScreen: ([e, n]: Vec2, z = 0) => [e * 10, -n * 6 - z * 8] } as unknown as View
  const tones = { lit: '#ffffff', shade: '#000000', roof: '#888888', cut: '#111111' }
  const whole = solidItem(view, tones, 'a', [prism(box, 0, 3)])
  // Top and the near wall (the far and side walls face away or edge on).
  assert.equal(whole?.shapes.length, 2)
  const { back } = splitSolids([prism(box, 0, 3)], cutPlane([1, 0], 30, 0, 'right'))
  const item = solidItem(view, tones, 'b', back)
  assert.equal(item?.shapes[item.shapes.length - 1].fill, '#111111')
})

test('the outline of footprints that share an edge is their union', () => {
  const segs = unionOutline([[[0, 0], [1, 0], [1, 1], [0, 1]], [[1, 0], [2, 0], [2, 1], [1, 1]]])
  const length = segs.reduce((a, [p, q]) => a + Math.hypot(q[0] - p[0], q[1] - p[1]), 0)
  assert.ok(Math.abs(length - 6) < 1e-9)
  assert.ok(isConvex(box))
  assert.ok(!isConvex([[0, 0], [4, 0], [4, 4], [2, 1], [0, 4]]))
})

test('a part says how it is known, approximate unless it says otherwise', () => {
  assert.equal(confidenceOf({}), 'approximate')
  assert.equal(confidenceOf({ confidence: 'drawn' }), 'drawn')
  assert.equal(confidenceOf({ confidence: 'written' }), 'written')
})
