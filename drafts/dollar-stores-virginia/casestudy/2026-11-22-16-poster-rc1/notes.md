# Step 16: final draft. rc1, inspection, fix round, rc2 (November 22, 11:31-12:05)

Chris, 11:31: "Continue forward to publication." Read as approving the look (the working-draft
gate). The poster became release candidate `1.0.0-rc1`, and the story page was drafted.

## rc1

- **Changes from d2.** Only the draft label in the sources line ("Working draft d2" became
  "Chris Busse, November 2026").
- **Files.** `dollar-stores-virginia-poster-1.0.0-rc1.{png,pdf}`, from commit 6ffef55.

## Inspection

- **Inspector.** An independent Fable agent, given the README checklist as it stands, the
  design key, the asset version, the commit, the print file and the board entry. It did not
  make the poster.
- **Report.** `inspection/report.md`, saved by this session because the agent's own write was
  refused, with its crops beside it.
- **Verdict.** Fix: 1 A, 5 C and 9 B findings.
- **Each A and C finding was re-checked against the data before fixing.** All six were
  confirmed. Drakes Branch was found to have the same problem as Union Hall.

| Finding | Fix in rc2 |
|---|---|
| A: locator numbers 2 and 4 outside Virginia. The step 15 log wrongly said they had been moved inside; only 1 and 5 were. | 2 and 4 placed inside their regions. 5 placed at a point on Northern Neck land computed from the counties (r1 of rc2 had it over the bay). |
| C: chart 1 note said "within twice the distance"; the test C5 uses A at or below 3. | "within three times the distance". |
| C: "redid every calculation from scratch" overstated the review. | "A separate review made with Claude recomputed the main results with its own code." |
| C: five "no traffic count" captions beside counted roads (no HPMS section within 60 m). | The caption gives the distance and count of the nearest counted road, for example "410 ft from a road with 7,791 vehicles/day". |
| C: Union Hall's "905 vehicles a day · busiest road in" at a corner with a 6,025 road. Drakes Branch is the same case (1,699 matched, 2,404 within 60 m). | New caption rule, in `caption_traffic`. The count is the busiest counted road within 60 m. The rank is printed only when that road is the one the tests matched. |
| C: "would matter" had no source. | "neither are zoning or water and sewer lines, which may matter". |

B findings:

- **Fixed in the same round, all text or spacing:**
  - "busiest road into town";
  - chart 2 label spacing;
  - "the middle of where a town's people live";
  - "that isn't part of a bigger urban area";
  - "actually" and "Things like" dropped;
  - the disclaimer rewritten ("A yellow square shows where a store is and says nothing about the
    store or the town");
  - "the file starts in 2005";
  - the deck now leads with the junction result and adds "although only about one in 6 is".
- **Accepted, on the board with their boxes:** markers under arrows at Mineral, Lake of the
  Woods and Honaker.

The same text fixes were made on the story page.

## Record fixes from the inspection

- **The case-study copy of `dg_classes.csv`** was from the first, unstable run. It was replaced
  with the stable run's table (the one the poster used). The old copy is kept as
  `dg_classes-run1-unstable-ties.csv`, and a dated correction note was added to the top of
  step 9's `findings.md`.
- **`sources.md`** now lists the six states' downloads. Checksums were made on the Mac in
  `raw/states/six-states-inputs.sha256`.

## rc2 rounds (layout, within the one fix round)

- **r1.**
  - Fixed: everything above.
  - Two problems remained. The bottom-left paragraph ran onto the sources line, and
    Hillsville's longer caption came within 0.1 in of Floyd's.
- **r2.**
  - Fixes for those two:
    - Tile captions are now 7.2 pt, with "vehicles/day".
    - The paragraph is shorter.
    - The sources line sits 0.13 in lower.
  - Measured: the widest caption is 3.45 in, leaving 0.44 in to the next caption.

## Targeted recheck

Only what changed was rechecked:

- The locator.
- The deck.
- A row of captions and the Union Hall and North Shore tiles.
- The charts band.
- The bottom paragraphs and the sources line.

Every caption's width was measured. All clear.

## Owner's note during this step

Chris, 11:45: "It's ok to use Opus for subagents and inspection at this phase going forward; no
need for Fable unless we need its unique capabilities."
