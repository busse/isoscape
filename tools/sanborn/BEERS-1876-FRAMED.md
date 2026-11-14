# The framed 1876 Beers map (Chris's copy)

## What it is

A framed, glazed print a little over 3 ft wide. Title block:

> JAMES RIVER AND KANAWHA CANAL / CAPITOL SQUARE AND ENVIRONS /
> PHOTOGRAPHIC REPRODUCTION OF F.W. BEARS [Beers] 1876 LITHOGRAPHIC MAPS OF RICHMOND, VIRGINIA

It has a scale bar of 0–200–400 ft, a compass rose, and "G.P.C. 8/67" in the corner.

It is a 1967 photographic copy of part of F. W. Beers, *Illustrated Atlas of the City of Richmond, Va.* (1876). The atlas plates are 1 in = 200 ft. This print is a reduced stitch of several plates. At 3 ft for about 2½ miles, it is roughly 1 in ≈ 350 ft. It runs from Gamble's Hill, Tredegar and Belle Isle to Rocketts. It shows Capitol Square, the canal basin, Mayo's Bridge, Brown's Island and the sand bar.

The project's notes (PROGRESS.md) say atlas sections J–M cover the downtown frame. This print probably joins those sections and their neighbours to the east and west. That is a guess from the photo, not checked plate by plate.

**Who "G.P.C." is: unknown.** I found no catalogue record for a 1967 "Capitol Square and Environs" reproduction. Searches covered the Library of Virginia's Richmond map guide, the LoC and HAER canal records, and VCU. The HAER survey of the canal locks (VA-23) dates from after 1968, so it is a different project. Possible makers include a city or state planning office, a canal-history group, or a printer. To find out:

- Check the back of the frame and the mat for a label.
- Ask the Library of Virginia map desk, or the Valentine, to search "Capitol Square and Environs".

## What it adds, and what it doesn't

**The content is the Beers atlas, which is already free online, and better there:**

- **VCU Libraries** digitized the whole atlas in 2023: 21 maps, each a full-plate JPG of about 69 MB. They are public domain (NoC-US), and VCU asks to be credited.
- **Library of Congress** item 2005630891 has another scan.

The framed copy is a photo of those plates. It is a generation further from the original, it is reduced in size, and it sits behind glass. It holds no buildings the scans lack.

**What an 1876 edition would add to the time series:**

- A dated layer between the 1865 scene and the 1886 Sanborn.
- Building footprints with owners' names, including the tobacco warehouses and the canal-basin warehouses.
- The Tredegar works, the canal basin and the Haxall Canal as they stood, and Mayo's Bridge.
- Property lines.

**The blocker is the drawing style, not getting a copy.** Beers draws buildings as grey hatching under the lettering. Our tracer reads Sanborn colour classes, so it cannot read hatching (see PROGRESS.md). That is equally true of this print and of the scans.

**What the photos show:**

- The street grid, the Capitol Square label, "Canal Basin", "Gambles Hill" and the river hatching are clear.
- Building names read at arm's length.
- The glass picks up glare across the whole sheet, including window reflections at the lower right and a pale band along the bottom.
- A tracing source has to be shot without the glass.

## Recommendation

1. **Trace from the VCU plates, not this print.** One 18×22 in plate at about 69 MB is very roughly 500 dpi, or about 0.12 m per pixel at 1 in = 200 ft. That is about the ground resolution of the Sanborn sheets we traced. Matching it from the framed copy would need about 900 dpi through glass, which isn't practical.
2. **Use the framed copy to check by eye,** and as a display or reference piece. A faithful photographic copy of a public-domain map adds no new US copyright (*Bridgeman v. Corel*, S.D.N.Y. 1999, persuasive rather than binding). If you ever sell a print of the map itself, credit: "F. W. Beers, *Illustrated Atlas of the City of Richmond*, 1876. Reproduction G.P.C., 1967. Collection of Chris Busse."

## If you want a good digital copy of the framed print anyway

1. **Take it out of the frame.** Glass adds glare and warping. If it can't come out, shoot through the glass with a polarizing filter on the lens and polarizing film on two lights set at 45°, in a dark room.
2. **Light it flat and even.** Use two daylight-balanced lights at 45°, no raking light (it shows paper texture, not hatching). Put a grey card or colour card in the first frame.
3. **Shoot overlapping tiles from straight above.** Use a phone or camera on a copy stand or tripod, lens parallel to the paper, and the longest lens that fits. Overlap tiles by about 30%. Aim for 400–600 dpi at print size, which is about 15–20 tiles of 24 MP for a 3 × 1.5 ft sheet. A flatbed in A3 sections also works if the print is loose and flat.
4. **Stitch.** Use Hugin (free) or PTGui with the "mosaic" or planar setting, not a panorama projection. Microsoft ICE is discontinued but still works offline. Save a 16-bit TIFF master and a JPG.
5. **Check the scale.** Measure the 400 ft scale bar and a few known block lengths in the stitch. If the stitch bends, re-shoot those tiles.
6. **Share the master** by putting it in the ISO-TEST folder. A filename such as `beers-1876-framed-master.tif` works.

## How 1876 would plug into tools/sanborn

- **Control points:** the same as the other editions. Read street corners by eye into a `cps1876.json` per plate. Fit with `rigid.py`, then rubber-sheet with `snap.py`.
- **Extraction:** this is the new part. `extract.py` and `material.py` sort pixels by Sanborn colour, and Beers is mostly monochrome. They need a hatching mode:
  - Find hatched areas by texture rather than colour. Use local line density, with orientation from a structure tensor or Gabor filters, so lettering (no single direction, small strokes) is rejected and hatching (long parallel strokes) is kept.
  - Close the hatching into solid fills with morphological closing, then drop small connected parts (letters, numbers).
  - Recover outlines from the black building edges where they are drawn.
  - Material is unknown from Beers. Default to brick at 3 storeys, or carry material from the nearest Sanborn match in 1886.
- **Fallback:** if texture classification stays noisy, hand-trace the blocks that matter most: the canal basin, Shockoe Slip, the Tredegar and the waterfront. A simple click tool over the warped plate would do; the sketch standard applies.
- **Dates:** add `1876` to `history/richmond-downtown.json` as a traced edition. Run `lifespans.py` as before, since 1886 then confirms or ends each 1876 building.

## Open questions

- Is there a label on the back? Who is G.P.C.?
- Can the print come out of the frame safely, or is it dry-mounted?
- Should 1876 be traced from the VCU plates (recommended), with this print as the check?

## Sources

- VCU Libraries, *Illustrated Atlas of the City of Richmond, Va.* (Beers, 1876), Scholars Compass, e.g. plate "Section P": https://scholarscompass.vcu.edu/beers_images/21 (1 in = 200 ft, JPG about 69 MB, public domain).
- VCU Libraries news, "Explore 1876 Richmond with newly digitized maps" (2023): https://www.library.vcu.edu/about/news/2023-news/explore-1876-richmond-with-newly-digitized-maps.html
- Library of Congress, Beers atlas: https://www.loc.gov/item/2005630891/
- Library of Virginia, Richmond maps guide: https://lva-virginia.libguides.com/richmond-maps/history (no G.P.C. or 1967 reproduction listed).
- HAER VA-23, James River & Kanawha Canal locks: https://www.loc.gov/item/va0894 (documentation after 1968, no Beers sheet).
- Also: VCU has the 1889 Baist atlas (https://scholarscompass.vcu.edu/baist), another possible edition between 1886 and 1895.
