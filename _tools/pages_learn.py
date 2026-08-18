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

{
 "slug": "vs/upscayl-alternative-mac",
 "section": "Compare",
 "crumb": "Upscayl",
 "title": "Upscayl vs Crisp on Mac: same engine, different job — Crisp",
 "h1": "Upscayl vs Crisp: the same engine, doing a different job",
 "desc": "Crisp bundles the same Real-ESRGAN engine Upscayl uses. That is not a coincidence and it is worth being straight about, because it means the honest comparison is not about upscaling quality at all.",
 "faq_heading": "Upscayl and Crisp, in detail",
 "body": """
  <p>Let's start with the part most comparison pages would bury. Crisp bundles <code>upscayl-bin</code>,
  the same ncnn build of Real-ESRGAN that Upscayl is built around, redistributed under its
  BSD-3-Clause and MIT licences and credited in Crisp's NOTICES file. On a single photo, at the same
  model and the same scale, you should expect the same result. There is no secret sauce and claiming
  one would be easy to disprove.</p>
  <p>So the real question isn't which upscales better. It's what happens either side of the upscale.</p>

  <h2>Upscayl is an image tool, and a good one</h2>
  <p>Upscayl is free, open source, actively developed, and genuinely excellent at what it does. Point
  it at a folder of photos, pick a model, get bigger photos. If that is your problem, it solves it
  completely and costs nothing, and you should use it.</p>
  <p>What it does not do is video. That is not a shortcoming, it's scope. A video is not a folder of
  photos, and treating it as one is where the difficulty starts.</p>

  <h2>What a video actually needs around the model</h2>
  <p>Run an image upscaler over extracted frames and you meet the problems in roughly this order.</p>
  <p><strong>Audio.</strong> Frames carry none. You have to demux it, keep it aligned through any
  frame-rate change, and mux it back without drift.</p>
  <p><strong>Frame rate.</strong> Phone and screen-recorded footage is often variable frame rate, so
  the gap between frames changes during the clip. Extract to stills and that timing information is
  gone, which is how audio ends up half a second out by the end of a long take.</p>
  <p><strong>Interlacing.</strong> Older footage stores each frame as two half-pictures captured
  moments apart. An upscaler reads the resulting comb pattern as fine detail and sharpens it into
  something much harder to remove. It has to be deinterlaced first, and nothing about a folder of PNGs
  tells you that it should be.</p>
  <p><strong>Colour.</strong> HDR sources need a proper tone map on the way in and out, or the result
  is flat and grey.</p>
  <p><strong>Order.</strong> Deinterlace, denoise, upscale, colour. Get that wrong and each step makes
  the next harder.</p>
  <p><strong>Scale.</strong> A ten minute clip is eighteen thousand frames. Somebody has to manage
  disk, memory, resumability and the encode at the end.</p>
  <p>None of that is upscaling. All of it is what makes upscaling a video work.</p>

  <h2>The comparison that's actually useful</h2>
  <table>
    <tr><th></th><th>Upscayl</th><th>Crisp</th></tr>
    <tr><td>Price</td><td>Free, open source</td><td>Free with a watermark; $99 once to remove it</td></tr>
    <tr><td>Photos</td><td>Yes, its whole purpose</td><td>Yes, 9 formats including HEIC and AVIF</td></tr>
    <tr><td>Video</td><td>No</td><td>Yes, with audio, timing and colour handled</td></tr>
    <tr><td>Upscaling engine</td><td>Real-ESRGAN (ncnn)</td><td>The same Real-ESRGAN (ncnn)</td></tr>
    <tr><td>Editing</td><td>No</td><td>Trim, crop, grade, stabilize, captions, timeline</td></tr>
    <tr><td>Plain-English requests</td><td>No</td><td>Type what you want</td></tr>
    <tr><td>Runs offline</td><td>Yes</td><td>Yes</td></tr>
  </table>

  <h2>The honest recommendation</h2>
  <p>If you are upscaling photos, use Upscayl. It is free, it is excellent, and Crisp would be
  charging you for an engine you can already run yourself.</p>
  <p>If you are upscaling video, the model was never the hard part, and a tool that only wraps the
  model leaves you to solve the rest by hand. That is the work Crisp is actually selling, and it is
  worth being clear that this, not image quality, is the difference.</p>
""",
 "faq": [
  ("Does Crisp really use the same upscaler as Upscayl?",
   "Yes. Crisp bundles upscayl-bin, an ncnn build of Real-ESRGAN, under its BSD-3-Clause and MIT licences, credited in Crisp's NOTICES file. On a single image at the same model and scale you should expect the same output."),
  ("Then why would I pay for Crisp?",
   "For video, and for everything around the model: audio kept in sync, variable frame rate normalised, interlacing handled before it gets sharpened, HDR tone mapped, the ordering of restoration steps handled for you, and a timeline to actually cut with. For photos alone, Upscayl is free and does the job."),
  ("Can Upscayl do video if I extract the frames myself?",
   "You can upscale the frames, yes. You then have to reassemble them with the original audio, preserve the timing of a variable-rate source, and handle interlacing and colour yourself. It's doable and it is a real afternoon of work per clip."),
  ("Is Crisp just a wrapper around Upscayl?",
   "For the standard upscale lane it uses that engine, and says so. The rest of the app is its own: the timeline editor, the plain-English layer, stabilization, grading, captions, the montage builder, and the generative Max restore lane, which is a different model entirely."),
 ],
},

{
 "slug": "learn/what-is-rolling-shutter",
 "crumb": "Rolling shutter",
 "title": "What is rolling shutter, and can it be fixed? — Crisp",
 "h1": "What is rolling shutter?",
 "desc": "Leaning lamp posts, wobbling propellers and a world that tilts when you pan. Where the distortion comes from, and the honest answer about fixing it afterwards.",
 "faq_heading": "Rolling shutter, in detail",
 "body": """
  <p>Pan quickly past a lamp post and it leans. Film out of a car window and the buildings tilt.
  Shoot a spinning propeller and it turns into something from a dream. That is rolling shutter, and
  once you know the cause you can predict exactly when it will bite.</p>

  <h2>The sensor doesn't take the picture all at once</h2>
  <p>A global shutter captures every pixel at the same instant. Almost nothing you own has one. Most
  phone, mirrorless and action-camera sensors read out row by row from the top of the frame to the
  bottom, over a few milliseconds.</p>
  <p>That means the bottom of a frame is a snapshot of a slightly later moment than the top. If
  nothing moved during the readout, no problem. If the camera or the subject moved, each row
  captured the scene from a marginally different position, and straight vertical lines come out
  slanted.</p>

  <h2>Why the effect scales the way it does</h2>
  <p>The distortion is proportional to how far the scene travels across the sensor during one
  readout. That gives you the practical rules.</p>
  <p>Fast pans are worse than slow pans. Long lenses are worse than wide ones, because the same
  angular movement sweeps far more of the frame. Vibration from an engine or a drone body is
  especially bad, because it moves the camera many times within a single readout and the frame
  ripples rather than simply leaning. And a cheaper or older sensor generally reads out more slowly,
  so it distorts more at the same shutter speed.</p>
  <p>Shutter speed itself is not the cause, which surprises people. A fast shutter freezes motion
  within each row but does nothing about the delay between the first row and the last.</p>

  <h2>Can it be fixed afterwards?</h2>
  <p>Not in Crisp, and it is worth explaining why rather than just saying no.</p>
  <p>Stabilization works by estimating how the whole frame moved between one frame and the next, then
  shifting the frame back to cancel it. That is a single transform applied to the entire picture.
  Rolling shutter is not a whole-frame offset. Every row needs a different correction, because every
  row was captured at a different moment, so undoing it means estimating motion per row and warping
  the frame non-uniformly. That is a fundamentally harder operation, it needs a good estimate of the
  sensor's readout time, and done badly it introduces wobble of its own.</p>
  <p>So stabilizing skewed footage gives you steady, still-skewed footage. Worse, removing the shake
  can make the skew more visible, because the shake was masking it.</p>

  <h2>What to do instead</h2>
  <p>Almost all of the fix happens at the camera. Pan slower, and if you need a fast whip, embrace it
  as a transition rather than something viewers will study. Use a wider lens and step closer. Isolate
  the camera from vibration, which matters more than anything else on drones and vehicles. Turn on
  in-body or in-app stabilization, because correcting during capture is far more effective than
  correcting after.</p>
  <p>In the edit, the honest options are to cut around the worst of it, slow the shot down so the
  distortion reads as motion blur, or crop in on a region where the skew is less obvious. None of
  those are glamorous, and all of them beat a render that cannot deliver.</p>
""",
 "faq": [
  ("Is rolling shutter the same as motion blur?",
   "No. Motion blur is smearing within a single exposure and affects the whole frame equally. Rolling shutter is geometric distortion caused by different rows being captured at different times, so it leans and wobbles rather than smearing."),
  ("Does a faster shutter speed help?",
   "Not with rolling shutter. A fast shutter freezes motion within each row, but the delay between the top row and the bottom row is unchanged, so the skew stays. It will reduce motion blur, which sometimes makes the skew easier to see."),
  ("Why do propellers and helicopter blades look so strange?",
   "They are moving fast enough to travel a long way during a single readout, so different parts of the blade are recorded at meaningfully different positions. The result can be blades that appear detached or bent into curves."),
  ("Will Crisp's stabilizer make it worse?",
   "It will not add skew, but it can make existing skew more noticeable by removing the shake that was disguising it. If a clip is mostly rolling shutter rather than shake, stabilizing costs you a small crop for little visible gain."),
 ],
},
{
 "slug": "learn/what-is-chroma-subsampling",
 "crumb": "Chroma subsampling",
 "title": "What is chroma subsampling? 4:2:0 vs 4:4:4 explained — Crisp",
 "h1": "What is chroma subsampling?",
 "desc": "Almost every video you own stores colour at a quarter of the detail of brightness. Usually invisible, occasionally the reason red text looks like it is bleeding.",
 "faq_heading": "Colour detail, in detail",
 "body": """
  <p>Here is a fact about nearly every video file you have ever watched: it stores far less colour
  information than brightness information. Not a little less. Typically a quarter as much.</p>
  <p>This is chroma subsampling, it has been standard since analogue television, and it works because
  of how your eyes are built.</p>

  <h2>Your eyes are not symmetrical about this</h2>
  <p>Human vision has far more rod cells, which resolve brightness, than cone cells, which resolve
  colour. We are extremely good at seeing fine detail in light and shade, and comparatively poor at
  seeing fine detail in hue. Video encoding exploits that directly: keep full resolution for
  brightness, throw away most of the colour resolution, and the loss is close to invisible on the
  sort of images cameras usually capture.</p>
  <p>The notation describes the sampling of a small block of pixels. 4:4:4 keeps colour at full
  resolution. 4:2:2 halves it horizontally. 4:2:0 halves it both horizontally and vertically, so one
  colour sample covers a two-by-two block of pixels. That last one is what your phone shoots, what
  streaming services deliver, and what almost every h.264 and HEVC file uses.</p>

  <h2>When you actually notice</h2>
  <p>On ordinary photographic footage, essentially never. The places it shows up are specific and
  worth knowing, because they explain problems that otherwise look like a bug.</p>
  <p><strong>Saturated text and graphics.</strong> Red or blue text on a contrasting background is
  the classic case. The edges look soft or fringed, because the letterforms are defined by a colour
  boundary that is being stored at half or quarter resolution. Screen recordings suffer the most.</p>
  <p><strong>Chroma keying.</strong> Pulling a clean key from green screen footage is much harder at
  4:2:0, because the edge between subject and background is exactly the fine colour detail that was
  discarded. This is why people shoot 4:2:2 or better for compositing.</p>
  <p><strong>Heavy grading.</strong> Pushing colour hard exaggerates whatever colour resolution you
  have, so banding and blockiness in gradients become visible.</p>
  <p><strong>Repeated re-encoding.</strong> Each generation resamples chroma again, and errors
  compound around sharp colour edges.</p>

  <h2>What you can and cannot do about it</h2>
  <p>You cannot recover colour detail that was never sampled, in the same way you cannot recover
  focus. Converting a 4:2:0 file to 4:4:4 upsamples what is there; it invents nothing.</p>
  <p>What you can do is avoid making it worse. Shoot 4:2:2 if your camera offers it and you plan to
  key or grade heavily. Keep an intermediate master rather than re-encoding a delivery file
  repeatedly. And when adding text or graphics, do it at the final stage so the letterforms are
  encoded once rather than surviving several generations.</p>
  <p>Crisp exports 4:2:0 for the same reason everyone does: universal compatibility. A file that
  plays everywhere is worth more than colour resolution most viewers cannot see, and the exceptions
  above are narrow enough to plan around.</p>
""",
 "faq": [
  ("Should I export 4:4:4?",
   "Only for a specific reason, such as delivering to someone who will key or grade the footage, or archiving text-heavy screen content. For anything headed to a viewer, 4:2:0 is what plays reliably everywhere, and the difference is invisible on photographic material."),
  ("Why does red text look blurry in my screen recording?",
   "Chroma subsampling. Text edges are defined by a colour boundary, and at 4:2:0 that boundary is stored at a quarter resolution. Recording at a higher resolution helps more than raising the bitrate, because it gives the colour channel more samples to work with."),
  ("Does upscaling fix it?",
   "It can improve the appearance, because a good model reconstructs plausible edges, but it is not recovering the original colour samples. Treat it as making the best of what survived rather than a genuine restoration."),
  ("Is this why green screen keys look ragged?",
   "Frequently, yes. The subject-to-background edge is precisely the fine colour detail that 4:2:0 discards. Shooting 4:2:2 or better, and lighting the screen evenly, both matter more than the software doing the key."),
 ],
},

{
 "slug": "learn/what-is-a-keyframe",
 "crumb": "Keyframes",
 "title": "What is a keyframe in video? Why scrubbing and trimming behave oddly — Crisp",
 "h1": "What is a keyframe?",
 "desc": "Most frames in a video file are not pictures. They are instructions describing how the last frame changed. That single fact explains scrubbing lag, odd cut points and why some edits are instant.",
 "faq_heading": "Keyframes, in detail",
 "body": """
  <p>Open a video file and you might assume it contains a sequence of pictures. It mostly doesn't. A
  small fraction of the frames are complete images, and the rest are descriptions of how the previous
  frame changed.</p>
  <p>The complete ones are keyframes, also called I-frames. Everything else depends on them.</p>

  <h2>Why encoders work this way</h2>
  <p>Consecutive frames are overwhelmingly similar. In a two second shot of someone talking, the wall
  behind them is identical in every frame. Storing that wall sixty times is enormously wasteful, so
  the encoder stores it once and then records only what moved.</p>
  <p>The saving is not marginal. A typical delivery file might place a keyframe every two to ten
  seconds, and the frames in between can be a small fraction of the size. That is most of why a
  ten minute video is not gigabytes.</p>

  <h2>The three consequences you actually feel</h2>
  <p><strong>Scrubbing feels sticky on some files.</strong> To display an arbitrary frame, the decoder
  has to find the previous keyframe and rebuild every frame from there to the one you asked for. Drop
  the playhead just before a keyframe and the work is small. Drop it just after and there may be
  hundreds of frames to reconstruct first.</p>
  <p><strong>Cuts can land where you didn't put them.</strong> A trim that re-encodes can cut
  anywhere. A trim that copies the stream without re-encoding can only start at a keyframe, because
  there is nothing else to start from. That is why some tools quietly move your in-point by up to a
  few seconds and why the result is sometimes shorter or longer than you asked for.</p>
  <p><strong>Some operations are instant and some are not.</strong> Anything that can be done by
  copying compressed data straight across is fast and lossless. Anything that has to decode and
  re-encode costs time and a generation of quality.</p>

  <h2>Editing codecs make a different trade</h2>
  <p>ProRes and similar intermediate codecs store every frame independently, which is to say every
  frame is a keyframe. That is why scrubbing a ProRes file is instant and why cuts land exactly where
  you place them. You pay in file size, often by a factor of ten or more.</p>
  <p>That trade is the whole reason both kinds of codec exist. Delivery codecs optimise for the
  viewer who watches start to finish. Editing codecs optimise for the editor who jumps around.</p>

  <h2>What this means in practice</h2>
  <p>If scrubbing is painful on a long file, the codec is usually the reason rather than your machine.
  Transcoding to an intermediate before a heavy edit is a real fix, not a superstition.</p>
  <p>If a trim landed in the wrong place, the tool almost certainly took the fast stream-copy path.
  Crisp uses that path for container conversion, where it is genuinely lossless and finishes in
  seconds, and re-encodes when the codec cannot survive the change. Frame-accurate trimming in the
  timeline re-encodes, which is slower and lands exactly where you asked.</p>
  <p>And if you are re-exporting the same file repeatedly, remember that each re-encode is a
  generation of loss. Keep the master.</p>
""",
 "faq": [
  ("Why does my video scrub smoothly in one app and badly in another?",
   "Usually because one app has transcoded or cached an intermediate version. The underlying file still needs a keyframe plus every frame since, so an app that quietly builds a proxy will feel far faster on the same source."),
  ("Can I add more keyframes to make editing easier?",
   "Only by re-encoding, which means a quality generation. If you are doing serious work the better move is transcoding to an intermediate codec where every frame is independent, rather than nudging the keyframe interval of a delivery codec."),
  ("Why is trimming sometimes instant and sometimes slow?",
   "Instant means the tool copied the compressed stream without decoding, which can only start at a keyframe. Slow means it decoded and re-encoded, which lands the cut exactly where you asked and costs a generation."),
  ("Does a shorter keyframe interval improve quality?",
   "Not directly, and it can hurt. Keyframes are large, so more of them at a fixed bitrate leaves fewer bits for everything else. Shorter intervals help seeking and streaming startup, which is why streaming platforms use them."),
 ],
},
{
 "slug": "learn/what-is-color-space",
 "crumb": "Colour space",
 "title": "What is a colour space? Rec.709, Rec.2020 and why colours shift — Crisp",
 "h1": "What is a colour space?",
 "desc": "A file does not store colours, it stores numbers. A colour space is the agreement about what those numbers mean, and when that agreement is missing your footage comes out wrong.",
 "faq_heading": "Colour space questions",
 "body": """
  <p>A video file contains numbers. The number 200 in the red channel means nothing on its own. A
  colour space is the agreement that turns those numbers into actual colours: which red is the reddest
  red, how brightness maps to the values, and what white looks like.</p>
  <p>When everything in the chain shares the agreement, colour just works. When something loses track
  of it, you get footage that looks flat, oversaturated, or subtly green, and nothing in the picture
  tells you why.</p>

  <h2>The ones you will meet</h2>
  <p><strong>Rec.709</strong> is the standard for ordinary HD video, and it is what most footage and
  most displays assume. If nothing is tagged and nothing is unusual, it is almost certainly this.</p>
  <p><strong>sRGB</strong> is its close cousin from the computer world. The primaries match Rec.709,
  the brightness curve differs slightly, which is why exported video can look a shade off next to the
  same frame in an image editor.</p>
  <p><strong>Rec.2020</strong> is the much wider space used for HDR and 4K delivery. It can describe
  colours Rec.709 simply cannot reach.</p>
  <p><strong>Log formats</strong> such as S-Log or C-Log are not really display spaces at all. They
  store a wide dynamic range in a deliberately flat, washed-out looking curve, expecting you to grade
  them afterwards. Footage that looks grey and lifeless straight out of a camera is usually log, not
  broken.</p>

  <h2>Why colours shift</h2>
  <p>Three failures cause nearly all of it.</p>
  <p><strong>Missing tags.</strong> The file never recorded which space it used, so the player guesses,
  and different players guess differently. This is why a clip can look right in one app and wrong in
  another with no edit in between.</p>
  <p><strong>Wrong interpretation.</strong> The tag exists but something ignores it. Rec.2020 content
  read as Rec.709 comes out oversaturated; the reverse comes out dull.</p>
  <p><strong>Missing conversion.</strong> Wide-gamut content sent to a standard display without a
  proper conversion looks flat and grey, because the numbers are being read against the wrong
  reference. That is the same failure as untagged HDR.</p>

  <h2>The practical rules</h2>
  <p>Normalise before you edit. Mixing spaces on one timeline means a grade that looks right on one
  clip is wrong on the next, and you will chase that inconsistency for hours before spotting the
  cause.</p>
  <p>Convert deliberately rather than by accident. A real conversion maps colours between the two
  spaces; simply relabelling a file changes what players think without changing the data, which is a
  different operation with a different result.</p>
  <p>Check on more than one screen. A colour problem that only exists on your display is a calibration
  issue, not a file issue, and the fix is in a different place entirely.</p>
  <p>Crisp reads the colour metadata on the way in and tone maps HDR sources properly when the output
  needs standard range, which removes the commonest version of this problem without asking you to
  understand any of the above.</p>
""",
 "faq": [
  ("Why does my footage look washed out before I have touched it?",
   "Two likely causes. It is log footage, which is meant to look flat and expects grading, or it is HDR being displayed by something that is ignoring the tagging. Both look similar and have completely different fixes."),
  ("What is the difference between converting and relabelling?",
   "Converting maps the actual pixel values from one space to another so the colours stay the same. Relabelling changes only the tag, so players reinterpret unchanged data and the colours shift. Relabelling is occasionally the right fix for a mis-tagged file and is wrong for everything else."),
  ("Should I edit in Rec.2020?",
   "Only if your whole chain supports it end to end and the footage has colour worth preserving. Otherwise you are carrying complexity for a range your delivery target will discard anyway."),
  ("Why do the same colours look different in my editor and my browser?",
   "Usually the slight curve difference between Rec.709 and sRGB, plus whether each application is colour-managed. It is a display-side disagreement rather than something wrong with the file."),
 ],
},

{
 "slug": "learn/why-vhs-tapes-degrade",
 "crumb": "VHS degradation",
 "title": "Why VHS tapes degrade, and what can still be recovered — Crisp",
 "h1": "Why VHS tapes degrade",
 "desc": "Magnetic tape loses signal whether you play it or not. What is actually failing, which faults respond to restoration, and why the capture matters more than the software.",
 "faq_heading": "Tape damage, in detail",
 "body": """
  <p>A VHS tape is a strip of plastic coated in magnetic particles, and the picture exists as the
  alignment of those particles. Everything that goes wrong follows from that being a physical
  arrangement rather than a recorded number.</p>

  <h2>What is actually failing</h2>
  <p>Magnetic particles gradually lose their alignment. The effect is slow, it happens whether or not
  the tape is ever played, and it shows as a picture that grows softer and noisier over decades.
  Nothing stops it. Cool, dry, dark storage slows it considerably.</p>
  <p>The binder holding those particles to the plastic can absorb moisture and break down, which is
  the failure people call sticky shed. The tape squeals, sheds oxide onto the heads, and can jam. It
  is sometimes recoverable by careful baking before capture, and that is a job for someone who has
  done it before rather than an experiment on an irreplaceable tape.</p>
  <p>Then there is mechanical wear. Every playback drags the tape across the heads. Tapes that were
  watched to death in the nineties have visibly worse pictures than tapes that sat in a box, and that
  damage is physical abrasion rather than signal loss.</p>

  <h2>The faults you see, and whether software helps</h2>
  <table>
    <tr><th>Symptom</th><th>Cause</th><th>Fixable after capture?</th></tr>
    <tr><td>Soft, low-detail picture</td><td>Format limit plus particle decay</td><td>Partly. Upscaling genuinely helps here.</td></tr>
    <tr><td>Grainy speckle</td><td>Analogue noise floor</td><td>Yes, denoise handles it well.</td></tr>
    <tr><td>Comb teeth on movement</td><td>Interlacing</td><td>Yes, and it must be done first.</td></tr>
    <tr><td>Horizontal streaks and dropouts</td><td>Missing oxide, head clog</td><td>Barely. Fix at the deck.</td></tr>
    <tr><td>Picture tearing at the top</td><td>Tracking misalignment</td><td>No. Re-capture with tracking adjusted.</td></tr>
    <tr><td>Colour bleeding sideways</td><td>Very low chroma bandwidth</td><td>Partly, and never fully.</td></tr>
    <tr><td>Rolling or flagging</td><td>Timebase instability</td><td>No. Needs a timebase corrector at capture.</td></tr>
  </table>
  <p>The pattern is worth internalising. Anything caused by the signal being noisy or low-resolution
  responds to restoration. Anything caused by the signal never being read correctly in the first place
  has to be fixed at the deck, and no amount of processing invents it back.</p>

  <h2>The capture matters more than the software</h2>
  <p>This is the part people skip, and it costs them. A tape captured on a clean, well-aligned deck
  with a timebase corrector produces a file that restoration can genuinely improve. The same tape
  captured on a jammed thrift-store VCR through a cheap USB dongle produces a file with damage baked
  in that no tool can remove.</p>
  <p>If the tapes matter, it is worth finding a good deck or a transfer service, and worth capturing
  once at the highest quality you can rather than repeatedly. Every playback costs a little more of
  the tape.</p>

  <h2>Then the software order</h2>
  <p>Deinterlace, denoise, upscale, colour. Interlacing first is not a preference: an upscaler reads
  comb teeth as fine detail and sharpens them into something far harder to remove. Denoise before
  upscaling for the same reason, since magnified noise is a much bigger problem than the original.</p>
  <p>Crisp runs that chain on-device, which for family tapes tends to matter more than it sounds. The
  usual alternative involves uploading footage of your family to a service, and these are the tapes
  people are least willing to hand over.</p>
""",
 "faq": [
  ("Are my tapes still playable after 30 years?",
   "Usually yes, if they were stored somewhere cool and dry. Heat and humidity are what kill tapes, not age alone. The picture will be softer and noisier than it was, and that part responds well to restoration."),
  ("Should I digitise now or wait for better software?",
   "Now. The tape is degrading whether or not you use it, and software improves far faster than tape survives. Capture at the best quality you can manage today and restore the digital file whenever you like."),
  ("Why does my capture look worse than the tape did on the old TV?",
   "A CRT was hiding a lot. Its softness and the way it drew interlaced fields flattered analogue video, and a modern flat panel shows every fault sharply. The tape has not necessarily got worse; the display got more honest."),
  ("Can Crisp fix tracking lines and dropouts?",
   "No. Those are places where the signal was never read correctly, so there is nothing in the file to recover. They have to be addressed at capture, with a properly aligned deck and ideally a timebase corrector."),
 ],
},
{
 "slug": "learn/what-is-aspect-ratio",
 "crumb": "Aspect ratio",
 "title": "What is aspect ratio? 16:9, 9:16 and the black bars — Crisp",
 "h1": "What is aspect ratio?",
 "desc": "Why your footage gets black bars, why cropping to vertical loses half the frame, and the difference between letterboxing and actually reframing a shot.",
 "faq_heading": "Aspect ratio questions",
 "body": """
  <p>Aspect ratio is the shape of the frame: its width divided by its height. 16:9 is the widescreen
  shape almost all video uses. 9:16 is the same shape turned on its side, which is what phones shoot
  and what vertical feeds expect. 1:1 is square, 4:3 is the old television shape, and cinema uses
  wider ratios still such as 2.39:1.</p>
  <p>The number itself is simple. The consequences of changing it are where the difficulty lives.</p>

  <h2>Something has to give</h2>
  <p>A 16:9 frame cannot become a 9:16 frame without losing something. You have three options and they
  are all trade-offs.</p>
  <p><strong>Crop.</strong> Cut the sides off. You keep full resolution and lose about three quarters
  of the width. If your subject is centred this works well. If two people are talking on opposite
  sides of the frame, one of them is now gone.</p>
  <p><strong>Letterbox or pillarbox.</strong> Add bars to pad the frame to the new shape. Nothing is
  lost, the composition survives intact, and the picture is smaller on screen. Perfectly respectable,
  and often the right answer for something that was carefully framed.</p>
  <p><strong>Fill with a blurred background.</strong> Scale the original to fit the height, then fill
  the space either side with a blurred, enlarged copy of the same frame. It reads as deliberate rather
  than accidental, keeps the whole composition, and has become the default look on vertical feeds for
  good reason.</p>

  <h2>Reframing is a different thing entirely</h2>
  <p>Cropping picks one region and keeps it for the whole clip. Reframing follows the subject, moving
  the crop window as they move, so a person walking across a wide shot stays in the vertical frame
  throughout.</p>
  <p>That is much closer to what an editor would do by hand, and it is the difference between a
  vertical version that works and one where the subject drifts out of shot halfway through.</p>

  <h2>The mistakes worth avoiding</h2>
  <p><strong>Stretching.</strong> Squashing a 16:9 frame into a 9:16 box makes everyone look wrong in
  a way viewers notice without being able to name. Never do this. Crop, pad, or fill.</p>
  <p><strong>Cropping before you have finished editing.</strong> Once the sides are gone they are
  gone, and any later decision to reframe has nothing left to work with. Keep the full-frame master.</p>
  <p><strong>Baking bars into the master.</strong> Letterbox for a specific delivery, not in your
  archive copy, or a future crop will be cropping your own black bars.</p>
  <p><strong>Ignoring safe areas.</strong> Vertical feeds overlay captions, usernames and buttons over
  roughly the bottom fifth of the screen. Anything important down there will be covered.</p>

  <h2>Doing it on a Mac</h2>
  <p>Crisp handles all three approaches on-device and will pick a sensible default rather than making
  you specify one. Ask for a vertical version in plain English and you get the fill-and-blur treatment
  unless you say otherwise, because it is the option that loses nothing and reads as intentional.</p>
""",
 "faq": [
  ("Why does my video have black bars on the sides?",
   "The player is pillarboxing a narrower frame into a wider window rather than distorting it. That is correct behaviour. Bars top and bottom are the same thing in the other direction, usually a cinema-ratio frame in a 16:9 window."),
  ("Is cropping or blur-fill better for vertical?",
   "Crop when the subject is centred and there is nothing important at the edges, because you keep full resolution. Blur-fill when the composition matters or several things are happening across the width, because nothing is lost."),
  ("Does converting to vertical lose quality?",
   "Cropping keeps the pixels it keeps at full quality, so the result is lower resolution overall but not degraded. Blur-fill keeps the whole picture and scales it down slightly. Neither reduces quality the way a re-encode does."),
  ("What resolution should a vertical video be?",
   "1080 by 1920 covers essentially every vertical platform. Going higher rarely helps, since the platform will re-encode to its own ladder anyway, and it makes the upload slower for no visible gain."),
 ],
},

{
 "slug": "for/wedding-videographers",
 "section": "By use",
 "crumb": "Wedding videographers",
 "title": "Crisp for wedding videographers — offline finishing on a Mac",
 "h1": "Crisp for wedding videographers",
 "desc": "Reception footage shot at ISO 12800, a second camera that does not match, and client media you would rather not upload anywhere. What Crisp handles and what it does not.",
 "faq_heading": "Wedding work, in detail",
 "body": """
  <p>Wedding work has a shape no other genre quite shares. You get one take of everything, the light
  goes from a bright ceremony to a dark reception in a single day, half the footage comes from a
  camera you were not operating, and the client is emotionally invested in every frame in a way a
  corporate client never is.</p>

  <h2>The reception is where the footage falls apart</h2>
  <p>By the evening you are shooting at whatever ISO keeps the shutter usable, and that means noise.
  Not a little grain, but the coloured speckle in the shadows that compression then turns into
  blotches. Denoising before you grade rather than after makes a visible difference, because a grade
  applied to noisy footage amplifies the noise along with everything else.</p>
  <p>The other reception problem is handheld movement. Dancing shots, walking shots, anything grabbed
  quickly. Stabilization helps genuinely with shake, and it is worth knowing it cannot help with
  rolling shutter skew, which is what the wobble on fast pans usually is.</p>

  <h2>Two cameras that do not match</h2>
  <p>A second shooter, a locked-off camera at the back, and a phone clip someone sent you afterwards.
  Three sources, three colour renderings, three noise characteristics, and often three frame rates.</p>
  <p>Normalise before you cut, not after. Get everything to the same frame rate and the same colour
  range first, then grade. The alternative is a grade that looks right on the A camera and wrong every
  time you cut away, which is the sort of thing that is invisible while you work and obvious to a
  viewer.</p>
  <p>Phone footage is the frequent offender because it is often variable frame rate and often HDR.
  Both are handled on the way in rather than left for you to notice at the export stage.</p>

  <h2>The delivery problem nobody warns you about</h2>
  <p>You grade a film carefully, export it, and the couple watches it on a platform that re-encodes
  everything you sent. Gradients band, the dress goes blotchy in the highlights, and the grain you
  added reads as noise.</p>
  <p>The practical countermeasures are to clean the footage before delivery so the encoder spends its
  budget on faces rather than noise, and to deliver at a higher resolution than strictly needed,
  because platforms allocate bitrate by resolution. A 1080p film uploaded as 4K frequently survives
  better than the same film uploaded at 1080p.</p>

  <h2>Client media and where it goes</h2>
  <p>This is the part that matters more in this genre than most. Wedding footage is intimate, it
  includes children and elderly relatives, and couples increasingly ask where their files are being
  processed. Crisp runs everything on your Mac, with no upload, no account and no cloud step, which
  makes that an easy question to answer rather than an awkward one.</p>
  <p>It also means an overnight batch costs electricity rather than per-minute cloud billing, which
  matters when a wedding is three hundred gigabytes of source.</p>

  <h2>Where Crisp is the wrong tool</h2>
  <p>It is not an NLE. If you are cutting a full film with multicam sync, audio sweetening, music
  licensing and a client review round, that lives in Resolve or Premiere and should. Crisp is a
  finishing and repair tool: cleaning up the footage that needs help, fixing the clips that do not
  match, making the vertical cutdowns for socials, and handling the archive job on the couple's
  parents' old tapes.</p>
  <p>It also cannot rescue a shot that missed focus, recover a blown highlight on a white dress, or
  fix a ceremony where the audio was never recorded. Nothing can, and knowing that before you promise
  a fix is worth more than any feature.</p>
""",
 "faq": [
  ("Can Crisp match two cameras automatically?",
   "It normalises the technical side, frame rate, colour range and HDR, so both clips are in the same space before you grade. Matching the creative look of two different sensors is still a grading decision, and it is much easier once the technical differences are gone."),
  ("Will it fix noisy reception footage?",
   "Yes, that is one of the things on-device denoising genuinely does well, and doing it before grading rather than after makes a real difference. It cannot recover detail that was never captured in the very darkest areas."),
  ("Is client footage uploaded anywhere?",
   "No. Everything runs on your Mac. There is no upload endpoint, no account and no cloud processing step, which for wedding work tends to be the deciding factor rather than a nice-to-have."),
  ("Can it replace Premiere or Resolve for a full wedding film?",
   "No, and it does not try to. It has a timeline for assembling and cutting down, but a full film with multicam sync and audio work belongs in an NLE. Crisp is for the repair and finishing passes around that."),
 ],
},
{
 "slug": "for/teachers",
 "section": "By use",
 "crumb": "Teachers",
 "title": "Crisp for teachers and educators — offline video on a Mac",
 "h1": "Crisp for teachers and educators",
 "desc": "Lecture recordings that are too big to share, screen captures where the text went soft, and student footage that should not be uploaded to a third party.",
 "faq_heading": "Classroom video, in detail",
 "body": """
  <p>Teaching video has an unusual constraint: most of the tooling assumes you are making something
  polished for an audience of strangers, when what you actually need is something clear, quick to
  produce, and safe to share within an institution.</p>

  <h2>The four problems that come up constantly</h2>
  <p><strong>The file is too big to send.</strong> A one-hour lecture recording can be several
  gigabytes, and mail systems and LMS uploads reject it. Compression is the whole answer here, and it
  costs far less quality than people expect on screen-heavy content, because a static slide compresses
  extremely well.</p>
  <p><strong>The text in the screen recording is soft.</strong> This is usually not a resolution
  problem. Video stores colour at a quarter the detail of brightness, so coloured text on a
  contrasting background is the worst case for the format. Recording at a higher resolution helps more
  than raising the bitrate does.</p>
  <p><strong>The recording is an hour of which twelve minutes matter.</strong> Trimming before you do
  anything else is the single biggest time saver, both for you and for the student watching.</p>
  <p><strong>The audio is quiet in places.</strong> A lapel microphone that drifted, or a question from
  the back of the room. Levelling the quiet parts up rather than turning everything up is what makes
  a recording listenable on a laptop speaker.</p>

  <h2>Student footage and where it goes</h2>
  <p>This is the constraint that rules out most convenient tools. Footage containing identifiable
  students frequently cannot be uploaded to a third-party service, and the answer to "where is this
  processed" needs to be simple enough to put in an email to a head of department.</p>
  <p>Crisp processes everything on the machine. No upload, no account, nothing transmitted. That is a
  short answer to a question that otherwise involves reading somebody's terms of service.</p>

  <h2>A workflow that fits a prep period</h2>
  <p>Trim to what matters. Compress for the platform you are actually using. Level the audio. Export.
  Four steps, all of which can be asked for in plain English rather than found in a menu, which
  matters when the tool is used once a fortnight rather than daily.</p>
  <p>For lecture capture specifically, the compression step is the one worth learning. Slides and
  talking heads compress dramatically better than general footage, so you can often cut the file size
  by an order of magnitude with no visible difference on the screen a student will watch it on.</p>

  <h2>Where Crisp is the wrong tool</h2>
  <p>It does not record your screen, so you still want whatever capture tool you already use. It does
  not generate captions from speech, so accessibility captioning needs a dedicated service or your
  institution's system, and that is worth checking before you plan around it. And it is not a course
  authoring tool, so quizzes, chaptering and LMS packaging live elsewhere.</p>
  <p>What it does is take the raw recording you already have and make it smaller, shorter, clearer and
  easier to listen to, without any of it leaving your Mac.</p>
""",
 "faq": [
  ("Can Crisp generate captions from the audio?",
   "No. It burns in typed captions you provide, but it does not transcribe speech. If you need accessibility captions, use a transcription service or your institution's system and bring the text across."),
  ("How much can I compress a lecture recording?",
   "More than you would expect. Slides and a mostly static presenter compress extremely well, so an order-of-magnitude reduction with no visible difference is common. Footage with lots of movement will not shrink nearly as far."),
  ("Why is the text in my screen recording blurry?",
   "Chroma subsampling. Video stores colour at a quarter the resolution of brightness, and text is defined by a colour edge. Recording at a higher resolution gives the colour channel more samples and helps more than raising the bitrate."),
  ("Is student footage safe?",
   "It never leaves the machine. There is no upload endpoint and no account, so the answer to an institutional question about third-party processing is simply that there isn't any."),
 ],
},

{
 "slug": "for/product-video",
 "section": "By use",
 "crumb": "Product video",
 "title": "Crisp for product and e-commerce video on a Mac",
 "h1": "Crisp for product and e-commerce video",
 "desc": "A hundred listings that need the same treatment, vertical cutdowns for every platform, and footage that has to look consistent rather than cinematic.",
 "faq_heading": "Product video, in detail",
 "body": """
  <p>Product video has a different success criterion from almost everything else. Nobody is going to
  praise your shot selection. The video works if the item is clearly visible, the colour is accurate,
  the file loads fast, and the two hundred other listings look like they came from the same shop.</p>
  <p>Consistency and throughput, in other words, rather than craft.</p>

  <h2>The throughput problem</h2>
  <p>One product video is easy. A catalogue of them is a different job, and it is where most people
  lose their evenings. The same crop, the same grade, the same compression, applied identically, over
  and over.</p>
  <p>Batch processing is the whole answer, and it is worth structuring your shoot around it: shoot
  every item the same way, at the same distance, under the same light, so one recipe applies to all
  of them. Footage that varies shot to shot forces you back into per-item decisions, which is the
  cost you were trying to avoid.</p>

  <h2>Colour accuracy matters more here than anywhere</h2>
  <p>In most genres colour is taste. In e-commerce it is a returns problem. A jumper that photographs
  slightly warmer than it is generates a stream of complaints and refunds, and no amount of styling
  compensates for it.</p>
  <p>The practical measures are unglamorous. Shoot under consistent light rather than mixed daylight
  and tungsten. Include a reference in a test frame so you have something to check against. Grade to
  accurate rather than pleasing. And be aware that if your camera shoots HDR by default, footage will
  render differently across devices unless it is converted properly, which is a silent way to end up
  with inaccurate colour without ever making a colour decision.</p>

  <h2>One master, many shapes</h2>
  <p>The same product video usually needs to exist as 16:9 for the listing page, 9:16 for stories and
  short-form, and often 1:1 for a feed. Shoot wide enough to survive the crop, keep the full-frame
  master, and generate the shapes from it rather than shooting three times.</p>
  <p>For a centred product on a plain background, cropping is usually fine and keeps full resolution.
  For anything where the composition matters, filling the frame with a blurred background loses
  nothing and reads as deliberate.</p>

  <h2>File size is a conversion metric</h2>
  <p>Product video is frequently watched on a phone on a weak connection by someone deciding whether
  to buy. A file that takes four seconds to start is a file many people never watch. Compression is
  not a quality compromise here, it is part of the job, and product footage on a plain background
  compresses extremely well because most of the frame is not changing.</p>

  <h2>Where Crisp is the wrong tool</h2>
  <p>It does not remove backgrounds or generate cutouts, so if your workflow depends on isolating the
  product from its surroundings, that lives elsewhere. It does not do motion graphics, animated price
  overlays or template-driven branding. And it will not rescue a badly lit shot: no restoration
  recovers detail from a blown highlight on a glossy surface, which is the single most common product
  photography failure.</p>
  <p>What it does is take the footage you shot and make it consistent, correctly sized, correctly
  coloured, and small enough to load, in batches, without uploading a product line that has not
  launched yet to somebody else's server.</p>
""",
 "faq": [
  ("Can Crisp process a whole catalogue at once?",
   "Batch processing is part of the paid unlock, and it applies the same treatment across a set of clips. The practical constraint is your own shoot: a recipe only applies cleanly if the footage was captured consistently."),
  ("Does it remove backgrounds?",
   "No. There is no cutout or background-removal lane. If isolating the product is core to your workflow, that needs a different tool and Crisp handles the finishing afterwards."),
  ("How small should a product video be?",
   "Small enough to start almost instantly on a phone. Product footage on a plain background compresses far better than general video, so aggressive compression usually costs nothing visible and directly affects how many people watch it."),
  ("Will upscaling make an old product video usable?",
   "If it is soft because it is low resolution, yes, meaningfully. If it is soft because it missed focus or the highlights are blown, no. Those are not recoverable by any tool, and re-shooting is cheaper than the render time."),
 ],
},
{
 "slug": "for/musicians",
 "section": "By use",
 "crumb": "Musicians",
 "title": "Crisp for musicians — live footage and music video on a Mac",
 "h1": "Crisp for musicians",
 "desc": "Dark venue footage shot on phones, three angles of the same set that do not match, and a release deadline. The realistic version of what can be fixed.",
 "faq_heading": "Music footage, in detail",
 "body": """
  <p>Almost all music footage arrives with the same two problems: it was shot in a dark room, and it
  came from several phones held by people who were not thinking about your edit.</p>
  <p>Both are more fixable than they look, within limits worth knowing in advance.</p>

  <h2>Dark venues are a noise problem, not a brightness problem</h2>
  <p>The instinct is to brighten the footage. That usually makes it worse, because lifting the
  exposure lifts the sensor noise with it, and the noise in a dark venue is the dominant fault.</p>
  <p>The order that works is to clean the noise first, then lift, then grade. Doing it the other way
  bakes amplified noise into the picture before anything has a chance to remove it. Stage lighting also
  tends to produce heavily saturated colour that clips in one channel, most often red, and that part
  is genuinely unrecoverable rather than a grading challenge.</p>

  <h2>Several phones, one show</h2>
  <p>Audience footage is a gift and a nuisance. Different phones, different colour rendering,
  different frame rates, and often variable frame rate, which is why a multi-angle cut can drift out
  of sync with the audio partway through even when it started aligned.</p>
  <p>Normalise everything to a constant frame rate and the same colour range before you cut. The sync
  problem largely disappears, and the grade you apply to one angle stops looking wrong on the next.</p>
  <p>Use the board mix or a dedicated recorder for the audio and treat the phone audio as a sync
  reference only. No amount of processing turns a phone microphone in front of a PA into a usable
  music recording, and this is the single most common way a live video gets abandoned.</p>

  <h2>Short-form is the actual distribution</h2>
  <p>The full show video matters less than the thirty-second clips cut from it. That means vertical
  versions, and it means picking the moments where something visibly happens rather than the moments
  that sounded best.</p>
  <p>Shoot wide enough that a vertical crop still has the performer in it, keep the full-frame master,
  and generate the cutdowns from it. An auto-montage cut to the music is a reasonable starting point
  for a highlights reel, and it is a starting point rather than a finished edit.</p>

  <h2>Old footage from before phones were good</h2>
  <p>Plenty of bands have a box of tapes from a decade when video was terrible. That material responds
  well to restoration, because the faults are exactly the recoverable kind: low resolution, analogue
  noise, and interlacing. Deinterlace first, then denoise, then upscale, and it is worth the render
  time on the one show that mattered.</p>

  <h2>Where Crisp is the wrong tool</h2>
  <p>It does not touch your music. There is no mixing, mastering, pitch correction or stem separation,
  and it deliberately refuses to pretend it can isolate the music from a mixed soundtrack. It is not
  a multicam NLE either, so genuine multi-angle synced editing belongs in Resolve or Premiere.</p>
  <p>And it cannot make a phone recording of a PA sound like a board mix. That one is worth accepting
  early, because it decides whether the shoot is worth doing at all.</p>
 """,
 "faq": [
  ("Can Crisp fix audio recorded on a phone at a gig?",
   "It can level and clean it up, and it cannot make it sound like a proper recording. A phone microphone in front of a PA is clipping and compressing before the file even exists. Use a board feed or a recorder and keep the phone audio for sync."),
  ("Can it separate the music from the crowd noise?",
   "No, and it says so rather than trying. Stem separation is a different class of tool. Crisp handles overall level, background noise reduction and wind, not pulling one source out of a mix."),
  ("Why does my multi-angle cut drift out of sync?",
   "Almost always variable frame rate on the phone footage. The clip declares one rate and was recorded at a changing one, so video and audio drift apart as it plays. Converting to a constant frame rate before editing fixes it."),
  ("Is old tape footage of a show worth restoring?",
   "Usually yes. The faults on old live footage are the recoverable kind, low resolution, analogue noise and interlacing, and the results are often dramatic. Deinterlace before upscaling or the upscaler will sharpen the comb artefacts."),
 ],
},

{
 "slug": "for/genealogists",
 "section": "By use",
 "crumb": "Genealogists",
 "title": "Crisp for genealogists and family historians on a Mac",
 "h1": "Crisp for genealogists and family historians",
 "desc": "Boxes of tape and cine film, one copy of everything, and relatives who will not be there next year. What to do first, and what no software can recover.",
 "faq_heading": "Family archives, in detail",
 "body": """
  <p>Family history work has a deadline nobody sets. The tapes are decaying, the people who can
  identify who is in them are getting older, and there is exactly one copy of most of it.</p>
  <p>That changes the priorities. Restoration quality matters less than getting everything captured
  and identified while it is still possible.</p>

  <h2>Capture first, restore later</h2>
  <p>This is the single most useful thing to know. Magnetic tape loses signal whether or not anyone
  plays it, and every playback wears it slightly. Software gets better every year; a tape from 1987
  does not.</p>
  <p>So capture the whole collection at the best quality you can manage now, even if you have no time
  to restore any of it. A digital file sitting on two drives is safe. A tape in a loft is on a clock.
  Restoration can happen in ten years; capture frequently cannot.</p>
  <p>If a tape squeals or sheds powder, stop and get advice before playing it again. That is binder
  breakdown, and forcing it through a deck can destroy both the tape and the heads.</p>

  <h2>Identify while people still can</h2>
  <p>Sit down with the oldest relatives and record them watching the footage. Their commentary is
  frequently more valuable than the footage itself, and it is the part that genuinely cannot be
  recovered later. Names, places, dates, the year a house looked like that.</p>
  <p>Do this before restoration, not after. It needs no processing and it is the piece with a hard
  deadline attached.</p>

  <h2>Then the restoration, in order</h2>
  <p>Deinterlace, denoise, upscale, colour. That sequence matters more than any individual setting.
  Nearly all tape and broadcast material is interlaced, and an upscaler reads the comb pattern as fine
  detail and sharpens it into something much harder to remove. Denoise before upscaling for the same
  reason: magnified noise is a worse problem than the original.</p>
  <p>Be conservative with denoising on old film. Grain is part of how film looks, and stripping it out
  gives faces the waxy appearance that makes an over-restored archive obvious. You can always run a
  second pass; you cannot put the texture back.</p>

  <h2>What cannot be recovered</h2>
  <p>Worth knowing before you spend a weekend on it. Tracking tears, dropouts where the signal was
  never read, and timebase instability all have to be fixed at capture with a properly aligned deck,
  not afterwards in software. A shot that missed focus has no detail to recover, and an upscaler will
  invent plausible features rather than restore real ones, which on a face you are trying to identify
  is worse than leaving it soft.</p>
  <p>Blown highlights are gone. Audio that was never recorded is gone. Accepting that early saves the
  time better spent on capture.</p>

  <h2>Where Crisp is the wrong tool</h2>
  <p>It does not capture from tape, so you still need a deck, a capture device and ideally a timebase
  corrector. It does not catalogue, tag or manage metadata, which for a serious archive matters as
  much as the footage. And it does not transcribe speech, so the commentary you record still needs
  transcribing elsewhere.</p>
  <p>What it does is the restoration pass, on your own machine, on footage of your family that never
  goes to anyone else's server. For this particular use, that tends to be the point rather than a
  feature.</p>
""",
 "faq": [
  ("Should I restore before or after digitising everything?",
   "Digitise everything first, without exception. The tape is degrading on a clock and software only improves. A complete set of raw captures is far more valuable than a handful of beautifully restored clips and a box you never got to."),
  ("How much should I denoise old film?",
   "Less than feels right. Grain is part of the image, and heavy denoising produces the waxy, plastic faces that give an over-processed archive away. Remove enough that it reads cleanly and stop there."),
  ("Can Crisp fix tracking lines and dropouts?",
   "No. Those are places where the signal was never read, so there is nothing in the file to work from. They need a properly aligned deck and ideally a timebase corrector at capture time."),
  ("Is upscaling a face reliable for identification?",
   "Be careful here. An upscaler predicts plausible detail rather than recovering real detail, so a sharpened face is partly invented. For identification purposes the soft original is more honest evidence than the crisp reconstruction."),
 ],
},
{
 "slug": "for/filmmakers",
 "section": "By use",
 "crumb": "Filmmakers",
 "title": "Crisp for independent filmmakers on a Mac",
 "h1": "Crisp for independent filmmakers",
 "desc": "A finishing and repair tool that sits beside your NLE rather than replacing it. Where it earns its place on a low-budget shoot, and where it does not.",
 "faq_heading": "Film work, in detail",
 "body": """
  <p>Let's be direct about scope. If you are cutting a film, that happens in Resolve, Premiere or Final
  Cut, and it should. Crisp is not an NLE and pretending otherwise would waste your time.</p>
  <p>Where it earns a place is the unglamorous work around the edit, the shots that need rescuing and
  the deliverables nobody budgeted for.</p>

  <h2>The shot you cannot reshoot</h2>
  <p>Every low-budget production has a few. The location is gone, the actor has left, the light was
  never coming back. The shot is noisy, or soft, or shaky, and it has to be in the film.</p>
  <p>Denoising and stabilization are genuinely useful here, with an important caveat: they work on
  faults of degradation, not faults of capture. Sensor noise, yes. Camera shake, yes. Missed focus,
  no. Rolling shutter skew, no. Knowing which category a problem falls into before you start the
  render saves hours you do not have.</p>

  <h2>Archival and stock material</h2>
  <p>Period footage, home video inserts, public-domain archive, a clip from a source that only exists
  at 480p. This is where upscaling earns its keep, because the fault is genuinely low resolution
  rather than something invented.</p>
  <p>The rule is the same as everywhere: deinterlace first if it is broadcast or tape material, then
  denoise, then upscale. Interlaced material sharpened by an upscaler is much harder to fix than it
  was originally.</p>

  <h2>Deliverables nobody budgets for</h2>
  <p>Once the film is done there is a second job: the trailer, the vertical cutdowns for socials, the
  festival submission at a specific resolution, the compressed screener that has to be small enough to
  email, and the stills for the press kit. None of that is creative work, all of it takes time, and
  most of it is mechanical enough to describe in a sentence rather than build in a timeline.</p>
  <p>Pulling a full-resolution still from an exact frame is worth mentioning specifically, because
  screenshotting the player gives you the display-scaled version with the wrong colour, and press kits
  need the real frame.</p>

  <h2>Client and unreleased material</h2>
  <p>Everything runs on your machine. For work under embargo, under NDA, or simply not yet announced,
  that removes a conversation rather than starting one. It also means an overnight batch costs
  electricity rather than per-minute cloud billing, which matters at the scale a feature generates.</p>

  <h2>Where Crisp is the wrong tool</h2>
  <p>No multicam sync, no audio post, no conform, no colour-managed grading pipeline, no LUT import,
  no motion graphics, no round-tripping with your NLE. It does not replace any part of a professional
  finishing chain, and a film that needs those things needs the tools that do them.</p>
  <p>It also cannot invent a shot you did not get. The most valuable thing it offers a low-budget
  production is an honest answer about which problems are fixable, delivered before you spend the
  night rendering one that is not.</p>
""",
 "faq": [
  ("Can Crisp replace Resolve or Premiere?",
   "No, and it does not try. There is a timeline for assembling and cutting down, but no multicam sync, no audio post, no conform and no colour-managed grading pipeline. It is a repair and finishing tool that sits beside an NLE."),
  ("Does it support LUTs?",
   "No. It applies its own looks rather than importing .cube files, so if your grade depends on a specific LUT chain that work belongs in your NLE."),
  ("Is upscaled archive footage good enough to intercut with modern camera footage?",
   "Often yes, if the source is genuinely low-resolution rather than soft or damaged, and if you match grain and colour afterwards. Upscaled material that is too clean sits oddly next to real footage, so adding a little grain back usually helps it blend."),
  ("Can it pull a press still from an exact frame?",
   "Yes, at full resolution and at the exact timestamp, which is different from screenshotting a player. A screenshot gives you the display-scaled image with player colour management applied, which is not the frame you shot."),
 ],
},

{
 "slug": "for/churches",
 "section": "By use",
 "crumb": "Churches",
 "title": "Crisp for churches and places of worship on a Mac",
 "h1": "Crisp for churches and places of worship",
 "desc": "A service every week, volunteers running the camera, and an archive going back years. The realistic version of what helps and what does not.",
 "faq_heading": "Service recordings, in detail",
 "body": """
  <p>Church video has a shape almost no commercial workflow shares. There is a new recording every
  week whether anyone is ready or not, the person operating the camera is a volunteer who may be
  different from last week, and the archive goes back further than anybody planned for.</p>
  <p>That combination rewards workflows that are simple and repeatable far more than ones that are
  powerful.</p>

  <h2>The weekly job</h2>
  <p>Most of the work is the same four steps every time: trim the dead air at the start and end, level
  the audio so the sermon and the music are both audible, compress the file so it will upload before
  Tuesday, and cut two or three short clips for social.</p>
  <p>Being able to ask for those in plain English matters more here than in most settings, because the
  person doing it this week may not have done it last week. A workflow that needs remembering where a
  setting lives is a workflow that breaks the moment the usual volunteer is away.</p>

  <h2>Audio is the whole game</h2>
  <p>Congregations forgive a soft picture and will not forgive audio they cannot follow. The common
  faults are a speaker who moves off the microphone, a music segment far louder than the spoken word,
  and room noise from the back.</p>
  <p>Levelling the quiet parts up rather than raising everything is what makes a recording listenable
  on a phone speaker, which is how most of the congregation will actually watch it. Do that before
  compressing, not after.</p>
  <p>Take the feed from the sound desk if there is one. A camera microphone at the back of a room with
  a PA in it is fighting a losing battle, and no processing fixes that.</p>

  <h2>Low light and long lenses</h2>
  <p>Sanctuaries are usually darker than they look, and volunteers often shoot from the back on a long
  lens, which is the worst combination for both noise and shake. Denoise before any brightening, or
  you amplify the noise along with the picture. Stabilization helps genuine handheld movement; it will
  not fix the wobble from a long lens on a cheap tripod head, which is often rolling shutter rather
  than shake.</p>

  <h2>The archive nobody has time for</h2>
  <p>Most churches have a shelf of tapes and DVDs of anniversaries, weddings and funerals going back
  decades. That material is genuinely worth restoring, and it responds well, because the faults are
  the recoverable kind: low resolution, analogue noise, interlacing.</p>
  <p>Deinterlace first, then denoise, then upscale. Almost all of it will be interlaced, and an
  upscaler run first will sharpen the comb artefacts into something much harder to remove.</p>
  <p>Batch processing is the practical route for a shelf rather than a clip, and because everything
  runs on the machine there is no per-minute billing on a job that might run overnight.</p>

  <h2>Privacy is not an abstract concern here</h2>
  <p>Services include children, funerals, baptisms and people who did not choose to be filmed. Uploading
  that to a third-party service to process it is a conversation most churches would rather not have.
  Crisp runs entirely on the machine, with nothing transmitted, which makes the answer short.</p>

  <h2>Where Crisp is the wrong tool</h2>
  <p>It does not stream, so live broadcast needs whatever you already use. It does not generate
  captions from speech, which matters because accessibility is a real obligation for many
  congregations, and that needs a transcription service. It has no multicam sync, so a genuinely
  multi-camera edit belongs in an NLE. And it will not fix audio recorded on a camera microphone at
  the back of a hall.</p>
  <p>What it does is the weekly cleanup, the short clips, and the archive, without any of it leaving
  the building.</p>
""",
 "faq": [
  ("Can Crisp add captions to our service recordings?",
   "It burns in captions you have typed, but it does not transcribe speech. If captions are an accessibility requirement, you need a transcription service to produce the text first. That is worth checking before planning a workflow around it."),
  ("How do we make the sermon audible on a phone?",
   "Level the quiet parts up rather than raising the overall volume, and do it before compressing. Most of a congregation watches on a phone speaker, and levelling makes far more difference there than any picture improvement."),
  ("Is it practical to restore an archive of old service tapes?",
   "Yes, and it is one of the better uses for it. The faults on old tape are the recoverable kind. Work through it in batches, deinterlace before upscaling, and expect it to run overnight rather than in minutes."),
  ("Does any footage leave our machine?",
   "No. There is no upload, no account and no cloud step, which for recordings involving children and funerals is usually the deciding factor rather than a bonus."),
 ],
},
]
