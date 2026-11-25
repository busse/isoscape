import { test } from 'node:test'
import assert from 'node:assert/strict'
import { fragmentUrl, renderExplorer } from '../src/explorer.ts'
import type { BuildMeta } from '../src/archive.ts'

const build = (id: string, year?: number): BuildMeta => ({
  id, name: 'r', region: 'r', title: 'T', palette: 'paper', createdAt: '2026-01-01T00:00:00Z', viewBox: [0, 0, 2000, 1000], bearing: 0, ms: 1, bytes: 1,
  stats: {}, config: { name: 'r', title: 'T', center: [0, 0], width: 1, depth: 1, bearing: 0, scale: 1 }, files: { svg: id + '.svg' }, sky: '#fff',
  ...(year ? { time: { year, series: 's', curated: [] } } : {}),
} as unknown as BuildMeta)

test('the explorer offers a link to the current view, and its script parses', () => {
  const html = renderExplorer([build('a', 1900), build('b', 1901)])
  assert.match(html, /<button id="link"[^>]*>Link<\/button>/)
  assert.match(html, /<kbd>L<\/kbd><\/dt><dd>Copy a link to this view/)
  const script = html.match(/<script>\n([\s\S]*?)<\/script>/)
  assert.ok(script)
  assert.doesNotThrow(() => new Function(script[1]))
  // The view rides in the hash, written with replaceState so panning makes no history entries.
  assert.match(script[1], /setAddress\(viewerHash\(\), false\)/)
  assert.match(script[1], /const how = push && !same \? 'pushState' : 'replaceState'/)
  // Relative URLs keep resolving beside index.html when the address bar shows a share page in s/.
  assert.match(html, /<head>\n<meta charset="utf-8">\n<meta name="viewport"[^>]*>\n<base href="\.\/">/)
  // Pages have a link button too.
  assert.match(html, /<button class="back" id="pageLink"[^>]*>Copy link<\/button>/)
  // Analytics keep the explorer's own path, whatever the address bar shows.
  assert.match(script[1], /page_location: location\.origin \+ appPath \+ where/)
})

test('routes write absolute addresses to history, so in-page links work opened from disk', () => {
  // Under <base href="./"> a bare '#/page/section' would resolve against the folder, another
  // document from file://, and pushState throws: every in-page and section link did nothing.
  assert.equal(fragmentUrl('file:///Users/x/site/index.html#/jackson-ward', '#/jackson-ward/the-tracing'), 'file:///Users/x/site/index.html#/jackson-ward/the-tracing')
  assert.equal(fragmentUrl('https://example.org/iso/s/page-a.html', '#/a/b'), 'https://example.org/iso/s/page-a.html#/a/b')
  const script = renderExplorer([build('a', 1900)]).match(/<script>\n([\s\S]*?)<\/script>/)
  assert.ok(script)
  assert.match(script[1], /const fragmentUrl = \(\(href\s*, hash\s*\)\s*=>/)
  assert.match(script[1], /: fragmentUrl\(location\.href, hash\)\n/)
  assert.doesNotMatch(script[1], /history\[how\]\(null, '', hash\)/)
  assert.doesNotMatch(script[1], /url \|\| hash/)
})
