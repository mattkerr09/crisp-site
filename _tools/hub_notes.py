#!/usr/bin/env python3
"""Give every /how-to/ hub entry a one-line note.

The how-to hub lists 46 guides whose titles all read "How to <x> on a Mac".
Scanning them tells the reader almost nothing, and it was the only hub without
notes -- /best/ and /for/ already use <span class="hub-note">, /vs/ carries the
differentiator in the link text, /learn/ is prose.

Each note is written from that guide's own meta description, minus the
boilerplate the hub already states once at the top ("nothing is uploaded,
nothing needs an account").

Idempotent: an <li> that already has a hub-note is left alone.
"""
import re
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent / "how-to" / "index.html"

NOTES = {
    # Rescue a bad recording
    "deinterlace-video-mac": "Comb-shaped stripes on moving edges, and why they have to go first.",
    "fix-blurry-video-mac": "Four different causes, and only some of them are fixable.",
    "remove-background-noise-video-mac": "Hiss and hum out of the audio. The picture is untouched.",
    "remove-noise-from-video-mac": "Grain and low-light speckle in the picture, denoised on-device.",
    "remove-wind-noise-from-video-mac": "A firm high-pass clears the rumble and keeps the voices.",
    "restore-old-film-footage-mac": "Single-frame dust, brightness flicker, and what cannot be recovered.",
    "restore-old-home-videos-mac": "Four separate problems, and the order you fix them in decides the result.",
    "stabilize-shaky-video-mac": "Tracks the motion and counter-shifts each frame. Audio kept.",
    "upscale-480p-to-1080p-mac": "A realistic 2.25x jump. 480p straight to 4K mostly is not.",
    # Change the format
    "batch-upscale-videos-mac": "Mostly about not discovering a mistake 200 files in.",
    "compress-video-on-mac": "Smaller for email or upload, at the same dimensions.",
    "convert-heic-to-jpg-mac": "Apple's photo format, and the quality question nobody mentions.",
    "convert-mkv-to-mp4-mac": "Usually a container swap that takes seconds and loses nothing.",
    "convert-mov-to-mp4-mac": "Lossless when the codec fits: the video is copied, not re-encoded.",
    "crop-video-mac": "Black bars and letterbox, detected for you. Audio stays in sync.",
    "edit-hdr-video-mac": "Why iPhone clips come out grey and washed-out almost everywhere else.",
    "make-video-vertical-mac": "9:16 for Reels and Shorts without cropping the subject out of frame.",
    "rotate-video-mac": "90 degrees either way, 180, or mirrored.",
    "upscale-a-finished-edit-to-4k-mac": "Cut it on the timeline, then upscale the whole export in one pass.",
    "upscale-video-on-mac": "The main guide: drop a clip, let it auto-enhance, export.",
    # Cut and arrange
    "change-video-speed-mac": "0.1x to 8x, with the audio pitch-corrected rather than chipmunked.",
    "loop-video-mac": "2 to 20 times back to back, picture and audio both.",
    "make-a-highlight-reel-mac": "The auto-editor finds the moments -- motion, sound, faces, speech.",
    "make-a-photo-slideshow-mac": "A Ken Burns move on each photo, music, and video clips mixed in.",
    "make-a-split-screen-video-mac": "Stacked for Reels, side by side for reactions.",
    "picture-in-picture-video-mac": "Easy to do, and easy to do badly. Where the inset belongs.",
    "reverse-video-mac": "Backwards, audio included, or a seamless boomerang.",
    "slow-mo-video-mac": "0.5x and 0.25x, with the audio pitch-corrected.",
    "split-a-clip-in-video-mac": "Press S at the playhead, then trim or re-time each half.",
    "trim-video-mac": "Frame-accurate: a range, the first ten seconds, or everything after a point.",
    # Give it a look
    "add-a-border-to-video-mac": "Seven colours, three thicknesses, the whole picture still visible.",
    "add-a-matte-look-to-video-mac": "The faded, muted, lifted-shadow film finish.",
    "add-a-vignette-to-video-mac": "Darkens the edges to pull the eye into the middle of the frame.",
    "add-captions-to-video-mac": "Burnt in, with exact show and hide timing.",
    "add-film-grain-to-video-mac": "The grainy, analog, shot-on-film look.",
    "add-title-cards-to-a-video-mac": "Images held on the timeline, with a Ken Burns move or a static hold.",
    "add-watermark-to-video-mac": "A logo in whichever corner you want, at the size you pick.",
    "color-grade-video-mac": "Cinematic, moody, warm, cool, mono. No LUTs and no curves.",
    "fade-video-mac": "In from black or out to it, picture and sound together.",
    # Fix the sound
    "extract-audio-from-video-mac": "The sound on its own, saved as an MP3.",
    "make-quiet-parts-louder-video-mac": "Levels the loud and the quiet so the dialogue is audible.",
    "mute-video-mac": "Drop the track, or scale it 0.1x to 4x. The video is copied byte for byte.",
    "normalize-audio-video-mac": "Evens out inconsistent volume without you guessing at a gain.",
    # Everything else
    "make-a-gif-on-mac": "Sharp colours, a small file, and boomerangs.",
    "remove-watermark-from-video-mac": "It is pixels, not a layer. What each of the three methods costs you.",
    "screenshot-from-video-mac": "A full-resolution still at the exact moment. PNG or JPG.",
}

LI = re.compile(
    r'<li><a href="https://crispvideo\.app/how-to/([^"/]+)/">(.*?)</a></li>'
)


def rewrite(html):
    """Return (new_html, added, unknown_slugs)."""
    added = []
    unknown = []

    def one(m):
        slug, title = m.group(1), m.group(2)
        note = NOTES.get(slug)
        if note is None:
            unknown.append(slug)
            return m.group(0)
        added.append(slug)
        return (
            f'<li><a href="https://crispvideo.app/how-to/{slug}/">{title}</a>'
            f' <span class="hub-note">{note}</span></li>'
        )

    return LI.sub(one, html), added, unknown


def main():
    check = "--check" in sys.argv
    html = HUB.read_text(encoding="utf-8")
    new, added, unknown = rewrite(html)

    if unknown:
        print(f"no note written for: {', '.join(sorted(set(unknown)))}")
        return 2
    if new == html:
        print(f"how-to hub: all {len(NOTES)} entries already have a note")
        return 0
    if check:
        print(f"how-to hub: {len(added)} entries are missing their note")
        return 1
    HUB.write_text(new, encoding="utf-8")
    print(f"how-to hub: added {len(added)} notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
