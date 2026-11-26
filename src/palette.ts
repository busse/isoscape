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
  /**
   * A story's pick-out (`Highlight` in history.ts): roofs inside its first polygon (`pick`) and
   * its later ones (`near`), every other roof (`quiet`), and the outlines, lost streets and
   * bridges it marks (`line`).
   */
  readonly mark: { readonly pick: string; readonly near: string; readonly quiet: string; readonly line: string }
  /**
   * Graded ground (`Tint` in history.ts): the tones in grade order (a 1937 HOLC map's A to D,
   * softened from its own green, blue, yellow and red), and the roads drawn over them. Mixed a
   * third of the way toward the paper so hillshade and buildings read through them (the owner's
   * choice, November 22, 2026), then nudged the least needed to pass the dataviz validator's
   * color-vision and normal-vision separation (paper: B darker and bluer, clear of the river; D
   * darker. night: A yellower, B and D more saturated). At this strength they sit outside its
   * lightness band and under its chroma floor, so grade identity is carried by the key's names
   * and the area labels on every picture, never by color alone.
   */
  readonly tint: { readonly tones: readonly string[]; readonly road: string }
  /**
   * A flood (experimental; flood.ts): the water over land by depth band (`FLOOD_BANDS`: under
   * 1 m, 1 to 3 m, 3 m and more), muddy and darker with depth so it reads apart from the river's
   * blue; the river's own channel on the flood's surface (`channel`); the waterline (`edge`); and
   * a floodwall's face and top.
   */
  readonly flood: FloodTones
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
  /** A cutaway's second way (`pumped`): what a works lifts, beside the route that drives it. */
  readonly pumped: string
  /**
   * A section's ways drawn as water (`section.ribbon`): the water that drives a works, and the
   * pale bands under both ways, the water that drives and the water pumped. Never the route's
   * red, which would read as warm water.
   */
  readonly drive: string
  readonly driveBand: string
  readonly pumpedBand: string
  /**
   * The water ways' marks in a section (`section.ribbon`), in section pixels: the paper edge
   * round each arrowhead, and an end tag's leader, its dot's radius and the dot's paper ring.
   */
  readonly wayMarks: { readonly arrowEdge: number; readonly leader: number; readonly dot: number; readonly ring: number }
  readonly routeWidth: number
  readonly routeDash: readonly [number, number]
  /** A light halo under the traveler's path and figures, where they cross red or dark ground. */
  readonly routeHalo?: string
  /**
   * The halo's widths: `edge`, how far it shows past each dash and arrowhead of the path;
   * `figure`, its stroke round a figure in the flat section; `plate`, round a figure on the plate.
   */
  readonly routeHaloWidth?: { readonly edge: number; readonly figure: number; readonly plate: number }
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
  mark: { pick: '#c4553b', near: '#e8a88f', quiet: '#ebe6db', line: '#8f2a22' },
  tint: { tones: ['#accf9c', '#71b1e1', '#dbc57e', '#db8981'], road: '#2c2b33' },
  flood: { tones: ['#c9b48c', '#ad9264', '#8a6f45'], channel: '#93b9cb', edge: '#5e4a2e', wall: '#a39c8f', wallTop: '#dcd6ca' },
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
    // Ground modeled as a part (a canal's bed under its water), cut in the section's earth color.
    earth: ['#cdbfa3', '#cdbfa3', '#d6c9ae'],
    redBrick: ['#c98c76', '#a46a57', '#b77d69'],
    granite: ['#a7a39c', '#85817a', '#b3afa8'],
    carpet: ['#9c2f2c', '#74211f', '#ab3a35'],
    damask: ['#d9b48a', '#b89068', '#e2c19b'],
    canvas: ['#f1ebdc', '#d6cebb', '#f6f1e5'],
    terracotta: ['#f1ece2', '#d4cdbf', '#ebe5d8'],
    gold: ['#d9b25e', '#b08a3e', '#e3c37a'],
    bronze: ['#a88a55', '#7c6439', '#b89a64'],
    seat: ['#a6403a', '#7a2c28', '#b8534a'],
    pipe: ['#d9d3c2', '#b3ab97', '#e5e0d2'],
    screen: ['#fbfaf5', '#ecebe4', '#ffffff'],
    lamp: ['#f6e7b8', '#e0c98a', '#fbf0cf'],
    marble: ['#3a3638', '#262325', '#4a4446'],
    land: ['#ebe5d6', '#ebe5d6', '#ebe5d6'],
  },
  poche: '#2c2b33',
  cutOutline: '#2c2b33',
  cutOutlineDash: [6, 4],
  route: '#b5392f',
  pumped: '#2f6690',
  drive: '#1f7a73',
  driveBand: '#9cc9c3',
  pumpedBand: '#a9c4dd',
  wayMarks: { arrowEdge: 1.2, leader: 2, dot: 5.5, ring: 2.5 },
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
  mark: { pick: '#e0614f', near: '#8a4a3e', quiet: '#2f3340', line: '#f07a5f' },
  tint: { tones: ['#445e32', '#005186', '#72642b', '#7a292f'], road: '#e8e4da' },
  flood: { tones: ['#5a4c36', '#4a3d2a', '#3a2f20'], channel: '#2c4a5c', edge: '#c9b48c', wall: '#6a6e7a', wallTop: '#8a8e98' },
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
    earth: ['#2b2f3b', '#2b2f3b', '#323746'],
    redBrick: ['#5b3a37', '#3d2727', '#4a3230'],
    granite: ['#4b4a4f', '#36353a', '#56555a'],
    carpet: ['#5e2322', '#421818', '#6a2a28'],
    damask: ['#7a6248', '#574532', '#86704f'],
    canvas: ['#8e8b84', '#67655f', '#9a978f'],
    terracotta: ['#8d8f98', '#62656f', '#9a9ca5'],
    gold: ['#8a7240', '#5e4d2c', '#9a8150'],
    bronze: ['#6a5838', '#4a3d27', '#776443'],
    seat: ['#6a2a28', '#4a1d1c', '#7a3330'],
    pipe: ['#6e6a62', '#4e4b45', '#7a766d'],
    screen: ['#d8d6cf', '#b8b6af', '#e2e0da'],
    lamp: ['#e8d49a', '#c9b273', '#f0dfae'],
    marble: ['#2a2628', '#1a1718', '#3a3437'],
    land: ['#1d2029', '#1d2029', '#1d2029'],
  },
  poche: '#c9d1e6',
  cutOutline: '#c9d1e6',
  route: '#e0614f',
  pumped: '#7fb6e0',
  drive: '#5fbfb4',
  driveBand: '#2a5652',
  pumpedBand: '#2b4a66',
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
    redBrick: ['#6a423c', '#47302c', '#55403e'],
    granite: ['#8f8c92', '#6c6a71', '#9d9aa0'],
    carpet: ['#8e2328', '#62171b', '#a02d31'],
    damask: ['#d9a878', '#b38253', '#e4b98c'],
    canvas: ['#efe6d2', '#cfc3a8', '#f5eedf'],
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
    land: ['#1f2636', '#1f2636', '#1f2636'],
  },
  poche: '#22181b',
  cutOutline: '#e6d3a8',
  route: '#d8392b',
  routeHalo: '#f6ead0',
  routeHaloWidth: { edge: 1.82, figure: 3.64, plate: 2.34 },
}

export const PALETTES: Readonly<Record<string, Palette>> = { paper, night, winter }

/** A flood's colors (experimental; see `Palette.flood`), and the optional looks tried on them. */
export interface FloodTones {
  readonly tones: readonly string[]
  readonly channel: string
  readonly edge: string
  readonly wall: string
  readonly wallTop: string
  /** Depth bands, true meters, one per tone (default `FLOOD_BANDS` in flood.ts). */
  readonly bands?: readonly number[]
  /** Short strokes on the water's surface, thicker where it is deeper. */
  readonly ripple?: string
  /** A line along a floodwall's top, and its width in pixels. */
  readonly wallLine?: string
  readonly wallLineWidth?: number
  /** Half the floodwall's drawn thickness, meters (default `WALL_HALF` in scene.ts). */
  readonly wallHalf?: number
  /** A pale casing under the wall's top line, 1.9 times as wide as its line. */
  readonly wallCasing?: string
  /** The wall's openings: a shut closure's face, and an open one's dashed line. */
  readonly gate?: string
  /** The waterline's width, as a share of the ink line (default 1.2). */
  readonly edgeWidth?: number
  /** A soft pool (`soft`): its tones and depth bands, fading from the land into the water. */
  readonly softTones?: readonly string[]
  readonly softBands?: readonly number[]
  /** The range of an estimate (`uncertainty`): its band on the ground, and the band's outer line. */
  readonly band?: string
  readonly bandEdge?: string
  /** The range band hatched in this color over `band`, rather than flat. */
  readonly bandHatch?: string
  /**
   * Ground whose protection is not known (a flood's `unknown`): a cross-hatch of `unknownHatch`
   * over `unknown`, apart from the range band's single hatch in the flood's hue.
   */
  readonly unknown?: string
  readonly unknownHatch?: string
  /** See-through water: the flood's opacity (0 to 1); walls in it reach the ground, tinted below the surface. */
  readonly aquarium?: number
  /** X-ray walls: the part of a wall under the water drawn over it ("band", or "fade" toward its foot); `xrayLine` the waterline's width. */
  readonly xray?: 'band' | 'fade'
  readonly xrayLine?: number
  /** A tide mark: on a wall standing in water, a band as tall as the depth above the surface (a convention). */
  readonly tideMark?: boolean
  /** Streets under the water, drawn on its surface in this color at about half strength. */
  readonly streets?: string
  /** In a flood build, dry ground drawn in this color instead of the palette's `land` (knocked back). */
  readonly land?: string
  /**
   * Buildings drawn as unconfirmed (a series' evidence layer: standing on an earlier source, not
   * ascertained for the scene's year): every face and roof taken `share` of the way toward
   * `tone`, inked with the finer line. Default `UNCONFIRMED`.
   */
  readonly unconfirmed?: UnconfirmedLook
}

/**
 * How a building drawn as unconfirmed looks: every face and roof taken `share` of the way to
 * `tone`; optionally the roof taken further (`roofShare` toward `roofTone`), and a dashed line
 * around the roof (`outline`, pixels at the build's scale).
 */
export interface UnconfirmedLook {
  readonly tone: string
  readonly share: number
  readonly roofTone?: string
  readonly roofShare?: number
  readonly outline?: { readonly color: string; readonly width: number; readonly dash: readonly [number, number] }
}

/** The unconfirmed look when a palette's flood looks set none: pale, toward the paper. */
export const UNCONFIRMED: UnconfirmedLook = { tone: '#f6f1e6', share: 0.6 }

/**
 * Looks tried for a flood (`--flood-style`, experimental), laid over a palette's own flood
 * colors. Rough looks for the owner to choose from (November 23, 2026); none is the default.
 */
/** Depth bands for the fine looks, true meters. */
export const FINE_BANDS: readonly number[] = [0, 0.3, 0.6, 1, 1.5, 2, 3, 4, 6]

/** `n` tones from `a` to `b`, eased so the shallow end changes fastest. */
function ramp(a: string, b: string, n: number): string[] {
  const rgb = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
  const [x, y] = [rgb(a), rgb(b)]
  return Array.from({ length: n }, (_, k) => {
    const t = Math.sqrt(k / (n - 1))
    return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join('')
  })
}

export const FLOOD_STYLES: Readonly<Record<string, Partial<FloodTones>>> = {
  // Lighter silt, five bands, so depth reads as a gradient.
  silt: { tones: ['#e4d8ba', '#d4c29d', '#c1ab7f', '#aa9164', '#8f764b'], bands: [0, 0.5, 1, 2, 3] },
  // The present muddy tones with ripple strokes on the surface.
  ripple: { ripple: '#efe5cf' },
  // A tinted blue-brown, nearer water than mud, still apart from the river's blue.
  murk: { tones: ['#bcc3ad', '#9ba893', '#7b8b77'], channel: '#8fb6c9', edge: '#4c5a4a' },
  // The floodwall as a subject: dark face, a pale top and an ink line along it, thicker.
  'wall-bold': { wall: '#525866', wallTop: '#f3eee2', wallLine: '#2c2b33', wallLineWidth: 1.4, wallHalf: 1.25 },
  // Round two (d1): lighter, siltier water, depth carried by nine fine bands (FINE_BANDS) from a
  // pale edge to a darker deep, a pale clean waterline, and the river's channel kept apart.
  'pale-silt': {
    tones: ramp('#ede7d7', '#a4937a', 9), bands: FINE_BANDS, channel: '#8db3c6', edge: '#fbf8f0', edgeWidth: 2.2,
    // A soft pool fades in from nearly the land's own color; the range of an estimate is a pale
    // grey-blue on the ground with a dashed edge.
    softTones: ramp('#e6dfcc', '#a4937a', 8), softBands: [0, 0.15, 0.3, 0.5, 0.8, 1.2, 2, 3],
    band: '#dcdcd2', bandEdge: '#7d7564',
  },
  // The same with pale glints on the surface, as floodwater looks from above.
  'silt-sheen': { tones: ramp('#ede7d7', '#a4937a', 9), bands: FINE_BANDS, channel: '#8db3c6', edge: '#fbf8f0', edgeWidth: 2.2, ripple: '#fcfaf3' },
  // Blue for depth under a silt tint: pale silt at the edge to a grey-blue deep; the channel a deeper blue.
  'blue-silt': { tones: ramp('#e8e4d4', '#6f8a99', 9), bands: FINE_BANDS, channel: '#56798d', edge: '#fbf8f0', edgeWidth: 2.2 },
  // Neutral grey-tan, cooler than mud.
  'grey-tan': { tones: ramp('#e9e6dc', '#958e7e', 9), bands: FINE_BANDS, channel: '#8db3c6', edge: '#fbf8f0', edgeWidth: 2.2 },
  // A warm ochre wash, the old muddy look made light.
  'ochre-wash': { tones: ramp('#f0e5c8', '#a68a58', 9), bands: FINE_BANDS, channel: '#8db3c6', edge: '#fbf8f0', edgeWidth: 2.2 },
  // The wall, round two: a casing (pale halo under a dark line) along its top, a darker face,
  // and its openings marked (a shut closure in a rust tone; an open one dashed).
  'wall-cased': { wall: '#7d8290', wallTop: '#f3eee2', wallCasing: '#fbf8f0', wallLine: '#2c2b33', wallLineWidth: 1.6, wallHalf: 1.0, gate: '#a5533f' },
  // The casing with the brick-red line: reads at full view and still says "wall", not "border".
  'wall-cased-red': { wall: '#7d8290', wallTop: '#f3eee2', wallCasing: '#fbf8f0', wallLine: '#9b3a2c', wallLineWidth: 3.6, wallHalf: 1.0, gate: '#2c2b33' },
  // Round three (d1r2, the owner: "not enough contrast"): each at least 20 L* darker than the
  // ground at its edge, with a dark inked waterline and the range hatched in the flood's hue.
  umber: { tones: ramp('#a89577', '#4f3f2c', 9), bands: FINE_BANDS, channel: '#8fb8cc', edge: '#2c2418', edgeWidth: 1.6, softTones: ramp('#c8b89a', '#4f3f2c', 8), band: '#efe7d4', bandHatch: '#8d7a5c', bandEdge: '#2c2418' },
  'green-brown': { tones: ramp('#a3a07a', '#55532f', 9), bands: FINE_BANDS, channel: '#8fb8cc', edge: '#2b2a17', edgeWidth: 1.6, softTones: ramp('#c4c19d', '#55532f', 8), band: '#ecebd6', bandHatch: '#88855f', bandEdge: '#2b2a17' },
  'blue-grey': { streets: '#c9d6de', tones: ramp('#8ea5b4', '#3c5466', 9), bands: FINE_BANDS, channel: '#a6dcf2', edge: '#1f2d38', edgeWidth: 1.6, softTones: ramp('#b4c4ce', '#3c5466', 8), band: '#e6ecee', bandHatch: '#6f8796', bandEdge: '#1f2d38', unknown: '#ebe4d6', unknownHatch: '#8c7a62' },
  ochre: { tones: ramp('#c9a25a', '#7d5420', 9), bands: FINE_BANDS, channel: '#8fb8cc', edge: '#3d2a10', edgeWidth: 1.8, softTones: ramp('#dcc28c', '#7d5420', 8), band: '#f3e6c6', bandHatch: '#b58a45', bandEdge: '#3d2a10' },
  // The same water against dry ground knocked back a step paler and cooler.
  knockback: { tones: ramp('#bfae8d', '#6b5a43', 9), bands: FINE_BANDS, channel: '#8fb8cc', edge: '#3a2f20', edgeWidth: 1.6, land: '#f6f5f1', softTones: ramp('#d5c8ad', '#6b5a43', 8), band: '#f3eee2', bandHatch: '#a29070', bandEdge: '#3a2f20' },
  // Round four (d1r3): showing the water's height on the buildings. See-through water at two
  // opacities (walls reach the ground, tinted below the surface), and a tide mark (a convention).
  'aquarium-70': { aquarium: 0.7, streets: undefined },
  'aquarium-50': { aquarium: 0.5, streets: undefined },
  // The pick: nearly as dark as the opaque water the owner chose, still seen through at the walls.
  'aquarium-85': { aquarium: 0.85, streets: undefined },
  'tide-mark': { tideMark: true },
  // Round five (d1r4): x-ray walls over opaque water.
  xray: { xray: 'band' },
  'xray-fade': { xray: 'fade' },
  'xray-heavy': { xray: 'band', xrayLine: 2.4 },
  // The period city (d2): unconfirmed buildings, tried at four strengths; `unconfirmed-slate` is the pick (the pale ones do not part from the cream walls).
  'unconfirmed-pale': { unconfirmed: { tone: '#f6f1e6', share: 0.6 } },
  'unconfirmed-ghost': { unconfirmed: { tone: '#f6f1e6', share: 0.78 } },
  // Cool grey, apart from the paper and from every roof tone: reads as "not this year's" at plate view.
  'unconfirmed-grey': { unconfirmed: { tone: '#c3c9cf', share: 0.72 } },
  'unconfirmed-slate': { unconfirmed: { tone: '#9fa9b3', share: 0.6 } },
  // d3 (the owner, 12:18: slate kept, with one more cue that holds at plate size): the slate
  // with a dashed ink line round the roof, with a darker slate roof, or with both.
  'unconfirmed-slate-dash': { unconfirmed: { tone: '#9fa9b3', share: 0.6, outline: { color: '#2c2b33', width: 1.1, dash: [2.2, 1.6] } } },
  'unconfirmed-slate-roof': { unconfirmed: { tone: '#9fa9b3', share: 0.6, roofTone: '#6b7480', roofShare: 0.75 } },
  'unconfirmed-slate-both': { unconfirmed: { tone: '#9fa9b3', share: 0.6, roofTone: '#6b7480', roofShare: 0.75, outline: { color: '#f6f1e6', width: 1.1, dash: [2.2, 1.6] } } },
  // Stronger still: a distinct brick-red line along the top, wide enough to carry the full view.
  'wall-strong': { wall: '#525866', wallTop: '#f3eee2', wallLine: '#9b3a2c', wallLineWidth: 4, wallHalf: 1.25 },
}

/** A palette with flood looks laid over its flood colors, in order. */
export const withFloodStyles = (p: Palette, names: readonly string[]): Palette => {
  let flood: FloodTones = p.flood
  for (const n of names) {
    const s = FLOOD_STYLES[n]
    if (s === undefined) throw new Error(`no flood style "${n}" (have: ${Object.keys(FLOOD_STYLES).join(', ')})`)
    flood = { ...flood, ...s }
  }
  return { ...p, flood, ...(flood.land === undefined ? {} : { land: flood.land }) }
}

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
