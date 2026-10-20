#!/usr/bin/env python3
"""Build every page's FAQPage structured data FROM the FAQ the page shows.

    python3 _tools/faq_jsonld.py            # report what would change, page by page (writes nothing)
    python3 _tools/faq_jsonld.py --write    # rewrite every FAQPage block from its page's visible FAQ
    python3 _tools/faq_jsonld.py --check    # exit 1 if any FAQPage is not exactly its page's visible FAQ
    python3 _tools/faq_jsonld.py --site DIR # any of the above on another copy of the site

WHY. On 2026-10-19, 166 of the 346 FAQ questions in this site's JSON-LD were not on their pages. They were written
twice, once as the visible <h3>/<p> FAQ and once, separately, as schema, and the two drifted into paraphrases of each
other ("Does the audio stay in sync when I change the speed?" in the schema, "Does changing speed keep the audio in
sync?" on the page). 22 pages carried an FAQPage and showed no FAQ at all, one of them answering three questions
copied from another page. Two hand-kept copies of one text will always drift, so there is now one copy: the page.
The schema is derived from it, and _tools/schema_matches_page.py (a pre-push gate) fails the push when they differ.

WHAT IS "THE PAGE'S FAQ". Inside <article>, the <h2> section with the most question headings (<h3>/<h4> whose text
ends in "?"); a tie goes to the later section, because the FAQ closes the article and a callout box with a question
heading sits earlier ("Where Crisp wins" > "Is the quality actually good?"). Each question's answer is the run of
<p>, <ul> and <ol> directly after it, stopping at the next heading, any other element (the product box <aside>
that follows the last answer is not part of it) or a paragraph holding a class="btn" link (new_pages.py's download
call-to-action sits directly under the last answer). Text is taken with schema_matches_page.text_of, the function the
gate compares with, so a rebuilt answer is by construction a run of the page's own visible text.

THE RULES IT KEEPS.
  * Never invents: a question goes into the schema only if the page shows it, and a schema question with no visible
    counterpart is DROPPED, never "fixed" by adding visible text. A page that shows no FAQ loses its FAQPage block
    (an empty FAQPage is invalid; a page without one makes no FAQ claim).
  * Never adds a block to a page that had none: whether a page carries FAQ markup at all is an editorial choice.
  * Changes only mainEntity. Every other key, and the block's layout (one line or one question per line, compact or
    spaced separators), is kept.
  * Writes text, not markup: the answer is plain text with entities decoded (Google accepts some HTML in an Answer,
    but plain text is what every consumer reads the same way, and what the gate compares).

new_pages.py and ../scripts/seo_render.py build their FAQ schema through rebuild() too, so a generated page cannot be
born with the drift this removes.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_matches_page import LD, norm, text_of  # noqa: E402  (one definition of visible text, shared with the gate)

SITE = Path(__file__).resolve().parent.parent
ARTICLE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.S | re.I)
BODY = re.compile(r"<body\b[^>]*>(.*)</body>", re.S | re.I)
HEADING = re.compile(r"<(h[1-6])\b[^>]*>(.*?)</\1>", re.S | re.I)
ANSWER_PART = re.compile(r"\s*<(p|ul|ol)\b[^>]*>(.*?)</\1>", re.S | re.I)
HIDDEN = re.compile(r"<(script|style|template|noscript)\b[^>]*>.*?</\1>|<!--.*?-->", re.S | re.I)


def visible_faq(page: str) -> list[tuple[str, str]]:
    """[(question, answer)] exactly as the page shows them, in page order. [] when the page shows no FAQ."""
    m = ARTICLE.search(page) or BODY.search(page)
    body = HIDDEN.sub(" ", m.group(1) if m else page)
    heads = list(HEADING.finditer(body))
    sections: list[list] = []
    for i, h in enumerate(heads):
        level = h.group(1).lower()
        if level in ("h1", "h2"):
            sections.append([h, []])
        elif level in ("h3", "h4") and sections and text_of(h.group(2)).endswith("?"):
            sections[-1][1].append(i)
    order = {id(s): k for k, s in enumerate(sections)}
    asked = [s for s in sections if s[1]]
    if not asked:
        return []
    _, idxs = max(asked, key=lambda s: (len(s[1]), order[id(s)]))
    out = []
    for i in idxs:
        end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        region, pos, parts = body[heads[i].end():end], 0, []
        while True:
            a = ANSWER_PART.match(region, pos)
            if not a or 'class="btn' in a.group(2):
                break                     # a call-to-action button is never part of an answer
            parts.append(text_of(a.group(2)))
            pos = a.end()
        answer = " ".join(p for p in parts if p)
        if answer:
            out.append((text_of(heads[i].group(2)), answer))
    return out


def _serialise(obj: dict, like: str) -> str:
    """obj as JSON in the layout of the block it replaces, safe inside a <script> element."""
    spaced = '": "' in like or '", "' in like
    seps = (", ", ": ") if spaced else (",", ":")
    if "\n" in like.strip():
        placeholder = "\u0000MAINENTITY\u0000"
        head = json.dumps({**obj, "mainEntity": placeholder}, ensure_ascii=False, separators=seps)
        rows = ",\n".join(json.dumps(q, ensure_ascii=False, separators=seps) for q in obj["mainEntity"])
        text = head.replace(json.dumps(placeholder), "[\n" + rows + "\n]")
    else:
        text = json.dumps(obj, ensure_ascii=False, separators=seps)
    return text.replace("</", "<\\/").replace("<!--", "<\\!--")


def _faq_block(page: str):
    for m in LD.finditer(page):
        try:
            data = json.loads(m.group(1))
        except ValueError:
            continue                      # the gate reports a block that does not parse; nothing to rebuild from
        if isinstance(data, dict) and data.get("@type") == "FAQPage":
            return m, data
        if isinstance(data, dict) and any(isinstance(it, dict) and it.get("@type") == "FAQPage"
                                          for it in data.get("@graph", [])):
            raise ValueError("an FAQPage inside an @graph: this tool does not rewrite graphs; edit it by hand")
    return None, None


def rebuild(page: str) -> tuple[str, dict]:
    """(page with its FAQPage rebuilt from its visible FAQ, what changed). A page with no FAQPage is returned as is."""
    m, data = _faq_block(page)
    if m is None:
        return page, {"action": "none", "old": [], "new": visible_faq(page)}
    old = [(q.get("name", ""), (q.get("acceptedAnswer") or {}).get("text", ""))
           for q in data.get("mainEntity") or [] if isinstance(q, dict)]
    shown = visible_faq(page)
    info = {"old": old, "new": shown}
    if not shown:
        start, end = m.start(), m.end()
        line_start = page.rfind("\n", 0, start) + 1
        if not page[line_start:start].strip() and page[end:end + 1] == "\n":
            start, end = line_start, end + 1
        return page[:start] + page[end:], {**info, "action": "dropped"}
    entity = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in shown]
    if data.get("mainEntity") == entity:
        return page, {**info, "action": "unchanged"}
    content = m.group(1)
    lead = content[:len(content) - len(content.lstrip())]
    trail = content[len(content.rstrip()):]
    new = lead + _serialise({**data, "mainEntity": entity}, content) + trail
    assert json.loads(new)["mainEntity"] == entity
    return page[:m.start(1)] + new + page[m.end(1):], {**info, "action": "rebuilt"}


def _explain(info: dict):
    """kept / rewritten from a paraphrase / dropped / newly marked up, for the report only (nothing is decided by it).
    Old and visible questions are paired best-first on how alike their question AND answer read."""
    old, new = info["old"], info["new"]
    sim = lambda a, b: difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()  # noqa: E731
    exact = [(i, j) for i, (q, _) in enumerate(old) for j, (v, _) in enumerate(new) if norm(q) == norm(v)]
    used_o, used_n = {i for i, _ in exact}, {j for _, j in exact}
    rewritten = sum(1 for i, j in exact if norm(old[i][1]) != norm(new[j][1]))
    scored = sorted(((0.5 * sim(q, v) + 0.5 * sim(a, b), i, j) for i, (q, a) in enumerate(old) if i not in used_o
                     for j, (v, b) in enumerate(new) if j not in used_n), reverse=True)
    para = []
    for score, i, j in scored:
        if score >= 0.45 and i not in used_o and j not in used_n:
            para.append((old[i][0], new[j][0]))
            used_o.add(i)
            used_n.add(j)
    dropped = [q for i, (q, _) in enumerate(old) if i not in used_o]
    added = [v for j, (v, _) in enumerate(new) if j not in used_n]
    info["counts"] = {"was": len(old), "now": len(new), "matched": len(exact), "answer_rewritten": rewritten,
                      "paraphrase": len(para), "dropped": len(dropped), "added": len(added)}
    return (f"{len(new)} questions now (was {len(old)}): {len(exact)} already matched ({rewritten} of their answers "
            f"rewritten to the visible text), {len(para)} paraphrases replaced by the visible wording, {len(dropped)} "
            f"dropped (not on the page), {len(added)} visible questions newly marked up"), para, dropped


def main(argv: list[str]) -> int:
    write, check = "--write" in argv, "--check" in argv
    site = Path(argv[argv.index("--site") + 1]).resolve() if "--site" in argv else SITE
    changed, totals = [], {"rebuilt": 0, "dropped": 0, "unchanged": 0}
    for f in sorted(site.rglob("*.html")):
        rel = f.relative_to(site)
        if any(part.startswith(("_", ".")) or part == "node_modules" for part in rel.parts[:-1]):
            continue
        page = f.read_text(encoding="utf-8")
        if '"FAQPage"' not in page:
            continue
        new, info = rebuild(page)
        if info["action"] == "none":
            continue
        totals[info["action"]] += 1
        if new == page:
            continue
        changed.append(rel.as_posix())
        summary, para, dropped = _explain(info)
        print(f"  {'WROTE' if write else 'WOULD'} {info['action']:8s} {rel.parent.as_posix()}: {summary}")
        if not check:
            for old_q, new_q in para:
                print(f"      {old_q!r}  ->  {new_q!r}")
            for q in dropped:
                print(f"      dropped {q!r}")
        if write:
            f.write_text(new, encoding="utf-8")
    print(f"FAQ JSON-LD: {totals['rebuilt']} rebuilt, {totals['dropped']} dropped (page shows no FAQ), "
          f"{totals['unchanged']} already the visible FAQ" + ("" if write else "; nothing written (pass --write)"))
    if check and changed:
        print(f"FAQ JSON-LD is not the visible FAQ on {len(changed)} pages: run python3 _tools/faq_jsonld.py --write")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
