/**
 * Land cover from the USGS National Land Cover Database (NLCD 2021, 30 m, public domain).
 *
 * OSM maps woods and fields patchily, and in rural places hardly at all; NLCD classifies every
 * 30 m of the country from satellite imagery. It is read through the MRLC's WMS as a palette
 * PNG, and each colour is matched back to its class by the published legend. Stored as gzipped
 * class codes with a one-line JSON header.
 */

import { execFile } from 'node:child_process'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { promisify } from 'node:util'
import { gunzipSync, gzipSync } from 'node:zlib'
import { decodePng } from './png.ts'
import { fetchBounds, type Region } from './region.ts'

const run = promisify(execFile)

/** NLCD classes and their legend colours. */
export const NLCD: Readonly<Record<number, { name: string; rgb: [number, number, number] }>> = {
  11: { name: 'open water', rgb: [70, 107, 159] },
  12: { name: 'perennial ice/snow', rgb: [209, 222, 248] },
  21: { name: 'developed, open space', rgb: [222, 197, 197] },
  22: { name: 'developed, low intensity', rgb: [217, 146, 130] },
  23: { name: 'developed, medium intensity', rgb: [235, 0, 0] },
  24: { name: 'developed, high intensity', rgb: [171, 0, 0] },
  31: { name: 'barren land', rgb: [179, 172, 159] },
  41: { name: 'deciduous forest', rgb: [104, 171, 95] },
  42: { name: 'evergreen forest', rgb: [28, 95, 44] },
  43: { name: 'mixed forest', rgb: [181, 197, 143] },
  52: { name: 'shrub/scrub', rgb: [204, 184, 121] },
  71: { name: 'grassland/herbaceous', rgb: [223, 223, 194] },
  81: { name: 'pasture/hay', rgb: [220, 217, 57] },
  82: { name: 'cultivated crops', rgb: [171, 108, 40] },
  90: { name: 'woody wetlands', rgb: [184, 217, 235] },
  95: { name: 'emergent herbaceous wetlands', rgb: [108, 159, 184] },
}

/** How the drawing groups the classes; each group is one fill in the palette. */
export type CoverGroup = 'forest' | 'evergreen' | 'swamp' | 'marsh' | 'field' | 'crop' | 'scrub' | 'barren'
export const COVER_OF: Readonly<Record<number, CoverGroup>> = {
  41: 'forest', 43: 'forest', 42: 'evergreen', 90: 'swamp', 95: 'marsh',
  71: 'field', 81: 'field', 82: 'crop', 52: 'scrub', 31: 'barren',
}
/** Paint order of the cover groups, bottom first: open ground under woods. */
export const COVER_ORDER: readonly CoverGroup[] = ['crop', 'field', 'scrub', 'barren', 'marsh', 'swamp', 'forest', 'evergreen']

export interface Landcover {
  readonly west: number
  readonly south: number
  readonly east: number
  readonly north: number
  readonly width: number
  readonly height: number
  /** Class codes, row-major from the north; 0 where unknown. */
  readonly codes: Uint8Array
}

const WMS = 'https://www.mrlc.gov/geoserver/mrlc_display/wms'

const nearestClass = ([r, g, b]: readonly [number, number, number]): number => {
  let best = 0
  let bestD = Infinity
  for (const [code, { rgb }] of Object.entries(NLCD)) {
    const d = (rgb[0] - r) ** 2 + (rgb[1] - g) ** 2 + (rgb[2] - b) ** 2
    if (d < bestD) { bestD = d; best = Number(code) }
  }
  // Anything far from every legend colour (a no-data fill) is unknown.
  return bestD > 40 * 40 ? 0 : best
}

export const fetchLandcover = async (r: Region, dir: string, log = console.error): Promise<void> => {
  const b = fetchBounds(r)
  const wm = (b.east - b.west) * 111_320 * Math.cos((((b.north + b.south) / 2) * Math.PI) / 180)
  const hm = (b.north - b.south) * 110_574
  // 10 m a pixel: finer than NLCD's 30 m, so its cells keep their edges when resampled.
  const width = Math.min(4000, Math.round(wm / 10))
  const height = Math.min(4000, Math.round(hm / 10))
  const q = new URLSearchParams({
    service: 'WMS', version: '1.1.1', request: 'GetMap', layers: 'NLCD_2021_Land_Cover_L48', styles: '',
    srs: 'EPSG:4326', bbox: [b.west, b.south, b.east, b.north].map((n) => n.toFixed(6)).join(','),
    width: String(width), height: String(height), format: 'image/png', transparent: 'false',
  })
  await mkdir(dir, { recursive: true })
  const tmp = join(dir, 'landcover.png.part')
  await run('curl', ['-sS', '-f', '-m', '170', '-A', 'isoscape/0.1', '-o', tmp, `${WMS}?${q}`])
  const png = decodePng(await readFile(tmp))
  const codes = new Uint8Array(png.width * png.height)
  const cache = new Map<string, number>()
  for (let y = 0; y < png.height; y++) {
    for (let x = 0; x < png.width; x++) {
      const c = png.rgb(x, y)
      const k = c.join()
      let v = cache.get(k)
      if (v === undefined) { v = nearestClass(c); cache.set(k, v) }
      codes[y * png.width + x] = v
    }
  }
  const header = JSON.stringify({ ...b, width: png.width, height: png.height, source: 'NLCD 2021 via MRLC WMS' })
  await writeFile(join(dir, 'landcover.bin.gz'), gzipSync(Buffer.concat([Buffer.from(header + '\n'), Buffer.from(codes)])))
  await run('rm', ['-f', tmp]).catch(() => undefined)
  const counts = new Map<number, number>()
  for (const v of codes) counts.set(v, (counts.get(v) ?? 0) + 1)
  log(`land cover ${png.width}×${png.height}: ` + [...counts].sort((a, b) => b[1] - a[1]).slice(0, 5).map(([c, n]) => `${NLCD[c]?.name ?? 'unknown'} ${Math.round((100 * n) / codes.length)}%`).join(', '))
}

export const loadLandcover = async (path: string): Promise<Landcover | null> => {
  let raw: Buffer
  try {
    raw = gunzipSync(await readFile(path))
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return null
    throw error
  }
  const nl = raw.indexOf(10)
  const h = JSON.parse(raw.toString('utf8', 0, nl)) as Omit<Landcover, 'codes'>
  return { ...h, codes: new Uint8Array(raw.subarray(nl + 1)) }
}

/** The class at lon/lat (nearest cell), or 0. */
export const coverSampler = (l: Landcover) => (lon: number, lat: number): number => {
  const x = Math.floor(((lon - l.west) / (l.east - l.west)) * l.width)
  const y = Math.floor(((l.north - lat) / (l.north - l.south)) * l.height)
  if (x < 0 || y < 0 || x >= l.width || y >= l.height) return 0
  return l.codes[y * l.width + x]
}
