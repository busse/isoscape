/**
 * The explorer: one local page over every archived build.
 *
 * A column of builds on the left, grouped by region and newest first; the selected build in
 * the middle, to pan and zoom; what it is underneath — when, from which commit, what it
 * measured, the settings it was built with. Pick a second build to compare: the two are laid
 * over each other in the same coordinates with a divider to drag, and the info panel shows
 * how their numbers differ.
 *
 * The page is self-contained (the build list is embedded), so it opens straight from disk:
 * `open out/index.html`. It is rewritten after every build; reloading keeps the selection.
 */

import type { BuildMeta } from './archive.ts'

const json = (v: unknown) => JSON.stringify(v).replace(/</g, '\\u003c')

export const renderExplorer = (builds: readonly BuildMeta[]): string => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>isoscape explorer</title>
<style>
:root {
  --bg: #f4f2ed; --panel: #fbfaf7; --line: #e2ded5; --ink: #26252b; --dim: #77737a; --faint: #a7a2a6;
  --accent: #2f6f8f; --accent-soft: #dcebf2; --stage: #e7e4dc; --chip: #efece5; --good: #3c7a4a; --bad: #a3473a;
  font: 13px/1.45 ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #15161b; --panel: #1b1d23; --line: #2b2e37; --ink: #e5e6ec; --dim: #9497a3; --faint: #646875;
    --accent: #7fb6d4; --accent-soft: #22323d; --stage: #101115; --chip: #252831; --good: #7fc28f; --bad: #e08c7e; }
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: var(--bg); color: var(--ink); }
body { display: grid; grid-template-columns: 300px 1fr; grid-template-rows: 100%; overflow: hidden; }
button { font: inherit; color: inherit; }
kbd { font: 11px ui-monospace, SFMono-Regular, Menlo, monospace; padding: 0 4px; border: 1px solid var(--line); border-radius: 3px; color: var(--dim); }

/* ---- nav ---------------------------------------------------------------- */
#nav { display: flex; flex-direction: column; min-height: 0; background: var(--panel); border-right: 1px solid var(--line); }
#nav header { padding: 14px 16px 10px; display: flex; align-items: baseline; gap: 8px; }
#nav header b { font-size: 15px; letter-spacing: -.01em; }
#nav header span { color: var(--dim); }
#nav header .count { margin-left: auto; font-size: 12px; color: var(--faint); }
#filter { margin: 0 12px 10px; padding: 6px 9px; border: 1px solid var(--line); border-radius: 6px; background: var(--bg); color: var(--ink); font: inherit; outline: none; }
#filter:focus { border-color: var(--accent); }
#list { overflow-y: auto; flex: 1; padding: 0 8px 16px; }
#list h2 { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--dim); margin: 14px 8px 6px; }
#list h2 small { display: block; text-transform: none; letter-spacing: 0; font-weight: 400; color: var(--faint); font-size: 11px; }
.build { display: grid; grid-template-columns: 76px 1fr; gap: 10px; width: 100%; padding: 7px 8px; border: 1px solid transparent; border-radius: 7px; background: none; text-align: left; cursor: pointer; align-items: center; }
.build:hover { background: var(--chip); }
.build.a { background: var(--accent-soft); border-color: var(--accent); }
.build.b { border-color: var(--accent); border-style: dashed; }
.thumb { width: 76px; height: 46px; border-radius: 4px; border: 1px solid var(--line); object-fit: cover; object-position: center 60%; display: block; }
.swatch { width: 76px; height: 46px; border-radius: 4px; border: 1px solid var(--line); display: grid; place-items: center; font-size: 10px; color: #888; }
.build .top { display: flex; gap: 6px; align-items: center; font-size: 12px; }
.build .note { font-size: 12px; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.build .sub { font-size: 11px; color: var(--faint); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.tag { font-size: 10.5px; padding: 0 6px; border-radius: 9px; background: var(--chip); color: var(--dim); }
.tag.ab { background: var(--accent); color: var(--panel); font-weight: 600; }
time { color: var(--dim); margin-left: auto; font-size: 11px; }
#nav footer { padding: 10px 14px; border-top: 1px solid var(--line); color: var(--faint); font-size: 11px; line-height: 1.7; }

/* ---- main ---------------------------------------------------------------- */
main { display: grid; grid-template-rows: 1fr auto; min-height: 0; min-width: 0; }
#stage { position: relative; overflow: hidden; background: var(--stage); cursor: grab; touch-action: none; user-select: none; }
#stage.dragging { cursor: grabbing; }
#stage img { position: absolute; max-width: none; pointer-events: none; image-rendering: auto; }
#clipB { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
#divider { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; background: var(--accent); cursor: ew-resize; display: none; }
#divider::after { content: "A │ B"; position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); white-space: nowrap; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; background: var(--accent); color: var(--panel); }
#divider::before { content: ""; position: absolute; inset: 0 -8px; }
#empty { position: absolute; inset: 0; display: grid; place-items: center; color: var(--dim); text-align: center; padding: 40px; }
#toolbar { position: absolute; top: 12px; right: 12px; display: flex; gap: 6px; align-items: center; }
#toolbar button, #toolbar select { border: 1px solid var(--line); background: var(--panel); border-radius: 6px; padding: 4px 9px; cursor: pointer; font: inherit; color: var(--ink); }
#toolbar button.on { background: var(--accent); color: var(--panel); border-color: var(--accent); }
#toolbar .zoom { font-variant-numeric: tabular-nums; color: var(--dim); background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 4px 8px; min-width: 56px; text-align: center; }
#loading { position: absolute; left: 12px; top: 12px; font-size: 12px; color: var(--dim); background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 3px 8px; display: none; }

/* ---- info ---------------------------------------------------------------- */
#info { border-top: 1px solid var(--line); background: var(--panel); max-height: 38vh; overflow: auto; }
#info.closed .body { display: none; }
#info .bar { display: flex; align-items: center; gap: 10px; padding: 8px 16px; position: sticky; top: 0; background: var(--panel); border-bottom: 1px solid var(--line); }
#info .bar h1 { font-size: 14px; margin: 0; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
#info .bar .links { margin-left: auto; display: flex; gap: 12px; white-space: nowrap; }
#info .bar a { color: var(--accent); text-decoration: none; font-size: 12px; }
#info .bar button { border: none; background: none; cursor: pointer; color: var(--dim); }
#info .body { display: grid; grid-template-columns: minmax(240px, 1fr) minmax(280px, 1.4fr) minmax(240px, 1fr); gap: 22px; padding: 12px 16px 16px; }
#info h3 { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--dim); margin: 0 0 6px; }
dl { display: grid; grid-template-columns: auto 1fr; gap: 3px 12px; margin: 0; font-size: 12.5px; }
dt { color: var(--dim); }
dd { margin: 0; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
table { border-collapse: collapse; width: 100%; font-size: 12.5px; font-variant-numeric: tabular-nums; }
th, td { text-align: right; padding: 2px 6px; border-bottom: 1px solid var(--line); white-space: nowrap; }
th:first-child, td:first-child { text-align: left; color: var(--dim); font-weight: 400; }
th { font-weight: 600; font-size: 11px; color: var(--dim); }
td.up { color: var(--good); } td.down { color: var(--bad); }
#info .settings table { table-layout: fixed; }
#info .settings td { white-space: normal; overflow-wrap: anywhere; text-align: left; }
#info .settings td:first-child { width: 38%; }
pre { margin: 0; font: 11.5px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--bg); border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; max-height: 26vh; overflow: auto; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
.dirty { color: var(--bad); }
</style>
</head>
<body>
<nav id="nav">
  <header><b>isoscape</b><span>explorer</span><span class="count" id="count"></span></header>
  <input id="filter" placeholder="Filter by region, palette, note, commit…" spellcheck="false">
  <div id="list"></div>
  <footer>Click to view · <kbd>⌥</kbd>-click to compare<br><kbd>↑</kbd><kbd>↓</kbd> builds · <kbd>F</kbd> fit · <kbd>1</kbd> 1:1 · <kbd>C</kbd> compare · <kbd>I</kbd> info</footer>
</nav>
<main>
  <div id="stage">
    <img id="imgA" alt="">
    <div id="clipB"><img id="imgB" alt=""></div>
    <div id="divider"></div>
    <div id="empty"></div>
    <div id="loading">loading…</div>
    <div id="toolbar">
      <span class="zoom" id="zoom">–</span>
      <button id="fit" title="Fit (F)">Fit</button>
      <button id="actual" title="Actual size (1)">1:1</button>
      <button id="compare" title="Compare (C)">Compare</button>
      <select id="pickB" title="Compare with" hidden></select>
    </div>
  </div>
  <section id="info">
    <div class="bar"><button id="toggleInfo" title="Info (I)">▾</button><h1 id="infoTitle"></h1><div class="links" id="links"></div></div>
    <div class="body" id="infoBody"></div>
  </section>
</main>
<script type="application/json" id="builds">${json(builds)}</script>
<script>
(() => {
  const builds = JSON.parse(document.getElementById('builds').textContent)
  const byId = new Map(builds.map((b) => [b.id, b]))
  const $ = (id) => document.getElementById(id)
  const stage = $('stage'), imgA = $('imgA'), imgB = $('imgB'), clipB = $('clipB'), divider = $('divider')
  const state = { a: null, b: null, compare: false, zoom: 1, panX: 0, panY: 0, split: 0.5, filter: '' }

  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
  const ago = (iso) => {
    const s = (Date.now() - new Date(iso).getTime()) / 1000
    if (s < 60) return 'just now'
    if (s < 3600) return Math.round(s / 60) + 'm ago'
    if (s < 86400) return Math.round(s / 3600) + 'h ago'
    if (s < 86400 * 14) return Math.round(s / 86400) + 'd ago'
    return new Date(iso).toLocaleDateString()
  }
  const when = (iso) => new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
  const mb = (n) => (n / 1e6).toFixed(2) + ' MB'
  const label = (b) => b.note || (b.git ? b.git.subject : b.region)

  // ---- nav ------------------------------------------------------------------------------------
  const visible = () => {
    const q = state.filter.toLowerCase().trim()
    if (!q) return builds
    return builds.filter((b) => [b.region, b.title, b.palette, b.note, b.git && b.git.commit, b.git && b.git.subject, b.name].join(' ').toLowerCase().includes(q))
  }
  const renderList = () => {
    const list = visible()
    $('count').textContent = builds.length + (builds.length === 1 ? ' build' : ' builds')
    const groups = new Map()
    for (const b of list) {
      if (!groups.has(b.region)) groups.set(b.region, [])
      groups.get(b.region).push(b)
    }
    let html = ''
    for (const [region, items] of groups) {
      html += '<h2>' + esc(items[0].config.title || region) + '<small>' + esc(region) + '</small></h2>'
      for (const b of items) {
        const cls = 'build' + (state.a === b.id ? ' a' : '') + (state.compare && state.b === b.id ? ' b' : '')
        const pic = b.files.thumb
          ? '<img class="thumb" loading="lazy" src="' + esc(b.files.thumb) + '" alt="">'
          : '<div class="swatch" style="background:' + esc(b.sky) + '">' + esc(b.palette) + '</div>'
        const ab = state.a === b.id ? '<span class="tag ab">A</span>' : state.compare && state.b === b.id ? '<span class="tag ab">B</span>' : ''
        html += '<button class="' + cls + '" data-id="' + esc(b.id) + '">' + pic +
          '<div><div class="top">' + ab + '<span class="tag">' + esc(b.palette) + '</span>' +
          (b.config.terrain ? '<span class="tag">terrain</span>' : '') +
          '<time datetime="' + esc(b.createdAt) + '">' + ago(b.createdAt) + '</time></div>' +
          '<div class="note" title="' + esc(label(b)) + '">' + esc(label(b)) + '</div>' +
          '<div class="sub">' + (b.git ? esc(b.git.commit) + (b.git.dirty ? '<span class="dirty">*</span>' : '') : '') + ' · ' + mb(b.bytes) + '</div></div></button>'
      }
    }
    $('list').innerHTML = html || '<p style="padding:12px;color:var(--dim)">No builds match.</p>'
    const cur = $('list').querySelector('.build.a')
    if (cur) cur.scrollIntoView({ block: 'nearest' })
  }
  $('list').addEventListener('click', (e) => {
    const el = e.target.closest('.build')
    if (!el) return
    if (e.altKey || e.metaKey || e.shiftKey) { state.b = el.dataset.id; state.compare = true }
    else select(el.dataset.id, false)
    update()
  })
  $('filter').addEventListener('input', (e) => { state.filter = e.target.value; renderList() })

  // ---- viewer ---------------------------------------------------------------------------------
  const place = (img, b) => {
    const vb = b.viewBox
    img.style.left = state.panX + vb[0] * state.zoom + 'px'
    img.style.top = state.panY + vb[1] * state.zoom + 'px'
    img.style.width = vb[2] * state.zoom + 'px'
    img.style.height = vb[3] * state.zoom + 'px'
  }
  const layout = () => {
    const a = byId.get(state.a)
    if (!a) return
    place(imgA, a)
    const b = state.compare ? byId.get(state.b) : null
    clipB.style.display = b ? 'block' : 'none'
    divider.style.display = b ? 'block' : 'none'
    if (b) {
      place(imgB, b)
      const x = stage.clientWidth * state.split
      clipB.style.clipPath = 'inset(0 0 0 ' + x + 'px)'
      divider.style.left = x + 'px'
    }
    $('zoom').textContent = Math.round(state.zoom * 100) + '%'
  }
  const fit = () => {
    const a = byId.get(state.a)
    if (!a) return
    const vb = a.viewBox
    const w = stage.clientWidth, h = stage.clientHeight
    state.zoom = Math.min(w / vb[2], h / vb[3]) * 0.94
    state.panX = (w - vb[2] * state.zoom) / 2 - vb[0] * state.zoom
    state.panY = (h - vb[3] * state.zoom) / 2 - vb[1] * state.zoom
    layout()
  }
  const zoomAt = (mx, my, k) => {
    const ux = (mx - state.panX) / state.zoom
    const uy = (my - state.panY) / state.zoom
    state.zoom = Math.min(40, Math.max(0.02, state.zoom * k))
    state.panX = mx - ux * state.zoom
    state.panY = my - uy * state.zoom
    layout()
  }
  const actual = () => {
    const r = stage.getBoundingClientRect()
    zoomAt(r.width / 2, r.height / 2, 1 / state.zoom)
  }
  stage.addEventListener('wheel', (e) => {
    e.preventDefault()
    const r = stage.getBoundingClientRect()
    zoomAt(e.clientX - r.left, e.clientY - r.top, Math.exp(-e.deltaY * 0.0015))
  }, { passive: false })
  let drag = null
  stage.addEventListener('pointerdown', (e) => {
    if (e.target.closest('#toolbar')) return
    drag = { x: e.clientX, y: e.clientY, divider: e.target === divider }
    stage.setPointerCapture(e.pointerId)
    if (!drag.divider) stage.classList.add('dragging')
  })
  stage.addEventListener('pointermove', (e) => {
    if (!drag) return
    if (drag.divider) {
      const r = stage.getBoundingClientRect()
      state.split = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width))
    } else {
      state.panX += e.clientX - drag.x
      state.panY += e.clientY - drag.y
      drag.x = e.clientX
      drag.y = e.clientY
    }
    layout()
  })
  stage.addEventListener('pointerup', () => { drag = null; stage.classList.remove('dragging') })
  stage.addEventListener('dblclick', (e) => { if (!e.target.closest('#toolbar')) fit() })
  new ResizeObserver(() => layout()).observe(stage)

  const load = (img, b) => {
    if (img.dataset.id === b.id) return
    img.dataset.id = b.id
    $('loading').style.display = 'block'
    img.onload = img.onerror = () => { $('loading').style.display = 'none' }
    img.src = b.files.svg
  }

  // ---- info -------------------------------------------------------------------------------------
  const STAT_ORDER = ['buildings', 'heightFromTag', 'heightFromLevels', 'heightGuessed', 'bridgePieces', 'ground', 'ribbons', 'elevationDatum', 'elevationTop', 'rapidCells', 'contourSegments', 'strips', 'features']
  const statKeys = (...bs) => {
    const keys = new Set()
    for (const b of bs) for (const k of Object.keys(b.stats)) keys.add(k)
    return [...STAT_ORDER.filter((k) => keys.has(k)), ...[...keys].filter((k) => !STAT_ORDER.includes(k)).sort()]
  }
  const fmt = (v) => (v === undefined ? '–' : typeof v === 'number' ? (Number.isInteger(v) ? v.toLocaleString() : v.toFixed(2)) : esc(v))
  const renderInfo = () => {
    const a = byId.get(state.a)
    if (!a) { $('infoTitle').textContent = ''; $('infoBody').innerHTML = ''; $('links').innerHTML = ''; return }
    const b = state.compare ? byId.get(state.b) : null
    $('infoTitle').textContent = b ? a.title + '  ·  A vs B' : a.title
    $('links').innerHTML = '<a href="' + esc(a.files.svg) + '" target="_blank">Open A’s SVG ↗</a>' +
      (b ? '<a href="' + esc(b.files.svg) + '" target="_blank">Open B’s SVG ↗</a>' : '') +
      '<a href="' + esc(a.name) + '.html" target="_blank" title="The latest build of this region, with hover labels">Latest page ↗</a>'
    const about = (x, tag) =>
      '<dl>' +
      (tag ? '<dt>' + tag + '</dt><dd><b>' + esc(label(x)) + '</b></dd>' : '<dt>note</dt><dd>' + (x.note ? '<b>' + esc(x.note) + '</b>' : '<span style="color:var(--faint)">none</span>') + '</dd>') +
      '<dt>built</dt><dd>' + when(x.createdAt) + '</dd>' +
      '<dt>commit</dt><dd class="mono">' + (x.git ? esc(x.git.commit) + (x.git.dirty ? ' <span class="dirty">+ uncommitted changes</span>' : '') + '<br><span style="color:var(--dim)">' + esc(x.git.subject) + '</span>' : '–') + '</dd>' +
      '<dt>region</dt><dd class="mono">' + esc(x.region) + '</dd>' +
      '<dt>palette</dt><dd>' + esc(x.palette) + '</dd>' +
      '<dt>bearing</dt><dd>' + x.bearing.toFixed(1) + '°</dd>' +
      '<dt>size</dt><dd>' + mb(x.bytes) + ' · ' + Math.round(x.viewBox[2]) + '×' + Math.round(x.viewBox[3]) + ' · ' + x.ms + ' ms</dd>' +
      '</dl>'
    let stats
    if (b) {
      stats = '<table><tr><th>stat</th><th>A</th><th>B</th><th>Δ</th></tr>' + statKeys(a, b).map((k) => {
        const va = a.stats[k], vb = b.stats[k]
        const d = typeof va === 'number' && typeof vb === 'number' ? vb - va : undefined
        const cls = d === undefined || d === 0 ? '' : d > 0 ? 'up' : 'down'
        return '<tr><td>' + esc(k) + '</td><td>' + fmt(va) + '</td><td>' + fmt(vb) + '</td><td class="' + cls + '">' + (d === undefined || d === 0 ? '' : (d > 0 ? '+' : '') + fmt(d)) + '</td></tr>'
      }).join('') + '</table>'
    } else {
      stats = '<table>' + statKeys(a).map((k) => '<tr><td>' + esc(k) + '</td><td>' + fmt(a.stats[k]) + '</td></tr>').join('') + '</table>'
    }
    const configDiff = (x, y) => {
      const flat = (o, p = '') => Object.entries(o).flatMap(([k, v]) => v && typeof v === 'object' && !Array.isArray(v) ? flat(v, p + k + '.') : [[p + k, JSON.stringify(v)]])
      const fx = new Map(flat(x.config)), fy = new Map(flat(y.config))
      const keys = [...new Set([...fx.keys(), ...fy.keys()])].filter((k) => fx.get(k) !== fy.get(k) && k !== 'name')
      if (keys.length === 0) return '<p style="margin:0;color:var(--dim)">Same settings.</p>'
      return '<table><tr><th>setting</th><th>A</th><th>B</th></tr>' + keys.map((k) => '<tr><td>' + esc(k) + '</td><td class="mono">' + esc(fx.get(k) ?? '–') + '</td><td class="mono">' + esc(fy.get(k) ?? '–') + '</td></tr>').join('') + '</table>'
    }
    $('infoBody').innerHTML =
      '<div><h3>' + (b ? 'A' : 'Build') + '</h3>' + about(a, b ? 'A' : '') + (b ? '<h3 style="margin-top:12px">B</h3>' + about(b, 'B') : '') + '</div>' +
      '<div><h3>Measures</h3>' + stats + '</div>' +
      '<div class="settings"><h3>' + (b ? 'Settings that differ' : 'Settings') + '</h3>' + (b ? configDiff(a, b) : '<pre>' + esc(JSON.stringify(a.config, null, 2)) + '</pre>') + '</div>'
  }
  $('toggleInfo').addEventListener('click', () => toggleInfo())
  const toggleInfo = () => {
    $('info').classList.toggle('closed')
    $('toggleInfo').textContent = $('info').classList.contains('closed') ? '▸' : '▾'
  }

  // ---- compare --------------------------------------------------------------------------------
  const defaultB = (aId) => {
    const a = byId.get(aId)
    const same = builds.filter((x) => x.id !== aId && x.region === a.region && x.palette === a.palette)
    const older = same.find((x) => x.createdAt < a.createdAt)
    return (older || same[0] || builds.find((x) => x.id !== aId) || {}).id || null
  }
  const renderPick = () => {
    const pick = $('pickB')
    pick.hidden = !state.compare
    $('compare').classList.toggle('on', state.compare)
    if (!state.compare) return
    pick.innerHTML = builds.filter((x) => x.id !== state.a).map((x) =>
      '<option value="' + esc(x.id) + '"' + (x.id === state.b ? ' selected' : '') + '>B: ' + esc(x.region + ' · ' + x.palette + ' · ' + ago(x.createdAt) + ' · ' + label(x)).slice(0, 90) + '</option>').join('')
  }
  $('pickB').addEventListener('change', (e) => { state.b = e.target.value; update() })
  const toggleCompare = () => {
    state.compare = !state.compare
    if (state.compare && (!state.b || state.b === state.a)) state.b = defaultB(state.a)
    if (!state.b) state.compare = false
    update()
  }
  $('compare').addEventListener('click', toggleCompare)
  $('fit').addEventListener('click', fit)
  $('actual').addEventListener('click', actual)

  // ---- selection, history, keys ------------------------------------------------------------------
  const select = (id, refit) => {
    const prev = byId.get(state.a)
    state.a = id
    if (state.b === id) state.b = defaultB(id)
    const next = byId.get(id)
    // Keep the view when stepping between builds of the same frame, so they can be flicked
    // through; refit when the frame changes.
    if (refit || !prev || prev.region !== next.region || prev.viewBox.join() !== next.viewBox.join()) state.refit = true
  }
  const update = () => {
    const a = byId.get(state.a)
    $('empty').style.display = a ? 'none' : 'grid'
    if (!a) return
    load(imgA, a)
    if (state.compare && byId.get(state.b)) load(imgB, byId.get(state.b))
    if (state.refit) { state.refit = false; fit() } else layout()
    renderList()
    renderPick()
    renderInfo()
    const hash = '#' + state.a + (state.compare && state.b ? '..' + state.b : '')
    if (location.hash !== hash) history.replaceState(null, '', hash)
  }
  document.addEventListener('keydown', (e) => {
    if (e.target === $('filter')) { if (e.key === 'Escape') e.target.blur(); return }
    const list = visible()
    const i = list.findIndex((b) => b.id === state.a)
    if (e.key === 'ArrowDown' || e.key === 'j') { if (i < list.length - 1) { select(list[i + 1].id); update() } e.preventDefault() }
    else if (e.key === 'ArrowUp' || e.key === 'k') { if (i > 0) { select(list[i - 1].id); update() } e.preventDefault() }
    else if (e.key === 'f' || e.key === 'F') fit()
    else if (e.key === '1') actual()
    else if (e.key === 'c' || e.key === 'C') toggleCompare()
    else if (e.key === 'i' || e.key === 'I') toggleInfo()
    else if (e.key === '/') { $('filter').focus(); e.preventDefault() }
  })

  if (builds.length === 0) {
    $('empty').innerHTML = '<div><b>No builds yet.</b><br>Run <code>node bin/isoscape.js build &lt;region&gt;</code> and reload.</div>'
    renderList()
    return
  }
  const [ha, hb] = location.hash.slice(1).split('..')
  select(byId.has(ha) ? ha : builds[0].id, true)
  if (hb && byId.has(hb)) { state.b = hb; state.compare = true }
  update()
})()
</script>
</body>
</html>
`
