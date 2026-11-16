/**
 * A cutaway in a scene: a modeled building's parts turned into solids, cut at the region's
 * plane, and made into items; the boxes of its trains and canopies lifted where asked; and the
 * dashed outline of what was taken away. With `section`, the same parts cut for the flat
 * section instead: nothing in front of the plane, and only so far behind it.
 */

import { centroid, convexHull, type Ring, type Vec2 } from './geom.ts'
import type { HistoryFeature } from './history.ts'
import type { Palette } from './palette.ts'
import { boxItem, domeProfile, toned, type Box } from './parts.ts'
import type { Cutaway } from './region.ts'
import type { Item, Shape } from './scene.ts'
import type { View } from './view.ts'
import {
  above, behind, below, clipAll, clipSolid, cutPlane, isConvex, prism, revolve, sectionOf, sideOf, solidItem, splitSolids, stair, unionOutline, within,
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
  if (h.shape === 'stair') return { solids: stair(outer, seat, top, h.steps ?? 12), hulled: false }
  if (isConvex(outer)) return { solids: [prism(outer, seat, top)], hulled: false }
  return { solids: [prism(convexHull(outer), seat, top)], hulled: true }
}

const tonesOf = (pal: Palette, h: HistoryFeature): Tones => {
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
    const tones = tonesOf(pal, p.h)
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
    if (opts.section) {
      const s = clipAll(prism(b.ring, b.z0, b.z1), [behind(plane), within(plane, other)])
      if (s === null) continue
      const it = solidItem(view, boxTones(pal, b), b.id, [s])
      if (it !== null) items.push(it)
      continue
    }
    if (lift.some((r) => r.test(b.id)) && sideOf(plane, centroid(b.ring)) > 0) {
      stats.lifted++
      continue
    }
    // Long boxes (a car, a run of canopy) are cut into short pieces, so each piece takes its
    // own place among the stairs and the concourse it passes.
    const pieces = shortPieces(b)
    pieces.forEach((piece, k) => items.push(pieces.length === 1 ? boxItem(view, pal, piece) : seamless(view, boxItem(view, pal, piece), piece, k > 0, k + 1 < pieces.length)))
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

/**
 * A piece of a cut box drawn without ink where it meets its neighbors: every face is sealed in
 * its own color, and only the edges that are not on a joint are inked, so the box reads whole.
 */
const seamless = (view: View, it: Item, b: Box, joinStart: boolean, joinEnd: boolean): Item => {
  const [p0, p1, p2, p3] = b.ring
  const joints: Vec2[] = []
  for (const z of [b.z0, b.z1]) {
    if (joinStart) joints.push(view.toScreen(p0, z), view.toScreen(p3, z))
    if (joinEnd) joints.push(view.toScreen(p1, z), view.toScreen(p2, z))
  }
  const onJoint = (q: Vec2) => joints.some((j) => Math.hypot(j[0] - q[0], j[1] - q[1]) < 1e-6)
  const shapes: Shape[] = []
  for (const sh of it.shapes) {
    shapes.push({ pts: sh.pts, fill: sh.fill, seal: true })
    for (let i = 0; i < sh.pts.length; i++) {
      const a = sh.pts[i]
      const c = sh.pts[(i + 1) % sh.pts.length]
      if (onJoint(a) && onJoint(c)) continue
      shapes.push({ pts: [a, c], fill: 'none', line: true })
    }
  }
  return { ...it, shapes }
}
