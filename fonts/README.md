# Fonts

Self-hosted, woff2 only. Nothing on this site loads from a third-party host — the pre-push check
asserts it, and a font CDN would break that as surely as an analytics tag would.

| file | family | weights | licence |
|---|---|---|---|
| `dmsans-var.woff2` | DM Sans | variable 400–700 | SIL Open Font License 1.1 |
| `dmsans-var-italic.woff2` | DM Sans italic | variable 400–700 | SIL Open Font License 1.1 |
| `clashdisplay-500.woff2` | Clash Display | 500 | ITF Free Font Licence (Fontshare) |
| `clashdisplay-600.woff2` | Clash Display | 600 | ITF Free Font Licence (Fontshare) |

**Provenance, stated plainly.** All four files came from `outlier-site/fonts`, where they are
already serving on outlier.host — the same owner, the same company. DM Sans is published by
Google Fonts under the SIL OFL, which permits commercial use, embedding and redistribution, so
that half needs no further argument.

Clash Display is Fontshare's, under the ITF Free Font Licence. **I could not read Fontshare's
licence page to verify its terms myself — the page renders its text with JavaScript and returned
nothing but the site title.** It is used here on the strength of it already being accepted and
deployed for outlier.host by its owner, not on the strength of my having checked it. If that
acceptance was ever in doubt, the display face is the only thing that would need to change:
`--head` falls back to Futura and then the system stack, and the body face is unaffected.
