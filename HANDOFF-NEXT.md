# veri-free.com — handoff (updated 2026-07-31)

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

## Consumer-info pass — steps 1 and 2 DONE (2026-07-31, live)
- `sentiment` 8 → **77 listings**. Shape unchanged: `{"split", "praised",
  "complained", "takeaway"}`.
- `external_ratings` 32 → **79 listings**, +127 chips, and the chip now takes
  an optional `"count"` (`"36M"`, `"122K"`) rendered after the score. The row
  is labelled "Ratings elsewhere" with a not-ours note. Rendered by
  `ratings_row()`.
- **Trustpilot and G2 both 403 automated access** — they cannot be scraped and
  nothing from them was guessed. The new scores came from Apple's public
  `itunes.apple.com/lookup` API and Play store `ratingValue`, title-matched
  against the listing. Existing Trustpilot/G2 entries were left alone. To
  refresh, re-run that fetch; to add Trustpilot/G2 for a new listing, read the
  score by hand.
- **`safety` field + "Is X safe?" section on 59 listings.** Shape:
  `{"verdict" (required), "download", "data", "scams", "account_risk"}` — the
  optional rows render only when present. Rendered by `safety_box()`, sits
  right after The catch, and `safety_faq()` injects it as the **second**
  FAQPage question. Generalises the earn-only `legitimacy` box.
- Caught a real drift while writing Plex's sentiment: since 2025, remote
  playback of your OWN media needs Plex Pass (server owner) or a Remote Watch
  Pass (viewer); Roku enforcement began late 2025, other apps through 2026.
  Re-graded **free forever → squeezed, 80 → 62** and rewrote catch/short/worth.

## /free-in-real-life/ — the offline extension (2026-08-01)
New page + new top-level `irl` key in listings.json: a list of
`{group, blurb, items[]}`, where each item uses the **same shape as `deals`**
(name, type, status, url, summary, who, how, worth, caveat). Rendered by the
shared `deal_card()` — hoisted out of the deals block, so both pages use it.

**The rule that defines this page: standing programmes only.** Published dates,
public policies, federal entitlements — things verifiable once that stay
verified. NOT weekly circulars, flash sales, sample-of-the-day or sweepstakes:
those churn daily and by zip code, so a "last checked" date on them would be a
lie, and that date is the whole product. Where something genuinely varies by
location (kids-eat-free, library passes) the card says so and explains how to
check locally rather than printing a national list that's wrong half the time.

Second rule, from the birthday-freebie group: **name the programme, not the
prize.** Loyalty programmes last years; the specific reward gets quietly
downgraded. Any page stating exactly what a chain gives you this year is
quoting something it hasn't checked.

NPS fee-free dates are year-specific — the remaining 2026 ones are hardcoded in
the card text and in the page's FAQ schema. **Refresh both each January.**

### Still open from that plan
3. **Reader feedback** ("Was this verdict right?") per listing.
   Netlify Forms (once detection is on) or the Netlify Blobs moderated-review
   pattern already running on the doula site. Publish curated quotes as
   "Reader reports".
4. Sentiment on the remaining 72 listings and safety on the remaining 90 —
   the ones done were picked by prominence and by where the question is real.
   Batch scripts live in the session scratchpad pattern: a `BATCH` dict keyed
   by listing name, applied by a small script that validates names and keys
   before writing. Cheap to repeat.

Also useful next: advice guides (/guides/: how to cancel any trial, how to
spot fake free, student discounts), and /compare/ additions now that the data
supports them (Feedly vs Inoreader, FlexJobs vs Remote OK).

## Facts discipline
Sentiment/safety text must be conservative and verifiable — no invented
review quotes, no specific figures that churn (message caps etc.); describe
structures, not numbers, unless checked. When in doubt, hedge the way the
existing listings do.

Two rules that came out of the 2026-07-31 pass and should hold:
- **Never write a rating you couldn't fetch.** If the source blocks you, use a
  source that doesn't, or write a non-numeric split line. A fabricated
  Trustpilot score would poison the one thing this site sells.
- **Hedge anything whose default is known to move.** The Claude safety row
  tells the reader to open the current privacy settings rather than asserting
  what the training default is, because that default has already changed once.
