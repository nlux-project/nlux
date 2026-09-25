// CarouselController.js
// Vanilla JS carousel controller with API integration

class CarouselController {
  constructor() {
    this.settings = window.nluxStores?.settingsStore || {
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
    
    this.slides = []
    this.currentSlideIndex = 0
    this.timer = null
    this.refreshTimer = null
    this.api = window.LUX_API || 'http://localhost:8000'
  }
  
  async init() {
    // Initialize slides from API
    await this.fetchSlides()
    
    // Start automatic slide transitions
    this.startAutoSlide()
    
    // Setup keyboard navigation
    this.setupKeyboardNavigation()
    
    // Setup form inputs to sync with settings
    this.setupSettingsInputs()
  }
  
  async fetchSlides() {
    const { collection, scope, count, maxAge } = this.settings
    
    const endpoint = `/api/search/${scope}?collection=${collection}&page=1&pageLength=${count}`
    const response = await fetch(this.api + endpoint)
    
    if (response.ok) {
      const data = await response.json()
      
      // Extract orderedItems (they have {id, type} stubs)
      this.slides = data.orderedItems?.slice(0, count) || []
      
      // Store API data for later refresh
      this.rawData = data
      
      // Apply slide transforms
      this.applyTransforms()
    } else {
      console.error('Failed to fetch slides:', response.status)
      this.slides = []
    }
  }
  
  startAutoSlide() {
    // Clear existing timer
    if (this.timer) {
      clearTimeout(this.timer)
    }
    
    // Set new timer based on interval setting
    const intervalSeconds = this.settings.config.interval || 5
    this.timer = setTimeout(() => {
      this.nextSlide()
      this.startAutoSlide()
    }, intervalSeconds * 1000)
  }
  
  nextSlide() {
    if (this.settings.config.lock) return
    
    const totalSlides = this.slides.length
    const nextIndex = (this.currentSlideIndex + 1) % totalSlides
    
    this.currentSlideIndex = nextIndex
    this.applyTransforms()
  }
  
  prevSlide() {
    if (this.settings.config.lock) return
    
    const totalSlides = this.slides.length
    const prevIndex = (this.currentSlideIndex - 1 + totalSlides) % totalSlides
    
    this.currentSlideIndex = prevIndex
    this.applyTransforms()
  }
  
  goToSlide(index) {
    if (index < 0 || index >= this.slides.length) return
    
    this.currentSlideIndex = index
    this.applyTransforms()
  }
  
  applyTransforms() {
    const totalSlides = this.slides.length
    const activeItem = this.slides[this.currentSlideIndex]
    
    // Update transforms for all slides
    this.slides.forEach((item, idx) => {
      const isPrev = idx === this.currentSlideIndex - 1
      const isNext = idx === this.currentSlideIndex + 1
      const isActive = idx === this.currentSlideIndex
      
      // Slide transform
      item.slide.transform = isActive ? 'translateX(0)' : isPrev ? 'translateX(-20px)' : 'translateX(20px)'
      item.slide.opacity = isActive ? 1 : 0.4
      item.slide.zIndex = isActive ? 10 : isPrev ? 5 : 0
    })
  }
  
  setupKeyboardNavigation() {
    // Left arrow
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') {
        this.prevSlide()
        this.renderSlide(this.currentSlideIndex)
      } else if (e.key === 'ArrowRight') {
        this.nextSlide()
        this.renderSlide(this.currentSlideIndex)
      }
    })
  }
  
  setupSettingsInputs() {
    document.addEventListener('DOMContentLoaded', () => {
      // Fullscreen toggle
      const fullscreenToggle = document.getElementById('toggle-fullscreen')
      if (fullscreenToggle) {
        fullscreenToggle.addEventListener('change', (e) => {
          this.settings.config.fullscreen = e.target.checked
          localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
          
          // Recreate carousel with new config
          this.init()
        })
      }
      
      // Lock toggle
      const lockToggle = document.getElementById('toggle-lock')
      if (lockToggle) {
        lockToggle.addEventListener('change', (e) => {
          this.settings.config.lock = e.target.checked
          localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
          
          // Stop auto-slide if locked
          if (this.settings.config.lock) {
            this.pauseAutoSlide()
          }
        })
      }
      
      // Interval slider
      const intervalSlider = document.getElementById('interval-slider')
      if (intervalSlider) {
        intervalSlider.addEventListener('input', (e) => {
          this.settings.config.interval = parseInt(e.target.value)
          localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
          
          // Update timer
          this.startAutoSlide()
        })
      }
      
      // Count slider
      const countSlider = document.getElementById('count-slider')
      if (countSlider) {
        countSlider.addEventListener('input', async (e) => {
          const count = parseInt(e.target.value)
          this.settings.config.count = count
          localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
          
          // Reload slides with new count
          await this.fetchSlides()
          this.startAutoSlide()
        })
      }
      
      // Collection select
      const collectionSelect = document.getElementById('collection-select')
      if (collectionSelect) {
        collectionSelect.addEventListener('change', async (e) => {
          this.settings.collection = e.target.value
          localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
          
          // Reload with new collection
          await this.fetchSlides()
          this.startAutoSlide()
        })
      }
      
      // Scope select
      const scopeSelect = document.getElementById('scope-select')
      if (scopeSelect) {
        scopeSelect.addEventListener('change', async (e) => {
          this.settings.scope = e.target.value
          localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
          
          // Reload with new scope
          await this.fetchSlides()
          this.startAutoSlide()
        })
      }
      
      // Random seed button
      const randomSeedBtn = document.getElementById('generate-seed')
      if (randomSeedBtn) {
        randomSeedBtn.addEventListener('click', async () => {
          this.settings.collection = ['teylers', 'rijksmuseum', 'nms', 'boijmans', 'bram van sleepshire'][Math.floor(Math.random() * 5)]
          this.settings.scope = ['item', 'work', 'agent', 'place', 'concept', 'event'][Math.floor(Math.random() * 6)]
          localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
          
          await this.fetchSlides()
          this.startAutoSlide()
        })
      }
      
      // Reset button
      const resetBtn = document.getElementById('reset-carousel')
      if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
          this.settings = {
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
          localStorage.setItem('nlux-settings', JSON.stringify(this.settings))
          
          await this.fetchSlides()
          this.startAutoSlide()
        })
      }
    })
  }
  
  async fetchNewData() {
    const { collection, scope, count } = this.settings
    
    const endpoint = `/api/search/${scope}?collection=${collection}&page=1&pageLength=${count}`
    const response = await fetch(this.api + endpoint)
    
    if (response.ok) {
      this.rawData = await response.json()
      this.slides = this.rawData.orderedItems || []
      this.applyTransforms()
    } else {
      console.error('Failed to fetch new data:', response.status)
    }
  }
  
  pauseAutoSlide() {
    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
  }
  
  resumeAutoSlide() {
    this.startAutoSlide()
  }
}

// Generate a new carousel instance
export async function generateCarousel() {
  return new CarouselController()
}
