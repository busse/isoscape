#!/usr/bin/env node
/**
 * The data behind the Jackson Ward story's method charts, in the story region's view meters
 * (E' across the frame, N' into it), written as one JSON file for charts.py:
 *
 *   node tools/stories/jackson-ward/data.ts [out.json]   # default out/stories/jackson-ward/data.json
 *
 * It runs the same code the 1952 build does (`makeTerrain`, `restoreGround`, `lowerGround` in
 * src/terrain.ts) on the region's cached lidar, so the charts show the ground the maps are drawn
 * on: today's ground, the rebuilt pre-1955 ground, and the rebuilt ground without the street
 * lines (the membrane alone). It adds what the charts draw over it: today's streets (OSM), the
 * restoration outlines and the seven streets held at grade (history/jackson-ward.json), the
 * count's polygons (tools/sanborn/jw/highway-footprint.geojson), the traced 1952 buildings'
 * centers by sheet, the 1934 check points and the fit's control points (from the trace's
 * residuals.csv, if given with --residuals).
 */

import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { loadRegion } from '../../../src/region.ts'
import { makeView } from '../../../src/view.ts'
import { cleanDem, loadDem, sampler } from '../../../src/dem.ts'
import { makeTerrain, restoreGround, lowerGround, type HeightGrid } from '../../../src/terrain.ts'
import { parseOsm } from '../../../src/osm.ts'
import { centroid, type Vec2 } from '../../../src/geom.ts'

const args = process.argv.slice(2)
const flag = (name: string): string | undefined => { const i = args.indexOf(name); return i < 0 ? undefined : args[i + 1] }
const out = resolve(args.find((a, i) => !a.startsWith('--') && (i === 0 || !args[i - 1].startsWith('--'))) ?? 'out/stories/jackson-ward/data.json')

const region = await loadRegion('jackson-ward')
const view = makeView(region, region.bearing)
const dem = await loadDem(resolve('data', region.data ?? region.name, 'dem.bin.gz'))
if (dem === null) throw new Error('no cached lidar for the jackson-ward region (data/richmond-streetcars)')
cleanDem(dem)
const sample = sampler(dem)
const history = JSON.parse(await readFile('history/jackson-ward.json', 'utf8')) as {
  ground: { id: string; method?: string; radius?: number; rings: [number, number][][]; lines?: { name: string; line: [number, number][] }[] }[]
}
const cell = region.terrain?.cell ?? 5
const v = (p: readonly number[]): Vec2 => { const q = view.toView(p[0], p[1]); return [Math.round(q[0] * 100) / 100, Math.round(q[1] * 100) / 100] }

/** The ground, as the build makes it: lidar, then a restoration (or none), then the light blur. */
const grid = (lines: boolean | null) => makeTerrain(view, cell, 1, sample, lines === null ? undefined : (g: HeightGrid) => {
  for (const r of history.ground) {
    const rings = r.rings.map((ring) => ring.map((p) => view.toView(p[0], p[1])))
    if (r.method === 'lower') lowerGround(g, rings, r.radius)
    else restoreGround(g, rings, lines ? (r.lines ?? []).map((l) => ({ pts: l.line.map((p) => view.toView(p[0], p[1])) })) : [])
  }
})
const today = grid(null)
const rebuilt = grid(true)
const membrane = grid(false)
const round = (a: Float32Array) => Array.from(a, (x) => Math.round(x * 100) / 100)

// Today's streets and highway ways, for the plans' base.
const features = parseOsm(await readFile(resolve('data', region.data ?? region.name, 'osm.json'), 'utf8'))
const f = view.frame
const near = (p: Vec2) => p[0] > f.minX - 300 && p[0] < f.maxX + 300 && p[1] > f.minY - 300 && p[1] < f.maxY + 300
const streets: { kind: string; name: string; pts: Vec2[] }[] = []
const buildings: Vec2[][] = []
for (const ft of features) {
  if (ft.type === 'line' && ft.tags.highway !== undefined) {
    const pts = ft.points.map(v)
    if (pts.some(near)) streets.push({ kind: ft.tags.highway, name: ft.tags.name ?? '', pts })
  } else if (ft.type === 'polygon' && ft.tags.building !== undefined) {
    const ring = ft.outers[0].map(v)
    if (near(centroid(ring))) buildings.push(ring)
  }
}

const foot = JSON.parse(await readFile('tools/sanborn/jw/highway-footprint.geojson', 'utf8')) as { features: { properties: { name: string }; geometry: { type: string; coordinates: any } }[] }
const footprint = Object.fromEntries(foot.features.map((ft) => {
  const polys: number[][][][] = ft.geometry.type === 'Polygon' ? [ft.geometry.coordinates] : ft.geometry.coordinates
  return [ft.properties.name, polys.map((poly) => poly.map((ring) => ring.map(v)))]
}))
const traced = JSON.parse(await readFile('history/sanborn/jackson-ward-1952.geojson', 'utf8')) as { features: { properties: { sheet: string; area: number; material: string; coverage?: unknown }; geometry: { coordinates: number[][][] } }[] }
// The edition file also holds each sheet's coverage outline: not a building (count.py skips it too).
const tracedOut = traced.features.filter((ft) => !ft.properties.coverage).map((ft) => {
  const ring = ft.geometry.coordinates[0].slice(0, -1).map(v)
  return { sheet: ft.properties.sheet, area: ft.properties.area, material: ft.properties.material, c: centroid(ring), ring }
})

// The twelve check points along the trench's center line (ground.md, check 2).
const checks: [string, number, number][] = [
  ['P1', 37.55499, -77.44662], ['P2', 37.55367, -77.44512], ['P3', 37.55246, -77.44333], ['P4', 37.55186, -77.44186],
  ['P5', 37.55122, -77.44026], ['P6', 37.5511, -77.4387], ['P7', 37.55045, -77.43696], ['P8', 37.55003, -77.43536],
  ['P9', 37.54936, -77.43396], ['P10', 37.54854, -77.43258], ['P11', 37.54702, -77.43034], ['P12', 37.54612, -77.42921],
]
let controls: { sheet: string; name: string; p: Vec2; residual: number }[] = []
const res = flag('--residuals')
if (res !== undefined) {
  const rows = (await readFile(res, 'utf8')).trim().split('\n').slice(1)
  controls = rows.map((r) => r.match(/("[^"]*"|[^,]*)(,|$)/g)!.map((c) => c.replace(/,$/, '').replace(/^"|"$/g, ''))).map((c) => ({ sheet: c[0], name: c[1], p: v([+c[2], +c[3]]), residual: +c[6] }))
}

const data = {
  note: 'Written by tools/stories/jackson-ward/data.ts. View meters of region jackson-ward; elevations in meters (NAVD 88).',
  bearing: view.bearing, center: region.center, frame: f,
  grid: { nx: today.nx, ny: today.ny, x0: today.x0, y0: today.y0, cell },
  today: round(today.elev), rebuilt: round(rebuilt.elev), membrane: round(membrane.elev),
  ground: history.ground.map((r) => ({ id: r.id, method: r.method ?? 'restore', rings: r.rings.map((ring) => ring.map(v)), lines: (r.lines ?? []).map((l) => ({ name: l.name, pts: l.line.map(v) })) })),
  streets, buildings, footprint, traced: tracedOut,
  checks: checks.map(([id, lat, lon]) => ({ id, p: v([lon, lat]) })),
  controls,
  // lon/lat of the frame's corners and center, so a chart can say where it is.
  corners: [[f.minX, f.minY], [f.maxX, f.minY], [f.maxX, f.maxY], [f.minX, f.maxY]].map((p) => view.fromView(p as unknown as Vec2)),
}
await mkdir(dirname(out), { recursive: true })
await writeFile(out, JSON.stringify(data))
console.log(`${out}: grid ${today.nx}x${today.ny}, ${streets.length} streets, ${buildings.length} buildings, ${tracedOut.length} traced, ${controls.length} control points`)
