/* The assistant, as ONE SCRIPT TAG.
 *
 * ⚠️ WHY THIS EXISTS. I made the worker multi-tenant, verified every origin got
 * its own prices, and reported the assistant as shipped across all five sites.
 * It was on ONE. The other four had a backend ready to answer questions nobody
 * could ask, because the widget only ever existed inside builtbykerr's index.html.
 *
 * I measured the mechanism and called it the artefact — the exact failure this
 * portfolio's notes describe over and over, committed by the person writing them.
 *
 * So the widget no longer lives in a page. It is served from the worker, and a
 * site adopts it with one line and no CSS, no markup, no copy to keep in sync:
 *
 *     <script src="https://kerr-lead-agent.kerrco.workers.dev/embed.js" defer></script>
 *
 * Everything is namespaced under .kcw- and injected into a shadow root, so it
 * cannot inherit or leak styles into whatever page it lands on. Four sites, four
 * different design systems, one widget that none of them can break.
 */
(function () {
  if (window.__kcAgentLoaded) return;
  window.__kcAgentLoaded = true;

  /* ⚠️ FIRST-PARTY ON PURPOSE. This file is served from crispvideo.app rather
   * than from the worker, because this site's pre-push gate refuses any
   * third-party <script src> that loads for every visitor — and it is right to.
   * The hero says "Nothing uploaded". A script fetched from another host on page
   * load contradicts the product on the axis it is sold on, whoever owns it.
   *
   * The ONLY third-party contact is the fetch below, and it fires strictly
   * inside the submit handler: a visitor types a question and presses send, and
   * that press is the only thing that leaves the page. Same shape the gate
   * already accepts for the subscribe form's POST.
   *
   * Because it is self-hosted it cannot read the API off its own src, so the
   * endpoint is explicit. Keep it in sync with ~/ops/lead-agent/widget/. */
  var API = "https://kerr-lead-agent.kerrco.workers.dev";

  var host = document.createElement("div");
  host.id = "kc-agent-host";
  host.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:2147483000";
  var root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;

  root.innerHTML = [
    '<style>',
    ':host{all:initial}',
    '*{box-sizing:border-box;font-family:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}',
    '.kcw-btn{display:inline-flex;align-items:center;gap:.5rem;min-height:44px;padding:.6rem 1.05rem;',
    '  border:0;border-radius:100px;background:#111114;color:#fff;font-size:.88rem;font-weight:600;',
    '  cursor:pointer;box-shadow:0 10px 30px rgba(0,0,0,.35);transition:transform .18s}',
    '.kcw-btn:hover{transform:translateY(-2px)}',
    '.kcw-panel{width:min(370px,calc(100vw - 2rem));max-height:min(560px,calc(100vh - 5rem));',
    '  display:flex;flex-direction:column;background:#fff;color:#17130c;border:1px solid #e4decf;',
    '  border-radius:16px;overflow:hidden;box-shadow:0 28px 70px rgba(0,0,0,.34)}',
    '.kcw-head{display:flex;align-items:center;justify-content:space-between;gap:.5rem;',
    '  padding:.8rem 1rem;border-bottom:1px solid #efe9dc;font-size:.9rem;font-weight:650}',
    '.kcw-x{border:0;background:none;font-size:1.2rem;line-height:1;cursor:pointer;color:#6b6152;',
    '  min-width:44px;min-height:44px}',
    '.kcw-log{flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:.7rem}',
    '.kcw-msg{font-size:.9rem;line-height:1.6;max-width:92%;padding:.6rem .8rem;border-radius:12px;white-space:pre-wrap}',
    '.kcw-a{background:#f5f2ea;color:#17130c;align-self:flex-start}',
    '.kcw-u{background:#111114;color:#fff;align-self:flex-end}',
    '.kcw-form{display:flex;gap:.5rem;padding:.8rem;border-top:1px solid #efe9dc}',
    '.kcw-form input{flex:1;min-height:44px;padding:.55rem .7rem;border:1px solid #e4decf;',
    '  border-radius:10px;font-size:.9rem;color:#17130c;background:#fff}',
    '.kcw-form input:focus{outline:none;border-color:#b8811f;box-shadow:0 0 0 3px rgba(184,129,31,.14)}',
    '.kcw-form button{min-height:44px;padding:.55rem 1rem;border:0;border-radius:10px;',
    '  background:#111114;color:#fff;font-weight:650;font-size:.88rem;cursor:pointer}',
    '.kcw-note{padding:0 1rem .8rem;font-size:.72rem;color:#6b6152;line-height:1.5}',
    '[hidden]{display:none!important}',
    '@media (prefers-reduced-motion:reduce){.kcw-btn{transition:none}}',
    '</style>',
    '<button class="kcw-btn" part="button" aria-haspopup="dialog">',
    '  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">',
    '    <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 9.9 9.9 0 0 1-4.2-.9L3 20.5l1.6-4.4A8.4 8.4 0 0 1 12 3.1a8.4 8.4 0 0 1 9 8.4z"/>',
    '  </svg> Ask a question</button>',
    '<div class="kcw-panel" role="dialog" aria-label="Ask a question" hidden>',
    '  <div class="kcw-head"><span>Ask a question</span><button class="kcw-x" aria-label="Close">&times;</button></div>',
    '  <div class="kcw-log"></div>',
    '  <form class="kcw-form"><input type="text" placeholder="Type your question" aria-label="Your question" maxlength="1500" required>',
    '  <button type="submit">Send</button></form>',
    '  <p class="kcw-note">Answers come from this page’s published prices and terms. It is an assistant, not a person.</p>',
    '</div>'
  ].join("");

  var btn = root.querySelector(".kcw-btn"), panel = root.querySelector(".kcw-panel"),
      log = root.querySelector(".kcw-log"), form = root.querySelector(".kcw-form"),
      input = form.querySelector("input"), close = root.querySelector(".kcw-x");
  var turns = [];

  function say(role, text) {
    var d = document.createElement("div");
    d.className = "kcw-msg " + (role === "user" ? "kcw-u" : "kcw-a");
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }
  function open(v) {
    panel.hidden = !v; btn.hidden = v;
    if (v) { input.focus(); if (!turns.length) say("assistant", "Ask me anything about the product, the price, or the licence."); }
  }
  btn.addEventListener("click", function () { open(true); });
  close.addEventListener("click", function () { open(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) open(false); });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;
    input.value = "";
    say("user", q);
    turns.push({ role: "user", content: q });
    var thinking = document.createElement("div");
    thinking.className = "kcw-msg kcw-a"; thinking.textContent = "…";
    log.appendChild(thinking); log.scrollTop = log.scrollHeight;

    fetch(API, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: turns.slice(-24) })
    }).then(function (r) { return r.json(); }).then(function (d) {
      thinking.remove();
      var a = d.reply || d.error || "I could not answer that just now.";
      say("assistant", a);
      turns.push({ role: "assistant", content: a });
    }).catch(function () {
      thinking.remove();
      /* Never a silent dead end. If the assistant cannot answer, the visitor
         still needs a way through — and that way is on the page they are on. */
      say("assistant", "I could not reach the server. The contact details on this page still work.");
    });
  });

  (document.body || document.documentElement).appendChild(host);
})();
