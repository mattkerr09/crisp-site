#!/usr/bin/env python3
"""Structured data may only say what the page says.

    python3 _tools/schema_matches_page.py              # --check (the default): exit 1 on any mismatch
    python3 _tools/schema_matches_page.py --list       # every page with JSON-LD, what was compared, and what failed
    python3 _tools/schema_matches_page.py --selftest   # plant each mismatch and prove it is caught (exit 1 if not)
    python3 _tools/schema_matches_page.py --site DIR   # check another copy of the site (the tests point it at HEAD)

WHY. Google's structured-data rules say the markup must describe content the reader can see: an FAQ question that
exists only in JSON-LD is "content that is not visible to the user", and an Article's headline and dates must be the
page's own. On 2026-10-19 this site carried 346 FAQPage questions on 99 content pages and 166 of them were nowhere on
the page: paraphrases of the visible FAQ (JSON-LD "Does the audio stay in sync when I change the speed?" over a visible
"Does changing speed keep the audio in sync?"), whole FAQ blocks on 22 pages that show no FAQ at all, and one page
(learn/why-topaz-ended-perpetual-licences) whose schema answered three AI-upscaling questions copied from another
page. 10 Article/HowTo headlines were not the H1 (a "(2026)" the H1 does not carry) and 8 datePublished values
disagreed with the byline a reader sees. Nothing checked any of it. Docket's site found the same problem the same day.

WHERE THIS CAME FROM. Docket's scripts/verify_structured_data_matches_page.py, kept in shape (norm / visible / blocks
/ problems / self-test / main, one FAIL line per problem). Changed for Crisp, and each change is deliberate:
  * SITE is this repo itself. Crisp has no build step; these files are what GitHub Pages serves.
  * Pages are every *.html outside _tools/ (and any other _ or . folder), minus the merge stubs whose meta refresh is
    INSTANT (content="0;..."); a page that refreshes later is still read by people and is checked. Labels are the
    folder ("/how-to/trim-video-mac/", "/" for the home page) or the file for a non-index page ("/404.html").
  * Dates are compared with the BYLINE, not searched for anywhere. Crisp's bylines are ISO
    (<div class="updated">Crisp · built in Grand Rapids · published 2026-08-07 · last updated 2026-10-16</div>);
    Docket's "19 October 2026" search would have flagged every page here. datePublished must equal "published" and
    dateModified must equal "last updated". A page with no byline makes no visible date claim and is not
    date-checked (--list says which).
  * The headline must EQUAL the H1, not merely appear somewhere on the page: Docket's "in the visible text" test
    passed "The best video compressor for Mac (2026)" here because "(2026)" was elsewhere. HowTo is checked too, by
    its "name". A trailing " | Crisp" (the <title> form) is NOT accepted: the H1 is the article's title, the brand
    suffix belongs to <title>, and a second accepted form is a second thing to drift. No page needed it.
  * The whole answer must be visible, not its first 80 characters: a paraphrase that kept the opening and rewrote
    the rest would pass a prefix test.
  * Inline tags (strong, a, em, span...) are removed WITHOUT a space and block tags with one, so "<strong>Speed</strong>."
    on the page and "Speed." in the schema compare equal; Docket's tag-to-space turned the first into "speed ." .
  * <head> is not visible text (Docket counted the <title>).
  * NEW: the same FAQ question on two pages with two different answers is reported. That is the shape copied schema
    leaves behind (pasted, then edited on one page), and no single-page check can see it.

Visible text is the <body> with script, style, template, noscript and comments removed, tags stripped as above,
entities decoded, curly quotes and non-breaking spaces normalised, whitespace collapsed, compared case-insensitively.

THE FIX FOR AN FAQ FAILURE is `python3 _tools/faq_jsonld.py --write`, which rebuilds every FAQPage from the page's
visible FAQ. Never fix one by adding visible text to match the schema: the page is the source of truth.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ARTICLE_TYPES = ("Article", "BlogPosting", "TechArticle", "NewsArticle", "HowTo")

# Tags a browser renders inside a run of text: removing them must not split a word or put a space before a full stop.
INLINE = ("a|abbr|b|bdi|bdo|cite|code|data|del|dfn|em|i|ins|kbd|mark|q|s|samp|small|span|strong|sub|sup|time|u|var"
          "|wbr")
_INLINE_TAG = re.compile(rf"</?(?:{INLINE})\b[^>]*>", re.I)
_ANY_TAG = re.compile(r"<[^>]+>")
_FOLD = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', " ": " ", " ": " "})
LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
H1 = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.S | re.I)
BYLINE = re.compile(r'<div class="updated">(.*?)</div>', re.S | re.I)
BYLINE_PUBLISHED = re.compile(r"published (\d{4}-\d{2}-\d{2})")
BYLINE_UPDATED = re.compile(r"last updated (\d{4}-\d{2}-\d{2})")
INSTANT_REFRESH = re.compile(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\']\s*0\s*[;"\']', re.I)


def text_of(x: str) -> str:
    """What a reader reads in an HTML fragment, case and characters kept: tags out (inline ones without a space),
    entities decoded, whitespace collapsed. faq_jsonld.py writes schema text with exactly this function, so a rebuilt
    answer is by construction a run of the page's own visible text."""
    x = _ANY_TAG.sub(" ", _INLINE_TAG.sub("", x or ""))
    return re.sub(r"\s+", " ", html.unescape(x).replace(" ", " ")).strip()


def norm(x: str) -> str:
    """text_of, folded for comparison: curly quotes straight, no-break spaces plain, lower case."""
    return re.sub(r"\s+", " ", text_of(x).translate(_FOLD)).strip().lower()


def visible(page: str) -> str:
    page = re.sub(r"<head\b.*?</head>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<(script|style|template|noscript)\b[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<!--.*?-->", " ", page, flags=re.S)
    return norm(page)


def blocks(page: str):
    for m in LD.finditer(page):
        try:
            data = json.loads(m.group(1))
        except ValueError as exc:
            yield {"_error": str(exc)}
            continue
        items = data.get("@graph", [data]) if isinstance(data, dict) else data
        for it in items if isinstance(items, list) else [items]:
            if isinstance(it, dict):
                yield it


def _types(it: dict) -> list:
    t = it.get("@type")
    return t if isinstance(t, list) else [t]


def faq_pairs(page: str) -> list[tuple[str, str]]:
    """Every (question, answer) the page's FAQPage markup claims, normalised for comparison."""
    out = []
    for it in blocks(page):
        if "_error" not in it and "FAQPage" in _types(it):
            for q in it.get("mainEntity") or []:
                if isinstance(q, dict):
                    out.append((norm(q.get("name")), norm((q.get("acceptedAnswer") or {}).get("text"))))
    return out


def byline_dates(page: str) -> dict:
    """{"datePublished": ..., "dateModified": ...} as the visible byline states them; {} when there is no byline."""
    m = BYLINE.search(page)
    if not m:
        return {}
    line = text_of(m.group(1))
    out = {}
    p, u = BYLINE_PUBLISHED.search(line), BYLINE_UPDATED.search(line)
    if p:
        out["datePublished"] = p.group(1)
    if u:
        out["dateModified"] = u.group(1)
    return out


def problems(page: str) -> list:
    out = []
    vis = visible(page)
    h1m = H1.search(page)
    h1 = norm(h1m.group(1)) if h1m else ""
    shown = byline_dates(page)
    for it in blocks(page):
        if "_error" in it:
            out.append(f"a JSON-LD block does not parse ({it['_error']})")
            continue
        types = _types(it)
        if "FAQPage" in types:
            qs = it.get("mainEntity") or []
            if not qs:
                out.append("an FAQPage with no questions (drop the block rather than ship an empty one)")
            for q in qs:
                if not isinstance(q, dict):
                    out.append(f"an FAQPage entry is not a Question: {q!r}"[:160])
                    continue
                name = norm(q.get("name"))
                if not name:
                    out.append("an FAQ question has no name")
                elif name not in vis:
                    out.append(f"FAQ question not visible on the page: {q.get('name')!r}")
                answer = norm((q.get("acceptedAnswer") or {}).get("text"))
                if not answer:
                    out.append(f"FAQ question has no answer text: {q.get('name')!r}")
                elif answer not in vis:
                    out.append(f"FAQ answer not visible on the page (question {q.get('name')!r}): {answer[:70]!r}...")
        if any(t in ARTICLE_TYPES for t in types):
            kind = next(t for t in types if t in ARTICLE_TYPES)
            raw = it.get("headline") if it.get("headline") else it.get("name")
            head = norm(raw)
            if head and not h1:
                out.append(f"{kind} headline {raw!r} but the page has no H1 to be the headline of")
            elif head and head != h1:
                out.append(f"{kind} {'headline' if it.get('headline') else 'name'} is not the H1: {raw!r} "
                           f"(H1 {text_of(h1m.group(1))!r})")
            for key in ("datePublished", "dateModified"):
                value = it.get(key)
                if not value:
                    continue
                try:
                    d = dt.date.fromisoformat(str(value)[:10]).isoformat()
                except ValueError:
                    out.append(f"{kind} {key} is not a date: {value!r}")
                    continue
                if key in shown and d != shown[key]:
                    label = "published" if key == "datePublished" else "last updated"
                    out.append(f"{kind} {key} {value} is not the byline's \"{label} {shown[key]}\"")
    return out


def copied(faqs: dict, shown: dict | None = None) -> tuple[list[str], list[str]]:
    """{label: [(question, answer)]} -> (FAIL lines, NOTE lines), one per question asked on several pages with
    different answers. It FAILS when some page's copy of the answer is not on that page (the copied-schema shape: the
    per-page check fails too, and this names where the text came from). When every page SHOWS its own answer it is a
    NOTE, not a failure: the same question answered for each page's own subject ("Is my video uploaded anywhere?" on
    a compress page and a border page) is the page talking, and the fix would be a copy change, not a schema one.
    shown = {label: visible text}; without it every group is a FAIL."""
    seen: dict = {}
    for label, pairs in faqs.items():
        for q, a in pairs:
            if q:
                seen.setdefault(q, {})[label] = a
    fail, note = [], []
    for q, by_page in sorted(seen.items()):
        if len(by_page) > 1 and len(set(by_page.values())) > 1:
            hidden = sorted(lab for lab, a in by_page.items() if shown is None or a not in shown.get(lab, ""))
            line = (f"the FAQ question {q!r} is on {len(by_page)} pages with {len(set(by_page.values()))} different "
                    f"answers ({', '.join(sorted(by_page))})")
            if hidden:
                fail.append(f"{line}: copied schema; the answer is not on {', '.join(hidden)}")
            else:
                note.append(f"{line}; every page shows its own, so it is the copy, not the schema, to read again")
    return fail, note


def label_of(f: Path, site: Path) -> str:
    rel = f.relative_to(site)
    if f.name == "index.html":
        parent = rel.parent.as_posix()
        return "/" if parent == "." else f"/{parent}/"
    return f"/{rel.as_posix()}"


def pages(site: Path):
    """(label, html) for every public page carrying JSON-LD, merge stubs and the tools folder left out."""
    for f in sorted(site.rglob("*.html")):
        rel = f.relative_to(site)
        if any(part.startswith(("_", ".")) or part == "node_modules" for part in rel.parts[:-1]):
            continue
        page = f.read_text(encoding="utf-8", errors="replace")
        if INSTANT_REFRESH.search(page) or "application/ld+json" not in page:
            continue
        yield label_of(f, site), page


def self_test() -> int:
    byline = '<div class="updated">Crisp · built in Grand Rapids · published 2026-10-01 · last updated 2026-10-19</div>'
    good = ("<html><head><title>Is it free? | Crisp</title><script type=\"application/ld+json\">"
            + json.dumps({"@context": "https://schema.org", "@graph": [
                {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Is it free?",
                 "acceptedAnswer": {"@type": "Answer", "text": "Yes. Exports up to a minute are free, everything else runs at full length, and a small mark sits in the corner."}}]},
                {"@type": "Article", "headline": "A page about Crisp", "datePublished": "2026-10-01",
                 "dateModified": "2026-10-19"},
                {"@type": "HowTo", "name": "A page about Crisp"}]})
            + "</script></head><body><article><h1>A page <span class=\"grad\">about Crisp</span></h1>" + byline
            + "<h2>Questions</h2><h3>Is it free?</h3><p>Yes. Exports up to a minute are <strong>free</strong>, everything else runs at full length, and a small mark sits in the corner.</p>"
            "</article></body></html>")
    if problems(good):
        print("STRUCTURED DATA self-test FAILED: a page whose markup matches it is reported", problems(good))
        return 1
    planted = {
        "a question that is not on the page": (good.replace("<h3>Is it free?</h3>", "<h3>Is Crisp free?</h3>"),
                                               "question not visible"),
        "an answer that is a paraphrase": (good.replace("<p>Yes. Exports up to", "<p>Yes. Anything up to"),
                                           "answer not visible"),
        "an answer whose ending differs (past Docket's 80-character prefix)": (
            good.replace("sits in the corner.</p>", "sits on the frame.</p>"), "answer not visible"),
        "a headline that is not the H1": (good.replace("about Crisp</span>", "about Crisp, 2026</span>"),
                                          "Article headline is not the H1"),
        "a headline with the title's brand suffix": (good.replace('"headline": "A page about Crisp"',
                                                                  '"headline": "A page about Crisp | Crisp"'),
                                                     "Article headline is not the H1"),
        "a HowTo name that is not the H1": (good.replace('"name": "A page about Crisp"', '"name": "How to do it"'),
                                            "HowTo name is not the H1"),
        "a datePublished that is not the byline's": (good.replace("published 2026-10-01", "published 2026-10-02"),
                                                     "datePublished 2026-10-01 is not the byline"),
        "a dateModified that is not the byline's": (good.replace("last updated 2026-10-19", "last updated 2026-10-18"),
                                                    "dateModified 2026-10-19 is not the byline"),
        "a block that does not parse": (good.replace('"@graph"', '"@graph" x'), "does not parse"),
        "a question that is only inside a script": (good.replace("<h3>Is it free?</h3>",
                                                                 "<script>var q='Is it free?'</script>"),
                                                    "question not visible"),
        "a question that is only in the <title>": (good.replace("<h3>Is it free?</h3>", ""), "question not visible"),
        "an empty FAQPage": (good.replace(json.dumps([{"@type": "Question", "name": "Is it free?", "acceptedAnswer": {
            "@type": "Answer", "text": "Yes. Exports up to a minute are free, everything else runs at full length, and a small mark sits in the corner."}}]), "[]"), "no questions"),
    }
    missed = []
    for what, (page, needle) in planted.items():
        if page == good:
            missed.append(f"{what}: the plant did not change the page (the self-test itself is broken)")
        elif not any(needle in p for p in problems(page)):
            missed.append(f"{what}: not caught ({problems(page)})")
    # copied schema needs two pages
    two = {"/a/": [("is it free?", "yes.")], "/b/": [("is it free?", "no.")]}
    if not copied(two, {"/a/": "is it free? yes.", "/b/": "is it free? yes."})[0]:
        missed.append("one question, two answers, one of them not on its page: not a FAIL")
    fail, note = copied(two, {"/a/": "is it free? yes.", "/b/": "is it free? no."})
    if fail or not note:
        missed.append("one question, two answers, each shown on its own page: should be a NOTE, not a FAIL")
    if any(copied({"/a/": [("is it free?", "yes.")], "/b/": [("is it free?", "yes.")], "/c/": [("why?", "b.")]})):
        missed.append("one question with ONE answer on two pages was reported as copied with different answers")
    # merge stubs skipped, folders labelled the way the site is laid out
    stub = '<meta http-equiv="refresh" content="0; url=/how-to/">'
    if not INSTANT_REFRESH.search(stub) or INSTANT_REFRESH.search('<meta http-equiv="refresh" content="30">'):
        missed.append("the instant-refresh stub test is wrong")
    if label_of(SITE / "index.html", SITE) != "/" or label_of(SITE / "how-to" / "x" / "index.html", SITE) != "/how-to/x/":
        missed.append("page labels do not follow the folder/index.html layout")
    # ...and on a REAL page: change one visible FAQ question, and the check must notice.
    real = next(((lab, pg) for lab, pg in pages(SITE) if faq_pairs(pg)), None)
    if real is None:
        missed.append("no page on the site carries an FAQPage to plant into (the self-test could not look)")
    else:
        lab, pg = real
        q0 = next(it for it in blocks(pg) if "FAQPage" in _types(it))["mainEntity"][0]["name"]
        heads = [m for m in re.finditer(r"(<h[2-4]\b[^>]*>)(.*?)(</h[2-4]>)", pg, re.S) if norm(m.group(2)) == norm(q0)]
        if not heads:
            missed.append(f"{lab}: its first FAQ question {q0!r} is not a visible heading, so nothing could be planted")
        else:
            m = heads[0]
            planted_pg = pg[:m.start(2)] + "A question this page never asked?" + pg[m.end(2):]
            if len(problems(planted_pg)) <= len(problems(pg)):
                missed.append(f"{lab}: renaming its visible question {q0!r} went unseen")
    if missed:
        print("STRUCTURED DATA self-test FAILED: this check cannot see")
        for m in missed:
            print("  " + m)
        return 1
    print(f"STRUCTURED DATA self-test ok: {len(planted)} planted single-page mismatches and 3 cross-page cases "
          f"judged right, a real page ({real[0]}) with one visible question renamed caught, merge stubs and labels "
          "as laid out")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv or "--self-test" in argv:
        return self_test()
    site = SITE
    if "--site" in argv:
        site = Path(argv[argv.index("--site") + 1]).resolve()
    listing = "--list" in argv
    # A gate that cannot see must not pass: prove it can fail before believing its green (exit 3 = BLIND).
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()) as said:
        blind = self_test()
    if blind:
        print(said.getvalue().rstrip())
        print("STRUCTURED DATA BLOCKED: the self-test failed, so a clean run below would prove nothing")
        return 3
    checked = failed = n_q = n_art = undated = 0
    faqs, shown = {}, {}
    for label, page in pages(site):
        checked += 1
        found = problems(page)
        faqs[label] = faq_pairs(page)
        if faqs[label]:
            shown[label] = visible(page)
        n_q += len(faqs[label])
        arts = sum(1 for it in blocks(page) if "_error" not in it and any(t in ARTICLE_TYPES for t in _types(it)))
        n_art += arts
        if arts and not byline_dates(page):
            undated += 1
        if listing:
            print(f"  {'FAIL' if found else 'ok  '}  {label}  faq={len(faqs[label])} article={arts} "
                  f"byline={'yes' if byline_dates(page) else 'no'}")
        for p in found:
            failed += 1
            print(f"  FAIL  {label}: {p}")
    fail_copied, notes = copied(faqs, shown)
    for p in fail_copied:
        failed += 1
        print(f"  FAIL  {p}")
    for p in notes:
        print(f"  NOTE  {p}")
    if checked == 0:
        print(f"STRUCTURED DATA BLOCKED: no page with JSON-LD under {site}; a check that read nothing proves nothing")
        return 3
    if failed:
        print(f"STRUCTURED DATA: {failed} problem(s) on {checked} pages with JSON-LD. Markup may only describe what the "
              "reader can see; for FAQs run _tools/faq_jsonld.py --write (the visible FAQ is the source), for a "
              "headline use the H1, for a date the byline.")
        return 1
    print(f"STRUCTURED DATA ok: {checked} pages, {n_q} FAQ questions and answers, {n_art} Article/HowTo headlines on "
          f"their own page ({undated} of those pages have no byline, so no date to compare; {len(notes)} NOTE)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
