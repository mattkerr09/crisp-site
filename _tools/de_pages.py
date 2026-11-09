#!/usr/bin/env python3
"""Generate the German doors and refresh boxes without editing the other copy.

Words come from de_strings; release and checkout facts use the English readers.
Run with --check to report stale pages without writing anything.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from html import escape
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import de_strings as words  # noqa: E402
import landing_pages as landing  # noqa: E402
import llms_txt  # noqa: E402
import thankyou_xsell  # noqa: E402

SITE = landing.SITE
OTHER_PAGES = (
    "de/index.html",
    "de/kostenlos-oder-pro/index.html",
    "de/anleitung/video-hochskalieren-mac/index.html",
    "de/vhs-digitalisieren-und-verbessern/index.html",
    "de/datenschutz/index.html",
)
FULL_PAGES = ("de/download/index.html", "de/preise/index.html")
PBOX = re.compile(r'<aside\b[^>]*class="pbox"[^>]*>.*?</aside>', re.S)
MARKED_BOX = re.compile(r'<!-- de-box:begin -->.*?<!-- de-box:end -->', re.S)
EXPIRY_SCRIPT = (
    "<script>(function(){var n=Date.now();document.querySelectorAll('[data-until]').forEach(function(e){"
    "if(Date.parse(e.getAttribute('data-until'))<=n)e.remove();});})();</script>"
)
PRICE_SCRIPT = (
    "<script>(function(){var n=Date.now();document.querySelectorAll('[data-price-ends]').forEach(function(e){"
    "if(Date.parse(e.getAttribute('data-price-ends'))<=n)e.textContent=e.getAttribute('data-full-price');});})();</script>"
)
# Date values, in the same Pacific last-day convention as llms_txt.offer_last_day.
MONTHS = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember")


def last_day(ends: str) -> str:
    end = datetime.fromisoformat(ends.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
    last = (end - timedelta(seconds=1)).date() if (end.hour, end.minute) == (0, 0) else end.date()
    return f"{last.day}. {MONTHS[last.month - 1]}"


def future_day(ends: str) -> str:
    end = datetime.fromisoformat(ends.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
    day = (end + timedelta(seconds=1)).date()
    return f"{day.day}. {MONTHS[day.month - 1]}"


def price_copy(f: dict) -> str:
    if not llms_txt.founding_live(f):
        return f"{words.money(f['price'])} einmalig."
    return (f"Einführungspreis: {words.money(f['now'])} einmalig, bis {last_day(f['ends'])}. "
            f"Ab {future_day(f['ends'])}: {words.money(f['price'])}.")


def values(f: dict) -> dict:
    return dict(f, price=words.money(f["price"]), now=words.money(f["now"]), ends=last_day(f["ends"]),
                future=future_day(f["ends"]), price_copy=price_copy(f),
                os=words.fact_de(f["os"]), chip=words.fact_de(f["chip"]))


def box(src: str, buy_first: bool = False, f: dict | None = None) -> str:
    landing.prepare_facts()
    f = f if f is not None else llms_txt.facts()
    v = values(f)
    live = llms_txt.founding_live(f)
    amount = f["now"] if live else f["price"]
    price_attrs = (f' data-launch-price data-price-ends="{f["ends"]}" data-full-price="{v["price"]}"'
                   if live else "")
    dl = (f'<a class="btn{" btn-ghost" if buy_first else ""}" data-track="{src}" '
          f'href="{llms_txt.dl_url(src)}" rel="nofollow">{words.BOX["download_mac"]}</a>')
    buy = (f'<a class="btn{"" if buy_first else " btn-ghost"}" data-crisp-checkout data-track="{src}-buy" '
           f'href="{landing.buy_base()}?src={src}" rel="nofollow">{words.BOX["buy"]}</a>')
    found = (f'<p class="pbox-found" data-until="{f["ends"]}">{words.BOX["found"].format(**v)}</p>'
             if llms_txt.founding_live(f) else "")
    win = llms_txt.windows()
    windows = (f'<p class="win-link">{words.BOX["windows_q"]} '
               f'<a data-track="{src}-windows" href="{llms_txt.dl_win_url(src + "-windows")}" rel="nofollow">'
               f'{words.BOX["windows_dl"].format(win_version=win["version"])}</a> '
               f'<span class="win-gpu">{words.BOX["windows_gpu"]}</span></p>') if win else ""
    split = (f'<span class="pbox-split"> · {words.SPLIT.format(amount=words.money(llms_txt.quarter(amount)))}</span>'
             if llms_txt.bnpl_on(f, amount) else "")
    return (f'<!-- de-box:begin --><aside class="pbox" data-landing-box>'
            f'<p class="pbox-name">{words.BOX["name"]}</p>'
            f'<p class="pbox-price"><span class="pbox-amt"{price_attrs}>{words.money(amount)}</span> {words.BOX["once"]}{split}</p>'
            f'{found}<p class="pbox-cur">{words.CURRENCY}</p>'
            f'<p class="pbox-actions">{buy + " " + dl if buy_first else dl + " " + buy}</p>{windows}'
            f'<p class="pbox-fine">{words.BOX["fine"].format(**v)}</p></aside>'
            f'{PRICE_SCRIPT}{EXPIRY_SCRIPT}<!-- de-box:end -->')


def speed_section(f: dict) -> str:
    if not landing.macos_speed_section(f["os"]):
        return ""
    floor = re.search(r"macOS\s+(\d+)", f["os"]).group(1)

    def text(key):
        return words.DOWNLOAD[key].replace("macOS 14", "macOS " + floor)

    return (f'  <h2 id="macos-speed">{text("speed_h")}</h2>\n'
            f'  <p>{text("speed_p")}</p>\n  <ul>\n'
            f'    <li>{text("speed_15")}</li>\n    <li>{text("speed_14")}</li>\n  </ul>\n'
            f'  <p>{text("speed_same")}</p>\n  <p class="muted">{text("speed_measured")}</p>\n')


def bundle() -> str:
    if not thankyou_xsell.FACTS.is_file():
        raise SystemExit(f"de_pages: required regular prices file is missing: {thankyou_xsell.FACTS}")
    apart = sum(thankyou_xsell.list_price(name) for name in ("Crisp", "Docket SEO", "Outlier"))
    text = words.PRICES["bundle"].format(bundle_copy=price_copy({
        "price": landing.BUNDLE_USD, "now": landing.BUNDLE_FOUNDING_USD, "ends": landing.BUNDLE_FOUNDING_ENDS}), apart=words.money(apart), future=future_day(landing.BUNDLE_FOUNDING_ENDS))
    return (f'<a href="{landing.BUNDLE_URL}?src=de-preise" rel="nofollow" '
            f'data-track="de-preise-bundle" data-launch-price data-price-ends="{landing.BUNDLE_FOUNDING_ENDS}" '
            f'data-full-price="Alle drei Apps, Crisp, Docket SEO und Outlier. {words.money(landing.BUNDLE_USD)} einmalig.">{text}</a>')


def page(slug: str, f: dict) -> str:
    download = slug == "download"
    copy = words.DOWNLOAD if download else words.PRICES
    v = values(f)
    src = "de-" + slug
    lede = copy["lede" if download else "free"].format(**v)
    if not download:
        lede += f'</p>\n  <p>{copy["pro"].format(**v)}</p>\n  <p>{bundle()}'
    # Reuse the English chrome so assets, nav and analytics cannot drift.
    source = landing.page("download" if download else "pricing", escape(copy["title"].format(**v)),
                          escape(copy["meta"].format(**v), quote=True), copy["h1"], lede,
                          src, not download, speed_section(f) if download else "")
    source = source.replace('<html lang="en">', '<html lang="de">')
    source = re.sub(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n', '', source)
    canonical = f'<link rel="canonical" href="{llms_txt.BASE}/{"download" if download else "pricing"}/">'
    english = f'{llms_txt.BASE}/{"download" if download else "pricing"}/'
    german = f'{llms_txt.BASE}/de/{slug}/'
    source = source.replace(canonical, f'<link rel="canonical" href="{german}">\n' + '\n'.join(
        f'<link rel="alternate" hreflang="{lang}" href="{url}">'
        for lang, url in (("de", german), ("en", english), ("x-default", english))))
    source = source.replace('<body>', f'<body>\n<p class="app-language">{words.APP_LANGUAGE}</p>')
    source = re.sub(r'<!-- Generated by _tools/landing_pages.py.*?-->',
                    '<!-- Generated by _tools/de_pages.py. Edit the generator, not this page. -->', source, flags=re.S)
    source = source.replace(f'href="{llms_txt.BASE}/"', f'href="{llms_txt.BASE}/de/"')
    source = source.replace(f'{llms_txt.BASE}/download/?src=nav-download', f'{llms_txt.BASE}/de/download/?src=nav-download')
    source = source.replace('>Download</a>', f'>{words.NAV_DOWNLOAD}</a>')
    source = PBOX.sub(lambda m: box(src, not download, f), source)
    source = re.sub(r'  <p>Everything Pro adds,.*?</p>', f'  <p>{copy["more"]}</p>', source)
    contact = (f'<section class="kontakt"><h2>{words.KONTAKT_H}</h2><p>Kerr &amp; Company LLC<br>'
               'E-Mail: <a href="mailto:support@crispvideo.app">support@crispvideo.app</a><br>'
               'Web: <a href="https://crispvideo.app/">crispvideo.app</a></p></section>')
    footer = (f'{contact}\n<footer><div class="wrap">\n'
              f'  <p>&#9670; {words.FOOTER["line"]} <a href="{llms_txt.BASE}/de/">crispvideo.app</a> &middot; '
              f'<a href="{llms_txt.BASE}/about/">{words.FOOTER["about"]}</a></p>\n'
              f'  {landing.sitewide_chrome.KCO.replace("Made by Kerr &amp; Company", words.FOOTER["made_by"])}\n'
              '</div></footer>')
    source = re.sub(r'<footer>.*?</footer>', lambda m: footer, source, flags=re.S)
    # founding.js inserts English sentences. The German offer uses data-until.
    return source.replace(landing.sitewide_chrome.founding_tag() + '\n', '')


def refresh_boxes(source: str, name: str, f: dict) -> str:
    # Strip old wrappers before matching, so a second run is byte-for-byte stable.
    source = MARKED_BOX.sub(lambda m: PBOX.search(m.group(0)).group(0), source)
    slug = name.removeprefix("de/").removesuffix("/index.html").replace("/", "-")
    if name == "de/index.html":
        slug = "home"
    count = 0

    def replace(match):
        nonlocal count
        count += 1
        return box(f'de-{slug}-pbox-{count}', f=f)

    return PBOX.sub(replace, source)


def pages() -> dict[Path, str]:
    landing.prepare_facts()
    f = llms_txt.facts()
    want = {SITE / name: page(slug, f) for name, slug in zip(FULL_PAGES, ("download", "preise"))}
    for name in OTHER_PAGES:
        source = refresh_boxes((SITE / name).read_text(encoding="utf-8"), name, f)
        # The homepage scaffold also carries a fixed schema version, not prose.
        source = re.sub(r'("softwareVersion":\s*")[^"]+(")',
                        lambda m: m.group(1) + f["version"] + m.group(2), source)
        want[SITE / name] = source
    return want


def write(check: bool = False) -> int:
    want = pages()
    stale = [str(p.relative_to(SITE)) for p, source in want.items()
             if not p.is_file() or p.read_text(encoding="utf-8") != source]
    if check:
        print(f"German pages: {'stale ' + ', '.join(stale) if stale else 'current'}")
        return 1 if stale else 0
    for p, source in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(source, encoding="utf-8")
    print(f"wrote {', '.join(str(p.relative_to(SITE)) for p in want)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(write(check="--check" in sys.argv[1:]))
