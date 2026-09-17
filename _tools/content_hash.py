#!/usr/bin/env python3
"""The hash of what a READER sees, so a template change cannot move a page's date.

WHY. On 2026-09-15 commit 0fdc72e ("The Outlier anatomy, applied mechanically to 111 pages")
touched 110 index.html files. `page_dates.content_changed` counted any diff line that was not a
date line as a content change, so all 110 lastmods moved to 09-15 — and IndexNow, correctly,
resent 120 URLs the next day. The live sitemap still shows 110 of 122 entries sharing one date,
which tells a crawler the site is generated rather than maintained.

Reading that commit's own diff shows what actually moved on most of those pages:

  * `datePublished` / `dateModified` added to the schema        <- a date, by definition
  * a `BreadcrumbList` JSON-LD block                            <- navigation, in schema form
  * `<div class="updated">… published … · last updated …</div>` <- the byline, a date line
  * a `<div class="quick">` wrapper promoting the existing lede <- REAL content, on 76 pages

So the honest answer was never 110. It was the pages whose article text changed.

WHAT COUNTS AS CONTENT HERE. Every page on this site has the same three landmarks — `<nav>`,
`<article>`, `<footer>` — so the split is structural rather than a list of class names that would
rot:

  INCLUDED   <title>, the `<article>` body, and JSON-LD that describes the PAGE
  EXCLUDED   <nav>, <footer>, everything else outside <article>, analytics/pixel scripts,
             BreadcrumbList blocks, the `<div class="updated">` byline, and every
             datePublished/dateModified value wherever it appears

⚠️ THE DATE FIELDS MUST BE EXCLUDED OR THIS FEEDS ITSELF. Writing a date is a commit; if the date
were part of the hash, tomorrow's run would see yesterday's date-write as a content change and
walk the value forward forever with nothing ever being edited. `page_dates.py`'s docstring
records that exact loop happening twice already. This is the same rule, applied to a hash instead
of to diff lines.

⚠️ AND THE BYLINE IS INSIDE `<article>`, not in the chrome — it sits directly under the `<h1>`.
Taking "everything in the article" without removing it would reintroduce the loop through the
one element that looks most like content.
"""
from __future__ import annotations

import hashlib
import re

# The byline directly under <h1>: "Crisp · built in Grand Rapids · published X · last updated Y".
BYLINE = re.compile(r'<div class="updated">.*?</div>', re.S | re.I)
# Any JSON-LD block. Kept unless it is a BreadcrumbList, which restates the nav.
LDJSON = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
# Date values, wherever they appear and however they are spaced.
DATEFIELD = re.compile(r'"date(?:Modified|Published)"\s*:\s*"[^"]*"', re.I)
ARTICLE = re.compile(r'<article\b[^>]*>(.*?)</article>', re.S | re.I)
TITLE = re.compile(r'<title\b[^>]*>(.*?)</title>', re.S | re.I)
TAGS = re.compile(r'<[^>]+>')


def content_of(html: str) -> str:
    """The reader-visible substance of a page, normalised. Chrome removed, dates removed."""
    parts: list[str] = []

    m = TITLE.search(html)
    if m:
        parts.append(TAGS.sub(" ", m.group(1)))

    for block in LDJSON.findall(html):
        if '"BreadcrumbList"' in block or "'BreadcrumbList'" in block:
            continue                      # navigation restated as schema; not page content
        parts.append(DATEFIELD.sub("", block))

    body = ARTICLE.search(html)
    if body:
        text = BYLINE.sub(" ", body.group(1))     # the byline is INSIDE the article
        parts.append(TAGS.sub(" ", text))

    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def hash_of(html: str) -> str:
    return hashlib.sha256(content_of(html).encode("utf-8")).hexdigest()[:16]
