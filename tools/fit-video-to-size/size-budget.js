(function (root) {
  'use strict';

  const _SIZE_LADDER = [1080, 720, 540, 480, 360];
  function pyRound(x) {
    const f = Math.floor(x), d = x - f;
    return d < 0.5 ? f : d > 0.5 ? f + 1 : f % 2 === 0 ? f : f + 1;
  }
  function general(x) {
    if (x === 0) return '0';
    const data = new DataView(new ArrayBuffer(8));
    data.setFloat64(0, x);
    const bits = data.getBigUint64(0), encoded = Number((bits >> 52n) & 2047n);
    let n = bits & ((1n << 52n) - 1n), d = 1n;
    if (encoded) n += 1n << 52n;
    const shift = encoded ? encoded - 1023 - 52 : -1074;
    if (shift >= 0) n <<= BigInt(shift); else d <<= BigInt(-shift);
    let e = Number(x.toExponential().split('e')[1]);
    const places = 5 - e;
    if (places >= 0) n *= 10n ** BigInt(places); else d *= 10n ** BigInt(-places);
    let q = n / d;
    const remainder = n % d;
    if (remainder * 2n > d || (remainder * 2n === d && q % 2n)) q++;
    if (q === 1000000n) { q /= 10n; e++; }
    const digits = q.toString().padStart(6, '0');
    if (e < -4 || e >= 6) {
      const tail = digits.slice(1).replace(/0+$/, '');
      return digits[0] + (tail ? '.' + tail : '') + 'e' + (e < 0 ? '-' : '+') + String(Math.abs(e)).padStart(2, '0');
    }
    const point = e + 1;
    const text = point <= 0 ? '0.' + '0'.repeat(-point) + digits : digits.slice(0, point) + (point < 6 ? '.' + digits.slice(point) : '');
    return text.includes('.') ? text.replace(/0+$/, '').replace(/\.$/, '') : text;
  }
  function _min_kbps(width, height) {
    const px = Math.max(1, Math.trunc(width) * Math.trunc(height));
    return Math.max(100, pyRound(400 * px / (1920 * 1080)));
  }
  function downscale_dims(width, height, res) {
    const w = Math.trunc(width || 0), h = Math.trunc(height || 0);
    if (!res || w < 2 || h < 2 || Math.trunc(res) >= Math.min(w, h)) return null;
    const s = Math.trunc(res) / Math.min(w, h);
    const even = v => Math.max(2, pyRound(v / 2.0) * 2);
    return [even(w * s), even(h * s)];
  }
  function _size_options(width, height) {
    const sizes = [[width - width % 2, height - height % 2]];
    for (const res of _SIZE_LADDER) {
      const dims = downscale_dims(width, height, res);
      if (dims && !sizes.some(([w, h]) => w === dims[0] && h === dims[1])) sizes.push(dims);
    }
    return sizes;
  }
  function _say_length(seconds) {
    const s = Math.max(1, pyRound(seconds)), m = Math.floor(s / 60), r = s % 60;
    if (!m) return r + ' second' + (r !== 1 ? 's' : '');
    const out = m + ' minute' + (m !== 1 ? 's' : '');
    return out + (r ? ' ' + r + ' second' + (r !== 1 ? 's' : '') : '');
  }
  function size_budget(duration, width, height, target_mb, audio_tracks = 0) {
    if (!Number.isFinite(target_mb) || !(0 < target_mb && target_mb <= 100000)) {
      throw new Error('Choose a size above 0 MB and at most 100000 MB.');
    }
    if (!Number.isFinite(duration) || duration <= 0) {
      throw new Error("Crisp could not read the clip's length, so it cannot fit a size safely.");
    }
    if (width < 2 || height < 2 || audio_tracks < 0) {
      throw new Error("Crisp could not read the video's picture or audio tracks.");
    }
    const aim_bytes = Math.trunc(target_mb * 1000000 * 0.95);
    const total_kbps = aim_bytes * 8 / 1000 / duration;
    let audio_kbps = audio_tracks ? 96 : 0;
    if (audio_tracks && (total_kbps < _min_kbps(width, height) + 96 * audio_tracks || total_kbps < 96 * audio_tracks * 3)) audio_kbps = 64;
    const video_kbps = total_kbps - audio_kbps * audio_tracks;
    const sizes = _size_options(width, height);
    const chosen = sizes.find(([w, h]) => video_kbps >= _min_kbps(w, h));
    if (!chosen) {
      const [w, h] = sizes[sizes.length - 1], floor = _min_kbps(w, h);
      const max_seconds = aim_bytes * 8 / 1000 / (floor + audio_kbps * audio_tracks);
      const parts = max_seconds > 0 ? Math.max(2, Math.ceil(duration / max_seconds)) : null;
      const length = _say_length(duration);
      const sound = audio_tracks ? ' once the sound takes its ' + audio_kbps * audio_tracks + ' kbps' : '';
      const picture = video_kbps > 0 ? 'leaves ' + pyRound(video_kbps) + ' kbps for the picture' + sound + ', below the ' + floor + ' kbps that ' + Math.min(w, h) + 'p needs' : 'leaves no room for the picture' + sound;
      const split = parts && parts <= 10 ? 'Split it into ' + parts + ' parts of about ' + _say_length(duration / parts) + ' each, or share a link.' : 'That size is too small for a video this long. Choose a larger size, or share a link.';
      throw new Error(length[0].toUpperCase() + length.slice(1) + ' of video in ' + general(target_mb) + ' MB ' + picture + '. Crisp aims at ' + general(aim_bytes / 1000000) + ' MB to stay under it. ' + split);
    }
    const [w, h] = chosen;
    const reason = w !== sizes[0][0] || h !== sizes[0][1] ? 'Chose ' + w + '×' + h + ' because the picture budget of ' + pyRound(video_kbps) + ' kbps is below what ' + width + '×' + height + ' needs.' : 'Kept ' + w + '×' + h + ' because the picture budget fits.';
    return { aim_bytes, aim_mb: aim_bytes / 1000000, video_kbps, audio_kbps, width: w, height: h, reason };
  }

  function destination_limit(destination, custom) {
    return { discord: 20, basic: 50, email: 25, whatsapp: 100, slack: 1000, custom }[destination];
  }
  function destination_budget(duration, width, height, destination, custom, tracks) {
    const limit = destination_limit(destination, custom);
    const target = destination === 'email' ? 18 / 0.95 : limit;
    return { limit, ...size_budget(duration, width, height, target, tracks) };
  }
  const api = { size_budget, _min_kbps, downscale_dims, _size_options, _SIZE_LADDER, _say_length, destination_budget, destination_limit };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CrispSizeBudget = api;
})(typeof window !== 'undefined' ? window : globalThis);
