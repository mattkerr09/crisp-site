#!/usr/bin/env python3
"""Offline UTC date checks, with all page writes confined to temporary sites."""
import contextlib
import io
import os
import subprocess
import tempfile
import time
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

import dateline
import landing_pages
import new_pages
import page_dates
import utc_date

# The gate reads product facts at import time. Use the existing worktree resolver.
landing_pages.prepare_facts()
import gate_read_dates  # noqa: E402


MOMENT = datetime(2026, 11, 11, 3, tzinfo=timezone.utc)
UTC_DAY = date(2026, 11, 11)
LOCAL_DAY = date(2026, 11, 10)


class FrozenClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return MOMENT.astimezone(tz) if tz else MOMENT.astimezone().replace(tzinfo=None)


class LocalDate(date):
    @classmethod
    def today(cls):
        return FrozenClock.now().date()


@contextlib.contextmanager
def utc_boundary():
    try:
        with patch.dict(os.environ, {"TZ": "America/New_York"}), \
                patch.object(utc_date, "datetime", FrozenClock):
            time.tzset()
            assert LocalDate.today() == LOCAL_DAY
            yield
    finally:
        time.tzset()


def live_utc_day():
    before = datetime.now(timezone.utc).date()
    actual = utc_date.utc_today()
    after = datetime.now(timezone.utc).date()
    assert type(actual) is date
    assert actual in (before, after), actual


def midnight_boundary():
    with utc_boundary():
        assert utc_date.utc_today() == UTC_DAY
        assert utc_date.utc_today() != LocalDate.today()
        assert utc_date.utc_today_iso() == "2026-11-11"


def override_day():
    with patch.dict(os.environ, {"SITE_TODAY": "2024-02-29"}):
        assert utc_date.utc_today() == date(2024, 2, 29)
        assert utc_date.utc_today_iso() == "2024-02-29"


def bad_overrides():
    for value in ("", "tomorrow", "20261111", "2026-11-1", "2026-02-30", "2026-11-11 "):
        with patch.dict(os.environ, {"SITE_TODAY": value}):
            for helper in (utc_date.utc_today, utc_date.utc_today_iso):
                try:
                    helper()
                except ValueError:
                    continue
                raise AssertionError(f"{helper.__name__} accepted SITE_TODAY={value!r}")


@contextlib.contextmanager
def read_site():
    with tempfile.TemporaryDirectory() as directory:
        site = Path(directory)
        (site / "index.html").write_text("<p>Read 11 Nov 2026</p>", encoding="utf-8")
        yield site


def gate_scan_boundary():
    with read_site() as site, utc_boundary(), patch.object(gate_read_dates, "date", LocalDate):
        assert list(gate_read_dates.reads_in((site / "index.html").read_text())) == [UTC_DAY]
        verdicts = gate_read_dates.scan(site, known_undated=set())
        assert set(verdicts) == {"/"}
        verdict = verdicts["/"]
        assert not verdict.failed, f"Read 11 Nov 2026 rejected: {verdict.loose_reads}"
        assert gate_read_dates.scan(site, today=LOCAL_DAY, known_undated=set())["/"].failed


def gate_cli_boundary():
    with read_site() as site, utc_boundary(), patch.object(gate_read_dates, "date", LocalDate), \
            patch.object(gate_read_dates, "load_baseline", return_value=set()):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = gate_read_dates.main(["--site", str(site)])
        assert result == 0, output.getvalue()
        assert "on 2026-11-11;" in output.getvalue(), output.getvalue()
        with contextlib.redirect_stdout(io.StringIO()):
            assert gate_read_dates.main(["--site", str(site), "--today", "2026-11-10"]) == 1


def generated_page_date():
    page = {"h1": "UTC test", "desc": "Date test", "slug": "learn/utc-test",
            "title": "UTC test", "crumb": "UTC test", "body": "<p>Test content.</p>",
            "faq_heading": "Questions", "faq": [("Test question?", "Test answer.")]}
    with utc_boundary():
        assert '"datePublished":"2026-11-11"' in new_pages.build(page)
        with patch.dict(os.environ, {"SITE_TODAY": "2026-11-12"}):
            assert '"datePublished":"2026-11-12"' in new_pages.build(page)


def git_dates():
    with tempfile.TemporaryDirectory() as directory, utc_boundary():
        site = Path(directory)
        page = site / "index.html"
        page.write_text("<body><article><h1>Test</h1><p>Original content.</p></article></body>", encoding="utf-8")
        env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
               "GIT_AUTHOR_NAME": "UTC date test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
               "GIT_COMMITTER_NAME": "UTC date test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
               "GIT_AUTHOR_DATE": "2026-11-10T22:00:00-0500",
               "GIT_COMMITTER_DATE": "2026-11-10T22:00:00-0500"}

        def git(*args):
            return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args],
                                  cwd=site, env=env, check=True, capture_output=True, text=True).stdout.strip()

        git("init", "--quiet")
        git("add", "--", "index.html")
        git("commit", "--quiet", "-m", "UTC date fixture")
        assert git("log", "-1", "--format=%aI") == "2026-11-10T22:00:00-05:00"
        with patch.object(page_dates, "SITE", site), patch.object(dateline, "SITE", site):
            assert page_dates.content_changed(page) == "2026-11-11"
            assert dateline.last_visible_change(page) == "2026-11-11"
            assert os.environ["TZ"] == "America/New_York"
            page.write_text("<body><article><h1>Test</h1><p>Changed content.</p></article></body>", encoding="utf-8")
            assert page_dates.content_changed(page) == "2026-11-11"
            assert dateline.last_visible_change(page) == "2026-11-11"
            with patch.dict(os.environ, {"SITE_TODAY": "2026-11-12"}):
                assert page_dates.content_changed(page) == "2026-11-12"
                assert dateline.last_visible_change(page) == "2026-11-12"


def main():
    checks = (
        ("helper matches the live UTC date", live_utc_day),
        ("UTC day differs from New York at 03:00 UTC", midnight_boundary),
        ("SITE_TODAY overrides both helpers", override_day),
        ("malformed SITE_TODAY values raise", bad_overrides),
        ("scan accepts 11 Nov while New York is on 10 Nov", gate_scan_boundary),
        ("gate CLI defaults to UTC and keeps --today", gate_cli_boundary),
        ("generated pages use the UTC date and SITE_TODAY", generated_page_date),
        ("git readers use UTC and dirty pages use the shared helper", git_dates),
    )
    failures = 0
    with patch.dict(os.environ):
        os.environ.pop("SITE_TODAY", None)
        os.environ.pop("CRISP_ALLOW_STALE_READS", None)
        for label, check in checks:
            try:
                check()
            except Exception as exc:
                failures += 1
                print(f"FAIL: {label}: {type(exc).__name__}: {exc}")
            else:
                print(f"PASS: {label}")
    print(f"UTC date checks: {len(checks) - failures} passed, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
