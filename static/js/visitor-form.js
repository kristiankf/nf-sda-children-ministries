(function () {
  const form = document.querySelector("[data-visitor-form]");
  if (!form) return;

  const identity = form.querySelector("[data-visitor-identity]");
  const existingInput = form.querySelector("#id_visit-existing_visitor");
  const selectedLabel = form.querySelector("[data-visitor-selected-label]");
  const clearButton = form.querySelector("[data-visitor-clear]");
  const cameWith = form.querySelector("#id_visit-came_with");
  const parentInput = form.querySelector("#id_visit-brought_by_parent");
  const childInput = form.querySelector("#id_visit-brought_by_child");
  const parentSummary = form.querySelector("[data-parent-summary]");
  const childSummary = form.querySelector("[data-child-summary]");

  function setIdentityEnabled(enabled) {
    if (!identity) return;
    identity.classList.toggle("hidden", !enabled);
    identity.querySelectorAll("input, select, textarea").forEach((field) => {
      field.disabled = !enabled;
      if (!enabled) field.removeAttribute("required");
    });
  }

  function setExisting(visitorId, name) {
    if (!existingInput) return;
    existingInput.value = visitorId || "";
    setIdentityEnabled(!visitorId);
    if (selectedLabel) {
      if (visitorId && name) {
        selectedLabel.hidden = false;
        selectedLabel.textContent = `Recording another visit for ${name}`;
      } else if (!visitorId) {
        selectedLabel.hidden = true;
        selectedLabel.textContent = "";
      }
    }
    clearButton?.classList.toggle("hidden", !visitorId);
  }

  function showCameWith(mode) {
    form.querySelectorAll("[data-came-with]").forEach((panel) => {
      panel.classList.toggle("hidden", panel.getAttribute("data-came-with") !== mode);
    });
    if (mode !== "parent" && parentInput) parentInput.value = "";
    if (mode !== "child" && childInput) childInput.value = "";
    if (mode !== "parent" && parentSummary) {
      parentSummary.classList.add("hidden");
      parentSummary.textContent = "";
    }
    if (mode !== "child" && childSummary) {
      childSummary.classList.add("hidden");
      childSummary.textContent = "";
    }
  }

  form.addEventListener("click", (event) => {
    const visitorButton = event.target.closest("[data-visitor-id]");
    if (visitorButton) {
      setExisting(visitorButton.dataset.visitorId, visitorButton.dataset.visitorName || "");
      return;
    }
    const parentButton = event.target.closest("[data-parent-id]");
    if (parentButton && parentInput) {
      parentInput.value = parentButton.dataset.parentId || "";
      if (parentSummary) {
        parentSummary.textContent = `Coming with ${parentButton.dataset.parentName || "selected parent"}`;
        parentSummary.classList.remove("hidden");
      }
      return;
    }
    const childButton = event.target.closest("[data-child-id]");
    if (childButton && childInput) {
      childInput.value = childButton.dataset.childId || "";
      if (childSummary) {
        childSummary.textContent = `Coming with ${childButton.dataset.childName || "selected child"}`;
        childSummary.classList.remove("hidden");
      }
    }
  });

  clearButton?.addEventListener("click", () => setExisting("", ""));

  cameWith?.addEventListener("change", () => showCameWith(cameWith.value));
  showCameWith(cameWith?.value || "none");

  if (existingInput?.value) {
    setExisting(existingInput.value, selectedLabel?.textContent?.replace(/^Recording another visit for /, "") || "");
  }
})();
