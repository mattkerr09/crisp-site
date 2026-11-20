(function () {
  'use strict';
  const input = document.getElementById('fit-file');
  const destination = document.getElementById('fit-destination');
  const custom = document.getElementById('fit-custom');
  const customBox = document.getElementById('fit-custom-box');
  const result = document.getElementById('fit-result');
  let clip = null, reading = false, revision = 0;
  const mb = bytes => (bytes / 1000000).toLocaleString('en-US', { maximumFractionDigits: 6 }) + ' MB';
  function line(text) {
    const p = document.createElement('p');
    p.textContent = text;
    result.appendChild(p);
  }
  function answer() {
    customBox.hidden = destination.value !== 'custom';
    if (reading || !clip) return;
    result.replaceChildren();
    result.hidden = false;
    const { file, meta } = clip;
    line(file.name + ': ' + mb(file.size) + ', ' + CrispSizeBudget._say_length(meta.duration) + ', ' + meta.width + '×' + meta.height + ', ' + meta.audioTracks + ' audio track' + (meta.audioTracks === 1 ? '' : 's') + '.');
    const limit = CrispSizeBudget.destination_limit(destination.value, Number(custom.value));
    if (!(Number.isFinite(limit) && limit > 0 && limit <= 100000)) {
      line('Choose a size above 0 MB and at most 100000 MB.'); return;
    }
    const fits = file.size <= limit * 1000000;
    line('Your video is ' + mb(file.size) + '. The limit is ' + mb(limit * 1000000) + '. ' + (fits ? 'It is already at or under the size limit.' : 'It is over the size limit.'));
    if (destination.value === 'whatsapp') line('WhatsApp also has a 720p limit for video, and a 64 MB limit on slower connections. This answer checks the default 100 MB size limit.');
    if (fits && (destination.value !== 'email' || file.size <= 18000000)) return;
    if (fits) line('It is above the 18 MB email aim, which leaves room for base64 encoding.');
    let plan;
    try {
      plan = CrispSizeBudget.destination_budget(meta.duration, meta.width, meta.height, destination.value, Number(custom.value), meta.audioTracks);
    } catch (e) { line(e.message); return; }
    line('Crisp aims at ' + mb(plan.aim_bytes) + ' with a ' + plan.width + '×' + plan.height + ' picture at about ' + Math.round(plan.video_kbps).toLocaleString('en-US') + ' kbps.');
    line(plan.reason);
    if (meta.audioTracks) line('Sound gets ' + plan.audio_kbps + ' kbps per track.');
    line('This is a plan from the file details, not a measured export. Crisp checks the exported size and may lower the picture size or bitrate again.');
  }
  input.addEventListener('change', async () => {
    const current = ++revision, file = input.files && input.files[0];
    clip = null;
    reading = false;
    result.replaceChildren();
    result.hidden = !file;
    if (!file) return;
    reading = true;
    line('Reading file details...');
    let meta;
    try { meta = await CrispChecker.inspect(file, true); }
    catch (e) { meta = { error: 'This page could not read this file. Choose an MP4 or MOV video with a readable index.' }; }
    if (current !== revision) return;
    reading = false;
    result.replaceChildren();
    if (meta.error) { line(meta.error); return; }
    if (meta.noVideo) { line('This file has no picture track. Choose an MP4 or MOV video.'); return; }
    if (!(Number.isFinite(meta.duration) && meta.duration > 0)) { line("Crisp could not read the clip's length, so it cannot fit a size safely."); return; }
    if (!(meta.width >= 2 && meta.height >= 2 && Number.isInteger(meta.audioTracks))) { line("Crisp could not read the video's picture or audio tracks."); return; }
    if (meta.par) meta.width = Math.round(meta.width * meta.par);
    clip = { file, meta };
    answer();
  });
  destination.addEventListener('change', answer);
  custom.addEventListener('input', answer);
})();
