function visibleRollRows() {
  return [...document.querySelectorAll("[data-child-name]")].filter((row) => !row.hidden);
}

function updateRollCounts() {
  let present = 0;
  let absent = 0;
  visibleRollRows().forEach((row) => {
    if (row.querySelector('input[value="PRESENT"]:checked')) present += 1;
    if (row.querySelector('input[value="ABSENT"]:checked')) absent += 1;
  });
  const presentNode = document.getElementById("present-count");
  const absentNode = document.getElementById("absent-count");
  if (presentNode) presentNode.textContent = String(present);
  if (absentNode) absentNode.textContent = String(absent);
}

function selectedDivision() {
  const pressed = document.querySelector("[data-division-choice][aria-pressed='true']");
  return pressed ? pressed.getAttribute("data-division-choice") || "" : "";
}

function applyRollFilter() {
  const search = document.getElementById("roll-search");
  const term = search ? search.value.trim().toLowerCase() : "";
  const division = selectedDivision();
  document.querySelectorAll("[data-child-name]").forEach((row) => {
    const name = row.getAttribute("data-child-name") || "";
    const rowDivision = row.getAttribute("data-division") || "";
    const nameHidden = Boolean(term) && !name.includes(term);
    const divisionHidden = Boolean(division) && rowDivision !== division;
    row.hidden = nameHidden || divisionHidden;
  });
  const scope = document.getElementById("roll-scope");
  const pressed = document.querySelector("[data-division-choice][aria-pressed='true']");
  const label = pressed ? pressed.getAttribute("data-division-label") : "";
  if (scope) scope.textContent = label ? `${label} · ` : "";
  const hidden = document.getElementById("roll-division");
  if (hidden) hidden.value = division;
  document.querySelectorAll('input[name="division"]').forEach((input) => {
    input.value = division;
  });
  document.querySelectorAll("[data-keep-division]").forEach((link) => {
    const url = new URL(link.href);
    if (division) url.searchParams.set("division", division);
    else url.searchParams.delete("division");
    link.href = url.toString();
  });
  updateRollCounts();
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("roll-form");
  const search = document.getElementById("roll-search");
  if (form) form.addEventListener("change", updateRollCounts);
  if (search) search.addEventListener("input", applyRollFilter);
  document.querySelectorAll("[data-division-choice]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-division-choice]").forEach((other) => {
        other.setAttribute("aria-pressed", other === button ? "true" : "false");
      });
      applyRollFilter();
    });
  });
  applyRollFilter();
});
