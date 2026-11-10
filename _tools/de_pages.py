#!/usr/bin/env python3
"""Legacy German entry point for the shared language generator."""
import sys

from lang_pages import LanguagePages

_generator = LanguagePages("de")
SITE = _generator.SITE


def __getattr__(name):
    return getattr(_generator, name)


def pages():
    return LanguagePages("de", SITE).pages()


def write(check: bool = False) -> int:
    return LanguagePages("de", SITE).write(check=check)


if __name__ == "__main__":
    raise SystemExit(write(check="--check" in sys.argv[1:]))
