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

/**
 * +1 when `a` paints after (in front of) `b`, −1 when before, 0 when it does not matter.
 *
 * With `stacked`, two items apart on the ground, the farther one wholly above the nearer (a
 * floor's slab beyond a pier under it, a deck beyond a train), cannot cover each other at all:
 * every line of sight falls as it goes, so it passes over the nearer before it reaches the
 * farther, or under the farther after it leaves the nearer. They are left unordered, so the
 * pair cannot close a cycle with the orders that matter. Cutaways, which stack many such
 * parts, use it; other views keep the plain rule.
 */
export const compare = (a: Item, b: Item, stacked = false): number => {
  // A part standing over a roof's shell (a dormer on it, a tower's upper stages rising through
  // it) is in front of every piece of that shell, apart or not: a piece's box reaches up to the
  // ridge, so beside a tower it would otherwise stand in front of stages far above the roof.
  if (b.shell !== undefined && a.over === b.shell.id) return 1
  if (a.shell !== undefined && b.over === a.shell.id) return -1
  // Modeled parts that abut may overlap by the centimeter their corners were rounded to.
  const axis: Vec2 | null = separatingAxis(a.hull, b.hull, stacked ? STACK_TOLERANCE : 1e-6)
  if (axis !== null) {
    // `axis` points from b to a. The camera sits toward −N', so a is nearer when the axis
    // has a negative N' component.
    const towardsCamera = -axis[1]
    if (towardsCamera > 1e-6) return stacked && b.zMin >= a.zMax - 0.05 ? 0 : 1
    if (towardsCamera < -1e-6) return stacked && a.zMin >= b.zMax - 0.05 ? 0 : -1
    return 0
  }
  if (a.zMin >= b.zMax - 0.05) return 1
  if (b.zMin >= a.zMax - 0.05) return -1
  // Inside a roof shell: its sides facing the camera cover what stands under them, the others
  // are covered by it.
  if (a.shell !== undefined && b.within === a.shell.id) return a.shell.faces
  if (b.shell !== undefined && a.within === b.shell.id) return -b.shell.faces
  // A pier under a deck, its own or another's, stands behind it.
  if (a.kind === 'bridge' && b.kind === 'bridge' && a.pier !== b.pier) return a.pier === true ? -1 : 1
  // Overlapping footprints at overlapping heights: a bridge over a low building, or bad data.
  if (a.kind !== b.kind) return a.kind === 'bridge' ? 1 : -1
  if (a.span !== undefined && b.span !== undefined) {
    const s = spanOrder(a.span, b.span)
    if (s !== 0) return s
  }
  return a.key < b.key ? 1 : a.key > b.key ? -1 : 0
}

type Span = NonNullable<Item['span']>

/**
 * How far `p` lies beyond the line of span `s`, along N' (into the frame). Null unless `p` is
 * beside the span (within half a span of it along its line), or when the span runs into the
 * frame; 0 when it lies within half a meter of the span's line.
 */
const beyond = (s: Span, p: Vec2): number | null => {
  const dx = s.b[0] - s.a[0]
  const dy = s.b[1] - s.a[1]
  const len = Math.hypot(dx, dy)
  if (Math.abs(dx) < 0.3 * len) return null
  const along = ((p[0] - s.a[0]) * dx + (p[1] - s.a[1]) * dy) / (len * len)
  if (along < -0.5 || along > 1.5) return null
  const off = p[1] - (s.a[1] + dy * ((p[0] - s.a[0]) / dx))
  return Math.abs(off) < 0.5 ? 0 : off
}

/**
 * Two bridge spans that overlap side by side (the two carriageways of a viaduct, a pair of
 * tracks). Their depth keys alternate along the road, so ordering them by key interleaves two
 * decks span by span into a ladder. Instead the deck whose line is nearer the camera is in
 * front, whatever its height (its fascia and piers hide the farther deck's); where one runs
 * right over the other, the upper one is.
 */
export const spanOrder = (a: Span, b: Span): number => {
  // Spans of one deck follow each other: depth decides.
  if (a.bridge === b.bridge) return 0
  // Only decks that run side by side; where one crosses another, depth decides as before (a
  // higher crossing deck painted later would lay its piers over the nearer, lower deck).
  const ax = a.b[0] - a.a[0], ay = a.b[1] - a.a[1], bx = b.b[0] - b.a[0], by = b.b[1] - b.a[1]
  if (Math.abs(ax * bx + ay * by) < 0.97 * Math.hypot(ax, ay) * Math.hypot(bx, by)) return 0
  const mid = (s: Span): Vec2 => [(s.a[0] + s.b[0]) / 2, (s.a[1] + s.b[1]) / 2]
  const ba = beyond(a, mid(b))
  const ab = beyond(b, mid(a))
  // b beyond a's line, or a short of b's: a is nearer.
  const votes = (ba === null ? 0 : Math.sign(ba)) - (ab === null ? 0 : Math.sign(ab))
  if (votes !== 0) return votes > 0 ? 1 : -1
  // Not beside each other at all: depth decides.
  if (ba === null && ab === null) return 0
  // One right over the other: the upper deck.
  return a.z > b.z + 1 ? 1 : b.z > a.z + 1 ? -1 : 0
}

/** How far (meters) two footprints may overlap and still count as apart, with `stacked`. */
export const STACK_TOLERANCE = 0.03

/**
 * `components`: break a cycle within it. The plain rule forces the farthest unplaced item, which
 * may be in no cycle at all (a tower behind a building whose attic floors and roof form one) and
 * then paints before parts it should follow. With `components`, the item forced is the farthest
 * of those left that lie in a cycle (a strongly connected group of more than one item). A
 * region's `cutaway.order` asks for it; others keep the plain rule.
 */
export const paintOrder = (items: readonly Item[], cell = 96, stacked = false, components = false): Item[] => {
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
        const c = compare(items[i], items[j], stacked)
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
      if (components) i = cycleStart(after, done, farFirst)
      else {
        // A cycle: force the farthest unplaced item.
        while (done[byDepth[cursor]]) cursor++
        i = byDepth[cursor]
      }
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

/**
 * The item to force when every item left waits on another: of the items left that lie in a
 * strongly connected group of more than one (Tarjan's algorithm), the one `first` puts first.
 */
const cycleStart = (after: readonly number[][], done: readonly boolean[], first: (i: number, j: number) => number): number => {
  const n = after.length
  const index = new Array<number>(n).fill(-1)
  const low = new Array<number>(n).fill(0)
  const group = new Array<number>(n).fill(-1)
  const onStack = new Array<boolean>(n).fill(false)
  const stack: number[] = []
  let next = 0
  let groups = 0
  // Iterative, so a long chain cannot overflow the call stack.
  for (let root = 0; root < n; root++) {
    if (done[root] || index[root] >= 0) continue
    const work: [number, number][] = [[root, 0]]
    index[root] = low[root] = next++
    stack.push(root)
    onStack[root] = true
    while (work.length > 0) {
      const top = work[work.length - 1]
      const [v, k] = top
      if (k < after[v].length) {
        top[1]++
        const w = after[v][k]
        if (done[w]) continue
        if (index[w] < 0) {
          index[w] = low[w] = next++
          stack.push(w)
          onStack[w] = true
          work.push([w, 0])
        } else if (onStack[w]) low[v] = Math.min(low[v], index[w])
        continue
      }
      work.pop()
      if (work.length > 0) {
        const u = work[work.length - 1][0]
        low[u] = Math.min(low[u], low[v])
      }
      if (low[v] === index[v]) {
        let w: number
        do {
          w = stack.pop()!
          onStack[w] = false
          group[w] = groups
        } while (w !== v)
        groups++
      }
    }
  }
  const size = new Array<number>(groups).fill(0)
  for (let v = 0; v < n; v++) if (!done[v]) size[group[v]]++
  let best = -1
  for (let v = 0; v < n; v++) {
    if (done[v] || size[group[v]] < 2) continue
    if (best < 0 || first(v, best) < 0) best = v
  }
  if (best < 0) for (let v = 0; v < n; v++) if (!done[v] && (best < 0 || first(v, best) < 0)) best = v
  return best
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
