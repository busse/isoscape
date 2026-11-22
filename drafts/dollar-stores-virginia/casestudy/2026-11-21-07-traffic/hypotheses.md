# Traffic at the edge stores: tests, written before fetching the counts

Written with Claude on November 21, 2026 at 13:08. This is before any traffic count was
downloaded or joined. Chris, 13:06: "Yes, this is an interesting thread to pull at and maybe
heat map".

## Source

- FHWA, Highway Performance Monitoring System 2024, "Spatial All Sections", on
  data.transportation.gov (dataset 42um-tgh5).
- License: Public Domain U.S. Government.
- Virginia sections (stateid 51) with functional system 1 to 6, the roads the edge stores and
  random points sit on.
- AADT is the annual average daily traffic. Each section's count carries its own date
  (`aadt_d`).

## Matching a point to a road

- A store or random point takes the AADT of the nearest HPMS section with an AADT, if that
  section is within 60 m.
- Otherwise it has no count and is reported as such.
- The count year is kept with each match.

## Tests

Same edge band, stores and random points as `../2026-11-21-06-edge-stores/` (score A 1 to 2,
40 random main-road points per edge store, seed 20261121).

1. **Busier road than the other sites in the band.**
   - Median AADT at the 34 edge Dollar General stores against the random points.
   - Interval: bootstrap of the stores' median, 10,000 resamples, seed 20261121.
   - Supported if the random median is below the interval. Contradicted if above.
     Otherwise the data cannot tell.
   - Reported for towns and cities apart too, since step 6 found they differ. That split
     is the follow-up to an earlier exploratory finding, so it is labeled as such.
2. **On the busiest road into town.**
   - For each place with an edge chain store, list the roads crossing its built-up edge, as
     HPMS sections cut by the edge line, each road taken at its highest AADT where it
     crosses.
   - Count how often an edge store sits on the busiest of them, and how often on one of the
     top two.
   - Compared with random points in the same band, which land on the busiest crossing road
     at some rate. Same rule for support.
3. **Traffic when the store was authorized.**
   - Only if the 2024 counts show a difference worth explaining.
   - For edge stores authorized 2011 to 2017, the AADT in FHWA's HPMS shapefile for that
     year, against 2024. The question is whether the road was already busy when the store
     came, or got busier since.
   - Reported as a description (few stores), not a test.

## The heat map

- Roads drawn in a single-hue sequential ramp by AADT (dataviz skill: sequential = one hue,
  light to dark), in fixed classes: under 2,000; 2,000 to 5,000; 5,000 to 10,000; 10,000 to
  20,000; 20,000 and over.
- Line width also rises with traffic, so the map does not rely on color alone.
- Stores in yellow with a black ring, as before.
