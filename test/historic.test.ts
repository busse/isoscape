import assert from 'node:assert/strict'
import { test } from 'node:test'
import { bridgeFeature, dropUnbuiltStreets, featureHistoric, switchedOn, type History, type HistoryFeature } from '../src/history.ts'
import type { LineFeature, PolygonFeature } from '../src/osm.ts'
import { historicWater, HISTORIC_BANK, makeTerrain } from '../src/terrain.ts'
import { makeView } from '../src/view.ts'
import type { Region } from '../src/region.ts'
import type { Vec2 } from '../src/geom.ts'

const line = (id: string, tags: Record<string, string>, points: [number, number][]): LineFeature => ({ type: 'line', id, tags, points })
const history = (over: Partial<History> = {}): History => ({ epochs: [], features: [], rules: [], present: 2026, dates: [], traced: [], ...over })

test('water drawn for a span that ends before today is historic; today\'s is not', () => {
  const h = history({ rules: [
    { where: { name: 'Old Canal' }, eras: [[1800, 1890], [1999, null]] },
    { where: { name: 'Mill Race' }, eras: [[1790, null]] },
  ] })
  const canal: PolygonFeature = { type: 'polygon', id: 'c', tags: { natural: 'water', name: 'Old Canal' }, outers: [[[0, 0], [1, 0], [1, 1]]], inners: [] }
  const race: PolygonFeature = { ...canal, id: 'r', tags: { natural: 'water', name: 'Mill Race' } }
  assert.equal(featureHistoric(canal, 1865, h), true)
  assert.equal(featureHistoric(canal, 2026, h), false)
  assert.equal(featureHistoric(race, 1865, h), false)
})

test('historic water lies level at its own height with a smooth bank, whatever today\'s ground does', () => {
  const region: Region = { name: 't', title: 't', center: [0, 0], width: 400, depth: 400, bearing: 0, scale: 1 }
  const view = makeView(region, 0)
  // Ground climbing 1 m in 5 northward: a filled basin on a hillside.
  const t = makeTerrain(view, 5, 1, (_lon, lat) => 20 + (lat * 110_574) / 5)
  const basin: Vec2[] = [[-50, -30], [50, -30], [50, 30], [-50, 30]]
  historicWater(t, [[basin]])
  const at = (x: number, y: number) => {
    const i = Math.round((x - t.x0) / t.cell), j = Math.round((y - t.y0) / t.cell)
    return { e: t.elev[j * t.nx + i], w: t.water[j * t.nx + i] }
  }
  const level = at(0, 0).e
  assert.equal(at(0, 0).w, 1)
  assert.equal(at(-45, 25).e, level)
  // The bank stands HISTORIC_BANK above the water at the edge on both sides, and the ground
  // eases back to today's beyond: no cliff.
  assert.ok(Math.abs(at(0, 35).e - (level + HISTORIC_BANK)) < 1.5, `uphill bank ${at(0, 35).e} vs ${level}`)
  assert.ok(Math.abs(at(0, -35).e - (level + HISTORIC_BANK)) < 1.5, `downhill bank ${at(0, -35).e} vs ${level}`)
  for (let y = 30; y < 60; y += 5) assert.ok(Math.abs(at(0, y + 5).e - at(0, y).e) <= 5, `step at ${y}`)
  assert.ok(Math.abs(at(0, 80).e - (20 + 80 / 5)) < 0.01, 'today\'s ground beyond the band')
})

test('a curated bridge is a bridge way of its own, switched on by name when it says so', () => {
  const b: HistoryFeature = { id: 'fb', name: 'Free Bridge', kind: 'bridge', from: 1873, to: 1972, deck: 8, highway: 'tertiary', switch: 'free-bridge', line: [[0, 0], [0, 0.01]], note: '', sources: [] }
  const f = bridgeFeature(b)
  assert.ok(f !== null && f.type === 'line')
  assert.equal(f.tags.bridge, 'yes')
  assert.equal(f.tags.highway, 'tertiary')
  assert.equal(f.tags['isoscape:deck'], '8')
  assert.equal(f.tags['isoscape:seat'], 'ground')
  const h = history({ features: [b] })
  assert.equal(switchedOn(h, []).features.length, 0)
  assert.equal(switchedOn(h, ['free-bridge']).features.length, 1)
  assert.equal(switchedOn(history(), []).features.length, 0)
})

test('a switch\'s settings apply only in builds that name it, and names add up', () => {
  const h = history({ switches: { next: { vergeReach: 60 }, next2: { bridgesClearTraced: true } } })
  assert.equal(switchedOn(h, []).bridgesClearTraced, undefined)
  assert.equal(switchedOn(h, ['next']).bridgesClearTraced, undefined)
  assert.equal(switchedOn(h, ['next']).vergeReach, 60)
  const both = switchedOn(h, ['next', 'next2'])
  assert.equal(both.bridgesClearTraced, true)
  assert.equal(both.vergeReach, 60)
})

test('a street that meets a road bridge stands with it: the road across an island between two spans', () => {
  const north = line('n', { highway: 'primary', bridge: 'yes' }, [[0, 0], [0, 0.002]])
  const island = line('i', { highway: 'primary' }, [[0, 0.002], [0, 0.004]])
  const south = line('s', { highway: 'primary', bridge: 'yes' }, [[0, 0.004], [0, 0.006]])
  const far = line('f', { highway: 'primary' }, [[0.05, 0], [0.05, 0.002]])
  const kept = dropUnbuiltStreets([north, island, south, far], 60, [], [], true).kept.map((f) => f.id)
  assert.deepEqual(kept, ['n', 'i', 's'])
})

test('with follow, the street a bridge leads onto is kept by name as far as it runs', () => {
  const span = line('b', { highway: 'primary', bridge: 'yes' }, [[0, 0], [0, 0.002]])
  const a = line('a', { highway: 'primary', name: 'Hull Street' }, [[0, 0.002], [0, 0.004]])
  const b = line('b2', { highway: 'primary', name: 'Hull Street' }, [[0, 0.004], [0, 0.03]])
  const other = line('o', { highway: 'primary', name: 'Cowardin Avenue' }, [[0, 0.004], [0.03, 0.004]])
  assert.deepEqual(dropUnbuiltStreets([span, a, b, other], 60, [], [], true).kept.map((f) => f.id), ['b', 'a'])
  assert.deepEqual(dropUnbuiltStreets([span, a, b, other], 60, [], [], true, true).kept.map((f) => f.id), ['b', 'a', 'b2'])
})
