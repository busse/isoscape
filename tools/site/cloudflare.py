"""Make a built site ready for Cloudflare Pages: python3 tools/site/cloudflare.py <site-dir> [--also <path>...]

Pages serves no file over 25 MiB. Each such file (the biggest map drawings) must be in the R2
bucket misfit-isoscape-maps under the same path (builds/<id>/image.svg); this script lists them,
writes _routes.json so that only those paths reach the Pages Function that reads R2
(cloudflare/functions/builds/[[path]].js, copied in as functions/), writes _headers and robots.txt (naming the sitemap), and prints
what to upload. It changes nothing else. The caller then commits the site without those files.
Prints the oversized paths, one per line, after "R2:". --also names oversized paths that are not
on disk (a sparse checkout of the site branch)."""
import json, os, shutil, sys
LIMIT = 25 * 1024 * 1024
site = os.path.abspath(sys.argv[1])
also = sys.argv[sys.argv.index('--also') + 1:] if '--also' in sys.argv else []
repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
big = []
for root, dirs, files in os.walk(site):
    dirs[:] = [d for d in dirs if d not in ('.git', 'functions')]
    for f in files:
        p = os.path.join(root, f)
        if os.path.getsize(p) > LIMIT: big.append(os.path.relpath(p, site).replace(os.sep, '/'))
big = sorted(set(big) | set(also))
if any(not b.startswith('builds/') for b in big): raise SystemExit(f'over 25 MiB outside builds/: {big}')
json.dump({'version': 1, 'include': ['/' + b for b in big] or ['/builds/__none__'], 'exclude': []}, open(os.path.join(site, '_routes.json'), 'w'), indent=1)
dst = os.path.join(site, 'functions')
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(os.path.join(repo, 'cloudflare', 'functions'), dst)
open(os.path.join(site, '_headers'), 'w').write('/builds/*\n  Cache-Control: public, max-age=31536000, immutable\n/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n')
# The site owns its host's root on Cloudflare, so it can name its sitemap in robots.txt.
site_url = json.load(open(os.path.join(repo, 'isoscape.config.json'))).get('siteUrl', '').rstrip('/') + '/'
if os.path.exists(os.path.join(site, 'sitemap.xml')) and site_url != '/':
    open(os.path.join(site, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {site_url}sitemap.xml\n')
print('R2:'); [print(b) for b in big]
