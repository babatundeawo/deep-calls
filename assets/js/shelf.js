/* ==========================================================================
   Shelf: saved essays, text size, continue reading, and a random essay.
   Everything is stored in this browser only (localStorage). Without
   JavaScript, or without storage, the site is still complete.
   ========================================================================== */
(() => {
  "use strict";

  const DC = window.DC;
  if (!DC) return;

  const SAVED_KEY = "deepcalls-saved";
  const SIZE_KEY = "deepcalls-textsize";
  const LAST_KEY = "deepcalls-last";
  const listeners = [];

  const read = (key, fallback) => {
    try { return JSON.parse(DC.store.get(key)) ?? fallback; } catch { return fallback; }
  };
  const write = (key, value) => DC.store.set(key, JSON.stringify(value));

  /* ---- Saved essays ---- */
  const saved = () => {
    const list = read(SAVED_KEY, []);
    return Array.isArray(list) ? list.filter((s) => typeof s === "string") : [];
  };
  const has = (slug) => saved().includes(slug);
  const paint = () => {
    const count = saved().length;
    document.querySelectorAll("[data-saved-count]").forEach((el) => {
      el.textContent = String(count);
      if (el.classList.contains("tabbar__badge")) el.hidden = count === 0;
    });
    document.querySelectorAll("[data-save]").forEach((btn) => {
      const on = has(btn.dataset.save);
      btn.setAttribute("aria-pressed", String(on));
      const label = btn.querySelector("[data-save-label]");
      if (label) label.textContent = on ? "Saved" : "Save for later";
    });
    listeners.forEach((fn) => fn());
  };
  const toggle = (slug) => {
    const list = saved();
    const at = list.indexOf(slug);
    if (at >= 0) list.splice(at, 1); else list.push(slug);
    write(SAVED_KEY, list);
    paint();
    return at < 0;
  };

  DC.shelf = { has, list: saved, toggle, onChange: (fn) => listeners.push(fn) };

  document.querySelectorAll("[data-save]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const now = toggle(btn.dataset.save);
      DC.toast(now ? "Saved to your shelf" : "Removed from your shelf");
    });
  });

  /* ---- Text size ---- */
  const MIN = -1;
  const MAX = 3;
  const setSize = (n) => {
    const size = Math.max(MIN, Math.min(MAX, n));
    if (size === 0) delete document.documentElement.dataset.ts;
    else document.documentElement.dataset.ts = String(size);
    return size;
  };
  let size = setSize(Number(DC.store.get(SIZE_KEY)) || 0);
  document.querySelectorAll("[data-textsize-step]").forEach((btn) => {
    btn.addEventListener("click", () => {
      size = setSize(size + Number(btn.dataset.textsizeStep));
      DC.store.set(SIZE_KEY, String(size));
      document.querySelectorAll("[data-textsize-step]").forEach((b) => {
        b.disabled = (Number(b.dataset.textsizeStep) < 0 && size <= MIN) || (Number(b.dataset.textsizeStep) > 0 && size >= MAX);
      });
    });
  });

  /* ---- Remember where the reader stopped ---- */
  const page = document.querySelector("[data-essay-page]");
  const prose = document.querySelector("[data-prose]");
  if (page && prose) {
    let ticking = false;
    const record = () => {
      ticking = false;
      const rect = prose.getBoundingClientRect();
      const total = rect.height - window.innerHeight * 0.6;
      const done = total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 1;
      write(LAST_KEY, {
        slug: page.dataset.slug,
        title: page.dataset.title,
        url: window.location.pathname.split("/").pop(),
        done: Math.round(done * 100) / 100,
      });
    };
    window.addEventListener("scroll", () => {
      if (!ticking) { ticking = true; requestAnimationFrame(record); }
    }, { passive: true });
  }

  /* ---- Continue reading card on the home page ---- */
  const slot = document.querySelector("[data-continue]");
  if (slot) {
    const last = read(LAST_KEY, null);
    if (last && last.url && last.done > 0.03 && last.done < 0.95) {
      const a = document.createElement("a");
      a.className = "continue";
      a.href = `${DC.siteRoot}writeups/${last.url}`;
      const small = document.createElement("span");
      small.className = "continue__label";
      small.textContent = `Continue reading, ${Math.round(last.done * 100)}% done`;
      const title = document.createElement("span");
      title.className = "continue__title";
      title.textContent = last.title;
      a.append(small, title);
      slot.append(a);
      slot.hidden = false;
    }
  }

  /* ---- Surprise me ---- */
  const surprise = document.querySelector("[data-surprise]");
  if (surprise) {
    surprise.addEventListener("click", () => {
      const links = Array.from(document.querySelectorAll("[data-grid] [data-essay]:not([hidden])"));
      const pool = links.length ? links : Array.from(document.querySelectorAll("[data-grid] [data-essay]"));
      if (!pool.length) return;
      window.location.href = pool[Math.floor(Math.random() * pool.length)].getAttribute("href");
    });
  }

  paint();
})();
