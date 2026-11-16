#!/usr/bin/env python3
"""Link-preview check: list every page of the explorer site whose preview tags are missing or broken.

    python3 tools/check/previews.py out/                              a local output directory
    python3 tools/check/previews.py https://busse.github.io/isoscape/ the live site
    python3 tools/check/previews.py out/ --site-url https://busse.github.io/isoscape/
    python3 tools/check/previews.py out/ --all      also list the pages that pass, with their image

Link-preview crawlers (Facebook, Threads, LinkedIn, iMessage, Slack, X, Bluesky, Discord) run no
script and never send the URL fragment, so each page must carry, in its own HTML: og:title,
og:description, og:url, og:type, og:site_name, og:image (absolute https, served, a PNG or JPEG
under 1 MB, its og:image:width and og:image:height true to the file and about 1.91:1),
og:image:alt, twitter:card summary_large_image, twitter:image and a canonical link.

Pages checked: index.html, every s/*.html, p/*.html and m/*.html. Against a URL, the list comes
from sitemap.xml (index, p/, m/) and from index.html's own data (the share pages it hands out).
Against a directory, absolute image URLs under the site URL (from the page's og:url, or
--site-url) are looked up as files in it; other images are fetched.

Exit status 1 when any page has a problem. Standard library only.
"""
import argparse, json, os, re, struct, sys, urllib.error, urllib.parse, urllib.request
from html import unescape

UA = 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)'
MAX_BYTES = 1_000_000
ASPECT = 1200 / 630
REQUIRED = ['og:title', 'og:description', 'og:url', 'og:type', 'og:site_name', 'og:image',
            'og:image:width', 'og:image:height', 'og:image:alt', 'twitter:card', 'twitter:image']


def fetch(url, head=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA}, method='HEAD' if head else 'GET')
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, dict((k.lower(), v) for k, v in r.headers.items()), (b'' if head else r.read())


def image_size(buf):
    """(kind, width, height) of a PNG or JPEG, else None."""
    if buf[:8] == b'\x89PNG\r\n\x1a\n' and len(buf) >= 24:
        w, h = struct.unpack('>II', buf[16:24])
        return 'image/png', w, h
    if buf[:2] != b'\xff\xd8':
        return None
    i = 2
    while i + 9 < len(buf):
        if buf[i] != 0xff:
            i += 1
            continue
        m = buf[i + 1]
        if 0xc0 <= m <= 0xcf and m not in (0xc4, 0xc8, 0xcc):
            h, w = struct.unpack('>HH', buf[i + 5:i + 9])
            return 'image/jpeg', w, h
        if m == 0xd8 or 0xd0 <= m <= 0xd7 or m == 0x01:
            i += 2
            continue
        i += 2 + struct.unpack('>H', buf[i + 2:i + 4])[0]
    return None


def head_tags(html):
    """Meta tags (property or name → content, first wins) and the canonical href, from <head>."""
    head = html.split('</head>', 1)[0]
    tags = {}
    for m in re.finditer(r'<meta\s+([^>]*)>', head, re.I):
        attrs = {}
        for k, q, v in re.findall(r'([\w:-]+)\s*=\s*(["\'])(.*?)\2', m.group(1), re.S):
            attrs[k.lower()] = unescape(v)
        key = attrs.get('property') or attrs.get('name')
        if key and 'content' in attrs and key not in tags:
            tags[key] = attrs['content']
    c = re.search(r'<link\s+rel="canonical"\s+href="([^"]*)"', head, re.I)
    if c:
        tags['canonical'] = unescape(c.group(1))
    return tags


class Site:
    def __init__(self, root, site_url):
        self.url_mode = root.startswith('http://') or root.startswith('https://')
        self.root = root if not self.url_mode else (root if root.endswith('/') else root + '/')
        self.site_url = site_url or (self.root if self.url_mode else None)
        self.images = {}

    def pages(self):
        if not self.url_mode:
            out = ['index.html'] if os.path.exists(os.path.join(self.root, 'index.html')) else []
            for sub in ('s', 'p', 'm'):
                d = os.path.join(self.root, sub)
                if os.path.isdir(d):
                    out += sorted(f'{sub}/{f}' for f in os.listdir(d) if f.endswith('.html'))
            return out
        out = ['']
        try:
            _, _, xml = fetch(self.root + 'sitemap.xml')
            for loc in re.findall(r'<loc>([^<]+)</loc>', xml.decode()):
                rel = unescape(loc)[len(self.root):] if unescape(loc).startswith(self.root) else None
                if rel and rel not in out:
                    out.append(rel)
        except (urllib.error.URLError, OSError) as e:
            print(f'sitemap.xml: {e}', file=sys.stderr)
        _, _, index = fetch(self.root)
        out += [s for s in share_pages(index.decode()) if s not in out]
        return out

    def read(self, rel):
        if self.url_mode:
            _, _, body = fetch(self.root + rel)
            return body.decode('utf-8', 'replace')
        with open(os.path.join(self.root, rel), encoding='utf-8') as f:
            return f.read()

    def image(self, url):
        """(bytes, content type or None, error or None) for an image URL."""
        if url in self.images:
            return self.images[url]
        res = None
        if not self.url_mode and self.site_url and url.startswith(self.site_url):
            path = os.path.join(self.root, urllib.parse.unquote(url[len(self.site_url):].split('#')[0].split('?')[0]))
            if os.path.isfile(path):
                with open(path, 'rb') as f:
                    res = (f.read(), None, None)
            else:
                res = (b'', None, f'not in the output: {os.path.relpath(path, self.root)}')
        else:
            try:
                status, headers, body = fetch(url)
                res = (body, headers.get('content-type'), None if status == 200 else f'HTTP {status}')
            except urllib.error.HTTPError as e:
                res = (b'', None, f'HTTP {e.code}')
            except (urllib.error.URLError, OSError) as e:
                res = (b'', None, str(e))
        self.images[url] = res
        return res


def share_pages(index_html):
    """The share pages the explorer hands out, from index.html's embedded data."""
    out = []
    m = re.search(r'<script type="application/json" id="shares">(.*?)</script>', index_html, re.S)
    if m:
        return [f's/{f}' for f in json.loads(m.group(1))]
    b = re.search(r'<script type="application/json" id="builds">(.*?)</script>', index_html, re.S)
    for x in json.loads(b.group(1)) if b else []:
        out.append(f's/{x["id"]}.html')
    p = re.search(r'<script type="application/json" id="pagesData">(.*?)</script>', index_html, re.S)
    for x in json.loads(p.group(1)) if p else []:
        if isinstance(x, dict) and 'slug' in x:
            out.append(f's/page-{x["slug"]}.html')
    return out


def check(site, rel):
    try:
        html = site.read(rel)
    except (urllib.error.URLError, OSError) as e:
        return [f'page not served: {e}'], None
    t = head_tags(html)
    probs = [f'no {k}' for k in REQUIRED if not t.get(k)]
    if t.get('twitter:card') and t['twitter:card'] != 'summary_large_image':
        probs.append(f'twitter:card is {t["twitter:card"]}, not summary_large_image')
    if not t.get('canonical'):
        probs.append('no canonical link')
    for k in ('og:url', 'og:image', 'twitter:image', 'canonical'):
        v = t.get(k)
        if v and not v.startswith('https://'):
            probs.append(f'{k} is not an absolute https URL: {v}')
    img = t.get('og:image')
    if img and t.get('twitter:image') and t['twitter:image'] != img:
        probs.append('twitter:image differs from og:image')
    summary = None
    if img and img.startswith('http'):
        body, ctype, err = site.image(img)
        if err:
            probs.append(f'og:image {err}: {img}')
        else:
            size = image_size(body)
            if size is None:
                probs.append(f'og:image is not a PNG or JPEG: {img}')
            else:
                kind, w, h = size
                summary = f'{w}x{h} {kind.split("/")[1]} {len(body) // 1000} KB'
                if ctype and ctype.split(';')[0].strip() != kind:
                    probs.append(f'og:image served as {ctype}, is {kind}')
                if t.get('og:image:type') and t['og:image:type'] != kind:
                    probs.append(f'og:image:type says {t["og:image:type"]}, is {kind}')
                if t.get('og:image:width') and t.get('og:image:height') and (t['og:image:width'], t['og:image:height']) != (str(w), str(h)):
                    probs.append(f'og:image:width/height say {t["og:image:width"]}x{t["og:image:height"]}, image is {w}x{h}')
                if abs(w / h - ASPECT) / ASPECT > 0.03:
                    probs.append(f'og:image is {w}x{h}, not about 1.91:1')
                if w < 600:
                    probs.append(f'og:image is only {w} px wide')
                if len(body) > MAX_BYTES:
                    probs.append(f'og:image is {len(body) // 1000} KB, over 1 MB')
    return probs, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('site', help='an output directory, or the site URL')
    ap.add_argument('--site-url', help='the public address of the directory (default: from each page\'s og:url)')
    ap.add_argument('--all', action='store_true', help='list the pages that pass too')
    a = ap.parse_args()
    site = Site(a.site, a.site_url)
    pages = site.pages()
    if not site.url_mode and site.site_url is None and pages:
        # The site URL, from index.html's own og:url (its address is the site's).
        u = head_tags(site.read(pages[0])).get('og:url')
        if u and u.startswith('http'):
            site.site_url = u if u.endswith('/') else u.rsplit('/', 1)[0] + '/'
    bad = 0
    for rel in pages:
        probs, summary = check(site, rel)
        name = rel or 'index.html'
        if probs:
            bad += 1
            print(f'{name}')
            for p in probs:
                print(f'  - {p}')
        elif a.all:
            print(f'{name}: ok ({summary})')
    print(f'{len(pages)} pages checked, {bad} with problems')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
