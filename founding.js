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
    '.bar{display:flex;align-items:center;justify-content:center;gap:.75rem;flex-wrap:wrap;',
    '  padding:.6rem 2.6rem .6rem 1rem;background:linear-gradient(96deg,#F0B429 0%,#E8A317 100%);',
    '  color:#1A1206;font-size:.9rem;line-height:1.35;position:relative;',
    '  box-shadow:0 1px 0 rgba(0,0,0,.18),0 6px 22px -8px rgba(0,0,0,.4)}',
    '.tag{font-weight:800;letter-spacing:.05em;text-transform:uppercase;font-size:.76rem;',
    '  background:#1A1206;color:#F0B429;padding:.22rem .5rem;border-radius:5px;white-space:nowrap}',
    '.txt{font-weight:600}',
    '.was{text-decoration:line-through;opacity:.55;margin-right:.25rem}',
    '.now{font-weight:800}',
    '.left{font-weight:700;opacity:.85;white-space:nowrap}',
    '.code{display:inline-flex;align-items:center;gap:.4rem;background:rgba(26,18,6,.1);',
    '  border:1px dashed rgba(26,18,6,.45);border-radius:7px;padding:.2rem .45rem;font-weight:800;',
    '  letter-spacing:.06em;font-size:.84rem}',
    'button.copy{border:0;background:#1A1206;color:#F0B429;border-radius:6px;padding:.3rem .6rem;',
    '  font-size:.76rem;font-weight:700;cursor:pointer;min-height:32px}',
    'button.copy:hover{background:#000}',
    '.x{position:absolute;right:.35rem;top:50%;transform:translateY(-50%);border:0;background:none;',
    '  cursor:pointer;color:#1A1206;opacity:.6;font-size:1.15rem;line-height:1;',
    '  min-width:44px;min-height:44px}',
    '.x:hover{opacity:1}',
    '@media(max-width:640px){.bar{font-size:.83rem;padding:.55rem 2.4rem .55rem .7rem;gap:.5rem}',
    '  .left{display:none}}',
    '</style>',
    '<div class="bar" role="region" aria-label="Founding offer">',
    '  <span class="tag">Founding offer</span>',
    '  <span class="txt">50% off',
        (was && now ? ' — <span class="was">' + was + '</span><span class="now">' + now + '</span>' : ''),
    '  </span>',
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

  /* ⚠️ NO LIVE COUNT ON CRISP, DELIBERATELY — and this is the one difference
     between this copy and the shared widget.
     The shared version fetches the remaining count from kerr-lead-agent so the
     number cannot be stale or invented. Crisp's own pre-push gate refuses any
     third-party host in loaded JS, and it is right to: this product is sold on
     "it never phones home", and a page that opens a connection to our
     infrastructure to render a scarcity counter is exactly the thing that claim
     is about. The gate asked for a reason that survives being read aloud to a
     customer, and "so the discount counter looks urgent" is not one.
     So the bar shows the offer, the price pair and the code — the whole
     persuasive core — and simply omits the count here. */

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
