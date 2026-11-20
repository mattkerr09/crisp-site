#!/usr/bin/env python3
"""Offline checks for the home proof, shared offers and real sale countdown."""
import html
import json
from pathlib import Path
import re
import subprocess

import faq_jsonld
import landing_pages
import lang_pages
import llms_txt
from sale_test_facts import sale_engine
import sitewide_chrome

SITE = Path(__file__).resolve().parents[1]
QUESTION = "Is Crisp Video the Crisp phone app?"
ANSWER = ("No. Crisp Video is a Mac and Windows app from Kerr & Company, paid once. "
          "The Crisp photo and video app on phones is a different product from a different company.")
EYEBROW = "AI video enhancer for Mac and PC, offline"
PROOF = "Free download, about 94 MB, no email or account. Real exports, not previews. 30-day refund on Pro."
PAGES = ["/best/image-upscaler-mac/", "/best/photo-enhancer-mac/", "/how-to/restore-old-photos-mac/",
         "/tools/fit-video-to-size/", "/learn/is-it-safe-to-upload-family-videos-to-an-ai-upscaler/"]


def nodes(source):
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S):
        data = json.loads(block)
        yield from data.get("@graph", [data])


def home_checks():
    source = llms_txt.read("/")
    visible = re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>', '', source, flags=re.S)
    assert visible.count(EYEBROW) == visible.count(PROOF) == 1
    assert re.search(r'<p class="hero-eyebrow">' + re.escape(EYEBROW) + r'</p>\s*<h1', visible)
    assert '<h1 class="h-xl"><span class="setup">Old, low-res video, made sharp.</span><br><span class="grad">On your computer.</span></h1>' in source
    assert re.search(r'</div>\s*<p class="hero-proof">' + re.escape(PROOF), source)
    for cls in ("hero-eyebrow", "hero-proof"):
        assert re.search(r'\.' + cls + r'\s*\{', source), cls + " needs a CSS rule"
    shown = faq_jsonld.visible_faq(source)
    assert shown.count((QUESTION, ANSWER)) == 1
    assert visible.count(QUESTION) == 1
    assert html.unescape(visible).count(ANSWER) == 1
    faq = next(node for node in nodes(source) if node.get("@type") == "FAQPage")
    entries = [item for item in faq["mainEntity"] if item["name"] == QUESTION]
    assert len(entries) == 1 and entries[0]["acceptedAnswer"]["text"] == ANSWER
    assert faq_jsonld.rebuild(source)[0] == source
    # The new details reader must leave the existing heading format working.
    fixture = '<article><h2>FAQ</h2><h3>Is it free?</h3><p>Yes.</p></article>'
    assert faq_jsonld.visible_faq(fixture) == [("Is it free?", "Yes.")]
    org = next(node for node in nodes(source) if node.get("@type") == "Organization")
    assert set(org["sameAs"]) == {
        "https://github.com/mattkerr09/crisp-site", "https://www.producthunt.com/products/crisp-7",
        "https://apps.microsoft.com/detail/xpdngln859ct8m", "https://alternativeto.net/software/crisp-video/",
        "https://www.saashub.com/crispvideo-app"}
    return source


def offers_checks(home):
    expected = next(node for node in nodes(home) if node.get("@type") == "SoftwareApplication")["offers"]
    with sale_engine():
        assert expected == llms_txt.home_offers(llms_txt.facts())
        assert landing_pages.home(home) == home
        for lang in ("de", "es", "ja", "pt-br"):
            generator = lang_pages.LanguagePages(lang)
            source = llms_txt.read('/' + lang + '/')
            offers = next(node for node in nodes(source) if node.get("@type") == "SoftwareApplication")["offers"]
            assert offers == expected, lang + " offers differ from English"
            assert generator.pages()[SITE / lang / 'index.html'] == source, lang + " home is stale"


def llms_checks():
    listed = llms_txt.BEST + llms_txt.HOWTOS + llms_txt.TOOLS + llms_txt.LEARN
    for page in PAGES:
        assert listed.count(page) == 1, page
        source = llms_txt.read(page)
        description = html.unescape(re.search(r'<meta name="description" content="([^"]+)"', source)[1])
        line = llms_txt.link(page)
        assert line.startswith('- [') and llms_txt.BASE + page in line
        note = line.split('): ', 1)[1]
        assert note and '\n' not in note and description.startswith(note), page + " must use its own description"


def countdown_checks():
    script = sitewide_chrome.founding_script()
    assert not re.search(r'\bfetch\b', script)
    cases = [
        {"at": "2026-11-20T12:00Z", "text": "Sale ends in 12 days 19 hours", "ended": False},
        {"at": "2026-12-03T07:30Z", "text": "Sale ends in 30 minutes", "ended": False},
        {"at": "2026-12-03T08:00Z", "text": "", "ended": True},
    ]
    pages = []
    for name in ("index.html", "for/family-archivists/index.html"):
        source = (SITE / name).read_text()
        mount = re.search(r'<div data-founding\b[^>]*>', source)[0]
        attrs = dict(re.findall(r'(data-[a-z-]+)="([^"]*)"', mount))
        assert source.count('data-sale-countdown data-founding-copy hidden></span>') == 1
        assert source.count(script) == 1, name + " inline script is stale"
        assert '[data-sale-countdown]{' in (source if name == "index.html" else (SITE / 'style.css').read_text())
        pages.append({"name": name, "attrs": attrs})
    probe = r'''
const assert = require('node:assert/strict');
const vm = require('node:vm');
const input = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
function run(page, test, loading, dismissed) {
  let clock = Date.parse(test.at), tick, cleared = false, ready, bar;
  const countdown = {hidden: true, textContent: '', style: {}};
  const price = {textContent: '$9.99', getAttribute: () => '$29'};
  const note = {style: {}};
  const mount = {getAttribute: name => page.attrs[name], remove() {}};
  const style = {setProperty() {}};
  const document = {
    readyState: loading ? 'loading' : 'complete', documentElement: {style},
    querySelector: selector => selector === '[data-founding]' ? mount : null,
    querySelectorAll(selector) {
      if (selector === '[data-sale-countdown]') return [countdown];
      if (selector === '[data-launch-price]') return [price];
      if (selector === '.pbox-found, .founding-note, [data-founding-copy]') return [note, countdown];
      throw Error('Unexpected selector ' + selector);
    },
    addEventListener(event, callback) { assert.equal(event, 'DOMContentLoaded'); ready = callback; },
    createElement() {
      bar = {style: {}, isConnected: false, offsetHeight: 30,
        attachShadow() { return {querySelector() { return {addEventListener() {}}; }}; },
        remove() { this.isConnected = false; }};
      return bar;
    },
    body: {firstChild: null, insertBefore(node) {node.isConnected = true;}}
  };
  const window = {addEventListener() {},
    setInterval(callback, delay) { assert.equal(delay, 60000); tick = callback; return 1; },
    clearInterval(id) { assert.equal(id, 1); cleared = true; }};
  const context = {window, document,
    Date: {now: () => clock, parse: Date.parse},
    localStorage: {getItem: () => dismissed ? String(clock - 60000) : null},
    setTimeout() { throw Error('Unexpected timeout'); }};
  vm.runInNewContext(input.script, context);
  if (loading) { assert.equal(countdown.hidden, true); ready(); }
  assert.equal(countdown.hidden, test.ended);
  assert.equal(countdown.textContent, test.text);
  assert.equal(!!window.__kcFoundingEnded, test.ended);
  if (test.ended) {
    assert.equal(price.textContent, '$29');
    assert.equal(note.style.display, 'none');
    assert.ok(!bar);
  } else {
    assert.equal(typeof tick, 'function');
    clock = Date.parse('2026-12-03T07:58:59Z'); tick();
    assert.equal(countdown.textContent, 'Sale ends in 1 minute');
    clock = Date.parse(page.attrs['data-ends']); tick();
    assert.equal(countdown.hidden, true);
    assert.equal(note.style.display, 'none');
    assert.equal(price.textContent, '$29');
    assert.ok(!bar || !bar.isConnected);
    assert.ok(cleared);
  }
}
for (const page of input.pages) for (const test of input.cases)
  for (const loading of [true, false]) for (const dismissed of [true, false])
    run(page, test, loading, dismissed);
for (const test of input.cases) console.log(test.at + ': ' + (test.ended ? 'hidden' : test.text));
console.log('Countdown: both pages, minute updates, expiry, dismissed bar and loading states passed');
'''
    subprocess.run(["node", "-e", probe], input=json.dumps({"script": script, "pages": pages, "cases": cases}),
                   text=True, check=True)


def main():
    home = home_checks()
    offers_checks(home)
    llms_checks()
    countdown_checks()
    print("Home proof: copy, FAQ, sameAs, shared offers and llms links passed")


if __name__ == "__main__":
    main()
