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
  /** 1 where a water node is rock standing clear of the river's surface. */
  readonly rocks: Uint8Array
  /** 1 where a water node is at least two cells from any shore: where rocks and rapids are read. */
  readonly interior: Uint8Array
  /** The river's surface elevation, carried a few cells inland past the shore; NaN beyond. */
  readonly level: Float32Array
  /** Land cover class (NLCD code) at each node; 0 where unknown. */
  readonly cover: Uint8Array
  /** Scene z of the water surface at a point; the ground's own z where there is no water near. */
  readonly waterZ: (p: Vec2) => number
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
  if (sample !== null) {
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const [lon, lat] = view.fromView([x0 + i * cell, y0 + j * cell])
        elev[j * nx + i] = sample(lon, lat)
      }
    }
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
  const z = (p: Vec2) => (elevation(p) - datum) * exaggeration
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
    return w > 0 ? (s / w - datum) * exaggeration : z([e, n])
  }
  return {
    cell, nx, ny, x0, y0, elev,
    water: new Uint8Array(nx * ny),
    rocks: new Uint8Array(nx * ny),
    interior: new Uint8Array(nx * ny),
    cover: new Uint8Array(nx * ny),
    level,
    waterZ,
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
 * `value` 1 marks water; 0 clears it again for islands.
 */
export const rasterize = (t: Terrain, polygons: readonly (readonly Ring[])[], value: 0 | 1): void => {
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
        for (let i = i0; i <= i1; i++) t.water[j * t.nx + i] = value
      }
    }
  }
}

/** Unit surface normal of the drawn (exaggerated) surface over cell (i, j). */
export const cellNormal = (t: Terrain, i: number, j: number): [number, number, number] => {
  const at = (ii: number, jj: number) => (t.elev[jj * t.nx + ii] - t.datum) * t.exaggeration
  const a = at(i, j)
  const b = at(i + 1, j)
  const c = at(i, j + 1)
  const d = at(i + 1, j + 1)
  const dzdx = (b + d - a - c) / (2 * t.cell)
  const dzdy = (c + d - a - b) / (2 * t.cell)
  const len = Math.hypot(dzdx, dzdy, 1)
  return [-dzdx / len, -dzdy / len, 1 / len]
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
    if (water[k] !== 1) continue
    if (markRocks && t.interior[k] === 1 && elev[k] - surface[k] > rockHeight) t.rocks[k] = 1
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
}

/**
 * How fast the river's surface falls at a water node, measured across `span` meters so that one
 * noisy node cannot fake a rapid, with the direction it falls in (unit vector, downhill).
 */
export const riverFall = (t: Terrain, i: number, j: number, span = 20): { slope: number; down: Vec2 } | null => {
  const k = Math.max(1, Math.round(span / t.cell))
  if (i < k || j < k || i >= t.nx - k || j >= t.ny - k) return null
  if (t.interior[j * t.nx + i] !== 1) return null
  let gx = 0
  let gy = 0
  let best = 0
  for (const [di, dj] of [[1, 0], [0, 1], [1, 1], [1, -1]] as const) {
    const a = (j + dj * k) * t.nx + (i + di * k)
    const b = (j - dj * k) * t.nx + (i - di * k)
    if (t.interior[a] !== 1 || t.interior[b] !== 1) continue
    const run = 2 * k * t.cell * Math.hypot(di, dj)
    const g = (t.elev[a] - t.elev[b]) / run
    if (Math.abs(g) > best) best = Math.abs(g)
    gx += (g * di) / Math.hypot(di, dj)
    gy += (g * dj) / Math.hypot(di, dj)
  }
  const len = Math.hypot(gx, gy)
  if (best === 0 || len === 0) return null
  return { slope: best, down: [-gx / len, -gy / len] }
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
    t.elev[k] = low
    t.level[k] = low
  }
}
