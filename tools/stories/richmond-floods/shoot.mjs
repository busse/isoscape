// Screenshot a page in headless Chrome (sandbox on, file://, no server) as a series of viewport
// tiles from top to bottom, so a long page can be read as a reader scrolls it.
//   node tools/stories/richmond-floods/shoot.mjs <url> <width> <out-prefix> [tile-height]
// Made with Claude.
import { spawn } from 'node:child_process'
import { writeFileSync } from 'node:fs'

const [url, width, prefix, tileArg] = process.argv.slice(2)
const W = Number(width), H = Number(tileArg || (W < 600 ? 844 : 900))
const port = 9300 + Math.floor(Math.random() * 500)
const chrome = spawn('google-chrome', ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--remote-debugging-port=${port}`,
  `--window-size=${W},${H}`, '--user-data-dir=/tmp/rf-chrome-' + port, 'about:blank'], { stdio: 'ignore' })
const sleep = ms => new Promise(r => setTimeout(r, ms))
let ws
for (let i = 0; i < 50 && !ws; i++) {
  await sleep(200)
  try {
    const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json()
    const page = list.find(t => t.type === 'page')
    if (page) ws = new WebSocket(page.webSocketDebuggerUrl)
  } catch { /* not up yet */ }
}
await new Promise(r => ws.addEventListener('open', r, { once: true }))
let id = 0
const pending = new Map()
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data)
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id) }
})
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })) })
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: W < 600 })
await send('Page.enable')
await send('Page.navigate', { url })
await sleep(4000)
const evalJs = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result.value
// The explorer scrolls a container; the static page scrolls the document. Find whichever scrolls.
const scroller = `(() => { const c = [...document.querySelectorAll('*')].filter(e => e.scrollHeight > e.clientHeight + 50 && ['auto','scroll'].includes(getComputedStyle(e).overflowY)); c.sort((a,b)=>b.scrollHeight-a.scrollHeight); return c[0] || document.scrollingElement })()`
const total = await evalJs(`${scroller}.scrollHeight`)
let n = 0
for (let y = 0; y < total; y += H - 60) {
  await evalJs(`${scroller}.scrollTop = ${y}`)
  await sleep(700)
  const shot = await send('Page.captureScreenshot', { format: 'png' })
  writeFileSync(`${prefix}-${String(++n).padStart(3, '0')}.png`, Buffer.from(shot.data, 'base64'))
}
console.log(`${n} tiles, page height ${total}`)
ws.close(); chrome.kill()
