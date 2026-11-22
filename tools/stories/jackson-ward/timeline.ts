#!/usr/bin/env node
/**
 * The Jackson Ward story's timeline of how the Turnpike came to be built, 1946 to 1958, as a flat diagram
 * in the FAQ's language (tools/diagrams/faq.ts): inked edges, a dot on every corner, colors from
 * src/palette.ts (paper, and night by prefers-color-scheme), text kept as text. Each date carries
 * its source and a mark for how sure it is: a solid disc where a source opened for the story
 * says so and no opened source disagrees, a ring where opened sources disagree, a dashed ring
 * where the only source is a summary of a book that has not been seen.
 *
 *   node tools/stories/jackson-ward/timeline.ts      # pages/jackson-ward-timeline.svg
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
  { date: '1946', what: 'Harland Bartholomew and Associates\' master plan for the city, made for the City Planning Commission, proposes expressways through it.', source: 'Encyclopedia Virginia (the plan); Style Weekly, 2013. Wikipedia, citing Campbell, names R. Stuart Royer and Associates as the firm that proposed a turnpike', sure: 'disputed' },
  { date: 'June 13, 1950', what: 'Voters reject the expressway plan in a citywide referendum. Only 8 of 55 precincts vote for it.', source: 'Style Weekly, 2013; Rogers, 2011, quoting Silver', sure: 'opened' },
  { date: 'November 1951', what: 'A second referendum, forced by former mayor J. Fulmer Bright\'s petition, fails by almost 2 to 1. A headline of the day put the margin at 6,002 votes.', source: 'Style Weekly, 2013; Rogers, 2011 (the same writer), citing the Times-Dispatch. His notes on Silver give June 13, 1951', sure: 'disputed' },
  { date: 'August 24, 1953', what: 'City Council, 6 to 1, concurs in a consultant\'s report on toll roads for the Richmond–Petersburg area. Silver writes that this moved the decision to the General Assembly and prevented another referendum.', source: 'Rogers, 2011, from the Council\'s records and quoting Silver, p. 192 (the book not seen)', sure: 'unconfirmed' },
  { date: 'April 8, 1954', what: 'The General Assembly creates the Richmond–Petersburg Turnpike Authority, with the power of eminent domain. The act lets the Authority fix the road\'s location, subject to the State Highway Commission, and puts its powers beyond any city\'s supervision.', source: 'Acts of Assembly, 1954, ch. 705. Library of Virginia, Wikipedia and VCU give 1955 for the Authority', sure: 'disputed' },
  { date: 'About four months later', what: 'The Authority announces that the road will run through Jackson Ward.', source: 'Campbell, 2012, p. 154, as cited by Wikipedia (the book not seen)', sure: 'unconfirmed' },
  { date: '1955–1958', what: 'Clearance and construction. The Authority photographs the work monthly, 1956–58. In 1956 Sixth Mount Zion Baptist Church is spared.', source: 'Community Plan, 2026; Library of Virginia, 2024; DHR nomination, 1996', sure: 'opened' },
  { date: 'July 1, 1958', what: 'The Turnpike opens: 34.7 miles, $76.7 million, paid for by toll revenue bonds. In August it becomes part of I-95.', source: 'Library of Virginia, 2024; Wikipedia', sure: 'opened' },
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
  const TW = W - TX - 14
  const parts: string[] = []
  let y = 30
  parts.push(t(16, y, 'THE TURNPIKE THROUGH THE WARD, 1946–58', 'h ink'))
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
  for (const [sure, label] of [['opened', 'sources opened for this story agree'], ['disputed', 'opened sources disagree (named)'], ['unconfirmed', 'rests on another writer\'s reading of a book not seen']] as const) {
    parts.push(mark(X, y, sure, 4.6) + t(TX, y + 4.5, label, 'b ink'))
    y += 22
  }
  const h = y + 6
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${n(h)}" width="${W}" height="${n(h)}" role="img" aria-labelledby="jw-tl-t jw-tl-d">
<title id="jw-tl-t">How the Richmond–Petersburg Turnpike came to be built through Jackson Ward, Richmond, 1946 to 1958</title>
<desc id="jw-tl-d">${esc(MOMENTS.map((m) => `${m.date}: ${m.what} (${m.source})`).join(' '))}</desc>
${STYLE}
<rect width="${W}" height="${n(h)}" class="bg"/>
${parts.join('\n')}
<circle cx="${X}" cy="${n(bottom)}" r="${n(DOT)}" class="ink"/>
</svg>
`
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const file = fileURLToPath(new URL('../../../pages/jackson-ward-timeline.svg', import.meta.url))
  writeFileSync(file, timeline())
  console.error('wrote pages/jackson-ward-timeline.svg')
}
