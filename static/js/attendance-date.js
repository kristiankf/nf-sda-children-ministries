(function () {
  const input = document.querySelector("[data-sabbath-date]");
  if (!input) return;

  function isSaturday(value) {
    if (!value) return false;
    const parts = value.split("-").map(Number);
    if (parts.length !== 3) return false;
    const day = new Date(parts[0], parts[1] - 1, parts[2]);
    return day.getDay() === 6;
  }

  input.addEventListener("change", () => {
    if (!input.value || isSaturday(input.value)) return;
    // Keep the chosen date so the server can show the Saturday-only warning.
  });
})();
