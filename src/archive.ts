/**
 * Every build is kept, so the explorer can show how a view has changed.
 *
 * A build is archived under out/builds/<id>/ as its SVG, a small PNG thumbnail and a 1200×630
 * link-preview image (social.png) when a rasteriser is available, and meta.json: what was
 * built, from which commit, with which settings, what it measured, and an optional note saying what was being tried.
 */

import { execFile } from 'node:child_process'
import { access, mkdir, readdir, readFile, writeFile } from 'node:fs/promises'
import { pathToFileURL } from 'node:url'
import { join, resolve } from 'node:path'
import { promisify } from 'node:util'
import type { Region } from './region.ts'
import { CHROMES, renderSocial } from './social.ts'

const run = promisify(execFile)

export interface BuildMeta {
  readonly id: string
  readonly name: string
  readonly region: string
  readonly title: string
  readonly palette: string
  readonly createdAt: string
  readonly note?: string
  readonly git?: { readonly commit: string; readonly dirty: boolean; readonly subject: string }
  readonly viewBox: readonly [number, number, number, number]
  readonly bearing: number
  readonly ms: number
  readonly bytes: number
  readonly stats: Readonly<Record<string, number>>
  readonly config: Region
  readonly files: { readonly svg: string; readonly thumb?: string; readonly social?: string; readonly preview?: string }
  /** The page color, for a swatch where there is no thumbnail. */
  readonly sky: string
  /** A dated build: its year, its place in the series, and the curated features drawn in it. */
  readonly time?: {
    readonly year: number
    readonly series: string
    readonly title?: string
    readonly note?: string
    readonly previous?: number
    readonly curated: readonly { readonly id: string; readonly name: string; readonly kind: string; readonly from: number; readonly to?: number; readonly note: string; readonly sources: readonly string[] }[]
  }
}

const gitInfo = async (): Promise<BuildMeta['git']> => {
  try {
    const commit = (await run('git', ['rev-parse', '--short', 'HEAD'])).stdout.trim()
    const subject = (await run('git', ['log', '-1', '--format=%s'])).stdout.trim()
    const dirty = (await run('git', ['status', '--porcelain', '--', 'src', 'regions'])).stdout.trim().length > 0
    return { commit, dirty, subject }
  } catch {
    return undefined
  }
}

/**
 * Rasterize a thumbnail with whatever is installed: rsvg-convert, else headless Chrome (which
 * draws the SVG exactly as the explorer will). ImageMagick's own SVG renderer is not tried: it
 * ignores clip paths and stylesheets and draws these blank. False when nothing worked.
 */
const thumbnail = async (svg: string, png: string, viewBox: readonly number[], width = 360): Promise<boolean> => {
  try {
    await run('rsvg-convert', ['-w', String(width), '-o', png, svg], { timeout: 60_000 })
    return true
  } catch {
    // fall through to Chrome
  }
  const height = Math.max(40, Math.round((width * viewBox[3]) / viewBox[2]))
  for (const chrome of CHROMES) {
    try {
      await run(
        chrome,
        ['--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
          `--window-size=${width},${height}`, `--screenshot=${png}`, pathToFileURL(svg).href],
        { timeout: 60_000 },
      )
      await access(png)
      return true
    } catch {
      // try the next one
    }
  }
  return false
}

const stamp = (d: Date) =>
  `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}-` +
  `${String(d.getHours()).padStart(2, '0')}${String(d.getMinutes()).padStart(2, '0')}${String(d.getSeconds()).padStart(2, '0')}`

export const archiveBuild = async (
  outDir: string,
  svg: string,
  meta: Omit<BuildMeta, 'id' | 'createdAt' | 'git' | 'files' | 'bytes'>,
  /** For a backfilled build: when its commit was made, and which commit it was. */
  override?: { createdAt: string; git: NonNullable<BuildMeta['git']> },
): Promise<BuildMeta> => {
  const now = override ? new Date(override.createdAt) : new Date()
  const id = `${stamp(now)}-${meta.name}`
  const dir = resolve(outDir, 'builds', id)
  await mkdir(dir, { recursive: true })
  await writeFile(join(dir, 'image.svg'), svg)
  const hasThumb = await thumbnail(join(dir, 'image.svg'), join(dir, 'thumb.png'), meta.viewBox)
  // The 1200×630 link-preview image (see social.ts).
  const hasSocial = await renderSocial(join(dir, 'image.svg'), join(dir, 'social.png'), meta.viewBox)
  const git = override ? override.git : await gitInfo()
  const full: BuildMeta = {
    ...meta,
    id,
    createdAt: now.toISOString(),
    bytes: svg.length,
    ...(git === undefined ? {} : { git }),
    files: { svg: `builds/${id}/image.svg`, ...(hasThumb ? { thumb: `builds/${id}/thumb.png` } : {}), ...(hasSocial ? { social: `builds/${id}/social.png` } : {}) },
  }
  await writeFile(join(dir, 'meta.json'), JSON.stringify(full, null, 2))
  return full
}

export const listBuilds = async (outDir: string): Promise<BuildMeta[]> => {
  const root = resolve(outDir, 'builds')
  let ids: string[]
  try {
    ids = await readdir(root)
  } catch {
    return []
  }
  const metas: BuildMeta[] = []
  for (const id of ids) {
    try {
      metas.push(JSON.parse(await readFile(join(root, id, 'meta.json'), 'utf8')) as BuildMeta)
    } catch {
      // not a build directory
    }
  }
  return metas.sort((a, b) => b.createdAt.localeCompare(a.createdAt))
}
