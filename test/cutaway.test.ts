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

test('a footprint pushed out keeps its corners square', async () => {
  const { offsetConvex } = await import('../src/cutaway.ts')
  const out = offsetConvex(box, 1)
  assert.deepEqual(out.map((p) => p.map((v) => Math.round(v * 1e9) / 1e9)), [[-1, -1], [5, -1], [5, 3], [-1, 3]])
})

test('long boxes are cut into short pieces along their length', async () => {
  const { shortPieces, BOX_PIECE } = await import('../src/cutaway-scene.ts')
  const pieces = shortPieces({ id: 'car', ring: [[0, 0], [26, 0], [26, 3], [0, 3]], z0: 0, z1: 4, tone: 'coach' })
  assert.equal(pieces.length, Math.ceil(26 / BOX_PIECE))
  assert.deepEqual(pieces[0].ring[1], [26 / pieces.length, 0])
  assert.equal(pieces[pieces.length - 1].id, `car/${pieces.length - 1}`)
  assert.equal(shortPieces({ id: 'cab', ring: [[0, 0], [4, 0], [4, 3], [0, 3]], z0: 0, z1: 4, tone: 'engine' }).length, 1)
})

test('stacked: a part wholly above a nearer one is left unordered', async () => {
  const { compare } = await import('../src/order.ts')
  const item = (n0: number, n1: number, z0: number, z1: number) => ({
    id: 'x', kind: 'building' as const, hull: [[0, n0], [1, n0], [1, n1], [0, n1]] as Vec2[], zMin: z0, zMax: z1, key: (n0 + n1) / 2, shapes: [], dots: [],
  })
  const near = item(0, 1, 0, 4)
  const farHigh = item(2, 3, 6, 8)
  const farLow = item(2, 3, 0, 8)
  assert.equal(compare(near, farHigh), 1)
  assert.equal(compare(near, farHigh, true), 0)
  assert.equal(compare(near, farLow, true), 1)
  // Footprints that overlap by a rounding centimeter still count as apart.
  assert.equal(compare(item(0, 2.01, 0, 4), farLow, true), 1)
})

test('the traveler stands 1.75 m tall, feet on the floor', async () => {
  const { travelerShapes, TRAVELER_HEIGHT } = await import('../src/traveler.ts')
  const pts = travelerShapes().flat()
  assert.equal(TRAVELER_HEIGHT, 1.75)
  assert.ok(Math.abs(Math.max(...pts.map((p) => p[1])) - 1.75) < 0.01)
  assert.ok(Math.abs(Math.min(...pts.map((p) => p[1]))) < 1e-9)
})

test('the section path stops short of what it must not cross, and leaves no scraps', async () => {
  const { routeRuns, arrowOn } = await import('../src/section.ts')
  // A path across a box (a car end): the part inside the box is gone, either side is kept.
  const runs = routeRuns([[0, 0], [100, 0]], [[40, -5, 60, 5]])
  assert.equal(runs.length, 2)
  assert.ok(runs[0][runs[0].length - 1][0] <= 40 && runs[1][0][0] >= 60)
  // A scrap shorter than the minimum, between two boxes, is dropped.
  assert.equal(routeRuns([[0, 0], [100, 0]], [[10, -5, 50, 5], [55, -5, 90, 5]], 10).length, 2)
  // The arrowhead points the way the path runs.
  const head = arrowOn([[0, 0], [100, 0]], 8)!
  assert.ok(head[0][0] > head[1][0])
})

test('a piece of a hipped roof keeps the whole roof\'s slopes', async () => {
  const { roofPiece, roofSolid } = await import('../src/cutaway-scene.ts')
  // A hip 30 m by 18 m, 0 to 9 m: the ridge runs 12 m, from x = 9 to x = 21.
  const whole: Vec2[] = [[0, 0], [30, 0], [30, 18], [0, 18]]
  const top = (s: Solid) => Math.max(...s.faces.flatMap((f) => f.pts.map((p) => p[2])))
  const zAt = (s: Solid, x: number) => Math.max(...s.faces.flatMap((f) => f.pts).filter((p) => Math.abs(p[0] - x) < 1e-6).map((p) => p[2]))
  // The piece east of x = 6 reaches the ridge, and at its cut it stands as the whole roof does (6 m),
  // not at its eaves as a hip on its own ring would.
  const east = roofPiece(whole, [[6, 0], [30, 0], [30, 18], [6, 18]], 0, 9)
  assert.ok(Math.abs(top(east) - 9) < 1e-6)
  assert.ok(Math.abs(zAt(east, 6) - 6) < 1e-6)
  assert.ok(zAt(roofSolid([[6, 0], [30, 0], [30, 18], [6, 18]], 0, 9, 'hip'), 6) < 1e-6)
  // A piece wholly in the west hip stays under it.
  const west = roofPiece(whole, [[0, 10], [6, 10], [6, 18], [0, 18]], 0, 9)
  assert.ok(Math.abs(top(west) - 6) < 1e-6)
  assert.equal(west.faces.filter((f) => f.role === 'cut').length, 0)
})
