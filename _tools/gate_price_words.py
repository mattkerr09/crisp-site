#!/usr/bin/env python3
"""Reject former-price claims in shipped copy. Rival exceptions name one exact sentence.

    python3 _tools/gate_price_words.py
    python3 _tools/gate_price_words.py --selftest
    python3 _tools/gate_price_words.py --site /tmp/site
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile

SITE = Path(__file__).resolve().parent.parent
# File, exact sentence after HTML decoding and whitespace folding, reason.
RIVAL_QUOTES = (
    ("vs/avclabs-video-enhancer-alternative-mac/index.html",
     'AVCLabs lists the perpetual licence at $299.90 and was selling it for $149.90 when checked: “SAVE $150”, under a “Limited Time” notice with no end date.',
     "AVCLabs' own perpetual licence promotion, quoted from its purchase page."),
    ("vs/avclabs-video-enhancer-alternative-mac/index.html",
     'The 1-year plan lists at $119.95 and was $95.96 (20% off), and there is a 1-month plan at $39.95.',
     "AVCLabs' own subscription promotion, quoted from its purchase page."),
    ("vs/unifab-alternative-mac/index.html",
     'On 27 August this page read $499.99 list discounted to $319.99, and UniFab’s promotion terms then said “the original price of $499.99” with 36% off: 36% off $499.99 is exactly $319.99, so that reading was right when it was taken.',
     "UniFab's historical promotion and the arithmetic behind its quoted price."),
    ("vs/unifab-vs-topaz-vs-crisp/index.html",
     'When this page was written on 27 August, UniFab listed at $499.99 with 36% off, which is exactly $319.99.',
     "UniFab's historical promotion, with the date of that reading."),
)
BANNED = re.compile(
    r"\bBlack[ -]Friday\b|\bhalf[ -]price\b|\bhalf\s+off\b|%\s*off\b|\bsave\s*\$|\bwas\s*\$\s*29\b"
    r"|%\s*(?:Rabatt|オフ|de descuento|de desconto)|\bonly \d+ (?:seconds|minutes|hours) left\b",
    re.I,
)
# Exact event names and real November comparisons only. The bundle has its own
# approved percentage. Nothing here exempts a nearby, different sale claim.
SALE_QUOTES = (
    "Black Friday sale", "31% off our November price", "29% off our November price", "32% off our November price",
    "Black Friday Angebot", "31% Rabatt auf unseren Novemberpreis", "29% Rabatt auf unseren Novemberpreis",
    "Black Friday セール", "11月の価格$14.50から31%オフ", "11月の価格$49.50から29%オフ",
    "Promoção Black Friday", "Oferta de Black Friday",
    "31% de desconto sobre nosso preço de novembro", "29% de desconto sobre nosso preço de novembro",
    "31% de descuento sobre nuestro precio de noviembre", "29% de descuento sobre nuestro precio de noviembre",
)
FOUNDING = re.compile(r"\bfounding\w*", re.I)
PRICE = re.compile(r"(?:[$€£]\s*\d|\d[\d.,]*\s*[$€£]|\bUSD\s*\d)", re.I)
# The supplied Topaz reading permits this first-year price only in these dated,
# attributed clauses. It is not another allowed Crisp price.
RIVAL_SALE_QUOTES = (
    "$254 for the first year in Topaz Video's sale, read 11 Nov 2026",
    "$254 first year in Topaz Video's sale, read 11 Nov 2026",
)
TOPAZ_SALE_PRICE = re.compile(r"\$\s*254(?!\d|\.\d|,\d)|\bUSD\s*254\b|\b254\s*\$")
STRIKE = re.compile(r"(?:text-decoration(?:-line)?\s*:[^;}]*\bline-through\b)", re.I)
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
BLOCK = set("p div section article aside h1 h2 h3 h4 h5 h6 li tr td th br title summary".split())


def normal(text: str) -> str:
    return " ".join(unescape(text).split())


def without_sale_quotes(text: str) -> str:
    for quote in SALE_QUOTES:
        text = re.sub(r'(?<![A-Za-z0-9_])' + re.escape(quote) + r'(?![A-Za-z0-9_])', '', text)
    return text


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def text(self) -> str:
        return ''.join(child if isinstance(child, str) else child.text() for child in self.children)

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def buyer_text(self) -> str:
        if self.tag == 'style' or (self.tag == 'script' and self.attrs.get('type') != 'application/ld+json'):
            return ''
        return ''.join(child if isinstance(child, str) else child.buyer_text() for child in self.children)


def allowed_strike(node: Node, root: Node) -> bool:
    reference = normal(node.text())
    pairs = (("$14.50", "$9.99"), ("14,50 $", "9,99 $"), ("US$ 14,50", "US$ 9,99"),
             ("14,50 US$", "9,99 US$"), ("$49.50", "$34.99"), ("49,50 $", "34,99 $"),
             ("US$ 49,50", "US$ 34,99"), ("49,50 US$", "34,99 US$"))
    for old, sale in pairs:
        if reference == old:
            return any(node in parent.children and sale in normal(parent.text()) for parent in root.walk())
    return False


class Document(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        if tag in BLOCK:
            self.stack[-1].children.append(' ')
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break
        if tag in BLOCK:
            self.stack[-1].children.append(' ')

    def handle_data(self, text):
        self.stack[-1].children.append(text)


def matches(node: Node, selector: str) -> bool:
    # The final selector component identifies the element whose price is crossed out.
    # Checking it also covers descendants and inherited text decoration.
    part = re.split(r"\s+|[>+~]", selector.strip())[-1]
    tag = re.match(r"^[a-z][\w-]*", part, re.I)
    if tag and node.tag != tag.group().lower():
        return False
    for kind, name in re.findall(r"([.#])([\w-]+)", part):
        if kind == '.' and name not in (node.attrs.get('class') or '').split():
            return False
        if kind == '#' and name != node.attrs.get('id'):
            return False
    return True


def json_problems(value, in_offer=False) -> list[str]:
    bad = []
    if isinstance(value, dict):
        kind = value.get('@type', [])
        types = kind if isinstance(kind, list) else [kind]
        in_offer = in_offer or bool(set(types) & {'Offer', 'AggregateOffer'})
        if in_offer:
            for key in value:
                if key.lower() in {'was', 'listprice', 'originalprice', 'highprice', 'pricespecification'}:
                    bad.append(f"JSON-LD offer contains {key}; carry the price only")
        for child in value.values():
            bad.extend(json_problems(child, in_offer))
    elif isinstance(value, list):
        for child in value:
            bad.extend(json_problems(child, in_offer))
    return bad


def problems(site: Path, allowlist=RIVAL_QUOTES) -> list[str]:
    paths = sorted(p for p in site.rglob('*.html')
                   if not any(part.startswith(('.', '_')) or part == 'node_modules'
                              for part in p.relative_to(site).parts[:-1]))
    paths += [site / name for name in ('founding.js', 'llms.txt') if (site / name).is_file()]
    css = (site / 'style.css').read_text() if (site / 'style.css').is_file() else ''
    bad = []
    for path in paths:
        name = path.relative_to(site).as_posix()
        source = path.read_text(encoding='utf-8')
        if path.suffix == '.html':
            doc = Document(source)
            text = normal(doc.root.text())
            # Include user-facing attributes, metadata and schema in the same scan.
            text += ' ' + normal(' '.join(str(value) for node in doc.root.walk()
                                          for key, value in node.attrs.items() if value and key in
                                          {'content', 'title', 'alt', 'aria-label', 'data-full-price', 'data-sale-copy'}))
            buyer_text = normal(doc.root.buyer_text()) + ' ' + normal(' '.join(
                str(value) for node in doc.root.walk() for key, value in node.attrs.items()
                if value and key in {'content', 'title', 'alt', 'aria-label', 'data-full-price', 'data-sale-copy'}))
            if FOUNDING.search(buyer_text):
                bad.append(f'{name}: founding words in buyer copy')
            styles = css + '\n' + '\n'.join(n.text() for n in doc.root.walk() if n.tag == 'style')
            selectors = [selector for rule, body in re.findall(r'([^{}]+)\{([^{}]+)\}', styles)
                         if STRIKE.search(body) for selector in rule.split(',')]
            for node in doc.root.walk():
                if not PRICE.search(normal(node.text())):
                    continue
                if node.tag in {'s', 'del'} or STRIKE.search(node.attrs.get('style') or '') or any(matches(node, s) for s in selectors):
                    if not allowed_strike(node, doc.root):
                        bad.append(f'{name}: price has an unapproved strike or line-through style')
            for node in doc.root.walk():
                if node.tag == 'script' and node.attrs.get('type') == 'application/ld+json':
                    try:
                        bad.extend(f'{name}: {message}' for message in json_problems(json.loads(node.text())))
                    except ValueError:
                        bad.append(f'{name}: invalid JSON-LD')
        else:
            text = normal(source)
            if path.suffix != '.js' and FOUNDING.search(text):
                bad.append(f'{name}: founding words in buyer copy')
            if path.suffix == '.js' and re.search(r'[>"\']\s*FOUNDING(?:CRISP|BUNDLE)?\b', source, re.I):
                bad.append(f'{name}: founding words in rendered script copy')
            for struck in re.findall(r'<(?:s|del)\b[^>]*>(.*?)</(?:s|del)>', source, re.S | re.I):
                if PRICE.search(normal(re.sub(r'<[^>]+>', '', struck))):
                    bad.append(f'{name}: price has a strike tag')
            if STRIKE.search(source) and PRICE.search(source):
                bad.append(f'{name}: price has a line-through style')
            if path.suffix == '.js' and re.search(r'\bline-through\b|class=["\']was["\']|data-was', source, re.I):
                bad.append(f'{name}: former-price strike code')
        sale_text = text
        for quote in RIVAL_SALE_QUOTES:
            sale_text = sale_text.replace(quote, '')
        if TOPAZ_SALE_PRICE.search(sale_text):
            bad.append(f'{name}: $254 requires the dated Topaz Video first-year sale quote')
        for file, sentence, reason in allowlist:
            if file == name:
                assert reason.strip() and sentence == normal(sentence)
                text = text.replace(sentence, '')
        text = without_sale_quotes(text)
        for hit in BANNED.finditer(text):
            bad.append(f'{name}: banned price words: {text[max(0, hit.start()-45):hit.end()+70]}')
    return bad


def selftest() -> None:
    forms = (
        'Black Friday', 'Black Friday sales', 'Black Friday salefoo', '131% off our November price',
        '31% off our December price', '31% off our November pricing', '32% Rabatt', '32%オフ',
        '32% de descuento', '32% de desconto', 'only 12 minutes left',
        'Founding price', '<img alt="FOUNDINGCRISP">', '<meta name="description" content="FOUNDINGCRISP">',
        'Black Friday price: $14.50', 'Black Friday offer: $14.50', 'half price', 'half-price',
        'half off', '50% off', '20% off', 'save $14.50', 'was $29',
        '<s>$29</s>', '<del>$29</del>', '<s><strong>$29</strong></s>',
        '<span style="text-decoration: line-through">$29</span>',
        '<span style="text-decoration-line: line-through"><b>$29</b></span>',
        '<style>.old {text-decoration:line-through}</style><span class="old">$29</span>',
        '<span class="old">$29</span>', 'half <strong>price</strong>', '50&#37; off',
        '<meta name="description" content="half price">',
        'Black-Friday-Preis: 14,50 $',
        '<script type="application/ld+json">{"@type":"Offer","price":"14.50","priceSpecification":{"price":"29"}}</script>',
        '<script type="application/ld+json">{"@type":"Offer","price":"14.50","listPrice":"29"}</script>',
    )
    with tempfile.TemporaryDirectory(prefix='crisp-price-words-') as folder:
        site = Path(folder)
        page = site / 'index.html'
        for form in forms:
            (site / 'style.css').write_text('.old {text-decoration:line-through}')
            page.write_text('<html><body>' + form + '</body></html>')
            assert problems(site), f'missed {form}'
        page.write_text('<p>Launch price: $14.50 once, through November 30. From December 1: $19. 100% offline.</p>')
        assert not problems(site)
        for quote in SALE_QUOTES:
            page.write_text('<p>' + quote + '</p>')
            assert not problems(site), f'approved sale words rejected: {quote}'
            page.write_text('<p>' + quote + '. Black Friday offer: 50% off.</p>')
            assert problems(site), 'sale allowlist exempted adjacent claims'
        for sale, reference in (("$9.99", "$14.50"), ("9,99 $", "14,50 $"), ("US$ 9,99", "US$ 14,50"),
                                ("9,99 US$", "14,50 US$"), ("$34.99", "$49.50"), ("34,99 $", "49,50 $"),
                                ("US$ 34,99", "US$ 49,50"), ("34,99 US$", "49,50 US$")):
            page.write_text(f'<p>{sale} <s>{reference}</s> once.</p>')
            assert not problems(site), f'real November strike rejected: {reference}'
        for form in ('<s>$14.50</s>', '$9.99 <s>$19</s>', '$9.99 <s>$29</s>'):
            page.write_text('<p>' + form + '</p>')
            assert problems(site), f'unapproved strike accepted: {form}'
        page.write_text('<div data-founding data-code="FOUNDINGCRISP"></div>')
        assert not problems(site), 'internal attributes rejected'
        for quote in RIVAL_SALE_QUOTES:
            page.write_text('<p>Topaz Video: $299/yr, ' + quote + '.</p>')
            assert not problems(site), 'dated Topaz sale quote rejected'
            for changed in (quote.replace('Topaz Video', 'Crisp'),
                            quote.replace('Topaz Video', 'Topaz Studio'),
                            quote.replace('Topaz Video', 'UniFab'),
                            quote.replace('11 Nov 2026', '10 Nov 2026'),
                            quote.replace('first year', 'each year')):
                page.write_text('<p>' + changed + '</p>')
                assert problems(site), 'edited Topaz sale quote accepted'
            page.write_text('<p>' + quote + '. Crisp is $254 once.</p>')
            assert problems(site), 'Topaz quote exempted adjacent Crisp price'
        page.write_text('<p>Launch price $14.50 through Nov 30, then $19.</p>')
        for name in ('founding.js', 'llms.txt'):
            extra = site / name
            for form in ('half price', '<s>$29</s>', '<del>$29</del>', '<span style="text-decoration:line-through">$29</span>'):
                extra.write_text(form)
                assert problems(site), f'missed {form} in {name}'
            extra.unlink()
        for name, sentence, reason in RIVAL_QUOTES:
            rival = site / name
            rival.parent.mkdir(parents=True, exist_ok=True)
            rival.write_text('<p>' + sentence + '</p>')
            assert not problems(site), f'allowlisted quote failed: {name}'
            rival.write_text('<p>' + sentence + ' Crisp is half price.</p>')
            assert problems(site), 'allowlist exempted our adjacent copy'
            rival.write_text('<p>' + sentence.replace('off', 'OFF').replace('SAVE', 'save') + '</p>')
            assert problems(site), 'allowlist accepted an edited sentence'
            page.write_text('<p>' + sentence + '</p>')
            rival.unlink()
            assert problems(site), 'allowlist accepted the wrong file'
            page.write_text('Launch price $14.50 through Nov 30, then $19')
        (site / 'founding.js').write_text("var css = '.was{text-decoration:line-through}';")
        assert problems(site), 'missed JS strike code'
    print(f'price words: {len(forms)} banned forms, both text assets and exact rival allowlist tests passed')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=SITE)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    bad = problems(args.site)
    if bad:
        print('\n'.join('FAIL: ' + message for message in bad))
        return 1
    print('price words: shipped pages, founding.js and llms.txt passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
