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
    const showIndexBtn = shell.querySelector(".library-index-show");
    const pinBtn = shell.querySelector(".library-index-pin");
    const hideBtn = shell.querySelector(".library-index-hide");
    const railExpandBtn = shell.querySelector(".library-index-rail-expand");
    const railPinBtn = shell.querySelector(".library-index-rail-pin");
    const scroller = shell.querySelector(".library-panels");
    const panels = [...shell.querySelectorAll(".library-panel[data-panel-id]")];
    const indexItems = [
      ...shell.querySelectorAll(".library-index .library-index-trigger[data-panel-id]"),
    ];
    const panelById = new Map(
      panels.map((panel) => [panel.getAttribute("data-panel-id"), panel])
    );

    function libraryIndexPinKey() {
      let path = window.location.pathname;
      if (!path.endsWith("/")) {
        const baseSlash = path.lastIndexOf("/");
        path = baseSlash >= 0 ? `${path.slice(0, baseSlash + 1)}` : "/";
      }
      return `yz-library-index-pinned:${path}`;
    }

    function defaultIndexPinnedForRoute() {
      return !window.location.pathname.includes("/notes/");
    }

    const INDEX_PIN_KEY = libraryIndexPinKey();
    let activeIndexId = null;
    let indexPinned = true;
    let indexDismissed = false;
    let indexHoverOpen = false;
    let indexHoverCloseTimer = null;
    const indexNav = shell.querySelector(".library-index");
    const libraryPane = shell.querySelector(".library-pane");
    const panelsRoot = shell.querySelector(".library-panels");
    let readingContext = libraryPane?.querySelector(".library-reading-context");

    if (libraryPane && panelsRoot && !readingContext) {
      readingContext = document.createElement("div");
      readingContext.className = "library-reading-context";
      readingContext.hidden = true;
      readingContext.innerHTML =
        '<button type="button" class="library-reading-context-title"></button>' +
        '<span class="library-reading-context-sep" aria-hidden="true">·</span>' +
        '<button type="button" class="library-reading-context-section"></button>';
      libraryPane.insertBefore(readingContext, panelsRoot);
    }

    const readingContextTitle = readingContext?.querySelector(
      ".library-reading-context-title"
    );
    const readingContextSection = readingContext?.querySelector(
      ".library-reading-context-section"
    );
    const readingContextSep = readingContext?.querySelector(
      ".library-reading-context-sep"
    );

    if (readingContextTitle) {
      readingContextTitle.setAttribute("aria-label", "Back to top of article");
    }
    if (readingContextSection) {
      readingContextSection.setAttribute("aria-label", "Jump to current section");
    }

    function isMobileLayout() {
      return window.matchMedia("(max-width: 48rem)").matches;
    }

    function isRailLayout() {
      return window.matchMedia("(min-width: 49rem)").matches;
    }

    function isIndexCollapsed() {
      return !isDrawerOpen();
    }

    function handleSplitEdgeHover(event) {
      if (isMobileLayout() || indexPinned || indexDismissed || !isIndexCollapsed()) {
        return;
      }
      const edge = split.getBoundingClientRect().left + 36;
      if (event.clientX <= edge) {
        openIndexHover();
      }
    }

    function syncPinControls() {
      const aria = indexPinned
        ? "Unpin table of contents panel"
        : "Pin table of contents panel";
      const title = indexPinned
        ? "Unpin panel (reveal on hover)"
        : "Pin panel (keep open)";
      if (pinBtn) {
        pinBtn.setAttribute("aria-pressed", indexPinned ? "true" : "false");
        pinBtn.title = title;
        pinBtn.setAttribute("aria-label", aria);
      }
      if (railPinBtn) {
        railPinBtn.setAttribute("aria-pressed", indexPinned ? "true" : "false");
        railPinBtn.title = title;
        railPinBtn.setAttribute("aria-label", aria);
      }
    }

    function readStoredBool(key, fallback) {
      try {
        const raw = localStorage.getItem(key);
        if (raw === "1") return true;
        if (raw === "0") return false;
      } catch (_) {
        /* ignore */
      }
      return fallback;
    }

    function writeStoredBool(key, value) {
      try {
        localStorage.setItem(key, value ? "1" : "0");
      } catch (_) {
        /* ignore */
      }
    }

    function isDrawerOpen() {
      if (indexDismissed) return false;
      if (indexPinned) return true;
      return indexHoverOpen;
    }

    function clearIndexHoverTimer() {
      if (indexHoverCloseTimer) {
        clearTimeout(indexHoverCloseTimer);
        indexHoverCloseTimer = null;
      }
    }

    function openIndexHover() {
      if (isMobileLayout() || indexPinned || indexDismissed) return;
      clearIndexHoverTimer();
      indexHoverOpen = true;
      syncIndexVisibility();
      scrollActiveIndexIntoView(activeIndexId);
    }

    function closeIndexHover() {
      if (isMobileLayout() || indexPinned || indexDismissed) return;
      clearIndexHoverTimer();
      indexHoverOpen = false;
      syncIndexVisibility();
    }

    function scheduleCloseIndexHover() {
      if (isMobileLayout() || indexPinned || indexDismissed) return;
      clearIndexHoverTimer();
      indexHoverCloseTimer = setTimeout(closeIndexHover, 220);
    }

    function syncIndexControls() {
      syncPinControls();
      const collapsed = !isDrawerOpen();
      const expanded = !collapsed;
      if (hideBtn) {
        hideBtn.hidden = collapsed;
        hideBtn.setAttribute("aria-pressed", "false");
        hideBtn.title = "Hide panel";
        hideBtn.setAttribute("aria-label", "Hide table of contents panel");
      }
      if (railExpandBtn) {
        railExpandBtn.setAttribute("aria-pressed", collapsed ? "false" : "true");
        railExpandBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
        railExpandBtn.title = indexDismissed
          ? "Show contents"
          : "Show contents (or hover the rail when unpinned)";
        railExpandBtn.setAttribute("aria-label", "Show table of contents");
      }
      if (showIndexBtn) {
        showIndexBtn.hidden = !collapsed || isMobileLayout() || isRailLayout();
        showIndexBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
      }
    }

    function isOverlayMode() {
      return isRailLayout() && !indexPinned;
    }

    function syncIndexVisibility() {
      if (!split) return;
      if (isMobileLayout()) {
        split.classList.remove("is-index-collapsed", "is-index-overlay-open", "is-index-unpinned");
        syncIndexControls();
        syncReadingContext();
        return;
      }
      const drawerOpen = isDrawerOpen();
      if (isOverlayMode()) {
        split.classList.add("is-index-collapsed", "is-index-unpinned");
        split.classList.toggle("is-index-overlay-open", drawerOpen);
      } else {
        split.classList.remove("is-index-overlay-open", "is-index-unpinned");
        split.classList.toggle("is-index-collapsed", !drawerOpen);
      }
      syncIndexControls();
      syncReadingContext();
    }

    function showIndexDrawer() {
      indexDismissed = false;
      if (!indexPinned) {
        indexHoverOpen = true;
      }
      syncIndexVisibility();
      scrollActiveIndexIntoView(activeIndexId);
    }

    function hideIndexDrawer() {
      indexDismissed = true;
      indexHoverOpen = false;
      clearIndexHoverTimer();
      syncIndexVisibility();
    }

    function setIndexPinned(next) {
      indexPinned = Boolean(next);
      writeStoredBool(INDEX_PIN_KEY, indexPinned);
      if (indexPinned) {
        indexDismissed = false;
      } else {
        indexHoverOpen = false;
      }
      syncIndexVisibility();
      if (indexPinned) scrollActiveIndexIntoView(activeIndexId);
    }

    indexPinned = readStoredBool(INDEX_PIN_KEY, defaultIndexPinnedForRoute());

    function parseInarticleToc(panelId) {
      const panel = panelById.get(panelId);
      if (!panel) return [];
      const raw = panel.getAttribute("data-inarticle-toc") || "";
      if (!raw) return [];
      try {
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
      } catch (_) {
        return [];
      }
    }

    function clearInarticleToc() {
      shell.querySelectorAll(".library-index-inarticle-wrap").forEach((node) => node.remove());
    }

    let panelScrollHandler = null;

    function unbindPanelScrollSpy() {
      if (panelScrollHandler && scroller) {
        scroller.removeEventListener("scroll", panelScrollHandler);
      }
      panelScrollHandler = null;
    }

    function bindPanelScrollSpy() {
      unbindPanelScrollSpy();
      if (!scroller) return;
      panelScrollHandler = () => {
        syncInarticleTocHighlight();
        syncReadingContext();
      };
      scroller.addEventListener("scroll", panelScrollHandler, { passive: true });
      panelScrollHandler();
    }

    function currentSectionHeading(panel) {
      if (!panel || !scroller) return null;
      const headings = [...panel.querySelectorAll(".note-section-heading[id]")];
      if (!headings.length) return null;
      const scrollerRect = scroller.getBoundingClientRect();
      const probe = 48;
      let current = headings[0];
      for (const heading of headings) {
        if (heading.getBoundingClientRect().top - scrollerRect.top <= probe) {
          current = heading;
        }
      }
      return current;
    }

    function shouldShowReadingContext() {
      if (!activeIndexId || !split?.classList.contains("is-detail-open")) return false;
      if (isMobileLayout()) return true;
      if (indexPinned) return false;
      return !isDrawerOpen();
    }

    function syncReadingContext() {
      if (!readingContext) return;
      const show = shouldShowReadingContext();
      readingContext.hidden = !show;
      split?.classList.toggle("is-reading-context-visible", show);
      if (!show || !activeIndexId) return;

      const panel = panelById.get(activeIndexId);
      if (!panel) return;

      const titleEl = panel.querySelector(".library-panel-title");
      if (readingContextTitle && titleEl) {
        readingContextTitle.textContent = titleEl.textContent.trim();
        readingContextTitle.onclick = (event) => {
          event.preventDefault();
          scrollPanelTop(activeIndexId);
        };
      }

      const section = currentSectionHeading(panel);
      if (readingContextSection && readingContextSep) {
        if (section) {
          readingContextSection.hidden = false;
          readingContextSep.hidden = false;
          readingContextSection.textContent = section.textContent.trim();
          readingContextSection.onclick = (event) => {
            event.preventDefault();
            scrollToAnchor(panel, section.id);
          };
        } else {
          readingContextSection.hidden = true;
          readingContextSep.hidden = true;
        }
      }
    }

    function syncInarticleTocHighlight() {
      if (!activeIndexId || !scroller) return;
      const panel = panelById.get(activeIndexId);
      if (!panel) return;
      const section = currentSectionHeading(panel);
      const links = [
        ...shell.querySelectorAll(
          ".library-index-inarticle-wrap .library-index-inarticle-link[data-anchor-id]"
        ),
      ];
      if (!section || !links.length) return;
      links.forEach((link) => {
        const match = link.getAttribute("data-anchor-id") === section.id;
        if (match) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    }

    function scrollPanelTop(panelId) {
      const panel = panelById.get(panelId);
      if (!panel) return;
      scrollToAnchor(panel, `${panelId}-top`);
    }

    function renderInarticleList(items, depth) {
      const ul = document.createElement("ul");
      ul.className = depth === 0 ? "library-index-inarticle" : "library-index-inarticle-sub";
      items.forEach((item) => {
        if (!item || !item.id) return;
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `library-index-inarticle-link library-index-inarticle-link--depth-${Math.min(depth, 2)}`;
        btn.textContent = item.label || item.id;
        btn.setAttribute("data-anchor-id", item.id);
        btn.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          const panel = panelById.get(activeIndexId);
          scrollToAnchor(panel, item.id);
        });
        li.appendChild(btn);
        const children = Array.isArray(item.children) ? item.children : [];
        if (children.length) {
          li.appendChild(renderInarticleList(children, depth + 1));
        }
        ul.appendChild(li);
      });
      return ul;
    }

    function renderInarticleToc(panelId) {
      clearInarticleToc();
      if (!panelId) return;
      const items = parseInarticleToc(panelId);
      if (!items.length) return;
      const trigger = indexItems.find(
        (item) => item.getAttribute("data-panel-id") === panelId
      );
      const row = trigger?.closest("li");
      if (!row) return;

      const wrap = document.createElement("div");
      wrap.className = "library-index-inarticle-wrap";

      const topBtn = document.createElement("button");
      topBtn.type = "button";
      topBtn.className = "library-index-inarticle-top";
      topBtn.textContent = "↑ Top";
      topBtn.setAttribute("aria-label", "Back to top of article");
      topBtn.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        scrollPanelTop(panelId);
      });
      wrap.appendChild(topBtn);
      wrap.appendChild(renderInarticleList(items, 0));
      row.appendChild(wrap);
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
        const row = item.closest("li");
        if (row) row.classList.toggle("is-active", Boolean(match));
        if (match) item.setAttribute("aria-current", "location");
        else item.removeAttribute("aria-current");
      });
    }

    function scrollActiveIndexIntoView(indexId) {
      if (!indexId) return;
      const indexBody = shell.querySelector(".library-index-body");
      if (!indexBody) return;
      const trigger = indexItems.find(
        (item) => item.getAttribute("data-panel-id") === indexId
      );
      const row = trigger?.closest("li");
      if (!row) return;

      const run = () => {
        const margin = 12;
        const bodyRect = indexBody.getBoundingClientRect();
        const rowRect = row.getBoundingClientRect();
        if (rowRect.top < bodyRect.top + margin) {
          indexBody.scrollTop += rowRect.top - bodyRect.top - margin;
        } else if (rowRect.bottom > bodyRect.bottom - margin) {
          indexBody.scrollTop += rowRect.bottom - bodyRect.bottom + margin;
        }
      };

      requestAnimationFrame(() => {
        requestAnimationFrame(run);
      });
    }

    function syncBackButton() {
      if (!backBtn) return;
      backBtn.hidden = !activeIndexId || !isMobileLayout() || !split?.classList.contains("is-detail-open");
    }

    function findAnchorInPanel(panel, requestedId) {
      if (!panel || !requestedId) return null;
      try {
        return panel.querySelector(`#${CSS.escape(requestedId)}`);
      } catch (_) {
        return panel.querySelector(`[id="${requestedId}"]`);
      }
    }

    function scrollToAnchor(panel, anchorId) {
      if (!anchorId || !scroller || !panel) return;
      const el = findAnchorInPanel(panel, anchorId);
      if (!el) return;
      const scroll = () => {
        const top =
          el.getBoundingClientRect().top -
          scroller.getBoundingClientRect().top +
          scroller.scrollTop;
        const stickyOffset =
          el.classList.contains("note-top-anchor") || anchorId.endsWith("-top") ? 0 : 12;
        const reduceMotion =
          window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        scroller.scrollTo({
          top: Math.max(0, top - stickyOffset),
          behavior: reduceMotion ? "auto" : "smooth",
        });
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
        const first = group.querySelector(".library-index-trigger[data-panel-id]");
        const firstId = first?.getAttribute("data-panel-id");
        if (firstId) return resolveTarget(firstId);
      }
      if (activeIndexId) {
        const activePanel = panelById.get(activeIndexId);
        if (activePanel && findAnchorInPanel(activePanel, requestedId)) {
          return {
            panelId: activeIndexId,
            anchorId: requestedId,
            indexId: activeIndexId,
          };
        }
      }
      for (const panel of panels) {
        if (findAnchorInPanel(panel, requestedId)) {
          return {
            panelId: panel.getAttribute("data-panel-id"),
            anchorId: requestedId,
            indexId: panel.getAttribute("data-panel-id"),
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
      if (!indexPinned) {
        indexHoverOpen = false;
      }
      panels.forEach((panel) => {
        panel.hidden = true;
        panel.classList.remove("is-active");
      });
      if (overview) overview.hidden = false;
      if (split) split.classList.remove("is-detail-open");
      setIndexHighlight(null);
      clearInarticleToc();
      unbindPanelScrollSpy();
      syncBackButton();
      syncIndexVisibility();
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
      renderInarticleToc(target.indexId);
      scrollActiveIndexIntoView(target.indexId);
      syncBackButton();
      syncIndexVisibility();
      updateHash(target.indexId);
      bindPanelScrollSpy();
      if (scroller && !target.anchorId) scroller.scrollTop = 0;
      if (target.anchorId) scrollToAnchor(panel, target.anchorId);
    }

    function activate(requestedId) {
      const resolved = resolveTarget(requestedId);
      if (resolved) {
        showPanel(resolved);
        return;
      }
      if (isMobileLayout()) {
        showOverview();
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
        if (activeIndexId && panelById.has(activeIndexId)) {
          return;
        }
      }
      if (isMobileLayout()) {
        showOverview();
        return;
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
        showOverview();
      });
    }

    if (pinBtn) {
      pinBtn.addEventListener("click", (event) => {
        event.preventDefault();
        setIndexPinned(!indexPinned);
      });
    }

    if (railExpandBtn) {
      railExpandBtn.addEventListener("click", (event) => {
        event.preventDefault();
        showIndexDrawer();
      });
    }

    if (railPinBtn) {
      railPinBtn.addEventListener("click", (event) => {
        event.preventDefault();
        setIndexPinned(!indexPinned);
      });
    }

    if (hideBtn) {
      hideBtn.addEventListener("click", (event) => {
        event.preventDefault();
        hideIndexDrawer();
      });
    }

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      if (!isDrawerOpen()) return;
      if (indexPinned && !isMobileLayout()) return;
      event.preventDefault();
      hideIndexDrawer();
    });

    if (showIndexBtn) {
      showIndexBtn.addEventListener("click", (event) => {
        event.preventDefault();
        showIndexDrawer();
      });
    }

    if (indexNav && isRailLayout()) {
      indexNav.addEventListener("mouseenter", openIndexHover);
      indexNav.addEventListener("mouseleave", scheduleCloseIndexHover);
      indexNav.addEventListener("focusin", openIndexHover);
      indexNav.addEventListener("focusout", (event) => {
        if (!indexNav.contains(event.relatedTarget)) {
          scheduleCloseIndexHover();
        }
      });
    }

    if (split && isRailLayout()) {
      split.addEventListener("mousemove", handleSplitEdgeHover);
    }

    shell.addEventListener("click", (event) => {
      if (event.target.closest("[data-library-back]")) {
        event.preventDefault();
        showOverview();
        return;
      }
      const link = event.target.closest(".note-body a[href^='#']");
      if (!link) return;
      const href = link.getAttribute("href") || "";
      if (href.length < 2) return;
      const anchorId = decodeURIComponent(href.slice(1));
      if (!anchorId || panelById.has(anchorId)) return;
      const panel = link.closest(".library-panel");
      if (!panel || panel.hidden) return;
      event.preventDefault();
      scrollToAnchor(panel, anchorId);
    });

    window.addEventListener("hashchange", applyHash);
    window.addEventListener("resize", () => {
      syncBackButton();
      syncIndexVisibility();
      if (isMobileLayout() && !window.location.hash) {
        showOverview();
      }
    });
    syncIndexControls();
    syncIndexVisibility();
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

  function siteBasePrefix() {
    const marker = document.querySelector('script[src*="chrome.js"]');
    const src = marker?.getAttribute("src") || "";
    const markerIndex = src.lastIndexOf("/chrome.js");
    if (markerIndex >= 0) return src.slice(0, markerIndex);
    const path = window.location.pathname;
    const known = ["/systems/", "/notes/", "/credentials/", "/about/", "/contact/", "/portfolio/", "/work/", "/perspectives/"];
    for (const route of known) {
      const idx = path.indexOf(route);
      if (idx > 0) return path.slice(0, idx);
    }
    return "";
  }

  function recordKindFromHref(href) {
    if (!href) return { label: "Rec", variant: "default" };
    try {
      let path = new URL(href, window.location.origin).pathname.replace(/\/$/, "") || "/";
      const base = siteBasePrefix();
      if (base && (path === base || path.startsWith(base + "/"))) {
        path = path.slice(base.length) || "/";
      }
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

  function initHomePacing() {
    const main = document.querySelector("main.home-route");
    if (!main) return;
    const sections = main.querySelectorAll(".home-snap-section");
    if (!sections.length) return;

    const reducedMotion =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!reducedMotion && "IntersectionObserver" in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            entry.target.classList.toggle("is-in-view", entry.isIntersecting);
          });
        },
        { root: null, rootMargin: "-12% 0px -28% 0px", threshold: 0.12 }
      );
      sections.forEach((section) => observer.observe(section));
    } else {
      sections.forEach((section) => section.classList.add("is-in-view"));
    }

    const strip = main.querySelector(".home-record-strip");
    if (!strip) return;
    strip.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      const cards = strip.querySelectorAll(".home-record-row");
      if (!cards.length) return;
      const gap = 16;
      const step = cards[0].getBoundingClientRect().width + gap;
      strip.scrollBy({
        left: event.key === "ArrowRight" ? step : -step,
        behavior: reducedMotion ? "auto" : "smooth",
      });
      event.preventDefault();
    });
  }

  function initChrome() {
    initThemeToggle();
    initReadingSizeToggle();
    if (initHashRedirects()) return;
    initLibraryShell();
    initTocSpy();
    initSearchResultBadges();
    initHomePacing();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initChrome);
  } else {
    initChrome();
  }
})();
