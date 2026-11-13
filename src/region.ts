/**
 * A region is a frame on the world: where the camera stands, which way it looks, and how big
 * a rectangle of ground it sees. Everything else (what to fetch, what to draw) follows from it.
 */

import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

export interface BridgeRule {
  /** Case-insensitive substring of the way's `name` (or `bridge:name`). */
  readonly match: string
  /** Deck height above the water or ground, in metres. */
  readonly deck: number
}

export interface Region {
  readonly name: string
  readonly title: string
  /** [lon, lat] of the frame's centre. */
  readonly center: readonly [number, number]
  /** Metres across the frame (left to right on screen). */
  readonly width: number
  /** Metres into the frame (near edge to far edge). */
  readonly depth: number
  /**
   * Compass direction the camera faces, in degrees: 0 looks north, so north is up the
   * screen. With `snap`, this is a starting point that may move by up to 45°.
   */
  readonly bearing: number
  /**
   * Turn the camera (by at most 45°) so the dominant street grid runs along the isometric
   * diagonals, which is what makes a city read as a SimCity-style grid of diamonds.
   * Pass a number instead to fix the bearing exactly and skip the search.
   */
  readonly snap?: boolean
  /** Pixels per metre across the frame. */
  readonly scale: number
  /** Ground foreshortening, the sine of the camera's tilt: 0.5 is the classic 2:1 view. */
  readonly squash?: number
  /** Vertical exaggeration on top of the true value for this tilt. */
  readonly exaggeration?: number
  /** Thickness of the diorama's ground slab, in metres. 0 for none. */
  readonly slab?: number
  readonly palette?: string
  /** Default deck height for bridges with no matching rule, metres per OSM `layer`. */
  readonly bridgeDeck?: number
  readonly bridges?: readonly BridgeRule[]
  /** Smallest building footprint kept, in square metres. */
  readonly minBuildingArea?: number
  /** Which vertices get dots: every visible corner, roof corners only, or none. */
  readonly dots?: 'all' | 'roof' | 'none'
  /** Use another region's cached data (data/<name>/) instead of this region's own. */
  readonly data?: string
  /** Draw the ground with relief from data/<region>/dem.bin.gz. Omit for a flat plate. */
  readonly terrain?: TerrainOptions
}

export interface TerrainOptions {
  /** Draw terrain at all, given elevation data. Default true. */
  readonly enabled?: boolean
  /** Vertical exaggeration of the ground (buildings keep their true heights). */
  readonly exaggeration?: number
  /** Grid spacing in metres for the draped surface, shading and contours. */
  readonly cell?: number
  /** Contour interval in metres; 0 for none. */
  readonly contour?: number
  /** Every n-th contour is drawn heavier. */
  readonly majorEvery?: number
  /** Water-surface gradient (m/m) above which a stretch of river reads as rapids. */
  readonly rapids?: number
}

export const loadRegion = async (name: string, root = process.cwd()): Promise<Region> => {
  const path = resolve(root, 'regions', `${name}.json`)
  const raw = JSON.parse(await readFile(path, 'utf8')) as Partial<Region>
  for (const key of ['center', 'width', 'depth', 'scale'] as const) {
    if (raw[key] === undefined) throw new Error(`regions/${name}.json: missing "${key}"`)
  }
  return { bearing: 0, snap: true, title: name, ...raw, name } as Region
}

const M_PER_DEG_LAT = 110_574

/**
 * The lon/lat box that covers the frame at *any* bearing, so a snapped camera never looks
 * past the data. It is the bounding box of the frame's circumscribed circle.
 */
export const fetchBounds = (r: Region): { south: number; west: number; north: number; east: number } => {
  const radius = Math.hypot(r.width, r.depth) / 2 + 50
  const [lon, lat] = r.center
  const dLat = radius / M_PER_DEG_LAT
  const dLon = radius / (111_320 * Math.cos((lat * Math.PI) / 180))
  return { south: lat - dLat, west: lon - dLon, north: lat + dLat, east: lon + dLon }
}

/** Local east/north metres about the region centre: equirectangular, fine at city scale. */
export const localMetres = (r: Region) => {
  const [lon0, lat0] = r.center
  const kx = 111_320 * Math.cos((lat0 * Math.PI) / 180)
  return (lon: number, lat: number): [number, number] => [(lon - lon0) * kx, (lat - lat0) * M_PER_DEG_LAT]
}

export const lonLatFromLocal = (r: Region) => {
  const [lon0, lat0] = r.center
  const kx = 111_320 * Math.cos((lat0 * Math.PI) / 180)
  return (e: number, n: number): [number, number] => [lon0 + e / kx, lat0 + n / M_PER_DEG_LAT]
}
