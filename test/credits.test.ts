import { test } from 'node:test'
import assert from 'node:assert/strict'
import { CREDIT_MICROSOFT, CREDIT_NLCD, CREDIT_OSM, CREDIT_SANBORN, CREDIT_YEAR_BUILT, sceneCredits } from '../src/credits.ts'
import type { Region } from '../src/region.ts'

const region = (extra: Partial<Region> = {}): Region => ({ name: 't', title: 't', center: [0, 0], width: 100, depth: 100, bearing: 0, scale: 1, ...extra })

test('a flat scene credits OpenStreetMap alone', () => {
  assert.deepEqual(sceneCredits(region(), {}, true), [CREDIT_OSM])
})

test('relief credits its elevation source by name, and its fill source', () => {
  assert.deepEqual(sceneCredits(region({ terrain: {} }), {}, false), [CREDIT_OSM, 'Elevation: USGS 3DEP'])
  const c = sceneCredits(region({ terrain: { source: 'ign', fillFrom: 'copernicus' } }), {}, false)
  assert.equal(c[1].startsWith('Elevation: RGE ALTI® © IGN; produced using Copernicus'), true)
})

test('a modern scene with no traced buildings never credits Sanborn maps', () => {
  const c = sceneCredits(region({ terrain: {} }), { traced: 0, buildings: 3782, datedFromParcels: 0 }, false)
  assert.ok(!c.includes(CREDIT_SANBORN))
  assert.ok(!c.includes(CREDIT_YEAR_BUILT))
})

test('each other source is credited when, and only when, the scene drew from it', () => {
  const all = sceneCredits(region({ terrain: {} }), { coverNodes: 5, footprintsDrawn: 2, datedFromParcels: 1, traced: 4 }, false)
  assert.deepEqual(all, [CREDIT_OSM, 'Elevation: USGS 3DEP', CREDIT_NLCD, CREDIT_MICROSOFT, CREDIT_YEAR_BUILT, CREDIT_SANBORN])
  // Footprints loaded but none drawn (all under OSM buildings or on water): no credit.
  assert.ok(!sceneCredits(region(), { footprintsAdded: 10, footprintsDrawn: 0 }, true).includes(CREDIT_MICROSOFT))
  // A year-built source can name itself.
  const named = region({ time: { history: 'h.json', yearBuilt: { url: 'u', field: 'f', credit: 'Buildings dated from Somewhere assessor records' } } })
  assert.ok(sceneCredits(named, { datedFromParcels: 3 }, true).includes('Buildings dated from Somewhere assessor records'))
})
