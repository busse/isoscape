/**
 * A region is a frame on the world: where the camera stands, which way it looks, and how big
 * a rectangle of ground it sees. Everything else (what to fetch, what to draw) follows from it.
 */

import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import type { Figure } from './traveler.ts'

export interface BridgeRule {
  /** Case-insensitive substring of the way's `name` (or `bridge:name`). */
  readonly match: string
  /** Deck height above the water or ground, in meters. */
  readonly deck: number
  /** Meters between piers (default 38). Suspension bridges want a long spacing: two towers, not a wall of piers. */
  readonly pierSpacing?: number
  /**
   * Meters of each end of the deck that stand on an abutment, the deck's side walled down to the
   * ground: with a long pier spacing, a deck that climbs off a bluff then does not hang out from
   * its first pier.
   */
  readonly abutment?: number
}

export interface Region {
  readonly name: string
  readonly title: string
  /** [lon, lat] of the frame's center. */
  readonly center: readonly [number, number]
  /** Meters across the frame (left to right on screen). */
  readonly width: number
  /** Meters into the frame (near edge to far edge). */
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
  /** Pixels per meter across the frame. */
  readonly scale: number
  /** Ground foreshortening, the sine of the camera's tilt: 0.5 is the classic 2:1 view. */
  readonly squash?: number
  /** Vertical exaggeration on top of the true value for this tilt. */
  readonly exaggeration?: number
  /** Thickness of the diorama's ground slab, in meters. 0 for none. */
  readonly slab?: number
  readonly palette?: string
  /** Default deck height for bridges with no matching rule, meters per OSM `layer`. */
  readonly bridgeDeck?: number
  readonly bridges?: readonly BridgeRule[]
  /**
   * Rail bridges stand on piers over water however low their deck (a set's maps): without it a
   * pier is drawn only where the deck stands more than 3 m above its foot.
   */
  readonly railPiersOverWater?: boolean
  /** The two ways of a double-track viaduct are drawn as one deck at one level (a set's maps). */
  readonly groupRailDecks?: boolean
  /**
   * Meters: where two rail decks cross, the one with the higher OSM `layer` passes at least this
   * far over the other (the lower dipped toward the ground there, then the upper raised, each at
   * a 3% grade), so a crossing of railroads at three levels reads (a set's maps).
   */
  readonly railCrossings?: number
  /** The halo round map labels, as a share of their size (default 0.22): wider over dense blocks. */
  readonly labelHalo?: number
  /** Leave out the cars and ramp houses under a modeled station's shed roofs (a close view of its front). */
  readonly hideUnderSheds?: boolean
  /** Ground ribbons (roads, paths, track) filled round at their bends, so no wedge opens on a bend's outside (a set's views). */
  readonly ribbonJoins?: boolean
  /** Meters: tie marks are drawn on only one of tracks this close (default TIE_RUN_CLEAR, 3.5). */
  readonly tieRunClear?: number
  /**
   * Extra data, beyond OSM and elevation. `buildings` lists where footprints come from:
   * OpenStreetMap and/or Microsoft's ML footprints (OSM wins where both have a building).
   * `landcover: 'nlcd'` draws woods, wetlands, fields and crops from the National Land Cover
   * Database, where OSM's own land use is thin.
   */
  readonly sources?: { readonly buildings?: readonly ('osm' | 'microsoft')[]; readonly landcover?: 'nlcd' }
  /** OSM is fetched in tiles no bigger than this, in meters a side. Default 1600; sparse
   * rural regions can take much bigger tiles. */
  readonly fetchTile?: number
  /** Smallest building footprint kept, in square meters. */
  readonly minBuildingArea?: number
  /** Which vertices get dots: every visible corner, roof corners only, or none. */
  readonly dots?: 'all' | 'roof' | 'none'
  /**
   * Seat a building that spans water (`layer` 1 or more, water under its center) on its banks:
   * its height counts from the ground at its corners on land, not the water's bed (`spansWater`
   * in scene.ts). Off unless set, so plates already sold redraw exactly as they were.
   */
  readonly seatOnBanks?: boolean
  /**
   * Draw a building of ordinary floors by its levels when its tagged height is more than
   * `MAX_LEVEL_HEIGHT` a level (classify.ts). Off unless set, like `seatOnBanks`.
   */
  readonly checkLevels?: boolean
  /** Use another region's cached data (data/<name>/) instead of this region's own. */
  readonly data?: string
  /**
   * A dated series: a history file (epochs, cited curated features, era rules for roads and
   * water) and where each building's year built comes from beyond OSM's own start_date.
   */
  readonly time?: {
    readonly history: string
    /** `credit`: how prints and pages credit the year-built records, when any date comes from them. */
    readonly yearBuilt?: { readonly url: string; readonly field: string; readonly credit?: string }
  }
  /** Draw the ground with relief from data/<region>/dem.bin.gz. Omit for a flat plate. */
  readonly terrain?: TerrainOptions
  /** Open a modeled building along a vertical plane: see `Cutaway`. */
  readonly cutaway?: Cutaway
}

/**
 * A cutaway: the curated parts of a dated scene cut by a vertical plane, the half on one side
 * lifted away. Only parts drawn with `only: 'cutaway'` or with no `only` take part, and only
 * those whose id starts with `parts`. See "Cutaways" in the README.
 */
export interface Cutaway {
  /** A point on the plane, [lon, lat]. */
  readonly through: readonly [number, number]
  /** Compass bearing the plane runs along, in degrees. */
  readonly bearing: number
  /** The side of that bearing lifted away. The camera should stand on it. */
  readonly remove: 'left' | 'right'
  /** On the removed side, keep what stands up to `keep` meters above the elevation `floor` (a plan of that floor). */
  readonly floor?: number
  readonly keep?: number
  /** Id prefix of the parts that are cut (default: every modeled part). */
  readonly parts?: string
  /** Items lifted away whole even though they are not cut (a shed over the nearest platform): regular expressions on item ids. */
  readonly lift?: readonly string[]
  /**
   * Outline, dashed on the ground, the removed side of the union of these parts' footprints
   * (id prefixes; convex footprints), pushed `offset` meters out.
   */
  readonly outline?: { readonly parts: readonly string[]; readonly offset?: number }
  /**
   * Travelers drawn to scale in the cutaway (src/traveler.ts): where each stands, the floor it
   * stands on (m above sea level; on the ground where none is given), and which way it faces
   * across the picture (1 right, -1 left); `figure`, a visitor in place of the traveler
   * (src/traveler.ts).
   */
  readonly travelers?: readonly { readonly at: readonly [number, number]; readonly floor?: number; readonly facing: 1 | -1; readonly figure?: Figure }[]
  /**
   * The traveler's way in the cutaway, as the flat section's `route` draws it: points [lon, lat,
   * elevation in meters above sea level] (waist height), drawn in the route's color and dashed,
   * dash by dash, so each sorts among what stands near it. `weight` scales the palette's route
   * width and dash, so that on a sheet, where the cutaway and the section are scaled differently,
   * the two read alike (the section's scale on the sheet over the cutaway's).
   */
  readonly route?: { readonly points: readonly (readonly [number, number, number])[]; readonly weight?: number }
  /**
   * A second way, drawn as `route` is but in the palette's `pumped` color: the water a works
   * lifts, beside the water that drives it (the Pump House). Its section has `section.pumped`.
   */
  readonly pumped?: { readonly points: readonly (readonly [number, number, number])[]; readonly weight?: number }
  /** How a cycle in the paint order is broken: `components` at its start (see `paintOrder`); by default, at the farthest item left. */
  readonly order?: 'components'
  /**
   * The flat section: the same plane, seen square on, everything on the removed side gone.
   * `from` and `to` are its ends, in meters along the plane from `through`; `beyond` is how far
   * behind the plane the cut parts are drawn, `other` how far everything else is.
   */
  readonly section?: {
    readonly from: number
    readonly to: number
    readonly beyond?: number
    readonly other?: number
    readonly scale?: number
    /** Floor of the earth drawn under the section, in meters below the lowest ground. */
    readonly earth?: number
    /** The traveler's path: points [meters along the plane, elevation in meters above sea level]. */
    readonly route?: readonly (readonly [number, number])[]
    /** The second way (`cutaway.pumped`), in the palette's `pumped` color: points as `route`'s. */
    readonly pumped?: readonly (readonly [number, number])[]
    /**
     * Draw the ways as water rather than as dashes: a pale band under a thin line with
     * arrowheads, the route in the palette's `drive` teal and `pumped` in its blue, each end
     * tagged with `routeEnds` / `pumpedEnds` ([in, out] labels, e.g. "IN: FOREBAY").
     */
    readonly ribbon?: boolean
    readonly routeEnds?: readonly [string, string]
    readonly pumpedEnds?: readonly [string, string]
    /**
     * Stairs hidden from the plane behind a wall (regular expressions on item ids): drawn as
     * their dashed outline, as a stair on the side lifted away is.
     */
    readonly hidden?: readonly string[]
    /**
     * Parts drawn only in a thin slice behind the plane (regular expressions on item ids, and
     * the slice's depth in meters, default 1): a roof seen from beneath would otherwise hide
     * the trusses under it; this way only its cut and the edge next to it show.
     */
    readonly slice?: { readonly parts: readonly string[]; readonly depth?: number }
    /** Travelers on the path: meters along the plane, the floor's elevation, and facing (1 toward `to`). */
    readonly travelers?: readonly { readonly s: number; readonly floor: number; readonly facing: 1 | -1; readonly figure?: Figure }[]
  }
}

export interface TerrainOptions {
  /** Draw terrain at all, given elevation data. Default true. */
  readonly enabled?: boolean
  /** Vertical exaggeration of the ground (buildings keep their true heights). */
  readonly exaggeration?: number
  /** Grid spacing in meters for the draped surface, shading and contours. */
  readonly cell?: number
  /** Contour interval in meters; 0 for none. */
  readonly contour?: number
  /** Every n-th contour is drawn heavier. */
  readonly majorEvery?: number
  /** Water-surface gradient (m/m) above which a stretch of river reads as rapids. */
  readonly rapids?: number
  /** The most rapids strokes drawn in one cell (default 2): 1 where a coarse grid seen close would pile them up. */
  readonly rapidsMarks?: number
  /**
   * Strength of the hillshade, 1 by default; 0 draws the ground flat-toned (its relief still
   * shapes it). A close view of one building, such as a cutaway, uses 0, so a bank does not
   * read as a stain.
   */
  readonly shade?: number
  /** Mark rock standing clear of the water. Default true; off for tidal flats and shoals. */
  readonly rocks?: boolean
  /** Meters per pixel to fetch the elevation at. Default 1 (or the source's native spacing, if coarser); coarser keeps big regions small. */
  readonly demResolution?: number
  /**
   * Where the heights come from (see `dem-sources.ts`): `3dep` (USGS, the US; the default),
   * `ign` (France), `swisstopo` (Switzerland), `gsi` (Japan), `copernicus` (worldwide, 30 m)
   * or `terrain-tiles` (worldwide mosaic of national models, on AWS).
   */
  readonly source?: '3dep' | 'ign' | 'swisstopo' | 'gsi' | 'copernicus' | 'terrain-tiles'
  /** A second source for whatever the first leaves empty (a national model stops at the border). */
  readonly fillFrom?: '3dep' | 'ign' | 'swisstopo' | 'gsi' | 'copernicus' | 'terrain-tiles'
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

/** Local east/north meters about the region center: equirectangular, fine at city scale. */
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
