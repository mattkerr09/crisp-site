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
import json
import re
import sys
from pathlib import Path

SITE = "https://crispvideo.app"
#: The price, declared once. This generator said $19 through TWO portfolio-wide
#: price changes (19->39 in e2769c6, 39->99 in 6cbe217) because both sweeps
#: corrected the PUBLISHED pages and never the thing that writes them. A bare
#: 19->99 rewrite would just reset that clock a third time.
#:
#: This site repo is nested and gitignored by the app repo, so it cannot import
#: entitlement.PRICE_USD. One declared constant per repo is the achievable
#: single source; keep it equal to entitlement.PRICE_USD.
PRICE_USD = 129

#: ⚠️ THE ANALYTICS + PIXEL LINE IS PART OF THE TEMPLATE, NOT AN AFTERTHOUGHT.
#: Until 2026-08-23 this HEAD carried neither, so every page this tool emitted was
#: born with no Plausible and no Meta pixel. That was survivable while the pixel
#: lived on one page by hand. It stopped being survivable the moment
#: /legal/privacy/ was corrected to read "EVERY page on this site loads" both of
#: them — a generated page missing them makes the privacy policy false, and it
#: would do so silently, on a page nobody re-reads after creating.
#:
#: Copied byte-for-byte from a shipped page rather than retyped, so the template
#: cannot drift from what the other 115 carry. The braces are doubled because
#: HEAD is consumed by str.format(); the fbq('init','…') call contains none, but
#: the pixel's own IIFE does.
#:
#: If the pixel id ever changes, ops/bin/insert-meta-pixel.py rewrites the 115
#: pages AND this line must move with them. Grep the id, do not trust one place.
#:
#: ⚠️ THE AFFILIATE SNIPPET LINE BELOW IT IS THE SAME LESSON, LEARNED LATE. /legal/privacy/
#: says "Affiliate referrals, on every page" and names snippet.js, and all 124 shipped HTML
#: files carry it — but this HEAD did not, so the next page this tool wrote would have made
#: that sentence false exactly the way the pixel once did. Copied byte for byte from a
#: shipped page (2026-09-26), markers included.
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
<meta property="og:image" content="{site}/og.png?v=20260924">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{ogtitle}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{site}/og.png?v=20260924">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{article_ld}</script>
<script type="application/ld+json">{faq_ld}</script>
<script defer data-domain="crispvideo.app" src="https://plausible.io/js/script.js"></script><!-- meta-pixel:begin --><script>!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version="2.0";n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,"script","https://connect.facebook.net/en_US/fbevents.js");fbq('init','1734031344415692');fbq('track','PageView');</script><!-- meta-pixel:end -->
<!-- affiliate-hub:begin --><script src="https://kerr-affiliate-hub.kerrco.workers.dev/snippet.js" defer></script><!-- affiliate-hub:end -->
</head>
<body>
<nav><div class="wrap nav-inner">
  <a class="nav-brand" href="{site}/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><circle cx="12" cy="12" r="3.2"/></svg> Crisp</a>
  <a class="btn" href="{site}/#download">Download for Mac</a>
</div></nav>

<article><div class="wrap">
  <div class="crumb"><a href="{site}/">Crisp</a> &rsaquo; {section} &rsaquo; {crumb}</div>
  <h1>{h1}</h1>
{body}
  <h2>{faq_heading}</h2>
{faq_html}
  <p><a class="btn" href="{cta_href}">Download Crisp for Mac</a> Free to try, one-time ${price} to remove the watermark. Runs entirely on your Mac.</p>
</div></article>

<footer><div class="wrap">
  <p>&#9670; <strong style="color:var(--text-mid)">Crisp</strong> &mdash; offline AI video &amp; photo upscaler + auto-editor for Mac. <a href="{site}/">crispvideo.app</a></p>
</div></footer>
{founding}</body>
</html>
"""

#: ⚠️ THE FOUNDING BAR IS PART OF THE TEMPLATE TOO, for the reason the analytics line above
#: gives: a page this tool emits without it is a page nobody re-reads after creating. Matthew's
#: order (CEO chat 2026-09-25, "make the discount banner go across all pages of every website")
#: put the bar on every page except /thank-you/ (a buyer who has just paid) and the three
#: canonical-merge pages.
#:
#: READ FROM THE HOME PAGE, NOT RETYPED HERE. The mount carries the code and both prices, and
#: PRICE_USD exists above because a price retyped into a generator outlives every sweep of the
#: pages. So the one mount on / is the source and this copies it byte for byte. A home page with
#: no bar at all means the offer is off, and a new page gets none; a bar this pattern cannot read
#: stops the run instead, because guessing is how a page gets born without it.
_FOUNDING = re.compile(r'<div data-founding\b[^>]*></div>\n<script src="/founding\.js" defer></script>')


def founding_block(root: Path = Path(__file__).resolve().parent.parent) -> str:
    home = (root / "index.html").read_text(encoding="utf-8")
    m = _FOUNDING.search(home)
    if m:
        return m.group(0) + "\n"
    # Tags, not words: the home page's own comments mention /founding.js.
    if re.search(r'<[^>]+\bdata-founding\b|<script[^>]+src="/founding\.js"', home):
        raise SystemExit("index.html mounts the founding bar in a shape _FOUNDING cannot read — "
                         "fix the pattern; do not emit pages without the bar")
    return ""


#: A page that IS the product rather than an article about it (/download/) carries the home
#: page's SoftwareApplication node in place of an Article. READ FROM index.html, NOT RETYPED:
#: that node is the one the pre-push hook reads and the one crawlers already hold for
#: https://crispvideo.app/#app, so a second hand-written copy would be a second place for the
#: name, the OS floor or the download link to drift. softwareVersion and fileSize are left out
#: on purpose: the version gate and drift.py's size check both read the home page only, so a
#: copy here would rot where nothing looks. The offer must agree with PRICE_USD or nothing is
#: written.
_SOFTWARE_KEYS = ("@id", "name", "alternateName", "applicationCategory", "applicationSubCategory",
                  "operatingSystem", "processorRequirements", "url", "downloadUrl", "offers")


def software_ld(root: Path = Path(__file__).resolve().parent.parent) -> str:
    home = (root / "index.html").read_text(encoding="utf-8")
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', home, re.S):
        data = json.loads(raw)
        for node in data.get("@graph", [data]):
            if node.get("@type") == "SoftwareApplication":
                price = node.get("offers", {}).get("price")
                if price != str(PRICE_USD):
                    raise SystemExit(f"index.html offers {price!r} and PRICE_USD is {PRICE_USD}; "
                                     "settle the price before generating a page that quotes it")
                out = {"@context": "https://schema.org", "@type": "SoftwareApplication"}
                out.update((k, node[k]) for k in _SOFTWARE_KEYS if k in node)
                return json.dumps(out, ensure_ascii=False)
    raise SystemExit("index.html has no SoftwareApplication node to copy")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build(page, founding=None, root=None):
    root = root or Path(__file__).resolve().parent.parent
    if founding is None:
        founding = founding_block(root)
    # "{price}" is the one token a page's prose may carry, and it is how a page quotes Crisp's
    # price without retyping it. Prose is literal HTML and never goes through str.format() (brace
    # collisions), so this is a plain replace of that exact token and nothing else.
    def priced(s):
        return s.replace("{price}", str(PRICE_USD))
    faq = [(q, priced(a)) for q, a in page["faq"]]
    faq_html = "\n".join(
        f"  <h3>{q}</h3>\n  <p>{a}</p>" for q, a in faq)
    if page.get("ld") == "software":
        article_ld = software_ld(root)
    else:
        article_ld = ('{"@context":"https://schema.org","@type":"Article","headline":"%s",'
                      '"description":"%s","author":{"@type":"Organization","name":"Crisp"},'
                      '"publisher":{"@type":"Organization","name":"Crisp"},"datePublished":"2026-08-10"}'
                      % (esc(page["h1"]), esc(priced(page["desc"]))))
    qs = ",".join('{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}'
                  % (esc(q), esc(re.sub(r"<[^>]+>", "", a))) for q, a in faq)
    faq_ld = '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[%s]}' % qs
    return HEAD.format(site=SITE, price=PRICE_USD, slug=page["slug"], title=page["title"],
                       desc=esc(priced(page["desc"])),
                       ogtitle=esc(page["h1"]), crumb=page["crumb"], h1=page["h1"],
                       section=page.get("section", "Learn"),
                       body=priced(page["body"]), faq_heading=page["faq_heading"], faq_html=faq_html,
                       cta_href=page.get("cta_href", SITE + "/#download"),
                       article_ld=article_ld, faq_ld=faq_ld, founding=founding)


def main():
    from pages_learn import PAGES
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    apply = "--apply" in sys.argv
    founding = founding_block(root)
    for page in PAGES:
        out = root / page["slug"] / "index.html"
        words = len(re.sub(r"<[^>]+>", " ", page["body"] + " ".join(a for _, a in page["faq"])).split())
        status = "EXISTS-SKIP" if out.exists() else ("WRITE" if apply else "WOULD")
        print(f"  {status:12s} {page['slug']:46s} {words:5d}w")
        if apply and not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(build(page, founding, root), encoding="utf-8")
    print("REPORT ONLY — pass --apply" if not apply else "APPLIED")


if __name__ == "__main__":
    main()
