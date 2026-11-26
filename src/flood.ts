/**
 * Floods (experimental): where the river stood at a given surface, drawn over today's ground.
 *
 * This is a bathtub fill, not hydraulics. A flood says the water stood at an elevation (meters,
 * the elevation model's own datum), level or falling along the river through control points.
 * Every node of the terrain's 5 m grid that lies below that surface and can be reached from the
 * river through other such nodes, without crossing a floodwall whose top is above the water, is
 * flooded. A pond is the other mode: water at one level inside a polygon, connected to the river
 * or not (rain that could not drain behind a wall). Depth is the surface minus the grid's
 * elevation, true meters.
 *
 * Everything here works in view meters on the terrain's grid, like `terrain.ts`.
 */

import { pointInPolygon, type Ring, type Vec2 } from './geom.ts'
import type { Feature } from './osm.ts'
import type { Region } from './region.ts'

// ---- config ----------------------------------------------------------------------------------

/** A floodwall: a line (or OSM's flood walls), with the elevation of its top. */
export interface FloodWallSpec {
  readonly name: string
  /** Take every OSM way tagged `wall=<osm>` (e.g. "flood_wall"), chained end to end. */
  readonly osm?: string
  /** Or a line given here, [lon, lat] points. */
  readonly line?: readonly (readonly [number, number])[]
  /** Elevation of the wall's top, meters (the elevation model's datum). */
  readonly top: number
  /** Gaps between OSM pieces up to this many meters are closed (gates shut in a flood). Default 60. */
  readonly maxGap?: number
  readonly note?: string
  /** The year it stood from: a dated scene before it has no wall. */
  readonly from?: number
  readonly sources?: readonly string[]
  /** Words set on the map beside it (one label, at its longest line's middle). */
  readonly label?: string
}

/** A place marked with a number on a flood's picture, keyed in its caption. */
export interface FloodMarker {
  readonly n: string
  readonly at: readonly [number, number]
  /** Words for the key: the place, the reported depth and its source. */
  readonly key: string
  /** Which side of the place the number sits: 'end' to its left, 'start' to its right. */
  readonly anchor?: 'start' | 'middle' | 'end'
}

/** Water standing at one level in a polygon, whether or not the river reaches it. */
export interface PondSpec {
  readonly level: number
  readonly ring: readonly (readonly [number, number])[]
  /**
   * A low point [lon, lat]: the pond is then only the ground below its level connected to this
   * point (a pool rising in a bowl), not every hollow inside the ring.
   */
  readonly from?: readonly [number, number]
  /**
   * Held on the city side of the walls (with `from`): the pool does not spread across a floodwall
   * or across the line of its openings, whatever the flood's `gates`. A rain pool behind a wall
   * whose gates stood open beside a low river drained out through them; it did not stand on the
   * river side.
   */
  readonly citySide?: boolean
}

export interface FloodSpec {
  readonly name: string
  readonly title?: string
  /** A line printed above the plate (a rough test says so here). */
  readonly caption?: string
  /** The river's surface, level everywhere: meters (the elevation model's datum). */
  readonly level?: number
  /**
   * Or a surface falling along the river: [lon, lat, elevation] control points in order along
   * the channel. Each node takes the elevation at its nearest point on this line, interpolated
   * by distance along it (held at the end values past either end).
   */
  readonly profile?: readonly (readonly [number, number, number])[]
  /** The river's flood only inside this polygon ([lon, lat] ring). */
  readonly within?: readonly (readonly [number, number])[]
  readonly ponds?: readonly PondSpec[]
  /** Which floodwalls stand: true for all of the region's, false or absent for none, or names. */
  readonly walls?: boolean | readonly string[]
  /**
   * The walls' openings (the gaps between OSM's pieces): "closed" (default) in a river flood, the
   * gates shut, so the wall runs across them; "open", drawn open and letting water through.
   */
  readonly gates?: 'open' | 'closed'
  /**
   * Plus or minus this many meters on the surface: the ground between the waterlines at the
   * level and at the level plus this is drawn as a pale band, the range of the estimate.
   * With `band: "range"` the water itself is drawn at the level minus this, and the band runs
   * from there to the level plus this.
   */
  readonly uncertainty?: number
  readonly band?: 'beyond' | 'range'
  /** A soft-edged pool: no inked waterline, its edge fading from the land into the water. */
  readonly soft?: boolean
  readonly markers?: readonly FloodMarker[]
  /** Staff gauges: at each place under water, a post from the ground to the surface with a tick every 5 ft, and the depth in feet. */
  readonly gauges?: readonly { readonly at: readonly [number, number]; readonly name?: string }[]
  /** More caption lines (the first is `caption`); `{name}` is replaced by the build's measure. */
  readonly notes?: readonly string[]
  /**
   * A dry twin's wet flood (`twinOf` in the region file, the flood's name): its reach, not the
   * twin's own (dry) water, decides what is near the water (outbuildings left out), so the twin
   * draws the same buildings as its flood.
   */
  readonly reach?: FloodSpec
  /**
   * Ground whose protection the data cannot show (a levee that is not mapped): `lines` ([lon,
   * lat] runs) close every course the missing levee might take. Land the fill floods with the
   * walls standing, but would not flood were these lines walls too (at the first wall's top), is
   * drawn as unknown (a hatch, no water, no depth) and counted apart. `note` is its key line.
   */
  readonly unknown?: { readonly lines: readonly (readonly (readonly [number, number])[])[]; readonly note?: string }
}

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const isPoint = (v: unknown, n: number): boolean => Array.isArray(v) && v.length >= n && v.slice(0, n).every(isNum)

/** The region's flood `name`, checked; throws with a plain message on anything malformed. */
export const parseFlood = (region: Region, name: string): FloodSpec => {
  const all = (region as { floods?: unknown }).floods
  if (all === null || typeof all !== 'object' || Array.isArray(all)) throw new Error(`regions/${region.name}.json has no "floods"`)
  const raw = (all as Record<string, unknown>)[name]
  if (raw === null || typeof raw !== 'object') throw new Error(`regions/${region.name}.json: no flood "${name}" (have: ${Object.keys(all).join(', ')})`)
  const r = raw as Record<string, unknown>
  const where = `regions/${region.name}.json floods.${name}`
  const out: { -readonly [K in keyof FloodSpec]: FloodSpec[K] } = { name }
  if (typeof r.title === 'string') out.title = r.title
  if (typeof r.caption === 'string') out.caption = r.caption
  if (r.level !== undefined) {
    if (!isNum(r.level)) throw new Error(`${where}: "level" must be a number of meters`)
    out.level = r.level
  }
  if (r.profile !== undefined) {
    if (!Array.isArray(r.profile) || r.profile.length < 2 || !r.profile.every((p) => isPoint(p, 3))) throw new Error(`${where}: "profile" must be two or more [lon, lat, elevation] points`)
    out.profile = r.profile as [number, number, number][]
  }
  if (r.within !== undefined) {
    if (!Array.isArray(r.within) || r.within.length < 3 || !r.within.every((p) => isPoint(p, 2))) throw new Error(`${where}: "within" must be a ring of [lon, lat] points`)
    out.within = r.within as [number, number][]
  }
  if (r.ponds !== undefined) {
    if (!Array.isArray(r.ponds)) throw new Error(`${where}: "ponds" must be a list`)
    out.ponds = r.ponds.map((p, k) => {
      const q = p as Record<string, unknown>
      if (!isNum(q?.level) || !Array.isArray(q.ring) || q.ring.length < 3 || !q.ring.every((v) => isPoint(v, 2))) throw new Error(`${where}: ponds[${k}] needs "level" (meters) and "ring" ([lon, lat] points)`)
      if (q.from !== undefined && !isPoint(q.from, 2)) throw new Error(`${where}: ponds[${k}].from must be [lon, lat]`)
      if (q.citySide !== undefined && typeof q.citySide !== 'boolean') throw new Error(`${where}: ponds[${k}].citySide must be true or false`)
      return { level: q.level, ring: q.ring as [number, number][], ...(q.from === undefined ? {} : { from: q.from as [number, number] }), ...(q.citySide === true ? { citySide: true } : {}) }
    })
  }
  if (r.walls !== undefined) {
    if (typeof r.walls === 'boolean') out.walls = r.walls
    else if (Array.isArray(r.walls) && r.walls.every((w) => typeof w === 'string')) out.walls = r.walls as string[]
    else throw new Error(`${where}: "walls" must be true, false or a list of wall names`)
  }
  if (r.gates !== undefined) {
    if (r.gates !== 'open' && r.gates !== 'closed') throw new Error(`${where}: "gates" must be "open" or "closed"`)
    out.gates = r.gates
  }
  if (r.uncertainty !== undefined) {
    if (!isNum(r.uncertainty) || r.uncertainty < 0) throw new Error(`${where}: "uncertainty" must be meters, zero or more`)
    out.uncertainty = r.uncertainty
  }
  if (r.band !== undefined) {
    if (r.band !== 'beyond' && r.band !== 'range') throw new Error(`${where}: "band" must be "beyond" or "range"`)
    out.band = r.band
  }
  if (r.soft !== undefined) out.soft = r.soft === true
  if (r.markers !== undefined) {
    if (!Array.isArray(r.markers)) throw new Error(`${where}: "markers" must be a list`)
    out.markers = r.markers.map((m, k) => {
      const q = m as Record<string, unknown>
      if (!isPoint(q?.at, 2) || typeof q.key !== 'string') throw new Error(`${where}: markers[${k}] needs "at" ([lon, lat]) and "key"`)
      const anchor = q.anchor === 'start' || q.anchor === 'end' || q.anchor === 'middle' ? { anchor: q.anchor as 'start' | 'middle' | 'end' } : {}
      return { n: typeof q.n === 'string' ? q.n : String(k + 1), at: q.at as [number, number], key: q.key, ...anchor }
    })
  }
  if (r.gauges !== undefined) {
    if (!Array.isArray(r.gauges) || !r.gauges.every((g) => isPoint((g as Record<string, unknown>)?.at, 2))) throw new Error(`${where}: "gauges" must be a list of { "at": [lon, lat] }`)
    out.gauges = (r.gauges as Record<string, unknown>[]).map((g) => ({ at: g.at as [number, number], ...(typeof g.name === 'string' ? { name: g.name } : {}) }))
  }
  if (r.notes !== undefined) {
    if (!Array.isArray(r.notes) || !r.notes.every((x) => typeof x === 'string')) throw new Error(`${where}: "notes" must be a list of lines`)
    out.notes = r.notes as string[]
  }
  if (r.unknown !== undefined) {
    const q = r.unknown as Record<string, unknown>
    if (q === null || typeof q !== 'object' || !Array.isArray(q.lines) || q.lines.length === 0 || !q.lines.every((l) => Array.isArray(l) && l.length >= 2 && l.every((v) => isPoint(v, 2)))) throw new Error(`${where}: "unknown" needs "lines": a list of [lon, lat] runs`)
    out.unknown = { lines: q.lines as [number, number][][], ...(typeof q.note === 'string' ? { note: q.note } : {}) }
  }
  if (r.twinOf !== undefined) {
    if (typeof r.twinOf !== 'string' || r.twinOf === name) throw new Error(`${where}: "twinOf" must name another flood`)
    out.reach = parseFlood(region, r.twinOf)
  }
  if (out.level === undefined && out.profile === undefined && (out.ponds ?? []).length === 0) throw new Error(`${where}: give a "level", a "profile" or "ponds"`)
  return out
}

/** The region's floodwalls that the flood says stand. */
export const parseWalls = (region: Region, flood: FloodSpec, year?: number): FloodWallSpec[] => {
  const raw = (region as { floodwalls?: unknown }).floodwalls
  if (flood.walls === undefined || flood.walls === false || raw === undefined) return []
  if (!Array.isArray(raw)) throw new Error(`regions/${region.name}.json: "floodwalls" must be a list`)
  const walls = raw.map((w, k): FloodWallSpec => {
    const q = w as Record<string, unknown>
    const where = `regions/${region.name}.json floodwalls[${k}]`
    if (!isNum(q?.top)) throw new Error(`${where}: "top" (meters) is required`)
    const name = typeof q.name === 'string' ? q.name : `wall ${k + 1}`
    const osm = typeof q.osm === 'string' ? q.osm : undefined
    const line = Array.isArray(q.line) && q.line.length >= 2 && q.line.every((p) => isPoint(p, 2)) ? (q.line as [number, number][]) : undefined
    if (osm === undefined && line === undefined) throw new Error(`${where}: give "osm" (a wall=* value) or a "line"`)
    return {
      name, top: q.top, ...(osm === undefined ? {} : { osm }), ...(line === undefined ? {} : { line }),
      ...(isNum(q.maxGap) ? { maxGap: q.maxGap } : {}), ...(typeof q.note === 'string' ? { note: q.note } : {}),
      ...(isNum(q.from) ? { from: q.from } : {}), ...(typeof q.label === 'string' ? { label: q.label } : {}),
      ...(Array.isArray(q.sources) && q.sources.every((x) => typeof x === 'string') ? { sources: q.sources as string[] } : {}),
    }
  })
  const named = flood.walls === true ? walls : walls.filter((w) => (flood.walls as readonly string[]).includes(w.name))
  // A dated scene before a wall was built has no wall.
  return year === undefined ? named : named.filter((w) => w.from === undefined || year >= w.from)
}

// ---- walls -----------------------------------------------------------------------------------

/** A barrier in view meters, with its top (elevation) at each point. */
export interface Barrier {
  readonly name: string
  readonly pts: readonly Vec2[]
  readonly top: number
  /** For each segment, true where it closes a gap between mapped pieces (an opening). */
  readonly gaps?: readonly boolean[]
  readonly label?: string
}

/** A barrier without its openings: the pieces between its gap segments. */
export const openPieces = (b: Barrier): Barrier[] => {
  if (b.gaps === undefined || !b.gaps.some((g) => g)) return [b]
  const out: Barrier[] = []
  let cur: Vec2[] = [b.pts[0]]
  for (let k = 0; k + 1 < b.pts.length; k++) {
    if (b.gaps[k]) {
      if (cur.length >= 2) out.push({ name: b.name, pts: cur, top: b.top })
      cur = [b.pts[k + 1]]
    } else cur.push(b.pts[k + 1])
  }
  if (cur.length >= 2) out.push({ name: b.name, pts: cur, top: b.top })
  return out
}

/**
 * Pieces of line joined end to end into as few lines as they make: repeatedly, the two free
 * ends nearest each other, if within `maxGap` meters, are joined (reversing pieces as needed).
 */
export const chainLines = (pieces: readonly (readonly Vec2[])[], maxGap: number): Vec2[][] => {
  const lines = pieces.filter((p) => p.length >= 2).map((p) => p.slice())
  const d = (a: Vec2, b: Vec2) => Math.hypot(a[0] - b[0], a[1] - b[1])
  for (;;) {
    let best: { i: number; j: number; ei: 0 | 1; ej: 0 | 1; gap: number } | null = null
    for (let i = 0; i < lines.length; i++) {
      for (let j = i + 1; j < lines.length; j++) {
        for (const ei of [0, 1] as const) {
          for (const ej of [0, 1] as const) {
            const a = ei === 0 ? lines[i][0] : lines[i][lines[i].length - 1]
            const b = ej === 0 ? lines[j][0] : lines[j][lines[j].length - 1]
            const gap = d(a, b)
            if (gap <= maxGap && (best === null || gap < best.gap)) best = { i, j, ei, ej, gap }
          }
        }
      }
    }
    if (best === null) return lines
    const a = best.ei === 0 ? lines[best.i].slice().reverse() : lines[best.i]
    const b = best.ej === 0 ? lines[best.j] : lines[best.j].slice().reverse()
    const joined = best.gap < 1e-6 ? [...a, ...b.slice(1)] : [...a, ...b]
    lines.splice(best.j, 1)
    lines[best.i] = joined
  }
}

/** The barriers a flood's walls make, in view meters. */
export const barriersOf = (walls: readonly FloodWallSpec[], features: readonly Feature[], toView: (lon: number, lat: number) => Vec2): Barrier[] => {
  const out: Barrier[] = []
  for (const w of walls) {
    const label = w.label === undefined ? {} : { label: w.label }
    if (w.line !== undefined) out.push({ name: w.name, pts: w.line.map(([lon, lat]) => toView(lon, lat)), top: w.top, ...label })
    if (w.osm !== undefined) {
      const pieces = features.filter((f) => f.type === 'line' && f.tags.wall === w.osm).map((f) => (f.type === 'line' ? f.points.map(([lon, lat]) => toView(lon, lat)) : []))
      // A segment that lies on no mapped piece closes a gap between two: an opening.
      const mapped = new Set<string>()
      const key = (a: Vec2, b: Vec2) => `${a[0]},${a[1]}|${b[0]},${b[1]}`
      for (const p of pieces) for (let k = 0; k + 1 < p.length; k++) { mapped.add(key(p[k], p[k + 1])); mapped.add(key(p[k + 1], p[k])) }
      for (const pts of chainLines(pieces, w.maxGap ?? 60)) {
        const gaps = pts.slice(1).map((q, k) => !mapped.has(key(pts[k], q)))
        out.push({ name: w.name, pts, top: w.top, gaps, ...label })
      }
    }
  }
  // An end within SNAP_ENDS meters of another wall's point is moved onto it, so a line given
  // to tie a mapped wall into high ground meets it exactly: a gap of a meter or two let the
  // water through between two grid nodes.
  for (const b of out) {
    const pts = b.pts as Vec2[]
    for (const at of [0, pts.length - 1]) {
      let best = SNAP_ENDS
      for (const o of out) {
        if (o === b) continue
        for (const p of o.pts) {
          const d = Math.hypot(p[0] - pts[at][0], p[1] - pts[at][1])
          if (d < best) { best = d; pts[at] = [p[0], p[1]] }
        }
      }
    }
  }
  return out
}

/** Meters: how near a wall's end must be to another wall to be joined to it. */
export const SNAP_ENDS = 5

// ---- the fill --------------------------------------------------------------------------------

/** A height grid in view meters, row-major from the near edge (see `Terrain`). */
export interface FloodGrid {
  readonly elev: Float32Array
  readonly nx: number
  readonly ny: number
  readonly x0: number
  readonly y0: number
  readonly cell: number
}

/** 1 for each node inside `rings` (view meters, even-odd). */
export const nodesInside = (g: FloodGrid, rings: readonly Ring[]): Uint8Array => {
  const m = new Uint8Array(g.nx * g.ny)
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  for (const r of rings) for (const [x, y] of r) { minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y) }
  const i0 = Math.max(0, Math.floor((minX - g.x0) / g.cell)), i1 = Math.min(g.nx - 1, Math.ceil((maxX - g.x0) / g.cell))
  const j0 = Math.max(0, Math.floor((minY - g.y0) / g.cell)), j1 = Math.min(g.ny - 1, Math.ceil((maxY - g.y0) / g.cell))
  for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) if (pointInPolygon([g.x0 + i * g.cell, g.y0 + j * g.cell], rings)) m[j * g.nx + i] = 1
  return m
}

/**
 * A surface falling along a line: each node takes the elevation at its nearest point on the
 * line through `pts` (view meters), interpolated by distance along the line between the
 * control elevations `elevs`, and held at the end values past either end.
 */
export const profileSurface = (g: FloodGrid, pts: readonly Vec2[], elevs: readonly number[]): Float32Array => {
  const cum = [0]
  for (let k = 1; k < pts.length; k++) cum.push(cum[k - 1] + Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]))
  const out = new Float32Array(g.nx * g.ny)
  for (let j = 0; j < g.ny; j++) {
    for (let i = 0; i < g.nx; i++) {
      const p: Vec2 = [g.x0 + i * g.cell, g.y0 + j * g.cell]
      let best = Infinity
      let at = 0
      for (let k = 0; k + 1 < pts.length; k++) {
        const a = pts[k], b = pts[k + 1]
        const dx = b[0] - a[0], dy = b[1] - a[1], l2 = dx * dx + dy * dy
        const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
        const d = Math.hypot(a[0] + dx * t - p[0], a[1] + dy * t - p[1])
        if (d < best) { best = d; at = cum[k] + t * (cum[k + 1] - cum[k]) }
      }
      let e = elevs[elevs.length - 1]
      for (let k = 0; k + 1 < pts.length; k++) {
        if (at <= cum[k + 1] || k + 2 === pts.length) {
          const u = cum[k + 1] === cum[k] ? 0 : Math.max(0, Math.min(1, (at - cum[k]) / (cum[k + 1] - cum[k])))
          e = elevs[k] + (elevs[k + 1] - elevs[k]) * u
          break
        }
      }
      out[j * g.nx + i] = e
    }
  }
  return out
}

const cross = (a: Vec2, b: Vec2, c: Vec2, d: Vec2): number | null => {
  // Where a–b meets c–d, as a fraction along c–d, or null.
  const rx = b[0] - a[0], ry = b[1] - a[1], sx = d[0] - c[0], sy = d[1] - c[1]
  const den = rx * sy - ry * sx
  if (Math.abs(den) < 1e-12) return null
  const t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / den
  const u = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / den
  return t >= 0 && t <= 1 && u >= 0 && u <= 1 ? u : null
}

/**
 * The top (elevation) of the highest barrier crossing each link between neighboring nodes:
 * `h[k]` for the link from node k to k + 1, `v[k]` from k to k + nx. −Infinity where none.
 */
export const barrierLinks = (g: FloodGrid, barriers: readonly Barrier[]): { h: Float32Array; v: Float32Array } => {
  const h = new Float32Array(g.nx * g.ny).fill(-Infinity)
  const v = new Float32Array(g.nx * g.ny).fill(-Infinity)
  const node = (i: number, j: number): Vec2 => [g.x0 + i * g.cell, g.y0 + j * g.cell]
  for (const b of barriers) {
    for (let s = 0; s + 1 < b.pts.length; s++) {
      const p = b.pts[s], q = b.pts[s + 1]
      const i0 = Math.max(0, Math.floor((Math.min(p[0], q[0]) - g.x0) / g.cell) - 1), i1 = Math.min(g.nx - 1, Math.ceil((Math.max(p[0], q[0]) - g.x0) / g.cell) + 1)
      const j0 = Math.max(0, Math.floor((Math.min(p[1], q[1]) - g.y0) / g.cell) - 1), j1 = Math.min(g.ny - 1, Math.ceil((Math.max(p[1], q[1]) - g.y0) / g.cell) + 1)
      for (let j = j0; j <= j1; j++) {
        for (let i = i0; i <= i1; i++) {
          const k = j * g.nx + i
          if (i + 1 < g.nx && cross(node(i, j), node(i + 1, j), p, q) !== null) h[k] = Math.max(h[k], b.top)
          if (j + 1 < g.ny && cross(node(i, j), node(i, j + 1), p, q) !== null) v[k] = Math.max(v[k], b.top)
        }
      }
    }
  }
  return { h, v }
}

export interface FloodInput {
  /** The river's flood surface at each node (elevation), NaN where it does not reach. */
  readonly surface?: Float32Array
  /**
   * Nodes the river's water may start from (open water); the fill starts from the largest group
   * of them connected without crossing a barrier (see `largestGroup`).
   */
  readonly seeds?: Uint8Array
  /** Nodes the river's flood may reach (absent: all). */
  readonly within?: Uint8Array
  readonly barriers?: readonly Barrier[]
  /** With `seed` (a node index), only the nodes connected to it below the level (4-connected, in the mask). */
  readonly ponds?: readonly { readonly mask: Uint8Array; readonly level: number; readonly seed?: number; readonly barriers?: readonly Barrier[] }[]
}

export interface FloodField {
  /** 1 where a node is under water: 1 from the river, 2 from a pond (pond wins where higher). */
  readonly flooded: Uint8Array
  /** The water's surface elevation at flooded nodes; NaN elsewhere. */
  readonly level: Float32Array
  /** The water's depth at flooded nodes (true meters); NaN elsewhere. */
  readonly depth: Float32Array
  /** How many links a barrier held (the water stood against it below its top). */
  readonly held: number
  /** How many links the water crossed over a barrier's top. */
  readonly overtopped: number
}

/**
 * The bathtub fill. From each seed below the surface, flood every node 4-connected to it
 * through nodes below the surface (within `within`), never across a barrier link whose top is
 * at or above the water there (the mean of the two nodes' surface). Then each pond floods every
 * node inside its mask below its level, connected or not.
 */
export const fillFlood = (g: FloodGrid, inp: FloodInput): FloodField => {
  const n = g.nx * g.ny
  const flooded = new Uint8Array(n)
  const level = new Float32Array(n).fill(NaN)
  let held = 0
  let overtopped = 0
  const S = inp.surface
  if (S !== undefined && inp.seeds !== undefined) {
    const links = inp.barriers !== undefined && inp.barriers.length > 0 ? barrierLinks(g, inp.barriers) : null
    const queue = new Int32Array(n)
    let head = 0
    let tail = 0
    const may = (k: number) => flooded[k] === 0 && !Number.isNaN(S[k]) && g.elev[k] < S[k] && (inp.within === undefined || inp.within[k] === 1)
    const river = largestGroup(inp.seeds, g.nx, g.ny, links ?? undefined)
    for (let k = 0; k < n; k++) if (river[k] === 1 && may(k)) { flooded[k] = 1; level[k] = S[k]; queue[tail++] = k }
    const step = (k: number, q: number, top: number) => {
      if (!may(q)) return
      if (top > -Infinity) {
        if (top >= (S[k] + S[q]) / 2) { held++; return }
        overtopped++
      }
      flooded[q] = 1
      level[q] = S[q]
      queue[tail++] = q
    }
    while (head < tail) {
      const k = queue[head++]
      const i = k % g.nx
      const j = (k - i) / g.nx
      if (i + 1 < g.nx) step(k, k + 1, links === null ? -Infinity : links.h[k])
      if (i > 0) step(k, k - 1, links === null ? -Infinity : links.h[k - 1])
      if (j + 1 < g.ny) step(k, k + g.nx, links === null ? -Infinity : links.v[k])
      if (j > 0) step(k, k - g.nx, links === null ? -Infinity : links.v[k - g.nx])
    }
  }
  for (const p of inp.ponds ?? []) {
    let reach: Uint8Array | null = null
    if (p.seed !== undefined) {
      reach = new Uint8Array(n)
      const low = (k: number) => p.mask[k] === 1 && g.elev[k] < p.level
      // A pond held by walls (`citySide`) does not cross a link whose wall top is at or above it.
      const pl = p.barriers !== undefined && p.barriers.length > 0 ? barrierLinks(g, p.barriers) : null
      const open = (k: number, q: number): boolean => {
        if (pl === null) return true
        const top = q === k + 1 ? pl.h[k] : q === k - 1 ? pl.h[q] : q === k + g.nx ? pl.v[k] : pl.v[q]
        return top < p.level
      }
      const queue = new Int32Array(n)
      let head = 0
      let tail = 0
      if (low(p.seed)) { reach[p.seed] = 1; queue[tail++] = p.seed }
      while (head < tail) {
        const k = queue[head++]
        const i = k % g.nx
        for (const q of [i + 1 < g.nx ? k + 1 : -1, i > 0 ? k - 1 : -1, k + g.nx < n ? k + g.nx : -1, k - g.nx]) {
          if (q < 0 || reach[q] === 1 || !low(q) || !open(k, q)) continue
          reach[q] = 1
          queue[tail++] = q
        }
      }
    }
    for (let k = 0; k < n; k++) {
      if (p.mask[k] !== 1 || g.elev[k] >= p.level || (reach !== null && reach[k] !== 1)) continue
      if (flooded[k] !== 0 && level[k] >= p.level) continue
      flooded[k] = 2
      level[k] = p.level
    }
  }
  const depth = new Float32Array(n).fill(NaN)
  for (let k = 0; k < n; k++) if (flooded[k] !== 0) depth[k] = level[k] - g.elev[k]
  return { flooded, level, depth, held, overtopped }
}

/**
 * The flood's signed depth field for tracing the waterline: the depth at flooded nodes, and at
 * dry nodes the (negative) depth the neighboring water's surface would give them, or a little
 * below zero where that would be positive (low ground the water did not reach): the waterline
 * then falls where the ground meets the surface, and short of ground cut off behind a wall.
 */
export const signedDepth = (g: FloodGrid, f: FloodField): Float32Array => {
  const out = new Float32Array(g.nx * g.ny)
  for (let j = 0; j < g.ny; j++) {
    for (let i = 0; i < g.nx; i++) {
      const k = j * g.nx + i
      if (f.flooded[k] !== 0) { out[k] = f.depth[k]; continue }
      let lv = -Infinity
      for (let dj = -1; dj <= 1; dj++) {
        for (let di = -1; di <= 1; di++) {
          const ii = i + di, jj = j + dj
          if (ii < 0 || jj < 0 || ii >= g.nx || jj >= g.ny) continue
          const q = jj * g.nx + ii
          if (f.flooded[q] !== 0) lv = Math.max(lv, f.level[q])
        }
      }
      out[k] = lv === -Infinity ? -1 : Math.min(-0.05, lv - g.elev[k])
    }
  }
  return out
}

/** The flood's surface elevation at a point, from the flooded nodes around it; NaN if none. */
export const levelAt = (g: FloodGrid, level: Float32Array, [e, n]: Vec2): number => {
  const fx = Math.min(g.nx - 1.001, Math.max(0, (e - g.x0) / g.cell))
  const fy = Math.min(g.ny - 1.001, Math.max(0, (n - g.y0) / g.cell))
  const i = Math.floor(fx)
  const j = Math.floor(fy)
  const tx = fx - i
  const ty = fy - j
  let s = 0
  let w = 0
  for (const [di, dj, wt] of [[0, 0, (1 - tx) * (1 - ty)], [1, 0, tx * (1 - ty)], [0, 1, (1 - tx) * ty], [1, 1, tx * ty]] as const) {
    const v = level[(j + dj) * g.nx + i + di]
    if (!Number.isNaN(v)) { s += v * Math.max(wt, 1e-6); w += Math.max(wt, 1e-6) }
  }
  return w > 0 ? s / w : NaN
}

/**
 * The largest 4-connected group of marked nodes: the river itself, where the water comes from.
 * A canal, a pond or a ditch cut off from it (behind a wall) is not a source.
 */
export const largestGroup = (mask: Uint8Array, nx: number, ny: number, links?: { h: Float32Array; v: Float32Array }): Uint8Array => {
  // A barrier link always parts two groups here, whatever its top: a canal behind a wall is
  // fed through gates, not over the wall.
  const open = (k: number, q: number) => links === undefined || (q === k + 1 ? links.h[k] : q === k - 1 ? links.h[q] : q === k + nx ? links.v[k] : links.v[q]) === -Infinity
  const label = new Int32Array(mask.length)
  const queue = new Int32Array(mask.length)
  let best = 0
  let bestSize = 0
  let next = 0
  for (let s = 0; s < mask.length; s++) {
    if (mask[s] !== 1 || label[s] !== 0) continue
    const id = ++next
    let head = 0
    let tail = 0
    label[s] = id
    queue[tail++] = s
    while (head < tail) {
      const k = queue[head++]
      const i = k % nx
      for (const q of [i + 1 < nx ? k + 1 : -1, i > 0 ? k - 1 : -1, k + nx < mask.length ? k + nx : -1, k - nx]) {
        if (q < 0 || mask[q] !== 1 || label[q] !== 0 || !open(k, q)) continue
        label[q] = id
        queue[tail++] = q
      }
    }
    if (tail > bestSize) { bestSize = tail; best = id }
  }
  return Uint8Array.from(label, (v) => (v === best && best !== 0 ? 1 : 0))
}

/** Depth bands drawn, true meters: shallow below the first, deep from the last. */
export const FLOOD_BANDS = [0, 1, 3] as const

/** The median of a list (NaN for none). */
export const median = (xs: readonly number[]): number => {
  if (xs.length === 0) return NaN
  const s = xs.slice().sort((a, b) => a - b)
  const m = s.length >> 1
  return s.length % 2 === 1 ? s[m] : (s[m - 1] + s[m]) / 2
}
