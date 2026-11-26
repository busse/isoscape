import { test } from 'node:test'
import assert from 'node:assert/strict'
import { convexPieces, type Vec2 } from '../src/geom.ts'
import { makeView } from '../src/view.ts'
import { buildScene, extrude, type Item } from '../src/scene.ts'
import { paintOrder } from '../src/order.ts'
import { parseOsm } from '../src/osm.ts'
import { palette } from '../src/palette.ts'
import { nearerThanBand, overPaints, prismDepth, type Painted } from '../src/occlusion.ts'
import type { Region } from '../src/region.ts'

const region: Region = { name: 't', title: 't', center: [0, 0], width: 300, depth: 300, bearing: 0, scale: 2, snap: false }
const view = makeView(region, 0)
const pal = palette('paper')

test('an L is cut into two convex pieces; a convex ring stays whole', () => {
  const L: Vec2[] = [[0, 0], [10, 0], [10, 4], [4, 4], [4, 10], [0, 10]]
  const parts = convexPieces(L)
  assert.equal(parts.length, 2)
  assert.deepEqual(parts.flat().sort(), [0, 0, 1, 2, 3, 3, 4, 5])
  assert.equal(convexPieces([[0, 0], [10, 0], [10, 10], [0, 10]]).length, 1)
})

test('the nearest surface on a line of sight is the highest point of the prism on it', () => {
  const ring: Vec2[] = [[-5, -5], [5, -5], [5, 5], [-5, 5]]
  // The roof's near edge at height 10.
  const roofNear = view.toScreen([0, -5], 10)
  assert.ok(Math.abs(prismDepth(view, ring, 0, 10, roofNear)! + 5) < 1e-6)
  // A point on the front wall, halfway up: N' -5.
  assert.ok(Math.abs(prismDepth(view, ring, 0, 10, view.toScreen([0, -5], 5))! + 5) < 1e-6)
  // Above the roof: missed.
  assert.equal(prismDepth(view, ring, 0, 10, view.toScreen([0, 6], 10)), null)
})

/**
 * Two buildings that wrap round each other, like the Paper Company's tower and garage on Hull
 * Street (OSM w943656806, w943656807): a tall L, and a low L in its notch whose west end lies
 * behind the tall one's west arm. Their convex hulls overlap, so one order serves neither.
 */
const interlocked = (strict: boolean) => {
  const toLonLat = (p: Vec2) => view.fromView(p)
  // The shared edge slants back to the west, as the real one does, so the low one's west end
  // lies behind the tall one's west arm on screen.
  const tall: Vec2[] = [[-30, -30], [-5, -30], [-5.5, -22], [-8, 0], [40, 0], [40, 15], [-30, 15]]
  const low: Vec2[] = [[-5.5, -22], [45, -22], [45, 15], [40, 15], [40, 0], [-8, 0]]
  const way = (id: number, ring: Vec2[], tags: Record<string, string>) => ({ type: 'way', id, tags: { building: 'yes', ...tags }, geometry: [...ring, ring[0]].map((p) => { const [lon, lat] = toLonLat(p); return { lon, lat } }) })
  const json = JSON.stringify({ elements: [way(1, [...tall].reverse(), { height: '40' }), way(2, [...low].reverse(), { height: '10' })] })
  const sc = buildScene({ ...region, ...(strict ? { occlusion: 'strict' as const } : {}) }, parseOsm(json), pal)
  const order: Painted[] = paintOrder(sc.items.filter((it) => it.kind === 'building')).map((item) => ({ item }))
  return { sc, faults: overPaints(view, order, { skip: (a, b) => a.item.id.split('#')[0] === b.item.id.split('#')[0] }) }
}

test('interlocking buildings: drawn whole, one is painted over the nearer one; in pieces, never', () => {
  const plain = interlocked(false)
  assert.ok(plain.faults.length > 0, 'the whole-building order paints over a nearer face')
  const strict = interlocked(true)
  assert.deepEqual(strict.faults, [])
  assert.ok(strict.sc.items.some((it) => it.id.includes('#')), 'drawn in pieces')
  assert.equal(strict.sc.stats.buildings, 2, 'a building in pieces counts once')
})

test('a piece has no wall and no roof ink along its seams', () => {
  const piece: Vec2[] = [[0, 0], [10, 0], [10, 4], [0, 4]]
  const whole = extrude(view, pal, 'a', piece, [], 0, 5, pal.roofs.other[0], 'none')
  const cut = extrude(view, pal, 'a#0', piece, [], 0, 5, pal.roofs.other[0], 'none', undefined, undefined, undefined, new Set([0]))
  // Edge 0 (the near side, facing the camera) is a seam: its wall goes, and the roof is sealed
  // with ink on its three other edges.
  assert.equal(cut.shapes.filter((s) => s.ink === true).length, whole.shapes.filter((s) => s.ink === true).length - 2)
  assert.equal(cut.shapes.filter((s) => s.line === true).length, 3)
})

test('a band behind a nearer building painted before it is cut from it', () => {
  // A wall face at N' 20 under water (its band), and a building in front of it at N' 0 to 10.
  const front = extrude(view, pal, 'front', [[-10, 0], [10, 0], [10, 10], [-10, 10]], [], 0, 12, pal.roofs.other[0], 'none')
  const back = extrude(view, pal, 'back', [[-10, 20], [10, 20], [10, 30], [-10, 30]], [], 0, 30, pal.roofs.other[0], 'none')
  const band: Item = {
    ...back,
    under: { reach: 1, edges: [[[-10, 20], [10, 20]]], shapes: [{ pts: [view.toScreen([-10, 20], 8), view.toScreen([10, 20], 8), view.toScreen([10, 20], 0), view.toScreen([-10, 20], 0)], fill: '#000000' }] },
  }
  const faults = overPaints(view, [{ item: band }, { item: front }, { item: band, band: true }])
  assert.ok(faults.some((f) => f.over === 'band:back' && f.under === 'front'), 'painted last, the band covers the nearer building')
  assert.deepEqual(nearerThanBand(view, [{ item: front }], { item: band, band: true }).map((p) => p.item.id), ['front'])
  // A building behind the band is not cut from it.
  const behind = extrude(view, pal, 'behind', [[-10, 40], [10, 40], [10, 50], [-10, 50]], [], 0, 60, pal.roofs.other[0], 'none')
  assert.deepEqual(nearerThanBand(view, [{ item: behind }], { item: band, band: true }), [])
})

test('a wall that runs through a building stops at its outline; a wall beside one is untouched', async () => {
  const { outsideRuns, mitredQuad, topBand } = await import('../src/scene.ts')
  const house: Vec2[] = [[4, -2], [6, -2], [6, 2], [4, 2]]
  // Through it: the wall on either side, none of it inside.
  const runs = outsideRuns([0, 0], [10, 0], [house])
  assert.equal(runs.length, 2)
  assert.ok(runs[0][1] <= 0.4 + 1e-9 && runs[1][0] >= 0.6 - 1e-9)
  assert.ok(runs[0][1] > 0.35 && runs[1][0] < 0.65)
  // Alongside it, 1 m off: whole.
  assert.deepEqual(outsideRuns([0, 3], [10, 3], [house]), [[0, 1]])
  // Wholly inside: nothing.
  assert.deepEqual(outsideRuns([4.5, 0], [5.5, 0], [house]), [])
  // Mitred pieces at a bend share their joint edge: no overlap, no gap.
  const a = mitredQuad([0, 0], [10, 0], undefined, [10, 10], 1)!
  const b = mitredQuad([10, 0], [10, 10], [0, 0], undefined, 1)!
  assert.deepEqual(a[1].map((v) => +v.toFixed(9)), b[0].map((v) => +v.toFixed(9)))
  assert.deepEqual(a[2].map((v) => +v.toFixed(9)), b[3].map((v) => +v.toFixed(9)))
  // A casing band's ends are cut square to the screen, so two pieces' bands meet without overlap.
  const p = topBand([0, 0], [10, 3], 4), q = topBand([10, 3], [20, 6], 4)
  assert.equal(p[1][0], q[0][0])
  assert.equal(p[2][0], q[3][0])
})
