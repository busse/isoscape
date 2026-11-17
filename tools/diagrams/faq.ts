#!/usr/bin/env node
/**
 * The flat diagrams on the FAQ page, and the pipeline diagram that page shares with How it's
 * made, written as SVG into pages/:
 *
 *   node tools/diagrams/faq.ts                 # pages/faq-*.svg and pages/pipeline.svg
 *   node tools/diagrams/faq.ts --social x.svg  # also the 1200 x 630 link-preview layout
 *
 * They are drawn in the maps' own language: inked edges, a dot on every corner, flat fills, with
 * every color taken from the paper palette (light) and the night palette (dark, by
 * prefers-color-scheme) in src/palette.ts, and line and dot at twice the maps' weights. The marks
 * for how sure a thing is are the cutaway sheets': a solid disc, a ring and a dashed ring.
 *
 * The diagrams are narrow (400 units, drawn at 400 px) and run top to bottom, so their text stays
 * readable on a phone. Text stays text. `npm test` checks the files in pages/ match this script.
 */

import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { PALETTES, type Palette } from '../../src/palette.ts'

const paper = PALETTES.paper
const night = PALETTES.night

/** The roles a diagram colors by, and where each comes from in a palette. */
const roles = (p: Palette, dark: boolean) => ({
  bg: p.sky,
  ink: p.ink,
  dim: dark ? p.railSteel : p.railTie,
  card: dark ? p.land : p.road,
  artist: p.fresh,
  agent: p.traced.stone,
  code: p.green,
  cache: p.water,
  accent: p.route,
})

export const LINE = paper.lineWidth * 2
export const DOT = paper.dotRadius * 2
export const W = 400
const SERIF = "'Libre Baskerville', Baskerville, Georgia, serif"
const SANS = "ui-sans-serif, -apple-system, 'Segoe UI', system-ui, sans-serif"
const MONO = 'ui-monospace, SFMono-Regular, Menlo, monospace'
/** Type sizes, in units of a 400-unit-wide drawing. */
export const SIZE = { head: 12, name: 16, body: 13.5, mono: 12.5, note: 12.5 } as const

const css = (r: ReturnType<typeof roles>) =>
  `.bg{fill:${r.bg}}.ink{fill:${r.ink}}.dim{fill:${r.dim}}.card{fill:${r.card}}` +
  `.artist{fill:${r.artist}}.agent{fill:${r.agent}}.code{fill:${r.code}}.cache{fill:${r.cache}}.acc{fill:${r.accent}}` +
  `.edge{fill:none;stroke:${r.ink};stroke-width:${LINE}}.thin{fill:none;stroke:${r.ink};stroke-width:${LINE * 0.6}}` +
  `.edge.card{fill:${r.card}}.edge.cache{fill:${r.cache}}.edge.artist{fill:${r.artist}}.edge.agent{fill:${r.agent}}.edge.code{fill:${r.code}}` +
  `.mark{fill:${r.bg};stroke:${r.ink};stroke-width:${LINE}}.mark.solid{fill:${r.ink}}.mark.dash{stroke-dasharray:2.6 1.7}` +
  `.hl{fill:none;stroke:${r.accent};stroke-width:${LINE * 1.4};stroke-dasharray:6 4}`

const STYLE = `<style>
text{font-family:${SANS}}
.h{font:600 ${SIZE.head}px ${SANS};letter-spacing:.08em}
.n{font:700 ${SIZE.name}px ${SERIF}}
.b{font-size:${SIZE.body}px}
.bb{font-size:${SIZE.body}px;font-weight:600}
.m{font:${SIZE.mono}px ${MONO}}
.s{font-size:${SIZE.note}px}
.si{font-size:${SIZE.note}px;font-style:italic}
${css(roles(paper, false))}
@media (prefers-color-scheme: dark){${css(roles(night, true))}}
</style>`

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const n = (v: number) => String(Math.round(v * 10) / 10)

/** One line of text. `cls` holds the size class and the fill class. */
const t = (x: number, y: number, s: string, cls: string, anchor: 'start' | 'middle' | 'end' = 'start') =>
  `<text x="${n(x)}" y="${n(y)}" class="${cls}"${anchor === 'start' ? '' : ` text-anchor="${anchor}"`}>${esc(s)}</text>`

const dots = (pts: readonly [number, number][]) => pts.map(([x, y]) => `<circle cx="${n(x)}" cy="${n(y)}" r="${n(DOT)}" class="ink"/>`).join('')

/** A box: inked edges, a flat fill, a dot on every corner. */
const box = (x: number, y: number, w: number, h: number, fill: string) =>
  `<rect x="${n(x)}" y="${n(y)}" width="${n(w)}" height="${n(h)}" class="edge ${fill}"/>` + dots([[x, y], [x + w, y], [x, y + h], [x + w, y + h]])

/** An arrow from (x0, y0) to (x1, y1), a dot at its tail and a filled head. */
const arrow = (x0: number, y0: number, x1: number, y1: number, head = true) => {
  const dx = x1 - x0
  const dy = y1 - y0
  const d = Math.hypot(dx, dy) || 1
  const ux = dx / d
  const uy = dy / d
  const L = 8
  const Wd = 4.2
  const bx = x1 - ux * L
  const by = y1 - uy * L
  return `<path d="M${n(x0)} ${n(y0)}L${n(head ? bx : x1)} ${n(head ? by : y1)}" class="edge"/>` +
    (head ? `<path d="M${n(x1)} ${n(y1)}L${n(bx - uy * Wd)} ${n(by + ux * Wd)}L${n(bx + uy * Wd)} ${n(by - ux * Wd)}Z" class="ink"/>` : '') +
    `<circle cx="${n(x0)}" cy="${n(y0)}" r="${n(DOT * 0.8)}" class="ink"/>`
}

/** A polyline arrow through points, a dot at its tail, a head at the last. */
const route = (pts: readonly [number, number][]) => {
  const [x1, y1] = pts[pts.length - 1]
  const [x0, y0] = pts[pts.length - 2]
  const d = Math.hypot(x1 - x0, y1 - y0) || 1
  const end: [number, number] = [x1 - ((x1 - x0) / d) * 8, y1 - ((y1 - y0) / d) * 8]
  const line = [...pts.slice(0, -1), end].map(([x, y]) => `${n(x)} ${n(y)}`).join('L')
  return `<path d="M${line}" class="edge"/>` + arrow(end[0], end[1], x1, y1).replace(/<path[^>]*class="edge"\/>/, '').replace(/<circle[^>]*\/>$/, '') +
    `<circle cx="${n(pts[0][0])}" cy="${n(pts[0][1])}" r="${n(DOT * 0.8)}" class="ink"/>`
}

/** How sure: the cutaway sheets' marks. */
export type Sure = 'measured' | 'inferred' | 'guessed'
const mark = (x: number, y: number, sure: Sure, r = 5.2) =>
  `<circle cx="${n(x)}" cy="${n(y)}" r="${n(r)}" class="mark${sure === 'measured' ? ' solid' : sure === 'guessed' ? ' dash' : ''}"/>`

const svg = (id: string, h: number, title: string, desc: string, body: string, width = W) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${n(h)}" width="${width}" height="${n(h)}" role="img" aria-labelledby="${id}-t ${id}-d">
<title id="${id}-t">${esc(title)}</title>
<desc id="${id}-d">${esc(desc)}</desc>
${STYLE}
<rect width="${width}" height="${n(h)}" class="bg"/>
${body}
</svg>
`

const X0 = 16
const BW = W - 2 * X0

/** A lane: a swatch of its color down the left, a name, and lines of text on a plain card. */
const lane = (y: number, fill: string, name: string, role: string, lines: readonly string[]) => {
  const h = 34 + lines.length * 19 + 6
  const out = box(X0, y, BW, h, 'card') +
    `<rect x="${n(X0)}" y="${n(y)}" width="10" height="${n(h)}" class="edge ${fill}"/>` + dots([[X0 + 10, y], [X0 + 10, y + h]]) +
    t(X0 + 24, y + 24, name, 'n ink') + t(X0 + BW - 12, y + 23, role, 's ink', 'end') +
    lines.map((l, i) => t(X0 + 24, y + 48 + i * 19, l, 'b ink')).join('')
  return { svg: out, h }
}

/** The two arrows between stacked lanes: down on the left, up on the right, each labeled. */
const between = (y0: number, y1: number, down: string, up: string) =>
  arrow(64, y0, 64, y1) + t(78, (y0 + y1) / 2 + 4.5, down, 's dim') +
  arrow(238, y1, 238, y0) + t(252, (y0 + y1) / 2 + 4.5, up, 's dim')

// ---- A: who does what --------------------------------------------------------------------------

export const whoDoesWhat = (): string => {
  let y = 14
  const parts: string[] = [t(X0, y + 12, 'WHO DOES WHAT', 'h dim')]
  y += 26
  const a = lane(y, 'artist', 'Chris Busse', 'the artist', [
    'Decides what to draw, and how it should look',
    'Sets the rules and limits the work follows',
    'Looks at every result, sends back what is',
    'wrong, and decides what to keep',
  ])
  parts.push(a.svg)
  y += a.h
  parts.push(between(y + 6, y + 50, 'asks, in words', 'shows the result'))
  y += 56
  const c = lane(y, 'agent', 'Claude', "under Chris's direction", [
    'Writes and changes the code',
    'Runs the builds, the tests and the checks',
    'Reports what changed, with pictures',
  ])
  parts.push(c.svg)
  y += c.h
  parts.push(between(y + 6, y + 50, 'runs a build', 'SVG, counts, warnings'))
  y += 56
  const s = lane(y, 'code', 'isoscape', 'the code', [
    'Computes the drawing from open data',
    'Same data and code in, same SVG out',
    'No image model; no network while it draws',
  ])
  parts.push(s.svg)
  y += s.h + 24
  parts.push(t(X0, y, 'The loop: direct, build, look, correct.', 'si ink'))
  parts.push(t(X0, y + 18, 'Nothing is kept until Chris approves it.', 'si ink'))
  y += 34
  return svg('who', y, 'Who does what',
    'Three lanes. Chris Busse, the artist, decides what to draw and how it should look, sets the rules and limits, looks at every result and decides what to keep. Claude, under his direction, writes and changes the code, runs the builds, tests and checks, and reports what changed with pictures. isoscape, the code, computes the drawing from open data, deterministically: the same data and code give the same SVG, with no image model and no network while it draws. Arrows run down (asks; runs a build) and back up (shows the result; SVG, counts, warnings): the loop of direct, build, look, correct.',
    parts.join('\n'))
}

// ---- B: where the geometry comes from -----------------------------------------------------------

export const SOURCES: readonly { name: string; note?: string; gives: readonly [Sure, string][] }[] = [
  { name: 'OpenStreetMap', gives: [['measured', 'Streets, rail, water, parks, building outlines'], ['measured', 'Building heights, where mappers tagged them'], ['guessed', 'Other heights, from building type and size']] },
  { name: 'USGS 3DEP lidar', note: 'or a national model', gives: [['measured', 'The ground: hills, banks, the riverbed'], ['inferred', 'River surface, rocks, rapids, shoreline']] },
  { name: 'Microsoft footprints', note: "Gwynn's Island", gives: [['inferred', 'Buildings OSM lacks, traced by a model']] },
  { name: 'NLCD land cover', note: "Gwynn's Island", gives: [['inferred', 'Woods, fields and wetlands, from satellites']] },
  { name: 'City year-built records', note: 'Richmond', gives: [['measured', 'The year each standing building went up']] },
  { name: 'Sanborn maps', note: 'Library of Congress', gives: [['inferred', 'Lost buildings, traced from the scans'], ['guessed', 'Their heights, from their material']] },
  { name: 'Rules in the code', gives: [['guessed', 'Bridge deck heights, by name or layer']] },
]

export const whereFrom = (): string => {
  let y = 14
  const parts: string[] = [t(X0, y + 12, 'WHERE THE GEOMETRY COMES FROM', 'h dim')]
  y += 30
  for (const src of SOURCES) {
    const h = 30 + src.gives.length * 21
    parts.push(box(X0, y, BW, h, 'card'))
    parts.push(t(X0 + 12, y + 21, src.name, 'bb ink'))
    if (src.note) parts.push(t(X0 + BW - 12, y + 21, src.note, 's ink', 'end'))
    src.gives.forEach(([sure, text], i) => {
      const ly = y + 43 + i * 21
      parts.push(mark(X0 + 20, ly - 4.6, sure))
      parts.push(t(X0 + 34, ly, text, 'b ink'))
    })
    y += h + 14
  }
  y += 14
  const key: [Sure, string][] = [['measured', 'measured'], ['inferred', 'inferred'], ['guessed', 'guessed']]
  key.forEach(([sure, label], i) => {
    const x = X0 + 8 + i * 112
    parts.push(mark(x, y - 4.6, sure))
    parts.push(t(x + 13, y, label, 'b ink'))
  })
  parts.push(t(X0, y + 22, 'The marks of the cutaway sheets: drawn, written, approximate.', 'si dim'))
  y += 36
  return svg('src', y, 'Where the geometry comes from',
    'Seven sources and what each gives, each marked measured (a solid disc), inferred (a ring) or guessed (a dashed ring). OpenStreetMap: streets, rail, water, parks and building outlines, measured; building heights where mappers tagged them, measured; other heights, guessed from building type and size. USGS 3DEP lidar, or a national elevation model: the ground, measured; the river surface, rocks, rapids and shoreline, inferred. Microsoft building footprints, used on Gwynn\'s Island: buildings OpenStreetMap lacks, traced by a model, inferred. NLCD land cover, on Gwynn\'s Island: woods, fields and wetlands from satellites, inferred. City of Richmond year-built records: the year each standing building went up, measured. Sanborn fire-insurance maps from the Library of Congress: lost buildings traced from the scans, inferred; their heights from their material, guessed. Rules in the code: bridge deck heights by name or layer, guessed.',
    parts.join('\n'))
}

// ---- C: from data to drawing (the pipeline, shared with How it's made) --------------------------

export const STAGES: readonly { name: string; mod: string; projection?: boolean }[] = [
  { name: 'Read the map data', mod: 'osm.ts' },
  { name: 'What each tag means', mod: 'classify.ts' },
  { name: 'The year, for a dated map', mod: 'history.ts' },
  { name: 'Camera', mod: 'view.ts', projection: true },
  { name: 'Ground, water, rapids', mod: 'terrain.ts' },
  { name: 'Buildings and bridges', mod: 'scene.ts' },
  { name: 'What hides what', mod: 'order.ts' },
  { name: 'Ink, color, dots', mod: 'render.ts' },
]

export const pipeline = (): string => {
  let y = 14
  const parts: string[] = [t(X0, y + 12, 'FROM DATA TO DRAWING', 'h dim')]
  y += 34
  parts.push(t(X0, y, 'fetch: the only step that uses the network', 'si dim'))
  y += 12
  parts.push(box(X0, y, BW, 38, 'card'), t(X0 + 12, y + 24, 'Region file', 'bb ink'), t(X0 + BW - 12, y + 24, 'regions/<name>.json', 'm ink', 'end'))
  y += 38
  parts.push(arrow(W / 2, y + 5, W / 2, y + 21))
  y += 26
  const half = (BW - 12) / 2
  parts.push(box(X0, y, half, 52, 'card'), t(X0 + 12, y + 22, 'OpenStreetMap', 'bb ink'), t(X0 + 12, y + 41, 'osm.ts', 'm ink'))
  parts.push(box(X0 + half + 12, y, half, 52, 'card'), t(X0 + half + 24, y + 22, 'Elevation', 'bb ink'), t(X0 + half + 24, y + 41, 'dem.ts', 'm ink'))
  y += 52
  parts.push(arrow(X0 + half / 2, y + 5, X0 + half / 2, y + 21), arrow(X0 + half * 1.5 + 12, y + 5, X0 + half * 1.5 + 12, y + 21))
  y += 26
  parts.push(box(X0, y, BW, 38, 'cache'), t(X0 + 12, y + 24, 'Local cache', 'bb ink'), t(X0 + BW - 12, y + 24, 'data/<name>/', 'm ink', 'end'))
  y += 38 + 30
  parts.push(t(X0, y, 'build: offline, from the cache, the same every time', 'si dim'))
  y += 12
  STAGES.forEach((s, i) => {
    if (i > 0) parts.push(arrow(W / 2, y + 5, W / 2, y + 19))
    if (i > 0) y += 24
    parts.push(box(X0, y, BW, 36, 'card'), t(X0 + 12, y + 23, s.name, 'bb ink'), t(X0 + BW - 12, y + 23, s.mod, 'm ink', 'end'))
    if (s.projection) {
      parts.push(`<rect x="${n(X0 - 6)}" y="${n(y - 6)}" width="${n(BW + 12)}" height="48" class="hl"/>`)
      parts.push(t(X0, y + 58, 'The projection is this step alone: view.ts is', 'si acc'))
      parts.push(t(X0, y + 75, 'about 90 lines of some 14,000 in src/.', 'si acc'))
      y += 44
    }
    y += 36
  })
  parts.push(arrow(W / 2, y + 5, W / 2, y + 19))
  y += 24
  parts.push(box(X0, y, BW, 56, 'cache'), t(X0 + 12, y + 22, 'The SVG, archived; the explorer', 'bb ink'), t(X0 + 12, y + 42, 'out/<name>.svg  out/index.html', 'm ink'))
  y += 56 + 16
  return svg('pipe', y, 'From data to drawing: the isoscape pipeline',
    'fetch, the only step that uses the network: a region file (regions/<name>.json) drives downloads from OpenStreetMap (osm.ts) and an elevation model (dem.ts) into a local cache (data/<name>/). build, offline and the same every time, runs eight steps: read the map data (osm.ts), what each tag means (classify.ts), the year for a dated map (history.ts), the camera (view.ts), ground, water and rapids (terrain.ts), buildings and bridges (scene.ts), what hides what (order.ts), and ink, color and dots (render.ts). The camera step, marked with a red dashed outline, is the projection: view.ts is about 90 lines of some 14,000 in src/. The SVG is archived and listed in the explorer (out/<name>.svg, out/index.html).',
    parts.join('\n'))
}

// ---- D: from drawing to print -------------------------------------------------------------------

export const toPrint = (): string => {
  let y = 14
  const parts: string[] = [t(X0, y + 12, 'FROM DRAWING TO PRINT', 'h dim')]
  y += 30
  const RW = BW - 34
  const steps: [string, string][] = [
    ['Build the scenes', 'isoscape build: deterministic SVG'],
    ['Look', 'at print size; the visual check'],
    ['Compose the print', 'tools/print/compose.py'],
    ['Title block', 'plate RVA·01, version, year, place'],
    ['Release record', 'commit, inputs by SHA-256'],
    ['Rebuild check', 'check.py --rebuild: same bytes'],
    ['Printed to order', 'from that file, through the shop'],
  ]
  const tops: number[] = []
  steps.forEach(([name, sub], i) => {
    if (i > 0) parts.push(arrow(X0 + RW / 2, y + 5, X0 + RW / 2, y + 19))
    if (i > 0) y += 24
    tops.push(y)
    parts.push(box(X0, y, RW, 52, i === 1 ? 'artist' : 'card'), t(X0 + 12, y + 22, name, 'bb ink'), t(X0 + 12, y + 41, sub, i === 1 ? 's ink' : 'm ink'))
    y += 52
  })
  // A correction goes round again as the next version.
  const rx = X0 + BW - 8
  parts.push(route([[X0 + RW, tops[6] + 26], [rx, tops[6] + 26], [rx, tops[0] + 26], [X0 + RW + 2, tops[0] + 26]]))
  y += 22
  parts.push(box(X0, y, BW, 96, 'card'), `<rect x="${n(X0 - 5)}" y="${n(y - 5)}" width="${n(BW + 10)}" height="106" class="hl"/>`)
  parts.push(t(X0 + 12, y + 22, 'A fault found after release goes round again', 'bb ink'))
  parts.push(t(X0 + 12, y + 42, 'Redrawn as the next version (-v4), never', 'b ink'))
  parts.push(t(X0 + 12, y + 61, 'changed in place. The plate stays; the', 'b ink'))
  parts.push(t(X0 + 12, y + 80, 'Changes page says what changed, and when.', 'b ink'))
  y += 96 + 20
  return svg('print', y, 'From drawing to print',
    'Seven steps: build the scenes (isoscape build, deterministic SVG); look at them at print size, with the visual check; compose the print (tools/print/compose.py); set the title block (plate, such as RVA·01, version, year, place); write the release record (the commit, and every input by SHA-256); run the rebuild check (check.py --rebuild, the same bytes again); and print to order from that file, through the shop. An arrow runs from the last step back to the first: a fault found after release is redrawn as the next version (such as -v4), never changed in place; the plate stays, and the Changes page says what changed and when.',
    parts.join('\n'))
}

// ---- E: using it with an agent ------------------------------------------------------------------

export const withAgent = (): string => {
  let y = 14
  const parts: string[] = [t(X0, y + 12, 'USING IT WITH AN AGENT', 'h dim')]
  y += 26
  const a = lane(y, 'artist', 'You', 'a person', ['Say what place to draw, and how', 'Look at the picture; say what to change'])
  parts.push(a.svg)
  y += a.h
  parts.push(between(y + 6, y + 50, 'a request', 'pictures, a summary'))
  y += 56
  const c = lane(y, 'agent', 'Claude', 'in the app or a terminal', ['Reads CLAUDE.md, the working contract,', 'and AGENTS.md; follows the loop'])
  parts.push(c.svg)
  y += c.h
  parts.push(between(y + 6, y + 50, 'commands', 'files, numbers'))
  y += 56
  const rows: [string, string][] = [
    ['regions/<name>.json', 'the place: center, size'],
    ['fetch', 'downloads into data/'],
    ['build <name> --png', 'out/<name>.png'],
    ['out/index.html', 'the explorer; C compares'],
    ['npm test', 'and npm run typecheck'],
    ['npm run check:visual', 'out/check/index.html'],
  ]
  const h = 34 + rows.length * 22 + 6
  parts.push(box(X0, y, BW, h, 'card'), `<rect x="${n(X0)}" y="${n(y)}" width="10" height="${n(h)}" class="edge code"/>`, dots([[X0 + 10, y], [X0 + 10, y + h]]))
  parts.push(t(X0 + 24, y + 24, 'The repo', 'n ink'), t(X0 + BW - 12, y + 23, 'isoscape', 's ink', 'end'))
  rows.forEach(([cmd, what], i) => {
    const ry = y + 50 + i * 22
    parts.push(t(X0 + 24, ry, cmd, 'm ink'), t(X0 + BW - 12, ry, what, 's ink', 'end'))
  })
  y += h + 24
  parts.push(t(X0, y, 'The loop: change, build, look at the picture,', 'si ink'))
  parts.push(t(X0, y + 18, 'compare with the last build, keep or undo.', 'si ink'))
  y += 34
  return svg('agent', y, 'Using isoscape with a coding agent',
    'Three lanes. You, a person: say what place to draw and how, look at the picture and say what to change. Claude, in the app or a terminal: reads CLAUDE.md, the working contract, and AGENTS.md, and follows the loop. Arrows run down (a request; commands) and back up (pictures and a summary; files and numbers). The repo, isoscape: regions/<name>.json (the place: center, size); fetch (downloads into data/); build <name> --png (out/<name>.png); out/index.html (the explorer, where C compares two builds); npm test and npm run typecheck; npm run check:visual (out/check/index.html). The loop: change, build, look at the picture, compare with the last build, keep or undo.',
    parts.join('\n'))
}

// ---- the link preview: who does what, across ----------------------------------------------------

export const social = (): string => {
  const SW = 1200
  const SH = 630
  const k = 2.4
  const parts: string[] = []
  parts.push(`<text x="60" y="92" style="font:700 44px ${SERIF}" class="ink">Who does what</text>`)
  parts.push(`<text x="${SW - 60}" y="90" text-anchor="end" style="font:600 26px ${SANS};letter-spacing:.06em" class="dim">ISOSCAPE · QUESTIONS</text>`)
  const cols: [string, string, string, string][] = [
    ['artist', 'Chris Busse', 'decides, sets', 'rules, approves'],
    ['agent', 'Claude', 'writes the code,', 'runs it, reports'],
    ['code', 'isoscape', 'computes the', 'map from data'],
  ]
  const cw = 310
  const gap = (SW - 120 - 3 * cw) / 2
  cols.forEach(([fill, name, l1, l2], i) => {
    const x = 60 + i * (cw + gap)
    const y = 170
    const h = 300
    parts.push(`<rect x="${x}" y="${y}" width="${cw}" height="${h}" class="edge card" style="stroke-width:${LINE * k}"/>`)
    parts.push(`<rect x="${x}" y="${y}" width="26" height="${h}" class="edge ${fill}" style="stroke-width:${LINE * k}"/>`)
    for (const [px, py] of [[x, y], [x + cw, y], [x, y + h], [x + cw, y + h], [x + 26, y], [x + 26, y + h]]) parts.push(`<circle cx="${px}" cy="${py}" r="${n(DOT * k)}" class="ink"/>`)
    parts.push(`<text x="${x + 50}" y="${y + 80}" style="font:700 38px ${SERIF}" class="ink">${esc(name)}</text>`)
    parts.push(`<text x="${x + 50}" y="${y + 160}" style="font-size:29px" class="ink">${esc(l1)}</text>`)
    parts.push(`<text x="${x + 50}" y="${y + 204}" style="font-size:29px" class="ink">${esc(l2)}</text>`)
    if (i < 2) {
      const ax = x + cw + 12
      const bx = x + cw + gap - 12
      const ay = y + h / 2
      for (const [x0, x1, yy] of [[ax, bx, ay - 26], [bx, ax, ay + 26]]) {
        const dir = Math.sign(x1 - x0)
        parts.push(`<path d="M${x0} ${yy}L${x1 - dir * 20} ${yy}" class="edge" style="stroke-width:${LINE * k}"/><path d="M${x1} ${yy}L${x1 - dir * 20} ${yy - 10}L${x1 - dir * 20} ${yy + 10}Z" class="ink"/><circle cx="${x0}" cy="${yy}" r="${n(DOT * k * 0.8)}" class="ink"/>`)
      }
    }
  })
  parts.push(`<text x="60" y="560" style="font-size:30px;font-style:italic" class="ink">The loop: direct, build, look, correct. Nothing is kept until Chris approves it.</text>`)
  return svg('social', SH, 'Who does what', 'Chris Busse decides, sets the rules and approves; Claude writes the code, runs it and reports; isoscape computes the drawing from data.', parts.join('\n'), SW)

}

/** Every file this script writes into pages/, by name. */
export const DIAGRAMS: Readonly<Record<string, () => string>> = {
  'faq-who-does-what.svg': whoDoesWhat,
  'faq-sources.svg': whereFrom,
  'pipeline.svg': pipeline,
  'faq-print.svg': toPrint,
  'faq-agent.svg': withAgent,
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const dir = fileURLToPath(new URL('../../pages/', import.meta.url))
  for (const [name, make] of Object.entries(DIAGRAMS)) writeFileSync(dir + name, make())
  const i = process.argv.indexOf('--social')
  if (i > 0 && process.argv[i + 1]) writeFileSync(process.argv[i + 1], social())
  console.error(`wrote ${Object.keys(DIAGRAMS).map((f) => 'pages/' + f).join(', ')}`)
}
