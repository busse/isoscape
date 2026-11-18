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
   * Main Street Station's buff brick and red clay tile, the painted steel of its train shed, the
   * ballast of its elevated tracks, and a diesel engine in a plain mid grey, light enough for
   * its edges to show. The Chesapeake and Ohio's passenger cars of the early 1950s: blue, a
   * yellow band along the top of the side, gray below the windows, a dark roof.
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
  /** The ink of a part drawn with `ink: "fine"` (small repeated work, a row of dormers). */
  readonly fineLineWidth: number
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
    // The dome as it was before its copper of 1955: red-brown terra-cotta tile (set views; the
    // cutaway, already sold, keeps `dome`).
    tile: ['#c08466', '#8e5a43', '#cc9276'],
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
    brick: ['#e2c99c', '#b89d72', '#d6bd92'],
    // Main Street Station's red tile roofs, dormers and tower dome in its own cutaway.
    roofTile: ['#b46049', '#844232', '#a9553f'],
    steel: ['#7d7f86', '#5c5e65', '#8e9096'],
    ballast: ['#b5aa90', '#948a72', '#aca186'],
    diesel: ['#9a9da1', '#7b7e83', '#8a8d92'],
    coachBlue: ['#2f4f7a', '#213a5c', '#3a3b3a'],
    coachBand: ['#e2b93b', '#b8932a', '#c9a433'],
    coachSkirt: ['#a9adb1', '#868a8f', '#9a9ea3'],
    coachRoof: ['#4a4b4f', '#36373a', '#4f5054'],
    // Water held in a modeled work (a forebay, a wheel pit), drawn as a solid at its level.
    water: ['#a8cad8', '#8fb3c4', '#b4d3df'],
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
  fineLineWidth: 0.35,
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
    tile: ['#7a4f3d', '#553628', '#865844'],
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
    brick: ['#5c5040', '#40382d', '#544a3c'],
    roofTile: ['#6a3a2e', '#4a2820', '#5e3428'],
    steel: ['#2c2d33', '#1d1e23', '#34353b'],
    ballast: ['#4a4840', '#38362f', '#43413a'],
    diesel: ['#34363b', '#232428', '#2d2f33'],
    coachBlue: ['#22385a', '#172843', '#26282b'],
    coachBand: ['#8f7628', '#6c591e', '#7d6723'],
    coachSkirt: ['#4a4d52', '#36393d', '#414448'],
    coachRoof: ['#2a2b2e', '#1d1e20', '#2e2f32'],
    water: ['#1b2e3b', '#16252f', '#223847'],
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

export const PALETTES: Readonly<Record<string, Palette>> = { paper, night }

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
