#!/usr/bin/env python3
"""Every claim this site makes about a competitor's PRICE or FEATURE carries a checked-on date, and no such date is older than 45 days.

WHY. A comparison quotes other companies' prices, plans, platforms and features, and those move without telling us. A date only proves
somebody looked once: nothing made anyone look again. The first version of this gate (2026-10-15) failed a push on any read date older
than 45 days, but it read only vs/ and learn/, so the home page's Topaz prices, the best/ round-ups and the how-to comparison tables were
never looked at, and a claim with NO date was not its business at all, so an undated claim could sit beside a fresh date and the page
passed. The rule now (CEO, 2026-10-19): every page that quotes any competitor's price or feature gives each claim set a checked-on date;
the push FAILS when a claim set's date is more than 45 days old and WARNS past 30.

WHICH PAGES. Every public .html page under the site (home, vs/, learn/, best/, how-to/, for/, pricing/, legal/ and anything added later),
except the instant-refresh merge stubs (<meta http-equiv="refresh" content="0; ...">), which carry no content. Only what a visitor reads
is looked at: comments, <script>, <style>, <head>, <nav> and <footer> are dropped. JSON-LD and meta descriptions are not read here
(price_sources.head_only_prices() makes the head's prices match the body's).

WHAT A READ DATE IS. "read", "re-read", "checked", "verified", "accessed" or "retrieved", then at most eight short words that do not end a
sentence ("read from each vendor's own buy page on"), then a date written as 15 October 2026, 15 Oct 2026, October 15, 2026, 2026-10-15
or October 2026 (a month with no day counts as the 1st, which can only make it older). "first read ...", "earlier read ...",
"previously read ..." and "originally read ..." are history, not the current read, and are skipped. A date in the future is a failure (a
typo that would hide a stale figure).

WHAT A COMPETITOR CLAIM IS. A sentence (a table row, for a table) that names a competitor in VENDORS below and says something checkable
about it. Its kind decides which dates may cover it:
  FEATURE  a platform or requirement (macOS, Windows, RAM, GPU, cloud, upload, offline, account), which wins even when the sentence
           also carries a price; otherwise a has / lacks / supports / does not / can't / only / includes / lists / exports / limits /
           up to statement;
  PRICE    a money figure that is not one of Crisp's own (price_sources.OURS), free / paid, a plan, tier, trial, subscription,
           licence term, refund, seats or machines, a watermark.
A sentence that names no competitor still counts when it opens with It / Its / They / Their right after a sentence that LEADS with
one ("Aiarty enhances video. It doesn't edit it."), or when it quotes a money figure that is not ours right after a sentence naming
one, or under a heading that names one ("Is Topaz Video AI free?" / "No. $299 a year ..."). A table row is a claim about every competitor named in the table's header row or
in the row itself, when it has two or more filled cells; a column headed "Crisp" is left out when judging its kind. NOT claims:
headings, <summary>, breadcrumbs (class *crumb*), the text of links to our own pages, "Crisp vs X" and "X alternative" (search terms),
and any block inside an element marked data-claims="none" (for a block that names a competitor but only describes Crisp; the marker
is visible in review, so use it sparingly and never to dodge a real claim). ffmpeg is deliberately not a competitor (see VENDORS).

WHICH DATE COVERS A CLAIM (its claim set), nearest scope first; within a scope the OLDEST current read date is the one that counts:
  1. its own block: the same paragraph, list item, table row, <dd>, <figcaption> or <blockquote>. Any read date there covers it.
  2. its table or list: the table's <caption> and header/footer rows, the block immediately before the table or list (its lead-in)
     and the block immediately after it (its source line). The lead-in and the source line belong to the same set, so "These are the
     plans as read on 28 September 2026" above a table also covers "There is no one-time price on that page" below it.
  3. the page's stated checked line for that competitor: a block with class price-receipts, src, sources, receipts or claims-checked,
     or one that opens with "Prices checked", "Sources, all read", "Read 15 October 2026 from ...", or has a sentence opening
     "Sources: ... read <date>" / "Prices ... checked <date>", AND names the competitor or links its domain.
In scopes 2 and 3 a date whose own label is a price read ("Prices checked 15 October 2026", "List price ... read from each vendor's
own buy page on ...") covers PRICE claims only: a price read does not prove a feature was read. Any other label covers both.

THE VERDICT, per page: the OLDEST date covering any claim decides. Older than --max-days (45): FAIL. Older than --warn-days (30): WARN,
printed and passed (the pre-push hook shows the WARN lines). In the future: FAIL. Every current read date on the page, claim or not,
is held to the same window (the first gate's rule, kept). A claim no date covers: FAIL, unless it is recorded in
claim_dates_baseline.json, the claims that were already undated when this rule landed (2026-10-19). Those are counted on every run,
listed by --list as REREAD, and each needs the vendor's page re-read and a date put on ours. A baselined claim that has since been
dated or removed prints as FIXED so its entry can be deleted. The baseline keys on the page, the competitor and the claim's own words,
so an undated claim that is rewritten is a new claim, and fails.

    python3 _tools/gate_read_dates.py                  # exit 1 on a stale, future or new undated claim; WARN lines past 30 days
    python3 _tools/gate_read_dates.py --max-days 30    # a stricter window
    python3 _tools/gate_read_dates.py --today 2026-12-01 --list   # what a later date would flag, every known undated claim too; exit 0
    python3 _tools/gate_read_dates.py --claims         # every claim set found, page by page, with the date that covers it
    python3 _tools/gate_read_dates.py --oldest         # the oldest competitor read date on the site, and its page
    python3 _tools/gate_read_dates.py --selftest       # the checker must fail on planted old, hidden, out-of-section and undated claims
    python3 _tools/gate_read_dates.py --baseline       # re-record today's undated claims (deliberate; say why in the commit)
    CRISP_ALLOW_STALE_READS=1 ...                      # a deliberate, loud override for an urgent push

It reads files on disk only. It never fetches anything.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from price_sources import MONEY, OURS  # noqa: E402  Crisp's own figures, from the one place they are listed
BASELINE = Path(__file__).resolve().parent / "claim_dates_baseline.json"
SECTIONS = ("vs", "learn")          # the first gate's scope; kept for anyone importing it. pages() now reads every public page.
MAX_DAYS, WARN_DAYS = 45, 30

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
_MONTH = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_M = _MONTH.replace("(", "(?:", 1)  # the same alternation, non-capturing, for the named groups below
_DATE = (r"(?:(?P<d1>\d{1,2})\s+(?P<m1>" + _M + r")\.?,?\s+(?P<y1>\d{4})"        # 15 October 2026, 15 Oct. 2026
         r"|(?P<m2>" + _M + r")\.?\s+(?P<d2>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y2>\d{4})"   # October 15, 2026
         r"|(?P<y3>\d{4})-(?P<n3>\d{2})-(?P<d3>\d{2})"                             # 2026-10-15
         r"|(?P<m4>" + _M + r")\.?,?\s+(?P<y4>\d{4}))")                            # October 2026 -> the 1st
_KEY = r"(?<![\w-])(?<!first )(?<!earlier )(?<!previously )(?<!originally )(?:re-?)?(?:read|checked|verified|accessed|retrieved)"
_GAP = r"(?:[:,]?\s+(?:[^\s\d]{0,39}[^\s\d.;!?])){0,8}?"  # up to eight short words, none ending a sentence
READ = re.compile(_KEY + r"\b" + _GAP + r"[:,]?\s+(?:on\s+)?" + _DATE + r"\b", re.I)
_DROP = re.compile(r"<!--.*?-->|<script.*?</script>|<style.*?</style>", re.S | re.I)
_TAGS = re.compile(r"<[^>]+>")
_REFRESH = re.compile(r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]*content=["\']\s*0\s*;', re.I)


def text_of(html: str) -> str:
    """What a visitor reads: comments, scripts and styles gone, tags gone, entities and whitespace flattened."""
    t = _TAGS.sub(" ", _DROP.sub(" ", html)).replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t)


def _to_date(m: re.Match) -> date | None:
    g = m.groupdict()
    try:
        if g["y1"]:
            return date(int(g["y1"]), MONTHS[g["m1"][:3].lower()], int(g["d1"]))
        if g["y2"]:
            return date(int(g["y2"]), MONTHS[g["m2"][:3].lower()], int(g["d2"]))
        if g["y3"]:
            return date(int(g["y3"]), int(g["n3"]), int(g["d3"]))
        if g["y4"]:
            return date(int(g["y4"]), MONTHS[g["m4"][:3].lower()], 1)
    except (ValueError, KeyError):
        return None
    return None


def _dates_in_text(t: str) -> list[date]:
    out = []
    for m in READ.finditer(t.replace("\xa0", " ")):
        d = _to_date(m)
        if d:
            out.append(d)
    return out


def reads_in(html: str) -> list[date]:
    """Every current read date in a page's visible text (the first gate's view, kept for its callers)."""
    return _dates_in_text(text_of(html))


# ── competitors ────────────────────────────────────────────────────────────────────────────────────
#: name -> (pattern, domains). Case-sensitive brand spellings; ambiguous one-word names (Photos, Motion, Preview, Clips, Resolve)
#: are matched only in their unambiguous forms, or as a table's column header.
VENDORS: dict[str, tuple[str, tuple[str, ...]]] = {
    "Topaz": (r"Topaz(?:\s+(?:Video(?:\s+AI)?|Labs|Studio|Photo|Gigapixel))?|Gigapixel|Project Starlight|Starlight Mini", ("topazlabs.com",)),
    "Aiarty": (r"Aiarty(?:\s+Video\s+Enhancer)?", ("aiarty.com",)),
    "HitPaw": (r"HitPaw(?:\s+VikPea)?|VikPea", ("hitpaw.com",)),
    "Upscayl": (r"Upscayl", ("upscayl.org", "github.com/upscayl")),
    "UniFab": (r"UniFab", ("unifab.ai",)),
    "AVCLabs": (r"AVCLabs(?:\s+Video\s+Enhancer(?:\s+AI)?)?", ("avclabs.com",)),
    "VideoProc": (r"VideoProc(?:\s+(?:Converter(?:\s+AI)?|Vlogger))?|Winxvideo(?:\s+AI)?|Digiarty", ("videoproc.com", "winxdvd.com")),
    "CapCut": (r"CapCut", ("capcut.com",)),
    "Clipchamp": (r"Clipchamp", ("clipchamp.com",)),
    "Filmora": (r"(?:Wondershare\s+)?Filmora|Wondershare", ("filmora.wondershare.com", "wondershare.com")),
    "Final Cut Pro": (r"Final\s+Cut(?:\s+Pro)?", ("apple.com/final-cut-pro",)),
    "HandBrake": (r"(?i:handbrake)", ("handbrake.fr",)),
    "iMovie": (r"iMovie", ("support.apple.com/guide/imovie", "apple.com/imovie")),
    "InShot": (r"InShot", ("inshot.com",)),
    "Kapwing": (r"Kapwing", ("kapwing.com",)),
    "Real-ESRGAN": (r"Real-ESRGAN", ("github.com/xinntao",)),
    "VEED": (r"VEED|Veed\.io", ("veed.io",)),
    "DaVinci Resolve": (r"DaVinci(?:\s+Resolve(?:\s+Studio)?)?", ("blackmagicdesign.com",)),
    "Premiere Pro": (r"(?:Adobe\s+)?Premiere(?:\s+(?:Pro|Rush|Elements))?", ("adobe.com/products/premiere",)),
    "Adobe": (r"Adobe(?!\s+Premiere)", ("adobe.com",)),
    "QuickTime": (r"QuickTime(?:\s+Player)?(?!\s+(?:container|format|files?|movies?|MOV|\.mov|wrapper))", ("support.apple.com/guide/quicktime-player",)),
    "Apple Photos": (r"Apple\s+Photos|the\s+Photos\s+app|Photos\s+app|Photos\s+for\s+Mac", ("support.apple.com/guide/photos",)),
    "waifu2x": (r"(?i:waifu2x)", ("github.com/nagadomi",)),
    "Video2X": (r"Video2X", ("github.com/k4yt3x",)),
    "Photoshop": (r"Photoshop", ("adobe.com/products/photoshop",)),
    "Lightroom": (r"Lightroom", ("adobe.com/products/photoshop-lightroom",)),
    "Pixelmator": (r"Pixelmator(?:\s+Pro)?", ("pixelmator.com",)),
    "Descript": (r"Descript", ("descript.com",)),
    "Canva": (r"Canva", ("canva.com",)),
    "Shotcut": (r"Shotcut", ("shotcut.org",)),
    "Remini": (r"Remini", ("remini.ai",)),
    "Movavi": (r"Movavi", ("movavi.com",)),
    "PowerDirector": (r"(?:CyberLink\s+)?PowerDirector", ("cyberlink.com",)),
    "LumaFusion": (r"(?i:lumafusion)", ("luma-touch.com",)),
    "Audacity": (r"Audacity", ("audacityteam.org",)),
    "iZotope RX": (r"iZotope(?:\s+RX)?", ("izotope.com",)),
    "Apple Compressor": (r"Apple\s+Compressor", ("apple.com/final-cut-pro/compressor",)),
    "Apple Motion": (r"Apple\s+Motion", ("apple.com/final-cut-pro/motion",)),
    "Apple Clips": (r"Apple\s+Clips|the\s+Clips\s+app", ("apple.com/clips",)),
}
#: a table column headed by exactly one of these is that competitor's column
HEADER_ALIASES = {"Photos": "Apple Photos", "Motion": "Apple Motion", "Clips": "Apple Clips", "Resolve": "DaVinci Resolve",
                  "Compressor": "Apple Compressor", "Preview": "Apple Preview"}
#: NOT A VENDOR, ON PURPOSE: ffmpeg. Crisp ships it, and nearly every sentence naming it on this site describes Crisp's own pipeline
#: ("the bundled ffmpeg's psnr filter", "a chain of ffmpeg atempo stages"); the rest say an open-source tool is free, which no vendor's
#: offer page can make stale. Measured on the 2026-10-19 site: with ffmpeg in, it flagged 33 sentences, about half of them Crisp's
#: own pipeline or our own measurements and the rest "ffmpeg is free" or its command line.
_VENDOR_RES = [(n, re.compile(r"(?<![\w.-])(?<!vs )(?<!vs\. )(?<!versus )(?:" + p + r")(?![\w-])(?!\s+alternatives?\b)"))
               for n, (p, _) in VENDORS.items()]
OURS_COLUMN = re.compile(r"^\s*Crisp(?:\s+Pro)?\s*$", re.I)


def vendors_in(text: str) -> list[str]:
    """The competitors a piece of text names, as the subject of something, not as "Crisp vs X" or "the X alternative" (a search term)."""
    found = []
    for name, rx in _VENDOR_RES:
        if rx.search(text) and name not in found:
            found.append(name)
    return found


def _leads_with_vendor(s: str) -> bool:
    return any((m := rx.search(s)) is not None and m.start() <= 20 for _, rx in _VENDOR_RES)


def _vendor_named(name: str, text: str, hrefs: list[str]) -> bool:
    rx = dict(_VENDOR_RES)[name] if name in VENDORS else None
    if rx is not None and rx.search(text):
        return True
    doms = VENDORS.get(name, ("", ()))[1]
    return any(d.lower() in h.lower() for d in doms for h in [*hrefs, text])   # its domain, linked or written out


PRICE_CUE = re.compile(
    r"\b(?:free|freemium|paid|price[sd]?|pricing|costs?|pay(?:s|ing)?|subscriptions?|subscribe|per\s+(?:year|month)|"
    r"a\s+(?:year|month)|annual(?:ly)?|monthly|one-time|lifetime|perpetual|licen[cs]e[sd]?|plans?|tiers?|trials?|refunds?|"
    r"discount(?:ed)?|on\s+offer|renew(?:s|al|ing)?|seats?|machines|devices|activations?|watermark(?:ed|s)?|credits?|upsell)\b"
    r"|/(?:yr|mo|year|month)\b", re.I)
#: a platform or requirement: a price read never covers one of these, even in a sentence that also carries a price
PLATFORM_CUE = re.compile(
    r"\b(?:macOS|Mac[- ]only|mobile[- ]only|Windows|Linux|iPhone|iPad|iOS|Android|Apple\s+Silicon|Intel|M[1-4]|RAM|VRAM|GPUs?|"
    r"NVIDIA|\d+\s?GB|requires?|required|requirements?|minimum|cloud|uploads?|uploaded|servers?|browser|web\s+app|online|"
    r"offline|on-device|locally|account|sign[- ]in|log[- ]in|internet)\b", re.I)
CAPABILITY_CUE = re.compile(
    r"\b(?:has|have|had|lacks?|lacking|supports?|supported|does\s+not|doesn't|did\s+not|didn't|do\s+not|don't|can't|cannot|"
    r"can\s+not|won't|will\s+not|isn't|aren't|no\s+longer|never|only|offers?|offered|includes?|included|ships?|lists?|listed|"
    r"documents?|documented|exports?|imports?|limits?|limited|caps?|capped|up\s+to|maximum|without|no|yes|varies|stripped|manual)\b", re.I)
_PRONOUN = re.compile(r"^\W*(?:It|Its|It's|They|Their|Theirs|That app|This app|The app)\b")
_SENT = re.compile(r"(?<=[.!?])[\"”’)]*\s+(?=[\"“(]?[A-Z0-9$])")
_ABBREV = re.compile(r"\b(?:e\.g|i\.e|vs|etc|approx|Mr|Ms|Dr|No|cf)\.$", re.I)
RECEIPT_CLASSES = {"price-receipts", "src", "sources", "receipts", "claims-checked"}
_LABEL_WORDS = r"(?:all\s+)?(?:prices?|pricing|features?|specs?|requirements?|facts?|claims?|sources?)\b"
#: a stated checked line: a block that OPENS with "Prices checked ...", "Sources, all read ...", "Read 15 October 2026 from ...",
#: or that has a sentence opening "Sources: ... read <date>" / "Prices ... checked <date>" (a bare mid-paragraph "Checked <date>." is
#: that paragraph's own date, not a line for the page)
_LABEL_START = re.compile(r"^\W*(?:" + _LABEL_WORDS + r"[^.!?]{0,300}?)?" + _KEY + r"\b", re.I)
_LABEL_MID = re.compile(r"[.!?]\s+\W*" + _LABEL_WORDS + r"[^.!?]{0,300}?" + _KEY + r"\b", re.I)
_PRICE_LABEL = re.compile(r"\b(?:prices?|pricing|costs?|plans?|buy\s+page|purchase\s+page|store)\b", re.I)
_FEATURE_LABEL = re.compile(r"\b(?:features?|specs?|requirements?|README|docs?|documentation|guide|support|manual|help|system)\b", re.I)


def sentences(text: str) -> list[str]:
    parts, cur = [], ""
    for piece in _SENT.split(text):
        cur = (cur + " " + piece).strip() if cur else piece
        if _ABBREV.search(cur):
            continue
        parts.append(cur)
        cur = ""
    if cur:
        parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


# ── the page, as blocks ────────────────────────────────────────────────────────────────────────────
_SKIP = {"script", "style", "head", "nav", "footer", "noscript", "svg", "template", "title"}
_UNITS = {"p", "li", "tr", "dt", "dd", "figcaption", "caption", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "summary", "pre",
          "div", "section", "article", "aside", "header", "main", "details", "body", "figure", "form", "label"}
_CONTAINERS = {"table", "ul", "ol", "dl"}
_VOID = {"br", "img", "hr", "meta", "link", "input", "source", "wbr", "area", "base", "col", "embed", "param", "track"}
_NOT_CLAIMS = {"h1", "h2", "h3", "h4", "h5", "h6", "summary", "caption"}
_INTERNAL = re.compile(r"^(?:/|#|\.|https?://(?:www\.)?crispvideo\.app\b)", re.I)


class Block:
    """One block of visible text. (Plain classes, not dataclasses: the tests load this file by path, without sys.modules, and a
    dataclass under `from __future__ import annotations` needs its module registered there.)"""

    def __init__(self, idx, tag, classes, container=None, role="", ancestors=(), optout=False):
        self.idx, self.tag, self.classes = idx, tag, classes
        self.container = container     # innermost table/ul/ol/dl
        self.role = role               # head | foot | row | item | ""
        self.text = ""                 # what a visitor reads
        self.claim_text = ""           # the same, without the text of links to our own pages
        self.cells, self.cell_claim, self.th, self.hrefs = [], [], [], []
        self.ancestors = ancestors
        self.optout = optout           # inside an element marked data-claims="none"


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        self.stack: list[tuple] = []   # (tag, block_idx|None, container_idx|None, internal_link, data-claims=none)
        self.containers: dict[int, dict] = {}
        self._cid = 0
        self.skip = 0

    def _unit(self) -> Block | None:
        for _, bi, _, _, _ in reversed(self.stack):
            if bi is not None:
                return self.blocks[bi]
        return None

    def _container(self):
        for _, _, ci, _, _ in reversed(self.stack):
            if ci is not None:
                return ci
        return None

    def _in(self, *tags) -> bool:
        return any(s[0] in tags for s in self.stack)

    def handle_starttag(self, tag, attrs):
        if tag in _VOID:
            if tag == "br" and not self.skip:
                u = self._unit()
                if u:
                    u.text += " "
                    u.claim_text += " "
            return
        a = dict(attrs)
        if tag in ("p", "li", "tr", "dt", "dd") and self.stack and self.stack[-1][0] == tag:
            self.handle_endtag(tag)    # an unclosed <p>/<li>/<tr> closes at the next one
        if tag in _SKIP:
            self.skip += 1
            self.stack.append((tag, None, None, False, False))
            return
        bi = ci = None
        optout = (a.get("data-claims") or "").strip().lower() == "none"
        if tag in _CONTAINERS and not self.skip:
            self._cid += 1
            ci = self._cid
            self.containers[ci] = {"tag": tag, "start": len(self.blocks), "end": None, "head_vendors": [], "ours": set(),
                                   "ancestors": {s[1] for s in self.stack if s[1] is not None}, "rows": 0}
        if tag in _UNITS and not self.skip:
            c = self._container()
            role = ""
            if tag == "tr":
                role = "head" if self._in("thead") else "foot" if self._in("tfoot") else "row"
            elif tag == "caption":
                role = "head"
            elif tag in ("li", "dt", "dd"):
                role = "item"
            b = Block(len(self.blocks), tag, set((a.get("class") or "").split()), c, role,
                      ancestors=tuple(s[1] for s in self.stack if s[1] is not None),
                      optout=optout or any(s[4] for s in self.stack))
            self.blocks.append(b)
            bi = b.idx
        internal = False
        if tag == "a" and not self.skip:
            href = a.get("href") or ""
            u = self._unit()
            if u is not None and href:
                u.hrefs.append(href)
            internal = bool(_INTERNAL.match(href))
        if tag in ("td", "th") and not self.skip:
            u = self._unit()
            if u is not None and u.tag == "tr":
                u.cells.append("")
                u.cell_claim.append("")
                u.th.append(tag == "th")
                u.text += " | "
                u.claim_text += " | "
        self.stack.append((tag, bi, ci, internal, optout))

    def handle_endtag(self, tag):
        if not any(s[0] == tag for s in self.stack):
            return
        while self.stack:
            t, bi, ci, _, _ = self.stack.pop()
            if t in _SKIP:
                self.skip -= 1
            if ci is not None:
                self.containers[ci]["end"] = len(self.blocks) - 1
            if t == tag:
                break

    def handle_data(self, data):
        if self.skip:
            return
        u = self._unit()
        if u is None:
            return
        internal = any(s[3] for s in self.stack)
        u.text += data
        if not internal:
            u.claim_text += data
        if u.tag == "tr" and u.cells:
            u.cells[-1] += data
            if not internal:
                u.cell_claim[-1] += data


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def blocks_of(html: str) -> tuple[list[Block], dict]:
    p = _Parser()
    p.feed(html)
    p.close()
    for info in p.containers.values():
        if info["end"] is None:
            info["end"] = len(p.blocks) - 1
    for b in p.blocks:
        b.text, b.claim_text = _clean(b.text), _clean(b.claim_text)
        b.cells = [_clean(c) for c in b.cells]
        b.cell_claim = [_clean(c) for c in b.cell_claim]
    # a table's header row: the vendors it names, and which column is ours
    for b in p.blocks:
        if b.tag != "tr" or b.container is None:
            continue
        info = p.containers[b.container]
        info["rows"] += 1
        if info["rows"] == 1 and (b.role == "head" or (b.th and all(b.th))):
            b.role = "head"
            cols = []
            for i, c in enumerate(b.cells):
                v = vendors_in(c) or ([HEADER_ALIASES[c.strip()]] if c.strip() in HEADER_ALIASES else [])
                cols.extend(x for x in v if x not in cols)
                if OURS_COLUMN.match(c):
                    info["ours"].add(i)
            info["head_vendors"] = cols
    return p.blocks, p.containers


# ── claims and what covers them ────────────────────────────────────────────────────────────────────
class Claim:
    def __init__(self, page, vendor, kind, text, block):
        self.page, self.vendor, self.text, self.block = page, vendor, text, block
        self.kind = kind               # PRICE | FEATURE
        self.covered = None            # the date that covers it, or None (undated)
        self.how = ""                  # own | container | page-line
        self.by = ""                   # the covering block's text

    def __repr__(self):
        return f"Claim({self.page!r}, {self.vendor!r}, {self.kind}, {self.covered}, {self.text[:60]!r})"


def _kind(text: str) -> str | None:
    """PRICE: money that is not ours, or a plan / licence / trial word. FEATURE: a platform or requirement (which wins over a price,
    so a "Prices checked" line cannot cover "it is $99 and Windows-only"), or a has / lacks / supports / does-not statement."""
    if PLATFORM_CUE.search(text):
        return "FEATURE"
    if _theirs_money(text) or PRICE_CUE.search(text):
        return "PRICE"
    if CAPABILITY_CUE.search(text):
        return "FEATURE"
    return None


def claims_in_blocks(blocks: list[Block], containers: dict, page: str = "") -> list[Claim]:
    out = []
    heading, last = {}, []
    for b in blocks:                    # the competitors the nearest heading above each block names
        if b.tag in ("h1", "h2", "h3", "h4", "h5", "h6", "summary"):
            last = vendors_in(b.claim_text or b.text)
        heading[b.idx] = last
    for b in blocks:
        if b.tag in _NOT_CLAIMS or not b.claim_text or b.optout or any("crumb" in c for c in b.classes):
            continue
        if b.tag == "tr":
            if b.role != "row":
                continue
            info = containers.get(b.container, {})
            filled = [c for c in b.cells if c]
            if len(filled) < 2:
                continue
            theirs = " | ".join(c for i, c in enumerate(b.cell_claim) if i not in info.get("ours", set()))
            vs = list(info.get("head_vendors", []))
            vs += [v for v in vendors_in(theirs) if v not in vs]
            k = _kind(theirs) or "FEATURE"
            for v in vs:
                out.append(Claim(page, v, k, theirs, b.idx))
            continue
        prev: list[str] = []
        prev_leads = False
        for s in sentences(b.claim_text):
            vs = vendors_in(s)
            if not vs and _PRONOUN.match(s) and prev_leads:
                vs = prev                       # "Aiarty enhances video. It doesn't edit it."
            if not vs and _theirs_money(s):
                vs = prev or heading.get(b.idx, [])   # "Is Topaz Video AI free?" / "No. $299 a year ..."
            if vs:
                prev, prev_leads = vs, _leads_with_vendor(s) or (prev_leads and not vendors_in(s))
                k = _kind(s)
                if k:
                    for v in vs:
                        out.append(Claim(page, v, k, s, b.idx))
            else:
                prev, prev_leads = [], False
    return out


def _theirs_money(s: str) -> bool:
    """A money figure that is not one of Crisp's own (price_sources.OURS, the one list of them)."""
    return any(m.group(1).rstrip(".,") not in OURS for m in MONEY.finditer(s))


def dated_reads(text: str) -> list[tuple[date, set]]:
    """Each current read date in a block, with what it may cover from OUTSIDE that block: prices only when its own label is a price
    read ("Prices checked 15 October 2026", "List price ... read from each vendor's own buy page on ..."), else prices and features."""
    out, prev_end = [], 0
    t = text.replace("\xa0", " ")
    for m in READ.finditer(t):
        d = _to_date(m)
        if not d:
            continue
        head = t[prev_end:m.start()]
        cut = max(head.rfind(". "), head.rfind("; "))
        head = (head[cut + 2:] if cut >= 0 else head)[-200:]
        kinds = {"PRICE"} if _PRICE_LABEL.search(head) and not _FEATURE_LABEL.search(head) else {"PRICE", "FEATURE"}
        out.append((d, kinds))
        prev_end = m.end()
    return out


def _is_page_line(b: Block) -> bool:
    return bool(b.classes & RECEIPT_CLASSES) or bool(_LABEL_START.match(b.text)) or bool(_LABEL_MID.search(b.text))


def cover(claims: list[Claim], blocks: list[Block], containers: dict) -> None:
    reads = {b.idx: dated_reads(b.text) for b in blocks}
    nonempty = [b.idx for b in blocks if b.text]

    def lead_trail(ci):
        """The blocks that speak for a whole table or list: its caption and header/footer rows, the block just before it (its lead-in)
        and the block just after it (its source line)."""
        info = containers.get(ci)
        if not info:
            return []
        lo, hi = info["start"], info["end"]
        before = [i for i in nonempty if i < lo and i not in info["ancestors"]]
        after = [i for i in nonempty if i > hi]
        out = [b.idx for b in blocks if b.container == ci and b.role in ("head", "foot")]
        if before:
            out.append(before[-1])
        if after:
            out.append(after[0])
        return out

    sets = {ci: lead_trail(ci) for ci in containers}
    beside = {}                     # a lead-in or source line belongs to its table's claim set too
    for ci, members in sets.items():
        for i in members:
            beside.setdefault(i, set()).update(members)

    def oldest_for(kind, idxs):
        best = None
        for i in idxs:
            for d, kinds in reads[i]:
                if kind in kinds and (best is None or d < best[0]):
                    best = (d, i)
        return best

    page_lines = [b.idx for b in blocks if reads[b.idx] and _is_page_line(b)]
    for c in claims:
        b = blocks[c.block]
        if reads[b.idx]:                                     # 1. its own block: any date there covers it
            c.covered, c.how, c.by = min(d for d, _ in reads[b.idx]), "own", b.text
            continue
        near = set(sets.get(b.container, [])) if b.container is not None and b.role in ("row", "item") else set()
        near |= beside.get(b.idx, set()) - {b.idx}
        if near:                                             # 2. its table or list, with that table's lead-in and source line
            hit = oldest_for(c.kind, sorted(near))
            if hit:
                c.covered, c.how, c.by = hit[0], "container", blocks[hit[1]].text
                continue
        hit = oldest_for(c.kind, [i for i in page_lines if _vendor_named(c.vendor, blocks[i].text, blocks[i].hrefs)])
        if hit:                                              # 3. the page's checked line for that competitor
            c.covered, c.how, c.by = hit[0], "page-line", blocks[hit[1]].text


def page_claims(html: str, page: str = "") -> list[Claim]:
    blocks, containers = blocks_of(html)
    cs = claims_in_blocks(blocks, containers, page)
    cover(cs, blocks, containers)
    return cs


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9$]+", " ", s.lower()).strip()


def _key(page: str, c: Claim) -> tuple:
    return (page, c.vendor, _norm(c.text))


class Verdict:
    """One page's result; its claims carry their covering date (None = undated)."""

    def __init__(self, page, claims):
        self.page, self.claims = page, claims
        self.stale, self.future, self.warn = [], [], []    # (date, [claims]) past max_days / after today / past warn_days
        self.undated_new, self.undated_known = [], []      # undated claims not in / in the baseline
        self.loose_reads = []                              # (date, level): read dates on the page that cover no detected claim

    @property
    def failed(self) -> bool:
        return bool(self.stale or self.future or self.undated_new or any(lvl != "WARN" for _, lvl in self.loose_reads))


def judge_page(html: str, today: date, max_days: int = MAX_DAYS, warn_days: int = WARN_DAYS, page: str = "",
               known_undated=frozenset()) -> Verdict:
    claims = page_claims(html, page)
    v = Verdict(page, claims)
    by_date: dict = {}
    for c in claims:
        if c.covered is None:
            (v.undated_known if _key(page, c) in known_undated else v.undated_new).append(c)
        else:
            by_date.setdefault(c.covered, []).append(c)
    for d, cs in sorted(by_date.items()):
        age = (today - d).days
        if d > today:
            v.future.append((d, cs))
        elif age > max_days:
            v.stale.append((d, cs))
        elif age > warn_days:
            v.warn.append((d, cs))
    for d in sorted(set(reads_in(html)) - set(by_date)):    # the first gate's rule, kept: every stated read, claim or not
        age = (today - d).days
        if d > today:
            v.loose_reads.append((d, "FUTURE"))
        elif age > max_days:
            v.loose_reads.append((d, "STALE"))
        elif age > warn_days:
            v.loose_reads.append((d, "WARN"))
    return v


def _vendors(cs) -> str:
    return ", ".join(sorted({c.vendor for c in cs}))


def _reasons(v: Verdict, today: date, max_days: int) -> tuple[list[str], list[str]]:
    fails, warns = [], []
    for d, cs in v.future:
        fails.append(f"{len(cs)} claim(s) on {_vendors(cs)} dated {d.isoformat()}, which is in the future: “{_short(cs[0].text)}”")
    for d, cs in v.stale:
        fails.append(f"{len(cs)} claim(s) on {_vendors(cs)} read {d.isoformat()}, {(today - d).days} days ago (limit {max_days}):"
                     f" “{_short(cs[0].text)}”")
    for d, lvl in v.loose_reads:
        msg = f"a read dated {d.isoformat()} ({(today - d).days} days ago) that covers no claim this gate recognised"
        (warns if lvl == "WARN" else fails).append(msg if lvl != "FUTURE" else f"a read dated {d.isoformat()} is in the future")
    for c in v.undated_new:
        fails.append(f"UNDATED {c.vendor} {c.kind.lower()} claim: “{_short(c.text)}”")
    for d, cs in v.warn:
        warns.append(f"{len(cs)} claim(s) on {_vendors(cs)} read {d.isoformat()}, {(today - d).days} days ago (re-read before day"
                     f" {max_days}): “{_short(cs[0].text)}”")
    return _uniq(fails), _uniq(warns)


def judge(html: str, today: date, max_days: int = MAX_DAYS, warn_days: int = WARN_DAYS, page: str = "",
          known_undated=frozenset()) -> tuple[list[str], list[str], list[Claim]]:
    """-> (failures, warnings, claims) for one page, as sentences."""
    v = judge_page(html, today, max_days, warn_days, page, known_undated)
    fails, warns = _reasons(v, today, max_days)
    return fails, warns, v.claims


def _uniq(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _short(s: str, n: int = 140) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"


def problems(html: str, today: date, max_days: int = MAX_DAYS, known_undated=frozenset()) -> list[str]:
    """Every reason this page FAILS: a stale or future read, a claim whose covering date is stale or future, an undated claim."""
    return judge(html, today, max_days, known_undated=known_undated)[0]


def warnings(html: str, today: date, warn_days: int = WARN_DAYS, max_days: int = MAX_DAYS, known_undated=frozenset()) -> list[str]:
    """Every reason this page WARNS: a read or a claim set read more than warn_days ago (and not yet past max_days)."""
    return judge(html, today, max_days, warn_days, known_undated=known_undated)[1]


def is_stub(html: str) -> bool:
    return bool(_REFRESH.search(html))


def pages(site: Path | None = None) -> list[Path]:
    """Every public page: all .html under the site except _tools/, dot-folders and the instant-refresh merge stubs."""
    root = Path(site) if site else SITE
    out = []
    for p in sorted(root.rglob("*.html")):
        rel = p.relative_to(root).parts
        if rel[0] in ("_tools", "node_modules") or any(x.startswith(".") for x in rel):
            continue
        if is_stub(p.read_text(errors="replace")):
            continue
        out.append(p)
    return out


def page_name(p: Path, root: Path) -> str:
    rel = p.relative_to(root)
    if rel.name == "index.html":
        return "/" if str(rel.parent) == "." else str(rel.parent)
    return str(rel)


def load_baseline(path: Path | None = None) -> set:
    path = path or BASELINE
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(pg, v, _norm(row["text"])) for pg, rows in data.get("undated", {}).items() for row in rows for v in row["vendors"]}


def scan(site: Path | None = None, today: date | None = None, max_days: int = MAX_DAYS, warn_days: int = WARN_DAYS,
         known_undated: set | None = None) -> dict:
    """-> {page name: Verdict} for every public page."""
    root = Path(site) if site else SITE
    today = today or date.today()
    known = load_baseline() if known_undated is None else known_undated
    return {page_name(p, root): judge_page(p.read_text(errors="replace"), today, max_days, warn_days, page_name(p, root), known)
            for p in pages(root)}


# ── self-test ──────────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    today = date(2026, 10, 15)
    fresh_topaz = '<p class="price-receipts">Prices checked 15 October 2026: topazlabs.com/pricing shows Topaz Video at $299/yr.</p>'
    row = '<table><thead><tr><th></th><th>Crisp</th><th>Aiarty</th></tr></thead><tbody><tr><td>{0}</td><td>Yes</td><td>{1}</td></tr></tbody></table>'
    checks = {
        "a planted old date fails": problems("<p>Prices checked 8 July 2026 on the vendor's page.</p>", today),
        "a fresh date with history passes": not problems("<p>Prices checked 15 October 2026 (first read 8 July 2026 in a browser).</p>", today),
        "no dates, no claims passes": not problems("<p>No dates here.</p>", today),
        "comments and scripts are not read": not problems("<!-- read 1 January 2020 --><script>var s='read 2 February 2020'</script><p>ok</p>", today),
        "a short inline date covers its claim": not problems("<p>Topaz Video is $299 (read 24 Sep 2026)</p>", today),
        "a future date fails": problems("<p>read 20 October 2026</p>", today),
        # what the first gate could not see
        "an old claim in US date format behind a fresh one fails":
            problems(fresh_topaz + "<p>HitPaw VikPea costs $99 a year (checked August 1, 2026).</p>", today),
        "an undated claim behind a fresh date for another vendor fails":
            problems(fresh_topaz + "<p>HitPaw VikPea costs $99 a year.</p>", today),
        "an undated competitor price fails": problems("<p>Aiarty Video Enhancer is $165 lifetime.</p>", today),
        "a feature claim is not covered by a price-only line": problems(fresh_topaz + "<p>Topaz Video does not run on Intel Macs.</p>", today),
        "a 31-day claim warns and passes":
            not problems("<p>Upscayl is free (read 14 September 2026).</p>", today)
            and bool(warnings("<p>Upscayl is free (read 14 September 2026).</p>", today)),
        "a table's source line covers its rows":
            not problems(row.format("Price", "$165 lifetime") + '<p class="src">Sources, all read 10 October 2026: aiarty.com.</p>', today),
        "an undated table row fails": problems(row.format("Timeline", "No") + "<p>Unrelated.</p>", today),
        "a stale table row fails through its source line":
            problems(row.format("Timeline", "No") + "<p>Sources, all read 1 August 2026.</p>", today),
        "a link to our own page is not a claim": not problems('<p>See <a href="/vs/topaz-alternative-mac/">Topaz has a plan</a>.</p>', today),
        "a block marked data-claims=none is not a claim": not problems('<p data-claims="none">Topaz is $1 a year.</p>', today),
    }
    bad = [k for k, ok in checks.items() if not ok]
    print("gate_read_dates self-check " + ("passed" if not bad else "FAILED: " + "; ".join(bad)))
    return 0 if not bad else 1


# ── CLI ────────────────────────────────────────────────────────────────────────────────────────────
def _write_baseline(res: dict, today: date) -> int:
    undated = {}
    for name, v in res.items():
        rows: dict = {}
        for c in v.claims:
            if c.covered is None:
                r = rows.setdefault(_norm(c.text), {"vendors": [], "kind": c.kind, "text": c.text})
                if c.vendor not in r["vendors"]:
                    r["vendors"].append(c.vendor)
        if rows:
            undated[name] = list(rows.values())
    BASELINE.write_text(json.dumps({
        "written": today.isoformat(),
        "why": "Competitor claims that carried no checked-on date when the claim-date rule landed (CEO, 2026-10-19). Each needs a "
               "re-read of the vendor's own page and then a date on our page; delete its entry once it is dated. A claim that is not "
               "listed here and has no date FAILS the push. Re-record with --baseline only deliberately, and say why in the commit.",
        "undated": undated}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n = sum(len(r) for r in undated.values())
    print(f"baseline recorded: {n} undated claim sentences or table rows on {len(undated)} pages -> {BASELINE.name}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Competitor claim dates: fail past --max-days, warn past --warn-days, fail when undated.")
    ap.add_argument("--max-days", type=int, default=MAX_DAYS)
    ap.add_argument("--warn-days", type=int, default=WARN_DAYS)
    ap.add_argument("--today", help="YYYY-MM-DD, to plan a refresh")
    ap.add_argument("--list", action="store_true", help="print every problem, including each known undated claim, and exit 0")
    ap.add_argument("--claims", action="store_true", help="print every claim set found, page by page, with the date that covers it")
    ap.add_argument("--oldest", action="store_true", help="print the oldest competitor read date and its page")
    ap.add_argument("--baseline", action="store_true", help="re-record today's undated claims in claim_dates_baseline.json (deliberate)")
    ap.add_argument("--site", help=argparse.SUPPRESS)   # for tests: a folder of planted pages instead of the site
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if selftest():
        return 1
    site = Path(a.site) if a.site else SITE
    today = date.fromisoformat(a.today) if a.today else date.today()
    if a.baseline:
        return _write_baseline(scan(site, today, a.max_days, a.warn_days, known_undated=set()), today)
    known = load_baseline()
    res = scan(site, today, a.max_days, a.warn_days, known_undated=known)
    claims = [(n, c) for n, v in res.items() for c in v.claims]
    dated = sorted(((c.covered, n, c) for n, c in claims if c.covered), key=lambda x: x[0])

    if a.claims:
        for name, v in res.items():
            if not v.claims:
                continue
            print(f"\n{name}")
            sets: dict = {}
            for c in v.claims:
                sets.setdefault((c.covered, c.how, c.by if c.covered else ""), []).append(c)
            for (d, how, by), cs in sorted(sets.items(), key=lambda kv: (kv[0][0] or date.min)):
                print(f"  {d.isoformat() if d else 'UNDATED   '}  {how or '-':9s} {len(cs):3d} claim(s)  {_vendors(cs)}"
                      + (f"   <- “{_short(by, 90)}”" if by else ""))
        print()

    if a.oldest:
        if not dated:
            print("oldest competitor read: none found (a gate that finds no dates proves nothing)")
            return 1
        d, n, c = dated[0]
        same = [x[2] for x in dated if x[1] == n and x[0] == d]
        print(f"oldest competitor read: {d.isoformat()} ({(today - d).days} days before {today.isoformat()}) on {n}, covering"
              f" {len(same)} claim(s) on {_vendors(same)}; e.g. “{_short(c.by, 160)}”")
        loose = sorted((d2, n2) for n2, v in res.items() for d2, _ in v.loose_reads)
        if loose and loose[0][0] < d:
            print(f"  older still: a read dated {loose[0][0].isoformat()} on {loose[0][1]} that covers no recognised claim")
        return 0

    failing = {n: v for n, v in res.items() if v.failed}
    n_known = n_warn = 0
    for n, v in res.items():
        fails, warns = _reasons(v, today, a.max_days)
        n_warn += len(warns)
        for w in warns:
            print(f"  WARN   {n}: {w}")
        for f in fails:
            print(f"  {'FAIL ' if f.startswith('UNDATED') else 'STALE'}  {n}: {f}")
        n_known += len(v.undated_known)
        if a.list:
            for c in v.undated_known:
                print(f"  REREAD {n}: undated {c.vendor} {c.kind.lower()} claim (baseline): “{_short(c.text)}”")
    present = {_key(n, c) for n, c in claims if c.covered is None}
    fixed = sorted({(k[0], k[1]) for k in known if k not in present})
    for pg, vendor in fixed:
        print(f"  FIXED  {pg}: a baselined undated {vendor} claim is dated or gone; delete it from {BASELINE.name}")
    oldest = f"oldest read {dated[0][0].isoformat()} on {dated[0][1]}" if dated else "no dated claim"
    tally = (f"{len(claims)} competitor claims on {sum(1 for v in res.values() if v.claims)} of {len(res)} pages, {oldest};"
             f" {n_warn} WARN past {a.warn_days} days; {n_known} undated claims awaiting a re-read ({BASELINE.name}, --list)")
    if failing and not a.list:
        print(f"  pages failing: {', '.join(failing)}")
        if os.environ.get("CRISP_ALLOW_STALE_READS") == "1":
            print(f"read-dates: {len(failing)} page(s) have a stale, future or undated competitor claim; ALLOWED by"
                  f" CRISP_ALLOW_STALE_READS=1. Re-read them next. ({tally})")
            return 0
        print(f"read-dates: {len(failing)} page(s) carry a competitor claim read more than {a.max_days} days ago, dated in the future,"
              f" or not dated at all. Re-read it on the vendor's own page and date it in the claim's own block or the page's checked"
              f" line, or take the claim down. ({tally})")
        return 1
    if failing:
        print(f"read-dates: {len(failing)} of {len(res)} pages would fail on {today.isoformat()} ({tally})")
        return 0
    print(f"read-dates: no competitor claim older than {a.max_days} days on {today.isoformat()}; {tally}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
