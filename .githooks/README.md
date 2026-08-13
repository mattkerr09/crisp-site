# Hooks

`.git/hooks/` is not tracked by git, so a re-clone loses them. Install with:

    git config core.hooksPath .githooks

## pre-push

Blocks a push where `index.html`'s JSON-LD `softwareVersion` disagrees with
`latest.json`'s `version`.

That drifted three times on 2026-08-12 — 0.1.810/0.1.813, 0.1.813/0.1.815,
0.1.815/0.1.816 — every time through a ship done by hand rather than through
`scripts/publish_release.sh`. Patching that script did not help, because the
path causing it never calls it. This is the boundary every path shares.
