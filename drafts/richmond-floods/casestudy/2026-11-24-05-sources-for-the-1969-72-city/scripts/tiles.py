# Fetch a small mosaic of XYZ tiles from an ArcGIS tile service around a lon/lat box.
import sys, math, urllib.request, io
from PIL import Image
url, out, w, s, e, n, z = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7]), int(sys.argv[7])
def xy(lon, lat):
    x = (lon + 180) / 360 * 2**z
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * 2**z
    return x, y
x0, y0 = xy(w, n); x1, y1 = xy(e, s)
tx = range(int(x0), int(x1) + 1); ty = range(int(y0), int(y1) + 1)
im = Image.new('RGB', (256 * len(tx), 256 * len(ty)), 'white')
for i, x in enumerate(tx):
    for j, y in enumerate(ty):
        try:
            data = urllib.request.urlopen(f'{url}/tile/{z}/{y}/{x}', timeout=30).read()
            im.paste(Image.open(io.BytesIO(data)).convert('RGB'), (256 * i, 256 * j))
        except Exception as ex:
            print('miss', x, y, ex)
left = int((x0 - tx[0]) * 256); top = int((y0 - ty[0]) * 256)
im = im.crop((left, top, int((x1 - tx[0]) * 256), int((y1 - ty[0]) * 256)))
im.save(out, optimize=True); print(out, im.size, len(tx) * len(ty), 'tiles')
