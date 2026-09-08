#!/usr/bin/env python3
"""Keep the VISIBLE "Updated <Month> <Year>" dateline true.

WHY A SECOND DATE TOOL. `page_dates.py` keeps JSON-LD `dateModified` honest, and its rule is
deliberate: "a page qualifies if it dates itself at all… a page with neither field is genuinely
not making a claim". That rule is right and this tool does not change it. But it is implemented
as two regexes over JSON-LD, so "dates itself" means "dates itself IN THE MARKUP GOOGLE READS".

Fifty-three pages date themselves in the sentence a HUMAN reads — `Updated July 2026`, in the
body, above the fold — and thirty-seven how-to pages carry that line and no JSON-LD date at all.
So page_dates.py reported "dateModified is accurate on every dated page" while every one of those
fifty-three visible datelines was stale. Not one was right. The check was not wrong; it was
scoped to the claims it could see, and silent about a claim of exactly the same kind sitting in
the text. A checker that can only see the field it was written for reads clean either way.

THE RULE HERE IS STRICTER THAN page_dates.py's, on purpose. That tool counts any non-date line
diff as a content change, so a mechanical sweep — wrapping every table in a scroll box, say —
walks the date forward. For a machine freshness signal that is fine. A visible "Updated" line is
a claim to a READER that the page was revisited, so this tool compares the page's VISIBLE TEXT
across commits and ignores markup-only changes entirely. The dateline itself is stripped before
comparing, so writing it can never be what moves it: idempotent by construction, and proved so.

    python3 _tools/dateline.py            # correct every stale dateline
    python3 _tools/dateline.py --check    # exit 1 if any is stale
    python3 _tools/dateline.py --self-check   # prove the check can fail
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
DATELINE = re.compile(r'Updated ([A-Z][a-z]+) (\d{4})')
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=SITE, capture_output=True, text=True).stdout


def visible(html: str) -> str:
    """What a reader sees, with the dateline removed so it cannot move itself."""
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    body = m.group(1) if m else html
    body = re.sub(r"<(script|style)\b.*?</\1>", "", body, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", body)
    text = DATELINE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def last_visible_change(page: Path) -> str | None:
    """The date this page's visible text last changed. None if git knows nothing about it."""
    rel = str(page.relative_to(SITE))
    current = visible(page.read_text())
    log = [l for l in _git("log", "--format=%H %ad", "--date=short", "--", rel).splitlines() if l.strip()]
    if not log:
        return None
    # A dirty working tree counts only if the VISIBLE text differs from the last commit.
    head_blob = _git("show", f"{log[0].split(' ')[0]}:{rel}")
    if head_blob and visible(head_blob) != current:
        return date.today().isoformat()
    newest, previous = None, current
    for line in log:
        sha, _, when = line.partition(" ")
        blob = _git("show", f"{sha}:{rel}")
        if not blob:
            break
        v = visible(blob)
        if v != previous:
            return newest or when
        newest, previous = when, v
    return newest


def audit() -> list[tuple[Path, str, str]]:
    out = []
    for page in sorted(SITE.rglob("index.html")):
        if "_tools" in page.parts:
            continue
        text = page.read_text()
        m = DATELINE.search(text)
        if not m:
            continue                      # makes no visible date claim — nothing to correct
        when = last_visible_change(page)
        if when is None:
            continue
        want = f"{MONTHS[int(when[5:7]) - 1]} {when[:4]}"
        have = f"{m.group(1)} {m.group(2)}"
        if have != want:
            out.append((page, have, want))
    return out


def _self_check() -> int:
    """The check must go red on a dateline that is wrong, or its green means nothing."""
    page = next(p for p in sorted(SITE.rglob("index.html"))
                if "_tools" not in p.parts and DATELINE.search(p.read_text()))
    original = page.read_text()
    when = last_visible_change(page)
    if when is None:
        print("✗ self-check needs a committed page", file=sys.stderr)
        return 1
    wrong_year = str(int(when[:4]) - 1)
    try:
        page.write_text(DATELINE.sub(f"Updated March {wrong_year}", original, count=1))
        caught = any(p == page for p, _, _ in audit())
    finally:
        page.write_text(original)
    if not caught:
        print(f"✗ a deliberately wrong dateline on {page.parent.name} was NOT reported — "
              "this check cannot fail, so its green proves nothing", file=sys.stderr)
        return 1
    # ⚠️ Restoration is proved against the FILE, not against audit(). The first version asked
    # whether audit() still flagged this page and called that "not restored" — but on a site
    # where the dateline is genuinely stale, audit() flags it either way, so the assertion
    # failed on a correctly restored file. A check whose failure mode is indistinguishable
    # from the condition it runs in is not a check.
    if page.read_text() != original:
        print("✗ the page was not restored", file=sys.stderr)
        return 1
    print(f"✓ a planted 'Updated March {wrong_year}' on {page.parent.name} is reported, "
          "and the page is restored — the check can fail")
    return 0


def main() -> int:
    if "--self-check" in sys.argv:
        return _self_check()
    check = "--check" in sys.argv
    stale = audit()
    if not stale:
        n = sum(1 for p in SITE.rglob("index.html")
                if "_tools" not in p.parts and DATELINE.search(p.read_text()))
        print(f"every visible dateline is true ({n} pages carry one)")
        return 0
    if check:
        print(f"{len(stale)} visible datelines are stale:")
        for page, have, want in stale:
            print(f"  {page.parent.relative_to(SITE)}: {have} -> {want}")
        return 1
    for page, have, want in stale:
        page.write_text(DATELINE.sub(f"Updated {want}", page.read_text(), count=1))
    print(f"corrected {len(stale)} datelines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
