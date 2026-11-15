/**
 * OpenStreetMap in, plain features out.
 *
 * `fetchOsm` asks Overpass for everything the renderer knows how to draw inside a region's
 * bounds and caches the raw answer under data/<region>/osm.json, so builds are repeatable and
 * offline. `parseOsm` turns that answer into polygons (closed ways and assembled
 * multipolygons) and lines, still in lon/lat. OSM data is © OpenStreetMap contributors, ODbL.
 */

import { execFile } from 'node:child_process'
import { access, mkdir, readFile, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { promisify } from 'node:util'
import type { Vec2 } from './geom.ts'
import { openRing, samePoint } from './geom.ts'
import { fetchBounds, type Region } from './region.ts'

const run = promisify(execFile)

export type Tags = Readonly<Record<string, string>>

export interface PolygonFeature {
  readonly type: 'polygon'
  readonly id: string
  readonly tags: Tags
  /** lon/lat rings, open (no repeated closing vertex). */
  readonly outers: Vec2[][]
  readonly inners: Vec2[][]
}

export interface LineFeature {
  readonly type: 'line'
  readonly id: string
  readonly tags: Tags
  readonly points: Vec2[]
}

export type Feature = PolygonFeature | LineFeature

const ALL_MIRRORS = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.private.coffee/api/interpreter',
  'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter',
]
/** Mirrors in the order tried. ISOSCAPE_OVERPASS_FIRST=<n> starts at the n-th, so parallel fetches can spread out. */
const first = Number(process.env.ISOSCAPE_OVERPASS_FIRST ?? 0) % ALL_MIRRORS.length
export const MIRRORS = [...ALL_MIRRORS.slice(first), ...ALL_MIRRORS.slice(0, first)]

export interface Bounds { readonly south: number; readonly west: number; readonly north: number; readonly east: number }

export const overpassQuery = (r: Region, b: Bounds = fetchBounds(r)): string => {
  const bbox = [b.south, b.west, b.north, b.east].map((n) => n.toFixed(5)).join(',')
  return `[out:json][timeout:170][bbox:${bbox}];
(
 way["building"]; relation["building"];
 way["building:part"]; relation["building:part"];
 nwr["natural"="water"]; nwr["water"]; nwr["waterway"="riverbank"];
 way["waterway"];
 way["highway"];
 way["railway"];
 nwr["leisure"~"^(park|garden|pitch|playground|nature_reserve)$"];
 nwr["landuse"~"^(grass|forest|cemetery|recreation_ground|meadow|railway|village_green)$"];
 nwr["natural"~"^(wood|scrub|grassland|wetland|bare_rock|sand|beach)$"];
 nwr["place"~"^(island|islet)$"];
 way["natural"="coastline"];
 nwr["amenity"="parking"];
 way["man_made"~"^(bridge|pier|dyke|embankment)$"];
 way["barrier"="wall"];
);
out geom;`
}

const postQuery = async (url: string, query: string): Promise<string> => {
  // curl honours the machine's proxy settings; Node's fetch does not, by default.
  try {
    const { stdout } = await run(
      'curl',
      ['-sS', '-m', '180', '-A', 'isoscape/0.1', '--data-urlencode', `data=${query}`, '-w', '\n%{http_code}', url],
      { maxBuffer: 1 << 30 },
    )
    const cut = stdout.lastIndexOf('\n')
    const code = stdout.slice(cut + 1).trim()
    if (code !== '200') throw new Error(`HTTP ${code}`)
    return stdout.slice(0, cut)
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error
    const res = await fetch(url, { method: 'POST', body: new URLSearchParams({ data: query }) })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.text()
  }
}

/** Ask each mirror in turn, backing off between rounds; Overpass is often at capacity. */
const askOverpass = async (query: string, rounds: number, log: (m: string) => void): Promise<string> => {
  for (let round = 0; round < rounds; round++) {
    for (const url of MIRRORS) {
      try {
        const body = await postQuery(url, query)
        // A timed-out transfer can arrive with a 200 and a truncated body: parse to be sure.
        const parsed = JSON.parse(body) as { elements?: unknown }
        if (!Array.isArray(parsed.elements)) throw new Error('not an Overpass JSON answer')
        log(`  ${(body.length / 1e6).toFixed(1)} MB from ${new URL(url).host}`)
        return body
      } catch (error) {
        log(`  ${new URL(url).host}: ${(error as Error).message.split('\n')[0]}`)
      }
    }
    if (round + 1 < rounds) {
      const wait = 15 * (round + 1)
      log(`  all mirrors busy; retrying in ${wait}s`)
      await new Promise((done) => setTimeout(done, wait * 1000))
    }
  }
  throw new Error('Overpass did not answer. Run fetch again later; finished tiles are kept.')
}

/** Cut the fetch bounds into tiles no bigger than `size` meters a side. */
export const tilesFor = (b: Bounds, size = 1600): Bounds[] => {
  const kx = 111_320 * Math.cos((((b.north + b.south) / 2) * Math.PI) / 180)
  const cols = Math.max(1, Math.ceil(((b.east - b.west) * kx) / size))
  const rows = Math.max(1, Math.ceil(((b.north - b.south) * 110_574) / size))
  const out: Bounds[] = []
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      out.push({
        south: b.south + ((b.north - b.south) * j) / rows,
        north: b.south + ((b.north - b.south) * (j + 1)) / rows,
        west: b.west + ((b.east - b.west) * i) / cols,
        east: b.west + ((b.east - b.west) * (i + 1)) / cols,
      })
    }
  }
  return out
}

/**
 * Fetch a region's OSM data tile by tile into `<dir>/osm-tiles/`, keeping every finished tile,
 * then merge them into `<dir>/osm.json`. A big region takes several minutes and Overpass is
 * often busy, so this resumes: run it again and only the missing tiles are asked for.
 * With `budgetSeconds`, it stops starting new tiles once that much time has passed.
 */
export const fetchOsm = async (
  r: Region,
  dir: string,
  options: { budgetSeconds?: number; rounds?: number; log?: (m: string) => void } = {},
): Promise<{ done: number; total: number }> => {
  const log = options.log ?? console.error
  const tiles = tilesFor(fetchBounds(r), r.fetchTile)
  const tileDir = join(dir, 'osm-tiles')
  await mkdir(tileDir, { recursive: true })
  const t0 = Date.now()
  let done = 0
  // A tile's cache file is named by its bounds, so changing the frame never reuses a tile
  // that covers somewhere else.
  const nameOf = (t: Bounds) => [t.south, t.west, t.north, t.east].map((n) => n.toFixed(5)).join('_') + '.json'
  for (let k = 0; k < tiles.length; k++) {
    const path = join(tileDir, nameOf(tiles[k]))
    if (await exists(path)) { done++; continue }
    if (options.budgetSeconds !== undefined && (Date.now() - t0) / 1000 > options.budgetSeconds) break
    log(`tile ${k + 1}/${tiles.length}`)
    await writeFile(path, await askOverpass(overpassQuery(r, tiles[k]), options.rounds ?? 3, log))
    done++
  }
  if (done === tiles.length) {
    // Merge, keeping one copy of anything that more than one tile returned.
    const seen = new Set<string>()
    const elements: unknown[] = []
    for (let k = 0; k < tiles.length; k++) {
      const part = JSON.parse(await readFile(join(tileDir, nameOf(tiles[k])), 'utf8')) as { elements: { type: string; id: number }[] }
      for (const e of part.elements) {
        const key = `${e.type}/${e.id}`
        if (seen.has(key)) continue
        seen.add(key)
        elements.push(e)
      }
    }
    await writeFile(join(dir, 'osm.json'), JSON.stringify({ version: 0.6, generator: 'isoscape (merged Overpass tiles)', copyright: 'OpenStreetMap contributors, ODbL', elements }))
    log(`merged ${tiles.length} tiles: ${elements.length} elements`)
  } else {
    log(`${done} of ${tiles.length} tiles fetched; run fetch again to continue`)
  }
  return { done, total: tiles.length }
}

const exists = async (path: string) => {
  try {
    await access(path)
    return true
  } catch {
    return false
  }
}

interface RawGeom {
  readonly lat: number
  readonly lon: number
}
interface RawElement {
  readonly type: 'node' | 'way' | 'relation'
  readonly id: number
  readonly tags?: Record<string, string>
  readonly geometry?: (RawGeom | null)[]
  readonly members?: { type: string; role: string; geometry?: (RawGeom | null)[] }[]
}

const toLonLat = (g: (RawGeom | null)[] | undefined): Vec2[] =>
  (g ?? []).filter((p): p is RawGeom => p !== null).map((p) => [p.lon, p.lat] as const)

const isClosed = (pts: readonly Vec2[]) => pts.length >= 4 && samePoint(pts[0], pts[pts.length - 1])

/** Tags that make a closed way an area even without `area=yes`. */
const AREA_KEYS = ['building', 'building:part', 'landuse', 'leisure', 'natural', 'amenity', 'place', 'water']

const isArea = (tags: Tags): boolean => {
  if (tags.area === 'no') return false
  if (tags.area === 'yes') return true
  if (tags.waterway === 'riverbank' || tags.waterway === 'dock') return true
  if (tags.natural === 'tree_row' || tags.natural === 'coastline') return false
  return AREA_KEYS.some((k) => k in tags)
}

/**
 * Join way fragments end to end into closed rings. Fragments that cannot be closed are
 * dropped: a river relation cut by the query's bounds is the usual cause, and the clip to
 * the frame repairs the rest.
 */
export const assembleRings = (parts: Vec2[][]): Vec2[][] => {
  const pool = parts.filter((p) => p.length >= 2).map((p) => p.slice())
  const rings: Vec2[][] = []
  while (pool.length > 0) {
    let ring = pool.pop()!
    let grew = true
    while (!isClosed(ring) && grew) {
      grew = false
      const end = ring[ring.length - 1]
      for (let i = 0; i < pool.length; i++) {
        const cand = pool[i]
        if (samePoint(cand[0], end)) ring = ring.concat(cand.slice(1))
        else if (samePoint(cand[cand.length - 1], end)) ring = ring.concat(cand.slice(0, -1).reverse())
        else continue
        pool.splice(i, 1)
        grew = true
        break
      }
    }
    if (isClosed(ring)) rings.push(openRing(ring))
  }
  return rings
}

export const parseOsm = (json: string): Feature[] => {
  const data = JSON.parse(json) as { elements: RawElement[] }
  const features: Feature[] = []
  for (const el of data.elements) {
    const tags = el.tags ?? {}
    if (el.type === 'way') {
      const pts = toLonLat(el.geometry)
      if (pts.length < 2) continue
      if (isClosed(pts) && isArea(tags)) {
        features.push({ type: 'polygon', id: `w${el.id}`, tags, outers: [openRing(pts)], inners: [] })
      } else {
        features.push({ type: 'line', id: `w${el.id}`, tags, points: pts })
      }
    } else if (el.type === 'relation' && (tags.type === 'multipolygon' || tags.type === 'building')) {
      const members = el.members ?? []
      const outers = assembleRings(members.filter((m) => m.type === 'way' && m.role !== 'inner').map((m) => toLonLat(m.geometry)))
      const inners = assembleRings(members.filter((m) => m.type === 'way' && m.role === 'inner').map((m) => toLonLat(m.geometry)))
      if (outers.length > 0) features.push({ type: 'polygon', id: `r${el.id}`, tags, outers, inners })
    }
  }
  return features
}
