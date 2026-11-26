/**
 * Floods series rc1: which items paint a point of a plate (SVG units), top first, with each
 * traced footprint's share covered by today's buildings drawn that year (`coveredShare`).
 *
 *   node tools/floods/rc1/which.ts <area> <flood>:<year> <x>,<y> ...
 */
import { readFileSync } from 'node:fs'
import { loadRegion } from '../../../src/region.ts'
import { parseOsm, type PolygonFeature } from '../../../src/osm.ts'
import { cleanDem, loadDem, sampler } from '../../../src/dem.ts'
import { buildScene, coveredShare } from '../../../src/scene.ts'
import { palette, withFloodStyles } from '../../../src/palette.ts'
import { parseFlood } from '../../../src/flood.ts'
import { pointInRing, type Vec2 } from '../../../src/geom.ts'
import { applyEvidence, dateBuildings, loadHistory, loadYearBuilt, yearBuiltDirs } from '../../../src/history.ts'

const [area, plate, ...pts] = process.argv.slice(2)
const region = { ...(await loadRegion(`richmond-floods-${area}`)), ...(process.env.NOCOVER === '1' ? { tracedCovered: undefined } : {}) }
const dir = `data/${region.data ?? region.name}`
const features = parseOsm(readFileSync(`${dir}/osm.json`, 'utf8'))
const dem = (await loadDem(`${dir}/dem.bin.gz`))!
cleanDem(dem)
const history = await loadHistory(region.time!.history)
const parcels = (await loadYearBuilt(yearBuiltDirs(region, 'data'), region.time!.yearBuilt!.field, region.name)).parcels
const dated = dateBuildings(features.filter((f): f is PolygonFeature => f.type === 'polygon'), parcels, history.dates, 4, 8, history.parkingFrom)
const dates = history.evidence === undefined ? dated : applyEvidence(dated, history.evidence)
const [fl, ys] = plate.split(':')
const sc = buildScene(region, features, withFloodStyles(palette(region.palette), region.floodStyles ?? []), sampler(dem), { time: { year: Number(ys), history, dates }, flood: parseFlood(region, fl) })
const today = sc.items.filter((it) => it.kind === 'building' && !it.id.startsWith('traced:') && !it.id.startsWith('flood') && it.footprint !== undefined).map((it) => ({ outer: it.footprint! }))
for (const s of pts) {
  const p = s.split(',').map(Number) as unknown as Vec2
  const hits = sc.items.filter((it) => it.shapes.some((sh) => sh.pts.length >= 3 && sh.line !== true && pointInRing(p, sh.pts)))
  console.log(s)
  for (const it of hits) {
    const cov = it.id.startsWith('traced:') && it.footprint !== undefined ? ` covered ${coveredShare(it.footprint, today).toFixed(2)}` : ''
    console.log(`  ${it.id} key ${it.key.toFixed(1)} z ${it.zMin.toFixed(1)}-${it.zMax.toFixed(1)}${cov}`)
  }
}
