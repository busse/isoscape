import { test } from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, normalize } from 'node:path'
import type { BuildMeta } from '../src/archive.ts'
import { renderExplorer } from '../src/explorer.ts'
import { loadPages } from '../src/pages.ts'
import { anyOnSale, buyLinks, loadSiteConfig, onSaleUrl, pageShop, sectionShop, shopCta, shopFor, withCampaign, writeSocial, type SiteConfig } from '../src/social.ts'
import {
  loadStaticPages, mapRefs, plainLinks, planStatic, sitemapXml, staticRoute, writeStatic,
} from '../src/static-pages.ts'
import { makeStory } from '../src/story.ts'

const build = (id: string, region: string, createdAt: string, year?: number, extra: Partial<BuildMeta> = {}): BuildMeta => ({
  id, name: region + (year ? `-${year}` : ''), region, title: `Place ${region}${year ? `, ${year}` : ''}`, palette: 'paper', createdAt, viewBox: [0, 0, 2000, 1000], bearing: -8, ms: 1200, bytes: 2e6,
  stats: { buildings: 120, features: 900, heightFromTag: 10, heightFromLevels: 20, heightGuessed: 90, bridgePieces: 0, ground: 5, ribbons: 7 },
  config: { name: region, title: `Place ${region}`, center: [-77.44, 37.53], width: 1700, depth: 950, bearing: 0, scale: 2.4 },
  files: { svg: `builds/${id}/image.svg`, thumb: `builds/${id}/thumb.png` }, sky: '#fff', note: 'trying lighter foam',
  ...(year ? { time: { year, series: region, title: `Era ${year}`, note: `What ${year} was.`, curated: [] } } : {}),
  ...extra,
} as unknown as BuildMeta)

const BUILDS = [
  build('b3', 'town-time', '2026-03-03T00:00:00Z', 1925),
  build('b2', 'town-time', '2026-03-02T00:00:00Z', 1888),
  build('b1', 'town-time', '2026-03-01T00:00:00Z', 1925),
  build('l2', 'lm-tower', '2026-02-02T00:00:00Z'),
  build('l1', 'lm-tower', '2026-02-01T00:00:00Z'),
  build('s1', 'cars', '2026-01-01T00:00:00Z', 1925),
]

const CONFIG: SiteConfig = {
  siteUrl: 'https://example.org/iso/',
  analytics: { ga: 'G-ABC1234' },
  shop: { label: 'Shop', url: 'https://shop.example/', onSale: { 'lm-': 'https://shop.example/c/landmarks', cars: 'https://shop.example/c/cars', 'town-time': 'https://shop.example/c/town' } },
  home: {
    title: 'Home', heroes: [{ region: 'town-time', year: 1925, title: 'The town through time', blurb: 'Year by year.' }],
    sections: [{ title: 'Landmarks', prefixes: ['lm-'], page: '#/story', pageLabel: 'Read the story' }, { title: 'Cars', prefixes: ['cars'] }],
  },
}

const PAGES: Record<string, string> = {
  'story.md': '---\ntitle: The story\nsummary: How the cars ran.\n---\n\n# The story\n\nSee [the cars](https://example.org/iso/#cars:1925@1,2,3), [how](how-its-made.md#camera) and [below](#below). ![Plan](plan.svg)\n\nBuy at the [shop](https://shop.example/c/cars).\n\n## Below\n\nText.\n',
  'how-its-made.md': '---\ntitle: How it is made\n---\n\n# How it is made\n\n## Camera\n\n## Time\n\n## Inputs\n\n## Ground\n\n## Rapids\n\n## Rivers\n\n## Buildings\n\n## Bridges\n\n## Paint order\n\n## Drawing\n\n## Archive and explorer\n',
}

const site = () => {
  const out = mkdtempSync(join(tmpdir(), 'iso-static-'))
  const pagesDir = mkdtempSync(join(tmpdir(), 'iso-pages-'))
  writeFileSync(join(out, 'index.html'), '<!doctype html>')
  for (const [name, src] of Object.entries(PAGES)) writeFileSync(join(pagesDir, name), src)
  writeFileSync(join(pagesDir, 'plan.svg'), '<svg xmlns="http://www.w3.org/2000/svg"/>')
  // A 1×1 PNG header is all previewOf reads.
  const png = Buffer.alloc(24)
  png.writeUInt32BE(0x89504e47, 0)
  png.writeUInt32BE(1200, 16)
  png.writeUInt32BE(630, 20)
  for (const b of BUILDS) {
    mkdirSync(join(out, 'builds', b.id), { recursive: true })
    writeFileSync(join(out, 'builds', b.id, 'meta.json'), JSON.stringify(b))
    writeFileSync(join(out, 'builds', b.id, 'thumb.png'), png)
    writeFileSync(join(out, 'builds', b.id, 'social.png'), png)
  }
  return { out, pagesDir }
}

test('the plan names each region, and each year of a series, at a stable path', () => {
  const plan = planStatic(BUILDS, ['story'], CONFIG.home)
  const paths = plan.entries.map((e) => e.path)
  assert.deepEqual(paths.sort(), ['m/cars.html', 'm/lm-tower.html', 'm/town-time-1888.html', 'm/town-time-1925.html', 'm/town-time.html', 'p/story.html'])
  const series = plan.entries.find((e) => e.kind === 'series')
  assert.ok(series && series.kind === 'series')
  // The featured year leads, and each year shows its newest build.
  assert.equal(series.build.id, 'b3')
  assert.equal(series.route, '#town-time:1925')
  assert.equal(plan.forBuild(BUILDS[2]), 'm/town-time-1925.html')
  assert.equal(plan.forBuild(BUILDS[4]), 'm/lm-tower.html')
  // A one-year series is one page, routed by its year.
  assert.equal(plan.entries.find((e) => e.path === 'm/cars.html')?.route, '#cars:1925')
  assert.equal(plan.forPage('story'), 'p/story.html')
  // A year page never takes a region's address.
  const clash = planStatic([build('x', 'a', '2026-01-01T00:00:00Z', 1900), build('y', 'a', '2026-01-02T00:00:00Z', 1910), build('z', 'a-1900', '2026-01-03T00:00:00Z')], [])
  assert.deepEqual(clash.entries.map((e) => e.path).sort(), ['m/a-1900-map.html', 'm/a-1900.html', 'm/a-1910.html', 'm/a.html'])
})

test('links in a static page go to files, sections to anchors, maps to the explorer, and the shop gets its tags', () => {
  const slugs = new Set(['story', 'how-its-made'])
  assert.equal(staticRoute('#/how-its-made/camera', 'story', slugs), 'how-its-made.html#camera')
  assert.equal(staticRoute('#/story/below', 'story', slugs), '#below')
  assert.equal(staticRoute('#/gone', 'story', slugs), '../index.html#/gone')
  assert.equal(staticRoute('#cars:1925@1,2,3', 'story', slugs), '../index.html#cars:1925@1,2,3')
  assert.equal(staticRoute('https://shop.example/c/cars', 'story', slugs, 'https://shop.example/'), 'https://shop.example/c/cars?utm_source=isoscape-explorer&utm_medium=referral&utm_campaign=story')
  assert.equal(staticRoute('https://osm.org/x', 'story', slugs, 'https://shop.example/'), 'https://osm.org/x')
  assert.equal(withCampaign('https://shop.example/a?utm_source=x', 'p'), 'https://shop.example/a?utm_source=x')
  assert.equal(withCampaign('https://shop.example/a', 'Lm Tower:1925!', 'https://shop.example/'), 'https://shop.example/a?utm_source=isoscape-explorer&utm_medium=referral&utm_campaign=Lm-Tower-1925-')
  assert.deepEqual(shopFor(CONFIG, 'town-time'), { url: 'https://shop.example/c/town', label: 'Buy a print ↗' })
  assert.equal(shopFor(CONFIG, 'lm-tower')?.url, 'https://shop.example/c/landmarks')
  assert.equal(shopFor(CONFIG, 'elsewhere'), undefined)
  assert.deepEqual(mapRefs('<a href="../index.html#cars:1925@1">a</a><a href="../index.html#lm-tower">b</a><a href="#below">c</a><a href="../index.html#/how-its-made">d</a>'), ['cars', 'lm-tower'])
})

test('the static pages carry their text, head tags and JSON-LD, and every relative link resolves', async () => {
  const { out, pagesDir } = site()
  const plan = planStatic(BUILDS, ['how-its-made', 'story'], CONFIG.home)
  const result = await writeStatic(out, BUILDS, plan, CONFIG, { pagesDir, dates: new Map([['story', '2026-03-05']]) })

  const story = readFileSync(join(out, 'p', 'story.html'), 'utf8')
  assert.match(story, /<title>The story · isoscape<\/title>/)
  assert.match(story, /<meta name="description" content="How the cars ran\.">/)
  assert.match(story, /<link rel="canonical" href="https:\/\/example.org\/iso\/p\/story.html">/)
  assert.match(story, /<link rel="sitemap" type="application\/xml" title="Sitemap" href="..\/sitemap.xml">/)
  assert.match(story, /og:image" content="https:\/\/example.org\/iso\/builds\/b3\/social.png"/)
  // The whole page is in the document, with GitHub's anchors.
  assert.match(story, /<h2 id="below">Below<\/h2>/)
  assert.match(story, /<a class="btn ghost" href="\.\.\/index\.html#\/story">Open this in the explorer<\/a>/)
  assert.match(story, /href="https:\/\/shop.example\/c\/cars\?utm_source=isoscape-explorer&amp;utm_medium=referral&amp;utm_campaign=story">Prints of this map/)
  assert.match(story, /<img src="plan.svg" alt="Plan"/)
  assert.match(story, /gtag\('config', 'G-ABC1234'\)/)
  const ld = JSON.parse(story.match(/<script type="application\/ld\+json">(.*?)<\/script>/)?.[1] ?? 'null')
  assert.equal(ld['@type'], 'Article')
  assert.equal(ld.author.name, 'Chris Busse')
  assert.equal(ld.dateModified, '2026-03-05')
  assert.equal(ld.url, 'https://example.org/iso/p/story.html')

  const year = readFileSync(join(out, 'm', 'town-time-1925.html'), 'utf8')
  assert.match(year, /<h1 class="title">Place town-time, 1925: Era 1925<\/h1>/)
  assert.match(year, /<a class="btn ghost" href="\.\.\/index\.html#town-time:1925">Explore this map<\/a>/)
  assert.match(year, /href="https:\/\/shop.example\/c\/town\?utm_source=isoscape-explorer&amp;utm_medium=referral&amp;utm_campaign=town-time">Buy a print/)
  assert.match(year, /<span aria-current="page">1925<\/span>/)
  assert.match(year, /<a href="\.\.\/m\/town-time-1888\.html"/)
  assert.match(year, /alt="Isometric map of Place town-time as it stood in 1925 \(Era 1925\)/)
  // "How this view was made", from the same code as the explorer, linking the static pages.
  assert.match(year, /How this view was made/)
  assert.match(year, /<a href="\.\.\/p\/how-its-made\.html#time">how time is drawn →<\/a>/)
  // A build's working note stays in the explorer.
  assert.doesNotMatch(year, /lighter foam/)
  const art = JSON.parse(year.match(/<script type="application\/ld\+json">(.*?)<\/script>/)?.[1] ?? 'null')
  assert.equal(art['@type'], 'VisualArtwork')
  assert.equal(art.creator.name, 'Chris Busse')
  assert.equal(art.temporalCoverage, '1925')
  assert.deepEqual(art.contentLocation.geo, { '@type': 'GeoCoordinates', latitude: 37.53, longitude: -77.44 })
  assert.doesNotMatch(year, /by hand|hand-drawn/i)
  const landmark = readFileSync(join(out, 'm', 'lm-tower.html'), 'utf8')
  assert.match(landmark, /builds\/l2\/social\.png/)
  assert.match(landmark, /<a class="btn ghost" href="\.\.\/p\/story\.html">Read the story<\/a>/)

  // Every relative href and src lands on a file, and every anchor on an id there.
  const html = result.files.filter((f) => f.endsWith('.html'))
  assert.equal(html.length, 7)
  for (const f of html) {
    const text = readFileSync(join(out, f), 'utf8').replace(/<script\b[\s\S]*?<\/script>/g, '')
    for (const [, raw] of text.matchAll(/\b(?:href|src)="([^"]*)"/g)) {
      const href = raw.replace(/&amp;/g, '&')
      if (/^(https?:|data:|mailto:)/.test(href)) continue
      const [path, frag] = href.split('#')
      const target = path === '' ? join(out, f) : normalize(join(out, dirname(f), path))
      assert.ok(existsSync(target), `${f}: ${href} does not resolve`)
      if (frag && !target.endsWith('index.html')) assert.match(readFileSync(target, 'utf8'), new RegExp(`id="${frag}"`), `${f}: ${href} has no anchor`)
    }
  }

  // The sitemap lists index.html and every page once, with absolute URLs.
  const xml = readFileSync(join(out, 'sitemap.xml'), 'utf8')
  const locs = [...xml.matchAll(/<loc>(.*?)<\/loc>/g)].map((m) => m[1])
  assert.deepEqual([...locs].sort(), ['https://example.org/iso/', ...html.map((f) => `https://example.org/iso/${f}`)].sort())
  assert.match(xml, /<loc>https:\/\/example.org\/iso\/m\/town-time.html<\/loc><lastmod>2026-03-03<\/lastmod>/)
  assert.equal(sitemapXml([{ loc: 'https://x/a&b' }, { loc: 'https://x/a&b' }]).match(/<url>/g)?.length, 1)
  assert.match(sitemapXml([{ loc: 'https://x/a&b' }]), /<loc>https:\/\/x\/a&amp;b<\/loc>/)

  // A page that is gone takes its static page with it.
  await writeStatic(out, BUILDS.filter((b) => b.region !== 'cars'), planStatic(BUILDS.filter((b) => b.region !== 'cars'), ['how-its-made', 'story'], CONFIG.home), CONFIG, { pagesDir })
  assert.ok(!existsSync(join(out, 'm', 'cars.html')))
  assert.ok(readdirSync(join(out, 'm')).includes('lm-tower.html'))
})

test('share pages keep their addresses and forwarding, and name the static page as canonical', async () => {
  const { out, pagesDir } = site()
  const pages = loadPages(pagesDir, CONFIG.siteUrl)
  const plan = planStatic(BUILDS, pages.map((p) => p.slug), CONFIG.home)
  await writeSocial(out, BUILDS, pages, CONFIG, undefined, (t) => ('build' in t ? plan.forBuild(t.build) : plan.forPage(t.page)))
  for (const b of BUILDS) assert.ok(existsSync(join(out, 's', `${b.id}.html`)))
  const share = readFileSync(join(out, 's', 'b1.html'), 'utf8')
  assert.match(share, /<link rel="canonical" href="https:\/\/example.org\/iso\/m\/town-time-1925.html">/)
  assert.match(share, /<meta property="og:url" content="https:\/\/example.org\/iso\/s\/b1.html">/)
  assert.match(share, /location\.replace\('\.\.\/index\.html'/)
  assert.match(share, /<a href="\.\.\/m\/town-time-1925\.html">About this map<\/a>/)
  assert.match(readFileSync(join(out, 's', 'page-story.html'), 'utf8'), /<link rel="canonical" href="https:\/\/example.org\/iso\/p\/story.html">/)
})

test('the explorer lists the static pages in plain links, and the story runs outside the browser', () => {
  const { pagesDir } = site()
  const pages = loadStaticPages(['how-its-made', 'story'], pagesDir).pages
  const plan = planStatic(BUILDS, pages.map((p) => p.slug), CONFIG.home)
  const groups = plainLinks(plan, pages, CONFIG.home)
  assert.deepEqual(groups.map((g) => g.title), ['Pages', 'Featured', 'Landmarks', 'Cars'])
  const html = renderExplorer(BUILDS, pages, { plain: groups, sitemap: true })
  assert.match(html, /<details id="plain"><summary>Every map and page as a plain web page<\/summary>/)
  assert.match(html, /<li><a href="m\/town-time-1925\.html">Place town-time, 1925: Era 1925<\/a><\/li>/)
  assert.match(html, /<noscript>/)
  assert.match(html, /<link rel="sitemap" type="application\/xml" title="Sitemap" href="sitemap.xml">/)
  const script = html.match(/<script>\n([\s\S]*?)<\/script>/)
  assert.ok(script)
  assert.doesNotThrow(() => new Function(script[1]))
  const story = makeStory({
    esc: (s) => String(s), label: () => '', when: (iso) => iso.slice(0, 10), mb: (n) => `${n} B`, fmt: (v) => String(v),
    demSources: {}, pageHref: (slug, section) => `${slug}.html${section ? `#${section}` : ''}`,
  })
  const text = story(BUILDS[0])
  assert.match(text, /^<div class="story">/)
  assert.match(text, /120 buildings/)
  assert.match(text, /<a href="how-its-made.html#camera">how the camera works →<\/a>/)
})

test('what is on sale: the longest key a region, set or page slug starts with', () => {
  const onSale = { richmond: 'https://s/c/rva', 'richmond-streetcars': 'https://s/c/cars', 'broad-street-cutaway': 'https://s/p/cut' }
  assert.equal(onSaleUrl(onSale, 'richmond-downtown-time'), 'https://s/c/rva')
  assert.equal(onSaleUrl(onSale, 'richmond-streetcars'), 'https://s/c/cars')
  assert.equal(onSaleUrl(onSale, 'richmond-streetcars-west'), 'https://s/c/cars')
  assert.equal(onSaleUrl(onSale, 'broad-street-cutaway'), 'https://s/p/cut')
  // A key longer than the subject, or one it does not start with, is no match.
  assert.equal(onSaleUrl(onSale, 'broad-street'), undefined)
  assert.equal(onSaleUrl(onSale, 'broad-street-lines'), undefined)
  assert.equal(onSaleUrl(onSale, 'rich'), undefined)
  assert.equal(onSaleUrl({}, 'richmond'), undefined)
  assert.equal(onSaleUrl(undefined, 'richmond'), undefined)

  const config: SiteConfig = { shop: { label: 'L', url: 'https://s/', cta: 'Buy prints', onSale }, home: {
    title: 'H', heroes: [{ region: 'richmond-i195', title: 'I-195', shopLabel: 'Prints ↗' }],
    sections: [
      { title: 'Richmond', prefixes: ['richmond'], page: '#/streetcars' },
      { title: 'Buildings', prefixes: ['broad-street'], page: '#/broad-street' },
      { title: 'Mixed', prefixes: ['richmond', 'gwynns'] },
    ],
  } }
  assert.deepEqual(shopFor(config, 'richmond-i195'), { url: 'https://s/c/rva', label: 'Prints ↗' })
  assert.equal(shopFor(config, 'gwynns-island'), undefined)
  // A section: one URL for all its prefixes, else its story page's slug.
  assert.deepEqual(sectionShop(config, config.home!.sections[0]), { url: 'https://s/c/rva', label: 'Buy prints ↗' })
  assert.equal(sectionShop(config, config.home!.sections[1]), undefined)
  assert.equal(sectionShop(config, config.home!.sections[2]), undefined)
  assert.deepEqual(sectionShop({ shop: { label: 'L', url: 'https://s/', onSale: { streetcars: 'https://s/c/set' } } }, { ...config.home!.sections[0], shopLabel: 'Shop ↗' }), { url: 'https://s/c/set', label: 'Shop ↗' })
  // A page: its own slug first (the cutaway turns on by its slug alone), then its maps', then its section's.
  assert.deepEqual(pageShop('broad-street-cutaway', [], config), { url: 'https://s/p/cut', label: 'Buy a print ↗' })
  assert.equal(pageShop('broad-street', ['broad-street-lines'], config), undefined)
  assert.deepEqual(pageShop('streetcars', ['richmond-streetcars', 'richmond-streetcars-west'], config), { url: 'https://s/c/cars', label: 'Prints of these maps ↗' })
  assert.equal(pageShop('landmarks', ['richmond-streetcars', 'gwynns-island'], config), undefined)
  assert.deepEqual(pageShop('streetcars', [], config), { url: 'https://s/c/rva', label: 'Buy a print ↗' })
  assert.equal(shopCta(config), 'Buy prints')
  assert.deepEqual(buyLinks(config, ['richmond-i195', 'gwynns-island']), {
    regions: { 'richmond-i195': { url: 'https://s/c/rva', label: 'Prints ↗' } },
    sections: [{ url: 'https://s/c/rva', label: 'Buy prints ↗' }, null, null],
  })
})

test('with nothing on sale, no page links to anything in the shop but its front page', async () => {
  // The config as written: an empty onSale, and old per-view and per-section shop URLs and a
  // `links` map, which are ignored.
  const dir = mkdtempSync(join(tmpdir(), 'iso-cfg-'))
  writeFileSync(join(dir, 'isoscape.config.json'), JSON.stringify({
    siteUrl: 'https://example.org/iso/',
    shop: { label: 'Holiday shop', url: 'https://shop.example/', cta: 'Buy prints of these maps', links: { 'lm-': 'https://shop.example/c/landmarks' }, onSale: {} },
    home: { ...CONFIG.home, heroes: [{ ...CONFIG.home!.heroes[0], shop: 'https://shop.example/c/town' }], sections: CONFIG.home!.sections.map((s) => ({ ...s, shop: 'https://shop.example/c/sec', shopLabel: 'Shop ↗' })) },
  }))
  const config = await loadSiteConfig(undefined, dir, {})
  assert.equal(anyOnSale(config), false)
  assert.equal(shopCta(config), undefined)
  assert.deepEqual(config.shop?.onSale, {})
  assert.equal((config.shop as { links?: unknown }).links, undefined)
  assert.equal((config.home?.heroes[0] as { shop?: unknown }).shop, undefined)

  const { out, pagesDir } = site()
  // The story page as it should now be written: no sentence about prints.
  writeFileSync(join(pagesDir, 'story.md'), '---\ntitle: The story\n---\n\n# The story\n\nSee [the cars](https://example.org/iso/#cars:1925@1,2,3) and [the tower](https://example.org/iso/#lm-tower).\n')
  const pages = loadPages(pagesDir, config.siteUrl)
  const plan = planStatic(BUILDS, pages.map((p) => p.slug), config.home)
  await writeSocial(out, BUILDS, pages, config, undefined, (t) => ('build' in t ? plan.forBuild(t.build) : plan.forPage(t.page)))
  const result = await writeStatic(out, BUILDS, plan, config, { pagesDir })
  writeFileSync(join(out, 'index.html'), renderExplorer(BUILDS, pages, { shop: config.shop, home: config.home, plain: plainLinks(plan, pages, config.home) }))
  const files = ['index.html', ...result.files.filter((f) => f.endsWith('.html')), ...readdirSync(join(out, 's')).map((f) => `s/${f}`)]
  assert.ok(files.length > 10)
  for (const f of files) {
    const text = readFileSync(join(out, f), 'utf8')
    for (const [m] of text.matchAll(/https:\/\/shop\.example[^"'\s<)\\]*/g)) {
      assert.ok(/^https:\/\/shop\.example\/(\?utm_source=isoscape-explorer&(amp;)?utm_medium=referral&(amp;)?utm_campaign=[a-z0-9-]+)?$/i.test(m), `${f}: ${m}`)
    }
    const hit = text.match(/.{80}(Buy a print|Prints of th|Buy prints of these maps|Shop ↗).{40}/)
    assert.equal(hit, null, `${f}: ${hit?.[0]}`)
  }
  const index = readFileSync(join(out, 'index.html'), 'utf8')
  assert.match(index, /<a class="shop" href="https:\/\/shop.example\/"[^>]*><b>Shop prints ↗<\/b><span>Holiday shop<\/span><\/a>/)
  assert.match(index, /"buy":\{"regions":\{\},"sections":\[null,null\]\}/)
  assert.match(readFileSync(join(out, 'p', 'story.html'), 'utf8'), /<p class="acts"><a class="btn ghost" href="\.\.\/index\.html#\/story">Open this in the explorer<\/a><\/p>/)
})
