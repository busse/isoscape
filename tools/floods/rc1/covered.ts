/**
 * Floods series rc1: for every traced footprint a plate draws, the share of it under today's
 * buildings drawn that year (`coveredShare`), and the m² under them; also traced footprints
 * that overlap another traced one. JSON to stdout, a summary to stderr.
 *
 *   node tools/floods/rc1/covered.ts <area> <flood>:<year> ...
 */
import { readFileSync } from 'node:fs'
import { loadRegion } from '../../../src/region.ts'
import { parseOsm, type PolygonFeature } from '../../../src/osm.ts'
import { cleanDem, loadDem, sampler } from '../../../src/dem.ts'
import { buildScene, coveredShare } from '../../../src/scene.ts'
import { palette, withFloodStyles } from '../../../src/palette.ts'
import { parseFlood } from '../../../src/flood.ts'
import { centroid, signedArea, type Vec2 } from '../../../src/geom.ts'
import { applyEvidence, dateBuildings, loadHistory, loadYearBuilt, yearBuiltDirs } from '../../../src/history.ts'

const [area, ...plates] = process.argv.slice(2)
const region = await loadRegion(`richmond-floods-${area}`)
const dir = `data/${region.data ?? region.name}`
const features = parseOsm(readFileSync(`${dir}/osm.json`, 'utf8'))
const dem = (await loadDem(`${dir}/dem.bin.gz`))!
cleanDem(dem)
const history = await loadHistory(region.time!.history)
const parcels = (await loadYearBuilt(yearBuiltDirs(region, 'data'), region.time!.yearBuilt!.field, region.name)).parcels
const dated = dateBuildings(features.filter((f): f is PolygonFeature => f.type === 'polygon'), parcels, history.dates, 4, 8, history.parkingFrom)
const dates = history.evidence === undefined ? dated : applyEvidence(dated, history.evidence)
const out: Record<string, unknown> = {}
for (const p of plates) {
  const [fl, ys] = p.split(':')
  const sc = buildScene(region, features, withFloodStyles(palette(region.palette), region.floodStyles ?? []), sampler(dem), { time: { year: Number(ys), history, dates }, flood: parseFlood(region, fl) })
  const today = sc.items.filter((it) => it.kind === 'building' && !it.id.startsWith('traced:') && !it.id.startsWith('flood') && it.footprint !== undefined).map((it) => ({ outer: it.footprint! }))
  // A traced building's pieces, joined back by id: the ring is the convex pieces' union, taken here as the list of pieces.
  const traced = new Map<string, Vec2[][]>()
  for (const it of sc.items) if (it.id.startsWith('traced:') && it.footprint !== undefined) {
    const id = it.id.split('#')[0]
    traced.set(id, [...(traced.get(id) ?? []), it.footprint as Vec2[]])
  }
  const rows: { id: string; share: number; m2: number; area: number; at: number[] }[] = []
  for (const [id, pieces] of traced) {
    let a = 0, under = 0
    for (const r of pieces) { const s = coveredShare(r, today); const ar = Math.abs(signedArea(r)); a += ar; under += s * ar }
    if (under <= 0) continue
    const big = pieces.reduce((m, r) => (Math.abs(signedArea(r)) > Math.abs(signedArea(m)) ? r : m))
    rows.push({ id, share: Number((under / a).toFixed(2)), m2: Number(under.toFixed(1)), area: Number(a.toFixed(1)), at: sc.view.toScreen(centroid(big), 0).map((v) => Number(v.toFixed(1))) })
  }
  rows.sort((x, y) => y.m2 - x.m2)
  const bands = [0.05, 0.25, 0.5].map((t) => rows.filter((r) => r.share >= t).length)
  out[p] = { tracedDrawn: traced.size, overlapping: rows.length, atLeast5pct: bands[0], atLeast25pct: bands[1], atLeast50pct: bands[2], rows }
  console.error(p, 'traced drawn', traced.size, 'under today at all', rows.length, '>=5%', bands[0], '>=25%', bands[1], '>=50%', bands[2], 'm2 >= 20:', rows.filter((r) => r.m2 >= 20).length)
}
console.log(JSON.stringify(out, null, 1))
