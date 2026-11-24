#!/usr/bin/env python3
"""Check the dated Nero and DVDFab comparisons and their discovery links."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from faq_jsonld import visible_faq
from gate_price_words import Document, Node, normal
from schema_matches_page import blocks, problems, text_of, visible

SITE = Path(__file__).resolve().parents[1]
BASE = 'https://crispvideo.app/'
PAGES = {
    'nero-ai-video-upscaler-alternative': {
        'sources': {
            'https://pcai.nero.com/video-upscaler',
            'https://store.nero.com/order/checkout.php?PRODS=51479181',
        },
        'prices': {'84.95', '195.00'},
    },
    'dvdfab-enlarger-ai-alternative': {
        'sources': {
            'https://www.dvdfab.cn/enlarger-ai.htm',
            'https://unifab.ai/ai-video-enhancer-online.htm',
            'https://unifab.ai/video-upscaler.htm',
            'https://unifab.ai/unifab.htm',
        },
        'prices': {'84.99', '129.99', '103.99', '319.99', '219.99'},
    },
}
MONEY = re.compile(r'\$\s*(\d+(?:\.\d+)?)')
FORBIDDEN = r'16K|colou?ri[sz](?:e|es|ing|ation)|SDR to HDR|face[- ]enhancement|face model'


def unguarded_prices(source, reference):
    """Only the reference's exact sale spans and sale note may carry our price."""
    reference_doc = Document(reference)
    approved = [(node.tag, node.attrs, normal(node.text()))
                for node in reference_doc.root.walk()
                if 'data-launch-price' in node.attrs
                or 'pbox-found' in (node.attrs.get('class') or '').split()]
    found = []

    def walk(node):
        if node.tag == 'style' or (node.tag == 'script' and node.attrs.get('type') != 'application/ld+json'):
            return
        guarded = ('data-launch-price' in node.attrs
                   or 'pbox-found' in (node.attrs.get('class') or '').split())
        if guarded:
            assert (node.tag, node.attrs, normal(node.text())) in approved, 'Price markup differs from the reference'
            return
        for key in ('content', 'title', 'alt', 'aria-label'):
            found.extend(MONEY.findall(node.attrs.get(key) or ''))
        for child in node.children:
            if isinstance(child, Node):
                walk(child)
            else:
                found.extend(MONEY.findall(child))

    walk(Document(source).root)
    return set(found)


def check_capabilities(source):
    """Reject positive Crisp claims in prose and in its own table column."""
    affirmative = re.compile(
        r'\bCrisp(?: Pro)?\s+(?:(?:also|now|can)\s+)*'
        r'(?:does|offers?|supports?|includes?|has|writes?|outputs?|exports?|converts?|colourises?|colorizes?)'
        r'\s+(?!no\b|not\b)[^.!?;:]{0,100}(?:' + FORBIDDEN + r')', re.I)
    prose = re.sub(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', '', source, flags=re.S | re.I)
    assert not affirmative.search(visible(prose)), 'Unsupported positive Crisp claim'
    doc = Document(source)
    for row in (node for node in doc.root.walk() if node.tag == 'tr'):
        cells = [child for child in row.children if isinstance(child, Node) and child.tag in {'th', 'td'}]
        if len(cells) != 3 or cells[1].tag != 'td':
            continue
        ours = normal(cells[1].text())
        if re.search(FORBIDDEN, ours, re.I):
            assert re.search(r'\b(?:no|none|does not)\b', ours, re.I), 'Unsupported capability in Crisp column'


class NeroDvdfabComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {slug: (SITE / 'vs' / slug / 'index.html').read_text() for slug in PAGES}
        cls.reference = (SITE / 'vs/unifab-alternative-mac/index.html').read_text()
        cls.hub = (SITE / 'vs/index.html').read_text()
        cls.llms = (SITE / 'llms.txt').read_text()

    def test_pages_are_discoverable(self):
        schema = next(item for item in blocks(self.hub) if item.get('@type') == 'CollectionPage')['mainEntity']
        items = schema['itemListElement']
        self.assertEqual(schema['numberOfItems'], len(items))
        self.assertEqual([item['position'] for item in items], list(range(1, len(items) + 1)))
        self.assertIn('Twenty-six comparisons', self.hub)
        namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemap_urls = [node.text for node in ET.parse(SITE / 'sitemap.xml').findall('sm:url/sm:loc', namespace)]
        for slug in PAGES:
            with self.subTest(page=slug):
                url = BASE + 'vs/' + slug + '/'
                self.assertIn('href="' + url + '"', self.hub.split('<body>', 1)[1])
                self.assertEqual(sum(item['url'] == url for item in items), 1)
                self.assertEqual(sitemap_urls.count(url), 1)
                self.assertIn('](' + url + '):', self.llms)

    def test_sources_and_read_date_beside_rival(self):
        for slug, source in self.pages.items():
            with self.subTest(page=slug):
                header = re.search(r'<thead>(.*?)</thead>', source, re.S)[1]
                self.assertIn('Read on 24 November 2026', header)
                receipt = re.search(r'<p class="price-receipts">(.*?)</p>', source, re.S)[1]
                self.assertIn('read on 24 November 2026', receipt)
                for url in PAGES[slug]['sources']:
                    self.assertIn('href="' + url + '"', header)
                    self.assertIn('href="' + url + '"', receipt)

    def test_nero_platform_prices_and_wins(self):
        page = self.pages['nero-ai-video-upscaler-alternative']
        shown = visible(page)
        for phrase in ('windows-only', 'us$84.95 a year', 'us$195.00', '1 pc', 'renews automatically',
                       'where nero wins', '120 fps', 'face enhancement', '7-day free trial', 'saved presets',
                       'so 30 fps reaches 120', 'make it 120 fps'):
            self.assertIn(phrase, shown)

    def test_dvdfab_redirect_and_separate_products(self):
        page = self.pages['dvdfab-enlarger-ai-alternative']
        answer = text_of(re.search(r'<p class="lede">(.*?)</p>', page, re.S)[1])
        self.assertRegex(answer, r"DVDFab's Enlarger AI page now redirects to UniFab's online AI video enhancer")
        shown = visible(page)
        for phrase in ('now sends enlarger ai visitors to unifab', 'where unifab wins', '16k', '30-day trial',
                       'three trials per feature', '5 computers', 'files deleted within 3 days',
                       'your own gpu or unifab cloud', 'fabcloud credits'):
            self.assertIn(phrase, shown)

    def test_price_markup_has_no_unguarded_crisp_price(self):
        for slug, page in self.pages.items():
            with self.subTest(page=slug):
                self.assertEqual(unguarded_prices(page, self.reference), PAGES[slug]['prices'])
                self.assertIn(re.search(r'<div data-founding[^>]*></div>', self.reference)[0], page)
                for location in ('top', 'end'):
                    self.assertIn('data-pbox="' + location + '"', page)

    def test_no_unsupported_crisp_capabilities(self):
        for slug, page in self.pages.items():
            with self.subTest(page=slug):
                check_capabilities(page)
                self.assertIn('Crisp does not', page)

    def test_scale_limits_and_platform_caveat(self):
        for slug, page in self.pages.items():
            with self.subTest(page=slug):
                scale = page.split('<h2>What 16x means in Crisp</h2>', 1)[1].split('<h2>', 1)[0]
                for phrase in ('16x', 'pixels, not detail', '80 megapixels', '640x480', '7680x4320',
                               '160x120', '2560x1920', '8 seconds', 'M1 Ultra', '1.0.2193'):
                    self.assertIn(phrase, scale)
                self.assertIn('on other PCs Crisp makes a standard upscale, not AI.', page)
                self.assertIn('macOS 14', page)
                self.assertIn('Apple Silicon', page)

    def test_metadata_and_faq_match_visible_page(self):
        for slug, page in self.pages.items():
            with self.subTest(page=slug):
                self.assertEqual(problems(page), [])
                url = BASE + 'vs/' + slug + '/'
                self.assertIn('<link rel="canonical" href="' + url + '">', page)
                self.assertIn('<meta property="og:url" content="' + url + '">', page)
                faq = next(item for item in blocks(page) if item.get('@type') == 'FAQPage')['mainEntity']
                self.assertEqual([(q['name'], q['acceptedAnswer']['text']) for q in faq], visible_faq(page))
                self.assertGreaterEqual(len(faq), 3)
                self.assertNotIn('\u2013', page)
                self.assertNotIn('\u2014', page)

    def test_unifab_refresh_is_consistent(self):
        for phrase in ('19 tools', 'US$319.99', 'US$219.99', '5 computers'):
            self.assertIn(phrase, self.reference)
            self.assertIn(phrase, self.llms)       # llms.txt's line is generated from the page's description
        self.assertIn('read on 24 November 2026', self.reference)
        for stale in ('17 tools', '17-tool', '17-in-1', '$229.99', '$319 once', '$319 buys'):
            self.assertNotIn(stale, self.reference)

    def test_price_guard_rejects_plain_or_changed_price(self):
        page = self.pages['nero-ai-video-upscaler-alternative']
        changed = page.replace('</article>', '<p>Crisp costs $29 once.</p></article>')
        self.assertNotEqual(unguarded_prices(changed, self.reference), PAGES['nero-ai-video-upscaler-alternative']['prices'])
        with self.assertRaises(AssertionError):
            unguarded_prices(page.replace('data-full-price="$29 once."', 'data-full-price="$30 once."'), self.reference)

    def test_capability_guard_rejects_positive_claims(self):
        page = self.pages['dvdfab-enlarger-ai-alternative']
        for claim in ('Crisp writes 16K video.', 'Crisp offers colourising.',
                      'Crisp supports SDR to HDR.', 'Crisp has a face model.'):
            with self.subTest(claim=claim), self.assertRaises(AssertionError):
                check_capabilities(page.replace('</article>', '<p>' + claim + '</p></article>'))


if __name__ == '__main__':
    unittest.main()
