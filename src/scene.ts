/**
 * From features to a drawable scene.
 *
 * Two kinds of thing come out. *Ground* is flat, at height zero, and paints in fixed layers
 * (water, parks, roads, rail) before anything stands on it. *Items* stand up — buildings and
 * bridge spans — and each carries its footprint, its height range and the shapes that draw
 * it, so `order.ts` can paint them back to front.
 */

import {
  centroid, clipRingToRect, clipSegmentToRect, convexHull, hash, insideRect, orient, pointInPolygon,
  pointInRing, signedArea, simplifyRing, type Ring, type Vec2,
} from './geom.ts'
import {
  buildingClass, buildingHeights, groundKind, isBridge, isPath, isRail, roadWidth, waterwayWidth, type GroundKind,
} from './classify.ts'
import type { Feature, LineFeature, PolygonFeature } from './osm.ts'
import { mix, type Palette } from './palette.ts'
import type { Region } from './region.ts'
import { dominantGridAngle, makeView, snapBearing, type View } from './view.ts'
import { localMetres } from './region.ts'
import { makeTerrain, rasterize, settleWater, stillWater, type Terrain } from './terrain.ts'
import { chainCoast, waterFromCoast } from './coast.ts'
import { mergeFootprints, type Footprint } from './footprints.ts'
import { alive, featureAlive, type Dated, type History, type HistoryFeature } from './history.ts'

/** A scene drawn as of a year: which year, the one before it in the series, and the evidence. */
export interface TimeContext {
  readonly year: number
  readonly previous?: number
  readonly title?: string
  readonly history: History
  readonly dates: ReadonlyMap<string, Dated>
}

/** A filled, optionally inked, polygon in screen pixels. */
export interface Shape {
  readonly pts: readonly Vec2[]
  readonly fill: string
  readonly ink?: boolean
  /** Dashed centre line, for track on a bridge. */
  readonly dash?: boolean
  /** Draw as an open polyline instead of a filled polygon. */
  readonly line?: boolean
  /** Stroke in its own fill colour, to close hairline seams between abutting pieces. */
  readonly seal?: boolean
  /** Dots painted with this shape, so whatever paints later can cover them. */
  readonly dots?: readonly Vec2[]
}

export interface Item {
  readonly id: string
  readonly kind: 'building' | 'bridge'
  /** Convex hull of the footprint, view metres. */
  readonly hull: Ring
  readonly zMin: number
  readonly zMax: number
  /** Fallback depth: centroid N'. Larger is farther. */
  readonly key: number
  readonly shapes: Shape[]
  readonly dots: Vec2[]
  readonly name?: string
}

export interface GroundPolygon {
  readonly kind: GroundKind
  /** View-metre rings, already clipped to the frame. Even-odd fill. */
  readonly rings: Ring[]
}

export interface Ribbon {
  readonly kind: 'road' | 'path' | 'rail' | 'canal' | 'weir'
  /** View-metre quads, draped over the terrain when drawn. */
  readonly quads: Vec2[][]
  /** View-metre centre segments, for rail ties and weir crests. */
  readonly centre: Vec2[][]
}

export interface Scene {
  readonly region: Region
  readonly view: View
  readonly palette: Palette
  readonly terrain: Terrain
  readonly ground: GroundPolygon[]
  readonly ribbons: Ribbon[]
  readonly items: Item[]
  readonly stats: Record<string, number>
  /** For a dated scene: the year, its title, and the curated features drawn in it. */
  readonly time?: { readonly year: number; readonly title?: string; readonly curated: readonly HistoryFeature[] }
}

const toViewRing = (view: View, ring: readonly Vec2[]): Ring => ring.map(([lon, lat]) => view.toView(lon, lat))

/** Pick the camera bearing: the region's own, or snapped to the street grid. */
export const chooseBearing = (region: Region, features: readonly Feature[]): number => {
  if (region.snap === false) return region.bearing
  const local = localMetres(region)
  const radius = Math.hypot(region.width, region.depth) / 2
  const rings: Vec2[][] = []
  for (const f of features) {
    if (f.type !== 'polygon' || f.tags.building === undefined) continue
    const ring = f.outers[0].map(([lon, lat]) => local(lon, lat))
    if (ring.every(([e, n]) => Math.hypot(e, n) < radius)) rings.push(ring)
  }
  const angle = dominantGridAngle(rings)
  return angle === null ? region.bearing : snapBearing(region.bearing, angle)
}

export const buildScene = (
  region: Region,
  features: readonly Feature[],
  pal: Palette,
  elevation: ((lon: number, lat: number) => number) | null = null,
  extra: { footprints?: readonly Footprint[]; cover?: (lon: number, lat: number) => number; time?: TimeContext } = {},
): Scene => {
  const time = extra.time
  const curated = time === undefined ? [] : time.history.features.filter((h) => alive(h.from, h.to, time.year))
  if (time !== undefined) features = asOf(features, time)
  const bearing = chooseBearing(region, features)
  const view = makeView(region, bearing)
  const frame = view.frame
  const stats: Record<string, number> = { features: features.length }
  const opts = region.terrain ?? {}
  const useTerrain = elevation !== null && region.terrain !== undefined && opts.enabled !== false
  const terrain = makeTerrain(view, opts.cell ?? 5, useTerrain ? (opts.exaggeration ?? 2) : 1, useTerrain ? elevation : null)

  // ---- ground ----------------------------------------------------------------------------
  const ground: GroundPolygon[] = []
  const margin = 40
  const wide = { minX: frame.minX - margin, maxX: frame.maxX + margin, minY: frame.minY - margin, maxY: frame.maxY + margin }
  for (const f of features) {
    if (f.type !== 'polygon') continue
    const kind = groundKind(f.tags)
    if (kind === null) continue
    // Outers counter-clockwise and holes clockwise, so many features can share one path
    // with a nonzero fill: overlaps union, holes stay holes.
    const rings = [
      ...f.outers.map((r) => orient(clipRingToRect(toViewRing(view, r), wide), true)),
      ...f.inners.map((r) => orient(clipRingToRect(toViewRing(view, r), wide), false)),
    ].filter((r) => r.length >= 3 && Math.abs(signedArea(r)) > 1)
    if (rings.length > 0) ground.push({ kind, rings })
  }
  // The sea and tidal water come as coastline, land on its left: the frame minus the land.
  const coastWays = features.filter((f): f is LineFeature => f.type === 'line' && f.tags.natural === 'coastline').map((f) => f.points)
  if (coastWays.length > 0) {
    const chains = chainCoast(coastWays).map((c) => c.map(([lon, lat]) => view.toView(lon, lat)))
    const sea = waterFromCoast(chains, wide)
    if (sea !== null) ground.unshift({ kind: 'water', rings: sea })
    stats.coastWays = coastWays.length
  }
  const curatedRings = (h: HistoryFeature) => [orient(clipRingToRect(toViewRing(view, h.ring ?? []), wide), true)].filter((r) => r.length >= 3)
  if (curated.some((h) => h.kind === 'water')) {
    const wet = curated.filter((h) => h.kind === 'water' && h.ring !== undefined).map((h) => toViewRing(view, h.ring ?? []))
    for (let k = ground.length - 1; k >= 0; k--) {
      const g = ground[k]
      if (g.kind !== 'water' && wet.some((r) => pointInRing(centroid(g.rings[0]), r))) ground.splice(k, 1)
    }
  }
  for (const h of curated) {
    if ((h.kind === 'water' || h.kind === 'burned' || h.kind === 'plan') && h.ring !== undefined) {
      const rings = curatedRings(h)
      if (rings.length > 0) ground.push({ kind: h.kind, rings })
    }
  }
  stats.ground = ground.length
  rasterize(terrain, ground.filter((g) => g.kind === 'water').map((g) => g.rings), 1)
  rasterize(terrain, ground.filter((g) => g.kind === 'island').map((g) => g.rings), 0)
  settleWater(terrain, 30, 1.0, opts.rocks !== false)
  if (!terrain.flat) stillWater(terrain, curated.filter((h) => h.kind === 'water').map(curatedRings))
  if (extra.cover !== undefined) {
    for (let j = 0; j < terrain.ny; j++) {
      for (let i = 0; i < terrain.nx; i++) {
        const [lon, lat] = view.fromView([terrain.x0 + i * terrain.cell, terrain.y0 + j * terrain.cell])
        terrain.cover[j * terrain.nx + i] = extra.cover(lon, lat)
      }
    }
  }
  if (!terrain.flat) {
    stats.elevationDatum = Number(terrain.datum.toFixed(1))
    let hi = -Infinity
    for (const v of terrain.elev) hi = Math.max(hi, v)
    stats.elevationTop = Number(hi.toFixed(1))
  }

  // ---- ribbons -----------------------------------------------------------------------------
  const ribbons: Ribbon[] = []
  // A town plan, while it is the whole town, keeps only the streets inside it.
  const plans = curated.filter((h) => h.kind === 'plan' && h.limitsStreets && h.ring !== undefined).map((h) => toViewRing(view, h.ring ?? []))
  // Curated water (a filled basin) was not yet built over: nothing of today's runs across it.
  const basins = curated.filter((h) => h.kind === 'water' && h.ring !== undefined).map((h) => toViewRing(view, h.ring ?? []))
  const inTown = (a: Vec2, b: Vec2) => {
    const mid: Vec2 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
    return (plans.length === 0 || plans.some((r) => pointInRing(mid, r))) && !basins.some((r) => pointInRing(mid, r))
  }
  const ribbonOf = (kind: Ribbon['kind'], line: LineFeature, width: number): Ribbon | null => {
    const pts = line.points.map(([lon, lat]) => view.toView(lon, lat))
    const quads: Vec2[][] = []
    const centre: Vec2[][] = []
    for (let i = 0; i + 1 < pts.length; i++) {
      const seg = clipSegmentToRect(pts[i], pts[i + 1], wide)
      if (seg === null) continue
      if ((kind === 'road' || kind === 'path' || kind === 'rail') && !inTown(seg[0], seg[1])) continue
      const q = segmentQuad(seg[0], seg[1], width / 2, width / 2)
      if (q === null) continue
      quads.push(q)
      centre.push([seg[0], seg[1]])
    }
    return quads.length === 0 ? null : { kind, quads, centre }
  }

  const bridgeLines: LineFeature[] = []
  for (const f of features) {
    if (f.type !== 'line') continue
    const t = f.tags
    if (isBridge(t) && (roadWidth(t) !== null || isRail(t))) {
      bridgeLines.push(f)
      continue
    }
    const w = roadWidth(t)
    if (w !== null) {
      const r = ribbonOf(isPath(t) ? 'path' : 'road', f, w)
      if (r) ribbons.push(r)
    } else if (isRail(t)) {
      const r = ribbonOf('rail', f, 3.2)
      if (r) ribbons.push(r)
    } else if (t.waterway === 'weir' || t.waterway === 'dam') {
      const r = ribbonOf('weir', f, t.waterway === 'dam' ? 6 : 3)
      if (r) ribbons.push(r)
    } else {
      const ww = waterwayWidth(t)
      if (ww !== null) {
        const r = ribbonOf('canal', f, ww)
        if (r) ribbons.push(r)
      }
    }
  }
  for (const h of curated) {
    if (h.kind !== 'creek' || h.line === undefined) continue
    const r = ribbonOf('canal', { type: 'line', id: h.id, tags: {}, points: h.line }, h.width ?? 6)
    if (r) ribbons.push(r)
  }
  stats.ribbons = ribbons.length

  // ---- buildings ---------------------------------------------------------------------------
  const items: Item[] = []
  const minArea = region.minBuildingArea ?? 12
  const dotsMode = region.dots ?? 'all'

  // Buildings from OSM, then any footprints from other sources that OSM does not already have.
  const wanted = region.sources?.buildings ?? ['osm']
  const osmBuildings = wanted.includes('osm') ? features.filter((f): f is PolygonFeature => f.type === 'polygon') : []
  const extraBuildings = extra.footprints !== undefined && wanted.includes('microsoft') ? mergeFootprints(osmBuildings, extra.footprints) : []
  stats.footprintsAdded = extraBuildings.length
  interface Solid { id: string; tags: PolygonFeature['tags']; outer: Ring; inners: Ring[] }
  const solids: Solid[] = []
  const parts: Solid[] = []
  for (const f of [...osmBuildings, ...extraBuildings]) {
    const isPart = f.tags['building:part'] !== undefined && f.tags.building === undefined
    if (f.tags.building === undefined && !isPart) continue
    // Canopies (`building=roof`) are open underneath; a solid prism would misdraw them.
    if (f.tags.building === 'no' || f.tags.building === 'roof') continue
    const inners = f.inners.map((r) => toViewRing(view, r))
    f.outers.forEach((o, i) => {
      const outer = toViewRing(view, o)
      const mine = inners.filter((h) => h.length > 0 && pointInRing(h[0], outer))
      ;(isPart ? parts : solids).push({ id: f.outers.length > 1 ? `${f.id}.${i}` : f.id, tags: f.tags, outer, inners: mine })
    })
  }
  // A lattice tower (the Eiffel Tower, Tokyo Tower) is drawn whole as a tapering spire from
  // its outline, so the platforms mapped inside it as parts are dropped.
  const lattice = solids.filter((s) => isLatticeTower(s.tags))
  // (The test is against the tower's hull: its outline is cut away by the arches between the
  // legs, and a leg's centroid can fall in an arch.)
  const latticeHulls = lattice.map((t) => convexHull(t.outer))
  const keptParts = parts.filter((p) => !latticeHulls.some((h) => pointInRing(centroid(p.outer), h)))
  // Simple 3D Buildings: where parts describe a building, draw the parts, not the outline.
  const partCentres = keptParts.map((p) => centroid(p.outer))
  const shown = solids.filter((s) => lattice.includes(s) || !partCentres.some((c) => pointInRing(c, s.outer))).concat(keptParts)

  let heightSources = { height: 0, model: 0, levels: 0, guess: 0 }
  let fresh = 0
  let undated = 0
  const datedBy = { curated: 0, osm: 0, parcel: 0 }
  for (const s of shown) {
    if (!s.outer.every((p) => insideRect(p, frame))) continue
    const area = Math.abs(signedArea(s.outer)) - s.inners.reduce((a, h) => a + Math.abs(signedArea(h)), 0)
    if (area < minArea) continue
    const outer = orient(simplifyRing(s.outer, 0.45), true)
    if (outer.length < 3) continue
    const inners = s.inners.map((h) => orient(simplifyRing(h, 0.45), false)).filter((h) => h.length >= 3)
    const h = buildingHeights(s.tags, area)
    if (!Number.isFinite(h.base) || !Number.isFinite(h.top)) continue
    heightSources[h.source]++
    // Seat the building on the ground under it: walls reach down to the lowest corner, so a
    // building on a slope shows its full height on the downhill side.
    const grounds = outer.map((p) => terrain.z(p))
    const gMin = Math.min(...grounds)
    const gMax = Math.max(...grounds)
    const gMean = grounds.reduce((a, b) => a + b, 0) / grounds.length
    const base = gMin + h.base
    const top = Math.max(gMean + h.top, gMax + 2.5, base + 2.5)
    const cls = buildingClass(s.tags)
    const roofs = pal.roofs[cls]
    let roof = roofs[hash(s.id) % roofs.length]
    const dated = time?.dates.get(s.id.split('.')[0])
    if (time !== undefined) {
      if (dated === undefined) undated++
      else datedBy[dated.source]++
    }
    if (time?.previous !== undefined && dated !== undefined && dated.year > time.previous) {
      roof = pal.fresh
      fresh++
    }
    if (lattice.includes(s)) items.push(spire(view, pal, s.id, outer, base, gMean + h.top, dotsMode, s.tags.name))
    else if (isShellRoof(s.tags)) items.push(spire(view, pal, s.id, outer, base, gMean + SHELL_RISE * Math.sqrt(area), dotsMode, s.tags.name, (t) => 1 - t * 0.97, false))
    else items.push(extrude(view, pal, s.id, outer, inners, base, top, roof, dotsMode, s.tags.name))
  }
  stats.buildings = items.length
  stats.heightFromTag = heightSources.height
  stats.heightFromModel = heightSources.model
  stats.heightFromLevels = heightSources.levels
  stats.heightGuessed = heightSources.guess
  if (time !== undefined) {
    stats.year = time.year
    stats.newSincePrevious = fresh
    stats.datedCurated = datedBy.curated
    stats.datedOsm = datedBy.osm
    stats.datedParcel = datedBy.parcel
    stats.undatedToday = undated
    // Curated landmarks: lost buildings, from published dimensions, in their own tone.
    let landmarks = 0
    for (const h of curated) {
      if (h.kind !== 'landmark' || h.ring === undefined) continue
      const outer = orient(toViewRing(view, h.ring), true)
      if (!outer.every((p) => insideRect(p, frame))) continue
      const ruined = h.ruin !== undefined && time.year >= h.ruin
      const grounds = outer.map((p) => terrain.z(p))
      const base = Math.min(...grounds)
      const top = Math.max(...grounds) + (h.height ?? 10) * (ruined ? 0.45 : 1)
      items.push(extrude(view, pal, `history:${h.id}`, outer, [], base, top, ruined ? pal.ash : pal.lost, dotsMode, h.name))
      landmarks++
    }
    stats.landmarks = landmarks
    // Buildings traced from fire-insurance maps that are gone today, in the maps' colours.
    const ends = { map: 0, rebuilt: 0, highway: 0, assumed: 0 }
    for (const b of time.history.traced) {
      if (!alive(b.from, b.to, time.year)) continue
      const outer = orient(simplifyRing(toViewRing(view, b.ring), 0.3), true)
      if (outer.length < 3 || !outer.every((p) => insideRect(p, frame))) continue
      const grounds = outer.map((p) => terrain.z(p))
      const base = Math.min(...grounds)
      const top = Math.max(...grounds) + b.storeys * 3.6
      items.push(extrude(view, pal, `traced:${b.id}`, outer, [], base, top, pal.traced[b.material], dotsMode))
      ends[b.end]++
    }
    stats.traced = ends.map + ends.rebuilt + ends.highway + ends.assumed
    stats.tracedEndMap = ends.map
    stats.tracedEndRebuilt = ends.rebuilt
    stats.tracedEndHighway = ends.highway
    stats.tracedEndAssumed = ends.assumed
    stats.curated = curated.length
  }

  // ---- bridges -----------------------------------------------------------------------------
  let spans = 0
  for (const chain of chainBridges(plans.length > 0 ? [] : bridgeLines)) {
    const pieces = bridgePieces(view, pal, region, terrain, chain)
    spans += pieces.length
    items.push(...pieces)
  }
  stats.bridgePieces = spans

  return {
    region, view, palette: pal, terrain, ground, ribbons, items, stats,
    ...(time === undefined ? {} : { time: { year: time.year, ...(time.title === undefined ? {} : { title: time.title }), curated } }),
  }
}

/**
 * The features that stood in a year. Buildings by their dates (undated ones only in the
 * present); everything else by the history's era rules.
 */
export const asOf = (features: readonly Feature[], time: TimeContext): Feature[] =>
  features.filter((f) => {
    const isBuilding = f.type === 'polygon' && (f.tags.building !== undefined || f.tags['building:part'] !== undefined)
    if (!isBuilding) return featureAlive(f, time.year, time.history)
    const d = time.dates.get(f.id)
    return d === undefined ? time.year >= time.history.present : d.year <= time.year
  })

/** The rectangle either side of a segment, as a ring: left offset `l`, right offset `r`. */
const segmentQuad = (a: Vec2, b: Vec2, l: number, r: number, extend = 0): Vec2[] | null => {
  const dx = b[0] - a[0]
  const dy = b[1] - a[1]
  const len = Math.hypot(dx, dy)
  if (len < 1e-6) return null
  const ux = dx / len
  const uy = dy / len
  const a2: Vec2 = [a[0] - ux * extend, a[1] - uy * extend]
  const b2: Vec2 = [b[0] + ux * extend, b[1] + uy * extend]
  // Left normal of the direction of travel.
  const nx = -uy
  const ny = ux
  return [
    [a2[0] + nx * l, a2[1] + ny * l],
    [b2[0] + nx * l, b2[1] + ny * l],
    [b2[0] - nx * r, b2[1] - ny * r],
    [a2[0] - nx * r, a2[1] - ny * r],
  ]
}

/**
 * A prism: walls on every edge turned towards the camera, painted far to near, then the roof.
 * Rings are view metres; the outer runs counter-clockwise and holes clockwise, so the outward
 * normal of edge a→b is (dy, −dx) on both, pointing away from the solid.
 */
export const extrude = (
  view: View, pal: Palette, id: string, outer: Ring, inners: Ring[], base: number, top: number,
  roof: string, dots: 'all' | 'roof' | 'none', name?: string,
): Item => {
  const walls: { key: number; shape: Shape }[] = []
  for (const ring of [outer, ...inners]) {
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i]
      const b = ring[(i + 1) % ring.length]
      const dx = b[0] - a[0]
      const dy = b[1] - a[1]
      const len = Math.hypot(dx, dy)
      if (len < 1e-6) continue
      const nE = dy / len
      const nN = -dx / len
      // The camera looks along +N', so a wall faces it when its normal points to −N'.
      if (nN >= -1e-6) continue
      // Light from the left: faces turned left are lit, faces turned right are in shade.
      const tone = mix(pal.wallLit, pal.wallShade, (nE + 1) / 2)
      walls.push({
        key: (a[1] + b[1]) / 2,
        shape: {
          pts: [view.toScreen(a, base), view.toScreen(b, base), view.toScreen(b, top), view.toScreen(a, top)],
          fill: tone,
          ink: true,
          // A wall carries the dots at its own foot, so a nearer wall hides them with it.
          ...(dots === 'all' ? { dots: [view.toScreen(a, base), view.toScreen(b, base)] } : {}),
        },
      })
    }
  }
  walls.sort((x, y) => y.key - x.key)
  const shapes: Shape[] = walls.map((w) => w.shape)
  for (const ring of [outer, ...inners]) {
    shapes.push({ pts: ring.map((p) => view.toScreen(p, top)), fill: roof, ink: true })
  }
  const roofDots = dots === 'none' ? [] : [...outer, ...inners.flat()].map((p) => view.toScreen(p, top))
  return {
    id,
    kind: 'building',
    hull: convexHull(outer),
    zMin: base,
    zMax: top,
    key: centroid(outer)[1],
    shapes,
    dots: dedupe(roofDots),
    ...(name === undefined ? {} : { name }),
  }
}

/** OSM's lattice towers: tagged as such, or a building whose pyramidal roof is its whole height. */
export const isLatticeTower = (t: Readonly<Record<string, string>>): boolean =>
  t.building !== undefined && (t['tower:construction'] === 'lattice' || (t['roof:shape'] === 'pyramidal' && t['roof:height'] !== undefined && t['roof:height'] === t.height))

/**
 * A curved roof shell mapped with no height (the Sydney Opera House's sails): a roof part whose
 * shape is round, spherical or circular. It is drawn as a sail rising to a point, its height
 * `SHELL_RISE` × √area, an approximation that grows with the shell like the real ones do.
 */
export const isShellRoof = (t: Readonly<Record<string, string>>): boolean =>
  t['building:part'] === 'roof' && ['round', 'spherical', 'circular'].includes(t['roof:shape'] ?? '') && t.height === undefined && t['min_height'] === undefined
export const SHELL_RISE = 1.4

/**
 * Half-width of a lattice tower at fraction `t` of its height, as a fraction of the base: the
 * Eiffel Tower's curve, which narrows roughly exponentially (0.56 at the first platform, 0.32
 * at the second), then runs out to a mast over the top sixth.
 */
export const spireProfile = (t: number): number => (t <= 0.84 ? Math.exp(-3.3 * t) : Math.exp(-3.3 * 0.84) * (1 - (t - 0.84) / 0.16) * 0.9 + 0.01)

/**
 * A tapering tower: stacked frustums following `spireProfile`, each one's walls then its cap,
 * bottom to top (an upper piece always sits inside and above the one below it). The walls are
 * darkened towards the ink, for iron.
 */
export const spire = (
  view: View, pal: Palette, id: string, outer: Ring, base: number, top: number, dots: 'all' | 'roof' | 'none', name?: string,
  profile: (t: number) => number = spireProfile, iron = true,
): Item => {
  const c = centroid(outer)
  const at = (p: Vec2, k: number): Vec2 => [c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k]
  const STEPS = 16
  const shapes: Shape[] = []
  for (let i = 0; i < STEPS; i++) {
    const t0 = i / STEPS
    const t1 = (i + 1) / STEPS
    const k0 = profile(t0)
    const k1 = profile(t1)
    const z0 = base + (top - base) * t0
    const z1 = base + (top - base) * t1
    const walls: { key: number; shape: Shape }[] = []
    for (let j = 0; j < outer.length; j++) {
      const a = outer[j]
      const b = outer[(j + 1) % outer.length]
      const dx = b[0] - a[0]
      const dy = b[1] - a[1]
      const len = Math.hypot(dx, dy)
      if (len < 1e-6 || -dx / len >= -1e-6) continue
      const tone = mix(mix(pal.wallLit, pal.wallShade, (dy / len + 1) / 2), pal.ink, iron ? 0.35 : 0)
      walls.push({
        key: (a[1] + b[1]) / 2,
        shape: { pts: [view.toScreen(at(a, k0), z0), view.toScreen(at(b, k0), z0), view.toScreen(at(b, k1), z1), view.toScreen(at(a, k1), z1)], fill: tone, ink: true },
      })
    }
    walls.sort((x, y) => y.key - x.key)
    shapes.push(...walls.map((w) => w.shape))
  }
  shapes.push({ pts: outer.map((p) => view.toScreen(at(p, profile(1)), top)), fill: mix(pal.wallShade, pal.ink, iron ? 0.35 : 0), ink: true })
  return {
    id,
    kind: 'building',
    hull: convexHull(outer),
    zMin: base,
    zMax: top,
    key: c[1],
    shapes,
    dots: dots === 'all' ? dedupe(outer.map((p) => view.toScreen(p, base))) : [],
    ...(name === undefined ? {} : { name }),
  }
}

const dedupe = (pts: Vec2[]): Vec2[] => {
  const seen = new Set<string>()
  return pts.filter((p) => {
    const k = `${p[0].toFixed(1)},${p[1].toFixed(1)}`
    if (seen.has(k)) return false
    seen.add(k)
    return true
  })
}

const FASCIA = 1.6
const PIER_SPACING = 38
const PIECE = 22

/** A run of bridge ways joined end to end, with which ends come down to the ground. */
export interface BridgeChain {
  readonly line: LineFeature
  /** Every name carried by any way in the chain, for deck rules. */
  readonly names: string
  readonly rampStart: boolean
  readonly rampEnd: boolean
}

const key = (p: Vec2) => `${p[0].toFixed(7)},${p[1].toFixed(7)}`

/**
 * OSM cuts one bridge into many ways (at every lane change, name change, or junction). Ramp
 * each of those down to the ground and a viaduct becomes a roller coaster, so join ways that
 * share an end and the same layer and kind, and only ramp an end that no other bridge way
 * touches — an end that really does meet the ground.
 */
export const chainBridges = (lines: readonly LineFeature[]): BridgeChain[] => {
  const group = (l: LineFeature) => `${l.tags.layer ?? '1'}|${isRail(l.tags) ? 'rail' : 'road'}`
  const touches = new Map<string, Set<string>>()
  for (const l of lines) {
    for (const p of l.points) {
      const k = key(p)
      const s = touches.get(k) ?? new Set<string>()
      s.add(l.id)
      touches.set(k, s)
    }
  }
  const chains: BridgeChain[] = []
  const byGroup = new Map<string, LineFeature[]>()
  for (const l of lines) byGroup.set(group(l), [...(byGroup.get(group(l)) ?? []), l])
  for (const pool of byGroup.values()) {
    const left = pool.slice()
    while (left.length > 0) {
      const first = left.pop()!
      let pts = first.points.slice()
      const members = [first]
      let grew = true
      while (grew) {
        grew = false
        for (let i = 0; i < left.length; i++) {
          const c = left[i]
          const s = c.points
          const head = key(pts[0])
          const tail = key(pts[pts.length - 1])
          if (key(s[0]) === tail) pts = pts.concat(s.slice(1))
          else if (key(s[s.length - 1]) === tail) pts = pts.concat(s.slice(0, -1).reverse())
          else if (key(s[s.length - 1]) === head) pts = s.slice(0, -1).concat(pts)
          else if (key(s[0]) === head) pts = s.slice(1).reverse().concat(pts)
          else continue
          members.push(c)
          left.splice(i, 1)
          grew = true
          break
        }
      }
      const ids = new Set(members.map((m) => m.id))
      const groundedAt = (p: Vec2) => [...(touches.get(key(p)) ?? [])].every((id) => ids.has(id))
      chains.push({
        line: { ...first, points: pts },
        names: members.map((m) => `${m.tags.name ?? ''} ${m.tags['bridge:name'] ?? ''}`).join(' ').toLowerCase(),
        rampStart: groundedAt(pts[0]),
        rampEnd: groundedAt(pts[pts.length - 1]),
      })
    }
  }
  return chains
}

/** Deck height for a bridge: a named rule, else the default per OSM layer. */
const deckHeight = (region: Region, chain: BridgeChain): number => {
  for (const rule of region.bridges ?? []) if (chain.names.includes(rule.match.toLowerCase())) return rule.deck
  const layer = Math.max(1, parseInt(chain.line.tags.layer ?? '1', 10) || 1)
  return (region.bridgeDeck ?? 7) * layer
}

/**
 * A bridge, cut into short spans so each can take its own place in the paint order. The deck
 * ramps up from the ground at both ends; piers drop from it at a fixed spacing.
 */
const pierSpacing = (region: Region, chain: BridgeChain): number => {
  for (const rule of region.bridges ?? []) if (chain.names.includes(rule.match.toLowerCase())) return rule.pierSpacing ?? PIER_SPACING
  return PIER_SPACING
}

const bridgePieces = (view: View, pal: Palette, region: Region, terrain: Terrain, chain: BridgeChain): Item[] => {
  const spacing = pierSpacing(region, chain)
  const line = chain.line
  const t = line.tags
  const rail = isRail(t)
  const width = rail ? 4.5 : (roadWidth(t) ?? 6) + 1.5
  const deck = deckHeight(region, chain)
  const pts = line.points.map(([lon, lat]) => view.toView(lon, lat))
  const cum = [0]
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
  const total = cum[cum.length - 1]
  const pointAt = (s: number): Vec2 => {
    let i = 1
    while (i < cum.length - 1 && cum[i] < s) i++
    const u = (s - cum[i - 1]) / Math.max(1e-9, cum[i] - cum[i - 1])
    return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * u, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * u]
  }
  const ground = (s: number) => terrain.z(pointAt(s))

  // The deck profile. A bridge runs fairly straight between its abutments, and never closer to
  // what is under it than its clearance — except where it comes down to meet the ground.
  const ramp = Math.min(70, total / 3)
  const clearance = (s: number) => {
    const e = Math.min(chain.rampStart ? s : Infinity, chain.rampEnd ? total - s : Infinity)
    if (ramp <= 0 || e >= ramp) return deck
    const u = Math.max(0, e / ramp)
    return deck * (u * u * (3 - 2 * u))
  }
  const startLevel = ground(0) + (chain.rampStart ? 0 : deck)
  const endLevel = ground(total) + (chain.rampEnd ? 0 : deck)
  const step = 5
  const samples = Math.max(2, Math.ceil(total / step) + 1)
  const raw: number[] = []
  for (let k = 0; k < samples; k++) {
    const s = (total * k) / (samples - 1)
    const chord = startLevel + (endLevel - startLevel) * (s / Math.max(1e-9, total))
    raw.push(Math.max(chord, ground(s) + clearance(s)))
  }
  // Decks run straight: pull a taut line over the obstacles (the upper hull of the profile),
  // so a bridge rises in straight runs to clear what is under it and never dips between.
  const hull: number[] = []
  for (let k = 0; k < samples; k++) {
    while (hull.length >= 2) {
      const a = hull[hull.length - 2]
      const b = hull[hull.length - 1]
      const cross = (b - a) * (raw[k] - raw[a]) - (raw[b] - raw[a]) * (k - a)
      if (cross >= 0) hull.pop()
      else break
    }
    hull.push(k)
  }
  const smooth = raw.slice()
  for (let h = 0; h + 1 < hull.length; h++) {
    const a = hull[h]
    const b = hull[h + 1]
    for (let k = a; k <= b; k++) smooth[k] = raw[a] + ((raw[b] - raw[a]) * (k - a)) / Math.max(1, b - a)
  }
  const zAt = (s: number) => {
    const f = (s / Math.max(1e-9, total)) * (samples - 1)
    const k = Math.min(samples - 2, Math.max(0, Math.floor(f)))
    const u = f - k
    return smooth[k] * (1 - u) + smooth[k + 1] * u
  }
  const items: Item[] = []
  let travelled = 0
  let nextPier = spacing / 2
  for (let i = 0; i + 1 < pts.length; i++) {
    const a = pts[i]
    const b = pts[i + 1]
    const len = Math.hypot(b[0] - a[0], b[1] - a[1])
    const n = Math.max(1, Math.ceil(len / PIECE))
    for (let k = 0; k < n; k++) {
      const s0 = travelled + (len * k) / n
      const s1 = travelled + (len * (k + 1)) / n
      const p0: Vec2 = [a[0] + ((b[0] - a[0]) * k) / n, a[1] + ((b[1] - a[1]) * k) / n]
      const p1: Vec2 = [a[0] + ((b[0] - a[0]) * (k + 1)) / n, a[1] + ((b[1] - a[1]) * (k + 1)) / n]
      if (!insideRect(p0, view.frame) || !insideRect(p1, view.frame)) {
        while (nextPier <= s1) nextPier += spacing
        continue
      }
      const quad = segmentQuad(p0, p1, width / 2, width / 2)
      if (quad === null) continue
      const z0 = zAt(s0)
      const z1 = zAt(s1)
      const shapes: Shape[] = []
      // Piers first: they stand behind the fascia.
      while (nextPier <= s1) {
        const u = (nextPier - s0) / Math.max(1e-6, s1 - s0)
        const pz = z0 + (z1 - z0) * u
        const c0: Vec2 = [p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u]
        const footZ = terrain.z(c0)
        if (pz - footZ > 3) {
          const c: Vec2 = [p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u]
          const dx = (p1[0] - p0[0]) / Math.max(1e-6, s1 - s0)
          const dy = (p1[1] - p0[1]) / Math.max(1e-6, s1 - s0)
          const half = width / 2 - 0.6
          const l: Vec2 = [c[0] - dy * half, c[1] + dx * half]
          const r: Vec2 = [c[0] + dy * half, c[1] - dx * half]
          shapes.push({ pts: [view.toScreen(l, footZ), view.toScreen(r, footZ), view.toScreen(r, pz - FASCIA), view.toScreen(l, pz - FASCIA)], fill: pal.pier, ink: true })
        }
        nextPier += spacing
      }
      // Fascia on whichever long side faces the camera.
      const [ql0, ql1, qr1, qr0] = quad
      const sides: [Vec2, Vec2][] = [[ql1, ql0], [qr0, qr1]]
      for (const [u0, u1] of sides) {
        const dx = u1[0] - u0[0]
        const dy = u1[1] - u0[1]
        const nN = -dx / Math.max(1e-6, Math.hypot(dx, dy))
        if (nN >= 0) continue
        const zu0 = u0 === ql0 || u0 === qr0 ? z0 : z1
        const zu1 = u1 === ql0 || u1 === qr0 ? z0 : z1
        const lo0 = view.toScreen(u0, zu0 - FASCIA)
        const lo1 = view.toScreen(u1, zu1 - FASCIA)
        const hi0 = view.toScreen(u0, zu0)
        const hi1 = view.toScreen(u1, zu1)
        // Filled and sealed, but inked only along its length: a span is one bridge, not a
        // stack of 22-metre slabs.
        shapes.push({ pts: [lo0, lo1, hi1, hi0], fill: pal.fascia, seal: true })
        shapes.push({ pts: [lo0, lo1], fill: 'none', line: true })
      }
      const d0 = view.toScreen(ql0, z0)
      const d1 = view.toScreen(ql1, z1)
      const d2 = view.toScreen(qr1, z1)
      const d3 = view.toScreen(qr0, z0)
      shapes.push({ pts: [d0, d1, d2, d3], fill: rail ? pal.rail : pal.deck, seal: true })
      shapes.push({ pts: [d0, d1], fill: 'none', line: true })
      shapes.push({ pts: [d3, d2], fill: 'none', line: true })
      if (rail) shapes.push({ pts: [view.toScreen(p0, z0), view.toScreen(p1, z1)], fill: 'none', line: true, dash: true })
      items.push({
        id: `${line.id}.${i}.${k}`,
        kind: 'bridge',
        hull: convexHull(quad),
        zMin: Math.min(terrain.z(p0), terrain.z(p1)),
        zMax: Math.max(z0, z1),
        key: (p0[1] + p1[1]) / 2,
        shapes,
        dots: [],
        ...(t.name === undefined ? {} : { name: t.name }),
      })
    }
    travelled += len
  }
  return items
}

/** Is this view-metre point on open water (inside water, outside every island)? */
export const onWater = (scene: Scene, p: Vec2): boolean => {
  let wet = false
  for (const g of scene.ground) {
    if (g.kind === 'water' && pointInPolygon(p, g.rings)) wet = true
  }
  if (!wet) return false
  for (const g of scene.ground) if (g.kind === 'island' && pointInPolygon(p, g.rings)) return false
  return true
}
