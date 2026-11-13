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

    python3 _tools/landing_pages.py          # write the English pages, then the German doors and boxes
    python3 _tools/landing_pages.py --check  # exit 1 if any managed English or German output differs
    python3 _tools/landing_pages.py --selftest  # offline template checks; no pages written
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
WINDOWS_HEAD = """<script>document.documentElement.classList.add('js');
(function (n) { var u = n.userAgent || ''; if (/iPhone|iPad|iPod|Android|Mobi/i.test(u) || (/Macintosh/.test(u) && n.maxTouchPoints > 1)) document.documentElement.classList.add('handheld');
  else if (/Windows NT/.test(u)) document.documentElement.classList.add('win'); })(navigator);</script>"""


def buy_base() -> str:
    m = re.search(r'var CRISP_BUY_VIA = "([^"]+)";', (SITE / "index.html").read_text())
    if not m:
        raise SystemExit("landing_pages: the homepage no longer declares CRISP_BUY_VIA — read the Buy link from there")
    return m.group(1)


#: THE THREE-APP BUNDLE (Matthew approved 2026-11-11): Crisp + Check Engine SEO + Outlier for $34.99 once through December 2
#: (29% off the real $49.50 November price, expires 2026-12-03T07:59:59Z), then $59 (ALLTHREE).
#: December's separate prices are $19 + $39 + $29 = $87. Names only, no
#: sister-site URL: the link goes to the hub (RULES 52).
BUNDLE_URL = "https://kerr-affiliate-hub.kerrco.workers.dev/buy/bundle"
BUNDLE_FOUNDING_USD, BUNDLE_USD = Decimal("34.99"), Decimal("59")
BUNDLE_NOVEMBER_USD = Decimal("49.50")
BUNDLE_PERCENT_OFF = 29
BUNDLE_FOUNDING_ENDS = "2026-12-03T07:59:59Z"


def bundle_facts() -> dict:
    return {"product": "bundle", "price": BUNDLE_USD, "now": BUNDLE_FOUNDING_USD, "november": BUNDLE_NOVEMBER_USD,
            "percent": BUNDLE_PERCENT_OFF, "ends": BUNDLE_FOUNDING_ENDS}


def bundle_copy() -> str:
    return llms_txt.price_copy(bundle_facts())


def prepare_facts() -> None:
    """A site-only worktree still reads the app's facts from the main checkout."""
    gitfile = SITE / ".git"
    if not llms_txt.ENGINE.is_file() and gitfile.is_file():
        gitdir = (SITE / gitfile.read_text().strip().removeprefix("gitdir: ")).resolve()
        common = (gitdir / (gitdir / "commondir").read_text().strip()).resolve()
        engine = common.parent.parent / "backend" / "crisp_engine" / "entitlement.py"
        if engine.is_file():
            llms_txt.ENGINE = engine


def box(src: str, buy_first: bool, platform_swap: bool = False) -> str:
    f = llms_txt.facts()
    m, q = llms_txt.money, llms_txt.quarter
    p, now = f["price"], f["now"]
    live = llms_txt.founding_live(f)
    amount = now if live else p
    price_attrs = f' data-launch-price data-full-price="{m(p)}"' if live else ""
    split = f'<span class="pbox-split"> · or 4 × {m(q(amount))}</span>' if llms_txt.bnpl_on(f, amount) else ""
    dl = (f'<a class="btn{"" if not buy_first else " btn-ghost"}" data-track="{src}" '
          f'href="{llms_txt.dl_url(src)}" rel="nofollow">Download free for Mac</a>')
    buy = (f'<a class="btn{" btn-ghost" if not buy_first else ""}" data-crisp-checkout data-track="{src}-buy" '
           f'href="{buy_base()}?src={src}" rel="nofollow">Buy Crisp Pro</a>')
    win = platform_swap and bool(llms_txt.windows())
    win_dl = (f'<a class="btn win-btn" data-track="{src}-windows" '
              f'href="{llms_txt.dl_win_url(src + "-windows")}" rel="nofollow">Download free for Windows</a> ') if win else ""
    win_fine = (f'<p class="pbox-fine fine-win">Free to use: {llms_txt.free_tier(f["cap"], "&ldquo;", "&rdquo;")} · '
                f'{llms_txt.WIN_REQ}, with {llms_txt.WIN_GPU}; {llms_txt.WIN_GPU_NOTE} · '
                f'{f["refund_days"]}-day refund, no reason needed. '
                f'Also on the <a href="{llms_txt.MS_STORE}" data-track="{src}-ms-store" rel="nofollow">Microsoft Store</a>.</p>') if win else ""
    found = (f'<p class="pbox-found">{llms_txt.price_copy(f)} '
             'The Buy button applies the sale price.</p>') if live else ""
    return (f'<aside class="pbox" data-landing-box>'
            f'<p class="pbox-name"><strong>Crisp Video</strong> restores, denoises and upscales video to 4K on your Mac or PC, offline.</p>'
            f'<p class="pbox-price"><span class="pbox-amt"{price_attrs}>{m(amount)}</span> once{split}</p>'
            f'{found}'
            f'<p class="pbox-cur">Priced in US dollars. Checkout shows your currency and any local tax.</p>'
            f'<p class="pbox-actions">{win_dl}{buy + " " + dl if buy_first else dl + " " + buy}</p>'
            f'{windows_line(src)}'
            f'<p class="pbox-fine{" mac-only" if win else ""}">Free to use: {llms_txt.free_tier(f["cap"], "&ldquo;", "&rdquo;")} · {f["os"]}{llms_txt.speed_note(f["os"])} · '
            f'{f["chip"]} · {f["refund_days"]}-day refund, no reason needed.</p>'
            f'{win_fine}'
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


def alternates(slug: str) -> str:
    """Link only to doors owned by a strings module and present on disk."""
    if slug not in ("download", "pricing"):
        return ""
    import importlib

    english = f"/{slug}/"
    translations = []
    for path in sorted(Path(__file__).parent.glob("strings_*.py")):
        lang = path.stem.removeprefix("strings_").replace("_", "-")
        # Use the chrome's ownership rule before loading a language module.
        if sitewide_chrome.language(SITE / lang / "index.html") != lang:
            continue
        # the module this loop found, loaded from where it was found (lang_pages.load_words resolves beside lang_pages.__file__,
        # which gate_lang's selftest points at a temporary folder; that made the German selftest fail on 10 Nov)
        words = importlib.import_module(path.stem)
        route = dict(words.ROUTES).get(english)
        if route and (SITE / route.lstrip("/") / "index.html").is_file():
            translations.append((getattr(words, "HREFLANG", lang), route))
    # Preserve the established German-only output, including its line order.
    routes = (translations + [("en", english)] if len(translations) == 1
              else [("en", english)] + translations)
    routes.append(("x-default", english))
    return "".join(f'<link rel="alternate" hreflang="{lang}" href="{llms_txt.BASE}{route}">\n'
                   for lang, route in routes)


def page(slug: str, title: str, desc: str, h1: str, lede: str, src: str, buy_first: bool, extra: str = "") -> str:
    url = f"{llms_txt.BASE}/{slug}/"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
{WINDOWS_HEAD if llms_txt.windows() else ""}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="msvalidate.01" content="34D102FD9C044A2BDA597B176842725B" />
<title>{title}</title>
<meta property="og:title" content="{title}">
<meta name="twitter:title" content="{title}">
<link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="description" content="{desc}">
<meta name="robots" content="noindex, follow">
<meta name="theme-color" content="#060810">
<link rel="canonical" href="{url}">
{alternates(slug)}<link rel="stylesheet" href="/style.css">
{_analytics_line()}
{_referral_line()}{(llms_txt.offer_schema(llms_txt.facts()) + chr(10)) if slug == "pricing" else ""}</head>
<body>
{sitewide_chrome.founding_tag()}
<!-- Generated by _tools/landing_pages.py. Edit that, not this file. -->
<nav><div class="wrap nav-inner">
  <a class="nav-brand" href="{llms_txt.BASE}/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><circle cx="12" cy="12" r="3.2"/></svg> Crisp Video</a>
  <a class="btn" data-track="nav-download" href="{llms_txt.BASE}/download/?src=nav-download">Download</a>
</div></nav>

<article><div class="wrap">
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
  {box(src, buy_first, platform_swap=True)}{extra}  <p>Everything Pro adds, the licence terms and the answers to the usual questions are on the <a href="{llms_txt.BASE}/#buy">home page</a>.</p>
</div></article>

<footer><div class="wrap">
  <p>&#9670; <strong style="color:var(--text-mid)">Crisp</strong>: offline AI video &amp; photo upscaler and auto-editor for Mac, and a video upscaler and editor for Windows. <a href="{llms_txt.BASE}/">crispvideo.app</a> &middot; <a href="{llms_txt.BASE}/about/">About</a></p>
  {sitewide_chrome.KCO}
</div></footer>
{sitewide_chrome.TRACK}
</body>
</html>
"""


def pages() -> dict[Path, str]:
    f = llms_txt.facts()
    m = llms_txt.money
    download_intro = f'The current release, notarized by Apple: {f["os"]}, {f["chip"]}.'
    speed = macos_speed_section(f["os"])
    if llms_txt.windows():
        download_intro = (f'<span class="mac-only">{download_intro}</span> '
                          f'<span class="win-only">{llms_txt.WIN_REQ}, with {llms_txt.WIN_GPU}.</span>')
        if speed:
            speed = f'<div class="mac-only">\n{speed}</div>\n'
    return {
        SITE / "pricing" / "index.html": page(
            "pricing", "Crisp pricing: free to use, Pro with one payment",
            f"Crisp restores and upscales video offline on Mac and Windows. Free, with no account or time limit. {llms_txt.price_short(f)}",
            "Crisp pricing",
            f"Crisp is free on Mac and Windows, offline, with no account or time limit. Pro is one payment. "
            f"{llms_txt.price_markup(f)} {f['updates'].replace(' included', ' is included').capitalize()}. "
            f'<a href="{BUNDLE_URL}?src=crisp-pricing" rel="nofollow" data-track="pricing-page-bundle">All three apps, Crisp, Check Engine SEO and Outlier. {llms_txt.price_markup(bundle_facts())}</a>',
            "pricing-page", True, llms_txt.free_pro_html(f["cap"]) + "\n"),
        SITE / "download" / "index.html": page(
            "download", "Download Crisp for Mac and Windows",
            f"Download Crisp Video for Mac and Windows. Free to use: enhanced exports up to {f['cap']} seconds, everything else at full length.",
            "Download Crisp for Mac and Windows",
            f"{download_intro} Free to use: {llms_txt.free_tier(f['cap'], '&ldquo;', '&rdquo;')}; Pro removes the mark and the limit.",
            "download-page", False, speed),
        # THE ADDRESS ON THE FREE MARK (CEO, 2026-11-05): every free video export carries "crispvideo.app" and, under it,
        # "crispvideo.app/w" (crisp scripts/make_watermark.py). This is that door: what Crisp is, and the download tagged
        # src=watermark, so the visits and downloads the mark sends can be counted.
        SITE / "w" / "index.html": page(
            "w", "Made with Crisp: restore and upscale video, offline",
            "You saw “crispvideo.app” on a video. Crisp restores, denoises and upscales video to 4K on your own Mac or PC, offline. Free to use.",
            "You saw &ldquo;crispvideo.app&rdquo; on a video",
            "That mark is on every free export from Crisp Video. Crisp restores, denoises and upscales old and low-res video to 4K "
            "on your own Mac or Windows PC, offline: your videos never leave your computer. It is free to use, and Pro removes the mark.",
            "watermark", False),
    }


def windows_line(src: str) -> str:
    """The Windows download line: one definition, llms_txt.windows_line (the in-article boxes use it too)."""
    return llms_txt.windows_line(src)


#: the home page's Windows line sits between these markers, under the hero's Mac button; this file writes it and --check reads it
WIN_HOME = re.compile(r"<!-- windows-download:begin -->.*?<!-- windows-download:end -->", re.S)


#: the Windows hero button (before the Mac button) and the Windows fine print (after the Mac's), written the same way
WIN_HERO = re.compile(r"<!-- windows-hero:begin -->.*?<!-- windows-hero:end -->", re.S)
WIN_FINE = re.compile(r"<!-- windows-fine:begin -->.*?<!-- windows-fine:end -->", re.S)
# the "Get Crisp" step further down offered only the Mac download, so a PC visitor who scrolled, or a PC buyer sent there
# from the thank-you page, found no installer (Windows buy-path audit, 2026-11-08)
WIN_STEP = re.compile(r"<!-- windows-step:begin -->.*?<!-- windows-step:end -->", re.S)
FREE_PRO = re.compile(r"<!-- free-pro:begin -->.*?<!-- free-pro:end -->", re.S)


def home(s: str) -> str:
    for rx, name in ((WIN_HOME, "windows-download"), (WIN_HERO, "windows-hero"), (WIN_FINE, "windows-fine"), (WIN_STEP, "windows-step")):
        assert rx.search(s), f"index.html: the {name} markers are gone"
    f = llms_txt.facts()
    cap = f["cap"]
    assert FREE_PRO.search(s), "index.html: the free-pro markers are gone"
    s = FREE_PRO.sub(lambda _m: '<!-- free-pro:begin -->\n'
                     f'<div class="free-pro"><h2>{llms_txt.free_pro_heading(f)}</h2>\n'
                     f'<div class="free-pro-lists">{llms_txt.free_pro_html(cap)}</div></div>\n'
                     '<!-- free-pro:end -->', s, count=1)
    s = WIN_HOME.sub(lambda _m: "<!-- windows-download:begin -->" + windows_line("home-hero") + "<!-- windows-download:end -->", s, count=1)
    s = WIN_HERO.sub(lambda _m: "<!-- windows-hero:begin -->" + llms_txt.windows_hero_button("home-hero-win") + "<!-- windows-hero:end -->", s, count=1)
    s = WIN_STEP.sub(lambda _m: "<!-- windows-step:begin -->" + windows_line("home-download-section") + "<!-- windows-step:end -->", s, count=1)
    return WIN_FINE.sub(lambda _m: "<!-- windows-fine:begin -->" + llms_txt.windows_hero_fine(cap, "home-hero-win") + "<!-- windows-fine:end -->", s, count=1)


def page404(s: str) -> str:
    b = box("404", False)
    if "data-landing-box" in s:
        return BOX.sub(lambda _m: b, s, count=1)
    a = '<a class="btn" href="/">Back to Crisp</a>'
    assert s.count(a) == 1, "404.html: the Back to Crisp button moved"
    return s.replace(a, b + '<p><a class="btn btn-ghost" href="/">Back to Crisp</a></p>')


def selftest() -> int:
    """Render in memory with site-side fixture facts; never read the app checkout or write a page."""
    import json
    import subprocess
    from unittest.mock import Mock, patch
    import new_pages
    import shipped_comments

    assert WINDOWS_HEAD in (SITE / "index.html").read_text(), "keep platform detection the same as the home page"
    engine = Mock()
    engine.read_text.return_value = (f'PRICE_USD = {new_pages.PRICE_USD}\n'
                                   'FOUNDING_OFF_USD = Decimal("9.01")\n'
                                   'NOVEMBER_PRICE_USD = Decimal("14.50")\n'
                                   f'LAUNCH_ENDS = "{BUNDLE_FOUNDING_ENDS}"\n'
                                   f'FREE_EXPORT_CAP_SECONDS = {new_pages.FREE_EXPORT_CAP_SECONDS}\n')
    with patch.object(llms_txt, "ENGINE", engine):
        f = llms_txt.facts()
        assert llms_txt.windows(), "selftest needs the repo's published Windows manifest"
        rendered = pages()
        for slug, src in (("download", "download-page"), ("pricing", "pricing-page"), ("w", "watermark")):
            s = rendered[SITE / slug / "index.html"]
            assert s.index(WINDOWS_HEAD) < s.index('<link rel="stylesheet"')
            assert f'<link rel="canonical" href="{llms_txt.BASE}/{slug}/">' in s
            actions = re.search(r'<p class="pbox-actions">(.*?)</p>', s).group(1)
            assert actions.startswith('<a class="btn win-btn"')
            assert f'data-track="{src}-windows"' in actions
            assert f'href="{llms_txt.dl_win_url(src + "-windows")}"' in actions
            assert f'href="{llms_txt.dl_url(src)}"' in actions
            assert 'data-crisp-checkout' in actions
            fine = re.search(r'<p class="pbox-fine fine-win">(.*?)</p>', s).group(1)
            assert llms_txt.WIN_REQ in fine and llms_txt.WIN_GPU in fine
            assert f'{f["refund_days"]}-day refund' in fine and llms_txt.MS_STORE in fine
            assert 'macOS' not in fine and 'Apple' not in fine
            assert '<p class="pbox-fine mac-only">' in s
            title = re.search(r'<title>(.*?)</title>', s).group(1)
            assert len(title) <= 60
            assert f'<meta property="og:title" content="{title}">' in s
            assert f'<meta name="twitter:title" content="{title}">' in s
            assert not shipped_comments.clean(s, "html")[1]
        download = rendered[SITE / "download" / "index.html"]
        title = "Download Crisp for Mac and Windows"
        assert f'<title>{title}</title>' in download and f'<h1>{title}</h1>' in download
        assert '<span class="mac-only">The current release, notarized by Apple:' in download
        assert f'<span class="win-only">{llms_txt.WIN_REQ}' in download
        assert 'win-btn' not in box("404", False)
        with patch.object(llms_txt, "windows", return_value=None):
            for s in pages().values():
                assert WINDOWS_HEAD not in s
                assert 'win-btn' not in s and 'fine-win' not in s and 'mac-only' not in s
                assert 'Download free for Mac' in s and 'macOS' in s
        for src, buy_first in (("download-page", False), ("pricing-page", True)):
            actions = re.search(r'<p class="pbox-actions">(.*?)</p>', box(src, buy_first, True)).group(1)
            mac = re.search(r'<a class="([^"]+)"[^>]*>Download free for Mac</a>', actions).group(1)
            assert ("btn-ghost" in mac) == buy_first

    script = WINDOWS_HEAD.removeprefix("<script>").removesuffix("</script>")
    cases = {"Windows NT 10.0; Win64; x64": True, "Windows NT 10.0; Mobi": False, "Macintosh; Intel Mac OS X": False,
             "Linux x86_64": False, "iPhone": False, "Android": False, "": False}
    probe = """const vm = require('node:vm');
const {script, cases} = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
for (const [userAgent, expected] of Object.entries(cases)) {
  const classes = new Set();
  vm.runInNewContext(script, {navigator: {userAgent}, document: {documentElement: {classList: {add: c => classes.add(c)}}}});
  if (classes.has('win') !== expected) throw new Error(userAgent);
}
"""
    subprocess.run(["node", "-e", probe], input=json.dumps({"script": script, "cases": cases}), text=True, check=True)
    print("OK: three landing templates, platform links and requirements, titles, Mac fallback and seven user agents; no pages written")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    import de_pages

    prepare_facts()
    check = "--check" in argv
    want = pages()
    p404 = SITE / "404.html"
    want[p404] = page404(p404.read_text())
    ph = SITE / "index.html"
    want[ph] = home(ph.read_text())
    stale = [str(p.relative_to(SITE)) for p, s in want.items() if not p.is_file() or p.read_text() != s]
    if check:
        print(f"landing pages: {'stale ' + ', '.join(stale) if stale else 'current'}")
        de_result = de_pages.write(check=True)
        return 1 if stale or de_result else 0
    for p, s in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(s)
    for p in want:                 # the chrome is in the template already, so this changes nothing — and
        sitewide_chrome.apply(p)   # if sitewide_chrome ever grows a new piece, --check then reports stale
    print(f"wrote {', '.join(str(p.relative_to(SITE)) for p in want)}")
    return de_pages.write()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
