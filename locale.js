/* Accessible links work without JS; JS only closes the picker and keeps anchors. */
(() => {
  'use strict';
  document.querySelectorAll('.language-picker').forEach(picker => {
    picker.addEventListener('keydown', event => {
      if (event.key === 'Escape') { picker.open = false; picker.querySelector('summary').focus(); }
    });
    picker.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        if (location.hash) {
          const target = new URL(link.href);
          target.hash = location.hash === '#english' && link.hreflang !== 'fr' ? '#main' : location.hash;
          link.href = target.href;
        }
      });
    });
    document.addEventListener('click', event => { if (!picker.contains(event.target)) picker.open = false; });
  });
})();
