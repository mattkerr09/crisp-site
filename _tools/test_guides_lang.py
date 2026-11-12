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
from tempfile import TemporaryDirectory
import unicodedata
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET

from gate_lang import Document, normal
from lang_pages import LanguagePages, alternate_routes
from sitewide_chrome import KCO

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


def reader_address_errors(text: str) -> bool:
    """Catch formal reader address without rejecting an app's own README."""
    return bool(re.search(r'\busted\b|\bsu(?:s)?\s+(?:Mac|PC|ordenador|moneda|grabaciones|vídeos|propio)\b|'
                          r'\b(?:al pagar verá|úselo|expórtelo)\b', text, re.I))


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


def css_classes(css: str) -> set[str]:
    """Read class selectors, excluding comments and declaration values."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', css)
    return {name for selector in re.findall(r'([^{}]+)\{', css)
            for name in re.findall(r'\.([A-Za-z_][\w-]*)', selector)}


def stylesheet_errors(doc: Document, file: Path, root: Path = ROOT) -> list[str]:
    """Check only CSS this page loads, resolving local links without a network."""
    styles = [doc.source[n.open_end:n.close_start] for n in doc.elements('style')]
    errors = []
    for link in doc.elements('link'):
        if 'stylesheet' not in (link.attrs.get('rel') or '').split():
            continue
        href = link.attrs.get('href') or ''
        target = urlsplit(urljoin(ORIGIN + '/' + file.relative_to(root).as_posix(), href))
        if not href or target.netloc != urlsplit(ORIGIN).netloc:
            errors.append('cannot check stylesheet offline: ' + href)
            continue
        css_file = root / target.path.lstrip('/')
        if not css_file.is_file():
            errors.append('missing stylesheet: ' + href)
            continue
        styles.append(css_file.read_text())
    defined = css_classes('\n'.join(styles))
    used = {name for node in doc.root.walk() for name in (node.attrs.get('class') or '').split()}
    errors.extend('class has no selector in loaded CSS: ' + name for name in sorted(used - defined))
    return errors


def home_guide_errors(doc: Document, lang: str, entries: list[dict], root: Path = ROOT) -> list[str]:
    errors = []
    linked = set()
    for link in doc.elements('a'):
        href = link.attrs.get('href') or ''
        target = urlsplit(urljoin(ORIGIN + '/' + lang + '/', href))
        if '/guia/' not in target.path:
            continue
        if target.scheme != 'https' or target.netloc != urlsplit(ORIGIN).netloc or not re.fullmatch(
                '/' + lang + r'/guia/[a-z0-9-]+/', target.path):
            errors.append('guide link must stay in the home language folder: ' + href)
            continue
        linked.add(target.path)
        text = normal(link.text())
        if re.search(r'en inglés|em inglês', text, re.I):
            errors.append('translated guide link has an English label: ' + href)
        file = root / target.path.lstrip('/') / 'index.html'
        if not file.is_file():
            errors.append('missing home guide target: ' + href)
            continue
        h1s = Document(file.read_text()).elements('h1')
        if len(h1s) != 1 or text != normal(h1s[0].text()):
            errors.append('home guide link text must match its H1: ' + href)
    for entry in entries:
        if entry['lang'] == lang and entry['path'] not in linked:
            errors.append('guide missing from language home: ' + entry['path'])
    return errors


def guide_footer(words) -> str:
    company = KCO.replace('Made by Kerr &amp; Company', words.FOOTER['made_by'])
    return (f'<footer><div class="wrap">\n'
            f'<p>&#9670; {words.FOOTER["line"]} <a href="{ORIGIN}{dict(words.ROUTES)["/"]}">crispvideo.app</a> &middot; '
            f'<a href="{ORIGIN}/about/">{words.FOOTER["about"]}</a></p>\n'
            f'{company}\n</div></footer>')


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
    assert reader_address_errors('Sus vídeos se quedan en su Mac. Al pagar verá su moneda.')
    assert reader_address_errors('Úselo gratis y expórtelo.')
    assert not reader_address_errors('Tus vídeos se quedan en tu Mac. Verás tu moneda.')
    assert not reader_address_errors('Su README describe sus funciones y su versión para Mac.')
    assert not reader_address_errors('Un archivo comprimido no se verá como la grabación directa.')
    assert css_classes('/* .fake {} */ .real:hover {content:".fake {}"; src:url(/fake.css);} '
                       '@media (width < 50rem) {.nested > .other {color:red;}}') == {'real', 'nested', 'other'}
    with TemporaryDirectory() as folder:
        root = Path(folder)
        (root / 'guide').mkdir()
        (root / 'shared.css').write_text('.linked {color:red;}')
        (root / 'guide/local.css').write_text('.relative {color:blue;}')
        page = root / 'guide/index.html'
        source = ('<link rel="stylesheet" href="/shared.css?v=1">'
                  '<link rel="stylesheet" href="local.css">'
                  '<style>.inline {color:green;}</style><p class="linked relative inline">Text</p>')
        assert not stylesheet_errors(Document(source), page, root)
        assert stylesheet_errors(Document(source.replace('relative inline', 'faq inline')), page, root) == [
            'class has no selector in loaded CSS: faq']
        assert 'missing stylesheet: missing.css' in stylesheet_errors(
            Document(source.replace('local.css', 'missing.css')), page, root)
        assert 'cannot check stylesheet offline: https://example.com/style.css' in stylesheet_errors(
            Document('<link rel="stylesheet" href="https://example.com/style.css">'), page, root)
        guide = root / 'es/guia/example'
        guide.mkdir(parents=True)
        (guide / 'index.html').write_text('<h1>Guía de ejemplo</h1>')
        entries = [{'lang': 'es', 'path': '/es/guia/example/'}]
        home = '<a href="https://crispvideo.app/es/guia/example/">Guía de ejemplo</a>'
        assert not home_guide_errors(Document(home), 'es', entries, root)
        assert home_guide_errors(Document(''), 'es', entries, root)
        assert home_guide_errors(Document(home.replace('/example/', '/missing/')), 'es', entries, root)
        assert home_guide_errors(Document(home.replace('/es/', '/pt-br/')), 'es', entries, root)
        assert home_guide_errors(Document(home.replace('crispvideo.app', 'example.com')), 'es', entries, root)
        for label in ('Guía distinta', 'Guía de ejemplo, en inglés', 'Guía de ejemplo, em inglês'):
            assert home_guide_errors(Document(home.replace('Guía de ejemplo', label)), 'es', entries, root)


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

    assert len(entries) == 24 and Counter(entry['lang'] for entry in entries) == {'pt-br': 13, 'es': 11}
    assert len({entry['path'] for entry in entries}) == 24
    required = {'english', 'lang', 'path', 'query', 'demand', 'demand_market', 'demand_read', 'published'}
    for entry in entries:
        path, lang = entry['path'], entry['lang']
        heic = entry['english'] == '/how-to/convert-heic-to-jpg-mac/'
        batch_date = '2026-11-12' if heic else '2026-11-11'
        fields = required | ({'es_demand_split'} if lang == 'es' else set())
        if set(entry) != fields or entry['demand_read'] != batch_date or entry['published'] != batch_date:
            fail(path, 'manifest fields or dates differ from the batch contract')
        split = {'Spain': 1065, 'Mexico': 115} if heic else {'Spain': 4122, 'Mexico': 1111}
        split['source'] = 'Bing exact, 90 days, read ' + batch_date
        if lang == 'es' and entry.get('es_demand_split') != split:
            fail(path, 'Spanish market split differs from the measured batch demand')
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
        for error in stylesheet_errors(doc, file):
            fail(path, error)
        generator = LanguagePages(lang)
        footers = doc.elements('footer')
        if len(footers) != 1 or source[footers[0].start:footers[0].end] != guide_footer(generator.words):
            fail(path, 'footer must match the shared local wording and company link byte for byte')
        company_links = [n for footer in footers for n in footer.walk()
                         if n.tag == 'a' and n.attrs.get('href') == 'https://kerrandcompanyholdings.com/']
        if len(company_links) != 1:
            fail(path, 'footer must have exactly one company link')
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
        if lang == 'es' and reader_address_errors(visible):
            fail(path, 'Spanish reader address must use tú')
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
        day = int(entry['published'].rsplit('-', 1)[1])
        month = 'novembro' if lang == 'pt-br' else 'noviembre'
        local_date = f'{day} de {month} de 2026'
        if not any(local_date in n.text() for n in doc.elements('div') if n.attrs.get('class') == 'updated'):
            fail(path, 'missing local publication dateline')
        faqs = [n for n in doc.elements('section') if n.attrs.get('id') == 'faq']
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
            elif 'kerr' in target.netloc and not (
                    link in company_links or
                    target.netloc == 'kerr-affiliate-hub.kerrco.workers.dev' and target.path in {'/dl/crisp', '/buy/crisp'}):
                fail(path, 'link to another Kerr domain: ' + href)
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = ET.fromstring((ROOT / 'sitemap.xml').read_text()).findall('s:url', ns)
        matches = [u for u in urls if u.findtext('s:loc', namespaces=ns) == ORIGIN + path]
        if len(matches) != 1 or matches[0].findtext('s:lastmod', namespaces=ns) != entry['published']:
            fail(path, 'sitemap entry missing, duplicated or incorrectly dated')

    adobe_tables = (
        ('how-to/mute-video-mac', 'Premiere', 'Not checked',
         ('Mute a clip (drop the audio)', 'Keeps the video lossless (no re-compress)'),
         'Read 11 November 2026', 'Adjust audio gain in Premiere'),
        ('pt-br/guia/remover-audio-de-video-mac', 'Premiere', 'Não verificado',
         ('Remover a faixa de áudio', 'Imagem sem recompressão'),
         'Verificado em 11 de novembro de 2026', 'Adjust audio gain in Premiere'),
        ('how-to/make-a-gif-on-mac', 'Photoshop', 'Not checked',
         ('Optimised palette (sharp, small)', 'Boomerang built-in'),
         'Read 11 November 2026', 'Create frame-based animations in Photoshop'),
        ('es/guia/convertir-video-a-gif-mac', 'Photoshop', 'No comprobado',
         ('Paleta optimizada', 'Boomerang integrado'),
         'Comprobado el 11 de noviembre de 2026', 'Create frame-based animations in Photoshop'),
    )
    for path, vendor, unchecked, labels, date, help_page in adobe_tables:
        doc = Document((ROOT / path / 'index.html').read_text())
        table = doc.elements('table')[0]
        rows = [node for node in table.walk() if node.tag == 'tr']
        if normal(rows[0].children[-1].text()) != vendor:
            fail(path, 'Adobe table must use the current product name')
        if sum(normal(row.children[-1].text()) == unchecked for row in rows) != len(labels):
            fail(path, 'only the unsupported Adobe cells should be unchecked')
        for label in labels:
            cells = [node for row in rows for node in row.children
                     if node.tag in {'th', 'td'} and normal(row.children[0].text()) == label]
            if not cells or normal(cells[-1].text()) != unchecked:
                fail(path, 'unsupported Adobe cell must be unchecked: ' + label)
        wrapper = next(node for node in doc.root.walk() if table in node.children)
        source_line = wrapper.children[wrapper.children.index(table) + 1:]
        source_text = normal(' '.join(node.text() for node in source_line))
        if date not in source_text or help_page not in source_text or vendor not in source_text:
            fail(path, 'missing Adobe help and plans read date below the table')
    baseline = json.loads((ROOT / '_tools/claim_dates_baseline.json').read_text())['undated']
    for path in ('how-to/mute-video-mac', 'how-to/make-a-gif-on-mac'):
        if path in baseline:
            fail(path, 'dated Adobe table must be removed from the baseline')

    dated_guides = ('add-a-border-to-video-mac', 'color-grade-video-mac', 'loop-video-mac')
    dot_guides = ['how-to/' + name for name in (*dated_guides, 'change-video-speed-mac',
                                              'mute-video-mac', 'compress-video-on-mac')]
    dot_guides += ['pt-br/guia/remover-audio-de-video-mac', 'pt-br/guia/comprimir-video-mac',
                   'es/guia/comprimir-video-mac']
    for path in dot_guides:
        doc = Document((ROOT / path / 'index.html').read_text())
        if any(normal(node.text()) == '.' for node in doc.elements('td')):
            fail(path, 'table cell must state a value or say it was not checked')
        if path.removeprefix('how-to/') in dated_guides:
            if path in baseline:
                fail(path, 'dated comparison must be removed from the baseline')
            for table in doc.elements('table'):
                headers = ' '.join(node.text() for node in table.walk() if node.tag == 'th')
                if 'iMovie' in headers:
                    wrapper = next(node for node in doc.root.walk() if table in node.children)
                    source_line = wrapper.children[wrapper.children.index(table) + 1:]
                    if 'Checked 11 November 2026' not in normal(' '.join(n.text() for n in source_line)):
                        fail(path, 'comparison needs its vendor read date below the table')

    for name in ('es/index.html', 'es/gratis-o-pro/index.html', 'es/descargar/index.html', 'es/precios/index.html'):
        if reader_address_errors(normal(Document((ROOT / name).read_text()).root.text())):
            fail(name, 'Spanish reader address must use tú')

    for lang in ('pt-br', 'es'):
        home = Document((ROOT / lang / 'index.html').read_text())
        for error in home_guide_errors(home, lang, entries):
            fail('/' + lang + '/', error)
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
    print(f'\nOK: {len(entries)} translated guides pass all checks.')
    return 0


if __name__ == '__main__':
    raise SystemExit(check())
