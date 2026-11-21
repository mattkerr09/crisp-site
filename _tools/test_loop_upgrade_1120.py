#!/usr/bin/env python3
"""Focused, offline checks for the 20 November loop guide update."""
import collections
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest


SITE = Path(__file__).resolve().parent.parent
PAGE = "how-to/loop-video-mac/index.html"
# Literal values read from the page on 21 November 2026 (no git, no commit hash, so the
# test survives rebases, merges and releases). Download links carry a version, so they
# are checked by prefix only.
CAPTION = "Either side of the loop point. A 2.00-second clip looped three times measures 6.01 seconds."
TITLE = "How to loop a video on a Mac: repeat a clip N times"
H1 = 'How to <span class="grad">loop a video</span> on a Mac'
PBOX_COUNT = 2
DL_PREFIXES = [
    "https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=how-to-loop-video-mac-pbox-top&to=",
    "https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=how-to-loop-video-mac-pbox-top-windows&to=",
    "https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=how-to-loop-video-mac-pbox-end&to=",
    "https://kerr-affiliate-hub.kerrco.workers.dev/dl/crisp?src=how-to-loop-video-mac-pbox-end-windows&to=",
]
KEPT_HREFS = {
    "/download/#macos-speed",
    "https://crispvideo.app/how-to/",
    "https://crispvideo.app/how-to/make-a-gif-on-mac/",
    "https://crispvideo.app/how-to/make-a-highlight-reel-mac/",
    "https://crispvideo.app/how-to/make-a-photo-slideshow-mac/",
    "https://crispvideo.app/how-to/reverse-video-mac/",
    "https://crispvideo.app/how-to/trim-video-mac/",
    "https://kerr-affiliate-hub.kerrco.workers.dev/buy/crisp?src=how-to-loop-video-mac-pbox-end",
    "https://kerr-affiliate-hub.kerrco.workers.dev/buy/crisp?src=how-to-loop-video-mac-pbox-top",
    "https://support.apple.com/guide/imovie/welcome/mac",
    "https://support.apple.com/guide/quicktime-player/open-and-play-a-file-qtp6cee0761b/mac",
}
OLD_CHECKED_FRAGMENT = ("Checked 11 November 2026 on Apple\u2019s <a href=\"https://support.apple.com/guide/"
                        "quicktime-player/open-and-play-a-file-qtp6cee0761b/mac\" rel=\"nofollow\">QuickTime playback guide</a>")
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

    def test_measurement_and_product_boxes_kept(self):
        self.assertEqual(one(r'<figcaption>(.*?)</figcaption>', self.page), CAPTION)
        self.assertIn("A 2.00-second clip looped three times measures 6.01 seconds.", self.page)
        boxes = re.findall(r'<aside class="pbox".*?</aside>', self.page, re.S)
        self.assertEqual(len(boxes), PBOX_COUNT)
        hrefs = re.findall(r'href="([^"]+)"', self.page)
        for prefix in DL_PREFIXES:
            self.assertTrue(any(h.startswith(prefix) for h in hrefs), prefix)

    def test_price_cell_present(self):
        # The price itself comes from the site's helpers and changes on schedule; only its presence is pinned.
        self.assertTrue(text(one(r'<tr><th scope="row">Price</th>(<td\b[^>]*>.*?</td>)', self.page)))

    def test_title_h1_links_and_old_checked_lines_kept(self):
        self.assertEqual(one(r'<title>(.*?)</title>', self.page), TITLE)
        self.assertEqual(one(r'<h1>(.*?)</h1>', self.page), H1)
        missing = KEPT_HREFS - set(re.findall(r'href="([^"]+)"', self.page))
        self.assertFalse(missing, sorted(missing))
        self.assertEqual(self.page.count(OLD_CHECKED_FRAGMENT), 2)

    def test_negative_control_dash(self):
        broken = self.page.replace("View &gt; Loop", "View \u2013 Loop", 1)
        self.assertRegex(broken, "[\u2013\u2014]")


if __name__ == "__main__":
    unittest.main()
