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
  /** Metres between piers (default 38). Suspension bridges want a long spacing: two towers, not a wall of piers. */
  readonly pierSpacing?: number
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
   * Set it to false to keep `bearing` exactly as given.
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
  /**
   * Extra data, beyond OSM and elevation. `buildings` lists where footprints come from:
   * OpenStreetMap and/or Microsoft's ML footprints (OSM wins where both have a building).
   * `landcover: 'nlcd'` draws woods, wetlands, fields and crops from the National Land Cover
   * Database, where OSM's own land use is thin.
   */
  readonly sources?: { readonly buildings?: readonly ('osm' | 'microsoft')[]; readonly landcover?: 'nlcd' }
  /** OSM is fetched in tiles no bigger than this, in metres a side. Default 1600; sparse
   * rural regions can take much bigger tiles. */
  readonly fetchTile?: number
  /** Smallest building footprint kept, in square metres. */
  readonly minBuildingArea?: number
  /** Which vertices get dots: every visible corner, roof corners only, or none. */
  readonly dots?: 'all' | 'roof' | 'none'
  /** Use another region's cached data (data/<name>/) instead of this region's own. */
  readonly data?: string
  /**
   * A dated series: a history file (epochs, cited curated features, era rules for roads and
   * water) and where each building's year built comes from beyond OSM's own start_date.
   */
  readonly time?: {
    readonly history: string
    readonly yearBuilt?: { readonly url: string; readonly field: string }
  }
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
  /** Mark rock standing clear of the water. Default true; off for tidal flats and shoals. */
  readonly rocks?: boolean
  /** Metres per pixel to fetch the elevation at. Default 1; coarser keeps big regions small. */
  readonly demResolution?: number
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
 * The lon/lat box the data must cover. With a fixed bearing it is the box around the rotated
 * frame; with `snap` the bearing is not known until the data is in, so it is the box around
 * the frame's circumscribed circle, which covers any bearing.
 */
export const fetchBounds = (r: Region): { south: number; west: number; north: number; east: number } => {
  const [lon, lat] = r.center
  const kx = 111_320 * Math.cos((lat * Math.PI) / 180)
  const margin = 60
  let halfE: number
  let halfN: number
  if (r.snap === false) {
    const b = (r.bearing * Math.PI) / 180
    const w = r.width / 2 + margin
    const d = r.depth / 2 + margin
    halfE = Math.abs(w * Math.cos(b)) + Math.abs(d * Math.sin(b))
    halfN = Math.abs(w * Math.sin(b)) + Math.abs(d * Math.cos(b))
  } else {
    halfE = halfN = Math.hypot(r.width, r.depth) / 2 + margin
  }
  return { south: lat - halfN / M_PER_DEG_LAT, west: lon - halfE / kx, north: lat + halfN / M_PER_DEG_LAT, east: lon + halfE / kx }
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
