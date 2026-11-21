// Export each OSM building's year (curated, start_date or assessor parcel) for the Sanborn tools.
import { readFile, writeFile } from 'node:fs/promises'
import { parseOsm, type PolygonFeature } from '../../src/osm.ts'
import { dateBuildings, loadHistory, parseParcels } from '../../src/history.ts'
import { loadRegion } from '../../src/region.ts'

const region = await loadRegion(process.argv[2] ?? 'richmond-downtown-time')
const features = parseOsm(await readFile(`data/${region.data ?? region.name}/osm.json`, 'utf8'))
const history = await loadHistory(region.time!.history)
const parcels = parseParcels(await readFile(`data/${region.name}/yearbuilt.json`, 'utf8'), region.time!.yearBuilt!.field)
const polys = features.filter((f): f is PolygonFeature => f.type === 'polygon' && f.tags.building !== undefined)
const d = dateBuildings(polys, parcels, history.dates, 4, 8, history.parkingFrom)
const out = polys.map((p) => ({ id: p.id, year: d.get(p.id)?.year ?? null, ring: p.outers[0] }))
await writeFile(process.argv[3] ?? 'data/sanborn/buildings.json', JSON.stringify(out))
console.log(out.length, 'buildings,', out.filter((o) => o.year !== null).length, 'dated')
