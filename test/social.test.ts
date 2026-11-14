import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import type { BuildMeta } from '../src/archive.ts'
import { renderExplorer } from '../src/explorer.ts'
import {
  buildCard, clip, escAttr, flagshipOf, loadSiteConfig, metaTags, normaliseSiteUrl, reframeSvg, shareFile, sharePage, siteHref, socialCrop,
} from '../src/social.ts'

const build = (id: string, extra: Partial<BuildMeta> = {}): BuildMeta => ({
  id, name: 'r', region: 'r', title: 'Richmond, VA — downtown', palette: 'paper', createdAt: '2026-01-01T00:00:00Z', viewBox: [0, 0, 2000, 1000], bearing: 0, ms: 1, bytes: 1,
  stats: { buildings: 1234, elevationDatum: 0, elevationTop: 57.2 }, config: { name: 'r', title: 'T' }, files: { svg: `builds/${id}/image.svg` }, sky: '#fff',
  ...extra,
} as unknown as BuildMeta)

test('meta tags escape quotes, ampersands and angle brackets', () => {
  const tags = metaTags({ title: 'Tom & Jerry\'s "place" <b>', description: 'a & b', image: 'https://x.org/a.png?x=1&y=2', imageWidth: 1200, imageHeight: 630, url: 'https://x.org/s/a.html' })
  assert.match(tags, /<meta property="og:title" content="Tom &amp; Jerry&#39;s &quot;place&quot; &lt;b&gt;">/)
  assert.match(tags, /<meta name="description" content="a &amp; b">/)
  assert.match(tags, /<meta property="og:image" content="https:\/\/x.org\/a.png\?x=1&amp;y=2">/)
  assert.match(tags, /<meta name="twitter:card" content="summary_large_image">/)
  assert.match(tags, /<link rel="canonical" href="https:\/\/x.org\/s\/a.html">/)
  assert.match(tags, /<meta property="og:image:width" content="1200">/)
  // Every attribute value is a clean double-quoted string: no stray quote ends one early.
  for (const line of tags.trim().split('\n')) assert.match(line, /^<(meta|link)( [\w:-]+="[^"<>]*")+>$/)
  assert.equal(escAttr(`"'&<>`), '&quot;&#39;&amp;&lt;&gt;')
})

test('without an image or a URL, no empty tags and a summary card', () => {
  const tags = metaTags({ title: 't', description: 'd' })
  assert.doesNotMatch(tags, /og:image|og:url|canonical/)
  assert.match(tags, /twitter:card" content="summary"/)
})

test('URLs join under a base, or stay relative to the page', () => {
  assert.equal(siteHref('builds/a/social.png', 'https://x.org/iso/'), 'https://x.org/iso/builds/a/social.png')
  assert.equal(siteHref('/s/a.html', 'https://x.org/iso'), 'https://x.org/iso/s/a.html')
  assert.equal(siteHref('builds/a/social.png'), 'builds/a/social.png')
  assert.equal(siteHref('builds/a/social.png', undefined, 1), '../builds/a/social.png')
  assert.equal(normaliseSiteUrl('https://x.org/iso'), 'https://x.org/iso/')
  assert.equal(normaliseSiteUrl('https://x.org/iso/?q#h'), 'https://x.org/iso/')
  assert.equal(normaliseSiteUrl('  '), undefined)
  assert.throws(() => normaliseSiteUrl('file:///tmp/'))
  assert.throws(() => normaliseSiteUrl('example.org'))
})

test('the site URL comes from the flag, then the environment, then the config file', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'isoscape-'))
  assert.deepEqual(await loadSiteConfig(undefined, dir, {}), {})
  await writeFile(join(dir, 'isoscape.config.json'), JSON.stringify({ siteUrl: 'https://file.org/a', flagship: 'r' }))
  assert.deepEqual(await loadSiteConfig(undefined, dir, {}), { siteUrl: 'https://file.org/a/', flagship: 'r' })
  assert.equal((await loadSiteConfig(undefined, dir, { ISOSCAPE_SITE_URL: 'https://env.org/' })).siteUrl, 'https://env.org/')
  assert.equal((await loadSiteConfig('https://flag.org', dir, { ISOSCAPE_SITE_URL: 'https://env.org/' })).siteUrl, 'https://flag.org/')
})

test('a share page redirects to the explorer, keeping the fragment it was opened with', () => {
  const html = sharePage({ title: 'A "b" & c', description: 'd', image: '../builds/x/social.png' }, '#x')
  const script = html.match(/<script>([\s\S]*?)<\/script>/)
  assert.ok(script)
  const run = (hash: string) => {
    const location = { hash, target: '', replace(u: string) { this.target = u } }
    new Function('location', script[1])(location)
    return location.target
  }
  assert.equal(run('#x@10.5,-3,2~0.3/made'), '../index.html#x@10.5,-3,2~0.3/made')
  assert.equal(run('#a..b'), '../index.html#a..b')
  assert.equal(run(''), '../index.html#x')
  assert.equal(run('#'), '../index.html#x')
  assert.match(html, /<a href="\.\.\/index\.html#x">A &quot;b&quot; &amp; c/)
  assert.match(html, /<title>A &quot;b&quot; &amp; c<\/title>/)
  // Crawlers that follow a meta refresh would take the index page's card instead.
  assert.doesNotMatch(html, /http-equiv="refresh"/)
  assert.equal(shareFile({ build: 'x' }), 'x.html')
  assert.equal(shareFile({ page: 'about' }), 'page-about.html')
})

test('a build card says where, when and what it holds', () => {
  const plain = buildCard(build('a'))
  assert.equal(plain.title, 'Richmond, VA — downtown · isoscape')
  assert.match(plain.description, /1,234 buildings and ground rising from 0 to 57 m/)
  const dated = buildCard(build('b', { title: 'Richmond, VA — downtown, 1865', time: { year: 1865, series: 'r', title: 'After the Evacuation Fire', note: 'Some 35 blocks burn.', curated: [] } }))
  assert.equal(dated.title, 'Richmond, VA — downtown, 1865: After the Evacuation Fire · isoscape')
  assert.match(dated.description, /^1865: After the Evacuation Fire\. Some 35 blocks burn\. .*1,234 buildings standing by 1865/)
  assert.ok(clip('word '.repeat(100), 50).length <= 50)
  assert.ok(clip('word '.repeat(100), 50).endsWith('…'))
})

test('the social crop fills 1.91:1 around the centre, and the SVG is reframed to it', () => {
  const wide = socialCrop([0, 0, 4000, 1000])
  assert.ok(Math.abs(wide[2] / wide[3] - 1200 / 630) < 1e-9)
  assert.equal(wide[3], 1000)
  assert.ok(Math.abs(wide[0] + wide[2] / 2 - 2000) < 1e-9)
  assert.equal(socialCrop([0, 0, 4000, 1000], true)[0], 0)
  const tall = socialCrop([0, 0, 1000, 1000])
  assert.equal(tall[2], 1000)
  assert.ok(tall[1] > 0 && tall[1] + tall[3] < 1000)
  const svg = reframeSvg('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" width="10" class="a"><rect/></svg>', [1, 2, 3, 4])
  assert.equal(svg, '<?xml version="1.0"?><svg viewBox="1 2 3 4" width="1200" height="630" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" class="a"><rect/></svg>')
})

test('the explorer carries the site card and copies share-page links', () => {
  const builds = [build('new'), build('old', { region: 'flag' })]
  assert.equal(flagshipOf(builds)?.id, 'new')
  assert.equal(flagshipOf(builds, 'flag')?.id, 'old')
  const html = renderExplorer(builds, [], { siteUrl: 'https://x.org/iso/', image: { path: 'builds/new/social.png', width: 1200, height: 630 } })
  assert.match(html, /<meta property="og:image" content="https:\/\/x.org\/iso\/builds\/new\/social.png">/)
  assert.match(html, /<meta property="og:url" content="https:\/\/x.org\/iso\/">/)
  assert.match(html, /<script type="application\/json" id="site">\{"siteUrl":"https:\/\/x.org\/iso\/","shop":null,"home":null,"latestPages":true\}<\/script>/)
  assert.match(html, /'s\/' \+ encodeURIComponent\(file\) \+ '\.html' \+ location\.hash/)
  const bare = renderExplorer(builds)
  assert.doesNotMatch(bare, /og:url|canonical/)
  assert.match(bare, /og:title/)
})

test('a front page comes from the config, and a malformed one is ignored', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'iso-home-'))
  const home = { title: 'T', heroes: [{ region: 'r', title: 'R' }], sections: [{ title: 'S', prefixes: ['lm-'], collapsed: true }] }
  await writeFile(join(dir, 'isoscape.config.json'), JSON.stringify({ home, shop: { label: 'L', url: 'https://s/', cta: 'Buy' } }))
  const config = await loadSiteConfig(undefined, dir, {})
  assert.deepEqual(config.home, home)
  const html = renderExplorer([build('a')], [], { home: config.home, shop: config.shop })
  assert.match(html, /<section id="home"/)
  assert.match(html, /"home":\{"title":"T"/)
  assert.match(html, /<a class="shop" href="https:\/\/s\/"[^>]*><b>Buy ↗<\/b><span>L<\/span><\/a>/)
  await writeFile(join(dir, 'isoscape.config.json'), JSON.stringify({ home: { title: 'T', heroes: 'no', sections: [] } }))
  assert.equal((await loadSiteConfig(undefined, dir, {})).home, undefined)
})
