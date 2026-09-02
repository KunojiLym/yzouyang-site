/**
 * Horizontal deck behavior for /career-journey/.
 *
 * Without JS, slides remain readable in document order. With JS, the slide
 * rail becomes a keyboardable snap deck with previous/next controls, chapter
 * jumps, and an active-slide class used by CSS motion.
 */
(function () {
  var stage = document.querySelector(".cj-stage");
  var container = document.querySelector(".cj-slides");
  if (!stage || !container) return;

  var slides = Array.prototype.slice.call(container.querySelectorAll(".cj-slide"));
  if (!slides.length) return;

  var prev = stage.querySelector("[data-cj-prev]");
  var next = stage.querySelector("[data-cj-next]");
  var resetBtn = stage.querySelector("[data-cj-reset]");
  var gotoInput = stage.querySelector("[data-cj-goto]");
  var current = stage.querySelector("[data-cj-current]");
  var chapterLinks = Array.prototype.slice.call(document.querySelectorAll(".cj-chapters a"));
  var activeIndex = 0;
  var ticking = false;

  var slideStepCounts = slides.map(function (slide) {
    return parseInt(slide.getAttribute("data-steps") || "0", 10);
  });
  var slideCurrentSteps = slides.map(function () { return 0; });

  container.classList.add("cj-js");

  var reduceMotion = !!(
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );

  function clampIndex(index) {
    return Math.max(0, Math.min(slides.length - 1, index));
  }

  function slideLeft(index) {
    return slides[index].offsetLeft - container.offsetLeft;
  }

  function nearestIndex() {
    var left = container.scrollLeft;
    var best = 0;
    var bestDistance = Infinity;
    slides.forEach(function (slide, index) {
      var distance = Math.abs(slide.offsetLeft - container.offsetLeft - left);
      if (distance < bestDistance) {
        best = index;
        bestDistance = distance;
      }
    });
    return best;
  }

  function revealStep(slideIndex, step) {
    var slide = slides[slideIndex];
    var steppedEls = Array.prototype.slice.call(slide.querySelectorAll("[data-step]"));
    steppedEls.forEach(function (el) {
      var elStep = parseInt(el.getAttribute("data-step") || "0", 10);
      el.classList.toggle("is-revealed", reduceMotion || elStep <= step);
    });
    slideCurrentSteps[slideIndex] = reduceMotion ? (slideStepCounts[slideIndex] || 0) : step;
  }

  function setActive(index) {
    activeIndex = clampIndex(index);
    slides.forEach(function (slide, i) {
      var active = i === activeIndex;
      slide.classList.toggle("is-active", active);
      slide.classList.toggle("is-in", active);
      slide.setAttribute("aria-hidden", active ? "false" : "true");
      if (active) revealStep(i, slideCurrentSteps[i]);
    });
    if (prev) prev.disabled = activeIndex === 0 && (reduceMotion || slideCurrentSteps[activeIndex] === 0);
    if (next) next.disabled = activeIndex === slides.length - 1 && (reduceMotion || slideCurrentSteps[activeIndex] >= slideStepCounts[activeIndex]);
    if (current) current.textContent = "Slide " + String(activeIndex + 1) + " of " + slides.length;
    if (gotoInput) gotoInput.value = String(activeIndex + 1);
  }

  function goTo(index, behavior) {
    var target = clampIndex(index);
    container.scrollTo({
      left: slideLeft(target),
      behavior: behavior || "smooth",
    });
    setActive(target);
  }

  function requestActiveFromScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      setActive(nearestIndex());
    });
  }

  if (prev) {
    prev.addEventListener("click", function () {
      if (!reduceMotion && slideCurrentSteps[activeIndex] > 0) {
        revealStep(activeIndex, slideCurrentSteps[activeIndex] - 1);
        if (prev) prev.disabled = activeIndex === 0 && slideCurrentSteps[activeIndex] === 0;
        if (next) next.disabled = false;
      } else {
        goTo(activeIndex - 1);
      }
    });
  }

  if (next) {
    next.addEventListener("click", function () {
      var maxSteps = slideStepCounts[activeIndex];
      if (!reduceMotion && maxSteps > 0 && slideCurrentSteps[activeIndex] < maxSteps) {
        revealStep(activeIndex, slideCurrentSteps[activeIndex] + 1);
        if (prev) prev.disabled = false;
        if (next) next.disabled = activeIndex === slides.length - 1 && slideCurrentSteps[activeIndex] >= maxSteps;
      } else {
        goTo(activeIndex + 1);
      }
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      slides.forEach(function (slide, i) {
        if (reduceMotion) {
          revealStep(i, slideStepCounts[i]);
        } else {
          slideCurrentSteps[i] = 0;
          var steppedEls = Array.prototype.slice.call(slide.querySelectorAll("[data-step]"));
          steppedEls.forEach(function (el) { el.classList.remove("is-revealed"); });
        }
      });
      goTo(0);
    });
  }

  if (gotoInput) {
    gotoInput.addEventListener("change", function () {
      var n = parseInt(gotoInput.value, 10);
      if (!isNaN(n)) goTo(clampIndex(n - 1));
    });
  }

  chapterLinks.forEach(function (link) {
    link.addEventListener("click", function (event) {
      var id = decodeURIComponent((link.getAttribute("href") || "").replace(/^#/, ""));
      var target = slides.findIndex(function (slide) {
        return slide.id === id;
      });
      if (target < 0) return;
      event.preventDefault();
      goTo(target);
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, "", "#" + id);
      }
    });
  });

  container.addEventListener("scroll", requestActiveFromScroll, { passive: true });
  container.addEventListener("keydown", function (event) {
    if (event.key === "ArrowRight" || event.key === "PageDown") {
      event.preventDefault();
      goTo(activeIndex + 1);
    }
    if (event.key === "ArrowLeft" || event.key === "PageUp") {
      event.preventDefault();
      goTo(activeIndex - 1);
    }
    if (event.key === "Home") {
      event.preventDefault();
      goTo(0);
    }
    if (event.key === "End") {
      event.preventDefault();
      goTo(slides.length - 1);
    }
  });

  var hashIndex = -1;
  if (window.location.hash) {
    var hash = decodeURIComponent(window.location.hash.slice(1));
    hashIndex = slides.findIndex(function (slide) {
      return slide.id === hash;
    });
  }

  if (reduceMotion) {
    slides.forEach(function (_slide, i) {
      revealStep(i, slideStepCounts[i]);
    });
  }

  setActive(hashIndex >= 0 ? hashIndex : 0);
  if (hashIndex >= 0) goTo(hashIndex, "auto");
})();
