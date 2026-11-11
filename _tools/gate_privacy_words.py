#!/usr/bin/env python3
"""Reject blanket privacy claims in shipped files and generator sources.

    python3 _tools/gate_privacy_words.py
    python3 _tools/gate_privacy_words.py --selftest

Checks and tests under _tools are not generators. The only shipped-path
exemption is legal/privacy/, which explains the counts the app sends.
"""
from __future__ import annotations

import argparse
from html import unescape
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

SITE = Path(__file__).resolve().parent.parent
BANNED = re.compile(
    r'\bnothing\s+(?:(?:is|gets|was)\s+)?(?:uploaded|sent|transmitted)\b'
    r'|\bnothing\s+leaves\s+(?:your|the)\b'
    r'|\bsends?\s+nothing\b'
    r'|\bnichts\s+wird\s+(?:hochgeladen|gesendet)\b'
    r'|\bnada\s+(?:é\s+enviado|es\s+enviado|se\s+(?:envía|sube))\b'
    r'|\bno\s+se\s+sube\s+nada\b'
    r'|何も(?:アップロード|送信)されません'
    r'|何も(?:アップロード|送信)しません',
    re.I,
)
ESCAPED = re.compile(r'\\u([0-9a-fA-F]{4})|\\x([0-9a-fA-F]{2})')


def paths(site: Path) -> list[Path]:
    shipped = [p for p in site.rglob('*') if p.is_file() and p.suffix.lower() in {'.html', '.js', '.txt'}
               and not any(part.startswith(('.', '_')) or part == 'node_modules'
                           for part in p.relative_to(site).parts[:-1])
               and p.relative_to(site).parts[:2] != ('legal', 'privacy')]
    generators = [p for p in (site / '_tools').glob('*.py')
                  if not p.name.startswith(('gate_', 'test_'))]
    return sorted(shipped + generators)


def normal(source: str) -> str:
    # Read entities, escaped schema/JS strings and text split across tags or lines.
    source = ESCAPED.sub(lambda m: chr(int(m[1] or m[2], 16)), source)
    source = unescape(source)
    return ' '.join((source + '\n' + re.sub(r'<[^>]*>', ' ', source)).split())


def problems(site: Path) -> list[str]:
    bad = []
    for path in paths(site):
        matches = dict.fromkeys(m[0] for m in BANNED.finditer(normal(path.read_text(encoding='utf-8'))))
        bad.extend(f'{path.relative_to(site).as_posix()}: {claim}' for claim in matches)
    return bad


def check(site: Path) -> int:
    files = paths(site)
    if not files:
        print(f'FAIL: privacy words: no shipped files or generators under {site}')
        return 1
    bad = problems(site)
    if bad:
        for message in bad:
            print(f'  FAIL {message}')
        print(f'FAIL: privacy words: {len(bad)} blanket claims')
        return 1
    print(f'OK: privacy words: {len(files)} shipped files and generator sources checked')
    return 0


def selftest() -> int:
    phrases = (
        'Nothing is uploaded.', 'NOTHING GETS UPLOADED.', 'nothing leaves your Mac',
        'Nothing uploaded', 'Nothing was uploaded.', 'Nothing leaves the device.', 'nothing is sent anywhere',
        'nothing transmitted', 'sends nothing', 'Nichts wird hochgeladen.',
        'Nada é enviado.', 'No se sube nada.', 'Nada se envía.',
        '何もアップロードされません。', '何も送信されません。',
        'Nothing\nis\nuploaded.', 'Nothing <strong>is</strong> uploaded.',
        'Nothing&#32;is uploaded.', r'Nothing \u0069s uploaded.',
        '<meta name="description" content="Nothing is uploaded.">',
        '<button aria-label="Nothing is uploaded.">Pick a video</button>',
        r'{"text": "Nothing \u0069s uploaded."}',
    )
    targets = ('index.html', 'nested/player.js', 'llms.txt', '_tools/generator.py')
    script = str(Path(__file__).resolve())
    count = 0
    with tempfile.TemporaryDirectory(prefix='crisp-privacy-words-') as tmp:
        clean = Path(tmp) / 'clean'
        for name in targets:
            path = clean / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Your videos and photos never leave your computer.', encoding='utf-8')
        exempt = clean / 'legal/privacy/index.html'
        exempt.parent.mkdir(parents=True)
        exempt.write_text(phrases[0], encoding='utf-8')

        def run(site: Path) -> int:
            return subprocess.run([sys.executable, script, '--site', str(site)],
                                  capture_output=True, text=True).returncode

        planted = Path(tmp) / 'planted'
        shutil.copytree(clean, planted)
        for name in targets:
            for phrase in phrases:
                path = planted / name
                original = path.read_text(encoding='utf-8')
                path.write_text(phrase, encoding='utf-8')
                if run(planted) != 1:
                    print(f'FAIL: privacy words selftest accepted {phrase!r} in {name}')
                    return 1
                path.write_text(original, encoding='utf-8')
                count += 1
        # A similar path must not inherit the privacy policy's exemption.
        lookalike = planted / 'legal/privacy-extra/index.html'
        lookalike.parent.mkdir(parents=True)
        lookalike.write_text(phrases[0], encoding='utf-8')
        if run(planted) != 1:
            print('FAIL: privacy words selftest exempted legal/privacy-extra/')
            return 1
        if run(clean) != 0:
            print('FAIL: privacy words selftest rejected clean copy or policy exemption')
            return 1
        print(f'OK: privacy words selftest: {count} planted claims failed; '
              'policy lookalike failed; clean copy passed')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    parser.add_argument('--site', type=Path, default=SITE)
    args = parser.parse_args()
    return selftest() if args.selftest else check(args.site)


if __name__ == '__main__':
    raise SystemExit(main())
