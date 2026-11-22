/**
 * Cutaways: a building opened along a vertical plane, so its rooms show.
 *
 * Everything that is cut is first turned into *solids*: convex polyhedra in view meters and
 * scene z (E′, N′, z), each a list of planar faces. A solid is clipped against half-spaces, and
 * where a clip opens it a new face closes it on the clipping plane: that face is the section,
 * drawn solid in ink (poché). On the removed side of the plane a part may still stand up to a
 * given height (the ground floor left as a plan); there the horizontal clip makes the cut tops
 * of its walls, also inked.
 *
 * Solids become ordinary items (see `solidItem`), so `order.ts` paints them with everything
 * else: a part's pieces behind the plane are one item, its pieces in front another, and the two
 * meet along the plane's line, which is what separates them in the paint order.
 */

import { centroid, convexHull, signedArea, type Ring, type Vec2 } from './geom.ts'
import { mix, type Palette } from './palette.ts'
import type { Item, Shape } from './scene.ts'
import type { View } from './view.ts'

export type Vec3 = readonly [number, number, number]

/**
 * What a face is: a wall (`side`), the inside of a shell (`inner`), a top or bottom, a face shared with a neighboring piece of the
 * same part (`internal`, never drawn, but kept so clipping can close the piece), or a section
 * (`cut`).
 */
export type FaceRole = 'side' | 'inner' | 'top' | 'bottom' | 'internal' | 'cut'
export interface Face { readonly pts: readonly Vec3[]; readonly role: FaceRole }
/** A convex polyhedron. Faces may be wound either way: `outward` orients them when drawn. */
export interface Solid { readonly faces: readonly Face[] }
/** The half-space n · p ≤ d: what a clip keeps. */
export interface HalfSpace { readonly n: Vec3; readonly d: number }

const EPS = 1e-7
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
const norm = (a: Vec3): Vec3 => {
  const l = Math.hypot(a[0], a[1], a[2]) || 1
  return [a[0] / l, a[1] / l, a[2] / l]
}

/** Newell's normal of a polygon (not normalized): its length is twice the area. */
export const newell = (pts: readonly Vec3[]): Vec3 => {
  let x = 0, y = 0, z = 0
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i]
    const b = pts[(i + 1) % pts.length]
    x += (a[1] - b[1]) * (a[2] + b[2])
    y += (a[2] - b[2]) * (a[0] + b[0])
    z += (a[0] - b[0]) * (a[1] + b[1])
  }
  return [x, y, z]
}

const mean = (pts: readonly Vec3[]): Vec3 => {
  let x = 0, y = 0, z = 0
  for (const p of pts) { x += p[0]; y += p[1]; z += p[2] }
  return [x / pts.length, y / pts.length, z / pts.length]
}

/** Drop repeated points (and a closing repeat) from a face. */
const clean = (pts: readonly Vec3[]): Vec3[] => {
  const out: Vec3[] = []
  for (const p of pts) {
    const q = out[out.length - 1]
    if (q === undefined || Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]) > 1e-6) out.push(p)
  }
  while (out.length > 1 && Math.hypot(out[0][0] - out[out.length - 1][0], out[0][1] - out[out.length - 1][1], out[0][2] - out[out.length - 1][2]) <= 1e-6) out.pop()
  return out
}

const faceOf = (pts: readonly Vec3[], role: FaceRole): Face | null => {
  const c = clean(pts)
  if (c.length < 3) return null
  const n = newell(c)
  if (Math.hypot(n[0], n[1], n[2]) < 1e-9) return null
  return { pts: c, role }
}

const solidOf = (faces: (Face | null)[]): Solid => ({ faces: faces.filter((f): f is Face => f !== null) })

/** Every corner of a solid, for hulls and extents. */
export const corners = (s: Solid): Vec3[] => s.faces.flatMap((f) => f.pts)

/** A vertical prism on a convex footprint, from z0 to z1. */
export const prism = (ring: readonly Vec2[], z0: number, z1: number): Solid => {
  const at = (p: Vec2, z: number): Vec3 => [p[0], p[1], z]
  const faces: (Face | null)[] = [
    faceOf(ring.map((p) => at(p, z0)), 'bottom'),
    faceOf(ring.map((p) => at(p, z1)), 'top'),
  ]
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i]
    const b = ring[(i + 1) % ring.length]
    faces.push(faceOf([at(a, z0), at(b, z0), at(b, z1), at(a, z1)], 'side'))
  }
  return solidOf(faces)
}

/** A level of a solid of revolution: height, and the outer and inner radii as fractions of the ring's. */
export interface Level { readonly z: number; readonly outer: number; readonly inner: number }

/**
 * A solid of revolution on `ring` (its outline at full radius), about the ring's centroid: a
 * dome, a drum, a shell. Between each pair of levels the ring is scaled linearly from the one
 * to the other, outer and inner; an inner radius of 0 is solid to the axis. Each slice between
 * two corners of the ring is one convex piece, so a shell is cut cleanly anywhere. Faces shared
 * by neighboring pieces are internal; only the bottom of the lowest level and the top of the
 * highest are drawn.
 */
export const revolve = (ring: readonly Vec2[], levels: readonly Level[]): Solid[] => {
  const c = centroid(ring as Vec2[])
  const at = (p: Vec2, k: number, z: number): Vec3 => [c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k, z]
  const out: Solid[] = []
  for (let l = 0; l + 1 < levels.length; l++) {
    const lo = levels[l]
    const hi = levels[l + 1]
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i]
      const b = ring[(i + 1) % ring.length]
      const oa0 = at(a, lo.outer, lo.z), ob0 = at(b, lo.outer, lo.z), oa1 = at(a, hi.outer, hi.z), ob1 = at(b, hi.outer, hi.z)
      const ia0 = at(a, lo.inner, lo.z), ib0 = at(b, lo.inner, lo.z), ia1 = at(a, hi.inner, hi.z), ib1 = at(b, hi.inner, hi.z)
      out.push(solidOf([
        faceOf([oa0, ob0, ob1, oa1], 'side'),
        faceOf([ia0, ia1, ib1, ib0], 'inner'),
        faceOf([oa0, oa1, ia1, ia0], 'internal'),
        faceOf([ob0, ib0, ib1, ob1], 'internal'),
        faceOf([oa0, ia0, ib0, ob0], l === 0 ? 'bottom' : 'internal'),
        faceOf([oa1, ob1, ib1, ia1], l + 2 === levels.length ? 'top' : 'internal'),
      ]))
    }
  }
  return out
}

/** A level of an inset solid: height, and how far in from the ring its outer and inner faces stand (m). */
export interface InsetLevel { readonly z: number; readonly outer: number; readonly inner: number }

/**
 * A convex ring moved in by `d` meters on every side, no further than the ring can go before it
 * turns inside out (a rectangle stops at a line down its middle: a hipped roof's ridge).
 */
export const insetRing = (ring: readonly Vec2[], d: number): Vec2[] => {
  const ok = (k: number) => {
    const r = offsetConvex(ring, -k)
    return r.every((a, i) => {
      const b = r[(i + 1) % r.length]
      const p = ring[i]
      const q = ring[(i + 1) % ring.length]
      return (b[0] - a[0]) * (q[0] - p[0]) + (b[1] - a[1]) * (q[1] - p[1]) >= -1e-9
    })
  }
  if (d <= 0 || ok(d)) return offsetConvex(ring, -Math.max(0, d))
  let lo = 0
  let hi = d
  for (let i = 0; i < 48; i++) {
    const mid = (lo + hi) / 2
    if (ok(mid)) lo = mid
    else hi = mid
  }
  return offsetConvex(ring, -lo)
}

/**
 * A solid stepped in from a convex ring level by level, like `revolve` but by distance rather
 * than by scale, so every side slopes alike: a hipped roof (outer inset growing to the ridge,
 * an inner inset a roof's thickness more, as a shell) or a square dome. Each slice between two
 * corners of the ring is one convex piece; faces shared by neighboring pieces are internal.
 */
export const insetSolids = (ring: readonly Vec2[], levels: readonly InsetLevel[]): Solid[] => {
  const rings = levels.map((l) => ({ z: l.z, o: insetRing(ring, l.outer), i: insetRing(ring, Math.max(l.inner, l.outer)) }))
  const out: Solid[] = []
  const at = (p: Vec2, z: number): Vec3 => [p[0], p[1], z]
  for (let l = 0; l + 1 < rings.length; l++) {
    const lo = rings[l]
    const hi = rings[l + 1]
    for (let i = 0; i < ring.length; i++) {
      const j = (i + 1) % ring.length
      const oa0 = at(lo.o[i], lo.z), ob0 = at(lo.o[j], lo.z), oa1 = at(hi.o[i], hi.z), ob1 = at(hi.o[j], hi.z)
      const ia0 = at(lo.i[i], lo.z), ib0 = at(lo.i[j], lo.z), ia1 = at(hi.i[i], hi.z), ib1 = at(hi.i[j], hi.z)
      out.push(solidOf([
        faceOf([oa0, ob0, ob1, oa1], 'side'),
        faceOf([ia0, ia1, ib1, ib0], 'inner'),
        faceOf([oa0, oa1, ia1, ia0], 'internal'),
        faceOf([ob0, ib0, ib1, ob1], 'internal'),
        faceOf([oa0, ia0, ib0, ob0], l === 0 ? 'bottom' : 'internal'),
        faceOf([oa1, ob1, ib1, ia1], l + 2 === rings.length ? 'top' : 'internal'),
      ]))
    }
  }
  return out
}

/**
 * Straight members in a vertical plane (a truss, a bracket, a roof slope): the plane stands on
 * the ring's first edge, from ring[0] toward ring[1]; each member runs from (u0, z0) to (u1, z1),
 * u meters along that edge and z scene height, `depth` deep in the plane, and is as thick as
 * the ring's second edge (ring[1] to ring[2]) is long. A member of six or more numbers is a
 * convex plate instead, its corners (u, z) in order. Each member is its own convex solid.
 */
export const frameSolids = (ring: readonly Vec2[], members: readonly (readonly number[])[]): Solid[] => {
  const [p0, p1, p2] = ring
  const span = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) || 1
  const thick = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) || 1
  const u: Vec2 = [(p1[0] - p0[0]) / span, (p1[1] - p0[1]) / span]
  const w: Vec2 = [(p2[0] - p1[0]) / thick, (p2[1] - p1[1]) / thick]
  const out: Solid[] = []
  for (const m of members) {
    if (m.length >= 6 && m.length % 2 === 0) {
      // A convex plate given by its corners (u, z), in order: a clock face, a gusset.
      const profile: Vec2[] = []
      for (let i = 0; i < m.length; i += 2) profile.push([m[i], m[i + 1]])
      out.push(sweep(profile, p0, u, w, 0, thick))
      continue
    }
    const [u0, z0, u1, z1, depth] = m
    const l = Math.hypot(u1 - u0, z1 - z0)
    if (l < 1e-6) continue
    const nu = (-(z1 - z0) / l) * depth / 2
    const nz = ((u1 - u0) / l) * depth / 2
    const profile: Vec2[] = [[u0 + nu, z0 + nz], [u1 + nu, z1 + nz], [u1 - nu, z1 - nz], [u0 - nu, z0 - nz]]
    out.push(sweep(profile, p0, u, w, 0, thick))
  }
  return out
}

/** A track's ties and rails, in meters: standard gauge, ties 8 ft 6 in long, 0.67 m apart. */
export const TRACK = { gauge: 1.435, tieLength: 2.6, tieWidth: 0.23, tieHeight: 0.18, every: 0.67, railWidth: 0.075, railHeight: 0.16 } as const

/**
 * A length of track on a deck: ties square to it and two rails on them, from the ring's first
 * edge (across the track, ring[0] to ring[1]) along its second (ring[1] to ring[2]), from `z`.
 */
export const trackSolids = (ring: readonly Vec2[], z: number): Solid[] => {
  const [p0, p1, p2] = ring
  const across = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) || 1
  const len = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) || 1
  const u: Vec2 = [(p1[0] - p0[0]) / across, (p1[1] - p0[1]) / across]
  const w: Vec2 = [(p2[0] - p1[0]) / len, (p2[1] - p1[1]) / len]
  const origin: Vec2 = [p0[0] + u[0] * across / 2, p0[1] + u[1] * across / 2]
  const out: Solid[] = []
  const rect = (a0: number, a1: number, z0: number, z1: number): Vec2[] => [[a0, z0], [a1, z0], [a1, z1], [a0, z1]]
  const half = TRACK.tieLength / 2
  for (let s = TRACK.every / 2; s + TRACK.tieWidth / 2 <= len; s += TRACK.every) {
    out.push(sweep(rect(-half, half, z, z + TRACK.tieHeight), origin, u, w, s - TRACK.tieWidth / 2, s + TRACK.tieWidth / 2))
  }
  const top = z + TRACK.tieHeight
  for (const side of [-1, 1]) {
    const c = side * (TRACK.gauge / 2 + TRACK.railWidth / 2)
    out.push(sweep(rect(c - TRACK.railWidth / 2, c + TRACK.railWidth / 2, top, top + TRACK.railHeight), origin, u, w, 0, len))
  }
  return out
}

/**
 * A flight of stairs on a four-cornered footprint: it rises from the edge ring[0]–ring[1] (at
 * z0) to the edge ring[2]–ring[3] (at z1) in `steps` treads, each a solid block down to z0.
 */
export const stair = (ring: readonly Vec2[], z0: number, z1: number, steps: number): Solid[] => {
  const [p0, p1, p2, p3] = ring
  const lerp = (a: Vec2, b: Vec2, t: number): Vec2 => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
  const n = Math.max(1, Math.round(steps))
  const out: Solid[] = []
  for (let k = 0; k < n; k++) {
    const t0 = k / n
    const t1 = (k + 1) / n
    const foot = [lerp(p0, p3, t0), lerp(p1, p2, t0), lerp(p1, p2, t1), lerp(p0, p3, t1)]
    out.push(prism(foot, z0, z0 + ((z1 - z0) * (k + 1)) / n))
  }
  return out
}

/**
 * A convex profile, given as (u, z) points, swept straight along a line: the cross-section of a
 * car body or a shed roof run along its track. `origin` is the line's start, `u` the unit
 * direction across it, `w` the unit direction along it; the solid runs from w0 to w1. End faces
 * can be marked internal, where the solid meets the next piece of the same run.
 */
export const sweep = (
  profile: readonly Vec2[], origin: Vec2, u: Vec2, w: Vec2, w0: number, w1: number, ends: [FaceRole, FaceRole] = ['side', 'side'],
): Solid => {
  const at = ([a, z]: Vec2, t: number): Vec3 => [origin[0] + u[0] * a + w[0] * t, origin[1] + u[1] * a + w[1] * t, z]
  const faces: (Face | null)[] = [
    faceOf(profile.map((q) => at(q, w0)), ends[0]),
    faceOf(profile.map((q) => at(q, w1)), ends[1]),
  ]
  for (let i = 0; i < profile.length; i++) {
    const a = profile[i]
    const b = profile[(i + 1) % profile.length]
    faces.push(faceOf([at(a, w0), at(b, w0), at(b, w1), at(a, w1)], 'side'))
  }
  return solidOf(faces)
}

/**
 * Clip a solid to a half-space. Returns the solid unchanged when it lies wholly inside, null
 * when wholly outside, and otherwise the part inside, closed by a `cut` face on the plane.
 */
export const clipSolid = (s: Solid, h: HalfSpace): Solid | null => {
  let inside = false
  let outside = false
  for (const f of s.faces) for (const p of f.pts) {
    const d = dot(h.n, p) - h.d
    if (d > EPS) outside = true
    else if (d < -EPS) inside = true
  }
  if (!outside) {
    // A face shared by two pieces of one part that lies on the plane is where the part is cut.
    const on = (f: Face) => f.role === 'internal' && f.pts.every((p) => Math.abs(dot(h.n, p) - h.d) <= 1e-6)
    return s.faces.some(on) ? { faces: s.faces.map((f) => (on(f) ? { pts: f.pts, role: 'cut' } : f)) } : s
  }
  if (!inside) return null
  const faces: Face[] = []
  const onPlane: Vec3[] = []
  for (const f of s.faces) {
    const out: Vec3[] = []
    const pts = f.pts
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i]
      const b = pts[(i + 1) % pts.length]
      const da = dot(h.n, a) - h.d
      const db = dot(h.n, b) - h.d
      if (da <= EPS) {
        out.push(a)
        if (da >= -EPS) onPlane.push(a)
      }
      if ((da < -EPS && db > EPS) || (da > EPS && db < -EPS)) {
        const t = da / (da - db)
        const p: Vec3 = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]
        out.push(p)
        onPlane.push(p)
      }
    }
    const face = faceOf(out, f.role)
    if (face !== null) faces.push(face)
  }
  const cap = capOf(onPlane, h.n)
  if (cap !== null) faces.push(cap)
  return faces.length === 0 ? null : { faces }
}

/** The convex polygon through points on a plane with normal `n`, as a cut face. */
const capOf = (pts: readonly Vec3[], n: Vec3): Face | null => {
  const unique: Vec3[] = []
  for (const p of pts) if (!unique.some((q) => Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]) < 1e-6)) unique.push(p)
  if (unique.length < 3) return null
  const ref: Vec3 = Math.abs(n[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0]
  const e1 = norm(cross(n, ref))
  const e2 = cross(n, e1)
  const c = mean(unique)
  const sorted = unique
    .map((p) => ({ p, t: Math.atan2(dot(sub(p, c), e2), dot(sub(p, c), e1)) }))
    .sort((a, b) => a.t - b.t)
    .map((x) => x.p)
  return faceOf(sorted, 'cut')
}

/** Clip by several half-spaces in turn (an intersection). */
export const clipAll = (s: Solid, hs: readonly HalfSpace[]): Solid | null => {
  let cur: Solid | null = s
  for (const h of hs) {
    if (cur === null) return null
    cur = clipSolid(cur, h)
  }
  return cur
}

/**
 * The cut plane, in view meters: a point on it, the unit direction it runs, and the unit normal
 * toward the side that is lifted away.
 */
export interface CutPlane { readonly p: Vec2; readonly u: Vec2; readonly n: Vec2 }

/**
 * The plane through view point `p` running along compass `bearing`, for a view whose own
 * bearing is `viewBearing`, with the `remove` side of that bearing lifted away.
 */
export const cutPlane = (p: Vec2, bearing: number, viewBearing: number, remove: 'left' | 'right'): CutPlane => {
  const r = ((bearing - viewBearing) * Math.PI) / 180
  const u: Vec2 = [Math.sin(r), Math.cos(r)]
  // Turning clockwise from the direction of the plane is its right.
  const right: Vec2 = [u[1], -u[0]]
  return { p, u, n: remove === 'right' ? right : [-right[0], -right[1]] }
}

/** Signed distance of a view point from the plane: positive on the removed side. */
export const sideOf = (pl: CutPlane, q: Vec2): number => (q[0] - pl.p[0]) * pl.n[0] + (q[1] - pl.p[1]) * pl.n[1]

/** The half-space behind the plane (kept), and the one in front of it (removed), in 3D. */
export const behind = (pl: CutPlane): HalfSpace => ({ n: [pl.n[0], pl.n[1], 0], d: pl.n[0] * pl.p[0] + pl.n[1] * pl.p[1] })
export const inFront = (pl: CutPlane): HalfSpace => ({ n: [-pl.n[0], -pl.n[1], 0], d: -(pl.n[0] * pl.p[0] + pl.n[1] * pl.p[1]) })
/** Everything at or below scene height z. */
export const below = (z: number): HalfSpace => ({ n: [0, 0, 1], d: z })
/** Everything at or above scene height z. */
export const above = (z: number): HalfSpace => ({ n: [0, 0, -1], d: -z })
/** Everything no more than `depth` meters behind the plane. */
export const within = (pl: CutPlane, depth: number): HalfSpace => ({ n: [-pl.n[0], -pl.n[1], 0], d: depth - (pl.n[0] * pl.p[0] + pl.n[1] * pl.p[1]) })

/**
 * Split a part's solids at the plane. Behind it they are kept whole; in front, only what lies
 * at or below `keepZ` (the ground floor, as a plan), or nothing when `keepZ` is undefined.
 */
export const splitSolids = (solids: readonly Solid[], pl: CutPlane, keepZ?: number): { back: Solid[]; front: Solid[] } => {
  const back: Solid[] = []
  const front: Solid[] = []
  for (const s of solids) {
    const b = clipSolid(s, behind(pl))
    if (b !== null) back.push(b)
    if (keepZ === undefined) continue
    const f = clipAll(s, [inFront(pl), below(keepZ)])
    if (f !== null) front.push(f)
  }
  return { back, front }
}

/**
 * The section of a convex solid on the plane: the polygon its cut face would have, in plane
 * coordinates (s along the plane's direction from its point, z), or null where it misses.
 */
export const sectionOf = (s: Solid, pl: CutPlane): Vec2[] | null => {
  const c = clipSolid(s, behind(pl))
  if (c === null) return null
  const cap = c.faces.find((f) => f.role === 'cut' && Math.abs(dot(norm(newell(f.pts)), [pl.n[0], pl.n[1], 0])) > 0.99)
  if (cap === undefined) return null
  return cap.pts.map((q): Vec2 => [(q[0] - pl.p[0]) * pl.u[0] + (q[1] - pl.p[1]) * pl.u[1], q[2]])
}

/** The colors a part is drawn in: walls lit and shaded, its top, and the section's ink. */
export interface Tones {
  readonly lit: string; readonly shade: string; readonly roof: string; readonly cut: string
  /** The inside of a shell (a dome's ceiling): lit and shaded. */
  readonly inner?: readonly [string, string]
  /** False: faces are filled without ink (the `land` tone, which stands for the ground). */
  readonly ink?: boolean
}

/**
 * One item from a part's solids. Faces turned away from the camera are dropped (on screen their
 * corners run clockwise); the rest are painted far to near by their centers' depth along the
 * line of sight, and the sections last, since they lie on the plane, in front of everything the
 * part keeps behind it. A face's tone follows its normal like a wall's in `extrude`, leaning
 * toward the roof tone as it turns up.
 */
export const solidItem = (
  view: View, tones: Tones, id: string, solids: readonly Solid[], name?: string, joint?: (p: Vec3) => boolean,
): Item | null => {
  const pts = solids.flatMap(corners)
  if (pts.length === 0) return null
  const sin = view.squash
  const cos = Math.sqrt(Math.max(0, 1 - sin * sin))
  const faces: { depth: number; cut: boolean; shape: Shape }[] = []
  for (const s of solids) {
    const c = mean(corners(s))
    for (const f of s.faces) {
      if (f.role === 'internal' || f.role === 'bottom') continue
      let n = newell(f.pts)
      const fc = mean(f.pts)
      // Outward: away from the solid's center (it is convex).
      const flip = dot(n, sub(fc, c)) < 0
      if (flip) n = [-n[0], -n[1], -n[2]]
      const ring = flip ? [...f.pts].reverse() : f.pts
      const screen = ring.map((p) => view.toScreen([p[0], p[1]], p[2]))
      // Seen from outside, an outward face runs counter-clockwise in view meters; on screen,
      // with y down, that is a negative signed area.
      if (signedArea(screen) > -1e-6) continue
      const u = norm(n)
      let fill: string
      if (f.role === 'cut') fill = tones.cut
      else if (f.role === 'top' || u[2] > 0.97) fill = tones.roof
      else {
        const h = Math.hypot(u[0], u[1]) || 1
        const [lit, shade] = f.role === 'inner' && tones.inner !== undefined ? tones.inner : [tones.lit, tones.shade]
        const wall = mix(lit, shade, (u[0] / h + 1) / 2)
        fill = u[2] > 0.05 ? mix(wall, tones.roof, u[2]) : wall
      }
      if (joint === undefined) faces.push({ depth: fc[1] * cos - fc[2] * sin, cut: f.role === 'cut', shape: { pts: screen, fill, ink: tones.ink ?? true } })
      else {
        // Sealed, and inked only along edges that are not on a joint with the next piece.
        const shapes: Shape[] = [{ pts: screen, fill, seal: true }]
        for (let i = 0; i < ring.length; i++) {
          const j = (i + 1) % ring.length
          if (joint(ring[i]) && joint(ring[j])) continue
          shapes.push({ pts: [screen[i], screen[j]], fill: 'none', line: true })
        }
        const depth = fc[1] * cos - fc[2] * sin
        for (const sh of shapes) faces.push({ depth, cut: f.role === 'cut', shape: sh })
      }
    }
  }
  faces.sort((a, b) => Number(a.cut) - Number(b.cut) || b.depth - a.depth)
  const flat = pts.map((p): Vec2 => [p[0], p[1]])
  const hull = convexHull(flat)
  const zs = pts.map((p) => p[2])
  return {
    id,
    kind: 'building',
    hull: hull.length >= 3 ? hull : thin(flat),
    zMin: Math.min(...zs),
    zMax: Math.max(...zs),
    key: centroid(hull.length >= 3 ? hull : thin(flat))[1],
    shapes: faces.map((f) => f.shape),
    dots: [],
    ...(name === undefined ? {} : { name }),
  }
}

/** A hull for points that have no area (a line seen end on): a sliver around them. */
const thin = (pts: readonly Vec2[]): Ring => {
  const p = pts[0]
  const q = pts.reduce((best, x) => (Math.hypot(x[0] - p[0], x[1] - p[1]) > Math.hypot(best[0] - p[0], best[1] - p[1]) ? x : best), p)
  const dx = q[0] - p[0]
  const dy = q[1] - p[1]
  const l = Math.hypot(dx, dy) || 1
  const nx = (-dy / l) * 0.01
  const ny = (dx / l) * 0.01
  return [[p[0] - nx, p[1] - ny], [q[0] - nx, q[1] - ny], [q[0] + nx, q[1] + ny], [p[0] + nx, p[1] + ny]]
}

/**
 * The outline of a union of footprints: the pieces of every ring's edges that do not run inside
 * another ring or along another ring's edge on its inside. Each edge is split where other rings
 * cross it, and a piece is kept when the point just outside its middle is outside every ring.
 */
export const unionOutline = (rings: readonly (readonly Vec2[])[]): [Vec2, Vec2][] => {
  const out: [Vec2, Vec2][] = []
  const inside = (q: Vec2) => rings.some((r) => pointIn(q, r))
  rings.forEach((ring, k) => {
    const ccw = signedArea(ring as Vec2[]) > 0
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i]
      const b = ring[(i + 1) % ring.length]
      const ts = [0, 1]
      rings.forEach((other, j) => {
        if (j === k) return
        for (let m = 0; m < other.length; m++) {
          const t = segT(a, b, other[m], other[(m + 1) % other.length])
          if (t !== null) ts.push(t)
        }
      })
      ts.sort((x, y) => x - y)
      const dx = b[0] - a[0]
      const dy = b[1] - a[1]
      const l = Math.hypot(dx, dy)
      if (l < 1e-9) continue
      // Outward: right of the direction of travel for a counter-clockwise ring.
      const o: Vec2 = ccw ? [dy / l, -dx / l] : [-dy / l, dx / l]
      for (let s = 0; s + 1 < ts.length; s++) {
        if (ts[s + 1] - ts[s] < 1e-6) continue
        const m = (ts[s] + ts[s + 1]) / 2
        const q: Vec2 = [a[0] + dx * m + o[0] * 0.02, a[1] + dy * m + o[1] * 0.02]
        if (inside(q)) continue
        out.push([[a[0] + dx * ts[s], a[1] + dy * ts[s]], [a[0] + dx * ts[s + 1], a[1] + dy * ts[s + 1]]])
      }
    }
  })
  return out
}

const pointIn = (p: Vec2, ring: readonly Vec2[]): boolean => {
  let c = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const a = ring[i]
    const b = ring[j]
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < ((b[0] - a[0]) * (p[1] - a[1])) / (b[1] - a[1]) + a[0]) c = !c
  }
  return c
}

/** Where segment a–b meets segment c–d, as a fraction along a–b, or null. */
const segT = (a: Vec2, b: Vec2, c: Vec2, d: Vec2): number | null => {
  const rx = b[0] - a[0], ry = b[1] - a[1], sx = d[0] - c[0], sy = d[1] - c[1]
  const den = rx * sy - ry * sx
  if (Math.abs(den) < 1e-12) return null
  const t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / den
  const u = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / den
  return t > 1e-9 && t < 1 - 1e-9 && u >= -1e-9 && u <= 1 + 1e-9 ? t : null
}

/** Is a footprint convex (every turn the same way)? */
export const isConvex = (ring: readonly Vec2[]): boolean => {
  let sign = 0
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i]
    const b = ring[(i + 1) % ring.length]
    const c = ring[(i + 2) % ring.length]
    const z = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
    if (Math.abs(z) < 1e-9) continue
    if (sign === 0) sign = Math.sign(z)
    else if (Math.sign(z) !== sign) return false
  }
  return true
}

export const tonesOf = (pal: Palette, lit: string, shade: string, roof: string): Tones => ({ lit, shade, roof, cut: pal.poche })

/**
 * A convex counter-clockwise ring pushed `d` meters out: each edge moved out along its normal,
 * the corners where the moved edges meet.
 */
export const offsetConvex = (ring: readonly Vec2[], d: number): Vec2[] => {
  if (d === 0) return ring.slice()
  const n = ring.length
  const lines = ring.map((a, i) => {
    const b = ring[(i + 1) % n]
    const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
    const o: Vec2 = [((b[1] - a[1]) / l) * d, (-(b[0] - a[0]) / l) * d]
    return { p: [a[0] + o[0], a[1] + o[1]] as Vec2, v: [b[0] - a[0], b[1] - a[1]] as Vec2 }
  })
  return lines.map((L, i) => {
    const M = lines[(i + n - 1) % n]
    const den = M.v[0] * L.v[1] - M.v[1] * L.v[0]
    if (Math.abs(den) < 1e-9 * Math.hypot(...M.v) * Math.hypot(...L.v)) return L.p
    const t = ((L.p[0] - M.p[0]) * L.v[1] - (L.p[1] - M.p[1]) * L.v[0]) / den
    return [M.p[0] + M.v[0] * t, M.p[1] + M.v[1] * t]
  })
}
