VERIFIED FREE — SOURCE PROJECT
==============================

WINDOWS — EASIEST PATH
----------------------
Just double-click  BUILD.bat
It installs Pillow, builds the sprite, and regenerates the site.
Then zip the CONTENTS of the site\ folder and drag to Netlify Drop.


WINDOWS — MANUAL (PowerShell)
-----------------------------
Note: "pip" alone may not be on your PATH. Always go through Python:

    cd path\to\this\folder
    python3 -m pip install pillow
    python3 selfhost_favicons.py
    python3 generate.py

Then zip the CONTENTS of site\ and deploy.


WHAT EACH FILE DOES
-------------------
generate.py           Builds the whole site into .\site\  (run this after any change)
listings.json         All 130 listings, 34 deals, comparisons, changelog. Edit here.
selfhost_favicons.py  Downloads brand icons and packs them into ONE sprite image.
                      Turns 140 image requests into 1. Run once, then re-run only
                      when you add listings with new domains.
assets\               Icons, favicons, og image, and _headers (security + framing).
                      Everything here is copied into the build automatically.
BUILD.bat             Windows one-click: does all three steps above.


NORMAL WORKFLOW AFTER THIS
--------------------------
1. Edit listings.json
2. python3 generate.py
3. Zip contents of site\
4. Drag to Netlify Drop

You only need selfhost_favicons.py again if you add a brand-new domain.


IF THE SPRITE SCRIPT FAILS
--------------------------
Nothing breaks. The generator falls back to loading brand icons from
Google's favicon service, exactly as the site does now. You just don't
get the speed win.


VERIFY THE SPRITE WORKED
------------------------
After running both scripts, check site\index.html:

    findstr /C:"s2/favicons" site\index.html   -> should find NOTHING
    findstr /C:"fav spr"     site\index.html   -> should find matches

If s2/favicons is still there, the sprite didn't build — look for
FAILED lines in the selfhost_favicons.py output.
