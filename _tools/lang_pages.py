#!/usr/bin/env python3
"""Generate localized doors and product boxes from strings_<lang>.py.

Run lang_pages.py <lang> --check to report stale pages without writing them.
Routes, copy and locale formatting come from the strings module.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from html import escape
import importlib
from pathlib import Path
import re
from zoneinfo import ZoneInfo

import landing_pages as landing
import llms_txt
import thankyou_xsell


def load_words(lang: str):
    """Load only a language module beside this generator."""
    if not re.fullmatch(r"[a-z]{2,8}(?:-[a-z0-9]{1,8})*", lang):
        raise ValueError(f"invalid language code: {lang!r}")
    if not Path(__file__).with_name(f"strings_{lang}.py").is_file():
        raise ValueError(f"missing strings_{lang}.py")
    return importlib.import_module(f"strings_{lang}")


PBOX = re.compile(r'<aside\b[^>]*class="pbox"[^>]*>.*?</aside>', re.S)
EXPIRY_SCRIPT = (
    "<script>(function(){var n=Date.now();document.querySelectorAll('[data-until]').forEach(function(e){"
    "if(Date.parse(e.getAttribute('data-until'))<=n)e.remove();});})();</script>"
)
PRICE_SCRIPT = (
    "<script>(function(){var n=Date.now();document.querySelectorAll('[data-price-ends]').forEach(function(e){"
    "if(Date.parse(e.getAttribute('data-price-ends'))<=n)e.textContent=e.getAttribute('data-full-price');});})();</script>"
)


class LanguagePages:
    # Keep the shared readers available to the legacy de_pages callers.
    landing = landing
    llms_txt = llms_txt
    thankyou_xsell = thankyou_xsell
    PBOX = PBOX
    PRICE_SCRIPT = PRICE_SCRIPT
    EXPIRY_SCRIPT = EXPIRY_SCRIPT

    def __init__(self, lang: str, site: Path | None = None):
        self.lang = lang
        self.words = load_words(lang)
        self.SITE = site if site is not None else landing.SITE
        self.routes = dict(self.words.ROUTES)
        self.folder = self.routes["/"].strip("/")
        self.download_slug = self.routes["/download/"].removeprefix(self.routes["/"]).strip("/")
        self.pricing_slug = self.routes["/pricing/"].removeprefix(self.routes["/"]).strip("/")
        self.FULL_PAGES = tuple(self.routes[route].lstrip("/") + "index.html"
                                for route in self.words.GENERATED_ROUTES)
        self.OTHER_PAGES = tuple(target.lstrip("/") + "index.html" for source, target in self.words.ROUTES
                                 if source not in self.words.GENERATED_ROUTES)
        self.MARKED_BOX = re.compile(r'<!-- ' + re.escape(lang) + r'-box:begin -->.*?<!-- '
                                     + re.escape(lang) + r'-box:end -->', re.S)

    def last_day(self, ends: str) -> str:
        end = datetime.fromisoformat(ends.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
        last = (end - timedelta(seconds=1)).date() if (end.hour, end.minute) == (0, 0) else end.date()
        return self.words.DATE_FORMAT.format(day=last.day, month=self.words.MONTHS[last.month - 1])

    def future_day(self, ends: str) -> str:
        end = datetime.fromisoformat(ends.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
        day = (end + timedelta(seconds=1)).date()
        return self.words.DATE_FORMAT.format(day=day.day, month=self.words.MONTHS[day.month - 1])

    def price_copy(self, f: dict) -> str:
        if not llms_txt.founding_live(f):
            return self.words.PRICE_ONCE.format(price=self.words.money(f["price"]))
        v = dict(price=self.words.money(f["price"]), now=self.words.money(f["now"]),
                 ends=self.last_day(f["ends"]), future=self.future_day(f["ends"]))
        return self.words.PRICE_COPY.format(**v)

    def price_short(self, f: dict) -> str:
        """The offer text for a meta description."""
        if not llms_txt.founding_live(f):
            return self.words.PRICE_ONCE.format(price=self.words.money(f["price"]))
        v = dict(price=self.words.money(f["price"]), now=self.words.money(f["now"]),
                 ends=self.f_ends_short(f["ends"]))
        return self.words.PRICE_SHORT.format(**v)

    def f_ends_short(self, ends: str) -> str:
        end = datetime.fromisoformat(ends.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
        day = (end - timedelta(seconds=1)).date() if (end.hour, end.minute) == (0, 0) else end.date()
        return self.words.SHORT_DATE_FORMAT.format(day=day.day, month=self.words.SHORT_MONTHS[day.month - 1])

    def values(self, f: dict) -> dict:
        return dict(f, price=self.words.money(f["price"]), now=self.words.money(f["now"]), ends=self.last_day(f["ends"]),
                    future=self.future_day(f["ends"]), price_copy=self.price_copy(f), price_short=self.price_short(f),
                    os=self.words.fact(f["os"]), chip=self.words.fact(f["chip"]))

    def box(self, src: str, buy_first: bool = False, f: dict | None = None) -> str:
        landing.prepare_facts()
        f = f if f is not None else llms_txt.facts()
        v = self.values(f)
        live = llms_txt.founding_live(f)
        amount = f["now"] if live else f["price"]
        price_attrs = (f' data-launch-price data-price-ends="{f["ends"]}" data-full-price="{v["price"]}"'
                       if live else "")
        dl = (f'<a class="btn{" btn-ghost" if buy_first else ""}" data-track="{src}" '
              f'href="{llms_txt.dl_url(src)}" rel="nofollow">{self.words.BOX["download_mac"]}</a>')
        buy = (f'<a class="btn{"" if buy_first else " btn-ghost"}" data-crisp-checkout data-track="{src}-buy" '
               f'href="{landing.buy_base()}?src={src}" rel="nofollow">{self.words.BOX["buy"]}</a>')
        found = (f'<p class="pbox-found" data-until="{f["ends"]}">{self.words.BOX["found"].format(**v)}</p>'
                 if llms_txt.founding_live(f) else "")
        win = llms_txt.windows()
        windows = (f'<p class="win-link">{self.words.BOX["windows_q"]} '
                   f'<a data-track="{src}-windows" href="{llms_txt.dl_win_url(src + "-windows")}" rel="nofollow">'
                   f'{self.words.BOX["windows_dl"].format(win_version=win["version"])}</a> '
                   f'<span class="win-gpu">{self.words.BOX["windows_gpu"]}</span></p>') if win else ""
        split = (f'<span class="pbox-split"> · {self.words.SPLIT.format(amount=self.words.money(llms_txt.quarter(amount)))}</span>'
                 if llms_txt.bnpl_on(f, amount) else "")
        return (f'<!-- {self.lang}-box:begin --><aside class="pbox" data-landing-box>'
                f'<p class="pbox-name">{self.words.BOX["name"]}</p>'
                f'<p class="pbox-price"><span class="pbox-amt"{price_attrs}>{self.words.money(amount)}</span> {self.words.BOX["once"]}{split}</p>'
                f'{found}<p class="pbox-cur">{self.words.CURRENCY}</p>'
                f'<p class="pbox-actions">{buy + " " + dl if buy_first else dl + " " + buy}</p>{windows}'
                f'<p class="pbox-fine">{self.words.BOX["fine"].format(**v)}</p></aside>'
                f'{PRICE_SCRIPT}{EXPIRY_SCRIPT}<!-- {self.lang}-box:end -->')

    def speed_section(self, f: dict) -> str:
        if not landing.macos_speed_section(f["os"]):
            return ""
        floor = re.search(r"macOS\s+(\d+)", f["os"]).group(1)

        def text(key):
            return self.words.DOWNLOAD[key].replace("macOS 14", "macOS " + floor)

        return (f'  <h2 id="macos-speed">{text("speed_h")}</h2>\n'
                f'  <p>{text("speed_p")}</p>\n  <ul>\n'
                f'    <li>{text("speed_15")}</li>\n    <li>{text("speed_14")}</li>\n  </ul>\n'
                f'  <p>{text("speed_same")}</p>\n  <p class="muted">{text("speed_measured")}</p>\n')

    def bundle(self) -> str:
        if not thankyou_xsell.FACTS.is_file():
            raise SystemExit(f"lang_pages {self.lang}: required regular prices file is missing: {thankyou_xsell.FACTS}")
        apart = sum(thankyou_xsell.list_price(name) for name in ("Crisp", "Docket SEO", "Outlier"))
        text = self.words.PRICES["bundle"].format(bundle_copy=self.price_copy({
            "price": landing.BUNDLE_USD, "now": landing.BUNDLE_FOUNDING_USD, "ends": landing.BUNDLE_FOUNDING_ENDS}), apart=self.words.money(apart), future=self.future_day(landing.BUNDLE_FOUNDING_ENDS))
        return (f'<a href="{landing.BUNDLE_URL}?src={self.lang}-{self.pricing_slug}" rel="nofollow" '
                f'data-track="{self.lang}-{self.pricing_slug}-bundle" data-launch-price data-price-ends="{landing.BUNDLE_FOUNDING_ENDS}" '
                f'data-full-price="{self.words.BUNDLE_FULL_PRICE.format(price=self.words.money(landing.BUNDLE_USD))}">{text}</a>')

    def page(self, slug: str, f: dict) -> str:
        download = slug == self.download_slug
        copy = self.words.DOWNLOAD if download else self.words.PRICES
        v = self.values(f)
        src = self.lang + "-" + slug
        lede = copy["lede" if download else "free"].format(**v)
        if not download:
            lede += f'</p>\n  <p>{copy["pro"].format(**v)}</p>\n  <p>{self.bundle()}'
        # Reuse the English chrome so assets, nav and analytics cannot drift.
        source = landing.page("download" if download else "pricing", escape(copy["title"].format(**v)),
                              escape(copy["meta"].format(**v), quote=True), copy["h1"], lede,
                              src, not download, self.speed_section(f) if download else "")
        source = source.replace('<html lang="en">', f'<html lang="{self.lang}">')
        source = re.sub(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n', '', source)
        canonical = f'<link rel="canonical" href="{llms_txt.BASE}/{"download" if download else "pricing"}/">'
        english = f'{llms_txt.BASE}/{"download" if download else "pricing"}/'
        localized = f'{llms_txt.BASE}{self.routes["/"]}{slug}/'
        source = source.replace(canonical, f'<link rel="canonical" href="{localized}">\n' + '\n'.join(
            f'<link rel="alternate" hreflang="{lang}" href="{url}">'
            for lang, url in ((self.lang, localized), ("en", english), ("x-default", english))))
        source = source.replace('<body>', f'<body>\n<p class="app-language">{self.words.APP_LANGUAGE}</p>')
        source = re.sub(r'<!-- Generated by _tools/landing_pages.py.*?-->',
                        lambda m: self.words.GENERATOR_COMMENT, source, flags=re.S)
        source = source.replace(f'href="{llms_txt.BASE}/"', f'href="{llms_txt.BASE}{self.routes["/"]}"')
        source = source.replace(f'{llms_txt.BASE}/download/?src=nav-download', f'{llms_txt.BASE}{self.routes["/download/"]}?src=nav-download')
        source = source.replace('>Download</a>', f'>{self.words.NAV_DOWNLOAD}</a>')
        source = PBOX.sub(lambda m: self.box(src, not download, f), source)
        source = re.sub(r'  <p>Everything Pro adds,.*?</p>', lambda m: f'  <p>{copy["more"]}</p>', source)
        footer = (f'{self.words.CONTACT}\n<footer><div class="wrap">\n'
                  f'  <p>&#9670; {self.words.FOOTER["line"]} <a href="{llms_txt.BASE}{self.routes["/"]}">crispvideo.app</a> &middot; '
                  f'<a href="{llms_txt.BASE}/about/">{self.words.FOOTER["about"]}</a></p>\n'
                  f'  {landing.sitewide_chrome.KCO.replace("Made by Kerr &amp; Company", self.words.FOOTER["made_by"])}\n'
                  '</div></footer>')
        source = re.sub(r'<footer>.*?</footer>', lambda m: footer, source, flags=re.S)
        # founding.js inserts English sentences. Localized offers use data-until.
        return source.replace(landing.sitewide_chrome.founding_tag() + '\n', '')

    def refresh_boxes(self, source: str, name: str, f: dict) -> str:
        # Strip old wrappers before matching, so a second run is byte-for-byte stable.
        source = self.MARKED_BOX.sub(lambda m: PBOX.search(m.group(0)).group(0), source)
        slug = name.removeprefix(self.folder + "/").removesuffix("/index.html").replace("/", "-")
        if name == self.folder + "/index.html":
            slug = "home"
        count = 0

        def replace(match):
            nonlocal count
            count += 1
            return self.box(f'{self.lang}-{slug}-pbox-{count}', f=f)

        return PBOX.sub(replace, source)

    def pages(self) -> dict[Path, str]:
        landing.prepare_facts()
        f = llms_txt.facts()
        want = {self.SITE / name: self.page(slug, f) for name, slug in zip(self.FULL_PAGES, (self.download_slug, self.pricing_slug))}
        for name in self.OTHER_PAGES:
            source = self.refresh_boxes((self.SITE / name).read_text(encoding="utf-8"), name, f)
            # The homepage scaffold also carries a fixed schema version, not prose.
            source = re.sub(r'("softwareVersion":\s*")[^"]+(")',
                            lambda m: m.group(1) + f["version"] + m.group(2), source)
            want[self.SITE / name] = source
        return want

    def write(self, check: bool = False) -> int:
        want = self.pages()
        stale = [str(p.relative_to(self.SITE)) for p, source in want.items()
                 if not p.is_file() or p.read_text(encoding="utf-8") != source]
        if check:
            print(f"{self.words.LANGUAGE_NAME} pages: {'stale ' + ', '.join(stale) if stale else 'current'}")
            return 1 if stale else 0
        for p, source in want.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(source, encoding="utf-8")
        print(f"wrote {', '.join(str(p.relative_to(self.SITE)) for p in want)}")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lang")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        generator = LanguagePages(args.lang)
    except ValueError as error:
        parser.error(str(error))
    return generator.write(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
