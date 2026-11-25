# Misfit: the design language for working-out-loud sites

Chris Busse keeps two kinds of site. **Finished ones**, like chrisbusse.com and the shop, are
edited and quiet. **Working-out-loud ones**, the misfit-* sites, show a project while it is
being made: its drafts, its changes, its numbers. This language is for the second kind. The
isoscape explorer is the first site to use it.

Written with Claude for Chris, November 25, 2026. `tokens.css` beside this file is the source
of truth; nothing in a misfit site declares a raw color, size or font that is not a token here.

## Same family, other register

The palette is chrisbusse.com's (busse/cbdot), value for value: paper, ink gray, and non-photo
blue. Non-photo blue keeps the job it has there. It was the pencil draftsmen used for layout,
because the reproduction camera could not see it. Blue is structure (rules, grid, marks,
underlays), ink is what you read, and true non-photo blue is never text on a light ground.

What changes is the register, from magazine to drafting sheet:

| | chrisbusse.com | misfit sites | the shop |
|---|---|---|---|
| Type | Archivo display, Newsreader text, Plex Mono labels | IBM Plex Sans for reading, IBM Plex Mono for everything measured | Libre Baskerville, Libre Franklin |
| Ground | Paper, white space | A sheet (tan-100) with a faint non-photo-blue grid where drawings sit; paper panels for reading | Cream, product photography |
| Scale | 17px body, a 10rem wordmark | 13px interface, 15.5px reading, 32px at most | Theme scale |
| Shape | Rules and generous margins | Square corners (2px), hairlines, dense panels | Theme cards |
| Signature | The wordmark and the island | Stamps: status, version, date, commit, in boxed mono | Prices, collections |

## Rules

1. **Show the working.** Every piece carries its state: a stamp (`WORKING DRAFT`, `LIVE`,
   `v4`), a date, and where it applies, the commit it came from. Changes have a page.
2. **Mono for anything measured.** Dates, counts, sizes, versions, coordinates, commits, keys,
   labels and stamps are set in Plex Mono. Reading text and headings are Plex Sans.
3. **Blue is structure, ink is content.** Grid lines, section rules (4px under a section head),
   focus rings and the link underlay are blue. Links are npb-700 (6.31:1) with a non-photo-blue
   underline that fills on hover, as on chrisbusse.com.
4. **The drawing sits on the grid.** Where a drawing, map or figure is shown on its own, the
   ground is the sheet with a 24px grid (major line every fifth). Reading happens on paper.
5. **Square and thin.** Corners 2px. Rules 1px hairline, 2px ink for a strong break, 4px blue
   for a section. No shadows except under a drawing lifted off the sheet.
6. **One loud thing per screen.** At most one filled button (ink on paper). Everything else is
   an outline or a link.
7. **Signals mean something.** Green, amber and red appear only in stamps and checks.
8. **Accessible by construction.** Text pairs meet WCAG 2.2 AA (the ratios above are against
   paper). Focus is always visible. Motion is limited to state changes.

## Components

- **Masthead:** the project mark, its name in Plex Sans semibold, and a mono tag `WORKING OUT LOUD`
  linking to chrisbusse.com/misfits.
- **Label:** mono, 11.5px, uppercase, tracked .12em, muted. Above every section and panel.
- **Stamp:** mono, 10.5px, uppercase, 1px border in the stamp's color, 2px radius, no fill.
- **Section head:** a label, a Plex Sans heading, and a 4px blue rule under it.
- **Button:** outline by default (1px ink, square); the one primary action on a screen is
  filled ink on paper. A buy link is a button with ↗ and never the only thing on a screen.
- **Sheet:** the grid ground, for drawings and the map viewer.
- **Panel:** paper, a 1px hairline frame, square.

## Using it in another misfit site

Copy `tokens.css`, load IBM Plex Sans (400, 500, 600) and IBM Plex Mono (400, 500, 600), and
map the site's own variables onto the `--m-*` semantic tokens, as `src/explorer.ts` does in
`THEME_CSS`. Keep the palette in step with busse/cbdot's `_sass/_tokens.scss`.
