/* Crisp video checker. Reads a video's own description (resolution, frame rate, bitrate, codec, colour, scan) IN THIS PAGE.
   It never sends the file anywhere: there is no fetch, no form and no upload in this script. It reads small slices of the
   file the visitor picked (File.slice), so a multi-gigabyte home video costs a few megabytes of memory, not its size.
   Containers: MP4 / MOV / M4V (ISO boxes), MKV / WebM (EBML), AVI (RIFF), MPEG-1/2 program and transport streams (sequence
   header). Anything else: the size and length the browser's own video element can read, if it can play the file.
   The "what Crisp's Auto would do" line follows backend/crisp_engine/presets.py auto_plan (short side; 2x at 1600 and over;
   otherwise round(2160 / short side) clamped to 2..4, Python rounding; stronger noise clean-up at 720 and under). */
(function (root) {
  'use strict';

  async function dv(file, off, len) {
    const end = Math.min(file.size, off + len);
    return new DataView(await file.slice(off, end).arrayBuffer());
  }
  const cc = (d, o) => String.fromCharCode(d.getUint8(o), d.getUint8(o + 1), d.getUint8(o + 2), d.getUint8(o + 3));
  const u64 = (d, o) => d.getUint32(o) * 4294967296 + d.getUint32(o + 4);

  /* ---------- MP4 / MOV ---------- */
  function* kids(d, start, end) {
    let o = start;
    while (o + 8 <= end) {
      let size = d.getUint32(o), hdr = 8;
      const type = cc(d, o + 4);
      if (size === 1) { if (o + 16 > end) return; size = u64(d, o + 8); hdr = 16; } else if (size === 0) size = end - o;
      if (size < hdr || o + size > end) return;
      yield { type, o, body: o + hdr, end: o + size };
      o += size;
    }
  }
  const child = (d, b, type) => { for (const k of kids(d, b.body, b.end)) if (k.type === type) return k; return null; };
  const path = (d, b, ...types) => { let x = b; for (const t of types) { x = x && child(d, x, t); } return x; };

  const VCODEC = {
    avc1: 'H.264', avc3: 'H.264', hvc1: 'HEVC (H.265)', hev1: 'HEVC (H.265)', dvh1: 'HEVC (H.265), Dolby Vision', dvhe: 'HEVC (H.265), Dolby Vision',
    dva1: 'H.264, Dolby Vision', dvav: 'H.264, Dolby Vision', av01: 'AV1', vp09: 'VP9', vp08: 'VP8', mp4v: 'MPEG-4 Part 2', s263: 'H.263',
    apch: 'Apple ProRes 422 HQ', apcn: 'Apple ProRes 422', apcs: 'Apple ProRes 422 LT', apco: 'Apple ProRes 422 Proxy', ap4h: 'Apple ProRes 4444', ap4x: 'Apple ProRes 4444 XQ',
    jpeg: 'Motion JPEG', mjpa: 'Motion JPEG', mjpb: 'Motion JPEG', 'dvc ': 'DV', dvcp: 'DV (PAL)', dvpp: 'DVCPRO', dv5n: 'DVCPRO50', dv5p: 'DVCPRO50', mx5p: 'MPEG-2 (IMX)',
    xdv7: 'MPEG-2 (XDCAM HD)', xdvc: 'MPEG-2 (XDCAM HD)', hdv2: 'MPEG-2 (HDV)', hdv3: 'MPEG-2 (HDV)', mp2v: 'MPEG-2', 'raw ': 'Uncompressed', '2vuy': 'Uncompressed 4:2:2', v210: 'Uncompressed 10-bit 4:2:2',
    png: 'PNG frames', 'png ': 'PNG frames', rle: 'Animation (RLE)', 'rle ': 'Animation (RLE)', SVQ3: 'Sorenson Video 3', cvid: 'Cinepak'
  };
  const ACODEC = { mp4a: 'AAC', 'ac-3': 'Dolby Digital (AC-3)', 'ec-3': 'Dolby Digital Plus (E-AC-3)', alac: 'Apple Lossless', lpcm: 'PCM', sowt: 'PCM', twos: 'PCM', in24: 'PCM 24-bit', in32: 'PCM 32-bit', fl32: 'PCM float', Opus: 'Opus', fLaC: 'FLAC', '.mp3': 'MP3', ulaw: 'µ-law', alaw: 'A-law', ima4: 'IMA ADPCM', samr: 'AMR', sawb: 'AMR-WB', 'raw ': 'PCM' };

  function avcInfo(d, b) {
    const prof = { 66: 'Baseline', 77: 'Main', 88: 'Extended', 100: 'High', 110: 'High 10', 122: 'High 4:2:2', 244: 'High 4:4:4' }[d.getUint8(b.body + 1)] || ('profile ' + d.getUint8(b.body + 1));
    const out = { profile: prof + ' @ level ' + (d.getUint8(b.body + 3) / 10) };
    try {
      if ((d.getUint8(b.body + 5) & 31) < 1) return out;
      const len = d.getUint16(b.body + 6), raw = [];
      for (let i = 0; i < len; i++) raw.push(d.getUint8(b.body + 8 + i));
      Object.assign(out, parseSPS(raw));
    } catch (e) { /* a short or odd SPS: keep the profile */ }
    return out;
  }
  function parseSPS(raw) {
    const s = [];
    for (let i = 1; i < raw.length; i++) { if (i >= 3 && raw[i] === 3 && raw[i - 1] === 0 && raw[i - 2] === 0) continue; s.push(raw[i]); }
    let bit = 0;
    const u = n => { let v = 0; for (let i = 0; i < n; i++) { v = v * 2 + ((s[bit >> 3] >> (7 - (bit & 7))) & 1); bit++; if (bit > s.length * 8) throw new Error('sps'); } return v; };
    const ue = () => { let z = 0; while (u(1) === 0) { z++; if (z > 31) throw new Error('sps'); } return (2 ** z - 1) + (z ? u(z) : 0); };
    const se = () => { const k = ue(); return k & 1 ? (k + 1) / 2 : -k / 2; };
    const profile = u(8); u(8); u(8); ue();
    let chroma = 1, depth = 8;
    if ([100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135].includes(profile)) {
      chroma = ue(); if (chroma === 3) u(1);
      depth = ue() + 8; ue(); u(1);
      if (u(1)) {
        for (let i = 0; i < (chroma === 3 ? 12 : 8); i++) {
          if (u(1)) { let last = 8, next = 8; for (let j = 0; j < (i < 6 ? 16 : 64); j++) { if (next !== 0) next = (last + se() + 256) % 256; last = next === 0 ? last : next; } }
        }
      }
    }
    ue();
    const poc = ue();
    if (poc === 0) ue(); else if (poc === 1) { u(1); se(); se(); const n = ue(); for (let i = 0; i < n; i++) se(); }
    ue(); u(1); ue(); ue();
    const frameOnly = u(1);
    const out = { depth, chroma: ['4:0:0', '4:2:0', '4:2:2', '4:4:4'][chroma], interlaced: frameOnly === 0 };
    try {
      if (!frameOnly) u(1);
      u(1);
      if (u(1)) { ue(); ue(); ue(); ue(); }
      if (u(1)) {
        if (u(1)) { if (u(8) === 255) { u(16); u(16); } }
        if (u(1)) u(1);
        if (u(1)) { u(3); u(1); if (u(1)) { out.prim = u(8); out.trc = u(8); out.mtx = u(8); } }
      }
    } catch (e) { /* no colour description: leave it unstated */ }
    return out;
  }
  function hevcInfo(d, b) {
    const p = d.getUint8(b.body + 1) & 31;
    const name = { 1: 'Main', 2: 'Main 10', 3: 'Main Still Picture', 4: 'Range extensions' }[p] || ('profile ' + p);
    return { profile: name + ' @ level ' + (d.getUint8(b.body + 12) / 30), chroma: ['4:0:0', '4:2:0', '4:2:2', '4:4:4'][d.getUint8(b.body + 16) & 3], depth: (d.getUint8(b.body + 17) & 7) + 8 };
  }

  async function readMp4(file, top) {
    const moovBox = top.find(b => b.type === 'moov');
    if (!moovBox) return { error: 'This file has no index (no "moov" box). It may be cut short, still being written, or damaged.' };
    if (moovBox.size > 400 * 1024 * 1024) return { error: 'The index of this file is unusually large; the checker stops here to keep your browser responsive.' };
    const d = await dv(file, moovBox.off, moovBox.size);
    const moov = { body: moovBox.hdr, end: moovBox.size };
    const r = { container: top.some(b => b.type === 'ftyp') ? null : 'QuickTime MOV', tracks: [] };
    const ftyp = top.find(b => b.type === 'ftyp');
    if (ftyp) {
      const f = await dv(file, ftyp.off + 8, 4), brand = cc(f, 0);
      r.container = brand === 'qt  ' ? 'QuickTime MOV' : /^M4V/.test(brand) ? 'MPEG-4 (M4V)' : /^(3gp|3g2)/.test(brand) ? '3GPP' : 'MPEG-4 (MP4)';
    }
    const mvhd = child(d, moov, 'mvhd');
    if (mvhd) {
      const v = d.getUint8(mvhd.body), ts = d.getUint32(mvhd.body + (v ? 20 : 12)), du = v ? u64(d, mvhd.body + 24) : d.getUint32(mvhd.body + 16);
      if (ts) r.duration = du / ts;
    }
    r.fragmented = !!child(d, moov, 'mvex');
    for (const trak of kids(d, moov.body, moov.end)) {
      if (trak.type !== 'trak') continue;
      const t = {};
      const hdlr = path(d, trak, 'mdia', 'hdlr'); t.kind = hdlr ? cc(d, hdlr.body + 8) : '?';
      const mdhd = path(d, trak, 'mdia', 'mdhd');
      if (mdhd) { const v = d.getUint8(mdhd.body); t.ts = d.getUint32(mdhd.body + (v ? 20 : 12)); t.dur = v ? u64(d, mdhd.body + 24) : d.getUint32(mdhd.body + 16); }
      const tkhd = child(d, trak, 'tkhd');
      if (tkhd) {
        const v = d.getUint8(tkhd.body), m = tkhd.body + (v ? 52 : 40);
        const a = d.getInt32(m) / 65536, bb = d.getInt32(m + 4) / 65536;
        t.rotation = ((Math.round(Math.atan2(bb, a) * 180 / Math.PI) % 360) + 360) % 360;
        t.tkW = d.getUint32(m + 36) / 65536; t.tkH = d.getUint32(m + 40) / 65536;
      }
      const stbl = path(d, trak, 'mdia', 'minf', 'stbl');
      const stsd = stbl && child(d, stbl, 'stsd');
      if (stsd && d.getUint32(stsd.body + 4) > 0) {
        const e = stsd.body + 8, eEnd = e + d.getUint32(e);
        t.fourcc = cc(d, e + 4);
        if (t.kind === 'vide') {
          t.w = d.getUint16(e + 32); t.h = d.getUint16(e + 34);
          const entry = { body: e + 86, end: Math.min(eEnd, stsd.end) };
          for (const k of kids(d, entry.body, entry.end)) {
            if (k.type === 'avcC') { const a = avcInfo(d, k); for (const key in a) if (t[key] == null) t[key] = a[key]; }
            else if (k.type === 'hvcC') Object.assign(t, hevcInfo(d, k));
            else if (k.type === 'colr') {
              const kind = cc(d, k.body);
              if (kind === 'nclx' || kind === 'nclc') { t.prim = d.getUint16(k.body + 4); t.trc = d.getUint16(k.body + 6); t.mtx = d.getUint16(k.body + 8); }
            } else if (k.type === 'dvcC' || k.type === 'dvvC' || k.type === 'dvwC') { t.dv = (d.getUint8(k.body + 2) >> 1) & 127; t.dvCompat = d.getUint8(k.body + 4) >> 4; }
            else if (k.type === 'fiel') t.fields = d.getUint8(k.body);
            else if (k.type === 'pasp') { const hs = d.getUint32(k.body), vs = d.getUint32(k.body + 4); if (hs && vs && hs !== vs) t.par = hs / vs; }
            else if (k.type === 'vpcC') { t.depth = d.getUint8(k.body + 6) >> 4; t.prim = d.getUint8(k.body + 7); t.trc = d.getUint8(k.body + 8); }
            else if (k.type === 'av1C') { const b2 = d.getUint8(k.body + 2); t.depth = (b2 & 64) ? ((b2 & 32) ? 12 : 10) : 8; }
            else if (k.type === 'mdcv' || k.type === 'SmDm') t.mastering = true;
            else if (k.type === 'clli' || k.type === 'CoLL') t.cll = true;
          }
        } else if (t.kind === 'soun') {
          const ver = d.getUint16(e + 16);
          if (ver === 2) { t.rate = d.getFloat64(e + 40); t.ch = d.getUint32(e + 48); }
          else { t.ch = d.getUint16(e + 24); t.rate = d.getUint32(e + 32) / 65536; }
        }
      }
      if (stbl) {
        const stts = child(d, stbl, 'stts');
        if (stts) {
          const n = d.getUint32(stts.body + 4), runs = [];
          for (let i = 0; i < n && stts.body + 16 + i * 8 <= stts.end; i++) runs.push([d.getUint32(stts.body + 8 + i * 8), d.getUint32(stts.body + 12 + i * 8)]);
          t.runs = runs;
        }
        const stsz = child(d, stbl, 'stsz');
        if (stsz) {
          const one = d.getUint32(stsz.body + 4), n = d.getUint32(stsz.body + 8);
          let sum = 0;
          if (one) sum = one * n; else for (let i = 0; i < n && stsz.body + 16 + i * 4 <= stsz.end; i++) sum += d.getUint32(stsz.body + 12 + i * 4);
          t.samples = n; t.bytes = sum;
        }
      }
      r.tracks.push(t);
    }
    const v = r.tracks.find(t => t.kind === 'vide'), a = r.tracks.find(t => t.kind === 'soun');
    if (!v) return Object.assign(r, { noVideo: true });
    const out = { container: r.container, duration: r.duration || (v.ts ? v.dur / v.ts : 0), fragmented: r.fragmented };
    out.codedW = v.w; out.codedH = v.h;
    const rot = v.rotation === 90 || v.rotation === 270;
    out.width = rot ? v.h : v.w; out.height = rot ? v.w : v.h; out.rotation = v.rotation || 0;
    if (v.par) out.par = v.par;
    out.vcodec = VCODEC[v.fourcc] || VCODEC[v.fourcc && v.fourcc.trim()] || ('"' + v.fourcc + '"');
    out.profile = v.profile; out.depth = v.depth; out.chroma = v.chroma;
    out.prim = v.prim; out.trc = v.trc; out.dv = v.dv; out.dvCompat = v.dvCompat; out.mastering = v.mastering;
    out.interlaced = v.fields === 2 ? true : v.fields === 1 ? false : v.interlaced;
    if (v.runs && v.runs.length && v.ts) {
      let frames = 0, ticks = 0; const byDelta = new Map();
      v.runs.forEach(([c, dl]) => { frames += c; ticks += c * dl; byDelta.set(dl, (byDelta.get(dl) || 0) + c); });
      let mode = 0, modeN = -1; byDelta.forEach((c, dl) => { if (c > modeN && dl > 0) { mode = dl; modeN = c; } });
      out.frames = frames;
      out.fps = ticks ? frames * v.ts / ticks : 0;
      out.fpsMode = mode ? v.ts / mode : 0;
      let off = 0, lo = Infinity, hi = 0;
      byDelta.forEach((c, dl) => { if (!dl) return; if (Math.abs(dl - mode) / mode > 0.02) off += c; if (c >= 2 || byDelta.size <= 2) { lo = Math.min(lo, dl); hi = Math.max(hi, dl); } });
      out.variable = frames > 0 && off / frames > 0.01;
      if (out.variable) { out.fpsLow = v.ts / hi; out.fpsHigh = v.ts / lo; }
    }
    if (v.bytes && v.ts && v.dur) out.vbitrate = v.bytes * 8 / (v.dur / v.ts);
    if (a) out.audio = { codec: ACODEC[a.fourcc] || ('"' + a.fourcc + '"'), ch: a.ch, rate: a.rate };
    else out.audio = null;
    return out;
  }

  /* ---------- MKV / WebM ---------- */
  function vint(d, o, keepMarker) {
    const b = d.getUint8(o); let len = 1, mask = 0x80;
    while (len <= 8 && !(b & mask)) { len++; mask >>= 1; }
    if (len > 8) throw new Error('vint');
    let v = keepMarker ? b : (b & (mask - 1)), allOnes = (b & (mask - 1)) === mask - 1;
    for (let i = 1; i < len; i++) { const x = d.getUint8(o + i); v = v * 256 + x; if (x !== 255) allOnes = false; }
    return { v, len, unknown: !keepMarker && allOnes };
  }
  function* ebml(d, start, end) {
    let o = start;
    while (o < end - 1) {
      let id, sz;
      try { id = vint(d, o, true); sz = vint(d, o + id.len, false); } catch (e) { return; }
      const body = o + id.len + sz.len, stop = sz.unknown ? end : Math.min(end, body + sz.v);
      yield { id: id.v, body, end: stop, size: sz.v, unknown: sz.unknown };
      if (sz.unknown) return;
      o = body + sz.v;
    }
  }
  const uint = (d, e) => { let v = 0; for (let i = e.body; i < e.end; i++) v = v * 256 + d.getUint8(i); return v; };
  const flt = (d, e) => (e.end - e.body === 4 ? d.getFloat32(e.body) : e.end - e.body === 8 ? d.getFloat64(e.body) : 0);
  const str = (d, e) => { let s = ''; for (let i = e.body; i < e.end; i++) { const c = d.getUint8(i); if (!c) break; s += String.fromCharCode(c); } return s; };
  const MKV_V = { 'V_MPEG4/ISO/AVC': 'H.264', 'V_MPEGH/ISO/HEVC': 'HEVC (H.265)', V_VP9: 'VP9', V_VP8: 'VP8', V_AV1: 'AV1', V_MPEG2: 'MPEG-2', V_MPEG1: 'MPEG-1', V_PRORES: 'Apple ProRes', V_THEORA: 'Theora', 'V_MPEG4/ISO/ASP': 'MPEG-4 Part 2', 'V_MJPEG': 'Motion JPEG', 'V_MS/VFW/FOURCC': 'Video for Windows codec' };
  const MKV_A = { A_AAC: 'AAC', A_OPUS: 'Opus', A_VORBIS: 'Vorbis', A_AC3: 'Dolby Digital (AC-3)', A_EAC3: 'Dolby Digital Plus (E-AC-3)', A_FLAC: 'FLAC', A_DTS: 'DTS', 'A_MPEG/L3': 'MP3', 'A_PCM/INT/LIT': 'PCM', 'A_PCM/FLOAT/IEEE': 'PCM float', A_TRUEHD: 'Dolby TrueHD', A_ALAC: 'Apple Lossless' };

  async function readMkv(file) {
    let d = await dv(file, 0, 8 * 1024 * 1024);
    const out = { container: 'Matroska (MKV)' };
    let seg = null;
    for (const e of ebml(d, 0, d.byteLength)) {
      if (e.id === 0x1A45DFA3) { for (const k of ebml(d, e.body, e.end)) if (k.id === 0x4282 && str(d, k) === 'webm') out.container = 'WebM'; }
      if (e.id === 0x18538067) { seg = e; break; }
    }
    if (!seg) return { error: 'This Matroska file has no segment the checker can read.' };
    let info = null, tracks = null, seekTracks = null, seekInfo = null;
    for (const e of ebml(d, seg.body, seg.end)) {
      if (e.id === 0x1549A966) info = { d, e };
      else if (e.id === 0x1654AE6B) tracks = { d, e };
      else if (e.id === 0x114D9B74) {
        for (const s of ebml(d, e.body, e.end)) if (s.id === 0x4DBB) {
          let sid = 0, pos = 0;
          for (const k of ebml(d, s.body, s.end)) { if (k.id === 0x53AB) sid = uint(d, k); if (k.id === 0x53AC) pos = uint(d, k); }
          if (sid === 0x1654AE6B) seekTracks = pos; if (sid === 0x1549A966) seekInfo = pos;
        }
      } else if (e.id === 0x1F43B675) break;
    }
    async function at(pos) {
      const dd = await dv(file, seg.body + pos, 1024 * 1024);
      for (const e of ebml(dd, 0, dd.byteLength)) return { d: dd, e };
      return null;
    }
    if (!tracks && seekTracks != null) tracks = await at(seekTracks);
    if (!info && seekInfo != null) info = await at(seekInfo);
    if (info) {
      let scale = 1000000, du = 0;
      for (const k of ebml(info.d, info.e.body, info.e.end)) { if (k.id === 0x2AD7B1) scale = uint(info.d, k); if (k.id === 0x4489) du = flt(info.d, k); }
      out.duration = du * scale / 1e9;
    }
    if (!tracks) return Object.assign(out, { error: 'The track list of this file is not where the checker looked.' });
    const T = tracks.d;
    for (const te of ebml(T, tracks.e.body, tracks.e.end)) {
      if (te.id !== 0xAE) continue;
      let type = 0, codec = '', dd = 0, vid = null, aud = null;
      for (const k of ebml(T, te.body, te.end)) {
        if (k.id === 0x83) type = uint(T, k); else if (k.id === 0x86) codec = str(T, k); else if (k.id === 0x23E383) dd = uint(T, k);
        else if (k.id === 0xE0) vid = k; else if (k.id === 0xE1) aud = k;
      }
      if (type === 1 && !out.vcodec) {
        out.vcodec = MKV_V[codec] || codec;
        if (dd) out.fps = 1e9 / dd;
        if (vid) for (const k of ebml(T, vid.body, vid.end)) {
          if (k.id === 0xB0) out.width = out.codedW = uint(T, k);
          else if (k.id === 0xBA) out.height = out.codedH = uint(T, k);
          else if (k.id === 0x9A) { const f = uint(T, k); out.interlaced = f === 1 ? true : f === 2 ? false : undefined; }
          else if (k.id === 0x55B0) for (const c of ebml(T, k.body, k.end)) {
            if (c.id === 0x55B2) out.depth = uint(T, c); else if (c.id === 0x55BA) out.trc = uint(T, c); else if (c.id === 0x55BB) out.prim = uint(T, c); else if (c.id === 0x55D0) out.mastering = true;
          }
        }
      } else if (type === 2 && out.audio === undefined) {
        out.audio = { codec: MKV_A[codec] || codec };
        if (aud) for (const k of ebml(T, aud.body, aud.end)) { if (k.id === 0xB5) out.audio.rate = flt(T, k); if (k.id === 0x9F) out.audio.ch = uint(T, k); }
      }
    }
    if (out.audio === undefined) out.audio = null;
    if (!out.vcodec) out.noVideo = true;
    return out;
  }

  /* ---------- AVI ---------- */
  async function readAvi(file) {
    const d = await dv(file, 0, 256 * 1024);
    const le32 = o => d.getUint32(o, true), le16 = o => d.getUint16(o, true);
    const out = { container: 'AVI', audio: null };
    let usPerFrame = 0, total = 0, odmlTotal = 0, cur = null;
    const walk = (start, end) => {
      let o = start;
      while (o + 8 <= end) {
        const id = cc(d, o), size = le32(o + 4), body = o + 8;
        if (id === 'LIST' || id === 'RIFF') { const t = cc(d, body); if (t === 'movi') return; walk(body + 4, Math.min(end, body + size)); }
        else if (id === 'avih') { usPerFrame = le32(body); total = le32(body + 16); out.width = out.codedW = le32(body + 32); out.height = out.codedH = le32(body + 36); }
        else if (id === 'dmlh') odmlTotal = le32(body);
        else if (id === 'strh') { cur = cc(d, body); if (cur === 'vids') { const sc = le32(body + 20), rt = le32(body + 24); if (sc) out.fps = rt / sc; } }
        else if (id === 'strf' && cur === 'vids') { const fcc = cc(d, body + 16); out.vfourcc = fcc; out.vcodec = ({ dvsd: 'DV', DVSD: 'DV', dv25: 'DVCPRO', MJPG: 'Motion JPEG', mjpg: 'Motion JPEG', XVID: 'MPEG-4 Part 2 (Xvid)', xvid: 'MPEG-4 Part 2 (Xvid)', DIVX: 'MPEG-4 Part 2 (DivX)', DX50: 'MPEG-4 Part 2 (DivX)', H264: 'H.264', h264: 'H.264', avc1: 'H.264', HFYU: 'HuffYUV' })[fcc] || (fcc.charCodeAt(0) ? '"' + fcc + '"' : 'Uncompressed'); }
        else if (id === 'strf' && cur === 'auds' && !out.audio) { const tag = le16(body); out.audio = { codec: ({ 1: 'PCM', 85: 'MP3', 255: 'AAC', 8192: 'Dolby Digital (AC-3)', 2: 'MS ADPCM', 17: 'IMA ADPCM' })[tag] || ('format ' + tag), ch: le16(body + 2), rate: le32(body + 4) }; }
        o = body + size + (size & 1);
      }
    };
    walk(12, d.byteLength);
    if (!out.fps && usPerFrame) out.fps = 1e6 / usPerFrame;
    const frames = odmlTotal || total;
    if (frames && out.fps) { out.duration = frames / out.fps; out.frames = frames; }
    if (!out.vcodec && !out.width) return { error: 'This AVI file has no video header the checker can read.' };
    return out;
  }

  /* ---------- MPEG-1/2 program or transport stream: the video sequence header ---------- */
  async function readMpeg(file, kind) {
    const d = await dv(file, 0, 4 * 1024 * 1024);
    const n = d.byteLength;
    for (let i = 0; i + 12 < n; i++) {
      if (d.getUint8(i) !== 0 || d.getUint8(i + 1) !== 0 || d.getUint8(i + 2) !== 1 || d.getUint8(i + 3) !== 0xB3) continue;
      const b4 = d.getUint8(i + 4), b5 = d.getUint8(i + 5), b6 = d.getUint8(i + 6), b7 = d.getUint8(i + 7);
      const w = (b4 << 4) | (b5 >> 4), h = ((b5 & 15) << 8) | b6;
      const fps = [0, 24000 / 1001, 24, 25, 30000 / 1001, 30, 50, 60000 / 1001, 60][b7 & 15];
      const brv = (d.getUint8(i + 8) << 10) | (d.getUint8(i + 9) << 2) | (d.getUint8(i + 10) >> 6);
      const out = { container: kind, width: w, height: h, codedW: w, codedH: h, fps, declaredBitrate: brv === 0x3FFFF ? 0 : brv * 400, vcodec: 'MPEG-1', audio: undefined };
      for (let j = i + 12; j + 10 < Math.min(n, i + 400); j++) {
        if (d.getUint8(j) === 0 && d.getUint8(j + 1) === 0 && d.getUint8(j + 2) === 1 && d.getUint8(j + 3) === 0xB5 && (d.getUint8(j + 4) >> 4) === 1) {
          // sequence_extension: id(4) profile_level(8) progressive(1) chroma(2) h_ext(2) v_ext(2) bitrate_ext(12) marker(1) vbv_ext(8) low_delay(1) fr_n(2) fr_d(5)
          let bits = 0; for (let q = 0; q < 6; q++) bits = bits * 256 + d.getUint8(j + 4 + q);
          const at = (from, len) => Math.floor(bits / 2 ** (48 - from - len)) % 2 ** len;
          out.vcodec = 'MPEG-2'; out.interlaced = at(12, 1) === 0;
          const dar = { 2: 4 / 3, 3: 16 / 9, 4: 2.21 }[b7 >> 4];
          if (dar && w && h && Math.abs(dar * h / w - 1) > 0.01) out.par = dar * h / w;
          const frn = at(41, 2), frd = at(43, 5);
          if (out.fps) out.fps = out.fps * (frn + 1) / (frd + 1);
          break;
        }
      }
      return out;
    }
    return { error: 'No MPEG video header in the first 4 MB of this file. If it is AVCHD (.mts) from a camcorder, the checker cannot read it yet.' };
  }

  /* ---------- dispatch ---------- */
  async function inspect(file) {
    const head = await dv(file, 0, 16);
    if (head.byteLength < 12) return { error: 'This file is too small to be a video.' };
    const t4 = cc(head, 4), t0 = cc(head, 0);
    let r;
    if (['ftyp', 'moov', 'mdat', 'wide', 'free', 'skip', 'pnot', 'uuid'].includes(t4)) {
      const top = [];
      let off = 0;
      while (off + 8 <= file.size && top.length < 100000) {
        const h = await dv(file, off, 16);
        let size = h.getUint32(0), hdr = 8;
        if (size === 1) { size = u64(h, 8); hdr = 16; } else if (size === 0) size = file.size - off;
        if (size < hdr) break;
        top.push({ type: cc(h, 4), off, size, hdr });
        off += size;
      }
      r = await readMp4(file, top);
    } else if (head.getUint32(0) === 0x1A45DFA3) r = await readMkv(file);
    else if (t0 === 'RIFF' && cc(head, 8) === 'AVI ') r = await readAvi(file);
    else if (head.getUint32(0) === 0x000001BA || head.getUint32(0) === 0x000001B3) r = await readMpeg(file, 'MPEG program stream');
    else if (head.getUint8(0) === 0x47 || (head.getUint8(4) === 0x47)) r = await readMpeg(file, 'MPEG transport stream');
    else r = { error: 'unknown' };
    r.size = file.size;
    if (r.duration && !r.bitrate) r.bitrate = file.size * 8 / r.duration;
    return r;
  }

  /* ---------- words ---------- */
  function sizeName(w, h) {
    const s = Math.min(w, h), l = Math.max(w, h);
    if (s >= 4320 || l >= 7680) return '8K';
    if (s >= 2160 || l >= 3840) return '4K (UHD)';
    if (s >= 1440 || l >= 2560) return '1440p (QHD)';
    if (s >= 1080 || l >= 1920) return '1080p (Full HD)';
    if (s >= 720 || l >= 1280) return '720p (HD)';
    if (s >= 480) return 'standard definition (SD)';
    return 'below standard definition';
  }
  function pyRound(x) { const f = Math.floor(x), diff = x - f; if (diff > 0.5) return f + 1; if (diff < 0.5) return f; return f % 2 === 0 ? f : f + 1; }
  function crispAuto(w, h) {
    const s = Math.min(w, h);
    if (!s) return null;
    const scale = s >= 1600 ? 2 : Math.max(2, Math.min(4, pyRound(2160 / s)));
    return { scale, w: w * scale, h: h * scale, harder: s <= 720 && scale > 2, big: s >= 1600 };
  }
  function trcName(r) {
    if (r.dv != null) return 'HDR, Dolby Vision (profile ' + r.dv + (r.dvCompat ? '.' + r.dvCompat : '') + ')' + (r.trc === 18 ? ' over HLG' : r.trc === 16 ? ' over PQ' : '');
    if (r.trc === 16) return 'HDR10 (PQ)' + (r.mastering ? ', with mastering data' : '');
    if (r.trc === 18) return 'HDR (HLG)';
    const prim = { 1: 'BT.709', 5: 'BT.601 (PAL)', 6: 'BT.601 (NTSC)', 9: 'BT.2020', 12: 'Display P3' }[r.prim];
    if ((r.trc == null || r.trc === 2) && !prim) return null;
    return 'SDR' + (prim ? ', ' + prim + ' colour' : '');
  }
  const fmtNum = (x, p) => (Math.round(x * 10 ** p) / 10 ** p).toString();
  const fmtFps = f => { const near = [23.976, 24, 25, 29.97, 30, 48, 50, 59.94, 60, 120, 240].find(n => Math.abs(n - f) < 0.006); return near != null ? String(near) : fmtNum(f, 2); };
  const fmtRate = b => (b >= 1e6 ? fmtNum(b / 1e6, b >= 1e8 ? 0 : 1) + ' Mbps' : fmtNum(b / 1e3, 0) + ' kbps');
  const fmtSize = n => (n >= 1e9 ? fmtNum(n / 1e9, 2) + ' GB' : n >= 1e6 ? fmtNum(n / 1e6, 1) + ' MB' : fmtNum(n / 1e3, 0) + ' KB');
  function fmtDur(s) { s = Math.round(s); const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = s % 60; return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(x).padStart(2, '0'); }

  function rows(r) {
    const out = [];
    out.push(['Container', r.container + (r.fragmented ? ' (fragmented)' : '')]);
    if (r.width && r.height) {
      let res = r.width + ' × ' + r.height + ', ' + sizeName(r.width, r.height);
      if (r.rotation === 90 || r.rotation === 270) res += '. Stored as ' + r.codedW + ' × ' + r.codedH + ' and turned upright when it plays, which is how phones save portrait video.';
      if (r.par) res += '. Pixels are not square (' + fmtNum(r.par, 3) + ':1), so it plays ' + Math.round(r.width * r.par) + ' wide.';
      out.push(['Resolution', res]);
    }
    if (r.fps) {
      let f = fmtFps(r.fps) + ' fps';
      if (r.variable) f = 'Variable: between ' + fmtFps(r.fpsLow) + ' and ' + fmtFps(r.fpsHigh) + ' fps, ' + fmtFps(r.fps) + ' on average. Editors can drift out of sync with files like this.';
      else if (r.fpsMode && Math.abs(r.fpsMode - r.fps) / r.fps > 0.005) f = fmtFps(r.fpsMode) + ' fps (' + fmtFps(r.fps) + ' on average)';
      out.push(['Frame rate', f]);
    } else out.push(['Frame rate', 'Not stated in the file']);
    if (r.duration) out.push(['Length', fmtDur(r.duration) + (r.frames ? ' (' + r.frames.toLocaleString('en-US') + ' frames)' : '')]);
    out.push(['File size', fmtSize(r.size)]);
    if (r.duration) out.push(['Bitrate', fmtRate(r.bitrate) + ' overall' + (r.vbitrate ? ', of which the picture is ' + fmtRate(r.vbitrate) : '')]);
    else if (r.declaredBitrate) out.push(['Bitrate', 'about ' + fmtRate(r.declaredBitrate) + ' (the most the file says it uses)']);
    if (r.vcodec) out.push(['Video codec', r.vcodec + (r.profile ? ', ' + r.profile : '') + (r.depth ? ', ' + r.depth + '-bit' : '') + (r.chroma && r.chroma !== '4:2:0' ? ' ' + r.chroma : '')]);
    const c = trcName(r); if (c) out.push(['Colour', c]);
    out.push(['Scan', r.interlaced === true ? 'Interlaced (two half-pictures per frame; moving edges show comb lines on a computer screen)' : r.interlaced === false ? 'Progressive (whole frames)' : 'Not stated in the file']);
    out.push(['Sound', r.audio ? r.audio.codec + (r.audio.ch ? ', ' + (r.audio.ch === 1 ? 'mono' : r.audio.ch === 2 ? 'stereo' : r.audio.ch + ' channels') : '') + (r.audio.rate ? ', ' + fmtNum(r.audio.rate / 1000, 1) + ' kHz' : '') : r.audio === null ? 'No sound track' : 'Not read by the checker']);
    return out;
  }
  function verdict(r) {
    if (!(r.width && r.height)) return null;
    const W = r.par ? Math.round(r.width * r.par) : r.width;
    const a = crispAuto(W, r.height);
    if (a.big) return 'This is already ' + sizeName(r.width, r.height) + '. Enlarging it will not add much you can see. If it looks noisy, cleaning it up at its own size is the better job.';
    let s = 'Crisp’s Auto setting would enlarge this ' + a.scale + '×, to ' + a.w + ' × ' + a.h;
    s += a.harder ? ', and clean it up harder, because clips this small are usually heavily compressed.' : '.';
    if (r.interlaced) s += ' It rebuilds whole frames from the two half-pictures first.';
    if (r.trc === 16 || r.trc === 18 || r.dv != null) s += ' This is HDR: Crisp turns it into ordinary (SDR) colour before it enlarges it, so the result looks right on any screen but is no longer HDR.';
    return s;
  }

  const api = { inspect, rows, verdict, crispAuto, sizeName };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.CrispChecker = api;

  /* ---------- the page ---------- */
  if (typeof document === 'undefined') return;
  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  async function fallback(file) {
    return new Promise(res => {
      const v = document.createElement('video'), url = URL.createObjectURL(file);
      const done = r => { URL.revokeObjectURL(url); res(r); };
      v.preload = 'metadata'; v.muted = true;
      v.onloadedmetadata = () => done({ container: 'read by your browser', width: v.videoWidth, height: v.videoHeight, codedW: v.videoWidth, codedH: v.videoHeight, duration: isFinite(v.duration) ? v.duration : 0, partial: true });
      v.onerror = () => done(null);
      setTimeout(() => done(null), 8000);
      v.src = url;
    });
  }
  async function show(file) {
    const box = document.getElementById('vc-result');
    box.textContent = ''; box.hidden = false;
    box.appendChild(el('p', 'vc-reading', 'Reading ' + file.name + '…'));
    let r;
    try { r = await inspect(file); } catch (e) { r = { error: 'unknown' }; }
    if (r.error === 'unknown') {
      const f = await fallback(file);
      r = f ? Object.assign(f, { size: file.size, bitrate: f.duration ? file.size * 8 / f.duration : 0, audio: undefined }) : { error: 'The checker cannot read this kind of file, and your browser cannot play it either. On a Mac, QuickTime Player’s Movie Inspector (below) may.' , size: file.size };
    }
    box.textContent = '';
    const title = el('p', 'vc-name'); title.appendChild(el('strong', null, file.name)); box.appendChild(title);
    if (r.error) { box.appendChild(el('p', 'vc-error', r.error)); return; }
    if (r.noVideo) { box.appendChild(el('p', 'vc-error', 'This file has no picture track (it may be sound only).')); return; }
    const t = el('table', 'vc-table'), tb = el('tbody');
    rows(r).forEach(([k, v]) => { const tr = el('tr'); tr.appendChild(el('th', null, k)); tr.appendChild(el('td', null, v)); tb.appendChild(tr); });
    t.appendChild(tb); box.appendChild(t);
    if (r.partial) box.appendChild(el('p', 'vc-note', 'Only the size and length could be read for this kind of file.'));
    const v = verdict(r);
    if (v) { const p = el('p', 'vc-verdict'); p.appendChild(el('strong', null, 'What Crisp would do: ')); p.appendChild(document.createTextNode(v)); box.appendChild(p); }
  }
  function init() {
    const input = document.getElementById('vc-file'), drop = document.getElementById('vc-drop');
    if (!input || !drop) return;
    input.addEventListener('change', () => { if (input.files && input.files[0]) show(input.files[0]); });
    ['dragenter', 'dragover'].forEach(n => drop.addEventListener(n, e => { e.preventDefault(); drop.classList.add('vc-over'); }));
    ['dragleave', 'drop'].forEach(n => drop.addEventListener(n, () => drop.classList.remove('vc-over')));
    drop.addEventListener('drop', e => { e.preventDefault(); const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]; if (f) show(f); });
    window.addEventListener('dragover', e => e.preventDefault());
    window.addEventListener('drop', e => e.preventDefault());
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})(typeof window !== 'undefined' ? window : globalThis);
