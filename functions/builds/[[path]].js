// Cloudflare Pages Function: a build file too big for Pages (over 25 MiB), served from the R2
// bucket bound as MAPS (misfit-isoscape-maps) at the same address it has on the site. Only the
// paths that _routes.json lists reach this function; every other file is a static asset.
// See tools/site/cloudflare.py and the README, "Publishing the site".
export async function onRequest({ request, params, env }) {
  if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method not allowed', { status: 405, headers: { allow: 'GET, HEAD' } })
  const key = 'builds/' + [].concat(params.path || []).join('/')
  const obj = await env.MAPS.get(key, { onlyIf: request.headers, range: request.headers })
  if (obj === null) return new Response('Not found', { status: 404 })
  const headers = new Headers()
  obj.writeHttpMetadata(headers)
  headers.set('etag', obj.httpEtag)
  if (key.endsWith('.svg')) headers.set('content-type', 'image/svg+xml')
  // Build folders never change once written (a rebuild is a new id), so browsers may keep them.
  headers.set('cache-control', 'public, max-age=31536000, immutable')
  if (!('body' in obj) || obj.body === undefined) return new Response(null, { status: 304, headers })
  return new Response(request.method === 'HEAD' ? null : obj.body, { status: obj.range ? 206 : 200, headers })
}
