/**
 * Link previews. Social crawlers (Slack, iMessage, X, Facebook, LinkedIn, Discord…) run no
 * script and ignore the URL fragment, so every explorer route (`index.html#<id>@…`) would
 * preview as the bare index page. So each build, and each content page, also gets a tiny
 * static share page, `out/s/<id>.html` / `out/s/page-<slug>.html`, carrying its own Open Graph
 * and Twitter card tags, and a script that sends a visitor on to the explorer, keeping any
 * fragment they arrived with: `s/<id>.html#<id>@cx,cy,z` opens that exact view.
 *
 * Each map also gets a share page that outlives its builds, `out/s/<name>.html`, named as its
 * static page `m/<name>.html` is, and sending a visitor to its lasting route (`#<region>` or
 * `#<region>:<year>`): the explorer's Link button hands these out, and its address bar shows
 * them. Share pages of builds that are gone are rewritten to their region's card, so links
 * already shared keep a preview whose image exists.
 *
 * Each build gets a 1200×630 preview image, `out/builds/<id>/social.png`: the picture cropped
 * (not letterboxed) to 1.91:1 around its center, rasterized with rsvg-convert, else headless
 * Chrome. Without either, the thumbnail stands in. Previews use `social.jpg`, the same picture
 * as a JPEG (a quarter of the bytes; some apps drop images near 1 MB), made with ImageMagick or
 * Python's Pillow where either is installed.
 *
 * Open Graph wants absolute URLs. The site's public address comes from `--site-url`, else
 * `ISOSCAPE_SITE_URL`, else `siteUrl` in `isoscape.config.json`; without one, URLs are
 * relative (which some clients accept, and which work once deployed under the same path).
 */

import { execFile } from 'node:child_process'
import { access, mkdir, open, readdir, readFile, rm, stat, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { extname, join, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { promisify } from 'node:util'
import type { BuildMeta } from './archive.ts'
import type { Page } from './pages.ts'

const run = promisify(execFile)

export const SOCIAL_W = 1200
export const SOCIAL_H = 630
export const SITE_NAME = 'isoscape'

// ---- configuration ------------------------------------------------------------------------------

export interface SiteConfig {
  /** The public address of the `out/` directory, ending in '/'. */
  readonly siteUrl?: string
  /** Region name or build id whose newest build is the site's preview image. */
  readonly flagship?: string
  /**
   * Optional shop for prints: a link to its front page in the header (always), plus a link to buy
   * on each map, section, set or page that is in `onSale` (see `onSaleUrl`), and nowhere else.
   * A key `<region>:<year>` (the explorer's route for a year) puts it on that year's view only.
   * `cta` is the header's wording while anything is on sale. `products` puts each piece's own
   * print beside the links to its view in the content pages (see `printLinks`). An `onSale` value
   * may be a list instead of a URL, when more than one print is made from the same view: its first
   * entry is the view's own buy link, the rest are shown beside it (`prints`, see `shopFor`).
   */
  readonly shop?: { readonly label: string; readonly url: string; readonly cta?: string; readonly onSale?: OnSale; readonly prints?: Prints; readonly products?: Products }
  /** Optional front page for the explorer: featured views, then the rest in sections. */
  readonly home?: HomeConfig
  /** False on a published site that does not carry out/<region>.html, to hide the "Latest page" link. */
  readonly latestPages?: boolean
  /** Optional visitor analytics for the published explorer: a Google Analytics measurement ID ("G-…"). Off when absent. */
  readonly analytics?: { readonly ga: string }
}

/** A featured view on the explorer's front page: the newest build of `region` (or its `year`, in a dated series). */
export interface HomeHero {
  readonly region: string
  readonly year?: number
  readonly title: string
  readonly blurb?: string
  /** The shop button's text for this view (default "Buy a print ↗"), shown while its region is in the shop's `onSale`. */
  readonly shopLabel?: string
  /** A page that is this view's front door ('#/<slug>', a series page: through-time.ts): the card's picture, years and button go there instead of the viewer. */
  readonly page?: string
  /** The card's button text when `page` is set (default "Step through the years"). */
  readonly pageLabel?: string
}

/** A group of regions, by name prefix, in the build list and on the front page. */
export interface HomeSection {
  readonly title: string
  readonly prefixes: readonly string[]
  /** Heading on the front page, if it differs from `title`. */
  readonly homeTitle?: string
  readonly blurb?: string
  /** Region names to show first on the front page, in this order; the rest follow by title. */
  readonly order?: readonly string[]
  /** Start folded in the build list. */
  readonly collapsed?: boolean
  /** The shop button's text (default "Buy prints ↗"), shown while the section is on sale (see `sectionShop`). */
  readonly shopLabel?: string
  /** A page that tells the section's story ('#/<slug>'), linked beside the shop button. */
  readonly page?: string
  readonly pageLabel?: string
}

export interface HomeConfig {
  readonly title: string
  readonly intro?: string
  readonly heroes: readonly HomeHero[]
  readonly sections: readonly HomeSection[]
  /** Story pages shown as cards under the featured views: a heading, an optional line, and page slugs in order. */
  readonly stories?: { readonly title: string; readonly blurb?: string; readonly pages: readonly string[] }
  /** Links under the sections: label and href (a page as '#/<slug>', or a URL). */
  readonly links?: readonly { readonly label: string; readonly href: string }[]
}

/** A site URL as given, made to end in '/'; undefined when empty. Throws if not http(s). */
export const normaliseSiteUrl = (raw: string | undefined): string | undefined => {
  const s = raw?.trim()
  if (s === undefined || s === '') return undefined
  let u: URL
  try {
    u = new URL(s)
  } catch {
    throw new Error(`site URL "${s}" is not a URL; give it as https://example.org/isoscape/`)
  }
  if (u.protocol !== 'https:' && u.protocol !== 'http:') throw new Error(`site URL "${s}" must be http(s)`)
  u.hash = ''
  u.search = ''
  return u.href.endsWith('/') ? u.href : `${u.href}/`
}

/** What is for sale: region prefix, set slug or page slug → the product or collection URL. */
export type OnSale = Readonly<Record<string, string>>

/**
 * The `onSale` keys whose value in the file is a list: key → every print made from that view, the
 * first being the one `onSale` keeps (its label, when given, replaces "Buy a print ↗"), the rest
 * shown beside it. Each entry is a URL or `{ "url", "label" }`; past the first, a label is needed.
 */
export type Prints = Readonly<Record<string, readonly { readonly url: string; readonly label?: string }[]>>

/** One piece's print in the shop: its product page, the link's words, and the store's design key. */
export interface Product {
  readonly url: string
  readonly label: string
  readonly design?: string
}

/**
 * The pieces on sale, by the explorer view each is cut from (`<region>:<year>@<x>,<y>,<zoom>`, or
 * a whole map's `<region>:<year>`), as the store's catalog names it (`explore`): a set's places
 * and stops, its map alone and its framed map. Written by tools/release/products.py from the
 * store's catalog and the board's `on_sale`, never by hand.
 */
export type Products = Readonly<Record<string, readonly Product[]>>

const isShop = (v: unknown): v is NonNullable<SiteConfig['shop']> =>
  typeof v === 'object' && v !== null && typeof (v as { label?: unknown }).label === 'string' && typeof (v as { url?: unknown }).url === 'string'

/**
 * The shop as the site uses it: label, url, cta and `onSale` (only string URLs kept, a list
 * reduced to its first URL, the whole list kept in `prints`). Anything else (an old `links` map)
 * is dropped, so no URL but these reaches a page.
 */
const shopOf = (v: NonNullable<SiteConfig['shop']>): NonNullable<SiteConfig['shop']> => {
  const raw = (v as { onSale?: unknown }).onSale
  const onSale: Record<string, string> = {}
  const prints: Record<string, { url: string; label?: string }[]> = {}
  const isUrl = (x: unknown): x is string => typeof x === 'string' && /^https?:\/\//.test(x)
  if (typeof raw === 'object' && raw !== null && !Array.isArray(raw)) {
    for (const [key, val] of Object.entries(raw)) {
      if (key === '') continue
      if (typeof val === 'string') { if (val !== '') onSale[key] = val; continue }
      if (!Array.isArray(val)) continue
      const list = val.flatMap((x, i): { url: string; label?: string }[] => {
        if (isUrl(x)) return i === 0 ? [{ url: x }] : []
        if (typeof x !== 'object' || x === null || !isUrl((x as { url?: unknown }).url)) return []
        const label = (x as { label?: unknown }).label
        if (typeof label === 'string' && label !== '') return [{ url: (x as { url: string }).url, label }]
        return i === 0 ? [{ url: (x as { url: string }).url }] : []
      })
      if (list.length === 0 || list[0].url !== (isUrl(val[0]) ? val[0] : (val[0] as { url?: unknown } | null)?.url)) continue
      onSale[key] = list[0].url
      if (list.length > 1 || list[0].label !== undefined) prints[key] = list
    }
  }
  const rawProducts = (v as { products?: unknown }).products
  const products: Record<string, Product[]> = {}
  if (typeof rawProducts === 'object' && rawProducts !== null && !Array.isArray(rawProducts)) {
    for (const [view, list] of Object.entries(rawProducts)) {
      const ok = (Array.isArray(list) ? list : [list]).filter((x): x is Product =>
        typeof x === 'object' && x !== null && typeof x.url === 'string' && /^https?:\/\//.test(x.url) && typeof x.label === 'string' && x.label !== '')
        .map((x) => ({ url: x.url, label: x.label, ...(typeof x.design === 'string' ? { design: x.design } : {}) }))
      if (view !== '' && ok.length > 0) products[view] = ok
    }
  }
  return { label: v.label, url: v.url, ...(typeof v.cta === 'string' && v.cta !== '' ? { cta: v.cta } : {}), onSale, ...(Object.keys(prints).length > 0 ? { prints } : {}), ...(Object.keys(products).length > 0 ? { products } : {}) }
}

/** A front page without per-view or per-section shop URLs: where to buy comes from `shop.onSale` only. */
const homeOf = (h: HomeConfig): HomeConfig => {
  const strip = <T extends object>(x: T): T => Object.fromEntries(Object.entries(x).filter(([k]) => k !== 'shop')) as T
  return { ...h, heroes: h.heroes.map(strip), sections: h.sections.map(strip) }
}

const isHome = (v: unknown): v is HomeConfig => {
  if (typeof v !== 'object' || v === null) return false
  const h = v as { title?: unknown; heroes?: unknown; sections?: unknown }
  return typeof h.title === 'string' && Array.isArray(h.heroes) && Array.isArray(h.sections) &&
    h.heroes.every((x) => typeof x === 'object' && x !== null && typeof (x as HomeHero).region === 'string' && typeof (x as HomeHero).title === 'string') &&
    h.sections.every((x) => typeof x === 'object' && x !== null && typeof (x as HomeSection).title === 'string' && Array.isArray((x as HomeSection).prefixes))
}

/** `--site-url`, else ISOSCAPE_SITE_URL, else isoscape.config.json in `root`. */
export const loadSiteConfig = async (flag?: string, root = process.cwd(), env = process.env): Promise<SiteConfig> => {
  let file: { siteUrl?: unknown; flagship?: unknown; shop?: unknown; home?: unknown; latestPages?: unknown; analytics?: unknown } = {}
  try {
    file = JSON.parse(await readFile(resolve(root, 'isoscape.config.json'), 'utf8')) as typeof file
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code !== 'ENOENT') throw new Error(`isoscape.config.json: ${(err as Error).message}`)
  }
  const raw = flag ?? env.ISOSCAPE_SITE_URL ?? (typeof file.siteUrl === 'string' ? file.siteUrl : undefined)
  const siteUrl = normaliseSiteUrl(raw)
  return {
    ...(siteUrl === undefined ? {} : { siteUrl }),
    ...(typeof file.flagship === 'string' && file.flagship !== '' ? { flagship: file.flagship } : {}),
    ...(isShop(file.shop) ? { shop: shopOf(file.shop) } : {}),
    ...(isHome(file.home) ? { home: homeOf(file.home) } : {}),
    ...(file.latestPages === false ? { latestPages: false } : {}),
    ...(isAnalytics(file.analytics) ? { analytics: { ga: file.analytics.ga } } : {}),
  }
}

/** Only a well-formed measurement ID is ever written into the page. */
const isAnalytics = (v: unknown): v is { ga: string } =>
  typeof v === 'object' && v !== null && typeof (v as { ga?: unknown }).ga === 'string' && /^G-[A-Z0-9]{6,16}$/.test((v as { ga: string }).ga)

// ---- URLs and tags ------------------------------------------------------------------------------

/**
 * A URL for `path` (relative to out/): absolute under `base` when there is one, else relative
 * to a page `depth` directories below out/ (index.html is 0, s/*.html is 1).
 */
export const siteHref = (path: string, base?: string, depth = 0): string => {
  const p = path.replace(/^\/+/, '')
  if (base !== undefined) return new URL(p, base.endsWith('/') ? base : `${base}/`).href
  return '../'.repeat(depth) + p
}

export const escAttr = (s: string): string =>
  s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c)

export interface Card {
  readonly title: string
  readonly description: string
  /** og:image, already resolved (absolute or relative). */
  readonly image?: string
  readonly imageWidth?: number
  readonly imageHeight?: number
  readonly imageAlt?: string
  /** og:url and the canonical link; only when absolute. */
  readonly url?: string
  /** The canonical link, when it is not `url`: a share page names the static page it stands for. */
  readonly canonical?: string
  readonly type?: 'website' | 'article'
}

/** The head tags for a card: description, canonical, Open Graph and Twitter. */
export const metaTags = (c: Card): string => {
  const m = (attr: 'name' | 'property', key: string, value: string | number | undefined) =>
    value === undefined || value === '' ? '' : `<meta ${attr}="${key}" content="${escAttr(String(value))}">\n`
  return (
    m('name', 'description', c.description) +
    ((c.canonical ?? c.url) === undefined ? '' : `<link rel="canonical" href="${escAttr(c.canonical ?? c.url ?? '')}">\n`) +
    m('property', 'og:site_name', SITE_NAME) +
    m('property', 'og:type', c.type ?? 'website') +
    m('property', 'og:title', c.title) +
    m('property', 'og:description', c.description) +
    m('property', 'og:url', c.url) +
    m('property', 'og:image', c.image) +
    (c.image?.startsWith('https:') ? m('property', 'og:image:secure_url', c.image) : '') +
    m('property', 'og:image:type', c.image === undefined ? undefined : c.image.endsWith('.jpg') ? 'image/jpeg' : 'image/png') +
    m('property', 'og:image:width', c.imageWidth) +
    m('property', 'og:image:height', c.imageHeight) +
    m('property', 'og:image:alt', c.imageAlt) +
    m('name', 'twitter:card', c.image === undefined ? 'summary' : 'summary_large_image') +
    m('name', 'twitter:title', c.title) +
    m('name', 'twitter:description', c.description) +
    m('name', 'twitter:image', c.image) +
    m('name', 'twitter:image:alt', c.imageAlt)
  )
}

/** Cut text at a word boundary to at most `max` characters, with an ellipsis if cut. */
export const clip = (s: string, max = 220): string => {
  const t = s.replace(/\s+/g, ' ').trim()
  if (t.length <= max) return t
  const cut = t.slice(0, max - 1)
  const sp = cut.lastIndexOf(' ')
  return `${(sp > max * 0.6 ? cut.slice(0, sp) : cut).replace(/[\s,;:.—–-]+$/, '')}…`
}

const int = (n: number) => Math.round(n).toLocaleString('en-US')
const plural = (n: number, one: string, many = `${one}s`) => `${int(n)} ${n === 1 ? one : many}`

/** One line of what a build holds, from its measures. */
export const statsLine = (b: BuildMeta): string => {
  const s = b.stats ?? {}
  const parts: string[] = []
  const num = (k: string) => (typeof s[k] === 'number' && Number.isFinite(s[k]) ? s[k] : undefined)
  const buildings = num('buildings')
  if (buildings !== undefined) parts.push(b.time ? `${plural(buildings, 'building')} standing by ${b.time.year}` : plural(buildings, 'building'))
  const lo = num('elevationDatum')
  const hi = num('elevationTop')
  if (lo !== undefined && hi !== undefined && hi > lo) parts.push(`ground rising from ${Math.round(lo)} to ${Math.round(hi)} m`)
  const what = b.palette === 'night' ? 'An isometric night view' : 'An isometric view'
  return `${what}${parts.length ? ` of ${parts.length > 1 ? `${parts.slice(0, -1).join(', ')} and ${parts[parts.length - 1]}` : parts[0]}` : ''}, drawn from OpenStreetMap and public elevation data.`
}

/** Title and description for a build's preview. */
export const buildCard = (b: BuildMeta): { title: string; description: string; alt: string } => {
  const place = b.title || b.config?.title || b.region
  const t = b.time
  const title = `${place}${t?.title ? `: ${t.title}` : ''} · ${SITE_NAME}`
  // A build's own note says what was being tried, which is for the explorer, not a preview.
  const lead = t ? [t.title ? `${t.year}: ${t.title}.` : `As it stood in ${t.year}.`, t.note ?? ''].join(' ') : ''
  const tail = statsLine(b)
  const description = lead.trim() === '' ? tail : `${clip(lead, 300 - tail.length - 1)} ${tail}`
  return { title, description: clip(description, 300), alt: `Isometric drawing: ${place}` }
}

/** What isoscape makes, in a sentence: the site's description, and any page's that has none of its own. */
export const SITE_DESCRIPTION = 'Isometric dot-and-line drawings of real places, built from OpenStreetMap and public elevation data.'

/** A content page's description: its summary, else its first paragraph, else the site's. */
export const pageDescription = (p: Pick<Page, 'summary' | 'html'>): string =>
  clip(p.summary || firstParagraph(p.html) || SITE_DESCRIPTION, 300)

/** The text of a page's first paragraph, for its description when it has no summary. */
export const firstParagraph = (html: string): string => {
  const m = html.match(/<p>([\s\S]*?)<\/p>/)
  if (m === null) return ''
  return m[1].replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'")
}

// ---- share pages --------------------------------------------------------------------------------

/**
 * A share page: the card's tags, then a redirect to the explorer at `route` (a fragment
 * starting with '#'), or at whatever fragment the visitor arrived with. A plain link for anyone
 * without script. No meta refresh: some crawlers (Facebook's) follow one, and would take the
 * index page's card instead of this one.
 */
export const sharePage = (card: Card, route: string, more?: { readonly href: string; readonly label: string }, buy?: { readonly href: string; readonly label: string }): string => {
  const target = `../index.html${route}`
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escAttr(card.title)}</title>
${metaTags(card)}<script>location.replace('../index.html' + (location.hash.length > 1 ? location.hash : ${JSON.stringify(route).replace(/</g, '\\u003c')}))</script>
<style>body{font:15px/1.5 system-ui,sans-serif;max-width:640px;margin:10vh auto;padding:0 20px;color:#26252b;background:#f4f2ed}img{max-width:100%;border-radius:6px}a{color:#2f6f8f}</style>
</head>
<body>
<p><a href="${escAttr(target)}">${escAttr(card.title)}</a></p>
${card.image === undefined ? '' : `<p><a href="${escAttr(target)}"><img src="${escAttr(card.image)}" alt="${escAttr(card.imageAlt ?? '')}"></a></p>\n`}<p>${escAttr(card.description)}</p>
${more === undefined ? '' : `<p><a href="${escAttr(more.href)}">${escAttr(more.label)}</a></p>\n`}${buy === undefined ? '' : `<p><a href="${escAttr(buy.href)}">${escAttr(buy.label)}</a></p>\n`}</body>
</html>
`
}

/** The share page's file name (in out/s/) for a build or a content page. */
export const shareFile = (target: { build: string } | { page: string }): string =>
  'build' in target ? `${target.build}.html` : `page-${target.page}.html`

// ---- preview images -----------------------------------------------------------------------------

/**
 * The part of a viewBox shown at 1200×630: the full height or width, whichever fits, cut to
 * 1.91:1 around the center. Cutting height, the sky above goes before the ground below. A
 * picture with a caption in its top-left corner (a dated build's year) is cut from the right
 * and the bottom instead, so the caption stays whole.
 */
export const socialCrop = (vb: readonly number[], captioned = false, w = SOCIAL_W, h = SOCIAL_H): [number, number, number, number] => {
  const [x, y, vw, vh] = vb
  const aspect = w / h
  if (vw / vh >= aspect) {
    const nw = vh * aspect
    return [captioned ? x : x + (vw - nw) / 2, y, nw, vh]
  }
  const nh = vw / aspect
  return [x, captioned ? y : y + (vh - nh) * 0.6, vw, nh]
}

/** The root <svg> tag of `svg` given a new viewBox and a fixed pixel size. */
export const reframeSvg = (svg: string, vb: readonly number[], w = SOCIAL_W, h = SOCIAL_H): string => {
  const m = svg.match(/<svg\b[^>]*>/)
  if (m === null || m.index === undefined) throw new Error('no <svg> element')
  const attrs = m[0]
    .replace(/\s(?:viewBox|width|height|preserveAspectRatio)\s*=\s*("[^"]*"|'[^']*')/g, '')
    .replace(/^<svg\b/, `<svg viewBox="${vb.map((n) => +n.toFixed(2)).join(' ')}" width="${w}" height="${h}" preserveAspectRatio="xMidYMid slice"`)
  return svg.slice(0, m.index) + attrs + svg.slice(m.index + m[0].length)
}

export const CHROMES = [
  process.env.CHROME,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  'google-chrome',
  'chromium',
  'chromium-browser',
].filter((c): c is string => typeof c === 'string' && c.length > 0)

type Rasteriser = { kind: 'rsvg' } | { kind: 'chrome'; bin: string } | null
let found: Promise<Rasteriser> | undefined

/** What is installed to rasterize SVG: rsvg-convert, else a headless Chrome, else nothing. */
export const findRasteriser = (): Promise<Rasteriser> =>
  (found ??= (async () => {
    try {
      await run('rsvg-convert', ['--version'], { timeout: 10_000 })
      return { kind: 'rsvg' } as const
    } catch {
      // try Chrome
    }
    for (const bin of CHROMES) {
      try {
        await run(bin, ['--version'], { timeout: 20_000 })
        return { kind: 'chrome', bin } as const
      } catch {
        // next
      }
    }
    return null
  })())

/** Render `svgPath` to a 1200×630 PNG at `pngPath`. False when nothing could rasterize it. */
export const renderSocial = async (svgPath: string, pngPath: string, viewBox: readonly number[]): Promise<boolean> => {
  const r = await findRasteriser()
  if (r === null) return false
  const tmp = join(tmpdir(), `isoscape-social-${process.pid}-${Date.now()}.svg`)
  try {
    const svg = await readFile(svgPath, 'utf8')
    await writeFile(tmp, reframeSvg(svg, socialCrop(viewBox, /<g\b[^>]*\bclass="caption"/.test(svg))))
    if (r.kind === 'rsvg') {
      await run('rsvg-convert', ['-w', String(SOCIAL_W), '-h', String(SOCIAL_H), '-o', pngPath, tmp], { timeout: 180_000 })
    } else {
      await run(
        r.bin,
        ['--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
          `--window-size=${SOCIAL_W},${SOCIAL_H}`, `--screenshot=${pngPath}`, pathToFileURL(tmp).href],
        { timeout: 180_000 },
      )
    }
    await access(pngPath)
    return true
  } catch {
    return false
  } finally {
    await rm(tmp, { force: true }).catch(() => undefined)
  }
}

/** Width and height of a PNG, JPEG or WebP held in memory; undefined if it is none of them. */
export const imageSize = (buf: Buffer): { width: number; height: number } | undefined => {
  if (buf.length >= 24 && buf.readUInt32BE(0) === 0x89504e47) return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) }
  // WebP: a RIFF file whose first chunk is VP8X (extended), VP8L (lossless) or VP8 (lossy).
  if (buf.length >= 30 && buf.toString('ascii', 0, 4) === 'RIFF' && buf.toString('ascii', 8, 12) === 'WEBP') {
    const chunk = buf.toString('ascii', 12, 16)
    if (chunk === 'VP8X') return { width: 1 + buf.readUIntLE(24, 3), height: 1 + buf.readUIntLE(27, 3) }
    if (chunk === 'VP8L') { const b = buf.readUInt32LE(21); return { width: 1 + (b & 0x3fff), height: 1 + ((b >> 14) & 0x3fff) } }
    if (chunk === 'VP8 ') return { width: buf.readUInt16LE(26) & 0x3fff, height: buf.readUInt16LE(28) & 0x3fff }
    return undefined
  }
  if (buf.length < 4 || buf[0] !== 0xff || buf[1] !== 0xd8) return undefined
  // JPEG: walk the segments to the first start-of-frame marker (C0–CF, except C4, C8 and CC).
  for (let i = 2; i + 9 < buf.length; ) {
    if (buf[i] !== 0xff) { i++; continue }
    const marker = buf[i + 1]
    if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) return { width: buf.readUInt16BE(i + 7), height: buf.readUInt16BE(i + 5) }
    if (marker === 0xd8 || (marker >= 0xd0 && marker <= 0xd7) || marker === 0x01) { i += 2; continue }
    i += 2 + buf.readUInt16BE(i + 2)
  }
  return undefined
}

/** Width and height of a PNG, from its header; undefined if it is not one. */
export const pngSize = async (path: string): Promise<{ width: number; height: number } | undefined> => {
  try {
    const fh = await open(path, 'r')
    try {
      const buf = Buffer.alloc(24)
      await fh.read(buf, 0, 24, 0)
      if (buf.readUInt32BE(0) !== 0x89504e47) return undefined
      return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) }
    } finally {
      await fh.close()
    }
  } catch {
    return undefined
  }
}

// ---- the whole site -----------------------------------------------------------------------------

export interface Preview {
  /** Path relative to out/. */
  readonly path: string
  readonly width: number
  readonly height: number
}

/** Width and height of a PNG or JPEG file; undefined if it is missing or neither. */
export const fileImageSize = async (path: string): Promise<{ width: number; height: number } | undefined> => {
  try {
    return imageSize(await readFile(path))
  } catch {
    return undefined
  }
}

/** The best preview image a build has on disk: social.jpg, else social.png, else its thumbnail. */
export const previewOf = async (outDir: string, b: BuildMeta): Promise<Preview | undefined> => {
  for (const path of [`builds/${b.id}/social.jpg`, `builds/${b.id}/social.png`, b.files?.thumb]) {
    if (path === undefined) continue
    const size = await fileImageSize(resolve(outDir, path))
    if (size !== undefined) return { path, ...size }
  }
  return undefined
}

/** JPEG quality for preview images: high enough that thin lines keep their color (no chroma subsampling either). */
export const SOCIAL_JPEG_QUALITY = 86

type JpegEncoder = (png: string, jpg: string) => Promise<unknown>
const q = String(SOCIAL_JPEG_QUALITY)
const PIL = `import sys\nfrom PIL import Image\nImage.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=${q}, subsampling=0, optimize=True)`
/** JPEG encoders, tried in order: ImageMagick 7, ImageMagick 6, Python's Pillow; each with how to tell it is installed. */
const JPEG_ENCODERS: readonly { readonly probe: readonly [string, readonly string[]]; readonly encode: JpegEncoder }[] = [
  { probe: ['magick', ['-version']], encode: (png, jpg) => run('magick', [png, '-quality', q, '-sampling-factor', '4:4:4', '-strip', jpg], { timeout: 60_000 }) },
  { probe: ['convert', ['-version']], encode: (png, jpg) => run('convert', [png, '-quality', q, '-sampling-factor', '4:4:4', '-strip', jpg], { timeout: 60_000 }) },
  { probe: ['python3', ['-c', 'import PIL']], encode: (png, jpg) => run('python3', ['-c', PIL, png, jpg], { timeout: 60_000 }) },
]
let jpegEncoder: Promise<JpegEncoder | null> | undefined

/** What is installed to write JPEGs, found once. */
const findJpegEncoder = (): Promise<JpegEncoder | null> =>
  (jpegEncoder ??= (async () => {
    for (const e of JPEG_ENCODERS) {
      try {
        await run(e.probe[0], [...e.probe[1]], { timeout: 20_000 })
        return e.encode
      } catch {
        // next
      }
    }
    return null
  })())

/** Write `jpg`, a JPEG of the PNG at `png`. False when no encoder is installed, or this PNG would not convert. */
export const writeJpeg = async (png: string, jpg: string): Promise<boolean> => {
  const enc = await findJpegEncoder()
  if (enc === null) return false
  try {
    await enc(png, jpg)
    if ((await fileImageSize(jpg)) !== undefined) return true
  } catch {
    // fall through
  }
  await rm(jpg, { force: true }).catch(() => undefined)
  return false
}

/** True when `a` is missing or older than `b`. */
const staler = async (a: string, b: string): Promise<boolean> => {
  try {
    const [sa, sb] = await Promise.all([stat(a), stat(b)])
    return sa.mtimeMs < sb.mtimeMs
  } catch {
    return true
  }
}

/** The site's preview build: the newest of the configured flagship, else the newest build. */
export const flagshipOf = (builds: readonly BuildMeta[], flagship?: string): BuildMeta | undefined =>
  (flagship === undefined ? undefined : builds.find((b) => b.id === flagship || b.region === flagship || b.name === flagship)) ?? builds[0]

/**
 * The URL `onSale` gives a subject (a region, a set slug, a page slug, or `<region>:<year>`): the
 * entry under the longest key the subject starts with; a key with a year (`<region>:<year>`)
 * only when it is the whole subject. No entry, no URL: nothing links to the shop for it.
 */
export const onSaleUrl = (onSale: OnSale | undefined, subject: string): string | undefined => {
  const key = onSaleKey(onSale, subject)
  return key === undefined ? undefined : onSale?.[key]
}

/** The `onSale` key a subject is on sale under (see `onSaleUrl`), if any. */
export const onSaleKey = (onSale: OnSale | undefined, subject: string): string | undefined =>
  onSale === undefined ? undefined : Object.keys(onSale).filter((k) => k !== '' && (k.includes(':') ? k === subject : subject.startsWith(k))).sort((a, b) => b.length - a.length)[0]

/**
 * The quiet line at the foot of a series page (through-time.ts): the shop's front page, when any
 * year of the series (or the whole series) is on sale. Its URL is the shop's own (`shop.url`); the
 * explorer tags it with the campaign when clicked, a static page through `href`.
 */
export const seriesShopLine = (config: Pick<SiteConfig, 'shop'>, region: string, href: (url: string) => string = (u) => u): string | undefined => {
  const shop = config.shop
  if (shop === undefined) return undefined
  const keys = Object.keys(shop.onSale ?? {})
  const any = onSaleKey(shop.onSale, region) !== undefined || keys.some((k) => k.startsWith(`${region}:`))
  if (!any) return undefined
  const esc = (x: string) => x.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c] as string)
  return `<p class="tt-shop">Some of these years are sold as prints: <a href="${esc(href(shop.url))}" target="_blank" rel="noopener">${esc(shop.label)} ↗</a></p>`
}

/** True while anything at all is on sale. */
export const anyOnSale = (config: Pick<SiteConfig, 'shop'>): boolean => Object.keys(config.shop?.onSale ?? {}).length > 0

/** The shop's call to action (`cta`), only while something is on sale. */
export const shopCta = (config: Pick<SiteConfig, 'shop'>): string | undefined =>
  anyOnSale(config) ? config.shop?.cta : undefined

/**
 * Where "Buy a print" goes for a region, or for one year of it: `onSale` by the longest key that
 * `<region>` (or `<region>:<year>`, the explorer's route for that year) starts with, with its
 * featured view's button text. So a region's key covers every year, and a key such as
 * `richmond-downtown-time:1925` that year's view alone (not the series' page, nor another year).
 * The explorer gets these resolved (`buyLinks`).
 */
export const shopFor = (config: Pick<SiteConfig, 'shop' | 'home'>, region: string, year?: number): ShopLink | undefined => {
  const key = onSaleKey(config.shop?.onSale, year === undefined ? region : `${region}:${year}`)
  const url = key === undefined ? undefined : config.shop?.onSale?.[key]
  if (key === undefined || url === undefined) return undefined
  const hero = config.home?.heroes.find((h) => h.region === region)
  const prints = config.shop?.prints?.[key]
  const more = (prints ?? []).slice(1).filter((p): p is Product => p.label !== undefined).map((p) => ({ url: p.url, label: p.label }))
  return { url, label: prints?.[0]?.label ?? hero?.shopLabel ?? 'Buy a print ↗', ...(more.length > 0 ? { more } : {}) }
}

/** A map's buy link, and any other prints made from the same view (`prints`), shown beside it. */
export interface ShopLink {
  readonly url: string
  readonly label: string
  readonly more?: readonly Product[]
}

/**
 * Where a front-page section's shop button goes: the one URL every one of its prefixes is on sale
 * under, else its story page's slug in `onSale`. Nothing when neither holds.
 */
export const sectionShop = (config: Pick<SiteConfig, 'shop'>, sec: Pick<HomeSection, 'page' | 'prefixes' | 'shopLabel'>): { url: string; label: string } | undefined => {
  const onSale = config.shop?.onSale
  const label = sec.shopLabel ?? 'Buy prints ↗'
  const urls = new Set(sec.prefixes.map((p) => onSaleUrl(onSale, p)))
  const shared = urls.size === 1 ? [...urls][0] : undefined
  if (shared !== undefined) return { url: shared, label }
  const slug = sec.page?.startsWith('#/') ? sec.page.slice(2).split('/')[0] : undefined
  const bySlug = slug === undefined || slug === '' ? undefined : onSaleUrl(onSale, slug)
  return bySlug === undefined ? undefined : { url: bySlug, label }
}

/**
 * Where a content page's shop button goes: its own slug in `onSale` (a set's or a cutaway's
 * page; "Prints of this set ↗" when that is a collection), else the one URL every map it links
 * to is on sale under, else its section's (the section whose story it tells). `maps` are the
 * regions the page links into, in order.
 */
export const pageShop = (slug: string, maps: readonly string[], config: Pick<SiteConfig, 'shop' | 'home'>): { url: string; label: string } | undefined => {
  const label = maps.length > 1 ? 'Prints of these maps ↗' : maps.length === 1 ? 'Prints of this map ↗' : 'Buy a print ↗'
  const own = onSaleUrl(config.shop?.onSale, slug)
  if (own !== undefined) return { url: own, label: /\/collections\//.test(own) ? 'Prints of this set ↗' : label }
  const urls = new Set(maps.map((r) => onSaleUrl(config.shop?.onSale, r)))
  const shared = urls.size === 1 ? [...urls][0] : undefined
  if (shared !== undefined) return { url: shared, label }
  const sec = config.home?.sections.find((s) => s.page === `#/${slug}`)
  const viaSection = sec === undefined ? undefined : sectionShop(config, sec)
  return viaSection === undefined ? undefined : { url: viaSection.url, label }
}

/**
 * The maps a content page links into, in order of first link: the region of each link to a view,
 * written as the explorer has it (`#<region>…`) or as a static page does (`../index.html#<region>…`).
 */
export const pageMapRefs = (html: string): string[] => {
  const out: string[] = []
  for (const m of html.matchAll(/href="(?:\.\.\/index\.html)?#([a-z0-9][a-z0-9-]*)(?=[:@"])/g)) if (m[1] !== 'home' && !out.includes(m[1])) out.push(m[1])
  return out
}

/**
 * A content page with each piece's print beside the link to its view: where a link to a view in
 * `products` (written `<prefix><view>`, `#` in the explorer, `../index.html#` in a static page)
 * leads a list of links (`See it on the map · Sources: …`), its prints follow it in that list;
 * otherwise they close its paragraph. Each view's prints are given once, at its first link.
 * `href` may tag a shop URL (`withCampaign`). Nothing changes for a view not on sale.
 */
export const printLinks = (html: string, products: Products | undefined, prefix = '#', href: (url: string) => string = (u) => u): string => {
  if (products === undefined || Object.keys(products).length === 0) return html
  const esc = (s: string) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string)
  const done = new Set<string>()
  // Paragraph by paragraph, so a print never lands outside the paragraph that links to its view.
  return html.replace(/<p>([\s\S]*?)<\/p>/g, (whole, body: string) => {
    let text = body
    let tail = ''
    for (const [view, list] of Object.entries(products)) {
      if (done.has(view)) continue
      const open = `<a href="${esc(prefix + view)}">`
      const at = text.indexOf(open)
      if (at < 0) continue
      done.add(view)
      const links = list.map((p) => `<a class="buy" href="${esc(href(p.url))}" target="_blank" rel="noopener">${esc(p.label)}</a>`).join(' · ')
      const end = text.indexOf('</a>', at) + 4
      if (text.startsWith(' · ', end)) text = text.slice(0, end) + ' · ' + links + text.slice(end)
      else tail += (/[.!?]$/.test((text + tail).replace(/<[^>]*>/g, '').trimEnd()) ? ' ' : ' · ') + links
    }
    return text === body && tail === '' ? whole : `<p>${text}${tail}</p>`
  })
}

/**
 * Every shop link the explorer's script shows, resolved here: per region and per `<region>:<year>`
 * (each given as such a string), and per front-page section (null when not on sale).
 */
export const buyLinks = (config: Pick<SiteConfig, 'shop' | 'home'>, regions: Iterable<string>): { regions: Record<string, ShopLink>; sections: ({ url: string; label: string } | null)[] } => {
  const out: Record<string, ShopLink> = {}
  for (const r of regions) {
    const m = /^(.*):(\d+)$/.exec(r)
    const s = m === null ? shopFor(config, r) : shopFor(config, m[1], Number(m[2]))
    if (s !== undefined) out[r] = s
  }
  return { regions: out, sections: (config.home?.sections ?? []).map((s) => sectionShop(config, s) ?? null) }
}

/**
 * A shop link tagged with where it was followed from, as the explorer tags them when clicked:
 * utm_source=isoscape-explorer, utm_medium=referral, utm_campaign=<page slug or region>. Only links
 * to the shop's own host are tagged, and a link that already carries utm_source is left alone.
 */
export const withCampaign = (href: string, campaign: string, shopUrl?: string): string => {
  let u: URL
  try {
    u = new URL(href)
  } catch {
    return href
  }
  let host: string | undefined
  try {
    host = shopUrl === undefined ? undefined : new URL(shopUrl).hostname
  } catch {
    host = undefined
  }
  if ((host !== undefined && u.hostname !== host) || u.searchParams.has('utm_source')) return href
  u.searchParams.set('utm_source', 'isoscape-explorer')
  u.searchParams.set('utm_medium', 'referral')
  u.searchParams.set('utm_campaign', campaign.replace(/[^a-z0-9-]+/gi, '-').slice(0, 60) || 'home')
  return u.toString()
}

/** What index.html needs to carry the site-wide card. */
export interface SiteCard {
  readonly siteUrl?: string
  readonly shop?: SiteConfig['shop']
  readonly home?: HomeConfig
  readonly latestPages?: boolean
  readonly analytics?: SiteConfig['analytics']
  readonly image?: Preview
  readonly imageAlt?: string
  /** Plain links to the static pages (static-pages.ts), grouped, for crawlers and readers without script. */
  readonly plain?: readonly { readonly title: string; readonly links: readonly { readonly href: string; readonly label: string }[] }[]
  /** True when sitemap.xml is written beside index.html. */
  readonly sitemap?: boolean
  /** The share pages that outlive builds, for the explorer's Link button and address bar (see `Shares`). */
  readonly shares?: Shares
}

/**
 * A map's lasting share page: `s/<name>.html`, named as its static page `m/<name>.html` is,
 * opening the explorer at `route` (`#<region>` or `#<region>:<year>`) with `build`'s card.
 */
export interface ShareDoor {
  readonly name: string
  readonly route: string
  readonly build: BuildMeta
  /** The card's title (the map page's heading), before " · isoscape"; default from the build. */
  readonly title?: string
  /** Its key in `Shares.maps`, when not the route without its '#': a series page's is its region. */
  readonly key?: string
}

/**
 * What the explorer needs to hand out share pages: `maps`, a map's route without its '#'
 * (`<region>` or `<region>:<year>`) → its name (`s/<name>.html`, `m/<name>.html`), and `pages`,
 * the slugs of the content pages (`s/page-<slug>.html`, `p/<slug>.html`).
 */
export interface Shares {
  readonly maps: Readonly<Record<string, string>>
  readonly pages: readonly string[]
}

/** A file name in s/ that a map's lasting share page may not take: a build's, or a content page's. */
export const doorNameClashes = (name: string): boolean => /^\d{8}-\d{6}-/.test(name) || name.startsWith('page-')

/** The site-wide tags for index.html (which sits at out/, depth 0). */
export const siteTags = (site: SiteCard, buildCount: number): string =>
  metaTags({
    title: `${SITE_NAME}: isometric views of real places`,
    description: buildCount > 1 ? `${SITE_DESCRIPTION.slice(0, -1)}: ${buildCount} views, with how each was made.` : SITE_DESCRIPTION,
    ...(site.image === undefined ? {} : {
      image: siteHref(site.image.path, site.siteUrl),
      imageWidth: site.image.width,
      imageHeight: site.image.height,
      ...(site.imageAlt === undefined ? {} : { imageAlt: site.imageAlt }),
    }),
    ...(site.siteUrl === undefined ? {} : { url: site.siteUrl }),
  })

/**
 * Make what link previews need: a social image for every build that lacks one (when a
 * rasteriser is installed), and a share page for every build and content page. Returns the
 * site-wide card for index.html.
 */
export const writeSocial = async (
  outDir: string,
  builds: readonly BuildMeta[],
  pages: readonly Page[],
  config: SiteConfig,
  log: (line: string) => void = () => undefined,
  /** The static page (path under out/) a build or content page is best read at: the share page names it as canonical and links to it. */
  staticOf: (target: { build: BuildMeta } | { page: string }) => string | undefined = () => undefined,
  /** The maps' lasting share pages (see `ShareDoor`), from the static plan (`shareDoors` in static-pages.ts). */
  doors: readonly ShareDoor[] = [],
): Promise<SiteCard & { rendered: number; missing: number; stale: number }> => {
  const base = config.siteUrl
  // A share page is a door into the explorer; the static page is what a search engine should index.
  const pointTo = (path: string | undefined, label: string) => path === undefined ? { card: {}, more: undefined } : {
    card: base === undefined ? {} : { canonical: siteHref(path, base) },
    more: { href: siteHref(path, undefined, 1), label },
  }
  let rendered = 0
  let missing = 0
  let canRender = true
  for (const b of builds) {
    const png = resolve(outDir, 'builds', b.id, 'social.png')
    if ((await pngSize(png)) !== undefined) continue
    if (canRender) {
      if ((await findRasteriser()) === null) canRender = false
      else {
        log(`social image for ${b.id}…`)
        if (await renderSocial(resolve(outDir, b.files?.svg ?? `builds/${b.id}/image.svg`), png, b.viewBox)) {
          rendered++
          continue
        }
      }
    }
    missing++
  }
  // The JPEG beside each social.png, made again whenever the PNG is newer.
  for (const b of builds) {
    const png = resolve(outDir, 'builds', b.id, 'social.png')
    const jpg = resolve(outDir, 'builds', b.id, 'social.jpg')
    if ((await pngSize(png)) === undefined || !(await staler(jpg, png))) continue
    if ((await findJpegEncoder()) === null) break
    await writeJpeg(png, jpg)
  }
  await mkdir(resolve(outDir, 's'), { recursive: true })
  const previews = new Map<string, Preview | undefined>()
  for (const b of builds) {
    const preview = await previewOf(outDir, b)
    previews.set(b.id, preview)
    const { title, description, alt } = buildCard(b)
    const file = shareFile({ build: b.id })
    const to = pointTo(staticOf({ build: b }), 'About this map')
    await writeFile(resolve(outDir, 's', file), sharePage({
      title, description, type: 'article',
      ...(preview === undefined ? {} : { image: siteHref(preview.path, base, 1), imageWidth: preview.width, imageHeight: preview.height, imageAlt: alt }),
      ...(base === undefined ? {} : { url: siteHref(`s/${file}`, base) }),
      ...to.card,
    }, `#${b.id}`, to.more))
  }
  const flag = flagshipOf(builds, config.flagship)
  const image = flag === undefined ? undefined : previews.get(flag.id)
  const imageAlt = flag === undefined ? undefined : buildCard(flag).alt
  // The maps' lasting share pages, and the card each gives.
  const doorCard = (d: ShareDoor): Card => {
    const preview = previews.get(d.build.id)
    const card = buildCard(d.build)
    return {
      title: d.title === undefined ? card.title : `${d.title} · ${SITE_NAME}`,
      description: card.description,
      type: 'article',
      ...(preview === undefined ? {} : { image: siteHref(preview.path, base, 1), imageWidth: preview.width, imageHeight: preview.height, imageAlt: card.alt }),
      ...(base === undefined ? {} : { url: siteHref(`s/${d.name}.html`, base) }),
    }
  }
  const maps: Record<string, string> = {}
  const written = new Set(builds.map((b) => shareFile({ build: b.id })))
  for (const d of doors) {
    if (doorNameClashes(d.name) || written.has(`${d.name}.html`)) continue
    written.add(`${d.name}.html`)
    maps[d.key ?? d.route.replace(/^#/, '')] = d.name
    const to = pointTo(staticOf({ build: d.build }), 'About this map')
    await writeFile(resolve(outDir, 's', `${d.name}.html`), sharePage({ ...doorCard(d), ...to.card }, d.route, to.more))
  }
  // Share pages of builds no longer here (links already shared): their region's card, newest
  // first by the build's name, then its region; else the site's. The fragment still passes on,
  // and the explorer opens a gone build id as the newest build of the same name.
  let stale = 0
  const newestFirst = [...builds].sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1))
  for (const f of await readdir(resolve(outDir, 's'))) {
    const m = /^\d{8}-\d{6}-(.+)\.html$/.exec(f)
    if (m === null || written.has(f)) continue
    const now = newestFirst.find((b) => b.name === m[1]) ?? newestFirst.find((b) => b.region === m[1])
    const door = now === undefined ? undefined : doors.find((d) => d.build.id === now.id) ?? doors.find((d) => d.build.region === now.region)
    const url = base === undefined ? {} : { url: siteHref(`s/${f}`, base) }
    const card: Card = door !== undefined ? { ...doorCard(door), ...url }
      : now !== undefined ? (() => {
        const c = buildCard(now)
        const p = previews.get(now.id)
        return { title: c.title, description: c.description, type: 'article' as const, ...(p === undefined ? {} : { image: siteHref(p.path, base, 1), imageWidth: p.width, imageHeight: p.height, imageAlt: c.alt }), ...url }
      })()
      : { title: `${SITE_NAME}: isometric views of real places`, description: SITE_DESCRIPTION, ...(image === undefined ? {} : { image: siteHref(image.path, base, 1), imageWidth: image.width, imageHeight: image.height, ...(imageAlt === undefined ? {} : { imageAlt }) }), ...url }
    const to = now === undefined ? { card: {}, more: undefined } : pointTo(staticOf({ build: now }), 'About this map')
    await writeFile(resolve(outDir, 's', f), sharePage({ ...card, ...to.card }, door?.route ?? (now === undefined ? '#home' : `#${now.id}`), to.more))
    stale++
  }
  for (const p of pages) {
    const file = shareFile({ page: p.slug })
    // A page with its own `social:` image gets it, copied beside its share page as
    // s/page-<slug>.<ext>; otherwise it shares the site's flagship picture.
    let own: Preview | undefined
    const size = p.social === undefined ? undefined : imageSize(p.social.bytes)
    if (p.social !== undefined && size !== undefined) {
      const name = `page-${p.slug}${extname(p.social.name).toLowerCase().replace('.jpeg', '.jpg')}`
      await writeFile(resolve(outDir, 's', name), p.social.bytes)
      own = { path: `s/${name}`, ...size }
    }
    const pic = own ?? image
    const alt = own === undefined ? imageAlt : p.summary ?? p.title
    const to = pointTo(staticOf({ page: p.slug }), 'Read it as a plain page')
    // Its shop button, as the explorer and the static page show it.
    const shop = config.shop === undefined || p.noShop ? undefined : pageShop(p.slug, pageMapRefs(p.html), config)
    await writeFile(resolve(outDir, 's', file), sharePage({
      title: `${p.title} · ${SITE_NAME}`,
      description: pageDescription(p),
      type: 'article',
      ...(pic === undefined ? {} : { image: siteHref(pic.path, base, 1), imageWidth: pic.width, imageHeight: pic.height, ...(alt === undefined ? {} : { imageAlt: alt }) }),
      ...(base === undefined ? {} : { url: siteHref(`s/${file}`, base) }),
      ...to.card,
    }, `#/${p.slug}`, to.more, shop === undefined ? undefined : { href: withCampaign(shop.url, p.slug, config.shop?.url), label: shop.label }))
  }
  return {
    ...(base === undefined ? {} : { siteUrl: base }),
    ...(image === undefined ? {} : { image }),
    ...(imageAlt === undefined ? {} : { imageAlt }),
    shares: { maps, pages: pages.map((p) => p.slug) },
    rendered,
    missing,
    stale,
  }
}
