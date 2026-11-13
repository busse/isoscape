/**
 * Scene → SVG, and SVG → a pan-and-zoom page.
 *
 * Paint order, bottom to top: the ground slab and its cut face; water; everything else on
 * the ground, masked so it never paints on open water; then the items, already sorted.
 */

import type { Vec2 } from './geom.ts'
import { GROUND_ORDER } from './classify.ts'
import { paintOrder } from './order.ts'
import { onWater, type Scene, type Shape } from './scene.ts'

const f = (n: number) => (Math.round(n * 10) / 10).toString()
const pathOf = (pts: readonly Vec2[], close = true) =>
  pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${f(p[0])} ${f(p[1])}`).join('') + (close ? 'Z' : '')

let r = 1
const dot = ([x, y]: Vec2) => `M${f(x - r)} ${f(y)}a${r} ${r} 0 1 0 ${f(2 * r)} 0a${r} ${r} 0 1 0 ${f(-2 * r)} 0`

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;')

export interface Rendered {
  readonly svg: string
  readonly viewBox: readonly [number, number, number, number]
}

export const renderSvg = (scene: Scene): Rendered => {
  const { view, palette: p, region } = scene
  const fr = view.frame
  const slab = region.slab ?? 14
  const S = (pt: Vec2, z = 0) => view.toScreen(pt, z)

  const items = paintOrder(scene.items)
  r = p.dotRadius

  // Frame on screen: the ground rectangle is a screen rectangle, since E' is screen x and N'
  // only moves screen y.
  const [x0, yFar] = S([fr.minX, fr.maxY])
  const [x1, yNear] = S([fr.maxX, fr.minY])
  let top = yFar
  for (const it of items) for (const s of it.shapes) for (const pt of s.pts) if (pt[1] < top) top = pt[1]
  const bottom = S([0, fr.minY], -slab)[1]
  const pad = 24
  const vb: [number, number, number, number] = [x0 - pad, top - pad, x1 - x0 + 2 * pad, bottom - top + 2 * pad]

  const out: string[] = []
  out.push(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.map(f).join(' ')}" class="isoscape" data-region="${esc(region.name)}" role="img">`,
    `<title>${esc(region.title)}</title>`,
    `<desc>Map data © OpenStreetMap contributors (ODbL). Bearing ${view.bearing.toFixed(1)}°.</desc>`,
    `<style>.i{stroke:${p.ink};stroke-width:${p.lineWidth};stroke-linejoin:round}.g{stroke:none}.d{fill:${p.ink}}.t{fill:none;stroke:${p.railTie};stroke-width:${p.groundLineWidth * 2};stroke-dasharray:1 2.2}.td{fill:none;stroke:${p.ink};stroke-width:${p.lineWidth};stroke-dasharray:1.2 1.8}</style>`,
    `<rect x="${f(vb[0])}" y="${f(vb[1])}" width="${f(vb[2])}" height="${f(vb[3])}" fill="${p.sky}"/>`,
  )

  // ---- slab ----------------------------------------------------------------------------------
  const frameRect = `M${f(x0)} ${f(yFar)}H${f(x1)}V${f(yNear)}H${f(x0)}Z`
  out.push(`<defs><clipPath id="frame"><path d="${frameRect}"/></clipPath>`)
  // Land only: the frame, minus water, plus islands.
  const water = scene.ground.filter((g) => g.kind === 'water')
  const islands = scene.ground.filter((g) => g.kind === 'island')
  out.push(
    `<mask id="land" maskUnits="userSpaceOnUse" x="${f(vb[0])}" y="${f(vb[1])}" width="${f(vb[2])}" height="${f(vb[3])}">`,
    `<rect x="${f(vb[0])}" y="${f(vb[1])}" width="${f(vb[2])}" height="${f(vb[3])}" fill="#fff"/>`,
    ...water.map((g) => `<path fill="#000" fill-rule="evenodd" d="${g.rings.map((r) => pathOf(r.map((pt) => S(pt)))).join('')}"/>`),
    ...islands.map((g) => `<path fill="#fff" fill-rule="evenodd" d="${g.rings.map((r) => pathOf(r.map((pt) => S(pt)))).join('')}"/>`),
    `</mask></defs>`,
  )
  if (slab > 0) {
    const yBase = S([0, fr.minY], -slab)[1]
    out.push(`<path class="i" fill="${p.slab}" d="M${f(x0)} ${f(yNear)}H${f(x1)}V${f(yBase)}H${f(x0)}Z"/>`)
    // Where the near edge crosses open water, show the water in the cut.
    const step = 2
    let start: number | null = null
    const runs: [number, number][] = []
    for (let e = fr.minX; e <= fr.maxX + 1e-6; e += step) {
      const wet = onWater(scene, [e, fr.minY + 0.01])
      if (wet && start === null) start = e
      if (!wet && start !== null) { runs.push([start, e]); start = null }
    }
    if (start !== null) runs.push([start, fr.maxX])
    const yWater = S([0, fr.minY], -1.5)[1]
    for (const [a, b] of runs) {
      out.push(`<path fill="${p.slabWater}" d="M${f(S([a, 0])[0])} ${f(yWater)}H${f(S([b, 0])[0])}V${f(yBase)}H${f(S([a, 0])[0])}Z"/>`)
    }
  }

  // ---- ground --------------------------------------------------------------------------------
  out.push(`<g clip-path="url(#frame)">`)
  out.push(`<path fill="${p.land}" d="${frameRect}"/>`)
  for (const g of water) {
    out.push(`<path fill="${p.water}" stroke="${p.waterLine}" stroke-width="${p.groundLineWidth}" fill-rule="evenodd" d="${g.rings.map((r) => pathOf(r.map((pt) => S(pt)))).join('')}"/>`)
  }
  for (const g of islands) {
    out.push(`<path fill="${p.land}" stroke="${p.waterLine}" stroke-width="${p.groundLineWidth}" fill-rule="evenodd" d="${g.rings.map((r) => pathOf(r.map((pt) => S(pt)))).join('')}"/>`)
  }
  out.push(`<g mask="url(#land)">`)
  const fills: Record<string, string> = { green: p.green, wood: p.wood, rock: p.rock, parking: p.parking, cemetery: p.cemetery }
  for (const kind of GROUND_ORDER) {
    const d = scene.ground.filter((g) => g.kind === kind).map((g) => g.rings.map((r) => pathOf(r.map((pt) => S(pt)))).join('')).join('')
    if (d) out.push(`<path class="g" fill="${fills[kind]}" fill-rule="evenodd" d="${d}"/>`)
  }
  const ribbonPath = (kind: string) => scene.ribbons.filter((r) => r.kind === kind).flatMap((r) => r.quads.map((q) => pathOf(q))).join('')
  const canal = ribbonPath('canal')
  if (canal) out.push(`<path fill="${p.water}" d="${canal}"/>`)
  const paths = ribbonPath('path')
  if (paths) out.push(`<path fill="${p.path}" d="${paths}"/>`)
  const roads = ribbonPath('road')
  if (roads) out.push(`<path fill="${p.road}" stroke="${p.road}" stroke-width="0.6" stroke-linejoin="round" d="${roads}"/>`)
  const rails = ribbonPath('rail')
  if (rails) {
    out.push(`<path fill="${p.rail}" d="${rails}"/>`)
    const ties = scene.ribbons.filter((r) => r.kind === 'rail').flatMap((r) => r.centre.map((c) => pathOf(c, false))).join('')
    out.push(`<path class="t" d="${ties}"/>`)
  }
  out.push(`</g></g>`)
  // A crisp ink edge along the front of the plate.
  out.push(`<path class="i" fill="none" d="M${f(x0)} ${f(yNear)}H${f(x1)}"/>`)

  // ---- items ---------------------------------------------------------------------------------
  // Standing things are cut at the plate's sides and front edge, like a diorama.
  out.push(`<clipPath id="above"><path d="M${f(x0)} ${f(vb[1])}H${f(x1)}V${f(yNear)}H${f(x0)}Z"/></clipPath>`)
  out.push(`<g clip-path="url(#above)">`)
  for (const it of items) {
    const title = it.name !== undefined ? `<title>${esc(it.name)}</title>` : ''
    const shapes = it.shapes.map((s: Shape) => {
      const own = s.dots !== undefined && s.dots.length > 0 ? `<path class="d" d="${s.dots.map(dot).join('')}"/>` : ''
      return paint(s) + own
    })
    const dots = it.dots.length > 0 ? `<path class="d" d="${it.dots.map(dot).join('')}"/>` : ''
    out.push(`<g data-id="${it.id}">${title}${shapes.join('')}${dots}</g>`)
  }
  out.push(`</g>`)

  out.push(`</svg>`)
  return { svg: out.join('\n'), viewBox: vb }
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
  #tip { position: fixed; pointer-events: none; padding: 2px 6px; background: ${scene.palette.ink}; color: ${scene.palette.sky}; border-radius: 3px; font-size: 12px; display: none; }
</style>
</head>
<body>
<div id="stage">${rendered.svg.replace('<svg ', '<svg preserveAspectRatio="xMidYMid meet" ')}</div>
<header><h1>${esc(scene.region.title)}</h1><div>drag to pan · scroll to zoom · double-click to reset</div></header>
<footer>Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors</footer>
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
