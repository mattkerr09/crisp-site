/* PLAUSIBLE CUSTOM EVENTS, on every page (moved out of the homepage 2026-09-28 so the in-article product
   boxes on every guide are counted too — "tracking on every button", the CEO's sell-checklist item 5).
   "Download" on every Crisp.dmg link and "Buy" on every checkout link, each with the button that was pressed
   (data-track, else its text). The GOALS live in Plausible's dashboard, which is Matthew's; this only sends
   the events. A Buy click leaves the page, so it waits for Plausible's callback (600 ms at most) before
   following the link — a modified click (new tab) is never intercepted. First-party, no network of its own. */
window.plausible = window.plausible || function () { (window.plausible.q = window.plausible.q || []).push(arguments); };
document.addEventListener("click", function (e) {
  var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
  if (!a) return;
  var href = a.getAttribute("href") || "";
  var name = a.getAttribute("data-track") || (a.textContent || "").replace(/\s+/g, " ").trim().slice(0, 40);
  if (/\/Crisp\.dmg$/.test(href)) {
    window.plausible("Download", { props: { button: name } });
  // ...and the hub's /buy/<app>, which opens the same Dodo checkout with the founding code applied (2026-10-01)
  } else if (/^https:\/\/(checkout\.dodopayments\.com\/|kerr-affiliate-hub\.kerrco\.workers\.dev\/buy\/)/.test(href)) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || a.target === "_blank" || e.button !== 0) {
      window.plausible("Buy", { props: { button: name } });
      return;
    }
    e.preventDefault();
    var done = false, go = function () { if (!done) { done = true; window.location.href = href; } };
    setTimeout(go, 600);
    window.plausible("Buy", { props: { button: name }, callback: go });
  }
}, true);

/* send-mac-link:begin. THE SAME BLOCK is inline at the foot of index.html (so the homepage's phone action never waits on
   another file, or on a blocker that refuses anything named track.js) and in track.js (every guide's product box); a test
   in the Crisp suite keeps the two byte-identical, and whichever runs first is the only one that binds.

   "Send the Mac link to yourself" (rebuilt 2026-10-28). Crisp is a Mac app, so a visitor on a phone or tablet has to get
   the link to their Mac, and every path here ends with them holding it, whatever the browser:
   1. the share sheet where there is one (Safari on iPhone and iPad, Chrome on Android, and the in-app browsers built on
      them), then one line saying what to do next;
   2. no share sheet: the link is copied at once, and the box under the button says "copied" only if the copy really worked;
   3. a share sheet that fails or is closed, or a copy that does not work: the same box shows the link as plain text to
      press and hold, a Copy button, and Email it / Text it links.
   NOTHING HERE NAVIGATES ON ITS OWN. The old fallback set location.href to a mailto:, and an in-app browser whose app does
   not hand mailto: on (a WKWebView, an Android WebView) did nothing at all, or replaced the page with an error; a share that
   failed or was closed also ended in nothing. Mail and Messages are now links the visitor taps, beside the copy and the text.
   kcCarry() keeps where the visitor came from (the hub snippet's kc_aff: ?ref=producthunt is stored as landing_source) on
   the link, so the Mac visit it leads to still counts for that source. */
(function () {
  if (window.crispSendLinkBound) return;
  window.crispSendLinkBound = true;
  var TITLE = 'Crisp Video for Mac';
  var TEXT = 'Crisp Video for Mac is free, with the full editor and 4K upscaling up to 60 seconds, everything else at full length, with a small “Made with Crisp” mark. Open this on your Mac to download it.';
  var SAY = {
    shared: 'Done. When you’re at your Mac, open the link to download Crisp.',
    copied: 'Link copied. Paste it into a note or a message to yourself, then open it on your Mac.',
    other: 'Here’s the link. Copy it, or email or text it to yourself:',
    nocopy: 'Press and hold the link to copy it, or email or text it to yourself:'
  };
  function kcCarry(url) { try { var s = JSON.parse(localStorage.getItem('kc_aff') || 'null'); var v = (s && s.exp > Date.now() && s.v) || {}; var q = []; var r = v.ref || v.landing_source; if (r) q.push('ref=' + encodeURIComponent(r)); ['via', 'rekomi_ref', 'affonso_referral', 'awc', 'cjevent', 'irclickid'].forEach(function (k) { if (v[k]) q.push(k + '=' + encodeURIComponent(v[k])); }); return q.length ? url + '&' + q.join('&') : url; } catch (e) { return url; } }
  function ev(name, props) { try { if (window.plausible) window.plausible(name, { props: props }); } catch (e) {} }
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; return n; }
  /* done(true) only when a copy is known to have happened. navigator.clipboard first; then the textarea + execCommand that
     older browsers and some in-app ones still need (16px so iOS does not zoom, fixed at the top so nothing scrolls). */
  function copy(t, done) {
    function legacy() {
      var ok = false, ta = null;
      try {
        ta = el('textarea'); ta.value = t; ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;font-size:16px;';
        document.body.appendChild(ta); ta.focus(); ta.select(); ta.setSelectionRange(0, t.length);
        ok = document.execCommand('copy') === true;
      } catch (e) {}
      try { if (ta && ta.parentNode) ta.parentNode.removeChild(ta); } catch (e) {}
      done(ok);
    }
    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        navigator.clipboard.writeText(t).then(function () { done(true); }, legacy);
        return;
      }
    } catch (e) {}
    legacy();
  }
  /* The box under the button: built on first use, after the paragraph the button sits in (or after the button itself). */
  function box(b, url) {
    // a button elsewhere (the top bar's) names the send button whose box it opens, so the box lands in the page, not the bar
    var to = b.getAttribute('data-send-box'), named = to ? document.querySelector('[data-send-mac-link="' + to + '"]') : null;
    var host = named || (b.closest && b.closest('p')) || b, s = host.nextElementSibling;
    if (!s || s.className !== 'sendlink') {
      s = el('div', 'sendlink');
      s.setAttribute('role', 'group');
      s.setAttribute('aria-label', 'Your link for later');
      var msg = s.appendChild(el('p', 'sendlink-msg'));
      msg.setAttribute('role', 'status');
      var u = s.appendChild(el('p', 'sendlink-url'));
      u.addEventListener('click', function () {   // one tap selects the whole link, ready for Copy
        try { var r = document.createRange(); r.selectNodeContents(u); var g = window.getSelection(); g.removeAllRanges(); g.addRange(r); } catch (e) {}
      });
      var w = s.appendChild(el('p', 'sendlink-ways'));
      var c = w.appendChild(el('button', 'btn btn-ghost', 'Copy link'));
      c.type = 'button';
      c.addEventListener('click', function () {
        copy(s.getAttribute('data-url'), function (ok) {
          msg.textContent = ok ? 'Link copied. Paste it into a note or a message to yourself.' : 'This browser would not copy it. Press and hold the link to copy it.';
          ev('Send Mac Link Result', { result: ok ? 'copy' : 'copy-failed' });
        });
      });
      w.appendChild(el('a', 'btn btn-ghost', 'Email it')).addEventListener('click', function () { ev('Send Mac Link Result', { result: 'email' }); });
      w.appendChild(el('a', 'btn btn-ghost', 'Text it')).addEventListener('click', function () { ev('Send Mac Link Result', { result: 'text' }); });
      host.parentNode.insertBefore(s, host.nextSibling);
    }
    s.setAttribute('data-url', url);
    s.querySelector('.sendlink-url').textContent = url;
    var links = s.querySelectorAll('.sendlink-ways a');
    links[0].setAttribute('href', 'mailto:?subject=' + encodeURIComponent('Crisp Video for Mac: download link') + '&body=' + encodeURIComponent(TEXT + '\n\n' + url));
    links[1].setAttribute('href', 'sms:?&body=' + encodeURIComponent(TEXT + ' ' + url));
    return s;
  }
  function show(b, url, result) {
    try {
      var s = box(b, url), full = result !== 'shared';
      s.querySelector('.sendlink-msg').textContent = SAY[result === 'shared' ? 'shared' : result === 'copied' ? 'copied' : result === 'copy-failed' ? 'nocopy' : 'other'];
      s.querySelector('.sendlink-url').hidden = !full;
      s.querySelector('.sendlink-ways').hidden = !full;
      if (s.scrollIntoView) s.scrollIntoView({ block: 'nearest' });   // on a phone the box lands under the fold otherwise
    } catch (e) {}
    ev('Send Mac Link Result', { result: result });
  }
  function send(b) {
    var where = b.getAttribute('data-send-mac-link') || (!b.closest ? 'page' : b.closest('.pbox') ? 'guide' : b.closest('.hero') ? 'hero-line' : 'page');
    var url = kcCarry('https://crispvideo.app' + location.pathname + '?utm_source=phone-share&utm_medium=share');
    var data = { title: TITLE, text: TEXT, url: url };
    ev('Send Mac Link', { where: where });
    var can = typeof navigator.share === 'function';
    try { if (can && typeof navigator.canShare === 'function' && !navigator.canShare(data)) can = false; } catch (e) {}
    if (can) {
      var p;
      try { p = navigator.share(data); } catch (e) { p = Promise.reject(e); }
      Promise.resolve(p).then(function () { show(b, url, 'shared'); },
        function (e) { show(b, url, e && e.name === 'AbortError' ? 'cancelled' : 'share-failed'); });
      return;
    }
    copy(url, function (ok) { show(b, url, ok ? 'copied' : 'copy-failed'); });
  }
  document.addEventListener('click', function (e) {
    var b = e.target && e.target.closest ? e.target.closest('[data-send-mac-link]') : null;
    if (b) send(b);
  });
})();
/* send-mac-link:end */
