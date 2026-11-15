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
 * page's preview uses the site's flagship view. `slug` defaults to the file name, `order` to 100 (lower comes first in the nav). A page is
 * reached at `#/<slug>`, and a section of it at `#/<slug>/<heading-id>`.
 *
 * Links are written as they would be for GitHub, so the files read well there too: `#rapids`
 * is a section of this page, `about.md` or `about.md#data` another page. Both are rewritten to
 * explorer routes. Images (`![alt](diagram.svg)`) name files beside the page and are inlined
 * as data: URIs; anything that is not a plain file name in `pages/` is dropped to its alt text.
 */

import { readdirSync, readFileSync } from 'node:fs'
import { basename, extname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { markdown, type Heading } from './markdown.ts'

export interface Page {
  readonly slug: string
  readonly title: string
  readonly order: number
  readonly summary?: string
  /** The source file, relative to the repo root, for an "edit this page" hint. */
  readonly file: string
  readonly html: string
  readonly headings: Heading[]
  /** The link-preview image named by `social:`, with its bytes, read from beside the page. */
  readonly social?: { readonly name: string; readonly bytes: Buffer }
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
 * Compile one page. `readAsset` returns the bytes of a file beside the page, or null; it is
 * only ever asked for plain file names with a known image extension.
 */
export const compilePage = (src: string, fileName: string, readAsset: (name: string) => Buffer | null = () => null, siteUrl?: string): Page => {
  const { data, body } = frontMatter(src)
  const slug = data.slug ?? basename(fileName, extname(fileName))
  if (!SLUG.test(slug)) throw new Error(`pages/${fileName}: slug "${slug}" must be lower-case letters, digits and hyphens`)
  const order = data.order === undefined ? 100 : Number(data.order)
  const result = markdown(body, {
    idPrefix: `p-${slug}-`,
    link: (href) => pageLink(slug, href, siteUrl),
    image: (src) => {
      const name = src.replace(/^\.\//, '')
      const mime = MIME[extname(name).toLowerCase()]
      if (mime === undefined || !/^[\w.-]+$/.test(name) || name.startsWith('.')) return /^https?:/i.test(src) ? src : null
      const bytes = readAsset(name)
      return bytes === null ? null : `data:${mime};base64,${bytes.toString('base64')}`
    },
  })
  const first = result.headings.find((h) => h.level === 1)
  let social: Page['social']
  if (data.social) {
    const name = data.social.replace(/^\.\//, '')
    if (!/^[\w.-]+\.(png|jpe?g)$/i.test(name) || name.startsWith('.')) throw new Error(`pages/${fileName}: social "${data.social}" must be a PNG or JPEG file name beside the page`)
    const bytes = readAsset(name)
    if (bytes === null) throw new Error(`pages/${fileName}: social image "${name}" not found beside the page`)
    social = { name, bytes }
  }
  return {
    slug,
    title: data.title ?? first?.text ?? slug,
    order: Number.isFinite(order) ? order : 100,
    ...(data.summary ? { summary: data.summary } : {}),
    file: `pages/${fileName}`,
    html: result.html,
    headings: result.headings,
    ...(social === undefined ? {} : { social }),
  }
}

/** Every `*.md` in the pages folder, in nav order. A missing folder is no pages. */
export const loadPages = (dir: string = PAGES_DIR, siteUrl?: string): Page[] => {
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
    }, siteUrl),
  )
  const seen = new Set<string>()
  for (const p of pages) {
    if (seen.has(p.slug)) throw new Error(`two pages share the slug "${p.slug}"`)
    seen.add(p.slug)
  }
  return pages.sort((a, b) => a.order - b.order || a.title.localeCompare(b.title))
}
