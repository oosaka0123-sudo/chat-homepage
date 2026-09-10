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

  function initCopyButtons() {
    if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") return;

    var liveRegion = document.querySelector(".g-live-region");
    var targets = document.querySelectorAll("[data-copy]");

    targets.forEach(function (el) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "copy-btn";
      button.textContent = "コピー";
      button.setAttribute("aria-label", "文例をコピー");

      button.addEventListener("click", function () {
        var text = el.textContent.trim();
        navigator.clipboard.writeText(text).then(
          function () {
            var original = button.textContent;
            button.textContent = "コピーしました";
            announce(liveRegion, "文例をコピーしました");
            window.setTimeout(function () {
              button.textContent = original;
            }, 2000);
          },
          function () {
            /* Clipboard write failed; leave button state unchanged. */
          }
        );
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
