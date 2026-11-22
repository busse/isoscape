# Redlining story: estimate and actuals

Kept with Claude in the form of `drafts/jackson-ward/effort.md`: the estimate written before the
work, against what the work took. Unit: one agent run of about 30 to 45 minutes of focused work.

## Rounds

| Round | Date | Estimate | Actual (wall clock, UTC) | Restarts | Delivered |
|---|---|---|---|---|---|
| Outline and rough draft | Nov. 21, 2026 | 4.75 runs | 21:57–22:38, about 41 min (1.0 run) | 0 | outline, six rough figures, tint switch (see `outputs/stories/redlining/rough/effort.md`) |
| Working draft d1 | Nov. 22, 2026 | 9.25 runs (5–7 h) | about 15:00–16:30, about 90 min (2.0–2.5 runs) | 0 | this draft: see `outputs/stories/redlining/working/d1.md` |
| Working draft d2 | Nov. 22, 2026 | 4.1 runs (2–3 h) | 16:44–17:15, about 30 min (0.75 run) | 0 | see `outputs/stories/redlining/working/d2.md` |
| Fact check applied (d4) | Nov. 22, 2026 | not estimated | about 75 min (2 runs), builds and views in the background | 0 | see `outputs/stories/redlining/working/d4.md` |
| Three reads applied, final draft (d5) | Nov. 22, 2026 | not estimated | about 2.5 h (4 runs), builds, views, the visual check and the browser checks in the background | 0 | see `outputs/stories/redlining/working/d5.md` |

Tokens were not metered from inside the run.

## d1 by part

| Part | Estimate (runs) | Actual (approx. minutes) |
|---|---|---|
| Reading, merge main, tests | 0.5 | 10 |
| Outline switch, palette check, key and credit | 0.5 | 8 |
| Full builds (four: lab set, then redrawn set) | 0.5 | about 12, in the background |
| Views: hero, compare pairs, twelve D views, grid; looking at each | 1.0 | 15 |
| Charts and timeline | 1.0 | 8 |
| The set file and `set.py` (stopped at the menu's layout) | 0.5 | 6, plus about 15 of background builds |
| Research: sources opened and recorded | 2.0 | 15 |
| Text: story.md, boxes.py, page.py | 1.5 | 15 |
| Owner's mid-run decisions: redrawn outlines, unnumbered pieces, checked quotation | not estimated | 15 |
| factcheck.csv | 0.5 | 5 |
| Preview, screenshots, looking at the page | 0.75 | 8 |
| Checks: byte-for-byte (four regions), visual check, tests; d1.md; board | 0.5 | 10, mostly background |
| **Total** | **9.25** | **about 90 min, 2.0–2.5 runs** |

## Notes for the next estimate

- The estimate was again high by three to four times. Most of the saving is that the rough round
  had already built the tool change (the tint switch) and the region, and that builds ran in the
  background while text was written.
- Research was the part most cut short: sources were opened at the level of abstracts and
  encyclopedia entries. Three claims still rest on Wikipedia; the fact-check stage will cost more
  than this round did.
- Three owner decisions arrived mid-run (the scan check, the redrawn outlines, the unnumbered
  pieces). Because the outline source sat behind one switch, switching sets cost one rebuild and
  one edit per script, about 15 minutes in all.
- Not done, and not in the time above: the menu sheet (needs a `set.py` layout option).

## d2 by part

Estimate 4.1 runs; actual about 30 minutes of wall clock (16:44–17:15 UTC), with builds, views
and checks running in the background while other parts went on. By weight of work, the scan
(48 pages tiled, 14 read closely) and the shop opt-out (four files and a test) took the most;
the tones, sources, terrain measure and labels were each a few minutes. Reading the scan paid
for itself: it corrected two figures and d1's note on the area names.

## The fact-check round (d4)

An independent check of d3 read 291 rows, of which 154 carry a checkable claim, and found 56
things to change (6 must fix, 32 should fix, 18 notes). Of the 154 checkable claims, 50 had a
should-fix or must-fix finding, about a third; of the whole page's 291 rows, about one in six.
d4 corrected all 38 must- and should-fix findings and 15 of the 18 notes, and disputed none.

| Part | Approx. minutes |
|---|---|
| Reading the contract, decisions, drafts and the check | 10 |
| Scan rereads (D2, D3, D4, D6, D8, D9, D10, D11, map title block) and sources reopened (EV, LVA, VCU Libraries) | 12 |
| measure.py: unrounded shares, frame and D1 splits, OSM checks; fmt.pct; the test | 10 |
| Text: story.md, boxes.py, timeline, charts, views | 20 |
| Two builds and every view rendered (background), looking at each changed figure | 10 of attention, about 15 of waiting |
| claims.py with findings, factcheck_d4.json, preview, screenshots, looking | 10 |
| d4.md, board, commit | 5 |

What the check cost: most of the corrections were small (wording cut back to a source,
citations added), but three needed new measurements (the D1 split, the frame and drawn-frame
totals, Providence Park's share), and one, the D4 remark, needed a scan read that changed a name
in five places. The rounding finding was a code fault, not a wording one, and is now guarded by
a test.

## The three reads (d5)

Three independent reads of d4, made with Claude (a skeptical scholar's, a dignity-and-harm read,
and a first-time reader's with publish readiness), asked for 20 must-fixes between them, about
40 should-fixes and a few dozen notes. d5 applies every must-fix and all but a handful of the
should-fixes (d5.md lists them, with reasons). Two owner messages arrived mid-round and changed
the notice, the review wording, the Jackson Ward links and the "How we know" passage on the
forms; both were applied.

| Part | Approx. minutes |
|---|---|
| Reading the contract, decisions, d4 and the three reads | 15 |
| Merging main; the explorer change (`images: link`), its test, the README | 15 |
| The highway base rate in measure.py; name checks (Oregon Hill, Carver); two charts | 20 |
| Sources opened (papers, local institutions, city maps, licenses) and the scan reread (C4, A5, all twelve D forms' fields 5, 12, 14, 15) | 35 |
| Text: story.md rewritten, boxes.py, areas.py, timeline, views | 35 |
| Two builds and every view (about 13 min in the background); the social image; looking at each | 15 |
| Tests, browser checks from file:// (images, lightbox, sliders), screenshots, the visual check, four byte-identical builds against main | 20 |
| claims.py, factcheck.csv, sources.md, d5.md, board, commit | 15 |

What the reads cost: the base rate and the dispute section needed new measurement and new
sources, which a fact check alone would not have asked for. The reads also caught a fault the
fact check passed: d4's "Providence Park" share measured a park, not the neighborhood.

