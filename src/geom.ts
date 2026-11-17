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
