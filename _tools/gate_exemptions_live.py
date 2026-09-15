#!/usr/bin/env python3
"""Every exemption in gate_thirdparty.py must actually FIRE.

WHY THIS EXISTS. On 2026-09-15 `founding.js` stopped fetching the founding count
— a deliberate change, made for a good reason. What nobody noticed is that
gate_thirdparty.py kept its CONDITIONAL exemption for that file, keyed to the
marker `countBtn.addEventListener('click'`, and went on PRINTING on every run
that the founding counter fires "on a click asking how many places are left".

That sentence was false for as long as the fetch was gone. Anyone auditing this
site's privacy runs that gate and reads its output, and the output described
behaviour that had been deleted. Worse, the exemption was pre-approval sitting in
wait: the day that host reappeared in that file for any reason — a tracker, a
beacon, anything — it would have passed silently.

gate_thirdparty.py's own docstring already states the rule:

    "A dead exemption is worse than none — it reads as a considered decision
    while silently exempting a case that never occurs, and the day the host DOES
    appear for real it is pre-approved."

It states it, and nothing enforced it, and it rotted anyway. That file's other
lesson applies to its own rule: "Instruction did not prevent it ... So this is a
gate, not a note."

WHAT LIVE MEANS, AND WHY BOTH HALVES ARE NEEDED. An exemption is live only if the
named file BOTH (a) really contains the host as a URL a browser would contact, so
the gate would otherwise flag it, AND (b) carries its marker. Checking only the
marker would call an exemption healthy when the call it excuses is gone; checking
only the host would call it healthy when the call has escaped its guard — which
is the entire failure gate_thirdparty.py's markers exist to catch.

⚠️ THIS GATE'S OWN VACUITY. It was run against the pre-fix founding.js before
being committed and reported "DEAD: host never appears, marker=NO" — so it can
see the defect it was written for, rather than passing over an empty table. The
file-count check below is the standing version of that: an exemption table that
reads as empty must fail rather than pass.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("g", Path(__file__).resolve().parent / "gate_thirdparty.py")
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)


def _find(name: str) -> Path | None:
    return next((q for q in ROOT.rglob(name) if "_tools" not in q.parts), None)


def main() -> int:
    checked = 0
    dead: list[str] = []

    for host, spec in g.CONDITIONAL.items():
        files = (spec[0],) if isinstance(spec[0], str) else tuple(spec[0])
        markers = spec[2]
        for fname in files:
            checked += 1
            p = _find(fname)
            if p is None:
                dead.append(f"    {host}  ->  {fname}: THE FILE NO LONGER EXISTS")
                continue
            flagged = any(h == host for h, _ in g.hosts_in(p))
            marker = markers if isinstance(markers, str) else markers.get(fname)
            has_marker = bool(marker) and marker in p.read_text(encoding="utf-8", errors="replace")
            if not flagged:
                dead.append(f"    {host}  ->  {fname}: the host never appears, so this "
                            f"exemption excuses nothing and pre-approves it if it returns")
            elif not has_marker:
                dead.append(f"    {host}  ->  {fname}: marker {marker!r} is absent, so the "
                            f"call is no longer inside the guard the exemption describes")
            else:
                print(f"  live: {host}  ({fname})")

    for (host, fname), why in g.NAVIGATION_FROM_JS.items():
        checked += 1
        p = _find(fname)
        hits = [w for h, w in g.hosts_in(p) if h == host] if p else []
        if "url in inline <script>" in hits:
            print(f"  live: {host}  ({fname}, navigation)")
        else:
            dead.append(f"    {host}  ->  {fname}: no inline-<script> hit, so this navigation "
                        f"exemption is consulted for nothing (hits: {hits or 'none'})")

    # A table that reads as empty must FAIL. A gate that cannot see its subject
    # must never report success — the pre-push hook's own words.
    if checked == 0:
        print("FAIL: no exemptions were examined — gate_thirdparty.py's tables read as empty.")
        return 1

    if dead:
        print(f"\nFAIL: {len(dead)} of {checked} exemption(s) in gate_thirdparty.py are DEAD.\n")
        print("A dead exemption reads as a considered decision while excusing a case that")
        print("never occurs, and pre-approves that host for the day it returns. Either")
        print("restore the behaviour the exemption describes, or delete the entry.\n")
        for d in dead:
            print(d)
        return 1

    print(f"\nOK: all {checked} exemption(s) in gate_thirdparty.py fire on real code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
