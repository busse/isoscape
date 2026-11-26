/**
 * Floods series: list every place a plate paints something over a nearer item (src/occlusion.ts),
 * and every building a floodwall runs within 15 m of.
 *
 *   [STRICT=0] node tools/floods/d3/occlusion.ts <area> <flood>:<year> ... > out.json
 *
 * The paint order is read from the rendered SVG (`data-id` groups, `data-under` for x-ray bands);
 * the geometry from the scene's items. Labels and gauge figures are left out: they are set over
 * everything by convention. Classes: building (OSM), traced, wall (a floodwall piece), gate, band
 * (an x-ray band), bridge, gauge. Pairs of one wall's own pieces at a joint are listed apart
 * ("wall joints"), as are pieces of one building split for drawing (never judged).
 */
import { readFileSync } from 'node:fs'
import { loadRegion } from '../../../src/region.ts'
import { parseOsm, type PolygonFeature } from '../../../src/osm.ts'
import { cleanDem, loadDem, sampler } from '../../../src/dem.ts'
import { buildScene, type Item } from '../../../src/scene.ts'
import { renderSvg } from '../../../src/render.ts'
import { palette, withFloodStyles } from '../../../src/palette.ts'
import { parseFlood } from '../../../src/flood.ts'
import { centroid } from '../../../src/geom.ts'
import { footprintOverlap, overPaints, type Painted } from '../../../src/occlusion.ts'
import { applyEvidence, dateBuildings, loadHistory, loadYearBuilt, yearBuiltDirs } from '../../../src/history.ts'

const [area, ...plates] = process.argv.slice(2)
const loaded = await loadRegion(`richmond-floods-${area}`)
// STRICT=0: the region as drawn before `occlusion: "strict"` (for a before-and-after count).
const region = process.env.STRICT === '0' ? { ...loaded, occlusion: undefined } : loaded
const dir = `data/${region.data ?? region.name}`
const features = parseOsm(readFileSync(`${dir}/osm.json`, 'utf8'))
const dem = (await loadDem(`${dir}/dem.bin.gz`))!
cleanDem(dem)
const history = await loadHistory(region.time!.history)
const parcels = (await loadYearBuilt(yearBuiltDirs(region, 'data'), region.time!.yearBuilt!.field, region.name)).parcels
const dated = dateBuildings(features.filter((f): f is PolygonFeature => f.type === 'polygon'), parcels, history.dates, 4, 8, history.parkingFrom)
const dates = history.evidence === undefined ? dated : applyEvidence(dated, history.evidence)
const pal = withFloodStyles(palette(region.palette), region.floodStyles ?? [])
const base = (id: string) => id.split('#')[0]
export const classOf = (id: string): string =>
  id.startsWith('band:') ? 'band' : id.startsWith('floodwall:') ? 'wall' : id.startsWith('floodgate:') ? 'gate' : id.startsWith('floodgauge:') ? 'gauge'
    : id.startsWith('traced:') ? 'traced' : /\.\d+\.\d+/.test(id) || id.includes('pier') ? 'bridge' : 'building'
const out: Record<string, unknown> = {}
for (const p of plates) {
  const [fl, ys] = p.split(':')
  const year = Number(ys)
  const sc = buildScene(region, features, pal, sampler(dem), { time: { year, history, dates }, flood: parseFlood(region, fl) })
  const svg = renderSvg(sc).svg
  const byId = new Map<string, Item>(sc.items.map((it) => [it.id, it]))
  const order: Painted[] = []
  for (const m of svg.matchAll(/<g data-(id|under)="([^"]+)">/g)) {
    const it = byId.get(m[2])
    if (it !== undefined) order.push(m[1] === 'under' ? { item: it, band: true } : { item: it })
  }
  // A band kept off nearer items by a mask (occlusion "strict") is not painted over them.
  const cuts = new Map<string, Set<string>>()
  for (const m of svg.matchAll(/data-cut="([^"]*)"><g data-under="([^"]+)">/g)) cuts.set(m[2], new Set(m[1].split(' ')))
  const tag = (x: Painted) => (x.band === true ? 'band:' : '') + x.item.id
  const found = overPaints(sc.view, order, { skip: (a, b) => base(a.item.id) === base(b.item.id) || (b.band === true && cuts.get(b.item.id)?.has(tag(a)) === true) })
  const wallJoint = (o: { over: string; under: string }) => classOf(o.over.replace('band:', '')) === 'wall' && classOf(o.under.replace('band:', '')) === 'wall' && o.over.replace('band:', '').split('.')[0] === o.under.replace('band:', '').split('.')[0]
  const ring = (id: string) => { const it = byId.get(id.replace('band:', '')); return it?.footprint ?? it?.hull ?? [] }
  const cases = found.map((o) => {
    const ov = footprintOverlap(ring(o.over), ring(o.under))
    const ovArea = footprintOverlap(ring(o.over), ring(o.under), 0.25, true)
    const kinds = `${o.over.startsWith('band:') ? 'band' : classOf(o.over)} over ${o.under.startsWith('band:') ? 'band' : classOf(o.under)}`
    // Classes judged apart: footprints that overlap on the ground by over 5% of the smaller or 1 m² (two
    // buildings mapped on one spot, or a band on one of them: the data, not the order), and bridge against bridge (sloped decks, not prisms).
    const kind = wallJoint(o) ? 'joint' : ov > 0.05 || ovArea >= 1 ? 'overlap' : kinds === 'bridge over bridge' ? 'decks' : 'order'
    return { ...o, kinds, overlap: Number(ov.toFixed(2)), overlapM2: Number(ovArea.toFixed(1)), kind }
  })
  const counts: Record<string, number> = {}
  for (const c of cases) if (c.kind === 'order') counts[c.kinds] = (counts[c.kinds] ?? 0) + 1
  const classes: Record<string, number> = {}
  for (const c of cases) classes[c.kind] = (classes[c.kind] ?? 0) + 1
  // Buildings within 15 m of a floodwall piece (view meters, footprint to footprint).
  const walls = sc.items.filter((it) => it.id.startsWith('floodwall:'))
  const near: { id: string; name?: string; m: number; at: number[]; lonlat: number[] }[] = []
  for (const it of sc.items) {
    if (it.kind !== 'building' || it.id.startsWith('flood') || it.footprint === undefined) continue
    let best = Infinity
    for (const w of walls) for (const a of w.footprint ?? w.hull) for (const b of it.footprint) best = Math.min(best, Math.hypot(a[0] - b[0], a[1] - b[1]))
    if (best <= 15) {
      const c = centroid(it.footprint)
      const top = sc.view.toScreen(c, it.zMin)
      near.push({ id: it.id, ...(it.name === undefined ? {} : { name: it.name }), m: Number(best.toFixed(1)), at: top.map((v) => Number(v.toFixed(1))), lonlat: sc.view.fromView(c).map((v) => Number(v.toFixed(6))) })
    }
  }
  out[p] = { classes, counts, cases: process.env.JOINTS === '1' ? cases : cases.filter((c) => c.kind !== 'joint'), nearWall: near.sort((a, b) => a.at[0] - b.at[0]) }
  console.error(p, JSON.stringify(classes), JSON.stringify(counts), 'buildings within 15 m of a wall', near.length)
}
console.log(JSON.stringify(out, null, 1))
