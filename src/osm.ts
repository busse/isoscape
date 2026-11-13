/**
 * OpenStreetMap in, plain features out.
 *
 * `fetchOsm` asks Overpass for everything the renderer knows how to draw inside a region's
 * bounds and caches the raw answer under data/<region>/osm.json, so builds are repeatable and
 * offline. `parseOsm` turns that answer into polygons (closed ways and assembled
 * multipolygons) and lines, still in lon/lat. OSM data is © OpenStreetMap contributors, ODbL.
 */

import { execFile } from 'node:child_process'
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname } from 'node:path'
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

export const MIRRORS = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.private.coffee/api/interpreter',
  'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter',
]

export const overpassQuery = (r: Region): string => {
  const b = fetchBounds(r)
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
export const fetchOsm = async (r: Region, out: string, rounds = 6, log = console.error): Promise<void> => {
  const query = overpassQuery(r)
  for (let round = 0; round < rounds; round++) {
    for (const url of MIRRORS) {
      try {
        const body = await postQuery(url, query)
        if (!body.trimStart().startsWith('{') || !body.includes('"elements"')) throw new Error('not an Overpass JSON answer')
        await mkdir(dirname(out), { recursive: true })
        await writeFile(out, body)
        log(`fetched ${(body.length / 1e6).toFixed(1)} MB from ${new URL(url).host}`)
        return
      } catch (error) {
        log(`${new URL(url).host}: ${(error as Error).message.split('\n')[0]}`)
      }
    }
    const wait = 15 * (round + 1)
    log(`all mirrors busy; retrying in ${wait}s`)
    await new Promise((done) => setTimeout(done, wait * 1000))
  }
  throw new Error('Overpass did not answer. Try again later, or save a query result to the cache path by hand.')
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
