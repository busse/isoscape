/**
 * Content pages for the explorer: Markdown files in `pages/`, compiled into the page at
 * generation time so the explorer stays one self-contained file that opens from disk.
 *
 * A page is `pages/<slug>.md` with a little front matter:
 *
 *     ---
 *     title: How it's made
 *     order: 10
 *     summary: One line for the nav's tooltip.
 *     social: world-landmarks-social.jpg
 *     ---
 *
 * `social` names a 1200×630 PNG or JPEG beside the page for its link preview; without one, the
 * page's preview uses the site's flagship view. `unlisted: true` keeps a page out of the nav, the
 * footers, the front page's plain list and the sitemap (and asks search engines not to index its
 * static page), while it stays reachable at its address: for a page waiting to be reviewed.
 * `schema: FAQPage` gives the static page FAQPage structured data, read from its headings that
 * end in a question mark and the text under each. `slug` defaults to the file name, `order` to 100 (lower comes first in the nav). A page is
 * reached at `#/<slug>`, and a section of it at `#/<slug>/<heading-id>`.
 *
 * Links are written as they would be for GitHub, so the files read well there too: `#rapids`
 * is a section of this page, `about.md` or `about.md#data` another page. Both are rewritten to
 * explorer routes. Images (`![alt](diagram.svg)`) name files beside the page and are inlined
 * as data: URIs (or, with `images: link` in the front matter, linked as their copies in `p/`); anything that is not a plain file name in `pages/` is dropped to its alt text.
 * Raster images carry their width and height, so the page keeps its layout while they load and
 * a section link lands where it should.
 *
 * Numbered figures (`::: figure`, see markdown.ts) open in a lightbox (lightbox.ts). A figure's
 * picture opens its larger copy when one sits beside it as `<name>-large.<ext>`
 * (`jackson-ward-state-1952.webp` → `jackson-ward-state-1952-large.webp`); the explorer links it
 * in `p/`, where the static pages put it, so it is fetched only when opened. `deck: …` in the
 * front matter is a one-sentence standfirst, set under the page's title. `pdf: true` adds a line
 * under the deck and another at the end linking the page's two PDF editions (tools/pdf/story_pdf.py
 * makes them; they sit beside the static page as `p/<slug>-phone.pdf` and `p/<slug>-large.pdf`).
 */

import { readdirSync, readFileSync } from 'node:fs'
import { basename, extname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { inline, markdown, type Figure, type Heading } from './markdown.ts'
import { imageSize } from './social.ts'

export interface Page {
  readonly slug: string
  readonly title: string
  readonly order: number
  readonly summary?: string
  /** The source file, relative to the repo root, for an "edit this page" hint. */
  readonly file: string
  readonly html: string
  readonly headings: Heading[]
  /** Its numbered figures (`::: figure`), in order. */
  readonly figures: Figure[]
  /** The standfirst under the title (`deck:`), as text. */
  readonly deck?: string
  /** The link-preview image named by `social:`, with its bytes, read from beside the page. */
  readonly social?: { readonly name: string; readonly bytes: Buffer }
  /** Reachable at its address but listed nowhere (`unlisted: true`). */
  readonly unlisted?: boolean
  /** Shows no shop link or button while it is open (`shop: false`), as a story page asks. */
  readonly noShop?: boolean
  /** Structured data for the static page beyond `Article` (`schema: FAQPage`). */
  readonly schema?: 'FAQPage'
  /** Offers the page as PDFs (`pdf: true`): `<slug>-phone.pdf` and `<slug>-large.pdf` in `p/` (tools/pdf). */
  readonly pdf?: boolean
}

export const PAGES_DIR = fileURLToPath(new URL('../pages/', import.meta.url))

/** `---`-fenced `key: value` lines at the top of a file. Values may be quoted. */
export const frontMatter = (src: string): { data: Record<string, string>; body: string } => {
  const text = src.replace(/^﻿/, '').replace(/\r\n?/g, '\n')
  const m = text.match(/^---\n([\s\S]*?)\n---[ \t]*(?:\n|$)/)
  if (m === null) return { data: {}, body: text }
  const data: Record<string, string> = {}
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^\s*([A-Za-z][\w-]*)\s*:\s*(.*?)\s*$/)
    if (kv === null) continue
    let v = kv[2]
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1)
    data[kv[1]] = v
  }
  return { data, body: text.slice(m[0].length) }
}

const SLUG = /^[a-z0-9][a-z0-9-]*$/

const MIME: Readonly<Record<string, string>> = { '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' }

/** Turn a link as written for GitHub into an explorer route. */
export const pageLink = (slug: string, href: string, siteUrl?: string): string => {
  // A link to a map on the public site (written so it also works on GitHub) stays in the explorer.
  if (siteUrl !== undefined && href.startsWith(siteUrl + '#')) return href.slice(siteUrl.length)
  if (href.startsWith('#/')) return href
  if (href.startsWith('#')) return href.length > 1 ? `#/${slug}/${href.slice(1)}` : `#/${slug}`
  const md = href.match(/^(?:\.\/)?([a-z0-9][a-z0-9-]*)\.md(?:#(.*))?$/)
  if (md) return `#/${md[1]}${md[2] ? '/' + md[2] : ''}`
  return href
}

/**
 * How a page is compiled for somewhere other than the explorer. The static pages
 * (static-pages.ts) keep GitHub's heading ids, turn explorer routes into links between files,
 * and link images as files beside the page instead of inlining them.
 */
export interface CompileMode {
  /** Prefix for heading ids in the HTML (default `p-<slug>-`, the explorer's). */
  readonly idPrefix?: string
  /** Rewrite a link once it is an explorer route (or left as written), given this page's slug. */
  readonly route?: (href: string, slug: string) => string
  /** Link an image file beside the page by this href instead of inlining it (called only for files that exist). */
  readonly imageHref?: (name: string) => string
  /** The href of a file beside the page that is linked, never inlined (a figure's larger copy): by default `p/<name>`, where the static pages put it. */
  readonly fileHref?: (name: string) => string
  /** The href of one of the page's PDFs (`pdf: true`), by file name: by default `p/<name>`; null leaves the line out (the PDF's own print build). */
  readonly pdfHref?: ((name: string) => string) | null
}

/** The line a page with `pdf: true` shows near its top and at its end, linking its two PDFs. */
export const pdfLine = (slug: string, href: (name: string) => string): string =>
  `<p class="pdf-links" style="font-size: .88em; color: var(--dim)">Read this as a PDF: <a href="${href(`${slug}-phone.pdf`)}" type="application/pdf">phone edition</a>, <a href="${href(`${slug}-large.pdf`)}" type="application/pdf">large-screen edition</a></p>`

/**
 * Compile one page. `readAsset` returns the bytes of a file beside the page, or null; it is
 * only ever asked for plain file names with a known image extension.
 */
export const compilePage = (src: string, fileName: string, readAsset: (name: string) => Buffer | null = () => null, siteUrl?: string, mode: CompileMode = {}): Page => {
  const { data, body } = frontMatter(src)
  const slug = data.slug ?? basename(fileName, extname(fileName))
  if (!SLUG.test(slug)) throw new Error(`pages/${fileName}: slug "${slug}" must be lower-case letters, digits and hyphens`)
  const order = data.order === undefined ? 100 : Number(data.order)
  const result = markdown(body, {
    idPrefix: mode.idPrefix ?? `p-${slug}-`,
    link: (href) => (mode.route === undefined ? pageLink(slug, href, siteUrl) : mode.route(pageLink(slug, href, siteUrl), slug)),
    image: (src) => {
      const name = src.replace(/^\.\//, '')
      const ext = extname(name)
      const mime = MIME[ext.toLowerCase()]
      if (mime === undefined || !/^[\w.-]+$/.test(name) || name.startsWith('.')) return /^https?:/i.test(src) ? src : null
      const bytes = readAsset(name)
      if (bytes === null) return null
      const size = imageSize(bytes)
      const large = name.slice(0, -ext.length) + '-large' + ext
      const hasLarge = readAsset(large) !== null
      const linked = (n: string) => (mode.imageHref !== undefined ? mode.imageHref(n) : mode.fileHref !== undefined ? mode.fileHref(n) : `p/${n}`)
      return {
        // `images: link` in the front matter links the explorer's copy in p/ (as the larger copy
        // is linked) instead of inlining it, so a picture-heavy page stays out of index.html.
        src: mode.imageHref !== undefined ? mode.imageHref(name) : data.images === 'link' ? linked(name) : `data:${mime};base64,${bytes.toString('base64')}`,
        ...(size === undefined ? {} : size),
        full: linked(hasLarge ? large : name),
      }
    },
  })
  const first = result.headings.find((h) => h.level === 1)
  // The deck sits straight under the first heading (or at the top, without one).
  let html = result.html
  if (data.deck) {
    const deck = `<p class="deck">${inline(data.deck, { link: (href) => (mode.route === undefined ? pageLink(slug, href, siteUrl) : mode.route(pageLink(slug, href, siteUrl), slug)) })}</p>`
    const end = html.indexOf('</h1>')
    html = end === -1 ? deck + '\n' + html : html.slice(0, end + 5) + '\n' + deck + html.slice(end + 5)
  }
  // `pdf: true`: a line linking the page's PDFs, under the deck (or the title) and at the end.
  if (data.pdf === 'true' && mode.pdfHref !== null) {
    const line = pdfLine(slug, mode.pdfHref ?? ((n) => `p/${n}`))
    const deckEnd = html.indexOf('<p class="deck">') === -1 ? -1 : html.indexOf('</p>', html.indexOf('<p class="deck">')) + 4
    const at = deckEnd > 3 ? deckEnd : html.indexOf('</h1>') === -1 ? 0 : html.indexOf('</h1>') + 5
    html = html.slice(0, at) + (at > 0 ? '\n' : '') + line + (at > 0 ? '' : '\n') + html.slice(at) + '\n' + line + '\n'
  }
  let social: Page['social']
  if (data.social) {
    const name = data.social.replace(/^\.\//, '')
    if (!/^[\w.-]+\.(png|jpe?g)$/i.test(name) || name.startsWith('.')) throw new Error(`pages/${fileName}: social "${data.social}" must be a PNG or JPEG file name beside the page`)
    const bytes = readAsset(name)
    if (bytes === null) throw new Error(`pages/${fileName}: social image "${name}" not found beside the page`)
    social = { name, bytes }
  }
  if (data.schema !== undefined && data.schema !== 'FAQPage') throw new Error(`pages/${fileName}: schema "${data.schema}" is not one isoscape writes (FAQPage)`)
  return {
    slug,
    title: data.title ?? first?.text ?? slug,
    order: Number.isFinite(order) ? order : 100,
    ...(data.summary ? { summary: data.summary } : {}),
    file: `pages/${fileName}`,
    html,
    headings: result.headings,
    figures: result.figures,
    ...(data.deck ? { deck: data.deck } : {}),
    ...(social === undefined ? {} : { social }),
    ...(data.unlisted === 'true' ? { unlisted: true } : {}),
    ...(data.shop === 'false' ? { noShop: true } : {}),
    ...(data.schema === 'FAQPage' ? { schema: 'FAQPage' as const } : {}),
    ...(data.pdf === 'true' ? { pdf: true } : {}),
  }
}

/** Every `*.md` in the pages folder, in nav order. A missing folder is no pages. */
export const loadPages = (dir: string = PAGES_DIR, siteUrl?: string, mode: CompileMode = {}): Page[] => {
  let files: string[]
  try {
    files = readdirSync(dir).filter((f) => f.endsWith('.md') && !f.startsWith('_') && f.toLowerCase() !== 'readme.md')
  } catch {
    return []
  }
  const pages = files.map((f) =>
    compilePage(readFileSync(join(dir, f), 'utf8'), f, (name) => {
      try {
        return readFileSync(join(dir, name))
      } catch {
        return null
      }
    }, siteUrl, mode),
  )
  const seen = new Set<string>()
  for (const p of pages) {
    if (seen.has(p.slug)) throw new Error(`two pages share the slug "${p.slug}"`)
    seen.add(p.slug)
  }
  return pages.sort((a, b) => a.order - b.order || a.title.localeCompare(b.title))
}
