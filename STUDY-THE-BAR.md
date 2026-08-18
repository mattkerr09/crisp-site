# The six reference sites, measured — and where crispvideo.app actually stands

Measured in a real browser at a **verified** `innerWidth: 1440` (checked inside the page each time;
the pane has opened at 400x225 and at 0 today). Mobbin returned **403 Forbidden** and I did not try
to work around it.

## The numbers

| site           | imgs | videos | canvas | CSS-animated | transitions | doc height |
|----------------|-----:|-------:|-------:|-------------:|------------:|-----------:|
| langchain.com  |   99 |      0 |      0 |            1 |           — |      7,335 |
| cofounder.co   |   51 |      1 |      1 |           14 |         362 |      9,107 |
| mistral.ai     |  127 |      0 |      1 |            4 |         683 |     11,760 |
| framer.com     |   86 |      5 |      0 |           16 |           1 |     10,877 |
| avo.bet        |  339 |      2 |     14 |           17 |          78 |     11,160 |
| **crispvideo** |  **3** |    3 |      0 |        **0** |      **38** | **14,700** |

**Crisp has three images. The bar is 51 to 339.** It is also the tallest page of the six while
carrying the least to look at — which is the measurable version of "lots of text, nothing to see".

## What each one actually does

**langchain.com** — a commissioned engraved illustration, full-bleed, headline set over it. No
video at all. Immediately below the fold: **17 customer logos** in two rows. Its credibility comes
from artwork and proof, not motion.

**cofounder.co** — the entire first screen is a **looping autoplay video** (`cofounder-2-hero.webm`,
1539x900) of a pixel-art scene, with product UI toasts animating over it. 362 elements carry
transitions.

**mistral.ai** — asymmetric editorial grid: a large brand-orange graphic panel on the left, a narrow
text column on the right. 683 elements with transitions, the most of the six. Dense navigation.

**framer.com** — the closest analogue to what Crisp should be. 54px/500 headline, two CTAs side by
side with the second an explicit **Download app**, a live proof stat inline and grey to the right of
the CTA row, and **the product's own interface as a 1200x673 looping video** below it with a soft
glow. Five videos on the page.

**avo.bet** — benefit-led 48px headline, **email capture inline in the hero**, four trust ticks, and
the product dashboard shown **rotated in 3D perspective**. Then "Supports 89+ Sportbooks" and a logo
wall. 339 images and 14 canvases.

## What they all do that we do not

1. **They show the product.** Framer shows its editor, AVO shows its dashboard, Cofounder shows its
   toasts firing. Crisp shows a before/after slider of *footage* — not the app. A visitor cannot
   see what using Crisp looks like.
2. **Something moves on arrival.** Cofounder's hero autoplays a full-bleed loop. Ours lazy-loads
   its hero pair on intersection and then plays them muted — which works, and which I briefly
   recorded here as "none of them autoplay". **That was my measurement error, not a site defect:**
   the Browser pane was not displayed, so `document.hidden` was true, IntersectionObserver never
   fired, and the videos sat at `readyState: 0`. With the pane visible they load and play. The
   real gap is not that ours fails to move — it is that what moves is a clip of *footage*, where
   Cofounder's is a designed scene and Framer's is the product itself.
3. **Social proof in the first screen.** LangChain: 17 logos. AVO: 89+ sportsbooks. Crisp: none.
4. **Density.** They put 51-339 images on a page. We put three on a page 14,700px tall.
5. **Art direction.** LangChain commissioned an engraving. Cofounder commissioned pixel art. Mistral
   built a colour system into large geometric blocks. Crisp has a dark background and text.

## The honest read

Everything measured and fixed on this site today — type scale, spacing rhythm, headline size,
emphasis colour, reveal-on-scroll — is a **static** property. Every one of those gates can be green
on a page that still has three images and nothing playing. Matthew's complaint is exactly right and
the metrics did not catch it because none of them was pointed at motion, demonstration or density.

## What would actually close the gap, in order of value

1. **A real video of Crisp running** — the app restoring footage, timeline visible, autoplaying and
   looping in the hero. Crisp is a video product and the site contains no footage of the product.
2. **Autoplay what is already there.** Three videos exist and none plays on load.
3. **The app's own interface as the hero image**, the way Framer does it, rather than a slider of
   footage that could have come from anywhere.
4. **Density**: real screenshots of the editor, the montage lane, the timeline.

This file is the study, not the fix. Nothing here is done until there are screenshots of ours beside
theirs at the same width.

## What the product actually looks like, and why that matters

I served the app's own UI (`ui/src`, the real shipped webview) and looked at it. The editor screen
carries: a Media panel with Import, a natural-language command bar — *"Tell Crisp what to do with
the selected clip — 'make it cinematic', 'mute it', '2x speed'"* with a **Do it** button — a
preview stage, transport controls with timecode, a Project panel (Transition, Look, Fade, Speed,
Music, and an **Auto-Montage** block with Style and Target-length controls), and a timeline with a
playhead and ruler. The tool palette lists **22 tools**: Enhance, Editor, Montage, Split Screen,
Reframe, Speed, Color, Trim, Rotate, Caption, Watermark, Reverse, Audio, Fade, Crop, GIF, Frame,
Loop, Stabilize, Compress, Border, Convert.

**None of it appears on crispvideo.app.** The site shows a before/after slider of footage that could
have come from anywhere. It never shows that Crisp is a real editor with a timeline — which is the
thing Framer and AVO both do with their own products, and the single biggest reason our page reads
as a description rather than a demonstration.

⚠️ The screenshot I can take today shows the empty state and a red "Backend offline" pill, because
the UI served over http cannot reach the sidecar — the Origin guard requires `tauri://localhost`,
which is correct and I am not weakening it. A populated screenshot has to come from the real app
with clips actually loaded. **I will not fabricate one by injecting state**: this site's own
truth-clause gate exists precisely to stop a page depicting something the product did not do.
