(() => {
  const root = document.documentElement;
  const themeButton = document.getElementById('theme-toggle');
  const themeForm = document.getElementById('theme-form');
  if (!themeButton || !themeForm) return;
  function labelTheme() {
    const dark = root.dataset.theme === 'dark';
    themeButton.setAttribute('aria-pressed', String(dark));
    themeButton.setAttribute('aria-label', dark ? 'Use light mode' : 'Use dark mode');
    themeButton.textContent = dark ? 'Light mode' : 'Dark mode';
  }
  themeButton.hidden = false;
  labelTheme();
  themeButton.addEventListener('click', async () => {
    const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = theme;
    try { localStorage.setItem('rootline-theme', theme); } catch { /* Optional persistence. */ }
    labelTheme();
    if (themeForm.dataset.authenticated !== 'true') return;
    themeButton.disabled = true;
    const data = new FormData(themeForm);
    data.set('theme', theme);
    try {
      const response = await fetch(themeForm.action, {method: 'POST', body: data,
        credentials: 'same-origin', headers: {Accept: 'application/json'}});
      if (!response.ok || (await response.json()).theme !== theme) throw new Error();
    } catch {
      const message = 'Theme changed for this page. Your account preference could not be saved; try again.';
      if (window.RootLine) window.RootLine.toast(message);
      else {
        let status = themeForm.querySelector('[role=status]');
        if (!status) { status = document.createElement('span'); status.setAttribute('role', 'status'); themeForm.append(status); }
        status.textContent = message;
      }
    }
    finally { themeButton.disabled = false; }
  });

})();
