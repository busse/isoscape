# Outline: Tutorial 2 (for Chris's approval, November 25, 2026)

**Title:** Tutorial: draw a neighborhood's history from old maps and open data with an AI chat,
using Jackson Ward and Broad and Belvidere in Richmond

**Summary for link previews:** A step-by-step isoscape tutorial. Use an AI chat to find old
fire-insurance maps, fit them to today's streets, trace and count what stood there, and check
what you find against the records. Worked example: the four corners of Broad and Belvidere in
Richmond, 1924, 1952 and today. Showcase: the Jackson Ward and redlining stories.

**Reader:** someone using the Claude desktop app who doesn't program. It stands on its own:
anything it borrows from Tutorial 1 (what the chat needs, the five questions to ask of any
dataset) is said again here in brief, with a link for readers who want more.

Each section lists its figures (F) and the real prompts it will show (P). The prompts are
recorded as the example is made.

---

### 1. What this tutorial teaches, and what it can grow into
isoscape in two sentences, for readers arriving here first, and what the chat needs (run code,
fetch public data, keep files in a folder). A story page works one question out
with drawings, counts and sources. Show the two Richmond stories as the full-size version.
- F: hero, the four corners in 1924 beside today, as one compare slider.
- F: small cards for *Jackson Ward before I-95* and *Redlining in Richmond, 1937*.

### 2. Choose a question a map can answer
The test is that the answer is a place, a count or a change over time. The example's
question: *what stood on the four corners of Broad and Belvidere, and what changed?* Kept to
one intersection on purpose.
- P: the first request, as it was asked.

### 3. Find the old maps and check each one
Sanborn fire-insurance maps at the Library of Congress (public domain); how to read the
volume's key map to find your sheets (here vol. 1, sheets 33 and 34, 1924 and the 1952
reissue); what the map colors and letters mean (D = dwelling, S = store, A = auto garage). Then
today's layers: the city assessor's parcels and years built, OpenStreetMap, lidar. Ask five
questions of each source (does it exist and can I get it, who made it and how, what it
covers, what license, what it can't show), stated here in full.
- F: the key-map crop with the two sheets marked; the corners in 1924 and 1952 side by side.
- P: "Which Sanborn sheets cover Broad and Belvidere?" and the dead end (vol. 3 has no Broad Street).

### 4. Put the old map on today's ground
Street corners that still exist become control points. The sheet is fitted to them, and the
miss at each corner is reported. Shown live: the Smith Street question (callout A).
- F: sheet 33 with its control points and misses; the fitted sheet over today's streets.

### 5. Trace it, then check the trace against the sheet
Building outlines traced in code; the trace laid over the scan; what the chat got wrong and
how it was fixed. The survivorship trap: today's records only date what survives.
- F: trace over scan, one block; the four corners traced for 1924 and 1952.

### 6. Count with a written rule
Write the rule first, then count: buildings per corner, kinds of use (auto, store, dwelling),
what survives today. Label every number as measured, inferred or unknown.
- F: a small table per year.

### 7. Draw each state and compare
isoscape builds of 1924, 1952 and 2026, with compare sliders between them. The CoStar Center
is drawn as "under construction".
- F: three views; two sliders.

### 8. When the sources disagree (the callouts)
Three real disagreements found while making the example, each with how it was handled.
- **A. The street that changed names.** Both Sanborn editions label the street north of Broad
  "Smith"; today it is North Belvidere (US 1). Handle it by laying the sheet on today's ground
  and seeing whether the road follows the old line. Say what the drawing shows and what it
  doesn't, and look for a city record of the change before naming a date.
- **B. "All four corners."** A guest commentary (BizSense, April 2026) says a VCU purchase at
  409–423 W. Broad gives VCU "control of all four corners". The city's July 2026 assessment
  lists the northeast corner under a private owner, and the northwest under the VCU Real
  Estate Foundation, a separate legal owner tied to the university. Handle it by reading the
  claim generously first: "control" may count the foundation, leases or a sale since July.
  Then check the newest record. Report what each source says, with its date, and don't call
  either side wrong without the deed. This is also a lesson in opinion pieces: quote them as
  arguments, not as records.
- **C. The train station.** A 2017 business article says the ICA site "was once the site of a
  small train station". The 1924 sheet puts the Richmond-Ashland Railway's station two blocks
  west, on the north side, with auto businesses on the ICA block. Handle it by checking the
  other editions (1905, 1919) before saying anything. A claim can be true for a year you
  haven't looked at. If it can't be settled, say so.
- A short general rule to close the section: keep every disagreement in a list; check the
  primary record; consider timing, definitions and scale; report both with dates; mark it
  unresolved if it is; and if your page has already published something wrong, correct it in
  public with a dated line.

### 9. Write it so it can be checked
Answer first. A source for every fact, opened while writing. A "How we know" section,
corrections, and who keeps the history (local archives, the neighborhood, the institutions
involved). The PDFs and a descriptive title for the link preview.

### 10. Care
Places with lived history: when a story touches displacement, get outside review from people
with standing, or say plainly that none happened. Give each side in its own words with a
source: VCU on the ICA and the CoStar Center as a gateway between the campuses and the city;
preservationists on reuse over demolition. Carver's history is linked, not summarized. Credit
the keepers. No prints.

### 11. Make your own
One sheet, two editions, one block in your own town. A starter prompt. An honest note on
effort: the example took about N sessions, and Jackson Ward many more. Links to the reference
site and the repo, and the shop mentioned once.

### Sources (so far)
LoC Sanborn Richmond 1924 vol. 1 (sanborn09064_006) and 1952 reissue (_016); City of Richmond
assessor parcels and Year_of_Construction (July 1, 2026); OpenStreetMap; VCU News (ICA 2011,
2014; CoStar Center 2025); Richmond BizSense guest commentary (Dotts and Kerr, April 3, 2026);
Virginia Business (April 25, 2017); WVTF (2018); Style Weekly (Legions).

---

**Work behind it, in order:** fetch sheets 33 and 34 at full resolution for both years → fit
(control points) → trace → check against the scans → a history file for the corners → builds
for 1924, 1952 and 2026 → figures → draft → fact check → local preview. The case-study record
is kept at each step.
