/**
 * CarouselApp — main controller for the NLUX carousel display.
 *
 * Fetches carousel configuration and slide items from the carousel server
 * (same origin; the dev server proxies /api), then hands them to the
 * Carousel renderer. Refreshes the item batch each time a full cycle
 * completes. Handles settings, fullscreen and keyboard shortcuts.
 */

import Carousel from './components/Carousel.js';
import VanillaSettingsModal from './VanillaSettingsModal.js';

// API base: same-origin by default (prod dist is served by the carousel
// server; dev uses the vite proxy). Override with ?api=http://host:port
const params = new URLSearchParams(location.search);
export const API_BASE = (params.get('api') || window.CAROUSEL_API || '').replace(/\/+$/, '');
// Collection is selected via the URL: /?collection=teylers
export const COLLECTION_PARAM = params.get('collection');

const DEFAULTS = { interval: 10, count: 5, scope: 'item' };

const state = {
  config: null,
  settings: VanillaSettingsModal.getSettings(),
  carousel: null,
  timer: null,
  items: [],
};

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body && body.detail) detail = body.detail;
    } catch { /* not JSON */ }
    throw new Error(detail);
  }
  return response.json();
}

async function fetchConfig() {
  return fetchJSON(`${API_BASE}/api/config`);
}

async function fetchItems(settings) {
  const url = new URL(`${API_BASE}/api/carousel`, location.href);
  url.searchParams.set('count', settings.count);
  url.searchParams.set('scope', settings.scope);
  if (settings.seed) url.searchParams.set('seed', settings.seed);
  if (COLLECTION_PARAM) url.searchParams.set('collection', COLLECTION_PARAM);
  const data = await fetchJSON(url.pathname + url.search);
  return data;
}

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

function applyTheme(theme = {}) {
  const root = document.documentElement;
  const mapping = {
    primary: '--primary',
    accent: '--accent',
    background: '--bg',
    text: '--textColor',
  };
  for (const [key, cssVar] of Object.entries(mapping)) {
    if (theme[key]) root.style.setProperty(cssVar, theme[key]);
  }
}

// ---------------------------------------------------------------------------
// Boot / render
// ---------------------------------------------------------------------------

function showError(message) {
  const container = document.getElementById('app-container');
  container.innerHTML = `
    <div class="boot error">
      <p class="boot-title">⚠ Carousel kon niet laden</p>
      <p class="boot-text">${message}</p>
      <button class="btn retry" type="button">Opnieuw proberen</button>
    </div>`;
  container.querySelector('.retry').addEventListener('click', () => {
    container.innerHTML = '<div class="boot"><div class="boot-spinner"></div></div>';
    start();
  });
}

async function loadItems({ silent = false } = {}) {
  const settings = state.settings;
  const data = await fetchItems(settings);
  if (!data.items || data.items.length === 0) {
    throw new Error('Geen objecten met afbeeldingen gevonden.');
  }
  state.items = data.items;
  if (state.carousel) {
    state.carousel.setItems(state.items, { silent });
  }
  return data;
}

function scheduleAdvance() {
  if (state.timer) clearTimeout(state.timer);
  const intervalMs = Math.max(2, state.settings.interval) * 1000;
  state.timer = setTimeout(async () => {
    if (document.hidden) { // retry when the display becomes visible again
      scheduleAdvance();
      return;
    }
    const carousel = state.carousel;
    const atEnd = carousel.index >= carousel.items.length - 1;
    if (atEnd && state.settings.refresh !== false) {
      // Cycle finished: fetch a fresh batch, then start over. On failure,
      // keep looping the current items.
      try {
        await loadItems({ silent: true });
      } catch { /* keep current items */ }
      carousel.goTo(0);
    } else {
      carousel.next();
    }
    scheduleAdvance();
  }, intervalMs);
}

function createCarousel(container, brandSub = null) {
  const carousel = new Carousel(container, {
    interval: state.settings.interval,
    getItems: () => state.items,
    brandSub,
    institution: brandSub,
  });
  // Pause/resume on hover
  container.addEventListener('mouseenter', () => carousel.setPaused(true));
  container.addEventListener('mouseleave', () => carousel.setPaused(false));
  // Stop the timer while paused, resume cleanly after
  carousel.onPauseChange = (paused) => {
    if (paused) {
      if (state.timer) clearTimeout(state.timer);
    } else {
      scheduleAdvance();
    }
  };
  return carousel;
}

// ---------------------------------------------------------------------------
// Fullscreen & keyboard
// ---------------------------------------------------------------------------

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.();
  } else {
    document.exitFullscreen?.();
  }
}

function bindKeyboard(carousel, modal) {
  document.addEventListener('keydown', (event) => {
    if (modal.isOpen) {
      if (event.key === 'Escape') modal.close();
      return;
    }
    switch (event.key) {
      case 'ArrowLeft': carousel.previous(); break;
      case 'ArrowRight': case 'Enter': carousel.next(); break;
      case ' ': carousel.togglePause(); event.preventDefault(); break;
      case 'f': case 'F': toggleFullscreen(); break;
      case 's': case 'S': modal.open(); break;
      case 'Escape':
        if (document.fullscreenElement) document.exitFullscreen?.();
        break;
    }
  });
}

// ---------------------------------------------------------------------------
// Settings modal integration
// ---------------------------------------------------------------------------

function createSettingsModal(container, carousel) {
  const modal = new VanillaSettingsModal(container, {
    settings: state.settings,
    config: state.config,
    onChange: async (settings) => {
      state.settings = settings;
      carousel.setInterval(settings.interval);
      try {
        await loadItems();
      } catch (error) {
        showError(error.message);
        return;
      }
      carousel.goTo(0);
      scheduleAdvance();
    },
  });
  return modal;
}

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------

export async function start() {
  try {
    const config = await fetchConfig();
    state.config = config;
    applyTheme(config.theme);

    // Collection: ?collection=<name> from the URL, else the server default
    const collections = config.collections || {};
    const selectedName = COLLECTION_PARAM
      || config.default_collection
      || Object.keys(collections)[0];
    const selected = collections[selectedName] || config.collection || {};
    if (COLLECTION_PARAM && !collections[selectedName]) {
      throw new Error(
        `Onbekende collectie: '${selectedName}'. ` +
        `Beschikbare collecties: ${Object.keys(collections).join(', ')}`);
    }

    // Server config is the base; stored user settings take precedence
    const carouselCfg = config.carousel || {};
    const stored = VanillaSettingsModal.getSettings();
    state.settings = {
      interval: stored.interval ?? carouselCfg.interval ?? DEFAULTS.interval,
      count: stored.count ?? carouselCfg.count ?? DEFAULTS.count,
      scope: stored.scope ?? selected.scope ?? DEFAULTS.scope,
      seed: stored.seed ?? selected.seed ?? null,
    };
    VanillaSettingsModal.saveSettings(state.settings);

    const data = await loadItems();
    const container = document.getElementById('app-container');
    container.innerHTML = '<div class="carousel" tabindex="0"></div>';
    const carouselEl = container.firstElementChild;
    document.title = selected.label
      ? `NLUX Carousel — ${selected.label}`
      : 'NLUX Carousel';
    state.carousel = createCarousel(carouselEl, selected.label);
    state.carousel.setItems(state.items);
    state.carousel.renderSlide(0);

    const modal = createSettingsModal(carouselEl, state.carousel);
    bindKeyboard(state.carousel, modal);
    scheduleAdvance();
    state.carousel.focus();

    console.info(
      `NLUX carousel gestart (collectie '${selectedName}'): ` +
      `${data.count}/${data.total_available} objecten, ` +
      `${state.settings.interval}s per object.`);
  } catch (error) {
    showError(error.message || String(error));
  }
}

start();