# Step 10: the editorial poster, rough draft (November 21, 22:15-22:25)

Chris, 22:15: "go" (the poster rough draft, built around the driver's view).

## What the draft carries

- **Headline.** Chris's question, then a short deck that answers it first. Most Dollar General
  stores are not at the edge. Those that are sit where state and US highways meet, like the
  convenience store next door, and most were approved for SNAP after 2005.
- **The grid.** Every Virginia Dollar General at the edge of a small town or a CDP, 30 stores.
  There was no picking. Each is a 3 km square with roads shaded and widened by 2024 traffic
  (HPMS) and the built-up town in gray. Town limits are dashed, and none are drawn for CDPs,
  which have none. Other stores are marked, and an arrow points to the center of town.
  - Artistic license: minor roads are thin gray lines and nothing else is drawn.
  - Each caption gives the store's SNAP year, the traffic past it, and whether it is on a
    top-two road in or at a junction.
- **Three charts, from the six-state replication.**
  - "Is it true?": where Dollar General stores near small towns are (1,198 in town, 234 at the
    edge, 183 on the edge line, 463 farther out). The edge holds 15 percent of those within
    A 3, against 33 percent of road frontage.
  - "Where are the ones at the edge?":
    - At a junction: 17 percent against 6 percent.
    - On a top-two road in: 39 percent against 32 percent.
    - Inside the limits: 23 percent against 13 percent.
    - Convenience stores marked beside each. Traffic 1.3 times.
  - "When did they come?": 86 percent at the edge approved after 2005, against 50 percent in
    town.
- **"How we know, and what this can't say".** The definitions, the frozen tests and the
  independent check, and what is not in the data. West Virginia's 0 of 19, and the
  statement that a dot is a location.
- **Credits.** Sources and licenses, "made with Claude", and not affiliated with any
  company named.

## Numbers

- Every number is computed in `tools/stories/dollar-stores/poster.py` from tests.csv,
  dg_classes.csv and the de-duplicated stores. None is typed in.
- The class counts (1,198 and 463) come from the stable tie rule. The checker's rule gave
  1,195 to 1,197 and 462.

## Rounds

1. **r1.** The deck ran off the right edge. The lower band ran past the bottom of the sheet,
   and "How we know" was off the page. The left chart's labels were cut off.
2. **r2.**
   - The tiles shrank to 2.9 in, the grid now spans the width, the deck is wrapped and the
     chart band moved up.
   - Left: the middle chart's caption sat on its axis labels and ran into the third column.
3. **r3.** The captions moved down and were wrapped. Seen at full size: the tiles read, and
   nothing collides.

## Known for the next round (not fixed)

- The grid's six-store rows are arranged by score A, not by region.
- Bottom whitespace of about 1 in.
- The chart typography is matplotlib's default family.
- The isoscape plate title block is not applied; drafts never carry one.
