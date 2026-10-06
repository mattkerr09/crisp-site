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

/* "On your phone? Send the Mac link to yourself" in the product box on every guide (content standard,
   2026-10-05). The homepage wires its own two buttons inline, so this binds only inside .pbox. The link is
   this page, tagged phone-share, carrying where the visitor came from (the hub snippet's kc_aff: ?ref=producthunt
   is kept as landing_source) so the Mac visit still counts for its source. Share sheet, else an email to self. */
(function () {
  function kcCarry(url) { try { var s = JSON.parse(localStorage.getItem('kc_aff') || 'null'); var v = (s && s.exp > Date.now() && s.v) || {}; var q = []; var r = v.ref || v.landing_source; if (r) q.push('ref=' + encodeURIComponent(r)); ['via', 'rekomi_ref', 'affonso_referral', 'awc', 'cjevent', 'irclickid'].forEach(function (k) { if (v[k]) q.push(k + '=' + encodeURIComponent(v[k])); }); return q.length ? url + '&' + q.join('&') : url; } catch (e) { return url; } }
  function bind() {
    document.querySelectorAll('.pbox [data-send-mac-link]').forEach(function (b) {
      b.addEventListener('click', function () {
        var url = kcCarry(location.origin + location.pathname + '?utm_source=phone-share&utm_medium=share');
        var text = 'Crisp Video for Mac is free, with the full editor, 4K upscaling and a small “Made with Crisp” mark on video exports. Open this on your Mac to download it.';
        try { window.plausible('Send Mac Link'); } catch (e) {}
        if (navigator.share) { navigator.share({ title: 'Crisp Video for Mac', text: text, url: url }).catch(function () {}); }
        else { location.href = 'mailto:?subject=' + encodeURIComponent('Crisp Video for Mac: download link') + '&body=' + encodeURIComponent(text + '\n\n' + url); }
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind); else bind();
})();
