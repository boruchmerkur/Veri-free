#!/usr/bin/env python3
"""Update already-published store ratings in place.

merge_ratings.py only ADDS chips, so once a score is published it never moves.
Store scores drift — nine of 125 shifted in five days — and a published number
that is quietly wrong is worse than no number on a site that sells accuracy.
"""
import json

REPO = r"C:\Users\BoruchMerkur\Projects\Veri-free\listings.json"
live = json.load(open("ratings.json", encoding="utf-8"))
d = json.load(open(REPO, encoding="utf-8"))


def human(n):
    if not n:
        return None
    if n >= 1_000_000:
        v = n / 1_000_000
        return f"{v:.0f}M" if v >= 10 else f"{v:.1f}M"
    if n >= 1_000:
        v = n / 1_000
        return f"{v:.0f}K" if v >= 10 else f"{v:.1f}K"
    return str(n)


changed = []
for l in d["listings"]:
    rows = live.get(l["name"])
    if not rows:
        continue
    for r in l.get("external_ratings", []):
        if r["source"] not in ("App Store", "Google Play"):
            continue
        cur = next((x for x in rows if x["source"] == r["source"]), None)
        if not cur:
            continue
        if cur["score"] != r["score"]:
            changed.append(f'{l["name"]} {r["source"]}: {r["score"]} -> {cur["score"]}')
            r["score"] = cur["score"]
        c = human(cur.get("count"))
        if c:
            r["count"] = c

with open(REPO, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(d, ensure_ascii=False, indent=2))
print(f"scores updated: {len(changed)}")
for c in changed:
    print("  " + c)
