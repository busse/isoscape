# Traffic at the edge stores (November 21, 13:06-13:24)

Research draft made with Claude. The tests were written in `hypotheses.md` (13:08) before any
count was fetched. Traffic: FHWA HPMS 2024 "Spatial All Sections", Virginia, functional
system 1 to 6, public domain. Of the matched counts, 1,760 are dated 2024, 3 are 2022 and 1 is
2017. Every number below was read back from `data/`.

## Test 1: busier road than the other sites in the band

Median vehicles a day on the road past the site:

| Group | Median | 95% interval | Random edge sites | Result |
|---|---|---|---|---|
| Edge Dollar General, all (30 of 34 counted) | 6,210 | 4,926-9,677 | 2,955 | busier, about twice |
| In towns (16 counted) | 5,851 | 2,891-9,667 | 3,139 | can't tell |
| In cities (14 counted) | 8,488 | 4,592-14,254 | 2,475 | busier |
| Edge supermarkets and groceries (8 of 28 counted) | 9,161 | | 2,955 | busier |
| Edge convenience stores (92 of 106) | 7,003 | | 2,955 | busier |

- **Every kind of store is on the busier roads.** That is ordinary retail siting, not
  something special to Dollar General.
- **Unmatched stores.** Supermarkets often sit back from the road behind parking, more than
  60 m from the counted line, so most have no match.

## Test 2: on the busiest road into town

The roads crossing each place's built-up edge are ranked by traffic where they cross.

| Group | On the busiest | On one of the top two | Random: busiest / top two |
|---|---|---|---|
| Edge Dollar General, all | 10 of 34 | 14 of 34 | 20% / 32% (can't tell) |
| In towns | 9 of 18 | 13 of 18 (72%, interval 49-88%) | 29% / 47%: top two **supported** |
| In cities | 1 of 16 | 1 of 16 | |

- **In towns, 13 of 18 edge Dollar General stores are on one of the two busiest roads into
  town.** For the other sites in the same band it is 47 percent. This is the town and city
  split that step 6 found by exploring. Here it was stated before the counts were fetched, and
  it holds.

## Test 3: traffic when the store came

- **The stores.** Edge Dollar General stores authorized 2011 to 2017. Of these, 9 have a count
  then and now.
- **Then and now.**
  - The change since then runs from -27 percent (Tazewell) to +82 percent (Drakes Branch,
    935 to 1,699 a day).
  - Most are within 10 percent: Lynchburg +7, Roanoke +6, South Boston +6, Martinsville 0,
    Richmond -10.
- **What it means.** The roads were already about as busy when the stores came. The stores
  went to busy roads; the roads did not grow up around them.
- **A data problem at the source.** FHWA's 2016 Virginia file is cut off. Its table declares
  4.38 GB and holds 2.15 GB, so no reader opens it. The four stores authorized in 2016 use
  the 2015 count, the year before, and are marked so.

## The heat map

- **The map.** `heat-towns-r2.png` shows the 18 town edge stores. Each is a 3 km square, with
  roads shaded and widened by 2024 traffic in five classes.
- **The ramp.** It passed the dataviz validator's ordinal checks after the light end was moved
  from #9ec5f4 (1.74:1 against the background, a fail) to #86b6ef.
- **Rounds.**
  - Gallery r1: the legend sat over the last row of tiles, and the footnote ran off the right.
    r2 fixed both.
  - Chart r1: the "14 counted" label sat under the cities interval. r2 moved the counts into
    the row labels.

## What this adds to the edge story

In towns, the edge Dollar General is on the road most people take into town, at or near a
junction, and usually just inside the town line. Every one of those roads was already busy
before the store came.
