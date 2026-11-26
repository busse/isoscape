/**
 * A story page as a document to print to PDF: the page's own Markdown, compiled as the site
 * compiles it, laid out for one of two editions with its own print stylesheet and `@page` size.
 * `story_pdf.py` (beside this) prepares the pictures, runs this, prints the result with headless
 * Chrome and finishes the PDF; see "Story PDFs" in the README.
 *
 *   node tools/pdf/print.ts <slug> --edition phone|large --assets assets.json [--pages pages.json]
 *        [--date "November 22, 2026"] --out <file.html>
 *
 * Nothing here is particular to one story. What it does to a page:
 *
 * - A title page (title, deck, a picture, "Chris Busse", the edition and its date, the live
 *   address), then a contents list of the `##` sections with their page numbers (`--pages`, from a
 *   first printing), then the whole page as written, then a short colophon.
 * - A compare slider becomes its two pictures, one after the other, each under its own label.
 * - The lightbox's links around pictures are dropped: a figure is simply large.
 * - Links into this page stay in the PDF; links to the explorer, a map or another page go to the
 *   live site; everything else is left as written.
 * - Wide pictures on the phone (see `PANORAMA`) are shown whole, then as two overlapping halves.
 *   Tall pictures (a timeline) are cut into page-high pieces at blank rows, in either edition.
 * - On the phone a table of three or more columns becomes a stack of rows.
 * - A paragraph that starts "Content note" is kept with the paragraph after it.
 * - The few phrases that tell a web reader to work a screen (drag the divider, click a picture)
 *   are reworded for paper by the rules in wording.ts; every change is reported, and any such
 *   phrase left without a rule is reported as `dead` (story_pdf.py fails on it).
 * - No picture is cropped: each is fitted whole, and nothing is wider than the page.
 */

import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { THEME_CSS } from '../../src/explorer.ts'
import { escapeHtml } from '../../src/markdown.ts'
import { compilePage, PAGES_DIR, type Page } from '../../src/pages.ts'
import { deadInstructions, SHARED, substitute, type Change, type Substitution } from './wording.ts'

export const AUTHOR = 'Chris Busse'
export const SITE_URL = 'https://isoscape.chrisbusse.com/'

export type Edition = 'phone' | 'large'

/** A picture as prepared for an edition (story_pdf.py): its file beside the HTML and its size. */
export interface Asset {
  readonly file: string
  readonly w: number
  readonly h: number
  /** Rows (as fractions of the height, 0–1) where the picture is blank across: places it may be cut. */
  readonly gaps?: readonly number[]
}

export interface PrintOptions {
  readonly edition: Edition
  readonly assets: Readonly<Record<string, Asset>>
  /** The page each section (by heading id) starts on, from a first printing. */
  readonly pages?: Readonly<Record<string, number>>
  /** The edition's date, as words. */
  readonly date: string
  readonly siteUrl?: string
}

/**
 * The two editions, in CSS px (96 to the inch; Chrome prints 1 px as 0.75 pt).
 *
 * phone: 360 × 640 px (270 × 480 pt, 3.75 × 6.67 in), 9:16. A phone's PDF viewer fits the page's
 * width to the screen (about 390 px on a 6.1-inch phone), and 9:16 is about the screen left after
 * the viewer's bars, so one page fills one screen. Body type 17 px, which on a 390 px screen is
 * 17 × 390 / 360 = 18.4 px; captions and tables 15 px (16.3 px).
 *
 * large: US Letter with 0.75 in margins. One text column of about 70 characters (33 em of
 * 15.5 px body); wide figures run the full 7 in between the margins.
 */
export const EDITIONS = {
  phone: { w: 360, h: 640, margin: [22, 18, 40, 18], body: 17, col: 324, wide: 324, maxPic: 470 },
  large: { w: 816, h: 1056, margin: [60, 72, 70, 72], body: 15.5, col: 512, wide: 672, maxPic: 820 },
} as const

/** Phone: a picture this much wider than tall is shown whole, then as two overlapping halves. */
export const PANORAMA = 1.8
/** Each half's share of the picture's width (so the halves overlap by 10%). */
export const HALF = 0.55

const esc = escapeHtml
const attr = (s: string) => escapeHtml(s)
const unesc = (s: string) => s.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')
const capital = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

/** The running title: the title up to its first colon, else its first comma. */
export const shortTitle = (title: string): string => {
  const colon = title.indexOf(':')
  if (colon > 0) return title.slice(0, colon).trim()
  const comma = title.indexOf(',')
  return (comma > 0 ? title.slice(0, comma) : title).trim()
}

/** Where a link in a story should go from a PDF: this page's sections stay inside, the rest goes live. */
export const printRoute = (href: string, slug: string, siteUrl = SITE_URL): string => {
  if (href.startsWith('#/')) {
    const [target, ...rest] = href.slice(2).split('/')
    const section = rest.join('/')
    if (target === slug) return section ? `#${section}` : '#'
    return `${siteUrl}p/${target}.html${section ? `#${section}` : ''}`
  }
  if (href.startsWith('#') && href.length > 1) return `${siteUrl}${href}`
  return href
}

/** The live address of a story's static page. */
export const liveUrl = (slug: string, siteUrl = SITE_URL) => `${siteUrl}p/${slug}.html`

/** The page compiled for print: GitHub's heading ids, links routed for a PDF, images by name. */
export const compileForPrint = (slug: string, dir = PAGES_DIR, siteUrl = SITE_URL): { page: Page; src: string } => {
  const src = readFileSync(join(dir, `${slug}.md`), 'utf8')
  const page = compilePage(src, `${slug}.md`, (name) => {
    try {
      return readFileSync(join(dir, name))
    } catch {
      return null
    }
  }, siteUrl, { idPrefix: '', route: (href) => printRoute(href, slug, siteUrl), imageHref: (name) => name, pdfHref: null })
  return { page, src }
}

// ---- pictures -----------------------------------------------------------------------------------

interface Pic {
  readonly name: string
  readonly alt: string
}

/** A crop of a picture: x, y, w, h in the picture's own pixels, shown at the container's width. */
const crop = (a: Asset, x: number, y: number, w: number, h: number, alt: string): string =>
  `<div class="crop" style="aspect-ratio: ${Math.round(w)} / ${Math.round(h)}"><img src="${attr(a.file)}" alt="${attr(alt)}" style="width: ${(100 * a.w / w).toFixed(4)}%; margin-left: -${(100 * x / w).toFixed(4)}%; margin-top: -${(100 * y / w).toFixed(4)}%"></div>`

/**
 * The pieces to cut a tall picture into so none is taller than `max` (in the picture's pixels), as
 * [top, bottom] pairs: at the lowest blank row in the lower half of each piece where there is one,
 * else at the limit, with the next piece starting a little above it so nothing is lost at the cut.
 */
export const piecesFor = (h: number, max: number, gaps: readonly number[] = []): [number, number][] => {
  const out: [number, number][] = []
  let from = 0
  while (h - from > max) {
    const blank = gaps.map((g) => g * h).filter((y) => y > from + max * 0.5 && y <= from + max)
    if (blank.length > 0) {
      const at = Math.max(...blank)
      out.push([from, at])
      from = at
    } else {
      out.push([from, from + max])
      from = from + max * 0.96
    }
  }
  out.push([from, h])
  return out
}

/**
 * One picture as the edition shows it. `seen` holds the pictures already shown in halves, so a
 * picture that comes back (in a compare figure) is shown whole the second time.
 */
const picture = (p: Pic, wide: boolean, ed: Edition, assets: PrintOptions['assets'], seen: Set<string>, figLabel: string): { html: string; height: number } => {
  const a = assets[p.name]
  if (a === undefined) throw new Error(`no prepared picture for ${p.name}`)
  const spec = EDITIONS[ed]
  const width = wide ? spec.wide : spec.col
  const aspect = a.w / a.h
  // Tall: page-high pieces, cut at blank rows.
  if (width / aspect > spec.maxPic) {
    const pieces = piecesFor(a.h, (spec.maxPic / width) * a.w, a.gaps)
    return {
      html: pieces.map(([top, bottom], i) => {
        const label = i === 0 ? '' : `<p class="pic-label" aria-hidden="true">${esc(figLabel)}, continued</p>`
        return `<div class="piece">${label}${crop(a, 0, top, a.w, bottom - top, i === 0 ? p.alt : '')}</div>`
      }).join('\n'),
      height: spec.maxPic,
    }
  }
  const whole = `<div class="piece"><img src="${attr(a.file)}" alt="${attr(p.alt)}" width="${a.w}" height="${a.h}"></div>`
  if (ed !== 'phone' || aspect < PANORAMA || seen.has(p.name)) return { html: whole, height: width / aspect }
  seen.add(p.name)
  const hw = a.w * HALF
  return {
    html: whole + '\n' +
      `<div class="piece"><p class="pic-label" aria-hidden="true">Left half, enlarged</p>${crop(a, 0, 0, hw, a.h, '')}</div>\n` +
      `<div class="piece"><p class="pic-label" aria-hidden="true">Right half, enlarged</p>${crop(a, a.w - hw, 0, hw, a.h, '')}</div>`,
    height: width / aspect + 2 * (width / (aspect * HALF) + 30),
  }
}

/**
 * About how tall a figure's caption sets, in px: its text at the caption size, with a line for
 * each paragraph break and two lines for each table row (on the phone, three).
 */
const captionHeight = (cap: string, ed: Edition, wide: boolean): number => {
  const spec = EDITIONS[ed]
  const size = ed === 'phone' ? 15 : 12.5
  const perLine = ((wide ? spec.wide : spec.col) - 24) / (size * 0.52)
  const rows = (cap.match(/<tr>/g) ?? []).length
  const text = textOf(cap.replace(/<table[\s\S]*?<\/table>/g, ''))
  return (Math.ceil(text.length / perLine) + (cap.match(/<p>/g) ?? []).length + rows * (ed === 'phone' ? 3 : 1.4)) * size * 1.5 + 20
}

const IMG = /<img\b[^>]*?\bsrc="([^"]*)"[^>]*?\balt="([^"]*)"[^>]*>/

/** Every figure of the compiled page, laid out for the edition. */
export const printFigures = (html: string, ed: Edition, assets: PrintOptions['assets'], seen = new Set<string>(), rules: readonly Substitution[] = SHARED, changes: Change[] = []): string =>
  html.replace(/<figure class="([^"]*)" id="([^"]*)">\n([\s\S]*?)\n<figcaption>([\s\S]*?)<\/figcaption>\n<\/figure>/g, (_m, cls: string, id: string, body: string, cap: string) => {
    // On Letter there is room: in the large edition every landscape photo-like picture (not an
    // SVG diagram) spans the full measure, as the page's own `wide` figures do.
    const names = [...body.matchAll(new RegExp(IMG.source, 'g'))].map((m) => assets[m[1]])
    const wide = /\bwide\b/.test(cls) || (ed === 'large' && names.length > 0 && names.every((a) => a !== undefined && !a.file.endsWith('.svg') && a.w > a.h))
    const n = cap.match(/<span class="fig-n">([^<]*)<\/span>/)?.[1] ?? ''
    const label = n.replace(/\.$/, '')
    let pics: string
    let height: number
    const cmp = body.match(/^<div class="cmp" data-a="([^"]*)" data-b="([^"]*)"/)
    if (cmp !== null) {
      // The slider's instructions, in its caption and its pictures' alt text, become the PDF's (wording.ts).
      const labels = { a: unesc(cmp[1]), b: unesc(cmp[2]) }
      cap = substitute(cap, rules, 'compare', `${label} caption`, changes, labels)
      const imgs = [...body.matchAll(new RegExp(IMG.source, 'g'))].slice(0, 2)
      const done = imgs.map((m, i) => picture({ name: m[1], alt: unesc(substitute(m[2], rules, 'compare', `${label} alt text, picture ${i + 1}`, changes, labels)) }, wide, ed, assets, seen, label))
      pics = done.map((d, i) => `<div class="side"><p class="side-label">${esc(capital(unesc(i === 0 ? cmp[1] : cmp[2])))}</p>\n${d.html}</div>`).join('\n')
      height = done.reduce((t, d) => t + d.height + 30, 0)
    } else {
      const done = [...body.matchAll(new RegExp(IMG.source, 'g'))].map((m) => picture({ name: m[1], alt: unesc(m[2]) }, wide, ed, assets, seen, label))
      pics = done.map((d) => d.html).join('\n')
      height = done.reduce((t, d) => t + d.height, 0)
    }
    const many = (pics.match(/class="piece"/g) ?? []).length > 1
    // A figure that would fill most of a page may break inside, after its picture, so a long
    // caption runs on rather than pushing the whole figure to a new page and leaving a gap.
    const room = EDITIONS[ed].h - EDITIONS[ed].margin[0] - EDITIONS[ed].margin[2]
    const long = /<table|<div class="stack"/.test(cap) || height + captionHeight(cap, ed, wide) > room * (ed === 'phone' ? 0.8 : 0.5)
    const classes = ['fig', ...(wide ? ['wide'] : []), ...(many ? ['many'] : []), ...(long ? ['long'] : [])].join(' ')
    return `<figure class="${classes}" id="${id}">\n${pics}\n<figcaption>${cap}</figcaption>\n</figure>`
  })

// ---- tables -------------------------------------------------------------------------------------

const cellsOf = (row: string, tag: 'th' | 'td'): string[] => [...row.matchAll(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, 'g'))].map((m) => m[1])
const textOf = (h: string) => unesc(h.replace(/<[^>]*>/g, '')).trim()

/**
 * On the phone, a table of three or more columns as a stack of rows: each row's first cell (with
 * the second, when the first is only a short number or mark) in bold, then the rest as
 * "Column: value". Narrower tables stay tables.
 */
export const stackTables = (html: string): string =>
  html.replace(/<div class="table"><table>([\s\S]*?)<\/table><\/div>/g, (whole, inner: string) => {
    const head = cellsOf(inner.match(/<thead>([\s\S]*?)<\/thead>/)?.[1] ?? '', 'th')
    if (head.length < 3) return whole
    const rows = [...(inner.match(/<tbody>([\s\S]*?)<\/tbody>/)?.[1] ?? '').matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map((m) => cellsOf(m[1], 'td'))
    const shortFirst = rows.every((r) => textOf(r[0] ?? '').length <= 4)
    const lead = shortFirst ? 2 : 1
    const items = rows.map((r) => {
      const title = r.slice(0, lead).filter((c) => textOf(c) !== '').join(' ')
      const rest = r.slice(lead).map((c, i) => `<span class="k">${head[i + lead]}:</span> ${c === '' ? '–' : c}`).join('<span class="sep"> · </span>')
      return `<li><p class="t">${title}</p>${rest ? `<p class="v">${rest}</p>` : ''}</li>`
    })
    return `<div class="stack"><ul>${items.join('')}</ul></div>`
  })

// ---- the document -------------------------------------------------------------------------------

export interface PrintDoc {
  readonly html: string
  readonly title: string
  readonly short: string
  /** The `##` sections, in order: the contents list. */
  readonly sections: readonly { readonly id: string; readonly text: string }[]
  /** Every heading's text, in order (for the PDF's outline). */
  readonly headings: readonly string[]
  /** Every change of wording the print build made (wording.ts). */
  readonly substitutions: readonly Change[]
  /** Likely instructions to a screen left after the substitutions: the build must fail on any. */
  readonly dead: readonly string[]
  readonly figures: number
  readonly compares: number
}

/** The title page's picture: a figure set before the first section, else the page's `social:` picture. */
const coverPicture = (src: string, html: string): string | undefined => {
  const first = html.search(/<h2[\s>]/)
  const fig = html.match(/<figure class="[^"]*" id="[^"]*">\n(?:<a [^>]*>)?<img src="([^"]*)"/)
  if (fig !== null && (fig.index ?? 0) < first) return fig[1]
  return src.match(/^social:\s*(\S+)\s*$/m)?.[1]
}

/** An address as shown: no scheme, breakable after each slash, the file name never split at its hyphen. */
const shownUrl = (url: string): string => {
  const parts = url.replace(/^https:\/\//, '').split('/')
  const last = parts.pop() ?? ''
  return parts.map((p) => esc(p) + '/<wbr>').join('') + `<span class="nobr">${esc(last)}</span>`
}

const STORIES_DIR = fileURLToPath(new URL('../stories/', import.meta.url))

/** A story's own PDF wording (`tools/stories/<slug>/pdf.json`), if it has any. */
export const storyWording = (slug: string): { substitutions: Substitution[]; allow: string[] } => {
  try {
    const j = JSON.parse(readFileSync(join(STORIES_DIR, slug, 'pdf.json'), 'utf8')) as { substitutions?: Substitution[]; allow?: string[] }
    return { substitutions: j.substitutions ?? [], allow: j.allow ?? [] }
  } catch (e) {
    if ((e as { code?: string }).code === 'ENOENT') return { substitutions: [], allow: [] }
    throw e
  }
}

export const printDoc = (slug: string, opts: PrintOptions, dir = PAGES_DIR): PrintDoc => {
  const siteUrl = opts.siteUrl ?? SITE_URL
  const { page, src } = compileForPrint(slug, dir, siteUrl)
  const ed = opts.edition
  const url = liveUrl(slug, siteUrl)
  let body = page.html
  // The title and deck go on the title page.
  const h1 = body.match(/^<h1 id="([^"]*)">([\s\S]*?)<\/h1>\n?/)
  if (h1 !== null) body = body.slice(h1[0].length)
  const deck = body.match(/^<p class="deck">([\s\S]*?)<\/p>\n?/)
  if (deck !== null) body = body.slice(deck[0].length)
  // The lightbox's links around pictures go; the pictures stay.
  body = body.replace(/<a class="fig-open"[^>]*>(<img [^>]*>)<\/a>/g, '$1')
  const own = storyWording(slug)
  const rules = [...SHARED, ...own.substitutions]
  const changes: Change[] = []
  body = printFigures(body, ed, opts.assets, new Set(), rules, changes)
  body = substitute(body, rules, 'all', 'text', changes)
  const dead = deadInstructions(body, own.allow)
  if (ed === 'phone') body = stackTables(body)
  // A road number (I-95) is not broken at its hyphen.
  body = body.replace(/>([^<]+)</g, (_m, t: string) => '>' + t.replace(/\b([A-Z]{1,3}-\d{1,3})\b/g, '<span class="nobr">$1</span>') + '<')
  // A content note stays with what it warns of.
  body = body.replace(/<p>(<em>)?Content note\b/g, (m) => m.replace('<p>', '<p class="keep-next">'))
  const sections = [...body.matchAll(/<h2 id="([^"]*)">([\s\S]*?)<\/h2>/g)].map((m) => ({ id: m[1], text: textOf(m[2]) }))
  const cover = coverPicture(src, page.html)
  const coverAsset = cover === undefined ? undefined : opts.assets[cover]
  const short = shortTitle(page.title)
  const pageNo = (id: string) => opts.pages?.[id]
  const edLabel = ed === 'phone' ? 'Phone edition' : 'Large-screen edition'
  const title = h1 === null ? esc(page.title) : h1[2]
  const html = `<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<title>${esc(page.title)}</title>
<meta name="author" content="${AUTHOR}">
<meta name="description" content="${attr(page.summary ?? page.deck ?? '')}">
<style>
${fontFaces()}
${THEME_CSS}
${printCss(ed, short, url)}
</style>
</head>
<body class="${ed}">
<section class="cover" aria-label="Title page">
<h1 id="${h1?.[1] ?? 'title'}">${title.replace(/\b([A-Z]{1,3}-\d{1,3})\b/g, '<span class="nobr">$1</span>')}</h1>
${deck === null ? '' : `<p class="deck">${deck[1]}</p>`}
${coverAsset === undefined ? '' : `<div class="cover-pic"><img src="${attr(coverAsset.file)}" alt="" width="${coverAsset.w}" height="${coverAsset.h}"></div>`}
<p class="byline">${AUTHOR}</p>
<p class="edition">${edLabel}, ${esc(opts.date)}</p>
<p class="live">The current version, with any later corrections, is at <a href="${attr(url)}">${shownUrl(url)}</a></p>
</section>
<nav class="contents" aria-labelledby="contents">
<h2 id="contents" class="contents-h">Contents</h2>
<ol>
${sections.map((s) => `<li><a href="#${attr(s.id)}"><span class="ct">${esc(s.text)}</span><span class="cp">${pageNo(s.id) ?? '00'}</span></a></li>`).join('\n')}
<li><a href="#about-this-pdf"><span class="ct">About this PDF</span><span class="cp">${pageNo('about-this-pdf') ?? '00'}</span></a></li>
</ol>
</nav>
<main class="prose">
${body}
<section class="colophon">
<h2 id="about-this-pdf">About this PDF</h2>
<p>Made from the web page with isoscape's PDF tool, drafted with Claude. ${edLabel}, ${esc(opts.date)}, from the page as it stood that day; the page's own note on how it was made is above, unchanged.</p>
<p>The current version, with any later corrections, is at <a href="${attr(url)}">${shownUrl(url)}</a></p>
</section>
</main>
</body>
</html>
`
  return {
    html,
    title: page.title,
    short,
    sections: [...sections, { id: 'about-this-pdf', text: 'About this PDF' }],
    substitutions: changes,
    dead,
    headings: [...html.matchAll(/<h[1-6][^>]*>([\s\S]*?)<\/h[1-6]>/g)].map((m) => textOf(m[1]).replace(/\s+/g, ' ')),
    figures: page.figures.length,
    compares: page.figures.filter((f) => f.compare).length,
  }
}

// ---- type ---------------------------------------------------------------------------------------

const FONT_DIR = fileURLToPath(new URL('./fonts/', import.meta.url))

/** Inter, from the TrueType copies beside this file (fonts.py; SIL Open Font License). */
const fontFaces = (): string =>
  [['Regular', 400, 'normal'], ['Italic', 400, 'italic'], ['SemiBold', 600, 'normal'], ['SemiBoldItalic', 600, 'italic'], ['Bold', 700, 'normal'], ['BoldItalic', 700, 'italic']]
    .map(([s, w, st]) => `@font-face { font-family: "Inter PDF"; src: url("file://${FONT_DIR}Inter-${s}.ttf") format("truetype"); font-weight: ${w}; font-style: ${st}; }`).join('\n')

const px = (n: number) => `${n}px`

/** The print stylesheet for an edition. Colors come from the site's theme (THEME_CSS). */
export const printCss = (ed: Edition, short: string, url: string): string => {
  const s = EDITIONS[ed]
  const [mt, mr, mb, ml] = s.margin
  const phone = ed === 'phone'
  const small = phone ? 15 : 12.5
  const foot = phone ? 11.5 : 9.5
  const footer = phone
    ? `@bottom-left { content: "${short.replace(/"/g, '\\"')}"; } @bottom-right { content: counter(page) " / " counter(pages); }`
    : `@bottom-left { content: "${short.replace(/"/g, '\\"')}"; } @bottom-center { content: "${url.replace(/^https:\/\//, '')}"; } @bottom-right { content: "Page " counter(page) " of " counter(pages); }`
  return `@page { size: ${px(s.w)} ${px(s.h)}; margin: ${px(mt)} ${px(mr)} ${px(mb)} ${px(ml)};
  ${footer}
  @bottom-left { font: ${foot}px/1.3 "Inter PDF"; color: #5f5b62; vertical-align: middle; }
  @bottom-center { font: ${foot}px/1.3 "Inter PDF"; color: #5f5b62; vertical-align: middle; }
  @bottom-right { font: ${foot}px/1.3 "Inter PDF"; color: #5f5b62; vertical-align: middle; font-variant-numeric: tabular-nums; }
}
@page :first { @bottom-left { content: none; } @bottom-center { content: none; } @bottom-right { content: none; } }
:root { --dim: #5f5b62; --faint: #77737a; }
html, body { margin: 0; padding: 0; background: #fff; color: var(--ink); }
body { font: ${s.body}px/1.6 "Inter PDF", sans-serif; font-kerning: normal; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
a { color: var(--accent); text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 2px; }
.nobr { white-space: nowrap; }
code { font: .92em "Inter PDF", sans-serif; background: var(--chip); padding: 0 .2em; border-radius: 3px; overflow-wrap: anywhere; }

/* Title page */
.cover { break-after: page; break-inside: avoid; }
.cover h1 { font-size: ${phone ? 23 : 34}px; line-height: 1.15; letter-spacing: -.02em; font-weight: 700; margin: ${phone ? 0 : 40}px 0 ${phone ? 10 : 18}px; }
.cover .deck { font-size: ${phone ? 15 : 17}px; line-height: 1.4; color: var(--dim); margin: 0 0 ${phone ? 10 : 24}px; ${phone ? '' : 'max-width: 36em;'} }
.cover .cover-pic { margin: 0 0 ${phone ? 10 : 28}px; }
.cover .cover-pic img { display: block; max-width: 100%; object-fit: contain; max-height: ${phone ? 140 : 400}px; width: auto; height: auto; margin: 0 auto; }
.cover .byline { font-size: ${phone ? 17 : 18}px; font-weight: 600; margin: ${phone ? 0 : 40}px 0 2px; }
.cover .edition { margin: 0 0 ${phone ? 2 : 6}px; color: var(--dim); font-size: ${small}px; }
.cover .live { margin: 0; font-size: ${small}px; color: var(--dim); overflow-wrap: anywhere; }
.cover .live a { display: inline-block; padding: ${phone ? '4px 0' : '0'}; }

/* Contents */
.contents { break-after: page; }
.contents h2 { font-size: ${phone ? 22 : 24}px; margin: 0 0 ${phone ? 10 : 16}px; font-weight: 650; }
.contents ol { list-style: none; margin: 0; padding: 0; ${phone ? '' : 'max-width: 33em;'} }
.contents li { margin: 0; border-bottom: 1px solid var(--line); break-inside: avoid; }
.contents a { display: flex; gap: 10px; align-items: baseline; padding: ${phone ? '8px 0' : '5px 0'}; min-height: ${phone ? 26 : 0}px; color: var(--ink); text-decoration: none; font-size: ${phone ? 15.5 : 14}px; line-height: 1.35; }
.contents .ct { flex: 1; text-decoration: underline; text-decoration-color: var(--line); text-underline-offset: 3px; }
.contents .cp { font-variant-numeric: tabular-nums; color: var(--accent); min-width: 2.2em; text-align: right; }

/* Reading */
.prose { ${phone ? '' : 'max-width: 33em; margin: 0 auto;'} overflow-wrap: break-word; hyphens: manual; }
.prose h2 { font-size: ${phone ? 22 : 23}px; line-height: 1.22; letter-spacing: -.01em; font-weight: 650; margin: 1.5em 0 .5em; padding-top: .5em; border-top: 1px solid var(--line); }
.prose h3 { font-size: ${phone ? 19 : 17.5}px; line-height: 1.3; font-weight: 650; margin: 1.3em 0 .4em; }
.prose h4 { font-size: ${phone ? 16 : 13}px; line-height: 1.3; font-weight: 650; letter-spacing: .03em; margin: 1.2em 0 .3em; color: var(--dim); }
.prose h2, .prose h3, .prose h4 { break-after: avoid; break-inside: avoid; }
.prose p, .prose ul, .prose ol, .prose blockquote { margin: 0 0 .9em; orphans: 2; widows: 2; }
.prose ul, .prose ol { padding-left: 1.25em; }
.prose li { margin: .3em 0; }
.prose blockquote { margin-left: 0; padding: .6em .9em; border-left: 3px solid var(--accent); background: var(--bg); }
.prose blockquote p:last-child { margin-bottom: 0; }
.prose hr { border: none; border-top: 1px solid var(--line); margin: 1.5em 0; }
.prose .keep-next { break-after: avoid; break-inside: avoid; }
.prose .table { margin: 0 0 1em; ${phone ? '' : `width: ${px(s.wide)}; margin-left: calc((100% - ${px(s.wide)}) / 2);`} }
.prose table { border-collapse: collapse; width: 100%; font-size: ${small}px; line-height: 1.4; }
.prose thead { display: table-header-group; }
.prose tr { break-inside: avoid; }
.prose th, .prose td { text-align: left; vertical-align: top; padding: 4px 10px 4px 0; border-bottom: 1px solid var(--line); }
.prose th { font-size: ${small - 1}px; font-weight: 650; color: var(--dim); border-bottom: 1.5px solid var(--dim); }

/* Figures */
.prose figure.fig { margin: 1.2em 0 1.4em; break-inside: avoid; }
.prose figure.fig.many, .prose figure.fig.long { break-inside: auto; }
.prose figure.fig.wide { width: ${px(s.wide)}; margin-left: calc((100% - ${px(s.wide)}) / 2); }
.prose figure .piece { break-inside: avoid; margin: 0 0 8px; }
/* The last picture keeps the caption's first lines with it. */
.prose figure > .piece:last-of-type, .prose figure > .side:last-of-type > .piece:last-child { break-after: avoid; }
.prose figure .side { margin: 0 0 6px; }
.prose figure .side + .side { margin-top: 10px; }
.prose figure .side-label, .prose figure .pic-label { font-size: ${small}px; font-weight: 650; margin: 0 0 4px; color: var(--ink); break-after: avoid; }
.prose figure .pic-label { font-weight: 500; color: var(--dim); }
.prose figure img { display: block; width: 100%; height: auto; margin: 0; }
.prose figure .crop { overflow: hidden; width: 100%; }
.prose figure .crop img { max-width: none; }
.prose figure figcaption { font-size: ${small}px; line-height: 1.5; background: var(--bg); border: 1px solid var(--line); padding: ${phone ? '8px 10px' : '8px 12px'}; }
.prose figure figcaption > p:first-child { break-inside: avoid; }
.prose figure.long figcaption > p:first-child { break-inside: auto; orphans: 3; widows: 2; }
.prose figure figcaption p { margin: 0 0 .5em; }
.prose figure figcaption p:last-child { margin-bottom: 0; }
.prose figure .fig-n { font-weight: 700; }
.prose figure figcaption .table { width: auto; margin: .6em 0 .2em; }
.prose .stack { font-size: ${small}px; line-height: 1.45; margin: .6em 0 .2em; }
.prose .stack ul { list-style: none; padding: 0; margin: 0; }
.prose .stack li { margin: 0; padding: 5px 0; border-top: 1px solid var(--line); break-inside: avoid; }
.prose .stack .t { font-weight: 600; margin: 0; }
.prose .stack .v { margin: 0; }
.prose .stack .k { color: var(--dim); }

/* Colophon */
.colophon { break-inside: avoid; margin-top: 2em; font-size: ${small}px; color: var(--dim); }
.colophon a { overflow-wrap: anywhere; }
`
}

// ---- command line -------------------------------------------------------------------------------

const arg = (name: string): string | undefined => {
  const i = process.argv.indexOf(name)
  return i < 0 ? undefined : process.argv[i + 1]
}

if (process.argv[1] !== undefined && fileURLToPath(import.meta.url) === process.argv[1]) {
  const slug = process.argv[2]
  const edition = arg('--edition') as Edition | undefined
  const assets = arg('--assets')
  const out = arg('--out')
  if (!slug || (edition !== 'phone' && edition !== 'large') || assets === undefined || out === undefined) {
    process.stderr.write('usage: node tools/pdf/print.ts <slug> --edition phone|large --assets assets.json [--pages pages.json] [--date words] [--pages-dir dir] --out file.html\n')
    process.exit(2)
  }
  const pagesFile = arg('--pages')
  const doc = printDoc(slug, {
    edition,
    assets: JSON.parse(readFileSync(assets, 'utf8')),
    ...(pagesFile === undefined ? {} : { pages: JSON.parse(readFileSync(pagesFile, 'utf8')) }),
    date: arg('--date') ?? new Date().toLocaleDateString('en-US', { dateStyle: 'long' }),
  }, arg('--pages-dir') ?? PAGES_DIR)
  writeFileSync(out, doc.html)
  process.stdout.write(JSON.stringify({ title: doc.title, short: doc.short, sections: doc.sections, headings: doc.headings, substitutions: doc.substitutions, dead: doc.dead, figures: doc.figures, compares: doc.compares }) + '\n')
}
