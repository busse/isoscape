/**
 * Dev tool (floods series, period city): how many buildings each choice of bound draws in each
 * plate year, over the evidence file (before the scene's own leave-outs: water, track, frame).
 *
 *   node tools/floods/period/choices.ts
 */
import { evidenceEnd, evidenceStart, loadHistory, type Sighting } from '../../../src/history.ts'

const h = await loadHistory('history/richmond-downtown.json')
const ev = (await loadHistory('history/richmond-floods.json')).evidence!
const years = [1969, 1972, 1985, 1996, 2004, 2020]
const traced = new Map(h.traced.map((b) => [b.id, b]))
const out: Record<string, Record<number, { confirmed: number; unconfirmed: number }>> = {}
for (const end of ['later', 'earlier'] as const) {
  for (const start of ['seen', 'earlier'] as const) {
    const key = `end ${end}, start ${start}`
    out[key] = {}
    for (const y of years) {
      let c = 0, u = 0
      for (const [id, s] of Object.entries(ev.traced)) {
        const b = traced.get(id)
        if (b === undefined || b.from > y) continue
        const e = evidenceEnd(b.lastSeen ?? b.edition, s as Sighting[], end)
        const to = e?.to ?? b.to
        if (y >= to) continue
        if (e !== null && y > e.seen) u++
        else c++
      }
      for (const s of Object.values(ev.today)) {
        const st = evidenceStart(s as Sighting[], start)
        if (st === null || y < st.from) continue
        if (y < st.seen) u++
        else c++
      }
      out[key][y] = { confirmed: c, unconfirmed: u }
    }
  }
}
console.log(JSON.stringify(out, null, 1))
