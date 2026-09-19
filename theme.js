/* Local display preference only; no account, cookie, or network service. */
(() => {
  'use strict';
  const root = document.documentElement;
  const storageKey = 'bb16-theme';
  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
  const isTheme = value => value === 'light' || value === 'dark';
  let preference = null;
  try {
    const saved = localStorage.getItem(storageKey);
    if (isTheme(saved)) preference = saved;
  } catch (_) { /* Display still works when browser storage is unavailable. */ }

  const preferredTheme = () => preference || (systemTheme.matches ? 'dark' : 'light');

  function apply(theme) {
    root.dataset.theme = theme;
    document.querySelectorAll('[data-set-theme]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.setTheme === theme));
    });
    const color = document.querySelector('meta[name="theme-color"]');
    if (color) color.content = theme === 'dark' ? '#000000' : '#ffffff';
    const icon = document.getElementById('site-icon');
    if (icon) {
      icon.href = icon.dataset[theme];
      icon.type = theme === 'dark' ? 'image/png' : 'image/jpeg';
    }
  }

  // Run before the stylesheet and page body to avoid a flash of the wrong theme.
  apply(preferredTheme());

  function bindControls() {
    document.querySelectorAll('.theme-switch').forEach(group => { group.hidden = false; });
    document.querySelectorAll('[data-set-theme]').forEach(button => {
      button.addEventListener('click', () => {
        preference = button.dataset.setTheme;
        apply(preference);
        try { localStorage.setItem(storageKey, preference); } catch (_) { /* Session choice remains usable. */ }
      });
    });
    apply(preferredTheme());
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindControls, { once: true });
  } else {
    bindControls();
  }
  systemTheme.addEventListener('change', () => {
    if (!preference) apply(preferredTheme());
  });
  window.addEventListener('storage', event => {
    if (event.key === storageKey || event.key === null) {
      preference = isTheme(event.newValue) ? event.newValue : null;
      apply(preferredTheme());
    }
  });
})();
