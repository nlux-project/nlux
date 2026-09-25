// CarouselController.js - Vanilla JS settings store and controller
// No framework - purely Vanilla JS

class CarouselController {
  constructor() {
    this.settings = {
      collectionId: 'teylers',
      scope: 'objects',
      sort: 'alphabetical',
      showMetadata: false
    }
    
    this.state = {
      totalItems: 0,
      isLoading: false,
      items: []
    }
    
    this.currentSlide = 0
    this.carousel = null
  }
  
  initialize() {
    // Initialize from URL parameters or defaults
    const urlParams = new URLSearchParams(window.location.search)
    const collectionId = urlParams.get('collection') || 'teylers'
    const scope = urlParams.get('scope') || 'objects'
    const sort = urlParams.get('sort') || 'alphabetical'
    
    this.settings = {
      collectionId,
      scope,
      sort,
      showMetadata: false
    }
    
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('carouselSettings')
    if (savedSettings) {
      try {
        this.settings = { ...this.settings, ...JSON.parse(savedSettings) }
      } catch (e) {
        console.error('Failed to load settings from localStorage:', e)
      }
    }
    
    console.log('CarouselController initialized:', this.settings)
  }
  
  getSettings() {
    return this.settings
  }
  
  getStore() {
    return {
      settings: this.settings,
      state: this.state,
      currentSlide: this.currentSlide
    }
  }
  
  async updateCollection(collectionId) {
    this.settings.collectionId = collectionId
    this.saveSettings()
    console.log('Collection changed:', collectionId)
    
    // Reload carousel with new collection
    this.loadCarousel()
  }
  
  async updateScope(scope) {
    this.settings.scope = scope
    this.saveSettings()
    console.log('Scope changed:', scope)
    
    // Reload carousel with new scope
    this.loadCarousel()
  }
  
  async updateSort(sort) {
    this.settings.sort = sort
    this.saveSettings()
    console.log('Sort changed:', sort)
    
    // Reload carousel with new sort
    this.loadCarousel()
  }
  
  updateState(updates) {
    this.state = { ...this.state, ...updates }
    this.saveState()
  }
  
  async loadCarousel() {
    try {
      this.state.isLoading = true
      this.updateState({ isLoading: true })
      
      // TODO: Implement fetch based on settings
      // For now, generate demo data
      const itemCount = this.settings.collectionId === 'texas' ? 10 : 20
      this.state.totalItems = itemCount
      this.state.items = []
      this.currentSlide = 0
      
      this.saveState()
      
      return await this.generateDemoSlides(itemCount)
      
    } catch (error) {
      console.error('Failed to load carousel:', error)
      this.state.items = []
      this.saveState()
      return []
    }
  }
  
  async generateDemoSlides(count) {
    const slides = []
    const names = ['Amphora', 'Vase', 'Plaster Cast', 'Brick Model', 'Statue', 'Mosaic', 'Relief', 'Sculpture', 'Panel', 'Tablet']
    
    for (let i = 0; i < count; i++) {
      slides.push({
        index: i,
        title: { value: `${names[i % names.length]} ${i + 1}` },
        description: { text: `This is a demo description for slide ${i + 1} of the ${this.settings.collectionId} collection.` },
        thumbnail: { url: `https://placehold.co/600x400/3182ce/ffffff?text=${names[i % names.length]}+${i + 1}` },
        credits: { text: `© ${this.settings.collectionId} Museum` },
        date: { year: 1900 + (i % 50) },
        type: this.settings.scope === 'objects' ? 'HumanMadeObject' : 'LinguisticObject',
        links: []
      })
    }
    
    return slides
  }
  
  saveSettings() {
    localStorage.setItem('carouselSettings', JSON.stringify(this.settings))
  }
  
  saveState() {
    localStorage.setItem('carouselState', JSON.stringify(this.state))
  }
  
  toggleFullscreen() {
    this.settings.fullscreen = !this.settings.fullscreen
    this.saveSettings()
    console.log('Fullscreen toggled:', this.settings.fullscreen)
  }
  
  toggleLock() {
    this.settings.lock = !this.settings.lock
    this.saveSettings()
    console.log('Lock toggled:', this.settings.lock)
  }
}

// Create global instance
const controller = new CarouselController()
controller.initialize()
export default controller
