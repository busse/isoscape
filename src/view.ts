/**
 * The camera. Turns lon/lat into view meters (E' across, N' into the frame) and view meters
 * plus a height into screen pixels.
 *
 * The camera is orthographic, tilted down from the horizon and looking along +N'. Ground
 * distance across the frame is drawn at full `scale`; ground distance into the frame is
 * foreshortened by `squash` (the sine of the tilt); height is drawn at the cosine of the tilt,
 * times any exaggeration. With squash 0.5 that is a 30° tilt — the classic 2:1 game view once
 * the street grid sits on the diagonals, which is what `snap` arranges.
 */

import type { Rect, Vec2 } from './geom.ts'
import { localMetres, lonLatFromLocal, type Region } from './region.ts'

export interface View {
  /** The bearing actually used, after any snap. */
  readonly bearing: number
  /** lon/lat → view meters. */
  readonly toView: (lon: number, lat: number) => Vec2
  /** view meters → lon/lat. */
  readonly fromView: (p: Vec2) => Vec2
  /** view meters + height → screen px. */
  readonly toScreen: (p: Vec2, z?: number) => Vec2
  /** The ground rectangle the frame shows, in view meters. */
  readonly frame: Rect
  readonly scale: number
  readonly squash: number
  readonly zScale: number
}

const rad = (deg: number) => (deg * Math.PI) / 180

/**
 * Dominant orientation (mod 90°, in degrees counter-clockwise from east) of a set of edges in
 * local meters, weighted by length. Angles are folded with 4θ so 0°, 90°, 180° and 270° all
 * vote for the same grid.
 */
export const dominantGridAngle = (rings: readonly (readonly Vec2[])[]): number | null => {
  let c = 0
  let s = 0
  for (const ring of rings) {
    for (let i = 0; i < ring.length; i++) {
      const a = ring[i]
      const b = ring[(i + 1) % ring.length]
      const dx = b[0] - a[0]
      const dy = b[1] - a[1]
      const len = Math.hypot(dx, dy)
      if (len < 2) continue
      const t = 4 * Math.atan2(dy, dx)
      c += len * Math.cos(t)
      s += len * Math.sin(t)
    }
  }
  if (Math.hypot(c, s) < 1e-6) return null
  return (Math.atan2(s, c) * 180) / Math.PI / 4
}

/**
 * The bearing that puts a grid at `gridAngle` onto the isometric diagonals, as close to
 * `bearing` as possible (within ±45°).
 */
export const snapBearing = (bearing: number, gridAngle: number): number => {
  // Rotating the world counter-clockwise by b turns an edge at φ to φ + b; we want φ + b ≡ 45.
  let delta = (((45 - gridAngle - bearing) % 90) + 90) % 90
  if (delta > 45) delta -= 90
  return bearing + delta
}

export const makeView = (region: Region, bearing: number): View => {
  const local = localMetres(region)
  const unlocal = lonLatFromLocal(region)
  const b = rad(bearing)
  const cos = Math.cos(b)
  const sin = Math.sin(b)
  const scale = region.scale
  const squash = region.squash ?? 0.5
  const zScale = Math.cos(Math.asin(squash)) * (region.exaggeration ?? 1)
  return {
    bearing,
    toView: (lon, lat) => {
      const [e, n] = local(lon, lat)
      // Counter-clockwise by the bearing brings the direction the camera faces to +N'.
      return [e * cos - n * sin, e * sin + n * cos]
    },
    fromView: ([x, y]) => unlocal(x * cos + y * sin, -x * sin + y * cos),
    toScreen: ([e, n], z = 0) => [e * scale, -n * scale * squash - z * scale * zScale],
    frame: { minX: -region.width / 2, maxX: region.width / 2, minY: -region.depth / 2, maxY: region.depth / 2 },
    scale,
    squash,
    zScale,
  }
}
