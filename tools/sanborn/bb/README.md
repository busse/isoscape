# Broad and Belvidere (Tutorial 2)

The four corners of West Broad and North Belvidere, Richmond, from the Sanborn map of 1924,
vol. 1 (LoC sanborn09064_006), sheets 33 and 34, and their 1952 reissue (_016). Scans are at 50%,
kept outside the repo (`~/work/bb/{1924,1952}-00{33,34}-50.jpg`; on the Mac in
`ISO-TEST/isoscape-work/tutorial-history-from-old-maps/research/`).

Run from `tools/sanborn/`:

```sh
python3 bb/fit.py bb/cps1924.json bb/geo1924.json          # from bb/: corners read off the sheets → fit and misses
python3 follow.py /tmp/geo1924.json "$HOME/work/bb/1924-{sh:04d}-50.jpg" "$HOME/work/bb/1952-{sh:04d}-50.jpg" bb/geo1952.json 33 34
python3 extract.py 1924 /tmp/geo1924.json "$HOME/work/bb/1924-{sh:04d}-50.jpg" bb/bb-1924.geojson "" bb/keep1924.json
python3 extract.py 1952 /tmp/geo1952.json "$HOME/work/bb/1952-{sh:04d}-50.jpg" bb/bb-1952.geojson "" bb/keep1952.json
python3 lifespans.py ../../history/sanborn/broad-belvidere-lost.geojson bb/buildings-today.json ../../data/sanborn/motorways.json bb/bb-1924.geojson bb/bb-1952.geojson --respect-years --strict-link
```

(`/tmp/geo*.json` are the `geo*.json` files reduced to `{sheet: {params}}`.) `buildings-today.json`
is `tools/sanborn/dates.ts broad-belvidere` with the CoStar Center dated 2025, as the history
file dates it. `overlay.py`, `fitfig.py` and `streets_over.py` draw the page's check figures;
`counts.py` writes `counts.json`. bb-1924.geojson was traced before the pale-pink rule in
`material.py`; rerunning it gives 255 buildings in place of 259.
