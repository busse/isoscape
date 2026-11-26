# 36. Rain on isoscape's drawing of the city (20:34 to 20:52)

New region `richmond-gaston-rain` (8.6 by 6.4 km over the watershed, looking north, the
`richmond-streetcars` cache, the city as dated to 2004) and history `gaston-2004` (switch
`rain`).

**(i) Drawn by isoscape.** The bands as a `Tint`, with a new `tones: "rain"` (`src/tint-tones.ts`).
- drape-r1: the first build. Blue bands at relief x3 read as a flooded city, and an
  island of 8 to 10 in east of the Bottom came out blank: the band builder subtracted holes
  that held islands (`bands-check-1.png`).
- Fix: rings nested by depth, each outer with its own holes; resampled x4 so edges are curves
  (`bands-check-2.png`).
- drape-r2: violet-gray tones (no longer water-like), the watershed as a red ring, relief x1 as
  the series decided. The ring's stair steps show.
- drape-r3: ring smoothed (out and back by 40 m). drape-r4: bands one inch apart from 7 to 12
  (the view lies in 8 to 12), lighter. Kept as (i), but faint: the bands hardly differ.
- Byte check: `richmond-downtown` and `richmond-1937 --with grades` built before and after the
  change, SVG and HTML identical (cmp).

**(ii) Composite.** isoscape's drawing without rain, with the rain as a see-through wash and
inch lines over it, placed with `isoscape locate`.
- r1: the wash spilled past the drawing into its caption; r2: clipped to the frame; r3 to r5:
  header spacing, a truer title ("8 to 11 inches", not "about 10 on every part"). r5 kept.

**(e) Explainer**, on the same view with relief drawn three times its height (said in the
picture). r1: a near-invisible wash and arrows from the wrong places; r2: wash removed, arrows
down the Shockoe valley, from the west lobe and off Church Hill; r3 kept (spacing).

Recommendation: keep (ii) for pages and the story; keep (i) in the code as the path for prints.
