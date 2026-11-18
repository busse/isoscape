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
 * pictures to move the divider (a mouse or a finger; a vertical swipe still scrolls the page). The
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
    const div = cmp.querySelector('.cmp-div')
    split.at(cmp.querySelector('.cmp-clip'), div, Math.round(f * 1000) / 10 + '%')
    const pct = Math.round(f * 100)
    div.setAttribute('aria-valuenow', String(pct))
    div.setAttribute('aria-valuetext', pct + '%: ' + cmp.dataset.a + ' on the left, ' + cmp.dataset.b + ' on the right')
  }
  const at = (cmp) => Number(cmp.dataset.split || 0.5)
  let drag = null
  doc.addEventListener('pointerdown', (e) => {
    const cmp = e.target.closest && e.target.closest('.cmp')
    if (!cmp || e.button !== 0 || e.target.closest('.cmp-open')) return
    drag = { cmp, id: e.pointerId }
    cmp.setPointerCapture(e.pointerId)
    cmp.classList.add('dragging')
    set(cmp, split.of(e.clientX, cmp.getBoundingClientRect()))
    const div = cmp.querySelector('.cmp-div')
    if (div && e.pointerType === 'mouse') div.focus({ preventScroll: true })
    e.preventDefault()
  })
  doc.addEventListener('pointermove', (e) => {
    if (!drag || e.pointerId !== drag.id) return
    set(drag.cmp, split.of(e.clientX, drag.cmp.getBoundingClientRect()))
  })
  const end = (e) => {
    if (!drag || e.pointerId !== drag.id) return
    drag.cmp.classList.remove('dragging')
    drag = null
  }
  doc.addEventListener('pointerup', end)
  doc.addEventListener('pointercancel', end)
  // Keys on a focused divider. Capturing, so the explorer's own shortcuts never see them.
  doc.addEventListener('keydown', (e) => {
    const div = e.target.closest && e.target.closest('.cmp-div')
    if (!div || e.metaKey || e.ctrlKey || e.altKey) return
    const cmp = div.closest('.cmp')
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
.cmp { position: relative; overflow: hidden; touch-action: pan-y; user-select: none; -webkit-user-select: none; cursor: ew-resize; }
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
.lb-stage.has-cmp { container-type: size; }
.lb-stage .cmp { width: min(100cqw, 100cqh * var(--ar)); flex: none; background: var(--panel); box-shadow: 0 1px 6px color-mix(in srgb, var(--ink) 18%, transparent); }
`
