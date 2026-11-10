#!/usr/bin/env python3
"""Check localized pages using local files and strings_<lang>.py.

--scaffold permits TODO markers on unfinished mirrors. Generated doors must
always be current. Final mode rejects markers and visible English sentences.
--selftest exercises the gate against damaged copies in temporary folders.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from html import escape, unescape
from html.parser import HTMLParser
import json
import io
from pathlib import Path
import re
import sys
import tempfile
from types import ModuleType
from typing import Callable
from unittest.mock import patch
from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

from lang_pages import LanguagePages

ORIGIN = "https://crispvideo.app"
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

    def text(self, *, omit_todos: bool = False, todo: str = "") -> str:
        if self.tag in {"script", "style", "template"}:
            return ""
        if self.tag == "#text":
            return "" if omit_todos and todo and todo in self.raw else unescape(self.raw)
        return "".join((" " if c.tag in BLOCKS or c.tag == "br" else "")
                       + c.text(omit_todos=omit_todos, todo=todo) for c in self.children)


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


def schema_copy(key: str, value: str) -> bool:
    return not key.startswith("@") and key not in SCHEMA_FIXED | {"inLanguage"} and needs_copy(value)


def release_values(source: str, todo: str) -> tuple:
    """Facts in visible copy, metadata and the founding mount, in either locale."""
    doc = Document(source.replace(todo + ": ", ""))
    text = doc.root.text() + " " + " ".join(
        value or "" for node in doc.root.walk() for key, value in node.attrs.items()
        if key in {"content", "data-code", "data-now", "data-then"})
    prices = {Decimal(value.replace(',', '.')) for pair in re.findall(
        r'\$\s*(\d+(?:\.\d+)?)|(\d+(?:,\d+)?)\s*\$', text) for value in pair if value}
    versions = set(re.findall(r'\b\d+\.\d+\.\d+(?:\.\d+)*\b', text))
    codes = Counter(re.findall(r'\b[A-Z][A-Z0-9]{5,}\b', text))
    floors = {Decimal(value) for value in re.findall(r'\bmacOS\s+(\d+(?:\.\d+)?)', text)}
    return prices, versions, codes, floors


class LanguageGate:
    def __init__(self, lang: str, root: Path | None = None):
        self.lang = lang
        self.ROOT = root if root is not None else Path(__file__).resolve().parent.parent
        self.generator = LanguagePages(lang, self.ROOT)
        self.words = self.generator.words
        self.PAGES = self.words.ROUTES
        self.ROUTES = dict(self.PAGES)
        self.CONTACT = self.words.CONTACT
        self.todo = "TODO-" + lang.upper()
        self.NOTICE = self.words.TODO_NOTICE
        self.home_file = self.ROUTES["/"].lstrip("/") + "index.html"
        self.download_file = self.ROUTES["/download/"].lstrip("/") + "index.html"

    def local_link(self, value: str, english: str) -> str:
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
        if path not in self.ROUTES:
            return value
        if value.startswith(("https://", "//")):
            return urlunsplit((absolute.scheme, absolute.netloc, self.ROUTES[path], absolute.query, absolute.fragment))
        return urlunsplit(("", "", self.ROUTES[path], absolute.query, absolute.fragment))

    def alternates(self, english: str, localized: str) -> str:
        return "\n".join(f'<link rel="alternate" hreflang="{lang}" href="{ORIGIN + path}">'
                         for lang, path in ((self.lang, localized), ("en", english), ("x-default", english)))

    def check(self, root: Path, scaffold: bool) -> list[str]:
        problems = []
        generated = self.generator.pages()

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
            elif target.startswith(self.todo + ":"):
                if normal(target[len(self.todo + ":"):]) != normal(source):
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
                if target != self.lang:
                    fail(path, f"{where} must be {self.lang}")
            elif isinstance(source, str) and schema_copy(key, source):
                copy_value(path, where, source, target)
            else:
                expected = self.local_link(source, english) if isinstance(source, str) else source
                if target != expected:
                    fail(path, f"{where} changes a fixed value or link: expected {expected!r}")

        for english, localized in self.PAGES:
            en_path, target_path = english.lstrip("/") + "index.html", localized.lstrip("/") + "index.html"
            en_source, target_source = read(en_path), read(target_path)
            if en_source is None or target_source is None:
                continue
            full = target_path in self.generator.FULL_PAGES
            # Written pages opt out of mirror structure, box counts and source-number comparisons.
            written = f'name="{self.lang}-written"' in target_source
            if full:
                if self.todo in target_source:
                    fail(target_path, f"generated page contains {self.todo} markers")
                if target_source != generated[self.generator.SITE / target_path]:
                    fail(target_path, f"generated {self.words.LANGUAGE_NAME} page is stale: copy, prices, versions, codes or links differ")
            else:
                expected = self.generator.refresh_boxes(target_source, target_path, self.generator.llms_txt.facts())
                if expected != target_source:
                    fail(target_path, f"generated {self.words.LANGUAGE_NAME} box is stale: prices, versions, codes or links differ")
                # The writer owns the boxes, while the person owns the surrounding
                # scaffold. Compare that scaffold separately, including its facts.
                if not written and len(self.generator.PBOX.findall(en_source)) != len(self.generator.MARKED_BOX.findall(target_source)):
                    fail(target_path, f"expected one generated {self.words.LANGUAGE_NAME} box per English product box")
                en_source = self.generator.PBOX.sub('', en_source)
                target_source = self.generator.MARKED_BOX.sub('', target_source)
                for label, source_values, target_values in zip(
                        ("prices", "versions", "codes", "macOS versions"),
                        release_values(en_source, self.todo), release_values(target_source, self.todo)):
                    if source_values != target_values and not written:
                        fail(target_path, f"{label} differ from the English page's values")
            en, target = Document(en_source), Document(target_source)
            for path, doc, language, canonical in ((en_path, en, "en", english), (target_path, target, self.lang, localized)):
                html = doc.elements("html")
                if len(html) != 1 or html[0].attrs.get("lang") != language:
                    fail(path, f"expected one html element with lang={language}")
                heads = doc.elements("head")
                links = [n for n in heads[0].walk() if n.tag == "link"] if len(heads) == 1 else []
                canonicals = [n.attrs.get("href") for n in links if n.attrs.get("rel") == "canonical"]
                if doc is target and canonicals != [ORIGIN + canonical]:
                    fail(path, f"canonical must be {ORIGIN + canonical}")
                expected = Counter((lang, ORIGIN + url) for lang, url in
                                   ((self.lang, localized), ("en", english), ("x-default", english)))
                actual = Counter((n.attrs.get("hreflang"), n.attrs.get("href")) for n in links
                                 if n.attrs.get("rel") == "alternate" and "hreflang" in n.attrs)
                if actual != expected:
                    fail(path, f"expected exactly the reciprocal {self.lang}, en and x-default hreflang links in head")

            contacts = [n for n in target.elements("section") if self.words.CONTACT_CLASS in (n.attrs.get("class") or "").split()]
            footers, bodies = target.elements("footer"), target.elements("body")
            if len(contacts) != 1 or target_source[contacts[0].start:contacts[0].end] != self.CONTACT:
                fail(target_path, "expected the exact contact block")
            if len(contacts) == 1 and (len(footers) != 1 or contacts[0].end > footers[0].start or
                                      target_source[contacts[0].end:footers[0].start].strip()):
                fail(target_path, "contact block must be immediately above the footer")
            notices = [n for n in target.elements("p") if n.attrs.get("class") == "app-language"]
            # The launch-price bar's mount and its script (founding.js's text, inline) sit first in <body> on the pages that carry
            # the bar (sitewide_chrome.py, 10 Nov 2026: there the bar is drawn before the page paints and pushes nothing down).
            # founding.js always put the bar above this notice once the page ran, so the notice is still the top of the page.
            def _bar_script(c):
                return c.tag == "script" and (c.attrs.get("src") == "/founding.js" or
                                              "window.__kcFounding" in "".join(x.raw for x in c.children if x.tag == "#text"))
            top = [c for c in (bodies[0].children if len(bodies) == 1 else [])
                   if not (c.tag == "#text" and not c.raw.strip())
                   and not (c.tag == "div" and "data-founding" in c.attrs)
                   and not _bar_script(c)]
            if len(notices) != 1 or len(bodies) != 1 or notices[0] not in top[:1]:
                fail(target_path, "expected one app-language paragraph at the top of body")
            elif scaffold and normal(notices[0].text()) not in {self.NOTICE, self.words.APP_LANGUAGE}:
                fail(target_path, "app-language placeholder must use the required sentence")
            elif not normal(notices[0].text()):
                fail(target_path, "app-language notice is empty")

            if any(re.search(re.escape(word), unescape(target_source), re.I) for word in self.words.FORBIDDEN_WORDS):
                fail(target_path, self.words.FORBIDDEN_WORD_MESSAGE)
            if target.elements("address") or re.search(r'"(?:@type"\s*:\s*"PostalAddress|telephone"\s*:)', target_source, re.I):
                fail(target_path, "postal address or telephone details are not allowed")
            for n in target.root.walk():
                if (n.attrs.get("href") or "").lower().startswith("tel:"):
                    fail(target_path, "telephone links are not allowed")
            visible_body = normal(bodies[0].text()) if len(bodies) == 1 else ""
            if re.search(r"(?:\+\d[\d .()-]{7,}\d|\(\d{3}\)\s*\d{3}[- .]\d{4})", visible_body):
                fail(target_path, "phone numbers are not allowed")
            if re.search(self.words.POSTAL_ADDRESS_PATTERN, visible_body, re.I):
                fail(target_path, "postal addresses are not allowed")

            if full:
                # Full generated equality above covers the translated structure,
                # assets, nav, footer, analytics and every fact without requiring
                # localized amounts or sentences to mirror English text nodes.
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

            # Only the localized document has the extra sections. Node identity matters here.
            en_shape, target_shape = skeleton(en.root), skeleton(target.root)
            if localized == self.ROUTES["/"]:
                # The person's homepage body predates unrelated English tool additions
                # and a tool-count change. Keep its chrome and schema checks, plus the
                # release-value checks above, without rewriting their TODO sentences.
                def chrome(doc):
                    nodes = [node for tag in ("head", "header", "footer", "script") for node in doc.elements(tag)]
                    nodes += [node for node in doc.elements("div") if "data-founding" in node.attrs]
                    return [item for node in nodes for item in skeleton(node)]

                en_shape, target_shape = chrome(en), chrome(target)
            if written:
                # A written page skips only the MIRROR checks. Its structured data must still parse, and every Article, FAQPage or
                # WebPage block must carry the target inLanguage value.
                for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', target_source, re.S):
                    try:
                        data = json.loads(m.group(1))
                    except ValueError as error:
                        fail(target_path, f"invalid JSON-LD: {error}")
                        continue
                    items = data if isinstance(data, list) else [data]
                    items = items + [it for d in items if isinstance(d, dict) for it in d.get("@graph", [])]   # a graph hides its nodes
                    for item in items:
                        if isinstance(item, dict) and item.get("@type") in ("Article", "FAQPage", "WebPage", "WebSite", "SoftwareApplication")\
                                and item.get("inLanguage") != self.lang:
                            fail(target_path, f"JSON-LD {item.get('@type')} must be {self.lang} (inLanguage)")
            elif [tag for tag, _ in en_shape] != [tag for tag, _ in target_shape]:
                fail(target_path, "element structure differs from the English skeleton")
            else:
                for (tag, a), (_, b) in zip(en_shape, target_shape):
                    if tag.startswith("/"):
                        continue
                    if tag == "title":
                        copy_value(target_path, "title", a.text(), b.text())
                    if a.attrs.keys() != b.attrs.keys():
                        fail(target_path, f"{tag} changes attribute names at line {target_source.count(chr(10), 0, b.start) + 1}")
                    for key in a.attrs.keys() & b.attrs.keys():
                        original, value = a.attrs[key], b.attrs[key]
                        meta = a.attrs.get("name", a.attrs.get("property"))
                        if key in COPY_ATTRS and original and needs_copy(original) or tag == "meta" and key == "content" and meta in META_COPY:
                            copy_value(target_path, f"{tag} {key}", original, value)
                        else:
                            expected = original
                            if tag == "html" and key == "lang":
                                expected = self.lang
                            elif tag == "link" and a.attrs.get("rel") == "canonical" and key == "href":
                                expected = ORIGIN + localized
                            elif key == "href" or tag == "meta" and meta == "og:url" and key == "content":
                                expected = self.local_link(original, english)
                            if value != expected:
                                fail(target_path, f"{tag} {key} must preserve the source value or mapped link: {expected!r}")
                    if tag == "script" and a.attrs.get("type") == "application/ld+json":
                        try:
                            json_values(target_path, json.loads(en_source[a.open_end:a.close_start]),
                                        json.loads(target_source[b.open_end:b.close_start]), english)
                        except (ValueError, TypeError) as error:
                            fail(target_path, f"invalid JSON-LD: {error}")
                    elif tag == "style" or tag == "script" and scaffold:
                        # Display strings in inline JS may carry markers; code and CSS stay intact.
                        original = en_source[a.open_end:a.close_start]
                        value = target_source[b.open_end:b.close_start].replace(self.todo + ": ", "")
                        if value != original:
                            fail(target_path, f"{tag} code differs from the English skeleton")

            def visible_texts(node):
                if localized == self.ROUTES["/"] and node.tag == "#document":
                    return [text for tag in ("header", "footer")
                            for part in node.walk() if part.tag == tag for text in visible_texts(part)]
                if any(node is n for n in contacts + notices) or node.tag in {"script", "style", "template", "head"}:
                    return []
                if node.tag == "#text":
                    return [normal(node.raw)] if normal(node.raw) else []
                return [text for child in node.children for text in visible_texts(child)]

            source_texts, target_texts = visible_texts(en.root), visible_texts(target.root)
            # Written pages keep their own text. Language, links, contact, markers and generated boxes are still checked.
            if written:
                source_texts = target_texts = []
            if Counter(re.findall(r"\d+(?:[.,]\d+)*", " ".join(source_texts))) != Counter(re.findall(r"\d+(?:[.,]\d+)*", " ".join(target_texts))):
                fail(target_path, "visible copy changes source numbers or prices")
            if scaffold:
                if len(source_texts) != len(target_texts):
                    fail(target_path, "visible copy no longer mirrors the source text nodes")
                for original, value in zip(source_texts, target_texts):
                    if needs_copy(original):
                        copy_value(target_path, "visible copy", original, value)
                    elif original != value:
                        fail(target_path, f"number, price or link text changed: {original!r}")
            else:
                lines = [str(i) for i, line in enumerate(target_source.splitlines(), 1) if self.todo in line]
                if lines:
                    fail(target_path, f"{target_source.count(self.todo)} {self.todo} markers on lines {', '.join(lines)}")
                # Whole blocks catch sentences split by <strong>, links, entities or newlines.
                visible = normal(bodies[0].text(omit_todos=True, todo=self.todo)) if len(bodies) == 1 else ""
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
                                and sentence not in self.words.SENTENCE_EXCEPTIONS):
                            sentences.add(sentence)
                for sentence in sorted(sentences):
                    if re.search(r"(?<!\w)" + re.escape(sentence) + r"(?!\w)", visible):
                        fail(target_path, f"English sentence remains in visible text: {sentence!r}")

        sitemap = read("sitemap.xml")
        if sitemap is not None:
            try:
                tree = ET.fromstring(sitemap)
                for _, localized in self.PAGES:
                    matches = [u for u in tree.findall("s:url", NS) if u.findtext("s:loc", namespaces=NS) == ORIGIN + localized]
                    # A noindex page stays out of the sitemap. An indexable page has exactly one entry.
                    page_html = read(localized.strip("/") + "/index.html") or ""
                    hidden = bool(re.search(r'<meta name="robots" content="[^"]*noindex', page_html))
                    if hidden:
                        if matches:
                            fail("sitemap.xml", f"{ORIGIN + localized} is noindex and must not be in the sitemap")
                        continue
                    if len(matches) != 1:
                        fail("sitemap.xml", f"expected one entry for {ORIGIN + localized}")
                        continue
                    lastmod = matches[0].findtext("s:lastmod", namespaces=NS) or ""
                    try:
                        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod):
                            raise ValueError
                        date.fromisoformat(lastmod)
                    except ValueError:
                        fail("sitemap.xml", f"{localized} needs a valid YYYY-MM-DD lastmod")
            except ET.ParseError as error:
                fail("sitemap.xml", f"invalid XML: {error}")
        return problems

    def selftest(self) -> int:
        """Mutation tests use only temporary copies; the working pages never change."""
        baseline = self.check(self.ROOT, True)
        if baseline:
            print("FAIL: selftest needs a valid scaffold first:")
            print("\n".join(baseline))
            return 1
        files = [url.lstrip("/") + "index.html" for pair in self.PAGES for url in pair] + ["sitemap.xml"]
        originals = {name: (self.ROOT / name).read_text(encoding="utf-8") for name in files}
        # Read the current sitemap date instead of fixing it in a fixture.
        found = re.search(re.escape("<loc>" + ORIGIN + self.ROUTES["/"] + "</loc><lastmod>") + r"(\d{4}-\d{2}-\d{2})", originals["sitemap.xml"])
        if not found:
            print(f"FAIL: selftest cannot find the {self.ROUTES['/']} lastmod in sitemap.xml")
            return 1
        lastmod = found.group(1)
        # the Windows version moves with every Windows release, so the fixture reads it from the page (it named 1.0.1853)
        win = re.search(self.words.GATE_WINDOWS_VERSION_PATTERN, originals[self.download_file])
        if not win:
            print(f"FAIL: selftest cannot find the Windows version on {self.ROUTES['/download/']}")
            return 1
        win_version = win.group(1)
        # the English home description changes with the copy (9 Nov: "Crisp enhancer restores ..."), so the fixture reads its opening
        en_desc = re.search(r'<meta name="description" content="([^"]{0,22})', originals["index.html"])
        if not en_desc:
            print("FAIL: selftest cannot find the English home description")
            return 1
        en_desc = en_desc.group(1)
        cases = self.words.gate_cases(self.generator, ORIGIN, lastmod, win_version, en_desc)
        with tempfile.TemporaryDirectory(prefix=f"crisp-{self.lang}-gate-") as folder:
            root = Path(folder)
            for name, source in originals.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")

            # Keep mirror-only checks alive with a marked copy of today's English homepage.
            mirror_labels = {
                "changed Plausible", "missing title marker", "missing description marker",
                "changed JSON price", "unmarked JSON prose", "invalid JSON",
                "changed schema type", "wrong schema language", "sentence across inline tags",
                "unmarked homepage price", "unmarked homepage code",
            }

            def run_cases(selected, sources):
                for label, name, before, after, expected, scaffold in selected:
                    path = root / name
                    if before is not None:
                        if before not in sources[name]:
                            print(f"FAIL: selftest fixture no longer exists: {label}")
                            return False
                        path.write_text(sources[name].replace(before, after, 1), encoding="utf-8")
                    else:
                        path.unlink()
                    errors = self.check(root, scaffold)
                    path.write_text(sources[name], encoding="utf-8")
                    if not any(expected in error for error in errors):
                        print(f"FAIL: selftest missed {label}: {errors}")
                        return False
                return True

            if not run_cases([case for case in cases if case[0] not in mirror_labels], originals):
                return 1

            # The written-page opt-out must leave these four checks active. Require
            # every diagnostic, rather than accepting a failure for only one fault.
            name = self.home_file
            source = originals[name]
            assert f'name="{self.lang}-written"' in source
            damaged = source.replace(self.CONTACT, '', 1).replace(f'lang="{self.lang}"', 'lang="en"', 1)
            damaged = damaged.replace(f'hreflang="{self.lang}"', 'hreflang="wrong"', 1)
            damaged = damaged.replace('</body>', f'<p>{self.todo}: test marker</p></body>', 1)
            (root / name).write_text(damaged, encoding="utf-8")
            errors = self.check(root, False)
            (root / name).write_text(source, encoding="utf-8")
            for expected in ("exact contact", f"{self.todo} markers", f"lang={self.lang}", "hreflang"):
                if not any(error.startswith(name + ":") and expected in error for error in errors):
                    print(f"FAIL: {self.lang}-written selftest missed {expected}: {errors}")
                    return 1

            mirror_originals = dict(originals)
            source = self.generator.PBOX.sub('', originals["index.html"])
            mirror_originals["index.html"] = source
            doc = Document(source)
            edits = []

            def mirror_json(value, key=""):
                if isinstance(value, dict):
                    return {k: mirror_json(v, k) for k, v in value.items()}
                if isinstance(value, list):
                    return [mirror_json(v, key) for v in value]
                if isinstance(value, str):
                    if key == "inLanguage":
                        return self.lang
                    if schema_copy(key, value):
                        return self.todo + ": " + value
                    return self.local_link(value, "/")
                return value

            def mirror(node):
                if node.tag == "script" and node.attrs.get("type") == "application/ld+json":
                    edits.append((node.open_end, node.close_start,
                                  json.dumps(mirror_json(json.loads(source[node.open_end:node.close_start])), indent=2)))
                    return
                if node.tag in {"script", "style", "template"}:
                    return
                if node.tag == "#text" and needs_copy(node.raw):
                    edits.append((node.start, node.end, self.todo + ": " + node.raw))
                elif node.tag != "#text" and node.tag != "#document":
                    attrs = dict(node.attrs)
                    for key, value in attrs.items():
                        meta = attrs.get("name", attrs.get("property"))
                        if key in COPY_ATTRS and value and needs_copy(value) or node.tag == "meta" and key == "content" and meta in META_COPY:
                            attrs[key] = self.todo + ": " + value
                        elif node.tag == "html" and key == "lang":
                            attrs[key] = self.lang
                        elif node.tag == "link" and attrs.get("rel") == "canonical" and key == "href":
                            attrs[key] = ORIGIN + self.ROUTES["/"]
                        elif node.tag == "link" and "hreflang" in attrs:
                            continue
                        elif key == "href" or node.tag == "meta" and meta == "og:url" and key == "content":
                            attrs[key] = self.local_link(value, "/")
                    if attrs != node.attrs:
                        tag = "<" + node.tag + "".join(
                            " " + key + (f'="{escape(value, quote=True)}"' if value is not None else "")
                            for key, value in attrs.items()) + ">"
                        edits.append((node.start, node.open_end, tag))
                for child in node.children:
                    mirror(child)

            mirror(doc.root)
            for start, end, replacement in sorted(edits, reverse=True):
                source = source[:start] + replacement + source[end:]
            source = source.replace('<body>', '<body>\n<p class="app-language">' + self.NOTICE + '</p>', 1)
            source = source.replace('<footer>', self.CONTACT + '\n<footer>', 1)
            mirror_originals[self.home_file] = source
            for name in ("index.html", self.home_file):
                (root / name).write_text(mirror_originals[name], encoding="utf-8")
            errors = self.check(root, True)
            if errors:
                print(f"FAIL: selftest needs a valid synthetic mirror first: {errors}")
                return 1
            if not run_cases([case for case in cases if case[0] in mirror_labels], mirror_originals):
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
                return dummy(value) if isinstance(value, str) and value.startswith(self.todo + ":") else value

            for _, localized in self.PAGES:
                name = localized.lstrip("/") + "index.html"
                source = mirror_originals[name]
                doc = Document(source)
                edits = []

                def substitute(node):
                    if node.tag == "script" and node.attrs.get("type") == "application/ld+json":
                        edits.append((node.open_end, node.close_start,
                                      json.dumps(dummy_json(json.loads(source[node.open_end:node.close_start])))))
                        return
                    if node.tag in {"script", "style"}:
                        return
                    if node.tag == "#text" and self.todo + ":" in node.raw:
                        edits.append((node.start, node.end, dummy(normal(node.raw))))
                    elif node.tag != "#text":
                        tag = source[node.start:node.open_end]
                        for key, value in node.attrs.items():
                            if value and value.startswith(self.todo + ":"):
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
            errors = self.check(root, False)
            if errors:
                print(f"FAIL: final mode rejected marker-free synthetic copy: {errors}")
                return 1
            for _, localized in self.PAGES:
                name = localized.lstrip("/") + "index.html"
                (root / name).write_text(mirror_originals[name].replace(self.todo + ": ", ""), encoding="utf-8")
            errors = self.check(root, False)
            if not any("English sentence remains" in error for error in errors) or any(f"{self.todo} markers" in error for error in errors):
                print(f"FAIL: final mode must reject English even after all markers are removed: {errors}")
                return 1
        self.generator_selftest()
        self.language_selftest()
        print(f"OK: {len(cases) + 3} {self.words.LANGUAGE_NAME} gate tests and generator regression checks passed.")
        return 0

    def generator_selftest(self) -> None:
        """Exercise changed sources and check/write mode, without touching the site."""
        f = self.generator.llms_txt.facts()
        changed = dict(f, price=Decimal("41"), now=Decimal("20.50"), code="NEXTCRISP",
                       ends="2026-12-16T07:59:59Z", os="macOS 15.0 or later", cap=22, refund_days=40)
        current_win = self.generator.llms_txt.windows()
        win = {"version": "2.3.4567", "url": current_win["url"].replace(current_win["version"], "2.3.4567")}
        with patch.object(self.generator.llms_txt, "facts", return_value=changed), patch.object(self.generator.llms_txt, "windows", return_value=win):
            page = self.generator.page(self.generator.download_slug, changed)
            for value in (self.words.money(changed["price"]), self.words.money(changed["now"]), "NEXTCRISP", self.generator.last_day(changed["ends"]), changed["ends"], win["version"], win["url"], self.words.fact(changed["os"])):
                assert value in page, f"{self.words.LANGUAGE_NAME} page did not update {value}"
            assert 'id="macos-speed"' not in page, "speed section must follow the English macOS floor"
            assert self.words.BOX["fine"].format(**self.generator.values(changed)) in page
            for name in self.generator.OTHER_PAGES:
                before = (self.ROOT / name).read_text()
                after = self.generator.refresh_boxes(before, name, changed)
                assert self.generator.MARKED_BOX.sub('', before) == self.generator.MARKED_BOX.sub('', after), "box refresh changed body copy"
                assert self.generator.refresh_boxes(after, name, changed) == after, "box refresh is not idempotent"
        with patch.object(self.generator.llms_txt, "windows", return_value=None):
            assert 'class="win-link"' not in self.generator.box(self.lang + "-test", f=f)
        instalments = dict(f, price=Decimal("80"), now=Decimal("60"), bnpl=True)
        assert f'{self.words.money(Decimal(60))}</span> {self.words.BOX["once"]}' in self.generator.box(self.lang + "-test", f=instalments)   # the launch amount leads
        assert self.words.SPLIT.format(amount=self.words.money(Decimal(15))) in self.generator.box(self.lang + "-test", f=instalments)
        live = self.generator.llms_txt.founding_live
        with patch.object(self.generator.llms_txt, "founding_live", side_effect=lambda fact: live(fact, datetime(2030, 1, 1, tzinfo=timezone.utc))):
            assert 'class="pbox-found"' not in self.generator.page(self.generator.download_slug, f)
            assert self.words.SPLIT.format(amount=self.words.money(Decimal(20))) in self.generator.box(self.lang + "-test", f=instalments)
            assert f'<span class="pbox-amt">{self.words.money(f["price"])}</span>' in self.generator.box(self.lang + "-test", f=f)
            assert self.words.PRICE_ONCE.format(price=self.words.money(self.generator.landing.BUNDLE_USD)) in self.generator.bundle(), "expired bundle offer remains"
            expired = {"price": f["price"], "ends": f["ends"]}
            expected = self.words.PRICE_ONCE.format(price=self.words.money(f["price"]))
            assert self.generator.price_copy(expired) == expected
            assert self.generator.price_short(expired) == expected
        assert self.generator.last_day("2026-12-01T08:00:00Z") == self.words.DATE_FORMAT.format(day=30, month=self.words.MONTHS[10])
        assert self.generator.EXPIRY_SCRIPT in self.generator.thankyou_xsell.block()
        with tempfile.TemporaryDirectory(prefix=f"crisp-{self.lang}-generator-") as folder:
            root = Path(folder)
            facts = root / "dodo-facts.json"
            with patch.object(self.generator.thankyou_xsell, "FACTS", facts):
                try:
                    self.generator.bundle()
                except SystemExit as error:
                    assert "required regular prices file is missing" in str(error)
                else:
                    raise AssertionError("missing regular prices did not fail")
                facts.write_text(json.dumps({"products": {name: {"name": name, "price_cents": cents}
                                                        for name, cents in (("Crisp", 3100), ("Docket SEO", 6100), ("Outlier", 5100))}}))
                assert self.words.money(Decimal(143)) in self.generator.bundle(), "bundle's separate total was not read from Dodo"
            for name in self.generator.OTHER_PAGES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text((self.ROOT / name).read_text())
            with patch.object(self.generator, "SITE", root), redirect_stdout(io.StringIO()):
                assert self.generator.write(check=True) == 1, f"missing {self.words.LANGUAGE_NAME} doors passed check"
                assert self.generator.write() == 0
                assert self.generator.write(check=True) == 0
                page = root / self.generator.FULL_PAGES[0]
                page.write_text(page.read_text().replace(self.words.money(f["price"]), self.words.money(f["price"] - 1), 1))
                assert self.generator.write(check=True) == 1, f"stale {self.words.LANGUAGE_NAME} price passed check"


    def language_selftest(self) -> None:
        """Test a second locale entirely in a temporary tree and an in-memory module."""
        import lang_pages
        import sitewide_chrome as chrome

        code = "zz-test"
        routes = {source: target.replace(self.ROUTES["/"], f"/{code}/", 1)
                  for source, target in self.PAGES}
        routes["/download/"] = f"/{code}/get-test/"
        routes["/pricing/"] = f"/{code}/cost-test/"

        def rebase(text):
            for source, target in sorted(self.PAGES, key=lambda pair: len(pair[1]), reverse=True):
                text = text.replace(target, routes[source])
            text = text.replace(f'lang="{self.lang}"', f'lang="{code}"')
            text = text.replace(f'name="{self.lang}-written"', f'name="{code}-written"')
            text = text.replace(f"{self.lang}-box:", f"{code}-box:")
            text = text.replace(self.todo, "TODO-" + code.upper())
            return re.sub(r'("inLanguage"\s*:\s*")' + re.escape(self.lang) + '"',
                          lambda m: m.group(1) + code + '"', text)

        def locale_data(value):
            if isinstance(value, str):
                return rebase(value)
            if isinstance(value, dict):
                return {key: locale_data(item) for key, item in value.items()}
            if isinstance(value, tuple):
                return tuple(locale_data(item) for item in value)
            return value

        words = ModuleType(f"strings_{code}")
        for key, value in vars(self.words).items():
            if key.isupper():
                setattr(words, key, locale_data(value))
        words.ROUTES = tuple(routes.items())
        words.LANGUAGE_NAME = "Test"
        words.APP_LANGUAGE = "Test app-language notice."
        words.CONTACT_CLASS = "test-contact"
        words.CONTACT = '<section class="test-contact"><h2>Test contact</h2></section>'
        words.FOOTER = dict(words.FOOTER, made_by="Test maker")
        words.MONTHS = tuple(f"month-{month}" for month in range(1, 13))
        words.SHORT_MONTHS = words.MONTHS
        words.DATE_FORMAT = "{month}/{day}"
        words.SHORT_DATE_FORMAT = "{month}:{day}"
        words.money = lambda amount: f"{amount:.2f} TEST"
        words.fact = lambda text: text.replace(" or later", " test floor")
        words.GENERATOR_COMMENT = "<!-- Generated by _tools/lang_pages.py. -->"
        facts = self.generator.llms_txt.facts()
        original_page = self.generator.page(self.generator.download_slug, facts)

        with tempfile.TemporaryDirectory(prefix="crisp-language-") as folder:
            root = Path(folder)
            tools = root / "_tools"
            tools.mkdir()
            # Only a discovery marker is needed. The module itself stays in memory.
            (tools / f"strings_{code}.py").write_text("# Temporary selftest fixture.\n")
            for english, target in self.PAGES:
                for old, new in ((english, english), (target, routes[english])):
                    source = (self.ROOT / old.lstrip("/") / "index.html").read_text(encoding="utf-8")
                    path = root / new.lstrip("/") / "index.html"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    source = rebase(source).replace(rebase(self.CONTACT), words.CONTACT)
                    source = source.replace(self.words.APP_LANGUAGE, words.APP_LANGUAGE)
                    path.write_text(source, encoding="utf-8")
            (root / "sitemap.xml").write_text(rebase((self.ROOT / "sitemap.xml").read_text()), encoding="utf-8")
            with patch.dict(sys.modules, {words.__name__: words}), \
                    patch.object(lang_pages, "__file__", str(tools / "lang_pages.py")):
                gate = LanguageGate(code, root)
                generator = gate.generator
                with redirect_stdout(io.StringIO()):
                    assert generator.write() == 0
                    assert generator.write(check=True) == 0
                source = (root / gate.download_file).read_text(encoding="utf-8")
                assert f'lang="{code}"' in source and f'hreflang="{code}"' in source
                assert f'{ORIGIN}/{code}/get-test/' in source
                assert words.APP_LANGUAGE in source and words.CONTACT in source
                assert words.money(facts["now"]) in source
                assert generator.last_day("2026-12-01T08:00:00Z") == "month-11/30"
                assert generator.f_ends_short("2026-12-01T08:00:00Z") == "month-11:30"
                problems = gate.check(root, False)
                assert not problems, f"second locale failed final checks: {problems}"
                path = root / gate.home_file
                home = path.read_text(encoding="utf-8")
                path.write_text(home.replace(words.APP_LANGUAGE, "Wrong notice", 1), encoding="utf-8")
                assert any("required sentence" in error for error in gate.check(root, True))
                english = Document((root / "index.html").read_text(encoding="utf-8"))
                sentence = next(normal(node.text()) for node in english.elements("p")
                                if re.search(r"[.!?]$", normal(node.text())) and needs_copy(node.text()))
                path.write_text(home.replace("</body>", f"<p>{escape(sentence)}</p></body>", 1), encoding="utf-8")
                assert any("English sentence remains" in error for error in gate.check(root, False))
                path.write_text(home, encoding="utf-8")
                with patch.object(chrome, "SITE", root), \
                        patch.object(chrome, "__file__", str(tools / "sitewide_chrome.py")):
                    path = root / gate.download_file
                    assert chrome.language(path) == code
                    assert "Test maker" in chrome.kco_for(path)
                    assert chrome.kco_for(root / "unknown/index.html") == chrome.KCO
                    assert chrome.language(root.parent / gate.download_file) is None
                    assert not chrome.wants_founding(path, source)
                    assert chrome.wants_founding(path, '<div data-founding></div>')
                    assert not chrome.wants_row_headers(path)
                    assert not chrome.apply(path), "chrome rewrote the second locale"
        assert self.generator.page(self.generator.download_slug, facts) == original_page, "locale state leaked"


def main(argv: list[str] | None = None, *, lang: str | None = None,
         selftest: Callable[[], int] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    if lang is None:
        parser.add_argument("lang")
    parser.add_argument("--scaffold", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    try:
        gate = LanguageGate(lang if lang is not None else args.lang)
    except ValueError as error:
        parser.error(str(error))
    if args.selftest:
        return (selftest or gate.selftest)()
    problems = gate.check(gate.ROOT, args.scaffold)
    if problems:
        print(f"FAIL: {len(problems)} {gate.words.LANGUAGE_NAME} page problem(s):")
        for problem in problems:
            print("  " + problem)
        return 1
    print(f"OK: all {gate.words.PAGE_COUNT} {gate.words.LANGUAGE_NAME} pages pass {'scaffold' if args.scaffold else 'final'} checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
