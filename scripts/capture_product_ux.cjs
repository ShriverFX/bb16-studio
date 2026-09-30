/* Local visual proof only. No dependency is shipped with the static site.
   Usage: node scripts/capture_product_ux.cjs before|after
   Set PLAYWRIGHT_MODULE to an installed Playwright directory when needed. */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json')));
const stage = process.argv[2];
assert(['before', 'after'].includes(stage), 'Choose before or after');
const output = path.join(root, '_apercu', stage);
fs.mkdirSync(output, { recursive: true });
const interactionOnly = process.argv.includes('--interactions-only');
assert(!interactionOnly || stage === 'after', 'Interaction-only is an after check');
const sourceFiles = ['styles.css', 'product.js', 'theme.js', 'product_pages.py', 'build_site.py',
  'convertair.html', 'doccipher.html', 'hgq.html'];
const sourceDigest = crypto.createHash('sha256');
sourceFiles.forEach(file => sourceDigest.update(file).update(fs.readFileSync(path.join(root, file))));
const sourceSha256 = sourceDigest.digest('hex');
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.mp4': 'video/mp4' };
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const rel = decodeURIComponent(url.pathname).slice(config.base_path.length);
  const file = path.resolve(root, rel || 'index.html');
  if (!url.pathname.startsWith(config.base_path) || !file.startsWith(root + path.sep)) {
    res.writeHead(404).end(); return;
  }
  fs.readFile(file, (error, bytes) => {
    if (error) { res.writeHead(404).end(); return; }
    res.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream');
    res.end(bytes);
  });
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? { executablePath: process.env.CHROMIUM_EXECUTABLE } : {}) });
  const proofFile = path.join(output, 'visual-proof.json');
  const previous = interactionOnly ? JSON.parse(fs.readFileSync(proofFile)) : null;
  if (previous) {
    if (previous.sourceSha256) assert.equal(previous.sourceSha256, sourceSha256, 'Visual source changed: recapture');
    else assert(sourceFiles.every(file => fs.statSync(path.join(root, file)).mtimeMs <= fs.statSync(proofFile).mtimeMs),
      'Visual source changed: recapture');
  }
  const results = previous ? previous.results : [];
  try {
    for (const width of (interactionOnly ? [] : [1440, 390])) {
      for (const theme of ['light', 'dark']) {
        const context = await browser.newContext({ viewport: { width, height: width === 1440 ? 900 : 844 },
          deviceScaleFactor: 1, colorScheme: theme, reducedMotion: 'reduce', hasTouch: width === 390 });
        for (const app of ['convertair', 'doccipher', 'hgq']) {
          const page = await context.newPage();
          const errors = [];
          const external = [];
          const failures = [];
          const videos = [];
          page.on('pageerror', error => errors.push(error.message));
          page.on('request', request => {
            if (!request.url().startsWith(origin + '/')) external.push(request.url());
            if (request.url().includes('.mp4')) videos.push(request.url());
          });
          page.on('response', response => { if (response.status() >= 400) failures.push(response.url()); });
          await page.goto(`${origin}${config.base_path}${app}.html`, { waitUntil: 'networkidle' });
          // Materialise lazy images, with motion disabled for reproducible captures.
          await page.evaluate(async () => {
            for (const image of document.images) {
              image.loading = 'eager';
              try { await image.decode(); } catch (_) { /* Assert below. */ }
            }
          });
          const name = `${app}-${width}-${theme}`;
          await page.screenshot({ path: path.join(output, `${name}-hero.png`) });
          await page.screenshot({ path: path.join(output, `${name}.png`), fullPage: true });
          await page.locator('[data-step]').nth(1).evaluate(element => element.scrollIntoView({ block: 'center' }));
          await page.screenshot({ path: path.join(output, `${name}-fonctions.png`) });
          await page.locator('.feature-grid').screenshot({ path: path.join(output, `${name}-apercus.png`),
            style: '.product-nav { visibility: hidden; }' });
          const metrics = await page.evaluate(() => {
            const props = ['width', 'height', 'padding', 'borderTopWidth', 'borderTopStyle', 'borderRightWidth',
              'borderBottomWidth', 'borderLeftWidth', 'borderRadius', 'backgroundImage', 'boxShadow', 'top', 'left', 'right'];
            const style = (el, pseudo) => {
              const css = getComputedStyle(el, pseudo);
              return Object.fromEntries(props.map(prop => [prop, css[prop]]));
            };
            const phones = Array.from(document.querySelectorAll('.phone')).filter(el => el.getBoundingClientRect().width > 0)
              .map(el => ({ frame: style(el), camera: style(el, '::before'), buttons: style(el, '::after'),
                screen: style(el.querySelector('.screen')), fit: getComputedStyle(el.querySelector('img')).objectFit }));
            return { phones, overflow: document.documentElement.scrollWidth > innerWidth,
              brokenImages: Array.from(document.images).filter(img => !img.complete || !img.naturalWidth).map(img => img.src),
              theme: document.documentElement.dataset.theme };
          });
          const record = { app, width, theme, ...metrics, errors, external, failures, videos };
          results.push(record);
          if (stage === 'after') {
            assert.equal(metrics.overflow, false, `${name}: horizontal overflow`);
            assert.equal(metrics.theme, theme);
            assert.deepEqual(metrics.brokenImages, []);
            assert.deepEqual(errors, []);
            assert.deepEqual(external, []);
            assert.deepEqual(failures, []);
            assert.deepEqual(videos, [], 'Reduced motion must not load video');
            for (const phone of metrics.phones) {
              assert.deepEqual(phone, metrics.phones[0], `${name}: inconsistent phone`);
              assert.equal(phone.fit, 'contain', 'Preserve the complete screenshot');
            }
          }
          console.log(`CAPTURE ${stage}/${name} phones=${metrics.phones.length}`);
          await page.close();
        }
        await context.close();
      }
    }
    if (stage === 'after') {
      const reference = results[0].phones[0];
      results.forEach(result => assert.deepEqual(result.phones[0], reference,
        `${result.app}-${result.width}-${result.theme}: phone differs across page/theme/viewport`));
      // Interaction proof uses normal motion; the still captures above use reduced motion.
      const interactive = [];
      for (const app of ['convertair', 'doccipher', 'hgq']) {
        const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'no-preference' });
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(`${origin}${config.base_path}${app}.html`, { waitUntil: 'networkidle' });
        assert.equal(await page.locator('video[src]').count(), 0, 'No video requested at initial load');
        await page.locator('[data-step]').nth(1).evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        await page.waitForFunction(() => document.querySelector('[data-counter]').textContent === '02');
        await page.waitForFunction(() => document.querySelector('.layer.is-active video').classList.contains('is-playing'));
        await page.locator('[data-step]').nth(2).evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        await page.waitForFunction(() => document.querySelector('[data-counter]').textContent === '03');
        await page.waitForFunction(() => document.querySelector('.layer.is-active video').classList.contains('is-playing'));
        assert.equal(await page.locator('.layer:not(.is-active) video').evaluateAll(videos => videos.every(video => video.paused)), true);
        const card = page.locator('[data-hover-video]').first();
        await card.locator('.phone').evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        await card.locator('.phone').hover();
        await page.waitForFunction(() => document.querySelector('[data-hover-video] video').classList.contains('is-playing'));
        await page.mouse.move(0, 100);
        await page.waitForFunction(() => document.querySelector('[data-hover-video] video').paused);
        const toggle = card.locator('[data-preview-toggle]');
        await toggle.focus();
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => !document.querySelector('[data-hover-video] video').paused);
        await page.keyboard.press('Enter');
        await page.waitForFunction(() => document.querySelector('[data-hover-video] video').paused);
        await page.locator('[data-motion-toggle]').click();
        assert.equal(await page.locator('video').evaluateAll(videos => videos.every(video => video.paused)), true);
        await card.locator('.phone').hover();
        assert.equal(await card.locator('video').evaluate(video => video.paused), true, 'Global pause overrides hover');
        await page.locator('[data-motion-toggle]').click();
        await page.locator('[data-step]').first().evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        await page.waitForFunction(() => document.querySelector('.layer.is-active video').classList.contains('is-playing'));
        await page.emulateMedia({ reducedMotion: 'reduce' });
        await page.waitForFunction(() => Array.from(document.querySelectorAll('video')).every(video => video.paused) &&
          Array.from(document.querySelectorAll('[data-preview-toggle]')).every(button => button.hidden));
        assert.equal(await page.locator('[data-preview-toggle]:visible').count(), 0);
        await page.locator('.faq-item summary').first().click();
        assert.equal(await page.locator('.faq-item').first().getAttribute('open'), '');
        await page.locator('[data-set-theme="dark"]').click();
        assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
        await page.reload();
        assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
        assert.deepEqual(errors, []);
        interactive.push({ app, desktop: 'PASS', keyboard: 'PASS', pause: 'PASS', liveReducedMotion: 'PASS', faq: 'PASS', themePersistence: 'PASS' });
        await context.close();

        const touch = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, reducedMotion: 'no-preference' });
        const mobile = await touch.newPage();
        await mobile.goto(`${origin}${config.base_path}${app}.html`);
        await mobile.locator('.step-phone').first().evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        await mobile.waitForFunction(() => document.querySelector('.step-phone video').classList.contains('is-playing'));
        await mobile.locator('[data-hover-video] .phone').first().evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        await mobile.waitForFunction(() => document.querySelector('[data-hover-video] video').classList.contains('is-playing'));
        await mobile.locator('[data-hover-video] [data-preview-toggle]').first().click();
        assert.equal(await mobile.locator('[data-hover-video] video').first().evaluate(video => video.paused), true);
        interactive[interactive.length - 1].touch = 'PASS';
        await touch.close();
        console.log(`INTERACTIONS ${app}=PASS`);
      }
      // Readable fallbacks: no script and short/small viewports retain inline phones.
      for (const scenario of [
        { viewport: { width: 320, height: 640 }, javaScriptEnabled: true },
        { viewport: { width: 1024, height: 680 }, javaScriptEnabled: true },
        { viewport: { width: 1440, height: 900 }, javaScriptEnabled: false }
      ]) {
        const context = await browser.newContext({ ...scenario, colorScheme: 'light', reducedMotion: 'reduce' });
        const page = await context.newPage();
        await page.goto(`${origin}${config.base_path}doccipher.html`);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
        assert.equal(await page.locator('.step-phone:visible').count(), 4);
        assert.equal(await page.locator('.tour-stage:visible').count(), 0);
        assert.equal(await page.locator('.motion-toggle:visible').count(), 0);
        await context.close();
      }
      fs.writeFileSync(path.join(output, 'interaction-proof.json'), JSON.stringify({ interactive,
        noJavaScript: 'PASS', narrow320: 'PASS', shortViewport: 'PASS' }, null, 2) + '\n');
    }
    fs.writeFileSync(proofFile, JSON.stringify({ stage, sourceSha256, results }, null, 2) + '\n');
    console.log(stage === 'after' ? 'PRODUCT_VISUAL_PROOF=PASS' : 'BASELINE_CAPTURED');
  } finally {
    await browser.close();
    server.close();
  }
})().catch(error => { console.error(error); server.close(); process.exitCode = 1; });
