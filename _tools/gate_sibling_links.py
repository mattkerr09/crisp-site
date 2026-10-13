#!/usr/bin/env python3
"""Fail on any link from a Crisp page to one of the sister sites, or on more than one link to the company.

WHY. CEO order, 2026-10-13 (Matthew: "fix bing ... make sure we dont make the same mistakes that made us stop getting sales").
outlier.host's Bing impressions went from 45-89 a day to 8 on 2026-09-15 and then to 0, within a day of a block of links to every
sibling domain going onto 171 of its pages. Bing reads sitewide links between commonly owned sites as a link scheme, and Bing feeds
ChatGPT search, where the early buyers came from. crispvideo.app's footer used to carry six such links on 130 of its 131 pages.

THE RULE. No page links to outlier.host, docketseo.app, adplaybook.app, bookbreaker.bet, builtbykerr.com or matthewkerr.dev, except
/about/ (where naming the sister apps once is fine). A page carries at most ONE link to the company, https://kerrandcompanyholdings.com/
("Made by Kerr & Company", the footer). The sister sites may be NAMED in plain text anywhere: only a URL counts here, in an href, in
structured data, in llms.txt or in a sitemap, because a crawler follows all of those.

    python3 _tools/gate_sibling_links.py            # exit 1 and list every violation

Wired into .githooks/pre-push and into tests/test_no_page_links_to_a_sibling_domain_outside_about.py (the build's suite).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]

SIBLINGS = ("outlier.host", "docketseo.app", "adplaybook.app", "bookbreaker.bet", "builtbykerr.com", "matthewkerr.dev")
COMPANY = "kerrandcompanyholdings.com"
#: Directories (first path segment) where naming the sister apps is allowed.
ALLOWED_DIRS = {"about"}
#: Text a crawler reads. Media, fonts and archives hold no links we can check here.
TEXT_SUFFIXES = {".html", ".htm", ".txt", ".xml", ".json", ".js", ".css", ".md", ".webmanifest"}
SKIP_PARTS = {".git", "_tools", "__pycache__", "node_modules"}

#: A URL form only: https://, http:// or protocol-relative //, with an optional www., then the domain as a whole label.
def _url(domains) -> "re.Pattern[str]":
    alt = "|".join(re.escape(d) for d in domains)
    return re.compile(rf"(?:https?:)?//(?:www\.)?(?:{alt})(?![A-Za-z0-9-])", re.I)


SIBLING_URL = _url(SIBLINGS)
COMPANY_URL = _url([COMPANY])


def _files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and not (SKIP_PARTS & set(p.relative_to(root).parts)):
            yield p


def violations(root: Path = SITE) -> list[str]:
    """Every breach of the rule under `root`, as 'path: what', most serious first. Empty means clean."""
    out: list[str] = []
    for p in _files(root):
        rel = p.relative_to(root)
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        if rel.parts[0] not in ALLOWED_DIRS:
            for m in SIBLING_URL.finditer(text):
                ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 30):m.end() + 20])
                out.append(f"{rel}: links to a sister site ({m.group(0)}): ...{ctx}...")
        n = len(COMPANY_URL.findall(text))
        if n > 1 and rel.parts[0] not in ALLOWED_DIRS:
            out.append(f"{rel}: {n} links to the company (at most one)")
    return out


def pages_scanned(root: Path = SITE) -> int:
    return sum(1 for p in _files(root) if p.suffix.lower() == ".html")


def main() -> int:
    bad = violations()
    n = pages_scanned()
    if n < 100:                                  # a gate that cannot see its subject must not report success
        print(f"gate_sibling_links: BLOCKED, only {n} pages found under {SITE}")
        return 1
    if bad:
        print(f"gate_sibling_links: {len(bad)} breach(es) in {n} pages (no link to a sister site outside /about/, one company link at most):")
        for b in bad[:30]:
            print("  " + b)
        if len(bad) > 30:
            print(f"  ... and {len(bad) - 30} more")
        return 1
    print(f"OK: no link to a sister site in {n} pages (and at most one company link per file).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
