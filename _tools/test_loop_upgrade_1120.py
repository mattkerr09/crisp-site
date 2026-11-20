#!/usr/bin/env python3
"""Focused, offline checks for the 20 November loop guide update."""
import collections
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import unittest


SITE = Path(__file__).resolve().parent.parent
PAGE = "how-to/loop-video-mac/index.html"
BASE = "4bfa68ea5995a8f6ad544523ad1fbdd029781806"
APPLE = "https://support.apple.com/guide/quicktime-player/open-and-play-a-file-qtp6cee0761b/mac"


class Text(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.feed(source)

    def handle_data(self, data):
        self.parts.append(data)

    def value(self):
        return " ".join("".join(self.parts).split())


def text(source):
    return Text(source).value()


def one(pattern, source):
    match = re.search(pattern, source, re.S)
    if not match:
        raise AssertionError(f"Missing page element: {pattern}")
    return match.group(1)


class LoopUpgrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (SITE / PAGE).read_text()
        cls.base = subprocess.run(
            ["git", "show", f"{BASE}:{PAGE}"], cwd=SITE,
            capture_output=True, text=True, check=True,
        ).stdout

    def test_first_screen_answers_both_needs(self):
        lede = one(r'<p class="lede">(.*?)</p>', self.page)
        shown = text(lede)
        for phrase in ("QuickTime Player", "View > Loop", "looped file",
                       "exact repeat count", "2 to 20", "offline", "no upload",
                       "20 November 2026"):
            self.assertIn(phrase, shown)
        self.assertIn(f'href="{APPLE}"', lede)
        self.assertLess(self.page.index(lede), self.page.index("<h2>"))

    def test_quicktime_section_steps_and_source(self):
        section = one(r'<h2>Loop playback in QuickTime</h2>(.*?)<h2>', self.page)
        shown = text(section)
        for phrase in ("Open your video file in QuickTime Player", "View > Loop",
                       "checkmark", "Click Play", "again to stop looping",
                       "does not describe saving a looped file",
                       "Checked 20 November 2026 on Apple's QuickTime Player guide"):
            self.assertIn(phrase, shown)
        self.assertEqual(shown.count("View > Loop"), 2)
        self.assertIn(f'href="{APPLE}"', section)
        self.assertEqual(one(r'<h2>(.*?)</h2>', self.page), "Loop playback in QuickTime")
        self.assertLess(self.page.index("Loop playback in QuickTime</h2>"),
                        self.page.index("The fastest way: just ask</h2>"))

    def test_no_long_dashes(self):
        self.assertNotRegex(self.page, "[\u2013\u2014]")

    def test_quicktime_comparison(self):
        row = one(r'<tr><th scope="row">Fast / lossless</th>(.*?)</tr>', self.page)
        cells = re.findall(r'<td\b[^>]*>(.*?)</td>', row, re.S)
        self.assertEqual(text(cells[1]), "Does not apply (playback only)")
        self.assertNotIn("Not checked", self.page)

    def test_faq_is_visible_and_free_answer_names_both_options(self):
        faq = one(r'<h2>Looping questions</h2>(.*?)<h3>Related guides</h3>', self.page)
        visible = [(text(q), text(a)) for q, a in re.findall(
            r'<h3>(.*?)</h3>\s*<p>(.*?)</p>', faq, re.S)]
        blocks = [json.loads(block) for block in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', self.page, re.S)]
        schema = next(b for b in blocks if b.get("@type") == "FAQPage")
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"])
                          for q in schema["mainEntity"]], visible)
        free = dict(visible)["How do I loop a video on a Mac for free?"]
        for phrase in ("free playback", "QuickTime Player", "built into your Mac",
                       "View > Loop", "looped file with a set count",
                       "Crisp's free version", "small “crispvideo.app” mark"):
            self.assertIn(phrase, free)

    def test_measurement_and_product_boxes_unchanged(self):
        caption = r'<figcaption>(.*?)</figcaption>'
        self.assertEqual(one(caption, self.page), one(caption, self.base))
        self.assertIn("A 2.00-second clip looped three times measures 6.01 seconds.", self.page)
        boxes = r'<aside class="pbox".*?</aside>'
        original = re.findall(boxes, self.base, re.S)
        self.assertTrue(original)
        self.assertEqual(re.findall(boxes, self.page, re.S), original)

    def test_price_cell_unchanged_from_base(self):
        cell = r'<tr><th scope="row">Price</th>(<td\b[^>]*>.*?</td>)'
        self.assertEqual(one(cell, self.page), one(cell, self.base))

    def test_title_h1_links_and_old_checked_lines_kept(self):
        for pattern in (r'<title>(.*?)</title>', r'<h1>(.*?)</h1>'):
            self.assertEqual(one(pattern, self.page), one(pattern, self.base))
        links = lambda s: collections.Counter(re.findall(r'href="([^"]+)"', s))
        self.assertFalse(links(self.base) - links(self.page))
        old_lines = [line for line in self.base.splitlines() if "Checked 11 November 2026" in line]
        self.assertTrue(old_lines)
        for line in old_lines:
            self.assertIn(line, self.page)


if __name__ == "__main__":
    unittest.main()
