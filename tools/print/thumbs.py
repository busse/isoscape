"""thumb.png (360 wide) and social.png (1200x630) for archived builds that lack them, via compose.svg_to_png
(rsvg-convert or cairosvg). python3 tools/print/thumbs.py <seconds> [id-substring]"""
import glob, json, os, re, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as C
from PIL import Image
T0 = time.time(); B = float(sys.argv[1]); sub = sys.argv[2] if len(sys.argv) > 2 else ''
n = 0
for d in sorted(glob.glob('out/builds/*')):
    if sub not in d: continue
    m = os.path.join(d, 'meta.json'); svg = os.path.join(d, 'image.svg')
    if not os.path.exists(m) or not os.path.exists(svg): continue
    meta = json.load(open(m)); files = meta.setdefault('files', {})
    if files.get('thumb') and files.get('social') and os.path.exists(os.path.join(d, 'social.png')): continue
    if time.time() - T0 > B: print('OUT OF TIME'); break
    i = os.path.basename(d)
    with tempfile.TemporaryDirectory() as t:
        src = open(svg, encoding='utf-8').read()
        src = re.sub(r'<g class="caption".*?</g>', '', src, flags=re.S)
        p = os.path.join(t, 'a.svg'); open(p, 'w', encoding='utf-8').write(src)
        big = os.path.join(t, 'big.png'); C.svg_to_png(p, big, 2400, None, C.PAPER)
        im = Image.open(big).convert('RGB')
    im.resize((360, round(im.height * 360 / im.width)), Image.LANCZOS).save(os.path.join(d, 'thumb.png'))
    # social: 1200x630 centred crop of the middle of the scene
    w = im.width; h = round(w * 630 / 1200)
    if h > im.height: h = im.height; w = round(h * 1200 / 630)
    x0 = (im.width - w) // 2; y0 = max(0, (im.height - h) // 2)
    im.crop((x0, y0, x0 + w, y0 + h)).resize((1200, 630), Image.LANCZOS).save(os.path.join(d, 'social.png'))
    files['thumb'] = f'builds/{i}/thumb.png'; files['social'] = f'builds/{i}/social.png'
    json.dump(meta, open(m, 'w'), indent=1); n += 1
print('rendered', n)
