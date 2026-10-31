(function () {
  const root = document.querySelector("[data-parent-picker]");
  if (!root) return;

  const dialog = root.querySelector("[data-parent-dialog]");
  const openButtons = root.querySelectorAll("[data-parent-open]");
  const closeButtons = root.querySelectorAll("[data-parent-close]");
  const clearButtons = root.querySelectorAll("[data-parent-clear]");
  const linkedInput = root.querySelector("[data-parent-linked]");
  const summary = root.querySelector("[data-parent-summary]");
  const summaryText = root.querySelector("[data-parent-summary-text]");
  const emptyState = root.querySelector("[data-parent-empty]");
  const newFields = root.querySelector("[data-parent-new-fields]");
  const firstName = root.querySelector("[data-parent-first-name]");
  const lastName = root.querySelector("[data-parent-last-name]");
  const phone = root.querySelector("[data-parent-phone]");
  const searchInput = root.querySelector("[data-parent-search]");
  const matches = root.querySelector("[data-parent-matches]");

  function linkedId() {
    return (linkedInput?.value || "").trim();
  }

  function newValuesFilled() {
    return Boolean(
      (firstName?.value || "").trim() ||
        (lastName?.value || "").trim() ||
        (phone?.value || "").trim(),
    );
  }

  function setNewFieldsEnabled(enabled) {
    if (!newFields) return;
    newFields.classList.toggle("is-disabled", !enabled);
    [firstName, lastName, phone].forEach((field) => {
      if (!field) return;
      field.disabled = !enabled;
    });
  }

  function markSelected(parentId) {
    if (!matches) return;
    matches.querySelectorAll(".parent-pick").forEach((button) => {
      button.classList.toggle("is-selected", button.dataset.parentId === String(parentId));
    });
  }

  function updateSummary() {
    const id = linkedId();
    let label = "";
    if (id) {
      const selected = matches?.querySelector(`.parent-pick[data-parent-id="${id}"]`);
      const name = selected?.dataset.parentName || summary?.dataset.linkedName || "Selected parent";
      const phoneLabel =
        selected?.dataset.parentPhone || summary?.dataset.linkedPhone || "";
      label = phoneLabel ? `Linking ${name} · ${phoneLabel}` : `Linking ${name}`;
      if (summary) {
        summary.dataset.linkedName = name;
        summary.dataset.linkedPhone = phoneLabel;
      }
    } else if (newValuesFilled()) {
      const name = `${(firstName?.value || "").trim()} ${(lastName?.value || "").trim()}`.trim();
      const phoneLabel = (phone?.value || "").trim();
      label = phoneLabel ? `Adding ${name || "new parent"} · ${phoneLabel}` : `Adding ${name || "new parent"}`;
    }

    if (summaryText) summaryText.textContent = label;
    summary?.classList.toggle("hidden", !label);
    emptyState?.classList.toggle("hidden", Boolean(label));
  }

  function selectParent(button) {
    if (!(button instanceof HTMLElement) || !linkedInput) return;
    linkedInput.value = button.dataset.parentId || "";
    if (summary) {
      summary.dataset.linkedName = button.dataset.parentName || "";
      summary.dataset.linkedPhone = button.dataset.parentPhone || "";
    }
    if (firstName) firstName.value = "";
    if (lastName) lastName.value = "";
    if (phone) phone.value = "";
    setNewFieldsEnabled(false);
    markSelected(linkedInput.value);
    updateSummary();
  }

  function clearParent() {
    if (linkedInput) linkedInput.value = "";
    if (summary) {
      delete summary.dataset.linkedName;
      delete summary.dataset.linkedPhone;
    }
    if (firstName) firstName.value = "";
    if (lastName) lastName.value = "";
    if (phone) phone.value = "";
    if (searchInput) searchInput.value = "";
    if (matches) {
      matches.innerHTML = '<p class="text-sm text-muted">Type a name or phone number to search.</p>';
    }
    setNewFieldsEnabled(true);
    updateSummary();
  }

  openButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (dialog && typeof dialog.showModal === "function") dialog.showModal();
    });
  });

  searchInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") event.preventDefault();
  });

  closeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      updateSummary();
      dialog?.close();
    });
  });

  clearButtons.forEach((button) => {
    button.addEventListener("click", () => {
      clearParent();
      dialog?.close();
    });
  });

  matches?.addEventListener("click", (event) => {
    const button = event.target.closest(".parent-pick");
    if (button) selectParent(button);
  });

  [firstName, lastName, phone].forEach((field) => {
    field?.addEventListener("input", () => {
      if (!newValuesFilled()) {
        updateSummary();
        return;
      }
      if (linkedInput) linkedInput.value = "";
      markSelected("");
      setNewFieldsEnabled(true);
      updateSummary();
    });
  });

  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.target !== matches) return;
    markSelected(linkedId());
    if (linkedId()) setNewFieldsEnabled(false);
  });

  if (linkedId()) setNewFieldsEnabled(false);
  else setNewFieldsEnabled(true);
  updateSummary();

  if (root.dataset.parentOpenOnLoad === "1" && dialog && typeof dialog.showModal === "function") {
    dialog.showModal();
  }
})();
