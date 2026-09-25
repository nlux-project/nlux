// App.jsx - Vanilla JS version
import Carousel from './components/Carousel.js'
import SettingsModal from './components/Settings.js'
import { settingsStore } from './store/StoreProvider.js'

// Museum logo
function MuseumLogo() {
  return (
    <svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="45" fill="#2c5282" />
      <circle cx="50" cy="50" r="35" fill="#ffffff" />
      <circle cx="50" cy="50" r="15" fill="#2c5282" />
      <text x="50" y="42" textAnchor="middle" fill="#2c5282" fontSize="10" fontWeight="bold" fontFamily="sans-serif">NLUX</text>
    </svg>
  )
}

function App() {
  const settings = settingsStore
  const [activeCollection, setActiveCollection] = useState('teylers')
  const [scope, setScope] = useState('item')
  const [carousel, setCarousel] = useState(null)
  const [currentSlide, setCurrentSlide] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [settingsVisible, setSettingsVisible] = useState(false)
  const [randomSeed, setRandomSeed] = useState(null)
  const [seeded, setSeeded] = useState(false)
  const API_BASE = window.LUX_API || 'http://localhost:8000'

  const generateCarousel = useCallback(async (customConfig = null) => {
    const finalConfig = customConfig || {
      collection: activeCollection,
      scope: scope,
      interval: settings.config.interval,
      count: settings.config.count,
      maxAge: settings.config.maxAge,
    }

    setIsLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem('nlux_token')
      const headers = token ? { Authorization: `Bearer ${token}` } : {}

      const endpoint = customConfig ? '/api/generate-seed' : '/api/generate'
      const url = `${API_BASE}${endpoint}`

      const response = await fetch(url, {
        method: customConfig ? 'POST' : 'GET',
        headers,
        body: customConfig ? JSON.stringify(customConfig) : null,
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
      }

      const data = await response.json()
      setCarousel(data)
      setRandomSeed(data.seed)
      setCurrentSlide(0)
      setIsLoading(false)
    } catch (err) {
      console.error('Failed to generate carousel:', err)
      setError(err.message)
      setIsLoading(false)
    }
  }, [activeCollection, scope, settings])

  useEffect(() => {
    if (carousel) return
    generateCarousel()
  }, [activeCollection, scope, generateCarousel])

  useEffect(() => {
    if (!carousel || settingsVisible) return

    const slideInterval = setInterval(() => {
      setCurrentSlide(prev => (prev + 1) % carousel.slides.length)
    }, settings.config.interval * 1000)

    const seedInterval = setInterval(() => {
      const now = Date.now()
      const lastUpdated = new Date(carousel.last_updated).getTime()
      const elapsed = now - lastUpdated

      if (elapsed > settings.config.maxAge * 1000) {
        setRandomSeed(null)
        setSeeded(false)
        clearInterval(seedInterval)
        clearInterval(slideInterval)
        generateCarousel()
      }
    }, 1000)

    return () => {
      clearInterval(slideInterval)
      clearInterval(seedInterval)
    }
  }, [carousel, settings.config.interval, settings.config.maxAge, settingsVisible, generateCarousel])

  const toggleFullscreen = useCallback(() => {
    settings.setFullscreen(!settings.config.fullscreen)
    const elem = document.documentElement
    if (elem.requestFullscreen) {
      elem.requestFullscreen().catch(err => {
        console.log('Fullscreen error:', err)
      })
    } else if (elem.webkitRequestFullscreen) {
      elem.webkitRequestFullscreen()
    }
  }, [])

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (settingsVisible) {
        if (e.key === 'Escape') {
          setSettingsVisible(false)
        }
        return
      }

      if (!settings.config.lock) {
        if (e.key === 'ArrowRight') {
          setCurrentSlide(prev => (prev + 1) % carousel.slides.length)
        } else if (e.key === 'ArrowLeft') {
          setCurrentSlide(prev => (prev - 1 + carousel.slides.length) % carousel.slides.length)
        } else if (e.key === 'ArrowDown' || e.key === ' ') {
          setCurrentSlide(prev => (prev + 1) % carousel.slides.length)
        } else if (e.key === 'ArrowUp') {
          setCurrentSlide(prev => (prev - 1 + carousel.slides.length) % carousel.slides.length)
        }
      }

      if (e.key === 't' || e.key === 'T') {
        setSettingsVisible(prev => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [carousel, settings.config.lock, settingsVisible])

  const handleGenerateSeed = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const url = `${API_BASE}/api/seed`
      const response = await fetch(url, { method: 'GET' })
      const data = await response.json()
      setRandomSeed(data.seed)
      setSeeded(true)
      setIsLoading(false)
    } catch (err) {
      setError('Failed to generate seed')
      setIsLoading(false)
    }
  }, [API_BASE])

  const handleResetCarousel = useCallback(() => {
    setIsLoading(true)
    setCarousel(null)
    setRandomSeed(null)
    setSeeded(false)
    setCurrentSlide(0)
    generateCarousel()
  }, [generateCarousel])

  if (isLoading) {
    return (
      <div style={styles.loading}>
        <MuseumLogo />
        <div style={styles.loadingText}>🎭 Loading NLUX Carousell...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.errorContainer}>
        <MuseumLogo />
        <div style={styles.error}>
          ⚠️ <strong>Error:</strong> {error}
          <button onClick={() => setActiveCollection('all')} style={styles.button}>
            Change Collection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {settingsVisible && (
        <SettingsModal />
      )}

      <div style={styles.header}>
        <div style={styles.logoContainer}>
          <MuseumLogo />
          <span style={styles.title}>NLUX</span>
        </div>
        <button onClick={() => setSettingsVisible(true)} style={styles.settingsButton} title="⚙️ Settings">
          ⚙️
        </button>
      </div>

      {carousel && !settingsVisible && (
        <Carousel
          slide={carousel.slides[currentSlide]}
          currentSlide={currentSlide}
          totalSlides={carousel.slides.length}
          config={settings.config}
          API_BASE={API_BASE}
          onSlideChange={setCurrentSlide}
        />
      )}

      {!carousel && !settingsVisible && (
        <div style={styles.loadingBanner}>
          <span>🎭 Waiting for data...</span>
        </div>
      )}

      {!settingsVisible && (
        <div style={styles.footer}>
          <span>Slide {currentSlide + 1} of {carousel.slides.length}</span>
        </div>
      )}
    </div>
  )
}

function useState(initialValue) {
  const [state, setState] = [initialValue, initialValue]
  return [state, setState]
}

function useCallback(callback, deps) {
  return callback
}

function useEffect(effect, deps) {
  if (deps && typeof window !== 'undefined') {
    if (deps.length === 0) {
      // Empty deps - run once on mount
      effect()
    } else {
      // Run when deps change
      const depsIndex = deps.indexOf('generateCarousel')
      if (depsIndex !== -1) {
        const oldCarousel = window.__appState?.carousel
        if (oldCarousel !== null && oldCarousel !== window.__appState?.carousel) {
          return
        }
      }
      effect()
    }
  }
}

// Styles
const styles = {
  container: {
    width: '100vw',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f7fafc',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 20px',
    backgroundColor: '#2c5282',
    color: '#ffffff',
    zIndex: 10,
  },
  logoContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  title: {
    fontSize: '20px',
    fontWeight: 'bold',
  },
  settingsButton: {
    padding: '8px 16px',
    backgroundColor: '#ffffff',
    color: '#2c5282',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  loading: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    color: '#2d3748',
  },
  loadingText: {
    marginTop: '20px',
    fontSize: '16px',
  },
  loadingBanner: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    padding: '20px 40px',
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    color: '#ffffff',
    borderRadius: '8px',
    fontSize: '18px',
    zIndex: 100,
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
  },
  error: {
    backgroundColor: '#fff5f5',
    border: '2px solid #fc8181',
    padding: '30px 40px',
    borderRadius: '8px',
    marginTop: '20px',
    textAlign: 'center',
  },
  button: {
    marginTop: '20px',
    padding: '12px 24px',
    backgroundColor: '#ed8936',
    color: '#ffffff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px',
  },
  footer: {
    position: 'absolute',
    bottom: '0',
    left: '0',
    right: '0',
    padding: '10px',
    backgroundColor: '#2c5282',
    color: '#ffffff',
    textAlign: 'center',
    fontSize: '14px',
    zIndex: 5,
  },
}

// Initialize and mount app
window.__appState = { carousel: null, collection: 'teylers', scope: 'item' }

// Export app for use in React
export default App
