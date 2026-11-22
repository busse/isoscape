# Step 13: findings. SNAP households near the stores (November 22, 11:05)

The tests are as stated in `hypotheses.md` (written 10:45, before any number). The script is
`tools/stories/dollar-stores/snap_test.py`, and the outputs are `snap_tests.csv` and
`snap_by_period.csv`.

## Store-level SNAP data: none public, before or after 2019

- **2011.** The Argus Leader asked USDA for each store's annual SNAP redemptions, fiscal years
  2005 to 2010. USDA refused.
- **2016 and 2018.** The newspaper won in district court (2016) and on appeal (May 2018). USDA
  told retailers the data might be released, but it was not.
- **2018.** Congress changed the law to bar USDA from disclosing store-level redemption data.
- **2019.** In *Food Marketing Institute v. Argus Leader Media* (June 24), the Supreme Court held
  the data confidential under FOIA Exemption 4.
- **What is public.** Redemptions by store type, nationally and by state (FNS Retailer
  Management Year End Summaries and dashboard). Dollar stores fall under "Combination
  Grocery/Other", which took about 5 to 6% of redemptions in 2016 to 2020, and they are not
  broken out.

## The test

| Test | Measure | Stores | Places | Stores' SNAP share | Random spots | Difference (points) | Verdict |
|---|---|---|---|---|---|---|---|
| S1 edge Dollar General (primary) | 3 km | 233 | 202 | 16.4% | 16.4% | -0.05 (-0.74 to 0.65) | cannot tell |
| S1 | 8 km | 234 | 203 | 16.4% | 16.4% | +0.06 (-0.21 to 0.34) | cannot tell |
| S1 | own block group | 224 | 195 | 15.4% | 15.4% | -0.01 (-1.24 to 1.26) | cannot tell |
| S2 in-town Dollar General | 3 km | 1,198 | 859 | 18.9% | 18.8% | +0.11 (-0.07 to 0.28) | cannot tell |
| S3 edge convenience | 3 km | 459 | 316 | 17.6% | 16.9% | +0.75 (0.20 to 1.28) | holds |
| S3 | 8 km, own block group | | | | | | cannot tell |

**Reading.**
- Edge Dollar Generals sit among the same share of SNAP households as other roadside spots at
  the same edge of the same town. The interval is tight: within about 0.7 points either way.
- Inside town it is the same.
- So within a town, where the store goes is not explained by SNAP households nearby. The
  stated threshold for any poster claim (1 point, interval above 0) is not met.
- Convenience stores at the edge sit in slightly higher-SNAP surroundings at 3 km only. That
  result does not hold at the other two measures, so it is not robust.

**Descriptive (no verdict).**

| Where | Approved | Stores | 3 km SNAP share (mean) |
|---|---|---|---|
| At the edge | by 2005 | 32 | 18.7% |
| At the edge | 2006 to 2015 | 51 | 17.4% |
| At the edge | 2016 and later | 151 | 15.5% |
| In town | by 2005 | 597 | 20.2% |
| In town | 2006 to 2015 | 260 | 16.8% |
| In town | 2016 and later | 341 | 18.3% |

The newer edge stores sit among a somewhat lower share of SNAP households than the older ones.
This mixes different towns, so it is a description, not a test.

## What this means for the "Why?"

- The SNAP link to Dollar General is real at the level of the company's sales: its 10-K risk
  language, and the 2026 guidance that cited SNAP cuts.
- It is not visible in where a store sits within a town.
- The edge pattern stays a roads-and-timing story: junctions, the busier road in, and newer
  stores.
- The question SNAP might still answer is a different one. **Which towns** get stores at all
  (town-level SNAP share against Dollar General stores per household), not where in town.

## Not done

- No independent review yet. This is a null result and changes no poster text. If any SNAP
  number goes on the poster, it gets checked first, as the six-state results were.
