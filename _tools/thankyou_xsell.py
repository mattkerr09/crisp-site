#!/usr/bin/env python3
"""Write the "Also from Kerr & Company" block on /thank-you/ (the CEO, 2026-11-07: Crisp's thank-you page was the only one of the
three without the cross-sell, and Crisp makes 7 of 8 sales). It sits BELOW the key and the activation steps, never above them. Prices are read, never
typed in the template: December prices and unchanged November prices come from december_prices.json, Matthew's 11 November
decision. November's prices were set from Dodo's earlier $59 and $49 records; they are not half of December's prices.
No bundle: the bundle is a cart of all three apps, so it would charge a Crisp buyer for Crisp again (CEO, sales
audit, 7 Nov). From 1 December an owner's code may go here, once it exists. The sale lines carry data-until and hide themselves after it,
because this page does not load founding.js. Every link to a sister app is rel="nofollow" (RULES 52) and the page stays noindex.

    python3 site/_tools/thankyou_xsell.py
"""
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
sys.path.insert(0, str(HERE))
import landing_pages  # noqa: E402

FACTS = HERE / "december_prices.json"
HUB = "https://kerr-affiliate-hub.kerrco.workers.dev/buy"
ENDS = landing_pages.BUNDLE_FOUNDING_ENDS          # every founding code ends together: 2026-12-01 07:59:59Z
APPS = [("Docket SEO", "docket", "Audits your whole website on your own computer and tells you what to fix first."),
        ("Outlier", "outlier", "Runs AI models on your Mac with no cloud and no subscription.")]


def money(d: Decimal) -> str:
    return f"${d:.2f}".replace(".00", "")


def list_price(name: str) -> Decimal:
    for p in json.loads(FACTS.read_text())["products"].values():
        if p["name"].startswith(name):
            if p.get("source") == "PRICE_AFTER_LAUNCH_USD":
                landing_pages.prepare_facts()
                return landing_pages.llms_txt.facts()["price"]
            return Decimal(p["price_cents"]) / 100
    raise SystemExit(f"no product named {name!r} in {FACTS}")


def launch_price(name: str) -> Decimal:
    for p in json.loads(FACTS.read_text())["products"].values():
        if p["name"].startswith(name):
            return Decimal(p["launch_price_cents"]) / 100
    raise SystemExit(f"no launch price for {name!r} in {FACTS}")


def block() -> str:
    rows = []
    for name, slug, line in APPS:
        full = list_price(name)
        rows.append(
            f'    <li><strong>{name}.</strong> {line} <span data-until="{ENDS}">{money(launch_price(name))} until 30 November, then </span>{money(full)} once. '
            f'<a href="{HUB}/{slug}?src=ty-crisp-xsell" rel="nofollow" data-track="ty-xsell-{slug}">See {name}</a></li>')
    return "\n".join([
        "<!-- xsell:begin (written by _tools/thankyou_xsell.py) -->",
        '  <h2 style="margin-top:2.4rem">Also from Kerr &amp; Company</h2>',
        '  <ul class="lede" style="padding-left:1.2rem;text-align:left">', *rows, "  </ul>",
        "  <script>(function(){var n=Date.now();document.querySelectorAll('[data-until]').forEach(function(e){"
        "if(Date.parse(e.getAttribute('data-until'))<=n)e.remove();});})();</script>",
        "<!-- xsell:end -->"])


def main() -> int:
    p = SITE / "thank-you" / "index.html"
    s = p.read_text(encoding="utf-8")
    if "<!-- xsell:begin" in s:
        s = re.sub(r"<!-- xsell:begin.*?<!-- xsell:end -->", lambda m: block(), s, flags=re.S)
    else:
        anchor = '  <p style="margin-top:2.6rem"><a class="btn" href="/#download">Download Crisp</a>'
        assert s.count(anchor) == 1, "the thank-you page's last block moved"
        s = s.replace(anchor, block() + "\n\n" + anchor)
    p.write_text(s, encoding="utf-8")
    print(f"wrote the cross-sell into {p.relative_to(SITE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
