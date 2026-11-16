/**
 * Elevation: fetch, store, sample.
 *
 * The heights come from one of several sources (`dem-sources.ts`), chosen by the region's
 * `terrain.source`: USGS 3DEP in the US (the default), or a national or global model
 * elsewhere. Whatever the source, the result is the same: a grid of meters above sea level on
 * the region's lon/lat box, stored compactly as gzipped int16 steps above the grid's minimum,
 * with a one-line JSON header. Nothing after the fetch needs to know which source it was, except
 * that grids fetched from 3DEP before `servedBox` was known are put right as they load.
 *
 * In 3DEP, water is hydro-flattened: a river surface is flat across its width and steps down
 * along its course, so the fall of the James through the city is in the data.
 */

import { execFile } from 'node:child_process'
import { access, readFile, rename, writeFile, mkdir, rm } from 'node:fs/promises'
import { join } from 'node:path'
import { promisify } from 'node:util'
import { gunzipSync, gzipSync } from 'node:zlib'
import { fetchBounds, type Region } from './region.ts'
import type { Bounds } from './osm.ts'
import { demSource, regrid, servedBox, type MosaicSource, type RequestSource } from './dem-sources.ts'
import { decodeTiff } from './rasters.ts'

const run = promisify(execFile)

export interface Dem {
  readonly west: number
  readonly south: number
  readonly east: number
  readonly north: number
  readonly width: number
  readonly height: number
  /** Row-major, row 0 at the north edge; meters; NaN where there is no data. */
  readonly data: Float32Array
  /** The source's id, as stored in the file (absent in the oldest files, which are all 3DEP). */
  readonly source?: string
  /** True when every sample sits where the box says (see `alignServed`). */
  readonly aligned?: boolean
}

const SIZE = (b: Bounds, metersPerPixel: number) => {
  const wm = (b.east - b.west) * 111_320 * Math.cos((((b.north + b.south) / 2) * Math.PI) / 180)
  const hm = (b.north - b.south) * 110_574
  return { width: Math.round(wm / metersPerPixel), height: Math.round(hm / metersPerPixel) }
}

/** Kept for callers that only want the 3DEP URL. */
export const demUrl = (b: Bounds, width: number, height: number): string => (demSource('3dep') as RequestSource).url(b, width, height)

/** 3DEP's TIFF for a request of `bounds`, resampled from the box it really covers (`servedBox`). */
export const readTiff = (buf: Buffer, bounds: { west: number; south: number; east: number; north: number }): Dem => {
  const r = decodeTiff(buf)
  return { ...bounds, width: r.width, height: r.height, data: regrid(r.data, r.width, r.height, servedBox(bounds, r.width, r.height), bounds), aligned: true }
}

/**
 * Put a 3DEP grid fetched before `servedBox` was known back where it belongs.
 *
 * 3DEP keeps its pixels square in degrees, so every image it served for a box sized in meters
 * covered more latitude than asked, about the box's center: the ground in it sits squeezed
 * north–south by the cosine of the latitude (0.73 at Crater Lake), up to a few hundred meters
 * off at an image's edge, with a step where two tiles meet. Each image is resampled from the
 * box it covered onto the box it was stored as. The oldest files were one image; later ones
 * are rows of `tile`-pixel tiles, told apart by the step at the first tile row.
 */
export const alignServed = (d: Dem, tile = (demSource('3dep') as RequestSource).tile): Dem => {
  const { width, height } = d
  const tiled = height > tile && rowStep(d, tile) > 4
  const rows = tiled ? tile : height
  const cols = tiled ? tile : width
  const dLon = (d.east - d.west) / width
  const dLat = (d.north - d.south) / height
  const data = new Float32Array(width * height)
  for (let y0 = 0; y0 < height; y0 += rows) {
    for (let x0 = 0; x0 < width; x0 += cols) {
      const w = Math.min(cols, width - x0)
      const h = Math.min(rows, height - y0)
      const box = { west: d.west + x0 * dLon, east: d.west + (x0 + w) * dLon, north: d.north - y0 * dLat, south: d.north - (y0 + h) * dLat }
      const piece = new Float32Array(w * h)
      for (let y = 0; y < h; y++) piece.set(d.data.subarray((y0 + y) * width + x0, (y0 + y) * width + x0 + w), y * w)
      const fixed = regrid(piece, w, h, servedBox(box, w, h), box)
      for (let y = 0; y < h; y++) data.set(fixed.subarray(y * w, (y + 1) * w), (y0 + y) * width + x0)
    }
  }
  return { ...d, data, aligned: true }
}

/** How much bigger the mean change across row `y` is than across the rows near it. */
const rowStep = (d: Dem, y: number): number => {
  const across = (r: number) => {
    let s = 0
    let n = 0
    for (let x = 0; x < d.width; x++) {
      const a = d.data[r * d.width + x]
      const b = d.data[(r - 1) * d.width + x]
      if (!Number.isNaN(a) && !Number.isNaN(b)) { s += Math.abs(a - b); n++ }
    }
    return n > 0 ? s / n : 0
  }
  const near = [y - 10, y - 5, y + 5, y + 10].filter((r) => r >= 1 && r < d.height).map(across)
  const base = near.reduce((a, b) => a + b, 0) / Math.max(1, near.length)
  return base > 0 ? across(y) / base : 0
}

type Log = (m: string) => void

/** Download `url` to `path` (via `.part`); `false` when the server has no such file (404). */
const download = async (url: string, path: string): Promise<boolean> => {
  const { stdout } = await run('curl', ['-sS', '-L', '-m', '180', '-A', 'isoscape/0.1', '-o', `${path}.part`, '-w', '%{http_code}', url], { maxBuffer: 1 << 20 })
  const code = Number(stdout.trim())
  if (code === 404 || code === 403) {
    await rm(`${path}.part`, { force: true })
    return false
  }
  if (code < 200 || code >= 300) throw new Error(`HTTP ${code} for ${url}`)
  await rename(`${path}.part`, path)
  return true
}

const getText = async (url: string): Promise<string> => {
  const { stdout } = await run('curl', ['-sS', '-f', '-L', '-m', '60', '-A', 'isoscape/0.1', url], { maxBuffer: 1 << 26 })
  return stdout
}

const exists = async (p: string) => access(p).then(() => true, () => false)

const retry = async <T>(what: string, log: Log, f: () => Promise<T>): Promise<T> => {
  for (let attempt = 0; ; attempt++) {
    try {
      return await f()
    } catch (error) {
      if (attempt >= 2) throw new Error(`${what} did not answer (${(error as Error).message.split('\n').pop()}). Run fetch again later; finished pieces are kept.`)
      log(`  ${what}: ${(error as Error).message.split('\n').pop()}; retrying`)
      await new Promise((wake) => setTimeout(wake, 4000 * (attempt + 1)))
    }
  }
}

/** A service that cuts images to order: fetch the grid in aligned tiles. */
const fetchByRequest = async (src: RequestSource, b: Bounds, width: number, height: number, dir: string, budget: number | undefined, log: Log) => {
  const cols = Math.ceil(width / src.tile)
  const rows = Math.ceil(height / src.tile)
  const dLon = (b.east - b.west) / width
  const dLat = (b.north - b.south) / height
  const plan: { path: string; x0: number; y0: number; w: number; h: number; bounds: Bounds }[] = []
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const x0 = i * src.tile
      const y0 = j * src.tile
      const w = Math.min(src.tile, width - x0)
      const h = Math.min(src.tile, height - y0)
      plan.push({
        path: join(dir, `${j}-${i}.bin`),
        x0, y0, w, h,
        bounds: { west: b.west + x0 * dLon, east: b.west + (x0 + w) * dLon, north: b.north - y0 * dLat, south: b.north - (y0 + h) * dLat },
      })
    }
  }
  const t0 = Date.now()
  let done = 0
  for (const [k, t] of plan.entries()) {
    if (await exists(t.path)) { done++; continue }
    if (budget !== undefined && (Date.now() - t0) / 1000 > budget) break
    log(`elevation tile ${k + 1}/${plan.length} (${src.name})`)
    await retry(src.name, log, async () => {
      if (!(await download(src.url(t.bounds, t.w, t.h), `${t.path}.dl`))) throw new Error('no such image')
      src.decode(await readFile(`${t.path}.dl`), t.bounds, t.w, t.h)
      await rename(`${t.path}.dl`, t.path)
    })
    done++
  }
  if (done < plan.length) return { done, total: plan.length, data: null }
  const data = new Float32Array(width * height).fill(NaN)
  for (const t of plan) {
    const tile = src.decode(await readFile(t.path), t.bounds, t.w, t.h)
    for (let y = 0; y < t.h; y++) for (let x = 0; x < t.w; x++) data[(t.y0 + y) * width + t.x0 + x] = tile[y * t.w + x]
  }
  return { done, total: plan.length, data }
}

/** A source published in fixed pieces: download those covering the box, then resample. */
const fetchByMosaic = async (src: MosaicSource, b: Bounds, width: number, height: number, mpp: number, dir: string, budget: number | undefined, log: Log) => {
  const pieces = await retry(src.name, log, () => src.pieces(b, mpp, getText))
  const t0 = Date.now()
  let done = 0
  for (const [k, p] of pieces.entries()) {
    const path = join(dir, p.file)
    if ((await exists(path)) || (await exists(`${path}.missing`))) { done++; continue }
    if (budget !== undefined && (Date.now() - t0) / 1000 > budget) break
    log(`elevation piece ${k + 1}/${pieces.length} (${src.name}): ${p.file}`)
    const found = await retry(src.name, log, () => download(p.url, path))
    if (!found) await writeFile(`${path}.missing`, '')
    done++
  }
  if (done < pieces.length) return { done, total: pieces.length, data: null }
  const got = await Promise.all(
    pieces.map(async (piece) => ({ piece, buf: (await exists(join(dir, piece.file))) ? await readFile(join(dir, piece.file)) : null })),
  )
  const missing = got.filter((g) => g.buf === null).length
  if (missing > 0) log(`  ${missing} of ${pieces.length} pieces have no data (outside the source's coverage, or sea)`)
  const sample = src.sampler(got)
  const data = new Float32Array(width * height)
  const dLon = (b.east - b.west) / width
  const dLat = (b.north - b.south) / height
  for (let y = 0; y < height; y++) {
    const lat = b.north - (y + 0.5) * dLat
    for (let x = 0; x < width; x++) data[y * width + x] = sample(b.west + (x + 0.5) * dLon, lat)
  }
  return { done, total: pieces.length, data }
}

/**
 * Fetch the region's elevation from its source, caching each downloaded tile or piece under
 * `<dir>/dem-tiles/` so a failed or interrupted fetch resumes. When every piece is in, the grid
 * is assembled, stored as `<dir>/dem.bin.gz` with the source's id, and the cache is removed.
 */
export const fetchDem = async (
  r: Region,
  dir: string,
  options: { budgetSeconds?: number; log?: (m: string) => void } = {},
): Promise<{ done: number; total: number }> => {
  const log = options.log ?? console.error
  const src = demSource(r.terrain?.source)
  const b = fetchBounds(r)
  const mpp = r.terrain?.demResolution ?? Math.max(1, src.native)
  const { width, height } = SIZE(b, mpp)
  const tileDir = join(dir, 'dem-tiles')
  const grid = async (s: typeof src, d: string) => {
    await mkdir(d, { recursive: true })
    return s.kind === 'request'
      ? fetchByRequest(s, b, width, height, d, options.budgetSeconds, log)
      : fetchByMosaic(s, b, width, height, mpp, d, options.budgetSeconds, log)
  }
  const got = await grid(src, tileDir)
  if (got.data === null) {
    log(`${got.done} of ${got.total} elevation pieces fetched; run fetch again to continue`)
    return { done: got.done, total: got.total }
  }
  // A national model stops at the border: fill what it leaves empty from a second source.
  const fillId = r.terrain?.fillFrom
  let filled = 0
  if (fillId !== undefined && got.data.some((v) => Number.isNaN(v))) {
    const fill = demSource(fillId)
    const more = await grid(fill, join(dir, 'dem-fill'))
    if (more.data === null) {
      log(`${more.done} of ${more.total} fill pieces (${fill.name}) fetched; run fetch again to continue`)
      return { done: got.done + more.done, total: got.total + more.total }
    }
    for (let i = 0; i < got.data.length; i++) if (Number.isNaN(got.data[i]) && !Number.isNaN(more.data[i])) { got.data[i] = more.data[i]; filled++ }
    log(`  ${((filled / got.data.length) * 100).toFixed(1)}% of the grid filled from ${fill.name}`)
  }
  const dem: Dem = { ...b, width, height, data: got.data, aligned: true }
  await writeFile(join(dir, 'dem.bin.gz'), encodeDem(dem, filled > 0 ? `${src.id}+${fillId}` : src.id))
  await rm(tileDir, { recursive: true, force: true })
  await rm(join(dir, 'dem-fill'), { recursive: true, force: true })
  log(`elevation ${width}×${height} from ${got.total} ${src.name} pieces, ${describe(dem)}`)
  return { done: got.done, total: got.total }
}

const describe = (d: Dem) => {
  let lo = Infinity
  let hi = -Infinity
  let missing = 0
  for (const v of d.data) if (!Number.isNaN(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v) } else missing++
  return `${lo.toFixed(1)}–${hi.toFixed(1)} m${missing ? `, ${((missing / d.data.length) * 100).toFixed(1)}% without data` : ''}`
}

export const encodeDem = (d: Dem, source?: string): Buffer => {
  let lo = Infinity
  let hi = -Infinity
  for (const v of d.data) if (!Number.isNaN(v)) { if (v < lo) lo = v; if (v > hi) hi = v }
  if (!Number.isFinite(lo)) { lo = 0; hi = 0 }
  // Centimeters while the relief fits in int16 (327 m); coarser steps beyond, so a canyon or a
  // mountain is never clipped flat at 327 m above its lowest point.
  const scale = Math.max(0.01, Math.ceil(((hi - lo) / 32767) * 100) / 100)
  const q = new Int16Array(d.data.length)
  for (let i = 0; i < q.length; i++) {
    const v = d.data[i]
    q[i] = Number.isNaN(v) ? -32768 : Math.max(-32767, Math.min(32767, Math.round((v - lo) / scale)))
  }
  const header = JSON.stringify({ west: d.west, south: d.south, east: d.east, north: d.north, width: d.width, height: d.height, offset: lo, scale, ...(source === undefined ? {} : { source }), ...(d.aligned === true ? { aligned: true } : {}) })
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
  return {
    west: h.west, south: h.south, east: h.east, north: h.north, width: h.width, height: h.height, data,
    ...(h.source === undefined ? {} : { source: h.source }), ...(h.aligned === true ? { aligned: true } : {}),
  }
}

/** Was this grid fetched from 3DEP before its served box was accounted for? */
export const misaligned = (d: Dem): boolean => d.aligned !== true && (d.source === undefined || d.source.split('+')[0] === '3dep')

export const loadDem = async (path: string): Promise<Dem | null> => {
  try {
    const d = decodeDem(await readFile(path))
    return misaligned(d) ? alignServed(d) : d
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return null
    throw error
  }
}

/**
 * Mark implausible samples as missing. 3DEP occasionally carries a void patch filled with a
 * large negative value (one patch near Shockoe Bottom reads −88 m); left in, it would drag
 * the datum down and lift the whole scene. Missing samples are filled from their neighbors
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
