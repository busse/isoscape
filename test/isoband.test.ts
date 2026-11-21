import { test } from 'node:test'
import assert from 'node:assert/strict'
import { isoBand, type BandPoint } from '../src/isoband.ts'
import { makeTerrain, nodeShade } from '../src/terrain.ts'
import { makeView } from '../src/view.ts'
import { shadeAlphas, simplify, steepShade } from '../src/render.ts'
import type { Region } from '../src/region.ts'

const area = (ring: readonly BandPoint[]) => {
  let a = 0
  for (let k = 0; k < ring.length; k++) {
    const p = ring[k]
    const q = ring[(k + 1) % ring.length]
    a += p.i * q.j - q.i * p.j
  }
  return a / 2
}

test('a single peak makes one counter-clockwise ring, edges interpolated', () => {
  const f = [0, 0, 0, 0, 2, 0, 0, 0, 0]
  const rings = isoBand(f, 3, 0, 2, 0, 2, 1)
  assert.equal(rings.length, 1)
  const r = rings[0]
  assert.ok(area(r) > 0)
  // The band's edge crosses each side from the peak halfway: a diamond of area 0.5.
  assert.ok(Math.abs(area(r) - 0.5) < 1e-9)
  for (const p of r) assert.ok(Math.abs(Math.abs(p.i - 1) + Math.abs(p.j - 1) - 0.5) < 1e-9)
})

test('a block wholly in the band is one rectangle, its row edges marked', () => {
  const nx = 5
  const f = new Array(nx * 3).fill(5)
  const rings = isoBand(f, nx, 0, 4, 0, 2, 1)
  assert.equal(rings.length, 1)
  assert.equal(area(rings[0]), 8)
  for (const p of rings[0]) assert.equal(p.onRow, p.j === 0 || p.j === 2)
})

test('a ring of high ground around a low center leaves a clockwise hole', () => {
  const f = [
    2, 2, 2, 2,
    2, 0, 0, 2,
    2, 0, 0, 2,
    2, 2, 2, 2,
  ]
  const rings = isoBand(f, 4, 0, 3, 0, 3, 1)
  assert.equal(rings.length, 2)
  const areas = rings.map(area).sort((a, b) => a - b)
  assert.ok(areas[0] < 0 && areas[1] > 0)
  // The hole runs halfway out to the high nodes: a square of side 2 with corners cut.
  assert.ok(Math.abs(areas[1] - 9) < 1e-9)
})

test('a saddle closes its rings', () => {
  const f = [2, 0, 0, 2]
  const rings = isoBand(f, 2, 0, 1, 0, 1, 1)
  assert.ok(rings.length >= 1)
  const total = rings.reduce((s, r) => s + area(r), 0)
  assert.ok(total > 0 && total < 1)
})

test('two blocks meeting on a row line find the same points along it', () => {
  const nx = 6
  const f: number[] = []
  for (let j = 0; j < 5; j++) for (let i = 0; i < nx; i++) f.push(Math.sin(i * 1.3 + j * 0.7) * 2)
  const far = isoBand(f, nx, 0, 5, 2, 4, 0.3).flat().filter((p) => p.onRow && p.j === 2)
  const near = isoBand(f, nx, 0, 5, 0, 2, 0.3).flat().filter((p) => p.onRow && p.j === 2)
  const key = (p: BandPoint) => p.i.toFixed(12)
  assert.deepEqual([...new Set(far.map(key))].sort(), [...new Set(near.map(key))].sort())
  // The two blocks together cover what one block over both covers.
  const sum = (rs: BandPoint[][]) => rs.reduce((s, r) => s + area(r), 0)
  const whole = sum(isoBand(f, nx, 0, 5, 0, 4, 0.3))
  assert.ok(Math.abs(sum(isoBand(f, nx, 0, 5, 0, 2, 0.3)) + sum(isoBand(f, nx, 0, 5, 2, 4, 0.3)) - whole) < 1e-9)
})

test('nested shade bands add up to the wash a single band of that step would give', () => {
  const alphas = shadeAlphas(0.045, 0.55)
  let through = 1
  alphas.forEach((a, k) => {
    through *= 1 - a
    assert.ok(Math.abs(1 - through - Math.min(0.55, (0.045 * (k + 1)) / (alphas.length / 12))) < 1e-9)
  })
})

test('steep shade: unchanged under the knee, then darker ever more slowly, never past the clamp', () => {
  for (const v of [0, 0.7, -2, 3.5, -4.9, 5, -5]) assert.equal(steepShade(v), v)
  // Symmetric, monotonic, continuous at the knee, and well short of the 12-step clamp.
  assert.equal(steepShade(-17), -steepShade(17))
  let last = steepShade(5)
  for (let v = 5.01; v < 60; v += 0.01) {
    const s = steepShade(v)
    assert.ok(s > last && s - last <= 0.01 + 1e-12)
    last = s
  }
  assert.ok(Math.abs(steepShade(5.001) - 5.001) < 1e-5)
  assert.ok(steepShade(17) > 8.5 && steepShade(17) < 9.5)
  assert.ok(steepShade(60) < 12)
})

test('the shade field is zero on flat ground and positive on a slope facing the light', () => {
  const region: Region = { name: 't', title: 't', center: [0, 0], width: 200, depth: 200, bearing: 0, scale: 1 }
  const view = makeView(region, 0)
  const light: [number, number, number] = [-0.6, 0, 0.8]
  const flat = nodeShade(makeTerrain(view, 5, 1, () => 10), light)
  assert.ok(flat.every((v) => Math.abs(v) < 1e-6))
  // Ground rising eastward faces west, toward a light from the west.
  const t = makeTerrain(view, 5, 1, (lon) => lon * 111_320 * 0.2)
  const s = nodeShade(t, light)
  const mid = Math.floor(t.ny / 2) * t.nx + Math.floor(t.nx / 2)
  assert.ok(s[mid] > 0.05)
})

test('a simplified draped edge stays within its tolerance of every point, even on a long gentle curve', () => {
  // A row edge 6000 units long that sags 10 units: every three neighbors are nearly in line,
  // so a test of each point against its neighbors alone kept almost nothing.
  const pts: [number, number][] = []
  for (let k = 0; k <= 1000; k++) {
    const x = -3000 + 6 * k
    pts.push([x, 10 * (1 - (x / 3000) ** 2)])
  }
  const out = simplify(pts, 0.25)
  assert.ok(out.length < pts.length / 4, `kept ${out.length}`)
  let worst = 0
  for (const [x, y] of pts) {
    const s = out.findIndex((q, i) => i + 1 < out.length && q[0] <= x && out[i + 1][0] >= x)
    const [a, b] = [out[s], out[s + 1]]
    const yy = a[1] + ((x - a[0]) / (b[0] - a[0] || 1)) * (b[1] - a[1])
    worst = Math.max(worst, Math.abs(yy - y))
  }
  assert.ok(worst <= 0.26, `off by ${worst}`)
})

test('rapids clumps: a smooth field from 0.4 to 1.6 that averages about 1', async () => {
  const { rapidsClumps } = await import('../src/render.ts')
  let sum = 0
  let n = 0
  let jump = 0
  for (let j = 0; j < 80; j++) {
    for (let i = 0; i < 80; i++) {
      const v = rapidsClumps(i, j)
      assert.ok(v >= 0.4 - 1e-9 && v <= 1.6 + 1e-9)
      sum += v
      n++
      if (i > 0) jump = Math.max(jump, Math.abs(v - rapidsClumps(i - 1, j)))
    }
  }
  assert.ok(Math.abs(sum / n - 1) < 0.1, `mean ${sum / n}`)
  // Smooth: neighbors never differ by more than about half the range.
  assert.ok(jump < 0.6, `jump ${jump}`)
})
