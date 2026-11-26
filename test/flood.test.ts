import { test } from 'node:test'
import assert from 'node:assert/strict'
import { barrierLinks, barriersOf, chainLines, fillFlood, largestGroup, nodesInside, openPieces, parseFlood, parseWalls, profileSurface, signedDepth, type FloodGrid } from '../src/flood.ts'
import type { Feature } from '../src/osm.ts'
import { extrude, xrayUnder } from '../src/scene.ts'
import { makeView } from '../src/view.ts'
import { palette, withFloodStyles } from '../src/palette.ts'
import type { Region } from '../src/region.ts'
import type { Vec2 } from '../src/geom.ts'

/** A grid of nx × ny nodes, 5 m apart, from (0, 0), heights from `h(i, j)`. */
const grid = (nx: number, ny: number, h: (i: number, j: number) => number): FloodGrid => {
  const elev = new Float32Array(nx * ny)
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) elev[j * nx + i] = h(i, j)
  return { elev, nx, ny, x0: 0, y0: 0, cell: 5 }
}
const at = (g: FloodGrid, i: number, j: number) => j * g.nx + i
/** The river: the first two columns, at elevation 0. */
const riverSeeds = (g: FloodGrid) => Uint8Array.from(g.elev, (_, k) => (k % g.nx < 2 ? 1 : 0))
const level = (g: FloodGrid, e: number) => new Float32Array(g.nx * g.ny).fill(e)

test('low ground connected to the river floods; low ground behind higher ground stays dry', () => {
  // Banks at 2 m, a ridge at 20 m in column 10, and a hollow at 1 m beyond it.
  const g = grid(20, 8, (i) => (i < 2 ? 0 : i === 10 ? 20 : i >= 14 && i <= 16 ? 1 : 2))
  const f = fillFlood(g, { surface: level(g, 3), seeds: riverSeeds(g) })
  assert.equal(f.flooded[at(g, 5, 4)], 1)
  assert.ok(Math.abs(f.depth[at(g, 5, 4)] - 1) < 1e-6)
  assert.equal(f.flooded[at(g, 10, 4)], 0, 'the ridge stands clear')
  assert.equal(f.flooded[at(g, 15, 4)], 0, 'the hollow behind the ridge is not reached')
  assert.ok(Number.isNaN(f.depth[at(g, 15, 4)]))
  // The waterline field is the depth on the water side and the shortfall on the dry side.
  const sd = signedDepth(g, f)
  assert.ok(sd[at(g, 9, 4)] > 0 && sd[at(g, 10, 4)] < -10)
  assert.ok(sd[at(g, 15, 4)] < 0)
})

test('a floodwall holds while the water is below its top, and is overtopped above it', () => {
  const g = grid(20, 8, (i) => (i < 2 ? 0 : 1))
  // A wall across the whole grid between columns 10 and 11, top at 5 m.
  const wall = { name: 'w', pts: [[52.5, -10], [52.5, 50]] as Vec2[], top: 5 }
  const low = fillFlood(g, { surface: level(g, 3), seeds: riverSeeds(g), barriers: [wall] })
  assert.equal(low.flooded[at(g, 10, 4)], 1)
  assert.equal(low.flooded[at(g, 11, 4)], 0)
  assert.equal(low.held, 8, 'one held link per row')
  assert.equal(low.overtopped, 0)
  const high = fillFlood(g, { surface: level(g, 6), seeds: riverSeeds(g), barriers: [wall] })
  assert.equal(high.flooded[at(g, 15, 4)], 1)
  assert.ok(high.overtopped > 0)
  // Without the wall the low water goes through.
  const open = fillFlood(g, { surface: level(g, 3), seeds: riverSeeds(g) })
  assert.equal(open.flooded[at(g, 15, 4)], 1)
})

test('a wall stops the water only where it runs: it is outflanked round its end', () => {
  const g = grid(20, 8, (i) => (i < 2 ? 0 : 1))
  // Covers rows 0 to 5 only; rows 6 and 7 are open.
  const wall = { name: 'w', pts: [[52.5, -10], [52.5, 27.5]] as Vec2[], top: 5 }
  const f = fillFlood(g, { surface: level(g, 3), seeds: riverSeeds(g), barriers: [wall] })
  assert.equal(f.flooded[at(g, 15, 0)], 1)
  const links = barrierLinks(g, [wall])
  assert.equal(links.h[at(g, 10, 0)], 5)
  assert.equal(links.h[at(g, 10, 7)], -Infinity)
})

test('the river is the largest body of water reachable without crossing a wall', () => {
  // Columns 0–1 are the river; a canal in column 15 is cut off from it by a wall.
  const g = grid(20, 8, (i) => (i < 2 || i === 15 ? 0 : 1))
  const seeds = Uint8Array.from(g.elev, (_, k) => (k % g.nx < 2 || k % g.nx === 15 ? 1 : 0))
  const wall = { name: 'w', pts: [[52.5, -10], [52.5, 50]] as Vec2[], top: 5 }
  const f = fillFlood(g, { surface: level(g, 3), seeds, barriers: [wall] })
  assert.equal(f.flooded[at(g, 15, 4)], 0, 'the canal behind the wall does not flood the land')
  assert.equal(f.flooded[at(g, 13, 4)], 0)
  const both = largestGroup(seeds, g.nx, g.ny)
  assert.equal(both[at(g, 15, 4)], 0)
  assert.equal(both[at(g, 0, 4)], 1)
})

test('a sloped surface interpolates along the channel, held past its ends', () => {
  const g = grid(30, 10, () => 0)
  // A line from (0, 0) to (100, 0), its surface falling from 10 m to 0 m.
  const s = profileSurface(g, [[0, 0], [100, 0]], [10, 0])
  assert.ok(Math.abs(s[at(g, 10, 0)] - 5) < 1e-5)
  assert.ok(Math.abs(s[at(g, 10, 6)] - 5) < 1e-5, 'off the line, the nearest point on it decides')
  assert.ok(Math.abs(s[at(g, 25, 0)] - 0) < 1e-5, 'past the end, the end value')
  // Three points: the middle one sets the bend.
  const t = profileSurface(g, [[0, 0], [50, 0], [100, 0]], [10, 9, 0])
  assert.ok(Math.abs(t[at(g, 5, 0)] - 9.5) < 1e-5)
  assert.ok(Math.abs(t[at(g, 15, 0)] - 4.5) < 1e-5)
})

test('a pond floods low ground inside its polygon whether or not the river reaches it', () => {
  // A hollow at 1 m behind a 20 m ridge; the river is low and reaches nothing.
  const g = grid(20, 8, (i) => (i < 2 ? 0 : i === 10 ? 20 : i >= 12 && i <= 18 ? 1 : 3))
  const ring: Vec2[] = [[57.5, -1], [82.5, -1], [82.5, 36], [57.5, 36]]
  const mask = nodesInside(g, [ring])
  const f = fillFlood(g, { surface: level(g, 0.5), seeds: riverSeeds(g), ponds: [{ mask, level: 2.5 }] })
  assert.equal(f.flooded[at(g, 14, 4)], 2)
  assert.ok(Math.abs(f.depth[at(g, 14, 4)] - 1.5) < 1e-6)
  assert.equal(f.flooded[at(g, 18, 4)], 0, 'outside the polygon stays dry')
  assert.equal(f.flooded[at(g, 5, 4)], 0, 'the river does not rise')
})

test('a pond from a low point fills only the bowl around it', () => {
  // Two hollows at 1 m, parted by a 4 m rise in column 10; the pond starts in the left one.
  const g = grid(20, 8, (i) => (i === 10 ? 4 : i === 0 || i === 19 ? 9 : 1))
  const mask = new Uint8Array(g.nx * g.ny).fill(1)
  const f = fillFlood(g, { ponds: [{ mask, level: 3, seed: at(g, 5, 4) }] })
  assert.equal(f.flooded[at(g, 5, 4)], 2)
  assert.equal(f.flooded[at(g, 15, 4)], 0, 'the other hollow is not reached below the rise')
  const over = fillFlood(g, { ponds: [{ mask, level: 5, seed: at(g, 5, 4) }] })
  assert.equal(over.flooded[at(g, 15, 4)], 2, 'over the rise it is')
})

test('a pond held on the city side does not spread across a wall line, its openings closed', () => {
  // Flat ground at 1 m; a wall line between columns 10 and 11, top 12 m, over the whole grid.
  const g = grid(20, 8, () => 1)
  const mask = new Uint8Array(g.nx * g.ny).fill(1)
  const wall = { name: 'w', pts: [[52.5, -10], [52.5, 50]] as Vec2[], top: 12 }
  const free = fillFlood(g, { ponds: [{ mask, level: 3, seed: at(g, 5, 4) }] })
  assert.equal(free.flooded[at(g, 15, 4)], 2, 'without the wall the pond spreads')
  const held = fillFlood(g, { ponds: [{ mask, level: 3, seed: at(g, 5, 4), barriers: [wall] }] })
  assert.equal(held.flooded[at(g, 5, 4)], 2)
  assert.equal(held.flooded[at(g, 15, 4)], 0, 'held on the city side')
})

test('wall pieces are chained across small gaps, not large ones', () => {
  const lines = chainLines([[[0, 0], [10, 0]], [[50, 0], [40, 0]], [[12, 0], [30, 0]]], 15)
  assert.equal(lines.length, 1)
  assert.equal(lines[0].length, 6)
  assert.equal(chainLines([[[0, 0], [10, 0]], [[100, 0], [110, 0]]], 15).length, 2)
})

test('a flood in the region config is checked', () => {
  const r = { name: 't', floods: { a: { level: 'high' }, b: { level: 9, walls: true }, c: {} } } as unknown as Region
  assert.throws(() => parseFlood(r, 'a'), /level/)
  assert.throws(() => parseFlood(r, 'c'), /level/)
  assert.throws(() => parseFlood(r, 'zzz'), /no flood/)
  assert.deepEqual(parseFlood(r, 'b'), { name: 'b', level: 9, walls: true })
})

test('a dated wall stands only from its year', () => {
  const r = { name: 't', floodwalls: [{ name: 'w', line: [[0, 0], [1, 1]], top: 12.5, from: 1994 }], floods: { f: { level: 9, walls: true } } } as unknown as Region
  const f = parseFlood(r, 'f')
  assert.equal(parseWalls(r, f, 1972).length, 0)
  assert.equal(parseWalls(r, f, 1996).length, 1)
  assert.equal(parseWalls(r, f).length, 1, 'an undated scene has it')
})

test('the gaps between mapped wall pieces are openings, open or shut', () => {
  const feats = [
    { type: 'line', id: 'a', tags: { wall: 'flood_wall' }, points: [[0, 0], [10, 0]] },
    { type: 'line', id: 'b', tags: { wall: 'flood_wall' }, points: [[20, 0], [30, 0]] },
  ] as unknown as Feature[]
  const walls = barriersOf([{ name: 'w', osm: 'flood_wall', top: 5 }], feats, (lon, lat) => [lon, lat])
  assert.equal(walls.length, 1)
  assert.deepEqual(walls[0].gaps, [false, true, false])
  const open = openPieces(walls[0])
  assert.equal(open.length, 2, 'open gates part the wall in two')
  // Shut, the water cannot pass the opening; open, it can.
  const g = grid(40, 4, (i) => (i < 2 ? 0 : 1))
  const wall = { name: 'w', pts: [[-1, 7.5], [10, 7.5], [20, 7.5], [41 * 5, 7.5]] as Vec2[], top: 5, gaps: [false, true, false] }
  const seeds = Uint8Array.from(g.elev, (_, k) => (Math.floor(k / g.nx) === 0 ? 1 : 0))
  const shut = fillFlood(g, { surface: level(g, 3), seeds, barriers: [wall] })
  assert.equal(shut.flooded[at(g, 3, 3)], 0)
  const gates = fillFlood(g, { surface: level(g, 3), seeds, barriers: openPieces(wall) })
  assert.equal(gates.flooded[at(g, 3, 3)], 1)
})

test('the range, soft pool, markers and notes of a flood are read from the region', () => {
  const r = { name: 't', floods: {
    a: { level: 9, uncertainty: 0.9, band: 'range', soft: true, notes: ['x {floodAcres}'], markers: [{ at: [1, 2], key: '1 here' }], gates: 'open' },
    b: { level: 9, uncertainty: -1 }, c: { level: 9, band: 'wide' }, d: { level: 9, markers: [{ key: 'no place' }] },
  } } as unknown as Region
  const a = parseFlood(r, 'a')
  assert.equal(a.uncertainty, 0.9)
  assert.equal(a.band, 'range')
  assert.equal(a.soft, true)
  assert.equal(a.gates, 'open')
  assert.deepEqual(a.markers, [{ n: '1', at: [1, 2], key: '1 here' }])
  assert.throws(() => parseFlood(r, 'b'), /uncertainty/)
  assert.throws(() => parseFlood(r, 'c'), /band/)
  assert.throws(() => parseFlood(r, 'd'), /markers/)
})

test('the range of an estimate: the fill at the high end reaches more ground', () => {
  // A slope rising 0.2 m a column from a river at 0.
  const g = grid(30, 4, (i) => (i < 2 ? 0 : i * 0.2))
  const lo = fillFlood(g, { surface: level(g, 3), seeds: riverSeeds(g) })
  const hi = fillFlood(g, { surface: level(g, 3.9), seeds: riverSeeds(g) })
  const band = Array.from(hi.flooded).filter((v, k) => v !== 0 && lo.flooded[k] === 0).length
  assert.equal(band, 4 * 5, 'five more columns, 0.9 m of rise at 0.2 m a column (rounded down)')
})

test('staff gauges are read from the region', () => {
  const r = { name: 't', floods: { a: { level: 9, gauges: [{ at: [1, 2], name: '17th and Main' }] }, b: { level: 9, gauges: [{ name: 'nowhere' }] } } } as unknown as Region
  assert.deepEqual(parseFlood(r, 'a').gauges, [{ at: [1, 2], name: '17th and Main' }])
  assert.throws(() => parseFlood(r, 'b'), /gauges/)
})

test('x-ray walls: a building in water gets its walls under the surface, painted later', () => {
  const view = makeView({ name: 't', title: 't', center: [0, 0], width: 200, depth: 200, bearing: 0, scale: 2, squash: 0.5 } as Region, 0)
  const outer: Vec2[] = [[0, 0], [10, 0], [10, 10], [0, 10]]
  const pal = withFloodStyles(palette('paper'), ['blue-grey', 'xray'])
  const item = extrude(view, pal, 'b', outer, [], 3, 10, '#ffffff', 'none')
  const dry = xrayUnder(view, pal, outer, item)
  assert.equal(dry.under, undefined)
  const wet = xrayUnder(view, pal, outer, item, { water: 3, ground: () => 0 })
  assert.ok(wet.under !== undefined && wet.under.shapes.length > 0)
  // 3 m of water at a 30 degree tilt: reach = 3 cos/sin + 1.
  assert.ok(Math.abs(wet.under!.reach - (3 * Math.sqrt(3) + 1)) < 1e-6)
  assert.equal(xrayUnder(view, palette('paper'), outer, item, { water: 3, ground: () => 0 }).under, undefined, 'only with the look')
})

test('a flood plate draws the river, canal and basins in the flood look\'s channel color, with no waterline across the river', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { renderSvg } = await import('../src/render.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 300, depth: 300, bearing: 0, scale: 1, terrain: { cell: 5 }, floods: { dry: { level: -20 } } } as const
  const ll = lonLatFromLocal(region as never)
  const ring = [[-150, -150], [150, -150], [150, -60], [-150, -60]].map(([e, n]) => ll(e, n) as Vec2)
  const water = { type: 'polygon' as const, id: 'w1', tags: { natural: 'water' }, outers: [ring], inners: [] }
  const pal = withFloodStyles(palette('paper'), ['blue-grey'])
  const plain = renderSvg(buildScene(region as never, [water], pal, () => 2)).svg
  const flood = renderSvg(buildScene(region as never, [water], pal, () => 2, { flood: parseFlood(region as never, 'dry') })).svg
  const channel = pal.flood.channel!
  assert.ok(!plain.includes(`.W{fill:${channel}`), 'a plate without a flood keeps the palette\'s water')
  assert.ok(flood.includes(`.W{fill:${channel}`), 'a flood plate draws its water in the channel color')
})

test('where the flood\'s level falls below the river\'s own surface (the falls), the river keeps its own color and no waterline or depth tone is laid on it', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { renderSvg } = await import('../src/render.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 300, depth: 300, bearing: 0, scale: 1, terrain: { cell: 5 }, floods: { mid: { level: 3 } } } as const
  const ll = lonLatFromLocal(region as never)
  const ring = [[-200, -200], [200, -200], [200, 200], [-200, 200]].map(([e, n]) => ll(e, n) as Vec2)
  const water = { type: 'polygon' as const, id: 'w1', tags: { natural: 'water' }, outers: [ring], inners: [] }
  const pal = withFloodStyles(palette('paper'), ['blue-grey'])
  // River across the whole plate, climbing from 0 m at the east edge to 6 m at the west.
  const [lon0] = ll(-150, 0)
  const [lon1] = ll(150, 0)
  const elevation = (lon: number): number => 6 * (lon1 - lon) / (lon1 - lon0)
  const svg = renderSvg(buildScene(region as never, [water], pal, elevation, { flood: parseFlood(region as never, 'mid') })).svg
  assert.ok(!/class="fl[0-8]"/.test(svg), 'no depth tone on the river\'s own water')
  assert.ok(!svg.includes('class="fle"'), 'no waterline across the river')
})
