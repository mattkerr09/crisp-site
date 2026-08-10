#!/usr/bin/env python3
"""Give each article's FAQ section a heading about ITS OWN subject.

48 of 80 articles carried an H2 that was literally "FAQ". One page doing that is normal; 48 doing
it is the corpus-level fingerprint that reads generated — the same tell the sibling site had with
100 articles sharing "Frequently asked questions".

⚠️ EVERY HEADING HERE IS HAND-WRITTEN, ON PURPOSE. The sibling site's version of this script tried
to DERIVE headings from slugs and titles and was thrown away four times for emitting things like
"What hIPAA-conscious healthcare on a Mac usually ask". A clean generic beats a mangled specific,
so there is no derivation step to go wrong: a page is either in this table with a heading a person
wrote, or it keeps "FAQ".

⚠️ Spelling-neutral by design. The corpus mixes British and American forms (a page can say "color
grade" in its H1 and "colours" in its body), so no heading here contains colour/color,
normalise/normalize, stabilise/stabilize or similar. That way a heading can never disagree with
the page it sits on.
"""
import re
import sys
from pathlib import Path

HEADINGS = {
    # ── vs/ : someone arriving from another tool ───────────────────────────────────────────
    "vs/adobe-premiere-alternative-mac":      "Switching from Premiere",
    "vs/capcut-alternative-mac":              "Switching from CapCut",
    "vs/clipchamp-alternative-mac":           "Switching from Clipchamp",
    "vs/davinci-resolve-alternative-mac":     "Switching from DaVinci Resolve",
    "vs/filmora-alternative-mac":             "Switching from Filmora",
    "vs/handbrake-alternative-mac":           "Coming from HandBrake",
    "vs/imovie-alternative-mac":              "Switching from iMovie",
    "vs/inshot-alternative-mac":              "Switching from InShot",
    "vs/kapwing-alternative-mac":             "Switching from Kapwing",
    "vs/topaz-alternative-mac":               "Switching from Topaz",
    "vs/topaz-video-ai-alternative-mac":      "Switching from Topaz Video AI",

    # ── how-to/ : the task the page teaches ────────────────────────────────────────────────
    "how-to/add-a-border-to-video-mac":       "Borders, in detail",
    "how-to/add-a-matte-look-to-video-mac":   "About the matte look",
    "how-to/add-a-vignette-to-video-mac":     "Vignette questions",
    "how-to/add-captions-to-video-mac":       "About captions",
    "how-to/add-film-grain-to-video-mac":     "Film grain, in detail",
    "how-to/add-title-cards-to-a-video-mac":  "Title card questions",
    "how-to/add-watermark-to-video-mac":      "Watermarks, in detail",
    "how-to/change-video-speed-mac":          "Speed changes, in detail",
    "how-to/color-grade-video-mac":           "Grading questions",
    "how-to/compress-video-on-mac":           "Compression, in detail",
    "how-to/convert-mov-to-mp4-mac":          "MOV and MP4 questions",
    "how-to/crop-video-mac":                  "Cropping questions",
    "how-to/edit-hdr-video-mac":              "HDR questions",
    "how-to/extract-audio-from-video-mac":    "Pulling out the audio, in detail",
    "how-to/fade-video-mac":                  "Fades, in detail",
    "how-to/loop-video-mac":                  "Looping questions",
    "how-to/make-a-gif-on-mac":               "GIF questions",
    "how-to/make-a-highlight-reel-mac":       "Highlight reels, in detail",
    "how-to/make-a-photo-slideshow-mac":      "Slideshow questions",
    "how-to/make-quiet-parts-louder-video-mac": "About evening out the levels",
    "how-to/make-video-vertical-mac":         "Going vertical, in detail",
    "how-to/mute-video-mac":                  "Muting questions",
    "how-to/normalize-audio-video-mac":       "About matching loudness",
    "how-to/remove-background-noise-video-mac": "Background noise questions",
    "how-to/remove-noise-from-video-mac":     "About noise in video",
    "how-to/remove-wind-noise-from-video-mac": "Wind noise questions",
    "how-to/restore-old-film-footage-mac":    "Restoring old film, in detail",
    "how-to/reverse-video-mac":               "Playing it backwards, in detail",
    "how-to/rotate-video-mac":                "Rotation questions",
    "how-to/screenshot-from-video-mac":       "Still frames, in detail",
    "how-to/slow-mo-video-mac":               "Slow motion questions",
    "how-to/split-a-clip-in-video-mac":       "Splitting clips, in detail",
    "how-to/stabilize-shaky-video-mac":       "Shaky footage, in detail",
    "how-to/trim-video-mac":                  "Trimming questions",
    "how-to/upscale-a-finished-edit-to-4k-mac": "Upscaling a finished edit",
    "how-to/upscale-video-on-mac":            "Upscaling questions",

    # ── best/ ──────────────────────────────────────────────────────────────────────────────
    "best/free-video-upscaler-mac":           "Free and paid, in detail",
}

FAQ_H2 = re.compile(r"(<h2\b[^>]*>)\s*FAQ\s*(</h2>)", re.I)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    apply = "--apply" in sys.argv
    changed = kept = 0
    for p in sorted(root.glob("**/index.html")):
        slug = str(p.parent.relative_to(root)).replace("\\", "/")
        html = p.read_text(encoding="utf-8")
        if not FAQ_H2.search(html):
            continue
        new_head = HEADINGS.get(slug)
        if not new_head:
            kept += 1
            print(f"  KEPT  {slug}  (no hand-written heading — generic beats mangled)")
            continue
        out = FAQ_H2.sub(lambda m: f"{m.group(1)}{new_head}{m.group(2)}", html, count=1)
        if out != html:
            if apply:
                p.write_text(out, encoding="utf-8")
            changed += 1
            print(f"  {'SET ' if apply else 'WOULD'}  {slug}  ->  {new_head!r}")
    print(f"\nrewritten: {changed}   left generic: {kept}")
    print("REPORT ONLY — pass --apply to write" if not apply else "APPLIED")


if __name__ == "__main__":
    main()
