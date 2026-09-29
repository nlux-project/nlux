/**
 * VanillaSettingsModal — small dependency-free settings dialog for the
 * carousel display (interval, number of objects, scope). Settings are
 * persisted to localStorage and applied through the onChange callback.
 */

const STORAGE_KEY = 'nlux-carousel-settings';
const SCOPES = [
  ['item', 'Objecten'],
  ['work', 'Werken'],
  ['agent', 'Personen & instellingen'],
  ['place', 'Plaatsen'],
];

const DEFAULTS = { interval: 10, count: 5, scope: 'item' };

export default class VanillaSettingsModal {
  constructor(parent, { settings, config = {}, onChange = null } = {}) {
    this.parent = parent;
    this.settings = { ...DEFAULTS, ...settings };
    this.config = config;
    this.onChange = onChange;
    this.isOpen = false;

    const overlay = document.createElement('div');
    overlay.className = 'settings-overlay';
    overlay.innerHTML = `
      <div class="settings-modal" role="dialog" aria-modal="true" aria-labelledby="settings-title">
        <div class="settings-header">
          <h2 class="settings-title" id="settings-title">Instellingen</h2>
          <button class="btn settings-close" aria-label="Sluiten">×</button>
        </div>
        <div class="settings-body">
          <label class="settings-section">
            <span class="settings-label">Wisseltijd: <output class="settings-value"></output></span>
            <input class="settings-input" type="range" name="interval" min="3" max="120" step="1">
          </label>
          <label class="settings-section">
            <span class="settings-label">Aantal objecten per reeks: <output class="settings-value"></output></span>
            <input class="settings-input" type="range" name="count" min="1" max="50" step="1">
          </label>
          <label class="settings-section">
            <span class="settings-label">Collectie (scope)</span>
            <select class="settings-input" name="scope"></select>
          </label>
          <p class="settings-note">Wijzigingen worden direct toegepast en opgeslagen op dit apparaat.</p>
        </div>
        <div class="settings-footer">
          <button class="btn ghost reset-btn" type="button">Standaardwaarden</button>
          <button class="btn primary apply-btn" type="button">Toepassen</button>
        </div>
      </div>`;
    parent.appendChild(overlay);
    this.overlay = overlay;

    this.intervalInput = overlay.querySelector('[name=interval]');
    this.countInput = overlay.querySelector('[name=count]');
    this.scopeSelect = overlay.querySelector('[name=scope]');
    this.closeBtn = overlay.querySelector('.settings-close');
    this.applyBtn = overlay.querySelector('.apply-btn');
    this.resetBtn = overlay.querySelector('.reset-btn');

    for (const [value, label] of SCOPES) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      this.scopeSelect.appendChild(option);
    }

    this.closeBtn.addEventListener('click', () => this.close());
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) this.close();
    });
    this.applyBtn.addEventListener('click', () => this._apply());
    this.resetBtn.addEventListener('click', () => {
      this.settings = { ...DEFAULTS, seed: null };
      this._fill();
    });
    this.intervalInput.addEventListener('input', () => this._syncOutputs());
    this.countInput.addEventListener('input', () => this._syncOutputs());

    this._fill();
  }

  static getSettings() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  static saveSettings(settings) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch { /* storage unavailable */ }
  }

  open() {
    this.settings = { ...DEFAULTS, ...VanillaSettingsModal.getSettings() };
    this._fill();
    this.overlay.classList.add('show');
    this.isOpen = true;
    this.overlay.querySelector('.settings-close').focus();
  }

  close() {
    this.overlay.classList.remove('show');
    this.isOpen = false;
  }

  _fill() {
    this.intervalInput.value = this.settings.interval;
    this.countInput.value = this.settings.count;
    this.scopeSelect.value = this.settings.scope;
    this._syncOutputs();
  }

  _syncOutputs() {
    const outputs = this.overlay.querySelectorAll('output');
    outputs[0].textContent = `${this.intervalInput.value}s`;
    if (outputs[1]) outputs[1].textContent = this.countInput.value;
  }

  _apply() {
    this.settings = {
      interval: Number(this.intervalInput.value),
      count: Number(this.countInput.value),
      scope: this.scopeSelect.value,
      seed: this.settings.seed ?? null,
    };
    VanillaSettingsModal.saveSettings(this.settings);
    this.close();
    if (this.onChange) this.onChange(this.settings);
  }
}