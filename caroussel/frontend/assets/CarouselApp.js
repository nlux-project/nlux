// CarouselApp.js - Main Vanilla JS carousel app with settings
import { Carousel } from './components/Carousel.js'
import { settingsStore } from './store/CarouselController.js'
import { Fetcher } from './components/Fetcher.js'

// Initialize settings store
if (typeof settingsStore === 'undefined') {
  settingsStore = {
    config: {
      fullscreen: false,
      lock: true,
      interval: 4000,
      showControls: true
    },
    settings: {
      collectionId: 'teylers',
      scope: 'objects',
      sort: 'alphabetical',
      showMetadata: false
    },
    state: {
      totalItems: 0,
      isLoading: false,
      items: []
    }
  }
}

// Fetch items from carousel collection
async function fetchItems(collectionId, scope, sortBy) {
  const fetcher = new Fetcher()
  
  // Estimate total items
  const estimateUrl = '/api/search-estimate/' + encodeURIComponent(scope)
  const estimate = await fetcher.fetch(estimateUrl)
  
  settingsStore.state.totalItems = estimate.totalItems || 0
  
  // Fetch items with sorting
  const itemsUrl = '/api/search/' + encodeURIComponent(scope) + '?' + 
    'page=0&pageSize=12&sort=' + encodeURIComponent(sortBy)
  const response = await fetcher.fetch(itemsUrl)
  
  return response.orderedItems || []
}

// Create carousel with settings
function createCarousel(collectionId, scope, sortBy, slideData, totalSlides) {
  const settings = settingsStore.settings
  const config = {
    fullscreen: settings.fullscreen || false,
    lock: settings.lock || true,
    interval: settings.interval || 4000
  }
  
  const appContainer = document.getElementById('carousel-container')
  
  const carousel = new Carousel(
    slideData,
    totalSlides,
    (currentSlide) => {
      settingsStore.updateState({ currentItem: currentSlide + 1, totalItems: totalSlides })
    },
    config
  )
  
  if (appContainer) {
    appContainer.appendChild(carousel.slidesContainer)
  }
  
  return carousel
}

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
  const settings = settingsStore.settings
  
  // Fetch items from collection
  const items = await fetchItems(settings.collectionId, settings.scope, settings.sort)
  settingsStore.state.items = items.slice(0, 20) // Limit for demo
  
  // Create carousel
  const slideData = items.map(item => ({
    title: { value: item.title || 'Untitled' },
    description: { text: item.description?.text || '' },
    thumbnail: { url: item.thumbnail?.url || '' },
    credits: item.credits ? { text: item.credits.text || '' } : null,
    date: item.startDate ? { year: item.startDate } : null,
    type: item.type,
    links: item.links ? item.links.slice(0, 3) : [],
    hasFullUrl: !!item.thumbnail?.url
  }))
  
  createCarousel(settings.collectionId, settings.scope, settings.sort, slideData, Math.min(items.length, 20))
})
