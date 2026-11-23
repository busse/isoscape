# Builds floods.json from hand-entered, sourced values. Read date for all sources: 2026-11-23.
import json
NGVD_TO_NAVD = -1.03   # NGS NCAT at both gauges: NAVD88 = NGVD29 - 0.313 m
W_DATUM_NGVD = 98.82   # Westham gauge zero, NGVD29 (OFR 70-51, PP 924, WDR 1986, MARFC)
W_DATUM_NAVD = 98.04   # Westham gauge zero, NAVD88 (USGS site file, GNSS level 2, +/-0.08 ft)
OLD_WB = 2.36          # Weather Bureau gauge near Mayo's Bridge, before Sept 1957 (OFR 70-51 p.119)

def westham(stage, flow, date, src):
    if stage is None: return None
    return {"date": date, "stage_ft": stage, "flow_cfs": flow,
            "elev_ngvd29_ft": round(stage + W_DATUM_NGVD, 2),
            "elev_navd88_ft_from_usgs_datum": round(stage + W_DATUM_NAVD, 2),
            "elev_navd88_ft_from_converted_ngvd": round(stage + W_DATUM_NGVD + NGVD_TO_NAVD, 2),
            "source": src}

def locks(stage, date, era, src, note=None):
    if stage is None: return None
    d = {"date": date, "stage_ft": stage, "gauge_era": era, "source": src}
    if era == "WB_Mayo_1876_1956":
        d["site"] = "Weather Bureau gauge near Mayo's Bridge (old river mile 104.6), 0.9 mi upstream of City Locks"
        d["elev_ngvd29_ft"] = round(stage + OLD_WB, 2)
        d["elev_navd88_ft"] = round(stage + OLD_WB + NGVD_TO_NAVD, 2)
    elif era == "Locks_NGVD29_1957_2007":
        d["site"] = "City Locks, foot of Pear Street (old river mile 103.7)"
        d["elev_ngvd29_ft"] = stage
        d["elev_navd88_ft"] = round(stage + NGVD_TO_NAVD, 2)
    elif era == "Locks_NAVD88_2007_on":
        d["site"] = "City Locks, USGS 02037705"
        d["elev_navd88_ft"] = stage
        d["elev_ngvd29_ft"] = round(stage - NGVD_TO_NAVD, 2)
    elif era == "elevation_given":
        d["site"] = "old river mile 104.6 (near Mayo's Bridge)"
        d["elev_ngvd29_ft"] = stage
        d["elev_navd88_ft"] = round(stage + NGVD_TO_NAVD, 2)
        d["stage_ft"] = None
    if note: d["note"] = note
    return d

S = {
 "USGS_PEAK": "https://nwis.waterdata.usgs.gov/nwis/peak?site_no=02037500&agency_cd=USGS&format=rdb (annual peak file)",
 "NWPS_W": "https://api.water.noaa.gov/nwps/v1/gauges/rmdv2 (flood.crests.historic)",
 "NWPS_L": "https://api.water.noaa.gov/nwps/v1/gauges/ricv2 (flood.crests.historic)",
 "OFR7051": "https://pubs.usgs.gov/of/1970/0051/report.pdf (Table 2, printed p.20; station pages printed pp.118-119)",
 "HA410": "https://pubs.usgs.gov/ha/410/plate-1.pdf (Table 1, Peak stages, James River at Richmond)",
 "PP924": "https://pubs.usgs.gov/pp/0924/report.pdf (Table A4, PDF p.406)",
 "HMDB133685": "https://www.hmdb.org/m.asp?m=133685 (High Water Mark sign, Dock and Pear streets)",
 "NOAA_DSR": "https://www.govinfo.gov/content/pkg/CZIC-gb70-9-u55-1972/html/CZIC-gb70-9-u55-1972.htm (NOAA Final Report of the Disaster Survey Team on the Events of Agnes, Oct 1972)",
 "MARFC1985": "https://www.weather.gov/media/marfc/Flood_Events_2016/1985/Nov4-7%2C1985.pdf",
 "WTVR2020": "https://www.wtvr.com/news/local-news/richmond-closes-floodwall-james-river-to-crest-friday",
 "CBM2025": "https://chesapeakebaymagazine.com/amid-multiple-winter-storms-flooding-prompts-richmond-to-close-floodwall-for-first-time-in-five-years",
 "RVAFAQ": "https://www.rva.gov/public-utilities/news/floodwall-faqs",
 "HENRICO1771": "https://henrico.gov/locations/flood/",
 "MARFC1816": "https://weather.gov/media/marfc/Flood_Events_2016/1816/Sep18%2C1816.pdf",
 "WATSON": "https://corpora.tika.apache.org/base/docs/govdocs1/204/204582.html (Barbara McNaught Watson, Virginia floods chapter)",
 "NWSVA": "https://www.weather.gov/safety/flood-states-va",
 "OFR_TEXT": "https://pubs.usgs.gov/of/1970/0051/report.pdf (text printed pp.19-22)",
 "PP924_TEXT": "https://pubs.usgs.gov/pp/0924/report.pdf (Virginia damage text, PDF p.95)",
 "RVANEWS2011": "https://rvanews.com/?p=41409",
 "RVAH2O": "https://threadreaderapp.com/thread/1326952085598986241.html (City DPU account @rvah2o, Nov 12 2020)",
}

floods = []
def add(**k): floods.append(k)

add(id="1771-05", name="Great Fresh of 1771", dates="1771-05-27", cause="10 to 12 days of rain over the central Blue Ridge (Henrico County; Watson)",
    westham=None,
    city_locks=[locks(38.0, "1771-05-27", "WB_Mayo_1876_1956", S["OFR7051"], "Stage 'c38' on the old Weather Bureau gauge scale, from a Corps of Engineers report based on diary accounts. Elevation is derived here, not published. UNCONFIRMED.")],
    other_heights=[{"value": "about 45 ft above normal", "source": S["HENRICO1771"]},
                   {"value": "record of 30 ft (magazine; conflicts with all agency figures, not trusted)", "source": "https://richmondfamilymagazine.com/community/history/water-water-everywhere/"}],
    flooded="Buildings, boats and animals in Richmond destroyed; about 150 deaths along the river (Henrico County). No street-level account found.",
    confidence="low")
add(id="1816-09", name="Flood of September 1816", dates="1816-09-18", cause="tropical storm",
    westham=None, city_locks=[], flooded="Water entered first floors of some homes; slightly below the 'High Fresh of 1814' (MARFC citing Roth and Cobb).",
    sources=[S["MARFC1816"]], confidence="low; no stage")
add(id="1870-10", name="Flood of October 1870", dates="1870-10-01", cause="UNCONFIRMED (fall rain)",
    westham=None, city_locks=[locks(27.5, "1870-10-01", "elevation_given", S["HA410"]+" footnote a: Corps of Engineers flood plain report, Norfolk District, Sept 1965; OFR 70-51 Table 2 gives stage c25.2 (= 27.56 ft NGVD29)")],
    flooded="UNCONFIRMED: no description found in sources read.", confidence="medium for the elevation, low for impacts")
add(id="1877-11", name="Flood of November 1877", dates="1877-11-26", cause="UNCONFIRMED",
    westham=None, city_locks=[locks(29.0, "1877-11-26", "elevation_given", S["HA410"]+"; OFR 70-51 Table 2 gives stage c26.7 (= 29.06 ft NGVD29)")],
    flooded="UNCONFIRMED", confidence="medium for elevation")
add(id="1886-04", name="Flood of April 1886", dates="1886-04-02", cause="UNCONFIRMED", westham=None,
    city_locks=[locks(25.6, "1886-04-02", "elevation_given", S["HA410"])], flooded="UNCONFIRMED", confidence="medium for elevation")
add(id="1889-06", name="Flood of June 1889", dates="1889-06-02", cause="UNCONFIRMED (same storm system as the Johnstown flood, not confirmed here)", westham=None,
    city_locks=[locks(26.6, "1889-06-02", "elevation_given", S["HA410"])], flooded="UNCONFIRMED", confidence="medium for elevation")
add(id="1901-12", name="Flood of December 1901", dates="1901-12-31", cause="UNCONFIRMED", westham=None,
    city_locks=[locks(23.2, "1901-12-31", "WB_Mayo_1876_1956", S["NWPS_L"]+"; HA-410 Table 1 gives 25.5 ft msl")], flooded="UNCONFIRMED", confidence="medium")
add(id="1935-09", name="Labor Day hurricane flood", dates="1935-09-07", cause="remnants of the 1935 Labor Day hurricane (MARFC tropical list)",
    westham=westham(21.01, 127000, "1935-09-07", S["USGS_PEAK"]),
    city_locks=[locks(23.65, "1935-09-07", "WB_Mayo_1876_1956", S["NWPS_L"]+"; HA-410 Table 1: 25.9 ft msl")], flooded="UNCONFIRMED", confidence="medium")
add(id="1936-03", name="March 1936 flood", dates="1936-03-18/1936-03-20", cause="two rainstorms on snowmelt (MARFC top-10 list)",
    westham=westham(23.42, 175000, "1936-03-19", S["USGS_PEAK"]),
    city_locks=[locks(26.5, "1936-03-20", "WB_Mayo_1876_1956", S["NWPS_L"]+" (NWS lists 1936-03-30; HA-410 Table 1 lists Mar. 20, 28.8 ft msl)"),
                {"date": "1936-03", "site": "City Locks (old river mile 103.7)", "elev_ngvd29_ft": 27.5, "elev_navd88_ft": 26.47, "source": S["PP924"]}],
    flooded="Serious flooding of industrial and business sections (Watson). High-water marks surveyed along the river (HA-410 Figure 1).",
    sources=[S["WATSON"]], confidence="high for elevations")
add(id="1937-04", name="April 1937 flood", dates="1937-04-27", cause="heavy rain over most of Virginia (MARFC)",
    westham=westham(22.65, 152000, "1937-04-27", S["USGS_PEAK"]+" (codes 1,8: daily mean, actual peak greater)"),
    city_locks=[locks(25.2, "1937-04-27", "WB_Mayo_1876_1956", S["NWPS_L"]+"; HA-410 Table 1: 27.5 ft msl")],
    flooded="UNCONFIRMED. Corps floodmarks give a full profile through the falls (HA-410 Figure 1).", confidence="high for profile")
add(id="1940-08", name="August 1940 flood", dates="1940-08-18", cause="1940 Southeast hurricane",
    westham=westham(21.80, 151000, "1940-08-18", S["USGS_PEAK"]), city_locks=[locks(23.3, "1940-08-18", "WB_Mayo_1876_1956", S["NWPS_L"]+"; HA-410: 25.6 ft msl")],
    flooded="UNCONFIRMED", confidence="medium")
add(id="1944-09", name="September 1944 flood", dates="1944-09-20/1944-09-21", cause="1944 Great Atlantic hurricane remnants (UNCONFIRMED; MARFC gives no summary)",
    westham=westham(21.80, 150000, "1944-09-20", S["USGS_PEAK"]), city_locks=[locks(22.4, "1944-09-21", "WB_Mayo_1876_1956", S["NWPS_L"]+"; HA-410: 24.7 ft msl")],
    flooded="UNCONFIRMED", confidence="medium")
add(id="1969-08", name="Camille", dates="1969-08-20/1969-08-23", cause="remnants of Hurricane Camille; 12 to 20 in of rain in 3 to 5 hours upstream (MARFC)",
    westham=westham(24.95, 222000, "1969-08-21 24:00", S["USGS_PEAK"]+"; OFR 70-51 p.118"),
    city_locks=[locks(28.64, "1969-08-22 06:00", "Locks_NGVD29_1957_2007", S["OFR7051"]+" p.119"),
                {"date": "1969-08-22", "site": "old WB site, river mile 104.6", "elev_ngvd29_ft": 29.9, "elev_navd88_ft": 28.87, "source": S["HA410"]}],
    flooded="Lower elevations of the city; Main Street (photo); flood extent mapped on HA-409, HA-410, HA-411. 153 deaths statewide, mostly Nelson County (NWS).",
    sources=[S["OFR_TEXT"], S["HA410"], S["NWSVA"]], confidence="high")
add(id="1972-06", name="Agnes", dates="1972-06-21/1972-06-25", cause="Tropical Storm Agnes",
    westham=westham(28.62, 313000, "1972-06-23 09:00", S["USGS_PEAK"]+"; PP 924 station 612 (discharge includes Kanawha Canal flow)"),
    city_locks=[locks(36.5, "1972-06-23 16:00", "Locks_NGVD29_1957_2007", S["NOAA_DSR"]+"; "+S["PP924"]),
                {"date": "1972-06-23", "site": "High Water Mark sign, Dock and Pear streets (Great Shiplock Park)", "elev_navd88_ft": 35.5, "height_above_ground_ft": 17, "source": S["HMDB133685"]},
                {"date": "1972-06-23", "site": "High Water Mark sign, Tredegar St at Brown's Island Way", "elev_navd88_ft": 40.0, "height_above_ground_ft": 3, "source": "https://www.hmdb.org/m.asp?m=124035", "note": "Lower than the 1969 profile at about the same river mile; see datums.md"}],
    flooded="Downtown flooded and lost power, water and communications; water purification plant inundated; 4 of 5 James bridges closed; evacuations from June 22 (NOAA DSR). Water and sewage, electric and gas plants flooded (NWS, PP 924). Sign text: 13 local deaths, over $140 million local damage.",
    sources=[S["NOAA_DSR"], S["PP924_TEXT"], S["HMDB133685"]], confidence="high")
add(id="1972-10", name="October 1972 flood", dates="1972-10-07", cause="low pressure and cold front, 6 to 8 in in the Shenandoah Valley (MARFC)",
    westham=westham(21.76, 162000, "1972-10-07", S["USGS_PEAK"]), city_locks=[locks(24.2, "1972-10-07", "Locks_NGVD29_1957_2007", S["NWPS_L"])],
    flooded="UNCONFIRMED", confidence="medium")
add(id="1979-02", name="February 1979 flood", dates="1979-02-27", cause="UNCONFIRMED", westham=westham(20.38, 138000, "1979-02-27", S["USGS_PEAK"]),
    city_locks=[locks(22.5, "1979-02-27", "Locks_NGVD29_1957_2007", S["NWPS_L"])], flooded="UNCONFIRMED", confidence="medium")
add(id="1985-11", name="Election Day flood (Juan)", dates="1985-11-04/1985-11-07", cause="Juan's moisture on Nov 1-3, then a slow coastal low with 6 to 14 in (NWS)",
    westham=westham(24.77, 218000, "1985-11-07 08:00", S["USGS_PEAK"]+"; WDR 1986 PDF p.230; "+S["MARFC1985"]),
    city_locks=[locks(30.76, "1985-11-07", "Locks_NGVD29_1957_2007", S["NWPS_L"])],
    flooded="Several blocks of commercial and industrial buildings downtown (Watson; JRA). Statewide 22 deaths, about $800 million (NWS). Led to the floodwall's authorization in 1986 (RVAH2O).",
    sources=[S["WATSON"], S["NWSVA"], S["RVAH2O"]], confidence="high for crest, low for street detail")
add(id="1987-04", name="April 1987 flood", dates="1987-04-18", cause="strong mid-latitude cyclone (MARFC)", westham=westham(21.91, 163000, "1987-04-18", S["USGS_PEAK"]),
    city_locks=[], flooded="UNCONFIRMED; no City Locks crest found in the NWS list", confidence="medium")
add(id="1996-01", name="Blizzard melt flood", dates="1996-01-19/1996-01-22", cause="2 to 4 ft of snow melted by rain (Watson; city FAQ)",
    westham=westham(20.63, 141000, "1996-01-21 20:30", S["NWPS_W"]), city_locks=[locks(22.05, "1996-01-22", "Locks_NGVD29_1957_2007", S["NWPS_L"])],
    flooded="First flood after the wall; some gates closed including Dock Street (RVANews 2011).", sources=[S["RVAFAQ"], S["RVANEWS2011"]], confidence="medium")
add(id="1996-09", name="Fran", dates="1996-09-06/1996-09-08", cause="remnants of Hurricane Fran",
    westham=westham(21.23, 152000, "1996-09-08 14:00", S["USGS_PEAK"]), city_locks=[locks(23.75, "1996-09-08 21:00", "Locks_NGVD29_1957_2007", S["NWPS_L"])],
    flooded="Highest river since the wall was built; city FAQ gives 23.8 ft. Some gates closed (RVANews 2011).", sources=[S["RVAFAQ"]], confidence="medium; Locks datum era assumed")
add(id="2003-02", name="February 2003 flood", dates="2003-02-25", cause="UNCONFIRMED (rain on snow)", westham=westham(18.73, 113000, "2003-02-25 00:30", S["USGS_PEAK"]),
    city_locks=[locks(17.76, "2003-02-25 10:00", "Locks_NGVD29_1957_2007", S["NWPS_L"])], flooded="No floodwall closure reported (DPU said no flood closure 1999 to 2020).", confidence="medium")
add(id="2010-01", name="January 2010 flood", dates="2010-01-27", cause="UNCONFIRMED", westham=westham(18.10, 104000, "2010-01-27 11:15", S["USGS_PEAK"]),
    city_locks=[{"date": "2010-01-27", "stage_ft": 15.92, "source": S["NWPS_L"], "note": "NOAA station 8638495 lists highest observed water 5.408 m above MLLW on 2010-01-27, which is 16.93 ft on its station datum labeled NAVD88. The 1.0 ft gap equals the NGVD29-NAVD88 shift. Datum of this NWS value UNCONFIRMED."}],
    flooded="UNCONFIRMED", confidence="low for the Locks datum")
add(id="2020-11", name="November 2020 flood", dates="2020-11-12/2020-11-14", cause="heavy rain in the western James basin",
    westham=westham(18.33, 108000, "2020-11-14 00:15", S["USGS_PEAK"]), city_locks=[locks(16.96, "2020-11-14 04:48", "Locks_NAVD88_2007_on", S["NWPS_L"])],
    flooded="Dock Street and Brander Street gates closed Nov 12 and Low Line doors closed; first flood closure since 1999 (WTVR; RVAH2O).", sources=[S["WTVR2020"], S["RVAH2O"]], confidence="high")
add(id="2025-02", name="February 2025 flood", dates="2025-02-16/2025-02-18", cause="winter storms with rain",
    westham=westham(17.14, 91600, "2025-02-18 12:00", S["USGS_PEAK"]+" (NWS provisional crest 17.23 ft, 92,822 cfs at 20:15 UTC)"),
    city_locks=[locks(14.62, "2025-02-18 18:42", "Locks_NAVD88_2007_on", S["NWPS_L"])],
    flooded="Dock Street floodwall closed Feb 17, Dock Street shut between 17th and 21st streets (Chesapeake Bay Magazine; The Richmonder).", sources=[S["CBM2025"]], confidence="high")

out = {"generated": "2026-11-23", "read_date_all_sources": "2026-11-23",
       "conventions": {"NGVD29_to_NAVD88_ft": NGVD_TO_NAVD, "ncat_source": "https://geodesy.noaa.gov/api/ncat/llh (both gauge coordinates, -0.313 m)",
                       "westham_gauge_zero_NGVD29_ft": W_DATUM_NGVD, "westham_gauge_zero_NAVD88_ft": W_DATUM_NAVD,
                       "old_weather_bureau_gauge_zero_NGVD29_ft": OLD_WB,
                       "city_locks_gauge_zero": "0.0 NGVD29 from Sept 1957 (OFR 70-51); 0.0 NAVD88 now (USGS 02037705, elevation series from 2007-10-01). Switch date UNCONFIRMED.",
                       "derived_values": "Every elev_* field is computed in tools/build_floods_json.py from the stage and the datum above unless a source gives the elevation directly."},
       "floods": floods}
json.dump(out, open("/home/claude/floods-research/river/floods.json", "w"), indent=1)
print(len(floods), "records")
