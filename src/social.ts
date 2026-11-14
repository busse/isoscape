/**
 * Link previews. Social crawlers (Slack, iMessage, X, Facebook, LinkedIn, Discord…) run no
 * script and ignore the URL fragment, so every explorer route (`index.html#<id>@…`) would
 * preview as the bare index page. So each build, and each content page, also gets a tiny
 * static share page, `out/s/<id>.html` / `out/s/page-<slug>.html`, carrying its own Open Graph
 * and Twitter card tags, and a script that sends a visitor on to the explorer, keeping any
 * fragment they arrived with: `s/<id>.html#<id>@cx,cy,z` opens that exact view.
 *
 * Each build gets a 1200×630 preview image, `out/builds/<id>/social.png`: the picture cropped
 * (not letterboxed) to 1.91:1 around its centre, rasterised with rsvg-convert, else headless
 * Chrome. Without either, the thumbnail stands in.
 *
 * Open Graph wants absolute URLs. The site's public address comes from `--site-url`, else
 * `ISOSCAPE_SITE_URL`, else `siteUrl` in `isoscape.config.json`; without one, URLs are
 * relative (which some clients accept, and which work once deployed under the same path).
 */

import { execFile } from 'node:child_process'
import { access, mkdir, open, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
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
  /** Optional shop for prints: a header link, plus a "Buy a print" link on views whose region starts with a key of `links`. */
  readonly shop?: { readonly label: string; readonly url: string; readonly cta?: string; readonly links?: Readonly<Record<string, string>> }
  /** Optional front page for the explorer: featured views, then the rest in sections. */
  readonly home?: HomeConfig
  /** False on a published site that does not carry out/<region>.html, to hide the "Latest page" link. */
  readonly latestPages?: boolean
}

/** A featured view on the explorer's front page: the newest build of `region` (or its `year`, in a dated series). */
export interface HomeHero {
  readonly region: string
  readonly year?: number
  readonly title: string
  readonly blurb?: string
  /** Where "Buy a print" goes for this view; else the shop's `links` by region prefix. */
  readonly shop?: string
  /** The shop button's text for this view (default "Buy a print ↗"), e.g. when the link is a collection rather than this map. */
  readonly shopLabel?: string
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
  readonly shop?: string
  readonly shopLabel?: string
}

export interface HomeConfig {
  readonly title: string
  readonly intro?: string
  readonly heroes: readonly HomeHero[]
  readonly sections: readonly HomeSection[]
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

const isShop = (v: unknown): v is NonNullable<SiteConfig['shop']> =>
  typeof v === 'object' && v !== null && typeof (v as { label?: unknown }).label === 'string' && typeof (v as { url?: unknown }).url === 'string'

const isHome = (v: unknown): v is HomeConfig => {
  if (typeof v !== 'object' || v === null) return false
  const h = v as { title?: unknown; heroes?: unknown; sections?: unknown }
  return typeof h.title === 'string' && Array.isArray(h.heroes) && Array.isArray(h.sections) &&
    h.heroes.every((x) => typeof x === 'object' && x !== null && typeof (x as HomeHero).region === 'string' && typeof (x as HomeHero).title === 'string') &&
    h.sections.every((x) => typeof x === 'object' && x !== null && typeof (x as HomeSection).title === 'string' && Array.isArray((x as HomeSection).prefixes))
}

/** `--site-url`, else ISOSCAPE_SITE_URL, else isoscape.config.json in `root`. */
export const loadSiteConfig = async (flag?: string, root = process.cwd(), env = process.env): Promise<SiteConfig> => {
  let file: { siteUrl?: unknown; flagship?: unknown; shop?: unknown; home?: unknown; latestPages?: unknown } = {}
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
    ...(isShop(file.shop) ? { shop: file.shop } : {}),
    ...(isHome(file.home) ? { home: file.home } : {}),
    ...(file.latestPages === false ? { latestPages: false } : {}),
  }
}

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
  readonly type?: 'website' | 'article'
}

/** The head tags for a card: description, canonical, Open Graph and Twitter. */
export const metaTags = (c: Card): string => {
  const m = (attr: 'name' | 'property', key: string, value: string | number | undefined) =>
    value === undefined || value === '' ? '' : `<meta ${attr}="${key}" content="${escAttr(String(value))}">\n`
  return (
    m('name', 'description', c.description) +
    (c.url === undefined ? '' : `<link rel="canonical" href="${escAttr(c.url)}">\n`) +
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
export const sharePage = (card: Card, route: string): string => {
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
</body>
</html>
`
}

/** The share page's file name (in out/s/) for a build or a content page. */
export const shareFile = (target: { build: string } | { page: string }): string =>
  'build' in target ? `${target.build}.html` : `page-${target.page}.html`

// ---- preview images -----------------------------------------------------------------------------

/**
 * The part of a viewBox shown at 1200×630: the full height or width, whichever fits, cut to
 * 1.91:1 around the centre. Cutting height, the sky above goes before the ground below. A
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

/** What is installed to rasterise SVG: rsvg-convert, else a headless Chrome, else nothing. */
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

/** Render `svgPath` to a 1200×630 PNG at `pngPath`. False when nothing could rasterise it. */
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

/** The best preview image a build has on disk: social.png, else its thumbnail. */
export const previewOf = async (outDir: string, b: BuildMeta): Promise<Preview | undefined> => {
  for (const path of [`builds/${b.id}/social.png`, b.files?.thumb]) {
    if (path === undefined) continue
    const size = await pngSize(resolve(outDir, path))
    if (size !== undefined) return { path, ...size }
  }
  return undefined
}

/** The site's preview build: the newest of the configured flagship, else the newest build. */
export const flagshipOf = (builds: readonly BuildMeta[], flagship?: string): BuildMeta | undefined =>
  (flagship === undefined ? undefined : builds.find((b) => b.id === flagship || b.region === flagship || b.name === flagship)) ?? builds[0]

/** What index.html needs to carry the site-wide card. */
export interface SiteCard {
  readonly siteUrl?: string
  readonly shop?: SiteConfig['shop']
  readonly home?: HomeConfig
  readonly latestPages?: boolean
  readonly image?: Preview
  readonly imageAlt?: string
}

/** The site-wide tags for index.html (which sits at out/, depth 0). */
export const siteTags = (site: SiteCard, buildCount: number): string =>
  metaTags({
    title: `${SITE_NAME}: isometric views of real places`,
    description: `Isometric dot-and-line drawings of real places, built from OpenStreetMap and public elevation data${buildCount > 1 ? `: ${buildCount} views, with how each was made` : ''}.`,
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
): Promise<SiteCard & { rendered: number; missing: number }> => {
  const base = config.siteUrl
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
  await mkdir(resolve(outDir, 's'), { recursive: true })
  const previews = new Map<string, Preview | undefined>()
  for (const b of builds) {
    const preview = await previewOf(outDir, b)
    previews.set(b.id, preview)
    const { title, description, alt } = buildCard(b)
    const file = shareFile({ build: b.id })
    await writeFile(resolve(outDir, 's', file), sharePage({
      title, description, type: 'article',
      ...(preview === undefined ? {} : { image: siteHref(preview.path, base, 1), imageWidth: preview.width, imageHeight: preview.height, imageAlt: alt }),
      ...(base === undefined ? {} : { url: siteHref(`s/${file}`, base) }),
    }, `#${b.id}`))
  }
  const flag = flagshipOf(builds, config.flagship)
  const image = flag === undefined ? undefined : previews.get(flag.id)
  const imageAlt = flag === undefined ? undefined : buildCard(flag).alt
  for (const p of pages) {
    const file = shareFile({ page: p.slug })
    await writeFile(resolve(outDir, 's', file), sharePage({
      title: `${p.title} · ${SITE_NAME}`,
      description: clip(p.summary ?? firstParagraph(p.html), 300),
      type: 'article',
      ...(image === undefined ? {} : { image: siteHref(image.path, base, 1), imageWidth: image.width, imageHeight: image.height, ...(imageAlt === undefined ? {} : { imageAlt }) }),
      ...(base === undefined ? {} : { url: siteHref(`s/${file}`, base) }),
    }, `#/${p.slug}`))
  }
  return {
    ...(base === undefined ? {} : { siteUrl: base }),
    ...(image === undefined ? {} : { image }),
    ...(imageAlt === undefined ? {} : { imageAlt }),
    rendered,
    missing,
  }
}
