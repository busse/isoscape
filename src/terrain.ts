/**
 * The ground as a height field, resampled onto a regular grid in view meters.
 *
 * Two heights live here. *Elevation* is meters above sea level, straight from the DEM: it is
 * what contours are drawn at and what slopes are measured in. *Scene z* is elevation above the
 * frame's lowest point, times the terrain exaggeration: it is what gets drawn. Buildings and
 * bridge clearances add true meters on top of scene z, so a hill can be exaggerated without
 * stretching the towers on it.
 */

import type { Ring, Vec2 } from './geom.ts'
import type { View } from './view.ts'

export interface Terrain {
  readonly cell: number
  readonly nx: number
  readonly ny: number
  readonly x0: number
  readonly y0: number
  /** Elevation in meters at grid nodes, row-major from the near edge (row 0 = frame.minY). */
  readonly elev: Float32Array
  /** 1 where a node is on open water. */
  readonly water: Uint8Array
  /** 1 where the source had no height for a node and it was filled from its neighbors. */
  readonly filled: Uint8Array
  /** 1 where a water node is rock standing clear of the river's surface. */
  readonly rocks: Uint8Array
  /** 1 where a water node is at least two cells from any shore: where rocks and rapids are read. */
  readonly interior: Uint8Array
  /**
   * 1 where a water node is a flowing river (mapped as a river, or still water a river runs
   * through), 0 on a lake, pond, basin, canal or the sea: only a river gets rocks and rapids.
   */
  readonly flowing: Uint8Array
  /** How fast the river's surface falls along its channel at each node, m/m (see `channelFall`). */
  readonly fall: Float32Array
  /** The direction the river runs at each node (unit E′, N′ pairs); 0, 0 where unknown. */
  readonly current: Float32Array
  /** The river's surface elevation, carried a few cells inland past the shore; NaN beyond. */
  readonly level: Float32Array
  /** Land cover class (NLCD code) at each node; 0 where unknown. */
  readonly cover: Uint8Array
  /** Scene z of the water surface at a point; the ground's own z where there is no water near. */
  readonly waterZ: (p: Vec2) => number
  /**
   * The shoreline field at each node: one half on the mapped shoreline, more over water, less
   * on land (see `traceShore`); 0 everywhere until the shore is traced.
   */
  readonly shore: Float32Array
  readonly datum: number
  readonly exaggeration: number
  readonly flat: boolean
  /** Scene z at a view-meter point. */
  readonly z: (p: Vec2) => number
  /** Elevation in meters at a view-meter point. */
  readonly elevation: (p: Vec2) => number
}

export const makeTerrain = (
  view: View,
  cell: number,
  exaggeration: number,
  sample: ((lon: number, lat: number) => number) | null,
): Terrain => {
  const f = view.frame
  // One cell of margin past every edge, so lookups at the frame's rim interpolate.
  const x0 = f.minX - cell
  const y0 = f.minY - cell
  const nx = Math.ceil((f.maxX - f.minX) / cell) + 3
  const ny = Math.ceil((f.maxY - f.minY) / cell) + 3
  const elev = new Float32Array(nx * ny)
  const filled = new Uint8Array(nx * ny)
  if (sample !== null) {
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const [lon, lat] = view.fromView([x0 + i * cell, y0 + j * cell])
        elev[j * nx + i] = sample(lon, lat)
      }
    }
    for (let k = 0; k < elev.length; k++) if (Number.isNaN(elev[k])) filled[k] = 1
    fillGaps(elev, nx, ny)
    // Lidar at 1 m carries curbs, rubble and noise that a 5 m grid aliases into speckle.
    // A light blur keeps the landforms and loses the grit.
    blur(elev, nx, ny, 2)
  }
  let datum = Infinity
  for (const v of elev) if (v < datum) datum = v
  if (!Number.isFinite(datum)) datum = 0

  const elevation = ([e, n]: Vec2): number => {
    const fx = Math.min(nx - 1.001, Math.max(0, (e - x0) / cell))
    const fy = Math.min(ny - 1.001, Math.max(0, (n - y0) / cell))
    const i = Math.floor(fx)
    const j = Math.floor(fy)
    const tx = fx - i
    const ty = fy - j
    const a = elev[j * nx + i]
    const b = elev[j * nx + i + 1]
    const c = elev[(j + 1) * nx + i]
    const d = elev[(j + 1) * nx + i + 1]
    return a * (1 - tx) * (1 - ty) + b * tx * (1 - ty) + c * (1 - tx) * ty + d * tx * ty
  }
  const level = new Float32Array(nx * ny).fill(NaN)
  const shore = new Float32Array(nx * ny)
  const ground = (p: Vec2) => (elevation(p) - datum) * exaggeration
  /**
   * The drawn ground meets the water at the traced shoreline: over the water side of it, the
   * ground lies on the water's surface, and on the land side it rises from that surface to its
   * own height a cell inland (see shoreRise). Without this a shoreline between two grid nodes
   * was draped partway up the bank, at a height that changed with where it crossed each cell.
   */
  const edge = SHORE_EDGE
  const z = (p: Vec2): number => {
    const fx = Math.min(nx - 1.001, Math.max(0, (p[0] - x0) / cell))
    const fy = Math.min(ny - 1.001, Math.max(0, (p[1] - y0) / cell))
    const i = Math.floor(fx)
    const j = Math.floor(fy)
    const k = j * nx + i
    const a = shore[k]
    const b = shore[k + 1]
    const c = shore[k + nx]
    const d = shore[k + nx + 1]
    // Far from any shore (the field is low at all four corners), the ground is the ground.
    if (a < edge && b < edge && c < edge && d < edge) return ground(p)
    const tx = fx - i
    const ty = fy - j
    const wet = a * (1 - tx) * (1 - ty) + b * tx * (1 - ty) + c * (1 - tx) * ty + d * tx * ty
    const surface = waterZ(p)
    if (wet >= 0.5) return surface
    return surface + (ground(p) - surface) * shoreRise(wet)
  }
  const waterZ = ([e, n]: Vec2): number => {
    const fx = Math.min(nx - 1.001, Math.max(0, (e - x0) / cell))
    const fy = Math.min(ny - 1.001, Math.max(0, (n - y0) / cell))
    const i = Math.floor(fx)
    const j = Math.floor(fy)
    const tx = fx - i
    const ty = fy - j
    let s = 0
    let w = 0
    for (const [di, dj, wt] of [[0, 0, (1 - tx) * (1 - ty)], [1, 0, tx * (1 - ty)], [0, 1, (1 - tx) * ty], [1, 1, tx * ty]] as const) {
      const v = level[(j + dj) * nx + i + di]
      if (!Number.isNaN(v) && wt > 0) { s += v * wt; w += wt }
    }
    return w > 0 ? (s / w - datum) * exaggeration : ground([e, n])
  }
  return {
    cell, nx, ny, x0, y0, elev, filled,
    water: new Uint8Array(nx * ny),
    rocks: new Uint8Array(nx * ny),
    interior: new Uint8Array(nx * ny),
    flowing: new Uint8Array(nx * ny),
    fall: new Float32Array(nx * ny),
    current: new Float32Array(2 * nx * ny),
    cover: new Uint8Array(nx * ny),
    level,
    waterZ,
    shore,
    datum,
    exaggeration,
    flat: sample === null,
    elevation,
    z,
  }
}

/** Replace missing samples by the mean of their present neighbors, repeatedly. */
const fillGaps = (a: Float32Array, nx: number, ny: number): void => {
  for (let pass = 0; pass < 256; pass++) {
    let missing = 0
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const k = j * nx + i
        if (!Number.isNaN(a[k])) continue
        let s = 0
        let n = 0
        for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const ii = i + di
          const jj = j + dj
          if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
          const v = a[jj * nx + ii]
          if (!Number.isNaN(v)) { s += v; n++ }
        }
        if (n > 0) a[k] = s / n
        else missing++
      }
    }
    if (missing === 0) return
  }
  for (let k = 0; k < a.length; k++) if (Number.isNaN(a[k])) a[k] = 0
}

/**
 * Mark grid nodes inside a set of polygons (even-odd across all their rings), by scanline.
 * `value` 1 marks water; 0 clears it again for islands. Water marked here is a flowing river
 * unless `flowing` is false (a lake, a basin, the sea): marked later, still water wins.
 */
export const rasterize = (t: Terrain, polygons: readonly (readonly Ring[])[], value: 0 | 1, flowing = true): void => {
  const flow = value === 1 && flowing ? 1 : 0
  scanPolygons(t, polygons, (k) => { t.water[k] = value; t.flowing[k] = flow })
}

/** 1 at every grid node inside the polygons (even-odd across all their rings). */
export const polygonMask = (t: Terrain, polygons: readonly (readonly Ring[])[]): Uint8Array => {
  const mask = new Uint8Array(t.nx * t.ny)
  scanPolygons(t, polygons, (k) => { mask[k] = 1 })
  return mask
}

const scanPolygons = (t: Terrain, polygons: readonly (readonly Ring[])[], mark: (k: number) => void): void => {
  for (const rings of polygons) {
    let minY = Infinity
    let maxY = -Infinity
    for (const r of rings) for (const p of r) { minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]) }
    const j0 = Math.max(0, Math.ceil((minY - t.y0) / t.cell))
    const j1 = Math.min(t.ny - 1, Math.floor((maxY - t.y0) / t.cell))
    for (let j = j0; j <= j1; j++) {
      const y = t.y0 + j * t.cell
      const xs: number[] = []
      for (const r of rings) {
        for (let k = 0, m = r.length - 1; k < r.length; m = k++) {
          const [ax, ay] = r[m]
          const [bx, by] = r[k]
          if (ay > y !== by > y) xs.push(ax + ((y - ay) / (by - ay)) * (bx - ax))
        }
      }
      xs.sort((a, b) => a - b)
      for (let k = 0; k + 1 < xs.length; k += 2) {
        const i0 = Math.max(0, Math.ceil((xs[k] - t.x0) / t.cell))
        const i1 = Math.min(t.nx - 1, Math.floor((xs[k + 1] - t.x0) / t.cell))
        for (let i = i0; i <= i1; i++) mark(j * t.nx + i)
      }
    }
  }
}

/**
 * How much more or less light each grid node takes than flat ground: light · n − light_z, for
 * the unit normal n of the drawn (exaggerated) surface. The surface is first smoothed once
 * with a 3×3 binomial kernel, and the slope at a node is the central difference across its two
 * neighbors, so the field varies smoothly from node to node and can be traced as bands.
 */
export const nodeShade = (t: Terrain, light: readonly [number, number, number]): Float32Array => {
  const { nx, ny } = t
  const z = new Float32Array(nx * ny)
  const clampI = (i: number) => Math.max(0, Math.min(nx - 1, i))
  const clampJ = (j: number) => Math.max(0, Math.min(ny - 1, j))
  const raw = (i: number, j: number) => drawnElevation(t, clampJ(j) * nx + clampI(i))
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      let sum = 0
      for (let dj = -1; dj <= 1; dj++) {
        for (let di = -1; di <= 1; di++) sum += raw(i + di, j + dj) * (di === 0 ? 2 : 1) * (dj === 0 ? 2 : 1)
      }
      z[j * nx + i] = ((sum / 16) - t.datum) * t.exaggeration
    }
  }
  const out = new Float32Array(nx * ny)
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const il = clampI(i - 1)
      const ir = clampI(i + 1)
      const jl = clampJ(j - 1)
      const jr = clampJ(j + 1)
      const dzdx = (z[j * nx + ir] - z[j * nx + il]) / ((ir - il) * t.cell)
      const dzdy = (z[jr * nx + i] - z[jl * nx + i]) / ((jr - jl) * t.cell)
      const len = Math.hypot(dzdx, dzdy, 1)
      out[j * nx + i] = (-dzdx * light[0] - dzdy * light[1] + light[2]) / len - light[2]
    }
  }
  return out
}

/** Is the whole cell (i, j) water? */
export const wetCell = (t: Terrain, i: number, j: number): boolean =>
  t.water[j * t.nx + i] === 1 && t.water[j * t.nx + i + 1] === 1 &&
  t.water[(j + 1) * t.nx + i] === 1 && t.water[(j + 1) * t.nx + i + 1] === 1

/** Is any corner of cell (i, j) water? */
export const dampCell = (t: Terrain, i: number, j: number): boolean =>
  t.water[j * t.nx + i] === 1 || t.water[j * t.nx + i + 1] === 1 ||
  t.water[(j + 1) * t.nx + i] === 1 || t.water[(j + 1) * t.nx + i + 1] === 1

/** Gradient of true elevation over a cell, meters per meter, pointing uphill. */
export const cellGradient = (t: Terrain, i: number, j: number): Vec2 => {
  const at = (ii: number, jj: number) => t.elev[jj * t.nx + ii]
  const a = at(i, j)
  const b = at(i + 1, j)
  const c = at(i, j + 1)
  const d = at(i + 1, j + 1)
  return [(b + d - a - c) / (2 * t.cell), (c + d - a - b) / (2 * t.cell)]
}

export interface ContourSegment {
  readonly a: Vec2
  readonly b: Vec2
  readonly major: boolean
  /** Grid row the segment came from, for band assignment. */
  readonly row: number
}

/**
 * Marching squares over true elevation, every `interval` meters, skipping cells that touch
 * water (a hydro-flattened river has no meaningful contours; its drops are drawn as rapids).
 */
export const contours = (t: Terrain, interval: number, majorEvery: number): ContourSegment[] => {
  const out: ContourSegment[] = []
  for (let j = 0; j + 1 < t.ny; j++) {
    for (let i = 0; i + 1 < t.nx; i++) {
      if (dampCell(t, i, j)) continue
      const v = [t.elev[j * t.nx + i], t.elev[j * t.nx + i + 1], t.elev[(j + 1) * t.nx + i + 1], t.elev[(j + 1) * t.nx + i]]
      const lo = Math.min(...v)
      const hi = Math.max(...v)
      const corners: Vec2[] = [
        [t.x0 + i * t.cell, t.y0 + j * t.cell],
        [t.x0 + (i + 1) * t.cell, t.y0 + j * t.cell],
        [t.x0 + (i + 1) * t.cell, t.y0 + (j + 1) * t.cell],
        [t.x0 + i * t.cell, t.y0 + (j + 1) * t.cell],
      ]
      for (let level = Math.ceil(lo / interval) * interval; level < hi; level += interval) {
        const pts: Vec2[] = []
        for (let k = 0; k < 4; k++) {
          const va = v[k]
          const vb = v[(k + 1) % 4]
          if ((va < level) !== (vb < level)) {
            const u = (level - va) / (vb - va)
            const pa = corners[k]
            const pb = corners[(k + 1) % 4]
            pts.push([pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u])
          }
        }
        const major = Math.abs(level / interval / majorEvery - Math.round(level / interval / majorEvery)) < 1e-6
        if (pts.length === 2) out.push({ a: pts[0], b: pts[1], major, row: j })
        else if (pts.length === 4) {
          out.push({ a: pts[0], b: pts[1], major, row: j })
          out.push({ a: pts[2], b: pts[3], major, row: j })
        }
      }
    }
  }
  return out
}

const blur = (a: Float32Array, nx: number, ny: number, passes: number, mask?: Uint8Array): void => {
  const tmp = new Float32Array(a.length)
  for (let pass = 0; pass < passes; pass++) {
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const k = j * nx + i
        if (mask !== undefined && mask[k] !== 1) { tmp[k] = a[k]; continue }
        let s = 0
        let n = 0
        for (let dj = -1; dj <= 1; dj++) {
          for (let di = -1; di <= 1; di++) {
            const ii = i + di
            const jj = j + dj
            if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
            const kk = jj * nx + ii
            if (mask !== undefined && mask[kk] !== 1) continue
            const w = di === 0 && dj === 0 ? 4 : di === 0 || dj === 0 ? 2 : 1
            s += a[kk] * w
            n += w
          }
        }
        tmp[k] = s / n
      }
    }
    a.set(tmp)
  }
}

/**
 * Find the river's surface under the noise.
 *
 * Elevation over mapped water is not the water: lidar returns from rocks, ledges and the edges
 * of banks the polygon overlaps all stand above it. The surface at a node is taken as a low
 * percentile of the water nodes within `radius` meters, then smoothed along the water. Nodes
 * standing more than `rockHeight` above that surface are rock. The water nodes' elevation is
 * replaced by the surface, so the river drapes as water — level across, falling along its
 * course, steeply only where it really drops.
 */
export const settleWater = (t: Terrain, radius = 30, rockHeight = 1.0, markRocks = true): void => {
  if (t.flat) return
  const { nx, ny, elev, water } = t
  const reach = Math.max(1, Math.round(radius / t.cell))
  const surface = new Float32Array(elev.length)
  // Water with a gap in the source near it (a bay the lidar did not cover) has a surface
  // filled in from the shore around it: no rock can be read there.
  const guessed = new Uint8Array(elev.length)
  const values: number[] = []
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const k = j * nx + i
      if (water[k] !== 1) continue
      values.length = 0
      for (let dj = -reach; dj <= reach; dj++) {
        for (let di = -reach; di <= reach; di++) {
          if (di * di + dj * dj > reach * reach) continue
          const ii = i + di
          const jj = j + dj
          if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
          const kk = jj * nx + ii
          if (t.filled[kk] === 1) guessed[k] = 1
          if (water[kk] === 1) values.push(elev[kk])
        }
      }
      values.sort((a, b) => a - b)
      surface[k] = values[Math.floor(values.length * 0.15)]
    }
  }
  blur(surface, nx, ny, 4, water)
  // Interior: water two cells from any shore. A mapped outline rarely matches the lidar to
  // the meter, so near the edge "rock" and "falls" are mostly the bank.
  const margin = 2
  const markInterior = () => {
    t.interior.fill(0)
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        if (water[j * nx + i] !== 1) continue
        let inside = true
        for (let dj = -margin; dj <= margin && inside; dj++) {
          for (let di = -margin; di <= margin; di++) {
            const ii = i + di
            const jj = j + dj
            if (ii < 0 || jj < 0 || ii >= nx || jj >= ny || water[jj * nx + ii] !== 1) { inside = false; break }
          }
        }
        if (inside) t.interior[j * nx + i] = 1
      }
    }
  }
  markInterior()
  // Near the shore, ground standing clear of the river is bank the outline overlaps: give it
  // back to the land, at its own height, so the shoreline follows the lidar.
  for (let k = 0; k < elev.length; k++) {
    if (water[k] === 1 && t.interior[k] !== 1 && elev[k] - surface[k] > rockHeight) water[k] = 0
  }
  markInterior()
  for (let k = 0; k < elev.length; k++) {
    if (water[k] !== 1 || !markRocks || t.flowing[k] !== 1 || t.interior[k] !== 1 || guessed[k] === 1) continue
    if (elev[k] - surface[k] > rockHeight) t.rocks[k] = 1
  }
  const raw = elev.slice()
  for (let k = 0; k < elev.length; k++) {
    if (water[k] !== 1) continue
    elev[k] = surface[k]
    t.level[k] = surface[k]
  }
  // Carry the surface a few cells past the shore, so water drawn to its mapped outline lies on
  // the river and does not climb a bank the outline happens to overlap.
  let frontier: number[] = []
  for (let k = 0; k < elev.length; k++) if (water[k] === 1) frontier.push(k)
  for (let step = 0; step < 4; step++) {
    const next: number[] = []
    for (const k of frontier) {
      const i = k % nx
      const j = (k - i) / nx
      for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const ii = i + di
        const jj = j + dj
        if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
        const kk = jj * nx + ii
        if (!Number.isNaN(t.level[kk])) continue
        t.level[kk] = t.level[k]
        next.push(kk)
      }
    }
    frontier = next
  }
  const up = channelFall(t)
  // Where a hydro-flattened river steps down, the water just above the step stands clear of a
  // surface read partly below it, and would read as a line of rock along the step. A rock must
  // stand clear of the water level with it and above it, too: the surface is read again, from
  // the water within `radius` that is no more than one cell further down the channel.
  if (up === null) return
  const prune: number[] = []
  for (let k = 0; k < elev.length; k++) {
    if (t.rocks[k] !== 1 || !Number.isFinite(up[k])) continue
    const i = k % nx
    const j = (k - i) / nx
    values.length = 0
    for (let dj = -reach; dj <= reach; dj++) {
      for (let di = -reach; di <= reach; di++) {
        if (di * di + dj * dj > reach * reach) continue
        const ii = i + di
        const jj = j + dj
        if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
        const kk = jj * nx + ii
        if (water[kk] === 1 && up[kk] >= up[k] - t.cell) values.push(raw[kk])
      }
    }
    values.sort((a, b) => a - b)
    if (values.length > 0 && raw[k] - values[Math.floor(values.length * 0.15)] <= rockHeight) prune.push(k)
  }
  for (const k of prune) t.rocks[k] = 0
}

/** The reach, in meters along the channel, over which `channelFall` measures the river's fall. */
export const FALL_REACH = 200

/** The default fall along the channel (m/m) above which a river reads as rapids: 4 m per km. */
export const RAPIDS = 0.004

/**
 * How fast the river's surface falls along its channel, at every flowing water node.
 *
 * A hydro-flattened river is level across and steps down along its course, and its steps are a
 * meter or less: measured across a few cells, the fall is all at the step lines and nil between
 * them. So the fall is measured along the channel, over a reach. Each flowing node's distance
 * up the channel is found first: the shortest path through the river's own water from the
 * lowest water of its stretch of river. At each node away from the shore, the surface height of
 * the river around it (within `reach` meters, and from a quarter of `reach` below it to `reach`
 * above it along the channel) is fitted against that distance; the slope of the fit is the
 * fall. It spreads a step's drop over the reach below it, where the water runs white, and
 * reads a pool above a dam as calm up to a short way above the crest. The current runs down
 * the distance. No fall is read on, or from, nodes the source had no heights for. Returns the
 * distance up the channel at each node (Infinity off the river), or null with no river.
 */
export const channelFall = (t: Terrain, reach = FALL_REACH): Float64Array | null => {
  const { nx, ny, elev, flowing, water } = t
  t.fall.fill(0)
  t.current.fill(0)
  if (t.flat) return null
  const n = nx * ny
  const wet = (k: number) => water[k] === 1 && flowing[k] === 1
  const nodes: number[] = []
  for (let k = 0; k < n; k++) if (wet(k)) nodes.push(k)
  if (nodes.length === 0) return null
  // Distance up the channel: Dijkstra over 8-connected flowing water, from the lowest water of
  // each connected stretch (every node within 5 cm of its lowest, so a level pool at the
  // bottom, such as a tidal reach, is all where the channel starts).
  nodes.sort((a, b) => elev[a] - elev[b])
  const up = new Float64Array(n).fill(Infinity)
  const heap = new MinHeap()
  const steps: [number, number, number][] = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, Math.SQRT2], [1, -1, Math.SQRT2], [-1, 1, Math.SQRT2], [-1, -1, Math.SQRT2]]
  const reached = new Uint8Array(n)
  for (const seed of nodes) {
    if (reached[seed] === 1) continue
    // The stretch of river this node lies in, and the water at its lowest level.
    const stretch: number[] = [seed]
    reached[seed] = 1
    for (let q = 0; q < stretch.length; q++) {
      const i = stretch[q] % nx
      const j = (stretch[q] - i) / nx
      for (const [di, dj] of steps) {
        const ii = i + di
        const jj = j + dj
        if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
        const kk = jj * nx + ii
        if (reached[kk] === 1 || !wet(kk)) continue
        reached[kk] = 1
        stretch.push(kk)
      }
    }
    // The channel starts where the water rises out of that lowest pool; the pool itself lies
    // below the start, at minus its distance from there, so the distance runs on through it.
    const pool = (k: number) => elev[k] <= elev[seed] + 0.05
    for (const k of stretch) {
      if (!pool(k)) continue
      const i = k % nx
      const j = (k - i) / nx
      let edge = false
      for (const [di, dj] of steps) {
        const ii = i + di
        const jj = j + dj
        const kk = jj * nx + ii
        if (ii >= 0 && jj >= 0 && ii < nx && jj < ny && wet(kk) && !pool(kk)) { edge = true; break }
      }
      if (edge) { up[k] = 0; heap.push(k, 0) }
    }
    // A pool the water never rises out of (a level river, all of it in frame) starts anywhere.
    if (heap.size === 0) { up[seed] = 0; heap.push(seed, 0) }
    while (heap.size > 0) {
      const [k, d] = heap.pop()
      if (d > up[k]) continue
      const i = k % nx
      const j = (k - i) / nx
      for (const [di, dj, len] of steps) {
        const ii = i + di
        const jj = j + dj
        if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
        const kk = jj * nx + ii
        if (!wet(kk)) continue
        const dd = d + len * t.cell
        if (dd < up[kk]) { up[kk] = dd; heap.push(kk, dd) }
      }
    }
    for (const k of stretch) if (pool(k)) up[k] = -up[k]
  }
  // The fit, over every other node of a disc (enough to fit a plane, a quarter of the work).
  const r = Math.max(2, Math.round(reach / t.cell))
  const disc: number[] = []
  for (let dj = -r; dj <= r; dj += 2) for (let di = -r; di <= r; di += 2) if (di * di + dj * dj <= r * r) disc.push(di, dj)
  for (const k of nodes) {
    if (t.interior[k] !== 1 || t.filled[k] === 1) continue
    const i = k % nx
    const j = (k - i) / nx
    const d0 = up[k]
    let m = 0
    let sd = 0
    let sz = 0
    let sdd = 0
    let sdz = 0
    // And a plane through the same heights, for the way it runs where the distance cannot say
    // (the level pool the channel starts from).
    let sx = 0
    let sy = 0
    let sxx = 0
    let syy = 0
    let sxy = 0
    let sxz = 0
    let syz = 0
    for (let q = 0; q < disc.length; q += 2) {
      const ii = i + disc[q]
      const jj = j + disc[q + 1]
      if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
      const kk = jj * nx + ii
      if (!wet(kk) || t.filled[kk] === 1) continue
      const d = up[kk] - d0
      if (d < -reach / 4 || d > reach) continue
      m++
      sd += d
      sz += elev[kk]
      sdd += d * d
      sdz += d * elev[kk]
      const x = disc[q]
      const y = disc[q + 1]
      sx += x
      sy += y
      sxx += x * x
      syy += y * y
      sxy += x * y
      sxz += x * elev[kk]
      syz += y * elev[kk]
    }
    if (m < 12) continue
    const vd = sdd / m - (sd / m) ** 2
    // A window too short along the channel (a pocket of water) cannot say how it falls.
    if (vd < (reach / 8) ** 2) continue
    t.fall[k] = Math.max(0, (sdz / m - (sd / m) * (sz / m)) / vd)
    // Down the channel: against the distance's gradient.
    const at = (ii: number, jj: number) => {
      const kk = jj * nx + ii
      return ii >= 0 && jj >= 0 && ii < nx && jj < ny && wet(kk) ? up[kk] : d0
    }
    const gx = at(i + 1, j) - at(i - 1, j)
    const gy = at(i, j + 1) - at(i, j - 1)
    const len = Math.hypot(gx, gy)
    if (len > 0) { t.current[2 * k] = -gx / len; t.current[2 * k + 1] = -gy / len; continue }
    const cxx = sxx / m - (sx / m) ** 2
    const cyy = syy / m - (sy / m) ** 2
    const cxy = sxy / m - (sx / m) * (sy / m)
    const cxz = sxz / m - (sx / m) * (sz / m)
    const cyz = syz / m - (sy / m) * (sz / m)
    const det = cxx * cyy - cxy * cxy
    if (det <= 0) continue
    const bx = (cxz * cyy - cyz * cxy) / det
    const by = (cyz * cxx - cxz * cxy) / det
    const blen = Math.hypot(bx, by)
    if (blen > 0) { t.current[2 * k] = -bx / blen; t.current[2 * k + 1] = -by / blen }
  }
  return up
}

/** A binary min-heap of node indices keyed by distance. */
class MinHeap {
  private keys: number[] = []
  private vals: number[] = []
  get size(): number { return this.keys.length }
  push(k: number, v: number): void {
    const { keys, vals } = this
    let c = keys.length
    keys.push(k)
    vals.push(v)
    while (c > 0) {
      const p = (c - 1) >> 1
      if (vals[p] <= v) break
      keys[c] = keys[p]
      vals[c] = vals[p]
      c = p
    }
    keys[c] = k
    vals[c] = v
  }
  pop(): [number, number] {
    const { keys, vals } = this
    const top: [number, number] = [keys[0], vals[0]]
    const k = keys.pop() as number
    const v = vals.pop() as number
    if (keys.length > 0) {
      let c = 0
      for (;;) {
        const l = 2 * c + 1
        if (l >= keys.length) break
        const rr = l + 1
        const s = rr < keys.length && vals[rr] < vals[l] ? rr : l
        if (vals[s] >= v) break
        keys[c] = keys[s]
        vals[c] = vals[s]
        c = s
      }
      keys[c] = k
      vals[c] = v
    }
    return top
  }
}

/**
 * How fast the river falls at a water node (`channelFall`), with the direction it runs (unit
 * vector, downstream); null where no fall is read: off the river, near the shore, on a gap in
 * the source, or where it does not fall at all.
 */
export const riverFall = (t: Terrain, i: number, j: number): { slope: number; down: Vec2 } | null => {
  if (i < 0 || j < 0 || i >= t.nx || j >= t.ny) return null
  const k = j * t.nx + i
  if (t.water[k] !== 1 || t.flowing[k] !== 1 || t.interior[k] !== 1 || t.filled[k] === 1) return null
  const slope = t.fall[k]
  const down: Vec2 = [t.current[2 * k], t.current[2 * k + 1]]
  if (!(slope > 0) || (down[0] === 0 && down[1] === 0)) return null
  return { slope, down }
}

/**
 * Still water drawn where the ground is now dry (a filled canal basin): its cells become water
 * at one level, the lowest ground under it, with no rocks and no rapids read in it.
 */
export const stillWater = (t: Terrain, rings: Vec2[][][]): void => {
  if (rings.length === 0) return
  const before = t.water.slice()
  t.water.fill(0)
  rasterize(t, rings, 1)
  const mask = t.water.slice()
  t.water.set(before)
  let low = Infinity
  for (let k = 0; k < mask.length; k++) if (mask[k] === 1) low = Math.min(low, t.elev[k])
  if (!Number.isFinite(low)) return
  for (let k = 0; k < mask.length; k++) {
    if (mask[k] !== 1) continue
    t.water[k] = 1
    t.rocks[k] = 0
    t.interior[k] = 0
    t.flowing[k] = 0
    t.fall[k] = 0
    t.elev[k] = low
    t.level[k] = low
  }
}

/**
 * Mapped water the lidar gave back to the land (see settleWater) is still drawn as water, up
 * to the outline, if it stands no more than this many meters above the river and lies within
 * SHORE_CELLS cells of the outline: the two often disagree by a few meters, and the outline is
 * the smoother line. Higher (a bluff the outline overlaps, a creek in its ravine) or further
 * out (a bar or a rock in midstream), it stays land.
 */
const SHORE_BANK = 1.5
/** The shoreline field reaches this many cells either side of the line (see `shoreField`). */
const SHORE_CELLS = 2
/** In the field, 1 is this many cells: field = 0.5 ± distance / (SHORE_REACH · cell). */
const SHORE_REACH = 2 * SHORE_CELLS
/**
 * The drawn ground rises from the water's surface at the shoreline to its own height one cell
 * inland, in proportion to the distance: as a fraction of that rise, at a field value `wet`.
 */
export const shoreRise = (wet: number): number => Math.max(0, Math.min(1, (0.5 - wet) * SHORE_REACH))
/** At or below this field value (a cell or more inland) the drawn ground is the ground. */
const SHORE_EDGE = 0.5 - 1 / SHORE_REACH

/** Elevation of the drawn ground at node k: eased to the water's surface near the shore. */
export const drawnElevation = (t: Terrain, k: number): number => {
  const f = t.shore[k]
  const e = t.elev[k]
  if (f <= SHORE_EDGE || Number.isNaN(t.level[k])) return e
  return t.level[k] + (e - t.level[k]) * shoreRise(f)
}

/**
 * Is a view-meter point on water as drawn: past the traced shoreline (the shore field, read
 * between its nodes, over one half)? Null before the shore is traced or on flat ground, where
 * only the mapped outlines say.
 */
export const drawnWet = (t: Terrain, p: Vec2): boolean | null => {
  if (t.flat) return null
  const fx = (p[0] - t.x0) / t.cell
  const fy = (p[1] - t.y0) / t.cell
  const i = Math.floor(fx)
  const j = Math.floor(fy)
  if (i < 0 || j < 0 || i + 1 >= t.nx || j + 1 >= t.ny) return null
  const u = fx - i
  const v = fy - j
  const at = (ii: number, jj: number) => t.shore[jj * t.nx + ii]
  const f = (at(i, j) * (1 - u) + at(i + 1, j) * u) * (1 - v) + (at(i, j + 1) * (1 - u) + at(i + 1, j + 1) * u) * v
  return f > 0.5
}

/** Trace the shoreline into `t.shore`, so the drawn ground meets the water on it. */
export const traceShore = (t: Terrain, water: readonly (readonly Ring[])[], islands: readonly (readonly Ring[])[]): void => {
  if (t.flat) return
  t.shore.set(shoreField(t, water, islands))
}

/**
 * Where the shoreline runs, as a field over the grid nodes that is one half on it.
 *
 * The water grid knows only which nodes are wet, so a shoreline traced from it alone can pass
 * only halfway between a wet node and a dry one: a shore running slantwise across the grid
 * came out as a staircase, a run of nodes long and a cell high, and on a print the bank read as
 * a saw. The mapped outline knows better. Each node's field is its signed distance to the
 * nearest edge of the mapped water and islands (wet nodes positive), over SHORE_CELLS cells
 * either way, so the one-half line traced between nodes is the outline itself, straight edges
 * exactly. Where the lidar moved the shore (see SHORE_BANK), the grid decides, and near those
 * nodes the line is traced as before, through the wet and dry nodes smoothed over 3 × 3.
 */
export const shoreField = (
  t: Terrain,
  water: readonly (readonly Ring[])[],
  islands: readonly (readonly Ring[])[],
): Float32Array => {
  const { nx, ny, cell } = t
  const reach = SHORE_CELLS * cell
  const dist = new Float32Array(nx * ny).fill(reach)
  for (const rings of [...water, ...islands]) {
    for (const r of rings) {
      for (let k = 0, m = r.length - 1; k < r.length; m = k++) {
        const [ax, ay] = r[m]
        const [bx, by] = r[k]
        const i0 = Math.max(0, Math.floor((Math.min(ax, bx) - reach - t.x0) / cell))
        const i1 = Math.min(nx - 1, Math.ceil((Math.max(ax, bx) + reach - t.x0) / cell))
        const j0 = Math.max(0, Math.floor((Math.min(ay, by) - reach - t.y0) / cell))
        const j1 = Math.min(ny - 1, Math.ceil((Math.max(ay, by) + reach - t.y0) / cell))
        const dx = bx - ax
        const dy = by - ay
        const len2 = dx * dx + dy * dy
        for (let j = j0; j <= j1; j++) {
          const y = t.y0 + j * cell
          for (let i = i0; i <= i1; i++) {
            const x = t.x0 + i * cell
            const u = len2 > 0 ? Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / len2)) : 0
            const d = Math.hypot(x - ax - dx * u, y - ay - dy * u)
            const q = j * nx + i
            if (d < dist[q]) dist[q] = d
          }
        }
      }
    }
  }
  // Which nodes the outline itself holds, before the lidar corrected it.
  const mapped = { ...t, water: new Uint8Array(nx * ny) }
  rasterize(mapped, water, 1)
  rasterize(mapped, islands, 0)
  // The outline decides which side a node is on, unless the lidar put the node on the bank
  // and it stands well clear of the water (a creek in its ravine, a bluff the outline
  // overlaps). There the grid decides, and the line is traced as it was before the outline
  // was read: where the grid's water, smoothed over 3 × 3 nodes (weights 4, 2, 1), is one half.
  const wet = new Uint8Array(nx * ny)
  const byGrid = new Uint8Array(nx * ny)
  for (let q = 0; q < wet.length; q++) {
    const outline = mapped.water[q] === t.water[q] || (dist[q] < reach && t.elev[q] - t.level[q] <= SHORE_BANK)
    wet[q] = outline ? mapped.water[q] : t.water[q]
    byGrid[q] = outline ? 0 : 1
  }
  const out = new Float32Array(nx * ny)
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const q = j * nx + i
      let near = false
      let sum = 0
      let wsum = 0
      for (let dj = -1; dj <= 1; dj++) {
        for (let di = -1; di <= 1; di++) {
          const ii = i + di
          const jj = j + dj
          if (ii < 0 || jj < 0 || ii >= nx || jj >= ny) continue
          const k = jj * nx + ii
          if (byGrid[k] === 1) near = true
          const w = di === 0 && dj === 0 ? 4 : di === 0 || dj === 0 ? 2 : 1
          sum += wet[k] * w
          wsum += w
        }
      }
      out[q] = near ? sum / wsum : 0.5 + (wet[q] === 1 ? 1 : -1) * (dist[q] / (SHORE_REACH * cell))
    }
  }
  return out
}
