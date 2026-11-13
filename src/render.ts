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

import { centroid, clipRingToRect, clipSegmentToRect, hash, type Rect, type Ring, type Vec2 } from './geom.ts'
import { GROUND_ORDER } from './classify.ts'
import { paintOrder } from './order.ts'
import type { Item, Scene, Shape } from './scene.ts'
import { cellNormal, contours, dampCell, riverFall, type ContourSegment } from './terrain.ts'

const f = (n: number) => (Math.round(n * 10) / 10).toString()
const pathOf = (pts: readonly Vec2[], close = true) =>
  pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${f(p[0])} ${f(p[1])}`).join('') + (close ? 'Z' : '')

let r = 1
const dot = ([x, y]: Vec2) => `M${f(x - r)} ${f(y)}a${r} ${r} 0 1 0 ${f(2 * r)} 0a${r} ${r} 0 1 0 ${f(-2 * r)} 0`

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

  const items = paintOrder(scene.items)
  r = p.dotRadius

  // ---- the frame on screen -------------------------------------------------------------------
  const xs: number[] = []
  for (let e = fr.minX; e < fr.maxX; e += c) xs.push(e)
  xs.push(fr.maxX)
  const front = xs.map((e) => drape([e, fr.minY]))
  const [x0] = P([fr.minX, 0])
  const [x1] = P([fr.maxX, 0])
  let top = Infinity
  for (const it of items) for (const s of it.shapes) for (const pt of s.pts) top = Math.min(top, pt[1])
  for (let n = fr.minY; n <= fr.maxY + 1e-6; n += c) for (const e of xs) top = Math.min(top, drape([e, n])[1])
  const bottom = P([0, fr.minY], -slab)[1]
  const pad = 24
  const vb: [number, number, number, number] = [x0 - pad, top - pad, x1 - x0 + 2 * pad, bottom - top + 2 * pad]

  const out: string[] = []
  const sealed = (cls: string, fill: string) => `.${cls}{fill:${fill};stroke:${fill};stroke-width:.6;stroke-linejoin:round}`
  out.push(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.map(f).join(' ')}" class="isoscape" data-region="${esc(region.name)}" role="img">`,
    `<title>${esc(region.title)}</title>`,
    `<desc>Map data © OpenStreetMap contributors (ODbL).${T.flat ? '' : ' Elevation: USGS 3DEP.'} Bearing ${view.bearing.toFixed(1)}°.</desc>`,
    `<style>`,
    `.i{stroke:${p.ink};stroke-width:${p.lineWidth};stroke-linejoin:round}.d{fill:${p.ink}}`,
    `.td{fill:none;stroke:${p.ink};stroke-width:${p.lineWidth};stroke-dasharray:1.2 1.8}`,
    `.L{fill:${p.land}}`, sealed('I', p.land), sealed('W', p.water), sealed('green', p.green), sealed('wood', p.wood), sealed('rock', p.rock),
    sealed('parking', p.parking), sealed('cemetery', p.cemetery), sealed('canal', p.water), sealed('path', p.path),
    sealed('road', p.road), sealed('rail', p.rail), sealed('weir', p.foam),
    `.ties{fill:none;stroke:${p.railTie};stroke-width:${p.groundLineWidth * 2};stroke-dasharray:1 2.2}`,
    `.crest{fill:none;stroke:${p.ink};stroke-width:${p.groundLineWidth};stroke-opacity:.6}`,
    `.cm{fill:none;stroke:${p.ink};stroke-width:${p.groundLineWidth};stroke-opacity:${p.contourMinor}}`,
    `.cM{fill:none;stroke:${p.ink};stroke-width:${p.groundLineWidth * 1.6};stroke-opacity:${p.contourMajor}}`,
    `.foam{fill:none;stroke:${p.foam};stroke-width:${f(p.lineWidth * 1.6)};stroke-linecap:round}`,
    `.froth{fill:${p.foam}}`,
    `.boulder{fill:${p.boulder};stroke:${p.ink};stroke-width:${p.groundLineWidth};stroke-opacity:.7;stroke-linejoin:round}`,
    `.edge{fill:none;stroke:${p.ink};stroke-width:${p.lineWidth}}`,
    `</style>`,
    `<rect x="${f(vb[0])}" y="${f(vb[1])}" width="${f(vb[2])}" height="${f(vb[3])}" fill="${p.sky}"/>`,
  )

  // ---- the slab: a cut through the ground along the front edge -------------------------------
  if (slab > 0) {
    const yBase = P([0, fr.minY], -slab)[1]
    out.push(`<path class="i" fill="${p.slab}" d="${pathOf([...front, [x1, yBase], [x0, yBase]])}"/>`)
    // Water in the cut, where the front edge crosses open water.
    const jFront = Math.round((fr.minY - T.y0) / c)
    let run: number[] = []
    const flush = () => {
      if (run.length >= 2) {
        const pts = run.map((k) => front[k])
        out.push(`<path fill="${p.slabWater}" d="${pathOf([...pts, [pts[pts.length - 1][0], yBase], [pts[0][0], yBase]])}"/>`)
      }
      run = []
    }
    xs.forEach((e, k) => {
      const i = Math.round((e - T.x0) / c)
      if (T.water[jFront * T.nx + i] === 1) run.push(k)
      else flush()
    })
    flush()
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
  // everything else paints under it, so a park drawn across the river is covered by it.
  const inRiver = (g: (typeof cover)[number]) => wetAt(centroid(g.rings[0]))
  const coverLayers = (after: boolean): Layer[] =>
    GROUND_ORDER.map((kind) => ({
      cls: kind,
      entries: cover.filter((g) => g.kind === kind && inRiver(g) === after).map((g) => entryOf(g.rings)),
    }))
  const ribbonLayer = (kind: string): Layer => ({
    cls: kind,
    entries: scene.ribbons.filter((rb) => rb.kind === kind).flatMap((rb) => rb.quads.map((q) => entryOf([q]))),
  })
  const layers: Layer[] = [
    ...coverLayers(false),
    { cls: 'W', entries: water.map((g) => entryOf(g.rings)) },
    { cls: 'I', entries: islands.map((g) => entryOf(g.rings)) },
    ...coverLayers(true),
    ribbonLayer('canal'),
    ribbonLayer('weir'),
    ribbonLayer('path'),
    ribbonLayer('road'),
    ribbonLayer('rail'),
  ]
  const lineLayer = (kind: string, cls: string) => ({
    cls,
    segs: scene.ribbons.filter((rb) => rb.kind === kind).flatMap((rb) => rb.centre),
  })
  const lineLayers = [lineLayer('rail', 'ties'), lineLayer('weir', 'crest')]

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
  const nodeX = (i: number) => Math.min(fr.maxX, Math.max(fr.minX, T.x0 + i * c))
  const iMin = Math.round((fr.minX - T.x0) / c)
  const iMax = Math.ceil((fr.maxX - T.x0) / c)
  // Light from the left and a little towards the camera, so the slopes we look at are lit and
  // the backs of hills fall into shade.
  const light = normalise([-0.85, -0.35, 1.0])

  const paintStrip = (s: Strip) => {
    // Each strip reaches a little past its near edge, under the next strip, so no hairline of
    // background shows between them; the next strip paints over the overlap.
    const lap = s.n0 > fr.minY ? 0.8 : 0
    const band: Rect = { minX: fr.minX, maxX: fr.maxX, minY: s.n0 - lap, maxY: s.n1 }
    const parts: string[] = []
    // Bare ground first: the strip's own surface, far edge left to right, near edge back.
    const far = xs.map((e) => drape([e, s.n1]))
    const near = xs.map((e) => drape([e, s.n0 - lap])).reverse()
    parts.push(`<path class="L" d="${pathOf([...far, ...near])}"/>`)
    for (const layer of layers) {
      let d = ''
      for (const e of layer.entries) {
        if (e.maxN < s.n0 || e.minN > s.n1) continue
        for (const ring of e.rings) {
          const clipped = clipRingToRect(ring, band)
          if (clipped.length < 3) continue
          d += pathOf(densify(clipped, c).map(drape))
        }
      }
      if (d) parts.push(`<path class="${layer.cls}" d="${d}"/>`)
    }
    for (const ll of lineLayers) {
      let d = ''
      for (const [a, b] of ll.segs) {
        const seg = clipSegmentToRect(a, b, band)
        if (seg === null) continue
        d += pathOf(densify(seg, c, false).map(drape), false)
      }
      if (d) parts.push(`<path class="${ll.cls}" d="${d}"/>`)
    }
    if (!T.flat) {
      // Hillshade: runs of cells along each row that share a shade level, washed light or dark.
      const flatShade = light[2]
      for (let j = s.j0; j < s.j1; j++) {
        let runStart = -1
        let runLevel = 0
        const emit = (iEnd: number) => {
          if (runStart < 0 || runLevel === 0) return
          const topEdge: Vec2[] = []
          const bottomEdge: Vec2[] = []
          for (let i = runStart; i <= iEnd; i++) {
            topEdge.push(drape([nodeX(i), T.y0 + (j + 1) * c]))
            bottomEdge.push(drape([nodeX(i), T.y0 + j * c]))
          }
          const colour = runLevel > 0 ? p.shadeLight : p.shadeDark
          const alpha = Math.min(0.55, Math.abs(runLevel) * (runLevel > 0 ? 0.045 : 0.04))
          parts.push(`<path fill="${colour}" fill-opacity="${alpha.toFixed(2)}" d="${pathOf([...topEdge, ...bottomEdge.reverse()])}"/>`)
        }
        for (let i = iMin; i < iMax; i++) {
          let level = 0
          if (!dampCell(T, i, j)) {
            const n = cellNormal(T, i, j)
            const shade = n[0] * light[0] + n[1] * light[1] + n[2] * light[2]
            level = Math.max(-12, Math.min(12, Math.round((shade - flatShade) * 22)))
          }
          if (level !== runLevel) {
            emit(i)
            runStart = i
            runLevel = level
          }
        }
        emit(iMax)
      }
      // Contours.
      let minor = ''
      let major = ''
      for (let j = s.j0; j < s.j1; j++) {
        for (const seg of contoursByRow.get(j) ?? []) {
          const clipped = clipSegmentToRect(seg.a, seg.b, band)
          if (clipped === null) continue
          const d = pathOf(clipped.map(drape), false)
          if (seg.major) major += d
          else minor += d
        }
      }
      if (minor) parts.push(`<path class="cm" d="${minor}"/>`)
      if (major) parts.push(`<path class="cM" d="${major}"/>`)
      // Rapids: where the river's surface falls, white strokes across the current.
      let foam = ''
      let froth = ''
      for (let j = s.j0; j < s.j1; j++) {
        for (let i = iMin; i < iMax; i++) {
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
    // Ground that faces away from the camera can project below the front edge; cut it there.
    out.push(`<g data-strip="${f(s.n0)}" clip-path="url(#above)">${parts.join('')}</g>`)
  }

  // ---- items, slotted between strips ---------------------------------------------------------------
  // Standing things are cut at the plate's sides and along the front ground line.
  out.push(`<defs><clipPath id="above"><path d="${pathOf([[x0, vb[1]], [x1, vb[1]], ...front.slice().reverse()])}"/></clipPath></defs>`)
  let next = 0
  const flushTo = (nearN: number) => {
    while (next < strips.length && strips[next].n1 > nearN + 1e-6) paintStrip(strips[next++])
  }
  for (const it of items) {
    const nearN = Math.min(...it.hull.map((pt) => pt[1]))
    flushTo(nearN)
    out.push(`<g clip-path="url(#above)">${paintItem(it)}</g>`)
  }
  flushTo(-Infinity)
  // A crisp ink line along the front ground.
  out.push(`<path class="edge" d="${pathOf(front, false)}"/>`)
  out.push(`</svg>`)
  stats.rapidCells = rapidCells
  stats.strips = strips.length
  return { svg: out.join('\n'), viewBox: vb, stats }
}

const normalise = (v: [number, number, number]): [number, number, number] => {
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
<footer>Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors${scene.terrain.flat ? '' : ' · Elevation: USGS 3DEP'}</footer>
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
