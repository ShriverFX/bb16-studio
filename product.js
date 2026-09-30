/* Pages produit : écran qui suit le défilement, aperçus vidéo au survol.
   Aucune requête réseau hors des fichiers du site ; aucune donnée conservée.
   Les vidéos ne sont chargées qu'au moment de les jouer, jamais quand
   l'utilisateur demande moins d'animations : les captures restent fixes. */
(() => {
  'use strict';
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  const fineHover = window.matchMedia('(hover: hover) and (pointer: fine)');
  const wide = window.matchMedia('(min-width: 900px)');
  const canObserve = 'IntersectionObserver' in window;

  function play(video) {
    if (!video || reduce.matches) return;
    video.muted = true;
    if (!video.getAttribute('src') && video.dataset.src) video.src = video.dataset.src;
    const attempt = video.play();
    if (attempt && attempt.catch) attempt.catch(() => { /* Lecture refusée : la capture reste affichée. */ });
  }

  function stop(video, rewind) {
    if (!video) return;
    video.pause();
    video.classList.remove('is-playing');
    if (rewind && video.readyState > 0) {
      try { video.currentTime = 0; } catch (_) { /* Rien à rembobiner. */ }
    }
  }

  document.querySelectorAll('video[data-src]').forEach(video => {
    video.addEventListener('playing', () => video.classList.add('is-playing'));
    video.addEventListener('error', () => video.classList.remove('is-playing'));
  });

  document.querySelectorAll('[data-tour]').forEach(tour => {
    const steps = Array.from(tour.querySelectorAll('[data-step]'));
    const layers = Array.from(tour.querySelectorAll('[data-layer]'));
    const counter = tour.querySelector('[data-counter]');
    let active = -1;

    function activate(index) {
      if (index === active || index < 0) return;
      active = index;
      steps.forEach((step, i) => step.classList.toggle('is-active', i === index));
      if (counter) counter.textContent = String(index + 1).padStart(2, '0');
      layers.forEach((layer, i) => {
        layer.classList.toggle('is-active', i === index);
        const video = layer.querySelector('video');
        if (i === index && wide.matches) play(video); else stop(video, true);
      });
    }

    if (!canObserve) return;
    const stepObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) activate(steps.indexOf(entry.target)); });
    }, { rootMargin: '-45% 0px -45% 0px' });
    steps.forEach(step => stepObserver.observe(step));

    // Téléphone : chaque étape porte son propre écran, joué quand il est visible.
    const inlineObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        const video = entry.target.querySelector('video');
        if (entry.isIntersecting && !wide.matches) play(video); else stop(video, false);
      });
    }, { threshold: 0.6 });
    tour.querySelectorAll('.step-phone').forEach(phone => inlineObserver.observe(phone));

    wide.addEventListener('change', () => {
      tour.querySelectorAll('video').forEach(video => stop(video, true));
      const current = active;
      active = -1;
      activate(current < 0 ? 0 : current);
    });
  });

  document.querySelectorAll('[data-hover-video]').forEach(card => {
    const video = card.querySelector('video');
    card.addEventListener('pointerenter', () => { if (fineHover.matches) play(video); });
    card.addEventListener('pointerleave', () => { if (fineHover.matches) stop(video, true); });
  });

  // Écrans tactiles : pas de survol, l'aperçu s'anime quand il est bien visible.
  if (canObserve) {
    const touchObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (fineHover.matches) return;
        const video = entry.target.querySelector('video');
        if (entry.isIntersecting) play(video); else stop(video, false);
      });
    }, { threshold: 0.7 });
    document.querySelectorAll('[data-hover-video]').forEach(card => touchObserver.observe(card));
  }

  reduce.addEventListener('change', () => {
    if (reduce.matches) document.querySelectorAll('video').forEach(video => stop(video, true));
  });
})();
