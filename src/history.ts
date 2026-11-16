/**
 * Time: drawing a place as it stood in a given year.
 *
 * Two kinds of evidence go into a dated scene, and they are kept apart:
 *
 * - *Measured*: today's buildings, each dated by its OSM `start_date` or, failing that, by the
 *   year built the city assessor records for the parcel under it. A building appears in every
 *   scene from its year on. This only ever shows what survives: a building torn down in 1950
 *   is in none of the scenes, because nothing today records it.
 * - *Curated*: a short, cited list of what is gone or was different (a filled canal basin, a
 *   burned district, a demolished landmark, a buried creek), and rules giving the years that
 *   roads, rail and water ways existed. Each entry carries its sources; positions are drawn
 *   from today's street grid and published dimensions, not surveyed.
 *
 * The ground itself is today's: the elevation model includes every cut and fill since.
 */

import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { join } from 'node:path'
import { centroid, pointInRing, type Vec2 } from './geom.ts'
import type { Feature, PolygonFeature, Tags } from './osm.ts'
import { fetchBounds, type Region } from './region.ts'

export interface Epoch {
  readonly year: number
  readonly title: string
  readonly note?: string
}

/** A curated thing that existed from `from` until (not including) `to`. */
export interface HistoryFeature {
  readonly id: string
  readonly name: string
  readonly kind: 'water' | 'burned' | 'plan' | 'landmark' | 'creek' | 'streetcar' | 'grounds' | 'track' | 'rail' | 'platform' | 'canopy' | 'site' | 'wood' | 'label'
  readonly from: number
  readonly to?: number
  /** lon/lat outline (open), for areas and landmarks. */
  readonly ring?: Vec2[]
  /** lon/lat center line, for creeks and streetcar lines (a streetcar line may hold several runs: `lines`). */
  readonly line?: Vec2[]
  readonly lines?: Vec2[][]
  /** Streetcar lines: the line's name, for the explorer, and the operator. */
  readonly route?: string
  /** Landmark height in meters; for a canopy, the height of its roof. */
  readonly height?: number
  /**
   * A landmark drawn as one part of a modeled building: it stands `base` meters above its seat,
   * the lowest ground under it (`seat: 'max'`: the highest, for a part carried over lower
   * ground, such as a concourse over tracks); `shape: 'dome'` rounds it to a dome; `tone`
   * paints it from the palette's `parts` instead of the lost-landmark tone. `on` names another
   * part it rests on: its seat is then that part's top, so parts that share a support (the
   * columns on a porch, an entablature on its columns) share one level on sloping ground.
   */
  readonly base?: number
  readonly seat?: 'min' | 'max'
  readonly on?: string
  readonly shape?: 'prism' | 'dome' | 'revolve' | 'stair' | 'arch' | 'inset' | 'frame' | 'track'
  readonly tone?: PartTone
  /**
   * Which views draw the part: `whole` only those without a cutaway (a building's massing),
   * `cutaway` only those with one (its walls, floors and rooms). Absent: both.
   */
  readonly only?: 'whole' | 'cutaway'
  /** The part's bottom at this elevation (meters above sea level), instead of on its seat. */
  readonly elevation?: number
  /** The part's top at this elevation, instead of `height` above its bottom. */
  readonly upTo?: number
  /**
   * `revolve`: levels of a solid of revolution about the ring's centroid, each [height above the
   * part's bottom, outer radius, inner radius], radii as fractions of the ring's (0 inside: solid).
   */
  readonly levels?: readonly (readonly [number, number, number])[]
  /**
   * `frame`: straight members in the vertical plane over the ring's first edge (a truss, a
   * bracket, a roof slope), each [u0, z0, u1, z1, depth]: from u0 to u1 meters along that edge
   * from its start, at z0 and z1 meters above the part's bottom, `depth` deep in that plane,
   * and as thick as the ring's second edge is long. `inset` uses `levels` as [height, outer
   * inset, inner inset] in meters in from the ring (a hipped roof, a square dome; an inner inset
   * past the middle is solid). `track`: ties and two rails on the ring, from its first edge
   * (across the track) along its second.
   */
  readonly members?: readonly (readonly number[])[]
  /**
   * `stair`: the number of treads; it rises from the ring's first edge to its third. `arch`: an
   * arched window on the ring's first edge (its span), rising to a half ellipse at the top.
   */
  readonly steps?: number
  /** A part standing inside a roof shell (that part's id): see `Item.within`. */
  readonly within?: string
  /** How the part is known: see `confidenceOf`. */
  readonly confidence?: Confidence
  /**
   * A label written on the map: `name` at the point `at` (lon/lat), with an optional second
   * line, `caption`, set from its start, middle or end.
   */
  readonly at?: Vec2
  readonly caption?: string
  readonly anchor?: 'start' | 'middle' | 'end'
  /**
   * A rail line: a train standing on it, `at` meters from the line's start. A line with an
   * `elevation` is carried on a deck (an elevated track): its train stands there, and it is not
   * drawn on the ground (its deck and rails are modeled parts).
   */
  readonly train?: Train
  /** The train a cutaway draws here instead: a close view places its train to be seen. */
  readonly cutTrain?: Train
  /** Width in meters: a creek's, a curated rail line's ballast (default 3.2), a canopy's roof. */
  readonly width?: number
  /** From this year a landmark stands as a burned shell. */
  readonly ruin?: number
  /** A `plan`: draw only the streets inside it while it stands. */
  readonly limitsStreets?: boolean
  readonly note: string
  readonly sources: readonly string[]
}

/**
 * How a part is known: `drawn` from a plan, a section or a survey map; `written` from a written
 * account; `approximate` where nothing shows it (its place or size inferred).
 */
export type Confidence = 'drawn' | 'written' | 'approximate'

/** A part's confidence: what it says, or `approximate` when it says nothing. */
export const confidenceOf = (h: { readonly confidence?: Confidence }): Confidence => h.confidence ?? 'approximate'

export type PartTone = 'stone' | 'dome' | 'iron' | 'ramp' | 'coach' | 'engine' | 'freight' | 'plaster' | 'floor' | 'wood' | 'glass' | 'tram' | 'roof' | 'loco' | 'coal' | 'carRoof' | 'brick' | 'tile' | 'steel' | 'ballast' | 'diesel'

/**
 * A train on a curated rail line: an engine (unless `engine` is false) and `cars` cars behind
 * it, from `at` meters along the line, running toward its end (or its start, with `reverse`).
 */
export interface Train {
  readonly cars: number
  readonly at: number
  readonly engine?: boolean
  /** The engine: a steam engine and its tender (the default), or a diesel unit. */
  readonly power?: 'steam' | 'diesel'
  readonly kind?: 'coach' | 'freight'
  readonly reverse?: boolean
}

/** Which years a kind of map feature existed: the first rule that matches decides. */
export interface Rule {
  readonly where: {
    /** Case-insensitive substring of `name` or `ref`. */
    readonly name?: string
    /** Tag key, with `is` listing values (any value when `is` is absent). */
    readonly tag?: string
    readonly is?: readonly string[]
    readonly type?: 'line' | 'polygon'
    /** Only bridges (true) or only what is not a bridge (false). */
    readonly bridge?: boolean
    /** OSM ids, such as "w1485004507": for a way a curated feature stands in for. */
    readonly id?: readonly string[]
  }
  /** Spans [from, to): null for an open end. An empty list means "not dated: today only". */
  readonly eras: readonly (readonly [number | null, number | null])[]
  readonly note?: string
  readonly sources?: readonly string[]
}

/** A building traced from a historic map that no longer stands, with the span it is drawn for. */
export interface TracedBuilding {
  readonly id: string
  readonly ring: Vec2[]
  /** First edition it appears on; it may be older. */
  readonly from: number
  /** First year it is known (or assumed) to be gone. */
  readonly to: number
  /** How `to` was found: a later map without it, a building on its site, a highway, or assumed. */
  readonly end: 'map' | 'rebuilt' | 'highway' | 'assumed'
  readonly material: 'brick' | 'frame' | 'stone' | 'iron' | 'special' | 'fireproof'
  readonly storeys: number
  readonly edition: number
  readonly sheet: number
}

export interface History {
  readonly epochs: readonly Epoch[]
  readonly features: readonly HistoryFeature[]
  readonly rules: readonly Rule[]
  /** The year that counts as today: undated buildings appear in this scene only. */
  readonly present: number
  /** Curated years built for particular OSM buildings, which win over every other date. */
  readonly dates: readonly { readonly id: string; readonly name?: string; readonly year: number; readonly until?: number; readonly source: string; readonly note?: string }[]
  /** Fire-insurance maps traced into footprints: the editions used, and the buildings since lost. */
  readonly sanborn?: { readonly lost: string | readonly string[]; readonly editions: readonly number[]; readonly source: string }
  readonly traced: readonly TracedBuilding[]
  /**
   * Minor streets (tertiary, residential, service, unclassified, living streets and paths) drawn only
   * where a building of the year stands within this many meters: a street with no house on it
   * yet is taken as not yet laid out. Larger roads follow the era rules as usual.
   */
  readonly streetsNearBuildings?: number
  /**
   * Hold main roads (trunk, primary, secondary) to the same test: for a series whose early
   * scenes have no map of the town's extent but its surviving buildings and its plan.
   */
  readonly majorStreetsNearBuildings?: boolean
  /**
   * Draw streetcar lines and cars this many times life size, so they read in a city-wide view
   * (default 1).
   */
  readonly streetcarScale?: number
  /** Draw railroad tracks this many times their width, and in the ties' darker tone, so the network reads from afar (default 1). */
  readonly railScale?: number
}

export const loadHistory = async (path: string): Promise<History> => {
  const raw = JSON.parse(await readFile(path, 'utf8')) as Partial<History>
  let traced: TracedBuilding[] = []
  if (raw.sanborn !== undefined) {
    for (const file of typeof raw.sanborn.lost === 'string' ? [raw.sanborn.lost] : raw.sanborn.lost) {
      const fc = JSON.parse(await readFile(file, 'utf8')) as { features: { properties: Omit<TracedBuilding, 'ring'>; geometry: { coordinates: number[][][] } }[] }
      traced = traced.concat(fc.features.map((f) => ({ ...f.properties, ring: f.geometry.coordinates[0].slice(0, -1).map(([x, y]) => [x, y] as Vec2) })))
    }
  }
  return {
    epochs: raw.epochs ?? [], features: raw.features ?? [], rules: raw.rules ?? [], present: raw.present ?? new Date().getFullYear(),
    dates: raw.dates ?? [], ...(raw.sanborn === undefined ? {} : { sanborn: raw.sanborn }), traced,
    ...(raw.streetsNearBuildings === undefined ? {} : { streetsNearBuildings: raw.streetsNearBuildings }),
    ...(raw.majorStreetsNearBuildings === undefined ? {} : { majorStreetsNearBuildings: raw.majorStreetsNearBuildings }),
    ...(raw.streetcarScale === undefined ? {} : { streetcarScale: raw.streetcarScale }),
    ...(raw.railScale === undefined ? {} : { railScale: raw.railScale }),
  }
}

export const alive = (from: number | null | undefined, to: number | null | undefined, year: number): boolean =>
  (from === null || from === undefined || from <= year) && (to === null || to === undefined || year < to)

/**
 * A year from an OSM date: "1885", "1885-04-01", "c. 1890", "~1850", "1890s" (taken as 1890),
 * "before 1900" (1900, the latest it can be). Null when no four-digit year is in it.
 */
export const parseYear = (s: string | undefined): number | null => {
  if (s === undefined) return null
  const m = /(1[5-9]\d\d|20\d\d)/.exec(s)
  if (m === null) return null
  const y = Number(m[1])
  return y >= 1600 && y <= 2100 ? y : null
}

const matches = (r: Rule, f: Feature): boolean => {
  const w = r.where
  if (w.id !== undefined && !w.id.includes(f.id)) return false
  if (w.type !== undefined && w.type !== f.type) return false
  if (w.bridge !== undefined && (f.tags.bridge !== undefined && f.tags.bridge !== 'no') !== w.bridge) return false
  if (w.name !== undefined) {
    const needle = w.name.toLowerCase()
    const hay = `${f.tags.name ?? ''}\u0000${f.tags.ref ?? ''}`.toLowerCase()
    if (!hay.includes(needle)) return false
  }
  if (w.tag !== undefined) {
    const v = f.tags[w.tag]
    if (v === undefined) return false
    if (w.is !== undefined && !w.is.includes(v)) return false
  }
  return true
}

/** Whether a non-building feature existed in `year`, by the first rule that matches it. */
export const featureAlive = (f: Feature, year: number, h: History): boolean => {
  for (const r of h.rules) {
    if (!matches(r, f)) continue
    if (r.eras.length === 0) return year >= h.present
    return r.eras.some(([a, b]) => alive(a, b, year))
  }
  return true
}

const MINOR_STREETS = new Set(['tertiary', 'tertiary_link', 'residential', 'service', 'unclassified', 'living_street', 'track', 'footway', 'path', 'cycleway', 'pedestrian', 'steps', 'bridleway'])

/** Main roads, held to the same test only where a series asks (`majorStreetsNearBuildings`). */
const MAJOR_STREETS = new Set(['trunk', 'primary', 'secondary'])

/** Streets a town plan lays out: a plan's own grid, never its service roads or paths. */
const PLANNED_STREETS = new Set(['tertiary', 'residential', 'unclassified', 'living_street'])

/**
 * Drop minor streets with no building within `meters` (of the buildings still in `features`,
 * plus `extra` points, such as buildings traced from old maps). A street in a 1925 scene with
 * no 1925 house anywhere along it was most likely laid out later. A street of the plan's kind
 * (a main road, tertiary, residential, unclassified, living) inside a town plan already laid
 * out (`plans`, lon/lat rings) is kept without houses: the plan is the record that it was laid
 * out. With `major`, main roads (trunk, primary, secondary) must pass the test too. Returns the
 * kept features and how many streets were dropped.
 */
export const dropUnbuiltStreets = (
  features: readonly Feature[], meters: number, extra: readonly Vec2[] = [], plans: readonly (readonly Vec2[])[] = [], major = false,
): { kept: Feature[]; dropped: number } => {
  let lat0 = 0
  let n = 0
  for (const f of features) if (f.type === 'line' && f.points.length) { lat0 += f.points[0][1]; n++ }
  lat0 = n ? lat0 / n : 0
  const kx = 111_320 * Math.cos((lat0 * Math.PI) / 180)
  const ky = 110_574
  const cell = meters
  const grid = new Set<string>()
  const add = (lon: number, lat: number) => {
    const x = Math.floor((lon * kx) / cell)
    const y = Math.floor((lat * ky) / cell)
    grid.add(`${x},${y}`)
  }
  for (const f of features) {
    if (f.type !== 'polygon' || (f.tags.building === undefined && f.tags['building:part'] === undefined)) continue
    for (const p of f.outers[0]) add(p[0], p[1])
  }
  for (const p of extra) add(p[0], p[1])
  const near = (lon: number, lat: number) => {
    const x = Math.floor((lon * kx) / cell)
    const y = Math.floor((lat * ky) / cell)
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) if (grid.has(`${x + dx},${y + dy}`)) return true
    return false
  }
  let dropped = 0
  const kept = features.filter((f) => {
    if (f.type !== 'line' || !(MINOR_STREETS.has(f.tags.highway ?? '') || (major && MAJOR_STREETS.has(f.tags.highway ?? '')))) return true
    if ((PLANNED_STREETS.has(f.tags.highway ?? '') || MAJOR_STREETS.has(f.tags.highway ?? '')) && f.points.some((p) => plans.some((r) => pointInRing(p, r as Vec2[])))) return true
    // Walk the street every half-cell, so a long block with one house still counts.
    for (let i = 0; i < f.points.length; i++) {
      const a = f.points[i]
      if (near(a[0], a[1])) return true
      const b = f.points[i + 1]
      if (b === undefined) continue
      const len = Math.hypot((b[0] - a[0]) * kx, (b[1] - a[1]) * ky)
      for (let s = cell / 2; s < len; s += cell / 2) {
        const t = s / len
        if (near(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)) return true
      }
    }
    dropped++
    return false
  })
  return { kept, dropped }
}

// ---- year built ------------------------------------------------------------------------------

/** A parcel from the assessor: outline (lon/lat, open) and year built. */
export interface Parcel {
  readonly ring: Vec2[]
  readonly year: number
}

export interface Dated {
  readonly year: number
  /**
   * Curated only: drawn before this year and not from it, until today's scene, which draws
   * everything mapped today. For a part that stands in for a building before it was enlarged
   * (the Capitol's central block before its wings), whose full outline is dated from then.
   */
  readonly until?: number
  readonly source: 'curated' | 'osm' | 'parcel'
}

/**
 * Date each building: a curated year first, then its own `start_date` when OSM has one, else
 * the year built of the parcel its center falls in.
 *
 * An assessor records one year per parcel: the year of its main building. Up to `few`
 * buildings on a lot (a row split in OSM, a house and its shed) all take it; with more, only one
 * clearly larger than the rest does; and where a parcel holds `crowd` or more (a campus,
 * Capitol Square) the year is no one's in particular, and those buildings stay undated.
 */
export const dateBuildings = (
  buildings: readonly PolygonFeature[], parcels: readonly Parcel[], curated: History['dates'] = [], few = 4, crowd = 8,
): Map<string, Dated> => {
  // Parcels into a grid of ~110 m cells, by their bounding boxes.
  const cell = 0.001
  const grid = new Map<string, number[]>()
  parcels.forEach((p, k) => {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity
    for (const [x, y] of p.ring) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y) }
    for (let i = Math.floor(x0 / cell); i <= Math.floor(x1 / cell); i++) {
      for (let j = Math.floor(y0 / cell); j <= Math.floor(y1 / cell); j++) {
        const key = `${i},${j}`
        const list = grid.get(key)
        if (list) list.push(k)
        else grid.set(key, [k])
      }
    }
  })
  const parcelOf = (b: PolygonFeature): number => {
    const c = centroid(b.outers[0])
    for (const k of grid.get(`${Math.floor(c[0] / cell)},${Math.floor(c[1] / cell)}`) ?? []) if (pointInRing(c, parcels[k].ring)) return k
    return -1
  }
  const fixed = new Map(curated.map((d) => [d.id, d.year]))
  const untils = new Map(curated.filter((d) => d.until !== undefined).map((d) => [d.id, d.until as number]))
  const out = new Map<string, Dated>()
  const tenants = new Map<number, PolygonFeature[]>()
  for (const b of buildings) {
    if (b.tags.building === undefined && b.tags['building:part'] === undefined) continue
    const mine = fixed.get(b.id)
    const own = parseYear(b.tags.start_date ?? b.tags['building:start_date'] ?? b.tags.construction_date)
    const until = untils.get(b.id)
    if (mine !== undefined) out.set(b.id, { year: mine, ...(until === undefined ? {} : { until }), source: 'curated' })
    else if (own !== null) out.set(b.id, { year: own, source: 'osm' })
    // Every building counts as a tenant of its parcel, dated or not.
    const k = parcelOf(b)
    if (k < 0) continue
    const list = tenants.get(k)
    if (list) list.push(b)
    else tenants.set(k, [b])
  }
  // Area in rough square degrees is enough to rank buildings on one parcel.
  const size = (b: PolygonFeature) => Math.abs(b.outers[0].reduce((a, p, i, r) => { const q = r[(i + 1) % r.length]; return a + p[0] * q[1] - q[0] * p[1] }, 0))
  for (const [k, list] of tenants) {
    // A curated building's parcel year is evidently not to be trusted for its neighbors either.
    if (list.length >= crowd || list.some((b) => fixed.has(b.id))) continue
    const ranked = [...list].sort((a, b) => size(b) - size(a))
    // A few buildings on one lot (a row, a house and its shed) are taken to share its year;
    // among more, only one clearly larger than the rest.
    const takers = ranked.length <= few ? ranked : size(ranked[0]) >= 2 * size(ranked[1]) ? [ranked[0]] : []
    for (const b of takers) if (!out.has(b.id)) out.set(b.id, { year: parcels[k].year, source: 'parcel' })
  }
  return out
}

/** Year-built parcels as GeoJSON (any polygon features with a numeric year property). */
export const parseParcels = (json: string, field: string): Parcel[] => {
  const fc = JSON.parse(json) as { features: { geometry: { type: string; coordinates: number[][][] | number[][][][] } | null; properties: Record<string, unknown> }[] }
  const out: Parcel[] = []
  for (const f of fc.features) {
    const y = Number(f.properties[field])
    if (!Number.isFinite(y) || y < 1600 || y > 2100 || f.geometry === null) continue
    const polys = f.geometry.type === 'MultiPolygon' ? (f.geometry.coordinates as number[][][][]) : [f.geometry.coordinates as number[][][]]
    for (const poly of polys) {
      const ring = poly[0].map(([x, yy]) => [x, yy] as Vec2)
      if (ring.length > 3) out.push({ ring: ring.slice(0, -1), year: y })
    }
  }
  return out
}

export interface YearBuiltSource {
  /** An ArcGIS FeatureServer layer URL (…/FeatureServer/0). */
  readonly url: string
  /** The year-built field. */
  readonly field: string
}

/**
 * Where a dated region's year-built parcels may be: its own data folder first (where `fetch`
 * writes them), then the shared folder it borrows OSM and elevation from (`"data"`).
 */
export const yearBuiltDirs = (r: Pick<Region, 'name' | 'data'>, root = 'data'): string[] =>
  [...new Set([join(root, r.name), join(root, r.data ?? r.name)])]

/**
 * Read the year-built parcels from the first of `dirs` that holds them. A dated series without
 * them would date nothing but its few curated buildings and draw every other building, of any
 * age, in today's scene only (or, worse, mis-date them), so a missing file is an error.
 */
export const loadYearBuilt = async (dirs: readonly string[], field: string, name: string): Promise<{ parcels: Parcel[]; path: string }> => {
  for (const dir of dirs) {
    const path = join(dir, 'yearbuilt.json')
    let json: string
    try {
      json = await readFile(path, 'utf8')
    } catch (e) {
      if ((e as NodeJS.ErrnoException).code === 'ENOENT') continue
      throw e
    }
    return { parcels: parseParcels(json, field), path }
  }
  throw new Error(`no year-built data for "${name}" (looked in ${dirs.join(', ')}); run: isoscape fetch ${name} --extras-only`)
}

/** Page through an ArcGIS layer for the region's box; store it as data/<region>/yearbuilt.json. */
export const fetchYearBuilt = async (r: Region, src: YearBuiltSource, dir: string, log = console.error): Promise<number> => {
  const b = fetchBounds(r)
  const features: unknown[] = []
  for (let offset = 0; ; offset += 2000) {
    const q = new URLSearchParams({
      where: `${src.field} > 0`,
      geometry: `${b.west},${b.south},${b.east},${b.north}`,
      geometryType: 'esriGeometryEnvelope',
      inSR: '4326',
      spatialRel: 'esriSpatialRelIntersects',
      outFields: src.field,
      outSR: '4326',
      returnGeometry: 'true',
      geometryPrecision: '7',
      resultOffset: String(offset),
      resultRecordCount: '2000',
      f: 'geojson',
    })
    const res = await fetch(`${src.url}/query?${q}`, { headers: { 'user-agent': 'isoscape/0.1' } })
    if (!res.ok) throw new Error(`year built: HTTP ${res.status}`)
    const page = (await res.json()) as { features?: unknown[]; error?: unknown }
    if (page.features === undefined) throw new Error(`year built: ${JSON.stringify(page.error ?? page).slice(0, 200)}`)
    features.push(...page.features)
    log(`year built: ${features.length} parcels`)
    if (page.features.length < 2000) break
  }
  await mkdir(dir, { recursive: true })
  await writeFile(join(dir, 'yearbuilt.json'), JSON.stringify({ type: 'FeatureCollection', source: src.url, features }))
  return features.length
}
