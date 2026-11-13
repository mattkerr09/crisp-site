#!/usr/bin/env python3
"""Offline launch-price regressions: generator and browser expiry, dates and checkout links."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import subprocess
from unittest.mock import patch

import de_pages
import landing_pages
import llms_txt
import product_box
import new_pages
import pages_learn
from lang_pages import LanguagePages


def shipped_surfaces():
    """Every visible sale sentence must have a browser expiry path."""
    from gate_price_words import Document, normal
    import sitewide_chrome
    home_mount = next(node.attrs for node in Document(llms_txt.read('/')).root.walk()
                      if 'data-founding' in node.attrs)
    surfaces = []
    for path in sorted(llms_txt.SITE.rglob('index.html')):
        if '_tools' in path.parts:
            continue
        source = path.read_text()
        doc = Document(source)

        def check(node, protected=False, in_body=False):
            in_body = in_body or node.tag == 'body'
            protected = protected or bool(
                {'data-launch-price', 'data-until', 'data-founding-copy'} & node.attrs.keys()
                or {'pbox-found', 'founding-note'} & set((node.attrs.get('class') or '').split()))
            if node.tag in {'script', 'style'}:
                return
            for child in node.children:
                if isinstance(child, str):
                    assert not (in_body and 'Black Friday' in child and not protected), (
                        f'{path.relative_to(llms_txt.SITE)}: sale text has no expiry switch')
                else:
                    check(child, protected, in_body)

        check(doc.root)
        prices = [dict(text=normal(node.text()), full=node.attrs['data-full-price'])
                  for node in doc.root.walk() if 'data-launch-price' in node.attrs]
        mount = next((node.attrs for node in doc.root.walk() if 'data-founding' in node.attrs), None)
        if mount:
            assert mount == home_mount, f'{path}: sale mount differs from home'
            assert sitewide_chrome.founding_script() in source, f'{path}: sale script differs from founding.js'
        if prices:
            assert mount or 'data-price-ends' in source
            surfaces.append(dict(name=str(path.relative_to(llms_txt.SITE)), prices=prices, mount=mount))
    return surfaces


def main():
    landing_pages.prepare_facts()
    facts = llms_txt.facts()
    end = datetime.fromisoformat(facts['ends'].replace('Z', '+00:00'))
    live = llms_txt.founding_live
    assert llms_txt.offer_last_day(facts) == 'through December 2'
    assert llms_txt.future_day(facts) == 'December 3'
    assert de_pages.last_day(facts['ends']) == '2. Dezember'
    assert de_pages.future_day(facts['ends']) == '3. Dezember'
    actions = None
    for instant in (end - timedelta(seconds=1), end, end + timedelta(seconds=1)):
        active = instant < end
        with patch.object(llms_txt, 'founding_live', side_effect=lambda f: live(f, instant)):
            languages = [LanguagePages(lang) for lang in ('de', 'ja', 'pt-br', 'es')]
            boxes = (product_box.box('top', '/test/'), landing_pages.box('test', False),
                     *(gen.box(gen.lang + '-test', f=facts) for gen in languages))
            for i, box in enumerate(boxes):
                amount = llms_txt.money if i < 2 else languages[i - 2].words.money
                price = facts['now'] if active else facts['price']
                assert re.search(r'class="pbox-amt"[^>]*>' + re.escape(amount(price)) + '</span>', box)
                assert ('class="pbox-found"' in box) == active
                assert 'FOUNDING' not in box
                assert ('data-launch-price' in box) == active
            links = [re.findall(r'<a\b[^>]*>', box) for box in boxes]
            if actions is None:
                actions = links
            else:
                assert links == actions, 'expiry changed a checkout link or tracking'
            rendered = new_pages.build(pages_learn.PAGES[0])
            assert ("Black Friday sale" in rendered) == active
            for copy in (llms_txt.price_copy(facts), landing_pages.bundle_copy(),
                         *(gen.price_copy(facts) for gen in languages), *(gen.bundle() for gen in languages)):
                assert ('Black Friday' in copy) == active
            offers = llms_txt.pro_offers(facts)
            assert len(offers) == (2 if active else 1)
            assert offers[-1]['price'] == '19.00'
    title, note = llms_txt.page_meta('/vs/aiarty-video-enhancer-alternative-mac/')
    # The llms.txt summary must include the regular-price sentence after the sale line.
    assert re.search(r'Then \$19\.', note), 'llms.txt cut off the future-price sentence'
    # Execute the real scripts with a small DOM stub. No browser, network, app or sound.
    probe = r'''
const vm = require('node:vm');
const {script, german, end, surfaces} = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
for (const now of [end - 1, end, end + 1]) {
  const prices = [{textContent: '$9.99', getAttribute: k => k === 'data-full-price' ? '$19' : new Date(end).toISOString()}];
  const notes = [{style: {}}];
  const root = {innerHTML: '', querySelector: () => ({addEventListener() {}})};
  const mount = {getAttribute: k => ({'data-ends': new Date(end).toISOString(), 'data-now': '$9.99', 'data-then': '$19', 'data-code': 'FOUNDINGCRISP', 'data-sale-copy': 'Black Friday sale: $9.99 once, 31% off our November price of $14.50, through December 2. Then $19.'})[k], remove() {}};
  const doc = {
    readyState: 'complete',
    querySelector: () => mount,
    querySelectorAll: s => s === '[data-launch-price]' ? prices : notes,
    createElement: () => ({style: {}, attachShadow: () => root}),
    body: {insertBefore() {}}, documentElement: {style: {setProperty() {}}}
  };
  const win = {__kcNow: now, addEventListener() {}};
  vm.runInNewContext(script, {window: win, document: doc, localStorage: {getItem: () => null}, Date});
  if (now < end) {
    const text = root.innerHTML.replace(/<[^>]+>/g, ' ');
    if (!text.includes('Black Friday sale: $9.99 once, 31% off our November price of $14.50, through December 2. Then $19.') || text.includes('FOUNDING') || /button class="copy"/.test(root.innerHTML)) throw Error(text);
    if (prices[0].textContent !== '$9.99') throw Error('early price reset');
  } else {
    if (root.innerHTML || prices[0].textContent !== '$19' || notes[0].style.display !== 'none') throw Error('expiry failed');
  }
  // German pages do not load founding.js; they carry their own price and note switch.
  const germanPrice = {textContent: '9,99 $', getAttribute: k => k === 'data-full-price' ? '19 $' : new Date(end).toISOString()};
  const germanNote = {removed: false, getAttribute: () => new Date(end).toISOString(), remove() {this.removed = true;}};
  vm.runInNewContext(german, {Date: {now: () => now, parse: Date.parse}, document: {
    querySelectorAll: s => s === '[data-price-ends]' ? [germanPrice] : [germanNote]
  }});
  if (germanPrice.textContent !== (now < end ? '9,99 $' : '19 $') || germanNote.removed !== (now >= end)) throw Error('German expiry failed');
}
// Use the prices and mounts from every shipped page, including bundle and cross-sell prices.
for (const surface of surfaces) for (const now of [end - 1, end, end + 1]) {
  const prices = surface.prices.map(p => ({textContent: p.text, getAttribute: k =>
    k === 'data-full-price' ? p.full : new Date(end).toISOString()}));
  const root = {innerHTML: '', querySelector: () => ({addEventListener() {}})};
  const document = {
    readyState: 'complete', querySelector: () => ({getAttribute: k => surface.mount[k], remove() {}}),
    querySelectorAll: s => s === '[data-launch-price]' || s === '[data-price-ends]' ? prices : [],
    createElement: () => ({style: {}, attachShadow: () => root}),
    body: {insertBefore() {}}, documentElement: {style: {setProperty() {}}}
  };
  if (surface.mount) vm.runInNewContext(script, {window: {__kcNow: now, addEventListener() {}},
    document, localStorage: {getItem: () => null}, Date});
  else vm.runInNewContext(german, {document, Date: {now: () => now, parse: Date.parse}});
  prices.forEach((p, i) => {
    const expected = now < end ? surface.prices[i].text : surface.prices[i].full;
    if (p.textContent !== expected) throw Error(surface.name + ': expiry failed for ' + p.textContent);
  });
}
'''
    german = ''.join(re.findall(r'<script>(.*?)</script>', de_pages.PRICE_SCRIPT + de_pages.EXPIRY_SCRIPT))
    payload = {'script': (Path(__file__).resolve().parent.parent / 'founding.js').read_text(),
               'german': german, 'end': int(end.timestamp() * 1000), 'surfaces': shipped_surfaces()}
    # A fixed Pacific date must survive the visitor's local time zone.
    import os
    for zone in ('America/Los_Angeles', 'Europe/Berlin', 'Asia/Tokyo'):
        subprocess.run(['node', '-e', probe], input=json.dumps(payload), text=True,
                       env=dict(os.environ, TZ=zone), check=True)
    print('launch prices: generator and JS boundary tests passed in three time zones; links and tracking unchanged')


if __name__ == '__main__':
    from sale_test_facts import sale_engine
    with sale_engine():
        main()
