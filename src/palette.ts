/**
 * Colors and line weights. A palette is the whole style: there is no other place a color is
 * chosen. Line weights are in screen pixels, so they hold at any `scale`.
 */

import type { PartTone } from './history.ts'

export interface Palette {
  readonly sky: string
  readonly land: string
  readonly slab: string
  readonly slabWater: string
  readonly water: string
  readonly waterLine: string
  readonly green: string
  readonly wood: string
  readonly marsh: string
  /** Land cover groups (NLCD), drawn under OSM's own land use. */
  readonly cover: Readonly<Record<'forest' | 'evergreen' | 'swamp' | 'marsh' | 'field' | 'crop' | 'scrub' | 'barren', string>>
  readonly sand: string
  readonly rock: string
  readonly parking: string
  readonly cemetery: string
  readonly road: string
  readonly path: string
  readonly rail: string
  readonly railTie: string
  readonly deck: string
  readonly fascia: string
  readonly pier: string
  readonly ink: string
  /** Whitewater: rapids marks and weir crests. */
  readonly foam: string
  /** Rock standing clear of the river. */
  readonly boulder: string
  /** Hillshade: what slopes turned to the light are washed with, and what turned away. */
  readonly shadeLight: string
  readonly shadeDark: string
  /**
   * Hillshade strength: the wash's opacity per step of shade toward or away from the light,
   * and the most it may reach. A step is 1/22 of the full range of light · normal.
   */
  readonly shadeLightStep: number
  readonly shadeDarkStep: number
  readonly shadeMax: number
  /** Contour ink opacity, minor and major. */
  readonly contourMinor: number
  readonly contourMajor: number
  /** Wall tones: the face turned to the light, and the face turned away. */
  readonly wallLit: string
  readonly wallShade: string
  /** Roof tones by building class; a building picks one deterministically by its id. */
  /** Dated scenes: roofs of buildings new since the previous scene, landmarks now lost, burned
   * shells, the burned district's ground, and a town plan's outline tint. */
  readonly fresh: string
  readonly lost: string
  readonly ash: string
  readonly burned: string
  readonly plan: string
  /** Vanished pleasure grounds (a fairground), and a racetrack's dirt oval. */
  readonly grounds: string
  readonly racetrack: string
  /** Roofs of buildings traced from fire-insurance maps, in the maps' own color code. */
  readonly traced: Readonly<Record<'brick' | 'frame' | 'stone' | 'iron' | 'special' | 'fireproof', string>>
  /** Streetcar lines on the ground, and the cars on them: side lit, side in shade, roof. */
  readonly tram: string
  readonly tramCar: readonly [string, string, string]
  /**
   * A modeled building's parts, by tone: side lit, side in shade, roof. Broad Street Station's
   * Indiana limestone, its dome's terra-cotta tile, the iron of its platform canopies and their
   * roofing, the plastered ramp houses, and the trains: Pullman-green coaches, black engines,
   * boxcar-red freight; and, for the larger trains of a cutaway, an engine's iron in a grey
   * light enough for its edges to show, the coal in its tender, and a coach's darker roof.
   */
  readonly parts: Readonly<Record<PartTone, readonly [string, string, string]>>
  /**
   * Cutaways: the ink fill of every cut surface (poché), the dashed outline of what was lifted
   * away, and the traveler's path on a flat section, with its stroke width and dash in pixels.
   */
  readonly poche: string
  readonly cutOutline: string
  readonly cutOutlineDash: readonly [number, number]
  readonly route: string
  readonly routeWidth: number
  readonly routeDash: readonly [number, number]
  /** Station platforms, and the running rails of a track at close scale. */
  readonly platform: string
  readonly railSteel: string
  readonly roofs: Readonly<Record<'residential' | 'commercial' | 'industrial' | 'civic' | 'other', readonly string[]>>
  readonly lineWidth: number
  readonly groundLineWidth: number
  readonly dotRadius: number
}

const paper: Palette = {
  sky: '#f4f1ea',
  land: '#ebe5d6',
  slab: '#cdbfa3',
  slabWater: '#8fb3c4',
  water: '#a8cad8',
  waterLine: '#7fa9bc',
  green: '#d3dfb9',
  wood: '#bccf9e',
  marsh: '#c9d6ae',
  cover: {
    forest: '#c3d3a3',
    evergreen: '#b3c697',
    swamp: '#bdd0b0',
    marsh: '#d0dcb6',
    field: '#e5e4c3',
    crop: '#ebdfc2',
    scrub: '#dcd8b4',
    barren: '#ece4cc',
  },
  sand: '#efe4c4',
  rock: '#d9d2c3',
  parking: '#e2ddd1',
  cemetery: '#cbd9b4',
  road: '#faf7ef',
  path: '#f3eee2',
  rail: '#b3a993',
  railTie: '#6e6656',
  deck: '#f2eee4',
  fascia: '#a49b8a',
  pier: '#8d8576',
  ink: '#2c2b33',
  foam: '#ffffff',
  boulder: '#cbbfa8',
  shadeLight: '#fffaf0',
  shadeDark: '#4a3b26',
  shadeLightStep: 0.045,
  shadeDarkStep: 0.04,
  shadeMax: 0.55,
  contourMinor: 0.16,
  contourMajor: 0.34,
  wallLit: '#ece7dc',
  wallShade: '#c3bbac',
  fresh: '#f2c879',
  lost: '#c98f7a',
  ash: '#6d6259',
  burned: '#d3c3ad',
  plan: '#e4dcc4',
  grounds: '#ddd0a8',
  racetrack: '#b39a6c',
  traced: { brick: '#e9c2b8', frame: '#efe0a6', stone: '#c3d3e2', iron: '#cfcdc8', special: '#c5dcc0', fireproof: '#cfc6a4' },
  tram: '#b8362c',
  tramCar: ['#c9473a', '#8f2a22', '#e8d9b0'],
  parts: {
    stone: ['#f1e9d6', '#cdbf9f', '#e7dcc2'],
    dome: ['#b2b8a6', '#808a7a', '#c0c5b4'],
    iron: ['#5d4f48', '#3a302c', '#9a5a45'],
    ramp: ['#f4efe4', '#d2cabb', '#ece5d6'],
    coach: ['#58704f', '#364934', '#3a3b3a'],
    engine: ['#4a4a4d', '#242427', '#333336'],
    freight: ['#a8553d', '#74382a', '#8c4632'],
    plaster: ['#f7f2e6', '#ddd4c2', '#f3ede0'],
    floor: ['#e9e1cf', '#cfc4ad', '#f6f1e4'],
    wood: ['#9a7350', '#6f5038', '#b08a62'],
    glass: ['#c9d3cf', '#a9b6b2', '#d9e0dc'],
    tram: ['#c9473a', '#8f2a22', '#e8d9b0'],
    roof: ['#8b8c84', '#6a6b64', '#8e8f87'],
    loco: ['#6b6c70', '#4a4b4f', '#5a5b5f'],
    coal: ['#403e3b', '#2f2e2c', '#4a4744'],
    carRoof: ['#43553d', '#2f3d2b', '#4a5d43'],
    brick: ['#c98c76', '#a46a57', '#b77d69'],
    terracotta: ['#f1ece2', '#d4cdbf', '#ebe5d8'],
    gold: ['#d9b25e', '#b08a3e', '#e3c37a'],
    bronze: ['#a88a55', '#7c6439', '#b89a64'],
    seat: ['#a6403a', '#7a2c28', '#b8534a'],
    pipe: ['#d9d3c2', '#b3ab97', '#e5e0d2'],
    screen: ['#fbfaf5', '#ecebe4', '#ffffff'],
    lamp: ['#f6e7b8', '#e0c98a', '#fbf0cf'],
    marble: ['#3a3638', '#262325', '#4a4446'],
    water: ['#a8cad8', '#7fa9bc', '#b9d6e2'],
    earth: ['#cdbfa3', '#b3a58a', '#d6c9ae'],
  },
  poche: '#2c2b33',
  cutOutline: '#2c2b33',
  cutOutlineDash: [6, 4],
  route: '#b5392f',
  routeWidth: 2.6,
  routeDash: [9, 6],
  platform: '#efe9dc',
  railSteel: '#4f4a45',
  roofs: {
    residential: ['#f6e9d8', '#f1e2cf', '#f7efe2', '#efd9c5'],
    commercial: ['#fbfaf6', '#f0eee8', '#e9e7e1', '#f6f4ee'],
    industrial: ['#dfdcd5', '#d6d3cb', '#e4e1d9'],
    civic: ['#f3e7c9', '#eedfbf'],
    other: ['#f5f2ea', '#eeeae0'],
  },
  lineWidth: 0.6,
  groundLineWidth: 0.35,
  dotRadius: 1.45,
}

const night: Palette = {
  ...paper,
  sky: '#14161d',
  land: '#1d2029',
  slab: '#2b2f3b',
  slabWater: '#1d3442',
  water: '#1b2e3b',
  waterLine: '#2c4a5c',
  green: '#22302a',
  wood: '#1f2d25',
  marsh: '#26332b',
  cover: {
    forest: '#203027',
    evergreen: '#1b2a22',
    swamp: '#1f2e2e',
    marsh: '#25322c',
    field: '#262a26',
    crop: '#2a2a25',
    scrub: '#272a24',
    barren: '#2b2b2a',
  },
  sand: '#33322b',
  rock: '#2a2c33',
  parking: '#24272f',
  cemetery: '#223027',
  road: '#2c303b',
  path: '#272a33',
  rail: '#3a3d47',
  railTie: '#5a5e6b',
  deck: '#323744',
  fascia: '#40465a',
  pier: '#3c4150',
  ink: '#c9d1e6',
  foam: '#b7d3e2',
  boulder: '#4a4d58',
  shadeLight: '#46526e',
  shadeDark: '#000000',
  shadeLightStep: 0.045,
  shadeDarkStep: 0.04,
  shadeMax: 0.55,
  contourMinor: 0.14,
  contourMajor: 0.3,
  wallLit: '#363b4a',
  wallShade: '#272b37',
  fresh: '#8a6f3c',
  lost: '#7a4a3e',
  ash: '#121114',
  burned: '#3a2f2a',
  plan: '#252836',
  grounds: '#2e2c2a',
  racetrack: '#4a3f30',
  traced: { brick: '#5a3c3a', frame: '#5a5236', stone: '#34465a', iron: '#45454a', special: '#3a4f3c', fireproof: '#4f4a36' },
  tram: '#e0614f',
  tramCar: ['#f07a5f', '#b04a3a', '#f2e2b8'],
  parts: {
    stone: ['#5a5648', '#3e3b33', '#4c4940'],
    dome: ['#45503f', '#2f372c', '#525c49'],
    iron: ['#2a2b33', '#1b1c22', '#5a3a32'],
    ramp: ['#4a4a4e', '#36363b', '#404045'],
    coach: ['#2f4a33', '#1f3022', '#26282b'],
    engine: ['#2a2b30', '#17181c', '#212226'],
    freight: ['#5e3328', '#40231c', '#4f2b22'],
    plaster: ['#4a4a50', '#36363b', '#45454a'],
    floor: ['#3a3a40', '#2c2c31', '#424248'],
    wood: ['#5a4434', '#3e2f24', '#6a5140'],
    glass: ['#3c4a52', '#2c3840', '#46545c'],
    tram: ['#f07a5f', '#b04a3a', '#f2e2b8'],
    roof: ['#4a4b48', '#383936', '#525350'],
    loco: ['#3a3b40', '#26272c', '#303136'],
    coal: ['#1f1f22', '#161618', '#29292c'],
    carRoof: ['#24382a', '#18261c', '#2a3e2f'],
    brick: ['#5b3a37', '#3d2727', '#4a3230'],
    terracotta: ['#8d8f98', '#62656f', '#9a9ca5'],
    gold: ['#8a7240', '#5e4d2c', '#9a8150'],
    bronze: ['#6a5838', '#4a3d27', '#776443'],
    seat: ['#6a2a28', '#4a1d1c', '#7a3330'],
    pipe: ['#6e6a62', '#4e4b45', '#7a766d'],
    screen: ['#d8d6cf', '#b8b6af', '#e2e0da'],
    lamp: ['#e8d49a', '#c9b273', '#f0dfae'],
    marble: ['#2a2628', '#1a1718', '#3a3437'],
    water: ['#1b2e3b', '#152430', '#22384a'],
    earth: ['#2b2f3b', '#20232c', '#323644'],
  },
  poche: '#c9d1e6',
  cutOutline: '#c9d1e6',
  route: '#e0614f',
  platform: '#3a3d48',
  railSteel: '#8a90a2',
  roofs: {
    residential: ['#3d3f4c', '#42434f'],
    commercial: ['#454a5a', '#3f4453'],
    industrial: ['#353844', '#393c47'],
    civic: ['#4a4636', '#4d4838'],
    other: ['#3c3f4b'],
  },
}

/**
 * A winter night with the lights on inside: the street, the ground and the outsides of
 * buildings in moonlit blues and dark brick, and a modeled building's rooms in warm lamplight
 * (plaster, gilding, crimson velvet), so a cutaway's open rooms glow against the dark. The cut
 * itself is inked dark, and the dashed outline of what was lifted away is drawn light, so it
 * reads on the dark ground.
 */
const winter: Palette = {
  ...night,
  sky: '#151b2a',
  land: '#1f2636',
  slab: '#3a3230',
  road: '#2a3141',
  path: '#363e51',
  ink: '#1c1517',
  wallLit: '#3a4152',
  wallShade: '#2a2f3d',
  parts: {
    ...night.parts,
    stone: ['#ead8b4', '#c9ae84', '#f0e0c2'],
    plaster: ['#f2dcaa', '#d6b67c', '#f6e6bf'],
    floor: ['#b98a5c', '#94673f', '#c9a070'],
    wood: ['#8e5d38', '#673f25', '#a06d45'],
    glass: ['#f2cf7a', '#d9ae55', '#f6dc98'],
    roof: ['#3e4454', '#2c313d', '#465062'],
    iron: ['#3c383a', '#282527', '#4c4648'],
    coal: ['#1f1d1e', '#141313', '#2a2829'],
    brick: ['#6a423c', '#47302c', '#55403e'],
    terracotta: ['#9a9ca6', '#6d7080', '#a8aab4'],
    gold: ['#e3b65a', '#b3882f', '#efca78'],
    bronze: ['#a5834a', '#7a5f33', '#b5935a'],
    seat: ['#a8322d', '#76201f', '#bd453b'],
    pipe: ['#ddd1b4', '#ada083', '#e9dfc7'],
    screen: ['#fcf5e1', '#efe4c6', '#fff9ea'],
    lamp: ['#fff1c6', '#f3d585', '#fff7dd'],
    marble: ['#2c2729', '#1b1819', '#3c3538'],
    water: ['#5b9fae', '#41798a', '#78b7c4'],
    earth: ['#3a3230', '#3a3230', '#3a3230'],
  },
  poche: '#22181b',
  cutOutline: '#e6d3a8',
  route: '#d8392b',
}

export const PALETTES: Readonly<Record<string, Palette>> = { paper, night, winter }

/**
 * Accents for a cutaway sheet's margins (tools/cutaway/sheet.py, a spec's `theme`), never for
 * the drawing itself: a holiday sheet's deep red and evergreen green, for the title, the
 * section headings and a plain border rule.
 */
export const SHEET_THEMES: Readonly<Record<string, { readonly red: string; readonly green: string; readonly gold: string }>> = {
  holiday: { red: '#8f1d24', green: '#1f4a33', gold: '#a8812f' },
}

export const palette = (name = 'paper'): Palette => {
  const p = PALETTES[name]
  if (p === undefined) throw new Error(`unknown palette "${name}"; have ${Object.keys(PALETTES).join(', ')}`)
  return p
}

const hex = (c: string): [number, number, number] => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16)) as [number, number, number]

/** Linear mix of two #rrggbb colors. */
export const mix = (a: string, b: string, t: number): string => {
  const [ar, ag, ab] = hex(a)
  const [br, bg, bb] = hex(b)
  const c = (x: number, y: number) => Math.round(x + (y - x) * Math.min(1, Math.max(0, t))).toString(16).padStart(2, '0')
  return `#${c(ar, br)}${c(ag, bg)}${c(ab, bb)}`
}
