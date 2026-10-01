'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM, VirtualConsole } = require('jsdom');
const source = fs.readFileSync(path.join(__dirname, '..', 'doccipher-test.html'), 'utf8');
const storageKey = 'doccipher-test-form';

function fixture(options = {}) {
  const downloads = [], links = [], errors = [], writes = [], network = [];
  let resolveClipboard;
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM(source, {
    url: 'https://shriverfx.github.io/bb16-studio/doccipher-test.html',
    runScripts: 'dangerously', virtualConsole,
    beforeParse(w) {
      w.Blob = Blob;
      w.URL.createObjectURL = blob => { downloads.push(blob); return 'blob:local-test'; };
      if (options.downloadBlocked) w.URL.createObjectURL = () => { throw new Error('fixture download unavailable'); };
      w.URL.revokeObjectURL = () => {};
      w.HTMLAnchorElement.prototype.click = function () { links.push(this.download); };
      w.confirm = () => options.confirm !== false;
      w.Date.now = () => 12345;
      Object.defineProperty(w, 'isSecureContext', { value: options.secure !== false });
      const clipboard = options.clipboard === 'missing' ? undefined : {
        writeText: text => {
          if (options.clipboard === 'throw') throw new Error('fixture clipboard unavailable');
          if (options.clipboard === 'pending') return new Promise(resolve => { resolveClipboard = resolve; });
          return options.clipboard === 'reject'
            ? Promise.reject(new Error('fixture clipboard unavailable')) : Promise.resolve(text);
        },
      };
      Object.defineProperty(w.navigator, 'clipboard', { value: clipboard });
      const refuse = name => () => { network.push(name); throw new Error('unexpected network call'); };
      w.fetch = refuse('fetch'); w.XMLHttpRequest = refuse('xhr'); w.WebSocket = refuse('websocket');
      w.navigator.sendBeacon = refuse('beacon');
      if (options.stored !== undefined) w.localStorage.setItem(storageKey, options.stored);
      w.localStorage.setItem('convertair-test-form', 'fixture belonging to ConvertAir');
      const nativeSet = w.Storage.prototype.setItem;
      w.Storage.prototype.setItem = function (key, value) {
        writes.push(key); return nativeSet.call(this, key, value);
      };
      if (options.storageBlocked) Object.defineProperty(w, 'localStorage', {
        get() { throw new Error('fixture storage unavailable'); },
      });
    },
  });
  const d = dom.window.document;
  const byId = id => d.getElementById(id);
  function set(id, value) { byId(id).value = value; byId(id).dispatchEvent(new dom.window.Event('input', { bubbles: true })); }
  function context() { set('device', 'Pixel fictif'); set('android', '14'); set('app-version', '1.0.0-test'); }
  function change(id, checked) { byId(id).checked = checked; byId(id).dispatchEvent(new dom.window.Event('change', { bubbles: true })); }
  async function exportData() {
    byId('export').click();
    return downloads.length ? JSON.parse(await downloads.at(-1).text()) : undefined;
  }
  function close() { assert.deepEqual(network, []); assert.deepEqual(errors, []); dom.window.close(); }
  return { dom, d, byId, set, context, change, exportData, downloads, links, errors, writes, close,
    resolveClipboard: () => resolveClipboard() };
}

async function savedData() {
  const f = fixture(); f.context();
  const data = await f.exportData(); f.close(); return data;
}

test('nothing is passed by default and no local draft is written without opt-in', async () => {
  const f = fixture(); f.context(); const data = await f.exportData();
  assert.equal(data.app, 'DocCipher'); assert.equal(data.schema_version, 1);
  assert.ok(data.tests.length >= 15); assert.ok(data.purchase_scenarios.length >= 3);
  assert.ok(data.tests.concat(data.purchase_scenarios).every(item => item.status === 'not_tested'));
  assert.deepEqual(f.writes, []); f.close();
});

test('export requires device, Android and version and focuses the missing field', () => {
  const f = fixture(); f.byId('export').click();
  assert.equal(f.downloads.length, 0); assert.equal(f.byId('message').className, 'error');
  assert.equal(f.d.activeElement.id, 'device');
  f.set('device', 'Fixture'); f.byId('export').click(); assert.equal(f.d.activeElement.id, 'android');
  f.set('android', '14'); f.byId('export').click(); assert.equal(f.d.activeElement.id, 'app-version'); f.close();
});

test('partial report exports statuses, problems and a DocCipher filename', async () => {
  const f = fixture(); f.context();
  const radio = f.d.querySelector('#tests input[value="ok"]'); radio.click();
  f.byId('add-feedback').click();
  const box = f.d.querySelector('.feedback');
  box.querySelector('[data-field="summary"]').value = 'Document TEST non ouvert';
  box.querySelector('[data-field="steps"]').value = 'Ouvrir le document fictif';
  box.querySelector('[data-field="blocking"]').checked = true;
  const data = await f.exportData();
  assert.equal(data.tests.filter(item => item.status === 'ok').length, 1);
  assert.equal(data.feedback[0].summary, 'Document TEST non ouvert');
  assert.equal(data.feedback[0].blocking, true);
  assert.match(f.links[0], /^doccipher-test-.*\.json$/);
  assert.ok(f.byId('summary').textContent.includes('Document TEST non ouvert')); f.close();
});

test('clipboard success is reported only after completion', async () => {
  const f = fixture(); f.context(); f.byId('copy-summary').click();
  await new Promise(setImmediate);
  assert.equal(f.byId('message').textContent, 'Résumé copié.'); f.close();
});

for (const options of [{ clipboard: 'reject' }, { clipboard: 'missing' }, { clipboard: 'throw' }, { secure: false }]) {
  test(`clipboard fallback offers visible selectable text: ${JSON.stringify(options)}`, async () => {
    const f = fixture(options); f.context(); f.byId('copy-summary').click();
    await new Promise(setImmediate);
    assert.match(f.byId('message').textContent, /sélectionnez-le puis copiez-le/);
    assert.ok(!f.byId('summary').classList.contains('hidden')); f.close();
  });
}

test('clipboard does not claim success while writeText is still pending', async () => {
  const f = fixture({ clipboard: 'pending' }); f.context(); f.byId('copy-summary').click();
  assert.notEqual(f.byId('message').textContent, 'Résumé copié.');
  f.resolveClipboard(); await new Promise(setImmediate);
  assert.equal(f.byId('message').textContent, 'Résumé copié.'); f.close();
});

test('download failure leaves a selectable summary and reports no false export success', () => {
  const f = fixture({ downloadBlocked: true }); f.context(); f.byId('export').click();
  assert.equal(f.downloads.length, 0); assert.equal(f.byId('message').className, 'error');
  assert.ok(!f.byId('summary').classList.contains('hidden'));
  assert.ok(f.byId('summary').textContent.includes('Pixel fictif')); f.close();
});

test('panic instructions use the armed PIN and disclose immediate irreversible logical deletion', async () => {
  const f = fixture(); f.context(); const data = await f.exportData();
  assert.ok(data.tests.find(item => item.id === 'pc3_open'));
  assert.ok(data.tests.find(item => item.id === 'pc2_setup'));
  assert.ok(data.tests.find(item => item.id === 'pc2_trigger_one'));
  assert.ok(data.tests.find(item => item.id === 'pc2_trigger_all'));
  assert.ok(f.byId('destructive').textContent.includes('saisissez exactement le PIN de panique armé'));
  assert.ok(f.byId('destructive').textContent.includes('sans confirmation supplémentaire'));
  assert.ok(f.byId('destructive').textContent.includes('EFFACEMENT LOCAL IRRÉVERSIBLE'));
  assert.ok(f.byId('destructive').textContent.includes('sauvegarde externe fictive'));
  assert.ok(f.d.querySelector('details #destructive'));
  assert.equal(f.d.querySelectorAll('input[type="password"], input[type="file"]').length, 0);
  f.close();
});

test('local draft is opt-in, survives reload and opting out clears only DocCipher', async () => {
  const f = fixture(); f.context(); f.change('save-local', true);
  const raw = f.dom.window.localStorage.getItem(storageKey); assert.ok(raw);
  const reloaded = fixture({ stored: raw });
  assert.equal(reloaded.byId('device').value, 'Pixel fictif');
  assert.equal(reloaded.byId('save-local').checked, true);
  reloaded.change('save-local', false);
  assert.equal(reloaded.dom.window.localStorage.getItem(storageKey), null);
  assert.equal(reloaded.dom.window.localStorage.getItem('convertair-test-form'), 'fixture belonging to ConvertAir');
  f.close(); reloaded.close();
});

test('blocked local storage leaves export working and reports storage failure truthfully', async () => {
  const f = fixture({ storageBlocked: true }); f.context();
  f.change('save-local', true); assert.equal(f.byId('message').className, 'error');
  const data = await f.exportData(); assert.equal(data.app, 'DocCipher'); f.close();
});

test('cancelled reset preserves fields; confirmed reset clears fields and only this draft', async () => {
  const a = fixture({ confirm: false }); a.context(); a.change('save-local', true); a.byId('reset').click();
  assert.equal(a.byId('device').value, 'Pixel fictif'); assert.ok(a.dom.window.localStorage.getItem(storageKey)); a.close();
  const b = fixture(); b.context(); b.change('save-local', true); b.byId('add-feedback').click();
  await b.exportData(); b.byId('reset').click();
  assert.equal(b.byId('device').value, ''); assert.equal(b.byId('save-local').checked, false);
  assert.equal(b.d.querySelectorAll('.feedback').length, 0);
  assert.ok(b.byId('summary').classList.contains('hidden'));
  assert.equal(b.dom.window.localStorage.getItem(storageKey), null);
  assert.equal(b.dom.window.localStorage.getItem('convertair-test-form'), 'fixture belonging to ConvertAir'); b.close();
});

test('responses are rendered as text rather than executable HTML', async () => {
  const f = fixture(); f.context(); f.byId('add-feedback').click();
  const text = '<img src=x onerror="window.INJECTED=true">';
  f.d.querySelector('[data-field="summary"]').value = text;
  await f.exportData(); assert.ok(f.byId('summary').textContent.includes(text));
  assert.equal(f.byId('summary').querySelector('img'), null); assert.equal(f.dom.window.INJECTED, undefined); f.close();
});

test('rapid feedback additions have unique ids and can be removed', () => {
  const f = fixture(); f.byId('add-feedback').click(); f.byId('add-feedback').click();
  const ids = Array.from(f.d.querySelectorAll('[id]'), element => element.id);
  assert.equal(ids.length, new Set(ids).size);
  f.d.querySelector('.feedback button').click(); assert.equal(f.d.querySelectorAll('.feedback').length, 1); f.close();
});

test('feedback list is capped without losing the existing entries', () => {
  const f = fixture(); for (let i = 0; i < 35; i++) f.byId('add-feedback').click();
  assert.equal(f.d.querySelectorAll('.feedback').length, 30); f.close();
});

test('pressing Enter cannot submit the page or send answers as URL parameters', () => {
  const f = fixture(); f.context();
  const event = new f.dom.window.Event('submit', { bubbles: true, cancelable: true });
  assert.equal(f.byId('test-form').dispatchEvent(event), false); f.close();
});

const corruptions = {
  'broken JSON': () => '{',
  'wrong app': data => JSON.stringify({ ...data, app: 'ConvertAir' }),
  'invalid status': data => { data.tests[0].status = 'pretend_pass'; return JSON.stringify(data); },
  'unknown id': data => { data.tests[0].id = 'unknown'; return JSON.stringify(data); },
  'duplicate id': data => { data.tests[1].id = data.tests[0].id; return JSON.stringify(data); },
  'wrong nickname type': data => { data.tester.nickname = {}; return JSON.stringify(data); },
  'wrong note type': data => { data.purchase_note = []; return JSON.stringify(data); },
  'oversized field': data => { data.tester.device_model = 'x'.repeat(121); return JSON.stringify(data); },
  'oversized draft': () => 'x'.repeat(200001),
  'oversized valid JSON': data => JSON.stringify({ ...data, unexpectedPadding: 'x'.repeat(200001) }),
};
for (const [name, corrupt] of Object.entries(corruptions)) {
  test(`corrupt or unexpected draft is discarded safely: ${name}`, async () => {
    const data = await savedData(); const f = fixture({ stored: corrupt(data) });
    assert.equal(f.byId('device').value, ''); assert.equal(f.byId('save-local').checked, false);
    assert.equal(f.dom.window.localStorage.getItem(storageKey), null); f.close();
  });
}
