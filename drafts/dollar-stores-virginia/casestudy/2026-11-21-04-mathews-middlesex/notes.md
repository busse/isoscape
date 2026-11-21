# Step 4: Mathews and Middlesex, store first (November 21, 11:53-11:59)

Chris, 11:53: "Ensure that you specifically include Middlesex and Mathews. It may be, find
DGs, infer centroid of why they are there. I'm just spitballing here."

Neither county fits the town rule. Mathews has no incorporated town, and Middlesex has only
Urbanna, which has no Dollar General. Both counties are added as the owner's choice. They are
labeled that way and kept apart from the seeded 20.

## Method: who lives nearest each store, by road

- **Catchments.** Every 2020 block in a window over the Middle Peninsula and lower Northern
  Neck goes to the Dollar General nearest it along OpenStreetMap roads. That covers 30 Dollar
  General stores, so stores in neighboring counties compete for the edge blocks too. A
  store's catchment is the set of blocks it wins. Rivers without bridges separate
  catchments, as they do on the ground.
- **Population center.** For each store, the population-weighted center of its catchment.
- **Distances.**
  - Store to that center, straight and by road.
  - Median road distance from residents to the store.
  - Nearest supermarket or grocery, by road.
  - Nearest other Dollar General, by road.
- **Script.** `tools/stories/dollar-stores/catchment.py`. Map: `catchment_map.py`.

## What it shows (seven stores, one region: a first look, not a finding)

| Store | SNAP year | Inside a Census place | Grocery by road | Catchment people |
|---|---|---|---|---|
| Mathews | 2005 | Mathews CDP | 0.6 km | 3,519 |
| Deltaville | 2005 | Deltaville CDP | 0.3 km | 2,072 |
| Saluda | 2007 | Saluda CDP | 0.4 km | 5,236 |
| Hartfield | 2014 | none | 7.7 km | 2,455 |
| Hudgins | 2017 | none | 4.8 km | 2,952 |
| Dutton | 2023 | none | 12.5 km | 3,247 |
| Topping | 2025 | none | 12.8 km | 1,584 |

- **Two kinds of store.** The three oldest are in the villages (the county seats of Mathews
  and Middlesex, and Deltaville), beside the grocery. The four added since 2014 are outside
  any Census place, 4.8 to 12.8 km from a grocery by road. They sit between the older stores.
  This is the handoff's "older in town, newer out on the road" hypothesis, seen in one region.
- **Not at the edge of a town.** The newer stores are on the state routes (VA 3, VA 33,
  VA 198) between villages.
- **Junctions (rough).** All seven are within 225 m of a point where two numbered routes meet.
  - Counting all numbered routes, including VDOT's "SR 6xx" secondary routes, 47.5 percent of
    random points on these counties' primary, secondary and tertiary roads are that close.
  - Counting only state and US routes, five of the seven stores are within 250 m of a junction,
    against 9.6 percent of random points.
  - Concurrent routes (one road carrying VA 3 and VA 33) can read as a junction along their
    whole length. This needs a cleaner junction rule before it is used.
- **Off-center stores.** The village stores sit well off their catchment's population center:
  Mathews 3.7 km and Saluda 4.0 km straight-line. Mathews' people live mostly south of the
  courthouse, down the peninsula. The newer stores sit closer to their centers: Hartfield
  0.4 km, Dutton 1.7 km, Hudgins 1.9 km.

## Rounds

1. **r1.** The dissolved catchment outlines traced every shoreline and creek. The Deltaville
   label was hidden under the Hartfield label.
2. **r2.**
   - Fixed: only edges shared between two catchments are drawn.
   - Fixed: grocery marks are drawn on top.
   - Fixed: label offsets.
   - Still wrong: the county line still traced shorelines.
3. **r3.**
   - Fixed: the county line now shows only between counties.
   - Known fault: the Hartfield label sits about 1 km southwest of its store and can read as
     belonging to nothing.
   - A fourth round needs Chris's say-so under the round budget, so it is left as listed.
