# Step 18: merge, deploy, record (November 22, 18:11-18:45)

## Merge and deploy (the planning session)

- **Merged to main** at 18:11: merge commit `f9767e9` ("Merge viz/dollar-stores-virginia: the
  dollar stores story and poster").
- **The page.** `d07cf6e` (18:12) added `shop: false`, `images: link` and `pdf: true` to
  `pages/dollar-stores.md` and to its source, `tools/stories/dollar-stores/story.md`.
- **Published to gh-pages** at 18:12 (`e88635a`), with the page listed:
  https://busse.github.io/isoscape/p/dollar-stores.html. The phone and large-screen PDF
  editions (`p/dollar-stores-phone.pdf`, `p/dollar-stores-large.pdf`) were built with
  `tools/pdf/story_pdf.py`. There is no shop link.

## The release record (this session, branch `release-editorial`)

The release tools knew only store designs, so step 17 left the poster at final draft. They now
also record an editorial piece, one that is released but not for sale:

- The spec is `releases/editorial/viz-dollar-stores-virginia-poster.json`.
- The record, `releases/viz-dollar-stores-virginia-poster/v1.json`, has kind `editorial`,
  `for_sale: false` and no store section.
- It pins these files by SHA-256:
  - the inputs: `poster.py`, `figures.py`, and step 9's `tests.csv` and `dg_classes.csv`;
  - the art: the 1.0.0 PDF, with the PNG beside it;
  - the seven page pictures made from the PDF;
  - the rc1 inspection report.
- It also names the working folder on the Mac that the poster reads, and where the piece is
  shown.

### Checks, run in the cloud container

- `check.py --editorial`: all 15 pinned files match their hashes (`check-editorial.txt`).
- `check.py --editorial --rebuild` (`check-editorial-rebuild.txt`) ends INCOMPLETE, and says
  why:
  - **Page pictures: reproduced.** `figures.py` was run on the recorded PDF in a scratch
    folder. All seven pictures came out byte-identical to the ones in `pages/`.
  - **Poster: not run.** Its working folder (`stores_dedup.csv.gz`, `hpms/va2024.gpkg`,
    `counties/va_regions.gpkg`, the fonts and the place folders) is on the Mac, and geopandas
    is not installed in the container. The check lists both.
  - **To finish it:** on the Mac, run `python3 tools/release/check.py --editorial --rebuild
    --data ds=<working folder>`. That remakes the poster, compares it with the record, and
    writes the working files' hashes into the record.
- **The released art against what was inspected.**
  - The 1.0.0 PDF is identical to rc2's except for matplotlib's `/CreationDate`.
  - The 1.0.0 PNG is byte-identical to rc2's.
  - I looked at the 1.0.0 PDF rasterized at 100 dpi. It matches the PNG: the mean
    difference is 3.6 of 255, which comes from anti-aliasing (pdftoppm and matplotlib's Agg
    draw edges differently).

## Board

- **Poster:** final production, `1.0.0`, `published_version` 1, not on sale, live version
  null, orders 0, rounds 0. Its three accepted faults are kept. Whether it is ever sold is
  Chris's later decision; selling it means a plate and a store record.
- **Story:** published. Chris approved going live without outside review on November 22.

Nothing goes on `pages/changes.md`: this is a first release, not a correction.
