#!/usr/bin/env python3
"""Reject generic Crisp promises of reaching 4K, with reviewed exceptions."""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
TRANSLATIONS = {"de", "es", "ja", "pt-br"}
TO_4K = re.compile(r"\bto\s+4k\b", re.I)

# Each exception names the page, the kept phrase and the reason. Matching one
# phrase never exempts another claim elsewhere in the same line or paragraph.
ALLOWLIST = [
    ("index.html", "1080p phone clip to 4K", "HD-specific timed clip"),
    ("index.html", "They arrive as 720p to 4K", "explanation of sample source sizes"),
    ("best/ai-video-enhancer-mac/index.html", "Local deblur, noise cleanup and enlargement, with several AI models and output to 4K", "rival: HitPaw"),
    ("best/ai-video-enhancer-mac/index.html", "FabCloud to 4K", "rival: UniFab cloud output"),
    ("best/free-video-upscaler-mac/index.html", "Denoise, deblur and upscale to 4K", "rival: HitPaw table row"),
    ("best/free-video-upscaler-mac/index.html", "Upscale to 4K or 8K", "rival: Aiarty table row"),
    ("best/free-video-upscaler-mac/index.html", "HD sources to 4K", "HD-specific rival: Resolve"),
    ("best/free-video-upscaler-mac/index.html", "HD to 4K", "HD-specific rival: Media.io"),
    ("best/free-video-upscaler-mac/index.html", "The same frame upscaled to 4K", "explanation of measured 1080p frame disk cost"),
    ("best/free-video-upscaler-mac/index.html", "One minute of 1080p at 30 fps, upscaled to 4K", "HD-specific disk cost table"),
    ("best/way-to-restore-old-home-videos/index.html", "Going to 4K does not create the missing information", "explanation of missing detail"),
    ("for/index.html", "upscaling a 1080p capture to 4K", "HD-specific upload advice"),
    ("for/youtubers/index.html", "more bitrate to 4K uploads", "explanation of YouTube bitrate"),
    ("for/youtubers/index.html", "A 1080p video upscaled to 4K", "HD-specific upload advice"),
    ("for/youtubers/index.html", "1080p video going to 4K", "HD-specific render cost"),
    ("how-to/index.html", "1080p phone clip to 4K", "HD-specific timed clip"),
    ("how-to/index.html", "480p straight to 4K mostly is not", "explanation of a realistic target"),
    ("how-to/restore-old-home-videos-mac/index.html", "Going to 4K is mostly the model inventing", "explanation of missing detail"),
    ("how-to/upscale-a-finished-edit-to-4k-mac/index.html", "Enhance to 4K", "preset name"),
    ("how-to/upscale-a-finished-edit-to-4k-mac/index.html", "Upscale to 4K Yes Yes No", "comparison table row, kept by job rule"),
    ("how-to/upscale-a-photo-mac/index.html", "upscale it to 4k", "explanation of photo prompt and its measured size, not a video claim"),
    ("how-to/upscale-video-on-mac/index.html", "1080p to 4K", "HD-specific target"),
    ("how-to/upscale-video-on-mac/index.html", "1080p phone clip to 4K", "HD-specific timed clip"),
    ("learn/bitrate-vs-resolution/index.html", "Will upscaling a low-bitrate video to 4K fix it?", "explanation question answered no"),
    ("learn/is-topaz-video-ai-free/index.html", "1080p phone clip to 4K", "HD-specific timed clip"),
    ("learn/what-is-ai-video-upscaling/index.html", "Enhance to 4K", "preset name"),
    ("learn/when-ai-upscaling-beats-a-plain-resize/index.html", "a 480p source resized to 4K", "explanation of plain resizing"),
    ("learn/when-ai-upscaling-beats-a-plain-resize/index.html", "1080p to 4K", "HD-specific delivery size"),
    ("learn/why-4k-exports-take-so-long/index.html", "How long does upscaling to 4K take?", "explanation of render cost"),
    ("learn/why-4k-exports-take-so-long/index.html", "720p to 4K on Auto", "explanation of measured render cost"),
    ("learn/why-4k-exports-take-so-long/index.html", "1080p to 4K", "HD-specific pixel cost"),
    ("learn/why-topaz-ended-perpetual-licences/index.html", "Enhance to 4K", "preset name"),
    ("learn/why-video-looks-worse-after-uploading/index.html", "1080p timeline upscaled to 4K", "HD-specific upload advice"),
    ("llms.txt", "1080p to 4K", "HD-specific guide title and description"),
    ("vs/avclabs-video-enhancer-alternative-mac/index.html", "1080p clip to 4K", "HD-specific memory measurement"),
    ("vs/inshot-alternative-mac/index.html", "Edit → upscale finished cut to 4K", "comparison table row, kept by job rule"),
    ("vs/real-esrgan-alternative-mac/index.html", "1080p phone clip to 4K", "HD-specific timed clip"),
    ("vs/switch-from-topaz-video-ai-to-crisp/index.html", "1080p to 4K", "HD-specific everyday job"),
    ("vs/topaz-alternative-mac/index.html", "1080p phone clip to 4K", "HD-specific timed clip"),
    ("vs/topaz-alternative-mac/index.html", "1080p clip to 4K", "HD-specific memory measurement"),
    ("vs/video2x-alternative-mac/index.html", "1080p to 4K", "HD-specific linked guide title"),
]
for page in ("learn/index.html", "learn/what-is-rolling-shutter/index.html",
             "learn/what-is-telecine/index.html", "learn/what-is-variable-frame-rate/index.html",
             "learn/why-4k-exports-take-so-long/index.html"):
    ALLOWLIST.append((page, "Why upscaling to 4K takes so long", "explanation title"))
for page in ("how-to/upscale-video-on-mac/index.html",
             "learn/why-video-looks-worse-after-uploading/index.html",
             "vs/real-esrgan-alternative-mac/index.html"):
    ALLOWLIST.append((page, "the same frame after upscaling to 4K on the right",
                      "explanation of a specific before/after sample"))


class PageText(HTMLParser):
    """Include copy, metadata, alt text and JSON-LD, even across inline tags."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks = []

    def handle_data(self, data: str) -> None:
        self.chunks.append(data)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.chunks.extend(value for name, value in attrs
                           if value and name in {"content", "alt", "title", "aria-label"})


def normalize(text: str) -> str:
    return " ".join(html.unescape(text).split())


def violations(page: str, source: str) -> list[str]:
    if page.endswith(".html"):
        parser = PageText()
        parser.feed(source)
        source = " ".join(parser.chunks)
    text = normalize(source)
    allowed = []
    for path, phrase, reason in ALLOWLIST:
        assert reason
        if path == page:
            allowed.extend((m.start(), m.end()) for m in re.finditer(re.escape(phrase), text, re.I))
    return [text[max(0, m.start() - 65):m.end() + 65] for m in TO_4K.finditer(text)
            if not re.search(r"\bup\s*$", text[:m.start()], re.I)
            and not any(start <= m.start() and m.end() <= end for start, end in allowed)]


def main() -> int:
    # Regression probes: an exception must not mask a nearby generic promise.
    assert violations("index.html", "<b>Upscale</b>to 4K")
    assert violations("index.html", '<meta content="Crisp exports to 4K">')
    assert violations("index.html", "1080p phone clip to 4K; Crisp restores to 4K")
    assert violations("index.html", "<p>Crisp exports\nto&nbsp;4K.</p>")
    assert not violations("index.html", "<p>Upscale up to 4K</p>")
    assert not violations("index.html", "1080p phone clip to 4K")
    pages = [p for p in sorted(SITE.rglob("index.html"))
             if p.relative_to(SITE).parts[0] not in TRANSLATIONS
             and not any(part.startswith(".") for part in p.relative_to(SITE).parts)]
    pages.append(SITE / "llms.txt")
    failures = [(str(p.relative_to(SITE)), match) for p in pages
                for match in violations(str(p.relative_to(SITE)), p.read_text())]
    for page, match in failures:
        print(f"{page}: {match}")
    print(f"up to 4K: checked {len(pages)} English files; {len(failures)} unqualified claims")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
