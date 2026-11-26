/**
 * Dev tool (floods series, period city): the buildings whose presence the evidence pass has to
 * call, for one region's frame.
 *
 *   node tools/floods/period/inventory.ts <region> > out.json
 *
 * Two lists, with outlines in lon/lat:
 *   traced:  traced Sanborn buildings gone today whose end is `assumed` (no map, rebuild or
 *            highway dates their loss), with any part in the frame;
 *   undated: today's OSM buildings with no year built (no curated date, no start_date, no
 *            parcel year), at least the region's minBuildingArea, wholly in the frame.
 * Reads the caches only.
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { loadRegion } from '../../../src/region.ts'
import { parseOsm, type PolygonFeature } from '../../../src/osm.ts'
import { makeView } from '../../../src/view.ts'
import { signedArea } from '../../../src/geom.ts'
import { dateBuildings, loadHistory, loadYearBuilt, yearBuiltDirs } from '../../../src/history.ts'

const name = process.argv[2]
const region = await loadRegion(name)
const dir = resolve('data', region.data ?? region.name)
const features = parseOsm(readFileSync(resolve(dir, 'osm.json'), 'utf8'))
const history = await loadHistory(resolve(region.time!.history))
const parcels = (await loadYearBuilt(yearBuiltDirs(region, resolve('data')), region.time!.yearBuilt!.field, name)).parcels
const polys = features.filter((f): f is PolygonFeature => f.type === 'polygon')
const dates = dateBuildings(polys, parcels, history.dates, 4, 8, history.parkingFrom)
const view = makeView(region, region.bearing ?? 0)
const fr = view.frame
const inside = (lon: number, lat: number) => {
  const [x, y] = view.toView(lon, lat)
  return x >= fr.minX && x <= fr.maxX && y >= fr.minY && y <= fr.maxY
}
const minArea = region.minBuildingArea ?? 12
const traced = history.traced
  .filter((b) => b.end === 'assumed' && b.ring.some(([x, y]) => inside(x, y)))
  .map((b) => ({ id: b.id, ring: b.ring, from: b.from, to: b.to, end: b.end, storeys: b.storeys, material: b.material, edition: b.edition, sheet: b.sheet }))
const undated = polys
  .filter((f) => (f.tags.building !== undefined || f.tags['building:part'] !== undefined) && !dates.has(f.id) && !dates.has(f.id.split('.')[0]))
  .filter((f) => f.outers[0].every(([x, y]) => inside(x, y)))
  .filter((f) => {
    const ring = f.outers[0].map(([x, y]) => view.toView(x, y))
    return Math.abs(signedArea(ring)) >= minArea
  })
  .map((f) => ({ id: f.id, ring: f.outers[0], building: f.tags.building ?? f.tags['building:part'], part: f.tags['building:part'] !== undefined && f.tags.building === undefined, name: f.tags.name, source: f.tags.source }))
const frame = [[fr.minX, fr.minY], [fr.maxX, fr.minY], [fr.maxX, fr.maxY], [fr.minX, fr.maxY]].map((p) => view.fromView(p as [number, number]))
console.error(name, 'traced (assumed end, in frame):', traced.length, 'undated today:', undated.length)
console.log(JSON.stringify({ region: name, frame, traced, undated }))
