/**
 * Elevation: fetch, store, sample.
 *
 * The source is USGS 3DEP (the National Map's seamless elevation service), which serves the
 * best available bare-earth model, 1 m lidar across Richmond. Water in 3DEP is
 * hydro-flattened: a river surface is flat across its width and steps down along its course,
 * so the fall of the James through the city is in the data, concentrated where it really
 * drops.
 *
 * The service answers with an uncompressed float GeoTIFF on a lon/lat grid. It is stored
 * compactly as gzipped int16 centimetres above the grid's minimum, with a one-line JSON header.
 */

import { execFile } from 'node:child_process'
import { readFile, writeFile, mkdir, mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { promisify } from 'node:util'
import { gunzipSync, gzipSync } from 'node:zlib'
import { fetchBounds, type Region } from './region.ts'

const run = promisify(execFile)

export interface Dem {
  readonly west: number
  readonly south: number
  readonly east: number
  readonly north: number
  readonly width: number
  readonly height: number
  /** Row-major, row 0 at the north edge; metres; NaN where there is no data. */
  readonly data: Float32Array
}

const SERVICE = 'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage'

/** Ask for a grid at about `metresPerPixel` over the region's fetch bounds. */
export const demUrl = (r: Region, metresPerPixel = 1): string => {
  const b = fetchBounds(r)
  const wm = (b.east - b.west) * 111_320 * Math.cos((((b.north + b.south) / 2) * Math.PI) / 180)
  const hm = (b.north - b.south) * 110_574
  const w = Math.min(8000, Math.round(wm / metresPerPixel))
  const h = Math.min(8000, Math.round(hm / metresPerPixel))
  const q = new URLSearchParams({
    bbox: [b.west, b.south, b.east, b.north].map((n) => n.toFixed(6)).join(','),
    bboxSR: '4326',
    imageSR: '4326',
    size: `${w},${h}`,
    format: 'tiff',
    pixelType: 'F32',
    noData: '-9999',
    noDataInterpretation: 'esriNoDataMatchAny',
    interpolation: 'RSP_BilinearInterpolation',
    compression: 'None',
    f: 'image',
  })
  return `${SERVICE}?${q}`
}

export const fetchDem = async (r: Region, out: string, log = console.error): Promise<void> => {
  const dir = await mkdtemp(join(tmpdir(), 'isoscape-'))
  const tif = join(dir, 'dem.tif')
  try {
    let lastError: unknown
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        await run('curl', ['-sS', '-f', '-m', '170', '-A', 'isoscape/0.1', '-o', tif, demUrl(r)])
        lastError = undefined
        break
      } catch (error) {
        lastError = error
        log(`3DEP: ${(error as Error).message.split('\n')[0]}; retrying`)
        await new Promise((done) => setTimeout(done, 5000 * (attempt + 1)))
      }
    }
    if (lastError !== undefined) throw lastError
    const b = fetchBounds(r)
    const dem = readTiff(await readFile(tif), b)
    await mkdir(dirname(out), { recursive: true })
    await writeFile(out, encodeDem(dem))
    log(`elevation ${dem.width}×${dem.height}, ${describe(dem)}`)
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
}

const describe = (d: Dem) => {
  let lo = Infinity
  let hi = -Infinity
  for (const v of d.data) if (!Number.isNaN(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v) }
  return `${lo.toFixed(1)}–${hi.toFixed(1)} m`
}

/**
 * Just enough TIFF: little- or big-endian, uncompressed, one 32-bit float sample, strips or
 * tiles. The georeference comes from the request, not the file's GeoTIFF tags.
 */
export const readTiff = (buf: Buffer, bounds: { west: number; south: number; east: number; north: number }): Dem => {
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
    const size = type === 3 ? 2 : type === 4 ? 4 : type === 16 ? 8 : 1
    const at = n * size > 4 ? u32(e + 8) : e + 8
    const values: number[] = []
    for (let k = 0; k < n && k < 1_000_000; k++) {
      if (type === 3) values.push(u16(at + k * 2))
      else if (type === 4) values.push(u32(at + k * 4))
      else values.push(buf[at + k])
    }
    tags.set(tag, values)
  }
  const get = (t: number) => tags.get(t)?.[0]
  const width = get(256)!
  const height = get(257)!
  if (get(258) !== 32 || (get(339) ?? 1) !== 3) throw new Error('expected 32-bit float samples')
  if ((get(259) ?? 1) !== 1) throw new Error('expected an uncompressed TIFF (compression=None)')
  const f32 = (o: number) => (le ? buf.readFloatLE(o) : buf.readFloatBE(o))
  const data = new Float32Array(width * height)
  const put = (x: number, y: number, v: number) => {
    if (x < width && y < height) data[y * width + x] = v <= -9000 || !Number.isFinite(v) ? NaN : v
  }
  if (tags.has(322)) {
    const tw = get(322)!
    const th = get(323)!
    const offsets = tags.get(324)!
    const across = Math.ceil(width / tw)
    offsets.forEach((off, t) => {
      const tx = (t % across) * tw
      const ty = Math.floor(t / across) * th
      for (let y = 0; y < th; y++) for (let x = 0; x < tw; x++) put(tx + x, ty + y, f32(off + (y * tw + x) * 4))
    })
  } else {
    const offsets = tags.get(273)!
    const rows = get(278) ?? height
    offsets.forEach((off, s) => {
      for (let y = 0; y < rows; y++) {
        const row = s * rows + y
        if (row >= height) break
        for (let x = 0; x < width; x++) put(x, row, f32(off + (y * width + x) * 4))
      }
    })
  }
  return { ...bounds, width, height, data }
}

export const encodeDem = (d: Dem): Buffer => {
  let lo = Infinity
  for (const v of d.data) if (!Number.isNaN(v) && v < lo) lo = v
  if (!Number.isFinite(lo)) lo = 0
  const q = new Int16Array(d.data.length)
  for (let i = 0; i < q.length; i++) {
    const v = d.data[i]
    q[i] = Number.isNaN(v) ? -32768 : Math.max(-32767, Math.min(32767, Math.round((v - lo) * 100)))
  }
  const header = JSON.stringify({ west: d.west, south: d.south, east: d.east, north: d.north, width: d.width, height: d.height, offset: lo, scale: 0.01 })
  return gzipSync(Buffer.concat([Buffer.from(header + '\n'), Buffer.from(q.buffer)]), { level: 9 })
}

export const decodeDem = (gz: Buffer): Dem => {
  const raw = gunzipSync(gz)
  const nl = raw.indexOf(10)
  const h = JSON.parse(raw.toString('utf8', 0, nl)) as Omit<Dem, 'data'> & { offset: number; scale: number }
  const body = raw.subarray(nl + 1)
  const q = new Int16Array(body.buffer.slice(body.byteOffset, body.byteOffset + body.byteLength))
  const data = new Float32Array(q.length)
  for (let i = 0; i < q.length; i++) data[i] = q[i] === -32768 ? NaN : h.offset + q[i] * h.scale
  return { west: h.west, south: h.south, east: h.east, north: h.north, width: h.width, height: h.height, data }
}

export const loadDem = async (path: string): Promise<Dem | null> => {
  try {
    return decodeDem(await readFile(path))
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return null
    throw error
  }
}

/** Bilinear elevation at lon/lat, ignoring missing samples. NaN outside the grid. */
export const sampler = (d: Dem) => (lon: number, lat: number): number => {
  const fx = ((lon - d.west) / (d.east - d.west)) * d.width - 0.5
  const fy = ((d.north - lat) / (d.north - d.south)) * d.height - 0.5
  const x0 = Math.floor(fx)
  const y0 = Math.floor(fy)
  const tx = fx - x0
  const ty = fy - y0
  let sum = 0
  let weight = 0
  for (const [dx, dy, w] of [[0, 0, (1 - tx) * (1 - ty)], [1, 0, tx * (1 - ty)], [0, 1, (1 - tx) * ty], [1, 1, tx * ty]] as const) {
    const x = Math.min(d.width - 1, Math.max(0, x0 + dx))
    const y = Math.min(d.height - 1, Math.max(0, y0 + dy))
    const v = d.data[y * d.width + x]
    if (!Number.isNaN(v) && w > 0) { sum += v * w; weight += w }
  }
  return weight > 0 ? sum / weight : NaN
}
