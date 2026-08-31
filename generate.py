#!/usr/bin/env python3
"""Verified Free — static site generator.
Reads listings.json, writes the full site into ./site/.
Run: python3 generate.py
"""
import json, re, os, re, shutil, html
from i18n import L10N, EXTRA_LANGS, LANG_NAMES, HTML_LANG

DOMAIN = "https://veri-free.com"
SPRITE_INDEX = {}
if os.path.exists("assets/brand-index.json") and os.path.exists("assets/brand-sprite.png"):
    SPRITE_INDEX = json.load(open("assets/brand-index.json"))

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")

# Translated per-listing card lines ("You get" text), keyed lang -> name -> text.
# Optional: missing file or missing entry falls back to the English line.
GET_L10N = {}
if os.path.exists("i18n_listings.json"):
    GET_L10N = json.load(open("i18n_listings.json", encoding="utf-8"))

CATS = {
    "software-tools": ("Software", "Editors, office suites, VPNs, storage, site builders — the apps everyone claims are free."),
    "ai-tools": ("AI", "Chatbots, image generators, and model hubs — which free tiers are real."),
    "business": ("Business", "The free tools companies dangle as their front door — verified on whether the door is real."),
    "learning": ("Learning", "Courses, certificates, and language apps — where the paywall actually sits."),
    "entertainment": ("Streaming", "Movies, music, and TV — free with ads, free with a library card, or a trial with a fuse."),
    "books-reading": ("Books", "Ebooks and audiobooks — the free libraries and the memberships in disguise."),
    "money-finance": ("Finance", "'Free' financial apps always get paid somehow. Here's how, for each one."),
    "earn": ("Earn", "Legitimate ways to earn money online — verified, with the scams exposed."),
    "reviews": ("Reviews", "The review platforms themselves, rated — whose trust do they actually serve?"),
    "data-apis": ("Data & APIs", "Datasets, dumps and developer APIs — which free tiers are real, and which ones died."),
    "leisure": ("Leisure", "Free things to do and the deal platforms behind the rest — museums, meetups, Groupon, and your library."),
}

VERDICTS = {
    "truly":   ("Truly Free",   "#0E7B47", "#E4F2EA", "No card, no account wall, no meaningful catch. Use it and go."),
    "forever": ("Free Forever", "#0A6E8A", "#E2EFF4", "A real permanent free plan. Signup and fair limits — but no clock and no card."),
    "freeish": ("Free-ish",     "#A05E03", "#F7EDDC", "A free tier exists, but it's shaped to squeeze you toward paying."),
    "trap":    ("Trap Trial",   "#C2410C", "#FBE8DE", "Card up front. It bills you automatically unless you cancel in time."),
    "fake":    ("Fake Free",    "#B3261E", "#F9E3E1", "Marketed as free. It isn't — you pay in money, data, or bandwidth."),
    "notfree": ("Not Free",     "#545E68", "#E9ECEF", "People search for a free version. There isn't one."),
}

def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"is-{s}-actually-free"

def esc(t): return html.escape(t, quote=True)

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="preconnect" href="https://www.google.com"><link rel="dns-prefetch" href="https://www.google.com"><link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Public+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500;600&display=swap"><link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Public+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet" media="print" onload="this.media=&#39;all&#39;"><noscript><link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Public+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet"></noscript>'

CSS = """
:root{--n:{SPRITE_N};--paper:#F7F8F5;--ink:#15181B;--muted:#5A6470;--line:#D9DDD6;--brand:#0E7B47;
--card:#FFFFFF;--maxw:1060px;}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--paper);color:var(--ink);font:400 16.5px/1.65 "Public Sans",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 22px}
.mono{font-family:"IBM Plex Mono",monospace}
.hero{position:relative;overflow:hidden}
/* nav */
.site-header{position:sticky;top:0;z-index:20;background:var(--paper);background-image:none}
.nav{border-bottom:1px solid var(--line);height:52px}
.nav-in{display:flex;align-items:center;justify-content:space-between;height:52px}
.logo{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:13px;letter-spacing:.14em;text-decoration:none;border:2px solid var(--ink);padding:4px 10px;border-radius:5px;display:inline-flex;gap:0;align-items:center}
.logo b{color:var(--brand)}
.nav-links{display:flex;gap:18px;align-items:center;height:52px}
.nav-links a{flex:0 0 auto;white-space:nowrap;font-size:13px;font-weight:600;text-decoration:none;color:var(--muted);line-height:52px}
.nav-links a:hover{color:var(--ink)}
/* The nav row has never had a small-screen rule, so it simply overflowed the
   page — adding a link made that visible. Let it scroll instead of pushing
   the document wider than the viewport. */
@media(max-width:1080px){
.nav-in{gap:12px}
.nav-links{gap:15px;flex:1;min-width:0;overflow-x:auto;justify-content:flex-start;scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch}
.nav-links::-webkit-scrollbar{display:none}
.nav-links a{white-space:nowrap}
}
.dropdown{position:relative;height:52px;display:flex;align-items:center}
.dropdown>a{line-height:52px}
.dropdown>a::after{content:" ▾";font-size:11px}
/* Was display:none -> display:block on hover, which cannot be delayed. The
   language trigger is ~50px wide and its menu is 230px right-aligned, so a
   diagonal move toward an option left the hover area and the menu vanished.
   visibility+opacity allows a grace period on the way out, and the padding-top
   bridges the trigger to the panel so there is no dead row between them. */
.dropdown-menu{visibility:hidden;opacity:0;position:absolute;top:52px;left:-12px;padding-top:6px;z-index:30;transition:opacity .12s ease}
.dropdown-menu .dd-inner{background:var(--card);border:1.5px solid var(--line);border-radius:0 0 10px 10px;padding:6px 0;min-width:230px;box-shadow:0 6px 20px rgba(0,0,0,.08)}
/* Open state is driven only by JS. Hiding must never depend on a transition
   finishing — under prefers-reduced-motion, or any context that does not run
   transitions, a delayed visibility change never commits and the menu sticks
   open. The close delay is a timer instead. */
.dropdown.open .dropdown-menu{visibility:visible;opacity:1}
.dropdown-menu a{display:flex;align-items:center;gap:10px;padding:9px 16px;font-size:14px;font-weight:600;text-decoration:none;color:var(--ink);white-space:nowrap;line-height:1.4}
.dropdown-menu a:hover{background:var(--paper);color:var(--brand)}
.dropdown-menu a .dd-count{margin-left:auto;font-size:11px;font-weight:700;color:var(--muted);opacity:.6}
.dropdown-menu.right{left:auto;right:-12px}
.langdd>a{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.06em}
.dropdown-menu a.cur{color:var(--brand)}
.dropdown-menu a .cicon{margin:0}
.dropdown-menu a .cicon svg{width:18px;height:18px}
.dropdown-menu .sep{height:1px;background:var(--line);margin:4px 12px}
.catbar{border-bottom:1px solid var(--line);padding:0;background:var(--paper);min-height:42px}
.catbar-in{display:flex;align-items:center;gap:10px;padding:6px 22px;max-width:var(--maxw);margin:0 auto}
.catfilters{display:flex;align-items:center;flex-wrap:wrap;gap:6px;flex:1 1 auto;min-width:0;padding:2px 1px}
.catbar .pill-toggle .pc{font-size:10px;font-weight:700;opacity:.5;margin-left:1px}
.catbar .pill-toggle.on .pc{color:var(--brand);opacity:.9}
.catbar .pill-toggle.reset .pc{color:var(--brand);opacity:.85}
.catbar .pill-toggle{display:inline-flex;align-items:center;gap:5px;font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.04em;text-decoration:none;color:var(--muted);padding:5px 11px;border-radius:99px;border:1.5px solid transparent;cursor:pointer;transition:color .15s,background .15s,border-color .15s,box-shadow .15s;line-height:1;white-space:nowrap;background:transparent;user-select:none}
.catbar .pill-toggle.reset{color:var(--brand);font-weight:700;border:1.5px solid var(--brand);background:#E4F2EA}
.catbar .pill-toggle.reset:not(.on):not(.none){background:transparent}
.catbar .pill-toggle.reset:hover{background:var(--brand);color:var(--paper)}
.catbar .pill-toggle.reset.none{color:var(--muted);border-color:var(--line);background:transparent}
.catbar .pill-toggle.reset.none:hover{background:var(--ink);border-color:var(--ink);color:var(--paper)}
.catbar .pill-toggle:hover{color:var(--ink);background:var(--card);border-color:var(--line)}
.catbar .pill-toggle.on{color:var(--brand);background:#E4F2EA;border-color:var(--brand);box-shadow:0 0 0 1px rgba(14,123,71,.12)}
.catbar .pill-toggle .caticon{width:14px;height:14px;border-radius:3px}
.catbar .pill-toggle.on .caticon{filter:none}
.catbar .pill-toggle:not(.on) .caticon{filter:grayscale(1);opacity:.5}
.catbar .divider{width:1px;height:18px;background:var(--line);flex-shrink:0;margin:0 3px}
.catbar .pill-link{display:inline-flex;align-items:center;font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.04em;text-decoration:none;color:var(--muted);padding:5px 11px;border-radius:99px;line-height:1;white-space:nowrap;transition:color .15s}
.catbar .pill-link:hover{color:var(--brand)}
.catbar .gear{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;border:1.5px solid var(--line);background:transparent;cursor:pointer;margin-left:auto;flex-shrink:0;color:var(--muted);font-size:14px;transition:all .15s}
.catbar .gear:hover{border-color:var(--brand);color:var(--brand);background:#E4F2EA}
.catbar .gear svg{width:16px;height:16px}
.custpanel{max-height:0;overflow:hidden;transition:max-height .25s ease,padding .25s ease;border-bottom:0;background:var(--card);padding:0 22px}
.custpanel.open{max-height:200px;padding:16px 22px;border-bottom:1px solid var(--line)}
.custpanel-in{max-width:var(--maxw);margin:0 auto;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.custpanel h3{font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0;white-space:nowrap}
.custpanel label{display:inline-flex;align-items:center;gap:5px;font-size:12.5px;font-weight:600;padding:5px 10px;cursor:pointer;border-radius:99px;border:1.5px solid var(--line);user-select:none;transition:all .15s;white-space:nowrap}
.custpanel label:hover{border-color:var(--ink)}
.custpanel label.on{border-color:var(--brand);background:#E4F2EA;color:var(--brand)}
.custpanel input{display:none}
.sortbar{display:none}
/* side legend */
.side-legend{position:fixed;top:100px;right:0;z-index:15;transition:transform .25s ease}
/* Fully off-screen, not 100%-minus-32px. The tab is absolutely positioned at
   left:-32px, i.e. OUTSIDE the panel, so it stays visible on its own — the
   32px allowance just left a strip of the panel body showing at the right
   edge, with chips half-cut. */
.side-legend.closed{transform:translateX(100%)}
.side-legend .sl-tab{position:absolute;left:-32px;top:0;width:32px;height:100px;background:var(--ink);color:var(--paper);border-radius:6px 0 0 6px;cursor:pointer;display:flex;align-items:center;justify-content:center;writing-mode:vertical-rl;font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase}
.side-legend .sl-body{background:var(--card);border:1.5px solid var(--line);border-right:0;border-radius:10px 0 0 10px;padding:14px 16px;width:240px;box-shadow:-4px 0 16px rgba(0,0,0,.06);max-height:calc(100vh - 120px);overflow-y:auto}
.side-legend h2{font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
.side-legend .sl-item{display:flex;gap:8px;align-items:baseline;font-size:12px;color:var(--muted);margin:0 0 5px;line-height:1.4}
.side-legend .sl-item .pill{font-size:9.5px;padding:2px 6px}
.side-legend .sl-divider{height:1px;background:var(--line);margin:10px 0}
.side-legend .sl-sorts{display:flex;flex-direction:column;gap:4px}
.side-legend .sortbtn{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.06em;border:1.5px solid var(--line);border-radius:6px;padding:4px 10px;background:var(--card);color:var(--muted);cursor:pointer;transition:all .12s;text-align:left}
.side-legend .sortbtn:hover{border-color:var(--ink);color:var(--ink)}
.side-legend .sortbtn.active{border-color:var(--brand);color:var(--brand);background:#E4F2EA}
@media(max-width:768px){.side-legend{display:none}}
/* legacy hidden */
.legend{display:none}
.hero{padding:26px 0 14px;text-align:left}
.hero h1{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:clamp(30px,3.8vw,46px);line-height:1;letter-spacing:-.02em;margin:0}
.hero-top{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 13px}
.hero-line{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:3px 26px;margin:9px 0 0}
.hero h1 em{font-style:normal;color:var(--brand)}
.hero h1 .amp{font-family:"Bricolage Grotesque",sans-serif;font-weight:300;font-style:italic;opacity:.5;font-size:.85em}
.hero .tagline{font-family:"IBM Plex Mono",monospace;font-size:clamp(11px,1.2vw,13px);font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--brand);margin:0;opacity:.7}
.hero p.sub{margin:0;font-size:16px;color:var(--muted);max-width:60ch}
.hero p.sub strong{color:var(--ink);font-weight:600}
.stats{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0;white-space:nowrap}
.searchbar{margin:15px 0 6px;display:flex;align-items:center;gap:0;max-width:640px;border:2.5px solid var(--ink);border-radius:12px;background:var(--card);overflow:hidden}
.searchbar input{flex:1;border:0;outline:0;padding:16px 18px;font:400 17px "Public Sans",sans-serif;background:transparent;color:var(--ink)}
.searchbar .kbd{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted);padding:0 16px;white-space:nowrap}
.count{font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--muted);margin-top:10px}
/* legend */
.legend{margin:44px 0 8px;border-top:2.5px solid var(--ink);padding-top:20px}
.legend h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:16px}
.legend-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px 26px}
.legend-item{display:flex;gap:12px;align-items:baseline;font-size:14.5px;color:var(--muted)}
.legend-item .pill{flex-shrink:0}
/* pills + stamp */
.pill{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;padding:3px 9px;border-radius:6px;border:1.5px solid;white-space:nowrap}
.stamp{display:inline-block;font-family:"IBM Plex Mono",monospace;font-weight:600;letter-spacing:.16em;text-transform:uppercase;border:3.5px solid;border-radius:10px;padding:12px 22px;font-size:clamp(17px,2.6vw,24px);transform:rotate(-2deg);transform-origin:center}
@keyframes thunk{0%{transform:rotate(-2deg) scale(1.25);opacity:0}55%{transform:rotate(-2deg) scale(.96);opacity:1}100%{transform:rotate(-2deg) scale(1)}}
.stamp.animate{animation:thunk .34s cubic-bezier(.2,.9,.3,1.2) both}
@media (prefers-reduced-motion:reduce){.stamp.animate{animation:none}}
/* sections + cards */
.section{padding:34px 0 6px}
.section-head{display:flex;justify-content:space-between;align-items:baseline;gap:16px;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:18px}
.section-head h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:26px;letter-spacing:-.01em}
.section-head h2 a{text-decoration:none}
.section-head h2 a:hover{color:var(--brand)}
.section-head .all{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--muted);text-decoration:none;white-space:nowrap}
.section-head .all:hover{color:var(--brand)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;padding-bottom:26px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 16px 14px;text-decoration:none;display:flex;flex-direction:column;gap:9px;transition:transform .12s ease,border-color .12s ease}
.card:hover{transform:translateY(-2px);border-color:var(--ink)}
.card h3{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:18.5px;line-height:1.2}
.card .cost{font-size:13.5px;color:var(--muted);line-height:1.5}
.card .cost b{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink);display:block;margin-bottom:2px}
.vtag{display:inline-block;font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-top:auto;padding-top:6px}
.vtag.saves{color:var(--brand);background:#E4F2EA;border:1.5px solid var(--brand);border-radius:6px;padding:3px 8px;margin-top:auto}
.vtag.pays{color:#fff;background:var(--brand);border:1.5px solid var(--brand);border-radius:6px;padding:3px 8px;margin-top:auto;font-weight:700}
.vtag.pays.low{color:#A05E03;background:#F7EDDC;border-color:#A05E03}
.vtag.trap-warn{color:#B3261E;background:#F9E3E1;border:1.5px solid #B3261E;border-radius:6px;padding:3px 8px;margin-top:auto}
.noresults{display:none;color:var(--muted);padding:26px 0 40px;font-size:15.5px}
/* listing page */
.crumb{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--muted);padding:26px 0 0}
.crumb a{color:var(--muted);text-decoration:none}
.crumb a:hover{color:var(--brand)}
.listing{padding:18px 0 30px;max-width:720px}
.listing h1{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:clamp(32px,5vw,50px);line-height:1.04;letter-spacing:-.015em;margin:8px 0 26px}
.answer{font-size:19px;line-height:1.6;margin:28px 0 0}
.facts{margin:30px 0;border:2.5px solid var(--ink);border-radius:12px;background:var(--card);overflow:hidden}
.facts h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;padding:12px 18px;border-bottom:2.5px solid var(--ink)}
.facts table{width:100%;border-collapse:collapse}
.facts td{padding:11px 18px;font-size:15px;border-top:1px solid var(--line);vertical-align:top}
.facts tr:first-child td{border-top:0}
.facts td.k{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);width:190px;white-space:nowrap}
.worth{margin:26px 0 0;border-left:4px solid var(--brand);background:var(--card);border-radius:0 10px 10px 0;padding:12px 16px}
.worth b{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--brand);display:block;margin-bottom:3px}
.worth p{margin:0;font-size:16px;line-height:1.55}
.plays{margin:26px 0 0}
.plays h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:21px;margin-bottom:8px}
.plays ul{list-style:none;margin:0;padding:0}
.plays li{padding:5px 0 5px 26px;position:relative;font-size:15.5px;line-height:1.55}
.plays li::before{content:"→";position:absolute;left:0;top:5px;font-family:"IBM Plex Mono",monospace;font-weight:600;color:var(--brand)}
.gets{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:30px 0 0}
.gets .col{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:16px 18px}
.gets h2{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.gets ul{list-style:none;margin:0;padding:0}
.gets li{padding:5px 0 5px 26px;position:relative;font-size:15px;line-height:1.5}
.gets li::before{position:absolute;left:0;top:5px;font-family:"IBM Plex Mono",monospace;font-weight:600}
.gets .free li::before{content:"✓";color:var(--brand)}
.gets .locked li::before{content:"✗";color:#9AA3AC}
.gets .none{color:var(--muted);font-style:italic;font-size:15px}
@media(max-width:640px){.gets{grid-template-columns:1fr}}
.row{display:flex;align-items:center;gap:8px}
.chip{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:12px;border:1.5px solid;border-radius:6px;padding:2px 8px;margin-left:auto;white-space:nowrap}
.scores{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:24px 0 0;max-width:520px}
.score b{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:4px}
.score .num{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:34px;line-height:1}
.score .num i{font-style:normal;font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;color:var(--muted);margin-left:3px}
.score .bar{height:7px;background:var(--line);border-radius:99px;margin-top:8px;overflow:hidden}
.score .bar div{height:100%;border-radius:99px}
.plain{margin:12px 0 0;padding-top:10px;border-top:1px solid var(--line);font-size:14.5px;color:var(--muted);line-height:1.55}
.gets .warn li::before{content:"!";color:#A05E03}
.gets h3.sub{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:12px 0 4px;padding-top:10px;border-top:1px solid var(--line)}
.moreinfo{margin:28px 0 0}
.moreinfo > h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
details.more{border:1px solid var(--line);border-radius:10px;background:var(--card);margin-top:8px;overflow:hidden}
details.more summary{cursor:pointer;padding:12px 16px;font-weight:600;font-size:15px;list-style:none;display:flex;justify-content:space-between;align-items:center;gap:12px}
details.more summary::-webkit-details-marker{display:none}
details.more summary::after{content:"+";font-family:"IBM Plex Mono",monospace;font-weight:600;color:var(--brand);font-size:17px;flex-shrink:0}
details.more[open] summary::after{content:"–"}
details.more .mbody{padding:0 16px 14px;font-size:15px;line-height:1.62;color:var(--ink)}
details.more.mini{max-width:520px;margin-top:10px}
details.more.mini summary{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding:9px 14px}
details.more.mini .mbody{font-size:13.5px;color:var(--muted)}
.disc{font-size:12px;color:var(--muted);margin:4px 0 0;line-height:1.5;opacity:.75}
.bizband{border-top:2.5px solid var(--ink);background:var(--card);margin-top:44px;padding:42px 0 48px}
.bizband h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:clamp(24px,3.5vw,34px);letter-spacing:-.015em}
.bizband p{margin:12px 0 22px;color:var(--muted);font-size:17px;max-width:60ch}
.fav{width:28px;height:28px;border-radius:7px;background:#fff;border:1px solid var(--line);padding:2px;object-fit:contain;flex-shrink:0}
.fav.big{width:46px;height:46px;border-radius:11px;padding:4px}
.titlerow{display:flex;gap:14px;align-items:flex-start;margin:8px 0 0}
.titlerow h1{margin:0}
.cicon{display:inline-flex;vertical-align:-4px;margin-right:10px}
.cicon svg{width:25px;height:25px}
.caticon{width:28px;height:28px;object-fit:contain}
.pagehead .cicon{display:block;margin:0 0 14px}
.pagehead .caticon{width:48px;height:48px}
.deal{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:14px}
.deal .dtop{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.deal .dtop h3{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:18px;margin:0}
.deal .dbadge{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;padding:3px 9px;border-radius:6px;border:1.5px solid;white-space:nowrap}
.deal .dbadge.verified{color:#0E7B47;border-color:#0E7B47;background:#E4F2EA}
.deal .dbadge.seasonal{color:#A05E03;border-color:#A05E03;background:#F7EDDC}
.deal .dbadge.expired{color:#B3261E;border-color:#B3261E;background:#F9E3E1}
.deal .dtype{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--brand);margin:0 0 6px}
.deal p{margin:0 0 8px;font-size:15px;line-height:1.55}
.deal .dlabel{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-top:12px}
.deal .dworth{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:20px;color:var(--brand);margin:4px 0 0}
.deal .dcav{font-size:13.5px;color:var(--muted);margin-top:8px;border-top:1px solid var(--line);padding-top:8px}
.deal a.dlink{display:inline-block;margin-top:10px;font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:13px;text-decoration:none;color:var(--brand);border-bottom:1.5px solid var(--brand)}
.deal a.dlink:hover{color:var(--ink);border-color:var(--ink)}
.alts{margin:28px 0 0;border:2px solid var(--brand);border-radius:12px;background:#E4F2EA;padding:18px 20px}
.alts h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--brand);margin:0 0 10px}
.alts h2::before{content:"✓ "}
.alt-card{display:flex;gap:12px;align-items:baseline;padding:8px 0;border-top:1px solid rgba(14,123,71,.2)}
.alt-card:first-of-type{border-top:0;padding-top:0}
.alt-card a{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:17px;color:var(--brand);text-decoration:none;flex-shrink:0}
.alt-card a:hover{text-decoration:underline}
.alt-card span{font-size:14.5px;color:var(--ink)}
.reqform{background:var(--card);border:2px solid var(--ink);border-radius:12px;padding:22px 24px;max-width:520px;margin:22px 0 30px}
.reqform label{display:block;font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:12px 0 4px}
.reqform label:first-child{margin-top:0}
.reqform input,.reqform textarea{width:100%;border:1.5px solid var(--line);border-radius:8px;padding:10px 12px;font:400 15px "Public Sans",sans-serif;color:var(--ink);background:var(--paper)}
.reqform input:focus,.reqform textarea:focus{outline:2px solid var(--brand);border-color:var(--brand)}
.reqform textarea{height:70px;resize:vertical}
.reqform button{margin-top:14px;font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:14px;letter-spacing:.06em;border:2.5px solid var(--ink);border-radius:10px;padding:12px 24px;background:var(--ink);color:var(--paper);cursor:pointer;transition:all .12s ease}
.reqform button:hover{background:var(--brand);border-color:var(--brand)}
.reqform .ty{display:none;font-size:15px;color:var(--brand);font-weight:600;padding:16px 0}
.badge-section{margin:30px 0}
.badge-preview{display:inline-flex;align-items:center;gap:8px;border:2px solid var(--brand);border-radius:10px;padding:8px 14px;background:#E4F2EA;font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:13px;color:var(--brand);text-decoration:none}
.badge-preview svg{width:20px;height:20px}
.embed-box{margin:12px 0;background:var(--paper);border:1.5px solid var(--line);border-radius:8px;padding:12px;font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted);word-break:break-all;line-height:1.6;cursor:pointer;position:relative}
.embed-box:hover{border-color:var(--brand)}
.embed-box .copied{display:none;position:absolute;top:8px;right:12px;font-size:11px;color:var(--brand);font-weight:600}
.chlog{margin:12px 0;border-left:3px solid var(--brand);padding:2px 0 2px 14px}
.chlog .chdate{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.chlog .chbody{font-size:14.5px;line-height:1.55;margin:2px 0 0}
.chlog .chtag{font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:600;letter-spacing:.08em;padding:2px 7px;border-radius:5px;margin-left:6px}
.chlog .chtag.down{color:#C2410C;background:#FBE8DE;border:1px solid #C2410C}
.chlog .chtag.up{color:#0E7B47;background:#E4F2EA;border:1px solid #0E7B47}
.chlog .chtag.note{color:#A05E03;background:#F7EDDC;border:1px solid #A05E03}
.ca-badge,.ca-note{display:none}
body.loc-ca .ca-badge,body.loc-ca .ca-note{display:block}
.ca-badge{align-items:center;gap:5px;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.06em;color:#C2410C;border:1.5px solid #C2410C;border-radius:6px;padding:3px 8px;margin:10px 0 0;background:#FBE8DE}
.ca-badge.avail{color:#0E7B47;border-color:#0E7B47;background:#E4F2EA}
body.loc-ca .ca-badge{display:inline-flex}
.ca-note{margin:6px 0 0;font-size:13.5px;color:var(--muted);line-height:1.5}
.loc-pick{display:inline-flex;align-items:center;gap:4px;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;color:var(--muted);padding:5px 10px;border-radius:99px;border:1.5px solid var(--line);cursor:pointer;background:transparent;white-space:nowrap;transition:all .15s;margin-left:4px}
.loc-pick:hover{border-color:var(--brand);color:var(--brand)}
.loc-pick.active{border-color:var(--brand);color:var(--brand);background:#E4F2EA}
.loc-menu{display:none;position:absolute;top:calc(100% + 6px);right:0;background:var(--card);border:1.5px solid var(--line);border-radius:10px;padding:6px 0;min-width:160px;box-shadow:0 4px 16px rgba(0,0,0,.08);z-index:30}
.loc-menu.open{display:block}
.loc-menu a{display:block;padding:8px 14px;font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;text-decoration:none;color:var(--ink);cursor:pointer}
.loc-menu a:hover{background:var(--paper);color:var(--brand)}
.loc-menu a.sel{color:var(--brand)}
.loc-wrap{position:relative;flex-shrink:0;padding-left:12px;border-left:1px solid var(--line)}
.ext-ratings{margin:22px 0 0;display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.ext-ratings .er-lbl{font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);width:100%;margin:0 0 -1px}
.ext-ratings .er-note{font-size:11px;color:var(--muted);font-style:italic;width:100%;margin:2px 0 0}
.ext-rat{display:inline-flex;align-items:center;gap:5px;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;text-decoration:none;color:var(--muted);border:1.5px solid var(--line);border-radius:6px;padding:3px 9px;transition:border-color .12s}
.ext-rat:hover{border-color:var(--brand);color:var(--brand)}
.ext-rat .er-score{color:var(--ink);font-size:12px}
.ext-rat .er-n{color:var(--muted);font-size:10.5px;font-weight:500}
.ext-rat .er-n::before{content:"· "}
/* AI-page leaderboard sidebar (self-hosted checkmysite widget, themed native) */
.ai-layout{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:30px;align-items:start}
.ai-lb{position:sticky;top:18px;
  --cms-bg:var(--card);--cms-panel:var(--paper);--cms-text:var(--ink);--cms-dim:var(--muted);
  --cms-accent:var(--brand);--cms-rule:var(--line);
  --cms-font:"Public Sans",system-ui,sans-serif;--cms-mono:"IBM Plex Mono",monospace}
.ai-lb-note{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted);margin:10px 0 0;line-height:1.6}
@media(max-width:1000px){.ai-layout{grid-template-columns:1fr}.ai-lb{position:static;order:2}}
/* free site check (AI + SEO) */
.sitecheck{border-top:1px solid var(--line);margin:36px 0 0;padding:44px 0}
.sitecheck .sc-head h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:clamp(26px,4vw,40px);line-height:1.05;letter-spacing:-.02em;margin:0 0 8px}
.sitecheck .sc-head p{margin:0 0 20px;color:var(--muted);max-width:60ch;font-size:16px}
.sitecheck .sc-head p b{color:var(--ink);font-weight:600}
.sc-form{display:flex;gap:0;max-width:560px;border:2.5px solid var(--ink);border-radius:12px;background:var(--card);overflow:hidden}
.sc-form input{flex:1;min-width:0;border:0;outline:0;padding:15px 18px;font:400 17px "Public Sans",sans-serif;background:transparent;color:var(--ink)}
.sc-form button{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;border:0;padding:0 22px;background:var(--brand);color:#fff;cursor:pointer;white-space:nowrap;transition:background .15s}
.sc-form button:hover{background:#0b6239}
.sc-form button:disabled{opacity:.6;cursor:default}
.sc-status{margin:16px 0 0;font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--muted);line-height:1.55}
.sc-status b{color:var(--ink);font-weight:600}
.sc-status.err{color:#C0392B}
.sc-results{margin:14px 0 0;max-width:720px}
.sc-row{display:grid;grid-template-columns:22px 1fr;gap:12px;padding:13px 0;border-bottom:1px solid var(--line)}
.sc-row:last-child{border-bottom:none}
.sc-ico{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;flex-shrink:0}
.sc-row.pass .sc-ico{background:var(--brand)}
.sc-row.warn .sc-ico{background:#B26A00}
.sc-row.fail .sc-ico{background:#C0392B}
.sc-rl{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.sc-rl b{font-size:15px;font-weight:600}
.sc-tag{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);border:1px solid var(--line);border-radius:99px;padding:1px 7px}
.sc-d{margin:3px 0 0;color:var(--muted);font-size:14px;line-height:1.55}
.sc-lead-h{margin:22px 0 8px;font-size:15px;font-weight:600;color:var(--ink)}
.sc-lead{margin-top:0}
.sc-lead-msg{margin:10px 0 0;font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;color:var(--brand)}
.sc-foot{margin:18px 0 0;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted)}
.sc-foot a{color:var(--brand);text-decoration:none}
.sc-foot a:hover{text-decoration:underline}
@media(max-width:480px){.sc-form{flex-direction:column;border-radius:12px}.sc-form button{padding:13px}}
.headlines{margin:32px 0 0;border-top:1px solid var(--line);padding-top:20px}
.headlines h2{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}
.hl-list{display:flex;flex-direction:column;gap:6px}
.hl-item{display:flex;gap:10px;align-items:baseline}
.hl-item .hl-date{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted);flex-shrink:0;width:60px}
.hl-item a{font-size:14.5px;font-weight:600;color:var(--ink);text-decoration:none}
.hl-item a:hover{color:var(--brand)}
.vfilters{display:flex;gap:4px;margin:10px 0 0;flex-wrap:wrap}
.vfilter{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.04em;border:1.5px solid var(--line);border-radius:99px;padding:4px 10px;background:transparent;color:var(--muted);cursor:pointer;transition:all .12s}
.vfilter:hover{border-color:var(--ink);color:var(--ink)}
.vfilter.on{border-color:var(--brand);color:var(--brand);background:#E4F2EA}
.backtop{position:fixed;bottom:24px;right:24px;width:40px;height:40px;border-radius:50%;background:var(--ink);color:var(--paper);border:0;cursor:pointer;font-size:18px;display:none;align-items:center;justify-content:center;z-index:15;box-shadow:0 2px 10px rgba(0,0,0,.15);transition:background .12s}
.backtop:hover{background:var(--brand)}
.backtop.show{display:flex}
[data-tip]{position:relative;cursor:help}
[data-tip]:hover::after{content:attr(data-tip);position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);background:var(--ink);color:var(--paper);font:600 12px/1.45 "Public Sans",sans-serif;letter-spacing:0;text-transform:none;padding:8px 12px;border-radius:8px;width:max-content;max-width:260px;white-space:normal;z-index:40;box-shadow:0 4px 14px rgba(0,0,0,.18);pointer-events:none}
[data-tip]:hover::before{content:"";position:absolute;bottom:calc(100% + 2px);left:50%;transform:translateX(-50%);border:6px solid transparent;border-top-color:var(--ink);z-index:40;pointer-events:none}
.sent{margin:26px 0 0;border:1.5px solid var(--line);border-left:4px solid var(--brand);border-radius:10px;padding:18px 20px;background:var(--card)}
.sent h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;margin:0 0 4px;color:var(--ink)}
.sent .sn-split{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--muted);margin:0 0 14px;letter-spacing:.02em}
.sent .sn-row{margin:0 0 12px;font-size:14.5px;line-height:1.6}
.sent .sn-row b{display:block;font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 3px}
.sent .sn-take{border-top:1px solid var(--line);padding-top:12px;margin-top:14px;font-size:15px;line-height:1.6;font-weight:600}
.sent .sn-src{font-size:11.5px;color:var(--muted);margin:12px 0 0;font-style:italic}
.safety{margin:26px 0 0;border:1.5px solid var(--line);border-left:4px solid var(--ink);border-radius:10px;padding:18px 20px;background:var(--card)}
.safety h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:21px;margin:0 0 8px}
.safety .sf-verdict{margin:0 0 14px;font-size:16px;line-height:1.55;font-weight:600}
.safety .sf-row{display:flex;gap:10px;margin:0 0 9px;font-size:14.5px;line-height:1.55}
.safety .sf-row b{font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);flex-shrink:0;width:118px;padding-top:3px}
.safety .sf-src{border-top:1px solid var(--line);padding-top:11px;margin:14px 0 0;font-size:11.5px;color:var(--muted);font-style:italic}
@media(max-width:560px){.safety .sf-row{display:block}.safety .sf-row b{width:auto;display:block;margin:0 0 2px}}
/* coupon codes */
.dcode{display:inline-flex;align-items:center;gap:0;margin:4px 0 14px;border:2px dashed var(--brand);border-radius:9px;background:#E4F2EA;cursor:pointer;user-select:none;transition:background .12s,border-color .12s}
.dcode:hover,.dcode:focus-visible{background:var(--brand);border-style:solid}
.dcode:hover .dc-val,.dcode:hover .dc-lbl,.dcode:hover .dc-act,.dcode:focus-visible .dc-val{color:var(--paper)}
.dcode.copied{background:var(--brand);border-style:solid}
.dcode.copied .dc-val,.dcode.copied .dc-lbl,.dcode.copied .dc-act{color:var(--paper)}
.dc-lbl{font-family:"IBM Plex Mono",monospace;font-size:9.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--brand);padding:0 9px 0 11px;opacity:.75}
.dc-val{font-family:"IBM Plex Mono",monospace;font-size:15px;font-weight:700;letter-spacing:.08em;color:var(--brand);padding:8px 0}
.dc-act{font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--brand);padding:0 11px 0 12px;opacity:.75}
/* same-publisher disclosure, above the pitch rather than under it */
.ddisc{margin:0 0 10px;font-size:12.5px;line-height:1.5;color:#A05E03;background:#F7EDDC;border-left:3px solid #A05E03;padding:7px 11px;border-radius:0 6px 6px 0}
.ddisc::before{content:"Disclosure — ";font-weight:700}
/* common questions */
.faqs{margin:26px 0 0}
.faqs h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;margin:0 0 10px}
.faq-q{border-bottom:1px solid var(--line)}
.faq-q>summary{cursor:pointer;list-style:none;padding:11px 0;font-weight:600;font-size:15.5px;line-height:1.4;display:flex;gap:10px;align-items:baseline}
.faq-q>summary::-webkit-details-marker{display:none}
.faq-q>summary::before{content:"+";font-family:"IBM Plex Mono",monospace;color:var(--brand);font-weight:700;flex-shrink:0}
.faq-q[open]>summary::before{content:"−"}
.faq-q>summary:hover{color:var(--brand)}
.faq-a{padding:0 0 13px 22px;font-size:14.5px;line-height:1.65;color:var(--muted);max-width:70ch}
/* comparable free-tier spec */
.freespec{margin:26px 0 0;border:1.5px solid var(--line);border-radius:12px;padding:18px 20px;background:var(--card)}
.freespec h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;margin:0 0 12px}
.freespec table{width:100%;border-collapse:collapse}
.freespec td{padding:7px 0;border-bottom:1px solid var(--line);font-size:14.5px;vertical-align:top}
.freespec tr:last-child td{border-bottom:0}
.freespec td.k{width:190px;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding-top:9px}
.freespec .fs-note{margin:12px 0 0;font-size:11.5px;color:var(--muted);font-style:italic;line-height:1.55}
.sv{display:inline-block;font-weight:600;font-size:14px;border-left:3px solid var(--line);padding-left:9px}
.sv.good{border-color:#0E7B47;color:#0E7B47}
.sv.bad{border-color:#B3261E;color:#B3261E}
.sv.mid{border-color:#A05E03;color:#A05E03}
.sv.off{border-color:var(--line);color:var(--muted)}
/* the category comparison grid */
.cmp{padding:44px 0 10px;border-top:2.5px solid var(--ink);margin-top:40px}
.cmp h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:25px;margin:0 0 6px}
.cmp-lede{color:var(--muted);font-size:15px;max-width:66ch;margin:0 0 18px}
.cmp-scroll{overflow-x:auto;border:1.5px solid var(--line);border-radius:12px}
.cmp-table{border-collapse:collapse;width:100%;min-width:820px;background:var(--card)}
.cmp-table th,.cmp-table td{padding:10px 13px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
.cmp-table thead th{font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);background:var(--paper);position:sticky;top:0}
.cmp-table tbody th{font-weight:700;font-size:14.5px;background:var(--card);position:sticky;left:0;border-right:1px solid var(--line)}
.cmp-table tbody th a{color:var(--ink);text-decoration:none}
.cmp-table tbody th a:hover{color:var(--brand)}
.cmp-table tbody tr:last-child th,.cmp-table tbody tr:last-child td{border-bottom:0}
.cmp-table .sv{font-size:13px;border-left-width:3px;padding-left:8px}
@media(max-width:560px){.freespec td.k{width:auto;display:block;padding-bottom:0;border:0}.freespec td{display:block}.freespec tr{display:block;border-bottom:1px solid var(--line);padding:6px 0}}
/* Folded page rationale. The reasoning behind a page is worth keeping and
   worth reading once — it is not worth 130 words of the first screen every
   time. Available in one click, invisible otherwise. */
.pagenote{max-width:720px;margin:0 0 20px;border-left:3px solid var(--line);padding:0 0 0 14px}
.pagenote>summary{cursor:pointer;list-style:none;font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding:3px 0}
.pagenote>summary::-webkit-details-marker{display:none}
.pagenote>summary::after{content:" +";font-weight:700}
.pagenote[open]>summary::after{content:" −"}
.pagenote>summary:hover{color:var(--brand)}
.pagenote .pn-body{padding:8px 0 4px;font-size:14.5px;line-height:1.65;color:var(--muted);max-width:68ch}
.pagenote .pn-body p{margin:0 0 11px}
.pagenote .pn-body p:last-child{margin:0}
/* tighter page heads — the h1 and one line, then the content */
.pagehead.tight{padding-top:34px;padding-bottom:6px}
.pagehead.tight p{margin:10px 0 14px;font-size:16.5px}
/* per-listing verification age */
.checked .ck-date{font-weight:600}
.checked .ck-date.fresh{color:var(--ink)}
.checked .ck-flag{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;border:1px solid var(--line);border-radius:5px;padding:1px 6px;margin-left:7px;color:var(--muted);cursor:help}
.checked .ck-flag.due{color:#A05E03;border-color:#A05E03;background:#F7EDDC}
/* "we checked this" — the door back into our own verdicts */
.st-ours{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 10px;padding:8px 11px;border:1.5px solid var(--line);border-radius:9px;background:var(--paper);text-decoration:none;transition:border-color .12s,background .12s}
.st-ours:hover{border-color:var(--ink);background:var(--card)}
.so-lbl{font-family:"IBM Plex Mono",monospace;font-size:9.5px;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.so-name{font-weight:700;font-size:13.5px;color:var(--ink)}
.so-verdict{font-family:"IBM Plex Mono",monospace;font-size:9.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:2px 7px;border-radius:5px;border:1.5px solid;margin-left:auto;white-space:nowrap}
.so-verdict.v-truly{color:#0E7B47;border-color:#0E7B47;background:#E4F2EA}
.so-verdict.v-forever{color:#0A6E8A;border-color:#0A6E8A;background:#E2EFF4}
.so-verdict.v-freeish{color:#A05E03;border-color:#A05E03;background:#F7EDDC}
.so-verdict.v-trap,.so-verdict.v-fake,.so-verdict.v-notfree{color:#B3261E;border-color:#B3261E;background:#F9E3E1}
/* landing handoff into the directory */
.handoff{padding:34px 0 46px}
.handoff-card{display:block;max-width:720px;border:2.5px solid var(--ink);border-radius:14px;padding:22px 26px;background:var(--card);text-decoration:none;transition:background .12s,transform .12s}
.handoff-card:hover{background:var(--paper);transform:translateY(-2px)}
.ho-k{display:block;font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.ho-h{display:block;font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:clamp(21px,2.5vw,28px);letter-spacing:-.015em;color:var(--ink);margin:6px 0 10px;line-height:1.15}
.ho-n{display:block;font-size:14.5px;color:var(--muted);line-height:1.6}
.ho-n b{color:var(--ink)}
.handoff .ho-go{display:inline-block;margin-top:14px;font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.05em;color:var(--brand)}
.handoff-card:hover .ho-go{text-decoration:underline}
/* homepage: thin, prominent find bar — the product, one band deep */
.hero.slim{padding:20px 0 12px}
.hero.slim .hero-top{align-items:baseline;gap:6px 14px}
.hero.slim .sub{margin:0;font-size:15px;color:var(--muted);flex-basis:100%}
@media(min-width:900px){.hero.slim .sub{flex-basis:auto}}
/* Deliberately NOT sticky. .site-header is already sticky at top:0, so a
   second sticky band would pin on top of the nav — and the header's height
   is not fixed (the wrapping category bar runs ~300px on a phone), so there
   is no honest `top` value to offset by. Prominence comes from the rules. */
.findbar{background:var(--paper);border-top:2.5px solid var(--ink);border-bottom:2.5px solid var(--ink)}
.findbar-in{display:flex;align-items:center;gap:12px 16px;padding:10px 22px;flex-wrap:wrap}
.findbar .searchbar{margin:0;flex:1 1 300px;min-width:0;border-width:2px;border-radius:10px}
.findbar .searchbar input{padding:9px 13px;font-size:15px}
.findbar .vfilters{margin:0;display:flex;flex-wrap:wrap;gap:6px}
.findbar .vfilter{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.03em;padding:6px 11px;border-radius:99px;border:1.5px solid var(--line);background:transparent;color:var(--muted);cursor:pointer;white-space:nowrap;transition:all .12s}
.findbar .vfilter i{font-style:normal;opacity:.6;margin-left:4px}
.findbar .vfilter:hover{border-color:var(--ink);color:var(--ink)}
.findbar .vfilter.on{background:var(--ink);border-color:var(--ink);color:var(--paper)}
.findbar .vfilter.on i{opacity:.75}
.findbar-jump{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;letter-spacing:.05em;text-decoration:none;color:var(--brand);white-space:nowrap;margin-left:auto}
.findbar-jump:hover{text-decoration:underline}
/* homepage stream slice */
.homestream{padding:26px 0 6px}
.hs-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:0 0 16px}
.hs-head h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:clamp(22px,2.6vw,30px);letter-spacing:-.015em;margin:0}
.hs-when{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--muted)}
.hs-all{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;letter-spacing:.05em;text-decoration:none;color:var(--brand);margin-left:auto;white-space:nowrap}
.hs-all:hover{text-decoration:underline}
.verdicts-head{padding:34px 0 4px;border-top:2.5px solid var(--ink);margin-top:26px}
.verdicts-head h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:clamp(22px,2.6vw,30px);letter-spacing:-.015em;margin:0}
.verdicts-head p{margin:6px 0 0;color:var(--muted);font-size:15.5px}
/* /now/ — the stream */
.streamwrap{padding-top:18px}
.st-strip{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 14px;padding:0 0 20px;border-bottom:2.5px solid var(--ink);margin-bottom:22px;font-size:14.5px;color:var(--muted)}
.st-strip span:nth-child(2){flex:1;min-width:260px;max-width:70ch}
.st-live{font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:600;letter-spacing:.16em;color:#B3261E;border:1.5px solid #B3261E;border-radius:5px;padding:2px 7px}
.st-when{font-family:"IBM Plex Mono",monospace;font-size:11.5px}
.stream{columns:3;column-gap:20px}
@media(max-width:980px){.stream{columns:2}}
@media(max-width:620px){.stream{columns:1}}
.st-card{break-inside:avoid;-webkit-column-break-inside:avoid;page-break-inside:avoid;display:inline-block;width:100%;margin:0 0 20px;border:1.5px solid var(--line);border-radius:12px;overflow:hidden;background:var(--card);transition:border-color .12s}
.st-card:hover{border-color:var(--ink)}
.st-art{margin:0;line-height:0;background:var(--paper)}
.st-art img{width:100%;height:auto;display:block}
.st-body{padding:14px 16px 15px}
.st-tags{display:flex;flex-wrap:wrap;gap:5px;margin:0 0 8px}
.st-tag{font-family:"IBM Plex Mono",monospace;font-size:9.5px;font-weight:600;letter-spacing:.11em;color:var(--brand);border:1.5px solid var(--brand);border-radius:4px;padding:2px 6px}
.st-card h3{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:18px;line-height:1.24;letter-spacing:-.01em;margin:0 0 8px}
.st-card h3 a{color:var(--ink);text-decoration:none}
.st-card h3 a:hover{color:var(--brand)}
.st-vid{color:var(--brand);margin-right:6px;font-size:14px}
.st-sum{font-size:14px;line-height:1.55;color:var(--muted);margin:0 0 10px}
.st-meta{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0}
/* text-only items still have to carry the page, so they lead with type */
.st-card.notart .st-body{padding:18px 18px 17px;border-left:4px solid var(--ink)}
.st-card.notart h3{font-size:21px}
.st-card.notart .st-sum{font-size:14.5px;color:var(--ink)}
.st-card.lead{border-color:var(--ink);border-width:2.5px}
.st-card.lead h3{font-size:25px}
.st-card.lead .st-sum{font-size:15px}
.st-foot{max-width:70ch;margin:14px 0 54px;font-size:12.5px;line-height:1.6;color:var(--muted);font-style:italic}
/* house ad — sister studio */
#hoad{position:fixed;left:0;right:0;bottom:0;z-index:900;display:flex;align-items:center;gap:12px;padding:10px 16px;background:var(--card);color:var(--ink);border-top:2px solid var(--ink);box-shadow:0 -2px 14px rgba(0,0,0,.07);transform:translateY(100%);transition:transform .45s cubic-bezier(.16,1,.3,1);font-size:14px}
#hoad.in{transform:none}
#hoad .ho-lbl{font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
#hoad .ho-msg{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--ink);text-decoration:none;font-weight:600}
#hoad .ho-msg:hover{text-decoration:underline}
#hoad .ho-pitch{font-weight:400;color:var(--muted)}
#hoad .ho-go{flex-shrink:0;border:1.5px solid var(--brand);color:var(--brand);border-radius:999px;padding:4px 15px;font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;letter-spacing:.05em;text-decoration:none}
#hoad .ho-go:hover{background:var(--brand);color:var(--paper)}
#hoad .ho-x{background:none;border:0;color:var(--muted);font-size:21px;line-height:1;cursor:pointer;padding:0 2px;flex-shrink:0}
#hoad .ho-x:hover{color:var(--ink)}
@media(max-width:620px){#hoad .ho-go{display:none}#hoad .ho-pitch{display:none}}
/* "was this verdict right?" */
.vfb{margin:34px 0 0;border-top:1px solid var(--line);padding:26px 0 0}
.vfb h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;margin:0 0 6px}
.vfb .vfb-lede{color:var(--muted);font-size:14.5px;line-height:1.6;margin:0 0 14px;max-width:56ch}
.vfb-opts{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.vfb-opt{display:inline-flex;align-items:center;gap:7px;border:1.5px solid var(--line);border-radius:8px;padding:8px 13px;font-size:14px;cursor:pointer;transition:border-color .12s,background .12s}
.vfb-opt:hover{border-color:var(--brand)}
.vfb-opt input{accent-color:var(--brand);margin:0}
.vfb-opt:has(input:checked){border-color:var(--ink);background:var(--card)}
.vfb textarea,.vfb input[type=email]{display:block;width:100%;max-width:520px;border:1.5px solid var(--line);border-radius:8px;padding:10px 12px;font:400 15px "Public Sans",sans-serif;color:var(--ink);background:var(--paper);margin:0 0 9px}
.vfb textarea{height:64px;resize:vertical}
.vfb textarea:focus,.vfb input[type=email]:focus{outline:2px solid var(--brand);border-color:var(--brand)}
.vfb button{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:13.5px;letter-spacing:.06em;border:2.5px solid var(--ink);border-radius:10px;padding:10px 22px;background:var(--ink);color:var(--paper);cursor:pointer;transition:background .12s,border-color .12s}
.vfb button:hover{background:var(--brand);border-color:var(--brand)}
.vfb button:disabled{opacity:.55;cursor:default}
.vfb .vfb-err{color:#C0392B;font-size:14px;font-weight:600;margin:10px 0 0}
.vfb .vfb-ty{color:var(--brand);font-size:15px;font-weight:600;margin:0;max-width:56ch;line-height:1.55}
/* free in real life */
.irl-wrap{max-width:720px}
.irl-wrap section{padding:0 0 14px}
.irl-h{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:25px;margin:34px 0 6px}
.irl-blurb{color:var(--muted);font-size:15.5px;line-height:1.6;margin:0 0 18px;max-width:62ch}
.legit{margin:26px 0 0;border:2px solid var(--ink);border-radius:12px;padding:18px 20px;background:var(--card)}
.legit h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;margin:0 0 12px;color:var(--ink)}
.legit h2::before{content:"🛡 "}
.legit .lg-row{display:flex;gap:10px;margin:0 0 8px;font-size:14.5px;line-height:1.5}
.legit .lg-row b{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);flex-shrink:0;width:110px;padding-top:2px}
.legit .lg-row.flag{border-top:1px solid var(--line);padding-top:10px;margin-top:12px}
.sechead{font-family:"Bricolage Grotesque",sans-serif;font-size:22px;font-weight:700;margin:0 0 4px;letter-spacing:-.01em}
.seclede{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--muted);margin:0 0 18px;letter-spacing:.04em}
.cmp-title{font-family:"Bricolage Grotesque",sans-serif;font-size:17px;font-weight:700;margin:0 0 4px;letter-spacing:-.01em}
.fav.spr{display:inline-block;background-image:url('/brand-sprite.png');background-repeat:no-repeat;background-size:calc(var(--n) * 28px) 28px;background-position:calc(var(--i) * -28px) 0;flex-shrink:0}
.fav.big.spr{background-size:calc(var(--n) * 46px) 46px;background-position:calc(var(--i) * -46px) 0}
.catch{margin:26px 0 0}
.catch h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:21px;margin-bottom:8px}
.checked{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--muted);margin:26px 0 0}
.visit{display:inline-block;margin:26px 0 0;font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:14px;letter-spacing:.06em;text-decoration:none;border:2.5px solid var(--ink);border-radius:10px;padding:12px 20px;background:var(--ink);color:var(--paper);transition:background .12s ease,color .12s ease}
.visit:hover{background:var(--brand);border-color:var(--brand)}
.related{padding:10px 0 50px;border-top:1px solid var(--line);margin-top:44px}
.related h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);padding:22px 0 16px}
/* category + method pages */
.pagehead{padding-top:56px;padding-bottom:8px}
.pagehead h1{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:clamp(34px,5.5vw,56px);letter-spacing:-.015em;line-height:1.02}
.pagehead p{margin:14px 0 22px;color:var(--muted);font-size:17.5px;max-width:58ch}
.prose{max-width:680px;padding:8px 0 60px}
.prose h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:23px;margin:34px 0 10px}
.prose p{margin:0 0 16px}
.vdef{display:flex;gap:14px;align-items:baseline;margin:0 0 14px}
.vdef .pill{flex-shrink:0}
.vdef p{margin:0;color:var(--muted);font-size:15.5px}
/* footer */
footer{border-top:2.5px solid var(--ink);margin-top:30px}
.foot-in{padding:30px 0 44px;display:flex;flex-wrap:wrap;gap:14px 30px;justify-content:space-between;align-items:baseline;font-size:14px;color:var(--muted)}
.foot-in a{color:var(--muted)}
.foot-in a:hover{color:var(--ink)}
:focus-visible{outline:3px solid var(--brand);outline-offset:2px;border-radius:4px}
@media(max-width:560px){.facts td.k{width:130px;white-space:normal}.hero{padding-top:20px}.stats{white-space:normal}}
/* the "n verified" badge is clipped by the search bar below this width */
@media(max-width:480px){.searchbar .kbd{display:none}}
"""

FEEDBACK_JS = """<script>
(function(){
  var f=document.getElementById('vfb');
  if(!f)return;
  f.addEventListener('submit',function(e){
    e.preventDefault();
    if(!f.querySelector('input[name=answer]:checked')){
      f.querySelector('.vfb-err').textContent='Pick one first.';
      f.querySelector('.vfb-err').style.display='block';return;
    }
    var btn=f.querySelector('button[type=submit]');
    btn.disabled=true;
    fetch(location.pathname,{method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body:new URLSearchParams(new FormData(f)).toString()})
      .then(function(r){
        if(!r.ok)throw 0;
        f.querySelector('.vfb-body').style.display='none';
        f.querySelector('.vfb-ty').style.display='block';
      })
      .catch(function(){
        var er=f.querySelector('.vfb-err');
        er.textContent="Couldn't send just now — email hello@veri-free.com instead.";
        er.style.display='block';btn.disabled=false;
      });
  });
})();
</script>"""


def feedback_form(l, vlabel):
    """"Was this verdict right?" — Netlify form, one per listing, moderated by hand."""
    opts = "".join(
        f'<label class="vfb-opt"><input type="radio" name="answer" value="{v}"><span>{t}</span></label>'
        for v, t in [("right", "Yes, that matches"),
                     ("changed", "It's changed since you checked"),
                     ("wrong", "No — you've got it wrong")])
    return (f'<form class="vfb" id="vfb" name="verdict-feedback" method="POST" '
            f'action="/submit/thanks/" data-netlify="true" netlify-honeypot="bot-field">'
            f'<input type="hidden" name="form-name" value="verdict-feedback">'
            f'<input type="hidden" name="listing" value="{esc(l["name"])}">'
            f'<input type="hidden" name="slug" value="{esc(l["slug"])}">'
            f'<input type="hidden" name="verdict" value="{esc(vlabel)}">'
            f'<p style="display:none"><label>Leave blank <input name="bot-field"></label></p>'
            f'<div class="vfb-body"><h2>Was this verdict right?</h2>'
            f'<p class="vfb-lede">Free tiers change without notice. If you have just used it, '
            f'you know something we don\'t.</p>'
            f'<div class="vfb-opts">{opts}</div>'
            f'<textarea name="note" placeholder="What changed? (optional, but it\'s what makes this useful)"></textarea>'
            f'<input type="email" name="email" placeholder="Email, only if you want a reply (optional)">'
            f'<button type="submit">Send</button>'
            f'<p class="vfb-err" style="display:none"></p></div>'
            f'<p class="vfb-ty" style="display:none">Thank you — that goes to a human, and if it '
            f'checks out the page gets re-verified.</p></form>')


import datetime as _dt


def ago(iso):
    """Absolute date, wrapped in <time> so the browser can age it.

    This used to return "2h ago" computed at BUILD time, which then froze into
    static HTML. Between deploys the page kept insisting a week-old story was
    an hour old — a live page is the one place a relative timestamp cannot be
    baked. The absolute date is always true; feed.js turns it into "3d ago" at
    view time, and without JS the reader still sees a real date.
    """
    if not iso:
        return ""
    try:
        d = _dt.datetime.fromisoformat(iso)
    except ValueError:
        return ""
    if not d.tzinfo:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return (f'<time class="ts" datetime="{esc(d.isoformat())}">'
            f'{d.strftime("%b %-d") if os.name != "nt" else d.strftime("%b %d").replace(" 0", " ")}'
            f'</time>')


# Names that would match constantly on unrelated stories, or whose listing is
# about something narrower than the word. Matching these would send a reader to
# a verdict that has nothing to do with what they just read.
MATCH_SKIP = {"Claude", "Wave Accounting", "Signal", "Plex", "Etsy", "Indeed",
              "Meetup (free events)", "Eventbrite (free events)", "Free Museum Days",
              "Free Community Events (Library, Parks & Rec)", "The Old Reader"}

# Story language -> the listing it actually concerns.
MATCH_ALIAS = {
    "OpenAI": "ChatGPT", "Twitter": "X (Twitter) API", "Prime Video": "Amazon Prime Video",
    "Disney Plus": "Disney+", "Google Assistant": "Google Drive & Gmail",
    "AnkiDroid": "Anki", "AnkiMobile": "Anki", "Wayback Machine": "Internet Archive",
    "Plex Pass": "Plex", "Amazon Kindle": "Kindle Unlimited",
}


def build_match_index(listings):
    """-> [(compiled_pattern, listing)], longest name first so the most
    specific listing wins ('Reddit API' before 'Reddit')."""
    import re as _re
    by = {l["name"]: l for l in listings}
    pairs = []
    for l in listings:
        if l["name"] in MATCH_SKIP:
            continue
        base = _re.sub(r"\s*\(.*?\)", "", l["name"]).strip()
        if len(base) < 5:
            continue
        pairs.append((base, l))
    for alias, target in MATCH_ALIAS.items():
        if target in by:
            pairs.append((alias, by[target]))
    # Longest name first so the most specific listing wins ("Reddit API" before
    # "Reddit"), then alphabetically — without the second key, equal-length
    # names tie-break on list order and the same story matches a different
    # listing depending on how the listings happen to be sorted that build.
    pairs.sort(key=lambda p: (-len(p[0]), p[0].lower()))
    return [(_re.compile(r"\b" + _re.escape(n) + r"\b", _re.I), l) for n, l in pairs]


def match_listing(it, index):
    hay = it.get("title", "") + " " + it.get("summary", "")
    for pat, l in index:
        if pat.search(hay):
            return l
    return None


VERIFY_STALE_MONTHS = 6


def verified_line(l, site_checked):
    """The date a listing's facts were last checked, not the date the file was
    rebuilt. Peacock carried a site-wide "July 2026" while stating something
    that stopped being true in January 2023 — a global date cannot catch that,
    because it moves whether or not anyone looked.
    """
    v = l.get("verified")
    if not v:
        return (f'<span class="ck-date">Last checked: {esc(site_checked)}</span>'
                f'<span class="ck-flag" title="No individual re-verification recorded for this '
                f'listing — the date shown is the site-wide pass.">site-wide date</span>')
    try:
        y, m = (int(x) for x in v.split("-")[:2])
    except ValueError:
        return f'<span class="ck-date">Last checked: {esc(v)}</span>'
    today = _dt.date.today()
    months = (today.year - y) * 12 + (today.month - m)
    label = _dt.date(y, m, 1).strftime("%B %Y")
    stale = ('<span class="ck-flag due">re-verify due</span>'
             if months >= VERIFY_STALE_MONTHS else "")
    return f'<span class="ck-date fresh">Checked: {esc(label)}</span>{stale}'


def stream_card(it, lead=False, match=None):
    img = ""
    if it.get("image"):
        img = (f'<div class="st-art"><img src="{esc(it["image"])}" alt="" loading="lazy" '
               f'referrerpolicy="no-referrer"></div>')
    tags = "".join(f'<span class="st-tag">{esc(t)}</span>' for t in it.get("tags", []))
    vid = '<span class="st-vid">▶</span>' if it.get("kind") == "video" else ""
    cls = "st-card lead" if lead else "st-card"
    if not it.get("image"):
        cls += " notart"
    # The whole reason a news feed belongs on this site: when a story is about
    # something we've graded, the card is a door into our verdict rather than
    # only a door out to the publisher.
    ours = ""
    if match:
        label = VERDICTS[match["verdict"]][0]
        ours = (f'<a class="st-ours" href="/{esc(match["slug"])}/">'
                f'<span class="so-lbl">We checked this</span>'
                f'<span class="so-name">{esc(match["name"])}</span>'
                f'<span class="so-verdict v-{match["verdict"]}">{esc(label)}</span></a>')
    return (f'<article class="{cls}">{img}'
            f'<div class="st-body"><div class="st-tags">{tags}</div>'
            f'<h3><a href="{esc(it["url"])}" target="_blank" rel="noopener nofollow">{vid}'
            f'{esc(it["title"])}</a></h3>'
            f'<p class="st-sum">{esc(it.get("summary", ""))}</p>'
            f'{ours}'
            f'<p class="st-meta">{esc(it["source"])} · {ago(it.get("date"))}</p>'
            f'</div></article>')


def deal_card(d, cta="Go to offer →"):
    """Shared card for /deals/, /coupons/ and /free-in-real-life/."""
    st = d.get("status", "verified")
    badge_cls = "verified" if st == "verified" else "seasonal" if st == "seasonal" else "expired"
    # Same-publisher disclosure goes ABOVE the pitch. On listing pages it is
    # already its own line; here it used to sit as prose at the foot of the
    # caveat, under the sales copy — which is the one place a disclosure is
    # worth nothing.
    disc = (f'<p class="ddisc">{esc(d["disclosure"])}</p>') if d.get("disclosure") else ""
    code = ""
    if d.get("code"):
        code = (f'<div class="dcode" data-code="{esc(d["code"])}" role="button" tabindex="0" '
                f'aria-label="Copy code {esc(d["code"])}">'
                f'<span class="dc-lbl">Code</span><span class="dc-val">{esc(d["code"])}</span>'
                f'<span class="dc-act">Copy</span></div>')
    return (f'<div class="deal">'
            f'<div class="dtop">{favicon(d["url"], override=d.get("favicon_url"))}<h3>{esc(d["name"])}</h3>'
            f'<span class="dbadge {badge_cls}">{st.upper()}</span></div>'
            f'{disc}'
            f'<p class="dtype">{esc(d["type"])}</p>'
            f'<p>{esc(d["summary"])}</p>'
            f'{code}'
            f'<p><b>Who qualifies:</b> {esc(d["who"])}</p>'
            f'<p><b>How to get it:</b> {esc(d["how"])}</p>'
            f'<p class="dlabel">What it\'s worth</p><p class="dworth">{esc(d["worth"])}</p>'
            f'<p class="dcav">{esc(d["caveat"])}</p>'
            f'<a class="dlink" href="{esc(d["url"])}" target="_blank" rel="noopener">{cta}</a>'
            f'</div>')


FEED_JS = """<script>
(function(){
  var els=document.querySelectorAll("time.ts[datetime]");
  if(!els.length)return;
  function rel(d){
    var s=(Date.now()-d.getTime())/1000;
    if(s<60)return "just now";
    if(s<3600)return Math.floor(s/60)+"m ago";
    if(s<86400)return Math.floor(s/3600)+"h ago";
    if(s<2592000)return Math.floor(s/86400)+"d ago";
    return null;                       // older than a month: keep the date
  }
  els.forEach(function(el){
    var d=new Date(el.getAttribute("datetime"));
    if(isNaN(d))return;
    el.title=d.toLocaleString();
    var r=rel(d);
    if(r)el.textContent=r;             // no match keeps the absolute date
  });
})();
</script>"""


COUPON_JS = """<script>
(function(){
  document.addEventListener('click',function(e){
    var c=e.target.closest('.dcode');
    if(!c)return;
    var code=c.getAttribute('data-code'),act=c.querySelector('.dc-act');
    function done(ok){act.textContent=ok?'Copied':'Select it';c.classList.add('copied');
      setTimeout(function(){act.textContent='Copy';c.classList.remove('copied');},1600);}
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(code).then(function(){done(true);},function(){done(false);});
    }else{
      // No clipboard API (or an insecure context) — select the text so the
      // reader can copy it themselves rather than silently doing nothing.
      var r=document.createRange();r.selectNodeContents(c.querySelector('.dc-val'));
      var s=getSelection();s.removeAllRanges();s.addRange(r);done(false);
    }
  });
  document.addEventListener('keydown',function(e){
    if((e.key==='Enter'||e.key===' ')&&e.target.classList&&e.target.classList.contains('dcode')){
      e.preventDefault();e.target.click();
    }
  });
})();
</script>"""


SAFETY_ROWS = [("Download", "download"), ("Your data", "data"),
               ("Scams to watch", "scams"), ("Account risk", "account_risk")]


def safety_box(l, checked=""):
    """"Is X safe?" — answers the safety-intent query directly, in its own section."""
    s = l.get("safety")
    if not s:
        return ""
    rows = "".join(f'<div class="sf-row"><b>{lbl}</b><span>{esc(s[k])}</span></div>'
                   for lbl, k in SAFETY_ROWS if s.get(k))
    return (f'<div class="safety" id="safe"><h2>Is {esc(l["name"])} safe?</h2>'
            f'<p class="sf-verdict">{esc(s["verdict"])}</p>{rows}'
            f'<p class="sf-src">Safety here means downloads, data practices, and scam exposure — '
            f'it is separate from the free verdict above. Checked {esc(checked)}.</p></div>')


def safety_faq(l):
    """The same answer, flattened for FAQPage schema."""
    s = l.get("safety")
    if not s:
        return None
    parts = [s["verdict"]] + [s[k] for _, k in SAFETY_ROWS if s.get(k)]
    return {"@type": "Question", "name": f"Is {l['name']} safe?",
            "acceptedAnswer": {"@type": "Answer", "text": " ".join(parts)}}


# Comparable free-tier specs. Every listing in a category answers the SAME
# questions in the SAME order, which is the only way a reader can scan across
# them. Values stay qualitative on purpose — "Daily cap", not "45 messages per
# 5 hours". Exact allowances change monthly and would make the whole grid a
# lie within a release or two; the shape of the limit doesn't.
SPEC_SCHEMA = {
    "ai-tools": ["Card required", "Usage ceiling", "Model quality", "File uploads",
                 "Image generation", "Web access", "Commercial use", "Runs offline",
                 "Trains on your input"],
    "data-apis": ["Card required", "Free ceiling", "API key needed", "Bulk download",
                  "Commercial use", "Self-hostable", "Sleeps when idle"],
    "learning": ["Card required", "Full course content", "Graded work", "Certificate",
                 "Access expires", "Ads"],
    # Business holds CRMs, schedulers, builders and one-off free tools, so the
    # columns have to be answerable by a QR generator and a CRM alike. These
    # are the four things that actually decide whether business software is
    # free to you: a clock, someone else's logo on your work, whether you can
    # take the work with you, and whether you may sell what you make.
    "business": ["Card required", "Free plan or trial", "Their branding",
                 "Export your work", "Commercial use", "Time limit"],
    # Not "Simultaneous streams" — the category holds Reddit and two media
    # servers, and a column three members cannot answer is a hole in the grid.
    "entertainment": ["Card required", "Account needed", "Ads", "Free catalogue",
                      "Offline downloads"],
    "books-reading": ["Card required", "What you need", "Catalogue", "Waitlists",
                      "Keep after leaving", "Offline reading"],
}

# Values worth colouring: green reads as "you get this", amber as "with a
# string attached", red as "you don't".
SPEC_GOOD = {"No", "Unlimited", "Yes", "Allowed", "None", "Current flagship",
             "Full", "Everything", "Your own terms", "No ads", "Never"}
SPEC_BAD = {"Yes — required", "Not allowed", "None", "Paid only", "No", "Trial only"}


# Capability questions, where a "No" is scope rather than stinginess.
# Claude not generating images isn't something withheld from the free tier,
# so colouring it red would misread the whole grid.
CAPABILITY = {"File uploads", "Image generation", "Web access", "Runs offline",
              "Export your work",
              "Bulk download", "Self-hostable", "Downloads", "Offline reading",
              "Graded work", "Certificate", "Simultaneous streams"}


def spec_tone(label, value):
    """Green/amber/red by meaning, which flips depending on the question asked."""
    inverted = label in ("Card required", "Ads", "Access expires", "Waitlists",
                         "Trains on your input", "Sleeps when idle", "API key needed",
                         "Their branding", "Time limit")
    v = value.split(" —")[0].strip()
    if label in CAPABILITY:
        # "Paid only" is a real cost, not mere absence, so it still earns amber.
        if v in ("Paid only", "Partial", "Sometimes"):
            return "mid"
        if v in ("Yes", "Free", "Only this", "Full", "Everything",
                 "Unlimited", "Your own terms"):
            return "good"
        return "off"
    # Always good regardless of the question — putting these in the No/None
    # bucket made "Free plan" render red, because that bucket flips on
    # inverted labels and "Free plan or trial" is not an inverted question.
    if v in ("Free plan", "No account needed"):
        return "good"
    if v in ("Trial only", "Trial clock", "On free tier"):
        return "bad"
    if v in ("No", "None", "Never", "No ads"):
        return "good" if inverted else "bad"
    if v in ("Yes", "Yes — required", "Always"):
        return "bad" if inverted else "good"
    if v in ("Unlimited", "Allowed", "Full", "Everything", "Current flagship",
             "Your own terms", "Open weights"):
        return "good"
    if v in ("Not allowed", "Paid only", "Trial only", "Older only"):
        return "bad"
    return "mid"


def faq_pairs(l):
    """Question/answer pairs built from fields every listing already has.

    These are the query families the pages never answered in words: people
    search "does X need a credit card", "X free plan limits" and "free
    alternative to X" far more than they search the phrasing we happened to
    use. Rendered visibly as well as in schema — Google restricted FAQ rich
    results, so the value is the page actually containing the answer, not the
    markup.
    """
    n = l["name"]
    out = [(f"Is {n} actually free?", l["short"])]
    if l.get("safety"):
        s = l["safety"]
        out.append((f"Is {n} safe?", " ".join(
            [s["verdict"]] + [s[k] for _, k in SAFETY_ROWS if s.get(k)])))
    card = (l.get("card") or "").strip()
    if card:
        neg = card.lower().startswith(("no", "—"))
        out.append((f"Does {n} require a credit card?",
                    (f"No — {n} does not ask for a card to use the free version. " if neg
                     else f"Yes. {n} asks for a card: {card}. ")
                    + f"Auto-billing: {l.get('autobill') or '—'}."))
    if l.get("limits"):
        out.append((f"What are the limits of {n}'s free plan?",
                    f"{l['limits']}. {l.get('catch','')}".strip()))
    if l.get("free_alternatives"):
        alts = ", ".join(a["name"] for a in l["free_alternatives"])
        out.append((f"What is a free alternative to {n}?",
                    f"{alts}. " + " ".join(f"{a['name']}: {a['why']}"
                                           for a in l["free_alternatives"])))
    if l.get("smart_moves"):
        out.append((f"How do I use {n} without paying?",
                    " ".join(l["smart_moves"])))
    if l.get("realcost"):
        out.append((f"What does {n} really cost?", l["realcost"]))
        # "why is blender free", "warum ist obs kostenlos", "why is hubspot crm
        # free" — a family with real volume that no page answered as a
        # question, even though realcost is exactly the answer.
        out.append((f"Why is {n} free?",
                    f"{l['realcost']} {l.get('worth', '')}".strip()))
    # "is trello still free", "is coursera not free anymore" — people asking
    # whether a tier they remember survived. That is this site's whole subject.
    when = l.get("verified") or ""
    asof = (_dt.date(int(when.split("-")[0]), int(when.split("-")[1]), 1).strftime("%B %Y")
            if re.match(r"^\d{4}-\d{2}", when) else None)
    stamp = f"As of our {asof} check" if asof else "As of our last check"
    v = l["verdict"]
    if v in ("truly", "forever"):
        still = f"{stamp}, yes. {l['short']}"
    elif v == "freeish":
        still = f"{stamp}, partly — and the free tier is squeezed. {l['short']}"
    else:
        still = f"{stamp}, no. {l['short']}"
    out.append((f"Is {n} still free?",
                still + " Free tiers change without notice, which is why every "
                        "page here carries the date it was checked."))
    return out


def faq_block(l):
    pairs = faq_pairs(l)[1:]          # the first is already the page's answer
    if not pairs:
        return ""
    items = "".join(
        f'<details class="faq-q"><summary>{esc(q)}</summary>'
        f'<div class="faq-a">{esc(a)}</div></details>' for q, a in pairs)
    return f'<div class="faqs"><h2>Common questions</h2>{items}</div>'


def spec_block(l):
    schema = SPEC_SCHEMA.get(l["category"])
    spec = l.get("free_spec")
    if not schema or not spec:
        return ""
    rows = ""
    for label in schema:
        if label not in spec:
            continue
        v = spec[label]
        rows += (f'<tr><td class="k">{esc(label)}</td>'
                 f'<td><span class="sv {spec_tone(label, v)}">{esc(v)}</span></td></tr>')
    if not rows:
        return ""
    ctitle = CATS[l["category"]][0]
    return (f'<div class="freespec"><h2>What the free tier actually gives you</h2>'
            f'<table>{rows}</table>'
            f'<p class="fs-note">Same questions, same order, for every listing in '
            f'<a href="/{l["category"]}/#compare">{esc(ctitle)}</a> — so you can compare them '
            f'side by side. Deliberately no exact allowances: those change monthly, '
            f'the shape of the limit doesn\'t.</p></div>')


def spec_table(cat, rows):
    """The payoff: every listing in the category, one grid."""
    schema = SPEC_SCHEMA.get(cat)
    have = [l for l in rows if l.get("free_spec")]
    if not schema or len(have) < 2:
        return ""
    head = "".join(f"<th>{esc(h)}</th>" for h in schema)
    body = ""
    for l in have:
        cells = ""
        for label in schema:
            v = l["free_spec"].get(label, "—")
            cells += f'<td><span class="sv {spec_tone(label, v)}">{esc(v)}</span></td>'
        body += (f'<tr><th scope="row"><a href="/{esc(l["slug"])}/">{esc(l["name"])}</a></th>'
                 f'{cells}</tr>')
    return (f'<section class="cmp" id="compare"><h2>Compare the free tiers</h2>'
            f'<p class="cmp-lede">Every {esc(CATS[cat][0]).lower()} listing, answering the same '
            f'questions. Values are deliberately qualitative — exact allowances change too '
            f'often to publish honestly.</p>'
            f'<div class="cmp-scroll"><table class="cmp-table">'
            f'<thead><tr><th scope="col">Service</th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div></section>')


def ratings_row(l):
    rows = l.get("external_ratings")
    if not rows:
        return ""
    chips = ""
    for r in rows:
        n = f'<span class="er-n">{esc(r["count"])}</span>' if r.get("count") else ""
        chips += (f'<a class="ext-rat" href="{esc(r["url"])}" target="_blank" rel="noopener">'
                  f'{esc(r["source"])} <span class="er-score">{esc(r["score"])}</span>{n}</a>')
    return (f'<div class="ext-ratings"><span class="er-lbl">Ratings elsewhere</span>{chips}'
            f'<span class="er-note">Live scores from the sources named — not ours. Store counts rounded.</span></div>')


def sentiment_box(l):
    s = l.get("sentiment")
    if not s:
        return ""
    return (f'<div class="sent"><h2>What users actually say</h2>'
            f'<p class="sn-split">{esc(s["split"])}</p>'
            f'<div class="sn-row"><b>What they praise</b>{esc(s["praised"])}</div>'
            f'<div class="sn-row"><b>What they complain about</b>{esc(s["complained"])}</div>'
            f'<p class="sn-take">{esc(s["takeaway"])}</p>'
            f'<p class="sn-src">Our reading of the public review record — patterns, not quotes. Scores link to their sources above.</p>'
            f'</div>')

def legit_box(l):
    lg = l.get("legitimacy")
    if not lg:
        return ""
    rows = ""
    for lbl, k in [("Company", "company"), ("Pays via", "pays_via"), ("Track record", "track_record")]:
        rows += f'<div class="lg-row"><b>{lbl}</b><span>{esc(lg[k])}</span></div>'
    rows += f'<div class="lg-row flag"><b>Red flags</b><span>{esc(lg["red_flags"])}</span></div>'
    return f'<div class="legit"><h2>Legitimacy check</h2>{rows}</div>'

def pill(vkey, tip=True, lang="en"):
    label, color, bg, d = VERDICTS[vkey]
    if lang != "en":
        label, d = L10N[lang]["verdicts"][vkey]
    t = f' data-tip="{esc(d)}"' if tip else ''
    return f'<span class="pill"{t} style="color:{color};border-color:{color};background:{bg}">{label}</span>'

def stamp(vkey, animate=False):
    label, color, bg, _ = VERDICTS[vkey]
    cls = "stamp animate" if animate else "stamp"
    return f'<span class="{cls}" style="color:{color};border-color:{color};background:{bg}">{label}</span>'

def score_color(pct):
    return "#0E7B47" if pct >= 85 else "#0A6E8A" if pct >= 60 else "#A05E03" if pct >= 40 else "#C2410C" if pct >= 15 else "#B3261E"

ICONS = {
    "software-tools": '<img src="/icons/software-tools.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "ai-tools": '<img src="/icons/ai-tools.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "business": '<img src="/icons/business.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "learning": '<img src="/icons/learning.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "entertainment": '<img src="/icons/entertainment.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "books-reading": '<img src="/icons/books-reading.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "money-finance": '<img src="/icons/money-finance.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "earn": '<img src="/icons/earn.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "reviews": '<img src="/icons/reviews.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "data-apis": '<img src="/icons/data-apis.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
    "leisure": '<img src="/icons/leisure.png" alt="" class="caticon" width="16" height="16" loading="lazy">',
}

def favicon(url, big=False, override=None):
    from urllib.parse import urlparse
    dom = urlparse(override or url).netloc
    cls = "fav big" if big else "fav"
    if dom in SPRITE_INDEX:
        # one shared image for every brand mark — no per-icon request
        return f'<span class="{cls} spr" style="--i:{SPRITE_INDEX[dom]}" role="presentation"></span>'
    wh = 'width="46" height="46"' if big else 'width="28" height="28"'
    return (f'<img class="{cls}" {wh} src="https://www.google.com/s2/favicons?domain={dom}&amp;sz=128" '
            f'alt="" loading="lazy" referrerpolicy="no-referrer">')

def lang_switcher(current="en"):
    items = ""
    for lg in ["en"] + EXTRA_LANGS:
        href = "/" if lg == "en" else "/" + lg + "/"
        cur = ' class="cur"' if lg == current else ""
        items += f'<a href="{href}"{cur}>{LANG_NAMES[lg]}</a>'
    return (f'<div class="dropdown langdd"><a href="#" onclick="return false">\U0001F310 {current.upper()}</a>'
            f'<div class="dropdown-menu right"><div class="dd-inner">{items}</div></div></div>')

# Hover alone left the language switcher unusable on touch, where there is no
# hover at all and the trigger carried onclick="return false". Tap now opens
# it; a second tap, an outside click, or Escape closes it. Links with a real
# destination still navigate on the second interaction rather than being
# swallowed.
NAV_JS = """<script>
(function(){
  var dds=[].slice.call(document.querySelectorAll('.dropdown'));
  if(!dds.length)return;
  var fine=!(window.matchMedia&&window.matchMedia('(hover:none)').matches);
  var timer=null;

  function setOpen(d,on){
    d.classList.toggle('open',on);
    var a=d.querySelector(':scope > a');
    if(a)a.setAttribute('aria-expanded',on?'true':'false');
  }
  function closeAll(except){
    clearTimeout(timer);
    dds.forEach(function(d){if(d!==except)setOpen(d,false);});
  }

  dds.forEach(function(d){
    var a=d.querySelector(':scope > a');
    if(!a)return;
    a.setAttribute('aria-haspopup','true');
    a.setAttribute('aria-expanded','false');

    if(fine){
      // Opening on enter and closing on a timer is what makes the diagonal
      // move from a narrow trigger to a wide menu survivable.
      d.addEventListener('mouseenter',function(){clearTimeout(timer);closeAll(d);setOpen(d,true);});
      d.addEventListener('mouseleave',function(){
        clearTimeout(timer);
        timer=setTimeout(function(){setOpen(d,false);},320);
      });
    }

    a.addEventListener('click',function(e){
      var href=a.getAttribute('href')||'';
      var open=d.classList.contains('open');
      if(href==='#'||href===''||(!fine&&!open)){
        e.preventDefault();
        if(open){closeAll(null);}else{closeAll(d);setOpen(d,true);}
      }
    });

    // Keyboard: opening on focus, closing when focus leaves the whole group.
    d.addEventListener('focusin',function(){clearTimeout(timer);closeAll(d);setOpen(d,true);});
    d.addEventListener('focusout',function(){
      setTimeout(function(){
        if(!d.contains(document.activeElement))setOpen(d,false);
      },0);
    });
  });

  document.addEventListener('click',function(e){
    if(!e.target.closest('.dropdown'))closeAll(null);
  });
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'){closeAll(null);if(document.activeElement)document.activeElement.blur();}
  });
})();
</script>"""


# House ad for the sister studio. Rendered natively rather than via the shared
# promo-bar.js so it needs no third-party script and no CSP loosening — the
# existing policy already permits inline script and dreamsitedesign.com.
# Same behaviour as the network bar: once per session, dismissible, remembered
# for 7 days, and it never runs on the pages about DreamSite itself.
HOUSE_AD = """<div id="hoad" hidden>
<span class="ho-lbl">From the studio behind this site</span>
<a class="ho-msg" href="https://dreamsitedesign.com/?ref=veri-free" rel="noopener">dreamsitedesign.com <span class="ho-pitch">— websites built to be found by Google and AI</span></a>
<a class="ho-go" href="https://dreamsitedesign.com/?ref=veri-free" rel="noopener">Visit</a>
<button class="ho-x" type="button" aria-label="Dismiss">&times;</button>
</div>
<script>
(function(){
  var p=location.pathname;
  if(p.indexOf('dreamsite')>-1||p.indexOf('checkmysite')>-1)return;
  try{
    var off=parseInt(localStorage.getItem('vfhoad:off')||'0',10);
    if(off&&Date.now()-off<6048e5)return;
    if(sessionStorage.getItem('vfhoad:seen'))return;
    sessionStorage.setItem('vfhoad:seen','1');
  }catch(e){}
  var bar=document.getElementById('hoad');
  if(!bar)return;
  bar.hidden=false;
  // setTimeout, not rAF: rAF never fires in a backgrounded or non-compositing
  // tab, which would leave the bar parked off-screen at translateY(100%).
  setTimeout(function(){bar.classList.add('in');},60);
  bar.querySelector('.ho-x').addEventListener('click',function(){
    try{localStorage.setItem('vfhoad:off',String(Date.now()));}catch(e){}
    bar.remove();
  });
})();
</script>"""


def page(title, desc, path, body, extra_head="", lang="en"):
    canonical = f"{DOMAIN}{path}"
    langbase = "" if lang == "en" else f' data-langbase="/{lang}"'
    return f"""<!DOCTYPE html>
<html lang="{HTML_LANG.get(lang, 'en')}"{langbase}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/og.png">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{FONTS}
<style>{CSS}</style>
{extra_head}
</head>
<body>
<!--NAV-->
{body}
<footer><div class="wrap foot-in">
<span>© 2026 Verified Free. Verified Free — we check so you don't get billed.</span>
<span><a href="/all/">Everything checked</a> · <a href="/methodology/">How we verify</a> · <a href="/deals/">Deals</a> · <a href="/coupons/">Coupons</a> · <a href="/free-consultations/">Consultations</a> · <a href="/free-in-real-life/">Free in Real Life</a> · <a href="/compare/">Compare</a> · <a href="/changelog/">What changed</a> · <a href="/when-to-buy/">When to buy</a> · <a href="/submit/">For businesses</a> · <a href="mailto:hello@veri-free.com">Contact</a> · <a href="/privacy/">Privacy</a></span>
</div></footer>
{NAV_JS}
{COUPON_JS}
{FEED_JS}
{HOUSE_AD}
<script
  src="https://dreamsitedesign.com/credit.js"
  data-site="verifree"
  defer></script>
<script>
(function(){{
  function strip(){{
    document.querySelectorAll('a[href*="analytics"]').forEach(function(a){{
      var sep = a.previousSibling;
      if (sep && sep.nodeType === 3 && /^[\\s\\u00b7|\\u2022\\-\\u2013\\u2014]*$/.test(sep.textContent)) sep.remove();
      else if (sep && sep.nodeType === 1 && /^[\\s\\u00b7|\\u2022\\-\\u2013\\u2014]*$/.test(sep.textContent||'')) sep.remove();
      a.remove();
    }});
  }}
  strip();
  var n = 0, t = setInterval(function(){{ strip(); if (++n > 25) clearInterval(t); }}, 100);
  window.addEventListener('load', strip);
}})();
</script>
<script>

function updateAllChip(){{
  var pills=document.querySelectorAll('.catbar .pill-toggle[data-cat]');
  var on=0;pills.forEach(function(p){{if(p.classList.contains('on'))on++}});
  var a=document.getElementById('catAll');
  if(!a)return;
  var allOn=(on===pills.length);
  a.classList.toggle('on',allOn);
  a.classList.toggle('none',on===0);
  // The chip is a button, so label it with what a click DOES rather than with
  // what is selected. Saying "All" while a click cleared everything was the
  // illogical part. The count carries the state instead.
  var lbl=a.querySelector('.pl'), cnt=a.querySelector('.pc');
  // Off the directory the chip is a doorway, not a toggle, so it keeps saying
  // "All" — offering to clear a selection that isn't on screen would be a lie.
  if(lbl)lbl.textContent=(!hasGrid())?(a.getAttribute('data-all')||'All')
        :(allOn?(a.getAttribute('data-none')||'None'):(a.getAttribute('data-all')||'All'));
  // Only meaningful where the grid exists. Elsewhere the server-rendered
  // total stands, rather than counting zero cards and reporting "None 0".
  if(cnt&&document.querySelector('.grid .card')){{
    var shown=0;
    document.querySelectorAll('.grid .card').forEach(function(c){{
      if(c.offsetParent!==null)shown++;
    }});
    cnt.textContent=shown;
  }}
  a.setAttribute('title',allOn?(a.getAttribute('data-tip-on')||''):(a.getAttribute('data-tip-off')||''));
  a.setAttribute('aria-pressed',allOn?'true':'false');
}}
document.addEventListener('keydown',function(e){{
  if(e.target&&e.target.id==='catAll'&&(e.key==='Enter'||e.key===' ')){{
    e.preventDefault();toggleAll();
  }}
}});
function noneCats(){{
  document.querySelectorAll('.catbar .pill-toggle[data-cat]').forEach(function(p){{p.classList.remove('on')}});
  saveCats();applyCats();updateAllChip();
}}
function resetCats(){{
  document.querySelectorAll('.catbar .pill-toggle[data-cat]').forEach(function(p){{p.classList.add('on')}});
  saveCats();applyCats();updateAllChip();
}}
function hasGrid(){{return !!document.querySelector('[data-section][data-cat]')}}
function toggleAll(){{
  if(!hasGrid()){{
    window.location=(document.documentElement.getAttribute('data-langbase')||'')+'/all/';
    return;
  }}
  var pills=document.querySelectorAll('.catbar .pill-toggle[data-cat]');
  var allOn=true;pills.forEach(function(p){{if(!p.classList.contains('on'))allOn=false}});
  if(allOn)noneCats();else resetCats();
}}
function toggleCat(el){{
  if(!document.querySelector('[data-section][data-cat]')){{
    window.location=(document.documentElement.getAttribute('data-langbase')||'')+'/'+el.getAttribute('data-cat')+'/';
    return;
  }}
  el.classList.toggle('on');
  saveCats();applyCats();updateAllChip();
}}
(function(){{
  var KEY='vf_cats';
  function getSaved(){{try{{var v=document.cookie.match('(^|;)\\s*'+KEY+'=([^;]*)');return v?JSON.parse(decodeURIComponent(v[2])):null}}catch(e){{return null}}}}
  window.saveCats=function(){{
    var active=[];
    document.querySelectorAll('.catbar .pill-toggle[data-cat]').forEach(function(p){{if(p.classList.contains('on'))active.push(p.getAttribute('data-cat'))}});
    var all=document.querySelectorAll('.catbar .pill-toggle[data-cat]').length;
    // Never persist an empty selection. "None" is a momentary action — a way
    // to clear before picking one or two — and nobody's standing preference is
    // "show me nothing". Storing [] blanked every page on the site until the
    // visitor happened to click All again, with no clue why.
    if(!active.length){{
      document.cookie=KEY+'=;path=/;max-age=0;SameSite=Lax';
      return;
    }}
    var val=active.length===all?null:active;
    document.cookie=KEY+'='+encodeURIComponent(JSON.stringify(val||active))+';path=/;max-age=31536000;SameSite=Lax';
  }};
  window.applyCats=function(){{
    var pills=document.querySelectorAll('.catbar .pill-toggle[data-cat]');
    var active=[];
    pills.forEach(function(p){{if(p.classList.contains('on'))active.push(p.getAttribute('data-cat'))}});
    var showAll=active.length===pills.length;
    document.querySelectorAll('[data-section][data-cat]').forEach(function(s){{
      var c=s.getAttribute('data-cat');
      s.style.display=(showAll||active.indexOf(c)>=0)?'':'none';
    }});
    // An empty page with no explanation reads as a broken site. Say what
    // happened and offer the way out, rather than leaving a void under the
    // filters.
    var host=document.getElementById('categories');
    if(!host||!pills.length)return;
    var msg=document.getElementById('catempty');
    if(!active.length){{
      if(!msg){{
        msg=document.createElement('p');
        msg.id='catempty';msg.className='noresults';msg.style.display='block';
        msg.innerHTML='No categories selected. <a href="#" onclick="resetCats();return false">Show everything</a>';
        host.insertBefore(msg,host.firstChild);
      }}
      msg.style.display='block';
    }}else if(msg){{msg.style.display='none'}}
  }};
  var saved=getSaved();
  // saved can be [], and [] is truthy in JS — the check that let a stored
  // "None" survive reloads. Require an actual selection.
  if(saved&&saved.length){{
    document.querySelectorAll('.catbar .pill-toggle[data-cat]').forEach(function(p){{
      var c=p.getAttribute('data-cat');
      p.classList.toggle('on',saved.indexOf(c)>=0);
    }});
    applyCats();
  }}
  // Always sync the chip, saved filters or not. Without this the default state
  // renders the static label from the HTML — "All", while a click clears
  // everything — which is the exact confusion this chip is meant to avoid.
  updateAllChip();
}})();
function setLoc(loc){{
  document.body.className=document.body.className.replace(/loc-[a-z]+/g,'').trim();
  if(loc!=='global')document.body.classList.add('loc-'+loc);
  var btn=document.getElementById('locbtn');
  if(btn)btn.innerHTML=loc==='ca'?'🍁 Canada':loc==='us'?'🇺🇸 US':'🌐 Global';
  if(btn)btn.classList.toggle('active',loc!=='global');
  var m=document.getElementById('locmenu');if(m)m.classList.remove('open');
  document.cookie='vf_loc='+loc+';path=/;max-age=31536000;SameSite=Lax';
}}
(function(){{
  var m=document.cookie.match('(^|;)\\\\s*vf_loc=([^;]*)');
  if(m&&m[2]!=='global')setLoc(m[2]);
}})();
</script>
<!-- network-block 2026-07-12 -->
<style>.toln{{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:4px 10px;padding:8px 16px;font:400 11px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;border-top:1px solid rgba(128,128,128,.1);color:rgba(128,128,128,.45)}}.toln a{{color:inherit;text-decoration:none}}.toln a:hover{{color:rgba(128,128,128,.85);text-decoration:underline}}.toln .d{{color:rgba(128,128,128,.2)}}@media(prefers-color-scheme:dark){{.toln{{border-top-color:rgba(200,200,200,.07);color:rgba(200,200,200,.35)}}.toln a:hover{{color:rgba(200,200,200,.8)}}.toln .d{{color:rgba(200,200,200,.15)}}}}</style>
<nav class="toln" aria-label="Related sites"><a href="https://dreamsitedesign.com">DreamSite Design</a></nav>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Verified Free",
  "url": "https://veri-free.com",
  "publisher": {{
    "@type": "Organization",
    "name": "DreamSite Design",
    "url": "https://dreamsitedesign.com"
  }}
}}
</script>
<!-- /network-block -->
</body></html>"""

def short_worth(w):
    """Extract the dollar figure or key phrase from the worth string."""
    import re
    m = re.search(r'[≈~]?\s?\$[\d,]+\+?(?:/(?:year|month|yr|mo))?', w)
    if m: return m.group(0).strip()
    m = re.search(r'\$[\d,]+[–\-][\d,]+\+?(?:/(?:year|month))?', w)
    if m: return m.group(0).strip()
    return None

def card(l, lang="en"):
    get_line = l.get("free_includes", [""])[0]
    if lang != "en":
        get_line = GET_L10N.get(lang, {}).get(l["name"], get_line)
    c = score_color(l["free_score"])
    sw = l.get("short_worth") or short_worth(l.get("worth", ""))
    if lang == "en":
        t_saves, t_pays_you, t_pays, t_costs, t_value, t_you_get = (
            f"SAVES {sw}", f"PAYS YOU {sw}", f"PAYS {sw}", "COSTS YOU", f"{sw} value", "You get")
    else:
        tc = L10N[lang]["card"]
        t_saves   = tc["saves"].replace("{v}", sw or "")
        t_pays_you= tc["pays_you"].replace("{v}", sw or "")
        t_pays    = tc["pays"].replace("{v}", sw or "")
        t_costs   = tc["costs_you"]
        t_value   = tc["value"].replace("{v}", sw or "")
        t_you_get = tc["you_get"]
    if l["category"] == "earn":
        if l["verdict"] in ("truly", "forever") and sw:
            val = f'<span class="vtag pays" data-tip="Real money paid to you — the realistic rate, not the marketing pitch">{t_pays_you}</span>'
        elif sw and l["verdict"] == "freeish":
            val = f'<span class="vtag pays low" data-tip="It does pay — but at this hourly rate. Compare before spending your time">{t_pays}</span>'
        elif l["verdict"] in ("trap", "fake", "notfree"):
            val = f'<span class="vtag trap-warn" data-tip="You pay them, not the other way around — see why inside">{t_costs}</span>'
        else:
            val = ""  # free-to-use earn tools (job boards etc.) — no rate, no scare tag
    elif l["verdict"] == "truly" and sw:
        val = f'<span class="vtag saves" data-tip="What the paid equivalent costs — money this free option keeps in your pocket">{t_saves}</span>'
    elif sw:
        val = f'<span class="vtag" data-tip="The price of the paid tier this free plan gives you a slice of">{t_value}</span>'
    else:
        val = ""
    return (f'<a class="card" href="/{l["slug"]}/" data-search="{esc((l["name"]+" "+CATS[l["category"]][0]+" "+VERDICTS[l["verdict"]][0]).lower())}" '
            f'data-free="{l["free_score"]}" data-value="{l["value_score"]}" data-name="{esc(l["name"].lower())}">'
            f'<div class="row">{favicon(l["url"], override=l.get("favicon_url"))}{pill(l["verdict"], lang=lang)}<span class="chip" data-tip="Free Score {l["free_score"]}/100 — how genuinely free this is. Higher means fewer strings." style="color:{c};border-color:{c}">{l["free_score"]}</span></div><h3>{esc(l["name"])}</h3>'
            f'<p class="cost"><b>{t_you_get}</b>{esc(get_line)}</p>'
            f'{val}</a>')

CSS = CSS.replace("{SPRITE_N}", str(len(SPRITE_INDEX) or 1))

def build():
    import shutil
    data = json.load(open(os.path.join(os.path.dirname(OUT), "listings.json")))
    checked = data["checked"]
    listings = data["listings"]
    for l in listings:
        l["slug"] = slugify(l["name"])
    listings.sort(key=lambda x: (-x["free_score"], -x["value_score"]))

    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)

    # ---------- homepage ----------
    legend = "".join(
        f'<div class="legend-item">{pill(k, tip=False)}<span>{esc(d)}</span></div>'
        for k, (_, _, _, d) in VERDICTS.items())
    legend_side = "".join(
        f'<div class="sl-item">{pill(k, tip=False)}<span>{esc(d)}</span></div>'
        for k, (_, _, _, d) in VERDICTS.items())

    import collections
    cat_counts = collections.Counter(l["category"] for l in listings)
    # Order categories by how many listings each has (largest first), so the
    # bar and the homepage sections both lead with the most substantial ones.
    CAT_ORDER = sorted(CATS.keys(), key=lambda k: (-cat_counts.get(k, 0), CATS[k][0].lower()))

    sections = ""
    for cslug in CAT_ORDER:
        ctitle, cblurb = CATS[cslug]
        cards = "".join(card(l) for l in listings if l["category"] == cslug)
        sections += (f'<section class="section" data-section data-cat="{cslug}">'
                     f'<div class="section-head"><h2><a href="/{cslug}/">{esc(ctitle)}</a></h2>'
                     f'<a class="all" href="/{cslug}/">All {esc(ctitle.lower())} →</a></div>'
                     f'<div class="grid">{cards}</div></section>')

    genuine = sum(1 for l in listings if l["verdict"] in ("truly", "forever"))
    squeeze = sum(1 for l in listings if l["verdict"] == "freeish")
    traps = sum(1 for l in listings if l["verdict"] in ("trap", "fake", "notfree"))

    cat_dd = "".join(
        f'<a href="/{cs}/"><span class="cicon">{ICONS[cs]}</span>{esc(CATS[cs][0])}<span class="dd-count">{cat_counts.get(cs,0)}</span></a>'
        for cs in CAT_ORDER)
    NAV = (f'<nav class="nav"><div class="wrap nav-in">'
           f'<a class="logo" href="/">VERIFIED·<b>FREE</b></a>'
           f'<div class="nav-links">'
           f'<div class="dropdown"><a href="/#categories">Categories</a>'
           f'<div class="dropdown-menu"><div class="dd-inner">{cat_dd}<div class="sep"></div>'
           f'<a href="/deals/">Verified Deals</a><a href="/free-in-real-life/">Free in Real Life</a><a href="/compare/">Comparisons</a><a href="/changelog/">What Changed</a><a href="/when-to-buy/">When to Buy</a></div></div></div>'
           f'<a href="/all/">Everything checked</a>'
           f'<a href="/deals/">Deals</a>'
           f'<a href="/coupons/">Coupons</a>'
           f'<a href="/free-consultations/">Consultations</a>'
           f'<a href="/free-in-real-life/">Real Life</a>'
           f'<a href="/compare/">Compare</a>'
           f'<a href="/methodology/">How we verify</a>'
           f'<a href="/submit/">For businesses</a>'
           f'{lang_switcher("en")}'
           f'</div></div></nav>')

    # Category bar
    cat_pills = "".join(
        f'<span class="pill-toggle on" data-cat="{cs}" data-tip="{esc(CATS[cs][1])}" onclick="toggleCat(this)">{ICONS[cs]}{esc(CATS[cs][0])}<span class="pc">{cat_counts.get(cs,0)}</span></span>'
        for cs in CAT_ORDER)
    CATBAR = (f'<div class="catbar"><div class="catbar-in">'
              f'<div class="catfilters">'
              f'<span class="pill-toggle reset on" id="catAll" role="button" tabindex="0" aria-pressed="true"'
              f' data-all="All" data-none="None" data-tip-on="Turn every category off"'
              f' data-tip-off="Turn every category on" data-tip="Turn every category off"'
              f' onclick="toggleAll()"><span class="pl">All</span><span class="pc">{len(listings)}</span></span>'
              f'{cat_pills}'
              f'</div>'
              f'<div class="loc-wrap"><button class="loc-pick" id="locbtn" onclick="document.getElementById(\'locmenu\').classList.toggle(\'open\')" title="Set your location">🌐 Global</button>'
              f'<div class="loc-menu" id="locmenu">'
              f'<a onclick="setLoc(\'global\')">🌐 Global</a>'
              f'<a onclick="setLoc(\'ca\')">🍁 Canada</a>'
              f'<a onclick="setLoc(\'us\')">🇺🇸 United States</a>'
              f'</div></div>'
              f'</div></div>')

    NAV = '<header class="site-header">' + NAV + CATBAR + '</header>'
    # The landing has no grid for the chips to filter, so they sit as a
    # browse row above the feed instead of jammed under the nav where they
    # read as nav overflow. There they navigate to the category pages.
    NAV_NOCAT = '<header class="site-header">' + NAV.split('<header class="site-header">')[1].replace(CATBAR, '')


    # Build an OG image URL from favicon as fallback
    OG_IMG = f"{DOMAIN}/og.png"

    _orig_page = page
    def page_with_nav(*a, **kw):
        return _orig_page(*a, **kw).replace('<!--NAV-->', NAV)
    page_nav = page_with_nav

    hl_items = ""
    for h in data.get("headlines", [])[:5]:
        hl_items += f'<div class="hl-item"><span class="hl-date">{esc(h["date"])}</span><a href="{esc(h["link"])}">{esc(h["title"])}</a></div>'
    headlines_html = f'<section class="headlines"><div class="wrap"><h2>In the news</h2><div class="hl-list">{hl_items}</div></div></section>' if hl_items else ""

    snap_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feed_snapshot.json")
    stream = json.load(open(snap_path, encoding="utf-8")) if os.path.exists(snap_path) else {}
    forever_n = sum(1 for l in listings if l["verdict"] == "forever")
    # `genuine` is truly+forever, which is right for prose and WRONG for the
    # "Truly free" filter button — that button filters to truly alone.
    truly_n = sum(1 for l in listings if l["verdict"] == "truly")
    match_index = build_match_index(listings)

    # The stream leads the homepage, but only a slice of it: /now/ keeps the
    # full run, so the two pages don't compete for the same content.
    home_stream = ""
    if stream.get("items"):
        si = stream["items"][:16]
        home_stream = (
            '<section class="homestream"><div class="wrap">'
            '<div class="stream">'
            + "".join(stream_card(it, lead=(i == 0), match=match_listing(it, match_index))
                        for i, it in enumerate(si))
            + '</div></div></section>')

    home_body = f"""
<header class="hero slim">
<div class="wrap">
<div class="hero-top"><h1>Veri-<em>Free</em></h1><p class="tagline">Very Free &amp; Easy</p>
<p class="sub">We check every "free" offer and tell you what it really costs.</p></div>
</div></header>
{home_stream}
<section class="handoff"><div class="wrap">
<a class="handoff-card" href="/all/">
<span class="ho-k">The verdicts</span>
<span class="ho-h">All {len(listings)}, checked against one rubric</span>
<span class="ho-n"><b>{genuine}</b> truly free · <b>{forever_n}</b> free forever · <b>{squeeze}</b> free-ish · <b>{traps}</b> traps &amp; fakes</span>
<span class="ho-go">Search and filter them →</span></a>
</div></section>
{headlines_html}
<section class="sitecheck"><div class="wrap">
<div class="sc-head">
<h2>Can AI and Google actually find your site?</h2>
<p>A free, instant check: are <b>ChatGPT, Perplexity &amp; Claude</b> allowed to read your site, and are your <b>SEO basics</b> in place? We check it live, free — no signup.</p>
</div>
<form class="sc-form" id="scForm" novalidate>
<input id="scInput" type="text" inputmode="url" autocomplete="off" spellcheck="false" placeholder="yourdomain.com" aria-label="Website address to check">
<button type="submit" id="scBtn">Check free</button>
</form>
<div class="sc-status" id="scStatus" hidden></div>
<div class="sc-results" id="scResults"></div>
<p class="sc-foot" id="scFoot" hidden>Deeper report — security, speed, accessibility &amp; more — at <a href="https://checkmysite.pro/" target="_blank" rel="noopener">checkmysite.pro</a></p>
</div></section>
<script src="/sitecheck.js" defer></script>
<section class="bizband"><div class="wrap">
<h2>Does your business lead with something free?</h2>
<p>A free tool, a free scan, a free tier — if it's genuinely free and easy, we'll verify it. Same rubric as everyone; a stamp your customers can trust.</p>
<a class="visit" href="/submit/">Get your free offering verified →</a>
</div></section>
<script>
const q=document.getElementById('q'),cards=[...document.querySelectorAll('.card')],
secs=[...document.querySelectorAll('[data-section]')],nores=document.getElementById('noresults'),
count=document.getElementById('count');
q.addEventListener('input',()=>{{
const v=q.value.trim().toLowerCase();let shown=0;
cards.forEach(c=>{{const hit=!v||c.dataset.search.includes(v);c.style.display=hit?'':'none';if(hit)shown++;}});
secs.forEach(s=>{{const any=[...s.querySelectorAll('.card')].some(c=>c.style.display!=='none');s.style.display=any?'':'none';}});
nores.style.display=shown?'none':'block';
count.textContent=v?shown+' result'+(shown===1?'':'s'):'';
}});
document.querySelectorAll('.sortbtn').forEach(btn => btn.addEventListener('click', () => {{
  document.querySelectorAll('.sortbtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const key = btn.dataset.sort;
  document.querySelectorAll('.grid').forEach(grid => {{
    const items = [...grid.children].filter(c => c.classList.contains('card'));
    items.sort((a, b) => {{
      if (key === 'free') return (+b.dataset.free) - (+a.dataset.free) || (+b.dataset.value) - (+a.dataset.value);
      if (key === 'value') return (+b.dataset.value) - (+a.dataset.value) || (+b.dataset.free) - (+a.dataset.free);
      return a.dataset.name.localeCompare(b.dataset.name);
    }});
    items.forEach(c => grid.appendChild(c));
  }});
}}));
// Verdict filters
document.querySelectorAll('.vfilter').forEach(function(btn){{
  btn.addEventListener('click',function(){{
    document.querySelectorAll('.vfilter').forEach(function(b){{b.classList.remove('on')}});
    btn.classList.add('on');
    var v=btn.dataset.v;
    document.querySelectorAll('.card').forEach(function(c){{
      if(v==='all'){{c.style.display='';return;}}
      var vs=v.split(',');
      var match=vs.some(function(vv){{return c.querySelector('.pill')&&c.querySelector('.pill').textContent.trim().toLowerCase().replace(/[- ]/g,'').indexOf(vv.replace(/[- ]/g,''))>=0}});
      c.style.display=match?'':'none';
    }});
    document.querySelectorAll('[data-section]').forEach(function(s){{
      var any=[...s.querySelectorAll('.card')].some(function(c){{return c.style.display!=='none'}});
      s.style.display=any?'':'none';
    }});
  }});
}});
</script>
<button class="backtop" id="btt" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" aria-label="Back to top">↑</button>
<script>
window.addEventListener('scroll',function(){{document.getElementById('btt').classList.toggle('show',window.scrollY>600)}});
</script>
"""
    home_extra = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Verified Free","url":"https://veri-free.com","description":"Verified rankings of how free the internets free offers really are.","potentialAction":{"@type":"SearchAction","target":"https://veri-free.com/?q={search_term_string}","query-input":"required name=search_term_string"}}</script>'
    # hreflang alternates shared by all five homepages
    ALT_LINKS = f'<link rel="alternate" hreflang="en" href="{DOMAIN}/">'
    for _lg in EXTRA_LANGS:
        ALT_LINKS += f'<link rel="alternate" hreflang="{HTML_LANG[_lg]}" href="{DOMAIN}/{_lg}/">'
    ALT_LINKS += f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/">'

    # Landing-language suggest banner (EN homepage only): if the browser prefers
    # es/pt/fr/de, offer that homepage once — dismissible, never a forced redirect.
    BANNER_JS = """
<script>
(function(){
  if(document.cookie.indexOf('vf_langoff=1')>=0)return;
  var m={'es':'\\u00bfPrefieres espa\\u00f1ol? Versi\\u00f3n en espa\\u00f1ol \\u2192','pt':'Prefere portugu\\u00eas? Vers\\u00e3o em portugu\\u00eas \\u2192','fr':'Vous pr\\u00e9f\\u00e9rez le fran\\u00e7ais ? Version fran\\u00e7aise \\u2192','de':'Lieber auf Deutsch? Deutsche Version \\u2192'};
  var l=(navigator.language||'').slice(0,2).toLowerCase();
  if(!m[l])return;
  var b=document.createElement('div');
  b.setAttribute('role','region');b.setAttribute('aria-label','Language suggestion');
  b.style.cssText='position:relative;z-index:60;background:#0E7B47;color:#fff;font:600 13.5px \\'Public Sans\\',sans-serif;padding:9px 40px 9px 16px;text-align:center';
  b.innerHTML='<a href="/'+l+'/" style="color:#fff">'+m[l]+'</a><span style="position:absolute;right:14px;top:7px;cursor:pointer;font-size:17px;line-height:1" aria-label="Dismiss">\\u00d7</span>';
  b.lastChild.onclick=function(){b.remove();document.cookie='vf_langoff=1;path=/;max-age=31536000;SameSite=Lax'};
  document.body.insertBefore(b,document.body.firstChild);
})();
</script>"""

    home = page("Verified Free — Is it actually free? We checked.",
                "Verified Free: verified rankings of how free the internet's 'free' offers really are.",
                "/", home_body + BANNER_JS, extra_head=home_extra + ALT_LINKS
                ).replace('<!--NAV-->', NAV_NOCAT)
    open(os.path.join(OUT, "index.html"), "w").write(home)

    # ---------- localized homepages (/es/ /pt/ /fr/ /de/) ----------
    # Phase 1: full chrome + verdicts + categories + checker in the language;
    # listing editorial text stays English until listings.json is translated.
    LANG_HOME_JS = """
<script>
const q=document.getElementById('q'),cards=[...document.querySelectorAll('.card')],
secs=[...document.querySelectorAll('[data-section]')],nores=document.getElementById('noresults'),
count=document.getElementById('count');
var R1='__R1__',RN='__RN__';
q.addEventListener('input',()=>{
const v=q.value.trim().toLowerCase();let shown=0;
cards.forEach(c=>{const hit=!v||c.dataset.search.includes(v);c.style.display=hit?'':'none';if(hit)shown++;});
secs.forEach(s=>{const any=[...s.querySelectorAll('.card')].some(c=>c.style.display!=='none');s.style.display=any?'':'none';});
nores.style.display=shown?'none':'block';
count.textContent=v?shown+' '+(shown===1?R1:RN):'';
});
document.querySelectorAll('.sortbtn').forEach(btn => btn.addEventListener('click', () => {
  document.querySelectorAll('.sortbtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const key = btn.dataset.sort;
  document.querySelectorAll('.grid').forEach(grid => {
    const items = [...grid.children].filter(c => c.classList.contains('card'));
    items.sort((a, b) => {
      if (key === 'free') return (+b.dataset.free) - (+a.dataset.free) || (+b.dataset.value) - (+a.dataset.value);
      if (key === 'value') return (+b.dataset.value) - (+a.dataset.value) || (+b.dataset.free) - (+a.dataset.free);
      return a.dataset.name.localeCompare(b.dataset.name);
    });
    items.forEach(c => grid.appendChild(c));
  });
}));
document.querySelectorAll('.vfilter').forEach(function(btn){
  btn.addEventListener('click',function(){
    document.querySelectorAll('.vfilter').forEach(function(b){b.classList.remove('on')});
    btn.classList.add('on');
    var v=btn.dataset.v;
    document.querySelectorAll('.card').forEach(function(c){
      if(v==='all'){c.style.display='';return;}
      var vs=v.split(',');
      var match=vs.some(function(vv){return c.querySelector('.pill')&&c.querySelector('.pill').textContent.trim().toLowerCase().replace(/[- ]/g,'').indexOf(vv.replace(/[- ]/g,''))>=0});
      c.style.display=match?'':'none';
    });
    document.querySelectorAll('[data-section]').forEach(function(s){
      var any=[...s.querySelectorAll('.card')].some(function(c){return c.style.display!=='none'});
      s.style.display=any?'':'none';
    });
  });
});
</script>
<button class="backtop" id="btt" onclick="window.scrollTo({top:0,behavior:'smooth'})" aria-label="Back to top">↑</button>
<script>
window.addEventListener('scroll',function(){document.getElementById('btt').classList.toggle('show',window.scrollY>600)});
</script>"""

    LANG_NAV = {}
    for LG in EXTRA_LANGS:
        T = L10N[LG]
        # nav (category links localized; other inner pages English until translated)
        cat_dd_L = ""
        for cs in CAT_ORDER:
            cat_dd_L += (f'<a href="/{LG}/{cs}/"><span class="cicon">{ICONS[cs]}</span>{esc(T["cats"][cs][0])}'
                         f'<span class="dd-count">{cat_counts.get(cs,0)}</span></a>')
        NAV_L = (f'<nav class="nav"><div class="wrap nav-in">'
                 f'<a class="logo" href="/{LG}/">VERIFIED·<b>FREE</b></a>'
                 f'<div class="nav-links">'
                 f'<div class="dropdown"><a href="/{LG}/#categories">{esc(T["nav"]["categories"])}</a>'
                 f'<div class="dropdown-menu"><div class="dd-inner">{cat_dd_L}<div class="sep"></div>'
                 f'<a href="/deals/">{esc(T["nav"]["dd_deals"])}</a><a href="/compare/">{esc(T["nav"]["dd_compare"])}</a>'
                 f'<a href="/changelog/">{esc(T["nav"]["dd_changed"])}</a><a href="/when-to-buy/">{esc(T["nav"]["dd_buy"])}</a></div></div></div>'
                 f'<a href="/deals/">{esc(T["nav"]["deals"])}</a>'
                 f'<a href="/compare/">{esc(T["nav"]["compare"])}</a>'
                 f'<a href="/methodology/">{esc(T["nav"]["method"])}</a>'
                 f'<a href="/submit/">{esc(T["nav"]["biz"])}</a>'
                 f'{lang_switcher(LG)}'
                 f'</div></div></nav>')
        cat_pills_L = ""
        for cs in CAT_ORDER:
            cat_pills_L += (f'<span class="pill-toggle on" data-cat="{cs}" data-tip="{esc(T["cats"][cs][1])}" '
                            f'onclick="toggleCat(this)">{ICONS[cs]}{esc(T["cats"][cs][0])}<span class="pc">{cat_counts.get(cs,0)}</span></span>')
        CATBAR_L = (f'<div class="catbar"><div class="catbar-in">'
                    f'<div class="catfilters">'
                    f'<span class="pill-toggle reset on" id="catAll" role="button" tabindex="0" aria-pressed="true"'
                    f' data-all="{esc(T["filters"]["all"])}" data-none="{esc(T["none_lbl"])}"'
                    f' data-tip-on="{esc(T["all_tip_on"])}" data-tip-off="{esc(T["all_tip_off"])}"'
                    f' data-tip="{esc(T["all_tip_on"])}" onclick="toggleAll()">'
                    f'<span class="pl">{esc(T["filters"]["all"])}</span><span class="pc">{len(listings)}</span></span>'
                    f'{cat_pills_L}'
                    f'</div>'
                    f'<div class="loc-wrap"><button class="loc-pick" id="locbtn" onclick="document.getElementById(\'locmenu\').classList.toggle(\'open\')" title="Set your location">\U0001F310 Global</button>'
                    f'<div class="loc-menu" id="locmenu">'
                    f'<a onclick="setLoc(\'global\')">\U0001F310 Global</a>'
                    f'<a onclick="setLoc(\'ca\')">\U0001F341 Canada</a>'
                    f'<a onclick="setLoc(\'us\')">\U0001F1FA\U0001F1F8 United States</a>'
                    f'</div></div>'
                    f'</div></div>')
        legend_side_L = "".join(
            f'<div class="sl-item">{pill(k, tip=False, lang=LG)}<span>{esc(L10N[LG]["verdicts"][k][1])}</span></div>'
            for k in VERDICTS)
        sections_L = ""
        for cslug in CAT_ORDER:
            clabel = T["cats"][cslug][0]
            cards_L = "".join(card(l, LG) for l in listings if l["category"] == cslug)
            sections_L += (f'<section class="section" data-section data-cat="{cslug}">'
                           f'<div class="section-head"><h2><a href="/{LG}/{cslug}/">{esc(clabel)}</a></h2>'
                           f'<a class="all" href="/{LG}/{cslug}/">{esc(T["all_cat"].replace("{c}", clabel))}</a></div>'
                           f'<div class="grid">{cards_L}</div></section>')
        stats_L = (T["stats"].replace("{g}", str(genuine)).replace("{s}", str(squeeze)).replace("{t}", str(traps)))
        headlines_L = (f'<section class="headlines"><div class="wrap"><h2>{esc(T["news"])}</h2>'
                       f'<div class="hl-list">{hl_items}</div></div></section>') if hl_items else ""
        sc_strings = json.dumps(T["sc_js"], ensure_ascii=False)
        # Same shape as the English landing: thin head, one find bar, the
        # stream, then the verdicts.
        home_stream_L = ""
        if stream.get("items"):
            si_L = stream["items"][:16]
            home_stream_L = (
                '<section class="homestream"><div class="wrap">'

                '<div class="stream">'
                + "".join(stream_card(it, lead=(i == 0), match=match_listing(it, match_index))
                          for i, it in enumerate(si_L))
                + '</div></div></section>')
        body_L = (f'<header class="hero slim"><div class="wrap">'
                  f'<div class="hero-top"><h1>Veri-<em>Free</em></h1>'
                  f'<p class="tagline">{esc(T["tagline"])}</p>'
                  f'<p class="sub">{T["sub"]}</p></div>'
                  f'</div></header>'
                  f'{home_stream_L}'
                  f'<div class="side-legend closed" id="sidepanel">'
                  f'<div class="sl-tab" onclick="document.getElementById(\'sidepanel\').classList.toggle(\'closed\')">{esc(T["guide"])}</div>'
                  f'<div class="sl-body"><h2>{esc(T["verdicts_h"])}</h2>{legend_side_L}'
                  f'<div class="sl-divider"></div><h2>{esc(T["sort_h"])}</h2>'
                  f'<div class="sl-sorts">'
                  f'<button class="sortbtn active" data-sort="free">{esc(T["sort_free"])}</button>'
                  f'<button class="sortbtn" data-sort="value">{esc(T["sort_value"])}</button>'
                  f'<button class="sortbtn" data-sort="name">{esc(T["sort_az"])}</button>'
                  f'</div></div></div>'
                  f'<div class="findbar"><div class="wrap findbar-in">'
                  f'<div class="searchbar"><input id="q" type="search" aria-label="Search" placeholder="{esc(T["search_ph"])}">'
                  f'<span class="kbd">{T["verified"].replace("{n}", str(len(listings)))}</span></div>'
                  f'<div class="vfilters">'
                  f'<button class="vfilter on" data-v="all">{esc(T["filters"]["all"])}</button>'
                  f'<button class="vfilter" data-v="truly">{esc(T["filters"]["truly"])}</button>'
                  f'<button class="vfilter" data-v="forever">{esc(T["filters"]["forever"])}</button>'
                  f'<button class="vfilter" data-v="freeish">{esc(T["filters"]["freeish"])}</button>'
                  f'<button class="vfilter" data-v="trap,fake,notfree">{esc(T["filters"]["traps"])}</button>'
                  f'</div></div></div>'
                  f'<main class="wrap" id="categories">'
                  f'<div class="verdicts-head"><h2>{esc(T["verdicts_all_h"])}</h2>'
                  f'<p class="count" id="count"></p></div>'
                  f'{sections_L}'
                  f'<p class="noresults" id="noresults">{T["noresults"]}</p></main>'
                  f'{headlines_L}'
                  f'<section class="sitecheck"><div class="wrap">'
                  f'<div class="sc-head"><h2>{T["sc_h2"]}</h2><p>{T["sc_sub"]}</p></div>'
                  f'<form class="sc-form" id="scForm" novalidate>'
                  f'<input id="scInput" type="text" inputmode="url" autocomplete="off" spellcheck="false" placeholder="{esc(T["sc_ph"])}" aria-label="URL">'
                  f'<button type="submit" id="scBtn">{esc(T["sc_btn"])}</button></form>'
                  f'<div class="sc-status" id="scStatus" hidden></div>'
                  f'<div class="sc-results" id="scResults"></div>'
                  f'<p class="sc-foot" id="scFoot" hidden>{esc(T["sc_foot"])} <a href="https://checkmysite.pro/" target="_blank" rel="noopener">checkmysite.pro</a></p>'
                  f'</div></section>'
                  f'<script>window.SC_STRINGS={sc_strings};</script>'
                  f'<script src="/sitecheck.js" defer></script>'
                  f'<section class="bizband"><div class="wrap">'
                  f'<h2>{esc(T["biz_h2"])}</h2><p>{esc(T["biz_p"])}</p>'
                  f'<a class="visit" href="/submit/">{esc(T["biz_cta"])}</a>'
                  f'</div></section>'
                  + LANG_HOME_JS.replace("__R1__", T["result_1"]).replace("__RN__", T["result_n"]))
        LANG_NAV[LG] = '<header class="site-header">' + NAV_L + CATBAR_L + '</header>'
        p_L = page(T["meta_title"], T["meta_desc"], f"/{LG}/", body_L,
                   extra_head=ALT_LINKS, lang=LG)
        p_L = p_L.replace('<!--NAV-->', LANG_NAV[LG])
        os.makedirs(os.path.join(OUT, LG), exist_ok=True)
        open(os.path.join(OUT, LG, "index.html"), "w").write(p_L)

    # ---------- category pages ----------
    # Live AI-agent leaderboard sidebar on the AI page (self-hosted widget +
    # same-origin /api/ai-leaderboard function; auto-refreshes from arena.ai).
    AI_LB = {
        "en": ("Live AI agent leaderboard",
               "Standings from 1.2M+ real coding-agent sessions, auto-refreshing. One lens on AI quality — the verified free tiers alongside cover the rest: chat, image, music, voice and open models."),
        "es": ("Ranking de agentes de IA — en vivo",
               "Posiciones de más de 1,2M de sesiones reales de agentes de código, actualizadas solas. Una lente sobre la IA — los niveles gratuitos verificados de al lado cubren el resto: chat, imagen, música, voz y modelos abiertos."),
        "pt": ("Ranking de agentes de IA — ao vivo",
               "Posições de mais de 1,2M de sessões reais de agentes de código, atualizadas sozinhas. Uma lente sobre a IA — os planos grátis verificados ao lado cobrem o resto: chat, imagem, música, voz e modelos abertos."),
        "fr": ("Classement des agents IA — en direct",
               "Classement issu de plus de 1,2 M de sessions réelles d'agents de code, mis à jour automatiquement. Un angle sur l'IA — les offres gratuites vérifiées à côté couvrent le reste : chat, image, musique, voix et modèles ouverts."),
        "de": ("KI-Agenten-Rangliste — live",
               "Stand aus über 1,2 Mio. echten Coding-Agent-Sessions, aktualisiert sich selbst. Eine Perspektive auf KI — die geprüften Gratis-Tarife daneben decken den Rest ab: Chat, Bild, Musik, Stimme und offene Modelle."),
    }
    def ai_aside(lg):
        t_lb, n_lb = AI_LB[lg]
        return (f'<aside class="ai-lb"><div data-checkmysite-ai data-compact="1" data-top="8" data-title="{esc(t_lb)}"></div>'
                f'<p class="ai-lb-note">{esc(n_lb)}</p></aside>')

    for cslug, (ctitle, cblurb) in CATS.items():
        cl = [l for l in listings if l["category"] == cslug]
        cards = "".join(card(l) for l in cl)
        truly = sum(1 for l in cl if l["verdict"] == "truly")
        is_ai = cslug == "ai-tools"
        main_cls = "wrap ai-layout" if is_ai else "wrap"
        body = (f'<header class="pagehead wrap"><h1>{esc(ctitle)}</h1><p>{esc(cblurb)}</p></header>'
                f'<main class="{main_cls}"><section data-section data-cat="{cslug}">'
                f'<h2 class="sechead">Every {esc(ctitle.lower())} listing, ranked by how free it really is</h2>'
                f'<p class="seclede">{len(cl)} verified · {truly} truly free · sorted by Free Score.</p>'
                f'<div class="grid">{cards}</div></section>'
                + spec_table(cslug, cl)
                + (ai_aside("en") if is_ai else "") + '</main>'
                + ('<script src="/ai-widget.js" defer></script>' if is_ai else ''))
        cat_schema = json.dumps({"@context": "https://schema.org", "@graph": [
            {"@type": "CollectionPage", "name": f"{ctitle} — Verified Free", "url": f"{DOMAIN}/{cslug}/", "description": cblurb},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": ctitle, "item": f"{DOMAIN}/{cslug}/"}]},
            {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": n + 1, "name": f"Is {l['name']} actually free?", "url": f"{DOMAIN}/{l['slug']}/"}
                for n, l in enumerate(cl)]}]})
        # hreflang alternates: EN /cat/ <-> each /{lg}/cat/
        cat_alt = f'<link rel="alternate" hreflang="en" href="{DOMAIN}/{cslug}/">'
        for _lg in EXTRA_LANGS:
            cat_alt += f'<link rel="alternate" hreflang="{HTML_LANG[_lg]}" href="{DOMAIN}/{_lg}/{cslug}/">'
        cat_alt += f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/{cslug}/">'
        p = page_nav(f"{ctitle} — Verified Free", cblurb, f"/{cslug}/", body,
                     extra_head=f'<script type="application/ld+json">{cat_schema}</script>' + cat_alt)
        os.makedirs(os.path.join(OUT, cslug))
        open(os.path.join(OUT, cslug, "index.html"), "w").write(p)

        # localized category pages (/{lg}/{cslug}/)
        for LG in EXTRA_LANGS:
            T = L10N[LG]
            clabel, cblurb_L = T["cats"][cslug]
            cards_L = "".join(card(l, LG) for l in cl)
            body_L = (f'<header class="pagehead wrap"><h1>{esc(clabel)}</h1><p>{esc(cblurb_L)}</p></header>'
                      f'<main class="{main_cls}"><section data-section data-cat="{cslug}">'
                      f'<h2 class="sechead">{esc(T["cat_every"].replace("{c}", clabel))}</h2>'
                      f'<p class="seclede">{esc(T["cat_lede"].replace("{n}", str(len(cl))).replace("{t}", str(truly)))}</p>'
                      f'<div class="grid">{cards_L}</div></section>'
                      + (ai_aside(LG) if is_ai else "") + '</main>'
                      + ('<script src="/ai-widget.js" defer></script>' if is_ai else ''))
            schema_L = json.dumps({"@context": "https://schema.org", "@graph": [
                {"@type": "CollectionPage", "name": f"{clabel} — Verified Free",
                 "url": f"{DOMAIN}/{LG}/{cslug}/", "inLanguage": HTML_LANG[LG], "description": cblurb_L},
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/{LG}/"},
                    {"@type": "ListItem", "position": 2, "name": clabel, "item": f"{DOMAIN}/{LG}/{cslug}/"}]}]},
                ensure_ascii=False)
            p_L = page(f"{clabel} — Verified Free", cblurb_L, f"/{LG}/{cslug}/", body_L,
                       extra_head=f'<script type="application/ld+json">{schema_L}</script>' + cat_alt,
                       lang=LG)
            p_L = p_L.replace('<!--NAV-->', LANG_NAV[LG])
            os.makedirs(os.path.join(OUT, LG, cslug), exist_ok=True)
            open(os.path.join(OUT, LG, cslug, "index.html"), "w").write(p_L)

    # ---------- listing pages ----------
    for l in listings:
        vlabel, vcolor, vbg, vdef = VERDICTS[l["verdict"]]
        ctitle = CATS[l["category"]][0]
        related = [r for r in listings if r["category"] == l["category"] and r["slug"] != l["slug"]][:4]
        rel_cards = "".join(card(r) for r in related)
        facts_rows = "".join(f'<tr><td class="k">{k}</td><td>{esc(v)}</td></tr>' for k, v in [
            ("Verdict", vlabel), ("Card required", l["card"]), ("Auto-bills", l["autobill"]),
            ("Account", l["account"]), ("Limits", l["limits"]), ("The real cost", l["realcost"])])
        # Schema and the visible block come from the same source, so the page
        # always contains the answer it claims in markup.
        faq_qs = [{"@type": "Question", "name": q,
                   "acceptedAnswer": {"@type": "Answer", "text": a}}
                  for q, a in faq_pairs(l)]
        if l.get("catch"):
            faq_qs.append({"@type": "Question",
                           "name": f"What's the catch with {l['name']}?",
                           "acceptedAnswer": {"@type": "Answer", "text": l["catch"]}})
        if l.get("free_includes"):
            faq_qs.append({"@type": "Question",
                           "name": f"What do you get free with {l['name']}?",
                           "acceptedAnswer": {"@type": "Answer", "text": "; ".join(l["free_includes"])}})
        schema = json.dumps({"@context": "https://schema.org", "@graph": [
            {"@type": "Review",
             "itemReviewed": {"@type": "Product", "name": l["name"], "url": l["url"]},
             "reviewRating": {"@type": "Rating", "ratingValue": {"truly":5,"forever":4,"freeish":3,"trap":2,"fake":1,"notfree":1}[l["verdict"]], "bestRating": 5, "worstRating": 1},
             "name": f"Is {l['name']} actually free?",
             "reviewBody": l["short"],
             "datePublished": __import__("datetime").date.today().isoformat(),
             "author": {"@type": "Organization", "name": "Verified Free", "url": DOMAIN},
             "publisher": {"@type": "Organization", "name": "Verified Free", "url": DOMAIN}},
            {"@type": "FAQPage", "mainEntity": faq_qs},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": ctitle, "item": f"{DOMAIN}/{l['category']}/"},
                {"@type": "ListItem", "position": 3, "name": f"Is {l['name']} actually free?", "item": f"{DOMAIN}/{l['slug']}/"}]}]})
        free_list = "".join(f"<li>{esc(x)}</li>" for x in l.get("free_includes", []))
        summary = f'<p class="plain">{esc(l["get_summary"])}</p>' if l.get("get_summary") else ""
        draw_list = "".join(f"<li>{esc(x)}</li>" for x in l.get("drawbacks", []))
        locked = l.get("paid_locked", [])
        also = ("<h3 class=\"sub\">Also paywalled</h3><ul>" + "".join(f"<li>{esc(x)}</li>" for x in locked) + "</ul>") if locked else ""
        gets = (f'<div class="gets"><div class="col free"><h2>What you get free</h2><ul>{free_list}</ul>{summary}</div>'
                f'<div class="col locked"><h2>Drawbacks</h2><ul class="warn">{draw_list}</ul>{also}</div></div>')
        fs, vs = l["free_score"], l["value_score"]
        fc, vc = score_color(fs), score_color(vs * 10)
        scores = (f'<div class="scores">'
                  f'<div class="score"><b>How free</b><span class="num">{fs}<i>/100</i></span><div class="bar"><div style="width:{fs}%;background:{fc}"></div></div></div>'
                  f'<div class="score"><b>Value</b><span class="num">{vs}<i>/10</i></span><div class="bar"><div style="width:{vs*10}%;background:{vc}"></div></div></div></div>'
                  f'<details class="more mini"><summary>How these scores work</summary><div class="mbody">'
                  f'Free Score (0–100) follows a fixed rubric: cards up front, auto-billing, hard time cutoffs, withheld core features, and paying with your data or attention all deduct points. 90–100 truly free · 70–89 free forever · 45–69 squeezed · 15–44 trial mechanics · under 15 fake or gone. '
                  f'Value (0–10) is editorial: real-world worth of the free offering measured against its paid equivalent. Full rubric on the <a href="/methodology/">methodology page</a>.</div></details>')
        more = ""
        if l.get("more_info"):
            items = "".join(f'<details class="more"><summary>{esc(t)}</summary><div class="mbody">{esc(x)}</div></details>'
                            for t, x in l["more_info"])
            more = f'<div class="moreinfo"><h2>More info — tap to expand</h2>{items}</div>'
        alts_html = ""
        if l.get("free_alternatives"):
            items = "".join(f'<div class="alt-card"><a href="/{esc(a["slug"])}/">{esc(a["name"])}</a><span>{esc(a["why"])}</span></div>'
                            for a in l["free_alternatives"])
            alts_html = f'<div class="alts"><h2>Use this instead — actually free</h2>{items}</div>'
        worth = (f'<div class="worth"><b>What it&rsquo;s worth</b><p>{esc(l["worth"])}</p></div>') if l.get("worth") else ""
        disc = (f'<p class="disc">Disclosure: {esc(l["disclosure"])}</p>') if l.get("disclosure") else ""
        plays = ""
        if l.get("smart_moves"):
            items = "".join(f"<li>{esc(x)}</li>" for x in l["smart_moves"])
            plays = f'<div class="plays"><h2>The smart play</h2><ul>{items}</ul></div>'
        body = f"""
<div class="wrap"><p class="crumb"><a href="/">Verified Free</a> / <a href="/{l['category']}/">{esc(ctitle)}</a></p></div>
<main class="wrap"><article class="listing">
<div class="titlerow">{favicon(l['url'], big=True, override=l.get("favicon_url"))}<h1>Is {esc(l['name'])} actually free?</h1></div>
{stamp(l['verdict'], animate=True)}
{scores}
<p class="answer">{esc(l['short'])}</p>
{alts_html}
{worth}
{gets}
{spec_block(l)}
<div class="facts"><h2>Free facts</h2><table>{facts_rows}</table></div>
<div class="catch"><h2>The catch</h2><p>{esc(l['catch'])}</p></div>
{safety_box(l, checked)}
{plays}
{faq_block(l)}
{more}
<p class="checked">{verified_line(l, checked)} · Verdict: {vlabel} — {esc(vdef.lower())}</p>
{disc}
{'<div class="ca-badge avail">🍁 Canada</div><p class="ca-note">'+esc(l["canada"])+'</p>' if l.get("canada") else ""}
{ratings_row(l)}
{legit_box(l)}
{sentiment_box(l)}
<a class="visit" href="{esc(l['url'])}" target="_blank" rel="noopener">Visit {esc(l['name'])} →</a>
{feedback_form(l, vlabel)}
</article>
{FEEDBACK_JS}
<section class="related"><h2>More in {esc(ctitle)}</h2><div class="grid">{rel_cards}</div></section>
</main>"""
        p = page_nav(f"Is {l['name']} Actually Free? ({checked}) — Verified Free",
                 f"{vlabel}: {l['realcost']} Our verified answer on whether {l['name']} is really free.",
                 f"/{l['slug']}/", body,
                 extra_head=f'<script type="application/ld+json">{schema}</script>')
        os.makedirs(os.path.join(OUT, l["slug"]))
        open(os.path.join(OUT, l["slug"], "index.html"), "w").write(p)

    # ---------- methodology ----------
    vdefs = "".join(f'<div class="vdef">{pill(k)}<p>{esc(d)}</p></div>' for k, (_, _, _, d) in VERDICTS.items())
    method_body = f"""
<header class="pagehead wrap"><h1>How we verify</h1>
<p>“Free” is the most abused word on the internet. Our job is to read the fine print so the word means something again.</p></header>
<main class="wrap"><div class="prose">
<h2>The six verdicts</h2>
{vdefs}
<h2>How we score</h2>
<p>Two numbers accompany every stamp. The <strong>Free Score</strong> (0–100) measures how free it actually is, on a fixed rubric: cards up front, auto-billing, hard time cutoffs, deliberately withheld core features, and paying with your data or attention all cost points. The bands: 90–100 truly free, 70–89 free forever with fair limits, 45–69 a squeezed free tier, 15–44 trial mechanics, below 15 fake or nonexistent.</p>
<p>The <strong>Value</strong> score (0–10) is editorial: how much real-world worth the free offering delivers, anchored to what the paid equivalent costs. A trap trial can still score a few value points — a kept audiobook is a kept audiobook — and a perfectly free tool can score modestly if it does one small job. Rankings on every page sort by Free Score first, value second.</p>
<h2>What we check</h2>
<p>For every listing we answer the same questions: Does it ask for a card before you can start? Does anything bill automatically? Do you need an account at all? What are the real limits of the free version — time, features, storage, usage? And when the price is zero, what is actually paying the bills: ads, your data, upgrade pressure, or genuine goodwill?</p>
<p>Those answers become the Free Facts panel on every page. Alongside it, every page lists in plain terms exactly what the free version includes and exactly what sits behind the paywall — so "free" stops being a vibe and becomes a list. The overall pattern earns the stamp.</p>
<h2>What the stamp means</h2>
<p>A verdict describes the free offering as it is marketed and experienced — not whether the product is good, and not whether paying for it is worth it. Plenty of Trap Trials are excellent products with hostile billing. Plenty of Truly Free tools are clunky. The stamp answers one question only: is it actually free?</p>
<h2>Freshness</h2>
<p>Free tiers change without notice, so every page carries a “last checked” date. If you catch something that's drifted, tell us and we'll re-verify it: <a href="mailto:hello@veri-free.com">hello@veri-free.com</a>.</p>
<h2>Independence</h2>
<p>Nobody pays to change a verdict. If a listing ever carries a paid or affiliate relationship, it will be labeled on that page — and the stamp stays honest either way, because the stamp is the whole point.</p>
</div></main>"""
    p = page_nav("How we verify — Verified Free",
             "The six verdicts, what we check, and why nobody can pay to change a stamp.",
             "/methodology/", method_body)
    os.makedirs(os.path.join(OUT, "methodology"))
    open(os.path.join(OUT, "methodology", "index.html"), "w").write(p)

    # ---------- deals ----------
    deals = data.get("deals", [])
    if deals:
        render_deal = deal_card
        guarantee_names = {"Costco — Risk-Free 100% Satisfaction Guarantee","REI — 100% Satisfaction Guarantee (1 Year for Co-op Members)","Zappos — 365-Day Free Returns","Target — 90 Days (1 Year on Target-Owned Brands)","Patagonia — Ironclad Guarantee (repair first)"}
        regular_deals = [d for d in deals if d["name"] not in guarantee_names]
        guarantee_deals = [d for d in deals if d["name"] in guarantee_names]
        deal_cards = "".join(render_deal(d) for d in regular_deals)
        guarantee_cards = "".join(render_deal(d) for d in guarantee_deals)
        guarantee_section = (f'<div style="max-width:720px;margin-top:10px"><h2 style="margin-top:40px">Generous return guarantees</h2>'
                             f'<p style="color:var(--muted);margin-bottom:6px">Not free — but a real safety net. These retailers stand behind what they sell, so an honest buyer is never stuck with something that failed, didn\'t fit, or disappointed. One principle makes them work: <strong>use them in good faith.</strong> A return guarantee is protection for genuine dissatisfaction, not a free rental service. Wearing something once and sending it back — "wardrobing" — is return fraud; it raises prices for everyone and gets policies tightened or memberships revoked. Buy with confidence, return with honesty.</p>'
                             f'{guarantee_cards}</div>') if guarantee_deals else ""
        deals_body = f"""
<header class="pagehead tight wrap"><h1>Verified Deals &amp; Discounts</h1>
<p>Every deal checked — who qualifies, what you get, and what the fine print hides.</p></header>
<main class="wrap">
<details class="pagenote"><summary>How we verify deals</summary><div class="pn-body">
<p>Each deal is stamped <span class="dbadge verified">VERIFIED</span> (confirmed working), <span class="dbadge seasonal">SEASONAL</span> (real but periodic — watch for it), or <span class="dbadge expired">EXPIRED</span> (was real, no longer available). We check terms and eligibility directly, and publish the caveat alongside the savings, because a discount that surprises you at renewal isn\'t a deal — it\'s a trap with a fuse.</p>
</div></details>
<div style="max-width:720px;padding-bottom:10px">{deal_cards}</div>
{guarantee_section}
<div style="padding-bottom:50px"></div></main>"""
        # ---------- /coupons/ ----------
        coded = [x for x in deals if x.get("code")]
        if coded:
            cards_c = "".join(deal_card(x) for x in coded)
            coup_body = f"""
<header class="pagehead tight wrap"><h1>Coupon Codes</h1>
<p>Codes we have actually checked. Click one to copy it.</p></header>
<main class="wrap">
<details class="pagenote"><summary>Why this page is short</summary><div class="pn-body">
<p>Coupon sites list thousands of codes because listing them costs nothing and a dead code still earns the click. We list a code only when we have confirmed it works, which means there will never be many. A short page of working codes beats a long one of expired ones — the same standard the verdicts are held to.</p>
<p>If a code here has stopped working, tell us and it comes down: <a href="mailto:hello@veri-free.com">hello@veri-free.com</a>.</p>
</div></details>
<div style="max-width:720px;padding-bottom:10px">{cards_c}</div>
<div style="padding-bottom:50px"></div></main>"""
            p_c = page_nav("Verified Coupon Codes — Verified Free",
                           "Coupon codes we have actually checked. Short by design: only codes confirmed to work.",
                           "/coupons/", coup_body)
            os.makedirs(os.path.join(OUT, "coupons"), exist_ok=True)
            open(os.path.join(OUT, "coupons", "index.html"), "w").write(p_c)

        # ---------- /free-consultations/ ----------
        consults = [x for x in deals if x.get("consultation")]
        if consults:
            cards_x = "".join(deal_card(x, cta="Book it →") for x in consults)
            cons_body = f"""
<header class="pagehead tight wrap"><h1>Free Consultations</h1>
<p>Expert time you can book without paying for it — verified, with the catch stated.</p></header>
<main class="wrap">
<details class="pagenote"><summary>What counts as free here</summary><div class="pn-body">
<p>A free consultation is only free if you can leave without owing anything and without having been sold to under pressure. Everything below meets that: government-funded advisers, volunteer professionals, or a business offering a genuine front door.</p>
<p>What we don't list: "free quotes" that are sales calls, timeshare-style presentations where the free hour is the price of admission to a pitch, and anything that needs a card to book. Where a consultation is the front door to a paid service, the card says so.</p>
</div></details>
<div style="max-width:720px;padding-bottom:10px">{cards_x}</div>
<div style="padding-bottom:50px"></div></main>"""
            p_x = page_nav("Free Consultations — Verified Free",
                           "Free expert time — business mentoring, legal answers, tax help and design advice — each verified and with the catch stated.",
                           "/free-consultations/", cons_body)
            os.makedirs(os.path.join(OUT, "free-consultations"), exist_ok=True)
            open(os.path.join(OUT, "free-consultations", "index.html"), "w").write(p_x)

        p = page_nav("Verified Deals & Discounts — Verified Free",
                 "Coupons and discounts that are actually real — verified, with the fine print included.",
                 "/deals/", deals_body)
        os.makedirs(os.path.join(OUT, "deals"))
        open(os.path.join(OUT, "deals", "index.html"), "w").write(p)


    # ---------- /all/ — the directory ----------
    all_body = f"""
<header class="pagehead tight wrap"><h1>Everything we&rsquo;ve checked</h1></header>
<div class="side-legend closed" id="sidepanel">
<div class="sl-tab" title="Verdict definitions and sorting" onclick="document.getElementById('sidepanel').classList.toggle('closed')">Guide</div>
<div class="sl-body">
<h2>Verdicts</h2>
{legend_side}
<div class="sl-divider"></div>
<h2>Sort</h2>
<div class="sl-sorts">
<button class="sortbtn active" data-sort="free">Most free</button>
<button class="sortbtn" data-sort="value">Highest value</button>
<button class="sortbtn" data-sort="name">A–Z</button>
</div>
</div>
</div>
<div class="findbar"><div class="wrap findbar-in">
<div class="searchbar"><input id="q" type="search" placeholder="Search {len(listings)} verified free things…" aria-label="Search listings"><span class="kbd">{len(listings)} verified</span></div>
<div class="vfilters">
<button class="vfilter on" data-v="all">All</button>
<button class="vfilter" data-v="truly">Truly free <i>{truly_n}</i></button>
<button class="vfilter" data-v="forever">Free forever <i>{forever_n}</i></button>
<button class="vfilter" data-v="freeish">Free-ish <i>{squeeze}</i></button>
<button class="vfilter" data-v="trap,fake,notfree">Traps &amp; fakes <i>{traps}</i></button>
</div>
<p class="count" id="count"></p>
</div></div>
<main class="wrap" id="categories">
{sections}
<p class="noresults" id="noresults">Nothing by that name yet. <a href="mailto:hello@veri-free.com">Suggest it</a> and we'll verify it.</p>
</main>"""
    p_all = page_nav(f"All {len(listings)} ‘free’ offers, checked — Verified Free",
                     f"All {len(listings)} listings, searchable and filterable by verdict and category.",
                     "/all/", all_body)
    os.makedirs(os.path.join(OUT, "all"), exist_ok=True)
    open(os.path.join(OUT, "all", "index.html"), "w").write(p_all)

    # ---------- free in real life ----------
    irl = data.get("irl", [])
    if irl:
        sections = ""
        for g in irl:
            cards = "".join(deal_card(i, cta="Official page →") for i in g["items"])
            sections += (f'<section><h2 class="irl-h">{esc(g["group"])}</h2>'
                         f'<p class="irl-blurb">{esc(g["blurb"])}</p>{cards}</section>')
        irl_faq = [
            {"@type": "Question", "name": "What free things can you get in real life?",
             "acceptedAnswer": {"@type": "Answer", "text":
              "Standing offline programmes: national park fee-free days, museum free days through "
              "Bank of America's Museums on Us and library museum passes, birthday rewards from "
              "loyalty programmes, kids-eat-free nights, USDA summer meals for children, "
              "sliding-scale community health centers, and retail price adjustments you can claim "
              "after buying."}},
            {"@type": "Question", "name": "Are birthday freebies real?",
             "acceptedAnswer": {"@type": "Answer", "text":
              "Yes. They are attached to loyalty programmes rather than to restaurants, so you join "
              "the programme, put your birth date in the profile, and the reward posts in your "
              "birthday month. Join at least 30 days ahead — most programmes require that. Rewards "
              "usually expire within days and most need another purchase to redeem."}},
            {"@type": "Question", "name": "When are national parks free in 2026?",
             "acceptedAnswer": {"@type": "Answer", "text":
              "The National Park Service waives entrance fees on announced days. The remaining 2026 "
              "dates are August 25, September 17, October 27 and November 11. The waiver covers the "
              "entrance fee only — camping, tours and timed-entry reservations still apply."}}]
        irl_schema = json.dumps({"@context": "https://schema.org", "@graph": [
            {"@type": "FAQPage", "mainEntity": irl_faq},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": "Free in Real Life",
                 "item": f"{DOMAIN}/free-in-real-life/"}]}]}, ensure_ascii=False)
        irl_body = f"""
<header class="pagehead tight wrap"><h1>Free in Real Life</h1>
<p>Standing programmes only — free things that are true all year, not this week's circular.</p></header>
<main class="wrap">
<details class="pagenote"><summary>What's here, and what isn't</summary><div class="pn-body">
<p>Everything below is a <strong>standing programme</strong>: published dates, a public policy, or a federal entitlement. Those can be verified once and stay verified, which is the only way a "last checked" date means anything.</p>
<p>What we deliberately don't list: weekly store circulars, flash sales, free-sample-of-the-day sites, and sweepstakes. Those change daily and by zip code, so any page claiming to have checked them is guessing — and that corner of the web is already wall-to-wall affiliate spam with dead links. We'd rather cover less and be right.</p>
<p>Where a thing genuinely varies by location — kids-eat-free nights, library passes — we say so and tell you how to check yours, instead of printing a national list that's wrong in half the country.</p>
</div></details>
<div class="irl-wrap">{sections}</div>
<div style="padding-bottom:50px"></div></main>"""
        p = page_nav("Free in Real Life — Verified Free",
                     "Free things offline that are true all year: park and museum free days, birthday rewards, kids eat free, health programmes, and retail refunds you can claim.",
                     "/free-in-real-life/", irl_body,
                     extra_head=f'<script type="application/ld+json">{irl_schema}</script>')
        os.makedirs(os.path.join(OUT, "free-in-real-life"))
        open(os.path.join(OUT, "free-in-real-life", "index.html"), "w").write(p)

    # ---------- when to buy ----------
    wtb_body = """
<header class="pagehead wrap"><h1>When to Buy</h1>
<p>Prices don't fall at random — they fall on a schedule, and most of what looks like a sale isn't one. This is the timing map: when things actually get cheaper, when to upgrade, and when the urgency is manufactured.</p></header>
<main class="wrap"><div class="prose" style="max-width:720px">

<h2>The one rule underneath all of this</h2>
<p>A discount only saves you money on something you were already going to buy. Everything below assumes you need the thing. If the sale is what created the need, the sale won a customer and you lost a hundred dollars — which is the same trick every "free" trial on this site is running, just with a price tag attached.</p>

<h2>When do I upgrade my phone?</h2>
<p><b>The honest answer: when it stops doing its job, not when a new one appears.</b> Phones now hold up for four to six years. The signals that actually justify an upgrade are the battery no longer lasting your day, the phone dropping out of security updates, or something breaking that costs more to repair than the phone is worth. "The new one is out" is not a signal — it's a calendar event a marketing department scheduled.</p>
<p><b>If you do upgrade, don't take the carrier's "free phone."</b> It is the single most convincing fake-free offer in consumer tech, and the math is brutal: a "free" flagship on AT&T's required $75.99/month unlimited plan runs about $2,735 over the 36-month credit term, plus taxes on full retail and a $35 activation fee, both due upfront. The phone was never discounted. The credits are a promise that evaporates the moment you leave, while the unpaid device balance comes due. <a href="/is-free-phone-carrier-deals-actually-free/">The full breakdown is here.</a></p>
<p><b>The cheaper path, almost always:</b> buy the phone unlocked (or buy last year's model, which drops 20–30% the week the new one lands), pair it with a prepaid or MVNO plan, and sell your old phone privately — buyback services and Swappa routinely pay around 30% more than carrier trade-in credit.</p>
<p><b>The best time to buy a phone</b> is the week after a new model launches, when the previous generation drops hard and is still supported for years. September–October for iPhones; January–February for Samsung Galaxy.</p>

<h2>The real price-drop calendar</h2>
<p>These are structural — they repeat every year because of inventory cycles and product launches, not because a retailer is feeling generous.</p>
<ul>
<li><b>TVs</b> — late January and early February, ahead of the Super Bowl, and again in the fall when new model years land. Black Friday TV "doorbusters" are frequently made-for-sale models with lower specs; compare the model number, not the discount.</li>
<li><b>Phones</b> — the week a new flagship launches, the previous generation falls 20–30% and stays supported for years.</li>
<li><b>Laptops</b> — back-to-school (July–August) and the post-holiday clearance in January.</li>
<li><b>Mattresses and furniture</b> — the long holiday weekends (Presidents' Day, Memorial Day, Labor Day) are genuinely when the discounting happens.</li>
<li><b>Winter clothing</b> — late January and February. Summer clothing — late August.</li>
<li><b>Fitness equipment and gym memberships</b> — the January rush ends by mid-February, and that's when the pressure to sign fades and the offers improve.</li>
<li><b>Last year's car models</b> — end of the model year (late summer through fall), and the last days of any month, when quotas close.</li>
</ul>

<h2>The "sale" patterns that aren't</h2>
<ul>
<li><b>The inflated original price.</b> A "was $199, now $99" item that has never sold at $199. Check the price history before believing the discount — the anchor is the product.</li>
<li><b>The countdown timer.</b> Manufactured urgency. If the offer genuinely expires in 20 minutes, it will be back next month under a different banner.</li>
<li><b>The bundle you didn't want.</b> "Free" accessories that push you to a higher tier cost more than buying the thing you actually needed.</li>
<li><b>The doorbuster spec-down.</b> Especially in TVs and laptops: a model manufactured specifically for the sale, with a slower panel or less RAM, at a price that looks like a steal against a model it isn't.</li>
</ul>

</div></main>"""
    p = page_nav("When to Buy — Verified Free",
                 "When prices actually drop, when to upgrade your phone, and which sales are manufactured. The timing map, without the hype.",
                 "/when-to-buy/", wtb_body)
    os.makedirs(os.path.join(OUT, "when-to-buy"), exist_ok=True)
    open(os.path.join(OUT, "when-to-buy", "index.html"), "w").write(p)


    # ---------- privacy ----------
    privacy_body = """
<header class="pagehead wrap"><h1>Privacy</h1>
<p>The short version: we count visits, we don't build profiles, and we never sell anything about you.</p></header>
<main class="wrap"><div class="prose" style="max-width:720px;padding-bottom:50px">
<h2>What we measure</h2>
<p>To understand which pages are useful, we keep a simple count of page views. For each view we record the page visited, the site that referred you (just the domain, like "google.com" — never the full link), your country, and whether you're on desktop, tablet, or mobile. That's it.</p>
<h2>What we don't do</h2>
<p>No cookies. No advertising trackers. We do not store your IP address or your full browser details — they're used for a moment to filter out bots and then discarded, never saved and never sent anywhere. We can't identify you, we don't follow you across other websites, and there's nothing here to sell because we don't collect anything worth selling.</p>
<h2>How the counting works</h2>
<p>To tell a returning reader from a brand-new one within a single day, our system creates a scrambled, one-way code from technical details of the request. It resets every day and can't be reversed to identify anyone — it's the same cookieless method privacy-first tools like Plausible and Fathom use. These aggregate counts are handled by DreamSite Design, the studio that builds and operates this site.</p>
<h2>Questions</h2>
<p>Email <a href="mailto:hello@veri-free.com">hello@veri-free.com</a> and we'll answer plainly.</p>
</div></main>"""
    p = page_nav("Privacy — Verified Free",
                 "How Verified Free counts visits: no cookies, no profiles, no selling your data.",
                 "/privacy/", privacy_body)
    os.makedirs(os.path.join(OUT, "privacy"), exist_ok=True)
    open(os.path.join(OUT, "privacy", "index.html"), "w").write(p)

    # ---------- changelog ----------
    changelog = data.get("changelog", [])
    if changelog:
        changelog.sort(key=lambda x: x["date"], reverse=True)
        ch_items = ""
        for ch in changelog:
            direction = "down" if any(w in ch["change"].lower() for w in ["killed","cut","restricted","suspended","breached","ads added","left","rules"]) else "up" if any(w in ch["change"].lower() for w in ["added","expanded","improved"]) else "note"
            tag = f'<span class="chtag {direction}">{"↓" if direction=="down" else "↑" if direction=="up" else "•"} {ch.get("from","—")} → {ch.get("to","—")}</span>' if ch.get("from") and ch.get("to") and ch["from"] != "—" else ""
            ch_items += (f'<div class="chlog">'
                         f'<span class="chdate">{esc(ch["date"])}</span>{tag}'
                         f'<p class="chbody"><strong>{esc(ch["item"])}:</strong> {esc(ch["change"])}. {esc(ch["detail"])}</p>'
                         f'</div>')
        ch_body = (f'<header class="pagehead wrap"><h1>What Just Changed</h1>'
                   f'<p>Free tiers change without warning. This is the record — every downgrade, every killed free plan, every quiet cut. Bookmark this page.</p></header>'
                   f'<main class="wrap" style="max-width:720px;padding-bottom:50px">{ch_items}</main>')
        p = page_nav("What Just Changed — Verified Free",
                     "A living changelog of free tier changes: downgrades, killed plans, and quiet cuts, tracked.",
                     "/changelog/", ch_body)
        os.makedirs(os.path.join(OUT, "changelog"), exist_ok=True)
        open(os.path.join(OUT, "changelog", "index.html"), "w").write(p)

    # build by_name for comparisons
    by_name = {l["name"]: l for l in listings}

    # ---------- comparison pages ----------
    comparisons = data.get("comparisons", [])
    if comparisons:
        comp_css = """<style>
.vs-table{width:100%;border-collapse:collapse;margin:22px 0;background:var(--card);border:1.5px solid var(--line);border-radius:12px;overflow:hidden}
.vs-table th{font-family:"IBM Plex Mono",monospace;font-size:11.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding:12px 14px;text-align:left;border-bottom:2px solid var(--ink);background:var(--paper)}
.vs-table td{padding:12px 14px;font-size:14.5px;border-top:1px solid var(--line);vertical-align:top}
.vs-table tr:first-child td{border-top:0}
.vs-table td:first-child{font-weight:600;white-space:nowrap;width:140px}
.vs-table .score-cell{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:20px}
.vs-verdict{border:2px solid var(--brand);border-radius:12px;background:#E4F2EA;padding:18px 20px;margin:26px 0}
.vs-verdict h2{font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--brand);margin:0 0 8px}
.vs-verdict h2::before{content:"✓ "}
.vs-verdict p{margin:0;font-size:15.5px;line-height:1.6}
.comp-nav{margin:22px 0 0;display:flex;flex-wrap:wrap;gap:8px}
.comp-nav a{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;text-decoration:none;border:1.5px solid var(--line);border-radius:7px;padding:6px 12px;color:var(--muted)}
.comp-nav a:hover{border-color:var(--brand);color:var(--brand)}
</style>"""
        for comp in comparisons:
            items = [by_name[n] for n in comp["items"] if n in by_name]
            if not items: continue
            # Build comparison table
            headers = "".join(f"<th>{favicon(it['url'], override=it.get('favicon_url'))} {esc(it['name'])}</th>" for it in items)
            def row(label, fn):
                cells = "".join(f"<td>{fn(it)}</td>" for it in items)
                return f"<tr><td>{label}</td>{cells}</tr>"
            rows = ""
            rows += row("Verdict", lambda it: pill(it["verdict"]))
            rows += row("Free Score", lambda it: f'<span class="score-cell" style="color:{score_color(it["free_score"])}">{it["free_score"]}</span>/100')
            rows += row("Value", lambda it: f'<span class="score-cell" style="color:{score_color(it["value_score"]*10)}">{it["value_score"]}</span>/10')
            rows += row("Card needed", lambda it: esc(it["card"]))
            rows += row("Account", lambda it: esc(it["account"]))
            rows += row("Limits", lambda it: esc(it["limits"]))
            rows += row("You get", lambda it: esc(it.get("free_includes",[""])[0]))
            rows += row("Real cost", lambda it: esc(it["realcost"]))
            rows += row("Full review", lambda it: f'<a href="/{it["slug"]}/">Read →</a>')

            table = f'<div style="overflow-x:auto"><table class="vs-table"><tr><th></th>{headers}</tr>{rows}</table></div>'
            verdict_box = f'<div class="vs-verdict"><h2>Our pick</h2><p>{esc(comp["verdict"])}</p></div>'

            # Links to other comparisons
            other_links = "".join(f'<a href="/compare/{esc(c["slug"])}/">{esc(c["title"])}</a>'
                                  for c in comparisons if c["slug"] != comp["slug"])
            comp_nav = f'<div class="comp-nav"><span style="font-family:IBM Plex Mono;font-size:11.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);padding:6px 0">More comparisons</span>{other_links}</div>'

            body = (f'{comp_css}'
                    f'<header class="pagehead wrap"><h1>{esc(comp["title"])}</h1>'
                    f'<p>{esc(comp["desc"])}</p></header>'
                    f'<main class="wrap" style="max-width:900px;padding-bottom:50px">'
                    f'<p style="font-size:17px;line-height:1.6;margin:0 0 10px">{esc(comp["intro"])}</p>'
                    f'{table}{verdict_box}{comp_nav}</main>')
            p = page_nav(f'{comp["title"]} — Verified Free', comp["desc"],
                         f'/compare/{comp["slug"]}/', body)
            os.makedirs(os.path.join(OUT, "compare", comp["slug"]), exist_ok=True)
            open(os.path.join(OUT, "compare", comp["slug"], "index.html"), "w").write(p)

        # Comparison index page
        comp_links = "".join(
            f'<a class="card" href="/compare/{esc(c["slug"])}/" style="text-decoration:none">'
            f'<h2 class="cmp-title">{esc(c["title"])}</h2><p class="cost">{esc(c["desc"])}</p></a>'
            for c in comparisons)
        comp_index_body = (f'<header class="pagehead wrap"><h1>Comparisons</h1>'
                           f'<p>Side-by-side verdicts on the free alternatives that matter most.</p></header>'
                           f'<main class="wrap"><div class="grid">{comp_links}</div></main>')
        comp_urls = [f"{DOMAIN}/compare/"]
        for c in comparisons: comp_urls.append(f"{DOMAIN}/compare/{c['slug']}/")
        p = page_nav("Comparisons — Verified Free", "Side-by-side comparisons of free tools, streaming services, and more.", "/compare/", comp_index_body)
        os.makedirs(os.path.join(OUT, "compare"), exist_ok=True)
        open(os.path.join(OUT, "compare", "index.html"), "w").write(p)

    # ---------- for businesses / submit ----------
    submit_body = """
<header class="pagehead wrap"><h1>Get verified</h1>
<p>Two ways to use Verified Free: request a verdict on anything, or get your business's free offering stamped.</p></header>
<main class="wrap"><div class="prose">

<h2>Request a verdict — anyone</h2>
<p>Found a "free" offer you don't trust? Want us to check something before you sign up? Drop it here.</p>
<form class="reqform" id="reqform" name="verify-request" method="POST" action="/submit/thanks/" data-netlify="true" netlify-honeypot="bot-field">
<input type="hidden" name="form-name" value="verify-request">
<p style="display:none"><label>Leave this empty: <input name="bot-field"></label></p>
<label for="req-name">What should we verify?</label>
<input type="text" id="req-name" name="what" required placeholder="App, service, or offer name">
<label for="req-url">Link (if you have one)</label>
<input type="url" id="req-url" name="link" placeholder="https://...">
<label for="req-note">What made you suspicious? (optional)</label>
<textarea id="req-note" name="note" placeholder="E.g. 'says free but asked for my card…'"></textarea>
<button type="submit">Submit for verification →</button>
<p class="ty">Request received — we'll verify it and publish the verdict.</p>
<p class="terr" style="display:none;font-size:15px;color:#C0392B;font-weight:600;padding:16px 0">Couldn't send just now — try again, or email <a href="mailto:hello@veri-free.com">hello@veri-free.com</a>.</p>
</form>
<script>
(function(){
  var f=document.getElementById('reqform');
  if(!f)return;
  f.addEventListener('submit',function(e){
    e.preventDefault();
    var btn=f.querySelector('button[type=submit]');
    btn.disabled=true;
    fetch('/submit/',{method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body:new URLSearchParams(new FormData(f)).toString()})
      .then(function(r){
        if(!r.ok)throw 0;
        f.querySelector('.ty').style.display='block';
        f.querySelector('.terr').style.display='none';
        f.reset();btn.disabled=false;
      })
      .catch(function(){
        f.querySelector('.terr').style.display='block';
        btn.disabled=false;
      });
  });
})();
</script>

<h2>For businesses — get your free offering stamped</h2>
<p>If your business leads with something genuinely free — a tool, a scan, a calculator, a real free tier — a verified listing puts it in front of people actively searching for free options.</p>
<p>What you get: a full verdict page with scores, exactly what users get free, drawbacks stated plainly, and the smart way to use it. Pages rank for "is [your product] actually free" — the question your customers are already typing.</p>
<p>How it works: email us the link. Same rubric as every listing on this site. If it's a trap trial, we stamp it a trap trial — that severity is precisely why a good stamp means something.</p>
<p><a class="visit" href="mailto:hello@veri-free.com?subject=Verify%20our%20free%20offering">Submit your free offering →</a></p>

<div class="badge-section">
<h2>The Verified Free badge</h2>
<p>Listings that earn a Truly Free or Free Forever stamp can embed the badge on their own site — a trust signal that links back to their verified page.</p>
<p>What it looks like:</p>
<a class="badge-preview" href="/">
<svg viewBox="0 0 20 20" fill="none"><rect x="1" y="1" width="18" height="18" rx="5" stroke="#0E7B47" stroke-width="2"/><path d="M6 10.5L9 13.5l5-6" stroke="#0E7B47" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
Verified Free
</a>
<p style="margin-top:16px">Embed code (click to copy):</p>
<div class="embed-box" onclick="navigator.clipboard.writeText(this.innerText.replace('Copied!','').trim());this.querySelector('.copied').style.display='block';setTimeout(()=>this.querySelector('.copied').style.display='none',1500)">
&lt;a href="https://veri-free.com" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:6px;border:2px solid #0E7B47;border-radius:8px;padding:6px 12px;font-family:monospace;font-weight:600;font-size:13px;color:#0E7B47;text-decoration:none;background:#E4F2EA"&gt;&lt;svg width="18" height="18" viewBox="0 0 20 20" fill="none"&gt;&lt;rect x="1" y="1" width="18" height="18" rx="5" stroke="#0E7B47" stroke-width="2"/&gt;&lt;path d="M6 10.5L9 13.5l5-6" stroke="#0E7B47" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/&gt;&lt;/svg&gt;Verified Free&lt;/a&gt;
<span class="copied">Copied!</span>
</div>
<p>Businesses with verified listings get a custom badge linking directly to their verdict page. <a href="mailto:hello@veri-free.com?subject=Badge%20request">Email us</a> for the personalized embed code.</p>
</div>

<h2>The rules</h2>
<p>Verdicts and scores are never for sale. Any commercial relationship is disclosed on the listing page. Featured placement for verified listings is coming; stamps will never be part of it. Listings are re-checked, and downgrades publish as readily as the original verdict.</p>
</div></main>"""
    p = page_nav("Get verified — Verified Free",
             "Request a verdict on any 'free' offer, or get your business's free tool verified with an embeddable trust badge.",
             "/submit/", submit_body)
    os.makedirs(os.path.join(OUT, "submit"))
    open(os.path.join(OUT, "submit", "index.html"), "w").write(p)

    # thanks page — non-JS fallback target for the verify-request form
    thanks_body = ('<main class="wrap"><header class="pagehead"><h1>Request received</h1>'
                   '<p>Thanks — it\'s in the verification queue. If it checks out (or doesn\'t), '
                   'the verdict gets published; watch the <a href="/changelog/">changelog</a>.</p>'
                   '<p><a href="/">← Back to the rankings</a></p></header></main>')
    p = page_nav("Request received — Verified Free", "Your verification request was received.",
                 "/submit/thanks/", thanks_body, extra_head='<meta name="robots" content="noindex">')
    os.makedirs(os.path.join(OUT, "submit", "thanks"), exist_ok=True)
    open(os.path.join(OUT, "submit", "thanks", "index.html"), "w").write(p)

    # ---------- extras ----------
    open(os.path.join(OUT, "favicon.svg"), "w").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect x="4" y="4" width="56" height="56" rx="14" fill="#0E7B47"/><path d="M18 33.5 28 43l18-21" fill="none" stroke="#F7F8F5" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")

    # Copy brand assets
    import shutil
    ASSETS = os.path.join(os.path.dirname(OUT), "assets")
    if os.path.isdir(ASSETS):
        for f in os.listdir(ASSETS):
            src_f = os.path.join(ASSETS, f)
            if os.path.isfile(src_f):
                shutil.copy2(src_f, os.path.join(OUT, f))
            elif os.path.isdir(src_f):
                shutil.copytree(src_f, os.path.join(OUT, f), dirs_exist_ok=True)
    urls = [f"{DOMAIN}/", f"{DOMAIN}/all/", f"{DOMAIN}/methodology/", f"{DOMAIN}/submit/", f"{DOMAIN}/deals/", f"{DOMAIN}/coupons/", f"{DOMAIN}/free-consultations/", f"{DOMAIN}/free-in-real-life/", f"{DOMAIN}/compare/", f"{DOMAIN}/changelog/", f"{DOMAIN}/when-to-buy/", f"{DOMAIN}/privacy/"] + [f"{DOMAIN}/{lg}/" for lg in EXTRA_LANGS] + [f"{DOMAIN}/{c}/" for c in CATS] + [f"{DOMAIN}/{lg}/{c}/" for lg in EXTRA_LANGS for c in CATS] + [f"{DOMAIN}/{l['slug']}/" for l in listings]
    if comparisons:
        urls.extend(comp_urls[1:])  # skip /compare/ already added
    from datetime import date
    today = date.today().isoformat()
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
              "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n"
    open(os.path.join(OUT, "sitemap.xml"), "w").write(sitemap)
    body404 = '<main class="wrap"><header class="pagehead"><h1>Not found</h1><p>That page doesn\'t exist — but the verdicts do. <a href="/">Search the full list</a>.</p></header></main>'
    open(os.path.join(OUT, "404.html"), "w").write(page_nav("Not found — Verified Free", "Page not found.", "/404.html", body404))

    print(f"Built {len(listings)} listings, {len(CATS)} categories → {OUT}")
    _v = [l for l in listings if l.get("verified")]
    print(f"  individually verified: {len(_v)}/{len(listings)} "
          f"({len(listings) - len(_v)} on the site-wide date)")

if __name__ == "__main__":
    build()
