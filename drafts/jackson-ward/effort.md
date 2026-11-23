# Jackson Ward story: estimate and actuals

Kept with Claude at the owner's request (November 18, 2026): track the working-draft estimate
against what the work took, for a case study and for better estimates later.

## The estimate (outline.md section 8, November 18, 2026)

| # | Work | Estimate (agent-days) |
|---|---|---|
| 1 | Street lines of 1952 inside the corridor, from the Sanborn sheets | 1 |
| 2 | Re-trace volume 1 sheets 2–3 (Second Street, Broad to Clay) | ½–1 |
| 3 | Read stories and uses for buildings in the corridor and on Second Street | 1–2 |
| 4 | Timeline diagram; study-area image; labels | 1 |
| 5 | The ten method charts, by script | 2 |
| 6 | Text, every fact sourced; disputed-figures table | 1–2 |
| 7 | Check sheet 318 (Gilpin Court) against 1950s aerials | ½ |
| 8 | 1925 state (approved) | 3–4 |
| 9 | Gilpin Court beat (added by the owner's decision; estimated November 18) | ½–1 |
| 10 | Fact check by a separate agent, and one fix round (not in the outline's table) | 1–2 |
| 11 | The island image: only what was removed, inside the boundary (added by the owner; estimated November 18) | 1 |
| | **Total** | **outline: 11–14 with 1925; with lines 9 to 11: about 13½–18** |

**The unit was never defined when the estimate was made.** That is the first lesson. From here
an agent-day means one agent's full working session on one line of work. The log below records
what can be measured, so the unit can be calibrated afterward.

## What to record for every agent run

Date; which lines above it worked on; wall-clock duration; tokens; tool calls; whether it was
restarted; fix rounds; what it delivered; what it left undone. Also record, separately: the
planning session's own time on the story, the owner's review time (his own note, if he gives
one), and elapsed calendar time from "outline approved" (November 18, 2026, 11:45 ET) to "ready
for outside review".

## Log

| Date | Run | Lines | Wall clock | Tokens | Tool calls | Restarts | Delivered | Left undone |
|---|---|---|---|---|---|---|---|---|
| 2026-11-18 | jw-text (Opus 5.5): story page, timeline, cap study area, ten method charts, How we know | 4, 5, 6, 9 | 31 min (12:45–13:16 ET) | 440,516 | 178 | 0 | page (unlisted), 12 charts by script, 45 claims checked against opened sources, 11 fact-check items | slots for 1925, the island, Second Street; 4 groups of facts still resting on secondary sources; three small number mismatches (count 235 vs 238; bank 10.1 vs 9 m; 1st Street cut 6.2 vs 6.4 m) |
| 2026-11-18 | jw-1925 (Opus 5.5): find, place and trace the 1925 volume; 1925 epoch; named buildings | 8 | 38 min (11:45–12:23 ET) | 377,761 | 194 | 0 | 15 of 15 sheets, 3,907 outlines, 46 named buildings, 1925 scene builds, three pairs with 1952 | outlines too busy at view size (many vertices); Apostle Town's own streets; stories beyond named buildings; scans not yet on the Mac |
| 2026-11-18 | jw-1925 follow-up (Opus 5.5, new agent; the first one's transcript was lost): simplify the 1925 outlines, scans to the Mac | 8 | 7 min | 168,583 | 61 | 0 | corners 61,738 to 21,833, largest move 1.00 m; five proofs replaced; scans on the Mac | Apostle Town's 1925 streets |
| 2026-11-18 | jw-streets (Opus 5.5): corridor streets, Second Street re-trace, stories and uses, count, 1952 outline cleanup, the island | 1, 2, 3, 7, 11 | 50 min | 418,570 | 292 | 0 | 24 street stretches; sheets 2–3 refit (0.5–2.9 m) and 198 outlines added; 479 buildings read; count 238/489 to 216/447 with the picture matching; island switch, two boundaries | line 7 (aerials need a USGS login); island's east loop bare |
| 2026-11-18 | integration (Opus 5.5): merge three streams, numbers, slots, overlay plan, Apostle Town's 1925 streets, chart faults, how-its-made | all, plus decision 11 | 27 min (12:36–13:03 ET) | 385,838 | 160 | 0 | one draft on story-jackson-ward (ce30c56): page, 24 images, PDF; 216/447 everywhere; island cut at 8th Street | 20 open items for the fact check; Pulliam, Judah and Price not found on the 1925 sheets |
| 2026-11-18 | fact check (Opus 5.5, independent) with one fix round | 10 | 24 min (13:04–13:28 ET) | 414,627 | 203 | 0 | 143 claims in a ledger: 95 confirmed, 34 reworded, 6 contradicted and fixed, 4 unsupported and reworded or cut, 4 not opened; 44 changes | Silver (1984) and Campbell (2012) unseen; three more sources not opened; sheet 318 against aerials |
| 2026-11-18 | page round 1 (Opus 5.5), from the owner's review of the explorer view: headline and deck, numbered figures, link fix, lightbox and grid, route section as prose | owner's review (not in the estimate) | 20 min (13:59–14:19 ET) | 297,108 | 93 | 0 | all five points; 24 figures; 100 in-page links tested; Mac preview updated | phone layout scrolls sideways (older fault) |
| 2026-11-18 | island trivia image (Opus 5.5) | side request (not in the estimate) | 3 min | 122,330 | 32 | 0 | five unlabeled crops and trivia notes | |
| 2026-11-18 | page round 2 (Opus 5.5), from the owner's request: compare sliders reusing the viewer's divider; all four years in one shared frame | owner's review (not in the estimate) | 17 min (14:32–14:49 ET) | 262,877 | 101 | 0 | four sliders (Figs. 4, 6, 15, 21); shared `compare.ts`; Mac preview updated | phone layout; divider tab clipped at 0% and 100% |
| 2026-11-22 | three reads applied (Opus 5.5): scholar, dignity and first-time-reader findings; owner's notice; count ranges; error widened; route section; pictures labeled | owner's reads (not in the estimate) | about 40 min (15:03–15:43 ET) | not measured by the run | about 160 | 0 | branch story-jackson-ward-reads: page, 12 charts and 15 views re-rendered, timeline back on the page, 24 new claims and 21 revised in the ledger, changes.md | page weight, autolinks, share-page noindex, og:image:alt and the explorer's back pill (shared site code, another agent's); Legistar public page; Silver and Campbell still unseen |

## Before the estimate (not counted against it)

Research and brief, the ground restoration (jw-ground), the 1952 trace (jw-trace), the rough
draft and the outline were done November 17–18, 2026, before this estimate was made.

## Notes for the case study

- The text-and-charts run was estimated at 4½–6 agent-days (lines 4, 5, 6, 9) and took one 31-minute run of 440,000 tokens. Either the estimate was far too high or the unit is wrong; the fact check will show how much of that work stands.
- The 1925 state was estimated at 3–4 agent-days and its first run took 38 minutes and 378,000 tokens. It could reuse the 1952 fits by matching each 1925 sheet to its 1952 reprint, which the estimate did not foresee.
- First pass of all three streams: 4 runs, about 2 h 6 min of agent wall clock in about 50 min of elapsed time, 1.41 million tokens, 725 tool calls, against lines estimated at 11–15 agent-days. Integration and the fact check are still to come.
- Outline approved to fact-checked draft: 11:45 to 13:28 ET, 1 h 43 min elapsed. Six agent runs, about 2 h 57 min of agent wall clock, 2.21 million tokens, 1,088 tool calls, no restarts (one agent's transcript was lost and a new agent took its follow-up). The estimate was 13½–18 agent-days.
- What the first pass got wrong, found by the independent check: 10 of 143 claims were contradicted or unsupported (7%), and 5 of our own numbers were misstated in the text. Speed did not come free; the separate check was necessary.
- Why the estimate missed: it was made in an undefined unit, by analogy to human research days; it did not foresee reusing the 1952 fits for 1925; and parallel streams with clear file ownership merged without conflicts.
- Not counted here: the planning session's own time and tokens, the owner's review time, and the outside review still to come.
- The three reads (November 22) found what the fact check had not: the stated ground error was tighter than the page's own trials, the count had no range, the tracing's east end was misplaced by a street, and the route section leaned on one uncited line. One run applied them. An independent read of method and framing earned its place after the fact check.
- Correction of November 23, 2026 (the Belvidere Street extension drawn in 1925 and 1952, and the 5th Street sentence): found by the pocket guide's rough draft, fixed in one run on `fix/jackson-ward-1952-bridges`, about 50 min of agent time (09:20-10:10 ET) including the scan of every dated view, two full rebuilds of the views (5 min each) and the checks. See `casestudy/log.md`.
