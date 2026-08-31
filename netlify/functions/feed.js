// netlify/functions/feed.js
// Serves the story feed as JSON at /api/feed, live.
//
// WHY THIS EXISTS
// The feed used to be baked into the HTML by feeds.py at build time. That is
// fine while Netlify builds on every push — but builds are stopped on this
// site and deploys are manual and metered, so the "latest" stories froze at
// whatever was last generated on a laptop. A feed that only moves when someone
// runs a script is not a feed.
//
// This is a straight port of feeds.py: same sources, same CORE/SUPPORT
// triggers, same threshold, same per-source cap and de-duplication. Keep the
// two in sync — feeds.py still writes the snapshot that renders server-side on
// first paint, and this function supplies everything after that.
//
// CACHING
// The CDN holds a response for 30 minutes and serves stale for a day while it
// revalidates, so the 28 upstream feeds see at most ~48 sweeps a day no matter
// how much traffic the site gets. No deploy, no build minutes, no credits.

const YT = 'https://www.youtube.com/feeds/videos.xml?channel_id=';

const SOURCES = [
  ['Ars Technica',      'https://feeds.arstechnica.com/arstechnica/index',          'article'],
  ['The Verge',         'https://www.theverge.com/rss/index.xml',                   'article'],
  ['TechCrunch',        'https://techcrunch.com/feed/',                             'article'],
  ['FTC',               'https://www.ftc.gov/feeds/press-release.xml',              'enforcement'],
  ['FTC Consumer',      'https://consumer.ftc.gov/blog/rss',                        'enforcement'],
  ['CFPB',              'https://www.consumerfinance.gov/about-us/newsroom/feed/',  'enforcement'],
  ['EFF',               'https://www.eff.org/rss/updates.xml',                      'article'],
  ['9to5Google',        'https://9to5google.com/feed/',                             'article'],
  ['Android Police',    'https://www.androidpolice.com/feed/',                      'article'],
  ['XDA',               'https://www.xda-developers.com/feed/',                     'article'],
  ['MakeUseOf',         'https://www.makeuseof.com/feed/',                          'article'],
  ['Krebs on Security', 'https://krebsonsecurity.com/feed/',                        'article'],
  ['Hacker News',       'https://hnrss.org/frontpage?points=150',                   'article'],
  ['How-To Geek',       'https://www.howtogeek.com/feed/',                          'article'],
  ['Lifehacker',        'https://lifehacker.com/feed/rss',                          'article'],
  ['Engadget',          'https://www.engadget.com/rss.xml',                         'article'],
  ['Android Authority', 'https://www.androidauthority.com/feed/',                   'article'],
  ["Tom's Guide",       'https://www.tomsguide.com/feeds/all',                      'article'],
  ['The Register',      'https://www.theregister.com/headlines.atom',               'article'],
  ['PCWorld',           'https://www.pcworld.com/feed',                             'article'],
  ['Louis Rossmann',    YT + 'UCl2mFZoRqjw_ELax4Yisf6w',                            'video'],
  ['Ars Technica',      YT + 'UCCDU1fsmgvWljcW2aodfJsA',                            'video'],
  ['The Verge',         YT + 'UCddiUEpeqJcYeBxX1IVBKvQ',                            'video'],
  ['TechLinked',        YT + 'UCeeFfhMcJa1kjtfZAGskOCA',                            'video'],
  ['Techquickie',       YT + 'UC0vBXGSyV14uvJ4hECDOl0Q',                            'video'],
  ['ThioJoe',           YT + 'UCQSpnDG3YsFNf5-qHocF-WQ',                            'video'],
  ['EFF',               YT + 'UCS66aeKQNvJSOOGPjVHDE3Q',                            'video'],
];

// CORE triggers are this site's beat: what something costs, and what you can
// still get without paying. An item needs at least one.
const CORE = [
  ['PRICE CHANGE',  6, /price (?:hike|increase|rise|change|goes? up)|raise[sd]? (?:the |its )?price|now costs|price (?:of|for) \w+ (?:is|goes)|costs? more/i],
  ['FREE TIER',     6, /free (?:tier|plan|version|account|option)|freemium|no longer free|used to be free|once free|drops? the free/i],
  ['PAYWALL',       6, /paywall|behind a (?:pay|sub)|locked behind|premium[- ]only|subscribers[- ]only|now requires? a (?:sub|paid|premium)/i],
  ['SUBSCRIPTION',  5, /subscription|auto[- ]?renew|recurring (?:charge|payment|bill)|monthly fee|per[- ]seat|annual plan/i],
  ['SHUTTING DOWN', 6, /shut(?:ting|s)? down|shutdown|discontinu|sunsett?ing|end of life|killing off|is being retired|pulls? the plug/i],
  ['ENFORCEMENT',   6, /\bFTC\b|\bCFPB\b|class[- ]action|settlement|deceptive (?:practice|advertis|design)|dark pattern|misled consumers|refund(?:s|ed)? customers/i],
  ['ADS ADDED',     5, /add(?:s|ing|ed)? ads|more ads|ad[- ]supported tier|ads to (?:the|its)|ad[- ]free (?:tier|plan|option)|introduc\w+ ads/i],
  ['CANCEL IT',     5, /how to cancel|cancel(?:ling|ed)? your|hard to cancel|refund|money[- ]back|opt out of|delete your account/i],
  ['FREE TRIAL',    5, /free trial|trial period|introductory offer|first (?:month|year) free/i],
  ['API PRICING',   5, /api (?:pricing|access|tier|limits?)|rate limits?|developer (?:tier|plan|access)|charges? for api/i],
  ['LICENSE',       4, /open[- ]?source|license change|relicens|source[- ]available|self[- ]host/i],
  ['FREE PICK',     5, /best free|free (?:app|tool|alternative|service|software)s?|completely free|totally free|without paying|for free|free forever/i],
];

// SUPPORT triggers only add weight to something already on-beat.
const SUPPORT = [
  ['PRIVACY',     3, /data broker|sells? your data|telemetry|privacy policy|harvest\w* (?:your )?data|tracks? you/i],
  ['ALTERNATIVE', 3, /alternative to|instead of paying|best free|switch(?:ing)? (?:from|away)|replace \w+ with/i],
  ['SCAM',        3, /\bscams?\b|fraudulent|too good to be true|fake (?:app|store|offer|giveaway)|bait[- ]and[- ]switch/i],
];

const TRIGGERS = CORE.concat(SUPPORT);
const CORE_LABELS = new Set(CORE.map(c => c[0]));
const THRESHOLD = 8;
const PER_SOURCE = 5;
const KEEP = 48;

// The agencies' feeds say "FTC"/"CFPB" in every item, so ENFORCEMENT fires on
// all of them — antitrust filings and internal policy notes included. On those
// feeds the item has to name something a consumer actually experiences.
const CONSUMER_SUBSTANCE = /deceptive|misled|refund|settlement|subscription|negative option|dark pattern|billing|charged|hidden fee|junk fee|cancel|auto[- ]?renew|free trial|scam|unauthorized|money back|consumers? harmed|returns? money/i;

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", '#39': "'", nbsp: ' ' };

function unescapeHtml(s) {
  return (s || '')
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
    .replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (m, e) => {
      if (e[0] === '#') {
        const n = e[1] === 'x' || e[1] === 'X'
          ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
        return Number.isFinite(n) ? String.fromCodePoint(n) : m;
      }
      const v = ENTITIES[e.toLowerCase()];
      return v === undefined ? m : v;
    })
    .trim();
}

const stripTags = s => unescapeHtml(s).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

function tag(block, name) {
  const m = block.match(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, 'i'));
  return m ? unescapeHtml(m[1]) : '';
}

function findImage(block) {
  const pats = [
    /<media:thumbnail[^>]+url="([^"]+)"/i,
    /<media:content[^>]+url="([^"]+)"/i,
    /<enclosure[^>]+url="([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"/i,
    /<img[^>]+src=['"]([^'"]+)/i,
  ];
  for (const p of pats) {
    const m = block.match(p);
    if (m) return unescapeHtml(m[1]);
  }
  const m = block.match(/&lt;img[^&]+src=['"]?(https?:\/\/[^'"&\s]+)/i);
  return m ? unescapeHtml(m[1]) : '';
}

function findLink(block) {
  const m = block.match(/<link[^>]*\shref="([^"]+)"/i);   // atom
  return m ? unescapeHtml(m[1]) : tag(block, 'link');
}

function findDate(block) {
  for (const name of ['pubDate', 'published', 'updated', 'dc:date']) {
    const raw = tag(block, name);
    if (!raw) continue;
    const d = new Date(raw);
    if (!isNaN(d)) return d.toISOString();
  }
  return null;
}

function score(title, summary, kind) {
  if (kind === 'enforcement' && !CONSUMER_SUBSTANCE.test(`${title} ${summary}`)) return [0, []];
  let total = 0;
  const labels = [];
  for (const [label, weight, pat] of TRIGGERS) {
    const inT = pat.test(title), inS = pat.test(summary || '');
    if (inT || inS) {
      total += weight * (inT ? 2 : 1);
      labels.push(label);
    }
  }
  return [total, labels];
}

async function fetchFeed([name, url, kind]) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 6000);
  let xml;
  try {
    const r = await fetch(url, {
      signal: ctl.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; VerifiedFreeBot/1.0; +https://veri-free.com)',
        'Accept': 'application/rss+xml,application/atom+xml,application/xml,text/xml,*/*',
      },
    });
    if (!r.ok) return { items: [], error: `${name}: HTTP ${r.status}` };
    xml = await r.text();
  } catch (e) {
    return { items: [], error: `${name}: ${e.name || 'fetch failed'}` };
  } finally {
    clearTimeout(timer);
  }

  const items = [];
  const blocks = xml.match(/<(?:item|entry)[\s>][\s\S]*?<\/(?:item|entry)>/g) || [];
  for (const block of blocks) {
    const title = stripTags(tag(block, 'title'));
    if (!title) continue;
    const summary = stripTags(tag(block, 'description') || tag(block, 'summary')
                           || tag(block, 'content') || tag(block, 'media:description'));
    const [sc, labels] = score(title, summary, kind);
    if (sc < THRESHOLD || !labels.some(l => CORE_LABELS.has(l))) continue;
    items.push({
      title, url: findLink(block), source: name, kind,
      image: findImage(block), summary: summary.slice(0, 600),
      date: findDate(block), score: sc, tags: labels.slice(0, 3),
    });
  }
  return { items, error: null };
}

export default async () => {
  const results = await Promise.all(SOURCES.map(fetchFeed));
  const all = [];
  const errors = [];
  for (const r of results) {
    all.push(...r.items);
    if (r.error) errors.push(r.error);
  }

  // Cap per source. Without this the highest-volume feed simply becomes the
  // page — the agencies publish daily and a blog doesn't.
  all.sort((a, b) => (b.date || '').localeCompare(a.date || '') || b.score - a.score);
  const seen = new Set(), perSource = {}, uniq = [];
  for (const it of all) {
    const key = it.title.toLowerCase().replace(/\W+/g, '').slice(0, 60);
    if (seen.has(key)) continue;
    const n = perSource[it.source] || 0;
    if (n >= PER_SOURCE) continue;
    seen.add(key);
    perSource[it.source] = n + 1;
    uniq.push(it);
  }

  const body = {
    updated: new Date().toISOString(),
    items: uniq.slice(0, KEEP),
    errors,
  };

  // If every upstream failed we have nothing worth caching for half an hour —
  // let the page keep its baked snapshot and retry sooner.
  const ok = body.items.length > 0;
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=0, must-revalidate',
      'Netlify-CDN-Cache-Control': ok
        ? 'public, s-maxage=1800, stale-while-revalidate=86400'
        : 'public, s-maxage=120',
    },
  });
};

export const config = { path: '/api/feed' };
