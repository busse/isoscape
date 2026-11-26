"""Write the floods series' evidence file: one list of sightings per building, from the scores
(score.py), the look-over (looked-<area>.json, looks.py) and the Sanborn matches (sanborn.py).

    python3 tools/floods/period/evidence.py <out.json> <nr1980.json> <area> <score.json> <looked.json> <sanborn.json> [<area> ...]

The 1980 survey of the 1983 National Register nomination (nr1980.py) adds, for each of today's
buildings it lists by address, a sighting at its dated year and one in 1980, both present. Where
it dates a building before a sighting that called the spot gone (a photograph or a traced map
whose footprint did not match), the survey wins: that call is set to unclear, with a note.

A sighting is {date, call, source, score?, look?}: `call` is present, gone or unclear; `look`
says whether a look at the contact sheet or block panel confirmed the machine's call or changed
it (`changed from gone`), or null where the building was on a sheet but not singled out. The
`today` list holds today's undated buildings (the question runs backward); `traced` the traced
Sanborn buildings whose end was assumed. src/history.ts turns these into lifespans.
"""
import json, sys

IMAGE_DATE = {'1974': 1974, '1999': 1999, '2002': 2002, '2017': 2017, '2021': 2021}
SOURCE = {
    '1974': '1974 USGS orthophoto map, Richmond quadrangle',
    '1999': '1999 City of Richmond orthophotos',
    '2002': '2002 VGIN VBMP orthophotos',
    '2017': '2017 VGIN VBMP orthophotos',
    '2021': '2021 VGIN VBMP orthophotos',
}


def score_of(im, key):
    if key == '1974':
        a = im['alone']
        return None if not a.get('measurable') else {'dark': a['dark'], 'contrast': a['contrast']}
    s = im.get('same_as_next')
    return None if s is None else {'sameAsNext': s}


def main(out, nr_path, *args):
    nr = json.load(open(nr_path))
    overruled = []
    res = {'about': ('Presence calls for the floods series\' period city (tools/floods/period/). Each sighting: the evidence image and its '
                     'date, the call (present, gone, unclear), the machine\'s score, and whether a look at the contact sheets confirmed or '
                     'changed the machine\'s call. Sanborn sightings for today\'s undated buildings: a traced footprint of that edition on '
                     'the same spot (sanborn.py). Read with the images\' registration in `images`.'),
           'images': {}, 'traced': {}, 'today': {}}
    from collections import Counter
    looks = Counter()
    for area, score_path, looked_path, sanborn_path in zip(args[::4], args[1::4], args[2::4], args[3::4]):  # noqa
        sc = json.load(open(score_path))
        looked = json.load(open(looked_path))
        sb = json.load(open(sanborn_path))
        for k, m in sc['images'].items():
            reg = m.get('registration', {})
            res['images'].setdefault(k, {'date': IMAGE_DATE[k], 'title': m['title'], 'url': m['url'], 'license': m['license'], 'resolution': m['resolution'], 'registration': {}})
            res['images'][k]['registration'][area] = {kk: reg.get(kk) for kk in ('method', 'ground_shift_at_center_m', 'control_points', 'used', 'rms_m', 'max_m') if kk in reg}
        # The machine's calls as the sheets proposed them, then the look's.
        import sheets
        for b in sc['buildings']:
            lk = looked.get(b['id'], {})
            prop = sheets.propose(b, lk.get('1974'))
            prop['1974'] = b['images']['1974']['auto']
            seen = []
            if b['kind'] == 'today':
                # A traced footprint on the spot is a sighting; none is not: the 1980 survey dates
                # 27 of 29 buildings it shares with this list before 1950, and most of those had
                # no matching trace (outlines merged, split or a few meters out). So no match is
                # unclear, not gone.
                for s in sb.get(b['id'], []):
                    if s['call'] == 'present':
                        seen.append({'date': s['date'], 'call': 'present', 'source': f"Sanborn {s['date']} (a traced footprint on the spot)"})
                    else:
                        seen.append({'date': s['date'], 'call': 'unclear', 'source': f"Sanborn {s['date']} (no traced footprint matched; not taken as absence)"})
            for k in IMAGE_DATE:
                call = lk.get(k, prop[k])
                look = lk.get('looked', {}).get(k)
                if look is None and k in lk:
                    look = 'confirmed'
                if look is None:
                    look = 'on sheet'
                looks[(k, 'changed' if look.startswith('changed') else look)] += 1
                rec = {'date': IMAGE_DATE[k], 'call': call, 'source': SOURCE[k], 'machine': prop[k], 'look': look}
                s = score_of(b['images'][k], k)
                if s is not None:
                    rec['score'] = s
                seen.append(rec)
            n = nr.get(b['id']) if b['kind'] == 'today' else None
            if n is not None:
                src = f"1983 National Register nomination, 1980 survey: {n['address']}, dated {n['built']}"
                for r in seen:
                    if r['call'] == 'gone' and n['built'] <= r['date'] <= 1980:
                        r['call'] = 'unclear'
                        r['note'] = 'the 1980 survey dates a building here from ' + str(n['built'])
                        overruled.append((b['id'], r['date']))
                seen.append({'date': n['built'], 'call': 'present', 'source': src})
                seen.append({'date': 1980, 'call': 'present', 'source': src})
                seen.sort(key=lambda r: r['date'])
            res['traced' if b['kind'] == 'traced' else 'today'][b['id']] = seen
    json.dump(res, open(out, 'w'), separators=(',', ':'))
    print('the 1980 survey overrules', len(overruled), 'gone calls:', overruled)
    print(len(res['traced']), 'traced,', len(res['today']), 'today;', dict(sorted(looks.items())))


if __name__ == '__main__':
    main(*sys.argv[1:])
