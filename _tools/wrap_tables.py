#!/usr/bin/env python3
"""Every table needs a scroll box, or its right-hand columns are unreachable on a phone.

MEASURED, not reasoned. style.css sets `table{min-width:540px}` and `body{overflow-x:hidden}`,
and `.wrap` — the ordinary page container — computes to `overflow-x: visible`. So on a phone a
bare table overflows its container by about 197px at a 343px content width, and because nothing
in the chain scrolls, those columns are clipped and cannot be reached at all. Confirmed in a real
browser against the live page: wrapOverflowX "visible", tableOverflowsWrapBy 197, reachable false.

The site already had the fix and 26 tables never got it, including the home page. `.cmp-wrap`
exists precisely for this and style.css says so in its own comment: "a table can't be its own
overflow container, and without one a min-width table pushes the whole page sideways on a phone."

Idempotent: a table already inside a .cmp-wrap is left alone.

    python3 _tools/wrap_tables.py           # wrap them
    python3 _tools/wrap_tables.py --check   # exit 1 if any table is unwrapped
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
OPEN = re.compile(r"<table[^>]*>")
LOOKBACK = 260


def unwrapped(text: str) -> list[int]:
    """Start offsets of tables that are not already inside a .cmp-wrap."""
    return [m.start() for m in OPEN.finditer(text)
            if "cmp-wrap" not in text[max(0, m.start() - LOOKBACK):m.start()]]


def wrap(text: str) -> tuple[str, int]:
    n = 0
    while True:
        spots = unwrapped(text)
        if not spots:
            return text, n
        i = spots[0]
        end = text.find("</table>", i)
        if end < 0:
            raise SystemExit(f"unclosed <table> at offset {i}")
        end += len("</table>")
        text = text[:i] + '<div class="cmp-wrap">' + text[i:end] + "</div>" + text[end:]
        n += 1


def main() -> int:
    check = "--check" in sys.argv
    touched, total = [], 0
    for page in sorted(SITE.rglob("index.html")):
        if "_tools" in page.parts:
            continue
        text = page.read_text()
        bare = len(unwrapped(text))
        total += len(OPEN.findall(text))
        if not bare:
            continue
        touched.append(f"{page.parent.relative_to(SITE)} ({bare})")
        if not check:
            out, _ = wrap(text)
            page.write_text(out)
    if check:
        if touched:
            print(f"{len(touched)} pages have a table with no scroll box: {', '.join(touched[:12])}")
            return 1
        print(f"every one of the {total} tables on the site is inside a scroll box")
        return 0
    print(f"{len(touched)} pages fixed, of {total} tables site-wide")
    for t in touched[:12]:
        print("  " + t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
