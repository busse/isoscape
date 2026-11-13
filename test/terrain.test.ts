import { test } from 'node:test'
import assert from 'node:assert/strict'
import { contours, makeTerrain, rasterize, riverFall, settleWater } from '../src/terrain.ts'
import { makeView } from '../src/view.ts'
import { encodeDem, decodeDem, sampler } from '../src/dem.ts'
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
  assert.ok(fall.slope > 0.05, `slope ${fall.slope}`)
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
