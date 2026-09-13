(function () {
  function getPreferredTheme() {
    try {
      const stored = localStorage.getItem("yz-theme");
      if (stored === "light" || stored === "dark") return stored;
    } catch (_) {
      /* ignore */
    }
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
      return "light";
    }
    return "dark";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    const toggle = document.querySelector("[data-theme-toggle]");
    if (toggle) {
      toggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      toggle.setAttribute(
        "aria-label",
        theme === "dark" ? "Theme: dark" : "Theme: light"
      );
      const label = toggle.querySelector(".theme-toggle-label");
      if (label) label.textContent = theme === "dark" ? "Dark" : "Light";
    }
  }

  function initThemeToggle() {
    applyTheme(getPreferredTheme());
    const toggle = document.querySelector("[data-theme-toggle]");
    if (!toggle) return;
    toggle.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem("yz-theme", next);
      } catch (_) {
        /* ignore */
      }
    });
  }

  var READING_SIZES = ["default", "large", "xlarge"];
  var READING_LABELS = {
    default: "standard",
    large: "large",
    xlarge: "extra large",
  };
  var READING_HINTS = {
    default: "Click to make text larger.",
    large: "Click to make text extra large.",
    xlarge: "Click to reset text size to standard.",
  };

  function getPreferredReadingSize() {
    try {
      const stored = localStorage.getItem("yz-reading-size");
      if (READING_SIZES.indexOf(stored) !== -1) return stored;
    } catch (_) {
      /* ignore */
    }
    return "default";
  }

  function applyReadingSize(size) {
    const root = document.documentElement;
    if (size === "default") {
      root.removeAttribute("data-reading-size");
    } else {
      root.setAttribute("data-reading-size", size);
    }
    const toggle = document.querySelector("[data-reading-size-toggle]");
    if (toggle) {
      const pressed = size !== "default";
      toggle.setAttribute("aria-pressed", pressed ? "true" : "false");
      toggle.setAttribute(
        "aria-label",
        "Text size: " + READING_LABELS[size] + ". " + READING_HINTS[size]
      );
      toggle.setAttribute("title", READING_HINTS[size]);
      toggle.querySelectorAll(".reading-size-step").forEach(function (step) {
        step.classList.toggle(
          "is-active",
          step.getAttribute("data-step") === size
        );
      });
    }
  }

  function initReadingSizeToggle() {
    applyReadingSize(getPreferredReadingSize());
    const toggle = document.querySelector("[data-reading-size-toggle]");
    if (!toggle) return;
    toggle.addEventListener("click", () => {
      const current = getPreferredReadingSize();
      const index = READING_SIZES.indexOf(current);
      const next = READING_SIZES[(index + 1) % READING_SIZES.length];
      applyReadingSize(next);
      try {
        if (next === "default") {
          localStorage.removeItem("yz-reading-size");
        } else {
          localStorage.setItem("yz-reading-size", next);
        }
      } catch (_) {
        /* ignore */
      }
    });
  }

  function initHashRedirects() {
    const hash = window.location.hash.slice(1);
    if (!hash) return false;
    const target = document.getElementById(hash);
    if (!target) return false;
    const slide = target.closest("[data-library-slide]");
    if (!slide) return false;
    const deck = document.querySelector("[data-library-deck]");
    if (!deck) return false;
    const index = [...deck.querySelectorAll("[data-library-slide]")].indexOf(slide);
    if (index < 0) return false;
    deck.scrollTo({ left: index * deck.clientWidth, behavior: "instant" });
    return true;
  }

  function initLibraryShell() {
    const shell = document.querySelector(".library-shell");
    if (!shell) return;

    const split = shell.querySelector(".library-split");
    const overview = shell.querySelector(".library-overview");
    const backBtn = shell.querySelector(".library-back");
    const scroller = shell.querySelector(".library-panels");
    const panels = [...shell.querySelectorAll(".library-panel[data-panel-id]")];
    const indexItems = [
      ...shell.querySelectorAll(".library-index [data-panel-id][tabindex]"),
    ];
    const panelById = new Map(
      panels.map((panel) => [panel.getAttribute("data-panel-id"), panel])
    );
    let activeIndexId = null;

    function isMobileLayout() {
      return window.matchMedia("(max-width: 48rem)").matches;
    }

    function updateHash(indexId) {
      const base = window.location.pathname;
      if (indexId) {
        history.replaceState(null, "", `${base}#${encodeURIComponent(indexId)}`);
      } else if (window.location.hash) {
        history.replaceState(null, "", base);
      }
    }

    function setIndexHighlight(indexId) {
      indexItems.forEach((item) => {
        const match = item.getAttribute("data-panel-id") === indexId;
        item.classList.toggle("is-active", Boolean(match));
        if (match) item.setAttribute("aria-current", "location");
        else item.removeAttribute("aria-current");
      });
    }

    function syncBackButton() {
      if (!backBtn) return;
      backBtn.hidden = !activeIndexId || !isMobileLayout() || !split?.classList.contains("is-detail-open");
    }

    function scrollToAnchor(panel, anchorId) {
      if (!anchorId || !scroller || !panel) return;
      let el = null;
      try {
        el = panel.querySelector(`#${CSS.escape(anchorId)}`);
      } catch (_) {
        el = panel.querySelector(`[id="${anchorId}"]`);
      }
      if (!el) return;
      const scroll = () => {
        const top =
          el.getBoundingClientRect().top -
          scroller.getBoundingClientRect().top +
          scroller.scrollTop;
        scroller.scrollTo({ top: Math.max(0, top - 12), behavior: "smooth" });
      };
      requestAnimationFrame(() => {
        requestAnimationFrame(scroll);
      });
    }

    function resolveTarget(requestedId) {
      if (!requestedId) return null;
      if (panelById.has(requestedId)) {
        return { panelId: requestedId, anchorId: null, indexId: requestedId };
      }
      let group = null;
      try {
        group = shell.querySelector(
          `[data-panel-group-id="${CSS.escape(requestedId)}"]`
        );
      } catch (_) {
        group = shell.querySelector(`[data-panel-group-id="${requestedId}"]`);
      }
      if (group) {
        const first = group.querySelector("[data-panel-id][tabindex]");
        const firstId = first?.getAttribute("data-panel-id");
        if (firstId) return resolveTarget(firstId);
      }
      for (const panel of panels) {
        let anchor = null;
        try {
          anchor = panel.querySelector(`#${CSS.escape(requestedId)}`);
        } catch (_) {
          anchor = panel.querySelector(`[id="${requestedId}"]`);
        }
        if (anchor) {
          return {
            panelId: panel.getAttribute("data-panel-id"),
            anchorId: requestedId,
            indexId: requestedId,
          };
        }
      }
      return null;
    }

    function firstIndexId() {
      return indexItems[0]?.getAttribute("data-panel-id") || null;
    }

    function showOverview() {
      activeIndexId = null;
      panels.forEach((panel) => {
        panel.hidden = true;
        panel.classList.remove("is-active");
      });
      if (overview) overview.hidden = false;
      if (split) split.classList.remove("is-detail-open");
      setIndexHighlight(null);
      syncBackButton();
      updateHash(null);
    }

    function showPanel(target) {
      const panel = panelById.get(target.panelId);
      if (!panel) return;
      activeIndexId = target.indexId;
      panels.forEach((entry) => {
        const open = entry.getAttribute("data-panel-id") === target.panelId;
        entry.hidden = !open;
        entry.classList.toggle("is-active", open);
        if (open) {
          void entry.offsetWidth;
        }
      });
      if (overview) overview.hidden = true;
      if (split) split.classList.add("is-detail-open");
      setIndexHighlight(target.indexId);
      syncBackButton();
      updateHash(target.indexId);
      if (scroller && !target.anchorId) scroller.scrollTop = 0;
      if (target.anchorId) scrollToAnchor(panel, target.anchorId);
    }

    function activate(requestedId) {
      const resolved = resolveTarget(requestedId);
      if (resolved) {
        showPanel(resolved);
        return;
      }
      const first = firstIndexId();
      if (first) activate(first);
      else showOverview();
    }

    function applyHash() {
      const hashId = decodeURIComponent(window.location.hash.slice(1));
      if (hashId) {
        const resolved = resolveTarget(hashId);
        if (resolved) {
          showPanel(resolved);
          return;
        }
      }
      const first = firstIndexId();
      if (first) activate(first);
      else showOverview();
    }

    indexItems.forEach((item) => {
      const panelId = item.getAttribute("data-panel-id");
      item.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        activate(panelId);
      });
      item.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          activate(panelId);
        }
      });
    });

    if (backBtn) {
      backBtn.addEventListener("click", (event) => {
        event.preventDefault();
        if (split) split.classList.remove("is-detail-open");
        syncBackButton();
      });
    }

    shell.addEventListener("click", (event) => {
      if (event.target.closest("[data-library-back]")) {
        event.preventDefault();
        if (split) split.classList.remove("is-detail-open");
        syncBackButton();
      }
    });

    window.addEventListener("hashchange", applyHash);
    window.addEventListener("resize", syncBackButton);
    applyHash();
  }

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

    const headerOffset = getComputedStyle(document.documentElement)
      .getPropertyValue("--header-offset")
      .trim();
    const probe = document.createElement("div");
    probe.style.cssText =
      "position:absolute;visibility:hidden;pointer-events:none;height:calc(" +
      (headerOffset || "4.75rem") +
      " + 0.5rem)";
    document.documentElement.appendChild(probe);
    const offset = probe.getBoundingClientRect().height || 0;
    probe.remove();

    const pick = () => {
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

  function recordKindFromHref(href) {
    if (!href) return { label: "Rec", variant: "default" };
    try {
      const path = new URL(href, window.location.origin).pathname.replace(/\/$/, "") || "/";
      if (path === "/" || path === "/index.html") return { label: "Home", variant: "home" };
      if (path.startsWith("/systems") || path.startsWith("/portfolio") || path.startsWith("/work")) {
        return { label: "SYS", variant: "systems" };
      }
      if (path.startsWith("/notes") || path.startsWith("/perspectives")) {
        return { label: "Note", variant: "notes" };
      }
      if (path.startsWith("/about")) return { label: "Pro", variant: "profile" };
      if (path.startsWith("/credentials")) return { label: "Cred", variant: "credentials" };
      if (path.startsWith("/contact")) return { label: "Link", variant: "contact" };
    } catch (_) {
      /* ignore malformed href */
    }
    return { label: "Rec", variant: "default" };
  }

  function decorateSearchResultRow(row) {
    const link =
      row.querySelector(":scope > .pagefind-ui__result-inner .pagefind-ui__result-link") ||
      row.querySelector(":scope > .pagefind-ui__result-link") ||
      row.querySelector(".pagefind-ui__result-link");
    const href = link?.getAttribute("href") || "";
    const kind = recordKindFromHref(href);
    const badgeKey = `${kind.variant}:${kind.label}:${href}`;
    if (row.dataset.searchBadgeKey === badgeKey) return;

    let thumb = row.querySelector(":scope > .pagefind-ui__result-thumb");
    if (!thumb) {
      thumb = document.createElement("div");
      row.prepend(thumb);
    } else if (thumb !== row.firstElementChild) {
      row.prepend(thumb);
    }
    thumb.className = "pagefind-ui__result-thumb search-result-badge-slot";

    const existingImg = row.querySelector(
      ".pagefind-ui__result-image:not(.pagefind-ui__loading)"
    );
    const imgSrc = existingImg?.getAttribute("src") || "";
    const usePhoto = kind.variant === "profile" && imgSrc && !imgSrc.startsWith("data:");

    thumb.replaceChildren();
    if (usePhoto) {
      const img = document.createElement("img");
      img.className = "pagefind-ui__result-image search-result-photo";
      img.src = imgSrc;
      img.alt = "";
      img.decoding = "async";
      img.loading = "lazy";
      thumb.appendChild(img);
    } else {
      const badge = document.createElement("span");
      badge.className = `search-result-badge search-result-badge--${kind.variant}`;
      badge.textContent = kind.label;
      thumb.appendChild(badge);
    }
    row.dataset.searchBadgeKey = badgeKey;
  }

  function decorateSearchResults(root) {
    if (!root) return;
    root.querySelectorAll(".pagefind-ui__result").forEach(decorateSearchResultRow);
  }

  function initSearchResultBadges() {
    const mount = document.querySelector(".header-search #search");
    if (!mount) return;

    let observer = null;
    let scheduled = false;

    const run = () => {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(() => {
        scheduled = false;
        observer?.disconnect();
        decorateSearchResults(mount);
        observer?.observe(mount, { childList: true, subtree: true });
      });
    };

    observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        const target = mutation.target;
        if (target instanceof Element && target.closest(".search-result-badge-slot")) continue;
        run();
        return;
      }
    });

    decorateSearchResults(mount);
    observer.observe(mount, { childList: true, subtree: true });
  }

  function initChrome() {
    initThemeToggle();
    initReadingSizeToggle();
    if (initHashRedirects()) return;
    initLibraryShell();
    initTocSpy();
    initSearchResultBadges();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initChrome);
  } else {
    initChrome();
  }
})();
