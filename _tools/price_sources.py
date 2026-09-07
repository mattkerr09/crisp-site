#!/usr/bin/env python3
"""Every rival price on a /vs/ page must carry the date it was checked.

A comparison page quotes other companies' prices, and those move without telling us. This site
has already published wrong ones: a blind find-and-replace put Crisp's own new price onto four
rivals' figures and they stayed wrong for eighteen days, through audits that read the HTML and
passed, because nothing tied a number to when anybody last looked at it.

Five pages already do it properly — a "Prices checked <date>" block naming each rival's own
pricing URL and what it showed. This makes that the rule, and reports the pages that quote a
rival's figure with no such block.

RATCHETS, IT DOES NOT GO RED. Six pages are in that state today. A gate red on six pages is one
nobody reads, which is exactly how the eighteen-day bug survived. So the current six live in
price_sources_baseline.json and the gate fails only on a page that is NOT in the baseline, or one
that has grown a new unsourced figure. Fixed pages are named so their line can be deleted.

    python3 _tools/price_sources.py            # report + exit 1 on new debt
    python3 _tools/price_sources.py --baseline # re-record today's state (deliberate)
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
BASELINE = Path(__file__).resolve().parent / "price_sources_baseline.json"

# Crisp's own price is not a rival's price and needs no external source.
OURS = {"129", "129.00", "0"}
MONEY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")
DATED = re.compile(r"Prices?\s+checked\s+\d", re.I)


def _text(p: Path) -> str:
    t = p.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"(?is)<(script|style|head|nav|footer)\b.*?</\1>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def survey():
    """-> {slug: [rival figures]} for /vs/ pages quoting a rival price with no dated block."""
    gaps = {}
    for page in sorted((SITE / "vs").glob("*/index.html")):
        txt = _text(page)
        rivals = sorted({m.group(1) for m in MONEY.finditer(txt)
                         if m.group(1).rstrip(".").rstrip(",") not in OURS})
        if rivals and not DATED.search(txt):
            gaps[page.parent.name] = rivals
    return gaps


def main():
    gaps = survey()
    if "--baseline" in sys.argv:
        BASELINE.write_text(json.dumps(gaps, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"baseline recorded: {len(gaps)} pages quote a rival price with no checked date")
        return 0

    known = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}

    new, worse = [], []
    for slug, figures in gaps.items():
        if slug not in known:
            new.append((slug, figures))
        elif set(figures) - set(known[slug]):
            worse.append((slug, sorted(set(figures) - set(known[slug]))))
    fixed = [s for s in known if s not in gaps]

    print(f"/vs/ pages quoting a rival price with no “Prices checked” date: "
          f"{len(gaps)} ({len(known)} known)")
    for slug in fixed:
        print(f"  FIXED   {slug} — delete its line from {BASELINE.name}")
    for slug, figures in new:
        print(f"  NEW     {slug} — quotes {', '.join('$' + f for f in figures)} "
              f"and says nothing about when that was true")
    for slug, figures in worse:
        print(f"  WORSE   {slug} — new unsourced figures: {', '.join('$' + f for f in figures)}")
    if new or worse:
        print("\nAdd a “Prices checked <date>” block naming the rival's own pricing page and what "
              "it showed, the way /vs/unifab-alternative-mac/ does.")
        return 1
    if not fixed:
        print("no new unsourced rival prices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
