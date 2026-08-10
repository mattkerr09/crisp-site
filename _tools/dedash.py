#!/usr/bin/env python3
"""Bring em-dash density down to something a person would actually type.

Measured on the Crisp corpus: 1311 em-dashes across 63,872 words = 20.5 per 1,000, against a
target of <6. Every other prose signal already passes comfortably (sentence-length CV 0.81,
23% short sentences, ~12 contractions/1k, almost no cliche vocabulary), so the dash rate is
the one thing in the writing itself that reads machine-made.

⚠️ THIS SCRIPT REFUSES RATHER THAN MANGLES. A previous heading-rewriter on the sibling site was
thrown away four times for emitting things like "What hIPAA-conscious healthcare on a Mac
usually ask" — a clean generic beats a mangled specific, every time. So each rewrite here has to
pass a check that it is unambiguous; anything else is left exactly as it was. The goal is not
zero em-dashes (that would read just as odd) but a human rate, reached by converting only the
instances where a comma, colon or full stop is plainly correct.

Rules, in order of confidence:
  1. BRACKETED ASIDE  "A — short aside — B"  -> commas, but only when the aside has no internal
     punctuation and is short. This is the pattern most obviously overused.
  2. TRAILING CLAUSE  "A — B."  where B begins with a determiner/pronoun and the sentence has no
     other comma -> comma. Safe because a comma cannot change the parse here.
  3. Everything else is left alone: dashes next to digits, inside headings, links, code, or
     attributes; any sentence already carrying commas in the relevant span; anything where the
     replacement would sit next to existing punctuation.

Usage:  python3 _tools/dedash.py .            # report only
        python3 _tools/dedash.py . --apply    # rewrite in place
"""
import re
import sys
from pathlib import Path

TARGET_PER_1K = 6.0

# Never touch dashes inside these — markup, code, or numeric ranges.
SKIP_BLOCK = re.compile(r"<(script|style|code|pre|head)\b.*?</\1>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")


def _spans_outside_tags(html: str):
    """Yield (start, end) of text runs inside REAL RUNNING PARAGRAPHS only.

    ⚠️ SCOPE IS THE WHOLE POINT. Measured separately, the corpus splits in two:

        flowing paragraphs (>=25 words) : 18.1 em-dashes per 1k words  <- the tell
        list items (term - definition)  : 30.2 per 1k                  <- correct typography

    An em-dash between a term and its definition is what that mark is FOR, and spec tables use it
    the same way ("Yes - nothing uploaded"). Rewriting those would make the pages worse to read
    while chasing a number. The repeated footer tagline is boilerplate every commercial site has,
    and varying it is pure detection-gaming. So only genuine prose paragraphs are touched.
    """
    blocked = [(m.start(), m.end()) for m in SKIP_BLOCK.finditer(html)]
    for t in ("table", "nav", "footer", "header"):
        for m in re.finditer(rf"<{t}\b.*?</{t}>", html, re.S | re.I):
            blocked.append((m.start(), m.end()))

    def is_blocked(i):
        return any(a <= i < b for a, b in blocked)

    out = []
    for pm in re.finditer(r"<p\b[^>]*>(.*?)</p>", html, re.S | re.I):
        if is_blocked(pm.start()):
            continue
        inner_start = pm.start(1)
        inner = pm.group(1)
        if len(TAG.sub(" ", inner).split()) < 25:      # too short to be running prose
            continue
        pos = 0
        for m in TAG.finditer(inner):
            if m.start() > pos:
                out.append((inner_start + pos, inner_start + m.start()))
            pos = m.end()
        if pos < len(inner):
            out.append((inner_start + pos, inner_start + len(inner)))
    return out


ASIDE = re.compile(r"(?<=\w)\s+—\s+([^—<>,;:()]{1,60}?)\s+—\s+(?=\w)")

# A comma is ALWAYS grammatical before a coordinating conjunction or a contrastive "not",
# so these carry no parse risk whatsoever.
COMMA = re.compile(r"(?<=\w)\s+—\s+(and|but|or|so|yet|nor|not|never|often|usually|always|"
                   r"already|instead|because|which|who|where|while|though|although)\b")

# A trailing appositive that ENDS the sentence is what a colon is for. Only fires when the
# sentence carries no colon already, so we never produce two in one breath.
APPOS_END = re.compile(r"(?<=\w)\s+—\s+((?:the|a|an|one|all|nothing|only|just|no)\b[^.—:<>]{2,90}\.)")
# The same elaboration mid-sentence takes a comma.
APPOS_MID = re.compile(r"(?<=\w)\s+—\s+((?:the|a|an|one|all|nothing|only|just)\b[^,.—:<>]{2,60}\s+)(?=and\b|so\b|but\b)")

# An independent clause after the dash can simply become its own sentence. Restricted to
# openers that are unambiguously subject-initial, so the split cannot produce a fragment.
SPLIT = re.compile(r"(?<=[a-z0-9\)])\s+—\s+(there(?:'s| is| are)|it(?:'s| is)|that(?:'s| is)|"
                   r"this (?:is|means)|these are|they(?:'re| are)|you (?:can|get|see|end|still)|"
                   r"we (?:do|don't|built|keep)|crisp )")


def convert_text(t: str, budget: list) -> str:
    """Rewrite one prose run. `budget` is a one-element list of remaining conversions."""
    def aside(m):
        if budget[0] <= 0:
            return m.group(0)
        inner = m.group(1).strip()
        # A one-word aside is a deliberate beat; leave it.
        if len(inner.split()) < 2:
            return m.group(0)
        budget[0] -= 2          # this removes TWO dashes
        return f", {inner}, "

    def comma(m):
        if budget[0] <= 0:
            return m.group(0)
        budget[0] -= 1
        return f", {m.group(1)}"

    def split(m):
        if budget[0] <= 0:
            return m.group(0)
        budget[0] -= 1
        w = m.group(1)
        return f". {w[0].upper()}{w[1:]}"

    def appos(m):
        """`… — the flat, faded matte finish.` -> a colon, which is what that sentence means."""
        if budget[0] <= 0:
            return m.group(0)
        budget[0] -= 1
        return f": {m.group(1)}"

    def appos_mid(m):
        if budget[0] <= 0:
            return m.group(0)
        budget[0] -= 1
        return f", {m.group(1)}"

    # ⚠️ PAIR GUARD — the single-dash rules must never touch HALF of a bracketing pair.
    # Caught in review: "Giving a clip a cinematic look — or just warming it up, … or making the
    # colours pop — usually means LUTs" had its CLOSING dash turned into a comma, leaving an
    # em-dash opening an aside that a comma then closed. ASIDE deliberately refuses asides
    # containing commas (a comma-laden aside cannot take commas), so nothing else caught it.
    # Rule: run the single-dash rewrites only on sentences holding exactly ONE dash. A pair is
    # either converted atomically by ASIDE or left completely alone.
    out = []
    for sent in re.split(r"(?<=[.!?])(\s+)", t):
        if not sent.strip() or sent.isspace():
            out.append(sent)
            continue
        s2 = ASIDE.sub(aside, sent)
        if s2.count("—") == 1:
            s2 = SPLIT.sub(split, s2)
            s2 = COMMA.sub(comma, s2)
            s2 = APPOS_END.sub(appos, s2)
            s2 = APPOS_MID.sub(appos_mid, s2)
        out.append(s2)
    return "".join(out)


def prose_words(html: str) -> int:
    body = SKIP_BLOCK.sub(" ", html)
    return len(TAG.sub(" ", body).split())


def process(path: Path, apply: bool):
    html = path.read_text(encoding="utf-8")
    words = prose_words(html)
    spans = _spans_outside_tags(html)
    total = sum(html[a:b].count("—") for a, b in spans)
    if not words or not total:
        return None
    density = total * 1000 / words
    if density <= TARGET_PER_1K:
        return (path, density, density, 0)
    # Convert only the excess: keep the dashes that give the prose its voice.
    allowed = max(1, int(TARGET_PER_1K * words / 1000))
    budget = [max(0, total - allowed)]
    before = budget[0]
    out, last = [], 0
    for a, b in spans:
        out.append(html[last:a])
        out.append(convert_text(html[a:b], budget))
        last = b
    out.append(html[last:])
    new = "".join(out)
    converted = before - budget[0]
    after = (total - converted) * 1000 / words
    if apply and converted:
        path.write_text(new, encoding="utf-8")
    return (path, density, after, converted)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    apply = "--apply" in sys.argv
    rows = []
    tot_w = tot_before = tot_after = 0
    for p in sorted(root.glob("**/index.html")):
        r = process(p, apply)
        if not r:
            continue
        path, before, after, n = r
        w = prose_words(path.read_text(encoding="utf-8"))
        tot_w += w
        tot_before += before * w / 1000
        tot_after += after * w / 1000
        if n:
            rows.append((before, after, n, path))
    rows.sort(reverse=True)
    print(f"{'before':>8} {'after':>8} {'conv':>5}  page")
    for b, a, n, p in rows[:20]:
        print(f"{b:8.1f} {a:8.1f} {n:5d}  {p}")
    print(f"\npages changed: {len(rows)}")
    print(f"corpus em-dashes/1k: {tot_before*1000/tot_w:.1f} -> {tot_after*1000/tot_w:.1f} "
          f"(target <{TARGET_PER_1K:.0f})")
    print("REPORT ONLY — pass --apply to write" if not apply else "APPLIED")


if __name__ == "__main__":
    main()
