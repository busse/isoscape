/**
 * The traveler: a plain standing figure drawn to scale in a cutaway, to show how big the
 * building is and the way from the street to the train. Its height is a stated convention
 * (TRAVELER_HEIGHT, 1.75 m, 5 ft 9 in), not a claim from any source.
 *
 * The figure is a few flat polygons in meters: x forward (the way it faces), y up from its
 * feet. Head, body with arms, two legs in a short stride, and a small suitcase in the trailing
 * hand. The flat section draws it on the plane; the isometric view stands it upright, facing
 * left or right across the picture.
 */
import type { Vec2 } from './geom.ts'

export const TRAVELER_HEIGHT = 1.75

/** The figure's polygons, in meters, for a figure `h` tall facing +x. */
export const travelerShapes = (h = TRAVELER_HEIGHT): Vec2[][] => {
  const k = h / 1.75
  const P = (pts: readonly (readonly [number, number])[]): Vec2[] => pts.map(([x, y]) => [x * k, y * k])
  const head: Vec2[] = []
  for (let i = 0; i < 16; i++) {
    const a = (i / 16) * Math.PI * 2
    head.push([0.02 * k + 0.115 * k * Math.cos(a), 1.625 * k + 0.125 * k * Math.sin(a)])
  }
  return [
    head,
    // Neck, shoulders and body, the arms hanging at the sides, down to the hips.
    P([[-0.03, 1.49], [0.06, 1.49], [0.17, 1.44], [0.2, 1.36], [0.22, 0.86], [0.15, 0.86], [0.14, 1.2], [0.13, 0.86], [-0.13, 0.86], [-0.14, 1.2], [-0.16, 0.8], [-0.23, 0.8], [-0.21, 1.36], [-0.17, 1.44]]),
    // The forward leg, a little ahead, and the trailing leg, a little behind.
    P([[0.0, 0.88], [0.13, 0.88], [0.2, 0.0], [0.07, 0.0]]),
    P([[-0.12, 0.88], [0.02, 0.88], [-0.11, 0.0], [-0.24, 0.0]]),
    // A small suitcase in the trailing hand.
    P([[-0.36, 0.8], [-0.09, 0.8], [-0.09, 0.44], [-0.36, 0.44]]),
  ]
}
