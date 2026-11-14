"""preview.jpg for archived builds that lack one: the whole view as a JPEG of about 6 megapixels,
which the explorer shows on phones instead of the SVG (a phone browser runs out of memory on
a 10-36 MB SVG). Run it before publishing a site. python3 tools/print/previews.py <seconds> [builds-dir]"""
import glob, json, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as C
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
T0 = time.time(); B = float(sys.argv[1]); root = sys.argv[2] if len(sys.argv) > 2 else 'out/builds'
PIXELS = 6e6
n = 0
for d in sorted(glob.glob(os.path.join(root, '*'))):
    m = os.path.join(d, 'meta.json'); svg = os.path.join(d, 'image.svg'); out = os.path.join(d, 'preview.jpg')
    if not os.path.exists(m) or not os.path.exists(svg): continue
    meta = json.load(open(m)); files = meta.setdefault('files', {})
    if files.get('preview') and os.path.exists(out): continue
    if time.time() - T0 > B: print('OUT OF TIME'); break
    vb = meta['viewBox']
    w = min(6000, round(math.sqrt(PIXELS * vb[2] / vb[3])))
    png = out + '.png'
    C.svg_to_png(svg, png, w, None, C.PAPER)
    Image.open(png).convert('RGB').save(out, quality=80, optimize=True, progressive=True)
    os.remove(png)
    files['preview'] = f"builds/{os.path.basename(d)}/preview.jpg"
    json.dump(meta, open(m, 'w'), indent=1); n += 1
    print(os.path.basename(d), w, round(os.path.getsize(out) / 1e6, 2), 'MB', flush=True)
print('previews made:', n)
