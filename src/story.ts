// @ts-nocheck: this function also runs in the browser (see below), so it is written as plain JavaScript.
/**
 * "How this view was made": a build's own story, written from its meta.json, in sentences. The
 * same code runs in two places. The explorer embeds its source (`makeStory.toString()`; Node
 * strips the type annotations before the code is loaded, so the source is plain JavaScript) and
 * calls it in the "How this view was made" tab; the static map pages (static-pages.ts) call it in
 * Node at generation time. So it may use nothing but its arguments and the language itself: no
 * imports, no closures over this module, no template literals.
 *
 * `ctx.pageHref(slug, section)` is where a link to a content page goes (an explorer route, or a
 * static page), or null when there is no such page; `when`, `mb` and `fmt` format a date, a byte
 * count and a measure for the place it is shown.
 */

export interface StoryContext {
  readonly esc: (s: unknown) => string
  readonly label: (b: unknown) => string
  readonly when: (iso: string) => string
  readonly mb: (bytes: number) => string
  readonly fmt: (v: unknown) => string
  readonly demSources: Readonly<Record<string, { name: string; coverage: string; about: string; credit: string; license: string }>>
  readonly pageHref: (slug: string, section?: string) => string | null
}

export const makeStory = (ctx: StoryContext): ((build: unknown, tag?: string) => string) => {
  const { esc, label, when, mb, fmt, demSources, pageHref } = ctx
  // A build's own story, written from its meta.json. Anything an older build did not record is
  // said to be unknown rather than guessed.
  const how = (id, text) => {
    const href = pageHref('how-its-made', id)
    return href ? '<a href="' + esc(href) + '">' + text + '</a>' : text
  }
  const KNOWN = new Set(['features', 'ground', 'ribbons', 'buildings', 'heightFromTag', 'heightFromModel', 'heightFromLevels', 'heightGuessed', 'footprintsAdded', 'bridgePieces', 'elevationDatum', 'elevationTop', 'rapidCells', 'contourSegments', 'strips', 'coastWays', 'year', 'newSincePrevious', 'landmarks', 'curated', 'datedCurated', 'datedOsm', 'datedParcel', 'undatedToday', 'traced', 'tracedEndMap', 'tracedEndRebuilt', 'tracedEndHighway', 'tracedEndAssumed'])
  const POINTS = ['north', 'north-northeast', 'northeast', 'east-northeast', 'east', 'east-southeast', 'southeast', 'south-southeast', 'south', 'south-southwest', 'southwest', 'west-southwest', 'west', 'west-northwest', 'northwest', 'north-northwest']
  const isNum = (v) => typeof v === 'number' && Number.isFinite(v)
  const int = (v) => Math.round(v).toLocaleString()
  const dist = (m) => (m >= 1000 ? +(m / 1000).toFixed(2) + ' km' : Math.round(m) + ' m')
  const deg360 = (d) => Math.round(((d % 360) + 360) % 360) % 360
  const compass = (d) => POINTS[Math.round((((d % 360) + 360) % 360) / 22.5) % 16]
  const plural = (n, one, many) => int(n) + ' ' + (Math.round(n) === 1 ? one : many || one + 's')
  const ordinal = (n) => n + (n % 100 >= 11 && n % 100 <= 13 ? 'th' : n % 10 === 1 ? 'st' : n % 10 === 2 ? 'nd' : n % 10 === 3 ? 'rd' : 'th')
  const pct = (part, whole) => (whole > 0 ? Math.round((100 * part) / whole) + '%' : '–')
  const areaText = (m2) => (m2 >= 10000 ? (m2 / 10000).toFixed(1) + ' ha' : int(m2) + ' m²')
  const latlon = (c) => Math.abs(c[1]).toFixed(4) + '°' + (c[1] >= 0 ? 'N' : 'S') + ', ' + Math.abs(c[0]).toFixed(4) + '°' + (c[0] >= 0 ? 'E' : 'W')
  const unknown = (text) => '<span class="unknown">' + text + '</span>'
  const story = (x, tag) => {
    const c = x.config || {}, s = x.stats || {}, t = c.terrain || null
    const has = (k) => isNum(s[k])
    const relief = !!t && t.enabled !== false && has('elevationTop') && has('elevationDatum')
    const out = []
    // Each heading opens a section; the sections flow into as many columns as fit.
    let inSection = false
    const head = (title, link) => {
      out.push((inSection ? '</section>' : '') + '<section><h4>' + title + (link ? ' ' + link : '') + '</h4>')
      inSection = true
    }
    out.push(tag ? '<h3>' + tag + ' · ' + esc(label(x)) + '</h3>' : '')

    // The place and the frame.
    let lede = '<b>' + esc(x.title || c.title || x.region) + '.</b> '
    if (isNum(c.width) && isNum(c.depth)) {
      lede += 'A frame ' + dist(c.width) + ' across and ' + dist(c.depth) + ' deep (' + ((c.width * c.depth) / 1e6).toFixed(2) + ' km²)'
      const ctr = Array.isArray(c.center) && isNum(c.center[0]) && isNum(c.center[1]) ? c.center : null
      if (ctr) lede += ', centered on <a href="https://www.openstreetmap.org/?mlat=' + ctr[1] + '&amp;mlon=' + ctr[0] + '#map=16/' + ctr[1] + '/' + ctr[0] + '" target="_blank" rel="noopener" title="Open this point on openstreetmap.org">' + latlon(ctr) + '</a>'
      lede += '.'
    }
    out.push('<p class="lede">' + lede + '</p>')

    // Time: what is measured and what is curated in a dated scene.
    if (x.time) {
      const tm = x.time
      head('The year ' + esc(tm.year) + (tm.title ? ': ' + esc(tm.title) : ''), how('time', 'how time is drawn →'))
      if (tm.note) out.push('<p>' + esc(tm.note) + '</p>')
      if (has('buildings')) {
        const dated = (s.datedCurated || 0) + (s.datedOsm || 0) + (s.datedParcel || 0)
        let p = '<b>Measured:</b> ' + plural(s.buildings, 'building') + ' standing today that had been built by ' + esc(tm.year) + '. '
        if (dated > 0) p += 'Their years: ' + int(s.datedParcel || 0) + ' from the city assessor’s year built, ' + int(s.datedOsm || 0) + ' from OpenStreetMap’s <code>start_date</code>' + (s.datedCurated ? ', ' + int(s.datedCurated) + ' curated' : '') + '. '
        if (s.undatedToday > 0) p += int(s.undatedToday) + ' more have no recorded year and appear only in today’s scene. '
        if (isNum(s.newSincePrevious) && isNum(tm.previous)) p += '<b>' + int(s.newSincePrevious) + '</b> are new since ' + esc(tm.previous) + ', roofed in gold. '
        p += 'Anything demolished since is missing unless traced or curated below.'
        out.push('<p>' + p + '</p>')
      }
      if (s.traced > 0) {
        out.push('<p><b>Traced:</b> ' + plural(s.traced, 'building') + ' that no longer stand, traced from Sanborn fire-insurance maps and drawn in the maps’ own colors (pink brick, yellow frame, blue stone, gray iron). Each appears from the first map that shows it, though it may be older. When it went: ' +
          int(s.tracedEndMap || 0) + ' by a later map that no longer shows it, ' + int(s.tracedEndRebuilt || 0) + ' by the year the building now on the site went up, ' +
          int(s.tracedEndHighway || 0) + ' by an expressway through the site, and ' + int(s.tracedEndAssumed || 0) + ' <b>assumed</b> gone by 1960. Heights are <b>guessed</b> from the material: brick and stone three stories, frame two.</p>')
      }
      if (s.streetcarLines > 0) {
        out.push('<p><b>Streetcars:</b> ' + plural(s.streetcarLines, 'car line') + ' in red, each placed on today’s streets from the corners its sources name (listed below), with ' + plural(s.streetcars || 0, 'car') + ' along them' +
          (isNum(s.streetcarScale) && s.streetcarScale !== 1 ? ', all drawn ' + esc(s.streetcarScale) + ' times life size so they read at this scale' : '') + '.' +
          (isNum(s.unbuiltStreets) && s.unbuiltStreets > 0 ? ' Small streets are drawn only where a house of the year stood nearby: ' + int(s.unbuiltStreets) + ' laid out since are left off.' : '') + '</p>')
      }
      if (!(s.streetcarLines > 0) && isNum(s.unbuiltStreets) && s.unbuiltStreets > 0) {
        out.push('<p><b>Streets:</b> a street is drawn only where a building of the year stood within reach of it or the town plan laid it out: ' + int(s.unbuiltStreets) + ' of today’s are left off. Whatever the era rules do not date (parks, cemeteries, dams, piers, parking aisles) is drawn in today’s scene only.</p>')
      }
      if (s.parts > 0 || s.canopyPieces > 0 || s.trainPieces > 0) {
        out.push('<p><b>Modeled close up:</b> ' + plural(s.parts || 0, 'part') + ' of one building, each from its plans and photographs, in the building’s own colors' +
          (s.canopyPieces > 0 ? '; ' + plural(s.canopyPieces, 'piece') + ' of platform canopy' : '') +
          (s.trainPieces > 0 ? '; and ' + plural(s.trainPieces, 'car') + ' of standing trains, their number and makeup illustrative' : '') + '. Heights are <b>approximate</b>. ' + how('one-building-close-up', 'how the station is modeled →') + '</p>')
      }
      const cur = Array.isArray(tm.curated) ? tm.curated : []
      if (cur.length) {
        out.push('<p><b>Curated</b> for this year, from published sources; positions are drawn from today’s street grid and published dimensions, not surveyed:</p><ul>' +
          cur.map((h) => '<li><b>' + esc(h.name) + '</b> (' + esc(h.from) + (h.to ? '–' + esc(h.to) : '') + '). ' + esc(h.note) +
            (h.sources && h.sources.length ? ' <span class="sources">' + h.sources.map((u, k) => '<a href="' + esc(u) + '" target="_blank" rel="noopener">[' + (k + 1) + ']</a>').join(' ') + '</span>' : '') + '</li>').join('') + '</ul>')
      } else out.push('<p>No curated features stand in this year; roads, rail and water follow the series’ era rules.</p>')
      out.push('<p>The ground is today’s: cuts and fills since (the interstate, the floodwall) are in the elevation.</p>')
    }

    // The camera.
    head('Camera', how('camera', 'how the camera works →'))
    const cam = []
    if (isNum(x.bearing)) {
      let p = 'Looking ' + compass(x.bearing) + ' (bearing ' + deg360(x.bearing) + '°)'
      if (c.snap !== false && isNum(c.bearing)) {
        const turn = x.bearing - c.bearing
        p += Math.abs(turn) < 0.05
          ? ', where snapping to the street grid left it'
          : ', turned ' + Math.abs(turn).toFixed(1) + '° ' + (turn < 0 ? 'counter-clockwise' : 'clockwise') + ' from the configured ' + deg360(c.bearing) + '° so the street grid runs along the diagonals'
      } else if (c.snap === false) p += ', a fixed bearing with no snapping'
      cam.push(p + '.')
    }
    const squash = isNum(c.squash) ? Math.min(1, Math.max(0.01, c.squash)) : 0.5
    const tilt = (Math.asin(squash) * 180) / Math.PI
    cam.push('Orthographic, tilted ' + Math.round(tilt) + '° down from the horizon: ground running into the picture is drawn at ' + +squash.toFixed(2) + '× its length and heights at ' + Math.cos(Math.asin(squash)).toFixed(2) + '×' +
      (isNum(c.exaggeration) && c.exaggeration !== 1 ? ', then ×' + c.exaggeration + ' for every height' : '') + '.')
    if (isNum(c.scale)) cam.push(c.scale + ' px per meter across the frame' + (Array.isArray(x.viewBox) ? '; the whole drawing is ' + int(x.viewBox[2]) + ' × ' + int(x.viewBox[3]) + ' px at 1:1' : '') + '.')
    out.push('<p>' + cam.join(' ') + '</p>')

    // What went in.
    head('Sources', how('inputs', 'where the data comes from →'))
    const src = []
    src.push('<li><b>OpenStreetMap</b>: ' + (has('features') ? int(s.features) + ' features read from the cached download' : unknown('feature count not recorded')) +
      (c.data && c.data !== x.region ? ', shared with region <code>' + esc(c.data) + '</code>' : '') +
      (has('coastWays') ? '; the sea and tidal water come from ' + plural(s.coastWays, 'coastline way') : '') + '.</li>')
    if (relief) {
      const dem = demSources[t.source || '3dep'] || demSources['3dep']
      const fill = t.fillFrom ? demSources[t.fillFrom] : null
      src.push('<li><b>' + esc(dem.name) + ' elevation</b> (' + esc(dem.coverage) + '; ' + esc(dem.about.charAt(0).toLowerCase() + dem.about.slice(1)) + ')' +
        (fill ? ', with gaps beyond its coverage filled from <b>' + esc(fill.name) + '</b>' : '') + ', fetched at ' + (t.demResolution ?? 1) + ' m per pixel and resampled to a ' + (t.cell ?? 5) + ' m grid. The ground runs from ' +
        s.elevationDatum.toFixed(1) + ' m to ' + s.elevationTop.toFixed(1) + ' m above sea level (' + (s.elevationTop - s.elevationDatum).toFixed(1) + ' m of relief), drawn ' +
        (t.exaggeration ?? 2) + '× taller than life. Buildings and bridges keep their true heights.</li>')
    } else if (t && t.enabled !== false) {
      src.push('<li><b>Elevation</b>: ' + unknown('the region asks for terrain, but this build recorded no elevation range. Either the elevation was not fetched yet (the build then falls back to a flat plate), or the build predates that measure.') + '</li>')
    } else {
      src.push('<li><b>No elevation</b>: drawn on a flat plate' + (t && t.enabled === false ? ' (terrain is switched off for this region)' : '') + '.</li>')
    }
    out.push('<ul>' + src.join('') + '</ul>')

    // Ground.
    head('Ground', how('ground', 'what the ground is made of →'))
    const g = []
    if (has('ground')) g.push(plural(s.ground, 'mapped area') + ' of water, islands, parks, woods and other cover')
    if (has('ribbons')) g.push(plural(s.ribbons, 'ribbon') + ' of road, path, rail, canal and weir')
    let gp = g.length ? 'From the map, ' + g.join(', and ') + '.' : unknown('Ground counts were not recorded.')
    if (has('strips')) gp += ' Painted in ' + int(s.strips) + ' strips from back to front, ' + 2 * ((t && t.cell) ?? 5) + ' m deep each, so hills hide what is behind them (' + how('drawing', 'why') + ').'
    if (relief && has('contourSegments')) {
      const iv = t.contour ?? 2
      gp += iv > 0 ? ' Contours every ' + iv + ' m with every ' + ordinal(t.majorEvery ?? 5) + ' line heavier: ' + int(s.contourSegments) + ' segments.' : ' No contours.'
    }
    out.push('<p>' + gp + '</p>')

    // Rivers and rapids.
    head('Rivers and rapids', how('rapids', 'how rapids are read →'))
    if (relief) {
      const thr = t.rapids ?? 0.035
      if (has('rapidCells')) {
        const cell = t.cell ?? 5
        out.push('<p>' + (s.rapidCells > 0 ? int(s.rapidCells) + ' grid cells (about ' + areaText(s.rapidCells * cell * cell) + ') read as rapids' : 'No stretch of water read as rapids') +
          ': places where the river’s surface, recovered from the lidar, falls faster than ' + +(thr * 100).toFixed(2) + ' m per 100 m, measured over 40 m. Rock standing more than 1 m clear of that surface is drawn as boulders. Both are ' +
          how('rivers', 'inferred') + ' from the lidar, not observed.</p>')
      } else out.push('<p>' + unknown('Rapids were not counted for this build.') + '</p>')
    } else {
      out.push('<p>Without elevation, water is drawn from OpenStreetMap’s outlines as they are. No river surface, rocks or rapids are inferred.</p>')
    }

    // Buildings.
    head('Buildings', how('buildings', 'where heights come from →'))
    if (has('buildings')) {
      const added = s.footprintsAdded > 0 ? s.footprintsAdded : 0
      out.push('<p>' + plural(s.buildings, 'building') + ', extruded from footprints of at least ' + (c.minBuildingArea ?? 12) + ' m² that lie wholly inside the frame' +
        (added > 0 ? ': OpenStreetMap’s, plus ' + int(added) + ' traced by <a href="https://github.com/microsoft/GlobalMLBuildingFootprints">Microsoft’s building model</a> where OpenStreetMap has none.' : ', from OpenStreetMap.') + '</p>')
      if (has('heightFromTag') && has('heightFromLevels') && has('heightGuessed')) {
        const model = s.heightFromModel > 0 ? s.heightFromModel : 0
        const tot = s.heightFromTag + model + s.heightFromLevels + s.heightGuessed
        const seg = (cls, n) => (n > 0 ? '<span class="' + cls + '" style="width:' + ((100 * n) / tot).toFixed(2) + '%"></span>' : '')
        out.push('<div class="mixbar" title="Where the heights came from">' + seg('m-tag', s.heightFromTag) + seg('m-model', model) + seg('m-lev', s.heightFromLevels) + seg('m-guess', s.heightGuessed) + '</div>')
        out.push('<ul class="keyed">' +
          '<li><span class="key m-tag"></span>' + int(s.heightFromTag) + ' (' + pct(s.heightFromTag, tot) + ') from a <code>height</code> tag</li>' +
          (model > 0 ? '<li><span class="key m-model"></span>' + int(model) + ' (' + pct(model, tot) + ') from Microsoft’s model, <b>estimated</b> from imagery</li>' : '') +
          '<li><span class="key m-lev"></span>' + int(s.heightFromLevels) + ' (' + pct(s.heightFromLevels, tot) + ') from the number of floors, at 3.4 m a floor</li>' +
          '<li><span class="key m-guess"></span>' + int(s.heightGuessed) + ' (' + pct(s.heightGuessed, tot) + ') <b>guessed</b> from the building’s type and size</li></ul>')
      } else out.push('<p>' + unknown('Where the heights came from was not recorded for this build.') + '</p>')
    } else out.push('<p>' + unknown('Buildings were not counted for this build.') + '</p>')

    // Bridges.
    head('Bridges', how('bridges', 'how decks are placed →'))
    const rules = Array.isArray(c.bridges) ? c.bridges : []
    let bp = has('bridgePieces') ? (s.bridgePieces > 0 ? plural(s.bridgePieces, 'bridge span') + ' of up to 22 m, so long bridges sort among the buildings.' : 'No bridges in the frame.') : unknown('Bridge spans were not counted for this build.')
    if (!has('bridgePieces') || s.bridgePieces > 0) {
      bp += ' Deck heights are rules of thumb' + (rules.length ? ': ' + rules.map((r) => esc(r.match) + ' ' + esc(r.deck) + ' m').join(', ') + ', and any other bridge ' : ': every bridge ') + (c.bridgeDeck ?? 7) + ' m per OSM layer.'
    }
    out.push('<p>' + bp + '</p>')

    // Drawing.
    head('Drawing', how('paint-order', 'paint order →'))
    const dots = { all: 'a dot on every visible corner', roof: 'dots on roof corners only', none: 'no dots' }[c.dots || 'all'] || 'dots: ' + esc(c.dots)
    out.push('<p>The <code>' + esc(x.palette || c.palette || 'paper') + '</code> palette, ' + dots + ', on a ground slab ' + (c.slab ?? 14) + ' m thick.</p>')

    // This build.
    head('This build', how('archive-and-explorer', 'the archive →'))
    const bl = []
    bl.push('Built ' + (x.createdAt ? when(x.createdAt) : unknown('at an unrecorded time')) + (isNum(x.ms) ? ' in ' + (x.ms / 1000).toFixed(1) + ' s' : '') + (isNum(x.bytes) ? ', ' + mb(x.bytes) + ' of SVG' : '') + '.')
    if (x.git) bl.push('From commit <code>' + esc(x.git.commit) + '</code>, “' + esc(x.git.subject) + '”' + (x.git.dirty ? ', <span class="dirty">with uncommitted changes in src/ or regions/</span>' : '') + '.')
    else bl.push(unknown('No commit was recorded; it was not built inside a git checkout.'))
    if (x.note) bl.push('Note: <b>' + esc(x.note) + '</b>.')
    out.push('<p>' + bl.join(' ') + '</p>')
    const other = Object.keys(s).filter((k) => !KNOWN.has(k)).sort()
    if (other.length) out.push('<p>Other measures: ' + other.map((k) => esc(k) + ' ' + fmt(s[k])).join(', ') + '.</p>')

    out.push('</section><p class="credit">Map data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors (ODbL)' +
      (relief ? ' · ' + esc((demSources[t.source || '3dep'] || demSources['3dep']).credit) + ' (' + esc((demSources[t.source || '3dep'] || demSources['3dep']).license) + ')' + (t.fillFrom && demSources[t.fillFrom] ? ' · ' + esc(demSources[t.fillFrom].credit) : '') : '') + (pageHref('about') ? ' · <a href="' + esc(pageHref('about')) + '">credits and licenses</a>' : '') + '</p>')
    return '<div class="story">' + out.join('') + '</div>'
  }
  return story
}
