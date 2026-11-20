#!/usr/bin/env python3
"""Offline source and copy checks for the family-video upload explainer.

Captures are required evidence, not optional fixtures. Missing captures fail.
"""
from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

import faq_jsonld
import schema_matches_page
import sitewide_chrome
import product_box
import landing_pages

SITE = Path(__file__).resolve().parents[1]
CAPTURES = Path('/Users/matthewkerr/ops/research/crisp-no-upload-captures-2026-11-20')
SLUG = 'is-it-safe-to-upload-family-videos-to-an-ai-upscaler'
REL = f'learn/{SLUG}/index.html'
URL = f'https://crispvideo.app/learn/{SLUG}/'
TITLE = 'Is it safe to upload family videos to an AI upscaler?'
MISSING = 'Not stated on the page we read'
# Preserve the captured policy's typographic apostrophes around Free.
POLICIES = {
    'avclabs': ('AVCLabs Online Video Enhancer', 'https://www.avclabs.com/privacy-policy.html', [
        ['The files includes images and/or videos you uploaded to our Services will be automatically deleted from our server after 3 days.'], [], []]),
    'hitpaw': ('HitPaw online tools', 'https://www.hitpaw.com/privacy-policy.html', [
        ['the system will automatically delete the relevant data and cache records within seven (7) days after processing is completed'],
        ['will not be used for model training, algorithm optimization'], []]),
    'cutout': ('Cutout.pro', 'https://www.cutout.pro/privacy', [
        ['Any uploaded images and videos, processed or non-processed will be deleted automatically.'], [], []]),
    'veed': ('VEED', 'https://www.veed.io/privacy', [
        ['as long as reasonably necessary'],
        ['by users under a ‘Free’ subscription', 'training and developing any relevant artificial intelligence models'], []]),
    'capcut': ('CapCut', 'https://www.capcut.com/clause/privacy', [
        [], ['train, test, and improve technology, such as machine learning models and algorithms'], []]),
    'pixop': ('Pixop', 'https://www.pixop.com/privacy-policy', [
        [], [], ['primary region AWS Europe (Ireland), within the EEA']]),
}
GYAZO_URL = 'https://www.helpnetsecurity.com/2026/09/21/helpfeel-gyazo-data-breach/'
GYAZO_QUOTES = [
    'exploited a vulnerability in its image upload server, stealing approximately 23.62 million user records',
    'approximately 490 million records',
    'EXIF location data where present, OCR text extracted from images',
]


def normal(text: str) -> str:
    return ' '.join(unescape(text).split())


def visible(source: str) -> str:
    source = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', source, flags=re.S | re.I)
    return normal(re.sub(r'<[^>]+>', ' ', source))


def capture_text(name: str, root: Path = CAPTURES) -> str:
    path = root / f'{name}.html'
    # read_text deliberately raises on a missing or unreadable source.
    text = visible(path.read_text(encoding='utf-8'))
    assert text, f'Empty capture: {path}'
    return text


class PolicyTable(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.cells = None
        self.cell = None
        self.quote = None
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            self.cells = []
        elif tag in {'th', 'td'}:
            self.cell = {'text': [], 'links': [], 'quotes': []}
        elif tag == 'a' and self.cell is not None:
            self.cell['links'].append(attrs)
        elif tag == 'q' and self.cell is not None:
            self.quote = {'cite': attrs.get('cite'), 'text': []}

    def handle_data(self, data):
        if self.cell is not None:
            self.cell['text'].append(data)
        if self.quote is not None:
            self.quote['text'].append(data)

    def handle_endtag(self, tag):
        if tag == 'q' and self.quote is not None:
            self.quote['text'] = normal(''.join(self.quote['text']))
            self.cell['quotes'].append(self.quote)
            self.quote = None
        elif tag in {'th', 'td'} and self.cell is not None:
            self.cell['text'] = normal(' '.join(self.cell['text']))
            self.cells.append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.cells is not None:
            self.rows.append(self.cells)
            self.cells = None


class NoUploadPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (SITE / REL).read_text(encoding='utf-8')
        cls.article = re.search(r'<article\b[^>]*>(.*?)</article>', cls.source, re.S).group(1)

    def test_policy_quotes_match_required_captures(self):
        table = re.findall(r'<table\b[^>]*>.*?</table>', self.article, re.S)
        self.assertEqual(len(table), 1)
        rows = PolicyTable(table[0]).rows
        self.assertEqual(len(rows), 7)
        for row, (name, (label, url, expected)) in zip(rows[1:], POLICIES.items()):
            with self.subTest(policy=name):
                captured = capture_text(name)
                self.assertEqual(len(row), 4)
                self.assertIn(label, row[0]['text'])
                self.assertIn('Read 20 November 2026', row[0]['text'])
                self.assertTrue(any(a.get('href') == url and 'nofollow' in a.get('rel', '').split()
                                    for a in row[0]['links']))
                for cell, quotes in zip(row[1:], expected):
                    self.assertEqual([q['text'] for q in cell['quotes']], quotes)
                    if not quotes:
                        self.assertEqual(cell['text'], MISSING)
                    for quote in cell['quotes']:
                        self.assertIn(quote['text'], captured, f'{name}: quote not in capture')
                        self.assertEqual(quote['cite'], url)
                        self.assertTrue(any(a.get('href') == url and 'nofollow' in a.get('rel', '').split()
                                            for a in cell['links']))
        self.assertIn('Policies change. Read each one yourself before you upload; these are what each page said on 20 November 2026.', visible(self.article))
        self.assertIn('Cutout.pro\'s quoted sentence gives no deletion time.', visible(self.article))
        veed = visible(re.findall(r'<tr>.*?</tr>', table[0], re.S)[4])
        for phrase in ('may be used', 'excludes uploads from its mobile apps'):
            self.assertIn(phrase, veed)

    def test_capture_reader_fails_when_missing_and_normalises_entities(self):
        with self.assertRaises(FileNotFoundError):
            capture_text('missing-source-for-test')
        self.assertEqual(visible('<p>A&nbsp;B\n &amp; <b>C</b></p>'), 'A B & C')
        self.assertNotEqual(normal('‘Free’'), normal("'Free'"))

    def test_gyazo_source_and_careful_context(self):
        captured = capture_text('helpnetsecurity-gyazo')
        paragraph = next(p for p in re.findall(r'<p\b[^>]*>.*?</p>', self.article, re.S)
                         if GYAZO_URL in p)
        for quote in GYAZO_QUOTES:
            self.assertIn(quote, captured)
            self.assertIn(quote, visible(paragraph))
        self.assertIn(f'href="{GYAZO_URL}" rel="nofollow"', paragraph)
        for phrase in ('21 September 2026', 'read 20 November 2026',
                       'Gyazo is a screenshot-sharing service, not a video upscaler.',
                       'whatever you upload is held somewhere.'):
            self.assertIn(phrase, visible(paragraph))
        # No incident claim may name one of the compared services, even as an implication.
        for block in re.findall(r'<(?:p|tr|li)\b[^>]*>.*?</(?:p|tr|li)>', self.article, re.S):
            text = visible(block)
            if re.search(r'\b(?:AVCLabs|HitPaw|Cutout\.pro|VEED|CapCut|Pixop)\b', text, re.I):
                self.assertNotRegex(text, r'(?i)\b(?:breach\w*|hack\w*|attack\w*|leak\w*|stolen|incident|compromis\w*|expos\w*)\b')

    def test_measured_numbers_and_scope(self):
        readme = (CAPTURES / 'netmeasure/README.md').read_text()
        result = json.loads((CAPTURES / 'netmeasure/result-2026-11-20T0441Z.json').read_text())
        self.assertEqual(result['job']['status'], 'done')
        self.assertEqual(result['build']['number'], 2089)
        self.assertEqual(result['job']['seconds'], 31.6)
        processes = result['external_bytes_by_process']
        # The JSON includes the measuring Python process. Only Crisp counts toward this claim.
        sent = sum(p['bytes_out'] for name, p in processes.items() if name.startswith('crisp.'))
        self.assertEqual(sent, 0)
        self.assertEqual(result['external_connections_seen'], [])
        self.assertIn('sent 0 bytes', readme)
        self.assertIn('20 s, 640x360', readme)
        text = visible(self.article)
        measured = re.search(r'During the ([\d.]+)-second job Crisp sent (\d+) bytes off the Mac\.', text)
        self.assertIsNotNone(measured)
        self.assertEqual(float(measured[1]), result['job']['seconds'])
        self.assertEqual(int(measured[2]), sent)
        build = re.search(r'20-second clip in Crisp 1\.0\.(\d+) on a Mac', text)
        self.assertIsNotNone(build)
        self.assertEqual(int(build[1]), result['build']['number'])
        for phrase in ('20 November 2026', '2× restore', 'one job with one clip', 'Pro licence',
                       'M1 Ultra', 'nettop', 'lsof', 'every two seconds',
                       'Checking for updates.', 'Licence activation and a weekly re-check.',
                       'The sale-price check on a free copy.', 'The one-time download of the Max model.',
                       'None of these carry your video.'):
            self.assertIn(phrase, text)

    def test_no_promises_and_no_typed_prices(self):
        # The requested question is allowed; a promise of safety elsewhere is not.
        metadata = ' '.join(re.findall(r'<meta\b[^>]*content="([^"]*)"', self.source))
        structured = ' '.join(json.dumps(b, ensure_ascii=False) for b in schema_matches_page.blocks(self.source))
        source = unescape(visible(self.source) + ' ' + metadata + ' ' + structured)
        source = source.replace(TITLE, '').replace(SLUG, '')
        self.assertNotRegex(source, r'(?i)\b(?:secure|safe)\b|100\s*%|hack[- ]proof|nothing\s+is\s+uploaded')
        copy = re.sub(r'<aside\b.*?</aside>', '', self.article, flags=re.S)
        self.assertNotRegex(visible(copy), r'[$€£]\s*\d')
        self.assertNotRegex(visible(self.article), '[\u2013\u2014]')
        for phrase in ("Crisp's Max mode can draw detail that was not in the film.",
                       'It is for watching, not evidence.', 'Pro removes it.', 'crispvideo.app'):
            self.assertIn(phrase, visible(self.article))

    def test_metadata_faq_and_chrome(self):
        title = re.search(r'<title>(.*?)</title>', self.source).group(1)
        h1 = re.findall(r'<h1>(.*?)</h1>', self.article)
        self.assertEqual(h1, [TITLE])
        self.assertEqual(title, TITLE)
        for field in ('og:title', 'twitter:title'):
            match = re.search(r'<meta (?:property|name)="'+field+r'" content="([^"]+)"', self.source)
            self.assertIsNotNone(match)
            self.assertEqual(unescape(match[1]), TITLE)
            self.assertLessEqual(len(unescape(match[1])), 60)
        self.assertLessEqual(len(title), 60)
        description = re.search(r'<meta name="description" content="([^"]+)"', self.source)[1]
        self.assertLessEqual(len(unescape(description)), 165)
        self.assertIn(f'<link rel="canonical" href="{URL}">', self.source)
        shown = faq_jsonld.visible_faq(self.source)
        self.assertEqual([q for q, _ in shown], ['Does Crisp upload my video?',
                                              'Do online upscalers keep my videos?',
                                              'How can I check what an app sends?'])
        schema = next(b for b in schema_matches_page.blocks(self.source) if b.get('@type') == 'FAQPage')
        self.assertEqual([(q['name'], q['acceptedAnswer']['text']) for q in schema['mainEntity']], shown)
        self.assertEqual(schema_matches_page.problems(self.source), [])
        self.assertEqual(sitewide_chrome.missing(SITE / REL), [])
        landing_pages.prepare_facts()
        self.assertEqual(product_box.missing(SITE / REL), [])
        self.assertLess(self.article.index('class="quick"'), self.article.index('data-pbox="top"'))
        classes = set(re.findall(r'class="([^"]+)"', self.source))
        css = (SITE / 'style.css').read_text()
        for group in classes:
            for name in group.split():
                self.assertTrue(re.search(r'\.'+re.escape(name)+r'(?![\w-])', css)
                                or re.search(r'\.'+re.escape(name)+r'(?![\w-])', self.source), name)

    def test_incoming_links_and_sitemap(self):
        for rel in ('learn/index.html', 'vs/avclabs-video-enhancer-alternative-mac/index.html',
                    'vs/hitpaw-vikpea-alternative-mac/index.html', 'for/genealogists/index.html'):
            text = (SITE / rel).read_text()
            self.assertEqual(text.count(f'href="{URL}"'), 1, rel)
        hub = (SITE / 'learn/index.html').read_text()
        collection = next(b for b in schema_matches_page.blocks(hub) if b.get('@type') == 'CollectionPage')
        items = collection['mainEntity']['itemListElement']
        self.assertEqual(collection['mainEntity']['numberOfItems'], len(items))
        self.assertEqual(sum(item['url'] == URL for item in items), 1)
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        entries = ET.parse(SITE / 'sitemap.xml').findall('s:url', ns)
        entry = [e for e in entries if e.findtext('s:loc', namespaces=ns) == URL]
        self.assertEqual(len(entry), 1)
        self.assertEqual(entry[0].findtext('s:lastmod', namespaces=ns), '2026-11-20')


if __name__ == '__main__':
    unittest.main(verbosity=2)
