#!/usr/bin/env python3
"""Offline checks of landing language clusters in isolated site copies."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


LINK = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">')
ROUTES = {
    "download": {"en": "/download/", "de": "/de/download/",
                 "es": "/es/descargar/", "pt-BR": "/pt-br/download/"},
    "pricing": {"en": "/pricing/", "de": "/de/preise/",
                "es": "/es/precios/", "pt-BR": "/pt-br/precos/"},
}


def check_copy(de_only: bool) -> None:
    import landing_pages as landing
    import lang_pages
    import llms_txt

    languages = ("de",) if de_only else ("de", "es", "pt-br")
    tags = ("de", "en", "x-default") if de_only else ("en", "de", "es", "pt-BR", "x-default")
    for slug, routes in ROUTES.items():
        expected = {tag: llms_txt.BASE + routes["en" if tag == "x-default" else tag] for tag in tags}
        sources = [landing.alternates(slug)]
        sources += [lang_pages.alternates(f"/{slug}/", lang_pages.load_words(lang)) for lang in languages]
        for source in sources:
            links = LINK.findall(source)
            assert [tag for tag, href in links] == list(tags), links
            assert dict(links) == expected, links
            for tag, href in links:
                route = href.removeprefix(llms_txt.BASE)
                assert (landing.SITE / route.lstrip("/") / "index.html").is_file(), href
        if de_only:
            legacy = "".join(f'<link rel="alternate" hreflang="{tag}" href="{expected[tag]}">\n'
                             for tag in ("de", "en", "x-default"))
            assert sources[0].encode() == legacy.encode(), slug

    # A strings file alone cannot advertise a page, and each door is checked separately.
    missing = landing.SITE / "de/download/index.html"
    missing.unlink()
    assert "de" not in dict(LINK.findall(landing.alternates("download")))
    assert "de" in dict(LINK.findall(landing.alternates("pricing")))
    for routes in ROUTES.values():
        for tag, route in routes.items():
            if tag != "en":
                (landing.SITE / route.lstrip("/") / "index.html").unlink(missing_ok=True)
    for slug, routes in ROUTES.items():
        assert dict(LINK.findall(landing.alternates(slug))) == {
            "en": llms_txt.BASE + routes["en"], "x-default": llms_txt.BASE + routes["en"]}
    assert landing.alternates("w") == ""


def main() -> None:
    tools = Path(__file__).resolve().parent
    for de_only in (True, False):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            copied_tools = site / "_tools"
            copied_tools.mkdir()
            for source in tools.glob("*.py"):
                shutil.copy2(source, copied_tools / source.name)
            # Leave all page files in place when hiding modules. Neither condition alone is enough.
            if de_only:
                for name in ("strings_pt_br.py", "strings_es.py"):
                    (copied_tools / name).rename(copied_tools / (name + ".hidden"))
            for routes in ROUTES.values():
                for route in routes.values():
                    page = site / route.lstrip("/") / "index.html"
                    page.parent.mkdir(parents=True, exist_ok=True)
                    page.write_text("<!DOCTYPE html>\n", encoding="utf-8")
            subprocess.run([sys.executable, str(copied_tools / Path(__file__).name),
                            "--copy", "de-only" if de_only else "all"], check=True)
    print("landing alternates: German-only bytes, both reciprocal clusters, missing modules and missing pages passed")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--copy":
        check_copy(sys.argv[2] == "de-only")
    else:
        main()
