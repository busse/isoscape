/**
 * A modeled building's pieces, for close views of a single place: domes, platform canopies and
 * standing trains. Everything here is in view meters and becomes ordinary items (prisms and
 * stacked frustums), so `order.ts` paints it with everything else.
 */

import { signedArea, type Ring, type Vec2 } from './geom.ts'
import type { PartTone, Train } from './history.ts'
import type { Palette } from './palette.ts'
import { extrude, spire, type Item } from './scene.ts'
import type { View } from './view.ts'

/** The palette with a part's tone on its walls; its roof color is returned beside it. */
export const toned = (pal: Palette, tone: PartTone): { pal: Palette; roof: string } => {
  const [lit, shade, roof] = pal.parts[tone]
  return { pal: { ...pal, wallLit: lit, wallShade: shade }, roof }
}

/**
 * A Roman dome's section: the radius at fraction `t` of its rise, a quarter circle, with the
 * crown left 3% wide so the top cap is a ring, not a point.
 */
export const domeProfile = (t: number): number => Math.sqrt(Math.max(0, 1 - (t * 0.995) ** 2))

/** What `partLevels` needs of a part: its seat rule, support, base, height and the ground under it. */
export interface PartSeat {
  readonly id: string
  readonly grounds: readonly number[]
  readonly seat?: 'min' | 'max'
  readonly on?: string
  readonly base?: number
  readonly height?: number
  /** A fixed seat (scene z), which wins over `on` and the ground. */
  readonly at?: number
}

/**
 * The scene z of each part's bottom. A part stands `base` above its seat: the top of the part
 * named by `on` when there is one, otherwise the lowest ground under it (the highest with
 * `seat: 'max'`). Seating on a support keeps a group level on sloping ground, so columns on one
 * porch all stand on its top and meet the entablature at one height. A missing or circular
 * support falls back to the part's own ground.
 */
export const partLevels = (parts: readonly PartSeat[]): Map<string, number> => {
  const byId = new Map(parts.map((p) => [p.id, p]))
  const levels = new Map<string, number>()
  const resolving = new Set<string>()
  const level = (p: PartSeat): number => {
    const known = levels.get(p.id)
    if (known !== undefined) return known
    resolving.add(p.id)
    const support = p.on === undefined ? undefined : byId.get(p.on)
    const seat = p.at !== undefined ? p.at : support !== undefined && !resolving.has(support.id)
      ? level(support) + (support.height ?? 10)
      : p.seat === 'max' ? Math.max(...p.grounds) : Math.min(...p.grounds)
    resolving.delete(p.id)
    const z = seat + (p.base ?? 0)
    levels.set(p.id, z)
    return z
  }
  for (const p of parts) level(p)
  return levels
}

/** A dome on `outer` (its springing line), from `base` to `top`. */
export const dome = (view: View, pal: Palette, id: string, outer: Ring, base: number, top: number, name?: string): Item =>
  spire(view, toned(pal, 'dome').pal, id, outer, base, top, 'none', name, domeProfile, false, 10)

/** Point and unit direction `d` meters along a polyline (clamped to its ends). */
export const along = (pts: readonly Vec2[], d: number): { p: Vec2; dir: Vec2 } => {
  let walked = 0
  for (let i = 0; i + 1 < pts.length; i++) {
    const a = pts[i]
    const b = pts[i + 1]
    const len = Math.hypot(b[0] - a[0], b[1] - a[1])
    if (len < 1e-9) continue
    const dir: Vec2 = [(b[0] - a[0]) / len, (b[1] - a[1]) / len]
    if (d <= walked + len || i + 2 === pts.length) {
      const t = Math.min(Math.max((d - walked) / len, 0), 1)
      return { p: [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t], dir }
    }
    walked += len
  }
  return { p: pts[0], dir: [1, 0] }
}

export const lengthOf = (pts: readonly Vec2[]): number => {
  let s = 0
  for (let i = 0; i + 1 < pts.length; i++) s += Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
  return s
}

/** A rectangle `2·hl` long and `2·hw` wide about `c`, turned to `dir`, counter-clockwise. */
export const box = (c: Vec2, dir: Vec2, hl: number, hw: number): Ring => {
  const [ux, uy] = dir
  let ring: Ring = [
    [c[0] - ux * hl + uy * hw, c[1] - uy * hl - ux * hw],
    [c[0] + ux * hl + uy * hw, c[1] + uy * hl - ux * hw],
    [c[0] + ux * hl - uy * hw, c[1] + uy * hl + ux * hw],
    [c[0] - ux * hl - uy * hw, c[1] - uy * hl + ux * hw],
  ]
  if (signedArea(ring) < 0) ring = ring.reverse()
  return ring
}

/**
 * Rolling stock of the 1940s, in meters: a steam engine and its tender, and the cars behind.
 * A heavyweight coach or Pullman is about 26 m (85 ft) long, 3.1 m wide and 4.1 m tall over the
 * roof; a 40-ft boxcar about 12.5 m long and 4.0 m tall. They stand 1 m apart.
 */
export const STOCK = {
  engine: { length: 18, width: 3.1, height: 4.6 },
  tender: { length: 11, width: 3.1, height: 4.0 },
  coach: { length: 26, width: 3.1, height: 4.1 },
  freight: { length: 12.5, width: 3.0, height: 4.0 },
  gap: 1,
} as const

/** A box a part is drawn as: a footprint, its bottom and top, and its tone. */
export interface Box { readonly id: string; readonly ring: Ring; readonly z0: number; readonly z1: number; readonly tone: PartTone }

export const boxItem = (view: View, pal: Palette, b: Box): Item => {
  const t = toned(pal, b.tone)
  return extrude(view, t.pal, b.id, b.ring, [], b.z0, b.z1, t.roof, 'none')
}

/** The cars of a standing train, each its own box, set on the ground under it. */
export const trainBoxes = (id: string, line: readonly Vec2[], train: Train, ground: (p: Vec2) => number): Box[] => {
  const pts = train.reverse === true ? [...line].reverse() : line
  const total = lengthOf(pts)
  const consist: { kind: 'engine' | 'tender' | 'coach' | 'freight'; tone: PartTone }[] = []
  if (train.engine !== false) consist.push({ kind: 'engine', tone: 'engine' }, { kind: 'tender', tone: 'engine' })
  const car = train.kind ?? 'coach'
  for (let k = 0; k < train.cars; k++) consist.push({ kind: car, tone: car })
  const boxes: Box[] = []
  let d = train.at
  consist.forEach((c, k) => {
    const dims = STOCK[c.kind]
    const mid = d + dims.length / 2
    d += dims.length + STOCK.gap
    if (mid > total) return
    const { p, dir } = along(pts, mid)
    const z = ground(p) + 0.6
    boxes.push({ id: `${id}:${k}`, ring: box(p, dir, dims.length / 2, dims.width / 2), z0: z, z1: z + dims.height - 0.6, tone: c.tone })
    if (c.kind === 'engine') {
      // The cab, a step up at the engine's back end.
      const cab = along(pts, mid - dims.length / 2 + 2)
      boxes.push({ id: `${id}:${k}:cab`, ring: box(cab.p, cab.dir, 2, dims.width / 2), z0: z, z1: z + dims.height + 0.2, tone: c.tone })
    }
  })
  return boxes
}

/** The cars of a standing train, each its own item, set on the ground under it. */
export const trainItems = (
  view: View, pal: Palette, id: string, line: readonly Vec2[], train: Train, ground: (p: Vec2) => number,
): Item[] => trainBoxes(id, line, train, ground).map((b) => boxItem(view, pal, b))

/**
 * An umbrella canopy over a platform: a roof `width` wide, 0.6 m deep, at `height` over the
 * platform, on a row of iron columns. It is cut into pieces `PIECE` long so it sorts among the
 * trains beside it, with a column under each piece.
 */
export const CANOPY_PIECE = 12
export const canopyBoxes = (id: string, line: readonly Vec2[], width: number, height: number, ground: (p: Vec2) => number): Box[] => {
  const total = lengthOf(line)
  const boxes: Box[] = []
  for (let s = 0, k = 0; s < total - 1; s += CANOPY_PIECE, k++) {
    const len = Math.min(CANOPY_PIECE, total - s)
    const { p, dir } = along(line, s + len / 2)
    const z = ground(p)
    boxes.push({ id: `${id}:post:${k}`, ring: box(p, dir, 0.3, 0.3), z0: z, z1: z + height - 0.6, tone: 'iron' })
    boxes.push({ id: `${id}:${k}`, ring: box(p, dir, len / 2, width / 2), z0: z + height - 0.6, z1: z + height, tone: 'iron' })
  }
  return boxes
}
export const canopyItems = (
  view: View, pal: Palette, id: string, line: readonly Vec2[], width: number, height: number, ground: (p: Vec2) => number,
): Item[] => canopyBoxes(id, line, width, height, ground).map((b) => boxItem(view, pal, b))
