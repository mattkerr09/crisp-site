"""Site-wide chrome every page carries: Bing's site verification tag and the "More from Kerr & Company" footer.

CEO order, 2026-09-26 (on Matthew's "AI-search visibility fixes, all site-side"):
  · <meta name="msvalidate.01" …> in EVERY page head — the Kerr & Company Bing account's code, the one that
    already verifies all 8 sites;
  · a footer block "More from Kerr & Company" on every page, plain followed links, wording exactly as ordered.

Idempotent: run it after adding or regenerating pages and it only adds what is missing. new_pages.py carries
both in its template, and tests/test_every_page_carries_the_sitewide_chrome.py fails any page without them.

    python3 _tools/sitewide_chrome.py          # apply
    python3 _tools/sitewide_chrome.py --check  # exit 1 if any page is missing either
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]

MSVALIDATE = '<meta name="msvalidate.01" content="34D102FD9C044A2BDA597B176842725B" />'

#: Wording exactly as ordered. Plain links: no rel, no target — followed, same tab.
SIBLINGS = [
    ("Outlier", "https://outlier.host/", "private, offline AI for your Mac"),
    ("Docket SEO", "https://docketseo.app/", "website audits that rank what to fix first"),
    ("AdPlaybook", "https://adplaybook.app/", "ad copy within every platform's limits"),
    ("Built by Kerr", "https://builtbykerr.com/", "websites and local SEO for Grand Rapids businesses"),
]
KCO = ('<div class="kco" data-kco><p class="kco-h">More from Kerr &amp; Company</p><ul class="kco-list">'
       + "".join(f'<li><a href="{u}">{n}</a>: {d}</li>' for n, u, d in SIBLINGS)
       + "</ul></div>")

#: The homepage's older, longer cross-sell ("Also built by the same person") is REPLACED by the standard block,
#: so the page does not carry two.
HOME_SIBLING = re.compile(r'  <div class="wrap foot foot-sibling">\n.*?\n  </div>\n(?=</footer>)', re.S)


def pages() -> list[Path]:
    return sorted(p for p in SITE.rglob("*.html") if ".git" not in p.parts and "_tools" not in p.parts)


def has_footer(s: str) -> bool:
    return "</footer>" in s


def apply(p: Path) -> bool:
    s = o = p.read_text()
    if MSVALIDATE not in s:
        m = re.search(r'<meta name="viewport"[^>]*>\n?', s)
        assert m, f"{p}: no viewport meta to anchor the verification tag"
        s = s[:m.end()] + ("" if m.group(0).endswith("\n") else "\n") + MSVALIDATE + "\n" + s[m.end():]
    if has_footer(s) and "data-kco" not in s:
        if p == SITE / "index.html":
            assert HOME_SIBLING.search(s), "homepage: the sibling block moved — update HOME_SIBLING"
            s = HOME_SIBLING.sub('  <div class="wrap foot foot-sibling">\n    ' + KCO + '\n  </div>\n', s)
        else:
            # inside the footer's .wrap, after whatever the page already says there
            assert s.count("</footer>") == 1, f"{p}: expected one </footer>"
            s, n = re.subn(r"</div>(\s*)</footer>", lambda m: "  " + KCO + "\n</div>" + m.group(1) + "</footer>", s)
            assert n == 1, f"{p}: footer does not end in </div></footer>"
    if s != o:
        p.write_text(s)
        return True
    return False


def missing(p: Path) -> list[str]:
    s = p.read_text()
    out = []
    head = s[:s.find("</head>")] if "</head>" in s else ""
    if head.count(MSVALIDATE) != 1:
        out.append("msvalidate")
    if has_footer(s) and s.count("data-kco") != 1:
        out.append("kco footer")
    return out


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = {str(p.relative_to(SITE)): m for p in pages() if (m := missing(p))}
        print(f"checked {len(pages())} pages; missing: {bad or 'none'}")
        sys.exit(1 if bad else 0)
    changed = [p for p in pages() if apply(p)]
    print(f"updated {len(changed)} of {len(pages())} pages")
