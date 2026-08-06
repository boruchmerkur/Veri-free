#!/usr/bin/env python3
"""Feed ingest for the /now/ stream.

Pulls a curated set of RSS/Atom feeds, keeps only the items that touch this
site's beat — price changes, free tiers, subscriptions, cancellations, scams,
enforcement — and normalises them into one dated record.

Relevance is the whole point. A raw tech firehose would be mostly chip
launches and rocket photos; the keyword scoring below is what makes this a
Verified Free stream rather than an aggregator. Items also carry the trigger
that matched, so the page can label WHY something is here.

Run standalone to refresh the snapshot:

    PYTHONUTF8=1 python3 feeds.py          # writes feed_snapshot.json
    PYTHONUTF8=1 python3 feeds.py --dry    # print what would be kept
"""
import concurrent.futures as cf
import html as _html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "feed_snapshot.json")
UA = "Mozilla/5.0 (compatible; VerifiedFreeBot/1.0; +https://veri-free.com)"
KEEP = 48          # items retained in the snapshot
PER_SOURCE = 5     # so the highest-volume feed cannot become the whole page
TIMEOUT = 20

YT = "https://www.youtube.com/feeds/videos.xml?channel_id="

# (name, url, kind). Channel ids resolved from each channel page's canonical
# link and confirmed against the feed's own <title> — resolving by handle
# regex returns the wrong channel often enough to matter.
SOURCES = [
    ("Ars Technica",     "https://feeds.arstechnica.com/arstechnica/index",        "article"),
    ("The Verge",        "https://www.theverge.com/rss/index.xml",                 "article"),
    ("TechCrunch",       "https://techcrunch.com/feed/",                           "article"),
    ("FTC",              "https://www.ftc.gov/feeds/press-release.xml",            "enforcement"),
    ("FTC Consumer",     "https://consumer.ftc.gov/blog/rss",                      "enforcement"),
    ("CFPB",             "https://www.consumerfinance.gov/about-us/newsroom/feed/", "enforcement"),
    ("EFF",              "https://www.eff.org/rss/updates.xml",                    "article"),
    ("9to5Google",       "https://9to5google.com/feed/",                           "article"),
    ("Android Police",   "https://www.androidpolice.com/feed/",                    "article"),
    ("XDA",              "https://www.xda-developers.com/feed/",                   "article"),
    ("MakeUseOf",        "https://www.makeuseof.com/feed/",                        "article"),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/",                      "article"),
    ("Hacker News",      "https://hnrss.org/frontpage?points=150",                 "article"),
    ("How-To Geek",     "https://www.howtogeek.com/feed/",                        "article"),
    ("Lifehacker",       "https://lifehacker.com/feed/rss",                        "article"),
    ("Engadget",         "https://www.engadget.com/rss.xml",                       "article"),
    ("Android Authority","https://www.androidauthority.com/feed/",                 "article"),
    ("Tom's Guide",      "https://www.tomsguide.com/feeds/all",                    "article"),
    ("The Register",     "https://www.theregister.com/headlines.atom",             "article"),
    ("PCWorld",          "https://www.pcworld.com/feed",                           "article"),
    ("Louis Rossmann",   YT + "UCl2mFZoRqjw_ELax4Yisf6w",                          "video"),
    ("Ars Technica",     YT + "UCCDU1fsmgvWljcW2aodfJsA",                          "video"),
    ("The Verge",        YT + "UCddiUEpeqJcYeBxX1IVBKvQ",                          "video"),
    ("TechLinked",       YT + "UCeeFfhMcJa1kjtfZAGskOCA",                          "video"),
    ("Techquickie",      YT + "UC0vBXGSyV14uvJ4hECDOl0Q",                          "video"),
    ("ThioJoe",          YT + "UCQSpnDG3YsFNf5-qHocF-WQ",                          "video"),
    ("EFF",              YT + "UCS66aeKQNvJSOOGPjVHDE3Q",                          "video"),
]

# CORE triggers are this site's actual beat: what something costs and what you
# can still get without paying. An item needs at least one of these — otherwise
# a security-industry feed alone fills the page with enterprise breach news
# that has nothing to do with whether anything is free.
CORE = [
    ("PRICE CHANGE",  6, r"price (?:hike|increase|rise|change|goes? up)|raise[sd]? (?:the |its )?price|now costs|price (?:of|for) \w+ (?:is|goes)|costs? more"),
    ("FREE TIER",     6, r"free (?:tier|plan|version|account|option)|freemium|no longer free|used to be free|once free|drops? the free"),
    ("PAYWALL",       6, r"paywall|behind a (?:pay|sub)|locked behind|premium[- ]only|subscribers[- ]only|now requires? a (?:sub|paid|premium)"),
    ("SUBSCRIPTION",  5, r"subscription|auto[- ]?renew|recurring (?:charge|payment|bill)|monthly fee|per[- ]seat|annual plan"),
    ("SHUTTING DOWN", 6, r"shut(?:ting|s)? down|shutdown|discontinu|sunsett?ing|end of life|killing off|is being retired|pulls? the plug"),
    ("ENFORCEMENT",   6, r"\bFTC\b|\bCFPB\b|class[- ]action|settlement|deceptive (?:practice|advertis|design)|dark pattern|misled consumers|refund(?:s|ed)? customers"),
    ("ADS ADDED",     5, r"add(?:s|ing|ed)? ads|more ads|ad[- ]supported tier|ads to (?:the|its)|ad[- ]free (?:tier|plan|option)|introduc\w+ ads"),
    ("CANCEL IT",     5, r"how to cancel|cancel(?:ling|ling|ed)? your|hard to cancel|refund|money[- ]back|opt out of|delete your account"),
    ("FREE TRIAL",    5, r"free trial|trial period|introductory offer|first (?:month|year) free"),
    ("API PRICING",   5, r"api (?:pricing|access|tier|limits?)|rate limits?|developer (?:tier|plan|access)|charges? for api"),
    ("LICENSE",       4, r"open[- ]?source|license change|relicens|source[- ]available|self[- ]host"),
    ("FREE PICK",     5, r"best free|free (?:app|tool|alternative|service|software)s?|completely free|totally free|without paying|for free|free forever"),
]

# SUPPORTING triggers only add weight to something already on-beat.
SUPPORT = [
    ("PRIVACY",       3, r"data broker|sells? your data|telemetry|privacy policy|harvest\w* (?:your )?data|tracks? you"),
    ("ALTERNATIVE",   3, r"alternative to|instead of paying|best free|switch(?:ing)? (?:from|away)|replace \w+ with"),
    ("SCAM",          3, r"\bscams?\b|fraudulent|too good to be true|fake (?:app|store|offer|giveaway)|bait[- ]and[- ]switch"),
]

TRIGGERS = CORE + SUPPORT
CORE_LABELS = {c[0] for c in CORE}
THRESHOLD = 8      # core hit in the title clears easily; a body-only core needs support


def get(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def unescape(s):
    s = re.sub(r"<!\[CDATA\[([\s\S]*?)\]\]>", r"\1", s or "")
    return _html.unescape(s).strip()


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def tag(block, name):
    m = re.search(rf"<{name}(?:\s[^>]*)?>([\s\S]*?)</{name}>", block, re.I)
    return unescape(m.group(1)) if m else ""


def find_image(block):
    for p in (r'<media:thumbnail[^>]+url="([^"]+)"',
              r'<media:content[^>]+url="([^"]+)"',
              r'<enclosure[^>]+url="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
              r'<img[^>]+src=[\'"]([^\'"]+)'):
        m = re.search(p, block, re.I)
        if m:
            return _html.unescape(m.group(1))
    m = re.search(r'&lt;img[^&]+src=[\'"]?(https?://[^\'"&\s]+)', block, re.I)
    return _html.unescape(m.group(1)) if m else ""


def find_link(block):
    m = re.search(r'<link[^>]*\shref="([^"]+)"', block, re.I)   # atom
    if m:
        return unescape(m.group(1))
    return tag(block, "link")


def find_date(block):
    for name in ("pubDate", "published", "updated", "dc:date"):
        raw = tag(block, name)
        if not raw:
            continue
        try:
            d = parsedate_to_datetime(raw) if "," in raw else datetime.fromisoformat(
                raw.replace("Z", "+00:00"))
            return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
        except Exception:
            continue
    return None


# The agencies' own feeds say "FTC"/"CFPB" in every single item, so the
# ENFORCEMENT trigger fires on all of them — including antitrust filings and
# internal policy notes nobody reading this site cares about. On those feeds
# the item has to name something a consumer actually experiences.
CONSUMER_SUBSTANCE = re.compile(
    r"deceptive|misled|refund|settlement|subscription|negative option|dark pattern|"
    r"billing|charged|hidden fee|junk fee|cancel|auto[- ]?renew|free trial|scam|"
    r"unauthorized|money back|consumers? harmed|returns? money", re.I)


def score(title, summary, kind="article"):
    """-> (score, [labels]). Title matches count double; that's where the news is."""
    t, s = title.lower(), (summary or "").lower()
    if kind == "enforcement" and not CONSUMER_SUBSTANCE.search(f"{title} {summary}"):
        return 0, []
    total, labels = 0, []
    for label, weight, pat in TRIGGERS:
        in_t = re.search(pat, t, re.I)
        in_s = re.search(pat, s, re.I)
        if in_t or in_s:
            total += weight * (2 if in_t else 1)
            labels.append(label)
    return total, labels


def parse(name, url, kind):
    try:
        xml = get(url)
    except Exception as e:
        return [], f"{name}: {type(e).__name__}"
    out = []
    for block in re.findall(r"<(?:item|entry)[\s>][\s\S]*?</(?:item|entry)>", xml):
        title = strip_tags(tag(block, "title"))
        if not title:
            continue
        summary = strip_tags(tag(block, "description") or tag(block, "summary")
                             or tag(block, "content") or tag(block, "media:description"))
        sc, labels = score(title, summary, kind)
        if sc < THRESHOLD or not (set(labels) & CORE_LABELS):
            continue
        d = find_date(block)
        out.append({
            "title": title,
            "url": find_link(block),
            "source": name,
            "kind": kind,
            "image": find_image(block),
            "summary": summary[:600],
            "date": d.isoformat() if d else None,
            "score": sc,
            "tags": labels[:3],
        })
    return out, None


def collect():
    items, errors = [], []
    with cf.ThreadPoolExecutor(10) as ex:
        for got, err in ex.map(lambda s: parse(*s), SOURCES):
            items += got
            if err:
                errors.append(err)
    # Cap per source. Without this the highest-volume feed simply becomes the
    # page — the agencies publish daily and a blog doesn't.
    seen, per_source, uniq = set(), {}, []
    for it in sorted(items, key=lambda x: (x["date"] or "", x["score"]), reverse=True):
        key = re.sub(r"\W+", "", it["title"].lower())[:60]
        if key in seen:
            continue
        n = per_source.get(it["source"], 0)
        if n >= PER_SOURCE:
            continue
        seen.add(key)
        per_source[it["source"]] = n + 1
        uniq.append(it)
    return {
        "updated": datetime.now(timezone.utc).isoformat(),
        "items": uniq[:KEEP],
        "errors": errors,
    }


if __name__ == "__main__":
    data = collect()
    if "--dry" in sys.argv:
        for it in data["items"]:
            img = "IMG" if it["image"] else "   "
            print(f'{img} {it["score"]:3} {it["source"][:16]:17} {",".join(it["tags"])[:28]:29} '
                  f'{it["title"][:64]}')
        print(f'\n{len(data["items"])} kept · errors: {data["errors"] or "none"}')
    else:
        with open(SNAPSHOT, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1))
        n_img = sum(1 for i in data["items"] if i["image"])
        print(f'wrote {SNAPSHOT}: {len(data["items"])} items, {n_img} with art'
              f' · errors: {data["errors"] or "none"}')
