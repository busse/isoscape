# 33. Radar against gauges, and the correction (20:19 to 20:50)

- Raw tropical radar was low at the official gauges (airport by a factor of 1.41, Ashland
  2.49, Sandston 1.62) and high at some unofficial reports in the city (Science Museum 0.68).
- **Dead end:** one factor for the whole map (1.43 from the official gauges, as the brief
  allowed) put the watershed at 13.1 in, more than any gauge, and failed the leave-one-out
  test (typical miss x1.53, worse than no correction, x1.49). It is kept in rain.json and the
  report as the rejected method.
- Used: a local correction (inverse-distance-weighted log ratio, L = 5 km, unofficial reports at
  half weight), typical miss x1.44. Factor at the watershed's center 1.12.
- Range for the watershed from every defensible estimate: 8.56 (AORC) to 11.60 in (local
  correction, L = 20 km); Stage IV's 24-hour analysis gives 10.79.
- Rounds: r1 (first), r3 (rejected mean-field replaced), r6 (subtitle cut off at the right),
  r7 (kept; says plainly the right panel is in-sample).
