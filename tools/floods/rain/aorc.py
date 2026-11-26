#!/usr/bin/env python3
"""Cut the AORC v1.1 hourly precipitation (1 km) for metro Richmond, Aug. 30 to 31, 2004.

    python3 tools/floods/rain/aorc.py OUT.npz

Dev tool (zarr, s3fs; anonymous access to the public bucket s3://noaa-nws-aorc-v1-1-1km).
Values are stored raw (int16); multiply by the scale_factor 0.1 for mm (kg/m^2). Missing is
-32767. Time is the hour's end (checked against the RIC gauge by the research step).
"""
import sys

import numpy as np
import zarr

g = zarr.open_consolidated("s3://noaa-nws-aorc-v1-1-1km/2004.zarr", storage_options={"anon": True}, mode="r")
lat, lon, tm = g["latitude"][:], g["longitude"][:], g["time"][:]
t = tm.astype("datetime64[s]")
it = np.where((t >= np.datetime64("2004-08-30T12:00")) & (t <= np.datetime64("2004-08-31T07:00")))[0]
ilat = np.where((lat >= 37.15) & (lat <= 37.95))[0]
ilon = np.where((lon >= -77.85) & (lon <= -76.95))[0]
a = g["APCP_surface"][it[0]:it[-1] + 1, ilat[0]:ilat[-1] + 1, ilon[0]:ilon[-1] + 1]
np.savez_compressed(sys.argv[1], apcp=a, lat=lat[ilat], lon=lon[ilon], time=tm[it])
print(a.shape, "chunks: time", it[0] // 144, "lat", ilat[0] // 128, "-", ilat[-1] // 128, "lon", ilon[0] // 256, "-", ilon[-1] // 256)
