# -*- coding: utf-8 -*-
"""Article bodies for the learn/ expansion. Prose lives here; scaffolding lives in new_pages.py.

Written to the house style the corpus was just corrected to: em-dashes stay rare, contractions
are normal, sentence lengths vary, and the five pages deliberately use FIVE DIFFERENT shapes.
Twelve distinct skeletons across 170 articles was the sibling site's real tell, so adding five
identical ones here would recreate it at a smaller scale.
"""

PAGES = [
{
 "slug": "learn/why-video-looks-worse-after-uploading",
 "crumb": "Why uploads look worse",
 "title": "Why your video looks worse after uploading it (2026) — Crisp",
 "h1": "Why your video looks worse after you upload it",
 "desc": "You exported a clean file and the version on Instagram looks mushy. Here is what every platform does to your footage on the way in, and the two things that actually help.",
 "faq_heading": "Uploads and compression, in detail",
 "body": """
  <p>You export a clip, watch it back, and it looks exactly right. Then you upload it, open the post
  on your phone, and the same shot has gone soft. Faces look waxy. Gradients in the sky have turned
  into bands. Fast movement smears. Nothing went wrong with your export. The platform re-encoded it.</p>

  <h2>Every upload is a re-encode</h2>
  <p>No large platform serves you the file you gave it. YouTube, Instagram, TikTok and the rest all
  transcode on ingest, because they have to deliver the same video to a laptop on fibre and a phone
  on a weak signal. That means several renditions at several bitrates, generated automatically, with
  no human looking at the result.</p>
  <p>Your file has already been compressed once when you exported it. The platform now compresses
  that compressed version again. Every codec throws away information it predicts you won't miss, and
  the second pass makes those predictions using footage that has already had detail removed. Errors
  from the first pass get treated as real image content and preserved, while genuinely fine detail
  competes for the same shrinking budget.</p>

  <h2>Why some clips survive and others fall apart</h2>
  <p>Compression works by describing what changed between frames. A locked-off interview is cheap,
  because almost nothing moves. Confetti, rain, foliage in wind, water, smoke, film grain and fast
  pans are expensive, because nearly every pixel changes every frame and none of it is predictable.</p>
  <p>Give an encoder a fixed bitrate and a difficult scene and it has one option: throw away more.
  That's why the worst artefacts always show up in exactly the shots you were proudest of. It's also
  why grain is such a problem. Real film grain is random by definition, so it's the least compressible
  thing you can hand an encoder, and it eats the budget that the faces in the shot needed.</p>

  <h2>The two things that genuinely help</h2>
  <p>The first is to give the platform a better master. Upload at a higher resolution than you need,
  because most platforms allocate a bigger bitrate to larger renditions. A 1080p timeline upscaled to
  4K before upload often survives compression better than the same edit uploaded at 1080p, not because
  4K has more real detail, but because the encoder is handed a more generous budget and a cleaner
  signal to work from.</p>
  <p>The second is to clean the source before you send it. Noise and compression artefacts in your
  master are, from the encoder's point of view, detail worth keeping. Remove them first and the
  bitrate goes to the parts of the frame a viewer actually looks at. Denoise, then upscale, then
  export. Doing it in that order matters, because an upscaler will happily magnify noise into
  something much harder to remove later.</p>
  <p>What doesn't help is exporting at a huge bitrate and hoping. The platform is going to re-encode
  to its own ladder regardless, so a 200 Mbps upload and a 40 Mbps upload usually converge on the
  same delivered file. Past a sensible threshold you're only making the upload slower.</p>

  <h2>Doing it on a Mac without a subscription</h2>
  <p>Crisp runs the whole chain on your machine. Drop the clip in, ask it to clean up the noise and
  upscale to 4K, and it does both locally with nothing uploaded anywhere. That last part matters more
  than it sounds for anyone working on client footage, since the usual alternative is handing an
  unreleased edit to a web service.</p>
""",
 "faq": [
  ("Does uploading at 4K really help a 1080p edit?",
   "Often, yes, and not for the reason people assume. You aren't inventing real detail by upscaling. You're qualifying for a larger bitrate allocation on the platform's encoding ladder, and handing that encoder a cleaner, larger source. The delivered 1080p rendition frequently looks better as a result."),
  ("Why does my footage look fine on my laptop and bad on my phone?",
   "You're being served a different rendition. Platforms pick a lower-bitrate version for smaller screens and weaker connections. The file you checked on your laptop may not be the file your audience sees."),
  ("Should I add grain before or after upscaling?",
   "After, and sparingly. Grain is close to incompressible, so adding it before a platform re-encode spends bitrate that the rest of the frame needed. Adding it last, at a modest strength, gives you the look without feeding the encoder noise to chew through."),
  ("Does re-uploading a downloaded video make it worse again?",
   "Yes. Every trip through an encoder is lossy, and downloading a compressed copy to re-upload it stacks another generation of loss on top. Always go back to your original export."),
 ],
},
{
 "slug": "learn/what-is-interlacing",
 "crumb": "Interlacing",
 "title": "What is interlacing, and why does old video have comb teeth? — Crisp",
 "h1": "What is interlacing?",
 "desc": "Those horizontal comb teeth on moving objects in old footage are interlacing. Here is where it came from, how to recognise it, and why deinterlacing has to happen before anything else.",
 "faq_heading": "Interlacing, in detail",
 "body": """
  <p>If moving objects in a clip have fine horizontal stripes along their edges while everything
  standing still looks perfectly normal, you're looking at interlacing. It isn't damage, and it isn't
  a bad transfer. It's the footage working exactly as designed, on a kind of display that no longer
  exists.</p>

  <h2>A bandwidth trick from the 1930s</h2>
  <p>Broadcast television couldn't carry enough bandwidth to send complete frames at a smooth rate.
  The workaround was to send half a picture at a time: all the odd-numbered lines, then all the
  even-numbered lines, each one a fraction of a second apart. Each half is called a field. A cathode
  ray tube drew them in sequence fast enough that your eye combined them, and you got the motion
  smoothness of fifty or sixty pictures per second for the bandwidth of twenty-five or thirty.</p>
  <p>It was a genuinely clever piece of engineering, and it survived into DV camcorders, DVDs and
  early digital broadcast. Which is why so much family footage from roughly 1980 to 2010 is
  interlaced.</p>

  <h2>Why it looks wrong now</h2>
  <p>Modern displays don't work that way. They show whole frames. So the two fields, captured at
  genuinely different moments, get displayed at the same instant. Anything that moved in the gap
  between them appears twice, offset, one stripe apart. That's the comb.</p>
  <p>Stationary parts of the frame look fine because nothing moved between the two fields, which is
  why the effect appears to cling to moving objects specifically.</p>

  <h2>Why it has to be fixed first</h2>
  <p>This is the part people get wrong, and it's expensive. An AI upscaler has no concept of fields.
  Hand it a combed frame and it sees a regular, high-contrast horizontal pattern, exactly the sort of
  fine structure it was trained to preserve and sharpen. So it preserves and sharpens the comb. You
  end up with crisp, high-resolution interlacing artefacts, which are far harder to remove than the
  originals and often impossible to fully undo.</p>
  <p>The order that works is deinterlace, then denoise, then upscale, then colour. Every step makes
  the following ones harder if you take it out of turn, and interlacing is the least forgiving of the
  lot.</p>

  <h2>Telling interlacing apart from things that look similar</h2>
  <p>Comb teeth only appear on movement, and they're perfectly horizontal and evenly spaced. Rolling
  shutter skew leans vertical edges over but doesn't stripe them. Compression blocking shows up as
  square patches, usually in dark or busy areas, and it doesn't care whether anything moved. Ghosting
  from a bad tape transfer smears rather than combs.</p>
  <p>If you're unsure, step through a few frames one at a time on a shot with fast motion. Interlacing
  is unmistakable frame by frame, and almost invisible at normal speed on some displays, which is how
  it survives into finished edits without anyone noticing.</p>

  <h2>Doing it on a Mac</h2>
  <p>Crisp detects interlaced sources and handles the deinterlace pass on-device, before any
  enhancement runs, so the ordering problem above is taken care of without you having to think about
  it. Nothing is uploaded, which tends to matter for exactly the sort of irreplaceable family footage
  that's most likely to be interlaced in the first place.</p>
""",
 "faq": [
  ("Can I just upscale interlaced footage and fix it afterwards?",
   "No, and this is the single most expensive mistake with old video. The upscaler treats comb teeth as real detail and sharpens them. Deinterlacing afterwards then has to work against artefacts that have been reinforced and enlarged. Deinterlace first, always."),
  ("Does deinterlacing lose quality?",
   "It costs something, unavoidably, because you're reconstructing whole frames from half-pictures. A good deinterlacer blends or interpolates intelligently rather than simply discarding one field. Throwing away every other line is the fast method and it halves your vertical resolution."),
  ("How do I know whether my footage is interlaced?",
   "Find a shot with fast horizontal movement and step through it a frame at a time. If moving edges break into fine horizontal stripes while static areas stay clean, it's interlaced. Footage from DV camcorders, DVDs and pre-2010 broadcast very often is."),
  ("Is 1080i actually 1080p?",
   "Not in terms of motion. 1080i carries the same line count but delivers it as two half-height fields per frame, so a moving subject never has a full 1920x1080 sample at a single instant. Deinterlaced 1080i and true 1080p are not equivalent."),
 ],
},
{
 "slug": "learn/what-is-frame-interpolation",
 "crumb": "Frame interpolation",
 "title": "What is frame interpolation? Smooth motion explained (2026) — Crisp",
 "h1": "What is frame interpolation?",
 "desc": "Frame interpolation invents new frames between the ones you shot, taking 30fps to 60 or beyond. How it works, where it fails badly, and when smoother motion is the wrong choice.",
 "faq_heading": "Smoother motion, in detail",
 "body": """
  <p>Frame interpolation creates frames that were never captured. Given two consecutive frames, the
  model works out how things moved between them and generates one or more intermediate pictures. Do
  that once between every pair and 30fps footage becomes 60fps. Do it more aggressively and you can
  push further, or turn ordinary footage into slow motion that was never shot as slow motion.</p>

  <h2>It's motion estimation, not guesswork</h2>
  <p>The useful mental model is that the software is tracking, not painting. It builds a map of how
  each region of the picture moved from one frame to the next, then warps both frames towards a point
  in between and blends them. Modern approaches estimate that motion field with a neural network,
  which is what makes them dramatically better than the frame blending that older editors offered.</p>
  <p>Frame blending simply cross-fades two frames. It produces a soft double image on anything that
  moves. Real interpolation moves the pixels, so a hand crossing the frame stays a hand rather than
  becoming two transparent hands.</p>

  <h2>Where it goes wrong</h2>
  <p>Interpolation fails in specific, predictable places, and knowing them saves a lot of wasted
  rendering.</p>
  <p>It struggles when something appears or disappears between frames, because there's nothing to
  track towards. Edges of the frame suffer for the same reason. It struggles with fast motion where
  an object travels a long way between samples, since the search has to guess which part of frame two
  corresponds to which part of frame one. Repeating patterns like railings, brickwork and venetian
  blinds confuse the matching badly. Motion blur is another one: a heavily blurred subject has no
  crisp features to track, so the estimate wanders.</p>
  <p>The failure looks like warping, tearing at edges, or a brief rubbery wobble as something passes
  in front of something else. It's usually confined to a handful of frames, which is precisely why it
  slips past a quick scrub through the timeline.</p>

  <h2>When smoother is worse</h2>
  <p>There's a reason cinema still shoots at 24fps. That frame rate carries strong associations, and
  interpolating a film-look sequence to 60fps produces the effect people describe as looking like a
  soap opera, or like behind-the-scenes video rather than the film itself. It isn't a technical fault.
  The motion is genuinely smoother. It just reads as cheaper.</p>
  <p>So the honest rule is that interpolation belongs on footage where smoothness is a virtue.
  Gameplay capture, sports, action cameras, drone shots, screen recordings and anything you intend to
  slow down all benefit. Narrative and cinematic work usually shouldn't be touched.</p>

  <h2>Doing it on a Mac</h2>
  <p>Crisp runs interpolation on-device. You can either pick a multiplier from the Smooth motion
  control or type what you want, and it keeps the audio in sync rather than leaving you to fix drift
  afterwards. Because it runs locally there's no per-minute billing, which matters here more than
  usual: interpolation is one of the most compute-heavy things you can ask of a clip, and it's exactly
  the operation cloud services price aggressively.</p>
""",
 "faq": [
  ("Does interpolation add real detail?",
   "No. It adds frames, not resolution. Every intermediate frame is built from the two real frames on either side of it, so the level of detail is unchanged. If you want more detail you want upscaling, which is a separate operation and can be run alongside it."),
  ("What multiplier should I use?",
   "Doubling is the safe default and covers the common case of 30fps to 60fps. Larger multipliers give the motion estimator less to work with per generated frame, so artefacts become more likely. If you're interpolating for slow motion, shoot at the highest frame rate your camera allows first."),
  ("Will it fix a video that stutters?",
   "It depends on the cause. If the source has a genuinely low frame rate, interpolation helps. If it stutters because of a frame rate mismatch with the display, or because the file is variable frame rate and something resampled it badly, interpolation will smooth over the symptom without addressing the cause."),
  ("Can I interpolate and upscale in the same pass?",
   "In Crisp, yes for the standard lanes, and the two are handled as separate stages internally so neither compromises the other. The generative Max restore lane is the exception and doesn't combine with interpolation."),
 ],
},
{
 "slug": "learn/bitrate-vs-resolution",
 "crumb": "Bitrate vs resolution",
 "title": "Bitrate vs resolution: why 4K can look worse than 1080p — Crisp",
 "h1": "Bitrate vs resolution",
 "desc": "Resolution is how many pixels you have. Bitrate is how much information describes them. Get the second one wrong and a 4K file will look worse than a good 1080p one.",
 "faq_heading": "Bitrate questions",
 "body": """
  <p>Two numbers decide how a video looks, and most people only pay attention to one of them.
  Resolution is the pixel count: 1920x1080, 3840x2160. Bitrate is how many bits per second the file
  spends describing those pixels. Resolution sets the size of the canvas. Bitrate decides how much
  paint you get.</p>
  <p>Starve a 4K file of bitrate and it will look worse than a well-fed 1080p one, on the same screen,
  every time. This is not a marginal effect. It's the single most common reason a video that should
  look good doesn't.</p>

  <h2>Why more pixels need more bits</h2>
  <p>A 4K frame has four times as many pixels as a 1080p frame. Hold the bitrate constant and each
  pixel gets a quarter of the description it had. The encoder responds the only way it can, by
  grouping pixels together and describing them as blocks rather than individually.</p>
  <p>That's what compression artefacts are. Blocking in dark areas, banding across skies and gradients,
  smeared texture on skin and hair, and detail that dissolves whenever the camera moves. The frame is
  still technically 3840 pixels wide. It just doesn't contain 3840 pixels worth of information.</p>

  <h2>What the numbers actually look like</h2>
  <table>
    <tr><th>Situation</th><th>Rough working range</th><th>What you notice if you go under</th></tr>
    <tr><td>1080p, talking head, locked off</td><td>8-12 Mbps</td><td>Very little. This is an easy scene.</td></tr>
    <tr><td>1080p, handheld, moving background</td><td>15-25 Mbps</td><td>Texture smears during movement.</td></tr>
    <tr><td>4K, general delivery</td><td>35-50 Mbps</td><td>Banding in skies, mushy foliage.</td></tr>
    <tr><td>4K, high motion or grain</td><td>60-100 Mbps</td><td>Blocking that pulses with the motion.</td></tr>
    <tr><td>Archival master</td><td>Higher, or an intermediate codec</td><td>Generational loss on every future edit.</td></tr>
  </table>
  <p>Treat those as starting points rather than rules. The honest answer is that the right bitrate
  depends on the content, and the way to find it is to encode a difficult thirty seconds and look at
  it, not to trust a table.</p>

  <h2>A rule of thumb that holds up</h2>
  <p>If you have to choose between resolution and bitrate, choose bitrate. A clean 1080p file beats a
  starved 4K one on any display, because a good scaler upsizing clean pixels produces a better picture
  than a decoder reconstructing damaged ones.</p>
  <p>The exception is upload, where platforms tie their bitrate allocation to the resolution you give
  them. There, going up in resolution can buy you a bigger budget than you would otherwise qualify for,
  which is a quirk of how the platforms work rather than anything about the format.</p>

  <h2>What to do with a file that's already starved</h2>
  <p>You can't recover information the encoder discarded. What you can do is stop making it worse and
  clean up what's visible. Compression artefacts respond reasonably well to targeted denoising, and an
  AI upscaler that has been trained on compressed footage will reconstruct plausible texture where
  blocking removed it. Crisp does both on-device, and it's worth doing before any re-encode rather than
  after, since a second compression pass will otherwise preserve the artefacts as if they were detail.</p>
""",
 "faq": [
  ("Is a bigger file always better?",
   "Up to a point, and then it stops mattering. Past the bitrate a scene actually needs, extra bits describe information the encoder has already captured perfectly well, and you're only making the file harder to store and slower to upload. The point of diminishing returns depends entirely on how difficult the footage is."),
  ("Should I export at a higher resolution than I shot?",
   "For upload, often yes, because platforms allocate bitrate by resolution. For archival or local playback, no. You aren't adding real information, and you're making every future operation on the file slower."),
  ("What is variable bitrate, and should I use it?",
   "Variable bitrate lets the encoder spend more on difficult scenes and less on easy ones, which is almost always what you want for delivery. Constant bitrate is mainly useful when something downstream needs a predictable data rate."),
  ("Why does my footage look worse after editing even though I didn't change anything?",
   "Because exporting re-encodes it. Unless you're stream-copying, the export is a fresh compression pass, and any clip that passes through it loses a little. Keeping an intermediate or high-bitrate master limits how much that accumulates over successive edits."),
 ],
},
{
 "slug": "learn/what-is-a-video-codec",
 "crumb": "Video codecs",
 "title": "What is a video codec? H.264, HEVC, ProRes and AV1 explained — Crisp",
 "h1": "What is a video codec?",
 "desc": "A codec decides how your video is compressed, a container decides how it is packaged, and confusing the two is why files refuse to open. A plain guide to the ones you will actually meet.",
 "faq_heading": "Codecs and containers, in detail",
 "body": """
  <p>A codec is the method used to compress and decompress video. A container is the file wrapper that
  holds the compressed video, the audio, and the metadata. They're different things, and almost every
  confusing playback problem comes from treating them as the same thing.</p>
  <p>The giveaway is that .mp4 and .mov are containers, not codecs. Either one can hold H.264, HEVC,
  ProRes and several others. So "my MP4 won't play" is rarely about MP4. It's about what's inside it.</p>

  <h2>The ones you'll actually encounter</h2>
  <table>
    <tr><th>Codec</th><th>What it's for</th><th>The catch</th></tr>
    <tr><td>H.264 (AVC)</td><td>The universal default. Plays on essentially everything.</td><td>Least efficient of the modern options, so files are larger for the same quality.</td></tr>
    <tr><td>HEVC (H.265)</td><td>Roughly half the size of H.264 at similar quality. Standard for 4K and for iPhone recording.</td><td>Patchier support on older hardware and some web platforms.</td></tr>
    <tr><td>ProRes</td><td>An editing and mastering codec. Very light to decode, near-lossless.</td><td>Enormous files. It lives in .mov, not .mp4.</td></tr>
    <tr><td>AV1</td><td>Royalty-free, very efficient, increasingly used for streaming delivery.</td><td>Encoding is slow, and hardware support is still arriving.</td></tr>
    <tr><td>VP9</td><td>Mostly a web delivery codec, common in .webm.</td><td>Can't be stream-copied into an .mp4, so conversion means a full re-encode.</td></tr>
  </table>

  <h2>Delivery codecs and editing codecs are not the same job</h2>
  <p>H.264, HEVC, AV1 and VP9 are delivery codecs. They're built to make files small, and they achieve
  that partly by describing frames in terms of other frames. That's efficient to store and awkward to
  edit, because reaching an arbitrary point means reconstructing the frames leading up to it.</p>
  <p>ProRes and similar intermediate codecs go the other way. Every frame is stored independently, so
  scrubbing is instant and repeated re-encoding costs you very little. You pay in disk space, sometimes
  by an order of magnitude. Grading and heavy multi-pass work is where that trade pays off.</p>

  <h2>Why converting is sometimes instant and sometimes slow</h2>
  <p>If the codec inside your file is already valid for the container you want, the video can be copied
  across untouched. That's a stream copy, it takes seconds, and it's mathematically lossless because
  nothing is re-compressed. Moving H.264 from a .mov into an .mp4 works this way.</p>
  <p>If the codec isn't compatible with the target container, everything has to be decoded and
  re-encoded. That's slower and it costs a compression generation. Going from VP9 in a .webm to an .mp4
  is the common example.</p>
  <p>Crisp takes the fast path wherever the source allows it and only falls back to a full re-encode
  when the codec genuinely can't live in the container you asked for. The practical upshot is that most
  format conversions finish in seconds with no quality cost at all, and the ones that don't are the
  ones where no tool could have avoided it.</p>
""",
 "faq": [
  ("What's the difference between .mp4 and .mov?",
   "They're both containers, and they can hold much the same content. .mov is Apple's format and is the only one of the two that can carry ProRes. For sending a file to someone else, .mp4 with H.264 inside is the safest choice by a wide margin."),
  ("Why won't my file play on someone else's computer?",
   "Almost always the codec rather than the container. HEVC and ProRes are the usual culprits, since both depend on support that older machines and some web platforms don't have. Converting to H.264 in an .mp4 fixes nearly every case."),
  ("Does converting a file lose quality?",
   "Only if it re-encodes. A stream copy, where the compressed video is moved into a different container untouched, is lossless. A genuine re-encode always costs something, though at a sensible bitrate the loss is usually invisible in a single generation."),
  ("Should I edit in ProRes?",
   "If you're doing heavy grading or several rounds of export, it's worth the disk space. For a quick trim and upload it's overkill, and the file sizes are large enough to be genuinely inconvenient."),
 ],
},
]
