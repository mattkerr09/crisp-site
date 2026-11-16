#!/usr/bin/env python3
"""Check the optional review ask, preserve the base page, and run pre-push gates."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

from gate_price_words import Document, normal

SITE = Path(__file__).resolve().parent.parent
PAGE = SITE / "thank-you" / "index.html"
# HEAD~0 when this job started. Keep the comparison fixed after the job is committed.
BASE_COMMIT = "c28fa1cc474ec8ac5fba954b2a192c588f9b8b38"
DESTINATION = "https://alternativeto.net/software/crisp-video/about/"
ASK = "Used Crisp? Add an honest review on AlternativeTo."
INSERTION = (
    '\n  <p class="lede">Used Crisp? <a href="' + DESTINATION
    + '" rel="noreferrer">Add an honest review on AlternativeTo.</a></p>\n'
).encode("utf-8")
ANCHOR = b'    <a href="/" style="margin-left:1.1rem">Back to the site</a></p>\n'
REWARD = re.compile(r"\b(?:free|discount|gift|coupon|5-star|five\s+star)\b|%\s*off\b", re.I)


def check_ask(source: str) -> None:
    document = Document(source)
    links = [node for node in document.root.walk() if node.tag == "a"
             and ("alternativeto" in (node.attrs.get("href") or "").lower()
                  or "alternativeto" in node.text().lower())]
    assert len(links) == 1, "expected exactly one AlternativeTo link"
    link = links[0]
    destination = link.attrs.get("href") or ""
    assert not urlsplit(destination).query and "?" not in destination, "review URL has a query string"
    assert destination == DESTINATION, "review URL differs from the listing"
    assert link.attrs == {"href": DESTINATION, "rel": "noreferrer"}, "unexpected review link attributes"
    paragraphs = [node for node in document.root.walk() if node.tag == "p"
                  and any(child is link for child in node.walk())]
    assert len(paragraphs) == 1, "review link must be in one paragraph"
    paragraph = paragraphs[0]
    text = normal(paragraph.text())
    assert not REWARD.search(text), "reward words inside the review ask"
    assert text == ASK, "review ask wording changed"
    assert paragraph.attrs == {"class": "lede"}, "review ask must reuse the existing lede class"
    assert source.count(INSERTION.decode("utf-8")) == 1, "expected one review paragraph"
    position = source.index(INSERTION.decode("utf-8"))
    assert source.index('href="mailto:support@crispvideo.app"') < position
    assert source.index("<!-- xsell:end -->") < position
    assert source.index(ANCHOR.decode("utf-8")) < position < source.index("</section>")


def check_unchanged(source: bytes, base: bytes) -> None:
    assert b"alternativeto" not in base.lower(), "review link already exists on the base"
    assert ASK.encode("utf-8") not in base, "review ask already exists on the base"
    assert base.count(ANCHOR) == 1, "base download paragraph moved"
    expected = base.replace(ANCHOR, ANCHOR + INSERTION, 1)
    assert source == expected, "thank-you page differs from the base beyond the inserted lines"


def rejected(label: str, check, diagnostic: str) -> None:
    try:
        check()
    except AssertionError as error:
        assert diagnostic in str(error), f"{label} failed for the wrong reason: {error}"
    else:
        raise AssertionError(f"{label} was accepted")
    print(f"PASS: {label} rejected", flush=True)


def controls(source: str, base: bytes) -> None:
    rejected("base without an ask", lambda: check_ask(base.decode("utf-8")),
             "expected exactly one AlternativeTo link")
    for word in ("free", "discount", "gift", "coupon", "% off", "5-star", "five star"):
        planted = source.replace("Used Crisp?", f"Used Crisp? {word}", 1)
        assert planted != source, "reward control did not change the page"
        rejected(f"reward control {word!r}", lambda: check_ask(planted), "reward words")
    planted = source.replace(DESTINATION, DESTINATION + "?payment_id=planted", 1)
    assert planted != source, "query control did not change the page"
    rejected("query-string control", lambda: check_ask(planted), "query string")
    planted = source.replace("Your key is on its way.", "Changed headline.", 1).encode("utf-8")
    assert planted != source.encode("utf-8"), "preservation control did not change the page"
    rejected("unrelated page edit", lambda: check_unchanged(planted, base), "beyond the inserted lines")


def check_other_pages() -> None:
    pages = sorted(path for path in SITE.rglob("*.html") if path != PAGE
                   and not {".git", "node_modules"}.intersection(path.relative_to(SITE).parts))
    assert pages, "no other HTML pages found"
    for path in pages:
        document = Document(path.read_text(encoding="utf-8"))
        assert ASK not in normal(document.root.text()), f"review ask also appears in {path.relative_to(SITE)}"
        assert not any(node.tag == "a" and (node.attrs.get("href") or "").startswith(DESTINATION)
                       for node in document.root.walk()), f"review listing linked in {path.relative_to(SITE)}"
    print(f"PASS: review ask absent from {len(pages)} other HTML pages", flush=True)


def main() -> int:
    source = PAGE.read_bytes()
    base = subprocess.run(["git", "show", f"{BASE_COMMIT}:thank-you/index.html"],
                          cwd=SITE, check=True, capture_output=True).stdout
    check_ask(source.decode("utf-8"))
    check_unchanged(source, base)
    print(f"PASS: one honest review ask and byte-identical existing content against {BASE_COMMIT}", flush=True)
    check_other_pages()
    controls(source.decode("utf-8"), base)

    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    # Empty push refs describe this site-only change. The job forbids forcing a live checkout check.
    environment.pop("CRISP_CHECK_TILL", None)
    print("Running sh .githooks/pre-push with empty push refs", flush=True)
    result = subprocess.run(["sh", ".githooks/pre-push"], cwd=SITE, input="", text=True, env=environment)
    print(f"pre-push exit code: {result.returncode}", flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
