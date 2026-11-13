import { execFile } from 'node:child_process'
import { mkdir, readFile, writeFile, readdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { parseArgs, promisify } from 'node:util'
import { fetchDem, loadDem, sampler } from './dem.ts'
import { fetchOsm, overpassQuery, parseOsm } from './osm.ts'
import { palette } from './palette.ts'
import { fetchBounds, loadRegion, type Region } from './region.ts'
import { renderPage, renderSvg } from './render.ts'
import { buildScene } from './scene.ts'

const run = promisify(execFile)

const HELP = `isoscape — isometric dot-and-line views of real places

  isoscape regions                 list region configs in regions/
  isoscape query <region>          print the Overpass query for a region
  isoscape fetch <region>          download OSM data and elevation to data/<region>/
  isoscape info <region>           camera, counts and height coverage, as JSON
  isoscape build <region>          write out/<region>.svg and out/<region>.html

  --osm-only / --dem-only   fetch just one of the two
  --palette <name>   override the region's palette (paper, night)
  --png [width]      also rasterise out/<region>.png (needs rsvg-convert)
  --out <dir>        output directory (default: out)
`

const dataDir = (r: Region) => resolve('data', r.data ?? r.name)

const loadScene = async (name: string, paletteName?: string) => {
  const region = await loadRegion(name)
  let json: string
  try {
    json = await readFile(resolve(dataDir(region), 'osm.json'), 'utf8')
  } catch {
    throw new Error(`no data for "${region.data ?? name}"; run: isoscape fetch ${region.data ?? name}`)
  }
  const features = parseOsm(json)
  let elevation = null
  if (region.terrain !== undefined && region.terrain.enabled !== false) {
    const dem = await loadDem(resolve(dataDir(region), 'dem.bin.gz'))
    if (dem === null) console.error(`no elevation for "${name}"; drawing it flat. Run: isoscape fetch ${region.data ?? name} --dem-only`)
    else elevation = sampler(dem)
  }
  return buildScene(region, features, palette(paletteName ?? region.palette), elevation)
}

export const main = async (argv: string[]): Promise<void> => {
  const { positionals, values } = parseArgs({
    args: argv,
    allowPositionals: true,
    options: {
      palette: { type: 'string' },
      png: { type: 'boolean' },
      width: { type: 'string' },
      out: { type: 'string' },
      help: { type: 'boolean', short: 'h' },
      'osm-only': { type: 'boolean' },
      'dem-only': { type: 'boolean' },
    },
  })
  const [command, name] = positionals
  if (command === undefined || values.help) {
    console.log(HELP)
    return
  }
  if (command === 'regions') {
    const files = (await readdir('regions')).filter((f) => f.endsWith('.json'))
    for (const f of files) {
      const r = await loadRegion(f.replace(/\.json$/, ''))
      console.log(`${r.name.padEnd(28)} ${r.title}`)
    }
    return
  }
  if (name === undefined) throw new Error(`usage: isoscape ${command} <region>`)

  switch (command) {
    case 'query': {
      console.log(overpassQuery(await loadRegion(name)))
      return
    }
    case 'fetch': {
      const region = await loadRegion(name)
      const b = fetchBounds(region)
      console.error(`fetching ${b.south.toFixed(4)},${b.west.toFixed(4)} → ${b.north.toFixed(4)},${b.east.toFixed(4)}`)
      if (!values['dem-only']) await fetchOsm(region, resolve(dataDir(region), 'osm.json'))
      if (!values['osm-only']) await fetchDem(region, resolve(dataDir(region), 'dem.bin.gz'))
      return
    }
    case 'info': {
      const scene = await loadScene(name, values.palette)
      console.log(JSON.stringify({ region: scene.region.name, bearing: Number(scene.view.bearing.toFixed(2)), ...scene.stats }, null, 2))
      return
    }
    case 'build': {
      const t0 = performance.now()
      const scene = await loadScene(name, values.palette)
      const rendered = renderSvg(scene)
      const outDir = resolve(values.out ?? 'out')
      await mkdir(outDir, { recursive: true })
      const suffix = values.palette !== undefined ? `-${values.palette}` : ''
      const base = resolve(outDir, `${name}${suffix}`)
      await writeFile(`${base}.svg`, rendered.svg)
      await writeFile(`${base}.html`, renderPage(scene, rendered))
      const mb = (rendered.svg.length / 1e6).toFixed(2)
      const relief = scene.terrain.flat ? 'flat' : `terrain ${scene.stats.elevationDatum}–${scene.stats.elevationTop} m ×${scene.terrain.exaggeration}, ${rendered.stats.rapidCells} rapid cells`
      console.error(`${name}: bearing ${scene.view.bearing.toFixed(1)}°, ${scene.stats.buildings} buildings, ${scene.stats.bridgePieces} bridge spans, ${relief}, ${mb} MB svg, ${Math.round(performance.now() - t0)} ms`)
      if (values.png) {
        const width = values.width ?? String(Math.round(Math.min(6000, rendered.viewBox[2])))
        await run('rsvg-convert', ['-w', width, '-o', `${base}.png`, `${base}.svg`], { maxBuffer: 1 << 26 })
        console.error(`wrote ${base}.png`)
      }
      console.error(`wrote ${base}.svg and ${base}.html`)
      return
    }
    default:
      throw new Error(`unknown command "${command}"\n\n${HELP}`)
  }
}
