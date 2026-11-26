# Fact check of the floods editorial (draft 1) and what was done

The independent fact check of `pages/richmond-floods.md` (draft 1, branch head db87bf2e) was run
on November 26, 2026 by a separate Claude agent that had not drafted the page, checking every
figure against the listed sources. Its report reached the drafting agent through the coordinator as
the list below (its full text is not in this folder). Verdict: nothing blocking, 14 fixes. All 14
were applied in `tools/stories/richmond-floods/story.md` and `page.py`; the page was rewritten
by `page.py`.

| # | Finding | Done |
|---|---|---|
| 1 | The older Shockoe Creek levee's "limited protection" is from FEMA's 1998 study (PDF p. 9), not 2025 | Cited FEMA Richmond 1998; its Sources entry says "PDF p. 9, levee history" |
| 2 | Camille: pumping at the levee "had to be stopped" for structural reasons; overtopped in 1972 | Reworded as given, cited 1998 and 2025 |
| 3 | FEMA 1998: met its rule of at least 3 ft freeboard above the 100-year; not adequate for the 500-year | Reworded as given |
| 4 | Forecast: the two main models called for 1 to 2 in over southern Virginia | Reworded as given |
| 5 | Deck and summary: "recorded or estimated height" | Done |
| 6 | Datum: City Locks records before 2007 on the older datum; before 1957 an older gauge near the Mayo Bridge | Reworded as given, citing River datums and Second read |
| 7 | "So 226 is a count of drawn buildings. It is not a count of the buildings that flooded." | Done |
| 8 | Describe Gaston's 28 ft the same way in all three places | The same words in the figure caption, the depths paragraph and the limits |
| 9 | Checks described plainly; "the series' second reader" becomes "a second Claude check"; this page's own fact check stated | Done in "How this page was made" and Sources |
| 10 | No internal working names in reader text; research paths that exist in the repo | Captions say "drawing", "close view"; Sources point at `drafts/richmond-floods/casestudy/2026-11-23-0x…` paths |
| 11 | "the height the water reached at the City Locks gauge"; "when the James rises toward them" | Done |
| 12 | "about 17 to 18 feet below" (lead and Fran) | Done (token in `page.py` gives the range, Fran's level being up to 1 ft higher) |
| 13 | "at the deepest point of their footprint" | Done |
| 14 | "Nearly ten years after"; "No rain since that the research checked has come close…, on the AORC record"; AP Sept. 2, 2004 for the 6:30 car; the 26 ft Great Shiplock Park gauge explained | Done; the AP source added and cited in Fig. 14's caption; the note is in Fig. 9's caption |
| also | Construction start attributed to the 1989 state report; $143 million kept as the city's figure; 1996 closures without tying Dock Street to a month | Done |
