document.querySelectorAll("[data-clear-date]").forEach((button) => {
  const input = document.getElementById(button.dataset.clearDate);
  if (!(input instanceof HTMLInputElement)) return;

  function syncClear() {
    button.classList.toggle("hidden", !input.value);
  }

  button.addEventListener("click", () => {
    input.value = "";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    syncClear();
    input.focus();
  });

  input.addEventListener("input", syncClear);
  input.addEventListener("change", syncClear);
  syncClear();
});
