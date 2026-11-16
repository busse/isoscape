/**
 * Iso-bands over a grid of node values: the part of a block of cells where a field is at or
 * above a threshold, as closed rings.
 *
 * Marching squares with linear interpolation along cell sides, then the cell pieces are
 * merged: a piece's edge that lies on a side shared with another cell of the block is dropped
 * (the cell across holds the same stretch of the same side), and what is left is chained into
 * rings. So a band comes out as a few smooth-edged polygons, not one polygon per cell, and the
 * only straight edges left are the block's own boundary.
 *
 * Coordinates are fractional grid indices (i across, j along). Rings are counter-clockwise in
 * (i, j), with the band on the left; holes come out clockwise.
 */

export interface BandPoint {
  readonly i: number
  readonly j: number
  /**
   * The point lies on the block's first or last row line (j0 or j1), where the block meets
   * the block before or after it. Both blocks find the same points there.
   */
  readonly onRow: boolean
}

/**
 * The region of cells [i0, i1) × [j0, j1) where `field` ≥ `t`, as rings. `field` holds node
 * values row-major, `nx` nodes to a row.
 */
export const isoBand = (field: ArrayLike<number>, nx: number, i0: number, i1: number, j0: number, j1: number, t: number): BandPoint[][] => {
  // Vertex ids: node (i, j) is 3k, the crossing on the side from it to (i+1, j) is 3k+1, the
  // crossing on the side from it to (i, j+1) is 3k+2, with k = j·nx + i.
  const next = new Map<number, number>()
  const v = (i: number, j: number) => field[j * nx + i]
  for (let j = j0; j < j1; j++) {
    for (let i = i0; i < i1; i++) {
      const k = j * nx + i
      const ids = [3 * k, 3 * (k + 1), 3 * (k + nx + 1), 3 * (k + nx)]
      const inside = [v(i, j) >= t, v(i + 1, j) >= t, v(i + 1, j + 1) >= t, v(i, j + 1) >= t]
      if (!inside[0] && !inside[1] && !inside[2] && !inside[3]) continue
      // The side k runs from corner k to corner k+1: bottom, right, top, left.
      const crossings = [3 * k + 1, 3 * (k + 1) + 2, 3 * (k + nx) + 1, 3 * k + 2]
      // Interior sides are shared with a cell of the block; their stretches are dropped.
      const interior = [j > j0, i + 1 < i1, j + 1 < j1, i > i0]
      const verts: number[] = []
      const sides: number[] = [] // for crossings, the side; for corners, the corner index + 4
      for (let c = 0; c < 4; c++) {
        if (inside[c]) { verts.push(ids[c]); sides.push(4 + c) }
        if (inside[c] !== inside[(c + 1) % 4]) { verts.push(crossings[c]); sides.push(c) }
      }
      const onSide = (s: number, side: number) => (s < 4 ? s === side : s - 4 === side || (s - 4 + 3) % 4 === side)
      for (let a = 0; a < verts.length; a++) {
        const b = (a + 1) % verts.length
        let shared = -1
        for (let side = 0; side < 4; side++) if (onSide(sides[a], side) && onSide(sides[b], side)) shared = side
        if (shared >= 0 && interior[shared]) continue
        next.set(verts[a], verts[b])
      }
    }
  }
  const at = (id: number): BandPoint => {
    const k = Math.floor(id / 3)
    const i = k % nx
    const j = Math.floor(k / nx)
    const kind = id % 3
    if (kind === 0) return { i, j, onRow: j === j0 || j === j1 }
    const fa = field[k]
    const fb = kind === 1 ? field[k + 1] : field[k + nx]
    const u = fb === fa ? 0.5 : (t - fa) / (fb - fa)
    return kind === 1 ? { i: i + u, j, onRow: j === j0 || j === j1 } : { i, j: j + u, onRow: false }
  }
  const rings: BandPoint[][] = []
  for (const start of [...next.keys()]) {
    if (!next.has(start)) continue
    const ring: BandPoint[] = []
    let id = start
    while (next.has(id)) {
      const to = next.get(id) as number
      next.delete(id)
      ring.push(at(id))
      id = to
    }
    if (ring.length >= 3) rings.push(ring)
  }
  return rings
}
