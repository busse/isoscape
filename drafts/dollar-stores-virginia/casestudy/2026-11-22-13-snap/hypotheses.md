# Step 13: SNAP households near the stores. Hypotheses, written before any ACS number was computed

Written 10:45, November 22, 2026, before the block-group data was joined to a single store.
Chris, 10:27: "Set aside Hartfield for now. Continue with snap research. Also, is there store level
data before 2019?"

## The question

Do Dollar General stores at the edge of small towns sit among more households that get SNAP
than other spots along the same roads at the same edge? This can show a link only. It cannot
say a company chose a site because of SNAP, and it cannot say who shops at a store.

## Data

- **ACS 2020-2024 5-year estimates, table B22010, block groups.**
  - Households: B22010_001.
  - Households that received SNAP in the past 12 months: B22010_002.
  - Downloaded from the Census table-based summary file. Public domain.
- **Boundaries.** Census cartographic block groups, 2024, 1:500k, for KY, MD, NC, SC, TN, VA and
  WV.

## Measure

- **S(point).** The share of households that get SNAP within 3 km of the point. Each block
  group's households and SNAP households are counted in proportion to the part of its area
  inside the circle (area weighting).
- **Sensitivities, stated now.**
  - Radius 8 km (a short drive).
  - The single block group that holds the point.

## Sample

- **Set B only**, the six held-out states, small incorporated places: the same 234 edge Dollar
  General stores as the poster, and the same null points (random spots on trunk to tertiary
  roads, seed 20261121).
- **Null points.**
  - At most 400 per place per class (edge band; in town), drawn with the same seed, to keep
    the work small.
  - Only places that hold a store of the kind being tested.

## Tests (place-conditional, the plan v2 machinery)

- **S1 (primary).**
  - Edge Dollar General against the place's edge-band null points.
  - D = mean(S_store minus mean S_null in that place's edge band).
  - Cluster bootstrap by place, 10,000 resamples.
  - Holds if the interval is above 0, against if below, otherwise cannot tell.
- **S2.** In-town Dollar General against the place's in-town null points.
- **S3 (contrast).** Edge convenience stores, tested the same way as S1.
- **S4 (descriptive, no verdict).**
  - S for edge against in-town Dollar General.
  - S by approval period (by 2005, 2006 to 2015, 2016 and later).

## What would change the poster

- **S1 holds with a meaningful gap** (at least 1 percentage point): the poster could say edge
  stores sit among more SNAP households than other spots at the same edge.
- **S1 cannot tell or is against:** the poster says nothing about SNAP households beyond the
  approval-date chart.
- **Either way, the copy says "link", never "because".**

## Known limits, stated before running

- **Margins of error.** A block group's margin is large, and the 3 km circle pools several
  block groups, which helps.
- **Area weighting** assumes households are spread evenly within a block group.
- **Answers a narrow question.** It describes the people who live around a spot, and says
  nothing about the people who shop there.
