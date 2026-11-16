import { test } from 'node:test'
import assert from 'node:assert/strict'
import { clipRingToRect, convexHull, separatingAxis, signedArea, simplifyRing, type Vec2 } from '../src/geom.ts'
import { dominantGridAngle, makeView, snapBearing } from '../src/view.ts'
import { chainBridges, extrude, bridgeEnds, rampClearance, RAMP, type Item } from '../src/scene.ts'
import { compare, paintOrder } from '../src/order.ts'
import { assembleRings, parseOsm } from '../src/osm.ts'
import { buildingHeights, parseLength } from '../src/classify.ts'
import { palette } from '../src/palette.ts'
import type { Region } from '../src/region.ts'

const region: Region = { name: 't', title: 't', center: [0, 0], width: 200, depth: 200, bearing: 0, scale: 1 }
const view = makeView(region, 0)
const pal = palette('paper')
const square = (x: number, y: number, s = 10): Vec2[] => [[x, y], [x + s, y], [x + s, y + s], [x, y + s]]

test('signed area is positive counter-clockwise', () => {
  assert.equal(signedArea(square(0, 0)), 100)
  assert.equal(signedArea(square(0, 0).reverse()), -100)
})

test('clipping a ring to a rectangle', () => {
  const clipped = clipRingToRect(square(-5, -5), { minX: 0, minY: 0, maxX: 100, maxY: 100 })
  assert.equal(Math.abs(signedArea(clipped)), 25)
})

test('simplify drops collinear vertices', () => {
  const ring: Vec2[] = [[0, 0], [5, 0.01], [10, 0], [10, 10], [0, 10]]
  assert.equal(simplifyRing(ring, 0.1).length, 4)
})

test('separating axis points from b to a', () => {
  const a = convexHull(square(20, 0))
  const b = convexHull(square(0, 0))
  const axis = separatingAxis(a, b)!
  assert.ok(axis[0] > 0.9)
  assert.equal(separatingAxis(square(0, 0), square(5, 5)), null)
})

test('the camera faces +N′: bearing 0 puts north up the screen', () => {
  const [, yNorth] = view.toScreen([0, 10])
  const [, ySouth] = view.toScreen([0, -10])
  assert.ok(yNorth < ySouth)
  const [, yHigh] = view.toScreen([0, 0], 10)
  assert.ok(yHigh < 0)
})

test('snap puts a street grid onto the diagonals, within 45°', () => {
  const grid = dominantGridAngle([square(0, 0, 50)])!
  assert.ok(Math.abs(grid) < 1e-6)
  assert.equal(snapBearing(0, 0), 45)
  assert.equal(snapBearing(0, 30), 15)
  assert.equal(snapBearing(0, 80), -35)
})

test('a box shows only the walls that face the camera', () => {
  const item = extrude(view, pal, 'b', square(0, 0), [], 0, 10, '#fff', 'all')
  // A square seen from the south: only the south wall faces −N′; plus the roof.
  assert.equal(item.shapes.length, 2)
  const diamond: Vec2[] = [[0, -10], [10, 0], [0, 10], [-10, 0]]
  // A diamond shows two walls: south-east and south-west.
  assert.equal(extrude(view, pal, 'd', diamond, [], 0, 10, '#fff', 'all').shapes.length, 3)
})

test('a nearer building paints after a farther one', () => {
  const near: Item = extrude(view, pal, 'n', square(0, 0), [], 0, 10, '#fff', 'none')
  const far: Item = extrude(view, pal, 'f', square(0, 30), [], 0, 40, '#fff', 'none')
  assert.equal(compare(near, far), 1)
  assert.deepEqual(paintOrder([near, far]).map((i) => i.id), ['f', 'n'])
})

test('a stacked part paints above the part it stands on', () => {
  const low = extrude(view, pal, 'low', square(0, 0, 20), [], 0, 10, '#fff', 'none')
  const high = extrude(view, pal, 'high', square(5, 5), [], 10, 30, '#fff', 'none')
  assert.equal(compare(high, low), 1)
})

test('bridge ways sharing ends chain, and only grounded ends ramp', () => {
  const a = { type: 'line' as const, id: 'a', tags: { bridge: 'yes', highway: 'primary' }, points: [[0, 0], [1, 0]] as Vec2[] }
  const b = { type: 'line' as const, id: 'b', tags: { bridge: 'yes', highway: 'primary' }, points: [[1, 0], [2, 0]] as Vec2[] }
  const chains = chainBridges([a, b])
  assert.equal(chains.length, 1)
  assert.equal(chains[0].line.points.length, 3)
  assert.ok(chains[0].rampStart && chains[0].rampEnd)
})

test('a short bridge stays low; a long one reaches its deck', () => {
  // A lone bridge, grounded at both ends: its distance to the ground is to the nearer end.
  const peak = (total: number) => Math.max(...Array.from({ length: 101 }, (_, k) => {
    const s = (total * k) / 100
    return rampClearance(7, total, s, Math.min(s, total - s), 0, 0)
  }))
  assert.ok(peak(30) < 1, `30 m footbridge peaks at ${peak(30)}`)
  assert.ok(peak(80) < 7 && peak(80) > 1)
  assert.equal(peak(2 * RAMP + 10), 7)
  // An end that joins a higher deck starts at its height and eases down to its own.
  assert.equal(rampClearance(7, 200, 0, Infinity, 21, 7), 21)
  assert.equal(rampClearance(7, 200, 100, Infinity, 21, 7), 7)
})

test('a ramp that joins a higher viaduct meets it at its height', () => {
  const line = (id: string, layer: string, pts: Vec2[]) =>
    ({ type: 'line' as const, id, tags: { highway: 'motorway_link', bridge: 'yes', layer }, points: pts })
  // A layer-1 link from the ground onto a layer-3 viaduct, which runs on to the ground 440 m on.
  const link = line('l', '1', [[0, 0], [0.002, 0]])
  const viaduct = line('v', '3', [[0.002, 0], [0.006, 0]])
  const chains = chainBridges([link, viaduct])
  const ends = bridgeEnds(view, region, chains)
  const li = chains.findIndex((c) => c.line.id === 'l')
  const vi = chains.findIndex((c) => c.line.id === 'v')
  assert.equal(ends[li].start, 0)
  assert.equal(ends[li].end, 21)
  assert.equal(ends[vi].start, 21)
})

test('a viaduct that fans into short lanes comes down to them', () => {
  const line = (id: string, pts: Vec2[]) =>
    ({ type: 'line' as const, id, tags: { highway: 'trunk', bridge: 'yes', layer: '1' }, points: pts })
  // A 440 m viaduct ending at a junction where two 10 m lanes each meet the ground.
  const main = line('m', [[0, 0], [0.004, 0]])
  const a = line('a', [[0.004, 0], [0.00409, 0.00001]])
  const b = line('b', [[0.004, 0], [0.00409, -0.00001]])
  const chains = chainBridges([main, a, b])
  const ends = bridgeEnds(view, region, chains)
  // The viaduct joins one lane into a chain; the other lane meets it at the junction.
  const mi = chains.findIndex((c) => c.line.points.some((p) => p[0] === 0))
  const j = chains[mi].line.points.findIndex((p) => p[0] === 0.004 && p[1] === 0)
  assert.ok(ends[mi].toGround[j] < 12, `junction is ${ends[mi].toGround[j]} m from the ground`)
  const other = chains.findIndex((_, i) => i !== mi)
  const atJunction = chains[other].line.points[0][0] === 0.004 ? ends[other].start : ends[other].end
  assert.ok(atJunction < 1, `junction stands ${atJunction} m up`)
})

test('multipolygon fragments assemble into rings', () => {
  const rings = assembleRings([
    [[0, 0], [1, 0]],
    [[1, 1], [1, 0]],
    [[1, 1], [0, 1], [0, 0]],
  ])
  assert.equal(rings.length, 1)
  assert.equal(rings[0].length, 4)
})

test('parseOsm keeps closed area ways as polygons', () => {
  const json = JSON.stringify({
    elements: [
      { type: 'way', id: 1, tags: { building: 'yes' }, geometry: [{ lat: 0, lon: 0 }, { lat: 0, lon: 1 }, { lat: 1, lon: 1 }, { lat: 0, lon: 0 }] },
      { type: 'way', id: 2, tags: { highway: 'residential' }, geometry: [{ lat: 0, lon: 0 }, { lat: 0, lon: 1 }] },
    ],
  })
  const f = parseOsm(json)
  assert.equal(f[0].type, 'polygon')
  assert.equal(f[1].type, 'line')
})

test('heights come from tags first, then levels, then a guess', () => {
  assert.equal(parseLength('40\''), 40 * 0.3048)
  assert.equal(buildingHeights({ height: '30' }, 100).top, 30)
  assert.equal(buildingHeights({ 'building:levels': '10' }, 100).source, 'levels')
  assert.equal(buildingHeights({ building: 'house' }, 100).source, 'guess')
})

test('render: a flat region renders, paths are well formed', async () => {
  const { renderSvg } = await import('../src/render.ts')
  const { buildScene } = await import('../src/scene.ts')
  const sq = (x: number, y: number) => [{ lat: y, lon: x }, { lat: y, lon: x + 0.0002 }, { lat: y + 0.0002, lon: x + 0.0002 }, { lat: y + 0.0002, lon: x }, { lat: y, lon: x }]
  const json = JSON.stringify({ elements: [
    { type: 'way', id: 1, tags: { building: 'yes', height: '20' }, geometry: sq(0, 0) },
    { type: 'way', id: 2, tags: { natural: 'water' }, geometry: sq(-0.0005, -0.0005).map((p) => ({ lat: p.lat * 2, lon: p.lon * 2 })) },
  ] })
  const { parseOsm } = await import('../src/osm.ts')
  const scene = buildScene({ ...region, snap: false, width: 300, depth: 200 }, parseOsm(json), pal)
  const { svg } = renderSvg(scene)
  assert.ok(svg.startsWith('<svg'))
  // Every path's data starts with a move, and a move is never followed by a bare pair.
  for (const m of svg.matchAll(/ d="([^"]*)"/g)) {
    assert.match(m[1], /^M/)
    // The first pair after a move is followed by a command, never by a bare (absolute) pair.
    assert.match(m[1], /^M-?[\d.]+(?: |(?=-))-?[\d.]+(?:[lhz]|$)/, m[1].slice(0, 60))
  }
})

test('nonsense numeric tags fall back instead of poisoning heights', () => {
  const h = buildingHeights({ building: 'yes', 'building:min_level': 'federal', 'building:levels': 'two', 'roof:levels': '?' }, 100)
  assert.ok(Number.isFinite(h.base) && Number.isFinite(h.top))
  assert.equal(h.base, 0)
})
