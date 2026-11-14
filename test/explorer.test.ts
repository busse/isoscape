import { test } from 'node:test'
import assert from 'node:assert/strict'
import { renderExplorer } from '../src/explorer.ts'
import type { BuildMeta } from '../src/archive.ts'

const build = (id: string, year?: number): BuildMeta => ({
  id, name: 'r', region: 'r', title: 'T', palette: 'paper', createdAt: '2026-01-01T00:00:00Z', viewBox: [0, 0, 2000, 1000], bearing: 0, ms: 1, bytes: 1,
  stats: {}, config: { name: 'r', title: 'T', center: [0, 0], width: 1, depth: 1, bearing: 0, scale: 1 }, files: { svg: id + '.svg' }, sky: '#fff',
  ...(year ? { time: { year, series: 's', curated: [] } } : {}),
} as unknown as BuildMeta)

test('the explorer offers a link to the current view, and its script parses', () => {
  const html = renderExplorer([build('a', 1900), build('b', 1901)])
  assert.match(html, /<button id="link"[^>]*>Link<\/button>/)
  assert.match(html, /<kbd>L<\/kbd> copy link/)
  const script = html.match(/<script>\n([\s\S]*?)<\/script>/)
  assert.ok(script)
  assert.doesNotThrow(() => new Function(script[1]))
  // The view rides in the hash, written with replaceState so panning makes no history entries.
  assert.match(script[1], /history\.replaceState\(null, '', hash\)/)
})
