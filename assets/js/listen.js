/* ==========================================================================
   Listen to this essay (browser speech synthesis)
   Client-side only: no server, no audio files. The control hides itself in
   browsers that cannot speak. The essay is read in short segments, which
   lets us highlight the paragraph being read, show progress, and avoid the
   bug in several mobile browsers where one long utterance simply stops.
   ========================================================================== */
(() => {
  "use strict";

  const widget = document.querySelector("[data-listen]");
  const prose = document.querySelector("[data-prose]");
  if (!widget || !prose) return;

  if (!("speechSynthesis" in window) || typeof SpeechSynthesisUtterance === "undefined") {
    widget.hidden = true;
    return;
  }
  widget.hidden = false;

  const synth = window.speechSynthesis;
  const toggle = widget.querySelector("[data-listen-toggle]");
  const controls = widget.querySelector("[data-listen-controls]");
  const playPause = widget.querySelector("[data-listen-playpause]");
  const stopBtn = widget.querySelector("[data-listen-stop]");
  const speedBtn = widget.querySelector("[data-listen-speed]");
  const progressEl = widget.querySelector("[data-listen-progress]");
  const toast = (msg) => { if (window.DC) window.DC.toast(msg); };

  // Read headings, paragraphs and list items; skip the reference lists.
  const blocks = Array.from(prose.querySelectorAll("h2, h3, p, li"))
    .filter((el) => !el.closest(".refs") && el.textContent.trim().length > 0);

  // Split each block into sentence groups of roughly 240 characters.
  const segments = [];
  blocks.forEach((el, blockIndex) => {
    const sentences = el.textContent.replace(/\s+/g, " ").trim().match(/[^.!?…]+[.!?…]+["'”’)]*\s*|[^.!?…]+$/g) || [];
    let chunk = "";
    sentences.forEach((sentence) => {
      if (chunk && (chunk + sentence).length > 240) {
        segments.push({ blockIndex, text: chunk.trim() });
        chunk = "";
      }
      chunk += sentence;
    });
    if (chunk.trim()) segments.push({ blockIndex, text: chunk.trim() });
  });

  const speeds = [1, 1.25, 1.5, 0.8];
  let speedIndex = 0;
  let position = 0;
  let state = "idle"; // idle | playing | paused
  let highlighted = -1;

  const pickVoice = () => {
    const voices = synth.getVoices() || [];
    const lang = (document.documentElement.lang || "en").toLowerCase();
    return voices.find((v) => v.lang.toLowerCase().startsWith(lang) && v.localService)
      || voices.find((v) => v.lang.toLowerCase().startsWith(lang))
      || null;
  };

  const clearHighlight = () => {
    if (highlighted >= 0 && blocks[highlighted]) blocks[highlighted].classList.remove("is-reading");
    highlighted = -1;
  };

  const highlight = (blockIndex) => {
    if (blockIndex === highlighted) return;
    clearHighlight();
    highlighted = blockIndex;
    const el = blocks[blockIndex];
    if (!el) return;
    el.classList.add("is-reading");
    const rect = el.getBoundingClientRect();
    const margin = 120;
    if (rect.top < margin || rect.bottom > window.innerHeight - 40) {
      const behavior = window.DC && window.DC.prefersReducedMotion() ? "auto" : "smooth";
      window.scrollTo({ top: window.scrollY + rect.top - margin, behavior });
    }
  };

  const render = () => {
    playPause.dataset.state = state;
    playPause.setAttribute("aria-label", state === "playing" ? "Pause" : "Play");
    progressEl.textContent = state === "idle" ? "" : `${Math.min(position + 1, segments.length)} / ${segments.length}`;
  };

  const speak = () => {
    if (position >= segments.length) { stop(); return; }
    const segment = segments[position];
    const utterance = new SpeechSynthesisUtterance(segment.text);
    utterance.rate = speeds[speedIndex];
    utterance.lang = document.documentElement.lang || "en";
    const voice = pickVoice();
    if (voice) utterance.voice = voice;
    utterance.onend = () => {
      if (state !== "playing") return;
      position += 1;
      speak();
    };
    utterance.onerror = (event) => {
      if (event.error === "canceled" || event.error === "interrupted") return;
      toast("Audio isn’t available in this browser.");
      stop();
    };
    highlight(segment.blockIndex);
    render();
    synth.speak(utterance);
  };

  const play = () => { state = "playing"; synth.cancel(); speak(); };
  // Pause by cancelling and remembering the segment: far more reliable across browsers than synth.pause().
  const pause = () => { state = "paused"; synth.cancel(); render(); };
  function stop() {
    state = "idle";
    synth.cancel();
    clearHighlight();
    position = 0;
    render();
  }

  toggle.addEventListener("click", () => {
    const opening = controls.hidden;
    controls.hidden = !opening;
    toggle.setAttribute("aria-expanded", String(opening));
    if (opening) play(); else stop();
  });
  playPause.addEventListener("click", () => { if (state === "playing") pause(); else play(); });
  stopBtn.addEventListener("click", () => { stop(); controls.hidden = true; toggle.setAttribute("aria-expanded", "false"); });
  speedBtn.addEventListener("click", () => {
    speedIndex = (speedIndex + 1) % speeds.length;
    speedBtn.textContent = `${speeds[speedIndex]}×`;
    if (state === "playing") { synth.cancel(); speak(); }
  });

  // Never keep talking after the reader leaves or hides the page.
  window.addEventListener("pagehide", () => synth.cancel());
  document.addEventListener("visibilitychange", () => { if (document.hidden && state === "playing") pause(); });
  render();
})();
