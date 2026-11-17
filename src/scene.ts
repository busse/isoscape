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
  buildingClass, buildingHeights, groundKind, isBridge, isPath, isRail, roadWidth, waterFlows, waterwayWidth, type GroundKind,
} from './classify.ts'
import type { Feature, LineFeature, PolygonFeature } from './osm.ts'
import { mix, type Palette } from './palette.ts'
import type { Region } from './region.ts'
import { dominantGridAngle, makeView, snapBearing, type View } from './view.ts'
import { localMetres } from './region.ts'
import { makeTerrain, rasterize, settleWater, stillWater, traceShore, type Terrain } from './terrain.ts'
import { chainCoast, waterFromCoast } from './coast.ts'
import { mergeFootprints, type Footprint } from './footprints.ts'
import { boxItem, canopyBoxes, dome, partLevels, toned, trainBoxes, type Box } from './parts.ts'
import { cutawayItems, partSolids, partTones, travelerItem, type PlacedPart } from './cutaway-scene.ts'
import { offsetConvex, solidItem, type CutPlane } from './cutaway.ts'
import { alive, dropUnbuiltStreets, featureAlive, laterWorks, type Dated, type History, type HistoryFeature } from './history.ts'

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
  /** Dashed center line, for track on a bridge. */
  readonly dash?: boolean
  /** Draw as an open polyline instead of a filled polygon. */
  readonly line?: boolean
  /** Stroke in its own fill color, to close hairline seams between abutting pieces. */
  readonly seal?: boolean
  /** Dots painted with this shape, so whatever paints later can cover them. */
  readonly dots?: readonly Vec2[]
  /** An open line's own stroke: color, width and dash, in pixels (a cutaway's dashed outline). */
  readonly stroke?: { readonly color: string; readonly width: number; readonly dash: readonly [number, number] }
}

export interface Item {
  readonly id: string
  readonly kind: 'building' | 'bridge'
  /** Convex hull of the footprint, view meters. */
  readonly hull: Ring
  readonly zMin: number
  readonly zMax: number
  /** Fallback depth: centroid N'. Larger is farther. */
  readonly key: number
  readonly shapes: Shape[]
  readonly dots: Vec2[]
  readonly name?: string
  /** A building's outline, view meters, where it is a plain prism. */
  readonly footprint?: Ring
  /** A bridge span's center line, view meters, its deck's mean height, and which bridge it is. */
  readonly span?: { readonly a: Vec2; readonly b: Vec2; readonly z: number; readonly bridge: string }
  /** A bridge pier, standing under a deck. */
  readonly pier?: boolean
}

export interface GroundPolygon {
  readonly kind: GroundKind
  /** View-meter rings, already clipped to the frame. Even-odd fill. */
  readonly rings: Ring[]
}

export interface Ribbon {
  readonly kind: 'road' | 'path' | 'rail' | 'canal' | 'weir' | 'tram' | 'racetrack'
  /** View-meter quads, draped over the terrain when drawn. */
  readonly quads: Vec2[][]
  /** View-meter center segments, for rail ties and weir crests. */
  readonly center: Vec2[][]
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
  /** Track drawn wider than life (a history's `railScale` over 1) is inked dark, to read from afar. */
  readonly boldRail?: boolean
  /** Words on the map: curated labels, at view meters and the ground height there. */
  readonly labels?: readonly MapLabel[]
  /** A cutaway's plane, in view meters. */
  readonly cut?: CutPlane
  /** A flat section's cut faces, in plane coordinates: meters along the plane, scene z. */
  readonly sections?: readonly Vec2[][]
}

export interface MapLabel {
  readonly text: string
  readonly caption?: string
  readonly at: Vec2
  readonly z: number
  readonly anchor: 'start' | 'middle' | 'end'
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
  extra: { footprints?: readonly Footprint[]; cover?: (lon: number, lat: number) => number; time?: TimeContext; section?: boolean } = {},
): Scene => {
  const time = extra.time
  const curated = time === undefined ? [] : time.history.features.filter((h) => alive(h.from, h.to, time.year))
  let later = { atGrade: 0, verges: 0 }
  if (time !== undefined) {
    const all = features
    const r = laterWorks(all, asOf(all, time), time.year, time.history)
    features = r.kept
    later = { atGrade: r.atGrade, verges: r.verges }
  }
  let unbuiltStreets = 0
  // Today's scene draws today's streets, built on or not.
  if (time !== undefined && time.history.streetsNearBuildings !== undefined && time.year < time.history.present) {
    // Traced and curated buildings of the year count as houses too; a town plan vouches for
    // its own streets.
    const traced = time.history.traced.filter((b) => alive(b.from, b.to, time.year)).map((b) => b.ring[0])
    const landmarks = curated.filter((h) => h.kind === 'landmark' && h.ring !== undefined).flatMap((h) => h.ring ?? [])
    // A plan's streets stay laid out after the plan stops limiting the town.
    const plans = time.history.features.filter((h) => h.kind === 'plan' && h.ring !== undefined && h.from <= time.year).map((h) => h.ring ?? [])
    const r = dropUnbuiltStreets(features, time.history.streetsNearBuildings, [...traced, ...landmarks], plans, time.history.majorStreetsNearBuildings === true)
    features = r.kept
    unbuiltStreets = r.dropped
  }
  const bearing = chooseBearing(region, features)
  const view = makeView(region, bearing)
  const frame = view.frame
  const stats: Record<string, number> = { features: features.length, ...(unbuiltStreets ? { unbuiltStreets } : {}), ...(later.atGrade ? { bridgesAtGrade: later.atGrade } : {}), ...(later.verges ? { vergesLater: later.verges } : {}) }
  const opts = region.terrain ?? {}
  const useTerrain = elevation !== null && region.terrain !== undefined && opts.enabled !== false
  const terrain = makeTerrain(view, opts.cell ?? 5, useTerrain ? (opts.exaggeration ?? 2) : 1, useTerrain ? elevation : null)

  // ---- ground ----------------------------------------------------------------------------
  const ground: GroundPolygon[] = []
  // Water by whether it flows: rivers get rocks and rapids, still water (and the sea) none.
  const riverWater: Ring[][] = []
  const stillWaters: Ring[][] = []
  const plainWater: Ring[][] = []
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
    if (rings.length === 0) continue
    ground.push({ kind, rings })
    if (kind === 'water') {
      const flows = waterFlows(f.tags)
      if (flows === true) riverWater.push(rings)
      else if (flows === false) stillWaters.push(rings)
      else plainWater.push(rings)
    }
  }
  // Plain water is a river where a river runs through it.
  const riverLines = features
    .filter((f): f is LineFeature => f.type === 'line' && (f.tags.waterway === 'river' || f.tags.waterway === 'stream'))
    .map((f) => f.points.map(([lon, lat]) => view.toView(lon, lat)))
  const crossedByRiver = (rings: Ring[]) => riverLines.some((pts) => pts.some((p, k) =>
    pointInPolygon(p, rings) || (k > 0 && pointInPolygon([(p[0] + pts[k - 1][0]) / 2, (p[1] + pts[k - 1][1]) / 2], rings))))
  for (const rings of plainWater) (crossedByRiver(rings) ? riverWater : stillWaters).push(rings)
  // The sea and tidal water come as coastline, land on its left: the frame minus the land.
  const coastWays = features.filter((f): f is LineFeature => f.type === 'line' && f.tags.natural === 'coastline').map((f) => f.points)
  if (coastWays.length > 0) {
    const chains = chainCoast(coastWays).map((c) => c.map(([lon, lat]) => view.toView(lon, lat)))
    const sea = waterFromCoast(chains, wide)
    if (sea !== null) {
      ground.unshift({ kind: 'water', rings: sea })
      stillWaters.push(sea)
    }
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
    if ((h.kind === 'water' || h.kind === 'burned' || h.kind === 'plan' || h.kind === 'grounds' || h.kind === 'platform' || h.kind === 'wood') && h.ring !== undefined) {
      // Pleasure grounds that are gone (a fairground, an amusement park) take a tint of their own.
      const rings = curatedRings(h)
      if (rings.length > 0) ground.push({ kind: h.kind, rings })
    }
  }
  // Skyways: footbridges that run from building to building at a floor the data does not give.
  // Drawn at a ramp's height they lie across walls and roofs, so they are left out. They are
  // decided once, here, from the buildings' outlines, so a way that is not drawn never carves
  // the ground under it either.
  const outlines = buildingOutlines([
    ...features.flatMap((f) => (f.type === 'polygon' && (f.tags.building !== undefined || f.tags['building:part'] !== undefined) ? f.outers : [])),
    ...(time === undefined ? [] : time.history.traced.filter((b) => alive(b.from, b.to, time.year)).map((b) => b.ring)),
    ...curated.filter((h) => h.kind === 'landmark' && h.ring !== undefined).map((h) => h.ring ?? []),
  ].map((r) => toViewRing(view, r)))
  const skyways = new Set(features.filter((f): f is LineFeature => f.type === 'line' && isBridge(f.tags) && roadWidth(f.tags) !== null && isSkyway(f.tags, f.points.map(([lon, lat]) => view.toView(lon, lat)), outlines)))
  if (skyways.size > 0) stats.skywaysLeftOut = skyways.size
  // A bare-earth model often keeps a short overpass as a ridge of ground across the cut or
  // street under it (the lidar saw the deck); carve it out before anything reads the ground.
  if (!terrain.flat && !curated.some((h) => h.kind === 'plan' && h.limitsStreets)) {
    const lines = features.filter((f): f is LineFeature => f.type === 'line' && isBridge(f.tags) && (roadWidth(f.tags) !== null || isRail(f.tags)) && !skyways.has(f))
    const abutments = chainBridges(lines).flatMap((c) => [
      ...(c.rampStart ? [c.line.points[0]] : []),
      ...(c.rampEnd ? [c.line.points[c.line.points.length - 1]] : []),
    ]).map(([lon, lat]) => view.toView(lon, lat))
    const lowered = carveUnderBridges(terrain, lines.map((f) => ({ pts: f.points.map(([lon, lat]) => view.toView(lon, lat)), width: deckWidth(f.tags) })), abutments)
    if (lowered > 0) stats.groundUnderBridgesLowered = lowered
  }
  stats.ground = ground.length
  // Every water outline is water; still water marked after the rivers wins where they overlap.
  rasterize(terrain, ground.filter((g) => g.kind === 'water').map((g) => g.rings), 1, false)
  rasterize(terrain, riverWater, 1, true)
  rasterize(terrain, stillWaters, 1, false)
  rasterize(terrain, ground.filter((g) => g.kind === 'island').map((g) => g.rings), 0)
  settleWater(terrain, 30, 1.0, opts.rocks !== false)
  if (!terrain.flat) stillWater(terrain, curated.filter((h) => h.kind === 'water').map(curatedRings))
  traceShore(terrain, ground.filter((g) => g.kind === 'water').map((g) => g.rings), ground.filter((g) => g.kind === 'island').map((g) => g.rings))
  if (extra.cover !== undefined) {
    for (let j = 0; j < terrain.ny; j++) {
      for (let i = 0; i < terrain.nx; i++) {
        const [lon, lat] = view.fromView([terrain.x0 + i * terrain.cell, terrain.y0 + j * terrain.cell])
        terrain.cover[j * terrain.nx + i] = extra.cover(lon, lat)
      }
    }
    // Land nodes that took a cover class: what the credit line goes by.
    let covered = 0
    for (let k = 0; k < terrain.cover.length; k++) if (terrain.cover[k] !== 0 && terrain.water[k] === 0) covered++
    stats.coverNodes = covered
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
  // Curated water (a filled basin) was not yet built over, and a site (a station's grounds) was
  // laid out otherwise: nothing of today's runs across either.
  const basins = curated.filter((h) => (h.kind === 'water' || h.kind === 'site') && h.ring !== undefined).map((h) => toViewRing(view, h.ring ?? []))
  const inTown = (a: Vec2, b: Vec2) => {
    const mid: Vec2 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
    return (plans.length === 0 || plans.some((r) => pointInRing(mid, r))) && !basins.some((r) => pointInRing(mid, r))
  }
  const ribbonOf = (kind: Ribbon['kind'], line: LineFeature, width: number, today = true): Ribbon | null => {
    const pts = line.points.map(([lon, lat]) => view.toView(lon, lat))
    const quads: Vec2[][] = []
    const center: Vec2[][] = []
    for (let i = 0; i + 1 < pts.length; i++) {
      const seg = clipSegmentToRect(pts[i], pts[i + 1], wide)
      if (seg === null) continue
      if (today && (kind === 'road' || kind === 'path' || kind === 'rail') && !inTown(seg[0], seg[1])) continue
      const q = segmentQuad(seg[0], seg[1], width / 2, width / 2)
      if (q === null) continue
      quads.push(q)
      center.push([seg[0], seg[1]])
    }
    return quads.length === 0 ? null : { kind, quads, center }
  }

  const railScale = time?.history.railScale ?? 1
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
      const r = ribbonOf('rail', f, 3.2 * railScale)
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
  // Curated track (a station's loop, long since taken up), drawn as rail.
  for (const h of curated) {
    if (h.kind !== 'rail') continue
    for (const [k, run] of [...(h.line ? [h.line] : []), ...(h.lines ?? [])].entries()) {
      const r = ribbonOf('rail', { type: 'line', id: `${h.id}:${k}`, tags: {}, points: run }, (h.width ?? 3.2) * railScale, false)
      if (r) ribbons.push(r)
    }
  }
  // A racecourse or promenade that is gone: a closed loop drawn as a path.
  for (const h of curated) {
    if (h.kind !== 'track' || h.line === undefined) continue
    const r = ribbonOf('racetrack', { type: 'line', id: h.id, tags: {}, points: [...h.line, h.line[0]] }, h.width ?? 12)
    if (r) ribbons.push(r)
  }
  // Streetcar lines: a bold ribbon down the street, wider than the track, so it reads at a
  // city-wide scale.
  const tramRuns: { id: string; pts: Vec2[] }[] = []
  const tramScale = time?.history.streetcarScale ?? 1
  for (const h of curated) {
    if (h.kind !== 'streetcar') continue
    for (const [k, run] of [...(h.line ? [h.line] : []), ...(h.lines ?? [])].entries()) {
      const r = ribbonOf('tram', { type: 'line', id: `${h.id}:${k}`, tags: {}, points: run }, (h.width ?? 9) * tramScale)
      if (r) ribbons.push(r)
      tramRuns.push({ id: `${h.id}:${k}`, pts: run.map(([lon, lat]) => view.toView(lon, lat)) })
    }
  }
  stats.streetcarLines = curated.filter((h) => h.kind === 'streetcar').length
  stats.ribbons = ribbons.length

  // ---- buildings ---------------------------------------------------------------------------
  const items: Item[] = []
  let cutPlaneOut: CutPlane | undefined
  let sectionsOut: Vec2[][] | undefined
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
  // Each part belongs to the smallest outline holding its centroid. The parts replace the
  // outline only where the parts that reach the ground cover at least half of it; many
  // outlines carry parts for only their crown or their rooftop works, and dropping such an
  // outline would leave its parts in the air. A kept outline is drawn whole, and its parts only
  // above its roof. Parts that are only roofs (building:part=roof) never replace the building
  // under them: it stays, as their podium.
  const areaOf = (s: Solid) => Math.abs(signedArea(s.outer))
  // Heights: a curated one for a building in a dated series (`History['dates']`), else the tags'.
  const heightOf = new Map((time?.history.dates ?? []).flatMap((d) => (d.height === undefined ? [] : [[d.id, d.height] as const])))
  const heightsOf = (s: { id: string; tags: Solid['tags'] }, area: number): ReturnType<typeof buildingHeights> => {
    const h = heightOf.get(s.id)
    return h === undefined ? buildingHeights(s.tags, area, region.checkLevels === true) : { base: 0, top: h, source: 'height' }
  }
  // Every outline holding a part's centroid, smallest first.
  const holders = new Map<Solid, Solid[]>()
  for (const p of keptParts) {
    const c = centroid(p.outer)
    const hs = solids.filter((s) => !lattice.includes(s) && pointInRing(c, s.outer)).sort((x, y) => areaOf(x) - areaOf(y))
    if (hs.length > 0) holders.set(p, hs)
  }
  const replaced = new Set<Solid>()
  let underParts = 0
  for (const s of solids) {
    const mine = keptParts.filter((p) => p.tags['building:part'] !== 'roof' && (holders.get(p) ?? []).includes(s))
    if (mine.length === 0) continue
    const grounded = mine.filter((p) => heightsOf(p, areaOf(p)).base < 0.5).map((p) => p.outer)
    if (groundCover(s.outer, s.inners, grounded) >= PARTS_REPLACE) replaced.add(s)
    else underParts++
  }
  if (underParts > 0) stats.outlinesUnderParts = underParts
  // The height a part's own data is raised to: the roof of the outline it stands on, if drawn.
  const floorOf = new Map<Solid, number>()
  const inFrame = (s: Solid) => s.outer.every((p) => insideRect(p, frame))
  const partsShown = keptParts.filter((p) => {
    const hs = holders.get(p)
    if (hs === undefined) return true
    // A building is drawn whole or not at all: its parts go with an outline the frame cuts.
    if (!inFrame(hs[0])) return false
    const kept = hs.filter((s) => !replaced.has(s))
    if (kept.length === 0 || isShellRoof(p.tags)) return true
    const roofTop = Math.max(...kept.map((s) => heightsOf(s, areaOf(s)).top))
    const own = heightsOf(p, areaOf(p))
    if (own.top <= roofTop + 0.5) return false
    if (own.base < roofTop) floorOf.set(p, roofTop)
    return true
  })
  const shown = solids.filter((s) => !replaced.has(s)).concat(partsShown)

  const towerParts: TowerPart[] = []
  let heightSources = { height: 0, model: 0, levels: 0, guess: 0 }
  let fresh = 0
  let undated = 0
  const datedBy = { curated: 0, osm: 0, parcel: 0 }
  // A curated site (a station's grounds, a fairground) was laid out otherwise while it stood:
  // today's buildings on it are not drawn.
  const sites = curated.filter((h) => h.kind === 'site' && h.ring !== undefined).map((h) => toViewRing(view, h.ring ?? []))
  // Prisms wait in `entries` until every one is placed, so that none is left standing on air.
  const entries: (Item | { prism: Prism; make: (p: Prism) => Item })[] = []
  // A footprint from a model (Microsoft's) whose center is on water is a boat, a pier head
  // or a boathouse the model cannot tell from a house; drawn, it is a house standing in the
  // water. Buildings mapped in OSM on water (boathouses, piers) stay.
  const sc = { ground } as unknown as Scene
  let modelOnWater = 0
  let footprintsDrawn = 0
  let datedFromParcels = 0
  for (const s of shown) {
    if (!inFrame(s)) continue
    if (sites.length > 0 && sites.some((r) => pointInRing(centroid(s.outer), r))) continue
    if (s.tags.source === 'microsoft' && onWater(sc, centroid(s.outer))) {
      modelOnWater++
      continue
    }
    const area = Math.abs(signedArea(s.outer)) - s.inners.reduce((a, h) => a + Math.abs(signedArea(h)), 0)
    if (area < minArea) continue
    const outer = orient(simplifyRing(s.outer, 0.45), true)
    if (outer.length < 3) continue
    const inners = s.inners.map((h) => orient(simplifyRing(h, 0.45), false)).filter((h) => h.length >= 3)
    const own = heightsOf(s, area)
    const floor = floorOf.get(s)
    const h = floor === undefined ? own : { ...own, base: floor }
    if (!Number.isFinite(h.base) || !Number.isFinite(h.top)) continue
    heightSources[h.source]++
    if (s.tags.source === 'microsoft') footprintsDrawn++
    // Seat the building on the ground under it (`seatLevel`): walls reach down to the lowest
    // corner, and heights count from a level set by the true slope, not the drawn one. The parts
    // of one building all count from the level of its outline.
    const grounds = outer.map((p) => terrain.z(p))
    const gMin = Math.min(...grounds)
    const gMean = grounds.reduce((a, b) => a + b, 0) / grounds.length
    const holder = holders.get(s)?.[0]
    const level = holder === undefined
      ? seatLevel(region.seatOnBanks === true && spansWater(s.tags, outer, (p) => onWater(sc, p)) ? bankGrounds(outer, grounds, (p) => onWater(sc, p)) : grounds, terrain.exaggeration)
      : seatLevel(holder.outer.map((p) => terrain.z(p)), terrain.exaggeration)
    // A bridge tower's lowest mapped parts stand on the ground or water: OSM often maps a
    // tower's legs from the pier top up and leaves the pier out. A part is lowest when no part
    // of a bridge tower within `TOWER_REACH` of it starts lower (struts between the legs do).
    const footed = h.base > 0 && isBridgeTower(s.tags) && !shown.some((o) => {
      if (o === s || !isBridgeTower(o.tags)) return false
      const c = centroid(s.outer)
      if (!o.outer.some((p) => Math.hypot(p[0] - c[0], p[1] - c[1]) < TOWER_REACH)) return false
      return heightsOf(o, Math.abs(signedArea(o.outer))).base < h.base
    })
    const base = h.base > 0 && !footed ? level + h.base : gMin
    const top = Math.max(level + h.top, base + 2.5)
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
    // A parcel's year built decided something here: whether the building stands in a past
    // year, or that it is drawn as new since the previous one. Today's scene otherwise draws
    // every building whatever its date.
    if (dated?.source === 'parcel' && time !== undefined && (time.year < time.history.present || roof === pal.fresh)) datedFromParcels++
    if (lattice.includes(s)) entries.push(spire(view, pal, s.id, latticeFootprint(outer, area), base, gMean + h.top, dotsMode, s.tags.name))
    else if (isShellRoof(s.tags)) {
      // Seat the shell on the roof of the building it stands on, if any.
      const c = centroid(outer)
      const under = solids.find((o) => o !== s && pointInRing(c, o.outer) && shown.includes(o))
      const podium = under === undefined ? 0 : heightsOf(under, Math.abs(signedArea(under.outer))).top
      entries.push(spire(view, pal, s.id, outer, gMin + podium, gMean + podium + SHELL_RISE * Math.sqrt(area), dotsMode, s.tags.name, (t) => 1 - t * 0.97, false, 4))
    } else {
      const span = s.tags.building === 'bridge' || s.tags['building:part'] === 'bridge' || s.tags.man_made === 'bridge' || isBridge(s.tags)
      const prism: Prism = { outer, base, top, foot: gMin, raised: h.base > 0 && !footed, span }
      entries.push({ prism, make: (p) => extrude(view, pal, s.id, outer, inners, p.base, p.top, roof, dotsMode, s.tags.name) })
    }
    if (isBridgeTower(s.tags)) towerParts.push({ at: centroid(outer), top })
  }
  if (modelOnWater > 0) stats.footprintsOnWater = modelOnWater
  stats.footprintsDrawn = footprintsDrawn
  if (time !== undefined) stats.datedFromParcels = datedFromParcels
  const prisms = entries.flatMap((e) => ('prism' in e ? [e.prism] : []))
  const settled = settlePrisms(prisms)
  if (settled > 0) stats.partsSettled = settled
  for (const e of entries) items.push('prism' in e ? e.make(e.prism) : e)
  stats.buildings = items.length
  // Streetcars on their lines: a car every `TRAM_SPACING` meters along each run, 14 m long and
  // 3.6 m tall (a 1920s double-truck car) but 5.4 m wide, about twice a real car's width so its
  // pale roof reads against the line, all times the history's `streetcarScale`; set on the
  // ground and turned with the street. Their spacing is for the picture, not a timetable.
  let cars = 0
  const tramBoxes: Box[] = []
  for (const run of tramRuns) {
    let along = TRAM_SPACING / 2
    let walked = 0
    for (let i = 0; i + 1 < run.pts.length; i++) {
      const a = run.pts[i]
      const b = run.pts[i + 1]
      const len = Math.hypot(b[0] - a[0], b[1] - a[1])
      while (along <= walked + len) {
        const t = (along - walked) / len
        const c: Vec2 = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
        along += TRAM_SPACING
        if (c[0] < frame.minX + 20 || c[0] > frame.maxX - 20 || c[1] < frame.minY + 20 || c[1] > frame.maxY - 20) continue
        const ux = (b[0] - a[0]) / len
        const uy = (b[1] - a[1]) / len
        const hl = 7 * tramScale
        const hw = 2.7 * tramScale
        let ring: Vec2[] = [
          [c[0] - ux * hl + uy * hw, c[1] - uy * hl - ux * hw],
          [c[0] + ux * hl + uy * hw, c[1] + uy * hl - ux * hw],
          [c[0] + ux * hl - uy * hw, c[1] + uy * hl + ux * hw],
          [c[0] - ux * hl - uy * hw, c[1] - uy * hl + ux * hw],
        ]
        if (signedArea(ring) < 0) ring = ring.reverse()
        const base = terrain.z(c)
        const carPal = { ...pal, wallLit: pal.tramCar[0], wallShade: pal.tramCar[1] }
        tramBoxes.push({ id: `tram:${run.id}:${cars}`, ring, z0: base + 0.4, z1: base + 0.4 + 3.6 * tramScale, tone: 'tram' })
        items.push(extrude(view, carPal, `tram:${run.id}:${cars}`, ring, [], base + 0.4, base + 0.4 + 3.6 * tramScale, pal.tramCar[2], 'none'))
        cars++
      }
      walked += len
    }
  }
  stats.streetcars = cars
  if (cars > 0 || tramRuns.length > 0) stats.streetcarScale = tramScale
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
    let parts = 0
    // Modeled parts first find their levels together, so a part can rest on another. A part
    // drawn only in whole views (a building's massing) or only in cutaways (its rooms) is left
    // out of the other.
    const cut = region.cutaway
    const shown = (h: HistoryFeature) => (cut === undefined ? h.only !== 'cutaway' : h.only !== 'whole')
    const zOf = (e: number) => (e - terrain.datum) * terrain.exaggeration
    const partGround = curated.filter((h) => h.kind === 'landmark' && h.ring !== undefined && h.tone !== undefined && shown(h))
      .map((h) => ({ id: h.id, seat: h.seat, on: h.on, base: h.base, height: h.height, grounds: orient(toViewRing(view, h.ring!), true).map((p) => terrain.z(p)), ...(h.elevation === undefined ? {} : { at: zOf(h.elevation) }) }))
    const levels = partLevels(partGround)
    const placed: PlacedPart[] = []
    for (const h of curated) {
      if (h.kind !== 'landmark' || h.ring === undefined || !shown(h)) continue
      const outer = orient(toViewRing(view, h.ring), true)
      if (!outer.every((p) => insideRect(p, frame))) continue
      const ruined = h.ruin !== undefined && time.year >= h.ruin
      const grounds = outer.map((p) => terrain.z(p))
      if (h.tone !== undefined) {
        // A part of a modeled building: from its seat, in its own tone.
        const seat = levels.get(h.id) ?? Math.min(...grounds) + (h.base ?? 0)
        const top = h.upTo !== undefined ? zOf(h.upTo) : seat + (h.height ?? 10)
        parts++
        // A stair or an arch keeps its corners in order: its first edge is its foot, or its span.
        if (cut !== undefined) placed.push({ h, outer: h.shape === 'stair' || h.shape === 'arch' ? toViewRing(view, h.ring) : outer, seat, top })
        else {
          const t = toned(pal, h.tone)
          const solid = h.shape === 'revolve' ? solidItem(view, partTones(pal, h), `history:${h.id}`, partSolids({ h, outer, seat, top }).solids, h.name) : null
          if (solid !== null) items.push(solid)
          else items.push(h.shape === 'dome'
            ? dome(view, pal, `history:${h.id}`, outer, seat, top, h.name)
            : extrude(view, t.pal, `history:${h.id}`, outer, [], seat, top, t.roof, 'none', h.name))
        }
        continue
      }
      const base = Math.min(...grounds)
      const top = Math.max(seatLevel(grounds, terrain.exaggeration) + (h.height ?? 10) * (ruined ? 0.45 : 1), base + 2.5)
      items.push(extrude(view, pal, `history:${h.id}`, outer, [], base, top, ruined ? pal.ash : pal.lost, dotsMode, h.name))
      landmarks++
    }
    stats.landmarks = landmarks
    if (parts > 0) stats.parts = parts
    // Platform canopies and standing trains, set on the ground under them.
    const inFrame = (p: Vec2) => p[0] > frame.minX + 5 && p[0] < frame.maxX - 5 && p[1] > frame.minY + 5 && p[1] < frame.maxY - 5
    const keepBoxes = (list: Box[]) => list.filter((b) => b.ring.every(inFrame))
    let canopies = 0
    let cars = 0
    const boxes: Box[] = []
    for (const h of curated) {
      if (h.kind === 'canopy' && h.line !== undefined && shown(h)) {
        const kept = keepBoxes(canopyBoxes(`history:${h.id}`, h.line.map(([lon, lat]) => view.toView(lon, lat)), h.width ?? 9, h.height ?? 5, (p) => terrain.z(p)))
        // A post stands only under a roof that is drawn.
        const roofs = new Set(kept.map((b) => b.id))
        const got = kept.filter((b) => !b.id.includes(':post:') || roofs.has(b.id.replace(':post:', ':')))
        boxes.push(...got)
        canopies += got.length / 2
      }
      const train = cut !== undefined && h.cutTrain !== undefined ? h.cutTrain : h.train
      if (h.kind === 'rail' && train !== undefined && h.line !== undefined) {
        const got = keepBoxes(trainBoxes(`history:${h.id}`, h.line.map(([lon, lat]) => view.toView(lon, lat)), train, (p) => terrain.z(p)))
        boxes.push(...got)
        cars += got.length
      }
    }
    if (canopies > 0) stats.canopyPieces = canopies
    if (cars > 0) stats.trainPieces = cars
    if (cut === undefined) items.push(...boxes.map((b) => boxItem(view, pal, b)))
    else {
      const outlineRings = cut.outline === undefined ? [] : curated
        .filter((h) => h.ring !== undefined && (cut.outline?.parts ?? []).some((p) => h.id.startsWith(p)))
        .map((h) => offsetConvex(orient(toViewRing(view, h.ring!), true), cut.outline?.offset ?? 0))
      const keepZ = cut.floor !== undefined && cut.keep !== undefined ? zOf(cut.floor) + cut.keep : undefined
      const done = cutawayItems(view, pal, cut, placed, extra.section === true ? [...boxes, ...tramBoxes] : boxes, {
        ...(keepZ === undefined ? {} : { keepZ }), ...(cut.floor === undefined ? {} : { floorZ: zOf(cut.floor) }), section: extra.section === true, outlineRings,
        // The outline lies on the ground, or on whatever kept part it crosses (a porch).
        // The outline lies level at the cut's floor (or on the ground, with no floor given).
        ground: (p) => (cut.floor === undefined ? terrain.z(p) : zOf(cut.floor)),
      })
      if (extra.section === true) items.length = 0
      for (const it of done.items) items.push(it)
      if (extra.section !== true) {
        (cut.travelers ?? []).forEach((t, k) => {
          const at = view.toView(t.at[0], t.at[1])
          items.push(travelerItem(view, pal, `traveler:${k + 1}`, at, t.floor === undefined ? terrain.z(at) : zOf(t.floor), t.facing))
        })
      }
      for (const [k, v] of Object.entries(done.stats)) stats[k] = v
      cutPlaneOut = done.plane
      if (done.sections.length > 0) sectionsOut = done.sections
    }
    // Buildings traced from fire-insurance maps that are gone today, in the maps' colors.
    // A sheet gives a building but not the shore it stood on: one with half its footprint or
    // more on water drawn in its year (today's river and canals, or a curated basin) would stand
    // in the water, so it is left out and counted (`tracedOnWater`).
    const ends = { map: 0, rebuilt: 0, highway: 0, assumed: 0 }
    let tracedOnWater = 0
    // A rail viaduct standing in the year runs where a traced building stood: the building was
    // cleared for it (most were mapped before the viaducts of 1901) or the sheet misplaces it.
    // Drawn, its piers pass through the roof, so it is left out and counted (`tracedUnderViaduct`).
    const viaducts = features.filter((f): f is LineFeature => f.type === 'line' && f.tags.railway !== undefined && isBridge(f.tags))
      .map((f) => f.points.map(([lon, lat]) => view.toView(lon, lat)))
    const underViaduct = (ring: Ring): boolean => viaducts.some((pts) => pts.some((p) => pointInRing(p, ring)) ||
      pts.slice(1).some((q, i) => ring.some((a, k) => segmentsCross(pts[i], q, a, ring[(k + 1) % ring.length]))))
    let tracedUnderViaduct = 0
    for (const b of time.history.traced) {
      if (!alive(b.from, b.to, time.year)) continue
      const outer = orient(simplifyRing(toViewRing(view, b.ring), 0.3), true)
      if (outer.length < 3 || !outer.every((p) => insideRect(p, frame))) continue
      if (wetShare(outer, (p) => onWater(sc, p)) >= 0.5) {
        tracedOnWater++
        continue
      }
      if (underViaduct(outer)) {
        tracedUnderViaduct++
        continue
      }
      const grounds = outer.map((p) => terrain.z(p))
      const base = Math.min(...grounds)
      const top = Math.max(seatLevel(grounds, terrain.exaggeration) + b.storeys * 3.6, base + 2.5)
      items.push(extrude(view, pal, `traced:${b.id}`, outer, [], base, top, pal.traced[b.material], dotsMode))
      ends[b.end]++
    }
    stats.traced = ends.map + ends.rebuilt + ends.highway + ends.assumed
    if (tracedOnWater > 0) stats.tracedOnWater = tracedOnWater
    if (tracedUnderViaduct > 0) stats.tracedUnderViaduct = tracedUnderViaduct
    stats.tracedEndMap = ends.map
    stats.tracedEndRebuilt = ends.rebuilt
    stats.tracedEndHighway = ends.highway
    stats.tracedEndAssumed = ends.assumed
    stats.curated = curated.length
  }

  if (extra.section === true) {
    // The flat section keeps only what the cut made.
    for (let k = items.length - 1; k >= 0; k--) if (!(items[k].id.startsWith('history:') || items[k].id.startsWith('tram:'))) items.splice(k, 1)
  }

  // ---- bridges -----------------------------------------------------------------------------
  let spans = 0
  const roofs = roofIndex(items)
  const chains = chainBridges(plans.length > 0 || extra.section === true ? [] : bridgeLines.filter((f) => !skyways.has(f)))
  const ends = bridgeEnds(view, region, chains)
  const towers = suspensionTowers(view, chains, towerParts)
  const lines = groupDecks(chains, joinDecks(chains, chains.map((c, i) => (fix?: { start?: number; end?: number }) => deckLine(view, region, terrain, c, ends[i], fix))))
  for (let c = 0; c < chains.length; c++) {
    const pieces = bridgePieces(view, pal, region, terrain, chains[c], lines[c], roofs, towers.get(c))
    spans += pieces.filter((p) => p.pier !== true).length
    items.push(...pieces)
  }
  stats.bridgePieces = spans

  const labels: MapLabel[] = []
  for (const h of curated) {
    if (h.kind !== 'label' || h.at === undefined) continue
    const at = view.toView(h.at[0], h.at[1])
    if (!insideRect(at, frame)) continue
    labels.push({ text: h.name, ...(h.caption === undefined ? {} : { caption: h.caption }), at, z: terrain.z(at), anchor: h.anchor ?? 'middle' })
  }
  if (labels.length > 0) stats.labels = labels.length

  return {
    region, view, palette: pal, terrain, ground, ribbons, items, stats,
    ...(time === undefined ? {} : { time: { year: time.year, ...(time.title === undefined ? {} : { title: time.title }), curated } }),
    ...(labels.length === 0 ? {} : { labels }),
    ...(railScale > 1 ? { boldRail: true } : {}),
    ...(cutPlaneOut === undefined ? {} : { cut: cutPlaneOut }),
    ...(sectionsOut === undefined ? {} : { sections: sectionsOut }),
  }
}

/**
 * The features that stood in a year. Buildings by their dates (undated ones only in the
 * present; a curated `until` ends one before today); everything else by the history's era rules.
 */
export const asOf = (features: readonly Feature[], time: TimeContext): Feature[] =>
  features.filter((f) => {
    const isBuilding = f.type === 'polygon' && (f.tags.building !== undefined || f.tags['building:part'] !== undefined)
    if (!isBuilding) return featureAlive(f, time.year, time.history)
    const d = time.dates.get(f.id)
    if (d === undefined) return time.year >= time.history.present
    return d.year <= time.year && (d.until === undefined || time.year < d.until || time.year >= time.history.present)
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
 * A prism: walls on every edge turned toward the camera, painted far to near, then the roof.
 * Rings are view meters; the outer runs counter-clockwise and holes clockwise, so the outward
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
    footprint: outer,
  }
}

/**
 * The level a building's heights count from, on ground drawn `exaggeration` times steeper
 * than life. Its walls reach down to the lowest ground under it, and its roof stands its
 * height above the lowest ground plus half the *true* fall across the footprint: so on the
 * downhill side it shows what it would on the real slope (its height, plus half the fall),
 * and the rest of the drawn relief goes into the hill on the uphill side. A two-story house
 * on a steep street stays a two-story house. On flat ground, the level is the ground.
 */
export const seatLevel = (grounds: readonly number[], exaggeration: number): number => {
  const lo = Math.min(...grounds)
  const hi = Math.max(...grounds)
  return lo + (hi - lo) / (2 * Math.max(1, exaggeration))
}

/**
 * Does a building span water? OSM says so with a `layer` of 1 or more (it stands over
 * something), and the water under its center says what: a mill or a house built over a canal
 * or a race. Such a building stands on the banks, and the ground under its middle is the
 * water's bed, so it counts its height from the banks (`bankGrounds`).
 */
export const spansWater = (tags: Readonly<Record<string, string>>, outer: Ring, wet: (p: Vec2) => boolean): boolean => {
  const layer = parseInt(tags.layer ?? '', 10)
  return Number.isFinite(layer) && layer >= 1 && wet(centroid(outer))
}

/** Do segments ab and cd cross (not merely touch at an end)? */
export const segmentsCross = (a: Vec2, b: Vec2, c: Vec2, d: Vec2): boolean => {
  const o = (p: Vec2, q: Vec2, r: Vec2) => (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
  return o(a, b, c) * o(a, b, d) < 0 && o(c, d, a) * o(c, d, b) < 0
}

/** The share of a footprint on water, from 0 to 1, sampled on a grid of about 100 points (its centroid alone if too small to sample). */
export const wetShare = (outer: Ring, wet: (p: Vec2) => boolean): number => {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  for (const [x, y] of outer) {
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y)
  }
  const step = Math.max(0.25, Math.sqrt(((maxX - minX) * (maxY - minY)) / 100))
  let inside = 0
  let wetCount = 0
  for (let y = minY + step / 2; y < maxY; y += step) {
    for (let x = minX + step / 2; x < maxX; x += step) {
      const p: Vec2 = [x, y]
      if (!pointInRing(p, outer)) continue
      inside++
      if (wet(p)) wetCount++
    }
  }
  if (inside === 0) return wet(centroid(outer)) ? 1 : 0
  return wetCount / inside
}

/** The ground under a building's corners on land, or all of them if none is on land. */
export const bankGrounds = (outer: Ring, grounds: readonly number[], wet: (p: Vec2) => boolean): number[] => {
  const dry = grounds.filter((_, i) => !wet(outer[i]))
  return dry.length > 0 ? dry : [...grounds]
}

/**
 * How much of an outline's ground the parts that reach the ground cover, from 0 to 1,
 * sampled on a grid of about 400 points (the centroid alone for a footprint too small to
 * sample). Holes in the outline are not ground.
 */
export const groundCover = (outer: Ring, inners: readonly Ring[], grounded: readonly Ring[]): number => {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  for (const [x, y] of outer) {
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y)
  }
  const step = Math.max(0.25, Math.sqrt(((maxX - minX) * (maxY - minY)) / 400))
  let inside = 0
  let covered = 0
  for (let y = minY + step / 2; y < maxY; y += step) {
    for (let x = minX + step / 2; x < maxX; x += step) {
      const p: Vec2 = [x, y]
      if (!pointInRing(p, outer) || inners.some((h) => pointInRing(p, h))) continue
      inside++
      if (grounded.some((r) => pointInRing(p, r))) covered++
    }
  }
  if (inside === 0) return grounded.some((r) => pointInRing(centroid(outer), r)) ? 1 : 0
  return covered / inside
}

/** Do two footprints overlap or touch (within `tol` meters)? */
export const footprintsMeet = (a: readonly Vec2[], b: readonly Vec2[], tol: number): boolean => {
  const near = (p: Vec2, ring: readonly Vec2[]) => {
    if (pointInRing(p, ring)) return true
    for (let i = 0; i < ring.length; i++) {
      const s = ring[i]
      const e = ring[(i + 1) % ring.length]
      const dx = e[0] - s[0]
      const dy = e[1] - s[1]
      const l2 = dx * dx + dy * dy
      const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - s[0]) * dx + (p[1] - s[1]) * dy) / l2))
      if (Math.hypot(p[0] - s[0] - t * dx, p[1] - s[1] - t * dy) <= tol) return true
    }
    return false
  }
  return a.some((p) => near(p, b)) || b.some((p) => near(p, a))
}

/** Do two footprints' interiors overlap? Tested at each one's centroid and at its corners pulled a tenth of the way in. */
export const footprintsOverlap = (a: readonly Vec2[], b: readonly Vec2[]): boolean => {
  const probes = (r: readonly Vec2[]): Vec2[] => {
    const c = centroid(r)
    return [c, ...r.map((p): Vec2 => [p[0] + (c[0] - p[0]) * 0.1, p[1] + (c[1] - p[1]) * 0.1])]
  }
  return probes(a).some((p) => pointInRing(p, b)) || probes(b).some((p) => pointInRing(p, a))
}

/** A prism about to be drawn: its footprint, its scene heights, and the ground under its foot. */
export interface Prism { outer: Ring; base: number; top: number; foot: number; raised: boolean; span: boolean }

/**
 * Nothing stands on air. A prism the data raises off the ground (`min_height`,
 * `building:min_level`) keeps its base if a prism beside or under it holds it there (a
 * cantilever off a tower's side, a skyway between two), or if the data says it is a bridge
 * (`span`). Otherwise it reaches down to the top of what is under it, or to the ground: a
 * crown whose shaft was left out of the data, or whose shaft was too small to draw, stands on
 * what is there. Prisms are settled from the lowest base up. Returns how many were lowered.
 */
export const settlePrisms = (prisms: Prism[]): number => {
  const tol = 0.5
  let lowered = 0
  const order = prisms.map((p, i) => i).filter((i) => prisms[i].raised && !prisms[i].span).sort((a, b) => prisms[a].base - prisms[b].base)
  const boxes = prisms.map((p) => {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
    for (const [x, y] of p.outer) {
      minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y)
    }
    return { minX, maxX, minY, maxY }
  })
  for (const i of order) {
    const p = prisms[i]
    if (p.base <= p.foot + tol) continue
    const bi = boxes[i]
    const others = prisms.filter((q, j) => j !== i && boxes[j].minX <= bi.maxX + tol && boxes[j].maxX >= bi.minX - tol && boxes[j].minY <= bi.maxY + tol && boxes[j].maxY >= bi.minY - tol)
    const held = others.some((q) => q.base <= p.base + tol && q.top >= p.base + tol && footprintsMeet(p.outer, q.outer, tol))
    if (held) continue
    let support = p.foot
    for (const q of others) if (q.top <= p.base + tol && q.top > support && footprintsOverlap(p.outer, q.outer)) support = q.top
    if (p.base - support > tol) {
      p.base = support
      lowered++
    }
  }
  return lowered
}

/** A part of a bridge's tower (a suspension or cable-stayed bridge's pylon). */
export const isBridgeTower = (t: Readonly<Record<string, string>>): boolean => t['tower:type'] === 'bridge'
/** Meters around a bridge tower's part to look for a part that starts lower. */
export const TOWER_REACH = 40

/** OSM's lattice towers: tagged as such, or a building whose pyramidal roof is its whole height. */
export const isLatticeTower = (t: Readonly<Record<string, string>>): boolean =>
  t.building !== undefined && (t['tower:construction'] === 'lattice' || (t['roof:shape'] === 'pyramidal' && t['roof:height'] !== undefined && t['roof:height'] === t.height))

/**
 * The outline a lattice tower tapers from. Every edge of the footprint becomes a wall that
 * narrows toward the axis all the way up, so the short jogs a mapped outline has where a leg
 * meets an arch (1 to 3 m on the Eiffel Tower) would run up the tower as slivers of near-doubled
 * lines. Corners closer than `LATTICE_SIMPLIFY` × √area to their neighbors' line are dropped;
 * the legs and the curve of the arches between them stay.
 */
export const LATTICE_SIMPLIFY = 0.03
export const latticeFootprint = (outer: Ring, area: number): Ring => {
  const ring = simplifyRing(outer, LATTICE_SIMPLIFY * Math.sqrt(area))
  return ring.length >= 3 ? orient(ring, true) : outer
}

/**
 * A curved roof shell mapped with no height (the Sydney Opera House's sails): a roof part whose
 * shape is round, spherical or circular. It is drawn as a sail rising to a point, its height
 * `SHELL_RISE` × √area, an approximation that grows with the shell like the real ones do.
 */
export const isShellRoof = (t: Readonly<Record<string, string>>): boolean =>
  t['building:part'] === 'roof' && ['round', 'spherical', 'circular'].includes(t['roof:shape'] ?? '') && t.height === undefined && t['min_height'] === undefined
export const SHELL_RISE = 1.6
/** Meters between the streetcars drawn on a line. */
/** Parts replace their outline when the parts that reach the ground cover at least this share of it. */
export const PARTS_REPLACE = 0.5
export const TRAM_SPACING = 900

/**
 * Half-width of a lattice tower at fraction `t` of its height, as a fraction of the base: the
 * Eiffel Tower's curve, which narrows roughly exponentially (0.56 at the first platform, 0.32
 * at the second), then runs out to a mast over the top sixth.
 */
export const spireProfile = (t: number): number => (t <= 0.84 ? Math.exp(-3.3 * t) : Math.exp(-3.3 * 0.84) * (1 - (t - 0.84) / 0.16) * 0.9 + 0.01)

/**
 * A tapering tower: stacked frustums following `spireProfile`, each one's walls then its cap,
 * bottom to top (an upper piece always sits inside and above the one below it). The walls are
 * darkened toward the ink, for iron.
 */
export const spire = (
  view: View, pal: Palette, id: string, outer: Ring, base: number, top: number, dots: 'all' | 'roof' | 'none', name?: string,
  profile: (t: number) => number = spireProfile, iron = true, STEPS = 16,
): Item => {
  const c = centroid(outer)
  const at = (p: Vec2, k: number): Vec2 => [c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k]
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
        shape: {
          pts: [view.toScreen(at(a, k0), z0), view.toScreen(at(b, k0), z0), view.toScreen(at(b, k1), z1), view.toScreen(at(a, k1), z1)],
          fill: tone,
          ink: true,
          // As in `extrude`, the lowest walls carry the dots at their own feet, so whatever is
          // painted in front of a corner (a nearer leg, the tower above it) hides its dot.
          ...(dots === 'all' && i === 0 ? { dots: [view.toScreen(a, base), view.toScreen(b, base)] } : {}),
        },
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
    dots: [],
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

/** A bridge deck's width, meters: the road's, plus a meter and a half of parapet. */
const deckWidth = (t: Readonly<Record<string, string>>): number => (isRail(t) ? 4.5 : (roadWidth(t) ?? 6) + 1.5)

/** Ground under a deck is lowered in full from this far from a grounded end, meters, and not at all within half of it. */
export const ABUTMENT_KEEP = 10

/** How far past a deck's edge the ground either side of it is read, meters. */
export const UNDER_DECK_REACH = 8

/**
 * Lower the ground under bridge decks to what lies either side of them. A bare-earth model is
 * meant to have bridges taken out, but an overpass often stays in it as a ridge across the cut
 * it spans (or is filled level with the street from its abutments), and the road under it then
 * climbs over a hump. A grid node within a deck's footprint that stands more than half a meter
 * above the ground `UNDER_DECK_REACH` past the edges of all the decks there, on both sides,
 * takes the straight line across between those two. Ground is never raised, and a deck over
 * flat ground, a valley, a hillside or a bluff's crest changes nothing. Returns the number of
 * nodes lowered.
 */
export const carveUnderBridges = (terrain: Terrain, decks: readonly { pts: readonly Vec2[]; width: number }[], abutments: readonly Vec2[] = []): number => {
  const { nx, ny, x0, y0, cell, elev } = terrain
  // Which nodes are under a deck, and the deck's direction there.
  const under = new Int8Array(nx * ny)
  const dir = new Float32Array(nx * ny * 2)
  const best = new Float32Array(nx * ny).fill(Infinity)
  for (const d of decks) {
    const half = d.width / 2 + cell / 2
    for (let k = 1; k < d.pts.length; k++) {
      const [a, b] = [d.pts[k - 1], d.pts[k]]
      const len = Math.hypot(b[0] - a[0], b[1] - a[1])
      if (len < 1e-6) continue
      const ux = (b[0] - a[0]) / len
      const uy = (b[1] - a[1]) / len
      const i0 = Math.max(0, Math.floor((Math.min(a[0], b[0]) - half - x0) / cell))
      const i1 = Math.min(nx - 1, Math.ceil((Math.max(a[0], b[0]) + half - x0) / cell))
      const j0 = Math.max(0, Math.floor((Math.min(a[1], b[1]) - half - y0) / cell))
      const j1 = Math.min(ny - 1, Math.ceil((Math.max(a[1], b[1]) + half - y0) / cell))
      for (let j = j0; j <= j1; j++) {
        for (let i = i0; i <= i1; i++) {
          const px = x0 + i * cell - a[0]
          const py = y0 + j * cell - a[1]
          const along = px * ux + py * uy
          if (along < 0 || along > len) continue
          const off = Math.abs(-px * uy + py * ux)
          if (off > half) continue
          const n = j * nx + i
          under[n] = 1
          if (off < best[n]) {
            best[n] = off
            dir[2 * n] = ux
            dir[2 * n + 1] = uy
          }
        }
      }
    }
  }
  const at = (x: number, y: number) => {
    const i = Math.round((x - x0) / cell)
    const j = Math.round((y - y0) / cell)
    return i < 0 || j < 0 || i >= nx || j >= ny ? -1 : j * nx + i
  }
  const out = Float32Array.from(elev)
  let lowered = 0
  for (let n = 0; n < nx * ny; n++) {
    if (under[n] === 0) continue
    const x = x0 + (n % nx) * cell
    const y = y0 + Math.floor(n / nx) * cell
    // Step out across the deck both ways until clear of every deck, then a little more.
    const side = (sign: number): { z: number; d: number } | null => {
      const qx = -dir[2 * n + 1] * sign
      const qy = dir[2 * n] * sign
      for (let t = cell / 2; t <= 80; t += cell / 2) {
        const m = at(x + qx * t, y + qy * t)
        if (m < 0) return null
        if (under[m] === 0) {
          const d = t + UNDER_DECK_REACH
          const e = at(x + qx * d, y + qy * d)
          return e < 0 ? null : { z: terrain.elevation([x + qx * d, y + qy * d]), d }
        }
      }
      return null
    }
    const l = side(1)
    const r = side(-1)
    if (l === null || r === null) continue
    // Full depth from `ABUTMENT_KEEP` past a grounded end, none at the end: the street that
    // runs onto the bridge keeps its level.
    let near = Infinity
    for (const a of abutments) near = Math.min(near, Math.hypot(a[0] - x, a[1] - y))
    const w = Math.min(1, Math.max(0, near / ABUTMENT_KEEP - 0.5))
    const across = l.z + ((r.z - l.z) * l.d) / (l.d + r.d)
    // Only a ridge: ground under the deck higher than on both sides of it. A deck along the
    // crest of a bluff or a hillside keeps the ground under it.
    if (w > 0 && elev[n] > Math.max(l.z, r.z) + 0.5) {
      out[n] = elev[n] + (across - elev[n]) * w
      lowered++
    }
  }
  elev.set(out)
  return lowered
}

/** A run of bridge ways joined end to end, with which ends come down to the ground. */
export interface BridgeChain {
  readonly line: LineFeature
  /** Every name carried by any way in the chain, for deck rules. */
  readonly names: string
  readonly rampStart: boolean
  readonly rampEnd: boolean
  /** Some way in the chain is tagged `bridge:structure=suspension`. */
  readonly suspension?: boolean
}

const key = (p: Vec2) => `${p[0].toFixed(7)},${p[1].toFixed(7)}`

/** The sharpest turn a chain of bridge ways takes where two ways join, radians. */
export const MAX_CHAIN_TURN = Math.PI / 3

/** The turn at vertex `j` of a lon/lat line, radians (0 straight on, π doubling back). */
const turnAt = (pts: readonly Vec2[], j: number): number => {
  if (j <= 0 || j >= pts.length - 1) return 0
  const k = Math.cos((pts[j][1] * Math.PI) / 180)
  const ax = (pts[j][0] - pts[j - 1][0]) * k
  const ay = pts[j][1] - pts[j - 1][1]
  const bx = (pts[j + 1][0] - pts[j][0]) * k
  const by = pts[j + 1][1] - pts[j][1]
  return Math.abs(Math.atan2(ax * by - ay * bx, ax * bx + ay * by))
}

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
        // At a fork, carry on along the straightest way, and never turn back through one: a
        // chain that doubled back up the other branch would join two tracks into a V.
        let pick: { i: number; next: Vec2[]; turn: number } | null = null
        const head = key(pts[0])
        const tail = key(pts[pts.length - 1])
        for (let i = 0; i < left.length; i++) {
          const s = left[i].points
          let next: Vec2[] | null = null
          if (key(s[0]) === tail) next = pts.concat(s.slice(1))
          else if (key(s[s.length - 1]) === tail) next = pts.concat(s.slice(0, -1).reverse())
          else if (key(s[s.length - 1]) === head) next = s.slice(0, -1).concat(pts)
          else if (key(s[0]) === head) next = s.slice(1).reverse().concat(pts)
          if (next === null) continue
          const atTail = next.length > pts.length && next[0] === pts[0]
          const j = atTail ? pts.length - 1 : next.length - pts.length
          const turn = turnAt(next, j)
          if (turn > MAX_CHAIN_TURN) continue
          if (pick === null || turn < pick.turn) pick = { i, next, turn }
        }
        if (pick !== null) {
          pts = pick.next
          members.push(left[pick.i])
          left.splice(pick.i, 1)
          grew = true
        }
      }
      const ids = new Set(members.map((m) => m.id))
      const groundedAt = (p: Vec2) => [...(touches.get(key(p)) ?? [])].every((id) => ids.has(id))
      chains.push({
        line: { ...first, points: pts },
        names: members.map((m) => `${m.tags.name ?? ''} ${m.tags['bridge:name'] ?? ''}`).join(' ').toLowerCase(),
        rampStart: groundedAt(pts[0]),
        rampEnd: groundedAt(pts[pts.length - 1]),
        ...(members.some((m) => m.tags['bridge:structure'] === 'suspension') ? { suspension: true } : {}),
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

/** How far a ramp runs from the ground up to full deck height, meters. */
export const RAMP = 70

const ease = (u: number) => {
  const v = Math.min(1, Math.max(0, u))
  return v * v * (3 - 2 * v)
}

/**
 * Clearance over the ground at a point `s` along a bridge whose deck is `deck` high, `dist`
 * meters from the nearest place where the bridge network meets the ground, and which must meet
 * clearance `startC` and `endC` at its two ends (another bridge's height where it joins one).
 * Within `RAMP` of the ground the deck eases down to it; the ramp keeps its length on a short
 * bridge, so one shorter than two ramps never reaches full height (a 30 m footbridge over a
 * canal rises a meter or so, not into a 7 m tent). Within `RAMP` of an end that joins a higher
 * deck, it eases up to that deck.
 */
export const rampClearance = (deck: number, total: number, s: number, dist: number, startC: number, endC: number): number => {
  const own = deck * ease(dist / RAMP)
  const a = ease(s / RAMP)
  const b = ease((total - s) / RAMP)
  return Math.max(own, startC * (1 - a) + own * a, endC * (1 - b) + own * b)
}

/** Length along a chain to each of its vertices, view meters. */
const chainLengths = (view: View, chain: BridgeChain): number[] => {
  const pts = chain.line.points.map(([lon, lat]) => view.toView(lon, lat))
  const cum = [0]
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
  return cum
}

/** How a chain meets the rest: clearance at each end, and each vertex's distance to the ground. */
export interface BridgeEnds {
  readonly start: number
  readonly end: number
  /** Per vertex: meters along the bridge network to the nearest end that meets the ground. */
  readonly toGround: readonly number[]
}

/**
 * Bridges that touch form a network, anchored to the ground at every end that touches no other
 * bridge. A deck can only be as high as a ramp from the nearest anchor allows, measured along
 * the network: so where a viaduct fans out into a dozen short plaza lanes that each come down
 * within a few meters, the viaduct ramps down to the plaza instead of standing at full height
 * over a fan of steep ribbons. An end that joins another bridge (a ramp onto a viaduct of
 * another layer, a link at a fork) meets the highest of the decks there, so the two arrive at
 * one height instead of one stopping in mid-air above or below the other.
 */
export const bridgeEnds = (view: View, region: Region, chains: readonly BridgeChain[]): BridgeEnds[] => {
  const info = chains.map((c) => ({ deck: deckHeight(region, c), cum: chainLengths(view, c), keys: c.line.points.map(key) }))
  // Shortest distance along the network from every vertex to a grounded end (Dijkstra).
  const edges = new Map<string, [string, number][]>()
  const link = (a: string, b: string, w: number) => {
    edges.set(a, [...(edges.get(a) ?? []), [b, w]])
    edges.set(b, [...(edges.get(b) ?? []), [a, w]])
  }
  const dist = new Map<string, number>()
  const heap: [number, string][] = []
  const push = (d: number, k: string) => {
    heap.push([d, k])
    let i = heap.length - 1
    while (i > 0) {
      const p = (i - 1) >> 1
      if (heap[p][0] <= heap[i][0]) break
      ;[heap[p], heap[i]] = [heap[i], heap[p]]
      i = p
    }
  }
  const pop = (): [number, string] => {
    const top = heap[0]
    const last = heap.pop()!
    if (heap.length > 0) {
      heap[0] = last
      let i = 0
      for (;;) {
        const l = 2 * i + 1
        const r = l + 1
        let m = i
        if (l < heap.length && heap[l][0] < heap[m][0]) m = l
        if (r < heap.length && heap[r][0] < heap[m][0]) m = r
        if (m === i) break
        ;[heap[m], heap[i]] = [heap[i], heap[m]]
        i = m
      }
    }
    return top
  }
  chains.forEach((c, i) => {
    const { cum, keys } = info[i]
    for (let k = 1; k < keys.length; k++) link(keys[k - 1], keys[k], cum[k] - cum[k - 1])
    if (c.rampStart) push(0, keys[0])
    if (c.rampEnd) push(0, keys[keys.length - 1])
  })
  while (heap.length > 0) {
    const [d, k] = pop()
    if (dist.has(k)) continue
    dist.set(k, d)
    for (const [n, w] of edges.get(k) ?? []) if (!dist.has(n)) push(d + w, n)
  }
  const toGround = info.map(({ keys }) => keys.map((k) => dist.get(k) ?? Infinity))
  // Each node's height: the highest any chain through it may stand there.
  const at = new Map<string, number>()
  info.forEach(({ deck, keys }, i) => {
    keys.forEach((k, v) => at.set(k, Math.max(at.get(k) ?? 0, deck * ease(toGround[i][v] / RAMP))))
  })
  return chains.map((c, i) => {
    const keys = info[i].keys
    return {
      start: c.rampStart ? 0 : at.get(keys[0]) ?? info[i].deck,
      end: c.rampEnd ? 0 : at.get(keys[keys.length - 1]) ?? info[i].deck,
      toGround: toGround[i],
    }
  })
}

/** A building a bridge can meet: its outline and the heights of its base and roof. */
interface Roof { readonly ring: Ring; readonly base: number; readonly top: number; readonly box: [number, number, number, number] }

/** The buildings in a scene, for `buildingAt`. */
export const roofIndex = (items: readonly Item[]): Roof[] =>
  items.filter((i) => i.kind === 'building' && i.footprint !== undefined).map((i) => {
    const r = i.footprint!
    const xs = r.map((p) => p[0])
    const ys = r.map((p) => p[1])
    return { ring: r, base: i.zMin, top: i.zMax, box: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] }
  })

/** Building outlines (view meters) as roofs with no height: enough for `isSkyway`. */
export const buildingOutlines = (rings: readonly Ring[]): Roof[] =>
  rings.filter((r) => r.length >= 3).map((r) => {
    const xs = r.map((p) => p[0])
    const ys = r.map((p) => p[1])
    return { ring: r, base: 0, top: 0, box: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] }
  })

/** The tallest building standing at a view-meter point, if any. */
export const buildingAt = (roofs: readonly Roof[], p: Vec2): Roof | null => {
  let best: Roof | null = null
  for (const r of roofs) {
    if (p[0] < r.box[0] || p[0] > r.box[2] || p[1] < r.box[1] || p[1] > r.box[3]) continue
    if (!pointInRing(p, r.ring)) continue
    if (best === null || r.top > best.top) best = r
  }
  return best
}

/** How near a building a footbridge's end must be for it to count as a skyway, meters. */
export const SKYWAY_REACH = 3

/** The longest footbridge counted as a skyway, meters (a bridge's walkway past its towers is not). */
export const SKYWAY_LONGEST = 80

/**
 * A footbridge (a footway, path or cycleway) no longer than `SKYWAY_LONGEST` with an end at or
 * within `SKYWAY_REACH` of a building: a skyway or an enclosed bridge into an upper floor,
 * whose height OSM rarely gives.
 */
export const isSkyway = (t: Readonly<Record<string, string>>, pts: readonly Vec2[], roofs: readonly Roof[]): boolean => {
  // A sidewalk beside a street bridge is not a skyway, however near a building it lands.
  if (!isPath(t) || t.footway === 'sidewalk' || t.footway === 'crossing' || pts.length < 2) return false
  let length = 0
  for (let i = 1; i < pts.length; i++) length += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
  if (length > SKYWAY_LONGEST) return false
  const near = (p: Vec2, q: Vec2) => {
    const len = Math.max(1e-6, Math.hypot(p[0] - q[0], p[1] - q[1]))
    for (const d of [0, SKYWAY_REACH]) if (buildingAt(roofs, [p[0] + ((p[0] - q[0]) * d) / len, p[1] + ((p[1] - q[1]) * d) / len]) !== null) return true
    return false
  }
  return near(pts[0], pts[1]) || near(pts[pts.length - 1], pts[pts.length - 2])
}

/** A part of a bridge tower: where it stands (view meters) and the scene z of its top. */
interface TowerPart { readonly at: Vec2; readonly top: number }

/** A suspension bridge's tower, along its chain: `s` meters in, and its legs' offsets and tops. */
export interface Tower { readonly s: number; readonly legs: readonly { readonly d: number; readonly top: number }[] }

/** Meters off a suspension bridge's line that its towers' parts may stand. */
const TOWER_OFFSET = 25

/**
 * The towers of each suspension bridge (`bridge:structure=suspension`), found from the bridge
 * tower parts standing on its line: a cluster of parts along the line is one tower, and the
 * parts either side of the widest gap across the line are its two legs. Only the longest chain through a set of towers
 * carries the cables, so a bridge mapped as two carriageways and two sidewalks gets one pair.
 */
export const suspensionTowers = (view: View, chains: readonly BridgeChain[], parts: readonly TowerPart[]): Map<number, Tower[]> => {
  const out = new Map<number, Tower[]>()
  const used = new Set<TowerPart>()
  const order = chains.map((c, i) => ({ c, i, cum: chainLengths(view, c) }))
    .filter((x) => x.c.suspension === true)
    .sort((a, b) => b.cum[b.cum.length - 1] - a.cum[a.cum.length - 1])
  for (const { c, i, cum } of order) {
    const pts = c.line.points.map(([lon, lat]) => view.toView(lon, lat))
    const near: { s: number; d: number; top: number; part: TowerPart }[] = []
    for (const part of parts) {
      if (used.has(part)) continue
      let best: { s: number; d: number } | null = null
      for (let k = 1; k < pts.length; k++) {
        const [a, b] = [pts[k - 1], pts[k]]
        const len = cum[k] - cum[k - 1]
        if (len < 1e-6) continue
        const ux = (b[0] - a[0]) / len
        const uy = (b[1] - a[1]) / len
        const along = (part.at[0] - a[0]) * ux + (part.at[1] - a[1]) * uy
        if (along < 0 || along > len) continue
        // Left of the direction of travel is positive.
        const d = -(part.at[0] - a[0]) * uy + (part.at[1] - a[1]) * ux
        if (Math.abs(d) <= TOWER_OFFSET && (best === null || Math.abs(d) < Math.abs(best.d))) best = { s: cum[k - 1] + along, d }
      }
      if (best !== null) near.push({ ...best, top: part.top, part })
    }
    near.sort((a, b) => a.s - b.s)
    const clusters: (typeof near)[] = []
    for (const n of near) {
      const last = clusters[clusters.length - 1]
      if (last !== undefined && n.s - last[last.length - 1].s < 40) last.push(n)
      else clusters.push([n])
    }
    const towers: Tower[] = []
    for (const cl of clusters) {
      // The legs: the parts either side of the widest gap across the line.
      const byD = cl.slice().sort((a, b) => a.d - b.d)
      let cut = 0
      for (let k = 1; k < byD.length; k++) if (byD[k].d - byD[k - 1].d > (cut === 0 ? 0 : byD[cut].d - byD[cut - 1].d)) cut = k
      if (cut === 0 || byD[cut].d - byD[cut - 1].d < 4) continue
      const legs = [byD.slice(0, cut), byD.slice(cut)].map((side) => ({
        d: side.reduce((a, n) => a + n.d, 0) / side.length,
        top: Math.max(...side.map((n) => n.top)),
      }))
      towers.push({ s: cl.reduce((a, n) => a + n.s, 0) / cl.length, legs })
    }
    if (towers.length < 2) continue
    for (const n of near) used.add(n.part)
    out.set(i, towers)
  }
  return out
}

/** Meters a main cable hangs over the deck at the middle of a span between towers. */
export const CABLE_CLEARANCE = 2

/**
 * A main cable's height at `s` along a suspension bridge: parabolas through the anchorages at
 * each end (on the deck) and the tower tops, sagging between towers to `CABLE_CLEARANCE` over
 * the deck at mid-span, and hanging a little between the end towers and the anchorages.
 */
export const cableZ = (s: number, total: number, towers: readonly { s: number; top: number }[], deckZ: (s: number) => number): number => {
  const knots = [{ s: 0, z: deckZ(0) + CABLE_CLEARANCE, tower: false }, ...towers.map((t) => ({ s: t.s, z: t.top, tower: true })), { s: total, z: deckZ(total) + CABLE_CLEARANCE, tower: false }]
  let k = 1
  while (k < knots.length - 1 && knots[k].s < s) k++
  const a = knots[k - 1]
  const b = knots[k]
  const span = Math.max(1e-6, b.s - a.s)
  const u = Math.min(1, Math.max(0, (s - a.s) / span))
  const chord = a.z + (b.z - a.z) * u
  const sag = a.tower && b.tower
    ? Math.max(0, (a.z + b.z) / 2 - (deckZ((a.s + b.s) / 2) + CABLE_CLEARANCE))
    : 0.15 * Math.abs(b.z - a.z)
  return Math.max(deckZ(s) + 0.5, chord - sag * 4 * u * (1 - u))
}

/** Distance to the ground along the network at `s`, from the nearest vertex's. */
const toGroundAt = (ends: BridgeEnds, cum: readonly number[], s: number): number => {
  let d = Infinity
  for (let k = 0; k < cum.length; k++) d = Math.min(d, ends.toGround[k] + Math.abs(cum[k] - s))
  return d
}

/** How far past a grounded end the ground is read for its abutment, meters. */
export const ABUTMENT_REACH = 12

/**
 * The level of a grounded bridge end, from the ground `past(t)` meters beyond it: the rim the
 * ground climbs to within `ABUTMENT_REACH` where it levels off there (the outer half climbs
 * less than three quarters as much as the inner half), else the ground at the end.
 */
export const abutmentLevel = (past: (t: number) => number): number => {
  const g0 = past(0)
  let inner = g0
  let outer = -Infinity
  for (let t = 2; t <= ABUTMENT_REACH; t += 2) {
    if (t <= ABUTMENT_REACH / 2) inner = Math.max(inner, past(t))
    else outer = Math.max(outer, past(t))
  }
  const rise = inner - g0
  return rise > 0.5 && outer - inner < rise * 0.75 ? Math.max(inner, outer) : g0
}

/**
 * The deck's height along a bridge `total` meters long, as a function of `s`: `ground(s)` is
 * the scene height under it and `clearance(s)` how high over it the deck must be;
 * `startLevel` and `endLevel` are the scene heights of its two ends. The deck never dips below
 * the straight line between its ends, and rises above it in straight runs only where the
 * clearance needs.
 */
export const deckProfile = (
  total: number, ground: (s: number) => number, clearance: (s: number) => number, startLevel: number, endLevel: number,
): ((s: number) => number) => {
  // The deck profile. A bridge runs fairly straight between its abutments, and never closer to
  // what is under it than its clearance — except where it comes down to meet the ground.
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
  return (s: number) => {
    const f = (s / Math.max(1e-9, total)) * (samples - 1)
    const k = Math.min(samples - 2, Math.max(0, Math.floor(f)))
    const u = f - k
    return smooth[k] * (1 - u) + smooth[k + 1] * u
  }
}

/**
 * Decks that meet at a node meet at one height. A chain that runs on through the node sets the
 * height there; where only chain ends meet, the highest of them does. An end that joins
 * another deck then runs straight to that height, so no deck stops short in mid-air above or
 * below the one it joins. Grounded ends stay on the ground.
 */
export const joinDecks = (
  chains: readonly BridgeChain[], line: readonly ((fix?: { start?: number; end?: number }) => DeckLine)[],
): DeckLine[] => {
  const keys = chains.map((c) => c.line.points.map(key))
  let lines = line.map((f) => f())
  for (let pass = 0; pass < 3; pass++) {
    const through = new Map<string, number>()
    const ended = new Map<string, number>()
    lines.forEach((l, i) => {
      const ks = keys[i]
      for (let k = 1; k + 1 < ks.length; k++) through.set(ks[k], Math.max(through.get(ks[k]) ?? -Infinity, l.zAt(l.cum[k])))
      ended.set(ks[0], Math.max(ended.get(ks[0]) ?? -Infinity, l.startLevel))
      ended.set(ks[ks.length - 1], Math.max(ended.get(ks[ks.length - 1]) ?? -Infinity, l.endLevel))
    })
    let changed = false
    lines = lines.map((l, i) => {
      const ks = keys[i]
      const want = (k: string, own: number) => through.get(k) ?? ended.get(k) ?? own
      const start = chains[i].rampStart ? l.startLevel : want(ks[0], l.startLevel)
      const end = chains[i].rampEnd ? l.endLevel : want(ks[ks.length - 1], l.endLevel)
      if (Math.abs(start - l.startLevel) < 0.2 && Math.abs(end - l.endLevel) < 0.2) return l
      changed = true
      return line[i]({ start, end })
    })
    if (!changed) break
  }
  return lines
}

/** How far apart parallel bridge ways of one street may lie and still be one deck, meters. */
export const DECK_GROUP_REACH = 15

/** A bridge way shorter than this, meters, that touches a longer deck is drawn level with it. */
export const SHORT_DECK = 10

/** Where a point falls along a polyline: meters along it, and meters off it. */
const alongLine = (pts: readonly Vec2[], cum: readonly number[], p: Vec2): { s: number; off: number } => {
  let best = { s: 0, off: Infinity }
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1]
    const b = pts[i]
    const dx = b[0] - a[0]
    const dy = b[1] - a[1]
    const l2 = dx * dx + dy * dy
    const u = l2 < 1e-12 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    const off = Math.hypot(p[0] - a[0] - dx * u, p[1] - a[1] - dy * u)
    if (off < best.off) best = { s: cum[i - 1] + (cum[i] - cum[i - 1]) * u, off }
  }
  return best
}

/** A point `s` meters along a deck line. */
const deckPointAt = (l: DeckLine, s: number): Vec2 => {
  let i = 1
  while (i < l.cum.length - 1 && l.cum[i] < s) i++
  const u = (s - l.cum[i - 1]) / Math.max(1e-9, l.cum[i] - l.cum[i - 1])
  return [l.pts[i - 1][0] + (l.pts[i][0] - l.pts[i - 1][0]) * u, l.pts[i - 1][1] + (l.pts[i][1] - l.pts[i - 1][1]) * u]
}

/**
 * Where `follower` runs beside `leader` its whole length, within `DECK_GROUP_REACH` and the
 * same way along (a sidewalk beside its street, the other half of a divided street), the meters
 * along the leader of each of the follower's samples, every 2 m; else null.
 */
const besideDeck = (follower: DeckLine, leader: DeckLine): number[] | null => {
  const n = Math.max(2, Math.ceil(follower.total / 2) + 1)
  const at: number[] = []
  for (let k = 0; k < n; k++) {
    const p = alongLine(leader.pts, leader.cum, deckPointAt(follower, (follower.total * k) / (n - 1)))
    if (p.off > DECK_GROUP_REACH) return null
    at.push(p.s)
  }
  // Running the same way along it: the follower's length shows up as about as much of the
  // leader's (a way that crosses it, or turns off it, does not).
  const run = Math.abs(at[at.length - 1] - at[0])
  if (run < follower.total * 0.8) return null
  const dir = Math.sign(at[at.length - 1] - at[0])
  for (let k = 1; k < at.length; k++) if ((at[k] - at[k - 1]) * dir < -0.5) return null
  return at
}

/**
 * Parallel bridge ways of one street are one deck. OSM maps a street's carriageways and its
 * sidewalks or cycle tracks as ways of their own, side by side, and each would get a profile of
 * its own: a sidewalk sitting lower beside its street, or a divided street as a cluster of
 * tilted slabs. A footway, path or cycleway bridge that runs beside a street's bridge its whole
 * length (within `DECK_GROUP_REACH`, the same way along), and a carriageway beside a longer one
 * of the same street (same name, kind and layer), take that bridge's heights wherever they lie
 * beside it. Then a bridge way shorter than `SHORT_DECK` that shares a node with a longer deck is
 * drawn level, at that deck's height at the node.
 */
export const groupDecks = (chains: readonly BridgeChain[], lines: readonly DeckLine[]): DeckLine[] => {
  const out = lines.slice()
  const follows = new Map<number, number>()
  const road = (c: BridgeChain) => !isRail(c.line.tags) && !isPath(c.line.tags) && roadWidth(c.line.tags) !== null
  const layer = (c: BridgeChain) => c.line.tags.layer ?? '1'
  const byLength = chains.map((_, i) => i).sort((a, b) => lines[b].total - lines[a].total)
  const follow = (i: number, leader: number, at: readonly number[]) => {
    const l = out[leader]
    const own = lines[i]
    const n = at.length
    const zs = at.map((s) => l.zAt(Math.max(0, Math.min(l.total, s))))
    const zAt = (s: number) => {
      const f = Math.max(0, Math.min(n - 1, (s / Math.max(1e-9, own.total)) * (n - 1)))
      const k = Math.min(n - 2, Math.floor(f))
      return zs[k] + (zs[k + 1] - zs[k]) * (f - k)
    }
    out[i] = { ...own, zAt, startLevel: zs[0], endLevel: zs[n - 1] }
    follows.set(i, leader)
  }
  // The nearest longer deck it runs beside; a street before a ramp (`*_link`) beside it. A deck
  // that itself follows another can lead a shorter one: it is longer, so no loop can form.
  const nearest = (i: number, ok: (j: number) => boolean) => {
    let best: { j: number; at: number[]; off: number } | null = null
    const link = (j: number) => ((chains[j].line.tags.highway ?? '').endsWith('_link') ? 1 : 0)
    for (const j of byLength) {
      if (j === i || lines[j].total <= lines[i].total || !ok(j)) continue
      const at = besideDeck(lines[i], lines[j])
      if (at === null) continue
      const off = alongLine(lines[j].pts, lines[j].cum, deckPointAt(lines[i], lines[i].total / 2)).off + link(j) * DECK_GROUP_REACH
      if (best === null || off < best.off) best = { j, at, off }
    }
    return best
  }
  // The other half of a divided street follows the longer half.
  for (const i of byLength) {
    const c = chains[i]
    if (!road(c) || (c.line.tags.name ?? '') === '') continue
    const b = nearest(i, (j) => road(chains[j]) && layer(chains[j]) === layer(c) && chains[j].line.tags.highway === c.line.tags.highway && chains[j].names.includes(c.line.tags.name!.toLowerCase()))
    if (b !== null) follow(i, b.j, b.at)
  }
  // Sidewalks and cycle tracks follow the street they run beside.
  for (const i of byLength) {
    const c = chains[i]
    if (!isPath(c.line.tags) || isRail(c.line.tags)) continue
    const b = nearest(i, (j) => road(chains[j]) && layer(chains[j]) === layer(c))
    if (b !== null) follow(i, b.j, b.at)
  }
  // A short way that touches a longer deck is level with it there.
  const keys = chains.map((c) => c.line.points.map(key))
  const nodeOf = new Map<string, number[]>()
  keys.forEach((ks, i) => ks.forEach((k) => nodeOf.set(k, [...(nodeOf.get(k) ?? []), i])))
  for (let i = 0; i < chains.length; i++) {
    if (follows.has(i) || lines[i].total >= SHORT_DECK) continue
    let best: { j: number; z: number } | null = null
    for (const k of [keys[i][0], keys[i][keys[i].length - 1]]) {
      for (const j of nodeOf.get(k) ?? []) {
        if (j === i || lines[j].total <= lines[i].total) continue
        if (best !== null && lines[j].total <= lines[best.j].total) continue
        const v = keys[j].indexOf(k)
        best = { j, z: out[j].zAt(out[j].cum[v]) }
      }
    }
    if (best === null) continue
    const z = best.z
    out[i] = { ...lines[i], zAt: () => z, startLevel: z, endLevel: z }
  }
  return out
}

/** A chain's deck line: its points and lengths, view meters, and the deck's height along it. */
interface DeckLine {
  readonly pts: Vec2[]
  readonly cum: number[]
  readonly total: number
  readonly zAt: (s: number) => number
  readonly startLevel: number
  readonly endLevel: number
}

/**
 * The deck line of a chain. A grounded end sits on its abutment; an end that joins another
 * bridge is at `fix` where given (the height of the deck it joins), else at its clearance.
 */
const deckLine = (
  view: View, region: Region, terrain: Terrain, chain: BridgeChain, ends: BridgeEnds,
  fix: { start?: number; end?: number } = {},
): DeckLine => {
  const deck = deckHeight(region, chain)
  const pts = chain.line.points.map(([lon, lat]) => view.toView(lon, lat))
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
  // A grounded end sits on its abutment. An overpass mapped rim to rim over a cut ends on the
  // cut's sloping sides in a smoothed ground model while its street runs on at the rim: where
  // the ground past the end climbs and then levels off within `ABUTMENT_REACH`, the end sits at
  // that level. Where it goes on climbing (a ramp landing on a hillside), it sits on the ground.
  const seat = (end: 0 | 1): number => {
    const [p, q] = end === 0 ? [pts[0], pts[1]] : [pts[pts.length - 1], pts[pts.length - 2]]
    return abutmentLevel((t) => {
      const len = Math.max(1e-6, Math.hypot(p[0] - q[0], p[1] - q[1]))
      return terrain.z([p[0] + ((p[0] - q[0]) * t) / len, p[1] + ((p[1] - q[1]) * t) / len])
    })
  }
  const startLevel = chain.rampStart ? seat(0) : fix.start ?? ground(0) + ends.start
  const endLevel = chain.rampEnd ? seat(1) : fix.end ?? ground(total) + ends.end
  // A joined end's own clearance is what the deck it joins gives it.
  const c0 = chain.rampStart ? ends.start : startLevel - ground(0)
  const c1 = chain.rampEnd ? ends.end : endLevel - ground(total)
  const zAt = deckProfile(total, ground, (s) => rampClearance(deck, total, s, toGroundAt(ends, cum, s), c0, c1), startLevel, endLevel)
  return { pts, cum, total, zAt, startLevel, endLevel }
}

const bridgePieces = (
  view: View, pal: Palette, region: Region, terrain: Terrain, chain: BridgeChain,
  dl: DeckLine, roofs: readonly Roof[] = [], towers?: readonly Tower[],
): Item[] => {
  const spacing = pierSpacing(region, chain)
  const line = chain.line
  const t = line.tags
  const rail = isRail(t)
  const width = deckWidth(t)
  const { pts, cum, zAt } = dl
  const items: Item[] = []
  let traveled = 0
  let nextPier = spacing / 2
  for (let i = 0; i + 1 < pts.length; i++) {
    const a = pts[i]
    const b = pts[i + 1]
    const len = Math.hypot(b[0] - a[0], b[1] - a[1])
    const n = Math.max(1, Math.ceil(len / PIECE))
    for (let k = 0; k < n; k++) {
      const s0 = traveled + (len * k) / n
      const s1 = traveled + (len * (k + 1)) / n
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
      // A span inside a building, below its roof (a garage ramp, a skyway's landing), is hidden
      // by it; drawn, it would cut through the walls and roof.
      const host = buildingAt(roofs, [(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2])
      if (host !== null && host.base <= Math.max(z0, z1) && host.top >= Math.max(z0, z1)) {
        while (nextPier <= s1) nextPier += spacing
        continue
      }
      const shapes: Shape[] = []
      // Piers: they stand behind the fascia.
      while (nextPier <= s1) {
        const u = (nextPier - s0) / Math.max(1e-6, s1 - s0)
        const pz = z0 + (z1 - z0) * u
        const c0: Vec2 = [p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u]
        // A pier over a building stands on its roof, not down through it.
        const below = buildingAt(roofs, c0)
        const footZ = Math.max(terrain.z(c0), below !== null && below.base < pz ? below.top : -Infinity)
        if (pz - footZ > 3) {
          const c: Vec2 = [p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u]
          const dx = (p1[0] - p0[0]) / Math.max(1e-6, s1 - s0)
          const dy = (p1[1] - p0[1]) / Math.max(1e-6, s1 - s0)
          const half = width / 2 - 0.6
          const l: Vec2 = [c[0] - dy * half, c[1] + dx * half]
          const r: Vec2 = [c[0] + dy * half, c[1] - dx * half]
          // Each pier is an item of its own, so it takes its place behind a building nearer
          // the camera even where the deck above passes over that building's edge.
          const foot = segmentQuad(l, r, 0.4, 0.4)
          if (foot !== null) {
            items.push({
              id: `${line.id}.${i}.${k}.pier${items.length}`,
              kind: 'bridge',
              hull: convexHull(foot),
              zMin: footZ,
              zMax: Math.min(z0, z1) - FASCIA,
              key: c[1],
              shapes: [{ pts: [view.toScreen(l, footZ), view.toScreen(r, footZ), view.toScreen(r, pz - FASCIA), view.toScreen(l, pz - FASCIA)], fill: pal.pier, ink: true }],
              dots: [],
              pier: true,
            })
          }
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
        // Where the deck meets the ground the fascia stops at it, so a ramp lands as a ramp and
        // not as a slab cut off square.
        const lo0 = view.toScreen(u0, Math.min(zu0, Math.max(zu0 - FASCIA, terrain.z(u0))))
        const lo1 = view.toScreen(u1, Math.min(zu1, Math.max(zu1 - FASCIA, terrain.z(u1))))
        const hi0 = view.toScreen(u0, zu0)
        const hi1 = view.toScreen(u1, zu1)
        // Filled and sealed, but inked only along its length: a span is one bridge, not a
        // stack of 22-meter slabs.
        shapes.push({ pts: [lo0, lo1, hi1, hi0], fill: pal.fascia, seal: true })
        shapes.push({ pts: [lo0, lo1], fill: 'none', line: true })
      }
      // An abutment: where a grounded end stands over lower ground, a wall down to it, seen
      // when the end faces the camera.
      for (const [at, zEnd, l, r, out] of [
        [i === 0 && k === 0 && chain.rampStart, z0, ql0, qr0, [p0[0] - p1[0], p0[1] - p1[1]]],
        [i === pts.length - 2 && k === n - 1 && chain.rampEnd, z1, qr1, ql1, [p1[0] - p0[0], p1[1] - p0[1]]],
      ] as const) {
        if (!at || out[1] >= 0) continue
        const gl = terrain.z(l)
        const gr = terrain.z(r)
        if (zEnd - Math.min(gl, gr) <= FASCIA) continue
        shapes.push({ pts: [view.toScreen(l, Math.min(gl, zEnd)), view.toScreen(r, Math.min(gr, zEnd)), view.toScreen(r, zEnd), view.toScreen(l, zEnd)], fill: pal.fascia, ink: true })
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
        // The deck's underside: a span over another span or a pier is in front of it.
        zMin: Math.min(z0, z1) - FASCIA,
        zMax: Math.max(z0, z1),
        key: (p0[1] + p1[1]) / 2,
        shapes,
        dots: [],
        ...(t.name === undefined ? {} : { name: t.name }),
        span: { a: p0, b: p1, z: (z0 + z1) / 2, bridge: line.id },
      })
    }
    traveled += len
  }
  if (towers !== undefined) items.push(...cablePieces(view, line.id, pts, cum, zAt, towers))
  return items
}

/** A suspension bridge's two main cables, cut into pieces like its deck. */
const cablePieces = (
  view: View, id: string, pts: readonly Vec2[], cum: readonly number[], zAt: (s: number) => number, towers: readonly Tower[],
): Item[] => {
  const total = cum[cum.length - 1]
  const at = (s: number): { p: Vec2; n: Vec2 } => {
    let i = 1
    while (i < cum.length - 1 && cum[i] < s) i++
    const len = Math.max(1e-9, cum[i] - cum[i - 1])
    const u = (s - cum[i - 1]) / len
    const dx = (pts[i][0] - pts[i - 1][0]) / len
    const dy = (pts[i][1] - pts[i - 1][1]) / len
    return { p: [pts[i - 1][0] + dx * len * u, pts[i - 1][1] + dy * len * u], n: [-dy, dx] }
  }
  const items: Item[] = []
  for (const side of [0, 1]) {
    const legs = towers.map((t) => ({ s: t.s, ...(side === 0 ? (t.legs[0].d > t.legs[1].d ? t.legs[0] : t.legs[1]) : (t.legs[0].d > t.legs[1].d ? t.legs[1] : t.legs[0])) }))
    const d = legs.reduce((a, l) => a + l.d, 0) / legs.length
    const n = Math.max(2, Math.ceil(total / PIECE))
    for (let k = 0; k < n; k++) {
      const s0 = (total * k) / n
      const s1 = (total * (k + 1)) / n
      const a = at(s0)
      const b = at(s1)
      const q0: Vec2 = [a.p[0] + a.n[0] * d, a.p[1] + a.n[1] * d]
      const q1: Vec2 = [b.p[0] + b.n[0] * d, b.p[1] + b.n[1] * d]
      if (!insideRect(q0, view.frame) || !insideRect(q1, view.frame)) continue
      const c0 = cableZ(s0, total, legs, zAt)
      const c1 = cableZ(s1, total, legs, zAt)
      const quad = segmentQuad(q0, q1, 0.5, 0.5)
      if (quad === null) continue
      items.push({
        id: `${id}.cable${side}.${k}`,
        kind: 'bridge',
        hull: convexHull(quad),
        zMin: Math.min(zAt(s0), zAt(s1)),
        zMax: Math.max(c0, c1),
        key: (q0[1] + q1[1]) / 2,
        shapes: [{ pts: [view.toScreen(q0, c0), view.toScreen(q1, c1)], fill: 'none', line: true }],
        dots: [],
      })
    }
  }
  return items
}

/** Is this view-meter point on open water (inside water, outside every island)? */
export const onWater = (scene: Scene, p: Vec2): boolean => {
  let wet = false
  for (const g of scene.ground) {
    if (g.kind === 'water' && pointInPolygon(p, g.rings)) wet = true
  }
  if (!wet) return false
  for (const g of scene.ground) if (g.kind === 'island' && pointInPolygon(p, g.rings)) return false
  return true
}
