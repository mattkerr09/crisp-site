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

{
 "slug": "learn/why-ai-upscaling-cant-fix-focus",
 "crumb": "Focus and upscaling",
 "title": "Why AI upscaling can't fix out-of-focus video — Crisp",
 "h1": "Why AI upscaling can't rescue a shot that missed focus",
 "desc": "Upscalers reconstruct detail from detail that survived. A soft-focus shot has none to work from, so what comes back is invention. What actually responds to restoration, and what doesn't.",
 "faq_heading": "Soft footage, in detail",
 "body": """
  <p>People try this constantly, and it's worth explaining why it disappoints. You have a shot that
  matters, it's slightly out of focus, and an AI upscaler seems like exactly the tool. You run it, the
  result looks sharper at a glance, and something about it is wrong.</p>

  <h2>What an upscaler is actually doing</h2>
  <p>An upscaler is a prediction engine. It was trained on millions of pairs of images, each pair
  being a high-quality original and a degraded copy, and it learned the statistical relationship
  between them. When you feed it a low-resolution frame, it predicts what the high-resolution version
  probably looked like.</p>
  <p>That works because degradation is usually partial. A 480p frame still contains edges, and the
  model has seen enough edges to know what a sharper one looks like. Compression damage leaves the
  underlying structure intact. Sensor noise sits on top of a real signal. In each case there's
  something genuine to reason from.</p>

  <h2>Focus is different in kind</h2>
  <p>An out-of-focus lens doesn't degrade detail, it never records it. Light from a single point in
  the scene lands as a disc rather than a point, so information from neighbouring parts of the subject
  is physically averaged together before it ever reaches the sensor. There's no encoding of the
  original arrangement anywhere in the file.</p>
  <p>Ask a model to sharpen that and it does the only thing it can. It generates plausible detail
  where the training data suggests detail belongs. On a stranger's footage that's often fine, because
  nobody can check. On a face you know, it isn't, because the invented detail is not that person's
  face. The eyes come back subtly wrong, and the effect is unsettling in a way that's hard to name.</p>
  <p>The same reasoning covers heavy motion blur from too slow a shutter, and blown highlights, where
  every pixel in a clipped region holds the identical maximum value and nothing distinguishes a bright
  sky from a brighter one.</p>

  <h2>What does respond well</h2>
  <table>
    <tr><th>Problem</th><th>Recoverable?</th><th>Why</th></tr>
    <tr><td>Low resolution, in focus</td><td>Yes, genuinely</td><td>Real structure survives; the model has something to reason from.</td></tr>
    <tr><td>Compression blocking</td><td>Yes</td><td>Damage sits on top of intact underlying detail.</td></tr>
    <tr><td>Sensor noise, low light</td><td>Yes</td><td>Signal is present, just buried.</td></tr>
    <tr><td>Soft focus</td><td>No</td><td>The detail was never recorded.</td></tr>
    <tr><td>Heavy motion blur</td><td>No</td><td>Same reason: averaged before capture.</td></tr>
    <tr><td>Blown highlights</td><td>No</td><td>Clipped pixels are all identical.</td></tr>
  </table>

  <h2>What to do with a soft shot instead</h2>
  <p>Be honest about what you're doing. If the shot is precious and slightly soft, a gentle
  sharpening pass and good grading will make it read better without pretending to recover anything.
  Cropping in less, keeping it on screen for less time, and cutting to a sharper angle all do more
  than any amount of processing.</p>
  <p>If the softness is uniform across the whole frame rather than just the subject, check whether it
  is actually focus at all. A dirty lens, a cheap filter, heavy denoising applied in-camera or a bad
  transfer all produce something that resembles soft focus and some of those do respond to
  restoration.</p>
  <p>Crisp will run any of this on-device, and it will not tell you a soft shot came back sharp when
  it didn't. That honesty is the useful part: knowing which of your footage is worth the render time
  saves more than a faster renderer would.</p>
""",
 "faq": [
  ("Can any tool fix out-of-focus video?",
   "Nothing recovers the original detail, because it was never recorded. Tools that claim otherwise are generating plausible detail rather than restoring real detail. That can look acceptable on unfamiliar subjects and tends to look wrong on faces you know."),
  ("Why does the sharpened version look strange rather than just sharp?",
   "Because the fine detail is invented. Your eye is very good at faces specifically, so small errors in the arrangement of features read as uncanny even when you can't articulate what changed. On landscapes or textures the same invention usually passes unnoticed."),
  ("Is a slightly soft shot worth upscaling at all?",
   "Often yes, if the softness is mild and the resolution is genuinely low. Upscaling addresses resolution, not focus, and a low-resolution in-focus shot has real structure to work from. Just don't expect the upscale to change how sharply focused it looks."),
  ("Does shooting at a higher resolution protect against this?",
   "It protects against resolution problems, not focus problems. A 4K shot that missed focus contains four times as many pixels of the same blur. Nail focus first; resolution is the easier thing to fix afterwards."),
 ],
},
{
 "slug": "learn/what-is-variable-frame-rate",
 "crumb": "Variable frame rate",
 "title": "What is variable frame rate (VFR), and why does it break edits? — Crisp",
 "h1": "What is variable frame rate?",
 "desc": "Screen recordings and phone footage often store frames at an inconsistent rate. Editors assume a constant one, which is why audio drifts out of sync partway through a cut.",
 "faq_heading": "Frame rate questions",
 "body": """
  <p>Most video stores frames at a fixed interval. Thirty frames per second means a frame every
  thirty-third of a second, forever, and everything downstream can rely on that. Variable frame rate
  breaks the assumption: the gap between frames changes during the recording.</p>

  <h2>Why anything records this way</h2>
  <p>It's usually a sensible decision made for good reasons. Screen recorders capture a new frame when
  something on screen changes, so a static document produces almost no frames and a scrolling page
  produces many. That saves an enormous amount of space.</p>
  <p>Phones do something similar for a different reason. In low light the sensor needs a longer
  exposure per frame, so the capture rate drops to let more light in, then climbs again when you walk
  outside. Thermal limits and battery saving push the same way. The file that comes out says 30fps in
  its metadata and contains stretches that were really recorded at 24, or 17.</p>

  <h2>How it shows up as a problem</h2>
  <p>Editors and encoders overwhelmingly assume a constant rate. Hand them a variable-rate file and
  they read the nominal rate from the header, lay the frames out at that spacing, and everything is
  fine until it isn't. Audio was recorded against real time and doesn't drift. Video laid out at the
  wrong spacing does.</p>
  <p>The signature is unmistakable once you know it: sync is perfect at the start of the clip and
  progressively worse towards the end. If your lips are half a second ahead by the five minute mark
  but fine at the beginning, you have a variable frame rate file, not a sync problem.</p>
  <p>Two other symptoms come from the same cause. Cuts landing a frame or two off where you placed
  them, and exported files whose duration doesn't match the source.</p>

  <h2>The fix is conversion, not correction</h2>
  <p>You can't repair the timing after the fact by nudging the audio, because the error accumulates
  rather than being a fixed offset. The fix is to convert the video to a constant frame rate before
  editing, duplicating or dropping frames as needed so that real time and frame position agree
  again.</p>
  <p>Done properly, this is close to invisible. The frames themselves are untouched; only their
  spacing changes. Done badly, by simply reinterpreting the file at a different nominal rate, it makes
  the drift worse.</p>
  <p>Crisp resamples to a constant rate as part of its decode stage, so anything you run through it
  comes out with the timing already regularised and the audio still lined up. That's not a feature
  anybody asks for by name. It's the reason screen recordings and phone clips behave predictably
  afterwards.</p>

  <h2>Catching it before it costs you an edit</h2>
  <p>The quickest check is duration against frame count. If the two disagree with the declared frame
  rate, the file is variable. Failing that, the practical habit is simply to normalise anything that
  came from a screen recorder, a phone shot in low light, or a game capture tool before it goes near a
  timeline. Those three sources account for the overwhelming majority of cases.</p>
""",
 "faq": [
  ("Why is my audio in sync at the start and drifting by the end?",
   "That pattern is nearly always variable frame rate. A fixed offset would be wrong from the first frame. Progressive drift means video and audio are being laid out against different clocks, and the gap accumulates as the clip plays."),
  ("Does converting to constant frame rate lose quality?",
   "The frames themselves aren't re-encoded by the resampling itself, so the picture is unchanged. What changes is spacing, which means some frames get duplicated or dropped. On footage that was genuinely varying a lot you can occasionally see a small hitch where a frame was repeated."),
  ("Which sources are usually variable?",
   "Screen recorders almost always, phone footage frequently once light drops, and game capture tools very often. Dedicated cameras generally record constant frame rate, which is why footage from a proper camera tends to behave in an editor."),
  ("Can I just tell my editor the real frame rate?",
   "No, because there isn't one. The rate genuinely changed during the recording, so no single number describes the file. That's what makes conversion rather than reinterpretation the only reliable fix."),
 ],
},
{
 "slug": "learn/film-grain-vs-digital-noise",
 "crumb": "Grain vs noise",
 "title": "Film grain vs digital noise: how to tell them apart — Crisp",
 "h1": "Film grain and digital noise are not the same thing",
 "desc": "One is a physical property of film stock that people pay to add. The other is sensor error that people pay to remove. Telling them apart decides whether you denoise a clip or ruin it.",
 "faq_heading": "Grain and noise, in detail",
 "body": """
  <p>Both look like a fine speckle over the picture. They come from completely different places, they
  behave differently frame to frame, and treating one as the other is how footage gets ruined in a
  single pass.</p>

  <h2>Grain is structure. Noise is error.</h2>
  <p>Film grain comes from the silver halide crystals in the emulsion. They're physically distributed
  through the film, they vary in size, and they're the mechanism by which the image exists at all.
  Grain is finer in shadows and coarser in highlights on some stocks, the opposite on others, and it
  has a texture that people find pleasant enough to simulate deliberately decades after shooting on
  film became unusual.</p>
  <p>Digital noise is measurement error. A sensor photosite counts photons, the count is uncertain,
  and amplifying a weak signal amplifies the uncertainty along with it. That's why noise climbs with
  ISO and why it's worst in shadows, which is the exact inverse of how most film grain behaves.</p>

  <h2>The tells, in order of usefulness</h2>
  <p><strong>Colour.</strong> Digital noise usually has chroma noise mixed in, showing as red and
  green blotches in dark areas. Film grain is largely luminance and stays neutral. Coloured speckle in
  shadows is close to conclusive.</p>
  <p><strong>Where it lives.</strong> Noise concentrates in the darkest parts of the frame and
  disappears in bright areas. Grain is present across the whole exposure range.</p>
  <p><strong>Behaviour over time.</strong> Both change every frame, but noise often has a directional
  or banded quality from the sensor readout, sometimes visible as faint horizontal streaking. Grain is
  isotropic.</p>
  <p><strong>Scale.</strong> Grain has a consistent size determined by the stock. Digital noise scales
  with whatever processing has been applied, so a heavily compressed file shows blocky noise that
  clusters at the edges of compression blocks.</p>

  <h2>Why it matters before you denoise</h2>
  <p>Denoising treats fine high-frequency variation as something to remove. Run it hard on genuinely
  grainy film and you get the waxy, plastic look that gives cheap restorations away, because the grain
  was carrying the impression of texture and detail. Faces suffer worst, since skin texture and grain
  occupy a similar frequency band.</p>
  <p>Run it on real sensor noise and it does exactly what you want. The signal underneath is real and
  the noise genuinely is error.</p>
  <p>The practical rule for restoring old footage is to denoise conservatively and stop earlier than
  feels right. You can always run a second pass. You can't put grain back convincingly once the
  structure it was sitting on has been smoothed away, and adding synthetic grain afterwards on top of
  a waxy image fools nobody.</p>

  <h2>Adding grain on purpose</h2>
  <p>Going the other way is legitimate and common. A little grain hides banding in gradients, gives
  digital footage a texture that reads as less clinical, and can mask mild compression artefacts.</p>
  <p>Two cautions. Grain is close to incompressible, so adding it before a platform re-encode spends
  bitrate that the rest of the frame needed. And it should go on last, after upscaling and grading,
  or the upscaler will treat it as detail to reconstruct and the grade will shift its character.</p>
  <p>Crisp handles both directions on-device: denoise for real sensor noise, and a grain pass in the
  colour lane for when you want the texture back.</p>
""",
 "faq": [
  ("Should I remove grain from old film footage?",
   "Usually only a little. Grain is part of how film footage looks, and aggressive denoising produces the waxy appearance that makes a restoration obvious. Remove enough that the picture reads cleanly and stop there."),
  ("How do I tell noise from grain quickly?",
   "Look at the shadows for coloured speckle. Red and green blotches in dark areas are chroma noise and mean digital. Neutral speckle spread evenly across bright and dark areas is more likely to be grain."),
  ("Does adding grain make my video look more cinematic?",
   "In moderation it can, mostly because it breaks up banding and softens the clinical look of clean digital footage. Overdone it just looks noisy, and it costs real bitrate on any platform that re-encodes."),
  ("Should grain go on before or after upscaling?",
   "After. An upscaler reconstructs what it reads as detail, and grain applied first gets magnified and reinterpreted. Grade, upscale, then add grain last."),
 ],
},

{
 "slug": "learn/why-phone-video-looks-shaky",
 "crumb": "Shaky phone video",
 "title": "Why phone video looks shaky, and what stabilization can fix — Crisp",
 "h1": "Why phone video looks shaky",
 "desc": "Handheld wobble and rolling shutter skew look similar and are different problems. Only one of them is fixable after the fact, and knowing which is which saves a lot of wasted rendering.",
 "faq_heading": "Shaky footage questions",
 "body": """
  <p>Two things make handheld footage unpleasant, and people tend to lump them together. One is
  ordinary camera shake. The other is rolling shutter, and it is a different problem with a different
  answer.</p>

  <h2>Shake is movement. Skew is a sampling artefact.</h2>
  <p>Shake is what it sounds like. Your hands move, the whole frame moves with them, and the picture
  jitters. Every part of the frame moves together, which is the important detail: the geometry inside
  the frame stays correct.</p>
  <p>Rolling shutter is stranger. Most phone and mirrorless sensors don't capture a whole frame at
  once. They read it out line by line, top to bottom, over a few milliseconds. If the camera or the
  subject moves during that readout, the top of the frame was captured at a slightly different moment
  than the bottom, so vertical lines lean. Pan quickly past a lamp post and it bends. Shoot from a
  moving car and the world tilts. Shoot a propeller and it turns into something surreal.</p>
  <p>You can tell them apart by looking at a still frame. Shake looks fine frozen and bad in motion.
  Rolling shutter is visible in a single frame, because the distortion is baked into the geometry.</p>

  <h2>What stabilization actually does</h2>
  <p>Stabilization estimates how much the frame moved between one frame and the next, then shifts each
  frame back the other way to cancel it out. Because shifting exposes empty edges, it either crops in
  slightly or fills the edges by mirroring what's next to them.</p>
  <p>That works genuinely well on shake, and it costs you a little framing. What it cannot do is undo
  rolling shutter, because the distortion isn't a whole-frame offset. Different rows of the same frame
  need different corrections, which is a fundamentally harder operation and one Crisp does not
  attempt. Stabilizing skewed footage produces steady, still-skewed footage.</p>

  <h2>What to do about each</h2>
  <table>
    <tr><th>Symptom</th><th>Cause</th><th>Fixable afterwards?</th></tr>
    <tr><td>Whole frame jitters, stills look fine</td><td>Camera shake</td><td>Yes, stabilization handles this well</td></tr>
    <tr><td>Vertical lines lean during pans</td><td>Rolling shutter</td><td>No, not in Crisp</td></tr>
    <tr><td>Sharp jolts at footsteps</td><td>Walking shake</td><td>Partly, and a slower walk helps more</td></tr>
    <tr><td>Wobble that looks like jelly</td><td>Rolling shutter plus shake</td><td>The shake, not the wobble</td></tr>
  </table>
  <p>On the shooting side, the fixes are boring and effective. Pan slower, because rolling shutter
  scales with how fast the scene crosses the sensor. Brace against something. Use the phone's own
  stabilization if it has it, since correcting during capture beats correcting afterwards. And shoot a
  little wider than you need, so stabilization has room to crop into without losing your framing.</p>

  <h2>Doing it on a Mac</h2>
  <p>Crisp stabilizes on-device using frame-to-frame motion estimation, keeps the audio in sync, and
  saves the result alongside the original rather than overwriting it. You can ask for it in plain
  English, and if the clip turns out to be steady enough already that stabilizing would cost framing
  for no visible gain, it will tell you rather than burning the render time.</p>
""",
 "faq": [
  ("Can stabilization fix rolling shutter?",
   "Not in Crisp, and not with the approach most tools use. Stabilization shifts whole frames to cancel movement. Rolling shutter distorts different rows of the same frame by different amounts, so cancelling it needs a per-row correction, which is a different and much harder operation."),
  ("Does stabilizing crop my video?",
   "Usually a little, because shifting a frame to cancel movement exposes empty edges that have to come from somewhere. Crisp fills those edges by mirroring rather than cropping hard, but framing still tightens slightly on very shaky footage."),
  ("Should I stabilize before or after upscaling?",
   "Stabilize first. Upscaling magnifies everything including the shake, and a stabilizer works better on the smaller frame anyway. It is also much faster in that order."),
  ("Why does my footage look worse after stabilizing?",
   "Usually one of two things. Either the clip was steady enough that you have paid a crop for nothing, or the motion was mostly rolling shutter, which stabilization cannot address and can make more obvious by removing the shake that was masking it."),
 ],
},
{
 "slug": "learn/what-is-hdr-video",
 "crumb": "HDR video",
 "title": "What is HDR video, and why does it look washed out? — Crisp",
 "h1": "What is HDR video?",
 "desc": "Your iPhone records HDR by default. Open that file somewhere that does not understand it and the colours go grey and flat. What HDR actually stores, and why tone mapping matters.",
 "faq_heading": "HDR questions",
 "body": """
  <p>HDR video stores a wider range of brightness than traditional video, and a wider range of colour
  with it. Where standard video assumes a display that peaks around 100 nits, HDR formats carry
  information for displays reaching ten times that or more, so a sunlit window can be genuinely bright
  while the shadows beside it stay detailed rather than crushed to black.</p>
  <p>If you own a recent iPhone, you are almost certainly shooting it already, and possibly without
  having chosen to.</p>

  <h2>Why it looks washed out somewhere else</h2>
  <p>This is the complaint that brings most people to the topic. Footage looks vivid on the phone,
  then grey and flat once it is somewhere else.</p>
  <p>The file stores brightness using a transfer curve designed for HDR displays, most often PQ or
  HLG. Software that understands the tagging maps those values onto whatever display you have.
  Software that does not simply reads the numbers as if they were ordinary values, and the result is
  flat, desaturated and slightly milky. Nothing is damaged. It is being interpreted with the wrong
  assumption.</p>
  <p>The same thing happens on upload. A platform that strips or ignores the HDR metadata serves
  everyone the washed-out interpretation, which is why a clip can look fine in your editor and wrong
  in the feed.</p>

  <h2>Tone mapping is the honest answer</h2>
  <p>Converting HDR to standard range properly is called tone mapping, and it is not a simple scale.
  You are fitting a wide brightness range into a narrower one, so something has to give. A good tone
  map compresses the highlights gradually, keeps mid-tones roughly where the eye expects them, and
  preserves colour relationships while it does so.</p>
  <p>A bad conversion clips the highlights flat, which throws away exactly the detail HDR was
  capturing, or lifts everything uniformly, which produces the grey look people are trying to escape.</p>
  <p>Crisp detects HDR sources from their colour metadata and runs a proper tone map on-device when
  the output needs standard range. There is no setting to get wrong, which matters because the failure
  mode here is silent: nothing errors, the colours are just quietly incorrect.</p>

  <h2>When to keep HDR and when to convert</h2>
  <p>Keep it when your delivery target genuinely supports it end to end, and when the footage has a
  brightness range worth preserving. A sunset, a stage with hard lighting, a window in an interior
  shot.</p>
  <p>Convert when the destination is uncertain. Anything going to a general audience, an older
  machine, a projector, or a platform whose handling you have not tested is safer delivered in
  standard range where you controlled the conversion, rather than left to whatever the viewer's
  software decides.</p>
  <p>Mixing HDR and non-HDR clips on one timeline is the other common trap. Convert everything to a
  single range before you start editing, or the grade you apply to one clip will be wrong on the
  next.</p>
""",
 "faq": [
  ("Why does my iPhone video look grey on my computer?",
   "It is HDR, and whatever you are viewing it in is not interpreting the HDR tagging. The file is fine. Converting it to standard range with a proper tone map gives you a version that looks right everywhere."),
  ("Should I turn HDR off on my phone?",
   "If most of your footage ends up on social platforms or gets shared widely, turning it off removes a whole class of problem. If you are shooting things with genuinely wide brightness range and you control delivery, keeping it is worth the extra care."),
  ("Does converting HDR to SDR lose quality?",
   "It loses range, unavoidably, because you are fitting a wider brightness scale into a narrower one. Done with a proper tone map the result looks natural and the loss is mostly in highlight detail you could not have displayed anyway."),
  ("Can I mix HDR and standard clips in one edit?",
   "You can, but you should not without converting first. The two ranges grade completely differently, so adjustments that look right on one clip will be wrong on the next. Normalise everything to one range before you start."),
 ],
},
{
 "slug": "learn/why-4k-exports-take-so-long",
 "crumb": "Why exports take so long",
 "title": "Why AI upscaling to 4K takes so long — Crisp",
 "h1": "Why upscaling to 4K takes so long",
 "desc": "A ten minute clip can take hours. Here is where that time actually goes, why it is not a bug, and the levers that genuinely shorten it.",
 "faq_heading": "Render time, in detail",
 "body": """
  <p>People are often surprised that upscaling a short clip can take longer than the clip itself by a
  large multiple. It is worth understanding where the time goes, because some of it is avoidable and
  some of it really is not.</p>

  <h2>Every frame is a separate job</h2>
  <p>A normal video export re-encodes frames, which modern hardware does in dedicated silicon at
  extraordinary speed. AI upscaling is a different kind of work. Each frame is passed through a neural
  network that performs many millions of operations to produce its output, and it does that
  independently for every single frame.</p>
  <p>A ten minute clip at 30fps is eighteen thousand frames. Even at a very respectable third of a
  second per frame, that is an hour and a half of pure model inference before any encoding happens.
  The maths is unforgiving and it scales linearly with length.</p>

  <h2>Where the rest of the time goes</h2>
  <p>Decoding the source, applying the colour chain, and writing frames out are all real costs, though
  smaller. Upscaling to 4K means the model is producing roughly eight million pixels per frame, and
  the encoder afterwards is compressing eight million pixels per frame too, which is four times the
  work of a 1080p export at the same length.</p>
  <p>Memory matters more than people expect. Large frames and large models compete for the same pool,
  and when that pool is tight the work has to be broken into tiles and reassembled, which costs both
  time and a little quality at the seams.</p>

  <h2>What genuinely makes it faster</h2>
  <p><strong>Trim first.</strong> The single biggest lever, and the most ignored. If you only need
  thirty seconds of a ten minute clip, cutting before upscaling removes 95% of the work. Do this
  before anything else.</p>
  <p><strong>Pick the target you actually need.</strong> Upscaling 1080p to 4K is four times the
  output pixels of 1080p to 1440p. If the destination is a phone screen or a social feed, the larger
  target may be invisible to every viewer.</p>
  <p><strong>Do not stack lanes you do not need.</strong> Frame interpolation multiplies the frame
  count before upscaling ever runs, so doubling the frame rate doubles an already long job.</p>
  <p><strong>Let it run unattended.</strong> Because everything is on-device there is no per-minute
  billing and no upload, so a long job overnight costs nothing but electricity. That changes the
  calculation compared with cloud services, where the incentive is to keep jobs short.</p>

  <h2>What does not help</h2>
  <p>Closing other applications rarely makes a measurable difference unless you were genuinely short
  of memory. Neither does exporting at a higher bitrate, which affects file size rather than the
  inference that dominates the time. And re-running a job at a lower quality preset to "warm it up"
  does nothing at all, since nothing is cached between runs.</p>
""",
 "faq": [
  ("Is it normal for a ten minute clip to take over an hour?",
   "For AI upscaling to 4K, yes. Each frame goes through a neural network individually, and a ten minute clip at 30fps is eighteen thousand of them. The time scales with length and with output resolution, and there is no shortcut that preserves the quality."),
  ("Does a faster Mac help?",
   "Substantially, because the work is dominated by model inference and that is exactly what Apple Silicon's neural and GPU hardware accelerates. Available memory matters too, since tight memory forces the frame to be processed in tiles."),
  ("Why is the first frame slower than the rest?",
   "The model has to be loaded and initialised before the first frame can be processed. After that the per-frame cost settles into a steady rate, so a progress estimate taken from the first few seconds usually reads pessimistically."),
  ("Can I use my Mac while it runs?",
   "Yes, though heavy work will compete for the same GPU and slow both. Light use is fine. Because nothing is uploaded, leaving a long job running overnight costs nothing beyond power."),
 ],
},
]
