import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import process from 'node:process';
import { chromium } from 'playwright-core';

const root = path.resolve(import.meta.dirname, '..');
const output = path.resolve(root, '..', 'store-listings', 'lg-webos', 'screenshots');
const edgeCandidates = [
  process.env.EDGE_PATH,
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'
].filter(Boolean);
const edge = edgeCandidates.find((candidate) => fs.existsSync(candidate));
if (!edge) throw new Error('Microsoft Edge was not found. Set EDGE_PATH.');

const mime = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.png', 'image/png']
]);

const server = http.createServer((request, response) => {
  const requested = new URL(request.url, 'http://127.0.0.1').pathname;
  const relative = requested === '/' ? 'index.html' : requested.slice(1);
  const file = path.resolve(root, relative);
  if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    response.writeHead(404).end();
    return;
  }
  response.writeHead(200, { 'Content-Type': mime.get(path.extname(file)) || 'application/octet-stream' });
  fs.createReadStream(file).pipe(response);
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const address = server.address();
const browser = await chromium.launch({ executablePath: edge, headless: true });

try {
  fs.mkdirSync(output, { recursive: true });
  const firstRunContext = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  await firstRunContext.addInitScript(() => {
    window.__tvViewerExitRequested = false;
    Object.defineProperty(window, 'close', {
      configurable: true,
      value: () => {
        window.__tvViewerExitRequested = true;
      }
    });
  });
  const firstRunPage = await firstRunContext.newPage();
  await firstRunPage.goto(`http://127.0.0.1:${address.port}`, { waitUntil: 'domcontentloaded' });
  await firstRunPage.locator('#firstRunModal:not(.hidden)').waitFor();
  await firstRunPage.locator('#acceptNotice').focus();
  await firstRunPage.waitForTimeout(500);
  await firstRunPage.screenshot({ path: path.join(output, '00-first-run-notice.png') });
  await firstRunPage.keyboard.press('Escape');
  if (!await firstRunPage.evaluate(() => window.__tvViewerExitRequested)) {
    throw new Error('Back from the first-run entry screen did not request app exit');
  }
  await firstRunContext.close();

  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  await context.addInitScript(() => {
    localStorage.setItem('tvviewer-webos-notice-v1', 'accepted');
  });
  const page = await context.newPage();
  await page.goto(`http://127.0.0.1:${address.port}`, { waitUntil: 'domcontentloaded' });
  await page.locator('.channel-card.focusable').first().waitFor({ timeout: 30000 });
  const undersized = await page.locator('.focusable:visible').evaluateAll((elements) => elements
    .map((element) => {
      const rect = element.getBoundingClientRect();
      return { label: element.textContent.trim(), width: rect.width, height: rect.height };
    })
    .filter((element) => element.height < 75));
  if (undersized.length) {
    throw new Error(`FHD focus targets below 75px: ${JSON.stringify(undersized)}`);
  }
  const undersizedText = await page.locator('body *:visible').evaluateAll((elements) => elements
    .filter((element) => element.children.length === 0 && element.textContent.trim())
    .map((element) => ({
      text: element.textContent.trim().slice(0, 60),
      size: Number.parseFloat(getComputedStyle(element).fontSize)
    }))
    .filter((element) => element.size < 20));
  if (undersizedText.length) {
    throw new Error(`FHD visible text below 20px: ${JSON.stringify(undersizedText)}`);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.mouse.wheel(0, 500);
  await page.waitForTimeout(100);
  if (await page.evaluate(() => window.scrollY) <= 0) {
    throw new Error('Magic Remote wheel-equivalent input did not scroll the catalog');
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.locator('#categorySelect').selectOption('Legislative');
  await page.locator('#applyFilters').click();
  await page.locator('.channel-card.focusable').first().waitFor({ timeout: 30000 });
  await page.locator('.channel-card.focusable').first().focus();
  await page.screenshot({ path: path.join(output, '01-catalog.png') });

  await page.locator('#openHelp').click();
  await page.locator('#helpModal:not(.hidden)').waitFor();
  await page.locator('#closeHelp').focus();
  await page.screenshot({ path: path.join(output, '02-remote-help.png') });
  await page.locator('#closeHelp').click();
  await page.locator('#helpModal').waitFor({ state: 'hidden' });

  const ontario = page.locator('.channel-card.focusable', { hasText: 'Ontario Parliamentary Network' });
  if (await ontario.count()) {
    await ontario.first().click();
  } else {
    await page.locator('.channel-card.focusable').first().click();
  }
  await page.locator('#playerLayer:not(.hidden)').waitFor();
  await page.locator('#videoPlayer').evaluate((video) => {
    video.pause();
    video.removeAttribute('src');
    video.load();
    video.poster = 'splash.png';
  });
  await page.locator('#playerMessage').evaluate((message) => message.classList.add('hidden'));
  await page.locator('#closePlayer').focus();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(output, '03-player-controls.png') });

  console.log(`Captured Seller Lounge screenshots in ${output}`);
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
