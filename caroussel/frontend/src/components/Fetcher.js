// Fetcher.js - Stub fetcher for demo purposes
// Will be replaced with actual NLUX API fetcher when available

class Fetcher {
  constructor() {
    this.baseUrl = ''
    this.timeout = 5000
  }

  async fetch(url, options = {}) {
    // Stub implementation - return dummy response for demo
    console.log('Fetcher stub called for:', url, 'with options:', options)
    
    // Check if this is a carousel fetch
    if (url.includes('/api/search/')) {
      return {
        totalItems: 0,
        orderedItems: [],
        next: null,
        prev: null
      }
    }

    // Check if this is an object fetch
    if (url.includes('/objects/')) {
      // Parse query parameters from URL
      const query = new URLSearchParams(url.split('?')[1] || '')
      const id = url.split('/').pop()
      
      return {
        id: id,
        uri: `https://example.org/${id}`,
        title: `Demo: Object ${id}`,
        abstract: 'This is a demo object. When the data pipeline is running, this will be replaced with real museum data.',
        copyright: 'Teylers Museum / Teylers',
        date: 'Unknown',
        creator: {
          id: 'unknown',
          label: 'Unknown Artist'
        }
      }
    }

    // Check if this is an item fetch
    if (url.includes('/api/items/') || url.includes('/items/')) {
      return {
        id: 'demo-id',
        uri: `https://example.org/demo-id`,
        title: 'Demo Item',
        type: 'sc:Item',
        data: {
          title: 'Demo Item',
          type: ['sc:Item', 'lulx:DigitalObject']
        }
      }
    }

    // Default response
    return {
      data: {
        '@context': 'https://linked.art/profile',
        id: `https://example.org/${Date.now()}`,
        type: ['http://schema.org/CreativeWork'],
        title: 'Demo Item',
        description: 'This is a demo response.',
        copyrightHolder: 'Demo Museum',
        dateCreated: 'Unknown',
        creator: {
          '@type': 'Organization',
          name: 'Demo Museum'
        }
      }
    }
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Fetcher }
}
