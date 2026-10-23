(() => {
  'use strict';
  const clear = document.querySelector('[data-partner-draft-clear]');
  if (clear) {
    try { sessionStorage.removeItem(clear.dataset.partnerDraftClear); } catch (_) { /* Storage may be disabled. */ }
  }
  const form = document.querySelector('[data-partner-application-form]');
  if (!form) return;
  const key = form.dataset.draftKey;
  // Only fields intended for the public directory. Never persist contacts,
  // passwords, files, trade-license details, CSRF tokens or consent.
  const allowed = {company_name: 160, district: 100, division: 100};
  if (form.dataset.bound !== 'true') {
    try {
      const draft = JSON.parse(sessionStorage.getItem(key) || 'null');
      if (draft && draft.version === 1 && draft.values) {
        Object.entries(allowed).forEach(([name, limit]) => {
          const field = form.elements.namedItem(name);
          if (field && typeof draft.values[name] === 'string') field.value = draft.values[name].slice(0, limit);
        });
      }
    } catch (_) { /* Ignore unavailable storage or an invalid draft. */ }
  }
  form.addEventListener('input', () => {
    const values = {};
    Object.entries(allowed).forEach(([name, limit]) => {
      const field = form.elements.namedItem(name);
      if (field) values[name] = field.value.slice(0, limit);
    });
    try { sessionStorage.setItem(key, JSON.stringify({version: 1, values})); } catch (_) { /* Keep the form usable. */ }
  });
  // Submission can fail validation or transport. Only the server's successful
  // application-status response contains the clear marker above.
})();
