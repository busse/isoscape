import { execFile } from 'node:child_process'
import { mkdir, readFile, writeFile, readdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { parseArgs, promisify } from 'node:util'
import { archiveBuild, listBuilds } from './archive.ts'
import { backfill } from './backfill.ts'
import { cleanDem, fetchDem, loadDem, sampler } from './dem.ts'
import { DEM_SOURCES } from './dem-sources.ts'
import { fetchFootprints, loadFootprints } from './footprints.ts'
import { coverSampler, fetchLandcover, loadLandcover } from './landcover.ts'
import { renderExplorer } from './explorer.ts'
import { fetchOsm, overpassQuery, parseOsm } from './osm.ts'
import { loadPages } from './pages.ts'
import { palette } from './palette.ts'
import { fetchBounds, loadRegion, type Region } from './region.ts'
import { renderPage, renderSvg } from './render.ts'
import { buildScene, type TimeContext } from './scene.ts'
import { loadSiteConfig, writeSocial } from './social.ts'
import { dateBuildings, fetchYearBuilt, loadHistory, parseParcels, type History } from './history.ts'
import type { PolygonFeature } from './osm.ts'

const run = promisify(execFile)

const HELP = `isoscape — isometric dot-and-line views of real places

  isoscape regions                 list region configs in regions/
  isoscape sources                 list the elevation sources, with credits and licenses, as JSON
  isoscape query <region>          print the Overpass query for a region
  isoscape fetch <region>          download OSM data and elevation to data/<region>/
  isoscape info <region>           camera, counts and height coverage, as JSON
  isoscape locate <region> <lon,lat>...
                                   where places fall in the built picture (SVG units)
  isoscape build <region>          write out/<region>.svg and .html, archive the build,
                                   and refresh the explorer at out/index.html
  isoscape series <region>         build every epoch of a dated region (see regions/*.json
                                   "time"), each as <region>-<year>
  isoscape explorer                rebuild out/index.html from the archived builds
  isoscape backfill <commit> <region>
                                   build a region with an earlier commit's code and archive it

  --osm-only / --dem-only / --extras-only
                            fetch just OSM, just elevation, or just the region's
                            other sources (footprints, land cover)
  --budget <seconds>        stop starting new OSM tiles after this long (fetch resumes)
  --palette <name>   override the region's palette (paper, night)
  --png [width]      also rasterize out/<region>.png (needs rsvg-convert)
  --note "<text>"    say what this build is trying, shown in the explorer
  --year <yyyy>      build a dated region as it stood in that year
  --streetcar-scale <n>  draw streetcar lines and cars at n times life size
                     (else the history's own streetcarScale)
  --rail-scale <n>   draw railroad track at n times its width (else the history's railScale)
  --no-archive       do not keep this build in out/builds/
  --out <dir>        output directory (default: out)
  --site-url <url>   the public address of out/, for absolute link-preview URLs
                     (else ISOSCAPE_SITE_URL, else "siteUrl" in isoscape.config.json)
`

const dataDir = (r: Region) => resolve('data', r.data ?? r.name)

const loadInputs = async (name: string) => {
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
  const extra: Parameters<typeof buildScene>[4] = {}
  if (region.sources?.buildings?.includes('microsoft')) {
    const fp = await loadFootprints(resolve(dataDir(region), 'footprints.json'))
    if (fp === null) console.error(`no footprints for "${name}"; run: isoscape fetch ${region.data ?? name} --extras-only`)
    else extra.footprints = fp
  }
  if (region.sources?.landcover === 'nlcd') {
    const lc = await loadLandcover(resolve(dataDir(region), 'landcover.bin.gz'))
    if (lc === null) console.error(`no land cover for "${name}"; run: isoscape fetch ${region.data ?? name} --extras-only`)
    else extra.cover = coverSampler(lc)
  }
  let history: History | null = null
  let dates: TimeContext['dates'] = new Map()
  if (region.time !== undefined) {
    history = await loadHistory(resolve(region.time.history))
    let parcels: ReturnType<typeof parseParcels> = []
    if (region.time.yearBuilt !== undefined) {
      try {
        parcels = parseParcels(await readFile(resolve(dataDir(region), 'yearbuilt.json'), 'utf8'), region.time.yearBuilt.field)
      } catch {
        console.error(`no year-built data for "${name}"; run: isoscape fetch ${name} --extras-only`)
      }
    }
    dates = dateBuildings(features.filter((f): f is PolygonFeature => f.type === 'polygon'), parcels, history.dates)
  }
  return { region, features, elevation, extra, history, dates }
}

type Inputs = Awaited<ReturnType<typeof loadInputs>>

/** `--streetcar-scale`: draw a series' streetcar lines and cars at this scale instead of its own. */
let streetcarScale: number | undefined
/** `--rail-scale`: likewise for railroad track. */
let railScale: number | undefined

const sceneOf = (inp: Inputs, paletteName?: string, year?: number, previous?: number) => {
  const extra = { ...inp.extra }
  if (inp.history !== null) {
    const y = year ?? inp.history.present
    const epoch = inp.history.epochs.find((e) => e.year === y)
    extra.time = {
      year: y, history: { ...inp.history, ...(streetcarScale === undefined ? {} : { streetcarScale }), ...(railScale === undefined ? {} : { railScale }) }, dates: inp.dates,
      ...(previous === undefined ? {} : { previous }),
      ...(epoch === undefined ? {} : { title: epoch.title }),
    }
  } else if (year !== undefined) throw new Error(`"${inp.region.name}" has no "time" section; --year needs one`)
  return buildScene(inp.region, inp.features, palette(paletteName ?? inp.region.palette), inp.elevation, extra)
}

const loadScene = async (name: string, paletteName?: string, year?: number) => sceneOf(await loadInputs(name), paletteName, year)

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
      'extras-only': { type: 'boolean' },
      note: { type: 'string' },
      budget: { type: 'string' },
      'no-archive': { type: 'boolean' },
      year: { type: 'string' },
      'streetcar-scale': { type: 'string' },
      'rail-scale': { type: 'string' },
      'site-url': { type: 'string' },
    },
  })
  if (values['streetcar-scale'] !== undefined) streetcarScale = Number(values['streetcar-scale'])
  if (values['rail-scale'] !== undefined) railScale = Number(values['rail-scale'])
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
  if (command === 'sources') {
    // The elevation sources, with their credits and licenses, as JSON (the print and shop tools read it).
    console.log(JSON.stringify(Object.values(DEM_SOURCES).map(({ id, name, coverage, about, credit, license, link, native }) => ({ id, name, coverage, about, credit, license, link, native })), null, 1))
    return
  }
  if (command === 'explorer') {
    const outDir = resolve(values.out ?? 'out')
    const n = await writeExplorer(outDir, values['site-url'], true)
    console.error(`wrote ${resolve(outDir, 'index.html')} (${n} builds)`)
    return
  }
  if (command === 'backfill') {
    const [, commit, region] = positionals
    if (commit === undefined || region === undefined) throw new Error('usage: isoscape backfill <commit> <region> [--palette p] [--note text]')
    const outDir = resolve(values.out ?? 'out')
    const meta = await backfill(commit, region, outDir, values.palette, values.note)
    const n = await writeExplorer(outDir, values['site-url'])
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
      const only = values['osm-only'] || values['dem-only'] || values['extras-only']
      if (!only || values['extras-only']) {
        if (region.sources?.buildings?.includes('microsoft')) await fetchFootprints(region, dataDir(region))
        if (region.sources?.landcover === 'nlcd') await fetchLandcover(region, dataDir(region))
        if (region.time?.yearBuilt !== undefined) await fetchYearBuilt(region, region.time.yearBuilt, resolve('data', region.name))
        if (values['extras-only']) return
      }
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
      const scene = await loadScene(name, values.palette, values.year === undefined ? undefined : Number(values.year))
      console.log(JSON.stringify({ region: scene.region.name, bearing: Number(scene.view.bearing.toFixed(2)), ...scene.stats }, null, 2))
      return
    }
    case 'locate': {
      // Where places fall in the built picture: lon,lat pairs → SVG coordinates on the ground.
      const scene = await loadScene(name, values.palette, values.year === undefined ? undefined : Number(values.year))
      const out = positionals.slice(2).map((arg) => {
        const [lon, lat] = arg.split(',').map(Number)
        const p = scene.view.toView(lon, lat)
        const [x, y] = scene.view.toScreen(p, scene.terrain.z(p))
        return { lon, lat, x: Number(x.toFixed(1)), y: Number(y.toFixed(1)) }
      })
      console.log(JSON.stringify(out, null, 1))
      return
    }
    case 'build': {
      const inp = await loadInputs(name)
      await buildOne(inp, name, values, values.year === undefined ? undefined : Number(values.year))
      return
    }
    case 'series': {
      const inp = await loadInputs(name)
      if (inp.history === null || inp.history.epochs.length === 0) throw new Error(`"${name}" has no epochs; add a "time" section with a history file`)
      const epochs = [...inp.history.epochs].sort((a, b) => a.year - b.year)
      for (let k = 0; k < epochs.length; k++) await buildOne(inp, name, values, epochs[k].year, k > 0 ? epochs[k - 1].year : undefined)
      return
    }
    default:
      throw new Error(`unknown command "${command}"\n\n${HELP}`)
  }
}

/**
 * Rewrite out/index.html, and the link-preview share pages in out/s/, rendering any missing
 * social images first (see social.ts). `verbose` reports on previews (the explorer command).
 */
const writeExplorer = async (outDir: string, siteUrl?: string, verbose = false): Promise<number> => {
  const builds = await listBuilds(outDir)
  const config = await loadSiteConfig(siteUrl)
  const pages = loadPages(undefined, config.siteUrl)
  await mkdir(outDir, { recursive: true })
  const site = await writeSocial(outDir, builds, pages, config, verbose ? (line) => console.error(line) : undefined)
  await writeFile(resolve(outDir, 'index.html'), renderExplorer(builds, pages, { ...site, ...(config.shop ? { shop: config.shop } : {}), ...(config.home ? { home: config.home } : {}), ...(config.latestPages === false ? { latestPages: false } : {}) }))
  if (verbose) {
    if (site.rendered > 0) console.error(`rendered ${site.rendered} social preview image${site.rendered === 1 ? '' : 's'}`)
    if (site.missing > 0) console.error(`${site.missing} build${site.missing === 1 ? ' has' : 's have'} no social image (no rsvg-convert or Chrome found); their previews use the thumbnail`)
    console.error(`wrote ${builds.length + pages.length} share pages in ${resolve(outDir, 's')}/`)
    if (config.siteUrl === undefined) console.error('link previews use relative URLs: set "siteUrl" in isoscape.config.json (or ISOSCAPE_SITE_URL, or --site-url) to the public address of out/ before publishing')
  }
  return builds.length
}

type Values = { palette?: string; png?: boolean; width?: string; out?: string; note?: string; 'no-archive'?: boolean; 'site-url'?: string }

const buildOne = async (inp: Inputs, name: string, values: Values, year?: number, previous?: number): Promise<void> => {
  const t0 = performance.now()
  const scene = sceneOf(inp, values.palette, year, previous)
  const rendered = renderSvg(scene)
  const outDir = resolve(values.out ?? 'out')
  await mkdir(outDir, { recursive: true })
  const dated = scene.time === undefined || year === undefined ? '' : `-${scene.time.year}`
  const suffix = `${dated}${values.palette !== undefined ? `-${values.palette}` : ''}`
  const base = resolve(outDir, `${name}${suffix}`)
  await writeFile(`${base}.svg`, rendered.svg)
  await writeFile(`${base}.html`, renderPage(scene, rendered))
  const mb = (rendered.svg.length / 1e6).toFixed(2)
  const relief = scene.terrain.flat ? 'flat' : `terrain ${scene.stats.elevationDatum}–${scene.stats.elevationTop} m ×${scene.terrain.exaggeration}, ${rendered.stats.rapidCells} rapid cells`
  console.error(`${name}${dated}: bearing ${scene.view.bearing.toFixed(1)}°, ${scene.stats.buildings} buildings, ${scene.stats.bridgePieces} bridge spans, ${relief}, ${mb} MB svg, ${Math.round(performance.now() - t0)} ms`)
  if (values.png) {
    const width = values.width ?? String(Math.round(Math.min(6000, rendered.viewBox[2])))
    await run('rsvg-convert', ['-w', width, '-o', `${base}.png`, `${base}.svg`], { maxBuffer: 1 << 26 })
    console.error(`wrote ${base}.png`)
  }
  console.error(`wrote ${base}.svg and ${base}.html`)
  if (values['no-archive']) return
  const paletteName = values.palette ?? scene.region.palette ?? 'paper'
  const epoch = inp.history?.epochs.find((e) => e.year === scene.time?.year)
  const meta = await archiveBuild(outDir, rendered.svg, {
    name: `${name}${suffix}`,
    region: name,
    title: scene.time === undefined ? scene.region.title : `${scene.region.title}, ${scene.time.year}`,
    palette: paletteName,
    ...(values.note === undefined ? {} : { note: values.note }),
    viewBox: rendered.viewBox,
    bearing: scene.view.bearing,
    ms: Math.round(performance.now() - t0),
    stats: { ...scene.stats, ...rendered.stats },
    config: scene.region,
    sky: scene.palette.sky,
    ...(scene.time === undefined ? {} : {
      time: {
        year: scene.time.year,
        series: name,
        ...(epoch === undefined ? {} : { title: epoch.title, ...(epoch.note === undefined ? {} : { note: epoch.note }) }),
        ...(previous === undefined ? {} : { previous }),
        curated: scene.time.curated.map((h) => ({ id: h.id, name: h.name, kind: h.kind, from: h.from, ...(h.to === undefined ? {} : { to: h.to }), note: h.note, sources: h.sources })),
      },
    }),
  })
  const n = await writeExplorer(outDir, values['site-url'])
  console.error(`archived ${meta.id}; explorer has ${n} builds: ${resolve(outDir, 'index.html')}`)
}
