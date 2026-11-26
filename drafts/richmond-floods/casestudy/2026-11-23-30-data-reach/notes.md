# 30. What the public archives gave (20:06 to 20:20)

Opus 5.5 subagent, branch `feature/flood-rain`. Probed every source in the research's
`rainfall-data.md` from the cloud container, anonymous HTTPS only, no forms or accounts.

- NEXRAD Level II, KAKQ: the `noaa-nexrad-level2` bucket answered 403; the Unidata bucket
  (`unidata-nexrad-level2`) listed 339 volumes a day. 268 volumes for 11:30 UTC Aug. 30 to
  06:30 UTC Aug. 31 (602 MB) downloaded and checked against their S3 MD5s
  (`tools/floods/rain/manifest-radar.json`, `fetch.py`), processed, then deleted for disk.
- AORC v1.1 (1 km, hourly): read anonymously from the Zarr store; one chunk holds the area
  (`manifest-aorc.json`). This is how the research step got its values too.
- Stage IV: NSF NCAR EOL's order form answered "Dataset is not currently available" (and a
  form is out of bounds anyway). The Iowa Environmental Mesonet keeps a public archive of the
  same GRIB1 files: 18 hourly, three 6-hourly and one 24-hourly file used.
- Also reached: NCEI Global Hourly (RIC), GHCN-Daily with station positions, NCEI HOMR
  (KAKQ's position), NOAA Atlas 14 PFDS, USGS 3DEP exportImage, Census TIGER 2023, HURDAT2.
- Nothing needed is left for the Mac. `manifest-other.json` lists the rest with sizes.
- Dev tools installed with pip: Py-ART 2.3.0, zarr 3.4.2 with s3fs, pygrib 2.1.8. The build
  itself gains no dependency.
