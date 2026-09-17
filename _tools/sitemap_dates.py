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
import subprocess  # noqa: F401 — kept for callers/tests that stub it
import sys
from pathlib import Path

import page_dates

SITE = Path(__file__).resolve().parent.parent
SITEMAP = SITE / "sitemap.xml"
PREFIX = "https://crispvideo.app/"


#: Pages under a live pre-registration, whose crawl signal must not move before the 2026-09-21
#: and 2026-09-22 reads. Derived into _tools/frozen_arms.txt from the JSON pre-registrations in
#: ~/ops/search — regenerate with a LOOSE `/how-to/[a-z0-9-]+/` regex over every *prereg*.json
#: and *experiment*.json, because a stricter one keyed on "page"/"url" fields returns ZERO for
#: rejected-pages-rewrite-preregistration.json, which stores a bare array of paths.
#: ⚠️ TEMPORARY. After 2026-09-23 empty the file and delete this exclusion — a permanent skip
#: list is a permanent lie in the sitemap.
FROZEN = {l.strip() for l in (Path(__file__).parent / "frozen_arms.txt").read_text().splitlines()
          if l.strip() and not l.startswith("#")} if (Path(__file__).parent / "frozen_arms.txt").is_file() else set()


def page_for(loc: str) -> Path | None:
    rel = loc[len(PREFIX):] if loc.startswith(PREFIX) else loc
    p = SITE / rel / "index.html" if rel else SITE / "index.html"
    return p if p.is_file() else None


def last_changed(page: Path) -> str | None:
    """The date this page's CONTENT last changed, or None if git cannot say.

    ⚠️ IT DELEGATES, AND THAT IS THE POINT. This used to be its own `git log -1`, which is the
    last commit touching the file FULL STOP. The moment _tools/page_dates.py landed — a commit
    whose only effect on 60 pages was to correct a dateModified string — that definition would
    have declared all 60 changed that day, and the sitemap would have told crawlers to re-fetch
    sixty pages whose visible content had not moved. Two tools with two definitions of "changed"
    is two answers to one question, and one of them is always wrong.

    None is deliberate: an uncommitted page has no honest date, and inventing today's would be
    the exact decorative lastmod this file exists to remove."""
    return page_dates.content_changed(page)


def rewrite(text: str) -> tuple[str, list[str]]:
    changed: list[str] = []
    skipped: list[str] = []

    def one(m: re.Match) -> str:
        loc = m.group("loc")
        rel = loc[len(PREFIX):] if loc.startswith(PREFIX) else loc
        if ("/" + rel.lstrip("/")) in FROZEN:
            skipped.append(loc)
            return m.group(0)            # a frozen arm keeps the date it had
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
    out = pattern.sub(one, text)
    if skipped:
        print(f"  ({len(skipped)} frozen arm(s) left untouched — see _tools/frozen_arms.txt)")
    return out, changed


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
