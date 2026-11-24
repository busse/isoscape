// Read-only: city blocks (data/sanborn/blocks.json) in the Shockoe Bottom area of coverage.ts whose center ground is under the Agnes level.
import { readFileSync } from 'node:fs'
import { loadDem, cleanDem, sampler } from '/home/claude/wt-floods/src/dem.ts'
const W = '/home/claude/wt-floods/'
const raw = JSON.parse(readFileSync(W + 'data/sanborn/blocks.json', 'utf8'))
const feats = raw.features ?? raw
const dem = (await loadDem(W + 'data/richmond-i195-rocketts/dem.bin.gz'))!; cleanDem(dem); const z = sampler(dem)
let n = 0, wet = 0, part = 0
for (const f of feats) {
  const g = f.geometry ?? f
  const ring: number[][] = (g.rings ?? g.coordinates)[0]
  let lon = 0, lat = 0; for (const [x, y] of ring) { lon += x; lat += y }; lon /= ring.length; lat /= ring.length
  if (Math.abs(lon) > 180) { console.log('projected coords, stop'); break }
  const river = 37.5277 - 0.39 * (lon + 77.4345)
  if (!(lon > -77.4330 && lon < -77.4245 && lat < 37.5365 && lat > river + 0.0012)) continue
  n++
  const zs = ring.map(([x, y]) => z(x, y)).concat([z(lon, lat)])
  if (z(lon, lat) < 10.82) wet++; else if (Math.min(...zs) < 10.82) part++
}
console.log(JSON.stringify({ blocksInArea: n, centerUnderAgnes: wet, edgeOnlyUnderAgnes: part }))
