import { test } from 'node:test'
import assert from 'node:assert/strict'
import { chainCoast, landFromCoast, waterFromCoast } from '../src/coast.ts'
import { signedArea, type Vec2 } from '../src/geom.ts'

const rect = { minX: 0, minY: 0, maxX: 100, maxY: 100 }
const area = (rings: Vec2[][]) => rings.reduce((a, r) => a + signedArea(r), 0)

test('a coast running east across the frame leaves land to the north', () => {
  // Traveling east, the land is on the left: north.
  const { land } = landFromCoast([[[-10, 40], [50, 45], [110, 40]]], rect)
  assert.equal(land.length, 1)
  const a = signedArea(land[0])
  assert.ok(a > 0, 'land ring is counterclockwise')
  assert.ok(Math.abs(a - 100 * 57.5) < 200, `land area ${a}`)
  const water = waterFromCoast([[[-10, 40], [50, 45], [110, 40]]], rect)!
  assert.ok(Math.abs(area(water) - (10000 - a)) < 1)
})

test('the same coast run westward puts the land to the south', () => {
  const { land } = landFromCoast([[[110, 40], [50, 45], [-10, 40]]], rect)
  assert.ok(Math.abs(signedArea(land[0]) - 100 * 42.5) < 200)
})

test('an island inside the frame is land in open water', () => {
  const island: Vec2[] = [[40, 40], [60, 40], [60, 60], [40, 60], [40, 40]]
  const water = waterFromCoast([island], rect)!
  assert.equal(Math.round(area(water)), 10000 - 400)
})

test('a peninsula entering and leaving through the same edge', () => {
  // Up from the bottom edge and back down: land on the left of travel is the peninsula.
  const coast: Vec2[] = [[60, -10], [60, 50], [40, 50], [40, -10]]
  const { land } = landFromCoast([coast], rect)
  assert.equal(land.length, 1)
  assert.ok(Math.abs(signedArea(land[0]) - 20 * 50) < 1, `${signedArea(land[0])}`)
})

test('two crossings make two pieces of land joined around the corner', () => {
  // A bay cut into the frame from the right edge: coast in from the top, out at the right.
  const coast: Vec2[] = [[80, 110], [80, 20], [110, 20]]
  const { land } = landFromCoast([coast], rect)
  // Heading south down x = 80 the land is on the left, to the east: [80, 100] × [20, 100].
  assert.ok(Math.abs(signedArea(land[0]) - 20 * 80) < 1, `${signedArea(land[0])}`)
})

test('coastline ways join end to start', () => {
  const chains = chainCoast([[[2, 0], [3, 0]], [[0, 0], [1, 0]], [[1, 0], [2, 0]]])
  assert.equal(chains.length, 1)
  assert.deepEqual(chains[0][0], [0, 0])
  assert.equal(chains[0].length, 4)
})

test('no coast at all means no water', () => {
  assert.equal(waterFromCoast([], rect), null)
})
