# Redlining story: datasets, licenses and credits

Every dataset the story's pictures and numbers use, where it came from, when, and on what terms.
Drafted with Claude for Chris Busse, November 21, 2026. Nothing here is for sale, and nothing
built from the Mapping Inequality polygons may be sold (see below).

## Used

The owner chose, on November 22, 2026, to build the story from the outlines redrawn from the
public-domain scan (`outlines.py`: `USE = 'nara-redraw'`). The lab's polygons are kept, outside
git, only to compare with.

| Dataset | Where it is | Fetched | License / terms | Used for | Sold work? |
|---|---|---|---|---|---|
| HOLC 1937 Richmond map, redrawn | `history/holc/richmond-1937-redrawn.geojson` (committed), made by `tools/holc/` from FRASER's copy of the National Archives scan, `rg195_holc_Richmond_VA.pdf` (SHA-256 `ecaab528…0281e`), georeferenced to 33 OpenStreetMap street corners | Nov. 22, 2026 | Scan: public domain (federal record). Control points from OpenStreetMap (ODbL). | The tinted ground, labels, every area and length by grade | Yes, as far as the data goes (credit OSM for the corners) |
| Unnumbered pieces | `tools/stories/redlining/unnumbered.json`, applied by `outlines.load()` | Nov. 22, 2026 | The story's own record | Four tinted pieces the map prints no number on (a B block at Rodney, Wythe and Bethlehem Roads; D blocks on Canal and Byrd Streets and by Monroe Park; a thin D strip along C10) are split off their nearest areas: they keep their grade and count in the totals by grade, and in no area's own figures (the owner's decision, Nov. 22, 2026). The redraw's GeoJSON is not edited. A fifth, a C patch under 1 ha joined to C10's outline, cannot be split without editing geometry and stays in C10; no per-area number for C8 or C10 is used. | — |
| HOLC area descriptions, scan | FRASER `ad_RichmondVA.pdf`, https://fraser.stlouisfed.org/files/docs/historical/maps/redline_nara/ad_RichmondVA.pdf | Nov. 22, 2026 (read by the planning session) | Public domain | The D11.5 quotation (p. 47, field 6d), checked on the scan | Yes |
| HOLC area descriptions, scan, rechecked for the fact check | as above; local copy SHA-256 `e56e4432…600ab` (matches compare.md) | Nov. 22, 2026 (d4) | Public domain | D4 field 14 reads "Same as Oak Park, D2." (p. 40; the Lab's transcription has "D3"); D10 6c "25 years and older" (p. 46); D3, D8, D9 remarks and D6, D11 inhabitants fields reread for capitals and punctuation | Yes |
| HOLC map scan, title block, rechecked | `rg195_holc_Richmond_VA.pdf`, SHA-256 `ecaab528…0281e` | Nov. 22, 2026 (d4) | Public domain | The HOLC's title "Residential Security Map"; the base map's title "City of Richmond, Virginia and Environs", Department of Public Works, 1923, revised to Aug. 1, 1936 | Yes |
| VCU Libraries, "Interstate Highways" | https://gallery.library.vcu.edu/exhibits/show/mcv-aerial-photography/interstate-highways | opened Nov. 22, 2026 (d4) | Cited, not reused | The Turnpike's opening (July 1, 1958), the Authority (1955), who selected the path | — |
| Mapping Inequality, Richmond 1937 polygons (48 graded areas and one ungraded "Industrial and Commercial" area) | `data/holc/richmond-1937.geojson`, **not committed** (see below). From https://dsl.richmond.edu/panorama/redlining/static/citiesData/VARichmond1937/geojson.json, SHA-256 `8fe7b5cf91cdd7591eeec07c2b053404ad7bc746d62c1b7f061959ce6a49014e`, 57,196 bytes, Last-Modified Aug. 19, 2024 | Nov. 21, 2026 | The DSL's data page: "The georectified rasters and spatial data are available under a CC-BY-NC license", linked to **CC BY-NC 2.5**; "They can be used for pretty much anything that is not commercial with just a citation for Mapping Inequality." (Older credits elsewhere read CC BY-NC-SA 4.0.) | Comparison with the redrawn set only (no longer drawn) | **No.** Free, noncommercial story only, with credit. Prints or a book need the DSL's permission or polygons re-digitized from the public-domain scan. |
| HOLC area descriptions, transcribed | `data/holc/richmond-1937-descriptions.json`, **not committed**: the 48 Richmond records of https://raw.githubusercontent.com/americanpanorama/HOLC_Area_Description_Data/master/ad_data.json, SHA-256 of the extract `8b4934aa9d6f55c946e20a039c5651fa73d2f5593976375dd83500fd40f380a8` | Nov. 21, 2026 | No license on the repository. The text is a federal record (public domain); the transcription is the DSL's work. | Short attributed quotations, each to be checked against the scan before publication | Quote from the scan, cite the transcription. |
| HOLC map and area-description scans | National Archives, RG 195, City Survey Files, https://catalog.archives.gov/id/720357 ; FRASER | not fetched | **Public domain** (federal work; the DSL: "The scans of maps and area descriptions are in the public domain") | To be shown and quoted in a working draft | Yes |
| OpenStreetMap | `data/richmond-streetcars/osm.json` (shared cache) | Nov. 16, 2026 | ODbL 1.0, © OpenStreetMap contributors | Streets, highways (motorway lengths), buildings, water, parks | As in every isoscape map |
| USGS 3D Elevation Program, 5 m | `data/richmond-streetcars/dem.bin.gz` | Nov. 16, 2026 | Public domain | Terrain and hillshade | Yes |
| City of Richmond, Year_of_Construction parcels | `data/richmond-streetcars/yearbuilt.json` (53,049 parcels) | Nov. 16, 2026 | Published by the City on its public ArcGIS service; terms not found (open question in the brief). Already used in published isoscape work. | Which of today's buildings stood in 1937; counts by grade | As now. Year only; no owner fields are fetched. |
| Sanborn fire-insurance maps, Jackson Ward 1952, as traced | `history/sanborn/jackson-ward-1952.geojson`, `jackson-ward-lost.geojson` | in repo | Library of Congress scans, public domain; the trace is isoscape's | The survival check (how many 1952 outlines stand today) | Yes |

**Why the polygons are not committed.** The repo also builds work that is sold. Keeping
CC BY-NC data out of it means nothing NC can drift into a print by accident. Anyone can
fetch the same file from the URL above and check its SHA-256; `history.py`, `measure.py`
and the builds read it from `data/holc/`.

## Credit lines

- On every image (from `outlines.py`): "Grades: Home Owners' Loan Corporation, 1937 (National
  Archives, RG 195, via FRASER); outlines redrawn with Claude from the public-domain scan,
  positioned with OpenStreetMap street corners (ODbL)."
- In the text, Mapping Inequality is credited as the project that digitized and published these
  maps, whose digitization checked the redraw and whose transcriptions were consulted.
- In sources, the citation the DSL asks for: Nelson, Robert K., LaDale Winling, et al. "Mapping
  Inequality: Redlining in New Deal America." Edited by Robert K. Nelson. *American Panorama: An
  Atlas of United States History*, 2023. https://dsl.richmond.edu/panorama/redlining. For an
  online article the DSL says "Courtesy of Mapping Inequality" or "Source: Mapping Inequality"
  is fine, and "Mapping Inequality, public domain image" for the scans.
- Map data © OpenStreetMap contributors (ODbL); elevation USGS 3DEP; year built, City of Richmond.

## Not used

| Dataset | Why not |
|---|---|
| Science Museum of Virginia / Hoffman 2017 heat rasters (OSF `f9nhg`) | **No license stated.** Not used in anything published until the Science Museum allows it. |
| Meier & Mitchell, Historic Redlining Indicator (openICPSR) | No license stated ("distributed as received"); not needed. |
| City of Richmond parcels with assessed value and owner | Not fetched in this round. If used later: values in aggregate only, never owner names. |
| VCU life-expectancy map, *Planned Destruction*, NYT 2020 graphics | Copyrighted visual work: cited and linked, never reused. |

## Opened for d5, November 22, 2026

Every new or changed factual sentence in d5 rests on a source opened on this date, by Claude,
from the session's own network (no logins, no paid sources). Quotations on the page are a few
words at most, one per source; the rest is paraphrase.

| Source | What it supports on the page | Notes |
|---|---|---|
| Hillier 2003, *Journal of Urban History* 29(4), author's postprint, https://core.ac.uk/download/76393191.pdf | Maps not widely distributed, none to private interests, some lenders and the FHA had access (pp. 398–402); more than 60% of HOLC loans in Philadelphia to areas later red (p. 397); lending already withheld before the maps (p. 398, p. 412); grades explain interest rates only (abstract, p. 412); the 1935 Underwriting Manual (p. 403, n. 39); the City Survey Program's name | Read through a fetch tool's summary with page numbers. |
| Fishback, LaVoice, Shertzer and Walsh, *JEH* 83(4), 2023, open access, https://doi.org/10.1017/S0022050723000475 | HOLC kept maps confidential inside government; FHA shared its maps; maps had virtually no influence on HOLC refinancing; HOLC finished lending June 1936; Black share 4.5% of HOLC mortgages in 1940; FHA established 1934; the 4 to 20 percent; Michney and Winling citations | Full text. |
| Aaronson, Hartley and Mazumder, Chicago Fed WP 2017-12, revised August 2020 | Pre-existing differences and propensity weighting; D–C racial gap 15 to 17 points in 1950–1970, 3.1 points by 2010; estimates "capture the sum of any HOLC and FHA effects where the boundaries align"; "We will likely never know the degree to which lenders used the actual maps" | Full text (pdftotext). The page paraphrases. |
| Aaronson, Mazumder, Hartley and Stinson, Chicago Fed WP 2022-13 | Estimates as a proxy for redlining practices that arose largely through federal housing policy | Full text. |
| Fishback, Rose, Snowden and Storrs, NBER w29244 (full text) and the University of Arizona record of *JUE* 141: 103462 (May 2024) | The racial clause of the abstract; loan data from Baltimore, Peoria and Greensboro; early Underwriting Manuals advised against insuring in racially integrated areas; the corrected citation | Full text and record. |
| Michney 2022; Winling and Michney 2021 | Cited by title only | Publisher pages blocked by a verification wall; not opened, not summarized. Titles and volumes from Fishback et al. 2023's reference list. |
| CFPB, "Mortgage data (HMDA)", https://www.consumerfinance.gov/data-research/hmda/ | HMDA enacted 1975; requires reporting and public disclosure | |
| Federal Reserve, "Community Reinvestment Act (CRA)", https://www.federalreserve.gov/consumerscommunities/cra_about.htm | CRA enacted 1977; what it directs regulators to do | |
| FRED Blog 2021 (reopened) | What the maps rated; informed the Federal Home Loan Bank Board's supervision; no mention of race in the grade summary | |
| Encyclopedia Virginia, "Urban Renewal in Richmond" (reopened) | Richmond Housing Authority (1940), RRHA; Apostle Town; Turnpike referendums and Authority (1954); Gilpin expanded 1957; Fairfield and Whitcomb 1958; 17th Street Urban Renewal Project; Mosby Court; RRHA-sponsored 1967 Fulton study ("slum"); RRHA razing from the early 1970s; Randolph; the 1924 ordinance and the Racial Integrity Act; Bartholomew's plan | |
| Encyclopedia Virginia, "James H. Blackwell (ca. 1864–1931)" | Principal of Manchester's school for Black students from 1888; demoted after the 1910 consolidation; school named for him 1951; the neighborhood's name | |
| Craig 2025 (reopened) | RHA built Creighton, Mosby, Whitcomb, Fairfield and Hillside Courts; Hillside served low-income white residents; the News Leader's 301 units (April 15, 1943) | No dates given for Creighton or Hillside. |
| HUD via ProPublica, VA007000001, 004, 005, 006, 007, 008 | Each court's address list, matched to OSM address points: Fairfield 27 of 29 and Whitcomb 15 of 18 matched addresses in D5; Mosby 22 of 24 in D5; Creighton 10 of 10 ungraded; Hillside 10 of 11 ungraded | The matching was run in the session; recorded in d5.md. |
| Library of Virginia, "House to Highway" | Jackson Ward the center of Richmond's Black community; The JXN Project the partner; shown July 14, 2025, to February 28, 2026 | |
| City of Richmond, "Jackson Ward" (rva.gov) | "Black Wall Street" and "Harlem of the South" | |
| Black History Museum & Cultural Center of Virginia, https://blackhistorymuseum.org/ | The museum and its address, 122 West Leigh Street | |
| Historic Jackson Ward Association, https://www.hjwa.org/ | The neighborhood association and its history pages | The page named in the dignity read (?p=4084) refused the request (406); the home page opened. |
| The JXN Project, https://www.thejxnproject.org/ | Historic preservation nonprofit, founded 2021 | |
| VCU News, Historic Fulton Oral History Project (2015) | Interviews 2011–2012; organizers; The Valentine holds the materials; VCU Libraries posted them | |
| Virginia DHR, Washington Park marker (2024) | Emancipated African Americans settled the area; Oak Park and Washington Park developments | |
| The Valentine, Oregon Hill self-guided tour (PDF) | The Oregon Hill Historic District's bounds; white, blue-collar by the mid-1900s | D8 overlap measured in measure.py `name_checks`. |
| City of Richmond civic-group maps: Providence Park, Union Hill, Carver, Swansboro; Church Hill North Old & Historic District | D4, D6, D1 and D10's modern names | Washington Park and Fairmount maps were downloaded but not used on the page. |
| LC Labs, Sanborn Maps data package README, https://data.labs.loc.gov/sanborn/README.html | The Library of Congress's online Sanborn collection is public domain, free to use and reuse | loc.gov itself refused automated requests. |
| americanpanorama/HOLC_Area_Description_Data (raw files) | No LICENSE file; the README states no license | GitHub's API was not available to this session; checked by fetching the raw README and LICENSE paths. |
| City of Richmond Year_of_Construction service (ArcGIS JSON) | No copyright text or terms in the service or layer description | |
| National Archives scan, `ad_RichmondVA.pdf` (local copy, SHA-256 `e56e4432…`) | Read this session: C4 p. 26 (field 14), A5 p. 5, D1 to D11.5 pp. 37–48 (fields 5, 12, 14, 15); D6 and D8 field 12 at 300 dpi | Ten of twelve D forms record a Black population; "Infiltration of: Negroes" on D2, D5, D6, D7; field 12 from "None" (D7) to 60% (D1, D2, D4, D11), blank D3 and D9; informants J. D. Carneal (D1–D9) and A. L. Adamson (D10, D11, D11.5). |

Licenses now named on the page: the city's parcel service states no terms; the Lab's
transcription repository states no license (the forms themselves are public-domain federal
records); the Library of Congress's online Sanborn collection is public domain.
