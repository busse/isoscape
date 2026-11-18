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
  readonly kind: 'water' | 'burned' | 'plan' | 'landmark' | 'creek' | 'streetcar' | 'grounds' | 'track' | 'rail' | 'platform' | 'canopy' | 'site' | 'wood' | 'label' | 'bridge'
  readonly from: number
  readonly to?: number
  /** lon/lat outline (open), for areas and landmarks. */
  readonly ring?: Vec2[]
  /**
   * lon/lat center line, for creeks, streetcar lines (a streetcar line may hold several runs:
   * `lines`) and lost road bridges (`bridge`: drawn as a road bridge of today would be, one
   * level up, its deck carrying any streetcar line that runs along it).
   */
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
  readonly shape?: 'prism' | 'dome' | 'revolve' | 'stair' | 'arch' | 'hip' | 'gable' | 'disc' | 'inset' | 'frame' | 'track'
  /**
   * A `hip` that is one piece of a larger hipped roof (split round a tower that stands in it):
   * that roof's whole outline (lon, lat, convex). The piece's slopes rise from the whole roof's
   * eaves, and its own ring only cuts it out, so the pieces meet as one roof.
   */
  readonly roofRing?: Vec2[]
  readonly tone?: PartTone
  /**
   * The modeled building a part belongs to, where a history holds more than one: the parts of
   * each `model` take their levels from the ground under that model alone (see `modelZ`), so
   * one building's ground does not lift another's. Parts with none share one model.
   */
  readonly model?: string
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
   * `hip`: a roof rising from every edge of its (convex) ring at one pitch to a ridge at its
   * top; `gable`: a roof rising from the ring's first and third edges (its eaves) to a ridge
   * midway between them at its top, the second and fourth edges its gable ends. `disc`: a disc
   * standing on the ring's first edge (its diameter), as thick as the second (a clock face).
   */
  readonly steps?: number
  /** A part standing inside a roof shell (that part's id): see `Item.within`. */
  readonly within?: string
  /** A part standing on a roof shell's outside (that part's id), a dormer: see `Item.over`. */
  readonly over?: string
  /** `fine`: its outlines drawn with the palette's finer ink, so small repeated work (a row of dormers) reads as a rhythm. */
  readonly ink?: 'fine'
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
  /**
   * A streetcar line: stretches (lon/lat ends) already drawn as curves where the line was placed,
   * kept to `tolerance` meters when the line is straightened, so their bends stay round.
   */
  readonly round?: readonly { readonly from: Vec2; readonly to: Vec2; readonly tolerance: number }[]
  /** From this year a landmark stands as a burned shell. */
  readonly ruin?: number
  /** A `plan`: draw only the streets inside it while it stands. */
  readonly limitsStreets?: boolean
  /**
   * A `bridge`: a road (`mode: 'road'`, default) or railroad (`'rail'`) bridge that is gone,
   * along `line` (lon/lat), drawn as a bridge of today's map would be: its deck `deck` meters
   * over the ground or water under it (default the region's), ramping down to the ground at
   * each end. Each end should be a node of a street (or track) standing in the years it is
   * drawn, so the bridge lands on it; a past year's check leaves out a road bridge that does
   * not (see `pastGround`). `highway` is the road's OSM class (default secondary).
   */
  readonly mode?: 'road' | 'rail'
  readonly deck?: number
  readonly highway?: string
  /**
   * Drawn only in builds asked for it by name (`isoscape build --with <name>`): for a feature
   * added after some years of a series were published, so their scenes stay as sold until each
   * is redrawn. A build records the names it was given.
   */
  readonly switch?: string
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

export type PartTone = 'stone' | 'dome' | 'iron' | 'ramp' | 'coach' | 'engine' | 'freight' | 'plaster' | 'floor' | 'wood' | 'glass' | 'tram' | 'roof' | 'loco' | 'coal' | 'carRoof' | 'brick' | 'tile' | 'roofTile' | 'steel' | 'ballast' | 'diesel' | 'coachBlue' | 'coachBand' | 'coachSkirt' | 'coachRoof' | 'water' | 'earth'

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
  /** The coaches' paint: Pullman green (the default), or the C&O's blue with a yellow band. */
  readonly livery?: 'pullman' | 'co'
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
    /** Tag keys the feature must not carry (a service road with no `service` kind and no name). */
    readonly without?: readonly string[]
  }
  /** Applied only in builds that switch it on by name (see `HistoryFeature.switch`). */
  readonly switch?: string
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
  readonly dates: readonly {
    /**
     * The year it was built, or null where no source gives one: such a building (one whose only
     * date was a parcel's and is known to be wrong) is drawn in today's scene only.
     */
    readonly id: string; readonly name?: string; readonly year: number | null; readonly until?: number; readonly source: string; readonly note?: string
    /** Its height in meters, where OSM's is missing or wrong for the series: the note says where it comes from. */
    readonly height?: number
  }[]
  /** Fire-insurance maps traced into footprints: the editions used, and the buildings since lost. */
  readonly sanborn?: {
    readonly lost: string | readonly string[]; readonly editions: readonly number[]; readonly source: string
    /** Sheets whose fit is known to be wrong, left out until they are placed again: each says why. */
    readonly leaveOut?: readonly { readonly edition: number; readonly sheet: string; readonly why: string }[]
  }
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
   * Hold service roads (driveways, yards, lanes to a building) to a closer test: a building of the
   * year within this many meters, so a works' yard roads are not kept by a house across the road.
   */
  readonly serviceNearBuildings?: number
  /**
   * Draw streetcar lines and cars this many times life size, so they read in a city-wide view
   * (default 1).
   */
  readonly streetcarScale?: number
  /** Draw railroad tracks this many times their width, and in the ties' darker tone, so the network reads from afar (default 1). */
  readonly railScale?: number
  /** Yard, siding and spur track (any `service` tag) drawn at no more than this scale (a set's map). */
  readonly railScaleService?: number
  /**
   * Date laid-out ground (lawns, beds, pitches, playgrounds) and service roads by the
   * assessor's year built of the parcel they lie in, as buildings are: the planted strips of a
   * lot paved in 2017 and the drives of a yard built in 1989 are no older than the lot.
   */
  readonly groundsByParcel?: boolean
  /**
   * More kinds of verge than woods and scrub (laterWorks), as "key=value": grass and meadow
   * along a road not yet built are its interchange's infields.
   */
  readonly vergeTags?: readonly string[]
  /**
   * Leave out a bridge's approaches with it: where a road bridge is not drawn in a year, the
   * ways that lead only to it (a chain of ways joined end to end, none touching another
   * street) end the street at its last junction instead of in a stub.
   */
  readonly approachesWithBridges?: boolean
  /**
   * Meters of clearance a viaduct of the year keeps: a traced building within this distance of
   * a rail viaduct or a curated bridge (not only crossed by its center line), and any dated
   * building a curated bridge passes over, is left out (it was cleared for the viaduct, or its
   * place or year is wrong).
   */
  readonly viaductClearance?: number
  /**
   * Meters: a traced building with a street's center line (a carriageway, not a service road or
   * path) or a streetcar line passing through it, or within this distance of it, is left out:
   * the sheet was fitted a little off and set it in the street.
   */
  readonly tracedClearOfStreets?: number
  /** Meters: the car lines' own clearance for traced buildings, if wider than the streets' (`tracedClearOfStreets`). */
  readonly tracedClearOfCarLines?: number
  /** Meters: simplify traced outlines to this and take out their spikes; drop ragged gray footprints. */
  readonly tracedSmooth?: number
  /** Track on a curated site is taken whole or not at all, never cut at the site's edge. */
  readonly siteWholeLines?: boolean
  /** Leave out a building dated only by its parcel that a car line of the year runs through. */
  readonly clearCarLines?: boolean
  /** Meters: close up, a tie within this of one already laid is left out (turnouts, wyes). */
  readonly tieClear?: number
  /** In a whole view, leave out train cars standing under a raised concourse (its name ends "concourse"). */
  readonly trainsClearOfDecks?: boolean
  /** Draw turned parts (`shape: 'revolve'`, a dome) shaded, inked only along their foot. */
  readonly revolveInkFoot?: boolean
  /** Meters of street bed drawn either side of each car line, under it (default none). */
  readonly carLineBed?: number
  /**
   * Paint the car lines' band exactly, unsimplified and cut at the grid lines, and lapping
   * half a unit on screen further back than the other ground layers, so no seam or notch shows
   * in it where the paint strips meet.
   */
  readonly carLineSeal?: boolean
  /** Keep a street a car line of the year ran along, even with no house of the year on it. */
  readonly streetsUnderCars?: boolean
  /**
   * A road bridge that carries a car line is drawn at least as wide as the line, the line on it
   * as wide as on the ground, so the line runs onto the deck without a step and no
   * square deck end shows beside it; a building (not curated) under such a deck is left out.
   */
  readonly carDecks?: boolean
  /** A road deck that carries a car line is laid on the line as drawn, so deck and ground bands meet without a step. */
  readonly carDeckSnap?: boolean
  /**
   * A road deck that carries a car line takes the line's center line, so the deck and the band
   * on the ground run as one (`true`), or only the decks listed, by id.
   */
  readonly carDeckOnLine?: boolean | readonly string[]
  /**
   * Meters: a car line that ends this close to another line, short of it, is carried on
   * straight to meet it (a junction where the two were placed on different corners).
   */
  readonly carLineEnds?: number
  /** Meters: a later road's corridor with woods on both sides within this of its edge is drawn as wood. */
  readonly vergeFill?: number
  /** Bridges drawn at grade before a year, with why (the street crossed there before its bridge). */
  readonly atGrade?: readonly { readonly id: readonly string[]; readonly before: number; readonly note: string; readonly sources?: readonly string[] }[]
  /**
   * A parking structure (`building=parking`, `parking=multi-storey`) that only its parcel dates,
   * to a year before this one, is dated this year instead: the assessor's year is the lot's
   * earlier building's, not the deck's. A curated date still wins.
   */
  readonly parkingFrom?: number
  /**
   * A minor road bridge (residential, service, unclassified, living street) over a canal, with
   * no `start_date`, is drawn from this year only: the canal's bridges of today belong to its
   * redevelopment, and what crossed it before is not known here. A rule naming the bridge wins.
   */
  readonly canalBridgesFrom?: number
  /**
   * Woods and scrub with `vergeShare` of their outline or more within `vergeReach` meters of a
   * road not yet built are its verges, dated with it (`laterWorks`; defaults 20 m and 0.4).
   */
  readonly vergeReach?: number
  readonly vergeShare?: number
  /**
   * Meters: mend the year's streets (`mendStreets`): put back runs of streets up to this long
   * left out between drawn ones for want of houses, and leave out road ways that led only to
   * later works. Off unless set.
   */
  readonly streetEnds?: number
  /** The street at either end of a curated bridge of the year is kept to it (`dropApproaches`, `mendStreets`). */
  readonly bridgeAnchors?: boolean
  /** Keep the whole of a street, by name, that leads onto a road bridge (`dropUnbuiltStreets`'s `follow`). */
  readonly bridgeStreets?: boolean
  /**
   * A curated road bridge clears traced buildings as a rail viaduct does: one with any part
   * within `TRACED_VIADUCT_CLEAR` of its line is left out (its line is approximate, and a deck
   * drawn over a roof reads as running through it).
   */
  readonly bridgesClearTraced?: boolean
  /**
   * Settings a build's `--with` names switch on, by name: for corrections made after some years
   * of a series were published, so their scenes stay as sold until each is redrawn.
   */
  readonly switches?: Readonly<Record<string, { readonly vergeReach?: number; readonly vergeShare?: number; readonly bridgeStreets?: boolean; readonly bridgesClearTraced?: boolean; readonly note?: string }>>
}

export const loadHistory = async (path: string): Promise<History> => {
  let raw = JSON.parse(await readFile(path, 'utf8')) as Partial<History> & { extends?: string }
  // A file can extend another: its rules and dates come first (so they win), its features are
  // added (replacing the base's of the same id), and any other field it sets replaces the base's. A set's views of a place can then
  // take rules the place's other drawings, already sold, must not.
  if (raw.extends !== undefined) {
    const base = JSON.parse(await readFile(raw.extends, 'utf8')) as Partial<History>
    raw = {
      ...base, ...raw,
      rules: [...(raw.rules ?? []), ...(base.rules ?? [])],
      dates: [...(raw.dates ?? []), ...(base.dates ?? [])],
      features: [...(base.features ?? []).filter((f) => !(raw.features ?? []).some((g) => g.id === f.id)), ...(raw.features ?? [])],
    }
  }
  let traced: TracedBuilding[] = []
  if (raw.sanborn !== undefined) {
    for (const file of typeof raw.sanborn.lost === 'string' ? [raw.sanborn.lost] : raw.sanborn.lost) {
      const fc = JSON.parse(await readFile(file, 'utf8')) as { features: { properties: Omit<TracedBuilding, 'ring'>; geometry: { coordinates: number[][][] } }[] }
      traced = traced.concat(fc.features.map((f) => ({ ...f.properties, ring: f.geometry.coordinates[0].slice(0, -1).map(([x, y]) => [x, y] as Vec2) })))
    }
    const out = raw.sanborn.leaveOut ?? []
    traced = traced.filter((b) => !out.some((o) => o.edition === b.edition && o.sheet === String(b.sheet)))
  }
  return {
    epochs: raw.epochs ?? [], features: raw.features ?? [], rules: raw.rules ?? [], present: raw.present ?? new Date().getFullYear(),
    dates: raw.dates ?? [], ...(raw.sanborn === undefined ? {} : { sanborn: raw.sanborn }), traced,
    ...(raw.streetsNearBuildings === undefined ? {} : { streetsNearBuildings: raw.streetsNearBuildings }),
    ...(raw.majorStreetsNearBuildings === undefined ? {} : { majorStreetsNearBuildings: raw.majorStreetsNearBuildings }),
    ...(raw.serviceNearBuildings === undefined ? {} : { serviceNearBuildings: raw.serviceNearBuildings }),
    ...(raw.streetcarScale === undefined ? {} : { streetcarScale: raw.streetcarScale }),
    ...(raw.railScale === undefined ? {} : { railScale: raw.railScale }),
    ...(raw.railScaleService === undefined ? {} : { railScaleService: raw.railScaleService }),
    ...(raw.groundsByParcel === undefined ? {} : { groundsByParcel: raw.groundsByParcel }),
    ...(raw.vergeTags === undefined ? {} : { vergeTags: raw.vergeTags }),
    ...(raw.approachesWithBridges === undefined ? {} : { approachesWithBridges: raw.approachesWithBridges }),
    ...(raw.atGrade === undefined ? {} : { atGrade: raw.atGrade }),
    ...(raw.tracedSmooth === undefined ? {} : { tracedSmooth: raw.tracedSmooth }),
    ...(raw.siteWholeLines === undefined ? {} : { siteWholeLines: raw.siteWholeLines }),
    ...(raw.clearCarLines === undefined ? {} : { clearCarLines: raw.clearCarLines }),
    ...(raw.tieClear === undefined ? {} : { tieClear: raw.tieClear }),
    ...(raw.carLineBed === undefined ? {} : { carLineBed: raw.carLineBed }),
    ...(raw.revolveInkFoot === undefined ? {} : { revolveInkFoot: raw.revolveInkFoot }),
    ...(raw.trainsClearOfDecks === undefined ? {} : { trainsClearOfDecks: raw.trainsClearOfDecks }),
    ...(raw.carLineSeal === undefined ? {} : { carLineSeal: raw.carLineSeal }),
    ...(raw.streetsUnderCars === undefined ? {} : { streetsUnderCars: raw.streetsUnderCars }),
    ...(raw.carDecks === undefined ? {} : { carDecks: raw.carDecks }),
    ...(raw.carDeckSnap === undefined ? {} : { carDeckSnap: raw.carDeckSnap }),
    ...(raw.carDeckOnLine === undefined ? {} : { carDeckOnLine: raw.carDeckOnLine }),
    ...(raw.carLineEnds === undefined ? {} : { carLineEnds: raw.carLineEnds }),
    ...(raw.vergeFill === undefined ? {} : { vergeFill: raw.vergeFill }),
    ...(raw.viaductClearance === undefined ? {} : { viaductClearance: raw.viaductClearance }),
    ...(raw.tracedClearOfStreets === undefined ? {} : { tracedClearOfStreets: raw.tracedClearOfStreets }),
    ...(raw.tracedClearOfCarLines === undefined ? {} : { tracedClearOfCarLines: raw.tracedClearOfCarLines }),
    ...(raw.parkingFrom === undefined ? {} : { parkingFrom: raw.parkingFrom }),
    ...(raw.canalBridgesFrom === undefined ? {} : { canalBridgesFrom: raw.canalBridgesFrom }),
    ...(raw.vergeReach === undefined ? {} : { vergeReach: raw.vergeReach }),
    ...(raw.vergeShare === undefined ? {} : { vergeShare: raw.vergeShare }),
    ...(raw.bridgeStreets === undefined ? {} : { bridgeStreets: raw.bridgeStreets }),
    ...(raw.bridgesClearTraced === undefined ? {} : { bridgesClearTraced: raw.bridgesClearTraced }),
    ...(raw.streetEnds === undefined ? {} : { streetEnds: raw.streetEnds }),
    ...(raw.bridgeAnchors === undefined ? {} : { bridgeAnchors: raw.bridgeAnchors }),
    ...(raw.switches === undefined ? {} : { switches: raw.switches }),
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
  if (w.without !== undefined && w.without.some((k) => f.tags[k] !== undefined)) return false
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

/**
 * Whether a feature standing in `year` stands then only for a span that ends before today: the
 * era its first matching rule draws it in has an end (the canal's downtown end, 1800 to 1890,
 * re-watered in 1999 along another bed). Such water is drawn as historic water (see
 * `historicWater` in terrain.ts), not on today's ground as it lies.
 */
export const featureHistoric = (f: Feature, year: number, h: History): boolean => {
  for (const r of h.rules) {
    if (!matches(r, f)) continue
    return r.eras.some(([a, b]) => b !== null && alive(a, b, year))
  }
  return false
}

/**
 * A history as a build's `--with` names (`on`) have it: every unswitched feature and rule and
 * those named, and the settings the names switch on.
 */
export const switchedOn = (h: History, on: readonly string[]): History => {
  const keep = (x: { readonly switch?: string }) => x.switch === undefined || on.includes(x.switch)
  let out = h
  if (!h.features.every(keep)) out = { ...out, features: h.features.filter(keep) }
  if (!h.rules.every(keep)) out = { ...out, rules: h.rules.filter(keep) }
  for (const name of on) {
    const set = h.switches?.[name]
    if (set === undefined) continue
    out = { ...out, ...(set.vergeReach === undefined ? {} : { vergeReach: set.vergeReach }), ...(set.vergeShare === undefined ? {} : { vergeShare: set.vergeShare }), ...(set.bridgeStreets === undefined ? {} : { bridgeStreets: set.bridgeStreets }), ...(set.bridgesClearTraced === undefined ? {} : { bridgesClearTraced: set.bridgesClearTraced }) }
  }
  return out
}

/** A curated bridge as the map feature it stands in for: a road or railroad bridge way. */
export const bridgeFeature = (h: HistoryFeature): Feature | null => {
  if (h.kind !== 'bridge' || h.line === undefined || h.line.length < 2) return null
  const tags: Record<string, string> = h.mode === 'rail'
    ? { railway: 'rail', bridge: 'yes', layer: '1', name: h.name }
    : { highway: h.highway ?? 'secondary', bridge: 'yes', layer: '1', name: h.name }
  tags['isoscape:seat'] = 'ground'
  if (h.deck !== undefined) tags['isoscape:deck'] = String(h.deck)
  return { type: 'line', id: `history:${h.id}`, tags, points: h.line }
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
 * out. With `major`, main roads (trunk, primary, secondary) must pass the test too. A street that
 * meets a road bridge is kept with it (with `follow`, the rest of that street by name too). A bridge is
 * never dropped: it carries its street over water or a valley where no house can stand, and its
 * era rule alone says when it stood. Returns the kept features and how many streets were dropped.
 */
export const dropUnbuiltStreets = (
  features: readonly Feature[], meters: number, extra: readonly Vec2[] = [], plans: readonly (readonly Vec2[])[] = [], major = false, follow = false,
  service?: number,
): { kept: Feature[]; dropped: number } => {
  let lat0 = 0
  let n = 0
  for (const f of features) if (f.type === 'line' && f.points.length) { lat0 += f.points[0][1]; n++ }
  lat0 = n ? lat0 / n : 0
  const kx = 111_320 * Math.cos((lat0 * Math.PI) / 180)
  const ky = 110_574
  const corners: Vec2[] = []
  for (const f of features) {
    if (f.type !== 'polygon' || (f.tags.building === undefined && f.tags['building:part'] === undefined)) continue
    for (const p of f.outers[0]) corners.push(p)
  }
  corners.push(...extra)
  // A grid of `size` m cells holding every building corner; near = a corner in this cell or one beside it.
  const nearTest = (size: number) => {
    const grid = new Set<string>()
    for (const p of corners) grid.add(`${Math.floor((p[0] * kx) / size)},${Math.floor((p[1] * ky) / size)}`)
    return (lon: number, lat: number) => {
      const x = Math.floor((lon * kx) / size)
      const y = Math.floor((lat * ky) / size)
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) if (grid.has(`${x + dx},${y + dy}`)) return true
      return false
    }
  }
  const nearStreet = nearTest(meters)
  const nearService = service === undefined ? nearStreet : nearTest(service)
  // Nodes of road bridges: a street that meets one carries the bridge's traffic on (the road
  // across an island between two spans, a bridge's approach), so it stands with the bridge.
  const bridgeNodes = new Set<string>()
  for (const f of features) if (f.type === 'line' && f.tags.highway !== undefined && f.tags.bridge !== undefined && f.tags.bridge !== 'no') for (const p of f.points) bridgeNodes.add(`${p[0]},${p[1]}`)
  // ...and, with `follow`, so does the rest of that street, by name, as far as it runs on
  // unbroken (Hull Street from Mayo's Bridge across Manchester).
  const carried = new Set<string>()
  const streets = features.filter((f): f is Extract<Feature, { type: 'line' }> => f.type === 'line' && f.tags.highway !== undefined && !(f.tags.bridge !== undefined && f.tags.bridge !== 'no'))
  let front = streets.filter((f) => f.points.some((p) => bridgeNodes.has(`${p[0]},${p[1]}`)))
  for (const f of front) carried.add(f.id)
  while (follow && front.length > 0) {
    const ends = new Map<string, string>()
    for (const f of front) if (f.tags.name !== undefined) for (const p of f.points) ends.set(`${p[0]},${p[1]}`, f.tags.name)
    front = streets.filter((g) => !carried.has(g.id) && g.tags.name !== undefined && g.points.some((p) => ends.get(`${p[0]},${p[1]}`) === g.tags.name))
    for (const g of front) carried.add(g.id)
  }
  let dropped = 0
  const kept = features.filter((f) => {
    if (f.type !== 'line' || !(MINOR_STREETS.has(f.tags.highway ?? '') || (major && MAJOR_STREETS.has(f.tags.highway ?? '')))) return true
    if (f.tags.bridge !== undefined && f.tags.bridge !== 'no') return true
    if (carried.has(f.id)) return true
    if ((PLANNED_STREETS.has(f.tags.highway ?? '') || MAJOR_STREETS.has(f.tags.highway ?? '')) && f.points.some((p) => plans.some((r) => pointInRing(p, r as Vec2[])))) return true
    const isService = f.tags.highway === 'service' && service !== undefined
    const near = isService ? nearService : nearStreet
    const cell = isService ? service : meters
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

/** A parking structure: what `parkingFrom` holds to a later year when only its parcel dates it. */
export const isParkingStructure = (t: Tags): boolean =>
  t.building === 'parking' || t['building:part'] === 'parking' || t.parking === 'multi-storey'

/**
 * Date each building: a curated year first, then its own `start_date` when OSM has one, else
 * the year built of the parcel its center falls in. A building part (`building:part`) of a
 * curated building takes its building's curated year: the part a parcel would date is a piece
 * of the same tower. A curated year of null leaves a building undated (today's scene only).
 * With `parkingFrom`, a parking structure dated by its parcel alone to an earlier year is dated
 * `parkingFrom`.
 *
 * An assessor records one year per parcel: the year of its main building. Up to `few`
 * buildings on a lot (a row split in OSM, a house and its shed) all take it; with more, only one
 * clearly larger than the rest does; and where a parcel holds `crowd` or more (a campus,
 * Capitol Square) the year is no one's in particular, and those buildings stay undated.
 */
export const dateBuildings = (
  buildings: readonly PolygonFeature[], parcels: readonly Parcel[], curated: History['dates'] = [], few = 4, crowd = 8, parkingFrom?: number,
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
    if (mine !== undefined) {
      if (mine !== null) out.set(b.id, { year: mine, ...(until === undefined ? {} : { until }), source: 'curated' })
    } else if (own !== null) out.set(b.id, { year: own, source: 'osm' })
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
    for (const b of takers) {
      if (out.has(b.id) || fixed.has(b.id)) continue
      const year = parkingFrom !== undefined && isParkingStructure(b.tags) ? Math.max(parcels[k].year, parkingFrom) : parcels[k].year
      out.set(b.id, { year, source: 'parcel' })
    }
  }
  // A part takes the curated year of the building it is a part of (the smallest curated outline
  // holding its center), unless the part is curated itself.
  const curatedOutlines = buildings.filter((b) => b.tags.building !== undefined && fixed.has(b.id))
  if (curatedOutlines.length > 0) {
    for (const p of buildings) {
      if (p.tags['building:part'] === undefined || p.tags.building !== undefined || fixed.has(p.id)) continue
      const c = centroid(p.outers[0])
      const holder = curatedOutlines.filter((b) => pointInRing(c, b.outers[0])).sort((a, b) => size(a) - size(b))[0]
      if (holder === undefined) continue
      const year = fixed.get(holder.id)
      const until = untils.get(holder.id)
      if (year === null || year === undefined) out.delete(p.id)
      else out.set(p.id, { year, ...(until === undefined ? {} : { until }), source: 'curated' })
    }
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

/** Roads whose coming changed what was there: a bridge over one, or a verge along one, is no older. */
export const WORKS = new Set(['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary_link'])

/** Roads of `all` built after `year` whose coming changed the ground (`WORKS`): an interstate, its ramps, a main road. */
export const laterWorkLines = (all: readonly Feature[], year: number, h: History): Vec2[][] =>
  all.filter((f): f is Extract<Feature, { type: 'line' }> => f.type === 'line' && WORKS.has(f.tags.highway ?? '') && !featureAlive(f, year, h)).map((f) => f.points)

/** Do segments ab and cd cross (not merely touch at an end)? */
const crosses = (a: Vec2, b: Vec2, c: Vec2, d: Vec2): boolean => {
  const o = (p: Vec2, q: Vec2, r: Vec2) => (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
  const d1 = o(a, b, c), d2 = o(a, b, d), d3 = o(c, d, a), d4 = o(c, d, b)
  return d1 * d2 < 0 && d3 * d4 < 0
}

/**
 * What the era rules alone cannot see, because it depends on what lies next to a feature.
 * `kept` are the features standing in `year`, `all` every feature mapped today.
 *
 * - A road or rail bridge stands only over something there in its year: one whose every
 *   crossing (a road, a railway or a waterway mapped under it) is not yet built or already gone
 *   carries its street or track at grade instead (its bridge and layer tags dropped). A street
 *   bridge over the turnpike (1958) is not drawn in 1950; the street is.
 * - Woods and scrub lying along roads not yet built (at least `share` of the outline within
 *   `reach` meters of them) are those roads' verges, the planted ground of an interchange,
 *   and are dated with them; so are the kinds a series adds (`vergeTags`, such as grass).
 */
export const laterWorks = (
  all: readonly Feature[], kept: readonly Feature[], year: number, h: History, reach = 20, share = 0.4,
): { kept: Feature[]; atGrade: number; verges: number } => {
  const lat0 = all.length > 0 ? (all[0].type === 'line' ? all[0].points[0][1] : all[0].outers[0][0][1]) : 0
  const kx = 111320 * Math.cos((lat0 * Math.PI) / 180), ky = 110540
  const m = (p: Vec2): Vec2 => [p[0] * kx, p[1] * ky]
  type Seg = { a: Vec2; b: Vec2; box: [number, number, number, number] }
  const segsOf = (pts: readonly Vec2[]): Seg[] => pts.slice(1).map((q, i) => {
    const a = m(pts[i]), b = m(q)
    return { a, b, box: [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])] }
  })
  const lines = all.filter((f): f is Extract<Feature, { type: 'line' }> => f.type === 'line')
  const under = lines.filter((f) => (f.tags.highway !== undefined || f.tags.railway !== undefined || f.tags.waterway !== undefined) && !(f.tags.bridge !== undefined && f.tags.bridge !== 'no'))
    .map((f) => ({ f, segs: segsOf(f.points), alive: featureAlive(f, year, h) }))
  const later = lines.filter((f) => WORKS.has(f.tags.highway ?? '') && !featureAlive(f, year, h)).flatMap((f) => segsOf(f.points))
  let atGrade = 0
  let verges = 0
  // A bridge is its spans: bridge ways of one street joined end to end. The spans over the
  // crossing and those beside it go to grade together.
  // A rail bridge counts only standing alone, with track on the ground at both ends: one that
  // meets another deck (a crossover between two viaducts) stays at its height with them.
  const decked = (f: Feature) => f.type === 'line' && f.tags.bridge !== undefined && f.tags.bridge !== 'no'
  const onDecks = new Map<string, number>()
  for (const f of kept) if (decked(f) && f.type === 'line' && f.tags.railway !== undefined) for (const p of f.points) onDecks.set(`${p[0]},${p[1]}`, (onDecks.get(`${p[0]},${p[1]}`) ?? 0) + 1)
  const alone = (f: Extract<Feature, { type: 'line' }>) => [f.points[0], f.points[f.points.length - 1]].every((p) => (onDecks.get(`${p[0]},${p[1]}`) ?? 0) <= 1)
  const isBridge = (f: Feature) => decked(f) && f.type === 'line' && (f.tags.highway !== undefined || (f.tags.railway !== undefined && alone(f)))
  const spans = kept.filter(isBridge) as Extract<Feature, { type: 'line' }>[]
  const parent = new Map(spans.map((f) => [f.id, f.id]))
  const find = (id: string): string => { let r = id; while (parent.get(r) !== r) r = parent.get(r)!; return r }
  const ends = new Map<string, string[]>()
  for (const f of spans) for (const p of [f.points[0], f.points[f.points.length - 1]]) {
    const k = `${p[0]},${p[1]}|${f.tags.name ?? f.id}`
    const list = ends.get(k)
    if (list) list.push(f.id)
    else ends.set(k, [f.id])
  }
  for (const ids of ends.values()) for (const id of ids.slice(1)) parent.set(find(id), find(ids[0]))
  const crossed = new Map<string, number>()
  const standing = new Map<string, number>()
  for (const f of spans) {
    const mine = segsOf(f.points)
    const g = find(f.id)
    for (const u of under) {
      if (u.f.id === f.id) continue
      if (!mine.some((s) => u.segs.some((t) => t.box[0] <= s.box[2] && s.box[0] <= t.box[2] && t.box[1] <= s.box[3] && s.box[1] <= t.box[3] && crosses(s.a, s.b, t.a, t.b)))) continue
      crossed.set(g, (crossed.get(g) ?? 0) + 1)
      if (u.alive) standing.set(g, (standing.get(g) ?? 0) + 1)
    }
  }
  const out: Feature[] = []
  for (const f of kept) {
    if (isBridge(f)) {
      const g = find(f.id)
      if ((crossed.get(g) ?? 0) > 0 && (standing.get(g) ?? 0) === 0) {
        const { bridge: _b, layer: _l, ...tags } = f.tags
        out.push({ ...f, tags })
        atGrade++
        continue
      }
    }
    if (f.type === 'polygon' && (f.tags.natural === 'wood' || f.tags.natural === 'scrub' || (h.vergeTags ?? []).some((t) => f.tags[t.split('=')[0]] === t.split('=')[1])) && later.length > 0) {
      const ring = f.outers[0].map(m)
      const nearLater = (p: Vec2) => later.some((s) => {
        if (p[0] < s.box[0] - reach || p[0] > s.box[2] + reach || p[1] < s.box[1] - reach || p[1] > s.box[3] + reach) return false
        const dx = s.b[0] - s.a[0], dy = s.b[1] - s.a[1], l2 = dx * dx + dy * dy
        const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - s.a[0]) * dx + (p[1] - s.a[1]) * dy) / l2))
        return Math.hypot(p[0] - s.a[0] - t * dx, p[1] - s.a[1] - t * dy) <= reach
      })
      if (ring.filter(nearLater).length >= share * ring.length) { verges++; continue }
    }
    out.push(f)
  }
  return { kept: out, atGrade, verges }
}

/** Laid-out ground and service roads a parcel's year can date (groundsByParcel). */
const PARCEL_GROUNDS: Record<string, readonly string[]> = {
  landuse: ['grass', 'flowerbed', 'village_green'],
  leisure: ['pitch', 'playground', 'dog_park', 'fitness_station', 'garden'],
}

/**
 * Years for laid-out ground and service roads from the parcel they lie in (a polygon's center,
 * a line's midpoint along its length), for a series with `groundsByParcel`. Parcels with no
 * plausible year (before 1700) date nothing.
 */
export const dateGrounds = (features: readonly Feature[], parcels: readonly Parcel[], curated: History['dates'] = []): Map<string, Dated> => {
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
  const parcelAt = (c: Vec2): number => {
    for (const k of grid.get(`${Math.floor(c[0] / cell)},${Math.floor(c[1] / cell)}`) ?? []) if (pointInRing(c, parcels[k].ring)) return k
    return -1
  }
  // As in dateBuildings, a parcel holding a building with a curated year dates nothing else:
  // its recorded year is evidently another building's (a station's grounds, a campus).
  const ids = new Set(curated.map((d) => d.id))
  const distrusted = new Set(features.filter((f) => f.type === 'polygon' && ids.has(f.id)).map((f) => parcelAt(centroid((f as PolygonFeature).outers[0]))))
  const yearAt = (c: Vec2): number | null => {
    const k = parcelAt(c)
    if (k < 0 || distrusted.has(k)) return null
    return parcels[k].year >= 1700 ? parcels[k].year : null
  }
  const midpoint = (pts: readonly Vec2[]): Vec2 => {
    const lens = pts.slice(1).map((q, i) => Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]))
    let half = lens.reduce((a, b) => a + b, 0) / 2
    for (let i = 0; i < lens.length; i++) {
      if (half <= lens[i] && lens[i] > 0) { const t = half / lens[i]; return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t] }
      half -= lens[i]
    }
    return pts[0]
  }
  const out = new Map<string, Dated>()
  for (const f of features) {
    let at: Vec2 | null = null
    if (f.type === 'polygon' && f.tags.building === undefined && Object.entries(PARCEL_GROUNDS).some(([k, vs]) => vs.includes(f.tags[k] ?? ''))) at = centroid(f.outers[0])
    else if (f.type === 'line' && f.tags.highway === 'service' && f.points.length > 1) at = midpoint(f.points)
    if (at === null) continue
    const y = yearAt(at)
    if (y !== null) out.set(f.id, { year: y, source: 'parcel' })
  }
  return out
}

/**
 * The ways that lead only to a road bridge not drawn this year (`kept` are the features drawn,
 * `all` every feature mapped): from each end of such a bridge, ways joined end to end through
 * nodes no other drawn street touches, up to the first junction. With them gone the street ends
 * at that junction, not in a stub pointing at a bridge that is not there.
 */
export const dropApproaches = (all: readonly Feature[], kept: readonly Feature[], anchors: ReadonlySet<string> = new Set()): { kept: Feature[]; dropped: number } => {
  const isRoad = (f: Feature): f is Extract<Feature, { type: 'line' }> => f.type === 'line' && f.tags.highway !== undefined
  const keptIds = new Set(kept.map((f) => f.id))
  const key = (p: Vec2) => `${p[0]},${p[1]}`
  const roads = kept.filter(isRoad)
  const at = new Map<string, Extract<Feature, { type: 'line' }>[]>()
  for (const f of roads) for (const p of f.points) {
    const k = key(p)
    const list = at.get(k)
    if (list) list.push(f)
    else at.set(k, [f])
  }
  const gone = new Set<Feature>()
  const lostBridges = all.filter((f) => isRoad(f) && !keptIds.has(f.id) && f.tags.bridge !== undefined && f.tags.bridge !== 'no') as Extract<Feature, { type: 'line' }>[]
  for (const b of lostBridges) {
    for (const end of [b.points[0], b.points[b.points.length - 1]]) {
      let node = key(end)
      for (let guard = 0; guard < 50; guard++) {
        // A curated bridge of the year lands here: the street goes on to it.
        if (anchors.has(node)) break
        const here = (at.get(node) ?? []).filter((f) => !gone.has(f))
        if (here.length !== 1) break
        const w = here[0]
        // Only a way that ends here leads on; one passing through is a street of its own.
        const ends = [key(w.points[0]), key(w.points[w.points.length - 1])]
        if (!ends.includes(node)) break
        // Nor one with a street joining it along the way.
        if (w.points.slice(1, -1).some((p) => (at.get(key(p)) ?? []).some((o) => o !== w && !gone.has(o)))) break
        gone.add(w)
        node = ends[0] === node ? ends[1] : ends[0]
      }
    }
  }
  return { kept: kept.filter((f) => !gone.has(f)), dropped: gone.size }
}

/**
 * Streets mended after the year's drops (`streetEnds`): a run of minor-street ways left out only
 * for want of a house beside it (`unbuilt`), no longer than `gap` meters and joining drawn
 * roads at two or more places, is put back, so a street does not break where one block is
 * empty; then a road way with an end that met only roads not drawn this year (a later bridge,
 * ramp or interchange, not a street left out for want of houses) and meets no drawn road is
 * left out too, and so on back to the nearest junction, so no approach ends square in a field.
 */
/** Meters: how far back from a later work `mendStreets` leaves out the ways that led to it. */
export const ENDS_REACH = 250

export const mendStreets = (
  all: readonly Feature[], kept: readonly Feature[], unbuilt: ReadonlySet<string>, gap: number, anchors: ReadonlySet<string> = new Set(),
): { kept: Feature[]; mended: number; ends: number } => {
  type Line = Extract<Feature, { type: 'line' }>
  const isRoad = (f: Feature): f is Line => f.type === 'line' && f.tags.highway !== undefined
  const key = (p: Vec2) => `${p[0]},${p[1]}`
  let lat0 = 0, n = 0
  for (const f of all) if (f.type === 'line' && f.points.length) { lat0 += f.points[0][1]; n++ }
  lat0 = n ? lat0 / n : 0
  const kx = 111_320 * Math.cos((lat0 * Math.PI) / 180), ky = 110_574
  const len = (f: Line) => f.points.reduce((a, p, i) => (i === 0 ? 0 : a + Math.hypot((p[0] - f.points[i - 1][0]) * kx, (p[1] - f.points[i - 1][1]) * ky)), 0)
  const allRoads = all.filter(isRoad)
  const byNode = new Map<string, Line[]>()
  for (const f of allRoads) for (const p of f.points) {
    const k = key(p)
    const l = byNode.get(k)
    if (l) l.push(f)
    else byNode.set(k, [f])
  }
  const keep = new Set(kept.filter(isRoad).map((f) => f.id))
  // 1. Gaps: components of unbuilt ways, joined at shared nodes.
  let mended = 0
  const seen = new Set<string>()
  for (const f of allRoads) {
    if (!unbuilt.has(f.id) || seen.has(f.id)) continue
    const comp: Line[] = []
    const stack = [f]
    seen.add(f.id)
    while (stack.length) {
      const w = stack.pop()!
      comp.push(w)
      for (const p of w.points) for (const o of byNode.get(key(p)) ?? []) if (unbuilt.has(o.id) && !seen.has(o.id)) { seen.add(o.id); stack.push(o) }
    }
    const meets = new Set<string>()
    for (const w of comp) for (const p of w.points) if ((byNode.get(key(p)) ?? []).some((o) => keep.has(o.id))) meets.add(key(p))
    if (meets.size >= 2 && comp.reduce((a, w) => a + len(w), 0) <= gap) {
      for (const w of comp) keep.add(w.id)
      mended += comp.length
    }
  }
  // 2. Ends that led only to later works.
  // Only roads count as later works (a bridge, a ramp, a main road), not paths and drives.
  const works = (f: Line) => (f.tags.bridge !== undefined && f.tags.bridge !== 'no') ||
    /^(motorway|trunk|primary|secondary|tertiary)(_link)?$/.test(f.tags.highway ?? '')
  const later = new Set(allRoads.filter((f) => !keep.has(f.id) && !unbuilt.has(f.id) && works(f)).map((f) => f.id))
  // How far back from the later work each way left out lies: a chain is followed back only
  // `ENDS_REACH` meters, so a long road that also led elsewhere is not lost whole.
  const back = new Map<string, number>()
  let ends = 0
  for (let round = 0; round < 40; round++) {
    let changed = false
    for (const f of allRoads) {
      if (!keep.has(f.id) || (f.tags.bridge !== undefined && f.tags.bridge !== 'no')) continue
      for (const end of [f.points[0], f.points[f.points.length - 1]]) {
        const others = (byNode.get(key(end)) ?? []).filter((o) => o !== f)
        if (others.length === 0 || others.some((o) => keep.has(o.id)) || anchors.has(key(end))) continue
        const from = others.filter((o) => later.has(o.id)).map((o) => back.get(o.id) ?? 0)
        if (from.length === 0) continue
        const d = Math.min(...from) + len(f)
        if (d > ENDS_REACH) continue
        keep.delete(f.id)
        later.add(f.id)
        back.set(f.id, d)
        ends++
        changed = true
        break
      }
    }
    if (!changed) break
  }
  const out = all.filter((f) => isRoad(f) && keep.has(f.id) && !kept.includes(f))
  return { kept: [...kept.filter((f) => !isRoad(f) || keep.has(f.id)), ...out], mended, ends }
}

/** Bridges a series draws at grade before a year (`atGrade`): their bridge and layer tags dropped. */
export const bridgesAtGrade = (kept: readonly Feature[], year: number, h: History): { kept: Feature[]; n: number } => {
  const ids = new Set((h.atGrade ?? []).filter((r) => year < r.before).flatMap((r) => r.id))
  let n = 0
  const out = kept.map((f) => {
    if (f.type !== 'line' || !ids.has(f.id)) return f
    n++
    const { bridge: _b, layer: _l, ...tags } = f.tags
    return { ...f, tags }
  })
  return { kept: out, n }
}

/**
 * Road bridges that lead nowhere this year: a chain of bridge ways joined end to end with an end
 * no drawn road reaches (its ramps not yet built, its street gone) would stand in the air, so
 * the chain is left out.
 */
export const dropOrphanBridges = (kept: readonly Feature[]): { kept: Feature[]; dropped: number } => {
  type Line = Extract<Feature, { type: 'line' }>
  const isRoad = (f: Feature): f is Line => f.type === 'line' && f.tags.highway !== undefined
  const isSpan = (f: Line) => f.tags.bridge !== undefined && f.tags.bridge !== 'no'
  const key = (p: Vec2) => `${p[0]},${p[1]}`
  const roads = kept.filter(isRoad)
  const at = new Map<string, Line[]>()
  for (const f of roads) for (const p of f.points) {
    const k = key(p)
    const list = at.get(k)
    if (list) list.push(f)
    else at.set(k, [f])
  }
  const spans = roads.filter(isSpan)
  const parent = new Map(spans.map((f) => [f, f]))
  const find = (f: Line): Line => { let r = f; while (parent.get(r) !== r) r = parent.get(r)!; return r }
  for (const f of spans) for (const p of [f.points[0], f.points[f.points.length - 1]]) {
    for (const o of at.get(key(p)) ?? []) if (o !== f && isSpan(o)) parent.set(find(o), find(f))
  }
  const chains = new Map<Line, Line[]>()
  for (const f of spans) { const r = find(f); const list = chains.get(r); if (list) list.push(f); else chains.set(r, [f]) }
  const gone = new Set<Feature>()
  for (const members of chains.values()) {
    const mine = new Set(members)
    // The chain's ends: span ends not shared with another span of the chain.
    const ends = members.flatMap((f) => [f.points[0], f.points[f.points.length - 1]])
      .filter((p) => (at.get(key(p)) ?? []).filter((o) => mine.has(o)).length === 1)
    const reached = (p: Vec2) => (at.get(key(p)) ?? []).some((o) => !mine.has(o))
    if (ends.length > 0 && !ends.every(reached)) for (const f of members) gone.add(f)
  }
  return { kept: kept.filter((f) => !gone.has(f)), dropped: gone.size }
}

/** Minor roads whose bridges over a canal `canalBridgesFrom` holds to its year. */
const CANAL_BRIDGE_ROADS = new Set(['residential', 'service', 'unclassified', 'living_street'])

/** Planted ground: what `pastGround` dates with the buildings around it when it is small. */
const PLANTING = new Set(['scrub', 'wood', 'grassland', 'heath', 'water'])

/**
 * What a past year leaves out that only its neighbors can show (never called for today's scene):
 *
 * - A minor road bridge with no `start_date` crossing a canal (a canal way or a canal's water)
 *   is not drawn before the history's `canalBridgesFrom`, unless a rule names it (`id`).
 * - A road bridge whose spans, joined end to end, do not meet a road of the year at each of
 *   their ends (a tunnel does not count: it is not drawn) is left out: a piece of deck whose
 *   approaches came later, or that leads into nothing drawn.
 * - Planting beds and ponds: a polygon of scrub, wood, grassland, heath or still water (no name,
 *   no waterway) under `small` m² is landscaping, dated with the nearest dated building within
 *   `reach` meters (the development around it): drawn only from that building's year. With no
 *   dated building that near it is not part of a development (a thicket on a river island) and
 *   is kept.
 *
 * - A rail spur, siding or yard track that ends with no building of the year within `reach`
 *   meters of its end is left out, and so on back along the spurs that led only to it: today's
 *   spurs serve today's buildings, and drawn in a past year one stops dead in open ground.
 *
 * `kept` are the features standing in `year` (after the era rules), `all` every feature mapped
 * today, `dates` the buildings' years, `traced` points of the year's traced buildings. Returns
 * the kept features and the counts left out.
 */
export const pastGround = (
  all: readonly Feature[], kept: readonly Feature[], year: number, h: History, dates: ReadonlyMap<string, { readonly year: number }>,
  small = 2000, reach = 40, traced: readonly Vec2[] = [],
): { kept: Feature[]; canalBridges: number; orphanBridges: number; plantings: number; spurs: number } => {
  const lat0 = all.length > 0 ? (all[0].type === 'line' ? all[0].points[0][1] : all[0].outers[0][0][1]) : 0
  const kx = 111320 * Math.cos((lat0 * Math.PI) / 180), ky = 110540
  const m = (p: Vec2): Vec2 => [p[0] * kx, p[1] * ky]
  const named = new Set(h.rules.flatMap((r) => r.where.id ?? []))
  const isRoadBridge = (f: Feature): f is Extract<Feature, { type: 'line' }> => f.type === 'line' && f.tags.highway !== undefined && f.tags.bridge !== undefined && f.tags.bridge !== 'no'
  // Canals: their ways and their water, in meters.
  const canalLines = all.filter((f): f is Extract<Feature, { type: 'line' }> => f.type === 'line' && f.tags.waterway === 'canal').map((f) => f.points.map(m))
  const canalRings = all.filter((f): f is PolygonFeature => f.type === 'polygon' && (f.tags.water === 'canal' || f.tags.waterway === 'canal')).flatMap((f) => f.outers.map((r) => r.map(m)))
  const overCanal = (pts: readonly Vec2[]): boolean => {
    const q = pts.map(m)
    for (let i = 1; i < q.length; i++) {
      for (const c of [...canalLines, ...canalRings.map((r) => [...r, r[0]])]) {
        for (let k = 1; k < c.length; k++) if (crosses(q[i - 1], q[i], c[k - 1], c[k])) return true
      }
    }
    return q.some((p) => canalRings.some((r) => pointInRing(p, r)))
  }
  let canalBridges = 0
  let out = kept.filter((f) => {
    if (h.canalBridgesFrom === undefined || year >= h.canalBridgesFrom || !isRoadBridge(f) || !CANAL_BRIDGE_ROADS.has(f.tags.highway ?? '')) return true
    if (named.has(f.id) || parseYear(f.tags.start_date) !== null || !overCanal(f.points)) return true
    canalBridges++
    return false
  })
  // Bridges joined end to end (by shared end points), and whether any end of the group meets a
  // road of the year that is not one of its own spans.
  const key = (p: Vec2) => `${p[0]},${p[1]}`
  const roadNodes = new Set<string>()
  for (const f of out) if (f.type === 'line' && f.tags.highway !== undefined && (f.tags.bridge === undefined || f.tags.bridge === 'no') && (f.tags.tunnel === undefined || f.tags.tunnel === 'no')) for (const p of f.points) roadNodes.add(key(p))
  const spans = out.filter(isRoadBridge)
  const parent = new Map(spans.map((f) => [f.id, f.id]))
  const find = (id: string): string => { let r = id; while (parent.get(r) !== r) r = parent.get(r)!; return r }
  const byEnd = new Map<string, string[]>()
  for (const f of spans) for (const p of [f.points[0], f.points[f.points.length - 1]]) byEnd.set(key(p), [...(byEnd.get(key(p)) ?? []), f.id])
  for (const ids of byEnd.values()) for (const id of ids.slice(1)) parent.set(find(id), find(ids[0]))
  // A group's free ends: span ends no other span of the group shares. Each must meet a road of
  // the year (not a tunnel, which is not drawn): a deck that ends in nothing, or runs into a
  // tunnel, is a stub.
  const ends = new Map<string, Vec2[]>()
  for (const f of spans) {
    for (const p of [f.points[0], f.points[f.points.length - 1]]) {
      if ((byEnd.get(key(p)) ?? []).length > 1) continue
      const g = find(f.id)
      ends.set(g, [...(ends.get(g) ?? []), p])
    }
  }
  const landed = new Set<string>()
  for (const [g, ps] of ends) if (ps.every((p) => roadNodes.has(key(p)))) landed.add(g)
  let orphanBridges = 0
  out = out.filter((f) => {
    if (!isRoadBridge(f) || landed.has(find(f.id))) return true
    orphanBridges++
    return false
  })
  // Plantings, dated with the nearest dated building within `reach`.
  const buildings = all.filter((f): f is PolygonFeature => f.type === 'polygon' && (f.tags.building !== undefined || f.tags['building:part'] !== undefined) && dates.has(f.id))
    .map((f) => ({ ring: f.outers[0].map(m), year: dates.get(f.id)!.year }))
  const area = (r: readonly Vec2[]) => Math.abs(r.reduce((a, p, i) => { const q = r[(i + 1) % r.length]; return a + p[0] * q[1] - q[0] * p[1] }, 0)) / 2
  const gap = (a: readonly Vec2[], b: readonly Vec2[]): number => {
    let best = Infinity
    for (const p of a) for (let i = 0; i < b.length; i++) {
      const s = b[i], e = b[(i + 1) % b.length]
      const dx = e[0] - s[0], dy = e[1] - s[1], l2 = dx * dx + dy * dy
      const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - s[0]) * dx + (p[1] - s[1]) * dy) / l2))
      best = Math.min(best, Math.hypot(p[0] - s[0] - t * dx, p[1] - s[1] - t * dy))
    }
    return best
  }
  let plantings = 0
  out = out.filter((f) => {
    if (f.type !== 'polygon' || !PLANTING.has(f.tags.natural ?? '') || f.tags.name !== undefined || f.tags.waterway !== undefined) return true
    if (f.tags.natural === 'water' && f.tags.water !== undefined && f.tags.water !== 'pond') return true
    const ring = f.outers[0].map(m)
    if (area(ring) >= small) return true
    const [x0, y0] = ring.reduce((a, p) => [Math.min(a[0], p[0]), Math.min(a[1], p[1])], [Infinity, Infinity])
    const [x1, y1] = ring.reduce((a, p) => [Math.max(a[0], p[0]), Math.max(a[1], p[1])], [-Infinity, -Infinity])
    let nearest: { d: number; year: number } | null = null
    for (const b of buildings) {
      if (!b.ring.some((p) => p[0] > x0 - reach && p[0] < x1 + reach && p[1] > y0 - reach && p[1] < y1 + reach)) continue
      const d = Math.min(gap(ring, b.ring), gap(b.ring, ring))
      if (d <= reach && (nearest === null || d < nearest.d)) nearest = { d, year: b.year }
    }
    // With no building that near, it is not part of a development: natural ground, kept.
    if (nearest === null || nearest.year <= year) return true
    plantings++
    return false
  })
  // Spurs that serve nothing of the year.
  const standing: Vec2[] = [
    ...out.flatMap((f) => (f.type === 'polygon' && (f.tags.building !== undefined || f.tags['building:part'] !== undefined) ? f.outers[0].map(m) : [])),
    ...traced.map(m),
  ]
  const cell = reach
  const grid = new Set(standing.map((p) => `${Math.floor(p[0] / cell)},${Math.floor(p[1] / cell)}`))
  const served = (p: Vec2): boolean => {
    const [x, y] = m(p)
    const i = Math.floor(x / cell), j = Math.floor(y / cell)
    for (let di = -1; di <= 1; di++) for (let dj = -1; dj <= 1; dj++) if (grid.has(`${i + di},${j + dj}`)) return true
    return false
  }
  const isSpur = (f: Feature): f is Extract<Feature, { type: 'line' }> => f.type === 'line' && f.tags.railway !== undefined && ['spur', 'siding', 'yard'].includes(f.tags.service ?? '')
  let spurs = 0
  for (;;) {
    const rails = out.filter((f): f is Extract<Feature, { type: 'line' }> => f.type === 'line' && f.tags.railway !== undefined)
    const uses = new Map<string, number>()
    for (const f of rails) for (const p of f.points) uses.set(key(p), (uses.get(key(p)) ?? 0) + 1)
    const dead = new Set(rails.filter(isSpur).filter((f) => [f.points[0], f.points[f.points.length - 1]].some((e) => uses.get(key(e)) === 1 && !served(e))).map((f) => f.id))
    if (dead.size === 0) break
    spurs += dead.size
    out = out.filter((f) => !dead.has(f.id))
  }
  return { kept: out, canalBridges, orphanBridges, plantings, spurs }
}
