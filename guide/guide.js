(function () {
  "use strict";

  function initCurrentYear() {
    var el = document.getElementById("current-year");
    if (!el) return;
    el.textContent = String(new Date().getFullYear());
  }

  function announce(liveRegion, text) {
    if (!liveRegion) return;
    liveRegion.textContent = text;
  }

  function copyText(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      try { document.execCommand("copy") ? resolve() : reject(); } catch (error) { reject(error); }
      document.body.removeChild(area);
    });
  }

  function initCopyButtons() {
    var liveRegion = document.querySelector(".g-live-region");
    document.querySelectorAll("[data-copy]").forEach(function (el) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "copy-btn";
      button.textContent = "コピー";
      button.setAttribute("aria-label", "文例をコピー");
      button.addEventListener("click", function () {
        copyText(el.textContent.trim()).then(function () {
          button.textContent = "コピーしました";
          announce(liveRegion, "文例をコピーしました");
          window.setTimeout(function () { button.textContent = "コピー"; }, 2000);
        }, function () {
          button.textContent = "文章を長押ししてコピー";
          announce(liveRegion, "コピーできませんでした。文章を長押ししてコピーしてください");
          window.setTimeout(function () { button.textContent = "コピー"; }, 3500);
        });
      });
      el.insertAdjacentElement("afterend", button);
    });
  }

  function initDirectEditMobileFix() {
    if (!document.querySelector(".direct-hero")) return;
    var style = document.createElement("style");
    style.id = "direct-edit-mobile-fix";
    style.textContent = [
      "body:has(.direct-hero) .g-header{background:#050912!important;border-bottom:1px solid rgba(255,255,255,.10)!important;}",
      "body:has(.direct-hero) .g-header-inner{min-height:72px!important;gap:16px!important;}",
      "body:has(.direct-hero) .g-brand{min-width:0!important;gap:10px!important;}",
      "body:has(.direct-hero) .g-brand-logo{width:168px!important;height:auto!important;filter:brightness(0) invert(1)!important;opacity:.98!important;}",
      "body:has(.direct-hero) .g-section-label{font-size:.82rem!important;white-space:nowrap!important;}",
      "body:has(.direct-hero) .g-mini-nav{display:flex!important;align-items:center!important;gap:8px!important;}",
      "body:has(.direct-hero) .g-mini-nav a{display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:40px!important;padding:8px 12px!important;border:1px solid rgba(255,255,255,.16)!important;border-radius:999px!important;background:rgba(255,255,255,.06)!important;color:#fff!important;white-space:nowrap!important;text-decoration:none!important;}",
      "body:has(.direct-hero) .direct-hero h1{max-width:900px!important;line-height:1.00!important;letter-spacing:-.05em!important;}",
      "@media(max-width:820px){",
      "body:has(.direct-hero) .container{width:min(100% - 32px,1180px)!important;}",
      "body:has(.direct-hero) .g-header{position:relative!important;}",
      "body:has(.direct-hero) .g-header-inner{min-height:auto!important;padding:12px 0 14px!important;display:block!important;}",
      "body:has(.direct-hero) .g-brand{justify-content:center!important;}",
      "body:has(.direct-hero) .g-brand-logo{width:150px!important;filter:brightness(0) invert(1)!important;}",
      "body:has(.direct-hero) .g-section-label{display:none!important;}",
      "body:has(.direct-hero) .g-mini-nav{margin-top:10px!important;justify-content:center!important;gap:7px!important;overflow:visible!important;flex-wrap:wrap!important;}",
      "body:has(.direct-hero) .g-mini-nav a{flex:0 0 auto!important;min-height:36px!important;padding:7px 12px!important;background:rgba(255,255,255,.08)!important;color:#f7fbff!important;border-color:rgba(255,255,255,.18)!important;font-size:.78rem!important;line-height:1!important;}",
      "body:has(.direct-hero) .direct-hero{padding:58px 0 46px!important;min-height:auto!important;}",
      "body:has(.direct-hero) .direct-hero .eyebrow{font-size:.72rem!important;letter-spacing:.10em!important;margin-bottom:16px!important;}",
      "body:has(.direct-hero) .direct-hero h1{font-size:clamp(2.65rem,12vw,4.4rem)!important;line-height:1.02!important;letter-spacing:-.055em!important;margin:.2em 0 .38em!important;max-width:100%!important;word-break:keep-all!important;overflow-wrap:normal!important;}",
      "body:has(.direct-hero) .direct-hero h1 br{display:none!important;}",
      "body:has(.direct-hero) .direct-hero .lead{font-size:1rem!important;line-height:1.78!important;}",
      "body:has(.direct-hero) .direct-nav{display:grid!important;grid-template-columns:1fr!important;gap:10px!important;margin-top:26px!important;}",
      "body:has(.direct-hero) .direct-nav .btn{width:100%!important;min-height:54px!important;}",
      "body:has(.direct-hero) .hero-proof{gap:7px!important;margin-top:20px!important;}",
      "body:has(.direct-hero) .hero-proof span{font-size:.78rem!important;padding:8px 10px!important;}",
      "body:has(.direct-hero) .hero-orb{opacity:.28!important;}",
      "}",
      "@media(max-width:420px){",
      "body:has(.direct-hero) .g-brand-logo{width:136px!important;}",
      "body:has(.direct-hero) .g-mini-nav a{font-size:.74rem!important;padding:7px 10px!important;}",
      "body:has(.direct-hero) .direct-hero h1{font-size:clamp(2.35rem,11.5vw,3.35rem)!important;}",
      "}"
    ].join("\n");
    document.head.appendChild(style);
  }

  function safeInit(fn) {
    try {
      fn();
    } catch (error) {
      /* JS failures must never hide main content. */
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    safeInit(initCurrentYear);
    safeInit(initCopyButtons);
    safeInit(initDirectEditMobileFix);
  });
})();