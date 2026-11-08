#!/usr/bin/env python3
"""Check the seven German mirrors using local files only.

--scaffold permits TODO-DE copy on the five unfinished pages. The generated
download and pricing doors must be current and have no TODO-DE markers. Final
mode also rejects every remaining TODO-DE and visible source sentence.
Schema keys, types, dates, currencies, measurements and URLs are not prose.
--selftest exercises the gate against damaged copies in a temporary directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from html import unescape
from html.parser import HTMLParser
import json
import io
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

import de_pages
import de_strings

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://crispvideo.app"
PAGES = (
    ("/", "/de/"),
    ("/download/", "/de/download/"),
    ("/pricing/", "/de/preise/"),
    ("/free-vs-pro/", "/de/kostenlos-oder-pro/"),
    ("/how-to/upscale-video-on-mac/", "/de/anleitung/video-hochskalieren-mac/"),
    ("/how-to/restore-old-home-videos-mac/", "/de/vhs-digitalisieren-und-verbessern/"),
    ("/legal/privacy/", "/de/datenschutz/"),
)
ROUTES = dict(PAGES)
CONTACT = '<section class="kontakt"><h2>Kontakt</h2><p>Kerr &amp; Company LLC<br>E-Mail: <a href="mailto:support@crispvideo.app">support@crispvideo.app</a><br>Web: <a href="https://crispvideo.app/">crispvideo.app</a></p></section>'
NOTICE = "TODO-DE: one sentence that the app itself is in English"
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
COPY_ATTRS = {"alt", "title", "aria-label", "aria-description", "placeholder"}
META_COPY = {"description", "og:title", "og:description", "og:site_name",
             "og:image:alt", "twitter:title", "twitter:description", "twitter:image:alt"}
SCHEMA_FIXED = {"applicationCategory", "softwareVersion", "fileSize", "priceCurrency",
                "totalTime", "datePublished", "dateModified", "price"}
BLOCKS = set("p h1 h2 h3 h4 h5 h6 li td th summary label button figcaption".split())
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def normal(text: str) -> str:
    return " ".join(unescape(text).split())


def local_link(value: str, english: str) -> str:
    """Map page links, retaining queries/fragments and leaving assets external."""
    if not value or value.startswith(("#", "mailto:", "tel:", "sms:", "javascript:")):
        return value
    absolute = urlsplit(urljoin(ORIGIN + english, value))
    if absolute.scheme != "https" or absolute.netloc != "crispvideo.app":
        return value
    path = absolute.path
    if path.endswith("index.html"):
        path = path[:-10]
    path = path.rstrip("/") + "/"
    if path not in ROUTES:
        return value
    if value.startswith(("https://", "//")):
        return urlunsplit((absolute.scheme, absolute.netloc, ROUTES[path], absolute.query, absolute.fragment))
    return urlunsplit(("", "", ROUTES[path], absolute.query, absolute.fragment))


def needs_copy(value: str) -> bool:
    text = normal(value)
    # Bare numbers, prices, URLs, email addresses and punctuation stay intact.
    if re.fullmatch(r"(?:https?://|mailto:|www\.)\S+|[^\s@]+@[^\s@]+", text):
        return False
    return bool(re.search(r"[A-Za-z]", text))


@dataclass
class Node:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    start: int = 0
    open_end: int = 0
    end: int = 0
    close_start: int = 0
    raw: str = ""
    children: list[Node] = field(default_factory=list)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()

    def text(self, *, omit_todos: bool = False) -> str:
        if self.tag in {"script", "style", "template"}:
            return ""
        if self.tag == "#text":
            return "" if omit_todos and "TODO-DE" in self.raw else unescape(self.raw)
        return "".join((" " if c.tag in BLOCKS or c.tag == "br" else "")
                       + c.text(omit_todos=omit_todos) for c in self.children)


class Document(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0] + [m.end() for m in re.finditer("\n", source)]
        self.root = Node("#document")
        self.stack = [self.root]
        self.feed(source)
        self.close()

    def char_offset(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        start = self.char_offset()
        end = start + len(self.get_starttag_text())
        node = Node(tag, dict(attrs), start, end, end, end)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                node = self.stack[i]
                node.close_start = self.char_offset()
                node.end = self.source.index(">", node.close_start) + 1
                del self.stack[i:]
                break

    def add_text(self, raw):
        start = self.char_offset()
        children = self.stack[-1].children
        if children and children[-1].tag == "#text" and children[-1].end == start:
            children[-1].raw += raw
            children[-1].end += len(raw)
        else:
            children.append(Node("#text", start=start, end=start + len(raw), raw=raw))

    def handle_data(self, data):
        self.add_text(data)

    def handle_entityref(self, name):
        self.add_text("&" + name + (";" if self.source[self.char_offset() + len(name) + 1:].startswith(";") else ""))

    def handle_charref(self, name):
        self.add_text("&#" + name + (";" if self.source[self.char_offset() + len(name) + 2:].startswith(";") else ""))

    def elements(self, tag):
        return [n for n in self.root.walk() if n.tag == tag]


def alternates(english: str, german: str) -> str:
    return "\n".join(f'<link rel="alternate" hreflang="{lang}" href="{ORIGIN + path}">'
                     for lang, path in (("de", german), ("en", english), ("x-default", english)))


def schema_copy(key: str, value: str) -> bool:
    return not key.startswith("@") and key not in SCHEMA_FIXED | {"inLanguage"} and needs_copy(value)


def release_values(source: str) -> tuple:
    """Facts in visible copy, metadata and the founding mount, in either locale."""
    doc = Document(source.replace("TODO-DE: ", ""))
    text = doc.root.text() + " " + " ".join(
        value or "" for node in doc.root.walk() for key, value in node.attrs.items()
        if key in {"content", "data-code", "data-now", "data-then"})
    prices = {Decimal(value.replace(',', '.')) for pair in re.findall(
        r'\$\s*(\d+(?:\.\d+)?)|(\d+(?:,\d+)?)\s*\$', text) for value in pair if value}
    versions = set(re.findall(r'\b\d+\.\d+\.\d+(?:\.\d+)*\b', text))
    codes = Counter(re.findall(r'\b[A-Z][A-Z0-9]{5,}\b', text))
    floors = {Decimal(value) for value in re.findall(r'\bmacOS\s+(\d+(?:\.\d+)?)', text)}
    return prices, versions, codes, floors


def check(root: Path, scaffold: bool) -> list[str]:
    problems = []
    generated = de_pages.pages()

    def fail(path, message):
        problems.append(f"{path}: {message}")

    def read(path):
        try:
            return (root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            fail(path, str(error))
            return None

    def copy_value(path, label, source, target):
        if not target or not normal(target):
            fail(path, f"missing {label}")
        elif target.startswith("TODO-DE:"):
            if normal(target[len("TODO-DE:"):]) != normal(source):
                fail(path, f"{label} placeholder does not preserve the English reference")
        elif scaffold and normal(source) == normal(target) and needs_copy(source):
            fail(path, f"unmarked English {label}: {normal(source)!r}")
        if target and Counter(re.findall(r"\d+(?:[.,]\d+)*", source)) != Counter(re.findall(r"\d+(?:[.,]\d+)*", target)):
            fail(path, f"{label} changes source numbers or prices")

    def json_values(path, source, target, english, key="", where="JSON-LD"):
        if type(source) is not type(target):
            fail(path, f"{where} changes a value type")
        elif isinstance(source, dict):
            if source.keys() != target.keys():
                fail(path, f"{where} changes schema keys")
            for k in source.keys() & target.keys():
                json_values(path, source[k], target[k], english, k, where + "." + k)
        elif isinstance(source, list):
            if len(source) != len(target):
                fail(path, f"{where} changes the list length")
            for a, b in zip(source, target):
                json_values(path, a, b, english, key, where + "[]")
        elif isinstance(source, str) and key == "inLanguage":
            if target != "de":
                fail(path, f"{where} must be de")
        elif isinstance(source, str) and schema_copy(key, source):
            copy_value(path, where, source, target)
        else:
            expected = local_link(source, english) if isinstance(source, str) else source
            if target != expected:
                fail(path, f"{where} changes a fixed value or link: expected {expected!r}")

    for english, german in PAGES:
        en_path, de_path = english.lstrip("/") + "index.html", german.lstrip("/") + "index.html"
        en_source, de_source = read(en_path), read(de_path)
        if en_source is None or de_source is None:
            continue
        full = de_path in de_pages.FULL_PAGES
        if full:
            if "TODO-DE" in de_source:
                fail(de_path, "generated page contains TODO-DE markers")
            if de_source != generated[de_pages.SITE / de_path]:
                fail(de_path, "generated German page is stale: copy, prices, versions, codes or links differ")
        else:
            expected = de_pages.refresh_boxes(de_source, de_path, de_pages.llms_txt.facts())
            if expected != de_source:
                fail(de_path, "generated German box is stale: prices, versions, codes or links differ")
            # The writer owns the boxes, while the person owns the surrounding
            # scaffold. Compare that scaffold separately, including its facts.
            if len(de_pages.PBOX.findall(en_source)) != len(de_pages.MARKED_BOX.findall(de_source)):
                fail(de_path, "expected one generated German box per English product box")
            en_source = de_pages.PBOX.sub('', en_source)
            de_source = de_pages.MARKED_BOX.sub('', de_source)
            for label, source_values, target_values in zip(
                    ("prices", "versions", "codes", "macOS versions"),
                    release_values(en_source), release_values(de_source)):
                if source_values != target_values:
                    fail(de_path, f"{label} differ from the English page's values")
        en, de = Document(en_source), Document(de_source)
        for path, doc, language, canonical in ((en_path, en, "en", english), (de_path, de, "de", german)):
            html = doc.elements("html")
            if len(html) != 1 or html[0].attrs.get("lang") != language:
                fail(path, f"expected one html element with lang={language}")
            heads = doc.elements("head")
            links = [n for n in heads[0].walk() if n.tag == "link"] if len(heads) == 1 else []
            canonicals = [n.attrs.get("href") for n in links if n.attrs.get("rel") == "canonical"]
            if language == "de" and canonicals != [ORIGIN + canonical]:
                fail(path, f"canonical must be {ORIGIN + canonical}")
            expected = Counter((lang, ORIGIN + url) for lang, url in
                               (("de", german), ("en", english), ("x-default", english)))
            actual = Counter((n.attrs.get("hreflang"), n.attrs.get("href")) for n in links
                             if n.attrs.get("rel") == "alternate" and "hreflang" in n.attrs)
            if actual != expected:
                fail(path, "expected exactly the reciprocal de, en and x-default hreflang links in head")

        contacts = [n for n in de.elements("section") if "kontakt" in (n.attrs.get("class") or "").split()]
        footers, bodies = de.elements("footer"), de.elements("body")
        if len(contacts) != 1 or de_source[contacts[0].start:contacts[0].end] != CONTACT:
            fail(de_path, "expected the exact contact block")
        if len(contacts) == 1 and (len(footers) != 1 or contacts[0].end > footers[0].start or
                                  de_source[contacts[0].end:footers[0].start].strip()):
            fail(de_path, "contact block must be immediately above the footer")
        notices = [n for n in de.elements("p") if n.attrs.get("class") == "app-language"]
        if len(notices) != 1 or len(bodies) != 1 or notices[0] not in bodies[0].children[:3]:
            fail(de_path, "expected one app-language paragraph at the top of body")
        elif scaffold and normal(notices[0].text()) not in {NOTICE, de_strings.APP_LANGUAGE}:
            fail(de_path, "app-language placeholder must use the required sentence")
        elif not normal(notices[0].text()):
            fail(de_path, "app-language notice is empty")

        if re.search("impressum", unescape(de_source), re.I):
            fail(de_path, "forbidden heading or link: Impressum")
        if de.elements("address") or re.search(r'"(?:@type"\s*:\s*"PostalAddress|telephone"\s*:)', de_source, re.I):
            fail(de_path, "postal address or telephone details are not allowed")
        for n in de.root.walk():
            if (n.attrs.get("href") or "").lower().startswith("tel:"):
                fail(de_path, "telephone links are not allowed")
        visible_body = normal(bodies[0].text()) if len(bodies) == 1 else ""
        if re.search(r"(?:\+\d[\d .()-]{7,}\d|\(\d{3}\)\s*\d{3}[- .]\d{4})", visible_body):
            fail(de_path, "phone numbers are not allowed")
        if re.search(r"\b\d+\s+[A-Za-z ]+\s+(?:Street|Road|Avenue|Boulevard)\b|\b\w+(?:straße|strasse)\s+\d+\b", visible_body, re.I):
            fail(de_path, "postal addresses are not allowed")

        if full:
            # Full generated equality above covers the translated structure,
            # assets, nav, footer, analytics and every fact without requiring
            # German amounts or sentences to mirror English text nodes.
            continue

        # Compare every element, including nav/footer, after removing the two additions.
        def skeleton(node):
            if any(node is n for n in contacts + notices) or node.tag == "link" and "hreflang" in node.attrs:
                return []
            result = [(node.tag, node)] if node.tag not in {"#document", "#text"} else []
            for child in node.children:
                result.extend(skeleton(child))
            if node.tag not in VOID | {"#document", "#text"}:
                result.append(("/" + node.tag, node))
            return result

        # Only the German document has the extra sections. Node identity matters here.
        en_shape, de_shape = skeleton(en.root), skeleton(de.root)
        if german == "/de/":
            # The person's homepage body predates unrelated English tool additions
            # and a tool-count change. Keep its chrome and schema checks, plus the
            # release-value checks above, without rewriting their TODO sentences.
            def chrome(doc):
                nodes = [node for tag in ("head", "header", "footer", "script") for node in doc.elements(tag)]
                nodes += [node for node in doc.elements("div") if "data-founding" in node.attrs]
                return [item for node in nodes for item in skeleton(node)]

            en_shape, de_shape = chrome(en), chrome(de)
        if [tag for tag, _ in en_shape] != [tag for tag, _ in de_shape]:
            fail(de_path, "element structure differs from the English skeleton")
        else:
            for (tag, a), (_, b) in zip(en_shape, de_shape):
                if tag.startswith("/"):
                    continue
                if tag == "title":
                    copy_value(de_path, "title", a.text(), b.text())
                if a.attrs.keys() != b.attrs.keys():
                    fail(de_path, f"{tag} changes attribute names at line {de_source.count(chr(10), 0, b.start) + 1}")
                for key in a.attrs.keys() & b.attrs.keys():
                    original, value = a.attrs[key], b.attrs[key]
                    meta = a.attrs.get("name", a.attrs.get("property"))
                    if key in COPY_ATTRS and original and needs_copy(original) or tag == "meta" and key == "content" and meta in META_COPY:
                        copy_value(de_path, f"{tag} {key}", original, value)
                    else:
                        expected = original
                        if tag == "html" and key == "lang":
                            expected = "de"
                        elif tag == "link" and a.attrs.get("rel") == "canonical" and key == "href":
                            expected = ORIGIN + german
                        elif key == "href" or tag == "meta" and meta == "og:url" and key == "content":
                            expected = local_link(original, english)
                        if value != expected:
                            fail(de_path, f"{tag} {key} must preserve the source value or mapped link: {expected!r}")
                if tag == "script" and a.attrs.get("type") == "application/ld+json":
                    try:
                        json_values(de_path, json.loads(en_source[a.open_end:a.close_start]),
                                    json.loads(de_source[b.open_end:b.close_start]), english)
                    except (ValueError, TypeError) as error:
                        fail(de_path, f"invalid JSON-LD: {error}")
                elif tag == "style" or tag == "script" and scaffold:
                    # Display strings in inline JS may carry markers; code and CSS stay intact.
                    original = en_source[a.open_end:a.close_start]
                    value = de_source[b.open_end:b.close_start].replace("TODO-DE: ", "")
                    if value != original:
                        fail(de_path, f"{tag} code differs from the English skeleton")

        def visible_texts(node):
            if german == "/de/" and node.tag == "#document":
                return [text for tag in ("header", "footer")
                        for part in node.walk() if part.tag == tag for text in visible_texts(part)]
            if any(node is n for n in contacts + notices) or node.tag in {"script", "style", "template", "head"}:
                return []
            if node.tag == "#text":
                return [normal(node.raw)] if normal(node.raw) else []
            return [text for child in node.children for text in visible_texts(child)]

        source_texts, target_texts = visible_texts(en.root), visible_texts(de.root)
        if Counter(re.findall(r"\d+(?:[.,]\d+)*", " ".join(source_texts))) != Counter(re.findall(r"\d+(?:[.,]\d+)*", " ".join(target_texts))):
            fail(de_path, "visible copy changes source numbers or prices")
        if scaffold:
            if len(source_texts) != len(target_texts):
                fail(de_path, "visible copy no longer mirrors the source text nodes")
            for original, value in zip(source_texts, target_texts):
                if needs_copy(original):
                    copy_value(de_path, "visible copy", original, value)
                elif original != value:
                    fail(de_path, f"number, price or link text changed: {original!r}")
        else:
            lines = [str(i) for i, line in enumerate(de_source.splitlines(), 1) if "TODO-DE" in line]
            if lines:
                fail(de_path, f"{de_source.count('TODO-DE')} TODO-DE markers on lines {', '.join(lines)}")
            # Whole blocks catch sentences split by <strong>, links, entities or newlines.
            visible = normal(bodies[0].text(omit_todos=True)) if len(bodies) == 1 else ""
            sentences = set()
            en_bodies = en.elements("body")

            def visible_nodes(node):
                if node.tag in {"script", "style", "template"}:
                    return
                yield node
                for child in node.children:
                    yield from visible_nodes(child)

            for block in visible_nodes(en_bodies[0]) if len(en_bodies) == 1 else []:
                for sentence in re.split(r"(?<=[.!?])\s+", normal(block.text())):
                    if (re.search(r'[.!?]["\u2019\u201d\')\]]*$', sentence) and needs_copy(sentence)
                            and not re.fullmatch(r"(?:Crisp|Pro|Max|Mac|Windows|USD|GIF|MP4|AI)\.", sentence)):
                        sentences.add(sentence)
            for sentence in sorted(sentences):
                if re.search(r"(?<!\w)" + re.escape(sentence) + r"(?!\w)", visible):
                    fail(de_path, f"English sentence remains in visible text: {sentence!r}")

    sitemap = read("sitemap.xml")
    if sitemap is not None:
        try:
            tree = ET.fromstring(sitemap)
            for _, german in PAGES:
                matches = [u for u in tree.findall("s:url", NS) if u.findtext("s:loc", namespaces=NS) == ORIGIN + german]
                if len(matches) != 1:
                    fail("sitemap.xml", f"expected one entry for {ORIGIN + german}")
                    continue
                lastmod = matches[0].findtext("s:lastmod", namespaces=NS) or ""
                try:
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod):
                        raise ValueError
                    date.fromisoformat(lastmod)
                except ValueError:
                    fail("sitemap.xml", f"{german} needs a valid YYYY-MM-DD lastmod")
        except ET.ParseError as error:
            fail("sitemap.xml", f"invalid XML: {error}")
    return problems


def selftest() -> int:
    """Mutation tests use only temporary copies; the working pages never change."""
    baseline = check(ROOT, True)
    if baseline:
        print("FAIL: selftest needs a valid scaffold first:")
        print("\n".join(baseline))
        return 1
    files = [url.lstrip("/") + "index.html" for pair in PAGES for url in pair] + ["sitemap.xml"]
    originals = {name: (ROOT / name).read_text(encoding="utf-8") for name in files}
    cases = [
        ("missing page", "de/download/index.html", None, None, "No such file", True),
        ("wrong language", "de/index.html", 'lang="de"', 'lang="en"', "lang=de", True),
        ("wrong canonical", "de/index.html", 'rel="canonical" href="' + ORIGIN + '/de/"', 'rel="canonical" href="' + ORIGIN + '/"', "canonical must", True),
        ("German hreflang", "de/index.html", 'hreflang="de"', 'hreflang="fr"', "hreflang", True),
        ("English hreflang", "index.html", 'hreflang="en"', 'hreflang="fr"', "hreflang", True),
        ("default hreflang", "de/preise/index.html", 'hreflang="x-default"', 'hreflang="fr"', "hreflang", True),
        ("missing stylesheet", "de/download/index.html", '<link rel="stylesheet" href="/style.css">', '', "generated German page is stale", True),
        ("changed stylesheet", "de/download/index.html", 'href="/style.css"', 'href="/other.css"', "generated German page is stale", True),
        ("changed Plausible", "de/index.html", 'src="https://plausible.io/js/script.js"', 'src="/wrong.js"', "script src must preserve", True),
        ("missing title marker", "de/index.html", '<title>TODO-DE:', '<title>', "unmarked English", True),
        ("missing description marker", "de/index.html", 'content="TODO-DE: Crisp restores', 'content="Crisp restores', "unmarked English", True),
        ("changed reference", "de/download/index.html", de_strings.DOWNLOAD['h1'], 'TODO-DE: Wrong reference', "TODO-DE markers", True),
        ("changed nav", "de/download/index.html", '>Download</a>', '>Wrong</a>', "generated German page is stale", True),
        ("footer removed", "de/download/index.html", '<footer>', '', "generated German page is stale", True),
        ("missing contact", "de/download/index.html", CONTACT, '', "exact contact", True),
        ("changed contact email", "de/download/index.html", CONTACT, CONTACT.replace('support@', 'other@'), "exact contact", True),
        ("contact in footer", "de/download/index.html", CONTACT + '\n<footer>', '<footer>' + CONTACT, "above the footer", True),
        ("missing app notice", "de/download/index.html", '<p class="app-language">' + de_strings.APP_LANGUAGE + '</p>', '', "app-language", True),
        ("wrong app notice", "de/download/index.html", de_strings.APP_LANGUAGE, 'TODO-DE: different notice', "required sentence", True),
        ("unmapped nav link", "de/download/index.html", ORIGIN + '/de/download/?src=nav-download', ORIGIN + '/download/?src=nav-download', "generated German page is stale", True),
        ("unmapped home link", "de/download/index.html", 'href="/de/"', 'href="/"', "generated German page is stale", True),
        ("altered download", "de/download/index.html", 'Crisp.dmg', 'Other.dmg', "generated German page is stale", True),
        ("changed price", "de/preise/index.html", '<span class="pbox-amt">29 $</span>', '<span class="pbox-amt">30 $</span>', "generated German page is stale", True),
        ("changed JSON price", "de/index.html", '"price": "29"', '"price": "30"', "fixed value", True),
        ("unmarked JSON prose", "de/index.html", '"name": "TODO-DE: Crisp Video"', '"name": "Crisp Video"', "unmarked English", True),
        ("invalid JSON", "de/index.html", '"@context": "https://schema.org",', '"@context": ,', "invalid JSON-LD", True),
        ("changed schema type", "de/index.html", '"@type": "Organization"', '"@type": "Thing"', "fixed value", True),
        ("wrong schema language", "de/index.html", '"inLanguage": "de"', '"inLanguage": "en"', "must be de", True),
        ("forbidden word", "de/download/index.html", '</body>', '<!-- iMpReSsUm --></body>', "forbidden heading", True),
        ("encoded forbidden word", "de/download/index.html", '</body>', '<!-- &#73;mpressum --></body>', "forbidden heading", True),
        ("postal markup", "de/download/index.html", '</body>', '<address>123 Example Street</address></body>', "postal address", True),
        ("plain postal address", "de/download/index.html", de_strings.DOWNLOAD['h1'] + '</h1>', '123 Example Street</h1>', "postal addresses", True),
        ("phone link", "de/download/index.html", 'href="mailto:support@crispvideo.app"', 'href="tel:+15555550123"', "telephone links", True),
        ("plain phone", "de/download/index.html", de_strings.DOWNLOAD['h1'] + '</h1>', '+1 555 555 0123</h1>', "phone numbers", True),
        ("missing sitemap URL", "sitemap.xml", '<loc>' + ORIGIN + '/de/</loc>', '<loc>' + ORIGIN + '/other/</loc>', "one entry", True),
        ("invalid lastmod", "sitemap.xml", '<loc>' + ORIGIN + '/de/</loc><lastmod>2026-11-07', '<loc>' + ORIGIN + '/de/</loc><lastmod>2026-02-30', "valid YYYY-MM-DD", True),
        ("invalid sitemap XML", "sitemap.xml", '</urlset>', '', "invalid XML", True),
        ("final markers", "de/download/index.html", None, None, "TODO-DE markers", False),
        ("English sentence", "de/download/index.html", de_strings.DOWNLOAD['speed_same'], 'The picture comes out the same either way; only the wait changes.', "generated German page is stale", False),
        ("sentence across inline tags", "de/index.html", 'TODO-DE: Crisp Video restores, denoises and upscales footage to 4K <strong>TODO-DE: offline</strong>TODO-DE: , then lets you edit it on a real timeline.', 'Crisp Video restores, denoises and upscales footage to 4K <strong>offline</strong>, then lets you edit it on a real timeline.', "English sentence remains", False),
        ("stale Windows version", "de/download/index.html", 'Crisp 1.0.1853', 'Crisp 1.0.1852', "generated German page is stale", True),
        ("stale code", "de/preise/index.html", 'FOUNDINGCRISP', 'WRONGCODE', "generated German page is stale", True),
        ("stale bundle price", "de/preise/index.html", '49,50 $', '48,50 $', "generated German page is stale", True),
        ("stale macOS floor", "de/download/index.html", 'macOS 14.0', 'macOS 13.0', "generated German page is stale", True),
        ("unmarked homepage price", "de/index.html", '$29 once', '$28 once', "prices differ", True),
        ("unmarked homepage code", "de/index.html", 'TODO-DE: FOUNDINGCRISP', 'WRONGCODE', "codes differ", True),
        ("stale generated box", "de/datenschutz/index.html", '14,50 $', '13,50 $', "generated German box is stale", True),
        ("missing box expiry", "de/datenschutz/index.html", de_pages.EXPIRY_SCRIPT, '', "generated German box is stale", True),
    ]
    with tempfile.TemporaryDirectory(prefix="crisp-de-gate-") as folder:
        root = Path(folder)
        for name, source in originals.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
        for label, name, before, after, expected, scaffold in cases:
            path = root / name
            if before is not None:
                if before not in originals[name]:
                    print(f"FAIL: selftest fixture no longer exists: {label}")
                    return 1
                path.write_text(originals[name].replace(before, after, 1), encoding="utf-8")
            elif scaffold:
                path.unlink()
            errors = check(root, scaffold)
            path.write_text(originals[name], encoding="utf-8")
            if not any(expected in error for error in errors):
                print(f"FAIL: selftest missed {label}: {errors}")
                return 1

        # A marker-free fixture with synthetic copy must pass final mode. It is
        # deliberately not a translation, and retains each original digit.
        def dummy(text):
            return " " + re.sub(r"[A-Za-z]+", lambda m: m.group(0) if m.group(0) == "macOS"
                                or re.fullmatch(r"[A-Z]{6,}", m.group(0)) else "ZZZ", text) + " "

        def dummy_json(value):
            if isinstance(value, dict):
                return {k: dummy_json(v) for k, v in value.items()}
            if isinstance(value, list):
                return [dummy_json(v) for v in value]
            return dummy(value) if isinstance(value, str) and value.startswith("TODO-DE:") else value

        for _, german in PAGES:
            name = german.lstrip("/") + "index.html"
            source = originals[name]
            doc = Document(source)
            edits = []

            def substitute(node):
                if node.tag == "script" and node.attrs.get("type") == "application/ld+json":
                    edits.append((node.open_end, node.close_start,
                                  json.dumps(dummy_json(json.loads(source[node.open_end:node.close_start])))))
                    return
                if node.tag in {"script", "style"}:
                    return
                if node.tag == "#text" and "TODO-DE:" in node.raw:
                    edits.append((node.start, node.end, dummy(normal(node.raw))))
                elif node.tag != "#text":
                    tag = source[node.start:node.open_end]
                    for key, value in node.attrs.items():
                        if value and value.startswith("TODO-DE:"):
                            tag = re.sub(r'(?<![\w-])' + re.escape(key) + r'="[^"]*"',
                                         lambda m: key + '="' + dummy(value) + '"', tag)
                    if tag != source[node.start:node.open_end]:
                        edits.append((node.start, node.open_end, tag))
                for child in node.children:
                    substitute(child)

            substitute(doc.root)
            for start, end, replacement in sorted(edits, reverse=True):
                source = source[:start] + replacement + source[end:]
            (root / name).write_text(source, encoding="utf-8")
        errors = check(root, False)
        if errors:
            print(f"FAIL: final mode rejected marker-free synthetic copy: {errors}")
            return 1
        for _, german in PAGES:
            name = german.lstrip("/") + "index.html"
            (root / name).write_text(originals[name].replace("TODO-DE: ", ""), encoding="utf-8")
        errors = check(root, False)
        if not any("English sentence remains" in error for error in errors) or any("TODO-DE markers" in error for error in errors):
            print(f"FAIL: final mode must reject English even after all markers are removed: {errors}")
            return 1
    generator_selftest()
    print(f"OK: {len(cases) + 2} German gate tests and generator regression checks passed.")
    return 0


def generator_selftest() -> None:
    """Exercise changed sources and check/write mode, without touching the site."""
    f = de_pages.llms_txt.facts()
    changed = dict(f, price=Decimal("41"), now=Decimal("20.50"), code="NEXTCRISP",
                   ends="2026-12-16T07:59:59Z", os="macOS 15.0 or later", cap=22, refund_days=40)
    current_win = de_pages.llms_txt.windows()
    win = {"version": "2.3.4567", "url": current_win["url"].replace(current_win["version"], "2.3.4567")}
    with patch.object(de_pages.llms_txt, "facts", return_value=changed), patch.object(de_pages.llms_txt, "windows", return_value=win):
        page = de_pages.page("download", changed)
        for value in ("41 $", "20,50 $", "NEXTCRISP", "15. Dezember", changed["ends"], win["version"], win["url"], changed["os"]):
            assert value in page, f"German page did not update {value}"
        assert 'id="macos-speed"' not in page, "speed section must follow the English macOS floor"
        assert "22 Sekunden" in page and "40 Tage" in page
        for name in de_pages.OTHER_PAGES:
            before = (ROOT / name).read_text()
            after = de_pages.refresh_boxes(before, name, changed)
            assert de_pages.MARKED_BOX.sub('', before) == de_pages.MARKED_BOX.sub('', after), "box refresh changed body copy"
            assert de_pages.refresh_boxes(after, name, changed) == after, "box refresh is not idempotent"
    with patch.object(de_pages.llms_txt, "windows", return_value=None):
        assert 'class="win-link"' not in de_pages.box("de-test", f=f)
    instalments = dict(f, price=Decimal("80"), now=Decimal("60"), bnpl=True)
    assert 'TODO-DE: or 4 × 20 $' in de_pages.box("de-test", f=instalments)
    assert 'TODO-DE: or 4 × 15 $' in de_pages.box("de-test", f=instalments)
    live = de_pages.llms_txt.founding_live
    with patch.object(de_pages.llms_txt, "founding_live", side_effect=lambda fact: live(fact, datetime(2030, 1, 1, tzinfo=timezone.utc))):
        assert 'class="pbox-found"' not in de_pages.page("download", f)
        assert 'data-until=' not in de_pages.bundle(), "expired bundle offer remains"
    assert de_pages.last_day("2026-12-01T08:00:00Z") == "30. November"
    assert de_pages.EXPIRY_SCRIPT in de_pages.thankyou_xsell.block()
    with tempfile.TemporaryDirectory(prefix="crisp-de-generator-") as folder:
        root = Path(folder)
        facts = root / "dodo-facts.json"
        with patch.object(de_pages.thankyou_xsell, "FACTS", facts):
            try:
                de_pages.bundle()
            except SystemExit as error:
                assert "required regular prices file is missing" in str(error)
            else:
                raise AssertionError("missing regular prices did not fail")
            facts.write_text(json.dumps({"products": {name: {"name": name, "price_cents": cents}
                                                    for name, cents in (("Crisp", 3100), ("Docket SEO", 6100), ("Outlier", 5100))}}))
            assert "143 $" in de_pages.bundle(), "bundle's separate total was not read from Dodo"
        for name in de_pages.OTHER_PAGES:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((ROOT / name).read_text())
        with patch.object(de_pages, "SITE", root), redirect_stdout(io.StringIO()):
            assert de_pages.write(check=True) == 1, "missing German doors passed check"
            assert de_pages.write() == 0
            assert de_pages.write(check=True) == 0
            page = root / de_pages.FULL_PAGES[0]
            page.write_text(page.read_text().replace("29 $", "28 $", 1))
            assert de_pages.write(check=True) == 1, "stale German price passed check"
        # Exercise the English entry point's integration without writing English
        # files or changing any release source.
        with patch.object(de_pages, "write", return_value=1) as german_check, redirect_stdout(io.StringIO()):
            assert de_pages.landing.main(["--check"]) == 1
            german_check.assert_called_once_with(check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scaffold", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    problems = check(ROOT, args.scaffold)
    if problems:
        print(f"FAIL: {len(problems)} German page problem(s):")
        for problem in problems:
            print("  " + problem)
        return 1
    print(f"OK: all seven German pages pass {'scaffold' if args.scaffold else 'final'} checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
