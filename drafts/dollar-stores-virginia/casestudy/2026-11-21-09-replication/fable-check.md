# Independent check of the replication findings (Fable)

- **Who checked.** The same independent Fable agent that reviewed the plan. It did not
  produce the results.
- **What it did.** It recomputed the primary table from the row-level data with its own code
  (`fable-check-scripts/`). It also rebuilt the junction distances for all 201 primary places
  (0 mismatches), and checked West Virginia, the driver's view and every sentence of the
  draft's "Why?".
- **Timing.** Finished November 21, 2026, about 20:45.

## Its verdict

- The frozen-test table reproduces. Every primary verdict stands, and C2 (junctions) is solid.
- C1 holds only by the letter of the plan and is weaker than the draft said.
- The driver's-view paragraph was wrong as worded: its "4 in 10 roads in" is about 6 in 100
  of all roads in.

## What it found, and what was done

| Finding | Severity | Done |
|---|---|---|
| Driver's view denominator: only roads with a matched SNAP store were counted (1,071 of 6,758 roads in) | high | Reworded: 6% of all roads in have a Dollar General on the approach; the 30% "outermost" figure is stated only for roads with any food store on that stretch |
| drive_in.py does not measure "first store passed": 57% of its "first" stores are inside the edge, 64% of roads have one store, a route number merges both approaches, order is radial | high | Dropped as evidence. The data do not show Dollar General placed ahead of other stores (30% outermost against a 26% share) |
| C1 is fragile: fails S4, S6 and a symmetric check; not different from convenience stores | medium | Findings call C1 "holds on the frozen test, not robust" |
| Store and random points not treated alike: stores go to one place, random points do not | medium | Reported as a sensitivity. C2, C3 and C5 survive it |
| S5 (metro suburbs) was in plan v2 but not run | medium | Stated as not run. The 2020 urban-area file carries no population, so the rule could not be applied as written |
| Unstable tie-break: 459 stores tie at their lowest A in two places | medium | Fixed: ties go to the larger place, then the lower GEOID, with a stable sort. 234 stores under this rule; the checker's rule gives 232. Verdicts unchanged |
| C4 measures SNAP authorization year, not opening year | medium | Worded as "newer SNAP authorizations"; "expansion" is inference |
| "Convenience stores and gas stations" | low | Changed to "SNAP convenience stores" |
| Set A C5 holds on the lead edge only (fails M6) | low | Corrected |
| Tennessee tags one route as both "SR n" and "TN n" | low | A stricter rule changes nothing: 39 against 13.1 expected |
| West Virginia's 0 of 19 junctions | checked | Real, not an artifact. Expected is 0.3, so 0 is unremarkable |

## Its corrected answer to "Why?" (adopted, with the tie-break numbers)

See `findings.md`.
