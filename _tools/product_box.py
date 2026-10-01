"""The in-article product box: right after the answer, and again at the end, on every page that sells.

CEO, 2026-09-28, on Matthew's "make sure those pages and actually all pages are fully optimized to get a
sale" (~/ops/search/WHAT-WORKS-2026-09-28.md, checklist items 1 and 3): a real next step INSIDE the article,
not only the menu button — a product box right after the part that answers the question, and again at the
end, carrying Download free (and the way to Pro — a link to the buy card, not a checkout, so
the checkout exemption stays on the homepage and a Buy event still means a real checkout click), the price with its four-payment split beside it, the founding code,
the requirements and the refund promise. The audit that day found 6 pages with no in-article path at all
and 75 with one, at the very end.

EVERY FIGURE IS READ, NOT TYPED: the price, the founding offer, pay-in-four, the macOS and chip requirements
and the refund window come from llms_txt.facts() — the same reader llms.txt is built from — so a price or a
floor that moves regenerates every box on the next run instead of leaving 118 stale copies.

WHERE:
  top ... after the page's Quick-answer block; a page without one (the hubs) gets it before its first <h2>,
          i.e. right after the intro. Not on legal documents (the terms themselves are not a sales page).
  end ... in place of the old one-button CTA line ("Download Crisp for Mac — Free to try…") where the page
          has it, otherwise before the "Related" heading, otherwise before </article>.
NOT ON: the homepage (it IS the product page), /thank-you/, merge stubs that canonicalise elsewhere, and the
arms of a running experiment (~/ops/search/ARMS.md) — a box is new copy and new links on the arm.

Idempotent: a re-run replaces the boxes it wrote (data-pbox) with freshly generated ones.

    python3 _tools/product_box.py          # apply
    python3 _tools/product_box.py --check  # exit 1 if a page that should carry both boxes does not
"""
from __future__ import annotations

import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llms_txt  # noqa: E402

SITE = Path(__file__).resolve().parents[1]
ARMS_FILE = Path.home() / "ops" / "search" / "ARMS.md"
LEGAL_DOCS = {"legal/terms", "legal/privacy", "legal/refunds"}

OLD_END_CTA = re.compile(
    r'  <p><a class="btn" href="(?:https://crispvideo\.app)?/#download">Download Crisp for Mac</a>[^\n]*?</p>\n')
BOX = re.compile(r'<aside class="pbox" data-pbox="(top|end)">.*?</aside>\n?', re.S)


def arms() -> set[str]:
    if not ARMS_FILE.is_file():
        raise SystemExit("product_box: ~/ops/search/ARMS.md is missing — refusing to guess which pages are experiment arms")
    return {m.group(1) for m in re.finditer(r"^crispvideo\.app \| (/\S+/) \|", ARMS_FILE.read_text(), re.M)}


def box(where: str, page: str = "") -> str:
    f = llms_txt.facts()
    src = (page.strip("/").replace("/", "-") + "-" if page.strip("/") else "") + f"pbox-{where}"
    p, now = f["price"], f["now"]
    q = llms_txt.quarter
    m = llms_txt.money
    split = f'<span class="pbox-split"> · or 4 × {m(q(p))}</span>' if f["bnpl"] else ""
    nsplit = f" · or 4 × {m(q(now))}" if f["bnpl"] else ""
    return (f'<aside class="pbox" data-pbox="{where}">'
            f'<p class="pbox-name"><strong>Crisp Video</strong> restores, denoises and upscales video to 4K on your Mac, offline.</p>'
            f'<p class="pbox-price"><span class="pbox-amt">{m(p)}</span> once{split}</p>'
            f'<p class="pbox-found">Founding price <strong>{m(now)}{nsplit}</strong> for the first {f["first"]} buyers — '
            f'enter <strong>{f["code"]}</strong> at checkout.</p>'
            f'<p class="pbox-actions"><a class="btn" data-track="pbox-{where}" href="{llms_txt.dl_url(src)}">Download free for Mac</a> '
            f'<a class="btn btn-ghost" data-track="pbox-{where}-pro" href="/#buy">See Pro pricing</a></p>'
            f'<p class="pbox-fine">Free to use with a small &ldquo;Made with Crisp&rdquo; mark · {f["os"]} · '
            f'{f["chip"]} · {f["refund_days"]}-day refund, no reason needed.</p>'
            f'</aside>\n')


def page_of(p: Path) -> str:
    return "/" + p.parent.relative_to(SITE).as_posix() + "/"


def targets() -> list[Path]:
    a = arms()
    out = []
    for p in sorted(SITE.rglob("index.html")):
        if ".git" in p.parts or "_tools" in p.parts or p == SITE / "index.html" or p.parent.name == "thank-you":
            continue
        rel = "/" + p.parent.relative_to(SITE).as_posix() + "/"
        s = p.read_text()
        m = re.search(r'<link rel="canonical" href="https://crispvideo\.app(/[^"]*)"', s)
        if (m and m.group(1) != rel) or rel in a:
            continue
        # a noindex page is a door, not an article: /pricing/ and /download/ carry their own box
        # (_tools/landing_pages.py) and must not get two more (2026-10-01)
        if re.search(r'<meta name="robots" content="noindex', s):
            continue
        out.append(p)
    return out


def wants_top(p: Path) -> bool:
    return p.parent.relative_to(SITE).as_posix() not in LEGAL_DOCS


def apply(p: Path) -> bool:
    orig = s = p.read_text()
    if "data-pbox=" in s:
        # regenerate IN PLACE — a re-run must not move a box or leave its indent behind
        s = BOX.sub(lambda m: box(m.group(1), page_of(p)), s)
    else:
        if wants_top(p):
            m = re.search(r'<div class="quick">.*?</div>\n', s, re.S)
            if m:
                s = s[:m.end()] + "      " + box("top", page_of(p)) + s[m.end():]
            else:
                art = s.find("<article")
                h2 = s.find("<h2", art if art >= 0 else 0)
                assert h2 > 0, f"{p}: no Quick answer and no <h2> to place the top box before"
                s = s[:h2] + box("top", page_of(p)) + "  " + s[h2:]
        m = OLD_END_CTA.search(s)
        if m:
            s = s[:m.start()] + "  " + box("end", page_of(p)) + s[m.end():]
        else:
            rel = re.search(r'\n\s*<h2>Related', s)
            at = rel.start() + 1 if rel else s.rfind("</article>")
            if not rel and s[:at].endswith("</div>"):
                at -= len("</div>")          # inside the content column (.wrap), not after it
            assert at > 0, f"{p}: nowhere to place the end box"
            s = s[:at] + "  " + box("end", page_of(p)) + s[at:]
    if s != orig:
        p.write_text(s)
        return True
    return False


def missing(p: Path) -> list[str]:
    s = p.read_text()
    out = []
    if wants_top(p) and s.count('data-pbox="top"') != 1:
        out.append("top box")
    if s.count('data-pbox="end"') != 1:
        out.append("end box")
    for b in BOX.finditer(s):
        if b.group(0).rstrip("\n") != box(b.group(1), page_of(p)).rstrip("\n"):
            out.append(f"stale {b.group(1)} box")
    return out


if __name__ == "__main__":
    pages = targets()
    if "--check" in sys.argv:
        bad = {str(p.relative_to(SITE)): m for p in pages if (m := missing(p))}
        print(f"checked {len(pages)} pages; missing: {bad or 'none'}")
        sys.exit(1 if bad else 0)
    changed = [p for p in pages if apply(p)]
    print(f"updated {len(changed)} of {len(pages)} pages")
