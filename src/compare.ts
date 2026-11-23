// @ts-nocheck: these functions run in the browser (see below), so they are written as plain JavaScript.
/**
 * The compare slider: two pictures of the same frame laid over each other, the second one cut
 * away left of a divider that can be dragged across. The explorer's viewer has had one since it
 * could compare two builds (key C, or ⌥-click a build or a year in a dated series): the second
 * build is drawn over the first in the same SVG coordinates and clipped with `clip-path: inset()`
 * left of the divider. `splitAt` and `splitOf` are that slider's moves, and `.cmp-div` its look,
 * shared by the viewer and by the slider a content page can place.
 *
 * In a content page (`::: compare`, markdown.ts) the slider is a numbered figure: the first
 * picture on the left, the second on the right, both the same size (they must be rendered from
 * the same frame; nothing here scales one to fit the other). Press or drag anywhere on the
 * pictures to move the divider: a mouse from the press, a finger by a sideways drag or a tap (a
 * vertical swipe still scrolls the page, and leaves the divider where it was). The
 * divider is a focusable slider: the arrow keys move it 2% (with Shift, or PageUp/PageDown, 10%),
 * Home and End take it to either edge, and it carries `aria-valuenow` and a `aria-valuetext` that
 * names the two sides. Its tab shows the two labels, one each side of the line. The figure's
 * expand button opens it in the lightbox (lightbox.ts), which shows the same slider large with
 * the larger copies of both pictures. Without script, the figure shows the two halves at 50%
 * and the expand button links to the first picture's larger copy.
 *
 * `compareSliders` listens on the whole document, so it serves every `.cmp` there, the copies
 * the lightbox makes included. Like the lightbox, the explorer and the static pages embed these
 * functions' source (`toString()`), so they use nothing but their arguments and the language
 * itself: no imports, no closures over this module, no template literals.
 */

/** Cut the top picture away left of `x` (a CSS length: px in the viewer, % in a figure) and put the divider there. */
export const splitAt = (clip, divider, x) => {
  clip.style.clipPath = 'inset(0 0 0 ' + x + ')'
  divider.style.left = x
}

/** Where a pointer at `clientX` puts the divider, as a fraction (0 to 1) of the box `r`. */
export const splitOf = (clientX, r) => Math.min(1, Math.max(0, (clientX - r.left) / r.width))

/** Wire every compare figure in `doc` (and any added later). `split` is `{ at: splitAt, of: splitOf }`. */
export const compareSliders = (doc, split) => {
  if (doc.documentElement.dataset.cmp) return
  doc.documentElement.dataset.cmp = '1'
  const set = (cmp, f) => {
    f = Math.min(1, Math.max(0, f))
    cmp.dataset.split = String(f)
    cmp.style.setProperty('--split', String(f))
    const div = cmp.querySelector('.cmp-div')
    split.at(cmp.querySelector('.cmp-clip'), div, Math.round(f * 1000) / 10 + '%')
    const pct = Math.round(f * 100)
    div.setAttribute('aria-valuenow', String(pct))
    div.setAttribute('aria-valuetext', pct + '%: ' + cmp.dataset.a + ' on the left, ' + cmp.dataset.b + ' on the right')
  }
  const at = (cmp) => Number(cmp.dataset.split || 0.5)
  // A mouse moves the divider from the press. A finger or pen waits to see which way it goes: a
  // sideways drag moves the divider (touch-action: pan-y keeps the browser from panning the page
  // sideways), a vertical one is left to the browser, which scrolls the page and cancels the
  // pointer, so the divider stays put. A tap moves it to where it lands.
  let drag = null
  doc.addEventListener('pointerdown', (e) => {
    const cmp = e.target.closest && e.target.closest('.cmp')
    if (!cmp || e.button !== 0 || e.target.closest('.cmp-open')) return
    const mouse = e.pointerType === 'mouse'
    drag = { cmp, id: e.pointerId, x0: e.clientX, y0: e.clientY, live: mouse }
    try { cmp.setPointerCapture(e.pointerId) } catch (err) { /* the pointer is already gone */ }
    if (!mouse) return
    cmp.classList.add('dragging')
    set(cmp, split.of(e.clientX, cmp.getBoundingClientRect()))
    const div = cmp.querySelector('.cmp-div')
    if (div) div.focus({ preventScroll: true })
    e.preventDefault()
  })
  doc.addEventListener('pointermove', (e) => {
    if (!drag || e.pointerId !== drag.id) return
    if (!drag.live) {
      const dx = Math.abs(e.clientX - drag.x0)
      const dy = Math.abs(e.clientY - drag.y0)
      if (dy > 8 && dy > dx) { drag = null; return }
      if (dx < 6 || dx < dy) return
      drag.live = true
      drag.cmp.classList.add('dragging')
    }
    set(drag.cmp, split.of(e.clientX, drag.cmp.getBoundingClientRect()))
    e.preventDefault()
  })
  const end = (e) => {
    if (!drag || e.pointerId !== drag.id) return
    if (e.type === 'pointerup' && !drag.live) set(drag.cmp, split.of(e.clientX, drag.cmp.getBoundingClientRect()))
    drag.cmp.classList.remove('dragging')
    drag = null
  }
  doc.addEventListener('pointerup', end)
  doc.addEventListener('pointercancel', end)
  // Keys on a focused divider. Capturing, so the explorer's own shortcuts never see them.
  doc.addEventListener('keydown', (e) => {
    const div = e.target.closest && e.target.closest('.cmp-div')
    // A divider outside a figure (a series page's, through-time.ts) handles its own keys.
    const cmp = div && div.closest('.cmp')
    if (!cmp || e.metaKey || e.ctrlKey || e.altKey) return
    const k = e.key
    const big = e.shiftKey ? 0.1 : 0.02
    const to = k === 'ArrowLeft' || k === 'ArrowDown' ? at(cmp) - big
      : k === 'ArrowRight' || k === 'ArrowUp' ? at(cmp) + big
        : k === 'PageDown' ? at(cmp) - 0.1
          : k === 'PageUp' ? at(cmp) + 0.1
            : k === 'Home' ? 0
              : k === 'End' ? 1 : null
    if (to === null) return
    set(cmp, to)
    e.preventDefault()
    e.stopPropagation()
  }, true)
}

/** The divider's look (the viewer's and the figures'), then the figure slider's. Colors from the shared theme only. */
export const COMPARE_CSS = `.cmp-div { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; background: var(--accent); cursor: ew-resize; }
.cmp-div::after { content: attr(data-badge); position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); white-space: nowrap; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; background: var(--accent); color: var(--panel); }
.cmp-div::before { content: ""; position: absolute; inset: 0 -8px; }
.cmp-div:focus { outline: none; }
.cmp-div:focus-visible::after { outline: 2px solid var(--ink); outline-offset: 2px; }
.cmp { position: relative; overflow: hidden; touch-action: pan-y; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; cursor: ew-resize; container-type: inline-size; }
.cmp .cmp-div::before { inset: 0 -22px; }
.cmp .cmp-div::after { transform: translateX(clamp(6px - var(--split, .5) * 100cqw, -50%, 100cqw - 6px - var(--split, .5) * 100cqw - 100%)); }
.cmp.dragging { cursor: grabbing; }
.cmp img.cmp-a { display: block; width: 100%; height: auto; max-width: none; margin: 0; pointer-events: none; }
.cmp .cmp-clip { position: absolute; inset: 0; overflow: hidden; clip-path: inset(0 0 0 50%); pointer-events: none; }
.cmp .cmp-clip img.cmp-b { position: absolute; inset: 0; display: block; width: 100%; height: 100%; max-width: none; margin: 0; }
.cmp .cmp-div { left: 50%; }
.cmp a.cmp-open { position: absolute; top: 8px; right: 8px; display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; border-radius: 15px; background: var(--panel); color: var(--ink); border: 1px solid var(--line); text-decoration: none; font-size: 16px; line-height: 1; cursor: zoom-in; }
.cmp a.cmp-open:hover { border-color: var(--accent); color: var(--accent); }
.cmp a.cmp-open:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.prose figure.fig .cmp img { border-radius: 4px 4px 0 0; }
.prose figure.fig a.fig-open.cmp-open { display: flex; border-radius: 15px; cursor: zoom-in; }
@media (pointer: coarse) { .cmp a.cmp-open, .prose figure.fig a.fig-open.cmp-open { width: 44px; height: 44px; border-radius: 22px; top: 6px; right: 6px; font-size: 19px; } }
.lb-stage.has-cmp { container-type: size; }
.lb-stage .cmp { width: min(100cqw, 100cqh * var(--ar)); flex: none; background: var(--panel); box-shadow: 0 1px 6px color-mix(in srgb, var(--ink) 18%, transparent); }
`
