/**
 * A cutaway in a scene: a modeled building's parts turned into solids, cut at the region's
 * plane, and made into items; the boxes of its trains and canopies lifted where asked; and the
 * dashed outline of what was taken away. With `section`, the same parts cut for the flat
 * section instead: nothing in front of the plane, and only so far behind it.
 */

import { centroid, convexHull, pointInRing, type Ring, type Vec2 } from './geom.ts'
import type { HistoryFeature, PartTone } from './history.ts'
import type { Palette } from './palette.ts'
import { boxItem, domeProfile, STOCK, toned, type Box } from './parts.ts'
import type { Cutaway } from './region.ts'
import type { Item, Shape } from './scene.ts'
import type { View } from './view.ts'
import { travelerShapes } from './traveler.ts'
import {
  above, behind, below, clipAll, corners, clipSolid, cutPlane, sweep, type FaceRole, type Vec3, isConvex, prism, revolve, sectionOf, sideOf, solidItem, splitSolids, stair, unionOutline, within,
  type CutPlane, type Solid, type Tones,
} from './cutaway.ts'

/** A modeled part placed in the view: its outline, bottom and top. */
export interface PlacedPart {
  readonly h: HistoryFeature; readonly outer: Ring; readonly seat: number; readonly top: number
  /** A hip piece's whole roof (`roofRing`), in view meters, counter-clockwise. */
  readonly roof?: Ring
}

/** The solids a placed part is made of. Non-convex prisms are drawn on their convex hull. */
export const partSolids = (p: PlacedPart): { solids: Solid[]; hulled: boolean } => {
  const { h, outer, seat, top } = p
  if (h.shape === 'revolve' && h.levels !== undefined) {
    return { solids: revolve(outer, h.levels.map(([z, o, i]) => ({ z: seat + z, outer: o, inner: i }))), hulled: false }
  }
  if (h.shape === 'dome') {
    const steps = 10
    const levels = Array.from({ length: steps + 1 }, (_, k) => ({ z: seat + ((top - seat) * k) / steps, outer: domeProfile(k / steps), inner: 0 }))
    return { solids: revolve(outer, levels), hulled: false }
  }
  if (h.shape === 'arch') {
    // A window or opening on the ring's first edge (its span), as thick as the second, rising
    // to a half ellipse `top − seat` high.
    const [p0, p1, p2] = outer
    const span = Math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    const thick = Math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    const u: Vec2 = [(p1[0] - p0[0]) / span, (p1[1] - p0[1]) / span]
    const w: Vec2 = [(p2[0] - p1[0]) / thick, (p2[1] - p1[1]) / thick]
    const n = 16
    const profile: Vec2[] = [[0, seat], [span, seat]]
    for (let i = 1; i < n; i++) {
      const x = span * (1 - i / n)
      const v = (x - span / 2) / (span / 2)
      profile.push([x, seat + (top - seat) * Math.sqrt(Math.max(0, 1 - v * v))])
    }
    return { solids: [sweep(profile, p0, u, w, 0, thick)], hulled: false }
  }
  if (h.shape === 'disc') {
    // A disc standing on the ring's first edge (its diameter), as thick as the second: a clock
    // face. Its height is `top − seat`; the ring's corners are kept in order (see placed parts).
    const [p0, p1, p2] = outer
    const span = Math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    const thick = Math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    const u: Vec2 = [(p1[0] - p0[0]) / span, (p1[1] - p0[1]) / span]
    const w: Vec2 = [(p2[0] - p1[0]) / thick, (p2[1] - p1[1]) / thick]
    const n = 20
    const profile: Vec2[] = Array.from({ length: n }, (_, k): Vec2 => [span / 2 + (span / 2) * Math.cos((2 * Math.PI * k) / n), (seat + top) / 2 + ((top - seat) / 2) * Math.sin((2 * Math.PI * k) / n)])
    return { solids: [sweep(profile, p0, u, w, 0, thick)], hulled: false }
  }
  if (h.shape === 'stair') return { solids: stair(outer, seat, top, h.steps ?? 12), hulled: false }
  if (h.shape === 'hip' && p.roof !== undefined && isConvex(p.roof) && isConvex(outer)) return { solids: [roofPiece(p.roof, outer, seat, top)], hulled: false }
  if ((h.shape === 'hip' || h.shape === 'gable') && isConvex(outer)) return { solids: [roofSolid(outer, seat, top, h.shape)], hulled: false }
  if (isConvex(outer)) return { solids: [prism(outer, seat, top)], hulled: false }
  return { solids: [prism(convexHull(outer), seat, top)], hulled: true }
}

/**
 * A roof on a convex ring (view meters, counter-clockwise), from `seat` at its eaves to a ridge
 * at `top`: a prism cut by a plane rising inward from each eave. A `hip` rises from every edge
 * at the pitch that brings its narrowest width to the ridge; a `gable` from its first and third
 * edges only, at the pitch that meets midway between them.
 */
export const roofSolid = (ring: readonly Vec2[], seat: number, top: number, kind: 'hip' | 'gable'): Solid => {
  const n = ring.length
  const inward = (i: number) => {
    const a = ring[i], b = ring[(i + 1) % n]
    const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
    return { a, nx: -(b[1] - a[1]) / l, ny: (b[0] - a[0]) / l }
  }
  // The width across from an edge: the farthest corner inward of it.
  const across = (i: number) => {
    const { a, nx, ny } = inward(i)
    return Math.max(...ring.map((p) => (p[0] - a[0]) * nx + (p[1] - a[1]) * ny))
  }
  const eaves = kind === 'hip' ? ring.map((_, i) => i) : [0, 2].filter((i) => i < n)
  const half = Math.min(...eaves.map(across)) / 2
  const slope = (top - seat) / Math.max(half, 1e-6)
  let s: Solid | null = prism(ring, seat, top)
  for (const i of eaves) {
    if (s === null) break
    const { a, nx, ny } = inward(i)
    // z − slope · (inward distance from the eave) ≤ seat.
    s = clipSolid(s, { n: [-slope * nx, -slope * ny, 1], d: seat - slope * (a[0] * nx + a[1] * ny) })
  }
  if (s === null) return prism(ring, seat, top)
  return { faces: s.faces.map((f) => (f.role === 'cut' ? { pts: f.pts, role: 'side' as const } : f)) }
}

/**
 * A piece of the hipped roof on `whole` (convex, counter-clockwise): the whole roof's solid, cut
 * to the piece's own ring `piece` by a wall standing on each of its edges.
 */
export const roofPiece = (whole: readonly Vec2[], piece: readonly Vec2[], seat: number, top: number): Solid => {
  let s: Solid | null = roofSolid(whole, seat, top, 'hip')
  const n = piece.length
  for (let i = 0; i < n && s !== null; i++) {
    const a = piece[i], b = piece[(i + 1) % n]
    const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
    const nx = -(b[1] - a[1]) / l, ny = (b[0] - a[0]) / l
    // Keep the inward side: (p − a) · n ≥ 0.
    s = clipSolid(s, { n: [-nx, -ny, 0], d: -(a[0] * nx + a[1] * ny) })
  }
  if (s === null) return prism(piece, seat, seat + 0.01)
  return { faces: s.faces.map((f) => (f.role === 'cut' ? { pts: f.pts, role: 'side' as const } : f)) }
}

/** The tones a modeled part is drawn in, its inside (a dome's ceiling) in plaster. */
export const partTones = (pal: Palette, h: HistoryFeature): Tones => {
  const [lit, shade, roof] = pal.parts[h.tone ?? 'stone']
  const [il, is] = pal.parts.plaster
  return { lit, shade, roof, cut: pal.poche, inner: [il, is] }
}

const boxTones = (pal: Palette, b: Box): Tones => {
  const [lit, shade, roof] = pal.parts[b.tone]
  return { lit, shade, roof, cut: pal.poche }
}

export interface CutawayResult {
  readonly items: Item[]
  readonly plane: CutPlane
  readonly stats: Record<string, number>
  /** In a section: every cut face of the cut parts, in plane coordinates (s, z). */
  readonly sections: Vec2[][]
}

/**
 * Cut the parts and boxes of a scene. `keepZ` is the scene height up to which the removed side
 * stands (undefined: nothing). `outlineRings` are footprints whose removed side is outlined,
 * dashed, on the ground (`ground`).
 */
export const cutawayItems = (
  view: View, pal: Palette, cut: Cutaway, parts: readonly PlacedPart[], boxes: readonly Box[],
  opts: { keepZ?: number; floorZ?: number; section?: boolean; outlineRings?: readonly Ring[]; ground: (p: Vec2) => number },
): CutawayResult => {
  const through = view.toView(cut.through[0], cut.through[1])
  const plane = cutPlane(through, cut.bearing, view.bearing, cut.remove)
  const prefix = cut.parts ?? ''
  const lift = (cut.lift ?? []).map((r) => new RegExp(r))
  const items: Item[] = []
  const sections: Vec2[][] = []
  const stats: Record<string, number> = { cutParts: 0, keptParts: 0, cutHulled: 0, lifted: 0 }
  // Footprints of what still stands on the removed side (its low walls), where the dashed
  // outline would only repeat them.
  const standing: Ring[] = []
  const beyond = cut.section?.beyond ?? 35
  const other = cut.section?.other ?? 2
  for (const p of parts) {
    const { solids, hulled } = partSolids(p)
    if (hulled) stats.cutHulled++
    const tones = partTones(pal, p.h)
    const id = `history:${p.h.id}`
    const subject = p.h.id.startsWith(prefix)
    if (opts.section) {
      // A flight down from the floor on the side lifted away (a stair to the platforms) is
      // drawn as its profile, dashed, on the plane.
      if (subject && p.h.shape === 'stair' && p.top <= (opts.floorZ ?? Infinity) + 0.05 && p.outer.every((q) => sideOf(plane, q) > 0) && Math.min(...p.outer.map((q) => sideOf(plane, q))) < beyond) {
        items.push(stairProfile(view, pal, plane, id, p))
        continue
      }
      if (subject) for (const s of solids) {
        const sec = sectionOf(s, plane)
        if (sec !== null) sections.push(sec)
      }
      const kept = solids.map((s) => clipAll(s, [behind(plane), within(plane, subject ? beyond : other)])).filter((s): s is Solid => s !== null)
      const it = solidItem(view, tones, id, kept, p.h.name)
      if (it !== null) items.push(it)
      continue
    }
    if (!subject) {
      const it = solidItem(view, tones, id, solids, p.h.name)
      if (it !== null) items.push(it)
      stats.keptParts++
      continue
    }
    stats.cutParts++
    const { back, front } = splitSolids(solids, plane, opts.keepZ)
    for (const x of front) {
      const c = corners(x)
      const zs = c.map((q) => q[2])
      if (Math.max(...zs) - Math.min(...zs) > 0.3) standing.push(convexHull(c.map((q): Vec2 => [q[0], q[1]])))
    }
    // A part that runs through the floor is drawn as two items, above and below it, so it
    // takes its place in the paint order on each side of the floor's slab.
    for (const [list, suffix] of [[back, ''], [front, ':near']] as const) {
      const parts = opts.floorZ === undefined ? [{ s: list, tag: '' }] : [
        { s: list.map((x) => clipSolid(x, below(opts.floorZ!))).filter((x): x is Solid => x !== null), tag: ':base' },
        { s: list.map((x) => clipSolid(x, above(opts.floorZ!))).filter((x): x is Solid => x !== null), tag: '' },
      ]
      for (const { s, tag } of parts) {
        const it = solidItem(view, tones, `${id}${suffix}${tag}`, s, p.h.name)
        if (it !== null) items.push(it)
      }
    }
  }
  // In the flat section, trains and sheds are drawn as flat end elevations where their tracks
  // and platforms meet the plane, not as boxes cut on the skew.
  if (opts.section) items.push(...flatElevations(view, pal, plane, boxes, other))
  for (const b of boxes) {
    if (opts.section && (b.front !== undefined || isShed(b))) continue
    if (!opts.section && lift.some((r) => r.test(b.id))) {
      stats.lifted++
      continue
    }
    // Long boxes (a car, a run of canopy) are cut into short pieces, so each piece takes its
    // own place among the stairs and the concourse it passes; each is drawn in its own shape
    // (a car's body and roof, an engine's boiler, a shed's butterfly roof) without seams.
    const pieces = shortPieces(b)
    const coupled = isCoupled(b, boxes)
    pieces.forEach((piece, k) => {
      const parts = shaped(pal, b, piece, k, pieces.length, coupled)
      const solids: Solid[] = []
      const id = pieces.length === 1 ? b.id : piece.id
      for (const part of parts) {
        const kept = opts.section ? clipAll(part.solid, [behind(plane), within(plane, other)]) : part.solid
        if (kept === null) continue
        // In the flat section a train or a shed is drawn in its own colors where the plane
        // cuts it, so it reads as a car end or a shed's profile, not as a solid wall.
        const tones = opts.section ? { ...part.tones, cut: part.tones.lit } : part.tones
        const it = solidItem(view, tones, `${id}${part.suffix}`, [kept], undefined, parts.joint)
        if (it !== null) items.push(it)
        solids.push(kept)
      }
    })
  }
  if (!opts.section && opts.outlineRings !== undefined && opts.outlineRings.length > 0) {
    let k = 0
    for (const [a, b] of unionOutline(opts.outlineRings)) {
      for (const [p, q] of removedPieces(plane, a, b)) {
        const len = Math.hypot(q[0] - p[0], q[1] - p[1])
        const n = Math.max(1, Math.ceil(len / OUTLINE_PIECE))
        for (let i = 0; i < n; i++) {
          const s0: Vec2 = [p[0] + ((q[0] - p[0]) * i) / n, p[1] + ((q[1] - p[1]) * i) / n]
          const s1: Vec2 = [p[0] + ((q[0] - p[0]) * (i + 1)) / n, p[1] + ((q[1] - p[1]) * (i + 1)) / n]
          if (standing.some((h) => distanceToRing([(s0[0] + s1[0]) / 2, (s0[1] + s1[1]) / 2], h) < OUTLINE_CLEAR)) continue
          items.push(outlineItem(view, pal, `cut-outline:${k++}`, s0, s1, opts.ground))
        }
      }
    }
    stats.outlinePieces = k
  }
  return { items, plane, stats, sections }
}

/** Dashed outline pieces are this long at most, so each sorts among what stands near it. */
export const OUTLINE_PIECE = 4
/** The outline is left out within this many meters of a low wall still standing. */
export const OUTLINE_CLEAR = 2.5

/** Distance from a point to a convex ring: 0 inside it. */
export const distanceToRing = (p: Vec2, ring: readonly Vec2[]): number => {
  if (ring.length >= 3 && pointInRing(p, ring)) return 0
  let best = Infinity
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i]
    const b = ring[(i + 1) % ring.length]
    const dx = b[0] - a[0]
    const dy = b[1] - a[1]
    const l2 = dx * dx + dy * dy || 1
    const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    best = Math.min(best, Math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dy * t))
  }
  return best
}

/** The part of segment a–b on the removed side of the plane, not on the plane itself. */
const removedPieces = (pl: CutPlane, a: Vec2, b: Vec2): [Vec2, Vec2][] => {
  const da = sideOf(pl, a)
  const db = sideOf(pl, b)
  if (da <= 0.05 && db <= 0.05) return []
  if (da >= 0 && db >= 0) return [[a, b]]
  const t = da / (da - db)
  const m: Vec2 = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
  return da > 0 ? [[a, m]] : [[m, b]]
}

const outlineItem = (view: View, pal: Palette, id: string, a: Vec2, b: Vec2, ground: (p: Vec2) => number): Item => {
  const za = ground(a) + 0.05
  const zb = ground(b) + 0.05
  const dx = b[0] - a[0]
  const dy = b[1] - a[1]
  const l = Math.hypot(dx, dy) || 1
  const nx = (-dy / l) * 0.05
  const ny = (dx / l) * 0.05
  return {
    id,
    kind: 'building',
    hull: [[a[0] - nx, a[1] - ny], [b[0] - nx, b[1] - ny], [b[0] + nx, b[1] + ny], [a[0] + nx, a[1] + ny]],
    zMin: Math.min(za, zb),
    zMax: Math.max(za, zb),
    key: (a[1] + b[1]) / 2,
    shapes: [{ pts: [view.toScreen(a, za), view.toScreen(b, zb)], fill: 'none', line: true, stroke: { color: pal.cutOutline, width: pal.lineWidth * 2, dash: pal.cutOutlineDash } }],
    dots: [],
  }
}

/** Boxes are cut into pieces no longer than this, in cutaways. */
export const BOX_PIECE = 7

/** A box's pieces along its first edge, each at most `BOX_PIECE` long (the box itself if short). */
export const shortPieces = (b: Box): Box[] => {
  const [p0, p1, p2, p3] = b.ring
  if (b.ring.length !== 4) return [b]
  const len = Math.hypot(p1[0] - p0[0], p1[1] - p0[1])
  const n = Math.ceil(len / BOX_PIECE - 1e-9)
  if (n <= 1) return [b]
  const at = (a: Vec2, c: Vec2, t: number): Vec2 => [a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t]
  return Array.from({ length: n }, (_, k) => ({
    ...b,
    id: `${b.id}/${k}`,
    ring: [at(p0, p1, k / n), at(p0, p1, (k + 1) / n), at(p3, p2, (k + 1) / n), at(p3, p2, k / n)],
  }))
}

/** Whether a car has another car (or the tender) just ahead of it, in the gap before its front. */
export const isCoupled = (b: Box, boxes: readonly Box[]): boolean => {
  if (b.front === undefined) return false
  const c = centroid(b.ring)
  const half = Math.max(...b.ring.map((q) => (q[0] - c[0]) * b.front![0] + (q[1] - c[1]) * b.front![1]))
  const probe: Vec2 = [c[0] + b.front[0] * (half + STOCK.gap + 0.5), c[1] + b.front[1] * (half + STOCK.gap + 0.5)]
  return boxes.some((o) => o !== b && o.front !== undefined && pointInRing(probe, o.ring))
}

/** A part of a shaped box: a solid, its tones, and a suffix for its item's id. */
interface Shaped { readonly solid: Solid; readonly tones: Tones; readonly suffix: string }

/**
 * The solids a box is drawn as in a cutaway, for piece `k` of `n`: a coach's body with its
 * arched roof and a band of windows down each side; an engine's frame, boiler, dome and stack;
 * a tender; a shed's two roof slopes falling to a valley over its posts (a butterfly roof);
 * anything else as its box. `joint` tells the points on a joint with the next piece.
 */
const shaped = (pal: Palette, whole: Box, b: Box, k: number, n: number, coupled = false): Shaped[] & { joint?: (p: Vec3) => boolean } => {
  const [p0, p1, , p3] = b.ring
  const len = Math.hypot(p1[0] - p0[0], p1[1] - p0[1])
  const wid = Math.hypot(p3[0] - p0[0], p3[1] - p0[1])
  const w: Vec2 = [(p1[0] - p0[0]) / len, (p1[1] - p0[1]) / len]
  const u: Vec2 = [(p3[0] - p0[0]) / wid, (p3[1] - p0[1]) / wid]
  const origin: Vec2 = [(p0[0] + p3[0]) / 2, (p0[1] + p3[1]) / 2]
  const hw = wid / 2
  const [w0, w1] = [0, len]
  const total = len * n
  const off = len * k
  const ends: [FaceRole, FaceRole] = [k > 0 ? 'internal' : 'side', k + 1 < n ? 'internal' : 'side']
  const toneOf = (t: PartTone, roof?: string): Tones => {
    const [lit, shade, r] = pal.parts[t]
    return { lit, shade, roof: roof ?? r, cut: pal.poche }
  }
  const { z0, z1 } = b
  const H = z1 - z0
  const out: Shaped[] = []
  const add = (profile: Vec2[], t: Tones, suffix: string, a = w0, c = w1) => {
    if (c - a > 1e-6) out.push({ solid: sweep(profile, origin, u, w, a, c, [a > w0 ? 'side' : ends[0], c < w1 ? 'side' : ends[1]]), tones: t, suffix })
  }
  const within = (a: number, c: number): [number, number] => [Math.max(w0, a - off), Math.min(w1, c - off)]
  const isCab = whole.id.endsWith(':cab')
  // Rolling stock faces `front` (its engine leads); `at(d0, d1)` is the run from d0 to d1
  // meters behind the front, in this piece's own coordinates.
  const frontAtEnd = whole.front !== undefined && whole.front[0] * w[0] + whole.front[1] * w[1] > 0
  const at = (d0: number, d1: number): [number, number] => {
    const [g0, g1] = frontAtEnd ? [total - d1, total - d0] : [d0, d1]
    return within(g0, g1)
  }
  const ngon = (r: number, cz: number, k = 12): Vec2[] => Array.from({ length: k }, (_, i) => [r * Math.cos(Math.PI / k + (2 * i * Math.PI) / k), cz + r * Math.sin(Math.PI / k + (2 * i * Math.PI) / k)])
  const slab = (x: number, za: number, zb: number): Vec2[] => [[-x, za], [x, za], [x, zb], [-x, zb]]
  if (isCab) {
    // A cutaway draws the cab as part of its engine, at the engine's back end.
  } else if (whole.tone === 'coach') {
    // A heavyweight coach: a solid Pullman-green body, a darker arched roof, a continuous band
    // of windows down each side, and the vestibule's diaphragm in the gap ahead of it.
    const eave = z0 + 0.78 * H
    add(slab(hw, z0, eave), toneOf('coach'), '')
    add([[-hw, eave], [hw, eave], [hw * 0.82, z0 + 0.9 * H], [hw * 0.45, z0 + 0.98 * H], [0, z1], [-hw * 0.45, z0 + 0.98 * H], [-hw * 0.82, z0 + 0.9 * H]], toneOf('carRoof'), ':roof')
    const [a, c] = at(1.4, total - 1.4)
    for (const side of [1, -1]) {
      const x0 = side * hw
      const x1 = side * (hw + 0.05)
      add([[x0, z0 + 0.4 * H], [x1, z0 + 0.4 * H], [x1, z0 + 0.64 * H], [x0, z0 + 0.64 * H]], toneOf('glass'), side > 0 ? ':windows' : ':windows-b', a, c)
    }
    const gap = STOCK.gap
    if (coupled && !frontAtEnd && k === 0) add(slab(hw * 0.7, z0 + 0.3, z0 + 0.72 * H), toneOf('coal'), ':diaphragm', -gap, 0)
    if (coupled && frontAtEnd && k + 1 === n) add(slab(hw * 0.7, z0 + 0.3, z0 + 0.72 * H), toneOf('coal'), ':diaphragm', len, len + gap)
  } else if (whole.tone === 'freight') {
    add([[-hw, z0], [hw, z0], [hw, z0 + 0.8 * H], [hw * 0.55, z0 + 0.96 * H], [0, z1], [-hw * 0.55, z0 + 0.96 * H], [-hw, z0 + 0.8 * H]], toneOf('freight', pal.parts.roof[2]), '')
  } else if (whole.tone === 'engine' && total > 14) {
    // A steam engine, its smokebox to the front: the frame and running board, a round boiler
    // with its stack and domes, and the boxy cab at the back, next to the tender.
    const t = toneOf('loco')
    const cab = 4
    const cz = z0 + 2.35
    add(slab(hw * 0.8, z0, z0 + 1.25), t, '', ...at(0.3, total))
    add(slab(hw, z0 + 1.25, z0 + 1.4), t, ':board', ...at(0.6, total - cab))
    add(ngon(1.02, cz), toneOf('coal'), ':smokebox', ...at(0.4, 2.6))
    add(ngon(0.98, cz), t, ':boiler', ...at(2.6, total - cab))
    add(slab(0.32, cz, z0 + 4.0), toneOf('coal'), ':stack', ...at(1.1, 1.8))
    add(slab(0.45, cz, z0 + 3.7), t, ':dome', ...at(6.4, 7.5))
    add(slab(0.4, cz, z0 + 3.6), t, ':sand', ...at(9.2, 10.1))
    add(slab(hw, z0 + 1.25, z0 + 3.65), t, ':cab', ...at(total - cab, total))
    add([[-hw - 0.12, z0 + 3.65], [hw + 0.12, z0 + 3.65], [hw * 0.6, z0 + 3.95], [-hw * 0.6, z0 + 3.95]], toneOf('coal'), ':cab-roof', ...at(total - cab - 0.1, total + 0.1))
    for (const side of [1, -1]) {
      add([[side * hw, z0 + 2.45], [side * (hw + 0.05), z0 + 2.45], [side * (hw + 0.05), z0 + 3.25], [side * hw, z0 + 3.25]], toneOf('glass'), side > 0 ? ':cab-window' : ':cab-window-b', ...at(total - cab + 0.6, total - 1.4))
    }
  } else if (whole.tone === 'engine') {
    // A tender: a low tank, lower than the cab, and its coal heaped at the front.
    add(slab(hw, z0, z0 + 2.5), toneOf('loco'), '')
    add([[-hw * 0.85, z0 + 2.5], [hw * 0.85, z0 + 2.5], [hw * 0.5, z0 + 3.05], [-hw * 0.5, z0 + 3.05]], toneOf('coal'), ':coal', ...at(0.4, total * 0.62))
  } else if (whole.tone === 'iron' && !whole.id.includes(':post:') && H < 1.5) {
    const t = toneOf('iron')
    add([[-hw, z1], [-hw, z1 - 0.25], [0, z1 - 0.85], [0, z1 - 0.6]], t, '')
    add([[0, z1 - 0.6], [0, z1 - 0.85], [hw, z1 - 0.25], [hw, z1]], t, ':b')
  } else {
    add([[-hw, z0], [hw, z0], [hw, z1], [-hw, z1]], toneOf(whole.tone), '')
  }
  const res = out as Shaped[] & { joint?: (p: Vec3) => boolean }
  if (n > 1) {
    res.joint = (q: Vec3) => {
      const t = (q[0] - origin[0]) * w[0] + (q[1] - origin[1]) * w[1]
      return (k > 0 && Math.abs(t - w0) < 1e-6) || (k + 1 < n && Math.abs(t - w1) < 1e-6)
    }
  }
  return res
}

/** A box of a platform shed: its roof or one of its posts. */
export const isShed = (b: Box): boolean => b.tone === 'iron' && /canopy/.test(b.id)

/** A box's length direction, half length and half width. */
const frameOf = (b: Box): { c: Vec2; w: Vec2; hl: number; hw: number } => {
  const [p0, p1, , p3] = b.ring
  const len = Math.hypot(p1[0] - p0[0], p1[1] - p0[1])
  const wid = Math.hypot(p3[0] - p0[0], p3[1] - p0[1])
  return { c: centroid(b.ring), w: [(p1[0] - p0[0]) / len, (p1[1] - p0[1]) / len], hl: len / 2, hw: wid / 2 }
}

/**
 * The flat section's trains and sheds: for each track with a train standing across the plane
 * or within `depth` behind it, one car's end (or the engine's front, or a tender's end) drawn
 * square on, true size, on its rails where the track meets the plane; for each shed there, its
 * butterfly profile: a center post and two wings rising outward.
 */
export const flatElevations = (view: View, pal: Palette, pl: CutPlane, boxes: readonly Box[], depth: number): Item[] => {
  const items: Item[] = []
  const reach = (b: Box) => {
    const d = b.ring.map((q) => sideOf(pl, q))
    return { lo: Math.min(...d), hi: Math.max(...d) }
  }
  const near = (b: Box) => { const r = reach(b); return r.hi >= -depth && r.lo <= 0 }
  // Where a box's axis meets the plane, as meters along it, and the point there.
  const meet = (b: Box): { s: number; q: Vec2 } | null => {
    const { c, w } = frameOf(b)
    const nw = w[0] * pl.n[0] + w[1] * pl.n[1]
    if (Math.abs(nw) < 0.05) return null
    const t = -sideOf(pl, c) / nw
    const q: Vec2 = [c[0] + w[0] * t, c[1] + w[1] * t]
    return { s: (q[0] - pl.p[0]) * pl.u[0] + (q[1] - pl.p[1]) * pl.u[1], q }
  }
  const toned3 = (t: PartTone): [string, string, string] => [...pal.parts[t]] as [string, string, string]
  const flat = (id: string, q: Vec2, polys: { pts: Vec2[]; fill: string }[], name: string): Item => {
    const P = (x: number, z: number): Vec2 => [q[0] + pl.u[0] * x, q[1] + pl.u[1] * x]
    const all = polys.flatMap((p) => p.pts)
    const xs = all.map((p) => p[0])
    const zs = all.map((p) => p[1])
    const x0 = Math.min(...xs)
    const x1 = Math.max(...xs)
    // A sliver on the plane, just behind it.
    const back: Vec2 = [-pl.n[0] * 0.05, -pl.n[1] * 0.05]
    const a = P(x0, 0)
    const b = P(x1, 0)
    const hull: Ring = [a, b, [b[0] + back[0], b[1] + back[1]], [a[0] + back[0], a[1] + back[1]]]
    return {
      id, kind: 'building', hull, zMin: Math.min(...zs), zMax: Math.max(...zs), key: centroid(hull)[1], name, dots: [],
      shapes: polys.map((p) => ({ pts: p.pts.map(([x, z]) => view.toScreen(P(x, z), z)), fill: p.fill, ink: true })),
    }
  }
  const rect = (x0: number, z0: number, x1: number, z1: number): Vec2[] => [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]
  // Trains: by track, the box nearest the plane among those that reach it.
  const tracks = new Map<string, Box[]>()
  for (const b of boxes) {
    if (b.front === undefined || b.id.endsWith(':cab') || !near(b)) continue
    const key = b.id.replace(/:\d+$/, '')
    tracks.set(key, [...(tracks.get(key) ?? []), b])
  }
  for (const [key, list] of tracks) {
    const b = list.reduce((best, x) => (reach(x).hi > reach(best).hi ? x : best))
    const m = meet(b)
    if (m === null) continue
    const { hw, hl } = frameOf(b)
    const z0 = b.z0
    const H = b.z1 - b.z0
    const rail = z0 - 0.1
    const [lit, shade] = toned3('coach')
    const [rl, rs, rr] = toned3('carRoof')
    const [ll, ls] = toned3('loco')
    const [cl] = toned3('coal')
    const glass = pal.parts.glass[0]
    const polys: { pts: Vec2[]; fill: string }[] = [
      // Two trucks on the rails.
      { pts: rect(-1.25, rail, 1.25, z0 + 0.15), fill: cl },
    ]
    if (b.tone === 'coach' || b.tone === 'freight') {
      const eave = z0 + 0.78 * H
      polys.push(
        { pts: [[-hw, z0 + 0.15], [hw, z0 + 0.15], [hw, eave], [hw * 0.82, z0 + 0.9 * H], [hw * 0.45, z0 + 0.98 * H], [0, b.z1], [-hw * 0.45, z0 + 0.98 * H], [-hw * 0.82, z0 + 0.9 * H], [-hw, eave]], fill: b.tone === 'coach' ? rs : pal.parts.freight[1] },
        { pts: rect(-hw, z0 + 0.15, hw, eave), fill: b.tone === 'coach' ? lit : pal.parts.freight[0] },
      )
      if (b.tone === 'coach') {
        polys.push(
          // The end door, with its window, and the diaphragm's frame around it.
          { pts: rect(-0.95, z0 + 0.15, 0.95, z0 + 0.74 * H), fill: shade },
          { pts: rect(-0.45, z0 + 0.15, 0.45, z0 + 0.7 * H), fill: rl },
          { pts: rect(-0.3, z0 + 0.42 * H, 0.3, z0 + 0.62 * H), fill: glass },
        )
      }
    } else if (hl > 7) {
      // An engine's front: the cab beyond, the boiler's round smokebox, its stack.
      const cz = z0 + 2.35
      const disc: Vec2[] = Array.from({ length: 20 }, (_, i) => [1.02 * Math.cos((i * Math.PI) / 10), cz + 1.02 * Math.sin((i * Math.PI) / 10)])
      polys.push(
        { pts: rect(-hw, z0 + 1.25, hw, z0 + 3.65), fill: ls },
        { pts: [[-hw - 0.12, z0 + 3.65], [hw + 0.12, z0 + 3.65], [hw * 0.6, z0 + 3.95], [-hw * 0.6, z0 + 3.95]], fill: cl },
        { pts: rect(-hw * 0.8, z0 + 0.15, hw * 0.8, z0 + 1.25), fill: ll },
        { pts: rect(-hw, z0 + 1.25, hw, z0 + 1.4), fill: ll },
        { pts: rect(-0.32, cz, 0.32, z0 + 4.0), fill: cl },
        { pts: disc, fill: cl },
        { pts: Array.from({ length: 12 }, (_, i): Vec2 => [0.22 * Math.cos((i * Math.PI) / 6), cz + 0.35 + 0.22 * Math.sin((i * Math.PI) / 6)]), fill: glass },
      )
    } else {
      // A tender's end: its tank, and the coal heaped over it.
      polys.push(
        { pts: [[-hw * 0.85, z0 + 2.5], [hw * 0.85, z0 + 2.5], [hw * 0.5, z0 + 3.05], [-hw * 0.5, z0 + 3.05]], fill: cl },
        { pts: rect(-hw, z0 + 0.15, hw, z0 + 2.5), fill: ll },
      )
    }
    items.push(flat(`${key}:end`, m.q, polys, 'A train: a car seen end on'))
  }
  // Sheds: by shed, its butterfly profile where its line meets the plane.
  const sheds = new Map<string, Box>()
  for (const b of boxes) {
    if (!isShed(b) || b.id.includes(':post:') || !near(b)) continue
    const key = b.id.replace(/:\d+$/, '')
    const prev = sheds.get(key)
    if (prev === undefined || reach(b).hi > reach(prev).hi) sheds.set(key, b)
  }
  const placed: number[] = []
  for (const [key, b] of sheds) {
    const m = meet(b)
    if (m === null || placed.some((s) => Math.abs(s - m.s) < 2)) continue
    placed.push(m.s)
    const { hw } = frameOf(b)
    const z1 = b.z1
    const ground = z1 - 0.6 - (b.z1 - b.z0 > 0 ? 0 : 0)
    const [il, is] = toned3('iron')
    const post = boxes.find((x) => x.id.startsWith(`${key.replace(/:\d+$/, '')}:post:`))
    const foot = post?.z0 ?? ground - 4
    items.push(flat(`${key}:end`, m.q, [
      { pts: rect(-0.16, foot, 0.16, z1 - 0.7), fill: is },
      { pts: [[-hw, z1], [-hw, z1 - 0.25], [0, z1 - 0.85], [0, z1 - 0.6]], fill: il },
      { pts: [[0, z1 - 0.6], [0, z1 - 0.85], [hw, z1 - 0.25], [hw, z1]], fill: il },
    ], 'A platform shed, end on'))
  }
  return items
}

/**
 * A stair on the removed side, for the flat section: its outline (slope, back and foot)
 * projected square on to the plane, dashed like the outline of what was lifted away.
 */
export const stairProfile = (view: View, pal: Palette, pl: CutPlane, id: string, p: PlacedPart): Item => {
  const [p0, p1, p2, p3] = p.outer
  const mid = (a: Vec2, b: Vec2): Vec2 => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
  const foot = mid(p0, p1)
  const head = mid(p2, p3)
  const sOf = (q: Vec2) => (q[0] - pl.p[0]) * pl.u[0] + (q[1] - pl.p[1]) * pl.u[1]
  const at = (s: number): Vec2 => [pl.p[0] + pl.u[0] * s, pl.p[1] + pl.u[1] * s]
  const s0 = sOf(foot)
  const s1 = sOf(head)
  // Only the flight's outline (slope, back and foot) is drawn, dashed. At the section's scale a
  // tread is a few pixels, and a sawtooth of them, dashed or solid, reads as a jagged line.
  const outline: Vec2[] = [view.toScreen(at(s0), p.seat), view.toScreen(at(s1), p.top), view.toScreen(at(s1), p.seat), view.toScreen(at(s0), p.seat)]
  const a = at(Math.min(s0, s1))
  const b = at(Math.max(s0, s1))
  const f: Vec2 = [pl.n[0] * 0.02, pl.n[1] * 0.02]
  return {
    id, kind: 'building', name: p.h.name, dots: [],
    hull: [a, b, [b[0] + f[0], b[1] + f[1]], [a[0] + f[0], a[1] + f[1]]],
    zMin: p.seat, zMax: p.top, key: (a[1] + b[1]) / 2,
    shapes: [
      { pts: outline, fill: 'none', line: true, stroke: { color: pal.cutOutline, width: pal.lineWidth * 2, dash: pal.cutOutlineDash } },
    ],
  }
}

/**
 * A traveler standing at `at` (view meters) on a floor at scene height z, upright and facing
 * across the picture (1 right, -1 left), in the route's color. Its footprint is a small square
 * where it stands, so it sorts among what stands near it like any other item.
 */
export const travelerItem = (view: View, pal: Palette, id: string, at: Vec2, z: number, facing: 1 | -1): Item => {
  const [bx, by] = view.toScreen(at, z)
  const up = by - view.toScreen(at, z + 1)[1]       // screen pixels per meter of height
  const shapes: Shape[] = travelerShapes().map((poly) => ({
    pts: poly.map(([x, y]): Vec2 => [bx + x * facing * view.scale, by - y * up]),
    fill: pal.route,
  }))
  const r = 0.25
  const hull: Ring = [[at[0] - r, at[1] - r], [at[0] + r, at[1] - r], [at[0] + r, at[1] + r], [at[0] - r, at[1] + r]]
  return { id, kind: 'building', hull, zMin: z, zMax: z + 1.75, key: at[1], name: 'A traveler, drawn to scale (1.75 m)', dots: [], shapes }
}

/**
 * A platform shed in a whole view, drawn as the cutaway draws it: in short pieces, each with its
 * two roof slopes falling to a valley over its posts (a butterfly roof). Posts stay boxes.
 */
export const shedItems = (view: View, pal: Palette, b: Box): Item[] => {
  if (!isShed(b) || b.id.includes(':post:')) return [boxItem(view, pal, b)]
  const pieces = shortPieces(b)
  const items: Item[] = []
  pieces.forEach((piece, k) => {
    const parts = shaped(pal, b, piece, k, pieces.length)
    const id = pieces.length === 1 ? b.id : piece.id
    for (const part of parts) {
      const it = solidItem(view, part.tones, `${id}${part.suffix}`, [part.solid], undefined, parts.joint)
      if (it !== null) items.push(it)
    }
  })
  return items
}
