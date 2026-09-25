/**
 * Smoke test: boots the real frontend modules in jsdom with a mocked
 * fetch, and asserts the carousel renders. Run with:  npm test
 */
import { JSDOM } from 'jsdom';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { setTimeout as delay } from 'node:timers/promises';

process.env.NODE_ENV = 'test';

const here = new URL('.', import.meta.url);
const dom = new JSDOM(readFileSync(new URL('../index.html', here), 'utf8'), {
  url: 'http://localhost:8089/',
  runScripts: 'outside-only',
  pretendToBeVisual: true,
});
const { window } = dom;

global.window = window;
global.document = window.document;
global.localStorage = window.localStorage;
global.HTMLElement = window.HTMLElement;
global.location = window.location;
global.KeyboardEvent = window.KeyboardEvent;
window.requestAnimationFrame = (cb) => setTimeout(cb, 16);
// jsdom has no fetch — stub with fixtures
window.fetch = global.fetch = async (url) => {
  const u = String(url);
  if (u.includes('/api/config')) {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        carousel: { interval: 10, count: 5, maxAge: 30 },
        collection: { name: 'teylers', scope: 'item' },
        theme: { primary: '#2c5282', accent: '#ed8936' },
        nlux_api: 'http://localhost:8000',
        total_items: 200,
      }),
    };
  }
  if (u.includes('/api/carousel')) {
    assert.match(u, /count=5/, 'count param passed');
    assert.match(u, /scope=item/, 'scope param passed');
    return {
      ok: true,
      status: 200,
      json: async () => ({
        collection: 'teylers',
        scope: 'item',
        count: 2,
        total_available: 200,
        seed: null,
        items: [
          {
            uri: 'https://example.com/nlux/HumanMadeObject/teylers1',
            id: 'teylers1',
            type: 'HumanMadeObject',
            title: 'Feesten van Hollandse boeren',
            creator: 'Surugue, Pierre Louis',
            date: '1748',
            classification: 'prints (visual works)',
            material: 'papier, beige',
            technique: 'ets',
            accession: 'KG 13459',
            image: '/iiif/image/token1',
            detail_url: 'https://example.com/details/1',
            credit: 'Teylers Museum, Haarlem',
          },
          {
            uri: 'https://example.com/nlux/HumanMadeObject/teylers2',
            id: 'teylers2',
            type: 'HumanMadeObject',
            title: 'Portret Keizer Mathias',
            creator: 'Sadaler, Aegidius',
            date: '1614',
            classification: 'drawings (visual works)',
            material: null,
            technique: null,
            accession: null,
            image: '/iiif/image/token2',
            detail_url: null,
            credit: 'Teylers Museum, Haarlem',
          },
        ],
      }),
    };
  }
  throw new Error(`Unexpected fetch: ${u}`);
};

// Boot the app (imports run start() immediately)
await import('../src/CarouselApp.js');
await delay(150);

// Carousel rendered?
const root = document.querySelector('.carousel-root');
assert.ok(root, 'carousel root rendered');
const slides = [...document.querySelectorAll('.slide')];
assert.equal(slides.length, 2, 'both slides rendered');

// First slide active with correct content
assert.ok(slides[0].classList.contains('active'), 'first slide active');
assert.equal(
  slides[0].querySelector('.slide-title').textContent,
  'Feesten van Hollandse boeren');
assert.equal(
  slides[0].querySelector('.slide-creator').textContent,
  'Surugue, Pierre Louis');
assert.equal(slides[0].querySelector('img').src, 'http://localhost:8089/iiif/image/token1');
assert.ok(slides[0].querySelector('.slide-link'), 'detail link rendered');
assert.equal(slides[1].querySelector('.slide-link'), null, 'no link without detail_url');

// Counter and progress bar
assert.equal(document.querySelector('.counter').textContent, '1 / 2');
assert.match(document.querySelector('.progress-fill').style.animation, /slide-progress 10s/);

// Navigation
const nextBtn = document.querySelector('.next-btn');
nextBtn.click();
await delay(50);
assert.ok(slides[1].classList.contains('active'), 'second slide active after next');
assert.equal(document.querySelector('.counter').textContent, '2 / 2');
document.querySelector('.prev-btn').click();
await delay(50);
assert.ok(slides[0].classList.contains('active'), 'wrap-around to first slide');

// Pause
const pauseBtn = document.querySelector('.pause-btn');
pauseBtn.click();
assert.ok(root.classList.contains('paused'), 'paused state toggles');
assert.equal(document.querySelector('.pause-btn').textContent, '▶');
pauseBtn.click();
assert.ok(!root.classList.contains('paused'), 'unpaused again');

// Settings modal
const overlay = document.querySelector('.settings-overlay');
const modal = document.querySelector('.settings-modal');
assert.ok(overlay && modal, 'settings modal present in DOM');
assert.ok(!overlay.classList.contains('show'), 'modal hidden initially');
document.querySelector('.fullscreen-btn'); // exists

// Keyboard: open settings with 's'
window.document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 's', bubbles: true }));
assert.ok(overlay.classList.contains('show'), 'settings opens via keyboard');
// Close with Escape
window.document.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
await delay(30);
assert.ok(!overlay.classList.contains('show'), 'settings closes via Escape');

// Stored settings boot merge
assert.equal(window.localStorage.getItem('nlux-carousel-settings') != null, true,
  'settings persisted');

console.log('✓ Carousel smoke test passed');
process.exit(0);