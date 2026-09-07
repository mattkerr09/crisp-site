#!/usr/bin/env python3
"""Give every sitemap entry a <lastmod> that is true, taken from git rather than typed.

WHY. Before this, 8 of 119 entries carried a lastmod and all eight said 2026-07-28 — a date
typed once and never revisited, which is worse than none: a crawler that learns a site's lastmod
is decorative stops reading it. The other 111 said nothing at all, so nothing on this site told
a crawler which of 119 pages had actually changed.

The honest answer is already recorded: the last commit that touched the page's index.html. This
site is hand-written, with no build step stamping anything into the output, so a commit to a page
IS a change to what a reader sees — which is exactly what makes the git date usable here and is
not true of a generated site (see the CEO's honest-dates entry in ~/ops/UPGRADES.md, where a
build clock was rewriting every page's date on every build).

Idempotent by construction: it recomputes from git and rewrites, so running it twice leaves the
file byte-identical. Run it after adding or editing pages:

    python3 _tools/sitemap_dates.py          # rewrite sitemap.xml
    python3 _tools/sitemap_dates.py --check  # exit 1 if any entry is stale (for a gate)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
SITEMAP = SITE / "sitemap.xml"
PREFIX = "https://crispvideo.app/"


def page_for(loc: str) -> Path | None:
    rel = loc[len(PREFIX):] if loc.startswith(PREFIX) else loc
    p = SITE / rel / "index.html" if rel else SITE / "index.html"
    return p if p.is_file() else None


def last_changed(page: Path) -> str | None:
    """The date of the last commit touching this page, or None if git cannot say.

    None is deliberate: an uncommitted page has no honest date, and inventing today's would be
    the exact decorative lastmod this file exists to remove."""
    out = subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "--", str(page)],
                         cwd=SITE, capture_output=True, text=True).stdout.strip()
    return out or None


def rewrite(text: str) -> tuple[str, list[str]]:
    changed: list[str] = []

    def one(m: re.Match) -> str:
        loc = m.group("loc")
        page = page_for(loc)
        if page is None:
            return m.group(0)
        date = last_changed(page)
        if date is None:
            return m.group(0)
        old = m.group("lastmod")
        if old == date:
            return m.group(0)
        changed.append(f"{loc} {old or '(none)'} -> {date}")
        rest = m.group("rest")
        return f"<url><loc>{loc}</loc><lastmod>{date}</lastmod>{rest}</url>"

    pattern = re.compile(
        r"<url><loc>(?P<loc>[^<]+)</loc>"
        r"(?:<lastmod>(?P<lastmod>[^<]*)</lastmod>)?"
        r"(?P<rest>.*?)</url>")
    return pattern.sub(one, text), changed


def main() -> int:
    text = SITEMAP.read_text()
    out, changed = rewrite(text)
    total = out.count("<lastmod>")
    urls = out.count("<loc>")
    if "--check" in sys.argv:
        if changed:
            print(f"sitemap lastmod is stale on {len(changed)} entries:")
            for c in changed[:20]:
                print("  " + c)
            return 1
        print(f"sitemap lastmod is current on all {total}/{urls} entries")
        return 0
    SITEMAP.write_text(out)
    print(f"sitemap: {len(changed)} entries updated; {total}/{urls} now carry a lastmod")
    for c in changed[:10]:
        print("  " + c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
