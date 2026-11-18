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
  const gameplay = Array.from(document.querySelectorAll('video[data-hgq-runtime], video[data-peaksolo-runtime], video[data-app-runtime]'));
  let stopHgqWarmupAudio = () => {};
  gameplay.forEach(video => video.addEventListener('play', () => {
    stopHgqWarmupAudio();
    gameplay.forEach(other => {
      if (other !== video) other.pause();
    });
  }));
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) gameplay.forEach(video => video.pause());
  });
  let paused = false;
  const allowed = () => !reduce.matches && !paused && !document.hidden;

  const warmup = document.querySelector('[data-hgq-warmup]');
  if (warmup) {
    const start = warmup.querySelector('[data-warmup-start]');
    const sound = warmup.querySelector('[data-warmup-sound]');
    const restart = warmup.querySelector('[data-warmup-restart]');
    const question = warmup.querySelector('[data-warmup-question]');
    const heading = warmup.querySelector('#hgq-question');
    const callout = warmup.querySelector('[data-warmup-callout]');
    const result = warmup.querySelector('[data-warmup-result]');
    const score = warmup.querySelector('[data-warmup-score]');
    const answers = Array.from(warmup.querySelectorAll('[data-warmup-answer]'));
    const audio = Object.fromEntries(Array.from(warmup.querySelectorAll('[data-warmup-audio]'))
      .map(player => [player.dataset.warmupAudio, player]));
    let warmupState = 'idle';
    let muted = false;
    let fightTimer = null;

    const setWarmupState = state => {
      warmupState = state;
      warmup.dataset.state = state;
    };
    const stopAudio = player => {
      if (!player) return;
      player.pause();
      if (player.readyState > 0) {
        try { player.currentTime = 0; } catch (_) { /* Audio may not be ready. */ }
      }
    };
    const stopWarmupAudio = () => Object.values(audio).forEach(stopAudio);
    stopHgqWarmupAudio = stopWarmupAudio;
    const playAudio = (player, volume) => {
      if (!player || muted || document.hidden) return;
      if (!player.getAttribute('src') && player.dataset.src) player.src = player.dataset.src;
      player.muted = false;
      player.volume = volume;
      if (player.readyState > 0) {
        try { player.currentTime = 0; } catch (_) { /* Audio may not be ready. */ }
      }
      const attempt = player.play();
      if (attempt && attempt.catch) attempt.catch(() => { /* The quiz remains usable without audio. */ });
    };
    const resetAnswers = () => answers.forEach(answer => {
      answer.open = false;
      answer.classList.remove('is-picked', 'is-right', 'is-wrong');
      answer.querySelector('[data-warmup-option]').removeAttribute('aria-disabled');
    });
    const beginWarmup = () => {
      if (fightTimer !== null) window.clearTimeout(fightTimer);
      gameplay.forEach(video => video.pause());
      stopWarmupAudio();
      resetAnswers();
      result.hidden = true;
      question.hidden = true;
      start.hidden = true;
      callout.textContent = 'FIGHT';
      callout.hidden = false;
      callout.setAttribute('aria-hidden', 'false');
      setWarmupState('fight');
      playAudio(audio.music, .28);
      playAudio(audio.fight, .78);
      fightTimer = window.setTimeout(() => {
        fightTimer = null;
        callout.hidden = true;
        callout.setAttribute('aria-hidden', 'true');
        question.hidden = false;
        setWarmupState('question');
        heading.focus({ preventScroll: true });
      }, reduce.matches ? 0 : 700);
    };
    const finishWarmup = answer => {
      if (warmupState !== 'question') return;
      const correct = answer.dataset.correct === 'true';
      answers.forEach(item => { if (item !== answer) item.open = false; });
      answer.open = true;
      answer.classList.add('is-picked', correct ? 'is-right' : 'is-wrong');
      answers.forEach(item => item.querySelector('[data-warmup-option]').setAttribute('aria-disabled', 'true'));
      stopAudio(audio.music);
      stopAudio(audio.fight);
      playAudio(audio.gameover, .82);
      score.textContent = correct ? warmup.dataset.scoreWon : warmup.dataset.scoreLost;
      result.hidden = false;
      setWarmupState('finished');
      if (typeof result.scrollIntoView === 'function') {
        result.scrollIntoView({ block: 'nearest', behavior: reduce.matches ? 'instant' : 'smooth' });
      }
    };

    question.hidden = true;
    result.hidden = true;
    start.hidden = false;
    sound.hidden = false;
    start.addEventListener('click', beginWarmup);
    restart.addEventListener('click', beginWarmup);
    answers.forEach(answer => answer.querySelector('[data-warmup-option]').addEventListener('click', event => {
      if (warmupState !== 'question') {
        event.preventDefault();
        return;
      }
      event.preventDefault();
      finishWarmup(answer);
    }));
    sound.addEventListener('click', () => {
      muted = !muted;
      sound.setAttribute('aria-pressed', String(muted));
      sound.textContent = muted ? warmup.dataset.labelUnmute : warmup.dataset.labelMute;
      Object.values(audio).forEach(player => { player.muted = muted; });
      if (muted) stopWarmupAudio();
      else if (warmupState === 'question') playAudio(audio.music, .28);
    });
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) stopWarmupAudio();
    });
    window.addEventListener('pagehide', stopWarmupAudio);
  }

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
    state.label.textContent = playing ? (document.documentElement.dataset.pauseOne || "Mettre l'aperçu en pause") : (document.documentElement.dataset.playOne || "Voir l'aperçu animé");
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
      button.textContent = paused ? (document.documentElement.dataset.resumeAll || 'Reprendre les aperçus') : (document.documentElement.dataset.pauseAll || 'Mettre les aperçus en pause');
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
