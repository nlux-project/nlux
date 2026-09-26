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
  url: 'http://localhost:8089/?collection=teylers',
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
        collections: {
          teylers: {
            label: 'Teylers Museum',
            scope: 'item',
            query: { hasDigitalImage: true },
            seed: null,
          },
        },
        default_collection: 'teylers',
        theme: { primary: '#2c5282', accent: '#ed8936' },
        nlux_api: 'http://localhost:8000',
        total_items: 200,
      }),
    };
  }
  if (u.includes('/api/carousel')) {
    assert.match(u, /count=5/, 'count param passed');
    assert.match(u, /scope=item/, 'scope param passed');
    assert.match(u, /collection=teylers/, 'collection param from URL passed through');
    return {
      ok: true,
      status: 200,
      json: async () => ({
        collection: 'teylers',
        scope: 'item',
        count: 4,
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
          {
            // very long title with sentence periods — displayed cut at first sentence
            uri: 'https://example.com/nlux/HumanMadeObject/teylers3',
            id: 'teylers3',
            type: 'HumanMadeObject',
            title: 'Gezicht in het dorp Appeldorn, 1746. Prent uit een 100-delige serie met gezichten op dorpen en steden te Kleef. Ets door door Paulus van Liender naar ontwerptekening van Jan de Beijer; gesigneerd en gedateerd',
            creator: 'Liender, Paulus van',
            date: '1746',
            classification: 'prints (visual works)',
            material: null,
            technique: null,
            accession: null,
            image: '/iiif/image/token3',
            detail_url: null,
            credit: 'Teylers Museum, Haarlem',
          },
          {
            // very long title whose first dots sit inside an abbreviation
            uri: 'https://example.com/nlux/HumanMadeObject/teylers4',
            id: 'teylers4',
            type: 'HumanMadeObject',
            title: 'Prent van de St. Janskerk te Gouda, vervaardigd in de achttiende eeuw door een plaatselijke graveur en uitgegeven door de kerk zelf als aandenken aan de restauratie van de toren. Tweede zin.',
            creator: null,
            date: null,
            classification: 'prints (visual works)',
            material: null,
            technique: null,
            accession: null,
            image: '/iiif/image/token4',
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
assert.equal(slides.length, 4, 'all slides rendered');

// First slide active with correct content
assert.ok(slides[0].classList.contains('active'), 'first slide active');
assert.equal(
  document.querySelector('.brand-sub').textContent,
  'Teylers Museum',
  'brand subtitle shows the collection label');
assert.equal(
  slides[0].querySelector('.slide-title').textContent,
  'Feesten van Hollandse boeren');
assert.equal(
  slides[0].querySelector('.slide-creator').textContent,
  'Surugue, Pierre Louis');
assert.equal(slides[0].querySelector('img').src, 'http://localhost:8089/iiif/image/token1');
assert.ok(slides[0].querySelector('.slide-link'), 'detail link rendered');
assert.equal(slides[1].querySelector('.slide-link'), null, 'no link without detail_url');

// Long titles are cut at the first sentence; the full title stays in img.alt
assert.equal(
  slides[2].querySelector('.slide-title').textContent,
  'Gezicht in het dorp Appeldorn, 1746',
  'long title displayed up to the first sentence');
assert.equal(
  slides[2].querySelector('img').alt,
  'Gezicht in het dorp Appeldorn, 1746. Prent uit een 100-delige serie met gezichten op dorpen en steden te Kleef. Ets door door Paulus van Liender naar ontwerptekening van Jan de Beijer; gesigneerd en gedateerd',
  'full title kept in img alt');
assert.equal(
  slides[3].querySelector('.slide-title').textContent,
  'Prent van de St. Janskerk te Gouda, vervaardigd in de achttiende eeuw door een plaatselijke graveur en uitgegeven door de kerk zelf als aandenken aan de restauratie van de toren',
  'dots inside abbreviations are skipped when cutting');
assert.equal(
  slides[0].querySelector('.slide-title').textContent,
  'Feesten van Hollandse boeren',
  'short titles are left untouched');

// Progress bar + removed chrome (no prev/next buttons, no counter)
assert.match(document.querySelector('.progress-fill').style.animation, /slide-progress 10s/);
assert.equal(document.querySelector('.carousel-bottombar'), null, 'bottom bar removed');
assert.equal(document.querySelector('.prev-btn'), null, 'prev button removed');
assert.equal(document.querySelector('.next-btn'), null, 'next button removed');
assert.equal(document.querySelector('.counter'), null, 'counter removed');

// Navigation via keyboard
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
await delay(50);
assert.ok(slides[1].classList.contains('active'), 'second slide active after ArrowRight');
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft' }));
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