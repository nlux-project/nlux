// VanillaSettingsModal.js - Vanilla JS settings modal
// No framework - purely Vanilla JS

class VanillaSettingsModal {
  constructor() {
    this.modal = null
    this.toggleBtn = null
    this.closeBtn = null
    this.collectionSelect = null
    this.scopeSelect = null
    this.sortSelect = null
    this.initialized = false
    
    this.bindEvents()
  }
  
  bindEvents() {
    // Toggle button click
    if (this.toggleBtn) {
      this.toggleBtn.addEventListener('click', () => {
        const isFullscreen = this.toggleBtn.style.display !== 'none'
        this.modal.style.display = isFullscreen ? 'none' : 'block'
        this.toggleBtn.style.display = isFullscreen ? 'none' : 'block'
      })
    }
    
    // Close button click
    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.close())
    }
    
    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal.style.display === 'block') {
        this.close()
      }
    })
  }
  
  show() {
    this.modal.style.display = 'block'
    this.toggleBtn.style.display = 'none'
  }
  
  close() {
    this.modal.style.display = 'none'
    this.toggleBtn.style.display = 'block'
  }
  
  initialize() {
    // Get all DOM elements
    this.modal = document.getElementById('settings-modal')
    this.toggleBtn = document.getElementById('toggle-settings')
    this.closeBtn = document.getElementById('close-settings')
    this.collectionSelect = document.getElementById('collection-select')
    this.scopeSelect = document.getElementById('scope-select')
    this.sortSelect = document.getElementById('sort-select')
    
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('carouselSettings')
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings)
        if (this.collectionSelect) {
          this.collectionSelect.value = settings.collectionId
        }
        if (this.scopeSelect) {
          this.scopeSelect.value = settings.scope
        }
        if (this.sortSelect) {
          this.sortSelect.value = settings.sort
        }
      } catch (e) {
        console.error('Failed to load settings:', e)
      }
    }
    
    // Bind event listeners
    if (this.collectionSelect) {
      this.collectionSelect.addEventListener('change', (e) => {
        console.log('Collection changed:', e.target.value)
        localStorage.setItem('carouselSettings', JSON.stringify({ ...localStorage.getItem('carouselSettings') || {}, collectionId: e.target.value }))
      })
    }
    
    if (this.scopeSelect) {
      this.scopeSelect.addEventListener('change', (e) => {
        console.log('Scope changed:', e.target.value)
        localStorage.setItem('carouselSettings', JSON.stringify({ ...localStorage.getItem('carouselSettings') || {}, scope: e.target.value }))
      })
    }
    
    if (this.sortSelect) {
      this.sortSelect.addEventListener('change', (e) => {
        console.log('Sort changed:', e.target.value)
        localStorage.setItem('carouselSettings', JSON.stringify({ ...localStorage.getItem('carouselSettings') || {}, sort: e.target.value }))
      })
    }
    
    // Set initial carousel scope (only works after carousel loads)
    if (typeof this.carouselScope !== 'undefined') {
      this.carouselScope = this.scopeSelect.value
    }
    
    this.initialized = true
    console.log('VanillaSettingsModal initialized')
  }
  
  // Get current settings
  getSettings() {
    const settings = localStorage.getItem('carouselSettings')
    return settings ? JSON.parse(settings) : {
      collectionId: 'teylers',
      scope: 'objects',
      sort: 'alphabetical',
      showMetadata: false
    }
  }
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  new VanillaSettingsModal().initialize()
})
