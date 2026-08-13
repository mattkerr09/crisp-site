#!/usr/bin/env bash
# Re-shoot the hero screenshot for crispvideo.app.
#
# WHY THIS EXISTS
#
# /img-app@2x.png has been a baked PNG of v0.1.0 build 769 since 7 August. The app
# now ships 0.1.83x. It is the most prominent visual on the homepage and it shows
# an eight-month-old build, which no text gate can catch because a picture is not
# text. It has sat on Matthew's list for twenty-two loop ticks, described each time
# as "a two-minute job", which is true and is exactly why it kept not happening:
# the two minutes were spent remembering the exact dimensions.
#
# So the dimensions are in here now, and the whole thing is one command.
#
# WHAT WAS TRIED AND DID NOT WORK, so nobody repeats it
#
# Fully automating this from a background agent does NOT work, and the reason is
# worth writing down. The mechanics are fine: System Events can read and set
# Crisp's window bounds, and `screencapture -R` on a Retina display captures a
# 900x614 logical region as exactly 1800x1228 — verified. The part that fails is
# z-order. `screencapture -R` captures a SCREEN REGION, not a window, so whatever
# is visually on top gets captured. Two attempts to bring Crisp forward with
# `activate` and `set frontmost to true` both came back with the frontmost app's
# window instead. Making that reliable means taking over the screen of whoever is
# using the machine, which is not a thing to do to someone mid-session.
#
# Hence: a script a human runs, not a job an agent runs.
#
#   cd site && ./tools/shoot-hero.sh
#
# Have Crisp open with a clip loaded and something worth looking at on screen
# before running it. Everything after that is handled.
set -euo pipefail

cd "$(dirname "$0")/.."
X=60; Y=80; W=900; H=614          # logical points; 2x Retina gives 1800x1228
OUT2X="img-app@2x.png"
OUT1X="img-app.png"

command -v screencapture >/dev/null || { echo "no screencapture on this machine" >&2; exit 1; }
pgrep -f '/Applications/Crisp.app' >/dev/null || {
  echo "Crisp is not running. Open it, load a clip, then run this again." >&2; exit 1; }

echo "==> bringing Crisp forward and sizing its window to ${W}x${H}"
osascript <<AS
tell application id "host.crisp.desktop" to activate
delay 1
tell application "System Events" to tell process "crisp"
  set frontmost to true
  set position of window 1 to {$X, $Y}
  set size of window 1 to {$W, $H}
end tell
AS

# Long enough for the window to settle and repaint after the resize. A capture
# taken too early catches a half-laid-out window, which looks like a rendering bug
# in the product rather than a timing bug in this script.
echo "==> waiting for the window to settle"
sleep 3

echo "==> capturing"
screencapture -x -R${X},${Y},${W},${H} "$OUT2X"

python3 - "$OUT2X" "$OUT1X" <<'PY'
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src)
if im.size != (1800, 1228):
    raise SystemExit(
        f"FAIL: captured {im.size}, expected (1800, 1228).\n"
        "  On a non-Retina display a 900x614 region captures 1:1, which is half\n"
        "  the resolution the site needs. Run this on the Retina display.")
im.resize((900, 614), Image.LANCZOS).save(dst, optimize=True)
print(f"  {src}  {im.size[0]}x{im.size[1]}")
print(f"  {dst}  900x614")
PY

echo
echo "==> LOOK AT BOTH FILES BEFORE COMMITTING."
echo "    This captures a screen region, so anything overlapping Crisp lands in the"
echo "    shot. The previous hero was wrong for eight months because nobody looked;"
echo "    do not replace it with a picture of a notification banner."
