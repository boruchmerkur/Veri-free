#!/usr/bin/env python3
"""Check every listing's outbound URL. Dead and moved links are the quietest
kind of rot on a site that tells people where to go.

Reports only what needs a human: failures, and redirects that leave the
original domain (a redirect within a domain is usually just marketing).
"""
import concurrent.futures as cf
import json
import urllib.error
import urllib.request
from urllib.parse import urlparse

REPO = r"C:\Users\BoruchMerkur\Projects\Veri-free\listings.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def check(item):
    name, url = item
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return name, url, r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return name, url, e.code, url
    except Exception as e:
        return name, url, type(e).__name__, url


d = json.load(open(REPO, encoding="utf-8"))
targets = [(l["name"], l["url"]) for l in d["listings"]]

bad, moved, ok = [], [], 0
with cf.ThreadPoolExecutor(12) as ex:
    for name, url, status, final in ex.map(check, targets):
        host0 = urlparse(url).netloc.replace("www.", "")
        host1 = urlparse(final).netloc.replace("www.", "")
        if status != 200:
            bad.append(f"  {str(status):18} {name[:26]:27} {url}")
        elif host1 and host0 not in host1 and host1 not in host0:
            moved.append(f"  {name[:26]:27} {host0}  ->  {host1}")
        else:
            ok += 1

print(f"OK: {ok}/{len(targets)}\n")
print(f"NON-200 ({len(bad)}):")
print("\n".join(sorted(bad)) or "  none")
print(f"\nREDIRECTS OFF-DOMAIN ({len(moved)}):")
print("\n".join(sorted(moved)) or "  none")
