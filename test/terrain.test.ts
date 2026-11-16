import { test } from 'node:test'
import assert from 'node:assert/strict'
import { contours, makeTerrain, RAPIDS, rasterize, riverFall, settleWater } from '../src/terrain.ts'
import { waterFlows } from '../src/classify.ts'
import { palette } from '../src/palette.ts'
import { makeView } from '../src/view.ts'
import { alignServed, encodeDem, decodeDem, misaligned, sampler } from '../src/dem.ts'
import { servedBox } from '../src/dem-sources.ts'
import type { Region } from '../src/region.ts'

const region: Region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 }
const view = makeView(region, 0)
const M = 111_320

test('the view inverts: fromView(toView(p)) is p', () => {
  const v = makeView(region, 23)
  const [lon, lat] = v.fromView(v.toView(0.001, -0.0007))
  assert.ok(Math.abs(lon - 0.001) < 1e-9 && Math.abs(lat + 0.0007) < 1e-9)
})

test('a slope samples to a terrain with the right scene z and datum', () => {
  // Elevation rises 1 m per 10 m northward.
  const t = makeTerrain(view, 5, 2, (_lon, lat) => 50 + (lat * 110_574) / 10)
  assert.ok(Math.abs(t.elevation([0, 100]) - t.elevation([0, 0]) - 10) < 0.5)
  assert.ok(Math.abs(t.z([0, 100]) - t.z([0, 0]) - 20) < 1)
  assert.ok(t.z([0, -200]) >= 0)
})

test('contours run across a slope at the interval', () => {
  const t = makeTerrain(view, 5, 1, (_lon, lat) => (lat * 110_574) / 10)
  const segs = contours(t, 2, 5)
  assert.ok(segs.length > 100)
  // Contours of a north-rising slope run east–west.
  const s = segs[0]
  assert.ok(Math.abs(s.b[1] - s.a[1]) < 1e-6)
})

test('water is found under the rocks, and the drop reads as rapids', () => {
  // A river channel falling 3 m over 20 m in the middle, with a rock standing 3 m proud.
  const t = makeTerrain(view, 5, 1, (lon, lat) => {
    const e = lon * M
    const n = lat * 110_574
    const water = e < 0 ? 10 : e > 20 ? 7 : 10 - (3 * e) / 20
    const rock = Math.hypot(e + 100, n) < 6 ? 3 : 0
    return water + rock
  })
  const channel = [[[-250, -30], [250, -30], [250, 30], [-250, 30]] as [number, number][]]
  rasterize(t, [channel], 1)
  settleWater(t)
  let rocks = 0
  for (const v of t.rocks) rocks += v
  assert.ok(rocks > 0, 'the rock is marked')
  const i = Math.round((10 - t.x0) / t.cell)
  const j = Math.round((0 - t.y0) / t.cell)
  const fall = riverFall(t, i, j)!
  assert.ok(fall.slope > 2 * RAPIDS, `slope ${fall.slope}`)
  assert.ok(fall.down[0] > 0.9, 'falls eastward')
  const calm = riverFall(t, Math.round((-180 - t.x0) / t.cell), j)
  assert.ok(calm === null || calm.slope < 0.01)
})

test('elevation round-trips through the compact store', () => {
  const data = new Float32Array([10, 10.5, NaN, 12.25])
  const dem = decodeDem(encodeDem({ west: 0, south: 0, east: 1, north: 1, width: 2, height: 2, data }))
  assert.ok(Math.abs(dem.data[1] - 10.5) < 0.006)
  assert.ok(Number.isNaN(dem.data[2]))
  assert.ok(Math.abs(sampler(dem)(0.75, 0.25) - 12.25) < 0.01)
})

// A 3DEP-style server: pixels square in degrees, so it covers servedBox(asked) about the center.
const serve = (asked: { west: number; south: number; east: number; north: number }, w: number, h: number, ground: (lon: number, lat: number) => number) => {
  const sv = servedBox(asked, w, h)
  const data = new Float32Array(w * h)
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) data[y * w + x] = ground(sv.west + ((x + 0.5) / w) * (sv.east - sv.west), sv.north - ((y + 0.5) / h) * (sv.north - sv.south))
  return data
}

test('a box sized in meters is widened north-south about its center to square pixels', () => {
  const b = { west: 0, east: 0.02, south: 40, north: 40.02 }
  const sv = servedBox(b, 200, 300)
  assert.ok(Math.abs((sv.east - sv.west) / 200 - (sv.north - sv.south) / 300) < 1e-12)
  assert.equal(sv.west, 0)
  assert.ok(Math.abs((sv.north + sv.south) / 2 - 40.01) < 1e-12)
  assert.ok(sv.north - sv.south > 0.02)
})

test('an old 3DEP grid, one image or rows of tiles, is put back where the ground is', () => {
  // A ridge running east-west at latitude 40.01: wherever the grid says it is, it should be.
  const ground = (_lon: number, lat: number) => 100 * Math.exp(-(((lat - 40.022) / 0.002) ** 2)) + (lat - 40) * 3000
  const b = { west: 0, east: 0.02, south: 40, north: 40.03 }
  const peakLat = (d: { data: Float32Array; width: number; height: number; north: number; south: number }) => {
    let best = -Infinity
    let at = 0
    for (let y = 0; y < d.height; y++) if (d.data[y * d.width + 5] > best) { best = d.data[y * d.width + 5]; at = y }
    return d.north - ((at + 0.5) / d.height) * (d.north - d.south)
  }
  // One image.
  const one = { ...b, width: 40, height: 90, data: serve(b, 40, 90, ground) }
  assert.ok(misaligned(one))
  assert.ok(Math.abs(peakLat(one) - 40.022) > 0.001, 'served as is, the ridge is off')
  const fixedOne = alignServed(one, 1000)
  assert.ok(Math.abs(peakLat(fixedOne) - 40.022) < 0.0004)
  assert.equal(misaligned(fixedOne), false)
  // Rows of 50-pixel tiles: each served on its own widened box, so a step shows at row 50.
  const w = 40
  const h = 90
  const data = new Float32Array(w * h)
  for (const [y0, th] of [[0, 50], [50, 40]]) {
    const box = { ...b, north: b.north - (y0 / h) * 0.03, south: b.north - ((y0 + th) / h) * 0.03 }
    data.set(serve(box, w, th, ground), y0 * w)
  }
  const tiled = alignServed({ ...b, width: w, height: h, data }, 50)
  assert.ok(Math.abs(peakLat(tiled) - 40.022) < 0.0004)
  const step = Math.abs(tiled.data[50 * w + 5] - tiled.data[49 * w + 5])
  const next = Math.abs(tiled.data[52 * w + 5] - tiled.data[51 * w + 5])
  assert.ok(step < 3 * next + 0.5, `no step where the tiles meet (${step} vs ${next})`)
  // Other sources were cut to the box, and new files say they are aligned.
  assert.equal(misaligned({ ...one, source: 'ign' }), false)
  assert.equal(misaligned(decodeDem(encodeDem(fixedOne, '3dep'))), false)
})

test('no rock and no rapid is read where the source has no heights', () => {
  // A bay the lidar did not cover: heights only on the shore, and a steep bank on one side.
  // Filled in from the shore, the bay's "surface" slopes and humps; none of it is rock or falls.
  const t = makeTerrain(view, 5, 1, (lon, lat) => {
    const e = lon * M
    const n = lat * 110_574
    if (Math.abs(n) < 120 && Math.abs(e) < 160) return NaN
    return n > 0 ? 40 + n / 5 : 0.5
  })
  rasterize(t, [[[[-160, -120], [160, -120], [160, 120], [-160, 120]]]], 1)
  settleWater(t)
  let rocks = 0
  for (const v of t.rocks) rocks += v
  assert.equal(rocks, 0)
  for (let j = 0; j < t.ny; j++) for (let i = 0; i < t.nx; i++) assert.equal(riverFall(t, i, j), null)
})

test('a stepped, hydro-flattened river reads its fall along the reach, not only at the steps', () => {
  // Level reaches stepping down 0.5 m every 100 m eastward (5 m per km), as 3DEP draws a river;
  // then, east of 0, a calm reach falling 1 m per km. A long, straight channel.
  const wide = makeView({ ...region, width: 1200, depth: 200 }, 0)
  const t = makeTerrain(wide, 5, 1, (lon) => {
    const e = lon * M
    return e < 0 ? 20 - 0.5 * Math.floor((e + 600) / 100) : 17 - e / 1000
  })
  rasterize(t, [[[[-600, -40], [600, -40], [600, 40], [-600, 40]]]], 1)
  settleWater(t)
  const j = Math.round((0 - t.y0) / t.cell)
  const at = (e: number) => riverFall(t, Math.round((e - t.x0) / t.cell), j)
  // Midway between two steps the water is level, yet it is in a reach that falls 5 m per km.
  for (const e of [-450, -350, -250]) {
    const f = at(e)
    assert.ok(f !== null && f.slope > RAPIDS && f.slope < 0.008, `${e}: ${f?.slope}`)
    assert.ok(f.down[0] > 0.9, 'runs east')
  }
  for (const e of [250, 350]) {
    const f = at(e)
    assert.ok(f === null || f.slope < RAPIDS / 2, `${e}: ${f?.slope}`)
  }
})

test('only a river gets rocks and rapids: not a basin, a lake or the ground drawn over it', async () => {
  assert.equal(waterFlows({ natural: 'water', water: 'river' }), true)
  assert.equal(waterFlows({ waterway: 'riverbank' }), true)
  assert.equal(waterFlows({ natural: 'water', water: 'wastewater', landuse: 'basin' }), false)
  assert.equal(waterFlows({ natural: 'water', water: 'basin' }), false)
  assert.equal(waterFlows({ natural: 'water', water: 'lake' }), false)
  assert.equal(waterFlows({ natural: 'water', amenity: 'fountain' }), false)
  assert.equal(waterFlows({ natural: 'water' }), undefined)
  const { buildScene } = await import('../src/scene.ts')
  const { renderSvg } = await import('../src/render.ts')
  const { parseOsm } = await import('../src/osm.ts')
  const box = (w: number, s: number, e: number, n: number) =>
    [[w, s], [e, s], [e, n], [w, n], [w, s]].map(([x, y]) => ({ lon: x / M, lat: y / 110_574 }))
  // A river falling 3 m over 40 m eastward at the middle with a rock in it (north half), and a
  // treatment basin that tilts and has a rock in it (south half).
  const ground = (lon: number, lat: number) => {
    const e = lon * M
    const n = lat * 110_574
    const rock = Math.hypot(e + 100, n - 60) < 7 || Math.hypot(e + 100, n + 80) < 7 ? 3 : 0
    if (n > 0) return (e < 0 ? 10 : e > 40 ? 7 : 10 - (3 * e) / 40) + rock
    return 2 + e / 50 + rock
  }
  const elements = (dry: boolean) => [
    { type: 'way', id: 1, tags: { natural: 'water', water: 'river' }, geometry: box(-190, 20, 190, 110) },
    { type: 'way', id: 2, tags: { natural: 'water', water: 'wastewater', landuse: 'basin' }, geometry: box(-190, -130, 190, -30) },
    ...(dry ? [{ type: 'way', id: 3, tags: { natural: 'bare_rock' }, geometry: box(-190, 20, 190, 110) }] : []),
  ]
  const r = { ...region, snap: false, width: 400, depth: 300, terrain: { cell: 5 } }
  const scene = buildScene(r, parseOsm(JSON.stringify({ elements: elements(false) })), palette('paper'), ground)
  const T = scene.terrain
  let riverRocks = 0
  for (let j = 0; j < T.ny; j++) {
    for (let i = 0; i < T.nx; i++) {
      const n = T.y0 + j * T.cell
      if (T.rocks[j * T.nx + i] === 1) {
        assert.ok(n > 0, 'no rock in the basin')
        riverRocks++
      }
      if (n < -20) assert.equal(riverFall(T, i, j), null, 'no rapid in the basin')
    }
  }
  assert.ok(riverRocks > 0, 'the rock in the river is marked')
  const wet = renderSvg(scene)
  assert.ok((wet.stats.rapidCells ?? 0) > 0, 'the river reads as rapids')
  assert.ok(wet.svg.includes('class="boulder"'))
  // The same river drawn as a bed of bare rock is dry ground: no rock and no rapid on it.
  const dry = renderSvg(buildScene(r, parseOsm(JSON.stringify({ elements: elements(true) })), palette('paper'), ground))
  assert.equal(dry.stats.rapidCells, 0)
  assert.ok(!dry.svg.includes('class="boulder"'))
})

test('where a hydro-flattened river steps down, the water above the step is not rock', () => {
  // Level water stepping down 2 m at e = 0, sharply, with one boulder 3 m proud upstream.
  const wide = makeView({ ...region, width: 800, depth: 200 }, 0)
  const t = makeTerrain(wide, 5, 1, (lon, lat) => {
    const e = lon * M
    const n = lat * 110_574
    return (e < 0 ? 12 : 10) + (Math.hypot(e + 200, n) < 6 ? 3 : 0)
  })
  rasterize(t, [[[[-400, -40], [400, -40], [400, 40], [-400, 40]]]], 1)
  settleWater(t)
  for (let j = 0; j < t.ny; j++) {
    for (let i = 0; i < t.nx; i++) {
      if (t.rocks[j * t.nx + i] !== 1) continue
      const e = t.x0 + i * t.cell
      const n = t.y0 + j * t.cell
      assert.ok(Math.hypot(e + 200, n) < 15, `rock at ${e}, ${n} is not the boulder`)
    }
  }
  let rocks = 0
  for (const v of t.rocks) rocks += v
  assert.ok(rocks > 0, 'the boulder is rock')
})
