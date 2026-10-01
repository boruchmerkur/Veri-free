#!/usr/bin/env python3
"""Weekly sweep of our own sites for free things Verified Free could list.

    python selfscan.py              # sweep, write selfscan-report.md
    python selfscan.py --full       # list every unlisted domain, not just changes
    python selfscan.py --one <dom>  # sweep a single domain

NEVER EDITS listings.json AND NEVER DEPLOYS. It writes a report and stops.
That is the design, not an omission: a site whose product is checking other
people's free claims cannot have a script quietly adding its owner's own
products to the shelf. Everything below is a suggestion for a person, and the
ordinary research still has to be done by hand before anything gets a verdict.
The rubric does not get a shortcut because the listing is ours.

WHY IT REPORTS CHANGES RATHER THAN RE-DISCOVERING EVERY WEEK
The first run is a backlog: 25 of our 28 domains are not on the shelf. After
somebody has triaged that once, a weekly re-list of the same 25 is noise and
will stop being read by the third week. So the state of each domain is kept in
selfscan-state.json and the report leads with what MOVED — a domain that
appeared, one that stopped looking paid, one that went dark. `--full` prints
the whole backlog again when you want it.

WHAT IT CAN AND CANNOT SEE
It reads server HTML. Several of ours — Sealed, Targum, BG Cutouts — render
entirely in the browser, so their markup is an empty shell and no amount of
reading the copy will reveal the tool inside. Those are flagged "renders in the
browser, look yourself" rather than scored, because a scanner that quietly
drops them is worse than one that admits the gap.

What it CAN judge reliably is the opposite question: whether there is
machinery for taking money. A live /pricing page, a cart, a per-month figure.
That works on server HTML, and for our purposes "no way to pay" plus "a thing
that exists" is most of the answer.

THE DISCLOSURE IS THE ONLY PROMOTION
Anything of ours that gets listed carries the same same-owner line the three
existing ones carry, and nothing else: no feature slot, no extra adjectives,
no placement the rubric would not give a stranger. The disclosure is there to
cost us something, not to advertise.
"""
import argparse
import concurrent.futures as cf
import datetime as _dt
import html as _html
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
NETWORK = os.path.join(HERE, "network.json")
LISTINGS = os.path.join(HERE, "listings.json")
REPORT = os.path.join(HERE, "selfscan-report.md")
STATE = os.path.join(HERE, "selfscan-state.json")

# ASCII only. HTTP headers are latin-1, and an em dash here raises
# UnicodeEncodeError on every single request - which the first run reported as
# 25 unreadable sites rather than as the one broken header it was.
UA = ("Mozilla/5.0 (compatible; VerifiedFreeSelfScan/1.0; "
      "+https://veri-free.com) - our own sites only")
TIMEOUT = 25

DISCLOSURE = ("This site and Verified Free share a publisher. Stamped on the "
              "same rubric as every other listing.")

PROBE = ["", "/tools/", "/free/", "/check/", "/scan/", "/library/", "/app/"]
PAID_PATHS = ["/pricing", "/plans", "/shop", "/store"]

PAYWALL = [
    (5, r"\$\s?\d+(?:\.\d\d)?\s*(?:/|per )?\s*(?:mo\b|month|yr\b|year|seat|user)"),
    (5, r"\bstarting at \$\d|\bfrom \$\d|\bplans start\b"),
    (4, r"\badd to cart\b|\bbuy now\b|\bcheckout\b|\bshop now\b"),
    (4, r"\bupgrade to (?:pro|premium|plus)\b|\bchoose (?:a )?plan\b"),
    (3, r"\bsubscribe\b|\bsubscription\b"),
    (3, r"\bbook (?:a |your )?(?:call|consult|appointment|session)\b"),
    (3, r"\brequest (?:a )?quote\b|\bget (?:a )?quote\b|\bhire (?:us|me)\b"),
]

FREE_CLAIM = [
    r"\bno (?:credit )?card (?:required|needed)\b",
    r"\bno (?:sign[- ]?up|signup|account|registration) (?:required|needed)\b",
    r"\bcompletely free\b|\balways free\b|\bfree forever\b|\bfree to use\b",
    r"\bfree (?:tool|check|scan|report|guide|version)\b",
]


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        raw = r.read(400_000)
        enc = r.headers.get_content_charset() or "utf-8"
        return r.status, raw.decode(enc, "replace"), r.geturl()


def text_of(h):
    h = re.sub(r"<(script|style|noscript)[\s>][\s\S]*?</\1>", " ", h, flags=re.I)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def title_of(h):
    m = re.search(r"<title[^>]*>([\s\S]*?)</title>", h, re.I)
    return re.sub(r"\s+", " ", _html.unescape(m.group(1))).strip() if m else ""


def meta_desc(h):
    m = (re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', h, re.I)
         or re.search(r'<meta[^>]+content="([^"]*)"[^>]+name="description"', h, re.I))
    return _html.unescape(m.group(1)).strip() if m else ""


def probe(domain, label):
    base = f"https://{domain}"
    out = {"domain": domain, "label": label, "title": "", "desc": "",
           "paid": [], "claims": [], "status": "", "spa": False,
           "extra_paths": [], "errors": []}

    for pp in PAID_PATHS:
        try:
            st, _h, _f = fetch(base + pp)
            if st == 200:
                out["paid"].append(pp)
        except Exception:
            pass

    try:
        st, h, _final = fetch(base + "/")
        out["status"] = str(st)
    except urllib.error.HTTPError as e:
        out["status"] = f"HTTP {e.code}"
        out["errors"].append(f"/: HTTP {e.code}")
        return out
    except Exception as e:
        out["status"] = type(e).__name__
        out["errors"].append(f"/: {type(e).__name__}")
        return out

    out["title"] = title_of(h)
    out["desc"] = meta_desc(h)[:200]
    body = text_of(h)
    hay = f"{out['title']} {out['desc']} {body[:8000]}"

    for w, pat in PAYWALL:
        m = re.search(pat, hay, re.I)
        if m:
            out["paid"].append(m.group(0).strip()[:40])
    for pat in FREE_CLAIM:
        m = re.search(pat, hay, re.I)
        if m:
            out["claims"].append(m.group(0).strip()[:40])

    # A shell with almost no text and no links is a client-rendered app. Say so
    # rather than scoring it zero and dropping it.
    links = len(re.findall(r'<a [^>]*href="/[^"]*"', h, re.I))
    out["spa"] = len(body) < 600 and links < 6

    for path in PROBE[1:]:
        try:
            st, _h2, _f2 = fetch(base + path)
            if st == 200:
                out["extra_paths"].append(path)
        except Exception:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--one")
    a = ap.parse_args()

    net = json.load(open(NETWORK, encoding="utf-8"))["sites"]
    if a.one:
        net = [s for s in net if s["domain"] == a.one] or [
            {"domain": a.one, "label": a.one}]

    blob = json.dumps(json.load(open(LISTINGS, encoding="utf-8")), ensure_ascii=False)
    prev = {}
    if os.path.exists(STATE):
        prev = json.load(open(STATE, encoding="utf-8")).get("sites", {})

    with cf.ThreadPoolExecutor(8) as ex:
        results = list(ex.map(lambda s: probe(s["domain"], s["label"]), net))

    now, moved = {}, []
    for r in results:
        bare = r["domain"].replace("www.", "")
        r["listed"] = bare in blob
        key = r["domain"]
        sig = {"listed": r["listed"], "paid": bool(r["paid"]),
               "status": r["status"], "title": r["title"]}
        now[key] = sig
        old = prev.get(key)
        if old is None:
            if prev:
                moved.append((key, "new to the sweep"))
        else:
            if old["listed"] != sig["listed"]:
                moved.append((key, "now listed" if sig["listed"] else "no longer listed"))
            if old["paid"] and not sig["paid"]:
                moved.append((key, "no longer shows a way to pay - worth a look"))
            if not old["paid"] and sig["paid"]:
                moved.append((key, "now shows a way to pay"))
            if old["status"] != sig["status"]:
                moved.append((key, f"status {old['status']} -> {sig['status']}"))
            if old["title"] != sig["title"] and sig["title"]:
                moved.append((key, f"title changed to “{sig['title'][:60]}”"))

    unlisted = [r for r in results if not r["listed"] and not r["errors"]]
    free_looking = [r for r in unlisted if not r["paid"]]
    paid_looking = [r for r in unlisted if r["paid"]]
    broken = [r for r in results if r["errors"]]
    first_run = not prev

    today = _dt.date.today().isoformat()
    L = ["# Ours, and whether Verified Free lists it", "",
         f"Swept {len(net)} of our domains on {today}.", "",
         "Nothing here is listed automatically. Each one still needs the "
         "ordinary check before it earns a verdict. Anything accepted carries "
         "this line and no other promotion:", "", f"> {DISCLOSURE}", ""]

    if first_run:
        L += ["> First run, so everything below is backlog rather than news. "
              "From next week this report leads with what changed.", ""]
    else:
        L += ["## What changed", ""]
        if moved:
            for dom, why in moved:
                L.append(f"- **{dom}** - {why}")
        else:
            L.append("Nothing moved this week.")
        L.append("")

    if first_run or a.full:
        L += ["---", "", f"## Not listed, and no way to pay found ({len(free_looking)})", ""]
        for r in sorted(free_looking, key=lambda r: r["domain"]):
            L.append(f"### {r['label']} - {r['domain']}")
            L.append(f"- {r['title'] or '(no title)'}")
            if r["desc"]:
                L.append(f"- {r['desc']}")
            if r["claims"]:
                L.append(f"- Says: {', '.join(r['claims'])}")
            if r["spa"]:
                L.append("- Renders in the browser, so the markup shows nothing. "
                         "Open it yourself before judging.")
            if r["extra_paths"]:
                L.append(f"- Also live: {', '.join(r['extra_paths'])}")
            L.append("")

        L += [f"## Not listed, but something is for sale ({len(paid_looking)})", "",
              "Not disqualified - plenty of listings are freemium - but the free "
              "part has to be found and described before these mean anything.", ""]
        for r in sorted(paid_looking, key=lambda r: r["domain"]):
            L.append(f"- **{r['domain']}** - {r['title'][:60]} "
                     f"(paid signals: {', '.join(str(p) for p in r['paid'][:3])})")
        L.append("")

    listed = [r for r in results if r["listed"]]
    if listed:
        L += ["## Already listed", "",
              ", ".join(sorted(r["domain"] for r in listed)), ""]
    if broken:
        L += ["## Could not be read", ""]
        for r in broken:
            L.append(f"- {r['domain']} - {'; '.join(r['errors'][:2])}")
        L.append("")

    open(REPORT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    json.dump({"swept": today, "sites": now},
              open(STATE, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)

    if first_run:
        print(f"first run: {len(free_looking)} unlisted with no way to pay, "
              f"{len(paid_looking)} unlisted with something for sale, "
              f"{len(listed)} already listed, {len(broken)} unreadable")
    else:
        print(f"{len(moved)} change(s) this week; {len(free_looking)} unlisted "
              f"with no way to pay. -> {REPORT}")
        for dom, why in moved[:12]:
            print(f"  {dom:26} {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
