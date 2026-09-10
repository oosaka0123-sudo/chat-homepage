(function () {
  "use strict";

  function initNavToggle() {
    var toggle = document.getElementById("nav-toggle");
    var nav = document.getElementById("site-nav");
    if (!toggle || !nav) return;

    toggle.addEventListener("click", function () {
      var isOpen = nav.getAttribute("data-open") === "true";
      nav.setAttribute("data-open", String(!isOpen));
      toggle.setAttribute("aria-expanded", String(!isOpen));
    });

    nav.addEventListener("click", function (event) {
      if (event.target.tagName === "A") {
        nav.setAttribute("data-open", "false");
        toggle.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.getAttribute("data-open") === "true") {
        nav.setAttribute("data-open", "false");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  function initCurrentYear() {
    var el = document.getElementById("current-year");
    if (!el) return;
    el.textContent = String(new Date().getFullYear());
  }

  function initRevealOnScroll() {
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion || typeof IntersectionObserver === "undefined") return;

    var targets = document.querySelectorAll(".section > .container > h2");
    if (!targets.length) return;

    targets.forEach(function (el) {
      el.classList.add("reveal-init");
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.2 }
    );

    targets.forEach(function (el) {
      observer.observe(el);
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
    safeInit(initNavToggle);
    safeInit(initCurrentYear);
    safeInit(initRevealOnScroll);
  });
})();
