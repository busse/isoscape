import { test } from 'node:test'
import assert from 'node:assert/strict'
import { escapeHtml, inline, markdown, safeHref, slugify } from '../src/markdown.ts'

const md = (s: string) => markdown(s).html

test('headings get GitHub-style ids, deduplicated', () => {
  const r = markdown('# How it’s made\n\n## Paint order\n\n## Paint order\n\n### What *is* `snap`?')
  assert.deepEqual(r.headings.map((h) => h.id), ['how-its-made', 'paint-order', 'paint-order-1', 'what-is-snap'])
  assert.match(r.html, /<h2 id="paint-order">Paint order<\/h2>/)
  assert.match(r.html, /<h3 id="what-is-snap">What <em>is<\/em> <code>snap<\/code>\?<\/h3>/)
  assert.equal(slugify('Measured, inferred, guessed'), 'measured-inferred-guessed')
})

test('heading ids take a prefix in the HTML only', () => {
  const r = markdown('## Rapids', { idPrefix: 'p-x-' })
  assert.equal(r.headings[0].id, 'rapids')
  assert.match(r.html, /id="p-x-rapids"/)
})

test('paragraphs join lines; blank lines split them', () => {
  assert.equal(md('one\ntwo\n\nthree'), '<p>one\ntwo</p>\n<p>three</p>')
})

test('emphasis, strong, code', () => {
  assert.equal(inline('**bold** and *em* and _em_ and `a < b`'), '<strong>bold</strong> and <em>em</em> and <em>em</em> and <code>a &lt; b</code>')
  assert.equal(inline('snake_case_name stays'), 'snake_case_name stays')
  assert.equal(inline('2 * 3 * 4'), '2 * 3 * 4')
  assert.equal(inline('``a ` b``'), '<code>a ` b</code>')
  assert.equal(inline('\\*not em\\*'), '*not em*')
})

test('all text is escaped', () => {
  assert.equal(md('<script>alert(1)</script>'), '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>')
  assert.equal(md('a & b "c" \'d\''), '<p>a &amp; b &quot;c&quot; &#39;d&#39;</p>')
  assert.equal(escapeHtml('<>&"\''), '&lt;&gt;&amp;&quot;&#39;')
  assert.match(md('```\n<b>x</b>\n```'), /<pre><code>&lt;b&gt;x&lt;\/b&gt;<\/code><\/pre>/)
})

test('links: safe schemes kept, others dropped, external ones open a new tab', () => {
  assert.equal(inline('[OSM](https://www.openstreetmap.org/copyright)'), '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OSM</a>')
  assert.equal(inline('[x](javascript:alert(1))'), '<a href="#">x</a>')
  assert.equal(inline('[x]( JavaScript:alert(1))'), '<a href="#">x</a>')
  assert.equal(inline('[x](data:text/html,hi)'), '<a href="#">x</a>')
  assert.equal(inline('[a section](#rapids)'), '<a href="#rapids">a section</a>')
  assert.equal(inline('[*em* link](about.md)'), '<a href="about.md"><em>em</em> link</a>')
  assert.equal(inline('<https://usgs.gov>'), '<a href="https://usgs.gov" target="_blank" rel="noopener">https://usgs.gov</a>')
  assert.equal(inline('[x](a"onmouseover="b)'), '<a href="a&quot;onmouseover=&quot;b">x</a>')
  assert.equal(safeHref('mailto:a@b.c'), 'mailto:a@b.c')
  assert.equal(safeHref('java\tscript:x'), null)
})

test('link and image hooks', () => {
  assert.equal(inline('[s](#x)', { link: (h) => '#/page/' + h.slice(1) }), '<a href="#/page/x">s</a>')
  assert.equal(inline('![alt](d.svg)', { image: () => 'data:image/svg+xml;base64,AA' }), '<img src="data:image/svg+xml;base64,AA" alt="alt" loading="lazy">')
  assert.equal(inline('![alt <b>](d.svg)', { image: () => null }), 'alt &lt;b&gt;')
  assert.equal(inline('![x](javascript:1)'), 'x')
})

test('lists: tight, ordered, nested, continued', () => {
  assert.equal(md('- a\n- b'), '<ul><li>a</li><li>b</li></ul>')
  assert.equal(md('3. a\n4. b'), '<ol start="3"><li>a</li><li>b</li></ol>')
  assert.equal(md('- a\n  more\n- b\n  - c\n  - d'), '<ul><li>a\nmore</li><li>b\n<ul><li>c</li><li>d</li></ul></li></ul>')
  assert.equal(md('- a\nlazy\n\npara'), '<ul><li>a\nlazy</li></ul>\n<p>para</p>')
  assert.equal(md('- a\n\n- b'), '<ul><li><p>a</p></li><li><p>b</p></li></ul>')
  assert.equal(md('1. **one**\n2. two'), '<ol><li><strong>one</strong></li><li>two</li></ol>')
})

test('a list straight after a paragraph line starts a list', () => {
  assert.equal(md('Where to start:\n- a'), '<p>Where to start:</p>\n<ul><li>a</li></ul>')
})

test('tables with alignment and escaped pipes', () => {
  const html = md('| a | b |\n|:--|--:|\n| `x` | 1 \\| 2 |\n| y |')
  assert.equal(html, '<div class="table"><table><thead><tr><th style="text-align:left">a</th><th style="text-align:right">b</th></tr></thead>' +
    '<tbody><tr><td style="text-align:left"><code>x</code></td><td style="text-align:right">1 | 2</td></tr>' +
    '<tr><td style="text-align:left">y</td><td style="text-align:right"></td></tr></tbody></table></div>')
})

test('code fences, quotes, rules', () => {
  assert.equal(md('```sh\nnode bin/isoscape.js\n```'), '<pre><code class="language-sh">node bin/isoscape.js</code></pre>')
  assert.equal(md('> quoted\n> *line*'), '<blockquote><p>quoted\n<em>line</em></p></blockquote>')
  assert.equal(md('a\n\n---\n\nb'), '<p>a</p>\n<hr>\n<p>b</p>')
  assert.equal(md('line one  \nline two'), '<p>line one<br>\nline two</p>')
})

test('an unclosed fence runs to the end without losing text', () => {
  assert.equal(md('```\na\nb'), '<pre><code>a\nb</code></pre>')
})

test('a figure block numbers its picture, links it to its full file and keeps its caption, tables included', () => {
  const src = 'Before.\n\n::: figure wide bogus\n![A wide view](a.webp)\n\nThe caption. *How this was made:* in code.\n\n| # | Name |\n|---|---|\n| 1 | Hall |\n:::\n\n::: figure\n![Second](b.webp)\n:::\n\nAfter.'
  const r = markdown(src, { idPrefix: 'p-x-', image: (s) => ({ src: 'data:' + s, width: 1600, height: 680, full: 'p/' + s.replace('.webp', '-large.webp') }) })
  assert.deepEqual(r.figures, [{ n: 1, id: 'fig-1', alt: 'A wide view' }, { n: 2, id: 'fig-2', alt: 'Second' }])
  assert.match(r.html, /<figure class="fig wide" id="p-x-fig-1">\n<a class="fig-open" href="p\/a-large\.webp" aria-label="Fig\. 1\. Open larger"><img src="data:a\.webp" alt="A wide view" width="1600" height="680" loading="lazy"><\/a>/)
  assert.match(r.html, /<figcaption><p><span class="fig-n">Fig\. 1\.<\/span> The caption\. <em>How this was made:<\/em> in code\.<\/p>\n<div class="table"><table>[\s\S]*Hall[\s\S]*<\/table><\/div><\/figcaption>\n<\/figure>/)
  // A figure without a caption still gets its number; the text around figures is untouched.
  assert.match(r.html, /<figure class="fig" id="p-x-fig-2">[\s\S]*<figcaption><p><span class="fig-n">Fig\. 2\.<\/span><\/p><\/figcaption>/)
  assert.match(r.html, /^<p>Before\.<\/p>\n<figure/)
  assert.match(r.html, /<\/figure>\n<p>After\.<\/p>$/)
  assert.doesNotMatch(r.html, /bogus|data-full/)
})

test('without a figure block, images render as before (plus their size when known)', () => {
  assert.equal(md('![d](d.svg)'), '<p><img src="d.svg" alt="d" loading="lazy"></p>')
  assert.equal(markdown('![d](d.webp)', { image: (s) => ({ src: s, width: 4, height: 3, full: 'x' }) }).html, '<p><img src="d.webp" alt="d" width="4" height="3" loading="lazy"></p>')
  assert.deepEqual(markdown('![d](d.svg)').figures, [])
})
