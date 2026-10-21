(() => {
  const root = document.documentElement;
  const account = root.dataset.accountTheme;
  let saved;
  try { saved = localStorage.getItem('rootline-theme'); } catch { /* Private browsing. */ }
  root.dataset.theme = ['light', 'dark'].includes(account) ? account :
    ['light', 'dark'].includes(saved) ? saved :
    'light';
})();
