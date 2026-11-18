import { test } from 'node:test'
import assert from 'node:assert/strict'
import { makeTerrain, restoreGround, type HeightGrid } from '../src/terrain.ts'
import { makeView } from '../src/view.ts'
import type { Region } from '../src/region.ts'
import type { Vec2 } from '../src/geom.ts'

/** A plain grid: x and y in meters, cell 5, origin at (0, 0). */
const grid = (nx: number, ny: number, f: (x: number, y: number) => number): HeightGrid => {
  const elev = new Float32Array(nx * ny)
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) elev[j * nx + i] = f(i * 5, j * 5)
  return { elev, nx, ny, x0: 0, y0: 0, cell: 5 }
}
const at = (g: HeightGrid, x: number, y: number) => g.elev[Math.round(y / 5) * g.nx + Math.round(x / 5)]
const box = (x0: number, y0: number, x1: number, y1: number): Vec2[] => [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]

test('a trench across a plain is filled back to the plain', () => {
  // A 50 m plain, with a trench 8 m deep and 60 m wide running east-west through it.
  const g = grid(61, 61, (x, y) => (x > 10 && x < 290 && y > 120 && y < 180 ? 42 : 50))
  const n = restoreGround(g, [box(-10, 110, 310, 190)])
  assert.ok(n > 0)
  assert.ok(Math.abs(at(g, 150, 150) - 50) < 0.01, `rebuilt ${at(g, 150, 150)}`)
})

test('a membrane carries a slope across the gap, and leaves the ground outside alone', () => {
  // Ground rising 1 m per 10 m northward, cut 6 m in a band.
  const g = grid(61, 61, (x, y) => 30 + y / 10 - (x > 10 && x < 290 && y > 120 && y < 180 ? 6 : 0))
  const before = at(g, 150, 100)
  restoreGround(g, [box(-10, 110, 310, 190)])
  assert.ok(Math.abs(at(g, 150, 150) - 45) < 0.05, `rebuilt ${at(g, 150, 150)}`)
  assert.equal(at(g, 150, 100), before)
})

test('a street through the gap runs at a straight grade between its ends', () => {
  // Rim: 40 m south of the band, 50 m north of it, but a street along x = 150 is held to a
  // straight grade between its own ends, and the nodes beside it follow it.
  const g = grid(61, 61, (x, y) => (y <= 110 ? 40 + x / 30 : y >= 190 ? 50 + x / 30 : 0))
  restoreGround(g, [box(-10, 112, 310, 188)], [{ pts: [[150, 60], [150, 240]] }])
  const z = (y: number) => at(g, 150, y)
  // Measured ends: 45 at y = 110 and 55 at y = 190 (x = 150), straight between them.
  assert.ok(Math.abs(z(150) - 50) < 0.15, `mid ${z(150)}`)
  assert.ok(Math.abs(z(130) - 47.5) < 0.2, `quarter ${z(130)}`)
})

test('a line with a known elevation holds it', () => {
  const g = grid(41, 41, () => 20)
  restoreGround(g, [box(40, 40, 160, 160)], [{ pts: [[50, 100], [150, 100]], elevation: 26 }])
  assert.ok(Math.abs(at(g, 100, 100) - 26) < 1e-6)
  assert.ok(at(g, 100, 120) > 20 && at(g, 100, 120) < 26)
})

test('a terrain built with a restoration rebuilds inside it, and without one is unchanged', () => {
  const region: Region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 }
  const view = makeView(region, 0)
  // A plain at 50 m with a trench 8 m deep and 80 m wide across the middle of the frame.
  const sample = (lon: number, lat: number) => (Math.abs(lat * 110_574) < 40 && Math.abs(lon * 111_320) < 150 ? 42 : 50)
  const plain = makeTerrain(view, 5, 1, sample)
  const restored = makeTerrain(view, 5, 1, sample, (g) => { restoreGround(g, [[[-180, -60], [180, -60], [180, 60], [-180, 60]]]) })
  const again = makeTerrain(view, 5, 1, sample)
  assert.deepEqual(again.elev, plain.elev)
  assert.ok(plain.elevation([0, 0]) < 43)
  assert.ok(Math.abs(restored.elevation([0, 0]) - 50) < 0.05)
  // The frame's lowest point was the trench's floor; rebuilt, it is the plain.
  assert.ok(Math.abs(restored.datum - 50) < 0.05)
})
