# Replication plan, frozen before any new place is looked at

Written with Claude on November 21, 2026 at 15:58. At that point the Virginia CDPs were being
scored but no CDP result had been read, and no place in another state had been scored.

- **Chris, 15:44.** "I believe the sample is too weak a link to declare editorial coverage.
  Get more/total coverage of data then let's analyze more deeply. Consider if we should use
  Fable."
- **Chris's choices.** Virginia in full, then replicate in neighboring states. An independent
  Fable agent reviews this plan before the run, and the findings after.

## Where the claims come from

- Discovery is Virginia's 227 incorporated places (steps 6 and 7).
- The claims below were found there and are tested here on data not used to find them:
  1. Virginia's 461 census-designated places (CDPs).
  2. Six states: North Carolina, Tennessee, Kentucky, West Virginia, Maryland and South
     Carolina.

## Units and definitions (unchanged from Virginia unless stated)

- **Places.**
  - Every incorporated place (TIGER 2024 places with FUNCSTAT A) and every CDP (LSAD 57) in
    each state.
  - The edge is the lead edge: 200+ homes per square mile or 20 percent non-road impervious,
    closed over 400 m.
  - The tiny-town and joined-town rules apply. The window is 8 km.
- **Size, not legal name.** "Town" and "city" mean different things in each state; in
  Kentucky every incorporated place is a "city". So the confirmatory unit is the *small
  incorporated place*: incorporated, under 25,000 people inside its limits in 2020, and not
  joined to a larger urban area. Larger incorporated places are the comparison. CDPs are
  reported as their own class.
- **Discovery recut.** Virginia's places will be re-cut by the same size rule and reported
  beside the replication. That is the discovery result under the new definition, not a test.
- **Stores.** USDA SNAP, still authorized, national file, by window. A store is counted once,
  at its lowest score.
- **Edge stores.** Dollar General with score A from 1 to 2.
- **Random comparison.** 40 random main-road points per edge store in the same place's edge
  band (seed 20261121).
- **Roads into town.** HPMS 2024 sections crossing the built-up edge, ranked by AADT where
  they cross.
- **Junction.** As in `features.py`: route numbers that are not "SR", two or more numbers
  meeting, degree 3 or more, within 250 m.

## Confirmatory tests

All are on the pooled replication data for small incorporated places, across the six states.
Virginia CDPs are reported apart. Each test is one-sided in the direction Virginia found.
"Holds" means the 95 percent interval clears the comparison; "against" means it clears it the
other way. Otherwise the data cannot tell.

| # | Claim from Virginia | Test | Virginia, small towns (discovery) |
|---|---|---|---|
| C1 | Edge Dollar General stores sit on one of the two busiest roads into town | share on top two vs random share; Wilson | 72% vs 47% |
| C2 | They sit at junctions of US or state routes | share within 250 m vs random; Wilson | 33% vs 7% |
| C3 | They are usually inside the town limits | share outside limits vs random; Wilson (incorporated only) | 39% vs 82% |
| C4 | They are newer than in-town stores | share authorized after 2005, edge vs in town; Wilson for edge against the in-town share | 74% vs 46% (all VA places) |
| C5 | The edge is not crowded with them | among Dollar General with A at or below 3, share at A 1 to 2 vs random road share | 11% vs 25% (all VA places) |
| C6 | The road past them is busier | median AADT vs random; bootstrap 10,000 | about 2x (all VA places) |

- **Primary claims.** C1 and C2 together are the editorial line ("the road in"). The line is
  supported for publication only if both hold.
- **Secondary.** C3 to C6 add to it or qualify it.
- **Per state.** Results by state are descriptive; no state-level test.
- **Multiple tests.** Six tests on overlapping data. No correction is applied. Instead, the
  primary claim needs both C1 and C2 to hold, and every interval is shown.

## Also reported (descriptive)

- Every Dollar General in each state, by class: in town, fringe, another place, between
  places, beyond any window.
- The same tests for Family Dollar, Dollar Tree, supermarkets and convenience stores.

## What would change the editorial line

- **C1 and C2 both hold:** "the road in" is the line, with the replication as its evidence.
- **One fails:** the line is narrowed to what held, and the poster says so.
- **Both fail:** Virginia's pattern was the small sample, and line 2 ("it's the drive, not
  the map") leads, if C5 holds.
