/**
 * Just enough PNG: 8-bit, non-interlaced, palette (type 3), gray (0), RGB (2) or RGBA (6).
 * Enough to read a WMS map image without a dependency.
 */

import { inflateSync } from 'node:zlib'

export interface Png {
  readonly width: number
  readonly height: number
  /** One entry per pixel: [r, g, b]. */
  readonly rgb: (x: number, y: number) => readonly [number, number, number]
}

export const decodePng = (buf: Buffer): Png => {
  if (buf.readUInt32BE(0) !== 0x89504e47) throw new Error('not a PNG')
  let width = 0
  let height = 0
  let depth = 0
  let type = 0
  let interlace = 0
  let palette: Buffer | null = null
  const data: Buffer[] = []
  for (let i = 8; i < buf.length; ) {
    const len = buf.readUInt32BE(i)
    const kind = buf.toString('latin1', i + 4, i + 8)
    const body = buf.subarray(i + 8, i + 8 + len)
    if (kind === 'IHDR') {
      width = body.readUInt32BE(0)
      height = body.readUInt32BE(4)
      depth = body[8]
      type = body[9]
      interlace = body[12]
    } else if (kind === 'PLTE') palette = Buffer.from(body)
    else if (kind === 'IDAT') data.push(body)
    else if (kind === 'IEND') break
    i += 12 + len
  }
  if (depth !== 8 || interlace !== 0) throw new Error(`unsupported PNG: depth ${depth}, interlace ${interlace}`)
  const channels = type === 3 || type === 0 ? 1 : type === 2 ? 3 : type === 6 ? 4 : 0
  if (channels === 0) throw new Error(`unsupported PNG color type ${type}`)
  if (type === 3 && palette === null) throw new Error('palette PNG without a palette')
  const raw = inflateSync(Buffer.concat(data))
  const stride = width * channels
  const px = Buffer.alloc(height * stride)
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)]
    const src = y * (stride + 1) + 1
    const out = y * stride
    for (let x = 0; x < stride; x++) {
      const a = x >= channels ? px[out + x - channels] : 0
      const b = y > 0 ? px[out - stride + x] : 0
      const c = x >= channels && y > 0 ? px[out - stride + x - channels] : 0
      let v = raw[src + x]
      switch (filter) {
        case 1: v += a; break
        case 2: v += b; break
        case 3: v += (a + b) >> 1; break
        case 4: {
          const p = a + b - c
          const pa = Math.abs(p - a)
          const pb = Math.abs(p - b)
          const pc = Math.abs(p - c)
          v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c
          break
        }
        default: break
      }
      px[out + x] = v & 0xff
    }
  }
  return {
    width,
    height,
    rgb: (x, y) => {
      const k = y * stride + x * channels
      if (type === 3) {
        const p = px[k] * 3
        return [palette![p], palette![p + 1], palette![p + 2]]
      }
      if (type === 0) return [px[k], px[k], px[k]]
      return [px[k], px[k + 1], px[k + 2]]
    },
  }
}
