/* ==========================================================================
   Deep Calls — core behaviour (loaded on every page)
   Theme, header state, scroll reveal, toast, back-to-top,
   share buttons and the Ctrl/Cmd+K search palette.
   Everything degrades gracefully: without this file the site is still a
   complete, readable set of linked pages.
   ========================================================================== */
(() => {
  "use strict";

  const root = document.documentElement;
  const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const siteRoot = root.dataset.root || "";
  const THEME_KEY = "deepcalls-theme";

  /** Lower-case and strip accents so "Ọlá" matches "ola". */
  const norm = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  const store = {
    get(key) {
      try { return localStorage.getItem(key); } catch { return null; }
    },
    set(key, value) {
      try { localStorage.setItem(key, value); } catch { /* storage unavailable: ignore */ }
    },
  };

  /* ---- Toast (polite live region declared in the page markup) ---- */
  let toastTimer;
  const toast = (message) => {
    const el = document.querySelector("[data-toast]");
    if (!el) return;
    el.textContent = message;
    el.dataset.show = "true";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.dataset.show = "false"; }, 2600);
  };

  window.DC = { norm, toast, store, siteRoot, prefersReducedMotion };

  /* ---- Theme ---- */
  const themeBtn = document.querySelector("[data-theme-toggle]");
  const setTheme = (theme) => {
    root.dataset.theme = theme;
    if (themeBtn) themeBtn.setAttribute("aria-pressed", String(theme === "dark"));
  };

  if (themeBtn) {
    setTheme(root.dataset.theme === "dark" ? "dark" : "light");
    themeBtn.addEventListener("click", () => {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      store.set(THEME_KEY, next);
      if (!prefersReducedMotion() && document.startViewTransition) {
        document.startViewTransition(() => setTheme(next));
      } else {
        root.classList.add("theme-anim");
        setTheme(next);
        setTimeout(() => root.classList.remove("theme-anim"), 350);
      }
    });
  }

  // Follow the operating system until the reader makes an explicit choice.
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (event) => {
    if (!store.get(THEME_KEY)) setTheme(event.matches ? "dark" : "light");
  });

  /* ---- Header: blur and shrink once the page scrolls ---- */
  const header = document.querySelector(".site-header");
  if (header) {
    let ticking = false;
    const update = () => {
      header.dataset.scrolled = String(window.scrollY > 8);
      ticking = false;
    };
    window.addEventListener("scroll", () => {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ---- Scroll reveal ---- */
  const revealEls = document.querySelectorAll("[data-reveal]");
  if (revealEls.length) {
    if (!("IntersectionObserver" in window) || prefersReducedMotion()) {
      revealEls.forEach((el) => el.classList.add("is-in"));
    } else {
      revealEls.forEach((el) => {
        const siblings = el.parentElement ? Array.from(el.parentElement.children) : [];
        el.style.setProperty("--i", String(Math.max(0, siblings.indexOf(el)) % 6));
      });
      const io = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
      revealEls.forEach((el) => io.observe(el));
    }
  }

  /* ---- Back to top ---- */
  const toTop = document.querySelector("[data-to-top]");
  if (toTop) {
    let ticking = false;
    window.addEventListener("scroll", () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        toTop.dataset.show = String(window.scrollY > 900);
        ticking = false;
      });
    }, { passive: true });
    toTop.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    });
  }

  /* ---- Footer year ---- */
  document.querySelectorAll("[data-year]").forEach((el) => { el.textContent = String(new Date().getFullYear()); });

  /* ---- Share / copy link ---- */
  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.className = "sr-only";
      document.body.appendChild(area);
      area.select();
      let ok = false;
      try { ok = document.execCommand("copy"); } catch { ok = false; }
      area.remove();
      return ok;
    }
  };
  window.DC.copyText = copyText;

  document.querySelectorAll("[data-copy-link]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const ok = await copyText(window.location.href.split("#")[0]);
      toast(ok ? "Link copied" : "Couldn’t copy the link. Copy it from the address bar.");
    });
  });

  document.querySelectorAll("[data-share-native]").forEach((btn) => {
    if (!navigator.share) { btn.hidden = true; return; }
    btn.addEventListener("click", () => {
      navigator.share({ title: document.title, url: window.location.href.split("#")[0] }).catch(() => {});
    });
  });

  /* ---- Search palette (Ctrl/Cmd + K, or "/") ---- */
  let palette = null;
  let index = null;
  let indexError = false;

  const buildPalette = () => {
    const dialog = document.createElement("dialog");
    dialog.className = "palette";
    dialog.setAttribute("aria-label", "Search essays");
    dialog.innerHTML = `
      <div class="palette__field">
        <svg class="i" aria-hidden="true" focusable="false"><use href="#i-search"/></svg>
        <input class="palette__input" type="search" role="combobox" aria-expanded="true"
          aria-controls="palette-results" aria-autocomplete="list" autocomplete="off" spellcheck="false"
          placeholder="Search essays by title, theme or idea" aria-label="Search essays">
      </div>
      <ul class="palette__results" id="palette-results" role="listbox" aria-label="Matching essays"></ul>
      <div class="palette__foot" aria-hidden="true">
        <span><kbd>↑</kbd> <kbd>↓</kbd> to move</span><span><kbd>Enter</kbd> to open</span><span><kbd>Esc</kbd> to close</span>
      </div>`;
    document.body.appendChild(dialog);

    const input = dialog.querySelector("input");
    const list = dialog.querySelector("ul");
    let active = -1;

    const options = () => Array.from(list.querySelectorAll("[role=option]"));
    const select = (i) => {
      const opts = options();
      if (!opts.length) { active = -1; input.removeAttribute("aria-activedescendant"); return; }
      active = (i + opts.length) % opts.length;
      opts.forEach((o, n) => o.setAttribute("aria-selected", String(n === active)));
      input.setAttribute("aria-activedescendant", opts[active].id);
      opts[active].scrollIntoView({ block: "nearest" });
    };

    const render = () => {
      list.replaceChildren();
      if (indexError) {
        list.innerHTML = `<li class="palette__status" role="presentation">Search couldn’t load. <a class="link" href="${siteRoot}library.html">Browse the library</a> instead.</li>`;
        return;
      }
      if (!index) {
        list.innerHTML = '<li role="presentation"><span class="skeleton"></span><span class="skeleton"></span><span class="skeleton"></span></li>';
        return;
      }
      const tokens = norm(input.value).split(/\s+/).filter(Boolean);
      let results;
      if (!tokens.length) {
        results = index.filter((e) => e.f).map((e) => ({ e, score: 0 }));
      } else {
        results = index.map((e) => {
          const title = norm(e.t), cat = norm(e.c);
          const rest = norm(`${e.s || ""} ${e.e || ""} ${e.v || ""}`);
          let score = 0;
          for (const t of tokens) {
            if (title.includes(t)) score += 3;
            else if (cat.includes(t)) score += 2;
            else if (rest.includes(t)) score += 1;
            else return null;
          }
          return { e, score };
        }).filter(Boolean).sort((a, b) => b.score - a.score || a.e.t.localeCompare(b.e.t));
      }
      if (!results.length) {
        list.innerHTML = '<li class="palette__empty" role="presentation">No essays match that. Try a different word.</li>';
        select(-1);
        return;
      }
      const label = tokens.length ? "" : '<li class="palette__status" role="presentation">Featured essays</li>';
      list.innerHTML = label + results.slice(0, 8).map(({ e }, n) => `
        <li class="palette__item" role="option" id="palette-opt-${n}" aria-selected="false">
          <a href="${siteRoot}${e.u}" tabindex="-1">
            <span class="palette__title"></span>
            <span class="palette__meta"></span>
          </a>
        </li>`).join("");
      options().forEach((li, n) => {
        const { e } = results[n];
        li.querySelector(".palette__title").textContent = e.t;
        li.querySelector(".palette__meta").textContent = `${e.c} · ${e.m} min read`;
      });
      select(0);
    };

    input.addEventListener("input", render);
    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") { event.preventDefault(); select(active + 1); }
      else if (event.key === "ArrowUp") { event.preventDefault(); select(active - 1); }
      else if (event.key === "Enter") {
        const opt = options()[active];
        if (opt) { event.preventDefault(); window.location.href = opt.querySelector("a").href; }
      }
    });
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
      const link = event.target.closest("a");
      if (link) dialog.close();
    });
    dialog.addEventListener("close", () => { document.body.style.removeProperty("overflow"); });
    dialog.render = render;
    return dialog;
  };

  const loadIndex = async () => {
    if (index || indexError) return;
    try {
      const response = await fetch(`${siteRoot}assets/search.json`);
      if (!response.ok) throw new Error(String(response.status));
      index = await response.json();
    } catch {
      indexError = true;
    }
    if (palette && palette.open) palette.render();
  };

  const openPalette = () => {
    if (!palette) palette = buildPalette();
    if (typeof palette.showModal !== "function") { window.location.href = `${siteRoot}library.html`; return; }
    if (!palette.open) palette.showModal();
    palette.render();
    palette.querySelector("input").focus();
    loadIndex();
  };

  document.querySelectorAll("[data-search-open]").forEach((el) => {
    el.addEventListener("click", (event) => { event.preventDefault(); openPalette(); });
  });

  document.addEventListener("keydown", (event) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test((event.target.tagName || "")) || event.target.isContentEditable;
    if ((event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      openPalette();
    } else if (event.key === "/" && !typing && !event.metaKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      openPalette();
    }
  });

  // Show the platform-appropriate shortcut hint.
  const mac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
  document.querySelectorAll("[data-kbd-hint]").forEach((el) => { el.textContent = mac ? "⌘K" : "Ctrl K"; });
})();
