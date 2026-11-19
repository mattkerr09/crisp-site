#!/usr/bin/env python3
"""Offline checks for December prices, launch prices and every published price surface."""
from collections import Counter
from decimal import Decimal
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from sale_test_facts import sale_engine

with sale_engine():
    import gate_read_dates as reads


SITE = Path(__file__).resolve().parent.parent
ENDS = "2026-12-03T07:59:59Z"
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
            old = set(amounts(text)) & {Decimal("14.50"), Decimal("19"), Decimal("99")}
            if any(reference in text for reference in (
                'November price of $14.50', 'Novemberpreis von 14,50 $', '11月の価格$14.50から',
                'preço de novembro de US$ 14,50', 'precio de noviembre de 14,50 US$')):
                old.discard(Decimal('14.50'))
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
            description = attrs.get("content", "")
            self.descriptions.append(description)
            if len(description) > 165:
                self.errors.append("meta description exceeds 165 characters")
        bundle = "/buy/bundle" in attrs.get("href", "")
        expected = Decimal({"bundle": "79", "outlier": "39", "docket": "39"}.get(attrs.get("data-product"), "79" if bundle else "29"))
        for key in ("data-then", "data-full-price", "data-was"):
            if key in attrs and amounts(attrs[key]) != [expected]:
                self.errors.append(f"{key}: expected {expected}, got {attrs[key]!r}")
        if "data-founding" in attrs:
            if amounts(attrs.get("data-now", "")) != [Decimal("9.99")]:
                self.errors.append("sale mount lost $9.99")
        for key in ("data-ends", "data-price-ends", "data-until"):
            if key in attrs and attrs[key] != ENDS:
                self.errors.append(f"{key}: changed launch end {attrs[key]!r}")


def schema_errors(value, context=""):
    errors = []
    if isinstance(value, dict):
        context = value.get("name", context)
        if value.get('@type') == 'Offer' and value.get('price') not in (None, '0', '0.00', 0):
            price = str(value['price'])
            if price == '9.99':
                if value.get('priceValidUntil') != '2026-12-02' or value.get('validFrom'):
                    errors.append('JSON-LD sale Offer has wrong dates')
            elif price in ('29', '29.00'):
                if value.get('validFrom') != '2026-12-03' or value.get('priceValidUntil'):
                    errors.append('JSON-LD regular Offer has wrong dates')
            else:
                errors.append(f'JSON-LD Offer has stale price {price}')
        for key, item in value.items():
            if key in ("price", "minPrice", "maxPrice") and str(item) in ("19", "19.00", "59", "59.00", "99", "99.00"):
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
        if not price or amounts(price.group(1)) != [Decimal("9.99")]:
            errors.append("product box lost its $9.99 sale price")
        if 'data-full-price=' not in box:
            errors.append("product box lost its December price")
    for bundle in re.findall(r'<a\b[^>]*href="[^"]*/buy/bundle[^"]*"[^>]*>(.*?)</a>', raw, re.S):
        prices = amounts(re.sub(r"<[^>]+>", " ", bundle))
        if prices[:3] != [Decimal("34.99"), Decimal("49.50"), Decimal("79")]:
            errors.append("bundle lost its $34.99 sale, $49.50 November reference or $79 regular price")
    for script in LD.findall(raw):
        try:
            errors += schema_errors(json.loads(script))
        except ValueError as error:
            errors.append(f"invalid JSON-LD: {error}")
    return errors


def selftest():
    assert amounts("US$ 49,50, até novembro; $1,495.00; 14,50 US$.") == [Decimal("49.50"), Decimal("1495"), Decimal("14.50")]
    for price in ("$19", "19 $", "US$ 19", "19 US$", "$19.00", "$99", "99 $", "US$ 99", "99 US$", "$99.00"):
        assert page_errors(f"<p>Crisp costs {price}.</p>"), price
        assert page_errors(f'<meta name="description" content="Crisp costs {price}.">'), price
        assert page_errors('<script type="application/ld+json">' + json.dumps({
            "@type": "FAQPage", "mainEntity": [{"name": "What does Crisp cost?", "acceptedAnswer": {"text": price}}]
        }) + '</script>'), price
    assert page_errors('<meta name="description" content="' + "x" * 166 + '">')
    assert not page_errors('<meta name="description" content="' + "x" * 165 + '">')
    for attr in ("data-then", "data-full-price", "data-was"):
        assert page_errors(f'<span {attr}="$19">$14.50</span>'), attr
    assert page_errors('<script type="application/ld+json">{"@type":"Offer","priceSpecification":{"price":"19.00"}}</script>')
    assert page_errors('<aside class="pbox"><span class="pbox-amt" data-full-price="$29">$9.50</span></aside>')
    assert page_errors('<p>Aiarty costs $165; Crisp costs $19.</p>')
    assert page_errors('<p>Aiarty costs $165. Crisp costs $19.</p>')
    table = '<table><thead><tr><th>Price</th><th>Crisp</th><th>Aiarty</th></tr></thead><tbody><tr><th>Once</th><td>{}</td><td>$99</td></tr></tbody></table>'
    assert page_errors(table.format('$19'))
    assert not page_errors(table.format('$29'))
    assert not page_errors('<p>Aiarty costs $29 a year. Its lifetime licence costs $99.</p>')
    assert not page_errors('<meta name="description" content="Aiarty costs $99 a year.">')
    assert not page_errors('<script type="application/ld+json">{"description":"Aiarty costs $99 a year."}</script>')
    assert page_errors('<p>Launch price $14.50 through Nov 30, then $19.</p>')
    assert not page_errors('<p>Black Friday sale: $9.99 once, 31% off our November price of $14.50, through December 2. Then $29.</p>')
    assert not page_errors('<p>Outlier. Black Friday sale: $16.99 once, 31% off our November price of $24.50, through December 2. Then $39.</p>')
    assert page_errors('<a href="https://example.test/buy/bundle">Launch $39.50, then $59.</a>')
    for offer in ({'price': '14.50', 'priceValidUntil': '2026-12-02'},
                  {'price': '9.99', 'priceValidUntil': '2026-11-30'},
                  {'price': '29.00', 'validFrom': '2026-12-01'}):
        assert schema_errors(dict(offer, **{'@type': 'Offer'}))
    assert not schema_errors({'@type': 'Offer', 'price': '9.99', 'priceValidUntil': '2026-12-02'})
    assert not schema_errors({'@type': 'Offer', 'price': '29.00', 'validFrom': '2026-12-03'})


def source_checks():
    import landing_pages
    import llms_txt
    import price_sources
    import thankyou_xsell

    facts = llms_txt.facts()
    assert facts["price"] == facts["then"] == Decimal("29")
    assert facts["now"] == Decimal("9.99") and facts["ends"] == ENDS
    assert landing_pages.BUNDLE_USD == Decimal("79")
    assert landing_pages.BUNDLE_FOUNDING_USD == Decimal("34.99")
    assert landing_pages.BUNDLE_FOUNDING_ENDS == ENDS
    assert thankyou_xsell.list_price("Crisp") == facts["price"]
    assert thankyou_xsell.list_price("Outlier") == Decimal("39")
    assert thankyou_xsell.list_price("Check Engine SEO") == Decimal("39")
    assert thankyou_xsell.sale_price("Outlier") == Decimal("16.99")
    assert thankyou_xsell.sale_price("Check Engine SEO") == Decimal("19.99")
    assert thankyou_xsell.block() in (SITE / "thank-you" / "index.html").read_text()
    assert {"9.99", "14.50", "29.00", "2.50", "7.25", "34.99", "49.50", "79.00", "8.75", "19.75"} <= price_sources.OURS
    assert not {"19", "19.00", "59", "59.00", "99", "99.00"} & price_sources.OURS
    assert llms_txt.quarter(facts["price"]) == Decimal("7.25")
    assert llms_txt.quarter(facts["now"]) == Decimal("2.50")
    home = (SITE / "index.html").read_text()
    graphs = [json.loads(script) for script in LD.findall(home)]
    pro = [offer for graph in graphs for node in graph.get("@graph", [])
           for offer in node.get("offers", []) if offer.get("name") == "Pro"]
    # Two dated Pro offers: sale through December 2, regular price from December 3.
    assert len(pro) == 2, "home must carry two dated Pro Offers"
    launch = [o for o in pro if o.get("priceValidUntil")]
    later = [o for o in pro if o.get("validFrom")]
    assert len(launch) == 1 and launch[0]["price"] == "9.99" and launch[0]["priceValidUntil"] == "2026-12-02", launch
    assert len(later) == 1 and later[0]["price"] == "29.00" and later[0]["validFrom"] == "2026-12-03", later


def facts_checks():
    from unittest.mock import Mock, patch
    import llms_txt
    from sale_test_facts import ENGINE_SOURCE

    # The exact new names work without the old PRICE_AFTER_LAUNCH_USD alias.
    for source in (ENGINE_SOURCE, ENGINE_SOURCE.replace('= 29\n', '= Decimal("29")\n')
                   .replace('= 19.01\n', '= Decimal("19.01")\n')
                   .replace('= 14.50\n', '= Decimal("14.50")\n')):
        with patch.object(llms_txt, "ENGINE", Mock(read_text=Mock(return_value=source))):
            facts = llms_txt.facts()
            assert facts["price"] == Decimal("29") and facts["now"] == Decimal("9.99")
            assert facts["november"] == Decimal("14.50") and facts["percent"] == 31

    for old, new, message in (('= 19.01\n', '= 9\n', 'sale price'),
                              ('NOVEMBER_PRICE_USD', 'OTHER_PRICE', 'could not read'),
                              ('= 14.50\n', '= 15\n', 'November price'),
                              ('= 29\n', '= 20\n', 'full price'),
                              ('2026-12-03T07:59:59Z', '2026-12-02T07:59:59Z', 'LAUNCH_ENDS')):
        with patch.object(llms_txt, "ENGINE", Mock(read_text=Mock(return_value=ENGINE_SOURCE.replace(old, new)))):
            try:
                llms_txt.facts()
            except SystemExit as error:
                assert message in str(error), str(error)
            else:
                raise AssertionError(f"facts accepted {new}")
    with patch.object(llms_txt, 'ENGINE', Path('/nonexistent/crisp-sale-engine/entitlement.py')):
        try:
            llms_txt.facts()
        except SystemExit as error:
            assert 'No price fallback' in str(error)
        else:
            raise AssertionError('missing engine silently accepted')


def main():
    selftest()
    facts_checks()
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
    if "Then $29" not in llms:
        errors.append('llms.txt: missing "Then $29"')
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
    from sale_test_facts import sale_engine
    with sale_engine():
        raise SystemExit(main())
