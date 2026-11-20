#!/usr/bin/env python3
"""Offline checks for the old-home workflow and the sourced Mac enhancer picks."""
from pathlib import Path
import json
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

import faq_jsonld
from gate_price_words import Document, normal
import landing_pages
import llms_txt
from schema_matches_page import text_of

SITE = Path(__file__).resolve().parents[1]
FAMILY = 'for/family-archivists/index.html'
BEST = 'best/ai-video-enhancer-mac/index.html'
URL = '/best/ai-video-enhancer-mac/'
MONEY = re.compile(r'\$[\d,]+(?:\.\d+)?')


def read(rel):
    return (SITE / rel).read_text()


def nodes(source, tag):
    return [n for n in Document(source).root.walk() if n.tag == tag]


def article(source):
    return nodes(source, 'article')[0]


def links(source):
    return {n.attrs.get('href') for n in nodes(source, 'a')}


def json_nodes(source):
    return [json.loads(n.text()) for n in nodes(source, 'script')
            if n.attrs.get('type') == 'application/ld+json']


def rival_figures(source):
    """Match each dated price set to its original site source, not just any page number."""
    home = read('index.html')
    comparison = home[home.index('<section id="compare">'):].split('</section>', 1)[0]
    rows = nodes(source, 'tr')[2:]  # header and Crisp's row are not rival prices
    expected = [
        ('Topaz Video', comparison, 'read 11 Nov 2026',
         '$299/yr, $254 first year in Topaz Video\'s sale, read 11 Nov 2026, or $59/mo',
         {'$299', '$254', '$59', '$1,495'}),
        ('Aiarty Video Enhancer', comparison, 'read 19 October 2026',
         '$235 list, $165 on offer', {'$235', '$165'}),
        ('HitPaw VikPea', comparison, 'read 19 October 2026',
         '$437.99 list, $284.69 on offer', {'$437.99', '$284.69'}),
        ('VideoProc Converter AI', read('vs/videoproc-alternative-mac/index.html'),
         'checked 19 October 2026', '$54.95', {'$54.95', '$89.95'}),
    ]
    assert len(rows) == len(expected), 'all four rivals need a price row'
    for row, (name, original, date, phrase, amounts) in zip(rows, expected):
        shown = normal(row.text())
        original = text_of(original)
        assert shown.startswith(name), 'rival row order changed'
        price_cell = [n for n in row.children if getattr(n, 'tag', '') in ('th', 'td')][1]
        assert date in normal(price_cell.text()), name + ': missing original read date'
        assert phrase in shown and phrase in original, name + ': price wording changed'
        assert set(MONEY.findall(shown)) == amounts, name + ': unsourced price'
        assert amounts <= set(MONEY.findall(original)), name + ': figure absent from source'
        assert date.removeprefix('checked ').removeprefix('read ') in original, name + ': date absent from source'
        if name == 'Topaz Video':
            assert '$1,495 at $299/yr' in shown, 'five-year cost must use the regular price'
    # Narrative may quote the ownership date, but may not introduce another rival price.
    outside = re.sub(r'<table\b.*?</table>|<aside\b.*?</aside>', '', source, flags=re.S)
    outside = text_of(re.search(r'<article>(.*?)</article>', outside, re.S)[1])
    assert not MONEY.search(outside), 'new narrative price needs a source check'


class OldHomeAndEnhancer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = read(FAMILY)
        cls.best = read(BEST)
        cls.home = read('index.html')

    def test_five_steps_and_app_words(self):
        steps = next(n for n in nodes(self.family, 'ol') if n.attrs.get('id') == 'old-home-steps')
        items = [normal(n.text()) for n in steps.children if getattr(n, 'tag', '') == 'li']
        self.assertEqual(len(items), 5)
        for item, start in zip(items, ('Get the tape into a file.', 'Open the file in Crisp.',
                                     'Interlaced tape:', 'Try a 15-second piece first.', 'Export.')):
            self.assertTrue(item.startswith(start), item)
        self.assertLess(self.family.index('id="old-home-steps"'), self.family.index('<h2>'))
        self.assertIn("Crisp doesn't capture tape", items[0])
        self.assertIn('/how-to/convert-vhs-to-digital-mac/', links(self.family))
        self.assertIn('USB capture device', items[0])
        self.assertIn('transfer service', items[0])
        self.assertIn('Free enhanced exports stop at 15 seconds', items[3])
        self.assertIn('crispvideo.app', items[4])
        self.assertIn('Pro removes it and the 15-second limit', items[4])

        landing_pages.prepare_facts()
        app = llms_txt.ENGINE.resolve().parents[2]
        ui = (app / 'ui/src/index.html').read_text()
        preset = next(n.text() for n in nodes(ui, 'option') if n.attrs.get('value') == 'homevideo')
        hint = next(n.text() for n in nodes(ui, 'p') if n.attrs.get('id') == 'ed-tape-motion-hint')
        checkbox = next(n for n in nodes(ui, 'input') if n.attrs.get('id') == 'ed-t-tape-motion')
        label = next(n for n in nodes(ui, 'label') if any(c.attrs.get('id') == 'ed-t-tape-motion'
                     for c in n.walk() if c.tag == 'input'))
        label_text = normal(label.text())
        self.assertNotIn('checked', checkbox.attrs, 'default changed in the app')
        self.assertIn("It's off by default.", items[2])
        quoted = [normal(n.text()) for n in nodes(self.family, 'q')]
        self.assertIn(preset, quoted)
        self.assertIn(label_text, quoted)
        self.assertIn(normal(hint), quoted)
        self.assertIn('in Enhance', items[2])

        # Read the shipped preset notes from app history. Never use current price copy from these old notes.
        commits = subprocess.run(['git', 'log', '-10', '--format=%H', '--', '.last_release_notes'],
                                 cwd=app, check=True, capture_output=True, text=True).stdout.splitlines()
        notes = [subprocess.run(['git', 'show', f'{sha}:.last_release_notes'], cwd=app,
                                check=True, capture_output=True, text=True).stdout for sha in commits]
        note = next(n for n in notes if 'uses Auto\'s picture fixes and turns down tape hiss' in n)
        quote = "uses Auto's picture fixes and turns down tape hiss"
        self.assertIn(quote, quoted)
        self.assertIn(note.splitlines()[0], items[1])
        self.assertIn('id="faces"', self.family)
        self.assertIn('/ww2-face-crop.jpg', self.family)
        self.assertIn('stubble the film recorded is', text_of(self.family))
        # Both merge stubs must still canonicalise to this page.
        for rel in ('best/way-to-restore-old-home-videos/index.html',
                    'how-to/restore-old-home-videos-mac/index.html'):
            canonical = next(n.attrs['href'] for n in nodes(read(rel), 'link') if n.attrs.get('rel') == 'canonical')
            self.assertEqual(canonical, 'https://crispvideo.app/for/family-archivists/')

    def test_recording_and_proof_match_home(self):
        demo = next(n for n in nodes(self.home, 'video') if 'data-demo' in n.attrs)
        cap = next(n for n in nodes(self.home, 'figcaption') if n.attrs.get('class') == 'demo-cap')
        assets = [(n.attrs['data-src'], n.attrs['type']) for n in demo.walk() if n.tag == 'source']
        for source in (self.family, self.best):
            videos = nodes(source, 'video')
            self.assertEqual(len(videos), 1)
            video = videos[0]
            for attr in ('muted', 'playsinline', 'controls'):
                self.assertIn(attr, video.attrs)
            self.assertNotIn('autoplay', video.attrs)
            self.assertEqual(video.attrs['poster'], demo.attrs['data-poster'])
            self.assertEqual([(n.attrs['src'], n.attrs['type']) for n in video.walk() if n.tag == 'source'], assets)
            for path, _ in assets:
                self.assertTrue((SITE / path.lstrip('/')).is_file())
            self.assertTrue((SITE / video.attrs['poster'].lstrip('/')).is_file())
            self.assertIn(normal(cap.text()), [normal(n.text()) for n in nodes(source, 'figcaption')])
            proof = next(n.text() for n in nodes(source, 'q') if '1.50' in n.text())
            self.assertIn(normal(proof), text_of(self.home))
            self.assertIn('Max results on selected clips', text_of(source))

    def test_prices_dates_and_negative_controls(self):
        rival_figures(self.best)
        for before, after in (('$235 list', '$236 list'), ('read 11 Nov 2026', 'read 12 Nov 2026'),
                              ('$1,495 at', '$1,496 at'), ('offer, read 19 October 2026', 'offer, no read date')):
            planted = self.best.replace(before, after, 1)
            self.assertNotEqual(planted, self.best)
            with self.assertRaises(AssertionError):
                rival_figures(planted)
        ownership = ('Adobe completed its purchase of Topaz Labs on 23 September 2026 '
                     '(Adobe, read 20 Nov 2026); Topaz Video is still sold on its own.')
        self.assertIn(ownership, text_of(self.best))

    def test_metadata_faq_css_and_reading_length(self):
        css = read('style.css')
        for source in (self.family, self.best):
            titles = [n.text() for n in nodes(source, 'title')]
            titles += [n.attrs['content'] for n in nodes(source, 'meta')
                       if n.attrs.get('name', n.attrs.get('property')) in ('og:title', 'twitter:title')]
            self.assertEqual(len(titles), 3)
            self.assertTrue(all(len(t) <= 60 for t in titles))
            self.assertEqual(len(set(titles)), 1)
            self.assertEqual(titles[0], nodes(source, 'h1')[0].text())
            canonical = next(n.attrs['href'] for n in nodes(source, 'link') if n.attrs.get('rel') == 'canonical')
            schema = json_nodes(source)
            page = next(n for n in schema if n.get('@type') == 'Article')
            crumb = next(n for n in schema if n.get('@type') == 'BreadcrumbList')
            self.assertEqual(page['mainEntityOfPage'], canonical)
            self.assertEqual(crumb['itemListElement'][-1]['item'], canonical)
            parent = '/best/' if source == self.best else '/for/'
            self.assertEqual(crumb['itemListElement'][-2]['item'], 'https://crispvideo.app' + parent)
            desc = next(n.attrs['content'] for n in nodes(source, 'meta') if n.attrs.get('name') == 'description')
            self.assertLessEqual(len(desc), 165)
            self.assertTrue(faq_jsonld.visible_faq(source))
            self.assertEqual(faq_jsonld.rebuild(source)[0], source)
            self.assertTrue(any(n.get('@type') == 'FAQPage' for n in json_nodes(source)))
            self.assertEqual(len([n for n in nodes(source, 'aside') if n.attrs.get('data-pbox')]), 2)
            # Inspect the actual article, rather than class-like strings in the sale banner's JS.
            for node in article(source).walk():
                for cls in (node.attrs.get('class') or '').split():
                    self.assertRegex(css, r'\.' + re.escape(cls) + r'(?![\w-])', cls)
            self.assertNotRegex(article(source).text(), '[\u2013\u2014]')
        self.assertLess(len(normal(article(self.family).text()).split()), 1200,
                        'family article should take under six minutes at 200 words a minute')

    def test_links_llms_and_sitemap(self):
        for rel in ('index.html', 'best/index.html', 'vs/index.html'):
            targets = links(read(rel))
            self.assertTrue({URL, 'https://crispvideo.app' + URL} & targets, rel)
        compare = self.home[self.home.index('<section id="compare">'):]
        self.assertIn(URL, links(compare.split('</section>', 1)[0]))
        self.assertEqual(llms_txt.BEST.count(URL), 1)
        desc = next(n.attrs['content'] for n in nodes(self.best, 'meta') if n.attrs.get('name') == 'description')
        self.assertEqual(llms_txt.link(URL).split('): ', 1)[1], desc)
        sitemap = ET.fromstring(read('sitemap.xml'))
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locs = [n.text for n in sitemap.findall('s:url/s:loc', ns)]
        for path in (URL, '/for/family-archivists/'):
            self.assertEqual(locs.count('https://crispvideo.app' + path), 1)
        for rel in ('best/index.html', 'vs/index.html'):
            collection = next(n for n in json_nodes(read(rel)) if n.get('@type') == 'CollectionPage')
            items = collection['mainEntity']['itemListElement']
            self.assertEqual(collection['mainEntity']['numberOfItems'], len(items))
            self.assertIn('https://crispvideo.app' + URL, {n['url'] for n in items})


if __name__ == '__main__':
    unittest.main(verbosity=2)
