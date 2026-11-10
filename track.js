window.plausible = window.plausible || function () { (window.plausible.q = window.plausible.q || []).push(arguments); };
document.addEventListener("click", function (e) {
  var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
  if (!a) return;
  var href = a.getAttribute("href") || "";
  var name = a.getAttribute("data-track") || (a.textContent || "").replace(/\s+/g, " ").trim().slice(0, 40);
  if (/\/Crisp\.dmg$|\/Crisp-[\d.]+-x64-setup\.exe$/.test(href)) {
    window.plausible("Download", { props: { button: name } });
    try { crispNextSteps(a, /\.exe$/.test(href)); } catch (err) {}
  } else if (/^(?:https:\/\/crispvideo\.app)?\/download\/(?:\?|$)/.test(href) && a.getAttribute("data-track")) {
    window.plausible("Download Page", { props: { button: name } });
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

/* send-mac-link:begin */
(function () {
  if (window.crispSendLinkBound) return;
  window.crispSendLinkBound = true;
  var TITLE = 'Crisp Video for Mac';
  var TEXT = 'Crisp Video for Mac and Windows is free, with the full editor and 4K upscaling up to 15 seconds, everything else at full length, with a small “crispvideo.app” mark. Open this on your Mac or PC to download it.';
  var SAY = {
    shared: 'Done. When you’re at your Mac, open the link to download Crisp.',
    copied: 'Link copied. Paste it into a note or a message to yourself, then open it on your Mac.',
    other: 'Here’s the link. Copy it, or email or text it to yourself:',
    nocopy: 'Press and hold the link to copy it, or email or text it to yourself:'
  };
  function kcCarry(url) { try { var s = JSON.parse(localStorage.getItem('kc_aff') || 'null'); var v = (s && s.exp > Date.now() && s.v) || {}; var q = []; var r = v.ref || v.landing_source; if (r) q.push('ref=' + encodeURIComponent(r)); ['via', 'rekomi_ref', 'affonso_referral', 'awc', 'cjevent', 'irclickid'].forEach(function (k) { if (v[k]) q.push(k + '=' + encodeURIComponent(v[k])); }); return q.length ? url + '&' + q.join('&') : url; } catch (e) { return url; } }
  function ev(name, props) { try { if (window.plausible) window.plausible(name, { props: props }); } catch (e) {} }
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; return n; }
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
  function box(b, url) {
    var to = b.getAttribute('data-send-box'), named = to ? document.querySelector('[data-send-mac-link="' + to + '"]') : null;
    var host = named || (b.closest && b.closest('p')) || b, s = host.nextElementSibling;
    if (!s || s.className !== 'sendlink') {
      s = el('div', 'sendlink');
      s.setAttribute('role', 'group');
      s.setAttribute('aria-label', 'Your link for later');
      var msg = s.appendChild(el('p', 'sendlink-msg'));
      msg.setAttribute('role', 'status');
      var u = s.appendChild(el('p', 'sendlink-url'));
      u.addEventListener('click', function () {   
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
      if (s.scrollIntoView) s.scrollIntoView({ block: 'nearest' });   
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

/* next-steps:begin */
function crispNextSteps(a, win) {
  var root = document.documentElement;
  if (!/^en\b/i.test(root.lang || 'en') || root.classList.contains('handheld')) return;
  if (!document.getElementById('crisp-next-css')) {
    var st = document.createElement('style');
    st.id = 'crisp-next-css';
    st.textContent = '.crisp-next{margin:.9rem 0 1.1rem;padding:1rem 1.15rem;max-width:30rem;text-align:left;border:1px solid rgba(255,255,255,.14);' +
      'border-radius:12px;background:rgba(255,255,255,.04);color:var(--white,#f2f4f7);font-size:.95rem;line-height:1.5;}' +
      '.crisp-next strong{display:block;margin-bottom:.35rem;font-weight:650;}' +
      '.crisp-next ol{margin:0;padding-left:1.25rem;color:var(--grey,#b4bbc6);}.crisp-next li{margin:.2rem 0;}' +
      '.crisp-next li span{color:var(--white,#f2f4f7);}';
    document.head.appendChild(st);
  }
  var steps = win
    ? ['Open the Crisp setup file in your Downloads.', 'Follow its steps to install Crisp, then open Crisp.',
       'Drop in a clip. The first 15 seconds restore free, with a small mark.']
    : ['Open the Crisp .dmg in your Downloads.', 'Drag Crisp into Applications, then open it.',
       'Drop in a clip. The first 15 seconds restore free, with a small mark.'];
  var host = (a.closest && a.closest('p, .cta, .pbox-actions, .step-dl, li')) || a;
  var old = document.querySelector('.crisp-next');
  if (old && old.parentNode) old.parentNode.removeChild(old);
  var box = document.createElement('div');
  box.className = 'crisp-next';
  box.setAttribute('role', 'status');
  var h = document.createElement('strong');
  h.textContent = 'Crisp is downloading.';
  box.appendChild(h);
  var ol = document.createElement('ol');
  for (var i = 0; i < steps.length; i++) {
    var li = document.createElement('li'), sp = document.createElement('span');
    sp.textContent = steps[i];
    li.appendChild(sp);
    ol.appendChild(li);
  }
  box.appendChild(ol);
  host.parentNode.insertBefore(box, host.nextSibling);
}
/* next-steps:end */
