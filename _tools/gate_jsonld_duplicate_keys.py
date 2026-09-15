#!/usr/bin/env python3
"""No JSON-LD block may declare the same key twice.

WHY THIS EXISTS. `_tools/page_dates.py` matched `"dateModified":"…"` with NO space after the
colon. 94 of 122 pages carry `"dateModified": "…"` WITH a space, so the pattern matched nothing
on them, the substitution was a no-op, and the insertion fallback concluded the key was ABSENT
and appended a second one at the end of the object. Sixteen pages shipped like this:

    {"datePublished": "2026-07-04", "dateModified": "2026-09-15", … ,"dateModified":"2026-09-07"}

⚠️ AND THE STALE ONE WON. A JSON parser keeps the LAST occurrence of a repeated key, so the
freshly computed date was silently discarded and crawlers read the older one. MEASURED on the
live site: best/free-video-upscaler-mac parsed to **2026-09-07** while the correct 2026-09-15 sat
in the same object, ignored. The tool whose entire purpose is to keep this field honest was
reporting success while making the field wrong.

★ WHY GREP COULD NOT FIND THIS AND A PARSER CAN. Every check anyone would naturally write stayed
GREEN: the correct value WAS in the file, the JSON WAS valid (duplicate keys are legal to
`json.loads`, which just keeps the last), and `.count('dateModified')` is not something anyone
thinks to assert. The defect is not a wrong value or a broken file — it is a value that never
wins. That is the recorded "right value, silently overwritten later" shape, in structured data
nobody ever looks at with their eyes.

The fix is `object_pairs_hook`, which is the only way to SEE a duplicate: by the time you have a
dict, the evidence has been thrown away.

⚠️ This checks EVERY key at EVERY depth, not just dateModified. The specific bug was one field;
the shape — a writer that appends because its reader could not find what was already there — is
not field-specific, and a gate written around the one field we happened to hit would miss the
next one.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


class Duplicate(ValueError):
    pass


def _no_duplicates(pairs):
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise Duplicate(k)
        seen.add(k)
    return dict(pairs)


def main() -> int:
    pages = [p for p in sorted(ROOT.rglob("*.html")) if "_tools" not in p.parts]
    if not pages:
        print("FAIL: no pages scanned — a gate that cannot see its subject must not pass.")
        return 1

    blocks = 0
    bad: list[str] = []
    unparseable: list[str] = []

    for p in pages:
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in BLOCK.finditer(text):
            blocks += 1
            try:
                json.loads(m.group(1), object_pairs_hook=_no_duplicates)
            except Duplicate as e:
                bad.append(f"    {p.relative_to(ROOT)}  declares {e.args[0]!r} twice in one "
                           f"JSON-LD object — the LAST one wins and the other is discarded")
            except Exception:
                # Malformed JSON-LD is a different defect with its own owner; this gate is about
                # duplicate keys only. Counted so a page that stops parsing cannot quietly shrink
                # this gate's coverage to nothing.
                unparseable.append(str(p.relative_to(ROOT)))

    # VACUITY GUARD. Without this, a regex that stops matching reports a clean site.
    if blocks < 100:
        print(f"FAIL: only {blocks} JSON-LD block(s) found across {len(pages)} page(s) — "
              f"the extractor has gone blind; this gate would pass over nothing.")
        return 1

    print(f"  scanned {blocks} JSON-LD block(s) across {len(pages)} page(s)")
    if unparseable:
        print(f"  note: {len(unparseable)} block(s) did not parse and were not checked here")

    if bad:
        print(f"\nFAIL: {len(bad)} JSON-LD block(s) declare a key twice.\n")
        print("A duplicate key is valid JSON and invalid JSON-LD: the parser keeps the LAST")
        print("value and silently drops the other, so the field can be 'correct' in the file")
        print("and wrong to every crawler. Usually means a writer appended a key because its")
        print("reader could not find the one already there — fix the reader, not the symptom.\n")
        for b in bad:
            print(b)
        return 1

    print("\nOK: no JSON-LD block declares a key twice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
