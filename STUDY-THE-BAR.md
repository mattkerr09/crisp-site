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

## The side-by-side, at last — and what it actually shows

All four rendered headless at an identical 1440x900 (`--window-size=1440,900`), so the comparison is
like-for-like rather than eyeballed.

**Ours is mostly empty.** That is the finding, and it is not "add more images":

1. **Our visual floats in dark space.** The hero clip is 998px centred in a 1440px viewport with
   dark margin either side, and nothing frames it. Framer's product surface **bleeds off the right
   edge**. Cofounder's scene is **full-bleed, edge to edge, no margin at all**. Theirs fill the
   frame; ours sits in the middle of it.
2. **We have no colour.** Near-black, grey text, one blue button. Cofounder runs a full-colour
   painted scene, AVO carries purple and green accents through the UI, Framer has a blue glow
   behind the product. Our page has one accent and barely uses it.
3. **Our visual does not show the product.** A pagoda clip demonstrates *footage*. Framer shows its
   editor mid-keystroke ("homepage for a|"), AVO shows its odds dashboard, Cofounder shows task
   toasts firing. A visitor learns what their product IS from the first screen. Ours does not.
4. **Density below the fold.** AVO is already into "Supports 89+ Sportbooks" and a logo wall at
   900px. We are still in whitespace.

`app-editor.jpg` in this directory is the real Crisp editor, rendered from the shipped webview at
1440x900 and cropped below the title bar. It is on disk and not yet on the page — that is the next
change, not a claim that it is done.

## CORRECTION — the site does show the product, and I said it did not

I wrote above that "the product is a real editor and the site never shows it" and that "none of it
appears on crispvideo.app". **Both are false.** `img-app.png` has been on the page all along, in the
"What it does" section: the full editor in a macOS window with traffic lights, a **Pro** badge and a
real build number, framed and captioned. It is a better screenshot than the one I rendered — mine
had no window chrome and I had to crop a "Backend offline" pill out of it. I deleted mine.

**How I got it wrong.** I measured `imgs: 3` and `productUIImages: 3` on the live page. The second
number was the answer, sitting in my own output, and I read the first as "almost nothing" and
concluded the product was absent without looking at what those three images were. Fourth
wrong-property measurement today, and the most consequential, because I reported it to Matthew and
committed it twice.

**The accurate gap is placement, not absence:**

    img-app.png sits at y=4,842 — 5.4 screens down a 14,641px page

Framer's editor is in the **first screen**. AVO's dashboard is in the **first screen**. Cofounder's
product toasts are in the **first screen**. Ours is past the fold five times over, which for most
visitors is the same as not having it. That is a fixable placement problem and a much smaller one
than what I claimed.

## Colour is NOT the gap — measured, and my own hypothesis was wrong

I had "almost no colour" on the open list for hours, on the strength of counting text colours
(116 white / 65 grey / 17 ice / 10 cyan). So I measured mean saturation and brightness on renders
of all four at an identical 1440x1800:

    site              saturation   brightness
    cofounder.co          63.7        108.8      painted full-colour scene
    mistral.ai            57.8         61.5      brand-orange geometric blocks
    crispvideo.app        10.4         38.8      us
    avo.bet                5.6         12.4      darker and LESS saturated than us

**avo.bet is half our saturation and a third our brightness, and Matthew named it as the bar.**
So the bar contains both highly-saturated sites and a near-monochrome one, which means colour is not
what separates us from it. Adding colour would have been effort spent on a property the reference
set does not agree on — and Crisp's restrained dark palette is defensible precisely because avo
proves a dark monochrome site can be at that level.

What avo has instead is 339 images, 14 canvases, its dashboard rendered at an angle, and a logo
wall inside the first two screens. **The gap is density and product presence, not colour.** That is
the one item that every site above us shares.

⚠️ THE FIRST MEASUREMENT WAS AN INSTRUMENT ARTIFACT AND I NEARLY PUBLISHED IT. Rendering avo.bet at
1440x9000 gave saturation 1.1, which would have made it the most monochrome site by far. The render
was nearly EMPTY — nav and background, no content — because its page does not populate at that
viewport height. A number that surprising is a hypothesis about the instrument first; I looked at
the image before believing it, and re-measured at a height where content is known to load.
