/**
 * Water from coastline.
 *
 * OSM draws the sea, and tidal water like the Chesapeake Bay and the mouths of its rivers, not
 * as water polygons but as `natural=coastline` ways, with the land always on their left. To get
 * water for a frame: join the ways into chains, cut the chains where they cross the frame,
 * and close each run of land by walking the frame's edge counterclockwise (keeping the land on
 * the left) to where the coast comes back in. That gives the land; the water is the frame
 * minus the land.
 */

import { clipSegmentToRect, insideRect, pointInRing, samePoint, type Rect, type Ring, type Vec2 } from './geom.ts'

/** Join directed coastline ways end to start. Coastlines never need reversing. */
export const chainCoast = (ways: readonly (readonly Vec2[])[]): Vec2[][] => {
  const key = (p: Vec2) => `${p[0].toFixed(7)},${p[1].toFixed(7)}`
  const byStart = new Map<string, number>()
  ways.forEach((w, i) => byStart.set(key(w[0]), i))
  const used = new Array<boolean>(ways.length).fill(false)
  const chains: Vec2[][] = []
  // Start from ways nothing leads into, then pick up the closed loops left over.
  const leadsIn = new Set(ways.map((w) => key(w[w.length - 1])))
  const order = [...ways.keys()].sort((a, b) => Number(leadsIn.has(key(ways[a][0]))) - Number(leadsIn.has(key(ways[b][0]))))
  for (const start of order) {
    if (used[start]) continue
    used[start] = true
    let chain = ways[start].slice()
    for (;;) {
      const next = byStart.get(key(chain[chain.length - 1]))
      if (next === undefined || used[next]) break
      used[next] = true
      chain = chain.concat(ways[next].slice(1))
    }
    chains.push(chain)
  }
  return chains
}

/** Position along the rectangle's edge, counterclockwise from the lower-left corner. */
const perimeterOf = (r: Rect) => {
  const w = r.maxX - r.minX
  const h = r.maxY - r.minY
  const total = 2 * (w + h)
  const at = ([x, y]: Vec2): number => {
    const eps = 1e-6 * (w + h)
    if (Math.abs(y - r.minY) < eps) return x - r.minX
    if (Math.abs(x - r.maxX) < eps) return w + (y - r.minY)
    if (Math.abs(y - r.maxY) < eps) return w + h + (r.maxX - x)
    return 2 * w + h + (r.maxY - y)
  }
  const corners: { s: number; p: Vec2 }[] = [
    { s: w, p: [r.maxX, r.minY] },
    { s: w + h, p: [r.maxX, r.maxY] },
    { s: 2 * w + h, p: [r.minX, r.maxY] },
    { s: total, p: [r.minX, r.minY] },
  ]
  return { total, at, corners }
}

/** Move a point inside the rectangle out to the nearest point of its edge. */
const toEdge = ([x, y]: Vec2, r: Rect): Vec2 => {
  const d = [x - r.minX, r.maxX - x, y - r.minY, r.maxY - y]
  const k = d.indexOf(Math.min(...d))
  return k === 0 ? [r.minX, y] : k === 1 ? [r.maxX, y] : k === 2 ? [x, r.minY] : [x, r.maxY]
}

interface Piece { pts: Vec2[]; sIn: number; sOut: number }

/**
 * Land polygons inside `rect`, from coastline chains already in the rectangle's coordinates.
 * Every ring returned runs counterclockwise around land.
 */
export const landFromCoast = (chains: readonly Vec2[][], rect: Rect): { land: Ring[]; allLand: boolean } => {
  const per = perimeterOf(rect)
  const land: Ring[] = []
  const pieces: Piece[] = []
  const outsideRings: Vec2[][] = []

  for (const raw of chains) {
    if (raw.length < 2) continue
    const closed = raw.length >= 4 && samePoint(raw[0], raw[raw.length - 1])
    const inside = raw.map((p) => insideRect(p, rect))
    if (closed && inside.every(Boolean)) {
      land.push(raw.slice(0, -1))
      continue
    }
    if (inside.every((v) => !v)) {
      // It may still cross the frame between vertices; test segment by segment below. If it
      // never does, a closed ring may surround the whole frame.
      let crosses = false
      for (let i = 0; i + 1 < raw.length && !crosses; i++) crosses = clipSegmentToRect(raw[i], raw[i + 1], rect) !== null
      if (!crosses) {
        if (closed) outsideRings.push(raw)
        continue
      }
    }
    // A closed ring that crosses the frame is walked from a vertex outside it.
    let pts = raw
    if (closed) {
      const k = inside.findIndex((v) => !v)
      const ring = raw.slice(0, -1)
      pts = [...ring.slice(k), ...ring.slice(0, k), ring[k]]
    }
    let cur: Vec2[] | null = null
    let sIn = 0
    if (insideRect(pts[0], rect)) {
      // An open chain that starts inside the frame: the data stops here. Carry it to the edge.
      const e = toEdge(pts[0], rect)
      cur = [e, pts[0]]
      sIn = per.at(e)
    }
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i]
      const b = pts[i + 1]
      const aIn = insideRect(a, rect)
      const bIn = insideRect(b, rect)
      if (aIn && bIn) {
        cur?.push(b)
        continue
      }
      const seg = clipSegmentToRect(a, b, rect)
      if (seg === null) continue
      if (!aIn) {
        cur = [seg[0]]
        sIn = per.at(seg[0])
      }
      if (bIn) cur?.push(b)
      else if (cur !== null) {
        cur.push(seg[1])
        pieces.push({ pts: cur, sIn, sOut: per.at(seg[1]) })
        cur = null
      }
    }
    if (cur !== null) {
      // An open chain that ends inside the frame.
      const e = toEdge(cur[cur.length - 1], rect)
      cur.push(e)
      pieces.push({ pts: cur, sIn, sOut: per.at(e) })
    }
  }

  // Close each run of land along the frame edge, counterclockwise, to the next coast coming in.
  const used = new Array<boolean>(pieces.length).fill(false)
  for (let start = 0; start < pieces.length; start++) {
    if (used[start]) continue
    const ring: Vec2[] = []
    let cur = start
    for (let guard = 0; guard <= pieces.length; guard++) {
      used[cur] = true
      ring.push(...pieces[cur].pts)
      const out = pieces[cur].sOut
      let best = -1
      let bestD = Infinity
      for (let k = 0; k < pieces.length; k++) {
        if (used[k] && k !== start) continue
        const d = (((pieces[k].sIn - out) % per.total) + per.total) % per.total
        if (d < bestD) { bestD = d; best = k }
      }
      if (best < 0) break
      for (const c of [...per.corners, ...per.corners.map((q) => ({ s: q.s + per.total, p: q.p }))]) {
        const dc = c.s - out
        if (dc > 1e-9 && dc < bestD) ring.push(c.p)
      }
      // Corners are listed in order of s, so those pushed above are already in walking order.
      if (best === start) break
      cur = best
    }
    if (ring.length >= 3) land.push(dedupeCorners(ring))
  }

  if (pieces.length === 0) {
    // No coast crosses the frame: it is all land if a ring surrounds it, or if there is no
    // coast at all; it is water with islands if all the coast lies inside it.
    const centre: Vec2 = [(rect.minX + rect.maxX) / 2, (rect.minY + rect.maxY) / 2]
    const surrounded = outsideRings.some((r) => pointInRing(centre, r))
    if (surrounded || land.length === 0) return { land: [rectRing(rect)], allLand: true }
  }
  return { land, allLand: false }
}

const rectRing = (r: Rect): Ring => [[r.minX, r.minY], [r.maxX, r.minY], [r.maxX, r.maxY], [r.minX, r.maxY]]

const dedupeCorners = (ring: Vec2[]): Ring => ring.filter((p, i) => i === 0 || !samePoint(p, ring[i - 1], 1e-9))

/**
 * Water for the frame from its coastline: the rectangle counterclockwise, with every piece of
 * land as a clockwise hole, so a nonzero (or even-odd) fill leaves the land empty.
 */
export const waterFromCoast = (chains: readonly Vec2[][], rect: Rect): Ring[] | null => {
  if (chains.length === 0) return null
  const { land, allLand } = landFromCoast(chains, rect)
  if (allLand) return null
  return [rectRing(rect), ...land.map((r) => r.slice().reverse())]
}
