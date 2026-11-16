/**
 * A cutaway in a scene: a modeled building's parts turned into solids, cut at the region's
 * plane, and made into items; the boxes of its trains and canopies lifted where asked; and the
 * dashed outline of what was taken away. With `section`, the same parts cut for the flat
 * section instead: nothing in front of the plane, and only so far behind it.
 */

import { centroid, convexHull, type Ring, type Vec2 } from './geom.ts'
import type { HistoryFeature, PartTone } from './history.ts'
import type { Palette } from './palette.ts'
import { boxItem, domeProfile, toned, type Box } from './parts.ts'
import type { Cutaway } from './region.ts'
import type { Item, Shape } from './scene.ts'
import type { View } from './view.ts'
import {
  above, behind, below, clipAll, clipSolid, cutPlane, sweep, type FaceRole, type Vec3, isConvex, prism, revolve, sectionOf, sideOf, solidItem, splitSolids, stair, unionOutline, within,
  type CutPlane, type Solid, type Tones,
} from './cutaway.ts'

/** A modeled part placed in the view: its outline, bottom and top. */
export interface PlacedPart { readonly h: HistoryFeature; readonly outer: Ring; readonly seat: number; readonly top: number }

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
  if (h.shape === 'stair') return { solids: stair(outer, seat, top, h.steps ?? 12), hulled: false }
  if (isConvex(outer)) return { solids: [prism(outer, seat, top)], hulled: false }
  return { solids: [prism(convexHull(outer), seat, top)], hulled: true }
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
  const beyond = cut.section?.beyond ?? 35
  const other = cut.section?.other ?? 2
  for (const p of parts) {
    const { solids, hulled } = partSolids(p)
    if (hulled) stats.cutHulled++
    const tones = partTones(pal, p.h)
    const id = `history:${p.h.id}`
    const subject = p.h.id.startsWith(prefix)
    if (opts.section) {
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
  for (const b of boxes) {
    if (!opts.section && lift.some((r) => r.test(b.id)) && sideOf(plane, centroid(b.ring)) > 0) {
      stats.lifted++
      continue
    }
    // Long boxes (a car, a run of canopy) are cut into short pieces, so each piece takes its
    // own place among the stairs and the concourse it passes; each is drawn in its own shape
    // (a car's body and roof, an engine's boiler, a shed's butterfly roof) without seams.
    const pieces = shortPieces(b)
    pieces.forEach((piece, k) => {
      const parts = shaped(pal, b, piece, k, pieces.length)
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

/** A part of a shaped box: a solid, its tones, and a suffix for its item's id. */
interface Shaped { readonly solid: Solid; readonly tones: Tones; readonly suffix: string }

/**
 * The solids a box is drawn as in a cutaway, for piece `k` of `n`: a coach's body with its
 * arched roof and a band of windows down each side; an engine's frame, boiler, dome and stack;
 * a tender; a shed's two roof slopes falling to a valley over its posts (a butterfly roof);
 * anything else as its box. `joint` tells the points on a joint with the next piece.
 */
const shaped = (pal: Palette, whole: Box, b: Box, k: number, n: number): Shaped[] & { joint?: (p: Vec3) => boolean } => {
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
  if ((whole.tone === 'coach' || whole.tone === 'freight') && !isCab) {
    const roof = pal.parts.roof[2]
    add([[-hw, z0], [hw, z0], [hw, z0 + 0.8 * H], [hw * 0.55, z0 + 0.96 * H], [0, z1], [-hw * 0.55, z0 + 0.96 * H], [-hw, z0 + 0.8 * H]], toneOf(whole.tone, roof), '')
    if (whole.tone === 'coach') {
      const [a, c] = within(1.6, total - 1.6)
      for (const side of [1, -1]) {
        const x0 = side * hw
        const x1 = side * (hw + 0.04)
        add([[x0, z0 + 0.36 * H], [x1, z0 + 0.36 * H], [x1, z0 + 0.62 * H], [x0, z0 + 0.62 * H]], toneOf('glass'), side > 0 ? ':windows' : ':windows-b', a, c)
      }
    }
  } else if (whole.tone === 'engine' && !isCab && total > 14) {
    const t = toneOf('engine')
    add([[-hw, z0], [hw, z0], [hw, z0 + 1.1], [-hw, z0 + 1.1]], t, '')
    const r = 0.95
    const cz = z0 + 1.1 + r
    const oct: Vec2[] = Array.from({ length: 8 }, (_, i) => [r * Math.cos(Math.PI / 8 + (i * Math.PI) / 4), cz + r * Math.sin(Math.PI / 8 + (i * Math.PI) / 4)])
    add(oct, t, ':boiler', ...within(3.2, total - 0.4))
    add([[-0.3, cz], [0.3, cz], [0.3, cz + r + 0.8], [-0.3, cz + r + 0.8]], t, ':stack', ...within(total - 2.6, total - 2.0))
    add([[-0.4, cz], [0.4, cz], [0.4, cz + r + 0.4], [-0.4, cz + r + 0.4]], t, ':dome', ...within(total * 0.55, total * 0.55 + 1.0))
  } else if (whole.tone === 'engine' && !isCab) {
    // A tender: its tank, and the coal heaped in a bunker on top.
    add([[-hw, z0], [hw, z0], [hw, z0 + 0.75 * H], [hw * 0.6, z1], [-hw * 0.6, z1], [-hw, z0 + 0.75 * H]], toneOf('engine', pal.parts.roof[1]), '')
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
