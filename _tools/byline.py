#!/usr/bin/env python3
"""The byline: a named person under the H1, with the dates beside it, and the same person in the page's structured data.

WHY (CEO, 2026-11-02, from ~/ops/launch/WHAT-WORKS-2026-11-02.md). Across the company's 652 pages a named author byline
was on 53% of the pages that earn clicks and 20% of the ones that earn nothing, and 0% of Crisp's pages showed one: the
line under every H1 read "Crisp · built in Grand Rapids · published X · last updated Y". Crisp is made by one person,
so the line now says so: "By Matt Kerr, who makes Crisp in Grand Rapids · published X · last updated Y".

ONE COMPONENT, NOT HAND-TYPED COPIES. This tool writes the line and the author field together, so the person a reader
sees and the person the Article/HowTo/CollectionPage JSON-LD names cannot drift apart.

⚠️ THE LINE STAYS PLAIN TEXT UP TO "last updated". page_dates.py finds the date it keeps true with
r'<div class="updated">[^<]*?last updated ', and tests/test_the_byline_date_is_the_page_date.py uses the same pattern:
a link on the name (an <a> before the date) would hide the date from both, and the visible "last updated" would go
stale while every check stayed green. The link to /about/ lives in the JSON-LD author's "url" instead.

    python3 _tools/byline.py PATH [PATH ...]   # convert these pages (index.html files or their folders)
    python3 _tools/byline.py --check           # exit 1 if a "By Matt Kerr" page names anyone else in its JSON-LD
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
NAME = "Matt Kerr"
OLD = '<div class="updated">Crisp · built in Grand Rapids · '
NEW = f'<div class="updated">By {NAME}, who makes Crisp in Grand Rapids · '
#: the five how-tos whose line is the month dateline dateline.py keeps true ("Updated October 2026 · step-by-step"):
#: the name goes in front, and the "Updated <Month> <Year>" it maintains is left exactly as it is.
OLD_MONTH = '<div class="updated">Updated '
NEW_MONTH = NEW + 'Updated '
AUTHOR = {"@type": "Person", "name": NAME, "url": "https://crispvideo.app/about/"}
AUTHOR_JSON = json.dumps(AUTHOR, ensure_ascii=False, separators=(",", ":"))
TYPES = {"Article", "HowTo", "CollectionPage", "TechArticle", "BlogPosting"}
LD = re.compile(r'(<script[^>]+type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', re.S | re.I)
AUTHOR_FIELD = re.compile(r'"author"\s*:\s*\{[^{}]*\}')
CONTEXT_FIELD = re.compile(r'("@context"\s*:\s*"https://schema\.org"\s*,)')


def _types(block: dict) -> set:
    t = block.get("@type")
    return set(t) if isinstance(t, list) else {t}


def _fix_block(raw: str) -> str:
    """Point one JSON-LD block's author at the person, editing the text in place so nothing else in it moves."""
    try:
        data = json.loads(raw)
    except ValueError:
        return raw
    if not isinstance(data, dict) or not (_types(data) & TYPES):
        return raw
    if "author" in data:
        new = AUTHOR_FIELD.sub('"author":' + AUTHOR_JSON, raw, count=1)
    else:
        new = CONTEXT_FIELD.sub(lambda m: m.group(1) + '"author":' + AUTHOR_JSON + ",", raw, count=1)
    if json.loads(new).get("author") != AUTHOR:
        raise SystemExit(f"byline.py: could not set the author in a JSON-LD block: {raw[:120]!r}")
    return new


def convert(page: Path) -> bool:
    text = page.read_text(encoding="utf-8")
    if OLD not in text and NEW not in text and OLD_MONTH not in text:
        print(f"  SKIP {page.parent.relative_to(SITE)}: no standard byline under the H1")
        return False
    out = text.replace(OLD, NEW, 1) if OLD in text else text.replace(OLD_MONTH, NEW_MONTH, 1)
    out = LD.sub(lambda m: m.group(1) + _fix_block(m.group(2)) + m.group(3), out)
    if out != text:
        page.write_text(out, encoding="utf-8")
        return True
    return False


def problems(text: str) -> list[str]:
    if NEW not in text:
        return []
    out, named = [], 0
    for m in LD.finditer(text):
        try:
            data = json.loads(m.group(2))
        except ValueError:
            continue
        if isinstance(data, dict) and _types(data) & TYPES:
            named += 1
            if (data.get("author") or {}).get("name") != NAME:
                out.append(f"the byline says {NAME} but the {'/'.join(sorted(_types(data) & TYPES))} JSON-LD author is "
                           f"{data.get('author')!r}")
    if not named:
        out.append(f"the byline says {NAME} but no Article/HowTo/CollectionPage JSON-LD names an author")
    return out


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--check":
        bad, n = [], 0
        for page in sorted(SITE.rglob("index.html")):
            if "_tools" in page.parts:
                continue
            text = page.read_text(encoding="utf-8", errors="replace")
            n += NEW in text
            bad += [f"{page.parent.relative_to(SITE)}: {p}" for p in problems(text)]
        for b in bad:
            print("FAIL " + b)
        print(f"byline: {n} pages say 'By {NAME}'; {len(bad)} disagree with their JSON-LD author")
        return 1 if bad else 0
    changed = 0
    for a in args:
        p = (SITE / a) if not Path(a).is_absolute() else Path(a)
        p = p / "index.html" if p.is_dir() else p
        changed += convert(p)
    print(f"byline: {changed} of {len(args)} pages converted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
