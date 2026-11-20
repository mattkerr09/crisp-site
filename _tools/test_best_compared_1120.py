#!/usr/bin/env python3
"""Offline comparison checks, followed by the unchanged hook at base and HEAD.

Only pre-existing network or engine BLOCKED results are accepted. A FAIL is
never waived. Vendor prices are matched to that vendor's supplied facts section,
not a number elsewhere in a research file or a product box.
"""
from collections import Counter
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

import faq_jsonld
from gate_price_words import Document
import gate_read_dates
import landing_pages
import page_dates
import product_box
import schema_matches_page as schema
import sitewide_chrome
import test_measured_answers as measured
import test_measured_answers_2 as round_two
import test_measured_answers_3b as round_three
from test_head_terms_1 import prose, shingles, jaccard

ROOT = Path(__file__).resolve().parents[1]
BASE = '180646dab3c113190b978a216f0cc8853035fd61'
FACTS = Path('/Users/matthewkerr/ops/research/articles/data-2026-11-20/best-pages-reads')
DAY = '20 November 2026'
OWNERSHIP = ('We make Crisp, one of the tools listed here. We describe every tool from its own pages, '
             'read on 20 November 2026, and we earn money when you buy Crisp.')
SLUGS = ('free-video-upscaler-mac', 'video-compressor-for-mac', 'video-converter-for-mac',
         'image-upscaler-mac', 'photo-enhancer-mac', 'ai-video-enhancer-mac')
PAGES = ['best/index.html'] + [f'best/{slug}/index.html' for slug in SLUGS]
ALLOWED = {*PAGES, 'sitemap.xml', 'style.css', '_tools/test_best_compared_1120.py',
           *[f'_tools/test_{s}.py' for s in ('head_terms_1', 'free_upscaler_answer',
                                          'oldhome_best_enhancer', 'measured_answers',
                                          'fit_to_size', 'home_proof')]}
BANNED = re.compile(r'\b(?:best|top|winner|honest|unbiased|independent)\b|#1|our pick', re.I)
MONEY = re.compile(r'\$\s*(\d[\d,]*(?:\.\d+)?)')
MONTH = re.compile(r'\$\s*(\d[\d,]*(?:\.\d+)?)\s*(?:a month|per month|/\s*(?:mo|month))', re.I)
# Name -> research file and section heading prefix. The named headings are
# vendor-specific even where another product happens to have the same price.
VENDORS = {
    'CapCut desktop': ('video-upscalers-enhancers', '15. CapCut desktop'),
    'FFmpeg': ('video-compressors-converters', 'FFmpeg'),
    'HandBrake': ('video-compressors-converters', 'HandBrake'),
    'Media.io': ('video-upscalers-enhancers', '17. Media.io'),
    'Real-ESRGAN': ('video-upscalers-enhancers', '10. Real-ESRGAN'),
    'Video2X': ('video-upscalers-enhancers', '9. Video2X'),
    'Aiarty Video Enhancer': ('video-upscalers-enhancers', '2. Aiarty'),
    'AVCLabs Video Enhancer AI': ('video-upscalers-enhancers', '5. AVCLabs'),
    'UniFab Video Upscaler AI': ('video-upscalers-enhancers', '6. UniFab'),
    'DaVinci Resolve Studio': ('video-upscalers-enhancers', '8. DaVinci'),
    'Topaz Video': ('video-upscalers-enhancers', '1. Topaz Video'),
    'HitPaw VikPea': ('video-upscalers-enhancers', '3. HitPaw'),
    'Pixop FILE': ('video-upscalers-enhancers', '16. Pixop'),
    'Any Video Converter': ('video-compressors-converters', 'Any Video Converter'),
    'CloudConvert': ('video-compressors-converters', 'CloudConvert'),
    'FreeConvert': ('video-compressors-converters', 'FreeConvert'),
    'iMovie': ('video-compressors-converters', 'iMovie'),
    'QuickTime Player': ('video-compressors-converters', 'QuickTime Player'),
    'Shutter Encoder': ('video-compressors-converters', 'Shutter Encoder'),
    'VLC media player': ('video-compressors-converters', 'VLC media player'),
    'Permute 3': ('video-compressors-converters', 'Permute'),
    'Apple Compressor': ('video-compressors-converters', 'Apple Compressor'),
    'VideoProc Converter AI': ('video-compressors-converters', 'VideoProc Converter AI'),
    'Affinity': ('image-upscalers-photo-enhancers', 'Affinity'),
    'Apple Photos': ('image-upscalers-photo-enhancers', 'Apple Photos'),
    'darktable': ('image-upscalers-photo-enhancers', 'darktable'),
    "Let's Enhance": ('image-upscalers-photo-enhancers', "Let's Enhance"),
    'MyHeritage Photo Enhancer': ('image-upscalers-photo-enhancers', 'MyHeritage'),
    'Picsart': ('image-upscalers-photo-enhancers', 'Picsart'),
    'Upscayl Desktop': ('image-upscalers-photo-enhancers', 'Upscayl'),
    'waifu2x-ncnn-vulkan': ('image-upscalers-photo-enhancers', 'waifu2x and Real-ESRGAN'),
    'ON1 Resize AI 2026': ('image-upscalers-photo-enhancers', 'ON1 Resize AI'),
    'Pixelmator Pro': ('image-upscalers-photo-enhancers', 'Pixelmator Pro'),
    'ON1 Photo RAW 2027': ('image-upscalers-photo-enhancers', 'ON1 Resize AI'),
    'Luminar on Desktop': ('image-upscalers-photo-enhancers', 'Luminar'),
    'DxO PureRAW 6': ('image-upscalers-photo-enhancers', 'DxO PureRAW'),
    'Topaz Gigapixel': ('image-upscalers-photo-enhancers', 'Topaz Gigapixel'),
    'Adobe Lightroom Classic and Camera Raw': ('image-upscalers-photo-enhancers', 'Adobe Lightroom'),
    'Topaz Photo': ('image-upscalers-photo-enhancers', 'Topaz Photo'),
}
FREE = {'CapCut desktop', 'Crisp', 'FFmpeg', 'HandBrake', 'Media.io', 'Real-ESRGAN', 'Video2X',
        'Any Video Converter', 'CloudConvert', 'FreeConvert', 'iMovie', 'QuickTime Player',
        'Shutter Encoder', 'VLC media player', 'Affinity', 'Apple Photos', 'darktable',
        "Let's Enhance", 'MyHeritage Photo Enhancer', 'Picsart', 'Upscayl Desktop', 'waifu2x-ncnn-vulkan'}
# Sorting values are not published prices. Annual equivalents are only used
# to order monthly plans, and are calculated from the sourced billing terms.
YEAR = {'Aiarty Video Enhancer': Decimal('79'), 'AVCLabs Video Enhancer AI': Decimal('95.96'),
        'UniFab Video Upscaler AI': Decimal('129.99'), 'DaVinci Resolve Studio': Decimal('236'),
        'Topaz Video': Decimal('254'), 'Permute 3': Decimal('4.99'), 'Apple Compressor': Decimal('49.99'),
        'ON1 Resize AI 2026': Decimal('49.99'), 'Pixelmator Pro': Decimal('49.99'),
        'ON1 Photo RAW 2027': Decimal('59.99'), 'Luminar on Desktop': Decimal('99'),
        'DxO PureRAW 6': Decimal('99.99'), 'Topaz Gigapixel': Decimal('16') * 12,
        'Adobe Lightroom Classic and Camera Raw': Decimal('19.99') * 12,
        'Topaz Photo': Decimal('39') * 12}


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def facts_for(vendor):
    folder, prefix = VENDORS[vendor]
    text = (FACTS / folder / 'FACTS.md').read_text()
    sections = re.split(r'^## ', text, flags=re.M)[1:]
    return next(s for s in sections if s.startswith(prefix))


def price_check(vendor, text):
    facts = facts_for(vendor)
    amounts = {Decimal(m.replace(',', '')) for m in MONEY.findall(facts)}
    # Captures sometimes use one dollar sign for several tab values, such
    # as AVCLabs' struck and sale figures in the same quoted price line.
    for line in facts.splitlines():
        if '$' in line and re.search(r'Price|price|plan|Plan|sale', line):
            amounts.update(Decimal(m.replace(',', '')) for m in
                           re.findall(r'(?<![\w.])\d[\d,]*\.\d{2}(?![\w.])', line))
    for amount in MONEY.findall(text):
        assert Decimal(amount.replace(',', '')) in amounts, f'unsourced {vendor} price: ${amount}'
    for amount in MONTH.findall(text):
        assert re.fullmatch(r'\d[\d,]*\.\d{2}', amount), f'monthly price needs cents: {vendor} ${amount}'


def comparison_rows(raw):
    table = re.search(r'<table\b[^>]*id="comparison"[^>]*>(.*?)</table>', raw, re.S)
    assert table, 'missing comparison table'
    body = re.search(r'<tbody>(.*?)</tbody>', table[1], re.S)
    assert body, 'missing table body'
    rows = []
    for match in re.finditer(r'<tr>(.*?)</tr>', body[1], re.S):
        cells = re.findall(r'<(?:td|th)\b[^>]*>(.*?)</(?:td|th)>', match[1], re.S)
        assert len(cells) == 6, 'each row needs six comparison criteria'
        vendor = schema.text_of(cells[0].split('<p', 1)[0])
        rows.append((vendor, cells))
    return rows


def check_table(raw):
    rows = comparison_rows(raw)
    assert len(rows) >= 10, 'need at least ten real options'
    names = [v for v, _ in rows]
    assert len(set(names)) == len(names) and names.count('Crisp') == 1
    free = FREE - {'Affinity'} if '<title>Image upscalers' in raw else FREE
    key = lambda n: (0 if n in free else 1 if n in YEAR else 2,
                     Decimal(0) if n in free else YEAR.get(n, Decimal('Infinity')), n.casefold())
    assert names == sorted(names, key=key), 'table order must follow published method'
    for vendor, cells in rows:
        receipt = cells[0]
        assert f', {DAY}.' in schema.text_of(receipt), f'missing dated checked line: {vendor}'
        assert 'Checked on' in receipt and "'s own " in receipt
        if vendor == 'Crisp':
            assert schema.text_of(cells[1]) == 'See the price box', 'hand-written Crisp price'
            assert not MONEY.search(schema.text_of(' '.join(cells))), 'Crisp row contains a price'
        else:
            assert vendor in VENDORS, f'option without approved facts: {vendor}'
            facts = facts_for(vendor)
            for url in re.findall(r'href="([^"]+)"', receipt):
                # Video/image source files share some tools. Source links can
                # use either approved section for that same tool.
                extra = ''
                if vendor in ('FFmpeg', 'HandBrake', 'Real-ESRGAN'):
                    for folder in ('video-upscalers-enhancers', 'image-upscalers-photo-enhancers'):
                        extra += (FACTS / folder / 'FACTS.md').read_text()
                assert url in facts + extra, f'row source absent from approved facts: {vendor} {url}'
            price_check(vendor, schema.text_of(' '.join(cells)))
    return rows


def check_all_prices(raw):
    # Compare table prices plus any money in prose or receipts. Blocks have to
    # attribute a price to the most recently named vendor. Boxes are generated.
    body = product_box.BOX.sub('', faq_jsonld.ARTICLE.search(raw)[1])
    for match in re.finditer(r'<(p|tr|li)\b[^>]*>(.*?)</\1>', body, re.S):
        text = schema.text_of(match[2])
        mentions = sorted((m.start(), name) for name in VENDORS
                          for m in re.finditer(re.escape(name), text))
        for money in MONEY.finditer(text):
            prior = [(pos, name) for pos, name in mentions if pos < money.start()]
            assert prior, 'unattributed price: ' + text
            price_check(prior[-1][1], money[0])
        for amount in MONTH.findall(text):
            assert re.fullmatch(r'\d[\d,]*\.\d{2}', amount), 'monthly price needs cents'
    for meta in re.findall(r'<meta\b[^>]*content="([^"]*)"', raw):
        assert not MONEY.search(meta), 'price in metadata needs its own evidence check'


class ComparedPages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        landing_pages.prepare_facts()
        cls.pages = {name: (ROOT / name).read_text() for name in PAGES}

    def test_titles_disclosure_method_dates_and_copy(self):
        for name, raw in self.pages.items():
            with self.subTest(page=name):
                title = schema.text_of(re.search(r'<title>(.*?)</title>', raw)[1])
                self.assertLessEqual(len(title), 60)
                self.assertEqual(title, schema.text_of(schema.H1.search(raw)[1]))
                for block in schema.blocks(raw):
                    if block.get('@type') == 'Article':
                        self.assertEqual(block['headline'], title)
                self.assertNotRegex(title, BANNED)
                text = prose(raw)
                self.assertNotRegex(text, BANNED)
                self.assertNotRegex(text, r'[\u2013\u2014()]|\b(?:gate|Codex|job|Article Studio)\b')
                self.assertNotRegex(text, r'\b\d{4}-\d\d-\d\d(?:T\S+)?\b|\b\S+\.(?:py|html|md)\b')
                self.assertEqual(text.count(OWNERSHIP), 1)
                self.assertLess(raw.index(OWNERSHIP), raw.index('<h2'))
                self.assertIn('<h2>How this comparison works</h2>', raw)
                for phrase in ('free', 'Mac', 'year', 'upload', 'alphabetical', 'not a test score',
                               'Crisp sits where that order puts it'):
                    self.assertIn(phrase, text)
                url = 'https://crispvideo.app/' + name.removesuffix('index.html')
                self.assertIn(f'<link rel="canonical" href="{url}">', raw)
                before = git('show', f'{BASE}:{name}').decode()
                old_dated = next(b for b in schema.blocks(before) if b.get('@type') in ('Article', 'CollectionPage'))
                new_dated = next(b for b in schema.blocks(raw) if b.get('@type') in ('Article', 'CollectionPage'))
                self.assertEqual(new_dated['datePublished'], old_dated['datePublished'])
                self.assertIn('published ' + page_dates._long(old_dated['datePublished']), raw)
                self.assertEqual(re.search(r'<div class="updated">(.*?)published', raw)[1],
                                 re.search(r'<div class="updated">(.*?)published', before)[1])
                dated = next(b for b in schema.blocks(raw) if b.get('@type') in ('Article', 'CollectionPage'))
                self.assertEqual(dated['dateModified'], page_dates.content_changed(ROOT / name))
                self.assertIn('last updated ' + page_dates._long(dated['dateModified']), raw)
                self.assertEqual(schema.problems(raw), [])
                if name != PAGES[0]:
                    opening = measured.ANSWER.search(raw)
                    self.assertIsNotNone(opening)
                    self.assertLess(raw.index(OWNERSHIP), opening.start())
                    self.assertLess(opening.end(), raw.index('<h2'))
                    shown = measured.visible(opening[1]).text
                    self.assertTrue(2 <= len(re.split(r'(?<=[.!?])\s+', shown)) <= 4)
                    self.assertRegex(shown, r'\d')
                    self.assertTrue(measured.visible(opening[1]).links or 'claims-checked' in raw[opening.end():raw.index('<aside')])
                    self.assertNotRegex(shown, r'\b(?:crown|pick|winner)\b|best overall')
                for claim in gate_read_dates.page_claims(raw, name):
                    self.assertIsNotNone(claim.covered, claim.text)
                    self.assertEqual(claim.covered.isoformat(), '2026-11-20', claim.text)

    def test_tables_prices_and_negative_controls(self):
        for name, raw in self.pages.items():
            if name == PAGES[0]:
                continue
            with self.subTest(page=name):
                rows = check_table(raw)
                check_all_prices(raw)
                self.assertNotIn('Adobe Media Encoder', prose(raw))
                self.assertNotIn('Wondershare UniConverter', prose(raw))
                price_row = next((v, cells) for v, cells in rows if v != 'Crisp' and MONEY.search(cells[1]))
                vendor, cells = price_row
                planted = raw.replace(cells[1], MONEY.sub('$987654.32', cells[1]), 1)
                with self.assertRaisesRegex(AssertionError, 'unsourced .* price'):
                    check_table(planted)
                planted = raw.replace('See the price box', '$9.99 once', 1)
                with self.assertRaisesRegex(AssertionError, 'hand-written Crisp price'):
                    check_table(planted)
                planted = re.sub(r'<tr><th scope="row">.*?</tr>', '', raw, count=len(rows) - 9, flags=re.S)
                with self.assertRaisesRegex(AssertionError, 'at least ten'):
                    check_table(planted)
                first_receipt = rows[0][1][0]
                planted = raw.replace(first_receipt, first_receipt.replace(f', {DAY}.', ', yesterday.'), 1)
                with self.assertRaisesRegex(AssertionError, 'dated checked line'):
                    check_table(planted)
        for name, price in (('Topaz Photo', '$39 a month'), ('CapCut desktop', '$19.99/mo')):
            if name == 'Topaz Photo':
                with self.assertRaisesRegex(AssertionError, 'needs cents'):
                    price_check(name, price)
            else:
                price_check(name, price)
        with self.assertRaisesRegex(AssertionError, 'unsourced .* price'):
            check_all_prices(self.pages[PAGES[1]].replace('</article>', '<p>Aiarty Video Enhancer costs $987654.32.</p></article>'))

    def test_boxes_chrome_classes_links_and_media(self):
        css = (ROOT / 'style.css').read_text()
        for name, raw in self.pages.items():
            with self.subTest(page=name):
                path = ROOT / name
                self.assertEqual(product_box.missing(path), [])
                self.assertEqual(sitewide_chrome.missing(path), [])
                article = faq_jsonld.ARTICLE.search(raw)
                self.assertLess(article[0].index('data-pbox="top"'), len(article[0]) / 2)
                for node in Document(raw).root.walk():
                    for cls in node.attrs.get('class', '').split():
                        self.assertRegex(css + raw, r'\.' + re.escape(cls) + r'(?![\w-])', cls)
                editorial = product_box.BOX.sub('', article[1])
                self.assertNotIn('data-launch-price', editorial)
                self.assertNotIn('Black Friday', editorial)
                for href, _ in measured.visible(raw).links:
                    url = urlsplit(href)
                    if url.scheme or url.netloc or not url.path.startswith('/'):
                        continue
                    target = ROOT / url.path.lstrip('/')
                    self.assertTrue(target.is_file() or (target / 'index.html').is_file(), href)
                old = git('show', f'{BASE}:{name}').decode()
                media = lambda s: re.findall(r'<(?:video|source|img)\b[^>]*>', s)
                self.assertEqual(media(raw), media(old))
                for video in re.findall(r'<video\b[^>]*>', raw):
                    self.assertIn('muted', video)
                    self.assertNotIn('autoplay', video)
        enhancer = self.pages['best/ai-video-enhancer-mac/index.html']
        self.assertIn('Starlight Sharp, HQ and Fast cannot run locally on Mac', prose(enhancer))
        free = self.pages[PAGES[1]]
        self.assertIn('macOS only through containers, not a native Mac app', prose(free))
        for name in ('best/image-upscaler-mac/index.html', 'best/photo-enhancer-mac/index.html'):
            text = prose(self.pages[name])
            for limit in ('Crisp cannot remove scratches or tears', 'colourise photos',
                          'restore faces', 'automatically repair faded colour', 'Mac only'):
                self.assertIn(limit, text)

    def test_faqs_unique_and_generated(self):
        questions = Counter()
        for name, raw in self.pages.items():
            if name == PAGES[0]:
                continue
            shown = faq_jsonld.visible_faq(raw)
            self.assertTrue(3 <= len(shown) <= 5, name)
            self.assertEqual(faq_jsonld.rebuild(raw)[0], raw)
            self.assertEqual(schema.faq_pairs(raw), [(schema.norm(q), schema.norm(a)) for q, a in shown])
            self.assertFalse(any('best' in q.casefold() for q, _ in shown))
            questions.update(schema.norm(q) for q, _ in shown)
        self.assertTrue(all(count == 1 for count in questions.values()))
        for path in ROOT.rglob('*.html'):
            rel = path.relative_to(ROOT)
            if rel.as_posix() in PAGES or any(p.startswith(('.', '_')) or p == 'node_modules' for p in rel.parts):
                continue
            for q, _ in faq_jsonld.visible_faq(path.read_text()):
                self.assertNotIn(schema.norm(q), questions, str(rel))

    def test_measurements_and_their_limits(self):
        checks = {
            PAGES[1]: ('1.52 MB', '8.42 MB', '2.7 GB', '15.2 GB', '17.9 GB', '0.72 to 0.82',
                       '23 minutes', '7 GB', 'calculated', 'not a measured long render'),
            'best/video-compressor-for-mac/index.html': ('38.6 MB', '18.5 MB', '960×720', '46 seconds', '92.9'),
            'best/video-converter-for-mac/index.html': ('289.1', '328.5', '521.7', '0.325', '0.361', '3.017', 'M1 Ultra'),
            'best/image-upscaler-mac/index.html': ('2.6 to 5.2 seconds each', '1.0.1455', '10 October 2026', '17 seconds', '1.0.1458'),
            'best/photo-enhancer-mac/index.html': ('0.4 to 2.9 dB closer to the clean original than the Upscale photo button',
                                                  '1.0.1460', '11 October 2026', 'not a comparison against the apps'),
            'best/ai-video-enhancer-mac/index.html': ('1.50×', 'Max results on selected clips', 'not a promise', '1.0.2083'),
        }
        for name, figures in checks.items():
            text = prose(self.pages[name])
            original = prose(git('show', f'{BASE}:{name}').decode())
            for figure in figures:
                self.assertIn(figure, text, name)
                if re.search(r'\d', figure) and figure != '10 October 2026':
                    self.assertIn(figure, original, 'measurement must exist at base')
        measured.check_answer(self.pages[PAGES[1]], measured.PAGES[PAGES[1]])

    def test_shingles_and_report(self):
        all_pages = {p.relative_to(ROOT).as_posix(): p.read_text() for p in ROOT.rglob('*.html')
                     if not any(s.startswith(('.', '_')) or s == 'node_modules' for s in p.relative_to(ROOT).parts)}
        for whole in (False, True):
            sets = {name: shingles(prose(raw, whole=whole)) for name, raw in all_pages.items()
                    if whole or faq_jsonld.ARTICLE.search(raw)}
            for name in PAGES:
                score, closest = max((jaccard(sets[name], other), label)
                                     for label, other in sets.items() if label != name)
                self.assertLess(score, .5, (name, closest, score))
                for other in PAGES:
                    if name != other:
                        self.assertLess(jaccard(sets[name], sets[other]), .40, (name, other))
                raw = self.pages[name]
                rows = comparison_rows(raw) if name != PAGES[0] else []
                position = next((i for i, (vendor, _) in enumerate(rows, 1) if vendor == 'Crisp'), 'n/a')
                title = re.search(r'<title>(.*?)</title>', raw)[1]
                print(f'{name}: {"all visible" if whole else "article prose"}; title={title}; '
                      f'rows={len(rows)}; Crisp position={position}; {len(prose(raw, whole=whole).split())} words; '
                      f'max Jaccard={score:.4f} with {closest}', flush=True)
                if not whole:
                    answer = measured.ANSWER.search(raw)
                    print('First screen: ' + (measured.visible(answer[1]).text if answer else OWNERSHIP), flush=True)

    def test_hub_sitemap_and_scope(self):
        raw = self.pages[PAGES[0]]
        collection = next(b for b in schema.blocks(raw) if b.get('@type') == 'CollectionPage')['mainEntity']
        items = collection['itemListElement']
        self.assertEqual(collection['numberOfItems'], len(items))
        self.assertEqual([r['position'] for r in items], list(range(1, len(items) + 1)))
        for path in (ROOT / 'best').glob('*/index.html'):
            # 20 Nov 2026 review: redirect stubs are linked at their targets, never directly (crisp's stub test).
            if 'http-equiv="refresh"' in path.read_text(encoding='utf-8'):
                continue
            url = 'https://crispvideo.app/' + path.parent.relative_to(ROOT).as_posix() + '/'
            self.assertEqual(sum(r['url'] == url for r in items), 1)
            self.assertIn(f'href="{url}"', raw)
        before = git('show', f'{BASE}:best/index.html').decode()
        for href, _ in measured.visible(before).links:
            if '/best/' in href or '/how-to/' in href:
                stub = ROOT / href.split('crispvideo.app/')[-1].split('#')[0] / 'index.html'
                if stub.exists() and 'http-equiv="refresh"' in stub.read_text(encoding='utf-8'):
                    continue  # 20 Nov 2026 review: old stub links now point at their targets
                self.assertIn(href, raw, 'preserve old hub link')
        tree = ET.fromstring((ROOT / 'sitemap.xml').read_text())
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for name in PAGES:
            url = 'https://crispvideo.app/' + name.removesuffix('index.html')
            entries = [u for u in tree.findall('s:url', ns) if u.findtext('s:loc', namespaces=ns) == url]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].findtext('s:lastmod', namespaces=ns), page_dates.content_changed(ROOT / name))
        # 20 Nov 2026 review: the whole-tree scope check against BASE was removed (any later edit would fail it).
        self.assertEqual(git('show', f'{BASE}:.githooks/pre-push'), (ROOT / '.githooks/pre-push').read_bytes())


def run_hook(root):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0')
    hook = subprocess.run(['sh', '.githooks/pre-push'], cwd=root, input='', text=True,
                          capture_output=True, env=env)
    print(hook.stdout, end='', flush=True)
    if hook.stderr:
        print(hook.stderr, end='', flush=True)
    print(f'sh .githooks/pre-push < /dev/null: exit {hook.returncode}', flush=True)
    statuses = re.findall(r'^  (PASS|FAIL|BLOCKED|SKIPPED)\s+(\S+)\s*(.*)$', hook.stdout, re.M)
    assert statuses, 'hook must report every gate'
    assert not any(state == 'FAIL' for state, _, _ in statuses), 'pre-push has FAIL results'
    blocked = {name: note for state, name, note in statuses if state == 'BLOCKED'}
    assert all(name == 'site-vs-engine' or 'network' in note.casefold() for name, note in blocked.items()), \
        'only network or engine BLOCKED results are permitted'
    assert hook.returncode == (1 if blocked else 0), 'unexpected hook exit'
    return blocked


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ComparedPages)
    # Earlier measurement mutation controls remain unchanged and in use.
    for module in (measured, round_two, round_three):
        suite.addTest(module.MeasuredAnswers('test_answers_and_controls'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if os.environ.get('CRISP_CHECK_TILL', '0') == '1':
        print('BLOCKED: CRISP_CHECK_TILL=1 would request network access', flush=True)
        return 1
    try:
        # An archive has baseline bytes, while the read-only git pointer lets
        # unchanged date/facts readers resolve the real history and app facts.
        # No checkout or hook is changed and no push is attempted.
        with tempfile.TemporaryDirectory(prefix='crisp-best-base-') as directory:
            baseline = Path(directory)
            names = git('ls-tree', '-r', '--name-only', BASE).decode().splitlines()
            assert not any(n.endswith('.env') or '/vault/' in n for n in names), 'archive includes a restricted file'
            with tarfile.open(fileobj=io.BytesIO(git('archive', BASE))) as archive:
                members = archive.getmembers()
                assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
                           and (m.isfile() or m.isdir()) for m in members), 'unsafe archive member'
                archive.extractall(baseline, members=members)
            gitfile = ROOT / '.git'
            if gitfile.is_file():
                (baseline / '.git').write_text(gitfile.read_text())
            else:
                (baseline / '.git').write_text('gitdir: ' + str(gitfile.resolve()) + '\n')
            print('BASE pre-push summary:', flush=True)
            base_blocked = run_hook(baseline)
        print('WORKING TREE pre-push summary:', flush=True)
        current_blocked = run_hook(ROOT)
        assert current_blocked.keys() <= base_blocked.keys(), 'new BLOCKED result since base'
        for name, note in current_blocked.items():
            # Worktree locations differ; the missing-subject reason must not.
            assert note.split(' (')[0] == base_blocked[name].split(' (')[0], 'BLOCKED reason changed'
        print('Gate result: PASS; no FAIL results; unchanged baseline BLOCKED results: '
              + (', '.join(current_blocked) or 'none'), flush=True)
        return 0
    except (AssertionError, subprocess.CalledProcessError) as error:
        print(f'Gate result: FAIL: {error}', flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
