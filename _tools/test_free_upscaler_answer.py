#!/usr/bin/env python3
"""Offline checks for the existing free Mac upscaler article.

The approved job base is pinned so preservation checks still work after a commit.
Use --page /tmp/base.html --answer-only to show that the old answer fails.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import urlsplit

import faq_jsonld
import gate_read_dates
import landing_pages
import product_box
from test_head_terms_1 import check_comparison
import schema_matches_page

# 20 Nov 2026 (Article Studio): find the reviewed compared-pages commit by its subject, not its hash, so a rebase keeps
# this test working. Falls back to the original hash if the subject is not in this history.
def _compared_commit():
    import subprocess as _sp
    out = _sp.run(["git", "log", "--format=%H", "-n", "1", "--fixed-strings",
                   "--grep=codex: cx-20261120-1400-crispsite-best-compared Reworked seven pages"],
                  cwd=str(Path(__file__).resolve().parent.parent), capture_output=True, text=True).stdout.strip()
    return out or "90ae8a080e8832b077312d84fb06496a25674d77"


COMPARED = _compared_commit()


SITE = Path(__file__).resolve().parents[1]
REL = "best/free-video-upscaler-mac/index.html"
CANONICAL = "https://crispvideo.app/best/free-video-upscaler-mac/"
BASE = "b8b3dd50cfebb6df39bf5a6cad90f1f209bf10ca"
PAGE = SITE / REL
VOID = set("area base br col embed hr img input link meta param source track wbr".split())


def base_file(path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{BASE}:{path}"], cwd=SITE, check=True,
        capture_output=True, text=True).stdout


class ArticleText(HTMLParser):
    """Article words without navigation, dates, product boxes or download chrome."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        article = tag == "article" or bool(self.stack and self.stack[-1][1])
        skip = bool(self.stack and self.stack[-1][2])
        skip |= tag in {"script", "style", "template", "noscript", "nav", "footer", "header", "aside"}
        skip |= bool(set(attrs.get("class", "").split()) & {"crumb", "updated", "pbox", "cta"})
        self.parts.append(" ")
        if tag not in VOID:
            self.stack.append((tag, article, skip))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        self.parts.append(" ")

    def handle_data(self, data):
        if self.stack and self.stack[-1][1] and not self.stack[-1][2]:
            self.parts.append(data)


def words(source: str) -> list[str]:
    # Related links are navigation, not article substance.
    source = re.sub(r'<h2\b[^>]*>Related</h2>.*?(?=</article>)', '', source, flags=re.S | re.I)
    return re.findall(r"[a-z0-9]+(?:['’][a-z]+)?", "".join(ArticleText(source).parts).lower())


def shingles(source: str) -> set[tuple[str, ...]]:
    tokens = words(source)
    return {tuple(tokens[i:i + 5]) for i in range(len(tokens) - 4)}


def answer_control(source: str) -> None:
    quick = re.search(r'<div class="quick">(.*?)</div>', source, re.S)
    assert quick, "missing near-top answer"
    answer = schema_matches_page.text_of(quick.group(1))
    # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: opening now answers the comparison; free terms remain below.
    required = ("Free video upscaling on a Mac", "15 seconds", "crispvideo.app", "29 seconds", "132 frames", "M1 Ultra")
    missing = [phrase for phrase in required if phrase not in answer]
    assert not missing, f"near-top free-limit answer missing: {missing}"
    assert source.index('class="quick"') < source.index('data-pbox="top"')


class FreeUpscalerAnswer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text()
        cls.base = base_file(REL)

    def test_direct_answer_and_useful_sample(self):
        answer_control(self.source)
        sample = self.source.split('<h2>Try a short sample of an old home video</h2>', 1)[1].split('<h2>', 1)[0]
        shown = schema_matches_page.text_of(sample)
        for phrase in ("Keep that source unchanged", "Trim", "15 seconds", "stretched", "Comb teeth",
                       "Enhance", "Auto", "Run", "Before / After", "waxy skin", "shimmers", "use it instead"):
            self.assertIn(phrase, shown)
        self.assertIn('href="https://crispvideo.app/how-to/upscale-video-on-mac/"', sample)

    def test_faq_and_schema_agree(self):
        shown = faq_jsonld.visible_faq(self.source)
        schema = schema_matches_page.faq_pairs(self.source)
        self.assertEqual(schema, [(schema_matches_page.norm(q), schema_matches_page.norm(a)) for q, a in shown])
        self.assertEqual(schema_matches_page.problems(self.source), [])
        answers = dict(shown)
        self.assertIn("Trim the clip", answers["Can I choose which 15 seconds to upscale?"])
        whole = answers["Can Crisp upscale a whole tape for free?"]
        self.assertTrue(whole.startswith("No."))
        for phrase in ("15 seconds", "Pro adds full-length AI exports", "Convert and Compress", '"crispvideo.app" mark'):
            self.assertIn(phrase, whole)
        rebuilt, info = faq_jsonld.rebuild(self.source)
        self.assertEqual(info["action"], "unchanged")
        self.assertEqual(rebuilt, self.source)

    def test_canonical_download_boxes_and_media_preserved(self):
        canon = re.findall(r'<link rel="canonical" href="([^"]+)"', self.source)
        self.assertEqual(canon, [CANONICAL])
        boxes = lambda s: re.findall(r'<aside class="pbox".*?</aside>', s, re.S)
        self.assertEqual(len(boxes(self.source)), 2)
        # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: render current boxes instead of pinning an expired sale.
        landing_pages.prepare_facts()
        self.assertEqual(boxes(self.source), [product_box.box(where, '/best/free-video-upscaler-mac/').strip()
                                              for where in ('top', 'end')])
        self.assertIn("src=best-free-video-upscaler-mac-pbox-top&to=https://github.com/mattkerr09/crisp-site/releases/download/v1/Crisp.dmg", self.source)
        media = lambda s: re.findall(r'<(?:img|video|source)\b[^>]*>', s)
        self.assertEqual(media(self.source), media(self.base))

    # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: expanded rivals need sourced prices and dated links, not old link counts.
    def test_comparison_links_prices_and_free_terms(self):
        check_comparison(self.source, 'Free video upscalers for Mac compared')
        shown = schema_matches_page.text_of(self.source)
        for phrase in ("Crisp's free version works offline", "no account or time limit", "full editor and preview",
                       "AI exports for upscale, restore and colour stop at 15 seconds per export",
                       'video and GIF exports carry a small "crispvideo.app" mark',
                       "All other exports run at full length", "Upscaling a whole tape needs Pro",
                       "removes the limit and mark"):
            self.assertIn(phrase, shown)

    # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: preserve measured figures and sources through the rewritten explanation.
    def test_measurements_preserved(self):
        heading = "What the free command-line route costs, measured"
        section = lambda s: s.split(f'<h2>{heading}</h2>', 1)[1].split('<h2>', 1)[0]
        old = schema_matches_page.text_of(section(self.base))
        current = schema_matches_page.text_of(section(self.source))
        # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: wording changed; all original measured numbers must survive.
        figures = lambda text: Counter(re.findall(r'(?<![\d.])\d+(?:[,.]\d+)*(?![\d.])', text))
        self.assertFalse(figures(old.replace('read 11 November 2026', '')) - figures(current))
        for phrase in ('1.52 MB', '8.42 MB', '2.7 GB', '15.2 GB', '17.9 GB',
                       '0.72 to 0.82 seconds', '23 minutes', '7 GB', 'not measured on a long render'):
            self.assertIn(phrase, old)
            self.assertIn(phrase, current)
        self.assertIn('not a measured long render', current)
        self.assertIn('href="/learn/why-4k-exports-take-so-long/"', section(self.source))
        resize = self.source.split('<h2>Our plain-resize check</h2>', 1)[1].split('<h2>', 1)[0]
        for phrase in ('three of four frames', 'all four', '23 July 2026',
                       '/learn/what-is-ai-video-upscaling/', '/learn/when-ai-upscaling-beats-a-plain-resize/#lanczos'):
            self.assertIn(phrase, resize)

    def test_dates_and_only_target_sitemap_entry(self):
        article = next(b for b in schema_matches_page.blocks(self.source) if b.get("@type") == "Article")
        # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: parse long visible dates and the Article block independent of JSON spacing.
        line = schema_matches_page.text_of(schema_matches_page.BYLINE.search(self.source)[1])
        for field, label in (('datePublished', 'published'), ('dateModified', 'last updated')):
            shown = re.search(label + r' (\d{1,2} [A-Za-z]+ \d{4})', line)[1]
            self.assertEqual(article[field], datetime.strptime(shown, '%d %B %Y').date().isoformat())
        self.assertEqual(article["datePublished"], "2026-07-04")
        self.assertEqual(article["dateModified"], "2026-11-20")
        sitemap = (SITE / "sitemap.xml").read_text()
        # Keep complete non-target entries byte-for-byte, including their original dates.
        def urls(source):
            return {re.search(r'<loc>([^<]+)</loc>', entry).group(1): entry
                    for entry in re.findall(r'<url>.*?</url>', source, re.S)}
        # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: unrelated sitemap updates already exist at this job base.
        approved = subprocess.run(['git', 'show', f'{COMPARED}:sitemap.xml'],
                                  cwd=SITE, check=True, capture_output=True, text=True).stdout
        current, base = urls(sitemap), urls(approved)
        self.assertIn(f'<lastmod>{article["dateModified"]}</lastmod>', current.pop(CANONICAL))
        base.pop(CANONICAL)
        self.assertEqual(current, base)

    def test_substance_and_distinctness(self):
        count = len(words(self.source))
        self.assertGreaterEqual(count, 300)
        target = shingles(self.source)
        scores = []
        for path in sorted(SITE.rglob("*.html")):
            rel = path.relative_to(SITE)
            if path == SITE / REL or any(p.startswith(("_", ".")) or p == "node_modules" for p in rel.parts):
                continue
            source = path.read_text()
            if not re.search(r'<html\b[^>]*\blang=["\']en(?:-[\w]+)?["\']', source, re.I):
                continue
            if "<article" not in source or gate_read_dates.is_stub(source):
                continue
            other = shingles(source)
            if other:
                scores.append((len(target & other) / len(target | other), rel.as_posix()))
        self.assertTrue(scores, "distinctness check must see existing English articles")
        score, closest = max(scores)
        print(f"Article: {count} words without chrome; {len(scores)} English articles compared; "
              f"maximum 5-word-shingle Jaccard {score:.4f} at {closest}")
        self.assertLess(score, 0.5, f"near duplicate of {closest}")


def main() -> int:
    global PAGE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path, default=PAGE)
    parser.add_argument("--answer-only", action="store_true")
    args = parser.parse_args()
    PAGE = args.page
    if args.answer_only:
        try:
            answer_control(PAGE.read_text())
        except AssertionError as error:
            print(f"FAIL: {error}")
            return 1
        print("PASS: near-top free-limit answer")
        return 0
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FreeUpscalerAnswer))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
