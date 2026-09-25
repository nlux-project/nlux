// App.js - Vanilla JS single-page app
import Carousel from './components/Carousel.js'
import SettingsModal from './components/SettingsModal.js'
import { API_BASE, DEFAULT_COLLECTION, DEFAULT_SCOPE } from './config'

// Initialize and export app
export default class App {
  constructor(containerId = 'app-container') {
    this.container = document.getElementById(containerId)
    this.collection = localStorage.getItem('nlux-collection') || DEFAULT_COLLECTION
    this.scope = localStorage.getItem('nlux-scope') || DEFAULT_SCOPE
    this.settings = { ...DEFAULT_SETTINGS }
    this.carousel = null
    this.settingsModal = null
    this.fetchController = null
    this.intervalController = null
    this.initialized = false

    this.init()
  }

  async init() {
    if (this.initialized) return

    // Load settings from localStorage
    const storedSettings = localStorage.getItem('nlux-settings')
    if (storedSettings) {
      this.settings = { ...this.settings, ...JSON.parse(storedSettings) }
    }

    // Initialize components
    this.settingsModal = new SettingsModal()

    // Initialize carousel controller
    this.fetchController = new FetchController(API_BASE)
    this.carousel = new Carousel([], 0, this.onSlideChange, this.settings)

    // Initialize fullscreen
    this.handleFullscreenToggle()

    // Initialize lock
    this.handleLockToggle()

    // Start carousel interval
    this.startInterval()

    this.initialized = true

    // Render
    this.render()
  }

  async render() {
    if (!this.initialized) return
    return
  }

  async fetchCarouselItems() {
    try {
      const queryParams = new URLSearchParams()
      queryParams.append('collection', this.collection)
      queryParams.append('scope', this.scope)
      queryParams.append('page', '0')
      queryParams.append('pageLength', this.settings.count)

      const url = `${API_BASE}/api/search/${this.scope}?${queryParams.toString()}`
      
      const response = await this.fetchController.fetch(url, {
        headers: {
          'Accept': 'application/ld+json',
        }
      })

      const data = await response.json()

      if (data.orderedItems && data.orderedItems.length > 0) {
        // Extract items from orderedItems
        const items = data.orderedItems
          .filter(item => item.type === 'HumanMadeObject')
          .map(item => ({
            uri: item.id,
            thumbnail: item.properties?.thumbnail || {},
            title: item.properties?.title || { value: 'Untitled' },
            description: item.properties?.description?.text || '',
            credits: item.properties?.credits?.text || null,
            endDate: item.properties?.endDate,
            startDate: item.properties?.startDate,
            datePeriodBeginning: item.properties?.datePeriodBeginning,
            type: item.properties?.type || '',
            links: item.properties?.links?.slice(0, 10) || [],
          }))

        this.onSlideChange?.({
          count: items.length,
          items: items,
          isReady: true,
        })

        // Start interval
        this.startInterval()
      } else {
        this.onSlideChange?.({
          count: 0,
          items: [],
          isReady: true,
        })
      }
    } catch (error) {
      console.error('Error fetching carousel items:', error)
      this.onSlideChange?.({
        count: 0,
        items: [],
        isReady: false,
        error: error.message,
      })
    }
  }

  async fetchMetadata(uri) {
    try {
      const url = `${API_BASE}/${uri}`
      const response = await this.fetchController.fetch(url)
      
      if (response.ok) {
        const data = await response.json()
        return data.properties || data
      } else if (response.status === 404) {
        return {
          uri: uri,
          properties: {
            thumbnail: null,
            title: { value: 'Not found' },
          }
        }
      } else {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error(`Error fetching metadata for ${uri}:`, error)
      return {
        uri: uri,
        properties: {
          thumbnail: null,
          title: { value: 'Error fetching metadata' },
        }
      }
    }
  }

  async populateCarousel() {
    if (!this.carousel) {
      this.carousel = new Carousel([], 0, this.onSlideChange, this.settings)
    }

    try {
      // Fetch items from API
      const queryParams = new URLSearchParams()
      queryParams.append('collection', this.collection)
      queryParams.append('scope', this.scope)
      queryParams.append('page', '0')
      queryParams.append('pageLength', this.settings.count)

      const url = `${API_BASE}/api/search/${this.scope}?${queryParams.toString()}`
      const response = await this.fetchController.fetch(url, {
        headers: {
          'Accept': 'application/ld+json',
        }
      })

      const data = await response.json()
      
      // Extract items from orderedItems
      const items = data.orderedItems
        .filter(item => item.type === 'HumanMadeObject')
        .slice(0, this.settings.count)
        .map(item => this.transformItem(item))

      this.carousel = new Carousel(items, items.length, this.onSlideChange, this.settings)

      if (items.length > 0) {
        // Fetch metadata for each item
        const metadataPromises = items.map(item => this.fetchMetadata(item.uri))
        const metadata = await Promise.all(metadataPromises)

        items.forEach((item, index) => {
          item.metadata = metadata[index] || {}
        })
      }

      this.onSlideChange?.({
        count: items.length,
        items: items,
        isReady: true,
      })
    } catch (error) {
      console.error('Error populating carousel:', error)
      this.onSlideChange?.({
        count: 0,
        items: [],
        isReady: false,
        error: error.message,
      })
    }
  }

  transformItem(item) {
    return {
      uri: item.id,
      thumbnail: item.properties?.thumbnail || {},
      title: item.properties?.title || { value: 'Untitled' },
      description: item.properties?.description?.text || '',
      credits: item.properties?.credits?.text || null,
      endDate: item.properties?.endDate,
      startDate: item.properties?.startDate,
      datePeriodBeginning: item.properties?.datePeriodBeginning,
      type: item.properties?.type || '',
      links: item.properties?.links?.slice(0, 10) || [],
    }
  }

  handleFullscreenToggle(event) {
    this.settings.setFullscreen(!this.settings.config.fullscreen)
    this.settingsModal.save()
  }

  handleLockToggle(event) {
    this.settings.setLock(!this.settings.config.lock)
    this.settingsModal.save()
  }

  startInterval() {
    if (this.intervalController) {
      clearInterval(this.intervalController)
    }

    this.intervalController = setInterval(() => {
      if (this.carousel && !this.carousel.effectiveConfig.lock) {
        this.carousel.next()
      }
    }, this.settings.config.interval * 1000)
  }

  stopInterval() {
    if (this.intervalController) {
      clearInterval(this.intervalController)
      this.intervalController = null
    }
  }

  async onSlideChange({ count, items, isReady, error }) {
    if (isReady) {
      console.log(`Carousel ready with ${count} items`)
      
      if (this.settings.config.autoFetch && count === 0 && !error) {
        this.populateCarousel()
      }
    } else {
      console.error('Carousel error:', error)
      
      // Auto-fetch after timeout
      setTimeout(() => {
        this.populateCarousel()
      }, this.settings.config.autoFetchTimeout)
    }
  }

  setCollection(collection) {
    this.collection = collection
    localStorage.setItem('nlux-collection', collection)
  }

  setScope(scope) {
    this.scope = scope
    localStorage.setItem('nlux-scope', scope)
  }

  setConfig(config) {
    this.settings.config = { ...this.settings.config, ...config }
    this.saveSettings()
  }

  setFullscreen(fullscreen) {
    this.settings.config.fullscreen = fullscreen
    this.saveSettings()
  }

  setLock(lock) {
    this.settings.config.lock = lock
    this.saveSettings()
  }

  setInterval(interval) {
    this.settings.config.interval = interval
    this.saveSettings()
  }

  setCount(count) {
    this.settings.config.count = count
    this.saveSettings()
  }

  setMaxAge(maxAge) {
    this.settings.config.maxAge = maxAge
    this.saveSettings()
  }

  saveSettings() {
    localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
    this.settingsModal.save()
  }

  async fetchCollectionStats() {
    try {
      const url = `${API_BASE}/api/stats?collection=${this.collection}`
      const response = await this.fetchController.fetch(url)
      return await response.json()
    } catch (error) {
      console.error('Error fetching collection stats:', error)
      return null
    }
  }

  async handleSearch(q, searchType = 'query') {
    try {
      let url
      if (searchType === 'query') {
        url = `${API_BASE}/api/search/info?q=${encodeURIComponent(q)}`
      } else if (searchType === 'grammar') {
        url = `${API_BASE}/api/translate/${this.scope}?q=${encodeURIComponent(q)}`
      } else {
        url = `${API_BASE}/api/search/${searchType}?q=${encodeURIComponent(q)}`
      }
      
      const response = await this.fetchController.fetch(url, {
        headers: {
          'Accept': 'application/ld+json',
        }
      })
      
      return await response.json()
    } catch (error) {
      console.error('Error:', error)
      return null
    }
  }

  handleCollectionChange(e) {
    this.collection = e.target.value
    localStorage.setItem('nlux-collection', this.collection)
    
    // Refresh carousel with new collection
    this.populateCarousel()
  }

  handleScopeChange(e) {
    this.scope = e.target.value
    localStorage.setItem('nlux-scope', this.scope)
    
    // Refresh carousel with new scope
    this.populateCarousel()
  }

  get settings() {
    return this.settings
  }

  getFetchController() {
    return this.fetchController
  }

  async stop() {
    this.stopInterval()
    if (this.carousel) {
      this.carousel.destroy()
      this.carousel = null
    }
    this.initialized = false
  }

  destroy() {
    this.stop()
    this.settingsModal.hide()
  }
}

// Export globally for browser usage
if (typeof window !== 'undefined') {
  window.nluxCarousell = {
    App,
  }

  // Auto-initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('app-container')
    if (container) {
      const app = new App(container.id)
      window.nluxApp = app
      
      // Auto-start carousel
      setTimeout(() => {
        if (window.nluxApp) {
          window.nluxApp.populateCarousel()
        }
      }, 500)
    }
  })
}
