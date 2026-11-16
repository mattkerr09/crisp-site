#!/usr/bin/env python3
"""Offline checks for the C2, C5 and C9 answers, followed by the real pre-push hook.

Published source copy is checked against the job's base commit too, so adding a
number to an answer cannot make that number its own evidence.
"""
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
BASE = "a034b2e911134e179e0a56912ec503c3a6b8d3d3"
TEST = "_tools/test_measured_answers.py"
PAGES = {
    "how-to/restore-old-film-footage-mac/index.html": (
        "/vs/video2x-alternative-mac/", "newsreel test",
        ("6-second", "4×", "17.5 seconds", "M1 Ultra"),
    ),
    "how-to/upscale-video-on-mac/index.html": (
        "/learn/why-4k-exports-take-so-long/", "4K timing test",
        ("40-second", "1080p", "4K", "3 min 26 s", "M1 Ultra"),
    ),
    "best/free-video-upscaler-mac/index.html": (
        "/how-to/upscale-video-on-mac/", "demo clip test",
        ("29 seconds", "132 frames", "M1 Ultra"),
    ),
}
QUICK = re.compile(r'<div class="quick"><strong>Quick answer</strong>.*?</div>', re.S)
ANSWER = re.compile(r'<p class="lede" id="measured-answer">(.*?)</p>', re.S)
NUMBER = re.compile(r"(?<![\d.])\d+(?:[,.]\d+)*(?![\d.])")


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.skip = []
        self.link = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"head", "script", "style", "template", "noscript"}:
            self.skip.append(tag)
        if self.skip:
            return
        if tag in {"p", "td", "th", "li", "br", "div", "figcaption"}:
            self.parts.append(" ")
        if tag == "a":
            self.link = [attrs.get("href", ""), []]
            self.links.append(self.link)

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
            return
        if tag == "a":
            self.link = None
        if tag in {"p", "td", "th", "li", "div", "figcaption"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)
            if self.link is not None:
                self.link[1].append(data)

    @property
    def text(self):
        return " ".join("".join(self.parts).split())


def visible(raw):
    page = Visible()
    page.feed(raw)
    page.close()
    return page


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True).stdout.decode("utf-8")


def check_answer(raw, spec):
    source_url, label, facts = spec
    matches = list(ANSWER.finditer(raw))
    assert len(matches) == 1, "expected one measured answer"
    match = matches[0]
    first_h2 = re.search(r"<h2\b", raw, re.I)
    assert first_h2 and match.end() < first_h2.start(), "answer must precede first h2"
    quick = QUICK.search(raw)
    assert quick and quick.start() < match.start() < match.end() < quick.end(), "answer must be in quick box"
    answer = visible(match.group(1))
    assert not re.search(r"[\u2013\u2014()]", answer.text), "use plain punctuation"
    # A decimal point inside a measurement is not a sentence ending.
    sentences = re.split(r"(?<=[.!?])\s+", answer.text)
    assert 2 <= len(sentences) <= 4, "answer must have two to four sentences"
    links = [(href, "".join(parts).strip()) for href, parts in answer.links]
    assert (source_url, label) in links, "missing visible source link"
    assert len(links) == 1, "each answer must link its measurement to one source"
    url = urlsplit(source_url)
    assert not url.scheme and not url.netloc and not url.query and not url.fragment
    target = (ROOT / url.path.lstrip("/") / "index.html").resolve()
    assert target.is_relative_to(ROOT) and target.is_file(), "missing local source page"
    # Exclude the new answer, including when the source is another changed page.
    source = visible(ANSWER.sub("", target.read_text(encoding="utf-8"))).text
    published = visible(git("show", f"{BASE}:{target.relative_to(ROOT).as_posix()}")).text
    figures = NUMBER.findall(answer.text)
    assert figures, "answer has no number"
    for text in (source, published):
        sourced = set(NUMBER.findall(text))
        for figure in figures:
            assert figure in sourced, f"unsourced number: {figure}"
        for fact in facts:
            assert fact in text, f"measurement missing from source: {fact}"
    for fact in facts:
        assert fact in answer.text, f"measurement missing from answer: {fact}"
    assert "M1 Ultra" in answer.text, "measurement must name its Mac"
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
                # The old introduction stays verbatim, immediately after the new
                # answer. This protects offers, licence terms and all FAQ copy.
                expected = before.replace(old_quick.group(), new_quick.group() + "\n  " + old_lede, 1)
                expected = re.sub(r'("dateModified":\s*")[^"]+', r'\g<1>2026-11-16', expected)
                expected = re.sub(r'last updated \d{4}-\d{2}-\d{2}', 'last updated 2026-11-16', expected)
                self.assertEqual(expected, after)
                self.assertIn("last updated 2026-11-16", after)
                self.assertRegex(after, r'"dateModified":\s*"2026-11-16"')

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
    # No release refs and no forced checkout check: the hook's declared
    # non-release branch must skip the network-only till check.
    if os.environ.get("CRISP_CHECK_TILL", "0") == "1":
        print("BLOCKED: CRISP_CHECK_TILL=1 would request network access", flush=True)
        return 1
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    hook = subprocess.run(["sh", ".githooks/pre-push"], cwd=ROOT, input="", text=True, env=env)
    print(f"sh .githooks/pre-push < /dev/null: exit {hook.returncode}", flush=True)
    # Preserve even the permitted worktree-only BLOCKED result for the reviewer.
    return hook.returncode


if __name__ == "__main__":
    sys.exit(main())
