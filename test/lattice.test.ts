import assert from 'node:assert/strict'
import { test } from 'node:test'
import { signedArea, type Vec2 } from '../src/geom.ts'
import { palette } from '../src/palette.ts'
import type { Region } from '../src/region.ts'
import { LATTICE_SIMPLIFY, latticeFootprint, spire } from '../src/scene.ts'
import { makeView } from '../src/view.ts'

const region: Region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 }
const view = makeView(region, 0)
const pal = palette('paper')
const square: Vec2[] = [[-50, -50], [50, -50], [50, 50], [-50, 50]]

test('a lattice footprint drops the short jogs that would run up the tower as slivers', () => {
  // A 100 m square with a 1.5 m notch in its near side, as where a leg meets an arch.
  const notched: Vec2[] = [[-50, -50], [0, -50], [0, -48.5], [1.5, -48.5], [1.5, -50], [50, -50], [50, 50], [-50, 50]]
  const ring = latticeFootprint(notched, 100 * 100)
  assert.ok(LATTICE_SIMPLIFY * 100 > 1.5)
  assert.equal(ring.length, 4)
  assert.ok(signedArea(ring) > 0)
  // A plain square keeps its corners.
  assert.deepEqual(latticeFootprint(square, 100 * 100), square)
})

test('a spire puts dots only at the feet of the walls that face the camera', () => {
  const it = spire(view, pal, 't', square, 0, 300, 'all')
  // No loose dots painted over the whole item: a hidden corner would show through the faces.
  assert.equal(it.dots.length, 0)
  const dots = it.shapes.flatMap((s) => s.dots ?? [])
  // Only the near wall (y = −50) faces this camera, so only its two corners get dots.
  assert.equal(dots.length, 2)
  const near = [view.toScreen([-50, -50], 0), view.toScreen([50, -50], 0)]
  for (const d of dots) assert.ok(near.some((p) => Math.hypot(p[0] - d[0], p[1] - d[1]) < 1e-9))
})
