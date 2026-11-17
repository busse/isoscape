#!/usr/bin/env node
/**
 * Browser check of the explorer's addresses and Link buttons, in headless Chrome, offline.
 *
 *   node tools/check/browser.mjs <site-dir> [--out out/check/browser] [--only desktop|phone]
 *
 * Serves <site-dir> (an `isoscape explorer` output, e.g. a copy of the published site) at
 * http://127.0.0.1:<port>/isoscape/, as GitHub Pages serves it under a path, and blocks every
 * request to any other host. Then, on a desktop window and on a phone-sized one, it opens the
 * front page, follows in-app links to a content page, a map, a year of a series and a set page,
 * goes Back and Forward, reloads each kind of share address, opens old-style '#…' links, the
 * static pages' links into the explorer, presses Link / Copy link and fetches what it copied
 * as a crawler would (the site URL mapped to the local server), and checks the shop link's
 * campaign tags. Screenshots go to --out. Prints PASS/FAIL per check; exits 1 on any FAIL.
 *
 * Needs playwright-core (found by `import`, or at $PLAYWRIGHT_CORE, a path to its folder) and
 * Chrome ($CHROME, else google-chrome or chromium on the PATH). Without either it says
 * "skipped" and exits 0. Not a dependency of isoscape: install playwright-core anywhere.
 */
import { createServer } from 'node:http'
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { extname, join, normalize, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { execFileSync } from 'node:child_process'

const args = process.argv.slice(2)
const flag = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args.splice(i, 2)[1] : dflt }
const OUT = resolve(flag('--out', 'out/check/browser'))
const ONLY = flag('--only', '')
const SITE = args[0] ? resolve(args[0]) : ''
if (!SITE || !existsSync(join(SITE, 'index.html'))) {
  console.error('usage: node tools/check/browser.mjs <site-dir> [--out dir] [--only desktop|phone]')
  process.exit(2)
}

// ---- what is needed, else skip -------------------------------------------------------------------
const loadPlaywright = async () => {
  for (const spec of [process.env.PLAYWRIGHT_CORE && pathToFileURL(join(process.env.PLAYWRIGHT_CORE, 'index.js')).href, 'playwright-core'].filter(Boolean)) {
    try { return (await import(spec)).default ?? (await import(spec)) } catch { /* next */ }
  }
  return null
}
const findChrome = () => {
  for (const c of [process.env.CHROME, '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'].filter(Boolean)) {
    if (existsSync(c)) return c
  }
  for (const c of ['google-chrome', 'chromium', 'chromium-browser']) {
    try { return execFileSync('which', [c], { encoding: 'utf8' }).trim() || null } catch { /* next */ }
  }
  return null
}
const pw = await loadPlaywright()
const chromePath = findChrome()
if (!pw || !chromePath) {
  console.log(`skipped: ${!pw ? 'playwright-core not found (set PLAYWRIGHT_CORE to its folder)' : 'no Chrome found (set CHROME)'}`)
  process.exit(0)
}

// ---- the site, served under /isoscape/ ----------------------------------------------------------
const TYPES = { '.html': 'text/html; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json', '.xml': 'application/xml', '.webp': 'image/webp', '.js': 'text/javascript', '.css': 'text/css' }
const PREFIX = '/isoscape/'
const server = createServer((req, res) => {
  const u = new URL(req.url, 'http://x')
  if (!u.pathname.startsWith(PREFIX)) { res.writeHead(u.pathname === '/isoscape' ? 301 : 404, u.pathname === '/isoscape' ? { location: PREFIX } : {}); res.end(); return }
  let p = normalize(join(SITE, decodeURIComponent(u.pathname.slice(PREFIX.length))))
  if (!p.startsWith(SITE)) { res.writeHead(403); res.end(); return }
  if (existsSync(p) && statSync(p).isDirectory()) p = join(p, 'index.html')
  if (!existsSync(p)) { res.writeHead(404); res.end('not found'); return }
  res.writeHead(200, { 'content-type': TYPES[extname(p)] ?? 'application/octet-stream' })
  res.end(req.method === 'HEAD' ? undefined : readFileSync(p))
})
await new Promise((r) => server.listen(0, '127.0.0.1', r))
const ORIGIN = `http://127.0.0.1:${server.address().port}`
const BASE = ORIGIN + PREFIX
const indexHtml = readFileSync(join(SITE, 'index.html'), 'utf8')
const SITE_URL = (/<meta property="og:url" content="([^"]+)">/.exec(indexHtml) ?? [])[1] ?? BASE
const local = (u) => (u && u.startsWith(SITE_URL) ? BASE + u.slice(SITE_URL.length) : u)
const data = (id) => JSON.parse((new RegExp(`<script type="application/json" id="${id}">([\\s\\S]*?)</script>`).exec(indexHtml) ?? [])[1] ?? 'null')
const builds = data('builds') ?? []
const site = data('site') ?? {}
const newest = (pred) => builds.filter(pred).sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1))[0]

// The entries the checks use, from what the site holds.
const series = builds.find((b) => b.time && builds.filter((x) => x.region === b.region && x.time).map((x) => x.time.year).filter((y, i, a) => a.indexOf(y) === i).length > 1)?.region
const YEAR = series ? newest((b) => b.region === series && b.time.year === (site.home?.heroes?.find((h) => h.region === series)?.year ?? b.time.year)) : null
const MAP = newest((b) => b.region === 'lm-eiffel-tower') ?? newest((b) => !b.time)
const OTHER = newest((b) => !b.time && b.region !== MAP.region)
const pageSlugs = (data('pagesData') ?? []).map((p) => p.slug)
const CUTAWAY = pageSlugs.includes('broad-street-cutaway') ? 'broad-street-cutaway' : pageSlugs[0]
const SET = pageSlugs.find((s) => s === 'streetcars') ?? pageSlugs.find((s) => s !== CUTAWAY)
const ids = new Set(builds.map((b) => b.id))
const STALE = readdirSync(join(SITE, 's')).find((f) => /^\d{8}-\d{6}-.+\.html$/.test(f) && !ids.has(f.slice(0, -5)))
const doorOf = (key) => site.shares?.maps?.[key]

// ---- reporting ------------------------------------------------------------------------------------
mkdirSync(OUT, { recursive: true })
let failed = 0
const report = (ok, name, detail) => {
  if (!ok) failed++
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? `: ${detail}` : ''}`)
}
const eq = (name, got, want) => report(got === want, name, got === want ? String(got) : `got ${got}, want ${want}`)

// ---- one browser context: a desktop window or a phone ---------------------------------------------
const browser = await pw.chromium.launch({ executablePath: chromePath, headless: true, args: ['--no-sandbox'] })

const session = async (kind) => {
  const phone = kind === 'phone'
  const context = await browser.newContext(phone
    ? { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }
    : { viewport: { width: 1400, height: 900 } })
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: ORIGIN })
  // What a phone's share sheet is given, kept for the checks (headless has no sheet to show).
  await context.addInitScript(() => {
    window.__shared = []
    navigator.share = (d) => { window.__shared.push(d.url); return Promise.resolve() }
  })
  await context.route('**/*', (route) => (route.request().url().startsWith(ORIGIN) ? route.continue() : route.abort()))
  const page = await context.newPage()
  const errors = []
  const missing = []
  page.on('pageerror', (e) => errors.push(String(e)))
  page.on('console', (m) => { if (m.type() === 'error' && !/ERR_FAILED|ERR_BLOCKED|net::/.test(m.text())) errors.push(m.text()) })
  page.on('response', (r) => { if (r.url().startsWith(ORIGIN) && r.status() >= 400) missing.push(`${r.status()} ${r.url().slice(ORIGIN.length)}`) })
  const settle = async () => {
    await page.waitForLoadState('load')
    await page.waitForFunction(() => {
      const img = document.getElementById('imgA')
      const viewer = !document.body.classList.contains('home') && !document.body.classList.contains('reading')
      return !viewer || !img || !img.getAttribute('src') || img.complete
    }, null, { timeout: 60_000 }).catch(() => undefined)
    await page.waitForTimeout(400)
  }
  const view = () => page.evaluate(() => {
    const b = document.body.classList
    const img = document.getElementById('imgA')
    return {
      url: location.href,
      canonical: document.querySelector('link[rel="canonical"]')?.getAttribute('href') ?? null,
      mode: b.contains('home') ? 'home' : b.contains('reading') ? 'page' : 'viewer',
      slug: b.contains('reading') ? document.getElementById('article')?.dataset.slug ?? null : null,
      img: b.contains('home') || b.contains('reading') ? null : (img?.getAttribute('src') ?? null),
      imgOk: img ? img.complete && img.naturalWidth > 0 : false,
      title: document.getElementById('infoTitle')?.textContent ?? '',
      history: history.length,
    }
  })
  const shot = async (name) => page.screenshot({ path: join(OUT, `${kind}-${name}.png`) })
  // Follow an in-app link as a click would (the link on the page, else one made for the purpose).
  const follow = async (href) => {
    await page.evaluate((h) => {
      let a = [...document.querySelectorAll('a')].find((x) => x.getAttribute('href') === h && x.offsetParent !== null)
      if (!a) { a = document.createElement('a'); a.setAttribute('href', h); a.textContent = 'x'; document.body.appendChild(a) }
      a.click()
    }, href)
    await settle()
  }
  const copyLink = async () => {
    await page.evaluate(() => navigator.clipboard.writeText(''))
    const btn = await page.evaluate(() => (document.body.classList.contains('reading') ? 'pageLink' : 'link'))
    await page.click('#' + btn)
    await page.waitForTimeout(300)
    return page.evaluate(async () => window.__shared.length ? 'share:' + window.__shared.pop() : navigator.clipboard.readText())
  }
  // The og:image a crawler gets for a URL (fragment dropped, as crawlers drop it).
  const crawl = async (url) => {
    const res = await fetch(local(url).replace(/#.*$/, ''), { headers: { 'user-agent': 'facebookexternalhit/1.1' } })
    const html = await res.text()
    return { status: res.status, image: (/<meta property="og:image" content="([^"]+)">/.exec(html) ?? [])[1] ?? null }
  }
  const imageOf = (b) => `${SITE_URL}builds/${b.id}/social.jpg`
  const pageImage = (slug) => {
    const own = ['jpg', 'png'].map((x) => `s/page-${slug}.${x}`).find((f) => existsSync(join(SITE, f)))
    return own ? SITE_URL + own : (/<meta property="og:image" content="([^"]+)">/.exec(indexHtml) ?? [])[1]
  }
  return { context, page, errors, missing, settle, view, shot, follow, copyLink, crawl, imageOf, pageImage }
}

const k = (kind, n) => `[${kind}] ${n}`

const run = async (kind) => {
  const S = await session(kind)
  const { page, errors, missing, settle, view, shot, follow, copyLink, crawl, imageOf, pageImage } = S
  const T = (n) => k(kind, n)
  // A phone is shown the lighter preview.jpg, where a build has one; a desktop the SVG.
  const pic = (b) => (kind === 'phone' && b.files.preview ? b.files.preview : b.files.svg)
  const yearKey = YEAR ? `${YEAR.region}:${YEAR.time.year}` : null

  // 1. The front page.
  await page.goto(BASE)
  await settle()
  let v = await view()
  await shot('1-home')
  eq(T('1 home: shows the front page'), v.mode, 'home')
  eq(T('1 home: address stays the front page'), v.url.replace(/#home$/, ''), BASE)
  eq(T('1 home: canonical is the site'), v.canonical, SITE_URL)
  const startHistory = v.history

  // 2. In-app links, each a history entry, each with its share address and canonical.
  const steps = [
    { name: `content page #/${CUTAWAY}`, href: `#/${CUTAWAY}`, url: `${BASE}s/page-${CUTAWAY}.html#/${CUTAWAY}`, canonical: `${SITE_URL}p/${CUTAWAY}.html`, mode: 'page', slug: CUTAWAY },
    { name: `map #${MAP.region}`, href: `#${MAP.region}`, url: `${BASE}s/${doorOf(MAP.region)}.html#${MAP.id}`, canonical: `${SITE_URL}m/${doorOf(MAP.region)}.html`, mode: 'viewer', img: pic(MAP) },
    ...(YEAR ? [{ name: `year #${yearKey}`, href: `#${yearKey}`, url: `${BASE}s/${doorOf(yearKey)}.html#${YEAR.id}`, canonical: `${SITE_URL}m/${doorOf(yearKey)}.html`, mode: 'viewer', img: pic(YEAR) }] : []),
    { name: `set page #/${SET}`, href: `#/${SET}`, url: `${BASE}s/page-${SET}.html#/${SET}`, canonical: `${SITE_URL}p/${SET}.html`, mode: 'page', slug: SET },
  ]
  const seen = [{ ...v }]
  for (const [i, s] of steps.entries()) {
    await follow(s.href)
    v = await view()
    seen.push(v)
    await shot(`2-${i + 1}-${s.mode}`)
    eq(T(`2 ${s.name}: address`), v.url, s.url)
    eq(T(`2 ${s.name}: canonical`), v.canonical, s.canonical)
    eq(T(`2 ${s.name}: view`), s.mode === 'page' ? `page ${v.slug}` : `${v.mode} ${v.img}`, s.mode === 'page' ? `page ${s.slug}` : `viewer ${s.img}`)
    if (s.mode === 'viewer' && kind === 'desktop') report(v.imgOk, T(`2 ${s.name}: picture loads`), v.img)
    if (s.mode === 'viewer') {
      // Relative links in the info bar (the SVG, the full drawing) resolve beside index.html, not s/.
      const hrefs = await page.evaluate((base) => [...document.querySelectorAll('#links a[href], #infoBody a[href]')].map((a) => a.href).filter((h) => h.startsWith(base) && !h.includes('#')), BASE)
      const bad = []
      for (const h of hrefs) { const r = await fetch(h, { method: 'HEAD' }); if (r.status !== 200) bad.push(`${r.status} ${h.slice(ORIGIN.length)}`) }
      report(hrefs.length > 0 && bad.length === 0, T(`2 ${s.name}: its file links resolve`), bad.length ? bad.join(', ') : `${hrefs.length} links, e.g. ${(hrefs[0] ?? '').slice(ORIGIN.length)}`)
    }
  }
  eq(T('2 one history entry per link'), v.history - startHistory, steps.length)

  // 3. Back to the front page and Forward again: each step's address and view come back.
  for (let i = steps.length - 1; i >= 0; i--) {
    await page.goBack()
    await settle()
    const b = await view()
    const want = seen[i]
    report(b.url === want.url && b.mode === want.mode && b.slug === want.slug && b.img === want.img, T(`3 back to step ${i}`), `${b.mode} ${b.slug ?? b.img ?? ''} at ${b.url.slice(ORIGIN.length)}${b.url === want.url ? '' : ` (want ${want.url.slice(ORIGIN.length)})`}`)
  }
  for (let i = 1; i <= steps.length; i++) {
    await page.goForward()
    await settle()
    const f = await view()
    const want = seen[i]
    report(f.url === want.url && f.mode === want.mode && f.slug === want.slug && f.img === want.img, T(`3 forward to step ${i}`), `${f.mode} ${f.slug ?? f.img ?? ''} at ${f.url.slice(ORIGIN.length)}`)
  }
  eq(T('3 no entries added by Back and Forward'), (await view()).history - startHistory, steps.length)

  // 7. Link / Copy link on each kind of view, and what a crawler gets for it.
  const links = [
    { name: 'content page', at: `#/${CUTAWAY}`, want: `${SITE_URL}s/page-${CUTAWAY}.html`, image: pageImage(CUTAWAY) },
    { name: 'section of a page', at: `#/${CUTAWAY}/sources`, want: `${SITE_URL}s/page-${CUTAWAY}.html#/${CUTAWAY}/sources`, image: pageImage(CUTAWAY) },
    { name: 'map', at: `#${MAP.region}`, want: `${SITE_URL}s/${doorOf(MAP.region)}.html`, image: imageOf(MAP) },
    ...(YEAR ? [{ name: 'year', at: `#${yearKey}`, want: `${SITE_URL}s/${doorOf(yearKey)}.html`, image: imageOf(YEAR) }] : []),
    { name: 'set page', at: `#/${SET}`, want: `${SITE_URL}s/page-${SET}.html`, image: pageImage(SET) },
    ...(OTHER ? [{ name: 'compare', at: `#${MAP.region}..${OTHER.region}`, want: `${SITE_URL}s/${doorOf(MAP.region)}.html#${MAP.region}..${OTHER.id}`, image: imageOf(MAP) }] : []),
  ]
  for (const l of links) {
    if (kind === 'phone' && l.name === 'compare') continue
    await follow(l.at)
    const raw = await copyLink()
    // A phone hands the address to its share sheet; a desktop copies it.
    report(raw.startsWith('share:') === (kind === 'phone'), T(`7 Link on a ${l.name} uses the ${kind === 'phone' ? 'share sheet' : 'clipboard'}`), raw.startsWith('share:') ? 'share sheet' : 'clipboard')
    const got = raw.replace(/^share:/, '')
    eq(T(`7 Link on a ${l.name} ${kind === 'phone' ? 'shares' : 'copies'}`), got, l.want)
    const c = await crawl(got)
    eq(T(`7 a crawler fetching it gets the ${l.name}'s own og:image`), c.image, l.image)
  }
  // A map moved off its fitted view: the link carries the view, under its lasting name.
  await follow(`#${MAP.region}`)
  await page.evaluate(() => document.getElementById('actual').click())
  await page.waitForTimeout(500)
  const viewed = (await copyLink()).replace(/^share:/, '')
  report(new RegExp(`^${SITE_URL.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}s/${doorOf(MAP.region)}\\.html#${MAP.region}@[-0-9.]+,[-0-9.]+,[0-9.]+$`).test(viewed), T('7 Link on a zoomed map carries the view'), viewed)
  await shot('7-zoomed')
  // ... and opening that link comes back to the same view.
  await page.goto(local(viewed))
  await settle()
  const back = await view()
  report(back.url.endsWith(viewed.slice(viewed.indexOf('#')).replace(`#${MAP.region}@`, `#${MAP.id}@`)), T('7 the zoomed link reopens the same view'), back.url.slice(ORIGIN.length))

  if (kind === 'desktop') {
    // 4. Reload on each kind of share address: the same view comes back, at the same address.
    for (const [name, url] of [
      ['content page', `${BASE}s/page-${CUTAWAY}.html#/${CUTAWAY}`],
      ['section', `${BASE}s/page-${CUTAWAY}.html#/${CUTAWAY}/sources`],
      ['map', `${BASE}s/${doorOf(MAP.region)}.html#${MAP.id}`],
      ...(YEAR ? [['year', `${BASE}s/${doorOf(yearKey)}.html#${YEAR.id}`]] : []),
      ['map, no fragment', `${BASE}s/${doorOf(MAP.region)}.html`],
    ]) {
      await page.goto(url)
      await settle()
      const a = await view()
      await page.reload()
      await settle()
      const r = await view()
      const expect = name === 'map, no fragment' ? `${BASE}s/${doorOf(MAP.region)}.html#${MAP.id}` : url
      report(a.url === expect && r.url === expect && r.mode === a.mode && r.slug === a.slug && r.img === a.img, T(`4 reload ${name}`), `${r.mode} ${r.slug ?? r.img ?? ''} at ${r.url.slice(ORIGIN.length)}`)
    }

    // 5. Old-style links, and an old build's share page.
    const old = [
      [`#/${CUTAWAY}`, 'page', CUTAWAY, `${BASE}s/page-${CUTAWAY}.html#/${CUTAWAY}`],
      [`#${MAP.region}`, 'viewer', MAP.files.svg, `${BASE}s/${doorOf(MAP.region)}.html#${MAP.id}`],
      ...(YEAR ? [[`#${yearKey}`, 'viewer', YEAR.files.svg, `${BASE}s/${doorOf(yearKey)}.html#${YEAR.id}`]] : []),
      ...(OTHER ? [[`#${MAP.region}..${OTHER.region}`, 'viewer', MAP.files.svg, `${BASE}s/${doorOf(MAP.region)}.html#${MAP.id}..${OTHER.id}`]] : []),
      [`#${MAP.id}`, 'viewer', MAP.files.svg, `${BASE}s/${doorOf(MAP.region)}.html#${MAP.id}`],
    ]
    for (const [hash, mode, what, url] of old) {
      await page.goto(BASE + hash)
      await settle()
      const o = await view()
      report(o.mode === mode && (mode === 'page' ? o.slug === what : o.img === what) && o.url === url, T(`5 old link ${hash}`), `${o.mode} ${o.slug ?? o.img ?? ''} at ${o.url.slice(ORIGIN.length)}`)
    }
    if (STALE) {
      const name = STALE.replace(/^\d{8}-\d{6}-|\.html$/g, '')
      await page.goto(`${BASE}s/${STALE}#${STALE.slice(0, -5)}`)
      await settle()
      const o = await view()
      const now = newest((b) => b.name === name) ?? newest((b) => b.region === name)
      report(o.mode === 'viewer' && now !== undefined && o.img === now.files.svg, T(`5 old build's share page s/${STALE}`), `${o.mode} ${o.img} at ${o.url.slice(ORIGIN.length)}`)
      await shot('5-old-build')
    }

    // 6. The static pages' links into the explorer.
    for (const [path, mode, what] of [[`p/${CUTAWAY}.html`, 'page', CUTAWAY], [`m/${doorOf(MAP.region)}.html`, 'viewer', MAP.files.svg], ...(YEAR ? [[`m/${doorOf(yearKey)}.html`, 'viewer', YEAR.files.svg]] : [])]) {
      await page.goto(BASE + path)
      await page.waitForLoadState('load')
      const href = await page.evaluate(() => [...document.querySelectorAll('a[href^="../index.html#"]')].find((a) => /explorer|Explore/i.test(a.textContent))?.getAttribute('href') ?? null)
      if (href === null) { report(false, T(`6 ${path} links into the explorer`), 'no link'); continue }
      await page.click(`a[href="${href}"]`)
      await settle()
      const o = await view()
      report(o.mode === mode && (mode === 'page' ? o.slug === what : o.img === what), T(`6 ${path} → ${href}`), `${o.mode} ${o.slug ?? o.img ?? ''} at ${o.url.slice(ORIGIN.length)}`)
    }

    // 8. The shop button on the cutaway's page: the product, with the campaign tags.
    const onSale = site.shop?.onSale?.[CUTAWAY]
    if (onSale) {
      await page.goto(`${BASE}#/${CUTAWAY}`)
      await settle()
      const href = await page.evaluate(() => {
        const a = document.querySelector('#article .buyp a')
        if (!a) return null
        a.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }))
        return a.href
      })
      const u = href ? new URL(href) : null
      report(u !== null && u.origin + u.pathname === onSale && u.searchParams.get('utm_source') === 'isoscape-explorer' && u.searchParams.get('utm_medium') === 'referral' && u.searchParams.get('utm_campaign') === CUTAWAY, T('8 shop button in the explorer'), href ?? 'none')
      await page.goto(`${BASE}p/${CUTAWAY}.html`)
      const st = await page.evaluate((p) => [...document.querySelectorAll('a')].map((a) => a.href).find((h) => h.startsWith(p)) ?? null, onSale)
      report(st !== null && /utm_source=isoscape-explorer&utm_medium=referral&utm_campaign=/.test(st), T('8 shop button on the static page'), st ?? 'none')
    }
  }

  report(errors.length === 0, T('no script errors'), errors.slice(0, 3).join(' | '))
  const realMissing = [...new Set(missing)]
  report(realMissing.length === 0, T('no 404s from the site'), realMissing.slice(0, 5).join(', '))
  await S.context.close()
}

try {
  for (const kind of ['desktop', 'phone']) if (!ONLY || ONLY === kind) await run(kind)
} finally {
  await browser.close()
  server.close()
}
console.log(`${failed === 0 ? 'all passed' : `${failed} failed`}; screenshots in ${OUT}`)
process.exit(failed === 0 ? 0 : 1)
