// Read-only: traced Sanborn buildings standing in 1952 but not drawn in 1969/1972, by area,
// and how many sit on ground below the Agnes level (10.82 m NAVD88 at the Locks; +0.4 m by Mayo Bridge).
import { readFileSync } from 'node:fs'
import { loadDem, cleanDem, sampler } from '/home/claude/wt-floods/src/dem.ts'
const W = '/home/claude/wt-floods/'
const lost = JSON.parse(readFileSync(W + 'history/sanborn/lost.geojson', 'utf8'))
const drop1 = new Set((JSON.parse(readFileSync(W + 'history/sanborn/clean-dropped.json', 'utf8')) as any[]).map(d => d.id))
const sh = JSON.parse(readFileSync(W + 'history/sanborn/clean-shapes.json', 'utf8'))
const drop2 = new Set(Object.entries(sh).filter(([k]) => k !== 'trim' && k !== 'smooth').flatMap(([, v]) => Array.isArray(v) ? v : []))
const dem = (await loadDem(W + 'data/richmond-i195-rocketts/dem.bin.gz'))!
cleanDem(dem)
const z = sampler(dem)
const area = (lon: number, lat: number): string => {
  const river = 37.5277 - 0.39 * (lon + 77.4345)
  if (lat < river - 0.0008) return 'manchester (south bank)'
  if (lat < river + 0.0012) return 'riverfront and islands'
  if (lat > 37.5365) return 'north of Broad Street'
  if (lon > -77.4245) return 'Church Hill foot and Rocketts'
  if (lon < -77.4330) return 'Shockoe Slip and downtown'
  return 'Shockoe Bottom'
}
const by: Record<string, any> = {}
const ids: any[] = []
for (const f of lost.features) {
  const p = f.properties
  if (drop1.has(p.id) || drop2.has(p.id)) continue
  if (!(p.from <= 1952 && p.to > 1952)) continue   // standing in 1952
  if (p.to > 1969) continue                         // already drawn in 1969
  const ring = f.geometry.coordinates[0]
  let lon = 0, lat = 0
  for (const [x, y] of ring) { lon += x; lat += y }
  lon /= ring.length; lat /= ring.length
  const a = area(lon, lat)
  const g = z(lon, lat)
  const level = 10.82 + (lon < -77.4345 ? 0.4 : 0)
  by[a] ??= { total: 0, assumed: 0, highway: 0, rebuilt: 0, map: 0, belowAgnes: 0, belowAgnesAssumed: 0, area_m2: 0 }
  const b = by[a]
  b.total++; b[p.end] = (b[p.end] ?? 0) + 1
  if (g < level) { b.belowAgnes++; if (p.end === 'assumed') { b.belowAgnesAssumed++; ids.push({ id: p.id, lon, lat, ground: +g.toFixed(2), storeys: p.storeys, material: p.material, sheet: p.sheet, edition: p.edition }) } }
}
console.log(JSON.stringify({ about: 'Traced Sanborn buildings standing in 1952 and not drawn in 1969 (to <= 1969), from wt-floods history/sanborn/lost.geojson less clean.py drops; centroid ground from the 2 m cache vs Agnes 10.82 m NAVD88 (+0.4 m west of Mayo Bridge). Ground only: no connectivity test.', byArea: by }, null, 1))
import { writeFileSync } from 'node:fs'
writeFileSync('/home/claude/floods-research/period-city/scripts/dropped-below-agnes.json', JSON.stringify(ids, null, 0))
