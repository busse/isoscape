# Did the floodwall trap Gaston's water in Shockoe Bottom?

Source keys resolve in `sources.md`. All sources read November 23, 2026. Arithmetic marked
"my calculation" is mine, not a source's.

## The answer

**Mostly no, and the popular version mixes up three different kinds of gate.**

1. **The water came from rain on the Shockoe Creek valley, not from the James.** The river was low.
   It peaked at 14,800 cfs at Westham at 9:15 p.m., about a third of the flow at which minor
   flooding begins (42,000 cfs) [S10], [S12]. There was no river flood for the wall to hold back,
   and none came over or through it.
2. **The floodwall did not close.** Its road and rail openings ("closures" or "floodgates") stayed
   open [S22], [S29], [S30]. The DPU director said in 2018 that the wall is closed for river
   forecasts, not for rain falling on the city [S30]. So "the floodgates were shut and held the water
   in" is not supported.
3. **The Bottom flooded because far more water arrived than the drains, buried creek sewers and
   pumps could carry away.** That is the explanation of the NWS [S3 p1], of the city's own engineers
   [S16], [S17], of the then DPU director in 2018 [S30], and of the 2004 news reports [S23], [S24].
4. **A different set of gates is the real controversy.** The 2009 lawsuit by Shockoe businesses
   alleged that a control gate at the end of the city's underground "Shockoe Box" sewer was kept
   closed and had rusted shut, that other gates were opened late, that a pumping station had no
   power, and that the retention basin was already full [S18]. Those are allegations about the
   sewer system, not the floodwall. I found no ruling, settlement or public finding on them.

**In what sense the "trapped" account is partly right.** Shockoe Bottom is a bowl. Its lowest
streets (about 17 to 18 ft above sea level, NAVD88) sit lower than the strip along the river, where
Dock Street, the railroad embankments and the floodwall stand at roughly 20 to 28 ft (my spot
checks of the USGS elevation service [S41], approximate; see `gaston-water.md`). Water that cannot
get into the pipes has nowhere to drain overland until it rises over that strip or out through
gaps in it. So the riverfront line, of which the floodwall is one part, does define the basin the
water filled. One secondary source states plainly that the floodwall kept the combined storm and
sewage water from reaching the river and so trapped it in the Bottom [S21]. No primary source I read
says this, and no source separates the wall's share of that riverfront barrier from the much older
railroad embankments and fill. Whether the wall raised the peak depth at all, and by how much, is
**UNCONFIRMED**. It can be tested with the lidar (see "What would settle it" below).

## Mechanism by mechanism

### 1. How much rain, where, how fast

- Official gauge, Richmond International Airport: **6.68 in** on Aug. 30 [S1 p8], [S2], [S9]. Its
  hourly record [S8]: 1.27 in (1:54-2:54 p.m.), **2.10 in** (2:54-3:54 p.m.), then 0.4 to 0.7 in per
  hour until about 10 p.m. Three-hour maximum 3.95 in; six-hour 5.51 in [S8].
- Unofficial reports: Richmond West End **12.60 in**; Richmond (Math & Science Center) 12.30 in;
  Mechanicsville 10.70; Ashland 10.61; Sandston 8.10; Science Museum 6.56; St. Christopher's
  6.40 [S1 p8, Table 3], [S2]. NHC says two Richmond sites topped 12 inches, most of it in about
  eight hours late on Aug. 30 [S1 p3]. The exact sites of "West End" and "Math & Science Center"
  gauges are not given. UNCONFIRMED.
- Radar: the NWS put the heaviest radar totals, 10 to 12 inches, over the city and western Hanover
  [S2]. Over a sub-basin near Shockoe Bottom the radar showed peaks of 2 to 3, at times over 3,
  inches per hour around 6 p.m. [S3 p5].
- Over the Shockoe watershed itself no gauge stood. The AORC 1 km reanalysis gives 8.3 to 8.7 in at
  three points down the valley, with up to 1.8 in in one hour, 4.1 to 4.8 in in three hours and
  7.6 to 8.1 in in six hours [S14, my extraction]. AORC caught only 4.57 in at Ashland, where the
  gauge read 10.61, so these are likely low.
- Reported but unverified: "14 inches in five hours" on the Shockoe Valley watershed [S28]. No
  source for it is given. UNCONFIRMED.
- How rare (NOAA Atlas 14, downtown Richmond [S13]): six hours, 100-year 5.54 in, 500-year 7.22,
  1,000-year 8.04. Twelve hours, 1,000-year 10.6 in. By AORC's likely-low numbers, the Shockoe
  watershed got roughly a 500- to 1,000-year six-hour rain; the 12.6 in West End report exceeds the
  1,000-year 12-hour depth. At the airport the six-hour total was about a 100-year amount. Details
  in `rainfall-data.md`. The "1,000-year event" attributed to the NWS [S33] and the "2,500-year
  event" quoted from a business leader [S28] are claims, not published analyses I could find.

### 2. The watershed

- **Area**: about 8,000 acres (12.5 sq mi) [S16 abstract], [S40 p42]; "more than 12 square miles
  and 8,000 acres" [S36]; about 14 square miles, citing the DPU [S35]. The difference probably
  reflects sewershed versus surface-watershed boundaries. UNCONFIRMED.
- **Shape**: a long valley from headwaters just north of I-64 near Mechanicsville Turnpike, south
  along I-64 toward downtown, joined by Cannon's Branch, to the James near 17th and Dock streets
  [S35]; tributaries include Bacon's Quarter Branch and Gum Tree Creek [S36]. It falls about 200
  feet from source to river [S36]. The extent runs roughly from Laburnum Avenue south to the James
  and from Scott's Addition east to Church Hill [S35].
- **How much is paved**: no figure found. The city plan says the Bottom's high share of impervious
  surface worsens flooding but gives no number [S40 p44]. UNCONFIRMED; it can be computed from
  NLCD once the boundary is in hand (see `rainfall-data.md`).
- **Where it drains**: into Richmond's combined sewer system (storm and sanitary together), Shockoe
  district, whose main outfall (006) is by far the city's largest [S39 p21, Table 3-1]. The
  combined system serves about 12,000 acres [S39 p20].
- **Not a USGS watershed**: the national Watershed Boundary Dataset does not carry Shockoe Creek as
  its own unit; it lies inside HUC12 020802060101, "Almond Creek-James River," 126.25 km²
  [S42].

### 3. The pipes: the Arch and the Box

- Shockoe Creek was enclosed in the 1920s: a 1923-1928 project costing over $3 million [S36]; the
  lawsuit dates the Shockoe Creek Arch Sewer to 1926-1927 [S18]. The creek's lower course became
  two underground conduits: the **Shockoe Arch**, a pressure conduit, and the **Shockoe Box**, a
  concrete sewer [S21]. One secondary source gives the Box as 17 by 12 ft and a main drain as 17 ft
  high by 29 ft wide [S21]; I could not confirm either from a primary source. UNCONFIRMED.
- What the city's engineers found (abstract of a 2006 paper by Steidel, a DPU official, and
  others [S16]): in a 65-acre downtown sub-basin, ponding happens because (a) flows into the
  Shockoe Box exceed the capacity of the **Dock Street Pumping Station**, swollen by excess flow
  from the Northeast Interceptor and by flow passed **from the Arch into the Box through existing
  gates**; and (b) runoff exceeds what the street inlets can capture, from downtown and from the
  watershed to the east. The study was framed around a 2-year design storm.
- The DPU director in 2009 said the gutter inlets were in the wrong places and "grossly, grossly
  undersized," and that the Arch, carrying water from higher parts of the city, overwhelmed the
  Box [S17].
- Note on the Dock Street Pumping Station: Style Weekly says it pumps rainwater under the floodwall
  [S20]. The floodwall marker lists one north-side pump station of 75,000 gallons per minute
  [S37], which is about 167 cfs (my calculation). That these are the same station is likely but
  UNCONFIRMED.

### 4. Drop inlets and debris

- Undersized and misplaced inlets: the DPU director [S17]; the city's 2006 engineering paper [S16].
- Debris: the lawsuit alleged litter and debris built up in the system and that the city never
  inspected the Box or Arch [S18]; it also alleged a natural detention basin along I-64 had silted
  up [S18]. A plaintiff said the city cleared drains when asked but never fixed the cause [S18].
  These are allegations. I found no inspection record either way. UNCONFIRMED.

### 5. The Shockoe Retention Basin

- Built in the 1980s on Chapel Island, just downstream of the creek's old mouth [S21], [S39 p15, Fig. 2-1].
- Capacity: **35 million gallons**, filling and draining by gravity, per the DPU in 2024 [S39 p36];
  44 million gallons per Style Weekly in 2004 [S20]; 50 million per the lawsuit [S18]. I trust the
  DPU's 35 MG for the basin's current capacity; whether it was different in 2004 is UNCONFIRMED.
- In Gaston: it overflowed [S20]; the lawsuit says it was already full when the storm hit, and that
  the city had time to start draining it [S18]. The DPU director in 2009 said the basin had not
  worked properly for years [S17]; a 10-foot layer of sludge was later found on its floor [S21].
- Scale (my calculation): 8.2 in of rain (the AORC watershed mean, likely low) on 8,000 acres is
  about 5,470 acre-feet, or roughly 1.8 billion gallons. A 35 to 50 MG basin holds 2 to 3 percent of
  that. Even empty, it could not have absorbed more than a small share of Gaston's rain. This does not
  say whether its being full mattered to the timing or depth of the first flooding; that is
  contested and UNCONFIRMED.

### 6. The pumping station

- Lawsuit: the Dock Street Northside pumping station was never turned on because it had no
  electrical service connected [S18].
- Style Weekly (2004): it lost electricity in the storm; the article asks whether that mattered and
  does not answer [S20]. AP: a substation feeding the Bottom was destroyed [S23]. A secondary source
  says it lost power [S21].
- The sources disagree on why it was not running (never connected versus lost power). I trust
  neither over the other. Whether it would have changed the outcome: scale suggests little, since
  75,000 gpm (about 167 cfs) [S37] is small beside the rain falling on the watershed (next point),
  but it was sized for the downtown sub-basin, where it may have mattered locally. UNCONFIRMED.
- Order of magnitude (my calculation, rational method, rough): 1.5 in per hour over 8,000 acres
  is about 12,000 cfs of rain; with half to nine-tenths running off, 6,000 to 11,000 cfs. That is
  comparable to the whole James at Westham that evening (14,800 cfs peak) [S10], and tens of times
  the pump's 167 cfs.

### 7. The outfall gates and the river's level

- The gates at issue in the lawsuit are sewer gates. The suit says the Box ends at a control gate;
  the Corps of Engineers had recommended keeping it open when the river was low; the city kept it
  closed and it had rusted shut; water then surged through the Arch and forced its way into the
  streets [S18]. It also alleges the city waited until after 4:30 p.m., after flooding began, to
  open gates sending water to the basin or the river [S18]. A secondary source repeats that one
  outlet gate was rusted shut [S21]. I found no city statement confirming or denying the rusted
  gate. UNCONFIRMED.
- The river was low. Westham flow was about 1,900 cfs at 2:15 p.m., 14,800 cfs at its 9:15 p.m.
  peak [S10]. Flood stage (12 ft) corresponds to 42,000 cfs [S12]. The tidal river at the floodwall
  has no recorded stage for 2004; the City Locks stage record begins in October 2007 [S11]. So the
  exact water level against the wall that evening is UNCONFIRMED, but nothing suggests it was high.
  The lawsuit's own framing (a gate meant to be open in low river) assumes a low river [S18].

### 8. What the floodwall physically did

- It did not close; openings stayed open [S22], [S29], [S30].
- It was built for the James, not rain [S24], [S26], [S27]; it guards only against river flooding
  [S35].
- It did not hold back the river, because the river did not rise to it [S10], [S12].
- It forms part of the riverfront line that encloses the Bottom (section above). Whether that line
  held ponded water higher than it would have stood without the wall is UNCONFIRMED.
- A side effect that is supported: the wall removed the Bottom from the mapped flood zone, so almost
  no one carried flood insurance [S22], [S33].

### 9. What official reviews concluded

- **NWS** (Billet and Lynch): the city's drainage system was overwhelmed; warnings preceded the
  worst flooding by more than 90 minutes [S3 p1].
- **NHC**: flash flooding from 6 to 12 in of rain in about eight hours [S1 p3].
- **City of Richmond / DPU** (2006 WEFTEC paper, abstract only): Box flows exceed Dock Street pump
  capacity, aggravated by Northeast Interceptor overflow and Arch-to-Box transfer through gates;
  inlets cannot capture the runoff. Recommended: Northeast Interceptor improvements, more inlets near
  low points, and changed Dock Street pump operation [S16]. I could not read the full paper. It is
  the closest thing to an official engineering review that I found.
- **City Auditor, City Council, USACE, VDEM**: I found no review of Gaston by any of these.
  UNCONFIRMED whether one exists.

### 10. The lawsuit

- Filed August 2009 in Richmond Circuit Court, about five years after the flood [S18], [S19].
- Plaintiffs: 18 named businesses and owners per BizSense (including Bottom's Up, River City Diner,
  O'Briensteins, 17.5 Uncommon Cafe, Market Slip Commercial LP, Pine Alley Lofts LP and others)
  [S18]; 19 per AP [S19].
- Sought $25 million compensatory plus $350,000 per plaintiff [S18], [S19]. Counts: willful and
  wanton negligence, gross negligence, ordinary negligence, nuisance and trespass; 18 alleged errors
  [S18].
- Allegations (as reported): closed and rusted Box control gate; gates opened late; unpowered pump
  station; full retention basin; silted I-64 basin despite a duty under a settlement of a 1968 suit by
  Richmond Engineering Company; debris never inspected; city encouraged development without warning
  of flood risk [S18].
- City response then: no comment on pending litigation [S18], [S19].
- **Outcome: UNCONFIRMED.** I searched for a ruling, dismissal, nonsuit or settlement and found
  none. The Virginia circuit court case index would answer this; I did not query it.

### 11. What was fixed, cost, dates, capacity

| What | When | Cost | Source |
|---|---|---|---|
| Nearly 100 gutter inlets relocated and added; Arch disconnected from Box | Phase 1 began Jan. 2007; project due early 2009 | $20 million total program; Phase 1 about a third under budget | [S17] |
| 93 curb drains | completed by Feb. 2008 | $3.7 million | [S18] |
| Drainage improvements | "past three years" to 2009 | $20 million | [S19] |
| Three new sewer gates, 100 curb inlets modified, floodplain buyouts | 2008-2010 | not given | [S43], citing a hazard mitigation plan I could not open (UNCONFIRMED) |
| About 100 sidewalk grates; flap gates letting street water into the canal; outlets to the James improved | by 2018 | about $20 million over a decade | [S30] |
| Retention basin sludge removal | about 2008-2010 | over $12 million | [S21] (citing Style Weekly, 2010; original not fetched) |

- **Capacity before and after**: the DPU director said in 2018 that the system could carry more
  than three times the stormwater it could during Gaston [S30]. No cfs or MGD figures found.
  UNCONFIRMED.
- **The arch-and-box description conflicts**: the 2006 paper describes Arch flow entering the Box
  through gates [S16]; the 2009 account says the Arch was disconnected from the Box so uphill water
  goes straight to treatment [S17]. Where the Arch's flow goes now is UNCONFIRMED.

### 12. Has the fix been tested?

Not by a storm like Gaston. No rain since 2004 has come close over the Shockoe watershed, by AORC:
Irene (Aug. 27, 2011) about 5 in; Sept. 28, 2016 about 4 in; June 21-22, 2018 about 1 to 2 in on the
watershed [S14, my extraction]. The June 2018 case is mixed: the airport took 7.43 in and a
Henrico station in East Highland Park 6.08 in [S54, events 768425, 768465], yet AORC shows much
less on the watershed, and Shockoe Bottom saw only minor street flooding at 18th and Cary [S54,
event 768486]. Smaller floods in the Bottom since 2004: Aug. 15, 2006, street flooding with $20,000
damage [S54, event 5528489]; May 31, 2019, a water rescue at 24th and Cary [S54, event 831583];
July 20, 2024, flooding across Dock Street [S54, event 1206058]. Officials have said a Gaston-size
rain could flood the Bottom again [S29], [S30], [S31].

## What would settle the wall question

1. With the isoscape lidar, find the lowest overland spill path from 17th and Main to the river,
   with and without the floodwall (wall crest and the sill height of each open closure). If the
   spill elevation without the wall is at or above about 27 ft, the wall made no difference to the
   peak. If it is well below, the wall line mattered.
2. Get the full WEFTEC 2006 paper [S16] and the 2022 Greeley and Hansen H&H study of the Shockoe
   floodplain [S40 p42, p46].
3. Get the court file for the 2009 suit.

## Three sentences the series could print

Gaston's flood in Shockoe Bottom came from rain falling on the city, not from the James River,
which stayed far below flood stage that night and never reached the floodwall's open gates. Eight
to twelve inches fell on the Shockoe Creek valley in about eight hours, many times what its buried
creek sewers, street drains and pumps could carry, and the water pooled up to about ten feet deep
in the lowest blocks before it drained. Shockoe businesses later sued the city, alleging that a
rusted sewer gate, an unpowered pumping station and a full retention basin made it worse; we found
no court ruling on those claims.

## Claims the series must NOT make

- That the floodwall's gates (closures) were shut during Gaston. The sources say they were open.
- That the James River flooded, rose against the wall, or backed up into the Bottom.
- That the floodwall caused the flood, or that the Bottom would have stayed dry without it.
- That the wall "trapped" or "dammed" the water, stated as fact. Unsupported until the spill-path
  test is done.
- That a rusted gate, a dead pump station or a full retention basin caused the flood, or added a
  stated number of feet. These are lawsuit allegations with no public finding.
- That the city was negligent, was found liable, settled, or was cleared. The outcome is unknown.
- "10 to 12 feet" of water. No source I read says it. Say "up to about 10 feet," with the single
  13-foot report at Havana '59 attributed.
- "A 1,000-year (or 2,500-year) flood" as fact. Those are quotes. Atlas 14 supports "rain far rarer
  than a 100-year storm" over the watershed, and is about rain, not flood.
- "14 inches in five hours" as fact.
- That all eight (or nine) deaths were in Richmond, or any in Shockoe Bottom.
- $130 million as Richmond's damage. It is the storm's total across three states.
- That Gaston struck Richmond as a hurricane. It was a tropical depression over Virginia, regaining
  tropical-storm strength near Yorktown that evening.
- That it happened on Aug. 29 or Aug. 31. It was the afternoon and evening of Monday, Aug. 30.
- That the post-Gaston work would prevent a repeat. It has not met a comparable rain.
