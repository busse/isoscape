import assert from 'node:assert/strict'
import { test } from 'node:test'
import { corners, frameSolids, insetRing, insetSolids, newell, sectionOf, cutPlane, trackSolids, TRACK, type Solid } from '../src/cutaway.ts'
import { ghostItem, partSolids, FRAME_PIECE, sideElevation } from '../src/cutaway-scene.ts'
import { palette } from '../src/palette.ts'
import type { HistoryFeature } from '../src/history.ts'
import type { Vec2 } from '../src/geom.ts'
import type { View } from '../src/view.ts'

const rect: Vec2[] = [[0, 0], [10, 0], [10, 4], [0, 4]]
const zs = (s: Solid) => corners(s).map((p) => p[2])
const view = { squash: 0.5, scale: 1, toScreen: (p: Vec2, z: number): Vec2 => [p[0], p[1] * 0.5 - z] } as unknown as View

test('a ring moved in stops at its middle line, not inside out', () => {
  const r = insetRing(rect, 5)
  const ys = r.map((p) => p[1])
  assert.ok(ys.every((y) => Math.abs(y - 2) < 1e-6), 'a 4-m-deep rectangle closes to a line 2 m in')
  const xs = r.map((p) => p[0]).sort((a, b) => a - b)
  assert.ok(Math.abs(xs[0] - 2) < 1e-6 && Math.abs(xs[3] - 8) < 1e-6, 'the ridge runs 2 m in from each end')
})

test('a hipped shell: one piece per side, its ridge at the top, open inside', () => {
  const solids = insetSolids(rect, [{ z: 0, outer: 0, inner: 0.3 }, { z: 3, outer: 2, inner: 2 }])
  assert.equal(solids.length, 4)
  assert.ok(Math.abs(Math.max(...solids.flatMap(zs)) - 3) < 1e-9)
  // Cut across the middle, the shell shows two thin legs, not a solid triangle.
  const pl = cutPlane([5, 0], 0, 0, 'right')
  const secs = solids.map((s) => sectionOf(s, pl)).filter((s) => s !== null)
  assert.equal(secs.length, 2)
  for (const s of secs) {
    const n = newell(s!.map(([u, z]): [number, number, number] => [u, z, 0]))
    assert.ok(Math.abs(n[2]) / 2 < 1.5, 'each leg is a thin band')
  }
})

test('a frame: each member is a slab in the plane of the ring\'s first edge; six numbers make a plate', () => {
  const ring: Vec2[] = [[0, 0], [10, 0], [10, 0.4], [0, 0.4]]
  const [beam] = frameSolids(ring, [[1, 2, 9, 2, 0.5]])
  const c = corners(beam)
  assert.ok(Math.abs(Math.min(...c.map((p) => p[2])) - 1.75) < 1e-9 && Math.abs(Math.max(...c.map((p) => p[2])) - 2.25) < 1e-9)
  assert.ok(Math.abs(Math.min(...c.map((p) => p[1]))) < 1e-9 && Math.abs(Math.max(...c.map((p) => p[1])) - 0.4) < 1e-9)
  const [plate] = frameSolids(ring, [[2, 0, 4, 0, 3, 2]])
  assert.equal(plate.faces.length, 5)
  assert.equal(frameSolids(ring, [[1, 1, 1, 1, 0.2]]).length, 0, 'a member of no length is left out')
})

test('a long frame is drawn in pieces of members, a short one whole', () => {
  const h = (ring: Vec2[]): HistoryFeature => ({ id: 'x', name: 'x', kind: 'landmark', from: 0, ring, shape: 'frame', members: [[1, 0, 2, 1, 0.2], [20, 0, 21, 1, 0.2], [40, 0, 41, 1, 0.2]], note: '', sources: [] })
  const long = partSolids({ h: h([[0, 0], [45, 0], [45, 0.4], [0, 0.4]]), outer: [[0, 0], [45, 0], [45, 0.4], [0, 0.4]], seat: 0, top: 1 })
  assert.deepEqual(long.sides, [0, 3, 6].map((k) => Math.floor((k * FRAME_PIECE + 1.5) / FRAME_PIECE)))
  const short = partSolids({ h: h([[0, 0], [10, 0], [10, 0.4], [0, 0.4]]), outer: [[0, 0], [10, 0], [10, 0.4], [0, 0.4]], seat: 0, top: 1 })
  assert.equal(short.sides, undefined)
})

test('a track on a deck: ties 0.67 m apart and two rails at standard gauge', () => {
  const solids = trackSolids([[-1.3, 0], [1.3, 0], [1.3, 6.7], [-1.3, 6.7]], 10)
  assert.equal(solids.length, 10 + 2)
  const rails = solids.slice(-2).map((s) => corners(s).map((p) => p[0]))
  const centers = rails.map((x) => (Math.min(...x) + Math.max(...x)) / 2)
  assert.ok(Math.abs(centers[1] - centers[0] - (TRACK.gauge + TRACK.railWidth)) < 1e-9)
  assert.ok(Math.abs(Math.min(...solids.flatMap(zs)) - 10) < 1e-9)
})

test('a lifted part leaves the dashed outline of its upper face, shared edges once', () => {
  const ring: Vec2[] = [[0, 0], [10, 0], [10, 5], [0, 5]]
  const g = ghostItem(view, palette('paper'), 'g', frameSolids(ring, [[0, 1, 5, 3, 0.2], [5, 3, 10, 1, 0.2]]))
  assert.ok(g !== null)
  assert.ok(g!.shapes.every((s) => s.stroke !== undefined && s.stroke.dash.length === 2))
  assert.ok(g!.shapes.length >= 6 && g!.shapes.length <= 8)
})

test('a car beside the plane is drawn from the side, flat, at true length', () => {
  const pal = palette('paper')
  const pl = cutPlane([0, 0], 0, 0, 'right')
  const b = { id: 'car:0', ring: [[-3, 0], [-3, 26], [-6.1, 26], [-6.1, 0]] as Vec2[], z0: 1, z1: 4.5, tone: 'coach' as const, front: [0, 1] as Vec2 }
  const it = sideElevation(view, pal, pl, b, -3)
  const xs = it.shapes.flatMap((s) => s.pts.map((p) => p[1]))
  assert.ok(it.id.endsWith(':side'))
  assert.ok(it.shapes.some((s) => s.fill === pal.parts.glass[0]), 'it has windows')
  assert.ok(Math.max(...xs) - Math.min(...xs) > 10, 'it runs along the plane')
})

test('inside a roof shell: a slope facing the camera covers what stands under it, one facing away does not', async () => {
  const { compare } = await import('../src/order.ts')
  const hull: Vec2[] = [[0, 0], [10, 0], [10, 10], [0, 10]]
  const item = (id: string, z0: number, z1: number, extra = {}) => ({ id, kind: 'building' as const, hull, zMin: z0, zMax: z1, key: 5, shapes: [], dots: [], ...extra })
  const floor = item('floor', 2, 2.3, { within: 'roof' })
  assert.equal(compare(item('near', 0, 5, { shell: { id: 'roof', faces: 1 } }), floor), 1)
  assert.equal(compare(item('far', 0, 5, { shell: { id: 'roof', faces: -1 } }), floor), -1)
  assert.equal(compare(floor, item('near', 0, 5, { shell: { id: 'roof', faces: 1 } })), -1)
})

test('a dormer on a roof shell paints after its sides', async () => {
  const { compare } = await import('../src/order.ts')
  const hull: Vec2[] = [[0, 0], [10, 0], [10, 10], [0, 10]]
  const item = (id: string, z0: number, z1: number, extra = {}) => ({ id, kind: 'building' as const, hull, zMin: z0, zMax: z1, key: 5, shapes: [], dots: [], ...extra })
  assert.equal(compare(item('dormer', 1, 3, { over: 'roof', key: 9 }), item('side', 0, 5, { shell: { id: 'roof', faces: 1 }, key: 1 })), 1)
})
