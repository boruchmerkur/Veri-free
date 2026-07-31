# veri-free.com — handoff (written 2026-07-30)

## Ground rules — read first
- **Working home: `C:\Users\BoruchMerkur\Projects\Veri-free`** (git works here).
  The old copy under OneDrive is RETIRED — its `.git` is a corrupted cloud
  placeholder. Never push from OneDrive.
- Repo `github.com/boruchmerkur/Veri-free`, branch `main`. Netlify auto-deploys
  every push (build runs on Linux). Git identity: `boruchmerkur <boruchmerkur@gmail.com>`.
- Local build on Windows needs UTF-8 mode: `PYTHONUTF8=1 python3 generate.py`
  (writes ./site/). Verify by grepping site/ output, then push and poll the
  live site with curl.
- **Netlify v2 functions** (`export default` + `export const config={path}`)
  are served AT their config.path and NOT at /.netlify/functions/<name>.
  NEVER add a [[redirects]] rule for them — that's what broke /api/lily once.
- CSP lives in `assets/_headers` (copied to site root at build).
  `connect-src 'self' https://dreamsitedesign.com`.
- **Every new listing needs its card line translated**: add lang→name→text to
  `i18n_listings.json` for es/pt/fr/de (falls back to English if missing).
  UI-chrome strings live in `i18n.py`.
- Verdicts must be honest per /methodology/; the publisher's own sites carry a
  same-publisher disclosure (see the Beis Moshiach listing for the wording).

## Current state (all live on veri-free.com)
- 149 listings, 10 categories. Localized homepages + category pages at
  /es/ /pt/ /fr/ /de/ with hreflang; language switcher in nav; browser-language
  suggest banner on the EN homepage.
- Category bar: wrapping counted chips, All chip toggles all⇄none.
- Free site check section on all homepages → POSTs to
  `https://dreamsitedesign.com/api/audit`, shows the `AI Search` + `SEO`
  checks; offers the full report by email → `dreamsitedesign.com/api/lead`
  (source `verifree`). Strings localized via `window.SC_STRINGS` (assets/sitecheck.js).
- /submit/ "Request a verdict" is a real Netlify form (`verify-request`,
  honeypot, AJAX, /submit/thanks/ fallback).
- AI page (/ai-tools/ + 4 langs): 14 listings across modalities + a live
  AI-agent leaderboard sidebar — self-hosted widget `assets/ai-widget.js` +
  function `netlify/functions/ai-leaderboard.js` at `/api/ai-leaderboard`
  (scrapes arena.ai, CDN-cached 6h, snapshot fallback flagged `stale:true`).
  A weekly cloud routine health-checks it (Sundays 12:00 UTC,
  claude.ai/code/routines/trig_015NEeX8Kiy5mf8U9whQzyqo).
- Analytics: lily edge tracker (netlify/ files) → dashboard at
  dreamsitedesign.com/dashboard (password-gated).

## PENDING — user must click (blocks form capture)
Netlify dashboard → veri-free project → **Forms → "Enable form detection"**,
then trigger a redeploy. Until then POSTs to the verify-request form 404.
After enabling: re-test with a POST, and add a form email notification to
hello@veri-free.com. (Everything code-side is already deployed.)

## THE NEXT TASK — consumer-info pass (user approved direction)
Goal: more consumer info, reviews, and advice. Agreed plan, in order:

1. **Populate existing fields on the top ~50 listings** (by traffic/prominence):
   - `sentiment` boxes ("What users actually say") — currently only 8/149 have
     them. Shape: `{"split": "...", "praised": "...", "complained": "...",
     "takeaway": "..."}` — see an existing listing for the voice. These are
     editorial readings of the public review record — patterns, not quotes.
   - `external_ratings` — currently 32/149. Shape:
     `[{"source": "Trustpilot", "score": "4.1", "url": "https://..."}]`.
2. **"Is it safe?" block** on listing pages + FAQPage schema:
   - Search Console shows safety-intent queries (is gimp safe, gimp download
     safe, is openlibrary.org safe). Add an optional `safety` field per listing
     (short honest verdict: download safety, data practices, scam status) and
     render it as its own section with FAQ schema so it can win rich results.
   - Generalizes the existing `legitimacy` box (earn-only today).
3. **Reader feedback** ("Was this verdict right?") per listing — after 1+2.
   Netlify Forms (once detection is on) or the Netlify Blobs moderated-review
   pattern already running on the doula site. Publish curated quotes as
   "Reader reports".

Also useful next: advice guides (/guides/: how to cancel any trial, how to
spot fake free, student discounts), and /compare/ additions now that the data
supports them (Feedly vs Inoreader, FlexJobs vs Remote OK).

## Facts discipline
Sentiment/safety text must be conservative and verifiable — no invented
review quotes, no specific figures that churn (message caps etc.); describe
structures, not numbers, unless checked. When in doubt, hedge the way the
existing listings do.
