/**
 * Graded ground in one hue (experimental, for the floods series' rain map): a `Tint` with
 * `tones: "rain"` is painted in a sequence of violet-blues, light to deep, one per value, in
 * place of the palette's four `tint.tones`; a value named `outline` takes the palette's mark
 * line. Each tone is mixed from the palette's own colors (its sky, its blue and red tint tones
 * and its ink), so no color is introduced outside palette.ts.
 *
 * Kept apart from render.ts and scene.ts on purpose: the scene hands the renderer a palette
 * whose `tint.tones` are the blues, and nothing else changes. A scene with no tint, or a tint
 * without `tones`, gets the palette it was given, the same object, so every other build is
 * unchanged byte for byte.
 */
import { mix, type Palette } from './palette.ts'

/** The tone sets a `Tint` may ask for by name. */
export type TintToneSet = 'rain'

/** The value that draws an outline (a thin ring polygon) in the palette's mark line, not a blue. */
export const OUTLINE = 'outline'

/**
 * `n` tones from near the paper to the set's deepest, evenly spaced (the first a faint wash,
 * not blank). The deepest stops short of the river's own blue in weight, so rain on the ground
 * is not read as standing water: a violet-blue, mixed from the palette's blue and red tint tones
 * and its ink, at most `reach` of the way from the paper.
 */
export const rainTones = (p: Palette, n: number, reach = 0.8): string[] => {
  const deep = mix(mix(p.tint.tones[1], p.tint.tones[3], 0.35), p.ink, 0.3)
  const out: string[] = []
  for (let k = 0; k < n; k++) out.push(mix(p.sky, deep, (0.05 + (0.95 * k) / Math.max(1, n - 1)) * reach))
  return out
}

/** The palette a scene's graded ground is painted with. */
export const tintPalette = (p: Palette, tint: { readonly tones?: TintToneSet; readonly values: readonly string[] } | undefined): Palette => {
  if (tint?.tones !== 'rain') return p
  const graded = tint.values.filter((v) => v !== OUTLINE)
  const blues = rainTones(p, graded.length)
  let k = 0
  return { ...p, tint: { ...p.tint, tones: tint.values.map((v) => (v === OUTLINE ? p.mark.line : blues[k++])) } }
}
