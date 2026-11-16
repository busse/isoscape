/**
 * The flat section: a cutaway's plane seen square on, as an architect's longitudinal section.
 *
 * It is built from the same parts and the same plane as the isometric cutaway (`buildScene` with
 * `section`, from the region `sectionRegion` makes): the camera looks level and straight at the
 * plane from the removed side, so the cut faces are drawn true to scale, solid in ink, and what
 * stands behind the plane (within the section's `beyond`) is drawn in elevation. Under it the
 * ground is cut too: the earth along the plane, dug out where the building goes below it, the
 * platforms and the rails where the plane crosses them. A red dashed line follows the traveler.
 */

import { pointInRing, type Vec2 } from './geom.ts'
import { paintOrder } from './order.ts'
import type { Cutaway, Region } from './region.ts'
import { lonLatFromLocal } from './region.ts'
import type { Item, Scene } from './scene.ts'

const f = (n: number) => (Math.round(n * 10) / 10).toString()
const path = (pts: readonly Vec2[], close = true) => pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${f(p[0])} ${f(p[1])}`).join('') + (close ? 'Z' : '')
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;')

/**
 * The region a cutaway's flat section is built in: centered on the plane between the
 * section's ends, the camera level (squash 0) and looking at the plane from the removed side,
 * so the plane runs left to right.
 */
export const sectionRegion = (region: Region): Region => {
  const cut = region.cutaway
  if (cut?.section === undefined) throw new Error(`"${region.name}" has no cutaway section`)
  const { from, to } = cut.section
  const mid = (from + to) / 2
  const r = (cut.bearing * Math.PI) / 180
  const at = lonLatFromLocal({ ...region, center: cut.through })
  const center = at(Math.sin(r) * mid, Math.cos(r) * mid)
  const beyond = Math.max(cut.section.beyond ?? 35, cut.section.other ?? 2)
  return {
    ...region,
    name: `${region.name}-section`,
    title: `${region.title}: section`,
    center,
    width: to - from,
    depth: 2 * beyond + 20,
    bearing: cut.bearing + (cut.remove === 'right' ? -90 : 90),
    snap: false,
    squash: 0,
    exaggeration: 1,
    scale: cut.section.scale ?? 10,
    slab: 0,
    terrain: { ...(region.terrain ?? {}), contour: 0 },
  }
}

export interface SectionRendered {
  readonly svg: string
  readonly viewBox: readonly [number, number, number, number]
  /** Screen boxes of the drawn parts, by item id, for callouts: [minX, minY, maxX, maxY]. */
  readonly anchors: Record<string, readonly [number, number, number, number]>
  /** How to place a point by meters along the plane and elevation: x = (x0 + s) × scale, y = −(elevation − datum) × exaggeration × scale. */
  readonly frame: { readonly x0: number; readonly scale: number; readonly datum: number; readonly exaggeration: number }
}

/** Draw a section scene (`buildScene` with `section`) as SVG. */
export const renderSection = (scene: Scene, cut: Cutaway): SectionRendered => {
  const { view, palette: p, terrain: T } = scene
  const pl = scene.cut
  if (pl === undefined || cut.section === undefined) throw new Error('not a cutaway section')
  const { from, to } = cut.section
  const s0 = from
  // Points along the plane, from its own point: s meters along u.
  const along = (s: number): Vec2 => [pl.p[0] + pl.u[0] * s, pl.p[1] + pl.u[1] * s]
  const P = (s: number, z: number): Vec2 => view.toScreen(along(s), z)
  const zOf = (e: number) => (e - T.datum) * T.exaggeration
  const items = paintOrder(scene.items, 96, true)
  // The ground along the plane, dug out under whatever the building cut puts below it.
  const step = 0.5
  const ground: [number, number][] = []
  for (let s = s0; s <= to + 1e-9; s += step) {
    let z = T.z(along(s))
    for (const sec of scene.sections ?? []) {
      const xs = sec.map((q) => q[0])
      if (s < Math.min(...xs) - 1e-6 || s > Math.max(...xs) + 1e-6) continue
      const lo = Math.min(...sec.map((q) => q[1]))
      if (lo < z) z = Math.min(z, lo)
    }
    ground.push([s, z])
  }
  const zMinGround = Math.min(...ground.map((g) => g[1]))
  const floor = zMinGround - (cut.section.earth ?? 4)
  const out: string[] = []
  const earth = [...ground.map(([s, z]) => P(s, z)), P(to, floor), P(s0, floor)]
  // Box around everything drawn.
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  const grow = (q: Vec2) => { minX = Math.min(minX, q[0]); maxX = Math.max(maxX, q[0]); minY = Math.min(minY, q[1]); maxY = Math.max(maxY, q[1]) }
  earth.forEach(grow)
  for (const it of items) for (const sh of it.shapes) for (const q of sh.pts) grow(q)
  out.push(`<path fill="${p.slab}" class="i" d="${path(earth)}"/>`)
  // Platforms where the plane crosses them: a low slab on the ground.
  const curated = scene.time?.curated ?? []
  for (const h of curated) {
    if (h.kind !== 'platform' || h.ring === undefined) continue
    const ring = h.ring.map(([lon, lat]) => view.toView(lon, lat))
    let run: number | null = null
    for (let s = s0; s <= to + 1e-9; s += 0.1) {
      const inside = pointInRing(along(s), ring)
      if (inside && run === null) run = s
      if ((!inside || s + 0.1 > to) && run !== null) {
        const g = T.z(along((run + s) / 2))
        out.push(`<path fill="${p.platform}" class="i" d="${path([P(run, g), P(s, g), P(s, g + PLATFORM_HEIGHT), P(run, g + PLATFORM_HEIGHT)])}"/>`)
        run = null
      }
    }
  }
  // Rails where the plane crosses a track: the ballast, and the two rails over it.
  for (const h of curated) {
    if (h.kind !== 'rail') continue
    for (const line of [...(h.line ? [h.line] : []), ...(h.lines ?? [])]) {
      const pts = line.map(([lon, lat]) => view.toView(lon, lat))
      for (let i = 0; i + 1 < pts.length; i++) {
        const s = crossing(pl, pts[i], pts[i + 1])
        if (s === null || s < s0 || s > to) continue
        const a = pts[i]
        const b = pts[i + 1]
        // Across the plane at an angle, the gauge and ballast are drawn as long as they cut.
        const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
        const sin = Math.abs(((b[0] - a[0]) * pl.n[0] + (b[1] - a[1]) * pl.n[1]) / l) || 1
        const g = T.z(along(s))
        const half = 1.6 / sin
        out.push(`<path fill="${p.rail}" class="i" d="${path([P(s - half - 0.4, g), P(s + half + 0.4, g), P(s + half, g + 0.35), P(s - half, g + 0.35)])}"/>`)
        for (const k of [-0.72, 0.72]) {
          const c = s + k / sin
          out.push(`<path fill="${p.railSteel}" d="${path([P(c - 0.08, g + 0.35), P(c + 0.08, g + 0.35), P(c + 0.08, g + 0.5), P(c - 0.08, g + 0.5)])}"/>`)
        }
      }
    }
  }
  const anchors: Record<string, [number, number, number, number]> = {}
  for (const it of items) {
    out.push(paintItem(it))
    anchorOf(anchors, it)
  }
  // The traveler's path.
  if (cut.section.route !== undefined && cut.section.route.length > 1) {
    const pts = cut.section.route.map(([s, e]) => P(s, zOf(e)))
    out.push(`<path fill="none" stroke="${p.route}" stroke-width="${f(p.routeWidth)}" stroke-dasharray="${p.routeDash.map(f).join(' ')}" stroke-linecap="round" stroke-linejoin="round" d="${path(pts, false)}"/>`)
  }
  const pad = 20
  const vb: [number, number, number, number] = [minX - pad, minY - pad, maxX - minX + 2 * pad, maxY - minY + 2 * pad]
  const svg = [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.map(f).join(' ')}" class="isoscape-section" role="img">`,
    `<title>${esc(scene.region.title)}</title>`,
    `<style>.i{stroke:${p.ink};stroke-width:${p.lineWidth};stroke-linejoin:round}</style>`,
    `<rect x="${f(vb[0])}" y="${f(vb[1])}" width="${f(vb[2])}" height="${f(vb[3])}" fill="${p.sky}"/>`,
    ...out,
    `</svg>`,
  ].join('\n')
  return { svg, viewBox: vb, anchors, frame: { x0: pl.p[0], scale: view.scale, datum: T.datum, exaggeration: T.exaggeration } }
}

/** Platforms stand this high over the rails in the section (approximate: no drawing gives it). */
export const PLATFORM_HEIGHT = 0.35

/** Where segment a–b crosses the plane, as meters along it, or null. */
const crossing = (pl: NonNullable<Scene['cut']>, a: Vec2, b: Vec2): number | null => {
  const da = (a[0] - pl.p[0]) * pl.n[0] + (a[1] - pl.p[1]) * pl.n[1]
  const db = (b[0] - pl.p[0]) * pl.n[0] + (b[1] - pl.p[1]) * pl.n[1]
  if ((da > 0) === (db > 0)) return null
  const t = da / (da - db)
  const q: Vec2 = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
  return (q[0] - pl.p[0]) * pl.u[0] + (q[1] - pl.p[1]) * pl.u[1]
}

const paintItem = (it: Item): string => {
  const title = it.name === undefined ? '' : `<title>${esc(it.name)}</title>`
  return `<g data-id="${esc(it.id)}">${title}${it.shapes.map((s) => `<path class="i" fill="${s.fill}" d="${path(s.pts)}"/>`).join('')}</g>`
}

/** Grow the anchor box of an item's part (its id, less any `:near` or piece suffix). */
export const anchorOf = (anchors: Record<string, [number, number, number, number]>, it: Item): void => {
  if (it.shapes.length === 0) return
  const key = it.id.replace(/\/\d+$/, '').replace(/(:near)?(:base)?$/, '')
  let box = anchors[key]
  for (const s of it.shapes) for (const [x, y] of s.pts) {
    if (box === undefined) box = anchors[key] = [x, y, x, y]
    else { box[0] = Math.min(box[0], x); box[1] = Math.min(box[1], y); box[2] = Math.max(box[2], x); box[3] = Math.max(box[3], y) }
  }
}
