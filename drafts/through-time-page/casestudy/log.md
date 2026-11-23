# Downtown Richmond through time: the series page, case-study log

Kept with Claude, under Chris's standing rule of November 21, 2026. Times are the container's
clock (UTC). Every round of screenshots is in its own numbered folder; none was written over.

## The brief (2026-11-23)

Chris: "The 'Downtown Richmond Through Time' comparison feature is really broken. Horrible UX.
It needs its own section & landing page in explorer." The series (26 years, 1737 to 2026, 43
archived builds) was reached from a front-page hero that dropped visitors into the raw build
viewer: build notes, commit hashes and settings JSON under the map, 26 floating year chips,
Compare labelled A and B with the later year on the left, `[` `]` keys in grey text, no
Compare on a phone. The work was handed to an agent (Claude) as a preview for Chris to review:
nothing pushed, nothing published.

## Steps

### 01 baseline (16:54)

`2026-11-23-01-baseline/`: the viewer at `#richmond-downtown-time:1925` at 1280x711 and
390x844, and the front page, as they are on main (054d148). The SVGs are not in this
container, so the viewer's picture is empty here; the panel of build notes and settings is
what a visitor meets. `peek-1865.jpg` is a scaled-down `preview.jpg`: the pictures carry their
own year and title in the top-left corner.

Pictures: the published site's checkout here (`/home/claude/site`) holds only `meta.json` and
`social.png` per build. A shallow, blob-filtered sparse clone of `gh-pages` fetched just
`builds/*richmond-downtown-time*/preview.jpg` and `thumb.png` (43 builds, 36 MB) into a
scratch folder. Every picture in these rounds is real; none is a stand-in.

Decision: build the page as a content page with `series: <region>` in its front matter, not a
new kind of route. It then gets the left menu, `p/<slug>.html`, the share page
`s/page-<slug>.html`, the sitemap and the Copy link button for free, and its state rides in
`#/<slug>/<year>` and `#/<slug>/<a>..<b>`.

### 02 first build (r1)

`2026-11-23-02-first-build/`. Faults seen: the picture was drawn too large (`.prose img`
outranked the view's own image rule); the years "1860" wrapped one digit per line in compare
captions on desktop and phone; "Back to the viewer: The Byrd Theatre…" sat on top (the viewer
selects the first build when a page opens first); the phone's "Best on a big screen" banner
showed over a page made for phones; the row of 26 year chips did not fit at 1280 or 1440 and
scrolled out of sight, starting at "5 1870".

### 03 timeline (r2)

`2026-11-23-03-timeline/`. The chip row became a timeline: every year a dot, spaced by the
time between them (1737 to 1788 is long, 1860 to 1870 short), with half-century marks; press,
click or drag along it to scrub through the years. Previous and next buttons with their years,
and Compare two years, sit on the same row, above the picture, so on a 1280x711 laptop the
year, the controls and nearly all of the picture are on the first screen. On a phone the order
is controls, picture, caption. Back link, Copy link and the phone banner hidden on this page.
Faults seen: the last mark "2026" wrapped; the left side's year tag covered the year printed in
the picture.

### 04 fixes (r3)

`2026-11-23-04-fixes/`. Tags moved to the bottom corners, zoom buttons to the top right. Phone:
"2000" and "2026" collided; the marks now keep 30 years from either end.

### 05 final (r4)

`2026-11-23-05-final/`: single year and compare at 1280x711, 1440x900 and 390x844, the whole
page at 1280 and 390, and `p/downtown-through-time.html` without script.

### 06 interaction (i1, i2)

`2026-11-23-06-interaction/` and `interact.mjs`: Playwright driving Chrome (sandbox on,
file://, no server), 31 checks, desktop and an emulated phone with emulated touch. Round i1
found a real bug: `ttPick` called `ttStep`, which does not exist once the explorer embeds each
function's source on its own ("ttStep is not defined" when a picker crossed the other side). Fixed, and a
unit test now runs each embedded function on its own. Also from i1: zoom went to 8x, past the
preview's own pixels (blurry, `d3` in i1); it now stops near 1.25 picture pixels per screen
pixel. The divider's tag covered a side's tag near the edge (`p1`); a side's tag now steps aside.
i2: all 31 pass, no page errors.

## Findings for Chris

- 14 of the 26 years shown are builds of November 14 ("Sanborn clean"), the other 12 of
  November 16 and 17 (wave 4, the version 5 redraws of 1925 and 1950, and 2026's version 4). Their drawing differs (the canal and basin as water,
  the Free Bridge, the frame's height), so a pair across the two vintages, such as 1865 and
  1870, shows differences of method as well as of history. A fresh `isoscape series` run would
  make every pair compare cleanly.
- The 1870 build's own caption says Shockoe Creek "still runs open, until 1877"; the history
  file now says the 1886 map still shows it open and draws it to 1890. The page shows each
  build's own caption, so 1870 shows the stale one until it is rebuilt.
