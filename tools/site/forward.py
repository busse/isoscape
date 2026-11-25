"""Turn a GitHub Pages copy of the site into forwarding pages for its new address.

  python3 tools/site/forward.py <new-site-dir> <old-site-dir> <new-url>

For every HTML page in <new-site-dir> (the site as built for <new-url>), write the same path in
<old-site-dir> as a small page that sends the visitor to <new-url> + that path, keeping the query
and the #fragment (the explorer's route), so links already shared still land where they pointed.
Each forwarding page keeps the new page's title, description, canonical link and link-preview
tags, so a link shared before the move still shows its card. Pictures and build files in
<old-site-dir> are left alone (shared cards may still name them); HTML pages there that the new
site no longer has are forwarded to the new site's front page."""
import html, os, re, sys
new, old, url = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3].rstrip('/') + '/'
KEEP = re.compile(r'<title>.*?</title>|<meta\s+(?:name|property)="(?:description|og:[^"]*|twitter:[^"]*)"[^>]*>|<link\s+rel="canonical"[^>]*>', re.S | re.I)

def stub(rel, src):
    target = url + ('' if rel == 'index.html' else rel)
    head = '\n'.join(KEEP.findall(src)) if src else f'<title>isoscape</title>\n<link rel="canonical" href="{html.escape(target)}">'
    if 'rel="canonical"' not in head: head += f'\n<link rel="canonical" href="{html.escape(target)}">'
    t = html.escape(target)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
{head}
<meta http-equiv="refresh" content="0; url={t}">
<script>location.replace({target!r} + location.search + location.hash)</script>
</head>
<body style="font:15px/1.5 system-ui,sans-serif;max-width:40rem;margin:10vh auto;padding:0 20px">
<p>The isoscape explorer has moved to <a href="{t}">{html.escape(url)}</a>.</p>
</body>
</html>
'''

made = 0
for root, dirs, files in os.walk(new):
    dirs[:] = [d for d in dirs if d not in ('.git', 'functions', 'builds')]
    for f in files:
        if not f.endswith('.html'): continue
        p = os.path.join(root, f); rel = os.path.relpath(p, new).replace(os.sep, '/')
        dst = os.path.join(old, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'w').write(stub(rel, open(p, encoding='utf-8').read())); made += 1
gone = 0
for root, dirs, files in os.walk(old):
    dirs[:] = [d for d in dirs if d not in ('.git', 'builds')]
    for f in files:
        if not f.endswith('.html'): continue
        rel = os.path.relpath(os.path.join(root, f), old).replace(os.sep, '/')
        if not os.path.exists(os.path.join(new, rel)):
            open(os.path.join(root, f), 'w').write(stub('index.html', '')); gone += 1
for f in ('sitemap.xml',):
    if os.path.exists(os.path.join(old, f)): os.remove(os.path.join(old, f))
print(made, 'pages forwarded,', gone, 'gone pages sent to the front page')
