#!/usr/bin/env python3
"""Fetch verifiable consumer ratings (Apple App Store + Google Play) for veri-free listings.

Apple: official iTunes lookup API (public, no auth).
Play:  ld+json ratingValue embedded in the store page.
Writes ratings.json keyed by listing name. Only confident title matches are kept.
"""
import json, re, sys, time, urllib.parse, urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# listing name -> (apple track id or None, play package id or None, expected title fragment)
APPS = {
    "Canva":                  (897446215,  "com.canva.editor",                     "canva"),
    "Notion":                 (1232780281, "notion.id",                            "notion"),
    "Zoom":                   (546505307,  "us.zoom.videomeetings",                "zoom"),
    "Slack":                  (618783545,  "com.Slack",                            "slack"),
    "Dropbox":                (327630330,  "com.dropbox.android",                  "dropbox"),
    "Proton VPN":             (1437005085, "ch.protonvpn.android",                 "proton"),
    "Hola VPN":               (None,       "org.hola",                             "hola"),
    "Wix":                    (665694627,  "com.wix.android",                      "wix"),
    "ChatGPT":                (6448311069, "com.openai.chatgpt",                   "chatgpt"),
    "Claude":                 (6473753684, "com.anthropic.claude",                 "claude"),
    "Google Gemini":          (6477489729, "com.google.android.apps.bard",         "gemini"),
    "Perplexity":             (1668000334, "ai.perplexity.app.android",            "perplexity"),
    "Khan Academy":           (469863705,  "org.khanacademy.android",              "khan"),
    "Duolingo":               (570060128,  "com.duolingo",                         "duolingo"),
    "Coursera":               (736535961,  "org.coursera.android",                 "coursera"),
    "edX":                    (945480667,  "org.edx.mobile",                       "edx"),
    "Skillshare":             (881301397,  "com.skillshare.Skillshare",            "skillshare"),
    "LinkedIn Learning":      (1084377179, "com.linkedin.android.learning",        "learning"),
    "YouTube":                (544007664,  "com.google.android.youtube",           "youtube"),
    "Tubi":                   (886445756,  "com.tubitv",                           "tubi"),
    "Pluto TV":               (751712884,  "tv.pluto.android",                     "pluto"),
    "Spotify":                (324684580,  "com.spotify.music",                    "spotify"),
    "Crunchyroll":            (329913454,  "com.crunchyroll.crunchyroid",          "crunchyroll"),
    "Kanopy":                 (1094410043, "com.kanopy",                           "kanopy"),
    "Hoopla":                 (580643740,  "com.hoopladigital.android",            "hoopla"),
    "Amazon Prime Video":     (545519333,  "com.amazon.avod.thirdpartyclient",     "prime video"),
    "Libby":                  (1076402606, "com.overdrive.mobile.android.libby",   "libby"),
    "Sefaria":                (1163273965, "org.sefaria.sefaria",                  "sefaria"),
    "Audible":                (379693831,  "com.audible.application",              "audible"),
    "Kindle Unlimited":       (302584613,  "com.amazon.kindle",                    "kindle"),
    "Credit Karma":           (519817714,  "com.creditkarma.mobile",               "credit karma"),
    "Wealthsimple":           (1403963101, "com.wealthsimple",                     "wealthsimple"),
    "Robinhood":              (938003185,  "com.robinhood.android",                "robinhood"),
    "Rocket Money":           (1049724540, "com.truebill",                         "rocket money"),
    "Mailchimp":              (366794783,  "com.mailchimp.mailchimp",              "mailchimp"),
    "Trello":                 (461504587,  "com.trello",                           "trello"),
    "HubSpot CRM":            (1107711722, "com.hubspot.android",                  "hubspot"),
    "Netflix":                (363590051,  "com.netflix.mediaclient",              "netflix"),
    "Disney+":                (1446075923, "com.disney.disneyplus",                "disney"),
    "Peacock":                (1508186374, "com.peacocktv.peacockandroid",         "peacock"),
    "Discord":                (985746746,  "com.discord",                          "discord"),
    "Reddit":                 (1064216828, "com.reddit.frontpage",                 "reddit"),
    "Plex":                   (383457673,  "com.plexapp.android",                  "plex"),
    "LastPass":               (324613447,  "com.lastpass.lpandroid",               "lastpass"),
    "NordVPN":                (905953485,  "com.nordvpn.android",                  "nordvpn"),
    "Bitwarden":              (1137397744, "com.x8bit.bitwarden",                  "bitwarden"),
    "Signal":                 (874139669,  "org.thoughtcrime.securesms",           "signal"),
    "WhatsApp":               (310633997,  "com.whatsapp",                         "whatsapp"),
    "Telegram":               (686449807,  "org.telegram.messenger",               "telegram"),
    "Cash App":               (711923939,  "com.squareup.cash",                    "cash app"),
    "Venmo":                  (351727428,  "com.venmo",                            "venmo"),
    "PayPal":                 (283646709,  "com.paypal.android.p2pmobile",         "paypal"),
    "TurboTax Free Edition":  (1046651404, "com.intuit.turbotax.mobile",           "turbotax"),
    "Udemy":                  (562413829,  "com.udemy.android",                    "udemy"),
    "Shopify":                (861973446,  "com.shopify.mobile",                   "shopify"),
    "Wikipedia":              (324715238,  "org.wikipedia",                        "wikipedia"),
    "Swagbucks":              (703616627,  "com.prodege.swagbucksmobile",          "swagbucks"),
    "Fiverr":                 (1076753179, "com.fiverr.fiverr",                    "fiverr"),
    "Etsy":                   (477128284,  "com.etsy.android",                     "etsy"),
    "Indeed":                 (309735670,  "com.indeed.android.jobsearch",         "indeed"),
    "LinkedIn Jobs":          (288429040,  "com.linkedin.android",                 "linkedin"),
    "Groupon":                (352683833,  "com.groupon",                          "groupon"),
    "Meetup (free events)":   (375990038,  "com.meetup",                           "meetup"),
    "Eventbrite (free events)": (487922291,"com.eventbrite.attendee",              "eventbrite"),
    "Yelp":                   (284910350,  "com.yelp.android",                     "yelp"),
    "Glassdoor":              (487852809,  "com.glassdoor.app",                    "glassdoor"),
    "Feedly":                 (865549308,  "com.devhd.feedly",                     "feedly"),
    "Inoreader":              (892355414,  "com.innologica.inoreader",             "inoreader"),
    "VLC Media Player":       (650377962,  "org.videolan.vlc",                     "vlc"),
    "Microsoft Copilot":      (6472538445, "com.microsoft.copilot",                "copilot"),
    "DeepSeek":               (6737597349, "com.deepseek.chat",                    "deepseek"),
    "Character.AI":           (1530267977, "ai.character.app",                     "character"),
    "Grok":                   (6670324846, "ai.x.grok",                            "grok"),
    "Prolific":               (None,       None,                                   ""),
    "Open Library":           (None,       None,                                   ""),
}


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def apple(track_id, frag):
    try:
        d = json.loads(get(f"https://itunes.apple.com/lookup?id={track_id}&country=us"))
    except Exception as e:
        return None, f"err {e}"
    if not d.get("results"):
        return None, "no result"
    r = d["results"][0]
    title = r.get("trackName", "")
    if frag and frag not in title.lower():
        return None, f"title mismatch: {title}"
    score = r.get("averageUserRating")
    count = r.get("userRatingCount")
    if not score or not count:
        return None, f"no rating ({title})"
    return {"source": "App Store", "score": f"{score:.1f}/5", "count": count,
            "url": f"https://apps.apple.com/us/app/id{track_id}", "title": title}, "ok"


def play(pkg, frag):
    url = f"https://play.google.com/store/apps/details?id={pkg}&hl=en_US&gl=US"
    try:
        html = get(url)
    except Exception as e:
        return None, f"err {e}"
    m = re.search(r'<title[^>]*>([^<]{0,160})</title>', html)
    title = (m.group(1) if m else "").replace(" - Apps on Google Play", "")
    if frag and frag not in title.lower():
        return None, f"title mismatch: {title}"
    m = re.search(r'"ratingValue"\s*:\s*"?([0-9.]+)"?', html)
    c = re.search(r'"ratingCount"\s*:\s*"?([0-9]+)"?', html)
    if not m:
        return None, f"no rating ({title})"
    return {"source": "Google Play", "score": f"{float(m.group(1)):.1f}/5",
            "count": int(c.group(1)) if c else None, "url": url, "title": title}, "ok"


def main():
    out = {}
    for name, (aid, pkg, frag) in APPS.items():
        row = []
        if aid:
            r, msg = apple(aid, frag)
            print(f"  apple {name:24} {msg}" + (f" -> {r['score']} ({r['title']})" if r else ""))
            if r:
                row.append(r)
        if pkg:
            r, msg = play(pkg, frag)
            print(f"  play  {name:24} {msg}" + (f" -> {r['score']} ({r['title']})" if r else ""))
            if r:
                row.append(r)
        if row:
            out[name] = row
        time.sleep(0.4)
    with open("ratings.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nwrote {len(out)} listings with ratings")


if __name__ == "__main__":
    main()
