#!/usr/bin/env python3
"""
Turn ~140 brand-favicon requests into ONE.

Run this on your own machine (it needs internet access), then rebuild:

    pip install pillow
    python3 selfhost_favicons.py
    python3 generate.py

What it does:
  1. Downloads every brand icon the site references.
  2. Packs them all into a single sprite: assets/brand-sprite.png
  3. Writes assets/brand-index.json (domain -> cell number)

generate.py picks both up automatically and switches from 140 <img> tags
pointing at google.com to 140 <span> tags sharing one same-origin image.
Requests for brand marks: 140 -> 1.

Re-run whenever you add listings with new domains. If it can't run,
nothing breaks — the site falls back to the remote favicon service.
"""
import json, os, re, sys, time
from urllib.parse import urlparse
from urllib.request import urlopen, Request

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required:  pip install pillow")

CELL = 128
TMP = "assets/brand"
SPRITE = "assets/brand-sprite.png"
INDEX = "assets/brand-index.json"

os.makedirs(TMP, exist_ok=True)

data = json.load(open("listings.json"))
urls = {l.get("favicon_url") or l["url"] for l in data["listings"]}
urls |= {d.get("favicon_url") or d["url"] for d in data.get("deals", [])}
domains = sorted({urlparse(u).netloc for u in urls if urlparse(u).netloc})

print(f"{len(domains)} unique brand domains\n")

got, failed = [], []
for dom in domains:
    safe = re.sub(r"[^a-z0-9]+", "-", dom.lower()).strip("-") + ".png"
    path = os.path.join(TMP, safe)
    if not (os.path.exists(path) and os.path.getsize(path) > 100):
        try:
            req = Request(f"https://www.google.com/s2/favicons?domain={dom}&sz={CELL}",
                          headers={"User-Agent": "Mozilla/5.0"})
            blob = urlopen(req, timeout=15).read()
            if len(blob) < 100:
                raise ValueError("placeholder icon")
            open(path, "wb").write(blob)
            print(f"  fetched  {dom}")
            time.sleep(0.12)
        except Exception as e:
            print(f"  FAILED   {dom}  ({e})")
            failed.append(dom)
            continue
    got.append((dom, path))

if not got:
    sys.exit("\nNothing downloaded — leaving the remote favicon service in place.")

sheet = Image.new("RGBA", (CELL * len(got), CELL), (0, 0, 0, 0))
index = {}
for i, (dom, path) in enumerate(got):
    try:
        icon = Image.open(path).convert("RGBA").resize((CELL, CELL), Image.LANCZOS)
    except Exception as e:
        print(f"  skip     {dom}  ({e})")
        continue
    sheet.paste(icon, (i * CELL, 0))
    index[dom] = i

sheet.save(SPRITE, optimize=True)
json.dump(index, open(INDEX, "w"), indent=2)

kb = os.path.getsize(SPRITE) / 1024
print(f"\nsprite:  {SPRITE}  ({len(index)} icons, {kb:.0f} KB)")
print(f"index:   {INDEX}")
if failed:
    print(f"\n{len(failed)} domain(s) failed and keep using the remote service:")
    for d in failed:
        print(f"  {d}")
print("\nNow run:  python3 generate.py")
