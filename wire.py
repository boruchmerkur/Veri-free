#!/usr/bin/env python3
"""The Quick Buck — collector for the get-rich-fast board.

Writes wire_snapshot.json, which generate.py renders server-side at
/quick-buck/. The live version of this same collection is
netlify/functions/wire.js at /api/wire; keep the two in sync.

WHY THE SOURCE LIST IS NOT THE ONE IN THE HANDOFF
The handoff shipped 25 feeds fetched in the browser through public CORS relays
(rss2json, allorigins, corsproxy). Neither half survives here:

  * This site's CSP is `connect-src 'self'` — the browser cannot call a relay
    at all, so the whole client-side approach is blocked before it starts.
  * Probed server-side on 2026-09-01, 16 of the 25 returned nothing usable.
    13 of them were Reddit, which answers 429 to unauthenticated datacenter
    traffic; sequential requests spaced over a second still only got the first
    one through. Reddit RSS at this scale needs OAuth, which is a bigger build
    than the board is worth.
    Also dead: Side Hustle Nation (serves an HTML challenge page), The Penny
    Hoarder (200 with an empty body), and Shopify's blog.atom and Indie
    Hackers' feed.xml, both of which 404 — the handoff had already flagged
    those two as unverified.

Every source below was fetched and confirmed to return parseable items on
2026-09-01. Re-run `python3 wire.py --probe` to check them again; a feed that
goes dark should be removed rather than left to fail quietly.

THE REALITY CHECK IS A FEED, NOT A PARAGRAPH
The handoff had a static "read this before you read any of that" strip. On
this site that belongs in the same board as the pitches: FTC Consumer and the
CFPB publish the enforcement actions against exactly these schemes. Scored as
its own scheme, "Reality check", so the pitch and the prosecution sit side by
side.
"""
import json
import os
import re
import sys
import concurrent.futures as cf
from datetime import datetime, timezone

from feeds import get, strip_tags, tag, find_image, find_link, find_date

SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wire_snapshot.json")
# 4, not 6: at 6 the two highest-volume blogs took a third of the board.
PER_SOURCE = 4
KEEP = 60

# name, url, fallback scheme when the keywords don't decide
SOURCES = [
    ("NerdWallet",           "https://www.nerdwallet.com/blog/feed/",                       "Side hustles"),
    ("GOBankingRates",       "https://www.gobankingrates.com/feed/",                        "Side hustles"),
    ("Money.com",            "https://money.com/feed/",                                     "Side hustles"),
    ("Smart Passive Income", "https://www.smartpassiveincome.com/feed/",                    "Passive income"),
    ("Millennial Money",     "https://millennialmoney.com/feed/",                           "Passive income"),
    ("Financial Samurai",    "https://www.financialsamurai.com/feed/",                      "Investing"),
    ("Mr. Money Mustache",   "https://www.mrmoneymustache.com/feed/",                       "Investing"),
    ("CNBC Investing",       "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069", "Investing"),
    ("CNBC Finance",         "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "Trading"),
    ("MarketWatch",          "https://feeds.content.dowjones.io/public/rss/mw_topstories",  "Trading"),
    ("Business Insider",     "https://feeds.businessinsider.com/custom/all",                "Trading"),
    ("CoinDesk",             "https://www.coindesk.com/arc/outboundfeeds/rss/",             "Crypto"),
    ("Cointelegraph",        "https://cointelegraph.com/rss",                               "Crypto"),
    ("Decrypt",              "https://decrypt.co/feed",                                     "Crypto"),
    ("The Block",            "https://www.theblock.co/rss.xml",                             "Crypto"),
    ("BiggerPockets",        "https://www.biggerpockets.com/blog/feed",                     "Real estate"),
    ("Entrepreneur",         "https://www.entrepreneur.com/latest.rss",                     "Startups"),
    ("Fast Company",         "https://www.fastcompany.com/latest/rss",                      "Startups"),
    ("Hacker News (Show)",   "https://hnrss.org/show",                                      "Startups"),
    ("FTC Consumer",         "https://consumer.ftc.gov/blog/rss",                           "Reality check"),
    ("CFPB",                 "https://www.consumerfinance.gov/about-us/newsroom/feed/",     "Reality check"),
]

SCHEMES = ["Side hustles", "Passive income", "Investing", "Trading", "Crypto",
           "Real estate", "Ecommerce", "Flipping", "Startups", "Reality check"]

# Straight from the handoff — the classifier was the good part of it. Order
# matters: the first match wins, so the specific schemes are tested before the
# broad ones, and Reality check outranks everything because an enforcement
# story about crypto belongs under enforcement.
KEYWORDS = [
    ("Reality check",  r"\b(ftc|cfpb|sec charges|lawsuit|sued|settlement|refunds?|deceptive|"
                       r"misled|ponzi|pyramid scheme|fraud|scam|investigation|fined?|penalt)"),
    ("Trading",        r"\b(options?|calls?|puts?|yolo|day ?trad|swing trad|margin|leverage|"
                       r"short squeeze|ticker|\$[A-Z]{2,5}\b|earnings|stock pick)"),
    ("Crypto",         r"\b(crypto|bitcoin|btc|eth(ereum)?|solana|memecoin|altcoin|token|defi|"
                       r"nft|staking|airdrop|blockchain)"),
    ("Real estate",    r"\b(real estate|rental|landlord|airbnb|house hack|brrrr|wholesal|"
                       r"flip(ping)? (a )?house|mortgage|cash ?flow propert)"),
    ("Ecommerce",      r"\b(dropship|shopify|amazon fba|etsy|print on demand|ecommerce|"
                       r"e-commerce|online store|tiktok shop)"),
    ("Flipping",       r"\b(flip|resell|thrift|garage sale|ebay|facebook marketplace|"
                       r"arbitrage|sneaker)"),
    ("Passive income", r"\b(passive|dividend|royalt|affiliate|digital product|automat|"
                       r"while you sleep)"),
    ("Side hustles",   r"\b(side hustle|gig|freelanc|extra (cash|money|income)|per hour|"
                       r"weekend|deliver|uber|doordash|survey)"),
    ("Startups",       r"\b(startup|founder|saas|launch|mrr|bootstrapp|indie|business idea|"
                       r"scale|revenue)"),
    ("Investing",      r"\b(invest|index fund|etf|portfolio|net worth|retire|fire\b|compound|"
                       r"savings rate|wealth)"),
]
KEYWORDS = [(c, re.compile(p, re.I)) for c, p in KEYWORDS]

# A CLASSIFIER IS NOT A FILTER
# The handoff's sources were niche hustle feeds where every item was already
# on-topic, so sorting them into schemes was the whole job. These sources are
# mainstream outlets — CNBC, Fast Company, MarketWatch — where the get-rich
# story is maybe one item in ten. Classifying without filtering produced a
# board reading "5 myths about being a genius" and "What to expect at Apple's
# iPhone 18 launch event": correctly sorted, entirely beside the point.
#
# So an item has to earn its place. HOOK is the actual promise this board is
# about — a number, a timeframe, a life change. ENFORCEMENT is the other side
# of the same story. One of those two is required; SCHEME words only add
# weight to something already pitching.
HOOK = [
    (6, r"\b(?:make|made|earn(?:ed|ing)?|turn(?:ed)?|pocket(?:ed)?)\b[^.]{0,24}\$[\d,]+"),
    (6, r"\$[\d,]+(?:k|m)?\s*(?:a|per|/)\s*(?:month|week|day|year|hour)"),
    (6, r"\b(?:six|seven|6|7)[- ]figure"),
    (6, r"\b(?:get rich|getting rich|rich quick|overnight millionaire|financial freedom)"),
    (5, r"\bpassive income\b|\bwhile you sleep\b|\bmoney on autopilot\b"),
    (5, r"\bside (?:hustle|gig)s?\b"),
    (5, r"\bquit (?:my|his|her|their) (?:job|9-5|day job)\b|\bretire (?:early|at \d)"),
    (5, r"\bhow (?:i|he|she|they|we) (?:made|built|turned|earned|got)\b"),
    (4, r"\b(?:millionaire|self[- ]made|net worth of)\b"),
    (4, r"\bin (?:just )?(?:\d+|a few) (?:days?|weeks?|months?)\b"),
    (4, r"\bno (?:experience|money|skills?) (?:needed|required)\b|\banyone can\b"),
    (4, r"\b(?:easy|quick|fast|effortless) (?:money|cash|income|profits?)\b"),
    (4, r"\bbest (?:ways?|side hustles?|apps?) to (?:make|earn)\b"),
]
ENFORCEMENT = [
    (7, r"\b(?:ftc|cfpb|sec)\b[^.]{0,40}\b(?:charge|sue|settle|order|refund|ban|action|alleg)"),
    (7, r"\b(?:ponzi|pyramid scheme|get[- ]rich[- ]quick scheme)\b"),
    (6, r"\b(?:fraud|defraud|scam(?:med|mers?)?)\b"),
    (5, r"\b(?:deceptive|misled|misleading) (?:claims?|advertis|marketing|practice)"),
    (5, r"\b(?:refunds?|restitution) (?:to|for) (?:consumers?|investors?|customers?)"),
    (4, r"\b(?:class[- ]action|fined|penalt(?:y|ies)|indicted|guilty plea)\b"),
]
SCHEME_WEIGHT = 2
THRESHOLD = 6

HOOK = [(w, re.compile(p, re.I)) for w, p in HOOK]
ENFORCEMENT = [(w, re.compile(p, re.I)) for w, p in ENFORCEMENT]


def score(title, summary):
    """-> (score, is_enforcement). Title hits count double; that's the pitch."""
    t, s = title, summary or ""
    total, hooked, enforced = 0, False, False
    for weight, pat in HOOK:
        in_t, in_s = pat.search(t), pat.search(s)
        if in_t or in_s:
            total += weight * (2 if in_t else 1)
            hooked = True
    for weight, pat in ENFORCEMENT:
        in_t, in_s = pat.search(t), pat.search(s)
        if in_t or in_s:
            total += weight * (2 if in_t else 1)
            enforced = True
    if not (hooked or enforced):
        return 0, False
    for _scheme, pat in KEYWORDS:
        if pat.search(f"{t} {s}"):
            total += SCHEME_WEIGHT
    return total, enforced


def classify(text, fallback, enforced):
    # An enforcement story about crypto is enforcement first — that is the
    # whole point of putting the two on one board.
    if enforced:
        return "Reality check"
    for scheme, pat in KEYWORDS:
        if scheme == "Reality check":
            continue
        if pat.search(text):
            return scheme
    return fallback


def parse(name, url, fallback):
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
        sc, enforced = score(title, summary[:400])
        if sc < THRESHOLD:
            continue
        d = find_date(block)
        out.append({
            "title": title,
            "url": find_link(block),
            "source": name,
            "image": find_image(block),
            "summary": summary[:240],
            "date": d.isoformat() if d else None,
            "score": sc,
            "scheme": classify(f"{title} {summary[:200]}", fallback, enforced),
        })
    # No items here means nothing cleared the bar today, which is normal for a
    # single feed and is NOT the same as the feed being dead. Only `--probe`
    # reports on liveness.
    return out, None


def collect():
    items, errors = [], []
    with cf.ThreadPoolExecutor(10) as ex:
        for got, err in ex.map(lambda s: parse(*s), SOURCES):
            items += got
            if err:
                errors.append(err)
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
        "sources": [s[0] for s in SOURCES],
        "errors": errors,
    }


if __name__ == "__main__":
    if "--probe" in sys.argv:
        for name, url, fb in SOURCES:
            try:
                xml = get(url)
                raw = len(re.findall(r"<(?:item|entry)[\s>]", xml))
            except Exception as e:
                print(f'--  DEAD  {name}  <- {type(e).__name__}')
                continue
            kept, _ = parse(name, url, fb)
            print(f'{"OK " if raw else "-- "} {raw:>3} live, {len(kept):>2} on-beat  {name}')
        raise SystemExit
    data = collect()
    if "--dry" in sys.argv:
        for it in data["items"]:
            print(f'{"IMG" if it["image"] else "   "} {it["scheme"][:14]:15} '
                  f'{it["source"][:18]:19} {it["title"][:60]}')
        print(f'\n{len(data["items"])} kept · errors: {data["errors"] or "none"}')
    else:
        with open(SNAPSHOT, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1))
        n_img = sum(1 for i in data["items"] if i["image"])
        print(f'wrote {SNAPSHOT}: {len(data["items"])} items, {n_img} with art'
              f' · errors: {data["errors"] or "none"}')
