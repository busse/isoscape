// @ts-nocheck: these functions run in the browser (see below), so they are written as plain JavaScript.
/**
 * A dated series' own page: one view of the same frame in every year, made for a visitor rather
 * than for someone inspecting builds. A content page opts in with `series: <region>` in its front
 * matter (pages.ts). The explorer then puts this view into the page, before its first `##`
 * heading, and widens the reading column; `p/<slug>.html` (static-pages.ts) puts a list of the
 * years there instead, each a link to that year's map page.
 *
 * The view shows the series' light preview pictures (each build's `preview.jpg`, about 3,700 px
 * wide), never the SVGs, so a year switches at once; the years on either side of the one shown
 * are fetched ahead. Each picture is placed by its build's viewBox in the frame they all share, so
 * two years line up even where their drawings differ a little in height.
 *
 * - One year: the year large with its caption (the epoch's title and note from the build), the
 *   previous and next years as buttons with their years on them, and every year as a button,
 *   grouped by century. The arrow keys and `[` `]` step through the years.
 * - Two years: "Earlier year" and "Later year" pickers offer only the series' years; the earlier
 *   is always on the left. Both sides and the divider's tab are labelled with their years. The
 *   divider is compare.ts's: its moves (`splitAt`, `splitOf`) and its look (`.cmp-div`). At the
 *   fitted size a press or a sideways drag anywhere moves it (a vertical swipe still scrolls the
 *   page); zoomed in, drag the divider itself, and drag elsewhere to pan. Focused, the arrow keys
 *   move it 2% (with Shift 10%), Home and End to either edge.
 * - Zoom: the + and − buttons, a double-click or double-tap, or a pinch (Ctrl or ⌘ with the wheel,
 *   or a trackpad pinch); Fit goes back. Zoomed in, a drag pans. At the fitted size the stage
 *   leaves vertical swipes to the page, so a phone still scrolls past it.
 *
 * The state rides in the page's route: `#/<slug>/<year>` or `#/<slug>/<earlier>..<later>`
 * (`ttParse`, `ttRoute`), so a link can point at "1865 vs 1870"; a heading id there still opens
 * that section. "Open in the full viewer" goes to the explorer's viewer at the lasting route
 * (`#<region>:<year>`, or `#<region>:<a>..<region>:<b>` to compare).
 *
 * Like compare.ts, the explorer embeds these functions' source (`toString()`), so they use
 * nothing but their arguments and the language itself: no imports, no closures over this module,
 * no template literals.
 */

/** A page route's section as a state of the view: `{ a, b }` (b null for one year), or null when it is not one. */
export const ttParse = (section, years) => {
  const m = /^(\d{3,4})(?:\.\.(\d{3,4}))?$/.exec(String(section || ''))
  if (!m) return null
  const a = Number(m[1])
  const b = m[2] === undefined ? null : Number(m[2])
  if (years.indexOf(a) < 0 || (b !== null && years.indexOf(b) < 0)) return null
  if (b === null || b === a) return { a: a, b: null }
  return { a: Math.min(a, b), b: Math.max(a, b) }
}

/** The page route for a state: `#/<slug>/<year>` or `#/<slug>/<earlier>..<later>`. */
export const ttRoute = (slug, s) => '#/' + slug + '/' + s.a + (s.b === null || s.b === undefined ? '' : '..' + s.b)

/** The year `d` steps from `year` (−1 the one before), or null past either end. */
export const ttStep = (years, year, d) => {
  const i = years.indexOf(year)
  const j = i + d
  return i < 0 || j < 0 || j >= years.length ? null : years[j]
}

/** The two years to compare when a visitor turns comparing on while `year` is shown: that year against the newest ("then and now"), or, on the newest, the year before it against it. */
export const ttPair = (years, year) => {
  const i = years.indexOf(year)
  const last = years[years.length - 1]
  if (year !== last) return { a: year, b: last }
  return i > 0 ? { a: years[i - 1], b: year } : { a: year, b: null }
}

/** Pick `year` for one side ('a' earlier, 'b' later), keeping the earlier year left of the later: the other side moves when it would cross. */
export const ttPick = (years, s, side, year) => {
  const i = years.indexOf(year)
  if (i < 0) return s
  // (No helpers here: the explorer embeds each function's source on its own.)
  const before = i > 0 ? years[i - 1] : null
  const after = i < years.length - 1 ? years[i + 1] : null
  if (side === 'a') {
    if (year < s.b) return { a: year, b: s.b }
    return after === null ? { a: before, b: year } : { a: year, b: after }
  }
  if (year > s.a) return { a: s.a, b: year }
  return before === null ? { a: year, b: after } : { a: before, b: year }
}

/** The frame every year's picture is placed in: the union of their viewBoxes, [x, y, w, h]. */
export const ttFrame = (boxes) => {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity
  for (const v of boxes) {
    x0 = Math.min(x0, v[0])
    y0 = Math.min(y0, v[1])
    x1 = Math.max(x1, v[0] + v[2])
    y1 = Math.max(y1, v[1] + v[3])
  }
  return [x0, y0, x1 - x0, y1 - y0]
}

/**
 * Where each year sits on the timeline, from 0 to 1, in proportion to the years between them
 * (1737 to 1788 is a long stretch, 1860 to 1870 a short one), inside a margin `pad` at either end.
 */
export const ttPos = (years, pad = 0.02) => {
  const p = pad
  const y0 = years[0], y1 = years[years.length - 1]
  return years.map((y) => (y1 === y0 ? 0.5 : p + (1 - 2 * p) * (y - y0) / (y1 - y0)))
}

/** The year whose place on the timeline (`ttPos`) is nearest the fraction `f`. */
export const ttNearest = (years, pos, f) => {
  let best = 0
  for (let i = 1; i < years.length; i++) if (Math.abs(pos[i] - f) < Math.abs(pos[best] - f)) best = i
  return years[best]
}

/** The labelled marks under the timeline: its first and last years, and each half century at least `gap` years (default 30) from both. */
export const ttTicks = (years, gap = 30) => {
  const g = gap
  const y0 = years[0], y1 = years[years.length - 1]
  const out = [y0]
  for (let y = Math.ceil(y0 / 50) * 50; y < y1; y += 50) if (y - y0 >= g && y1 - y >= g) out.push(y)
  if (y1 !== y0) out.push(y1)
  return out
}

/**
 * Build the view in `root` and run it. `cfg`: `items` (one per year, in year order: `year`,
 * `title`, `note`, `src`, `alt`, `viewBox`), `start` (`{ a, b }`), `onChange(state)` after every
 * change the visitor makes, `onLink(button)` for "Copy link", and `viewerHref(state)`. `h` holds
 * this module's helpers, `split` compare.ts's moves. Returns `{ set(state), state() }`.
 */
export const seriesView = (root, cfg, h, split) => {
  const esc = (s) => String(s === undefined || s === null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
  const items = cfg.items
  const years = items.map((x) => x.year)
  const byYear = new Map(items.map((x) => [x.year, x]))
  const F = h.frame(items.map((x) => x.viewBox))
  const pos = h.pos(years)
  const y0 = years[0], y1 = years[years.length - 1]
  const at01 = (y) => (y1 === y0 ? 0.5 : 0.02 + 0.96 * (y - y0) / (y1 - y0))
  const pct = (f) => Math.round(f * 10000) / 100 + '%'
  const option = (y) => '<option value="' + y + '">' + y + (byYear.get(y).title ? ': ' + esc(byYear.get(y).title) : '') + '</option>'
  root.innerHTML =
    '<div class="tt-cap" aria-live="polite"></div>' +
    '<div class="tt-nav">' +
      '<button type="button" class="tt-step" data-d="-1"></button>' +
      '<div class="tt-line" role="slider" tabindex="0" aria-label="Year" aria-valuemin="' + y0 + '" aria-valuemax="' + y1 + '">' +
        '<div class="tt-track"></div>' +
        years.map((y, i) => '<i class="tt-dot" data-y="' + y + '" style="left: ' + pct(pos[i]) + '" title="' + y + (byYear.get(y).title ? ': ' + esc(byYear.get(y).title) : '') + '"></i>').join('') +
        h.ticks(years).map((y) => '<span class="tt-tick' + (y === y1 ? ' last' : '') + '" style="left: ' + pct(at01(y)) + '">' + y + '</span>').join('') +
        '<b class="tt-knob"><span></span></b>' +
      '</div>' +
      '<button type="button" class="tt-step" data-d="1"></button>' +
      '<button type="button" class="tt-mode"></button>' +
    '</div>' +
    '<div class="tt-pick" hidden>' +
      '<label>Earlier year <select data-side="a">' + years.map(option).join('') + '</select></label>' +
      '<label>Later year <select data-side="b">' + years.map(option).join('') + '</select></label>' +
      '<button type="button" class="tt-mode"></button>' +
    '</div>' +
    '<div class="tt-stage" style="aspect-ratio: ' + F[2] + ' / ' + F[3] + '">' +
      '<img class="tt-img tt-a" alt="" draggable="false">' +
      '<div class="tt-clip" hidden><img class="tt-img tt-b" alt="" draggable="false"></div>' +
      '<div class="cmp-div tt-div" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="100" hidden></div>' +
      '<span class="tt-tag tt-ta" hidden></span><span class="tt-tag tt-tb" hidden></span>' +
      '<div class="tt-load" hidden></div>' +
      '<div class="tt-zoom"><button type="button" data-z="in" aria-label="Zoom in" title="Zoom in">+</button><button type="button" data-z="out" aria-label="Zoom out" title="Zoom out">−</button><button type="button" data-z="fit" title="Show the whole view" hidden>Fit</button></div>' +
    '</div>' +
    '<div class="tt-tools">' +
      '<button type="button" class="tt-link" title="Copy a link to exactly this view">Copy link to this view</button>' +
      '<a class="tt-full"></a>' +
    '</div>'
  const q = (sel) => root.querySelector(sel)
  const stage = q('.tt-stage'), imgA = q('.tt-a'), imgB = q('.tt-b'), clip = q('.tt-clip'), div = q('.tt-div')
  const line = q('.tt-line'), knob = q('.tt-knob')
  const load = q('.tt-load')
  let s = { a: cfg.start.a, b: cfg.start.b === undefined ? null : cfg.start.b }
  // The view: zoom k (1 is the whole frame fitted), the center (cu, cv) in frame units, the divider at a fraction "at" of the width.
  let k = 1, cu = F[2] / 2, cv = F[3] / 2, at = 0.5
  const pending = { a: null, b: null }
  let loadTimer = 0

  const layout = () => {
    const w = stage.clientWidth, ht = stage.clientHeight
    if (!w || !ht) return
    const sc = Math.min(w / F[2], ht / F[3]) * k
    const hw = w / 2 / sc, hh = ht / 2 / sc
    cu = F[2] <= 2 * hw ? F[2] / 2 : Math.min(F[2] - hw, Math.max(hw, cu))
    cv = F[3] <= 2 * hh ? F[3] / 2 : Math.min(F[3] - hh, Math.max(hh, cv))
    const px = w / 2 - cu * sc, py = ht / 2 - cv * sc
    for (const img of [imgA, imgB]) {
      const it = byYear.get(Number(img.dataset.year))
      if (!it) continue
      const vb = it.viewBox
      img.style.left = px + (vb[0] - F[0]) * sc + 'px'
      img.style.top = py + (vb[1] - F[1]) * sc + 'px'
      img.style.width = vb[2] * sc + 'px'
      img.style.height = vb[3] * sc + 'px'
    }
    if (s.b !== null) {
      split.at(clip, div, Math.round(at * w) + 'px')
      // A side's year tag steps aside while the divider's own tag is over it.
      q('.tt-ta').style.visibility = at * w < 100 ? 'hidden' : ''
      q('.tt-tb').style.visibility = (1 - at) * w < 100 ? 'hidden' : ''
    }
    // Zoomed in, a finger pans the picture; at the fitted size a vertical swipe scrolls the page.
    stage.style.touchAction = k > 1.001 ? 'none' : 'pan-y'
    stage.classList.toggle('zoomed', k > 1.001)
    q('[data-z="fit"]').hidden = k <= 1.001
    q('[data-z="out"]').disabled = k <= 1.001
    q('[data-z="in"]').disabled = k >= maxK() - 0.001
  }
  // As close as the pictures stay sharp: about 1.25 of their own pixels to a screen pixel (at most 8, at least 2).
  const maxK = () => Math.max(2, Math.min(8, 1.25 * (imgA.naturalWidth || 3700) / Math.max(1, stage.clientWidth)))
  const zoomAt = (mx, my, f) => {
    const w = stage.clientWidth, ht = stage.clientHeight
    if (!w || !ht) return
    const sc = Math.min(w / F[2], ht / F[3]) * k
    // The frame point under the pointer stays under it.
    const u = cu + (mx - w / 2) / sc, v = cv + (my - ht / 2) / sc
    k = Math.min(maxK(), Math.max(1, k * f))
    const sc2 = Math.min(w / F[2], ht / F[3]) * k
    cu = u - (mx - w / 2) / sc2
    cv = v - (my - ht / 2) / sc2
    layout()
  }
  const show = (img, side, year) => {
    const it = byYear.get(year)
    pending[side] = year
    if (img.dataset.year === String(year)) return
    clearTimeout(loadTimer)
    loadTimer = setTimeout(() => { load.textContent = 'Loading ' + year + '…'; load.hidden = false }, 150)
    const pre = new Image()
    const done = (ok) => {
      if (pending[side] !== year) return
      clearTimeout(loadTimer)
      load.hidden = true
      if (!ok) { load.textContent = 'The picture for ' + year + ' did not load.'; load.hidden = false }
      img.src = it.src
      img.alt = it.alt || ''
      img.dataset.year = String(year)
      layout()
    }
    pre.onload = () => done(true)
    pre.onerror = () => done(false)
    pre.src = it.src
  }
  const preload = (year) => { if (year !== null && byYear.has(year)) { const p = new Image(); p.src = byYear.get(year).src } }
  const cap = (y, side) => {
    const it = byYear.get(y)
    return '<div class="tt-one' + (side ? ' ' + side : '') + '">' +
      '<span class="tt-y">' + (side ? '<small>' + (side === 'l' ? 'Left' : 'Right') + '</small>' : '') + y + '</span><div>' + (it.title ? '<b>' + esc(it.title) + '</b>' : '') + (it.note ? '<p>' + esc(it.note) + '</p>' : '') + '</div></div>'
  }
  const render = () => {
    const two = s.b !== null
    q('.tt-cap').innerHTML = two ? cap(s.a, 'l') + cap(s.b, 'r') : cap(s.a, '')
    q('.tt-cap').classList.toggle('two', two)
    show(imgA, 'a', s.a)
    clip.hidden = !two
    div.hidden = !two
    for (const t of root.querySelectorAll('.tt-tag')) t.hidden = !two
    if (two) {
      show(imgB, 'b', s.b)
      q('.tt-ta').textContent = s.a
      q('.tt-tb').textContent = s.b
      div.setAttribute('data-badge', s.a + ' │ ' + s.b)
      div.setAttribute('aria-label', 'Divider between ' + s.a + ' and ' + s.b)
      div.setAttribute('aria-valuenow', String(Math.round(at * 100)))
      div.setAttribute('aria-valuetext', Math.round(at * 100) + '%: ' + s.a + ' on the left, ' + s.b + ' on the right')
      q('[data-side="a"]').value = String(s.a)
      q('[data-side="b"]').value = String(s.b)
    } else {
      pending.b = null
      preload(h.step(years, s.a, -1))
      preload(h.step(years, s.a, 1))
    }
    q('.tt-nav').hidden = two
    q('.tt-pick').hidden = !two
    // The timeline: the year on show and its place.
    const i = years.indexOf(s.a)
    knob.style.left = pct(pos[i])
    knob.firstChild.textContent = s.a
    line.setAttribute('aria-valuenow', String(s.a))
    line.setAttribute('aria-valuetext', s.a + (byYear.get(s.a).title ? ': ' + byYear.get(s.a).title : ''))
    for (const d of root.querySelectorAll('.tt-dot')) d.classList.toggle('on', Number(d.dataset.y) === s.a)
    for (const b of root.querySelectorAll('.tt-step')) {
      const d = Number(b.dataset.d)
      const y = h.step(years, s.a, d)
      b.disabled = y === null
      b.dataset.to = y === null ? '' : String(y)
      b.innerHTML = d < 0 ? '<span aria-hidden="true">←</span> ' + (y === null ? y0 : y) : (y === null ? y1 : y) + ' <span aria-hidden="true">→</span>'
      b.setAttribute('aria-label', y === null ? (d < 0 ? 'No earlier year' : 'No later year') : 'Show ' + y)
    }
    for (const m of root.querySelectorAll('.tt-mode')) {
      m.textContent = two ? 'Show one year' : 'Compare two years'
      m.setAttribute('aria-pressed', two ? 'true' : 'false')
    }
    const full = q('.tt-full')
    full.href = cfg.viewerHref(s)
    full.textContent = two ? 'Open both in the full viewer' : 'Open ' + s.a + ' in the full viewer'
    layout()
  }
  const change = (next) => {
    const same = next.a === s.a && (next.b === undefined ? null : next.b) === s.b
    s = { a: next.a, b: next.b === undefined ? null : next.b }
    if (same) return
    render()
    cfg.onChange(s)
  }

  // ---- controls ----
  for (const b of root.querySelectorAll('.tt-step')) b.addEventListener('click', () => { if (b.dataset.to) change({ a: Number(b.dataset.to), b: null }) })
  for (const sel of root.querySelectorAll('.tt-pick select')) sel.addEventListener('change', () => change(h.pick(years, s, sel.dataset.side, Number(sel.value))))
  for (const m of root.querySelectorAll('.tt-mode')) m.addEventListener('click', () => change(s.b !== null ? { a: s.a, b: null } : h.pair(years, s.a)))
  q('.tt-link').addEventListener('click', (e) => cfg.onLink(e.currentTarget))
  q('.tt-zoom').addEventListener('click', (e) => {
    const b = e.target.closest('button')
    if (!b) return
    if (b.dataset.z === 'fit') { k = 1; layout() } else zoomAt(stage.clientWidth / 2, stage.clientHeight / 2, b.dataset.z === 'in' ? 2 : 0.5)
  })
  // The timeline: press or drag along it to scrub through the years (a vertical swipe still scrolls the page).
  let scrub = null
  const scrubTo = (x) => {
    const r = line.getBoundingClientRect()
    change({ a: h.nearest(years, pos, (x - r.left) / r.width), b: null })
  }
  line.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return
    scrub = { id: e.pointerId, x0: e.clientX, y0: e.clientY, live: e.pointerType === 'mouse' }
    try { line.setPointerCapture(e.pointerId) } catch (err) { /* gone */ }
    if (scrub.live) { scrubTo(e.clientX); line.classList.add('scrubbing'); e.preventDefault() }
  })
  line.addEventListener('pointermove', (e) => {
    if (!scrub || e.pointerId !== scrub.id) return
    if (!scrub.live) {
      const dx = Math.abs(e.clientX - scrub.x0), dy = Math.abs(e.clientY - scrub.y0)
      if (dy > 8 && dy > dx) { scrub = null; return }
      if (dx < 5) return
      scrub.live = true
      line.classList.add('scrubbing')
    }
    scrubTo(e.clientX)
  })
  const endScrub = (e) => {
    if (!scrub || e.pointerId !== scrub.id) return
    if (e.type === 'pointerup' && !scrub.live) scrubTo(e.clientX)
    scrub = null
    line.classList.remove('scrubbing')
  }
  line.addEventListener('pointerup', endScrub)
  line.addEventListener('pointercancel', endScrub)
  line.addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return
    const kk = e.key
    const y = kk === 'Home' ? y0 : kk === 'End' ? y1 : kk === 'ArrowLeft' || kk === 'ArrowDown' ? h.step(years, s.a, -1) : kk === 'ArrowRight' || kk === 'ArrowUp' ? h.step(years, s.a, 1) : undefined
    if (y === undefined) return
    e.preventDefault()
    e.stopPropagation()
    if (y !== null) change({ a: y, b: null })
  })

  // ---- the stage: the divider, panning, pinching ----
  let drag = null
  const touches = new Map()
  let pinch = null
  const spread = () => { const p = [...touches.values()]; return { d: Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y), x: (p[0].x + p[1].x) / 2, y: (p[0].y + p[1].y) / 2 } }
  const setAt = (f) => {
    at = Math.min(1, Math.max(0, f))
    layout()
    div.setAttribute('aria-valuenow', String(Math.round(at * 100)))
    div.setAttribute('aria-valuetext', Math.round(at * 100) + '%: ' + s.a + ' on the left, ' + s.b + ' on the right')
  }
  stage.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.tt-zoom') || e.button !== 0) return
    const two = s.b !== null
    const onDiv = two && e.target === div
    if (e.pointerType === 'touch') {
      touches.set(e.pointerId, { x: e.clientX, y: e.clientY })
      if (touches.size === 2) { drag = null; pinch = spread(); try { stage.setPointerCapture(e.pointerId) } catch (err) { /* gone */ } return }
    }
    // What a drag does: move the divider (on it, or anywhere at the fitted size), else pan (zoomed in).
    const mode = onDiv || (two && k <= 1.001) ? 'div' : k > 1.001 ? 'pan' : null
    if (mode === null) return
    // A finger at the fitted size waits to see which way it goes: sideways moves the divider, up or down scrolls the page.
    const wait = mode === 'div' && !onDiv && e.pointerType !== 'mouse'
    drag = { mode: mode, x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, live: !wait, id: e.pointerId }
    try { stage.setPointerCapture(e.pointerId) } catch (err) { /* gone */ }
    if (!wait && mode === 'div') setAt(split.of(e.clientX, stage.getBoundingClientRect()))
    if (mode === 'pan') stage.classList.add('dragging')
    if (e.pointerType === 'mouse') e.preventDefault()
  })
  stage.addEventListener('pointermove', (e) => {
    if (touches.has(e.pointerId)) touches.set(e.pointerId, { x: e.clientX, y: e.clientY })
    if (pinch && touches.size === 2) {
      const now = spread()
      const r = stage.getBoundingClientRect()
      const sc = Math.min(stage.clientWidth / F[2], stage.clientHeight / F[3]) * k
      cu -= (now.x - pinch.x) / sc
      cv -= (now.y - pinch.y) / sc
      zoomAt(now.x - r.left, now.y - r.top, pinch.d > 0 ? now.d / pinch.d : 1)
      pinch = now
      e.preventDefault()
      return
    }
    if (!drag || e.pointerId !== drag.id) return
    if (!drag.live) {
      const dx = Math.abs(e.clientX - drag.x0), dy = Math.abs(e.clientY - drag.y0)
      if (dy > 8 && dy > dx) { drag = null; return }
      if (dx < 6 || dx < dy) return
      drag.live = true
    }
    if (drag.mode === 'div') setAt(split.of(e.clientX, stage.getBoundingClientRect()))
    else {
      const sc = Math.min(stage.clientWidth / F[2], stage.clientHeight / F[3]) * k
      cu -= (e.clientX - drag.x) / sc
      cv -= (e.clientY - drag.y) / sc
      drag.x = e.clientX
      drag.y = e.clientY
      layout()
    }
    e.preventDefault()
  })
  const lift = (e) => {
    touches.delete(e.pointerId)
    if (touches.size < 2) pinch = null
    // A tap at the fitted size moves the divider to where it lands.
    if (drag && e.pointerId === drag.id && e.type === 'pointerup' && !drag.live && drag.mode === 'div') setAt(split.of(e.clientX, stage.getBoundingClientRect()))
    if (drag && e.pointerId === drag.id) drag = null
    stage.classList.remove('dragging')
  }
  stage.addEventListener('pointerup', lift)
  stage.addEventListener('pointercancel', lift)
  stage.addEventListener('dblclick', (e) => {
    if (e.target.closest('.tt-zoom') || e.target === div) return
    const r = stage.getBoundingClientRect()
    if (k >= maxK() - 0.001) { k = 1; layout() } else zoomAt(e.clientX - r.left, e.clientY - r.top, 2)
  })
  // The wheel scrolls the page; with Ctrl or ⌘ (and a trackpad's pinch, which comes as Ctrl and the wheel) it zooms.
  stage.addEventListener('wheel', (e) => {
    if (!e.ctrlKey && !e.metaKey) return
    e.preventDefault()
    const r = stage.getBoundingClientRect()
    zoomAt(e.clientX - r.left, e.clientY - r.top, Math.exp(-e.deltaY * 0.01))
  }, { passive: false })
  new ResizeObserver(() => layout()).observe(stage)

  // ---- keys ----
  div.addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return
    const big = e.shiftKey ? 0.1 : 0.02
    const kk = e.key
    const to = kk === 'ArrowLeft' || kk === 'ArrowDown' ? at - big : kk === 'ArrowRight' || kk === 'ArrowUp' ? at + big
      : kk === 'PageDown' ? at - 0.1 : kk === 'PageUp' ? at + 0.1 : kk === 'Home' ? 0 : kk === 'End' ? 1 : null
    if (to === null) return
    setAt(to)
    e.preventDefault()
    e.stopPropagation()
  })
  // Anywhere on the page, the arrow keys and [ ] step through the years (not while typing or choosing, or on the divider).
  root.ownerDocument.addEventListener('keydown', (e) => {
    if (!root.isConnected || root.offsetParent === null || s.b !== null) return
    if (e.metaKey || e.ctrlKey || e.altKey || e.defaultPrevented) return
    const t = e.target
    if (t && t.closest && t.closest('input, select, textarea, [contenteditable], .cmp-div, .tt-line, #lb')) return
    const d = e.key === 'ArrowLeft' || e.key === '[' ? -1 : e.key === 'ArrowRight' || e.key === ']' ? 1 : 0
    if (d === 0) return
    const y = h.step(years, s.a, d)
    e.preventDefault()
    if (y !== null) change({ a: y, b: null })
  })

  render()
  return {
    set: (next) => { s = { a: next.a, b: next.b === undefined ? null : next.b }; render() },
    state: () => ({ a: s.a, b: s.b }),
  }
}

/** The view's look. Colors from the shared theme only. */
export const TT_CSS = `#page.tt-wide .doc { grid-template-columns: minmax(0, 1180px); gap: 0; padding: 20px 32px 72px; }
#page.tt-wide #toc, #page.tt-wide .doc .back { display: none; }
#page.tt-wide .prose > p, #page.tt-wide .prose > ul, #page.tt-wide .prose > ol, #page.tt-wide .prose > h2, #page.tt-wide .prose > h3 { max-width: 74ch; }
#page.tt-wide .prose > h1 { font-size: 27px; margin-bottom: 8px; }
#page.tt-wide .prose > h1 + p { font-size: 15.5px; line-height: 1.6; max-width: 104ch; margin-bottom: 0; }
body.ttpage #mwarn { display: none !important; }
.tt { display: flex; flex-direction: column; margin: 16px 0 8px; }
.tt p { margin: 0; }
.tt-cap { display: flex; gap: 8px 28px; align-items: flex-start; min-height: 46px; }
.tt-one { display: flex; gap: 14px; align-items: baseline; flex: 1 1 0; min-width: 0; }
.tt-y { flex: none; white-space: nowrap; font-size: 36px; line-height: 1; font-weight: 700; letter-spacing: -.02em; font-variant-numeric: tabular-nums; }
.tt-y small { display: block; font-size: 10.5px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--faint); margin-bottom: 2px; }
.tt-one b { display: block; font-size: 16px; line-height: 1.3; }
.tt-one p { margin: 2px 0 0; font-size: 14px; line-height: 1.45; color: var(--dim); max-width: 72ch; }
.tt-cap.two .tt-y { font-size: 28px; }
.tt-cap.two .tt-one.r { flex-direction: row-reverse; text-align: right; }
.tt-nav, .tt-pick { display: flex; align-items: center; gap: 10px; margin: 10px 0 10px; }
.tt-nav[hidden], .tt-pick[hidden] { display: none; }
.tt-step { flex: none; min-width: 82px; padding: 6px 12px; border: 1px solid var(--accent); border-radius: 18px; background: var(--panel); color: var(--accent); font: 650 14px ui-sans-serif, system-ui, sans-serif; font-variant-numeric: tabular-nums; cursor: pointer; white-space: nowrap; }
.tt-step:hover:not(:disabled) { background: var(--accent-soft); }
.tt-step:disabled { visibility: hidden; }
.tt-mode { flex: none; margin-left: auto; padding: 6px 14px; border-radius: 18px; border: 1px solid var(--accent); background: var(--accent); color: var(--panel); font: 600 13.5px ui-sans-serif, system-ui, sans-serif; cursor: pointer; white-space: nowrap; }
.tt-mode[aria-pressed="true"] { background: var(--panel); color: var(--accent); }
.tt-mode:hover { filter: brightness(1.08); }
.tt-line { position: relative; flex: 1; min-width: 0; height: 46px; cursor: pointer; touch-action: pan-y; user-select: none; -webkit-user-select: none; outline: none; }
.tt-line:focus-visible { box-shadow: 0 0 0 2px var(--accent); border-radius: 6px; }
.tt-track { position: absolute; left: 0; right: 0; top: 22px; height: 2px; background: var(--line); border-radius: 1px; }
.tt-dot { position: absolute; top: 19px; width: 8px; height: 8px; margin-left: -4px; border-radius: 50%; background: var(--panel); border: 1.5px solid var(--dim); box-sizing: border-box; }
.tt-dot.on { border-color: var(--accent); background: var(--accent); }
.tt-tick { position: absolute; top: 30px; transform: translateX(-50%); white-space: nowrap; font-size: 10.5px; color: var(--faint); font-variant-numeric: tabular-nums; pointer-events: none; }
.tt-tick:first-of-type { transform: translateX(-4px); }
.tt-tick.last { transform: translateX(calc(-100% + 4px)); }
.tt-knob { position: absolute; top: 0; transform: translateX(-50%); pointer-events: none; transition: left .12s ease-out; }
.tt-line.scrubbing .tt-knob { transition: none; }
.tt-knob span { display: block; font: 700 12px ui-sans-serif, system-ui, sans-serif; font-variant-numeric: tabular-nums; padding: 1px 7px; border-radius: 9px; background: var(--accent); color: var(--panel); }
.tt-knob::after { content: ""; position: absolute; left: 50%; top: 17px; width: 2px; height: 7px; margin-left: -1px; background: var(--accent); }
.tt-pick label { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: var(--dim); }
.tt-pick select { font: 600 13.5px ui-sans-serif, system-ui, sans-serif; color: var(--ink); background: var(--panel); border: 1px solid var(--accent); border-radius: 8px; padding: 5px 8px; max-width: 100%; }
.tt-stage { position: relative; overflow: hidden; width: 100%; background: var(--stage); border: 1px solid var(--line); border-radius: 8px; touch-action: pan-y; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; }
.tt-stage.zoomed { cursor: grab; }
.tt-stage.dragging { cursor: grabbing; }
.prose .tt-img { position: absolute; display: block; max-width: none; height: auto; margin: 0; pointer-events: none; }
.tt-clip { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
.tt-clip[hidden], .tt-div[hidden], .tt-tag[hidden], .tt-load[hidden], .tt-zoom [hidden] { display: none; }
.tt-stage:has(.tt-clip:not([hidden])) { cursor: ew-resize; }
.tt-stage.zoomed:has(.tt-clip:not([hidden])) { cursor: grab; }
.tt .tt-div { z-index: 2; }
.tt .tt-div::before { inset: 0 -20px; }
.tt .tt-div:focus-visible { box-shadow: 0 0 0 2px var(--ink); }
.tt-tag { position: absolute; bottom: 10px; z-index: 1; font-size: 13px; font-weight: 700; padding: 2px 9px; border-radius: 10px; background: var(--accent); color: var(--panel); pointer-events: none; }
.tt-ta { left: 10px; } .tt-tb { right: 10px; }
.tt-load { position: absolute; left: 50%; top: 10px; transform: translateX(-50%); font-size: 12px; color: var(--dim); background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 3px 8px; }
.tt-zoom { position: absolute; right: 8px; top: 8px; display: flex; gap: 4px; z-index: 3; }
.tt-zoom button { min-width: 32px; height: 32px; padding: 0 9px; border: 1px solid var(--line); border-radius: 16px; background: var(--panel); color: var(--ink); font: 600 15px/1 ui-sans-serif, system-ui, sans-serif; cursor: pointer; }
.tt-zoom button[data-z="fit"] { font-size: 12.5px; }
.tt-zoom button:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.tt-zoom button:disabled { opacity: .45; cursor: default; }
.tt-tools { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; margin-top: 10px; font-size: 13px; }
.tt-link { font: 600 13px ui-sans-serif, system-ui, sans-serif; padding: 5px 13px; border-radius: 16px; border: 1px solid var(--line); background: var(--panel); color: var(--accent); cursor: pointer; }
.tt-link:hover, .tt-link.on { border-color: var(--accent); background: var(--accent-soft); }
.tt-tools a { color: var(--accent); }
.prose .tt-shop { font-size: 13.5px; color: var(--dim); margin-top: 2em; }
@media (max-width: 1180px) { #page.tt-wide .doc { padding: 18px 24px 60px; } }
@media (max-width: 760px) {
  #page.tt-wide .doc { padding: 14px 14px 56px; }
  #page.tt-wide .prose > h1 { font-size: 23px; }
  #page.tt-wide .prose > h1 + p { font-size: 15px; }
  .tt-nav, .tt-pick { order: 1; flex-wrap: wrap; gap: 8px; margin: 8px 0 10px; }
  .tt-stage { order: 2; margin: 0 -14px; width: calc(100% + 28px); max-width: none; border-radius: 0; border-left: none; border-right: none; }
  .tt-cap { order: 3; margin-top: 12px; }
  .tt-tools { order: 4; }
  .tt-line { order: -1; flex: 1 1 100%; }
  .tt-step { flex: 1 1 0; min-width: 0; }
  .tt-nav .tt-mode { flex: 1 1 100%; margin-left: 0; padding: 8px 14px; }
  .tt-pick label { flex: 1 1 100%; justify-content: space-between; }
  .tt-pick select { flex: 1; max-width: 72%; }
  .tt-pick .tt-mode { flex: 1 1 100%; margin-left: 0; padding: 8px 14px; }
  .tt-y { font-size: 30px; }
  .tt-one { gap: 10px; }
  .tt-one p { font-size: 13.5px; }
  .tt-cap.two { flex-direction: column; gap: 10px; }
  .tt-cap.two .tt-one.r { flex-direction: row; text-align: left; }
  .tt-cap.two .tt-y { font-size: 24px; min-width: 64px; }
  .tt-zoom { top: 6px; right: 6px; }
  .tt-zoom button { min-width: 36px; height: 36px; border-radius: 18px; }
}
`
