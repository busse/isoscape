/**
 * What a feature *is*, decided from its OSM tags: which ground layer a polygon paints in,
 * how wide a road is, how tall a building stands.
 */

import type { Tags } from './osm.ts'

export type GroundKind = 'water' | 'island' | 'green' | 'wood' | 'rock' | 'parking' | 'cemetery'

export const groundKind = (t: Tags): GroundKind | null => {
  if (t.building !== undefined || t['building:part'] !== undefined) return null
  if (t.natural === 'water' || t.water !== undefined || t.waterway === 'riverbank' || t.waterway === 'dock') return 'water'
  if (t.place === 'island' || t.place === 'islet') return 'island'
  if (t.landuse === 'forest' || t.natural === 'wood' || t.natural === 'scrub' || t.natural === 'wetland') return 'wood'
  if (t.natural === 'bare_rock' || t.natural === 'sand' || t.natural === 'beach') return 'rock'
  if (t.landuse === 'cemetery') return 'cemetery'
  if (t.amenity === 'parking') return 'parking'
  if (
    t.leisure === 'park' || t.leisure === 'garden' || t.leisure === 'pitch' || t.leisure === 'playground' ||
    t.leisure === 'nature_reserve' || t.landuse === 'grass' || t.landuse === 'meadow' ||
    t.landuse === 'recreation_ground' || t.landuse === 'village_green' || t.natural === 'grassland'
  ) {
    return 'green'
  }
  return null
}

/** Paint order of the ground layers, bottom first. Water and islands are handled apart. */
export const GROUND_ORDER: readonly GroundKind[] = ['green', 'cemetery', 'wood', 'rock', 'parking']

/** Carriageway widths in metres. Missing means "do not draw". */
const ROAD_WIDTH: Readonly<Record<string, number>> = {
  motorway: 14, trunk: 12, primary: 11, secondary: 10, tertiary: 8.5,
  motorway_link: 7, trunk_link: 7, primary_link: 7, secondary_link: 6.5, tertiary_link: 6,
  residential: 7, unclassified: 6.5, living_street: 5, service: 4, pedestrian: 5,
  footway: 1.8, path: 1.8, cycleway: 2, track: 3, bridleway: 1.8,
}

export const roadWidth = (t: Tags): number | null => {
  if (t.highway === undefined || t.area === 'yes') return null
  if (t.tunnel !== undefined && t.tunnel !== 'no') return null
  if (t.highway === 'service' && (t.service === 'parking_aisle' || t.service === 'drive-through')) return 3
  const explicit = parseLength(t.width)
  return explicit ?? ROAD_WIDTH[t.highway] ?? null
}

export const isPath = (t: Tags): boolean =>
  ['footway', 'path', 'cycleway', 'track', 'bridleway', 'pedestrian'].includes(t.highway ?? '')

export const isRail = (t: Tags): boolean =>
  ['rail', 'light_rail', 'subway', 'narrow_gauge', 'tram', 'disused', 'abandoned'].includes(t.railway ?? '') &&
  (t.tunnel === undefined || t.tunnel === 'no')

/** Canals and streams drawn as lines; rivers are drawn from their area polygons instead. */
export const waterwayWidth = (t: Tags): number | null => {
  switch (t.waterway) {
    case 'canal': return parseLength(t.width) ?? 12
    case 'stream': return 3
    case 'ditch': case 'drain': return 1.5
    default: return null
  }
}

export const isBridge = (t: Tags): boolean => t.bridge !== undefined && t.bridge !== 'no'

/** "12", "12 m", "40'", "40 ft", "12.5m" → metres. */
export const parseLength = (v: string | undefined): number | null => {
  if (v === undefined) return null
  const s = v.trim().toLowerCase()
  const feet = s.match(/^([\d.]+)\s*(?:'|ft|feet)$/)
  if (feet) return parseFloat(feet[1]) * 0.3048
  const ftIn = s.match(/^(\d+)'\s*(\d+)"?$/)
  if (ftIn) return parseInt(ftIn[1], 10) * 0.3048 + parseInt(ftIn[2], 10) * 0.0254
  const m = s.match(/^([\d.]+)\s*m?$/)
  if (m) {
    const n = parseFloat(m[1])
    return Number.isFinite(n) ? n : null
  }
  return null
}

export type BuildingClass = 'residential' | 'commercial' | 'industrial' | 'civic' | 'other'

export const buildingClass = (t: Tags): BuildingClass => {
  const b = t.building ?? t['building:part'] ?? 'yes'
  if (['house', 'detached', 'semidetached_house', 'terrace', 'residential', 'apartments', 'dormitory', 'bungalow'].includes(b)) return 'residential'
  if (['commercial', 'office', 'retail', 'hotel', 'supermarket', 'kiosk'].includes(b)) return 'commercial'
  if (['industrial', 'warehouse', 'manufacture', 'garage', 'garages', 'shed', 'hangar', 'storage_tank', 'silo', 'service', 'parking', 'train_station', 'transportation', 'ruins'].includes(b)) return 'industrial'
  if (['church', 'cathedral', 'chapel', 'civic', 'public', 'government', 'school', 'university', 'college', 'museum', 'hospital', 'courthouse', 'fire_station'].includes(b)) return 'civic'
  return 'other'
}

const METRES_PER_LEVEL = 3.4

/** A tag as a finite number, or null. OSM holds anything (one building's min_level is "federal"). */
const finite = (v: string | undefined): number | null => {
  if (v === undefined) return null
  const n = parseFloat(v)
  return Number.isFinite(n) ? n : null
}

/**
 * Height and base of a building, in metres. OSM's own `height` wins, then levels; failing
 * both, a guess from the building's type and footprint, which is what most of a city will be
 * until lidar heights are joined in.
 */
export const buildingHeights = (t: Tags, footprintArea: number): { base: number; top: number; source: 'height' | 'levels' | 'guess' } => {
  const minLevel = finite(t['building:min_level'])
  const base = Math.max(0, parseLength(t.min_height) ?? (minLevel !== null ? minLevel * METRES_PER_LEVEL : 0))
  const height = parseLength(t.height)
  if (height !== null && height > base) return { base, top: height, source: 'height' }
  const levels = finite(t['building:levels']) ?? NaN
  if (Number.isFinite(levels) && levels > 0) {
    const roof = finite(t['roof:levels']) ?? 0
    return { base, top: Math.max(base + 2.5, (levels + roof * 0.5) * METRES_PER_LEVEL + 0.8), source: 'levels' }
  }
  const b = t.building ?? t['building:part'] ?? 'yes'
  let guess: number
  if (footprintArea < 40 || ['shed', 'garage', 'garages', 'kiosk', 'roof', 'carport'].includes(b)) guess = 3.2
  else if (['house', 'detached', 'semidetached_house', 'bungalow'].includes(b)) guess = 8
  else if (['terrace', 'residential'].includes(b)) guess = 10
  else if (['apartments', 'dormitory', 'hotel'].includes(b)) guess = 16
  else if (['office', 'commercial'].includes(b)) guess = footprintArea > 1500 ? 24 : 13
  else if (['industrial', 'warehouse', 'manufacture'].includes(b)) guess = 11
  else if (['church', 'cathedral'].includes(b)) guess = 16
  else if (b === 'ruins') guess = 6
  else guess = footprintArea > 2500 ? 14 : footprintArea > 600 ? 11 : 8
  return { base, top: Math.max(base + 2.5, guess), source: 'guess' }
}
