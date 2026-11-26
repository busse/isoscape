import assert from 'node:assert/strict'
import { test } from 'node:test'
import { mkdtemp, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import {
  END_BOUND, START_BOUND, UNSEEN_BEFORE, applyEvidence, evidenceEnd, evidenceStart, loadHistory, tracedWithEvidence,
  unconfirmedDated, unconfirmedTraced, type Dated, type Evidence, type Sighting, type TracedBuilding,
} from '../src/history.ts'
import { OUTBUILDING_AREA, OUTBUILDING_STREET, OUTBUILDING_WATER, isOutbuilding, paleItem } from '../src/scene.ts'
import { parseFlood } from '../src/flood.ts'
import { FLOOD_STYLES, UNCONFIRMED, mix, palette, withFloodStyles } from '../src/palette.ts'

const at = (date: number, call: Sighting['call'], source = `photo ${date}`): Sighting => ({ date, call, source })

test('the defaults: draw the later bound of an end, start at the first sighting, five years of doubt before it', () => {
  assert.equal(END_BOUND, 'later')
  assert.equal(START_BOUND, 'seen')
  assert.equal(UNSEEN_BEFORE, 5)
})

test('a traced building seen standing in 1974 and gone in 1999 is confirmed through 1974, unconfirmed until 1999', () => {
  const e = evidenceEnd(1950, [at(1974, 'present'), at(1999, 'gone'), at(2021, 'gone')])
  assert.deepEqual({ seen: e?.seen, to: e?.to, gone: e?.gone }, { seen: 1974, to: 1999, gone: 1999 })
  const b = { seen: e!.seen }
  assert.equal(unconfirmedTraced(b, 1972), false)
  assert.equal(unconfirmedTraced(b, 1974), false)
  assert.equal(unconfirmedTraced(b, 1985), true)
  // The earlier bound ends it the year after it was last seen.
  assert.equal(evidenceEnd(1950, [at(1974, 'present'), at(1999, 'gone')], 'earlier')?.to, 1975)
})

test('gone in 1974 but on the 1952 map: not ascertained for 1969 or 1972, so drawn unconfirmed then', () => {
  const e = evidenceEnd(1950, [at(1974, 'gone'), at(1999, 'gone')])!
  assert.equal(e.seen, 1950)
  assert.equal(e.to, 1974)
  for (const y of [1969, 1972]) assert.equal(unconfirmedTraced(e, y), true)
  assert.match(e.source, /last mapped 1950; photo 1974: gone/)
})

test('unclear sightings say nothing: the end waits for the first sighting of the spot empty', () => {
  const e = evidenceEnd(1950, [at(1974, 'unclear'), at(1999, 'unclear'), at(2002, 'gone')])!
  assert.equal(e.seen, 1950)
  assert.equal(e.to, 2002)
  // No sighting finds it gone: no end from the evidence (the old one stands).
  assert.equal(evidenceEnd(1950, [at(1974, 'unclear')]), null)
})

test('an undated building of today starts at its first sighting, with the years just before it unconfirmed', () => {
  const s = evidenceStart([at(1950, 'gone', 'Sanborn 1950'), at(1974, 'present'), at(1999, 'present'), at(2021, 'present')])!
  assert.deepEqual(s, { from: 1969, seen: 1974, source: 'photo 1974: standing' })
  // Never back to or before a source that shows the spot empty.
  const t = evidenceStart([at(2002, 'gone'), at(2017, 'present'), at(2021, 'present')])!
  assert.equal(t.from, 2012)
  const u = evidenceStart([at(2016, 'gone'), at(2017, 'present')])!
  assert.equal(u.from, 2017)
  // `earlier` goes back to the empty sighting.
  assert.equal(evidenceStart([at(2002, 'gone'), at(2017, 'present')], 'earlier')!.from, 2003)
})

test('a building on the traced maps and on every photo since is confirmed from its first map', () => {
  const s = evidenceStart([at(1924, 'present', 'Sanborn 1924'), at(1950, 'present', 'Sanborn 1950'), at(1974, 'unclear'), at(1999, 'present')])!
  assert.equal(s.seen, 1924)
  assert.equal(unconfirmedDated({ seen: s.seen }, 1972), false)
})

test('seen, gone, seen again: the later building counts', () => {
  const s = evidenceStart([at(1950, 'present', 'Sanborn 1950'), at(1974, 'present'), at(1999, 'present'), at(2002, 'gone'), at(2017, 'present')])!
  assert.equal(s.seen, 2017)
  assert.equal(evidenceStart([at(1974, 'unclear'), at(1999, 'gone')]), null)
})

test('applyEvidence dates only undated buildings, and tracedWithEvidence only assumed ends', () => {
  const ev: Evidence = {
    file: 'x', today: { w1: [at(1974, 'present')], w2: [at(1974, 'present')] },
    traced: { a: [at(1974, 'present'), at(1999, 'gone')], m: [at(1974, 'present'), at(1999, 'gone')] },
  }
  const dates = new Map<string, Dated>([['w2', { year: 1900, source: 'parcel' }]])
  const out = applyEvidence(dates, ev)
  assert.deepEqual(out.get('w1'), { year: 1969, seen: 1974, source: 'evidence', note: 'photo 1974: standing' })
  assert.deepEqual(out.get('w2'), { year: 1900, source: 'parcel' })
  const tb = (id: string, end: TracedBuilding['end']): TracedBuilding => ({ id, ring: [], from: 1886, to: 1960, end, material: 'brick', storeys: 3, edition: 1950, sheet: 1, lastSeen: 1950 })
  const [a, m] = tracedWithEvidence([tb('a', 'assumed'), tb('m', 'map')], ev)
  assert.equal(a.end, 'evidence')
  assert.equal(a.to, 1999)
  assert.equal(a.seen, 1974)
  assert.equal(m.to, 1960)
  assert.equal(m.end, 'map')
})

test('a history file names its evidence layer; without one, nothing changes', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'evidence-'))
  const lost = join(dir, 'lost.geojson')
  await writeFile(lost, JSON.stringify({ features: [{ properties: { id: 'a', from: 1924, lastSeen: 1950, to: 1960, end: 'assumed', material: 'brick', storeys: 2, edition: 1950, sheet: 3 }, geometry: { coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] } }] }))
  const evp = join(dir, 'ev.json')
  await writeFile(evp, JSON.stringify({ traced: { a: [at(1974, 'present'), at(1999, 'gone')] }, today: {} }))
  const base = join(dir, 'base.json')
  await writeFile(base, JSON.stringify({ sanborn: { lost, editions: [1950], source: 's' } }))
  const withEv = join(dir, 'with.json')
  await writeFile(withEv, JSON.stringify({ extends: base, evidence: evp }))
  const h0 = await loadHistory(base)
  const h1 = await loadHistory(withEv)
  assert.equal(h0.evidence, undefined)
  assert.equal(h0.traced[0].to, 1960)
  assert.equal(h1.traced[0].to, 1999)
  assert.equal(h1.traced[0].seen, 1974)
  assert.match(h1.traced[0].source ?? '', /photo 1974: standing/)
})

test('the unconfirmed look is palette-only: faces and roofs toward the paper, the finer ink, lines kept', () => {
  const it = {
    id: 'b', kind: 'building', hull: [], zMin: 0, zMax: 1, key: 0, dots: [],
    shapes: [{ pts: [], fill: '#806040', ink: true }, { pts: [], fill: 'none', line: true, stroke: { color: '#000000', width: 1 } }],
  } as unknown as Parameters<typeof paleItem>[0]
  const out = paleItem(it, UNCONFIRMED)
  assert.equal(out.shapes[0].fill, mix('#806040', UNCONFIRMED.tone, UNCONFIRMED.share))
  assert.equal(out.shapes[0].fine, true)
  assert.deepEqual(out.shapes[1], it.shapes[1])
  // A region picks its strength with a flood style.
  assert.deepEqual(withFloodStyles(palette('paper'), ['unconfirmed-ghost']).flood.unconfirmed, FLOOD_STYLES['unconfirmed-ghost'].unconfirmed)
  assert.equal(palette('paper').flood.unconfirmed, undefined)
})

test('the d3 cue: a darker roof and a dashed line round it, from the look alone', () => {
  const roof: [number, number][] = [[0, 0], [10, 0], [10, 5]]
  const it = {
    id: 'b', kind: 'building', hull: [], zMin: 0, zMax: 1, key: 0, dots: [],
    shapes: [{ pts: [[0, 9], [10, 9], [10, 14]], fill: '#806040', ink: true }, { pts: roof, fill: '#f0eee8', ink: true }],
  } as unknown as Parameters<typeof paleItem>[0]
  const look = FLOOD_STYLES['unconfirmed-slate-both'].unconfirmed!
  const out = paleItem(it, look, roof)
  assert.equal(out.shapes[0].fill, mix('#806040', look.tone, look.share))
  assert.equal(out.shapes[1].fill, mix('#f0eee8', look.roofTone!, look.roofShare!))
  const line = out.shapes[2]
  assert.equal(line.line, true)
  assert.deepEqual(line.stroke?.dash, look.outline!.dash)
  assert.equal(line.pts.length, roof.length + 1)
})

test('an outbuilding is small, off the street and dry with room to spare', () => {
  const sq = (s: number): [number, number][] => [[0, 0], [s, 0], [s, s], [0, s]]
  const never = () => false
  assert.equal(isOutbuilding(sq(5), never, () => false), true)
  assert.equal(isOutbuilding(sq(8), never, () => false), false) // 64 m², over OUTBUILDING_AREA
  assert.equal(isOutbuilding(sq(5), () => true, () => false), false) // fronts a street
  assert.equal(isOutbuilding(sq(5), never, (pts) => pts.some(([x]) => x > OUTBUILDING_WATER - 1)), false) // water within reach
  assert.equal(OUTBUILDING_AREA, 60)
  assert.equal(OUTBUILDING_STREET, 12)
  assert.equal(OUTBUILDING_WATER, 60)
})

test('a dry twin carries its flood as its reach', () => {
  const region = { name: 'x', floods: { wet: { level: 10 }, 'wet-dry': { level: -20, twinOf: 'wet' } } } as unknown as Parameters<typeof parseFlood>[0]
  assert.equal(parseFlood(region, 'wet-dry').reach?.level, 10)
  assert.equal(parseFlood(region, 'wet').reach, undefined)
})
