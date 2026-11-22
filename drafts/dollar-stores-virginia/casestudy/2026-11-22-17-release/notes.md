# Step 17: release (November 22, 13:04-13:40)

Chris, 13:04: "approved for release through to live production"

## Done on the branch

- **Released art.** `dollar-stores-virginia-poster-1.0.0.{png,pdf}`, rendered from `poster.py` at
  this step. It is pixel-identical to the inspected rc2. The only change in the script is its
  docstring.
- **The story page is public.**
  - The `unlisted: true` line and the "Draft for review" box are removed.
  - In their place, a line says the page was made with Claude for Chris, the numbers were
    checked on November 22, and the work is independent and not affiliated with any company.
  - Built with `page.py --date "November 22, 2026"`.
- **`origin/main` merged into the branch** (it had moved 20 commits ahead). `pipeline.json`
  merged on its own. `pages/board.md` conflicted and was regenerated from the merged board.
- **Checks.**
  - The board check is clean (116 entries).
  - 239 tests pass and the typecheck passes.
  - The page is in `out/sitemap.xml` and has its static page `out/p/dollar-stores.html`.

## Not done, and why

- **The poster stays at final draft (rc2) on the board.**
  - Final production requires a release record (`board.py check`). `record.py` and `check.py`
    only know store designs: `check.py` checks every record against a store.
  - This poster is editorial and not for sale, so a record made up here could break the
    planning session's release checks.
  - The decision on the board asks the planning session how such a piece is recorded.
- **The story stays at fact check.**
  - Chris approved going live without outside review.
  - It is marked published once the page is actually live.
- **Merge to main and the push to the live site** are the planning session's, per the
  handoff ("Do not merge to main or push gh-pages; say when it is ready and the planning
  session does that after he approves").
- **Chris's 13:04 approval** is the approval the handoff names. Whether he wants this session to
  do the merge itself was put to him.
