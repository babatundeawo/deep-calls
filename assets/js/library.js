/* ==========================================================================
   Library: search, theme filter and sort
   State lives in the URL (?q=, ?cat=, ?sort=) so filtered views can be
   shared and the back button behaves. Legacy ?cat= links keep working.
   ========================================================================== */
(() => {
  "use strict";

  const grid = document.querySelector("[data-grid]");
  if (!grid) return;

  const norm = window.DC ? window.DC.norm : (s) => String(s || "").toLowerCase();
  const cards = Array.from(grid.querySelectorAll("[data-essay]"));
  const input = document.querySelector("[data-q]");
  const sortSel = document.querySelector("[data-sort]");
  const chips = Array.from(document.querySelectorAll("[data-chip]"));
  const countEl = document.querySelector("[data-count]");
  const empty = document.querySelector("[data-empty]");
  
  const sorters = {
    oldest: (a, b) => (a.dataset.date || "").localeCompare(b.dataset.date || "") || a.dataset.title.localeCompare(b.dataset.title),
    newest: (a, b) => (b.dataset.date || "").localeCompare(a.dataset.date || "") || a.dataset.title.localeCompare(b.dataset.title),
    quick: (a, b) => Number(a.dataset.min) - Number(b.dataset.min) || a.dataset.title.localeCompare(b.dataset.title),
    long: (a, b) => Number(b.dataset.min) - Number(a.dataset.min) || a.dataset.title.localeCompare(b.dataset.title),
    az: (a, b) => a.dataset.title.localeCompare(b.dataset.title),
  };

  const DEFAULT_SORT = "newest";
  const params = new URLSearchParams(window.location.search);
  const categories = chips.map((c) => c.dataset.chip).filter(Boolean);
  const state = { q: params.get("q") || "", cat: "", sort: params.get("sort") || DEFAULT_SORT, saved: params.get("saved") === "1", topic: (params.get("topic") || "").trim() };
  const shelf = window.DC && window.DC.shelf;
  const topicChips = Array.from(document.querySelectorAll("[data-topic]"));
  const savedChip = document.querySelector("[data-chip-saved]");

  // Accept exact names, and older links where "&" cut the value short ("Church ").
  const wanted = (params.get("cat") || "").trim().toLowerCase();
  if (wanted) {
    state.cat = categories.find((c) => c.toLowerCase() === wanted)
      || categories.find((c) => c.toLowerCase().startsWith(wanted))
      || "";
  }
  if (!sorters[state.sort]) state.sort = DEFAULT_SORT;

  const syncUrl = () => {
    const next = new URLSearchParams();
    if (state.q) next.set("q", state.q);
    if (state.cat) next.set("cat", state.cat);
    if (state.saved) next.set("saved", "1");
    if (state.topic) next.set("topic", state.topic);
    if (state.sort !== DEFAULT_SORT) next.set("sort", state.sort);
    const query = next.toString();
    history.replaceState(null, "", window.location.pathname + (query ? `?${query}` : ""));
  };

  const apply = () => {
    const tokens = norm(state.q).split(/\s+/).filter(Boolean);
    const ordered = cards.slice().sort(sorters[state.sort]);
    let shown = 0;
    ordered.forEach((card) => {
      const okCat = !state.cat || card.dataset.cat === state.cat;
      const okQuery = tokens.every((t) => card.dataset.hay.includes(t));
      const okTopic = !state.topic || (card.dataset.topics || "").split("|").includes(state.topic);
      const okSaved = !state.saved || (shelf && shelf.has(card.dataset.slug));
      card.hidden = !(okCat && okQuery && okSaved && okTopic);
      if (!card.hidden) shown += 1;
      grid.appendChild(card);
    });

    chips.forEach((chip) => chip.setAttribute("aria-pressed", String(!state.saved && (chip.dataset.chip || "") === state.cat)));
    topicChips.forEach((chip) => chip.setAttribute("aria-pressed", String(chip.dataset.topic === state.topic)));
    const topicsBox = document.querySelector(".topics");
    if (topicsBox && state.topic) topicsBox.open = true;
    if (savedChip) savedChip.setAttribute("aria-pressed", String(state.saved));
    if (countEl) {
      const filtered = state.cat || tokens.length || state.saved || state.topic;
      countEl.textContent = filtered ? `${shown} ${shown === 1 ? "match" : "matches"}` : "";
    }
    if (empty) {
      empty.dataset.show = String(shown === 0);
      const msg = empty.querySelector("[data-empty-text]");
      if (msg) msg.textContent = state.saved && !(shelf && shelf.list().length)
        ? "You haven’t saved anything yet. Use Save for later on any essay and it will wait for you here."
        : "Try a different word, or clear the filters to see everything.";
    }
    grid.hidden = shown === 0;
    syncUrl();
  };

  if (input) {
    input.value = state.q;
    let timer;
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => { state.q = input.value.trim(); apply(); }, 90);
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && input.value) { input.value = ""; state.q = ""; apply(); }
    });
  }
  if (sortSel) {
    sortSel.value = state.sort;
    sortSel.addEventListener("change", () => { state.sort = sortSel.value; apply(); });
  }
  chips.forEach((chip) => chip.addEventListener("click", () => { state.cat = chip.dataset.chip || ""; state.saved = false; apply(); }));
  topicChips.forEach((chip) => chip.addEventListener("click", () => { state.topic = state.topic === chip.dataset.topic ? "" : chip.dataset.topic; apply(); }));
  if (savedChip) savedChip.addEventListener("click", () => { state.saved = !state.saved; if (state.saved) state.cat = ""; apply(); });
  if (shelf) shelf.onChange(() => { if (state.saved) apply(); });

  const clear = document.querySelector("[data-clear]");
  if (clear) {
    clear.addEventListener("click", () => {
      state.q = ""; state.cat = ""; state.topic = ""; state.saved = false; state.sort = DEFAULT_SORT;
      if (input) input.value = "";
      if (sortSel) sortSel.value = DEFAULT_SORT;
      apply();
      if (input) input.focus();
    });
  }

  apply();
})();
