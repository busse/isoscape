import assert from 'node:assert/strict'
import { test } from 'node:test'
import { alive, dateBuildings, featureAlive, parseYear, type History, type Parcel } from '../src/history.ts'
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
