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
/* ⛔ THIS FILE IS A DELIBERATE FORK of the shared widget served by kerr-lead-agent.
 * It is NOT drift and must not be "fixed" by loading the worker's script or copying it
 * verbatim — both fail this site's own pre-push gate. The worker's tag is a third-party
 * <script src> the per-file exemption does not cover, and the worker's copy fetches the
 * count ON LOAD, which is a third-party request on every page view of a site whose hero
 * says "Nothing uploaded". PORT changes into this file; never adopt the file.
 *
 * ⚠️ THE COST OF A FORK IS THAT IT IS SILENT, AND IT WAS PAID ONCE ALREADY. The shared
 * widget's seven-day dismissal fix landed upstream on 2026-09-15 and this copy did not
 * inherit it, so a dismissal here still lasted forever — which is how a bar that had been
 * live since a1f3647 was reported as "there are no promo bars on crisp". Nothing was
 * broken, nothing failed a gate, and no check could see it.
 *
 * So the fork records WHICH upstream revision it was last reconciled against. When the
 * line below stops matching sha256(~/ops/lead-agent/widget/founding.js.txt), upstream has
 * moved and somebody must decide whether this file needs the change. ~/ops/bin/drift.py
 * checks it. Update this line ONLY after actually reading the upstream diff — bumping it
 * to silence the check is the one way to make this worse than having no check.
 *
 * upstream-reviewed: 92ec58509867e51cd38a75551fb74daf5e38cecccf5291783bfc9875bf4bca87  (2026-09-15)
 */
(function () {
  if (window.__kcFounding) return;
  window.__kcFounding = true;

  var KEY  = "kc-founding-dismissed";
  /* A dismissal used to last forever ("1"), which hid the offer from every
     returning visitor for good — including Matthew, who dismissed it and then
     reported the bar missing from crispvideo.app (2026-09-15). The shared widget
     was fixed the same day; this vendored copy is a FORK and did not inherit it,
     which is the standing cost of forking and the reason this comment names it.
     It now lasts seven days: the value is the dismissal time, and an old "1"
     counts as expired. */
  try {
    var when = Number(localStorage.getItem(KEY));
    if (when && Date.now() - when < 7 * 24 * 60 * 60 * 1000) return;
  } catch (e) {}

  /* Prices come from the mount if a site states them, else from the API. A site
     that hard-codes them is a site that can drift from Dodo; the attribute is a
     convenience, not the source of truth. */
  var mount = document.querySelector("[data-founding]");
  var was = mount && mount.getAttribute("data-was");
  var now = mount && mount.getAttribute("data-now");
  /* 2026-09-28, Matthew: the pay-in-four price goes RIGHT NEXT TO the price, in the same font —
     "$64.50 · or 4 × $16.13". It rides inside .now so it cannot be styled apart from the price.
     From the mount, like the prices: a site whose checkout does not offer pay-in-four simply omits
     data-now-split (the instalment gates fail a page that keeps it while CRISP_BNPL_LIVE is false). */
  var split = mount && mount.getAttribute("data-now-split");
  var first = mount && mount.getAttribute("data-first");
  /* ⚠️ THE FALLBACK IS THE DANGEROUS HALF, NOT THE ATTRIBUTE. Until 2026-09-15 the mount
     carried NO data-code at all, so the bar printed the OLD SHARED CODE through this default
     and nobody had typed that code anywhere on the site. That shared code is being expired in
     Dodo now that each app has its own, which would have turned this silent path into a bar
     offering a code the checkout rejects. Both halves are set, so a missing attribute cannot
     resurrect a dead code.

     ⛔ AND THE RETIRED CODE IS NOT SPELLED OUT HERE, DELIBERATELY. A grep for a promo code
     should find the code the site OFFERS, not a comment reminiscing about one it withdrew —
     this file's own history includes a checker that harvested quoted strings out of comments
     and reported them as live claims. Naming it here would make every future audit ambiguous. */
  var code = (mount && mount.getAttribute("data-code")) || "FOUNDINGCRISP";

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
    /* The shared bar's phone rule (upstream 2b57346): the tag goes, the code tightens. And
       because the price now carries its four-payment split, on a phone the line WRAPS rather
       than ellipsising — a price cut off mid-figure is worse than a two-line bar. */
    '@media(max-width:480px){.tag{display:none}.code{letter-spacing:.02em}',
    '  .bar{flex-wrap:wrap;row-gap:.2rem}.txt{white-space:normal;text-align:center}}',
    '</style>',
    '<div class="bar" role="region" aria-label="Founding offer">',
    '  <span class="tag">Founding</span>',
    '  <span class="dot"></span>',
    '  <span class="txt">50% off',
        (first ? ' for the first ' + first + ' buyers' : ''),
        (was && now ? ' — <span class="was">' + was + '</span><span class="now">' + now +
                      (split ? ' · or 4 × ' + split : '') + '</span>' : ''),
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
      /* If the clipboard is unavailable the code is still on screen and
         selectable — never claim a copy that did not happen. */
      .catch(function () { b.textContent = "Select it"; });
  });
  root.querySelector(".x").addEventListener("click", function () {
    bar.remove();
    publishHeight();
    try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {}
  });

  /* ⛔ NO SEAT COUNT, EVER (Matthew, 2026-09-28: "it still says 24/25, get that tf off, and do this
     for every site"). The count button and its call to the lead-agent worker's founding endpoint
     are gone, and with them the only network request this file made — so it also left
     gate_thirdparty.py's exemption table in the same change. The bar states the cap ("for the
     first 25 buyers") and nothing else about seats. Do not bring back a count, a remaining
     number or a "claimed" state without Matthew asking for it. */
  /* ⚠️ INTO THE BODY, not before it. document.documentElement.insertBefore(bar,
     document.body) puts an element between <head> and <body>, which is invalid
     HTML — the browser silently discards it and NOTHING THROWS. The widget
     reported no errors and simply was not there. */
  /* ⚠️ THE BAR AND THE SITE'S STICKY NAV BOTH WANT top:0. They did from the start — the bar
     covered the top of the nav once you scrolled — and on 2026-09-28 the four-payment price made the
     bar wrap to two lines on a phone, where it then hid the whole nav, Download button included.
     The bar publishes its height as --kc-bar-h and the nav sticks BELOW it (top:var(--kc-bar-h,0px)
     in index.html and style.css). Re-measured on resize; back to 0 when dismissed. */
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
