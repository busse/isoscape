// @ts-nocheck: this function runs in the browser (see below), so it is written as plain JavaScript.
/**
 * The figure lightbox for content pages. A page opts in by using numbered figures
 * (`::: figure`, markdown.ts): clicking a figure's picture, or pressing Enter on it, opens the
 * lightbox over the page. It shows the picture fitted to the window, then its larger copy when
 * that has loaded (the figure's link, `<name>-large.<ext>` where one exists, see pages.ts), with
 * the figure's "Fig. N." caption; previous and next buttons and the arrow keys step through every
 * figure in the article, with a counter ("3 of 25"); "Full size" (Z, or a click on the picture)
 * shows it at its own pixel size, panned by dragging or scrolling; "All figures" (G) shows the
 * article's figures as a grid of thumbnails, any of which opens; Esc closes the grid, then the
 * lightbox. Focus stays inside while it is open and goes back to the figure on close. While
 * open it takes every key first (a capturing listener on the window), so the explorer's own
 * shortcuts (arrows, Esc, F, C, L, I, M, brackets) wait until it closes. A link in the caption
 * closes it and is followed.
 *
 * The explorer embeds this function's source (`lightbox.toString()`, as it does story.ts) and
 * the static pages (static-pages.ts) put it in a script on any page with figures, so it may use
 * nothing but its argument and the language itself: no imports, no closures over this module,
 * no template literals. It works from file:// as well as over https: it only sets image sources.
 * Without script the picture is a plain link to its larger file.
 *
 * A compare figure (`::: compare`, compare.ts) opens through its expand button. The lightbox
 * then shows a copy of its slider, with the larger copy of each picture and the divider where it
 * was, fitted to the window; dragging or clicking on it moves the divider, and while its divider
 * has focus the arrow keys, Home and End move the divider (compare.ts handles them) instead of
 * stepping figures. "Full size" is hidden for it. In the grid it is one figure, shown by its first
 * picture.
 */

export const lightbox = (doc) => {
  if (doc.getElementById('lb')) return
  const el = (tag, cls, attrs) => {
    const e = doc.createElement(tag)
    if (cls) e.className = cls
    for (const k in attrs || {}) e.setAttribute(k, attrs[k])
    return e
  }
  const btn = (cls, label, text, key) => {
    const b = el('button', 'lb-btn ' + cls, { type: 'button', 'aria-label': label, title: label + (key ? ' (' + key + ')' : '') })
    b.textContent = text
    return b
  }
  const box = el('div', 'lb', { id: 'lb', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Figures', hidden: '' })
  const bar = el('div', 'lb-bar')
  const count = el('span', 'lb-count', { 'aria-live': 'polite' })
  const gridBtn = btn('lb-gridbtn', 'All figures', '▦ All figures', 'G')
  const zoomBtn = btn('lb-zoom', 'Full size', 'Full size', 'Z')
  zoomBtn.setAttribute('aria-pressed', 'false')
  const closeBtn = btn('lb-close', 'Close', '✕', 'Esc')
  bar.append(count, gridBtn, zoomBtn, closeBtn)
  const stage = el('div', 'lb-stage')
  const img = el('img', 'lb-img', { alt: '' })
  stage.append(img)
  const prev = btn('lb-prev', 'Previous figure', '‹', '←')
  const next = btn('lb-next', 'Next figure', '›', '→')
  const cap = el('div', 'lb-cap')
  const grid = el('div', 'lb-grid', { hidden: '', role: 'list', 'aria-label': 'All figures in this article' })
  box.append(bar, stage, prev, next, cap, grid)
  doc.body.append(box)

  let items = []
  let at = 0
  let opener = null
  let full = false
  let gridOpen = false
  const isOpen = () => !box.hidden

  // The figures of the article the clicked one belongs to, in page order.
  const collect = (from) => {
    const root = (from && from.closest('.prose')) || doc
    return Array.from(root.querySelectorAll('figure.fig a.fig-open')).map((a) => {
      const fig = a.closest('figure')
      const cmp = a.closest('.cmp')
      const pic = a.querySelector('img') || (cmp && cmp.querySelector('img.cmp-a'))
      const caption = fig.querySelector('figcaption')
      return { a, fig, cmp, small: pic ? pic.currentSrc || pic.src : a.href, large: a.href, alt: pic ? pic.alt : '', caption }
    })
  }
  const setZoom = (on, x, y) => {
    full = on
    box.classList.toggle('full', on)
    zoomBtn.setAttribute('aria-pressed', on ? 'true' : 'false')
    zoomBtn.textContent = on ? 'Fit to window' : 'Full size'
    if (on && x !== undefined) {
      // Keep the clicked point of the picture under the pointer.
      const r = stage.getBoundingClientRect()
      stage.scrollLeft = x * img.naturalWidth - (r.width / 2)
      stage.scrollTop = y * img.naturalHeight - (r.height / 2)
    } else if (on) {
      stage.scrollLeft = (img.naturalWidth - stage.clientWidth) / 2
      stage.scrollTop = (img.naturalHeight - stage.clientHeight) / 2
    }
  }
  // A compare figure: a copy of its slider, with the larger pictures, in place of the picture.
  const clearCmp = () => {
    for (const c of stage.querySelectorAll('.cmp')) c.remove()
    stage.classList.remove('has-cmp')
    img.hidden = false
    zoomBtn.hidden = false
  }
  const showCmp = (it) => {
    const c = it.cmp.cloneNode(true)
    for (const o of c.querySelectorAll('.cmp-open')) o.remove()
    c.classList.remove('dragging')
    for (const p of c.querySelectorAll('img')) {
      p.removeAttribute('loading')
      const small = p.currentSrc || p.src
      const large = p.getAttribute('data-large')
      // The large copy replaces the small one once loaded, so the slider never shows a blank.
      if (large && large !== small) { const big = new Image(); big.onload = () => { p.src = large }; big.src = large }
    }
    img.hidden = true
    img.removeAttribute('src')
    zoomBtn.hidden = true
    stage.classList.add('has-cmp')
    stage.append(c)
  }
  const show = (i) => {
    at = (i + items.length) % items.length
    const it = items[at]
    setZoom(false)
    clearCmp()
    if (it.cmp) showCmp(it)
    else {
      img.alt = it.alt
      img.src = it.small
    }
    if (!it.cmp && it.large && it.large !== it.small) {
      const big = new Image()
      big.onload = () => { if (items[at] === it) img.src = it.large }
      big.src = it.large
    }
    count.textContent = (at + 1) + ' of ' + items.length
    cap.innerHTML = ''
    if (it.caption) for (const p of it.caption.querySelectorAll(':scope > p')) cap.append(p.cloneNode(true))
    const one = items.length < 2
    prev.hidden = one
    next.hidden = one
  }
  const focusables = () => Array.from(box.querySelectorAll('button, a[href], .cmp-div')).filter((e) => !e.hidden && !e.closest('[hidden]') && e.offsetParent !== null)
  const buildGrid = () => {
    grid.innerHTML = ''
    items.forEach((it, i) => {
      const b = el('button', 'lb-thumb', { type: 'button', role: 'listitem', 'aria-label': 'Open ' + (it.caption ? (it.caption.querySelector('.fig-n') || {}).textContent || '' : '') + ' ' + it.alt })
      const t = el('img', '', { alt: '', loading: 'lazy' })
      t.src = it.small
      const n = el('b')
      const fn = it.caption && it.caption.querySelector('.fig-n')
      n.textContent = fn ? fn.textContent : String(i + 1)
      // The caption's opening words, after the number (cut to two lines by the style).
      const first = it.caption && it.caption.querySelector('p')
      const words = el('span')
      words.textContent = first ? first.textContent.replace(n.textContent, '').trim() : ''
      b.append(t, n, words)
      b.addEventListener('click', () => { setGrid(false); show(i); closeBtn.focus() })
      grid.append(b)
    })
  }
  const setGrid = (on) => {
    gridOpen = on
    grid.hidden = !on
    box.classList.toggle('gridding', on)
    gridBtn.setAttribute('aria-pressed', on ? 'true' : 'false')
    if (on) {
      buildGrid()
      count.textContent = items.length + ' figures'
      const cur = grid.children[at]
      if (cur) { cur.focus(); cur.scrollIntoView({ block: 'nearest' }) }
    } else count.textContent = (at + 1) + ' of ' + items.length
  }
  const open = (a, grid0) => {
    items = collect(a)
    if (items.length === 0) return
    opener = a || doc.activeElement
    const i = items.findIndex((it) => it.a === a)
    box.hidden = false
    doc.documentElement.classList.add('lb-on')
    show(i < 0 ? 0 : i)
    setGrid(!!grid0)
    if (!grid0) closeBtn.focus()
  }
  const close = (refocus) => {
    if (!isOpen()) return
    setGrid(false)
    box.hidden = true
    clearCmp()
    img.removeAttribute('src')
    doc.documentElement.classList.remove('lb-on')
    if (refocus !== false && opener && opener.focus) opener.focus({ preventScroll: true })
    opener = null
  }

  doc.addEventListener('click', (e) => {
    const a = e.target.closest && e.target.closest('a.fig-open')
    if (!a || isOpen() || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
    e.preventDefault()
    e.stopPropagation()
    open(a, false)
  }, true)
  closeBtn.addEventListener('click', () => close())
  prev.addEventListener('click', () => show(at - 1))
  next.addEventListener('click', () => show(at + 1))
  gridBtn.addEventListener('click', () => setGrid(!gridOpen))
  zoomBtn.addEventListener('click', () => setZoom(!full))
  // A link in the caption leaves the lightbox and is followed (the page's own handlers route it).
  cap.addEventListener('click', (e) => { if (e.target.closest('a[href]')) close(false) })
  // A click on the backdrop closes; on the picture, toggles full size there.
  stage.addEventListener('click', (e) => {
    if (moved) return
    // On a compare slider a click moves its divider (compare.ts).
    if (e.target.closest('.cmp')) return
    if (e.target !== img) { close(); return }
    const r = img.getBoundingClientRect()
    if (!full) setZoom(true, (e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height)
    else setZoom(false)
  })
  // Drag to pan at full size.
  let drag = null
  let moved = false
  stage.addEventListener('pointerdown', (e) => {
    moved = false
    if (!full || e.button !== 0 || e.target.closest('.cmp')) return
    drag = { x: e.clientX, y: e.clientY, l: stage.scrollLeft, t: stage.scrollTop }
    stage.setPointerCapture(e.pointerId)
  })
  stage.addEventListener('pointermove', (e) => {
    if (!drag) return
    const dx = e.clientX - drag.x
    const dy = e.clientY - drag.y
    if (Math.abs(dx) + Math.abs(dy) > 4) moved = true
    stage.scrollLeft = drag.l - dx
    stage.scrollTop = drag.t - dy
    e.preventDefault()
  })
  const endDrag = () => { drag = null }
  stage.addEventListener('pointerup', endDrag)
  stage.addEventListener('pointercancel', endDrag)
  img.addEventListener('dragstart', (e) => e.preventDefault())

  // While open, every key is the lightbox's: the page's own shortcuts wait until it closes.
  doc.defaultView.addEventListener('keydown', (e) => {
    if (!isOpen()) return
    const k = e.key
    // A compare slider's divider with focus takes its own keys (compare.ts, listening after this).
    if (doc.activeElement && doc.activeElement.classList.contains('cmp-div') && box.contains(doc.activeElement) &&
      /^(Arrow(Left|Right|Up|Down)|Home|End|PageUp|PageDown)$/.test(k) && !e.metaKey && !e.ctrlKey && !e.altKey) return
    e.stopPropagation()
    if (e.metaKey || e.ctrlKey || e.altKey) return
    if (k === 'Tab') {
      const f = focusables()
      if (f.length === 0) return
      const i = f.indexOf(doc.activeElement)
      const to = e.shiftKey ? (i <= 0 ? f.length - 1 : i - 1) : (i < 0 || i === f.length - 1 ? 0 : i + 1)
      f[to].focus()
      e.preventDefault()
      return
    }
    if (k === 'Escape') { if (gridOpen) { setGrid(false); closeBtn.focus() } else close(); e.preventDefault(); return }
    if (gridOpen) {
      // In the grid the arrows move between thumbnails; Enter opens one.
      const thumbs = Array.from(grid.children)
      const i = thumbs.indexOf(doc.activeElement)
      const cols = Math.max(1, Math.round(grid.clientWidth / ((thumbs[0] && thumbs[0].offsetWidth) || 1)))
      const step = k === 'ArrowRight' ? 1 : k === 'ArrowLeft' ? -1 : k === 'ArrowDown' ? cols : k === 'ArrowUp' ? -cols : 0
      if (step !== 0) { const t = thumbs[Math.min(thumbs.length - 1, Math.max(0, (i < 0 ? at : i) + step))]; if (t) t.focus(); e.preventDefault(); return }
      if (k === 'g' || k === 'G') { setGrid(false); closeBtn.focus(); e.preventDefault() }
      return
    }
    if (k === 'ArrowRight' || k === 'PageDown') { show(at + 1); e.preventDefault() }
    else if (k === 'ArrowLeft' || k === 'PageUp') { show(at - 1); e.preventDefault() }
    else if (k === 'Home') { show(0); e.preventDefault() }
    else if (k === 'End') { show(items.length - 1); e.preventDefault() }
    else if (k === 'g' || k === 'G') { setGrid(true); e.preventDefault() }
    else if (k === 'z' || k === 'Z' || k === '1') { setZoom(!full); e.preventDefault() }
    else if (full && (k === 'ArrowUp' || k === 'ArrowDown')) { stage.scrollTop += k === 'ArrowUp' ? -120 : 120; e.preventDefault() }
  }, true)
  // Opening the grid without a picture first: any element with data-lightbox-grid.
  doc.addEventListener('click', (e) => {
    const g = e.target.closest && e.target.closest('[data-lightbox-grid]')
    if (!g) return
    e.preventDefault()
    const first = (g.closest('.prose') || doc).querySelector('figure.fig a.fig-open')
    if (first) { open(first, true); opener = g }
  })
}

/** The lightbox's look: colors from the shared theme (THEME_CSS), nothing else. */
export const LIGHTBOX_CSS = `html.lb-on, html.lb-on body { overflow: hidden; }
.lb { position: fixed; inset: 0; z-index: 1000; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; background: var(--stage); color: var(--ink); overscroll-behavior: contain; }
.lb[hidden] { display: none; }
.lb-bar { display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-bottom: 1px solid var(--line); background: var(--panel); font-size: 13px; }
.lb-count { margin-right: auto; color: var(--dim); font-variant-numeric: tabular-nums; }
.lb-btn { font: inherit; font-size: 13px; color: var(--ink); background: var(--bg); border: 1px solid var(--line); border-radius: 14px; padding: 4px 12px; cursor: pointer; }
.lb-btn:hover { border-color: var(--accent); color: var(--accent); }
.lb-btn:focus-visible, .lb-thumb:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.lb-btn[aria-pressed="true"] { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
.lb-stage { position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 16px 64px; min-height: 0; }
.lb-img { display: block; max-width: 100%; max-height: 100%; width: auto; height: auto; cursor: zoom-in; background: var(--panel); box-shadow: 0 1px 6px color-mix(in srgb, var(--ink) 18%, transparent); }
.lb.full .lb-stage { display: block; overflow: auto; padding: 0; cursor: grab; }
.lb.full .lb-stage:active { cursor: grabbing; }
.lb.full .lb-img { max-width: none; max-height: none; cursor: zoom-out; }
.lb-prev, .lb-next { position: absolute; top: 50%; transform: translateY(-50%); width: 44px; height: 64px; border-radius: 10px; font-size: 30px; line-height: 1; padding: 0; background: color-mix(in srgb, var(--panel) 88%, transparent); }
.lb-prev { left: 10px; } .lb-next { right: 10px; }
.lb-prev[hidden], .lb-next[hidden] { display: none; }
.lb-cap { max-height: 24vh; overflow-y: auto; padding: 10px 20px 14px; border-top: 1px solid var(--line); background: var(--panel); font-size: 13px; line-height: 1.5; }
.lb-cap p { max-width: 110ch; margin: 0 auto 6px; }
.lb-cap a { color: var(--accent); }
.lb-cap .fig-n { font-weight: 650; margin-right: 2px; }
.lb-cap code { font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--chip); padding: 0 3px; border-radius: 3px; }
.lb.gridding .lb-stage, .lb.gridding .lb-prev, .lb.gridding .lb-next, .lb.gridding .lb-cap, .lb.gridding .lb-zoom { display: none; }
.lb-grid { grid-row: 2 / 4; overflow-y: auto; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; padding: 18px 20px 28px; align-content: start; }
.lb-grid[hidden] { display: none; }
.lb-thumb { display: flex; flex-direction: column; gap: 6px; padding: 8px; border: 1px solid var(--line); border-radius: 9px; background: var(--panel); color: var(--ink); font: inherit; font-size: 12.5px; line-height: 1.35; text-align: left; cursor: pointer; }
.lb-thumb:hover { border-color: var(--accent); }
.lb-thumb span { font-weight: 400; color: var(--dim); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.lb-thumb img { width: 100%; aspect-ratio: 16 / 10; object-fit: contain; background: var(--bg); border-radius: 5px; }
@media (max-width: 600px) { .lb-stage { padding: 8px; } .lb-prev, .lb-next { grid-row: 2 / 3; top: auto; bottom: 8px; transform: none; } .lb-gridbtn { font-size: 0; } .lb-gridbtn::before { content: "▦"; font-size: 14px; } }
@media (max-width: 600px), (pointer: coarse) { .lb-bar { padding: 6px 10px; gap: 6px; } .lb-bar .lb-btn { min-width: 44px; min-height: 44px; border-radius: 22px; padding: 4px 12px; } .lb-close { font-size: 17px; } }
`

/** Numbered figures in the reading column: the picture, then a book-style caption in small type on a light ground. */
export const FIGURE_CSS = `.prose figure.fig { margin: 1.6em 0 1.8em; }
.prose figure.fig a.fig-open { display: block; cursor: zoom-in; border-radius: 4px; }
.prose figure.fig a.fig-open:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
.prose figure.fig img { margin: 0; width: 100%; border-radius: 4px 4px 0 0; }
.prose figure.fig figcaption { font-size: 12.5px; line-height: 1.5; color: var(--ink); background: var(--bg); border: 1px solid var(--line); border-top: none; border-radius: 0 0 4px 4px; padding: 9px 12px 10px; }
.prose figure.fig figcaption p { margin: 0 0 .5em; }
.prose figure.fig figcaption p:last-child { margin-bottom: 0; }
.prose figure.fig .fig-n { font-weight: 650; }
.prose figure.fig figcaption .table { margin: .7em 0 .2em; }
.prose figure.fig figcaption table { font-size: 12px; }
.prose figure.fig figcaption th { font-size: 10.5px; }
.prose figure.fig figcaption th, .prose figure.fig figcaption td { padding: 3px 8px 3px 0; }
.prose .deck { font-size: 18px; line-height: 1.5; color: var(--dim); margin: -6px 0 22px; }
.prose .figs-all { font-size: 13px; }
`
