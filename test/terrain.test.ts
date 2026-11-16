import { test } from 'node:test'
import assert from 'node:assert/strict'
import { contours, makeTerrain, rasterize, riverFall, settleWater } from '../src/terrain.ts'
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
  assert.ok(fall.slope > 0.035, `slope ${fall.slope}`)
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
