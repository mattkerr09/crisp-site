#!/usr/bin/env python3
"""Every rival price on a /vs/ page must carry the date it was checked.

A comparison page quotes other companies' prices, and those move without telling us. This site
has already published wrong ones: a blind find-and-replace put Crisp's own new price onto four
rivals' figures and they stayed wrong for eighteen days, through audits that read the HTML and
passed, because nothing tied a number to when anybody last looked at it.

Five pages already do it properly — a "Prices checked <date>" block naming each rival's own
pricing URL and what it showed. This makes that the rule, and reports the pages that quote a
rival's figure with no such block.

RATCHETS, IT DOES NOT GO RED. Six pages are in that state today. A gate red on six pages is one
nobody reads, which is exactly how the eighteen-day bug survived. So the current six live in
price_sources_baseline.json and the gate fails only on a page that is NOT in the baseline, or one
that has grown a new unsourced figure. Fixed pages are named so their line can be deleted.

    python3 _tools/price_sources.py            # report + exit 1 on new debt
    python3 _tools/price_sources.py --baseline # re-record today's state (deliberate)
"""
import html
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
BASELINE = Path(__file__).resolve().parent / "price_sources_baseline.json"

# Crisp's own price is not a rival's price and needs no external source.
OURS = {"129", "129.00", "0"}
MONEY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")
DATED = re.compile(r"Prices?\s+checked\s+\d", re.I)


# The descriptions live in <head>, and they are the copy Google actually shows.
DESCRIPTIONS = re.compile(
    r'<meta[^>]+(?:name|property)="(?:description|og:description|twitter:description)"[^>]+'
    r'content="([^"]*)"|"description"\s*:\s*"((?:[^"\\]|\\.)*)"',
    re.I,
)


def _text(p: Path) -> str:
    """Body copy PLUS every description, which is where the stale price hid last time.

    Stripping <head> wholesale was this tool's own blind spot, and it is the exact bug the tool
    exists to catch: HitPaw's dead $349.99 survived in the meta description, og:description,
    twitter:description and the JSON-LD long after the body was right. A rival price quoted only
    in a description is the version a searcher reads FIRST, before deciding whether to click.
    Proven rather than reasoned: a $777 planted in a meta description passed this gate with
    exit 0 before this change.
    """
    t = p.read_text(encoding="utf-8", errors="replace")
    descs = " ".join(m.group(1) or m.group(2) or "" for m in DESCRIPTIONS.finditer(t))
    t = re.sub(r"(?is)<(script|style|head|nav|footer)\b.*?</\1>", " ", t)
    visible = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(visible + " " + descs))


#: ⚠️ A PATTERN TOO NARROW REPORTS ZERO AND READS EXACTLY LIKE A CLEAN SITE.
#: This gate's whole output is "N pages quote a rival price with no date". If MONEY stopped
#: matching the way prices are actually written, N would be 0 and the report would be
#: indistinguishable from success. That is not hypothetical here: this tool's first run said 19
#: pages, then 8, then 6, because "$129." with a trailing full stop is not the string "$129" —
#: the parser, not the site, moved the number three times. So the pattern proves itself against
#: known-good text before the survey is believed.
_MUST_MATCH = ("$129", "$ 129", "$1,299.99", "costs $299 a year", "$12/month", "$437.99 list")
_MUST_NOT = ("129 dollars", "£129", "$", "USD 129")


def _self_check() -> None:
    for sample in _MUST_MATCH:
        if not MONEY.search(sample):
            raise SystemExit(
                f"price pattern no longer matches {sample!r} — a clean report would prove "
                f"nothing, because the pattern has been narrowed past real prices")
    for sample in _MUST_NOT:
        if MONEY.search(sample):
            raise SystemExit(
                f"price pattern now matches {sample!r}, which is not a price this gate should "
                f"claim — a widened pattern turns every page into a false positive")


#: ⚠️ THIS WAS A CHARACTER COUNT AND THE COUNT WAS THE BUG. The first version read 900
#: characters from the phrase "Prices checked", calibrated because the longest real block then
#: ran 618. Then I wrote a longer block — sourcing three more vendors on one page — and the tool
#: reported MORE unsourced figures after the fix than before it, because everything past 900
#: characters fell outside the window and counted as unquoted. A threshold measured against
#: today's content is a threshold that breaks the moment the content grows, and it breaks
#: silently in the direction that looks like a regression.
#: All eleven dated pages wrap the block in <p class="price-receipts">, so the block has a real
#: boundary and the tool now uses it. The character window survives only as a fallback for a page
#: that has the phrase and not the class, and is generous rather than tight.
_BLOCK_FALLBACK_CHARS = 2000
_RECEIPTS = re.compile(r'<p[^>]+class="[^"]*price-receipts[^"]*"[^>]*>(.*?)</p>', re.S | re.I)


def unsourced_figures(page: Path) -> list[tuple[str, str]]:
    """Rival figures on the page that its own dated block does not record.

    WHY THIS EXISTS, AND IT IS NOT THE SAME CHECK AS THE ONE ABOVE. The survey below asks whether
    a page carries a dated block at all. It cannot ask whether the block covers the figures the
    page quotes, and those are different questions — Docket found the gap the hard way
    (docket-site 112afd3c): they published "$184-$428/yr" for a rival, arrived at by taking the
    monthly price, multiplying by twelve and applying the discount the vendor advertises. Both
    inputs true, the output false, because that vendor rounds — they charge $180 and $425. A date
    proves somebody looked. It does not prove the NUMBER was read rather than derived.
    Crisp shipped the same defect: our VEED row once read "$144 a year", being 12 x $12, where
    VEED's own annual figure is $147.
    So: every rival figure on the page must also appear inside the block that cites the vendor's
    page. A figure that appears only in prose was either derived, or read from somewhere the
    block does not name — and both are worth a human looking.
    Returns (figure, surrounding text) so the caller can judge rather than guess. Several honest
    shapes land here on purpose: an openly-labelled total ("over three years that is $897"), a
    hedged rounding ("roughly $120/year"), and a table quoting FOUR other vendors under a block
    that cites only one of them. The last is the one worth fixing, and it is invisible without
    this check.
    """
    txt = _text(page)
    m = DATED.search(txt)
    if not m:
        return []                      # no block at all is the survey's job, not this one
    raw = page.read_text(encoding="utf-8", errors="replace")
    receipts = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", b))
                        for b in _RECEIPTS.findall(raw))
    block = receipts if receipts.strip() else txt[m.start():m.start() + _BLOCK_FALLBACK_CHARS]
    in_block = {x.group(1).rstrip(".").rstrip(",") for x in MONEY.finditer(block)}
    out = []
    for x in MONEY.finditer(txt):
        fig = x.group(1).rstrip(".").rstrip(",")
        # ⚠️ KNOWN, BOUNDED, AND DELIBERATELY OPEN. Skipping OURS is what stops 34 true mentions
        # of our own $129 being reported as unsourced rival figures on every run. The cost is a
        # blind spot: a page saying "Topaz is $129" is excluded here as ours, and excluded by
        # our_price_errors() as theirs, so NEITHER lane reports it. Docket's rule for this shape is
        # to partition the pages rather than exclude them (Docket 1.3.40, `6dcf99e`) and it is the
        # right shape — but it is not free, and the hole only opens if a rival's price is exactly
        # $129. None is. Re-read this comment the day one is, and partition then.
        if fig in OURS or fig in in_block:
            continue
        out.append((fig, txt[max(0, x.start() - 70):x.start() + 60].strip()))
    seen, uniq = set(), []
    for fig, ctx in out:
        if fig not in seen:
            seen.add(fig)
            uniq.append((fig, ctx))
    return uniq


#: Prices ATTRIBUTED to Crisp — "Crisp is $129", "Crisp Pro — $129", "Crisp costs $129".
#: Attribution, not proximity: a ±90-character window around the word "Crisp" swallows whole
#: comparison rows and reported 45 false hits on a site where the real answer is zero.
OURS_ATTRIBUTED = [
    re.compile(r"Crisp\s+(?:Pro\s+)?(?:is|costs?|at)\s+\$\s?(\d[\d,]*(?:\.\d+)?)", re.I),
    re.compile(r"Crisp\s+(?:Pro\s+)?[—–-]\s*\$\s?(\d[\d,]*(?:\.\d+)?)", re.I),
    re.compile(r"Crisp\s+Pro\s+\$\s?(\d[\d,]*(?:\.\d+)?)", re.I),
]


def our_price_errors() -> list[tuple[str, str, str]]:
    """Every price this site puts in Crisp's own name that is not Crisp's price.

    ⚠️ THE OTHER AXIS. Everything above polices RIVAL figures — is this quoted, is it sourced, is
    it read rather than computed. Not one of those rules has an opinion about OUR price, so a page
    could say "Crisp is $149 once" and every gate here would pass it. Outlier found the same shape
    from the other side (outlier-site `2ae4223b`): their rival-price gate checked table COLUMNS,
    their own product was a ROW, and three competitors were published at Outlier's price under a
    gate that reported "clean" — truthfully, because it had no opinion about rows and said so in a
    sentence that reads like a verdict. **A decision enforced on one axis is enforced by nobody on
    the other.**
    Currently 34 attributed prices, all $129, none wrong — so this is a fence around something
    already right, and it can go red immediately rather than needing a baseline.
    """
    out = []
    for page in sorted(SITE.rglob("index.html")):
        if "_tools" in page.parts:
            continue
        txt = _text(page)
        for pat in OURS_ATTRIBUTED:
            for m in pat.finditer(txt):
                v = m.group(1).rstrip(".").rstrip(",")
                if v not in OURS:
                    out.append((str(page.parent.relative_to(SITE)), v,
                                txt[max(0, m.start() - 60):m.end() + 40].strip()))
    return out


def survey():
    """-> {slug: [rival figures]} for /vs/ pages quoting a rival price with no dated block."""
    gaps = {}
    for page in sorted((SITE / "vs").glob("*/index.html")):
        txt = _text(page)
        rivals = sorted({m.group(1) for m in MONEY.finditer(txt)
                         if m.group(1).rstrip(".").rstrip(",") not in OURS})
        if rivals and not DATED.search(txt):
            gaps[page.parent.name] = rivals
    return gaps


UNSOURCED_BASELINE = Path(__file__).resolve().parent / "price_unsourced_baseline.json"


def _unsourced_self_check() -> None:
    """A planted figure that the block does not record MUST be reported.

    Same reasoning as _self_check above: this check's clean output and its blind output are the
    same empty list, so it has to be shown failing before it is believed.
    """
    page = next((p for p in sorted((SITE / "vs").glob("*/index.html")) if DATED.search(_text(p))),
                None)
    if page is None:
        raise SystemExit("no dated page to self-check against — cannot prove this check works")
    original = page.read_text(encoding="utf-8")
    planted = original.replace("</body>", "<p>Rival Ultra costs $91919 a year.</p></body>", 1)
    try:
        page.write_text(planted, encoding="utf-8")
        caught = any(f == "91919" for f, _ in unsourced_figures(page))
    finally:
        page.write_text(original, encoding="utf-8")
    if not caught:
        raise SystemExit("a planted unsourced $91919 was NOT reported — this check cannot fail, "
                         "so its clean output proves nothing")
    if page.read_text(encoding="utf-8") != original:
        raise SystemExit("the self-check did not restore the page it edited")


def _ours_self_check() -> None:
    """A price planted in Crisp's own name MUST be reported, and by attribution rather than nearness.

    ⚠️ THIS CHECK SHIPPED WITHOUT ONE. Its docstring said it "can go red immediately rather than
    needing a baseline" — true, and unproven, because with zero offenders it printed nothing at
    all. A clean run and a blind run were the same silence, which is the exact shape Docket ran
    into (Docket 1.3.40, `6dcf99e`): one empty response testified that a site was missing eight
    things, and read like a finding because nothing distinguished "I looked and it was fine" from
    "I could not look". Its two neighbours here have had a self-check since the day they landed;
    this one went an hour without.
    THE PLANT AND THE COUNTER-PLANT USE THE SAME FIGURE so attribution is the only variable: $149
    in Crisp's name must be caught, and $149 in Topaz's name must not be, because this rule has no
    opinion about rivals — that is what the other two rules are for. A ±90-character window around
    the word "Crisp" reported 45 offenders on a site whose real answer is zero.
    """
    # NOT the home page: a sibling session edits site/index.html, and a plant that is live for a
    # few milliseconds is a plant that can be committed by somebody else.
    page = next(iter(sorted((SITE / "vs").glob("*/index.html"))), None)
    if page is None:
        raise SystemExit("no /vs/ page to self-check against — cannot prove this check works")
    original = page.read_text(encoding="utf-8")
    try:
        page.write_text(original.replace("</body>", "<p>Crisp is $149 once.</p></body>", 1),
                        encoding="utf-8")
        caught = any(v == "149" for _, v, _ in our_price_errors())
        page.write_text(original.replace("</body>", "<p>Topaz Video AI is $149 once.</p></body>", 1),
                        encoding="utf-8")
        false_alarm = any(v == "149" for _, v, _ in our_price_errors())
    finally:
        page.write_text(original, encoding="utf-8")
    if not caught:
        raise SystemExit("a planted “Crisp is $149” was NOT reported — this check cannot fail, "
                         "so its clean output proves nothing")
    if false_alarm:
        raise SystemExit("“Topaz Video AI is $149” was reported as OUR price — this check is "
                         "measuring nearness, not attribution")
    if page.read_text(encoding="utf-8") != original:
        raise SystemExit("the self-check did not restore the page it edited")


def unsourced_report() -> dict:
    return {p.parent.name: sorted({f for f, _ in unsourced_figures(p)})
            for p in sorted((SITE / "vs").glob("*/index.html")) if unsourced_figures(p)}


def main():
    _self_check()          # prove the instrument before believing what it reports
    _unsourced_self_check()
    _ours_self_check()
    ours = our_price_errors()
    if ours:
        print(f"{len(ours)} places give Crisp a price that is not Crisp's:")
        for slug, v, ctx in ours:
            print(f"  {slug}: ${v} — …{ctx}…")
        print("\nOur own price is the one number on this site nobody double-checks, because every "
              "other rule here is about rivals.")
        return 1
    print("no page gives Crisp a price that is not $129 (34 attributed, self-check passed)")
    if "--sources" in sys.argv:
        n = 0
        for page in sorted((SITE / "vs").glob("*/index.html")):
            rows = unsourced_figures(page)
            if not rows:
                continue
            print(f"\n{page.parent.name}")
            for fig, ctx in rows:
                n += 1
                print(f"   ${fig:<10} …{ctx}…")
        print(f"\n{n} rival figures quoted outside the block that cites their source.")
        print("Each is one of: derived arithmetic, a rounding, or a vendor the block never names.")
        return 0
    gaps = survey()
    if "--baseline" in sys.argv:
        BASELINE.write_text(json.dumps(gaps, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        u = unsourced_report()
        UNSOURCED_BASELINE.write_text(json.dumps(u, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
        print(f"baseline recorded: {len(gaps)} pages with no checked date; "
              f"{sum(len(v) for v in u.values())} figures outside their sourced block")
        return 0

    known = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}

    new, worse = [], []
    for slug, figures in gaps.items():
        if slug not in known:
            new.append((slug, figures))
        elif set(figures) - set(known[slug]):
            worse.append((slug, sorted(set(figures) - set(known[slug]))))
    fixed = [s for s in known if s not in gaps]

    print(f"/vs/ pages quoting a rival price with no “Prices checked” date: "
          f"{len(gaps)} ({len(known)} known)")
    for slug in fixed:
        print(f"  FIXED   {slug} — delete its line from {BASELINE.name}")
    for slug, figures in new:
        print(f"  NEW     {slug} — quotes {', '.join('$' + f for f in figures)} "
              f"and says nothing about when that was true")
    for slug, figures in worse:
        print(f"  WORSE   {slug} — new unsourced figures: {', '.join('$' + f for f in figures)}")
    # Second ratchet: figures the page's own block does not record. Separate baseline, because
    # this is a different defect from "no block at all" and mixing them would let a fix to one
    # mask a regression in the other.
    unsourced = unsourced_report()
    if "--baseline" not in sys.argv:
        known_u = (json.loads(UNSOURCED_BASELINE.read_text(encoding="utf-8"))
                   if UNSOURCED_BASELINE.exists() else {})
        new_u = []
        for slug, figs in unsourced.items():
            extra = sorted(set(figs) - set(known_u.get(slug, [])))
            if extra:
                new_u.append((slug, extra))
        print(f"/vs/ figures quoted outside their own sourced block: "
              f"{sum(len(v) for v in unsourced.values())} "
              f"({sum(len(v) for v in known_u.values())} known)")
        for slug, figs in new_u:
            print(f"  NEW     {slug} — {', '.join('$' + f for f in figs)} appears on the page but "
                  f"not in the block that cites the vendor's page")
        if new_u:
            print("\nEither read the figure off the vendor's page and record it in the block, or "
                  "say plainly in the text that it is derived. A date proves somebody looked; it "
                  "does not prove the number was read rather than computed.")
            return 1

    if new or worse:
        print("\nAdd a “Prices checked <date>” block naming the rival's own pricing page and what "
              "it showed, the way /vs/unifab-alternative-mac/ does.")
        return 1
    if not fixed:
        print("no new unsourced rival prices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
