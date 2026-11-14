/**
 * Building footprints from Microsoft's Global ML Building Footprints (ODbL).
 *
 * OSM is thorough in cities and thin in the country: around Gwynn's Island it maps 417
 * buildings where Microsoft's model finds over 6,000. The model traced footprints from aerial
 * imagery, and estimates a height for many of them. The dataset is split by zoom-9 quadkey;
 * the parts covering a region are downloaded, cut to the region, and stored as one small file.
 *
 * Merged with OSM, OSM wins: a footprint is dropped where it and an OSM building overlap.
 */

import { execFile } from 'node:child_process'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { promisify } from 'node:util'
import { gunzipSync } from 'node:zlib'
import type { Vec2 } from './geom.ts'
import type { Bounds, PolygonFeature } from './osm.ts'
import { fetchBounds, type Region } from './region.ts'

const run = promisify(execFile)

const LINKS = 'https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv'

/** Zoom-9 quadkey of a lon/lat. */
export const quadkey = (lon: number, lat: number, z = 9): string => {
  const n = 2 ** z
  const x = Math.min(n - 1, Math.floor(((lon + 180) / 360) * n))
  const s = Math.sin((lat * Math.PI) / 180)
  const y = Math.min(n - 1, Math.floor((0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * n))
  let k = ''
  for (let i = z; i > 0; i--) {
    const m = 1 << (i - 1)
    k += String((x & m ? 1 : 0) + (y & m ? 2 : 0))
  }
  return k
}

/** The quadkeys a box touches (sampled finely enough for zoom 9 tiles, ~70 km). */
export const quadkeysFor = (b: Bounds): string[] => {
  const keys = new Set<string>()
  for (let i = 0; i <= 8; i++) for (let j = 0; j <= 8; j++) {
    keys.add(quadkey(b.west + ((b.east - b.west) * i) / 8, b.south + ((b.north - b.south) * j) / 8))
  }
  return [...keys]
}

export interface Footprint {
  /** Outer ring, lon/lat, open. */
  readonly ring: Vec2[]
  /** Modelled height in metres, when the model gave one. */
  readonly height?: number
}

export const fetchFootprints = async (r: Region, dir: string, log = console.error): Promise<number> => {
  const b = fetchBounds(r)
  const keys = new Set(quadkeysFor(b))
  await mkdir(dir, { recursive: true })
  const tmp = join(dir, 'footprints.part')
  await run('curl', ['-sS', '-f', '-m', '120', '-A', 'isoscape/0.1', '-o', tmp, LINKS], { maxBuffer: 1 << 26 })
  const urls = (await readFile(tmp, 'utf8')).split('\n').slice(1).map((l) => l.split(',')).filter((c) => keys.has(c[1])).map((c) => c[2])
  const out: Footprint[] = []
  for (const url of urls) {
    log(`footprints ${url.split('quadkey=')[1]?.split('/')[0] ?? ''}`)
    await run('curl', ['-sS', '-f', '-m', '170', '-A', 'isoscape/0.1', '-o', tmp, url])
    for (const line of gunzipSync(await readFile(tmp)).toString('utf8').split('\n')) {
      if (!line.trim()) continue
      const f = JSON.parse(line) as { properties?: { height?: number }; geometry: { type: string; coordinates: number[][][] } }
      if (f.geometry.type !== 'Polygon') continue
      const ring = f.geometry.coordinates[0].map(([lon, lat]) => [Number(lon.toFixed(7)), Number(lat.toFixed(7))] as const)
      const c = ring.reduce((a, p) => [a[0] + p[0] / ring.length, a[1] + p[1] / ring.length], [0, 0])
      if (c[0] < b.west || c[0] > b.east || c[1] < b.south || c[1] > b.north) continue
      const h = f.properties?.height
      out.push({ ring: ring.slice(0, -1) as Vec2[], ...(h !== undefined && h > 0 ? { height: Number(h.toFixed(1)) } : {}) })
    }
  }
  await run('rm', ['-f', tmp]).catch(() => undefined)
  await writeFile(join(dir, 'footprints.json'), JSON.stringify({ source: 'Microsoft Global ML Building Footprints (ODbL)', footprints: out }))
  log(`${out.length} footprints in the region, ${out.filter((f) => f.height !== undefined).length} with a modelled height`)
  return out.length
}

export const loadFootprints = async (path: string): Promise<Footprint[] | null> => {
  try {
    return (JSON.parse(await readFile(path, 'utf8')) as { footprints: Footprint[] }).footprints
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return null
    throw error
  }
}

const inRing = (p: Vec2, ring: readonly Vec2[]): boolean => {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]
    const [xj, yj] = ring[j]
    if (yi > p[1] !== yj > p[1] && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) inside = !inside
  }
  return inside
}
const centre = (ring: readonly Vec2[]): Vec2 => ring.reduce<Vec2>((a, p) => [a[0] + p[0] / ring.length, a[1] + p[1] / ring.length], [0, 0])

/**
 * Footprints as building features, leaving out any that overlap an OSM building: a footprint
 * whose centre lies in an OSM building, or that holds an OSM building's centre.
 */
export const mergeFootprints = (osm: readonly PolygonFeature[], footprints: readonly Footprint[]): PolygonFeature[] => {
  const cell = 0.002
  const grid = new Map<string, PolygonFeature[]>()
  const keyOf = (p: Vec2) => `${Math.floor(p[0] / cell)},${Math.floor(p[1] / cell)}`
  for (const f of osm) {
    if (f.tags.building === undefined && f.tags['building:part'] === undefined) continue
    const k = keyOf(centre(f.outers[0]))
    const list = grid.get(k)
    if (list) list.push(f)
    else grid.set(k, [f])
  }
  const near = (p: Vec2) => {
    const [gx, gy] = [Math.floor(p[0] / cell), Math.floor(p[1] / cell)]
    const out: PolygonFeature[] = []
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) out.push(...(grid.get(`${gx + dx},${gy + dy}`) ?? []))
    return out
  }
  const merged: PolygonFeature[] = []
  footprints.forEach((fp, i) => {
    const c = centre(fp.ring)
    const clash = near(c).some((o) => inRing(c, o.outers[0]) || inRing(centre(o.outers[0]), fp.ring))
    if (clash) return
    merged.push({
      type: 'polygon',
      id: `m${i}`,
      tags: { building: 'yes', source: 'microsoft', ...(fp.height !== undefined ? { height: String(fp.height), 'height:source': 'model' } : {}) },
      outers: [fp.ring],
      inners: [],
    })
  })
  return merged
}
