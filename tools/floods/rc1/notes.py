"""Floods series, final draft rc1: every word the sheets print, with its sources, written to
drafts/richmond-floods/notes.json. The sheets (tools/floods/rc1/sheet.py) read their titles, box
titles and notes, key labels and credits from that file, so what it lists is what they print.
Plate captions are read from each built plate's `info` (the counts filled in), beside the
sources of the flood's level.

    python3 tools/floods/rc1/notes.py <plates-dir>

Sources are given as a URL or as a file (and page) in the series' research: the copies in
drafts/richmond-floods/casestudy/2026-11-23-02 to -05 (river, Gaston, FEMA and second read, the
period city) and later steps. `checked` says what the source does and does not support, and
`changed` records each place where an earlier draft said more than the research supports.
Written with Claude for Chris Busse, November 25, 2026.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STAGE, VERSION = 'FINAL DRAFT rc3', '1.0.0-rc3'
R02 = 'drafts/richmond-floods/casestudy/2026-11-23-02-research-river-floods-and-the-wall/'
R03 = 'drafts/richmond-floods/casestudy/2026-11-23-03-research-gaston-and-the-weather/'
R04 = 'drafts/richmond-floods/casestudy/2026-11-23-04-fema-profiles-and-second-read/'
R05 = 'drafts/richmond-floods/casestudy/2026-11-24-05-sources-for-the-1969-72-city/'

S = {  # the sources used below, by key
    'nws-ricv2': 'NWS National Water Prediction Service, City Locks gauge RICV2: historic crests and impact stages (41 ft "Flood wall is overtopped"; 27 ft 21st and Cary closed; 24 ft Mayo Bridge closed), https://api.water.noaa.gov/nwps/v1/gauges/ricv2 (copy: floods-research/river/raw/nwps_ricv2.json); summarized in ' + R02 + 'floods.md, "NWS impact stages"',
    'noaa-agnes': 'NOAA, Final Report of the Disaster Survey Team on the Events of Agnes, Oct. 1972, https://www.govinfo.gov/content/pkg/CZIC-gb70-9-u55-1972/html/CZIC-gb70-9-u55-1972.htm',
    'pp924': 'USGS Professional Paper 924, Table A4, PDF p. 406, https://pubs.usgs.gov/pp/0924/report.pdf',
    'agnes-sign': 'Agnes high-water sign, Dock and Pear streets, 17 ft above ground, 35.5 ft NAVD88, https://www.hmdb.org/m.asp?m=133685',
    'ofr70-51': 'USGS Open-File Report 70-51, station 02-0377.00, printed p. 119 (PDF p. 131) and Table 2, printed p. 20, https://pubs.usgs.gov/of/1970/0051/report.pdf',
    'ha410': 'USGS Hydrologic Atlas HA-410 (1969), Table 1 and Figure 1, and its mapped extent of the 1969 flood, https://pubs.usgs.gov/ha/410/plate-1.pdf',
    'levels': R04 + 'levels.json (the checked drawing levels) and second-read.md',
    'datums': R02 + 'datums.md; NGVD29 to NAVD88 -1.03 ft at the Locks (second-read.md, "Datums")',
    'usgs-iv': 'USGS 02037705 (James River at City Locks), parameter 62620 (NAVD88), approved instantaneous values: 16.96 ft, Nov. 14, 2020 (second-read.md)',
    'marker': 'Corps of Engineers and City of Richmond, "Richmond Local Flood Protection" marker, Dock and 17th streets (dedicated Oct. 21, 1994; 750 acres, 150 Shockoe and 600 Manchester; closures), https://www.hmdb.org/m.asp?m=23953; ' + R02 + 'floodwall.md',
    'city-faq': 'City of Richmond DPU, "Floodwall FAQs" (the gravity U-wall west of the Mayo Bridge, 43 ft from top to river\'s edge), https://www.rva.gov/public-utilities/news/floodwall-faqs; ' + R02 + 'floodwall.md, "Heights above ground"',
    'wrda1986': 'Water Resources Development Act of 1986, sec. 401(a), 100 Stat. 4126: "Such project shall include flood protection for the Richmond municipal wastewater treatment facility" (copy: floods-research/river/raw/pdf/wrda1986.txt, line 2885), https://www.govinfo.gov/content/pkg/STATUTE-100/pdf/STATUTE-100-Pg4082.pdf; ' + R02 + 'floodwall.md',
    'osm-levee': R02 + 'floodwall.md, "Coordinates from OpenStreetMap": the earthen levee from I-95 to Goodes Street is missing from OSM in the cache',
    'post2004': 'Washington Post, "Bottom\'s Up," Nov. 30, 2004 (most water converged on 17th and Main; Havana \'59, 13 ft up the dining-room wall; Main Street Station "escaped damage"), https://www.washingtonpost.com/wp-dyn/articles/A23727-2004Nov30.html; ' + R03 + 'sources.md S28',
    'nbc12-2022': 'NBC12, "Remembering the destruction of Hurricane Gaston 18 years later," Aug. 30, 2022 (Bottoms Up: 6 ft 2 in inside, above a 3 ft step), https://www.12onyourside.com/2022/08/30/remembering-destruction-hurricane-gaston-18-years-later/; sources.md S31',
    'wtvr2024': 'WTVR, "Richmond Remembers: How Gaston flooded Shockoe Bottom," Aug. 30, 2024 ("rapids" at 15th and Main), https://wtvr.com/news/local-news/richmond-remembers-tropical-storm-gaston-aug-30-2024; sources.md S33',
    'ap2004': 'AP via Insurance Journal and Fox News, Aug. 31 to Sept. 20, 2004 ("up to 10 feet"; the gates open), sources.md S22 to S27',
    'gaston-open': 'The floodwall\'s openings stayed open in Gaston: AP (Insurance Journal, Sept. 20, 2004, S22); NBC12, Sept. 1, 2017 (S29) and Sept. 11, 2018 (S30); ' + R03 + 'gaston-mechanism.md',
    'gaston-river': 'USGS 02037500 (Westham) discharge, Aug. 30, 2004: peak 14,800 cfs at 9:15 p.m., against 42,000 cfs for minor flooding (NWS RMDV2); ' + R03 + 'gaston-timeline.md, S10 and S12',
    'gaston-rain': 'Six to more than twelve inches in about eight hours: NHC Tropical Cyclone Report AL072004, Table 3 p. 8, https://www.nhc.noaa.gov/data/tcr/AL072004_Gaston.pdf; RIC airport hourly record (S8); ' + R03 + 'gaston-timeline.md',
    'gaston-depths': R03 + 'gaston-water.md, sections 2 and 4: the reports imply a surface between about 24 and 35 ft NAVD88; "up to 10 ft" at the low point gives 27 to 28 ft',
    'spill': 'drafts/richmond-floods/casestudy/2026-11-23-15-spill-path/ (spill.json; the low point, 4.07 m NAVD88, a pit beside the 17th Street Market) and step 20 (17th and Main corrected)',
    'creek': 'The Richmonder, Sept. 24, 2024 (Shockoe Creek runs buried to 17th and Dock), https://www.richmonder.org/helene-and-the-hidden-creek-2/; ' + R03 + 'sources.md S35',
    'closure-dock': R02 + 'floodwall.md, "Closures": the 17th Street closure on Dock Street (DPU thread; WTVR, Nov. 12, 2020)',
    'nr1980': 'National Register nomination, Shockoe Valley and Tobacco Row Historic District, 1980 survey, https://npgallery.nps.gov/GetAsset/2f9dd6b2-9d0e-4544-89d4-7071fc6d0063; ' + R05 + 'sources.md; check in drafts/richmond-floods/casestudy/2026-11-24-44-national-register-1980-check/',
    'osm': 'OpenStreetMap contributors (ODbL), in the cache data/richmond-i195-rocketts/osm.json (fetched November 14, 2026)',
    'retention': 'The Shockoe retention basin on Chapel Island, built 1983 (virginiaplaces.org, a secondary source; floodwall.md, "Shockoe drainage")',
    'rvanews2011': 'RVANews, May 12, 2011, https://rvanews.com/?p=41409 (some gates, including Dock Street, closed in the 1996 floods; floodwall.md)',
    'wtvr2020': 'WTVR, Nov. 12, 2020, https://www.wtvr.com/news/local-news/richmond-closes-floodwall-james-river-to-crest-friday (Dock Street closure at noon; floodwall.md)',
    'counts': 'drafts/richmond-floods/counts.json, "rc3" (tools/floods/d3/boxcounts.ts: depth at a box\'s center on the 2 m lidar; buildings in water)',
    'lidar': 'USGS 3DEP lidar, 2 m, NAVD88, in the cache data/richmond-i195-rocketts/dem.bin.gz',
    'rain-radar': ('Rain over the Shockoe Creek watershed, by hour: NEXRAD Level II, KAKQ Wakefield (NOAA, via the Unidata bucket on AWS), tropical Z = 250 R^1.2, '
                   'corrected to gauges (NCEI GHCN-Daily and Global Hourly; NWS Wakefield and NHC reports); the watershed (31 square km, 12 sq mi) computed from USGS 3DEP. '
                   'Computed for this series with Claude on branch feature/flood-rain: tools/floods/rain/data/rain.json ("basin_hourly", "basin_total"); method in tools/floods/rain/radar.py and watershed.py'),
    'rain-events': (R03 + 'sources.md: S20 (Style Weekly, quoting the weather service: the first flash-flood warning, 3:58 p.m.), S5 (NCEI Storm Events: flash flooding '
                    'begins 4:30; the file labels its times EST, and whether that means standard time, so 5:30 p.m. EDT, is not confirmed; hence "about 4:30, flooding reported"), '
                    'S18 (the 2009 lawsuit alleges flooding by 4:30), S23 (AP via Insurance Journal: a car afloat in the Bottom about 6:30), S10 and S12 (USGS 02037500 Westham: peak 14,800 cfs at 9:15 p.m.); '
                    'Storm Events times are labeled EST in the file, so they may be an hour late (tools/floods/rain/figures.py on feature/flood-rain)'),
    'spill-cityside': ('drafts/richmond-floods/casestudy/2026-11-23-15-spill-path/: the Bottom spills to the river at about 19 ft (5.8 m NAVD88) on the lidar; '
                       'with the gates open (gaston-open) and the James far below flood (gaston-river), water reaching the openings ran out to the river and could not stand there at 28 ft'),
    'nhc-gaston': 'NHC Tropical Cyclone Report AL072004 (Gaston), Table 1: a tropical depression over North Carolina and Virginia on Aug. 30, 2004, https://www.nhc.noaa.gov/data/tcr/AL072004_Gaston.pdf; ' + R03 + 'gaston-timeline.md, section 1',
    'evidence': 'history/evidence/richmond-floods.json and drafts/richmond-floods/casestudy/2026-11-24-40 to -47 (the period city: Sanborn traces, the 1974 USGS orthophoto, City of Richmond 1999 and VGIN 2002, 2017, 2021 orthophotos)',
    'town1788': 'history/richmond-floods.json and history/sanborn (the town of about 1788 as recorded and traced); 1771 level: ofr70-51 (diaries, via the Corps), levels.json',
}

LEVEL_SOURCES = {
    '1771': ['ofr70-51', 'levels', 'datums'], '1936': ['pp924', 'ha410', 'levels', 'datums'], '1969': ['ofr70-51', 'ha410', 'pp924', 'levels'],
    '1972': ['noaa-agnes', 'pp924', 'nws-ricv2', 'agnes-sign', 'levels'], '1985': ['nws-ricv2', 'levels', 'datums'], '1996': ['nws-ricv2', 'levels', 'marker'],
    '2020': ['usgs-iv', 'nws-ricv2', 'levels', 'marker'], 'agnes-today': ['levels', 'nws-ricv2', 'marker'], 'agnes-today-nowall': ['levels'],
    'gaston-b': ['post2004', 'nbc12-2022', 'wtvr2024', 'ap2004', 'gaston-open', 'gaston-river', 'gaston-rain', 'gaston-depths'],
}

BOXES = {
    'shockoe': {
        'market': ('17th Street Market', "Beside it lies the Bottom's lowest point on the lidar, a pit at 13.4 ft; water stood here in every river flood drawn before the wall.", ['spill', 'counts'],
                   'rc2 (fact 5): "the lowest ground of the Bottom" was too strong (box 3\'s center is lower); the pit is step 15\'s low point (4.07 m, 13.4 ft), beside the market. "Every river flood drawn before the wall": 1936, 1969, 1972, 1985 in this drawing (counts.json rc2).'),
        'station': ('Main Street Station and its train shed', "Camille's mapped water (USGS) reached about this far up the valley.", ['ha410'],
                    'HA-410 as read in floods.md ("up to about Main Street Station").'),
        'dock': ("17th and Dock, the canal's end", "Buried Shockoe Creek runs south under the valley to 17th and Dock; today the wall's 17th Street closure crosses Dock Street here.", ['creek', 'closure-dock', 'marker'],
                 'rc2 (fact 10): the source says the creek "runs south from north of I-64 to 17th and Dock" (S35); "reaches the James" was an inference.'),
        'slip': ('Shockoe Slip, 14th and Cary', "Where the water's edge meets the rise to downtown.", ['lidar', 'counts'], 'A statement about the drawing, true on 1969, 1972 and 1985 (the water\'s edge crosses the box: 0.5, 3.7 and 1.3 acres wet, counts.json rc3); 1936 has its own note.'),
        'canal': ('The canal at Virginia and Byrd streets', "The canal's riverfront: in the water in every river flood drawn before the wall; behind its west end (12th and Byrd) since.", ['counts', 'city-faq', 'osm'],
                  'Wet in 1936, 1969, 1972 and 1985 and dry behind the wall in 1996, 2020 and at the 1972 height today, in this drawing (counts.json rc2); the wall runs from 12th and Byrd to 21st and East Cary (City FAQ, floodwall.md). Names from OSM.'),
        'cary18': ('18th and Cary streets', 'Warehouses between Cary and Dock streets, in the water in every river flood drawn here before the wall.', ['counts', 'osm'],
                   'rc2 (fact 8): "Tobacco Row\'s west end" had no source and is dropped. A count of this drawing.'),
        'franklin': ('East Franklin and Grace, 17th to 19th', 'The 1980 National Register survey dates the Franklin Street row, 1703 to 1721, from about 1842 (the Anson Richards houses) to about 1950.', ['nr1980'],
                     'rc2 (fact 1): rc1 said "from 1842 to 1913"; the survey extract has 1705 at about 1930 and 1718 at about 1950 (step 44).'),
        # The Gaston sheet's own boxes (Chris, rc2): places with water or a named report.
        'g-market': ("17th Street Market and Havana '59 (pins A, B)", "A: most of the water came together at 17th and Main (Washington Post). B: Havana '59, at its usual address: water 13 ft up the dining-room wall, by the owner's account; on the lidar's 18 ft ground that is about 31 ft, in the hatch.",
                     ['post2004', 'gaston-depths', 'lidar'], 'Ground at the pin from the 2 m lidar: 18.4 ft; 18.4 + 13 = 31.4 ft. The address is the business\'s usual one, not stated in the source (gaston-water.md, section 2).'),
        'g-dock': ('Bottoms Up, 17th and Dock (pin C)', 'C: Bottoms Up, at its usual address: "6 ft 2 in inside, above a 3 ft step" (the owner, NBC12), about 9 ft over the street; on the lidar\'s 18 ft ground that is about 27 ft, as drawn.',
                   ['nbc12-2022', 'gaston-depths', 'lidar'], 'The source\'s own words; ground at the pin 18.2 ft (2 m lidar); 18.2 + 9.2 = 27.4 ft.'),
        'g-station': ('15th and Main, Main Street Station (pins D, E)', 'D: "rapids" at 15th and Main (a developer, WTVR). E: Main Street Station escaped damage (Washington Post), though still water at 28 ft would stand about 3 ft at its door: the water ran through here and did not stand at one level.',
                      ['wtvr2024', 'post2004', 'lidar'], 'Ground at pin E 25.2 ft (2 m lidar), so 2.8 ft under a 28 ft level; the reports and a level surface do not agree here, and the note says so.'),
        'g-valley': ('The valley above: 17th Street to Franklin', 'Runoff from Church Hill and the Capitol slope ran into the Bottom (AP); here the hatch reaches the reports\' upper figure, 35 ft.',
                     ['ap2004', 'gaston-depths'], 'S22 (Insurance Journal, AP, Sept. 20, 2004): runoff off Church Hill and the Capitol slope into the Bottom.'),
        # The with-wall sheets' boxes (1996, 2020); notes per sheet below.
        'w-market': ('17th Street Market, behind the wall', '', ['counts'], ''),
        'w-dock': ("17th and Dock, the wall's Dock Street closure", '', ['closure-dock'], ''),
        'w-canal': ("The canal at Virginia and Byrd, the wall's west end", "The north wall begins at 12th and Byrd; west of its end the canal's riverfront is open to the river.", ['city-faq', 'osm'], 'City FAQ via floodwall.md (12th and Byrd to 21st and East Cary).'),
        'w-chapel': ('Chapel Island, outside the wall', '', ['counts'], ''),
        'w-shiplock': ("Great Shiplock Park, past the wall's east end", "The north wall ends at 21st and East Cary; past it the park and the canal's lock lie open to the river.", ['city-faq', 'osm'], 'City FAQ via floodwall.md; names from OSM.'),
    },
    'manchester': {
        'hull': ('Hull Street at the Mayo Bridge', "The bridge's south foot, inside the wall: dry with it at the 1972 height, deep without.", ['counts', 'marker'], 'A count of this drawing.'),
        'flats': ('The flats at 5th and Stockton', "Warehouses and shops on the flats; USGS mapped Camille's water across them to about Commerce Road.", ['ha410'], 'HA-410 as read in floods.md, "What flooded".'),
        'tanks': ('The tank farm', 'Fuel storage tanks on the flats (as OSM tags them), behind the wall.', ['osm'], 'OSM: man_made=storage_tank, content=fuel (7 tanks).'),
        'wall': ('On the wall', "Just west of the Mayo Bridge the wall is a gravity U-wall, 43 ft from its top to the river's edge (City FAQ).", ['city-faq'], 'rc2 (fact 6): "its tallest part" dropped; rc3 (F2): "Just west", the FAQ\'s place.'),
        'plant': ('The treatment plant grounds', 'The 1986 law says the project "shall include flood protection for the Richmond municipal wastewater treatment facility"; our map data cannot show the levee, so with the wall this ground is drawn as not known.',
                  ['wrda1986', 'osm-levee'], 'WRDA 1986, 100 Stat. 4126 (floods-research/river/raw/pdf/wrda1986.txt, line 2885).'),
    },
}
# Notes that differ by sheet: {sheet: {box: (note, sources, checked)}}.
SHEET_NOTES = {
    'shockoe-1996': {
        'w-market': ("Behind the wall: dry at Fran's height. Before the wall, in 1972, the water stood 15 ft at 17th and Main.", ['counts'], 'Depths from counts.json rc2 (the 1972 gauge at 17th and Main).'),
        'w-dock': ('In January 1996 some gates were shut, Dock Street among them; in Fran, some gates.', ['closure-dock', 'rvanews2011'], 'rc3 (F1): RVANews, May 12, 2011 names Dock Street for January 1996 and only "some gates" for Fran (floodwall.md, "Every closure").'),
        'w-chapel': ("Outside the wall, between it and the river: at Fran's height the island lay under about 10 ft of water.", ['counts', 'levels'], 'rc3: the box shows water only, so the note says what it shows; 9.7 ft at the box\'s center (counts.json rc3).'),
    },
    'shockoe-1936': {
        'slip': ('Where the rise to downtown begins: in 1936 the water only touched the edge of this box; in 1969, 1972 and 1985 it reached into it.', ['counts'], 'rc3 (A10): 1936 has under 0.05 acres wet in the box and 1 building touching the water; 1969 0.5, 1972 3.7, 1985 1.3 acres (counts.json rc3).'),
    },
    'shockoe-2020': {
        'w-market': ('Behind the wall: dry at the November 2020 height. Before the wall, in 1972, the water stood 15 ft at 17th and Main.', ['counts'], 'Depths from counts.json rc2.'),
        'w-dock': ('The 17th Street closure on Dock Street was shut at noon on November 12, 2020.', ['closure-dock', 'wtvr2020'], 'WTVR, Nov. 12, 2020 (floodwall.md, "Every closure").'),
        'w-chapel': ('Outside the wall, between it and the river: at the November 2020 height shallow water covered most of the island.', ['counts', 'levels'], 'rc3: 3.8 ft at the box\'s center, 3.5 of its 3.8 acres wet (counts.json rc3).'),
    },
    'manchester-1996-2020': {
        'plant': ('With the wall this ground is drawn as not known; the weather service puts the plant\'s main access, Maury to Brander Street, under water at 18.5 ft, above the 2020 level.', ['nws-ricv2', 'wrda1986'], 'NWS RICV2 impacts: 18.5 ft, "The main access into the waste water treatment plant is flooded from Maury Street into Brander Street."'),
    },
}

KEY = [
    ('Water, by depth (ft)', "palette.ts flood tones; depth = the flood's level less the 5 m ground grid (the gauges and the boxes' figures read the 2 m lidar at their place)", ['lidar', 'levels']),
    ('The river, canal and basins at their own level', "the lidar's water surface, in the flood look's channel color on every flood sheet", ['lidar']),
    ('Hatched: the range of an estimate', "the flood's level to the top of its stated range (1771 ±3 ft; Fran +1 ft; Gaston 28 to 35 ft)", ['levels', 'gaston-depths']),
    ('Cross-hatched: not known; the earthen levee is not mapped (the edges assume where it runs)', "land the with-wall fill reaches only because the levee is not in our data (flood.ts `unknown`); no water and no depth are drawn there; its edges follow the two lines assumed for the levee's course (floods.py UNKNOWN)", ['osm-levee', 'wrda1986']),
    ('A building of the year', 'standing that year by year built, traced maps or air photos', ['evidence']),
    ('A building standing in 1788 (by its year built)', "today's buildings dated before 1788, and curated ones, as the downtown history draws them", ['town1788']),
    ('Grey, dashed roof edge: on an earlier map or photo, not ascertained for the year', 'evidence calls', ['evidence']),
    ('The floodwall (1994), where it stands', 'dedicated October 21, 1994; its top drawn at the 41 ft stage at which the weather service says the wall is overtopped, not a surveyed top', ['marker', 'nws-ricv2']),
    ('A bridge deck under the water (deck heights are estimates)', "a deck piece whose deck, at its middle, lies below the water: drawn faintly on the surface. Deck heights are the region's rules over the ground or river, not surveys", ['nws-ricv2']),
    ('A depth gauge, the figure in feet', "the flood's level less the 2 m lidar at the place", ['lidar', 'levels']),
    ('Lettered pins: places named in reports', "pins at 17th and Main, 16 N. 17th St., 1700 Dock St., 15th and Main and the station; the two addresses are the businesses' usual ones, not stated in the sources (gaston-water.md, section 2)", ['post2004', 'nbc12-2022', 'wtvr2024']),
    ('Dry twin: the same city with no flood', 'every plate has a pixel-aligned twin with the water taken away', []),
]

# rc3 (N3): the Gaston sheet's rain panel, from the rain branch's checked numbers (rain-radar,
# rain-events): the watershed's rain by hour, 1 p.m. to 11 p.m. EDT, Aug. 30, 2004.
RAIN = {
    'title': 'The rain over the land that drains to the Bottom, by hour',
    'hours': [13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
    'inches': [0.094, 1.444, 1.641, 1.535, 2.216, 1.308, 1.679, 0.344, 0.056, 0.005],
    'low': [0.078, 1.195, 1.359, 1.271, 1.834, 1.082, 1.389, 0.285, 0.046, 0.004],
    'high': [0.105, 1.619, 1.84, 1.721, 2.484, 1.466, 1.882, 0.386, 0.062, 0.005],
    'events': [[15 + 58 / 60, '3:58 first flash-flood warning'], [16.5, 'about 4:30, flooding reported'], [18.5, 'about 6:30 a car afloat in the Bottom'],
               [21.25, '9:15 the James peaks, far below flood']],
    'caption': ('About 10 inches of rain (8.6 to 11.6 by the estimates) fell on the 12 square miles that drain to Shockoe Bottom, most of it '
                'between 2 and 9 p.m., while the James stayed far below flood. Gaston was a tropical depression over Richmond while the rain fell (National Hurricane Center). Bars: the hourly average over the watershed; whiskers: the range of estimates.'),
    'source': ('Rain: NEXRAD radar (NOAA, Wakefield) corrected to rain gauges (NCEI), averaged over the watershed from USGS 3DEP; computed for this series with Claude. '
               'Times: the weather service warning, NCEI Storm Events, AP, USGS (Westham gauge).'),
    'sources': ['rain-radar', 'rain-events', 'gaston-river', 'nhc-gaston'],
    'checked': 'Numbers copied from tools/floods/rain/data/rain.json on feature/flood-rain (basin_hourly radar_corrected, low, high; basin_total 10.34, low 8.56, high 11.6; watershed 31.49 sq km). Event times as the rain branch\'s hyetograph gives them (figures.py EVENTS).',
}

CREDITS = {
    'shockoe': ('Water levels: USGS (high-water marks, PP 924, HA-410), NOAA and the National Weather Service. Ground: USGS 3DEP lidar. '
                'Buildings: © OpenStreetMap contributors (ODbL); City of Richmond assessor; Sanborn maps, Library of Congress; '
                'air photos: USGS 1974 orthophoto, City of Richmond 1999 and VGIN 2002, 2017 and 2021 orthophotos.'),
    'shockoe-2004': ("Water: news reports (AP, Washington Post, NBC12, WTVR) set on the USGS 3DEP lidar; the river's flow, USGS. "
                     'Buildings: © OpenStreetMap contributors (ODbL); City of Richmond assessor; Sanborn maps, Library of Congress; '
                     'air photos: USGS 1974 orthophoto, City of Richmond 1999 and VGIN 2002, 2017 and 2021 orthophotos.'),
    'manchester': ('Water levels: USGS (high-water marks, PP 924, HA-410), NOAA and the National Weather Service. Ground: USGS 3DEP lidar. '
                   'Buildings: © OpenStreetMap contributors (ODbL); City of Richmond assessor.'),
    'shockoe-1771': ("Water level: USGS Open-File Report 70-51 (the Corps of Engineers' 38 ft near Mayo's Bridge, from diaries). Ground: USGS 3DEP lidar, today's. "
                     "Town: isoscape's downtown history (the 1737 plan; buildings dated before 1788 by OpenStreetMap, © its contributors (ODbL), "
                     'and the City of Richmond assessor; curated features with their sources).'),
}
BYLINE = 'Drawn with isoscape by Chris Busse; made in code with Claude.'

SHEETS = [
    # id, area, plate, second (Manchester), title
    ('shockoe-1972', 'shockoe', '1972:1972', None, 'Shockoe Bottom in flood: Hurricane Agnes, June 1972'),
    ('shockoe-1936', 'shockoe', '1936:1936', None, 'Shockoe Bottom in flood: March 1936'),
    ('shockoe-1969', 'shockoe', '1969:1969', None, 'Shockoe Bottom in flood: Hurricane Camille, August 1969'),
    ('shockoe-1985', 'shockoe', '1985:1985', None, 'Shockoe Bottom in flood: the Election Day flood, November 1985'),
    ('shockoe-1996', 'shockoe', '1996:1996', None, 'Shockoe Bottom: Hurricane Fran, September 1996, against the new floodwall'),
    ('shockoe-2004', 'shockoe', 'gaston-b:2004', None, "Shockoe Bottom: Gaston's rain, August 30, 2004"),
    ('shockoe-2020', 'shockoe', '2020:2020', None, 'Shockoe Bottom: November 2020, against the floodwall'),
    ('shockoe-1771', 'shockoe', '1771:1788', None, 'The flood of 1771, an estimate, on the town of about 1788'),
    ('manchester-1972-height', 'manchester', 'agnes-today:2026', 'agnes-today-nowall:2026', "Manchester: the 1972 flood's height, with today's wall and without it"),
    ('manchester-1996-2020', 'manchester', '1996:2026', '2020:2026', "Manchester: Fran's height (1996) and the November 2020 height against today's wall"),
]

CHANGED = [
    ('Gaston pin 5 and its caption line', '"Main Street Station, dry"', '"Main Street Station, which escaped damage"', 'The Washington Post (S28) says the depot "escaped damage"; no source says it stayed dry (gaston-water.md, section 1).'),
    ('Gaston pins', 'numbered 1 to 5', 'lettered A to E', 'On the sheet the numbers read as the numbered boxes; pin 1 sat on box 1\'s frame.'),
    ('Gaston pin 1', '"17th Street Market, where the water met"', '"17th Street Market, where most water converged"', 'The Post says most water converged on 17th and Main; the market was swamped (gaston-timeline.md, section 4).'),
    ('Box 2 note (Main Street Station)', '"The station of 1901 and its long shed, standing in the water."', 'Camille\'s mapped extent and Gaston\'s report', 'No research file gives the station\'s date; the note now says what HA-410 and the Post support.'),
    ('Box 3 note (17th and Dock)', '"Where the Bottom meets the river; the wall\'s Dock Street opening today."', 'the buried creek and the 17th Street closure', 'Supported as rewritten (S35; floodwall.md closures).'),
    ('Box 5 (Mayo Island)', '"The island under the river, its buildings in it."', 'replaced by the canal at Virginia and Byrd streets', '"Under the river" said "the river" for the water\'s level, which the series never does; the box was also sparse (two buildings).'),
    ('Box 6 note (18th and Cary)', '"wet in every flood here"', '"in the water in every flood drawn here before the wall"', 'Behind the wall (1996, 2020) the box is dry in this drawing (counts.json rc1).'),
    ('Box 7 note (East Franklin)', '"Rows of shops and houses from 1842 to 1913, most of them still standing."', 'the 1980 survey\'s dates for 1703 to 1721', 'The 1842 to 1913 dates are for the Franklin Street face, 1703 to 1721 (step 44); "most still standing" was not checked.'),
    ('Manchester box 3 (tank farm)', '"Storage tanks"', '"Fuel storage tanks (as OSM tags them)"', 'Said with its source.'),
    ('Manchester box 4 (on the wall)', '"water on the river side, dry ground behind"', 'the gravity U-wall, 43 ft (City FAQ)', 'Now a sourced fact rather than a description of the drawing.'),
    ('Manchester box 5 (the plant)', '"whether the plant is inside it is not in our data"', 'adds that the 1986 authorization included the wastewater plant', 'WRDA 1986 sec. 401(a); the levee\'s line is still not in the data, so where the plant lies is still not known here.'),
    ('1771 method line', '"An estimate from diaries: the town of about 1788, buildings as recorded and traced."', '"...the town of 1788 as the downtown history draws it: few of its buildings are known."', 'The 1788 scene draws the 1737 plan, the buildings standing today dated before 1788 and a few curated features (history/richmond-downtown.json); nothing of 1788 is traced, and six buildings stand in the frame.'),
    # rc2, after the independent inspection (findings.md, 2026-11-25-06):
    ('rc2 A1, fact 2: Manchester plant with the wall', 'drawn 20 to 22 ft under water with a gauge', 'cross-hatched "not known", no depth, no gauge; acres and buildings counted apart', 'Chris, 12:27; WRDA 1986 sec. 401; the levee is not in our data.'),
    ('rc2 A2: bridge decks', 'always drawn above the water', 'a deck piece below the water is drawn under it, faintly; deck heights said to be estimates in the key', 'Chris, 12:27.'),
    ('rc2 A3, A4, fact 3: Gaston caption', '"B: the range, not a level: water to 25 ft ..., hatched to 31 ft"', '"Solid: water to about 28 ft ..., a middle figure of the reports; hatched to 35 ft: they imply 24 to 35 ft"', 'gaston-water.md section 4; the leaked working name "B:" removed.'),
    ('rc2 fact 3: Gaston pin C', '"about 9 ft"', '"6 ft 2 in inside, above a 3 ft step" (the source\'s words)', 'NBC12 (S31).'),
    ('rc2 fact 9: Gaston title', '"Tropical Storm Gaston"', '"the rain of Gaston\'s remnants"', 'Gaston was a tropical depression over Richmond while the rain fell (gaston-timeline.md, section 1).'),
    ('rc2 fact 3: Gaston credit', 'no WTVR', 'WTVR added', 'S33.'),
    ('rc2 fact 4: Mayo Bridge levels (1972, 1985, 1996)', '"about 36.8 / 31.0 / 24.0 ft at the Mayo Bridge"', '"perhaps 1 ft higher at the Mayo Bridge (assumed from 1969)"', 'levels.json: the Locks plus 1.3 ft assumed from 1969, UNCONFIRMED; no longer credited to the crest record.'),
    ('rc2 fact 7: 1771', '"about 38.0 ft ..., ±3 ft, the May 1771 Great Fresh"', 'where 38 ft is measured, accounts from 30 to 45 ft, ±3 ft our judgment; "Great Fresh" dropped', 'floods.md, "Disagreements"; OFR 70-51 does not use the name.'),
    ('rc2 A11: counts', '"1 of the 6 buildings shown stand in it"', '"buildings in the water: 1 of the 6 shown"', 'Grammar, every plate.'),
    ('rc2 fact 10: 2004 and 2020 method lines', '2004 without "left out"; 2020 "left out: 0 ..."', '2004 restored; 2020 dropped', ''),
    ('rc2 fact 10: depths', 'the key said 2 m lidar, how-its-made 5 m grid', 'both say: water drawn on the 5 m grid; gauge and box figures from the 2 m lidar at their place', 'scene.ts gauges read the elevation model; boxcounts.ts likewise.'),
    ('rc2 A9: box depth figures', 'at the box\'s center, beside gauges with other figures', 'boxes 1 to 3 give the depth at their gauge\'s place, named; others say "at the box\'s center"', ''),
    ('rc2 A13: key', '"The river\'s own channel" for basins and canal too', '"The river, canal and basins at their own level"', ''),
    # rc3, after the recheck (recheck.md, 2026-11-25-07):
    ('rc3 F1: 1996 box 2', '"in 1996 some of the wall\'s gates were shut, Dock Street among them"', '"In January 1996 some gates were shut, Dock Street among them; in Fran, some gates."', 'RVANews names Dock Street for January 1996 only.'),
    ('rc3 F2: Manchester box 4', '"West of the Mayo Bridge"', '"Just west of the Mayo Bridge"', 'City FAQ.'),
    ('rc3 F3: 1771 caption', '"accounts run from 30 to 45 ft ... Hatched: the top of that range."', '"other accounts give 30 ft and 45 ft on unstated bases; ±3 ft is our judgment. Hatched: up to 41 ft."', 'The 30 and 45 ft accounts are on no stated datum; the hatch is drawn to 12.50 m NAVD88 (11.582 + 0.914), 41.0 ft, at the City Locks.'),
    ('rc3: Gaston title', '"the rain of Gaston\'s remnants"', '"the rain of Gaston, then a tropical depression"', 'NHC TCR AL072004, Table 1 (nhc-gaston).'),
    ('rc3: Gaston box 3', '"the water moved, and kept no one level"', '"the water ran through here and did not stand at one level"', 'Plain wording.'),
    ('rc3 N1: Gaston pool', 'drawn on the river side of the wall too', 'held on the city side of the wall and its openings', 'spill-cityside; gaston-open; gaston-river.'),
    ('rc3: not known', 'acres only', 'acres and the buildings on that ground; the key says the edges assume where the levee runs', 'Scene stats floodUnknownBuildings.'),
    ('rc3: 18th and Cary title', '"18th and Cary, between Cary and Dock streets"', '"18th and Cary streets"', 'Plain.'),
    ('rc3 A10: 1936 box (Shockoe Slip)', '"Where the water\'s edge meets the rise to downtown."', 'a 1936 note: the water only touched the edge of the box', 'counts.json rc3: no water in the box in 1936.'),
    ('rc3: Chapel Island box', 'a note about the retention basin, which the box cannot show', 'what the box shows: the island under the water outside the wall', 'counts.json rc3.'),
    # rc3 re-stamp (the owner, 16:09; recheck.md 2026-11-25-08):
    ('rc3 re-stamp: Gaston title', '"Shockoe Bottom: the rain of Gaston, then a tropical depression, August 30, 2004"', '"Shockoe Bottom: Gaston\'s rain, August 30, 2004"; the storm\'s status moved to the rain panel\'s caption', 'The owner asked for the shorter title; NHC TCR Table 1 for the status.'),
    ('rc3 re-stamp R1: rain panel event', '"4:30 flooding under way"', '"about 4:30, flooding reported"', 'NCEI Storm Events times are labeled EST and may be an hour later in local time; the lawsuit is an allegation.'),
    ('rc3 re-stamp R2: 3:58 warning', 'credited to the weather service', 'Style Weekly quoting the weather service (notes.json only)', 'S20.'),
    ('Plate counts', '"N of the M buildings shown" counted today\'s buildings only', 'every building of the year, traced ones included', 'The d3 captions left traced buildings out of both numbers (scene stats `floodBuildingsInWater`, `buildings`); rc1 counts `floodShown…`.'),
]


def main(plates):
    out = {
        'about': 'Floods series, ' + STAGE + ' (' + VERSION + '): every word the sheets print, with its sources. Written by tools/floods/rc1/notes.py; read by tools/floods/rc1/sheet.py. `checked` says how far a source carries a line. Written with Claude for Chris Busse.',
        'stage': STAGE, 'version': VERSION, 'sources': S,
        'sheets': [], 'captions': {}, 'boxes': {}, 'key': [], 'credits': {}, 'byline': BYLINE, 'changed': [],
    }
    for sid, area, plate, second, title in SHEETS:
        out['sheets'].append({'id': sid, 'area': area, 'plate': plate, **({'second': second} if second else {}), 'title': title,
                              'sources': sorted({k for p in [plate, second] if p for k in LEVEL_SOURCES.get(p.split(':')[0], [])})})
    region = {a: json.load(open(os.path.join(ROOT, f'regions/richmond-floods-{a}.json'))) for a in ('shockoe', 'manchester')}
    for a in ('shockoe', 'manchester'):
        for name, f in region[a]['floods'].items():
            year = None
            for sid, area, plate, second, _ in SHEETS:
                for p in (plate, second):
                    if p and area == a and p.split(':')[0] in (name, name.removesuffix('-dry')):
                        year = p.split(':')[1]
            if year is None:
                continue
            info_path = os.path.join(plates, f'richmond-floods-{a}-{year}-flood-{name}.info.json')
            info = json.load(open(info_path)) if os.path.exists(info_path) else {}
            fill = lambda t: re.sub(r'\{(\w+)\}', lambda m: (f"{info[m.group(1)]:,}" if isinstance(info.get(m.group(1)), (int, float)) else m.group(0)), t)
            # Not-known ground with no building on it says only its acres.
            lines = [f.get('caption', '')] + [fill(n).replace(' (0 buildings on it)', '') for n in f.get('notes', [])]
            base = name.removesuffix('-dry')
            out['captions'][f'{a}:{name}:{year}'] = {
                'title': f.get('title'), 'lines': lines, 'sources': LEVEL_SOURCES.get(base, []) + (['counts', 'evidence'] if a == 'shockoe' else ['counts']),
                'checked': 'Level and its range from levels.json; counts from the build (scene stats); "not ascertained" and "left out" from the evidence layer and the stated rules (how-its-made, Floods).',
            }
    for a, boxes in BOXES.items():
        out['boxes'][a] = {k: {'title': t, 'note': n, 'sources': s, 'checked': c} for k, (t, n, s, c) in boxes.items()}
    out['sheetNotes'] = {sid: {k: {'note': n, 'sources': s, 'checked': c} for k, (n, s, c) in notes.items()} for sid, notes in SHEET_NOTES.items()}
    out['key'] = [{'label': l, 'means': m, 'sources': s} for l, m, s in KEY]
    out['credits'] = {a: {'text': t + ' ' + BYLINE, 'sources': (['ofr70-51', 'lidar', 'town1788'] if a == 'shockoe-1771' else ['ap2004', 'post2004', 'nbc12-2022', 'wtvr2024', 'gaston-river', 'lidar', 'osm', 'evidence'] if a == 'shockoe-2004' else ['levels', 'lidar', 'osm'] + (['evidence'] if a == 'shockoe' else []))} for a, t in CREDITS.items()}
    out['rain'] = RAIN
    out['changed'] = [{'what': w, 'was': was, 'now': now, 'why': why} for w, was, now, why in CHANGED]
    p = os.path.join(ROOT, 'drafts/richmond-floods/notes.json')
    json.dump(out, open(p, 'w'), indent=1, ensure_ascii=False)
    open(p, 'a').write('\n')
    print(p, len(out['captions']), 'captions,', sum(len(b) for b in out['boxes'].values()), 'boxes')


if __name__ == '__main__':
    main(*sys.argv[1:])
