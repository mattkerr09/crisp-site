/* "Coming to Windows — tell me when it's ready", as one script tag.
 *
 * ⚠️ IT PROMISES NO DATE, deliberately. Windows is real — AdPlaybook's CI
 * produces an .msi and a setup .exe, and ~/ops/windows-port/ carries the kit the
 * other three will use — but nothing has shipped to a customer and no date is
 * knowable. "Coming soon" with a sign-up is the honest shape for that: it states
 * the intent, and the list is the mechanism for "we do not know when yet".
 * A date here would be a promise nobody can keep, and the people who sign up are
 * exactly the ones who would remember it.
 *
 * ⚠️ EXPLICIT PLACEMENT, NEVER GUESSED. It renders into <div data-win-notify>
 * and does nothing at all if that element is absent. Four sites with four
 * layouts; a script deciding for itself where to inject a form is how you end up
 * with a signup box wedged into a footer nobody reads.
 *
 * Posts to the subscribe worker, which already accepts all four origins. The
 * source is "<host>-windows" so this list is separable from every other one —
 * a Windows waiting list is a different consent from a newsletter, and merging
 * them would mean mailing people about something they never asked for.
 */
(function () {
  var mount = document.querySelector("[data-win-notify]");
  if (!mount || window.__kcWinNotify) return;
  window.__kcWinNotify = true;

  var API = "https://kerr-subscribe.kerrco.workers.dev";
  var host = location.hostname.replace(/^www\./, "");
  var root = mount.attachShadow ? mount.attachShadow({ mode: "open" }) : mount;

  root.innerHTML = [
    '<style>',
    ':host{all:initial;display:block}',
    '*{box-sizing:border-box;font-family:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}',
    '.w{display:flex;flex-direction:column;gap:.6rem;padding:1.1rem 1.2rem;border-radius:14px;',
    '  border:1px solid rgba(128,128,128,.28);background:rgba(128,128,128,.06)}',
    '.t{display:flex;align-items:center;gap:.5rem;font-size:.98rem;font-weight:650;color:inherit}',
    '.t svg{width:17px;height:17px;flex:none;opacity:.85}',
    '.s{font-size:.86rem;line-height:1.55;opacity:.75;margin:0}',
    'form{display:flex;gap:.5rem;flex-wrap:wrap;margin:.15rem 0 0}',
    'input{flex:1 1 200px;min-height:44px;padding:.55rem .75rem;border-radius:10px;font-size:.92rem;',
    '  border:1px solid rgba(128,128,128,.38);background:rgba(255,255,255,.06);color:inherit}',
    'input:focus{outline:none;border-color:currentColor}',
    'button{min-height:44px;padding:.55rem 1.05rem;border:0;border-radius:10px;cursor:pointer;',
    '  font-size:.9rem;font-weight:650;background:currentColor;color:transparent}',
    'button span{color:#fff;mix-blend-mode:normal}',
    '.btn2{min-height:44px;padding:.55rem 1.05rem;border-radius:10px;cursor:pointer;font-size:.9rem;',
    '  font-weight:650;border:1px solid currentColor;background:transparent;color:inherit}',
    '.m{font-size:.85rem;margin:.2rem 0 0;min-height:1.2em}',
    '</style>',
    '<div class="w">',
    '  <div class="t">',
    '    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 5.6 10 4.6v6.8H3zM11 4.4 21 3v8.4H11zM3 12.6h7v6.8L3 18.4zM11 12.6h10V21l-10-1.4z"/></svg>',
    '    Coming to Windows</div>',
    '  <p class="s">It is being built now. No date yet — leave an address and you will hear the day it works, and nothing else.</p>',
    '  <form novalidate>',
    '    <input type="email" required placeholder="you@example.com" aria-label="Email address">',
    '    <button class="btn2" type="submit">Tell me when</button>',
    '  </form>',
    '  <p class="m" role="status" aria-live="polite"></p>',
    '</div>'
  ].join("");

  var form = root.querySelector("form"), input = root.querySelector("input"),
      msg = root.querySelector(".m"), btn = root.querySelector("button");

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var v = (input.value || "").trim();
    if (!v || v.indexOf("@") < 0) { msg.textContent = "That does not look like an email address."; return; }
    btn.disabled = true; msg.textContent = "One moment…";
    fetch(API, {
      method: "POST", headers: { "Content-Type": "application/json" },
      /* A Windows waiting list is its OWN consent. Merging it with any other
         list would mean mailing these people about something they never asked
         for, and the source column is how that stays separable. */
      body: JSON.stringify({ email: v, source: host + "-windows" })
    }).then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (d && d.ok) { form.remove(); msg.textContent = "Done — you will hear the day it works."; }
        else { btn.disabled = false; msg.textContent = "That did not save. Try again in a moment."; }
      })
      /* Never a silent failure. Telling someone they are on a list they are not
         on is worse than telling them it did not work. */
      .catch(function () { btn.disabled = false; msg.textContent = "That did not save. Try again in a moment."; });
  });
})();
