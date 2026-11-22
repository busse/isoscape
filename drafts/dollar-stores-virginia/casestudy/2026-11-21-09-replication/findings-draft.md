# Replication findings, draft for the independent check

Written with Claude, November 21, 2026, 20:30, after the frozen tests ran once on all data
(20:20). Numbers are from `data/tests.csv`, `data/drive_in.csv` and `data/dg_classes.csv`.
To be checked by an independent Fable agent before Chris sees it as a finding.

## Scope

- **Places scored.** 3,966 places in all:
  - Discovery: Virginia's 227 incorporated places.
  - Set A: Virginia's 461 CDPs.
  - Set B: 3,278 incorporated places and CDPs in NC, TN, KY, WV, MD and SC.
- **The primary unit.** Small incorporated places in set B, meaning under 25,000 people and
  not joined to a larger urban area. That covers 234 edge Dollar General stores in 203
  places. Virginia's discovery recut has 18.

## The frozen tests (primary: set B, small incorporated places)

D is the mean, over edge stores, of (store meets the claim − share of random edge-band road
points in the same place that meet it). The 95 percent interval comes from a cluster
bootstrap over places.

| Test | Edge Dollar General | Random sites, same places | D (95% interval) | Verdict |
|---|---|---|---|---|
| C1 On one of the two busiest roads crossing into town | 91 of 234 (39%) | 74.7 expected (32%) | +0.07 (+0.01 to +0.13) | holds |
| C2 Within 250 m of a junction of US or state routes | 40 of 234 (17%) | 13.6 expected (6%) | +0.11 (+0.07 to +0.16) | holds |
| C3 Inside the town's legal limits | 54 of 234 (23%) | 29.3 expected (13%) | +0.11 (+0.06 to +0.16) | holds |
| C4 Authorized for SNAP after 2005, edge against in-town Dollar General | 86% | in-town about 50% | +0.36 (+0.31 to +0.42) | holds |
| C5 Edge not crowded: of Dollar General within A 3, share in the edge band | 234 of 1,573 (15%) | 516.9 expected (33%) | −0.18 (−0.20 to −0.16) | holds; also holds on the homes-only edge (−0.15) |
| C6 Road past is busier (log AADT against the place's random edge points) | 1.32 times | | +0.28 (+0.18 to +0.38) | holds |

- **Decision rule (plan v2).** C1 and C2 both hold, so "the road in" stands as the line.
- **Wording gates.** No share has a lower bound above 50 percent. The copy must say "more
  often than other sites on the same roads", never "most" or "usually".
- **C3 in particular.** 77 percent of edge stores are *outside* the town limits. Virginia's
  "usually just inside the town line" does not carry over.

## Sensitivities (primary unit)

- **C2** holds in every one: S1 (100 m from the edge; band 0.75 to 2), S3 (A bins), S6
  (without odd shapes) and under 10,000 people.
- **C1** holds in S1, S2 (100 m match: 47 percent against 32 percent), S3 and under 10,000.
- **C1 cannot tell** in S4 (crossings on the store's side only: +0.056, −0.004 to +0.117) and
  in S6 (+0.075, −0.010 to +0.159).
- **So C1 is real but small and fragile.** C2 is the robust result.

## The stated contrast: convenience stores (same unit)

| Test | Edge convenience stores | D (95% interval) |
|---|---|---|
| C1 | 197 of 460 (43%) | +0.12 (+0.07 to +0.16) |
| C2 | 74 of 460 (16%) | +0.11 (+0.08 to +0.15) |
| C3 | 132 of 460 (29%) | +0.17 (+0.13 to +0.22) |
| C6 | 1.54 times | +0.43 |

Edge convenience stores show the same pattern as Dollar General, and at least as strongly.
Per the plan, the finding is "edge retail on the road in", not something particular to
Dollar General.

## Other units

- **Virginia CDPs (set A).** Only 8 edge stores. Every test is "cannot tell", except C2, which
  reads against (0 of 8) and has almost no power. C5 holds on the lead edge.
- **Set B CDPs (61 edge stores).** C2 holds (13 against 2.4 expected). C1 cannot tell. C4 and
  C5 hold.
- **Set B large incorporated places (125 edge stores in 53 places).** C2 holds weakly. C1 and
  C3 cannot tell. The edge of a big place is not a "road in".
- **Discovery recut (18 stores).** C2, C3, C5 and C6 hold. C1 and C4 cannot tell.

## By state (primary unit; descriptive only)

| | KY | MD | NC | SC | TN | WV |
|---|---|---|---|---|---|---|
| Edge stores | 57 | 5 | 54 | 31 | 68 | 19 |
| On a top-two road in | 49% | 0% | 33% | 39% | 37% | 42% |
| Near a junction | 23% | 40% | 15% | 19% | 16% | **0%** |

West Virginia's 0 of 19 is suspect and needs checking. It could be the junction rule meeting
WV's tagging, or US and WV routes sharing roads.

## Where every Dollar General sits (small incorporated places, all states)

Across the six states, about 1,100 Dollar General stores sit in town against 234 in the edge
band (KY 254/57, NC 314/54, SC 182/31, TN 303/68, WV 99/19, MD 45/5). Another 462 are beyond
A 2 of their nearest small place.

## The driver's view (exploratory; written after the frozen tests)

- **What was measured.** For each road crossing into a small place in set B, the stretch from
  twice the edge distance down to 0.75 of it: which store does a driver pass first?
- **Result.** Of 1,073 roads in with any store on that stretch:
  - The first store is a Dollar General on 30 percent.
  - Dollar General is 26 percent of all the stores on those stretches.
  - A Dollar General is somewhere on the stretch for 40 percent of roads in.
  - The first store is a convenience store or gas station on 53 percent.
- **Discovery Virginia.** 19 percent, 17 percent and 26 percent on the same three measures.

## Draft answer to "Why?"

1. **Most Dollar General stores are not at the edge.** In small towns there are about five
   in town for every one in the edge band. The edge band holds fewer of them than its share of
   road frontage would give (C5).
2. **The ones at the edge sit where highway retail sits:**
   - at junctions of US and state routes, three times as often as other edge sites (C2);
   - somewhat more often on one of the busiest roads in (C1, small effect);
   - on busier roads (C6).
   Convenience stores and gas stations are placed the same way.
3. **They are the newer stores** (C4). 86 percent of edge stores were authorized after 2005,
   against about half in town. The chain's expansion of the last twenty years added stores
   on the approaches.
4. **A driver sees them because of where they are.** On 4 in 10 roads into a small town
   there is a Dollar General in the approach stretch. On 3 in 10 it is the first store you
   pass. Only gas stations are first more often. (Exploratory.)
5. **What this cannot say.** Why the company chose these sites, land prices, and whether
   town rules (zoning, utilities) matter. Edge stores are more often inside the limits than
   random edge sites, but most are outside.
