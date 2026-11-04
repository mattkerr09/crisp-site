"""The addresses people guess — /pricing/, /download/ and any 404 — lead somewhere that sells.

CEO order, 2026-10-01, before the Product Hunt launch: crispvideo.app/pricing/ and /download/ answered 404,
and the 404 page offered one "Back to Crisp" button, no price, no Download, no Buy. A visitor, or an AI
assistant citing crispvideo.app/pricing, landed on a dead end. Outlier fixed the same thing on 09-29.

  /pricing/ and /download/  small real pages: noindex (they are doors, not search results), a self canonical,
                            one heading and one box — the price with its four-payment split, the founding
                            line, Download through the hub's /dl/crisp and Buy through its /buy/crisp (which
                            applies the founding code), the requirements and the refund window.
  404.html                  keeps its line and gains the same box (src=404).

EVERY FIGURE IS READ, NOT TYPED: llms_txt.facts() (the reader llms.txt and the in-article boxes use) for the
price, the founding offer, pay-in-four, macOS, chip and refund window; llms_txt.dl_url for the download; the
homepage's own CRISP_BUY_VIA for Buy. The analytics/pixel line comes from new_pages.HEAD and the referral
snippet from 404.html's head, so neither is typed twice. Not in the sitemap (noindex) — the page-finding test
exempts both with this reason. product_box.py skips noindex pages.

    python3 _tools/landing_pages.py          # write the two pages and refresh the 404 box
    python3 _tools/landing_pages.py --check  # exit 1 if any of the three differs from what this would write
"""
from __future__ import annotations

import re
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llms_txt  # noqa: E402
import sitewide_chrome  # noqa: E402

SITE = Path(__file__).resolve().parents[1]
BOX = re.compile(r'<aside class="pbox" data-landing-box>.*?</aside>\n?', re.S)


def buy_base() -> str:
    m = re.search(r'var CRISP_BUY_VIA = "([^"]+)";', (SITE / "index.html").read_text())
    if not m:
        raise SystemExit("landing_pages: the homepage no longer declares CRISP_BUY_VIA — read the Buy link from there")
    return m.group(1)


#: THE THREE-APP BUNDLE (Matthew approved 2026-10-14; re-priced 2026-11-02 with the video-game prices, read in the CEO's
#: REVENUE-AUDIT-CHECKLIST entry of 18:24Z): Crisp + Docket SEO + Outlier for $49.50 once through November (FOUNDINGBUNDLE, for
#: everyone, expires 2026-12-01T07:59:59Z), then $99 (ALLTHREE); bought separately $29 + $59 + $49 = $137. Names only, no
#: sister-site URL: the link goes to the hub (RULES 52).
BUNDLE_URL = "https://kerr-affiliate-hub.kerrco.workers.dev/buy/bundle"
BUNDLE_FOUNDING_USD, BUNDLE_USD = Decimal("49.50"), Decimal("99")
BUNDLE_FOUNDING_ENDS = "2026-12-01T07:59:59Z"


def box(src: str, buy_first: bool) -> str:
    f = llms_txt.facts()
    m, q = llms_txt.money, llms_txt.quarter
    p, now = f["price"], f["now"]
    split = f'<span class="pbox-split"> · or 4 × {m(q(p))}</span>' if llms_txt.bnpl_on(f, p) else ""
    nsplit = f" · or 4 × {m(q(now))}" if llms_txt.bnpl_on(f, now) else ""     # none under the $50.01 floor
    dl = (f'<a class="btn{"" if not buy_first else " btn-ghost"}" data-track="{src}" '
          f'href="{llms_txt.dl_url(src)}" rel="nofollow">Download free for Mac</a>')
    buy = (f'<a class="btn{" btn-ghost" if not buy_first else ""}" data-crisp-checkout data-track="{src}-buy" '
           f'href="{buy_base()}?src={src}" rel="nofollow">Buy Crisp Pro</a>')
    found = (f'<p class="pbox-found">Black Friday price <strong>{m(now)}{nsplit}</strong> {llms_txt.offer_who(f)}, then {m(p)}. '
             f'The Buy button applies <strong>{f["code"]}</strong> at checkout.</p>') if llms_txt.founding_live(f) else ""
    return (f'<aside class="pbox" data-landing-box>'
            f'<p class="pbox-name"><strong>Crisp Video</strong> restores, denoises and upscales video to 4K on your Mac, offline.</p>'
            f'<p class="pbox-price"><span class="pbox-amt">{m(p)}</span> once{split}</p>'
            f'{found}'
            f'<p class="pbox-actions">{buy + " " + dl if buy_first else dl + " " + buy}</p>'
            f'{windows_line(src)}'
            f'<p class="pbox-fine">Free to use: {llms_txt.free_tier(f["cap"], "&ldquo;", "&rdquo;")} · {f["os"]}{llms_txt.speed_note(f["os"])} · '
            f'{f["chip"]} · {f["refund_days"]}-day refund, no reason needed.</p>'
            f'</aside>\n')


def _analytics_line() -> str:
    import new_pages
    line = next(l for l in new_pages.HEAD.splitlines() if "plausible.io/js/script.js" in l)
    return line.replace("{{", "{").replace("}}", "}")


def _referral_line() -> str:
    m = re.search(r"<!-- affiliate-hub:begin -->.*?<!-- affiliate-hub:end -->", (SITE / "404.html").read_text())
    if not m:
        raise SystemExit("landing_pages: 404.html lost the referral snippet line it is read from")
    return m.group(0)


def macos_speed_section(os_line: str) -> str:
    """The download page says plainly what changes below macOS 15 (CEO, 2026-10-20). Empty when the floor is 15+."""
    m = re.search(r"macOS\s+(\d+)", os_line or "")
    if not m or int(m.group(1)) >= 15:
        return ""
    v = m.group(1)
    return (f'''  <h2 id="macos-speed">How fast it runs on your macOS</h2>
  <p>Crisp is built for macOS {v} and tested on macOS {v} and 26. Which upscaler it uses depends on your macOS:</p>
  <ul>
    <li><strong>macOS 15 Sequoia or later:</strong> Core ML, on your Mac's GPU. Full speed.</li>
    <li><strong>macOS {v}:</strong> a different upscaler, Crisp's ncnn engine, also on your Mac's GPU. Upscaling takes
      about 1.5 times as long.</li>
  </ul>
  <p>The picture comes out the same either way; only the wait changes.</p>
  <p class="muted">Measured on a Mac Studio (M1 Ultra) in October 2026: a 3-second clip doubled to 720p took 3.4 seconds with
    Core ML and 5.0 seconds with the ncnn upscaler that macOS {v} uses. That is the macOS {v} upscaler timed on a newer
    macOS; it has not yet been timed on a Mac running macOS {v} itself.</p>
''')


def page(slug: str, title: str, desc: str, h1: str, lede: str, src: str, buy_first: bool, extra: str = "") -> str:
    url = f"{llms_txt.BASE}/{slug}/"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="msvalidate.01" content="34D102FD9C044A2BDA597B176842725B" />
<title>{title}</title>
<link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="description" content="{desc}">
<meta name="robots" content="noindex, follow">
<meta name="theme-color" content="#060810">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="/style.css">
{_analytics_line()}
{_referral_line()}</head>
<body>
<!-- Generated by _tools/landing_pages.py — edit that, not this file. A door for an address people guess
     ({url}): noindex, so it never competes with the homepage in search. -->
<nav><div class="wrap nav-inner">
  <a class="nav-brand" href="{llms_txt.BASE}/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><circle cx="12" cy="12" r="3.2"/></svg> Crisp Video</a>
  <a class="btn" href="{llms_txt.BASE}/#download">Download for Mac</a>
</div></nav>

<article><div class="wrap">
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
  {box(src, buy_first)}{extra}  <p>Everything Pro adds, the licence terms and the answers to the usual questions are on the <a href="{llms_txt.BASE}/#buy">home page</a>.</p>
</div></article>

<footer><div class="wrap">
  <p>&#9670; <strong style="color:var(--text-mid)">Crisp</strong>: offline AI video &amp; photo upscaler and auto-editor for Mac. <a href="{llms_txt.BASE}/">crispvideo.app</a> &middot; <a href="{llms_txt.BASE}/about/">About</a></p>
  {sitewide_chrome.KCO}
</div></footer>
{sitewide_chrome.TRACK}
{sitewide_chrome.founding_tag()}
</body>
</html>
"""


def pages() -> dict[Path, str]:
    f = llms_txt.facts()
    m = llms_txt.money
    return {
        SITE / "pricing" / "index.html": page(
            "pricing", f"Crisp pricing: free to try, Pro {m(f['price'])} once",
            f"Free to use: enhanced exports up to {f['cap']} seconds, everything else at full length, with a small mark. Pro is {m(f['price'])} once, not a subscription.",
            "Crisp pricing",
            f"Free to use: the full editor and the full preview. Upscaling, restoring and colour exports stop at {f['cap']} seconds; everything else, such as Convert, Mute, Compress and Loop, "
            f"runs at full length; every free video export carries a small &ldquo;Made with Crisp&rdquo; mark. To spend the free {f['cap']} seconds on the part you care about, trim the clip to it, then run Enhance on it or export with Upscale on export. Pro is a one-time "
            f"{m(f['price'])}, {f['updates']}: it removes the mark and the {f['cap']}-second limit and adds the Max restore lane and batch processing. "
            f'<a href="{BUNDLE_URL}?src=crisp-pricing" rel="nofollow" data-track="pricing-page-bundle">All three apps, Crisp, Docket SEO and Outlier, for {llms_txt.money(BUNDLE_FOUNDING_USD)} once</a> '
            f"{llms_txt.offer_last_day({'ends': BUNDLE_FOUNDING_ENDS})}, our Black Friday price, then {llms_txt.money(BUNDLE_USD)}.",
            "pricing-page", True),
        SITE / "download" / "index.html": page(
            "download", "Download Crisp for Mac",
            f"Download Crisp Video for Mac: {f['os']}, {f['chip']}. Free to use: enhanced exports up to {f['cap']} seconds, everything else at full length.",
            "Download Crisp for Mac",
            f"The current release, notarized by Apple: {f['os']}, {f['chip']}. Free to use: {llms_txt.free_tier(f['cap'], '&ldquo;', '&rdquo;')}; Pro removes the mark and the limit.",
            "download-page", False, macos_speed_section(f["os"])),
    }


def windows_line(src: str) -> str:
    """The Windows download, through the hub's counting route like the Mac's (src = this place + "-windows"). Empty until a
    Windows release exists. Claims are only what the release run proved: the version, the requirement, the signer."""
    w = llms_txt.windows()
    if not w:
        return ""
    return (f'<p class="win-link">On {llms_txt.WIN_REQ}? <a data-track="{src}-windows" href="{llms_txt.dl_win_url(src + "-windows")}" '
            f'rel="nofollow">Download Crisp {w["version"]} for Windows</a></p>')


#: the home page's Windows line sits between these markers, under the hero's Mac button; this file writes it and --check reads it
WIN_HOME = re.compile(r"<!-- windows-download:begin -->.*?<!-- windows-download:end -->", re.S)


def home(s: str) -> str:
    assert WIN_HOME.search(s), "index.html: the windows-download markers are gone"
    return WIN_HOME.sub(lambda _m: "<!-- windows-download:begin -->" + windows_line("home-hero") + "<!-- windows-download:end -->",
                        s, count=1)


def page404(s: str) -> str:
    b = box("404", False)
    if "data-landing-box" in s:
        return BOX.sub(lambda _m: b, s, count=1)
    a = '<a class="btn" href="/">Back to Crisp</a>'
    assert s.count(a) == 1, "404.html: the Back to Crisp button moved"
    return s.replace(a, b + '<p><a class="btn btn-ghost" href="/">Back to Crisp</a></p>')


def main(argv: list[str]) -> int:
    check = "--check" in argv
    want = pages()
    p404 = SITE / "404.html"
    want[p404] = page404(p404.read_text())
    ph = SITE / "index.html"
    want[ph] = home(ph.read_text())
    stale = [str(p.relative_to(SITE)) for p, s in want.items() if not p.is_file() or p.read_text() != s]
    if check:
        print(f"landing pages: {'stale ' + ', '.join(stale) if stale else 'current'}")
        return 1 if stale else 0
    for p, s in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(s)
    for p in want:                 # the chrome is in the template already, so this changes nothing — and
        sitewide_chrome.apply(p)   # if sitewide_chrome ever grows a new piece, --check then reports stale
    print(f"wrote {', '.join(str(p.relative_to(SITE)) for p in want)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
