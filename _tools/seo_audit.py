#!/usr/bin/env python3
"""Per-page audit table: what Google did with each page, and the two things that predict it.

SEO order 4 asks for every page compared against the pages that earn clicks, recorded in the
repo "so the next cycle can see what moved". A static file could not do that, so this GENERATES
the table and is meant to be re-run.

WHAT IT MEASURES, AND WHY THESE TWO COLUMNS.

  chars  — visible body text. The standing order said thicken the thin pages, on ten indexed
           pages measuring 6,058 against 4,436. Measured across all 120 with one instrument
           that does not reproduce: the pages Google FETCHED AND DECLINED are, if anything,
           slightly thicker than the indexed ones. Kept in the table as the refutation, not as
           a lever.
  sim    — max Jaccard of this page's visible words against every other page in its family.
           This one is monotone with Google's own ladder: indexed < fetched-and-declined <
           never-fetched. Age is not the explanation (44 of 46 how-to pages were created in the
           same month) and neither is shared template furniture (stripping every fragment that
           appears on half the pages moves 8 words of 304).
  sim*   — the same, EXCLUDING the single nearest page. Two genuinely adjacent topics that
           reference each other on purpose — grain and vignette, reverse and fade — pin each
           other's `sim` and cannot be separated by rewriting. `sim*` is the number to act on;
           `sim` is the number to explain.

⚠️ Unigram Jaccard, not shingles. An 8-word-shingle Jaccard scores an 80%-word copy at 0.112,
so on that scale a real sibling pair reads as "barely similar" and the whole table would invert
its own meaning. Calibrated against three controls: a page against itself (1.000), against an
unrelated page (~0.11), and against a copy of itself with 20% of words dropped (0.879).

    python3 _tools/seo_audit.py            # write docs/seo-audit-2026-09.md
    python3 _tools/seo_audit.py --stdout   # print it instead
"""
from __future__ import annotations

import re
import statistics
import sys
from collections import Counter
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
BUCKETS = Path.home() / "ops/search/crisp-not-indexed-2026-09-07.md"
OUT = SITE / "docs/seo-audit-2026-09.md"


def visible(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    body = m.group(1) if m else html
    body = re.sub(r"<(script|style|nav|footer|header)\b.*?</\1>", "", body, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def buckets() -> tuple[set[str], set[str]]:
    """The console's own two not-indexed lists. Empty sets if the file is not present."""
    if not BUCKETS.exists():
        return set(), set()
    section, crawled, never = None, [], []
    for line in BUCKETS.read_text().split("\n"):
        if line.startswith("## The 41"):
            section = "c"
        elif line.startswith("## ") and section == "c":
            section = "n"
        m = re.match(r"\|\s*\d+\s*\|\s*(/[^\s|]*)\s*\|", line)
        if m:
            (crawled if section == "c" else never).append(m.group(1))
    return set(crawled), set(never)


def main() -> int:
    crawled, never = buckets()
    pages: dict[str, dict] = {}
    for f in sorted(SITE.rglob("index.html")):
        if "_tools" in f.parts:
            continue
        rel = f.parent.relative_to(SITE)
        url = "/" if str(rel) == "." else f"/{rel}/"
        text = visible(f.read_text())
        pages[url] = {"chars": len(text), "words": words(text),
                      "family": (str(rel).split("/")[0] if str(rel) != "." else "(home)")}

    # inbound internal anchors, absolute hrefs included, canonicals excluded
    inbound = Counter()
    for f in sorted(SITE.rglob("index.html")):
        if "_tools" in f.parts:
            continue
        html = re.sub(r'<link[^>]+rel="canonical"[^>]*>', "", f.read_text())
        here = "/" if str(f.parent.relative_to(SITE)) == "." else f"/{f.parent.relative_to(SITE)}/"
        for href in re.findall(r'href="(?:https://crispvideo\.app)?(/[^"#?]*)"', html):
            target = href if href.endswith("/") else href + "/"
            if target in pages and target != here:
                inbound[target] += 1

    for url, p in pages.items():
        fam = [q for q, o in pages.items() if o["family"] == p["family"] and q != url]
        sims = sorted((jaccard(p["words"], pages[q]["words"]) for q in fam), reverse=True)
        p["sim"] = sims[0] if sims else 0.0
        p["sim2"] = sims[1] if len(sims) > 1 else 0.0
        p["in"] = inbound[url]
        p["bucket"] = ("declined" if url in crawled else
                       "never-fetched" if url in never else "indexed?")

    order = {"indexed?": 0, "declined": 1, "never-fetched": 2}
    rows = sorted(pages.items(), key=lambda kv: (order[kv[1]["bucket"]], -kv[1]["sim2"]))
    L = ["# crispvideo.app — per-page audit", "",
         "Generated by `_tools/seo_audit.py`. Re-run it to see what moved.", "",
         "`sim` is max word-overlap with a page in the same family; `sim*` excludes the single",
         "nearest page, because two adjacent topics pin each other and rewriting cannot separate",
         "them. **Act on `sim*`.**", "",
         "## What this table established, stated no more strongly than it holds", "",
         "**Two things are NOT the discriminator, and both were proposed as levers.** Body length:",
         "the pages Google fetched and declined are slightly THICKER than the indexed ones, so the",
         "thicken-the-thin-pages order is refuted on its own site. Internal links: the not-indexed",
         "pages carry MORE inbound anchors than the indexed ones, so link-the-orphans is refuted",
         "too. Both columns stay in the table as the refutation.", "",
         "**Sibling similarity is a real signal in `how-to` and does not generalise.** Inside that",
         "family — the only one with enough pages to see anything — it runs 0.219 indexed, 0.315",
         "fetched-and-declined, 0.388 never-fetched, and holds after controlling for page age and",
         "for shared template text. In `learn` it is flat (0.245 / 0.240 / 0.250). In `vs` it is",
         "non-monotone: the declined pages score HIGHEST (0.388) and the never-fetched ones score",
         "the same as the indexed ones. In `for` it is mildly inverted. I first reported the ladder",
         "as a site-wide result; it is one family's result, resting on a single indexed page.", "",
         "So the honest reading is: differentiating a near-duplicate how-to is worth doing on its",
         "own merits — each page ends up carrying facts only it can carry — but nothing here",
         "licenses a claim that similarity CAUSES the indexing decision, and nothing here explains",
         "`learn` or `vs` at all. The next cycle should look for a different variable in those two",
         "rather than apply the how-to lever to them.", ""]
    for b in ("indexed?", "declined", "never-fetched"):
        g = [(u, p) for u, p in rows if p["bucket"] == b]
        if not g:
            continue
        L += [f"## {b} — {len(g)} pages", "",
              "| page | family | chars | sim | sim* | inbound |",
              "|---|---|---|---|---|---|"]
        L += [f"| {u} | {p['family']} | {p['chars']} | {p['sim']:.3f} | "
              f"{p['sim2']:.3f} | {p['in']} |" for u, p in g]
        L.append("")
    L += ["## What the columns say", ""]
    for b in ("indexed?", "declined", "never-fetched"):
        g = [p for _, p in rows if p["bucket"] == b]
        if not g:
            continue
        L.append(f"- **{b}** ({len(g)}): median chars "
                 f"{statistics.median(p['chars'] for p in g):.0f}, median sim "
                 f"{statistics.median(p['sim'] for p in g):.3f}, median sim* "
                 f"{statistics.median(p['sim2'] for p in g):.3f}, median inbound "
                 f"{statistics.median(p['in'] for p in g):.0f}")
    L += ["", "## Per family, which is where the signal actually lives", "",
          "| family | indexed? sim* | declined sim* | never-fetched sim* |", "|---|---|---|---|"]
    for fam in sorted({p["family"] for p in pages.values()}):
        cells = []
        for b in ("indexed?", "declined", "never-fetched"):
            g = [p["sim2"] for p in pages.values() if p["family"] == fam and p["bucket"] == b]
            cells.append(f"{statistics.median(g):.3f} (n={len(g)})" if g else "—")
        L.append(f"| {fam} | " + " | ".join(cells) + " |")
    L += ["", "⚠️ **Read this table before quoting the one above.** Site-wide, `sim` separates",
          "indexed from not-indexed but does NOT separate *declined* from *never-fetched* — those",
          "two are flat within noise. The clean three-step ladder holds inside `how-to`, the one",
          "family big enough to see it, and was reported site-wide when it should not have been.",
          "", "⚠️ And the indexed group's low similarity is partly composition, not cause: it",
          "contains the home page and the legal pages, which are unique by their nature and would",
          "score low whatever Google did with them. The comparison to trust is within one family."]
    text = "\n".join(L) + "\n"
    if "--stdout" in sys.argv:
        print(text)
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(SITE)} — {len(pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
