/* ==========================================================================
   Essay pages: reading progress, contents highlighting, select-to-quote
   ========================================================================== */
(() => {
  "use strict";

  const prose = document.querySelector("[data-prose]");
  if (!prose) return;

  const DC = window.DC || {};

  /* ---- Reading progress ---- */
  const bar = document.querySelector("[data-progress]");
  if (bar) {
    let ticking = false;
    const update = () => {
      const rect = prose.getBoundingClientRect();
      const scrollable = rect.height - window.innerHeight * 0.6;
      const progress = scrollable > 0 ? Math.min(1, Math.max(0, -rect.top / scrollable)) : 0;
      bar.style.setProperty("--p", progress.toFixed(4));
      ticking = false;
    };
    window.addEventListener("scroll", () => {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  /* ---- Contents: collapse on small screens, highlight the current section ---- */
  const toc = document.querySelector("[data-toc]");
  if (toc) {
    const wide = window.matchMedia("(min-width: 72rem)");
    toc.open = wide.matches;
    toc.dataset.ready = "true";
    wide.addEventListener("change", (event) => { toc.open = event.matches; });

    const links = Array.from(toc.querySelectorAll("a[href^='#']"));
    const byId = new Map(links.map((a) => [decodeURIComponent(a.getAttribute("href").slice(1)), a]));
    const headings = Array.from(prose.querySelectorAll("h2[id]")).filter((h) => byId.has(h.id));

    if (headings.length) {
      // The current section is the last heading that has scrolled past 30% of the viewport.
      let current = null;
      let ticking = false;
      const update = () => {
        const line = window.innerHeight * 0.3;
        let found = null;
        for (const h of headings) {
          if (h.getBoundingClientRect().top <= line) found = h; else break;
        }
        if (found !== current) {
          current = found;
          links.forEach((a) => a.removeAttribute("aria-current"));
          if (found) byId.get(found.id).setAttribute("aria-current", "true");
        }
        ticking = false;
      };
      window.addEventListener("scroll", () => {
        if (!ticking) { ticking = true; requestAnimationFrame(update); }
      }, { passive: true });
      window.addEventListener("resize", update);
      update();
    }
  }

  /* ---- Select-to-quote (mouse and trackpad only; touch has native menus) ---- */
  if (window.matchMedia("(pointer: fine)").matches) {
    const pop = document.createElement("div");
    pop.className = "quote-pop";
    pop.innerHTML = '<button type="button"><svg class="i" aria-hidden="true" focusable="false"><use href="#i-copy"/></svg>Copy quote</button>';
    document.body.appendChild(pop);
    let pending = "";

    const hide = () => { pop.dataset.show = "false"; };
    const place = () => {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || !selection.rangeCount) return hide();
      const text = selection.toString().trim();
      const range = selection.getRangeAt(0);
      if (text.length < 12 || text.length > 700 || !prose.contains(range.commonAncestorContainer)) return hide();
      const rect = range.getBoundingClientRect();
      if (!rect.width && !rect.height) return hide();
      pending = text;
      pop.style.top = `${Math.max(8, rect.top + window.scrollY - 48)}px`;
      pop.style.left = `${rect.left + window.scrollX + rect.width / 2}px`;
      pop.dataset.show = "true";
    };

    document.addEventListener("mouseup", () => setTimeout(place, 0));
    document.addEventListener("keyup", (event) => { if (event.shiftKey) place(); });
    document.addEventListener("scroll", hide, { passive: true });
    document.addEventListener("mousedown", (event) => { if (!pop.contains(event.target)) hide(); });

    pop.querySelector("button").addEventListener("click", async () => {
      const title = document.querySelector("h1") ? document.querySelector("h1").textContent.trim() : document.title;
      const text = `“${pending}”\n— ${title}, Deep Calls\n${window.location.href.split("#")[0]}`;
      const ok = DC.copyText ? await DC.copyText(text) : false;
      if (DC.toast) DC.toast(ok ? "Quote copied" : "Couldn’t copy the quote");
      hide();
      const selection = window.getSelection();
      if (selection) selection.removeAllRanges();
    });
  }
})();
