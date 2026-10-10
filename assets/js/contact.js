/* ==========================================================================
   Contact form
   Deep Calls is a static site with no server, so the form composes an email
   in the reader's own mail app (mailto:). Nothing is sent to or stored by
   this website. A visible fallback offers to copy the message in case no
   mail app opens.
   ========================================================================== */
(() => {
  "use strict";

  const form = document.querySelector("[data-contact-form]");
  if (!form) return;

  const to = form.dataset.to;
  const fields = {
    name: form.querySelector("#name"),
    email: form.querySelector("#email"),
    message: form.querySelector("#message"),
  };
  const topic = form.querySelector("#topic");
  const submit = form.querySelector("[type=submit]");
  const sent = document.querySelector("[data-sent]");
  const DC = window.DC || {};

  const setError = (input, message) => {
    const field = input.closest(".field");
    const error = field.querySelector(".field__error");
    field.dataset.invalid = message ? "true" : "false";
    input.setAttribute("aria-invalid", message ? "true" : "false");
    if (error) error.textContent = message;
  };

  const rules = {
    name: (v) => (v.trim() ? "" : "Please enter your name."),
    email: (v) => (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()) ? "" : "Please enter a valid email address."),
    message: (v) => (v.trim().length >= 5 ? "" : "Please write a short message."),
  };

  Object.entries(fields).forEach(([key, input]) => {
    input.addEventListener("blur", () => { if (input.value) setError(input, rules[key](input.value)); });
    input.addEventListener("input", () => {
      if (input.closest(".field").dataset.invalid === "true") setError(input, rules[key](input.value));
    });
  });

  const compose = () => {
    const name = fields.name.value.trim();
    const email = fields.email.value.trim();
    const subject = `[Deep Calls] ${topic.value} — from ${name}`;
    const body = `${fields.message.value.trim()}\n\n— ${name} (${email})`;
    return { subject, body, href: `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}` };
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    let firstInvalid = null;
    Object.entries(fields).forEach(([key, input]) => {
      const message = rules[key](input.value);
      setError(input, message);
      if (message && !firstInvalid) firstInvalid = input;
    });
    if (firstInvalid) {
      firstInvalid.focus();
      if (DC.toast) DC.toast("Please check the highlighted fields.");
      return;
    }

    const message = compose();
    submit.dataset.state = "loading";
    submit.setAttribute("aria-disabled", "true");
    setTimeout(() => {
      window.location.href = message.href;
      submit.removeAttribute("data-state");
      submit.removeAttribute("aria-disabled");
      if (sent) {
        sent.dataset.show = "true";
        const mailLink = sent.querySelector("[data-mailto]");
        if (mailLink) mailLink.href = message.href;
        const copyBtn = sent.querySelector("[data-copy-message]");
        if (copyBtn) {
          copyBtn.onclick = async () => {
            const ok = DC.copyText ? await DC.copyText(`To: ${to}\nSubject: ${message.subject}\n\n${message.body}`) : false;
            if (DC.toast) DC.toast(ok ? "Message copied" : "Couldn’t copy. Select the text in the box instead.");
          };
        }
        sent.focus();
      }
    }, 350);
  });
})();
