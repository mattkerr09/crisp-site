#!/usr/bin/env python3
"""Offline checks for the translated guide batch, driven by its manifest.

Run with plain python3. Shared chrome and generated product boxes are excluded
from prose comparisons; all visible body text is checked for new numbers.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from html import unescape
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET

from gate_lang import Document, normal
from lang_pages import LanguagePages, alternate_routes

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://crispvideo.app"
MANIFEST = ROOT / "_tools/guides_lang_manifest.json"
BLOCKS = {"p", "li", "th", "td", "h1", "h2", "h3", "figcaption"}
NUMBER = re.compile(r"(?<!\d)(?:−|(?<!\w)-)?(?:\d{1,3}(?:[\u00a0\u202f ]\d{3}(?!\d))+(?:[.,]\d+)?|\d+(?:[.,]\d+)*)")
UNITS = r"(?:MB|GB|KB|Mbps|dB|s|sec(?:ond)?s?|min(?:ute)?s?|fps|p|x|×|%|pixels?|megapixels?|frames?)"
MEASUREMENT = re.compile(r"(?<![\dA-Za-z])(?P<number>[−-]?\d+(?:[.,]\d+)*)(?:[ -]*\d+)?[\s\u00a0-]*(?:" + UNITS + r")(?![A-Za-z])", re.I)
EN_NUMBER_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10", "twenty": "20", "thirty": "30"}
LOCAL_NUMBER_WORDS = {
    'pt-br': {'um': '1', 'uma': '1', 'dois': '2', 'duas': '2', 'três': '3', 'quatro': '4', 'cinco': '5', 'seis': '6', 'sete': '7', 'oito': '8', 'nove': '9', 'dez': '10', 'vinte': '20', 'trinta': '30'},
    'es': {'un': '1', 'uno': '1', 'una': '1', 'dos': '2', 'tres': '3', 'cuatro': '4', 'cinco': '5', 'seis': '6', 'siete': '7', 'ocho': '8', 'nueve': '9', 'diez': '10', 'veinte': '20', 'treinta': '30'},
}
SPELLED_MEASUREMENT = re.compile(r"\b(" + "|".join(EN_NUMBER_WORDS) + r")[ -]+" + UNITS + r"\b", re.I)
BANNED = re.compile(r"Black Friday|%\s*off\b|desconto de\s*50\s*%|descuento de\s*50\s*%|metade do preço|mitad de precio|nada é enviado|no se sube nada|\b(?:gate|generator|gerador|generador|manifest|manifesto|manifiesto|job|Codex|Article Studio)\b", re.I)


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", unescape(text).lower()) if not unicodedata.combining(c))


def words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", fold(text))


def query_count(query: str, text: str) -> int:
    # Search queries omit articles that natural Portuguese and Spanish need.
    joiner = r'(?: (?:a|o|as|os|um|uma|la|el|las|los|un|una)){0,2} '
    pattern = r'\b' + joiner.join(re.escape(token) for token in words(query)) + r'\b'
    return len(re.findall(pattern, ' '.join(words(text))))


def spelling_errors(source: str, lang: str, query: str) -> list[str]:
    errors = []
    if 'Handbrake' in source:
        errors.append('product spelling must be HandBrake')
    if lang == 'es':
        doc = Document(source)

        def visible(node):
            # English app labels are quoted literally in code elements.
            if node.tag in {'script', 'style', 'template', 'code'}:
                return ''
            if node.tag == '#text':
                return unescape(node.raw)
            return ' '.join(visible(child) for child in node.children)

        text = normal(visible(doc.root))
        text = re.sub(r'\b(?:Crisp Video|Topaz Video AI)\b', '', text)
        # Permit the registered query, including natural articles and accents.
        accents = dict(zip('aeioun', ('[aá]', '[eé]', '[ií]', '[oó]', '[uúü]', '[nñ]')))
        tokens = [''.join(accents.get(c, re.escape(c)) for c in token) for token in words(query)]
        joiner = r'(?: (?:la|el|las|los|un|una)){0,2} '
        text = re.sub(r'\b' + joiner.join(tokens) + r'\b', '', text, flags=re.I)
        if re.search(r'\bvideos?\b', text, re.I):
            errors.append('Spanish prose must use vídeo/vídeos outside the query')
    return errors


def value(raw: str, locale: str) -> str:
    raw = re.sub(r"\s", "", raw).replace("−", "-")
    # Versions and dotted codec names are preserved, not treated as decimals.
    if raw.count(".") > 1 and not re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+", raw):
        return raw
    if locale == "en":
        raw = raw.replace(",", "")
    else:
        if re.fullmatch(r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?", raw):
            raw = raw.replace(".", "")
        raw = raw.replace(",", ".")
    return format(Decimal(raw).normalize(), "f")


def numbers(text: str, locale: str) -> set[str]:
    found = {value(match.group(), locale) for match in NUMBER.finditer(text)}
    vocabulary = EN_NUMBER_WORDS if locale == 'en' else LOCAL_NUMBER_WORDS[locale]
    units = UNITS if locale == 'en' else r'(?:segundos?|minutos?|horas?|pixels?|píxeles|megapixels?|megapíxeles|quadros?|fotogramas?)'
    pattern = r'\b(' + '|'.join(vocabulary) + r')[ -]+' + units + r'\b'
    found.update(vocabulary[match[1].lower()] for match in re.finditer(pattern, text, re.I))
    if locale == 'en':
        # Also covers an implied unit, such as "a second or two away".
        found.update(vocabulary[token] for token in words(text) if token in vocabulary)
    return found


def measurements(text: str) -> set[str]:
    found = {value(match['number'], 'en') for match in MEASUREMENT.finditer(text)}
    found.update(EN_NUMBER_WORDS[match[1].lower()] for match in SPELLED_MEASUREMENT.finditer(text))
    return found


def prose(node) -> str:
    """Article prose without repeated offer boxes, breadcrumbs or bylines."""
    if node.tag in {"script", "style", "template", "aside"} or node.attrs.get("class") in {"crumb", "updated"}:
        return ""
    if node.tag == "#text":
        return unescape(node.raw)
    return " ".join(prose(child) for child in node.children)


def shingles(text: str) -> set[tuple[str, ...]]:
    tokens = words(text)
    return set(zip(*(tokens[i:] for i in range(5))))


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a or b else 0.0


def sentences(node):
    if node.tag in {"script", "style", "template", "aside"}:
        return
    if node.tag in BLOCKS:
        # Parent list items can hold several paragraphs. Sets remove duplicates.
        text = normal(node.text())
        yield from re.split(r'(?<=[.!?])\s+', text)
        # Quoted app errors are prose too. Keep only menu/button labels in English.
        for quoted in re.findall(r'["“]([^"”]+)["”]', text):
            yield from re.split(r'(?<=[.!?])\s+', quoted)
    for child in node.children:
        yield from sentences(child)


def english_left(source, translated) -> set[str]:
    target = normal(translated.text())
    return {sentence for sentence in sentences(source)
            if len(words(sentence)) >= 6 and re.search(r'[.!?]["\u2019\u201d]*$', sentence)
            and sentence in target}


def alternates(doc) -> Counter:
    return Counter((n.attrs.get("hreflang"), n.attrs.get("href")) for n in doc.elements('link')
                   if n.attrs.get('rel') == 'alternate' and 'hreflang' in n.attrs)


def selftest():
    assert numbers('1.800 1,52 17,9 1.0.1458 −21,1 4,0', 'pt-br') == {'1800', '1.52', '17.9', '1.0.1458', '-21.1', '4'}
    assert numbers('1,800 1.52 17.9 1.0.1458 −21.1 4.0', 'en') == {'1800', '1.52', '17.9', '1.0.1458', '-21.1', '4'}
    assert measurements('48 GB, 29.97 fps, 5-to-10-second range, ten seconds, 30%') >= {'48', '29.97', '10', '30'}
    assert not BANNED.search('100% offline')
    assert BANNED.search('50% off')
    assert jaccard(shingles('a b c d e f'), shingles('a b c d e f')) == 1
    assert english_left(Document('<p>This is an English sentence with seven words.</p>').root,
                        Document('<p>This is an <strong>English sentence</strong> with seven words.</p>').root)
    assert not english_left(Document('<p>Press Do it.</p>').root, Document('<p>Press Do it.</p>').root)
    assert english_left(Document('<p>It says "this clip has no audio track. Nothing to extract".</p>').root,
                        Document('<p>Aviso: this clip has no audio track.</p>').root)
    assert words('áudio VÍDEO grátis') == words('audio video gratis')
    assert query_count('melhorar qualidade da foto', 'Melhorar a qualidade da foto') == 1
    assert query_count('reducir tamaño de video', 'Reducir el tamaño de video') == 1
    assert query_count('cortar video', 'Video para cortar') == 0
    assert query_count('cortar video', 'Cortar video y cortar video') == 2
    assert spelling_errors('<p>Handbrake</p>', 'pt-br', 'converter video')
    assert spelling_errors('<script>"Handbrake"</script>', 'es', 'cortar video')
    assert not spelling_errors('<p>HandBrake</p>', 'pt-br', 'converter video')
    assert not spelling_errors('<p>Reducir el tamaño de un video. Vídeos en Crisp Video y Topaz Video AI.</p><code>Export video</code>', 'es', 'reducir tamaño de video')
    assert not spelling_errors('<p>Cortar vídeo.</p>', 'es', 'cortar video')
    assert spelling_errors('<p>Cortar video. Otro video.</p>', 'es', 'cortar video')
    assert spelling_errors('<table><tr><td>Videos</td></tr></table>', 'es', 'cortar video')
    assert spelling_errors('<h3>¿Un <strong>video</strong>?</h3>', 'es', 'cortar video')
    assert not spelling_errors('<a href="/video/">Vídeo</a><script>const video = 1;</script>', 'es', 'cortar video')


def check() -> int:
    selftest()
    entries = json.loads(MANIFEST.read_text())
    failures = []
    documents = {}
    texts = {}
    signatures = {}
    questions = {}
    maxima = {}

    def fail(path, message):
        failures.append(f'{path}: {message}')

    assert len(entries) == 22 and Counter(entry['lang'] for entry in entries) == {'pt-br': 12, 'es': 10}
    assert len({entry['path'] for entry in entries}) == 22
    required = {'english', 'lang', 'path', 'query', 'demand', 'demand_market', 'demand_read', 'published'}
    for entry in entries:
        path, lang = entry['path'], entry['lang']
        if set(entry) != required or entry['demand_read'] != '2026-11-11' or entry['published'] != '2026-11-11':
            fail(path, 'manifest fields or dates differ from the batch contract')
        if not isinstance(entry['demand'], int) or entry['demand'] <= 0:
            fail(path, 'demand must be a positive measured integer')
        if not re.fullmatch('/' + lang + r'/guia/[a-z0-9-]+/', path):
            fail(path, 'invalid guide path')
        file = ROOT / path.lstrip('/') / 'index.html'
        if not file.is_file():
            fail(path, 'page is missing')
            continue
        source = file.read_text()
        for error in spelling_errors(source, lang, entry['query']):
            fail(path, error)
        doc = documents[path] = Document(source)
        generator = LanguagePages(lang)
        if dict(generator.words.ROUTES).get(entry['english']) != path:
            fail(path, 'ROUTES does not register the English/local pair')
        html_nodes, articles = doc.elements('html'), doc.elements('article')
        if len(html_nodes) != 1 or html_nodes[0].attrs.get('lang') != generator.words.HTML_LANG or len(articles) != 1:
            fail(path, 'wrong HTML language or missing article')
            continue
        article = articles[0]
        texts[path] = prose(article)
        signatures[path] = shingles(texts[path])
        h1s, titles = doc.elements('h1'), doc.elements('title')
        ps = [n for n in article.walk() if n.tag == 'p' and n.attrs.get('class') != 'crumb']
        if len(h1s) != 1 or len(titles) != 1 or not ps:
            fail(path, 'expected one title, H1 and lead paragraph')
            continue
        for label, text in [('title', titles[0].text()), ('H1', h1s[0].text()), ('first paragraph', ps[0].text())]:
            if query_count(entry['query'], text) != 1:
                fail(path, f'{label} must contain the query once: {entry["query"]}')
        title = normal(titles[0].text())
        if len(title.removesuffix(' | Crisp')) > 60 or len(title) > 68:
            fail(path, f'title too long: {len(title)} characters')
        descriptions = [n.attrs.get('content', '') for n in doc.elements('meta') if n.attrs.get('name') == 'description']
        if len(descriptions) != 1 or not 120 <= len(unescape(descriptions[0])) <= 160:
            fail(path, f'meta description must have 120 to 160 characters: {[len(d) for d in descriptions]}')
        english = Document((ROOT / entry['english'].lstrip('/') / 'index.html').read_text())
        en_article = english.elements('article')[0]
        body = doc.elements('body')[0]
        visible = normal(body.text())
        allowed = numbers(normal(english.elements('body')[0].text()), 'en')
        allowed |= numbers(normal(Document(generator.box('test')).root.text()), lang)
        added = numbers(visible, lang) - allowed
        if added:
            fail(path, 'NUMBER PARITY: new visible numbers ' + ', '.join(sorted(added)))
        dropped = measurements(prose(en_article)) - numbers(texts[path], lang)
        if dropped:
            fail(path, 'dropped source measurements ' + ', '.join(sorted(dropped)))
        leftovers = english_left(en_article, article)
        if leftovers:
            fail(path, f'English sentences remain: {sorted(leftovers)}')
        if BANNED.search(visible) or doc.elements('del') or doc.elements('s') or any(c in unescape(source) for c in '\u2013\u2014'):
            fail(path, 'banned wording, struck-out price or long dash')
        notices = [n for n in doc.elements('p') if n.attrs.get('class') == 'app-language']
        if len(notices) != 1 or normal(notices[0].text()) != generator.words.APP_LANGUAGE:
            fail(path, 'app-language notice differs from strings')
        if '/founding.js' in source or 'data-founding' in source:
            fail(path, 'English founding bar is present')
        local_date = '11 de novembro de 2026' if lang == 'pt-br' else '11 de noviembre de 2026'
        if not any(local_date in n.text() for n in doc.elements('div') if n.attrs.get('class') == 'updated'):
            fail(path, 'missing local publication dateline')
        faqs = [n for n in doc.elements('section') if n.attrs.get('class') == 'faq']
        visible_faq = []
        for section in faqs:
            pending = None
            for node in section.children:
                if node.tag == 'h3':
                    pending = normal(node.text())
                    if fold(pending) in questions:
                        fail(path, 'duplicate FAQ question with ' + questions[fold(pending)])
                    questions[fold(pending)] = path
                elif node.tag == 'p' and pending:
                    answer = normal(node.text())
                    visible_faq.append((pending, answer))
                    without_faq = texts[path].replace(prose(section), '')
                    if answer in normal(without_faq):
                        fail(path, 'FAQ answer copied from body: ' + pending)
                    pending = None
        schemas = []
        for node in doc.elements('script'):
            if node.attrs.get('type') == 'application/ld+json':
                try:
                    schemas.append(json.loads(source[node.open_end:node.close_start]))
                except ValueError as error:
                    fail(path, 'invalid JSON-LD: ' + str(error))
        schema_faq = [(q['name'], q['acceptedAnswer']['text']) for s in schemas if s.get('@type') == 'FAQPage' for q in s['mainEntity']]
        if visible_faq != schema_faq:
            fail(path, 'FAQPage does not match visible questions and answers')
        expected = Counter((code, ORIGIN + route) for code, route in alternate_routes(entry['english'], generator.words))
        for code, route in expected:
            if code == 'x-default':
                continue
            peer = Document((ROOT / route.removeprefix(ORIGIN).lstrip('/') / 'index.html').read_text())
            if alternates(peer) != expected:
                fail(path, f'hreflang cluster is not reciprocal at {route}')
        en_images = {n.attrs.get('src'): n for n in en_article.walk() if n.tag == 'img'}
        images = {n.attrs.get('src'): n for n in article.walk() if n.tag == 'img'}
        if images.keys() != en_images.keys():
            fail(path, 'images differ from source')
        for src, image in images.items():
            if not image.attrs.get('alt') or image.attrs['alt'] == en_images[src].attrs.get('alt'):
                fail(path, 'image alt text is missing or untranslated')
        for link in doc.elements('a'):
            href = link.attrs.get('href', '')
            target = urlsplit(urljoin(ORIGIN + path, href))
            if target.netloc == 'crispvideo.app':
                translated = dict(generator.words.ROUTES).get(target.path)
                contact_link = any(link in list(n.walk()) for n in doc.elements('section') if n.attrs.get('class') == generator.words.CONTACT_CLASS)
                if translated and target.path != translated and not contact_link:
                    fail(path, 'link should use the translation: ' + href)
                local = ROOT / target.path.lstrip('/')
                if not local.suffix:
                    local /= 'index.html'
                if not local.is_file():
                    fail(path, 'broken local link: ' + href)
                elif target.fragment and local.suffix == '.html':
                    peer = Document(local.read_text())
                    if target.fragment not in {n.attrs.get('id') for n in peer.root.walk()}:
                        fail(path, 'missing link fragment: ' + href)
            elif 'kerr' in target.netloc and not (target.netloc == 'kerr-affiliate-hub.kerrco.workers.dev' and target.path in {'/dl/crisp', '/buy/crisp'}):
                fail(path, 'link to another Kerr domain: ' + href)
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = ET.fromstring((ROOT / 'sitemap.xml').read_text()).findall('s:url', ns)
        matches = [u for u in urls if u.findtext('s:loc', namespaces=ns) == ORIGIN + path]
        if len(matches) != 1 or matches[0].findtext('s:lastmod', namespaces=ns) != '2026-11-11':
            fail(path, 'sitemap entry missing, duplicated or incorrectly dated')

    for lang in ('pt-br', 'es'):
        own = [entry['path'] for entry in entries if entry['lang'] == lang and entry['path'] in signatures]
        all_pages = {}
        for file in (ROOT / lang).rglob('index.html'):
            path = '/' + file.parent.relative_to(ROOT).as_posix() + '/'
            doc = Document(file.read_text())
            nodes = doc.elements('article') or doc.elements('main') or doc.elements('body')
            all_pages[path] = shingles(' '.join(prose(n) for n in nodes))
        for path in own:
            peers = [(jaccard(signatures[path], signature), other) for other, signature in all_pages.items() if other != path]
            maxima[path] = max(peers, default=(0.0, 'none'))
            for score, other in peers:
                limit = 0.40 if other in own else 0.50
                if score >= limit:
                    fail(path, f'5-word Jaccard {score:.3f} >= {limit:.2f} with {other}')
    print('path | query | prose words | max Jaccard | paired page')
    for entry in entries:
        path = entry['path']
        score, other = maxima.get(path, (0.0, 'none'))
        print(f'{path} | {entry["query"]} | {len(words(texts.get(path, "")))} | {score:.3f} | {other}')
    if failures:
        print('\nFAIL: ' + str(len(failures)) + ' guide problems')
        for error in failures:
            print('  ' + error)
        return 1
    print('\nOK: 22 translated guides pass all checks.')
    return 0


if __name__ == '__main__':
    raise SystemExit(check())
