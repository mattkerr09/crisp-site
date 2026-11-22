#!/usr/bin/env python3
"""Regression checks for the Topaz perpetual licence owner facts."""
import json
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

SITE = Path(__file__).resolve().parents[1]
PAGE = SITE / "learn/why-topaz-ended-perpetual-licences/index.html"
FREE_PAGE = SITE / "learn/is-topaz-video-ai-free/index.html"

KEPT_H2 = [
    "What actually changed",
    "The prices that ended",
    "What replaced them",
    "If you already own one",
    "Adobe now owns Topaz",
    "The arithmetic worth doing",
    "Where Topaz is still better",
    "Where Crisp sits",
]
KEPT_HREFS = {
    '/apple-touch-icon.png',
    '/download/#macos-speed',
    '/favicon.ico',
    '/favicon.svg',
    '/learn/why-4k-exports-take-so-long/',
    '/style.css',
    'https://blog.adobe.com/en/publish/2026/09/23/adobe-completes-acquisition-of-topaz-labs',
    'https://crispvideo.app/',
    'https://crispvideo.app/about/',
    'https://crispvideo.app/learn/',
    'https://crispvideo.app/learn/why-topaz-ended-perpetual-licences/',
    'https://digitalproduction.com/2025/10/02/topaz-drops-perpetual-licences-bets-on-subscriptions-with-studio-launch/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/crisp?src=learn-why-topaz-ended-perpetual-licences-pbox-end',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/crisp?src=learn-why-topaz-ended-perpetual-licences-pbox-top',
    'https://kerrandcompanyholdings.com/',
    'https://news.adobe.com/news/2026/06/adobe-to-acquire-topaz-labs',
    'https://www.cgchannel.com/2025/09/topaz-labs-to-end-perpetual-licenses-of-its-software/',
    'https://www.topazlabs.com/pricing',
    'https://www.topazlabs.com/topaz-video',
    'https://www.trustpilot.com/review/www.topazlabs.com',
}
DOWNLOAD_PREFIXES = (
    'https://crispvideo.app/download/?src=nav-download',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=learn-why-topaz-ended-perpetual-licences-pbox-end&to=https://github.com/mattkerr09/crisp-site/releases/download/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=learn-why-topaz-ended-perpetual-licences-pbox-end-windows&to=https://github.com/mattkerr09/crisp-site/releases/download/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=learn-why-topaz-ended-perpetual-licences-pbox-top&to=https://github.com/mattkerr09/crisp-site/releases/download/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=learn-why-topaz-ended-perpetual-licences-pbox-top-windows&to=https://github.com/mattkerr09/crisp-site/releases/download/',
)
FAQ = "Can I still use Topaz Video AI if I own it?"
DOCS = "https://docs.topazlabs.com/topaz-video/tvai-vs-tv"


def text(source):
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", source)).split())


class Links(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.hrefs = set()
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "href" in attrs:
            self.hrefs.add(attrs["href"])


def check_dashes(source):
    assert "\u2013" not in source and "\u2014" not in source, "Long dash found"


def check_headings(source):
    headings = re.findall(r"<h2>(.*?)</h2>", source)
    assert all(h in headings for h in KEPT_H2), "Existing heading removed"


class TopazOwnerFactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.visible = re.sub(r"<script\b.*?</script>|<head>.*?</head>", "", cls.source, flags=re.S)
        cls.schemas = [json.loads(s) for s in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', cls.source, re.S)]
        cls.section = cls.visible.split("<h2>If you already own one</h2>", 1)[1].split("<h2>", 1)[0]

    def test_kept_headings(self):
        check_headings(self.source)

    def test_kept_links(self):
        hrefs = Links(self.source).hrefs
        self.assertTrue(KEPT_HREFS <= hrefs, KEPT_HREFS - hrefs)
        for prefix in DOWNLOAD_PREFIXES:
            self.assertTrue(any(h.startswith(prefix) for h in hrefs), prefix)
        self.assertIn(DOCS, Links(self.section).hrefs)

    def test_owner_table(self):
        table = re.search(r'<div class="cmp-wrap"><table>(.*?)</table>', self.section, re.S)[1]
        rows = re.findall(r"<tr>(.*?)</tr>", re.search(r"<tbody>(.*?)</tbody>", table, re.S)[1], re.S)
        self.assertEqual(len(rows), 5)
        self.assertIn("What Topaz says", table)
        self.assertIn("What it means for you", table)
        self.assertTrue(all(len(re.findall(r"<(?:th|td)\b", row)) == 2 for row in rows))
        for row in rows:
            self.assertIn("Topaz says", text(row))
        for value in ("7.1.5", "final version", "model updates", "2 computers", "6 months",
                      "perpetual licence", "Expired", "not access", "Legacy", "September 2025",
                      "newer OS updates or new systems"):
            self.assertIn(value, text(table))
        self.assertIn("read 22 November 2026", text(self.section))

    def test_sales_date_and_existing_report(self):
        self.assertIn("3 October 2025", text(self.visible))
        self.assertIn("Existing perpetual licences continue to function", text(self.section))
        self.assertIn("What happens to a licence you already bought?", text(self.section))

    def test_owner_faq(self):
        answer = text(re.search(r"<h3>" + re.escape(FAQ) + r"</h3>\s*<p>(.*?)</p>", self.visible, re.S)[1])
        faqs = next(s for s in self.schemas if s.get("@type") == "FAQPage")["mainEntity"]
        entries = [q for q in faqs if q["name"] == FAQ]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["acceptedAnswer"]["text"], answer)
        for value in ("Topaz says", "perpetual licence", "7.1.5", "2 computers", "6 months",
                      "Expired", "Legacy", "September 2025", "read 22 November 2026"):
            self.assertIn(value, answer)
        for path in SITE.rglob("*.html"):
            if path != PAGE and not any(part.startswith((".", "_")) for part in path.relative_to(SITE).parts):
                self.assertNotIn(FAQ, path.read_text(encoding="utf-8"), str(path))

    def test_dates(self):
        article = next(s for s in self.schemas if s.get("@type") == "Article")
        self.assertEqual(article["dateModified"], "2026-11-22")
        self.assertIn("last updated 2026-11-22", self.visible)

    def test_no_long_dashes(self):
        check_dashes(self.source)

    def test_free_description_prices_in_first_sentence(self):
        source = FREE_PAGE.read_text(encoding="utf-8")
        values = []
        for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
            value = unescape(re.search(r'<meta ' + attr + r' content="([^"]+)"', source)[1])
            # A decimal point inside a price does not end a sentence.
            first_sentence = re.split(r"[.!?](?:\s|$)", value, maxsplit=1)[0]
            self.assertIn("$299.00", first_sentence)
            self.assertIn("$59.00", first_sentence)
            self.assertLessEqual(len(value), 155)
            values.append(value)
        self.assertEqual(len(set(values)), 1)
        schemas = [json.loads(s) for s in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', source, re.S)]
        article = next(s for s in schemas if s.get("@type") == "Article")
        self.assertEqual(article["description"], values[0])

    def test_en_dash_negative_control(self):
        with self.assertRaises(AssertionError):
            check_dashes(self.source + "\u2013")

    def test_removed_heading_negative_control(self):
        with self.assertRaises(AssertionError):
            check_headings(self.source.replace("<h2>If you already own one</h2>", "", 1))


if __name__ == "__main__":
    unittest.main()
