"""Add the period city's counts to drafts/richmond-floods/counts.json (key `period_city`):
for each plate of the two areas, buildings shown before (d2) and after the evidence layer,
confirmed and unconfirmed counted apart, from the builds' `info` (plates.sh writes them), and
the coverage table by evidence class (coverage.ts output).

    python3 tools/floods/period/counts.py <before-dir> <after-dir> <coverage-shockoe-before> <coverage-shockoe-after> <coverage-manchester-before> <coverage-manchester-after> <choices.json>
"""
import glob, json, os, sys

PATH = 'drafts/richmond-floods/counts.json'


def main(before, after, csb, csa, cmb, cma, choices):
    c = json.load(open(PATH))
    plates = []
    for f in sorted(glob.glob(os.path.join(after, '*.info.json'))):
        name = os.path.basename(f)[:-len('.info.json')]
        a = json.load(open(f)); b = json.load(open(os.path.join(before, os.path.basename(f))))
        shown_b = b.get('buildings', 0) + b.get('traced', 0)
        plates.append({
            'plate': name.replace('richmond-floods-', ''),
            'before': {'shown': shown_b, 'inWater': b.get('floodBuildingsInWater')},
            'after': {'shown': a.get('periodShown'), 'confirmed': a.get('periodConfirmed'), 'unconfirmed': a.get('periodUnconfirmed'),
                      'inWater': a.get('floodBuildingsInWater'), 'todayByEvidence': a.get('buildingsByEvidence', 0), 'tracedEndedByEvidence': a.get('tracedEndEvidence', 0)},
            'gained': {'confirmed': a.get('periodConfirmed', 0) - shown_b, 'unconfirmed': a.get('periodUnconfirmed', 0)},
        })
    c['period_city'] = {
        'about': ('d2, the period city from evidence (tools/floods/period/, history/richmond-floods.json): buildings shown on each plate before and after, '
                  'confirmed and unconfirmed apart. "Shown" counts today\'s buildings and traced ones the scene draws (inside the frame, not on water or track); '
                  '"gained confirmed" is confirmed after less everything shown before (the old "assumed" traced buildings counted as shown before). '
                  'Coverage: buildings by evidence class and area (tools/floods/coverage.ts). Choices: what each bound draws over the whole evidence file, before the scene\'s own leave-outs.'),
        'plates': plates,
        'coverage': {'shockoe': {'before': json.load(open(csb)), 'after': json.load(open(csa))},
                     'manchester': {'before': json.load(open(cmb)), 'after': json.load(open(cma))}},
        'choices': json.load(open(choices)),
    }
    json.dump(c, open(PATH, 'w'), indent=1)
    for p in plates:
        print(p['plate'], p['before']['shown'], '->', p['after']['shown'], f"({p['after']['confirmed']} confirmed, {p['after']['unconfirmed']} unconfirmed)")


if __name__ == '__main__':
    main(*sys.argv[1:])
