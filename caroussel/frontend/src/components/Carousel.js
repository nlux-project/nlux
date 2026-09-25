/**
 * Carousel — renders slides and handles navigation for the NLUX carousel.
 *
 * A carousel consists of stacked .slide elements; the active one fades in.
 * Images are lazily assigned to slide <img> tags when the slide is within
 * one step of the active index. Includes a per-slide progress bar, keyboard
 * and touch swipe navigation and a pause state.
 */

const PRELOAD_DISTANCE = 1;

export default class Carousel {
  constructor(container, { interval = 10, getItems = null, brandSub = null } = {}) {
    this.container = container;
    this.interval = interval;
    this.getItems = getItems;
    this.items = [];
    this.index = 0;
    this.paused = false;
    this.onPauseChange = null;

    container.classList.add('carousel-root');
    container.innerHTML = `
      <div class="slides" aria-live="polite"></div>
      <div class="progress-track"><div class="progress-fill"></div></div>
      <div class="carousel-topbar">
        <div class="brand">
          <span class="brand-title">NLUX</span>
          <span class="brand-sub"></span>
        </div>
        <div class="topbar-buttons">
          <button class="btn icon-btn pause-btn" title="Pauze (spatie)" aria-label="Pauze"></button>
          <button class="btn icon-btn fullscreen-btn" title="Volledig scherm (F)" aria-label="Volledig scherm"></button>
        </div>
      </div>`;

    const brandSubEl = container.querySelector('.brand-sub');
    if (brandSub) brandSubEl.textContent = brandSub;
    else brandSubEl.remove(); // hide the subtitle when no collection label

    this.slidesEl = container.querySelector('.slides');
    this.progressFill = container.querySelector('.progress-fill');
    this.pauseBtn = container.querySelector('.pause-btn');
    this.fullscreenBtn = container.querySelector('.fullscreen-btn');

    this.pauseBtn.addEventListener('click', () => this.togglePause());
    this.fullscreenBtn.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen?.();
      } else {
        document.exitFullscreen?.();
      }
    });

    this._bindSwipe();
  }

  focus() {
    this.container.focus?.();
  }

  setInterval(seconds) {
    this.interval = Math.max(2, seconds);
    this._restartProgress();
  }

  setPaused(paused) {
    if (this.paused === paused) return;
    this.paused = paused;
    this.container.classList.toggle('paused', paused);
    this.pauseBtn.textContent = paused ? '▶' : '❚❚';
    this.pauseBtn.title = paused ? 'Verder (spatie)' : 'Pauze (spatie)';
    this.progressFill.style.animationPlayState = paused ? 'paused' : 'running';
    if (this.onPauseChange) this.onPauseChange(paused);
  }

  togglePause() {
    this.setPaused(!this.paused);
  }

  setItems(items, { silent = false } = {}) {
    this.items = items || [];
    this.slidesEl.innerHTML = '';
    this._slideEls = this.items.map((item, i) => this._buildSlide(item, i));
    for (const el of this._slideEls) this.slidesEl.appendChild(el);
    if (this.index >= this.items.length) this.index = 0;
    this.renderSlide(this.index, { silent });
  }

  goTo(index) {
    const count = this.items.length;
    if (!count) return;
    this.renderSlide(((index % count) + count) % count);
  }

  next() {
    const count = this.items.length;
    if (!count) return;
    this.renderSlide((this.index + 1) % count);
  }

  previous() {
    const count = this.items.length;
    if (!count) return;
    this.renderSlide((this.index - 1 + count) % count);
  }

  renderSlide(index, { silent = false } = {}) {
    const count = this.items.length;
    if (!count) return;
    index = ((index % count) + count) % count;
    this.index = index;

    this._slideEls.forEach((el, i) => {
      el.classList.toggle('active', i === index);
      if (Math.abs(i - index) <= PRELOAD_DISTANCE) this._assignImage(i);
    });
    this._restartProgress();
  }

  // -- internals ----------------------------------------------------------

  _buildSlide(item, index) {
    const slide = document.createElement('figure');
    slide.className = 'slide';
    slide.dataset.index = index;

    const meta = [
      item.classification,
      item.technique,
      item.material,
      item.accession,
    ].filter(Boolean).join(' · ');

    const linkAttrs = item.detail_url
      ? ` href="${item.detail_url}" target="_blank" rel="noopener"`
      : '';

    slide.innerHTML = `
      <div class="slide-media"><img alt="" loading="eager" decoding="async"></div>
      <figcaption class="slide-caption">
        <div class="caption-body">
          <p class="slide-title"></p>
          <p class="slide-creator"></p>
          <p class="slide-meta"></p>
          <p class="slide-credit"></p>
        </div>
        ${item.detail_url
          ? `<a class="slide-link"${linkAttrs}>Bekijk bij Teylers Museum ↗</a>`
          : ''}
      </figcaption>`;

    const titleEl = slide.querySelector('.slide-title');
    const creatorEl = slide.querySelector('.slide-creator');
    const metaEl = slide.querySelector('.slide-meta');
    const creditEl = slide.querySelector('.slide-credit');
    const img = slide.querySelector('img');

    titleEl.textContent = item.title || 'Zonder titel';
    creatorEl.textContent = item.creator || '';
    metaEl.textContent = meta;
    creditEl.textContent = item.credit || '';
    img.alt = item.title || item.accession || 'Object';

    img.addEventListener('error', () => {
      slide.classList.add('image-failed');
      img.removeAttribute('src');
    });

    return slide;
  }

  _assignImage(index) {
    const el = this._slideEls[index];
    const img = el?.querySelector('img');
    if (!img || img.dataset.assigned) return;
    const item = this.items[index];
    if (!item?.image) {
      el.classList.add('image-failed');
      return;
    }
    img.dataset.assigned = '1';
    img.src = item.image;
  }

  _restartProgress() {
    const fill = this.progressFill;
    fill.style.animation = 'none';
    // force reflow so the animation restarts
    void fill.offsetWidth;
    fill.style.animation = `slide-progress ${this.interval}s linear forwards`;
    if (this.paused) fill.style.animationPlayState = 'paused';
  }

  _bindSwipe() {
    let startX = null;
    this.container.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
    }, { passive: true });
    this.container.addEventListener('touchend', (e) => {
      if (startX === null) return;
      const dx = e.changedTouches[0].clientX - startX;
      startX = null;
      if (Math.abs(dx) < 40) return;
      if (dx < 0) this.next(); else this.previous();
    }, { passive: true });
  }
}