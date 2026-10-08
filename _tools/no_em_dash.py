#!/usr/bin/env python3
"""No em-dash a visitor can see, on any page outside a running experiment (content standard rule 11, 2026-10-07).

Matthew's rule: public text reads like a person wrote it, and an em-dash chain is the commonest tell. The CEO
counted 6-16 visible em-dashes on each of the how-to pages that had just been fixed, and in their titles. This
is the gate and the tool:

    python3 _tools/no_em_dash.py --check     # exit 1 and list every visible em-dash on an unlocked page
    python3 _tools/no_em_dash.py --apply     # rewrite them

"Visible" means what a reader or a search result shows: text outside <script>, <style>, comments, <code>, <pre>
and <kbd>; the <title>; the description and the og:/twitter: title and description; alt, aria-label and title
attributes. JSON-LD is data, not copy, and is left alone.

⛔ QUOTED TEXT IS NEVER REWRITTEN AND NEVER FAILS THE GATE. A dash inside “…” is somebody's words (a vendor's
docs, Crisp's own UI label) and changing it would misquote them. The gate counts only unquoted dashes.
⛔ THE EIGHT HOW-TO ARMS in ~/ops/search/ARMS.md are skipped: their copy is locked until the read is scored.

How --apply chooses, in order: a pair of dashes around an aside becomes commas (brackets if the aside has its own
comma); a short label at the start of a list item, cell, heading or the title takes a colon ("Enhance: AI
upscale…"); a one-word answer ("Yes", "No") takes a full stop; a short tail (seven words or fewer to the end of
the sentence) takes a comma; anything longer becomes its own sentence. Every rewrite keeps the words.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ARMS = Path.home() / "ops" / "search" / "ARMS.md"
DASH = "—"
SKIP_TAGS = ("script", "style", "code", "pre", "kbd", "textarea")
BLOCK = re.compile(r"^(?:p|li|td|th|dt|dd|h[1-6]|div|section|article|aside|figure|figcaption|header|footer|nav|ul|ol|"
                   r"table|tr|tbody|thead|br|title|summary|details|blockquote|main|form|label|option|button)$", re.I)
LABELISH = re.compile(r"^(?:li|td|th|dt|dd|h[1-6]|title|summary|option|label|button)$", re.I)
ATTR_TITLES = ('property="og:title"', 'name="twitter:title"')
ATTR_DESCS = ('name="description"', 'property="og:description"', 'name="twitter:description"')


def arms() -> set[str]:
    try:
        return {l.split("|")[1].strip() for l in ARMS.read_text().splitlines() if l.startswith("crispvideo.app")}
    except FileNotFoundError:
        raise SystemExit("no_em_dash: ~/ops/search/ARMS.md is missing; refusing to guess which pages are locked")


def pages() -> list[Path]:
    locked = arms()
    out = []
    for p in sorted(SITE.rglob("*.html")):
        if ".git" in p.parts or "_tools" in p.parts:
            continue
        rel = "/" + p.parent.relative_to(SITE).as_posix() + "/" if p.name == "index.html" else "/" + p.relative_to(SITE).as_posix()
        rel = "/" if rel == "/./" else rel
        if rel in locked:
            continue
        out.append(p)
    return out


# ---------- visible text with a map back to the source ---------------------------------------------------------
ENT = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")
TAG = re.compile(r"<!--.*?-->|<(/?)([A-Za-z][A-Za-z0-9]*)\b[^>]*>", re.S)


def visible(raw: str):
    """(text, map, blocks): the visible text, each char's (start, end) in raw, and the block tag each char sits in.
    Whitespace inside text reads as a space; only block tags break a line, so a wrapped source line is one line."""
    chars, spans, block_of = [], [], []
    cur_block = "body"
    skip = None

    def take(a, b):
        j = a
        while j < b:
            e = ENT.match(raw, j)
            if raw[j] == "&" and e and e.end() <= b:
                ch = (html.unescape(e.group(0)) or " ")[:1]
                chars.append(" " if ch.isspace() else ch); spans.append((j, e.end())); block_of.append(cur_block); j = e.end()
            else:
                ch = raw[j]
                chars.append(" " if ch.isspace() else ch); spans.append((j, j + 1)); block_of.append(cur_block); j += 1

    i = 0
    for m in TAG.finditer(raw):
        if skip is None and m.start() > i:
            take(i, m.start())
        i = m.end()
        if m.group(0).startswith("<!--"):
            continue
        closing, name = m.group(1), (m.group(2) or "").lower()
        if skip:
            if closing and name == skip:
                skip = None
            continue
        if not closing and name in SKIP_TAGS:
            skip = name
            continue
        if BLOCK.match(name):
            chars.append("\n"); spans.append((m.start(), m.start())); block_of.append(cur_block)
            if not closing:
                cur_block = name
    if skip is None and len(raw) > i:
        take(i, len(raw))
    return "".join(chars), spans, block_of


def in_quotes(text: str, k: int) -> bool:
    start = text.rfind("\n", 0, k) + 1
    seg = text[start:k]
    return seg.count("“") > seg.count("”")


def choose(text: str, k: int, block: str, pair_with: int | None) -> str:
    """The separator for the dash at k (pairs are decided by the caller)."""
    start = text.rfind("\n", 0, k) + 1
    left = text[start:k]
    sent_start = max(left.rfind(". "), left.rfind("? "), left.rfind("! "))
    lead = left[sent_start + 2:] if sent_start >= 0 else left
    end_m = re.search(r"[.!?](?=\s|$)|\n", text[k + 1:])
    right = text[k + 1:k + 1 + (end_m.start() if end_m else len(text) - k - 1)]
    lw, rw = lead.split(), right.split()
    if not rw:
        return "."
    if lead.strip().lower().rstrip(",") in ("yes", "no", "mostly", "partly", "sometimes", "usually", "rarely"):
        return ". "
    if rw[0].lower().strip(",") in ("and", "so", "or", "but", "which", "then", "while", "because", "though", "although", "yet", "nor", "whereas", "unless", "until", "where", "when"):
        return ", "
    if (re.fullmatch(r"h[1-6]|a|title|summary|button", block or "") and len(rw) <= 4
            and re.fullmatch(r"offline|properly|measured|in .+|without .+", right.strip())):
        return ", "      # "Trim your first clip, offline": a tail that says HOW reads as one phrase, not a label
    if len(lw) <= 5 and LABELISH.match(block or "") and sent_start < 0:
        return ": "
    if len(lw) <= 3 and sent_start < 0 and block in ("p", "figcaption", "body", "div"):
        return ": "
    if rw and re.match(r"[\d$£€(“\"]", rw[0]):
        return ": "
    if rw[0].lower() in ("it", "it's", "it’s", "this", "that's", "that’s", "they", "we", "you", "there", "i", "he", "she",
                          "crisp", "topaz", "nothing", "everything", "none", "both", "each", "every", "the"):
        return ". "
    if len(rw) <= 7 or ":" in lead:
        return ", "
    return ": "          # a long tail elaborates; as its own sentence it is usually a fragment


def rewrite(raw: str) -> tuple[str, int]:
    text, spans, block_of = visible(raw)
    idx = [k for k, c in enumerate(text) if c == DASH and not in_quotes(text, k)]
    edits, done = [], set()
    for n, k in enumerate(idx):
        if k in done:
            continue
        line_end = text.find("\n", k)
        line_end = len(text) if line_end < 0 else line_end
        sent = re.search(r"[.!?](?=\s|$)", text[k + 1:line_end])
        stop = k + 1 + (sent.start() if sent else line_end - k - 1)
        partner = next((j for j in idx[n + 1:] if j < stop and j not in done), None)
        if partner is not None:
            aside = text[k + 1:partner]
            edits.append(_edit(raw, spans, k, " (", tight_right=True)); edits.append(_edit(raw, spans, partner, ") "))
            done.update((k, partner))
            continue
        tail = text[k + 1:stop].split()
        if tail and tail[0].lower() in ("checked", "read", "re-read", "measured", "updated", "tested") and len(tail) <= 7 \
                and stop < len(text) and text[stop] in ".!?" and spans[stop][1] - spans[stop][0] == 1:
            edits.append(_edit(raw, spans, k, " (", tight_right=True))
            edits.append((spans[stop][0], spans[stop][0], ")"))
            done.add(k)
            continue
        sep = choose(text, k, block_of[k], None)
        edits.append(_edit(raw, spans, k, sep))
        if sep == ". ":
            nxt = next((q for q in range(k + 1, len(text)) if text[q].isalpha() or text[q] == "\n"), None)
            if nxt is not None and text[nxt] != "\n" and text[nxt].islower():
                a, b = spans[nxt]
                if b - a == 1:
                    edits.append((a, b, raw[a].upper()))
        done.add(k)
    out, last = [], 0
    for st, en, rep in sorted(edits):
        if st < last:
            continue
        out.append(raw[last:st]); out.append(rep); last = en
    out.append(raw[last:])
    return "".join(out), len(done)


def _edit(raw, spans, k, sep, tight_right=False):
    """Replace the dash at visible index k and the spaces around it with sep; a line break after it is kept."""
    s, e = spans[k]
    while s > 0 and raw[s - 1] in " \t":
        s -= 1
    j = e
    while j < len(raw) and raw[j] in " \t\n":
        j += 1
    after = raw[e:j]
    core = sep.strip() if sep.strip() else sep
    lead = " " if sep.startswith(" ") else ""
    if "\n" in after:
        rep = lead + core + after
    elif tight_right:
        rep = lead + core
    else:
        rep = lead + core + (" " if sep.endswith(" ") or after else "")
    return (s, j, rep)


def attrs(raw: str) -> tuple[str, int]:
    n = 0

    def fix_title(v):
        nonlocal n
        k = v.count(DASH) + v.count("&mdash;")
        n += k
        def one(m):
            if re.fullmatch(r"\s*Crisp(?: Video)?\s*", v[m.end():]):
                return " | "          # the brand suffix keeps the site's title separator
            nxt = v[m.end():].split(" ", 1)[0].lower()
            return ", " if nxt in ("and", "so", "or", "but", "which", "then", "while", "because", "though", "although", "yet", "nor", "whereas", "unless", "until", "where", "when") else ": "
        return re.sub(r"\s*(?:\u2014|&mdash;)\s*", one, v)

    def fix_text(v):
        nonlocal n
        plain = html.unescape(v)
        if DASH not in plain:
            return v
        new, k = rewrite(html.escape(plain, quote=False).replace("\n", " "))
        n += k
        return new.replace('"', "&quot;")

    def sub_meta(m):
        tag = m.group(0)
        if not any(a in tag for a in ATTR_TITLES + ATTR_DESCS):
            return tag
        fn = fix_title if any(a in tag for a in ATTR_TITLES) else fix_text
        return re.sub(r'content="([^"]*)"', lambda c: 'content="' + fn(c.group(1)) + '"', tag)

    raw = re.sub(r"<meta\b[^>]*>", sub_meta, raw)
    raw = re.sub(r"(<title>)(.*?)(</title>)", lambda m: m.group(1) + fix_title(m.group(2)) + m.group(3), raw, flags=re.S)
    raw = re.sub(r'\b(alt|aria-label|title)="([^"]*)"', lambda m: f'{m.group(1)}="{fix_text(m.group(2))}"', raw)
    return raw, n


def remaining(raw: str) -> list[str]:
    """Every em-dash a visitor sees, outside quotes: visible text, title, meta titles/descriptions, alt/aria/title."""
    out = []
    text, _, _ = visible(raw)
    for k, c in enumerate(text):
        if c == DASH and not in_quotes(text, k):
            out.append(text[max(0, k - 40):k + 30].replace("\n", " "))
    for m in re.finditer(r"<meta\b[^>]*>", raw):
        t = m.group(0)
        if any(a in t for a in ATTR_TITLES + ATTR_DESCS):
            v = html.unescape((re.search(r'content="([^"]*)"', t) or [None, ""])[1] or "")
            if DASH in v and v.count("“") <= v.count("”") - 0:
                out.append("meta: " + v[:70])
    for m in re.finditer(r'\b(?:alt|aria-label|title)="([^"]*)"', raw):
        v = html.unescape(m.group(1))
        if DASH in v and "“" not in v:
            out.append("attr: " + v[:70])
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    total = conv = 0
    bad = {}
    for p in pages():
        raw = p.read_text(encoding="utf-8")
        if mode == "--apply":
            new, a = attrs(raw)
            new, b = rewrite(new)
            if new != raw:
                p.write_text(new, encoding="utf-8")
            conv += a + b
        left = remaining(p.read_text(encoding="utf-8"))
        if left:
            bad[str(p.relative_to(SITE))] = left
            total += len(left)
    if mode == "--apply":
        print(f"no_em_dash: rewrote {conv} em-dashes")
    if bad:
        print(f"no_em_dash: {total} visible em-dash(es) on {len(bad)} unlocked page(s):")
        for f, items in list(bad.items())[:25]:
            print(f"  {f}: {len(items)} — e.g. …{items[0]}…")
        sys.exit(1)
    print(f"OK: no visible em-dash on any of {len(pages())} unlocked pages (quotes and the {len(arms())} locked arms excepted).")


if __name__ == "__main__":
    main()
