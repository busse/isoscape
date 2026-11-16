/**
 * The credit line a scene must carry: exactly the sources its drawing used, read from what the
 * scene did (its stats), never from a hand-kept string, so a print cannot credit a source it
 * does not draw from, or leave one out.
 *
 * - OpenStreetMap, always (ODbL: produced works must credit it).
 * - The elevation source by name (and its fill source), when the ground has relief.
 * - Land cover, when cover classes were read onto the ground (USGS NLCD 2021, public domain).
 * - Building footprints from Microsoft's model, when any is drawn (ODbL).
 * - Assessor's year-built records, when a date from them decided whether or how a building
 *   is drawn (a past year, or new since the previous one).
 * - Sanborn Fire Insurance Maps, when any building traced from them is drawn.
 */

import { demCredit } from './dem-sources.ts'
import type { Region } from './region.ts'

export const CREDIT_OSM = 'Map data © OpenStreetMap contributors (ODbL)'
export const CREDIT_NLCD = 'Land cover: USGS National Land Cover Database 2021 (MRLC, public domain)'
export const CREDIT_MICROSOFT = 'Building footprints: Microsoft Global ML Building Footprints (ODbL)'
export const CREDIT_SANBORN = 'Historic buildings traced from Sanborn Fire Insurance Maps, Library of Congress'
/** For a dated series whose year-built source names no credit of its own. */
export const CREDIT_YEAR_BUILT = 'Buildings dated from assessor records'

export const sceneCredits = (region: Region, stats: Readonly<Record<string, number>>, flat: boolean): string[] => {
  const out = [CREDIT_OSM]
  if (!flat) out.push(demCredit(region))
  if ((stats.coverNodes ?? 0) > 0) out.push(CREDIT_NLCD)
  if ((stats.footprintsDrawn ?? 0) > 0) out.push(CREDIT_MICROSOFT)
  if ((stats.datedFromParcels ?? 0) > 0) out.push(region.time?.yearBuilt?.credit ?? CREDIT_YEAR_BUILT)
  if ((stats.traced ?? 0) > 0) out.push(CREDIT_SANBORN)
  return out
}
