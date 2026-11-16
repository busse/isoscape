import assert from 'node:assert/strict'
import { test } from 'node:test'
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { alive, dateBuildings, dropUnbuiltStreets, featureAlive, loadYearBuilt, parseYear, yearBuiltDirs, type History, type Parcel } from '../src/history.ts'
import type { LineFeature, PolygonFeature } from '../src/osm.ts'
import { asOf } from '../src/scene.ts'

const square = (x: number, y: number, s: number) => [[x, y], [x + s, y], [x + s, y + s], [x, y + s]] as [number, number][]
const building = (id: string, x: number, y: number, s = 0.0001, tags: Record<string, string> = {}): PolygonFeature =>
  ({ type: 'polygon', id, tags: { building: 'yes', ...tags }, outers: [square(x, y, s)], inners: [] })
const road = (id: string, tags: Record<string, string>): LineFeature => ({ type: 'line', id, tags: { highway: 'residential', ...tags }, points: [[0, 0], [1, 1]] })

const history = (over: Partial<History> = {}): History => ({ epochs: [], features: [], rules: [], present: 2026, dates: [], traced: [], ...over })

test('years from OSM dates', () => {
  assert.equal(parseYear('1885'), 1885)
  assert.equal(parseYear('1885-04-01'), 1885)
  assert.equal(parseYear('c. 1890'), 1890)
  assert.equal(parseYear('1890s'), 1890)
  assert.equal(parseYear('~1850'), 1850)
  assert.equal(parseYear('yes'), null)
  assert.equal(parseYear(undefined), null)
})

test('spans are half open', () => {
  assert.ok(alive(1800, 1885, 1800))
  assert.ok(!alive(1800, 1885, 1885))
  assert.ok(alive(null, null, 1700))
})

test('the first matching rule decides; no rule means always; an empty era list means today only', () => {
  const h = history({
    rules: [
      { where: { name: 'Expressway' }, eras: [[1976, null]] },
      { where: { tag: 'highway', is: ['motorway'] }, eras: [[1958, null]] },
      { where: { tag: 'highway', is: ['footway'] }, eras: [] },
      { where: { tag: 'railway', bridge: true }, eras: [[1901, null]] },
    ],
  })
  const expressway = road('a', { highway: 'motorway', name: 'Downtown Expressway' })
  assert.ok(!featureAlive(expressway, 1960, h))
  assert.ok(featureAlive(expressway, 1976, h))
  assert.ok(featureAlive(road('b', { highway: 'motorway' }), 1960, h))
  assert.ok(featureAlive(road('c', {}), 1740, h))
  assert.ok(!featureAlive(road('d', { highway: 'footway' }), 1990, h))
  assert.ok(featureAlive(road('d', { highway: 'footway' }), 2026, h))
  const viaduct: LineFeature = { type: 'line', id: 'e', tags: { railway: 'rail', bridge: 'yes' }, points: [] }
  const atGrade: LineFeature = { type: 'line', id: 'f', tags: { railway: 'rail' }, points: [] }
  assert.ok(!featureAlive(viaduct, 1900, h))
  assert.ok(featureAlive(atGrade, 1900, h))
})

test('dating: curated, then OSM, then the parcel, which a crowd does not share', () => {
  const parcels: Parcel[] = [
    { ring: square(0, 0, 0.001), year: 1890 }, // one building
    { ring: square(0.01, 0, 0.001), year: 1785 }, // a campus of eight
    { ring: square(0.02, 0, 0.001), year: 1737 }, // holds a curated building
  ]
  const campus = Array.from({ length: 8 }, (_, k) => building(`c${k}`, 0.0101 + k * 0.0001, 0.0002, 0.00005))
  const d = dateBuildings(
    [building('a', 0.0002, 0.0002), building('b', 0.0004, 0.0004, 0.0001, { start_date: '1910' }), ...campus,
      building('s', 0.0202, 0.0002), building('t', 0.0205, 0.0005)],
    parcels,
    [{ id: 's', year: 1754, source: 'x' }],
  )
  assert.deepEqual(d.get('a'), { year: 1890, source: 'parcel' })
  assert.deepEqual(d.get('b'), { year: 1910, source: 'osm' })
  assert.equal(d.get('c0'), undefined)
  assert.deepEqual(d.get('s'), { year: 1754, source: 'curated' })
  assert.equal(d.get('t'), undefined)
})

test('as of a year: dated buildings from their year, undated ones only today', () => {
  const dates = new Map([['old', { year: 1850, source: 'parcel' as const }]])
  const fs = [building('old', 0, 0), building('new', 0, 0)]
  const ids = (y: number) => asOf(fs, { year: y, history: history(), dates }).map((f) => f.id)
  assert.deepEqual(ids(1840), [])
  assert.deepEqual(ids(1860), ['old'])
  assert.deepEqual(ids(2026), ['old', 'new'])
})

test('year built is read from the region\'s own data folder first, then the shared one; missing is an error', async () => {
  assert.deepEqual(yearBuiltDirs({ name: 'time', data: 'shared' }, 'd'), [join('d', 'time'), join('d', 'shared')])
  assert.deepEqual(yearBuiltDirs({ name: 'solo' }, 'd'), [join('d', 'solo')])
  const root = await mkdtemp(join(tmpdir(), 'isoscape-yb-'))
  const fc = (y: number) => JSON.stringify({ features: [{ geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]] }, properties: { Y: y } }] })
  await mkdir(join(root, 'shared'))
  await writeFile(join(root, 'shared', 'yearbuilt.json'), fc(1900))
  // Only the shared folder has it (a view that borrows another's parcels).
  let got = await loadYearBuilt(yearBuiltDirs({ name: 'time', data: 'shared' }, root), 'Y', 'time')
  assert.equal(got.parcels[0].year, 1900)
  // The region's own folder wins (a series that borrows OSM but keeps its own parcels).
  await mkdir(join(root, 'time'))
  await writeFile(join(root, 'time', 'yearbuilt.json'), fc(1850))
  got = await loadYearBuilt(yearBuiltDirs({ name: 'time', data: 'shared' }, root), 'Y', 'time')
  assert.equal(got.parcels[0].year, 1850)
  await assert.rejects(loadYearBuilt(yearBuiltDirs({ name: 'none', data: 'nowhere' }, root), 'Y', 'none'), /no year-built data/)
})

test('streets before the houses: a plan vouches for its grid; main roads only when asked', () => {
  const street = (id: string, highway: string, x: number, extra: Record<string, string> = {}): LineFeature =>
    ({ type: 'line', id, tags: { highway, ...extra }, points: [[x, 0], [x, 0.001]] })
  const house = building('h', 0.01, 0.0005, 0.00005)
  const feats = [
    house,
    street('near', 'residential', 0.01),          // beside the house
    street('far', 'residential', 0.02),           // no house within 60 m
    street('planned', 'residential', 0.03),       // inside the plan
    street('planned-aisle', 'service', 0.0301, { service: 'parking_aisle' }), // a plan lays out no aisles
    street('main', 'primary', 0.04),              // a main road with no house
  ]
  const plan: [number, number][] = [[0.029, -0.001], [0.032, -0.001], [0.032, 0.002], [0.029, 0.002]]
  const ids = (r: { kept: readonly { id: string }[] }) => r.kept.map((f) => f.id).sort()
  assert.deepEqual(ids(dropUnbuiltStreets(feats, 60)), ['h', 'main', 'near'])
  assert.deepEqual(ids(dropUnbuiltStreets(feats, 60, [], [plan])), ['h', 'main', 'near', 'planned'])
  assert.deepEqual(ids(dropUnbuiltStreets(feats, 60, [], [plan], true)), ['h', 'near', 'planned'])
  // A curated or traced building counts as a house.
  assert.deepEqual(ids(dropUnbuiltStreets(feats, 60, [[0.02, 0.0005]])), ['far', 'h', 'main', 'near'])
})

test('a dated series: what no rule dates is drawn today only, except the street grid and natural water', async () => {
  const { loadHistory } = await import('../src/history.ts')
  const h = await loadHistory('history/richmond-downtown.json')
  const line = (tags: Record<string, string>): LineFeature => ({ type: 'line', id: 'x', tags, points: [[0, 0], [1, 1]] })
  const area = (tags: Record<string, string>): PolygonFeature => ({ type: 'polygon', id: 'y', tags, outers: [square(0, 0, 1)], inners: [] })
  for (const [f, early, why] of [
    [line({ highway: 'residential' }), true, 'a street'],
    [line({ highway: 'service', service: 'parking_aisle' }), false, 'a parking aisle'],
    [line({ highway: 'primary_link' }), false, 'an interchange ramp'],
    [line({ highway: 'construction' }), false, 'a road being built'],
    [line({ waterway: 'stream' }), true, 'a stream'],
    [line({ waterway: 'dam' }), false, 'an undated dam'],
    [line({ man_made: 'pier' }), false, 'a pier'],
    [area({ leisure: 'park' }), false, 'an undated park'],
    [area({ landuse: 'cemetery' }), false, 'an undated cemetery'],
    [area({ natural: 'water', water: 'river' }), true, 'the river'],
    [area({ natural: 'wood' }), true, 'woods'],
    [line({ highway: 'primary', name: 'Mayo Bridge', bridge: 'yes' }), false, 'the 1913 Mayo Bridge in 1900'],
  ] as const) assert.equal(featureAlive(f, 1900, h), early, why)
  assert.ok(featureAlive(line({ highway: 'primary', name: 'Mayo Bridge', bridge: 'yes' }), 1913, h))
  assert.ok(featureAlive(area({ leisure: 'park' }), 2026, h))
})
