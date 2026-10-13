/* Local browser evidence. No dependency is added to the published static site. */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(root, 'site.config.json')));
const ui = JSON.parse(fs.readFileSync(path.join(root, 'locales', 'ui.json')));
const draft = process.argv.includes('--draft');
const selected = process.argv.find(arg => arg.startsWith('--locales='));
const locales = selected ? selected.split('=')[1].split(',') : Object.keys(ui);
const quick = process.argv.includes('--quick');
const proofArg = process.argv.find(arg => arg.startsWith('--proof='));
const proofName = proofArg ? proofArg.slice('--proof='.length) : (draft ? 'i18n-draft-proof' : 'i18n-proof');
assert(/^[a-z0-9-]+$/.test(proofName),'safe local proof directory');
const output = path.join(root, '_apercu', proofName);
fs.mkdirSync(output, { recursive: true });
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript',
  '.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.mp4':'video/mp4'};
const server = http.createServer((req,res) => {
  const url = new URL(req.url,'http://localhost');
  if (!url.pathname.startsWith(config.base_path)) return res.writeHead(404).end();
  let rel = decodeURIComponent(url.pathname.slice(config.base_path.length));
  if (!rel || rel.endsWith('/')) rel += 'index.html';
  let file = path.resolve(root, rel);
  if (!file.startsWith(root + path.sep) || !mime[path.extname(file)]) return res.writeHead(404).end();
  if (draft && file.endsWith('.html')) {
    const candidate = path.join(root,'_apercu','i18n-draft',rel);
    if (fs.existsSync(candidate)) file = candidate;
  }
  fs.readFile(file, (error,bytes) => {
    if (error) return res.writeHead(404).end();
    res.setHeader('Content-Type',mime[path.extname(file)]); res.end(bytes);
  });
});
(async () => {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({headless:true,
    ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath:process.env.CHROMIUM_EXECUTABLE} : {})});
  const results=[];
  try {
    for (const width of (quick ? [390] : [320,390,1440])) {
      for (const theme of (quick ? ['dark'] : ['dark','light'])) {
        const context = await browser.newContext({viewport:{width,height:900},colorScheme:theme,reducedMotion:'reduce'});
        for (const locale of locales) {
          for (const app of (quick ? ['convertair'] : ['convertair','doccipher'])) {
            const page=await context.newPage();
            const errors=[],failed=[],external=[];
            page.on('pageerror',e=>errors.push(e.message));
            page.on('response',r=>{if(r.status()>=400) failed.push(r.url());});
            page.on('request',r=>{if(!r.url().startsWith(origin+'/')) external.push(r.url());});
            await page.goto(origin+config.base_path+(locale==='fr'?'':locale+'/')+app+'.html',{waitUntil:'networkidle'});
            await page.evaluate(async()=>{for(const img of document.images){img.loading='eager';await img.decode();}});
            const metrics=await page.evaluate(()=>({
              lang:document.documentElement.lang,dir:document.documentElement.dir,
              width:innerWidth,scroll:document.documentElement.scrollWidth,
              missing:[...document.images].filter(x=>!x.complete||x.naturalWidth===0).map(x=>x.src),
              phones:[...document.querySelectorAll('.phone')].map(x=>({width:x.getBoundingClientRect().width,height:x.getBoundingClientRect().height})),
              anchors:[...document.querySelectorAll('a[href^="#"]')].filter(x=>!document.getElementById(x.hash.slice(1))).map(x=>x.hash),
              motion:document.documentElement.dataset.motion
            }));
            assert.equal(metrics.lang,locale); assert.equal(metrics.dir,locale==='ar'?'rtl':'ltr');
            if (metrics.scroll>width+1) {
              const overflow=await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>!e.children.length).map(e=>({tag:e.tagName,class:e.className,text:e.textContent.slice(0,90),x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).filter(e=>e.width>0&&(e.right>innerWidth+1||e.x< -1)).slice(0,20));
              console.error(JSON.stringify({locale,app,width,overflow}));
              await page.screenshot({path:path.join(output,`overflow-${locale}-${app}-${width}.png`),fullPage:true});
            }
            assert(metrics.scroll<=width+1,`horizontal overflow ${locale}/${app}/${width}: ${metrics.scroll}`);
            assert.deepEqual(metrics.missing,[]); assert.deepEqual(metrics.anchors,[]);
            assert.deepEqual(errors,[]); assert.deepEqual(failed,[]); assert.deepEqual(external,[]);
            assert.equal(metrics.motion,'paused');
            await page.locator('.language-picker summary').focus();
            await page.keyboard.press('Enter');
            assert.equal(await page.locator('.language-list a').count(),22);
            await page.keyboard.press('Escape');
            assert.equal(await page.locator('.language-picker').getAttribute('open'),null);
            if ((['fr','en','ar','ja','zh-Hant','de'].includes(locale) && width!==320) || (width===390 && theme==='dark')) {
              await page.screenshot({path:path.join(output,`${locale}-${app}-${width}-${theme}.png`)});
            }
            if (width===390 && theme==='dark') {
              await page.locator('.phone').first().screenshot({path:path.join(output,`${locale}-${app}-phone.png`)});
            }
            results.push({locale,app,width,theme,...metrics});
            await page.close();
          }
        }
        await context.close();
      }
    }
    // The same shared phone geometry across languages and apps at each viewport.
    for (const width of [...new Set(results.map(x=>x.width))]) {
      const sizes=results.filter(x=>x.width===width).flatMap(x=>x.phones).filter(x=>x.width>0);
      assert.equal(new Set(sizes.map(x=>`${Math.round(x.width)}x${Math.round(x.height)}`)).size,1,`phone geometry ${width}`);
    }
    const general=[];
    const interactive=[];
    if (!quick) {
      // General pages and long privacy text also need RTL/mobile/desktop checks.
      for (const locale of locales) {
        const context=await browser.newContext({viewport:{width:320,height:900},reducedMotion:'reduce'});
        const page=await context.newPage();
        const errors=[],failed=[],external=[];
        page.on('pageerror',e=>errors.push(e.message));
        page.on('response',r=>{if(r.status()>=400) failed.push(r.url());});
        page.on('request',r=>{if(!r.url().startsWith(origin+'/')) external.push(r.url());});
        for (const name of ['index','studio','apps','support','contact','privacy','legal','convertair-privacy','doccipher-privacy','404']) {
          await page.goto(origin+config.base_path+(locale==='fr'?'':locale+'/')+name+'.html',{waitUntil:'networkidle'});
          const scroll=await page.evaluate(()=>document.documentElement.scrollWidth);
          assert(scroll<=321,`general page overflow ${locale}/${name}: ${scroll}`);
          assert.deepEqual(errors,[]); assert.deepEqual(failed,[]); assert.deepEqual(external,[]);
          general.push({locale,page:name,width:320,scroll});
        }
        await context.close();
      }
      // Exercise translated labels after JS changes their state, not only initial HTML.
      for (const locale of locales) {
        const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
        const page=await context.newPage();
        await page.goto(origin+config.base_path+(locale==='fr'?'':locale+'/')+'convertair.html',{waitUntil:'networkidle'});
        const toggle=page.locator('[data-motion-toggle]').first();
        assert.equal(await toggle.textContent(),ui[locale].pause_all);
        await toggle.click();
        assert.equal(await toggle.textContent(),ui[locale].resume_all);
        assert.equal(await page.locator('html').getAttribute('data-motion'),'paused');
        const label=page.locator('[data-preview-label]').first();
        assert.equal(await label.textContent(),ui[locale].play_one);
        await toggle.click();
        assert.equal(await toggle.textContent(),ui[locale].pause_all);
        await page.emulateMedia({reducedMotion:'reduce'});
        await page.waitForFunction(()=>document.documentElement.dataset.motion==='paused');
        assert.equal(await toggle.isVisible(),false);
        interactive.push({locale,localizedMotionLabels:'PASS',reduceMotionChange:'PASS'});
        await context.close();
      }
    }
    // No-JS navigation, translated content, and images remain available.
    const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
    const page=await context.newPage();
    await page.goto(origin+config.base_path+'en/convertair.html');
    assert(await page.locator('h1').textContent());
    await page.locator('.language-picker summary').click();
    await page.locator('.language-list a[hreflang="fr"]').click();
    assert.equal(await page.locator('html').getAttribute('lang'),'fr');
    await context.close();
    if (!quick && locales.includes('ja')) {
      const context=await browser.newContext({viewport:{width:390,height:844}});
      const page=await context.newPage();
      await page.goto(origin+config.base_path+'convertair-privacy.html#english');
      await page.locator('.language-picker summary').click();
      await page.locator('.language-list a[hreflang="ja"]').click();
      assert.equal(new URL(page.url()).hash,'#main');
      assert.equal(await page.locator('html').getAttribute('lang'),'ja');
      await context.close();
    }
    const report={status:'PASS',scope:draft?'LOCAL_DRAFT_NOT_EXPORT':'LOCAL_BROWSER_NOT_PUBLICATION',pages:results.length,
      locales,general_pages_checked:general.length,interaction_locales:interactive.length,
      external_requests:0,javaScriptDisabledNavigation:'PASS',results,general,interactive};
    fs.writeFileSync(path.join(output,'browser-proof.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify({...report,results:undefined,general:undefined,interactive:undefined}));
  } finally {await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
