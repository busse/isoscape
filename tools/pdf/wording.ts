/**
 * PDF wording: the few phrases on a web page that tell the reader to work something the PDF does
 * not have (a compare slider's divider, the lightbox, the figure grid), and what the PDF says in
 * their place. Applied only to the print build (print.ts), never to the page's source or the web
 * page. Everything else in a page prints word for word.
 *
 * The shared list is below. A story adds its own in `tools/stories/<story>/pdf.json`:
 *
 *     { "substitutions": [{ "pattern": "…", "replace": "…", "scope": "all", "note": "…" }],
 *       "allow": ["a phrase the check may pass, e.g. Richmond Free Press"] }
 *
 * `pattern` is a regular expression over the compiled HTML (case-sensitive, `**x**` is
 * `<strong>x</strong>`); `replace` may use `$1`… and, in a compare figure, `{a}` and `{b}` for
 * the slider's two labels as written. `scope` is `compare` (a compare figure's caption and its
 * pictures' alt text) or `all` (the whole page, alt text included). Rewording is preferred to
 * deleting; a sentence is dropped only when nothing true of the PDF remains of it.
 *
 * After the substitutions, `deadInstructions` looks through the page's text and alt text for
 * words that usually mean an instruction to a screen (drag, click, tap, hover, press, swipe,
 * scroll, zoom, arrow keys, lightbox, slider, divider, All figures). story_pdf.py fails if any is
 * left that no rule handled and no `allow` entry covers, so a new story cannot ship a PDF that
 * tells its reader to drag a divider that is not there.
 */

export interface Substitution {
  readonly pattern: string
  readonly replace: string
  readonly scope: 'compare' | 'all'
  readonly note: string
}

export const SHARED: readonly Substitution[] = [
  {
    pattern: '\\(left of the divider\\)',
    replace: '(first picture)',
    scope: 'compare',
    note: 'a compare figure: the left side of the slider is printed first',
  },
  {
    pattern: '\\(left\\)',
    replace: '(first picture)',
    scope: 'compare',
    note: 'a compare figure: the left side of the slider is printed first',
  },
  {
    pattern: '\\(right\\)',
    replace: '(second picture)',
    scope: 'compare',
    note: 'a compare figure: the right side of the slider is printed second',
  },
  {
    pattern: '([.;:]\\s+)[Dd]rag the divider, or move it with the arrow keys\\.',
    replace: '$1{The} two pictures follow, {a} first, then {b}.',
    scope: 'compare',
    note: 'a compare figure: the slider becomes its two pictures, in order',
  },
  {
    pattern: '([.;:]\\s+)[Dd]rag the divider to compare\\.',
    replace: '$1{The} two pictures follow, {a} first, then {b}.',
    scope: 'compare',
    note: 'a compare figure: the slider becomes its two pictures, in order',
  },
  {
    pattern: '\\s*Click any picture to\\s+open it large[^.]*\\.(?=\\s|<|$)',
    replace: '',
    scope: 'all',
    note: 'the lightbox and the figure grid: nothing of the sentence is true of a PDF, where every figure is already large',
  },
]

/** Words that usually tell a reader to work a screen. `press` only in lower case (the Richmond Free Press is a newspaper). */
const DEAD = /\b(?:drag(?:s|ging|ged)?|click(?:s|ing|ed)?|taps?|tapping|hover(?:s|ing)?|swipe[sd]?|swiping|scroll(?:s|ing)?|zoom(?:s|ing)?|pinch(?:es|ing)?|arrow keys?|lightbox|slider|divider|All figures)\b|\bpress(?:es|ing)?\b(?! release)/gi
const DEAD_PRESS = /\bpress(?:es|ing)?\b/

export interface Change {
  readonly where: string
  readonly from: string
  readonly to: string
}

/** Fill `{a}`, `{b}` and `{The}` (capitalized after a full stop) in a replacement. */
const fill = (replace: string, groups: string[], labels?: { a: string; b: string }): string => {
  let out = replace.replace(/\$(\d)/g, (_m, i: string) => groups[Number(i)] ?? '')
  const lead = groups[1] ?? ''
  out = out.replace('{The}', /^[.:]/.test(lead) ? 'The' : 'the')
  if (labels !== undefined) out = out.replace(/\{a\}/g, labels.a).replace(/\{b\}/g, labels.b)
  return out
}

/** Apply the rules of one scope to a piece of HTML, recording each change. */
export const substitute = (html: string, rules: readonly Substitution[], scope: Substitution['scope'], where: string, changes: Change[], labels?: { a: string; b: string }): string => {
  let out = html
  for (const r of rules) {
    if (r.scope !== scope) continue
    out = out.replace(new RegExp(r.pattern, 'g'), (...m: unknown[]) => {
      const groups = m.slice(0, -2).filter((x) => typeof x === 'string' || x === undefined) as string[]
      const to = fill(r.replace, groups, labels)
      changes.push({ where, from: String(m[0]).replace(/\s+/g, ' ').trim(), to: to.replace(/\s+/g, ' ').trim() })
      return to
    })
  }
  return out
}

/**
 * Words left in the print build's text and alt text that look like instructions to a screen,
 * with the sentence around each. Link targets and URLs are not text, and `allow` phrases pass.
 */
export const deadInstructions = (html: string, allow: readonly string[] = []): string[] => {
  const alts = [...html.matchAll(/\balt="([^"]*)"/g)].map((m) => m[1])
  const text = [html.replace(/<[^>]*>/g, ' '), ...alts].join(' \n ')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&')
    .replace(/\S*(?:https?:\/\/|www\.|\.(?:com|org|gov|edu|html?|pdf)\b)\S*/g, ' ')
    .replace(/\s+/g, ' ')
  let scrubbed = text
  for (const a of allow) scrubbed = scrubbed.split(a).join(' '.repeat(a.length))
  const found: string[] = []
  for (const m of scrubbed.matchAll(DEAD)) {
    if (/^press/i.test(m[0]) && !DEAD_PRESS.test(m[0])) continue
    const at = m.index ?? 0
    const start = Math.max(0, text.lastIndexOf('.', at) + 1, at - 120)
    const end = Math.min(text.length, at + 120)
    found.push(text.slice(start, end).trim())
  }
  return found
}
