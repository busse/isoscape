/**
 * Paint order for things that stand up.
 *
 * A single depth key per item is only right while nothing straddles anything else. A long
 * warehouse beside a small house, a bridge deck beside a tower: one key gets those wrong. So
 * order is decided pairwise, and only between items whose screen boxes overlap:
 *
 * - If their footprints are separable, the separating line decides. Seen from the camera, the
 *   footprint on the near side of any separating line is in front.
 * - If the footprints overlap (stacked building parts), the one entirely above is in front.
 * - Otherwise, the centroid depth decides.
 *
 * Those pairwise facts form a graph that a topological sort turns into one order. Cycles
 * (rare, from concave footprints that interlock) are broken by depth.
 */

import { separatingAxis, type Vec2 } from './geom.ts'
import type { Item } from './scene.ts'

interface Box { minX: number; minY: number; maxX: number; maxY: number }

const screenBox = (item: Item): Box => {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const s of item.shapes) {
    for (const [x, y] of s.pts) {
      if (x < minX) minX = x
      if (y < minY) minY = y
      if (x > maxX) maxX = x
      if (y > maxY) maxY = y
    }
  }
  return { minX, minY, maxX, maxY }
}

/** +1 when `a` paints after (in front of) `b`, −1 when before, 0 when it does not matter. */
export const compare = (a: Item, b: Item): number => {
  const axis: Vec2 | null = separatingAxis(a.hull, b.hull)
  if (axis !== null) {
    // `axis` points from b to a. The camera sits toward −N', so a is nearer when the axis
    // has a negative N' component.
    const towardsCamera = -axis[1]
    if (towardsCamera > 1e-6) return 1
    if (towardsCamera < -1e-6) return -1
    return 0
  }
  if (a.zMin >= b.zMax - 0.05) return 1
  if (b.zMin >= a.zMax - 0.05) return -1
  // Overlapping footprints at overlapping heights: a bridge over a low building, or bad data.
  if (a.kind !== b.kind) return a.kind === 'bridge' ? 1 : -1
  return a.key < b.key ? 1 : a.key > b.key ? -1 : 0
}

export const paintOrder = (items: readonly Item[], cell = 96): Item[] => {
  const n = items.length
  const boxes = items.map(screenBox)
  // Spatial hash on screen boxes, so only near neighbors are compared.
  const grid = new Map<string, number[]>()
  boxes.forEach((b, i) => {
    for (let gx = Math.floor(b.minX / cell); gx <= Math.floor(b.maxX / cell); gx++) {
      for (let gy = Math.floor(b.minY / cell); gy <= Math.floor(b.maxY / cell); gy++) {
        const k = `${gx},${gy}`
        const list = grid.get(k)
        if (list) list.push(i)
        else grid.set(k, [i])
      }
    }
  })
  const after: number[][] = Array.from({ length: n }, () => [])
  const indegree = new Array<number>(n).fill(0)
  const seen = new Set<number>()
  for (const list of grid.values()) {
    for (let x = 0; x < list.length; x++) {
      for (let y = x + 1; y < list.length; y++) {
        const i = list[x]
        const j = list[y]
        const pair = i < j ? i * n + j : j * n + i
        if (seen.has(pair)) continue
        seen.add(pair)
        const bi = boxes[i]
        const bj = boxes[j]
        if (bi.maxX <= bj.minX || bj.maxX <= bi.minX || bi.maxY <= bj.minY || bj.maxY <= bi.minY) continue
        const c = compare(items[i], items[j])
        if (c > 0) { after[j].push(i); indegree[i]++ }
        else if (c < 0) { after[i].push(j); indegree[j]++ }
      }
    }
  }

  // Kahn's algorithm, taking the farthest ready item first so ties fall back to depth.
  const farFirst = (i: number, j: number) => items[j].key - items[i].key || items[i].zMin - items[j].zMin
  const heap = new Heap<number>(farFirst)
  for (let i = 0; i < n; i++) if (indegree[i] === 0) heap.push(i)
  const done = new Array<boolean>(n).fill(false)
  const byDepth = [...items.keys()].sort(farFirst)
  let cursor = 0
  const out: Item[] = []
  while (out.length < n) {
    let i = heap.pop()
    if (i === undefined) {
      // A cycle: force the farthest unplaced item.
      while (done[byDepth[cursor]]) cursor++
      i = byDepth[cursor]
    }
    if (done[i]) continue
    done[i] = true
    out.push(items[i])
    for (const j of after[i]) {
      indegree[j]--
      if (indegree[j] === 0 && !done[j]) heap.push(j)
    }
  }
  return out
}

class Heap<T> {
  private readonly data: T[] = []
  private readonly less: (a: T, b: T) => number
  constructor(less: (a: T, b: T) => number) {
    this.less = less
  }
  push(value: T): void {
    const d = this.data
    d.push(value)
    let i = d.length - 1
    while (i > 0) {
      const p = (i - 1) >> 1
      if (this.less(d[i], d[p]) >= 0) break
      ;[d[i], d[p]] = [d[p], d[i]]
      i = p
    }
  }
  pop(): T | undefined {
    const d = this.data
    if (d.length === 0) return undefined
    const top = d[0]
    const last = d.pop()!
    if (d.length > 0) {
      d[0] = last
      let i = 0
      for (;;) {
        const l = 2 * i + 1
        const r = l + 1
        let m = i
        if (l < d.length && this.less(d[l], d[m]) < 0) m = l
        if (r < d.length && this.less(d[r], d[m]) < 0) m = r
        if (m === i) break
        ;[d[i], d[m]] = [d[m], d[i]]
        i = m
      }
    }
    return top
  }
}
