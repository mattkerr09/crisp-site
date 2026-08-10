#!/usr/bin/env python3
"""Emit new learn/ articles using the site's existing page scaffolding.

Why learn/ and not more how-to/: measured against the sibling site, which is the model Matt asked
to copy, the shape is 51 learn pages to 16 how-to. Crisp is the inverse — 40 how-to and 2 learn —
so the task pages are well covered and the concept pages barely exist. learn/ answers "why is my
video like this", how-to/ answers "how do I do X". They compete for different queries and can't
cannibalise each other.

⚠️ NOT copied from the sibling site: its /seo/ set, 61 programmatically templated pages that
already threw near-duplicate shingle errors and are the one genuinely machine-generated thing
over there. Copying the volume would import the liability.

⚠️ Every capability claim below was checked against the shipping code before it was written:
frame interpolation is real (RIFE, vendored, wired NL->plan->UI->job); image upscaling is real
(pipeline.upscale_image, 9 image formats); convert targets mp4/mov. Nothing here promises a
feature Crisp does not have.

⚠️ House style, enforced on myself: em-dashes stay rare (the corpus was just cut from 18.1 to
11.6 per 1k for exactly this reason), contractions are normal, sentence length varies, and the
five articles deliberately do NOT share one skeleton — that sameness across pages is the tell,
not the prose.
"""
import re
import sys
from pathlib import Path

SITE = "https://crispvideo.app"

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="description" content="{desc}">
<meta name="theme-color" content="#060810">
<link rel="canonical" href="{site}/{slug}/">
<meta property="og:type" content="article">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}/{slug}/">
<meta property="og:site_name" content="Crisp">
<meta property="og:image" content="{site}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{ogtitle}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{site}/og.png">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{article_ld}</script>
<script type="application/ld+json">{faq_ld}</script>
</head>
<body>
<nav><div class="wrap nav-inner">
  <a class="nav-brand" href="{site}/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><circle cx="12" cy="12" r="3.2"/></svg> Crisp</a>
  <a class="btn" href="{site}/#download">Download for Mac</a>
</div></nav>

<article><div class="wrap">
  <div class="crumb"><a href="{site}/">Crisp</a> &rsaquo; Learn &rsaquo; {crumb}</div>
  <h1>{h1}</h1>
{body}
  <h2>{faq_heading}</h2>
{faq_html}
  <p><a class="btn" href="{site}/#download">Download Crisp for Mac</a> Free to try, one-time $19 to remove the watermark. Runs entirely on your Mac.</p>
</div></article>

<footer><div class="wrap">
  <p>&#9670; <strong style="color:var(--text-mid)">Crisp</strong> &mdash; offline AI video &amp; photo upscaler + auto-editor for Mac. <a href="{site}/">crispvideo.app</a></p>
</div></footer>
</body>
</html>
"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build(page):
    faq_html = "\n".join(
        f"  <h3>{q}</h3>\n  <p>{a}</p>" for q, a in page["faq"])
    article_ld = ('{"@context":"https://schema.org","@type":"Article","headline":"%s",'
                  '"description":"%s","author":{"@type":"Organization","name":"Crisp"},'
                  '"publisher":{"@type":"Organization","name":"Crisp"},"datePublished":"2026-08-10"}'
                  % (esc(page["h1"]), esc(page["desc"])))
    qs = ",".join('{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}'
                  % (esc(q), esc(re.sub(r"<[^>]+>", "", a))) for q, a in page["faq"])
    faq_ld = '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[%s]}' % qs
    return HEAD.format(site=SITE, slug=page["slug"], title=page["title"], desc=esc(page["desc"]),
                       ogtitle=esc(page["h1"]), crumb=page["crumb"], h1=page["h1"],
                       body=page["body"], faq_heading=page["faq_heading"], faq_html=faq_html,
                       article_ld=article_ld, faq_ld=faq_ld)


def main():
    from pages_learn import PAGES
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    apply = "--apply" in sys.argv
    for page in PAGES:
        out = root / page["slug"] / "index.html"
        words = len(re.sub(r"<[^>]+>", " ", page["body"] + " ".join(a for _, a in page["faq"])).split())
        status = "EXISTS-SKIP" if out.exists() else ("WRITE" if apply else "WOULD")
        print(f"  {status:12s} {page['slug']:46s} {words:5d}w")
        if apply and not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(build(page), encoding="utf-8")
    print("REPORT ONLY — pass --apply" if not apply else "APPLIED")


if __name__ == "__main__":
    main()
