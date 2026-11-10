"""Site-wide chrome every page carries: Bing's site verification tag, the "Made by Kerr & Company" footer link, and
the founding-offer bar.

CEO order, 2026-10-13 (Bing): the footer block is now ONE link, to the company, and nothing links to a sister site (see
SIBLINGS below for why). Earlier orders in this docstring describe the block as it used to be.

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

#: CEO order, 2026-10-13 (Matthew: "fix bing ... make sure we dont make the same mistakes that made us stop getting sales"):
#: ONE off-site link in the footer, to the company, and no link to any sister site from any page. outlier.host's Bing
#: impressions went from 45-89 a day to 8 and then to 0 within a day of a block of links to every sibling domain going
#: onto 171 of its pages: Bing reads sitewide links between commonly owned sites as a link scheme, and Bing feeds ChatGPT
#: search, where the early buyers came from. This file used to list five sister sites and the company on every page.
#: The sister sites may still be NAMED in plain text; they are not linked. _tools/gate_sibling_links.py fails the push, and
#: tests/test_no_page_links_to_a_sibling_domain_outside_about.py fails the build, on any link to one outside /about/.
SIBLINGS = [("Made by Kerr &amp; Company", "https://kerrandcompanyholdings.com/")]
KCO = ('<div class="kco" data-kco><ul class="kco-list">'
       + "".join(f'<li><a href="{u}">{n}</a></li>' for n, u in SIBLINGS)
       + "</ul></div>")

#: The homepage's older, longer cross-sell ("Also built by the same person") is REPLACED by the standard block,
#: so the page does not carry two.
HOME_SIBLING = re.compile(r'  <div class="wrap foot foot-sibling">\n.*?\n  </div>\n(?=</footer>)', re.S)


#: Plausible custom events ("Download" on every Crisp.dmg link, "Buy" on every checkout link) — first-party
TRACK = '<script src="/track.js" defer></script>'


KCO_BLOCK = re.compile(r'<div class="kco" data-kco>.*?</ul></div>', re.S)
ARMS_FILE = Path.home() / "ops" / "search" / "ARMS.md"

# THE NAV BUTTON AND THE FOOTER SAY MAC OR PC (CEO, 2026-11-05). A Windows visitor reading "Download for Mac" in the bar is a lost
# download: the bar now says "Download" and opens /download/, which shows both, tagged nav-download (track.js counts it as the
# "Download Page" event). The footer says "for Mac and PC" only for what runs on Windows: the video upscaler and the timeline editor
# (the editor ran in the real Windows window in the Store screenshots); the photo upscaler and the auto-editor stay "for Mac" until a
# Windows run proves them. NAVIGATION IS NOT CONTENT: both sit outside <article>, so content_hash ignores them and no page is re-dated.
NAV_OLD = '<a class="btn" href="https://crispvideo.app/#download">Download for Mac</a>'
NAV_NEW = '<a class="btn" data-track="nav-download" href="https://crispvideo.app/download/?src=nav-download">Download</a>'
FOOTER_OLD_NEW = {
    "offline AI video &amp; photo upscaler and auto-editor for Mac.":
        "offline AI video &amp; photo upscaler and auto-editor for Mac, and a video upscaler and editor for Windows.",
    "offline AI video upscaler + full timeline editor for Mac.":
        "offline AI video upscaler + full timeline editor for Mac and PC.",
}


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


# THE BAR IS DRAWN BEFORE THE FIRST PAINT (Crisp, 2026-11-10). founding.js inserts the launch-price bar as the first thing in
# <body>. Loaded with `defer` at the end of the page, it ran after the browser had already painted the page, so the bar arrived
# 0.4 s in and pushed the whole page down by its own height (61 px on a phone): Lighthouse measured CLS 0.069 on the home page
# from that one shift (layout-shift source: div.hero, moved 57 -> 118 px). The mount and a plain (blocking) script now sit
# FIRST in <body>, so the bar is in place before anything below it is laid out: CLS 0.069 -> 0 on the home page, with no
# Performance cost (three Lighthouse runs each on local copies: 81-82 before, 82-83 after; FCP the same). The mount has no
# margin any more: at the top of the page an empty mount (a visitor who closed the bar, or after the offer ends) must take
# no room. Measured and recorded in ~/ops/launch/crisp/cls-founding-bar-2026-11-10.md.
FOUNDING_RE = re.compile(r'<div data-founding[^>]*></div>\n<script src="/founding\.js"></script>')
#: the old placement (deferred, before </body>), migrated by apply()
FOUNDING_OLD_RE = re.compile(r'\n?<div data-founding[^>]*></div>\n<script src="/founding\.js" defer></script>')
BODY_OPEN = re.compile(r'<body[^>]*>\n?')


def founding_tag() -> str:
    """The homepage's founding mount + script, verbatim — the single place the offer's figures are written."""
    home = (SITE / "index.html").read_text()
    m = FOUNDING_RE.search(home)
    assert m, "homepage: the founding mount moved — update founding_tag()"
    return m.group(0)


def founding_first_in_body(s: str) -> bool:
    """The bar's mount + script are the first thing in <body>, so the bar is drawn before the page below it."""
    b = BODY_OPEN.search(s)
    return bool(b) and FOUNDING_RE.match(s, b.end()) is not None


def _put_founding_first(s: str, p: Path) -> str:
    b = BODY_OPEN.search(s)
    assert b and s.count("<body") == 1, f"{p}: expected one <body>"
    head = s[:b.end()] if b.group(0).endswith("\n") else s[:b.end()] + "\n"
    return head + founding_tag() + "\n" + s[b.end():]


# GERMAN PAGES KEEP THEIR OWN FOOTER AND OFFER (Crisp, 2026-11-10). de_pages.py writes the footer link as "Von Kerr &amp;
# Company" (de_strings.FOOTER["made_by"]) and leaves the bar off ("founding.js inserts English sentences. The German offer uses
# data-until."). This tool did not know that: run in apply mode it rewrote the German footer into English on 7 pages and added the
# English bar to 5 (found and reverted on 10 Nov, before any push). So on a German page the footer link is checked in German,
# the bar is never added, and where a German page already carries it (/de/datenschutz/, /de/kostenlos-oder-pro/) it is only
# kept first in <body> like everywhere else.
def german(p: Path) -> bool:
    try:
        return p.relative_to(SITE).parts[:1] == ("de",)
    except ValueError:
        return False


def kco_for(p: Path) -> str:
    if german(p):
        from de_strings import FOOTER
        return KCO.replace("Made by Kerr &amp; Company", FOOTER["made_by"])
    return KCO


def wants_founding(p: Path, s: str) -> bool:
    if p == SITE / "index.html" or p.name != "index.html" or p.parent.name == "thank-you":
        return False
    if german(p):
        return "/founding.js" in s
    try:
        rel = "/" + p.parent.relative_to(SITE).as_posix() + "/"
    except ValueError:          # a page outside the site tree (the gate's own fixture): judge it on its canonical alone
        return "rel=\"canonical\"" not in s
    m = re.search(r'<link rel="canonical" href="https://crispvideo\.app(/[^"]*)"', s)
    return not (m and m.group(1) != rel)     # a merge stub points elsewhere: no offer on it


def pages() -> list[Path]:
    # a redirect stub (instant meta refresh: how a merged page is retired on GitHub Pages) is not a page that carries the chrome
    stub = re.compile(r'<meta\s+http-equiv="refresh"\s+content="0;\s*url=', re.I)
    return sorted(p for p in SITE.rglob("*.html") if ".git" not in p.parts and "_tools" not in p.parts
                  and not stub.search(p.read_text(errors="replace")))


def has_footer(s: str) -> bool:
    return "</footer>" in s


def apply(p: Path) -> bool:
    s = o = p.read_text()
    if MSVALIDATE not in s:
        m = re.search(r'<meta name="viewport"[^>]*>\n?', s)
        assert m, f"{p}: no viewport meta to anchor the verification tag"
        s = s[:m.end()] + ("" if m.group(0).endswith("\n") else "\n") + MSVALIDATE + "\n" + s[m.end():]
    # A footer whose block predates a wording change is regenerated in place — except on an experiment arm.
    if "data-kco" in s and kco_for(p) not in s and not is_arm(p):
        s, n = KCO_BLOCK.subn(lambda _m: kco_for(p), s)
        assert n == 1, f"{p}: expected one kco block to refresh, found {n}"
    if has_footer(s) and "data-kco" not in s:
        if p == SITE / "index.html":
            assert HOME_SIBLING.search(s), "homepage: the sibling block moved — update HOME_SIBLING"
            s = HOME_SIBLING.sub('  <div class="wrap foot foot-sibling">\n    ' + KCO + '\n  </div>\n', s)
        else:
            # inside the footer's .wrap, after whatever the page already says there
            assert s.count("</footer>") == 1, f"{p}: expected one </footer>"
            s, n = re.subn(r"</div>(\s*)</footer>", lambda m: "  " + kco_for(p) + "\n</div>" + m.group(1) + "</footer>", s)
            assert n == 1, f"{p}: footer does not end in </div></footer>"
    # the Download/Buy events, on every page with a body (moved out of the homepage 2026-09-28)
    if "</body>" in s and TRACK not in s:
        s = s.replace("</body>", TRACK + "\n</body>")
    if wants_founding(p, s):
        if FOUNDING_OLD_RE.search(s):
            s, n = FOUNDING_OLD_RE.subn("", s)
            assert n == 1, f"{p}: expected one old founding mount, found {n}"
        if "/founding.js" not in s:
            s = _put_founding_first(s, p)
    # the bar and the footer for a PC too; an experiment arm keeps its copy and links as they are
    if not is_arm(p):
        if NAV_OLD in s:
            assert s.count(NAV_OLD) == 1, f"{p}: expected one nav download button"
            s = s.replace(NAV_OLD, NAV_NEW)
        for old, new in FOOTER_OLD_NEW.items():
            s = s.replace(old, new)
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
    elif has_footer(s) and kco_for(p) not in s and not is_arm(p):
        out.append("stale kco footer")
    if "</body>" in s and s.count(TRACK) != 1:
        out.append("track.js")
    if wants_founding(p, s) and s.count(founding_tag()) != 1:
        out.append("founding bar")
    elif wants_founding(p, s) and not founding_first_in_body(s):
        out.append("founding bar not first in body")
    if not wants_founding(p, s) and p != SITE / "index.html" and "/founding.js" in s:
        out.append("founding bar where it must not be")
    if not is_arm(p):
        if NAV_OLD in s:
            out.append("nav says Download for Mac")
        if any(old in s for old in FOOTER_OLD_NEW):
            out.append("footer says Mac only")
    return out


if __name__ == "__main__":
    if "--check" in sys.argv:
        bad = {str(p.relative_to(SITE)): m for p in pages() if (m := missing(p))}
        print(f"checked {len(pages())} pages; missing: {bad or 'none'}")
        sys.exit(1 if bad else 0)
    changed = [p for p in pages() if apply(p)]
    print(f"updated {len(changed)} of {len(pages())} pages")
