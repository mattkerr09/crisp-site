#!/usr/bin/env python3
"""No founding price ships once the founding offer has ended (CEO, 2026-10-21).

FOUNDINGCRISP in Dodo: 50% off, limit 24, expires 2026-11-25T01:26Z. The home page's founding mount is the single place
the offer is written (data-code, data-now, data-first, data-ends); the product boxes, the landing pages, llms.txt and
every page's mount copy are generated from it. Two switches turn it off:
  * founding.js hides every founding line and does not mount the bar from data-ends on, with no deploy;
  * the generators (llms_txt.founding_live) write no founding line when they run after data-ends.
This gate is the third: a push is refused when
  * the mount has no data-ends (the switch would never fire), or data-first disagrees with Dodo's limit;
  * the offer has ended (now >= data-ends, or the places are used) and any page's VISIBLE text still carries the
    founding price, the code or a founding line (static HTML must be regenerated, not merely hidden by script).

Dodo's own count lives in Dodo, not here: the places used and the limit are read from an ops file the CEO's Dodo reads
keep current, ~/ops/launch/founding-crisp.json {"code": ..., "limit": 24, "used": N, "read": "<ISO date>"}. Missing, it
is reported, not guessed: the date switch still holds.

    python3 _tools/gate_founding.py                 # exit 1 on a problem
    python3 _tools/gate_founding.py --today 2026-11-26
    python3 _tools/gate_founding.py --selftest
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
STATE = Path(os.path.expanduser("~/ops/launch/founding-crisp.json"))
_DROP = re.compile(r"<!--.*?-->|<script.*?</script>|<style.*?</style>|<head.*?</head>", re.S | re.I)


def mount(site: Path) -> dict:
    home = (site / "index.html").read_text(encoding="utf-8")
    m = re.search(r"<div data-founding[^>]*>", home)
    if not m:
        raise SystemExit("gate_founding: the home page has no founding mount")
    attrs = dict(re.findall(r'data-([a-z-]+)="([^"]*)"', m.group(0)))
    return attrs


def visible(path: Path) -> str:
    s = _DROP.sub(" ", path.read_text(encoding="utf-8", errors="replace"))
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


def pages(site: Path) -> list[Path]:
    out = [p for p in site.rglob("*.html") if not p.relative_to(site).as_posix().startswith(("_", "."))]
    return sorted(out)


def problems(site: Path, now: dt.datetime, state: dict | None) -> tuple[list[str], list[str]]:
    bad, notes = [], []
    a = mount(site)
    code, ends, first, price = a.get("code"), a.get("ends"), a.get("first"), a.get("now")
    try:
        end = dt.datetime.fromisoformat((ends or "").replace("Z", "+00:00"))
    except ValueError:
        bad.append(f"the founding mount has no valid data-ends ({ends!r}): nothing would ever switch the offer off")
        return bad, notes
    used_up = False
    if state:
        if str(state.get("limit")) != str(first):
            bad.append(f"the site says the first {first} buyers, Dodo's limit is {state.get('limit')} "
                       f"(read {state.get('read', '?')})")
        if state.get("used") is not None and state.get("limit") is not None and int(state["used"]) >= int(state["limit"]):
            used_up = True
            notes.append(f"Dodo: {state['used']} of {state['limit']} founding places used (read {state.get('read', '?')})")
    else:
        notes.append(f"no {STATE} (Dodo's used/limit count): only the date switch is checked")
    ended = now >= end
    if not (ended or used_up):
        days = (end - now).total_seconds() / 86400
        if days <= 7:
            notes.append(f"the founding offer ends in {days:.1f} days ({ends}): regenerate the site after it so no page "
                         f"ships the founding line")
        return bad, notes
    why = f"ended {ends}" if ended else "all places used"
    needles = [n for n in (code, price and f"{price}", "Founding price", "founding buyers", "founding price") if n]
    for p in pages(site):
        text = visible(p)
        hit = [n for n in needles if n in text]
        if hit:
            bad.append(f"{p.relative_to(site).as_posix()}: still shows the founding offer ({why}): {hit[:3]}")
    return bad, notes


def selftest() -> bool:
    with tempfile.TemporaryDirectory() as d:
        site = Path(d)
        mount_html = ('<div data-founding data-code="CODEX" data-was="$129" data-now="$64.50" data-first="24" '
                      'data-ends="2026-11-25T01:26:00Z"></div>')
        (site / "index.html").write_text(f"<html><body>{mount_html}<p>Founding price $64.50 for the first 24 buyers.</p>"
                                         "<!-- Founding price in a comment does not count --></body></html>")
        before = problems(site, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), {"limit": 24, "used": 3})[0]
        after = problems(site, dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc), {"limit": 24, "used": 3})[0]
        sold = problems(site, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), {"limit": 24, "used": 24})[0]
        wrong = problems(site, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), {"limit": 25, "used": 0})[0]
        no_end_mount = mount_html.replace(' data-ends="2026-11-25T01:26:00Z"', "")
        (site / "index.html").write_text("<html><body>" + no_end_mount + "</body></html>")
        no_end = problems(site, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), None)[0]
    return not before and bool(after) and bool(sold) and bool(wrong) and bool(no_end)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", help="YYYY-MM-DD (UTC midnight) or an ISO time; default now")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if not selftest():
        print("gate_founding: SELFTEST FAILED: the checker would not catch a stale founding offer", file=sys.stderr)
        return 3
    if a.selftest:
        print("gate_founding self-check passed")
        return 0
    now = dt.datetime.now(dt.timezone.utc)
    if a.today:
        now = dt.datetime.fromisoformat(a.today if "T" in a.today else a.today + "T00:00:00+00:00")
        if now.tzinfo is None:
            now = now.replace(tzinfo=dt.timezone.utc)
    state = json.loads(STATE.read_text()) if STATE.exists() else None
    bad, notes = problems(SITE, now, state)
    for n in notes:
        print(f"  note  {n}")
    if bad:
        print(f"founding: {len(bad)} problem(s):")
        for b in bad[:30]:
            print(f"  ✗ {b}")
        return 1
    m = mount(SITE)
    print(f"founding: {m.get('code')} {m.get('now')} for the first {m.get('first')} buyers, live until {m.get('ends')}; "
          f"no stale founding copy")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
