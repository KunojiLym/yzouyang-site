/* Header theme toggle + long-form TOC active underline. */
(function () {
  const KEY = "yz-theme";

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "light"
      ? "light"
      : "dark";
  }

  function syncToggle(theme) {
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
      const light = theme === "light";
      btn.setAttribute("aria-pressed", light ? "true" : "false");
      btn.setAttribute("aria-label", light ? "Theme: light" : "Theme: dark");
      const label = btn.querySelector(".theme-toggle-label");
      if (label) label.textContent = light ? "Light" : "Dark";
    });
  }

  function applyTheme(theme) {
    const next = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* private mode */
    }
    syncToggle(next);
  }

  document.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-theme-toggle]");
    if (!btn) return;
    applyTheme(currentTheme() === "light" ? "dark" : "light");
  });

  syncToggle(currentTheme());

  function initTocSpy() {
    const toc = document.querySelector(".page-toc");
    if (!toc) return;
    const links = [...toc.querySelectorAll('a[href^="#"]')];
    if (!links.length) return;

    const targets = [];
    for (const link of links) {
      const id = decodeURIComponent((link.getAttribute("href") || "").slice(1));
      if (!id) continue;
      const el = document.getElementById(id);
      if (el) targets.push({ el, link });
    }
    if (!targets.length) return;

    const setActive = (activeLink) => {
      for (const { link } of targets) {
        if (link === activeLink) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      }
    };

    const pick = () => {
      const offset = 96;
      let current = targets[0];
      for (const item of targets) {
        const top = item.el.getBoundingClientRect().top;
        if (top - offset <= 0) current = item;
      }
      setActive(current.link);
    };

    pick();
    window.addEventListener("scroll", pick, { passive: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTocSpy);
  } else {
    initTocSpy();
  }
})();
