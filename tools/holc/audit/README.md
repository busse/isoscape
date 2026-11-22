# HOLC area-description audit

A field-by-field comparison of Mapping Inequality's transcription of Richmond's 1937 HOLC area
descriptions (`ad_data.json` from americanpanorama/HOLC_Area_Description_Data, commit
`1dea892`, December 5, 2023) with the scans of the forms themselves (FRASER,
`ad_RichmondVA.pdf`, 48 pages, SHA-256 `e56e4432…600ab`). Done with Claude, November 22, 2026,
for the redlining story. Neither the lab's file nor the scans are in this repo.

## How it was done

1. Each page's embedded JPEG (1220 x 2038 px, 144 ppi) was extracted with `pdfimages -j`,
   enlarged 2x and OCR'd with tesseract as a first pass.
2. `forms.py` lays out each record in the form's printed order and flags values the OCR text
   lacks (`--ocr-dir`, `--pages`). The flags were only a pointer.
3. Every page was then read on the image, every field, with enlarged crops for any figure in
   doubt. Every number, the grade, the area number and the remarks were read whatever the OCR
   said.
4. Each difference went into `richmond-differences.csv`. `tally.py` counts them.

```sh
python3 -I tools/holc/audit/forms.py ad_data.json --label D4          # one record, form order
python3 -I tools/holc/audit/tally.py tools/holc/audit/richmond-differences.csv ad_data.json
```

## The CSV

One row per field where the scan and the transcription differ. Columns: `area`, `page` (1-based
page of `ad_RichmondVA.pdf`), `form_field` (the printed field number), `field` (the lab's schema
key), `scan_reading`, `transcription` (the lab's differing value; long fields are cut to the
differing sentence and say so in `note`), `class`, `subclass`, `note`.

Classes:

- **a, substantive:** changes a value or a reference to another area. Subclasses: `a1` a number,
  year, percentage, area reference or field's value changed; `a2` a word changed that does not
  change a number (a plural, houses/homes, dropped words); `a3` the transcription silently fixed
  a typo on the form (`$6,00`).
- **b, formatting only:** capitals, punctuation, a dollar sign, spacing, "to" written as a hyphen.
- **c, ambiguous or illegible on the scan.** None were needed; figures typed over another figure
  are read as they appear and say so in `note`.
- **d, blank on one side only:** the transcription is blank (or holds a stray character) where
  the scan has text, or the reverse.

Fields the schema has no place for (the typed neighborhood headings, 5g "static") are listed
separately in the audit report as "not captured"; they are not errors.

One field (D11.5, 6d) holds a racial slur on the form; it is in the CSV as data.

The readings are one reader's. A second reading of the `a1` rows is the cheapest check on them.
