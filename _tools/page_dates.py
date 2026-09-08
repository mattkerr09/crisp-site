#!/usr/bin/env python3
"""Make every page's dateModified say when the page actually last changed.

WHY. All 51 pages carrying a dateModified were wrong — not one matched reality. Twenty-nine
claimed 2026-07-23 for pages last edited on 2026-08-26; others claimed dates in early July.
Each was typed once when the page was written and never touched again, so the site was telling
crawlers, in structured data they read directly for freshness, that nothing had changed in six
weeks while most of it had.

That is the same failure the sitemap had (see _tools/sitemap_dates.py): the field was PRESENT,
which is what a checklist looks for, and false, which is what a reader gets. Present is not the
property worth checking.

⚠️ WHY IT IS NOT SIMPLY "THE LAST COMMIT". Writing this field is itself a commit. If the date
came from the last commit touching the file, then every run would set the field to today,
tomorrow's run would see today's date-only commit and set it to tomorrow, and the value would
walk forward forever without any content ever changing. So a commit whose only effect on this
page was to change a date line does not count as a change — which is the CEO's "minus its
date-bearing parts" rule from ~/ops/UPGRADES.md, applied to a hand-written site.

Idempotent by construction and checked: run it twice and the second run changes nothing, because
the commit the first run produced is a date-only commit and is skipped.

    python3 _tools/page_dates.py           # write
    python3 _tools/page_dates.py --check   # exit 1 if any page's date is wrong
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
# A "date-bearing part" is any line whose only job is to state a date — JSON-LD's fields AND the
# visible "Updated <Month> <Year>" dateline that `_tools/dateline.py` maintains. Both had to be
# here: the moment dateline.py corrected 53 visible datelines, this tool read those working-tree
# diffs as real content changes and wanted to walk 53 dateModified values forward, which is the
# same self-feeding loop the docstring above describes, arriving through the other tool's edit.
# Two tools writing dates on one page need ONE definition of what a date line is.
DATE_LINE = re.compile(r'^[-+].*(?:"date(?:Modified|Published)":"[^"]*"'
                       r'|Updated [A-Z][a-z]+ \d{4})')
PUBLISHED = re.compile(r'"datePublished":"([^"]+)"')
MODIFIED = re.compile(r'"dateModified":"([^"]+)"')


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=SITE, capture_output=True, text=True).stdout


def content_changed(page: Path) -> str | None:
    """The date this page's CONTENT last changed, ignoring date-only commits.

    Returns None when git knows nothing about the file — an uncommitted page has no honest
    answer, and inventing today's is the decorative date this tool exists to remove."""
    rel = str(page.relative_to(SITE))
    if _git("status", "--porcelain", "--", rel).strip():
        # ⚠️ DIRTY IS NOT THE SAME AS CHANGED, and treating it as such made this tool
        # non-idempotent: its own edit left every page dirty, so a second run saw "changing right
        # now" and walked all 40 dates forward to today. The working-tree diff gets the same
        # date-only test as a commit does — only a real edit counts.
        wt = [l for l in _git("diff", "--unified=0", "--", rel).splitlines()
              if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        if any(not DATE_LINE.match(l) for l in wt):
            return date.today().isoformat()
    log = _git("log", "--format=%H %ad", "--date=short", "--", rel).splitlines()
    for line in log:
        sha, _, when = line.partition(" ")
        diff = _git("show", "--format=", "--unified=0", sha, "--", rel).splitlines()
        touched = [l for l in diff
                   if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        if any(not DATE_LINE.match(l) for l in touched):
            return when                      # a real content change
    return log[0].split(" ")[1] if log else None


def main() -> int:
    check = "--check" in sys.argv
    wrong, fixed, skipped = [], [], 0
    for page in sorted(SITE.rglob("index.html")):
        if "_tools" in page.parts:
            continue
        text = page.read_text()
        # ⚠️ "HAS A datePublished" WAS THE WRONG GATE, AND IT MADE THIS FIX LOOK COMPLETE WHILE
        # LEAVING SEVENTEEN STALE DATES IN PLACE. The /best/ and /vs/ pages carry a dateModified
        # and no datePublished, so the first version skipped them as "no article schema" — and
        # skipping a page that already publishes a WRONG date is the one thing this tool must
        # never do. Caught by spot-checking a live page after the first run said it was done.
        #
        # So: a page qualifies if it dates itself at all. A page with neither field is genuinely
        # not making a claim, and gets nothing added — inventing a date for a hub page would be
        # the decorative-metadata habit this whole exercise is removing.
        if not PUBLISHED.search(text) and not MODIFIED.search(text):
            skipped += 1                     # makes no date claim — nothing to correct
            continue
        when = content_changed(page)
        if when is None:
            continue
        cur = MODIFIED.search(text)
        if cur and cur.group(1) == when:
            continue
        wrong.append(f"{page.parent.relative_to(SITE)}: "
                     f"{cur.group(1) if cur else '(none)'} -> {when}")
        if check:
            continue
        if cur:
            out = MODIFIED.sub(f'"dateModified":"{when}"', text)
        else:
            # only reachable when the page has a datePublished to anchor to; a page with neither
            # was filtered out above.
            out = PUBLISHED.sub(
                lambda m: f'{m.group(0)},"dateModified":"{when}"', text, count=1)
        page.write_text(out)
        fixed.append(page)
    if check:
        if wrong:
            print(f"dateModified is wrong on {len(wrong)} pages:")
            for w in wrong[:20]:
                print("  " + w)
            return 1
        print("dateModified is accurate on every dated page")
        return 0
    print(f"{len(fixed)} pages corrected ({skipped} have no article schema and were left alone)")
    for w in wrong[:10]:
        print("  " + w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
