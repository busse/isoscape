/**
 * Dev tool (floods series): where a dated flood view's buildings come from, by area and by
 * evidence class, so the captions can say what each year's picture can and cannot claim.
 *
 *   node tools/floods/coverage.ts <region> [--history <file>] <year>...
 *
 * `--history` reads another history file than the region's (the before of a comparison).
 *
 * Classes: `today` (standing today, dated by the assessor, OSM or a curated date), `todaySeen`
 * and `todayUnconfirmed` (today's undated buildings dated by the evidence layer, confirmed for
 * the year or not), `traced` (a traced building whose end a map, a rebuild or a highway dates,
 * or assumed), `tracedSeen` and `tracedUnconfirmed` (a traced building whose end the evidence
 * dates), `curated`.
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { loadRegion } from '../../src/region.ts'
import { parseOsm, type PolygonFeature } from '../../src/osm.ts'
import { cleanDem, loadDem, sampler } from '../../src/dem.ts'
import { buildScene } from '../../src/scene.ts'
import { palette } from '../../src/palette.ts'
import { centroid } from '../../src/geom.ts'
import { applyEvidence, dateBuildings, loadHistory, loadYearBuilt, unconfirmedDated, unconfirmedTraced, yearBuiltDirs } from '../../src/history.ts'

const argv = process.argv.slice(2)
const hi = argv.indexOf('--history')
const historyFile = hi >= 0 ? argv.splice(hi, 2)[1] : undefined
const [name, ...years] = argv
const region = await loadRegion(name)
const dir = resolve('data', region.data ?? region.name)
const features = parseOsm(readFileSync(resolve(dir, 'osm.json'), 'utf8'))
const dem = (await loadDem(resolve(dir, 'dem.bin.gz')))!
cleanDem(dem)
const history = await loadHistory(resolve(historyFile ?? region.time!.history))
const parcels = (await loadYearBuilt(yearBuiltDirs(region, resolve('data')), region.time!.yearBuilt!.field, name)).parcels
const dated = dateBuildings(features.filter((f): f is PolygonFeature => f.type === 'polygon'), parcels, history.dates, 4, 8, history.parkingFrom)
const dates = history.evidence === undefined ? dated : applyEvidence(dated, history.evidence)
const tracedById = new Map(history.traced.map((b) => [b.id, b]))
// Areas by lon/lat: the river's north bank east of 14th Street is Shockoe Bottom and Rocketts
// (split at 21st Street); south of the river, Manchester.
const area = (lon: number, lat: number): string => {
  // The river's line, from the Mayo Bridge (37.5277, -77.4345) to Rocketts (37.5210, -77.4175).
  const river = 37.5277 - 0.39 * (lon + 77.4345)
  if (lat < river - 0.0008) return 'manchester (south bank)'
  if (lat < river + 0.0012) return 'riverfront and islands'
  if (lat > 37.5365) return 'north of Broad Street'
  if (lon > -77.4245) return 'Church Hill foot and Rocketts'
  if (lon < -77.4330) return 'Shockoe Slip and downtown'
  return 'Shockoe Bottom'
}
const out: Record<string, unknown> = {}
for (const y of years.map(Number)) {
  const sc = buildScene(region, features, palette('paper'), sampler(dem), { time: { year: y, history, dates } })
  type Count = { today: number; todaySeen: number; todayUnconfirmed: number; traced: number; tracedSeen: number; tracedUnconfirmed: number; curated: number }
  const zero = (): Count => ({ today: 0, todaySeen: 0, todayUnconfirmed: 0, traced: 0, tracedSeen: 0, tracedUnconfirmed: 0, curated: 0 })
  const by: Record<string, Count> = {}
  for (const it of whole(sc.items)) {
    if (it.kind !== 'building' || it.id.startsWith('floodwall')) continue
    const [lon, lat] = sc.view.fromView(centroid(it.footprint ?? it.hull))
    const a = area(lon, lat)
    by[a] ??= zero()
    by.all ??= zero()
    const k: keyof Count = it.id.startsWith('traced:')
      ? (() => {
          const b = tracedById.get(it.id.slice(7))
          if (b?.end !== 'evidence') return 'traced'
          return unconfirmedTraced(b, y) ? 'tracedUnconfirmed' : 'tracedSeen'
        })()
      : it.id.startsWith('history:') ? 'curated'
        : (() => {
            const d = dates.get(it.id.split('.')[0])
            if (d?.source !== 'evidence') return 'today'
            return unconfirmedDated(d, y) ? 'todayUnconfirmed' : 'todaySeen'
          })()
    by[a][k]++
    by.all[k]++
  }
  out[y] = by
  console.error(y, JSON.stringify(by))
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
