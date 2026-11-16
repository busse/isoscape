import assert from 'node:assert/strict'
import { test } from 'node:test'
import { partLevels } from '../src/parts.ts'

test('parts resting on a support share its top on sloping ground', () => {
  // A porch on ground falling from 7.1 to 6.0, two columns on ground at different heights, and
  // an entablature on the first column: every column stands on the porch top, both reach the
  // same height, and the entablature starts there.
  const levels = partLevels([
    { id: 'entablature', on: 'column-1', height: 2.5, grounds: [6.1, 7.1] },
    { id: 'porch', height: 1, grounds: [6.0, 7.1] },
    { id: 'column-1', on: 'porch', height: 11.5, grounds: [7.08, 7.12] },
    { id: 'column-2', on: 'porch', height: 11.5, grounds: [6.3, 6.4] },
  ])
  assert.equal(levels.get('porch'), 6.0)
  assert.equal(levels.get('column-1'), 7.0)
  assert.equal(levels.get('column-2'), 7.0)
  assert.equal(levels.get('entablature'), 18.5)
})

test('without a support a part sits on its own ground, plus its base', () => {
  const levels = partLevels([
    { id: 'low', grounds: [3, 5], base: 2 },
    { id: 'high', seat: 'max', grounds: [3, 5] },
    { id: 'lost', on: 'nowhere', grounds: [4, 6] },
    { id: 'a', on: 'b', grounds: [1, 2], height: 1 },
    { id: 'b', on: 'a', grounds: [5, 6], height: 1 },
  ])
  assert.equal(levels.get('low'), 5)
  assert.equal(levels.get('high'), 5)
  assert.equal(levels.get('lost'), 4)
  // A cycle is cut where it closes: one of the pair keeps its own ground.
  assert.ok(Number.isFinite(levels.get('a')) && Number.isFinite(levels.get('b')))
})

test('absolute part elevations keep true meters between parts on exaggerated terrain', async () => {
  const { modelZ } = await import('../src/scene.ts')
  // Ground exaggerated 3x from a 60 m datum; the model's ground is at 66 m. Columns from 67.4 m,
  // 11.8 m tall, carry an entablature given at 79.2 m: it must start where they end.
  const z = modelZ({ datum: 60, exaggeration: 3 }, [66, 65, 70])
  assert.equal(z(66), 18)
  assert.ok(Math.abs(z(67.4) + 11.8 - z(79.2)) < 1e-9)
  // Without exaggeration nothing changes.
  const plain = modelZ({ datum: 60, exaggeration: 1 }, [66])
  assert.equal(plain(79.2), 79.2 - 60)
})

test('a streetcar line that runs along a road bridge leaves the ground there; one passing under does not', async () => {
  const { offDecks, onDeck } = await import('../src/scene.ts')
  const deck = [{ a: [100, 0] as [number, number], b: [200, 0] as [number, number], half: 5 }]
  // Along the bridge, 4 m off its center line: cut out between the abutments.
  const runs = offDecks([[0, 4], [300, 4]], deck)
  assert.equal(runs.length, 2)
  assert.ok(runs[0][runs[0].length - 1][0] <= 102 && runs[0][runs[0].length - 1][0] >= 96)
  assert.ok(runs[1][0][0] >= 196 && runs[1][0][0] <= 204)
  // Crossing under it: drawn whole.
  assert.equal(offDecks([[150, -50], [150, 50]], deck).length, 1)
  assert.equal(onDeck([150, 0], [0, 1], deck), false)
  // A parallel street 20 m away is not on it.
  assert.equal(offDecks([[0, 20], [300, 20]], deck).length, 1)
})
