# Dollar stores (Virginia): estimate and actuals

Kept with Claude at the owner's request, in the pattern of `drafts/jackson-ward/effort.md`.

**Unit:** an agent-session is one agent's working session on one line of work, from the
owner's go-ahead to a delivered preview.

## The estimate (plan.md section 5, November 21, 2026, before any analysis)

| # | Work | Estimate (agent-sessions) |
|---|---|---|
| 1 | Data assembly, all sources, sources.md | 1-2 |
| 2 | Edge measures A and B tested on three towns | 1 |
| 3 | Full analysis: every store, comparison retail, null model, ACS | 2 |
| 4 | Editorial grid maps (20 towns) | 2-3 |
| 5 | Artistic grid (227 tiles) | not in the first estimate; 1-2 |
| 6 | Charts | 1-2 |
| 7 | Poster rough drafts (two versions) | 1-2 |
| 8 | Explorer page | 1-2 |
| 9 | Fact check by a separate agent, one fix round | 1 |
| | **Total** | **about 11-17** |

## Runs

| Date | Lines | Wall clock | Tool calls | Delivered | Left undone |
|---|---|---|---|---|---|
| 2026-11-21 | plan | 11:12-11:25 | ~30 | plan.md, sources.md, first SNAP counts, owner decisions | none |
| 2026-11-21 | 2 (edge test), part of 1 | 11:25-11:45 | ~45 | prep.py, measure.py, test_maps.py; three test maps and the score chart; findings-edge-test.md; sources.md with checksums | impervious cover not yet added; null model window to tighten |
| 2026-11-21 | 3 (lead edge), editorial draw (part of 4), case-study record | 11:45-11:52 | ~40 | case-study folder and rule; impervious edge in two rounds; regions.json, draw.py, the 20 towns | full analysis of the 20 towns |
| 2026-11-21 | Mathews and Middlesex catchments (new line of work, owner's request) | 11:53-11:59 | ~20 | catchment.py, catchment_map.py, map in 3 rounds, table | cleaner junction rule; Hartfield label |
| 2026-11-21 | 3 (analysis, editorial 20), part of 6 (charts) | 12:02-12:26 | ~45 | osm_extract.py, pool.py, contact_sheet.py, pool_chart.py; 20 towns scored; findings | statewide view; the artistic 227; ACS "who lives near" |
| 2026-11-21 | Hartfield r4; edge-store reasons (new line, owner's direction): statewide scoring of 227 places, features, gallery, chart | 12:40-12:59 | ~45 | hypotheses.md; features.py, reasons.py, gallery.py, reasons_chart.py; findings | towns-only gallery; water and sewer data; ACS |
| 2026-11-21 | Traffic tests and heat map (new line, owner's request) | 13:06-13:24 | ~45 | traffic.py, traffic_then.py, heat_gallery.py, traffic_chart.py; HPMS 2024 and 2012-2016; findings | heat map for the artistic version |
