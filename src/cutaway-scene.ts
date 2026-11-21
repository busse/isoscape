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
import { travelerShapes, type Figure } from './traveler.ts'
import {
  above, behind, below, clipAll, corners, clipSolid, cutPlane, frameSolids, newell, insetSolids, sweep, trackSolids, type FaceRole, type Vec3, isConvex, prism, revolve, sectionOf, sideOf, solidItem, splitSolids, stair, unionOutline, within,
  type CutPlane, type Solid, type Tones,
} from './cutaway.ts'

/** A modeled part placed in the view: its outline, bottom and top. */
export interface PlacedPart {
  readonly h: HistoryFeature; readonly outer: Ring; readonly seat: number; readonly top: number
  /** A hip piece's whole roof (`roofRing`), in view meters, counter-clockwise. */
  readonly roof?: Ring
}

/** The solids a placed part is made of. Non-convex prisms are drawn on their convex hull. */
export const partSolids = (p: PlacedPart): { solids: Solid[]; hulled: boolean; sides?: number[] } => {
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
  if (h.shape === 'inset' && h.levels !== undefined) {
    const solids = insetSolids(outer, h.levels.map(([z, o, i]) => ({ z: seat + z, outer: o, inner: i })))
    // A shell (a hipped roof over rooms) is drawn side by side, so what stands inside it sorts
    // between its near and far sides; a solid one (a square dome) as one.
    const shell = h.levels.some(([, o, i]) => i > o + 1e-6 && i < 8)
    if (!shell) return { solids, hulled: false }
    // Each side is drawn in lengths of SHELL_PIECE along its edge, so a dormer on a long slope
    // sorts against the length of roof under it, not the whole slope.
    const pieces: Solid[] = []
    const sides: number[] = []
    solids.forEach((sol, k) => {
      const e = k % outer.length
      const a = outer[e]
      const b = outer[(e + 1) % outer.length]
      const len = Math.hypot(b[0] - a[0], b[1] - a[1])
      const n = Math.max(1, Math.round(len / SHELL_PIECE))
      const d: Vec3 = [(b[0] - a[0]) / len, (b[1] - a[1]) / len, 0]
      const at0 = d[0] * a[0] + d[1] * a[1]
      for (let i = 0; i < n; i++) {
        const lo = i === 0 ? -Infinity : at0 + (len * i) / n
        const hi = i + 1 === n ? Infinity : at0 + (len * (i + 1)) / n
        const cut = clipAll(sol, [
          ...(Number.isFinite(lo) ? [{ n: [-d[0], -d[1], 0] as Vec3, d: -lo }] : []),
          ...(Number.isFinite(hi) ? [{ n: d, d: hi }] : []),
        ])
        if (cut === null) continue
        // The faces where one length meets the next are joints, not sections.
        pieces.push({ faces: cut.faces.map((f) => (f.role === 'cut' ? { pts: f.pts, role: 'internal' as const } : f)) })
        sides.push(e * 100 + i)
      }
    })
    return { solids: pieces, hulled: false, sides }
  }
  if (h.shape === 'frame' && h.members !== undefined) {
    const members = h.members.filter((m) => m.length >= 5).map((m) => (m.length >= 6 && m.length % 2 === 0
      ? m.map((v, i) => (i % 2 === 1 ? seat + v : v))
      : [m[0], seat + m[1], m[2], seat + m[3], m[4]]))
    const solids = frameSolids(outer, members)
    // A long frame (a truss across a shed) is drawn in pieces of members FRAME_PIECE apart, so
    // what stands under it sorts against the piece above it, not the whole span.
    const span = Math.hypot(outer[1][0] - outer[0][0], outer[1][1] - outer[0][1])
    if (span <= 2 * FRAME_PIECE) return { solids, hulled: false }
    // (frameSolids leaves out members of no length; so does this.)
    const drawn = members.filter((m) => (m.length >= 6 && m.length % 2 === 0) || Math.hypot(m[2] - m[0], m[3] - m[1]) >= 1e-6)
    const sides = drawn.map((m) => {
      const us = m.length >= 6 ? m.filter((_, i) => i % 2 === 0) : [m[0], m[2]]
      return Math.floor(us.reduce((t, v) => t + v, 0) / us.length / FRAME_PIECE)
    })
    return { solids, hulled: false, sides }
  }
  if (h.shape === 'track') return { solids: trackSolids(outer, seat), hulled: false }
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
/** A shell's sides are drawn in lengths of about this many meters along their edges. */
export const SHELL_PIECE = 6

/** A frame longer than twice this (m) is drawn in pieces of members this far apart along it. */
export const FRAME_PIECE = 6

/** The tones a modeled part is drawn in, its inside (a dome's ceiling) in plaster. */
export const partTones = (pal: Palette, h: HistoryFeature): Tones => {
  const [lit, shade, roof] = pal.parts[h.tone ?? 'stone']
  const [il, is] = pal.parts.plaster
  // The ground's own color, uninked: earth outside a building's walls below the sidewalk, so a
  // cutaway's plan shows nothing under the ground beyond the cut.
  if (h.tone === 'land') return { lit: pal.land, shade: pal.land, roof: pal.land, cut: pal.land, ink: false }
  // Water held in a work, and ground modeled as a part, are cut in their own shade, so a
  // section reads them as water and earth, not as ink.
  return { lit, shade, roof, cut: h.tone === 'water' || h.tone === 'earth' ? shade : pal.poche, inner: [il, is] }
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
  const hidden = (cut.section?.hidden ?? []).map((r) => new RegExp(r))
  const slice = (cut.section?.slice?.parts ?? []).map((r) => new RegExp(r))
  const sliceDepth = cut.section?.slice?.depth ?? 1
  const items: Item[] = []
  const sections: Vec2[][] = []
  const stats: Record<string, number> = { cutParts: 0, keptParts: 0, cutHulled: 0, lifted: 0 }
  // Footprints of what still stands on the removed side (its low walls), where the dashed
  // outline would only repeat them.
  const standing: Ring[] = []
  const beyond = cut.section?.beyond ?? 35
  const other = cut.section?.other ?? 2
  for (const p of parts) {
    const made = partSolids(p)
    if (made.hulled) stats.cutHulled++
    // A shell's sides are each their own item (see `partSolids`); anything else is one.
    const groups = made.sides === undefined ? [-1] : [...new Set(made.sides)]
    // A shell's side faces the camera when its slope's outward normal points toward it: its
    // edge's outward normal (dy, −dx) tilted up by the slope's pitch, against the camera, which
    // looks along +N' from `squash` (the sine of its elevation) above the horizon.
    const facing = (g: number): 1 | -1 => {
      const e = Math.floor(g / 100) % p.outer.length
      const a = p.outer[e]
      const b = p.outer[(e + 1) % p.outer.length]
      const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
      const nN = -(b[0] - a[0]) / l
      const lv = p.h.levels ?? [[0, 0, 0], [1, 1, 1]]
      const pitch = Math.atan2(lv[lv.length - 1][0] - lv[0][0], (lv[lv.length - 1][1] - lv[0][1]) || 1e-9)
      const sin = view.squash
      const cos = Math.sqrt(Math.max(0, 1 - sin * sin))
      return -nN * Math.sin(pitch) * cos + Math.cos(pitch) * sin > 0 ? 1 : -1
    }
    const mark = (it: Item | null, g: number): Item | null => {
      if (it === null) return null
      const withShell = p.h.shape === 'inset' && g >= 0 ? { ...it, shell: { id: `history:${p.h.id}`, faces: facing(g) } } : it
      const inside = p.h.within === undefined ? withShell : { ...withShell, within: `history:${p.h.within}` }
      const fine = p.h.ink === 'fine' ? { ...inside, shapes: inside.shapes.map((s) => (s.ink === true ? { ...s, fine: true } : s)) } : inside
      return p.h.over === undefined ? fine : { ...fine, over: `history:${p.h.over}` }
    }
    for (const g of groups) {
      const solids = g < 0 ? made.solids : made.solids.filter((_, k) => made.sides![k] === g)
      const at = g < 0 ? '' : `/${g}`
      const tones = partTones(pal, p.h)
      const id = `history:${p.h.id}`
      const subject = p.h.id.startsWith(prefix)
      // A part lifted away whole (a shed's roofing, to show the trusses under it) leaves the
      // outline of its upper face, dashed, where it was.
      if (!opts.section && lift.some((r) => r.test(id))) {
        stats.lifted++
        const ghost = ghostItem(view, pal, `${id}:lifted${at}`, solids)
        if (ghost !== null) items.push(ghost)
        continue
      }
      if (opts.section) {
        // A flight down from the floor on the side lifted away (a stair to the platforms), or one
        // hidden behind a wall (`section.hidden`), is drawn as its profile, dashed, on the plane.
        const removed = p.top <= (opts.floorZ ?? Infinity) + 0.05 && p.outer.every((q) => sideOf(plane, q) > 0) && Math.min(...p.outer.map((q) => sideOf(plane, q))) < beyond
        if (subject && p.h.shape === 'stair' && (removed || hidden.some((r) => r.test(id)))) {
          items.push(stairProfile(view, pal, plane, id, p))
          continue
        }
        if (subject) for (const s of solids) {
          const sec = sectionOf(s, plane)
          if (sec !== null) sections.push(sec)
        }
        const sliced = slice.some((r) => r.test(id))
        const kept = solids.map((s) => clipAll(s, [behind(plane), within(plane, sliced ? sliceDepth : subject ? beyond : other)])).filter((s): s is Solid => s !== null)
        const it = mark(solidItem(view, tones, `${id}${at}`, kept, p.h.name), g)
        if (it !== null) items.push(it)
        continue
      }
      if (!subject) {
        const it = mark(solidItem(view, tones, `${id}${at}`, solids, p.h.name), g)
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
          const it = mark(solidItem(view, tones, `${id}${suffix}${tag}${at}`, s, p.h.name), g)
          if (it !== null) items.push(it)
        }
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

/**
 * The dashed outline of a lifted part: the edges of each solid's most upward-facing face, an
 * edge shared by two faces drawn once.
 */
export const ghostItem = (view: View, pal: Palette, id: string, solids: readonly Solid[]): Item | null => {
  const edges = new Map<string, [Vec3, Vec3]>()
  const key = (p: Vec3) => p.map((v) => v.toFixed(2)).join(',')
  for (const s of solids) {
    const cs = corners(s)
    const c: Vec3 = [cs.reduce((t, q) => t + q[0], 0) / cs.length, cs.reduce((t, q) => t + q[1], 0) / cs.length, cs.reduce((t, q) => t + q[2], 0) / cs.length]
    let best: { pts: readonly Vec3[]; up: number } | null = null
    for (const f of s.faces) {
      if (f.role === 'internal' || f.role === 'bottom') continue
      let n = newell(f.pts)
      const fc = f.pts.reduce((t, q) => [t[0] + q[0] / f.pts.length, t[1] + q[1] / f.pts.length, t[2] + q[2] / f.pts.length] as Vec3, [0, 0, 0] as Vec3)
      if (n[0] * (fc[0] - c[0]) + n[1] * (fc[1] - c[1]) + n[2] * (fc[2] - c[2]) < 0) n = [-n[0], -n[1], -n[2]]
      const up = n[2] / (Math.hypot(n[0], n[1], n[2]) || 1)
      if (up > 0.2 && (best === null || up > best.up)) best = { pts: f.pts, up }
    }
    if (best === null) continue
    best.pts.forEach((a, i) => {
      const b = best!.pts[(i + 1) % best!.pts.length]
      const k = [key(a), key(b)].sort().join('|')
      if (edges.has(k)) edges.delete(k)
      else edges.set(k, [a, b])
    })
  }
  if (edges.size === 0) return null
  const pts = [...edges.values()].flat()
  const flat = pts.map((q): Vec2 => [q[0], q[1]])
  const hull = convexHull(flat)
  if (hull.length < 3) return null
  const zs = pts.map((q) => q[2])
  return {
    id, kind: 'building', hull, zMin: Math.min(...zs), zMax: Math.max(...zs), key: centroid(hull)[1], dots: [],
    shapes: [...edges.values()].map(([a, b]) => ({ pts: [view.toScreen([a[0], a[1]], a[2]), view.toScreen([b[0], b[1]], b[2])], fill: 'none', line: true, stroke: { color: pal.cutOutline, width: pal.lineWidth * 2, dash: pal.cutOutlineDash } })),
  }
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
export const shaped = (pal: Palette, whole: Box, b: Box, k: number, n: number, coupled = false): Shaped[] & { joint?: (p: Vec3) => boolean } => {
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
  } else if (whole.tone === 'coach' || whole.tone === 'coachBlue') {
    // A heavyweight coach: a solid Pullman-green body, a darker arched roof, a continuous band
    // of windows down each side, and the vestibule's diaphragm in the gap ahead of it. In the
    // C&O's colors, blue, with a yellow band along the top of the side and gray below the windows.
    const eave = z0 + 0.78 * H
    if (whole.tone === 'coachBlue') {
      // Stacked bands of one width, so each sorts cleanly above the one below it.
      add(slab(hw, z0, z0 + 0.36 * H), toneOf('coachSkirt'), ':skirt')
      add(slab(hw, z0 + 0.36 * H, z0 + 0.66 * H), toneOf('coachBlue'), '')
      add(slab(hw, z0 + 0.66 * H, z0 + 0.76 * H), toneOf('coachBand'), ':band')
      add(slab(hw, z0 + 0.76 * H, eave), toneOf('coachBlue'), ':top')
    } else add(slab(hw, z0, eave), toneOf(whole.tone), '')
    add([[-hw, eave], [hw, eave], [hw * 0.82, z0 + 0.9 * H], [hw * 0.45, z0 + 0.98 * H], [0, z1], [-hw * 0.45, z0 + 0.98 * H], [-hw * 0.82, z0 + 0.9 * H]], toneOf(whole.tone === 'coachBlue' ? 'coachRoof' : 'carRoof'), ':roof')
    const [a, c] = at(1.4, total - 1.4)
    for (const side of [1, -1]) {
      const x0 = side * hw
      const x1 = side * (hw + 0.05)
      add([[x0, z0 + 0.4 * H], [x1, z0 + 0.4 * H], [x1, z0 + 0.64 * H], [x0, z0 + 0.64 * H]], toneOf('glass'), side > 0 ? ':windows' : ':windows-b', a, c)
    }
    const gap = STOCK.gap
    if (coupled && !frontAtEnd && k === 0) add(slab(hw * 0.7, z0 + 0.3, z0 + 0.72 * H), toneOf('coal'), ':diaphragm', -gap, 0)
    if (coupled && frontAtEnd && k + 1 === n) add(slab(hw * 0.7, z0 + 0.3, z0 + 0.72 * H), toneOf('coal'), ':diaphragm', len, len + gap)
  } else if (whole.tone === 'diesel') {
    // A streamlined passenger cab unit of about 1950, in plain generic form: a full-width body
    // with a darker arched roof, and at its front a nose that slopes up to a raked windshield
    // (the "bulldog" nose of the cab units then hauling most named trains), a band of small
    // windows along the body.
    const t = toneOf('diesel')
    const eave = z0 + 0.8 * H
    const nose = 3.0
    add(slab(hw, z0, eave), t, '', ...at(nose, total))
    add([[-hw, eave], [hw, eave], [hw * 0.8, z0 + 0.93 * H], [0, z1], [-hw * 0.8, z0 + 0.93 * H]], toneOf('carRoof', pal.parts.diesel[1]), ':roof', ...at(nose, total))
    // The nose, its side profile swept across the unit's width: d meters behind the front.
    const local = (d: number) => (frontAtEnd ? total - d : d) - off
    const inPiece = [0, nose].every((d) => local(d) >= w0 - 1e-6 && local(d) <= w1 + 1e-6)
    if (inPiece) {
      const side = (pts: [number, number][]): Vec2[] => pts.map(([d, z]): Vec2 => [local(d), z0 + z * H])
      const across = (pr: Vec2[], tones: Tones, suffix: string, half = hw) => out.push({ solid: sweep(pr, origin, w, u, -half, half), tones, suffix })
      across(side([[0, 0], [nose, 0], [nose, 0.8], [2.0, 0.78], [0.9, 0.58], [0, 0.4]]), t, ':nose')
      // The windshield, a thin pane laid on the slope from the nose to the cab's roof.
      const slope = (d: number) => 0.58 + ((d - 0.9) * 0.2) / 1.1
      const o = 0.05 / H
      across(side([[1.05, slope(1.05) + 0.002], [1.95, slope(1.95) + 0.002], [1.95, slope(1.95) + o], [1.05, slope(1.05) + o]]), toneOf('glass'), ':windshield', hw * 0.85)
    }
    for (const sd of [1, -1]) {
      add([[sd * hw, z0 + 0.55 * H], [sd * (hw + 0.05), z0 + 0.55 * H], [sd * (hw + 0.05), z0 + 0.7 * H], [sd * hw, z0 + 0.7 * H]], toneOf('glass'), sd > 0 ? ':windows' : ':windows-b', ...at(nose + 0.4, nose + 1.8))
      add([[sd * hw, z0 + 0.6 * H], [sd * (hw + 0.05), z0 + 0.6 * H], [sd * (hw + 0.05), z0 + 0.7 * H], [sd * hw, z0 + 0.7 * H]], toneOf('glass'), sd > 0 ? ':ports' : ':ports-b', ...at(6, total - 2))
    }
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
    const [lit, shade] = toned3(b.tone === 'coachBlue' ? 'coachBlue' : 'coach')
    const [rl, rs, rr] = toned3(b.tone === 'coachBlue' ? 'coachRoof' : 'carRoof')
    const [ll, ls] = toned3('loco')
    const [cl] = toned3('coal')
    const glass = pal.parts.glass[0]
    const polys: { pts: Vec2[]; fill: string }[] = [
      // Two trucks on the rails.
      { pts: rect(-1.25, rail, 1.25, z0 + 0.15), fill: cl },
    ]
    const coach = b.tone === 'coach' || b.tone === 'coachBlue'
    if (coach || b.tone === 'freight') {
      const eave = z0 + 0.78 * H
      polys.push(
        { pts: [[-hw, z0 + 0.15], [hw, z0 + 0.15], [hw, eave], [hw * 0.82, z0 + 0.9 * H], [hw * 0.45, z0 + 0.98 * H], [0, b.z1], [-hw * 0.45, z0 + 0.98 * H], [-hw * 0.82, z0 + 0.9 * H], [-hw, eave]], fill: coach ? rs : pal.parts.freight[1] },
        { pts: rect(-hw, z0 + 0.15, hw, eave), fill: coach ? lit : pal.parts.freight[0] },
      )
      if (b.tone === 'coachBlue') {
        polys.push(
          { pts: rect(-hw, z0 + 0.66 * H, hw, z0 + 0.76 * H), fill: pal.parts.coachBand[0] },
          { pts: rect(-hw, z0 + 0.15, hw, z0 + 0.36 * H), fill: pal.parts.coachSkirt[0] },
        )
      }
      if (coach) {
        polys.push(
          // The end door, with its window, and the diaphragm's frame around it.
          { pts: rect(-0.95, z0 + 0.15, 0.95, z0 + 0.74 * H), fill: shade },
          { pts: rect(-0.45, z0 + 0.15, 0.45, z0 + 0.7 * H), fill: rl },
          { pts: rect(-0.3, z0 + 0.42 * H, 0.3, z0 + 0.62 * H), fill: glass },
        )
      }
    } else if (b.tone === 'diesel') {
      // A diesel unit's front: its body and roof, the windshield's two panes, a headlight.
      const eave = z0 + 0.8 * H
      const [dl, ds] = toned3('diesel')
      polys.push(
        { pts: [[-hw, eave], [hw, eave], [hw * 0.8, z0 + 0.93 * H], [0, b.z1], [-hw * 0.8, z0 + 0.93 * H]], fill: ds },
        { pts: rect(-hw, z0 + 0.15, hw, eave), fill: dl },
        { pts: rect(-hw * 0.85, z0 + 0.58 * H, -0.1, eave - 0.1), fill: glass },
        { pts: rect(0.1, z0 + 0.58 * H, hw * 0.85, eave - 0.1), fill: glass },
        { pts: Array.from({ length: 12 }, (_, i): Vec2 => [0.2 * Math.cos((i * Math.PI) / 6), z0 + 0.42 * H + 0.2 * Math.sin((i * Math.PI) / 6)]), fill: glass },
      )
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
  // Trains standing alongside the plane, behind it within `depth`: each car, engine and tender
  // in side elevation, true size, on its rails, with the gaps between them.
  for (const b of boxes) {
    if (b.front === undefined || b.id.endsWith(':cab')) continue
    const { w } = frameOf(b)
    if (Math.abs(w[0] * pl.n[0] + w[1] * pl.n[1]) >= 0.05) continue
    const d = b.ring.map((q) => sideOf(pl, q))
    if (Math.max(...d) > 1e-6 || Math.min(...d) < -depth) continue
    items.push(sideElevation(view, pal, pl, b, Math.max(...d)))
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
 * A car, engine or tender seen from the side, square on, for the flat section: flat shapes on
 * its near side (`near` meters from the plane, behind it), drawn in the train's own tones.
 */
export const sideElevation = (view: View, pal: Palette, pl: CutPlane, b: Box, near: number): Item => {
  const sOf = (q: Vec2) => (q[0] - pl.p[0]) * pl.u[0] + (q[1] - pl.p[1]) * pl.u[1]
  const ss = b.ring.map(sOf)
  const s0 = Math.min(...ss)
  const s1 = Math.max(...ss)
  const len = s1 - s0
  // Which end leads: +1 when the front is toward larger s.
  const ahead = (b.front![0] * pl.u[0] + b.front![1] * pl.u[1]) > 0 ? 1 : -1
  // x: meters from the car's front, back along it.
  const S = (x: number) => (ahead > 0 ? s1 - x : s0 + x)
  const P = (x: number, z: number): Vec2 => view.toScreen([pl.p[0] + pl.u[0] * S(x) + pl.n[0] * near, pl.p[1] + pl.u[1] * S(x) + pl.n[1] * near], z)
  const z0 = b.z0
  const z1 = b.z1
  const H = z1 - z0
  const t = (tone: PartTone, k: 0 | 1 | 2 = 0) => pal.parts[tone][k]
  const glass = pal.parts.glass[0]
  const polys: { pts: Vec2[]; fill: string }[] = []
  const rect = (x0: number, za: number, x1: number, zb: number) => polys.push({ pts: [[x0, za], [x1, za], [x1, zb], [x0, zb]], fill: '' })
  const add = (pts: Vec2[], fill: string) => polys.push({ pts, fill })
  const box = (x0: number, za: number, x1: number, zb: number, fill: string) => { rect(x0, za, x1, zb); polys[polys.length - 1].fill = fill }
  const disc = (cx: number, cz: number, r: number, fill: string) => add(Array.from({ length: 16 }, (_, i): Vec2 => [cx + r * Math.cos((i * Math.PI) / 8), cz + r * Math.sin((i * Math.PI) / 8)]), fill)
  const truck = (x: number) => box(x - 1.3, z0 - 0.42, x + 1.3, z0 + 0.12, t('coal'))
  const coach = b.tone === 'coach' || b.tone === 'coachBlue'
  if (coach || b.tone === 'freight') {
    const eave = z0 + 0.78 * H
    const roof = coach ? t(b.tone === 'coachBlue' ? 'coachRoof' : 'carRoof', 1) : t('freight', 1)
    add([[0, eave], [0.25, z0 + 0.9 * H], [0.9, z1], [len - 0.9, z1], [len - 0.25, z0 + 0.9 * H], [len, eave]], roof)
    box(0, z0 + 0.12, len, eave, coach ? t(b.tone) : t('freight'))
    truck(3.2)
    truck(len - 3.2)
    if (b.tone === 'coachBlue') {
      box(0, z0 + 0.66 * H, len, z0 + 0.76 * H, t('coachBand'))
      box(0, z0 + 0.12, len, z0 + 0.36 * H, t('coachSkirt'))
    }
    if (coach) {
      // The vestibule doors at each end, and the windows between.
      box(0.35, z0 + 0.12, 1.15, z0 + 0.74 * H, t(b.tone, 1))
      box(len - 1.15, z0 + 0.12, len - 0.35, z0 + 0.74 * H, t(b.tone, 1))
      for (let x = 2.0; x + 0.9 <= len - 1.9; x += 1.55) box(x, z0 + 0.42 * H, x + 0.9, z0 + 0.64 * H, glass)
    }
  } else if (b.tone === 'diesel') {
    const eave = z0 + 0.8 * H
    const nose = 2.2
    add([[nose, eave], [nose + 0.4, z1], [len - 0.6, z1], [len, eave]], t('diesel', 1))
    add([[0, z0 + 0.12], [len, z0 + 0.12], [len, eave], [nose, eave], [0.25, z0 + 0.5 * H], [0, z0 + 0.45 * H]], t('diesel'))
    add([[nose - 1.4, z0 + 0.58 * H], [nose - 0.05, z0 + 0.58 * H], [nose - 0.05, eave - 0.1], [nose - 0.35, eave - 0.1]], glass)
    box(nose + 0.8, z0 + 0.55 * H, nose + 2.4, z0 + 0.7 * H, glass)
    for (let x = 6; x + 0.7 <= len - 2; x += 1.6) box(x, z0 + 0.6 * H, x + 0.7, z0 + 0.7 * H, glass)
    truck(3.4)
    truck(len - 3.4)
  } else if (b.tone === 'engine' && len > 14) {
    // A steam engine: pilot, frame and running board, boiler with stack and domes, the cab at
    // the back, three driving wheels.
    const cz = z0 + 2.35
    box(0.3, z0, len, z0 + 1.25, t('loco', 1))
    box(0.4, cz - 1.0, len - 4, cz + 1.0, t('loco'))
    box(0.4, cz - 1.02, 2.6, cz + 1.02, t('coal'))
    box(1.1, cz, 1.8, z0 + 4.0, t('coal'))
    box(6.4, cz, 7.5, z0 + 3.7, t('loco'))
    box(9.2, cz, 10.1, z0 + 3.6, t('loco'))
    box(len - 4, z0 + 1.25, len, z0 + 3.65, t('loco'))
    box(len - 4.1, z0 + 3.65, len + 0.1, z0 + 3.95, t('coal'))
    box(len - 3.4, z0 + 2.45, len - 1.4, z0 + 3.25, glass)
    for (const x of [5.2, 7.2, 9.2]) disc(x, z0 + 0.75, 0.85, t('coal'))
    add([[0, z0 - 0.4], [0.9, z0 - 0.4], [0.9, z0 + 0.5]], t('coal'))
  } else if (b.tone === 'engine') {
    box(0, z0, len, z0 + 2.5, t('loco'))
    add([[0.4, z0 + 2.5], [len * 0.62, z0 + 2.5], [len * 0.55, z0 + 3.05], [0.9, z0 + 3.05]], t('coal'))
    truck(2.6)
    truck(len - 2.6)
  } else {
    box(0, z0, len, z1, t(b.tone))
  }
  return {
    id: `${b.id}:side`, kind: 'building', hull: b.ring, zMin: z0 - 0.42, zMax: z1, key: centroid(b.ring)[1], name: 'A train, seen from the side', dots: [],
    shapes: polys.map((q) => ({ pts: q.pts.map(([x, z]) => P(x, z)), fill: q.fill, ink: true })),
  }
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
export const travelerItem = (view: View, pal: Palette, id: string, at: Vec2, z: number, facing: 1 | -1, figure: Figure = 'traveler'): Item => {
  const [bx, by] = view.toScreen(at, z)
  const up = by - view.toScreen(at, z + 1)[1]       // screen pixels per meter of height
  const polys = travelerShapes(undefined, figure).map((poly) => poly.map(([x, y]): Vec2 => [bx + x * facing * view.scale, by - y * up]))
  // Over a light halo, where the palette has one, so the figure reads on red seats.
  const halo = pal.routeHalo
  const shapes: Shape[] = [
    ...(halo === undefined ? [] : polys.map((pts): Shape => ({ pts: [...pts, pts[0]], fill: 'none', line: true, stroke: { color: halo, width: pal.routeWidth * 0.9, dash: [1e3, 0] } }))),
    ...polys.map((pts): Shape => ({ pts, fill: pal.route })),
  ]
  const r = 0.25
  const hull: Ring = [[at[0] - r, at[1] - r], [at[0] + r, at[1] - r], [at[0] + r, at[1] + r], [at[0] - r, at[1] + r]]
  return { id, kind: 'building', hull, zMin: z, zMax: z + 1.75, key: at[1], name: figure === 'traveler' ? 'A traveler, drawn to scale (1.75 m)' : 'A visitor, drawn to scale (1.75 m)', dots: [], shapes }
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

/**
 * The traveler's way in the cutaway (`cutaway.route`): a polyline through points [view meters,
 * scene height], cut into dashes the length of the flat section's (the palette's `routeDash`,
 * times `weight`), measured along the line on the screen, so the dashes read evenly whichever
 * way it runs. Each dash is an item of its own, with a footprint the width of the line, so it
 * sorts among what stands near it: a dash behind a wall or under a floor is hidden like
 * anything else there.
 */
export const routeItems = (view: View, pal: Palette, pts: readonly (readonly [Vec2, number])[], weight: number, pumped = false): Item[] => {
  const [on, off] = pal.routeDash.map((d) => d * weight)
  const width = pal.routeWidth * weight
  const at = (i: number, t: number): [Vec2, number] => {
    const [a, za] = pts[i]
    const [b, zb] = pts[i + 1]
    return [[a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t], za + (zb - za) * t]
  }
  // Every segment's screen length, and the dashes laid along their sum.
  const lens = pts.slice(1).map(([b, zb], i) => {
    const [a, za] = pts[i]
    const p = view.toScreen(a, za)
    const q = view.toScreen(b, zb)
    return Math.hypot(q[0] - p[0], q[1] - p[1])
  })
  const total = lens.reduce((s, l) => s + l, 0)
  const where = (d: number): [number, number] => {
    let i = 0
    while (i < lens.length - 1 && d > lens[i]) { d -= lens[i]; i++ }
    return [i, lens[i] > 0 ? Math.min(1, d / lens[i]) : 0]
  }
  const items: Item[] = []
  for (let d = 0, k = 0; d < total; d += on + off, k++) {
    const [i0, t0] = where(d)
    const [i1, t1] = where(Math.min(total, d + on))
    // A dash that turns a corner keeps the corner's point.
    const run: [Vec2, number][] = [at(i0, t0)]
    for (let i = i0; i < i1; i++) run.push(at(i, 1))
    run.push(at(i1, t1))
    const xs = run.map(([p]) => p)
    const r = 0.06
    const hull = convexHull(xs.flatMap(([x, y]): Vec2[] => [[x - r, y - r], [x + r, y - r], [x + r, y + r], [x - r, y + r]]))
    items.push({
      id: pumped ? `pumped:${k}` : `route:${k}`,
      kind: 'building',
      hull,
      zMin: Math.min(...run.map(([, z]) => z)),
      zMax: Math.max(...run.map(([, z]) => z)),
      key: xs.reduce((s, p) => s + p[1], 0) / xs.length,
      name: pumped ? 'The way of the water pumped' : 'The way to the train',
      shapes: [{ pts: run.map(([p, z]) => view.toScreen(p, z)), fill: 'none', line: true, stroke: { color: pumped ? pal.pumped : pal.route, width, round: true } }],
      dots: [],
    })
  }
  return items
}
