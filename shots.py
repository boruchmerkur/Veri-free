#!/usr/bin/env python3
"""Screenshot pages of the live site (or any URL) to PNG.

The in-app browser can only screenshot when its pane is actually displayed, so
this drives the installed Chrome through Playwright instead — works headless
and needs nobody watching.

    python3 shots.py                         # the standard set, desktop
    python3 shots.py --mobile                # 390x844 instead
    python3 shots.py /business/ /now/        # specific paths
    python3 shots.py --full /business/       # full-page rather than viewport
    python3 shots.py --base http://localhost:8080 /   # a local build

Uses channel="chrome" so it reuses the browser already on this machine rather
than downloading Playwright's own.
"""
import os
import sys

from playwright.sync_api import sync_playwright

BASE = "https://veri-free.com"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
DEFAULT = ["/", "/business/", "/now/", "/coupons/", "/free-consultations/"]
DESKTOP = {"width": 1440, "height": 900}
MOBILE = {"width": 390, "height": 844}


def capture(paths, base=BASE, mobile=False, full=False):
    os.makedirs(OUT, exist_ok=True)
    size = MOBILE if mobile else DESKTOP
    made = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(viewport=size, device_scale_factor=2,
                                  is_mobile=mobile, has_touch=mobile)
        page = ctx.new_page()
        for path in paths:
            url = path if path.startswith("http") else base.rstrip("/") + path
            try:
                page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1200)          # let feed art settle
            name = (path.strip("/").replace("/", "-") or "home") + \
                   ("-mobile" if mobile else "") + ".png"
            dest = os.path.join(OUT, name)
            page.screenshot(path=dest, full_page=full)
            made.append(dest)
            print(f"  {size['width']}x{size['height']}{' full' if full else ''}  {url}\n      -> {dest}")
        browser.close()
    return made


if __name__ == "__main__":
    a = sys.argv[1:]
    mobile = "--mobile" in a
    full = "--full" in a
    base = BASE
    if "--base" in a:
        base = a[a.index("--base") + 1]
        a = [x for i, x in enumerate(a) if i not in (a.index("--base"), a.index("--base") + 1)]
    paths = [x for x in a if not x.startswith("--") and x != base] or DEFAULT
    capture(paths, base=base, mobile=mobile, full=full)
