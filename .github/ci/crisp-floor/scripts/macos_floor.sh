#!/bin/bash
# The oldest macOS the app at $1 can actually run on: the HIGHEST `minos` any of its Mach-O files
# declares, as a major version ("26"). With --full, the whole version ("14.4"), which is what the
# release floor gate (scripts/check_macos_floor.py) compares: a dylib built for 14.4 does not load
# on 14.0, and a major-only answer calls both "14".
#
# ⚠️ NOT LSMinimumSystemVersion. That is what the bundle DECLARES, and it said 12.0 while 79 of the
# binaries behind it needed 26 — macOS checks only the front door, so a Monterey buyer could pay,
# launch, and watch the backend fail. The site's promise is sourced from the binaries for that
# reason (ops/facts.tsv `crisp-min-macos`, the same command as below); the GitHub release page was
# still TYPED as "macOS 12+" in publish_release.sh, and said so on every release after the site
# was corrected. One reader for both, so the two cannot disagree again.
#
# ⚠️ EVERY REGULAR FILE, NOT ONLY THE EXECUTABLE ONES (2026-10-19). This used to sweep
# `find -perm +111`, and 17 of the 84 Mach-O files in the installed 1.0.1540 are NOT executable:
# every ffmpeg dylib in Contents/Resources/crisp/libs (libavcodec, libavutil, libx264, libssl…),
# mode 644. dyld loads a dylib whatever its mode, so they count. They happened to sit at 26 beside
# ffmpeg itself, so the answer was right by luck; the day ffmpeg and ffprobe are rebuilt for 14 and
# one dylib is not, the exec-only sweep says "14" while ffmpeg cannot load on 14. 149 files in the
# whole bundle, so reading them all costs about a second.
#
# ⚠️ EVERY SLICE. A universal file has one LC_BUILD_VERSION per architecture; the highest counts.
#
# Fails closed: no Mach-O found, or no minos read, is an error, never a default.
set -u
FULL=0
if [ "${1:-}" = "--full" ]; then FULL=1; shift; fi
APP="${1:?usage: macos_floor.sh [--full] path/to/Crisp.app}"
[ -d "$APP/Contents" ] || { echo "✗ no app bundle at $APP" >&2; exit 1; }
HIGHEST="$(find "$APP" -type f 2>/dev/null | while read -r f; do
  file -b "$f" 2>/dev/null | grep -q Mach-O && vtool -show-build "$f" 2>/dev/null | awk '/minos/{print $2}'
done | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)"
[ -n "$HIGHEST" ] || { echo "✗ read no minos from any Mach-O file in $APP" >&2; exit 1; }
if [ "$FULL" = 1 ]; then echo "$HIGHEST"; else echo "${HIGHEST%%.*}"; fi
