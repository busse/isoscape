import { execFile } from 'node:child_process'
import { mkdir, readFile, writeFile, readdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { parseArgs, promisify } from 'node:util'
import { archiveBuild, listBuilds } from './archive.ts'
import { backfill } from './backfill.ts'
import { cleanDem, fetchDem, loadDem, sampler } from './dem.ts'
import { renderExplorer } from './explorer.ts'
import { fetchOsm, overpassQuery, parseOsm } from './osm.ts'
import { loadPages } from './pages.ts'
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
  isoscape build <region>          write out/<region>.svg and .html, archive the build,
                                   and refresh the explorer at out/index.html
  isoscape explorer                rebuild out/index.html from the archived builds
  isoscape backfill <commit> <region>
                                   build a region with an earlier commit's code and archive it

  --osm-only / --dem-only   fetch just one of the two
  --budget <seconds>        stop starting new OSM tiles after this long (fetch resumes)
  --palette <name>   override the region's palette (paper, night)
  --png [width]      also rasterise out/<region>.png (needs rsvg-convert)
  --note "<text>"    say what this build is trying, shown in the explorer
  --no-archive       do not keep this build in out/builds/
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
    else {
      const voids = cleanDem(dem)
      if (voids > 0) console.error(`elevation: ${voids} implausible samples treated as missing`)
      elevation = sampler(dem)
    }
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
      note: { type: 'string' },
      budget: { type: 'string' },
      'no-archive': { type: 'boolean' },
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
  if (command === 'explorer') {
    const outDir = resolve(values.out ?? 'out')
    const n = await writeExplorer(outDir)
    console.error(`wrote ${resolve(outDir, 'index.html')} (${n} builds)`)
    return
  }
  if (command === 'backfill') {
    const [, commit, region] = positionals
    if (commit === undefined || region === undefined) throw new Error('usage: isoscape backfill <commit> <region> [--palette p] [--note text]')
    const outDir = resolve(values.out ?? 'out')
    const meta = await backfill(commit, region, outDir, values.palette, values.note)
    const n = await writeExplorer(outDir)
    console.error(`archived ${meta.id} (${meta.git?.commit}); explorer has ${n} builds`)
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
      let osmDone = true
      if (!values['dem-only']) {
        const budget = values.budget === undefined ? undefined : Number(values.budget)
        const { done, total } = await fetchOsm(region, dataDir(region), budget === undefined ? {} : { budgetSeconds: budget })
        osmDone = done === total
      }
      if (!values['osm-only'] && osmDone) {
        const budget = values.budget === undefined ? undefined : Number(values.budget)
        await fetchDem(region, dataDir(region), budget === undefined ? {} : { budgetSeconds: budget })
      }
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
      if (!values['no-archive']) {
        const paletteName = values.palette ?? scene.region.palette ?? 'paper'
        const meta = await archiveBuild(outDir, rendered.svg, {
          name: `${name}${suffix}`,
          region: name,
          title: scene.region.title,
          palette: paletteName,
          ...(values.note === undefined ? {} : { note: values.note }),
          viewBox: rendered.viewBox,
          bearing: scene.view.bearing,
          ms: Math.round(performance.now() - t0),
          stats: { ...scene.stats, ...rendered.stats },
          config: scene.region,
          sky: scene.palette.sky,
        })
        const n = await writeExplorer(outDir)
        console.error(`archived ${meta.id}; explorer has ${n} builds: ${resolve(outDir, 'index.html')}`)
      }
      return
    }
    default:
      throw new Error(`unknown command "${command}"\n\n${HELP}`)
  }
}

const writeExplorer = async (outDir: string): Promise<number> => {
  const builds = await listBuilds(outDir)
  await mkdir(outDir, { recursive: true })
  await writeFile(resolve(outDir, 'index.html'), renderExplorer(builds, loadPages()))
  return builds.length
}
