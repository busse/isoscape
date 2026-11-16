/**
 * Scene → SVG, and SVG → a pan-and-zoom page.
 *
 * The ground is a height field, and a height field hides itself: a bank that falls away from
 * the camera covers the water behind it. So the ground is painted in strips across the frame,
 * far to near, each strip draping everything that lies on it (water, parks, roads, shading,
 * contours, rapids) over the terrain. Standing things are slotted in among the strips: each
 * item paints straight after the strip that holds its near edge, so ground in front of it
 * (and any hill there) paints over it, and ground behind it does not.
 */

import { clipRingToRect, pointInPolygon, clipSegmentToRect, hash, type Rect, type Ring, type Vec2 } from './geom.ts'
import { GROUND_ORDER } from './classify.ts'
import { paintOrder } from './order.ts'
import type { Item, Scene, Shape } from './scene.ts'
import { contours, nodeShade, riverFall, type ContourSegment } from './terrain.ts'
import { isoBand, type BandPoint } from './isoband.ts'
import { coverFields as coverFieldsOf, type CoverGroup } from './landcover.ts'
import { demCredit } from './dem-sources.ts'

const f = (n: number) => (Math.round(n * 10) / 10).toString()

/** A number in tenths, as short as SVG allows: no leading zero, no "-0". */
const num = (tenths: number): string => {
  if (tenths === 0) return '0'
  const neg = tenths < 0
  const a = Math.abs(tenths)
  const whole = Math.floor(a / 10)
  const frac = a % 10
  const body = whole === 0 ? `.${frac}` : frac === 0 ? `${whole}` : `${whole}.${frac}`
  return neg ? `-${body}` : body
}
/** Join numbers, leaving out the separator where a sign or a leading dot already parts them. */
const pair = (a: string, b: string) => (b.startsWith('-') || (b.startsWith('.') && a.includes('.')) ? a + b : `${a} ${b}`)

/**
 * The directions from a kept point `a` along which a straight line passes within `tol` of
 * every point dropped since: a cone, narrowed by each point in turn. Testing a dropped point
 * against its neighbors alone lets a long, gentle curve drift off by many pixels, and then
 * the two edges of a draped row no longer meet the rows beside them.
 */
class Sleeve {
  a: Vec2 = [0, 0]
  ref = 0
  lo = -Infinity
  hi = Infinity
  tol: number
  constructor(tol: number) { this.tol = tol }
  reset(a: Vec2): void {
    this.a = a
    this.lo = -Infinity
    this.hi = Infinity
  }
  private angle(p: Vec2): number {
    const t = Math.atan2(p[1] - this.a[1], p[0] - this.a[0])
    if (this.lo === -Infinity && this.hi === Infinity) this.ref = t
    let d = t - this.ref
    while (d > Math.PI) d -= 2 * Math.PI
    while (d <= -Math.PI) d += 2 * Math.PI
    return d
  }
  /** Narrow the cone so the line passes within `tol` of `p`. */
  add(p: Vec2): void {
    const r = Math.hypot(p[0] - this.a[0], p[1] - this.a[1])
    if (r <= this.tol) return
    const t = this.angle(p)
    const w = Math.asin(this.tol / r)
    this.lo = Math.max(this.lo, t - w)
    this.hi = Math.min(this.hi, t + w)
  }
  /** Does the line from `a` to `b` pass within `tol` of every point added? */
  holds(b: Vec2): boolean {
    if (this.lo === -Infinity) return true
    if (this.lo > this.hi) return false
    const r = Math.hypot(b[0] - this.a[0], b[1] - this.a[1])
    if (r <= 1e-9) return false
    const t = this.angle(b)
    return t >= this.lo && t <= this.hi
  }
}

/**
 * Drop points while the line between the points kept passes within `tol` pixels of every point
 * dropped. Draped edges carry a point per grid node; on screen most of them are straight.
 */
export const simplify = (pts: readonly Vec2[], tol: number): Vec2[] => {
  if (pts.length <= 3) return pts.slice()
  const out: Vec2[] = [pts[0]]
  const sleeve = new Sleeve(tol)
  sleeve.reset(pts[0])
  for (let i = 1; i < pts.length - 1; i++) {
    sleeve.add(pts[i])
    if (!sleeve.holds(pts[i + 1])) {
      out.push(pts[i])
      sleeve.reset(pts[i])
    }
  }
  out.push(pts[pts.length - 1])
  return out
}

/**
 * Which points to keep when simplifying to within `tol`: like `simplify`, but points marked in
 * `fixed` are always kept, and points `may` refuses are never kept unless fixed.
 */
const keptPoints = (pts: readonly Vec2[], fixed: Uint8Array, tol: number, may: (k: number) => boolean = () => true): Uint8Array => {
  const keep = new Uint8Array(pts.length)
  if (pts.length === 0) return keep
  keep[0] = 1
  keep[pts.length - 1] = 1
  const sleeve = new Sleeve(tol)
  sleeve.reset(pts[0])
  for (let k = 1; k < pts.length - 1; k++) {
    if (fixed[k] === 1) { keep[k] = 1; sleeve.reset(pts[k]); continue }
    if (!may(k)) continue
    sleeve.add(pts[k])
    // The next point that may be kept stands in for the line's far end.
    let n = k + 1
    while (n < pts.length - 1 && fixed[n] !== 1 && !may(n)) n++
    if (!sleeve.holds(pts[n])) { keep[k] = 1; sleeve.reset(pts[k]) }
  }
  return keep
}

/** Path data, relative after the first point, in tenths of a unit. */
const pathOf = (input: readonly Vec2[], close = true, tol = 0) => {
  const pts = tol > 0 ? simplify(input, tol) : input
  let d = ''
  let px = 0
  let py = 0
  let lines = 0
  pts.forEach((p, i) => {
    const x = Math.round(p[0] * 10)
    const y = Math.round(p[1] * 10)
    if (i === 0) d += 'M' + pair(num(x), num(y))
    else {
      const dx = x - px
      const dy = y - py
      if (dx === 0 && dy === 0) return
      // After the first relative lineto, further pairs continue it implicitly.
      d += (lines === 0 ? 'l' : ' ') + pair(num(dx), num(dy))
      lines++
    }
    px = x
    py = y
  })
  return d + (close ? 'z' : '')
}
/** Draped ground: simplified to a quarter pixel. */
const groundPath = (pts: readonly Vec2[], close = true) => pathOf(pts, close, 0.25)

/** A dot is a zero-length stroke with round caps: the shortest circle SVG has. */
const dot = ([x, y]: Vec2) => 'M' + pair(num(Math.round(x * 10)), num(Math.round(y * 10))) + 'h0'

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;')

export interface Rendered {
  readonly svg: string
  readonly viewBox: readonly [number, number, number, number]
  readonly stats: Record<string, number>
}

/** Insert points along every edge so no edge is longer than `step`: draped edges bend. */
const densify = (ring: readonly Vec2[], step: number, closed = true): Vec2[] => {
  const out: Vec2[] = []
  const n = ring.length
  for (let i = 0; i < (closed ? n : n - 1); i++) {
    const a = ring[i]
    const b = ring[(i + 1) % n]
    out.push(a)
    const len = Math.hypot(b[0] - a[0], b[1] - a[1])
    const k = Math.floor(len / step)
    for (let m = 1; m <= k; m++) {
      const u = m / (k + 1)
      out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u])
    }
  }
  if (!closed && n > 0) out.push(ring[n - 1])
  return out
}

/** Layers drawn on the water's surface rather than the ground's. */
/** Pixels per meter at and above which tracks are drawn with ties and running rails. */
export const CLOSE_RAIL = 1.5

const WATERY = new Set(['W', 'canal', 'weir'])

interface Entry { rings: Ring[]; minN: number; maxN: number }
interface Layer { cls: string; entries: Entry[] }

const entryOf = (rings: Ring[]): Entry => {
  let minN = Infinity
  let maxN = -Infinity
  for (const ring of rings) for (const p of ring) { minN = Math.min(minN, p[1]); maxN = Math.max(maxN, p[1]) }
  return { rings, minN, maxN }
}

export const renderSvg = (scene: Scene): Rendered => {
  const { view, palette: p, region, terrain: T } = scene
  const fr = view.frame
  const slab = region.slab ?? 14
  const opts = region.terrain ?? {}
  const c = T.cell
  const stats: Record<string, number> = {}
  const P = (pt: Vec2, z = 0) => view.toScreen(pt, z)
  const drape = (pt: Vec2) => P(pt, T.z(pt))
  /** Water lies on the river's surface, wherever its outline reaches. */
  const drapeWater = (pt: Vec2) => P(pt, T.waterZ(pt))

  const items = paintOrder(scene.items)
  const close = view.scale >= CLOSE_RAIL

  // ---- the frame on screen -------------------------------------------------------------------
  const xs: number[] = []
  for (let e = fr.minX; e < fr.maxX; e += c) xs.push(e)
  xs.push(fr.maxX)
  const front = xs.map((e) => drape([e, fr.minY]))
  const [x0] = P([fr.minX, 0])
  const [x1] = P([fr.maxX, 0])
  let top = Infinity
  // One bad coordinate must not take the whole frame with it: skip anything not finite.
  for (const it of items) for (const s of it.shapes) for (const pt of s.pts) if (pt[1] < top) top = pt[1]
  for (let n = fr.minY; n <= fr.maxY + 1e-6; n += c) for (const e of xs) { const y = drape([e, n])[1]; if (y < top) top = y }
  const bottom = P([0, fr.minY], -slab)[1]
  const pad = 24
  // A dated scene carries its year as a caption above the plate, in room of its own.
  const capSize = scene.time === undefined ? 0 : Math.max(28, (x1 - x0) * 0.022)
  const capRoom = scene.time === undefined ? 0 : capSize * 2.4
  const vb: [number, number, number, number] = [x0 - pad, top - pad - capRoom, x1 - x0 + 2 * pad, bottom - top + 2 * pad + capRoom]

  const out: string[] = []
  const sealed = (cls: string, fill: string) => `.${cls}{fill:${fill};stroke:${fill};stroke-width:.6;stroke-linejoin:round}`
  out.push(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.map(f).join(' ')}" class="isoscape" data-region="${esc(region.name)}" role="img">`,
    `<title>${esc(region.title)}</title>`,
    `<desc>Map data © OpenStreetMap contributors (ODbL).${T.flat ? '' : ` ${esc(demCredit(region))}.`} Bearing ${view.bearing.toFixed(1)}°.</desc>`,
    `<style>`,
    `.i{stroke:${p.ink};stroke-width:${p.lineWidth};stroke-linejoin:round}.d{fill:none;stroke:${p.ink};stroke-width:${f(p.dotRadius * 2)};stroke-linecap:round}`,
    `.td{fill:none;stroke:${p.ink};stroke-width:${p.lineWidth};stroke-dasharray:1.2 1.8}`,
    sealed('L', p.land), sealed('Lw', p.water),
    ...Object.entries(p.cover).map(([g, color]) => sealed(`cv-${g}`, color)), sealed('I', p.land), sealed('W', p.water), sealed('green', p.green), sealed('wood', p.wood), sealed('marsh', p.marsh), sealed('sand', p.sand), sealed('rock', p.rock),
    sealed('parking', p.parking), sealed('cemetery', p.cemetery), sealed('plan', p.plan), sealed('grounds', p.grounds), sealed('racetrack', p.racetrack), sealed('burned', p.burned), sealed('platform', p.platform), sealed('canal', p.water), sealed('path', p.path),
    sealed('road', p.road), sealed('rail', scene.boldRail ? p.railTie : p.rail), sealed('tram', p.tram), sealed('weir', p.foam),
    // At close scale (CLOSE_RAIL px per meter or more) a track shows its ties, about 0.25 m
    // wide every 0.67 m across 2 m of the ribbon, and its two running rails, 1.44 m apart.
    close
      ? `.ties{fill:none;stroke:${p.railTie};stroke-width:${f(view.scale * 2 * view.squash)};stroke-dasharray:${f(view.scale * 0.25)} ${f(view.scale * 0.42)};stroke-opacity:.75}.steel{fill:none;stroke:${p.railSteel};stroke-width:${f(Math.max(p.groundLineWidth, view.scale * 0.12))}}`
      : `.ties{fill:none;stroke:${p.railTie};stroke-width:${p.groundLineWidth * 2};stroke-dasharray:1 2.2}`,
    `.crest{fill:none;stroke:${p.ink};stroke-width:${p.groundLineWidth};stroke-opacity:.6}`,
    `.cm{fill:none;stroke:${p.ink};stroke-width:${p.groundLineWidth};stroke-opacity:${p.contourMinor}}`,
    `.cM{fill:none;stroke:${p.ink};stroke-width:${p.groundLineWidth * 1.6};stroke-opacity:${p.contourMajor}}`,
    `.foam{fill:none;stroke:${p.foam};stroke-width:${f(p.lineWidth * 1.6)};stroke-linecap:round}`,
    `.froth{fill:${p.foam}}`,
    `.boulder{fill:${p.boulder};stroke:${p.ink};stroke-width:${p.groundLineWidth};stroke-opacity:.7;stroke-linejoin:round}`,
    `.edge{fill:none;stroke:${p.ink};stroke-width:${p.lineWidth}}`,
    // Hillshade bands: hp1… lit, hm1… shaded. The bands nest (each lies inside the one before),
    // so each class carries only what its band adds to the one below it.
    ...(T.flat ? [] : shadeAlphas(p.shadeLightStep, p.shadeMax).map((a, k) => `.hp${k + 1}{fill:${p.shadeLight};fill-opacity:${a.toFixed(4)}}`)),
    ...(T.flat ? [] : shadeAlphas(p.shadeDarkStep, p.shadeMax).map((a, k) => `.hm${k + 1}{fill:${p.shadeDark};fill-opacity:${a.toFixed(4)}}`)),
    `</style>`,
    `<rect x="${f(vb[0])}" y="${f(vb[1])}" width="${f(vb[2])}" height="${f(vb[3])}" fill="${p.sky}"/>`,
  )

  // ---- the slab: a cut through the ground along the front edge -------------------------------
  if (slab > 0) {
    const yBase = P([0, fr.minY], -slab)[1]
    out.push(`<path class="i" fill="${p.slab}" d="${pathOf([...front, [x1, yBase], [x0, yBase]])}"/>`)
    // Water in the cut, where the front edge crosses open water: with terrain, from shoreline
    // to shoreline as traced (see shoreField), and only where it is two cells wide or more. A
    // stream a node wide had cut a blue stripe down the whole face of the slab.
    const jFront = Math.round((fr.minY - T.y0) / c)
    const wetOf = (e: number) => {
      const k = jFront * T.nx + Math.round((e - T.x0) / c)
      return T.flat ? T.water[k] : T.shore[k]
    }
    const v = xs.map(wetOf)
    const at = (k: number): Vec2 => {
      // Where the front edge crosses the shoreline between xs[k] and xs[k + 1].
      const u = T.flat ? 0 : Math.max(0, Math.min(1, (0.5 - v[k]) / (v[k + 1] - v[k])))
      return [xs[k] + (xs[k + 1] - xs[k]) * u, fr.minY]
    }
    let k = 0
    while (k < xs.length) {
      if (v[k] < 0.5) { k++; continue }
      let m = k
      while (m + 1 < xs.length && v[m + 1] >= 0.5) m++
      const start: Vec2 = k > 0 && !T.flat ? at(k - 1) : [xs[k], fr.minY]
      const end: Vec2 = m + 1 < xs.length && !T.flat ? at(m) : [xs[m], fr.minY]
      if (end[0] - start[0] >= 2 * c - 1e-6) {
        const pts = [drape(start), ...front.slice(k, m + 1), drape(end)]
        out.push(`<path fill="${p.slabWater}" d="${pathOf([...pts, [pts[pts.length - 1][0], yBase], [pts[0][0], yBase]])}"/>`)
      }
      k = m + 1
    }
  }

  // ---- ground layers, indexed for strip lookup -------------------------------------------------
  const water = scene.ground.filter((g) => g.kind === 'water')
  const islands = scene.ground.filter((g) => g.kind === 'island')
  const wetAt = (pt: Vec2) => {
    const i = Math.round((pt[0] - T.x0) / c)
    const j = Math.round((pt[1] - T.y0) / c)
    return i >= 0 && j >= 0 && i < T.nx && j < T.ny && T.water[j * T.nx + i] === 1
  }
  const cover = scene.ground.filter((g) => GROUND_ORDER.includes(g.kind))
  // Cover that sits in the river (vegetation on its islands and rocks) paints over the water;
  // everything else paints under it, so a park drawn across the river is covered by it. In
  // the river means mostly over water, judged on up to about 400 points spread over it: a
  // park round a pond can have its middle in the pond.
  const inRiver = (g: (typeof cover)[number]): boolean => {
    let minX = Infinity
    let maxX = -Infinity
    let minY = Infinity
    let maxY = -Infinity
    for (const r of g.rings) for (const [x, y] of r) { minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y) }
    const step = Math.max(c, Math.sqrt(((maxX - minX) * (maxY - minY)) / 400))
    let inside = 0
    let wet = 0
    for (let y = minY + step / 2; y < maxY; y += step) {
      for (let x = minX + step / 2; x < maxX; x += step) {
        if (!pointInPolygon([x, y], g.rings)) continue
        inside++
        if (wetAt([x, y])) wet++
      }
    }
    // Smaller than a cell: its middle decides.
    if (inside === 0) return wetAt([(minX + maxX) / 2, (minY + maxY) / 2])
    return wet * 2 > inside
  }
  const coverLayers = (after: boolean): Layer[] =>
    GROUND_ORDER.map((kind) => ({
      cls: kind,
      entries: cover.filter((g) => g.kind === kind && inRiver(g) === after).map((g) => entryOf(g.rings)),
    }))
  const ribbonLayer = (kind: string): Layer => ({
    cls: kind,
    entries: scene.ribbons.filter((rb) => rb.kind === kind).flatMap((rb) => rb.quads.map((q) => entryOf([q]))),
  })
  // Cover on land paints under the water: with terrain, the water comes from the grid and is
  // painted first in each strip, so this cover goes in ahead of it (see paintStrip).
  const underWater: Layer[] = coverLayers(false)
  const layers: Layer[] = [
    // OSM's water outline draws a flat scene's shore; with terrain the water grid does.
    { cls: 'W', entries: T.flat ? water.map((g) => entryOf(g.rings)) : [] },
    { cls: 'I', entries: T.flat ? islands.map((g) => entryOf(g.rings)) : [] },
    ...coverLayers(true),
    ribbonLayer('canal'),
    ribbonLayer('weir'),
    ribbonLayer('path'),
    ribbonLayer('racetrack'),
    ribbonLayer('road'),
    ribbonLayer('rail'),
    ribbonLayer('tram'),
  ]
  const lineLayer = (kind: string, cls: string) => ({
    cls,
    segs: scene.ribbons.filter((rb) => rb.kind === kind).flatMap((rb) => rb.center),
  })
  const railCenters = lineLayer('rail', 'ties').segs
  const gauge = (k: number): Vec2[][] => railCenters.map(([a, b]) => {
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
    const nx = ((b[1] - a[1]) / len) * k
    const ny = (-(b[0] - a[0]) / len) * k
    return [[a[0] + nx, a[1] + ny], [b[0] + nx, b[1] + ny]]
  })
  const lineLayers = [
    lineLayer('rail', 'ties'),
    ...(close ? [{ cls: 'steel', segs: [...gauge(0.72), ...gauge(-0.72)] }] : []),
    lineLayer('weir', 'crest'),
  ]

  // ---- terrain extras -------------------------------------------------------------------------
  const interval = opts.contour ?? 2
  const allContours: ContourSegment[] = T.flat || interval <= 0 ? [] : contours(T, interval, opts.majorEvery ?? 5)
  const contoursByRow = new Map<number, ContourSegment[]>()
  for (const s of allContours) {
    const list = contoursByRow.get(s.row)
    if (list) list.push(s)
    else contoursByRow.set(s.row, [s])
  }
  stats.contourSegments = allContours.length
  const rapidsThreshold = opts.rapids ?? 0.035
  let rapidCells = 0

  // ---- strips -----------------------------------------------------------------------------------
  // Two grid rows per strip, aligned to the grid, from the far edge to the near.
  const jNear = Math.round((fr.minY - T.y0) / c)
  const jFar = Math.round((fr.maxY - T.y0) / c)
  interface Strip { j0: number; j1: number; n0: number; n1: number }
  const strips: Strip[] = []
  for (let j1 = jFar; j1 > jNear; j1 -= 2) {
    const j0 = Math.max(jNear, j1 - 2)
    strips.push({ j0, j1, n0: Math.max(fr.minY, T.y0 + j0 * c), n1: Math.min(fr.maxY, T.y0 + j1 * c) })
  }
  // The ground reaches a cell past the plate's sides, which are then covered in paper (see
  // the items below): cut at the sides by its own edges, it showed a dotted pale line there.
  const nodeX = (i: number) => T.x0 + i * c
  const iMin = Math.max(0, Math.round((fr.minX - T.x0) / c) - 1)
  const iMax = Math.min(T.nx - 1, Math.ceil((fr.maxX - T.x0) / c) + 1)
  // Light from the left and a little toward the camera, so the slopes we look at are lit and
  // the backs of hills fall into shade.
  const light = normalize([-0.85, -0.35, 1.0])
  // The shade field, in steps (one step is 1/22 of light · normal), at every node. The
  // river's surface is not shaded: the bands are cut at the traced shoreline (see below).
  const litField = new Float32Array(T.elev.length)
  const darkField = new Float32Array(T.elev.length)
  // With terrain, the traced shoreline says which nodes are wet (see shoreField); flat, the grid.
  const wetNodes = T.flat ? T.water : Uint8Array.from(T.shore, (v) => (v >= 0.5 ? 1 : 0))
  const wetNode = (k: number) => wetNodes[k]
  /** 1 for each cell (by its first node) that is part water and part land. */
  const shoreCells = new Uint8Array(T.nx * T.ny)
  for (let j = 0; j + 1 < T.ny; j++) {
    for (let i = 0; i + 1 < T.nx; i++) {
      const k = j * T.nx + i
      const n = wetNodes[k] + wetNodes[k + 1] + wetNodes[k + T.nx] + wetNodes[k + T.nx + 1]
      if (n > 0 && n < 4) shoreCells[k] = 1
    }
  }
  const wetCorners = (i: number, j: number) =>
    wetNodes[j * T.nx + i] + wetNodes[j * T.nx + i + 1] + wetNodes[(j + 1) * T.nx + i] + wetNodes[(j + 1) * T.nx + i + 1]
  /**
   * Is cell (i, j) water in the strip base? With terrain, only cells wholly in the water: the
   * shoreline is traced separately. Flat, a majority will do, and OSM's outline draws the shore.
   */
  const baseWet = (i: number, j: number) => wetCorners(i, j) >= (T.flat ? 2 : 4)
  // The shoreline, for terrain: one half of a field that follows the mapped outline between
  // the grid's nodes (see shoreField).
  const wetness = T.shore
  const dryness = wetness.map((v) => 1 - v)
  // Land cover: each group's field, blurred and traced at one half (see coverFields), cut at
  // the shoreline.
  const coverFields = new Map<CoverGroup, Float32Array>()
  if (T.cover.some((v) => v !== 0)) {
    const skip = (k: number) => T.cover[k] === 0 || T.cover[k] === 11 || wetNode(k) === 1
    for (const [g, field] of coverFieldsOf(T.cover, T.nx, T.ny, c, skip)) {
      for (let k = 0; k < field.length; k++) field[k] = Math.min(field[k], dryness[k])
      if (field.some((v) => v >= 0.5)) coverFields.set(g, field)
    }
  }
  /** The part of cell (i, j) where `field` is at least one half, as a polygon in view meters. */
  const traceCell = (field: Float32Array, i: number, j: number, yLo: number, yHi: number): Vec2[] | null => {
    const k = j * T.nx + i
    if (field[k] < 0.5 && field[k + 1] < 0.5 && field[k + T.nx] < 0.5 && field[k + T.nx + 1] < 0.5) return null
    const xa = nodeX(i)
    const xb = nodeX(i + 1)
    const corners: [Vec2, number][] = [
      [[xa, yLo], field[j * T.nx + i]],
      [[xb, yLo], field[j * T.nx + i + 1]],
      [[xb, yHi], field[(j + 1) * T.nx + i + 1]],
      [[xa, yHi], field[(j + 1) * T.nx + i]],
    ]
    const out: Vec2[] = []
    for (let k = 0; k < 4; k++) {
      const [pa, va] = corners[k]
      const [pb, vb] = corners[(k + 1) % 4]
      if (va >= 0.5) out.push(pa)
      if ((va >= 0.5) !== (vb >= 0.5)) {
        const u = (0.5 - va) / (vb - va)
        out.push([pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u])
      }
    }
    return out.length >= 3 ? out : null
  }

  if (!T.flat) {
    const shade = nodeShade(T, light)
    for (let k = 0; k < shade.length; k++) {
      litField[k] = shade[k] * SHADE_GAIN
      darkField[k] = -shade[k] * SHADE_GAIN
    }
    // Over the water the shading is held down, except at nodes beside the land: there it
    // carries on as the land beside it has it, across the shoreline, and the shoreline itself
    // cuts it (see shadeStrip). Held down at every wet node, each band ended partway across
    // the cell between a wet node and a dry one, wherever its value happened to fall, and
    // along a shore that crosses the grid the shading showed the grid's teeth.
    const lit = litField.slice()
    const dark = darkField.slice()
    for (let j = 0; j < T.ny; j++) {
      for (let i = 0; i < T.nx; i++) {
        const k = j * T.nx + i
        if (wetNode(k) !== 1) continue
        let l = -SHORE_CAP
        let d = -SHORE_CAP
        for (let dj = -1; dj <= 1; dj++) {
          for (let di = -1; di <= 1; di++) {
            const ii = i + di
            const jj = j + dj
            if (ii < 0 || jj < 0 || ii >= T.nx || jj >= T.ny) continue
            const q = jj * T.nx + ii
            if (wetNode(q) === 1) continue
            l = Math.max(l, lit[q])
            d = Math.max(d, dark[q])
          }
        }
        litField[k] = l
        darkField[k] = d
      }
    }
  }
  /**
   * The water within view-meter rows [lo, hi], as path data for holes in a clip: traced as
   * whole rings (see isoBand), so no two holes share an edge, where a clip's antialiasing let a
   * hairline through.
   */
  const waterHoles = (lo: number, hi: number): string => {
    const jA = Math.max(0, Math.floor((lo - T.y0) / c))
    const jB = Math.min(T.ny - 1, Math.ceil((hi - T.y0) / c))
    let d = ''
    // Cut to [lo, hi]: water further off lies under ground of this strip's that stands in
    // front of it, and must not be cut out of that ground's shading.
    const rows: Rect = { minX: -Infinity, maxX: Infinity, minY: lo, maxY: hi }
    for (const ring of isoBand(wetness, T.nx, iMin, iMax, jA, jB, 0.5)) {
      const cut = clipRingToRect(ring.map((q): Vec2 => [T.x0 + q.i * c, T.y0 + q.j * c]), rows)
      if (cut.length >= 3) d += pathOf(alongShore(densify(cut, c), true).map(drape), true, 0.25)
    }
    return d
  }
  // Each strip's shading reaches this far past its far edge, and stops this far short of its
  // near edge: as far as the next strip's ground layers lap back over it (0.6 m), plus their
  // sealing strokes. Those laps then fall under the shading of the strip that drew them, and
  // ground the laps do not cover is shaded once, by that same strip.
  const shadeLap = 0.6 + 0.6 / (view.scale * view.squash)
  const nodes = iMax - iMin + 1
  /** The shade fields along view-meter line n, interpolated between grid rows. */
  const fieldRow = (field: Float32Array, n: number, into: Float32Array, at: number) => {
    const g = (n - T.y0) / c
    const j = Math.min(T.ny - 2, Math.floor(g + 1e-9))
    const u = Math.max(0, g - j)
    for (let i = 0; i < nodes; i++) {
      const lo = field[j * T.nx + iMin + i]
      into[at + i] = u < 1e-9 ? lo : lo + (field[(j + 1) * T.nx + iMin + i] - lo) * u
    }
  }
  // Along each row line, which nodes survive simplification of the draped line as a whole. A
  // band edge running along a strip's boundary keeps exactly these nodes (and its own
  // crossings), so the strips on either side draw the same line and meet without a hairline.
  const rowKeep = new Map<number, Uint8Array>()
  const keepOnRow = (n: number): Uint8Array => {
    let keep = rowKeep.get(n)
    if (keep === undefined) {
      const pts: Vec2[] = []
      for (let i = iMin; i <= iMax; i++) pts.push(drape([nodeX(i), n]))
      keep = keptPoints(pts, new Uint8Array(pts.length), 0.25)
      rowKeep.set(n, keep)
    }
    return keep
  }
  /** A ring from `isoBand` over a strip's rows (`ys`, view meters), as draped path data. */
  const bandPath = (input: readonly BandPoint[], ys: readonly number[]): string => {
    const yOf = (lj: number) => {
      const r = Math.min(ys.length - 2, Math.floor(lj))
      return ys[r] + (ys[r + 1] - ys[r]) * (lj - r)
    }
    // A node on a boundary line that the line's own simplification dropped may not be kept.
    // Start the ring at a point that may, and close it on that point again, so simplification
    // never has to keep one.
    const rowNode = (q: BandPoint) => q.onRow && q.i === Math.floor(q.i)
    const may = (q: BandPoint) => !rowNode(q) || keepOnRow(ys[q.j])[q.i] === 1
    const s0 = Math.max(0, input.findIndex(may))
    const ring = [...input.slice(s0), ...input.slice(0, s0), input[s0]]
    const pts: Vec2[] = []
    const fixedList: number[] = []
    const mayList: boolean[] = []
    let prev: Vec2 | null = null
    ring.forEach((q) => {
      const i = Math.floor(q.i)
      const x = q.i === i ? nodeX(iMin + i) : nodeX(iMin + i) + (nodeX(iMin + i + 1) - nodeX(iMin + i)) * (q.i - i)
      const v: Vec2 = [x, yOf(q.j)]
      // Where the band crosses the shoreline, it bends there as the ground does: drawn
      // straight across, from the bank down to a wet node, it stood clear of the ground and
      // shaded the water behind it.
      if (prev !== null) {
        for (const w of shoreCrossings(prev, v)) {
          pts.push(drape(w))
          fixedList.push(0)
          mayList.push(true)
        }
      }
      pts.push(drape(v))
      fixedList.push(q.onRow && may(q) ? 1 : 0)
      mayList.push(may(q))
      prev = v
    })
    const keep = keptPoints(pts, Uint8Array.from(fixedList), 0.5, (k) => mayList[k])
    return pathOf(pts.filter((_, k) => keep[k] === 1 && k < pts.length - 1))
  }
  /**
   * The line through `pts` with a point added wherever it crosses the traced shoreline, so that
   * draped it bends there as the ground does (see Terrain.z): drawn straight across a shore
   * cell, from up the bank to a point on the water, a road or a beach stood clear of the
   * ground and showed over what lay behind it.
   */
  /** Does the box around a–b touch a cell that is part water, part land? */
  const nearShore = (a: Vec2, b: Vec2): boolean => {
    const i0 = Math.max(0, Math.floor((Math.min(a[0], b[0]) - T.x0) / c))
    const i1 = Math.min(T.nx - 2, Math.floor((Math.max(a[0], b[0]) - T.x0) / c))
    const j0 = Math.max(0, Math.floor((Math.min(a[1], b[1]) - T.y0) / c))
    const j1 = Math.min(T.ny - 2, Math.floor((Math.max(a[1], b[1]) - T.y0) / c))
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) if (shoreCells[j * T.nx + i] === 1) return true
    return false
  }
  const alongShore = (pts: readonly Vec2[], closed: boolean): Vec2[] => {
    if (T.flat) return pts.slice()
    const out: Vec2[] = []
    const n = pts.length
    for (let k = 0; k < (closed ? n : n - 1); k++) {
      const a = pts[k]
      const b = pts[(k + 1) % n]
      out.push(a)
      if (!nearShore(a, b)) continue
      // Cut a–b where it crosses grid lines, so each piece lies in one cell.
      const ts = [0, 1]
      const dx = b[0] - a[0]
      const dy = b[1] - a[1]
      if (Math.abs(dx) > 1e-9) {
        const lo = Math.ceil((Math.min(a[0], b[0]) - T.x0) / c)
        const hi = Math.floor((Math.max(a[0], b[0]) - T.x0) / c)
        for (let i = lo; i <= hi; i++) ts.push((T.x0 + i * c - a[0]) / dx)
      }
      if (Math.abs(dy) > 1e-9) {
        const lo = Math.ceil((Math.min(a[1], b[1]) - T.y0) / c)
        const hi = Math.floor((Math.max(a[1], b[1]) - T.y0) / c)
        for (let j = lo; j <= hi; j++) ts.push((T.y0 + j * c - a[1]) / dy)
      }
      ts.sort((u, v) => u - v)
      for (let m = 0; m + 1 < ts.length; m++) {
        if (ts[m + 1] - ts[m] < 1e-9) continue
        const p: Vec2 = [a[0] + dx * ts[m], a[1] + dy * ts[m]]
        const q: Vec2 = [a[0] + dx * ts[m + 1], a[1] + dy * ts[m + 1]]
        out.push(...shoreCrossings(p, q))
      }
    }
    if (!closed && n > 0) out.push(pts[n - 1])
    return out
  }
  /**
   * Where the segment a–b (view meters, within one cell) crosses the cell's traced shoreline,
   * in order from a: none unless the cell is part water and part land.
   */
  const shoreCrossings = (a: Vec2, b: Vec2): Vec2[] => {
    if (T.flat) return []
    const ci = Math.floor(((a[0] + b[0]) / 2 - T.x0) / c)
    const cj = Math.floor(((a[1] + b[1]) / 2 - T.y0) / c)
    if (ci < 0 || cj < 0 || ci >= T.nx - 1 || cj >= T.ny - 1) return []
    const n = wetCorners(ci, cj)
    if (n === 0 || n === 4) return []
    const xa = T.x0 + ci * c
    const ya = T.y0 + cj * c
    const corners: [Vec2, number][] = [
      [[xa, ya], wetness[cj * T.nx + ci]],
      [[xa + c, ya], wetness[cj * T.nx + ci + 1]],
      [[xa + c, ya + c], wetness[(cj + 1) * T.nx + ci + 1]],
      [[xa, ya + c], wetness[(cj + 1) * T.nx + ci]],
    ]
    const cross: Vec2[] = []
    for (let k = 0; k < 4; k++) {
      const [pa, va] = corners[k]
      const [pb, vb] = corners[(k + 1) % 4]
      if ((va >= 0.5) === (vb >= 0.5)) continue
      const u = (0.5 - va) / (vb - va)
      cross.push([pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u])
    }
    const out: [number, Vec2][] = []
    const dx = b[0] - a[0]
    const dy = b[1] - a[1]
    for (let k = 0; k + 1 < cross.length; k += 2) {
      const [p, q] = [cross[k], cross[k + 1]]
      const ex = q[0] - p[0]
      const ey = q[1] - p[1]
      const den = dx * ey - dy * ex
      if (Math.abs(den) < 1e-12) continue
      const t = ((p[0] - a[0]) * ey - (p[1] - a[1]) * ex) / den
      const u = ((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / den
      if (t > 1e-6 && t < 1 - 1e-6 && u >= 0 && u <= 1) out.push([t, [a[0] + dx * t, a[1] + dy * t]])
    }
    return out.sort((x, y) => x[0] - y[0]).map(([, v]) => v)
  }
  /** A strip's hillshade: nested bands, lit and shaded, one path per band. */
  const shadeStrip = (s: Strip, dry: string): string => {
    const lo = s.n0 > fr.minY ? s.n0 + shadeLap : s.n0
    const hi = s.n1 < fr.maxY ? s.n1 + shadeLap : s.n1
    const ys = [lo]
    for (let j = Math.floor((lo - T.y0) / c) + 1; T.y0 + j * c < hi - 1e-6; j++) if (T.y0 + j * c > lo + 1e-6) ys.push(T.y0 + j * c)
    ys.push(hi)
    let out = ''
    for (const [field, cls] of [[litField, 'hp'], [darkField, 'hm']] as const) {
      const local = new Float32Array(ys.length * nodes)
      ys.forEach((n, r) => fieldRow(field, n, local, r * nodes))
      let top = -Infinity
      for (const v of local) top = Math.max(top, v)
      for (let m = 1; m <= SHADE_BANDS && bandThreshold(m) <= top; m++) {
        let d = ''
        for (const ring of isoBand(local, nodes, 0, nodes - 1, 0, ys.length - 1, bandThreshold(m))) d += bandPath(ring, ys)
        if (d) out += `<path class="${cls}${m}" d="${d}"/>`
      }
    }
    // The shading stops at the shoreline: the strip's water is cut out of it (see paintStrip).
    return out && dry !== '' ? `<g clip-path="url(#${dry})">${out}</g>` : out
  }

  const paintStrip = (s: Strip) => {
    // Strips overlap their neighbors so no background shows between them, and no two edges
    // may coincide: where two anti-aliased edges land on the same pixel row, a browser
    // scaling the image down shows a faint stripe. So the bare ground reaches a little past the
    // far edge, everything on it reaches further, and everything but the ground reaches past
    // the near edge too; each edge then falls inside something painted later.
    // The base laps toward the camera, by most of a strip (more than a pixel even zoomed
    // right out), into ground the next strip
    // always repaints; it never laps away from the camera, where it could cover a building
    // standing in the strip before.
    const lapNear = s.n0 > fr.minY ? Math.min(8, (s.n1 - s.n0) * 0.8) : 0
    const lapFar = s.n1 < fr.maxY ? 0.6 : 0
    // Rows within a strip overlap a little too: their shared edges are simplified separately,
    // so they no longer meet exactly, and a hairline would show between them.
    const rowLap = c * 0.3
    // The bases stop short of the far edge, in ground the strip before has already lapped
    // over; what is drawn on them still reaches the edge. Their edges then never meet over
    // a different color, which is what shows as a hairline.
    const baseInset = s.n1 < fr.maxY ? Math.min(lapNear * 0.4, c * 0.25) : 0
    const groundFar = 0
    const band: Rect = { minX: fr.minX - c, maxX: fr.maxX + c, minY: s.n0 - lapNear, maxY: s.n1 + lapFar }
    const parts: string[] = []
    // The rows the strip's ground covers: its own, and those its lap toward the camera falls
    // in, each cut to the part the strip paints. Each keeps its own cells: a lap drawn by
    // stretching the strip's first row over the next strip's ground put that row's shore
    // there, out of step with the next strip's, and the shore showed a saw's teeth.
    const lapTo = s.n0 - lapNear
    const rows: { j: number; lo: number; hi: number; yLo: number; top: boolean }[] = []
    for (let j = Math.max(0, Math.floor((lapTo - T.y0) / c + 1e-9)); j < s.j1; j++) {
      const lo = T.y0 + j * c
      const hi = T.y0 + (j + 1) * c
      if (hi <= lapTo) continue
      const top = j === s.j1 - 1
      rows.push({ j, lo, hi, yLo: Math.max(lapTo, lo - rowLap), top })
    }
    /** Cell (i, j)'s part of `field` at one half, traced in the cell and cut to [yLo, yHi]. */
    const tracedIn = (field: Float32Array, i: number, r: (typeof rows)[number], yLo: number, yHi: number): Vec2[] | null => {
      const poly = traceCell(field, i, r.j, r.lo, r.hi)
      if (poly === null || (yLo <= r.lo && yHi >= r.hi)) return poly
      const cut = clipRingToRect(poly, { minX: -Infinity, maxX: Infinity, minY: yLo, maxY: yHi })
      return cut.length >= 3 ? cut : null
    }
    // The strip's base: its own surface, cell row by cell row, colored water where the grid
    // is water and land elsewhere. It hides what lies behind a rise, and because it already
    // matches what is drawn on it, no seam can leak a wrong color through.
    let landBase = ''
    let waterBase = ''
    for (const r of rows) {
      const j = r.j
      const yLo = r.yLo
      const yHi = r.top ? s.n1 - baseInset : r.hi
      // Water reaches the far edge, over the cover painted under it (see underWater).
      const yWet = r.top ? s.n1 : yHi
      // Each cell is land (0), water (1) or, with terrain, part of each (2): the land part of
      // that is traced up to the shoreline, and the shore pass below paints the rest as water.
      // Painted whole, its wet part stood above the water on the bank's slope, and the next
      // strip's showed over this one's shore as a tooth.
      const kindOf = (i: number) => (T.flat ? (baseWet(i, j) ? 1 : 0) : baseWet(i, j) ? 1 : wetCorners(i, j) === 0 ? 0 : 2)
      let start = iMin
      let kind = kindOf(start)
      for (let i = iMin + 1; i <= iMax; i++) {
        const w = i < iMax ? kindOf(i) : -1
        if (w === kind && kind !== 2) continue
        if (kind === 2) {
          const poly = tracedIn(dryness, start, r, Math.max(lapTo, r.lo), yHi)
          if (poly !== null) landBase += groundPath(poly.map(drape))
        } else {
          const wet = kind === 1
          const top: Vec2[] = []
          const bottom: Vec2[] = []
          const lay = wet ? drapeWater : drape
          for (let k = start; k <= i; k++) {
            top.push(lay([nodeX(k), wet ? yWet : yHi]))
            bottom.push(lay([nodeX(k), yLo]))
          }
          // Wound like the traced cells (along the near edge first), so overlaps add, not cancel.
          const d = groundPath([...bottom, ...top.reverse()])
          if (wet) waterBase += d
          else landBase += d
        }
        start = i
        kind = w
      }
    }
    if (landBase) parts.push(`<path class="L" d="${landBase}"/>`)
    // Land cover over the bare ground: whole cells merged into runs, edges traced through.
    for (const [g, field] of coverFields) {
      let d = ''
      for (const r of rows) {
        const j = r.j
        const yLo = r.yLo
        const yHi = r.top ? s.n1 + groundFar : r.hi
        let runStart = -1
        const full = (i: number) => field[j * T.nx + i] >= 0.5 && field[j * T.nx + i + 1] >= 0.5 && field[(j + 1) * T.nx + i] >= 0.5 && field[(j + 1) * T.nx + i + 1] >= 0.5
        const flushRun = (iEnd: number) => {
          if (runStart < 0) return
          const top: Vec2[] = []
          const bottom: Vec2[] = []
          for (let k = runStart; k <= iEnd; k++) {
            top.push(drape([nodeX(k), yHi]))
            bottom.push(drape([nodeX(k), yLo]))
          }
          d += groundPath([...bottom, ...top.reverse()])
          runStart = -1
        }
        for (let i = iMin; i < iMax; i++) {
          if (full(i)) {
            if (runStart < 0) runStart = i
            continue
          }
          flushRun(i)
          const poly = tracedIn(field, i, r, Math.max(lapTo, r.lo), yHi)
          if (poly !== null) d += groundPath(poly.map(drape))
        }
        flushRun(iMax)
      }
      if (d) parts.push(`<path class="cv-${g}" d="${d}"/>`)
    }
    const paintLayers = (list: readonly Layer[], band: Rect) => {
      for (const layer of list) {
        let d = ''
        for (const e of layer.entries) {
          if (e.maxN < s.n0 || e.minN > s.n1) continue
          for (const ring of e.rings) {
            const clipped = clipRingToRect(ring, band)
            if (clipped.length < 3) continue
            d += groundPath(WATERY.has(layer.cls) ? densify(clipped, c).map(drapeWater) : alongShore(densify(clipped, c), true).map(drape))
          }
        }
        if (d) parts.push(`<path class="${layer.cls}" d="${d}"/>`)
      }
    }
    // Parks, woods and the like that are not in the water go under it: a park drawn across a
    // lake (Central Park around the Lake) must not paint the lake over as lawn.
    // It stops a little short of the strip's far edge, where this strip's water reaches: the
    // strip before has lapped its own cover over that much, so on land nothing shows.
    // Everything but the strip's water, as a clip: the cover under the water and the shading
    // over the ground stop at the shoreline. Cover left under the water showed through the
    // seams between strips as faint lines across a lake, and shading held down over the water
    // ended short of the shore in teeth. The holes reach a little past what they cut at either
    // end, so its edges there are not also the clip's.
    let dry = ''
    if (!T.flat) {
      const reach = 2 / (view.scale * view.squash)
      const holes = waterHoles(lapTo - reach, s.n1 + shadeLap + reach)
      if (holes) {
        dry = `dry${strips.indexOf(s)}`
        parts.push(`<clipPath id="${dry}"><path clip-rule="evenodd" d="${pathOf([[vb[0], vb[1]], [vb[0] + vb[2], vb[1]], [vb[0] + vb[2], vb[1] + vb[3]], [vb[0], vb[1] + vb[3]]])}${holes}"/></clipPath>`)
      }
    }
    const under = parts.length
    paintLayers(underWater, { ...band, maxY: s.n1 - Math.min(0.3, baseInset / 2) })
    if (dry !== '' && parts.length > under) parts.push(`<g clip-path="url(#${dry})">${parts.splice(under).join('')}</g>`)
    // With terrain, the shoreline is traced (see shoreField), and each shore cell's wet part
    // is drawn on the ground there, which lies on the water's surface on that side of the line
    // (see Terrain.z). It goes in the same path as the wholly wet cells: drawn as a path of its
    // own, the two met along the cells' sides in a faint seam where the ground beneath showed.
    if (!T.flat) {
      for (const r of rows) {
        const yHi = r.top ? s.n1 + groundFar : r.hi
        for (let i = iMin; i < iMax; i++) {
          const n = wetCorners(i, r.j)
          if (n === 4 || n === 0) continue
          const poly = tracedIn(wetness, i, r, Math.max(lapTo, r.lo), yHi)
          if (poly !== null) waterBase += groundPath(poly.map(drape))
        }
      }
    }
    if (waterBase) parts.push(`<path class="Lw" d="${waterBase}"/>`)
    paintLayers(layers, band)
    for (const ll of lineLayers) {
      let d = ''
      for (const [a, b] of ll.segs) {
        const seg = clipSegmentToRect(a, b, band)
        if (seg === null) continue
        d += groundPath(alongShore(densify(seg, c, false), false).map(drape), false)
      }
      if (d) parts.push(`<path class="${ll.cls}" d="${d}"/>`)
    }
    if (!T.flat) {
      // Hillshade: nested iso-bands of the shade field, traced across the strip.
      const shading = shadeStrip(s, dry)
      if (shading) parts.push(shading)
      // Contours, over the same stretch as the shading: the next strip's ground laps back over
      // this one's near edge, so that strip draws the lines there, and they are not cut.
      let minor = ''
      let major = ''
      const lineBand: Rect = { ...band, minY: s.n0 > fr.minY ? s.n0 + shadeLap : s.n0, maxY: s.n1 < fr.maxY ? s.n1 + shadeLap : s.n1 }
      for (let j = s.j0; j <= s.j1; j++) {
        for (const seg of contoursByRow.get(j) ?? []) {
          const clipped = clipSegmentToRect(seg.a, seg.b, lineBand)
          if (clipped === null) continue
          const d = pathOf(alongShore(clipped, false).map(drape), false)
          if (seg.major) major += d
          else minor += d
        }
      }
      // They stop at the shoreline, like the shading: the ground's contours do not cross water.
      const lines = (minor ? `<path class="cm" d="${minor}"/>` : '') + (major ? `<path class="cM" d="${major}"/>` : '')
      if (lines) parts.push(dry !== '' ? `<g clip-path="url(#${dry})">${lines}</g>` : lines)
      // Rapids: where the river's surface falls, white strokes across the current.
      let foam = ''
      let froth = ''
      for (let j = s.j0; j < s.j1; j++) {
        for (let i = iMin; i < iMax; i++) {
          if (rapidsThreshold <= 0) continue
          const fall = riverFall(T, i, j)
          if (fall === null || fall.slope < rapidsThreshold) continue
          const slope = fall.slope
          rapidCells++
          const h = hash(`${i},${j}`)
          const strength = Math.min(1, (slope - rapidsThreshold) / (rapidsThreshold * 3))
          const cx = T.x0 + (i + 0.5) * c
          const cy = T.y0 + (j + 0.5) * c
          // Across the current: perpendicular to the downhill direction.
          const ux = -fall.down[1]
          const uy = fall.down[0]
          // Sparse and deliberate: one stroke for a riffle, two where it really drops.
          if (hash(`k${i},${j}`) % 3 === 0 && strength < 0.5) continue
          const marks = strength < 0.5 ? 1 : 2
          for (let m = 0; m < marks; m++) {
            const hm = hash(`${h}:${m}`)
            const jx = ((hm % 1000) / 1000 - 0.5) * c * 0.8
            const jy = (((hm >>> 10) % 1000) / 1000 - 0.5) * c * 0.8
            const len = c * (0.35 + 0.3 * (((hm >>> 20) % 100) / 100))
            const a: Vec2 = [cx + jx - ux * len, cy + jy - uy * len]
            const b: Vec2 = [cx + jx + ux * len, cy + jy + uy * len]
            foam += pathOf([drape(a), drape(b)], false)
          }
          const q: Vec2[] = [[cx - c / 2, cy - c / 2], [cx + c / 2, cy - c / 2], [cx + c / 2, cy + c / 2], [cx - c / 2, cy + c / 2]]
          if (strength > 0.3) froth += `<path class="froth" fill-opacity="${(0.1 + 0.25 * strength).toFixed(2)}" d="${pathOf(q.map(drape))}"/>`
        }
      }
      // Rock standing clear of the river: the boulder fields that make the falls.
      let rock = ''
      for (let j = s.j0; j < s.j1; j++) {
        for (let i = iMin; i < iMax; i++) {
          if (T.rocks[j * T.nx + i] !== 1) continue
          const cx = T.x0 + i * c
          const cy = T.y0 + j * c
          const h = hash(`r${i},${j}`)
          const rad = c * (0.45 + 0.3 * ((h % 100) / 100))
          const ring: Vec2[] = []
          for (let k = 0; k < 6; k++) {
            const a = (k / 6) * Math.PI * 2 + (h % 7)
            const wob = 0.75 + 0.25 * (((h >>> (k * 3)) % 8) / 8)
            ring.push([cx + Math.cos(a) * rad * wob, cy + Math.sin(a) * rad * wob])
          }
          rock += pathOf(ring.map((pt) => P(pt, T.z([cx, cy]) + 0.6)))
        }
      }
      if (rock) parts.push(`<path class="boulder" d="${rock}"/>`)
      if (froth) parts.push(froth)
      if (foam) parts.push(`<path class="foam" d="${foam}"/>`)
    }
    out.push(`<g data-strip="${f(s.n0)}">${parts.join('')}</g>`)
  }

  // ---- items, slotted between strips ---------------------------------------------------------------
  // Ground and standing things are cut along the front ground line (ground that faces away
  // from the camera can project below it).
  // The plate's sides are cut by covering what lies past them in paper, after: the ground
  // reaches a cell past each side, so the cover's one antialiased edge is all there is. Cut by
  // a clip, a renderer that clips each shape in turn laid the side's edge once per shape that
  // reached it, and the side showed a dotted line where strips and rows overlapped.
  const fx0 = front[0]
  const fx1 = front[front.length - 1]
  out.push(`<defs><clipPath id="above"><path d="${pathOf([[vb[0], vb[1]], [vb[0] + vb[2], vb[1]], [vb[0] + vb[2], fx1[1]], ...front.slice().reverse(), [vb[0], fx0[1]]])}"/></clipPath></defs>`)
  out.push(`<g clip-path="url(#above)">`)
  let next = 0
  const flushTo = (nearN: number) => {
    while (next < strips.length && strips[next].n1 > nearN + 1e-6) paintStrip(strips[next++])
  }
  for (const it of items) {
    const nearN = Math.min(...it.hull.map((pt) => pt[1]))
    flushTo(nearN)
    out.push(paintItem(it))
  }
  flushTo(-Infinity)
  out.push(`</g>`)
  out.push(`<path fill="${p.sky}" d="${pathOf([[vb[0], vb[1]], [x0, vb[1]], [x0, fx0[1]], [vb[0], fx0[1]]])}${pathOf([[x1, vb[1]], [vb[0] + vb[2], vb[1]], [vb[0] + vb[2], fx1[1]], [x1, fx1[1]]])}"/>`)
  // A crisp ink line along the front ground.
  out.push(`<path class="edge" d="${pathOf(front, false)}"/>`)
  // Labels over everything, haloed in the land color so they read across lines and roofs.
  if (scene.labels !== undefined) {
    const size = Math.max(14, capSize * 0.42)
    out.push(`<g class="labels" font-family="Georgia, 'Times New Roman', serif" fill="${p.ink}" stroke="${p.land}" stroke-width="${f(size * 0.22)}" stroke-linejoin="round" paint-order="stroke">`)
    for (const l of scene.labels) {
      const [sx, sy] = P(l.at, l.z)
      out.push(`<text x="${f(sx)}" y="${f(sy)}" font-size="${f(size)}" text-anchor="${l.anchor}" font-weight="bold">${esc(l.text)}</text>`)
      if (l.caption !== undefined) out.push(`<text x="${f(sx)}" y="${f(sy + size * 1.05)}" font-size="${f(size * 0.72)}" text-anchor="${l.anchor}" font-style="italic">${esc(l.caption)}</text>`)
    }
    out.push(`</g>`)
  }
  if (scene.time !== undefined) {
    const tx = vb[0] + pad
    const ty = vb[1] + pad + capSize
    out.push(
      `<g class="caption" font-family="Georgia, 'Times New Roman', serif" fill="${p.ink}">`,
      `<text x="${f(tx)}" y="${f(ty)}" font-size="${f(capSize)}" font-weight="bold">${scene.time.year}</text>`,
      scene.time.title === undefined ? '' : `<text x="${f(tx + capSize * 2.6)}" y="${f(ty)}" font-size="${f(capSize * 0.62)}" font-style="italic">${esc(scene.time.title)}</text>`,
      `</g>`,
    )
  }
  out.push(`</svg>`)
  stats.rapidCells = rapidCells
  stats.strips = strips.length
  return { svg: out.join('\n'), viewBox: vb, stats }
}

/** Hillshade: steps per unit of light · normal, and nested bands per step on each side. */
const SHADE_GAIN = 22
const SHADE_SUBSTEPS = 2
const SHADE_STEPS = 12
const SHADE_BANDS = SHADE_STEPS * SHADE_SUBSTEPS
/** Over open water the shade field is held this many steps below every band. */
const SHORE_CAP = 100
/** Band m covers the ground at least this many steps lit (or shaded). */
const bandThreshold = (m: number) => (m - 0.5) / SHADE_SUBSTEPS
/**
 * Each nested band's own opacity, so that ground inside band m shows the wash at
 * min(max, step · m / substeps), as a single flat wash at that opacity would.
 */
export const shadeAlphas = (step: number, max: number): number[] => {
  const out: number[] = []
  let below = 0
  for (let m = 1; m <= SHADE_BANDS; m++) {
    const total = Math.min(max, (step * m) / SHADE_SUBSTEPS)
    out.push(1 - (1 - total) / (1 - below))
    below = total
  }
  return out
}

const normalize = (v: [number, number, number]): [number, number, number] => {
  const l = Math.hypot(...v)
  return [v[0] / l, v[1] / l, v[2] / l]
}

const paintItem = (it: Item): string => {
  const title = it.name !== undefined ? `<title>${esc(it.name)}</title>` : ''
  const shapes = it.shapes.map((s) => {
    const own = s.dots !== undefined && s.dots.length > 0 ? `<path class="d" d="${s.dots.map(dot).join('')}"/>` : ''
    return paint(s) + own
  })
  const dots = it.dots.length > 0 ? `<path class="d" d="${it.dots.map(dot).join('')}"/>` : ''
  return `<g data-id="${it.id}">${title}${shapes.join('')}${dots}</g>`
}

const paint = (s: Shape): string => {
  if (s.line) return `<path class="${s.dash ? 'td' : 'i'}" d="${pathOf(s.pts, false)}"/>`
  if (s.seal) return `<path fill="${s.fill}" stroke="${s.fill}" stroke-width="0.5" stroke-linejoin="round" d="${pathOf(s.pts)}"/>`
  return `<path${s.ink ? ' class="i"' : ''} fill="${s.fill}" d="${pathOf(s.pts)}"/>`
}

/** A standalone page: the SVG inline, with drag-to-pan and wheel-to-zoom. */
export const renderPage = (scene: Scene, rendered: Rendered): string => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(scene.region.title)}</title>
<style>
  html, body { margin: 0; height: 100%; background: ${scene.palette.sky}; font: 13px/1.4 ui-sans-serif, system-ui, sans-serif; color: ${scene.palette.ink}; }
  #stage { position: fixed; inset: 0; overflow: hidden; cursor: grab; touch-action: none; }
  #stage.dragging { cursor: grabbing; }
  #stage svg { width: 100%; height: 100%; display: block; }
  header { position: fixed; left: 16px; top: 12px; pointer-events: none; }
  header h1 { margin: 0; font-size: 15px; font-weight: 600; }
  footer { position: fixed; right: 12px; bottom: 8px; opacity: .7; font-size: 11px; }
  footer a { color: inherit; }
  #tip { position: fixed; pointer-events: none; padding: 2px 6px; background: ${scene.palette.ink}; color: ${scene.palette.sky}; border-radius: 3px; font-size: 12px; display: none; }
</style>
</head>
<body>
<div id="stage">${rendered.svg.replace('<svg ', '<svg preserveAspectRatio="xMidYMid meet" ')}</div>
<header><h1>${esc(scene.region.title)}</h1><div>drag to pan · scroll to zoom · double-click to reset</div></header>
<footer>Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors${scene.terrain.flat ? '' : ` · ${esc(demCredit(scene.region))}`}</footer>
<div id="tip"></div>
<script>
(() => {
  const stage = document.getElementById('stage')
  const svg = stage.querySelector('svg')
  const home = svg.getAttribute('viewBox').split(' ').map(Number)
  let vb = home.slice()
  const apply = () => svg.setAttribute('viewBox', vb.join(' '))
  const toUser = (cx, cy) => {
    const r = svg.getBoundingClientRect()
    const s = Math.max(vb[2] / r.width, vb[3] / r.height)
    const ox = vb[0] + vb[2] / 2 - (r.width * s) / 2
    const oy = vb[1] + vb[3] / 2 - (r.height * s) / 2
    return [ox + (cx - r.left) * s, oy + (cy - r.top) * s, s]
  }
  stage.addEventListener('wheel', (e) => {
    e.preventDefault()
    const [ux, uy] = toUser(e.clientX, e.clientY)
    const k = Math.exp(e.deltaY * 0.0015)
    const w = Math.min(home[2] * 1.5, Math.max(40, vb[2] * k))
    const kk = w / vb[2]
    vb = [ux - (ux - vb[0]) * kk, uy - (uy - vb[1]) * kk, vb[2] * kk, vb[3] * kk]
    apply()
  }, { passive: false })
  let drag = null
  stage.addEventListener('pointerdown', (e) => { drag = [e.clientX, e.clientY]; stage.setPointerCapture(e.pointerId); stage.classList.add('dragging') })
  stage.addEventListener('pointerup', () => { drag = null; stage.classList.remove('dragging') })
  stage.addEventListener('pointermove', (e) => {
    const tip = document.getElementById('tip')
    if (drag) {
      const s = toUser(0, 0)[2]
      vb[0] -= (e.clientX - drag[0]) * s
      vb[1] -= (e.clientY - drag[1]) * s
      drag = [e.clientX, e.clientY]
      apply()
      tip.style.display = 'none'
      return
    }
    const g = e.target.closest && e.target.closest('g[data-id]')
    const t = g && g.querySelector('title')
    if (t) { tip.textContent = t.textContent; tip.style.left = e.clientX + 12 + 'px'; tip.style.top = e.clientY + 12 + 'px'; tip.style.display = 'block' }
    else tip.style.display = 'none'
  })
  stage.addEventListener('dblclick', () => { vb = home.slice(); apply() })
})()
</script>
</body>
</html>
`
