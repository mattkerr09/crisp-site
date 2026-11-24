# Fonts

Self-hosted, woff2 only. Nothing on this site loads from a third-party host — the pre-push check
asserts it, and a font CDN would break that as surely as an analytics tag would.

| file | family | weights | licence |
|---|---|---|---|
| `dmsans-latin.woff2` | DM Sans, basic Latin (U+0000-00FF …) | variable 400–700 | SIL Open Font License 1.1 |
| `dmsans-latin-italic.woff2` | DM Sans italic, basic Latin | variable | SIL Open Font License 1.1 |
| `dmsans-var.woff2` | DM Sans, latin-EXT only (U+0100-02BA …) | variable 400–700 | SIL Open Font License 1.1 |
| `dmsans-var-italic.woff2` | DM Sans italic, latin-EXT only | variable | SIL Open Font License 1.1 |
| `bricolage-500.woff2` | Bricolage Grotesque (wdth 100, opsz 48), basic Latin | 500 (serves 500) | SIL Open Font License 1.1 (`OFL-BricolageGrotesque.txt`) |
| `bricolage-700.woff2` | Bricolage Grotesque (wdth 100, opsz 48), basic Latin | 700 (serves 600-700) | SIL Open Font License 1.1 (`OFL-BricolageGrotesque.txt`) |

**Provenance, stated plainly.** All four files came from `outlier-site/fonts`, where they are
already serving on outlier.host — the same owner, the same company. DM Sans is published by
Google Fonts under the SIL OFL, which permits commercial use, embedding and redistribution, so
that half needs no further argument.

## The heading face: Bricolage Grotesque, since 2026-11-24 (CEO fix 131)

Until 2026-11-24 the headings were Clash Display (Indian Type Foundry, Fontshare "Closed Source"). Its licence, the ITF Free
Font License v2.0, allows self-hosting on our own site but forbids making the files available through a public repository
(section 02), and this repo is public because it hosts the installers. So the two Clash files were removed (`git rm`, no
history rewrite) and the headings moved to an OFL face.

How it was chosen (2026-11-24, Crisp chat): five OFL candidates (Space Grotesk, Familjen Grotesk, Red Hat Display, Bricolage
Grotesque at width 100 and at 87.5) were rendered on /, /pricing/ and /windows/ at 1280 and 375 wide against Clash Display, with
heading line counts and the font's own metrics measured. Bricolage Grotesque at width 100, optical size 48 was closest: the
same line breaks at 1280 (two headings get one line SHORTER at 375, none longer), cap height 0.66 against Clash's 0.67, and
ink density matched by weight: Clash 500 measures 0.259 ink per glyph area and Bricolage 500 0.266; Clash 600 measures 0.335
and Bricolage 700 0.326 (Bricolage 600 only 0.297). That is why the 600-700 face is Bricolage's weight 700. Space Grotesk
was closest in advance width but stayed visibly lighter even at its heaviest (700: 0.279).

The files are static instances of the variable font from github.com/google/fonts (ofl/bricolagegrotesque), pinned with
fontTools' instancer (wght, wdth 100, opsz 48) and subset to the same basic-Latin range as `dmsans-latin.woff2`; the OFL
allows both. The licence travels with them as `OFL-BricolageGrotesque.txt`. German, Spanish and Portuguese letters are
inside that range; Japanese headings fall back to the system stack as before.

## What it costs

Measured on the live site, three runs each, by loading the same page twice in one headless Chrome
— once normally, once with `/fonts/*` blocked at the network layer. Blocking is the only honest
control: comparing against yesterday's deploy would compare two different pages under two
different network conditions.

| | first contentful paint | cumulative layout shift | bytes |
|---|---|---|---|
| fonts served | 220–300 ms | **0.0000** | 78,240 |
| fonts blocked | 176–188 ms | 0.0000 | 0 |

So roughly **45–110 ms of FCP**, against a total FCP that is already well inside "good", and — the
number that actually matters for a font swap — **no layout shift at all**. `font-display: swap`
paints text in the fallback immediately and the metrics are close enough that nothing moves when
the real face arrives.

Re-run it if the file list changes:

```
python3 /tmp/fontcost2.py     # or rebuild from the recipe above
```

## ⚠️ Correction, 2026-09-24 — the numbers above measured a font that was barely used

Until 2026-09-24 only the two `dmsans-var*` files shipped, and they are Google's **latin-ext**
subset: 149 glyphs, no a–z (outlier-site serves the same bytes as `a18ee4a68c.woff2` beside the
latin file `fc88c23021.woff2`, and the copy took the wrong one). So every line of body text rendered
in the system fallback except capital **A**, NBSP and accented letters — two typefaces inside one
word — and the "no layout shift at all" row above is true only because almost nothing swapped.
The latin files are now `dmsans-latin*.woff2`, split from the ext files by `unicode-range` in both
`@font-face` blocks (index.html and style.css), and the homepage preloads the latin one. Re-measure
FCP/CLS before quoting the table again.
