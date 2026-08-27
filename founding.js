/* The founding offer, as a STICKY TOP BANNER that mounts itself.
 *
 * ⚠️ WHY IT MOVED. This rendered into <div data-founding> wherever each site
 * chose to put it, and Docket put it at 93% of the page — above the footer,
 * below the FAQ, in translucent gold on near-black. Matthew: "the one on docket
 * looks like shit and its all the way at the bottom, i need like a banner or a
 * pop up or something".
 *
 * He is right, and the placement was the bigger half. An offer nobody scrolls to
 * is not an offer. So this no longer asks a site where to go — it mounts a bar at
 * the very top of the document, on every site, identically.
 *
 * ⚠️ A BAR, NOT A MODAL, deliberately. A popup that covers the page is the single
 * most-hated pattern on the web, it is what people install blockers for, and on a
 * product page it interrupts exactly the person who was already reading about the
 * product. A bar is unmissable without being in the way, and it survives being
 * dismissed — which a modal does not, because dismissing a modal is a relief and
 * dismissing a bar is a decision.
 *
 * ⚠️ SOLID, NOT TRANSLUCENT. The old version used rgba(200,150,60,.09) over a
 * dark page and was barely readable. This is a solid amber ground with near-black
 * text — the highest contrast pairing available that still reads as an offer
 * rather than an error.
 *
 * Dismissal is remembered per site in localStorage, wrapped in try/catch because
 * a private window throws on access rather than returning null.
 */
(function () {
  if (window.__kcFounding) return;
  window.__kcFounding = true;

  var KEY  = "kc-founding-dismissed";
  try { if (localStorage.getItem(KEY) === "1") return; } catch (e) {}

  /* Prices come from the mount if a site states them, else from the API. A site
     that hard-codes them is a site that can drift from Dodo; the attribute is a
     convenience, not the source of truth. */
  var mount = document.querySelector("[data-founding]");
  var was = mount && mount.getAttribute("data-was");
  var now = mount && mount.getAttribute("data-now");
  var code = (mount && mount.getAttribute("data-code")) || "FOUNDING1";

  var bar = document.createElement("div");
  bar.id = "kc-founding-bar";
  bar.style.cssText = "position:sticky;top:0;left:0;right:0;z-index:2147482000;width:100%";
  var root = bar.attachShadow ? bar.attachShadow({ mode: "open" }) : bar;

  root.innerHTML = [
    '<style>',
    ':host{all:initial;display:block}',
    '*{box-sizing:border-box;font-family:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}',
    /* ⚠️ SLIM AND DARK, NOT A MUSTARD SLAB. The first version was a full-width
       amber ground 60px tall and Matthew's word for it was "big ass musterd
       color banner", which is fair — a solid saturated fill across the whole
       viewport competes with the page instead of sitting above it.
       This is ~38px, near-black, with amber used as an ACCENT on the tag and the
       new price only. Same information, a tenth of the visual weight. An
       announcement bar should be noticed once and then ignored, and a loud one
       gets dismissed for being loud rather than considered. */
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
    '.left{opacity:.62;white-space:nowrap;flex:none}',
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
    '  .left,.dot{display:none}}',
    '@media(max-width:420px){.was{display:none}}',
    '</style>',
    '<div class="bar" role="region" aria-label="Founding offer">',
    '  <span class="tag">Founding</span>',
    '  <span class="dot"></span>',
    '  <span class="txt">50% off',
        (was && now ? ' — <span class="was">' + was + '</span><span class="now">' + now + '</span>' : ''),
    '  </span>',
    '  <span class="dot"></span>',
    '  <span class="left" data-left></span>',
    '  <span class="code">' + code + '<button class="copy" type="button">Copy</button></span>',
    '  <button class="x" type="button" aria-label="Dismiss this offer">&times;</button>',
    '</div>'
  ].join("");

  root.querySelector(".copy").addEventListener("click", function () {
    var b = this;
    (navigator.clipboard ? navigator.clipboard.writeText(code) : Promise.reject())
      .then(function () { b.textContent = "Copied"; setTimeout(function(){ b.textContent = "Copy"; }, 1800); })
      /* If the clipboard is unavailable the code is still on screen and
         selectable — never claim a copy that did not happen. */
      .catch(function () { b.textContent = "Select it"; });
  });
  root.querySelector(".x").addEventListener("click", function () {
    bar.remove();
    try { localStorage.setItem(KEY, "1"); } catch (e) {}
  });

  /* ⚠️ NO LIVE COUNT ON CRISP, DELIBERATELY. The shared widget reads the
     remaining count from kerr-lead-agent. Crisp's pre-push gate refuses any
     third-party host in loaded JS and is right to: this product is sold on "it
     never phones home", and opening a connection to render a scarcity counter is
     exactly what that claim is about. "So the counter looks urgent" is not a
     reason that survives being read aloud to a customer. */

  /* ⚠️ INTO THE BODY, not before it. document.documentElement.insertBefore(bar,
     document.body) puts an element between <head> and <body>, which is invalid
     HTML — the browser silently discards it and NOTHING THROWS. The widget
     reported no errors and simply was not there. */
  function place() {
    if (!document.body) return setTimeout(place, 50);
    document.body.insertBefore(bar, document.body.firstChild);
    if (mount) mount.remove();
  }
  place();
})();
