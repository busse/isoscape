import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { loadHistory, switchedOn } from '../src/history.ts'

const polygons = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { name: 'paved' }, geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]] } },
    { type: 'Feature', properties: { name: 'corridor' }, geometry: { type: 'MultiPolygon', coordinates: [[[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]], [[0.5, 0.5], [0.6, 0.5], [0.6, 0.6], [0.5, 0.5]]], [[[5, 5], [6, 5], [6, 6], [5, 5]]]] } },
  ],
}

test('a highlight is off unless its switch is named, and its polygons are read from its file', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'isoscape-highlight-'))
  await writeFile(join(dir, 'fp.geojson'), JSON.stringify(polygons))
  await writeFile(join(dir, 'h.json'), JSON.stringify({
    epochs: [], features: [], rules: [], present: 2026,
    switches: { count: { highlight: { file: join(dir, 'fp.geojson'), polygons: ['paved', 'corridor'], quiet: true } } },
  }))
  const h = await loadHistory(join(dir, 'h.json'))
  assert.equal(switchedOn(h, []).highlight, undefined)
  assert.equal(switchedOn(h, ['other']).highlight, undefined)
  const on = switchedOn(h, ['count']).highlight
  assert.ok(on !== undefined)
  assert.equal(on.quiet, true)
  // One ring for the paved polygon; the corridor's outer, its hole and its second part.
  assert.deepEqual(on.rings?.map((rs) => rs.length), [1, 3])
  assert.deepEqual(on.rings?.[0][0], [[0, 0], [1, 0], [1, 1], [0, 1]])
})

test('a highlight naming a polygon its file lacks fails to load', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'isoscape-highlight-'))
  await writeFile(join(dir, 'fp.geojson'), JSON.stringify(polygons))
  await writeFile(join(dir, 'h.json'), JSON.stringify({
    epochs: [], features: [], rules: [], present: 2026,
    switches: { count: { highlight: { file: join(dir, 'fp.geojson'), polygons: ['right-of-way'] } } },
  }))
  await assert.rejects(loadHistory(join(dir, 'h.json')), /no polygon named "right-of-way"/)
})

test('a highlight with an ids file reads the counted ids in polygon order', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'isoscape-highlight-'))
  await writeFile(join(dir, 'fp.geojson'), JSON.stringify(polygons))
  await writeFile(join(dir, 'ids.json'), JSON.stringify({ corridor: ['b'], paved: ['a', 'c'] }))
  await writeFile(join(dir, 'h.json'), JSON.stringify({
    epochs: [], features: [], rules: [], present: 2026,
    switches: { count: { highlight: { file: join(dir, 'fp.geojson'), polygons: ['paved', 'corridor'], ids: join(dir, 'ids.json') } } },
  }))
  const on = switchedOn(await loadHistory(join(dir, 'h.json')), ['count']).highlight
  assert.deepEqual(on?.picked, [['a', 'c'], ['b']])
})
