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
