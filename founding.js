// upstream-reviewed: 2824cf91adee883d7a93b0c3c7a128892995aaec2abe7ee41869eb4343b20d30
(function () {
  if (window.__kcFounding) return;
  window.__kcFounding = true;
  (function () {
    var m = document.querySelector("[data-founding]");
    var ends = m && m.getAttribute("data-ends");
    var nowMs = (typeof window.__kcNow === "number") ? window.__kcNow : Date.now();   
    if (!ends || isNaN(Date.parse(ends)) || nowMs < Date.parse(ends)) return;
    window.__kcFoundingEnded = true;
    var hide = function () {
      var els = document.querySelectorAll(".pbox-found, .founding-note, [data-founding-copy]");
      for (var i = 0; i < els.length; i++) els[i].style.display = "none";
    };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", hide); else hide();
  })();
  if (window.__kcFoundingEnded) return;

  var untilTxt = "";
  (function () {
    var mt = document.querySelector("[data-founding]");
    var e = mt && mt.getAttribute("data-ends");
    var t = e ? Date.parse(e) : NaN;
    var n = (typeof window.__kcNow === "number") ? window.__kcNow : Date.now();   
    if (isNaN(t) || t <= n) return;
    try {
      var end = new Date(t), day = end.getHours() < 12 ? new Date(t - 12 * 3600e3) : end;
      untilTxt = "until " + day.toLocaleDateString(undefined, { month: "long", day: "numeric" });
    } catch (x) {}
  })();
  if (untilTxt) {
    var dateLines = function () {
      try {
        if (!document.createTreeWalker || typeof NodeFilter === "undefined") return;
        var els = document.querySelectorAll(".pbox-found, .founding-note, [data-founding-copy]");
        for (var i = 0; i < els.length; i++) {
          if ((els[i].textContent || "").indexOf(untilTxt) !== -1) continue;
          var w = document.createTreeWalker(els[i], NodeFilter.SHOW_TEXT, null);
          for (var tn = w.nextNode(); tn; tn = w.nextNode()) {
            var m = /(first \d+ buyers)(?=[.,;:]|\s|$)/.exec(tn.nodeValue);
            if (m) { tn.nodeValue = tn.nodeValue.replace(m[1], m[1] + ", " + untilTxt); break; }
          }
        }
      } catch (x) {}
    };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", dateLines); else dateLines();
  }

  var KEY  = "kc-founding-dismissed";
  try {
    var when = Number(localStorage.getItem(KEY));
    if (when && Date.now() - when < 7 * 24 * 60 * 60 * 1000) return;
  } catch (e) {}

  var mount = document.querySelector("[data-founding]");
  var was = mount && mount.getAttribute("data-was");
  var now = mount && mount.getAttribute("data-now");
  var then = mount && mount.getAttribute("data-then");
  var split = mount && mount.getAttribute("data-now-split");
  var first = mount && mount.getAttribute("data-first");
  var code = (mount && mount.getAttribute("data-code")) || "FOUNDINGCRISP";
  var PH = { url: "https://www.producthunt.com/posts/crisp-8", from: "2026-10-03T07:01:00Z", to: "2026-10-04T07:01:00Z" };
  var phNow = (typeof window.__kcNow === "number") ? window.__kcNow : Date.now();   
  var phLive = phNow >= Date.parse(PH.from) && phNow < Date.parse(PH.to);

  var bar = document.createElement("div");
  bar.id = "kc-founding-bar";
  bar.style.cssText = "position:sticky;top:0;left:0;right:0;z-index:2147482000;width:100%";
  var root = bar.attachShadow ? bar.attachShadow({ mode: "open" }) : bar;

  root.innerHTML = [
    '<style>',
    ':host{all:initial;display:block}',
    '*{box-sizing:border-box;font-family:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}',
    '.bar{display:flex;align-items:center;justify-content:center;gap:.55rem;flex-wrap:nowrap;',
    '  padding:.4rem 2.2rem .4rem .9rem;background:#100D08;color:#EDE6D6;',
    '  font-size:.795rem;line-height:1.3;position:relative;overflow:hidden;',
    '  border-bottom:1px solid rgba(240,180,41,.22)}',
    '.bar::after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;',
    '  background:linear-gradient(90deg,transparent,rgba(240,180,41,.5),transparent)}',
    '.tag{font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:.66rem;',
    '  color:#F0B429;white-space:nowrap;flex:none}',
    '.dot{width:3px;height:3px;border-radius:50%;background:rgba(237,230,214,.3);flex:none}',
    '.txt{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.was{text-decoration:line-through;opacity:.42;margin-right:.28rem}',
    '.now{font-weight:700;color:#F0B429}',
    '.code{display:inline-flex;align-items:center;gap:.35rem;border:1px dashed rgba(240,180,41,.4);',
    '  border-radius:5px;padding:.1rem .3rem .1rem .42rem;font-weight:700;letter-spacing:.05em;',
    '  font-size:.735rem;color:#F0B429;white-space:nowrap;flex:none}',
    'button.copy{border:0;background:rgba(240,180,41,.14);color:#F0B429;border-radius:4px;',
    '  padding:.16rem .38rem;font-size:.68rem;font-weight:700;cursor:pointer;min-height:24px}',
    'button.copy:hover{background:rgba(240,180,41,.28)}',
    '.x{position:absolute;right:.15rem;top:50%;transform:translateY(-50%);border:0;background:none;',
    '  cursor:pointer;color:#EDE6D6;opacity:.4;font-size:1rem;line-height:1;min-width:44px;min-height:38px}',
    '.x:hover{opacity:.9}',
    '@media(max-width:700px){.bar{font-size:.735rem;padding:.38rem 2rem .38rem .6rem;gap:.4rem}',
    '  .dot{display:none}}',
    '@media(max-width:420px){.was{display:none}}',
    '@media(max-width:480px){.tag{display:none}.code{letter-spacing:.02em}',
    '  .bar{flex-wrap:wrap;row-gap:.2rem}.txt{white-space:normal;text-align:center}}',
    '.ph{display:block;text-align:center;padding:.3rem 2.2rem .3rem .9rem;background:#1C1408;color:#EDE6D6;',
    '  font-size:.75rem;line-height:1.3;border-bottom:1px solid rgba(240,180,41,.18);text-decoration:none}',
    '.ph b{color:#F0B429;font-weight:700}',
    '.ph:hover{background:#261B0B}',
    '</style>',
    (phLive ? '<a class="ph" href="' + PH.url + '" target="_blank" rel="noopener">We\u2019re live on <b>Product Hunt</b> today. We\u2019d love your feedback \u2192</a>' : ''),
    '<div class="bar" role="region" aria-label="' + (then ? 'Black Friday offer' : 'Founding offer') + '">',
    '  <span class="tag">' + (then ? 'Black Friday' : 'Founding') + '</span>',
    '  <span class="dot"></span>',
    (then && now
      ? '  <span class="txt">Crisp Pro <span class="now">' + now + (split ? ' · or 4 × ' + split : '') + '</span>' +
        (first ? ' for the first ' + first + ' buyers' : '') + (untilTxt ? ', ' + untilTxt : '') + ', then ' + then
      : '  <span class="txt">50% off' + (first ? ' for the first ' + first + ' buyers' : '') + (untilTxt ? ', ' + untilTxt : '') +
        (was && now ? ': <span class="was">' + was + '</span><span class="now">' + now +
                      (split ? ' · or 4 × ' + split : '') + '</span>' : '')),
    '  </span>',
    '  <span class="dot"></span>',
    '  <span class="code">' + code + '<button class="copy" type="button">Copy</button></span>',
    '  <button class="x" type="button" aria-label="Dismiss this offer">&times;</button>',
    '</div>'
  ].join("");

  root.querySelector(".copy").addEventListener("click", function () {
    var b = this;
    (navigator.clipboard ? navigator.clipboard.writeText(code) : Promise.reject())
      .then(function () { b.textContent = "Copied"; setTimeout(function(){ b.textContent = "Copy"; }, 1800); })
      .catch(function () { b.textContent = "Select it"; });
  });
  root.querySelector(".x").addEventListener("click", function () {
    bar.remove();
    publishHeight();
    try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {}
  });

  function publishHeight() {
    try { document.documentElement.style.setProperty("--kc-bar-h", (bar.isConnected ? bar.offsetHeight : 0) + "px"); } catch (e) {}
  }
  function place() {
    if (!document.body) return setTimeout(place, 50);
    document.body.insertBefore(bar, document.body.firstChild);
    if (mount) mount.remove();
    publishHeight();
    window.addEventListener("resize", publishHeight);
    if (window.ResizeObserver) new ResizeObserver(publishHeight).observe(bar);
  }
  place();
})();
