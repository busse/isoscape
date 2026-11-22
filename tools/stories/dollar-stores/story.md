---
title: Dollar General on the edge of town
deck: Every Dollar General near a small town in six states, compared with random spots on the same roads, and every one at the edge of a small Virginia town on a map.
order: 65
summary: Why it always seems like there's a Dollar General on the edge of town, checked against public data, and how we know. A draft for review.
unlisted: true
social: dollar-stores-social.jpg
---

# Why does it always seem like there's a Dollar General on the edge of town?

> **Draft for review.** This page is not listed on the site. The numbers were checked against
> their sources on November 22, 2026. Made with Claude for Chris Busse, {{date}}. This work is
> independent, and it is not affiliated with any company named on this page.

Most Dollar General stores near small towns are in town. We counted every Dollar General near
a small town in six states that border or sit close to Virginia. Of the {{total}} stores,
{{edge}} stand just outside the built-up part of town, about one in {{one_in}}. Those {{edge}}
tend to be on the busier roads coming in, and they are about {{junction_x}} times as likely as
a random roadside spot at the same edge to be within 800 feet of a spot where two US or state
highways cross. Convenience stores do the same thing. The edge stores are also newer. These are
the roads people use to get into town, which may be why the edge stores seem so common.

Chris Busse asked the question. This page explains how we checked it, what we found, and what the data can't say. The
poster below shows the results, and [How we know](#how-we-know) covers the method.

::: figure wide
![The poster: the question as a headline, a short answer, a grid of 30 small square maps of Virginia stores at the edge of town grouped by region, a locator map of Virginia, and three charts](dollar-stores-poster.webp)

The poster, 24 by 36 inches. Every number on it is computed from the test results; none is
typed in. *How this was made:* drawn in code with Claude from public data, listed under
[Sources](#sources).
:::

## How many stores are at the edge

To say a store is "at the edge," we need a line for where a town stops. We started at the spot
where most of a town's people live and worked outward, block by block, using 2020 Census
counts of homes and the U.S. Geological Survey's map of paved and built-on land. The built-up
part of town ends where there are fewer than 200 homes per square mile and less than a fifth of
the land is built on or paved (not counting roads). A store is "at the edge" if it is past that
line but less than twice as far from the center as the line is.

We first saw the pattern in Virginia. To check it wasn't a fluke, we wrote the tests down ahead
of time and then ran them on six other states: North Carolina, Tennessee, Kentucky, West
Virginia, Maryland and South Carolina. In those states there are {{total}} Dollar Generals near
small towns (incorporated places with fewer than 25,000 people). {{town}} are in town, {{edge}}
are at the edge, {{margin}} sit right on the edge line, and {{farther}} are farther out.

If the stores had been dropped at random spots along the same main roads, about
{{band_expected}} of those within twice the distance to the edge would have landed in the edge
band. Only {{band_share}} did. So the edge has fewer Dollar Generals than chance would give it.
The impression that they are always at the edge does not come from their numbers.

## The Virginia maps

::: figure wide
![Twelve of the 30 small square maps from the poster, from Bristol to Oak Level, each with a yellow square for the store, roads colored by traffic and a gray area for the built-up town](dollar-stores-tiles.webp)

The first two rows of the poster's grid. Each map is 3 km (1.9 miles) across, with north at the
top. The yellow square is the store, and the arrow points toward the middle of town. Roads are
colored by how many vehicles use them on an average day in 2024 [[FHWA HPMS](#sources)]. Under
each name: the year the store was first approved for SNAP, the traffic on its road, and whether
it is on one of the two busiest roads into town or at a junction.
:::

The poster maps every Dollar General at the edge of a small Virginia town or community,
{{va_grid}} stores in all, with none left out. They are grouped into five regions made from
Virginia's planning districts and run from west to east. Some fit the pattern well. Others sit
on quiet roads with no junction nearby. Showing all of them, including the ones that don't fit,
is the point of the grid.

## What the edge stores sit next to

::: figure wide
![The poster's three charts: the stores counted by where they sit, three measures of what the edge stores sit next to compared with random spots, and the share approved for SNAP after 2005](dollar-stores-charts.webp)

The poster's charts, for the six states. In the middle chart, yellow squares are the edge Dollar
Generals with a gray line for the margin of error, black ticks are random spots on the same roads
at the same edges, and open circles are convenience stores at the edge.
:::

We compared the {{edge}} edge stores with random spots on the same main roads at the edge of
the same towns, so every store is measured against its own town.

- **Highway crossings.** {{junction}} of the edge stores are within 250 m (about 800 feet) of a
  spot where two US or state highways cross. The random spots give {{junction_exp}}. That is the
  clearest difference we found, and it held up under every check we ran on the six states. Convenience stores at
  the edge come in at {{junction_conv}}.
- **The busiest roads in.** {{busiest}} are on one of the two busiest roads into town, against
  {{busiest_exp}} for the random spots ({{busiest_conv}} for convenience stores). This held up in most of our checks
  but not all of them.
- **Traffic.** On average, the road in front of an edge Dollar General carries about
  {{traffic_x}} times as much traffic as the random spots.
- **Town limits.** {{inside}} of the edge stores are inside the town limits, against
  {{inside_exp}} for the random spots, so they lean toward the inside. Still, most of them
  ({{outside}}) are outside the limits. In Virginia most edge stores were just inside the town
  line, so this part of the picture changes from state to state.

Convenience stores land in nearly the same places. Whatever puts a Dollar General near a
highway crossing seems to put a convenience store there too. The pattern isn't
the same everywhere, though. In West Virginia, none of the {{wv_edge}} edge stores is near a
highway crossing.

## How new the stores are

{{new_edge}} of the edge stores were first approved to take SNAP benefits after 2005, compared
with {{new_town}} of the stores in town. SNAP is the federal food program that used to be
called food stamps, and USDA publishes every approved store with the date it was approved
[[USDA SNAP Retailer Locator](#sources)]. An approval date can come later than an opening date.
Around the 2009 stimulus, the number of stores taking SNAP rose 67% from 2007 to 2012, and most
of the new ones were stores other than grocers, such as dollar, drug and convenience stores
[[Byrne and others 2025](#sources)]. In our data, Dollar General's approval years show no large
jump in 2009, and the edge stores cluster in 2016 and later, so the approval year works as a
rough stand-in for when a store arrived. The records only go back to 2005.

## Does SNAP explain it?

We checked two ways, writing each test down before running it.

**Inside a town.** Using the Census's 2020–2024 estimates, we measured the share of households
within 3 km that received SNAP in the past year [[ACS B22010](#sources)]. Around the edge Dollar
Generals it is {{s1_store}}. Around random spots on the same roads at the same edges it is
{{s1_null}}. The difference is within {{s1_gap}} percentage points either way, which is too small
to matter. In town it is the same ({{s2_store}} against {{s2_null}}). Where a store sits inside a
town does not follow where SNAP households live.

**Across towns.** In {{t_places}} small towns, towns where more households get SNAP do have more
Dollar Generals for their size: about {{t1}} times as many per household for every 10 more
percentage points of SNAP households ({{t1_lo}} to {{t1_hi}}), comparing towns of the same size
in the same state. But they also have more grocery stores ({{t_grocery}} times) and convenience
stores ({{t_conv}} times). In the third of towns with the fewest SNAP households there are
{{third_lo_dg}} Dollar Generals and {{third_lo_gr}} grocery stores per 1,000 households. In the
third with the most, there are {{third_hi_dg}} and {{third_hi_gr}}. Towns where more families use
SNAP have more food stores of every kind for their size. That doesn't explain the edge.

We could not measure how much SNAP money any one store takes in. USDA does not release
store-level redemption data. A South Dakota newspaper asked for it in 2011 and won in the lower
courts, but in 2018 Congress changed the law to bar its release [[Pomeranz 2019](#sources)], and
in 2019 the Supreme Court held that the data is confidential [[FMI v. Argus Leader](#sources)].

## What the data can't show

The maps show where the stores are. Why the company chose a particular site is not in the data.
Things like zoning and water and sewer lines would matter, and neither is included. Dollar General
says about 80% of its stores serve communities of 20,000 or fewer people
[[Dollar General](#sources)], which fits a chain built around small towns but doesn't say
where in a town it builds. A yellow square marks a location only. It is not a judgment of any
store or town.

Other researchers have studied what happens after a dollar store opens. They found that
independent grocery stores are more likely to close, and more so in rural areas
[[Caoui, Hollenbeck and Osborne](#sources); [USDA ERS 2024](#sources)]. Those studies use private
store data we don't have, and this page takes no position on them.

## How we know

- **Stores.** Every store from USDA's SNAP Retailer Locator historical file (2005–2025), with
  duplicates of the same store removed. A store that doesn't take SNAP is missing. We did not use
  any company's store locator.
- **The edge.** Built from 2020 Census blocks (homes per square mile) and the 2021 National Land
  Cover Database (built-on and paved land, roads left out). Gaps of up to about 800 m between built-up pieces
  are filled in. A store
  within 30 m of the edge line is counted as "on the edge line" and left out of the tests. When a
  store is near two towns, it counts once, for the town it is closest to by this measure.
- **Random spots.** Points on trunk, primary, secondary and tertiary roads from OpenStreetMap, in
  each town's own edge band, drawn with a fixed seed so the run can be repeated.
- **Traffic and junctions.** Annual average daily traffic from the Federal Highway
  Administration's 2024 Highway Performance Monitoring System. A junction is a spot where two
  US or state highways meet.
- **Testing.** The tests and what would count as a result were written down before any data from
  the six states was opened. Each result is the average difference between a store and its own
  town's random spots, with a margin of error from resampling whole towns 10,000 times. A
  separate review, also run with Claude, read the plan before the run and redid the calculations
  from scratch afterward. It found a mistake in one exploratory number, which was corrected and is
  not used here.
- **The record.** Every step, including dead ends, is kept in the project's case study
  (`drafts/dollar-stores-virginia/casestudy/`). The scripts are in
  `tools/stories/dollar-stores/`: `measure.py` (the edge), `confirm.py` (the tests),
  `snap_test.py` and `snap_towns.py` (SNAP), `poster.py` (the poster) and `counts.py` (this
  page's numbers).

## Sources

- **USDA SNAP Retailer Locator** historical data, 2005–2025. USDA Food and Nutrition Service.
  https://www.fns.usda.gov/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip.
  Public domain.
- **FHWA HPMS:** Highway Performance Monitoring System, 2024 spatial data, all sections. Federal
  Highway Administration, via https://data.transportation.gov/. Public domain.
- **Census 2020 blocks** (homes and people), TIGER/Line places 2024, cartographic boundaries 2024.
  U.S. Census Bureau. Public domain.
- **ACS B22010:** American Community Survey 2020–2024 5-year estimates, table B22010, receipt of
  food stamps/SNAP. U.S. Census Bureau. Public domain.
- **NLCD 2021** impervious surface and descriptor. U.S. Geological Survey and MRLC. Public domain.
- **OpenStreetMap** roads, © OpenStreetMap contributors, ODbL.
- **Virginia planning districts:** Virginia Association of Planning District Commissions,
  https://www.vapdc.org/pdc-directory.
- **Byrne and others 2025:** Anne T. Byrne, Xiao Dong, Jessie Handbury, Erik James, Katherine
  Meckel and Andrés Rovira, "SNAP chain expansion" working paper, November 20, 2025,
  https://realestate.wharton.upenn.edu/wp-content/uploads/2025/12/SNAP_chain_expansion_CurrentPublic.pdf.
- **Pomeranz 2019:** Jennifer L. Pomeranz, "Supplemental Nutrition Assistance Program Data: Why
  Disclosure Is Needed," *American Journal of Public Health* 109(12), 2019,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6836781.
- **FMI v. Argus Leader:** *Food Marketing Institute v. Argus Leader Media*, No. 18-481 (U.S.
  June 24, 2019).
- **Dollar General:** "Here for What Matters: How DG Chooses Store Locations," company news
  release,
  https://newscenter.dollargeneral.com/news/here-for-what-matters-how-dg-chooses-store-locations/3fcd5a78-37f6-43da-95f5-8e12ad8f8749.
- **Caoui, Hollenbeck and Osborne:** "The Impact of Dollar Store Expansion on Local Market
  Structure and Food Access," July 31, 2025 version,
  https://www.anderson.ucla.edu/sites/default/files/document/2025-08/caoui_hollenbeck_osborne_dollarstores_foodaccess%20(1).pdf.
- **USDA ERS 2024:** Keenan Marchesi, Sandro Steinbach and Rigoberto A. Lopez, "Dollar Store
  Entry Affects Rural Grocery Stores More Than Urban," *Amber Waves*, May 6, 2024,
  https://www.ers.usda.gov/amber-waves/2024/may/dollar-store-entry-affects-rural-grocery-stores-more-than-urban.

## How this page was made

Chris Busse asked the question and directed the work. The research, the tests, the poster and
this page were made in code with Claude, and every number on the page is filled in from the
results files by `tools/stories/dollar-stores/page.py`. See the
[artist statement](artist-statement.md) for how Chris works with isoscape and Claude.
