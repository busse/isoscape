/**
 * Floods series d3: counts for each box of tools/floods/d3/boxes.json on each plate: depth at its
 * center (the cached 2 m lidar against the flood's surface there), acres under water inside it,
 * and its buildings shown and in water, confirmed and unconfirmed apart. A box's ground is the
 * view rectangle under its `size` in SVG units (at scale 2 and squash 0.5: half that in meters
 * across, the same in meters deep).
 *
 *   node tools/floods/d3/boxcounts.ts <area> <flood>:<year> ... > out.json
 */
import { readFileSync } from 'node:fs'
import { loadRegion } from '../../../src/region.ts'
import { parseOsm, type PolygonFeature } from '../../../src/osm.ts'
import { cleanDem, loadDem, sampler } from '../../../src/dem.ts'
import { buildScene } from '../../../src/scene.ts'
import { palette } from '../../../src/palette.ts'
import { centroid } from '../../../src/geom.ts'
import { levelAt, parseFlood } from '../../../src/flood.ts'
import { applyEvidence, dateBuildings, loadHistory, loadYearBuilt, unconfirmedDated, unconfirmedTraced, yearBuiltDirs } from '../../../src/history.ts'

const [area, ...plates] = process.argv.slice(2)
const spec = JSON.parse(readFileSync('tools/floods/d3/boxes.json', 'utf8'))
const A = spec[area]
// rc2: every box of the area, its default list and its sheets' own lists, each with its list's size.
type Box = { id: string; at: [number, number]; depthAt?: [number, number]; size: [number, number] }
const allBoxes: Box[] = [
  ...A.boxes.map((b: Box) => ({ ...b, size: A.size })),
  ...Object.values((A.lists ?? {}) as Record<string, { size: [number, number]; boxes: Box[] }>).flatMap((l) => l.boxes.map((b) => ({ ...b, size: l.size }))),
]
const region = await loadRegion(A.region)
const features = parseOsm(readFileSync(`data/${region.data ?? region.name}/osm.json`, 'utf8'))
const dem = (await loadDem(`data/${region.data ?? region.name}/dem.bin.gz`))!
cleanDem(dem)
const ground2 = sampler(dem)
const history = await loadHistory(region.time!.history)
const parcels = (await loadYearBuilt(yearBuiltDirs(region, 'data'), region.time!.yearBuilt!.field, region.name)).parcels
const dated = dateBuildings(features.filter((f): f is PolygonFeature => f.type === 'polygon'), parcels, history.dates, 4, 8, history.parkingFrom)
const dates = history.evidence === undefined ? dated : applyEvidence(dated, history.evidence)
const traced = new Map(history.traced.map((b) => [b.id, b]))
const out: Record<string, Record<string, unknown>> = {}
for (const p of plates) {
  const [fl, ys] = p.split(':'); const y = Number(ys)
  const sc = buildScene(region, features, palette('paper'), sampler(dem), { time: { year: y, history, dates }, flood: parseFlood(region, fl) })
  const t = sc.terrain, lv = sc.flood!.level
  out[p] = {}
  // The whole plate: buildings shown and in water, confirmed and unconfirmed apart.
  {
    const n = { shown: 0, shownUnconfirmed: 0, inWater: 0, inWaterUnconfirmed: 0 }
    for (const it of whole(sc.items)) {
      if (it.kind !== 'building' || it.footprint === undefined || it.id.startsWith('floodwall')) continue
      const cc = centroid(it.footprint)
      const unc = it.id.startsWith('traced:') ? (() => { const tb = traced.get(it.id.slice(7)); return tb !== undefined && unconfirmedTraced(tb, y) })() : unconfirmedDated(dates.get(it.id.split('.')[0]), y)
      const w = [...it.footprint, cc].some((q) => { const l = levelAt(t, lv, q); return !Number.isNaN(l) && l > t.elevation(q) })
      n.shown++; if (unc) n.shownUnconfirmed++
      if (w) { n.inWater++; if (unc) n.inWaterUnconfirmed++ }
    }
    out[p].plate = { acres: sc.stats.floodAcres, outbuildingsHidden: sc.stats.outbuildingsHidden ?? 0, ...n }
  }
  for (const b of allBoxes) {
    const [W, H] = b.size
    const hw = W / 2 / sc.view.scale, hd = H / 2 / sc.view.scale / sc.view.squash
    const c = sc.view.toView(b.at[0], b.at[1])
    const inBox = (q: readonly number[]) => Math.abs(q[0] - c[0]) <= hw && Math.abs(q[1] - c[1]) <= hd
    // The depth at the box's named place (`depthAt`, a gauge's place), else at its center.
    const dp = b.depthAt ?? b.at
    const L = levelAt(t, lv, sc.view.toView(dp[0], dp[1]))
    const g = ground2(dp[0], dp[1])
    let wet = 0, cells = 0
    for (let j = 0; j < t.ny; j++) for (let i = 0; i < t.nx; i++) {
      const q = [t.x0 + i * t.cell, t.y0 + j * t.cell]
      if (!inBox(q)) continue
      cells++
      if (sc.flood!.flooded[j * t.nx + i] !== 0 && t.water[j * t.nx + i] !== 1) wet++
    }
    const n = { shown: 0, shownUnconfirmed: 0, inWater: 0, inWaterUnconfirmed: 0 }
    for (const it of whole(sc.items)) {
      if (it.kind !== 'building' || it.footprint === undefined || it.id.startsWith('floodwall')) continue
      const cc = centroid(it.footprint)
      if (!inBox(cc)) continue
      const unc = it.id.startsWith('traced:') ? (() => { const tb = traced.get(it.id.slice(7)); return tb !== undefined && unconfirmedTraced(tb, y) })() : unconfirmedDated(dates.get(it.id.split('.')[0]), y)
      const w = [...it.footprint, cc].some((q) => { const l = levelAt(t, lv, q); return !Number.isNaN(l) && l > t.elevation(q) })
      n.shown++; if (unc) n.shownUnconfirmed++
      if (w) { n.inWater++; if (unc) n.inWaterUnconfirmed++ }
    }
    out[p][b.id] = { depthFt: Number.isNaN(L) || L <= g ? 0 : Number(((L - g) / 0.3048).toFixed(2)), ...(b.depthAt === undefined ? {} : { depthAtPlace: true }), groundM: Number(g.toFixed(2)), acresWet: Number((wet * t.cell * t.cell / 4046.86).toFixed(1)), ...n }
  }
  console.error(p, JSON.stringify(out[p]))
}
console.log(JSON.stringify(out, null, 1))

/** A building drawn in pieces (`<id>#<k>`, occlusion "strict") as one: its pieces' outlines' points together. */
function whole<T extends { id: string; footprint?: readonly (readonly [number, number])[]; hull: readonly (readonly [number, number])[] }>(items: readonly T[]): T[] {
  const out = new Map<string, T>()
  for (const it of items) {
    const id = it.id.split('#')[0]
    const prev = out.get(id)
    if (prev === undefined) out.set(id, { ...it, id })
    else out.set(id, { ...prev, footprint: [...(prev.footprint ?? prev.hull), ...(it.footprint ?? it.hull)] })
  }
  return [...out.values()]
}
