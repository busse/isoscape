# Step 14: which towns get Dollar Generals. Hypotheses, written before any number

Written 10:50, November 22, 2026. Chris, 10:45: "Yes" (to testing whether towns with more SNAP
households have more Dollar Generals per household).

## The question

Across small towns, do towns where more households get SNAP have more Dollar General stores
per household? This can show a link only. SNAP share moves with income, poverty, age and how
rural a place is, and none of those can be pulled apart here.

## Sample

- **Primary.** Set B, the six held-out states: every small incorporated place scored in step 9
  (incorporated, active, under 25,000 people, not joined). This includes the places with no
  Dollar General.
- **Exploratory.** Virginia small places, reported separately, with no verdict.

## Measures

- **Stores.** Dollar Generals that belong to the place (each store once, at its lowest A, as in
  confirm.py) with A of 2 or less: in town, at the edge or on the edge line.
- **Households and SNAP share.**
  - Primary: ACS 2020-2024 5-year, B22010, for the place itself.
  - Sensitivity: households and SNAP share within 5 km of the place's population-weighted
    center, area-weighted from block groups as in step 13. This counts the people around the
    town who shop there too.

## Tests

- **T1 (primary).**
  - A Poisson regression of the store count on SNAP share, controlling for log households and
    the state.
  - Reported as a rate ratio for 10 more percentage points of SNAP share, with a 95%
    bootstrap interval over places (2,000 resamples, seed 20261121).
  - Holds if the interval is above 1, against if below, otherwise cannot tell.
- **T2.** The same with the 5 km measures.
- **T3 (contrast).**
  - Grocery stores, the same as T1.
  - Convenience stores, the same as T1.
- **T4 (descriptive).** Stores per 1,000 households by SNAP-share third, primary sample.

## What would change the poster

- **If T1 holds and T2 agrees,** the "Why?" could add a sentence about which towns get stores,
  worded as a link, and only after an independent check.
- **Otherwise,** nothing changes.

## Known limits

- **ACS margins** for places of a few hundred households are wide.
- **Stores near two towns** count once, for the town they are closest to (by A).
- **Places with no stores at all** are kept. That is the point.
