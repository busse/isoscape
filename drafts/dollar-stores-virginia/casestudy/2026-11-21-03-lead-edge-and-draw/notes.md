# Step 3: the lead edge and the editorial draw (November 21, 11:45-12:20)

## The lead edge: homes plus paved land

- **Rule.** A Census 2020 block is built up when it has 200 or more homes per square mile,
  or when 20 percent or more of it is non-road impervious cover. The pieces are closed over
  400 m gaps, and the piece holding the population-weighted center is kept. Both numbers
  follow the Census's 2020 urban-area rules.
- **Round 1 (folder `round1-impervious-with-roads/`).**
  - Used all impervious cover, NLCD 2021.
  - Marion's built-up area doubled to 23.5 km². The I-81 right-of-way blocks are nearly all
    pavement, so they chained the built-up area 10 km east along the interstate.
  - That pulled the Lee Highway Dollar General from 4.5 to 0.8, "in town".
  - Rejected.
- **Round 2 (folder `round2-non-road-impervious/`).**
  - Counted only NLCD's descriptor class 24, non-road non-energy impervious. Primary,
    secondary and tertiary road pixels were left out.
  - Marion: 13.5 km² built up. South Hill: 12.8 km². Chase City: 5.0 km².
  - Every supermarket and pharmacy now scores at or below 1.0. The highest is Castle's
    Butcher Shop in Chase City at 1.01.
  - South Hill's I-85 interchange cluster comes inside: Walmart 0.53, Dollar Tree 0.61.
- **Dollar General, three towns, lead edge.**
  - Six stores score 0.11 to 0.90.
  - Four score 3.07 to 5.28, between towns.
  - None scores between 1 and 2.
  - This is the same split as the homes-only edge.

## The editorial draw

- **Regions.** Five regions, each a group of Virginia's 21 planning district commissions.
  Membership comes from the VAPDC directory, opened 2026-11-21. The grouping and the five
  localities that belong to two commissions are in `tools/stories/dollar-stores/regions.json`.
  - The handoff's five regions left the central Piedmont out.
  - It was joined to Southside as "Piedmont and Southside", to keep five regions and 20
    towns. This is a judgment call to show Chris.
- **Pool.**
  - Every incorporated town and independent city under 50,000 people, using Census Vintage
    2024 estimates.
  - Census-designated places, which have no limits, are left out.
- **Bands.** Under 1,000; 1,000-2,499; 2,500-9,999; 10,000-49,999.
- **Draw.** Seed 20261121, one draw per cell.
- **The empty cell.** Northern Neck / Middle Peninsula / Eastern Shore has no place of 10,000
  or more. By the rule written before the draw ran, that cell was filled from the same band
  statewide, which gave Leesburg (49,831).
- **Result.** `data/editorial-draw.csv`; the pool is in `data/editorial-pool.csv`.
