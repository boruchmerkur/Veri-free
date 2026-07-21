@echo off
REM ── Verified Free — one-click build (Windows) ───────────────────────────
REM Double-click this file. It installs Pillow, builds the brand sprite,
REM regenerates the site into .\site\, and stops so you can zip and deploy.

echo.
echo  [1/3] Installing Pillow...
python -m pip install pillow --quiet
if errorlevel 1 python3 -m pip install pillow --quiet

echo  [2/3] Building brand sprite (downloads ~140 icons, first run only)...
python selfhost_favicons.py
if errorlevel 1 python3 selfhost_favicons.py

echo  [3/3] Generating site...
python generate.py
if errorlevel 1 python3 generate.py

echo.
echo  ================================================================
echo   DONE. Now zip the CONTENTS of the "site" folder
echo   (not the folder itself) and drag it to Netlify Drop.
echo  ================================================================
echo.
pause
