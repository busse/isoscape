/**
 * The traveler: a plain standing figure drawn to scale in a cutaway, to show how big the
 * building is and the way from the street to the train. Its height is a stated convention
 * (TRAVELER_HEIGHT, 1.75 m, 5 ft 9 in), not a claim from any source.
 *
 * The figure is a few flat polygons in meters: x forward (the way it faces), y up from its
 * feet. Head, body with arms, two legs in a short stride, and a small suitcase in the trailing
 * hand. The flat section draws it on the plane; the isometric view stands it upright, facing
 * left or right across the picture.
 *
 * A cutaway of a place people visited rather than passed through draws visitors instead: the
 * same figure with empty hands (`visitor`), or one in a long skirt to the ground
 * (`visitor-skirt`). Both are the same stated height; neither claims who was there.
 *
 * A cutaway set in the late 1920s draws patrons in that decade's dress: a woman in a cloche hat
 * and a coat to just below the knee (`patron`), a man in a brimmed hat (`patron-hat`), and a
 * figure seated at a keyboard (`seated`, an organist at a console), its feet on the floor and
 * its hands forward at the keys. The same stated height standing; no one in particular.
 */
import type { Vec2 } from './geom.ts'

export const TRAVELER_HEIGHT = 1.75

/** Which figure a cutaway draws: the traveler with a suitcase, or a visitor. */
export type Figure = 'traveler' | 'visitor' | 'visitor-skirt' | 'patron' | 'patron-hat' | 'seated'

/** The figure's polygons, in meters, for a figure `h` tall facing +x. */
export const travelerShapes = (h = TRAVELER_HEIGHT, figure: Figure = 'traveler'): Vec2[][] => {
  const k = h / 1.75
  const P = (pts: readonly (readonly [number, number])[]): Vec2[] => pts.map(([x, y]) => [x * k, y * k])
  const head: Vec2[] = []
  for (let i = 0; i < 16; i++) {
    const a = (i / 16) * Math.PI * 2
    head.push([0.02 * k + 0.115 * k * Math.cos(a), 1.625 * k + 0.125 * k * Math.sin(a)])
  }
  if (figure === 'patron') {
    return [
      head,
      // A cloche hat: a close crown down to the brow, a narrow brim.
      P([[-0.13, 1.6], [-0.12, 1.7], [-0.06, 1.77], [0.05, 1.78], [0.13, 1.72], [0.16, 1.62], [0.19, 1.6], [0.18, 1.58], [-0.14, 1.58]]),
      // A coat from the shoulders to just below the knee, the arms in it.
      P([[-0.03, 1.49], [0.06, 1.49], [0.17, 1.44], [0.2, 1.36], [0.22, 0.9], [0.17, 0.9], [0.17, 0.42], [-0.19, 0.42], [-0.2, 0.9], [-0.23, 0.9], [-0.21, 1.36], [-0.17, 1.44]]),
      // The legs below the hem, in a short stride.
      P([[0.02, 0.43], [0.11, 0.43], [0.15, 0.0], [0.07, 0.0]]),
      P([[-0.11, 0.43], [-0.02, 0.43], [-0.1, 0.0], [-0.18, 0.0]]),
    ]
  }
  if (figure === 'seated') {
    // Seated on a bench 0.5 m high, facing +x: the torso upright, the thighs forward, the shins
    // down to the floor, the forearms forward to a keyboard. Its head stands at about 1.3 m.
    const sh: Vec2[] = []
    for (let i = 0; i < 16; i++) {
      const a = (i / 16) * Math.PI * 2
      sh.push([0.115 * k * Math.cos(a), 1.3 * k + 0.125 * k * Math.sin(a)])
    }
    return [
      sh,
      P([[-0.05, 1.17], [0.05, 1.17], [0.14, 1.12], [0.15, 1.04], [0.13, 0.6], [-0.15, 0.55], [-0.17, 1.04], [-0.14, 1.12]]),
      // The upper arm down and the forearm out to the keys.
      P([[0.06, 1.08], [0.15, 1.06], [0.16, 0.84], [0.42, 0.86], [0.42, 0.78], [0.08, 0.76]]),
      // Thigh, and shin to the floor.
      P([[-0.12, 0.62], [0.36, 0.62], [0.38, 0.48], [-0.12, 0.48]]),
      P([[0.26, 0.55], [0.38, 0.55], [0.4, 0.0], [0.28, 0.0]]),
    ]
  }
  if (figure === 'patron-hat') {
    return [
      head,
      // A brimmed hat.
      P([[-0.17, 1.705], [0.21, 1.705], [0.21, 1.73], [0.12, 1.735], [0.11, 1.84], [-0.09, 1.84], [-0.1, 1.735], [-0.17, 1.73]]),
      P([[-0.03, 1.49], [0.06, 1.49], [0.17, 1.44], [0.2, 1.36], [0.22, 0.86], [0.15, 0.86], [0.14, 1.2], [0.13, 0.86], [-0.13, 0.86], [-0.14, 1.2], [-0.16, 0.8], [-0.23, 0.8], [-0.21, 1.36], [-0.17, 1.44]]),
      P([[0.0, 0.88], [0.13, 0.88], [0.2, 0.0], [0.07, 0.0]]),
      P([[-0.12, 0.88], [0.02, 0.88], [-0.11, 0.0], [-0.24, 0.0]]),
    ]
  }
  if (figure === 'visitor-skirt') {
    return [
      head,
      // Neck, shoulders and a fitted bodice, the arms at the sides, to the waist.
      P([[-0.03, 1.49], [0.06, 1.49], [0.16, 1.44], [0.19, 1.36], [0.21, 0.9], [0.14, 0.9], [0.12, 1.12], [-0.12, 1.12], [-0.14, 0.9], [-0.21, 0.9], [-0.19, 1.36], [-0.15, 1.44]]),
      // A long skirt from the waist to the ground, fuller behind.
      P([[-0.11, 1.14], [0.11, 1.14], [0.22, 0.0], [-0.3, 0.0]]),
    ]
  }
  return [
    head,
    // Neck, shoulders and body, the arms hanging at the sides, down to the hips.
    P([[-0.03, 1.49], [0.06, 1.49], [0.17, 1.44], [0.2, 1.36], [0.22, 0.86], [0.15, 0.86], [0.14, 1.2], [0.13, 0.86], [-0.13, 0.86], [-0.14, 1.2], [-0.16, 0.8], [-0.23, 0.8], [-0.21, 1.36], [-0.17, 1.44]]),
    // The forward leg, a little ahead, and the trailing leg, a little behind.
    P([[0.0, 0.88], [0.13, 0.88], [0.2, 0.0], [0.07, 0.0]]),
    P([[-0.12, 0.88], [0.02, 0.88], [-0.11, 0.0], [-0.24, 0.0]]),
    // A small suitcase in the trailing hand.
    ...(figure === 'traveler' ? [P([[-0.36, 0.8], [-0.09, 0.8], [-0.09, 0.44], [-0.36, 0.44]])] : []),
  ]
}
