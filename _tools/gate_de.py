#!/usr/bin/env python3
"""Legacy German entry point for the shared language gate."""
import sys
from contextlib import redirect_stdout
import io
from unittest.mock import patch

import de_pages
import gate_lang

_gate = gate_lang.LanguageGate("de")


def __getattr__(name):
    if hasattr(_gate, name):
        return getattr(_gate, name)
    return getattr(gate_lang, name)


def selftest() -> int:
    result = _gate.selftest()
    if result:
        return result
    # The English generator still calls the legacy German module.
    with patch.object(de_pages, "write", return_value=1) as german_check, redirect_stdout(io.StringIO()):
        assert de_pages.landing.main(["--check"]) == 1
        german_check.assert_called_once_with(check=True)
    return 0


def main() -> int:
    return gate_lang.main(lang="de", selftest=selftest)


if __name__ == "__main__":
    sys.exit(main())
