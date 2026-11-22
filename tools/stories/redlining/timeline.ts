#!/usr/bin/env node
/**
 * The redlining story's timeline, 1871 to 1977: Richmond's own lines, the 1937 map, and what was built and cleared on graded land after it, as a flat diagram
 * in the FAQ's language (tools/diagrams/faq.ts): inked edges, a dot on every corner, colors from
 * src/palette.ts (paper, and night by prefers-color-scheme), text kept as text. Each date carries
 * its source and a mark for how sure it is: a solid disc where a source opened for the story
 * says so and no opened source disagrees, a ring where opened sources disagree, a dashed ring
 * where no opened source confirms it (none at present).
 *
 *   node tools/stories/redlining/timeline.ts      # pages/redlining-timeline.svg
 *
 * `npm test` checks the file in pages/ matches what this script writes.
 */

import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { PALETTES, type Palette } from '../../../src/palette.ts'
import { LINE, DOT, SIZE, W } from '../../diagrams/faq.ts'

type Sure = 'opened' | 'disputed' | 'unconfirmed'

export interface Moment {
  readonly date: string
  readonly what: string
  readonly source: string
  readonly sure: Sure
}

/** The dates, each from a source opened for the story (see the story page's sources). */
export const MOMENTS: readonly Moment[] = [
  { date: '1871', what: 'The city\'s wards are redrawn to pack Black voters into one, Jackson Ward.', source: 'Library of Virginia, Mapping Inequality timeline', sure: 'opened' },
  { date: '1888', what: 'Electric streetcars open suburbs that covenants keep white.', source: 'Library of Virginia', sure: 'opened' },
  { date: 'April 1911', what: 'City Council passes a residential segregation ordinance. In 1912 the General Assembly lets every Virginia city do the same.', source: 'Library of Virginia; Encyclopedia Virginia', sure: 'opened' },
  { date: '1917', what: 'In Buchanan v. Warley the Supreme Court strikes down segregation ordinances.', source: 'Library of Virginia', sure: 'opened' },
  { date: '1924 or 1929', what: 'Richmond passes a new ordinance tied to the state\'s Racial Integrity Act. A federal appeals court strikes it down in 1929.', source: 'Encyclopedia Virginia gives 1924; the Library of Virginia gives 1929', sure: 'disputed' },
  { date: '1933', what: 'Congress creates the Home Owners\' Loan Corporation (HOLC) to refinance the mortgages of home owners in distress.', source: 'Home Owners\' Loan Act, June 13, 1933 (Harriss, 1951); Federal Reserve Bank of Chicago, 2022', sure: 'opened' },
  { date: 'April 3, 1937', what: 'The HOLC\'s map of Richmond grades its residential areas A to D.', source: 'National Archives, RG 195, via FRASER', sure: 'opened' },
  { date: '1943', what: 'Gilpin Court is dedicated on cleared Apostle Town land in D1.', source: 'Library of Virginia, Craig, 2025; Encyclopedia Virginia', sure: 'opened' },
  { date: '1946', what: 'Harland Bartholomew\'s master plan calls the city\'s Black neighborhoods slums.', source: 'Encyclopedia Virginia', sure: 'opened' },
  { date: '1948', what: 'In Shelley v. Kraemer the Supreme Court makes racial covenants unenforceable.', source: 'Library of Virginia', sure: 'opened' },
  { date: '1955–1958', what: 'The Richmond–Petersburg Turnpike, now I-95 and I-64, is cut through D1. By 1957 about 1,900 Black families had been displaced.', source: 'Encyclopedia Virginia, citing the Richmond Times-Dispatch; the Jackson Ward story', sure: 'opened' },
  { date: '1962', what: 'Mosby Court opens in D5, home to many of the 1,300 people the 17th Street renewal displaced.', source: 'Encyclopedia Virginia', sure: 'opened' },
  { date: '1967–1970', what: 'A study calls Fulton (D7) a slum; the 1970 plan would displace about 785 households.', source: 'Encyclopedia Virginia', sure: 'opened' },
  { date: '1970', what: 'Richmond annexes 23 square miles of Chesterfield County. Public housing, 464 scattered-site units, is built in Blackwell (D11.5).', source: 'Library of Virginia; Richmond Magazine, 2018', sure: 'opened' },
  { date: '1973', what: 'HUD approves the Randolph project (D8), about 1,800 to be displaced, for the Downtown Expressway.', source: 'Encyclopedia Virginia', sure: 'opened' },
]

const roles = (p: Palette, dark: boolean) => ({ bg: p.sky, ink: p.ink, dim: dark ? p.railSteel : p.railTie, card: dark ? p.land : p.road, accent: p.mark.line })
const SANS = "ui-sans-serif, -apple-system, 'Segoe UI', system-ui, sans-serif"
const SERIF = "'Libre Baskerville', Baskerville, Georgia, serif"
const css = (r: ReturnType<typeof roles>) =>
  `.bg{fill:${r.bg}}.ink{fill:${r.ink}}.dim{fill:${r.dim}}.acc{fill:${r.accent}}` +
  `.edge{fill:none;stroke:${r.ink};stroke-width:${LINE}}.card{fill:${r.card};stroke:${r.ink};stroke-width:${LINE}}` +
  `.mark{fill:${r.bg};stroke:${r.ink};stroke-width:${LINE}}.mark.solid{fill:${r.ink}}.mark.dash{stroke-dasharray:2.6 1.7}`
const STYLE = `<style>
text{font-family:${SANS}}
.d{font:700 ${SIZE.name - 1}px ${SERIF}}
.b{font-size:${SIZE.body}px}
.s{font-size:${SIZE.note - 1}px;font-style:italic}
.h{font:600 ${SIZE.head}px ${SANS};letter-spacing:.08em}
${css(roles(PALETTES.paper, false))}
@media (prefers-color-scheme: dark){${css(roles(PALETTES.night, true))}}
</style>`

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const n = (v: number) => String(Math.round(v * 10) / 10)
const t = (x: number, y: number, s: string, cls: string) => `<text x="${n(x)}" y="${n(y)}" class="${cls}">${esc(s)}</text>`
const mark = (x: number, y: number, sure: Sure, r = 5.2) =>
  `<circle cx="${n(x)}" cy="${n(y)}" r="${n(r)}" class="mark${sure === 'opened' ? ' solid' : sure === 'unconfirmed' ? ' dash' : ''}"/>`

/** Greedy wrap by characters: about 6.6 px a character at the body size. */
const wrap = (s: string, width: number, px = 6.6): string[] => {
  const max = Math.floor(width / px)
  const out: string[] = []
  let line = ''
  for (const w of s.split(' ')) {
    if (line && (line + ' ' + w).length > max) { out.push(line); line = w } else line = line ? line + ' ' + w : w
  }
  if (line) out.push(line)
  return out
}

export const timeline = (): string => {
  const X = 34              // the time line
  const TX = 54             // text
  const TW = W - TX - 30
  const parts: string[] = []
  let y = 30
  parts.push(t(16, y, 'RICHMOND\'S LINES, 1871 TO 1977', 'h ink'))
  y += 26
  const top = y
  for (const m of MOMENTS) {
    const what = wrap(m.what, TW)
    const src = wrap(m.source, TW, 6.2)
    parts.push(mark(X, y - 5, m.sure))
    parts.push(t(TX, y, m.date, 'd ink'))
    y += 20
    for (const l of what) { parts.push(t(TX, y, l, 'b ink')); y += 18 }
    for (const l of src) { parts.push(t(TX, y, l, 's dim')); y += 16 }
    y += 16
  }
  const bottom = y - 30
  parts.unshift(`<path d="M${X} ${n(top - 5)}L${X} ${n(bottom)}" class="edge"/>`)
  // the key
  y += 4
  parts.push(`<path d="M16 ${n(y - 14)}L${W - 16} ${n(y - 14)}" class="edge" style="stroke-width:${LINE * 0.6}"/>`)
  for (const [sure, label] of [['opened', 'sources opened for this story agree'], ['disputed', 'opened sources disagree (named)'], ['unconfirmed', 'not confirmed by an opened source']] as const) {
    parts.push(mark(X, y, sure, 4.6) + t(TX, y + 4.5, label, 'b ink'))
    y += 22
  }
  const h = y + 6
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${n(h)}" width="${W}" height="${n(h)}" role="img" aria-labelledby="rl-tl-t rl-tl-d">
<title id="rl-tl-t">Richmond's lines, 1871 to 1977: ordinances, the 1937 map, and what was built and cleared on graded land</title>
<desc id="rl-tl-d">${esc(MOMENTS.map((m) => `${m.date}: ${m.what} (${m.source})`).join(' '))}</desc>
${STYLE}
<rect width="${W}" height="${n(h)}" class="bg"/>
${parts.join('\n')}
<circle cx="${X}" cy="${n(bottom)}" r="${n(DOT)}" class="ink"/>
</svg>
`
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const file = fileURLToPath(new URL('../../../pages/redlining-timeline.svg', import.meta.url))
  writeFileSync(file, timeline())
  console.error('wrote pages/redlining-timeline.svg')
}
