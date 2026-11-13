/**
 * Build a region with the code from an earlier commit and add it to the archive, so the
 * explorer can compare today's output with what the pipeline drew before.
 *
 * The commit's tree is exported (`git archive`) to a temporary directory, given this
 * checkout's cached data, and run with its own CLI. Its numbers come from its own `info`
 * command; older commits that predate some stats simply report fewer.
 */

import { execFile } from 'node:child_process'
import { cp, mkdtemp, readFile, rm, symlink } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { promisify } from 'node:util'
import { archiveBuild, type BuildMeta } from './archive.ts'
import { loadRegion } from './region.ts'
import { palette as paletteOf } from './palette.ts'

const run = promisify(execFile)

export const backfill = async (commit: string, name: string, outDir: string, paletteName?: string, note?: string): Promise<BuildMeta> => {
  const full = (await run('git', ['rev-parse', '--short', commit])).stdout.trim()
  const subject = (await run('git', ['log', '-1', '--format=%s', full])).stdout.trim()
  const when = (await run('git', ['log', '-1', '--format=%cI', full])).stdout.trim()
  const dir = await mkdtemp(join(tmpdir(), `isoscape-${full}-`))
  try {
    await run('sh', ['-c', `git archive ${full} | tar -x -C "${dir}"`])
    // The old tree gets this checkout's data, so it builds offline exactly as it would have.
    await rm(join(dir, 'data'), { recursive: true, force: true })
    await symlink(resolve('data'), join(dir, 'data'))
    // A region config that is newer than the commit is copied in.
    await cp(resolve('regions', `${name}.json`), join(dir, 'regions', `${name}.json`))
    const args = ['bin/isoscape.js', 'build', name, '--out', 'out-old', ...(paletteName ? ['--palette', paletteName] : [])]
    const t0 = performance.now()
    try {
      await run('node', [...args, '--no-archive'], { cwd: dir, maxBuffer: 1 << 26 })
    } catch {
      // Commits from before the archive existed do not know the flag.
      await run('node', args, { cwd: dir, maxBuffer: 1 << 26 })
    }
    const ms = Math.round(performance.now() - t0)
    const suffix = paletteName ? `-${paletteName}` : ''
    const svg = await readFile(join(dir, 'out-old', `${name}${suffix}.svg`), 'utf8')
    let stats: Record<string, number> = {}
    let bearing = 0
    try {
      const info = JSON.parse((await run('node', ['bin/isoscape.js', 'info', name], { cwd: dir })).stdout) as Record<string, number>
      bearing = info.bearing ?? 0
      stats = Object.fromEntries(Object.entries(info).filter(([k, v]) => typeof v === 'number' && k !== 'bearing'))
    } catch {
      // no info command at that commit
    }
    const vb = (svg.match(/viewBox="([^"]+)"/)?.[1] ?? '0 0 100 100').split(/\s+/).map(Number) as [number, number, number, number]
    const region = await loadRegion(name)
    const pal = paletteName ?? region.palette ?? 'paper'
    return await archiveBuild(
      outDir,
      svg,
      {
        name: `${name}${suffix}`,
        region: name,
        title: region.title,
        palette: pal,
        note: note ?? `As of ${full}: ${subject}`,
        viewBox: vb,
        bearing,
        ms,
        stats,
        config: region,
        sky: paletteOf(pal).sky,
      },
      { createdAt: when, git: { commit: full, dirty: false, subject } },
    )
  } finally {
    await rm(dir, { recursive: true, force: true })
  }
}
