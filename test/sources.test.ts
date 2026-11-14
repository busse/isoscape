import { test } from 'node:test'
import assert from 'node:assert/strict'
import { deflateSync } from 'node:zlib'
import { decodePng } from '../src/png.ts'
import { mergeFootprints, quadkey } from '../src/footprints.ts'
import { buildingHeights } from '../src/classify.ts'
import type { PolygonFeature } from '../src/osm.ts'

const chunk = (type: string, body: Buffer) => {
  const len = Buffer.alloc(4)
  len.writeUInt32BE(body.length)
  return Buffer.concat([len, Buffer.from(type, 'latin1'), body, Buffer.alloc(4)])
}

test('a palette PNG decodes, filters and all', () => {
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(2, 0)
  ihdr.writeUInt32BE(2, 4)
  ihdr[8] = 8
  ihdr[9] = 3
  const plte = Buffer.from([255, 0, 0, 0, 0, 255])
  // Row 0 unfiltered [0, 1]; row 1 "up" filtered: [1, -1] + row above = [1, 0].
  const raw = Buffer.from([0, 0, 1, 2, 1, 255])
  const png = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', ihdr), chunk('PLTE', plte), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))])
  const img = decodePng(png)
  assert.deepEqual(img.rgb(0, 0), [255, 0, 0])
  assert.deepEqual(img.rgb(1, 0), [0, 0, 255])
  assert.deepEqual(img.rgb(0, 1), [0, 0, 255])
  assert.deepEqual(img.rgb(1, 1), [255, 0, 0])
})

test('quadkeys: Richmond and Gwynn’s Island sit in their zoom-9 tiles', () => {
  assert.equal(quadkey(-76.34, 37.5), '032010231')
  assert.equal(quadkey(-76.34, 37.5).length, 9)
})

test('footprints that overlap an OSM building are left out', () => {
  const sq = (x: number, y: number, s = 0.0001) => [[x, y], [x + s, y], [x + s, y + s], [x, y + s]] as [number, number][]
  const osm: PolygonFeature[] = [{ type: 'polygon', id: 'w1', tags: { building: 'house' }, outers: [sq(0, 0)], inners: [] }]
  const merged = mergeFootprints(osm, [{ ring: sq(0.00002, 0.00002) }, { ring: sq(0.001, 0.001), height: 7.5 }])
  assert.equal(merged.length, 1)
  assert.equal(merged[0].tags.height, '7.5')
  assert.equal(buildingHeights(merged[0].tags, 100).source, 'model')
})
