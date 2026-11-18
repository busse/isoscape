"""Carry the uses and stories read off the 1952 sheets (uses1952.csv) into the traced data.

    python3 apply_reads.py uses1952.csv history/sanborn/jackson-ward-1952.geojson \
        history/sanborn/jackson-ward-lost.geojson

uses1952.csv has one row per building read: its id in the traced files, the sheet, what is
printed on it ("D (dwelling)", "F (flat)", "S (store)", "A (auto: private garage)", or a written
use such as "laundry" or "St. Beulah Holiness Church (Colored)"), a plain use for grouping, and
the number of stories where the printed figure could be read. The reading was done with Claude
from contact sheets of every building in the highway's corridor (paved plus 15 m) and every
building within 40 m of Second Street between Broad and Leigh Streets, each tile a crop of the
50% scan with the traced outline over it (November 18, 2026). A figure next to the outline's
corner that belongs to a neighbor can be misread; where none could be read the field is empty
and the building stays at 2 stories, assumed.

For each row, in both files: `printed` and `use` are set (a name or use already read in
named.csv is kept); where stories were read, `storeys` is set to them and `storeysFrom` to
"sheet" (heights are 3.6 m a story in the renderer). A row with use "not a building" (a
correction-table box the tracer took for an outline) marks the edition's record `notBuilding`,
which count.py leaves out, and removes it from the lost layer."""
import json, sys, csv


def main(reads, edition, lost):
    rows = {r['id']: r for r in csv.DictReader(open(reads))}
    seen = set()
    for path in (edition, lost):
        g = json.load(open(path))
        keep = []
        for f in g['features']:
            p = f['properties']
            r = rows.get(p.get('id'))
            if r is None:
                keep.append(f); continue
            seen.add(r['id'])
            if r['use'] == 'not a building':
                if path == edition:
                    p['notBuilding'] = True; keep.append(f)
                continue
            p['printed'] = r['printed']
            if not p.get('use'):
                p['use'] = r['use']
            if r['stories']:
                p['storeys'] = int(r['stories']); p['storeysFrom'] = 'sheet'
            keep.append(f)
        g['features'] = keep
        json.dump(g, open(path, 'w'))
    print(len(rows), 'rows;', len(seen), 'found;', sum(1 for r in rows.values() if r['stories']), 'with stories')


if __name__ == '__main__':
    main(*sys.argv[1:])
