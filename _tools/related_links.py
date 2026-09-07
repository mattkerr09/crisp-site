#!/usr/bin/env python3
"""Give every learn article links to its neighbours, so no page is reachable only from the hub.

WHY. Before this, one of the twenty learn articles carried a Related block. The rest linked
onward only where the prose happened to mention another page, so most were reachable from the
/learn/ hub and nowhere else. A page with one route in is a page a crawler reaches last and a
reader leaves from.

HOW, and why it is not hand-picked. Each article links to the three that follow it in the
section's own alphabetical order, wrapping at the end, never itself. That is the CEO's
`neighbours()` pattern from ~/ops/UPGRADES.md, and the reason it is deterministic rather than
curated is maintenance: a hand-picked list is correct on the day it is written and silently
wrong the moment an article is added or renamed. This regenerates, so it is never stale, and
adding an article automatically pulls it into three other pages' blocks.

Idempotent: an existing Related block is replaced, not appended, so running twice leaves every
file byte-identical.

    python3 _tools/related_links.py           # write
    python3 _tools/related_links.py --check   # exit 1 if any page's block is stale
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
#: Every section whose pages should link to their neighbours. Each links WITHIN itself: a
#: comparison page's useful neighbour is another comparison, not a how-to.
SECTIONS = ("learn", "vs", "best", "how-to", "for")
N = 3
#: Preferred insertion point — just above the download CTA, so the call to action stays last.
CTA = '  <p><a class="btn" href="https://crispvideo.app/#download">Download Crisp for Mac</a>'
#: Fallback, because the CTA is NOT universal: it is on all 20 /learn/ pages but only 13 of 24
#: /vs/, 10 of 46 /how-to/ and none of /best/. `</div></article>` closes the article on all 108
#: pages in these sections, exactly once each — checked, not assumed.
END = "</div></article>"
# ⚠️ THE BLOCK OWNS ITS OWN TRAILING BLANK LINE, and the inserter adds nothing around it.
# My first version stripped "\n...  </ul>\n" and re-inserted with an extra "\n", so every
# run added one newline to all twenty files and --check reported all twenty stale forever.
# The strip and the insert have to be exact inverses or "idempotent" is just a word in a
# docstring. --check is what caught it.
BLOCK = re.compile(r"  <h2>Related</h2>\n  <ul>\n(?:    <li>.*?</li>\n)+  </ul>\n\n")


def articles(section: Path) -> list[tuple[str, str, Path]]:
    """(slug, title, path) for every article in the section, in a stable order."""
    out = []
    for d in sorted(p for p in section.iterdir() if p.is_dir()):
        page = d / "index.html"
        if not page.is_file():
            continue
        m = re.search(r"<h1>(.*?)</h1>", page.read_text(), re.S)
        if not m:
            continue
        out.append((d.name, re.sub(r"<[^>]+>", "", m.group(1)).strip(), page))
    return out


def block_for(section: str, items: list[tuple[str, str, Path]], i: int) -> str:
    lines = []
    for k in range(1, N + 1):
        slug, title, _ = items[(i + k) % len(items)]
        lines.append(f'    <li><a href="https://crispvideo.app/{section}/{slug}/">{title}</a></li>')
    return "  <h2>Related</h2>\n  <ul>\n" + "\n".join(lines) + "\n  </ul>\n\n"


def main() -> int:
    check = "--check" in sys.argv
    stale, total = [], 0
    for name in SECTIONS:
        section = SITE / name
        if not section.is_dir():
            continue
        items = articles(section)
        if len(items) < N + 1:
            print(f"  {name}: only {len(items)} pages — need more than {N} for neighbours")
            continue
        total += len(items)
        for i, (slug, _, page) in enumerate(items):
            text = page.read_text()
            want = block_for(name, items, i)
            stripped = BLOCK.sub("", text)
            if CTA in stripped:
                out = stripped.replace(CTA, want + CTA, 1)
            elif END in stripped:
                # keep the block inside the article, immediately before it closes
                # ⚠️ `want` ALREADY ENDS IN A BLANK LINE, and BLOCK requires it to strip the
                # block back out. My first version rstrip'd it here, so the regex no longer
                # matched, nothing was stripped on the next run, and each run inserted ANOTHER
                # block — 53 pages accumulating duplicates. Second time the strip/insert pair
                # in this file drifted out of being exact inverses; both times --check caught it.
                out = stripped.replace(END, want + END, 1)
            else:
                print(f"  SKIP {name}/{slug}: no CTA and no article close to anchor to")
                continue
            if out != text:
                stale.append(f"{name}/{slug}")
                if not check:
                    page.write_text(out)
    if check:
        if stale:
            print(f"Related block is stale on {len(stale)} pages: {', '.join(stale[:12])}"
                  + (" …" if len(stale) > 12 else ""))
            return 1
        print(f"Related block is current on all {total} pages")
        return 0
    print(f"{len(stale)} of {total} pages updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
