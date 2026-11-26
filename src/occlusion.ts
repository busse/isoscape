/**
 * Occlusion checks after the fact: given items in the order they are painted, find where one is
 * painted over another that stands nearer the camera at the same point of the picture.
 *
 * Every standing item is taken as a prism: its footprint (view meters) from `zMin` to `zMax`
 * (scene height). A point of the picture is a line of sight; on it a prism's nearest surface is
 * found exactly (the line of sight falls as it goes into the frame, so its nearest point inside a
 * prism is the highest one there). An x-ray band (`Item.under`) is the vertical face it is drawn
 * on (`under.edges`). Used by tools/floods/d3/occlusion.ts to list faults, and by render.ts to
 * keep a band off the nearer items painted before it (a region's `occlusion: "strict"`).
 */
import { pointInRing, type Vec2 } from './geom.ts'
import type { Item, Shape } from './scene.ts'
import type { View } from './view.ts'

/** The nearest N' at which the line of sight through screen point `p` meets a prism, or null. */
export const prismDepth = (view: Pick<View, 'scale' | 'squash' | 'zScale'>, ring: readonly Vec2[], zMin: number, zMax: number, p: Vec2): number | null => {
  const s = view.scale, q = view.squash, k = view.zScale
  const e = p[0] / s
  // N' along the line of sight at height z.
  const nAt = (z: number) => -(p[1] + z * s * k) / (s * q)
  const nLo = nAt(zMax), nHi = nAt(zMin) // nearer end at the top
  // The footprint's extent along N' at this E': the crossings of the vertical line E' = e.
  const xs: number[] = []
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i], b = ring[(i + 1) % ring.length]
    if ((a[0] <= e && b[0] > e) || (b[0] <= e && a[0] > e)) xs.push(a[1] + ((e - a[0]) / (b[0] - a[0])) * (b[1] - a[1]))
  }
  if (xs.length < 2) return null
  xs.sort((u, v) => u - v)
  let best: number | null = null
  for (let i = 0; i + 1 < xs.length; i += 2) {
    const lo = Math.max(xs[i], nLo), hi = Math.min(xs[i + 1], nHi)
    if (lo <= hi + 1e-9 && (best === null || lo < best)) best = lo
  }
  return best
}

/** The N' of a vertical face on edge a→b (view meters) at screen point `p`, or null off its ends. */
export const faceDepth = (view: Pick<View, 'scale'>, a: Vec2, b: Vec2, p: Vec2): number | null => {
  const e = p[0] / view.scale
  const lo = Math.min(a[0], b[0]), hi = Math.max(a[0], b[0])
  if (e < lo - 1e-9 || e > hi + 1e-9 || hi - lo < 1e-9) return null
  return a[1] + ((e - a[0]) / (b[0] - a[0])) * (b[1] - a[1])
}

/** Whether screen point `p` is painted by a shape (a filled polygon, or a stroked line). */
export const paints = (sh: Shape, p: Vec2): boolean => {
  if (sh.line === true || sh.fill === 'none') {
    const w = sh.stroke?.width ?? 0.6
    for (let i = 0; i + 1 < sh.pts.length; i++) if (segDist(p, sh.pts[i], sh.pts[i + 1]) <= w / 2) return true
    return false
  }
  return sh.pts.length >= 3 && pointInRing(p, sh.pts)
}

const segDist = (p: Vec2, a: Vec2, b: Vec2): number => {
  const dx = b[0] - a[0], dy = b[1] - a[1]
  const l = dx * dx + dy * dy
  const t = l === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l))
  return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
}

/** Something painted: an item, or an item's x-ray band (`band`). */
export interface Painted {
  readonly item: Item
  readonly band?: boolean
}

export const shapesOf = (x: Painted): readonly Shape[] => (x.band === true ? x.item.under?.shapes ?? [] : x.item.shapes)

/** Screen box of what is painted, strokes included. */
export const boxOf = (shapes: readonly Shape[]): [number, number, number, number] => {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity
  for (const sh of shapes) {
    const w = sh.line === true || sh.fill === 'none' ? (sh.stroke?.width ?? 0.6) / 2 : 0
    for (const [x, y] of sh.pts) { x0 = Math.min(x0, x - w); y0 = Math.min(y0, y - w); x1 = Math.max(x1, x + w); y1 = Math.max(y1, y + w) }
  }
  return [x0, y0, x1, y1]
}

/**
 * Depth (N') of what is painted at screen point `p`: a band's face, else the item's prism; where
 * the line of sight misses the prism (a stroke's width past its outline, a casing), the nearest
 * N' of its footprint at that E', else of the whole footprint.
 */
export const depthOf = (view: Pick<View, 'scale' | 'squash' | 'zScale'>, x: Painted, p: Vec2): number | null => {
  if (x.band === true) {
    let best: number | null = null
    for (const [a, b] of x.item.under?.edges ?? []) {
      const d = faceDepth(view, a, b, p)
      if (d !== null && (best === null || d < best)) best = d
    }
    return best
  }
  const ring = x.item.footprint ?? x.item.hull
  const d = prismDepth(view, ring, x.item.zMin, x.item.zMax, p)
  if (d !== null) return d
  const tall = prismDepth(view, ring, -1e4, 1e4, p)
  return tall ?? Math.min(...ring.map((v) => v[1]))
}

/**
 * Where `B` (painted after `A`) covers `A` at points where `A` stands more than `tol` meters
 * nearer: how many grid points (`step` SVG units apart), the most it is nearer by, and where.
 */
export const pairOver = (
  view: Pick<View, 'scale' | 'squash' | 'zScale'>, A: Painted, B: Painted, a: readonly number[] = boxOf(shapesOf(A)), b: readonly number[] = boxOf(shapesOf(B)), step = 0.5, tol = 0.75,
): { n: number; by: number; at: Vec2 } => {
  const x0 = Math.max(a[0], b[0]), y0 = Math.max(a[1], b[1]), x1 = Math.min(a[2], b[2]), y1 = Math.min(a[3], b[3])
  let n = 0, by = 0
  let at: Vec2 = [0, 0]
  if (x0 >= x1 || y0 >= y1) return { n, by, at }
  const sa = shapesOf(A), sb = shapesOf(B)
  for (let y = y0 + step / 2; y < y1; y += step) for (let x = x0 + step / 2; x < x1; x += step) {
    const p: Vec2 = [x, y]
    if (!sb.some((sh) => paints(sh, p)) || !sa.some((sh) => paints(sh, p))) continue
    const da = depthOf(view, A, p), db = depthOf(view, B, p)
    if (da === null || db === null || da >= db - tol) continue
    n++
    if (db - da > by) { by = db - da; at = p }
  }
  return { n, by, at }
}

export interface OverPaint {
  /** Painted later, over `under`, which is nearer where they meet. */
  readonly over: string
  readonly under: string
  /** Screen area (SVG units²) where it happens, and one point of it. */
  readonly area: number
  readonly at: Vec2
  /** How much nearer `under` is there, meters (the largest found). */
  readonly by: number
}

/**
 * Every pair (earlier, later) in paint order where the later is painted over the earlier at
 * points where the earlier stands more than `tol` meters nearer, over at least `minArea` SVG
 * units² (sampled on a grid of `step` units). `skip` leaves out pairs not to judge (one item's
 * own band, the pieces of one building).
 */
export const overPaints = (
  view: Pick<View, 'scale' | 'squash' | 'zScale'>, order: readonly Painted[], opts: { tol?: number; minArea?: number; step?: number; skip?: (a: Painted, b: Painted) => boolean } = {},
): OverPaint[] => {
  const tol = opts.tol ?? 0.75, minArea = opts.minArea ?? 2, step = opts.step ?? 0.5
  const boxes = order.map((x) => boxOf(shapesOf(x)))
  const cell = 64
  const grid = new Map<string, number[]>()
  boxes.forEach((b, i) => {
    for (let gx = Math.floor(b[0] / cell); gx <= Math.floor(b[2] / cell); gx++) for (let gy = Math.floor(b[1] / cell); gy <= Math.floor(b[3] / cell); gy++) {
      const k = `${gx},${gy}`
      const l = grid.get(k); if (l) l.push(i); else grid.set(k, [i])
    }
  })
  const seen = new Set<string>()
  const out: OverPaint[] = []
  for (const list of grid.values()) {
    for (let u = 0; u < list.length; u++) for (let v = u + 1; v < list.length; v++) {
      const i = Math.min(list[u], list[v]), j = Math.max(list[u], list[v])
      const key = `${i},${j}`
      if (seen.has(key)) continue
      seen.add(key)
      const A = order[i], B = order[j] // A painted first
      if (A.item.id === B.item.id || opts.skip?.(A, B) === true) continue
      const { n, by, at } = pairOver(view, A, B, boxes[i], boxes[j], step, tol)
      const area = n * step * step
      if (area >= minArea) out.push({ over: (B.band === true ? 'band:' : '') + B.item.id, under: (A.band === true ? 'band:' : '') + A.item.id, area, at, by: Number(by.toFixed(2)) })
    }
  }
  return out
}

/**
 * Of `painted` (items and bands painted after a band's own building and before the band), those
 * that stand nearer than the band where they meet on screen: what the band must be kept off.
 */
export const nearerThanBand = (view: Pick<View, 'scale' | 'squash' | 'zScale'>, painted: readonly Painted[], band: Painted): Painted[] => {
  const own = band.item.id.split('#')[0]
  const bb = boxOf(shapesOf(band))
  return painted.filter((c) => c.item.id.split('#')[0] !== own && pairOver(view, c, band, boxOf(shapesOf(c)), bb, 0.5, 0.25).n >= 2)
}

/** The share of the smaller footprint (view meters) that the two overlap (or, `absolute`, the area in m²), sampled every `step` m. */
export const footprintOverlap = (a: readonly Vec2[], b: readonly Vec2[], step = 0.5, absolute = false): number => {
  const bx = (r: readonly Vec2[]) => [Math.min(...r.map((p) => p[0])), Math.min(...r.map((p) => p[1])), Math.max(...r.map((p) => p[0])), Math.max(...r.map((p) => p[1]))]
  const A = bx(a), B = bx(b)
  const x0 = Math.max(A[0], B[0]), y0 = Math.max(A[1], B[1]), x1 = Math.min(A[2], B[2]), y1 = Math.min(A[3], B[3])
  if (x0 >= x1 || y0 >= y1) return 0
  let both = 0
  for (let y = y0 + step / 2; y < y1; y += step) for (let x = x0 + step / 2; x < x1; x += step) if (pointInRing([x, y], a) && pointInRing([x, y], b)) both++
  const area = (r: readonly Vec2[]) => Math.abs(r.reduce((s, p, i) => { const q = r[(i + 1) % r.length]; return s + p[0] * q[1] - q[0] * p[1] }, 0) / 2)
  return absolute ? both * step * step : (both * step * step) / Math.max(1e-6, Math.min(area(a), area(b)))
}
