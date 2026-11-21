import { test } from 'node:test'
import assert from 'node:assert/strict'
import { compareSliders, splitAt, splitOf } from '../src/compare.ts'
import { renderExplorer } from '../src/explorer.ts'
import { loadPages } from '../src/pages.ts'
import { planStatic, renderContentPage } from '../src/static-pages.ts'

// On a phone, a content page must never be wider than the screen. In November 2026 the Jackson
// Ward story laid out 927 px wide in the explorer on a 390 px phone (907 px as p/jackson-ward.html):
// the bare URLs in its Sources list could not wrap, so the reading view scrolled sideways, a thumb
// scroll drifted, and dragging a compare slider panned the page.

const pages = loadPages()
const story = pages.find((p) => p.slug === 'jackson-ward')
const explorer = renderExplorer([], pages)
const staticStory = story && renderContentPage(story, { config: {}, plan: planStatic([], pages.map((p) => p.slug)), pages, depth: 1 })

/** The declarations of the first rule whose selector is exactly `selector`, at the top level or in a media block. */
const rule = (css: string, selector: string): string => {
  const at = css.search(new RegExp(`(^|[\\n{]\\s*)${selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')} \\{`))
  assert.ok(at >= 0, `a rule for ${selector}`)
  const open = css.indexOf('{', at + 1)
  return css.slice(open + 1, css.indexOf('}', open))
}

test('in both views, long words and URLs wrap in the text column, and tables and code blocks scroll in their own box', () => {
  assert.ok(story && staticStory)
  for (const [view, doc] of [['explorer', explorer], ['static page', staticStory]] as const) {
    assert.match(rule(doc, '.prose'), /overflow-wrap: anywhere/, `${view}: text wraps anywhere rather than overflow`)
    assert.match(rule(doc, '.prose table'), /overflow-wrap: normal/, `${view}: table cells keep whole words`)
    assert.match(rule(doc, '.prose .table'), /overflow-x: auto/, `${view}: a table scrolls inside its wrapper`)
    assert.match(rule(doc, '.prose pre'), /overflow-x: auto/, `${view}: a code block scrolls inside its own box`)
  }
  // Every table on the story sits in its own scrolling wrapper.
  const tables = [...story.html.matchAll(/<table/g)].length
  assert.ok(tables >= 4)
  assert.equal([...story.html.matchAll(/<div class="table"><table/g)].length, tables)
  // The longest bare URL in Sources is what made the page 927 px wide: it is still there, as text that can wrap.
  assert.match(story.html, /https:\/\/prd-tnm\.s3\.amazonaws\.com\/\S+_geo\.tif/)
})

test("on a phone the explorer's reading view uses the narrow padding and cannot scroll sideways", () => {
  // The phone padding must come after the reading view's own padding, or the desktop rule wins.
  const base = explorer.indexOf('.doc { display: grid;')
  const phone = explorer.indexOf('@media (max-width: 760px) { .doc { padding: 18px 16px 60px; } }')
  assert.ok(base > 0 && phone > base, 'the phone padding follows the base rule')
  assert.match(explorer, /#page, #home \{ overflow-x: hidden; \}/, 'a guard, inside the phone media block')
  assert.match(staticStory ?? '', /\.wrap \{ padding-top: 18px; overflow-x: clip; \}/, 'the static page has the same guard on phones')
  // A wide figure never runs past the screen on a phone: no negative bleed in the explorer, at least the column on p/.
  assert.match(explorer, /--bleed: max\(0px, \(100cqw - 100%\) \/ 2 - 24px\)/)
  assert.match(staticStory ?? '', /--w: max\(100%, min\(1120px, 100vw - 56px\)\)/)
})

test('a compare slider takes sideways drags and a tap from a finger, and leaves vertical swipes to the page', () => {
  assert.match(rule(explorer, '.cmp'), /touch-action: pan-y/)
  assert.match(rule(explorer, '.cmp .cmp-div::before'), /inset: 0 -22px/, 'a 44 px touch target round the line')
  assert.match(rule(explorer, '.cmp .cmp-div::after'), /clamp\(/, 'the label tab is kept inside the picture')

  // A document, a figure and its divider, just enough for compareSliders.
  const on: Record<string, (e: unknown) => void> = {}
  const doc = { documentElement: { dataset: {} as Record<string, string> }, addEventListener: (t: string, f: (e: unknown) => void) => { on[t] = f } }
  const div = { style: {} as Record<string, string>, setAttribute: () => {}, focus: () => {} }
  const clip = { style: {} as Record<string, string> }
  const vars: Record<string, string> = {}
  const cmp = {
    dataset: { a: '1925', b: '1952' } as Record<string, string>, style: { setProperty: (k: string, v: string) => { vars[k] = v } },
    classList: { add: () => {}, remove: () => {} }, setPointerCapture: () => {},
    getBoundingClientRect: () => ({ left: 0, width: 200 }), querySelector: (s: string) => (s === '.cmp-div' ? div : clip),
  }
  compareSliders(doc, { at: splitAt, of: splitOf })
  const target = { closest: (s: string) => (s === '.cmp' ? cmp : null) }
  const ev = (type: string, x: number, y: number, pointerType = 'touch') => on[type]({ type, target, button: 0, pointerId: 1, pointerType, clientX: x, clientY: y, preventDefault: () => {} })
  const split = () => Number(cmp.dataset.split ?? 0.5)

  // A vertical swipe that starts on the slider scrolls the page (the browser cancels the pointer): the divider stays put.
  ev('pointerdown', 60, 100); ev('pointermove', 62, 80); ev('pointermove', 63, 20); ev('pointercancel', 63, 20)
  assert.equal(split(), 0.5, 'a vertical swipe does not move the divider')
  // A sideways drag moves it with the finger.
  ev('pointerdown', 100, 100); ev('pointermove', 110, 102); ev('pointermove', 170, 104); ev('pointerup', 170, 104)
  assert.equal(split(), 0.85)
  assert.equal(vars['--split'], '0.85', 'the label tab knows where the line is')
  assert.equal(div.style.left, '85%')
  // A tap moves it to where it lands; a mouse moves it from the press.
  ev('pointerdown', 40, 100); ev('pointerup', 40, 100)
  assert.equal(split(), 0.2)
  ev('pointerdown', 150, 100, 'mouse')
  assert.equal(split(), 0.75)
  ev('pointerup', 150, 100, 'mouse')
})
