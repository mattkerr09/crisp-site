#!/usr/bin/env python3
"""Check the sale mounts and refuse expired sale copy.

The reviewed CEO sale record in december_prices.json is checked offline. The job
forbids network access. It records an unlimited sale, ending 2026-12-03T07:59:59Z.
The engine reader separately checks its LAUNCH_ENDS against the homepage mount.
Browser expiry hides sale notes and restores regular prices without a deploy;
this gate also refuses stale static sale copy after that instant.

    python3 _tools/gate_founding.py
    python3 _tools/gate_founding.py --today 2026-12-03T07:59:59Z
    python3 _tools/gate_founding.py --selftest
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
STATE = SITE / "_tools" / "december_prices.json"


def sale_state() -> dict:
    try:
        return json.loads(STATE.read_text())["sale"]
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"gate_founding: required reviewed sale state is unavailable: {error}") from error


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
        src = state.get("source", "?")
        if state.get("unlimited") and first is not None:
            bad.append(f"the site says the first {first} buyers, but the live offer is for everyone ({src}): drop data-first")
        if state.get("total") is not None and str(state["total"]) != str(first):
            bad.append(f"the site says the first {first} buyers, the live cap is {state['total']} ({src})")
        if state.get("ends") and state["ends"] != ends:
            bad.append(f"the site's data-ends is {ends}, the code ends {state['ends']} ({src})")
        if state.get("code") and code and state["code"] != code:
            bad.append(f"the site offers {code}, the live code is {state['code']} ({src})")
        if state.get("sold_out") or state.get("expired"):
            used_up = True
        notes.append((f"reviewed state from {src}: for everyone, no cap" if state.get("unlimited") else
                      f"live count from {src}: {state.get('left')} of {state.get('total')} left")
                     + (", SOLD OUT" if state.get("sold_out") else "") + (", EXPIRED" if state.get("expired") else ""))
    else:
        notes.append("no live count (worker unreachable and no ops JSON): only the date switch is checked")
    ended = now >= end
    if not (ended or used_up):
        days = (end - now).total_seconds() / 86400
        if days <= 7:
            notes.append(f"the founding offer ends in {days:.1f} days ({ends}): regenerate the site after it so no page "
                         f"ships the founding line")
        return bad, notes
    why = f"ended {ends}" if ended else "all places used"
    needles = [n for n in (code, price and f"{price}", "Founding price", "founding buyers", "founding price",
                           "Black Friday", "Launch price", "launch price", "Einführungspreis", "発売記念価格",
                           "Preço de lançamento", "Precio de lanzamiento") if n]
    for p in pages(site):
        text = visible(p)
        hit = [n for n in needles if n in text]
        if hit:
            bad.append(f"{p.relative_to(site).as_posix()}: still shows the founding offer ({why}): {hit[:3]}")
    return bad, notes


def selftest() -> bool:
    with tempfile.TemporaryDirectory() as d:
        site = Path(d)
        mount_html = ('<div data-founding data-code="CODEX" data-then="$129" data-now="$64.50" data-first="24" '
                      'data-ends="2026-11-25T01:26:00Z"></div>')
        (site / "index.html").write_text(f"<html><body>{mount_html}<p>Launch price: $64.50 once, through November 24. From November 25: $129.</p>"
                                         "<!-- Founding price in a comment does not count --></body></html>")
        live = {"source": "test", "total": 24, "left": 21, "sold_out": False, "expired": False,
                "ends": "2026-11-25T01:26:00Z", "code": "CODEX"}
        before = problems(site, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), live)[0]
        after = problems(site, dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc), live)[0]
        sold = problems(site, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), {**live, "left": 0, "sold_out": True})[0]
        wrong = problems(site, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), {**live, "total": 25})[0]
        labels = []
        for label in ("Black Friday sale", "Black Friday セール", "Promoção Black Friday",
                      "Oferta de Black Friday", "Launch price", "launch price", "Einführungspreis"):
            (site / "index.html").write_text(f"<html><body>{mount_html}<p>{label}</p></body></html>")
            labels.append(bool(problems(site, dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc), live)[0]))
        no_end_mount = mount_html.replace(' data-ends="2026-11-25T01:26:00Z"', "")
        (site / "index.html").write_text("<html><body>" + no_end_mount + "</body></html>")
        no_end = problems(site, dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), None)[0]
        # Check the real sale's exact UTC boundary as well as the capped fixture.
        sale_end = "2026-12-03T07:59:59Z"
        (site / "index.html").write_text(
            f'<div data-founding data-code="FOUNDINGCRISP" data-now="$9.99" data-then="$19" data-ends="{sale_end}"></div>'
            '<p>Black Friday sale: $9.99 once, 31% off our November price of $14.50, through December 2. Then $19.</p>')
        sale = {"source": "test", "unlimited": True, "total": None, "ends": sale_end, "code": "FOUNDINGCRISP"}
        end = dt.datetime.fromisoformat(sale_end.replace("Z", "+00:00"))
        sale_before = problems(site, end - dt.timedelta(seconds=1), sale)[0]
        sale_after = problems(site, end, sale)[0]
    return (not before and bool(after) and bool(sold) and bool(wrong) and bool(no_end) and all(labels)
            and not sale_before and bool(sale_after))


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
    state = sale_state()
    print("  note  offline check against the reviewed CEO sale record; checkout was not queried")
    bad, notes = problems(SITE, now, state)
    for n in notes:
        print(f"  note  {n}")
    if bad:
        print(f"founding: {len(bad)} problem(s):")
        for b in bad[:30]:
            print(f"  ✗ {b}")
        return 1
    m = mount(SITE)
    who = f"for the first {m.get('first')} buyers" if m.get("first") else "for everyone"
    print(f"founding: {m.get('code')} {m.get('now')} {who}, then {m.get('then') or m.get('was')}, live until {m.get('ends')}; "
          f"no stale founding copy")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
