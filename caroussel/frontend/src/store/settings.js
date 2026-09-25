export const settingsStore = {
  // API URLs
  API_NLUX: 'http://localhost:8000',  // Default NLUX API (when running locally)
  API_TEYLERS: 'https://www.teylersmuseum.nl/api.php',  // Teylers Adlib API fallback
  
  // Default API to use
  DEFAULT_API: API_NLUX,
  
  DEFAULT_CONFIG: {
    // Display settings
    fullscreen: false,
    lock: false,

    // Carousel settings
    interval: 5,
    count: 3,
    maxAge: 5,
  },
  DEFAULT_STATE: {
    collection: 'all',
    scope: 'item',
    api: DEFAULT_API,
    teylersApiUrl: API_TEYLERS,
    isNLUXAvailable: false,  // Will be determined at runtime
    ...DEFAULT_CONFIG,
  },
}
