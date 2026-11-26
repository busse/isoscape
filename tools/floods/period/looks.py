"""Read the look-over notes (one file per area and image: lines of `n=P|G|U` with free text,
`#` for a panel's heading) into looked.json: for each building id, the call the look made for
that image, where it differs from or confirms the machine's.

    python3 tools/floods/period/looks.py <index.json> <looked.json> <image> <notes.txt> [<image> <notes.txt> ...]

Later photos are noted `n:XXXX`, one letter for each of 1999, 2002, 2017 and 2021.
A building in a panel or sheet that was looked at and has no line keeps the machine's call:
the look confirmed it (or, where the notes say "left as proposed", did not judge it). The
summary counts calls changed by the look.
"""
import json, re, sys
CALL = {'P': 'present', 'G': 'gone', 'U': 'unclear'}


def main(index_path, out_path, *pairs):
    idx = {r['n']: r for r in json.load(open(index_path))}
    try:
        out = json.load(open(out_path))
    except FileNotFoundError:
        out = {}
    for image, notes in zip(pairs[::2], pairs[1::2]):
        changed = same = 0
        for line in open(notes):
            if line.startswith('#'):
                continue
            # `n:XXXX`: one letter per later photo, 1999 2002 2017 2021.
            for n, cs in re.findall(r'\b(\d+):([PGU]{4})\b', line):
                r = idx[int(n)]
                for im, c in zip(['1999', '2002', '2017', '2021'], cs):
                    call = CALL[c]
                    was = r['proposed'][im]
                    out.setdefault(r['id'], {})[im] = call
                    out[r['id']].setdefault('looked', {})[im] = 'confirmed' if call == was else f'changed from {was}'
                    changed += call != was
                    same += call == was
            for n, c in re.findall(r'\b(\d+)=([PGU])\b', line):
                r = idx[int(n)]
                call = CALL[c]
                was = r['proposed'][image]
                out.setdefault(r['id'], {})[image] = call
                out[r['id']].setdefault('looked', {})[image] = 'confirmed' if call == was else f'changed from {was}'
                changed += call != was
                same += call == was
        print(image, notes, 'lines:', changed + same, 'changed:', changed, 'confirmed by a line:', same)
    json.dump(out, open(out_path, 'w'), indent=0)


if __name__ == '__main__':
    main(*sys.argv[1:])
