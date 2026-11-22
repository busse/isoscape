# Why are the edge stores where they are? Hypotheses, written before looking

Written with Claude on November 21, 2026 at 12:45. That is before any edge store statewide
was scored or any reason was measured. Chris, 12:40: "We really want to focus an editorial in
the edge of town ones. Explore the idea of the non-edge locations as irrelevant, why are the
edge ones where they are?"

## Which stores count as edge stores

- **Places.** Every incorporated town and independent city in Virginia (189 towns and 38
  cities), scored with the lead edge. The lead edge is 200 or more homes per square mile, or
  20 percent or more non-road impervious cover. The tiny-town rule applies. Places joined to
  a larger urban area are left out.
- **Edge stores.** Dollar General, Family Dollar and Dollar Tree stores (USDA SNAP, still
  authorized) with score A from 1 to 2. That is past the built-up edge, but within twice its
  distance from the center. A store seen from two places counts once, at its lowest score.
- **Sensitivity check, reported but not the lead.** The band 0.75 to 2.

## What they are compared with

- **R.** Random points on main roads (trunk, primary, secondary, tertiary) in the same edge
  band of the same places. Each place is weighted by its number of edge stores. These are the
  sites a store at the edge could have taken.
- **G.** Edge-band supermarkets, groceries and convenience stores.
- **T.** In-town Dollar General stores (A at or below 1), for the store-age question only.

## Reasons, and what would count as support

Each reason is supported when the share among edge chain stores is above R's share, and
R's share falls outside the stores' 95 percent interval (Wilson). It is contradicted when
R's share is above the interval. Otherwise the data cannot tell.

1. **The road into town.** The store is within 60 m of a US or state primary or secondary
   route (OSM trunk, primary or secondary) that crosses the built-up edge.
2. **A crossroads.** Within 250 m of a point where two different US or state routes meet,
   leaving out VDOT's "SR 6xx" numbers. Points where two numbers share one road (concurrent
   routes) do not count as junctions.
3. **Outside the town limits.** The store is in county land, not inside the town's legal
   limits. Town zoning, town taxes and town approval would not apply there. The data can say
   where the line is. It cannot say why a builder chose either side.
4. **Built on open land after 2001.** The store's site (the 3 x 3 pixels around it) was under
   10 percent impervious in NLCD 2001 and is 20 percent or more in NLCD 2021. That points to
   a new build on open land, which the company's 10-K describes as build-to-suit leases.
   NLCD 2001 vs 2021 cannot say what the land cost.
5. **Reaching the people outside town.** Of the people living within 5 km of the site by
   road, the share living outside the built-up area. Edge stores against R.
6. **The other side of town from the supermarket.** The angle at the town's center between
   the store and the nearest supermarket is more than 90 degrees. Edge stores against R.
7. **Newer than the in-town stores.** The share authorized for SNAP after 2005 (dates of 2004
   and 2005 mean "already authorized when the file starts"). Edge Dollar General against T.

## What this cannot show

- **Intent.** Nothing here says why a company chose a site. The company's own words and the
  research literature are quoted for that, with sources.
- **Land prices.** Parcel values are not available statewide.
- **Traffic counts.** VDOT's license limits use to the official business of the
  Commonwealth. Road class stands in for traffic.
