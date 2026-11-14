import { test } from 'node:test'
import assert from 'node:assert/strict'
import { deflateSync } from 'node:zlib'
import { decodeTiff, lzwDecode } from '../src/rasters.ts'
import { DEM_SOURCES, demSource, mercatorPixel, toLv95 } from '../src/dem-sources.ts'

/** A one-strip little-endian float TIFF, `compression` 1 or 8, optional predictor 3 and geotags. */
const tiff = (w: number, h: number, values: number[], compression: 1 | 8, predictor: 1 | 3, geo?: { scale: number[]; tie: number[] }) => {
  let body = Buffer.alloc(w * h * 4)
  values.forEach((v, i) => body.writeFloatLE(v, i * 4))
  if (predictor === 3) {
    const out = Buffer.alloc(body.length)
    for (let y = 0; y < h; y++) {
      const row = Buffer.alloc(w * 4)
      for (let x = 0; x < w; x++) {
        const be = Buffer.alloc(4)
        be.writeFloatBE(values[y * w + x])
        for (let b = 0; b < 4; b++) row[b * w + x] = be[b]
      }
      for (let i = row.length - 1; i > 0; i--) row[i] = (row[i] - row[i - 1]) & 0xff
      row.copy(out, y * w * 4)
    }
    body = out
  }
  const data = compression === 8 ? deflateSync(body) : body
  const tags: [number, number, number, number[]][] = [
    [256, 3, 1, [w]], [257, 3, 1, [h]], [258, 3, 1, [32]], [259, 3, 1, [compression]], [273, 4, 1, [0]],
    [278, 3, 1, [h]], [279, 4, 1, [data.length]], [317, 3, 1, [predictor]], [339, 3, 1, [3]],
  ]
  const extra: Buffer[] = []
  const ifdAt = 8
  const n = tags.length + (geo ? 2 : 0)
  let tail = ifdAt + 2 + n * 12 + 4
  const entries: Buffer[] = []
  for (const [tag, type, count, v] of tags) {
    const e = Buffer.alloc(12)
    e.writeUInt16LE(tag, 0); e.writeUInt16LE(type, 2); e.writeUInt32LE(count, 4)
    if (type === 3) e.writeUInt16LE(v[0], 8); else e.writeUInt32LE(v[0], 8)
    entries.push(e)
  }
  if (geo) {
    for (const [tag, v] of [[33550, geo.scale], [33922, geo.tie]] as const) {
      const e = Buffer.alloc(12)
      e.writeUInt16LE(tag, 0); e.writeUInt16LE(12, 2); e.writeUInt32LE(v.length, 4); e.writeUInt32LE(tail, 8)
      const d = Buffer.alloc(v.length * 8)
      v.forEach((x, i) => d.writeDoubleLE(x, i * 8))
      extra.push(d); tail += d.length; entries.push(e)
    }
    entries.sort((a, b) => a.readUInt16LE(0) - b.readUInt16LE(0))
  }
  const strip = tail
  const stripEntry = entries.find((e) => e.readUInt16LE(0) === 273)!
  stripEntry.writeUInt32LE(strip, 8)
  const head = Buffer.from([0x49, 0x49, 42, 0, 8, 0, 0, 0])
  const count = Buffer.alloc(2); count.writeUInt16LE(n)
  return Buffer.concat([head, count, ...entries, Buffer.alloc(4), ...extra, data])
}

test('an uncompressed float TIFF reads back', () => {
  const r = decodeTiff(tiff(2, 2, [1, 2, 3, -9999], 1, 1))
  assert.deepEqual([...r.data].slice(0, 3), [1, 2, 3])
  assert.ok(Number.isNaN(r.data[3]))
})

test('a Deflate TIFF with the floating-point predictor (Copernicus-style) reads back, georeferenced', () => {
  const values = [100.5, 101.25, 99, 98.75, 1234.5, -3.5]
  const r = decodeTiff(tiff(3, 2, values, 8, 3, { scale: [0.5, 0.25, 0], tie: [0, 0, 0, -73, -13, 0] }))
  assert.deepEqual([...r.data], values)
  assert.deepEqual(r.geo, { x0: -73, y0: -13, dx: 0.5, dy: 0.25 })
})

test('TIFF LZW decodes a repeating run (the KwKwK case)', () => {
  // Codes, 9 bits each, MSB first: 256 (clear), 65 'A', 258 ('AA', not yet defined), 257 (end).
  const codes = [256, 65, 258, 257]
  let bits = ''
  for (const c of codes) bits += c.toString(2).padStart(9, '0')
  while (bits.length % 8) bits += '0'
  const bytes = Uint8Array.from(bits.match(/.{8}/g)!.map((b) => parseInt(b, 2)))
  assert.deepEqual([...lzwDecode(bytes, 3)], [65, 65, 65])
})

test('Web Mercator and Swiss grid conversions land where they should', () => {
  // Zoom 0: the whole world is one 256-pixel tile, the equator and prime meridian at its centre.
  assert.deepEqual(mercatorPixel(0, 0, 0).map((v) => Math.round(v)), [128, 128])
  // The old Bern observatory, LV95's origin, is at 2 600 000 / 1 200 000 (to a metre or so).
  const [e, n] = toLv95(7.438632, 46.951083)
  assert.ok(Math.abs(e - 2_600_000) < 2 && Math.abs(n - 1_200_000) < 2, `${e} ${n}`)
})

test('every elevation source names its licence and credit, and 3DEP is the default', () => {
  for (const s of Object.values(DEM_SOURCES)) {
    assert.ok(s.credit.length > 10 && s.licence.length > 5 && s.link.startsWith('https://'), s.id)
  }
  assert.equal(demSource(undefined).id, '3dep')
  assert.throws(() => demSource('nowhere'))
})
