# Independent review of the replication plan (Fable)

- **Who reviewed.** A separate agent on Claude Fable 5.2 that had not seen the work being
  produced. It read the frozen plan (`plan-v1-as-frozen.md`), steps 5 to 7, the code and the
  Virginia discovery data.
- **What it was kept from.** It was told not to open the held-out Virginia CDP results or
  any replication state. It reports that it did not.
- **Timing.** Finished November 21, 2026, about 16:05. Its scripts are kept in
  `fable-review-scripts/`.
- **Text.** Its report follows as delivered, with its formatting.

---

METHODS REVIEW: replication plan (2026-11-21-09), read cold. Nothing in work_cdp, osm_cdp or the CDP logs was opened.

1. VERDICT

Not ready to run as frozen. The design is sound (pre-stated claims, held-out data, same-place null), but the plan's discovery column is not computed on the plan's own unit, the Wilson-vs-fixed-share test is the wrong test, and the junction rule and several scripts are Virginia-specific. All fixes are small and need no held-out data.

2. MUST-FIX BEFORE RUNNING

M1. The discovery column is for legal towns, not "small incorporated places".
- Problem: the table is labelled "small towns" but shows the 18 legal-town stores. Under the under-25,000 rule Virginia has 23 edge stores (Galax, Martinsville and Bristol add 5).
- Why: recut numbers are weaker. C1 is 14/23 = 61% (41-78) vs random 40%, which clears by one point. C2 is 6/23 = 26% (13-46) vs 6%. C3 is 52% outside vs 85%.
- Fix: put the recut numbers in the plan. State under-10,000 as a sensitivity now (Virginia: 74% vs 47%, 32% vs 7%, 42% vs 83%) and say it was picked on Virginia.

M2. The sentence is absolute; the tests are relative.
- Problem: "usually just inside the town line" needs more than half inside; the recut has 11 of 23. "Near a junction" describes a quarter to a third of stores. With about ten times the sample, any small gap over random will "hold".
- Fix: add wording gates. "Usually" or "most" needs the interval's lower bound above 50%. Otherwise the copy says "more often than other sites" and gives the share.

M3. Replace Wilson-vs-pooled-random with a place-conditional test.
- Problem: the random share is treated as a constant, though it varies by place (crossing roads per place run 2 to 91, median 7.5) and comes from only 40 points per store. Stores sharing a place or overlapping windows are not independent.
- Fix in traffic.py and reasons.py: for each store, p_i is the share of all in-band null.csv points of its place that meet the claim. The statistic is mean(x_i - p_i), with a cluster bootstrap by place. "Holds" means the interval excludes 0. This also answers the 2-vs-12-roads question without rank percentiles.
- Virginia towns under this test: C1 is 13 observed vs 8.7 expected, interval -0.01 to +0.45, so it does not clear. C2 is 6 vs 1.2, interval +0.06 to +0.49. C3 is 7 vs 14.3, interval -0.58 to -0.24.
- So C1 is the fragile primary claim; say so in the plan.

M4. The junction rule is Virginia-specific.
- Problem: `not startswith("SR")` drops Virginia and North Carolina secondaries as intended. It keeps West Virginia "CR" county routes, Kentucky's four-digit rural routes and South Carolina "S-" secondaries, and it drops any state route tagged "SR n". I could not confirm how Tennessee is tagged; the search was inconclusive.
- Fix: tabulate ref prefixes by highway class per state before the run (no outcomes involved). Then use an allowlist, `^(US|<state postal codes>) \d+`, with the Kentucky and West Virginia secondary handling written down. Report each state's random junction rate.

M5. The built-up edge runs along roads.
- Problem: block boundaries are roads. 90 of the 237 HPMS sections "crossing" the 18 town edges run more than 100 m along the edge. 7.4% of random band points have A between 1.00 and 1.02, so their band membership is a coin flip.
- Virginia survives: all 13 top-two stores stay top-two with those sections dropped. Other states may not.
- Fix: a section crosses only if it has length both inside `edge.buffer(-30)` and outside `edge.buffer(30)`. Apply the same 30 m margin to band membership for stores and random points.

M6. C5 is partly made by the stores' own pavement.
- Problem: 27 of 264 in-town Dollar Generals are in town only through the impervious rule. On the loose edge the fringe share is 47/300 = 16%, not 11%. Random points carry no pavement.
- Why: C5 gates the fallback line.
- Fix: report C5 on both the lead and loose edges and require the same verdict.

M7. Code that breaks or leaks outside Virginia.
- pool.py hardcodes `tl_2024_51_place.zip` for "another place".
- traffic.py derives `is_town` from a name-slug dictionary. Belle Haven and Wakefield already collide in Virginia, and GEOID folder names never match it. Switch both to GEOID and the population rule.
- The HPMS and place layers must include neighbouring states for windows that cross a line.
- Dedupe must run across all states at once.
- Exclude from replication any store within 8 km of a Virginia incorporated place, since it was already seen.

3. SHOULD-FIX

S1. Geocode error.
- OSM vs SNAP Dollar General positions (312 pairs within 500 m): median 50 m, 90th percentile 133 m, 40% over 60 m.
- Six of the 34 edge stores are under 100 m beyond the edge; 10 in-town stores are under 100 m inside.
- Fix: state a sensitivity dropping stores within 100 m of the edge, and report the 0.75-2 band.

S2. The 60 m HPMS match sits on the store setback.
- Five of the 13 top-two town stores match at 52-60 m. Random points match at a median 0.7 m.
- Unmatched stores count as failures in C1 (conservative) but drop out of C6.
- Fix: report match rates by state and a 100 m sensitivity. Keep nearest-section; "best rank within radius" would favour corner stores.

S3. Radial position.
- Stores hug the inner band: median A is 1.27 vs 1.46 for random.
- The random outside-limits rate is 61% at A 1-1.25 and 95% at 1.5-2.
- A-matched random shares move little in Virginia (C1 48%, C2 8%, C3 77%).
- Fix: stratify p_i by A bin, mainly for C3.

S4. C1 rank.
- A route takes its maximum AADT over all its crossings, so a store on the quiet side inherits the busy side's rank. Add a sensitivity using crossings within 90 degrees of the store's bearing.
- `road_id` ignores route signing, so US 11 and SR 11 would merge. Add signing to the key.

S5. Joined-town rule.
- The 5x and 30 km2 thresholds were set on Virginia (Winchester stays in).
- Where annexed limits are large, a suburb inside a metro will not reach 5x and will take the metro's edge.
- Fix: a sensitivity excluding places whose center lies in a 2020 urban area of 50,000 or more that they do not dominate.

S6. Score A.
- The ray takes the farthest exit, so stores in notches between lobes count as in town.
- With the center-in-a-gap fallback, bearings that miss the piece give A = infinity.
- Fix: log per place whether the fallback fired and how many rays re-enter. List those places and rerun without them.

S7. Other comparisons.
- C6 and C1 are not specific to Dollar General; convenience stores show the same. Promote the convenience-store comparison from descriptive to a stated contrast.
- Say what a CDP failure would change; at present, nothing.

4. FINE AS IS

- Hypotheses written first; fixed seed; a two-sided interval for a one-sided claim (conservative).
- Requiring both C1 and C2, with no correction.
- Same-place random points on main roads as the frontage null. Being exactly on the road makes C2 conservative.
- No state-level tests; C3 limited to incorporated places.
- UTM 17N for western Tennessee and Kentucky: about 0.8% scale error, negligible.
- Clustering within Virginia towns: 18 stores in 18 places.

5. CHECKS RUN (Virginia discovery only)

- Under-25,000 recut: 23 stores. C1 14/23 (41-78) vs 40%; C2 6/23 vs 6%; C3 12/23 outside vs 85%. Median AADT 5,807 vs 3,088.
- 25,000 and over: 0/11 top-two; 10/11 outside.
- Place-conditional test, towns: C1 one-sided p = 0.021, cluster interval -0.01 to +0.45. C2 p = 0.0006.
- Rank present: stores 72%, random 68%. AADT match: stores 88%, random 85%.
- Edge-following sections: 90 of 237. Top-two stores surviving their removal: 13 of 13.
- No HPMS route_number is "0"; 5% are blank and fall back to the road name.
- Scripts used are in /tmp/rev/ (c1.py to c4.py); nothing was written to the repo.
