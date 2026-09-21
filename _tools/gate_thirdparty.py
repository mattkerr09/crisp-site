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
#:
#: connect.facebook.net was added 2026-08-23, at the same time as the inline
#: <script> scan below — because until that scan existed this gate could not SEE
#: it, and had been printing "no third-party host loads for an ordinary visitor"
#: while Meta's pixel loaded on every visit. Listing it here is not a loosening:
#: it is the first time the host has been visible to this gate at all, and the
#: entry is what makes it deliberate rather than invisible.
#:
#: The reason, and it does have to survive being read aloud to a customer:
#: /legal/privacy/ names it explicitly — "An advertising pixel, which does set a
#: cookie. This site loads connect.facebook.net/en_US/fbevents.js, Meta's
#: advertising pixel" — and says plainly that a content blocker stops it. The
#: app still ships no analytics, no crash reporter and no advertising
#: identifiers; this is the marketing site, and the policy draws that line.
ALLOWED_ON_LOAD = {"crispvideo.app", "plausible.io", "connect.facebook.net"}

#: (host, PATH) pairs a visitor may load — and nothing else from that host.
#:
#: ⚠️ WHY EXACT AND NOT A HOST. This gate's own table above records a host-only
#: exemption going GREEN on the exact bug it was written to catch. A worker host
#: that may serve one 4.9 KB script must not thereby be allowed to serve a
#: beacon from the same origin tomorrow: /snippet.js is exempt, /anything-else
#: from the same host still fails. That is the whole point of carrying the path.
ALLOWED_ON_LOAD_EXACT = {
    ("kerr-affiliate-hub.kerrco.workers.dev", "/snippet.js"): (
        # The reason has to survive being read aloud to a customer, so here it is
        # in those words: "If you arrive from a partner's link, the referral code
        # is kept in your browser on this site and attached to the checkout link
        # if you buy, so the partner gets credited. It is not a cookie, and this
        # site sends it nowhere."
        #
        # Verified before the exemption was written, rather than taken from the
        # order that requested it:
        #   * the served file is SHA-256 identical to ops/affiliate-hub/snippet.js
        #     (88762a01f5705d9607c5eeec7f8d77735af1c83de2b3e1157c676f8b0b547986);
        #   * grepping that source for fetch( / XMLHttpRequest / document.cookie /
        #     navigator.sendBeacon returns NOTHING, and the same pattern with
        #     localStorage added returns 4 — so the empty result is a real
        #     absence and not a broken pattern;
        #   * /legal/privacy/ names it, in the section listing what the site
        #     stores, in the same commit that added the tag.
        #
        # ⚠️ IT IS SERVED WITHOUT SRI ON PURPOSE (the hub updates the file in
        # place and a stale integrity hash would silently kill it), so the hash
        # above is EVIDENCE OF WHAT WAS AUDITED, not an enforcement mechanism.
        # If that file changes, this exemption is describing something nobody
        # has read. Re-audit it rather than trusting this comment.
        "affiliate referral capture; first-party storage only, no cookie, no "
        "network call; named in /legal/privacy/"
    ),
}

#: (host, filename) pairs a SCRIPT may name because it assigns them to an href —
#: navigation, not a load. The module docstring already exempts anchor hrefs
#: ("linking to topazlabs.com in a comparison is not loading anything from
#: them"); a URL the page navigates you to is the same act whether the href was
#: authored in the markup or set by JS, so it gets the same answer.
#:
#: ⚠️ KEYED ON THE `why` AS WELL AS THE HOST, and that is the whole safety of it.
#: This gate's own history records an exemption keyed on host alone going GREEN
#: on the exact bug it was written to catch. These entries are consulted ONLY for
#: a hit whose reason is "url in inline <script>". Add a real
#: `<script src="https://github.com/…">` and it is reported as `<script src>`,
#: matches nothing here, and still FAILS. Proven with a planted tag, not assumed.
#: Every entry here must actually FIRE. A github.com entry was drafted for the
#: Crisp.dmg release asset and then removed on measurement: that URL turned out
#: to live only inside a JSON-LD block, which the inert-type rule below already
#: skips, so the exemption covered nothing. A dead exemption is worse than none —
#: it reads as a considered decision while silently exempting a case that never
#: occurs, and the day the host DOES appear for real it is pre-approved. If
#: github.com ever shows up as a genuine load, this gate should fail loudly and
#: somebody should decide about it then.
NAVIGATION_FROM_JS = {
    ("checkout.dodopayments.com", "index.html"):
        "CRISP_CHECKOUT_URL — assigned to the Buy button's href, so it is where a "
        "click SENDS you. Nothing is fetched from Dodo to render this page.",
}

#: Script blocks whose contents a browser never fetches. `application/ld+json` is
#: DATA: the parser reads it as structured data and resolves nothing, so the 114
#: `"@context":"https://schema.org"` strings across this site are not contacts.
#:
#: Every deliberate exemption creates a region where a defect and correctness look
#: identical, so state what is given up: a tracker URL hidden inside a JSON-LD
#: block would not be reported. That is acceptable ONLY because such a URL cannot
#: execute or fetch from there — it would be inert text. If this site ever ships a
#: script that READS its own JSON-LD and acts on a URL in it, this exemption stops
#: being safe and must go.
INERT_SCRIPT_TYPES = {"application/ld+json"}

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
#: The third field is a MARKER THE FILE MUST CONTAIN, and it exists because the file scoping
#: above is not enough on its own. Scoping to index.html would let the same endpoint be moved
#: from a submit handler to a load handler and still pass — which is the entire failure this
#: gate exists to prevent, just relocated. The marker makes the exemption describe the CODE,
#: not the filename. (I made exactly this mistake in the sibling pytest gate an hour ago: two
#: of three controls sailed through a page-scoped exemption.)
CONDITIONAL = {
    "usesled.com": ("sled.js",
                    "api/click beacon, fired strictly inside `if(ref)` — so only "
                    "for visitors who arrived on an affiliate ?ref= link, which "
                    "is what /legal/privacy/ discloses",
                    "if(ref)"),
    "kerr-subscribe.kerrco.workers.dev":
                   (("index.html", "notify.js"),
                    "the subscribe form's POST, fired only inside a submit handler — a "
                    "visitor types an address and presses a button, and that press is the "
                    "only thing that sends it. Nothing leaves the page on load. First-party "
                    "on purpose: a marketing SDK here would contradict the hero",
                    "addEventListener('submit'"),

    # The on-page assistant. Added deliberately, using this gate's own mechanism
    # rather than by widening ALLOWED_ON_LOAD — the script is FIRST-PARTY
    # (/assistant.js), so nothing third-party loads for a visitor who never opens
    # it. The reason has to survive being read aloud to a customer, so here it is
    # in those words: "It contacts our server only when you type a question and
    # press send. Nothing is sent when the page loads."
    #
    # The marker is the submit handler the fetch lives inside. Move the fetch out
    # of that handler and this exemption stops applying, which is the point of
    # requiring one.
    # ⚠️ founding.js LEFT THIS TABLE AND CAME BACK ON THE SAME DAY (2026-09-15), WITH ITS
    # MARKER BOTH TIMES. It was removed when the seat counter was held pending Matthew's
    # decision on whether the offer has a cap at all; he decided each app gets its own 25 seats
    # and its own code, the worker went per-site, and the counter returned. Recorded because the
    # round trip is the whole lesson of this mechanism: the entry went DEAD earlier that day and
    # kept printing a reason for behaviour that had been deleted, which is why
    # _tools/gate_exemptions_live.py now exists and why the file and its marker are only ever
    # added or removed TOGETHER. Never re-add a file here without a marker that actually matches.
    "kerr-lead-agent.kerrco.workers.dev":
                   (("assistant.js", "founding.js"),
                    "both fired only inside a handler a visitor triggers — the assistant's "
                    "question on submit, the founding counter on a click asking how many of "
                    "Crisp's own 25 seats are left. Nothing on load, nothing at all for a "
                    "visitor who opens neither. Both widgets are served first-party",
                    {"assistant.js": 'form.addEventListener("submit"',
                     "founding.js":  "countBtn.addEventListener('click'"}),
}

FETCHING_REL = {"stylesheet", "preload", "prefetch", "preconnect", "dns-prefetch", "icon", "apple-touch-icon"}


def hosts_in(path: Path) -> set[tuple[str, str, str]]:
    """(host, why, url-path) triples this file would cause a browser to contact.

    The PATH is carried because an exemption keyed on host alone is this gate's
    own recorded failure: one went green on the exact bug it was written to
    catch. A host that may serve one file may not thereby serve every file.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    found: set[tuple[str, str, str]] = set()

    def host(u: str) -> str:
        m = re.match(r"https?://([^/\"'\s]+)", u)
        return m.group(1).lower() if m else ""

    def urlpath(u: str) -> str:
        """The path a browser would request, query and fragment stripped.

        "" when there is none, so a bare host reads as "/" nowhere and cannot
        accidentally match an exact-path exemption.
        """
        m = re.match(r"https?://[^/\"'\s]+([^\s\"'<>()\\]*)", u)
        raw = m.group(1) if m else ""
        return raw.split("?")[0].split("#")[0]

    if path.suffix == ".html":
        for tag, attr in (("script", "src"), ("img", "src"), ("iframe", "src"),
                          ("source", "src"), ("video", "src"), ("audio", "src")):
            for m in re.finditer(rf"<{tag}\b[^>]*\b{attr}=[\"']([^\"']+)", text, re.I):
                h, up = host(m.group(1)), urlpath(m.group(1))
                if h:
                    found.add((h, f"<{tag} {attr}>", up))
        for m in re.finditer(r"<link\b[^>]*>", text, re.I):
            tag = m.group(0)
            rel = (re.search(r'rel=["\']([^"\']+)', tag, re.I) or [None, ""])[1].lower()
            if not any(r in FETCHING_REL for r in rel.split()):
                continue
            href = (re.search(r'href=["\']([^"\']+)', tag, re.I) or [None, ""])[1]
            h, up = host(href), urlpath(href)
            if h:
                found.add((h, f"<link rel={rel}>", up))

    for m in re.finditer(r"url\(\s*[\"']?(https?://[^)\"']+)", text, re.I):
        h, up = host(m.group(1)), urlpath(m.group(1))
        if h:
            found.add((h, "css url()", up))

    if path.suffix == ".js":
        for m in re.finditer(r"[\"'](https?://[^\"'\s]+)[\"']", text):
            h, up = host(m.group(1)), urlpath(m.group(1))
            if h:
                found.add((h, "url in js", up))

    # ── INLINE <script> BODIES ────────────────────────────────────────────────
    # THE HOLE THAT MADE THIS GATE REPORT GREEN WHILE A TRACKER LOADED.
    # The Meta pixel builds its own element — `t=b.createElement(e); t.src=v` —
    # and passes the URL as a bare argument:
    #
    #   }(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    #
    # There is no `src=` ATTRIBUTE, so none of the HTML patterns above match, and
    # it is not a `url()`, so the CSS pattern misses it too. The permissive scan
    # that WOULD have caught it is three lines up, fenced behind
    # `path.suffix == ".js"` — and an inline block lives in a .html file, so it
    # never reaches it. The gate printed "no third-party host loads for an
    # ordinary visitor" on the very commit that added the pixel.
    #
    # That is this repo's own recorded failure mode, one level down: a checker
    # whose extraction is shaped like the input it expects cannot see input of
    # another shape. The fix is the standing rule — EXTRACT PERMISSIVELY, JUDGE
    # STRICTLY. Take every absolute URL in the block, quoted or bare, and let
    # the allow-lists below do the deciding.
    if path.suffix == ".html":
        for blk in re.finditer(r"<script\b([^>]*)>(.*?)</script>", text, re.I | re.S):
            stype = (re.search(r'type=["\']([^"\']+)', blk.group(1), re.I) or [None, ""])[1].strip().lower()
            if stype in INERT_SCRIPT_TYPES:
                continue
            for u in re.finditer(r"https?://[^\s\"'<>()\\]+", blk.group(2)):
                h, up = host(u.group(0)), urlpath(u.group(0))
                if h:
                    found.add((h, "url in inline <script>", up))

    return found


def main() -> int:
    files = [p for p in ROOT.rglob("*")
             if p.suffix in {".html", ".js"} and "_tools" not in p.parts and "node_modules" not in p.parts]
    if not files:
        print("FAIL: no files scanned — a gate that cannot see its subject must not pass.")
        return 1

    bad: list[str] = []
    seen_conditional: set[str] = set()
    seen_exact: set[tuple[str, str]] = set()
    seen_navigation: set[tuple[str, str]] = set()

    for f in sorted(files):
        for h, why, upath in sorted(hosts_in(f)):
            # EXACT (host, path) first: narrower than ALLOWED_ON_LOAD, and the
            # only thing that lets a host serve one file without serving all.
            if (h, upath) in ALLOWED_ON_LOAD_EXACT:
                seen_exact.add((h, upath))
                continue
            if h in ALLOWED_ON_LOAD:
                continue
            # A host may legitimately appear in MORE THAN ONE file — the subscribe
            # POST is in index.html and in notify.js, both inside submit handlers.
            # Accepting a tuple keeps the exemption per-FILE rather than
            # per-host: each named file must still carry the marker, so adding a
            # second file does not weaken the first.
            _spec = CONDITIONAL.get(h)
            _files = () if _spec is None else (
                (_spec[0],) if isinstance(_spec[0], str) else tuple(_spec[0]))
            if _spec is not None and f.name in _files:
                # The marker must be PRESENT in this file, or the exemption does not apply.
                # Without it, moving the same call out of its guard keeps the pass.
                # ⚠️ A MARKER PER FILE, not per host. Two files can both hold a
                # legitimate conditional call and guard it DIFFERENTLY — the
                # assistant's fetch lives in a submit handler, the founding
                # counter's in a click handler. One shared marker would have to
                # be loose enough to match both, which is exactly the weakening
                # this mechanism exists to prevent. A dict keeps each file's
                # exemption tied to its own guard.
                _m = CONDITIONAL[h][2]
                marker = _m if isinstance(_m, str) else _m.get(f.name)
                if marker and marker in f.read_text(encoding="utf-8", errors="replace"):
                    seen_conditional.add(h)
                    continue
            # Navigation targets — consulted ONLY for an inline-script hit, so a
            # real <script src> or <img src> from the same host still fails.
            if why == "url in inline <script>" and (h, f.name) in NAVIGATION_FROM_JS:
                seen_navigation.add((h, f.name))
                continue
            bad.append(f"    {f.relative_to(ROOT)}  {h}  ({why})")

    print(f"  scanned {len(files)} file(s); allowed on load: {', '.join(sorted(ALLOWED_ON_LOAD))}")
    for h in sorted(seen_conditional):
        _w = CONDITIONAL[h][0]
        where = _w if isinstance(_w, str) else " and ".join(_w)
        why = CONDITIONAL[h][1]
        print(f"  conditional: {h} (only in {where}) — {why}")
    # Printed on every run, never allowed silently: an exemption nobody sees
    # again becomes the next incident.
    for h, where in sorted(seen_navigation):
        print(f"  navigation:  {h} (in {where}) — {NAVIGATION_FROM_JS[(h, where)]}")
    # Exact (host, path) exemptions, printed for the same reason as the two
    # above: a host that loads on EVERY visit and is never named in this gate's
    # output is invisible, and invisible is how the Meta pixel loaded for weeks
    # while the last line said nothing third-party loaded at all.
    for h, up in sorted(seen_exact):
        print(f"  exact:       {h}{up} (this path only) — {ALLOWED_ON_LOAD_EXACT[(h, up)]}")

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

    # ⚠️ SAY WHAT IS TRUE, NOT WHAT WAS TRUE BEFORE THE ALLOWLIST EXISTED. This printed
    # "no third-party host loads for an ordinary visitor" — the sentence the header comment
    # above records as the ORIGINAL defect, from back when the gate could not see Meta's pixel.
    # The pixel is visible and deliberate now, but it still loads on every visit, so the old
    # sentence is exactly as false as it was then; only the reason changed. Anyone auditing
    # privacy runs this gate and reads its last line, and that line has to survive being read
    # aloud next to /legal/privacy/. Name the hosts instead of claiming there are none.
    # ⚠️ AND THE EXACT-PATH EXEMPTIONS BELONG IN THIS SENTENCE TOO. The affiliate
    # snippet loads from a third-party host on EVERY page for EVERY visitor. Listing
    # only ALLOWED_ON_LOAD here would have printed "nothing third-party loads except
    # connect.facebook.net, plausible.io" on a run where a third host loaded 124 times
    # — the same false last line this comment was written about, one mechanism later.
    # A narrower exemption is not a quieter one.
    third = sorted(h for h in ALLOWED_ON_LOAD if h != "crispvideo.app")
    third += sorted(f"{h}{up}" for h, up in seen_exact)
    if third:
        print("\nOK: nothing third-party loads for an ordinary visitor except the hosts "
              "allowed above — " + ", ".join(third) + " — each with a stated reason.")
    else:
        print("\nOK: no third-party host loads for an ordinary visitor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
