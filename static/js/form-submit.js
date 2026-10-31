function isMutatingForm(form) {
  if (!(form instanceof HTMLFormElement)) return false;
  if (form.hasAttribute("data-no-loading")) return false;
  if (form.hasAttribute("hx-post") || form.hasAttribute("hx-put") || form.hasAttribute("hx-patch") || form.hasAttribute("hx-delete")) {
    return true;
  }
  return form.method.toLowerCase() === "post";
}

function submitButtons(form) {
  return [...form.querySelectorAll('button[type="submit"], input[type="submit"]')];
}

function loadingLabel(button) {
  if (button instanceof HTMLElement && button.dataset.loadingLabel) {
    return button.dataset.loadingLabel;
  }
  return "Saving...";
}

function setButtonLoading(button) {
  if (!(button instanceof HTMLElement) || button.dataset.loading === "1") return;
  button.dataset.loading = "1";
  button.dataset.originalHtml = button.innerHTML;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  button.classList.add("is-loading");

  if (button instanceof HTMLInputElement) {
    button.dataset.originalValue = button.value;
    button.value = loadingLabel(button);
    return;
  }

  button.replaceChildren();
  const spinner = document.createElement("span");
  spinner.className = "btn-spinner";
  spinner.setAttribute("aria-hidden", "true");
  button.append(spinner, document.createTextNode(loadingLabel(button)));
}

function clearButtonLoading(button) {
  if (!(button instanceof HTMLElement) || button.dataset.loading !== "1") return;
  button.disabled = false;
  button.removeAttribute("aria-busy");
  button.classList.remove("is-loading");
  if (button instanceof HTMLInputElement && button.dataset.originalValue != null) {
    button.value = button.dataset.originalValue;
    delete button.dataset.originalValue;
  } else if (button.dataset.originalHtml != null) {
    button.innerHTML = button.dataset.originalHtml;
  }
  delete button.dataset.originalHtml;
  delete button.dataset.loading;
}

function startFormLoading(form, submitter) {
  if (!isMutatingForm(form) || form.dataset.loading === "1") return;
  form.dataset.loading = "1";
  form.setAttribute("aria-busy", "true");
  const buttons = submitButtons(form);
  const active = submitter instanceof HTMLElement && buttons.includes(submitter) ? submitter : buttons[0];
  buttons.forEach((button) => {
    if (button === active) setButtonLoading(button);
    else {
      button.disabled = true;
      button.dataset.loadingDisabled = "1";
    }
  });
}

function clearFormLoading(form) {
  if (!(form instanceof HTMLFormElement) || form.dataset.loading !== "1") return;
  form.removeAttribute("aria-busy");
  delete form.dataset.loading;
  submitButtons(form).forEach((button) => {
    if (button.dataset.loading === "1") clearButtonLoading(button);
    else if (button.dataset.loadingDisabled === "1") {
      button.disabled = false;
      delete button.dataset.loadingDisabled;
    }
  });
}

document.addEventListener(
  "submit",
  (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !isMutatingForm(form)) return;
    startFormLoading(form, event.submitter);
  },
  true,
);

function htmxVerb(event) {
  return (event.detail?.requestConfig?.verb || event.detail?.verb || "get").toLowerCase();
}

function isMutatingHtmxRequest(event) {
  return ["post", "put", "patch", "delete"].includes(htmxVerb(event));
}

document.body.addEventListener("htmx:beforeRequest", (event) => {
  const source = event.detail?.elt;
  if (!(source instanceof Element) || !isMutatingHtmxRequest(event)) return;
  const form = source.closest("form") || (source instanceof HTMLFormElement ? source : null);
  if (!form || !isMutatingForm(form)) return;
  const submitter = source.matches('button[type="submit"], input[type="submit"]') ? source : event.detail?.requestConfig?.triggeringEvent?.submitter;
  startFormLoading(form, submitter);
});

document.body.addEventListener("htmx:afterRequest", (event) => {
  const source = event.detail?.elt;
  if (!(source instanceof Element)) return;
  const form = source.closest("form") || (source instanceof HTMLFormElement ? source : null);
  if (form) clearFormLoading(form);
});

window.addEventListener("pageshow", (event) => {
  if (!event.persisted) return;
  document.querySelectorAll("form[data-loading='1']").forEach((form) => clearFormLoading(form));
});
