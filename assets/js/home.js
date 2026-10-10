/* ==========================================================================
   Home: rotating scripture panel
   Slides are real markup (the first is readable without JavaScript). This
   script only cross-fades between them, with a pause control, dot
   navigation, and no motion at all for readers who prefer reduced motion.
   ========================================================================== */
(() => {
  "use strict";

  const panel = document.querySelector("[data-verses]");
  if (!panel) return;

  const slides = Array.from(panel.querySelectorAll(".verse"));
  const dots = Array.from(panel.querySelectorAll("[data-verse-dot]"));
  const pauseBtn = panel.querySelector("[data-verse-pause]");
  const live = panel.querySelector("[data-verse-live]");
  if (slides.length < 2) {
    if (pauseBtn) pauseBtn.hidden = true;
    return;
  }

  const INTERVAL = 9000;
  let current = 0;
  let timer = null;
  let paused = window.DC ? window.DC.prefersReducedMotion() : false;
  let hovering = false;

  const show = (index) => {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, n) => {
      slide.dataset.active = String(n === current);
      slide.setAttribute("aria-hidden", String(n !== current));
    });
    dots.forEach((dot, n) => dot.setAttribute("aria-current", String(n === current)));
  };

  const stop = () => { clearInterval(timer); timer = null; };
  const start = () => {
    stop();
    if (paused || hovering || document.hidden) return;
    timer = setInterval(() => show(current + 1), INTERVAL);
  };

  const syncPause = () => {
    if (pauseBtn) {
      pauseBtn.setAttribute("aria-pressed", String(paused));
      pauseBtn.setAttribute("aria-label", paused ? "Play verse rotation" : "Pause verse rotation");
    }
    // Announce slide changes only when the reader is driving them.
    if (live) live.setAttribute("aria-live", paused ? "polite" : "off");
  };

  show(0);
  syncPause();
  start();

  dots.forEach((dot, n) => dot.addEventListener("click", () => { show(n); start(); }));
  if (pauseBtn) {
    pauseBtn.addEventListener("click", () => { paused = !paused; syncPause(); start(); });
  }
  panel.addEventListener("mouseenter", () => { hovering = true; stop(); });
  panel.addEventListener("mouseleave", () => { hovering = false; start(); });
  panel.addEventListener("focusin", () => { hovering = true; stop(); });
  panel.addEventListener("focusout", () => { hovering = false; start(); });
  document.addEventListener("visibilitychange", start);
})();
