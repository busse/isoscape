/**
 * Plane geometry on the view plane.
 *
 * Everything after projection lives in "view meters": E' runs left to right across the frame,
 * N' runs from the near edge (small) to the far edge (large). The camera always looks along +N',
 * so *nearer* means *smaller N'*. That one convention is what the extruder, the paint order and
 * the renderer all agree on.
 */

export type Vec2 = readonly [number, number]
export type Ring = Vec2[]

/** Shoelace area; positive for counter-clockwise rings in a right-handed (E right, N up) plane. */
export const signedArea = (ring: readonly Vec2[]): number => {
  let sum = 0
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    sum += ring[j][0] * ring[i][1] - ring[i][0] * ring[j][1]
  }
  return sum / 2
}

export const centroid = (ring: readonly Vec2[]): Vec2 => {
  let a = 0
  let cx = 0
  let cy = 0
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const cross = ring[j][0] * ring[i][1] - ring[i][0] * ring[j][1]
    a += cross
    cx += (ring[j][0] + ring[i][0]) * cross
    cy += (ring[j][1] + ring[i][1]) * cross
  }
  if (Math.abs(a) < 1e-9) {
    const n = ring.length || 1
    return [ring.reduce((s, p) => s + p[0], 0) / n, ring.reduce((s, p) => s + p[1], 0) / n]
  }
  return [cx / (3 * a), cy / (3 * a)]
}

/** Drop a repeated closing vertex, as OSM closed ways carry one. */
export const openRing = (ring: readonly Vec2[]): Ring => {
  const out = ring.slice()
  while (out.length > 1 && samePoint(out[0], out[out.length - 1])) out.pop()
  return out
}

export const samePoint = (a: Vec2, b: Vec2, eps = 1e-9): boolean =>
  Math.abs(a[0] - b[0]) < eps && Math.abs(a[1] - b[1]) < eps

export const orient = (ring: Ring, ccw: boolean): Ring => {
  const isCcw = signedArea(ring) > 0
  return isCcw === ccw ? ring : ring.slice().reverse()
}

const distToLine = (p: Vec2, a: Vec2, b: Vec2): number => {
  const dx = b[0] - a[0]
  const dy = b[1] - a[1]
  const len = Math.hypot(dx, dy)
  if (len < 1e-9) return Math.hypot(p[0] - a[0], p[1] - a[1])
  return Math.abs(dx * (a[1] - p[1]) - dy * (a[0] - p[0])) / len
}

/**
 * Remove vertices that sit within `tolerance` of the line through their neighbors, and
 * vertices closer than `tolerance` to the previous one. Mapped footprints carry a lot of
 * near-collinear noise, and every surviving vertex becomes a dot and a wall.
 */
export const simplifyRing = (ring: Ring, tolerance: number): Ring => {
  let pts = ring.slice()
  let changed = true
  while (changed && pts.length > 3) {
    changed = false
    for (let i = 0; i < pts.length && pts.length > 3; i++) {
      const prev = pts[(i - 1 + pts.length) % pts.length]
      const cur = pts[i]
      const next = pts[(i + 1) % pts.length]
      if (Math.hypot(cur[0] - prev[0], cur[1] - prev[1]) < tolerance || distToLine(cur, prev, next) < tolerance) {
        pts.splice(i, 1)
        changed = true
        i--
      }
    }
  }
  return pts
}

/** Andrew's monotone chain; counter-clockwise, no repeated point. */
export const convexHull = (points: readonly Vec2[]): Ring => {
  const pts = points.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1])
  if (pts.length < 3) return pts
  const cross = (o: Vec2, a: Vec2, b: Vec2) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
  const lower: Vec2[] = []
  for (const p of pts) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop()
    lower.push(p)
  }
  const upper: Vec2[] = []
  for (let i = pts.length - 1; i >= 0; i--) {
    const p = pts[i]
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop()
    upper.push(p)
  }
  upper.pop()
  lower.pop()
  return lower.concat(upper)
}

export interface Rect {
  readonly minX: number
  readonly minY: number
  readonly maxX: number
  readonly maxY: number
}

export const insideRect = (p: Vec2, r: Rect): boolean =>
  p[0] >= r.minX && p[0] <= r.maxX && p[1] >= r.minY && p[1] <= r.maxY

/** Sutherland–Hodgman against an axis-aligned rectangle. Concave subjects are fine. */
export const clipRingToRect = (ring: Ring, r: Rect): Ring => {
  let out: Vec2[] = ring
  const edges: [(p: Vec2) => boolean, (a: Vec2, b: Vec2) => Vec2][] = [
    [(p) => p[0] >= r.minX, (a, b) => lerpAtX(a, b, r.minX)],
    [(p) => p[0] <= r.maxX, (a, b) => lerpAtX(a, b, r.maxX)],
    [(p) => p[1] >= r.minY, (a, b) => lerpAtY(a, b, r.minY)],
    [(p) => p[1] <= r.maxY, (a, b) => lerpAtY(a, b, r.maxY)],
  ]
  for (const [inside, cut] of edges) {
    if (out.length === 0) break
    const input = out
    out = []
    for (let i = 0; i < input.length; i++) {
      const cur = input[i]
      const prev = input[(i - 1 + input.length) % input.length]
      const curIn = inside(cur)
      const prevIn = inside(prev)
      if (curIn) {
        if (!prevIn) out.push(cut(prev, cur))
        out.push(cur)
      } else if (prevIn) {
        out.push(cut(prev, cur))
      }
    }
  }
  return out
}

/**
 * One polygon (outers counter-clockwise, holes clockwise, filled nonzero) clipped to an
 * axis-aligned rectangle, with no edge running along the rectangle's sides where the polygon
 * is not.
 *
 * Each ring is clipped by Sutherland–Hodgman, which fills correctly but, where a concave ring
 * leaves the rectangle and comes back across a notch, or a hole crosses a side, leaves edges
 * along that side over ground the polygon does not cover: an edge out and an edge back, or an
 * outer's edge over a hole's. They enclose nothing, but a ground shape is stroked in its own
 * color to seal it, and each showed as a line across the bare ground. So along each side the
 * edges' directions are summed, and where they cancel they are dropped; the rest are joined
 * again into rings. The fill is the same; the polygon falls apart into its separate pieces, and
 * a hole that crossed the side becomes a bay in the outer's edge. Where nothing cancels, the
 * rings are returned exactly as clipped.
 */
export const clipPolygonToRect = (rings: readonly Ring[], r: Rect): Ring[] => {
  const clipped = rings.map((ring) => clipRingToRect(ring, r)).filter((ring) => ring.length >= 3)
  const sides = [r.minX, r.maxX, r.minY, r.maxY]
  // Which side an edge runs along (0 to 3), or -1; x sides first, then y.
  const sideOf = (a: Vec2, b: Vec2): number => {
    for (let k = 0; k < 4; k++) {
      const v = sides[k]
      if (!Number.isFinite(v)) continue
      const axis = k < 2 ? 0 : 1
      if (a[axis] === v && b[axis] === v && a[1 - axis] !== b[1 - axis]) return k
    }
    return -1
  }
  const along: { a: number; b: number }[][] = [[], [], [], []]
  const inner: [Vec2, Vec2][] = []
  for (const ring of clipped) {
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i]
      const b = ring[(i + 1) % ring.length]
      if (a[0] === b[0] && a[1] === b[1]) continue
      const k = sideOf(a, b)
      if (k < 0) inner.push([a, b])
      else along[k].push(k < 2 ? { a: a[1], b: b[1] } : { a: a[0], b: b[0] })
    }
  }
  // Along each side: the net direction (+1 up the axis, −1 down) and how many edges cover each
  // stretch between consecutive endpoints.
  let cancels = false
  const kept: [Vec2, Vec2][] = []
  along.forEach((edges, k) => {
    if (edges.length < 2) {
      for (const e of edges) kept.push(k < 2 ? [[sides[k], e.a], [sides[k], e.b]] : [[e.a, sides[k]], [e.b, sides[k]]])
      return
    }
    const ts = [...new Set(edges.flatMap((e) => [e.a, e.b]))].sort((x, y) => x - y)
    const at = new Map(ts.map((t, i) => [t, i]))
    const net = new Array<number>(ts.length).fill(0)
    const count = new Array<number>(ts.length).fill(0)
    for (const e of edges) {
      const lo = at.get(Math.min(e.a, e.b))!
      const hi = at.get(Math.max(e.a, e.b))!
      const s = e.b > e.a ? 1 : -1
      net[lo] += s
      net[hi] -= s
      count[lo] += 1
      count[hi] -= 1
    }
    let n = 0
    let c = 0
    for (let i = 0; i + 1 < ts.length; i++) {
      n += net[i]
      c += count[i]
      if (c > Math.abs(n)) cancels = true
      for (let m = 0; m < Math.abs(n); m++) {
        const [t0, t1] = n > 0 ? [ts[i], ts[i + 1]] : [ts[i + 1], ts[i]]
        kept.push(k < 2 ? [[sides[k], t0], [sides[k], t1]] : [[t0, sides[k]], [t1, sides[k]]])
      }
    }
  })
  if (!cancels) return clipped
  // Join the edges again into rings. Every point has as many edges in as out, before and after
  // the cancelling, so a walk from any edge comes back to where it started.
  const key = (p: Vec2) => `${p[0]},${p[1]}`
  const from = new Map<string, [Vec2, Vec2][]>()
  for (const e of [...inner, ...kept]) {
    const list = from.get(key(e[0]))
    if (list === undefined) from.set(key(e[0]), [e])
    else list.push(e)
  }
  const out: Ring[] = []
  for (const list of from.values()) {
    while (list.length > 0) {
      const first = list.pop()!
      const ring: Vec2[] = [first[0]]
      const home = key(first[0])
      let e = first
      while (key(e[1]) !== home) {
        ring.push(e[1])
        const next = from.get(key(e[1]))
        if (next === undefined || next.length === 0) break
        e = next.pop()!
      }
      if (ring.length >= 3 && Math.abs(signedArea(ring)) > 1e-9) out.push(ring)
    }
  }
  return out
}

const lerpAtX = (a: Vec2, b: Vec2, x: number): Vec2 => {
  const t = (x - a[0]) / (b[0] - a[0])
  return [x, a[1] + t * (b[1] - a[1])]
}
const lerpAtY = (a: Vec2, b: Vec2, y: number): Vec2 => {
  const t = (y - a[1]) / (b[1] - a[1])
  return [a[0] + t * (b[0] - a[0]), y]
}

/** Liang–Barsky. Returns null when the segment misses the rectangle. */
export const clipSegmentToRect = (a: Vec2, b: Vec2, r: Rect): [Vec2, Vec2] | null => {
  let t0 = 0
  let t1 = 1
  const dx = b[0] - a[0]
  const dy = b[1] - a[1]
  const checks: [number, number][] = [
    [-dx, a[0] - r.minX],
    [dx, r.maxX - a[0]],
    [-dy, a[1] - r.minY],
    [dy, r.maxY - a[1]],
  ]
  for (const [p, q] of checks) {
    if (p === 0) {
      if (q < 0) return null
    } else {
      const t = q / p
      if (p < 0) {
        if (t > t1) return null
        if (t > t0) t0 = t
      } else {
        if (t < t0) return null
        if (t < t1) t1 = t
      }
    }
  }
  return [
    [a[0] + t0 * dx, a[1] + t0 * dy],
    [a[0] + t1 * dx, a[1] + t1 * dy],
  ]
}

export const pointInRing = (p: Vec2, ring: readonly Vec2[]): boolean => {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]
    const [xj, yj] = ring[j]
    if (yi > p[1] !== yj > p[1] && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) inside = !inside
  }
  return inside
}

/** Even-odd containment across all rings of a polygon (outers and holes alike). */
export const pointInPolygon = (p: Vec2, rings: readonly (readonly Vec2[])[]): boolean => {
  let inside = false
  for (const ring of rings) if (pointInRing(p, ring)) inside = !inside
  return inside
}

/**
 * Do two convex polygons' interiors overlap? If not, returns the separating axis as a unit
 * normal pointing from `b` toward `a`.
 */
export const separatingAxis = (a: readonly Vec2[], b: readonly Vec2[], eps = 1e-6): Vec2 | null => {
  for (const poly of [a, b]) {
    for (let i = 0; i < poly.length; i++) {
      const p = poly[i]
      const q = poly[(i + 1) % poly.length]
      const len = Math.hypot(q[0] - p[0], q[1] - p[1])
      if (len < 1e-9) continue
      const n: Vec2 = [(q[1] - p[1]) / len, -(q[0] - p[0]) / len]
      const [aMin, aMax] = projectOnto(a, n)
      const [bMin, bMax] = projectOnto(b, n)
      if (aMin >= bMax - eps) return n
      if (bMin >= aMax - eps) return [-n[0], -n[1]]
    }
  }
  return null
}

const projectOnto = (poly: readonly Vec2[], n: Vec2): [number, number] => {
  let min = Infinity
  let max = -Infinity
  for (const p of poly) {
    const d = p[0] * n[0] + p[1] * n[1]
    if (d < min) min = d
    if (d > max) max = d
  }
  return [min, max]
}

/** A stable small hash, for picking per-building tones deterministically. */
export const hash = (s: string): number => {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

/** Distance from p to the segment a–b. */
export const distToSegment = (p: Vec2, a: Vec2, b: Vec2): number => {
  const dx = b[0] - a[0]
  const dy = b[1] - a[1]
  const len2 = dx * dx + dy * dy
  const u = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2))
  return Math.hypot(p[0] - a[0] - u * dx, p[1] - a[1] - u * dy)
}

/** Douglas–Peucker: the fewest points of an open polyline that stay within `tol` of it. */
export const simplifyLine = (pts: readonly Vec2[], tol: number): Vec2[] => {
  if (pts.length <= 2) return pts.slice()
  const keep = new Uint8Array(pts.length)
  keep[0] = keep[pts.length - 1] = 1
  const stack: [number, number][] = [[0, pts.length - 1]]
  while (stack.length > 0) {
    const [i, j] = stack.pop() as [number, number]
    const a = pts[i], b = pts[j]
    const dx = b[0] - a[0], dy = b[1] - a[1], l2 = dx * dx + dy * dy
    let best = -1, far = 0
    for (let k = i + 1; k < j; k++) {
      const p = pts[k]
      const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
      const d = Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
      if (d > far) { far = d; best = k }
    }
    if (best >= 0 && far > tol) { keep[best] = 1; stack.push([i, best], [best, j]) }
  }
  return pts.filter((_, k) => keep[k] === 1)
}

/**
 * A ring without its spikes: a corner sharper than `minDeg` with an edge shorter than `maxLen`
 * on either side is dropped, again and again until none is left (a traced outline's pixel teeth).
 */
export const despike = (ring: Ring, minDeg = 40, maxLen = 8): Ring => {
  let r = ring.slice()
  for (let pass = 0; pass < 20 && r.length > 3; pass++) {
    let changed = false
    const out: Vec2[] = []
    for (let i = 0; i < r.length; i++) {
      const a = r[(i - 1 + r.length) % r.length], b = r[i], c = r[(i + 1) % r.length]
      const ux = a[0] - b[0], uy = a[1] - b[1], vx = c[0] - b[0], vy = c[1] - b[1]
      const lu = Math.hypot(ux, uy), lv = Math.hypot(vx, vy)
      if (lu < 1e-9 || lv < 1e-9) { changed = true; continue }
      const ang = (Math.acos(Math.max(-1, Math.min(1, (ux * vx + uy * vy) / (lu * lv)))) * 180) / Math.PI
      if (ang < minDeg && Math.min(lu, lv) < maxLen && r.length - (changed ? 1 : 0) > 3) { changed = true; continue }
      out.push(b)
    }
    r = out
    if (!changed) break
  }
  return r
}

/**
 * A simple polygon (counter-clockwise, no repeated closing point) cut into convex pieces: ear
 * clipping into triangles, then neighbors merged while the union stays convex (Hertel and
 * Mehlhorn), so an L comes out as two pieces. Each piece is a list of indices into `ring`, counter-
 * clockwise. A convex ring comes back whole; a ring that will not triangulate (self-touching) too.
 */
export const convexPieces = (ring: readonly Vec2[]): number[][] => {
  const n = ring.length
  if (n < 4) return [ring.map((_, i) => i)]
  const cross = (o: Vec2, a: Vec2, b: Vec2) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
  const convex = (idx: readonly number[]) => idx.every((v, k) => cross(ring[idx[(k + idx.length - 1) % idx.length]], ring[v], ring[idx[(k + 1) % idx.length]]) >= -1e-9)
  const all = ring.map((_, i) => i)
  if (convex(all)) return [all]
  // Ear clipping.
  const tris: number[][] = []
  const left = [...all]
  let guard = 0
  while (left.length > 3 && guard++ < 10 * n) {
    let cut = false
    for (let k = 0; k < left.length; k++) {
      const a = left[(k + left.length - 1) % left.length], b = left[k], c = left[(k + 1) % left.length]
      if (cross(ring[a], ring[b], ring[c]) <= 1e-9) continue
      const inside = left.some((v) => v !== a && v !== b && v !== c && cross(ring[a], ring[b], ring[v]) >= -1e-9 && cross(ring[b], ring[c], ring[v]) >= -1e-9 && cross(ring[c], ring[a], ring[v]) >= -1e-9)
      if (inside) continue
      tris.push([a, b, c])
      left.splice(k, 1)
      cut = true
      break
    }
    if (!cut) return [all]
  }
  if (left.length === 3) tris.push([...left])
  // Merge across shared diagonals while the result stays convex.
  const pieces = tris.map((t) => [...t])
  let merged = true
  while (merged) {
    merged = false
    outer: for (let i = 0; i < pieces.length; i++) for (let j = i + 1; j < pieces.length; j++) {
      const P = pieces[i], Q = pieces[j]
      for (let a = 0; a < P.length; a++) {
        const u = P[a], v = P[(a + 1) % P.length]
        const b = Q.findIndex((w, k) => w === v && Q[(k + 1) % Q.length] === u)
        if (b < 0) continue
        // P runs ... u v ..., Q runs ... v u ...: join them along u-v.
        const joined = [...P.slice(a + 1), ...P.slice(0, a + 1)] // starts at v, ends at u
        const rest: number[] = []
        for (let k = 2; k < Q.length; k++) rest.push(Q[(b + k) % Q.length]) // after u, before v
        const cand = [...joined, ...rest]
        if (convex(cand)) {
          pieces[i] = cand
          pieces.splice(j, 1)
          merged = true
          break outer
        }
      }
    }
  }
  return pieces
}
