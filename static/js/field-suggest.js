(function () {
  function wrapFor(list) {
    return list?.closest("[data-field-suggest]");
  }

  function inputFor(wrap) {
    return wrap?.querySelector("[data-suggest-input]");
  }

  function listFor(wrap) {
    return wrap?.querySelector("[data-suggest-list]");
  }

  function hideList(list) {
    if (!list) return;
    list.innerHTML = "";
    list.hidden = true;
  }

  function showList(list) {
    if (!list) return;
    list.hidden = !list.innerHTML.trim();
  }

  function applySuggestion(wrap, value) {
    const input = inputFor(wrap);
    const list = listFor(wrap);
    if (!input) return;
    input.value = value;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    hideList(list);
    input.focus();
  }

  document.addEventListener("click", (event) => {
    const option = event.target.closest("[data-suggest-value]");
    if (option) {
      const wrap = wrapFor(option.closest("[data-suggest-list]"));
      applySuggestion(wrap, option.getAttribute("data-suggest-value") || "");
      return;
    }
    document.querySelectorAll("[data-suggest-list]").forEach((list) => {
      const wrap = wrapFor(list);
      if (!wrap || wrap.contains(event.target)) return;
      hideList(list);
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    document.querySelectorAll("[data-suggest-list]").forEach(hideList);
  });

  document.body.addEventListener("htmx:afterSwap", (event) => {
    const list = event.target;
    if (!(list instanceof HTMLElement) || !list.hasAttribute("data-suggest-list")) return;
    showList(list);
  });
})();
