# Step 11: the editorial poster, working draft d1 (November 22, 08:02-08:40)

Chris, 08:02: "continue with your thoughts. don't make the text copy read like AI wrote it. Use a
freshman college level educational writing style"

Read as passing the first gate (worth pursuing), so the rough draft became working draft d1 with
the three changes proposed at the end of step 10. All of the poster's text was rewritten.

## What changed from rough r3

- **Grid by region.** The 30 stores are grouped into the five regions of `regions.json`, west to
  east, and sorted west to east within each region. Each store is placed in a region by
  its point in Census 2024 county boundaries (`cb_2024_us_county_500k`, newly fetched; all 133
  Virginia counties and cities matched a region). A rule and a numbered region name sit over
  each run of tiles. Counts: Southwest 8, Valley and Blue Ridge 1, Piedmont and Southside 18,
  Urban crescent 1, Northern Neck, Middle Peninsula and Eastern Shore 2.
- **Locator map.** A small Virginia map in the header shows the five regions and the 30 stores, so
  the grouping means something to a reader.
- **Typeface.** Libre Baskerville, the print title block's font (`tools/print/fonts`, OFL),
  converted from woff to TTF for matplotlib. Text is wrapped by measuring it in that font.
- **Whitespace.** The bottom gap is gone; the sources sit at the foot of the sheet.

## Two errors in the rough draft, fixed

1. **Wrong place.** The rough deck said "Around the small towns of Virginia and six neighboring
   states, 234 of 2,078". Those counts are set B only: North Carolina, Tennessee, Kentucky, West
   Virginia, Maryland and South Carolina, with no Virginia stores. d1 says "In six states around
   Virginia", and a line over the charts names the six states and says they are where the
   tests were run.
2. **Overstated.** The rough deck said edge stores "are found where state and US highways meet".
   Only 17 percent are within 250 m of such a junction (6 percent expected by chance). d1 says
   they are about 3 times as likely as a random roadside spot at the same edge to be near one,
   "even though only about one in 6 is".

Both numbers are computed in `poster.py` (`junction_x`, `1 / c2.share`), not typed.

## Writing

Plain textbook register for a first-year college reader:
- Answer first.
- Terms explained where they first appear (SNAP, margin of error, "at the edge", small town).
- Charts read in words ("Suppose the stores had been placed at random...").
- The house rules hold: no em dashes, no "X, not Y" contrasts, no colon punchlines.
- The rough draft's closing triad ("a store, a town or the people who live there") became
  "It says nothing about the quality of any store or town."

## Rounds

1. **r1.** The deck was too long and collided with the grid heading. The sheet ran about 2.4 in
   past the bottom, and the locator's region names sat on top of the stores.
2. **r2.** These changes fit the sheet:
   - shorter deck;
   - tiles 2.62 in;
   - region numbers on the locator, with names in a key below it.
   The grid's caption touched the first region label, and the middle chart's note touched the
   rule below it.
3. **r3.** More room under the deck and above the grid. Shorter traffic sentence, then corrected:
   "1.3 times as much traffic" had no comparison, so it became "as the random spots do".
4. **r4.** Tiles 2.55 in with 1.1 in between rows, so each region label clears the tile above.
   Middle note widened to 7.4 in.
5. **r5.** The locator's "4" moved off a region border, into open space beside Northern
   Virginia. Checked at full size: the header, the locator, a region run and the middle chart.
   Nothing collides.

## Known for the next round (not fixed)

- Two tiles are both captioned "Martinsville". Both are edges of the city, and the stores' mail
  goes to Fieldale and Axton.
- Three of the five regions hold one or two stores, so their runs are short. That is the data.
- The locator's numbers float beside their regions rather than in them for 1, 4 and 5.
