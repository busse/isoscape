/**
 * Just enough raster decoding for elevation, with no dependencies.
 *
 * - **GeoTIFF**: classic TIFF, little- or big-endian, strips or tiles; uncompressed, LZW or
 *   Deflate; no predictor, horizontal (2) or floating-point (3) predictor; one 32-bit float or
 *   16-bit integer sample. That covers USGS 3DEP's exports, swisstopo's swissALTI3D tiles and
 *   the Copernicus DEM's cloud-optimised GeoTIFFs. The georeference (pixel scale, tie point,
 *   pixel-is-area or -point) is read from the GeoTIFF tags when present.
 *
 * PNG elevation tiles (GSI, AWS Terrain Tiles) are read with `png.ts`.
 */

import { inflateSync } from 'node:zlib'

export interface Raster {
  readonly width: number
  readonly height: number
  /** Row-major, row 0 at the top; NaN where there is no data. */
  readonly data: Float32Array
  /**
   * Where pixel (0, 0)'s outer corner sits in the file's own CRS, and the size of a pixel
   * (y grows downward, so `dy` is positive and northing falls). Undefined when the file
   * carries no georeference.
   */
  readonly geo?: { readonly x0: number; readonly y0: number; readonly dx: number; readonly dy: number }
}

// ------------------------------------------------------------------------------------ TIFF

/** TIFF's LZW: MSB-first codes, 9 to 12 bits, with the "early change" one code before full. */
export const lzwDecode = (src: Uint8Array, expected: number): Uint8Array => {
  const out = new Uint8Array(expected)
  let o = 0
  const dict: Uint8Array[] = []
  const reset = () => {
    dict.length = 0
    for (let i = 0; i < 256; i++) dict.push(Uint8Array.of(i))
    dict.push(new Uint8Array(0), new Uint8Array(0)) // 256 clear, 257 end
  }
  reset()
  let bits = 9
  let pos = 0
  const total = src.length * 8
  let prev: Uint8Array | null = null
  const read = () => {
    let v = 0
    for (let i = 0; i < bits; i++) {
      const p = pos + i
      v = (v << 1) | ((src[p >> 3] >> (7 - (p & 7))) & 1)
    }
    pos += bits
    return v
  }
  const emit = (s: Uint8Array) => {
    const n = Math.min(s.length, expected - o)
    out.set(n === s.length ? s : s.subarray(0, n), o)
    o += n
  }
  while (pos + bits <= total && o < expected) {
    const code = read()
    if (code === 257) break
    if (code === 256) {
      reset()
      bits = 9
      prev = null
      continue
    }
    let entry: Uint8Array
    if (code < dict.length) entry = dict[code]
    else if (prev !== null) {
      entry = new Uint8Array(prev.length + 1)
      entry.set(prev)
      entry[prev.length] = prev[0]
    } else throw new Error('LZW: bad code')
    emit(entry)
    if (prev !== null) {
      const add = new Uint8Array(prev.length + 1)
      add.set(prev)
      add[prev.length] = entry[0]
      dict.push(add)
    }
    prev = entry
    if (dict.length + 1 >= 1 << bits && bits < 12) bits++
  }
  return out
}

/** Undo the floating-point predictor (3) on one row of `w` samples of `bps` bytes. */
const unpredictFloat = (row: Uint8Array, w: number, bps: number): Uint8Array => {
  for (let i = 1; i < row.length; i++) row[i] = (row[i] + row[i - 1]) & 0xff
  // Bytes were split into planes, most significant first; put each sample back big-endian.
  const out = new Uint8Array(row.length)
  for (let x = 0; x < w; x++) for (let b = 0; b < bps; b++) out[x * bps + b] = row[b * w + x]
  return out
}

/** Parse a classic TIFF to metres, with its georeference when the file carries one. */
export const decodeTiff = (buf: Buffer): Raster => {
  const le = buf.toString('latin1', 0, 2) === 'II'
  const u16 = (o: number) => (le ? buf.readUInt16LE(o) : buf.readUInt16BE(o))
  const u32 = (o: number) => (le ? buf.readUInt32LE(o) : buf.readUInt32BE(o))
  if (u16(2) !== 42) throw new Error('not a classic TIFF')
  const ifd = u32(4)
  const count = u16(ifd)
  const tags = new Map<number, number[]>()
  for (let i = 0; i < count; i++) {
    const e = ifd + 2 + i * 12
    const tag = u16(e)
    const type = u16(e + 2)
    const n = u32(e + 4)
    const size = type === 3 ? 2 : type === 4 ? 4 : type === 12 || type === 16 ? 8 : 1
    const at = n * size > 4 ? u32(e + 8) : e + 8
    const values: number[] = []
    for (let k = 0; k < n && k < 1_000_000; k++) {
      if (type === 3) values.push(u16(at + k * 2))
      else if (type === 4) values.push(u32(at + k * 4))
      else if (type === 12) values.push(le ? buf.readDoubleLE(at + k * 8) : buf.readDoubleBE(at + k * 8))
      else values.push(buf[at + k])
    }
    tags.set(tag, values)
  }
  const get = (t: number) => tags.get(t)?.[0]
  const width = get(256)!
  const height = get(257)!
  const bitsPer = get(258) ?? 1
  const format = get(339) ?? 1 // 1 uint, 2 int, 3 float
  const compression = get(259) ?? 1
  const predictor = get(317) ?? 1
  const bps = bitsPer / 8
  if (!((bitsPer === 32 && format === 3) || (bitsPer === 16 && (format === 1 || format === 2)))) {
    throw new Error(`unsupported samples: ${bitsPer}-bit format ${format}`)
  }
  if (![1, 5, 8, 32946].includes(compression)) throw new Error(`unsupported TIFF compression ${compression}`)
  const noDataText = tags.get(42113)
  const noData = noDataText === undefined ? undefined : Number(String.fromCharCode(...noDataText).replace(/\0/g, ''))

  const data = new Float32Array(width * height).fill(NaN)
  const decodeBlock = (off: number, len: number, bw: number, bh: number): Uint8Array => {
    const raw = buf.subarray(off, off + len)
    const want = bw * bh * bps
    let bytes: Uint8Array =
      compression === 1 ? new Uint8Array(raw) : compression === 5 ? lzwDecode(raw, want) : new Uint8Array(inflateSync(raw))
    if (predictor === 3) {
      const out = new Uint8Array(want)
      for (let y = 0; y < bh; y++) out.set(unpredictFloat(bytes.slice(y * bw * bps, (y + 1) * bw * bps), bw, bps), y * bw * bps)
      return out // big-endian samples now
    }
    if (predictor === 2) {
      const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
      for (let y = 0; y < bh; y++) {
        for (let x = 1; x < bw; x++) {
          const k = (y * bw + x) * bps
          if (bps === 2) view.setUint16(k, (view.getUint16(k, le) + view.getUint16(k - 2, le)) & 0xffff, le)
        }
      }
    }
    return bytes
  }
  const readSample = (bytes: Uint8Array, k: number): number => {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
    const bigEndian = predictor === 3 || !le
    if (bitsPer === 32) return view.getFloat32(k * 4, !bigEndian)
    return format === 2 ? view.getInt16(k * 2, !bigEndian) : view.getUint16(k * 2, !bigEndian)
  }
  const put = (x: number, y: number, v: number) => {
    if (x >= width || y >= height) return
    data[y * width + x] = !Number.isFinite(v) || v <= -9000 || (noData !== undefined && v === noData) ? NaN : v
  }
  if (tags.has(322)) {
    const tw = get(322)!
    const th = get(323)!
    const offsets = tags.get(324)!
    const counts = tags.get(325)!
    const across = Math.ceil(width / tw)
    offsets.forEach((off, t) => {
      const bytes = decodeBlock(off, counts[t], tw, th)
      const tx = (t % across) * tw
      const ty = Math.floor(t / across) * th
      for (let y = 0; y < th; y++) for (let x = 0; x < tw; x++) put(tx + x, ty + y, readSample(bytes, y * tw + x))
    })
  } else {
    const offsets = tags.get(273)!
    const counts = tags.get(279) ?? offsets.map(() => width * (get(278) ?? height) * bps)
    const rows = get(278) ?? height
    offsets.forEach((off, s) => {
      const h = Math.min(rows, height - s * rows)
      const bytes = decodeBlock(off, counts[s], width, h)
      for (let y = 0; y < h; y++) for (let x = 0; x < width; x++) put(x, s * rows + y, readSample(bytes, y * width + x))
    })
  }

  // Georeference: ModelPixelScale (33550) and ModelTiepoint (33922), shifted half a pixel
  // when the GeoKey directory (34735) says the raster is pixel-is-point (GTRasterTypeGeoKey 1025 = 2).
  const scale = tags.get(33550)
  const tie = tags.get(33922)
  let geo: Raster['geo']
  if (scale !== undefined && tie !== undefined) {
    const keys = tags.get(34735) ?? []
    let pointish = false
    for (let k = 4; k + 3 < keys.length; k += 4) if (keys[k] === 1025 && keys[k + 3] === 2) pointish = true
    const half = pointish ? 0.5 : 0
    geo = { x0: tie[3] - (tie[0] + half) * scale[0], y0: tie[4] + (tie[1] + half) * scale[1], dx: scale[0], dy: scale[1] }
  }
  return { width, height, data, geo }
}

/** Bilinear sample of a raster at fractional pixel (fx, fy), measured from pixel centres. NaN-aware. */
export const bilinear = (r: { width: number; height: number; data: Float32Array }, fx: number, fy: number): number => {
  if (fx < -0.5 || fy < -0.5 || fx > r.width - 0.5 || fy > r.height - 0.5) return NaN
  const x0 = Math.floor(fx)
  const y0 = Math.floor(fy)
  const tx = fx - x0
  const ty = fy - y0
  let sum = 0
  let weight = 0
  for (const [dx, dy, w] of [[0, 0, (1 - tx) * (1 - ty)], [1, 0, tx * (1 - ty)], [0, 1, (1 - tx) * ty], [1, 1, tx * ty]] as const) {
    const x = Math.min(r.width - 1, Math.max(0, x0 + dx))
    const y = Math.min(r.height - 1, Math.max(0, y0 + dy))
    const v = r.data[y * r.width + x]
    if (!Number.isNaN(v) && w > 0) { sum += v * w; weight += w }
  }
  return weight > 0 ? sum / weight : NaN
}
