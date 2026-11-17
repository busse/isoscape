/**
 * Static pages for search engines and anyone without script.
 *
 * The explorer is one page that routes with the URL fragment (`#/streetcars`,
 * `#richmond-streetcars:1925`), so a crawler sees a single address, and the share pages in `s/`
 * forward to it at once. This writes, beside index.html, a plain HTML page for everything worth
 * finding, each with its whole text in the document, its own title, description, canonical URL,
 * link-preview tags and JSON-LD, and a way into the explorer:
 *
 *   p/<slug>.html            every content page in pages/ (`#/<slug>` in the explorer)
 *   m/<region>.html          every region: its newest build, or for a dated series of more
 *                            than one year, the series with its years
 *   m/<region>-<year>.html   each year of such a series (`#<region>:<year>`)
 *   sitemap.xml              all of them, with index.html, when the site URL is known
 *
 * Map pages are named by region, not by build id, so a rebuild keeps their address (a search
 * engine's ranking stays with it); build ids change with every build. The share pages stay
 * where they are, forwarding into the explorer, and name these pages as canonical.
 *
 * Links between these pages are relative, so the same files work under the site's path
 * (/isoscape/) and opened from disk.
 */

import { execFile } from 'node:child_process'
import { mkdir, readdir, readFile, rm, writeFile } from 'node:fs/promises'
import { extname, resolve } from 'node:path'
import { promisify } from 'node:util'
import type { BuildMeta } from './archive.ts'
import { DEM_SOURCES } from './dem-sources.ts'
import { MARK, PROSE_CSS, STORY_CSS, THEME_CSS } from './explorer.ts'
import { escapeHtml } from './markdown.ts'
import { loadPages, PAGES_DIR, type Page } from './pages.ts'
import {
  buildCard, clip, escAttr, firstParagraph, flagshipOf, pageDescription, imageSize, metaTags, pageShop, previewOf, shopFor, siteHref, withCampaign, type ShareDoor,
  SITE_NAME, statsLine, type HomeConfig, type Preview, type SiteConfig,
} from './social.ts'
import { makeStory } from './story.ts'

const run = promisify(execFile)

/** Who draws the maps and writes the pages. */
export const AUTHOR = 'Chris Busse'

// ---- the plan: which pages, at which paths ------------------------------------------------------

export interface MapEntry {
  readonly kind: 'map'
  /** Path under out/, e.g. `m/lm-grand-canyon.html`. */
  readonly path: string
  readonly region: string
  /** The build shown: the newest of the region, or of its year. */
  readonly build: BuildMeta
  /** The year, for a dated build. */
  readonly year?: number
  /** Its explorer route, a lasting name: `#<region>` or `#<region>:<year>`. */
  readonly route: string
  /** The series page this year belongs to, for a year of a series. */
  readonly series?: string
}

export interface SeriesEntry {
  readonly kind: 'series'
  readonly path: string
  readonly region: string
  /** The year shown first: the featured year, else the latest. */
  readonly build: BuildMeta
  readonly years: readonly MapEntry[]
  readonly route: string
}

export interface PageEntry {
  readonly kind: 'page'
  readonly path: string
  readonly slug: string
  readonly route: string
}

export type StaticEntry = MapEntry | SeriesEntry | PageEntry

export interface StaticPlan {
  readonly entries: readonly StaticEntry[]
  /** The static page for a build: its year's page, else its region's. */
  readonly forBuild: (b: BuildMeta) => string | undefined
  readonly forPage: (slug: string) => string | undefined
  /** The page for a region (its series page, for a series). */
  readonly forRegion: (region: string) => string | undefined
}

const safeName = (s: string): string => s.toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '') || 'map'
const newest = (bs: readonly BuildMeta[]): BuildMeta => bs.reduce((a, b) => (b.createdAt > a.createdAt ? b : a))

/** Every static page for these builds and content pages, with stable paths. */
export const planStatic = (builds: readonly BuildMeta[], pageSlugs: readonly string[], home?: HomeConfig): StaticPlan => {
  const entries: StaticEntry[] = []
  const byPage = new Map<string, string>()
  for (const slug of pageSlugs) {
    const path = `p/${slug}.html`
    entries.push({ kind: 'page', path, slug, route: `#/${slug}` })
    byPage.set(slug, path)
  }
  const regions = new Map<string, BuildMeta[]>()
  for (const b of builds) {
    if (!regions.has(b.region)) regions.set(b.region, [])
    regions.get(b.region)?.push(b)
  }
  const names = [...regions.keys()].sort()
  // Region pages first, so a year page can never take a region's address.
  const taken = new Set(names.map((r) => `m/${safeName(r)}.html`))
  const byRegion = new Map<string, string>()
  const byYear = new Map<string, string>()
  for (const region of names) {
    const bs = regions.get(region) ?? []
    const dated = bs.filter((b) => b.time !== undefined)
    const years = [...new Set(dated.map((b) => b.time?.year as number))].sort((a, b) => a - b)
    const path = `m/${safeName(region)}.html`
    byRegion.set(region, path)
    if (years.length > 1) {
      const yearEntries: MapEntry[] = years.map((year) => {
        let p = `m/${safeName(region)}-${year}.html`
        if (taken.has(p)) p = `m/${safeName(region)}-${year}-map.html`
        taken.add(p)
        byYear.set(`${region}:${year}`, p)
        return { kind: 'map', path: p, region, build: newest(dated.filter((b) => b.time?.year === year)), year, route: `#${region}:${year}`, series: path }
      })
      const featured = home?.heroes.find((h) => h.region === region)?.year
      const lead = yearEntries.find((e) => e.year === featured) ?? yearEntries[yearEntries.length - 1]
      entries.push({ kind: 'series', path, region, build: lead.build, years: yearEntries, route: lead.route })
      entries.push(...yearEntries)
    } else {
      const build = newest(dated.length > 0 ? dated : bs)
      const year = build.time?.year
      entries.push({ kind: 'map', path, region, build, ...(year === undefined ? {} : { year }), route: year === undefined ? `#${region}` : `#${region}:${year}` })
    }
  }
  return {
    entries,
    forBuild: (b) => (b.time === undefined ? undefined : byYear.get(`${b.region}:${b.time.year}`)) ?? byRegion.get(b.region),
    forPage: (slug) => byPage.get(slug),
    forRegion: (region) => byRegion.get(region),
  }
}

/**
 * Every map's lasting share page (social.ts writes them as `s/<name>.html`), named as its static
 * page is: `m/<name>.html` → `s/<name>.html`, with its route and its page's heading.
 */
export const shareDoors = (plan: StaticPlan, home?: HomeConfig): ShareDoor[] =>
  plan.entries.filter((e): e is MapEntry | SeriesEntry => e.kind !== 'page').map((e) => ({
    name: e.path.replace(/^m\//, '').replace(/\.html$/, ''),
    route: e.route,
    build: e.build,
    title: mapTitle(e, home),
    ...(e.kind === 'series' ? { key: e.region } : {}),
  }))

/** The front-page section a region belongs to (the first whose prefixes match), as the explorer groups them. */
export const sectionOf = (home: HomeConfig | undefined, region: string) =>
  home?.sections.find((s) => s.prefixes.some((p) => region.startsWith(p)))

const titleOf = (b: BuildMeta): string => b.config?.title || b.title || b.region

/** A map page's heading: the featured view's title, else the region's; then the year and what it was. */
export const mapTitle = (e: MapEntry | SeriesEntry, home?: HomeConfig): string => {
  const hero = home?.heroes.find((h) => h.region === e.region)
  if (e.kind === 'series') return hero?.title ?? titleOf(e.build)
  const place = e.series === undefined ? hero?.title ?? titleOf(e.build) : titleOf(e.build)
  if (e.year === undefined) return place
  const epoch = e.build.time?.title
  return `${place}${place.includes(String(e.year)) ? '' : `, ${e.year}`}${epoch ? `: ${epoch}` : ''}`
}

/** The regions a static content page links into (`../index.html#<region>…`), in order of first mention. */
export const mapRefs = (html: string): string[] => {
  const out: string[] = []
  for (const m of html.matchAll(/href="\.\.\/index\.html#([a-z0-9][a-z0-9-]*)(?=[:@"])/g)) if (m[1] !== 'home' && !out.includes(m[1])) out.push(m[1])
  return out
}

// ---- links --------------------------------------------------------------------------------------

/**
 * A link in a content page, once it is an explorer route (see `pageLink`), as it should read in
 * `p/<slug>.html`: another page is its file, a section of this one its own anchor, and anything
 * else in the explorer (a map) is the explorer's route.
 */
export const staticRoute = (href: string, slug: string, slugs: ReadonlySet<string>, shopUrl?: string): string => {
  // A link to the shop carries the campaign tags the explorer adds when it is clicked.
  if (shopUrl !== undefined && /^https?:/i.test(href)) return withCampaign(href, slug, shopUrl)
  if (href.startsWith('#/')) {
    const [target, ...rest] = href.slice(2).split('/')
    const section = rest.join('/')
    if (!slugs.has(target)) return `../index.html${href}`
    if (target === slug) return section ? `#${section}` : '#'
    return `${target}.html${section ? `#${section}` : ''}`
  }
  if (href.startsWith('#')) return href.length > 1 ? `../index.html${href}` : href
  return href
}

/** The content pages as the static pages show them: GitHub's anchors, links between files, images as files in p/. */
export const loadStaticPages = (slugs: readonly string[], dir: string = PAGES_DIR, siteUrl?: string, shopUrl?: string): { pages: Page[]; images: Set<string> } => {
  const images = new Set<string>()
  const known = new Set(slugs)
  const pages = loadPages(dir, siteUrl, {
    idPrefix: '',
    route: (href, slug) => staticRoute(href, slug, known, shopUrl),
    imageHref: (name) => {
      images.add(name)
      return name
    },
  })
  return { pages, images }
}

// ---- the pieces of a page -----------------------------------------------------------------------

const ldJson = (v: unknown): string => `<script type="application/ld+json">${JSON.stringify(v).replace(/</g, '\\u003c')}</script>\n`

const analytics = (ga: string | undefined): string =>
  ga === undefined ? '' : `<script async src="https://www.googletagmanager.com/gtag/js?id=${escAttr(ga)}"></script>
<script>window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments)} gtag('js', new Date()); gtag('config', '${escAttr(ga)}')</script>
`

/** Layout for the static pages; colors and type come from the explorer's own CSS (THEME_CSS and the rest). */
export const STATIC_CSS = `html, body { margin: 0; background: var(--panel); color: var(--ink); }
.top { display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px 18px; padding: 12px 20px; border-bottom: 1px solid var(--line); background: var(--panel); }
.top a.brand { display: flex; align-items: baseline; gap: 8px; color: inherit; text-decoration: none; }
.top a.brand b { font-size: 15px; letter-spacing: -.01em; }
.top a.brand span { color: var(--dim); }
.top nav { margin-left: auto; display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 13px; }
.top nav a { color: var(--accent); text-decoration: none; }
.top nav a:hover { text-decoration: underline; }
.wrap { max-width: 70ch; margin: 0 auto; padding: 26px 20px 40px; }
.wrap.wide { max-width: 1040px; }
.acts { display: flex; flex-wrap: wrap; gap: 10px; margin: 0 0 22px; }
.btn { display: inline-block; padding: 7px 15px; border-radius: 18px; background: var(--accent); color: var(--panel); border: 1px solid var(--accent); text-decoration: none; font-weight: 600; font-size: 13px; }
.btn.ghost { background: transparent; color: var(--accent); }
.btn:hover { filter: brightness(1.08); }
h1.title { font-size: 30px; line-height: 1.15; letter-spacing: -.02em; margin: 0 0 12px; font-weight: 650; }
.lede { font-size: 16px; line-height: 1.6; margin: 0 0 18px; max-width: 74ch; }
.plain { font-size: 15px; line-height: 1.6; max-width: 74ch; }
.plain a { color: var(--accent); text-underline-offset: 2px; }
figure.pic { margin: 0 0 18px; }
figure.pic img { display: block; width: 100%; height: auto; border-radius: 10px; background: var(--stage); border: 1px solid var(--line); }
figure.pic figcaption { font-size: 12.5px; color: var(--dim); margin-top: 6px; }
.years { display: flex; flex-wrap: wrap; gap: 5px; margin: 0 0 20px; padding: 0; list-style: none; }
.years a, .years span { display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 10px; border: 1px solid var(--line); color: var(--ink); text-decoration: none; }
.years a:hover { border-color: var(--accent); color: var(--accent); }
.years span { background: var(--accent); border-color: var(--accent); color: var(--panel); }
h2.sub { font-size: 20px; letter-spacing: -.01em; margin: 34px 0 12px; padding-top: 14px; border-top: 1px solid var(--line); font-weight: 650; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; padding: 0; list-style: none; }
.cards a { display: flex; flex-direction: column; gap: 5px; text-decoration: none; color: var(--ink); background: var(--bg); border: 1px solid var(--line); border-radius: 9px; padding: 8px; height: 100%; box-sizing: border-box; }
.cards a:hover { border-color: var(--accent); }
.cards img { width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 5px; background: var(--stage); display: block; }
.cards b { font-size: 13px; line-height: 1.3; }
.cards small { color: var(--dim); font-size: 12px; }
.more { font-size: 14px; }
.more ul { columns: 2 220px; padding-left: 1.1em; margin: 0; }
.more li { margin: 2px 0; }
.more a { color: var(--accent); }
.foot { max-width: 1040px; margin: 0 auto; padding: 14px 20px 48px; border-top: 1px solid var(--line); font-size: 12.5px; color: var(--dim); }
.foot p { margin: 0 0 6px; }
.foot a { color: var(--accent); }
@media (max-width: 600px) { h1.title, .prose h1 { font-size: 25px; } .wrap { padding-top: 18px; } .top nav { margin-left: 0; } }
`

interface Head {
  /** Ask search engines not to index the page (an unlisted page, waiting to be reviewed). */
  readonly noindex?: boolean
  readonly title: string
  readonly description: string
  readonly path: string
  readonly image?: Preview
  readonly imageAlt?: string
  readonly type: 'website' | 'article'
  readonly ld: unknown
}

interface Ctx {
  readonly config: SiteConfig
  readonly plan: StaticPlan
  readonly pages: readonly Page[]
  readonly depth: number
}

const up = (depth: number) => '../'.repeat(depth)

const head = (h: Head, ctx: Ctx): string => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(h.title)}</title>
${h.noindex ? '<meta name="robots" content="noindex">\n' : ''}${analytics(ctx.config.analytics?.ga)}<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,${encodeURIComponent(MARK)}">
${ctx.config.siteUrl === undefined ? '' : `<link rel="sitemap" type="application/xml" title="Sitemap" href="${up(ctx.depth)}sitemap.xml">\n`}${metaTags({
  title: h.title,
  description: h.description,
  type: h.type,
  ...(h.image === undefined ? {} : {
    image: siteHref(h.image.path, ctx.config.siteUrl, ctx.depth), imageWidth: h.image.width, imageHeight: h.image.height,
    ...(h.imageAlt === undefined ? {} : { imageAlt: h.imageAlt }),
  }),
  ...(ctx.config.siteUrl === undefined ? {} : { url: siteHref(h.path, ctx.config.siteUrl) }),
})}${ldJson(h.ld)}<style>
${THEME_CSS}* { box-sizing: border-box; }
${PROSE_CSS}${STORY_CSS}${STATIC_CSS}</style>
</head>
<body>
`

/** The bar along the top: the site's name into the explorer, the main pages, the shop. */
const topBar = (ctx: Ctx, campaign: string): string => {
  const u = up(ctx.depth)
  const nav: string[] = []
  for (const slug of ['how-its-made', 'about']) {
    const p = ctx.pages.find((x) => x.slug === slug)
    const path = ctx.plan.forPage(slug)
    if (p !== undefined && path !== undefined) nav.push(`<a href="${escAttr(u + path)}">${escapeHtml(p.title)}</a>`)
  }
  if (ctx.config.shop) nav.push(`<a href="${escAttr(withCampaign(ctx.config.shop.url, campaign, ctx.config.shop.url))}">Shop prints ↗</a>`)
  return `<header class="top"><a class="brand" href="${u}index.html" title="Open the isoscape explorer"><b>${SITE_NAME}</b><span>isometric maps of real places</span></a>${nav.length ? `<nav aria-label="Site">${nav.join('')}</nav>` : ''}</header>\n`
}

/** The footer: who draws the maps and how, the credits, every content page. */
const footer = (ctx: Ctx): string => {
  const u = up(ctx.depth)
  const links = ctx.pages.filter((p) => !p.unlisted).map((p) => {
    const path = ctx.plan.forPage(p.slug)
    return path === undefined ? '' : `<a href="${escAttr(u + path)}">${escapeHtml(p.title)}</a>`
  }).filter((x) => x !== '')
  const statement = ctx.plan.forPage('artist-statement')
  return `<footer class="foot">
<p>Maps by ${AUTHOR}, drawn with isoscape, a free, open-source tool he built with Claude${statement === undefined ? '' : ` (see the <a href="${escAttr(u + statement)}">artist statement</a>)`}, from OpenStreetMap and public elevation data. Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors (ODbL).</p>
<p><a href="${u}index.html">Open the explorer</a>${links.length ? ` · ${links.join(' · ')}` : ''} · <a href="https://github.com/busse/isoscape">isoscape on GitHub</a></p>
</footer>
`
}

const person = (ctx: Ctx) => {
  const about = ctx.plan.forPage('about')
  return { '@type': 'Person', name: AUTHOR, ...(about !== undefined && ctx.config.siteUrl !== undefined ? { url: siteHref(`${about}#contact`, ctx.config.siteUrl) } : {}) }
}

const abs = (path: string, ctx: Ctx) => (ctx.config.siteUrl === undefined ? undefined : siteHref(path, ctx.config.siteUrl))

// ---- content pages ------------------------------------------------------------------------------

export interface ContentImages {
  /** The page's own link-preview image (`social:`), already written under out/. */
  readonly own?: Preview
  /** The site's flagship preview, for pages without their own. */
  readonly flagship?: Preview
  readonly flagshipAlt?: string
}

const ENTITIES: Readonly<Record<string, string>> = { amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'", nbsp: ' ' }

/** Compiled HTML as plain text: tags dropped, entities read, white space collapsed. */
export const plainText = (html: string): string =>
  html.replace(/<[^>]*>/g, ' ').replace(/&(amp|lt|gt|quot|#39|nbsp);/g, (_, e: string) => ENTITIES[e] ?? '').replace(/\s+/g, ' ').replace(/ ([.,;:!?)])/g, '$1').replace(/\( /g, '(').trim()

/**
 * The questions of a compiled page and their answers: every heading whose text ends in a question
 * mark, with the text under it up to the next heading of any level. For FAQPage structured data.
 */
export const faqEntries = (html: string): { question: string; answer: string }[] => {
  const heads = [...html.matchAll(/<h([1-6])\b[^>]*>([\s\S]*?)<\/h\1>/g)]
  const out: { question: string; answer: string }[] = []
  heads.forEach((m, i) => {
    const question = plainText(m[2])
    if (!question.endsWith('?')) return
    const start = (m.index ?? 0) + m[0].length
    const end = i + 1 < heads.length ? heads[i + 1].index ?? html.length : html.length
    const answer = plainText(html.slice(start, end))
    if (answer !== '') out.push({ question, answer })
  })
  return out
}

/** A content page as a plain HTML document: `p/<slug>.html`. */
export const renderContentPage = (page: Page, ctx: Ctx, imgs: ContentImages = {}, modified?: string): string => {
  const path = ctx.plan.forPage(page.slug) ?? `p/${page.slug}.html`
  const description = pageDescription(page)
  const image = imgs.own ?? imgs.flagship
  const imageAlt = imgs.own === undefined ? imgs.flagshipAlt : page.summary ?? page.title
  const shop = pageShop(page.slug, mapRefs(page.html), ctx.config)
  const acts = `<p class="acts"><a class="btn ghost" href="../index.html#/${escAttr(page.slug)}">Open this in the explorer</a>${shop === undefined ? '' : ` <a class="btn" href="${escAttr(withCampaign(shop.url, page.slug, ctx.config.shop?.url))}">${escapeHtml(shop.label)}</a>`}</p>\n`
  const url = abs(path, ctx)
  const faq = page.schema === 'FAQPage' ? faqEntries(page.html) : []
  const ld = {
    '@context': 'https://schema.org',
    ...(faq.length > 0
      ? { '@type': 'FAQPage', name: page.title, mainEntity: faq.map((q) => ({ '@type': 'Question', name: q.question, acceptedAnswer: { '@type': 'Answer', text: q.answer } })) }
      : { '@type': 'Article', headline: page.title }),
    description,
    author: person(ctx),
    inLanguage: 'en',
    ...(image === undefined || ctx.config.siteUrl === undefined ? {} : { image: siteHref(image.path, ctx.config.siteUrl) }),
    ...(url === undefined ? {} : { url, mainEntityOfPage: url }),
    ...(modified === undefined ? {} : { dateModified: modified }),
    isPartOf: { '@type': 'WebSite', name: SITE_NAME, ...(ctx.config.siteUrl === undefined ? {} : { url: ctx.config.siteUrl }) },
  }
  return head({ title: `${page.title} · ${SITE_NAME}`, description, path, type: 'article', ld, ...(page.unlisted ? { noindex: true } : {}), ...(image === undefined ? {} : { image }), ...(imageAlt === undefined ? {} : { imageAlt }) }, ctx) +
    topBar(ctx, page.slug) +
    `<main class="wrap">\n${acts}<article class="prose">\n${page.html}</article>\n${acts}</main>\n` +
    footer(ctx) + '</body>\n</html>\n'
}

// ---- map pages ----------------------------------------------------------------------------------

/** Meaningful alt text for a map's picture. */
export const mapAlt = (b: BuildMeta): string => {
  const place = titleOf(b)
  const t = b.time
  return `Isometric map of ${place}${t && !place.includes(String(t.year)) ? ` as it stood in ${t.year}` : ''}${t?.title ? ` (${t.title})` : ''}: buildings, streets${b.config?.terrain ? ', water and the lie of the land' : ' and water'}, seen from above at an angle`
}

const storyFor = (b: BuildMeta, ctx: Ctx): string => {
  const slugs = new Set(ctx.pages.map((p) => p.slug))
  const u = up(ctx.depth)
  const story = makeStory({
    esc: (s) => escapeHtml(String(s ?? '')),
    label: (x) => {
      const y = x as BuildMeta
      return y.note || y.git?.subject || y.region
    },
    when: (iso) => new Date(iso).toLocaleDateString('en-US', { dateStyle: 'long', timeZone: 'UTC' }),
    mb: (n) => `${(n / 1e6).toFixed(2)} MB`,
    fmt: (v) => (v === undefined ? '–' : typeof v === 'number' ? (Number.isInteger(v) ? v.toLocaleString('en-US') : v.toFixed(2)) : escapeHtml(String(v))),
    demSources: Object.fromEntries(Object.values(DEM_SOURCES).map((d) => [d.id, { name: d.name, coverage: d.coverage, about: d.about, credit: d.credit, license: d.license }])),
    pageHref: (slug, section) => (slugs.has(slug) ? `${u}p/${slug}.html${section ? `#${section}` : ''}` : null),
  })
  // A build's note says what was being tried, which is for the explorer, not a public page.
  return story({ ...b, note: undefined })
}

/** The other maps in the same front-page section, for "More in …". */
const siblings = (e: MapEntry | SeriesEntry, ctx: Ctx): { title: string; links: string[] } | undefined => {
  const sec = sectionOf(ctx.config.home, e.region)
  if (sec === undefined) return undefined
  const order = (r: string) => {
    const i = sec.order?.indexOf(r) ?? -1
    return i < 0 ? 1e6 : i
  }
  const others = ctx.plan.entries.filter((x): x is MapEntry | SeriesEntry =>
    (x.kind === 'series' || (x.kind === 'map' && x.series === undefined)) && x.region !== e.region && sectionOf(ctx.config.home, x.region) === sec)
    .sort((a, b) => order(a.region) - order(b.region) || mapTitle(a, ctx.config.home).localeCompare(mapTitle(b, ctx.config.home)))
  if (others.length === 0) return undefined
  return {
    title: sec.title,
    links: others.map((x) => `<li><a href="${escAttr(up(ctx.depth) + x.path)}">${escapeHtml(mapTitle(x, ctx.config.home))}</a></li>`),
  }
}

const drawnBy = (ctx: Ctx, dated: boolean): string => {
  const how = ctx.plan.forPage('how-its-made')
  return `<p class="plain">Drawn by ${AUTHOR} with isoscape, a free, open-source tool he built with Claude, from OpenStreetMap and public elevation data${how === undefined ? '' : `; <a href="${escAttr(up(ctx.depth) + how)}">how it's made</a>`}. In the explorer you can pan and zoom the full drawing${dated ? ', step through its years' : ''} and compare it with other maps.</p>\n`
}

const mapLd = (e: MapEntry | SeriesEntry, title: string, description: string, image: Preview | undefined, ctx: Ctx) => {
  const b = e.build
  const c = b.config as { center?: unknown } | undefined
  const center = Array.isArray(c?.center) && c.center.length === 2 && c.center.every((n) => typeof n === 'number') ? c.center as [number, number] : undefined
  const url = abs(e.path, ctx)
  return {
    '@context': 'https://schema.org',
    '@type': 'VisualArtwork',
    name: title,
    description,
    creator: person(ctx),
    artform: 'Map',
    artMedium: 'Digital drawing (SVG) made with isoscape, open-source software, from OpenStreetMap and public elevation data',
    dateCreated: b.createdAt.slice(0, 10),
    inLanguage: 'en',
    ...(image === undefined || ctx.config.siteUrl === undefined ? {} : { image: siteHref(image.path, ctx.config.siteUrl) }),
    ...(url === undefined ? {} : { url, mainEntityOfPage: url }),
    ...(e.kind === 'map' && e.year !== undefined ? { temporalCoverage: String(e.year) } : {}),
    ...(e.kind === 'series' && e.years.length > 0 ? { temporalCoverage: `${e.years[0].year}/${e.years[e.years.length - 1].year}` } : {}),
    contentLocation: { '@type': 'Place', name: titleOf(b), ...(center === undefined ? {} : { geo: { '@type': 'GeoCoordinates', latitude: center[1], longitude: center[0] } }) },
    isPartOf: { '@type': 'WebSite', name: SITE_NAME, ...(ctx.config.siteUrl === undefined ? {} : { url: ctx.config.siteUrl }) },
  }
}

/** A map's own page (one region, or one year of a series): `m/<region>.html`, `m/<region>-<year>.html`. */
export const renderMapPage = (e: MapEntry, ctx: Ctx, previews: ReadonlyMap<string, Preview | undefined>): string => {
  const home = ctx.config.home
  const b = e.build
  const u = up(ctx.depth)
  const title = mapTitle(e, home)
  const hero = e.series === undefined ? home?.heroes.find((h) => h.region === e.region) : undefined
  const sec = sectionOf(home, e.region)
  const card = buildCard(b)
  const description = clip(hero?.blurb ? `${hero.blurb} ${card.description}` : card.description, 300)
  const image = previews.get(b.id)
  const alt = mapAlt(b)
  const shop = shopFor(ctx.config, e.region, e.year)
  const explore = `${u}index.html${e.route}`
  const series = e.series === undefined ? undefined : ctx.plan.entries.find((x): x is SeriesEntry => x.kind === 'series' && x.path === e.series)
  const story = sec?.page === undefined ? undefined : sec.page.startsWith('#/') ? ctx.plan.forPage(sec.page.slice(2).split('/')[0]) : undefined
  const more = siblings(e, ctx)
  const t = b.time
  const body =
    `<main class="wrap wide">\n` +
    (series === undefined ? '' : `<p class="plain"><a href="${escAttr(u + series.path)}">${escapeHtml(mapTitle(series, home))}</a></p>\n`) +
    `<h1 class="title">${escapeHtml(title)}</h1>\n` +
    (hero?.blurb ? `<p class="lede">${escapeHtml(hero.blurb)}</p>\n` : t?.note ? `<p class="lede">${escapeHtml(t.note)}</p>\n` : '') +
    (image === undefined ? '' : `<figure class="pic"><a href="${escAttr(explore)}"><img src="${escAttr(u + image.path)}" width="${image.width}" height="${image.height}" alt="${escAttr(alt)}"></a><figcaption>${escapeHtml(statsLine(b))}</figcaption></figure>\n`) +
    `<p class="acts"><a class="btn${shop ? ' ghost' : ''}" href="${escAttr(explore)}">Explore this map</a>` +
    (shop === undefined ? '' : ` <a class="btn" href="${escAttr(withCampaign(shop.url, e.region, ctx.config.shop?.url))}">${escapeHtml(shop.label)}</a>`) +
    (story === undefined ? '' : ` <a class="btn ghost" href="${escAttr(u + story)}">${escapeHtml(sec?.pageLabel ?? 'Read the story')}</a>`) + `</p>\n` +
    (series === undefined ? '' : `<nav aria-label="Years"><ul class="years">${series.years.map((y) => `<li>${y.year === e.year ? `<span aria-current="page">${y.year}</span>` : `<a href="${escAttr(u + y.path)}"${y.build.time?.title ? ` title="${escAttr(y.build.time.title)}"` : ''}>${y.year}</a>`}</li>`).join('')}</ul></nav>\n`) +
    drawnBy(ctx, series !== undefined) +
    `<section aria-labelledby="made"><h2 class="sub" id="made">How this view was made</h2>\n${storyFor(b, ctx)}\n</section>\n` +
    (more === undefined ? '' : `<nav class="more" aria-labelledby="more"><h2 class="sub" id="more">More in ${escapeHtml(more.title)}</h2><ul>${more.links.join('')}</ul></nav>\n`) +
    `</main>\n`
  return head({ title: `${title} · ${SITE_NAME}`, description, path: e.path, type: 'article', ld: mapLd(e, title, description, image, ctx), ...(image === undefined ? {} : { image, imageAlt: alt }) }, ctx) +
    topBar(ctx, e.region) + body + footer(ctx) + '</body>\n</html>\n'
}

/** A dated series with its years: `m/<region>.html`. */
export const renderSeriesPage = (e: SeriesEntry, ctx: Ctx, previews: ReadonlyMap<string, Preview | undefined>): string => {
  const home = ctx.config.home
  const u = up(ctx.depth)
  const title = mapTitle(e, home)
  const hero = home?.heroes.find((h) => h.region === e.region)
  const sec = sectionOf(home, e.region)
  const first = e.years[0].year
  const last = e.years[e.years.length - 1].year
  const description = clip(`${hero?.blurb ?? sec?.blurb ?? `${titleOf(e.build)}, year by year.`} ${e.years.length} years, ${first} to ${last}, drawn from OpenStreetMap, public elevation data and dated sources.`, 300)
  const image = previews.get(e.build.id)
  const alt = mapAlt(e.build)
  const shop = shopFor(ctx.config, e.region)
  const explore = `${u}index.html${e.route}`
  const more = siblings(e, ctx)
  const body =
    `<main class="wrap wide">\n<h1 class="title">${escapeHtml(title)}</h1>\n` +
    `<p class="lede">${escapeHtml(hero?.blurb ?? sec?.blurb ?? `${titleOf(e.build)}, drawn as it stood in each of ${e.years.length} years from ${first} to ${last}.`)}</p>\n` +
    (image === undefined ? '' : `<figure class="pic"><a href="${escAttr(explore)}"><img src="${escAttr(u + image.path)}" width="${image.width}" height="${image.height}" alt="${escAttr(alt)}"></a><figcaption>${escapeHtml(statsLine(e.build))}</figcaption></figure>\n`) +
    `<p class="acts"><a class="btn${shop ? ' ghost' : ''}" href="${escAttr(explore)}">Explore this map: step through ${e.years.length} years</a>` +
    (shop === undefined ? '' : ` <a class="btn" href="${escAttr(withCampaign(shop.url, e.region, ctx.config.shop?.url))}">${escapeHtml(shop.label)}</a>`) + `</p>\n` +
    drawnBy(ctx, true) +
    `<h2 class="sub">The years</h2>\n<ul class="cards">${e.years.map((y) => {
      const p = y.build.files?.thumb ?? previews.get(y.build.id)?.path
      return `<li><a href="${escAttr(u + y.path)}">${p === undefined ? '' : `<img loading="lazy" src="${escAttr(u + p)}" alt="${escAttr(mapAlt(y.build))}">`}<b>${y.year}${y.build.time?.title ? `: ${escapeHtml(y.build.time.title)}` : ''}</b>${y.build.time?.note ? `<small>${escapeHtml(clip(y.build.time.note, 140))}</small>` : ''}</a></li>`
    }).join('')}</ul>\n` +
    (more === undefined ? '' : `<nav class="more" aria-labelledby="more"><h2 class="sub" id="more">More in ${escapeHtml(more.title)}</h2><ul>${more.links.join('')}</ul></nav>\n`) +
    `</main>\n`
  return head({ title: `${title} · ${SITE_NAME}`, description, path: e.path, type: 'website', ld: mapLd(e, title, description, image, ctx), ...(image === undefined ? {} : { image, imageAlt: alt }) }, ctx) +
    topBar(ctx, e.region) + body + footer(ctx) + '</body>\n</html>\n'
}

// ---- the sitemap and the index's plain links ----------------------------------------------------

const xmlEsc = (s: string) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[c] ?? c)

/** sitemap.xml for these absolute URLs, each once, in order. */
export const sitemapXml = (urls: readonly { readonly loc: string; readonly lastmod?: string }[]): string => {
  const seen = new Set<string>()
  const rows: string[] = []
  for (const u of urls) {
    if (seen.has(u.loc)) continue
    seen.add(u.loc)
    rows.push(`  <url><loc>${xmlEsc(u.loc)}</loc>${u.lastmod ? `<lastmod>${xmlEsc(u.lastmod)}</lastmod>` : ''}</url>\n`)
  }
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${rows.join('')}</urlset>\n`
}

/** A plain link to every static page, grouped as the front page groups them, for index.html. */
export interface PlainLinks {
  readonly title: string
  readonly links: readonly { readonly href: string; readonly label: string }[]
}

export const plainLinks = (plan: StaticPlan, pages: readonly Page[], home?: HomeConfig): PlainLinks[] => {
  const groups: PlainLinks[] = []
  const pageLinks = pages.filter((p) => !p.unlisted).map((p) => ({ href: plan.forPage(p.slug) ?? '', label: p.title })).filter((l) => l.href !== '')
  if (pageLinks.length) groups.push({ title: 'Pages', links: pageLinks })
  const maps = plan.entries.filter((e): e is MapEntry | SeriesEntry => e.kind !== 'page')
  const label = (e: MapEntry | SeriesEntry) => mapTitle(e, home)
  const heroes = new Set(home?.heroes.map((h) => h.region) ?? [])
  const bySection = new Map<string, (MapEntry | SeriesEntry)[]>()
  for (const e of maps) {
    const key = heroes.has(e.region) ? 'Featured' : sectionOf(home, e.region)?.title ?? 'Other maps'
    if (!bySection.has(key)) bySection.set(key, [])
    bySection.get(key)?.push(e)
  }
  const keys = ['Featured', ...(home?.sections.map((s) => s.title) ?? []), 'Other maps']
  for (const k of keys) {
    const es = bySection.get(k)
    if (es === undefined) continue
    groups.push({ title: k, links: es.map((e) => ({ href: e.path, label: label(e) })) })
  }
  return groups
}

// ---- writing it all -----------------------------------------------------------------------------

/** The date each page file was last committed (YYYY-MM-DD), where git knows it. */
export const pageDates = async (pages: readonly Page[], root = process.cwd()): Promise<Map<string, string>> => {
  const out = new Map<string, string>()
  for (const p of pages) {
    try {
      const { stdout } = await run('git', ['log', '-1', '--format=%cs', '--', p.file], { cwd: root, timeout: 10_000 })
      if (/^\d{4}-\d{2}-\d{2}$/.test(stdout.trim())) out.set(p.slug, stdout.trim())
    } catch {
      // not a checkout: no date
    }
  }
  return out
}

export interface StaticResult {
  /** Paths under out/ of every file written, the sitemap included. */
  readonly files: readonly string[]
  readonly bytes: number
}

/**
 * Write every static page in the plan, the images the content pages use, and sitemap.xml (when
 * the site URL is known). Pages left from regions or content pages that are gone are removed.
 */
export const writeStatic = async (
  outDir: string,
  builds: readonly BuildMeta[],
  plan: StaticPlan,
  config: SiteConfig,
  opts: { readonly pagesDir?: string; readonly dates?: ReadonlyMap<string, string> } = {},
): Promise<StaticResult> => {
  const dir = opts.pagesDir ?? PAGES_DIR
  const slugs = plan.entries.filter((e): e is PageEntry => e.kind === 'page').map((e) => e.slug)
  const { pages, images } = loadStaticPages(slugs, dir, config.siteUrl, config.shop?.url)
  const files: string[] = []
  let bytes = 0
  const put = async (path: string, data: string | Buffer) => {
    await mkdir(resolve(outDir, path, '..'), { recursive: true })
    await writeFile(resolve(outDir, path), data)
    files.push(path)
    bytes += typeof data === 'string' ? Buffer.byteLength(data) : data.length
  }
  const previews = new Map<string, Preview | undefined>()
  for (const e of plan.entries) {
    if (e.kind === 'page') continue
    for (const b of e.kind === 'series' ? [e.build, ...e.years.map((y) => y.build)] : [e.build]) if (!previews.has(b.id)) previews.set(b.id, await previewOf(outDir, b))
  }
  const flag = flagshipOf(builds, config.flagship)
  const flagPreview = flag === undefined ? undefined : previews.get(flag.id) ?? await previewOf(outDir, flag)
  for (const name of images) await put(`p/${name}`, await readFile(resolve(dir, name)))
  for (const e of plan.entries) {
    const ctx: Ctx = { config, plan, pages, depth: e.path.split('/').length - 1 }
    if (e.kind === 'page') {
      const page = pages.find((p) => p.slug === e.slug)
      if (page === undefined) continue
      let own: Preview | undefined
      const size = page.social === undefined ? undefined : imageSize(page.social.bytes)
      if (page.social !== undefined && size !== undefined) {
        const path = `s/page-${page.slug}${extname(page.social.name).toLowerCase().replace('.jpeg', '.jpg')}`
        await mkdir(resolve(outDir, 's'), { recursive: true })
        await writeFile(resolve(outDir, path), page.social.bytes)
        own = { path, ...size }
      }
      await put(e.path, renderContentPage(page, ctx, {
        ...(own === undefined ? {} : { own }),
        ...(flagPreview === undefined ? {} : { flagship: flagPreview }),
        ...(flag === undefined ? {} : { flagshipAlt: mapAlt(flag) }),
      }, opts.dates?.get(page.slug)))
    } else if (e.kind === 'series') await put(e.path, renderSeriesPage(e, ctx, previews))
    else await put(e.path, renderMapPage(e, ctx, previews))
  }
  // Pages of regions or content pages that no longer exist.
  for (const sub of ['m', 'p']) {
    let have: string[] = []
    try {
      have = await readdir(resolve(outDir, sub))
    } catch {
      continue
    }
    for (const f of have) if (f.endsWith('.html') && !files.includes(`${sub}/${f}`)) await rm(resolve(outDir, sub, f), { force: true })
  }
  if (config.siteUrl !== undefined) {
    const base = config.siteUrl
    const day = (iso: string) => iso.slice(0, 10)
    const newestDay = builds.length ? day(newest(builds).createdAt) : undefined
    const hidden = new Set(pages.filter((p) => p.unlisted).map((p) => p.slug))
    const urls = [{ loc: base, ...(newestDay === undefined ? {} : { lastmod: newestDay }) }, ...plan.entries.filter((e) => e.kind !== 'page' || !hidden.has(e.slug)).map((e) => {
      const lastmod = e.kind === 'page' ? opts.dates?.get(e.slug) : day(e.kind === 'series' ? newest(e.years.map((y) => y.build)).createdAt : e.build.createdAt)
      return { loc: siteHref(e.path, base), ...(lastmod === undefined ? {} : { lastmod }) }
    })]
    await put('sitemap.xml', sitemapXml(urls))
  }
  return { files, bytes }
}
