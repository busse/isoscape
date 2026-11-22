# Step 12: a Hartfield tile, and the SNAP question (November 22, 10:20)

Chris, 10:20: "Show me what the square for Hartfield might look like. It is somewhat important for me
to include it, if it "works". Also, should we explore the SNAP angle more? Is there more
correlation/possible causation there? Perhaps from sources such as regulatory filings?"

## Hartfield

- **The store.** SNAP record 1153672, Dollar General 14349, 10989 General Puller Hwy (VA 33),
  Hartfield, Middlesex County, approved June 23, 2014.
- **Why it is not in the grid.** Hartfield has no Census place, so the rule scores the store
  against Deltaville CDP, 7.8 km from Deltaville's edge (A = 4.95, "farther out").
- **On the tile:**
  - 238 m from a junction of numbered routes, with 6,402 vehicles a day.
  - One convenience store beside it.
  - 596 homes in the 3 km square, and one block at 200 or more homes per square mile (it barely
    shows).
  - It reads as a crossroads store with no town around it.
- **Script.** `tools/stories/dollar-stores/hartfield_tile.py`.
- **Rounds.**
  - r1: geopandas put axis labels on the tile, and the note was cut off.
  - r2: fixed.

## SNAP (desk research and one check of our data)

- **Store-level SNAP redemptions are confidential.** *Food Marketing Institute v. Argus Leader
  Media* (2019) held them exempt from FOIA, so how much SNAP any store takes can't be measured
  from public data.
- **Byrne, Dong, Handbury, James, Meckel and Rovira (Wharton, November 20, 2025).**
  - Retailer participation in SNAP rose 67% from 2007 to 2012, after ARRA. Most new adopters
    were non-grocers, including dollar stores.
  - So a SNAP approval date can be an adoption date, which comes after the opening date.
- **Our data (set B, small places, Dollar General).** Dollar General was mostly authorized
  before the 2009 wave. 516 of the in-town stores carry 2004 (records start; "by 2005"), and the
  2009 to 2011 years show only a small bump (37, 31 and 33 in town). The edge stores cluster in
  2016 and later.
  - Reading: for this chain, the approval year is a fair stand-in for "arrived", with the caveat
    the poster already prints.
- **Filings.**
  - Dollar General's 10-Ks list changes to SNAP among the economic factors in their risk
    language.
  - The company says about 80% of its stores serve communities of 20,000 or fewer.
  - These tie SNAP to sales, not to where stores are put.
- **Studies.**
  - Caoui, Hollenbeck and Osborne: dollar store entry leads to grocery exits.
  - Marchesi, Steinbach and Lopez (USDA ERS): the effect is larger in rural tracts.
  - Both use private store data.
