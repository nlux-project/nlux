// CarouselApp.js - Main Vanilla JS carousel app with settings
// Simplified version - uses static data for demo purposes

import { Carousel } from './components/Carousel.js'

// Static fallback data - mock carousel items
const staticCarouselItems = [
  {
    title: "Rembrandt - The Storm on the Sea of Galilee",
    artist: "Rembrandt Harmenszoon van Rijn",
    date: "1668",
    copyright: "Teylers Museum / Teylers",
    image: {
      src: "https://www.teylersmuseum.nl/sites/teylers/files/styles/hero_image/public/36f082a6-365f-454b-b01d-40966580405a.jpg?itok=vFpEJ8Qo",
      width: 2048,
      height: 2560
    }
  },
  {
    title: "Vincent van Gogh - The Potato Eaters",
    artist: "Vincent Willem van Gogh",
    date: "1885",
    copyright: "Teylers Museum / Teylers",
    image: {
      src: "https://www.teylersmuseum.nl/sites/teylers/files/styles/image/public/a23a23c2-1390-4843-b91d-7667e335755a.jpg?itok=8kLj5X2Y",
      width: 1536,
      height: 2048
    }
  },
  {
    title: "Pablo Picasso - The Weeping Woman",
    artist: "Pablo Picasso",
    date: "1937",
    copyright: "Teylers Museum / Teylers",
    image: {
      src: "https://www.teylersmuseum.nl/sites/teylers/files/styles/image/public/b4a7a654-953e-4b2a-8c1f-3d5e4f6a8b2c.jpg?itok=9mNk7LpQ",
      width: 1920,
      height: 2560
    }
  }
]

// Initialize settings store
const settingsStore = {
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
    totalItems: staticCarouselItems.length,
    isLoading: false,
    items: staticCarouselItems,
    currentIndex: 0
  }
}

// Retrieve slides from items
async function getSlides(items, options = {}) {
  const { 
    baseUrl = '',
    teylersApiUrl = '',
    showMetadata = false,
    maxSlides = 100
  } = options

  const slides = []
  
  // Use static data for demo
  slides.push({
    id: 'slide-demo-1',
    title: 'Rembrandt - The Storm on the Sea of Galilee',
    artist: 'Rembrandt Harmenszoon van Rijn',
    date: '1668',
    image: {
      src: 'https://www.teylersmuseum.nl/sites/teylers/files/styles/hero_image/public/36f082a6-365f-454b-b01d-40966580405a.jpg?itok=vFpEJ8Qo',
      width: 2048,
      height: 2560
    },
    copyright: 'Teylers Museum / Teylers'
  })
  
  slides.push({
    id: 'slide-demo-2',
    title: 'Vincent van Gogh - The Potato Eaters',
    artist: 'Vincent Willem van Gogh',
    date: '1885',
    image: {
      src: 'https://www.teylersmuseum.nl/sites/teylers/files/styles/image/public/a23a23c2-1390-4843-b91d-7667e335755a.jpg?itok=8kLj5X2Y',
      width: 1536,
      height: 2048
    },
    copyright: 'Teylers Museum / Teylers'
  })
  
  slides.push({
    id: 'slide-demo-3',
    title: 'Pablo Picasso - The Weeping Woman',
    artist: 'Pablo Picasso',
    date: '1937',
    image: {
      src: 'https://www.teylersmuseum.nl/sites/teylers/files/styles/image/public/b4a7a654-953e-4b2a-8c1f-3d5e4f6a8b2c.jpg?itok=9mNk7LpQ',
      width: 1920,
      height: 2560
    },
    copyright: 'Teylers Museum / Teylers'
  })

  return slides
}

// Create carousel with settings
function createCarousel(collectionId, scope, sortBy, slideData, totalSlides) {
  const settings = settingsStore.settings
  const config = {
    container: document.getElementById('app-container') || document.body,
    settings: settings,
    totalSlides: totalSlides || 1,
    initialIndex: 0
  }
  
  // Initialize carousel
  const carousel = new Carousel(config)
  
  return { carousel, settingsStore }
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('CarouselApp loaded with', staticCarouselItems.length, 'static items')
  
  // Auto-initialize carousel
  const appContainer = document.getElementById('app-container')
  if (appContainer) {
    createCarousel('teylers', 'objects', 'alphabetical', staticCarouselItems, staticCarouselItems.length)
  }
})

