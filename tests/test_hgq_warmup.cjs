'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { JSDOM } = require('jsdom');

const script = fs.readFileSync(path.join(__dirname, '..', 'product.js'), 'utf8');

function fixture() {
  return `<!doctype html><html><body>
    <aside data-hgq-warmup data-state="idle" data-label-mute="Mute" data-label-unmute="Sound on"
      data-score-won="1 / 1 · Correct" data-score-lost="0 / 1 · Try again">
      <button data-warmup-start hidden>Start</button><button data-warmup-sound hidden>Mute</button>
      <div data-warmup-callout hidden>FIGHT</div>
      <div data-warmup-question><h2 id="hgq-question" tabindex="-1">Question</h2>
        <details data-warmup-answer data-correct="false"><summary data-warmup-option>A</summary><p>No</p></details>
        <details data-warmup-answer data-correct="true"><summary data-warmup-option>B</summary><p>Yes</p></details>
        <details data-warmup-answer data-correct="false"><summary data-warmup-option>C</summary><p>No</p></details>
        <details data-warmup-answer data-correct="false"><summary data-warmup-option>D</summary><p>No</p></details>
      </div>
      <div data-warmup-result hidden><strong>GAME OVER</strong><p data-warmup-score></p><button data-warmup-restart>Again</button></div>
      <audio data-warmup-audio="music" data-src="music.ogg" preload="none" loop></audio>
      <audio data-warmup-audio="fight" data-src="fight.ogg" preload="none"></audio>
      <audio data-warmup-audio="gameover" data-src="gameover.ogg" preload="none"></audio>
    </aside><video data-hgq-runtime="trailer"></video>`;
}

test('warm-up audio starts on gesture, locks one answer, then supports replay and mute', async () => {
  const dom = new JSDOM(fixture(), { runScripts: 'outside-only', pretendToBeVisual: true, url: 'https://example.test/' });
  const { window } = dom;
  const plays = [];
  const pauses = [];
  window.matchMedia = () => ({ matches: true, addEventListener() {} });
  delete window.IntersectionObserver;
  Object.defineProperty(window.HTMLMediaElement.prototype, 'readyState', { configurable: true, get: () => 1 });
  window.HTMLMediaElement.prototype.play = function () { plays.push(this.dataset.warmupAudio); return Promise.resolve(); };
  window.HTMLMediaElement.prototype.pause = function () { pauses.push(this.dataset.warmupAudio); };
  window.eval(script);

  const root = window.document.querySelector('[data-hgq-warmup]');
  const question = root.querySelector('[data-warmup-question]');
  const sound = root.querySelector('[data-warmup-sound]');
  assert.equal(question.hidden, true);
  assert.equal(root.querySelector('[data-warmup-start]').hidden, false);
  assert.equal(sound.hidden, false);
  assert.deepEqual(plays, []);
  for (const media of root.querySelectorAll('audio')) assert.equal(media.hasAttribute('src'), false);

  root.querySelector('[data-warmup-start]').click();
  await new Promise(resolve => window.setTimeout(resolve, 5));
  assert.equal(root.dataset.state, 'question');
  assert.equal(question.hidden, false);
  assert.deepEqual(plays, ['music', 'fight']);
  assert.ok(pauses.includes(undefined), 'starting the warm-up pauses HGQ video');
  for (const media of root.querySelectorAll('audio')) {
    if (media.dataset.warmupAudio !== 'gameover') assert.equal(media.hasAttribute('src'), true);
  }

  root.querySelector('[data-correct="true"] summary').click();
  assert.equal(root.dataset.state, 'finished');
  assert.equal(root.querySelector('[data-correct="true"]').open, true);
  assert.equal(root.querySelectorAll('.is-picked').length, 1);
  assert.equal(root.querySelector('[data-warmup-score]').textContent, '1 / 1 · Correct');
  assert.equal(root.querySelector('[data-warmup-result]').hidden, false);
  for (const summary of root.querySelectorAll('summary')) assert.equal(summary.getAttribute('aria-disabled'), 'true');
  assert.equal(plays.at(-1), 'gameover');
  root.querySelector('[data-correct="false"] summary').click();
  assert.equal(root.querySelectorAll('.is-picked').length, 1);

  sound.click();
  assert.equal(sound.getAttribute('aria-pressed'), 'true');
  assert.equal(sound.textContent, 'Sound on');
  assert.ok(pauses.length >= 3);
  root.querySelector('[data-warmup-restart]').click();
  await new Promise(resolve => window.setTimeout(resolve, 5));
  assert.equal(root.dataset.state, 'question');
  assert.equal(root.querySelector('[data-warmup-result]').hidden, true);
  assert.equal(root.querySelectorAll('.is-picked').length, 0);
  for (const summary of root.querySelectorAll('summary')) assert.equal(summary.hasAttribute('aria-disabled'), false);

  const pausesBeforeVideo = pauses.length;
  window.document.querySelector('video[data-hgq-runtime]').dispatchEvent(new window.Event('play'));
  assert.ok(pauses.length >= pausesBeforeVideo + 3, 'playing HGQ video stops every warm-up audio track');
  dom.window.close();
});
