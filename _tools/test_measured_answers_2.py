#!/usr/bin/env python3
"""Offline checks for the C4, C8 and C10 answers, then the real pre-push hook.

Reuse Round 1's HTML reader. Source facts must already exist at the job's base,
and Round 1's pages and test must remain byte-for-byte unchanged.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import urlsplit

import test_measured_answers as round_one
from test_measured_answers import ANSWER, NUMBER, QUICK, git, visible


ROOT = Path(__file__).resolve().parent.parent
BASE = "0cb93158cbc7f1e47e34261e5ddf14e0f083bb28"
TEST = "_tools/test_measured_answers_2.py"
UPDATED = "2026-11-17"
PAGES = {
    "learn/why-topaz-ended-perpetual-licences/index.html": (
        "/learn/why-4k-exports-take-so-long/", "4K timing test",
        ("40-second", "1080p", "4K", "3 min 26 s", "M1 Ultra"),
    ),
    "how-to/fix-pixelated-video-mac/index.html": (
        "/how-to/upscale-video-on-mac/", "demo clip test",
        ("132 frames", "29 seconds", "M1 Ultra"),
    ),
    "learn/what-is-offline-video-editing/index.html": (
        "/learn/why-4k-exports-take-so-long/", "4K timing test",
        ("40-second", "1080p", "4K", "3 min 26 s", "M1 Ultra"),
    ),
}


def check_answer(raw, spec):
    source_url, label, facts = spec
    matches = list(ANSWER.finditer(raw))
    assert len(matches) == 1, "expected one measured answer"
    match = matches[0]
    first_h2 = re.search(r"<h2\b", raw, re.I)
    assert first_h2 and match.end() < first_h2.start(), "answer must precede first h2"
    quick = QUICK.search(raw)
    assert quick and quick.start() < match.start() < match.end() < quick.end(), "answer must be in quick box"
    h1 = re.search(r"<h1\b.*?</h1>", raw, re.S | re.I)
    assert h1 and h1.end() < quick.start(), "answer must follow h1"
    assert len(visible(raw[h1.end():quick.start()]).text.split()) < 40, "too much prose before answer"
    for landmark in (r"<aside\b", r"<figure\b"):
        first = re.search(landmark, raw, re.I)
        assert not first or match.end() < first.start(), "answer must precede product boxes and figures"
    answer = visible(match.group(1))
    assert not re.search(r"[\u2013\u2014()]", answer.text), "use plain punctuation"
    assert 2 <= len(re.split(r"(?<=[.!?])\s+", answer.text)) <= 4, "answer must have two to four sentences"
    links = [(href, "".join(parts).strip()) for href, parts in answer.links]
    assert (source_url, label) in links, "missing visible source link"
    assert len(links) == 1, "expected one measurement source"
    url = urlsplit(source_url)
    assert url.path.startswith("/") and not url.scheme and not url.netloc and not url.query and not url.fragment
    target = (ROOT / url.path.lstrip("/") / "index.html").resolve()
    assert target.is_relative_to(ROOT) and target.is_file(), "missing local source page"
    assert target.relative_to(ROOT).as_posix() not in PAGES, "source must be an unchanged page"
    figures = NUMBER.findall(answer.text)
    assert figures, "answer has no number"
    # Both versions must support the answer. New copy cannot become its own
    # evidence, and a number in metadata or an unrelated paragraph is not proof.
    for source in (target.read_text(encoding="utf-8"),
                   git("show", f"{BASE}:{target.relative_to(ROOT).as_posix()}")):
        source = ANSWER.sub("", source)
        text = visible(source).text
        sourced = set(NUMBER.findall(text))
        for figure in figures:
            assert figure in sourced, f"unsourced number: {figure}"
        blocks = re.findall(r"<(p|figcaption)\b[^>]*>(.*?)</\1>", source, re.S | re.I)
        assert any(all(fact in visible(body).text for fact in facts) for _tag, body in blocks), \
            "source must state the measurement and machine together"
    for fact in facts:
        assert fact in answer.text, f"measurement missing from answer: {fact}"
    return match


class MeasuredAnswers(unittest.TestCase):
    def test_answers_and_controls(self):
        for name, spec in PAGES.items():
            with self.subTest(page=name):
                raw = (ROOT / name).read_text(encoding="utf-8")
                answer = check_answer(raw, spec)
                invented = answer.group().replace("</p>", " Invented result: 987654.321 seconds.</p>")
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
                old_lede = re.search(r'<p class="lede">.*?</p>', old_quick.group(), re.S).group()
                # Preserve the original introduction verbatim below the new box.
                # Everything else, including prices, licence terms and FAQs,
                # must be identical apart from the two page-date values.
                expected = before.replace(old_quick.group(), new_quick.group() + "\n  " + old_lede, 1)
                expected = re.sub(r'("dateModified":\s*")[^"]+', lambda m: m[1] + UPDATED, expected)
                expected = re.sub(r'last updated \d{4}-\d{2}-\d{2}', 'last updated ' + UPDATED, expected)
                self.assertEqual(expected, after)
                self.assertIn("last updated " + UPDATED, after)
                self.assertRegex(after, r'"dateModified":\s*"' + UPDATED + '"')

    def test_round_one_unchanged(self):
        for name in (*round_one.PAGES, "_tools/test_measured_answers.py"):
            with self.subTest(path=name):
                self.assertEqual(git("show", f"{BASE}:{name}"), (ROOT / name).read_text(encoding="utf-8"))
        for name, spec in round_one.PAGES.items():
            with self.subTest(page=name):
                round_one.check_answer((ROOT / name).read_text(encoding="utf-8"), spec)

    def test_changed_paths(self):
        changed = set(git("diff", "--name-only", "-z", BASE, "--").split("\0"))
        changed.update(git("ls-files", "--others", "--exclude-standard", "-z").split("\0"))
        changed.discard("")
        self.assertFalse(changed - {*PAGES, TEST}, f"out-of-scope changes: {changed}")


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MeasuredAnswers)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    # Empty release refs take the hook's declared offline, non-release branch.
    if os.environ.get("CRISP_CHECK_TILL", "0") == "1":
        print("BLOCKED: CRISP_CHECK_TILL=1 would request network access", flush=True)
        return 1
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    hook = subprocess.run(["sh", ".githooks/pre-push"], cwd=ROOT, input="", text=True, env=env)
    print(f"sh .githooks/pre-push < /dev/null: exit {hook.returncode}", flush=True)
    # Do not hide even the allowed worktree-only site-vs-engine BLOCKED result.
    return hook.returncode


if __name__ == "__main__":
    sys.exit(main())
