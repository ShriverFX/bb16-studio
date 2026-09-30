/* Local product interactions. Videos load only when visible and playing.
   Reduced motion, explicit pause and hidden tabs always retain the still image. */
(() => {
  'use strict';
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  const fineHover = window.matchMedia('(hover: hover) and (pointer: fine)');
  const wide = window.matchMedia('(min-width: 900px) and (min-height: 760px)');
  const canObserve = 'IntersectionObserver' in window;
  const videos = Array.from(document.querySelectorAll('video[data-src]'));
  const tours = [];
  const cards = [];
  let paused = false;
  const allowed = () => !reduce.matches && !paused && !document.hidden;

  function play(video) {
    if (!video || !allowed()) return;
    video.muted = true;
    if (!video.getAttribute('src') && video.dataset.src) video.src = video.dataset.src;
    const attempt = video.play();
    if (attempt && attempt.catch) attempt.catch(() => { /* Keep the still image. */ });
  }

  function stop(video, rewind = false) {
    if (!video) return;
    video.pause();
    video.classList.remove('is-playing');
    if (rewind && video.readyState > 0) {
      try { video.currentTime = 0; } catch (_) { /* Media may not be ready. */ }
    }
  }

  function cardLabel(state) {
    const playing = state.video && !state.video.paused && allowed();
    state.button.setAttribute('aria-pressed', String(Boolean(playing)));
    state.label.textContent = playing ? "Mettre l'aperçu en pause" : "Voir l'aperçu animé";
  }

  videos.forEach(video => {
    video.addEventListener('playing', () => {
      if (allowed()) video.classList.add('is-playing'); else stop(video);
    });
    video.addEventListener('error', () => video.classList.remove('is-playing'));
  });

  function syncTour(state) {
    state.layers.forEach((layer, i) => {
      const video = layer.querySelector('video');
      if (i === state.active && wide.matches && state.visible && allowed()) play(video);
      else stop(video);
    });
    state.inline.forEach(item => {
      if (!wide.matches && item.visible && allowed()) play(item.video); else stop(item.video);
    });
  }

  document.querySelectorAll('[data-tour]').forEach(tour => {
    const state = { steps: Array.from(tour.querySelectorAll('[data-step]')),
      layers: Array.from(tour.querySelectorAll('[data-layer]')), active: 0, visible: false,
      inline: Array.from(tour.querySelectorAll('.step-phone')).map(phone =>
        ({ phone, video: phone.querySelector('video'), visible: false })) };
    const counter = tour.querySelector('[data-counter]');
    function activate(index) {
      if (index !== state.active) stop(state.layers[state.active].querySelector('video'), true);
      state.active = index;
      state.steps.forEach((step, i) => step.classList.toggle('is-active', i === index));
      state.layers.forEach((layer, i) => layer.classList.toggle('is-active', i === index));
      if (counter) counter.textContent = String(index + 1).padStart(2, '0');
      syncTour(state);
    }
    tours.push(state);
    activate(0);
    if (!canObserve) return;
    const stepObserver = new IntersectionObserver(entries => {
      if (!entries.some(entry => entry.isIntersecting)) return;
      const positions = state.steps.map(step => {
        const rect = step.getBoundingClientRect();
        return Math.abs((rect.top + rect.bottom) / 2 - innerHeight / 2);
      });
      activate(positions.indexOf(Math.min(...positions)));
    }, { rootMargin: '-35% 0px -35% 0px' });
    state.steps.forEach(step => stepObserver.observe(step));
    const stageObserver = new IntersectionObserver(entries => {
      state.visible = entries[0].isIntersecting;
      syncTour(state);
    }, { threshold: .2 });
    stageObserver.observe(tour.querySelector('.tour-sticky'));
    state.inline.forEach(item => {
      const observer = new IntersectionObserver(entries => {
        item.visible = entries[0].isIntersecting;
        syncTour(state);
      }, { threshold: .55 });
      observer.observe(item.phone);
    });
  });

  function syncCard(state) {
    const requested = state.manual === null ?
      (fineHover.matches ? state.hover : true) : state.manual;
    if (state.visible && requested && allowed()) play(state.video); else stop(state.video);
    cardLabel(state);
  }

  document.querySelectorAll('[data-hover-video]').forEach(card => {
    const state = { card, video: card.querySelector('video'),
      button: card.querySelector('[data-preview-toggle]'), label: card.querySelector('[data-preview-label]'),
      visible: !canObserve, hover: false, manual: null };
    cards.push(state);
    card.addEventListener('pointerenter', () => { state.hover = true; syncCard(state); });
    card.addEventListener('pointerleave', () => { state.hover = false; syncCard(state); });
    state.button.addEventListener('click', () => {
      state.manual = state.video.paused;
      syncCard(state);
    });
    ['playing', 'pause', 'error'].forEach(event => state.video.addEventListener(event, () => cardLabel(state)));
    if (canObserve) {
      const observer = new IntersectionObserver(entries => {
        state.visible = entries[0].isIntersecting;
        syncCard(state);
      }, { threshold: .35 });
      observer.observe(card.querySelector('.phone'));
    }
  });

  function refresh() {
    document.querySelectorAll('[data-motion-toggle]').forEach(button => {
      button.hidden = reduce.matches;
      button.setAttribute('aria-pressed', String(paused));
      button.textContent = paused ? 'Reprendre les aperçus' : 'Mettre les aperçus en pause';
    });
    cards.forEach(state => { state.button.hidden = reduce.matches; syncCard(state); });
    tours.forEach(syncTour);
    if (!allowed()) videos.forEach(video => stop(video));
    document.documentElement.dataset.motion = reduce.matches || paused ? 'paused' : 'active';
  }
  document.querySelectorAll('[data-motion-toggle]').forEach(button => {
    button.addEventListener('click', () => { paused = !paused; refresh(); });
  });
  [reduce, wide, fineHover].forEach(query => query.addEventListener('change', refresh));
  document.addEventListener('visibilitychange', refresh);
  refresh();

  if (canObserve) {
    // Reveal text only. Device geometry and screenshots never scale or tilt.
    const revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: .1 });
    document.querySelectorAll('.section-head, .step-copy, .feature-copy, .faq > h2').forEach(element => {
      element.dataset.reveal = '';
      revealObserver.observe(element);
    });
    document.documentElement.classList.add('motion-ready');
    const links = Array.from(document.querySelectorAll('.product-nav-links a'));
    const sections = links.map(link => document.querySelector(link.getAttribute('href')));
    const sectionObserver = new IntersectionObserver(entries => {
      entries.filter(entry => entry.isIntersecting).forEach(entry => {
        links.forEach((link, i) => {
          if (sections[i] === entry.target) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      });
    }, { rootMargin: '-15% 0px -65% 0px' });
    sections.forEach(section => sectionObserver.observe(section));
  }
})();
