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
import { access, readFile, rename, writeFile, mkdir, rm } from 'node:fs/promises'
import { join } from 'node:path'
import { promisify } from 'node:util'
import { gunzipSync, gzipSync } from 'node:zlib'
import { fetchBounds, type Region } from './region.ts'
import type { Bounds } from './osm.ts'

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

const SIZE = (b: Bounds, metresPerPixel: number) => {
  const wm = (b.east - b.west) * 111_320 * Math.cos((((b.north + b.south) / 2) * Math.PI) / 180)
  const hm = (b.north - b.south) * 110_574
  return { width: Math.round(wm / metresPerPixel), height: Math.round(hm / metresPerPixel) }
}

/** The service's URL for a `width` × `height` grid over `b`. */
export const demUrl = (b: Bounds, width: number, height: number): string => {
  const q = new URLSearchParams({
    bbox: [b.west, b.south, b.east, b.north].map((n) => n.toFixed(7)).join(','),
    bboxSR: '4326',
    imageSR: '4326',
    size: `${width},${height}`,
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

/** Largest tile the service reliably answers, in pixels a side. */
const TILE = 1500

/**
 * Fetch the region's elevation as a mosaic of tiles (the service refuses large images), each
 * cached under `<dir>/dem-tiles/` so a failed or interrupted fetch resumes. When every tile is
 * in, they are stitched, stored as `<dir>/dem.bin.gz`, and the tile cache is removed.
 */
export const fetchDem = async (
  r: Region,
  dir: string,
  options: { budgetSeconds?: number; log?: (m: string) => void } = {},
): Promise<{ done: number; total: number }> => {
  const log = options.log ?? console.error
  const b = fetchBounds(r)
  const { width, height } = SIZE(b, r.terrain?.demResolution ?? 1)
  const cols = Math.ceil(width / TILE)
  const rows = Math.ceil(height / TILE)
  const dLon = (b.east - b.west) / width
  const dLat = (b.north - b.south) / height
  const tileDir = join(dir, 'dem-tiles')
  await mkdir(tileDir, { recursive: true })
  const t0 = Date.now()
  let done = 0
  const plan: { path: string; x0: number; y0: number; w: number; h: number; bounds: Bounds }[] = []
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const x0 = i * TILE
      const y0 = j * TILE
      const w = Math.min(TILE, width - x0)
      const h = Math.min(TILE, height - y0)
      plan.push({
        path: join(tileDir, `${j}-${i}.tif`),
        x0, y0, w, h,
        bounds: { west: b.west + x0 * dLon, east: b.west + (x0 + w) * dLon, north: b.north - y0 * dLat, south: b.north - (y0 + h) * dLat },
      })
    }
  }
  for (const [k, t] of plan.entries()) {
    try {
      await access(t.path)
      done++
      continue
    } catch {
      // not fetched yet
    }
    if (options.budgetSeconds !== undefined && (Date.now() - t0) / 1000 > options.budgetSeconds) break
    log(`elevation tile ${k + 1}/${plan.length}`)
    let ok = false
    for (let attempt = 0; attempt < 3 && !ok; attempt++) {
      try {
        await run('curl', ['-sS', '-f', '-m', '90', '-A', 'isoscape/0.1', '-o', `${t.path}.part`, demUrl(t.bounds, t.w, t.h)])
        readTiff(await readFile(`${t.path}.part`), t.bounds)
        await rename(`${t.path}.part`, t.path)
        ok = true
      } catch (error) {
        log(`  3DEP: ${(error as Error).message.split('\n').pop()}; retrying`)
        await new Promise((wake) => setTimeout(wake, 4000 * (attempt + 1)))
      }
    }
    if (!ok) throw new Error('3DEP did not answer. Run fetch again later; finished tiles are kept.')
    done++
  }
  if (done < plan.length) {
    log(`${done} of ${plan.length} elevation tiles fetched; run fetch again to continue`)
    return { done, total: plan.length }
  }
  const data = new Float32Array(width * height).fill(NaN)
  for (const t of plan) {
    const tile = readTiff(await readFile(t.path), t.bounds)
    for (let y = 0; y < Math.min(t.h, tile.height); y++) {
      for (let x = 0; x < Math.min(t.w, tile.width); x++) data[(t.y0 + y) * width + t.x0 + x] = tile.data[y * tile.width + x]
    }
  }
  const dem: Dem = { ...b, width, height, data }
  await writeFile(join(dir, 'dem.bin.gz'), encodeDem(dem))
  await rm(tileDir, { recursive: true, force: true })
  log(`elevation ${width}×${height} from ${plan.length} tiles, ${describe(dem)}`)
  return { done, total: plan.length }
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

/**
 * Mark implausible samples as missing. 3DEP occasionally carries a void patch filled with a
 * large negative value (one patch near Shockoe Bottom reads −88 m); left in, it would drag
 * the datum down and lift the whole scene. Missing samples are filled from their neighbours
 * when the terrain is built.
 */
export const cleanDem = (d: Dem, floor = -5, grow = 3): number => {
  // Mark the void, then grow the mark a few pixels: the service's resampling blends the
  // void's edge with real ground, leaving a rim of values that are wrong but not absurd.
  const bad = new Uint8Array(d.data.length)
  for (let i = 0; i < d.data.length; i++) if (d.data[i] < floor) bad[i] = 1
  let n = 0
  for (let y = 0; y < d.height; y++) {
    for (let x = 0; x < d.width; x++) {
      if (bad[y * d.width + x] !== 1) continue
      for (let dy = -grow; dy <= grow; dy++) {
        for (let dx = -grow; dx <= grow; dx++) {
          const xx = x + dx
          const yy = y + dy
          if (xx < 0 || yy < 0 || xx >= d.width || yy >= d.height) continue
          const k = yy * d.width + xx
          if (!Number.isNaN(d.data[k])) { d.data[k] = NaN; n++ }
        }
      }
    }
  }
  return n
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
