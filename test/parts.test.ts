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
