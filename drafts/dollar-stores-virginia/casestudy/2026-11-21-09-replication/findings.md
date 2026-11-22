# Why does it seem there's a Dollar General on the edge of town? Replication findings

Research draft made with Claude, November 21, 2026.

- **How it was tested.** Tests frozen before the data was read (plan v2), run once on held-out
  data, checked by an independent Fable agent (`fable-check.md`).
- **Not affiliated** with any company named.

## Scope

- **Places scored.** 3,966:
  - Virginia's 227 incorporated places (where the claims were found).
  - Virginia's 461 CDPs (held out).
  - Every incorporated place and CDP in NC, TN, KY, WV, MD and SC (held out).
- **The answer rests on** small incorporated places in those six states: under 25,000
  people, not joined to a bigger urban area. Within 8 km of them there are about 2,070
  Dollar General stores, of which 234 are at the edge.
- **Measures.** "Edge" is score A from 1 to 2: past the town's built-up edge, but within
  twice its distance from the center. Built-up means 200 or more homes per square mile, or
  20 percent or more paved non-road land.
- **Comparison.** Random points on main roads in the same edge band of the same towns.

## The answer

### 1. Most Dollar General stores are not at the edge

- Around small towns in the six states, about 1,200 are in town, 234 in the edge band,
  about 180 right on the edge line (within 30 m, counted in neither) and 462 farther out.
- Of the stores within A 3, the edge band holds 15 percent. It holds 33 percent of the main
  roads (C5, holds on both edge definitions).
- **What this means.** The edge is not where the chain concentrates. The feeling comes from
  something else.

### 2. The edge stores sit where other roadside stores sit

- **Junctions.** 17 percent are within 250 m of a junction of US or state routes. That is
  about three times the rate of random sites in the same edge bands, 6 percent (C2). This
  held in every sensitivity check.
- **Busiest roads in.** 39 percent are on one of the two busiest roads crossing into town,
  against 32 percent (C1). It holds on the frozen test but fails three of the sensitivity
  checks, so it is not robust.
- **Traffic.** The road past carries about 1.3 times the traffic (C6). That is among the
  three-quarters of stores with a traffic count.
- **Not particular to Dollar General.** SNAP convenience stores at the edge show the same
  pattern at least as strongly: 43 percent on a top-two road in, 16 percent at a junction,
  1.5 times the traffic.

### 3. The edge stores are the newer ones

- 86 percent of edge stores were authorized for SNAP after 2005, against 50 percent of
  in-town stores (C4).
- That is consistent with later building on the approaches. But authorization year is not
  opening year, so "expansion" is an inference.

### 4. The driver's view (exploratory)

- **Few roads.** Of about 6,800 roads crossing into these towns, about 6 percent have a
  Dollar General on the approach, from twice the edge distance in to just inside it.
- **Not placed ahead of others.** Where any food store sits on that stretch (1,071 roads),
  the outermost is a Dollar General 30 percent of the time. That is close to its 26 percent
  share of those stores.
- **Visibility.** The stores you pass are on the busy, numbered roads you drive, and the
  newer ones are out where those roads meet. That fits why they are noticed. It is not
  something counted here.

### 5. What this cannot say

- **Not measured.** Why the company chose these sites, what the land cost, and whether zoning
  or water and sewer matter.
- **Town limits.** Edge stores are inside the town limits more often than random edge sites
  (23 against 13 percent), but most (77 percent) are outside. Virginia's "just inside the
  town line" did not carry over.
- **West Virginia.** No edge store there is near a junction: 0 of 19, with 0.3 expected. The
  junction result rests on the other five states.

## Wording allowed by the gates

- **No "most" or "usually" about the edge stores.** No share's lower bound passes 50
  percent.
- **The copy says "more often than other sites on the same roads"** and gives the share.

## Units beyond the primary

- **Virginia CDPs.** 8 edge stores: cannot tell on anything.
- **Six-state CDPs.** 61 edge stores: junctions hold, the busiest-road test cannot tell.
- **Large towns.** The edge of a large town is not a "road in": C1 and C3 cannot tell.

## Not run

S5 (places inside a big metro they do not dominate). The urban-area file carries no
population, so the rule could not be applied as written.

## For the editorial line

- **Supported:**
  - The edge is not where Dollar General clusters.
  - The ones at the edge are highway-junction stores, placed like gas-station convenience
    stores.
  - They are mostly the newer stores.
- **Not supported:**
  - "On the busiest road in" as a headline (fragile).
  - "Just inside the town line" (Virginia only).
  - Anything about intent.
