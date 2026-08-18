#!/usr/bin/env python3
"""No third-party host may load for a visitor who has not opted into one.

WHY THIS EXISTS. On 2026-08-17 the homepage fired THREE cross-origin scripts on
load — two separate Plausible installs and usesled.com — 218px above a hero
reading "100% offline · Nothing uploaded · No account". The whole product is
sold on nothing leaving your machine, and the highest-value page carried the
heaviest tracker load in the repo. Sub-pages were clean; only index.html was
wrong, which is exactly the shape a human review misses.

Instruction did not prevent it. A comment sat directly above the Sled tag
arguing that the privacy claim was "scoped to the APP, not this website" — a
reasonable-sounding sentence that made the contradiction feel resolved. So this
is a gate, not a note.

WHAT IT CHECKS. Every host that a browser would CONTACT: script/img/iframe src,
link href with a rel that fetches (stylesheet, preload, preconnect), and any
url() in inline CSS. Anchor hrefs are NOT flagged — linking to topazlabs.com in
a comparison is not loading anything from them.

IT ALSO SCANS .js, and that is the part most likely to be dropped later. Sled is
now served first-party from /sled.js, so a gate that only read HTML would report
zero third-party hosts while a hardcoded usesled.com endpoint sat inside that
file. The existing pre-push hook already states the principle: a gate that
cannot see its subject must never report success.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Hosts a visitor may contact without having asked for anything.
ALLOWED_ON_LOAD = {"crispvideo.app", "plausible.io"}

#: Contacts that happen ONLY on an explicit user path, with the reason. These
#: are printed on every run rather than allowed silently — an exception nobody
#: sees again becomes the next incident.
#: host -> (file it is allowed to appear in, reason).
#:
#: SCOPED TO ONE FILE, and that scoping is the whole point. The first version of
#: this gate exempted usesled.com everywhere, so when I re-added the original
#: third-party <script src="https://usesled.com/..."> to test it, the gate went
#: GREEN on the exact bug it was written to catch. An exemption keyed on host
#: alone cannot tell "a beacon inside our own pinned script" from "a tracker we
#: just re-added to the homepage".
CONDITIONAL = {
    "usesled.com": ("sled.js",
                    "api/click beacon, fired strictly inside `if(ref)` — so only "
                    "for visitors who arrived on an affiliate ?ref= link, which "
                    "is what /legal/privacy/ discloses"),
}

FETCHING_REL = {"stylesheet", "preload", "prefetch", "preconnect", "dns-prefetch", "icon", "apple-touch-icon"}


def hosts_in(path: Path) -> set[tuple[str, str]]:
    """(host, why) pairs this file would cause a browser to contact."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    found: set[tuple[str, str]] = set()

    def host(u: str) -> str:
        m = re.match(r"https?://([^/\"'\s]+)", u)
        return m.group(1).lower() if m else ""

    if path.suffix == ".html":
        for tag, attr in (("script", "src"), ("img", "src"), ("iframe", "src"),
                          ("source", "src"), ("video", "src"), ("audio", "src")):
            for m in re.finditer(rf"<{tag}\b[^>]*\b{attr}=[\"']([^\"']+)", text, re.I):
                h = host(m.group(1))
                if h:
                    found.add((h, f"<{tag} {attr}>"))
        for m in re.finditer(r"<link\b[^>]*>", text, re.I):
            tag = m.group(0)
            rel = (re.search(r'rel=["\']([^"\']+)', tag, re.I) or [None, ""])[1].lower()
            if not any(r in FETCHING_REL for r in rel.split()):
                continue
            href = (re.search(r'href=["\']([^"\']+)', tag, re.I) or [None, ""])[1]
            h = host(href)
            if h:
                found.add((h, f"<link rel={rel}>"))

    for m in re.finditer(r"url\(\s*[\"']?(https?://[^)\"']+)", text, re.I):
        h = host(m.group(1))
        if h:
            found.add((h, "css url()"))

    if path.suffix == ".js":
        for m in re.finditer(r"[\"'](https?://[^\"'\s]+)[\"']", text):
            h = host(m.group(1))
            if h:
                found.add((h, "url in js"))

    return found


def main() -> int:
    files = [p for p in ROOT.rglob("*")
             if p.suffix in {".html", ".js"} and "_tools" not in p.parts and "node_modules" not in p.parts]
    if not files:
        print("FAIL: no files scanned — a gate that cannot see its subject must not pass.")
        return 1

    bad: list[str] = []
    seen_conditional: set[str] = set()

    for f in sorted(files):
        for h, why in sorted(hosts_in(f)):
            if h in ALLOWED_ON_LOAD:
                continue
            if h in CONDITIONAL and f.name == CONDITIONAL[h][0]:
                seen_conditional.add(h)
                continue
            bad.append(f"    {f.relative_to(ROOT)}  {h}  ({why})")

    print(f"  scanned {len(files)} file(s); allowed on load: {', '.join(sorted(ALLOWED_ON_LOAD))}")
    for h in sorted(seen_conditional):
        where, why = CONDITIONAL[h]
        print(f"  conditional: {h} (only in {where}) — {why}")

    if bad:
        print(f"\nFAIL: {len(bad)} third-party contact(s) a visitor did not ask for.")
        print("This site's hero says \"Nothing uploaded\". A tracker firing for every")
        print("visitor contradicts the product on the axis it is sold on.\n")
        for b in bad:
            print(b)
        print("\nSelf-host it (see /sled.js) or remove it. Adding a host to")
        print("ALLOWED_ON_LOAD requires a reason that survives being read aloud")
        print("to a customer.")
        return 1

    print("\nOK: no third-party host loads for an ordinary visitor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
