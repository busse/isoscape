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

test('a curated part can stand in for a building until it was enlarged, and stays in today\'s scene', () => {
  const curated = [
    { id: 'core', year: 1788, until: 1906, source: 's' },
    { id: 'whole', year: 1906, source: 's' },
  ]
  const fs = [building('core', 0, 0, 0.0001, { 'building:part': 'yes' }), building('whole', 0, 0, 0.0003)]
  const dates = dateBuildings(fs, [], curated)
  assert.equal(dates.get('core')?.until, 1906)
  const ids = (y: number) => asOf(fs, { year: y, history: history(), dates }).map((f) => f.id)
  assert.deepEqual(ids(1800), ['core'])
  assert.deepEqual(ids(1910), ['whole'])
  assert.deepEqual(ids(2026), ['core', 'whole'])
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

test('service roads can be held to a closer test than streets (serviceNearBuildings)', () => {
  const ids = (r: { kept: { id: string }[] }) => r.kept.map((f) => f.id).sort()
  // A house at the origin; a street and a yard road each about 100 m off (0.0009° of latitude).
  const line = (id: string, highway: string, y: number): LineFeature => ({ type: 'line', id, tags: { highway }, points: [[0, y], [0.0002, y]] })
  const feats = [building('h', 0, 0), line('street', 'residential', 0.0009), line('yard', 'service', 0.0009), line('drive', 'service', 0.0002)]
  // With streets kept within 60 m (cells of 60 m, so up to about 120 m), both survive.
  assert.deepEqual(ids(dropUnbuiltStreets(feats, 60)), ['drive', 'h', 'street', 'yard'])
  // Service roads within 25 m: the yard road goes, the drive by the house stays.
  assert.deepEqual(ids(dropUnbuiltStreets(feats, 60, [], [], false, 25)), ['drive', 'h', 'street'])
})

test('every curated year cites a source, and a curated height says where it comes from', async () => {
  const { loadHistory } = await import('../src/history.ts')
  const h = await loadHistory('history/richmond-downtown.json')
  const ids = new Set<string>()
  for (const d of h.dates) {
    assert.match(d.source, /^https:\/\//, d.id)
    assert.ok(!ids.has(d.id), `${d.id} is dated twice`)
    ids.add(d.id)
    if (d.height !== undefined) assert.ok(d.height > 0 && (d.note ?? '').length > 0, `${d.id}: a height needs a note`)
  }
})

test('a sheet whose fit is known to be wrong is left out', async () => {
  const { loadHistory } = await import('../src/history.ts')
  const dir = await mkdtemp(join(tmpdir(), 'iso-leave-'))
  const ring = [[0, 0], [1, 0], [1, 1], [0, 0]]
  const f = (id: string, sheet: string, edition: number) => ({ type: 'Feature', properties: { id, from: edition, to: 1960, end: 'assumed', material: 'brick', storeys: 3, edition, sheet }, geometry: { type: 'Polygon', coordinates: [ring] } })
  await writeFile(join(dir, 'lost.geojson'), JSON.stringify({ type: 'FeatureCollection', features: [f('a', '5', 1905), f('b', '6', 1905), f('c', '5', 1886)] }))
  await writeFile(join(dir, 'h.json'), JSON.stringify({ sanborn: { lost: join(dir, 'lost.geojson'), editions: [1886, 1905], source: 'x', leaveOut: [{ edition: 1905, sheet: '5', why: 'misfit' }] } }))
  const h = await loadHistory(join(dir, 'h.json'))
  assert.deepEqual(h.traced.map((b) => b.id), ['b', 'c'])
})

test('a bridge over a road not yet built is drawn at grade, and that road\'s verges are not drawn', async () => {
  const { laterWorks } = await import('../src/history.ts')
  const h = history({ rules: [{ where: { name: 'Turnpike' }, eras: [[1958, null]] }] as History['rules'] })
  const line = (id: string, tags: Record<string, string>, points: [number, number][]): LineFeature => ({ type: 'line', id, tags, points })
  const pike = line('pike', { highway: 'motorway', name: 'Turnpike' }, [[0, -0.001], [0, 0.001]])
  const span = line('span', { highway: 'primary', name: 'Broad', bridge: 'yes', layer: '1' }, [[-0.0002, 0], [0.0002, 0]])
  const side = line('side', { highway: 'primary', name: 'Broad', bridge: 'yes', layer: '1' }, [[0.0002, 0], [0.0004, 0]])
  const rail = line('rail', { railway: 'rail' }, [[0.001, -0.001], [0.001, 0.001]])
  const overRail = line('over', { highway: 'primary', name: 'Main', bridge: 'yes' }, [[0.0009, 0.0005], [0.0011, 0.0005]])
  const verge: PolygonFeature = { type: 'polygon', id: 'verge', tags: { natural: 'wood' }, outers: [[[0.00005, -0.0005], [0.0001, -0.0005], [0.0001, 0.0005], [0.00005, 0.0005]]], inners: [] }
  const woods: PolygonFeature = { type: 'polygon', id: 'woods', tags: { natural: 'wood' }, outers: [[[0.003, 0], [0.004, 0], [0.004, 0.001], [0.003, 0.001]]], inners: [] }
  const all = [pike, span, side, rail, overRail, verge, woods]
  const early = laterWorks(all, [span, side, rail, overRail, verge, woods], 1950, h)
  assert.equal(early.atGrade, 2)
  assert.deepEqual(early.kept.filter((f) => f.tags.bridge).map((f) => f.id), ['over'])
  assert.ok(early.kept.some((f) => f.id === 'span' && f.tags.layer === undefined))
  assert.deepEqual(early.kept.filter((f) => f.type === 'polygon').map((f) => f.id), ['woods'])
  const late = laterWorks(all, all, 1960, h)
  assert.equal(late.atGrade, 0)
  assert.equal(late.verges, 0)
})
