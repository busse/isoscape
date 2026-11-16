import { test } from 'node:test'
import assert from 'node:assert/strict'
import { makeTerrain, rasterize, settleWater, shoreField, traceShore } from '../src/terrain.ts'
import { coverFields, COVER_BLUR } from '../src/landcover.ts'
import { makeView } from '../src/view.ts'
import { palette } from '../src/palette.ts'
import type { Region } from '../src/region.ts'
import type { Vec2 } from '../src/geom.ts'

const region: Region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 }
const view = makeView(region, 0)

/** Water east of the line e = 40 + 0.3 n: a shore slanting across the grid. */
const slant = (n: number) => 40 + 0.3 * n
const water: Vec2[][] = [[[slant(-300), -300], [400, -300], [400, 300], [slant(300), 300]]]

test('the shoreline follows the mapped outline between grid nodes, not the grid', () => {
  const t = makeTerrain(view, 5, 1, () => 10)
  rasterize(t, [water], 1)
  const f = shoreField(t, [water], [])
  // Along every grid row the field crosses one half where the outline does, to a few cm.
  let rows = 0
  for (let j = 10; j < t.ny - 10; j++) {
    const n = t.y0 + j * t.cell
    for (let i = 0; i + 1 < t.nx; i++) {
      const a = f[j * t.nx + i]
      const b = f[j * t.nx + i + 1]
      if ((a >= 0.5) === (b >= 0.5)) continue
      const e = t.x0 + (i + (0.5 - a) / (b - a)) * t.cell
      assert.ok(Math.abs(e - slant(n)) < 0.05, `row ${j}: ${e.toFixed(2)} vs ${slant(n).toFixed(2)}`)
      rows++
    }
  }
  assert.ok(rows > 50)
})

test('the drawn ground lies on the water at the shoreline and is the ground a cell inland', () => {
  // A bank rising 1 m in 5 westward from the water at 2 m.
  const t = makeTerrain(view, 5, 1, (lon, lat) => {
    const e = lon * 111_320
    const n = lat * 110_574
    return Math.max(2, 2 + (slant(n) - e) / 5)
  })
  rasterize(t, [water], 1)
  settleWater(t, 30, 1.0, false)
  traceShore(t, [water], [])
  // On grid rows, where the shoreline is traced from the field along the cells' sides.
  for (const n of [-50, -15, 5, 35].map((v) => t.y0 + Math.round((v - t.y0) / t.cell) * t.cell)) {
    const onLine: Vec2 = [slant(n), n]
    assert.ok(Math.abs(t.z(onLine) - t.waterZ(onLine)) < 1e-6, 'on the line, the water')
    const inland: Vec2 = [slant(n) - 2 * t.cell, n]
    assert.ok(Math.abs(t.z(inland) - (t.elevation(inland) - t.datum)) < 1e-6, 'two cells inland, the ground')
  }
})

test('mapped water the lidar finds well above the river stays land, traced as the grid has it', () => {
  // The outline reaches 10 m up a bluff; the bluff is 6 m above the river there.
  const t = makeTerrain(view, 5, 1, (lon) => (lon * 111_320 < 30 ? 8 : 2))
  const wide: Vec2[][] = [[[20, -300], [400, -300], [400, 300], [20, 300]]]
  rasterize(t, [wide], 1)
  settleWater(t, 30, 1.0, false)
  traceShore(t, [wide], [])
  const k = (e: number, n: number) => Math.round((n - t.y0) / t.cell) * t.nx + Math.round((e - t.x0) / t.cell)
  assert.ok(t.shore[k(25, 0)] < 0.5, 'the bluff inside the outline stays land')
  assert.ok(t.shore[k(40, 0)] >= 0.5, 'the river beyond it is water')
})

test('land cover is blurred over 30 m cells into smooth patches that meet without gaps', () => {
  // 30 m cells in a diagonal staircase: forest (41) below the diagonal, field (71) above it.
  const nx = 60
  const ny = 60
  const cell = 5
  const cover = new Uint8Array(nx * ny)
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) cover[j * nx + i] = Math.floor(i / 6) > Math.floor(j / 6) ? 41 : 71
  const fields = coverFields(cover, nx, ny, cell, () => false)
  const forest = fields.get('forest')!
  const field = fields.get('field')!
  let worst = 0
  for (let j = 15; j < 45; j++) {
    for (let i = 15; i + 1 < 45; i++) {
      const a = forest[j * nx + i]
      const b = forest[j * nx + i + 1]
      if ((a >= 0.5) === (b >= 0.5)) continue
      // The two groups' boundaries are the same line.
      const u = (0.5 - a) / (b - a)
      const v = (0.5 - field[j * nx + i]) / (field[j * nx + i + 1] - field[j * nx + i])
      assert.ok(Math.abs(u - v) < 1e-3)
      // And it runs close to the staircase's diagonal (offset by half a step, 15 m).
      const x = (i + u) * cell
      const y = j * cell
      worst = Math.max(worst, Math.abs((x - y - 15) / Math.SQRT2))
    }
  }
  assert.ok(worst < 2, `${worst.toFixed(2)} m from the diagonal at most (blur ${COVER_BLUR} m)`)
})

test('render: a stream a node wide cuts no water into the front of the slab', async () => {
  const { renderSvg } = await import('../src/render.ts')
  const { buildScene } = await import('../src/scene.ts')
  const { parseOsm } = await import('../src/osm.ts')
  const strip = (x: number, w: number) => [{ lat: -0.002, lon: x }, { lat: -0.002, lon: x + w }, { lat: 0.002, lon: x + w }, { lat: 0.002, lon: x }, { lat: -0.002, lon: x }]
  const build = (w: number) => {
    const json = JSON.stringify({ elements: [{ type: 'way', id: 1, tags: { natural: 'water' }, geometry: strip(0, w) }] })
    const scene = buildScene({ ...region, snap: false, width: 200, depth: 200, terrain: { cell: 5 } }, parseOsm(json), palette('paper'), () => 10)
    return renderSvg(scene).svg
  }
  const slabWater = `fill="${palette('paper').slabWater}"`
  assert.ok(!build(4 / 111_320).includes(slabWater), 'a 4 m stream')
  assert.ok(build(40 / 111_320).includes(slabWater), 'a 40 m river')
})
