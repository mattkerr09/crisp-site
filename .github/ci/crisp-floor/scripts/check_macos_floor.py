#!/usr/bin/env python3
"""Release floor gate: a built Crisp.app must not need a newer macOS than the one we declare.

    python3 scripts/check_macos_floor.py path/to/Crisp.app [--conf ui/src-tauri/tauri.conf.json]

THE DECLARED FLOOR HAS ONE HOME: ui/src-tauri/tauri.conf.json `bundle.macOS.minimumSystemVersion`. Tauri copies it
into the app's Info.plist as LSMinimumSystemVersion (the only floor macOS itself enforces), and the site's requirement
line is tied to the same number by tests/test_the_os_we_promise_is_the_os_the_binaries_accept.py. This gate reads it
from there and nowhere else, so lowering the floor is one edit, and a build that does not meet it cannot ship.

Exit 1 (and nothing may be published) when either is true:
  1. a Mach-O file in the app declares a `minos` above the declared floor. The highest is read by
     scripts/macos_floor.sh --full (the same reader the release page's "macOS N+" comes from), and a second, independent
     sweep here reads every file by its Mach-O magic, so the two instruments agree for different reasons and the error
     can name the files;
  2. the app's LSMinimumSystemVersion is not the declared floor (a front door that says 26 over binaries built for 14
     turns away buyers the build supports; one that says 12 over binaries built for 14 lets a buyer pay and fail).
Exit 2 when it cannot read the floor, the plist or any minos: a gate that cannot see its subject fails, it never passes.

WHY IT EXISTS. On 1.0.1252 the plist said 12.0 and 79 of 84 Mach-O files needed 26 (Homebrew's Python and ffmpeg, built
on this macOS 26 box). Nothing in the release path compared the two, because every check ran ON the build box, above the
hidden floor: a machine cannot detect a floor it is standing on. This compares declarations, so it works on any Mac.
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "ui" / "src-tauri" / "tauri.conf.json"
FLOOR_SH = ROOT / "scripts" / "macos_floor.sh"

#: Mach-O and universal (fat) magic numbers, both byte orders.
MACHO_MAGIC = (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce",
               b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca")


class FloorUnreadable(Exception):
    """Something the gate needs could not be read. Always a failure, never a pass."""


def version_tuple(v: str) -> tuple[int, int, int]:
    """'14' -> (14, 0, 0); '14.4' -> (14, 4, 0). Anything else is unreadable, not zero."""
    m = re.fullmatch(r"\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?\s*", str(v))
    if not m:
        raise FloorUnreadable(f"not a macOS version: {v!r}")
    return tuple(int(x or 0) for x in m.groups())  # type: ignore[return-value]


def declared_floor(conf: Path = CONF) -> str:
    """The one declared floor: tauri.conf.json bundle.macOS.minimumSystemVersion, e.g. '14.0'."""
    try:
        v = json.loads(conf.read_text(encoding="utf-8"))["bundle"]["macOS"]["minimumSystemVersion"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise FloorUnreadable(f"no bundle.macOS.minimumSystemVersion in {conf}: {e}") from e
    version_tuple(v)
    return str(v)


def plist_floor(app: Path) -> str:
    """LSMinimumSystemVersion from the app's Info.plist."""
    plist = app / "Contents" / "Info.plist"
    try:
        v = plistlib.loads(plist.read_bytes()).get("LSMinimumSystemVersion")
    except (OSError, plistlib.InvalidFileException, ValueError) as e:
        raise FloorUnreadable(f"cannot read {plist}: {e}") from e
    if not v:
        raise FloorUnreadable(f"{plist} has no LSMinimumSystemVersion")
    return str(v)


def highest_minos_by_reader(app: Path) -> str:
    """The highest minos as scripts/macos_floor.sh --full reads it (the release page's reader)."""
    got = subprocess.run(["bash", str(FLOOR_SH), "--full", str(app)], capture_output=True, text=True, timeout=600)
    out = got.stdout.strip()
    if got.returncode != 0 or not out:
        raise FloorUnreadable(f"macos_floor.sh read no floor from {app}: {got.stderr.strip()[:300]}")
    version_tuple(out)
    return out


def _file_minos(path: Path) -> list[str]:
    """Every minos in this file (one per architecture slice)."""
    try:
        out = subprocess.run(["vtool", "-show-build", str(path)], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return re.findall(r"^\s*minos\s+([\d.]+)\s*$", out, re.M)


def macho_files(app: Path) -> list[Path]:
    """Every regular, non-symlink file in the bundle that starts with a Mach-O magic, whatever its mode."""
    found = []
    for dirpath, _dirs, files in os.walk(app):
        for name in files:
            p = Path(dirpath) / name
            if p.is_symlink() or not p.is_file():
                continue
            try:
                with open(p, "rb") as fh:
                    if fh.read(4) in MACHO_MAGIC:
                        found.append(p)
            except OSError:
                continue
    return sorted(found)


def sweep(app: Path) -> dict[str, str]:
    """{relative path: highest minos} for every Mach-O file that declares one."""
    got = {}
    for p in macho_files(app):
        vs = _file_minos(p)
        if vs:
            got[str(p.relative_to(app))] = max(vs, key=version_tuple)
    return got


def check(app: Path, conf: Path = CONF) -> list[str]:
    """Problems that must stop a release; an empty list means the build meets its declared floor.
    Raises FloorUnreadable when it cannot tell."""
    if not (app / "Contents").is_dir():
        raise FloorUnreadable(f"no app bundle at {app}")
    floor = declared_floor(conf)
    want = version_tuple(floor)
    problems = []

    declared = plist_floor(app)
    if version_tuple(declared) != want:
        problems.append(f"Info.plist LSMinimumSystemVersion is {declared}, but {conf.name} declares {floor}: "
                        f"the front door and the declared floor disagree (rebuild; tauri writes the plist from the conf)")

    highest = highest_minos_by_reader(app)
    swept = sweep(app)
    if not swept:
        raise FloorUnreadable(f"no Mach-O file in {app} declares a minos: this sweep saw nothing, so it proves nothing")
    too_new = sorted(((v, n) for n, v in swept.items() if version_tuple(v) > want),
                     key=lambda t: (version_tuple(t[0]), t[1]), reverse=True)
    if version_tuple(highest) > want or too_new:
        lines = "\n    ".join(f"needs {v}: {n}" for v, n in too_new[:15])
        more = f"\n    …and {len(too_new) - 15} more" if len(too_new) > 15 else ""
        problems.append(f"{len(too_new)} of {len(swept)} Mach-O files need a newer macOS than the declared {floor} "
                        f"(highest {highest} by macos_floor.sh):\n    {lines}{more}")
    if (version_tuple(highest) > want) != bool(too_new):
        problems.append(f"the two readers disagree: macos_floor.sh says {highest}, the magic sweep found "
                        f"{len(too_new)} file(s) above {floor}; one of them is blind to part of the bundle")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("app", type=Path)
    ap.add_argument("--conf", type=Path, default=CONF)
    a = ap.parse_args(argv)
    try:
        problems = check(a.app, a.conf)
    except FloorUnreadable as e:
        print(f"✗ macOS floor gate could not read the build: {e}", file=sys.stderr)
        return 2
    floor = declared_floor(a.conf)
    if problems:
        print(f"✗ macOS floor gate: {a.app} does not meet the declared floor macOS {floor}:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"✓ macOS floor gate: every Mach-O in {a.app.name} runs on macOS {floor}, and its Info.plist says {floor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
