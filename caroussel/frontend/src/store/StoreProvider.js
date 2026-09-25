// Settings default state
const DEFAULT_STATE = {
  collection: 'teylers',
  scope: 'item',
  config: {
    fullscreen: false,
    lock: false,
    interval: 5,
    count: 3,
    maxAge: 5,
  },
}

// Global settings store
const settingsStore = {
  config: DEFAULT_STATE.config,
  collection: DEFAULT_STATE.collection,
  scope: DEFAULT_STATE.scope,
  
  setCollection(collection) {
    this.collection = collection
    this.save()
  },
  
  setScope(scope) {
    this.scope = scope
    this.save()
  },
  
  setFullscreen(fullscreen) {
    this.config.fullscreen = fullscreen
    this.save()
  },
  
  setLock(lock) {
    this.config.lock = lock
    this.save()
  },
  
  setInterval(interval) {
    this.config.interval = interval
    this.save()
  },
  
  setCount(count) {
    this.config.count = count
    this.save()
  },
  
  setMaxAge(maxAge) {
    this.config.maxAge = maxAge
    this.save()
  },
  
  setConfig(config) {
    this.config = { ...this.config, ...config }
    this.save()
  },
  
  save() {
    localStorage.setItem('nlux-settings', JSON.stringify(this))
  },
}

// Export globally
if (typeof window !== 'undefined') {
  window.nluxStores = {
    settingsStore,
  }
}

// Default values
export { settingsStore, DEFAULT_STATE }

// Global store (unified access point)
window.nluxGlobalStore = window.nluxGlobalStore || {}
window.nluxGlobalStore.settingsStore = window.nluxGlobalStore.settingsStore || settingsStore
window.nluxGlobalStore.carouselController = window.nluxGlobalStore.carouselController || null
