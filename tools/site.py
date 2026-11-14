"""Assemble the public site: the newest build of every view (by build name), its thumbnail and
link-preview image, then the explorer and share pages. python3 tools/site.py <dest-dir>"""
import glob, json, os, shutil, subprocess, sys
dest = os.path.abspath(sys.argv[1]); os.makedirs(os.path.join(dest, 'builds'), exist_ok=True)
latest = {}
for d in sorted(glob.glob('out/builds/*')):
    m = os.path.join(d, 'meta.json')
    if not os.path.exists(m): continue
    meta = json.load(open(m))
    if not os.path.exists(os.path.join(d, 'thumb.png')): continue
    latest[meta['name']] = d            # ids sort by time, so the last one wins
keep = set(os.path.basename(d) for d in latest.values())
for old in os.listdir(os.path.join(dest, 'builds')):
    if old not in keep: shutil.move(os.path.join(dest, 'builds', old), os.path.join(dest, '..', '_site_trash_' + old))
size = 0
for name, d in latest.items():
    t = os.path.join(dest, 'builds', os.path.basename(d))
    if not os.path.exists(t): shutil.copytree(d, t)
    size += sum(os.path.getsize(os.path.join(t, f)) for f in os.listdir(t))
subprocess.run(['node', 'bin/isoscape.js', 'explorer', '--out', dest], check=True)
open(os.path.join(dest, '.nojekyll'), 'w').close()
print(len(latest), 'views,', round(size / 1e6), 'MB in builds')
