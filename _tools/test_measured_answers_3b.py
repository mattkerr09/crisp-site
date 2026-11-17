#!/usr/bin/env python3
"""Offline C1 and C3 answer checks, followed by the unchanged pre-push hook.

Use the earlier rounds' HTML and measurement checks. Both source pages must
already support the figures at this job's base; earlier rounds stay unchanged.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

import test_measured_answers as round_one
import test_measured_answers_2 as round_two
from test_measured_answers import QUICK, git


ROOT = Path(__file__).resolve().parent.parent
BASE = "74fddba3e644021255df2bd89a5f9fe7183ff7b2"
TEST = "_tools/test_measured_answers_3b.py"
UPDATED = "2026-11-17"
PAGES = {
    "vs/topaz-alternative-mac/index.html": (
        "/download/", "Mac upscaling test",
        ("3-second", "720p", "3.4 seconds", "Core ML", "M1 Ultra"),
    ),
    "learn/what-is-ai-video-upscaling/index.html": (
        "/", "Max restore sample",
        ("58 frames", "30 minutes 22 seconds", "M1 Ultra Mac Studio"),
    ),
}


def check_answer(raw, spec):
    # The shared checker reads its module's base and page set. Override neither:
    # it proves these sources predate Round 2, then check our own base as well.
    match = round_two.check_answer(raw, spec)
    source_url, _label, facts = spec
    target = ROOT / source_url.lstrip("/") / "index.html"
    published = round_one.visible(git("show", f"{BASE}:{target.relative_to(ROOT).as_posix()}"))
    answer = round_one.visible(match.group(1))
    for figure in round_one.NUMBER.findall(answer.text):
        assert figure in round_one.NUMBER.findall(published.text), f"unsourced number: {figure}"
    for fact in facts:
        assert fact in published.text, f"measurement missing from published source: {fact}"
    return match


class MeasuredAnswers(unittest.TestCase):
    def test_answers_and_controls(self):
        for name, spec in PAGES.items():
            with self.subTest(page=name):
                raw = (ROOT / name).read_text(encoding="utf-8")
                answer = check_answer(raw, spec)
                invented = round_one.NUMBER.sub("987654.321", answer.group(), count=1)
                self.assertNotEqual(invented, answer.group(), "invented-figure plant did not land")
                with self.assertRaisesRegex(AssertionError, "unsourced number: 987654.321"):
                    check_answer(raw[:answer.start()] + invented + raw[answer.end():], spec)
                source_url, label, _facts = spec
                missing = answer.group().replace(f'<a href="{source_url}">{label}</a>', label)
                self.assertNotEqual(missing, answer.group(), "missing-link plant did not land")
                with self.assertRaisesRegex(AssertionError, "missing visible source link"):
                    check_answer(raw[:answer.start()] + missing + raw[answer.end():], spec)
                moved = raw[:answer.start()] + raw[answer.end():]
                moved = moved.replace("</article>", answer.group() + "</article>", 1)
                with self.assertRaisesRegex(AssertionError, "answer must precede first h2"):
                    check_answer(moved, spec)
                print(f"{name}: sourced answer passes; invented figure, missing link and late answer fail", flush=True)

    def test_existing_copy_and_dates_preserved(self):
        for name in PAGES:
            with self.subTest(page=name):
                before = git("show", f"{BASE}:{name}")
                after = (ROOT / name).read_text(encoding="utf-8")
                old_quick, new_quick = QUICK.search(before), QUICK.search(after)
                self.assertIsNotNone(old_quick)
                self.assertIsNotNone(new_quick)
                # Move all original quick-box copy intact below the new box,
                # including the Topaz page's second paragraph. Prices, sale
                # lines, licence terms, legal text and FAQs stay byte-identical.
                old_body = old_quick.group().removeprefix('<div class="quick"><strong>Quick answer</strong>').removesuffix("</div>")
                expected = before.replace(old_quick.group(), new_quick.group() + "\n  " + old_body, 1)
                expected = re.sub(r'("dateModified":\s*")[^"]+', lambda m: m[1] + UPDATED, expected)
                expected = re.sub(r'last updated \d{4}-\d{2}-\d{2}', 'last updated ' + UPDATED, expected)
                self.assertEqual(expected, after)
                self.assertIn("last updated " + UPDATED, after)
                self.assertRegex(after, r'"dateModified":\s*"' + UPDATED + '"')

    def test_earlier_rounds_unchanged(self):
        for name in (*round_one.PAGES, *round_two.PAGES,
                     "_tools/test_measured_answers.py", "_tools/test_measured_answers_2.py"):
            with self.subTest(path=name):
                self.assertEqual(git("show", f"{BASE}:{name}"), (ROOT / name).read_text(encoding="utf-8"))
        for module in (round_one, round_two):
            for name, spec in module.PAGES.items():
                with self.subTest(page=name):
                    module.check_answer((ROOT / name).read_text(encoding="utf-8"), spec)

    def test_changed_paths(self):
        changed = set(git("diff", "--name-only", "-z", BASE, "--").split("\0"))
        changed.update(git("ls-files", "--others", "--exclude-standard", "-z").split("\0"))
        changed.discard("")
        self.assertEqual(changed, {*PAGES, TEST}, f"unexpected changed paths: {changed}")


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MeasuredAnswers)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    # Empty refs use the hook's declared non-release branch without network.
    if os.environ.get("CRISP_CHECK_TILL", "0") == "1":
        print("BLOCKED: CRISP_CHECK_TILL=1 would request network access", flush=True)
        return 1
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    hook = subprocess.run(["sh", ".githooks/pre-push"], cwd=ROOT, input="", text=True, env=env)
    print(f"sh .githooks/pre-push < /dev/null: exit {hook.returncode}", flush=True)
    # Propagate even the permitted worktree-only site-vs-engine BLOCKED result.
    return hook.returncode


if __name__ == "__main__":
    sys.exit(main())
