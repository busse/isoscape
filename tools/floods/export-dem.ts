/**
 * Dev tool (floods spike): write a window of a region's cached elevation, as isoscape reads it
 * (aligned to the served box, voids marked missing), to a raw float32 file plus a JSON header,
 * for the Python spill-path analysis (spill.py). No blur, no resampling: the cached pixels.
 *
 *   node tools/floods/export-dem.ts <data-dir> <west> <south> <east> <north> <out-prefix>
 */
import { writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { cleanDem, loadDem } from '../../src/dem.ts'

const [dir, w, s, e, n, out] = process.argv.slice(2)
const dem = await loadDem(resolve(dir, 'dem.bin.gz'))
if (dem === null) throw new Error(`no elevation in ${dir}`)
const voids = cleanDem(dem)
const px = (dem.east - dem.west) / dem.width
const py = (dem.north - dem.south) / dem.height
const x0 = Math.max(0, Math.floor((Number(w) - dem.west) / px))
const x1 = Math.min(dem.width, Math.ceil((Number(e) - dem.west) / px))
const y0 = Math.max(0, Math.floor((dem.north - Number(n)) / py))
const y1 = Math.min(dem.height, Math.ceil((dem.north - Number(s)) / py))
const width = x1 - x0
const height = y1 - y0
const data = new Float32Array(width * height)
for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) data[y * width + x] = dem.data[(y0 + y) * dem.width + x0 + x]
writeFileSync(`${out}.f32`, Buffer.from(data.buffer))
writeFileSync(`${out}.json`, JSON.stringify({
  west: dem.west + x0 * px, north: dem.north - y0 * py, east: dem.west + x1 * px, south: dem.north - y1 * py,
  width, height, source: dem.source ?? '3dep', voidsInWholeCache: voids, note: 'row 0 at the north edge; pixel centers at half a pixel in',
}, null, 1))
console.error(`wrote ${out}.f32 (${width}×${height})`)
