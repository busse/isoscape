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

## Before the estimate (not counted against it)

Research and brief, the ground restoration (jw-ground), the 1952 trace (jw-trace), the rough
draft and the outline were done November 17–18, 2026, before this estimate was made.

## Notes for the case study

- The text-and-charts run was estimated at 4½–6 agent-days (lines 4, 5, 6, 9) and took one 31-minute run of 440,000 tokens. Either the estimate was far too high or the unit is wrong; the fact check will show how much of that work stands.
- The 1925 state was estimated at 3–4 agent-days and its first run took 38 minutes and 378,000 tokens. It could reuse the 1952 fits by matching each 1925 sheet to its 1952 reprint, which the estimate did not foresee.
