# Case-study log: Jackson Ward story, corrections after publication

Kept with Claude under Chris's case-study rule (November 21, 2026). The story's earlier record is
in `../decisions.md`, `../effort.md` and `/mnt/user-data/outputs/stories/jackson-ward/`. Times are
Eastern.

## Step 1: the 1952 bridges (November 23, 2026, 09:20-10:45)

Folder: `2026-11-23-01-fix-1952-bridges/`. Branch `fix/jackson-ward-1952-bridges`.

- Reported by the pocket guide's rough draft: the stop 5 pair showed elevated Chamberlayne Avenue
  bridges in 1952.
- Found: the bridges are the Belvidere Street extension's (National Bridge Inventory: both
  bridges 1958). An era rule dated them from 1901 together with the old concrete bridge beside
  them, and the extension's at-grade ways had no rule. Looked at the USGS sheets of 1934 and
  1956 side by side (`usgs-1934-left-1956-right.jpg`): the 1934 sheet has no diagonal road; the
  1956 sheet shows it as US 1 through interchange 13. Overlaid today's ways on the 1952 Sanborn
  sheets 304, 315 and 317 (`sanborn-*.jpg`): houses, a coal yard and the S.A.L. tracks on its
  line, and a "Concrete Bridge" on the old line.
- Dead end: a first version of the rule also listed the extension's sidewalks. It changed the
  1959 view (two sidewalk pieces appeared, since a dated way is kept away from houses) and
  changed nothing in 1925 or 1952, so the sidewalks were taken out of the rule.
- Fixed in the history file: a 1958 rule for 12 ways, the 1901 rule cut to the concrete bridge,
  four ids out of `atGrade`. Rebuilt the views with `views.py`; before and after looked at side by
  side (`*-before-after.jpg`). Changed: 1925, 1952, count, lost streets, island, link preview.
  Unchanged: 1959, today, Second Street; apostle-town's file changed by antialiasing only.
- Scanned every dated view for other later structures (`scan-later-roads.*`): later street
  alignments in Navy Hill and Gilpin Court run through 1952 houses (`plan-1952-*.jpg`). Not fixed:
  they need the 1952 street lines read off the sheets first. Listed for the planning session.
- "5th (now Maggie L. Walker Place)": the City's street centerlines and OSM both keep N 5th St
  across the trench and give Maggie L Walker Pl as a separate 200 block. Sentence corrected.
- Checks: counts identical (216 / 447 / 2,875 and every range); five reference builds
  byte-identical to origin/main; visual check identical or within tolerance
  (`check-visual-report.jpg`); 257 tests pass; typecheck clean. Story PDFs not rebuilt.
- Delivered: `/mnt/user-data/outputs/stories/jackson-ward/fix-1952-bridges/fix.md`.
