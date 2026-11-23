// Which of today's roads drawn in a dated Jackson Ward scene run through buildings traced for that year?
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
const R = process.argv[2]
const { parseOsm } = await import(R + '/src/osm.ts')
const { loadRegion } = await import(R + '/src/region.ts')
const H = await import(R + '/src/history.ts')
const { buildScene } = await import(R + '/src/scene.ts')
const { palette } = await import(R + '/src/palette.ts')
const { loadDem, cleanDem, sampler } = await import(R + '/src/dem.ts')
process.chdir(R)
const region = await loadRegion('jackson-ward')
const features = parseOsm(await readFile(resolve('data', region.data, 'osm.json'), 'utf8'))
const dem = await loadDem(resolve('data', region.data, 'dem.bin.gz')); cleanDem(dem); const elevation = sampler(dem)
const history = await H.loadHistory(resolve(region.time.history))
const parcels = (await H.loadYearBuilt(H.yearBuiltDirs(region, resolve('data')), region.time.yearBuilt.field, 'jackson-ward')).parcels
const dates = H.dateBuildings(features.filter((f: any) => f.type === 'polygon'), parcels, history.dates, 4, 8, history.parkingFrom)
const years = (process.argv[3] ?? '1925,1952,1959').split(',').map(Number)
const sw = process.argv[4] ? process.argv[4].split(',') : []
const pip = (p: number[], ring: number[][]) => { let c = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) { const [xi, yi] = ring[i], [xj, yj] = ring[j]; if ((yi > p[1]) !== (yj > p[1]) && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) c = !c } return c }
for (const year of years) {
  const hist = H.switchedOn(history, sw)
  const scene = buildScene(region, features, palette(region.palette), elevation, { time: { year, history: hist, dates } })
  const v = scene.view
  // road cells, 2 m grid in view meters
  const cells = new Set<string>()
  for (const r of scene.ribbons) if (r.kind === 'road' || r.kind === 'path') for (const q of r.quads) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity
    for (const [x, y] of q) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y) }
    for (let x = Math.floor(x0 / 2); x <= Math.floor(x1 / 2); x++) for (let y = Math.floor(y0 / 2); y <= Math.floor(y1 / 2); y++) if (pip([x * 2 + 1, y * 2 + 1], q)) cells.add(`${x},${y}`)
  }
  const bridgeIds = new Set(scene.items.filter((i: any) => i.kind === 'bridge').map((i: any) => String(i.id).split('.')[0]))
  const traced = hist.traced.filter((b: any) => H.alive(b.from, b.to, year)).map((b: any) => ({ id: b.id, ring: b.ring.map(([lo, la]: number[]) => v.toView(lo, la)) }))
  const grid = new Map<string, any[]>()
  for (const t of traced) { const xs = t.ring.map((p: number[]) => p[0]), ys = t.ring.map((p: number[]) => p[1]); for (let x = Math.floor(Math.min(...xs) / 20); x <= Math.floor(Math.max(...xs) / 20); x++) for (let y = Math.floor(Math.min(...ys) / 20); y <= Math.floor(Math.max(...ys) / 20); y++) { const k = `${x},${y}`; (grid.get(k) ?? grid.set(k, []).get(k)!).push(t) } }
  const out: any[] = []
  for (const f of features) {
    if (f.type !== 'line' || f.tags.highway === undefined) continue
    const pts = f.points.map(([lo, la]: number[]) => v.toView(lo, la))
    let len = 0, inB = 0, drawn = 0; const hit = new Set<string>()
    for (let i = 0; i + 1 < pts.length; i++) {
      const [a, b] = [pts[i], pts[i + 1]]; const L = Math.hypot(b[0] - a[0], b[1] - a[1]); const n = Math.max(1, Math.round(L))
      for (let s = 0; s < n; s++) {
        const t = (s + 0.5) / n, p = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
        if (Math.abs(p[0]) > region.width / 2 || Math.abs(p[1]) > region.depth / 2 + 200) continue
        len += L / n
        if (cells.has(`${Math.floor(p[0] / 2)},${Math.floor(p[1] / 2)}`)) drawn += L / n
        for (const tb of grid.get(`${Math.floor(p[0] / 20)},${Math.floor(p[1] / 20)}`) ?? []) if (pip(p, tb.ring)) { inB += L / n; hit.add(tb.id); break }
      }
    }
    if (inB >= 6 && drawn >= 0.5 * len) out.push({ id: f.id, hw: f.tags.highway, name: f.tags.name ?? '', bridge: f.tags.bridge ?? '', len: Math.round(len), inB: Math.round(inB), drawn: Math.round(drawn), deck: bridgeIds.has(f.id), n: hit.size, at: pts[Math.floor(pts.length / 2)].map((x: number) => Math.round(x)) })
  }
  out.sort((a, b) => b.inB - a.inB)
  console.log(`== ${year}${sw.length ? ' +' + sw : ''}: ${out.length} ways drawn that run 6 m or more through buildings traced for the year`)
  for (const o of out) console.log([o.id, o.hw, JSON.stringify(o.name), o.bridge, `len ${o.len}`, `inside ${o.inB}`, `drawn ${o.drawn}`, o.deck ? 'DECK' : '', `bldgs ${o.n}`, `at ${o.at}`].join('\t'))
  console.log('bridge decks drawn:', [...bridgeIds].sort().join(' '))
}
