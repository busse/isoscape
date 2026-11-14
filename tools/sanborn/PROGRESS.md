# Tracing progress (working notes)

Scans live outside the repo in `~/work/sanborn/img25|img50|img100` (device VM), fits in
`~/work/geo/`. LOC item numbers: sanborn09064_001 1886, _002 1895, _003 1905 (files sbNNNNNx),
_004 1908, _005 1919, _006–_009 1924–25 vols 1–4, _011 1950 vol 2, _016 1952 vol 1.

| Edition | Status | Notes |
|---|---|---|
| 1886 | traced | sheets 6–22 except 14; scale 0.2014 m/px at 25% |
| 1924–25 | traced | vol 1 cbd1 key map at 100% (rubber sheet, `snap.py`), vol 1 sheets 17,18,19,21,22 (0.2085 m/px; traced at 50%), vol 2 sheets 201–208, 212–216 (0.2014). Missing: vol 1 sheets 20, 23, 24 (corners misread), 209 |
| 1950–52 | traced | vol 1 (1952) sheets 1–13, 15 by eye (0.318 m/px at 25%), 17–22 via `follow.py` from 1924; vol 2 (1950) 201–216 via `follow.py`. Missing: 14, 16, 20, 23, 24 |
| 1905 | traced | sheets 2,3,4,5,7,9,11,17,18,20,43–47 read by eye (0.1525 m/px at 25%). Missing: 6,8,10,12–16,19,41,42,48–51 |
| 1895 | traced | sheets 13,14,15,18,22–25,27–30 (0.2010 m/px). Missing: 16,17,26,34–36 |

Corner readings are made from `mosaic.py` contact sheets (grid labels are scan pixels), and
their world positions come from OSM intersections (see `cps*.json`).
