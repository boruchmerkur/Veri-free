// netlify/functions/wire.js
// The Quick Buck board, live, at /api/wire.
//
// Port of wire.py — same 21 sources, same HOOK/ENFORCEMENT gate, same
// threshold, same per-source cap and de-duplication. Keep the two in sync:
// wire.py writes the snapshot that renders server-side on first paint, this
// supplies everything after that.
//
// The handoff fetched feeds in the BROWSER through public CORS relays. That
// cannot work here — this site's CSP is `connect-src 'self'`, so the relay
// call never leaves the page — and the relays were the handoff's own stated
// weak point. Server-side with a 30-minute CDN hold removes both problems.

const PER_SOURCE = 4;
const KEEP = 60;
const THRESHOLD = 6;
const SCHEME_WEIGHT = 2;

const SOURCES = [
  ['NerdWallet',           'https://www.nerdwallet.com/blog/feed/',                    'Side hustles'],
  ['GOBankingRates',       'https://www.gobankingrates.com/feed/',                     'Side hustles'],
  ['Money.com',            'https://money.com/feed/',                                  'Side hustles'],
  ['Smart Passive Income', 'https://www.smartpassiveincome.com/feed/',                 'Passive income'],
  ['Millennial Money',     'https://millennialmoney.com/feed/',                        'Passive income'],
  ['Financial Samurai',    'https://www.financialsamurai.com/feed/',                   'Investing'],
  ['Mr. Money Mustache',   'https://www.mrmoneymustache.com/feed/',                    'Investing'],
  ['CNBC Investing',       'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069', 'Investing'],
  ['CNBC Finance',         'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664', 'Trading'],
  ['MarketWatch',          'https://feeds.content.dowjones.io/public/rss/mw_topstories', 'Trading'],
  ['Business Insider',     'https://feeds.businessinsider.com/custom/all',             'Trading'],
  ['CoinDesk',             'https://www.coindesk.com/arc/outboundfeeds/rss/',          'Crypto'],
  ['Cointelegraph',        'https://cointelegraph.com/rss',                            'Crypto'],
  ['Decrypt',              'https://decrypt.co/feed',                                  'Crypto'],
  ['The Block',            'https://www.theblock.co/rss.xml',                          'Crypto'],
  ['BiggerPockets',        'https://www.biggerpockets.com/blog/feed',                  'Real estate'],
  ['Entrepreneur',         'https://www.entrepreneur.com/latest.rss',                  'Startups'],
  ['Fast Company',         'https://www.fastcompany.com/latest/rss',                   'Startups'],
  ['Hacker News (Show)',   'https://hnrss.org/show',                                   'Startups'],
  ['FTC Consumer',         'https://consumer.ftc.gov/blog/rss',                        'Reality check'],
  ['CFPB',                 'https://www.consumerfinance.gov/about-us/newsroom/feed/',  'Reality check'],
];

// Order matters: specific schemes before broad ones.
const KEYWORDS = [
  ['Reality check',  /\b(ftc|cfpb|sec charges|lawsuit|sued|settlement|refunds?|deceptive|misled|ponzi|pyramid scheme|fraud|scam|investigation|fined?|penalt)/i],
  ['Trading',        /\b(options?|calls?|puts?|yolo|day ?trad|swing trad|margin|leverage|short squeeze|ticker|\$[A-Z]{2,5}\b|earnings|stock pick)/i],
  ['Crypto',         /\b(crypto|bitcoin|btc|eth(ereum)?|solana|memecoin|altcoin|token|defi|nft|staking|airdrop|blockchain)/i],
  ['Real estate',    /\b(real estate|rental|landlord|airbnb|house hack|brrrr|wholesal|flip(ping)? (a )?house|mortgage|cash ?flow propert)/i],
  ['Ecommerce',      /\b(dropship|shopify|amazon fba|etsy|print on demand|ecommerce|e-commerce|online store|tiktok shop)/i],
  ['Flipping',       /\b(flip|resell|thrift|garage sale|ebay|facebook marketplace|arbitrage|sneaker)/i],
  ['Passive income', /\b(passive|dividend|royalt|affiliate|digital product|automat|while you sleep)/i],
  ['Side hustles',   /\b(side hustle|gig|freelanc|extra (cash|money|income)|per hour|weekend|deliver|uber|doordash|survey)/i],
  ['Startups',       /\b(startup|founder|saas|launch|mrr|bootstrapp|indie|business idea|scale|revenue)/i],
  ['Investing',      /\b(invest|index fund|etf|portfolio|net worth|retire|fire\b|compound|savings rate|wealth)/i],
];

// HOOK is the promise this board is about — a number, a timeframe, a life
// change. ENFORCEMENT is the other side of the same story. One is required;
// scheme words only add weight to something already pitching. Without this
// gate the mainstream sources fill the board with ordinary business news.
const HOOK = [
  [6, /\b(?:make|made|earn(?:ed|ing)?|turn(?:ed)?|pocket(?:ed)?)\b[^.]{0,24}\$[\d,]+/i],
  [6, /\$[\d,]+(?:k|m)?\s*(?:a|per|\/)\s*(?:month|week|day|year|hour)/i],
  [6, /\b(?:six|seven|6|7)[- ]figure/i],
  [6, /\b(?:get rich|getting rich|rich quick|overnight millionaire|financial freedom)/i],
  [5, /\bpassive income\b|\bwhile you sleep\b|\bmoney on autopilot\b/i],
  [5, /\bside (?:hustle|gig)s?\b/i],
  [5, /\bquit (?:my|his|her|their) (?:job|9-5|day job)\b|\bretire (?:early|at \d)/i],
  [5, /\bhow (?:i|he|she|they|we) (?:made|built|turned|earned|got)\b/i],
  [4, /\b(?:millionaire|self[- ]made|net worth of)\b/i],
  [4, /\bin (?:just )?(?:\d+|a few) (?:days?|weeks?|months?)\b/i],
  [4, /\bno (?:experience|money|skills?) (?:needed|required)\b|\banyone can\b/i],
  [4, /\b(?:easy|quick|fast|effortless) (?:money|cash|income|profits?)\b/i],
  [4, /\bbest (?:ways?|side hustles?|apps?) to (?:make|earn)\b/i],
];
const ENFORCEMENT = [
  [7, /\b(?:ftc|cfpb|sec)\b[^.]{0,40}\b(?:charge|sue|settle|order|refund|ban|action|alleg)/i],
  [7, /\b(?:ponzi|pyramid scheme|get[- ]rich[- ]quick scheme)\b/i],
  [6, /\b(?:fraud|defraud|scam(?:med|mers?)?)\b/i],
  [5, /\b(?:deceptive|misled|misleading) (?:claims?|advertis|marketing|practice)/i],
  [5, /\b(?:refunds?|restitution) (?:to|for) (?:consumers?|investors?|customers?)/i],
  [4, /\b(?:class[- ]action|fined|penalt(?:y|ies)|indicted|guilty plea)\b/i],
];

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
  const m = block.match(/<link[^>]*\shref="([^"]+)"/i);
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

function score(title, summary) {
  const s = summary || '';
  let total = 0, hooked = false, enforced = false;
  for (const [w, pat] of HOOK) {
    const inT = pat.test(title), inS = pat.test(s);
    if (inT || inS) { total += w * (inT ? 2 : 1); hooked = true; }
  }
  for (const [w, pat] of ENFORCEMENT) {
    const inT = pat.test(title), inS = pat.test(s);
    if (inT || inS) { total += w * (inT ? 2 : 1); enforced = true; }
  }
  if (!hooked && !enforced) return [0, false];
  const hay = `${title} ${s}`;
  for (const [, pat] of KEYWORDS) if (pat.test(hay)) total += SCHEME_WEIGHT;
  return [total, enforced];
}

function classify(text, fallback, enforced) {
  if (enforced) return 'Reality check';
  for (const [scheme, pat] of KEYWORDS) {
    if (scheme === 'Reality check') continue;
    if (pat.test(text)) return scheme;
  }
  return fallback;
}

async function fetchFeed([name, url, fallback]) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 7000);
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
    const [sc, enforced] = score(title, summary.slice(0, 400));
    if (sc < THRESHOLD) continue;
    items.push({
      title, url: findLink(block), source: name,
      image: findImage(block), summary: summary.slice(0, 240),
      date: findDate(block), score: sc,
      scheme: classify(`${title} ${summary.slice(0, 200)}`, fallback, enforced),
    });
  }
  // An empty result means nothing cleared the bar today, which is normal for
  // one feed and is NOT the same as the feed being dead — so no error here.
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
    sources: SOURCES.map(s => s[0]),
    errors,
  };
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

export const config = { path: '/api/wire' };
