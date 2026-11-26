import { test } from 'node:test'
import assert from 'node:assert/strict'
import { bankGrounds, groundCover, segmentsCross, wetShare, seatLevel, settlePrisms, spansWater, type Prism } from '../src/scene.ts'
import type { Vec2 } from '../src/geom.ts'
import { buildingHeights } from '../src/classify.ts'

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

test("a model's footprint on water is left out; a mapped boathouse stays", async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1, sources: { buildings: ['osm', 'microsoft'] } } as const
  const ll = lonLatFromLocal(region as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  const water = { type: 'polygon' as const, id: 'w1', tags: { natural: 'water' }, outers: [sq(-150, -150, 300)], inners: [] }
  const boathouse = { type: 'polygon' as const, id: 'w2', tags: { building: 'boathouse' }, outers: [sq(-50, -50, 10)], inners: [] }
  const scene = buildScene(region as never, [water, boathouse], palette('paper'), null, { footprints: [{ ring: sq(40, 40, 10) }, { ring: sq(160, -20, 10) }] })
  const ids = scene.items.map((i) => i.id).sort()
  assert.deepEqual(ids, ['m1', 'w2'])
  assert.equal(scene.stats.footprintsOnWater, 1)
})

test("a cutaway's lift takes a neighbor's OSM building away whole; others stay", async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const base = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 } as const
  const ll = lonLatFromLocal(base as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  const house = (id: string, x: number) => ({ type: 'polygon' as const, id, tags: { building: 'house' }, outers: [sq(x, 50, 10)], inners: [] })
  const region = { ...base, cutaway: { through: ll(0, 0), bearing: 0, remove: 'right', parts: 'none-', lift: ['^w2$'] } }
  const scene = buildScene(region as never, [house('w1', -60), house('w2', 60)], palette('paper'), null)
  assert.deepEqual(scene.items.map((i) => i.id).filter((id) => id.startsWith('w')), ['w1'])
  assert.equal(scene.stats.liftedBuildings, 1)
})

test('a building traced from an old map whose middle is on water mapped today is left out', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 } as const
  const ll = lonLatFromLocal(region as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  const water = { type: 'polygon' as const, id: 'w1', tags: { natural: 'water' }, outers: [sq(-150, -150, 300)], inners: [] }
  const traced = (id: string, x: number, y: number) => ({ id, ring: sq(x, y, 12), from: 1905, to: 1960, end: 'assumed' as const, material: 'brick' as const, storeys: 3 })
  const history = { epochs: [], features: [], rules: [], present: 2026, dates: [], traced: [traced('wet', 0, 0), traced('dry', 170, 170)] }
  const scene = buildScene(region as never, [water], palette('paper'), null, { time: { year: 1925, history: history as never, dates: new Map() } })
  assert.deepEqual(scene.items.map((i) => i.id).filter((id) => id.startsWith('traced:')), ['traced:dry'])
  assert.equal(scene.stats.tracedOnWater, 1)
})

test('a curated lost road bridge is drawn as a bridge in its years, and a streetcar line along it rides its deck', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 } as const
  const ll = lonLatFromLocal(region as never)
  const line = [ll(-150, 0) as Vec2, ll(150, 0) as Vec2]
  const bridge = { id: 'old', name: 'Old Bridge', kind: 'bridge', from: 1878, to: 1972, line }
  const car = { id: 'car', name: 'A line', kind: 'streetcar', from: 1890, to: 1934, line }
  const history = { epochs: [], features: [bridge, car], rules: [], present: 2026, dates: [], traced: [] }
  const at = (year: number) => buildScene(region as never, [], palette('paper'), null, { time: { year, history: history as never, dates: new Map() } })
  const deck = (s: ReturnType<typeof at>) => s.items.filter((i) => i.id.startsWith('history:old.') && !i.id.includes('pier'))
  const s1925 = at(1925)
  assert.ok(deck(s1925).length > 0)
  // The deck carries the line, in the line's color.
  assert.ok(deck(s1925).some((i) => i.shapes.some((sh) => sh.fill === palette('paper').tram)))
  assert.equal(deck(at(1980)).length, 0)
})

test('a building over water counts its height from the banks', () => {
  const outer = square(0, 0, 20)
  const canal = (p: Vec2) => p[0] > 5 && p[0] < 15
  const wetAll = () => true
  assert.equal(spansWater({ layer: '1' }, outer, canal), true)
  assert.equal(spansWater({}, outer, canal), false)
  assert.equal(spansWater({ layer: '-1' }, outer, canal), false)
  assert.equal(spansWater({ layer: 'federal' }, outer, canal), false)
  assert.equal(spansWater({ layer: '1' }, outer, () => false), false)
  const pts: Vec2[] = [[0, 0], [10, 0], [20, 0], [20, 20], [10, 20], [0, 20]]
  assert.deepEqual(bankGrounds(pts, [9, 1, 8, 8, 1, 9], canal), [9, 8, 8, 9])
  // A boathouse wholly on the water keeps every corner.
  assert.deepEqual(bankGrounds(pts, [1, 1, 1, 1, 1, 1], wetAll), [1, 1, 1, 1, 1, 1])
})

test('a tagged height far over its floors is a mistag, when the map checks levels', () => {
  const hues = { building: 'apartments', 'building:levels': '6', height: '80' }
  assert.equal(buildingHeights(hues, 2000).top, 80)
  assert.equal(buildingHeights(hues, 2000, true).source, 'levels')
  assert.ok(Math.abs(buildingHeights(hues, 2000, true).top - 21.2) < 0.01)
  // Five and a half meters a floor still stands, and a church keeps its tall tagged height.
  assert.equal(buildingHeights({ building: 'office', 'building:levels': '4', height: '22' }, 900, true).top, 22)
  assert.equal(buildingHeights({ building: 'church', 'building:levels': '1', height: '40' }, 900, true).top, 40)
  assert.equal(buildingHeights({ building: 'apartments', 'building:levels': 'many', height: '80' }, 900, true).top, 80)
})

test('the share of a footprint on water', () => {
  const half = (p: Vec2) => p[0] < 10
  assert.ok(Math.abs(wetShare(square(0, 0, 20), half) - 0.5) < 0.05)
  assert.equal(wetShare(square(0, 0, 20), () => false), 0)
  assert.equal(wetShare(square(0, 0, 20), () => true), 1)
})

test('segments cross only through each other, not at a shared end', () => {
  assert.equal(segmentsCross([0, 0], [2, 2], [0, 2], [2, 0]), true)
  assert.equal(segmentsCross([0, 0], [1, 1], [1, 1], [2, 0]), false)
  assert.equal(segmentsCross([0, 0], [1, 0], [0, 1], [1, 1]), false)
})

test('a nature reserve wholly in the sea is not drawn as ground; one on the shore stays', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 } as const
  const ll = lonLatFromLocal(region as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  // Coastline running west along y = 0, land on its left (south), sea to the north.
  const coast = { type: 'line' as const, id: 'c1', tags: { natural: 'coastline' }, points: [ll(400, 0) as Vec2, ll(-400, 0) as Vec2] }
  const marine = { type: 'polygon' as const, id: 'r1', tags: { leisure: 'nature_reserve' }, outers: [sq(-50, 60, 40)], inners: [] }
  const shore = { type: 'polygon' as const, id: 'r2', tags: { leisure: 'nature_reserve' }, outers: [sq(60, -30, 60)], inners: [] }
  const park = { type: 'polygon' as const, id: 'p1', tags: { leisure: 'park' }, outers: [sq(-150, 60, 40)], inners: [] }
  // A marine reserve running out past the frame's far edge is cut there, and still dropped.
  const past = { type: 'polygon' as const, id: 'r3', tags: { leisure: 'nature_reserve' }, outers: [sq(100, 150, 200)], inners: [] }
  const scene = buildScene(region as never, [coast, marine, shore, park, past], palette('paper'), null)
  const greens = scene.ground.filter((g) => g.kind === 'green')
  assert.equal(greens.length, 2)
  assert.ok(scene.ground.some((g) => g.kind === 'water'))
})

test('a traced footprint covered half or more by a building of the year is left out (tracedCovered), and only where the region asks', async () => {
  const { buildScene, coveredShare } = await import('../src/scene.ts')
  const { palette } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  // The share: half a square under another, a hole not counted.
  const a = square(0, 0, 10)
  assert.ok(Math.abs(coveredShare(a, [{ outer: square(5, 0, 10) }]) - 0.5) < 0.02)
  assert.ok(Math.abs(coveredShare(a, [{ outer: square(0, 0, 20), inners: [square(0, 0, 10)] }])) < 0.02)
  assert.equal(coveredShare(a, [{ outer: square(50, 50, 10) }]), 0)
  const region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 } as const
  const ll = lonLatFromLocal(region as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  const house = { type: 'polygon' as const, id: 'w9', tags: { building: 'yes' }, outers: [sq(0, 0, 20)], inners: [] }
  const traced = (id: string, x: number, y: number) => ({ id, ring: sq(x, y, 12), from: 1905, to: 1990, end: 'assumed' as const, material: 'brick' as const, storeys: 3 })
  // `under` is wholly under the house, `edge` about a third under it, `apart` clear of it.
  const history = { epochs: [], features: [], rules: [], present: 2026, dates: [], traced: [traced('under', 0, 0), traced('edge', 16, 0), traced('apart', 100, 100)] }
  const dates = new Map([['w9', { year: 1950, source: 'parcel' as const }]])
  const ids = (r: object) => buildScene(r as never, [house], palette('paper'), null, { time: { year: 1960, history: history as never, dates } })
  const off = ids(region)
  assert.deepEqual(off.items.map((i) => i.id).filter((id) => id.startsWith('traced:')).sort(), ['traced:apart', 'traced:edge', 'traced:under'])
  assert.equal(off.stats.tracedCovered, undefined)
  const on = ids({ ...region, tracedCovered: 0.5 })
  assert.deepEqual(on.items.map((i) => i.id).filter((id) => id.startsWith('traced:')).sort(), ['traced:apart', 'traced:edge'])
  assert.equal(on.stats.tracedCovered, 1)
  assert.deepEqual(on.tracedLeftOut?.filter((x) => x.why === 'covered').map((x) => x.id), ['under'])
})

test('in a flood, a traced building stands in the water as today\'s do: walls from the surface, an x-ray band, counted', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette, withFloodStyles } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const { parseFlood } = await import('../src/flood.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1, terrain: { cell: 5 }, floods: { f: { level: 5 } } } as const
  const ll = lonLatFromLocal(region as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  const water = { type: 'polygon' as const, id: 'w1', tags: { natural: 'water' }, outers: [sq(-190, -190, 60)], inners: [] }
  const house = { type: 'polygon' as const, id: 'w9', tags: { building: 'yes' }, outers: [sq(60, 60, 20)], inners: [] }
  const traced = { id: 'old', ring: sq(0, 0, 12), from: 1905, to: 1990, end: 'assumed' as const, material: 'brick' as const, storeys: 3 }
  const history = { epochs: [], features: [], rules: [], present: 2026, dates: [], traced: [traced] }
  const dates = new Map([['w9', { year: 1950, source: 'parcel' as const }]])
  const pal = withFloodStyles(palette('paper'), ['blue-grey', 'xray-heavy'])
  const scene = buildScene(region as never, [water, house], pal, () => 2, { time: { year: 1960, history: history as never, dates }, flood: parseFlood(region as never, 'f') })
  const old = scene.items.find((i) => i.id === 'traced:old')!
  assert.ok(old !== undefined && old.under !== undefined, 'the traced building has its x-ray band')
  assert.ok(old.zMin > scene.terrain.z(old.footprint![0]) + 2.9, 'its walls start at the water, 3 m over the ground')
  assert.equal(scene.stats.floodShown, 2)
  assert.equal(scene.stats.floodShownInWater, 2)
  assert.equal(scene.stats.floodBuildingsInWater, 1, "today's buildings alone, as before")
})

test('in a flood, a bridge pier standing in the water gets an x-ray band; dry, none', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette, withFloodStyles } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const { parseFlood } = await import('../src/flood.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1, terrain: { cell: 5 }, floods: { f: { level: 3.5 }, dry: { level: -20 } } } as const
  const ll = lonLatFromLocal(region as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  const water = { type: 'polygon' as const, id: 'w1', tags: { natural: 'water' }, outers: [sq(-190, -190, 60)], inners: [] }
  const road = { type: 'line' as const, id: 'w2', tags: { highway: 'primary', bridge: 'yes', layer: '1' }, points: [ll(-150, 0) as Vec2, ll(150, 0) as Vec2] }
  const pal = withFloodStyles(palette('paper'), ['blue-grey', 'xray-heavy'])
  const piers = (flood: string) => buildScene(region as never, [water, road], pal, () => 2, { flood: parseFlood(region as never, flood) }).items.filter((i) => i.pier === true)
  const wet = piers('f')
  assert.ok(wet.length > 0)
  assert.ok(wet.every((p) => p.under !== undefined && p.under.shapes.length > 0))
  assert.ok(piers('dry').every((p) => p.under === undefined))
})

test('in a flood, a deck piece below the water is drawn under it (faint, on the surface); above it, as before', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette, withFloodStyles } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const { parseFlood } = await import('../src/flood.ts')
  const region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1, terrain: { cell: 5 }, floods: { low: { level: 3.5 }, high: { level: 20 } } } as const
  const ll = lonLatFromLocal(region as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  const water = { type: 'polygon' as const, id: 'w1', tags: { natural: 'water' }, outers: [sq(-190, -190, 60)], inners: [] }
  const road = { type: 'line' as const, id: 'w2', tags: { highway: 'primary', bridge: 'yes', layer: '1' }, points: [ll(-150, 0) as Vec2, ll(150, 0) as Vec2] }
  const pal = withFloodStyles(palette('paper'), ['blue-grey', 'xray-heavy'])
  const decks = (flood: string) => {
    const sc = buildScene(region as never, [water, road], pal, () => 2, { flood: parseFlood(region as never, flood) })
    return { all: sc.items.filter((i) => i.span !== undefined && i.pier !== true), under: sc.stats.floodDeckSpansAwash }
  }
  const low = decks('low'), high = decks('high')
  assert.ok(low.all.some((i) => !i.id.endsWith('.under')), 'decks above a low flood are drawn as decks')
  assert.ok(high.all.length > 0 && high.all.every((i) => i.id.endsWith('.under')), 'every deck under a high flood is drawn under it')
  assert.ok(high.all.every((i) => i.shapes.length === 1 && i.shapes[0].seal === true))
  assert.equal(high.under, high.all.length)
})

test('ground the walls hold only because a levee is missing is drawn as unknown, out of the flood and its counts', async () => {
  const { buildScene } = await import('../src/scene.ts')
  const { palette, withFloodStyles } = await import('../src/palette.ts')
  const { lonLatFromLocal } = await import('../src/region.ts')
  const { parseFlood } = await import('../src/flood.ts')
  const base = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1, terrain: { cell: 5 } } as const
  const ll = lonLatFromLocal(base as never)
  const sq = (x: number, y: number, s: number): Vec2[] => square(x, y, s).map(([e, n]) => ll(e, n) as Vec2)
  // The river along the west edge; a wall from the south edge partway north at x = -100, so the
  // water goes round its north end; the "levee" line closes that course.
  const water = { type: 'polygon' as const, id: 'w1', tags: { natural: 'water' }, outers: [sq(-200, -200, 60)], inners: [] }
  const wall = [ll(-100, -210) as Vec2, ll(-100, 50) as Vec2]
  const levee = [ll(-100, 50) as Vec2, ll(-100, 210) as Vec2]
  const region = { ...base, floodwalls: [{ name: 'wall', line: wall, top: 50 }],
    floods: { open: { level: 5, walls: true }, held: { level: 5, walls: true, unknown: { lines: [levee] } } } }
  const pal = withFloodStyles(palette('paper'), ['blue-grey'])
  const sc = (f: string) => buildScene(region as never, [water], pal, () => 2, { flood: parseFlood(region as never, f) })
  const open = sc('open'), held = sc('held')
  assert.ok((open.stats.floodAcres ?? 0) > 20, 'without the line the water goes round the wall')
  assert.ok(held.flood?.unknown !== undefined)
  assert.ok((held.stats.floodUnknownAcres ?? 0) > 20, 'the ground behind is counted as not known')
  assert.ok((held.stats.floodAcres ?? 0) < (open.stats.floodAcres ?? 0) - 20, 'and taken out of the flooded acres')
  assert.equal(open.flood?.unknown, undefined)
})
