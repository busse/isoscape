/**
 * The explorer: one local page over every archived build.
 *
 * A column of builds on the left, grouped by region and newest first; the selected build in
 * the middle, to pan and zoom; what it is underneath — when, from which commit, what it
 * measured, the settings it was built with. Pick a second build to compare: the two are laid
 * over each other in the same coordinates with a divider to drag, and the info panel shows
 * how their numbers differ.
 *
 * Content pages (Markdown in `pages/`, compiled by `pages.ts`) are listed above the builds and
 * open in a reading view at `#/<slug>`. Each build also gets a "How this view was made" tab,
 * written from its meta.json, that links into those pages.
 *
 * The page is self-contained (the build list and the pages are embedded), so it opens straight
 * from disk: `open out/index.html`. It is rewritten after every build; reloading keeps the
 * selection.
 *
 * Routes (the URL hash): `#<id>` one build, `#<idA>..<idB>` compare, either with `/made` for
 * the "How this view was made" tab; `#/<slug>` a page, `#/<slug>/<section>` a section of it.
 *
 * A build route can also carry the window view, so a link reopens the same part of the picture:
 *
 *   #<idA>[..<idB>][@<cx>,<cy>,<z>][~<split>][/made]
 *
 * `cx,cy` is the centre of the visible area in the image's own SVG viewBox units (1 decimal),
 * and `z` the zoom relative to "fit" (3 significant digits; 1 is fit, 2 twice as close), so the
 * same link frames the same part of the picture on any screen size. `~<split>` is the compare
 * divider's position as a fraction of the stage width (only when comparing and not centred).
 * The view is left out while it is the fitted view. Anything malformed falls back to fit. The
 * hash follows panning and zooming (debounced, with replaceState, so Back is not flooded);
 * choosing a build, comparing or changing tab still makes a history entry. The Link button
 * (or L) copies the URL of the build's (or page's) share page, `s/<id>.html` or
 * `s/page-<slug>.html`, with the current fragment: link previews then show that build, and
 * the share page passes the fragment on, so the link still opens this exact view (see
 * social.ts). Under the site URL when one is set, else beside this file.
 */

import type { BuildMeta } from './archive.ts'
import type { Page } from './pages.ts'
import { escAttr, siteTags, type SiteCard } from './social.ts'

const escHtml = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c] as string)
const json = (v: unknown) => JSON.stringify(v).replace(/</g, '\\u003c')

export const renderExplorer = (builds: readonly BuildMeta[], pages: readonly Page[] = [], site: SiteCard = {}): string => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>isoscape explorer</title>
${siteTags(site, builds.length)}<style>
:root {
  --bg: #f4f2ed; --panel: #fbfaf7; --line: #e2ded5; --ink: #26252b; --dim: #77737a; --faint: #a7a2a6;
  --accent: #2f6f8f; --accent-soft: #dcebf2; --stage: #e7e4dc; --chip: #efece5; --good: #3c7a4a; --bad: #a3473a; --warn: #b8860b;
  font: 13px/1.45 ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #15161b; --panel: #1b1d23; --line: #2b2e37; --ink: #e5e6ec; --dim: #9497a3; --faint: #646875;
    --accent: #7fb6d4; --accent-soft: #22323d; --stage: #101115; --chip: #252831; --good: #7fc28f; --bad: #e08c7e; --warn: #f2c94c; }
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
#nav a.shop { display: block; margin: 0 16px 8px; padding: 6px 10px; border-radius: 6px; background: var(--accent-soft); color: var(--accent); text-decoration: none; font-weight: 600; }
#nav a.shop:hover { background: var(--accent); color: var(--panel); }
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
.big { color: var(--warn); cursor: help; }
.tag { font-size: 10.5px; padding: 0 6px; border-radius: 9px; background: var(--chip); color: var(--dim); }
.tag.ab { background: var(--accent); color: var(--panel); font-weight: 600; }
time { color: var(--dim); margin-left: auto; font-size: 11px; }
.tag.yr { background: var(--accent-soft); color: var(--ink); font-weight: 600; }
#timeline { position: absolute; top: 10px; left: 10px; right: 10px; display: flex; flex-wrap: wrap; gap: 4px; align-items: center; pointer-events: none; }
#timeline[hidden] { display: none; }
#timeline button { pointer-events: auto; font: 600 12px ui-sans-serif, system-ui, sans-serif; padding: 3px 8px; border-radius: 12px; border: 1px solid var(--line); background: var(--panel); color: var(--ink); cursor: pointer; }
#timeline button:hover { border-color: var(--accent); }
#timeline button.on { background: var(--accent); border-color: var(--accent); color: var(--panel); }
#timeline .hint { pointer-events: none; font-size: 11px; color: var(--faint); margin-left: 6px; }
.story ul.sources { font-size: 12px; color: var(--dim); }
#nav footer { padding: 10px 14px; border-top: 1px solid var(--line); color: var(--faint); font-size: 11px; line-height: 1.7; }
#nav footer a { color: var(--dim); }

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

/* ---- pages: nav ---------------------------------------------------------------- */
#pages { padding: 0 8px 8px; }
#pages a { display: flex; align-items: baseline; gap: 8px; padding: 5px 8px; border-radius: 6px; color: var(--ink); text-decoration: none; font-size: 13px; }
#pages a:hover { background: var(--chip); }
#pages a.on { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
#pages a::before { content: "§"; color: var(--faint); font-weight: 400; width: 10px; }
#pages a.on::before { color: var(--accent); }

/* ---- pages: reading view --------------------------------------------------------- */
#page { display: none; overflow-y: auto; background: var(--panel); min-height: 0; }
body.reading #stage, body.reading #info { display: none; }
body.reading #page { display: block; }
body.reading main { grid-template-rows: 1fr; }
.doc { display: grid; grid-template-columns: minmax(0, 70ch) 220px; gap: 56px; justify-content: center; padding: 28px 40px 80px; }
@media (max-width: 1180px) { .doc { grid-template-columns: minmax(0, 70ch); } #toc { display: none; } }
.doc .back { display: inline-block; margin-bottom: 18px; font-size: 12.5px; color: var(--accent); text-decoration: none; border: 1px solid var(--line); border-radius: 14px; padding: 3px 11px; background: var(--bg); cursor: pointer; }
.doc .back:hover { border-color: var(--accent); }
.prose { font-size: 15.5px; line-height: 1.65; color: var(--ink); min-width: 0; }
.prose h1 { font-size: 30px; line-height: 1.15; letter-spacing: -.02em; margin: 0 0 18px; font-weight: 650; }
.prose h2 { font-size: 20px; letter-spacing: -.01em; margin: 2.2em 0 .5em; padding-top: .6em; border-top: 1px solid var(--line); font-weight: 650; }
.prose h3 { font-size: 16px; margin: 1.6em 0 .4em; }
.prose h4 { font-size: 13px; text-transform: uppercase; letter-spacing: .05em; color: var(--dim); margin: 1.5em 0 .3em; }
.prose h2, .prose h3 { scroll-margin-top: 16px; }
.prose p, .prose ul, .prose ol, .prose blockquote, .prose .table, .prose pre { margin: 0 0 1em; }
.prose ul, .prose ol { padding-left: 1.3em; }
.prose li { margin: .25em 0; }
.prose li::marker { color: var(--faint); }
.prose a { color: var(--accent); text-decoration: underline; text-decoration-color: color-mix(in srgb, var(--accent) 35%, transparent); text-underline-offset: 2px; }
.prose a:hover { text-decoration-color: var(--accent); }
.prose code { font: .86em ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--chip); padding: .05em .25em; border-radius: 4px; }
.prose pre { max-height: none; font-size: 12.5px; }
.prose pre code { background: none; padding: 0; font-size: inherit; }
.prose blockquote { margin-left: 0; padding: .5em 1em; border-left: 3px solid var(--accent); background: var(--bg); border-radius: 0 6px 6px 0; }
.prose blockquote p:last-child { margin-bottom: 0; }
.prose img { display: block; max-width: 100%; height: auto; margin: 1.4em auto; }
.prose hr { border: none; border-top: 1px solid var(--line); margin: 2em 0; }
.prose .table { overflow-x: auto; }
.prose table { font-size: 13.5px; font-variant-numeric: normal; }
.prose th, .prose td { text-align: left; white-space: normal; vertical-align: top; padding: 6px 10px 6px 0; color: var(--ink); }
.prose th { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--dim); border-bottom: 1.5px solid var(--line); }
.prose td:first-child { color: var(--ink); font-weight: 500; }
.prose .source { margin-top: 3em; padding-top: 1em; border-top: 1px solid var(--line); font-size: 12.5px; color: var(--faint); }
#toc { position: sticky; top: 28px; align-self: start; font-size: 12.5px; max-height: calc(100vh - 56px); overflow-y: auto; }
#toc h3 { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--dim); margin: 6px 0 8px; }
#toc a { display: block; padding: 3px 0 3px 10px; border-left: 2px solid var(--line); color: var(--dim); text-decoration: none; }
#toc a:hover { color: var(--ink); }
#toc a.on { color: var(--accent); border-left-color: var(--accent); }

/* ---- info: tabs and the per-build story ---------------------------------------- */
#info .tabs { display: flex; gap: 2px; margin-left: 8px; }
#info .bar .tabs button { padding: 2px 10px; border-radius: 12px; font-size: 12px; color: var(--dim); }
#info .bar .tabs button:hover { color: var(--ink); background: var(--chip); }
#info .bar .tabs button.on { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
#info.made { max-height: 52vh; }
#info .body.stories { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 40px; padding: 14px 24px 22px; }
.story { font-size: 13.5px; line-height: 1.6; display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 380px), 1fr)); gap: 0 36px; align-content: start; }
.story > h3, .story > .lede, .story > .credit { grid-column: 1 / -1; }
.story section { max-width: 72ch; }
.story h3 { margin: 0 0 8px; }
.story h4 { font-size: 13px; margin: 12px 0 3px; font-weight: 600; }
.story h4 a { font-weight: 400; font-size: 11.5px; margin-left: 6px; }
.story p { margin: 0 0 6px; }
.story ul { margin: 0 0 6px; padding-left: 1.2em; }
.story li { margin: 2px 0; }
.story a { color: var(--accent); text-decoration: none; }
.story a:hover { text-decoration: underline; }
.story .lede { font-size: 14.5px; max-width: 110ch; margin-bottom: 2px; }
.story .unknown { color: var(--faint); }
.story code { font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--chip); padding: 0 4px; border-radius: 3px; }
.story .credit { margin-top: 14px; padding-top: 8px; border-top: 1px solid var(--line); font-size: 12px; color: var(--dim); }
.mixbar { display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin: 6px 0 4px; max-width: 360px; background: var(--chip); }
.mixbar span { display: block; height: 100%; }
.m-tag { background: var(--good); } .m-model { background: #8a7bb8; } .m-lev { background: var(--accent); } .m-guess { background: var(--faint); }
.doc .back[hidden] { display: none; }
#page:focus { outline: none; }
.story ul.keyed { list-style: none; padding-left: 0; }
.key { display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 4px; vertical-align: -1px; }
</style>
</head>
<body>
<nav id="nav">
  <header><b>isoscape</b><span>explorer</span><span class="count" id="count"></span></header>${site.shop ? `
  <a class="shop" href="${escAttr(site.shop.url)}" target="_blank" rel="noopener">${escHtml(site.shop.label)} ↗</a>` : ''}
  <div id="pages"></div>
  <input id="filter" placeholder="Filter by region, palette, note, commit…" spellcheck="false">
  <div id="list"></div>
  <footer>Click to view · <kbd>⌥</kbd>-click to compare<br><kbd>↑</kbd><kbd>↓</kbd> builds · <kbd>F</kbd> fit · <kbd>1</kbd> 1:1 · <kbd>C</kbd> compare · <kbd>L</kbd> copy link<br><kbd>I</kbd> info · <kbd>M</kbd> how it was made · <kbd>Esc</kbd> back<br><kbd>[</kbd><kbd>]</kbd> step through a dated series<br>By Chris Busse · <a href="#/about/contact">Contact</a></footer>
</nav>
<main>
  <div id="stage">
    <img id="imgA" alt="">
    <div id="clipB"><img id="imgB" alt=""></div>
    <div id="divider"></div>
    <div id="empty"></div>
    <div id="loading">loading…</div>
    <div id="timeline" hidden></div>
    <div id="toolbar">
      <span class="zoom" id="zoom">–</span>
      <button id="fit" title="Fit (F)">Fit</button>
      <button id="actual" title="Actual size (1)">1:1</button>
      <button id="compare" title="Compare (C)">Compare</button>
      <button id="link" title="Copy a link to this view, with a link preview (L)">Link</button>
      <select id="pickB" title="Compare with" hidden></select>
    </div>
  </div>
  <section id="info">
    <div class="bar"><button id="toggleInfo" title="Info (I)">▾</button><h1 id="infoTitle"></h1>
      <div class="tabs" id="tabs"><button data-tab="details" title="Details (I)">Details</button><button data-tab="made" title="How this view was made (M)">How this view was made</button></div>
      <div class="links" id="links"></div></div>
    <div class="body" id="infoBody"></div>
  </section>
  <section id="page" tabindex="-1"><div class="doc"><div><a class="back" id="back" hidden></a><article class="prose" id="article"></article></div><aside id="toc"></aside></div></section>
</main>
<script type="application/json" id="site">${json({ siteUrl: site.siteUrl ?? null, shop: site.shop ?? null, latestPages: site.latestPages !== false })}</script>
<script type="application/json" id="builds">${json(builds)}</script>
<script type="application/json" id="pagesData">${json(pages.map((p) => ({ slug: p.slug, title: p.title, summary: p.summary ?? '', file: p.file, html: p.html, headings: p.headings.filter((h) => h.level === 2) })))}</script>
<script>
(() => {
  const builds = JSON.parse(document.getElementById('builds').textContent)
  const byId = new Map(builds.map((b) => [b.id, b]))
  const $ = (id) => document.getElementById(id)
  const stage = $('stage'), imgA = $('imgA'), imgB = $('imgB'), clipB = $('clipB'), divider = $('divider')
  const state = { a: null, b: null, compare: false, zoom: 1, panX: 0, panY: 0, split: 0.5, filter: '', tab: 'details', page: null, refit: false, pendingView: null }
  const pages = JSON.parse(document.getElementById('pagesData').textContent)
  const pageBySlug = new Map(pages.map((p) => [p.slug, p]))
  const site = JSON.parse(document.getElementById('site').textContent)

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
  const mb = (n) => (n / 1e6).toFixed(2) + ' MB' + (n > 9e6 ? ' <span class="big" title="Over 9 MB: slow to open in a browser">⚠️</span>' : '')
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
      // A dated series reads in time order, oldest first.
      if (items[0].time) items.sort((x, y) => ((x.time ? x.time.year : 1e9) - (y.time ? y.time.year : 1e9)) || y.createdAt.localeCompare(x.createdAt))
      html += '<h2>' + esc((items[0].config && items[0].config.title) || items[0].title || region) + '<small>' + esc(region) + '</small></h2>'
      for (const b of items) {
        const cls = 'build' + (state.a === b.id ? ' a' : '') + (state.compare && state.b === b.id ? ' b' : '')
        const pic = b.files.thumb
          ? '<img class="thumb" loading="lazy" src="' + esc(b.files.thumb) + '" alt="">'
          : '<div class="swatch" style="background:' + esc(b.sky) + '">' + esc(b.palette) + '</div>'
        const ab = state.a === b.id ? '<span class="tag ab">A</span>' : state.compare && state.b === b.id ? '<span class="tag ab">B</span>' : ''
        html += '<button class="' + cls + '" data-id="' + esc(b.id) + '">' + pic +
          '<div><div class="top">' + ab + (b.time ? '<span class="tag yr">' + esc(b.time.year) + '</span>' : '') + '<span class="tag">' + esc(b.palette) + '</span>' +
          (b.config && b.config.terrain && b.config.terrain.enabled !== false ? '<span class="tag">terrain</span>' : '') +
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
    const leaving = state.page !== null
    if (leaving) closePage()
    if (e.altKey || e.metaKey || e.shiftKey) { state.b = el.dataset.id; state.compare = true }
    else select(el.dataset.id, false)
    update(leaving)
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
    scheduleHash()
  }
  // The zoom at which the whole image fits the stage; the URL's zoom is relative to it.
  const fitZoom = (vb) => Math.min(stage.clientWidth / vb[2], stage.clientHeight / vb[3]) * 0.94
  // The current view, resolution-independent: the visible centre in viewBox units, zoom / fit.
  const viewOf = () => {
    const a = byId.get(state.a)
    const w = stage.clientWidth, h = stage.clientHeight
    if (!a || w === 0 || h === 0) return null
    return { cx: (w / 2 - state.panX) / state.zoom, cy: (h / 2 - state.panY) / state.zoom, z: state.zoom / fitZoom(a.viewBox) }
  }
  const applyView = (v) => {
    const a = byId.get(state.a)
    const w = stage.clientWidth, h = stage.clientHeight
    if (!a || w === 0 || h === 0) return
    state.zoom = Math.min(40, Math.max(0.02, fitZoom(a.viewBox) * v.z))
    state.panX = w / 2 - v.cx * state.zoom
    state.panY = h / 2 - v.cy * state.zoom
    layout()
  }
  const fit = () => {
    const a = byId.get(state.a)
    if (!a) return
    const vb = a.viewBox
    const w = stage.clientWidth, h = stage.clientHeight
    // Hidden behind a page: fit when the viewer is next shown.
    if (w === 0 || h === 0) { state.refit = true; return }
    state.zoom = fitZoom(vb)
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
  // When the stage changes size (the info panel opens, closes or changes tab), keep the point at
  // its centre where it was.
  let stageSize = null
  new ResizeObserver(() => {
    const w = stage.clientWidth, h = stage.clientHeight
    if (stageSize && stageSize[0] > 0 && stageSize[1] > 0 && w > 0 && h > 0) {
      state.panX += (w - stageSize[0]) / 2
      state.panY += (h - stageSize[1]) / 2
    }
    stageSize = [w, h]
    layout()
  }).observe(stage)

  const load = (img, b) => {
    if (img.dataset.id === b.id) return
    img.dataset.id = b.id
    $('loading').style.display = 'block'
    img.onload = img.onerror = () => { $('loading').style.display = 'none' }
    img.src = b.files.svg
  }

  // ---- info -------------------------------------------------------------------------------------
  const STAT_ORDER = ['buildings', 'footprintsAdded', 'heightFromTag', 'heightFromModel', 'heightFromLevels', 'heightGuessed', 'bridgePieces', 'ground', 'ribbons', 'elevationDatum', 'elevationTop', 'rapidCells', 'contourSegments', 'strips', 'features']
  const statKeys = (...bs) => {
    const keys = new Set()
    for (const b of bs) for (const k of Object.keys(b.stats || {})) keys.add(k)
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
      (site.latestPages ? '<a href="' + esc(a.name) + '.html" target="_blank" title="The latest build of this region, with hover labels">Latest page ↗</a>' : '') +
      (() => { const L = site.shop && site.shop.links; if (!L) return ''; const k = Object.keys(L).filter((p) => a.region.startsWith(p)).sort((x, y) => y.length - x.length)[0]; return k ? '<a class="buy" href="' + esc(L[k]) + '" target="_blank" rel="noopener">Buy a print ↗</a>' : '' })()
    $('info').classList.toggle('made', state.tab === 'made')
    for (const t of $('tabs').children) t.classList.toggle('on', t.dataset.tab === state.tab)
    if (state.tab === 'made') {
      $('infoBody').className = 'body stories'
      $('infoBody').innerHTML = story(a, b ? 'A' : '') + (b ? story(b, 'B') : '')
      return
    }
    $('infoBody').className = 'body'
    const about = (x, tag) =>
      '<dl>' +
      (tag ? '<dt>' + tag + '</dt><dd><b>' + esc(label(x)) + '</b></dd>' : '<dt>note</dt><dd>' + (x.note ? '<b>' + esc(x.note) + '</b>' : '<span style="color:var(--faint)">none</span>') + '</dd>') +
      '<dt>built</dt><dd>' + when(x.createdAt) + '</dd>' +
      '<dt>commit</dt><dd class="mono">' + (x.git ? esc(x.git.commit) + (x.git.dirty ? ' <span class="dirty">+ uncommitted changes</span>' : '') + '<br><span style="color:var(--dim)">' + esc(x.git.subject) + '</span>' : '–') + '</dd>' +
      '<dt>region</dt><dd class="mono">' + esc(x.region) + '</dd>' +
      '<dt>palette</dt><dd>' + esc(x.palette) + '</dd>' +
      '<dt>bearing</dt><dd>' + (typeof x.bearing === 'number' ? x.bearing.toFixed(1) + '°' : '–') + '</dd>' +
      '<dt>size</dt><dd>' + mb(x.bytes) + ' · ' + Math.round(x.viewBox[2]) + '×' + Math.round(x.viewBox[3]) + ' · ' + x.ms + ' ms</dd>' +
      '</dl>'
    let stats
    if (b) {
      stats = '<table><tr><th>stat</th><th>A</th><th>B</th><th>Δ</th></tr>' + statKeys(a, b).map((k) => {
        const va = (a.stats || {})[k], vb = (b.stats || {})[k]
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
  // ---- how this view was made ------------------------------------------------------------------
  // A build's own story, written from its meta.json. Anything an older build did not record is
  // said to be unknown rather than guessed.
  const how = (id, text) => pageBySlug.has('how-its-made') ? '<a href="#/how-its-made/' + id + '">' + text + '</a>' : text
  const KNOWN = new Set(['features', 'ground', 'ribbons', 'buildings', 'heightFromTag', 'heightFromModel', 'heightFromLevels', 'heightGuessed', 'footprintsAdded', 'bridgePieces', 'elevationDatum', 'elevationTop', 'rapidCells', 'contourSegments', 'strips', 'coastWays', 'year', 'newSincePrevious', 'landmarks', 'curated', 'datedCurated', 'datedOsm', 'datedParcel', 'undatedToday', 'traced', 'tracedEndMap', 'tracedEndRebuilt', 'tracedEndHighway', 'tracedEndAssumed'])
  const POINTS = ['north', 'north-northeast', 'northeast', 'east-northeast', 'east', 'east-southeast', 'southeast', 'south-southeast', 'south', 'south-southwest', 'southwest', 'west-southwest', 'west', 'west-northwest', 'northwest', 'north-northwest']
  const isNum = (v) => typeof v === 'number' && Number.isFinite(v)
  const int = (v) => Math.round(v).toLocaleString()
  const dist = (m) => (m >= 1000 ? +(m / 1000).toFixed(2) + ' km' : Math.round(m) + ' m')
  const deg360 = (d) => Math.round(((d % 360) + 360) % 360) % 360
  const compass = (d) => POINTS[Math.round((((d % 360) + 360) % 360) / 22.5) % 16]
  const plural = (n, one, many) => int(n) + ' ' + (Math.round(n) === 1 ? one : many || one + 's')
  const ordinal = (n) => n + (n % 100 >= 11 && n % 100 <= 13 ? 'th' : n % 10 === 1 ? 'st' : n % 10 === 2 ? 'nd' : n % 10 === 3 ? 'rd' : 'th')
  const pct = (part, whole) => (whole > 0 ? Math.round((100 * part) / whole) + '%' : '–')
  const areaText = (m2) => (m2 >= 10000 ? (m2 / 10000).toFixed(1) + ' ha' : int(m2) + ' m²')
  const latlon = (c) => Math.abs(c[1]).toFixed(4) + '°' + (c[1] >= 0 ? 'N' : 'S') + ', ' + Math.abs(c[0]).toFixed(4) + '°' + (c[0] >= 0 ? 'E' : 'W')
  const unknown = (text) => '<span class="unknown">' + text + '</span>'
  const story = (x, tag) => {
    const c = x.config || {}, s = x.stats || {}, t = c.terrain || null
    const has = (k) => isNum(s[k])
    const relief = !!t && t.enabled !== false && has('elevationTop') && has('elevationDatum')
    const out = []
    // Each heading opens a section; the sections flow into as many columns as fit.
    let inSection = false
    const head = (title, link) => {
      out.push((inSection ? '</section>' : '') + '<section><h4>' + title + (link ? ' ' + link : '') + '</h4>')
      inSection = true
    }
    out.push(tag ? '<h3>' + tag + ' · ' + esc(label(x)) + '</h3>' : '')

    // The place and the frame.
    let lede = '<b>' + esc(x.title || c.title || x.region) + '.</b> '
    if (isNum(c.width) && isNum(c.depth)) {
      lede += 'A frame ' + dist(c.width) + ' across and ' + dist(c.depth) + ' deep (' + ((c.width * c.depth) / 1e6).toFixed(2) + ' km²)'
      const ctr = Array.isArray(c.center) && isNum(c.center[0]) && isNum(c.center[1]) ? c.center : null
      if (ctr) lede += ', centred on <a href="https://www.openstreetmap.org/?mlat=' + ctr[1] + '&amp;mlon=' + ctr[0] + '#map=16/' + ctr[1] + '/' + ctr[0] + '" target="_blank" rel="noopener" title="Open this point on openstreetmap.org">' + latlon(ctr) + '</a>'
      lede += '.'
    }
    out.push('<p class="lede">' + lede + '</p>')

    // Time: what is measured and what is curated in a dated scene.
    if (x.time) {
      const tm = x.time
      head('The year ' + esc(tm.year) + (tm.title ? ': ' + esc(tm.title) : ''), how('time', 'how time is drawn →'))
      if (tm.note) out.push('<p>' + esc(tm.note) + '</p>')
      if (has('buildings')) {
        const dated = (s.datedCurated || 0) + (s.datedOsm || 0) + (s.datedParcel || 0)
        let p = '<b>Measured:</b> ' + plural(s.buildings, 'building') + ' standing today that had been built by ' + esc(tm.year) + '. '
        if (dated > 0) p += 'Their years: ' + int(s.datedParcel || 0) + ' from the city assessor’s year built, ' + int(s.datedOsm || 0) + ' from OpenStreetMap’s <code>start_date</code>' + (s.datedCurated ? ', ' + int(s.datedCurated) + ' curated' : '') + '. '
        if (s.undatedToday > 0) p += int(s.undatedToday) + ' more have no recorded year and appear only in today’s scene. '
        if (isNum(s.newSincePrevious) && isNum(tm.previous)) p += '<b>' + int(s.newSincePrevious) + '</b> are new since ' + esc(tm.previous) + ', roofed in gold. '
        p += 'Anything demolished since is missing unless traced or curated below.'
        out.push('<p>' + p + '</p>')
      }
      if (s.traced > 0) {
        out.push('<p><b>Traced:</b> ' + plural(s.traced, 'building') + ' that no longer stand, traced from Sanborn fire-insurance maps and drawn in the maps’ own colours (pink brick, yellow frame, blue stone, grey iron). Each appears from the first map that shows it, though it may be older. When it went: ' +
          int(s.tracedEndMap || 0) + ' by a later map that no longer shows it, ' + int(s.tracedEndRebuilt || 0) + ' by the year the building now on the site went up, ' +
          int(s.tracedEndHighway || 0) + ' by an expressway through the site, and ' + int(s.tracedEndAssumed || 0) + ' <b>assumed</b> gone by 1960. Heights are <b>guessed</b> from the material: brick and stone three storeys, frame two.</p>')
      }
      const cur = Array.isArray(tm.curated) ? tm.curated : []
      if (cur.length) {
        out.push('<p><b>Curated</b> for this year, from published sources; positions are drawn from today’s street grid and published dimensions, not surveyed:</p><ul>' +
          cur.map((h) => '<li><b>' + esc(h.name) + '</b> (' + esc(h.from) + (h.to ? '–' + esc(h.to) : '') + '). ' + esc(h.note) +
            (h.sources && h.sources.length ? ' <span class="sources">' + h.sources.map((u, k) => '<a href="' + esc(u) + '" target="_blank" rel="noopener">[' + (k + 1) + ']</a>').join(' ') + '</span>' : '') + '</li>').join('') + '</ul>')
      } else out.push('<p>No curated features stand in this year; roads, rail and water follow the series’ era rules.</p>')
      out.push('<p>The ground is today’s: cuts and fills since (the interstate, the floodwall) are in the elevation.</p>')
    }

    // The camera.
    head('Camera', how('camera', 'how the camera works →'))
    const cam = []
    if (isNum(x.bearing)) {
      let p = 'Looking ' + compass(x.bearing) + ' (bearing ' + deg360(x.bearing) + '°)'
      if (c.snap !== false && isNum(c.bearing)) {
        const turn = x.bearing - c.bearing
        p += Math.abs(turn) < 0.05
          ? ', where snapping to the street grid left it'
          : ', turned ' + Math.abs(turn).toFixed(1) + '° ' + (turn < 0 ? 'counter-clockwise' : 'clockwise') + ' from the configured ' + deg360(c.bearing) + '° so the street grid runs along the diagonals'
      } else if (c.snap === false) p += ', a fixed bearing with no snapping'
      cam.push(p + '.')
    }
    const squash = isNum(c.squash) ? Math.min(1, Math.max(0.01, c.squash)) : 0.5
    const tilt = (Math.asin(squash) * 180) / Math.PI
    cam.push('Orthographic, tilted ' + Math.round(tilt) + '° down from the horizon: ground running into the picture is drawn at ' + +squash.toFixed(2) + '× its length and heights at ' + Math.cos(Math.asin(squash)).toFixed(2) + '×' +
      (isNum(c.exaggeration) && c.exaggeration !== 1 ? ', then ×' + c.exaggeration + ' for every height' : '') + '.')
    if (isNum(c.scale)) cam.push(c.scale + ' px per metre across the frame' + (Array.isArray(x.viewBox) ? '; the whole drawing is ' + int(x.viewBox[2]) + ' × ' + int(x.viewBox[3]) + ' px at 1:1' : '') + '.')
    out.push('<p>' + cam.join(' ') + '</p>')

    // What went in.
    head('Sources', how('inputs', 'where the data comes from →'))
    const src = []
    src.push('<li><b>OpenStreetMap</b>: ' + (has('features') ? int(s.features) + ' features read from the cached download' : unknown('feature count not recorded')) +
      (c.data && c.data !== x.region ? ', shared with region <code>' + esc(c.data) + '</code>' : '') +
      (has('coastWays') ? '; the sea and tidal water come from ' + plural(s.coastWays, 'coastline way') : '') + '.</li>')
    if (relief) {
      src.push('<li><b>USGS 3DEP elevation</b>, fetched at ' + (t.demResolution ?? 1) + ' m per pixel and resampled to a ' + (t.cell ?? 5) + ' m grid. The ground runs from ' +
        s.elevationDatum.toFixed(1) + ' m to ' + s.elevationTop.toFixed(1) + ' m above sea level (' + (s.elevationTop - s.elevationDatum).toFixed(1) + ' m of relief), drawn ' +
        (t.exaggeration ?? 2) + '× taller than life. Buildings and bridges keep their true heights.</li>')
    } else if (t && t.enabled !== false) {
      src.push('<li><b>Elevation</b>: ' + unknown('the region asks for terrain, but this build recorded no elevation range. Either the elevation was not fetched yet (the build then falls back to a flat plate), or the build predates that measure.') + '</li>')
    } else {
      src.push('<li><b>No elevation</b>: drawn on a flat plate' + (t && t.enabled === false ? ' (terrain is switched off for this region)' : '') + '.</li>')
    }
    out.push('<ul>' + src.join('') + '</ul>')

    // Ground.
    head('Ground', how('ground', 'what the ground is made of →'))
    const g = []
    if (has('ground')) g.push(plural(s.ground, 'mapped area') + ' of water, islands, parks, woods and other cover')
    if (has('ribbons')) g.push(plural(s.ribbons, 'ribbon') + ' of road, path, rail, canal and weir')
    let gp = g.length ? 'From the map, ' + g.join(', and ') + '.' : unknown('Ground counts were not recorded.')
    if (has('strips')) gp += ' Painted in ' + int(s.strips) + ' strips from back to front, ' + 2 * ((t && t.cell) ?? 5) + ' m deep each, so hills hide what is behind them (' + how('drawing', 'why') + ').'
    if (relief && has('contourSegments')) {
      const iv = t.contour ?? 2
      gp += iv > 0 ? ' Contours every ' + iv + ' m with every ' + ordinal(t.majorEvery ?? 5) + ' line heavier: ' + int(s.contourSegments) + ' segments.' : ' No contours.'
    }
    out.push('<p>' + gp + '</p>')

    // Rivers and rapids.
    head('Rivers and rapids', how('rapids', 'how rapids are read →'))
    if (relief) {
      const thr = t.rapids ?? 0.035
      if (has('rapidCells')) {
        const cell = t.cell ?? 5
        out.push('<p>' + (s.rapidCells > 0 ? int(s.rapidCells) + ' grid cells (about ' + areaText(s.rapidCells * cell * cell) + ') read as rapids' : 'No stretch of water read as rapids') +
          ': places where the river’s surface, recovered from the lidar, falls faster than ' + +(thr * 100).toFixed(2) + ' m per 100 m, measured over 40 m. Rock standing more than 1 m clear of that surface is drawn as boulders. Both are ' +
          how('rivers', 'inferred') + ' from the lidar, not observed.</p>')
      } else out.push('<p>' + unknown('Rapids were not counted for this build.') + '</p>')
    } else {
      out.push('<p>Without elevation, water is drawn from OpenStreetMap’s outlines as they are. No river surface, rocks or rapids are inferred.</p>')
    }

    // Buildings.
    head('Buildings', how('buildings', 'where heights come from →'))
    if (has('buildings')) {
      const added = s.footprintsAdded > 0 ? s.footprintsAdded : 0
      out.push('<p>' + plural(s.buildings, 'building') + ', extruded from footprints of at least ' + (c.minBuildingArea ?? 12) + ' m² that lie wholly inside the frame' +
        (added > 0 ? ': OpenStreetMap’s, plus ' + int(added) + ' traced by <a href="https://github.com/microsoft/GlobalMLBuildingFootprints">Microsoft’s building model</a> where OpenStreetMap has none.' : ', from OpenStreetMap.') + '</p>')
      if (has('heightFromTag') && has('heightFromLevels') && has('heightGuessed')) {
        const model = s.heightFromModel > 0 ? s.heightFromModel : 0
        const tot = s.heightFromTag + model + s.heightFromLevels + s.heightGuessed
        const seg = (cls, n) => (n > 0 ? '<span class="' + cls + '" style="width:' + ((100 * n) / tot).toFixed(2) + '%"></span>' : '')
        out.push('<div class="mixbar" title="Where the heights came from">' + seg('m-tag', s.heightFromTag) + seg('m-model', model) + seg('m-lev', s.heightFromLevels) + seg('m-guess', s.heightGuessed) + '</div>')
        out.push('<ul class="keyed">' +
          '<li><span class="key m-tag"></span>' + int(s.heightFromTag) + ' (' + pct(s.heightFromTag, tot) + ') from a <code>height</code> tag</li>' +
          (model > 0 ? '<li><span class="key m-model"></span>' + int(model) + ' (' + pct(model, tot) + ') from Microsoft’s model, <b>estimated</b> from imagery</li>' : '') +
          '<li><span class="key m-lev"></span>' + int(s.heightFromLevels) + ' (' + pct(s.heightFromLevels, tot) + ') from the number of floors, at 3.4 m a floor</li>' +
          '<li><span class="key m-guess"></span>' + int(s.heightGuessed) + ' (' + pct(s.heightGuessed, tot) + ') <b>guessed</b> from the building’s type and size</li></ul>')
      } else out.push('<p>' + unknown('Where the heights came from was not recorded for this build.') + '</p>')
    } else out.push('<p>' + unknown('Buildings were not counted for this build.') + '</p>')

    // Bridges.
    head('Bridges', how('bridges', 'how decks are placed →'))
    const rules = Array.isArray(c.bridges) ? c.bridges : []
    let bp = has('bridgePieces') ? (s.bridgePieces > 0 ? plural(s.bridgePieces, 'bridge span') + ' of up to 22 m, so long bridges sort among the buildings.' : 'No bridges in the frame.') : unknown('Bridge spans were not counted for this build.')
    if (!has('bridgePieces') || s.bridgePieces > 0) {
      bp += ' Deck heights are rules of thumb' + (rules.length ? ': ' + rules.map((r) => esc(r.match) + ' ' + esc(r.deck) + ' m').join(', ') + ', and any other bridge ' : ': every bridge ') + (c.bridgeDeck ?? 7) + ' m per OSM layer.'
    }
    out.push('<p>' + bp + '</p>')

    // Drawing.
    head('Drawing', how('paint-order', 'paint order →'))
    const dots = { all: 'a dot on every visible corner', roof: 'dots on roof corners only', none: 'no dots' }[c.dots || 'all'] || 'dots: ' + esc(c.dots)
    out.push('<p>The <code>' + esc(x.palette || c.palette || 'paper') + '</code> palette, ' + dots + ', on a ground slab ' + (c.slab ?? 14) + ' m thick.</p>')

    // This build.
    head('This build', how('archive-and-explorer', 'the archive →'))
    const bl = []
    bl.push('Built ' + (x.createdAt ? when(x.createdAt) : unknown('at an unrecorded time')) + (isNum(x.ms) ? ' in ' + (x.ms / 1000).toFixed(1) + ' s' : '') + (isNum(x.bytes) ? ', ' + mb(x.bytes) + ' of SVG' : '') + '.')
    if (x.git) bl.push('From commit <code>' + esc(x.git.commit) + '</code>, “' + esc(x.git.subject) + '”' + (x.git.dirty ? ', <span class="dirty">with uncommitted changes in src/ or regions/</span>' : '') + '.')
    else bl.push(unknown('No commit was recorded; it was not built inside a git checkout.'))
    if (x.note) bl.push('Note: <b>' + esc(x.note) + '</b>.')
    out.push('<p>' + bl.join(' ') + '</p>')
    const other = Object.keys(s).filter((k) => !KNOWN.has(k)).sort()
    if (other.length) out.push('<p>Other measures: ' + other.map((k) => esc(k) + ' ' + fmt(s[k])).join(', ') + '.</p>')

    out.push('</section><p class="credit">Map data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors (ODbL)' +
      (relief ? ' · Elevation: USGS 3DEP (public domain)' : '') + (pageBySlug.has('about') ? ' · <a href="#/about">credits and licences</a>' : '') + '</p>')
    return '<div class="story">' + out.join('') + '</div>'
  }
  $('toggleInfo').addEventListener('click', () => toggleInfo())
  const toggleInfo = () => {
    $('info').classList.toggle('closed')
    $('toggleInfo').textContent = $('info').classList.contains('closed') ? '▸' : '▾'
  }

  // ---- compare --------------------------------------------------------------------------------
  const defaultB = (aId) => {
    const a = byId.get(aId)
    // In a dated series, compare with the year before.
    if (a.time) {
      const ser = seriesOf(a)
      const i = ser.findIndex((x) => x.id === aId)
      if (i > 0) return ser[i - 1].id
      if (ser.length > 1) return ser[1].id
    }
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

  // ---- links ----------------------------------------------------------------------------------
  // Copy the full URL of what is on screen, view included.
  const copied = (text) => {
    const btn = $('link')
    btn.textContent = text
    btn.classList.add('on')
    clearTimeout(copied.t)
    copied.t = setTimeout(() => { btn.textContent = 'Link'; btn.classList.remove('on') }, 1400)
  }
  const copyFallback = (url) => {
    const ta = document.createElement('textarea')
    ta.value = url
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    let ok = false
    try { ok = document.execCommand('copy') } catch (err) { ok = false }
    ta.remove()
    if (ok) copied('Copied')
    else window.prompt('Copy this link:', url)
  }
  // The share page (s/<id>.html, s/page-<slug>.html) carries the link preview and passes the
  // fragment on to this page, so the link both previews well and opens this exact view.
  const shareUrl = () => {
    const file = state.page !== null ? 'page-' + state.page : state.a
    if (!file) return location.href
    const root = site.siteUrl || location.href.replace(/[#?].*$/, '').replace(/[^/]*$/, '')
    return root + 's/' + encodeURIComponent(file) + '.html' + location.hash
  }
  const copyLink = () => {
    writeHash()
    const url = shareUrl()
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(() => copied('Copied'), () => copyFallback(url))
    } else copyFallback(url)
  }
  $('link').addEventListener('click', copyLink)

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
  // The view part of the hash: '@cx,cy,z', or '' while the view is the fitted one.
  const viewPart = () => {
    const a = byId.get(state.a)
    // A view asked for but not yet shown (the viewer is hidden): keep it in the URL.
    const v = state.pendingView || (state.refit ? null : viewOf())
    if (!a || !v) return ''
    const vb = a.viewBox
    const z = Number(v.z.toPrecision(3))
    const cx = Math.round(v.cx * 10) / 10, cy = Math.round(v.cy * 10) / 10
    const tol = Math.max(vb[2], vb[3]) * 0.001
    if (Math.abs(z - 1) < 0.005 && Math.abs(cx - (vb[0] + vb[2] / 2)) < tol && Math.abs(cy - (vb[1] + vb[3] / 2)) < tol) return ''
    return '@' + cx + ',' + cy + ',' + z
  }
  const splitPart = () => (state.compare && state.b && Math.abs(state.split - 0.5) > 0.0005 ? '~' + Math.round(state.split * 1000) / 1000 : '')
  const viewerHash = () => '#' + state.a + (state.compare && state.b ? '..' + state.b : '') + viewPart() + splitPart() + (state.tab === 'made' ? '/made' : '')
  // Follow panning and zooming in the URL, without making history entries.
  let hashTimer = 0
  const writeHash = () => {
    clearTimeout(hashTimer)
    if (state.page !== null || !byId.has(state.a)) return
    const hash = viewerHash()
    if (location.hash !== hash) history.replaceState(null, '', hash)
    routed = location.hash
  }
  const scheduleHash = () => {
    clearTimeout(hashTimer)
    hashTimer = setTimeout(writeHash, 300)
  }
  // Redraw the viewer. With push, make a history entry (coming back from a page); else replace the hash.
  // A dated series: the newest build of each year, in time order.
  const seriesOf = (b) => {
    if (!b || !b.time) return []
    const last = new Map()
    for (const x of builds) {
      if (!x.time || x.time.series !== b.time.series || x.palette !== b.palette) continue
      const cur = last.get(x.time.year)
      if (!cur || x.createdAt > cur.createdAt) last.set(x.time.year, x)
    }
    return [...last.values()].sort((x, y) => x.time.year - y.time.year)
  }
  const renderTimeline = (a) => {
    const el = $('timeline')
    const ser = seriesOf(a)
    el.hidden = ser.length < 2
    if (el.hidden) return
    el.innerHTML = ser.map((x) => '<button data-id="' + esc(x.id) + '" class="' + (x.time.year === a.time.year ? 'on' : '') + '" title="' + esc(x.time.title || '') + '">' + esc(x.time.year) + '</button>').join('') +
      '<span class="hint">[ ] to step</span>'
  }
  $('timeline').addEventListener('click', (e) => {
    const t = e.target.closest('button')
    if (!t) return
    select(t.dataset.id, false)
    update(true)
  })
  const stepYear = (d) => {
    const a = byId.get(state.a)
    const ser = seriesOf(a)
    const i = ser.findIndex((x) => x.time.year === (a && a.time && a.time.year))
    const next = ser[i + d]
    if (next) { select(next.id, false); update(true) }
  }
  const update = (push) => {
    const a = byId.get(state.a)
    $('empty').style.display = a ? 'none' : 'grid'
    if (!a) return
    renderTimeline(a)
    load(imgA, a)
    if (state.compare && byId.get(state.b)) load(imgB, byId.get(state.b))
    // The info panel first: its height sets the stage's, which the fit depends on.
    renderList()
    renderPick()
    renderInfo()
    // A view from the URL is applied once the stage's size is known, on top of the fit.
    if (state.refit || state.pendingView) {
      state.refit = false
      fit()
      if (!state.refit && state.pendingView) { const v = state.pendingView; state.pendingView = null; applyView(v) }
    } else layout()
    clearTimeout(hashTimer)
    const hash = viewerHash()
    if (location.hash !== hash) history[push ? 'pushState' : 'replaceState'](null, '', hash)
    routed = location.hash
  }
  const setTab = (tab) => {
    state.tab = tab
    if ($('info').classList.contains('closed')) toggleInfo()
    update()
  }
  $('tabs').addEventListener('click', (e) => { const t = e.target.closest('button'); if (t) setTab(t.dataset.tab) })

  // ---- pages and routing ----------------------------------------------------------------------
  // #/<slug> and #/<slug>/<section> open a page; anything else is a build selection.
  let routed = null
  const renderPages = () => {
    $('pages').hidden = pages.length === 0
    $('pages').innerHTML = pages.map((p) => '<a href="#/' + esc(p.slug) + '"' + (state.page === p.slug ? ' class="on"' : '') +
      (p.summary ? ' title="' + esc(p.summary) + '"' : '') + '>' + esc(p.title) + '</a>').join('')
  }
  const markToc = () => {
    const page = $('page')
    let current = null
    for (const a of $('toc').querySelectorAll('a')) {
      const el = document.getElementById('p-' + state.page + '-' + a.dataset.id)
      if (el && el.offsetTop - page.scrollTop <= 80) current = a
    }
    for (const a of $('toc').querySelectorAll('a')) a.classList.toggle('on', a === current)
  }
  $('page').addEventListener('scroll', markToc, { passive: true })
  const openPage = (slug, section) => {
    const p = pageBySlug.get(slug) || pages[0]
    if (!p) return
    state.page = p.slug
    document.body.classList.add('reading')
    if ($('article').dataset.slug !== p.slug) {
      $('article').dataset.slug = p.slug
      $('article').innerHTML = p.html + '<p class="source">This page is <code>' + esc(p.file) + '</code>. Edit it there; the next build, or <code>isoscape explorer</code>, puts the change here.</p>'
      $('toc').innerHTML = p.headings.length < 2 ? '' : '<h3>On this page</h3>' + p.headings.map((h) =>
        '<a href="#/' + esc(p.slug) + '/' + esc(h.id) + '" data-id="' + esc(h.id) + '">' + esc(h.text) + '</a>').join('')
    }
    const a = byId.get(state.a)
    $('back').hidden = !a
    if (a) { $('back').href = viewerHash(); $('back').textContent = '← Back to the viewer' + (state.compare ? '' : ': ' + label(a)) }
    document.title = p.title + ' · isoscape explorer'
    renderPages()
    renderList()
    const target = section ? document.getElementById('p-' + p.slug + '-' + section) : null
    if (target) target.scrollIntoView({ block: 'start' })
    else $('page').scrollTop = 0
    $('page').focus({ preventScroll: true })
    markToc()
  }
  const closePage = () => {
    state.page = null
    document.body.classList.remove('reading')
    document.title = 'isoscape explorer'
    renderPages()
  }
  const parseHash = () => {
    let h = location.hash.slice(1)
    try { h = decodeURIComponent(h) } catch (err) { /* keep it raw */ }
    if (h.startsWith('/')) {
      const parts = h.slice(1).split('/')
      return { page: parts[0] || (pages[0] ? pages[0].slug : ''), section: parts.slice(1).join('/') }
    }
    const [whole, tab] = h.split('/')
    let sel = whole || '', view = null, split = null
    const t = sel.indexOf('~')
    if (t >= 0) {
      const s = Number(sel.slice(t + 1))
      if (sel.slice(t + 1) !== '' && Number.isFinite(s) && s >= 0 && s <= 1) split = s
      sel = sel.slice(0, t)
    }
    const at = sel.indexOf('@')
    if (at >= 0) {
      const n = sel.slice(at + 1).split(',').map((x) => (x.trim() === '' ? NaN : Number(x)))
      if (n.length === 3 && n.every(Number.isFinite) && n[2] > 0) view = { cx: n[0], cy: n[1], z: n[2] }
      sel = sel.slice(0, at)
    }
    const [a, b] = sel.split('..')
    return { a, b, tab, view, split }
  }
  const route = () => {
    routed = location.hash
    const r = parseHash()
    if (r.page !== undefined && pageBySlug.size > 0) { openPage(r.page, r.section); return }
    if (state.page !== null) closePage()
    if (builds.length === 0) return
    if (r.a && byId.has(r.a)) {
      if (r.a !== state.a) select(r.a, false)
      if (r.b && byId.has(r.b)) { state.b = r.b; state.compare = true } else state.compare = false
      state.tab = r.tab === 'made' ? 'made' : 'details'
      if (state.compare) state.split = r.split !== null ? r.split : 0.5
      // A link with a view lands on it; one without opens fitted, unless it only names what
      // is already shown (the view is then simply not in it yet).
      if (r.view) state.pendingView = r.view
      else if (location.hash !== viewerHash()) state.refit = true
    }
    update()
  }
  // In-page links (pages, sections, "back to the viewer") make history entries, so Back works.
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href^="#"]')
    if (!link || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
    e.preventDefault()
    const href = link.getAttribute('href')
    if (href !== location.hash) history.pushState(null, '', href)
    route()
  })
  const onNavigate = () => { if (location.hash !== routed) route() }
  window.addEventListener('popstate', onNavigate)
  window.addEventListener('hashchange', onNavigate)
  document.addEventListener('keydown', (e) => {
    if (e.target === $('filter')) { if (e.key === 'Escape') e.target.blur(); return }
    if (e.metaKey || e.ctrlKey || e.altKey) return
    if (state.page !== null) {
      // Reading: the arrows scroll the page. Esc goes back to the viewer.
      if (e.key === 'Escape' && byId.has(state.a)) { history.pushState(null, '', viewerHash()); route() }
      else if (e.key === '/') { $('filter').focus(); e.preventDefault() }
      else if (e.key === 'l' || e.key === 'L') copyLink()
      return
    }
    const list = visible()
    const i = list.findIndex((b) => b.id === state.a)
    if (e.key === 'ArrowDown' || e.key === 'j') { if (i < list.length - 1) { select(list[i + 1].id); update() } e.preventDefault() }
    else if (e.key === 'ArrowUp' || e.key === 'k') { if (i > 0) { select(list[i - 1].id); update() } e.preventDefault() }
    else if (e.key === '[') stepYear(-1)
    else if (e.key === ']') stepYear(1)
    else if (e.key === 'f' || e.key === 'F') fit()
    else if (e.key === '1') actual()
    else if (e.key === 'c' || e.key === 'C') toggleCompare()
    else if (e.key === 'l' || e.key === 'L') copyLink()
    else if (e.key === 'i' || e.key === 'I') toggleInfo()
    else if (e.key === 'm' || e.key === 'M') setTab(state.tab === 'made' ? 'details' : 'made')
    else if (e.key === '/') { $('filter').focus(); e.preventDefault() }
  })

  renderPages()
  const start = parseHash()
  if (builds.length === 0) {
    $('empty').innerHTML = '<div><b>No builds yet.</b><br>Run <code>node bin/isoscape.js build &lt;region&gt;</code> and reload.' +
      (pages.length ? '<br><br>Meanwhile: <a href="#/' + esc(pages[0].slug) + '">' + esc(pages[0].title) + '</a>' : '') + '</div>'
    renderList()
  } else {
    select(start.a && byId.has(start.a) ? start.a : builds[0].id, true)
    if (start.b && byId.has(start.b)) { state.b = start.b; state.compare = true }
    if (start.tab === 'made') state.tab = 'made'
    if (start.split !== null && start.split !== undefined) state.split = start.split
    if (start.view && byId.has(start.a)) state.pendingView = start.view
    if (start.page === undefined) update()
  }
  if (start.page !== undefined) route()
})()
</script>
</body>
</html>
`
