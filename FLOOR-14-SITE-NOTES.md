# floor-14 (site): NOT for main until the macOS 14 build ships

Written 2026-10-20 at the CEO's ask: the download and requirements pages say plainly that on macOS 14 Crisp uses a
different upscaler (ncnn, not Core ML) and upscaling takes about 1.5 times as long as on macOS 15 or later.

Changed on this branch: download/ (requirement line, landing box, a "How fast it runs on your macOS" section, meta
description), pricing/ (landing-box requirement line, linked to download/#macos-speed), home (hero fine print, step-req
line, SoftwareApplication operatingSystem "macOS 14.0 or later").

Source for the numbers: ~/ops/research/crisp-macos-speed-table-draft-2026-10-20.md (M1 Ultra, 2026-10-19: Core ML 3.36 s
vs ncnn 4.97 s, 1.48x wall / 1.55x engine fps; earlier 1080p->4K figures 1.5x). Not timed on a Mac running macOS 14.
"Same picture" rests on the repo's Core ML vs ncnn pixel check (mean difference 0.05 to 0.26 of 255).

BEFORE MERGING (at ship time, after the runner proves the install on macos-14):
- About 95 other pages still say "macOS 26": sweep them (`grep -rl 'macOS 26' --include=index.html .`), plus
  ~/ops/facts.tsv crisp-min-macos and the llms.txt / JSON-LD copies; the comparison pages' "Crisp requires macOS 26" rows.
- Re-run page_dates.py, sitemap_dates.py, llms_txt.py, the pre-push gates and the crisp site-reading tests
  (test_the_os_we_promise_is_the_os_the_binaries_accept and the floor tests read these lines).
- If Core ML models are reconverted for macOS 14 (scripts/make_coreml_models.py --min-macos 14), the 1.5x line goes.
