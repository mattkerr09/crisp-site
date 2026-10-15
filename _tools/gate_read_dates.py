#!/usr/bin/env python3
"""No "read <date>" or "checked <date>" on a comparison or explainer page may be older than 45 days.

A /vs/ or /learn/ page quotes other companies' prices, plans and policies, and those move without telling us. Every one of those
pages already says when the figure was read ("Prices checked 15 October 2026", "read 16 September 2026"), but a date only proves somebody
looked once: nothing made anyone look again. This fails the push when the newest read a page states for a fact is more than 45 days old,
so a figure either gets re-read or the page stops claiming it.

WHAT COUNTS. A phrase "read|checked|verified|accessed" followed by at most four short words ("read from topazlabs.com/pricing on 15 October 2026") and a day, a month and a year, in the visible
text of a page under vs/ or learn/. A mention that begins "first read ..." or "earlier read ..." is history, not the current read, and is
skipped. A date in the future is also a failure (a typo that would hide a stale figure). The dates in JSON-LD (datePublished, dateModified) are
not reads and are not looked at: the other date gates cover them.

    python3 _tools/gate_read_dates.py                  # exit 1 on any page with a stale or future read
    python3 _tools/gate_read_dates.py --max-days 30    # a stricter window
    python3 _tools/gate_read_dates.py --today 2026-12-01 --list   # what a later date would flag (planning a refresh)
    python3 _tools/gate_read_dates.py --selftest       # the checker must fail on a planted old date
    CRISP_ALLOW_STALE_READS=1 ...                      # a deliberate, loud override for an urgent push

A page with no read date at all is not this gate's business (price_sources.py requires one wherever a rival price is quoted).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
SECTIONS = ("vs", "learn")
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
_MONTH = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
READ = re.compile(r"(?<!first )(?<!earlier )(?<!previously )\b(?:read|checked|verified|accessed)(?:\s+[^\s\d]{1,40}){0,4}?\s+(\d{1,2})\s+" + _MONTH + r"\.?,?\s+(\d{4})\b", re.I)
_DROP = re.compile(r"<!--.*?-->|<script.*?</script>|<style.*?</style>", re.S | re.I)
_TAGS = re.compile(r"<[^>]+>")


def text_of(html: str) -> str:
    """What a visitor reads: comments, scripts and styles gone, tags gone, entities and whitespace flattened."""
    t = _TAGS.sub(" ", _DROP.sub(" ", html)).replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t)


def reads_in(html: str) -> list[date]:
    out = []
    for d, mon, y in READ.findall(text_of(html)):
        try:
            out.append(date(int(y), MONTHS[mon[:3].lower()], int(d)))
        except ValueError:
            pass
    return out


def problems(html: str, today: date, max_days: int) -> list[str]:
    oldest = today - timedelta(days=max_days)
    bad = []
    for d in reads_in(html):
        if d > today:
            bad.append(f"{d.isoformat()} is in the future")
        elif d < oldest:
            bad.append(f"{d.isoformat()} is {(today - d).days} days old (limit {max_days})")
    return sorted(set(bad))


def pages() -> list[Path]:
    return sorted(p for s in SECTIONS for p in (SITE / s).glob("*/index.html"))


def selftest() -> int:
    today = date(2026, 10, 15)
    old = "<p>Prices checked 8 July 2026 on the vendor's page.</p>"
    fresh = "<p>Prices checked 15 October 2026 (first read 8 July 2026 in a browser).</p>"
    none = "<p>No dates here.</p>"
    hidden = "<!-- read 1 January 2020 --><script>var s='read 2 February 2020'</script><p>ok</p>"
    short = "<p>Topaz Video is $299 (read 24 Sep 2026)</p>"
    ok = (problems(old, today, 45) and not problems(fresh, today, 45) and not problems(none, today, 45)
          and not problems(hidden, today, 45) and not problems(short, today, 45)
          and problems("<p>read 20 October 2026</p>", today, 45))
    print("gate_read_dates self-check " + ("passed" if ok else "FAILED: the checker missed a planted old date or flagged a fresh one"))
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=45)
    ap.add_argument("--today", help="YYYY-MM-DD, to plan a refresh")
    ap.add_argument("--list", action="store_true", help="print every page with a stale read and exit 0")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if selftest():
        return 1
    today = date.fromisoformat(a.today) if a.today else date.today()
    found = {}
    checked = 0
    for p in pages():
        html = p.read_text(errors="replace")
        if reads_in(html):
            checked += 1
        bad = problems(html, today, a.max_days)
        if bad:
            found[str(p.relative_to(SITE).parent)] = bad
    if found:
        for page, bad in found.items():
            print(f"  STALE  {page}: " + "; ".join(bad))
    if found and not a.list:
        if os.environ.get("CRISP_ALLOW_STALE_READS") == "1":
            print(f"read-dates: {len(found)} page(s) have a read older than {a.max_days} days; ALLOWED by CRISP_ALLOW_STALE_READS=1. Re-read them next.")
            return 0
        print(f"read-dates: {len(found)} page(s) state a read older than {a.max_days} days. Re-read the figure on the vendor's own page and change the date,"
              " or take the claim down.")
        return 1
    print(f"read-dates: every read date on {checked} vs/ and learn/ pages is within {a.max_days} days of {today.isoformat()}" if not found else
          f"read-dates: {len(found)} of {checked} pages would be stale on {today.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
