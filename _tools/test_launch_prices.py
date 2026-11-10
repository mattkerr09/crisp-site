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


def main():
    landing_pages.prepare_facts()
    facts = llms_txt.facts()
    end = datetime.fromisoformat(facts['ends'].replace('Z', '+00:00'))
    live = llms_txt.founding_live
    assert llms_txt.offer_last_day(facts) == 'through November 30'
    assert llms_txt.future_day(facts) == 'December 1'
    assert de_pages.last_day(facts['ends']) == '30. November'
    assert de_pages.future_day(facts['ends']) == '1. Dezember'
    actions = None
    for instant in (end - timedelta(seconds=1), end, end + timedelta(seconds=1)):
        active = instant < end
        with patch.object(llms_txt, 'founding_live', side_effect=lambda f: live(f, instant)):
            boxes = (product_box.box('top', '/test/'), landing_pages.box('test', False),
                     de_pages.box('de-test', f=facts))
            for i, box in enumerate(boxes):
                amount = llms_txt.money if i < 2 else de_pages.words.money
                price = facts['now'] if active else facts['price']
                assert re.search(r'class="pbox-amt"[^>]*>' + re.escape(amount(price)) + '</span>', box)
                assert ('class="pbox-found"' in box) == active
                assert ('FOUNDINGCRISP' in box) == active
                assert ('data-launch-price' in box) == active
            links = [re.findall(r'<a\b[^>]*>', box) for box in boxes]
            if actions is None:
                actions = links
            else:
                assert links == actions, 'expiry changed a checkout link or tracking'
            rendered = new_pages.build(pages_learn.PAGES[0])
            assert ("Launch price" in rendered) == active
            for copy in (llms_txt.price_copy(facts), landing_pages.bundle_copy(), de_pages.price_copy(facts), de_pages.bundle()):
                assert ('Launch price' in copy or 'Einführungspreis' in copy) == active
    title, note = llms_txt.page_meta('/vs/aiarty-video-enhancer-alternative-mac/')
    # the summary must still say the price after the launch ends, in full; a page may word it "From December 1: $29." or "then $29."
    # (the Aiarty page's description says "... $14.50 through Nov 30, then $29." since 9 Nov), but never stop before the $29
    assert re.search(r'(From December 1: \$29\.|then \$29\.)', note), 'llms.txt cut off the future-price sentence'
    # Execute the real scripts with a small DOM stub. No browser, network, app or sound.
    probe = r'''
const vm = require('node:vm');
const {script, german, end} = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
for (const now of [end - 1, end, end + 1]) {
  const prices = [{textContent: '$14.50', getAttribute: k => k === 'data-full-price' ? '$29' : new Date(end).toISOString()}];
  const notes = [{style: {}}];
  const root = {innerHTML: '', querySelector: () => ({addEventListener() {}})};
  const mount = {getAttribute: k => ({'data-ends': new Date(end).toISOString(), 'data-now': '$14.50', 'data-then': '$29', 'data-code': 'FOUNDINGCRISP'})[k], remove() {}};
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
    if (!/Launch price\s+\$14.50\s+through Nov 30, then \$29/.test(text) || !text.includes('FOUNDINGCRISP')) throw Error(text);
    if (prices[0].textContent !== '$14.50') throw Error('early price reset');
  } else {
    if (root.innerHTML || prices[0].textContent !== '$29' || notes[0].style.display !== 'none') throw Error('expiry failed');
  }
  // German pages do not load founding.js; they carry their own price and note switch.
  const germanPrice = {textContent: '14,50 $', getAttribute: k => k === 'data-full-price' ? '29 $' : new Date(end).toISOString()};
  const germanNote = {removed: false, getAttribute: () => new Date(end).toISOString(), remove() {this.removed = true;}};
  vm.runInNewContext(german, {Date: {now: () => now, parse: Date.parse}, document: {
    querySelectorAll: s => s === '[data-price-ends]' ? [germanPrice] : [germanNote]
  }});
  if (germanPrice.textContent !== (now < end ? '14,50 $' : '29 $') || germanNote.removed !== (now >= end)) throw Error('German expiry failed');
}
'''
    german = ''.join(re.findall(r'<script>(.*?)</script>', de_pages.PRICE_SCRIPT + de_pages.EXPIRY_SCRIPT))
    payload = {'script': (Path(__file__).resolve().parent.parent / 'founding.js').read_text(),
               'german': german, 'end': int(end.timestamp() * 1000)}
    # A fixed Pacific date must survive the visitor's local time zone.
    import os
    for zone in ('America/Los_Angeles', 'Europe/Berlin', 'Asia/Tokyo'):
        subprocess.run(['node', '-e', probe], input=json.dumps(payload), text=True,
                       env=dict(os.environ, TZ=zone), check=True)
    print('launch prices: generator and JS boundary tests passed in three time zones; links and tracking unchanged')


if __name__ == '__main__':
    main()
