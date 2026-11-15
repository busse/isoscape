#!/usr/bin/env python3
"""Stamp a design's title block onto its print and canvas files, as its next version.

The art is not redrawn: version N+1 is version N's sold files, unchanged, with the title block
(tools/print/titleblock.py) set into the bottom-right corner of the sheet, or of the canvas face
(the mirrored wrap is left as it was). Because the base files are frozen in version N's record,
the new files can always be made again from them byte for byte (check.py --rebuild does this).

    python3 tools/release/stamp.py <store-dir> <design>... [--version N] [--out DIR] [--budget S]
    python3 tools/release/stamp.py <store-dir> all --budget 160      every design in the catalog

Without --out the new files go beside the old ones, named <stem>-vN_<size>.jpg, and each is
logged in <store>/pipeline/state/stamps.json: its base file and that file's SHA-256, the block's
fields and placement, and the new file's SHA-256 (record.py and check.py read it). A file already
logged there is skipped, so a run cut short by --budget picks up where it stopped. A sheet with no
room for the block raises an error.
"""
import argparse, hashlib, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ISO, 'tools', 'print')); sys.path.insert(0, HERE)
from PIL import Image  # noqa: E402
import titleblock, plates  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
WRAP = 1.5            # inches of mirrored wrap around a canvas face (tools/sets/set.py, compose.py)


def size_u(long_in, dpi):
    """The block's size for a sheet: 1.3 on a 36 in sheet at 300 dpi, a little smaller on
    smaller sheets (by the square root, so it stays legible), in the file's own pixels."""
    return round(1.3 * (long_in / 36) ** 0.5 * dpi / 300, 4)


def versioned(name, n):
    stem, size = re.match(r'(.+?)(_(?:canvas-)?\d+x\d+\.jpg)$', name).groups()
    return re.sub(r'-v\d+$', '', stem) + f'-v{n}' + size


def sheet_geometry(name, im):
    """(face box or None, long side in inches, dpi) from a file's name and pixel size."""
    m = re.search(r'_canvas-(\d+)x(\d+)\.jpg$', name)
    if m:
        w_in, h_in = int(m.group(1)), int(m.group(2))
        dpi = im.width / (w_in + 2 * WRAP)
        wr = round(WRAP * dpi)
        return (wr, wr, im.width - wr, im.height - wr), max(w_in, h_in), dpi
    w_in, h_in = map(int, re.search(r'_(\d+)x(\d+)\.jpg$', name).groups())
    if (im.width > im.height) != (w_in > h_in): w_in, h_in = h_in, w_in
    return None, max(w_in, h_in), im.width / w_in


def files_of(store, d, key):
    pdir = os.path.join(store, d.get('print_dir') or ('print-files/landmarks' if key.startswith('lm-') else 'print-files'))
    out = [os.path.join(pdir, d['print'])]
    if d.get('canvas'):
        rx = re.compile('^' + re.escape(d['canvas']).replace(r'\{w\}', r'\d+').replace(r'\{h\}', r'\d+') + '$')
        for sub in (os.path.join(pdir, 'canvas'), pdir):
            if os.path.isdir(sub):
                out += sorted(os.path.join(sub, f) for f in os.listdir(sub) if rx.match(f))
    return out


def stamp_file(src, dst, info):
    im = Image.open(src)
    face, long_in, dpi = sheet_geometry(os.path.basename(src), im)
    try:
        out, at = titleblock.stamp(im, info, size_u(long_in, dpi), face)
    except ValueError as e:
        raise ValueError(f'{os.path.basename(src)}: {e}') from None
    kw = {k: im.info[k] for k in ('dpi', 'icc_profile') if k in im.info}
    if im.format == 'JPEG':   # the source's own quantization and chroma subsampling
        from PIL import JpegImagePlugin
        kw.update(qtables=im.quantization, subsampling=JpegImagePlugin.get_sampling(im))
    out.save(dst, **kw)
    return at


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('store'); ap.add_argument('designs', nargs='+')
    ap.add_argument('--version', type=int, help='the new version (default: the catalog version + 1)')
    ap.add_argument('--drawn', default='2026'); ap.add_argument('--out'); ap.add_argument('--dry', action='store_true')
    ap.add_argument('--budget', type=float, default=1e9)
    a = ap.parse_args()
    t0 = time.time()
    cat = json.load(open(os.path.join(a.store, 'pipeline', 'catalog.json')))['designs']
    log_p = os.path.join(a.store, 'pipeline', 'state', 'stamps.json')
    log = json.load(open(log_p)) if os.path.exists(log_p) else {}
    report = {}
    for key in (list(cat) if a.designs == ['all'] else a.designs):
        d = cat[key]; n = a.version or d.get('version', 1) + 1
        info = plates.info(key, n, a.drawn)
        report[key] = {'version': n, 'info': info, 'files': {}}
        for src in files_of(a.store, d, key):
            dst = os.path.join(a.out or os.path.dirname(src), versioned(os.path.basename(src), n))
            if a.dry: report[key]['files'][os.path.basename(src)] = os.path.basename(dst); continue
            if not a.out and os.path.basename(dst) in log and os.path.exists(dst): continue
            if time.time() - t0 > a.budget:
                print('OUT OF TIME: run the same command again to continue', flush=True); sys.exit(3)
            at = stamp_file(src, dst, info)
            report[key]['files'][os.path.basename(src)] = {'to': os.path.basename(dst), 'at': at}
            if not a.out:
                log[os.path.basename(dst)] = {'design': key, 'version': n, 'base': os.path.relpath(src, a.store), 'base_sha256': sha(src),
                    'file': os.path.relpath(dst, a.store), 'sha256': sha(dst), 'info': info,
                    'at': {'x': at[0], 'y': at[1], 'w': at[2], 'h': at[3], 'u': at[4], 'where': at[5]},
                    'tools': {f: sha(os.path.join(ISO, f)) for f in ('tools/print/titleblock.py', 'tools/release/stamp.py', 'catalog/plates.json')}}
                json.dump(log, open(log_p, 'w'), indent=1, ensure_ascii=False)
            print(key, os.path.basename(dst), at, flush=True)
    if a.out:
        json.dump(report, open(os.path.join(a.out, 'stamp-report.json'), 'w'), indent=1, ensure_ascii=False)
    return report


if __name__ == '__main__':
    main()
