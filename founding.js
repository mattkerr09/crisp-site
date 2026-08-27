/* The founding offer — 50% off, and a counter that cannot lie.
 *
 * ⚠️ THE NUMBER COMES FROM DODO, NOT FROM HERE. /founding reads times_used off
 * the discount record itself, so there is no second copy to drift and nothing to
 * remember to update. If the code is used, the number moves; if it is not, it
 * does not.
 *
 * ⚠️ WHY TWO TIERS OF 25 RATHER THAN ONE OF 50. Matthew asked for a counter that
 * "shows under 30 all the time". Displaying a number chosen for effect rather
 * than read from the ledger is a false statement of fact to a customer — and a
 * checkable one, since anyone can buy and watch it not move. Splitting 50 into
 * two cohorts of 25 gives the same urgency honestly: the remainder is genuinely
 * under 30 throughout, because each tier IS 25.
 *
 * ⚠️ IT RENDERS NOTHING IF THE ENDPOINT IS UNREACHABLE. A scarcity claim with no
 * live number behind it is exactly the thing this design exists to avoid, so
 * failure is silence rather than a stale figure.
 *
 * Placement is explicit: <div data-founding data-was="$199" data-now="$99.50">.
 * The two prices are the site's own, stated once per site, because a widget
 * deriving them would be a second source for a number the page already shows.
 */
(function () {
  var mount = document.querySelector("[data-founding]");
  if (!mount || window.__kcFounding) return;
  window.__kcFounding = true;

  /* ⚠️ FIRST-PARTY. Served from crispvideo.app because this site's gate refuses
   * any third-party <script src> loading for every visitor, against a hero that
   * says "Nothing uploaded". The only third-party contact is the fetch below.
   * Keep in sync with ~/ops/lead-agent/widget/founding.js.txt. */
  var API = "https://kerr-lead-agent.kerrco.workers.dev/founding";
  var was = mount.getAttribute("data-was") || "";
  var now = mount.getAttribute("data-now") || "";

  /* ⚠️ THE COUNT LOADS ON A CLICK HERE, NOT ON PAGE LOAD — and that is not a
   * workaround, it is the site's own rule applied correctly.
   *
   * The shared version of this widget fetches the remaining count as soon as the
   * page renders. On the other three sites that is fine. On this one it is not:
   * the hero says "Nothing uploaded", and a visitor who never looks at the offer
   * should not cause a request to anything. The pre-push gate refused it, which
   * is the gate working.
   *
   * So the OFFER renders statically — the code, the price, the terms, all of
   * which are true without asking anybody — and only the live remaining count
   * needs the server. A visitor who wants that number presses a button, and that
   * press is the only thing that leaves the page.
   *
   * The offer is not weaker for it. "50% off, first 50, code FOUNDING1" is the
   * whole of what a buyer needs; the counter is urgency, not information.
   */
  var root = mount.attachShadow ? mount.attachShadow({ mode: "open" }) : mount;
  root.innerHTML = [
    '<style>',
    ':host{all:initial;display:block}',
    '*{box-sizing:border-box;font-family:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}',
    '.w{border:1px solid rgba(200,150,60,.45);background:rgba(200,150,60,.09);',
    '  border-radius:14px;padding:1.05rem 1.15rem;display:flex;flex-direction:column;gap:.5rem;color:inherit}',
    '.tag{font-size:.7rem;font-weight:750;letter-spacing:.11em;text-transform:uppercase;color:#c8963c}',
    '.p{margin:0;font-size:1.15rem;font-weight:700}',
    '.p s{opacity:.5;font-weight:500;margin-right:.4rem}',
    '.c{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;margin-top:.15rem}',
    '.code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.95rem;font-weight:700;',
    '  letter-spacing:.06em;padding:.34rem .7rem;border-radius:8px;border:1px dashed rgba(200,150,60,.65)}',
    '.hint{font-size:.82rem;opacity:.75;line-height:1.5;margin:0}',
    'button{min-height:44px;padding:.4rem .8rem;border-radius:8px;cursor:pointer;font-size:.82rem;',
    '  font-weight:650;border:1px solid rgba(128,128,128,.4);background:transparent;color:inherit}',
    '.left{font-size:.86rem;font-weight:650;opacity:.85}',
    '</style>',
    '<div class="w">',
    '  <span class="tag">Founding offer &mdash; 50% off the first 50</span>',
    (was && now ? '  <p class="p"><s>' + was + '</s>' + now + '</p>' : ''),
    '  <div class="c"><span class="code">FOUNDING1</span>',
    '    <button type="button" data-copy>Copy</button>',
    '    <button type="button" data-count>How many left?</button></div>',
    '  <p class="hint">Enter it in the discount box at checkout. It is not applied automatically.</p>',
    '</div>'
  ].join("");

  var copyBtn = root.querySelector("[data-copy]"), countBtn = root.querySelector("[data-count]");
  copyBtn.addEventListener('click', function () {
    (navigator.clipboard ? navigator.clipboard.writeText("FOUNDING1") : Promise.reject())
      .then(function () { copyBtn.textContent = "Copied"; })
      .catch(function () { copyBtn.textContent = "FOUNDING1"; });
  });
  countBtn.addEventListener('click', function () {
    countBtn.disabled = true; countBtn.textContent = "Checking…";
    fetch(API).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || d.error) { countBtn.textContent = "Could not check"; return; }
      var s2 = document.createElement("span");
      s2.className = "left";
      s2.textContent = d.soldOut ? "All claimed" : d.left + " of " + d.of + " left";
      countBtn.replaceWith(s2);
    }).catch(function () { countBtn.textContent = "Could not check"; });
  });
})();
