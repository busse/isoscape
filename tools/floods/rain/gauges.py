"""Gauge totals for Gaston around Richmond, Aug. 30 to 31, 2004.

Totals and keys from the research files (drafts/richmond-floods/casestudy/
2026-11-23-03-research-gaston-and-the-weather/rainfall-data.md and sources.md), read 2026-11-23:
  S1  NHC Tropical Cyclone Report AL072004, Table 3 (p8)
  S2  NWS Wakefield Gaston page, preliminary rainfall statement of Aug. 31, 2004
  S8  NCEI Global Hourly, RIC 72401013740
  S9  NCEI GHCN-Daily (coop totals close at the observer's morning reading)
Coordinates: official stations from GHCN-Daily station metadata (NCEI Access Data Service
with includeStationLocation=1, read 2026-11-23). Unofficial reports give a place name only;
their coordinates here are approximate (the named place's usual location), marked
`loc: "approximate"`, and they are not used to correct the radar. Places that cannot be put
on the map honestly ("West End", "St. Mary's School") have no coordinates.
`bias: True` marks the gauges used for the mean-field radar correction: official, located,
and whose reporting period covers 12 UTC Aug. 30 to 06 UTC Aug. 31.
"""

GAUGES = [
    {"name": "Richmond Intl. Airport (RIC)", "short": "Airport", "inches": 6.68, "period": "calendar day Aug. 30 (rain 11:24 a.m. to 10:54 p.m. EDT)",
     "kind": "official", "source": "S1 p8; S8; S9", "lat": 37.51154, "lon": -77.32338, "loc": "GHCN", "bias": True},
    {"name": "Ashland, Hanover Co. airport (ASOS)", "short": "Ashland", "inches": 10.61, "period": "calendar day Aug. 30",
     "kind": "official", "source": "S1 p8; S9", "lat": 37.70926, "lon": -77.43484, "loc": "GHCN", "bias": True},
    {"name": "Sandston (coop)", "short": "Sandston", "inches": 8.10, "period": "24 h to morning of Aug. 31",
     "kind": "official", "source": "S1 p8; S9", "lat": 37.54417, "lon": -77.27583, "loc": "GHCN", "bias": True},
    {"name": "Winterpock (coop)", "short": "Winterpock", "inches": 5.69, "period": "24 h to morning of Aug. 31",
     "kind": "official", "source": "S2; S9", "lat": 37.32459, "lon": -77.64364, "loc": "GHCN", "bias": True},
    {"name": "Hopewell (coop)", "short": "Hopewell", "inches": 4.63, "period": "24 h to morning of Aug. 31 (2.32 more the day before, outside the window)",
     "kind": "official", "source": "S9", "lat": 37.2992, "lon": -77.2775, "loc": "GHCN", "bias": True},
    {"name": "Montpelier (coop)", "short": "Montpelier", "inches": 0.72, "period": "24 h to morning of Aug. 31",
     "kind": "official", "source": "S9", "lat": 37.8644, "lon": -77.6383, "loc": "GHCN", "bias": False,
     "note": "light total; left out of the ratio, where a small value would only add noise"},
    {"name": "Richmond (West End)", "short": "West End", "inches": 12.60, "period": "storm", "kind": "unofficial",
     "source": "S1 p8; S2", "lat": None, "lon": None, "loc": "unknown: the reports say only 'West End' (UNCONFIRMED)", "bias": False},
    {"name": "Richmond (Math & Science Center)", "short": "Math & Sci. Ctr.", "inches": 12.30, "period": "storm", "kind": "unofficial",
     "source": "S1 p8; S2", "lat": 37.547, "lon": -77.383, "loc": "approximate: Mathematics and Science Center, eastern Henrico (UNCONFIRMED)", "bias": False},
    {"name": "Mechanicsville", "short": "Mechanicsville", "inches": 10.70, "period": "storm", "kind": "unofficial",
     "source": "S1 p8; S2", "lat": 37.609, "lon": -77.373, "loc": "approximate: the community's center", "bias": False},
    {"name": "Science Museum of Virginia", "short": "Science Museum", "inches": 6.56, "period": "storm", "kind": "unofficial",
     "source": "S1 p8; S2", "lat": 37.5613, "lon": -77.4675, "loc": "approximate: 2500 W. Broad St.", "bias": False},
    {"name": "St. Christopher's School", "short": "St. Christopher's", "inches": 6.40, "period": "storm", "kind": "unofficial",
     "source": "S1 p8; S2", "lat": 37.578, "lon": -77.519, "loc": "approximate: the school's campus", "bias": False},
    {"name": "Chester", "short": "Chester", "inches": 6.20, "period": "storm", "kind": "unofficial",
     "source": "S2", "lat": 37.356, "lon": -77.441, "loc": "approximate: the community's center", "bias": False},
    {"name": "St. Mary's School", "short": "St. Mary's", "inches": 5.80, "period": "storm", "kind": "unofficial",
     "source": "S2", "lat": None, "lon": None, "loc": "unknown: which St. Mary's is not said", "bias": False},
    {"name": "WWBT TV-12", "short": "WWBT", "inches": 4.80, "period": "storm", "kind": "unofficial",
     "source": "S2", "lat": 37.5115, "lon": -77.504, "loc": "approximate: the station on Midlothian Turnpike", "bias": False},
    {"name": "Midlothian", "short": "Midlothian", "inches": 4.30, "period": "storm", "kind": "unofficial",
     "source": "S2", "lat": 37.506, "lon": -77.649, "loc": "approximate: the community's center", "bias": False},
    {"name": "Clover Hill H.S.", "short": "Clover Hill", "inches": 4.30, "period": "storm", "kind": "unofficial",
     "source": "S2", "lat": 37.413, "lon": -77.642, "loc": "approximate: the school's 2004 site on Hull Street Road (UNCONFIRMED)", "bias": False},
]
