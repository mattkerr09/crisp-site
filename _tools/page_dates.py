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

import content_hash

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
# ⚠️ \s* IS LOAD-BEARING, AND ITS ABSENCE COST THE SITE ITS FRESHNESS SIGNAL.
# This read r'"dateModified":"([^"]+)"' — no space after the colon. 94 of 122 pages carry
# '"dateModified": "…"' WITH a space, so this pattern matched nothing on them, the substitution
# below was a no-op, and the insertion fallback then concluded the key was ABSENT and added a
# second one. The result on 16 pages was a JSON-LD block with dateModified declared TWICE:
#
#     "dateModified":"2026-09-15","dateModified": "2026-09-07"
#
# That is not cosmetic. A JSON parser keeps the LAST key, so the freshly computed date was
# silently discarded and crawlers read the STALE one — measured on the live site:
# best/free-video-upscaler-mac parsed to 2026-09-07. The tool whose entire job is to keep this
# field honest was reporting success while making the field wrong, and a grep for the correct
# value stayed green because the correct value WAS in the file. It just never won.
MODIFIED = re.compile(r'"dateModified":\s*"([^"]+)"')


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=SITE, capture_output=True, text=True).stdout


def content_changed(page: Path) -> str | None:
    """The date this page's CONTENT last changed, judged by a hash of what a reader sees.

    Returns None when git knows nothing about the file — an uncommitted page has no honest
    answer, and inventing today's is the decorative date this tool exists to remove.

    ⚠️ WHY THIS STOPPED BEING A DIFF-LINE TEST (2026-09-17). The old version asked "does this
    commit touch any line that is not a date line?", which is true of EVERY template change. On
    2026-09-15 commit 0fdc72e added a BreadcrumbList block and a byline to 110 pages; all 110
    dates moved to that day and IndexNow correctly resent 120 URLs. Measured against that commit
    with the hash below: 81 of the 110 had a real content change (the quick answer), and
    **29 moved for nothing**. A diff line cannot tell you which region of the page it landed in.
    A hash of the extracted content can, so the question is now asked of the content itself.

    The walk is: compare the working tree to the newest commit, then each commit to the one
    before it, newest first, and stop at the first pair whose content hash differs. That commit
    is when the content last moved. If no pair differs, the content has never changed since the
    file was created, and the creation date is the honest answer."""
    rel = str(page.relative_to(SITE))
    log = [l.partition(" ") for l in
           _git("log", "--format=%H %ad", "--date=short", "--", rel).splitlines()]
    if not log:
        return None

    def at(sha: str) -> str | None:
        blob = _git("show", f"{sha}:{rel}")
        return content_hash.hash_of(blob) if blob else None

    # Dirty is not the same as changed: only a content edit in the working tree counts as today.
    if _git("status", "--porcelain", "--", rel).strip():
        try:
            if content_hash.hash_of(page.read_text(encoding="utf-8")) != at(log[0][0]):
                return date.today().isoformat()
        except OSError:
            pass

    newer = at(log[0][0])
    for i in range(1, len(log)):
        older = at(log[i][0])
        if older != newer:
            return log[i - 1][2]             # content moved at the newer of the pair
        newer = older
    return log[-1][2]                        # never changed since it was created


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
