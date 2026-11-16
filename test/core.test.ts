import { test } from 'node:test'
import assert from 'node:assert/strict'
import { clipRingToRect, convexHull, separatingAxis, signedArea, simplifyRing, type Vec2 } from '../src/geom.ts'
import { dominantGridAngle, makeView, snapBearing } from '../src/view.ts'
import {
  abutmentLevel, bridgeEnds, buildingAt, cableZ, CABLE_CLEARANCE, carveUnderBridges, chainBridges, deckProfile, extrude, isSkyway, joinDecks,
  groupDecks, rampClearance, RAMP, roofIndex, type Item,
} from '../src/scene.ts'
import { makeTerrain } from '../src/terrain.ts'
import { compare, paintOrder, spanOrder } from '../src/order.ts'
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

test('a bridge finds the building under it', () => {
  const low = extrude(view, pal, 'low', square(0, 0, 20), [], 0, 6, 'none', 'none')
  const high = extrude(view, pal, 'high', square(5, 5, 5), [], 0, 30, 'none', 'none')
  const roofs = roofIndex([low, high])
  assert.equal(buildingAt(roofs, [2, 2])?.top, 6)
  assert.equal(buildingAt(roofs, [7, 7])?.top, 30)
  assert.equal(buildingAt(roofs, [30, 30]), null)
})

test('side-by-side decks keep one order along their length', () => {
  // Two parallel decks 10 m apart; their spans are staggered, so their centers alternate.
  const near = (x: number) => ({ a: [x, 0] as Vec2, b: [x + 22, 0] as Vec2, z: 14, bridge: 'n' })
  const far = (x: number) => ({ a: [x, 10] as Vec2, b: [x + 22, 10] as Vec2, z: 14, bridge: 'f' })
  for (const dx of [-11, 0, 11]) {
    assert.equal(spanOrder(near(0), far(dx)), 1)
    assert.equal(spanOrder(far(dx), near(0)), -1)
  }
  // Crossing decks, and spans of one deck, are left to depth.
  assert.equal(spanOrder(near(0), { a: [11, -11], b: [11, 11], z: 21, bridge: 'x' }), 0)
  assert.equal(spanOrder(near(0), { ...near(22), bridge: 'n' }), 0)
  // One right over the other: the upper.
  assert.equal(spanOrder({ ...near(0), z: 21, bridge: 'u' }, near(0)), 1)
})

test('a main cable hangs between its towers and meets them at the top', () => {
  const deck = () => 67
  const towers = [{ s: 340, top: 227 }, { s: 1620, top: 227 }]
  const z = (s: number) => cableZ(s, 1960, towers, deck)
  assert.equal(z(340), 227)
  assert.equal(z(1620), 227)
  assert.ok(Math.abs(z(980) - (67 + CABLE_CLEARANCE)) < 1e-9)
  // A parabola: a quarter of the way along the main span, three quarters of the sag remains.
  assert.ok(Math.abs(z(660) - (227 - (227 - 69) * 0.75)) < 1e-9)
  // The side spans come down to the anchorages on the deck.
  assert.equal(z(0), 67 + CABLE_CLEARANCE)
  assert.ok(z(170) < (227 + 69) / 2)
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

test('the lowest parts of a bridge tower reach the ground; its struts do not', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { parseOsm } = await import('../src/osm.ts')
  const box = (x: number, y: number, w: number) => [{ lat: y, lon: x }, { lat: y, lon: x + w }, { lat: y + w, lon: x + w }, { lat: y + w, lon: x }, { lat: y, lon: x }]
  const tower = { 'building:part': 'yes', man_made: 'tower', 'tower:type': 'bridge' }
  const json = JSON.stringify({ elements: [
    { type: 'way', id: 1, tags: { ...tower, min_height: '21', height: '74' }, geometry: box(0, 0, 0.0001) },
    { type: 'way', id: 2, tags: { ...tower, min_height: '21', height: '74' }, geometry: box(0.0003, 0, 0.0001) },
    { type: 'way', id: 3, tags: { ...tower, min_height: '50', height: '52' }, geometry: box(0.0001, 0, 0.0002) },
  ] })
  const scene = buildScene({ ...region, snap: false, width: 300, depth: 200 }, parseOsm(json), pal)
  const base = (id: string) => scene.items.find((i) => i.id === id)!.zMin
  assert.equal(base('w1'), 0)
  assert.equal(base('w2'), 0)
  assert.equal(base('w3'), 50)
})

test('nonsense numeric tags fall back instead of poisoning heights', () => {
  const h = buildingHeights({ building: 'yes', 'building:min_level': 'federal', 'building:levels': 'two', 'roof:levels': '?' }, 100)
  assert.ok(Number.isFinite(h.base) && Number.isFinite(h.top))
  assert.equal(h.base, 0)
})

test('render: with terrain, a park drawn around a lake is painted under the lake, not over it', async () => {
  const { renderSvg } = await import('../src/render.ts')
  const { buildScene } = await import('../src/scene.ts')
  const { parseOsm } = await import('../src/osm.ts')
  const box = (x: number, y: number, s: number) => [{ lat: y, lon: x }, { lat: y, lon: x + s }, { lat: y + s, lon: x + s }, { lat: y + s, lon: x }, { lat: y, lon: x }]
  const json = JSON.stringify({ elements: [
    { type: 'way', id: 1, tags: { leisure: 'park' }, geometry: box(-0.002, -0.002, 0.004) },
    { type: 'way', id: 2, tags: { natural: 'water', water: 'lake' }, geometry: box(-0.0006, -0.0006, 0.0012) },
  ] })
  const scene = buildScene({ ...region, snap: false, width: 300, depth: 300, terrain: { cell: 5 } }, parseOsm(json), pal, () => 10)
  const { svg } = renderSvg(scene)
  let both = 0
  // Each strip's own markup runs to the next strip's (strips hold groups of their own).
  for (const g of svg.split('<g data-strip=').slice(1)) {
    const lawn = g.indexOf('class="green"')
    const lake = g.indexOf('class="Lw"')
    if (lawn < 0 || lake < 0) continue
    both++
    assert.ok(lawn < lake, 'the lawn comes first in its strip, and the lake over it')
  }
  assert.ok(both > 3)
})

test('render: with no slab the plate is cut square, on straight lines, over rolling ground', async () => {
  const { renderSvg } = await import('../src/render.ts')
  const { buildScene } = await import('../src/scene.ts')
  const { parseOsm } = await import('../src/osm.ts')
  const json = JSON.stringify({ elements: [] })
  // Ground that rolls across the frame, so a draped edge would wander up and down on screen.
  const scene = buildScene({ ...region, snap: false, width: 300, depth: 200, slab: 0, terrain: { cell: 5 } }, parseOsm(json), pal, (lon) => 10 + 6 * Math.sin(lon * 20000))
  const { svg } = renderSvg(scene)
  const ground = svg.match(/<clipPath id="ground"><path d="([^"]*)"/)
  assert.ok(ground, 'the ground has a clip of its own')
  // The clip is a rectangle: a move, then runs (the last closes it), each straight across or
  // straight down.
  const nums = ground[1].replace(/^M[^l]*l/, '').replace(/z$/, '').match(/-?[\d.]+/g)!.map(Number)
  assert.equal(nums.length, 6, ground[1])
  for (let k = 0; k < 6; k += 2) assert.ok(nums[k] === 0 || nums[k + 1] === 0, ground[1])
  const strips = [...svg.matchAll(/<g data-strip="[^"]*" clip-path="url\(#(\w+)\)"/g)]
  assert.ok(strips.length > 3)
  for (const m of strips) assert.equal(m[1], 'ground')
  assert.ok(!svg.includes('class="edge"'), 'no wandering ink line along the front')
})

test('close-scale ties lie square to their track on the ground, evenly spaced across a bend', async () => {
  const { tiesAlong, offsetJoined, TIE } = await import('../src/render.ts')
  // A track that runs diagonally, then bends.
  const segs: Vec2[][] = [[[0, 0], [30, 40]], [[30, 40], [30, 90]]]
  const ties = tiesAlong(segs)
  assert.ok(ties.length > 100)
  const unit = (a: Vec2, b: Vec2): Vec2 => { const l = Math.hypot(b[0] - a[0], b[1] - a[1]); return [(b[0] - a[0]) / l, (b[1] - a[1]) / l] }
  const u0 = unit([0, 0], [30, 40])
  const first = ties[0]
  // Its long side (corner 0 to 1) is square to the track, its short side (1 to 2) along it.
  const long = unit(first[0], first[1])
  assert.ok(Math.abs(long[0] * u0[0] + long[1] * u0[1]) < 1e-9)
  assert.ok(Math.abs(Math.hypot(first[1][0] - first[0][0], first[1][1] - first[0][1]) - TIE.length) < 1e-9)
  assert.ok(Math.abs(Math.hypot(first[2][0] - first[1][0], first[2][1] - first[1][1]) - TIE.width) < 1e-9)
  // Centers keep the same spacing along the line, across the bend too (measured along the track).
  const center = (q: Vec2[]): Vec2 => [(q[0][0] + q[2][0]) / 2, (q[0][1] + q[2][1]) / 2]
  const along = (p: Vec2) => (p[1] <= 40 + 1e-9 && Math.abs(p[0] - 0.75 * p[1]) < 1e-6 ? Math.hypot(p[0], p[1]) : 50 + (p[1] - 40))
  const ds = ties.map((q) => along(center(q)))
  for (let i = 1; i < ds.length; i++) assert.ok(Math.abs(ds[i] - ds[i - 1] - TIE.every) < 1e-6, `tie ${i}: ${ds[i] - ds[i - 1]}`)
  // A running rail offset from the bending line meets itself at the bend.
  const rail = offsetJoined(segs, 0.72)
  assert.ok(Math.hypot(rail[0][1][0] - rail[1][0][0], rail[0][1][1] - rail[1][0][1]) < 1e-9)
})

test('a deck over a cut runs straight between its ends, whatever is under it', () => {
  // A 40 m overpass, both ends at street level (10), over a cut 8 m deep.
  const cut = (s: number) => (s > 8 && s < 32 ? 2 : 10)
  const own = (s: number) => rampClearance(7, 40, s, Math.min(s, 40 - s), 0, 0)
  const z = deckProfile(40, cut, own, 10, 10)
  // (Within a meter of street level: it eases off the rim the way a ramp would.)
  for (let s = 0; s <= 40; s += 2) assert.ok(Math.abs(z(s) - 10) < 0.2, `deck at ${s} is ${z(s)}`)
  // Ends at different heights: a straight grade between them.
  const slope = deckProfile(40, () => 0, own, 4, 12)
  for (let s = 0; s <= 40; s += 5) assert.ok(Math.abs(slope(s) - (4 + (8 * s) / 40)) < 1e-6)
  // A long bridge from low banks still rises to its clearance in the middle.
  const river = deckProfile(300, () => 0, (s) => rampClearance(7, 300, s, Math.min(s, 300 - s), 0, 0), 0, 0)
  assert.ok(Math.abs(river(150) - 7) < 1e-6)
})

test('a grounded end sits on the rim the ground levels off at, not on a hillside', () => {
  // Past the end the ground climbs 3 m in 4 m and then levels: the end sits on the rim.
  assert.equal(abutmentLevel((t) => Math.min(3, (3 * t) / 4)), 3)
  // A steady climb (a ramp landing on a hillside): the end stays on the ground.
  assert.ok(Math.abs(abutmentLevel((t) => t / 2)) < 1e-9)
  // Level or falling ground: on the ground.
  assert.equal(abutmentLevel(() => 5), 5)
  assert.ok(Math.abs(abutmentLevel((t) => -t)) < 1e-9)
})

test('bridge ways chain straight on through a fork, never back up the other branch', () => {
  const line = (id: string, pts: Vec2[]) => ({ type: 'line' as const, id, tags: { railway: 'rail', bridge: 'yes' }, points: pts })
  // Two tracks that meet at a point, and one that runs on from it.
  const a = line('a', [[0, 0], [0.001, 0]])
  const b = line('b', [[0, 0.0002], [0.001, 0]])
  const on = line('on', [[0.001, 0], [0.002, 0]])
  const chains = chainBridges([a, b, on])
  assert.equal(chains.length, 2)
  // No chain turns back through the fork into a V.
  for (const c of chains) assert.ok(c.line.points.every((p, i, ps) => i === 0 || p[0] >= ps[i - 1][0]))
})

test('a deck that ends at another meets it at that deck\'s height', () => {
  const chain = (rampStart: boolean, rampEnd: boolean, pts: Vec2[]) => ({ line: { type: 'line' as const, id: 'x', tags: {}, points: pts }, names: '', rampStart, rampEnd })
  // A runs through the node (0.001, 0) at 30; B ends there from the ground, first drawn at 20.
  const chains = [chain(true, true, [[0, 0], [0.001, 0], [0.002, 0]]), chain(true, false, [[0.001, 0.001], [0.001, 0]])]
  const flat = (start: number, end: number) => ({ pts: [], cum: [0, 100], total: 100, zAt: (s: number) => start + ((end - start) * s) / 100, startLevel: start, endLevel: end })
  const a = { pts: [], cum: [0, 100, 200], total: 200, zAt: () => 30, startLevel: 30, endLevel: 30 }
  const lines = joinDecks(chains, [() => a, (fix) => flat(0, fix?.end ?? 20)])
  assert.equal(lines[1].endLevel, 30)
  assert.equal(lines[1].startLevel, 0)
  assert.equal(lines[0], a)
})

test('ground left standing under a deck is carved down to the ground either side', () => {
  const r: Region = { ...region, width: 200, depth: 200 }
  const v = makeView(r, 0)
  // A cut 60 m wide running along N' (floor 0, rims 10), crossed along E' by a 100 m deck that
  // the ground model kept as a ridge at street level across the cut.
  const t = makeTerrain(v, 5, 1, (lon, lat) => {
    const [x, y] = v.toView(lon, lat)
    return Math.abs(x) > 30 || Math.abs(y) < 8 ? 10 : 0
  })
  const before = t.elevation([0, 0])
  assert.ok(before > 5, `ridge stands ${before}`)
  carveUnderBridges(t, [{ pts: [[-60, 0], [60, 0]], width: 12 }], [[-60, 0], [60, 0]])
  const under = t.elevation([0, 0])
  assert.ok(under < before - 4, `ground under the deck is ${under}`)
  // The rims and the ground off the deck are untouched; nothing is raised.
  assert.ok(Math.abs(t.elevation([60, 0]) - 10) < 1e-6)
  assert.ok(Math.abs(t.elevation([0, 40])) < 1e-6)
})

test('a footbridge into a building is a skyway; a sidewalk beside a bridge is not', () => {
  const hall = extrude(view, pal, 'hall', square(0, 0, 20), [], 0, 30, 'none', 'none')
  const roofs = roofIndex([hall])
  const pts: Vec2[] = [[10, 10], [10, 40]]
  assert.equal(isSkyway({ highway: 'footway', bridge: 'yes' }, pts, roofs), true)
  assert.equal(isSkyway({ highway: 'footway', footway: 'sidewalk', bridge: 'yes' }, pts, roofs), false)
  assert.equal(isSkyway({ highway: 'primary', bridge: 'yes' }, pts, roofs), false)
  assert.equal(isSkyway({ highway: 'footway', bridge: 'yes' }, [[50, 50], [50, 80]], roofs), false)
  // A long walkway that passes a building (a suspension bridge's sidewalk at its towers) is not.
  assert.equal(isSkyway({ highway: 'cycleway', bridge: 'yes' }, [[10, 10], [10, 500]], roofs), false)
})

test('a pier stands behind its deck and behind a building nearer the camera', () => {
  const deck: Item = { id: 'd', kind: 'bridge', hull: square(0, 20, 10), zMin: 18, zMax: 20, key: 25, shapes: [], dots: [], span: { a: [0, 25], b: [10, 25], z: 20, bridge: 'd' } }
  const pier: Item = { id: 'p', kind: 'bridge', hull: square(4, 24, 2), zMin: 0, zMax: 18, key: 25, shapes: [], dots: [], pier: true }
  assert.equal(compare(pier, deck), -1)
  assert.equal(compare(deck, pier), 1)
  const house = extrude(view, pal, 'h', square(0, 0, 10), [], 0, 8, 'none', 'none')
  assert.equal(compare(pier, house), -1)
})

test('a skyway is left out and carves nothing; a street bridge in its place carves the ridge', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const m = 1 / 111320
  const box = (x: number, y: number, s: number) => [[x, y], [x + s, y], [x + s, y + s], [x, y + s], [x, y]].map(([a, b]) => ({ lon: a * m, lat: b * m }))
  // Two halls 40 m apart, a way between them at y = 10; the ground model kept a ridge under it
  // across a cut 40 m wide.
  const scene = (tags: Record<string, string>) => buildScene({ ...region, snap: false, width: 200, depth: 200, terrain: { cell: 5 } }, parseOsm(JSON.stringify({ elements: [
    { type: 'way', id: 1, tags: { building: 'yes', height: '20' }, geometry: box(-40, 0, 20) },
    { type: 'way', id: 2, tags: { building: 'yes', height: '20' }, geometry: box(20, 0, 20) },
    { type: 'way', id: 3, tags: { ...tags, bridge: 'yes', layer: '1' }, geometry: [{ lon: -20 * m, lat: 10 * m }, { lon: 20 * m, lat: 10 * m }] },
  ] })), pal, (lon, lat) => (Math.abs(lon / m) > 20 || Math.abs(lat / m - 10) < 6 ? 10 : 0))
  const sky = scene({ highway: 'footway' })
  assert.equal(sky.stats.skywaysLeftOut, 1)
  assert.equal(sky.stats.groundUnderBridgesLowered, undefined)
  assert.ok(!sky.items.some((i) => i.kind === 'bridge'))
  const street = scene({ highway: 'primary' })
  assert.equal(street.stats.skywaysLeftOut, undefined)
  assert.ok((street.stats.groundUnderBridgesLowered ?? 0) > 0)
})

test('a sidewalk beside its street is one deck with it; a short stub is level with the deck it touches', () => {
  const chain = (id: string, tags: Record<string, string>, pts: Vec2[]) => ({ line: { type: 'line' as const, id, tags: { bridge: 'yes', ...tags }, points: pts }, names: (tags.name ?? '').toLowerCase(), rampStart: true, rampEnd: true })
  const line = (pts: Vec2[], z: (s: number) => number) => {
    const cum = [0]
    for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    const total = cum[cum.length - 1]
    return { pts, cum, total, zAt: z, startLevel: z(0), endLevel: z(total) }
  }
  // A 60 m street along x at y = 0, its deck climbing from 10 to 16; a 50 m sidewalk 9 m to
  // its side on a profile of its own, lower; a 50 m ramp 4 m to the other side; a 6 m stub that
  // ends on the street's node at x = 30; a footbridge that crosses the street.
  const chains = [
    chain('street', { highway: 'primary', name: 'Broad' }, [[0, 0], [30, 0], [60, 0]]),
    chain('walk', { highway: 'footway', footway: 'sidewalk' }, [[5, 9], [55, 9]]),
    chain('ramp', { highway: 'primary_link' }, [[0, -4], [58, -4]]),
    chain('stub', { highway: 'footway' }, [[30, 0], [30, 6]]),
    chain('across', { highway: 'footway' }, [[20, -12], [20, 12]]),
  ]
  const lines = [
    line([[0, 0], [30, 0], [60, 0]], (s) => 10 + s / 10),
    line([[5, 9], [55, 9]], () => 5),
    line([[0, -4], [58, -4]], () => 20),
    line([[30, 0], [30, 6]], (s) => 2 + s),
    line([[20, -12], [20, 12]], () => 3),
  ]
  // Chains carry lon/lat points; these share the street's node at (30, 0) by key.
  const out = groupDecks(chains, lines)
  // The sidewalk takes the street's heights where it lies beside it, not the ramp's.
  for (const s of [0, 25, 50]) assert.ok(Math.abs(out[1].zAt(s) - (10 + (5 + s) / 10)) < 0.05, `walk at ${s}: ${out[1].zAt(s)}`)
  assert.ok(Math.abs(out[1].startLevel - 10.5) < 0.05)
  // The street and the crossing footbridge keep their own.
  assert.equal(out[0], lines[0])
  assert.equal(out[4], lines[4])
  // The stub is level, at the street's height at the shared node.
  assert.equal(out[3].zAt(0), 13)
  assert.equal(out[3].zAt(6), 13)
})

test('the other half of a divided street follows the longer half', () => {
  const chain = (id: string, name: string, pts: Vec2[]) => ({ line: { type: 'line' as const, id, tags: { bridge: 'yes', highway: 'primary', name }, points: pts }, names: name.toLowerCase(), rampStart: true, rampEnd: true })
  const line = (pts: Vec2[], z: (s: number) => number) => {
    const total = Math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
    return { pts, cum: [0, total], total, zAt: z, startLevel: z(0), endLevel: z(total) }
  }
  const chains = [chain('east', 'Broad', [[0, 0], [24, 0]]), chain('west', 'Broad', [[22, 10], [2, 10]]), chain('other', 'Main', [[22, -10], [2, -10]])]
  const out = groupDecks(chains, [line([[0, 0], [24, 0]], (s) => 10 + s / 4), line([[22, 10], [2, 10]], () => 0), line([[22, -10], [2, -10]], () => 0)])
  // Running the other way: its start lies beside the street's 22 m mark.
  assert.ok(Math.abs(out[1].startLevel - 15.5) < 0.05)
  assert.ok(Math.abs(out[1].endLevel - 10.5) < 0.05)
  // A street of another name keeps its own.
  assert.equal(out[2].startLevel, 0)
})
