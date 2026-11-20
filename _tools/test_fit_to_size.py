#!/usr/bin/env python3
"""Offline parity with the app's actual Python source, plus file and page regressions."""
from __future__ import annotations

import ast
import itertools
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys

from faq_jsonld import visible_faq
from schema_matches_page import text_of

SITE = Path(__file__).resolve().parent.parent
TOOL = SITE / 'tools/fit-video-to-size'
BACKEND = SITE.parent / 'backend'
ORIGINAL = BACKEND / 'crisp_engine/compress.py'
DESTINATIONS = [('discord', 20), ('basic', 50), ('email', 18 / 0.95),
                ('whatsapp', 100), ('slack', 1000), ('custom', 25)]


def run_node(code, payload=None):
    return subprocess.run(['node', '-e', code], input=json.dumps(payload), text=True,
                          capture_output=True, check=True, cwd=SITE).stdout


def original_functions():
    assert shutil.which('node'), 'FAIL: node is required; arithmetic parity must not be skipped'
    assert ORIGINAL.is_file(), f'FAIL: ../backend is required: {ORIGINAL}'
    # Compile only the requested pure code from the real source. No app imports, encoders or sound.
    tree = ast.parse(ORIGINAL.read_text())
    names = {'size_budget', '_min_kbps', 'downscale_dims', '_size_options', '_SIZE_LADDER',
             '_say_length', '_MIN_KBPS_1080P', '_MIN_KBPS_ABS',
             # 2026-11-20: size_budget now takes its aim from these (the email preset's 18 MB aim).
             'size_aim_bytes', 'DESTINATION_LIMITS_MB'}
    body = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in names)
            or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets))]
    env = {'math': math}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(ORIGINAL), 'exec'), env)
    assert names <= env.keys(), 'FAIL: original pure functions changed; update the port and test'
    return env


def outcome(fn, args):
    try:
        return {'value': fn(*args)}
    except ValueError as error:
        return {'error': str(error)}


def arithmetic(env):
    dimensions = [(640, 360), (854, 480), (960, 540), (1280, 720), (1920, 1080),
                  (2560, 1440), (3840, 2160), (641, 481)]
    dimensions += [(h, w) for w, h in dimensions]
    grid = [[duration, w, h, target, tracks, key]
            for duration, (w, h), tracks, (key, target) in itertools.product(
                range(5, 1801, 5), dimensions, range(3), DESTINATIONS)]
    # All validation errors, audio starvation, >10-part refusal, split advice and Python ties.
    extra = [[d, w, h, mb, tracks, None] for d, w, h, mb, tracks in [
        (0, 1920, 1080, 20, 1), (-1, 1920, 1080, 20, 1),
        ('NaN', 1920, 1080, 20, 1), ('Infinity', 1920, 1080, 20, 1),
        (120, 1, 1080, 20, 1), (120, 1920, 0, 20, 1), (120, 1920, 1080, 20, -1),
        (120, 1920, 1080, 0, 1), (120, 1920, 1080, -1, 1),
        (120, 1920, 1080, 100001, 1), (120, 1920, 1080, 'NaN', 1),
        (120, 1920, 1080, 'Infinity', 1), (1800, 3840, 2160, 0.001, 2),
        (1800, 3840, 2160, 1, 0), (600, 1920, 1080, 1, 2),
        (120.5, 1920, 1080, 0.001234567, 0), (59.5, 1920, 1080, 0.1, 2),
        (60.5, 1920, 1080, 0.01, 2), (120, 1920, 1080, 100000, 0),
        (5, 641, 481, 0.0000001, 0), (120, 1920, 1080, 1.234565, 1),
        (1800, 1920, 1080, 1.015625, 1), (1800, 1920, 1080, 1.046875, 1)]]
    cases = grid + extra
    code = r'''
const a = require('./tools/fit-video-to-size/size-budget.js');
const cases = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
const special = x => typeof x === 'string' ? Number(x) : x;
const out = cases.map(([d,w,h,mb,n,key]) => {
  try {
    const value = key ? a.destination_budget(special(d),w,h,key,25,n) : a.size_budget(special(d),w,h,special(mb),n);
    if (key) delete value.limit;
    return {value};
  } catch(e) { return {error: e.message}; }
});
process.stdout.write(JSON.stringify(out));
'''
    got = json.loads(run_node(code, cases))
    errors = 0
    assert len(cases) == len(got), 'Node returned an incomplete grid'
    for case, actual in zip(cases, got):
        args = [float(v) if isinstance(v, str) else v for v in case[:5]]
        expected = outcome(env['size_budget'], args)
        assert actual == expected, f'Python/JS mismatch for {case}:\n{expected}\n{actual}'
        errors += 'error' in expected
    helpers = {'dimensions': dimensions + [(1921, 1081), (1923, 1080), (3, 2), (1, 0)],
               'seconds': [0, 0.5, 1, 1.5, 2.5, 59.5, 60.5, 90.5, 120.5, 1800],
               'resolutions': [None, 0, 360, 480, 540, 720, 1080, 1440, 2160]}
    helper_got = json.loads(run_node(r'''
const a = require('./tools/fit-video-to-size/size-budget.js');
const x = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify({ladder:a._SIZE_LADDER,
  lengths:x.seconds.map(a._say_length),
  sizes:x.dimensions.map(([w,h]) => a._size_options(w,h)),
  floors:x.dimensions.map(([w,h]) => a._min_kbps(w,h)),
  scaled:x.dimensions.map(([w,h]) => x.resolutions.map(r => a.downscale_dims(w,h,r)))}));
''', helpers))
    expected_helpers = dict(ladder=list(env['_SIZE_LADDER']),
        lengths=[env['_say_length'](s) for s in helpers['seconds']],
        sizes=[env['_size_options'](*d) for d in helpers['dimensions']],
        floors=[env['_min_kbps'](*d) for d in helpers['dimensions']],
        scaled=[[env['downscale_dims'](*d, r) for r in helpers['resolutions']] for d in helpers['dimensions']])
    assert helper_got == json.loads(json.dumps(expected_helpers)), 'helper arithmetic differs from Python'
    print(f'fit-to-size: {len(grid):,} grid cases + {len(extra)} error/boundary cases match Python exactly; '
          f'{errors:,} exact error sentences; all six helpers match')


def page_checks():
    page = (TOOL / 'index.html').read_text()
    options = re.findall(r'<option value="([^"]+)"([^>]*)>(.*?)</option>', page)
    expected = [('discord', '20', None), ('basic', '50', None), ('email', '25', '18'),
                ('whatsapp', '100', None), ('slack', '1000', None), ('custom', None, None)]
    assert len(options) == len(expected)
    for (key, attrs, label), (want, limit, aim) in zip(options, expected):
        assert key == want
        attr = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
        assert attr.get('data-limit-mb') == limit and attr.get('data-aim-mb') == aim
    sources = re.search(r'<ul class="fit-sources">(.*?)</ul>', page, re.S).group(1)
    rows = re.findall(r'<li>(.*?)</li>', sources, re.S)
    assert len(rows) == 5
    urls = [
        ['https://support.discord.com/hc/en-us/articles/25444343291031-File-Attachments-FAQ'],
        ['https://support.discord.com/hc/en-us/articles/25444343291031-File-Attachments-FAQ'],
        ['https://support.google.com/mail/answer/6584', 'https://support.microsoft.com/en-us/outlook/sending-limits-in-outlook-com'],
        ['https://faq.whatsapp.com/453914586839706/'],
        ['https://slack.com/help/articles/201330736-Add-files-to-Slack']]
    quotes = [
        ['For non-Nitro subscribers, the maximum file upload is 20MB.'],
        ['Nitro Basic offers 50MB and Nitro offers up to 1GB.'],
        ['For personal Gmail accounts, the limit is 25 MB.', 'The attachment size limit for files is 25 MB.'],
        ['the default video size limit is 100MB and 720p resolution'],
        ['Members and guests can add files up to 1GB in size.']]
    for row, links, words in zip(rows, urls, quotes):
        assert re.findall(r'href="([^"]+)"', row) == links
        assert row.count('read 20 Nov 2026') == len(links)
        assert re.findall(r'<q>(.*?)</q>', row) == words
    assert 'aimed at 18 MB' in rows[2] and '64 MB on slower connections' in rows[3]
    assert '1,000,000 bytes' in page and 'iMessage' not in page
    assert len(re.search(r'<meta name="description" content="([^"]+)"', page).group(1)) <= 165
    assert '/tools/video-checker/checker.js' in page
    assert not re.search(r'function\s+(?:readMp4|parseSPS|inspect)\b', ''.join(p.read_text() for p in TOOL.glob('*.js')))
    for js in [*TOOL.glob('*.js'), SITE / 'tools/video-checker/checker.js']:
        assert not re.search(r'\b(?:fetch|XMLHttpRequest|sendBeacon|WebSocket)\b', js.read_text()), f'network API in {js}'
    assert not re.search(r'<script(?![^>]*\bsrc=)[^>]*>(?!\{)[\s\S]*?\b(?:fetch|XMLHttpRequest|sendBeacon|WebSocket)\b', page)
    schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
    faq = next(s for s in schemas if s.get('@type') == 'FAQPage')
    assert [(q['name'], q['acceptedAnswer']['text']) for q in faq['mainEntity']] == visible_faq(page)
    assert len(faq['mainEntity']) == 3
    ui = BACKEND.resolve().parent / 'ui/src/index.html'
    assert ui.is_file(), f'FAIL: app markup missing: {ui}'
    ui_text = ui.read_text()
    for label in ['Compress', 'Fit a size']:
        assert re.search(r'>\s*' + re.escape(label) + r'\s*<', ui_text), f'app label absent: {label}'
    checker = (SITE / 'tools/video-checker/index.html').read_text()
    for tag in ['<script defer data-domain="crispvideo.app" src="https://plausible.io/js/script.js"></script>', '<script src="/track.js" defer></script>']:
        assert tag in page and tag in checker
    for name in ['how-to/compress-video-on-mac', 'how-to/compress-video-for-discord',
                 'best/video-compressor-for-mac', 'learn/email-size-limits-for-video', 'tools/video-checker']:
        linked = (SITE / name / 'index.html').read_text()
        assert 'Check if your clip fits: <a href="/tools/fit-video-to-size/">' in linked
    proof = re.search(r'<blockquote><p>(.*?)</p></blockquote>', page, re.S).group(1)
    assert proof in (SITE / 'how-to/compress-video-for-discord/index.html').read_text()
    # 2026-11-20: the page carries the site's own top and end product boxes (product_box.py), so the proof order is
    # checked against the END box, and the download link may carry a source tag.
    assert page.index('<blockquote>') < page.index("This page doesn't compress") < page.index('The free version puts') < page.rindex('class="pbox-price"')
    assert 'href="/download/' in page or 'href="https://crispvideo.app/download/' in page
    assert '<loc>https://crispvideo.app/tools/fit-video-to-size/</loc>' in (SITE / 'sitemap.xml').read_text()
    print('fit-to-size: destination values, sources, dates, proof, FAQ, app labels, links and no-network checks passed')


def parser_and_ui():
    # Minimal MP4 metadata fixtures. The browser parser only reads the index, with no media decode.
    print(run_node(r'''
const assert = require('node:assert/strict');
const fs = require('node:fs'), vm = require('node:vm');
const checker = require('./tools/video-checker/checker.js');
const budget = require('./tools/fit-video-to-size/size-budget.js');
const box = (name, ...parts) => { const b = Buffer.concat([Buffer.alloc(8), ...parts]); b.writeUInt32BE(b.length); b.write(name,4); return b; };
function track(kind, rotate = false) {
  const tk = Buffer.alloc(84); tk.writeInt32BE(rotate ? 0 : 65536,40); tk.writeInt32BE(rotate ? 65536 : 0,44);
  const hd = Buffer.alloc(12); hd.write(kind,8);
  const md = Buffer.alloc(20); md.writeUInt32BE(1000,12); md.writeUInt32BE(120000,16);
  const entry = Buffer.alloc(kind === 'vide' ? 86 : 36); entry.writeUInt32BE(entry.length); entry.write(kind === 'vide' ? 'avc1' : 'mp4a',4);
  if (kind === 'vide') { entry.writeUInt16BE(1920,32); entry.writeUInt16BE(1080,34); }
  const sd = Buffer.alloc(8); sd.writeUInt32BE(1,4);
  return box('trak', box('tkhd',tk), box('mdia', box('hdlr',hd), box('mdhd',md), box('minf',box('stbl',box('stsd',sd,entry)))));
}
const file = (...tracks) => new Blob([box('ftyp',Buffer.from('isom0000')), box('moov',...tracks)]);
class Element {
  constructor(value='') { this.value=value; this.children=[]; this.events={}; this.hidden=false; this.files=[]; }
  addEventListener(event, fn) { this.events[event]=fn; }
  replaceChildren() { this.children=[]; }
  appendChild(node) { this.children.push(node); }
}
(async () => {
  for (let n=0; n<=2; n++) {
    const r=await checker.inspect(file(track('vide',true), ...Array.from({length:n},()=>track('soun'))),true);
    assert.equal(r.audioTracks,n); assert.equal(r.duration,120); assert.equal(r.width,1080); assert.equal(r.height,1920);
  }
  assert.equal((await checker.inspect(file(track('soun')),true)).noVideo,true);
  assert.match((await checker.inspect(new Blob([Buffer.from('not an mp4 file at all')]),true)).error,/only read MP4 and MOV/);
  const ebml=new Uint8Array(16); ebml.set([0x1a,0x45,0xdf,0xa3]);
  assert.match((await checker.inspect(new Blob([ebml]),true)).error,/only read MP4 and MOV/);
  assert.match((await checker.inspect(new Blob([box('ftyp',Buffer.from('isom0000'))]),true)).error,/no index/);
  assert.match((await checker.inspect(new Blob(['tiny']),true)).error,/too small/);
  const els=Object.fromEntries(['file','destination','custom','custom-box','result'].map(n=>['fit-'+n,new Element()]));
  els['fit-destination'].value='discord'; els['fit-custom'].value='25';
  const doc={getElementById:id=>els[id],createElement:()=>new Element()};
  let inspect=async f=>f.meta;
  vm.runInNewContext(fs.readFileSync('./tools/fit-video-to-size/fit.js','utf8'),{document:doc,CrispSizeBudget:budget,CrispChecker:{inspect:(...args)=>inspect(...args)}});
  const text=()=>els['fit-result'].children.map(p=>p.textContent).join('\n');
  const choose=async(size, meta={duration:120,width:1920,height:1080,audioTracks:2})=>{
    els['fit-file'].files=[{name:'<img onerror=bad>.mp4',size,meta}];
    await els['fit-file'].events.change();
  };
  await choose(20000000); assert.match(text(),/already at or under/); assert.doesNotMatch(text(),/Crisp aims at/);
  await choose(20000001); assert.match(text(),/20\.000001 MB/); assert.match(text(),/over the size limit/);
  await choose(38600000); assert.match(text(),/Crisp aims at 19 MB/); assert.match(text(),/96 kbps per track/); assert.match(text(),/not a measured export/);
  els['fit-destination'].value='email'; els['fit-destination'].events.change(); assert.match(text(),/Crisp aims at 18 MB/);
  await choose(20000000); assert.match(text(),/already at or under/); assert.match(text(),/above the 18 MB email aim/);
  await choose(18000000); assert.doesNotMatch(text(),/Crisp aims at/);
  els['fit-destination'].value='custom'; els['fit-custom'].value='0'; els['fit-destination'].events.change();
  assert.equal(els['fit-custom-box'].hidden,false); assert.match(text(),/Choose a size above 0/);
  els['fit-custom'].value='0.001'; els['fit-custom'].events.input(); assert.match(text(),/Choose a larger size/);
  els['fit-destination'].value='whatsapp'; els['fit-destination'].events.change(); assert.match(text(),/720p/); assert.match(text(),/64 MB/);
  await choose(1000,{duration:1800,width:3840,height:2160,audioTracks:2}); assert.match(text(),/already at or under/);
  for (const meta of [{error:'Unreadable index'}, {noVideo:true}, {duration:0}, {duration:120,width:0,height:0}, {duration:120,width:1920,height:1080}]) {
    await choose(100,meta); assert.doesNotMatch(text(),/Crisp aims at|already at or under/);
  }
  inspect=async()=>{throw Error('bad file')}; await choose(100); assert.match(text(),/could not read this file/);
  let resolveOld;
  inspect=f=>f.name==='old.mp4'?new Promise(resolve=>resolveOld=resolve):Promise.resolve(f.meta);
  els['fit-file'].files=[{name:'old.mp4',size:1}]; const old=els['fit-file'].events.change();
  await choose(500000); resolveOld({error:'stale result'}); await old; assert.doesNotMatch(text(),/stale result/);
  els['fit-file'].files=[]; await els['fit-file'].events.change(); assert.equal(els['fit-result'].hidden,true);
  process.stdout.write('fit-to-size: MP4 parser reuse, rotation, 0–2 audio tracks, rejected files and picker/destination UI passed\n');
})().catch(e=>{console.error(e);process.exitCode=1});
''').strip())


def main():
    env = original_functions()
    arithmetic(env)
    page_checks()
    parser_and_ui()


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, subprocess.CalledProcessError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError):
            print(error.stderr, file=sys.stderr)
        sys.exit(1)
