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
  });
})();
