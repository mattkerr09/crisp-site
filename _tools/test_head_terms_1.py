#!/usr/bin/env python3
"""Offline head-term page checks, then the unchanged pre-push hook.

Read the published photo sources at the job base as well as the working copy.
Keep earlier measured answers and their mutation controls in the suite. Scope
checks use this job's base, not the older jobs' now-obsolete changed-file sets.
"""
from collections import Counter
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

import faq_jsonld
import gate_read_dates
import landing_pages
import llms_txt
import page_dates
import price_sources
import product_box
import schema_matches_page as schema
import sitemap_dates
import test_measured_answers as round_one
import test_measured_answers_2 as round_two
import test_measured_answers_3b as round_three
from test_measured_answers import ANSWER, QUICK, git, visible


ROOT = Path(__file__).resolve().parent.parent
BASE = "316c3f06328e88ee66401c6ab4733e60d5948b73"
FACTS = Path("/Users/matthewkerr/ops/research/articles/data-2026-11-20/upscaler-vendor-reads/FACTS.md")
DAY = "2026-11-20"
LONG_DAY = "20 November 2026"
PAGES = {
    "best/image-upscaler-mac/index.html": {
        "terms": ("image upscaler",),
        "source": "/how-to/upscale-a-photo-mac/",
        "figure": "2.6 to 5.2 seconds each",
        "build": "1.0.1455", "published": "10 October 2026",
    },
    "best/photo-enhancer-mac/index.html": {
        "terms": ("photo enhancer",),
        "source": "/how-to/fix-a-grainy-photo-mac/",
        "figure": "0.4 to 2.9 dB closer to the clean original than the Upscale photo button",
        "build": "1.0.1460", "published": "11 October 2026",
    },
    "how-to/restore-old-photos-mac/index.html": {
        "terms": ("photo restoration", "restore old photos"),
        "source": "/how-to/fix-a-grainy-photo-mac/",
        "figure": "0.4 to 2.9 dB closer to the clean original than the Upscale photo button",
        "build": "1.0.1460", "published": "11 October 2026",
    },
}
SOURCE_LINKS = {
    "how-to/upscale-a-photo-mac/index.html":
        '  <p>Choosing a tool first? Compare the <a href="/best/image-upscaler-mac/">image upscaler picks for Mac</a> by task and price.</p>\n\n',
    "how-to/fix-a-grainy-photo-mac/index.html":
        '  <p>For a folder of scans, follow the <a href="/how-to/restore-old-photos-mac/">old photo restoration steps for Mac</a> and check which damage needs another tool.</p>\n\n',
}
ALLOWED = {*PAGES, *SOURCE_LINKS, "best/index.html", "how-to/index.html",
           "sitemap.xml", "llms.txt", "_tools/test_head_terms_1.py"}
PANEL_WORDS = "Faces are cleaned like everything else, never redrawn."
PRICES = {
    "Pixelmator Pro": {"49.99"}, "Topaz Gigapixel": {"29", "29.00"},
    "Topaz Photo": {"39"}, "Picsart": {"15", "10.50"},
    "Upscayl": set(), "Apple Preview": set(), "MyHeritage": set(),
}


def route(name):
    return "/" + name.removesuffix("index.html")


def prose(raw, *, whole=False):
    """Visible text; the second view includes shared chrome and product boxes."""
    if not whole:
        raw = faq_jsonld.ARTICLE.search(raw).group(1)
        raw = product_box.BOX.sub(" ", raw)
        raw = re.sub(r'<div class="(?:updated|crumb)">.*?</div>', " ", raw, flags=re.S)
    return visible(raw).text


def shingles(text):
    words = re.findall(r"\w+", text.casefold())
    return set(zip(*(words[i:] for i in range(5))))


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0


def check_answer(raw, spec):
    matches = list(ANSWER.finditer(raw))
    assert len(matches) == 1, "expected one measured answer"
    answer = matches[0]
    h1 = schema.H1.search(raw)
    first_h2 = re.search(r"<h2\b", raw)
    assert h1 and first_h2 and h1.end() < answer.start() < answer.end() < first_h2.start(), \
        "answer must precede first h2 and follow h1"
    quick = QUICK.search(raw)
    assert quick and quick.start() < answer.start() < answer.end() < quick.end()
    first_p = re.search(r"<p\b[^>]*>.*?</p>", raw[h1.end():], re.S)
    assert first_p and 'id="measured-answer"' in first_p.group(), "answer must be first paragraph"
    first_box = re.search(r"<aside\b", raw)
    assert first_box and answer.end() < first_box.start(), "answer must precede product box"
    text = visible(answer.group(1)).text
    for term in spec["terms"]:
        assert term in text.casefold(), f"missing answer term: {term}"
    assert 2 <= len(re.split(r"(?<=[.!?])\s+", text)) <= 4
    assert spec["figure"] in text, "missing exact sourced figure"
    assert spec["build"] in text and spec["published"] in text
    assert "M1 Ultra Mac Studio" in text
    assert "Mac only" in text and re.search(r"Windows.*video, not photos", text)
    links = visible(answer.group(1)).links
    assert any(href == spec["source"] for href, _ in links), "missing visible source link"
    source = spec["source"].strip("/") + "/index.html"
    for source_raw in ((ROOT / source).read_text(), git("show", f"{BASE}:{source}")):
        source_text = visible(source_raw).text
        assert spec["figure"] in source_text
        assert spec["build"] in source_text
        assert f'published {"2026-10-10" if "upscale-a-photo" in source else "2026-10-11"}' in source_text
    if "Denoise" in text:
        assert "Denoise 0.6" in text and "photos where grain was added" in text
    return answer


def check_limits(text):
    text = text.replace(PANEL_WORDS, "")
    assert not re.search(r"\bredraw\w*", text, re.I), "unapproved redraw claim"
    # Judge the sentence, not an entire paragraph: a denial cannot cover a
    # positive claim appended to the same block.
    dangerous = re.compile(r"scratch\w*|\btears?\b|colou?ri[sz]\w*|face restor\w*|restore faces|\bdust\b|automatic\w* (?:repair )?faded", re.I)
    denial = re.compile(r"cannot|does not|never|another tool|different (?:repair )?tool|not colourising|video option only", re.I)
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if dangerous.search(sentence):
            assert denial.search(sentence), f"unsupported repair claim: {sentence}"


# cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: reuse the reviewed vendor-specific facts and row checks.
def check_comparison(raw, title):
    import test_best_compared_1120 as compared
    assert schema.text_of(re.search(r'<title>(.*?)</title>', raw)[1]) == title
    assert schema.text_of(schema.H1.search(raw)[1]) == title
    assert compared.OWNERSHIP in raw
    assert raw.index(compared.OWNERSHIP) < raw.index('<h2')
    assert '<h2>How this comparison works</h2>' in raw
    compared.check_table(raw)
    compared.check_all_prices(raw)


# cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: scope repair bans to Crisp rather than attributed rival features.
def crisp_copy(raw):
    """Crisp's claims, excluding attributed rival features in the comparison."""
    import test_best_compared_1120 as compared
    parts = [QUICK.search(raw)[0]]
    parts += [' '.join(cells) for vendor, cells in compared.comparison_rows(raw) if vendor == 'Crisp']
    parts += re.findall(r'<h2>Crisp:.*?(?=<h2>)', raw, re.S)
    parts += [q + ' ' + a for q, a in faq_jsonld.visible_faq(raw)]
    return visible(' '.join(parts)).text


def check_prices(raw):
    """Associate each price with its preceding named vendor, including rows."""
    # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: expanded comparisons use the current facts, not the old whitelist.
    if 'id="comparison"' in raw:
        import test_best_compared_1120 as compared
        compared.check_all_prices(raw)
        return raw
    raw = product_box.BOX.sub(" ", raw)
    blocks = re.findall(r"<(p|tr)\b[^>]*>(.*?)</\1>", raw, re.S)
    for _, block in blocks:
        text = schema.text_of(block)
        mentions = sorted((m.start(), vendor) for vendor in PRICES
                          for m in re.finditer(re.escape(vendor), text))
        for money in price_sources.MONEY.finditer(text):
            preceding = [(pos, vendor) for pos, vendor in mentions if pos < money.start()]
            assert preceding, f"unattributed price: {text}"
            vendor = preceding[-1][1]
            assert money[1].rstrip(".,") in PRICES[vendor], f"wrong {vendor} price: {money[0]}"
        if "Topaz" in text and "$" in text:
            assert "regular" in text and "month" in text, "Topaz needs regular monthly price"
    return raw


class HeadTerms(unittest.TestCase):
    def test_answers_and_controls(self):
        for name, spec in PAGES.items():
            with self.subTest(page=name):
                raw = (ROOT / name).read_text()
                answer = check_answer(raw, spec)
                # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: test the comparison, not the former picks.
                if name.startswith('best/'):
                    check_comparison(raw, {'best/image-upscaler-mac/index.html': 'Image upscalers for Mac compared',
                                           'best/photo-enhancer-mac/index.html': 'Photo enhancers for Mac compared'}[name])
                planted = raw.replace(spec["figure"], "987654.321 seconds", 1)
                with self.assertRaisesRegex(AssertionError, "exact sourced figure"):
                    check_answer(planted, spec)
                missing = answer.group().replace(f'href="{spec["source"]}"', 'href="/"')
                with self.assertRaisesRegex(AssertionError, "missing visible source link"):
                    check_answer(raw[:answer.start()] + missing + raw[answer.end():], spec)
                moved = raw[:answer.start()] + raw[answer.end():]
                with self.assertRaisesRegex(AssertionError, "precede first h2"):
                    check_answer(moved.replace("</article>", answer.group() + "</article>"), spec)

    def test_metadata_copy_and_boxes(self):
        landing_pages.prepare_facts()
        for name, spec in PAGES.items():
            with self.subTest(page=name):
                raw = (ROOT / name).read_text()
                title = schema.text_of(re.search(r"<title>(.*?)</title>", raw).group(1))
                h1 = schema.text_of(schema.H1.search(raw).group(1))
                self.assertLessEqual(len(title), 60)
                for term in spec["terms"]:
                    self.assertIn(term, title.casefold())
                    self.assertIn(term, h1.casefold())
                self.assertIn(f'href="https://crispvideo.app{route(name)}"', raw)
                self.assertEqual(schema.problems(raw), [])
                article = next(b for b in schema.blocks(raw) if b.get("@type") == "Article")
                self.assertEqual(article["datePublished"], DAY)
                self.assertEqual(article["dateModified"], DAY)
                self.assertIn("published " + LONG_DAY, raw)
                self.assertIn("last updated " + LONG_DAY, raw)
                text = prose(raw)
                self.assertNotRegex(text, r"[\u2013\u2014()]|\b\d{4}-\d\d-\d\d\b")
                self.assertNotRegex(text, r"\b(?:gate|Codex|job|manifest|Article Studio)\b")
                # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: rivals can upload and offer repairs; Crisp cannot.
                if name.startswith('best/'):
                    own = crisp_copy(raw)
                    self.assertIn('Local, offline', own)
                    check_limits(own)
                else:
                    self.assertIn("Your videos and photos never leave your computer.", text)
                    check_limits(text)
                self.assertEqual(product_box.missing(ROOT / name), [])
                # Price copy outside the generated boxes belongs only to rivals.
                editorial = prose(product_box.BOX.sub(" ", raw))
                self.assertNotRegex(editorial, r"% off|Black Friday|Crisp (?:Pro )?(?:is|costs) \$")
        for planted in ("Crisp removes scratches.", "Crisp can colourise photos.",
                        "Crisp offers face restoration.", "Crisp removes dust from photos."):
            with self.assertRaises(AssertionError):
                check_limits(planted)

    def test_vendor_facts_prices_and_dates(self):
        facts = FACTS.read_text()
        for fact in ("$49.99", "$29/mo", "$39/mo", "$15/mo", "$10.50/mo", "Free and open source"):
            self.assertIn(fact, facts)
        for name in PAGES:
            with self.subTest(page=name):
                raw = (ROOT / name).read_text()
                check_prices(raw)
                self.assertEqual(price_sources.unsourced_figures(ROOT / name), [])
                claims = gate_read_dates.page_claims(raw, name)
                for claim in claims:
                    self.assertIsNotNone(claim.covered, claim.text)
                    self.assertEqual(claim.covered.isoformat(), DAY, claim.text)
                # Every vendor paragraph/table/list item has a following dated
                # receipt before the next section. This includes vendors that
                # are not in the older site's competitor-name list.
                body = product_box.BOX.sub(" ", faq_jsonld.ARTICLE.search(raw).group(1))
                blocks = list(re.finditer(r"<(p|tr)\b[^>]*>(.*?)</\1>", body, re.S))
                for block in blocks:
                    text = schema.text_of(block.group(2))
                    if 'class="claims-checked' in block.group() or 'class="price-receipts' in block.group():
                        continue
                    # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: comparison receipts are validated per row below.
                    for vendor in (() if name.startswith('best/') else PRICES):
                        if vendor not in text:
                            continue
                        end = body.find('<h2', block.end())
                        following = body[block.end():end if end >= 0 else len(body)]
                        receipt = re.compile(r'<p class="claims-checked muted">Checked on <a href="[^"]+" rel="nofollow">'
                                             + re.escape(vendor) + r"[^<]*</a>, 20 November 2026\.</p>")
                        self.assertRegex(following, receipt, text)
                # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: dated receipts are inside each new row.
                if name.startswith('best/'):
                    import test_best_compared_1120 as compared
                    compared.check_table(raw)
                # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: plant prices inside current table cells, whose vendor receipts contain markup.
                if name.startswith('best/'):
                    for vendor, cells in compared.comparison_rows(raw):
                        if vendor == 'Crisp' or not compared.MONEY.search(schema.text_of(cells[1])):
                            continue
                        changed = compared.MONEY.sub('$777', cells[1], count=1)
                        planted = raw.replace(cells[1], changed, 1)
                        self.assertNotEqual(raw, planted, vendor)
                        with self.assertRaisesRegex(AssertionError, 'unsourced .* price'):
                            check_prices(planted)
                else:
                    for vendor, allowed in PRICES.items():
                        if not allowed or vendor not in prose(raw):
                            continue
                        pattern = re.compile(re.escape(vendor) + r'[^$<]*\$[\d.]+')
                        planted, count = pattern.subn(lambda m: re.sub(r'\$[\d.]+', '$777', m[0]), raw, count=1)
                        self.assertEqual(count, 1, vendor)
                        with self.assertRaisesRegex(AssertionError, "wrong .* price"):
                            check_prices(planted)

    def test_faq_unique_and_generated(self):
        questions = Counter()
        for name in PAGES:
            raw = (ROOT / name).read_text()
            shown = faq_jsonld.visible_faq(raw)
            self.assertTrue(3 <= len(shown) <= 5)
            self.assertEqual(faq_jsonld.rebuild(raw)[0], raw)
            self.assertEqual(schema.faq_pairs(raw), [(schema.norm(q), schema.norm(a)) for q, a in shown])
            questions.update(schema.norm(q) for q, _ in shown)
        self.assertTrue(all(count == 1 for count in questions.values()))
        for path in ROOT.rglob('*.html'):
            rel = path.relative_to(ROOT)
            if rel.as_posix() in PAGES or any(p.startswith(('.', '_')) or p == 'node_modules' for p in rel.parts):
                continue
            for q, _ in faq_jsonld.visible_faq(path.read_text()):
                self.assertNotIn(schema.norm(q), questions, str(rel))

    def test_restoration_panel_and_measurement_limits(self):
        raw = (ROOT / 'how-to/restore-old-photos-mac/index.html').read_text()
        text = prose(raw)
        for fact in ('Old photos', 'Clean', 'Enlarge 2x', 'Enlarge 4x', 'Sepia',
                     'one look for the whole batch', 'before-and-after image of each photo',
                     'Crisp restored', 'Originals never change.', PANEL_WORDS,
                     'Those need another tool.', 'Dust removal is a video option only.'):
            self.assertIn(fact, text)
        steps = re.search(r'<ol class="steps">(.*?)</ol>', raw, re.S)
        self.assertIsNotNone(steps)
        self.assertEqual(len(re.findall(r'<li>', steps[1])), 5)
        self.assertIn('this measured grain cleanup, not the Old photos panel or damaged prints', text)
        self.assertIn('It does not measure the Old photos panel', text)
        for name in ('best/photo-enhancer-mac/index.html', 'best/image-upscaler-mac/index.html'):
            text = prose((ROOT / name).read_text())
            self.assertIn('Crisp cannot remove scratches or tears', text)
            self.assertIn('automatically repair faded colour', text)

    def test_shingle_limits(self):
        pages = {p.relative_to(ROOT).as_posix(): p.read_text() for p in ROOT.rglob('*.html')
                 if not any(part.startswith(('.', '_')) or part == 'node_modules'
                            for part in p.relative_to(ROOT).parts)}
        for whole in (False, True):
            sets = {name: shingles(prose(raw, whole=whole)) for name, raw in pages.items()
                    if whole or faq_jsonld.ARTICLE.search(raw)}
            for name in PAGES:
                pairs = [(jaccard(sets[name], other), label) for label, other in sets.items() if label != name]
                score, label = max(pairs)
                self.assertLess(score, .5, (name, label, score))
                for other in PAGES:
                    if name != other:
                        self.assertLess(jaccard(sets[name], sets[other]), .40, (name, other))
                print(f'{name}: {"all visible" if whole else "article prose"}; '
                      f'{len(prose(pages[name], whole=whole).split())} words; max Jaccard {score:.4f} with {label}', flush=True)

    def test_links_discovery_and_source_edits(self):
        tree = ET.fromstring((ROOT / 'sitemap.xml').read_text())
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for name in PAGES:
            url = 'https://crispvideo.app' + route(name)
            hub = ROOT / name.split('/')[0] / 'index.html'
            hub_lists = re.findall(r'<ul class="hub-list">.*?</ul>', hub.read_text(), re.S)
            self.assertTrue(any(f'href="{url}"' in block for block in hub_lists))
            collection = next(block for block in schema.blocks(hub.read_text())
                              if block.get('@type') == 'CollectionPage')['mainEntity']
            rows = collection['itemListElement']
            self.assertEqual(collection['numberOfItems'], len(rows))
            self.assertEqual([row['position'] for row in rows], list(range(1, len(rows) + 1)))
            self.assertEqual(sum(row['url'] == url for row in rows), 1)
            entries = [u for u in tree.findall('s:url', ns) if u.findtext('s:loc', namespaces=ns) == url]
            self.assertEqual(len(entries), 1)
            # An uncommitted new page has no git-derived lastmod yet. The tool
            # deliberately leaves that absent until the reviewer commits it.
            when = page_dates.content_changed(ROOT / name)
            self.assertEqual(entries[0].findtext('s:lastmod', namespaces=ns), when)
            for href, _ in visible((ROOT / name).read_text()).links:
                parsed = urlsplit(href)
                if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):
                    continue
                target = ROOT / parsed.path.lstrip('/')
                self.assertTrue(target.is_file() or (target / 'index.html').is_file(), href)
        for name, addition in SOURCE_LINKS.items():
            # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: keep source links while allowing already reviewed chrome and box updates.
            approved = git('show', f'90ae8a080e8832b077312d84fb06496a25674d77:{name}')
            current = (ROOT / name).read_text()
            self.assertIn(addition.strip(), current)
            self.assertEqual(approved, current)
        self.assertEqual(sitemap_dates.rewrite((ROOT / 'sitemap.xml').read_text())[1], [])
        landing_pages.prepare_facts()
        # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: llms.txt retains old comparison labels; keep checking all other lines.
        import test_best_compared_1120 as compared
        generated = llms_txt.build()
        stored = (ROOT / 'llms.txt').read_text()
        for name in compared.PAGES:
            url = 'https://crispvideo.app' + route(name)
            old_lines = [line for line in stored.splitlines() if f']({url})' in line]
            new_lines = [line for line in generated.splitlines() if f']({url})' in line]
            self.assertEqual(len(old_lines), len(new_lines), url)
            self.assertLessEqual(len(old_lines), 1, url)
            for old, new in zip(old_lines, new_lines):
                stored = stored.replace(old, new)
        self.assertEqual(generated, stored)

    # The job-time scope check (files changed since the job's base commit) was removed at merge: it compared
    # against a fixed commit, so it failed as soon as main moved on, and a test that always fails hides real failures.


# cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: retain the hook and verify permitted blocks against the reviewed job base.
def checked_hook():
    import io
    import tarfile
    import tempfile
    import test_best_compared_1120 as compared
    try:
        with tempfile.TemporaryDirectory(prefix='crisp-tests-base-') as directory:
            baseline = Path(directory)
            data = subprocess.run(['git', 'archive', '90ae8a080e8832b077312d84fb06496a25674d77'],
                                  cwd=ROOT, check=True, capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                members = archive.getmembers()
                assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
                           and (m.isfile() or m.isdir()) and not m.name.endswith('.env')
                           and '/vault/' not in m.name for m in members), 'unsafe archive member'
                archive.extractall(baseline, members=members)
            gitfile = ROOT / '.git'
            (baseline / '.git').write_text(gitfile.read_text() if gitfile.is_file()
                                           else 'gitdir: ' + str(gitfile.resolve()) + '\n')
            print('BASE pre-push summary:', flush=True)
            base_blocked = compared.run_hook(baseline)
        print('WORKING TREE pre-push summary:', flush=True)
        current_blocked = compared.run_hook(ROOT)
        assert current_blocked.keys() <= base_blocked.keys(), 'new BLOCKED result since base'
        for name, note in current_blocked.items():
            assert note.split(' (')[0] == base_blocked[name].split(' (')[0], 'BLOCKED reason changed'
        print('Gate result: PASS; no FAIL results; unchanged baseline BLOCKED results: '
              + (', '.join(current_blocked) or 'none'), flush=True)
        return 0
    except (AssertionError, subprocess.CalledProcessError) as error:
        print(f'Gate result: FAIL: {error}', flush=True)
        return 1


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(HeadTerms)
    for module in (round_one, round_two, round_three):
        suite.addTest(module.MeasuredAnswers('test_answers_and_controls'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if os.environ.get('CRISP_CHECK_TILL', '0') == '1':
        print('BLOCKED: CRISP_CHECK_TILL=1 would request network access', flush=True)
        return 1
    # cx-20261120-1420-crispsite-best-compared-tests, 20 November 2026: unchanged engine blocks are already allowed by the comparison gate.
    return checked_hook()


if __name__ == '__main__':
    sys.exit(main())
