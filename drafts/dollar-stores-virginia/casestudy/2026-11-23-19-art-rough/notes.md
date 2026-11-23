# Step 19: the art poster, rough draft (November 23, 08:49-09:30)

- **Chris, 08:49:** "show me the "art" version if we have that here"
- **Chris, 08:50:** "how was it you thought we were ready to handoff, but didn't have the art
  poster ready yet?"
- **Chris, 08:52:** "yes" (to tracking it on the board, telling the planning session, and
  starting the rough draft)

## How it was dropped

- The plan (step 1) committed to two posters: the editorial poster and a "simplified artistic"
  version, "denser and reduced element resolution", with every town and city (227 tiles).
- The art version never got a board entry. When Chris said "continue forward to publication"
  (step 16), it was read as the piece in progress, and every release step after that was about
  the editorial poster.
- The handoff prompt to the planning session described what was on the branch and left out what
  was not. So it read as if the whole job were finished.
- The art version was listed as remaining work in the 11:22 summary on November 22, and nowhere
  after that.
- **Fix.** The art version is now its own board entry (`viz-dollar-stores-virginia-art`), and the
  planning session gets a one-line note.

## By the time of this step

The planning session had already merged, released and published the editorial poster and the
page (step 18, on main). This work is on a new branch, `viz/dollar-stores-virginia-art`, off
main at ecc8917.

## The draft

- **Script.** `tools/stories/dollar-stores/art.py`.
- **Every town and city.** All 227 places scored in Virginia (`work_all`), each the same 5 km of
  ground around its population-weighted center, north up.
- **Only three things drawn:**
  - the built-up town (the lead edge) in flat gray;
  - the HPMS 2024 counted roads in dark ink, five widths by traffic, simplified to 25 m;
  - every Dollar General as a yellow square with a black ring.
- **Grouping.** The five regions of `regions.json` (each place by the county at its center,
  nearest county if on a line), west to east within each region.
- **Text.** One line of explanation and the sources line. No captions, arrows or charts.
- **Counts.** Southwest 52, Valley and Blue Ridge 41, Piedmont and Southside 64, Urban crescent
  42, Northern Neck, Middle Peninsula and Eastern Shore 28.

## Rounds

1. **r1.** 13 columns ran to 20 rows and 41 in, off the 36 in sheet. The style worked.
   - Troutdale drew as a perfect circle. It was checked and is real: its Census town limits are
     a circle (circularity 0.99, 8.1 km²). Its built-up area is under 1 km², so the rule uses
     the limits.
2. **r2.** 14 columns, 17 rows. It fits, with the grid ending at 33.25 in. Two problems:
   - The town names were 5.6 pt, under the 6 pt minimum.
   - The store squares were small at arm's length.
3. **r3.** Names at 6.5 pt, store squares about a third larger. Looked at whole and at 100% on
   a crop of the Urban crescent rows.

## Open for the next round

- About 2 in of empty paper at the bottom. Bigger squares would need fewer columns, or a sheet
  with more rows.
- City squares (Roanoke, Richmond, Norfolk) are solid gray and road. Fine for a portrait of
  every place, but they carry little of the edge story.
- Whether the art version wants its own title; it reuses the editorial poster's for now.
