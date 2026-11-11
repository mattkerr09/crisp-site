#!/usr/bin/env python3
"""Offline checks for December prices, launch prices and every published price surface."""
from collections import Counter
from decimal import Decimal
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import gate_read_dates as reads


SITE = Path(__file__).resolve().parent.parent
ENDS = "2026-12-01T07:59:59Z"
MONEY = re.compile(r"(?:US)?\$\s*(\d+(?:,\d{3})*(?:[.,]\d+)?)|(?<![\w.,])(\d+(?:[.,]\d+)?)\s*(?:US)?\$")
OWN_NAME = re.compile(r"Crisp|Outlier|Docket|Check Engine|bundle", re.I)
PBOX = re.compile(r'<aside\b[^>]*class="pbox"[^>]*>.*?</aside>', re.S)
LD = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.S | re.I)


def amounts(text):
    out = []
    for match in MONEY.finditer(unescape(text)):
        value = match.group(1) or match.group(2)
        if "," in value and "." not in value and len(value.rsplit(",", 1)[1]) == 2:
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")
        out.append(Decimal(value))
    return out


def text_errors(raw):
    """Use the read-date gate's claims and table columns to preserve rival prices.

    A mixed sentence naming Crisp is still checked. A competitor name somewhere in
    a paragraph must not exempt a later sentence about Crisp's price.
    """
    blocks, containers = reads.blocks_of(raw)
    claims = reads.claims_in_blocks(blocks, containers)
    by_block = {}
    for claim in claims:
        by_block.setdefault(claim.block, []).append(claim.text)
    errors = []
    for block in blocks:
        units = block.cells if block.tag == "tr" else reads.sentences(block.text)
        ours = containers.get(block.container, {}).get("ours", set()) if block.tag == "tr" else set()
        for i, text in enumerate(units):
            old = set(amounts(text)) & {Decimal("29"), Decimal("99")}
            if "Outlier" in block.text and "Crisp" not in block.text:
                old.discard(Decimal("29"))
            if not old:
                continue
            rival = (i not in ours and bool(by_block.get(block.idx)) if block.tag == "tr" else
                     text in by_block.get(block.idx, []))
            if rival and not OWN_NAME.search(text):
                continue
            errors.append("stale own price: " + text)
    return errors


class Attributes(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.errors = []
        self.descriptions = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and "description" in (attrs.get("name", "") + attrs.get("property", "")):
            self.descriptions.append(attrs.get("content", ""))
        bundle = "/buy/bundle" in attrs.get("href", "")
        expected = Decimal("59" if bundle else "19")
        for key in ("data-then", "data-full-price", "data-was"):
            if key in attrs and amounts(attrs[key]) != [expected]:
                self.errors.append(f"{key}: expected {expected}, got {attrs[key]!r}")
        if "data-founding" in attrs:
            if amounts(attrs.get("data-now", "")) != [Decimal("14.50")]:
                self.errors.append("founding mount lost $14.50")
        for key in ("data-ends", "data-price-ends", "data-until"):
            if key in attrs and attrs[key] != ENDS:
                self.errors.append(f"{key}: changed launch end {attrs[key]!r}")


def schema_errors(value, context=""):
    errors = []
    if isinstance(value, dict):
        context = value.get("name", context)
        for key, item in value.items():
            if key in ("price", "minPrice", "maxPrice") and str(item) in ("29", "29.00", "99", "99.00"):
                errors.append(f"JSON-LD {key}: stale {item}")
            elif isinstance(item, str) and amounts(item):
                errors += text_errors(f"<h2>{escape(context)}</h2><p>{escape(item)}</p>")
            else:
                errors += schema_errors(item, context)
    elif isinstance(value, list):
        for item in value:
            errors += schema_errors(item, context)
    return errors


def page_errors(raw):
    errors = text_errors(raw)
    attrs = Attributes()
    attrs.feed(raw)
    attrs.close()
    errors += attrs.errors
    for description in attrs.descriptions:
        errors += text_errors(f"<p>{escape(description)}</p>")
    for title in re.findall(r"<title>(.*?)</title>", raw, re.S | re.I):
        errors += text_errors(f"<p>{title}</p>")
    for box in PBOX.findall(raw):
        price = re.search(r'<span\b[^>]*class="pbox-amt"[^>]*>(.*?)</span>', box, re.S)
        if not price or amounts(price.group(1)) != [Decimal("14.50")]:
            errors.append("product box lost its $14.50 launch price")
        if 'data-full-price=' not in box:
            errors.append("product box lost its December price")
    for bundle in re.findall(r'<a\b[^>]*href="[^"]*/buy/bundle[^"]*"[^>]*>(.*?)</a>', raw, re.S):
        prices = amounts(re.sub(r"<[^>]+>", " ", bundle))
        if prices[:2] != [Decimal("49.50"), Decimal("59")]:
            errors.append("bundle lost its $49.50 launch price or $59 December price")
    for script in LD.findall(raw):
        try:
            errors += schema_errors(json.loads(script))
        except ValueError as error:
            errors.append(f"invalid JSON-LD: {error}")
    return errors


def selftest():
    assert amounts("US$ 49,50, até novembro; $1,495.00; 14,50 US$.") == [Decimal("49.50"), Decimal("1495"), Decimal("14.50")]
    for price in ("$29", "29 $", "US$ 29", "29 US$", "$29.00", "$99", "99 $", "US$ 99", "99 US$", "$99.00"):
        assert page_errors(f"<p>Crisp costs {price}.</p>"), price
        assert page_errors(f'<meta name="description" content="Crisp costs {price}.">'), price
        assert page_errors('<script type="application/ld+json">' + json.dumps({
            "@type": "FAQPage", "mainEntity": [{"name": "What does Crisp cost?", "acceptedAnswer": {"text": price}}]
        }) + '</script>'), price
    for attr in ("data-then", "data-full-price", "data-was"):
        assert page_errors(f'<span {attr}="$29">$14.50</span>'), attr
    assert page_errors('<script type="application/ld+json">{"@type":"Offer","priceSpecification":{"price":"29.00"}}</script>')
    assert page_errors('<aside class="pbox"><span class="pbox-amt" data-full-price="$19">$9.50</span></aside>')
    assert page_errors('<p>Aiarty costs $165; Crisp costs $29.</p>')
    assert page_errors('<p>Aiarty costs $165. Crisp costs $29.</p>')
    table = '<table><thead><tr><th>Price</th><th>Crisp</th><th>Aiarty</th></tr></thead><tbody><tr><th>Once</th><td>{}</td><td>$99</td></tr></tbody></table>'
    assert page_errors(table.format('$29'))
    assert not page_errors(table.format('$19'))
    assert not page_errors('<p>Aiarty costs $29 a year. Its lifetime licence costs $99.</p>')
    assert not page_errors('<meta name="description" content="Aiarty costs $99 a year.">')
    assert not page_errors('<script type="application/ld+json">{"description":"Aiarty costs $99 a year."}</script>')
    assert not page_errors('<p>Launch price $14.50 through Nov 30, then $19. Bundle $49.50, then $59.</p>')
    assert not page_errors('<p>Outlier. Launch price $24.50, then $29 once.</p>')
    assert page_errors('<a href="https://example.test/buy/bundle">Launch $39.50, then $59.</a>')


def source_checks():
    import landing_pages
    import llms_txt
    import price_sources
    import thankyou_xsell

    facts = llms_txt.facts()
    assert facts["price"] == facts["then"] == Decimal("19")
    assert facts["now"] == Decimal("14.50") and facts["ends"] == ENDS
    assert landing_pages.BUNDLE_USD == Decimal("59")
    assert landing_pages.BUNDLE_FOUNDING_USD == Decimal("49.50")
    assert landing_pages.BUNDLE_FOUNDING_ENDS == ENDS
    assert thankyou_xsell.list_price("Crisp") == facts["price"]
    assert thankyou_xsell.list_price("Outlier") == Decimal("29")
    assert thankyou_xsell.list_price("Docket SEO") == Decimal("39")
    assert thankyou_xsell.launch_price("Outlier") == Decimal("24.50")
    assert thankyou_xsell.launch_price("Docket SEO") == Decimal("29.50")
    assert thankyou_xsell.block() in (SITE / "thank-you" / "index.html").read_text()
    assert {"14.50", "19.00", "3.63", "4.75", "49.50", "59.00", "12.38", "14.75"} <= price_sources.OURS
    assert not {"29", "29.00", "99", "99.00"} & price_sources.OURS


def main():
    selftest()
    source_checks()
    errors = []
    counts = Counter()
    boxes = 0
    for path in sorted(SITE.rglob("*.html")):
        if ".git" in path.parts or "_tools" in path.parts:
            continue
        raw = path.read_text(encoding="utf-8")
        lang = re.search(r'<html\b[^>]*lang="([^"]+)"', raw)
        counts[lang.group(1) if lang else "unknown"] += 1
        boxes += len(PBOX.findall(raw))
        errors += [f"{path.relative_to(SITE)}: {error}" for error in page_errors(raw)]
    llms = (SITE / "llms.txt").read_text(encoding="utf-8")
    if "then $19" not in llms:
        errors.append('llms.txt: missing "then $19"')
    for line in llms.splitlines():
        errors += ["llms.txt: " + error for error in text_errors(f"<p>{escape(line)}</p>")]
    if not boxes:
        errors.append("no product boxes checked")
    if errors:
        print(f"December prices: FAIL ({len(errors)} errors)")
        for error in errors[:25]:
            print("  " + error)
        return 1
    print(f"December prices: passed on {sum(counts.values())} pages and {boxes} product boxes; languages {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
