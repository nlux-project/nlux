/**
 * Live check: boots the real frontend (dist/index.html + src/CarouselApp.js)
 * in jsdom against the running carousel (:8089) and backend (:8000) servers,
 * and asserts that long titles are displayed cut at their first sentence
 * while the full title is kept in img.alt.
 */
import { JSDOM } from 'jsdom';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { setTimeout as delay } from 'node:timers/promises';

const realFetch = globalThis.fetch.bind(globalThis); // capture BEFORE stubbing

process.env.NODE_ENV = 'test';

const here = new URL('.', import.meta.url);
const dom = new JSDOM(readFileSync(new URL('../index.html', here), 'utf8'), {
  url: 'http://localhost:8089/?collection=nha',
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

window.fetch = global.fetch = (url, opts) => {
  const u = new URL(String(url), 'http://localhost:8089');
  if (u.pathname.includes('/api/carousel')) u.searchParams.set('count', '50'); // broader sample
  return realFetch(u.toString(), opts);
};

await import('../src/CarouselApp.js');
await delay(500);

const slides = [...document.querySelectorAll('.slide')];
assert.ok(slides.length > 0, `slides rendered (got ${slides.length})`);

const TITLE_LONG_THRESHOLD = 100;
const TITLE_MIN_FIRST_SENTENCE = 20;

function expectedDisplay(full) {
  full = (full ?? '').trim();
  if (full.length <= TITLE_LONG_THRESHOLD) return full;
  let from = 0;
  while (from < full.length) {
    const dot = full.indexOf('.', from);
    if (dot === -1) return full;
    if (dot >= TITLE_MIN_FIRST_SENTENCE) return full.slice(0, dot).trim();
    from = dot + 1;
  }
  return full;
}

let checked = 0;
let appeldorn = false;
for (const slide of slides) {
  const full = slide.querySelector('img').alt;
  if (!full || full.length <= TITLE_LONG_THRESHOLD) continue;
  const shown = slide.querySelector('.slide-title').textContent;
  assert.equal(
    shown,
    expectedDisplay(full),
    `long title displayed cut at first sentence: "${full.slice(0, 60)}…"`);
  assert.notEqual(shown.length, full.length, 'displayed title is shorter than full');
  checked++;
  if (full.includes('Appeldorn')) appeldorn = true;
}

assert.ok(checked > 0, `at least one long-title slide to verify (got ${checked})`);
console.log(`✓ ${checked} long-title slides verified (Appeldorn example included: ${appeldorn})`);
process.exit(0);