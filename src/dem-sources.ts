/**
 * Where elevation comes from. Every source ends in the same thing: a grid of metres above sea
 * level on the region's lon/lat box (see `fetchDem` in `dem.ts`), so nothing downstream knows
 * or cares which one was used. They differ in how they hand the heights over:
 *
 * - **request** sources cut an image to order for any box (USGS 3DEP, IGN). The grid is
 *   fetched in tiles that line up with the output exactly.
 * - **mosaic** sources publish fixed pieces: map tiles in Web Mercator (GSI, AWS Terrain
 *   Tiles), one-degree squares (Copernicus) or one-kilometre squares in the Swiss grid
 *   (swisstopo). The pieces covering the box are downloaded, then the output grid is sampled
 *   from them, reprojecting each sample to the piece's own coordinates.
 *
 * All five non-US sources allow commercial use with attribution; `credit` is the line the
 * maps and pages carry, and `licence` names the terms.
 */

import { bilinear, decodeTiff, type Raster } from './rasters.ts'
import { decodePng } from './png.ts'
import type { Bounds } from './osm.ts'

export type DemSourceId = '3dep' | 'ign' | 'swisstopo' | 'gsi' | 'copernicus' | 'terrain-tiles'

export interface Piece {
  readonly url: string
  /** File name under the region's download folder. */
  readonly file: string
  /** Free-form per-piece facts the sampler needs (tile x/y/z, layer, grid square). */
  readonly key: Record<string, number | string>
}

interface Common {
  readonly id: DemSourceId
  /** Short name for credits and the explorer, e.g. "IGN RGE ALTI". */
  readonly name: string
  /** Who publishes it and where it covers. */
  readonly coverage: string
  /** One sentence on what the heights are (bare earth or surface, how measured, native spacing). */
  readonly about: string
  /** The attribution line every map using it must carry. */
  readonly credit: string
  readonly licence: string
  readonly link: string
  /** Finest useful metres per pixel; finer `demResolution` just interpolates. */
  readonly native: number
}

export interface RequestSource extends Common {
  readonly kind: 'request'
  readonly url: (b: Bounds, width: number, height: number) => string
  /** Largest tile the service reliably answers, in pixels a side. */
  readonly tile: number
  readonly decode: (buf: Buffer, b: Bounds, width: number, height: number) => Float32Array
}

export interface MosaicSource extends Common {
  readonly kind: 'mosaic'
  /** The pieces covering `b` at about `metresPerPixel`. May ask a catalogue first. */
  readonly pieces: (b: Bounds, metresPerPixel: number, get: (url: string) => Promise<string>) => Promise<Piece[]>
  /** Build a lon/lat → metres sampler from the downloaded pieces (`null` where a piece is missing). */
  readonly sampler: (pieces: { piece: Piece; buf: Buffer | null }[]) => (lon: number, lat: number) => number
}

export type DemSource = RequestSource | MosaicSource

// ------------------------------------------------------------------------- shared helpers

/** Web Mercator: lon/lat → global pixel at zoom z (256-px tiles). */
export const mercatorPixel = (lon: number, lat: number, z: number): [number, number] => {
  const n = 256 * 2 ** z
  const s = Math.sin((lat * Math.PI) / 180)
  return [((lon + 180) / 360) * n, (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * n]
}

/** Every z/x/y tile touching `b`. */
const tilesOver = (b: Bounds, z: number) => {
  const [x0, y0] = mercatorPixel(b.west, b.north, z).map((v) => Math.floor(v / 256))
  const [x1, y1] = mercatorPixel(b.east, b.south, z).map((v) => Math.floor(v / 256))
  const out: { x: number; y: number }[] = []
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) out.push({ x, y })
  return out
}

/** Sample a set of same-zoom map tiles, each already decoded to metres, as one surface. */
const tileSampler = (z: number, tiles: Map<string, Raster>) => (lon: number, lat: number): number => {
  const [px, py] = mercatorPixel(lon, lat, z)
  const tx = Math.floor(px / 256)
  const ty = Math.floor(py / 256)
  const t = tiles.get(`${tx}/${ty}`)
  if (t === undefined) return NaN
  return bilinear(t, px - tx * 256 - 0.5, py - ty * 256 - 0.5)
}

const pngHeights = (buf: Buffer, unpack: (r: number, g: number, b: number) => number): Raster => {
  const png = decodePng(buf)
  const data = new Float32Array(png.width * png.height)
  for (let y = 0; y < png.height; y++) for (let x = 0; x < png.width; x++) data[y * png.width + x] = unpack(...png.rgb(x, y))
  return { width: png.width, height: png.height, data }
}

/** Zoom whose pixels are no bigger than `m` metres at latitude `lat`, capped at `max`. */
const zoomFor = (m: number, lat: number, max: number) =>
  Math.min(max, Math.max(0, Math.ceil(Math.log2((156_543.034 * Math.cos((lat * Math.PI) / 180)) / m))))

/**
 * WGS84 → Swiss LV95 (EPSG:2056), swisstopo's published approximation (good to about a metre,
 * well under one 2 m pixel).
 */
export const toLv95 = (lon: number, lat: number): [number, number] => {
  const p = (lat * 3600 - 169_028.66) / 10_000
  const l = (lon * 3600 - 26_782.5) / 10_000
  const e = 2_600_072.37 + 211_455.93 * l - 10_938.51 * l * p - 0.36 * l * p * p - 44.54 * l ** 3
  const n = 1_200_147.07 + 308_807.95 * p + 3_745.25 * l * l + 76.63 * p * p - 194.56 * l * l * p + 119.79 * p ** 3
  return [e, n]
}

/** Sample a georeferenced raster at (x, y) in its own CRS. */
const sampleGeo = (r: Raster, x: number, y: number) =>
  r.geo === undefined ? NaN : bilinear(r, (x - r.geo.x0) / r.geo.dx - 0.5, (r.geo.y0 - y) / r.geo.dy - 0.5)

// ---------------------------------------------------------------------------------- sources

const usgs3dep: RequestSource = {
  id: '3dep',
  kind: 'request',
  name: 'USGS 3DEP',
  coverage: 'United States (U.S. Geological Survey)',
  about: 'Bare-earth lidar, 1 m across most of the US, served by the National Map',
  credit: 'Elevation: USGS 3DEP',
  licence: 'public domain',
  link: 'https://www.usgs.gov/3d-elevation-program',
  native: 1,
  tile: 1500,
  url: (b, width, height) =>
    'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?' +
    new URLSearchParams({
      bbox: [b.west, b.south, b.east, b.north].map((n) => n.toFixed(7)).join(','),
      bboxSR: '4326',
      imageSR: '4326',
      size: `${width},${height}`,
      format: 'tiff',
      pixelType: 'F32',
      noData: '-9999',
      noDataInterpretation: 'esriNoDataMatchAny',
      interpolation: 'RSP_BilinearInterpolation',
      compression: 'None',
      f: 'image',
    }),
  decode: (buf) => decodeTiff(buf).data,
}

const ign: RequestSource = {
  id: 'ign',
  kind: 'request',
  name: 'IGN RGE ALTI',
  coverage: 'France (Institut national de l’information géographique et forestière)',
  about: 'Bare-earth model at 1 m, from airborne lidar in cities, along coasts and in forests, and image correlation elsewhere',
  credit: 'Elevation: RGE ALTI® © IGN',
  licence: 'Licence Ouverte 2.0 (Etalab)',
  link: 'https://geoservices.ign.fr/rgealti',
  native: 1,
  tile: 2000,
  // WMS 1.3.0 with EPSG:4326 takes the box as lat,lon. The BIL answer is raw little-endian
  // float32, row 0 at the north edge.
  url: (b, width, height) =>
    'https://data.geopf.fr/wms-r?' +
    new URLSearchParams({
      SERVICE: 'WMS',
      VERSION: '1.3.0',
      REQUEST: 'GetMap',
      LAYERS: 'ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES',
      STYLES: '',
      CRS: 'EPSG:4326',
      BBOX: [b.south, b.west, b.north, b.east].map((n) => n.toFixed(7)).join(','),
      WIDTH: String(width),
      HEIGHT: String(height),
      FORMAT: 'image/x-bil;bits=32',
    }),
  decode: (buf, _b, width, height) => {
    if (buf.length !== width * height * 4) throw new Error(`IGN answered ${buf.length} bytes, expected ${width * height * 4}: ${buf.toString('utf8', 0, 200)}`)
    const out = new Float32Array(width * height)
    for (let i = 0; i < out.length; i++) {
      const v = buf.readFloatLE(i * 4)
      out[i] = v <= -1000 ? NaN : v
    }
    return out
  },
}

const GSI_LAYERS = [
  { layer: 'dem5a_png', z: 15 }, // 5 m, airborne lidar
  { layer: 'dem5b_png', z: 15 }, // 5 m, photogrammetry
  { layer: 'dem_png', z: 14 }, // 10 m, from the 1:25,000 map's contours; covers all of Japan
] as const

const gsi: MosaicSource = {
  id: 'gsi',
  kind: 'mosaic',
  name: 'GSI elevation tiles',
  coverage: 'Japan (Geospatial Information Authority of Japan, 国土地理院)',
  about: 'Bare-earth 5 m lidar where it has been flown, filled from the 10 m national model elsewhere',
  credit: 'Elevation: 地理院タイル (標高タイル) を加工して作成 — GSI elevation tiles, processed',
  licence: 'GSI content terms (国土地理院コンテンツ利用規約), compatible with CC BY 4.0',
  link: 'https://maps.gsi.go.jp/development/ichiran.html',
  native: 5,
  pieces: async (b) =>
    GSI_LAYERS.flatMap(({ layer, z }) =>
      tilesOver(b, z).map(({ x, y }) => ({
        url: `https://cyberjapandata.gsi.go.jp/xyz/${layer}/${z}/${x}/${y}.png`,
        file: `${layer}-${z}-${x}-${y}.png`,
        key: { layer, z, x, y },
      })),
    ),
  sampler: (got) => {
    // x = R·2¹⁶ + G·2⁸ + B in hundredths of a metre, two's complement in 24 bits; 2²³ is "no data".
    const unpack = (r: number, g: number, b: number) => {
      const x = r * 65_536 + g * 256 + b
      return x === 8_388_608 ? NaN : (x < 8_388_608 ? x : x - 16_777_216) * 0.01
    }
    const layers = GSI_LAYERS.map(({ layer, z }) => {
      const tiles = new Map<string, Raster>()
      for (const { piece, buf } of got) if (piece.key.layer === layer && buf !== null) tiles.set(`${piece.key.x}/${piece.key.y}`, pngHeights(buf, unpack))
      return tileSampler(z, tiles)
    })
    return (lon, lat) => {
      for (const s of layers) {
        const v = s(lon, lat)
        if (!Number.isNaN(v)) return v
      }
      return NaN
    }
  },
}

const terrainTiles: MosaicSource = {
  id: 'terrain-tiles',
  kind: 'mosaic',
  name: 'Terrain Tiles',
  coverage: 'Worldwide (Mapzen/Tilezen, on AWS Open Data), the best open source per country',
  about: 'A mosaic of national bare-earth models; in Australia, Geoscience Australia’s 5 m lidar DEM where flown, SRTM elsewhere',
  credit: 'Elevation: Terrain Tiles (Mapzen/Tilezen, AWS Open Data); Australia terrain data © Commonwealth of Australia (Geoscience Australia) 2017',
  licence: 'per source; see the Tilezen attribution list (Geoscience Australia: CC BY 4.0)',
  link: 'https://registry.opendata.aws/terrain-tiles/',
  native: 5,
  pieces: async (b, m) => {
    const z = zoomFor(m, (b.north + b.south) / 2, 15)
    return tilesOver(b, z).map(({ x, y }) => ({
      url: `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/${z}/${x}/${y}.png`,
      file: `terrarium-${z}-${x}-${y}.png`,
      key: { z, x, y },
    }))
  },
  sampler: (got) => {
    const z = Number(got[0]?.piece.key.z ?? 0)
    const tiles = new Map<string, Raster>()
    // Terrarium: metres = R·256 + G + B/256 − 32768.
    for (const { piece, buf } of got) if (buf !== null) tiles.set(`${piece.key.x}/${piece.key.y}`, pngHeights(buf, (r, g, b) => r * 256 + g + b / 256 - 32_768))
    return tileSampler(z, tiles)
  },
}

const copernicus: MosaicSource = {
  id: 'copernicus',
  kind: 'mosaic',
  name: 'Copernicus DEM GLO-30',
  coverage: 'Worldwide (European Space Agency, Copernicus programme)',
  about: 'A 30 m surface model from the TanDEM-X radar mission: it includes forest canopy and buildings, so it suits mountains better than cities',
  credit: 'Elevation: produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved',
  licence: 'Licence for the use of the Copernicus WorldDEM-30 (free, worldwide, commercial use allowed)',
  link: 'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM',
  native: 30,
  pieces: async (b) => {
    const out: Piece[] = []
    for (let lat = Math.floor(b.south); lat <= Math.floor(b.north); lat++) {
      for (let lon = Math.floor(b.west); lon <= Math.floor(b.east); lon++) {
        const ns = `${lat < 0 ? 'S' : 'N'}${String(Math.abs(lat)).padStart(2, '0')}_00`
        const ew = `${lon < 0 ? 'W' : 'E'}${String(Math.abs(lon)).padStart(3, '0')}_00`
        const name = `Copernicus_DSM_COG_10_${ns}_${ew}_DEM`
        out.push({ url: `https://copernicus-dem-30m.s3.amazonaws.com/${name}/${name}.tif`, file: `${name}.tif`, key: { lat, lon } })
      }
    }
    return out
  },
  sampler: (got) => {
    const squares = new Map<string, Raster>()
    for (const { piece, buf } of got) if (buf !== null) squares.set(`${piece.key.lat}/${piece.key.lon}`, decodeTiff(buf))
    return (lon, lat) => {
      const r = squares.get(`${Math.floor(lat)}/${Math.floor(lon)}`)
      return r === undefined ? NaN : sampleGeo(r, lon, lat)
    }
  },
}

const swisstopo: MosaicSource = {
  id: 'swisstopo',
  kind: 'mosaic',
  name: 'swisstopo swissALTI3D',
  coverage: 'Switzerland and Liechtenstein (Federal Office of Topography swisstopo)',
  about: 'Bare-earth lidar model, published as 1 km squares at 2 m in the Swiss grid (LV95) and refreshed on a six-year cycle',
  credit: 'Elevation: swissALTI3D © Federal Office of Topography swisstopo',
  licence: 'swisstopo terms of use for free geodata (OGD): free use, commercial included, with source attribution',
  link: 'https://www.swisstopo.admin.ch/en/height-model-swissalti3d',
  native: 2,
  pieces: async (b, _m, get) => {
    // The STAC catalogue lists every published square; keep the newest year of each.
    const newest = new Map<string, { year: number; url: string }>()
    let next: string | undefined =
      `https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d/items?bbox=${[b.west, b.south, b.east, b.north].join(',')}&limit=100`
    while (next !== undefined) {
      const page = JSON.parse(await get(next)) as {
        features: { id: string; assets: Record<string, { href: string; 'eo:gsd'?: number }> }[]
        links?: { rel: string; href: string }[]
      }
      for (const f of page.features) {
        const m = /_(\d{4})_(\d{4}-\d{4})$/.exec(f.id)
        const asset = Object.values(f.assets).find((a) => a.href.endsWith('.tif') && a['eo:gsd'] === 2)
        if (m === null || asset === undefined) continue
        const year = Number(m[1])
        if ((newest.get(m[2])?.year ?? 0) < year) newest.set(m[2], { year, url: asset.href })
      }
      next = page.links?.find((l) => l.rel === 'next')?.href
    }
    return [...newest].map(([square, { url }]) => ({ url, file: url.split('/').pop()!, key: { square } }))
  },
  sampler: (got) => {
    const squares = new Map<string, Raster>()
    for (const { piece, buf } of got) if (buf !== null) squares.set(String(piece.key.square), decodeTiff(buf))
    return (lon, lat) => {
      const [e, n] = toLv95(lon, lat)
      const r = squares.get(`${Math.floor(e / 1000)}-${Math.floor(n / 1000)}`)
      return r === undefined ? NaN : sampleGeo(r, e, n)
    }
  },
}

export const DEM_SOURCES: Record<DemSourceId, DemSource> = {
  '3dep': usgs3dep,
  ign,
  swisstopo,
  gsi,
  copernicus,
  'terrain-tiles': terrainTiles,
}

export const demSource = (id: string | undefined): DemSource => {
  const s = DEM_SOURCES[(id ?? '3dep') as DemSourceId]
  if (s === undefined) throw new Error(`unknown elevation source "${id}"; one of ${Object.keys(DEM_SOURCES).join(', ')}`)
  return s
}
