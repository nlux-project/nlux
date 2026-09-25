import {chromium} from 'playwright';

(async () => {
  const url = process.env.URL || 'http://localhost:3004/';
  console.log(`Launching headless browser to ${url}`);

  const browser = await chromium.launch();
  const context = await browser.newContext({
    javaScriptEnabled: true,
  });
  const page = await context.newPage();

  page.on('console', (msg) => {
    try {
      console.log(`[console:${msg.type()}] ${msg.text()}`);
      for (const arg of msg.args()) {
        // attempt to serialize
        arg.jsonValue()
            .then((v) => {
              if (typeof v === 'object')
                console.log('  arg:', JSON.stringify(v));
            })
            .catch(() => {});
      }
    } catch (e) {
      console.log('[console] (error reading message)', e.message);
    }
  });

  page.on('pageerror', (err) => {
    console.error('[pageerror]', err.message);
    console.error(err.stack);
  });

  page.on('requestfailed', (req) => {
    const failure = req.failure();
    console.log('[requestfailed]', req.url(), failure && failure.errorText);
  });

  page.on('response', (res) => {
    if (res.status() >= 400) {
      console.log('[http error]', res.status(), res.url());
    }
  });

  try {
    const resp = await page.goto(url, {waitUntil: 'networkidle'});
    console.log('[navigation] status=', resp && resp.status());
  } catch (e) {
    console.error('[navigation error]', e?.message || e);
  }

  // Wait a bit to capture runtime console errors
  await page.waitForTimeout(5000);

  await browser.close();
  console.log('Headless run complete.');
})();
