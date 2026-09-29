"""Site-wide chrome every page carries: Bing's site verification tag, the "More from Kerr & Company" footer, and
the founding-offer bar.

CEO order, 2026-09-26 (on Matthew's "AI-search visibility fixes, all site-side"):
  · <meta name="msvalidate.01" …> in EVERY page head — the Kerr & Company Bing account's code, the one that
    already verifies all 8 sites;
  · a footer block "More from Kerr & Company" on every page, plain followed links, wording exactly as ordered.

CEO order, 2026-09-28 (Matthew: "make the discount banner go across all pages of every website, not just the
home pages"): the founding bar on EVERY page — the homepage's own mount tag, copied verbatim so the offer is
stated in one place — EXCEPT /thank-you/ (a buyer who has just paid must not be offered a discount) and pages
that canonicalise to another URL (merge stubs). Experiment arms get it too: identical site-wide chrome on
treatment and control does not bias the read.

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
    # CEO order, 2026-09-29: the company Dodo shows buyers (the DODOPAY_KERRANDCOMPANY card-statement line)
    # was linked from no product page. The LEGAL name, as the privacy page and the terms state it (the CEO's
    # correction the same day: "Holdings" is only in the domain). The name is HTML (the & is escaped).
    ("Kerr &amp; Company LLC", "https://kerrandcompanyholdings.com/", "the company behind these apps"),
]
KCO = ('<div class="kco" data-kco><p class="kco-h">More from Kerr &amp; Company</p><ul class="kco-list">'
       + "".join(f'<li><a href="{u}">{n}</a>: {d}</li>' for n, u, d in SIBLINGS)
       + "</ul></div>")

#: The homepage's older, longer cross-sell ("Also built by the same person") is REPLACED by the standard block,
#: so the page does not carry two.
HOME_SIBLING = re.compile(r'  <div class="wrap foot foot-sibling">\n.*?\n  </div>\n(?=</footer>)', re.S)


#: Plausible custom events ("Download" on every Crisp.dmg link, "Buy" on every checkout link) — first-party
TRACK = '<script src="/track.js" defer></script>'


KCO_BLOCK = re.compile(r'<div class="kco" data-kco>.*?</ul></div>', re.S)
ARMS_FILE = Path.home() / "ops" / "search" / "ARMS.md"


def arms() -> set[str]:
    """The arms of a running experiment (~/ops/search/ARMS.md): their copy and links do not change mid-read, so an
    existing footer on an arm is left exactly as it is. Refuses to guess if the file is missing."""
    if not ARMS_FILE.is_file():
        raise SystemExit("sitewide_chrome: ~/ops/search/ARMS.md is missing — refusing to guess which pages are arms")
    return {m.group(1) for m in re.finditer(r"^crispvideo\.app \| (/\S+/) \|", ARMS_FILE.read_text(), re.M)}


def is_arm(p: Path) -> bool:
    try:
        rel = "/" + p.parent.relative_to(SITE).as_posix() + "/"
    except ValueError:
        return False
    return p.name == "index.html" and rel in arms()


def founding_tag() -> str:
    """The homepage's founding mount + script, verbatim — the single place the offer's figures are written."""
    home = (SITE / "index.html").read_text()
    m = re.search(r'<div data-founding[^>]*></div>\n<script src="/founding\.js" defer></script>', home)
    assert m, "homepage: the founding mount moved — update founding_tag()"
    return m.group(0)


def wants_founding(p: Path, s: str) -> bool:
    if p == SITE / "index.html" or p.name != "index.html" or p.parent.name == "thank-you":
        return False
    try:
        rel = "/" + p.parent.relative_to(SITE).as_posix() + "/"
    except ValueError:          # a page outside the site tree (the gate's own fixture): judge it on its canonical alone
        return "rel=\"canonical\"" not in s
    m = re.search(r'<link rel="canonical" href="https://crispvideo\.app(/[^"]*)"', s)
    return not (m and m.group(1) != rel)     # a merge stub points elsewhere: no offer on it


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
    # A footer whose block predates a wording change is regenerated in place — except on an experiment arm.
    if "data-kco" in s and KCO not in s and not is_arm(p):
        s, n = KCO_BLOCK.subn(KCO, s)
        assert n == 1, f"{p}: expected one kco block to refresh, found {n}"
    if has_footer(s) and "data-kco" not in s:
        if p == SITE / "index.html":
            assert HOME_SIBLING.search(s), "homepage: the sibling block moved — update HOME_SIBLING"
            s = HOME_SIBLING.sub('  <div class="wrap foot foot-sibling">\n    ' + KCO + '\n  </div>\n', s)
        else:
            # inside the footer's .wrap, after whatever the page already says there
            assert s.count("</footer>") == 1, f"{p}: expected one </footer>"
            s, n = re.subn(r"</div>(\s*)</footer>", lambda m: "  " + KCO + "\n</div>" + m.group(1) + "</footer>", s)
            assert n == 1, f"{p}: footer does not end in </div></footer>"
    # the Download/Buy events, on every page with a body (moved out of the homepage 2026-09-28)
    if "</body>" in s and TRACK not in s:
        s = s.replace("</body>", TRACK + "\n</body>")
    if wants_founding(p, s) and "/founding.js" not in s:
        assert s.count("</body>") == 1, f"{p}: expected one </body>"
        s = s.replace("</body>", founding_tag() + "\n</body>")
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
    elif has_footer(s) and KCO not in s and not is_arm(p):
        out.append("stale kco footer")
    if "</body>" in s and s.count(TRACK) != 1:
        out.append("track.js")
    if wants_founding(p, s) and s.count(founding_tag()) != 1:
        out.append("founding bar")
    if not wants_founding(p, s) and p != SITE / "index.html" and "/founding.js" in s:
        out.append("founding bar where it must not be")
    return out


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = {str(p.relative_to(SITE)): m for p in pages() if (m := missing(p))}
        print(f"checked {len(pages())} pages; missing: {bad or 'none'}")
        sys.exit(1 if bad else 0)
    changed = [p for p in pages() if apply(p)]
    print(f"updated {len(changed)} of {len(pages())} pages")
