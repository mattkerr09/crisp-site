#!/usr/bin/env python3
"""Regression checks for the Topaz free-plan article update."""
import json
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

PAGE = Path(__file__).resolve().parents[1] / "learn/is-topaz-video-ai-free/index.html"

KEPT_H2 = [
    "What Topaz Video costs today",
    "How it got here",
    "Free and one-time options on a Mac",
    "What Topaz still does better",
    "Questions people ask",
    "Related",
]

KEPT_HREFS = {
    '/apple-touch-icon.png',
    '/download/#macos-speed',
    '/favicon.ico',
    '/favicon.svg',
    '/style.css',
    'https://blog.adobe.com/en/publish/2026/09/23/adobe-completes-acquisition-of-topaz-labs',
    'https://crispvideo.app/',
    'https://crispvideo.app/about/',
    'https://crispvideo.app/best/free-video-upscaler-mac/',
    'https://crispvideo.app/how-to/upscale-video-on-mac/',
    'https://crispvideo.app/learn/',
    'https://crispvideo.app/learn/is-topaz-video-ai-free/',
    'https://crispvideo.app/learn/what-is-ai-video-upscaling/',
    'https://crispvideo.app/learn/why-topaz-ended-perpetual-licences/',
    'https://crispvideo.app/vs/switch-from-topaz-video-ai-to-crisp/',
    'https://crispvideo.app/vs/topaz-alternative-mac/',
    'https://crispvideo.app/vs/unifab-vs-topaz-vs-crisp/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/crisp?src=learn-is-topaz-video-ai-free-pbox-end',
    'https://kerr-affiliate-hub.kerrco.workers.dev/buy/crisp?src=learn-is-topaz-video-ai-free-pbox-top',
    'https://kerrandcompanyholdings.com/',
    'https://www.topazlabs.com/pricing',
    'https://www.topazlabs.com/topaz-video',
}

DOWNLOAD_PREFIXES = (
    'https://crispvideo.app/download/?src=nav-download',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=learn-is-topaz-video-ai-free-pbox-end&to=https://github.com/mattkerr09/crisp-site/releases/download/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=learn-is-topaz-video-ai-free-pbox-end-windows&to=https://github.com/mattkerr09/crisp-site/releases/download/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=learn-is-topaz-video-ai-free-pbox-top&to=https://github.com/mattkerr09/crisp-site/releases/download/',
    'https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=learn-is-topaz-video-ai-free-pbox-top-windows&to=https://github.com/mattkerr09/crisp-site/releases/download/',
)

FAQ = "Does Topaz Video still work after I cancel?"
ADOBE = "https://blog.adobe.com/en/publish/2026/09/23/adobe-completes-acquisition-of-topaz-labs"


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


class TopazFreeUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.visible = re.sub(r"<script\b.*?</script>|<head>.*?</head>", "", cls.source, flags=re.S)
        cls.schemas = [json.loads(s) for s in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', cls.source, re.S)]

    def test_title_and_metadata(self):
        title = text(re.search(r"<title>(.*?)</title>", self.source)[1])
        self.assertIn("Is Topaz Video AI free", title)
        self.assertLessEqual(len(title), 60)
        for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
            value = re.search(r'<meta ' + attr + r' content="([^"]+)"', self.source)[1]
            self.assertTrue(value.startswith("No free desktop plan."))
            self.assertLess(len(unescape(value)), 155)

    def test_no_long_dashes(self):
        check_dashes(self.source)

    def test_answer(self):
        before_h2 = self.source.split("<h2>", 1)[0]
        answer = text(re.search(r'<p class="lede">(.*?)</p>', before_h2, re.S)[1])
        self.assertLessEqual(len(answer.split()), 60)
        for required in ("No free desktop plan", "16 December 2025", "$299.00", "$254.00", "$59.00",
                         "22 November 2026", "you'll keep access through the end of your billing period"):
            self.assertIn(required, answer)
        self.assertLess(before_h2.index('class="updated"'), before_h2.index('class="quick"'))

    def test_kept_headings(self):
        check_headings(self.source)

    def test_kept_links(self):
        hrefs = Links(self.source).hrefs
        self.assertTrue(KEPT_HREFS <= hrefs, KEPT_HREFS - hrefs)
        for prefix in DOWNLOAD_PREFIXES:
            self.assertTrue(any(h.startswith(prefix) for h in hrefs), prefix)
        self.assertIn(ADOBE, hrefs)

    def test_plan_table(self):
        table = re.search(r'<div class="cmp-wrap"><table>(.*?)</table>', self.source, re.S)[1]
        rows = re.findall(r"<tr>(.*?)</tr>", re.search(r"<tbody>(.*?)</tbody>", table, re.S)[1], re.S)
        self.assertEqual(len(rows), 8)
        for value in ("$59.00", "$299.00", "$699.00", "$29.00", "$254.00", "$39.00",
                      "$33.00", "$74.00", "$79.00", "$499.00", "read 22 November 2026"):
            self.assertIn(value, table)
        self.assertIn("annual commitment", text(rows[2]))
        self.assertIn("first year only", text(rows[6]))
        self.assertTrue(all(len(re.findall(r"<(?:th|td)\b", row)) == 4 for row in rows))

    def test_kept_faqs(self):
        for question in (
            "Is there a free trial of Topaz Video?",
            "Did Adobe buy Topaz Labs?",
            "Can I still buy Topaz Video AI with a one-time payment?",
            "What is a free alternative to Topaz Video AI on a Mac?",
        ):
            self.assertIn("<h3>" + question + "</h3>", self.visible)

    def test_trial(self):
        self.assertIn("Topaz staff said on 16 December 2025", text(self.visible))
        self.assertIn("legacy Video AI can still be downloaded and tried", text(self.visible))
        self.assertIn("https://community.topazlabs.com/t/is-there-a-topaz-video-trial/99441", Links(self.source).hrefs)

    def test_cancellation_faq(self):
        answer = text(re.search(r"<h3>" + re.escape(FAQ) + r"</h3>\s*<p>(.*?)</p>", self.visible, re.S)[1])
        faqs = next(s for s in self.schemas if s.get("@type") == "FAQPage")["mainEntity"]
        entries = [q for q in faqs if q["name"] == FAQ]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["acceptedAnswer"]["text"], answer)
        self.assertIn("you'll keep access through the end of your billing period", answer)
        for path in PAGE.parents[2].rglob("*.html"):
            if path != PAGE and not any(part.startswith((".", "_")) for part in path.relative_to(PAGE.parents[2]).parts):
                self.assertNotIn(FAQ, path.read_text(encoding="utf-8"), str(path))

    def test_dates(self):
        article = next(s for s in self.schemas if s.get("@type") == "Article")
        self.assertEqual(article["dateModified"], "2026-11-22")
        self.assertEqual(article["datePublished"], "2026-09-28")
        self.assertIn("last updated 2026-11-22", self.visible)

    def test_en_dash_negative_control(self):
        with self.assertRaises(AssertionError):
            check_dashes(self.source.replace("No free desktop plan.", "No free desktop plan.\u2013", 1))

    def test_removed_heading_negative_control(self):
        with self.assertRaises(AssertionError):
            check_headings(self.source.replace("<h2>What Topaz Video costs today</h2>", "", 1))


if __name__ == "__main__":
    unittest.main()
