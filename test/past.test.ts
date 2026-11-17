import assert from 'node:assert/strict'
import { test } from 'node:test'
import { dateBuildings, dropUnbuiltStreets, featureAlive, pastGround, type History, type Parcel } from '../src/history.ts'
import type { LineFeature, PolygonFeature } from '../src/osm.ts'
import { extrude, lineNearRing, ringSamples } from '../src/scene.ts'
import { makeView } from '../src/view.ts'
import { palette } from '../src/palette.ts'

const square = (x: number, y: number, s: number) => [[x, y], [x + s, y], [x + s, y + s], [x, y + s]] as [number, number][]
const building = (id: string, x: number, y: number, s = 0.0001, tags: Record<string, string> = {}): PolygonFeature =>
  ({ type: 'polygon', id, tags: { building: 'yes', ...tags }, outers: [square(x, y, s)], inners: [] })
const line = (id: string, tags: Record<string, string>, points: [number, number][]): LineFeature => ({ type: 'line', id, tags, points })
const history = (over: Partial<History> = {}): History => ({ epochs: [], features: [], rules: [], present: 2026, dates: [], traced: [], ...over })

test('a bridge is never dropped for want of houses: it crosses where none can stand', () => {
  const bridge = line('b', { highway: 'primary', bridge: 'yes' }, [[0, 0], [0, 0.002]])
  const street = line('s', { highway: 'primary' }, [[0.01, 0], [0.01, 0.002]])
  const kept = dropUnbuiltStreets([bridge, street], 60, [], [], true).kept.map((f) => f.id)
  assert.deepEqual(kept, ['b'])
})

test('a part takes its building\'s curated year; an unknown year leaves a building to today; parking waits for its decks', () => {
  const parcels: Parcel[] = [{ ring: square(0, 0, 0.001), year: 1900 }, { ring: square(0.01, 0, 0.001), year: 1925 }]
  const tower = building('tower', 0.0001, 0.0001, 0.0005)
  const part = building('part', 0.0002, 0.0002, 0.0001, { 'building:part': 'yes' })
  delete (part.tags as Record<string, string>).building
  const deck = building('deck', 0.0101, 0.0001, 0.0005, { amenity: 'parking', parking: 'multi-storey' })
  const unknown = building('unknown', 0.0201, 0.0001)
  const d = dateBuildings([tower, part, deck, unknown], parcels, [
    { id: 'tower', year: 1929, source: 'https://example.org' },
    { id: 'unknown', year: null, source: 'https://example.org' },
  ], 4, 8, 1960)
  assert.deepEqual(d.get('part'), { year: 1929, source: 'curated' })
  assert.deepEqual(d.get('deck'), { year: 1960, source: 'parcel' })
  assert.equal(d.get('unknown'), undefined)
})

test('a rule can ask that a tag be absent', () => {
  const h = history({ rules: [{ where: { tag: 'highway', is: ['service'], without: ['service', 'name'] }, eras: [[1960, null]] }] })
  assert.ok(!featureAlive(line('a', { highway: 'service' }, [[0, 0], [1, 1]]), 1925, h))
  assert.ok(featureAlive(line('b', { highway: 'service', service: 'alley' }, [[0, 0], [1, 1]]), 1925, h))
})

test('a past year: canal bridges wait, decks that do not meet a road at both ends go, plantings come with their buildings, spurs need a building', () => {
  const canal = line('canal', { waterway: 'canal' }, [[0, 0], [0.002, 0]])
  const over = line('over', { highway: 'residential', bridge: 'yes' }, [[0.001, -0.0002], [0.001, 0.0002]])
  const approach = line('appr', { highway: 'residential' }, [[0.001, 0.0002], [0.001, 0.001]])
  const south = line('south', { highway: 'residential' }, [[0.001, -0.001], [0.001, -0.0002]])
  const lone = line('lone', { highway: 'unclassified', bridge: 'yes' }, [[0.005, 0], [0.005, 0.0001]])
  const landed = line('landed', { highway: 'primary', bridge: 'yes' }, [[0.007, 0], [0.007, 0.0005]])
  const street = line('street', { highway: 'primary' }, [[0.007, 0.0005], [0.007, 0.001]])
  const across = line('across', { highway: 'primary' }, [[0.007, -0.0005], [0.007, 0]])
  const into = line('into', { highway: 'unclassified', bridge: 'yes' }, [[0.009, 0], [0.009, 0.0002]])
  const tunnel = line('tunnel', { highway: 'unclassified', tunnel: 'yes' }, [[0.009, 0.0002], [0.009, 0.0005]])
  const lead = line('lead', { highway: 'unclassified' }, [[0.009, -0.0003], [0.009, 0]])
  const tower = building('tower', 0.003, 0.003, 0.0002)
  const bed: PolygonFeature = { type: 'polygon', id: 'bed', tags: { natural: 'scrub' }, outers: [square(0.0032, 0.0028, 0.0001)], inners: [] }
  const spur = line('spur', { railway: 'rail', service: 'spur' }, [[0.02, 0], [0.02, 0.001]])
  const main = line('main', { railway: 'rail' }, [[0.019, 0], [0.02, 0], [0.021, 0]])
  const all = [canal, over, approach, south, lone, landed, street, across, into, tunnel, lead, tower, bed, spur, main]
  const h = history({ canalBridgesFrom: 1999 })
  const dates = new Map([['tower', { year: 1990 }]])
  const r = pastGround(all, all, 1925, h, dates)
  const ids = r.kept.map((f) => f.id)
  assert.ok(!ids.includes('over') && !ids.includes('lone') && !ids.includes('into') && !ids.includes('bed') && !ids.includes('spur'))
  assert.ok(ids.includes('landed') && ids.includes('main'))
  assert.deepEqual([r.canalBridges, r.orphanBridges, r.plantings, r.spurs], [1, 2, 1, 1])
  // In 2000 the canal bridge stands and the bed with its tower; a building at its end serves the spur.
  const later = pastGround(all, all, 2000, h, dates, 2000, 40, [[0.02, 0.001]]).kept.map((f) => f.id)
  assert.ok(later.includes('over') && later.includes('bed') && later.includes('spur'))
})

test('a footprint is read all over for water, and a line near it is found', () => {
  const ring: [number, number][] = [[0, 0], [10, 0], [10, 10], [0, 10]]
  const pts = ringSamples(ring, 1)
  assert.ok(pts.length > 100)
  // A sliver of water 1.5 m deep along one edge is found.
  assert.ok(pts.some((p) => p[1] < 1.5))
  assert.ok(lineNearRing([[-20, 12], [20, 12]], ring, 2.5))
  assert.ok(!lineNearRing([[-20, 13], [20, 13]], ring, 2.5))
  assert.ok(lineNearRing([[5, 5], [6, 6]], ring, 0))
})

test('a wall whose corners both stand above the lowest one stops level at the ground in front of it', () => {
  const view = makeView({ name: 't', title: 't', center: [0, 0], width: 100, depth: 100, bearing: 0, scale: 1, squash: 0.5 } as never, 0)
  const ring: [number, number][] = [[0, 0], [10, 0], [10, 10], [0, 10]]
  const plain = extrude(view, palette('paper'), 'a', ring, [], 0, 10, palette('paper').fresh, 'none')
  const seated = extrude(view, palette('paper'), 'b', ring, [], 0, 10, palette('paper').fresh, 'none', undefined, [3, 4, 0, 0])
  // The front wall (0,0)→(10,0) faces the camera: its foot rises to 3, the lower of its corners.
  const front = (it: typeof plain) => it.shapes[it.shapes.length - 2].pts
  assert.notDeepEqual(front(plain), front(seated))
  const ys = (it: typeof plain) => it.shapes.flatMap((s) => s.pts.map((p) => p[1]))
  assert.ok(Math.max(...ys(seated)) < Math.max(...ys(plain)))
})
