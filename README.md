# Crisp: restore and upscale old video on your own computer

Crisp cleans up old home videos, VHS transfers and early phone clips, and upscales them up to 4K. It runs on your Mac or PC,
offline. Your videos never leave your computer, and there's no account. You can trim, add captions and export on a real
timeline when it's done.

**Download:** [crispvideo.app/download](https://crispvideo.app/download/?utm_source=github)

- **Mac:** Apple Silicon (M1 or later), macOS 14 or later. Signed and notarized by Apple.
- **Windows:** 64-bit Windows 10 or 11, with graphics that support Vulkan. On Windows, Crisp upscales video; photo
  upscaling is Mac only.

The installers are also on this repo's [releases page](https://github.com/mattkerr09/crisp-site/releases/tag/v1). That tag
always holds the current build, and it's where the in-app updater downloads from.

## Free, or pay once

The free version needs no account. Free video exports carry a small "crispvideo.app" mark, and upscale, restore and colour
stop at 15 seconds. Everything else runs at full length. Crisp Pro removes both and adds batch processing. It's a one-time
purchase, not a subscription. Current price: [crispvideo.app/pricing](https://crispvideo.app/pricing/?utm_source=github).

## Help

Email [support@crispvideo.app](mailto:support@crispvideo.app). Privacy policy:
[crispvideo.app/legal/privacy](https://crispvideo.app/legal/privacy/).

Made by Matthew Kerr (Kerr & Company LLC) in Grand Rapids, Michigan.

---

### For maintainers

This repo is the static site served at https://crispvideo.app. Edit the pages and push to `main`; GitHub Pages deploys it.
The pre-push hook in `.githooks/` runs the site's gates.

Serve locally:

```bash
python3 -m http.server 5601
```
