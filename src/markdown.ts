/**
 * Just enough Markdown for the explorer's content pages, and safe by construction.
 *
 * Every piece of source text is HTML-escaped; the only markup in the output is markup this
 * file writes. Links keep http(s), mailto, relative and in-page targets and drop any other
 * scheme (`javascript:` and friends become `#`).
 *
 * Blocks: ATX headings (`#`…`######`), paragraphs, `-`/`*`/`+` and `1.` lists (nested by
 * indenting), fenced code (```), block quotes, pipe tables, and `---` rules.
 * Inline: `code`, **strong**, *em* / _em_, [links](url), ![images](src), <https://autolinks>,
 * backslash escapes, and a hard break from two trailing spaces.
 *
 * Headings get GitHub-style ids (lower case, punctuation dropped, spaces to hyphens), so a
 * page reads the same, anchors included, on GitHub and in the explorer.
 */

export interface Heading {
  readonly level: number
  /** The anchor, without any prefix: what a `#fragment` link names. */
  readonly id: string
  readonly text: string
}

export interface MarkdownOptions {
  /** Prepended to every heading id in the HTML (not in `headings`), to keep ids unique in a page that holds several documents. */
  readonly idPrefix?: string
  /** Rewrite a link target; called with targets that have already passed the safety check. */
  readonly link?: (href: string) => string
  /** Resolve an image source to a URL (a data: URI, say). Null drops the image to its alt text. */
  readonly image?: (src: string) => string | null
}

export interface MarkdownResult {
  readonly html: string
  readonly headings: Heading[]
}

export const escapeHtml = (s: string): string =>
  s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string)

/** A link target, or null when its scheme is not one a page should follow. */
export const safeHref = (href: string): string | null => {
  const h = href.trim()
  // Control characters and whitespace inside a scheme are how filters get dodged.
  if (/[\u0000-\u001f\u007f]/.test(h)) return null
  const scheme = h.match(/^([a-z][a-z0-9+.-]*):/i)
  if (scheme === null) return h
  return ['http', 'https', 'mailto'].includes(scheme[1].toLowerCase()) ? h : null
}

/** GitHub's heading anchor: lower case, letters/digits/space/hyphen/underscore kept, spaces to hyphens. */
export const slugify = (text: string): string =>
  text.toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu, '').trim().replace(/\s/g, '-')

const PUNCT = /[!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~]/

/** Inline markup to HTML. */
export const inline = (src: string, opts: MarkdownOptions = {}): string => {
  let out = ''
  let i = 0
  const n = src.length
  const findClose = (delim: string, from: number): number => {
    let j = src.indexOf(delim, from)
    while (j !== -1) {
      // A closing delimiter follows non-space, and an em `*` must not be half of a `**`.
      const prevOk = !/\s/.test(src[j - 1] ?? ' ')
      const single = delim.length === 1
      const doubled = single && (src[j + 1] === delim || src[j - 1] === delim)
      const wordAfter = delim[0] === '_' && /[\p{L}\p{N}]/u.test(src[j + delim.length] ?? '')
      if (prevOk && !doubled && !wordAfter && j > from) return j
      j = src.indexOf(delim, j + 1)
    }
    return -1
  }
  const linkParts = (start: number): { text: string; href: string; end: number } | null => {
    // [text](href "title") with balanced brackets in the text.
    let depth = 0
    let j = start
    for (; j < n; j++) {
      if (src[j] === '\\') { j++; continue }
      if (src[j] === '[') depth++
      else if (src[j] === ']') { depth--; if (depth === 0) break }
    }
    if (j >= n || src[j + 1] !== '(') return null
    // The target ends at the ")" that balances its "(": URLs can hold parentheses.
    let close = -1
    for (let k = j + 2, d = 1; k < n; k++) {
      if (src[k] === '\\') { k++; continue }
      if (src[k] === '(') d++
      else if (src[k] === ')' && --d === 0) { close = k; break }
    }
    if (close === -1) return null
    const target = src.slice(j + 2, close).trim().replace(/\s+"[^"]*"$/, '')
    return { text: src.slice(start + 1, j), href: target.replace(/^<|>$/g, ''), end: close + 1 }
  }
  while (i < n) {
    const c = src[i]
    if (c === '\\' && i + 1 < n && PUNCT.test(src[i + 1])) {
      out += escapeHtml(src[i + 1])
      i += 2
      continue
    }
    if (c === '`') {
      let run = 1
      while (src[i + run] === '`') run++
      const fence = '`'.repeat(run)
      const end = src.indexOf(fence, i + run)
      if (end !== -1) {
        let code = src.slice(i + run, end).replace(/\n/g, ' ')
        if (code.length > 2 && code.startsWith(' ') && code.endsWith(' ')) code = code.slice(1, -1)
        out += '<code>' + escapeHtml(code) + '</code>'
        i = end + run
        continue
      }
      out += escapeHtml(fence)
      i += run
      continue
    }
    if (c === '!' && src[i + 1] === '[') {
      const p = linkParts(i + 1)
      if (p !== null) {
        const safe = safeHref(p.href)
        const url = safe === null ? null : opts.image ? opts.image(safe) : safe
        out += url === null
          ? escapeHtml(p.text)
          : '<img src="' + escapeHtml(url) + '" alt="' + escapeHtml(p.text) + '" loading="lazy">'
        i = p.end
        continue
      }
    }
    if (c === '[') {
      const p = linkParts(i)
      if (p !== null) {
        const safe = safeHref(p.href)
        const href = safe === null ? '#' : opts.link ? opts.link(safe) : safe
        const external = /^https?:/i.test(href)
        out += '<a href="' + escapeHtml(href) + '"' + (external ? ' target="_blank" rel="noopener"' : '') + '>' +
          inline(p.text, opts) + '</a>'
        i = p.end
        continue
      }
    }
    if (c === '<') {
      const m = src.slice(i).match(/^<((?:https?:\/\/|mailto:)[^\s<>]+)>/i)
      if (m) {
        const external = /^https?:/i.test(m[1])
        out += '<a href="' + escapeHtml(m[1]) + '"' + (external ? ' target="_blank" rel="noopener"' : '') + '>' + escapeHtml(m[1]) + '</a>'
        i += m[0].length
        continue
      }
    }
    if ((c === '*' || c === '_') && src[i + 1] === c && src[i + 2] !== undefined && !/\s/.test(src[i + 2])) {
      const d = c + c
      const end = findClose(d, i + 2)
      if (end !== -1) {
        out += '<strong>' + inline(src.slice(i + 2, end), opts) + '</strong>'
        i = end + 2
        continue
      }
    }
    if ((c === '*' || c === '_') && src[i + 1] !== undefined && !/\s/.test(src[i + 1]) && src[i + 1] !== c) {
      // `_` only opens at a word's start: snake_case stays as it is.
      const opens = c === '*' || !/[\p{L}\p{N}]/u.test(src[i - 1] ?? '')
      const end = opens ? findClose(c, i + 1) : -1
      if (end !== -1) {
        out += '<em>' + inline(src.slice(i + 1, end), opts) + '</em>'
        i = end + 1
        continue
      }
    }
    if (c === ' ' && src.startsWith('  \n', i)) {
      out += '<br>\n'
      i += 3
      continue
    }
    out += escapeHtml(c)
    i++
  }
  return out
}

// ---- blocks ------------------------------------------------------------------------------------

const FENCE = /^ {0,3}(`{3,}|~{3,})\s*([\w+-]*)\s*$/
const HEADING = /^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$/
const RULE = /^ {0,3}([-*_])(?:\s*\1){2,}\s*$/
const QUOTE = /^ {0,3}>\s?/
const ITEM = /^( {0,3})([-*+]|\d{1,9}[.)])(\s+|$)/
const TABLE_SEP = /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$/

const startsBlock = (line: string): boolean =>
  FENCE.test(line) || HEADING.test(line) || RULE.test(line) || QUOTE.test(line) || ITEM.test(line)

const cells = (row: string): string[] => {
  let s = row.trim()
  if (s.startsWith('|')) s = s.slice(1)
  if (s.endsWith('|') && !s.endsWith('\\|')) s = s.slice(0, -1)
  const out: string[] = []
  let cur = ''
  for (let i = 0; i < s.length; i++) {
    if (s[i] === '\\' && s[i + 1] === '|') { cur += '|'; i++; continue }
    if (s[i] === '|') { out.push(cur.trim()); cur = ''; continue }
    cur += s[i]
  }
  out.push(cur.trim())
  return out
}

interface Ctx {
  readonly opts: MarkdownOptions
  readonly headings: Heading[]
  readonly used: Map<string, number>
}

const blocks = (lines: readonly string[], ctx: Ctx): string => {
  const out: string[] = []
  let i = 0
  const inl = (s: string) => inline(s, ctx.opts)
  while (i < lines.length) {
    const line = lines[i]
    if (line.trim() === '') { i++; continue }

    const fence = line.match(FENCE)
    if (fence) {
      const close = new RegExp('^ {0,3}' + fence[1][0] + '{' + fence[1].length + ',}\\s*$')
      const body: string[] = []
      i++
      while (i < lines.length && !close.test(lines[i])) body.push(lines[i++])
      i++
      const lang = fence[2] ? ' class="language-' + escapeHtml(fence[2]) + '"' : ''
      out.push('<pre><code' + lang + '>' + escapeHtml(body.join('\n')) + '</code></pre>')
      continue
    }

    const heading = line.match(HEADING)
    if (heading) {
      const level = heading[1].length
      const text = heading[2]
      const plain = text.replace(/[*_`]/g, '').replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
      const base = slugify(plain) || 'section'
      const seen = ctx.used.get(base) ?? 0
      ctx.used.set(base, seen + 1)
      const id = seen === 0 ? base : `${base}-${seen}`
      ctx.headings.push({ level, id, text: plain })
      out.push(`<h${level} id="${escapeHtml((ctx.opts.idPrefix ?? '') + id)}">${inl(text)}</h${level}>`)
      i++
      continue
    }

    if (RULE.test(line)) { out.push('<hr>'); i++; continue }

    if (QUOTE.test(line)) {
      const body: string[] = []
      while (i < lines.length && lines[i].trim() !== '' && (QUOTE.test(lines[i]) || body.length > 0)) {
        body.push(lines[i].replace(QUOTE, ''))
        i++
      }
      out.push('<blockquote>' + blocks(body, ctx) + '</blockquote>')
      continue
    }

    const item = line.match(ITEM)
    if (item) {
      const ordered = /\d/.test(item[2])
      const indent = item[1].length
      const items: string[][] = []
      const start = ordered ? parseInt(item[2], 10) : 1
      let loose = false
      while (i < lines.length) {
        const m = lines[i].match(ITEM)
        if (m === null || m[1].length !== indent || /\d/.test(m[2]) !== ordered) break
        const width = m[1].length + m[2].length + Math.max(1, Math.min(4, m[3].length))
        const body = [lines[i].slice(m[0].length)]
        i++
        while (i < lines.length) {
          const l = lines[i]
          if (l.trim() === '') {
            // A blank line continues the item only if indented content follows.
            const next = lines[i + 1]
            if (next !== undefined && /^\s+\S/.test(next) && next.search(/\S/) >= width) {
              body.push('')
              loose = true
              i++
              continue
            }
            break
          }
          const lead = l.search(/\S/)
          if (lead >= width) { body.push(l.slice(width)); i++; continue }
          const sub = l.match(ITEM)
          if (sub !== null && sub[1].length > indent) { body.push(l.slice(Math.min(lead, width))); i++; continue }
          if (startsBlock(l)) break
          body.push(l.trim()) // lazy continuation of the item's paragraph
          i++
        }
        items.push(body)
        // A blank line between items of the same list keeps the list going.
        if (lines[i]?.trim() === '' && lines[i + 1] !== undefined) {
          const m2 = lines[i + 1].match(ITEM)
          if (m2 !== null && m2[1].length === indent && /\d/.test(m2[2]) === ordered) { i++; loose = true }
        }
      }
      const lis = items.map((body) => {
        const html = blocks(body, ctx)
        const single = html.match(/^<p>([\s\S]*?)<\/p>([\s\S]*)$/)
        // Tight lists keep their text bare; a nested list or code block follows it.
        return '<li>' + (single && !loose && !single[2].includes('<p>') ? single[1] + single[2] : html) + '</li>'
      })
      const tag = ordered ? 'ol' : 'ul'
      out.push(`<${tag}${ordered && start !== 1 ? ` start="${start}"` : ''}>${lis.join('')}</${tag}>`)
      continue
    }

    if (line.includes('|') && i + 1 < lines.length && TABLE_SEP.test(lines[i + 1]) && lines[i + 1].includes('-')) {
      const head = cells(line)
      const align = cells(lines[i + 1]).map((s) => (s.startsWith(':') && s.endsWith(':') ? 'center' : s.endsWith(':') ? 'right' : s.startsWith(':') ? 'left' : ''))
      const a = (k: number) => (align[k] ? ` style="text-align:${align[k]}"` : '')
      i += 2
      const rows: string[][] = []
      while (i < lines.length && lines[i].trim() !== '' && lines[i].includes('|')) rows.push(cells(lines[i++]))
      out.push(
        '<div class="table"><table><thead><tr>' + head.map((h, k) => `<th${a(k)}>${inl(h)}</th>`).join('') + '</tr></thead><tbody>' +
        rows.map((r) => '<tr>' + head.map((_, k) => `<td${a(k)}>${inl(r[k] ?? '')}</td>`).join('') + '</tr>').join('') +
        '</tbody></table></div>',
      )
      continue
    }

    const para: string[] = []
    while (i < lines.length && lines[i].trim() !== '' && (para.length === 0 || !startsBlock(lines[i]))) {
      // A table can start straight after a paragraph line.
      if (para.length > 0 && lines[i].includes('|') && TABLE_SEP.test(lines[i + 1] ?? '') && (lines[i + 1] ?? '').includes('-')) break
      para.push(lines[i].replace(/^\s+/, ''))
      i++
    }
    out.push('<p>' + inl(para.join('\n').replace(/\s+$/, '')) + '</p>')
  }
  return out.join('\n')
}

export const markdown = (src: string, opts: MarkdownOptions = {}): MarkdownResult => {
  const ctx: Ctx = { opts, headings: [], used: new Map() }
  const lines = src.replace(/\r\n?/g, '\n').replace(/\t/g, '    ').split('\n')
  return { html: blocks(lines, ctx), headings: ctx.headings }
}
