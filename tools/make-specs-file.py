"""Build a single, self-contained HTML file that shows ONLY the Premium Specifications part of the deck.

    python tools/make-specs-file.py [--probe]

Output: "Ananta Premium Specifications.html" in the project root. Double-click it: no server, no presenter console,
no solo mode. It opens on "Click to begin", then plays 8 slides with Next / arrow keys:
  Master Plan (hotspot buttons)  ->  Floor Plans (block / floor / flat)  ->
  THE DIFFERENCE IS VISIBLE  ->  Smartness  ->  Grandeur  ->  Entrance  ->  Security  ->  Luxury

How: the deck's own app.js / app.css are copied in memory and patched (the real deck files are not touched):
  * the cue list is filtered to the 6 cues above,
  * the route is forced to the audience screen (no launcher / presenter / solo),
  * the whole-deck image preloader is switched off,
  * the asset helper looks files up in an embedded map (base64 data URIs) before falling back to ./assets/...
Only the files those 6 slides actually request are embedded (found by loading them in Chrome with --probe).
--probe writes assets/_specs-probe.html (non-embedded, served by the deck server) and prints the requested files.
"""
import base64
import json
import mimetypes
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'assets')
CUES = ['liv-explore', 'liv-floorplans', 'val-interior', 'val-smartness', 'val-grandeur', 'val-entrance', 'val-security', 'val-luxury']
NEEDED = os.path.join(ROOT, 'tools', 'specs-assets.json')  # written from a probe run
OUT = os.path.join(ROOT, 'Ananta Premium Specifications.html')


def patch_js(js):
    def rep(old, new):
        nonlocal js
        assert js.count(old) == 1, old[:80]
        js = js.replace(old, new)

    rep('var Wi = (e) => `./assets/${e}`,', 'var Wi = (e) => (window.__EMBED && window.__EMBED[e]) || `./assets/${e}`,')
    rep('var wa = Ca();', 'var wa = window.__SPECS_ONLY ? Ca().filter((c) => window.__SPECS_ONLY.includes(c.id)).sort((a, b) => window.__SPECS_ONLY.indexOf(a.id) - window.__SPECS_ONLY.indexOf(b.id)) : Ca();')
    rep("var HA = () => window.location.hash.replace(/^#\\/?/, ``).split(`?`)[0] || `launcher`;",
        "var HA = () => (window.__SPECS_ONLY ? `audience` : window.location.hash.replace(/^#\\/?/, ``).split(`?`)[0] || `launcher`);")
    rep('    t(Gi.anantaOverview.endStill),\n    [...e]\n', '    t(Gi.anantaOverview.endStill),\n    window.__SPECS_ONLY ? [] : [...e]\n')
    # paths built without the helper
    js = js.replace('t(`./assets/${e}`)', 't(Wi(e))')
    return js


def data_uri(path):
    mt = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    if path.endswith('.woff2'):
        mt = 'font/woff2'
    elif path.endswith('.ogg'):
        mt = 'audio/ogg'
    with open(path, 'rb') as f:
        return f'data:{mt};base64,' + base64.b64encode(f.read()).decode()


def build(probe=False):
    js = patch_js(open(os.path.join(A, 'app.js'), encoding='utf-8').read())
    css = open(os.path.join(A, 'app.css'), encoding='utf-8').read()
    head = f'<script>window.__SPECS_ONLY = {json.dumps(CUES)};</script>'
    if probe:
        open(os.path.join(A, '_specs-probe.js'), 'w', encoding='utf-8').write(js)
        html = (f'<!doctype html><html lang="en"><head><meta charset="UTF-8"><title>probe</title>{head}'
                f'<link rel="stylesheet" href="./assets/app.css"><script type="module" src="./assets/_specs-probe.js"></script>'
                f'</head><body><div id="root"></div></body></html>')
        open(os.path.join(ROOT, '_specs-probe.html'), 'w', encoding='utf-8').write(html)
        return
    files = [f for f in json.load(open(NEEDED)) if not f.endswith(('.js', '.css', '.html'))]
    embed = {f: data_uri(os.path.join(A, f)) for f in files}
    # fonts referenced from the stylesheet: embed the woff2 files
    def font(m):
        name = m.group(1)
        p = os.path.join(A, name)
        return f'url({data_uri(p)})' if name.endswith('.woff2') and os.path.exists(p) else 'url(data:,)'
    css = re.sub(r'url\(\./([^)]+)\)', font, css)
    js = js.replace('</script', '<\\/script')
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="UTF-8" />\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
            '<meta name="theme-color" content="#161D33" />\n'
            '<title>Ananta — Premium Specifications</title>\n'
            f'{head}\n<script>window.__EMBED = {json.dumps(embed)};</script>\n'
            f'<style>\n{css}\n</style>\n</head>\n<body>\n<div id="root"></div>\n'
            f'<script type="module">\n{js}\n</script>\n</body>\n</html>\n')
    open(OUT, 'w', encoding='utf-8').write(html)
    print(f'{OUT}  {os.path.getsize(OUT) / 1e6:.1f} MB  ({len(embed)} embedded files)')


if __name__ == '__main__':
    build(probe='--probe' in sys.argv)
